import sys
import json
from pathlib import Path
from datetime import date, datetime


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_text(
    pdf_path: Path
) -> str:

    try:
        from pypdf import PdfReader

        reader = PdfReader(
            str(pdf_path)
        )

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            text = (
                page.extract_text()
                or ""
            )

            pages.append(
                f"\n--- PAGE {page_number} ---\n"
                f"{text}"
            )

        return "\n".join(
            pages
        )

    except ImportError:
        pass

    try:
        import pdfplumber

        pages = []

        with pdfplumber.open(
            str(pdf_path)
        ) as pdf:

            for page_number, page in enumerate(
                pdf.pages,
                start=1
            ):

                text = (
                    page.extract_text()
                    or ""
                )

                pages.append(
                    f"\n--- PAGE {page_number} ---\n"
                    f"{text}"
                )

        return "\n".join(
            pages
        )

    except ImportError:

        raise RuntimeError(
            "Ne pypdf ne de pdfplumber kurulu."
        )


# =========================================================
# JSON SERIALIZER
# =========================================================

def json_serializer(
    obj
):

    if isinstance(
        obj,
        (date, datetime)
    ):

        return obj.isoformat()

    return str(
        obj
    )


# =========================================================
# PREVIEW
# =========================================================

def preview_text(
    text: str,
    max_length: int = 700
) -> str:

    text = text.strip()

    if len(text) <= max_length:
        return text

    return (
        text[:max_length]
        + "\n...[DEVAMI KESİLDİ]..."
    )


# =========================================================
# SAFE PARSER
# =========================================================

def safe_parse(
    parser,
    text: str
):

    try:

        return (
            parser(text)
            or {}
        )

    except Exception as exc:

        return {
            "_parser_error":
                str(exc)
        }


# =========================================================
# MAIN
# =========================================================

