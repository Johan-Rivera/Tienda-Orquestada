from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ItemSolicitudVenta(BaseModel):
    producto_id: str = Field(
        ...,
        description="Código identificador del mueble a comprar (ej. MUE-001, MUE-002)",
        json_schema_extra={"example": "MUE-001"}
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description="Cantidad requerida de muebles (debe ser mayor a cero)",
        json_schema_extra={"example": 2}
    )


class ClienteSolicitud(BaseModel):
    nombre: str = Field(
        ...,
        description="Nombre completo o razón social del cliente comprador",
        json_schema_extra={"example": "Carlos Mendoza"}
    )
    documento: str = Field(
        ...,
        description="Número de documento de identidad (Cédula de Ciudadanía, Extranjería o NIT)",
        json_schema_extra={"example": "1018234901"}
    )
    direccion: str = Field(
        ...,
        description="Dirección física completa donde se realizará la entrega de los muebles",
        json_schema_extra={"example": "Calle 100 # 19-61, Bogotá"}
    )
    telefono: Optional[str] = Field(
        "3114567890",
        description="Número telefónico de contacto para coordinar la entrega",
        json_schema_extra={"example": "3114567890"}
    )
    correo: Optional[str] = Field(
        "cmendoza@gmail.com",
        description="Correo electrónico para remisión de la factura electrónica y guía de transporte",
        json_schema_extra={"example": "cmendoza@gmail.com"}
    )


class RegistrarVentaRequest(BaseModel):
    cliente: ClienteSolicitud = Field(
        ...,
        description="Información detallada del cliente comprador y destino de entrega"
    )
    items: List[ItemSolicitudVenta] = Field(
        ...,
        min_length=1,
        description="Lista de uno o varios muebles a comprar"
    )
    metodo_pago: Optional[str] = Field(
        "TRANSFERENCIA_PSE",
        description="Modalidad de pago seleccionada por el cliente",
        json_schema_extra={"example": "TRANSFERENCIA_PSE"}
    )


class ItemSolicitudCompra(BaseModel):
    producto_id: str = Field(
        ...,
        description="Código identificador del mueble a abastecer (ej. MUE-001, MUE-002)",
        json_schema_extra={"example": "MUE-001"}
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description="Cantidad de unidades a ingresar al almacén",
        json_schema_extra={"example": 5}
    )
    costo_unitario: Optional[float] = Field(
        None,
        gt=0,
        description="Costo unitario acordado con el proveedor (si se omite, se toma el costo base del catálogo)",
        json_schema_extra={"example": 750000.0}
    )


class ProveedorSolicitud(BaseModel):
    nombre: str = Field(
        ...,
        description="Razón social del fabricante o proveedor de muebles",
        json_schema_extra={"example": "Industrias Madereras del Cauca S.A.S."}
    )
    nit: str = Field(
        ...,
        description="Número de Identificación Tributaria del proveedor",
        json_schema_extra={"example": "890.301.204-5"}
    )
    contacto: Optional[str] = Field(
        "Maria Fernanda Ruiz",
        description="Nombre del asesor o representante comercial del proveedor",
        json_schema_extra={"example": "Maria Fernanda Ruiz"}
    )
    telefono: Optional[str] = Field(
        "3209876543",
        description="Teléfono de contacto del proveedor",
        json_schema_extra={"example": "3209876543"}
    )
    correo: Optional[str] = Field(
        "ventas@maderascauca.com",
        description="Correo corporativo del proveedor",
        json_schema_extra={"example": "ventas@maderascauca.com"}
    )


class RegistrarCompraRequest(BaseModel):
    proveedor: ProveedorSolicitud = Field(
        ...,
        description="Datos corporativos del proveedor que suministra los muebles"
    )
    items: List[ItemSolicitudCompra] = Field(
        ...,
        min_length=1,
        description="Lista de productos a ingresar al inventario"
    )
    terminos_pago: Optional[str] = Field(
        "CREDITO_45_DIAS",
        description="Condición comercial o plazo de pago pactado",
        json_schema_extra={"example": "CREDITO_45_DIAS"}
    )


class DespachoInfo(BaseModel):
    numero_guia: str = Field(..., description="Número de guía logística", json_schema_extra={"example": "GUIA-20261025-4987"})
    transportadora: str = Field(..., description="Empresa transportadora asignada", json_schema_extra={"example": "Logística & Carga Móvil Express de Colombia S.A.S."})
    vehiculo: str = Field(..., description="Vehículo asignado para el despacho", json_schema_extra={"example": "CAMION-02 (Plataforma Hidráulica)"})
    fecha_estimada_entrega: str = Field(..., description="Fecha compromiso de entrega", json_schema_extra={"example": "2026-10-27"})


