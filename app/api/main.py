import asyncio
from datetime import datetime
import logging
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import recipes, shopping_lists, users, auth, users_preferences, meal_plans
from app.core.logging_config import setup_logging
from app.core.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.db.db_connection import init_db
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.user import delete_unverified_users



setup_logging()
logger = logging.getLogger(__name__)

init_db()

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("🔄 Scheduler started")
    
    trigger = CronTrigger(hour=0, minute=0)
    scheduler.add_job(
        delete_unverified_users,
        trigger=trigger,
        name="delete_unverified_users_job"
    )
    
    yield
    scheduler.shutdown()
    logger.info("🛑 Scheduler stopped")


app = FastAPI(lifespan=lifespan)

# Limiter Configuration
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def simulate_latency(request: Request, call_next):
    await asyncio.sleep(1)
    response = await call_next(request)
    return response

@app.middleware("http")
async def log_requests_and_errors_middleware(request: Request, call_next) -> Response | JSONResponse:
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Request finished: {request.method} {request.url.path} - Status {response.status_code}")
        return response
    except Exception as e:
        logger.error(
            f"Unhandled error during the request {request.method} {request.url.path}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"},
        )


    
### CORS configuration
origins = [
    "http://localhost:8081",
    "http://localhost:19006",  # Expo development server
    "http://localhost:13000",  # Your API server
    "exp://localhost:19000"    # Expo Go app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(users_preferences.router)
app.include_router(meal_plans.router)
app.include_router(recipes.router)
app.include_router(shopping_lists.router)

@app.get("/", summary="Endpoint to check API status")
def read_root():
    """Root endpoint to check if the API is running"""
    logger.info("Accessed root endpoint /")
    return {"status": "ok", "message": "Welcome to the FastDiet API!"}

#app.mount("/static", StaticFiles(directory="static"), name="static")