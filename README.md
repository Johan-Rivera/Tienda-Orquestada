# Sistema Distribuido Orquestado con Middleware - Tienda de Muebles

**Curso:** Sistemas Distribuidos  
**Taller Corte 2:** Middleware (Coreografías, Coordinación y Orquestación)  
**Profesor:** Carlos Armando López Solano, MSc.  
**Institución:** Corporación Universitaria Minuto de Dios (UNIMINUTO)  

---

## 1. Resumen Ejecutivo y Transformación de Arquitectura

El presente proyecto implementa un **sistema de software distribuido** para una tienda de muebles, donde el componente neurálgico es un **Middleware Orquestador** encargado de coordinar de forma centralizada todas las transacciones de **Venta a Clientes** y de **Compra / Abastecimiento a Proveedores**.

### 1.1. Arquitectura Original (Coordinada / Coreografiada) vs. Arquitectura Transformada (Orquestada con Middleware)

* **Arquitectura Original (Esquema del PDF - Coreografía/Coordinación P2P):**  
  En el diseño inicial, los componentes interactuaban entre sí de manera descentralizada y punto a punto:
  - El `Cliente` interactuaba con la `Tienda`. La `Tienda` debía invocar directamente a `Inventario.cargarProductos()`, llamar a `Compras/Ventas.registrarVenta()` y luego ordenar el despacho a `Transportador.ordenarTransporte()`.
  - A su vez, `Compras/Ventas` debía invocar a `Contabilidad.generarFactura()` y recibir la confirmación `recibirFactura()`.
  - El `Proveedor` interactuaba con `AtenciónProveedores`, que a su vez debía consultar directamente `Inventario.cargarRequerimientosProductos()` y llamar a `Compras/Ventas.registrarCompra()`.
  
  **Desventajas del esquema original:**
  1. *Fuerte acoplamiento:* Cada microservicio debía conocer las URLs, contratos y estados internos de los demás.
  2. *Manejo de fallos complejo:* Si fallaba la facturación o el transporte, revertir la venta o el inventario requería compensaciones distribuidas en cascada difíciles de auditar.
  3. *Lógica de negocio dispersa:* Las reglas de validación de crédito, stock mínimo y control tributario estaban fragmentadas en la interfaz de la tienda y la interfaz de proveedores.

* **Arquitectura Transformada (Orquestación con Middleware):**  
  Se transformó el sistema incorporando un **Middleware Orquestador Central**, el cual asume el rol de director de orquesta:
  - La `Tienda` y el portal de `Atención a Proveedores` delegan toda la lógica transaccional al **Middleware**.
  - El **Middleware** ejecuta las secuencias de negocio completas, valida precondiciones (como la existencia y stock en Blockchain), coordina en orden estricto las invocaciones REST hacia los servicios de dominio (`Inventario`, `Compras/Ventas`, `Contabilidad`, `Transportador`), consolida los resultados y provee trazabilidad y bitácora unificada de cada proceso.

