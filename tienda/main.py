from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import os
import socket
import datetime

app = FastAPI(
    title="Portal de Tienda de Muebles",
    description="Portal de cara al cliente final. En la arquitectura orquestada, delega la coordinación al Middleware.",
    version="1.0.0"
)

def resolver_url_servicio(var_entorno: str, docker_name: str, puerto: int) -> str:
    if os.getenv(var_entorno):
        return os.getenv(var_entorno)
    try:
        socket.gethostbyname(docker_name)
        return f"http://{docker_name}:{puerto}"
    except Exception:
        return f"http://localhost:{puerto}"

MIDDLEWARE_URL = resolver_url_servicio("MIDDLEWARE_URL", "c-middleware", 8000)
pedidos_locales: List[Dict[str, Any]] = []


class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)


class DatosCliente(BaseModel):
    nombre: str
    documento: str
    direccion: str
    telefono: Optional[str] = "3001234567"
    correo: Optional[str] = "cliente@correo.com"


class RealizarCompraRequest(BaseModel):
    cliente: DatosCliente
    items: List[ItemPedido]
    metodo_pago: Optional[str] = "TRANSFERENCIA_BANCARIA"


@app.get("/", response_class=HTMLResponse)
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Tienda de Muebles Confort - Portal Cliente</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
            h1 { color: #1e3a8a; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }
            .badge { background: #10b981; color: white; padding: 4px 10px; border-radius: 20px; font-size: 13px; font-weight: bold; }
            .info-box { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px; }
            button { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold; }
            button:hover { background: #1d4ed8; }
            pre { background: #1e293b; color: #38bdf8; padding: 15px; border-radius: 8px; overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { border: 1px solid #e2e8f0; padding: 10px; text-align: left; }
            th { background-color: #f8fafc; color: #475569; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛋️ Tienda de Muebles Confort <span class="badge">Portal Cliente</span></h1>
            <div class="info-box">
                <strong>Arquitectura Distribuida Orquestada:</strong> Este componente no se comunica directamente con Transportador ni con Contabilidad; delega el proceso completo de compra al <strong>Middleware Orquestador</strong>.
            </div>
            <h3>Endpoints de la API:</h3>
            <ul>
                <li><code>GET /productos</code> - Consulta el catálogo y stock en tiempo real desde la Blockchain a través del Middleware.</li>
                <li><code>POST /comprar</code> - Inicia el flujo orquestado de venta coordinado por el Middleware.</li>
                <li><code>GET /pedidos</code> - Lista las compras realizadas desde este portal.</li>
                <li><code>GET /docs</code> - Documentación Swagger interactiva.</li>
            </ul>
            <p><a href="/docs" target="_blank"><button>Ir a Swagger UI /docs</button></a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/productos")
async def consultar_productos():
    """Consulta el catálogo de muebles y existencias validadas en la blockchain vía Middleware"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{MIDDLEWARE_URL}/orquestar/catalogo")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.text)
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"No es posible conectar con el Middleware: {str(e)}")


@app.post("/comprar")
async def realizar_compra(payload: RealizarCompraRequest):
    """
    El cliente realiza su compra:
    La tienda envía la solicitud al Middleware para que orqueste:
      - Verificación de existencias en Blockchain
      - Registro de orden en Compras/Ventas
      - Facturación y CUFE en Contabilidad
      - Deducción de stock con minado en Blockchain
      - Programación de envío en Transportador
    """
    req_orquestador = {
        "cliente": payload.cliente.model_dump(),
        "items": [it.model_dump() for it in payload.items],
        "metodo_pago": payload.metodo_pago,
        "observaciones": "Compra generada desde el Portal Web de la Tienda"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(f"{MIDDLEWARE_URL}/orquestar/venta", json=req_orquestador)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", res.text))
            
            resultado = res.json()
            pedidos_locales.append({
                "fecha": datetime.datetime.now().isoformat(),
                "id_venta": resultado.get("resumen", {}).get("id_venta"),
                "cliente": payload.cliente.nombre,
                "factura": resultado.get("resumen", {}).get("numero_factura"),
                "guia_transporte": resultado.get("resumen", {}).get("numero_guia_transporte"),
                "total": resultado.get("resumen", {}).get("total_pagado")
            })
            return resultado
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Falla de comunicación con el Middleware: {str(e)}")


@app.get("/pedidos")
def listar_pedidos():
    return {
        "total_pedidos": len(pedidos_locales),
        "pedidos": pedidos_locales
    }
