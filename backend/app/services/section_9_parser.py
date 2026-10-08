import re


# =========================================================
# FIELD LABELS
# =========================================================

FIELD_PATTERNS = {
    "physical_state": [
        r"Fiziksel\s+hal(?:i)?",
        r"Fiziksel\s+durum",
        r"Toplama\s+durumu",
        r"Physical\s+state",
        r"Appearance",
        r"Görünüş",
        r"Görünüm",
    ],

    "color": [
        r"Renk",
        r"Colou?r",
    ],

    "odor": [
        r"Koku(?!\s+eşiği)",
        r"Odou?r(?!\s+threshold)",
    ],

    "ph": [
        r"pH\s+Değeri",
        r"pH\s+değeri",
        r"pH\s+value",
        r"pH",
    ],

    "melting_freezing_point": [
        r"Erime\s+noktası\s*/\s*donma\s+noktası",
        r"Erime\s+noktası",
        r"Donma\s+noktası",
        r"Melting\s+point\s*/\s*freezing\s+point",
        r"Melting\s+point",
        r"Freezing\s+point",
    ],

    "boiling_point": [
        r"Kaynama\s+noktası\s+veya\s+başlangıç\s+kaynama\s+noktası\s+ve\s+kaynama\s+aralığı",
        r"Kaynama\s+noktası\s*/\s*kaynama\s+aralığı",
        r"Kaynama\s+noktası",
        r"Kaynama\s+aralığı",
        r"Boiling\s+point\s+or\s+initial\s+boiling\s+point\s+and\s+boiling\s+range",
        r"Boiling\s+point\s*/\s*boiling\s+range",
        r"Boiling\s+point",
        r"Boiling\s+range",
    ],

    "flash_point": [
        r"Parlama\s+noktası",
        r"Flash\s+point",
    ],

    "vapour_pressure": [
        r"Buhar\s+basıncı",
        r"Vapou?r\s+pressure",
    ],

    "density": [
        r"Density\s+and/or\s+relative\s+density",
        r"Sıvı\s+yoğunluğu",
        r"Kütle\s+yoğunluğu",
        r"Özgül\s+ağırlık",
        r"Bağıl\s+yoğunluk",
        r"Nispi\s+yoğunluk",
        r"Relative\s+density",
        r"Specific\s+gravity",
        r"Density",
        r"Yoğunluk",
    ],

    "viscosity": [
        r"Kinematik\s+viskozite",
        r"Dinamik\s+viskozite",
        r"Akışkanlık\s*\(viskozite\)",
        r"Viskozite",
        r"Kinematic\s+viscosity",
        r"Dynamic\s+viscosity",
        r"Viscosity",
    ],

    "solubility": [
        r"Suda\s+çözünürlüğü",
        r"Suda\s+çözünürlük",
        r"Su\s+içinde\s+çözünürlüğü",
        r"Su\s+içinde\s+çözünürlük",
        r"Çözünürlüğü\s*\(su\s+içinde\)",
        r"Çözünürlük\s*\(ler\)",
        r"Çözünürlük",
        r"Solubility\s+in\s+water",
        r"Solubility",
    ],

    "flammability": [
        r"Alevlenebilirlik\s*\(katı,\s*gaz\)",
        r"Alevlenebilirlik",
        r"Alevlenirlik",
        r"Yanıcılık",
        r"Flammability",
    ],

    "explosive_properties": [
        r"Patlayıcılık\s+özellikleri",
        r"Patlayıcılık\s+özellikler",
        r"Patlama\s+özellikleri",
        r"Patlayıcı\s+özellikler",
        r"Explosive\s+properties",
    ],

    "oxidising_properties": [
        r"Oksitleyici\s+özellikler",
        r"Oxidi[sz]ing\s+properties",
    ],

    "lower_explosion_limit": [
        r"Alt\s+alevlenebilirlik\s+veya\s+patlama\s+limitleri",
        r"Alt\s+(?:alevlenirlik|alevlenebilirlik|patlama)\s+(?:limiti|limitleri|sınırı)",
        r"Lower\s+(?:explosion|flammability)\s+limit",
    ],

    "upper_explosion_limit": [
        r"Üst\s+alevlenebilirlik\s+veya\s+patlama\s+limitleri",
        r"Üst\s+(?:alevlenirlik|alevlenebilirlik|patlama)\s+(?:limiti|limitleri|sınırı)",
        r"Upper\s+(?:explosion|flammability)\s+limit",
    ],
}


