import argparse
from pathlib import Path

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import (
    Chemical,
    ChemicalIdentifier,
    SDSDocument,
    HazardStatement,
    PrecautionaryStatement,
    GHSPictogram,
)

from app.services.document_classifier import classify_document
from app.services.pdf_reader import extract_pdf_text
from app.services.section_splitter import split_sds_sections
from app.services.sds_parser import parse_section_1
from app.services.section_2_parser import parse_section_2
from app.services.section_3_parser import parse_section_3
from app.services.revision_parser import parse_revision_metadata


UPLOAD_DIR = Path("uploads")


# =========================================================
# HELPERS
# =========================================================

def normalize_list(values):
    if not values:
        return []

    return sorted(
        list(
            dict.fromkeys(
                str(value).strip()
                for value in values
                if value is not None
                and str(value).strip()
            )
        )
    )


def safe_string(value):
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


# =========================================================
# DATABASE READ HELPERS
# =========================================================

def get_identifiers(
    db,
    chemical_id: int,
    identifier_type: str
) -> list[str]:

    statement = (
        select(ChemicalIdentifier)
        .where(
            ChemicalIdentifier.chemical_id == chemical_id,
            ChemicalIdentifier.identifier_type == identifier_type
        )
    )

    records = db.scalars(
        statement
    ).all()

    return normalize_list(
        record.identifier_value
        for record in records
    )


def get_hazard_codes(
    db,
    sds_id: int
) -> list[str]:

    records = db.scalars(
        select(HazardStatement)
        .where(
            HazardStatement.sds_document_id == sds_id
        )
    ).all()

    return normalize_list(
        record.code
        for record in records
    )


def get_precautionary_codes(
    db,
    sds_id: int
) -> list[str]:

    records = db.scalars(
        select(PrecautionaryStatement)
        .where(
            PrecautionaryStatement.sds_document_id == sds_id
        )
    ).all()

    return normalize_list(
        record.code
        for record in records
    )


def get_ghs_codes(
    db,
    sds_id: int
) -> list[str]:

    records = db.scalars(
        select(GHSPictogram)
        .where(
            GHSPictogram.sds_document_id == sds_id
        )
    ).all()

    return normalize_list(
        record.code
        for record in records
    )


# =========================================================
# PARSER
# =========================================================

def parse_existing_sds(
    file_path: Path
) -> dict:

    text = extract_pdf_text(
        file_path
    )

    document_type = classify_document(
        text
    )

    sections = split_sds_sections(
        text
    )

    section_1_data = {}
    section_2_data = {}
    section_3_data = {}

    if 1 in sections:

        section_1_data = parse_section_1(
            sections[1]
        )

    if 2 in sections:

        section_2_data = parse_section_2(
            sections[2]
        )

    if 3 in sections:

        section_3_data = parse_section_3(
            sections[3]
        )

    revision_data = parse_revision_metadata(
        text
    )

    # -----------------------------------------------------
    # CAS
    # -----------------------------------------------------

    cas_numbers = (
        section_1_data.get(
            "cas_numbers"
        )
        or []
    )

    if not cas_numbers:

        cas_numbers = (
            section_3_data.get(
                "cas_numbers"
            )
            or []
        )

    # -----------------------------------------------------
    # EC
    # -----------------------------------------------------

    ec_number = section_1_data.get(
        "ec_number"
    )

    if not ec_number:

        ec_number = section_3_data.get(
            "ec_number"
        )

    # -----------------------------------------------------
    # REACH
    # -----------------------------------------------------

    reach_number = section_1_data.get(
        "reach_number"
    )

    if not reach_number:

        reach_number = section_3_data.get(
            "reach_number"
        )

    return {

        "document_type":
            document_type,

        "product_name":
            section_1_data.get(
                "product_name"
            ),

        "manufacturer":
            section_1_data.get(
                "manufacturer"
            ),

        "cas_numbers":
            normalize_list(
                cas_numbers
            ),

        "ec_number":
            safe_string(
                ec_number
            ),

        "reach_number":
            safe_string(
                reach_number
            ),

        "ufi":
            safe_string(
                section_1_data.get(
                    "ufi"
                )
            ),

        "product_code":
            safe_string(
                section_1_data.get(
                    "product_code"
                )
            ),

        "component_names":
            section_3_data.get(
                "component_names"
            )
            or [],

        "hazard_codes":
            normalize_list(
                section_2_data.get(
                    "hazard_codes"
                )
                or []
            ),

        "precautionary_codes":
            normalize_list(
                section_2_data.get(
                    "precautionary_codes"
                )
                or []
            ),

        "signal_word":
            safe_string(
                section_2_data.get(
                    "signal_word"
                )
            ),

        "ghs_codes":
            normalize_list(
                section_2_data.get(
                    "ghs_codes"
                )
                or []
            ),

        "preparation_date":
            revision_data.get(
                "preparation_date"
            ),

        "revision_date":
            revision_data.get(
                "revision_date"
            ),

        "version":
            safe_string(
                revision_data.get(
                    "version"
                )
            ),

        "supersedes_date":
            revision_data.get(
                "supersedes_date"
            ),

        "section_count":
            len(
                sections
            ),

        "sections":
            sorted(
                sections.keys()
            ),

        "character_count":
            len(
                text
            )
    }


