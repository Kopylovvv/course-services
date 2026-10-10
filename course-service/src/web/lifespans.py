import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_service_router(app: FastAPI):
    logger.debug("Lifespan (service router) startup")
    yield
    logger.debug("Lifespan (service router) shutdown")


@asynccontextmanager
async def lifespan_app(app: FastAPI):
    logger.debug("Lifespan (app) startup")
    yield
    logger.debug("Lifespan (app) shutdown")
