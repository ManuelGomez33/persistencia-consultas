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
| 4 | Reglas de negocio (service de consultas) | #8 | Hecho |
| 5 | Caché cache-aside delante de la base | #8 | Hecho |
| 6 | Adaptadores reales: MongoDB y Redis | #7 | Hecho |
| 7 | Endpoints HTTP, `/health` y correlation ID | #9 | Hecho |
| 8 | Dockerfile y docker-compose | #11 | Hecho |
| 9 | Documentación de uso e integración | #12 | Hecho |
| 10 | Verificación de calidad final | #13 | Hecho |

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

### 2026-09-29 — Paso 4: reglas de negocio (issue #8)

`app/services/consulta_service.py` implementa `ConsultaPdfService`, que recibe un
`PdfRepository` por constructor. No importa FastAPI: recibe y devuelve tipos del dominio,
así que se puede testear sin levantar un servidor HTTP.

`app/core/exceptions.py` define los errores de dominio con el `code` y el `status_code`
del contrato común: `RESOURCE_NOT_FOUND` (404) y `VALIDATION_ERROR` (400).

Verificar con:

```bash
uv run pytest tests/unit/test_consulta_service.py -v
```

### 2026-09-29 — Paso 5: caché cache-aside (issue #8)

`app/core/cached_repository.py` implementa `CachedPdfRepository`, que envuelve a otro
`PdfRepository`. Ante una consulta busca primero en la caché; si no está (MISS) delega en
el repositorio envuelto y guarda el resultado con el TTL configurado.

Claves usadas: `pdf:id:{id}`, `pdf:checksum:{checksum}`, `pdf:list:{limit}:{offset}` y
`pdf:total`.

`app/core/cache.py` define el puerto y `app/core/in_memory_cache.py` la implementación que
usan los tests.

La suite del repositorio (`tests/unit/test_pdf_repository.py`) corre parametrizada contra
las dos implementaciones, lo que demuestra que son intercambiables.

Verificar con:

```bash
uv run pytest tests/unit/test_cached_repository.py tests/unit/test_pdf_repository.py -v
```

### 2026-09-29 — Paso 6: adaptadores de MongoDB y Redis (issue #7)

Se adelantó este paso, que en el plan original iba después de los endpoints, para que al
armar `main.py` el cableado sea el real y no haya que pasar por una implementación
provisoria.

- `app/core/database.py` — creación de los clientes de Mongo y Redis a partir de `Settings`.
- `app/core/mongo_repository.py` — `MongoPdfRepository`, más `documento_desde_mongo()`,
  que traduce el documento de la base a la entidad de dominio.
- `app/core/redis_cache.py` — `RedisCache`, que implementa el puerto `Cache`.

Verificar con:

```bash
uv run pytest tests/unit/test_mongo_repository.py -v
```

### 2026-09-29 — Paso 7: endpoints HTTP (issue #9)

La aplicación ya arranca y responde. Componentes:

- `app/controllers/pdf_controller.py` — `GET /pdf`, `GET /pdf/{id}`,
  `GET /pdf/checksum/{checksum}`.
- `app/controllers/health_controller.py` — `GET /health`.
- `app/schemas/error.py` — el formato de error compartido.
- `app/core/composition.py` — el único lugar donde se eligen las implementaciones
  concretas (Mongo, Redis). Es lo que los tests reemplazan con `dependency_overrides`.
- `app/main.py` — ensamblado, middleware de `X-Correlation-ID` y handlers de excepciones.

Comprobado a mano contra el servicio levantado: `/health` responde
`{"status":"ok"}` con la cabecera `X-Correlation-ID`, y `/pdf` sin las bases levantadas
devuelve `INTERNAL_ERROR` con el formato del contrato en lugar de un error del framework.

Verificar con:

```bash
uv run pytest tests/integration -v
```

### 2026-09-29 — Pasos 8 y 9: Docker y documentación (issues #11 y #12)

`Dockerfile` (usuario sin privilegios, healthcheck, dependencias con uv) y
`docker-compose.yml` con MongoDB y Redis, ambos con volumen nombrado y healthcheck.

**Verificado de punta a punta contra el stack real**, no solo con tests:

- Los tres contenedores levantan y quedan `healthy`.
- `GET /health` → `{"status":"ok"}` con cabecera `X-Correlation-ID`.
- Insertado un documento en MongoDB, los tres endpoints de consulta lo devuelven con las
  fechas en el formato del contrato (`2026-09-14T18:00:00Z`).
- Redis queda con las cuatro claves: `pdf:id:...`, `pdf:checksum:...`, `pdf:list:20:0`,
  `pdf:total`. Esa es la evidencia del cache-aside.
- `GET /pdf/no-existe` → 404 `RESOURCE_NOT_FOUND`; `GET /pdf?limit=0` → 400
  `VALIDATION_ERROR` con `details`.

Durante esta verificación apareció un comportamiento que conviene tener presente:
consultar `GET /pdf` con la base vacía deja el listado vacío cacheado durante todo el TTL,
así que un documento insertado después no aparece hasta que la entrada vence. Es el
comportamiento esperado de una caché con TTL —quien invalida al escribir es
`persistencia-actualizaciones`, según su propio contrato— pero desorienta al probar este
servicio aislado, así que quedó advertido en el README.

