import hashlib
import datetime
from typing import Dict, Any, List
from schemas.contabilidad import GenerarFacturaRequest


class GestorContable:
    """
    Clase de dominio orientada a objetos (POO) que encapsula
    la emisión de facturas electrónicas, generación de CUFE y balance contable.
    """

    def __init__(self):
        self.facturas_db: Dict[str, Dict[str, Any]] = {}
        self.contador_ventas = 1000
        self.contador_compras = 5000

    def generar_factura(self, payload: GenerarFacturaRequest) -> Dict[str, Any]:
        tipo = payload.tipo_operacion.upper()
        if tipo not in ["VENTA", "COMPRA"]:
            raise ValueError("El tipo de operación debe ser 'VENTA' o 'COMPRA'.")

        fecha_emision = datetime.datetime.now().isoformat()

        if tipo == "VENTA":
            self.contador_ventas += 1
            prefijo = "FE-VEN"
            numero_factura = f"{prefijo}-{self.contador_ventas}"
        else:
            self.contador_compras += 1
            prefijo = "FE-COM"
            numero_factura = f"{prefijo}-{self.contador_compras}"

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

        self.facturas_db[numero_factura] = factura

        return {
            "status": "EXITOSO",
            "mensaje": f"Factura electrónica {numero_factura} emitida correctamente",
            "factura": factura
        }

    def listar_facturas(self) -> List[Dict[str, Any]]:
        return list(self.facturas_db.values())

    def obtener_balance(self) -> Dict[str, Any]:
        total_ingresos = sum(f["total"] for f in self.facturas_db.values() if f["tipo_operacion"] == "VENTA")
        total_egresos = sum(f["total"] for f in self.facturas_db.values() if f["tipo_operacion"] == "COMPRA")
        balance_neto = total_ingresos - total_egresos

        return {
            "total_ingresos_ventas": round(total_ingresos, 2),
            "total_egresos_compras": round(total_egresos, 2),
            "balance_neto": round(balance_neto, 2),
            "cantidad_facturas_emitidas": len(self.facturas_db)
        }
