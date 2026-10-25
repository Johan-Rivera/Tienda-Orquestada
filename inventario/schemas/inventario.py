from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ActualizarInventarioRequest(BaseModel):
    tipo: str = Field(
        ...,
        description="Tipo de operación sobre el inventario. Debe ser 'VENTA' (reducción) o 'ADQUISICION' (incremento)",
        json_schema_extra={"example": "VENTA"}
    )
    producto_id: str = Field(
        ...,
        description="Identificador único del producto en el catálogo (ej. MUE-001, MUE-002)",
        json_schema_extra={"example": "MUE-001"}
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description="Cantidad entera de unidades a incrementar o reducir (debe ser mayor a cero)",
        json_schema_extra={"example": 2}
    )
    referencia: str = Field(
        ...,
        description="Código o identificador de referencia externa que origina la transacción (ej. ID de venta o ID de compra)",
        json_schema_extra={"example": "VEN-20261025-A1B2C3"}
    )
    motivo: Optional[str] = Field(
        "",
        description="Descripción o justificación detallada de la operación para fines de auditoría",
        json_schema_extra={"example": "Venta en línea - Factura FE-VEN-1001"}
    )


class ProductoItem(BaseModel):
    id: str = Field(..., description="Identificador único del producto", json_schema_extra={"example": "MUE-001"})
    nombre: str = Field(..., description="Nombre comercial del mueble", json_schema_extra={"example": "Sofá Seccional Cuero 3 Puestos"})
    categoria: str = Field(..., description="Categoría del mueble (Sala, Comedor, etc.)", json_schema_extra={"example": "Sala"})
    precio_unitario: float = Field(..., description="Precio de venta al público (COP)", json_schema_extra={"example": 1200000.0})
    costo_unitario: float = Field(..., description="Costo de adquisición al proveedor (COP)", json_schema_extra={"example": 750000.0})
    stock_actual: int = Field(..., description="Existencias disponibles computadas a partir del ledger Blockchain", json_schema_extra={"example": 8})
    stock_minimo: int = Field(..., description="Nivel mínimo de existencias antes de disparar reabastecimiento", json_schema_extra={"example": 4})
    requiere_reabastecimiento: bool = Field(..., description="Indica si el stock actual es menor o igual al stock mínimo", json_schema_extra={"example": False})


class CargarProductosResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado de la consulta")
    total_productos: int = Field(..., description="Cantidad de productos retornados")
    productos: List[ProductoItem] = Field(..., description="Listado de productos con existencias auditadas en Blockchain")


class RequerimientoItem(BaseModel):
    producto_id: str = Field(..., description="ID del producto en déficit", json_schema_extra={"example": "MUE-005"})
    nombre: str = Field(..., description="Nombre del mueble", json_schema_extra={"example": "Mesa de Centro Rústica Pino"})
    categoria: str = Field(..., description="Categoría", json_schema_extra={"example": "Sala"})
    stock_actual: int = Field(..., description="Stock actual disponible en Blockchain", json_schema_extra={"example": 2})
    stock_minimo: int = Field(..., description="Umbral mínimo configurado", json_schema_extra={"example": 4})
    cantidad_sugerida: int = Field(..., description="Cantidad sugerida a ordenar al proveedor", json_schema_extra={"example": 6})
    costo_estimado_unitario: float = Field(..., description="Costo unitario referencial (COP)", json_schema_extra={"example": 130000.0})
    urgencia: str = Field(..., description="Nivel de urgencia ('ALTA' si stock=0, 'MEDIA' si stock <= mínimo)", json_schema_extra={"example": "MEDIA"})


class CargarRequerimientosResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado de la consulta")
    total_requerimientos: int = Field(..., description="Cantidad de productos que requieren reabastecimiento")
    requerimientos: List[RequerimientoItem] = Field(..., description="Lista de requerimientos para abastecimiento de proveedores")


class BloqueResponse(BaseModel):
    index: int = Field(..., description="Índice del bloque en la cadena", json_schema_extra={"example": 1})
    timestamp: float = Field(..., description="Timestamp Unix de creación")
    fecha_legible: str = Field(..., description="Fecha y hora legible", json_schema_extra={"example": "2026-10-25 12:30:00"})
    transacciones: List[Dict[str, Any]] = Field(..., description="Transacciones selladas dentro del bloque")
    previous_hash: str = Field(..., description="Hash SHA-256 del bloque predecesor", json_schema_extra={"example": "03c3ff2bb4786f8a41dd83c27614e2dd..."})
    proof: int = Field(..., description="Nonce obtenido mediante Proof of Work", json_schema_extra={"example": 226})
    hash: str = Field(..., description="Hash criptográfico SHA-256 inmutable del bloque", json_schema_extra={"example": "94ef4709d7435eb4ba278a0942758ee6..."})


class ActualizarInventarioResponse(BaseModel):
    status: str = Field("EXITOSO", description="Resultado de la operación")
    tipo_operacion: str = Field(..., description="Tipo de movimiento registrado")
    producto_id: str = Field(..., description="ID del producto afectado")
    cantidad: int = Field(..., description="Cantidad movilizada")
    stock_anterior: int = Field(..., description="Stock previo a la transacción")
    stock_resultante: int = Field(..., description="Nuevo stock calculado tras la operación")
    bloque_minado: BloqueResponse = Field(..., description="Bloque sellado y agregado a la Blockchain")


class BlockchainResponse(BaseModel):
    blockchain_valida: bool = Field(..., description="Indica si la integridad de la cadena es matemáticamente válida", json_schema_extra={"example": True})
    info_validacion: Dict[str, Any] = Field(..., description="Detalles del análisis criptográfico")
    longitud: int = Field(..., description="Número total de bloques en el ledger", json_schema_extra={"example": 5})
    cadena: List[BloqueResponse] = Field(..., description="Cadena cronológica inmutable de bloques")
