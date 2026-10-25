from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import datetime
import random
import uuid

app = FastAPI(
    title="Microservicio Transportador y Logística",
    description="Gestiona la programación de despachos y generación de guías de transporte para ventas de muebles.",
    version="1.0.0"
)

guias_db: Dict[str, Dict[str, Any]] = {}

VEHICULOS_DISPONIBLES = ["CAMION-01 (Furgón Carga Pesada)", "CAMION-02 (Plataforma Hidráulica)", "CAMION-03 (Furgón Mediano)"]
RUTAS_LOGISTICAS = ["Ruta Norte - Bogotá y Sabana", "Ruta Sur - Soacha y Cundinamarca", "Ruta Centro - Despacho Exprés"]


class PaqueteInfo(BaseModel):
    producto_id: str
    nombre: str
    cantidad: int
    peso_estimado_kg: Optional[float] = 30.0


class OrdenarTransporteRequest(BaseModel):
    id_venta: str = Field(..., description="Referencia de la venta asociada")
    destinatario: str = Field(..., description="Nombre del cliente o persona que recibe")
    direccion_entrega: str = Field(..., description="Dirección física de destino")
    ciudad: Optional[str] = "Bogotá D.C."
    telefono: Optional[str] = "N/A"
    paquetes: List[PaqueteInfo] = Field(..., description="Lista de artículos a transportar")


@app.post("/ordenarTransporte")
def ordenar_transporte(payload: OrdenarTransporteRequest):
    """
    Método requerido por el esquema:
    Programa la logística y genera la guía de transporte para la entrega del pedido de muebles.
    """
    if not payload.paquetes:
        raise HTTPException(status_code=400, detail="Debe especificar al menos un paquete para transportar.")

    codigo_guia = f"GUIA-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    fecha_despacho = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    fecha_estimada_entrega = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

    peso_total = sum(p.cantidad * (p.peso_estimado_kg or 25.0) for p in payload.paquetes)
    vehiculo = random.choice(VEHICULOS_DISPONIBLES)
    ruta = random.choice(RUTAS_LOGISTICAS)

    guia = {
        "numero_guia": codigo_guia,
        "id_venta": payload.id_venta,
        "transportadora": "Logística & Carga Móvil Express de Colombia S.A.S.",
        "destinatario": payload.destinatario,
        "direccion_entrega": payload.direccion_entrega,
        "ciudad": payload.ciudad,
        "telefono": payload.telefono,
        "vehiculo_asignado": vehiculo,
        "ruta_asignada": ruta,
        "peso_total_kg": round(peso_total, 2),
        "paquetes": [p.model_dump() for p in payload.paquetes],
        "fecha_creacion": datetime.datetime.now().isoformat(),
        "fecha_despacho_programada": fecha_despacho,
        "fecha_estimada_entrega": fecha_estimada_entrega,
        "estado_envio": "DESPACHO_PROGRAMADO"
    }

    guias_db[codigo_guia] = guia

    return {
        "status": "EXITOSO",
        "mensaje": "Transporte programado y guía generada exitosamente",
        "guia": guia
    }


@app.get("/guias")
def listar_guias():
    return {
        "total": len(guias_db),
        "guias": list(guias_db.values())
    }
