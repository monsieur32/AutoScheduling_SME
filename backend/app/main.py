"""
FastAPI application entry point.
Assembles all routers and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, DEBUG
from .api.routes_dxf import router as dxf_router
from .api.routes_jobs import router as jobs_router
from .api.routes_machines import router as machines_router
from .api.routes_schedule import router as schedule_router
from .api.routes_masterdata import router as masterdata_router
from .api.routes_worker import router as worker_router
from .api.ws_handler import router as ws_router

# Initialize tables on startup (via import side-effect)
from .database import session as _  # noqa: F401


app = FastAPI(
    title="AutoScheduling SME — Backend API",
    description=(
        "Backend API cho Hệ thống Lập lịch Sản xuất Tự động.\n\n"
        "Cung cấp REST endpoints để quản lý Job Queue, chạy thuật toán GA-VNS, "
        "quản lý Master Data, và WebSocket cho cập nhật thời gian thực."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────
app.include_router(dxf_router)
app.include_router(jobs_router)
app.include_router(machines_router)
app.include_router(schedule_router)
app.include_router(masterdata_router)
app.include_router(worker_router)
app.include_router(ws_router)


# ─── Health Check ────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "AutoScheduling SME API",
        "version": "2.0.0",
    }


@app.get("/api/health", tags=["Health"])
def api_health():
    return {"status": "ok"}
