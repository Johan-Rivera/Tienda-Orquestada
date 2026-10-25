from fastapi import FastAPI, HTTPException, status
from schemas.compras_ventas import (
    RegistrarVentaRequest,
    RegistrarCompraRequest,
    RecibirFacturaRequest,
    RegistrarVentaResponse,
    RegistrarCompraResponse,
    RecibirFacturaResponse,
    ListarVentasResponse,
    ListarComprasResponse
)
from services import GestorComprasVentas

tags_metadata = [
    {
        "name": "Ventas",
        "description": "Gestión de contratos y órdenes mercantiles de venta a clientes."
    },
    {
        "name": "Compras",
        "description": "Gestión de órdenes mercantiles de adquisición y reabastecimiento con proveedores."
    },
    {
        "name": "Facturación y Control",
        "description": "Vinculación y conciliación de facturas electrónicas con operaciones mercantiles."
    }
]

app = FastAPI(
    title="Microservicio de Compras y Ventas",
    description="""
    Microservicio encargado del registro comercial de órdenes de compra a proveedores y órdenes de venta a clientes.
    
    ### Funcionalidades:
    * **Cálculo Tributario Comercial:** Aplica cálculo automático de subtotal, IVA (19%) y total general.
    * **Conciliación Contable:** Vincula las órdenes mercantiles con las facturas emitidas por el área de Contabilidad.
    * **Trazabilidad de Estados:** Mantiene el estado del ciclo de vida de cada orden (`REGISTRADA`, `FACTURADA`).
    """,
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Instancia global del servicio comercial orientado a objetos (POO)
gestor_compras_ventas = GestorComprasVentas()


@app.post(
    "/registrarVenta",
    response_model=RegistrarVentaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar orden comercial de venta",
    description="Genera y almacena una nueva orden de venta a nombre de un cliente, calculando el subtotal, el impuesto al valor agregado (IVA 19%) y el total general a pagar.",
    responses={
        400: {"description": "Solicitud inválida o lista de artículos vacía."}
    },
    tags=["Ventas"]
)
def registrar_venta(payload: RegistrarVentaRequest):
    try:
        return gestor_compras_ventas.registrar_venta(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post(
    "/registrarCompra",
    response_model=RegistrarCompraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar orden comercial de compra a proveedor",
    description="Genera y registra una nueva orden de abastecimiento con un proveedor, calculando el costo total, IVA correspondiente y estipulando los plazos de pago comercial acordados.",
    responses={
        400: {"description": "Solicitud inválida o lista de artículos de compra vacía."}
    },
    tags=["Compras"]
)
def registrar_compra(payload: RegistrarCompraRequest):
    try:
        return gestor_compras_ventas.registrar_compra(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post(
    "/recibirFactura",
    response_model=RecibirFacturaResponse,
    summary="Vincular factura electrónica a una orden comercial",
    description="Recibe los datos de la factura fiscal emitida por Contabilidad (número de factura, código CUFE y fecha de emisión) y los asocia a la orden comercial de venta o compra correspondiente, actualizando su estado a 'FACTURADA'.",
    responses={
        404: {"description": "No se encontró ninguna orden de venta o compra con la referencia indicada."}
    },
    tags=["Facturación y Control"]
)
def recibir_factura(payload: RecibirFacturaRequest):
    resultado = gestor_compras_ventas.recibir_factura(payload)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró operación comercial con referencia '{payload.referencia_operacion}'."
        )
    return resultado


@app.get(
    "/ventas",
    response_model=ListarVentasResponse,
    summary="Listar histórico de ventas",
    description="Retorna el listado completo de todas las ventas registradas en el sistema.",
    tags=["Ventas"]
)
def listar_ventas():
    ventas = gestor_compras_ventas.listar_ventas()
    return {
        "total": len(ventas),
        "ventas": ventas
    }


@app.get(
    "/compras",
    response_model=ListarComprasResponse,
    summary="Listar histórico de compras",
    description="Retorna el listado completo de todas las órdenes de compra a proveedores registradas en el sistema.",
    tags=["Compras"]
)
def listar_compras():
    compras = gestor_compras_ventas.listar_compras()
    return {
        "total": len(compras),
        "compras": compras
    }
