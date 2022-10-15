from typing import List, Optional
from tortoise.expressions import Q

from src.models import tables
from src.models import Role, A, M
from src.models import UserStates
from src.utils import get_hashed_password


class UserRepository:
    def __init__(self):
        self._db = tables.User

    async def get_user(self, *args, **kwargs) -> Optional[tables.User]:
        return await self._db.get_or_none(*args, **kwargs)

    async def get_users(self, *args, **kwargs) -> Optional[List[tables.User]]:
        return await self._db.filter(*args, **kwargs)

    async def create_user(self, **kwargs) -> tables.User:
        return await self._db.create(
            role=Role(M.user, A.one),
            state=UserStates.not_confirmed,
            hashed_password=get_hashed_password(kwargs.pop("password")),
            **kwargs
        )

    async def update_user(self, user_id: int, **kwargs) -> tables.User:
        return await self._db.update_from_dict(await self.get_user(id=user_id), kwargs)  # todo: упростить

    async def delete_user(self, user_id: int) -> int:
        return await self._db.filter(id=user_id).delete()

    async def get_user_by_username_or_email(self, username: str, email: str) -> Optional[tables.User]:
        return await self._db.filter(Q(username=username) | Q(email=email)).first()
