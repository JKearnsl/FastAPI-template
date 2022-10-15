import uuid
from typing import Optional

from fastapi import Request, Response
from ...config import load_config
from ...utils import RedisClient

config = load_config()


class SessionManager:
    COOKIE_EXP = 31536000
    COOKIE_PATH = "/api" if not config.debug else "/"   # todo: изменить конфиг
    COOKIE_DOMAIN = None
    COOKIE_SESSION_KEY = "session_id"

    def get_session_id(self, request: Request) -> Optional[int]:
        """
        Выдает идентификатор сессии из куков

        :param request:
        :return: session_id
        """

        str_cookie_session_id = request.cookies.get(self.COOKIE_SESSION_KEY)
        try:
            cookie_session_id = int(str_cookie_session_id)
        except (ValueError, TypeError):
            return None
        return cookie_session_id

    async def set_session_id(
            self,
            response: Response,
            refresh_token: str,
            session_id: int = None
    ) -> int:
        """
        Генерирует и устанавливает сессию в redis и в куки

        :param response: 
        :param refresh_token: 
        :param session_id: 
        :return: session_id
        """
        if not session_id:
            session_id = uuid.uuid4().int
        response.set_cookie(
            key=self.COOKIE_SESSION_KEY,
            value=str(session_id),
            secure=not config.debug,  # todo изменить конфиг
            httponly=True,
            samesite="Strict",
            max_age=self.COOKIE_EXP,
            path=self.COOKIE_PATH
        )
        await RedisClient.set(str(session_id), refresh_token)
        return session_id

    async def delete_session_id(self, session_id: int, response: Response) -> None:
        """
        Удаляет сессию из куков и из redis

        :param
        """
        await RedisClient.delete(str(session_id))
        response.delete_cookie(
            key=self.COOKIE_SESSION_KEY,
            secure=not config.debug,   # todo изменить конфиг
            httponly=True,
            samesite="Strict",
            path=self.COOKIE_PATH
        )

    async def is_valid_session(self, session_id: int, cookie_refresh_token: str) -> bool:
        """
        Проверяет валидность сессии
        :param session_id:
        :param cookie_refresh_token:
        :return: True or False
        """
        redis_refresh_token = await RedisClient.get(str(session_id))
        if not redis_refresh_token:
            return False
        if redis_refresh_token != cookie_refresh_token:
            return False
        return True