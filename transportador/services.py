import datetime
import random
from typing import Dict, Any, List
from schemas.transportador import OrdenarTransporteRequest


class GestorTransporte:
    """
    Clase que encapsula la asignación logística de vehículos, rutas y generación de guías de despacho.
    """

    VEHICULOS_DISPONIBLES = [
        "CAMION-01 (Furgón Carga Pesada)",
        "CAMION-02 (Plataforma Hidráulica)",
        "CAMION-03 (Furgón Mediano)"
    ]
    RUTAS_LOGISTICAS = [
        "Ruta Norte - Bogotá y Sabana",
        "Ruta Sur - Soacha y Cundinamarca",
        "Ruta Centro - Despacho Exprés"
    ]

    def __init__(self):
        self.guias_db: Dict[str, Dict[str, Any]] = {}

    def ordenar_transporte(self, payload: OrdenarTransporteRequest) -> Dict[str, Any]:
        if not payload.paquetes:
            raise ValueError("Debe especificar al menos un paquete para transportar.")

        codigo_guia = f"GUIA-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        fecha_despacho = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        fecha_estimada_entrega = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

        peso_total = sum(p.cantidad * (p.peso_estimado_kg or 25.0) for p in payload.paquetes)
        vehiculo = random.choice(self.VEHICULOS_DISPONIBLES)
        ruta = random.choice(self.RUTAS_LOGISTICAS)

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

        self.guias_db[codigo_guia] = guia

        return {
            "status": "EXITOSO",
            "mensaje": "Transporte programado y guía generada exitosamente",
            "guia": guia
        }

    def listar_guias(self) -> List[Dict[str, Any]]:
        return list(self.guias_db.values())
