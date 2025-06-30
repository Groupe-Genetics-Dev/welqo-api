
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import data, user, auth, guard, qrcode, owner, report

from rich.console import Console
from app.config import settings
console = Console()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    console.print(":banana: [cyan underline] Welqo services  is starting ...[/]")
    yield
    console.print(":mango: [bold red underline] Welqo services  shutting down ...[/]")



app = FastAPI(lifespan=lifespan)

# origins = ["http://95.111.231.146"]
origins =settings.cors_origin.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ajout de la route racine
@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API Acces-Residence de Genetics",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs"
    }

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(guard.router, prefix="/api/v1")
app.include_router(qrcode.router, prefix="/api/v1")
app.include_router(owner.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
