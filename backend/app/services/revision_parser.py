import re
import unicodedata

from datetime import date


# =========================================================
# MONTH MAP
# =========================================================

MONTH_MAP = {

    # Turkish
    "oca": 1,
    "ocak": 1,

    "sub": 2,
    "subat": 2,

    "mar": 3,
    "mart": 3,

    "nis": 4,
    "nisan": 4,

    "may": 5,
    "mayis": 5,

    "haz": 6,
    "haziran": 6,

    "tem": 7,
    "temmuz": 7,

    "agu": 8,
    "agustos": 8,

    "eyl": 9,
    "eylul": 9,

    "eki": 10,
    "ekim": 10,

    "kas": 11,
    "kasim": 11,

    "ara": 12,
    "aralik": 12,

    # English
    "jan": 1,
    "january": 1,

    "feb": 2,
    "february": 2,

    "mar": 3,
    "march": 3,

    "apr": 4,
    "april": 4,

    "may": 5,

    "jun": 6,
    "june": 6,

    "jul": 7,
    "july": 7,

    "aug": 8,
    "august": 8,

    "sep": 9,
    "sept": 9,
    "september": 9,

    "oct": 10,
    "october": 10,

    "nov": 11,
    "november": 11,

    "dec": 12,
    "december": 12,
}


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


def _normalize_word(
    value: str
) -> str:

    """
    Turkish / Unicode month names are converted
    to a comparison-safe form.

    Examples:

        Ağu      -> agu
        Ağustos  -> agustos
        Şub      -> sub
        Mayıs    -> mayis
    """

    value = value.casefold()

    value = value.replace(
        "ı",
        "i"
    )

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    value = re.sub(
        r"[^a-z]",
        "",
        value
    )

    return value


def _make_iso_date(
    year: int,
    month: int,
    day: int
) -> str | None:

    try:

        parsed_date = date(
            year,
            month,
            day
        )

        return parsed_date.isoformat()

    except ValueError:

        return None


# =========================================================
# DATE PARSER
# =========================================================

def _parse_date_value(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = _clean_text(
        value
    )

    if not value:
        return None

    # -----------------------------------------------------
    # FORMAT 1
    #
    # 2021-07-15
    # 2021/07/15
    # 2021.07.15
    # -----------------------------------------------------

    match = re.search(
        r"(?<!\d)"
        r"(\d{4})"
        r"[-/.]"
        r"(\d{1,2})"
        r"[-/.]"
        r"(\d{1,2})"
        r"(?!\d)",
        value
    )

    if match:

        year = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        day = int(
            match.group(3)
        )

        result = _make_iso_date(
            year,
            month,
            day
        )

        if result:
            return result

    # -----------------------------------------------------
    # FORMAT 2
    #
    # 15-07-2021
    # 15/07/2021
    # 15.07.2021
    # 15.5.2018
    # -----------------------------------------------------

    match = re.search(
        r"(?<!\d)"
        r"(\d{1,2})"
        r"[-/.]"
        r"(\d{1,2})"
        r"[-/.]"
        r"(\d{4})"
        r"(?!\d)",
        value
    )

    if match:

        day = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

        result = _make_iso_date(
            year,
            month,
            day
        )

        if result:
            return result

    # -----------------------------------------------------
    # FORMAT 3
    #
    # 15-Tem-2021
    # 15-Ağu-2021
    # 15 Temmuz 2021
    # 15-Jul-2021
    # -----------------------------------------------------

    match = re.search(
        r"(?<!\d)"
        r"(\d{1,2})"
        r"\s*[-./ ]\s*"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)"
        r"\s*[-./ ]\s*"
        r"(\d{4})"
        r"(?!\d)",
        value
    )

    if match:

        day = int(
            match.group(1)
        )

        month_text = _normalize_word(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

        month = MONTH_MAP.get(
            month_text
        )

        if month:

            result = _make_iso_date(
                year,
                month,
                day
            )

            if result:
                return result

    # -----------------------------------------------------
    # FORMAT 4
    #
    # July 15, 2021
    # Temmuz 15, 2021
    # -----------------------------------------------------

    match = re.search(
        r"(?<![A-Za-z])"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)"
        r"\s+"
        r"(\d{1,2})"
        r"(?:st|nd|rd|th)?"
        r"\s*,?\s*"
        r"(\d{4})",
        value,
        flags=re.IGNORECASE
    )

    if match:

        month_text = _normalize_word(
            match.group(1)
        )

        day = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

        month = MONTH_MAP.get(
            month_text
        )

        if month:

            result = _make_iso_date(
                year,
                month,
                day
            )

            if result:
                return result

    return None


