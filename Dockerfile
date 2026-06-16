# ==========================================
# ETAPA 1: Builder (Usando uv puro sobre Debian)
# ==========================================
FROM ghcr.io/astral-sh/uv:trixie-slim AS builder

# Optimizaciones de uv para entornos Docker
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

# Forzar a uv a guardar Python en una ruta fija y usar SOLO su versión gestionada
ENV UV_PYTHON_INSTALL_DIR=/python \
    UV_PYTHON_PREFERENCE=only-managed

# 1. uv descarga e instala Python de manera independiente
RUN uv python install 3.12

WORKDIR /app

# 2. Capa intermedia: Instalar dependencias del proyecto (Cacheable)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# 3. Copiar el código fuente y sincronizar el proyecto completo
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# ==========================================
# ETAPA 2: Runtime de Producción (Imagen Limpia)
# ==========================================
FROM debian:trixie-slim

# Buenas prácticas de seguridad: Crear un usuario sin privilegios root
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Instalar certificados SSL necesarios en el SO final para llamadas HTTPS salientes
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar el Python descargado por uv desde el builder
COPY --from=builder /python /python

# Copiar la aplicación y el .venv asignándole los permisos al usuario nonroot
COPY --from=builder --chown=nonroot:nonroot /app /app

# Inyectar el entorno virtual al PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Evitar que Python guarde en buffer los logs (vital para ver logs en tiempo real en tu self-host)
ENV PYTHONUNBUFFERED=1

# Cambiar al usuario seguro
USER nonroot

EXPOSE 8000

# Ejecutar FastAPI mediante el CLI oficial en producción
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]