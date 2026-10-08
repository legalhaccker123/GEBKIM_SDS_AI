# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_submodules,
)


# =========================================================
# PROJECT PATHS
# =========================================================

BACKEND_DIR = Path(SPECPATH)
PROJECT_ROOT = BACKEND_DIR.parent

FRONTEND_DIST = (
    PROJECT_ROOT
    / "frontend"
    / "dist"
)

SEED_DATABASE = (
    BACKEND_DIR
    / "gebkim_sds_dev.db"
)

SEED_UPLOADS = (
    BACKEND_DIR
    / "uploads"
)


# =========================================================
# DATA FILES
# =========================================================

datas = []


# React production build
if FRONTEND_DIST.exists():

    datas.append(
        (
            str(FRONTEND_DIST),
            "frontend/dist",
        )
    )


# Initial SQLite database
if SEED_DATABASE.exists():

    datas.append(
        (
            str(SEED_DATABASE),
            "seed",
        )
    )


# Initial uploaded SDS files
if SEED_UPLOADS.exists():

    datas.append(
        (
            str(SEED_UPLOADS),
            "seed/uploads",
        )
    )


# =========================================================
# HIDDEN IMPORTS
# =========================================================

hiddenimports = []


hiddenimports += collect_submodules(
    "app"
)


hiddenimports += [
    "uvicorn.logging",

    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",

    "uvicorn.protocols",

    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",

    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",

    "uvicorn.lifespan",
    "uvicorn.lifespan.on",

    "multipart",
]


# =========================================================
# ANALYSIS
# =========================================================

a = Analysis(
    [
        str(
            BACKEND_DIR
            / "launcher.py"
        )
    ],

    pathex=[
        str(
            BACKEND_DIR
        )
    ],

    binaries=[],

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False,

    optimize=0,
)


# =========================================================
# PYZ
# =========================================================

pyz = PYZ(
    a.pure
)


# =========================================================
# EXE
# =========================================================

exe = EXE(
    pyz,

    a.scripts,

    [],

    exclude_binaries=True,

    name="GEBKIM_SDS_AI",

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    upx=True,

    console=False,

    disable_windowed_traceback=False,

    argv_emulation=False,

    target_arch=None,

    codesign_identity=None,

    entitlements_file=None,
)


# =========================================================
# COLLECT
# =========================================================

coll = COLLECT(
    exe,

    a.binaries,

    a.datas,

    strip=False,

    upx=True,

    upx_exclude=[],

    name="GEBKIM_SDS_AI",
)