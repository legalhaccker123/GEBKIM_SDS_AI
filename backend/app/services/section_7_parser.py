import re


# =========================================================
# EMPTY RESULT
# =========================================================

def _empty_result() -> dict:
    return {
        "handling_precautions": [],
        "storage_conditions": [],
        "incompatible_materials": [],
        "fire_explosion_precautions": [],
        "specific_end_use": None,
        "raw_subsection_7_1": None,
        "raw_subsection_7_2": None,
        "raw_subsection_7_3": None,
    }


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

        key = value.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def _remove_repeated_page_headers(
    text: str | None
) -> str:

    """
    Removes repeated PDF page header / footer material from
    structured Section 7 values.

    IMPORTANT:
    Raw subsection values are NOT modified by this function.
    It is used only while generating structured fields.

    This is deliberately generic:
    - no manufacturer names
    - no product names
    - no SDS-specific identifiers
    """

    if not text:
        return ""

    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # -----------------------------------------------------
    # PAGE MARKERS
    # -----------------------------------------------------

    text = re.sub(
        r"(?im)^\s*---\s*PAGE\s+\d+\s*---\s*$",
        "",
        text
    )

    text = re.sub(
        r"(?im)^\s*Sayfa\s+No\s*:\s*\d+\s*/\s*\d+\s*$",
        "",
        text
    )

    text = re.sub(
        r"(?im)^\s*Sayfa\s+\d+\s*/\s*\d+\s*$",
        "",
        text
    )

    text = re.sub(
        r"(?im)^\s*Page\s+\d+\s*(?:of|/)\s*\d+\s*$",
        "",
        text
    )

    # -----------------------------------------------------
    # MULTILINE SDS HEADER BLOCK
    #
    # Common structure:
    #
    #   GÜVENLİK BİLGİ FORMU
    #   regulation text...
    #   PRODUCT NAME
    #   Düzenleme Sayısı...
    #   Hazırlama Tarihi...
    #   www.company...
    #
    # We only remove the block when an SDS heading and
    # a nearby URL are both present. This keeps the rule
    # generic and prevents arbitrary document text from
    # being deleted.
    # -----------------------------------------------------

    lines = text.split("\n")

    cleaned_lines = []

    index = 0

    while index < len(lines):

        current_line = lines[index]

        if re.search(
            r"\b(?:"
            r"GÜVENLİK\s+BİLGİ\s+FORMU"
            r"|SAFETY\s+DATA\s+SHEET"
            r")\b",
            current_line,
            flags=re.IGNORECASE
        ):

            lookahead_end = min(
                len(lines),
                index + 15
            )

            url_index = None

            for probe_index in range(
                index,
                lookahead_end
            ):

                if re.search(
                    r"(?:"
                    r"https?://"
                    r"|www\."
                    r")",
                    lines[probe_index],
                    flags=re.IGNORECASE
                ):

                    url_index = probe_index
                    break

            if url_index is not None:

                # Remove the whole repeated page header.

                index = (
                    url_index
                    + 1
                )

                continue

        cleaned_lines.append(
            current_line
        )

        index += 1

    text = "\n".join(
        cleaned_lines
    )

    # -----------------------------------------------------
    # STANDALONE HEADER / FOOTER LINES
    # -----------------------------------------------------

    standalone_patterns = [

        r"^\s*GÜVENLİK\s+BİLGİ\s+FORMU\s*$",

        r"^\s*SAFETY\s+DATA\s+SHEET\s*$",

        r"^\s*Düzenleme\s+Sayısı\s*:.*$",

        r"^\s*Düzenleme\s+No\.?\s*:.*$",

        r"^\s*Revizyon\s+Numarası\s*:.*$",

        r"^\s*Revision\s+(?:Number|No\.?)\s*:.*$",

        r"^\s*Form\s+No\s*:.*$",

        r"^\s*Hazırlama\s+Tarihi\s*:.*$",

        r"^\s*Hazırlanma\s+Tarihi\s*:.*$",

        r"^\s*Preparation\s+Date\s*:.*$",

        r"^\s*Revision\s+Date\s*:.*$",

        r"^\s*Revizyon\s+Tarihi\s*:.*$",

        r"^\s*Yeniden\s+Düzenlenme\s+ve\s+Yayın\s+Tarihi\s*:.*$",

        r"^\s*Yeniden\s+Düzenleme\s+ve\s+Yayın\s+Tarihi\s*:.*$",

        r"^\s*(?:https?://|www\.)\S+.*$",
    ]

    result_lines = []

    for line in text.split("\n"):

        remove_line = False

        for pattern in standalone_patterns:

            if re.search(
                pattern,
                line,
                flags=re.IGNORECASE
            ):

                remove_line = True
                break

        if not remove_line:

            result_lines.append(
                line
            )

    text = "\n".join(
        result_lines
    )

    return text


