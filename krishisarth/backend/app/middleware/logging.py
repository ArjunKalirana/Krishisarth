import time
import json
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure app access logger
logger = logging.getLogger("app.access")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured JSON logging and request tracking.
    Injects X-Request-ID into headers.
    """
    async def dispatch(self, request: Request, call_next):
        # Generate short request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Execute the next handler
        try:
            response: Response = await call_next(request)
        except Exception as e:
            # Basic error capture handled by global exception handler, but log context here
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Request failed: {str(e)} | duration={duration_ms}ms")
            raise e
            
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Extract user context if available (injected by AuthMiddleware)
        farmer_id = None
        if hasattr(request.state, "farmer"):
            farmer_id = str(request.state.farmer.id)
            
        log_data = {
            "req_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": f"{duration_ms}ms",
            "farmer_id": farmer_id
        }
        
        # Output structured log
        logger.info(json.dumps(log_data))
        
        # Return ID to client for debugging triage
        response.headers["X-Request-ID"] = request_id
        return response
