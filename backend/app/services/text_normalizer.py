import re
import unicodedata


# =========================================================
# COMMON PDF / ENCODING REPLACEMENTS
# =========================================================

CHARACTER_REPLACEMENTS = {
    # Turkish characters frequently broken in PDFs
    "Ģ": "ş",
    "ġ": "Ş",
    "Ġ": "İ",
    "ý": "ı",
    "Ý": "İ",

    # Common UTF-8 mojibake
    "Ã§": "ç",
    "Ã‡": "Ç",
    "Ã¼": "ü",
    "Ãœ": "Ü",
    "Ã¶": "ö",
    "Ã–": "Ö",
    "ÄŸ": "ğ",
    "Äž": "Ğ",
    "ÅŸ": "ş",
    "Åž": "Ş",
    "Ä±": "ı",
    "Ä°": "İ",

    # Spaces / punctuation
    "\u00a0": " ",
    "\u200b": "",
    "\ufeff": "",
}


def normalize_sds_text(
    text: str
) -> str:

    if not text:
        return ""

    result = text

    # -----------------------------------------------------
    # CHARACTER REPLACEMENTS
    # -----------------------------------------------------

    for bad, good in CHARACTER_REPLACEMENTS.items():

        result = result.replace(
            bad,
            good
        )

    # -----------------------------------------------------
    # UNICODE NORMALIZATION
    # -----------------------------------------------------

    result = unicodedata.normalize(
        "NFKC",
        result
    )

    # -----------------------------------------------------
    # NORMALIZE LINE ENDINGS
    # -----------------------------------------------------

    result = result.replace(
        "\r\n",
        "\n"
    )

    result = result.replace(
        "\r",
        "\n"
    )

    # -----------------------------------------------------
    # REMOVE EXCESSIVE SPACES INSIDE LINES
    # -----------------------------------------------------

    normalized_lines = []

    for line in result.splitlines():

        line = re.sub(
            r"[ \t]+",
            " ",
            line
        )

        normalized_lines.append(
            line.rstrip()
        )

    result = "\n".join(
        normalized_lines
    )

    # -----------------------------------------------------
    # TOO MANY BLANK LINES
    # -----------------------------------------------------

    result = re.sub(
        r"\n{4,}",
        "\n\n\n",
        result
    )

    return result.strip()