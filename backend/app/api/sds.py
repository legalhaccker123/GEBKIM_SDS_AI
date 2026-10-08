import hashlib
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.runtime_paths import UPLOAD_DIR

from app.models import (
    Chemical,
    ChemicalIdentifier,
    SDSDocument,
    SDSSection,
    HazardStatement,
    PrecautionaryStatement,
    GHSPictogram,
    SDSStorageInfo,
    SDSPPEInfo,
    SDSPhysicalProperties,
)

from app.services.pdf_reader import extract_pdf_text
from app.services.revision_manager import determine_is_current
from app.services.sds_ingestion import ingest_sds_text


router = APIRouter(
    prefix="/sds",
    tags=["SDS"]
)




# =========================================================
# DATABASE
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# SHA-256
# =========================================================

def calculate_sha256(
    file_path: Path
) -> str:

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as file:

        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


# =========================================================
# CHEMICAL IDENTIFIERS
# =========================================================

def save_chemical_identifiers(
    db: Session,
    chemical: Chemical,
    parsed_data: dict
):

    identifiers_to_save = []

    # CAS
    for cas_number in (
        parsed_data.get("cas_numbers")
        or []
    ):

        identifiers_to_save.append(
            (
                "CAS",
                cas_number
            )
        )

    # EC
    ec_number = parsed_data.get(
        "ec_number"
    )

    if ec_number:

        identifiers_to_save.append(
            (
                "EC",
                ec_number
            )
        )

    # REACH
    reach_number = parsed_data.get(
        "reach_number"
    )

    if reach_number:

        identifiers_to_save.append(
            (
                "REACH",
                reach_number
            )
        )

    # UFI
    ufi = parsed_data.get(
        "ufi"
    )

    if ufi:

        identifiers_to_save.append(
            (
                "UFI",
                ufi
            )
        )

    # SAVE
    for (
        identifier_type,
        identifier_value
    ) in identifiers_to_save:

        existing_identifier = db.scalar(
            select(
                ChemicalIdentifier
            ).where(
                ChemicalIdentifier.chemical_id
                == chemical.id,

                ChemicalIdentifier.identifier_type
                == identifier_type,

                ChemicalIdentifier.identifier_value
                == identifier_value
            )
        )

        if existing_identifier:
            continue

        db.add(
            ChemicalIdentifier(
                chemical_id=chemical.id,
                identifier_type=identifier_type,
                identifier_value=identifier_value
            )
        )


# =========================================================
# H / P / GHS DATABASE SAVE
# =========================================================

def save_sds_hazard_data(
    db: Session,
    sds_document: SDSDocument,
    parsed_data: dict
):

    # -----------------------------------------------------
    # H CODES
    # -----------------------------------------------------

    for code in (
        parsed_data.get(
            "hazard_codes"
        )
        or []
    ):

        existing = db.scalar(
            select(
                HazardStatement
            ).where(
                HazardStatement.sds_document_id
                == sds_document.id,

                HazardStatement.code
                == code
            )
        )

        if existing:
            continue

        db.add(
            HazardStatement(
                sds_document_id=
                    sds_document.id,

                code=
                    code,

                statement_text=
                    None
            )
        )

    # -----------------------------------------------------
    # P CODES
    # -----------------------------------------------------

    for code in (
        parsed_data.get(
            "precautionary_codes"
        )
        or []
    ):

        existing = db.scalar(
            select(
                PrecautionaryStatement
            ).where(
                PrecautionaryStatement.sds_document_id
                == sds_document.id,

                PrecautionaryStatement.code
                == code
            )
        )

        if existing:
            continue

        db.add(
            PrecautionaryStatement(
                sds_document_id=
                    sds_document.id,

                code=
                    code,

                statement_text=
                    None
            )
        )

    # -----------------------------------------------------
    # GHS
    # -----------------------------------------------------

    for code in (
        parsed_data.get(
            "ghs_codes"
        )
        or []
    ):

        existing = db.scalar(
            select(
                GHSPictogram
            ).where(
                GHSPictogram.sds_document_id
                == sds_document.id,

                GHSPictogram.code
                == code
            )
        )

        if existing:
            continue

        db.add(
            GHSPictogram(
                sds_document_id=
                    sds_document.id,

                code=
                    code
            )
        )


# =========================================================
# SECTION 7 SAVE
# =========================================================

def save_storage_info(
    db: Session,
    sds_document: SDSDocument,
    section_7_data: dict
):

    existing = db.scalar(
        select(
            SDSStorageInfo
        ).where(
            SDSStorageInfo.sds_document_id
            == sds_document.id
        )
    )

    if existing:
        return

    db.add(
        SDSStorageInfo(

            sds_document_id=
                sds_document.id,

            handling_precautions=
                section_7_data.get(
                    "handling_precautions"
                )
                or [],

            storage_conditions=
                section_7_data.get(
                    "storage_conditions"
                )
                or [],

            incompatible_materials=
                section_7_data.get(
                    "incompatible_materials"
                )
                or [],

            fire_explosion_precautions=
                section_7_data.get(
                    "fire_explosion_precautions"
                )
                or [],

            specific_end_use=
                section_7_data.get(
                    "specific_end_use"
                )
        )
    )


# =========================================================
# SECTION 8 SAVE
# =========================================================

def save_ppe_info(
    db: Session,
    sds_document: SDSDocument,
    section_8_data: dict
):

    existing = db.scalar(
        select(
            SDSPPEInfo
        ).where(
            SDSPPEInfo.sds_document_id
            == sds_document.id
        )
    )

    if existing:
        return

    db.add(
        SDSPPEInfo(

            sds_document_id=
                sds_document.id,

            respiratory_protection=
                section_8_data.get(
                    "respiratory_protection"
                )
                or [],

            hand_protection=
                section_8_data.get(
                    "hand_protection"
                )
                or [],

            glove_materials=
                section_8_data.get(
                    "glove_materials"
                )
                or [],

            glove_thickness=
                section_8_data.get(
                    "glove_thickness"
                )
                or [],

            eye_face_protection=
                section_8_data.get(
                    "eye_face_protection"
                )
                or [],

            body_protection=
                section_8_data.get(
                    "body_protection"
                )
                or [],

            engineering_controls=
                section_8_data.get(
                    "engineering_controls"
                )
                or [],

            exposure_limits=
                section_8_data.get(
                    "exposure_limits"
                )
                or [],

            dnel=
                section_8_data.get(
                    "dnel"
                )
                or [],

            pnec=
                section_8_data.get(
                    "pnec"
                )
                or [],

            hygiene_measures=
                section_8_data.get(
                    "hygiene_measures"
                )
                or []
        )
    )