# =========================================================
# SAFE IDENTIFIER INSERT
# =========================================================

def safe_add_identifier(
    db,
    chemical_id: int,
    identifier_type: str,
    identifier_value: str,
    apply_changes: bool
) -> str:

    identifier_value = safe_string(
        identifier_value
    )

    if not identifier_value:

        return "EMPTY"

    # Sadece aynı Chemical içinde duplicate kontrol edilir.
    #
    # Aynı CAS / EC / REACH başka Chemical kayıtlarında
    # bulunabilir.

    existing = db.scalar(
        select(
            ChemicalIdentifier
        )
        .where(
            ChemicalIdentifier.chemical_id
            == chemical_id,

            ChemicalIdentifier.identifier_type
            == identifier_type,

            ChemicalIdentifier.identifier_value
            == identifier_value
        )
    )

    if existing:

        return "EXISTS"

    if apply_changes:

        db.add(
            ChemicalIdentifier(
                chemical_id=
                    chemical_id,

                identifier_type=
                    identifier_type,

                identifier_value=
                    identifier_value
            )
        )

    return "ADD"


# =========================================================
# H CODES
# =========================================================

def safe_add_hazard_codes(
    db,
    sds_id: int,
    codes: list[str],
    apply_changes: bool
) -> int:

    added = 0

    existing_codes = set(
        get_hazard_codes(
            db,
            sds_id
        )
    )

    for code in codes:

        if code in existing_codes:

            continue

        if apply_changes:

            db.add(
                HazardStatement(
                    sds_document_id=
                        sds_id,

                    code=
                        code,

                    statement_text=
                        None
                )
            )

        added += 1

    return added


# =========================================================
# P CODES
# =========================================================

def safe_add_precautionary_codes(
    db,
    sds_id: int,
    codes: list[str],
    apply_changes: bool
) -> int:

    added = 0

    existing_codes = set(
        get_precautionary_codes(
            db,
            sds_id
        )
    )

    for code in codes:

        if code in existing_codes:

            continue

        if apply_changes:

            db.add(
                PrecautionaryStatement(
                    sds_document_id=
                        sds_id,

                    code=
                        code,

                    statement_text=
                        None
                )
            )

        added += 1

    return added


# =========================================================
# GHS CODES
# =========================================================

def safe_add_ghs_codes(
    db,
    sds_id: int,
    codes: list[str],
    apply_changes: bool
) -> int:

    added = 0

    existing_codes = set(
        get_ghs_codes(
            db,
            sds_id
        )
    )

    for code in codes:

        if code in existing_codes:

            continue

        if apply_changes:

            db.add(
                GHSPictogram(
                    sds_document_id=
                        sds_id,

                    code=
                        code
                )
            )

        added += 1

    return added


# =========================================================
# SAFE UPDATE
# =========================================================

