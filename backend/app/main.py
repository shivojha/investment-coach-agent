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
    print("Azure clients initialised.")
    yield
    # ── Shutdown: close connections cleanly ───────────────────────────────
    await client_module.clients.close()
    print("Azure clients closed.")


app = FastAPI(title="Investment Coach API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.azurestaticapps.net", "http://localhost:5174"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router, prefix="/v1")
app.include_router(chat.router, prefix="/v1")