# =========================================================
# SECTION 9 SAVE
# =========================================================

def save_physical_properties(
    db: Session,
    sds_document: SDSDocument,
    section_9_data: dict
):

    existing = db.scalar(
        select(
            SDSPhysicalProperties
        ).where(
            SDSPhysicalProperties.sds_document_id
            == sds_document.id
        )
    )

    if existing:
        return

    db.add(
        SDSPhysicalProperties(

            sds_document_id=
                sds_document.id,

            physical_state=
                section_9_data.get(
                    "physical_state"
                ),

            color=
                section_9_data.get(
                    "color"
                ),

            odor=
                section_9_data.get(
                    "odor"
                ),

            ph=
                section_9_data.get(
                    "ph"
                ),

            flash_point=
                section_9_data.get(
                    "flash_point"
                ),

            boiling_point=
                section_9_data.get(
                    "boiling_point"
                ),

            melting_freezing_point=
                section_9_data.get(
                    "melting_freezing_point"
                ),

            density=
                section_9_data.get(
                    "density"
                ),

            viscosity=
                section_9_data.get(
                    "viscosity"
                ),

            solubility=
                section_9_data.get(
                    "solubility"
                ),

            vapour_pressure=
                section_9_data.get(
                    "vapour_pressure"
                ),

            flammability=
                section_9_data.get(
                    "flammability"
                ),

            explosive_properties=
                section_9_data.get(
                    "explosive_properties"
                ),

            oxidising_properties=
                section_9_data.get(
                    "oxidising_properties"
                ),

            lower_explosion_limit=
                section_9_data.get(
                    "lower_explosion_limit"
                ),

            upper_explosion_limit=
                section_9_data.get(
                    "upper_explosion_limit"
                )
        )
    )


# =========================================================
# CHEMICAL MATCHING
# =========================================================

def find_existing_chemical(
    db: Session,
    parsed_data: dict
) -> Chemical | None:

    product_name = parsed_data.get(
        "product_name"
    )

    manufacturer = parsed_data.get(
        "manufacturer"
    )

    product_code = parsed_data.get(
        "product_code"
    )

    ufi = parsed_data.get(
        "ufi"
    )

    # =====================================================
    # 1. UFI EXACT
    # =====================================================

    if ufi:

        identifier = db.scalar(
            select(
                ChemicalIdentifier
            ).where(
                ChemicalIdentifier.identifier_type
                == "UFI",

                func.lower(
                    ChemicalIdentifier.identifier_value
                )
                == ufi.strip().lower()
            )
        )

        if identifier:

            return db.get(
                Chemical,
                identifier.chemical_id
            )

    # =====================================================
    # 2. PRODUCT NAME + MANUFACTURER
    # =====================================================

    if product_name and manufacturer:

        chemical = db.scalar(
            select(
                Chemical
            ).where(
                func.lower(
                    Chemical.product_name
                )
                == product_name.strip().lower(),

                func.lower(
                    Chemical.manufacturer
                )
                == manufacturer.strip().lower()
            )
        )

        if chemical:

            return chemical

    # =====================================================
    # 3. PRODUCT CODE + MANUFACTURER
    # =====================================================

    if product_code and manufacturer:

        chemical = db.scalar(
            select(
                Chemical
            ).where(
                func.lower(
                    Chemical.internal_code
                )
                == product_code.strip().lower(),

                func.lower(
                    Chemical.manufacturer
                )
                == manufacturer.strip().lower()
            )
        )

        if chemical:

            return chemical

    # =====================================================
    # 4. PRODUCT NAME ONLY
    # =====================================================

    if product_name:

        chemical = db.scalar(
            select(
                Chemical
            ).where(
                func.lower(
                    Chemical.product_name
                )
                == product_name.strip().lower()
            )
        )

        if chemical:

            return chemical

    return None


# =========================================================
# SDS UPLOAD
# =========================================================

