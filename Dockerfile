FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Las dependencias se instalan antes de copiar el codigo: mientras el lock no cambie,
# esta capa se reutiliza entre builds.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY logging.json ./
COPY app ./app

RUN useradd --create-home appuser && chown --recursive appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# --no-access-log: el acceso lo registra la app con el correlation_id.
# Forma exec: uvicorn es el PID 1 y recibe el SIGTERM de docker stop. Con
# --timeout-graceful-shutdown deja de aceptar conexiones y espera hasta 30 s a que
# terminen las consultas en curso antes de salir (contrato 1.2.0, 12-Factor IX).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--timeout-graceful-shutdown", "30"]