El README quedó con: instalación, ejecución local y con Docker, variables, endpoints,
errores, pasos de verificación, decisiones técnicas y deuda técnica.

### 2026-09-29 — Paso 10: verificación de calidad (issues #13 y #14)

Resultados de la verificación completa:

| Chequeo | Comando | Resultado |
|---|---|---|
| Suite de tests | `uv run pytest -v` | 60 en verde |
| Hermeticidad | `mv .env .env.bak && uv run pytest` | 60 en verde sin `.env` |
| Linter | `uv run ruff check app/ tests/` | sin advertencias |
| Formato | `uv run black --check app/ tests/` | 35 archivos sin cambios |
| Cobertura | `uv run pytest --cov=app` | 94 % |
| Secretos versionados | `git ls-files \| grep -E "\.(env\|pyc)$"` | vacío |

Revisión manual:

- **Imports entre capas:** `services/` no importa `fastapi`; `controllers/` no importa
  Motor, pymongo ni redis; `models/` no importa Pydantic.
- **Lógica duplicada:** las dos búsquedas del service comparten `_asegurar_encontrado`,
  las del repositorio con caché comparten `_documento_cacheado` y las de Mongo comparten
  `_buscar_uno`.
- **Símbolos sin uso:** ninguno. Los cinco que no tienen llamador directo
  (`buscar_por_id`, `buscar_por_checksum`, los dos handlers de excepciones y el middleware
  de correlation ID) los invoca FastAPI a través de sus decoradores.
- **Cobertura:** el 6 % sin cubrir corresponde exactamente al seam declarado — las
  llamadas directas a Motor y Redis y el cableado de producción. No hay reglas de negocio
  sin test.

Sobre el issue #14 (validar integración con la arquitectura completa): este servicio **no
hace llamadas salientes a otros microservicios**, así que los puntos de timeouts, retry y
compensación SAGA no le aplican —corresponden al `orquestador`—. Lo que sí le aplica está
verificado: compatibilidad con el contrato compartido, Redis HIT y MISS, y MongoDB, todo
comprobado contra el stack real levantado con Docker (ver paso 8).

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
- **El mensaje de los errores 500 es genérico.** El detalle del fallo interno puede
  revelar la topología del sistema (URIs, nombres de host). La trazabilidad se resuelve con
  el `correlation_id`, que sí viaja al cliente y permite ubicar el caso en los logs.
- **La caché es un decorador del repositorio, no lógica del service.** Poner el
  cache-aside dentro de `ConsultaPdfService` habría mezclado una optimización de
  infraestructura con las reglas de negocio; ponerlo dentro del adaptador de Mongo habría
  atado la caché a esa base en particular. Como decorador, se puede quitar del cableado y
  el servicio sigue funcionando.
- **Los documentos inexistentes no se cachean.** Guardar un "no existe" haría invisible
  durante todo el TTL a un documento creado por `persistencia-actualizaciones` justo
  después de la consulta.
- **Claves de listado por `limit` y `offset` explícitos.** El contrato sugiere
  `pdf:list:{hash-de-parametros}`; con solo dos parámetros, escribirlos en la clave es
  equivalente y deja la caché legible al inspeccionar Redis.
- **`limit` tope 100.** El contrato no fija un máximo. Sin tope, un cliente puede pedir el
  listado completo en una sola llamada y forzar al servicio a materializar toda la
  colección. Se rechaza con `VALIDATION_ERROR` en lugar de recortar en silencio, para que
  el cliente sepa que su pedido no se respetó tal cual.
- **La validación de paginación vive en el service, no en el controller.** Es una regla de
  dominio y así queda cubierta por tests que no necesitan HTTP. El controller solo
  transporta los valores.
- **Sin `BaseService` intermedio.** La metodología lo muestra como ejemplo, pero con un
  solo service una clase base sería una capa vacía. Lo que sí se respeta es lo que esa
  clase base ilustra: el repositorio entra por constructor, tipado contra la abstracción
  y sin valor por defecto.
- **Dos niveles de abstracción en el repositorio.** `Repository[T]` es el puerto genérico
  que pide la metodología de la cátedra; `PdfRepository` agrega la única operación propia
  del dominio. Con una sola entidad podría haber alcanzado una interfaz plana: se mantiene
  la forma genérica porque es la prescrita, y el costo es una clase de cuatro líneas.

## Deuda técnica

- **Los adaptadores de MongoDB y Redis no tienen tests automatizados.** `MongoPdfRepository`
  y `RedisCache` son envoltorios delgados sobre Motor y `redis.asyncio`: cada método es una
  llamada directa al driver. Testearlos exigiría levantar contenedores reales, lo que
  rompería la regla de que la suite corra sin red ni bases de datos. Lo único con lógica
  propia —la traducción del documento de Mongo a la entidad de dominio— sí está cubierto
  en `tests/unit/test_mongo_repository.py`. Se cubrirían con un test de integración contra
  un contenedor efímero.
- **La caché no simula vencimiento en los tests.** `InMemoryCache` guarda sin expirar: el
  TTL es responsabilidad de Redis y no hay reglas propias que verificar.
