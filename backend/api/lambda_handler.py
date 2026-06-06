"""Lambda handler for FastAPI application."""

from mangum import Mangum
from api.main import app

# Create the Lambda handler
# API Gateway passes the full path including the /api/ prefix
handler = Mangum(app, lifespan="off")
