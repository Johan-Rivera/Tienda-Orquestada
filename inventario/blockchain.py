import hashlib
import json
import time
from typing import List, Dict, Any, Optional


class Transaccion:
    def __init__(self, tipo: str, producto_id: str, nombre: str, cantidad: int, referencia: str, motivo: str = ""):
        self.tipo = tipo.upper()  # ADQUISICION, VENTA, AJUSTE_INICIAL
        self.producto_id = producto_id
        self.nombre = nombre
        self.cantidad = int(cantidad)
        self.referencia = referencia
        self.motivo = motivo
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo,
            "producto_id": self.producto_id,
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "referencia": self.referencia,
            "motivo": self.motivo,
            "timestamp": self.timestamp
        }


class Bloque:
    def __init__(self, index: int, timestamp: float, transacciones: List[Dict[str, Any]], previous_hash: str, proof: int = 0, hash_bloque: Optional[str] = None):
        self.index = index
        self.timestamp = timestamp
        self.transacciones = transacciones
        self.previous_hash = previous_hash
        self.proof = proof
        self.hash = hash_bloque or self.calcular_hash()

    def calcular_hash(self) -> str:
        bloque_serializado = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transacciones": self.transacciones,
            "previous_hash": self.previous_hash,
            "proof": self.proof
        }, sort_keys=True).encode("utf-8")
        return hashlib.sha256(bloque_serializado).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "fecha_legible": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp)),
            "transacciones": self.transacciones,
            "previous_hash": self.previous_hash,
            "proof": self.proof,
            "hash": self.hash
        }