```
+-----------------------------------------------------------------------------------------+
|                               ARQUITECTURA ORQUESTADA                                   |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|       [ Cliente ]                                      [ Proveedor ]                    |
|            |                                                 |                          |
|            v                                                 v                          |
|     +--------------+                                 +------------------------+         |
|     |    Tienda    |                                 |  AtenciónProveedores   |         |
|     | (Puerto 8005)|                                 |      (Puerto 8006)     |         |
|     +-------+------+                                 +-----------+------------+         |
|             \                                                   /                       |
|              \                     POST /orquestar/compra      /                        |
|   POST        \                  GET /orquestar/requerimientos/                         |
|   /orquestar/  \                                             /                          |
|   venta         v                                           v                           |
|             +====================================================+                      |
|             |             MIDDLEWARE ORQUESTADOR                 |                      |
|             |                  (Puerto 8000)                     |                      |
|             +====================================================+                      |
|                      |             |             |            |                         |
|      (1) Stock & PoW |         (2) |         (3) |        (4) |                         |
|            Minado    |   Contratos |   Factura & |  Despacho  |                         |
|                      v             v        CUFE v            v                         |
|               +------------+ +-----------+ +------------+ +---------------+             |
|               | Inventario | |  Compras/ | |Contabilidad| | Transportador |             |
|               | Blockchain | |   Ventas  | |Facturación | |   Logística   |             |
|               |(Port 8001) | |(Port 8002)| |(Port 8003) | | (Port 8004)   |             |
|               +------------+ +-----------+ +------------+ +---------------+             |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Mapeo de Flujos de Negocio

### 2.1. Flujo Orquestado de Venta a Clientes (`POST /orquestar/venta`)

1. **Recepción:** El cliente solicita la compra de muebles desde la `Tienda` (o directamente al Middleware).
2. **Paso 1 (Inventario - Blockchain):** El Middleware invoca `GET /cargarProductos` en el servicio de Inventario. Verifica la disponibilidad de existencias calculadas criptográficamente. Si el stock es insuficiente, se interrumpe la orquestación y se retorna error controlado (HTTP 400).
3. **Paso 2 (Compras/Ventas):** El Middleware invoca `POST /registrarVenta`, registrando la orden comercial con los precios unitarios, subtotal, IVA (19%) y total general. Se asigna un identificador `id_venta`.
4. **Paso 3 (Contabilidad):** El Middleware invoca `POST /generarFactura`, generando la Factura Electrónica legal con número consecutivo oficial y el cálculo del CUFE (Código Único de Factura Electrónica) mediante hash criptográfico SHA-256.
5. **Paso 4 (Compras/Ventas):** El Middleware invoca `POST /recibirFactura`, asociando el número de factura y CUFE a la orden comercial de venta y marcándola como `FACTURADA`.
6. **Paso 5 (Inventario - Blockchain):** Por cada producto vendido, el Middleware invoca `POST /actualizarInventario` con tipo `VENTA`. El servicio de Inventario ejecuta el algoritmo de consenso PoW (Proof of Work), mina un nuevo bloque inmutable en la cadena y descuenta el stock.
7. **Paso 6 (Transportador):** El Middleware invoca `POST /ordenarTransporte`, asignando transportadora, vehículo (camión), ruta y emitiendo el número de guía de despacho logístico con fecha estimada de entrega.
8. **Paso 7 (Consolidación y Auditoría):** El Middleware registra la bitácora completa en su almacén de trazabilidad y entrega al cliente la respuesta consolidada con factura, guía y hashes de la Blockchain.

### 2.2. Flujo Orquestado de Compra a Proveedores (`POST /orquestar/compra`)

1. **Recepción:** El proveedor o el área de compras inicia un pedido de abastecimiento desde `Atención a Proveedores`.
2. **Paso 1 (Inventario):** El Middleware verifica los ítems contra el catálogo de productos y costos autorizados.
3. **Paso 2 (Compras/Ventas):** El Middleware invoca `POST /registrarCompra`, generando la orden de compra mercantil (`id_compra`) con los términos de pago pactados.
4. **Paso 3 (Contabilidad):** El Middleware invoca `POST /generarFactura` con tipo `COMPRA`, registrando la cuenta por pagar fiscal y emitiendo factura con CUFE.
5. **Paso 4 (Compras/Ventas):** El Middleware invoca `POST /recibirFactura` vinculando la factura contable a la compra mercantil.
6. **Paso 5 (Inventario - Blockchain):** Por cada producto ingresado, el Middleware invoca `POST /actualizarInventario` con tipo `ADQUISICION`. Se mina un nuevo bloque en la Blockchain aumentando las existencias de forma inmutable.
7. **Paso 6 (Consolidación):** El Middleware registra la trazabilidad del reabastecimiento y entrega la confirmación al proveedor.

---

## 3. Matriz de Métodos Web, Parámetros y Respuestas

A continuación se especifican los contratos REST de cada componente:

| Componente | Método HTTP | Endpoint | Parámetros de Entrada (Request Body / Query) | Objeto de Retorno (Response Body) | Códigos HTTP |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Inventario** | `GET` | `/cargarProductos` | Ninguno | `{"status": "EXITOSO", "total_productos": int, "productos": [{"id": str, "nombre": str, "precio_unitario": float, "stock_actual": int, ...}]}` | 200 |
| **Inventario** | `GET` | `/cargarRequerimientosProductos` | Ninguno | `{"status": "EXITOSO", "total_requerimientos": int, "requerimientos": [{"producto_id": str, "stock_actual": int, "cantidad_sugerida": int, ...}]}` | 200 |
| **Inventario** | `POST` | `/actualizarInventario` | `{"tipo": "VENTA"\|"ADQUISICION", "producto_id": str, "cantidad": int, "referencia": str, "motivo": str}` | `{"status": "EXITOSO", "stock_anterior": int, "stock_resultante": int, "bloque_minado": {"index": int, "proof": int, "hash": str, ...}}` | 200, 400 |
| **Inventario** | `GET` | `/blockchain` | Ninguno | `{"blockchain_valida": bool, "longitud": int, "cadena": [bloques...]}` | 200 |
| **Compras/Ventas**| `POST` | `/registrarVenta` | `{"cliente": {...}, "items": [{"producto_id": str, "cantidad": int, "precio_unitario": float}], "metodo_pago": str}` | `{"status": "EXITOSO", "venta": {"id_venta": str, "subtotal": float, "iva": float, "total": float, "estado": "REGISTRADA"}}` | 200, 400 |
| **Compras/Ventas**| `POST` | `/registrarCompra` | `{"proveedor": {...}, "items": [{"producto_id": str, "cantidad": int, "costo_unitario": float}], "terminos_pago": str}` | `{"status": "EXITOSO", "compra": {"id_compra": str, "subtotal": float, "iva": float, "total": float, "estado": "REGISTRADA"}}` | 200, 400 |
| **Compras/Ventas**| `POST` | `/recibirFactura` | `{"referencia_operacion": str, "numero_factura": str, "cufe": str, "fecha_emision": str, "total_facturado": float}` | `{"status": "EXITOSO", "registro": {...}}` | 200, 404 |
| **Contabilidad** | `POST` | `/generarFactura` | `{"tipo_operacion": "VENTA"\|"COMPRA", "referencia_operacion": str, "emisor": str, "receptor": str, "subtotal": float, "iva": float, "total": float, "detalles": [...]}` | `{"status": "EXITOSO", "factura": {"numero_factura": str, "cufe": str, "fecha_emision": str, "estado_tributario": "VALIDADA_DIAN"}}` | 200, 400 |
| **Contabilidad** | `GET` | `/balance` | Ninguno | `{"total_ingresos_ventas": float, "total_egresos_compras": float, "balance_neto": float, "cantidad_facturas_emitidas": int}` | 200 |
| **Transportador** | `POST` | `/ordenarTransporte`| `{"id_venta": str, "destinatario": str, "direccion_entrega": str, "ciudad": str, "paquetes": [...]}` | `{"status": "EXITOSO", "guia": {"numero_guia": str, "transportadora": str, "vehiculo_asignado": str, "fecha_estimada_entrega": str}}` | 200, 400 |
| **Middleware** | `POST` | `/orquestar/venta` | `{"cliente": {...}, "items": [{"producto_id": str, "cantidad": int}], "metodo_pago": str}` | Resumen consolidado: `id_venta`, `numero_factura`, `cufe`, `numero_guia_transporte`, `bloques_blockchain`, etc. | 200, 400, 502, 503 |
| **Middleware** | `POST` | `/orquestar/compra` | `{"proveedor": {...}, "items": [{"producto_id": str, "cantidad": int}], "terminos_pago": str}` | Resumen consolidado: `id_compra`, `numero_factura`, `cufe`, `bloques_blockchain` | 200, 400, 502, 503 |
| **Middleware** | `GET` | `/orquestar/salud` | Ninguno | Diagnóstico en tiempo real del estado de conexión hacia los 4 microservicios de dominio. | 200 |
| **Tienda** | `POST` | `/comprar` | `{"cliente": {...}, "items": [...]}` | Delega y retorna el resultado de `Middleware.orquestar_venta()` | 200, 400, 503 |
| **Atención Prov.**| `POST` | `/abastecer` | `{"proveedor": {...}, "items": [...]}` | Delega y retorna el resultado de `Middleware.orquestar_compra()` | 200, 400, 503 |

---

## 4. Implementación de la Blockchain en Inventario

El componente `inventario` incorpora un ledger distribuido inmutable desarrollado en Python (`inventario/blockchain.py`):

1. **Estructura del Bloque:**
   - `index`: Posición secuencial del bloque en la cadena.
   - `timestamp`: Marca de tiempo Unix de la creación del bloque.
   - `transacciones`: Lista de operaciones criptográficamente selladas (`tipo`, `producto_id`, `nombre`, `cantidad`, `referencia`, `motivo`, `timestamp`).
   - `previous_hash`: Hash SHA-256 del bloque precedente.
   - `proof` (Nonce): Número entero obtenido mediante el algoritmo de prueba de trabajo.
   - `hash`: Hash criptográfico SHA-256 representativo del contenido inmutable del bloque.
2. **Bloque Génesis:**
   - Se crea automáticamente al inicializar el servicio con el índice `0`, hash previo `0000...0000` y transacciones de tipo `AJUSTE_INICIAL` que cargan el inventario base del almacén de muebles.
3. **Prueba de Trabajo (PoW - Consensus):**
   - Implementa la función `prueba_trabajo(ultimo_proof)`, encontrando un valor tal que `sha256(ultimo_proof, proof)` cumpla con la dificultad establecida (prefijo `00`), garantizando la resistencia ante manipulaciones.
4. **Cálculo Dinámico de Existencias:**
   - El inventario **no** se guarda como una simple variable modificable. La función `calcular_stock(producto_id)` recorre toda la cadena de bloques desde el bloque génesis y computa:
     $$\text{Stock Actual} = \sum (\text{ADQUISICION} + \text{AJUSTE\_INICIAL}) - \sum (\text{VENTA})$$
5. **Auditoría e Integridad (`GET /blockchain`):**
   - El método `es_cadena_valida()` verifica que ningún bloque haya sido alterado recalculando los hashes y validando la continuidad de los `previous_hash`.

---

## 5. Estructura del Proyecto

Cada componente está aislado dentro de su propia carpeta de microservicio:

```
middleware/
├── TallerCorte2TiendaMuebles2026-1.docx.pdf   # Documento oficial del taller
├── README.md                                  # Documentación técnica completa
├── inventario/                                # Microservicio Inventario con Blockchain
│   ├── blockchain.py                          # Algoritmo de Blockchain, PoW y SHA-256
│   └── main.py                                # API FastAPI (cargarProductos, actualizarInventario, etc.)
├── compras_ventas/                            # Microservicio Compras y Ventas
│   └── main.py                                # API FastAPI (registrarVenta, registrarCompra, recibirFactura)
├── contabilidad/                              # Microservicio Contabilidad y Facturación
│   └── main.py                                # API FastAPI (generarFactura, balance, CUFE)
├── transportador/                             # Microservicio Transportador y Logística
│   └── main.py                                # API FastAPI (ordenarTransporte, guías, vehículos)
├── middleware/                                # Componente Principal: Middleware Orquestador
│   └── main.py                                # Motor de Orquestación Central (orquestar/venta, orquestar/compra)
├── tienda/                                    # Portal Web y Gateway Cliente
│   └── main.py                                # Interfaz Web HTML y API cliente
├── atencion_proveedores/                      # Portal Web y Gateway Proveedores
│   └── main.py                                # Interfaz Web HTML y API proveedores
└── scripts/
    ├── comandos_manuales.txt                  # Listado de comandos Docker manuales
    ├── iniciar_contenedores.ps1               # Script PowerShell para iniciar los 7 contenedores
    ├── detener_contenedores.ps1               # Script PowerShell para detener y limpiar contenedores
    ├── iniciar_contenedores.sh                # Script Bash para entornos Linux/macOS
    ├── detener_contenedores.sh                # Script Bash para detener en Linux/macOS
    └── probar_sistema.py                      # Script de pruebas end-to-end automatizadas
