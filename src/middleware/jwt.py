from starlette.authentication import AuthCredentials, UnauthenticatedUser, BaseUser
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi.responses import Response
from fastapi.requests import Request

from models import schemas, Role, UserStates
from services.auth import JWTManager
from services.auth import SessionManager
from services import repository


class JWTMiddleware(BaseHTTPMiddleware):

    def __init__(
            self,
            app,
            jwt: JWTManager = JWTManager(),
            session: SessionManager = SessionManager(),
    ):
        super().__init__(app)

        self._jwt = jwt
        self._session = session
        self.UserRepo = repository.user

        self.session_id = None
        self.current_tokens = None
        self._is_need_update = False
        self._is_auth = False

    async def dispatch(self, request: Request, call_next):
        await self.pre_process(request)
        response = await call_next(request)
        await self.post_process(request, response)
        return response

    async def pre_process(self, request: Request):
        # Проверка авторизации
        self.current_tokens = self._jwt.get_jwt_cookie(request)
        if self.current_tokens:
            is_valid_access_token = self._jwt.is_valid_access_token(self.current_tokens.access_token)
            is_valid_refresh_token = self._jwt.is_valid_refresh_token(self.current_tokens.refresh_token)
            is_valid_session = False

            if is_valid_refresh_token:
                # Проверка валидности сессии
                self.session_id = self._session.get_session_id(request)
                if await self._session.is_valid_session(self.session_id, self.current_tokens.refresh_token):
                    is_valid_session = True

            self._is_auth = is_valid_access_token and is_valid_refresh_token and is_valid_session
            self._is_need_update = (not is_valid_access_token) and is_valid_refresh_token and is_valid_session

        # Обновление токенов
        if self._is_need_update:
            user_id = self._jwt.decode_refresh_token(self.current_tokens.refresh_token).id
            user = await self.UserRepo.get_user(id=user_id)
            if user:
                new_payload = schemas.TokenPayload(
                    id=user.id,
                    username=user.username,
                    role_id=user.role_id,
                    state_id=user.state_id,
                    exp=0
                )  # exp не используется, но нужно для составления модели
                _new_tokens = schemas.Tokens(
                    access_token=self._jwt.generate_access_token(**new_payload.dict()),
                    refresh_token=self._jwt.generate_refresh_token(**new_payload.dict())
                )
                # Для бесшовного обновления токенов:
                request.cookies["access_token"] = _new_tokens.access_token
                request.cookies["refresh_token"] = _new_tokens.refresh_token
                self.current_tokens = _new_tokens

        # Установка данных авторизации
        if self._is_auth:
            payload: schemas.TokenPayload = self._jwt.decode_access_token(self.current_tokens.access_token)
            request.scope["user"] = AuthenticatedUser(**payload.dict())
            request.scope["auth"] = AuthCredentials(["authenticated"])
        else:
            request.scope["user"] = UnauthenticatedUser()
            request.scope["auth"] = AuthCredentials()

    async def post_process(self, request: Request, response: Response):
        if self._is_need_update:
            # Обновляем response
            self._jwt.set_jwt_cookie(response, self.current_tokens)
            await self._session.set_session_id(response, self.current_tokens.refresh_token, self.session_id)


class AuthenticatedUser(BaseUser):
    def __init__(self, id: int, username: str, role_id: int, state_id: int, **kwargs):
        self.id = id
        self.username = username
        self.role_id = role_id
        self.state_id = state_id

    def is_authenticated(self) -> bool:
        return True

    def display_name(self) -> str:
        return self.username

    def identity(self) -> int:
        return self.id

    def role(self) -> Role:
        return Role.from_int(self.role_id)

    def state(self) -> UserStates:
        return UserStates(self.state_id)

    def __eq__(self, other):
        return isinstance(other, AuthenticatedUser) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"<AuthenticatedUser(id={self.id}, username={self.username})>"
