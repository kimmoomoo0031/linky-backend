from fastapi import APIRouter

from app.api.v1.endpoints import auth, lounge, user

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/users", tags=["User"])
api_router.include_router(lounge.router, prefix="/lounges", tags=["Lounge"])
