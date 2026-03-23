from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine
from app.core.exception_handlers import add_exception_handlers
from app.core.limiter import limiter
from app.routes import auth, conversation, health, journal, memory, note, profile, recovery, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
add_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(journal.router, prefix="/api/v1")
app.include_router(recovery.router, prefix="/api/v1")
app.include_router(conversation.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(note.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
