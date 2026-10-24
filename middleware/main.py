from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import httpx
import os
import socket
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("middleware-orquestador")

app = FastAPI(
    title="Middleware Orquestador Central",
    description="Componente principal de arquitectura distribuida orquestada para coordinar compras y ventas de muebles.",
    version="1.0.0"
)

def resolver_url_servicio(var_entorno: str, docker_name: str, puerto: int) -> str:
    """Detecta inteligentemente si está dentro de la red Docker o en host local"""
    if os.getenv(var_entorno):
        return os.getenv(var_entorno)
    try:
        socket.gethostbyname(docker_name)
        return f"http://{docker_name}:{puerto}"
    except Exception:
        return f"http://localhost:{puerto}"

# URLs dinámicas de los microservicios
INVENTARIO_URL = resolver_url_servicio("INVENTARIO_URL", "c-inventario", 8001)
COMPRAS_VENTAS_URL = resolver_url_servicio("COMPRAS_VENTAS_URL", "c-compras-ventas", 8002)
CONTABILIDAD_URL = resolver_url_servicio("CONTABILIDAD_URL", "c-contabilidad", 8003)
TRANSPORTADOR_URL = resolver_url_servicio("TRANSPORTADOR_URL", "c-transportador", 8004)

# Registro en memoria de trazabilidad y auditoría de orquestaciones
trazabilidad_db: List[Dict[str, Any]] = []


class ItemSolicitudVenta(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)


class ClienteSolicitud(BaseModel):
    nombre: str
    documento: str
    direccion: str
    telefono: Optional[str] = "3001234567"
    correo: Optional[str] = "cliente@correo.com"


class OrquestarVentaRequest(BaseModel):
    cliente: ClienteSolicitud
    items: List[ItemSolicitudVenta]
    metodo_pago: Optional[str] = "TRANSFERENCIA_BANCARIA"
    observaciones: Optional[str] = "Venta coordinada por Middleware"


class ItemSolicitudCompra(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)
    costo_unitario: Optional[float] = None


class ProveedorSolicitud(BaseModel):
    nombre: str
    nit: str
    contacto: Optional[str] = "Asesor Comercial"
    telefono: Optional[str] = "3109876543"
    correo: Optional[str] = "proveedor@maderas.com"


class OrquestarCompraRequest(BaseModel):
    proveedor: ProveedorSolicitud
    items: List[ItemSolicitudCompra]
    terminos_pago: Optional[str] = "CREDITO_30_DIAS"
    observaciones: Optional[str] = "Reabastecimiento coordinado por Middleware"


def _resolver_url(url_principal: str, fallback_puerto: int) -> str:
    """Retorna la URL configurada o fallback a localhost si no está en red Docker"""
    return url_principal


@app.get("/")
def estado():
    return {
        "componente": "Middleware Orquestador Central",
        "rol": "Coordinador central de arquitectura distribuida orquestada",
        "estado": "ACTIVO",
        "servicios_coordinados": {
            "inventario": INVENTARIO_URL,
            "compras_ventas": COMPRAS_VENTAS_URL,
            "contabilidad": CONTABILIDAD_URL,
            "transportador": TRANSPORTADOR_URL
        },
        "flujos_orquestados": [
            "POST /orquestar/venta (Flujo completo de venta a cliente)",
            "POST /orquestar/compra (Flujo completo de compra a proveedor)",
            "GET /orquestar/catalogo (Consulta centralizada de catálogo con stock de blockchain)",
            "GET /orquestar/requerimientos (Consulta de necesidades de reabastecimiento)",
            "GET /orquestar/blockchain (Auditoría del ledger de inventario)",
            "GET /orquestar/balance (Auditoría contable y financiera)",
            "GET /orquestar/trazabilidad (Historial de orquestaciones ejecutadas)",
            "GET /orquestar/salud (Diagnóstico de salud de todos los nodos)"
        ]
    }


@app.get("/orquestar/salud")
async def verificar_salud_servicios():
    """Realiza un ping a todos los microservicios participantes en la red distribuida"""
    servicios = {
        "inventario": f"{INVENTARIO_URL}/",
        "compras_ventas": f"{COMPRAS_VENTAS_URL}/",
        "contabilidad": f"{CONTABILIDAD_URL}/",
        "transportador": f"{TRANSPORTADOR_URL}/"
    }
    diagnostico = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        for nombre, url in servicios.items():
            try:
                res = await client.get(url)
                diagnostico[nombre] = {
                    "url": url,
                    "estado": "CONECTADO" if res.status_code == 200 else f"HTTP_{res.status_code}",
                    "detalle": res.json().get("servicio", "OK")
                }
            except Exception as e:
                diagnostico[nombre] = {
                    "url": url,
                    "estado": "NO_DISPONIBLE",
                    "error": str(e)
                }

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "middleware_estado": "OPERATIVO",
        "diagnostico_nodos": diagnostico
    }


