from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from txnweave_api.db.database import init_db
from txnweave_api.routes import documents, graphs, imports, investigations, settings
from txnweave_api.services.errors import AppError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # create the database file and tables on startup (B1)
    yield


app = FastAPI(title="TxnWeave API", lifespan=lifespan)

# All endpoints are prefixed /api.
app.include_router(investigations.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(graphs.router, prefix="/api")
app.include_router(imports.router, prefix="/api")


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, error: AppError) -> JSONResponse:
    """The app error body: {"detail": {"code": ..., "message": ..., ...extra}} (api.md)."""
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, error: RequestValidationError) -> JSONResponse:
    """FastAPI's standard 422 body, minus the `input` echo, so a card number sent in a bad
    request is never sent back (BD8, B13)."""
    errors = [{key: value for key, value in item.items() if key != "input"} for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})


@app.get("/api/hello")
def hello_world():
    return {"message": "Hello World"}