def _flatten(
    text: str | None
) -> str:

    if not text:
        return ""

    text = _remove_repeated_page_headers(
        text
    )

    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\s*\n\s*",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def _clean_value(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = _flatten(
        value
    )

    # -----------------------------------------------------
    # PAGE MARKERS — defensive second pass
    # -----------------------------------------------------

    value = re.sub(
        r"---\s*PAGE\s+\d+\s*---",
        " ",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"\bSayfa\s+No\s*:\s*\d+\s*/\s*\d+\b",
        " ",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"\bSayfa\s+\d+\s*/\s*\d+\b",
        " ",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"\bPage\s+\d+\s*(?:of|/)\s*\d+\b",
        " ",
        value,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # SYMBOL NOISE
    # -----------------------------------------------------

    value = re.sub(
        r"[ꞏ▤▪■]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    value = value.strip(
        " :-–—•·"
    )

    return value or None


def _is_meaningful(
    value: str | None
) -> bool:

    if not value:
        return False

    cleaned = _clean_value(
        value
    )

    if not cleaned:
        return False

    if len(cleaned) < 12:
        return False

    words = cleaned.split()

    if len(words) < 3:
        return False

    return True


# =========================================================
# REGEX LABEL HELPERS
# =========================================================

def _label_group(
    labels: list[str]
) -> str:

    return (
        "(?:"
        + "|".join(labels)
        + ")"
    )


def _extract_after_labels(
    text: str,
    labels: list[str],
    stop_labels: list[str] | None = None
) -> str | None:

    if not text:
        return None

    flat = _flatten(
        text
    )

    if not flat:
        return None

    label_pattern = (
        _label_group(
            labels
        )
    )

    match = re.search(
        label_pattern,
        flat,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    start = match.end()

    remainder = (
        flat[start:]
        .lstrip(" :-–—•·")
    )

    if not remainder:
        return None

    if stop_labels:

        stop_pattern = (
            _label_group(
                stop_labels
            )
        )

        stop_match = re.search(
            stop_pattern,
            remainder,
            flags=re.IGNORECASE
        )

        if stop_match:

            remainder = (
                remainder[
                    :stop_match.start()
                ]
            )

    value = _clean_value(
        remainder
    )

    if not _is_meaningful(
        value
    ):

        return None

    return value


# =========================================================
# SUBSECTION SPLITTER
# =========================================================

SUBSECTION_PATTERN = re.compile(
    r"(?<!\d)"
    r"7\s*\.\s*([123])"
    r"\s*\.?"
    r"(?!\d)",
    flags=re.IGNORECASE
)


def _split_section_7_subsections(
    section_text: str
) -> dict[str, str | None]:

    result = {
        "7.1": None,
        "7.2": None,
        "7.3": None,
    }

    if not section_text:
        return result

    matches = list(
        SUBSECTION_PATTERN.finditer(
            section_text
        )
    )

    if not matches:
        return result

    selected = []

    last_number = 0

    for match in matches:

        try:

            number = int(
                match.group(1)
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        if number <= last_number:
            continue

        if number > 3:
            continue

        selected.append(
            (
                number,
                match
            )
        )

        last_number = number

        if number == 3:
            break

    if not selected:
        return result

    for index, item in enumerate(
        selected
    ):

        number, match = item

        start = match.start()

        if (
            index + 1
            < len(selected)
        ):

            end = (
                selected[
                    index + 1
                ][1].start()
            )

        else:

            end = len(
                section_text
            )

        raw = (
            section_text[
                start:end
            ]
            .strip()
        )

        result[
            f"7.{number}"
        ] = (
            raw
            if raw
            else None
        )

    return result


# =========================================================
# REMOVE SUBSECTION HEADER
# =========================================================

def _remove_subsection_number(
    text: str | None,
    subsection_number: int
) -> str:

    if not text:
        return ""

    text = re.sub(
        rf"^\s*"
        rf"7\s*\.\s*{subsection_number}"
        rf"\s*\.?\s*",
        "",
        text,
        count=1,
        flags=re.IGNORECASE
    )

    return text.strip()


# =========================================================
# 7.1 — HANDLING
# =========================================================

HANDLING_VALUE_LABELS = [

    r"Güvenli\s+elleçleme\s+için\s+tavsiye",

    r"Elleçleme\s+için\s+tavsiye",

    r"Güvenli\s+kullanım\s+için\s+tavsiye",

    r"Güvenli\s+Elleçleme\s+İçin\s+Uyarılar",

    r"Advice\s+on\s+safe\s+handling",

    r"Precautions\s+for\s+safe\s+handling",

    r"Safe\s+handling\s+advice",
]


HANDLING_HEADING_LABELS = [

    r"Güvenli\s+elleçleme\s+için\s+önlemler",

    r"Precautions\s+for\s+safe\s+handling",
]


HYGIENE_LABELS = [

    r"Genel\s+hijyen\s+hususları",

    r"Genel\s+hijyen\s+önlemleri",

    r"Genel\s+Mesleki\s+Hijyen\s+İle\s+İlgili\s+Tavsiyeler",

    r"Hijyen\s+önlemleri",

    r"General\s+hygiene\s+considerations",

    r"Hygiene\s+measures",
]


FIRE_LABELS = [

    r"Yangın\s+ve\s+patlamadan\s+korunmak\s+için\s+uyarılar",

    r"Yangın\s+ve\s+patlamadan\s+korunma\s+için\s+uyarılar",

    r"Yangın\s+ve\s+patlamadan\s+korunma",

    r"Yangın\s+ve\s+patlama\s+önlemleri",

    r"Yangın\s+ve\s+patlama\s+tehlikelerine\s+karşı\s+önlemler",

    r"Information\s+about\s+fire\s*[-–—]\s*and\s+explosion\s+protection",

    r"Advice\s+on\s+protection\s+against\s+fire\s+and\s+explosion",

    r"Advice\s+on\s+protection\s+against\s+fire",

    r"Fire\s+and\s+explosion\s+protection",
]


HANDLING_STOP_LABELS = (
    HYGIENE_LABELS
    + FIRE_LABELS
    + [
        r"Madde\s+veya\s+Karışımların\s+Uyuşmazlıkları",
        r"Çevre\s+İle\s+İlgili\s+Uyarılar",
        r"Ek\s+Uyarılar",
    ]
)


def _parse_handling_precautions(
    subsection_text: str | None
) -> list[str]:

    if not subsection_text:
        return []

    body = _remove_subsection_number(
        subsection_text,
        1
    )

    values = []

    handling = _extract_after_labels(
        body,
        HANDLING_VALUE_LABELS,
        HANDLING_STOP_LABELS
    )

    if handling:

        values.append(
            handling
        )

    hygiene = _extract_after_labels(
        body,
        HYGIENE_LABELS,
        FIRE_LABELS
    )

    if hygiene:

        values.append(
            hygiene
        )

    if not values:

        fallback = _flatten(
            body
        )

        for heading in HANDLING_HEADING_LABELS:

            fallback = re.sub(
                heading,
                " ",
                fallback,
                count=1,
                flags=re.IGNORECASE
            )

        fallback = _clean_value(
            fallback
        )

        if _is_meaningful(
            fallback
        ):

            values.append(
                fallback
            )

    return _unique(
        values
    )


# =========================================================
# 7.1 — FIRE / EXPLOSION
# =========================================================

def _parse_fire_explosion_precautions(
    subsection_text: str | None
) -> list[str]:

    if not subsection_text:
        return []

    value = _extract_after_labels(
        subsection_text,
        FIRE_LABELS,
        (
            HYGIENE_LABELS
            + [
                r"7\s*\.\s*1\s*\.\s*1\s*\.\s*2",
                r"Madde\s+veya\s+Karışımların\s+Uyuşmazlıkları",
                r"Çevre\s+İle\s+İlgili\s+Uyarılar",
            ]
        )
    )

    if not value:
        return []

    return [
        value
    ]


# =========================================================
# 7.2 — STORAGE
# =========================================================

STORAGE_VALUE_LABELS = [

    r"Depolama\s+Koşulları",

    r"Depolama\s+Şartları",

    r"Saklama\s+Koşulları",

    r"Saklama\s+Şartları",

    r"Further\s+information\s+about\s+storage\s+conditions",

    r"Storage\s+conditions",

    r"Conditions\s+for\s+safe\s+storage",

    r"Requirements\s+for\s+storage\s+areas\s+and\s+containers",
]


STORAGE_HEADING_LABELS = [

    r"Uyuşmazlıkları\s+da\s+içeren\s+güvenli\s+depolama\s+için\s+koşullar",

    r"Uyuşmazlıkları\s+da\s+içeren\s+güvenli\s+depolama\s+koşulları",

    r"Conditions\s+for\s+safe\s+storage,\s+including\s+any\s+incompatibilities",
]


STORAGE_CLASS_LABELS = [

    r"Alman\s+depolama\s+sınıfı(?:\s*\(TRGS\s*510\))?",

    r"Depolama\s+sınıfı",

    r"Storage\s+class",
]


INCOMPATIBLE_LABELS = [

    r"Uyumsuz\s+Maddeler",

    r"Uyumsuz\s+malzemeler",

    r"Uyuşmayan\s+malzemeler",

    r"Madde\s+veya\s+Karışımların\s+Uyuşmazlıkları\s+İle\s+İlgili\s+Uyarılar",

    r"Birlikte\s+depolanmaması\s+gereken\s+malzemeler",

    r"Birlikte\s+depolamayın",

    r"Information\s+about\s+storage\s+in\s+one\s+common\s+storage\s+facility",

    r"Incompatible\s+materials",

    r"Materials\s+to\s+avoid",
]


STORAGE_STOP_LABELS = (
    STORAGE_CLASS_LABELS
    + INCOMPATIBLE_LABELS
    + [
        r"Ortak\s+Depolama\s+Şartları",
        r"Maksimum\s+Depolama\s+Süresi",
    ]
)


def _extract_storage_class(
    text: str
) -> str | None:

    if not text:
        return None

    flat = _flatten(
        text
    )

    match = re.search(
        r"\bDepolama\s+sınıfı"
        r"\s*:?\s*"
        r"("
        r"\d{1,3}"
        r"(?:\s*[-–—]\s*.*?)?"
        r")"
        r"(?="
        r"$"
        r"|Uyumsuz\s+malzemeler"
        r"|Uyumsuz\s+Maddeler"
        r"|Uyuşmayan\s+malzemeler"
        r"|Incompatible\s+materials"
        r")",
        flat,
        flags=re.IGNORECASE
    )

    if match:

        value = _clean_value(
            match.group(1)
        )

        if value:

            return (
                "Depolama sınıfı "
                + value
            )

    match = re.search(
        r"\bStorage\s+class"
        r"\s*:?\s*"
        r"([^.;]+)",
        flat,
        flags=re.IGNORECASE
    )

    if match:

        value = _clean_value(
            match.group(1)
        )

        if value:

            return (
                "Storage class "
                + value
            )

    return None


def _parse_storage_conditions(
    subsection_text: str | None
) -> list[str]:

    if not subsection_text:
        return []

    body = _remove_subsection_number(
        subsection_text,
        2
    )

    values = []

    storage = _extract_after_labels(
        body,
        STORAGE_VALUE_LABELS,
        STORAGE_STOP_LABELS
    )

    if storage:

        values.append(
            storage
        )

    storage_class = (
        _extract_storage_class(
            body
        )
    )

    if storage_class:

        values.append(
            storage_class
        )

    if not values:

        fallback = _flatten(
            body
        )

        for heading in STORAGE_HEADING_LABELS:

            fallback = re.sub(
                heading,
                " ",
                fallback,
                count=1,
                flags=re.IGNORECASE
            )

        fallback = _clean_value(
            fallback
        )

        if _is_meaningful(
            fallback
        ):

            values.append(
                fallback
            )

    return _unique(
        values
    )


# =========================================================
# 7.2 — INCOMPATIBLE MATERIALS
# =========================================================

def _parse_incompatible_materials(
    subsection_text: str | None
) -> list[str]:

    if not subsection_text:
        return []

    value = _extract_after_labels(
        subsection_text,
        INCOMPATIBLE_LABELS,
        (
            STORAGE_CLASS_LABELS
            + [
                r"7\s*\.\s*3",
                r"Belirli\s+Son\s+Kullanımlar",
                r"Specific\s+end\s+uses?",
            ]
        )
    )

    if not value:
        return []

    return [
        value
    ]


# =========================================================
# 7.3 — SPECIFIC END USE
# =========================================================

SPECIFIC_USE_VALUE_LABELS = [

    r"Spesifik\s+kullanım\s*\(lar\)",

    r"Spesifik\s+kullanımlar",

    r"Specific\s+end\s+use\s*\(s\)",

    r"Specific\s+end\s+uses",

    r"Specific\s+use\s*\(s\)",
]


SPECIFIC_USE_HEADING_LABELS = [

    r"Belirli\s+son\s+kullanım\s*\(lar\)",

    r"Belirli\s+son\s+kullanımlar",

    r"Belirli\s+Son\s+Kullanımlar",

    r"Specific\s+end\s+use\s*\(s\)",

    r"Specific\s+end\s+uses",
]


SPECIFIC_USE_STOP_LABELS = [

    r"Tanımlanan\s+Kullanımlar",

    r"Tanımlanmış\s+Kullanımlar",

    r"Risk\s+Yönetim\s+Yöntemleri",

    r"Risk\s+Yönetim\s+Önlemleri",

    r"Identified\s+uses",

    r"Risk\s+management\s+measures",

    r"\bRMM\b",
]


def _remove_known_page_noise(
    text: str
) -> str:

    return _remove_repeated_page_headers(
        text
    )


def _parse_specific_end_use(
    subsection_text: str | None
) -> str | None:

    if not subsection_text:
        return None

    body = _remove_subsection_number(
        subsection_text,
        3
    )

    value = _extract_after_labels(
        body,
        SPECIFIC_USE_VALUE_LABELS,
        SPECIFIC_USE_STOP_LABELS
    )

    if value:

        return value

    fallback = (
        _remove_known_page_noise(
            body
        )
    )

    for heading in SPECIFIC_USE_HEADING_LABELS:

        fallback = re.sub(
            heading,
            " ",
            fallback,
            count=1,
            flags=re.IGNORECASE
        )

    fallback = _clean_value(
        fallback
    )

    if not _is_meaningful(
        fallback
    ):

        return None

    return fallback


# =========================================================
# SEMANTIC FALLBACKS
# =========================================================

def _semantic_fallback_handling(
    whole_section: str
) -> list[str]:

    value = _extract_after_labels(
        whole_section,
        HANDLING_VALUE_LABELS,
        (
            HYGIENE_LABELS
            + STORAGE_VALUE_LABELS
            + STORAGE_HEADING_LABELS
        )
    )

    if value:

        return [
            value
        ]

    return []


def _semantic_fallback_storage(
    whole_section: str
) -> list[str]:

    values = []

    value = _extract_after_labels(
        whole_section,
        STORAGE_VALUE_LABELS,
        (
            STORAGE_CLASS_LABELS
            + INCOMPATIBLE_LABELS
            + SPECIFIC_USE_VALUE_LABELS
            + SPECIFIC_USE_HEADING_LABELS
        )
    )

    if value:

        values.append(
            value
        )

    storage_class = (
        _extract_storage_class(
            whole_section
        )
    )

    if storage_class:

        values.append(
            storage_class
        )

    return _unique(
        values
    )


def _semantic_fallback_specific_use(
    whole_section: str
) -> str | None:

    return _extract_after_labels(
        whole_section,
        SPECIFIC_USE_VALUE_LABELS,
        SPECIFIC_USE_STOP_LABELS
    )


# =========================================================
# FINAL STRUCTURED VALUE CLEANER
# =========================================================

def _clean_structured_list(
    values: list[str]
) -> list[str]:

    cleaned_values = []

    for value in values:

        cleaned = _clean_value(
            value
        )

        if not _is_meaningful(
            cleaned
        ):

            continue

        cleaned_values.append(
            cleaned
        )

    return _unique(
        cleaned_values
    )


# =========================================================
# PUBLIC PARSER
# =========================================================

def parse_section_7(
    section_text: str
) -> dict:

    if not section_text:

        return _empty_result()

    result = _empty_result()

    # =====================================================
    # 1. SPLIT RAW 7.1 / 7.2 / 7.3
    #
    # Raw source is deliberately preserved unchanged.
    # =====================================================

    subsections = (
        _split_section_7_subsections(
            section_text
        )
    )

    raw_7_1 = (
        subsections.get(
            "7.1"
        )
    )

    raw_7_2 = (
        subsections.get(
            "7.2"
        )
    )

    raw_7_3 = (
        subsections.get(
            "7.3"
        )
    )

    result[
        "raw_subsection_7_1"
    ] = raw_7_1

    result[
        "raw_subsection_7_2"
    ] = raw_7_2

    result[
        "raw_subsection_7_3"
    ] = raw_7_3

    # =====================================================
    # 2. HANDLING — 7.1
    # =====================================================

    handling_precautions = (
        _parse_handling_precautions(
            raw_7_1
        )
    )

    if not handling_precautions:

        handling_precautions = (
            _semantic_fallback_handling(
                section_text
            )
        )

    result[
        "handling_precautions"
    ] = _clean_structured_list(
        handling_precautions
    )

    # =====================================================
    # 3. STORAGE — 7.2
    # =====================================================

    storage_conditions = (
        _parse_storage_conditions(
            raw_7_2
        )
    )

    if not storage_conditions:

        storage_conditions = (
            _semantic_fallback_storage(
                section_text
            )
        )

    result[
        "storage_conditions"
    ] = _clean_structured_list(
        storage_conditions
    )

    # =====================================================
    # 4. INCOMPATIBLE MATERIALS — 7.2
    # =====================================================

    incompatible_materials = (
        _parse_incompatible_materials(
            raw_7_2
        )
    )

    result[
        "incompatible_materials"
    ] = _clean_structured_list(
        incompatible_materials
    )

    # =====================================================
    # 5. FIRE / EXPLOSION — 7.1
    # =====================================================

    fire_explosion_precautions = (
        _parse_fire_explosion_precautions(
            raw_7_1
        )
    )

    result[
        "fire_explosion_precautions"
    ] = _clean_structured_list(
        fire_explosion_precautions
    )

    # =====================================================
    # 6. SPECIFIC END USE — 7.3
    # =====================================================

    specific_end_use = (
        _parse_specific_end_use(
            raw_7_3
        )
    )

    if not specific_end_use:

        specific_end_use = (
            _semantic_fallback_specific_use(
                section_text
            )
        )

    result[
        "specific_end_use"
    ] = _clean_value(
        specific_end_use
    )

    return result