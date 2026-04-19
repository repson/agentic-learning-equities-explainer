"""Handler Lambda para la aplicación FastAPI."""

from mangum import Mangum
from api.main import app

# Crear el handler de Lambda
# API Gateway pasa la ruta completa incluyendo el prefijo /api/
handler = Mangum(app, lifespan="off")