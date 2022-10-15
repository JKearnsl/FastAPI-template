"""Application implementation - ASGI."""
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from .config import load_config
from .exceptions.api import APIError, api_exception_handler, not_found_exception_handler, validation_exception_handler
from .router import root_api_router
from .utils import RedisClient, AiohttpClient

config = load_config()
log = logging.getLogger(__name__)


async def on_startup():
    log.debug("Execute FastAPI startup event handler.")
    if config.db.redis:
        await RedisClient.open_redis_client()

    AiohttpClient.get_aiohttp_client()


async def on_shutdown():
    log.debug("Execute FastAPI shutdown event handler.")
    # Gracefully close utilities.
    if config.db.postgresql:
        await RedisClient.close_redis_client()
    await AiohttpClient.close_aiohttp_client()


log.debug("Initialize FastAPI application node.")
app = FastAPI(
    title=config.base.name,
    debug=config.debug,
    version=config.base.vers,
    description=config.base.description,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    contact={
        "name": config.base.contact.name,
        "url": config.base.contact.url,
        "email": config.base.contact.email,
    },
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
)
log.debug("Add application routes.")
app.include_router(root_api_router)
log.debug("Register global exception handler for custom HTTPException.")
app.add_exception_handler(APIError, api_exception_handler)
app.add_exception_handler(404, not_found_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
