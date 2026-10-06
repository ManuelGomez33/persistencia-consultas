# persistencia-consultas

Microservicio de **consultas** (solo lectura) de documentos PDF, dentro de la arquitectura
`microservicios-pdf`. Trabajo de Desarrollo de Software (UTN).

Consulta documentos almacenados en MongoDB y usa Redis como caché con estrategia
*cache-aside*.

## Responsabilidad

Hace:

- Listar documentos, paginado.
- Buscar un documento por ID.
- Buscar un documento por checksum.
- Servir esas consultas desde Redis cuando la información ya está cacheada.

No hace, a propósito:

- No crea, modifica ni borra documentos — eso es de `persistencia-actualizaciones`.
- No valida archivos PDF — eso es de `validacion-pdf`.
- No extrae texto ni calcula checksums — eso es de `extraccion-texto`.
- No llama a ningún otro microservicio.

## Endpoints

Contrato compartido `microservicios-pdf` v1.0.0.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/pdf` | Lista documentos. Parámetros `limit` (1–100, por defecto 20) y `offset` (≥ 0). |
| `GET` | `/pdf/{id}` | Busca un documento por ID. |
| `GET` | `/pdf/checksum/{checksum}` | Busca un documento por checksum. |
| `GET` | `/health` | Healthcheck. |

Documentación interactiva, con el servicio levantado: <http://localhost:8000/docs>

### Respuesta de un documento

```json
{
  "id": "8f6f7c3e-12d5-4f57-9c6c-123456789abc",
  "nombre": "contrato.pdf",
  "checksum": "a7f5f35426b927411fc9231b56382173",
  "texto": "Contenido extraído del PDF",
  "tamano_bytes": 245760,
  "paginas": 3,
  "created_at": "2026-09-14T18:00:00Z",
  "updated_at": "2026-09-14T18:00:00Z"
}
```

### Respuesta del listado

```json
{ "items": [], "total": 0, "limit": 20, "offset": 0 }
```

### Respuesta de error

Todos los errores usan el formato común del contrato:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "No existe un documento con id 123",
    "details": {},
    "correlation_id": "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
  }
}
```

| Código | HTTP | Cuándo |
|---|---|---|
| `VALIDATION_ERROR` | 400 | `limit` fuera de 1–100, `offset` negativo, o parámetros que no son números. |
| `RESOURCE_NOT_FOUND` | 404 | No existe un documento con ese ID o checksum, o la ruta no existe. |
| `DATABASE_ERROR` | 503 | MongoDB no responde. |
| `INTERNAL_ERROR` | 500 | Fallo inesperado. |

Si Redis no responde, **no** es un error: la consulta sigue contra MongoDB (ver *Caché
cache-aside*).

### Correlation ID

El servicio propaga la cabecera `X-Correlation-ID`. Si la petición la trae, la reutiliza y
la devuelve en la respuesta; si no, genera un UUID. El mismo identificador aparece en el
cuerpo de los errores, para poder seguir una operación entre microservicios.

### Logs

Los logs van a `stdout` (12-Factor XI), sin archivos, y **cada línea** lleva el
`correlation_id`: el middleware lo guarda en una `ContextVar` y una *record factory* lo
agrega a cada registro, así que lo tienen también los logs de los adaptadores.

```text
2026-10-06 19:55:01,905 INFO app.main correlation_id=demo-1 method=GET path=/pdf status=200 duracion_ms=3.4
2026-10-06 19:55:01,907 WARNING app.main correlation_id=demo-2 code=RESOURCE_NOT_FOUND status=404 message=No existe un documento con id nada
```

Cada request se registra con método, ruta, status y duración; cada error con su código
(`WARNING` para 4xx, `ERROR` con traza para 5xx). El access log de uvicorn está desactivado
en la imagen porque no lleva el `correlation_id`.

## Levantar con Docker (recomendado)

Levanta el servicio junto con MongoDB y Redis. Es la única forma de correrlo sin instalar
nada más que Docker.

```bash
docker compose up --build -d
```

El servicio queda en <http://localhost:8000>. Para ver los logs y para detenerlo:

```bash
docker compose logs -f persistencia-consultas
docker compose down            # conserva los datos
docker compose down -v         # borra también los volúmenes
```

## Levantar sin Docker

