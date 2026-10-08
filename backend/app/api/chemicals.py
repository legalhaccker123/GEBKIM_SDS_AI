from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.session import SessionLocal
from app.models import Chemical, SDSDocument
from app.schemas.chemical import ChemicalCreate, ChemicalRead


router = APIRouter(
    prefix="/chemicals",
    tags=["Chemicals"]
)


# =========================================================
# DATABASE SESSION
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# HELPERS
# =========================================================

def _serialize_identifier(identifier) -> dict:
    return {
        "id": identifier.id,
        "identifier_type": identifier.identifier_type,
        "identifier_value": identifier.identifier_value,
    }


def _serialize_sds(
    document: SDSDocument
) -> dict:

    return {
        "id": document.id,

        "original_filename":
            document.original_filename,

        "preparation_date":
            document.preparation_date,

        "revision_date":
            document.revision_date,

        "version":
            document.version,

        "language":
            document.language,

        "is_current":
            document.is_current,

        "processing_status":
            document.processing_status,

        "uploaded_at":
            document.uploaded_at,
    }


def _get_chemical_with_relations(
    db: Session,
    chemical_id: int
) -> Chemical:

    statement = (
        select(Chemical)
        .options(
            selectinload(
                Chemical.identifiers
            ),
            selectinload(
                Chemical.sds_documents
            )
        )
        .where(
            Chemical.id == chemical_id
        )
    )

    chemical = db.scalar(
        statement
    )

    if chemical is None:
        raise HTTPException(
            status_code=404,
            detail="Kimyasal bulunamadı."
        )

    return chemical


def _sort_sds_documents(
    documents: list[SDSDocument]
) -> list[SDSDocument]:

    return sorted(
        documents,
        key=lambda document: (
            bool(
                document.is_current
            ),

            document.revision_date
            or date.min,

            document.uploaded_at
            or datetime.min,
        ),
        reverse=True
    )


# =========================================================
# CHEMICAL LIST
# =========================================================

@router.get(
    "/",
    response_model=list[ChemicalRead]
)
def get_chemicals(
    db: Session = Depends(
        get_db
    )
):

    statement = (
        select(Chemical)
        .order_by(
            Chemical.id
        )
    )

    chemicals = db.scalars(
        statement
    ).all()

    return chemicals


# =========================================================
# CREATE CHEMICAL
# =========================================================

@router.post(
    "/",
    response_model=ChemicalRead
)
def create_chemical(
    chemical_data: ChemicalCreate,
    db: Session = Depends(
        get_db
    )
):

    chemical = Chemical(
        product_name=
            chemical_data.product_name,

        manufacturer=
            chemical_data.manufacturer,

        description=
            chemical_data.description,

        internal_code=
            chemical_data.internal_code
    )

    db.add(
        chemical
    )

    db.commit()

    db.refresh(
        chemical
    )

    return chemical


# =========================================================
# CHEMICAL DETAIL
# =========================================================

@router.get(
    "/{chemical_id}"
)
def get_chemical_detail(
    chemical_id: int,
    db: Session = Depends(
        get_db
    )
):

    chemical = (
        _get_chemical_with_relations(
            db=db,
            chemical_id=chemical_id
        )
    )

    # -----------------------------------------------------
    # IDENTIFIERS
    # -----------------------------------------------------

    identifiers = sorted(
        chemical.identifiers,
        key=lambda identifier: (
            identifier.identifier_type,
            identifier.identifier_value
        )
    )

    # -----------------------------------------------------
    # SDS DOCUMENTS
    # -----------------------------------------------------

    sds_documents = (
        _sort_sds_documents(
            chemical.sds_documents
        )
    )

    current_sds = next(
        (
            document
            for document
            in sds_documents
            if document.is_current
        ),
        None
    )

    latest_sds = (
        sds_documents[0]
        if sds_documents
        else None
    )

    needs_review_count = sum(
        1
        for document
        in sds_documents
        if document.processing_status
        == "needs_review"
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {
        "id":
            chemical.id,

        "product_name":
            chemical.product_name,

        "manufacturer":
            chemical.manufacturer,

        "description":
            chemical.description,

        "internal_code":
            chemical.internal_code,

        "is_active":
            chemical.is_active,

        "created_at":
            chemical.created_at,

        "updated_at":
            chemical.updated_at,

        "identifiers": [
            _serialize_identifier(
                identifier
            )
            for identifier
            in identifiers
        ],

        "sds_summary": {
            "total_documents":
                len(
                    sds_documents
                ),

            "current_sds_id":
                (
                    current_sds.id
                    if current_sds
                    else None
                ),

            "latest_sds_id":
                (
                    latest_sds.id
                    if latest_sds
                    else None
                ),

            "needs_review_count":
                needs_review_count,
        },

        "current_sds":
            (
                _serialize_sds(
                    current_sds
                )
                if current_sds
                else None
            ),
    }


# =========================================================
# SDS REVISION HISTORY
# =========================================================

@router.get(
    "/{chemical_id}/sds"
)
def get_chemical_sds_history(
    chemical_id: int,
    db: Session = Depends(
        get_db
    )
):

    chemical = (
        _get_chemical_with_relations(
            db=db,
            chemical_id=chemical_id
        )
    )

    sds_documents = (
        _sort_sds_documents(
            chemical.sds_documents
        )
    )

    return {
        "chemical": {
            "id":
                chemical.id,

            "product_name":
                chemical.product_name,

            "manufacturer":
                chemical.manufacturer,

            "internal_code":
                chemical.internal_code,
        },

        "total_sds_documents":
            len(
                sds_documents
            ),

        "current_sds_id":
            next(
                (
                    document.id
                    for document
                    in sds_documents
                    if document.is_current
                ),
                None
            ),

        "sds_documents": [
            _serialize_sds(
                document
            )
            for document
            in sds_documents
        ],
    }