# =========================================================
# LABELS USED ONLY AS FIELD BOUNDARIES
# =========================================================

STOP_ONLY_PATTERNS = [
    r"Koku\s+eşiği",
    r"Odou?r\s+threshold",

    r"Buharlaşma\s+hızı",
    r"Evaporation\s+rate",

    r"Buhar\s+yoğunluğu",
    r"Vapou?r\s+density",

    r"Bölüntü\s+katsayısı",
    r"Partition\s+coefficient",

    r"Kendiliğinden\s+tutuşma\s+sıcaklığı",
    r"Otomatik\s+tutuşma\s+sıcaklığı",
    r"Auto[-\s]*ignition\s+temperature",

    r"Bozunma\s+sıcaklığı",
    r"Decomposition\s+temperature",

    r"Patlayıcı\s+sınırlar",
    r"Explosive\s+limits",

    r"Moleküler\s+ağırlık",
    r"Molecular\s+weight",

    r"Diğer\s+bilgiler",
    r"Other\s+information",

    r"Alev\s+Alma\s+Sıcaklığı",
    r"Tutuşma\s+sıcaklığı",

    r"Kısmi\s+Buhar\s+Basıncı",
    r"Partial\s+vapou?r\s+pressure",

    r"Molekül\s+Ağırlığı",

    r"Dağılım\s+katsayısı",

    r"Solvent\s*/\s*Alkol\s+Çözünürlüğü",

    r"Açıklamalar",
    r"Remarks?",

    r"Solvent\s+content",
    r"Organic\s+solvents?",
    r"Change\s+in\s+condition",

    r"Üst\s*/\s*Alt\s+Alevlenirlik\s+veya\s+patlayıcı\s+Limitleri",
    r"Alt\s*/\s*Üst\s+Alevlenirlik\s+veya\s+patlayıcı\s+Limitleri",

    r"Lower\s+and\s+upper\s+(?:explosion|flammability)\s+limits?",
    r"Upper\s+and\s+lower\s+(?:explosion|flammability)\s+limits?",

    r"9\.2\.?",
]


# =========================================================
# EMPTY RESULT
# =========================================================

