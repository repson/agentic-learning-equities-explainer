"""
Backend FastAPI para Alex Financial Advisor
Gestiona todas las rutas de API con autenticación Clerk JWT
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
import boto3
from mangum import Mangum
from dotenv import load_dotenv
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials

from src import Database
from src.schemas import (
    UserCreate,
    AccountCreate,
    PositionCreate,
    JobCreate, JobUpdate,
    JobType, JobStatus
)

# Cargar variables de entorno
load_dotenv(override=True)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StructuredLogger:
    @staticmethod
    def log_event(event_type, user_id=None, details=None):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        logger.info(json.dumps(log_entry))

# Inicializar aplicación FastAPI
app = FastAPI(
    title="Alex Financial Advisor API",
    description="API backend para planificación financiera potenciada por IA",
    version="1.0.0"
)

# Configuración CORS
# Obtener orígenes de la variable de entorno CORS_ORIGINS (separados por coma) o usar localhost por defecto
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Controladores de excepción personalizados para mejores mensajes de error
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Gestiona errores de validación de Pydantic con mensajes amigables"""
    return JSONResponse(
        status_code=422,
        content={"detail": "Datos de entrada no válidos. Por favor revisa tu solicitud e inténtalo de nuevo."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Gestiona excepciones HTTP con mensajes mejorados"""
    # Mapea errores técnicos a mensajes amigables
    user_friendly_messages = {
        401: "Tu sesión ha expirado. Por favor inicia sesión de nuevo.",
        403: "No tienes permiso para acceder a este recurso.",
        404: "El recurso solicitado no ha sido encontrado.",
        429: "Demasiadas solicitudes. Por favor espera e inténtalo más tarde.",
        500: "Ha ocurrido un error interno. Inténtalo de nuevo más tarde.",
        503: "El servicio está temporalmente no disponible. Inténtalo de nuevo más tarde."
    }

    message = user_friendly_messages.get(exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": message}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Gestiona errores inesperados de manera amable"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ha ocurrido un error inesperado. Nuestro equipo ha sido notificado."}
    )

# Inicializar servicios
db = Database()

# Cliente SQS para la cola de trabajos
sqs_client = boto3.client('sqs', region_name=os.getenv('DEFAULT_AWS_REGION', 'us-east-1'))
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', '')

# Configuración de autenticación de Clerk (igual que referencia saas)
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

async def get_current_user_id(creds: HTTPAuthorizationCredentials = Depends(clerk_guard)) -> str:
    """Extraer el ID de usuario desde el token Clerk validado"""
    # La dependencia clerk_guard ya validó el token
    # creds.decoded contiene el payload JWT
    user_id = creds.decoded["sub"]
    logger.info(f"Usuario autenticado: {user_id}")
    return user_id

# Modelos de solicitud/respuesta
class UserResponse(BaseModel):
    user: Dict[str, Any]
    created: bool

class UserUpdate(BaseModel):
    """Actualizar configuración del usuario"""
    display_name: Optional[str] = None
    years_until_retirement: Optional[int] = None
    target_retirement_income: Optional[float] = None
    asset_class_targets: Optional[Dict[str, float]] = None
    region_targets: Optional[Dict[str, float]] = None

class AccountUpdate(BaseModel):
    """Actualizar cuenta"""
    account_name: Optional[str] = None
    account_purpose: Optional[str] = None
    cash_balance: Optional[float] = None

class PositionUpdate(BaseModel):
    """Actualizar posición"""
    quantity: Optional[float] = None

class AnalyzeRequest(BaseModel):
    analysis_type: str = Field(default="portfolio", description="Tipo de análisis a realizar")
    options: Dict[str, Any] = Field(default_factory=dict, description="Opciones del análisis")

class AnalyzeResponse(BaseModel):
    job_id: str
    message: str

# Rutas de la API

@app.get("/health")
async def health_check():
    """Endpoint de prueba de salud"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/user", response_model=UserResponse)
async def get_or_create_user(
    clerk_user_id: str = Depends(get_current_user_id),
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard)
):
    """Obtiene el usuario o lo crea si es la primera vez"""

    try:
        # Verifica si el usuario existe
        user = db.users.find_by_clerk_id(clerk_user_id)

        if user:
            return UserResponse(user=user, created=False)

        # Crear nuevo usuario con valores por defecto tomados del token JWT
        token_data = creds.decoded
        display_name = token_data.get('name') or token_data.get('email', '').split('@')[0] or "Nuevo Usuario"

        # Crear usuario con TODOS los valores por defecto en una sola operación
        user_data = {
            'clerk_user_id': clerk_user_id,
            'display_name': display_name,
            'years_until_retirement': 20,
            'target_retirement_income': 60000,
            'asset_class_targets': {"equity": 70, "fixed_income": 30},
            'region_targets': {"north_america": 50, "international": 50}
        }

        # Insertar directamente con todos los datos
        created_clerk_id = db.users.db.insert('users', user_data, returning='clerk_user_id')

        # Obtener el usuario creado
        created_user = db.users.find_by_clerk_id(clerk_user_id)
        logger.info(f"Nuevo usuario creado: {clerk_user_id}")

        return UserResponse(user=created_user, created=True)

    except Exception as e:
        logger.error(f"Error en get_or_create_user: {e}")
        raise HTTPException(status_code=500, detail="No se pudo cargar el perfil de usuario")