Requiere Python 3.12+, [uv](https://docs.astral.sh/uv/), y MongoDB y Redis accesibles.
El `docker-compose.yml` no publica los puertos de MongoDB ni Redis en el host (chocan con
los entrypoints TCP de Traefik de la infraestructura del equipo), así que para correr el
servicio fuera de Docker hace falta un MongoDB y un Redis propios.

```bash
uv sync
cp .env.example .env     # ajustar las URLs si hace falta
uv run uvicorn app.main:app --reload
```

## Variables de entorno

Todas son obligatorias: si falta alguna, el servicio no arranca. Ver `.env.example`.

| Variable | Ejemplo | Para qué |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | Conexión a MongoDB. |
| `MONGO_DATABASE` | `pdfs_db` | Base de datos a consultar. |
| `MONGO_COLLECTION` | `pdfs` | Colección de documentos. |
| `REDIS_URL` | `redis://localhost:6379/0` | Conexión a Redis. |
| `REDIS_TTL_SECONDS` | `300` | Segundos que vive cada entrada de caché. |

El archivo `.env` está en `.gitignore` y nunca se versiona. `docker-compose.yml` define
estos valores directamente, porque apuntan a los servicios de su propia red y no son
secretos.

## Cómo comprobar que funciona

Con el stack levantado (`docker compose up --build -d`):

**1. El servicio responde**

```bash
curl -i http://localhost:8000/health
```

Debe devolver `200` con `{"status":"ok"}` y una cabecera `X-Correlation-ID`.

**2. Cargar un documento de prueba**

Este servicio no crea documentos: en el sistema completo los crea
`persistencia-actualizaciones`. Para probarlo de forma aislada se inserta uno a mano:

```bash
docker compose exec mongodb mongosh pdfs_db --quiet --eval '
db.pdfs.insertOne({
  id: "8f6f7c3e-12d5-4f57-9c6c-123456789abc",
  nombre: "contrato.pdf",
  checksum: "a7f5f35426b927411fc9231b56382173",
  texto: "Contenido extraido del PDF",
  tamano_bytes: 245760,
  paginas: 3,
  created_at: new Date("2026-09-14T18:00:00Z"),
  updated_at: new Date("2026-09-14T18:00:00Z")
})'
```

**3. Las tres consultas del contrato**

```bash
curl http://localhost:8000/pdf
curl http://localhost:8000/pdf/8f6f7c3e-12d5-4f57-9c6c-123456789abc
curl http://localhost:8000/pdf/checksum/a7f5f35426b927411fc9231b56382173
```

Las tres deben devolver el documento recién insertado.

> **Insertar antes de consultar.** Si se consulta `GET /pdf` con la base vacía, la caché
> guarda ese listado vacío durante `REDIS_TTL_SECONDS` y las consultas siguientes lo van a
> seguir devolviendo, aunque después se inserte un documento. No es una falla: es el
> comportamiento esperado de una caché con TTL. En el sistema completo, quien invalida esas
> claves al escribir es `persistencia-actualizaciones`, tal como fija su contrato. Para
> forzar el refresco durante una prueba:
> `docker compose exec redis redis-cli FLUSHALL`.

**4. La caché está funcionando**

Después de las consultas anteriores, las claves deben existir en Redis:

```bash
docker compose exec redis redis-cli KEYS "pdf:*"
```

Debe listar `pdf:id:...`, `pdf:checksum:...` y `pdf:list:<hash>`. Esa es la
prueba de que la respuesta se guardó: la primera consulta fue un MISS contra MongoDB y las
siguientes se sirven desde Redis.

**5. Los errores respetan el contrato**

```bash
curl -i http://localhost:8000/pdf/no-existe          # 404 RESOURCE_NOT_FOUND
curl -i "http://localhost:8000/pdf?limit=0"          # 400 VALIDATION_ERROR
curl -i "http://localhost:8000/pdf?limit=abc"        # 400 VALIDATION_ERROR
```

## Tests

```bash
uv run pytest -v                              # toda la suite
uv run pytest --cov=app --cov-report=term-missing
```

La suite es **hermética**: corre sin `.env`, sin MongoDB y sin Redis levantados. La
configuración se inyecta desde `tests/conftest.py` y el repositorio real se sustituye por
`InMemoryPdfRepository` mediante `app.dependency_overrides`.

### Qué se testea y qué no

Se testea:

- Las reglas de negocio del service, contra el repositorio en memoria.
- El puerto `PdfRepository`, con la misma suite corriendo contra sus dos implementaciones
  hermeticas (en memoria y en memoria + caché), lo que demuestra que son intercambiables.
- El cache-aside: HIT, MISS, claves del contrato, serialización de ida y vuelta y la
  degradación cuando Redis no responde.
- La traducción de errores de los adaptadores: una colección de Motor y un cliente de
  Redis de prueba, inyectados por constructor, que fallan como sin conexión.
- Los endpoints HTTP completos, con códigos de estado, formato de errores, correlation ID
  y logs.

No se testea, a propósito: las llamadas reales a MongoDB y Redis y el cierre de las
conexiones al apagar. Ver *Deuda técnica*.

## Arquitectura

Arquitectura de n-capas con patrón Repository.

```
app/
├── main.py                      # ensamblado: routers, middleware, handlers de error
├── controllers/                 # CAPA 1 — HTTP
│   ├── pdf_controller.py
│   └── health_controller.py
├── schemas/                     # CAPA 1 — contrato público (Pydantic)
│   ├── pdf.py
│   └── error.py
├── services/                    # CAPA 2 — reglas de negocio
│   └── consulta_service.py
├── models/                      # CAPA 2 — entidad de dominio (Python puro)
│   └── pdf_document.py
└── core/                        # CAPA 3 + transversal
    ├── repository.py            # puerto abstracto
    ├── in_memory_repository.py  # adaptador en memoria (tests)
    ├── mongo_repository.py      # adaptador MongoDB
    ├── cached_repository.py     # decorador cache-aside
    ├── cache.py                 # puerto de caché
    ├── in_memory_cache.py       # adaptador en memoria (tests)
    ├── redis_cache.py           # adaptador Redis
    ├── database.py              # creación de clientes
    ├── composition.py           # inyección de dependencias y cierre de conexiones
    ├── config.py                # configuración
    ├── logs.py                  # logs a stdout con correlation_id
    └── exceptions.py            # errores de dominio
```

Flujo: `controller → service → repository → base de datos`.

- Los controllers no importan Motor, Redis ni repositorios concretos.
- El service no importa FastAPI.
- El modelo de dominio no usa Pydantic ni decoradores de persistencia.
- Los schemas son independientes de la entidad de dominio.
- Las implementaciones concretas se eligen en un único lugar: `app/core/composition.py`.

### Caché cache-aside

`CachedPdfRepository` envuelve a otro `PdfRepository`: busca en Redis, y ante un MISS
consulta MongoDB y guarda el resultado con el TTL configurado.

Claves (las del contrato): `pdf:id:{id}`, `pdf:checksum:{checksum}` y
`pdf:list:{hash}`, donde el hash es el SHA-256 de `limit={limit}&offset={offset}`.

El `total` del listado **no se cachea**: se cuenta en MongoDB en cada listado. No hay una
clave del contrato para él, así que `persistencia-actualizaciones` no la invalidaría al
escribir y el total quedaría viejo hasta que venza el TTL. Lo que sí tiene que hacer
`persistencia-actualizaciones` después de cada escritura es invalidar `pdf:id:{id}`,
`pdf:checksum:{checksum}` y todas las `pdf:list:*`.

**Si Redis no responde**, el adaptador lo informa como `CacheNoDisponible`, el decorador
registra un `WARNING` y la consulta sigue contra MongoDB: la caché acelera, pero no es un
punto único de falla.

Como decorador, la caché se puede quitar del cableado sin tocar el service ni el adaptador
de MongoDB.

## Decisiones técnicas

- **Sin prefijo de API.** El contrato define las rutas en `/pdf`; agregar `/api/v1`
  rompería la compatibilidad con el orquestador.
- **`Settings` sin valores por defecto.** Un default para `MONGO_URI` haría que un error de
  configuración pase desapercibido y el servicio apunte a otra base en silencio.
- **`limit` tope 100.** El contrato no fija un máximo. Sin tope, un cliente puede forzar al
  servicio a materializar la colección entera en una sola llamada.
- **La validación de paginación vive en el service.** Es una regla de dominio, no un
  detalle del transporte, y así queda cubierta por tests que no necesitan HTTP.
- **Los documentos inexistentes no se cachean.** Guardar un "no existe" haría invisible
  durante todo el TTL a un documento creado justo después de la consulta.
- **Listados ordenados por `created_at` descendente.** Una paginación sin orden definido
  puede repetir o saltear documentos entre páginas.
- **El mensaje de los errores 500 es genérico.** El detalle interno puede revelar la
  topología del sistema; la trazabilidad se resuelve con el `correlation_id`.
- **MongoDB caído es `DATABASE_ERROR` 503, no `INTERNAL_ERROR`.** El contrato distingue la
  dependencia caída del fallo inesperado; el adaptador traduce los errores de pymongo.

El registro completo del desarrollo, paso por paso, está en [BITACORA.md](BITACORA.md).

## Deuda técnica

- **Las llamadas reales a MongoDB y Redis no tienen tests automatizados.**
  `MongoPdfRepository` y `RedisCache` son envoltorios delgados sobre Motor y
  `redis.asyncio`. Lo que tienen de lógica propia sí está cubierto: la traducción de un
  documento de MongoDB a la entidad de dominio y la traducción de los errores de cada
  driver. Las consultas reales se cubrirían con tests de integración contra contenedores
  efímeros.
- **El cierre de conexiones al apagar no tiene test.** Se verificó a mano creando los
  clientes reales y cerrándolos; testearlo en la suite exigiría parchear la composición.
- **La caché no simula vencimiento en los tests.** `InMemoryCache` guarda sin expirar: el
  TTL es responsabilidad de Redis.
- **La colección de MongoDB no se crea con índices desde este servicio.** Las consultas por
  `id` y `checksum` conviene que estén indexadas; crear los índices corresponde a
  `persistencia-actualizaciones`, que es el dueño de la escritura.
