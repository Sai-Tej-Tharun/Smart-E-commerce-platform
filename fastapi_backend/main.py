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
from fastapi.staticfiles import StaticFiles

from core.media import MEDIA_ROOT

from core.config import settings
from routes import admin_returns, auth, blog, cart, checkout, dashboard, notifications, orders, products, recommendations, reviews, subscriptions, support, ws

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

MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": str(exc) if settings.DEBUG else "Something went wrong."},
    )


app.include_router(auth.router)
app.include_router(blog.router) 
app.include_router(dashboard.router)
app.include_router(support.router)
# recommendations.router defines GET /products/trending, which MUST be
# matched before products.router's GET /products/{product_id} — see
# routes/recommendations.py's module docstring.
app.include_router(recommendations.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(notifications.router)
app.include_router(ws.router)
app.include_router(admin_returns.router)
app.include_router(reviews.router)
app.include_router(subscriptions.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}


@app.get("/version", tags=["System"])
def version():
    return {"app_name": settings.APP_NAME, "version": settings.APP_VERSION}