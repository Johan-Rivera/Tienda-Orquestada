from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DetalleItem(BaseModel):
    producto_id: str = Field(..., description="ID del producto facturado", json_schema_extra={"example": "MUE-001"})
    nombre: str = Field(..., description="Nombre comercial del mueble", json_schema_extra={"example": "Sofá Seccional Cuero 3 Puestos"})
    cantidad: int = Field(..., gt=0, description="Cantidad facturada", json_schema_extra={"example": 2})
    precio_unitario: float = Field(..., gt=0, description="Precio unitario o costo base (COP)", json_schema_extra={"example": 1200000.0})


class GenerarFacturaRequest(BaseModel):
    tipo_operacion: str = Field(
        ...,
        description="Naturaleza de la factura: 'VENTA' (ingreso operacional) o 'COMPRA' (egreso/cuenta por pagar)",
        json_schema_extra={"example": "VENTA"}
    )
    referencia_operacion: str = Field(
        ...,
        description="Identificador de la orden comercial vinculada (ID de Venta o ID de Compra)",
        json_schema_extra={"example": "VEN-20261025-A1B2C3"}
    )
    emisor: str = Field(
        ...,
        description="Razón social e identificación del emisor de la factura",
        json_schema_extra={"example": "Muebles Confort S.A.S. - NIT 901.888.777-1"}
    )
    receptor: str = Field(
        ...,
        description="Razón social o nombre completo del adquirente",
        json_schema_extra={"example": "Carlos Mendoza (CC/NIT: 1018234901)"}
    )
    subtotal: float = Field(..., gt=0, description="Base gravable antes de impuestos (COP)", json_schema_extra={"example": 2400000.0})
    iva: float = Field(..., ge=0, description="Monto del Impuesto al Valor Agregado calculado (COP)", json_schema_extra={"example": 456000.0})
    total: float = Field(..., gt=0, description="Importe total liquidado de la factura (COP)", json_schema_extra={"example": 2856000.0})
    detalles: List[DetalleItem] = Field(..., min_length=1, description="Detalle desagregado de los ítems facturados")
    metodo_pago: Optional[str] = Field("ELECTRONICO", description="Medio de liquidación o término de pago", json_schema_extra={"example": "TRANSFERENCIA_PSE"})


class FacturaModel(BaseModel):
    numero_factura: str = Field(..., description="Consecutivo fiscal único", json_schema_extra={"example": "FE-VEN-1001"})
    cufe: str = Field(..., description="Código Único de Factura Electrónica (SHA-256)", json_schema_extra={"example": "dafab70a662c7879..."})
    tipo_operacion: str = Field(..., description="VENTA o COMPRA")
    referencia_operacion: str = Field(..., description="Referencia de la orden comercial")
    emisor: str = Field(..., description="Emisor fiscal")
    receptor: str = Field(..., description="Receptor fiscal")
    fecha_emision: str = Field(..., description="Marca temporal ISO de expedición")
    subtotal: float = Field(..., description="Subtotal antes de IVA")
    iva: float = Field(..., description="Monto de IVA")
    total: float = Field(..., description="Total facturado")
    metodo_pago: str = Field(..., description="Método o término de pago")
    detalles: List[Dict[str, Any]] = Field(..., description="Ítems facturados")
    estado_tributario: str = Field("VALIDADA_DIAN", description="Estado de validación tributaria")
    estado_pago: str = Field("CONCILIADO", description="Estado contable")


class GenerarFacturaResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado de la emisión")
    mensaje: str = Field(..., description="Mensaje de confirmación")
    factura: FacturaModel = Field(..., description="Comprobante fiscal electrónico generado")


class ListarFacturasResponse(BaseModel):
    total_facturas: int = Field(..., description="Cantidad de facturas emitidas")
    facturas: List[FacturaModel] = Field(..., description="Libro cronológico de facturación electrónica")


class BalanceResponse(BaseModel):
    total_ingresos_ventas: float = Field(..., description="Suma total facturada por ventas a clientes (COP)", json_schema_extra={"example": 3117800.0})
    total_egresos_compras: float = Field(..., description="Suma total facturada por compras a proveedores (COP)", json_schema_extra={"example": 7318500.0})
    balance_neto: float = Field(..., description="Diferencia financiera neta (Ingresos - Egresos)", json_schema_extra={"example": -4200700.0})
    cantidad_facturas_emitidas: int = Field(..., description="Total de comprobantes fiscales procesados", json_schema_extra={"example": 2})
