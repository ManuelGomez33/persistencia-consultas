# persistencia-consultas

Microservicio de **consultas** (lectura) de documentos PDF, dentro de la arquitectura de
microservicios `microservicios-pdf`. Forma parte del TP de Desarrollo de Software (UTN).

## Responsabilidad

- Consultar documentos (listar, por ID, por checksum).
- Utilizar Redis como caché delante de MongoDB (patrón cache-aside).

**No** hace (queda fuera de este servicio):

- No modifica información (eso es responsabilidad de `persistencia-actualizaciones`).
- No valida PDFs (`validacion-pdf`).
- No extrae texto ni calcula checksum (`extraccion-texto`).

## Arquitectura

```
app/
├── main.py           # ensamblado: routers, middleware, handler de excepciones
├── controllers/       # CAPA 1 — HTTP: rutas, status codes, HTTPException
├── schemas/            # CAPA 1 — DTOs Pydantic (contrato de la API)
├── services/           # CAPA 2 — reglas de negocio
├── models/              # CAPA 2 — entidades del dominio (Python puro)
└── core/                 # CAPA 3 + transversal
    ├── repository.py        # puerto abstracto (ABC)
    ├── mongo_repository.py  # adaptador concreto (Mongo)
    ├── cache_repository.py  # adaptador concreto (Redis)
    ├── database.py          # conexión Mongo
    ├── config.py            # settings
    └── exceptions.py        # excepciones de dominio
```

Regla de dependencia: `controller → service → repository → BD`.

## Endpoints (contrato `microservicios-pdf` v1.0.0)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/pdf` | Lista documentos (paginado con `limit`/`offset`) |
| GET | `/pdf/{id}` | Busca un documento por ID |
| GET | `/pdf/checksum/{checksum}` | Busca un documento por checksum |
| GET | `/health` | Healthcheck |

## Variables de entorno

Ver [.env.example](.env.example). Copiar a `.env` para desarrollo local:

```bash
cp .env.example .env
```

## Instalación y ejecución local

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## Tests

```bash
uv run pytest -v
```

## Docker

_Pendiente (ver Fase 7 del plan de microservicios)._

## Deuda técnica

_Se documentará acá cualquier decisión de alcance no implementada, con su motivo._
