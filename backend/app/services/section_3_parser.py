import re


# =========================================================
# UNIQUE
# =========================================================

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


# =========================================================
# CAS VALIDATION
# =========================================================

def _is_valid_cas(
    cas_number: str
) -> bool:

    """
    CAS checksum doğrulaması.

    Örnek:
        1310-58-3 -> valid

    CAS formatı:
        2-7 digits
        -
        2 digits
        -
        1 check digit
    """

    try:

        if not re.fullmatch(
            r"\d{2,7}-\d{2}-\d",
            cas_number
        ):
            return False

        parts = cas_number.split("-")

        first_part = parts[0]
        second_part = parts[1]
        check_digit = int(parts[2])

        digits = (
            first_part
            + second_part
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


# =========================================================
# CAS EXTRACTION
# =========================================================

def _find_cas_numbers(
    text: str
) -> list[str]:

    """
    Section 3 içindeki bileşen CAS numaralarını bulur.

    ÖNEMLİ:

    019-002-00-8 gibi CLP Index No değerlerinin içinden:

        002-00-8

    şeklinde sahte CAS çıkarmamalıdır.
    """

    if not text:
        return []

    # -----------------------------------------------------
    # Generic CAS candidate
    #
    # Sol ve sağ tarafta digit veya "-" bulunamaz.
    #
    # Böylece:
    #
    # 019-002-00-8
    #
    # içindeki:
    #
    # 002-00-8
    #
    # eşleşmez.
    # -----------------------------------------------------

    matches = re.findall(
        r"(?<![\d-])"
        r"(\d{2,7}-\d{2}-\d)"
        r"(?![\d-])",
        text
    )

    valid = []

    for value in matches:

        if not _is_valid_cas(
            value
        ):
            continue

        valid.append(
            value
        )

    return _unique(
        valid
    )


# =========================================================
# EC / EG / EINECS
# =========================================================

def _find_ec_numbers(
    text: str
) -> list[str]:

    patterns = [
        (
            r"\bEC\s*"
            r"(?:number|no\.?|numarası|numarasi)?"
            r"\s*[:\-]?\s*"
            r"(\d{3}-\d{3}-\d)\b"
        ),

        (
            r"\bEC-No\.?\s*:\s*"
            r"(\d{3}-\d{3}-\d)\b"
        ),

        (
            r"\bEG\s*"
            r"(?:number|no\.?|numarası|numarasi)?"
            r"\s*[:\-]?\s*"
            r"(\d{3}-\d{3}-\d)\b"
        ),

        (
            r"\bEINECS\s*"
            r"(?:number|no\.?)?"
            r"\s*[:\-]?\s*"
            r"(\d{3}-\d{3}-\d)\b"
        ),
    ]

    values = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        values.extend(
            matches
        )

    return _unique(
        values
    )


# =========================================================
# REACH
# =========================================================

def _find_reach_numbers(
    text: str
) -> list[str]:

    if not text:
        return []

    # Standard REACH registration number
    matches = re.findall(
        r"(?<!\d)"
        r"\d{2}-\d{10}-\d{2}-\d{4}"
        r"(?!\d)",
        text
    )

    return _unique(
        matches
    )


# =========================================================
# COMPONENT NAMES
# =========================================================

def _find_component_names(
    text: str
) -> list[str]:

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    components = []

    heading_patterns = [
        r"^Kimyasal\s+yap[ıi]s[ıi]\s*:?\s*$",
        r"^Kimyasal\s+özellikleri\s*:?\s*$",
        r"^Chemical\s+composition\s*:?\s*$",
    ]

    for index, line in enumerate(
        lines
    ):

        # -------------------------------------------------
        # Heading -> next line
        # -------------------------------------------------

        if any(
            re.match(
                pattern,
                line,
                flags=re.IGNORECASE
            )
            for pattern in heading_patterns
        ):

            if index + 1 < len(lines):

                candidate = (
                    lines[index + 1]
                    .strip()
                )

                if candidate:
                    components.append(
                        candidate
                    )

        # -------------------------------------------------
        # Explicit chemical-name labels
        # -------------------------------------------------

        match = re.match(
            (
                r"^(?:"
                r"Kimyasal\s+ad[ıi]|"
                r"Madde\s+ad[ıi](?:\s*\([^)]*\))?|"
                r"Chemical\s+name|"
                r"Substance\s+name"
                r")"
                r"\s*:?\s*(.+)$"
            ),
            line,
            flags=re.IGNORECASE
        )

        if match:

            value = (
                match.group(1)
                .strip()
            )

            if value:
                components.append(
                    value
                )

    return _unique(
        components
    )


# =========================================================
# SECTION 3 PARSER
# =========================================================

def parse_section_3(
    section_text: str
) -> dict:

    cas_numbers = (
        _find_cas_numbers(
            section_text
        )
    )

    ec_numbers = (
        _find_ec_numbers(
            section_text
        )
    )

    reach_numbers = (
        _find_reach_numbers(
            section_text
        )
    )

    component_names = (
        _find_component_names(
            section_text
        )
    )

    return {

        # These identifiers belong to COMPONENTS,
        # not automatically to the commercial product.
        "cas_numbers":
            cas_numbers,

        "ec_numbers":
            ec_numbers,

        "reach_numbers":
            reach_numbers,

        "component_names":
            component_names,

        # Backward compatibility
        "ec_number": (
            ec_numbers[0]
            if ec_numbers
            else None
        ),

        "reach_number": (
            reach_numbers[0]
            if reach_numbers
            else None
        ),
    }