# =========================================================
# LABELED DATE EXTRACTION
# =========================================================

def _find_date_after_labels(
    text: str,
    labels: list[str]
) -> str | None:

    """
    Searches for a date only after an explicit
    semantic label.

    This avoids treating unrelated dates as
    revision dates.
    """

    if not text:
        return None

    for label in labels:

        pattern = re.compile(
            rf"(?is)"
            rf"{label}"
            rf"\s*:?\s*"
            rf"("
            rf"\d{{1,2}}\s*[-./ ]\s*"
            rf"[A-Za-zÇĞİÖŞÜçğıöşü]+\s*[-./ ]\s*"
            rf"\d{{4}}"
            rf"|"
            rf"\d{{4}}[-/.]\d{{1,2}}[-/.]\d{{1,2}}"
            rf"|"
            rf"\d{{1,2}}[-/.]\d{{1,2}}[-/.]\d{{4}}"
            rf"|"
            rf"[A-Za-zÇĞİÖŞÜçğıöşü]+\s+"
            rf"\d{{1,2}}(?:st|nd|rd|th)?"
            rf"\s*,?\s*\d{{4}}"
            rf")"
        )

        match = pattern.search(
            text
        )

        if not match:
            continue

        parsed = _parse_date_value(
            match.group(1)
        )

        if parsed:
            return parsed

    return None


# =========================================================
# REVISION DATE
# =========================================================

def _find_revision_date(
    text: str
) -> str | None:

    """
    Finds the date representing the current
    revision / update of the SDS.

    Specific labels are intentionally checked before
    short / generic revision labels.
    """

    labels = [

        # =================================================
        # TURKISH — explicit reissue / update labels
        # =================================================

        r"Yeniden\s+Düzenlenme\s+ve\s+Yayın\s+Tarihi",

        r"Yeniden\s+Düzenleme\s+ve\s+Yayın\s+Tarihi",

        r"Yeniden\s+Düzenlenme\s+ve\s+Yayım\s+Tarihi",

        r"Yeniden\s+Düzenleme\s+ve\s+Yayım\s+Tarihi",

        r"Yeniden\s+Düzenlenme\s+Tarihi",

        r"Yeniden\s+Düzenleme\s+Tarihi",

        r"Yeni\s+Düzenlenme\s+Tarihi",

        r"Yeni\s+Düzenleme\s+Tarihi",

        r"Güncelleme\s+Tarihi",

        r"Gözden\s+Geçirilme\s+Tarihi",

        r"Tarih\s*/\s*Gözden\s+Geçirilme\s+Tarihi",

        # =================================================
        # TURKISH — revision labels
        # =================================================

        r"Revizyon\s+Tarihi",

        r"Revizyon\s+tarihi",

        # =================================================
        # ENGLISH
        # =================================================

        r"Revision\s+date",

        r"Date\s+of\s+revision",

        r"Date\s+of\s+last\s+revision",

        r"Last\s+revision",

        r"Revised\s+on",

        r"Updated\s+on",

        r"Update\s+date",

        r"Date\s+of\s+update",

        # =================================================
        # GENERIC REVISION LABEL
        #
        # Revision: 31.01.2024
        # Revizyon: 31.01.2024
        #
        # Revision Number / Revision No are excluded.
        # =================================================

        r"Revision"
        r"(?!\s+(?:number|no\.?))",

        r"Revizyon"
        r"(?!\s+(?:numarası|numarasi|no\.?))",
    ]

    return _find_date_after_labels(
        text,
        labels
    )