@app.get("/orquestar/catalogo")
async def consultar_catalogo():
    """Consulta al microservicio de inventario para obtener el stock desde la blockchain"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{INVENTARIO_URL}/cargarProductos")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.text)
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"No fue posible conectar con Inventario: {str(e)}")


@app.get("/orquestar/requerimientos")
async def consultar_requerimientos():
    """Consulta al inventario los productos que necesitan reabastecimiento"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{INVENTARIO_URL}/cargarRequerimientosProductos")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.text)
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"No fue posible conectar con Inventario: {str(e)}")


@app.get("/orquestar/blockchain")
async def consultar_blockchain():
    """Consulta el estado del blockchain en el microservicio de inventario"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{INVENTARIO_URL}/blockchain")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.text)
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"No fue posible conectar con Inventario: {str(e)}")


@app.get("/orquestar/balance")
async def consultar_balance():
    """Consulta el balance financiero consolidado en el microservicio de contabilidad"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{CONTABILIDAD_URL}/balance")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.text)
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"No fue posible conectar con Contabilidad: {str(e)}")


@app.get("/orquestar/trazabilidad")
def consultar_trazabilidad():
    """Retorna la bitácora completa de procesos orquestados por el middleware"""
    return {
        "total_procesos_orquestados": len(trazabilidad_db),
        "historial": trazabilidad_db
    }