def process_sds(
    db,
    sds: SDSDocument,
    apply_changes: bool
):

    print()
    print("=" * 90)

    print(
        f"SDS ID: {sds.id}"
    )

    print(
        f"Dosya: {sds.original_filename}"
    )

    file_path = (
        UPLOAD_DIR
        / sds.stored_filename
    )

    # -----------------------------------------------------
    # FILE EXISTS?
    # -----------------------------------------------------

    if not file_path.exists():

        print(
            "❌ PDF dosyası bulunamadı."
        )

        return {
            "status":
                "missing_file",

            "changes":
                0
        }

    # -----------------------------------------------------
    # PARSE
    # -----------------------------------------------------

    try:

        parsed = parse_existing_sds(
            file_path
        )

    except Exception as exc:

        print(
            "❌ Parser hatası:"
        )

        print(
            f"   {type(exc).__name__}: "
            f"{exc}"
        )

        return {
            "status":
                "parser_error",

            "changes":
                0
        }

    # -----------------------------------------------------
    # SDS DEĞİLSE ATLAMA
    # -----------------------------------------------------

    if (
        parsed["document_type"]
        != "SDS"
    ):

        print(
            "⏭ SDS değil, atlandı."
        )

        print(
            f"   Document type: "
            f"{parsed['document_type']}"
        )

        return {
            "status":
                "skipped_not_sds",

            "changes":
                0
        }

    # -----------------------------------------------------
    # CHEMICAL
    # -----------------------------------------------------

    chemical = db.get(
        Chemical,
        sds.chemical_id
    )

    if chemical is None:

        print(
            "❌ Chemical kaydı bulunamadı."
        )

        return {
            "status":
                "missing_chemical",

            "changes":
                0
        }

    changes = 0

    print(
        f"Chemical ID: "
        f"{chemical.id}"
    )

    print(
        f"Ürün: "
        f"{chemical.product_name}"
    )

    print(
        f"Parser ürün: "
        f"{parsed['product_name']}"
    )

    print(
        f"Bölüm sayısı: "
        f"{parsed['section_count']}"
    )

    # =====================================================
    # PRODUCT NAME
    # =====================================================

    if (
        parsed["product_name"]
        and parsed["product_name"]
        != chemical.product_name
    ):

        print(
            "⚠ Ürün adı farklı ancak "
            "safe-update değiştirmedi:"
        )

        print(
            f"   DB     : "
            f"{chemical.product_name}"
        )

        print(
            f"   Parser : "
            f"{parsed['product_name']}"
        )

    # =====================================================
    # MANUFACTURER
    # =====================================================

    if (
        parsed["manufacturer"]
        and parsed["manufacturer"]
        != chemical.manufacturer
    ):

        print(
            "⚠ Üretici farklı ancak "
            "safe-update değiştirmedi:"
        )

        print(
            f"   DB     : "
            f"{chemical.manufacturer}"
        )

        print(
            f"   Parser : "
            f"{parsed['manufacturer']}"
        )

    # =====================================================
    # PREPARATION DATE
    # =====================================================

    if (
        sds.preparation_date
        is None

        and parsed[
            "preparation_date"
        ]
        is not None
    ):

        print(
            f"+ Hazırlama tarihi: "
            f"{parsed['preparation_date']}"
        )

        if apply_changes:

            sds.preparation_date = (
                parsed[
                    "preparation_date"
                ]
            )

        changes += 1

    # =====================================================
    # REVISION DATE
    # =====================================================

    if (
        sds.revision_date
        is None

        and parsed[
            "revision_date"
        ]
        is not None
    ):

        print(
            f"+ Revizyon tarihi: "
            f"{parsed['revision_date']}"
        )

        if apply_changes:

            sds.revision_date = (
                parsed[
                    "revision_date"
                ]
            )

        changes += 1

    # =====================================================
    # VERSION
    # =====================================================

    if (
        not safe_string(
            sds.version
        )

        and parsed[
            "version"
        ]
    ):

        print(
            f"+ Versiyon: "
            f"{parsed['version']}"
        )

        if apply_changes:

            sds.version = (
                parsed[
                    "version"
                ]
            )

        changes += 1

    # =====================================================
    # CAS
    # =====================================================

    for cas_number in (
        parsed[
            "cas_numbers"
        ]
    ):

        result = safe_add_identifier(
            db=db,
            chemical_id=chemical.id,
            identifier_type="CAS",
            identifier_value=cas_number,
            apply_changes=apply_changes
        )

        if result == "ADD":

            print(
                f"+ CAS: "
                f"{cas_number}"
            )

            changes += 1

    # =====================================================
    # EC
    # =====================================================

    if parsed["ec_number"]:

        result = safe_add_identifier(
            db=db,
            chemical_id=chemical.id,
            identifier_type="EC",
            identifier_value=parsed["ec_number"],
            apply_changes=apply_changes
        )

        if result == "ADD":

            print(
                f"+ EC: "
                f"{parsed['ec_number']}"
            )

            changes += 1

    # =====================================================
    # REACH
    # =====================================================

    if parsed["reach_number"]:

        result = safe_add_identifier(
            db=db,
            chemical_id=chemical.id,
            identifier_type="REACH",
            identifier_value=parsed["reach_number"],
            apply_changes=apply_changes
        )

        if result == "ADD":

            print(
                f"+ REACH: "
                f"{parsed['reach_number']}"
            )

            changes += 1

    # =====================================================
    # UFI
    # =====================================================

    if parsed["ufi"]:

        result = safe_add_identifier(
            db=db,
            chemical_id=chemical.id,
            identifier_type="UFI",
            identifier_value=parsed["ufi"],
            apply_changes=apply_changes
        )

        if result == "ADD":

            print(
                f"+ UFI: "
                f"{parsed['ufi']}"
            )

            changes += 1

    # =====================================================
    # H CODES
    # =====================================================

    h_added = safe_add_hazard_codes(
        db=db,
        sds_id=sds.id,
        codes=parsed[
            "hazard_codes"
        ],
        apply_changes=apply_changes
    )

    if h_added:

        print(
            f"+ H kodu: "
            f"{h_added} adet"
        )

        changes += h_added

    # =====================================================
    # P CODES
    # =====================================================

    p_added = (
        safe_add_precautionary_codes(
            db=db,
            sds_id=sds.id,
            codes=parsed[
                "precautionary_codes"
            ],
            apply_changes=apply_changes
        )
    )

    if p_added:

        print(
            f"+ P kodu: "
            f"{p_added} adet"
        )

        changes += p_added

    # =====================================================
    # GHS
    # =====================================================

    ghs_added = safe_add_ghs_codes(
        db=db,
        sds_id=sds.id,
        codes=parsed[
            "ghs_codes"
        ],
        apply_changes=apply_changes
    )

    if ghs_added:

        print(
            f"+ GHS: "
            f"{ghs_added} adet"
        )

        changes += ghs_added

    # =====================================================
    # PROCESSING STATUS
    # =====================================================

    if (
        parsed[
            "section_count"
        ]
        == 16

        and sds.processing_status
        != "sections_extracted"
    ):

        print(
            "+ Processing status: "
            f"{sds.processing_status} "
            "-> sections_extracted"
        )

        if apply_changes:

            sds.processing_status = (
                "sections_extracted"
            )

        changes += 1

    # =====================================================
    # RESULT
    # =====================================================

    if changes == 0:

        print(
            "✓ Güvenli güncelleme gerekmiyor."
        )

    else:

        if apply_changes:

            print(
                f"✅ {changes} güvenli değişiklik "
                f"uygulandı."
            )

        else:

            print(
                f"🔎 {changes} güvenli değişiklik "
                f"uygulanabilir."
            )

    return {
        "status":
            "ok",

        "changes":
            changes
    }


