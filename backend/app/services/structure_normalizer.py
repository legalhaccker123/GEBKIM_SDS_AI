import re

from app.services.semantic_labels import (
    SECTION_7_LABELS,
    SECTION_8_LABELS,
    SECTION_9_LABELS,
)


# =========================================================
# UNIVERSAL SDS STRUCTURE NORMALIZER - V8.2
#
# AMAÇ
# ---------------------------------------------------------
# PDF text extraction sırasında aynı satıra birleşen yapısal
# SDS alanlarını tekrar ayırmak.
#
# ÖNEMLİ:
# - Firma özel kural içermez.
# - Veri çıkarmaya çalışmaz.
# - Kelime içlerini ASLA parçalamamalıdır.
# - "renksiz" içindeki "renk",
#   "kokusuz" içindeki "koku",
#   "tripolyphosphate" içindeki "pH"
#   eşleşmemelidir.
# =========================================================


# =========================================================
# SECTION 1 LABELS
# =========================================================

SECTION_1_LABELS = [
    "Ürün Adı",
    "Ürün adı",
    "Ürün İsmi",
    "Ürün ismi",

    "Ticari Adı",
    "Ticari adı",

    "Madde Adı",
    "Madde/Karışım Adı",

    "Ürün Kodu(ları)",
    "Ürün Kodu",
    "Ürün kodu",

    "Product name",
    "Product identifier",
    "Product code",

    "Benzersiz Formül Tanımlayıcı (UFI)",
    "UFI",

    "REACH kayıt numarası",
    "REACH registration number",

    "Tedarikçi",
    "Üretici",
    "Firma Adı",
    "Şirket Adı",

    "Supplier",
    "Manufacturer",
]


# =========================================================
# SECTION 2 LABELS
# =========================================================

SECTION_2_LABELS = [
    "Madde veya karışımın sınıflandırılması",
    "Madde ve Karışımın Sınıflandırılması",
    "Classification of the substance or mixture",

    "Etiket unsurları",
    "Etiket Unsurları",
    "Label elements",

    "Uyarı kelimesi",
    "Uyarı Kelimesi",
    "Signal word",

    "Zararlılık İfadeleri",
    "Zararlılık ifadeleri",
    "Hazard statements",

    "Önlem İfadeleri",
    "Önlem ifadeleri",
    "Precautionary statements",

    "Zararlılık İşaretleri",
    "Zararlılık işaretleri",
    "Piktogramlar",
    "Pictograms",

    "Diğer zararlar",
    "Diğer Zararlar",
    "Other hazards",
]


# =========================================================
# REVISION LABELS
# =========================================================

REVISION_LABELS = [
    "Hazırlama Tarihi",
    "Hazırlanma Tarihi",

    "Yeni Düzenleme Tarihi",
    "Yeniden Düzenleme Tarihi",
    "Yeniden Düzenlenme Tarihi",

    "Revizyon tarihi",
    "Revizyon Tarihi",

    "Revision date",
    "Date of revision",

    "Düzenleme Sayısı",
    "Kaçıncı Düzenleme Olduğu",

    "Revizyon Numarası",
    "Revision Number",

    "Version",
    "Sürüm",
]


# =========================================================
# SECTION 8 STRUCTURAL LABELS
# =========================================================

SECTION_8_STRUCTURAL_LABELS = [
    "Kişisel koruyucu ekipman",
    "Kişisel Koruyucu Donanımlar",

    "Maruz Kalma Limitleri",
    "Mesleki maruziyet limitleri",

    "İşçiler için DNELs",
    "Genel nüfus için DNELs",

    "Öngörülen Etkisiz Konsantrasyon",

    "PNEC",
    "DNEL",
]


# =========================================================
# SECTION 9 ADDITIONAL LABELS
#
# semantic_labels.py'daki ana alanlara ek olarak yapıyı
# ayırmak için kullanılır.
# =========================================================

SECTION_9_EXTRA_LABELS = [
    "Sıvı Yoğunluğu",
    "Yığın yoğunluğu",
    "Buhar yoğunluğu",

    "Kendiliğinden tutuşma sıcaklığı",
    "Bozunma sıcaklığı",

    "Havadaki Alevlenebilirlik Limiti",

    "Özellik",
    "Değerler",
    "Notlar",
    "Yöntem",
]


# =========================================================
# SAFE CONCATENATED LABELS
#
# Sadece gerçekten güvenli olan birkaç yapı.
#
# Örnek:
# Uyarı kelimesiDikkat
# ->
# Uyarı kelimesi: Dikkat
#
# Genel semantic label'lara BU İŞLEM uygulanmaz.
# =========================================================

SAFE_CONCATENATED_RULES = [
    (
        r"Uyarı\s+kelimesi",
        r"(Dikkat|Tehlike|Warning|Danger)",
    ),
    (
        r"Signal\s+word",
        r"(Warning|Danger)",
    ),
]


# =========================================================
# BASIC NORMALIZATION
# =========================================================

