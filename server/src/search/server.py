from typing import Optional, List, Dict, Any
import time
from uuid import uuid4
import logging
import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, BaseSettings
from starlette.middleware.cors import CORSMiddleware
import uvicorn, logging

# Import PTO scheduling functions
from src.search.pto_tools import get_current_month_schedule
from src.search._search import PlanStore

class Settings(BaseSettings):
    APP_NAME: str = "Idea Generator - Search Server"
    VERSION: str = "0.1.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"

settings = Settings()

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger("search.server")

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CalendarRequest(BaseModel):
    store_json: Optional[str] = None
    additional_pto: Optional[Dict[str, List[str]]] = None
    timezone_offset: int = 0
    use_global_pto: bool = True
    plan_data: Optional[Dict[str, Any]] = None

# Minimal exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "validation_error", "details": exc.errors()})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"error": "internal_server_error"})

# 3 endpoints: root, search, items
@app.get("/", tags=["meta"])
async def root():
    return {"service": settings.APP_NAME, "version": settings.VERSION}

@app.post("/calendar", tags=["calendar"])
async def get_calendar(req: CalendarRequest):
    start_time = time.time()
    request_id = str(uuid4())
    
    try:
        # Multiple options for creating/using PlanStore:
        
        # Option 1: Use provided JSON string (most flexible)
        if req.store_json:
            store = req.store_json
        # Option 2: Create PlanStore from plan_data dict
        elif req.plan_data:
            store = PlanStore.from_json(json.dumps(req.plan_data))
        # Option 3: Create empty PlanStore (fresh scheduling)
        else:
            store = PlanStore()
        
        # Generate the monthly schedule using global PTO system
        schedule_result = get_current_month_schedule(
            store=store,
            now_epoch=int(time.time()),
            pto_map=req.additional_pto,  # type: ignore
            tz_offset_hours=req.timezone_offset,
            use_global_pto=req.use_global_pto
        )
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return {
            "request_id": request_id,
            "success": True,
            "schedule": schedule_result,
            "took_ms": took_ms
        }
        
    except Exception as e:
        logger.exception("Error generating calendar")
        took_ms = int((time.time() - start_time) * 1000)
        return JSONResponse(
            status_code=500,
            content={
                "request_id": request_id,
                "success": False,
                "error": str(e),
                "took_ms": took_ms
            }
        )


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=settings.DEBUG, log_level="debug" if settings.DEBUG else "info")