# =========================================================
# PREPARATION / ISSUE DATE
# =========================================================

def _find_preparation_date(
    text: str
) -> str | None:

    """
    Only explicit preparation / original issue
    labels are accepted.

    IMPORTANT:

        Yerine Geçme Tarihi
        Supersedes
        Replaces
        Printing date
        Baskı tarihi
        Yeniden düzenlenme tarihi

    are NOT automatically treated as preparation dates.
    """

    labels = [

        # Turkish
        r"Hazırlanma\s+Tarihi",

        r"Hazırlama\s+Tarihi",

        r"İlk\s+Hazırlanma\s+Tarihi",

        r"İlk\s+Düzenlenme\s+Tarihi",

        r"İlk\s+Düzenleme\s+Tarihi",

        r"Düzenlenme\s+Tarihi",

        r"Düzenleme\s+Tarihi",

        r"Yayın\s+Tarihi",

        r"Yayım\s+Tarihi",

        # English
        r"Preparation\s+date",

        r"Date\s+of\s+preparation",

        r"Issue\s+date",

        r"Date\s+of\s+issue",

        r"First\s+issue\s+date",
    ]

    return _find_date_after_labels(
        text,
        labels
    )


# =========================================================
# VERSION / REVISION NUMBER
# =========================================================

def _find_version(
    text: str
) -> str | None:

    if not text:
        return None

    # -----------------------------------------------------
    # IMPORTANT
    #
    # Specific patterns MUST come before generic patterns.
    #
    # Example:
    #
    #     Version number 13
    #
    # must return:
    #
    #     13
    #
    # and not:
    #
    #     number
    #
    #
    # Turkish SDS examples:
    #
    #     Düzenleme Sayısı: 3.1
    #     Kaçıncı Düzenleme Olduğu: 02
    #     Revizyon Numarası: 3
    #
    # -----------------------------------------------------

    patterns = [

        # =================================================
        # TURKISH SDS EDITION / VERSION LABELS
        # =================================================

        (
            r"Kaçıncı\s+Düzenleme\s+Olduğu"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Düzenleme\s+Sayısı"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Düzenleme\s+Numarası"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Düzenleme\s+No\.?"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        # =================================================
        # TURKISH REVISION NUMBER
        # =================================================

        (
            r"Revizyon\s+Numarası"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Revizyon\s+No\.?"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        # =================================================
        # ENGLISH REVISION NUMBER
        # =================================================

        (
            r"Revision\s+Number"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Revision\s+No\.?"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        # =================================================
        # ENGLISH VERSION NUMBER
        # =================================================

        (
            r"Version\s+number"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Version\s+No\.?"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        # =================================================
        # GENERIC VERSION
        #
        # Version: 11.2
        #
        # Do NOT allow:
        #
        # Version number 13
        # =================================================

        (
            r"Version"
            r"(?!\s+(?:number|no\.?))"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        # =================================================
        # TURKISH VERSION
        # =================================================

        (
            r"Sürüm\s+Numarası"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Sürüm\s+No\.?"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),

        (
            r"Sürüm"
            r"\s*:?\s*"
            r"([A-Za-z0-9._\-]+)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if not match:
            continue

        value = (
            match.group(1)
            .strip()
        )

        if not value:
            continue

        # -------------------------------------------------
        # Defensive validation
        #
        # Prevent accidental capture of label words.
        # -------------------------------------------------

        invalid_values = {
            "number",
            "no",
            "numara",
            "numarası",
            "numarasi",
            "sayısı",
            "sayisi",
        }

        if (
            value.casefold()
            in invalid_values
        ):
            continue

        return value

    return None


# =========================================================
# PUBLIC PARSER
# =========================================================

def parse_revision_metadata(
    text: str
) -> dict:

    if not text:

        return {
            "preparation_date": None,
            "revision_date": None,
            "version": None,
        }

    revision_date = _find_revision_date(
        text
    )

    preparation_date = _find_preparation_date(
        text
    )

    version = _find_version(
        text
    )

    return {
        "preparation_date":
            preparation_date,

        "revision_date":
            revision_date,

        "version":
            version,
    }