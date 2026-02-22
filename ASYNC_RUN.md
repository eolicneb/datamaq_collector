# ASYNC_MAIN.md

Documentación de las funcionalidades implementadas en `async_run.py`.

## Ejecución

```bash
python async_run.py
```

## Componentes Inicializados

### 1. ThreadPoolExecutor
```python
executor = ThreadPoolExecutor(max_workers=10)
```
Pool de threads para operaciones bloqueantes (serial, HTTP). Compartido entre logger asíncrono y controlador.

### 2. Lectura Modbus

| Componente | Clase | Propósito |
|------------|-------|-----------|
| `conn_manager` | `ModbusConnectionManager` | Detecta puerto COM ("DigiRail Connect" o "USB-SERIAL CH340") y establece conexión |
| `device` | `ModbusDevice` | Wrapper de `minimalmodbus.Instrument` con lectura segura |
| `modbus` | `ModbusScanner` | Scheduler de lecturas periódicas |

**Configuración actual:**
```python
ModbusReadingSetup(
    read_address=ModbusReadAddress(address=22, bytes_count=2),
    name="vel_upm",
    period=0.2  # cada 200ms
)
```
Lee 2 registros desde dirección 22, etiqueta "vel_upm".

### 3. Cache en Memoria

```python
cache = MemoryCache(max_readings=5)
```
Buffer circular por etiqueta. Máximo 5 lecturas por label antes de descartar las más antiguas.

### 4. Persistencia a MySQL

| Componente | Clase | Propósito |
|------------|-------|-----------|
| `repo` | `SQLAlchemyDatabaseRepository` | Inserta readings en MySQL |
| `transfer` | `CachedDataTransferController` | Agrega datos del cache y persiste |

**Configuración actual:**
```python
DataPersistSetup(
    label="vel_upm",
    period=5,              # cada 5 segundos
    method="average_readings",  # promedio de lecturas en ventana
    units="unidades/min"
)
```
Cada 5 segundos: obtiene lecturas de los últimos 5s, calcula promedio, inserta en DB.

### 5. Cliente REST

```python
rest_client = create_rest_client(cache)
```

**Endpoints configurados:**

| Objeto | URI | Período | Campos |
|--------|-----|---------|--------|
| `edge` | `http://localhost:5001/edge` | 0.5s | `position` (int, px) |
| `buttler` | `http://localhost:5000/reel` | 5s | `diameter`, `width`, `height` (int, px) |

**Transferencia REST → DB:**
```python
set_rest_client_transfer(transfer)
```
Configura persistencia para: `edge_position`, `buttler_diameter`, `buttler_width` (promedio cada 5s).

### 6. Controlador Principal

```python
controller = AsyncAppController(process, period=0.01, executor=executor)
```
Loop principal con período de 10ms. Ejecuta en paralelo:
```python
await asyncio.gather(modbus.process(), rest_client.process(), transfer.process())
```

## Flujo de Datos

```
┌─────────────────┐     ┌─────────────────┐
│  ModbusScanner  │     │   RestClient    │
│  (period=0.2s)  │     │  (period=0.5s)  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    save_reading()     │
         └──────────┬────────────┘
                    ▼
           ┌────────────────┐
           │  MemoryCache   │
           │ (max=5/label)  │
           └────────┬───────┘
                    │
                    │ get_last_reading_for_label(since=now-period)
                    ▼
    ┌───────────────────────────────┐
    │ CachedDataTransferController  │
    │       (period=5s)             │
    │  average_readings() → INSERT  │
    └───────────────────────────────┘
                    │
                    ▼
           ┌────────────────┐
           │     MySQL      │
           │ (readings tbl) │
           └────────────────┘
```

## Señales del Sistema

El `AsyncAppController` maneja:
- **Unix**: `SIGINT`, `SIGTERM` → termina loop gracefully
- **Windows**: `KeyboardInterrupt` (Ctrl+C)

## Scheduler Interno

Cada componente usa `ScheduledController` con:
- Tracking de período y última ejecución
- Detección de pasos perdidos (si el proceso tarda más que el período)
- Ejecuta métodos parciales (`functools.partial`) con timestamp actual
