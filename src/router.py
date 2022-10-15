from fastapi import APIRouter
from .controllers import auth

root_api_router = APIRouter(prefix="/api/v1")

root_api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
