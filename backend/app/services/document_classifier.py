import re


def _find_main_section_numbers(
    text: str
) -> set[int]:

    pattern = re.compile(
        r"(?im)^"
        r"\s*"
        r"[\*\-·•]?\s*"
        r"(?:"
        r"(?:BÖLÜM|SECTION)\s+(\d{1,2})\s*[:\-]?"
        r"|"
        r"(\d{1,2})\s*[\.\-]\s+(?!\d)"
        r")"
    )

    section_numbers = set()

    for match in pattern.finditer(text):

        value = (
            match.group(1)
            or match.group(2)
        )

        if not value:
            continue

        number = int(value)

        if 1 <= number <= 16:
            section_numbers.add(number)

    return section_numbers


def classify_document(
    text: str
) -> str:

    if not text:
        return "UNKNOWN"

    normalized = re.sub(
        r"\s+",
        " ",
        text
    ).upper()

    # =====================================================
    # SDS SECTION DETECTION
    # =====================================================

    section_numbers = (
        _find_main_section_numbers(
            text
        )
    )

    section_count = len(
        section_numbers
    )

    # =====================================================
    # STRONG SDS MARKERS
    # =====================================================

    sds_markers = [
        "GÜVENLİK BİLGİ FORMU",
        "GÜVENLİK BİLGİ FORMU",
        "SAFETY DATA SHEET",
        "SAFETY DATA",
        "ZARARLILIK TANIMLANMASI",
        "TEHLİKELERİN TANIMLANMASI",
        "HAZARDS IDENTIFICATION",
        "BİLEŞİMİ/İÇİNDEKİLER",
        "COMPOSITION/INFORMATION",
        "İLK YARDIM ÖNLEMLERİ",
        "FIRST AID MEASURES",
        "YANGINLA MÜCADELE",
        "FIREFIGHTING MEASURES",
        "ELLEÇLEME VE DEPOLAMA",
        "HANDLING AND STORAGE",
        "MARUZ KALMA KONTROLLERİ",
        "EXPOSURE CONTROLS",
        "FİZİKSEL VE KİMYASAL ÖZELLİKLER",
        "PHYSICAL AND CHEMICAL PROPERTIES",
        "TOKSİKOLOJİK BİLGİLER",
        "TOXICOLOGICAL INFORMATION",
        "EKOLOJİK BİLGİLER",
        "ECOLOGICAL INFORMATION",
        "TAŞIMACILIK BİLGİLERİ",
        "TRANSPORT INFORMATION",
        "MEVZUAT BİLGİLERİ",
        "REGULATORY INFORMATION",
        "DİĞER BİLGİLER",
        "OTHER INFORMATION",
    ]

    marker_count = sum(
        1
        for marker in sds_markers
        if marker in normalized
    )

    # =====================================================
    # STRONG SDS DECISION
    # =====================================================

    # 1-16'nın önemli bölümü mevcutsa kesin SDS
    if section_count >= 8:
        return "SDS"

    # Güvenlik Bilgi Formu başlığı +
    # birkaç gerçek ana bölüm
    if (
        (
            "GÜVENLİK BİLGİ FORMU"
            in normalized
            or
            "GÜVENLİK BİLGİ FORMU"
            in normalized
            or
            "SAFETY DATA SHEET"
            in normalized
        )
        and section_count >= 4
    ):
        return "SDS"

    # Bölüm numaraları PDF extraction nedeniyle
    # bozulmuş olsa bile güçlü başlıklar yeterli
    if marker_count >= 6:
        return "SDS"

    # =====================================================
    # HAZARDOUS MATERIAL INSTRUCTION
    # =====================================================

    hazardous_instruction_markers = [
        "HAZARDOUS MATERIAL INSTRUCTION",
        "HAZARDOUS MATERIAL INFORMATION",
    ]

    if any(
        marker in normalized
        for marker
        in hazardous_instruction_markers
    ):
        return "HAZARDOUS_MATERIAL_INSTRUCTION"

    return "UNKNOWN"