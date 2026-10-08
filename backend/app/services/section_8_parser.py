import re


# =========================================================
# EMPTY RESULT
# =========================================================

def _empty_result() -> dict:
    return {
        "respiratory_protection": [],
        "hand_protection": [],
        "glove_materials": [],
        "glove_thickness": [],
        "eye_face_protection": [],
        "body_protection": [],
        "engineering_controls": [],
        "exposure_limits": [],
        "dnel": [],
        "pnec": [],
        "hygiene_measures": [],
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


def _clean_line(
    line: str
) -> str:

    if not line:
        return ""

    line = line.replace(
        "\uf0b3",
        "≥"
    )

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


# =========================================================
# PAGE HEADER / FOOTER CLEANING
# =========================================================

def _remove_repeated_page_headers(
    text: str
) -> str:

    """
    Removes repeated SDS page headers from parser working text.

    Raw SDS source is NOT modified in the database.

    Generic approach:
    - no manufacturer names
    - no product names
    - no SDS-specific codes
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

    lines = text.split("\n")

    cleaned_lines = []

    index = 0

    while index < len(lines):

        line = lines[index]

        # -------------------------------------------------
        # PAGE MARKER
        # -------------------------------------------------

        if re.match(
            r"^\s*---\s*PAGE\s+\d+\s*---\s*$",
            line,
            flags=re.IGNORECASE
        ):

            lookahead_end = min(
                len(lines),
                index + 18
            )

            has_sds_heading = False
            url_index = None

            for probe_index in range(
                index + 1,
                lookahead_end
            ):

                probe = lines[
                    probe_index
                ]

                if re.search(
                    r"\b(?:"
                    r"GÜVENLİK\s+BİLGİ\s+FORMU"
                    r"|SAFETY\s+DATA\s+SHEET"
                    r")\b",
                    probe,
                    flags=re.IGNORECASE
                ):

                    has_sds_heading = True

                if re.search(
                    r"(?:https?://|www\.)",
                    probe,
                    flags=re.IGNORECASE
                ):

                    url_index = probe_index
                    break

            if (
                has_sds_heading
                and url_index is not None
            ):

                index = (
                    url_index
                    + 1
                )

                continue

            # Even if full header was not found,
            # discard the page marker itself.

            index += 1
            continue

        cleaned_lines.append(
            line
        )

        index += 1

    text = "\n".join(
        cleaned_lines
    )

    # -----------------------------------------------------
    # STANDALONE HEADER / FOOTER LINES
    # -----------------------------------------------------

    patterns = [
        r"^\s*Sayfa\s+(?:No\s*:?\s*)?\d+\s*/\s*\d+\s*$",
        r"^\s*Page\s+\d+\s*(?:of|/)\s*\d+\s*$",

        r"^\s*GÜVENLİK\s+BİLGİ\s+FORMU\s*$",
        r"^\s*SAFETY\s+DATA\s+SHEET\s*$",

        r"^\s*Form\s+No\s*:.*$",

        r"^\s*Düzenleme\s+Sayısı\s*:.*$",
        r"^\s*Düzenleme\s+No\.?\s*:.*$",
        r"^\s*Revizyon\s+Numarası\s*:.*$",

        r"^\s*Hazırlama\s+Tarihi\s*:.*$",
        r"^\s*Hazırlanma\s+Tarihi\s*:.*$",

        r"^\s*Yeni\s+Düzenleme\s+Tarihi\s*:.*$",

        r"^\s*Yeniden\s+Düzenlenme"
        r"(?:\s+ve\s+(?:Yayın|Yayım))?"
        r"\s+Tarihi\s*:.*$",

        r"^\s*Yeniden\s+Düzenleme"
        r"(?:\s+ve\s+(?:Yayın|Yayım))?"
        r"\s+Tarihi\s*:.*$",

        r"^\s*Revision\s+Date\s*:.*$",
        r"^\s*Preparation\s+Date\s*:.*$",

        r"^\s*(?:https?://|www\.)\S+.*$",
    ]

    result = []

    for raw_line in text.splitlines():

        remove = False

        for pattern in patterns:

            if re.search(
                pattern,
                raw_line,
                flags=re.IGNORECASE
            ):

                remove = True
                break

        if not remove:

            result.append(
                raw_line
            )

    return "\n".join(
        result
    )


# =========================================================
# LINE NOISE
# =========================================================

def _is_noise_line(
    line: str
) -> bool:

    if not line:
        return True

    patterns = [
        r"^---\s*PAGE\s+\d+\s*---$",

        r"^PAGE\s+\d+",

        r"^Sayfa\s+(?:No\s*:?\s*)?\d+\s*/?\s*\d*",

        r"^Form\s+No",

        r"^GÜVENLİK\s+BİLGİ\s+FORMU",

        r"^SAFETY\s+DATA\s+SHEET",

        r"^Hazırlama\s+Tarihi",

        r"^Hazırlanma\s+Tarihi",

        r"^Yeni\s+Düzenleme\s+Tarihi",

        r"^Yeniden\s+Düzenleme",

        r"^Yeniden\s+Düzenlenme",

        r"^Kaçıncı\s+Düzenleme",

        r"^Düzenleme\s+Sayısı",

        r"^Revizyon\s+Numarası",

        r"^Revision\s+Date",

        r"^Preparation\s+Date",

        r"^https?://",

        r"^www\.",
    ]

    return any(
        re.search(
            pattern,
            line,
            flags=re.IGNORECASE
        )
        for pattern in patterns
    )


def _get_lines(
    text: str
) -> list[str]:

    result = []

    if not text:
        return result

    text = _remove_repeated_page_headers(
        text
    )

    for raw_line in text.splitlines():

        line = _clean_line(
            raw_line
        )

        if not line:
            continue

        if _is_noise_line(
            line
        ):
            continue

        result.append(
            line
        )

    return result


# =========================================================
# NORMALIZE TEXT
# =========================================================

def _normalize_text(
    text: str
) -> str:

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

    text = text.replace(
        "\uf0b3",
        "≥"
    )

    # -----------------------------------------------------
    # Remove repeated multi-line SDS headers BEFORE
    # flattening the PDF text.
    # -----------------------------------------------------

    text = _remove_repeated_page_headers(
        text
    )

    # -----------------------------------------------------
    # Defensive page marker cleanup
    # -----------------------------------------------------

    text = re.sub(
        r"---\s*PAGE\s+\d+\s*---",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bSayfa\s+(?:No\s*:?\s*)?"
        r"\d+\s*/\s*\d+\b",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bPage\s+\d+\s*(?:of|/)\s*\d+\b",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Remove repeated revision fragments
    # -----------------------------------------------------

    text = re.sub(
        r"\bRevizyon\s+tarihi\s+"
        r"\d{1,2}\s*[-./]\s*"
        r"[A-Za-zÇĞİÖŞÜçğıöşü]+\s*[-./]\s*"
        r"\d{4}",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bRevision\s+date\s*:?\s*"
        r"\d{1,2}\s*[-./]\s*"
        r"[A-Za-z]+\s*[-./]\s*"
        r"\d{4}",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# VALUE CLEANING
# =========================================================

def _clean_value(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    value = value.strip(
        " :-–—•·"
    )

    # -----------------------------------------------------
    # Fix PDF concatenation:
    #
    # eldivenlerUygun
    # ->
    # eldivenler Uygun
    # -----------------------------------------------------

    value = re.sub(
        r"(?<=[a-zçğıöşü])"
        r"(?=[A-ZÇĞİÖŞÜ])",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    # -----------------------------------------------------
    # Defensive removal of header fragments
    # -----------------------------------------------------

    contamination_patterns = [
        r"\bSayfa\s+(?:No\s*:?\s*)?\d+\s*/\s*\d+\b",
        r"\bPage\s+\d+\s*(?:of|/)\s*\d+\b",
        r"\bGÜVENLİK\s+BİLGİ\s+FORMU\b",
        r"\bSAFETY\s+DATA\s+SHEET\b",
    ]

    for pattern in contamination_patterns:

        value = re.sub(
            pattern,
            " ",
            value,
            flags=re.IGNORECASE
        )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    if value in {
        "",
        "-",
        "—",
        "/",
    }:

        return None

    return value


def _split_sentences(
    value: str | None
) -> list[str]:

    if not value:
        return []

    value = _clean_value(
        value
    )

    if not value:
        return []

    parts = re.split(
        r"(?<=[.!?])\s+"
        r"(?=[A-ZÇĞİÖŞÜ])",
        value
    )

    return _unique(
        [
            part.strip()
            for part in parts
            if part.strip()
        ]
    )


# =========================================================
# OPTIONAL SECTION NUMBER PREFIX
# =========================================================

PREFIX = (
    r"(?:"
    r"(?<!\d)"
    r"8"
    r"(?:\s*\.\s*\d+){1,4}"
    r"\s*\.?\s*"
    r"(?!\d)"
    r")?"
)


# =========================================================
# SEMANTIC LABELS
# =========================================================

ENGINEERING_LABELS = [
    PREFIX + r"Uygun\s+mühendislik\s+kontrolleri",
    PREFIX + r"Mühendislik\s+kontrolleri",
    PREFIX + r"Mühendislik\s+önlemleri",
    PREFIX + r"Teknik\s+kontroller",
    PREFIX + r"Appropriate\s+engineering\s+controls",
    PREFIX + r"Engineering\s+controls",
    PREFIX + r"Engineering\s+measures",
]


RESPIRATORY_LABELS = [
    PREFIX + r"Solunum\s+korunması",
    PREFIX + r"Solunum\s+sisteminin\s+korunması",
    PREFIX + r"Solunum\s+ile\s+ilgili\s+önlemler",
    PREFIX + r"Solunumun\s+korunması",
    PREFIX + r"Solunum\s+koruması",
    PREFIX + r"Respiratory\s+protection",
    PREFIX + r"Breathing\s+protection",
]


HAND_LABELS = [
    PREFIX + r"Ellerin\s+korunması",
    PREFIX + r"Elleri\s+koruma",
    PREFIX + r"El\s+koruması",
    PREFIX + r"El\s+korunması",
    PREFIX + r"Hand\s+protection",
]


EYE_LABELS = [
    PREFIX + r"Göz\s*/\s*yüz\s+korunması",
    PREFIX + r"Göz\s*/\s*yüz\s+koruması",
    PREFIX + r"Göz\s+ve\s+yüz\s+korunması",
    PREFIX + r"Göz\s+ve\s+yüz\s+koruması",
    PREFIX + r"Gözlerin\s*/\s*yüzün\s+korunması",
    PREFIX + r"Gözlerin\s+korunması",
    PREFIX + r"Gözleri\s+koruma",
    PREFIX + r"Göz\s+koruması",
    PREFIX + r"Eye\s*/\s*face\s+protection",
    PREFIX + r"Eye\s+and\s+face\s+protection",
    PREFIX + r"Eye\s+protection",
]


BODY_LABELS = [
    PREFIX + r"Cildin\s+ve\s+vücudun\s+korunması",
    PREFIX + r"Cilt\s+ve\s+vücudun\s+korunması",
    PREFIX + r"Deri\s+ve\s+vücudun\s+korunması",
    PREFIX + r"Cildin\s+korunması",
    PREFIX + r"Deri\s+korunması",
    PREFIX + r"Vücudun\s+korunması",
    PREFIX + r"Vücut\s+koruması",
    PREFIX + r"Skin\s+and\s+body\s+protection",
    PREFIX + r"Skin\s+protection",
    PREFIX + r"Body\s+protection",
]


HYGIENE_LABELS = [
    PREFIX + r"Genel\s+hijyen\s+hususları",
    PREFIX + r"Genel\s+hijyen\s+önlemleri",
    PREFIX + r"Sağlık\s+tedbirleri",
    PREFIX + r"Hijyen\s+önlemleri",
    PREFIX + r"General\s+hygiene\s+considerations",
    PREFIX + r"General\s+hygiene\s+measures",
    PREFIX + r"Hygiene\s+measures",
]


ENVIRONMENT_LABELS = [
    PREFIX + r"Çevresel\s+maruziyet\s+kontrolleri",
    PREFIX + r"Çevresel\s+maruz\s+kalma\s+kontrolleri",
    PREFIX + r"Environmental\s+exposure\s+controls",
]


EXPOSURE_LIMIT_LABELS = [
    r"Maruz\s+Kalma\s+Limitleri",
    r"Maruziyet\s+Limitleri",
    r"Mesleki\s+maruziyet\s+limitleri",
    r"Occupational\s+exposure\s+limits",
    r"Exposure\s+limits",
]


DNEL_LABELS = [
    r"İşçiler\s+için\s+DNELs?",
    r"Genel\s+nüfus\s+için\s+DNELs?",
    r"\bDNELs?\b",
    r"Derived\s+No[-\s]*Effect\s+Level",
]


PNEC_LABELS = [
    r"Öngörülen\s+Etkisiz\s+Konsantrasyon\s*\(PNEC\)",
    r"\bPNECs?\b",
    r"Predicted\s+No[-\s]*Effect\s+Concentration",
]


# =========================================================
# LABEL MAP
# =========================================================

LABEL_MAP = {
    "engineering_controls":
        ENGINEERING_LABELS,

    "respiratory_protection":
        RESPIRATORY_LABELS,

    "hand_protection":
        HAND_LABELS,

    "eye_face_protection":
        EYE_LABELS,

    "body_protection":
        BODY_LABELS,

    "hygiene_measures":
        HYGIENE_LABELS,

    "environmental_controls":
        ENVIRONMENT_LABELS,
}


# =========================================================
# STOP ONLY PATTERNS
#
# IMPORTANT:
# Section-number patterns use digit boundaries.
#
# Without this, "8.2" can accidentally match a date such as:
#
#   06.08.2013
#
# and truncate engineering controls.
# =========================================================

STOP_ONLY_PATTERNS = [
    r"(?<!\d)8\s*\.\s*1\s*\.?(?!\d)",
    r"(?<!\d)8\s*\.\s*2\s*\.?(?!\d)",

    r"(?<!\d)"
    r"8\s*\.\s*2\s*\.\s*3"
    r"\s*\.?(?!\d)",

    r"Biyolojik\s+mesleki\s+maruziyet\s+limitleri",
    r"Biological\s+limit\s+values",

    r"(?:BÖLÜM|SECTION)\s+9\b",

    r"(?<!\d)"
    r"9\s*\.\s*1"
    r"\s*\.?(?!\d)",
]


# =========================================================
# SEMANTIC LABEL MATCHING
# =========================================================

def _collect_label_matches(
    text: str
) -> list[dict]:

    matches = []

    for (
        field_name,
        patterns
    ) in LABEL_MAP.items():

        for pattern in patterns:

            try:

                regex = re.compile(
                    pattern,
                    flags=re.IGNORECASE
                )

            except re.error:
                continue

            for match in regex.finditer(
                text
            ):

                matches.append(
                    {
                        "start":
                            match.start(),

                        "end":
                            match.end(),

                        "field":
                            field_name,

                        "label":
                            match.group(0),
                    }
                )

    for pattern in STOP_ONLY_PATTERNS:

        try:

            regex = re.compile(
                pattern,
                flags=re.IGNORECASE
            )

        except re.error:
            continue

        for match in regex.finditer(
            text
        ):

            matches.append(
                {
                    "start":
                        match.start(),

                    "end":
                        match.end(),

                    "field":
                        None,

                    "label":
                        match.group(0),
                }
            )

    # -----------------------------------------------------
    # Position first.
    # If labels begin at same location, longest wins.
    # -----------------------------------------------------

    matches.sort(
        key=lambda item: (
            item["start"],
            -(
                item["end"]
                - item["start"]
            )
        )
    )

    selected = []

    for item in matches:

        if not selected:

            selected.append(
                item
            )

            continue

        previous = selected[-1]

        if (
            item["start"]
            < previous["end"]
        ):

            continue

        selected.append(
            item
        )

    return selected


# =========================================================
# GENERIC SEMANTIC BLOCK EXTRACTION
# =========================================================

def _extract_semantic_block(
    text: str,
    labels: list[dict],
    field_name: str
) -> str | None:

    field_matches = [
        item
        for item in labels
        if item["field"] == field_name
    ]

    if not field_matches:
        return None

    for current in field_matches:

        end = len(
            text
        )

        for candidate in labels:

            if (
                candidate["start"]
                >= current["end"]
            ):

                if (
                    candidate["start"]
                    == current["start"]
                ):

                    continue

                end = (
                    candidate["start"]
                )

                break

        value = (
            text[
                current["end"]:
                end
            ]
        )

        value = _clean_value(
            value
        )

        if value:
            return value

    return None


# =========================================================
# SECTION 8.1
# =========================================================

def _extract_section_8_1(
    section_text: str
) -> str:

    if not section_text:
        return ""

    start_match = re.search(
        r"(?<!\d)"
        r"8\s*\.\s*1\s*\.?"
        r"(?!\d)",
        section_text,
        flags=re.IGNORECASE
    )

    end_match = re.search(
        r"(?<!\d)"
        r"8\s*\.\s*2\s*\.?"
        r"(?!\d)",
        section_text,
        flags=re.IGNORECASE
    )

    start = (
        start_match.start()
        if start_match
        else 0
    )

    end = (
        end_match.start()
        if end_match
        else len(section_text)
    )

    if end <= start:
        return section_text

    return section_text[
        start:end
    ]


# =========================================================
# KEYWORD LINES
# =========================================================

def _find_keyword_lines(
    text: str,
    keywords: list[str]
) -> list[str]:

    lines = _get_lines(
        text
    )

    result = []

    for line in lines:

        folded = (
            line.casefold()
        )

        if any(
            keyword.casefold()
            in folded
            for keyword in keywords
        ):

            result.append(
                line
            )

    return _unique(
        result
    )


# =========================================================
# EXPOSURE LIMIT CLEANING
# =========================================================

def _is_weak_exposure_fragment(
    value: str
) -> bool:

    if not value:
        return True

    folded = value.casefold()

    # Table-heading-only rows are not useful as actual
    # exposure-limit values.

    table_tokens = [
        "kaynak twa",
        "twa8",
        "stel9",
        "twa (8 saat)",
        "stel (15",
    ]

    if any(
        token in folded
        for token in table_tokens
    ):

        has_measurement = bool(
            re.search(
                r"\b\d+(?:[.,]\d+)?\s*"
                r"(?:ppm|mg/m3|mg/m³|mg\s*/\s*m3|mg\s*/\s*m³)\b",
                value,
                flags=re.IGNORECASE
            )
        )

        if not has_measurement:
            return True

    # Very short legislation-only fragments are low value.

    if (
        len(value.split()) < 5
        and not re.search(
            r"\b(?:ppm|mg/m3|mg/m³|twa|stel|pel|tlv)\b",
            value,
            flags=re.IGNORECASE
        )
    ):

        return True

    return False


# =========================================================
# EXPOSURE LIMITS
# =========================================================

def _find_exposure_limits(
    section_8_1: str
) -> list[str]:

    values = _find_keyword_lines(
        section_8_1,
        [
            "maruz kalma limit",
            "maruziyet limit",
            "mesleki maruziyet",

            "occupational exposure",
            "exposure limit",

            "twa",
            "stel",
            "ceiling",
            "pel",
            "tlv",
            "ngv",
            "kgv",
            "osha",
            "acgih",
        ]
    )

    result = []

    for value in values:

        cleaned = _clean_value(
            value
        )

        if not cleaned:
            continue

        if _is_weak_exposure_fragment(
            cleaned
        ):

            continue

        result.append(
            cleaned
        )

    return _unique(
        result
    )


# =========================================================
# DNEL
# =========================================================

def _find_dnel(
    section_8_1: str
) -> list[str]:

    return _find_keyword_lines(
        section_8_1,
        [
            "dnel",
            "derived no effect",
            "derived no-effect",
        ]
    )


# =========================================================
# PNEC
# =========================================================

def _find_pnec(
    section_8_1: str
) -> list[str]:

    return _find_keyword_lines(
        section_8_1,
        [
            "pnec",

            "öngörülen etkisiz konsantrasyon",

            "predicted no effect",
            "predicted no-effect",
        ]
    )


# =========================================================
# ENGINEERING CONTROLS FALLBACK
# =========================================================

def _engineering_fallback(
    text: str,
    labels: list[dict]
) -> list[str]:

    # -----------------------------------------------------
    # Find Section 8.2 start.
    #
    # Boundary checking is critical so a date such as
    # 06.08.2013 cannot be interpreted as "8.2".
    # -----------------------------------------------------

    match = re.search(
        r"(?<!\d)"
        r"8\s*\.\s*2\s*\.?"
        r"(?!\d)"
        r"(?:"
        r"\s*Maruz\s+Kalma\s+Kontrolleri"
        r"|\s*Exposure\s+Controls"
        r")?",
        text,
        flags=re.IGNORECASE
    )

    if not match:
        return []

    start = match.end()

    end = len(
        text
    )

    # -----------------------------------------------------
    # Stop at first PPE semantic label.
    # -----------------------------------------------------

    ppe_fields = {
        "respiratory_protection",
        "hand_protection",
        "eye_face_protection",
        "body_protection",
        "hygiene_measures",
    }

    for item in labels:

        if (
            item["start"] >= start
            and item["field"]
            in ppe_fields
        ):

            end = item["start"]
            break

    value = _clean_value(
        text[
            start:end
        ]
    )

    if not value:
        return []

    value = re.sub(
        r"^(?:"
        r"Maruz\s+kalma\s+kontrolleri"
        r"|Kişisel\s+koruyucu\s+ekipman"
        r"|Kişisel\s+koruyucu\s+donanım"
        r"|Exposure\s+controls"
        r")"
        r"\s*:?\s*",
        "",
        value,
        flags=re.IGNORECASE
    ).strip()

    if len(
        value.split()
    ) < 3:

        return []

    engineering_keywords = [
        "havalandır",
        "ventilat",

        "lokal emiş",
        "local exhaust",

        "göz yıkama",
        "eye wash",
        "eyewash",

        "duş",
        "shower",

        "kapalı sistem",
        "closed system",

        "maruziyet sınır",
        "maruz kalma sınır",

        "işverenin uygun olduğu",

        "mühendislik kontrol",
        "engineering control",
    ]

    folded = (
        value.casefold()
    )

    if not any(
        keyword.casefold()
        in folded
        for keyword in engineering_keywords
    ):

        return []

    return _split_sentences(
        value
    )


# =========================================================
# GLOVE MATERIAL
# =========================================================

def _find_glove_materials(
    hand_values: list[str]
) -> list[str]:

    keywords = [
        "nitril",
        "nitrile",

        "kauçuk",
        "rubber",

        "bütil",
        "butil",
        "butyl",

        "neopren",
        "neoprin",
        "neoprene",

        "pvc",
        "polivinil",

        "latex",
        "viton",
        "eval",

        "polietilen",
        "polyethylene",
    ]

    result = []

    for value in hand_values:

        folded = (
            value.casefold()
        )

        if any(
            keyword.casefold()
            in folded
            for keyword in keywords
        ):

            result.append(
                value
            )

    return _unique(
        result
    )


# =========================================================
# GLOVE THICKNESS
# =========================================================

def _find_glove_thickness(
    hand_values: list[str]
) -> list[str]:

    text = " ".join(
        hand_values
    )

    matches = re.findall(
        r"(?:"
        r">=|<=|>|<|≥|≤"
        r")?"
        r"\s*"
        r"\d+(?:[.,]\d+)?"
        r"\s*mm\b",
        text,
        flags=re.IGNORECASE
    )

    return _unique(
        [
            re.sub(
                r"\s+",
                " ",
                value
            ).strip()

            for value in matches
        ]
    )


# =========================================================
# HYGIENE FALLBACK
# =========================================================

def _hygiene_fallback(
    section_text: str
) -> list[str]:

    lines = _get_lines(
        section_text
    )

    keywords = [
        "ellerinizi yık",
        "elleri yık",

        "kirlenmiş giysi",
        "kirli kıyafet",

        "wash hands",
        "contaminated clothing",

        "sigara",
        "yemeyin",
        "içmeyin",
    ]

    result = []

    for line in lines:

        folded = (
            line.casefold()
        )

        if any(
            keyword.casefold()
            in folded
            for keyword in keywords
        ):

            cleaned = _clean_value(
                line
            )

            if cleaned:

                result.append(
                    cleaned
                )

    return _unique(
        result
    )


# =========================================================
# FINAL LIST CLEANUP
# =========================================================

def _clean_result_list(
    values: list[str]
) -> list[str]:

    result = []

    for value in values:

        cleaned = _clean_value(
            value
        )

        if not cleaned:
            continue

        folded = cleaned.casefold()

        contamination_markers = [
            "güvenlik bilgi formu",
            "safety data sheet",

            "sayfa no:",
            "page no:",

            "düzenleme sayısı",
            "hazırlama tarihi",

            "yeniden düzenlenme ve yayın tarihi",

            "form no:",

            "www.",
        ]

        if any(
            marker in folded
            for marker in contamination_markers
        ):

            continue

        result.append(
            cleaned
        )

    return _unique(
        result
    )


# =========================================================
# PUBLIC PARSER
# =========================================================

def parse_section_8(
    section_text: str
) -> dict:

    result = _empty_result()

    if not section_text:
        return result

    normalized = (
        _normalize_text(
            section_text
        )
    )

    if not normalized:
        return result

    labels = (
        _collect_label_matches(
            normalized
        )
    )

    # =====================================================
    # RESPIRATORY PROTECTION
    # =====================================================

    respiratory_text = (
        _extract_semantic_block(
            normalized,
            labels,
            "respiratory_protection"
        )
    )

    result[
        "respiratory_protection"
    ] = _clean_result_list(
        _split_sentences(
            respiratory_text
        )
    )

    # =====================================================
    # HAND PROTECTION
    # =====================================================

    hand_text = (
        _extract_semantic_block(
            normalized,
            labels,
            "hand_protection"
        )
    )

    hand_values = (
        _clean_result_list(
            _split_sentences(
                hand_text
            )
        )
    )

    result[
        "hand_protection"
    ] = hand_values

    # =====================================================
    # GLOVE MATERIAL / THICKNESS
    # =====================================================

    result[
        "glove_materials"
    ] = _clean_result_list(
        _find_glove_materials(
            hand_values
        )
    )

    result[
        "glove_thickness"
    ] = _clean_result_list(
        _find_glove_thickness(
            hand_values
        )
    )

    # =====================================================
    # EYE / FACE
    # =====================================================

    eye_text = (
        _extract_semantic_block(
            normalized,
            labels,
            "eye_face_protection"
        )
    )

    result[
        "eye_face_protection"
    ] = _clean_result_list(
        _split_sentences(
            eye_text
        )
    )

    # =====================================================
    # BODY PROTECTION
    # =====================================================

    body_text = (
        _extract_semantic_block(
            normalized,
            labels,
            "body_protection"
        )
    )

    result[
        "body_protection"
    ] = _clean_result_list(
        _split_sentences(
            body_text
        )
    )

    # =====================================================
    # ENGINEERING CONTROLS
    # =====================================================

    engineering_text = (
        _extract_semantic_block(
            normalized,
            labels,
            "engineering_controls"
        )
    )

    engineering_values = (
        _split_sentences(
            engineering_text
        )
    )

    if not engineering_values:

        engineering_values = (
            _engineering_fallback(
                normalized,
                labels
            )
        )

    result[
        "engineering_controls"
    ] = _clean_result_list(
        engineering_values
    )

    # =====================================================
    # HYGIENE
    # =====================================================

    hygiene_text = (
        _extract_semantic_block(
            normalized,
            labels,
            "hygiene_measures"
        )
    )

    hygiene_values = (
        _split_sentences(
            hygiene_text
        )
    )

    if not hygiene_values:

        hygiene_values = (
            _hygiene_fallback(
                section_text
            )
        )

    result[
        "hygiene_measures"
    ] = _clean_result_list(
        hygiene_values
    )

    # =====================================================
    # SECTION 8.1
    # =====================================================

    section_8_1 = (
        _extract_section_8_1(
            section_text
        )
    )

    result[
        "exposure_limits"
    ] = _clean_result_list(
        _find_exposure_limits(
            section_8_1
        )
    )

    result[
        "dnel"
    ] = _clean_result_list(
        _find_dnel(
            section_8_1
        )
    )

    result[
        "pnec"
    ] = _clean_result_list(
        _find_pnec(
            section_8_1
        )
    )

    return result