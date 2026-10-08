import re


# =========================================================
# BASIC HELPERS
# =========================================================

def _clean_text(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value or None


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


def _strip_leading_decoration(
    value: str | None
) -> str | None:

    value = _clean_text(value)

    if not value:
        return None

    value = re.sub(
        r"^[\s\-–—•·ꞏ*_:|/\\]+",
        "",
        value
    ).strip()

    return value or None


# =========================================================
# PRODUCT NAME
# =========================================================

PRODUCT_NAME_LABELS = [
    r"Ürün\s+Adı",
    r"Ürün\s+adı",
    r"Ürün\s+İsmi",
    r"Ürün\s+ismi",
    r"Ticari\s+Adı",
    r"Ticari\s+adı",
    r"Madde\s+Adı",
    r"Madde/Karışım\s+Adı",
    r"Product\s+Name",
    r"Product\s+name",
    r"Product\s+Identifier",
    r"Product\s+identifier",
    r"Trade\s+Name",
    r"Trade\s+name",
]


PRODUCT_VALUE_STOP_PATTERN = re.compile(
    r"(?i)"
    r"\s+(?="
    r"(?:"
    r"Ürün\s+Kodu"
    r"|Product\s+Code"
    r"|Article\s+(?:No|Number)"
    r"|UFI"
    r"|Benzersiz\s+Formül"
    r"|REACH"
    r"|CAS(?:\s+No\.?)?"
    r"|EC(?:\s+No\.?)?"
    r"|1\.2\b"
    r"|1\.3\b"
    r"|1\.4\b"
    r")"
    r")"
)


def _clean_product_name_value(
    value: str | None
) -> str | None:

    value = _strip_leading_decoration(value)

    if not value:
        return None

    value = PRODUCT_VALUE_STOP_PATTERN.split(
        value,
        maxsplit=1
    )[0]

    value = _clean_text(value)

    if not value:
        return None

    label_group = "|".join(
        PRODUCT_NAME_LABELS
    )

    value = re.sub(
        rf"(?i)^(?:{label_group})\s*:?\s*",
        "",
        value
    ).strip()

    value = _strip_leading_decoration(
        value
    )

    return value


def _find_product_name(
    text: str
) -> str | None:

    if not text:
        return None

    # Label + value on same line
    for label in PRODUCT_NAME_LABELS:

        pattern = re.compile(
            rf"(?im)"
            rf"^\s*"
            rf"[-–—•·ꞏ*_:|/\\]*"
            rf"\s*"
            rf"{label}"
            rf"\s*:?\s*"
            rf"(.+?)"
            rf"\s*$"
        )

        match = pattern.search(
            text
        )

        if match:

            value = _clean_product_name_value(
                match.group(1)
            )

            if value:
                return value

    # Fallback for compressed PDF text
    label_group = "|".join(
        PRODUCT_NAME_LABELS
    )

    match = re.search(
        rf"(?is)"
        rf"(?:{label_group})"
        rf"\s*:?\s*"
        rf"(.+?)"
        rf"(?="
        rf"\n"
        rf"|Ürün\s+Kodu"
        rf"|Product\s+Code"
        rf"|Article\s+(?:No|Number)"
        rf"|UFI"
        rf"|Benzersiz\s+Formül"
        rf"|REACH"
        rf"|CAS(?:\s+No\.?)?"
        rf"|EC(?:\s+No\.?)?"
        rf"|1\.2\b"
        rf"|1\.3\b"
        rf"|1\.4\b"
        rf"|$"
        rf")",
        text
    )

    if match:

        return _clean_product_name_value(
            match.group(1)
        )

    return None


# =========================================================
# PRODUCT CODE
# =========================================================

def _find_product_code(
    text: str
) -> str | None:

    if not text:
        return None

    patterns = [
        (
            r"(?i)"
            r"Ürün\s+Kodu"
            r"(?:\s*\(\s*ları\s*\))?"
            r"\s*:?\s*"
            r"([A-Z0-9][A-Z0-9._/\-]*)"
        ),
        (
            r"(?i)"
            r"Ürün\s+Kodları"
            r"\s*:?\s*"
            r"([A-Z0-9][A-Z0-9._/\-]*)"
        ),
        (
            r"(?i)"
            r"Product\s+Code"
            r"(?:\(s\))?"
            r"\s*:?\s*"
            r"([A-Z0-9][A-Z0-9._/\-]*)"
        ),
        (
            r"(?i)"
            r"Article\s+(?:No|Number)"
            r"\.?\s*:?\s*"
            r"([A-Z0-9][A-Z0-9._/\-]*)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            value = (
                match.group(1)
                .strip()
            )

            if value:
                return value

    return None


# =========================================================
# UFI
# =========================================================

UFI_PATTERN = re.compile(
    r"(?<![A-Z0-9])"
    r"([A-Z0-9]{4}"
    r"-[A-Z0-9]{4}"
    r"-[A-Z0-9]{4}"
    r"-[A-Z0-9]{4})"
    r"(?![A-Z0-9])",
    flags=re.IGNORECASE
)


def _find_ufis(
    text: str
) -> list[str]:

    if not text:
        return []

    values = [
        match.group(1).upper()
        for match in UFI_PATTERN.finditer(
            text
        )
    ]

    return _unique(
        values
    )


def _find_ufi(
    text: str
) -> str | None:

    ufis = _find_ufis(
        text
    )

    if not ufis:
        return None

    return "; ".join(
        ufis
    )


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


def _find_product_cas_numbers(
    text: str
) -> list[str]:

    if not text:
        return []

    matches = re.findall(
        r"(?<![\d-])"
        r"(\d{2,7}-\d{2}-\d)"
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
# EC NUMBER
# =========================================================

def _find_ec_number(
    text: str
) -> str | None:

    if not text:
        return None

    patterns = [
        (
            r"(?i)"
            r"(?:EC|EG|EINECS)"
            r"\s*(?:No\.?|Number|Numarası|Numarasi)?"
            r"\s*:?\s*"
            r"(\d{3}-\d{3}-\d)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(1)

    return None


# =========================================================
# REACH NUMBER
# =========================================================

def _find_reach_number(
    text: str
) -> str | None:

    if not text:
        return None

    match = re.search(
        r"(?<!\d)"
        r"(\d{2}-\d{10}-\d{2}-\d{4})"
        r"(?!\d)",
        text
    )

    if match:
        return match.group(1)

    return None


# =========================================================
# MANUFACTURER / SUPPLIER
# =========================================================

SUPPLIER_LABELS = [
    r"Üretici(?:\s*/\s*Tedarikçi)?",
    r"İmalatçı(?:\s*/\s*Tedarikçi)?",
    r"Tedarikçi(?:\s*/\s*Üretici)?",
    r"Manufacturer(?:\s*/\s*Supplier)?",
    r"Supplier(?:\s*/\s*Manufacturer)?",
    r"Firma\s+Adı",
    r"Şirket\s+Adı",
    r"Firma",
    r"Company\s+Name",
]


INVALID_SUPPLIER_VALUES = {
    "/undertaking",
    "undertaking",
    "company/undertaking",
    "the company/undertaking",
    "company",
    "supplier",
    "manufacturer",
    "details",
    "information",
}


def _clean_supplier_value(
    value: str | None
) -> str | None:

    value = _strip_leading_decoration(
        value
    )

    if not value:
        return None

    value = re.split(
        r"(?i)"
        r"\s+(?="
        r"(?:"
        r"Address|Adres|Telefon|Telephone|Phone|Tel\.?|Fax|"
        r"E-?mail|E-posta|Email|Web|Website|www\."
        r")"
        r"\s*:?"
        r")",
        value,
        maxsplit=1
    )[0]

    value = _clean_text(
        value
    )

    if not value:
        return None

    normalized = value.casefold().strip()

    if normalized in INVALID_SUPPLIER_VALUES:
        return None

    if (
        normalized.startswith("/undertaking")
        or normalized.startswith("undertaking")
    ):
        return None

    if (
        "@" in value
        or re.fullmatch(
            r"(?:https?://)?(?:www\.)?\S+\.\S+",
            value,
            flags=re.IGNORECASE
        )
        or re.fullmatch(
            r"[+\d()\s./\-]+",
            value
        )
    ):
        return None

    return value


def _find_manufacturer(
    text: str
) -> str | None:

    if not text:
        return None

    lines = [
        re.sub(
            r"\s+",
            " ",
            line
        ).strip()
        for line in text.splitlines()
        if line.strip()
    ]

    label_group = "|".join(
        SUPPLIER_LABELS
    )

    for index, line in enumerate(
        lines
    ):

        cleaned_line = re.sub(
            r"^[\s\-–—•·ꞏ*_:|/\\]+",
            "",
            line
        ).strip()

        # Label + value on same line.
        # Separator is required so that
        # "Manufacturer/undertaking"
        # does not become "/undertaking".
        match = re.match(
            rf"(?i)"
            rf"^(?:{label_group})"
            rf"(?:\s*:\s*|\s{{2,}})"
            rf"(.+)$",
            cleaned_line
        )

        if match:

            value = _clean_supplier_value(
                match.group(1)
            )

            if value:
                return value

        # Label-only line -> next meaningful line
        if re.fullmatch(
            rf"(?i)"
            rf"(?:{label_group})"
            rf"\s*:?",
            cleaned_line
        ):

            for next_index in range(
                index + 1,
                min(
                    index + 4,
                    len(lines)
                )
            ):

                candidate = _clean_supplier_value(
                    lines[next_index]
                )

                if candidate:
                    return candidate

    return None


# =========================================================
# PUBLIC SECTION 1 PARSER
# =========================================================

def parse_section_1(
    section_text: str
) -> dict:

    if not section_text:

        return {
            "product_name": None,
            "manufacturer": None,
            "cas_numbers": [],
            "ec_number": None,
            "reach_number": None,
            "product_code": None,
            "ufi": None,
        }

    product_name = (
        _find_product_name(
            section_text
        )
    )

    manufacturer = (
        _find_manufacturer(
            section_text
        )
    )

    cas_numbers = (
        _find_product_cas_numbers(
            section_text
        )
    )

    ec_number = (
        _find_ec_number(
            section_text
        )
    )

    reach_number = (
        _find_reach_number(
            section_text
        )
    )

    product_code = (
        _find_product_code(
            section_text
        )
    )

    ufi = (
        _find_ufi(
            section_text
        )
    )

    return {
        "product_name":
            product_name,

        "manufacturer":
            manufacturer,

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
    }