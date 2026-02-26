"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, armies, auth, messages, nations, sectors, worlds

app = FastAPI(
    title=settings.project_name,
    description="Conquer v5 reboot — multi-player turn-based strategy game API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],  # React game UI (nginx)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(worlds.router)
app.include_router(nations.router)
app.include_router(sectors.router)
app.include_router(armies.router)
app.include_router(messages.router)
app.include_router(admin.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
