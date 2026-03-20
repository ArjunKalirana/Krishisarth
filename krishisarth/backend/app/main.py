import uuid
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import rate_limit

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    default_response_class=JSONResponse,
    dependencies=[Depends(rate_limit)]
)

# Register Custom Middlewares
app.add_middleware(LoggingMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Global exception handler to return errors in the KrishiSarth standard envelope.
    Format: {"success": False, "error": {"code": "...", "message": "...", "request_id": "..."}}
    """
    # Prefer request_id if set by logging middleware, else generate one
    request_id = str(getattr(request.state, "request_id", uuid.uuid4()))
    
    # PROJECT_RULES.md 5.3: exc.detail must be a string code
    error_code = str(exc.detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail if isinstance(exc.detail, str) else "AN_ERROR_OCCURRED",
                "request_id": request_id
            }
        }
    )



@app.get("/health")
async def health_check():
    """
    Ping PostgreSQL, Redis, and InfluxDB to verify system health.
    Returns: status of each component.
    """
    from app.db.postgres import ping_db
    from app.db.redis import ping_redis
    from app.db.influxdb import ping_influx

    health = {
        "status": "healthy",
        "components": {
            "postgresql": "healthy" if ping_db() else "unhealthy",
            "redis": "healthy" if ping_redis() else "unhealthy",
            "influxdb": "healthy" if ping_influx() else "unhealthy"
        }
    }

    if any(status == "unhealthy" for status in health["components"].values()):
        health["status"] = "degraded"

    return health

# Router Registration
from app.api.v1 import api_router
app.include_router(api_router, prefix="/v1")