@router.post("/upload")
def upload_sds(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. PDF CONTROL
    # -----------------------------------------------------

    if file.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail=(
                "Sadece PDF dosyaları "
                "kabul edilir."
            )
        )

    original_filename = (
        file.filename
        or "unknown.pdf"
    )

    # -----------------------------------------------------
    # 2. SAVE FILE
    # -----------------------------------------------------

    unique_filename = (
        f"{uuid.uuid4().hex}.pdf"
    )

    stored_path = (
        UPLOAD_DIR
        / unique_filename
    )

    with open(
        stored_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # -----------------------------------------------------
    # 3. SHA-256 DUPLICATE CONTROL
    # -----------------------------------------------------

    file_hash = calculate_sha256(
        stored_path
    )

    existing_sds = db.scalar(
        select(
            SDSDocument
        ).where(
            SDSDocument.file_hash
            == file_hash
        )
    )

    if existing_sds:

        stored_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=409,
            detail={
                "message":
                    "Bu doküman daha önce sisteme yüklenmiş.",

                "existing_sds_id":
                    existing_sds.id
            }
        )

    # -----------------------------------------------------
    # 4. PDF TEXT
    # -----------------------------------------------------

    try:

        extracted_text = extract_pdf_text(
            stored_path
        )

    except Exception as exc:

        stored_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "PDF metni okunamadı.",

                "error":
                    str(exc)
            }
        )

    if not extracted_text.strip():

        stored_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "PDF dosyasından metin çıkarılamadı."
            )
        )

    # -----------------------------------------------------
    # 5. UNIVERSAL SDS INGESTION
    # -----------------------------------------------------

    try:

        ingestion = ingest_sds_text(
            text=extracted_text,
            original_filename=original_filename
        )

    except Exception as exc:

        stored_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Universal SDS ingestion sırasında hata oluştu.",

                "error":
                    str(exc)
            }
        )

    # -----------------------------------------------------
    # 6. SDS CONFIDENCE CONTROL
    # -----------------------------------------------------

    if not ingestion.get(
        "is_probable_sds"
    ):

        stored_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Doküman güvenilir biçimde SDS/GBF olarak tanınamadı.",

                "sds_confidence":
                    ingestion.get(
                        "sds_confidence"
                    ),

                "classification_evidence":
                    ingestion.get(
                        "classification_evidence"
                    )
            }
        )

    # -----------------------------------------------------
    # 7. INGESTION DATA
    # -----------------------------------------------------

    sections = (
        ingestion.get(
            "sections"
        )
        or {}
    )

    section_count = (
        ingestion.get(
            "section_count"
        )
        or len(sections)
    )

    parsed_data = (
        ingestion.get(
            "parsed_data"
        )
        or {}
    )

    revision_data = (
        ingestion.get(
            "revision_data"
        )
        or {}
    )

    section_7_data = (
        ingestion.get(
            "section_7_data"
        )
        or {}
    )

    section_8_data = (
        ingestion.get(
            "section_8_data"
        )
        or {}
    )

    section_9_data = (
        ingestion.get(
            "section_9_data"
        )
        or {}
    )

    needs_review = bool(
        ingestion.get(
            "needs_review"
        )
    )

    review_reasons = list(
        ingestion.get(
            "review_reasons"
        )
        or []
    )

    # -----------------------------------------------------
    # 8. PRODUCT DATA
    # -----------------------------------------------------

    product_name = parsed_data.get(
        "product_name"
    )

    manufacturer = parsed_data.get(
        "manufacturer"
    )

    product_code = parsed_data.get(
        "product_code"
    )

    # -----------------------------------------------------
    # 9. FINAL PRODUCT NAME FALLBACK
    # -----------------------------------------------------

    if not product_name:

        product_name = Path(
            original_filename
        ).stem

        parsed_data[
            "product_name"
        ] = product_name

        parsed_data[
            "product_name_source"
        ] = "filename_fallback"

        needs_review = True

        if (
            "product_name_from_filename"
            not in review_reasons
        ):

            review_reasons.append(
                "product_name_from_filename"
            )

    # -----------------------------------------------------
    # 10. CHEMICAL MATCHING
    # -----------------------------------------------------

    chemical = find_existing_chemical(
        db=db,
        parsed_data=parsed_data
    )

    chemical_created = False

    # -----------------------------------------------------
    # 11. CREATE CHEMICAL
    # -----------------------------------------------------

    if chemical is None:

        chemical = Chemical(

            product_name=
                product_name,

            manufacturer=
                manufacturer,

            internal_code=
                product_code,

            description=(
                "SDS universal ingestion sırasında "
                "otomatik oluşturuldu."
            )
        )

        db.add(
            chemical
        )

        db.flush()

        chemical_created = True

    # -----------------------------------------------------
    # 12. SAVE IDENTIFIERS
    # -----------------------------------------------------

    save_chemical_identifiers(
        db=db,
        chemical=chemical,
        parsed_data=parsed_data
    )

    # -----------------------------------------------------
    # 13. DETERMINE CURRENT SDS
    # -----------------------------------------------------

    is_current = determine_is_current(

        db=db,

        chemical_id=
            chemical.id,

        new_revision_date=
            revision_data.get(
                "revision_date"
            ),

        new_preparation_date=
            revision_data.get(
                "preparation_date"
            ),

        new_version=
            revision_data.get(
                "version"
            )
    )

    # -----------------------------------------------------
    # 14. CREATE SDS DOCUMENT
    # -----------------------------------------------------

    sds_document = SDSDocument(

        chemical_id=
            chemical.id,

        original_filename=
            original_filename,

        stored_filename=
            unique_filename,

        file_hash=
            file_hash,

        preparation_date=
            revision_data.get(
                "preparation_date"
            ),

        revision_date=
            revision_data.get(
                "revision_date"
            ),

        version=
            revision_data.get(
                "version"
            ),

        is_current=
            is_current,

        processing_status=
            "processing"
    )

    db.add(
        sds_document
    )

    db.flush()

    # -----------------------------------------------------
    # 15. H / P / GHS
    # -----------------------------------------------------

    save_sds_hazard_data(
        db=db,
        sds_document=sds_document,
        parsed_data=parsed_data
    )

    # -----------------------------------------------------
    # 16. SECTION 7
    # -----------------------------------------------------

    if section_7_data:

        save_storage_info(
            db=db,
            sds_document=sds_document,
            section_7_data=section_7_data
        )

    # -----------------------------------------------------
    # 17. SECTION 8
    # -----------------------------------------------------

    if section_8_data:

        save_ppe_info(
            db=db,
            sds_document=sds_document,
            section_8_data=section_8_data
        )

    # -----------------------------------------------------
    # 18. SECTION 9
    # -----------------------------------------------------

    if section_9_data:

        save_physical_properties(
            db=db,
            sds_document=sds_document,
            section_9_data=section_9_data
        )

    # -----------------------------------------------------
    # 19. RAW SDS SECTIONS
    # -----------------------------------------------------

    for (
        section_number,
        section_content
    ) in sections.items():

        db.add(
            SDSSection(

                sds_document_id=
                    sds_document.id,

                section_number=
                    section_number,

                section_title=
                    None,

                content=
                    section_content
            )
        )

    # -----------------------------------------------------
    # 20. PROCESSING STATUS
    # -----------------------------------------------------

    if needs_review:

        sds_document.processing_status = (
            "needs_review"
        )

    elif section_count >= 14:

        sds_document.processing_status = (
            "sections_extracted"
        )

    else:

        sds_document.processing_status = (
            "sections_incomplete"
        )

    # -----------------------------------------------------
    # 21. COMMIT
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(
            chemical
        )

        db.refresh(
            sds_document
        )

    except Exception as exc:

        db.rollback()

        stored_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Veritabanına kayıt sırasında hata oluştu.",

                "error":
                    str(exc)
            }
        )

    # -----------------------------------------------------
    # 22. RESPONSE
    # -----------------------------------------------------

    return {

        "message":
            "SDS universal ingestion ile başarıyla işlendi.",

        "ingestion": {

            "is_probable_sds":
                ingestion.get(
                    "is_probable_sds"
                ),

            "sds_confidence":
                ingestion.get(
                    "sds_confidence"
                ),

            "classification_evidence":
                ingestion.get(
                    "classification_evidence"
                ),

            "legacy_document_type":
                ingestion.get(
                    "legacy_document_type"
                ),

            "needs_review":
                needs_review,

            "review_reasons":
                review_reasons
        },

        "chemical": {

            "id":
                chemical.id,

            "created_automatically":
                chemical_created,

            "product_name":
                chemical.product_name,

            "manufacturer":
                chemical.manufacturer,

            "internal_code":
                chemical.internal_code
        },

        "parsed_data":
            parsed_data,

        "storage_info":
            section_7_data,

        "ppe_info":
            section_8_data,

        "physical_properties":
            section_9_data,

        "sds": {

            "id":
                sds_document.id,

            "original_filename":
                sds_document.original_filename,

            "stored_filename":
                sds_document.stored_filename,

            "file_hash":
                sds_document.file_hash,

            "preparation_date": (
                sds_document.preparation_date.isoformat()
                if sds_document.preparation_date
                else None
            ),

            "revision_date": (
                sds_document.revision_date.isoformat()
                if sds_document.revision_date
                else None
            ),

            "version":
                sds_document.version,

            "is_current":
                sds_document.is_current,

            "processing_status":
                sds_document.processing_status,

            "section_count":
                section_count,

            "section_numbers":
                ingestion.get(
                    "section_numbers"
                ),

            "needs_review":
                needs_review,

            "review_reasons":
                review_reasons,

            "sds_confidence":
                ingestion.get(
                    "sds_confidence"
                ),

            "hazard_statement_count":
                len(
                    parsed_data.get(
                        "hazard_codes"
                    )
                    or []
                ),

            "precautionary_statement_count":
                len(
                    parsed_data.get(
                        "precautionary_codes"
                    )
                    or []
                ),

            "ghs_pictogram_count":
                len(
                    parsed_data.get(
                        "ghs_codes"
                    )
                    or []
                ),

            "section_7_saved":
                bool(
                    section_7_data
                ),

            "section_8_saved":
                bool(
                    section_8_data
                ),

            "section_9_saved":
                bool(
                    section_9_data
                ),

            "character_count":
                len(
                    extracted_text
                )
        }
    }


