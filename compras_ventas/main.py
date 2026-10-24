from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import datetime

app = FastAPI(
    title="Microservicio de Compras y Ventas",
    description="Gestiona el registro de transacciones comerciales de compra a proveedores y venta a clientes.",
    version="1.0.0"
)

# Base de datos en memoria para pedidos de compras y ventas
ventas_db: Dict[str, Dict[str, Any]] = {}
compras_db: Dict[str, Dict[str, Any]] = {}


class ItemVenta(BaseModel):
    producto_id: str
    nombre: str
    cantidad: int = Field(..., gt=0)
    precio_unitario: float = Field(..., gt=0)


class ClienteInfo(BaseModel):
    nombre: str
    documento: str
    direccion: str
    telefono: Optional[str] = "N/A"
    correo: Optional[str] = "cliente@example.com"


class RegistrarVentaRequest(BaseModel):
    cliente: ClienteInfo
    items: List[ItemVenta]
    metodo_pago: Optional[str] = "TRANSFERENCIA"
    observaciones: Optional[str] = ""


class ItemCompra(BaseModel):
    producto_id: str
    nombre: str
    cantidad: int = Field(..., gt=0)
    costo_unitario: float = Field(..., gt=0)


class ProveedorInfo(BaseModel):
    nombre: str
    nit: str
    contacto: Optional[str] = "Ventas Corporativas"
    telefono: Optional[str] = "N/A"
    correo: Optional[str] = "proveedor@example.com"


class RegistrarCompraRequest(BaseModel):
    proveedor: ProveedorInfo
    items: List[ItemCompra]
    terminos_pago: Optional[str] = "CREDITO_30_DIAS"
    observaciones: Optional[str] = ""


class RecibirFacturaRequest(BaseModel):
    referencia_operacion: str = Field(..., description="ID de la venta o compra (ej. VEN-... o COM-...)")
    numero_factura: str
    cufe: str
    fecha_emision: str
    total_facturado: float


@app.get("/")
def estado():
    return {
        "servicio": "Compras y Ventas",
        "estado": "ACTIVO",
        "total_ventas": len(ventas_db),
        "total_compras": len(compras_db),
        "metodos_disponibles": [
            "POST /registrarVenta",
            "POST /registrarCompra",
            "POST /recibirFactura",
            "GET /ventas",
            "GET /compras"
        ]
    }


@app.post("/registrarVenta")
def registrar_venta(payload: RegistrarVentaRequest):
    """
    Registra una nueva orden de venta hacia un cliente.
    Calcula subtotal, IVA (19%) y total general.
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="La venta debe contener al menos un producto.")

    id_venta = f"VEN-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    subtotal = sum(item.cantidad * item.precio_unitario for item in payload.items)
    iva = round(subtotal * 0.19, 2)
    total = round(subtotal + iva, 2)

    registro = {
        "id_venta": id_venta,
        "fecha": datetime.datetime.now().isoformat(),
        "cliente": payload.cliente.model_dump(),
        "items": [item.model_dump() for item in payload.items],
        "metodo_pago": payload.metodo_pago,
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
        "estado": "REGISTRADA",
        "factura": None,
        "observaciones": payload.observaciones
    }

    ventas_db[id_venta] = registro

    return {
        "status": "EXITOSO",
        "mensaje": "Venta registrada satisfactoriamente",
        "venta": registro
    }


@app.post("/registrarCompra")
def registrar_compra(payload: RegistrarCompraRequest):
    """
    Registra una orden de compra o abastecimiento a un proveedor.
    Calcula subtotal, IVA (19%) y total.
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="La compra debe contener al menos un producto.")

    id_compra = f"COM-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    subtotal = sum(item.cantidad * item.costo_unitario for item in payload.items)
    iva = round(subtotal * 0.19, 2)
    total = round(subtotal + iva, 2)

    registro = {
        "id_compra": id_compra,
        "fecha": datetime.datetime.now().isoformat(),
        "proveedor": payload.proveedor.model_dump(),
        "items": [item.model_dump() for item in payload.items],
        "terminos_pago": payload.terminos_pago,
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
        "estado": "REGISTRADA",
        "factura": None,
        "observaciones": payload.observaciones
    }

    compras_db[id_compra] = registro

    return {
        "status": "EXITOSO",
        "mensaje": "Compra registrada satisfactoriamente",
        "compra": registro
    }


@app.post("/recibirFactura")
def recibir_factura(payload: RecibirFacturaRequest):
    """
    Método requerido por el esquema:
    Recibe la confirmación y datos de la factura generada por Contabilidad
    y la vincula con la orden comercial correspondiente (venta o compra).
    """
    ref = payload.referencia_operacion
    factura_info = {
        "numero_factura": payload.numero_factura,
        "cufe": payload.cufe,
        "fecha_emision": payload.fecha_emision,
        "total_facturado": payload.total_facturado,
        "recibido_en": datetime.datetime.now().isoformat()
    }

    if ref in ventas_db:
        ventas_db[ref]["factura"] = factura_info
        ventas_db[ref]["estado"] = "FACTURADA"
        return {
            "status": "EXITOSO",
            "mensaje": f"Factura vinculada exitosamente a la venta {ref}",
            "tipo": "VENTA",
            "registro": ventas_db[ref]
        }
    elif ref in compras_db:
        compras_db[ref]["factura"] = factura_info
        compras_db[ref]["estado"] = "FACTURADA"
        return {
            "status": "EXITOSO",
            "mensaje": f"Factura vinculada exitosamente a la compra {ref}",
            "tipo": "COMPRA",
            "registro": compras_db[ref]
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró operación comercial con referencia '{ref}'."
        )


@app.get("/ventas")
def listar_ventas():
    return {
        "total": len(ventas_db),
        "ventas": list(ventas_db.values())
    }


@app.get("/ventas/{id_venta}")
def consultar_venta(id_venta: str):
    if id_venta not in ventas_db:
        raise HTTPException(status_code=404, detail="Venta no encontrada.")
    return ventas_db[id_venta]


@app.get("/compras")
def listar_compras():
    return {
        "total": len(compras_db),
        "compras": list(compras_db.values())
    }


@app.get("/compras/{id_compra}")
def consultar_compra(id_compra: str):
    if id_compra not in compras_db:
        raise HTTPException(status_code=404, detail="Compra no encontrada.")
    return compras_db[id_compra]
