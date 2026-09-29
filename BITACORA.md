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
| 1 | Configuración con Pydantic Settings | #4 | Pendiente |
| 2 | Modelos de dominio y schemas Pydantic | #6 | Pendiente |
| 3 | Repository abstracto + InMemoryRepository | #7 | Pendiente |
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

## Decisiones técnicas

_Se van registrando acá a medida que se toman._

## Deuda técnica

_Se registra acá todo lo que se decide no hacer, con el motivo._
