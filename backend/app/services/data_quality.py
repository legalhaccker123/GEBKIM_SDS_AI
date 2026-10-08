import re


# =========================================================
# PLACEHOLDER / INVALID VALUES
# =========================================================

INVALID_EXACT_VALUES = {
    "",
    ":",
    "::",
    "-",
    "--",
    "---",
    "—",
    "_",
    "/",
    "\\",
    ".",
    "..",
    "...",
}


def normalize_quality_text(
    value: str | None
) -> str | None:

    if value is None:
        return None

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def is_placeholder_value(
    value: str | None
) -> bool:

    value = normalize_quality_text(
        value
    )

    if value is None:
        return True

    if value in INVALID_EXACT_VALUES:
        return True

    if re.fullmatch(
        r"[:\-\–\—\._/\s]+",
        value
    ):
        return True

    return False


def is_meaningful_value(
    value: str | None
) -> bool:

    return not is_placeholder_value(
        value
    )


# =========================================================
# KNOWN "NO DATA / NOT APPLICABLE" VALUES
#
# These are meaningful SDS statements.
# They are NOT parser failures.
# =========================================================

NO_DATA_MARKERS = [
    "bilgi yok",
    "bilgi bulunmamaktadır",
    "veri yok",
    "veri yoktur",
    "uygulanabilir değil",
    "uygulanamaz",
    "uygun veri yoktur",
    "mevcut değildir",
    "belirlenmemiş",
    "bilinmiyor",
    "not available",
    "no data available",
    "not applicable",
    "not determined",
]


def is_explicit_no_data_value(
    value: str | None
) -> bool:

    value = normalize_quality_text(
        value
    )

    if not value:
        return False

    lowered = value.lower()

    return any(
        marker in lowered
        for marker in NO_DATA_MARKERS
    )


# =========================================================
# MANUFACTURER QUALITY
# =========================================================

SUSPICIOUS_MANUFACTURER_VALUES = {
    "bilgisi",
    "adı",
    "firma",
    "firma bilgisi",
    "şirket",
    "şirket bilgisi",
    "üretici",
    "tedarikçi",
    "manufacturer",
    "supplier",
    "company",
}


def is_suspicious_manufacturer(
    value: str | None
) -> bool:

    value = normalize_quality_text(
        value
    )

    if not value:
        return True

    lowered = value.lower()

    if lowered in SUSPICIOUS_MANUFACTURER_VALUES:
        return True

    if len(value) < 4:
        return True

    return False


# =========================================================
# COLLECTION QUALITY
# =========================================================

def meaningful_list(
    values: list[str] | None
) -> list[str]:

    if not values:
        return []

    result = []

    for value in values:

        if not is_meaningful_value(
            value
        ):
            continue

        cleaned = normalize_quality_text(
            value
        )

        if cleaned:
            result.append(
                cleaned
            )

    return result


def count_meaningful_values(
    values: list[str | None]
) -> int:

    return sum(
        1
        for value in values
        if is_meaningful_value(
            value
        )
    )