# =========================================================
# RUN
# =========================================================

def run(
    apply_changes: bool
):

    db = SessionLocal()

    try:

        sds_documents = db.scalars(
            select(
                SDSDocument
            )
            .order_by(
                SDSDocument.id
            )
        ).all()

        print()
        print("=" * 90)

        print(
            "GEBKIM SDS BACKFILL / "
            "SAFE UPDATE"
        )

        print("=" * 90)

        if apply_changes:

            print(
                "MOD: SAFE UPDATE"
            )

            print(
                "Güvenli değişiklikler "
                "veritabanına yazılacak."
            )

        else:

            print(
                "MOD: DRY RUN"
            )

            print(
                "Veritabanında hiçbir "
                "değişiklik yapılmayacak."
            )

        print()

        print(
            f"Toplam kayıt: "
            f"{len(sds_documents)}"
        )

        total_changes = 0
        skipped_not_sds = 0
        errors = 0

        for sds in sds_documents:

            result = process_sds(
                db=db,
                sds=sds,
                apply_changes=apply_changes
            )

            total_changes += (
                result[
                    "changes"
                ]
            )

            if (
                result[
                    "status"
                ]
                == "skipped_not_sds"
            ):

                skipped_not_sds += 1

            if result[
                "status"
            ] in {
                "missing_file",
                "parser_error",
                "missing_chemical"
            }:

                errors += 1

        # =================================================
        # COMMIT / ROLLBACK
        # =================================================

        if apply_changes:

            try:

                db.commit()

            except Exception as exc:

                db.rollback()

                print()
                print(
                    "❌ COMMIT HATASI"
                )

                print(
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                raise

        else:

            db.rollback()

        # =================================================
        # SUMMARY
        # =================================================

        print()
        print("=" * 90)
        print("ÖZET")
        print("=" * 90)

        print(
            f"Toplam SDS kaydı: "
            f"{len(sds_documents)}"
        )

        print(
            f"SDS olmadığı için atlanan: "
            f"{skipped_not_sds}"
        )

        print(
            f"Hata sayısı: "
            f"{errors}"
        )

        if apply_changes:

            print(
                f"Uygulanan güvenli değişiklik: "
                f"{total_changes}"
            )

        else:

            print(
                f"Uygulanabilecek güvenli değişiklik: "
                f"{total_changes}"
            )

        print()

        if apply_changes:

            print(
                "✅ SAFE UPDATE tamamlandı."
            )

        else:

            print(
                "🔎 DRY RUN tamamlandı. "
                "Veritabanı değiştirilmedi."
            )

    finally:

        db.close()


# =========================================================
# COMMAND LINE
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "GEBKIM SDS backfill / "
            "safe update aracı"
        )
    )

    mode = (
        parser
        .add_mutually_exclusive_group()
    )

    mode.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Sadece yapılabilecek "
            "değişiklikleri gösterir."
        )
    )

    mode.add_argument(
        "--safe-update",
        action="store_true",
        help=(
            "Yalnızca güvenli eksik "
            "alanları günceller."
        )
    )

    args = parser.parse_args()

    # Argüman verilmezse de dry-run.
    apply_changes = bool(
        args.safe_update
    )

    run(
        apply_changes=
            apply_changes
    )


if __name__ == "__main__":
    main()