def _basic_normalize(
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
        "\u00a0",
        " "
    )

    text = text.replace(
        "\t",
        " "
    )

    # Sadece horizontal whitespace.
    # Newline korunur.
    text = re.sub(
        r"[ ]{2,}",
        " ",
        text
    )

    return text


# =========================================================
# PAGE ARTIFACTS
# =========================================================

def _separate_page_artifacts(
    text: str
) -> str:

    # Local PDF extractor:
    # --- PAGE 3 ---
    text = re.sub(
        r"(?i)"
        r"\s*"
        r"(---\s*PAGE\s+\d+\s*---)"
        r"\s*",
        r"\n\1\n",
        text
    )

    # Uzun underscore header/footer çizgileri
    text = re.sub(
        r"_{20,}",
        "\n",
        text
    )

    return text


# =========================================================
# MAIN SECTION HEADINGS
# =========================================================

def _break_before_section_headings(
    text: str
) -> str:

    """
    Gerçek section heading formatı:

        BÖLÜM 7:
        SECTION 8:

    ":" zorunlu tutulduğu için:
        "bakınız bölüm 8"
    gibi referanslar bölünmez.
    """

    pattern = re.compile(
        r"(?i)"
        r"[ \t]*"
        r"("
        r"(?:BÖLÜM|BOLUM|SECTION)"
        r"\s*"
        r"(?:1[0-6]|[1-9])"
        r"\s*:"
        r")"
    )

    return pattern.sub(
        r"\n\1",
        text
    )


# =========================================================
# NUMBERED SDS SUBSECTIONS
# =========================================================

def _break_before_numbered_subheadings(
    text: str
) -> str:

    """
    Desteklenen:

        1.1.
        2.2.
        7.3.
        8.2.1.
        8.2.2.3

    Tarih gibi:
        15.07.2016
    değerleri mümkün olduğunca subsection olarak algılamaz.

    İlk section numarası 1-16 olmak zorunda.
    Alt numaralar 1-2 basamak.
    """

    pattern = re.compile(
        r"(?i)"
        r"(?<![\d.])"
        r"[ \t]+"
        r"("
        r"(?:1[0-6]|[1-9])"
        r"(?:\.\d{1,2}){1,3}"
        r"\.?"
        r")"
        r"(?=[ \t])"
    )

    return pattern.sub(
        r"\n\1 ",
        text
    )


# =========================================================
# COLLECT SEMANTIC LABELS
# =========================================================

def _collect_semantic_labels() -> list[str]:

    labels = []

    labels.extend(
        SECTION_1_LABELS
    )

    labels.extend(
        SECTION_2_LABELS
    )

    labels.extend(
        REVISION_LABELS
    )

    labels.extend(
        SECTION_8_STRUCTURAL_LABELS
    )

    labels.extend(
        SECTION_9_EXTRA_LABELS
    )

    for group in (
        SECTION_7_LABELS.values()
    ):

        labels.extend(
            group
        )

    for group in (
        SECTION_8_LABELS.values()
    ):

        labels.extend(
            group
        )

    for group in (
        SECTION_9_LABELS.values()
    ):

        labels.extend(
            group
        )

    # ---------------------------------------------
    # Case-insensitive deduplication
    # ---------------------------------------------

    unique = {}

    for label in labels:

        cleaned = (
            label.strip()
        )

        if not cleaned:
            continue

        key = (
            cleaned.casefold()
        )

        unique[
            key
        ] = cleaned

    # Uzun başlıklar önce.
    #
    # Örn:
    # "Kaynama noktası / kaynama aralığı"
    # "Kaynama noktası"
    #
    return sorted(
        unique.values(),
        key=len,
        reverse=True
    )


# =========================================================
# SAFE BOUNDARY BEFORE LABEL
# =========================================================

def _break_before_label(
    text: str,
    label: str
) -> str:

    """
    Yalnızca label'ın önünde gerçek whitespace varsa böl.

    Ayrıca label'ın sonrasında:
        whitespace
        :
        satır sonu
    olmak zorunda.

    Böylece:

        renksiz
        kokusuz
        kullanımları
        DNELs
        tripolyphosphate

    içinde eşleşme oluşmaz.
    """

    escaped = re.escape(
        label
    )

    pattern = re.compile(
        rf"(?i)"
        rf"(?<!\S)"
        rf"({escaped})"
        rf"(?="
        rf"[ \t\n:]"
        rf"|$"
        rf")"
    )

    # Baştaki whitespace'i silmeden önce kontrol edeceğiz.
    # Pattern doğrudan label'da başlıyor.
    #
    # Eğer label zaten satır başındaysa değiştirmiyoruz.

    def replacer(
        match: re.Match
    ) -> str:

        start = match.start()

        if (
            start == 0
            or text[
                start - 1
            ] == "\n"
        ):

            return match.group(1)

        return (
            "\n"
            + match.group(1)
        )

    return pattern.sub(
        replacer,
        text
    )


# =========================================================
# SEMANTIC LABEL PASS
# =========================================================