```

> **OPTIMIZACIÓN:** Como todos los microservicios comparten la misma base (`fastapi`, `uvicorn`, `pydantic` y `httpx`), no se requiere un archivo `requirements.txt` redundante en cada carpeta. En su lugar, se instala la pila tecnológica una única vez sobre un contenedor Alpine y se genera la imagen base `alpine-fastapi:latest` mediante **`docker commit`** (sin Dockerfile ni docker-compose).

---

## 6. Despliegue Manual en Contenedores Alpine por Comandos

### Paso 1: Creación de la Imagen Base con `docker commit` (Una Sola Vez)
Para evitar instalaciones repetitivas en cada contenedor, se crea la imagen base compartida:
```powershell
# 1. Ejecutar contenedor temporal para instalar las librerías
docker run --name builder-alpine-fastapi --dns 8.8.8.8 alpine:latest sh -c "apk add --no-cache python3 py3-pip && pip install --no-cache-dir --break-system-packages fastapi uvicorn pydantic httpx"

# 2. Generar la imagen local con docker commit
docker commit builder-alpine-fastapi alpine-fastapi:latest

# 3. Remover el contenedor temporal de construcción
docker rm builder-alpine-fastapi
```

### Paso 2: Crear la Red Bridge de Docker
```bash
docker network create red-muebles
```

### Paso 3: Ejecutar los Contenedores Manualmente
Ubicado en el directorio raíz del proyecto (`c:\Users\johan\Downloads\a\middleware`), ejecute los siguientes comandos:

#### En Windows PowerShell:
```powershell
# 1. Inventario con Blockchain (Puerto 8001)
docker run -d --name c-inventario --network red-muebles -p 8001:8001 -v "${PWD}/inventario:/app" -w /app alpine-fastapi:latest uvicorn main:app --host 0.0.0.0 --port 8001

