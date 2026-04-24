from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.clients as client_module
from app.clients import AppClients
from app.routers import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup: create singleton clients once ─────────────────────────────
    client_module.clients = AppClients()
    await client_module.clients.ensure_search_index()
    print("Azure clients initialised.")
    yield
    # ── Shutdown: close connections cleanly ───────────────────────────────
    await client_module.clients.close()
    print("Azure clients closed.")


app = FastAPI(title="Investment Coach API", version="1.0.0", lifespan=lifespan)

ASWA_ORIGIN = "https://wonderful-moss-09a2daf0f.7.azurestaticapps.net"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ASWA_ORIGIN,
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

app.include_router(health.router, prefix="/v1")
app.include_router(chat.router, prefix="/v1")
