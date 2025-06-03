
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import data, user, auth

from rich.console import Console

console = Console()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    console.print(":banana: [cyan underline] QronoTract-Api  is starting ...[/]")
    yield
    console.print(":mango: [bold red underline] QronoTract-Api  shutting down ...[/]")



app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(data.router)


