"""
main.py
--------
FastAPI application entrypoint for the E-Commerce backend (Day 1 milestone:
auth + RBAC foundation).

Run with: uvicorn main:app --reload
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from routes import auth, cart, checkout, orders, products

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Day 1: Project setup, authentication, and role-based access control.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": str(exc) if settings.DEBUG else "Something went wrong."},
    )


app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}


@app.get("/version", tags=["System"])
def version():
    return {"app_name": settings.APP_NAME, "version": settings.APP_VERSION}
