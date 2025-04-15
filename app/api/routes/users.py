from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.auth.auth import authenticate_user, get_current_user
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.crud.user import register_user
from app.models.user import User


router = APIRouter(tags=["users"])

# Endpoint to login a user and return a JWT token
@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    token_data = authenticate_user(db, form_data.username, form_data.password)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return token_data

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    return user

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

