# Bitácora de desarrollo — `persistencia-consultas`

Registro de todo lo que se va construyendo, en orden, con el comando que lo verifica.
Si hay que retomar el trabajo desde cero, este archivo es el punto de entrada: alcanza
con leerlo para saber qué está hecho, qué falta y cómo comprobarlo.

- **Repositorio:** https://github.com/ManuelGomez33/persistencia-consultas
- **Contrato:** `microservicios-pdf` v1.0.0 (PDF "Pasos para desarrollar los microservicios")
- **Metodología:** la definida en `CLAUDE.md` — TDD con commit rojo antes del verde.

## Cómo levantar y probar el proyecto

```bash
uv sync                                  # instalar dependencias
uv run pytest -v                         # correr la suite de tests
uv run uvicorn app.main:app --reload     # levantar el servicio en http://127.0.0.1:8000
```

Documentación interactiva de la API una vez levantado: http://127.0.0.1:8000/docs

## Roadmap

Cada paso es un ciclo TDD completo: primero el test que falla (commit `test:`), después
la implementación mínima que lo hace pasar (commit `feat:`).

| # | Paso | Issue | Estado |
|---|---|---|---|
| 0 | Estructura inicial de n-capas | #3 | Hecho |
| 1 | Configuración con Pydantic Settings | #4 | Hecho |
| 2 | Modelos de dominio y schemas Pydantic | #6 | Hecho |
| 3 | Repository abstracto + InMemoryRepository | #7 | Hecho |
| 4 | Reglas de negocio (service de consultas) | #8 | Pendiente |
| 5 | Caché cache-aside delante de la base | #8 | Pendiente |
| 6 | Endpoints HTTP, `/health` y correlation ID | #9 | Pendiente |
| 7 | Adaptadores reales: MongoDB y Redis | #7 | Pendiente |
| 8 | Dockerfile y docker-compose | #11 | Pendiente |
| 9 | Documentación de uso e integración | #12 | Pendiente |
| 10 | Verificación de calidad final | #13 | Pendiente |

Los issues #5, #10 y #14 (tests unitarios, integración HTTP y validación de arquitectura)
no son pasos aparte: se cumplen dentro de cada ciclo, porque el test siempre va primero.

## Registro

### 2026-09-29 — Bitácora creada

Se agrega este archivo para dejar asentado el avance. Motivo: una sesión de trabajo
anterior se perdió por completo y lo único que sobrevivió fue lo que estaba commiteado
en GitHub. A partir de acá, cada paso terminado se anota acá y se commitea.

### 2026-09-29 — Paso 1: configuración (issue #4)

`app/core/config.py` expone `Settings`, que lee `MONGO_URI`, `MONGO_DATABASE`,
`MONGO_COLLECTION`, `REDIS_URL` y `REDIS_TTL_SECONDS` del entorno. Ningún campo tiene
valor por defecto, así que si falta una variable la aplicación no arranca.

`tests/conftest.py` inyecta esas variables en cada test, de modo que la suite corre sin
`.env` presente y sin Mongo ni Redis levantados.

Verificar con:

```bash
uv run pytest tests/unit/test_config.py -v
```

### 2026-09-29 — Paso 2: modelo de dominio y schemas (issue #6)

`app/models/pdf_document.py` define `PdfDocument`, una dataclass inmutable con los campos
del contrato compartido. No usa Pydantic ni decoradores de persistencia: es la entidad
interna, y la capa de negocio trabaja con ella.

`app/schemas/pdf.py` define `PdfDocumentResponse` y `PdfListResponse`, que son el contrato
público de la API. `from_domain()` traduce de la entidad al schema en un solo lugar.

Verificar con:

```bash
uv run pytest tests/unit/test_schemas.py -v
```

### 2026-09-29 — Paso 3: patrón Repository (issue #7)

`app/core/repository.py` define el puerto abstracto: `Repository[T]` con las operaciones de
lectura genéricas (`get_by_id`, `listar`, `contar`) y `PdfRepository`, que agrega
`get_by_checksum`. Ninguna implementación queda con métodos vacíos.

`app/core/in_memory_repository.py` es el adaptador en memoria que usan los tests. Es el
doble de test del proyecto: no se parchean atributos privados ni se mockean internals.

Verificar con:

```bash
uv run pytest tests/unit/test_in_memory_repository.py -v
```

## Decisiones técnicas

- **Sin prefijo de API.** El contrato compartido define las rutas en `/pdf`, no bajo
  `/api/v1`. Se eliminó `API_PREFIX` de `.env.example` para no exponer una variable que
  contradice el contrato y que nadie lee.
- **Sin `LOCK_TIMEOUT_SECONDS`.** Esa variable pertenece al contrato de
  `persistencia-actualizaciones`. Este servicio es de solo lectura y no toma locks, así
  que se eliminó por YAGNI.
- **Settings sin valores por defecto.** Un default para `MONGO_URI` haría que un error de
  configuración pase desapercibido y el servicio apunte a una base equivocada en silencio.
  Es preferible que falle al arrancar.
- **`paginas` es opcional.** El contrato compartido lo muestra en el ejemplo de documento
  pero no lo lista entre los campos obligatorios, así que el modelo lo admite ausente.
- **Listados ordenados por `created_at` descendente.** Una paginación sin orden definido
  puede repetir o saltear documentos entre páginas. Ambos adaptadores respetan ese orden.
- **Dos niveles de abstracción en el repositorio.** `Repository[T]` es el puerto genérico
  que pide la metodología de la cátedra; `PdfRepository` agrega la única operación propia
  del dominio. Con una sola entidad podría haber alcanzado una interfaz plana: se mantiene
  la forma genérica porque es la prescrita, y el costo es una clase de cuatro líneas.

## Deuda técnica

_Se registra acá todo lo que se decide no hacer, con el motivo._
