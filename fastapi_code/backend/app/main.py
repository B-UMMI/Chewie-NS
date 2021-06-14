import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

# from app import tasks
from app.api.api_v1.routers.auth import auth_router
from app.api.api_v1.routers.loci.loci import loci_router
from app.api.api_v1.routers.sequences.sequences import sequences_router
from app.api.api_v1.routers.species.species import species_router
from app.api.api_v1.routers.stats.stats import stats_router
from app.api.api_v1.routers.users import users_router
from app.core import config
from app.core.auth import get_current_active_user
from app.core.celery_app import celery_app
from app.db.session import SessionLocal

import time

app = FastAPI(
    title=config.PROJECT_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api",
    default_response_class=ORJSONResponse,
)

origins = [
    "http://localhost:8888",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response


@app.get("/api/v1")
async def root():
    return {"message": "Sanity check"}


@app.get("/api/v1/task")
async def example_task():
    ola = celery_app.send_task("app.tasks.example_task", args=["Hello World"])

    time.sleep(3)

    print(ola.result, flush=True)

    return {"message": "success"}


@app.get("/api/v1/loci_task")
async def example_task2():
    ola = celery_app.send_task("app.loci_tasks.example_task2", args=["Hello World"])

    time.sleep(3)

    print(ola.result, flush=True)

    return {"message": "success"}


# Routers
app.include_router(auth_router, prefix="/api", tags=["auth"])

app.include_router(
    users_router,
    prefix="/api/v1",
    tags=["users"],
    dependencies=[Depends(get_current_active_user)],
)

app.include_router(
    stats_router, prefix="/api/v1", tags=["stats"],
)

app.include_router(
    loci_router, prefix="/api/v1", tags=["loci"],
)

app.include_router(
    species_router, prefix="/api/v1", tags=["species"],
)

app.include_router(
    sequences_router, prefix="/api/v1", tags=["sequences"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8888)
