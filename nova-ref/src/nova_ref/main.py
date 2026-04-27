from fastapi import FastAPI
from .api import lookup_router, search_router, ingest_router, feedback_router, health_router
from .api.rate_limits import router as rate_limits_router

app = FastAPI(title="nova-ref", version="0.1.0")
app.include_router(lookup_router)
app.include_router(search_router)
app.include_router(ingest_router)
app.include_router(feedback_router)
app.include_router(health_router)
app.include_router(rate_limits_router)
