from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import os
import socket
import datetime

app = FastAPI(
    title="Portal de Atención a Proveedores",
    description="Portal para gestión de proveedores de muebles. En la arquitectura orquestada, delega la coordinación al Middleware.",
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
abastecimientos_locales: List[Dict[str, Any]] = []


class ItemAbastecimiento(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)
    costo_unitario: Optional[float] = None


class DatosProveedor(BaseModel):
    nombre: str
    nit: str
    contacto: Optional[str] = "Representante Comercial"
    telefono: Optional[str] = "3151234567"
    correo: Optional[str] = "proveedor@mueblesyestilo.com"


class RegistrarAbastecimientoRequest(BaseModel):
    proveedor: DatosProveedor
    items: List[ItemAbastecimiento]
    terminos_pago: Optional[str] = "CREDITO_30_DIAS"


@app.get("/", response_class=HTMLResponse)
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Atención a Proveedores - Tienda de Muebles</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
            h1 { color: #0f766e; border-bottom: 3px solid #14b8a6; padding-bottom: 10px; }
            .badge { background: #0d9488; color: white; padding: 4px 10px; border-radius: 20px; font-size: 13px; font-weight: bold; }
            .info-box { background: #f0fdfa; border-left: 4px solid #14b8a6; padding: 15px; margin: 20px 0; border-radius: 4px; }
            button { background: #0f766e; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold; }
            button:hover { background: #115e59; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏭 Portal de Atención a Proveedores <span class="badge">B2B</span></h1>
            <div class="info-box">
                <strong>Orquestación con Middleware:</strong> Este componente permite a los proveedores consultar las necesidades de abastecimiento generadas desde el análisis de stock de la <strong>Blockchain de Inventario</strong> y despachar materias primas o muebles terminados orquestados por el <strong>Middleware</strong>.
            </div>
            <h3>Endpoints de la API:</h3>
            <ul>
                <li><code>GET /requerimientos</code> - Consulta productos por debajo del stock mínimo calculados en Blockchain.</li>
                <li><code>POST /abastecer</code> - Inicia el flujo orquestado de compra y reabastecimiento coordinado por el Middleware.</li>
                <li><code>GET /compras</code> - Historial de despachos/abastecimientos realizados.</li>
                <li><code>GET /docs</code> - Documentación Swagger interactiva.</li>
            </ul>
            <p><a href="/docs" target="_blank"><button>Ir a Swagger UI /docs</button></a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/requerimientos")
async def consultar_requerimientos():
    """Consulta requerimientos de productos con stock bajo validados por el Middleware"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{MIDDLEWARE_URL}/orquestar/requerimientos")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.text)
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"No fue posible conectar con el Middleware: {str(e)}")


@app.post("/abastecer")
async def abastecer_inventario(payload: RegistrarAbastecimientoRequest):
    """
    El proveedor suministra muebles a la tienda:
    Delega al Middleware la orquestación de:
      - Validación contra el catálogo de Inventario
      - Registro comercial de compra en Compras/Ventas
      - Facturación y cuenta por pagar en Contabilidad
      - Aumento inmutable de existencias minando en la Blockchain de Inventario
    """
    req_orquestador = {
        "proveedor": payload.proveedor.model_dump(),
        "items": [it.model_dump() for it in payload.items],
        "terminos_pago": payload.terminos_pago,
        "observaciones": "Abastecimiento realizado desde el Portal de Proveedores"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(f"{MIDDLEWARE_URL}/orquestar/compra", json=req_orquestador)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", res.text))
            
            resultado = res.json()
            abastecimientos_locales.append({
                "fecha": datetime.datetime.now().isoformat(),
                "id_compra": resultado.get("resumen", {}).get("id_compra"),
                "proveedor": payload.proveedor.nombre,
                "factura": resultado.get("resumen", {}).get("numero_factura"),
                "total": resultado.get("resumen", {}).get("total_compra")
            })
            return resultado
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Falla de comunicación con el Middleware: {str(e)}")


@app.get("/compras")
def listar_compras():
    return {
        "total_abastecimientos": len(abastecimientos_locales),
        "abastecimientos": abastecimientos_locales
    }