class ItemFactura(BaseModel):
    producto_id: str = Field(..., description="Código del mueble", json_schema_extra={"example": "MUE-001"})
    nombre: str = Field(..., description="Nombre comercial del mueble", json_schema_extra={"example": "Sofá Seccional Cuero 3 Puestos"})
    cantidad: int = Field(..., description="Cantidad de unidades", json_schema_extra={"example": 2})
    precio_unitario: float = Field(..., description="Precio unitario (COP)", json_schema_extra={"example": 1200000.0})
    subtotal: float = Field(..., description="Subtotal liquidado (COP)", json_schema_extra={"example": 2400000.0})


class FacturaVentaResponse(BaseModel):
    id_venta: str = Field(..., description="Código de orden mercantil de venta", json_schema_extra={"example": "VEN-20261025-A1B2C3"})
    numero_factura: str = Field(..., description="Consecutivo de Factura Electrónica legal", json_schema_extra={"example": "FE-VEN-1001"})
    cufe: str = Field(..., description="Código Único de Factura Electrónica emitido con SHA-256", json_schema_extra={"example": "dafab70a662c7879..."})
    fecha_emision: str = Field(..., description="Fecha y hora de expedición fiscal", json_schema_extra={"example": "2026-10-25T14:30:00"})
    cliente: ClienteSolicitud = Field(..., description="Datos del comprador")
    items: List[ItemFactura] = Field(..., description="Lista de muebles adquiridos")
    subtotal: float = Field(..., description="Base gravable antes de impuestos (COP)", json_schema_extra={"example": 2620000.0})
    iva: float = Field(..., description="Impuesto al Valor Agregado (19%) (COP)", json_schema_extra={"example": 497800.0})
    total: float = Field(..., description="Total general pagado (COP)", json_schema_extra={"example": 3117800.0})
    metodo_pago: str = Field(..., description="Medio de pago seleccionado", json_schema_extra={"example": "TRANSFERENCIA_PSE"})
    despacho: DespachoInfo = Field(..., description="Información de despacho y entrega a domicilio")


class ItemFacturaCompra(BaseModel):
    producto_id: str = Field(..., description="Código del producto", json_schema_extra={"example": "MUE-001"})
    nombre: str = Field(..., description="Nombre comercial del mueble", json_schema_extra={"example": "Sofá Seccional Cuero 3 Puestos"})
    cantidad: int = Field(..., description="Cantidad adquirida", json_schema_extra={"example": 5})
    costo_unitario: float = Field(..., description="Costo unitario acordado (COP)", json_schema_extra={"example": 750000.0})
    subtotal: float = Field(..., description="Subtotal liquidado (COP)", json_schema_extra={"example": 3750000.0})


class FacturaCompraResponse(BaseModel):
    id_compra: str = Field(..., description="Código de orden de compra", json_schema_extra={"example": "COM-20261025-D4E5F6"})
    numero_factura: str = Field(..., description="Consecutivo fiscal / Cuenta por pagar", json_schema_extra={"example": "FE-COM-5001"})
    cufe: str = Field(..., description="Código CUFE emitido con SHA-256", json_schema_extra={"example": "6741944a6f05..."})
    fecha_emision: str = Field(..., description="Fecha y hora de emisión", json_schema_extra={"example": "2026-10-25T14:30:00"})
    proveedor: ProveedorSolicitud = Field(..., description="Datos del proveedor que suministra")
    items: List[ItemFacturaCompra] = Field(..., description="Lista de productos abastecidos")
    subtotal: float = Field(..., description="Subtotal antes de IVA (COP)", json_schema_extra={"example": 6150000.0})
    iva: float = Field(..., description="IVA liquidado (19%) (COP)", json_schema_extra={"example": 1168500.0})
    total: float = Field(..., description="Total general liquidado (COP)", json_schema_extra={"example": 7318500.0})
    terminos_pago: str = Field(..., description="Condición y plazo de pago", json_schema_extra={"example": "CREDITO_45_DIAS"})


# Alias para retrocompatibilidad
OrquestarVentaResponse = FacturaVentaResponse
OrquestarCompraResponse = FacturaCompraResponse
