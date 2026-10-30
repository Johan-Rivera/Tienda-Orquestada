from fastapi import FastAPI, HTTPException, status
from blockchain import BlockchainInventario
from schemas.inventario import (
    ActualizarInventarioRequest,
    CargarProductosResponse,
    CargarRequerimientosResponse,
    ActualizarInventarioResponse,
    BlockchainResponse
)

tags_metadata = [
    {
        "name": "Catálogo e Inventario",
        "description": "Consultas del catálogo de productos y existencias calculadas en tiempo real desde la Blockchain."
    },
    {
        "name": "Operaciones y Ledger",
        "description": "Registro transaccional de adquisiciones y ventas mediante minado Proof-of-Work (PoW)."
    }
]

app = FastAPI(
    title="Microservicio de Inventario con Blockchain",
    description="""
    Microservicio autónomo encargado de administrar el catálogo de muebles y la trazabilidad inmutable de existencias.
    
    ### Características Principales:
    * **Ledger Inmutable:** Cada ingreso o salida se registra en bloques encadenados criptográficamente mediante SHA-256.
    * **Consenso Proof of Work (PoW):** Algoritmo de prueba de trabajo para sellar cada bloque.
    * **Cálculo de Existencias en Vivo:** El stock no es un valor estático editable, sino el resultado del cálculo de las transacciones acumuladas en la cadena.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Instancia global del ledger blockchain
blockchain = BlockchainInventario()


@app.get(
    "/cargarProductos",
    response_model=CargarProductosResponse,
    summary="Consultar catálogo de muebles y stock en Blockchain",
    description="Calcula y retorna la lista completa de productos del almacén junto con sus existencias disponibles en tiempo real, derivadas directamente del historial inmutable de la Blockchain.",
    tags=["Catálogo e Inventario"]
)
def cargar_productos():
    productos = blockchain.obtener_productos_con_stock()
    return {
        "status": "EXITOSO",
        "total_productos": len(productos),
        "productos": productos
    }


@app.get(
    "/cargarRequerimientosProductos",
    response_model=CargarRequerimientosResponse,
    summary="Consultar necesidades de abastecimiento por bajo stock",
    description="Identifica de forma automática los productos cuyo inventario se encuentra en o por debajo del umbral mínimo de seguridad, calculando las cantidades sugeridas a ordenar a los proveedores.",
    tags=["Catálogo e Inventario"]
)
def cargar_requerimientos_productos():
    requerimientos = blockchain.obtener_requerimientos()
    return {
        "status": "EXITOSO",
        "total_requerimientos": len(requerimientos),
        "requerimientos": requerimientos
    }


@app.post(
    "/actualizarInventario",
    response_model=ActualizarInventarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar movimiento y minar bloque en Blockchain",
    description="""
    Registra una operación de inventario de tipo:
    * **ADQUISICION:** Incrementa las existencias a partir de una orden de compra o abastecimiento de proveedor.
    * **VENTA:** Reduce las existencias a raíz de una compra de cliente, validando previamente que exista suficiente disponibilidad.
    
    Cada operación ejecuta el algoritmo de consenso Proof of Work (PoW) y genera un nuevo bloque con hash SHA-256 en la cadena inmutable.
    """,
    responses={
        400: {"description": "Datos de entrada inválidos o stock insuficiente para concretar la venta."},
        500: {"description": "Fallo interno durante el proceso criptográfico de minado."}
    },
    tags=["Operaciones y Ledger"]
)
def actualizar_inventario(payload: ActualizarInventarioRequest):
    try:
        resultado = blockchain.registrar_operacion(
            tipo=payload.tipo,
            producto_id=payload.producto_id,
            cantidad=payload.cantidad,
            referencia=payload.referencia,
            motivo=payload.motivo or ""
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno en blockchain: {str(e)}")


@app.get(
    "/blockchain",
    response_model=BlockchainResponse,
    summary="Auditar integridad criptográfica de la Blockchain",
    description="Inspecciona toda la cadena de bloques desde el bloque génesis, recalculando hashes previos y proofs para certificar la integridad matemática inalterada del inventario.",
    tags=["Operaciones y Ledger"]
)
def obtener_cadena():
    validacion = blockchain.es_cadena_valida()
    return {
        "blockchain_valida": validacion["valida"],
        "info_validacion": validacion,
        "longitud": len(blockchain.chain),
        "cadena": [bloque.to_dict() for bloque in blockchain.chain]
    }
