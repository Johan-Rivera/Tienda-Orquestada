from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PaqueteInfo(BaseModel):
    producto_id: str = Field(..., description="ID del mueble embalado", json_schema_extra={"example": "MUE-001"})
    nombre: str = Field(..., description="Descripción del artículo", json_schema_extra={"example": "Sofá Seccional Cuero 3 Puestos"})
    cantidad: int = Field(..., gt=0, description="Cantidad de bultos/muebles", json_schema_extra={"example": 2})
    peso_estimado_kg: Optional[float] = Field(30.0, description="Peso volumétrico o real estimado por unidad (kg)", json_schema_extra={"example": 45.0})


class OrdenarTransporteRequest(BaseModel):
    id_venta: str = Field(
        ...,
        description="Código de referencia de la venta que origina el despacho",
        json_schema_extra={"example": "VEN-20261025-A1B2C3"}
    )
    destinatario: str = Field(
        ...,
        description="Nombre completo de la persona autorizada para recibir la entrega",
        json_schema_extra={"example": "Carlos Mendoza"}
    )
    direccion_entrega: str = Field(
        ...,
        description="Dirección física exacta para entrega en destino",
        json_schema_extra={"example": "Calle 100 # 19-61, Bogotá"}
    )
    ciudad: Optional[str] = Field("Bogotá D.C.", description="Ciudad de destino", json_schema_extra={"example": "Bogotá D.C."})
    telefono: Optional[str] = Field("N/A", description="Teléfono de contacto para la entrega", json_schema_extra={"example": "3114567890"})
    paquetes: List[PaqueteInfo] = Field(..., min_length=1, description="Lista de muebles y paquetes a transportar")


class GuiaTransporteModel(BaseModel):
    numero_guia: str = Field(..., description="Identificador único de rastreo y guía logística", json_schema_extra={"example": "GUIA-20261025-4987"})
    id_venta: str = Field(..., description="Referencia de la venta asociada")
    transportadora: str = Field(..., description="Empresa transportadora asignada", json_schema_extra={"example": "Logística & Carga Móvil Express de Colombia S.A.S."})
    destinatario: str = Field(..., description="Nombre del receptor")
    direccion_entrega: str = Field(..., description="Dirección de entrega")
    ciudad: str = Field(..., description="Ciudad de destino")
    telefono: str = Field(..., description="Teléfono")
    vehiculo_asignado: str = Field(..., description="Vehículo o camión de la flota asignado", json_schema_extra={"example": "CAMION-02 (Plataforma Hidráulica)"})
    ruta_asignada: str = Field(..., description="Ruta logística planificada", json_schema_extra={"example": "Ruta Norte - Bogotá y Sabana"})
    peso_total_kg: float = Field(..., description="Peso total calculado de la carga (kg)", json_schema_extra={"example": 90.0})
    paquetes: List[Dict[str, Any]] = Field(..., description="Detalle de paquetes asignados al vehículo")
    fecha_creacion: str = Field(..., description="Fecha de emisión de la orden de despacho")
    fecha_despacho_programada: str = Field(..., description="Fecha programada para salida del camión", json_schema_extra={"example": "2026-10-26"})
    fecha_estimada_entrega: str = Field(..., description="Fecha compromiso de entrega al cliente", json_schema_extra={"example": "2026-10-27"})
    estado_envio: str = Field("DESPACHO_PROGRAMADO", description="Estado de la guía")


class OrdenarTransporteResponse(BaseModel):
    status: str = Field("EXITOSO", description="Estado de la programación")
    mensaje: str = Field(..., description="Mensaje informativo")
    guia: GuiaTransporteModel = Field(..., description="Guía de transporte y despacho emitida")


class ListarGuiasResponse(BaseModel):
    total: int = Field(..., description="Total de guías emitidas")
    guias: List[GuiaTransporteModel] = Field(..., description="Listado histórico de despachos y guías de transporte")
