from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ItemVenta(BaseModel):
    producto_id: str = Field(..., description="ID del producto a vender", json_schema_extra={"example": "MUE-001"})
    nombre: str = Field(..., description="Nombre comercial del mueble", json_schema_extra={"example": "Sofá Seccional Cuero 3 Puestos"})
    cantidad: int = Field(..., gt=0, description="Cantidad de unidades vendidas", json_schema_extra={"example": 2})
    precio_unitario: float = Field(..., gt=0, description="Precio unitario de venta (COP)", json_schema_extra={"example": 1200000.0})


class ClienteInfo(BaseModel):
    nombre: str = Field(..., description="Nombre completo del cliente", json_schema_extra={"example": "Carlos Mendoza"})
    documento: str = Field(..., description="Cédula de ciudadanía o NIT del comprador", json_schema_extra={"example": "1018234901"})
    direccion: str = Field(..., description="Dirección física de despacho", json_schema_extra={"example": "Calle 100 # 19-61, Bogotá"})
    telefono: Optional[str] = Field("N/A", description="Teléfono de contacto", json_schema_extra={"example": "3114567890"})
    correo: Optional[str] = Field("cliente@example.com", description="Correo electrónico para remisión de comprobantes", json_schema_extra={"example": "cmendoza@gmail.com"})


class RegistrarVentaRequest(BaseModel):
    cliente: ClienteInfo = Field(..., description="Datos de contacto y facturación del cliente")
    items: List[ItemVenta] = Field(..., min_length=1, description="Lista de artículos incluidos en la venta")
    metodo_pago: Optional[str] = Field("TRANSFERENCIA", description="Modalidad de pago", json_schema_extra={"example": "TRANSFERENCIA_PSE"})
    observaciones: Optional[str] = Field("", description="Notas internas sobre la orden de venta")


class ItemCompra(BaseModel):
    producto_id: str = Field(..., description="ID del producto a adquirir", json_schema_extra={"example": "MUE-001"})
    nombre: str = Field(..., description="Nombre del mueble", json_schema_extra={"example": "Sofá Seccional Cuero 3 Puestos"})
    cantidad: int = Field(..., gt=0, description="Cantidad de unidades a comprar", json_schema_extra={"example": 5})
    costo_unitario: float = Field(..., gt=0, description="Costo unitario pactado con el proveedor (COP)", json_schema_extra={"example": 750000.0})


class ProveedorInfo(BaseModel):
    nombre: str = Field(..., description="Razón social del proveedor", json_schema_extra={"example": "Industrias Madereras del Cauca S.A.S."})
    nit: str = Field(..., description="Número de Identificación Tributaria", json_schema_extra={"example": "890.301.204-5"})
    contacto: Optional[str] = Field("Ventas Corporativas", description="Persona o área de contacto", json_schema_extra={"example": "Maria Fernanda Ruiz"})
    telefono: Optional[str] = Field("N/A", description="Teléfono corporativo", json_schema_extra={"example": "3209876543"})
    correo: Optional[str] = Field("proveedor@example.com", description="Correo corporativo del proveedor", json_schema_extra={"example": "ventas@maderascauca.com"})


class RegistrarCompraRequest(BaseModel):
    proveedor: ProveedorInfo = Field(..., description="Información del proveedor proveedor")
    items: List[ItemCompra] = Field(..., min_length=1, description="Lista de productos a reabastecer")
    terminos_pago: Optional[str] = Field("CREDITO_30_DIAS", description="Condiciones comerciales de pago", json_schema_extra={"example": "CREDITO_45_DIAS"})
    observaciones: Optional[str] = Field("", description="Notas adicionales de la orden de compra")


class RecibirFacturaRequest(BaseModel):
    referencia_operacion: str = Field(
        ...,
        description="Código de referencia de la orden comercial vinculada (ID de Venta o ID de Compra)",
        json_schema_extra={"example": "VEN-20261025-A1B2C3"}
    )
    numero_factura: str = Field(..., description="Consecutivo fiscal asignado por Contabilidad", json_schema_extra={"example": "FE-VEN-1001"})
    cufe: str = Field(..., description="Código Único de Factura Electrónica emitido", json_schema_extra={"example": "dafab70a662c787994ef4709..."})
    fecha_emision: str = Field(..., description="Fecha y hora de expedición fiscal", json_schema_extra={"example": "2026-10-25T14:30:00"})
    total_facturado: float = Field(..., gt=0, description="Importe total de la factura vinculada", json_schema_extra={"example": 3117800.0})


class RegistrarVentaResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado de la operación")
    mensaje: str = Field(..., description="Mensaje informativo")
    venta: Dict[str, Any] = Field(..., description="Registro mercantil completo de la venta")


class RegistrarCompraResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado de la operación")
    mensaje: str = Field(..., description="Mensaje informativo")
    compra: Dict[str, Any] = Field(..., description="Registro mercantil completo de la orden de compra")


class RecibirFacturaResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado del enlace")
    mensaje: str = Field(..., description="Detalle del enlace")
    tipo: str = Field(..., description="Tipo de operación vinculada ('VENTA' o 'COMPRA')")
    registro: Dict[str, Any] = Field(..., description="Orden comercial actualizada con datos tributarios")


class ListarVentasResponse(BaseModel):
    total: int = Field(..., description="Total de ventas registradas")
    ventas: List[Dict[str, Any]] = Field(..., description="Listado histórico de ventas comerciales")


class ListarComprasResponse(BaseModel):
    total: int = Field(..., description="Total de compras registradas")
    compras: List[Dict[str, Any]] = Field(..., description="Listado histórico de órdenes de compra a proveedores")
