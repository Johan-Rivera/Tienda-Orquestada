from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from blockchain import BlockchainInventario

app = FastAPI(
    title="Microservicio de Inventario con Blockchain",
    description="Gestiona el catálogo y el stock inmutable de muebles usando una cadena de bloques.",
    version="1.0.0"
)

# Instancia global del ledger blockchain
blockchain = BlockchainInventario()


class ActualizarInventarioRequest(BaseModel):
    tipo: str = Field(..., description="Tipo de movimiento: 'VENTA' o 'ADQUISICION'")
    producto_id: str = Field(..., description="Identificador único del producto, ej. MUE-001")
    cantidad: int = Field(..., gt=0, description="Cantidad a incrementar o reducir")
    referencia: str = Field(..., description="ID de referencia externa (ID Venta o ID Compra)")
    motivo: Optional[str] = Field("", description="Detalle explicativo de la operación")


@app.get("/cargarProductos")
def cargar_productos():
    """
    Método requerido por el esquema coordinado/orquestado:
    Retorna la lista de productos y sus niveles de stock calculados a partir de la blockchain.
    """
    productos = blockchain.obtener_productos_con_stock()
    return {
        "status": "EXITOSO",
        "total_productos": len(productos),
        "productos": productos
    }


@app.get("/cargarRequerimientosProductos")
def cargar_requerimientos_productos():
    """
    Método requerido por el esquema:
    Retorna los requerimientos de productos cuyo inventario está por debajo del stock mínimo.
    Consumido por la orquestación para atención a proveedores.
    """
    requerimientos = blockchain.obtener_requerimientos()
    return {
        "status": "EXITOSO",
        "total_requerimientos": len(requerimientos),
        "requerimientos": requerimientos
    }


@app.post("/actualizarInventario")
def actualizar_inventario(payload: ActualizarInventarioRequest):
    """
    Método requerido por el esquema:
    Registra una adquisición (incremento de stock) o una venta (reducción de stock)
    minando un nuevo bloque inmutable en la blockchain.
    """
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en blockchain: {str(e)}")


@app.get("/blockchain")
def obtener_cadena():
    """
    Permite auditar toda la cadena de bloques y verificar su integridad criptográfica.
    """
    validacion = blockchain.es_cadena_valida()
    return {
        "blockchain_valida": validacion["valida"],
        "info_validacion": validacion,
        "longitud": len(blockchain.chain),
        "cadena": [bloque.to_dict() for bloque in blockchain.chain]
    }