def main():

    if len(sys.argv) < 2:

        print()
        print(
            "KULLANIM:"
        )

        print(
            'python test_sds_file.py "uploads/dosya.pdf"'
        )

        print()

        sys.exit(
            1
        )

    pdf_path = Path(
        sys.argv[1]
    )

    if not pdf_path.exists():

        print(
            f"\nPDF bulunamadı:\n{pdf_path}\n"
        )

        sys.exit(
            1
        )

    # =====================================================
    # IMPORT SERVICES
    # =====================================================

    from app.services.text_normalizer import (
        normalize_sds_text,
    )

    from app.services.structure_normalizer import (
        normalize_sds_structure,
    )

    from app.services.section_splitter import (
        split_sds_sections,
    )

    from app.services.sds_parser import (
        parse_section_1,
    )

    from app.services.section_2_parser import (
        parse_section_2,
    )

    from app.services.section_3_parser import (
        parse_section_3,
    )

    from app.services.section_7_parser import (
        parse_section_7,
    )

    from app.services.section_8_parser import (
        parse_section_8,
    )

    from app.services.section_9_parser import (
        parse_section_9,
    )

    from app.services.revision_parser import (
        parse_revision_metadata,
    )

    from app.services.sds_ingestion import (
        ingest_sds_text,
    )

    # =====================================================
    # PDF -> RAW TEXT
    # =====================================================

    raw_text = extract_pdf_text(
        pdf_path
    )

    # =====================================================
    # NORMALIZATION
    # =====================================================

    normalized_text = (
        normalize_sds_text(
            raw_text
        )
    )

    structured_text = (
        normalize_sds_structure(
            normalized_text
        )
    )

    # =====================================================
    # HEADER
    # =====================================================

    print()
    print(
        "=" * 70
    )

    print(
        "UNIVERSAL SDS LOCAL TEST"
    )

    print(
        "=" * 70
    )

    print(
        f"Dosya: {pdf_path}"
    )

    print(
        f"Raw character count: "
        f"{len(raw_text)}"
    )

    print(
        f"Normalized character count: "
        f"{len(normalized_text)}"
    )

    print(
        f"Structured character count: "
        f"{len(structured_text)}"
    )

    # =====================================================
    # SPLIT
    # =====================================================

    sections = (
        split_sds_sections(
            structured_text
        )
    )

    section_numbers = sorted(
        sections.keys()
    )

    print()
    print(
        "=" * 70
    )

    print(
        "SECTION SPLITTER"
    )

    print(
        "=" * 70
    )

    print(
        f"Section count: {len(sections)}"
    )

    print(
        f"Section numbers: {section_numbers}"
    )

    # =====================================================
    # STRUCTURED TEXT PREVIEW
    # =====================================================

    print()
    print(
        "=" * 70
    )

    print(
        "STRUCTURED TEXT PREVIEW"
    )

    print(
        "=" * 70
    )

    print(
        preview_text(
            structured_text,
            max_length=2500
        )
    )

    # =====================================================
    # SECTION PREVIEWS
    # =====================================================

    print()
    print(
        "=" * 70
    )

    print(
        "SECTION PREVIEWS"
    )

    print(
        "=" * 70
    )

    for section_number in (
        section_numbers
    ):

        print()
        print(
            f"--- SECTION "
            f"{section_number} ---"
        )

        print(
            preview_text(
                sections[
                    section_number
                ],
                max_length=450
            )
        )

    # =====================================================
    # PARSERS
    # =====================================================

    section_1_data = (
        safe_parse(
            parse_section_1,
            sections.get(
                1,
                ""
            )
        )
        if 1 in sections
        else {}
    )

    section_2_data = (
        safe_parse(
            parse_section_2,
            sections.get(
                2,
                ""
            )
        )
        if 2 in sections
        else {}
    )

    section_3_data = (
        safe_parse(
            parse_section_3,
            sections.get(
                3,
                ""
            )
        )
        if 3 in sections
        else {}
    )

    section_7_data = (
        safe_parse(
            parse_section_7,
            sections.get(
                7,
                ""
            )
        )
        if 7 in sections
        else {}
    )

    section_8_data = (
        safe_parse(
            parse_section_8,
            sections.get(
                8,
                ""
            )
        )
        if 8 in sections
        else {}
    )

    section_9_data = (
        safe_parse(
            parse_section_9,
            sections.get(
                9,
                ""
            )
        )
        if 9 in sections
        else {}
    )

    revision_data = (
        safe_parse(
            parse_revision_metadata,
            structured_text
        )
    )

    # =====================================================
    # INGESTION
    #
    # IMPORTANT:
    # structured_text veriyoruz.
    #
    # Bu çağrı yine DB'ye hiçbir şey yazmaz.
    # =====================================================

    ingestion_data = (
        safe_parse(
            lambda value:
                ingest_sds_text(
                    text=value,
                    original_filename=
                        pdf_path.name,
                ),
            structured_text
        )
    )

    # =====================================================
    # RESULT
    # =====================================================

    result = {

        "file":
            str(pdf_path),

        "character_count":
            len(
                structured_text
            ),

        "section_count":
            len(
                sections
            ),

        "section_numbers":
            section_numbers,

        "section_1":
            section_1_data,

        "section_2":
            section_2_data,

        "section_3":
            section_3_data,

        "section_7":
            section_7_data,

        "section_8":
            section_8_data,

        "section_9":
            section_9_data,

        "revision":
            revision_data,

        "ingestion_summary": {

            "is_probable_sds":
                ingestion_data.get(
                    "is_probable_sds"
                ),

            "sds_confidence":
                ingestion_data.get(
                    "sds_confidence"
                ),

            "section_count":
                ingestion_data.get(
                    "section_count"
                ),

            "section_numbers":
                ingestion_data.get(
                    "section_numbers"
                ),

            "parsed_data":
                ingestion_data.get(
                    "parsed_data"
                ),

            "section_7_data":
                ingestion_data.get(
                    "section_7_data"
                ),

            "section_8_data":
                ingestion_data.get(
                    "section_8_data"
                ),

            "section_9_data":
                ingestion_data.get(
                    "section_9_data"
                ),

            "revision_data":
                ingestion_data.get(
                    "revision_data"
                ),

            "needs_review":
                ingestion_data.get(
                    "needs_review"
                ),

            "review_reasons":
                ingestion_data.get(
                    "review_reasons"
                ),
        },
    }

    # =====================================================
    # PRINT
    # =====================================================

    print()
    print(
        "=" * 70
    )

    print(
        "PARSER RESULT"
    )

    print(
        "=" * 70
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=json_serializer,
        )
    )

    # =====================================================
    # OUTPUT FILE
    # =====================================================

    output_path = (
        Path(
            "test_outputs"
        )
        /
        (
            pdf_path.stem
            + "_parser_result_v81.json"
        )
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=json_serializer,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "=" * 70
    )

    print(
        "Sonuç kaydedildi:"
    )

    print(
        output_path
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()