# 2. Compras y Ventas (Puerto 8002)
docker run -d --name c-compras-ventas --network red-muebles -p 8002:8002 -v "${PWD}/compras_ventas:/app" -w /app alpine-fastapi:latest uvicorn main:app --host 0.0.0.0 --port 8002

# 3. Contabilidad y Facturación (Puerto 8003)
docker run -d --name c-contabilidad --network red-muebles -p 8003:8003 -v "${PWD}/contabilidad:/app" -w /app alpine-fastapi:latest uvicorn main:app --host 0.0.0.0 --port 8003

# 4. Transportador y Logística (Puerto 8004)
docker run -d --name c-transportador --network red-muebles -p 8004:8004 -v "${PWD}/transportador:/app" -w /app alpine-fastapi:latest uvicorn main:app --host 0.0.0.0 --port 8004

# 5. Middleware Orquestador Central (Puerto 8000)
docker run -d --name c-middleware --network red-muebles -p 8000:8000 -v "${PWD}/middleware:/app" -w /app alpine-fastapi:latest uvicorn main:app --host 0.0.0.0 --port 8000

# 6. Portal Tienda Cliente (Puerto 8005)
docker run -d --name c-tienda --network red-muebles -p 8005:8005 -v "${PWD}/tienda:/app" -w /app alpine-fastapi:latest uvicorn main:app --host 0.0.0.0 --port 8005

