import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.custom_suites import router as custom_suites_router
from .api.evaluations import router as eval_router
from .api.health import router as health_router
from .api.stream import router as stream_router
from .core.settings import settings
from .services import database, redis_client
from .services.chroma_store import init_chroma

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AgentProbe API starting up")

    # PostgreSQL
    await database.init_db(settings.asyncpg_url)

    # Redis
    await redis_client.init_redis(settings.redis_url)

    # ChromaDB (sync — runs in-process with PersistentClient)
    init_chroma(settings.chromadb_path)

    logger.info("All services initialised — ready to serve")
    yield

    # Teardown
    await redis_client.close_redis()
    await database.close_db()
    logger.info("AgentProbe API shut down cleanly")


app = FastAPI(
    title="AgentProbe API",
    description="Multi-agent AI stress-testing platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(eval_router)
app.include_router(stream_router)
app.include_router(health_router)
app.include_router(custom_suites_router)


@app.get("/")
async def root() -> dict:
    return {
        "name": "AgentProbe API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
