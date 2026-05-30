from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.agent import get_agent
from backend.routes.chat import router as chat_router

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = get_agent()
    await agent.setup()
    yield
    await agent.teardown()


app = FastAPI(title="Stock Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