# 7. Portal Atención Proveedores (Puerto 8006)
docker run -d --name c-atencion-proveedores --network red-muebles -p 8006:8006 -v "${PWD}/atencion_proveedores:/app" -w /app alpine-fastapi:latest uvicorn main:app --host 0.0.0.0 --port 8006
```

*(Nota: También puede ejecutar directamente `./scripts/iniciar_contenedores.ps1` en PowerShell o `./scripts/iniciar_contenedores.sh` en Bash).*

*(Nota: También puede ejecutar directamente `./scripts/iniciar_contenedores.ps1` en PowerShell o `./scripts/iniciar_contenedores.sh` en Bash).*

### Paso 3: Verificar los Contenedores
```bash
docker ps
```
Debe observar los 7 contenedores con estado `Up`.

---

## 7. Pruebas y Validación del Sistema

### 7.1. Ejecución del Script de Prueba Automatizado
El repositorio incluye un script completo de prueba end-to-end (`scripts/probar_sistema.py`) que valida:
- Conectividad y salud del Middleware y los 6 microservicios.
- Consulta de catálogo y balance inicial de la Blockchain.
- Ejecución completa de una venta orquestada (con facturación DIAN, CUFE, transporte y minado PoW en Blockchain).
- Ejecución completa de una compra orquestada a proveedores (con aumento de existencias en Blockchain).
- Verificación matemática de la integridad de la cadena de bloques (`valida: True`).
- Balance contable consolidado.

Para ejecutarlo:
```powershell
py scripts/probar_sistema.py
```

### 7.2. Acceso a las Interfaces Web y Documentación Swagger
Una vez levantados los contenedores, puede interactuar con el sistema a través de su navegador web:

- **Middleware Orquestador (Documentación Swagger):**  
  [http://localhost:8000/docs](http://localhost:8000/docs)
- **Portal Web de la Tienda (Cliente):**  
  [http://localhost:8005](http://localhost:8005)
- **Portal Web de Atención a Proveedores:**  
  [http://localhost:8006](http://localhost:8006)
- **Auditoría de Blockchain en Inventario:**  
  [http://localhost:8001/blockchain](http://localhost:8001/blockchain)
- **Balance Financiero Contable:**  
  [http://localhost:8003/balance](http://localhost:8003/balance)

---

## 8. Detención y Limpieza de Recursos

Para detener y eliminar todos los contenedores y la red creada:
```powershell
docker stop c-inventario c-compras-ventas c-contabilidad c-transportador c-middleware c-tienda c-atencion-proveedores
docker rm c-inventario c-compras-ventas c-contabilidad c-transportador c-middleware c-tienda c-atencion-proveedores
docker network rm red-muebles
```
*(O ejecute `./scripts/detener_contenedores.ps1` en PowerShell).*