def _empty_result() -> dict:
    return {
        "physical_state": None,
        "color": None,
        "odor": None,
        "ph": None,
        "melting_freezing_point": None,
        "boiling_point": None,
        "flash_point": None,
        "vapour_pressure": None,
        "density": None,
        "viscosity": None,
        "solubility": None,
        "flammability": None,
        "explosive_properties": None,
        "oxidising_properties": None,
        "lower_explosion_limit": None,
        "upper_explosion_limit": None,
    }


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def _normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # PDF page markers
    text = re.sub(
        r"---\s*PAGE\s+\d+\s*---",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Turkish page numbers
    text = re.sub(
        r"\bSayfa\s*(?:No\s*:\s*)?\d+\s*/\s*\d+\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # English page numbers
    text = re.sub(
        r"\bPage\s+\d+\s*(?:of|/)\s*\d+\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Common Turkish Section 9 table header
    text = re.sub(
        r"\bÖzellik\s+Değerler\s+Notlar\s*[•·]?\s*Yöntem\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Common English Section 9 table header
    text = re.sub(
        r"\bProperty\s+Values?\s+Remarks?\s+Method\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Revision header fragments
    text = re.sub(
        r"\bRevizyon\s+tarihi\s+\d{1,2}\s*[-./]\s*"
        r"[A-Za-zÇĞİÖŞÜçğıöşü]+\s*[-./]\s*\d{4}",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bRevision\s+date\s*:?\s*\d{1,2}\s*[-./]\s*"
        r"[A-Za-z]+\s*[-./]\s*\d{4}",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# LABEL COLLECTION
# =========================================================

def _collect_label_matches(text: str) -> list[dict]:
    matches = []

    for field_name, patterns in FIELD_PATTERNS.items():

        for pattern in patterns:

            try:
                regex = re.compile(
                    rf"(?<!\w)(?:{pattern})(?!\w)",
                    flags=re.IGNORECASE,
                )

            except re.error:
                continue

            for match in regex.finditer(text):

                matches.append(
                    {
                        "start": match.start(),
                        "end": match.end(),
                        "field": field_name,
                        "text": match.group(0),
                    }
                )

    for pattern in STOP_ONLY_PATTERNS:

        try:
            regex = re.compile(
                rf"(?<!\w)(?:{pattern})(?!\w)",
                flags=re.IGNORECASE,
            )

        except re.error:
            continue

        for match in regex.finditer(text):

            matches.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "field": None,
                    "text": match.group(0),
                }
            )

    matches.sort(
        key=lambda item: (
            item["start"],
            -(item["end"] - item["start"]),
        )
    )

    selected = []

    for item in matches:

        if not selected:
            selected.append(item)
            continue

        previous = selected[-1]

        # Ignore overlapping shorter labels.
        if item["start"] < previous["end"]:
            continue

        selected.append(item)

    return selected


# =========================================================
# CLEANING HELPERS
# =========================================================

def _remove_note_column_noise(value: str) -> str:
    markers = [
        "Hiçbiri bilinmiyor",
        "None known",
        "No method available",
    ]

    for marker in markers:

        match = re.search(
            re.escape(marker),
            value,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        before = value[:match.start()].strip()

        if before:
            return before

    return value


def _clean_value(
    field_name: str,
    value: str | None,
) -> str | None:

    if not value:
        return None

    value = re.sub(
        r"[ꞏ▤▪■]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    # Do NOT strip "-" because negative values such as -52 °C
    # are legitimate physical property values.
    value = value.lstrip(
        " :;–—•·"
    )

    value = value.rstrip(
        " :;–—•·"
    )

    value = _remove_note_column_noise(
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    if value in {
        "",
        "/",
        "-",
        "—",
        "•",
        "·",
        "ꞏ",
        "▤",
    }:
        return None

    if field_name == "melting_freezing_point":

        value = re.sub(
            r"^/?\s*(?:Donma\s+noktası|Freezing\s+point)\s*:?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()

    if field_name == "boiling_point":

        value = re.sub(
            r"^/?\s*(?:Kaynama\s+aralığı|Boiling\s+range)\s*:?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()

    if not value:
        return None

    return value


# =========================================================
# GENERIC FIELD EXTRACTION
# =========================================================

def _extract_field_from_labels(
    text: str,
    labels: list[dict],
    field_name: str,
) -> str | None:

    field_matches = [
        item
        for item in labels
        if item["field"] == field_name
    ]

    for current in field_matches:

        next_start = len(text)

        for candidate in labels:

            if candidate["start"] >= current["end"]:

                if candidate["start"] == current["start"]:
                    continue

                next_start = candidate["start"]
                break

        raw_value = text[
            current["end"]:next_start
        ]

        value = _clean_value(
            field_name,
            raw_value,
        )

        if value:
            return value

    return None


# =========================================================
# pH FALLBACK
# =========================================================

def _extract_ph_fallback(
    text: str,
) -> str | None:

    match = re.search(
        r"(?<!\w)"
        r"pH"
        r"(?:\s+(?:değeri|value))?"
        r"\s*:?\s*"
        r"(~?\s*[<>]?\s*"
        r"\d{1,2}(?:[.,]\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return re.sub(
        r"\s+",
        "",
        match.group(1),
    )


# =========================================================
# MELTING / FREEZING FALLBACK
# =========================================================

def _extract_melting_fallback(
    text: str,
) -> str | None:

    label = re.search(
        r"(?:"
        r"Erime\s+noktası"
        r"(?:\s*/\s*donma\s+noktası)?"
        r"|"
        r"Melting\s+point"
        r"(?:\s*/\s*freezing\s+point)?"
        r")"
        r"(?:\s*\([^)]{0,80}\))?",
        text,
        flags=re.IGNORECASE,
    )

    if not label:
        return None

    tail = text[
        label.end():
        label.end() + 160
    ]

    stop = re.search(
        r"\b(?:"
        r"Kaynama\s+noktası"
        r"|Boiling\s+point"
        r"|Parlama\s+noktası"
        r"|Flash\s+point"
        r")\b",
        tail,
        flags=re.IGNORECASE,
    )

    if stop:
        tail = tail[:stop.start()]

    tail = re.sub(
        r"-\s+(?=\d)",
        "-",
        tail,
    )

    candidates = []

    for match in re.finditer(
        r"[<>≤≥~]?\s*-?\d+(?:[.,]\d+)?",
        tail,
    ):

        after = tail[
            match.end():
            match.end() + 12
        ]

        before = tail[
            max(
                0,
                match.start() - 4,
            ):
            match.start()
        ]

        # Pressure condition, not temperature value.
        if re.match(
            r"\s*mmHg\b",
            after,
            flags=re.IGNORECASE,
        ):
            continue

        # Concentration value, not temperature.
        if "%" in before:
            continue

        candidates.append(
            re.sub(
                r"\s+",
                "",
                match.group(0),
            )
        )

    if not candidates:
        return None

    value = candidates[0]

    return f"{value} °C"


# =========================================================
# BOILING FALLBACK
# =========================================================

def _extract_boiling_fallback(
    text: str,
) -> str | None:

    label = re.search(
        r"(?:"
        r"Kaynama\s+noktası"
        r"(?:\s*/\s*kaynama\s+aralığı)?"
        r"|"
        r"Boiling\s+point"
        r"(?:\s*/\s*boiling\s+range)?"
        r")"
        r"(?:\s*\([^)]{0,80}\))?",
        text,
        flags=re.IGNORECASE,
    )

    if not label:
        return None

    tail = text[
        label.end():
        label.end() + 200
    ]

    stop = re.search(
        r"\b(?:"
        r"Parlama\s+noktası"
        r"|Flash\s+point"
        r"|Alevlenebilirlik"
        r"|Flammability"
        r")\b",
        tail,
        flags=re.IGNORECASE,
    )

    if stop:
        tail = tail[:stop.start()]

    tail = re.sub(
        r"-\s+(?=\d)",
        "-",
        tail,
    )

    candidates = []

    for match in re.finditer(
        r"[<>≤≥~]?\s*-?\d+(?:[.,]\d+)?",
        tail,
    ):

        raw_value = match.group(0)

        after = tail[
            match.end():
            match.end() + 12
        ]

        before = tail[
            max(
                0,
                match.start() - 4,
            ):
            match.start()
        ]

        # 760 mmHg is a pressure condition, not boiling value.
        if re.match(
            r"\s*mmHg\b",
            after,
            flags=re.IGNORECASE,
        ):
            continue

        # e.g. %15 solution
        if "%" in before:
            continue

        candidates.append(
            re.sub(
                r"\s+",
                "",
                raw_value,
            )
        )

    if not candidates:
        return None

    value = candidates[0]

    result = f"{value} °C"

    pressure = re.search(
        r"\b\d+(?:[.,]\d+)?\s*mmHg\b",
        tail,
        flags=re.IGNORECASE,
    )

    if pressure:

        result += (
            " ("
            + pressure.group(0)
            + ")"
        )

    return result


# =========================================================
# VAPOUR PRESSURE FALLBACK
# =========================================================

def _extract_vapour_pressure_fallback(
    text: str,
) -> str | None:

    # Example:
    # Buhar Basıncı (mmHg) @ 30°C 18

    match = re.search(
        r"(?:Buhar\s+basıncı|Vapou?r\s+pressure)"
        r"\s*\("
        r"(hPa|kPa|Pa|mbar|bar|mmHg)"
        r"\)"
        r"\s*"
        r"(?:@\s*([^\s]+))?"
        r"\s*"
        r"([<>≤≥~]?\s*\d+(?:[.,]\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if match:

        value = re.sub(
            r"\s+",
            "",
            match.group(3),
        )

        result = (
            value
            + " "
            + match.group(1)
        )

        if match.group(2):

            result += (
                " @ "
                + match.group(2)
            )

        return result

    # Example:
    # Vapour pressure 23 hPa (20°C)

    match = re.search(
        r"(?:Buhar\s+basıncı|Vapou?r\s+pressure)"
        r"\s*:?\s*"
        r"("
        r"[<>≤≥~]?\s*"
        r"\d+(?:[.,]\d+)?"
        r"\s*"
        r"(?:hPa|kPa|Pa|mbar|bar|mmHg)"
        r"(?:\s*\([^)]{1,40}\))?"
        r")",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return re.sub(
        r"\s+",
        " ",
        match.group(1),
    ).strip()


# =========================================================
# DENSITY FALLBACK
# =========================================================

def _extract_density_fallback(
    text: str,
) -> str | None:

    labels = (
        r"Density\s+and/or\s+relative\s+density"
        r"|Sıvı\s+yoğunluğu"
        r"|Kütle\s+yoğunluğu"
        r"|Bağıl\s+yoğunluk"
        r"|Nispi\s+yoğunluk"
        r"|Özgül\s+ağırlık"
        r"|Relative\s+density"
        r"|Specific\s+gravity"
        r"|Density"
        r"|Yoğunluk"
    )

    # Example:
    # Bağıl Yoğunluk kg/l 20°C / 4°C 1.19

    match = re.search(
        rf"(?:{labels})"
        r"\s*:?\s*"
        r"(kg\s*/\s*l"
        r"|g\s*/\s*ml"
        r"|g\s*/\s*cm(?:3|³)"
        r"|kg\s*/\s*m(?:3|³))"
        r"\s*"
        r"(\d+(?:[.,]\d+)?"
        r"\s*[°˚]?C"
        r"\s*/\s*"
        r"\d+(?:[.,]\d+)?"
        r"\s*[°˚]?C)"
        r"\s*"
        r"(\d+(?:[.,]\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if match:

        unit = re.sub(
            r"\s+",
            "",
            match.group(1),
        )

        condition = (
            match.group(2)
            or ""
        ).strip()

        result = (
            match.group(3)
            + " "
            + unit
        )

        if condition:

            result += (
                " ("
                + condition
                + ")"
            )

        return result

    # Example:
    # Density 1.56 g/cm3

    match = re.search(
        rf"(?:{labels})"
        r"\s*:?\s*"
        r"("
        r"(?:yaklaşık\s*)?"
        r"\d+(?:[.,]\d+)?"
        r"(?:\s*[-–]\s*"
        r"\d+(?:[.,]\d+)?)?"
        r"\s*"
        r"(?:"
        r"g\s*/\s*cm(?:3|³)"
        r"|kg\s*/\s*m(?:3|³)"
        r"|g\s*/\s*ml"
        r"|kg\s*/\s*l"
        r")"
        r")",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return re.sub(
        r"\s+",
        " ",
        match.group(1),
    ).strip()


# =========================================================
# VISCOSITY FALLBACK
# =========================================================

def _extract_viscosity_fallback(
    text: str,
) -> str | None:

    labels = (
        r"Kinematik\s+viskozite"
        r"|Dinamik\s+viskozite"
        r"|Viskozite"
        r"|Kinematic\s+viscosity"
        r"|Dynamic\s+viscosity"
        r"|Viscosity"
    )

    units = (
        r"mPa\s*[·.]?\s*s"
        r"|Pa\s*[·.]?\s*s"
        r"|cP"
        r"|cps"
        r"|mm(?:2|²)\s*/\s*s"
        r"|cSt"
    )

    # Example:
    # Viskozite cps @25°C 1.245

    match = re.search(
        rf"(?:{labels})"
        r"\s*:?\s*"
        rf"({units})"
        r"\s*"
        r"(?:@\s*([^\s]+))?"
        r"\s*"
        r"([<>≤≥~]?\s*\d+(?:[.,]\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if match:

        value = re.sub(
            r"\s+",
            "",
            match.group(3),
        )

        result = (
            value
            + " "
            + match.group(1)
        )

        if match.group(2):

            result += (
                " @ "
                + match.group(2)
            )

        return result

    # Example:
    # Viscosity 90 mPa.s

    match = re.search(
        rf"(?:{labels})"
        r"\s*:?\s*"
        r"("
        r"[<>≤≥~]?\s*"
        r"\d+(?:[.,]\d+)?"
        r"\s*"
        rf"(?:{units})"
        r")",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return re.sub(
        r"\s+",
        " ",
        match.group(1),
    ).strip()


# =========================================================
# EXPLOSIVE PROPERTIES FALLBACK
# =========================================================

def _extract_explosive_properties_fallback(
    text: str,
) -> str | None:

    # Some PDF tables may split a value around the label:
    #
    # Kapalı kaplarda dekompozisyon durumunda basınç
    # Patlayıcılık Özellikler
    # patlaması yapar.

    if not re.search(
        r"Patlayıcılık\s+Özellikler\b",
        text,
        flags=re.IGNORECASE,
    ):
        return None

    match = re.search(
        r"(?:Bilgi\s+[Yy]ok\s+|Not\s+available\s+)?"
        r"([^.!?]{20,180}?)"
        r"\s+"
        r"(?:"
        r"Patlayıcılık\s+özellikleri"
        r"|Patlayıcılık\s+özellikler"
        r"|Patlama\s+özellikleri"
        r"|Patlayıcı\s+özellikler"
        r"|Explosive\s+properties"
        r")"
        r"\s+"
        r"([^.!?]{2,120}[.!?])",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    before = re.split(
        r"(?:"
        r"Bilgi\s+[Yy]ok"
        r"|Not\s+available"
        r"|Not\s+determined"
        r")\s*",
        match.group(1),
        flags=re.IGNORECASE,
    )[-1]

    value = (
        before
        + " "
        + match.group(2)
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    if len(value) < 20:
        return None

    return value


# =========================================================
# EXPLOSION LIMITS FALLBACK
# =========================================================

def _extract_combined_explosion_limits(
    text: str,
) -> tuple[str | None, str | None]:

    match = re.search(
        r"(?:"
        r"Lower\s+and\s+upper"
        r"|Upper\s+and\s+lower"
        r")"
        r"\s+(?:explosion|flammability)"
        r"\s+limits?"
        r"(.{0,260})",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None, None

    tail = match.group(1)

    lower = re.search(
        r"\bLower\s*:?\s*"
        r"([^.;]{1,100})",
        tail,
        flags=re.IGNORECASE,
    )

    upper = re.search(
        r"\bUpper\s*:?\s*"
        r"([^.;]{1,100})",
        tail,
        flags=re.IGNORECASE,
    )

    lower_value = (
        lower.group(1).strip()
        if lower
        else None
    )

    upper_value = (
        upper.group(1).strip()
        if upper
        else None
    )

    return (
        lower_value,
        upper_value,
    )


# =========================================================
# CONTAMINATION DETECTION
# =========================================================

def _looks_contaminated(
    field_name: str,
    value: str | None,
) -> bool:

    if not value:
        return True

    value_folded = value.casefold()

    common_markers = [
        "güvenlik bilgi formu",
        "safety data sheet",
        "sayfa no:",
        "page no:",
        "düzenleme sayısı",
        "hazırlama tarihi",
        "printing date",
        "form no:",
        "www.",
    ]

    for marker in common_markers:

        if marker in value_folded:
            return True

    # -----------------------------------------------------
    # MELTING / FREEZING
    #
    # mmHg usually indicates that a pressure condition from
    # another table column has contaminated the extracted
    # melting/freezing value.
    # -----------------------------------------------------

    if (
        field_name == "melting_freezing_point"
        and "mmhg" in value_folded
    ):
        return True

    # -----------------------------------------------------
    # BOILING POINT
    #
    # A value such as:
    #
    #   (%15'lik çözelti) (°C) 760 mmHg 114
    #
    # is a table-layout extraction and should be rebuilt by
    # the dedicated boiling fallback as:
    #
    #   114 °C (760 mmHg)
    #
    # Clean values such as "> 100 °C" do not contain mmHg
    # and therefore remain unchanged.
    # -----------------------------------------------------

    if (
        field_name == "boiling_point"
        and "mmhg" in value_folded
    ):
        return True

    contamination_markers = {

        "melting_freezing_point": [
            "kaynama noktası",
            "boiling point",
            "alevlenebilirlik",
        ],

        "boiling_point": [
            "alevlenebilirlik",
            "flammability",
            "parlama noktası",
            "flash point",
        ],

        "flash_point": [
            "alev alma sıcaklığı",
            "tutuşma sıcaklığı",
            "auto-ignition",
            "buharlaşma hızı",
            "evaporation rate",
            "buhar basıncı",
            "vapour pressure",
            "vapor pressure",
        ],

        "vapour_pressure": [
            "kısmi buhar basıncı",
            "partial vapour pressure",
            "buhar yoğunluğu",
            "vapour density",
            "vapor density",
            "bağıl yoğunluk",
            "relative density",
        ],

        "density": [
            "çözünürlük",
            "solubility",
            "bölüntü katsayısı",
            "partition coefficient",
        ],

        "viscosity": [
            "molekül ağırlığı",
            "molecular weight",
            "patlayıcılık",
            "explosive properties",
            "oksitleyici",
            "oxidising",
            "oxidizing",
        ],

        "solubility": [
            "solvent/alkol çözünürlüğü",
            "dağılım katsayısı",
            "bölüntü katsayısı",
            "partition coefficient",
            "kendiliğinden tutuşma",
            "auto-ignition",
        ],

        "explosive_properties": [
            "solvent content",
            "organic solvents",
            "change in condition",
        ],

        "oxidising_properties": [
            "açıklamalar",
            "remarks",
        ],
    }

    for marker in contamination_markers.get(
        field_name,
        [],
    ):

        if marker in value_folded:
            return True

    if value.strip() == "/":
        return True

    return False


# =========================================================
# PUBLIC PARSER
# =========================================================

def parse_section_9(
    section_text: str,
) -> dict:

    result = _empty_result()

    if not section_text:
        return result

    text = _normalize_text(
        section_text
    )

    if not text:
        return result

    labels = _collect_label_matches(
        text
    )

    # -----------------------------------------------------
    # 1. Generic extraction
    # -----------------------------------------------------

    for field_name in FIELD_PATTERNS:

        result[field_name] = (
            _extract_field_from_labels(
                text,
                labels,
                field_name,
            )
        )

    # -----------------------------------------------------
    # 2. pH fallback
    # -----------------------------------------------------

    ph_fallback = (
        _extract_ph_fallback(
            text
        )
    )

    if (
        not result["ph"]
        or _looks_contaminated(
            "ph",
            result["ph"],
        )
    ):

        if ph_fallback:

            result["ph"] = (
                ph_fallback
            )

    # -----------------------------------------------------
    # 3. Melting / freezing fallback
    #
    # IMPORTANT:
    # Do NOT replace an already clean generic value.
    #
    # This protects existing regression behaviour such as:
    # < 0
    #
    # while still allowing contaminated PDFs such as the
    # hydrogen peroxide SDS to be corrected to -52 °C.
    # -----------------------------------------------------

    melting_fallback = (
        _extract_melting_fallback(
            text
        )
    )

    if (
        not result[
            "melting_freezing_point"
        ]
        or _looks_contaminated(
            "melting_freezing_point",
            result[
                "melting_freezing_point"
            ],
        )
    ):

        if melting_fallback:

            result[
                "melting_freezing_point"
            ] = melting_fallback

    # -----------------------------------------------------
    # 4. Boiling fallback
    #
    # Same rule:
    # preserve an already clean generic value.
    # -----------------------------------------------------

    boiling_fallback = (
        _extract_boiling_fallback(
            text
        )
    )

    if (
        not result[
            "boiling_point"
        ]
        or _looks_contaminated(
            "boiling_point",
            result[
                "boiling_point"
            ],
        )
    ):

        if boiling_fallback:

            result[
                "boiling_point"
            ] = boiling_fallback

    # -----------------------------------------------------
    # 5. Vapour pressure fallback
    # -----------------------------------------------------

    vapour_pressure_fallback = (
        _extract_vapour_pressure_fallback(
            text
        )
    )

    if vapour_pressure_fallback:

        result[
            "vapour_pressure"
        ] = vapour_pressure_fallback

    # -----------------------------------------------------
    # 6. Density fallback
    # -----------------------------------------------------

    density_fallback = (
        _extract_density_fallback(
            text
        )
    )

    if density_fallback:

        result[
            "density"
        ] = density_fallback

    # -----------------------------------------------------
    # 7. Viscosity fallback
    # -----------------------------------------------------

    viscosity_fallback = (
        _extract_viscosity_fallback(
            text
        )
    )

    if viscosity_fallback:

        result[
            "viscosity"
        ] = viscosity_fallback

    # -----------------------------------------------------
    # 8. Explosive properties fallback
    # -----------------------------------------------------

    explosive_fallback = (
        _extract_explosive_properties_fallback(
            text
        )
    )

    if (
        explosive_fallback
        and (
            not result[
                "explosive_properties"
            ]
            or len(
                result[
                    "explosive_properties"
                ]
            ) < 20
            or _looks_contaminated(
                "explosive_properties",
                result[
                    "explosive_properties"
                ],
            )
        )
    ):

        result[
            "explosive_properties"
        ] = explosive_fallback

    # -----------------------------------------------------
    # 9. Combined explosion limits
    # -----------------------------------------------------

    lower_limit, upper_limit = (
        _extract_combined_explosion_limits(
            text
        )
    )

    if lower_limit:

        result[
            "lower_explosion_limit"
        ] = lower_limit

    if upper_limit:

        result[
            "upper_explosion_limit"
        ] = upper_limit

    # -----------------------------------------------------
    # 10. Final cleanup
    # -----------------------------------------------------

    for field_name, value in list(
        result.items()
    ):

        result[field_name] = (
            _clean_value(
                field_name,
                value,
            )
        )

    return result