import os
import shutil
import sys
from pathlib import Path


APP_NAME = "GEBKIM_SDS_AI"


# =========================================================
# APPLICATION MODE
# =========================================================

IS_FROZEN = bool(
    getattr(
        sys,
        "frozen",
        False,
    )
)


# =========================================================
# DEVELOPMENT ROOT
# =========================================================

BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


# =========================================================
# PACKAGED RESOURCE ROOT
# =========================================================

if IS_FROZEN:

    RESOURCE_ROOT = Path(
        getattr(
            sys,
            "_MEIPASS",
            Path(sys.executable).parent,
        )
    )

else:

    RESOURCE_ROOT = (
        BACKEND_ROOT.parent
    )


# =========================================================
# DATA DIRECTORY
# =========================================================

def get_data_dir() -> Path:

    # -----------------------------------------------------
    # Optional manual override
    # -----------------------------------------------------

    custom_data_dir = os.getenv(
        "GEBKIM_DATA_DIR"
    )

    if custom_data_dir:

        return (
            Path(
                custom_data_dir
            )
            .expanduser()
            .resolve()
        )


    # -----------------------------------------------------
    # Windows packaged application
    # -----------------------------------------------------

    if IS_FROZEN:

        local_app_data = os.getenv(
            "LOCALAPPDATA"
        )

        if local_app_data:

            return (
                Path(
                    local_app_data
                )
                / APP_NAME
            )


        return (
            Path.home()
            / APP_NAME
        )


    # -----------------------------------------------------
    # Development
    # -----------------------------------------------------

    return BACKEND_ROOT


DATA_DIR = get_data_dir()

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# PERSISTENT PATHS
# =========================================================

DATABASE_PATH = (
    DATA_DIR
    / "gebkim_sds_dev.db"
)

UPLOAD_DIR = (
    DATA_DIR
    / "uploads"
)

SEED_MARKER = (
    DATA_DIR
    / ".seed_initialized"
)


# =========================================================
# FIRST-RUN SEED DATA
# =========================================================

def initialize_seed_data():

    # -----------------------------------------------------
    # Development mode
    #
    # Existing backend database/uploads are used directly.
    # -----------------------------------------------------

    if not IS_FROZEN:

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        return


    # -----------------------------------------------------
    # Already initialized
    # -----------------------------------------------------

    if SEED_MARKER.exists():

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        return


    # -----------------------------------------------------
    # Do not overwrite pre-existing user data
    # -----------------------------------------------------

    existing_user_data = (
        DATABASE_PATH.exists()
        or UPLOAD_DIR.exists()
    )


    if existing_user_data:

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        SEED_MARKER.write_text(
            "existing_data_preserved",
            encoding="utf-8",
        )

        return


    # -----------------------------------------------------
    # Bundled seed locations
    # -----------------------------------------------------

    seed_root = (
        RESOURCE_ROOT
        / "seed"
    )

    seed_database = (
        seed_root
        / "gebkim_sds_dev.db"
    )

    seed_uploads = (
        seed_root
        / "uploads"
    )


    # -----------------------------------------------------
    # Copy seed database
    # -----------------------------------------------------

    if seed_database.exists():

        shutil.copy2(
            seed_database,
            DATABASE_PATH,
        )


    # -----------------------------------------------------
    # Copy seed SDS PDFs
    # -----------------------------------------------------

    if seed_uploads.exists():

        shutil.copytree(
            seed_uploads,
            UPLOAD_DIR,
        )

    else:

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )


    # -----------------------------------------------------
    # Initialization marker
    # -----------------------------------------------------

    SEED_MARKER.write_text(
        "seed_initialized",
        encoding="utf-8",
    )


initialize_seed_data()