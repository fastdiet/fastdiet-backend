import logging
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import feedback, recipes, shopping_lists, tasks, users, auth, users_preferences, meal_plans, waitlist
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.db.db_connection import init_db



setup_logging()
logger = logging.getLogger(__name__)

init_db()

app = FastAPI()

# Limiter Configuration
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# @app.middleware("http")
# async def simulate_latency(request: Request, call_next):
#     await asyncio.sleep(1)
#     response = await call_next(request)
#     return response

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
settings = get_settings()
origins = [origin.strip() for origin in settings.cors_origins.split(",")]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(tasks.router)
app.include_router(waitlist.router)
app.include_router(feedback.router)

@app.get("/", summary="Endpoint to check API status")
def read_root():
    """Root endpoint to check if the API is running"""
    logger.info("Accessed root endpoint /")
    return {"status": "ok", "message": "Welcome to the FastDiet API!"}

#app.mount("/static", StaticFiles(directory="static"), name="static")