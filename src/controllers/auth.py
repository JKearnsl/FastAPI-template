import logging

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import Response

from src.config import load_docs
from src.dependencies import JWTCookie
from src.exceptions.api import APIError
from src import utils
from src.services.auth import authenticate, logout, refresh_tokens
from src.views import ErrorAPIResponse, LoginResponse, RegisterResponse
from src.models import schemas
from src.services.repository import UserRepository

router = APIRouter(responses={"400": {"model": ErrorAPIResponse}})
docs = load_docs("auth.ini")


@router.post(
    "/signUp",
    response_model=RegisterResponse,
    summary=docs["signIn"]["summary"],
    description=docs["signIn"]["description"]
)
async def sign_up(
        user: schemas.UserSignUp,
        is_auth=Depends(JWTCookie(auto_error=False)),
        UserRepo: UserRepository = UserRepository()
):
    if is_auth:
        raise APIError(920)
    if await UserRepo.get_user_by_username_or_email(user.username, user.email):
        raise APIError(903)
    return await UserRepo.create_user(**user.dict())


@router.post(
    "/signIn",
    response_model=LoginResponse,
    summary=docs["signUp"]["summary"],
    description=docs["signUp"]["description"]
)
async def sign_in(
        user: schemas.UserSignIn,
        response: Response,
        is_auth=Depends(JWTCookie(auto_error=False))
):
    if is_auth:
        raise APIError(920)
    await authenticate(user.username, user.password, response)
    # todo: return user info


@router.post('/logout', summary="Выход из аккаунта")
async def logout_controller(request: Request, response: Response):
    await logout(request, response)


@router.post('/refresh_tokens', dependencies=[Depends(JWTCookie())])
async def refresh(request: Request, response: Response):
    await refresh_tokens(request, response)


@router.get("/test", summary=docs["test"]["summary"], description=docs["test"]["description"])
async def test():
    return {"resp": await utils.RedisClient.ping()}
