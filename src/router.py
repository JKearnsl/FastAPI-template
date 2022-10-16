from fastapi import APIRouter
from controllers import auth
from controllers import user

root_api_router = APIRouter(prefix="/api/v1")

root_api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
root_api_router.include_router(user.router, prefix="/user", tags=["User"])
