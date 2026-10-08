import re
from pathlib import Path
from typing import Any, Callable

from app.services.document_classifier import classify_document
from app.services.section_splitter import split_sds_sections

from app.services.sds_parser import parse_section_1
from app.services.section_2_parser import parse_section_2
from app.services.section_3_parser import parse_section_3
from app.services.section_7_parser import parse_section_7
from app.services.section_8_parser import parse_section_8
from app.services.section_9_parser import parse_section_9
from app.services.revision_parser import parse_revision_metadata
from app.services.text_normalizer import normalize_sds_text


# =========================================================
# BASIC HELPERS
# =========================================================

def _clean_line(
    line: str
) -> str:

    line = line.strip()

    line = re.sub(
        r"^[\*\-·•]+\s*",
        "",
        line
    )

    line = re.sub(
        r"\s+",
        " ",
        line
    )

    return line.strip()


def _unique(
    values: list[str]
) -> list[str]:

    result = []
    seen = set()

    for value in values:

        if not value:
            continue

        value = value.strip()

        if not value:
            continue

        key = value.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def _safe_parse(
    parser: Callable,
    text: str,
    default: Any
):

    try:

        result = parser(
            text
        )

        if result is None:
            return default

        return result

    except Exception:

        return default


# =========================================================
# CAS
# =========================================================

def _is_valid_cas(
    cas_number: str
) -> bool:

    try:

        if not re.fullmatch(
            r"\d{2,7}-\d{2}-\d",
            cas_number
        ):
            return False

        parts = cas_number.split("-")

        if len(parts) != 3:
            return False

        digits = (
            parts[0]
            + parts[1]
        )

        check_digit = int(
            parts[2]
        )

        total = 0

        for index, digit in enumerate(
            reversed(digits),
            start=1
        ):

            total += (
                int(digit)
                * index
            )

        return (
            total % 10
            == check_digit
        )

    except Exception:

        return False


def _find_cas_numbers(
    text: str
) -> list[str]:

    if not text:
        return []

    matches = re.findall(
        r"(?<![\d-])"
        r"\d{2,7}-\d{2}-\d"
        r"(?![\d-])",
        text
    )

    return _unique(
        [
            value
            for value in matches
            if _is_valid_cas(
                value
            )
        ]
    )


# =========================================================
# PRODUCT
# =========================================================

PRODUCT_LABELS = [
    r"Madde\s+Adı",
    r"Madde/Karışım\s+Adı",
    r"Madde/Karışımın\s+Adı",
    r"Ürün\s+ismi",
    r"Ürün\s+adı",
    r"Ticari\s+ismi",
    r"Ticari\s+adı",
    r"Product\s+name",
    r"Trade\s+name",
    r"Commercial\s+name",
    r"Product\s+identifier",
]


