"""
ArtiCurated Order Management System

Main application entry point for FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import orders, returns, health

# Create FastAPI application
app = FastAPI(
    title="ArtiCurated Order Management API",
    description="RESTful API for managing orders and returns with state machine validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders.router, prefix=settings.API_V1_PREFIX, tags=["orders"])
app.include_router(returns.router, prefix=settings.API_V1_PREFIX, tags=["returns"])
app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["health"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "ArtiCurated Order Management API",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