# =========================================================
# SDS DETAILS
# =========================================================

@router.get("/{sds_id}/sections")
def get_sds_sections(
    sds_id: int,
    db: Session = Depends(get_db)
):

    sds_document = db.get(
        SDSDocument,
        sds_id
    )

    if sds_document is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "SDS dokümanı bulunamadı."
            )
        )

    # -----------------------------------------------------
    # SECTIONS
    # -----------------------------------------------------

    sections = db.scalars(
        select(
            SDSSection
        )
        .where(
            SDSSection.sds_document_id
            == sds_id
        )
        .order_by(
            SDSSection.section_number
        )
    ).all()

    # -----------------------------------------------------
    # H
    # -----------------------------------------------------

    hazards = db.scalars(
        select(
            HazardStatement
        )
        .where(
            HazardStatement.sds_document_id
            == sds_id
        )
        .order_by(
            HazardStatement.code
        )
    ).all()

    # -----------------------------------------------------
    # P
    # -----------------------------------------------------

    precautions = db.scalars(
        select(
            PrecautionaryStatement
        )
        .where(
            PrecautionaryStatement.sds_document_id
            == sds_id
        )
        .order_by(
            PrecautionaryStatement.code
        )
    ).all()

    # -----------------------------------------------------
    # GHS
    # -----------------------------------------------------

    ghs_pictograms = db.scalars(
        select(
            GHSPictogram
        )
        .where(
            GHSPictogram.sds_document_id
            == sds_id
        )
        .order_by(
            GHSPictogram.code
        )
    ).all()

    # -----------------------------------------------------
    # SECTION 7
    # -----------------------------------------------------

    storage_info = db.scalar(
        select(
            SDSStorageInfo
        ).where(
            SDSStorageInfo.sds_document_id
            == sds_id
        )
    )

    # -----------------------------------------------------
    # SECTION 8
    # -----------------------------------------------------

    ppe_info = db.scalar(
        select(
            SDSPPEInfo
        ).where(
            SDSPPEInfo.sds_document_id
            == sds_id
        )
    )

    # -----------------------------------------------------
    # SECTION 9
    # -----------------------------------------------------

    physical = db.scalar(
        select(
            SDSPhysicalProperties
        ).where(
            SDSPhysicalProperties.sds_document_id
            == sds_id
        )
    )

    return {

        "sds_id":
            sds_document.id,

        "chemical_id":
            sds_document.chemical_id,

        "original_filename":
            sds_document.original_filename,

        "preparation_date": (
            sds_document.preparation_date.isoformat()
            if sds_document.preparation_date
            else None
        ),

        "revision_date": (
            sds_document.revision_date.isoformat()
            if sds_document.revision_date
            else None
        ),

        "version":
            sds_document.version,

        "is_current":
            sds_document.is_current,

        "processing_status":
            sds_document.processing_status,

        "hazard_codes": [
            item.code
            for item in hazards
        ],

        "precautionary_codes": [
            item.code
            for item in precautions
        ],

        "ghs_codes": [
            item.code
            for item in ghs_pictograms
        ],

        "storage_info": (
            {
                "handling_precautions":
                    storage_info.handling_precautions,

                "storage_conditions":
                    storage_info.storage_conditions,

                "incompatible_materials":
                    storage_info.incompatible_materials,

                "fire_explosion_precautions":
                    storage_info.fire_explosion_precautions,

                "specific_end_use":
                    storage_info.specific_end_use,
            }
            if storage_info
            else None
        ),

        "ppe_info": (
            {
                "respiratory_protection":
                    ppe_info.respiratory_protection,

                "hand_protection":
                    ppe_info.hand_protection,

                "glove_materials":
                    ppe_info.glove_materials,

                "glove_thickness":
                    ppe_info.glove_thickness,

                "eye_face_protection":
                    ppe_info.eye_face_protection,

                "body_protection":
                    ppe_info.body_protection,

                "engineering_controls":
                    ppe_info.engineering_controls,

                "exposure_limits":
                    ppe_info.exposure_limits,

                "dnel":
                    ppe_info.dnel,

                "pnec":
                    ppe_info.pnec,

                "hygiene_measures":
                    ppe_info.hygiene_measures,
            }
            if ppe_info
            else None
        ),

        "physical_properties": (
            {
                "physical_state":
                    physical.physical_state,

                "color":
                    physical.color,

                "odor":
                    physical.odor,

                "ph":
                    physical.ph,

                "flash_point":
                    physical.flash_point,

                "boiling_point":
                    physical.boiling_point,

                "melting_freezing_point":
                    physical.melting_freezing_point,

                "density":
                    physical.density,

                "viscosity":
                    physical.viscosity,

                "solubility":
                    physical.solubility,

                "vapour_pressure":
                    physical.vapour_pressure,

                "flammability":
                    physical.flammability,

                "explosive_properties":
                    physical.explosive_properties,

                "oxidising_properties":
                    physical.oxidising_properties,

                "lower_explosion_limit":
                    physical.lower_explosion_limit,

                "upper_explosion_limit":
                    physical.upper_explosion_limit,
            }
            if physical
            else None
        ),

        "section_count":
            len(
                sections
            ),

        "sections": [

            {
                "section_number":
                    section.section_number,

                "section_title":
                    section.section_title,

                "content":
                    section.content
            }

            for section in sections
        ]
    }
    # =========================================================
