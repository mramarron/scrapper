from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config.database import Base, engine, mssql_engine
from backend.routes import directory, home


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if mssql_engine is not None:
        with mssql_engine.connect():
            pass
    yield


app = FastAPI(title="Scrapper API", lifespan=lifespan)

origins=[
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home.router, tags=["home"])
app.include_router(directory.router, tags=["directory"])