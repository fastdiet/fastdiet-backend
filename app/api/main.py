from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api. routes import users

app = FastAPI()

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