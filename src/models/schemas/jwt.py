from pydantic import BaseModel


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    id: int
    username: str
    role_id: int
    state_id: int
    exp: int