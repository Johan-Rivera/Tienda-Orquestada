from fastapi import FastAPI, HTTPException, status
from schemas.contabilidad import (
    GenerarFacturaRequest,
    GenerarFacturaResponse,
    ListarFacturasResponse,
    BalanceResponse
)
from services import GestorContable

tags_metadata = [
    {
        "name": "Facturación Electrónica",
        "description": "Emisión y certificación fiscal de comprobantes electrónicos con CUFE para ventas y compras."
    },
    {
        "name": "Finanzas y Contabilidad",
        "description": "Consolidación de ingresos, egresos y balance contable de la tienda de muebles."
    }
]

app = FastAPI(
    title="Microservicio de Contabilidad y Facturación",
    description="""
    Microservicio fiscal encargado de la liquidación y emisión de comprobantes tributarios electrónicos para ventas y compras.
    
    ### Capacidades:
    * **Emisión con CUFE:** Genera automáticamente el Código Único de Facturación Electrónica mediante hash criptográfico SHA-256.
    * **Consecutivos Fiscales:** Maneja series y consecutivos diferenciados (`FE-VEN` para ventas y `FE-COM` para adquisiciones).
    * **Balance Financiero:** Totaliza en tiempo real ingresos operacionales, costos por compras y utilidad neta contable.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Instancia global del servicio contable orientado a objetos (POO)
gestor_contable = GestorContable()


@app.post(
    "/generarFactura",
    response_model=GenerarFacturaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Emitir factura electrónica contable",
    description="Genera el comprobante electrónico fiscal para una operación de venta a cliente o de compra a proveedor, asignando un número consecutivo único y calculando el código de validación CUFE con algoritmo SHA-256.",
    responses={
        400: {"description": "Tipo de operación no admitido o montos inconsistentes."}
    },
    tags=["Facturación Electrónica"]
)
def generar_factura(payload: GenerarFacturaRequest):
    try:
        return gestor_contable.generar_factura(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get(
    "/facturas",
    response_model=ListarFacturasResponse,
    summary="Listar facturas electrónicas emitidas",
    description="Consulta el libro contable con el total de facturas electrónicas expedidas en el sistema.",
    tags=["Facturación Electrónica"]
)
def listar_facturas():
    facturas = gestor_contable.listar_facturas()
    return {
        "total_facturas": len(facturas),
        "facturas": facturas
    }


@app.get(
    "/balance",
    response_model=BalanceResponse,
    summary="Consultar balance financiero consolidado",
    description="Calcula y retorna en tiempo real el balance financiero del almacén, consolidando el total de ingresos por ventas, egresos por compras a proveedores y la diferencia neta resultante.",
    tags=["Finanzas y Contabilidad"]
)
def obtener_balance_financiero():
    return gestor_contable.obtener_balance()
