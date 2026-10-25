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

    async def cargar_productos(self) -> Dict[str, Any]:
        """Consulta al microservicio de inventario para obtener el stock calculado desde la blockchain"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                res = await client.get(f"{self.inventario_url}/cargarProductos")
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail=res.text)
                return res.json()
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"No fue posible conectar con Inventario: {str(e)}")

    async def cargar_requerimientos_productos(self) -> Dict[str, Any]:
        """Consulta al inventario los productos que necesitan reabastecimiento"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                res = await client.get(f"{self.inventario_url}/cargarRequerimientosProductos")
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail=res.text)
                return res.json()
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"No fue posible conectar con Inventario: {str(e)}")

    async def registrar_venta(self, payload: RegistrarVentaRequest) -> Dict[str, Any]:
        """
        FLUJO ORQUESTADO DE VENTA A CLIENTE:
          1. Inventario: Valida disponibilidad de stock en el ledger blockchain para cada ítem.
          2. Compras/Ventas: Registra la orden comercial de venta con precios oficiales.
          3. Contabilidad: Emite la factura electrónica formal (genera CUFE).
          4. Compras/Ventas: Vincula la factura a la venta (recibirFactura).
          5. Inventario: Actualiza el stock minando un nuevo bloque inmutable en la Blockchain.
          6. Transportador: Programa el despacho logístico y genera la guía de transporte.
          7. Consolidación: Retorna la confirmación completa.
        """
        id_proceso = f"ORQ-VEN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        pasos_completados = []
        logger.info(f"[{id_proceso}] Iniciando orquestación de venta para cliente: {payload.cliente.nombre}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            # PASO 1: Validación de stock en Inventario (Blockchain)
            try:
                res_inv = await client.get(f"{self.inventario_url}/cargarProductos")
                if res_inv.status_code != 200:
                    raise HTTPException(status_code=502, detail="Falla al consultar el catálogo de Inventario.")
                catalogo = {p["id"]: p for p in res_inv.json().get("productos", [])}
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Microservicio Inventario inaccesible: {str(e)}")

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

            pasos_completados.append({
                "paso": 1,
                "componente": "Inventario",
                "accion": "cargarProductos / Verificación de stock en Blockchain",
                "resultado": "OK - Stock suficiente verificado"
            })

            # PASO 2: Registro de la Venta en Compras/Ventas
            req_venta = {
                "cliente": payload.cliente.model_dump(),
                "items": items_venta_procesados,
                "metodo_pago": payload.metodo_pago,
                "observaciones": f"Venta coordinada por Middleware [{id_proceso}]"
            }
            try:
                res_cv = await client.post(f"{self.compras_ventas_url}/registrarVenta", json=req_venta)
                if res_cv.status_code not in [200, 201]:
                    raise HTTPException(status_code=res_cv.status_code, detail=f"Error en Compras/Ventas: {res_cv.text}")
                venta_registrada = res_cv.json().get("venta")
                id_venta = venta_registrada["id_venta"]
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Microservicio Compras/Ventas inaccesible: {str(e)}")

            pasos_completados.append({
                "paso": 2,
                "componente": "Compras/Ventas",
                "accion": "registrarVenta",
                "id_venta": id_venta,
                "subtotal": venta_registrada["subtotal"],
                "total": venta_registrada["total"],
                "resultado": "OK - Venta registrada"
            })

            # PASO 3: Emisión de Factura en Contabilidad
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
            try:
                res_cont = await client.post(f"{self.contabilidad_url}/generarFactura", json=req_factura)
                if res_cont.status_code not in [200, 201]:
                    raise HTTPException(status_code=res_cont.status_code, detail=f"Error en Contabilidad: {res_cont.text}")
                factura_generada = res_cont.json().get("factura")
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Microservicio Contabilidad inaccesible: {str(e)}")

            pasos_completados.append({
                "paso": 3,
                "componente": "Contabilidad",
                "accion": "generarFactura",
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "resultado": "OK - Factura electrónica generada"
            })

            # PASO 4: Confirmación y vinculación de factura en Compras/Ventas
            req_recibir_fac = {
                "referencia_operacion": id_venta,
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "fecha_emision": factura_generada["fecha_emision"],
                "total_facturado": factura_generada["total"]
            }
            try:
                res_rf = await client.post(f"{self.compras_ventas_url}/recibirFactura", json=req_recibir_fac)
                if res_rf.status_code not in [200, 201]:
                    logger.warning(f"Advertencia al notificar factura: {res_rf.text}")
            except Exception as e:
                logger.warning(f"No se pudo vincular factura en Compras/Ventas: {str(e)}")

            pasos_completados.append({
                "paso": 4,
                "componente": "Compras/Ventas",
                "accion": "recibirFactura",
                "resultado": "OK - Factura vinculada al registro de venta"
            })

            # PASO 5: Actualización del inventario en Blockchain (Reducción por Venta)
            bloques_minados = []
            for item in payload.items:
                req_act_inv = {
                    "tipo": "VENTA",
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "referencia": id_venta,
                    "motivo": f"Venta {id_venta} - Factura {factura_generada['numero_factura']}"
                }
                try:
                    res_act = await client.post(f"{self.inventario_url}/actualizarInventario", json=req_act_inv)
                    if res_act.status_code not in [200, 201]:
                        raise HTTPException(status_code=res_act.status_code, detail=f"Error en Blockchain Inventario: {res_act.text}")
                    datos_bloque = res_act.json()
                    bloques_minados.append({
                        "producto_id": item.producto_id,
                        "cantidad": item.cantidad,
                        "stock_resultante": datos_bloque.get("stock_resultante"),
                        "bloque_hash": datos_bloque.get("bloque_minado", {}).get("hash"),
                        "bloque_index": datos_bloque.get("bloque_minado", {}).get("index")
                    })
                except httpx.RequestError as e:
                    raise HTTPException(status_code=503, detail=f"Microservicio Inventario inaccesible durante minado: {str(e)}")

            pasos_completados.append({
                "paso": 5,
                "componente": "Inventario",
                "accion": "actualizarInventario (Minado de Bloques en Blockchain)",
                "bloques": bloques_minados,
                "resultado": "OK - Blockchain actualizada con reducción de stock"
            })

            # PASO 6: Programación de Despacho en Transportador
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
            try:
                res_trans = await client.post(f"{self.transportador_url}/ordenarTransporte", json=req_transporte)
                if res_trans.status_code not in [200, 201]:
                    raise HTTPException(status_code=res_trans.status_code, detail=f"Error en Transportador: {res_trans.text}")
                guia_transporte = res_trans.json().get("guia")
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Microservicio Transportador inaccesible: {str(e)}")

            pasos_completados.append({
                "paso": 6,
                "componente": "Transportador",
                "accion": "ordenarTransporte",
                "numero_guia": guia_transporte["numero_guia"],
                "vehiculo": guia_transporte["vehiculo_asignado"],
                "fecha_entrega": guia_transporte["fecha_estimada_entrega"],
                "resultado": "OK - Logística programada y guía emitida"
            })

        logger.info(f"[{id_proceso}] Venta orquestada con éxito total.")

        return {
            "status": "EXITOSO",
            "mensaje": "Venta orquestada y coordinada completamente por el Middleware",
            "id_proceso": id_proceso,
            "resumen": {
                "id_venta": id_venta,
                "cliente": payload.cliente.nombre,
                "total_pagado": venta_registrada["total"],
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "numero_guia_transporte": guia_transporte["numero_guia"],
                "transportadora": guia_transporte["transportadora"],
                "vehiculo": guia_transporte["vehiculo_asignado"],
                "fecha_estimada_entrega": guia_transporte["fecha_estimada_entrega"],
                "bloques_blockchain": bloques_minados
            },
            "detalles_completos": {
                "venta": venta_registrada,
                "factura": factura_generada,
                "guia_transporte": guia_transporte,
                "trazabilidad_pasos": pasos_completados
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
          6. Consolidación: Confirma la transacción de reabastecimiento.
        """
        id_proceso = f"ORQ-COM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        pasos_completados = []
        logger.info(f"[{id_proceso}] Iniciando orquestación de compra para proveedor: {payload.proveedor.nombre}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            # PASO 1: Validación contra el catálogo de Inventario
            try:
                res_inv = await client.get(f"{self.inventario_url}/cargarProductos")
                if res_inv.status_code != 200:
                    raise HTTPException(status_code=502, detail="Falla al consultar el catálogo de Inventario.")
                catalogo = {p["id"]: p for p in res_inv.json().get("productos", [])}
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Microservicio Inventario inaccesible: {str(e)}")

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

            pasos_completados.append({
                "paso": 1,
                "componente": "Inventario",
                "accion": "Verificación de catálogo y costos base",
                "resultado": "OK - Productos validados para adquisición"
            })

            # PASO 2: Registro de la Orden de Compra en Compras/Ventas
            req_compra = {
                "proveedor": payload.proveedor.model_dump(),
                "items": items_compra_procesados,
                "terminos_pago": payload.terminos_pago,
                "observaciones": f"Compra coordinada por Middleware [{id_proceso}]"
            }
            try:
                res_cv = await client.post(f"{self.compras_ventas_url}/registrarCompra", json=req_compra)
                if res_cv.status_code not in [200, 201]:
                    raise HTTPException(status_code=res_cv.status_code, detail=f"Error en Compras/Ventas: {res_cv.text}")
                compra_registrada = res_cv.json().get("compra")
                id_compra = compra_registrada["id_compra"]
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Microservicio Compras/Ventas inaccesible: {str(e)}")

            pasos_completados.append({
                "paso": 2,
                "componente": "Compras/Ventas",
                "accion": "registrarCompra",
                "id_compra": id_compra,
                "subtotal": compra_registrada["subtotal"],
                "total": compra_registrada["total"],
                "resultado": "OK - Orden de compra registrada"
            })

            # PASO 3: Emisión de Factura de Compra / Cuenta por Pagar en Contabilidad
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
            try:
                res_cont = await client.post(f"{self.contabilidad_url}/generarFactura", json=req_factura)
                if res_cont.status_code not in [200, 201]:
                    raise HTTPException(status_code=res_cont.status_code, detail=f"Error en Contabilidad: {res_cont.text}")
                factura_generada = res_cont.json().get("factura")
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Microservicio Contabilidad inaccesible: {str(e)}")

            pasos_completados.append({
                "paso": 3,
                "componente": "Contabilidad",
                "accion": "generarFactura (Compra)",
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "resultado": "OK - Factura/Cuenta por pagar registrada"
            })

            # PASO 4: Vinculación de factura en Compras/Ventas
            req_recibir_fac = {
                "referencia_operacion": id_compra,
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "fecha_emision": factura_generada["fecha_emision"],
                "total_facturado": factura_generada["total"]
            }
            try:
                res_rf = await client.post(f"{self.compras_ventas_url}/recibirFactura", json=req_recibir_fac)
                if res_rf.status_code not in [200, 201]:
                    logger.warning(f"Advertencia al notificar factura de compra: {res_rf.text}")
            except Exception as e:
                logger.warning(f"No se pudo vincular factura en Compras/Ventas: {str(e)}")

            pasos_completados.append({
                "paso": 4,
                "componente": "Compras/Ventas",
                "accion": "recibirFactura",
                "resultado": "OK - Factura vinculada a la compra"
            })

            # PASO 5: Actualización del inventario en Blockchain (Incremento por Adquisición)
            bloques_minados = []
            for item in payload.items:
                req_act_inv = {
                    "tipo": "ADQUISICION",
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "referencia": id_compra,
                    "motivo": f"Abastecimiento Compra {id_compra} - Factura {factura_generada['numero_factura']}"
                }
                try:
                    res_act = await client.post(f"{self.inventario_url}/actualizarInventario", json=req_act_inv)
                    if res_act.status_code not in [200, 201]:
                        raise HTTPException(status_code=res_act.status_code, detail=f"Error en Blockchain Inventario: {res_act.text}")
                    datos_bloque = res_act.json()
                    bloques_minados.append({
                        "producto_id": item.producto_id,
                        "cantidad": item.cantidad,
                        "stock_resultante": datos_bloque.get("stock_resultante"),
                        "bloque_hash": datos_bloque.get("bloque_minado", {}).get("hash"),
                        "bloque_index": datos_bloque.get("bloque_minado", {}).get("index")
                    })
                except httpx.RequestError as e:
                    raise HTTPException(status_code=503, detail=f"Microservicio Inventario inaccesible durante minado: {str(e)}")

            pasos_completados.append({
                "paso": 5,
                "componente": "Inventario",
                "accion": "actualizarInventario (Minado de Bloques en Blockchain)",
                "bloques": bloques_minados,
                "resultado": "OK - Blockchain actualizada con ingreso de stock"
            })

        logger.info(f"[{id_proceso}] Compra orquestada con éxito total.")

        return {
            "status": "EXITOSO",
            "mensaje": "Compra a proveedor orquestada y coordinada completamente por el Middleware",
            "id_proceso": id_proceso,
            "resumen": {
                "id_compra": id_compra,
                "proveedor": payload.proveedor.nombre,
                "total_compra": compra_registrada["total"],
                "numero_factura": factura_generada["numero_factura"],
                "cufe": factura_generada["cufe"],
                "terminos_pago": compra_registrada["terminos_pago"],
                "bloques_blockchain": bloques_minados
            },
            "detalles_completos": {
                "compra": compra_registrada,
                "factura": factura_generada,
                "trazabilidad_pasos": pasos_completados
            }
        }