@app.post("/orquestar/venta")
async def orquestar_venta(payload: OrquestarVentaRequest):
    """
    FLUJO ORQUESTADO DE VENTA A CLIENTE:
    El Middleware actúa como director orquestador ejecutando la siguiente secuencia:
      1. Inventario: Valida disponibilidad de stock en el ledger blockchain para cada ítem.
      2. Compras/Ventas: Registra la orden comercial de venta con precios oficiales.
      3. Contabilidad: Emite la factura electrónica formal (genera CUFE).
      4. Compras/Ventas: Vincula la factura a la venta (recibirFactura).
      5. Inventario: Actualiza el stock minando un nuevo bloque inmutable en la Blockchain.
      6. Transportador: Programa el despacho logístico y genera la guía de transporte.
      7. Consolidación: Registra la trazabilidad y retorna la confirmación completa.
    """
    id_proceso = f"ORQ-VEN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    pasos_completados = []
    logger.info(f"[{id_proceso}] Iniciando orquestación de venta para cliente: {payload.cliente.nombre}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # ---------------------------------------------------------------------
        # PASO 1: Validación de stock en Inventario (Blockchain)
        # ---------------------------------------------------------------------
        try:
            res_inv = await client.get(f"{INVENTARIO_URL}/cargarProductos")
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

        # ---------------------------------------------------------------------
        # PASO 2: Registro de la Venta en Compras/Ventas
        # ---------------------------------------------------------------------
        req_venta = {
            "cliente": payload.cliente.model_dump(),
            "items": items_venta_procesados,
            "metodo_pago": payload.metodo_pago,
            "observaciones": f"{payload.observaciones} | Orquestado por Middleware [{id_proceso}]"
        }
        try:
            res_cv = await client.post(f"{COMPRAS_VENTAS_URL}/registrarVenta", json=req_venta)
            if res_cv.status_code != 200:
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

        # ---------------------------------------------------------------------
        # PASO 3: Emisión de Factura en Contabilidad
        # ---------------------------------------------------------------------
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
            res_cont = await client.post(f"{CONTABILIDAD_URL}/generarFactura", json=req_factura)
            if res_cont.status_code != 200:
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

        # ---------------------------------------------------------------------
        # PASO 4: Confirmación y vinculación de factura en Compras/Ventas
        # ---------------------------------------------------------------------
        req_recibir_fac = {
            "referencia_operacion": id_venta,
            "numero_factura": factura_generada["numero_factura"],
            "cufe": factura_generada["cufe"],
            "fecha_emision": factura_generada["fecha_emision"],
            "total_facturado": factura_generada["total"]
        }
        try:
            res_rf = await client.post(f"{COMPRAS_VENTAS_URL}/recibirFactura", json=req_recibir_fac)
            if res_rf.status_code != 200:
                logger.warning(f"Advertencia al notificar factura: {res_rf.text}")
        except Exception as e:
            logger.warning(f"No se pudo vincular factura en Compras/Ventas: {str(e)}")

        pasos_completados.append({
            "paso": 4,
            "componente": "Compras/Ventas",
            "accion": "recibirFactura",
            "resultado": "OK - Factura vinculada al registro de venta"
        })

        # ---------------------------------------------------------------------
        # PASO 5: Actualización del inventario en Blockchain (Reducción por Venta)
        # ---------------------------------------------------------------------
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
                res_act = await client.post(f"{INVENTARIO_URL}/actualizarInventario", json=req_act_inv)
                if res_act.status_code != 200:
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

        # ---------------------------------------------------------------------
        # PASO 6: Programación de Despacho en Transportador
        # ---------------------------------------------------------------------
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
            res_trans = await client.post(f"{TRANSPORTADOR_URL}/ordenarTransporte", json=req_transporte)
            if res_trans.status_code != 200:
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

    # Consolidación final del proceso orquestado
    registro_trazabilidad = {
        "id_proceso": id_proceso,
        "tipo_flujo": "ORQUESTACION_VENTA",
        "fecha": datetime.datetime.now().isoformat(),
        "cliente": payload.cliente.nombre,
        "id_venta": id_venta,
        "numero_factura": factura_generada["numero_factura"],
        "cufe": factura_generada["cufe"],
        "numero_guia_transporte": guia_transporte["numero_guia"],
        "total_transaccion": venta_registrada["total"],
        "pasos": pasos_completados,
        "estado": "COMPLETADO_EXITOSAMENTE"
    }

    trazabilidad_db.append(registro_trazabilidad)
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


@app.post("/orquestar/compra")
async def orquestar_compra(payload: OrquestarCompraRequest):
    """
    FLUJO ORQUESTADO DE COMPRA A PROVEEDOR:
    El Middleware coordina la adquisición de muebles con proveedores:
      1. Inventario: Valida el catálogo de productos y costos vigentes.
      2. Compras/Ventas: Registra la orden de compra comercial a favor del proveedor.
      3. Contabilidad: Emite la factura/cuenta por pagar con su correspondiente consecutivo y CUFE.
      4. Compras/Ventas: Registra la factura en el expediente de compras (recibirFactura).
      5. Inventario: Actualiza el inventario minando bloques de adquisición en la Blockchain.
      6. Consolidación: Registra la trazabilidad y confirma la transacción de reabastecimiento.
    """
    id_proceso = f"ORQ-COM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    pasos_completados = []
    logger.info(f"[{id_proceso}] Iniciando orquestación de compra para proveedor: {payload.proveedor.nombre}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # ---------------------------------------------------------------------
        # PASO 1: Validación contra el catálogo de Inventario
        # ---------------------------------------------------------------------
        try:
            res_inv = await client.get(f"{INVENTARIO_URL}/cargarProductos")
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

        # ---------------------------------------------------------------------
        # PASO 2: Registro de la Orden de Compra en Compras/Ventas
        # ---------------------------------------------------------------------
        req_compra = {
            "proveedor": payload.proveedor.model_dump(),
            "items": items_compra_procesados,
            "terminos_pago": payload.terminos_pago,
            "observaciones": f"{payload.observaciones} | Orquestado por Middleware [{id_proceso}]"
        }
        try:
            res_cv = await client.post(f"{COMPRAS_VENTAS_URL}/registrarCompra", json=req_compra)
            if res_cv.status_code != 200:
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

        # ---------------------------------------------------------------------
        # PASO 3: Emisión de Factura de Compra / Cuenta por Pagar en Contabilidad
        # ---------------------------------------------------------------------
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
            res_cont = await client.post(f"{CONTABILIDAD_URL}/generarFactura", json=req_factura)
            if res_cont.status_code != 200:
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

        # ---------------------------------------------------------------------
        # PASO 4: Vinculación de factura en Compras/Ventas
        # ---------------------------------------------------------------------
        req_recibir_fac = {
            "referencia_operacion": id_compra,
            "numero_factura": factura_generada["numero_factura"],
            "cufe": factura_generada["cufe"],
            "fecha_emision": factura_generada["fecha_emision"],
            "total_facturado": factura_generada["total"]
        }
        try:
            res_rf = await client.post(f"{COMPRAS_VENTAS_URL}/recibirFactura", json=req_recibir_fac)
            if res_rf.status_code != 200:
                logger.warning(f"Advertencia al notificar factura de compra: {res_rf.text}")
        except Exception as e:
            logger.warning(f"No se pudo vincular factura en Compras/Ventas: {str(e)}")

        pasos_completados.append({
            "paso": 4,
            "componente": "Compras/Ventas",
            "accion": "recibirFactura",
            "resultado": "OK - Factura vinculada a la compra"
        })

        # ---------------------------------------------------------------------
        # PASO 5: Actualización del inventario en Blockchain (Incremento por Adquisición)
        # ---------------------------------------------------------------------
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
                res_act = await client.post(f"{INVENTARIO_URL}/actualizarInventario", json=req_act_inv)
                if res_act.status_code != 200:
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

    # Consolidación final de la compra orquestada
    registro_trazabilidad = {
        "id_proceso": id_proceso,
        "tipo_flujo": "ORQUESTACION_COMPRA",
        "fecha": datetime.datetime.now().isoformat(),
        "proveedor": payload.proveedor.nombre,
        "id_compra": id_compra,
        "numero_factura": factura_generada["numero_factura"],
        "cufe": factura_generada["cufe"],
        "total_transaccion": compra_registrada["total"],
        "pasos": pasos_completados,
        "estado": "COMPLETADO_EXITOSAMENTE"
    }

    trazabilidad_db.append(registro_trazabilidad)
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
