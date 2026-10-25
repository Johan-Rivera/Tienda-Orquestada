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


class BloqueMinadoResumen(BaseModel):
    producto_id: str = Field(..., description="ID del producto")
    cantidad: int = Field(..., description="Cantidad transaccionada")
    stock_resultante: int = Field(..., description="Nuevo saldo en Blockchain")
    bloque_hash: str = Field(..., description="Hash SHA-256 del bloque minado")
    bloque_index: int = Field(..., description="Índice del bloque en la cadena")


class ResumenVentaOrquestada(BaseModel):
    id_venta: str = Field(..., description="Código de orden mercantil", json_schema_extra={"example": "VEN-20261025-A1B2C3"})
    cliente: str = Field(..., description="Nombre del comprador")
    total_pagado: float = Field(..., description="Monto total liquidado (COP)", json_schema_extra={"example": 3117800.0})
    numero_factura: str = Field(..., description="Consecutivo de Factura Electrónica", json_schema_extra={"example": "FE-VEN-1001"})
    cufe: str = Field(..., description="Código Único de Factura Electrónica (SHA-256)", json_schema_extra={"example": "dafab70a662c..."})
    numero_guia_transporte: str = Field(..., description="Número de guía logística", json_schema_extra={"example": "GUIA-20261025-4987"})
    transportadora: str = Field(..., description="Empresa logística asignada")
    vehiculo: str = Field(..., description="Camión asignado")
    fecha_estimada_entrega: str = Field(..., description="Fecha compromiso de entrega")
    bloques_blockchain: List[BloqueMinadoResumen] = Field(..., description="Bloques PoW minados que redujeron el stock")


class OrquestarVentaResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado del flujo orquestado")
    mensaje: str = Field(..., description="Mensaje general")
    id_proceso: str = Field(..., description="Identificador único del proceso orquestado", json_schema_extra={"example": "ORQ-VEN-20261025143000"})
    resumen: ResumenVentaOrquestada = Field(..., description="Resumen consolidado para el cliente y desarrolladores")
    detalles_completos: Dict[str, Any] = Field(..., description="Detalles completos de cada paso (venta, factura, transporte)")


class ResumenCompraOrquestada(BaseModel):
    id_compra: str = Field(..., description="Código de orden de compra", json_schema_extra={"example": "COM-20261025-D4E5F6"})
    proveedor: str = Field(..., description="Nombre del proveedor")
    total_compra: float = Field(..., description="Monto total liquidado (COP)", json_schema_extra={"example": 7318500.0})
    numero_factura: str = Field(..., description="Consecutivo de Factura / Cuenta por pagar", json_schema_extra={"example": "FE-COM-5001"})
    cufe: str = Field(..., description="Código CUFE emitido", json_schema_extra={"example": "6741944a6f05..."})
    terminos_pago: str = Field(..., description="Condición de pago")
    bloques_blockchain: List[BloqueMinadoResumen] = Field(..., description="Bloques PoW minados que incrementaron el stock")


class OrquestarCompraResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado del flujo orquestado")
    mensaje: str = Field(..., description="Mensaje general")
    id_proceso: str = Field(..., description="Identificador único del proceso orquestado", json_schema_extra={"example": "ORQ-COM-20261025143000"})
    resumen: ResumenCompraOrquestada = Field(..., description="Resumen consolidado para el proveedor y desarrolladores")
    detalles_completos: Dict[str, Any] = Field(..., description="Detalles completos de cada paso (compra, factura, blockchain)")
