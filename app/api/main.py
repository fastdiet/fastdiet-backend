from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api. routes import users


app = FastAPI()


@app.middleware("http")
async def http_error_handler(request: Request, call_next) -> Response | JSONResponse:
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        content = f"error: {str(e)}"
        status_code = 500
        response = JSONResponse(
            content=content,
            status_code=status_code,
        )
        return response
    
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



#app.mount("/static", StaticFiles(directory="static"), name="static")