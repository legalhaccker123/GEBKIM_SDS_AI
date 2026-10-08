import re


def _unique(values: list[str]) -> list[str]:
    return list(
        dict.fromkeys(
            value.strip().upper()
            for value in values
            if value and value.strip()
        )
    )


H_TO_GHS = {
    "H302": ["GHS07"],
    "H312": ["GHS07"],
    "H315": ["GHS07"],
    "H317": ["GHS07"],
    "H319": ["GHS07"],
    "H332": ["GHS07"],

    "H318": ["GHS05"],

    "H314": ["GHS05"],

    "H400": ["GHS09"],
    "H410": ["GHS09"],
    "H411": ["GHS09"],
}


def find_ghs_codes(
    text: str,
    hazard_codes: list[str] | None = None
) -> list[str]:

    # =====================================================
    # 1. PDF METNİNDE AÇIK GHS KODU ARA
    # =====================================================

    values = re.findall(
        r"\bGHS\s*0?[1-9]\b",
        text,
        flags=re.IGNORECASE
    )

    normalized = []

    for value in values:

        number_match = re.search(
            r"([1-9])",
            value
        )

        if not number_match:
            continue

        normalized.append(
            f"GHS0{number_match.group(1)}"
        )

    # =====================================================
    # 2. H KODLARINDAN GÜVENİLİR FALLBACK
    # =====================================================

    if hazard_codes:

        for hazard_code in hazard_codes:

            mapped_codes = H_TO_GHS.get(
                hazard_code.upper(),
                []
            )

            normalized.extend(
                mapped_codes
            )

    return _unique(
        normalized
    )