# SDS REPROCESS PREVIEW
# =========================================================


@router.post("/{sds_id}/reprocess-preview")
def reprocess_sds_preview(
    sds_id: int,
    db: Session = Depends(get_db)
):
    """
    Mevcut bir SDS dosyasını güncel parser ile yeniden analiz eder.

    Bu endpoint yalnızca önizleme yapar.
    Veritabanında hiçbir kayıt değiştirilmez veya silinmez.
    """

    # -----------------------------------------------------
    # 1. SDS DOCUMENT
    # -----------------------------------------------------

    sds_document = db.get(
        SDSDocument,
        sds_id
    )

    if sds_document is None:
        raise HTTPException(
            status_code=404,
            detail="SDS dokümanı bulunamadı."
        )

    # -----------------------------------------------------
    # 2. STORED PDF
    # -----------------------------------------------------

    if not sds_document.stored_filename:
        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "SDS kaydında stored_filename bulunamadı.",
                "sds_id":
                    sds_document.id
            }
        )

    stored_path = (
        UPLOAD_DIR
        / sds_document.stored_filename
    )

    if not stored_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    "SDS PDF dosyası uploads klasöründe bulunamadı.",
                "sds_id":
                    sds_document.id,
                "stored_filename":
                    sds_document.stored_filename
            }
        )

    # -----------------------------------------------------
    # 3. PDF TEXT
    # -----------------------------------------------------

    try:

        extracted_text = extract_pdf_text(
            stored_path
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Mevcut SDS PDF dosyasından metin çıkarılamadı.",
                "error":
                    str(exc)
            }
        )

    if not extracted_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Mevcut SDS PDF dosyasından metin çıkarılamadı."
            )
        )

    # -----------------------------------------------------
    # 4. UNIVERSAL INGESTION
    # -----------------------------------------------------

    try:

        ingestion = ingest_sds_text(
            text=extracted_text,
            original_filename=
                sds_document.original_filename
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "SDS yeniden analiz edilirken hata oluştu.",
                "error":
                    str(exc)
            }
        )

    # -----------------------------------------------------
    # 5. PARSED DATA
    # -----------------------------------------------------

    parsed_data = (
        ingestion.get("parsed_data")
        or {}
    )

    revision_data = (
        ingestion.get("revision_data")
        or {}
    )

    sections = (
        ingestion.get("sections")
        or {}
    )

    section_7_data = (
        ingestion.get("section_7_data")
        or {}
    )

    section_8_data = (
        ingestion.get("section_8_data")
        or {}
    )

    section_9_data = (
        ingestion.get("section_9_data")
        or {}
    )

    # -----------------------------------------------------
    # 6. CURRENT CHEMICAL
    # -----------------------------------------------------

    chemical = db.get(
        Chemical,
        sds_document.chemical_id
    )

    # -----------------------------------------------------
    # 7. PREVIEW RESPONSE
    # -----------------------------------------------------

    return {

        "message":
            "SDS yeniden analiz önizlemesi oluşturuldu. "
            "Veritabanında hiçbir değişiklik yapılmadı.",

        "database_changed":
            False,

        "current_record": {

            "chemical": {

                "id":
                    chemical.id
                    if chemical
                    else None,

                "product_name":
                    chemical.product_name
                    if chemical
                    else None,

                "manufacturer":
                    chemical.manufacturer
                    if chemical
                    else None,

                "internal_code":
                    chemical.internal_code
                    if chemical
                    else None
            },

            "sds": {

                "id":
                    sds_document.id,

                "original_filename":
                    sds_document.original_filename,

                "stored_filename":
                    sds_document.stored_filename,

                "preparation_date": (
                    sds_document.preparation_date.isoformat()
                    if sds_document.preparation_date
                    else None
                ),

                "revision_date": (
                    sds_document.revision_date.isoformat()
                    if sds_document.revision_date
                    else None
                ),

                "version":
                    sds_document.version,

                "processing_status":
                    sds_document.processing_status,

                "is_current":
                    sds_document.is_current
            }
        },

        "preview": {

            "is_probable_sds":
                ingestion.get(
                    "is_probable_sds"
                ),

            "sds_confidence":
                ingestion.get(
                    "sds_confidence"
                ),

            "needs_review":
                ingestion.get(
                    "needs_review"
                ),

            "review_reasons":
                ingestion.get(
                    "review_reasons"
                )
                or [],

            "section_count":
                ingestion.get(
                    "section_count"
                )
                or len(sections),

            "section_numbers":
                ingestion.get(
                    "section_numbers"
                )
                or sorted(
                    sections.keys()
                ),

            "product_name":
                parsed_data.get(
                    "product_name"
                ),

            "manufacturer":
                parsed_data.get(
                    "manufacturer"
                ),

            "product_code":
                parsed_data.get(
                    "product_code"
                ),

            "ufi":
                parsed_data.get(
                    "ufi"
                ),

            "cas_numbers":
                parsed_data.get(
                    "cas_numbers"
                )
                or [],

            "component_cas_numbers":
                parsed_data.get(
                    "component_cas_numbers"
                )
                or [],

            "ec_number":
                parsed_data.get(
                    "ec_number"
                ),

            "reach_number":
                parsed_data.get(
                    "reach_number"
                ),

            "hazard_codes":
                parsed_data.get(
                    "hazard_codes"
                )
                or [],

            "precautionary_codes":
                parsed_data.get(
                    "precautionary_codes"
                )
                or [],

            "ghs_codes":
                parsed_data.get(
                    "ghs_codes"
                )
                or [],

            "revision_data":
                revision_data,

            "storage_info":
                section_7_data,

            "ppe_info":
                section_8_data,

            "physical_properties":
                section_9_data
        }
    }
    # =========================================================
