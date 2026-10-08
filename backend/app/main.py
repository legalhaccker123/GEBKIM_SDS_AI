import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.chemicals import router as chemicals_router
from app.api.sds import router as sds_router


# =========================================================
# DEVELOPMENT / PACKAGED PATHS
# =========================================================

IS_FROZEN = bool(
    getattr(
        sys,
        "frozen",
        False,
    )
)


if IS_FROZEN:

    # PyInstaller tarafından paketlenen salt-okunur
    # uygulama kaynaklarının bulunduğu klasör.
    RESOURCE_ROOT = Path(
        getattr(
            sys,
            "_MEIPASS",
            Path(sys.executable).parent,
        )
    )

else:

    # main.py:
    # GEBKIM_SDS_PRO/backend/app/main.py
    #
    # parents[2]:
    # GEBKIM_SDS_PRO
    RESOURCE_ROOT = (
        Path(__file__)
        .resolve()
        .parents[2]
    )


FRONTEND_DIST = (
    RESOURCE_ROOT
    / "frontend"
    / "dist"
)

FRONTEND_INDEX = (
    FRONTEND_DIST
    / "index.html"
)

FRONTEND_ASSETS = (
    FRONTEND_DIST
    / "assets"
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="GEBKIM SDS AI Platform API",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# API ROUTERS
# =========================================================

app.include_router(
    chemicals_router
)

app.include_router(
    sds_router
)


# =========================================================
# HEALTH / API INFO
# =========================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "application": "GEBKIM SDS AI Platform",
        "version": "1.0.0",
    }


@app.get("/api-info")
def api_info():

    return {
        "application": "GEBKIM SDS AI Platform",
        "backend": "Professional API",
        "version": "1.0.0",
        "status": "running",
        "packaged": IS_FROZEN,
        "frontend_build_found": FRONTEND_INDEX.exists(),
    }


# =========================================================
# FRONTEND STATIC ASSETS
# =========================================================

if FRONTEND_ASSETS.exists():

    app.mount(
        "/assets",
        StaticFiles(
            directory=str(
                FRONTEND_ASSETS
            )
        ),
        name="frontend-assets",
    )


# =========================================================
# FRONTEND HOME
# =========================================================

@app.get("/")
def home():
    """
    React production frontend'i açar.

    Geliştirme ortamında:
        project/frontend/dist

    PyInstaller paketinde:
        bundled frontend/dist

    kullanılır.
    """

    if FRONTEND_INDEX.exists():

        return FileResponse(
            str(
                FRONTEND_INDEX
            )
        )


    return {
        "application": "GEBKIM SDS AI Platform",
        "backend": "Professional API",
        "version": "1.0.0",
        "status": "running",
        "frontend": "build_not_found",
        "resource_root": str(
            RESOURCE_ROOT
        ),
        "message": (
            "Frontend production build bulunamadı."
        ),
    }