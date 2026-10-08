import re


# =========================================================
# BASIC HELPERS
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

        key = value.upper()

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


# =========================================================
# H CODES
# =========================================================

_HAZARD_SUFFIXES = {
    "350": {
        "I": "i",
    },
    "360": {
        "F": "F",
        "D": "D",
        "FD": "FD",
        "DF": "DF",
    },
    "361": {
        "F": "f",
        "D": "d",
        "FD": "fd",
        "DF": "df",
    },
}


def _find_hazard_codes(
    text: str
) -> list[str]:

    if not text:
        return []

    # =====================================================
    # IMPORTANT
    # =====================================================
    #
    # Product H statements must be parsed independently
    # from EUH supplemental statements.
    #
    # Example:
    #
    #   EUH205
    #
    # must NOT become:
    #
    #   H205
    #
    # We therefore explicitly reject an H token when it is
    # immediately preceded by "EU".
    #
    # The parser also rejects longer numeric/alphanumeric
    # strings such as:
    #
    #   GmbH20539
    #
    # Valid examples:
    #
    #   H315
    #   H411
    #   H350i
    #   H360F
    #   H360FD
    #   H361fd
    #
    # =====================================================

    pattern = re.compile(
        r"(?<!EU)"
        r"H"
        r"\s*"
        r"(\d{3})"
        r"([A-Za-z]{0,2})?"
        r"(?![A-Za-z0-9])",
        flags=re.IGNORECASE
    )

    codes = []

    for match in pattern.finditer(
        text
    ):

        base_code = (
            match.group(1)
            or ""
        )

        raw_suffix = (
            match.group(2)
            or ""
        )

        suffix = ""

        if raw_suffix:

            normalized_suffix = (
                raw_suffix.upper()
            )

            allowed_suffixes = (
                _HAZARD_SUFFIXES.get(
                    base_code,
                    {}
                )
            )

            # A suffix exists but this H-code does not
            # officially use that suffix pattern.
            # Reject the complete candidate rather than
            # silently converting it into the base code.
            if (
                normalized_suffix
                not in allowed_suffixes
            ):
                continue

            suffix = (
                allowed_suffixes[
                    normalized_suffix
                ]
            )

        code = (
            "H"
            + base_code
            + suffix
        )

        codes.append(
            code
        )

    return _unique(
        codes
    )


# =========================================================
# P CODE NORMALIZATION
# =========================================================

def _normalize_precautionary_code(
    value: str
) -> str:

    """
    Examples:

        P280
        -> P280

        P305 + P351+P338
        -> P305+P351+P338

        P332 + P313
        -> P332+P313

        P302+352
        -> P302+P352
    """

    if not value:
        return ""

    numbers = re.findall(
        r"P?\s*(\d{3})",
        value,
        flags=re.IGNORECASE
    )

    if not numbers:
        return ""

    return "+".join(
        f"P{number}"
        for number in numbers
    )


# =========================================================
# P CODES
# =========================================================

def _find_precautionary_codes(
    text: str
) -> list[str]:

    if not text:
        return []

    # =====================================================
    # IMPORTANT PDF EXTRACTION NOTE
    # =====================================================
    #
    # Some PDFs produce text like:
    #
    # kullanınP234
    # saklayınP305 + P351+P338
    #
    # Therefore we MUST NOT require whitespace or a word
    # boundary before the initial "P".
    #
    # We only require:
    #
    #   P + exactly 3 digits
    #
    # followed optionally by:
    #
    #   + Pxxx
    #   + xxx
    #
    # =====================================================

    pattern = re.compile(
        r"P\s*\d{3}"
        r"(?:"
        r"\s*\+\s*"
        r"P?\s*\d{3}"
        r")*",
        flags=re.IGNORECASE
    )

    matches = pattern.findall(
        text
    )

    normalized = []

    for match in matches:

        code = (
            _normalize_precautionary_code(
                match
            )
        )

        if code:
            normalized.append(
                code
            )

    return _unique(
        normalized
    )


# =========================================================
# SIGNAL WORD
# =========================================================

def _find_signal_word(
    text: str
) -> str | None:

    if not text:
        return None

    match = re.search(
        r"(?:"
        r"Uyarı\s+kelimesi"
        r"|Signal\s+word"
        r")"
        r"\s*:?\s*"
        r"(Tehlike|Dikkat|Danger|Warning)",
        text,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1)

    folded = value.casefold()

    if folded == "tehlike":
        return "Tehlike"

    if folded == "dikkat":
        return "Dikkat"

    if folded == "danger":
        return "Danger"

    if folded == "warning":
        return "Warning"

    return value


# =========================================================
# GHS CODES
# =========================================================

def _find_ghs_codes(
    text: str
) -> list[str]:

    if not text:
        return []

    matches = re.findall(
        r"GHS\s*0?([1-9])",
        text,
        flags=re.IGNORECASE
    )

    return _unique(
        [
            f"GHS0{value}"
            for value in matches
        ]
    )


# =========================================================
# SECTION 2 PARSER
# =========================================================

def parse_section_2(
    section_text: str
) -> dict:

    if not section_text:

        return {
            "hazard_codes": [],
            "precautionary_codes": [],
            "signal_word": None,
            "ghs_codes": [],
        }

    hazard_codes = (
        _find_hazard_codes(
            section_text
        )
    )

    precautionary_codes = (
        _find_precautionary_codes(
            section_text
        )
    )

    signal_word = (
        _find_signal_word(
            section_text
        )
    )

    ghs_codes = (
        _find_ghs_codes(
            section_text
        )
    )

    return {
        "hazard_codes":
            hazard_codes,

        "precautionary_codes":
            precautionary_codes,

        "signal_word":
            signal_word,

        "ghs_codes":
            ghs_codes,
    }