# SDS REAL REPROCESS
# =========================================================


def _coerce_reprocess_date(
    value
):
    """
    Revision parser ISO tarih string'i döndürüyorsa
    SQLAlchemy Date kolonu için Python date nesnesine
    dönüştürür.
    """

    from datetime import date as date_type

    if value is None:
        return None

    if isinstance(
        value,
        date_type
    ):
        return value

    if isinstance(
        value,
        str
    ):

        value = value.strip()

        if not value:
            return None

        try:

            return date_type.fromisoformat(
                value[:10]
            )

        except ValueError:

            return None

    return None


def _split_reprocess_ufi_values(
    value
) -> set[str]:

    """
    Tek veya birden fazla UFI değerini
    karşılaştırma için normalize eder.

    Örnek:

        ABCD-...; EFGH-...
    """

    if not value:
        return set()

    if isinstance(
        value,
        (list, tuple, set)
    ):

        raw_values = value

    else:

        raw_values = str(
            value
        ).split(";")

    result = set()

    for raw_value in raw_values:

        raw_value = str(
            raw_value
        ).strip().upper()

        if raw_value:

            result.add(
                raw_value
            )

    return result


def _delete_sds_derived_records_for_reprocess(
    db: Session,
    sds_id: int
):
    """
    Sadece belirtilen SDS dokümanına ait parser-türevi
    kayıtları siler.

    SDSDocument'ın kendisine,
    PDF dosyasına veya chemical kaydına dokunmaz.

    Silme + yeniden oluşturma aynı transaction içinde
    gerçekleştirilecektir.
    """

    models_to_clear = (

        HazardStatement,

        PrecautionaryStatement,

        GHSPictogram,

        SDSStorageInfo,

        SDSPPEInfo,

        SDSPhysicalProperties,

        SDSSection,
    )

    for model in models_to_clear:

        records = db.scalars(
            select(
                model
            ).where(
                model.sds_document_id
                == sds_id
            )
        ).all()

        for record in records:

            db.delete(
                record
            )

    # Eski kayıtlar gerçekten silinmiş olarak
    # işaretlensin. Sonraki save_* fonksiyonları
    # eski kayıtları görmemeli.
    db.flush()