def _break_before_semantic_labels(
    text: str
) -> str:

    for label in (
        _collect_semantic_labels()
    ):

        text = _break_before_label(
            text,
            label
        )

    return text


# =========================================================
# SAFE CONCATENATED LABEL/VALUE FIX
# =========================================================

def _fix_safe_concatenated_labels(
    text: str
) -> str:

    """
    Genel label parser DEĞİL.

    Sadece kesin olarak bildiğimiz ve kelime içi
    false-positive oluşturmayacak yapıların bitişik
    value'sunu ayırır.
    """

    for (
        label_pattern,
        value_pattern
    ) in SAFE_CONCATENATED_RULES:

        pattern = re.compile(
            rf"(?i)"
            rf"(?<!\w)"
            rf"({label_pattern})"
            rf"({value_pattern})"
            rf"\b"
        )

        text = pattern.sub(
            r"\1: \2",
            text
        )

    return text


# =========================================================
# P-CODE GROUP NORMALIZATION
# =========================================================

def _normalize_precautionary_code_groups(
    text: str
) -> str:

    """
    Örnek:

        P305 + P351 + P338
          ->
        P305+P351+P338

        P301 + 310
          ->
        P301+P310
    """

    # İlk P kodu
    text = re.sub(
        r"\bP\s*(\d{3})\b",
        r"P\1",
        text,
        flags=re.IGNORECASE
    )

    # Zinciri adım adım tamamla
    for _ in range(6):

        new_text = re.sub(
            r"\b"
            r"(P\d{3}"
            r"(?:\+P\d{3})*)"
            r"\s*\+\s*"
            r"P?\s*"
            r"(\d{3})"
            r"\b",
            r"\1+P\2",
            text,
            flags=re.IGNORECASE
        )

        if new_text == text:
            break

        text = new_text

    return text


# =========================================================
# H CODE NORMALIZATION
# =========================================================

def _normalize_hazard_codes(
    text: str
) -> str:

    # H 315 -> H315
    text = re.sub(
        r"\bH\s+(\d{3}[A-Za-z]?)\b",
        r"H\1",
        text,
        flags=re.IGNORECASE
    )

    return text


# =========================================================
# FIX COMMON NEWLINE ARTIFACTS
# =========================================================

def _cleanup_newlines(
    text: str
) -> str:

    # Horizontal whitespace around newline
    text = re.sub(
        r"[ \t]*\n[ \t]*",
        "\n",
        text
    )

    # Maximum two blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# =========================================================
# SAFETY CHECK
#
# Normalizer kendi yarattığı tehlikeli patternleri
# mümkün olduğunca geri çevirmeye çalışır.
# =========================================================

def _repair_known_bad_splits(
    text: str
) -> str:

    """
    Önceki V8.1 sürümünün oluşturduğu:
        renk: siz
        koku: suz
        DNEL: s
        pH: osph
    gibi yapıların yeni metinde oluşmaması gerekir.

    Bu fonksiyon yeni normalize edilen text için koruma
    amaçlıdır.
    """

    replacements = [
        (
            r"\brenk\s*:\s*siz\b",
            "renksiz"
        ),
        (
            r"\bkoku\s*:\s*suz\b",
            "kokusuz"
        ),
        (
            r"\bDNEL\s*:\s*s\b",
            "DNELs"
        ),
        (
            r"\bPNEC\s*:\s*s\b",
            "PNECs"
        ),
        (
            r"\bteleph\s*:\s*one\b",
            "telephone"
        ),
        (
            r"\btripolyph\s*:\s*osph\s*:\s*ate\b",
            "tripolyphosphate"
        ),
        (
            r"\btripolyph\s*:\s*osphate\b",
            "tripolyphosphate"
        ),
        (
            r"\bkullanım\s*:\s*ları\b",
            "kullanımları"
        ),
        (
            r"\bUyuşmaz\s*:\s*lıkları\b",
            "Uyuşmazlıkları"
        ),
        (
            r"\balev\s*:\s*len",
            "alevlen"
        ),
    ]

    for (
        pattern,
        replacement
    ) in replacements:

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE
        )

    return text


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def normalize_sds_structure(
    text: str
) -> str:

    """
    SDS structural normalization.

    Firma bağımsız.

    Sadece yapıyı iyileştirir.
    Veri extraction yapmaz.
    """

    if not text:
        return ""

    # 1
    text = _basic_normalize(
        text
    )

    # 2
    text = _separate_page_artifacts(
        text
    )

    # 3
    text = _break_before_section_headings(
        text
    )

    # 4
    text = _break_before_numbered_subheadings(
        text
    )

    # 5
    text = _fix_safe_concatenated_labels(
        text
    )

    # 6
    text = _break_before_semantic_labels(
        text
    )

    # 7
    text = _normalize_precautionary_code_groups(
        text
    )

    # 8
    text = _normalize_hazard_codes(
        text
    )

    # 9
    text = _repair_known_bad_splits(
        text
    )

    # 10
    text = _cleanup_newlines(
        text
    )

    return text