def _normalize_product_name(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = _clean_line(
        value
    )

    for _ in range(4):

        original = value

        for label in PRODUCT_LABELS:

            value = re.sub(
                rf"^{label}\s*:?\s*",
                "",
                value,
                flags=re.IGNORECASE
            ).strip()

        if value == original:
            break

    return value or None


def _find_product_name_fallback(
    text: str
) -> str | None:

    lines = [
        _clean_line(line)
        for line in text.splitlines()[:300]
    ]

    for line in lines:

        for label in PRODUCT_LABELS:

            match = re.match(
                rf"^{label}\s*:?\s*(.+)$",
                line,
                flags=re.IGNORECASE
            )

            if not match:
                continue

            candidate = (
                _normalize_product_name(
                    match.group(1)
                )
            )

            if candidate:
                return candidate

    return None


# =========================================================
# MANUFACTURER
# =========================================================

def _normalize_manufacturer(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = _clean_line(
        value
    )

    prefixes = [
        r"Firma\s+Adı",
        r"Şirket\s+Adı",
        r"Üretici",
        r"İmalatçı",
        r"Tedarikçi",
        r"Manufacturer",
        r"Supplier",
        r"Company",
        r"Adı",
    ]

    for prefix in prefixes:

        value = re.sub(
            rf"^{prefix}\s*:?\s*",
            "",
            value,
            flags=re.IGNORECASE
        ).strip()

    return value or None


def _is_suspicious_manufacturer(
    value: str | None
) -> bool:

    if not value:
        return True

    normalized = (
        value.strip()
        .casefold()
    )

    bad_values = {
        "bilgisi",
        "adı",
        "firma",
        "şirket",
        "üretici",
        "tedarikçi",
        "company",
        "supplier",
        "manufacturer",
    }

    if normalized in bad_values:
        return True

    if len(normalized) < 4:
        return True

    return False


def _find_manufacturer_fallback(
    text: str
) -> str | None:

    lines = [
        _clean_line(line)
        for line in text.splitlines()[:400]
    ]

    labels = [
        r"Tedarikçi",
        r"Üretici",
        r"Firma\s+Adı",
        r"Şirket\s+Adı",
        r"Manufacturer",
        r"Supplier",
        r"Company",
    ]

    for index, line in enumerate(lines):

        for label in labels:

            match = re.match(
                rf"^{label}\s*:?\s*(.*)$",
                line,
                flags=re.IGNORECASE
            )

            if not match:
                continue

            inline = (
                _normalize_manufacturer(
                    match.group(1)
                )
            )

            if (
                inline
                and not _is_suspicious_manufacturer(
                    inline
                )
            ):
                return inline

            if index + 1 < len(lines):

                next_value = (
                    _normalize_manufacturer(
                        lines[
                            index + 1
                        ]
                    )
                )

                if (
                    next_value
                    and not _is_suspicious_manufacturer(
                        next_value
                    )
                ):
                    return next_value

    return None


# =========================================================
# IDENTIFIERS
# =========================================================

def _find_ec_number(
    text: str
) -> str | None:

    match = re.search(
        r"(?:EC\s*(?:No)?|EINECS)"
        r"\s*:?\s*"
        r"(\d{3}-\d{3}-\d)",
        text,
        flags=re.IGNORECASE
    )

    return (
        match.group(1)
        if match
        else None
    )


def _find_reach_number(
    text: str
) -> str | None:

    match = re.search(
        r"\b"
        r"\d{2}-\d{10}-\d{2}-\d{4}"
        r"\b",
        text
    )

    return (
        match.group(0)
        if match
        else None
    )


def _find_ufi(
    text: str
) -> str | None:

    if not text:
        return None

    matches = re.findall(
        r"(?<![A-Z0-9])"
        r"([A-Z0-9]{4}-"
        r"[A-Z0-9]{4}-"
        r"[A-Z0-9]{4}-"
        r"[A-Z0-9]{4})"
        r"(?![A-Z0-9])",
        text,
        flags=re.IGNORECASE
    )

    if not matches:
        return None

    values = _unique(
        [
            value.upper()
            for value in matches
        ]
    )

    return "; ".join(
        values
    )


# =========================================================
# H / P / GHS
# =========================================================

def _find_hazard_codes(
    text: str
) -> list[str]:

    if not text:
        return []

    return _unique(
        [
            value.upper()
            for value in re.findall(
                r"\bH\d{3}[A-Z]?\b",
                text,
                flags=re.IGNORECASE
            )
        ]
    )


def _normalize_p_code(
    code: str
) -> str:

    """
    P-code groups are normalized as:

        P305+P351+P338

    Every component keeps the P prefix.
    """

    if not code:
        return ""

    numbers = re.findall(
        r"P?\s*(\d{3})",
        code,
        flags=re.IGNORECASE
    )

    if not numbers:
        return ""

    return "+".join(
        f"P{number}"
        for number in numbers
    )


def _find_precautionary_codes(
    text: str
) -> list[str]:

    """
    Fallback P-code extractor.

    This is only used when section_2_parser did not
    return any precautionary codes.
    """

    if not text:
        return []

    matches = re.findall(
        r"P\s*\d{3}"
        r"(?:"
        r"\s*\+\s*"
        r"P?\s*\d{3}"
        r")*",
        text,
        flags=re.IGNORECASE
    )

    result = []

    for value in matches:

        normalized = (
            _normalize_p_code(
                value
            )
        )

        if normalized:
            result.append(
                normalized
            )

    return _unique(
        result
    )


def _find_ghs_codes(
    text: str
) -> list[str]:

    if not text:
        return []

    return _unique(
        [
            value.upper()
            for value in re.findall(
                r"\bGHS0[1-9]\b",
                text,
                flags=re.IGNORECASE
            )
        ]
    )


def _normalize_signal_word(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = re.sub(
        r"^[\s·•\-\*]+",
        "",
        value
    ).strip()

    upper = value.upper()

    if "TEHLİKE" in upper:
        return "Tehlike"

    if "DİKKAT" in upper:
        return "Dikkat"

    if "DANGER" in upper:
        return "Danger"

    if "WARNING" in upper:
        return "Warning"

    return value or None


# =========================================================
# CLASSIFICATION STATUS
# =========================================================

def _detect_classification_status(
    section_2_text: str,
    hazard_codes: list[str],
    precautionary_codes: list[str],
    signal_word: str | None,
    ghs_codes: list[str]
) -> str:

    if (
        hazard_codes
        or precautionary_codes
        or signal_word
        or ghs_codes
    ):
        return "classified"

    normalized = re.sub(
        r"\s+",
        " ",
        section_2_text
    ).casefold()

    not_classified_markers = [
        "sınıflandırılmamıştır",
        "sınıflandırılmamış",
        "tehlikeli olarak sınıflandırılmamıştır",
        "zararlı olarak sınıflandırılmamıştır",
        "etiketleme yok",
        "no classification",
        "not classified",
        "not classified as hazardous",
        "no labelling",
        "no labeling",
    ]

    if any(
        marker in normalized
        for marker in not_classified_markers
    ):
        return "not_classified"

    return "unknown"


# =========================================================
# H -> GHS FALLBACK
# =========================================================

H_TO_GHS = {
    "H220": "GHS02",
    "H221": "GHS02",
    "H224": "GHS02",
    "H225": "GHS02",
    "H226": "GHS02",

    "H270": "GHS03",
    "H271": "GHS03",
    "H272": "GHS03",

    "H290": "GHS05",
    "H314": "GHS05",
    "H318": "GHS05",

    "H300": "GHS06",
    "H310": "GHS06",
    "H330": "GHS06",

    "H302": "GHS07",
    "H312": "GHS07",
    "H315": "GHS07",
    "H317": "GHS07",
    "H319": "GHS07",
    "H332": "GHS07",
    "H335": "GHS07",
    "H336": "GHS07",

    "H304": "GHS08",
    "H334": "GHS08",
    "H340": "GHS08",
    "H341": "GHS08",
    "H350": "GHS08",
    "H351": "GHS08",
    "H360": "GHS08",
    "H361": "GHS08",
    "H370": "GHS08",
    "H371": "GHS08",
    "H372": "GHS08",
    "H373": "GHS08",

    "H400": "GHS09",
    "H410": "GHS09",
    "H411": "GHS09",
}


# =========================================================
# CONFIDENCE
# =========================================================

def _calculate_sds_confidence(
    text: str,
    sections: dict[int, str]
) -> tuple[float, list[str]]:

    normalized = re.sub(
        r"\s+",
        " ",
        text
    ).upper()

    score = 0.0
    evidence = []

    titles = [
        "GÜVENLİK BİLGİ FORMU",
        "SAFETY DATA SHEET",
        "MATERIAL SAFETY DATA SHEET",
    ]

    for title in titles:

        if title in normalized:

            score += 0.25

            evidence.append(
                f"title:{title}"
            )

            break

    heading_groups = [
        [
            "ZARARLILIK TANIMLANMASI",
            "HAZARDS IDENTIFICATION"
        ],
        [
            "İLK YARDIM",
            "FIRST AID"
        ],
        [
            "YANGINLA MÜCADELE",
            "FIREFIGHTING"
        ],
        [
            "ELLEÇLEME VE DEPOLAMA",
            "HANDLING AND STORAGE"
        ],
        [
            "MARUZİYET KONTROLLERİ",
            "EXPOSURE CONTROLS"
        ],
        [
            "FİZİKSEL VE KİMYASAL",
            "PHYSICAL AND CHEMICAL"
        ],
        [
            "TOKSİKOLOJİ",
            "TOXICOLOGICAL"
        ],
        [
            "TAŞIMACILIK",
            "TRANSPORT INFORMATION"
        ],
        [
            "MEVZUAT",
            "REGULATORY INFORMATION"
        ],
    ]

    heading_hits = sum(
        1
        for group in heading_groups
        if any(
            marker in normalized
            for marker in group
        )
    )

    if heading_hits >= 3:

        score += 0.20

        evidence.append(
            f"heading_hits:{heading_hits}"
        )

    if heading_hits >= 6:
        score += 0.15

    section_count = len(
        sections
    )

    if section_count >= 4:

        score += 0.10

        evidence.append(
            f"sections:{section_count}"
        )

    if section_count >= 8:
        score += 0.15

    if section_count >= 14:
        score += 0.15

    chemical_markers = [
        "CAS",
        "REACH",
        "H315",
        "H319",
        "H400",
        "H410",
        "P280",
        "UFI",
    ]

    if any(
        marker in normalized
        for marker in chemical_markers
    ):
        score += 0.10

    return (
        min(
            score,
            1.0
        ),
        evidence
    )


# =========================================================
# MAIN INGESTION
# =========================================================

def ingest_sds_text(
    text: str,
    original_filename: str | None = None
) -> dict:

    # -----------------------------------------------------
    # NORMALIZATION
    # -----------------------------------------------------

    text = normalize_sds_text(
        text
    )

    # -----------------------------------------------------
    # SECTION SPLIT
    # -----------------------------------------------------

    sections = split_sds_sections(
        text
    )

    # -----------------------------------------------------
    # SDS CLASSIFICATION
    # -----------------------------------------------------

    legacy_classifier = _safe_parse(
        classify_document,
        text,
        "UNKNOWN"
    )

    confidence, evidence = (
        _calculate_sds_confidence(
            text,
            sections
        )
    )

    is_probable_sds = (
        legacy_classifier == "SDS"
        or confidence >= 0.45
    )

    # -----------------------------------------------------
    # SECTION PARSERS
    # -----------------------------------------------------

    section_1 = _safe_parse(
        parse_section_1,
        sections.get(1) or text,
        {}
    )

    section_2 = (
        _safe_parse(
            parse_section_2,
            sections[2],
            {}
        )
        if 2 in sections
        else {}
    )

    section_3 = (
        _safe_parse(
            parse_section_3,
            sections[3],
            {}
        )
        if 3 in sections
        else {}
    )

    section_7 = (
        _safe_parse(
            parse_section_7,
            sections[7],
            {}
        )
        if 7 in sections
        else {}
    )

    section_8 = (
        _safe_parse(
            parse_section_8,
            sections[8],
            {}
        )
        if 8 in sections
        else {}
    )

    section_9 = (
        _safe_parse(
            parse_section_9,
            sections[9],
            {}
        )
        if 9 in sections
        else {}
    )

    revision = _safe_parse(
        parse_revision_metadata,
        text,
        {}
    )

    # =====================================================
    # PRODUCT
    # =====================================================

    section_product_name = (
        _normalize_product_name(
            section_1.get(
                "product_name"
            )
        )
    )

    product_name = (
        section_product_name
        or _find_product_name_fallback(
            text
        )
    )

    if section_product_name:

        product_name_source = (
            "section_1"
        )

    elif product_name:

        product_name_source = (
            "document_fallback"
        )

    else:

        product_name_source = None

    if (
        not product_name
        and original_filename
    ):

        product_name = (
            Path(
                original_filename
            ).stem
        )

        product_name_source = (
            "filename_fallback"
        )

    # =====================================================
    # MANUFACTURER
    # =====================================================

    manufacturer = (
        _normalize_manufacturer(
            section_1.get(
                "manufacturer"
            )
        )
    )

    if _is_suspicious_manufacturer(
        manufacturer
    ):

        manufacturer = (
            _find_manufacturer_fallback(
                text
            )
        )

    # =====================================================
    # SOURCE-AWARE IDENTIFIERS
    # =====================================================
    #
    # Section 1 = PRODUCT identifiers
    # Section 3 = COMPONENT identifiers
    # =====================================================

    section_1_text = (
        sections.get(1)
        or ""
    )

    section_3_text = (
        sections.get(3)
        or ""
    )

    # =====================================================
    # PRODUCT CAS — SECTION 1 ONLY
    # =====================================================

    product_cas_candidates = (
        section_1.get(
            "cas_numbers"
        )
        or []
    )

    product_cas_candidates = (
        product_cas_candidates
        +
        _find_cas_numbers(
            section_1_text
        )
    )

    cas_numbers = _unique(
        [
            cas
            for cas in product_cas_candidates
            if _is_valid_cas(
                cas
            )
        ]
    )

    # =====================================================
    # COMPONENT CAS — SECTION 3 ONLY
    # =====================================================

    component_cas_numbers = _unique(
        [
            cas
            for cas in (
                section_3.get(
                    "cas_numbers"
                )
                or []
            )
            if _is_valid_cas(
                cas
            )
        ]
    )

    # =====================================================
    # PRODUCT EC — SECTION 1 ONLY
    # =====================================================

    ec_number = (
        section_1.get(
            "ec_number"
        )
        or _find_ec_number(
            section_1_text
        )
    )

    # =====================================================
    # COMPONENT EC — SECTION 3 ONLY
    # =====================================================

    component_ec_numbers = _unique(
        section_3.get(
            "ec_numbers"
        )
        or []
    )

    # =====================================================
    # PRODUCT REACH — SECTION 1 ONLY
    # =====================================================

    reach_number = (
        section_1.get(
            "reach_number"
        )
        or _find_reach_number(
            section_1_text
        )
    )

    # =====================================================
    # COMPONENT REACH — SECTION 3 ONLY
    # =====================================================

    component_reach_numbers = _unique(
        section_3.get(
            "reach_numbers"
        )
        or []
    )

    # =====================================================
    # PRODUCT CODE
    # =====================================================

    product_code = (
        section_1.get(
            "product_code"
        )
    )

    # =====================================================
    # UFI — SECTION 1 ONLY
    # =====================================================

    ufi = (
        section_1.get(
            "ufi"
        )
        or _find_ufi(
            section_1_text
        )
    )

    # =====================================================
    # COMPONENT NAMES
    # =====================================================

    component_names = (
        section_3.get(
            "component_names"
        )
        or []
    )

    # =====================================================
    # PRODUCT HAZARDS — SECTION 2 ONLY
    # =====================================================

    section_2_text = (
        sections.get(2)
        or ""
    )

    # -----------------------------------------------------
    # Parser result has priority.
    #
    # section_2_parser performs the stricter hazard-code
    # extraction. A second generic scan must not be merged
    # into a successful parser result because ordinary SDS
    # text, addresses or other document content can create
    # false-positive H codes.
    #
    # Generic extraction is used only as a fallback when
    # the dedicated Section 2 parser returns no H codes.
    # -----------------------------------------------------

    parser_hazard_codes = (
        section_2.get(
            "hazard_codes"
        )
        or []
    )

    if parser_hazard_codes:

        hazard_codes = _unique(
            parser_hazard_codes
        )

    else:

        hazard_codes = _unique(
            _find_hazard_codes(
                section_2_text
            )
        )

    # =====================================================
    # PRECAUTIONARY CODES
    # =====================================================
    #
    # Parser result has priority.
    #
    # Fallback is used ONLY if section_2_parser returns
    # no precautionary codes.
    #
    # This prevents:
    #
    # P305+P351+P338
    #
    # from being duplicated as:
    #
    # P351+P338
    # =====================================================

    parser_precautionary_codes = (
        section_2.get(
            "precautionary_codes"
        )
        or []
    )

    if parser_precautionary_codes:

        precautionary_codes = _unique(
            [
                _normalize_p_code(
                    code
                )
                for code
                in parser_precautionary_codes
                if _normalize_p_code(
                    code
                )
            ]
        )

    else:

        precautionary_codes = _unique(
            [
                _normalize_p_code(
                    code
                )
                for code
                in _find_precautionary_codes(
                    section_2_text
                )
                if _normalize_p_code(
                    code
                )
            ]
        )

    signal_word = (
        _normalize_signal_word(
            section_2.get(
                "signal_word"
            )
        )
    )

    ghs_codes = _unique(
        (
            section_2.get(
                "ghs_codes"
            )
            or []
        )
        +
        _find_ghs_codes(
            section_2_text
        )
    )

    # -----------------------------------------------------
    # CLASSIFICATION STATUS
    # -----------------------------------------------------

    classification_status = (
        _detect_classification_status(
            section_2_text=
                section_2_text,

            hazard_codes=
                hazard_codes,

            precautionary_codes=
                precautionary_codes,

            signal_word=
                signal_word,

            ghs_codes=
                ghs_codes
        )
    )

    # -----------------------------------------------------
    # H -> GHS FALLBACK
    # -----------------------------------------------------

    if (
        classification_status
        == "classified"
    ):

        for hazard_code in hazard_codes:

            inferred = (
                H_TO_GHS.get(
                    hazard_code
                )
            )

            if (
                inferred
                and inferred
                not in ghs_codes
            ):

                ghs_codes.append(
                    inferred
                )

    # =====================================================
    # COMPONENT HAZARDS — SECTION 3 ONLY
    # =====================================================

    component_hazard_codes = (
        _find_hazard_codes(
            section_3_text
        )
    )

    # =====================================================
    # REVIEW SYSTEM
    # =====================================================

    review_reasons = []

    if (
        not product_name
        or product_name_source
        == "filename_fallback"
    ):

        review_reasons.append(
            "product_name_needs_review"
        )

    if (
        not manufacturer
        or _is_suspicious_manufacturer(
            manufacturer
        )
    ):

        review_reasons.append(
            "manufacturer_needs_review"
        )

    if not (
        cas_numbers
        or ec_number
        or reach_number
        or ufi
        or product_code
    ):

        review_reasons.append(
            "chemical_identifier_missing"
        )

    if len(sections) < 10:

        review_reasons.append(
            "low_section_count"
        )

    if confidence < 0.60:

        review_reasons.append(
            "low_sds_confidence"
        )

    # -----------------------------------------------------
    # SECTION 2 QUALITY
    # -----------------------------------------------------

    if 2 in sections:

        if (
            classification_status
            == "unknown"
        ):

            review_reasons.append(
                "classification_status_unknown"
            )

        if (
            classification_status
            == "classified"
            and not hazard_codes
            and not signal_word
            and not ghs_codes
        ):

            review_reasons.append(
                "section_2_data_incomplete"
            )

    # -----------------------------------------------------
    # SECTION 7
    # -----------------------------------------------------

    if (
        7 in sections
        and not section_7
    ):

        review_reasons.append(
            "section_7_parse_failed"
        )

    # -----------------------------------------------------
    # SECTION 8
    # -----------------------------------------------------

    if 8 in sections:

        if not section_8:

            review_reasons.append(
                "section_8_parse_failed"
            )

        else:

            ppe_count = sum(
                1
                for key in [
                    "respiratory_protection",
                    "hand_protection",
                    "eye_face_protection",
                    "body_protection",
                ]
                if section_8.get(
                    key
                )
            )

            if ppe_count == 0:

                review_reasons.append(
                    "ppe_data_missing"
                )

    # -----------------------------------------------------
    # SECTION 9
    # -----------------------------------------------------

    if 9 in sections:

        if not section_9:

            review_reasons.append(
                "section_9_parse_failed"
            )

        else:

            important_fields = [
                "physical_state",
                "color",
                "odor",
                "ph",
                "flash_point",
                "density",
                "boiling_point",
                "viscosity",
                "solubility",
            ]

            found_count = sum(
                1
                for field in important_fields
                if section_9.get(
                    field
                )
            )

            if found_count < 3:

                review_reasons.append(
                    "physical_properties_incomplete"
                )

    review_reasons = list(
        dict.fromkeys(
            review_reasons
        )
    )

    needs_review = bool(
        review_reasons
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "is_probable_sds":
            is_probable_sds,

        "sds_confidence":
            round(
                confidence,
                2
            ),

        "classification_evidence":
            evidence,

        "legacy_document_type":
            legacy_classifier,

        "section_count":
            len(
                sections
            ),

        "section_numbers":
            sorted(
                sections.keys()
            ),

        "sections":
            sections,

        "parsed_data": {

            "product_name":
                product_name,

            "product_name_source":
                product_name_source,

            "manufacturer":
                manufacturer,

            # =============================================
            # PRODUCT IDENTIFIERS
            # =============================================

            "cas_numbers":
                cas_numbers,

            "ec_number":
                ec_number,

            "reach_number":
                reach_number,

            "product_code":
                product_code,

            "ufi":
                ufi,

            # =============================================
            # COMPONENT IDENTIFIERS
            # =============================================

            "component_cas_numbers":
                component_cas_numbers,

            "component_ec_numbers":
                component_ec_numbers,

            "component_reach_numbers":
                component_reach_numbers,

            "component_names":
                component_names,

            # =============================================
            # PRODUCT HAZARDS
            # =============================================

            "classification_status":
                classification_status,

            "hazard_codes":
                hazard_codes,

            "precautionary_codes":
                precautionary_codes,

            "signal_word":
                signal_word,

            "ghs_codes":
                ghs_codes,

            # =============================================
            # COMPONENT HAZARDS
            # =============================================

            "component_hazard_codes":
                component_hazard_codes,
        },

        "revision_data":
            revision,

        "section_7_data":
            section_7,

        "section_8_data":
            section_8,

        "section_9_data":
            section_9,

        "needs_review":
            needs_review,

        "review_reasons":
            review_reasons,
    }