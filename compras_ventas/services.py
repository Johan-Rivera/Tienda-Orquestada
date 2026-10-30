import uuid
import datetime
from typing import Dict, Any, List
from schemas.compras_ventas import RegistrarVentaRequest, RegistrarCompraRequest, RecibirFacturaRequest


class GestorComprasVentas:
    """
    Clase que encapsula el registro, control y consulta de operaciones de compra y venta.
    """

    def __init__(self):
        self.ventas_db: Dict[str, Dict[str, Any]] = {}
        self.compras_db: Dict[str, Dict[str, Any]] = {}

    def registrar_venta(self, payload: RegistrarVentaRequest) -> Dict[str, Any]:
        if not payload.items:
            raise ValueError("La venta debe contener al menos un producto.")

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
            "observaciones": payload.observaciones or ""
        }

        self.ventas_db[id_venta] = registro
        return registro

    def registrar_compra(self, payload: RegistrarCompraRequest) -> Dict[str, Any]:
        if not payload.items:
            raise ValueError("La compra debe contener al menos un producto.")

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
            "observaciones": payload.observaciones or ""
        }

        self.compras_db[id_compra] = registro
        return registro

    def recibir_factura(self, payload: RecibirFacturaRequest) -> Dict[str, Any]:
        ref = payload.referencia_operacion
        factura_info = {
            "numero_factura": payload.numero_factura,
            "cufe": payload.cufe,
            "fecha_emision": payload.fecha_emision,
            "total_facturado": payload.total_facturado,
            "recibido_en": datetime.datetime.now().isoformat()
        }

        if ref in self.ventas_db:
            self.ventas_db[ref]["factura"] = factura_info
            self.ventas_db[ref]["estado"] = "FACTURADA"
            return {
                "status": "EXITOSO",
                "mensaje": f"Factura vinculada exitosamente a la venta {ref}",
                "tipo": "VENTA",
                "registro": self.ventas_db[ref]
            }
        elif ref in self.compras_db:
            self.compras_db[ref]["factura"] = factura_info
            self.compras_db[ref]["estado"] = "FACTURADA"
            return {
                "status": "EXITOSO",
                "mensaje": f"Factura vinculada exitosamente a la compra {ref}",
                "tipo": "COMPRA",
                "registro": self.compras_db[ref]
            }
        else:
            return None

    def listar_ventas(self) -> List[Dict[str, Any]]:
        return list(self.ventas_db.values())

    def listar_compras(self) -> List[Dict[str, Any]]:
        return list(self.compras_db.values())
