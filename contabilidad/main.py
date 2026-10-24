from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import hashlib
import datetime
import uuid

app = FastAPI(
    title="Microservicio de Contabilidad y Facturación",
    description="Emite facturas electrónicas para compras y ventas y gestiona el balance financiero.",
    version="1.0.0"
)

# Base de datos en memoria para facturas
facturas_db: Dict[str, Dict[str, Any]] = {}
contador_ventas = 1000
contador_compras = 5000


class DetalleItem(BaseModel):
    producto_id: str
    nombre: str
    cantidad: int
    precio_unitario: float


class GenerarFacturaRequest(BaseModel):
    tipo_operacion: str = Field(..., description="'VENTA' (ingreso) o 'COMPRA' (egreso)")
    referencia_operacion: str = Field(..., description="ID de la venta o compra vinculada")
    emisor: str = Field(..., description="Nombre/Razón Social del emisor")
    receptor: str = Field(..., description="Nombre/Razón Social del receptor")
    subtotal: float = Field(..., gt=0)
    iva: float = Field(..., ge=0)
    total: float = Field(..., gt=0)
    detalles: List[DetalleItem]
    metodo_pago: Optional[str] = "ELECTRONICO"


@app.get("/")
def estado():
    return {
        "servicio": "Contabilidad y Facturación",
        "estado": "ACTIVO",
        "total_facturas_emitidas": len(facturas_db),
        "metodos_disponibles": [
            "POST /generarFactura",
            "GET /facturas",
            "GET /facturas/{numero_factura}",
            "GET /balance"
        ]
    }


@app.post("/generarFactura")
def generar_factura(payload: GenerarFacturaRequest):
    """
    Método requerido por el esquema:
    Genera una factura electrónica contable con número consecutivo y CUFE (Código Único de Facturación).
    """
    global contador_ventas, contador_compras

    tipo = payload.tipo_operacion.upper()
    if tipo not in ["VENTA", "COMPRA"]:
        raise HTTPException(status_code=400, detail="El tipo de operación debe ser 'VENTA' o 'COMPRA'.")

    fecha_emision = datetime.datetime.now().isoformat()

    if tipo == "VENTA":
        contador_ventas += 1
        prefijo = "FE-VEN"
        numero_factura = f"{prefijo}-{contador_ventas}"
    else:
        contador_compras += 1
        prefijo = "FE-COM"
        numero_factura = f"{prefijo}-{contador_compras}"

    # Generación de CUFE (Código Único de Factura Electrónica con SHA-256)
    cufe_raw = f"{numero_factura}|{payload.referencia_operacion}|{payload.subtotal}|{payload.iva}|{payload.total}|{fecha_emision}"
    cufe = hashlib.sha256(cufe_raw.encode("utf-8")).hexdigest()

    factura = {
        "numero_factura": numero_factura,
        "cufe": cufe,
        "tipo_operacion": tipo,
        "referencia_operacion": payload.referencia_operacion,
        "emisor": payload.emisor,
        "receptor": payload.receptor,
        "fecha_emision": fecha_emision,
        "subtotal": payload.subtotal,
        "iva": payload.iva,
        "total": payload.total,
        "metodo_pago": payload.metodo_pago,
        "detalles": [d.model_dump() for d in payload.detalles],
        "estado_tributario": "VALIDADA_DIAN",
        "estado_pago": "CONCILIADO"
    }

    facturas_db[numero_factura] = factura

    return {
        "status": "EXITOSO",
        "mensaje": f"Factura electrónica {numero_factura} emitida correctamente",
        "factura": factura
    }


@app.get("/facturas")
def listar_facturas():
    return {
        "total_facturas": len(facturas_db),
        "facturas": list(facturas_db.values())
    }


@app.get("/facturas/{numero_factura}")
def consultar_factura(numero_factura: str):
    if numero_factura not in facturas_db:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
    return facturas_db[numero_factura]


@app.get("/balance")
def obtener_balance_financiero():
    """Calcula ingresos por ventas, egresos por compras y balance neto"""
    total_ingresos = sum(f["total"] for f in facturas_db.values() if f["tipo_operacion"] == "VENTA")
    total_egresos = sum(f["total"] for f in facturas_db.values() if f["tipo_operacion"] == "COMPRA")
    balance_neto = total_ingresos - total_egresos

    return {
        "total_ingresos_ventas": round(total_ingresos, 2),
        "total_egresos_compras": round(total_egresos, 2),
        "balance_neto": round(balance_neto, 2),
        "cantidad_facturas_emitidas": len(facturas_db)
    }
