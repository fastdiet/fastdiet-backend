from fastapi import APIRouter


router = APIRouter(tags=["users"])

@router.get("/users")
def get_users():
    return {"message": "Hello World"}