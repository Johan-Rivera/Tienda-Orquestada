from fastapi import FastAPI, HTTPException, status
from schemas.transportador import (
    OrdenarTransporteRequest,
    OrdenarTransporteResponse,
    ListarGuiasResponse
)
from services import GestorTransporte

tags_metadata = [
    {
        "name": "Logística y Envíos",
        "description": "Programación de vehículos de transporte pesado, asignación de rutas y expedición de guías de carga."
    }
]

app = FastAPI(
    title="Microservicio Transportador y Logística",
    description="""
    Microservicio logístico encargado de coordinar la flota de camiones, planificar rutas metropolitanas y emitir guías de despacho.
    
    ### Funciones:
    * **Asignación Vehicular:** Asigna camiones adecuados (furgón, plataforma hidráulica) según el volumen y peso de la carga de muebles.
    * **Generación de Guías:** Emite un identificador alfanumérico único para rastreo y control del despacho.
    * **Cálculo de Tiempos de Entrega:** Determina fechas programadas de despacho y fechas compromiso de entrega.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Instancia global del servicio logístico
gestor_transporte = GestorTransporte()


@app.post(
    "/ordenarTransporte",
    response_model=OrdenarTransporteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Programar transporte y generar guía de entrega",
    description="Programa el envío logístico de muebles vinculados a una orden de venta, calculando el peso acumulado de la carga, asignando un camión disponible, una ruta geográfica y emitiendo la guía de entrega oficial.",
    responses={
        400: {"description": "Lista de paquetes vacía o datos de entrega incompletos."}
    },
    tags=["Logística y Envíos"]
)
def ordenar_transporte(payload: OrdenarTransporteRequest):
    try:
        return gestor_transporte.ordenar_transporte(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get(
    "/guias",
    response_model=ListarGuiasResponse,
    summary="Listar guías de despacho y transporte",
    description="Retorna el listado completo de todas las guías de transporte programadas en el sistema.",
    tags=["Logística y Envíos"]
)
def listar_guias():
    guias = gestor_transporte.listar_guias()
    return {
        "total": len(guias),
        "guias": guias
    }
