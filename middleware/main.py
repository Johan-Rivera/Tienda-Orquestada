from fastapi import FastAPI, status
from schemas.middleware import (
    RegistrarVentaRequest,
    RegistrarCompraRequest,
    OrquestarVentaResponse,
    OrquestarCompraResponse
)
from orchestrator import OrquestadorMiddleware
import socket

tags_metadata = [
    {
        "name": "Orquestación de Ventas",
        "description": "Flujo distribuido de venta: validación de existencias en Blockchain, orden comercial, emisión de factura electrónica con CUFE, minado de reducción de stock y despacho logístico."
    },
    {
        "name": "Orquestación de Compras",
        "description": "Flujo distribuido de abastecimiento con proveedores: validación de catálogo, orden de compra, comprobante contable con CUFE y minado de ingreso de stock en Blockchain."
    },
    {
        "name": "Consultas de Inventario",
        "description": "Consultas centralizadas hacia la Blockchain de Inventario para visualización de catálogo y detección de productos con stock crítico."
    }
]

app = FastAPI(
    title="Middleware Orquestador Central",
    description="""
    ## Sistema Distribuido de la Tienda de Muebles
    
    Este componente es el **director orquestador** de la arquitectura distribuida. Provee una interfaz unificada para que cualquier cliente, portal o desarrollador interactúe con el ecosistema sin tener que coordinar microservicios de manera manual.
    
    ### Flujos Coordinados:
    1. **Venta a Clientes (`POST /registrarVenta`):**
       - **Paso 1:** Valida disponibilidad en tiempo real contra el ledger inmutable de la Blockchain (`Inventario`).
       - **Paso 2:** Genera la orden mercantil con liquidación de impuestos (`Compras/Ventas`).
       - **Paso 3:** Emite la Factura Electrónica legal con código CUFE (SHA-256) ante la DIAN (`Contabilidad`).
       - **Paso 4:** Vincula el número fiscal a la orden comercial (`Compras/Ventas`).
       - **Paso 5:** Mina un nuevo bloque con algoritmo Proof-of-Work (PoW) reduciendo el stock (`Inventario`).
       - **Paso 6:** Asigna vehículo de carga, ruta metropolitana y emite la guía de entrega (`Transportador`).
       
    2. **Compra a Proveedores (`POST /registrarCompra`):**
       - **Paso 1:** Valida los productos contra el catálogo corporativo (`Inventario`).
       - **Paso 2:** Emite la orden mercantil de compra con plazos acordados (`Compras/Ventas`).
       - **Paso 3:** Emite la factura contable de cuenta por pagar con CUFE (`Contabilidad`).
       - **Paso 4:** Asocia la factura a la orden mercantil (`Compras/Ventas`).
       - **Paso 5:** Mina un nuevo bloque PoW aumentando las existencias de forma inmutable (`Inventario`).
    """,
    version="1.0.0",
    openapi_tags=tags_metadata
)

def resolver_url_servicio(docker_name: str, puerto: int) -> str:
    """Detecta si está dentro de la red Docker o en host local"""
    try:
        socket.gethostbyname(docker_name)
        return f"http://{docker_name}:{puerto}"
    except Exception:
        return f"http://localhost:{puerto}"

# URLs dinámicas de los microservicios
INVENTARIO_URL = resolver_url_servicio("inventario", 8001)
COMPRAS_VENTAS_URL = resolver_url_servicio("compras-ventas", 8002)
CONTABILIDAD_URL = resolver_url_servicio("contabilidad", 8003)
TRANSPORTADOR_URL = resolver_url_servicio("transportador", 8004)

# Instancia global del Orquestador
orquestador = OrquestadorMiddleware(
    inventario_url=INVENTARIO_URL,
    compras_ventas_url=COMPRAS_VENTAS_URL,
    contabilidad_url=CONTABILIDAD_URL,
    transportador_url=TRANSPORTADOR_URL
)


@app.get(
    "/cargarProductos",
    summary="Consultar catálogo de muebles y existencias en Inventario",
    description="Consulta al microservicio de Inventario para computar y retornar las existencias disponibles de todos los muebles, calculadas a partir del historial inmutable de transacciones en la Blockchain.",
    tags=["Consultas de Inventario"]
)
async def cargar_productos():
    return await orquestador.cargar_productos()


@app.get(
    "/cargarRequerimientosProductos",
    summary="Consultar requerimientos de abastecimiento por bajo stock",
    description="Consulta al microservicio de Inventario los artículos que se encuentran en o por debajo del stock mínimo de seguridad, sugiriendo las cantidades a ordenar para reabastecer el almacén.",
    tags=["Consultas de Inventario"]
)
async def cargar_requerimientos_productos():
    return await orquestador.cargar_requerimientos_productos()


@app.post(
    "/registrarVenta",
    response_model=OrquestarVentaResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar venta a cliente y emitir factura electrónica",
    description="Coordina el flujo distribuido de la venta (validación de stock en Blockchain, orden mercantil, facturación electrónica con CUFE, minado de existencias y logística), retornando la factura con los datos esenciales de la transacción y entrega para el cliente.",
    responses={
        400: {"description": "Stock insuficiente en Blockchain o producto no catalogado."},
        502: {"description": "Falla de comunicación con alguno de los microservicios participantes."},
        503: {"description": "Microservicio indispensable inaccesible."}
    },
    tags=["Orquestación de Ventas"]
)
async def registrar_venta(payload: RegistrarVentaRequest):
    return await orquestador.registrar_venta(payload)


@app.post(
    "/registrarCompra",
    response_model=OrquestarCompraResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar orden de abastecimiento y emitir comprobante de compra",
    description="Coordina el flujo distribuido de reabastecimiento (validación de catálogo, orden de compra, facturación contable con CUFE y minado de ingreso en Blockchain), retornando el comprobante con los datos esenciales de la compra para el proveedor.",
    responses={
        400: {"description": "Producto no existente en catálogo o costo inválido."},
        502: {"description": "Falla de comunicación con los microservicios."},
        503: {"description": "Microservicio indispensable inaccesible."}
    },
    tags=["Orquestación de Compras"]
)
async def registrar_compra(payload: RegistrarCompraRequest):
    return await orquestador.registrar_compra(payload)
