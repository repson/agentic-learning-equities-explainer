FROM --platform=linux/amd64 python:3.13-slim

WORKDIR /app

# Instalar Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Playwright (dependencias de sistema para Chromium)
RUN npx -y playwright install --with-deps chromium

# Instalar el gestor de paquetes de Python
RUN pip install uv

# Copiar archivos del proyecto
COPY pyproject.toml uv.lock ./

# Instalar dependencias de Python durante el build
# uv instalará automáticamente los paquetes para la arquitectura del contenedor (linux/amd64)
RUN uv sync --frozen --no-install-project

# Copiar el código de la aplicación
COPY *.py ./

# Exponer el puerto
EXPOSE 8000

# Ejecutar la aplicación (las dependencias ya están instaladas)
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]