class BlockchainInventario:
    def __init__(self):
        self.chain: List[Bloque] = []
        self.catalogo_base: Dict[str, Dict[str, Any]] = {
            "MUE-001": {
                "id": "MUE-001",
                "nombre": "Sofá Seccional Cuero 3 Puestos",
                "categoria": "Sala",
                "precio_unitario": 1200000.0,
                "costo_unitario": 750000.0,
                "stock_minimo": 4
            },
            "MUE-002": {
                "id": "MUE-002",
                "nombre": "Comedor Madera Roble 6 Puestos",
                "categoria": "Comedor",
                "precio_unitario": 950000.0,
                "costo_unitario": 600000.0,
                "stock_minimo": 3
            },
            "MUE-003": {
                "id": "MUE-003",
                "nombre": "Cama Queen Size Tapizada Gris",
                "categoria": "Dormitorio",
                "precio_unitario": 850000.0,
                "costo_unitario": 500000.0,
                "stock_minimo": 3
            },
            "MUE-004": {
                "id": "MUE-004",
                "nombre": "Escritorio Ergonómico Home Office",
                "categoria": "Estudio",
                "precio_unitario": 450000.0,
                "costo_unitario": 280000.0,
                "stock_minimo": 5
            },
            "MUE-005": {
                "id": "MUE-005",
                "nombre": "Mesa de Centro Rústica Pino",
                "categoria": "Sala",
                "precio_unitario": 220000.0,
                "costo_unitario": 130000.0,
                "stock_minimo": 4
            }
        }
        # Crear bloque génesis con inventario inicial
        self._crear_bloque_genesis()

    def _crear_bloque_genesis(self):
        transacciones_genesis = [
            Transaccion("AJUSTE_INICIAL", "MUE-001", "Sofá Seccional Cuero 3 Puestos", 10, "GENESIS-001", "Carga inicial de inventario").to_dict(),
            Transaccion("AJUSTE_INICIAL", "MUE-002", "Comedor Madera Roble 6 Puestos", 8, "GENESIS-001", "Carga inicial de inventario").to_dict(),
            Transaccion("AJUSTE_INICIAL", "MUE-003", "Cama Queen Size Tapizada Gris", 7, "GENESIS-001", "Carga inicial de inventario").to_dict(),
            Transaccion("AJUSTE_INICIAL", "MUE-004", "Escritorio Ergonómico Home Office", 12, "GENESIS-001", "Carga inicial de inventario").to_dict(),
            Transaccion("AJUSTE_INICIAL", "MUE-005", "Mesa de Centro Rústica Pino", 6, "GENESIS-001", "Carga inicial de inventario").to_dict()
        ]
        bloque_genesis = Bloque(
            index=0,
            timestamp=time.time(),
            transacciones=transacciones_genesis,
            previous_hash="0" * 64,
            proof=100
        )
        self.chain.append(bloque_genesis)

    @property
    def ultimo_bloque(self) -> Bloque:
        return self.chain[-1]

    def prueba_trabajo(self, ultimo_proof: int) -> int:
        """Algoritmo de consenso PoW liviano: encontrar p tal que sha256(last_p, p) comience con '00'"""
        proof = 0
        while not self.validar_prueba(ultimo_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def validar_prueba(ultimo_proof: int, proof: int) -> bool:
        guess = f"{ultimo_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:2] == "00"

    def calcular_stock(self, producto_id: str) -> int:
        """Calcula el stock actual a partir de la historia inmutable de la blockchain"""
        stock = 0
        for bloque in self.chain:
            for tx in bloque.transacciones:
                if tx["producto_id"] == producto_id:
                    if tx["tipo"] in ["ADQUISICION", "AJUSTE_INICIAL"]:
                        stock += tx["cantidad"]
                    elif tx["tipo"] == "VENTA":
                        stock -= tx["cantidad"]
        return stock

    def obtener_productos_con_stock(self) -> List[Dict[str, Any]]:
        """Calcula el estado actual del catálogo utilizando el ledger inmutable de blockchain"""
        resultado = []
        for pid, prod in self.catalogo_base.items():
            stock = self.calcular_stock(pid)
            resultado.append({
                "id": prod["id"],
                "nombre": prod["nombre"],
                "categoria": prod["categoria"],
                "precio_unitario": prod["precio_unitario"],
                "costo_unitario": prod["costo_unitario"],
                "stock_actual": stock,
                "stock_minimo": prod["stock_minimo"],
                "requiere_reabastecimiento": stock <= prod["stock_minimo"]
            })
        return resultado

    def obtener_requerimientos(self) -> List[Dict[str, Any]]:
        """Genera requerimientos de abastecimiento para compras a proveedores basados en stock mínimo"""
        requerimientos = []
        for prod in self.obtener_productos_con_stock():
            if prod["requiere_reabastecimiento"]:
                nivel_urgencia = "ALTA" if prod["stock_actual"] == 0 else "MEDIA"
                deficit = (prod["stock_minimo"] * 2) - prod["stock_actual"]
                cantidad_sugerida = max(deficit, 5)
                requerimientos.append({
                    "producto_id": prod["id"],
                    "nombre": prod["nombre"],
                    "categoria": prod["categoria"],
                    "stock_actual": prod["stock_actual"],
                    "stock_minimo": prod["stock_minimo"],
                    "cantidad_sugerida": cantidad_sugerida,
                    "costo_estimado_unitario": prod["costo_unitario"],
                    "urgencia": nivel_urgencia
                })
        return requerimientos

    def registrar_operacion(self, tipo: str, producto_id: str, cantidad: int, referencia: str, motivo: str = "") -> Dict[str, Any]:
        """
        Registra una transacción (adquisición o venta) y mina un nuevo bloque en la blockchain.
        Valida reglas de negocio: el stock no puede ser negativo en caso de venta.
        """
        if producto_id not in self.catalogo_base:
            raise ValueError(f"Producto con ID '{producto_id}' no existe en el catálogo.")

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")

        tipo = tipo.upper()
        if tipo not in ["ADQUISICION", "VENTA"]:
            raise ValueError("El tipo de operación debe ser 'ADQUISICION' o 'VENTA'.")

        stock_actual = self.calcular_stock(producto_id)
        if tipo == "VENTA" and stock_actual < cantidad:
            raise ValueError(f"Stock insuficiente para {producto_id}. Stock actual: {stock_actual}, solicitado: {cantidad}.")

        prod_info = self.catalogo_base[producto_id]
        nueva_tx = Transaccion(
            tipo=tipo,
            producto_id=producto_id,
            nombre=prod_info["nombre"],
            cantidad=cantidad,
            referencia=referencia,
            motivo=motivo
        ).to_dict()

        # Minar nuevo bloque
        ultimo_bloque = self.ultimo_bloque
        proof = self.prueba_trabajo(ultimo_bloque.proof)
        nuevo_bloque = Bloque(
            index=len(self.chain),
            timestamp=time.time(),
            transacciones=[nueva_tx],
            previous_hash=ultimo_bloque.hash,
            proof=proof
        )

        self.chain.append(nuevo_bloque)
        nuevo_stock = self.calcular_stock(producto_id)

        return {
            "status": "EXITOSO",
            "tipo_operacion": tipo,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "stock_anterior": stock_actual,
            "stock_resultante": nuevo_stock,
            "bloque_minado": nuevo_bloque.to_dict()
        }

    def es_cadena_valida(self) -> Dict[str, Any]:
        """Valida criptográficamente la integridad de toda la cadena de bloques"""
        for i in range(1, len(self.chain)):
            bloque_actual = self.chain[i]
            bloque_anterior = self.chain[i - 1]

            # Verificar hash previo
            if bloque_actual.previous_hash != bloque_anterior.hash:
                return {
                    "valida": False,
                    "error": f"Hash previo inconsistente en bloque {i}. Esperado {bloque_anterior.hash}, obtenido {bloque_actual.previous_hash}"
                }

            # Recalcular hash del bloque
            if bloque_actual.hash != bloque_actual.calcular_hash():
                return {
                    "valida": False,
                    "error": f"Hash alterado en bloque {i}. Calculado {bloque_actual.calcular_hash()}, almacenado {bloque_actual.hash}"
                }

            # Validar prueba de trabajo
            if not self.validar_prueba(bloque_anterior.proof, bloque_actual.proof):
                return {
                    "valida": False,
                    "error": f"Prueba de trabajo inválida en bloque {i}"
                }

        return {
            "valida": True,
            "total_bloques": len(self.chain),
            "mensaje": "La blockchain es íntegra y válida."
        }