@app.put("/api/user")
async def update_user(user_update: UserUpdate, clerk_user_id: str = Depends(get_current_user_id)):
    """Actualizar configuración del usuario"""

    try:
        # Obtener usuario
        user = db.users.find_by_clerk_id(clerk_user_id)

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Actualizar usuario - la tabla users usa clerk_user_id como clave primaria
        update_data = user_update.model_dump(exclude_unset=True)

        # Usa el cliente de base de datos directamente ya que users usa clerk_user_id como PK
        db.users.db.update(
            'users',
            update_data,
            "clerk_user_id = :clerk_user_id",
            {'clerk_user_id': clerk_user_id}
        )

        # Retornar usuario actualizado
        updated_user = db.users.find_by_clerk_id(clerk_user_id)
        return updated_user

    except Exception as e:
        logger.error(f"Error actualizando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accounts")
async def list_accounts(clerk_user_id: str = Depends(get_current_user_id)):
    """Listar cuentas del usuario"""

    try:
        # Obtener cuentas para el usuario
        accounts = db.accounts.find_by_user(clerk_user_id)
        return accounts

    except Exception as e:
        logger.error(f"Error listando cuentas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts")
async def create_account(account: AccountCreate, clerk_user_id: str = Depends(get_current_user_id)):
    """Crear nueva cuenta"""

    try:
        # Verifica que el usuario exista
        user = db.users.find_by_clerk_id(clerk_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Crear cuenta
        account_id = db.accounts.create_account(
            clerk_user_id=clerk_user_id,
            account_name=account.account_name,
            account_purpose=account.account_purpose,
            cash_balance=getattr(account, 'cash_balance', Decimal('0'))
        )

        # Retornar cuenta creada
        created_account = db.accounts.find_by_id(account_id)
        return created_account

    except Exception as e:
        logger.error(f"Error creando cuenta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/accounts/{account_id}")
async def update_account(account_id: str, account_update: AccountUpdate, clerk_user_id: str = Depends(get_current_user_id)):
    """Actualizar cuenta"""

    try:
        # Verificar que la cuenta pertenezca al usuario
        account = db.accounts.find_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        # Verificar propiedad - la tabla accounts almacena clerk_user_id directamente
        if account.get('clerk_user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="No autorizado")

        # Actualizar cuenta
        update_data = account_update.model_dump(exclude_unset=True)
        db.accounts.update(account_id, update_data)

        # Retornar cuenta actualizada
        updated_account = db.accounts.find_by_id(account_id)
        return updated_account

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando cuenta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str, clerk_user_id: str = Depends(get_current_user_id)):
    """Eliminar una cuenta y todas sus posiciones"""

    try:
        # Verificar que la cuenta pertenezca al usuario
        account = db.accounts.find_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        # Verificar propiedad - la tabla accounts almacena clerk_user_id directamente
        if account.get('clerk_user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="No autorizado")

        # Eliminar todas las posiciones primero (por restricción de clave foránea)
        positions = db.positions.find_by_account(account_id)
        for position in positions:
            db.positions.delete(position['id'])

        # Eliminar la cuenta
        db.accounts.delete(account_id)

        return {"message": "Cuenta eliminada exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando cuenta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accounts/{account_id}/positions")
async def list_positions(account_id: str, clerk_user_id: str = Depends(get_current_user_id)):
    """Obtener posiciones de una cuenta"""

    try:
        # Verificar que la cuenta pertenezca al usuario
        account = db.accounts.find_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        # Verificar propiedad - la tabla accounts almacena clerk_user_id directamente
        if account.get('clerk_user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="No autorizado")

        positions = db.positions.find_by_account(account_id)

        # Formatear posiciones con datos de instrumentos para el frontend
        formatted_positions = []
        for pos in positions:
            # Obtener datos completos del instrumento
            instrument = db.instruments.find_by_symbol(pos['symbol'])
            formatted_positions.append({
                **pos,
                'instrument': instrument
            })

        return {"positions": formatted_positions}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando posiciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/positions")
async def create_position(position: PositionCreate, clerk_user_id: str = Depends(get_current_user_id)):
    """Crear posición"""

    try:
        # Verificar que la cuenta pertenezca al usuario
        account = db.accounts.find_by_id(position.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        # Verificar propiedad - la tabla accounts almacena clerk_user_id directamente
        if account.get('clerk_user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="No autorizado")

        # Verifica si el instrumento existe, si no lo crea
        instrument = db.instruments.find_by_symbol(position.symbol.upper())
        if not instrument:
            logger.info(f"Creando nuevo instrumento: {position.symbol.upper()}")
            # Crear entrada básica de instrumento con asignaciones por defecto
            # Importar el esquema desde la base de datos
            from src.schemas import InstrumentCreate

            # Determinar tipo basándose en patrones comunes
            symbol_upper = position.symbol.upper()
            if len(symbol_upper) <= 5 and symbol_upper.isalpha():
                instrument_type = "stock"
            else:
                instrument_type = "etf"

            # Crear instrumento con asignaciones básicas por defecto
            # Estas pueden actualizarse luego por el agente tagger
            new_instrument = InstrumentCreate(
                symbol=symbol_upper,
                name=f"{symbol_upper} - Agregado por el Usuario",  # Nombre básico, actualizable después
                instrument_type=instrument_type,
                current_price=Decimal("0.00"),  # El precio se actualizará por procesos background
                allocation_regions={"north_america": 100.0},  # Por defecto 100% NA
                allocation_sectors={"other": 100.0},  # Por defecto 100% otro
                allocation_asset_class={"equity": 100.0} if instrument_type == "stock" else {"fixed_income": 100.0}
            )

            db.instruments.create_instrument(new_instrument)

        # Agregar posición
        position_id = db.positions.add_position(
            account_id=position.account_id,
            symbol=position.symbol.upper(),
            quantity=position.quantity
        )

        # Retornar posición creada
        created_position = db.positions.find_by_id(position_id)
        return created_position

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando posición: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/positions/{position_id}")
async def update_position(position_id: str, position_update: PositionUpdate, clerk_user_id: str = Depends(get_current_user_id)):
    """Actualizar posición"""

    try:
        # Obtener posición y verificar propiedad
        position = db.positions.find_by_id(position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Posición no encontrada")

        account = db.accounts.find_by_id(position['account_id'])
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        # Verificar propiedad - la tabla accounts almacena clerk_user_id directamente
        if account.get('clerk_user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="No autorizado")

        # Actualizar posición
        update_data = position_update.model_dump(exclude_unset=True)
        db.positions.update(position_id, update_data)

        # Retornar posición actualizada
        updated_position = db.positions.find_by_id(position_id)
        return updated_position

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando posición: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/positions/{position_id}")
async def delete_position(position_id: str, clerk_user_id: str = Depends(get_current_user_id)):
    """Eliminar posición"""

    try:
        # Obtener posición y verificar propiedad
        position = db.positions.find_by_id(position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Posición no encontrada")

        account = db.accounts.find_by_id(position['account_id'])
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        # Verificar propiedad - la tabla accounts almacena clerk_user_id directamente
        if account.get('clerk_user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="No autorizado")

        db.positions.delete(position_id)
        return {"message": "Posición eliminada"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando posición: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/instruments")
async def list_instruments(clerk_user_id: str = Depends(get_current_user_id)):
    """Obtener todos los instrumentos disponibles para autocompletar"""

    try:
        instruments = db.instruments.find_all()
        # Retornar lista simplificada para autocompletar
        return [
            {
                "symbol": inst["symbol"],
                "name": inst["name"],
                "instrument_type": inst["instrument_type"],
                "current_price": float(inst["current_price"]) if inst.get("current_price") else None
            }
            for inst in instruments
        ]
    except Exception as e:
        logger.error(f"Error obteniendo instrumentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def trigger_analysis(request: AnalyzeRequest, clerk_user_id: str = Depends(get_current_user_id)):
    """Lanzar análisis de portafolio"""

    try:
        # Obtener usuario
        user = db.users.find_by_clerk_id(clerk_user_id)

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        accounts = db.accounts.find_by_user(clerk_user_id)
        StructuredLogger.log_event(
            "ANALYSIS_TRIGGERED",
            user_id=clerk_user_id,
            details={
                "analysis_type": request.analysis_type,
                "options": request.options,
                "account_count": len(accounts),
            },
        )

        # Crear trabajo
        job_id = db.jobs.create_job(
            clerk_user_id=clerk_user_id,
            job_type="portfolio_analysis",
            request_payload=request.model_dump()
        )

        # Obtener trabajo creado
        job = db.jobs.find_by_id(job_id)

        # Enviar a SQS
        if SQS_QUEUE_URL:
            message = {
                'job_id': str(job_id),
                'clerk_user_id': clerk_user_id,
                'analysis_type': request.analysis_type,
                'options': request.options
            }

            sqs_client.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(message)
            )
            StructuredLogger.log_event(
                "ANALYSIS_ENQUEUED",
                user_id=clerk_user_id,
                details={"job_id": str(job_id), "queue_configured": True},
            )
            logger.info(f"Enviado trabajo de análisis a SQS: {job_id}")
        else:
            StructuredLogger.log_event(
                "ANALYSIS_NOT_ENQUEUED",
                user_id=clerk_user_id,
                details={"job_id": str(job_id), "queue_configured": False},
            )
            logger.warning("SQS_QUEUE_URL no está configurada, el trabajo se ha creado pero no ha sido encolado")

        return AnalyzeResponse(
            job_id=str(job_id),
            message="Análisis iniciado. Consulta el estado del trabajo para ver los resultados."
        )

    except Exception as e:
        logger.error(f"Error lanzando análisis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str, clerk_user_id: str = Depends(get_current_user_id)):
    """Obtener estado y resultados del trabajo"""

    try:
        # Obtener trabajo
        job = db.jobs.find_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")

        # Verificar que el trabajo pertenezca al usuario - jobs almacena clerk_user_id directamente
        if job.get('clerk_user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="No autorizado")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado del trabajo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
async def list_jobs(clerk_user_id: str = Depends(get_current_user_id)):
    """Listar trabajos de análisis del usuario"""

    try:
        # Obtener trabajos para este usuario (con límite mayor para no perder recientes)
        user_jobs = db.jobs.find_by_user(clerk_user_id, limit=100)
        # Ordenar por created_at descendente (más reciente primero)
        user_jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return {"jobs": user_jobs}

    except Exception as e:
        logger.error(f"Error listando trabajos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reset-accounts")
async def reset_accounts(clerk_user_id: str = Depends(get_current_user_id)):
    """Eliminar todas las cuentas del usuario actual"""

    try:
        # Obtener usuario
        user = db.users.find_by_clerk_id(clerk_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Obtener todas las cuentas del usuario
        accounts = db.accounts.find_by_user(clerk_user_id)

        # Eliminar cada cuenta (las posiciones se eliminan en cascada)
        deleted_count = 0
        for account in accounts:
            try:
                # Las posiciones se eliminan automáticamente por CASCADE
                db.accounts.delete(account['id'])
                deleted_count += 1
            except Exception as e:
                logger.warning(f"No se pudo eliminar la cuenta {account['id']}: {e}")

        return {
            "message": f"Eliminadas {deleted_count} cuenta(s)",
            "accounts_deleted": deleted_count
        }

    except Exception as e:
        logger.error(f"Error reseteando cuentas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/populate-test-data")
async def populate_test_data(clerk_user_id: str = Depends(get_current_user_id)):
    """Poblar datos de prueba para el usuario actual"""

    try:
        # Obtener usuario
        user = db.users.find_by_clerk_id(clerk_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Definir instrumentos faltantes que puede que no estén en la base de datos
        missing_instruments = {
            "AAPL": {
                "name": "Apple Inc.",
                "type": "stock",
                "current_price": 195.89,
                "allocation_regions": {"north_america": 100},
                "allocation_sectors": {"technology": 100},
                "allocation_asset_class": {"equity": 100}
            },
            "AMZN": {
                "name": "Amazon.com Inc.",
                "type": "stock",
                "current_price": 178.35,
                "allocation_regions": {"north_america": 100},
                "allocation_sectors": {"consumer_discretionary": 100},
                "allocation_asset_class": {"equity": 100}
            },
            "NVDA": {
                "name": "NVIDIA Corporation",
                "type": "stock",
                "current_price": 522.74,
                "allocation_regions": {"north_america": 100},
                "allocation_sectors": {"technology": 100},
                "allocation_asset_class": {"equity": 100}
            },
            "MSFT": {
                "name": "Microsoft Corporation",
                "type": "stock",
                "current_price": 430.82,
                "allocation_regions": {"north_america": 100},
                "allocation_sectors": {"technology": 100},
                "allocation_asset_class": {"equity": 100}
            },
            "GOOGL": {
                "name": "Alphabet Inc. Class A",
                "type": "stock",
                "current_price": 173.69,
                "allocation_regions": {"north_america": 100},
                "allocation_sectors": {"technology": 100},
                "allocation_asset_class": {"equity": 100}
            },
        }

        # Verificar y agregar instrumentos faltantes
        for symbol, info in missing_instruments.items():
            existing = db.instruments.find_by_symbol(symbol)
            if not existing:
                try:
                    from src.schemas import InstrumentCreate

                    instrument_data = InstrumentCreate(
                        symbol=symbol,
                        name=info["name"],
                        instrument_type=info["type"],
                        current_price=Decimal(str(info["current_price"])),
                        allocation_regions=info["allocation_regions"],
                        allocation_sectors=info["allocation_sectors"],
                        allocation_asset_class=info["allocation_asset_class"]
                    )
                    db.instruments.create_instrument(instrument_data)
                    logger.info(f"Instrumento faltante añadido: {symbol}")
                except Exception as e:
                    logger.warning(f"No se pudo agregar instrumento {symbol}: {e}")

        # Crear cuentas con datos de prueba
        accounts_data = [
            {
                "name": "401k Long-term",
                "purpose": "Cuenta primaria de ahorro para retiro con aportes del empleador",
                "cash": 5000.00,
                "positions": [
                    ("SPY", 150),   # ETF S&P 500
                    ("VTI", 100),   # ETF Total Stock Market
                    ("BND", 200),   # ETF Bonos
                    ("QQQ", 75),    # ETF Nasdaq
                    ("IWM", 50),    # ETF Small Cap
                ]
            },
            {
                "name": "Roth IRA",
                "purpose": "Cuenta de crecimiento para retiro libre de impuestos",
                "cash": 2500.00,
                "positions": [
                    ("VTI", 80),    # ETF Total Stock Market
                    ("VXUS", 60),   # ETF Internacional
                    ("VNQ", 40),    # ETF Real Estate
                    ("GLD", 25),    # ETF Oro
                    ("TLT", 30),    # ETF Bonos Tesoro Largo Plazo
                    ("VIG", 45),    # ETF Dividendos Crecientes
                ]
            },
            {
                "name": "Brokerage Account",
                "purpose": "Cuenta de inversión gravable para acciones individuales",
                "cash": 10000.00,
                "positions": [
                    ("TSLA", 15),   # Tesla
                    ("AAPL", 50),   # Apple
                    ("AMZN", 10),   # Amazon
                    ("NVDA", 25),   # Nvidia
                    ("MSFT", 30),   # Microsoft
                    ("GOOGL", 20),  # Google
                ]
            }
        ]

        created_accounts = []
        for account_data in accounts_data:
            # Crear cuenta
            account_id = db.accounts.create_account(
                clerk_user_id=clerk_user_id,
                account_name=account_data["name"],
                account_purpose=account_data["purpose"],
                cash_balance=Decimal(str(account_data["cash"]))
            )

            # Agregar posiciones
            for symbol, quantity in account_data["positions"]:
                try:
                    db.positions.add_position(
                        account_id=account_id,
                        symbol=symbol,
                        quantity=Decimal(str(quantity))
                    )
                except Exception as e:
                    logger.warning(f"No se pudo agregar posición {symbol}: {e}")

            created_accounts.append(account_id)

        # Obtener todas las cuentas con sus posiciones para resumen
        all_accounts = []
        for account_id in created_accounts:
            account = db.accounts.find_by_id(account_id)
            positions = db.positions.find_by_account(account_id)
            account['positions'] = positions
            all_accounts.append(account)

        return {
            "message": "Datos de prueba poblados correctamente",
            "accounts_created": len(created_accounts),
            "accounts": all_accounts
        }

    except Exception as e:
        logger.error(f"Error poblando datos de prueba: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Handler para Lambda
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
