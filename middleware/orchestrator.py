import httpx
import datetime
import logging
from typing import Dict, Any, List
from fastapi import HTTPException
from schemas.middleware import RegistrarVentaRequest, RegistrarCompraRequest

logger = logging.getLogger("middleware-orquestador")


class OrquestadorMiddleware:
    """
    Clase de dominio orientada a objetos (POO) que coordina los flujos distribuidos
    de venta a clientes y compra a proveedores conectando con los microservicios de dominio.
    """

    def __init__(self, inventario_url: str, compras_ventas_url: str, contabilidad_url: str, transportador_url: str):
        self.inventario_url = inventario_url
        self.compras_ventas_url = compras_ventas_url
        self.contabilidad_url = contabilidad_url
        self.transportador_url = transportador_url

    async def _solicitar(self, client: httpx.AsyncClient, metodo: str, url: str, servicio: str, json_data: Any = None) -> Any:
        """Centraliza la ejecución y el manejo de excepciones HTTP de los microservicios."""
        try:
            res = await client.request(metodo, url, json=json_data)
            if res.status_code not in [200, 201]:
                raise HTTPException(status_code=res.status_code, detail=f"Error en {servicio}: {res.text}")
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Microservicio {servicio} inaccesible: {str(e)}")

    async def cargar_productos(self) -> Dict[str, Any]:
        """Consulta al microservicio de inventario para obtener el stock calculado desde la blockchain"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            return await self._solicitar(client, "GET", f"{self.inventario_url}/cargarProductos", "Inventario")

    async def cargar_requerimientos_productos(self) -> Dict[str, Any]:
        """Consulta al inventario los productos que necesitan reabastecimiento"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            return await self._solicitar(client, "GET", f"{self.inventario_url}/cargarRequerimientosProductos", "Inventario")

    async def registrar_venta(self, payload: RegistrarVentaRequest) -> Dict[str, Any]:
        """
        FLUJO ORQUESTADO DE VENTA A CLIENTE:
          1. Inventario: Valida disponibilidad de stock en el ledger blockchain para cada ítem.
          2. Compras/Ventas: Registra la orden comercial de venta con precios oficiales.
          3. Contabilidad: Emite la factura electrónica formal (genera CUFE).
          4. Compras/Ventas: Vincula la factura a la venta (recibirFactura).
          5. Inventario: Actualiza el stock minando un nuevo bloque inmutable en la Blockchain.
          6. Transportador: Programa el despacho logístico y genera la guía de transporte.
          7. Retorna la factura electrónica con los datos esenciales para el cliente comprador.
        """
        id_proceso = f"ORQ-VEN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"[{id_proceso}] Iniciando orquestación de venta para cliente: {payload.cliente.nombre}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Validación de stock en Inventario (Blockchain)
            res_inv = await self._solicitar(client, "GET", f"{self.inventario_url}/cargarProductos", "Inventario")
            catalogo = {p["id"]: p for p in res_inv.get("productos", [])}

            items_venta_procesados = []
            for item in payload.items:
                if item.producto_id not in catalogo:
                    raise HTTPException(status_code=400, detail=f"El producto '{item.producto_id}' no existe en el catálogo.")
                info_prod = catalogo[item.producto_id]
                if info_prod["stock_actual"] < item.cantidad:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Stock insuficiente para '{info_prod['nombre']}' ({item.producto_id}). "
                               f"Disponible: {info_prod['stock_actual']}, Requerido: {item.cantidad}."
                    )
                items_venta_procesados.append({
                    "producto_id": item.producto_id,
                    "nombre": info_prod["nombre"],
                    "cantidad": item.cantidad,
                    "precio_unitario": info_prod["precio_unitario"]
                })

            # 2. Registro de la Venta en Compras/Ventas
            req_venta = {
                "cliente": payload.cliente.model_dump(),
                "items": items_venta_procesados,
                "metodo_pago": payload.metodo_pago,
                "observaciones": f"Venta coordinada por Middleware [{id_proceso}]"
            }
            res_cv = await self._solicitar(client, "POST", f"{self.compras_ventas_url}/registrarVenta", "Compras/Ventas", req_venta)
            venta_registrada = res_cv.get("venta", res_cv)
            id_venta = venta_registrada["id_venta"]

            # 3. Emisión de Factura en Contabilidad
            req_factura = {
                "tipo_operacion": "VENTA",
                "referencia_operacion": id_venta,
                "emisor": "Muebles Confort S.A.S. - NIT 901.888.777-1",
                "receptor": f"{payload.cliente.nombre} (CC/NIT: {payload.cliente.documento})",
                "subtotal": venta_registrada["subtotal"],
                "iva": venta_registrada["iva"],
                "total": venta_registrada["total"],
                "detalles": [
                    {
                        "producto_id": it["producto_id"],
                        "nombre": it["nombre"],
                        "cantidad": it["cantidad"],
                        "precio_unitario": it["precio_unitario"]
                    } for it in items_venta_procesados
                ],
                "metodo_pago": payload.metodo_pago
            }
            res_cont = await self._solicitar(client, "POST", f"{self.contabilidad_url}/generarFactura", "Contabilidad", req_factura)
            factura_generada = res_cont.get("factura", res_cont)

            # 4. Confirmación y vinculación de factura en Compras/Ventas
            req_recibir_fac = {
                "referencia_operacion": id_venta,
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "fecha_emision": factura_generada["fecha_emision"],
                "total_facturado": factura_generada["total"]
            }
            try:
                await self._solicitar(client, "POST", f"{self.compras_ventas_url}/recibirFactura", "Compras/Ventas", req_recibir_fac)
            except Exception as e:
                logger.warning(f"No se pudo vincular factura en Compras/Ventas: {str(e)}")

            # 5. Actualización del inventario en Blockchain (Reducción por Venta)
            for item in payload.items:
                req_act_inv = {
                    "tipo": "VENTA",
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "referencia": id_venta,
                    "motivo": f"Venta {id_venta} - Factura {factura_generada['numero_factura']}"
                }
                await self._solicitar(client, "POST", f"{self.inventario_url}/actualizarInventario", "Inventario", req_act_inv)

            # 6. Programación de Despacho en Transportador
            paquetes_transporte = [
                {
                    "producto_id": item["producto_id"],
                    "nombre": item["nombre"],
                    "cantidad": item["cantidad"],
                    "peso_estimado_kg": 35.0
                } for item in items_venta_procesados
            ]
            req_transporte = {
                "id_venta": id_venta,
                "destinatario": payload.cliente.nombre,
                "direccion_entrega": payload.cliente.direccion,
                "telefono": payload.cliente.telefono,
                "paquetes": paquetes_transporte
            }
            res_trans = await self._solicitar(client, "POST", f"{self.transportador_url}/ordenarTransporte", "Transportador", req_transporte)
            guia_transporte = res_trans.get("guia", res_trans)

        logger.info(f"[{id_proceso}] Venta orquestada con éxito total.")

        # Retorna únicamente los datos esenciales de la factura y entrega para el cliente
        return {
            "id_venta": id_venta,
            "numero_factura": factura_generada["numero_factura"],
            "cufe": factura_generada["cufe"],
            "fecha_emision": factura_generada["fecha_emision"],
            "cliente": payload.cliente.model_dump(),
            "items": [
                {
                    "producto_id": it["producto_id"],
                    "nombre": it["nombre"],
                    "cantidad": it["cantidad"],
                    "precio_unitario": it["precio_unitario"],
                    "subtotal": round(it["cantidad"] * it["precio_unitario"], 2)
                } for it in items_venta_procesados
            ],
            "subtotal": venta_registrada["subtotal"],
            "iva": venta_registrada["iva"],
            "total": venta_registrada["total"],
            "metodo_pago": payload.metodo_pago,
            "despacho": {
                "numero_guia": guia_transporte["numero_guia"],
                "transportadora": guia_transporte["transportadora"],
                "vehiculo": guia_transporte["vehiculo_asignado"],
                "fecha_estimada_entrega": guia_transporte["fecha_estimada_entrega"]
            }
        }

    async def registrar_compra(self, payload: RegistrarCompraRequest) -> Dict[str, Any]:
        """
        FLUJO ORQUESTADO DE COMPRA A PROVEEDOR:
          1. Inventario: Valida el catálogo de productos y costos vigentes.
          2. Compras/Ventas: Registra la orden de compra comercial a favor del proveedor.
          3. Contabilidad: Emite la factura/cuenta por pagar con su correspondiente consecutivo y CUFE.
          4. Compras/Ventas: Registra la factura en el expediente de compras (recibirFactura).
          5. Inventario: Actualiza el inventario minando bloques de adquisición en la Blockchain.
          6. Retorna el comprobante de compra con los datos esenciales para el proveedor.
        """
        id_proceso = f"ORQ-COM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"[{id_proceso}] Iniciando orquestación de compra para proveedor: {payload.proveedor.nombre}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Validación contra el catálogo de Inventario
            res_inv = await self._solicitar(client, "GET", f"{self.inventario_url}/cargarProductos", "Inventario")
            catalogo = {p["id"]: p for p in res_inv.get("productos", [])}

            items_compra_procesados = []
            for item in payload.items:
                if item.producto_id not in catalogo:
                    raise HTTPException(status_code=400, detail=f"El producto '{item.producto_id}' no existe en el catálogo.")
                info_prod = catalogo[item.producto_id]
                costo_final = item.costo_unitario if item.costo_unitario is not None else info_prod["costo_unitario"]

                items_compra_procesados.append({
                    "producto_id": item.producto_id,
                    "nombre": info_prod["nombre"],
                    "cantidad": item.cantidad,
                    "costo_unitario": costo_final
                })

            # 2. Registro de la Orden de Compra en Compras/Ventas
            req_compra = {
                "proveedor": payload.proveedor.model_dump(),
                "items": items_compra_procesados,
                "terminos_pago": payload.terminos_pago,
                "observaciones": f"Compra coordinada por Middleware [{id_proceso}]"
            }
            res_cv = await self._solicitar(client, "POST", f"{self.compras_ventas_url}/registrarCompra", "Compras/Ventas", req_compra)
            compra_registrada = res_cv.get("compra", res_cv)
            id_compra = compra_registrada["id_compra"]

            # 3. Emisión de Factura de Compra / Cuenta por Pagar en Contabilidad
            req_factura = {
                "tipo_operacion": "COMPRA",
                "referencia_operacion": id_compra,
                "emisor": f"{payload.proveedor.nombre} (NIT: {payload.proveedor.nit})",
                "receptor": "Muebles Confort S.A.S. - NIT 901.888.777-1",
                "subtotal": compra_registrada["subtotal"],
                "iva": compra_registrada["iva"],
                "total": compra_registrada["total"],
                "detalles": [
                    {
                        "producto_id": it["producto_id"],
                        "nombre": it["nombre"],
                        "cantidad": it["cantidad"],
                        "precio_unitario": it["costo_unitario"]
                    } for it in items_compra_procesados
                ],
                "metodo_pago": payload.terminos_pago
            }
            res_cont = await self._solicitar(client, "POST", f"{self.contabilidad_url}/generarFactura", "Contabilidad", req_factura)
            factura_generada = res_cont.get("factura", res_cont)

            # 4. Vinculación de factura en Compras/Ventas
            req_recibir_fac = {
                "referencia_operacion": id_compra,
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "fecha_emision": factura_generada["fecha_emision"],
                "total_facturado": factura_generada["total"]
            }
            try:
                await self._solicitar(client, "POST", f"{self.compras_ventas_url}/recibirFactura", "Compras/Ventas", req_recibir_fac)
            except Exception as e:
                logger.warning(f"No se pudo vincular factura de compra: {str(e)}")

            # 5. Actualización del inventario en Blockchain (Incremento por Adquisición)
            for item in payload.items:
                req_act_inv = {
                    "tipo": "ADQUISICION",
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "referencia": id_compra,
                    "motivo": f"Abastecimiento Compra {id_compra} - Factura {factura_generada['numero_factura']}"
                }
                await self._solicitar(client, "POST", f"{self.inventario_url}/actualizarInventario", "Inventario", req_act_inv)

        logger.info(f"[{id_proceso}] Compra orquestada con éxito total.")

        # Retorna únicamente los datos esenciales del comprobante de compra para el proveedor
        return {
            "id_compra": id_compra,
            "numero_factura": factura_generada["numero_factura"],
            "cufe": factura_generada["cufe"],
            "fecha_emision": factura_generada["fecha_emision"],
            "proveedor": payload.proveedor.model_dump(),
            "items": [
                {
                    "producto_id": it["producto_id"],
                    "nombre": it["nombre"],
                    "cantidad": it["cantidad"],
                    "costo_unitario": it["costo_unitario"],
                    "subtotal": round(it["cantidad"] * it["costo_unitario"], 2)
                } for it in items_compra_procesados
            ],
            "subtotal": compra_registrada["subtotal"],
            "iva": compra_registrada["iva"],
            "total": compra_registrada["total"],
            "terminos_pago": compra_registrada["terminos_pago"]
        }