@router.post("/{sds_id}/reprocess")
def reprocess_sds(
    sds_id: int,
    db: Session = Depends(get_db)
):
    """
    Mevcut SDS dokümanını güncel parser ile yeniden işler.

    ÖNEMLİ:

    - Yeni SDSDocument oluşturmaz.
    - SDS ID değişmez.
    - PDF dosyası değişmez.
    - file_hash değişmez.
    - stored_filename değişmez.
    - uploaded_at değişmez.
    - chemical_id otomatik olarak başka kimyasala taşınmaz.

    Yalnızca parser tarafından türetilen veriler
    transaction içinde yeniden oluşturulur.
    """

    # -----------------------------------------------------
    # 1. EXISTING SDS
    # -----------------------------------------------------

    sds_document = db.get(
        SDSDocument,
        sds_id
    )

    if sds_document is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "SDS dokümanı bulunamadı."
            )
        )

    # -----------------------------------------------------
    # 2. EXISTING CHEMICAL
    # -----------------------------------------------------

    chemical = db.get(
        Chemical,
        sds_document.chemical_id
    )

    if chemical is None:

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "SDS dokümanına bağlı chemical kaydı bulunamadı.",

                "sds_id":
                    sds_document.id,

                "chemical_id":
                    sds_document.chemical_id
            }
        )

    # -----------------------------------------------------
    # 3. STORED PDF
    # -----------------------------------------------------

    if not sds_document.stored_filename:

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "SDS kaydında stored_filename bulunamadı.",

                "sds_id":
                    sds_document.id
            }
        )

    stored_path = (
        UPLOAD_DIR
        / sds_document.stored_filename
    )

    if not stored_path.exists():

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    "SDS PDF dosyası uploads klasöründe bulunamadı.",

                "sds_id":
                    sds_document.id,

                "stored_filename":
                    sds_document.stored_filename
            }
        )

    # -----------------------------------------------------
    # 4. PDF TEXT
    #
    # DB HENÜZ DEĞİŞTİRİLMİYOR.
    # -----------------------------------------------------

    try:

        extracted_text = extract_pdf_text(
            stored_path
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "SDS PDF dosyasından metin çıkarılamadı.",

                "error":
                    str(exc)
            }
        )

    if not extracted_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "SDS PDF dosyasından metin çıkarılamadı."
            )
        )

    # -----------------------------------------------------
    # 5. CURRENT UNIVERSAL PARSER
    #
    # HÂLÂ DB DEĞİŞİKLİĞİ YOK.
    # -----------------------------------------------------

    try:

        ingestion = ingest_sds_text(
            text=extracted_text,
            original_filename=
                sds_document.original_filename
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "SDS yeniden analiz edilirken hata oluştu.",

                "error":
                    str(exc)
            }
        )

    # -----------------------------------------------------
    # 6. SDS VALIDATION
    # -----------------------------------------------------

    if not ingestion.get(
        "is_probable_sds"
    ):

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Yeni parser sonucu dokümanı güvenilir "
                    "biçimde SDS olarak doğrulayamadı. "
                    "Veritabanı değiştirilmedi.",

                "sds_confidence":
                    ingestion.get(
                        "sds_confidence"
                    )
            }
        )

    needs_review = bool(
        ingestion.get(
            "needs_review"
        )
    )

    review_reasons = list(
        ingestion.get(
            "review_reasons"
        )
        or []
    )

    # Gerçek reprocess sırasında şüpheli bir parser
    # çıktısını eski verinin üstüne yazmıyoruz.
    if needs_review:

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Yeni parser sonucu manuel inceleme "
                    "gerektiriyor. Veritabanı değiştirilmedi.",

                "review_reasons":
                    review_reasons
            }
        )

    # -----------------------------------------------------
    # 7. INGESTION DATA
    # -----------------------------------------------------

    sections = (
        ingestion.get(
            "sections"
        )
        or {}
    )

    section_count = (
        ingestion.get(
            "section_count"
        )
        or len(
            sections
        )
    )

    parsed_data = (
        ingestion.get(
            "parsed_data"
        )
        or {}
    )

    revision_data = (
        ingestion.get(
            "revision_data"
        )
        or {}
    )

    section_7_data = (
        ingestion.get(
            "section_7_data"
        )
        or {}
    )

    section_8_data = (
        ingestion.get(
            "section_8_data"
        )
        or {}
    )

    section_9_data = (
        ingestion.get(
            "section_9_data"
        )
        or {}
    )

    # -----------------------------------------------------
    # 8. SECTION SAFETY
    # -----------------------------------------------------

    if section_count < 14:

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Yeni parser yeterli sayıda SDS bölümü "
                    "çıkaramadı. Mevcut kayıt korunuyor.",

                "section_count":
                    section_count,

                "section_numbers":
                    ingestion.get(
                        "section_numbers"
                    )
                    or sorted(
                        sections.keys()
                    )
            }
        )

    # -----------------------------------------------------
    # 9. PRODUCT NAME SAFETY
    # -----------------------------------------------------

    product_name = parsed_data.get(
        "product_name"
    )

    if not product_name:

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Yeni parser ürün adını belirleyemedi. "
                    "Mevcut kayıt korunuyor."
            }
        )

    manufacturer = parsed_data.get(
        "manufacturer"
    )

    product_code = parsed_data.get(
        "product_code"
    )

    # -----------------------------------------------------
    # 10. STRONG IDENTITY CHECK — UFI
    #
    # Reprocess aynı chemical üzerinde kalmalı.
    # Mevcut UFI ile yeni parser UFI'si açıkça
    # çelişiyorsa sessizce güncelleme yapma.
    # -----------------------------------------------------

    existing_ufi_rows = db.scalars(
        select(
            ChemicalIdentifier.identifier_value
        ).where(
            ChemicalIdentifier.chemical_id
            == chemical.id,

            ChemicalIdentifier.identifier_type
            == "UFI"
        )
    ).all()

    existing_ufi_values = set()

    for existing_ufi in existing_ufi_rows:

        existing_ufi_values.update(
            _split_reprocess_ufi_values(
                existing_ufi
            )
        )

    parsed_ufi_values = (
        _split_reprocess_ufi_values(
            parsed_data.get(
                "ufi"
            )
        )
    )

    if (
        existing_ufi_values
        and parsed_ufi_values
        and existing_ufi_values.isdisjoint(
            parsed_ufi_values
        )
    ):

        raise HTTPException(
            status_code=409,
            detail={
                "message":
                    "Yeni parser UFI değeri mevcut chemical "
                    "kimliğiyle uyuşmuyor. Güvenlik nedeniyle "
                    "reprocess durduruldu.",

                "chemical_id":
                    chemical.id,

                "existing_ufi":
                    sorted(
                        existing_ufi_values
                    ),

                "parsed_ufi":
                    sorted(
                        parsed_ufi_values
                    )
            }
        )

    # -----------------------------------------------------
    # 11. DATE VALUES
    # -----------------------------------------------------

    raw_preparation_date = (
        revision_data.get(
            "preparation_date"
        )
    )

    raw_revision_date = (
        revision_data.get(
            "revision_date"
        )
    )

    preparation_date = (
        _coerce_reprocess_date(
            raw_preparation_date
        )
    )

    revision_date = (
        _coerce_reprocess_date(
            raw_revision_date
        )
    )

    if (
        raw_preparation_date
        and preparation_date is None
    ):

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Preparation date güvenli biçimde "
                    "veritabanı tarihine dönüştürülemedi.",

                "value":
                    raw_preparation_date
            }
        )

    if (
        raw_revision_date
        and revision_date is None
    ):

        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Revision date güvenli biçimde "
                    "veritabanı tarihine dönüştürülemedi.",

                "value":
                    raw_revision_date
            }
        )

    version = revision_data.get(
        "version"
    )

    # -----------------------------------------------------
    # 12. OLD SNAPSHOT
    #
    # Response içinde neyin değiştiğini görebilelim.
    # -----------------------------------------------------

    old_snapshot = {

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

        "sds": {

            "id":
                sds_document.id,

            "preparation_date": (
                sds_document.preparation_date.isoformat()
                if sds_document.preparation_date
                else None
            ),

            "revision_date": (
                sds_document.revision_date.isoformat()
                if sds_document.revision_date
                else None
            ),

            "version":
                sds_document.version,

            "processing_status":
                sds_document.processing_status,

            "is_current":
                sds_document.is_current,
        }
    }

    # =====================================================
    # 13. TRANSACTIONAL DATABASE REPROCESS
    #
    # BU NOKTADAN SONRA DB DEĞİŞİKLİĞİ BAŞLIYOR.
    # =====================================================

    try:

        # -------------------------------------------------
        # CHEMICAL MASTER DATA
        #
        # chemical_id kesinlikle değiştirilmiyor.
        # Yalnızca güvenilir yeni değerler güncelleniyor.
        # -------------------------------------------------

        chemical.product_name = (
            product_name
        )

        if manufacturer:

            chemical.manufacturer = (
                manufacturer
            )

        if product_code:

            chemical.internal_code = (
                product_code
            )

        # -------------------------------------------------
        # IDENTIFIERS
        #
        # Chemical-level identifier geçmişini silmiyoruz.
        # Yalnızca yeni doğrulanmış identifier'ları ekliyoruz.
        #
        # UFI'ları ayrı ayrı kaydetmek için mevcut helper'a
        # UFI göndermiyoruz.
        # -------------------------------------------------

        identifier_data = dict(
            parsed_data
        )

        identifier_data[
            "ufi"
        ] = None

        save_chemical_identifiers(
            db=db,
            chemical=chemical,
            parsed_data=identifier_data
        )

        for ufi_value in sorted(
            parsed_ufi_values
        ):

            existing_identifier = db.scalar(
                select(
                    ChemicalIdentifier
                ).where(
                    ChemicalIdentifier.chemical_id
                    == chemical.id,

                    ChemicalIdentifier.identifier_type
                    == "UFI",

                    ChemicalIdentifier.identifier_value
                    == ufi_value
                )
            )

            if not existing_identifier:

                db.add(
                    ChemicalIdentifier(
                        chemical_id=
                            chemical.id,

                        identifier_type=
                            "UFI",

                        identifier_value=
                            ufi_value
                    )
                )

        # -------------------------------------------------
        # SDS MASTER DATA
        #
        # ID / file_hash / stored_filename / uploaded_at
        # korunuyor.
        # -------------------------------------------------

        sds_document.preparation_date = (
            preparation_date
        )

        sds_document.revision_date = (
            revision_date
        )

        sds_document.version = (
            version
        )

        # is_current değerini koruyoruz.
        #
        # Reprocess mevcut revision kaydını yeniden
        # yorumlamaktır; yeni revision oluşturmak değildir.

        # -------------------------------------------------
        # DELETE OLD PARSER-DERIVED DATA
        # -------------------------------------------------

        _delete_sds_derived_records_for_reprocess(
            db=db,
            sds_id=sds_document.id
        )

        # -------------------------------------------------
        # H / P / GHS
        # -------------------------------------------------

        save_sds_hazard_data(
            db=db,
            sds_document=sds_document,
            parsed_data=parsed_data
        )

        # -------------------------------------------------
        # SECTION 7
        # -------------------------------------------------

        if section_7_data:

            save_storage_info(
                db=db,
                sds_document=sds_document,
                section_7_data=
                    section_7_data
            )

        # -------------------------------------------------
        # SECTION 8
        # -------------------------------------------------

        if section_8_data:

            save_ppe_info(
                db=db,
                sds_document=sds_document,
                section_8_data=
                    section_8_data
            )

        # -------------------------------------------------
        # SECTION 9
        # -------------------------------------------------

        if section_9_data:

            save_physical_properties(
                db=db,
                sds_document=sds_document,
                section_9_data=
                    section_9_data
            )

        # -------------------------------------------------
        # RAW SDS SECTIONS
        # -------------------------------------------------

        for (
            section_number,
            section_content
        ) in sections.items():

            db.add(
                SDSSection(
                    sds_document_id=
                        sds_document.id,

                    section_number=
                        section_number,

                    section_title=
                        None,

                    content=
                        section_content
                )
            )

        # -------------------------------------------------
        # PROCESSING STATUS
        # -------------------------------------------------

        if needs_review:

            sds_document.processing_status = (
                "needs_review"
            )

        elif section_count >= 14:

            sds_document.processing_status = (
                "sections_extracted"
            )

        else:

            sds_document.processing_status = (
                "sections_incomplete"
            )

        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        db.commit()

        db.refresh(
            chemical
        )

        db.refresh(
            sds_document
        )

    except Exception as exc:

        # Tek transaction olduğu için:
        #
        # - eski H/P/GHS
        # - eski sections
        # - eski Section 7/8/9
        # - eski chemical metadata
        # - eski SDS revision metadata
        #
        # rollback ile korunur.

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "SDS reprocess sırasında veritabanı "
                    "güncellenemedi. Transaction geri alındı.",

                "error":
                    str(exc)
            }
        )

    # -----------------------------------------------------
    # 14. RESPONSE
    # -----------------------------------------------------

    return {

        "message":
            "SDS mevcut kayıt üzerinde başarıyla "
            "yeniden işlendi.",

        "database_changed":
            True,

        "sds_id":
            sds_document.id,

        "chemical_id":
            chemical.id,

        "old_record":
            old_snapshot,

        "updated_record": {

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

            "sds": {

                "id":
                    sds_document.id,

                "original_filename":
                    sds_document.original_filename,

                "stored_filename":
                    sds_document.stored_filename,

                "preparation_date": (
                    sds_document.preparation_date.isoformat()
                    if sds_document.preparation_date
                    else None
                ),

                "revision_date": (
                    sds_document.revision_date.isoformat()
                    if sds_document.revision_date
                    else None
                ),

                "version":
                    sds_document.version,

                "processing_status":
                    sds_document.processing_status,

                "is_current":
                    sds_document.is_current,
            }
        },

        "parser_result": {

            "section_count":
                section_count,

            "section_numbers":
                ingestion.get(
                    "section_numbers"
                )
                or sorted(
                    sections.keys()
                ),

            "sds_confidence":
                ingestion.get(
                    "sds_confidence"
                ),

            "hazard_codes":
                parsed_data.get(
                    "hazard_codes"
                )
                or [],

            "precautionary_codes":
                parsed_data.get(
                    "precautionary_codes"
                )
                or [],

            "ghs_codes":
                parsed_data.get(
                    "ghs_codes"
                )
                or [],
        }
    }