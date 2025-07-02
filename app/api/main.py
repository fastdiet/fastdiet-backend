from datetime import datetime
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import recipes, users, auth, users_preferences, meal_plans
from app.core.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.db.db_connection import init_db
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.user import delete_unverified_users


init_db()

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    print("🔄 Scheduler started")
    
    trigger = CronTrigger(hour=0, minute=0)
    scheduler.add_job(
        delete_unverified_users,
        trigger=trigger,
        name="delete_unverified_users_job"
    )
    
    yield
    scheduler.shutdown()
    print("🛑 Scheduler stopped")


app = FastAPI(lifespan=lifespan)

# Limiter Configuration
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def http_error_handler(request: Request, call_next) -> Response | JSONResponse:
    try:
        response = await call_next(request)
        return response
    except Exception as e:
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



#app.mount("/static", StaticFiles(directory="static"), name="static")