import re
import unicodedata


# =========================================================
# UNIVERSAL SDS SECTION SPLITTER
#
# V8.3.2
#
# Turkish / Unicode safe section-title matching.
#
# Supports:
#
# BÖLÜM 1:
# SECTION 1:
# 1. MADDENİN/KARIŞIMIN...
#
# Also supports subsection-based recovery if a main section
# heading is genuinely missing from PDF extraction.
# =========================================================


# =========================================================
# SECTION TITLE HINTS
# =========================================================

SECTION_TITLE_HINTS = {

    1: [
        "kimliği",
        "kimligi",
        "identification",
    ],

    2: [
        "zararlılık",
        "zararlilik",
        "hazard",
    ],

    3: [
        "bileşim",
        "bilesim",
        "içindekiler",
        "icindekiler",
        "composition",
        "ingredients",
    ],

    4: [
        "ilk yardım",
        "first aid",
    ],

    5: [
        "yangın",
        "yangin",
        "firefighting",
        "fire-fighting",
    ],

    6: [
        "kaza sonucu",
        "yayılma",
        "yayilma",
        "accidental release",
    ],

    7: [
        "elleçleme",
        "ellecleme",
        "depolama",
        "handling",
        "storage",
    ],

    8: [
        "maruz kalma",
        "maruziyet",
        "kişisel korunma",
        "kisisel korunma",
        "exposure controls",
        "personal protection",
    ],

    9: [
        "fiziksel",
        "kimyasal özellik",
        "kimyasal ozellik",
        "physical",
        "chemical properties",
    ],

    10: [
        "kararlılık",
        "kararlilik",
        "tepkime",
        "stability",
        "reactivity",
    ],

    11: [
        "toksikolojik",
        "toksikoloji",
        "toxicological",
    ],

    12: [
        "ekolojik",
        "ecological",
    ],

    13: [
        "bertaraf",
        "atık",
        "atik",
        "disposal",
    ],

    14: [
        "taşımacılık",
        "tasimacilik",
        "transport",
    ],

    15: [
        "mevzuat",
        "regulatory",
    ],

    16: [
        "diğer bilgiler",
        "diger bilgiler",
        "other information",
    ],

}


# =========================================================
# TEXT NORMALIZATION
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
        "\u00a0",
        " "
    )

    return text


# =========================================================
# UNICODE-SAFE MATCH NORMALIZATION
#
# Important for Turkish:
#
# "İlk yardım".lower()
#
# may produce:
#
# i + COMBINING DOT ABOVE
#
# rather than plain ASCII-style "ilk yardım".
#
# Therefore section-title matching must normalize Unicode
# before comparison.
# =========================================================

def _normalize_for_match(
    value: str
) -> str:

    if not value:
        return ""

    # Turkish dotless i -> ordinary i for semantic matching
    value = value.replace(
        "ı",
        "i"
    )

    value = value.replace(
        "I",
        "i"
    )

    # casefold is stronger and safer than lower()
    value = value.casefold()

    # Decompose characters:
    # İ -> i + combining dot
    # ş -> s + combining mark, etc.
    value = unicodedata.normalize(
        "NFKD",
        value
    )

    # Remove combining marks
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    # Normalize whitespace
    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value


# =========================================================
# HEADING PATTERNS
# =========================================================

WORD_SECTION_PATTERN = re.compile(
    r"\b"
    r"(BÖLÜM|BOLUM|SECTION)"
    r"\s*"
    r"(1[0-6]|[1-9])"
    r"\s*"
    r"([:.\-]?)",
    flags=re.IGNORECASE
)


LEGACY_NUMBER_PATTERN = re.compile(
    r"(?m)"
    r"(^|\n)"
    r"\s*"
    r"(1[0-6]|[1-9])"
    r"\s*[.)\-:]"
    r"\s*"
)


# =========================================================
# CONTEXT
# =========================================================

def _following_text(
    text: str,
    end_position: int,
    length: int = 220
) -> str:

    return (
        text[
            end_position:
            end_position + length
        ]
        .replace(
            "\n",
            " "
        )
        .strip()
    )


def _has_correct_title(
    section_number: int,
    following_text: str
) -> bool:

    hints = SECTION_TITLE_HINTS.get(
        section_number,
        []
    )

    normalized_context = (
        _normalize_for_match(
            following_text
        )
    )

    for hint in hints:

        normalized_hint = (
            _normalize_for_match(
                hint
            )
        )

        if (
            normalized_hint
            and normalized_hint
            in normalized_context
        ):
            return True

    return False


# =========================================================
# EXPLICIT BÖLÜM / SECTION CANDIDATES
# =========================================================

def _is_heading_line_start(
    text: str,
    position: int
) -> bool:

    line_start = (
        text.rfind(
            "\n",
            0,
            position
        )
        + 1
    )

    prefix = text[
        line_start:
        position
    ].strip()

    if not prefix:
        return True

    return bool(
        re.fullmatch(
            r"[-–—•·ꞏ*_:|/\\\s]*",
            prefix
        )
    )


def _is_reference_like_word_candidate(
    text: str,
    match: re.Match
) -> bool:

    punctuation = (
        match.group(3)
        or ""
    ).strip()

    at_line_start = (
        _is_heading_line_start(
            text,
            match.start()
        )
    )

    following = _following_text(
        text,
        match.end(),
        length=160
    )

    normalized_following = (
        _normalize_for_match(
            following
        )
    )

    # "See Section 7 for information..."
    # gibi satır ortasında geçen referansları
    # gerçek bölüm başlığı olarak kabul etme.
    if (
        punctuation
        not in {":", "-"}
        and not at_line_start
    ):
        return True

    # Açık referans kalıpları.
    if punctuation in {"", "."}:

        reference_starts = (
            "for information",
            "for more information",
            "see ",
            "refer to ",
            "reference to ",
            "bkz",
            "bakiniz",
        )

        if normalized_following.startswith(
            reference_starts
        ):
            return True

    return False


def _find_word_candidates(
    text: str
) -> list[dict]:

    candidates = []

    for match in (
        WORD_SECTION_PATTERN
        .finditer(text)
    ):

        section_number = int(
            match.group(2)
        )

        if _is_reference_like_word_candidate(
            text,
            match
        ):
            continue

        following = _following_text(
            text,
            match.end(),
            length=160
        )

        if not _has_correct_title(
            section_number,
            following
        ):
            continue

        candidates.append(
            {
                "section_number":
                    section_number,

                "start":
                    match.start(),

                "end":
                    match.end(),

                "source":
                    "word_heading",
            }
        )

    return candidates


# =========================================================
# LEGACY NUMBERED HEADINGS
# =========================================================

def _find_legacy_candidates(
    text: str
) -> list[dict]:

    candidates = []

    for match in (
        LEGACY_NUMBER_PATTERN
        .finditer(text)
    ):

        section_number = int(
            match.group(2)
        )

        following = _following_text(
            text,
            match.end()
        )

        if not _has_correct_title(
            section_number,
            following
        ):
            continue

        start = match.start()

        if (
            start < len(text)
            and text[start:start + 1]
            == "\n"
        ):
            start += 1

        candidates.append(
            {
                "section_number":
                    section_number,

                "start":
                    start,

                "end":
                    match.end(),

                "source":
                    "legacy_heading",
            }
        )

    return candidates


# =========================================================
# DEDUPLICATE
# =========================================================

def _deduplicate_candidates(
    candidates: list[dict]
) -> list[dict]:

    result = []
    seen = set()

    for candidate in sorted(
        candidates,
        key=lambda item: (
            item["start"],
            item["section_number"],
        )
    ):

        key = (
            candidate[
                "section_number"
            ],
            candidate[
                "start"
            ],
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        result.append(
            candidate
        )

    return result


# =========================================================
# INITIAL ORDERED SEQUENCE
# =========================================================

def _choose_initial_sequence(
    candidates: list[dict]
) -> list[dict]:

    if not candidates:
        return []

    candidates = (
        _deduplicate_candidates(
            candidates
        )
    )

    selected = []

    last_position = -1

    # SDS bölümlerini mantıksal olarak
    # 1 -> 16 sırasıyla seç.
    #
    # Böylece Bölüm 6 içindeki:
    #
    # "See Section 13 for disposal information"
    #
    # gibi bir referans gerçek Bölüm 13 olarak
    # algılanıp Bölüm 7-12'yi devre dışı bırakamaz.
    for section_number in range(
        1,
        17
    ):

        possible_candidates = [
            candidate
            for candidate in candidates
            if (
                candidate[
                    "section_number"
                ]
                == section_number
                and candidate[
                    "start"
                ]
                > last_position
            )
        ]

        if not possible_candidates:
            continue

        selected_candidate = min(
            possible_candidates,
            key=lambda item:
                item["start"]
        )

        selected.append(
            selected_candidate
        )

        last_position = (
            selected_candidate[
                "start"
            ]
        )

    return selected


# =========================================================
# MISSING SECTION RECOVERY
# =========================================================

def _find_subsection_recovery_candidate(
    text: str,
    section_number: int,
    search_start: int,
    search_end: int
) -> dict | None:

    if search_end <= search_start:
        return None

    region = text[
        search_start:
        search_end
    ]

    # Important:
    # Prevent matching 14.1 while searching for 4.1.
    #
    # (?<!\d) ensures the number is not preceded by another
    # digit.
    pattern = re.compile(
        rf"(?<!\d)"
        rf"{section_number}"
        rf"\s*\.\s*"
        rf"1"
        rf"\.?"
        rf"\s+",
        flags=re.IGNORECASE
    )

    for match in pattern.finditer(
        region
    ):

        absolute_start = (
            search_start
            + match.start()
        )

        absolute_end = (
            search_start
            + match.end()
        )

        context = _following_text(
            text,
            absolute_end,
            length=300
        )

        if not _has_correct_title(
            section_number,
            context
        ):
            continue

        return {
            "section_number":
                section_number,

            "start":
                absolute_start,

            "end":
                absolute_end,

            "source":
                "recovered_from_subsection",
        }

    return None


# =========================================================
# RECOVER HOLES
# =========================================================

def _recover_missing_sections(
    text: str,
    selected: list[dict]
) -> list[dict]:

    if len(selected) < 2:
        return selected

    recovered = list(
        selected
    )

    ordered = sorted(
        selected,
        key=lambda item:
            item["start"]
    )

    for index in range(
        len(ordered) - 1
    ):

        current = (
            ordered[index]
        )

        following = (
            ordered[index + 1]
        )

        current_number = (
            current[
                "section_number"
            ]
        )

        next_number = (
            following[
                "section_number"
            ]
        )

        if (
            next_number
            <= current_number + 1
        ):
            continue

        for missing_number in range(
            current_number + 1,
            next_number
        ):

            candidate = (
                _find_subsection_recovery_candidate(
                    text=text,
                    section_number=
                        missing_number,
                    search_start=
                        current["end"],
                    search_end=
                        following["start"],
                )
            )

            if candidate:

                recovered.append(
                    candidate
                )

    return sorted(
        recovered,
        key=lambda item:
            item["start"]
    )


# =========================================================
# FINAL MONOTONIC FILTER
# =========================================================

def _final_sequence_filter(
    candidates: list[dict]
) -> list[dict]:

    if not candidates:
        return []

    result = []

    last_section = 0
    last_position = -1

    for candidate in sorted(
        candidates,
        key=lambda item:
            item["start"]
    ):

        section_number = (
            candidate[
                "section_number"
            ]
        )

        position = (
            candidate[
                "start"
            ]
        )

        if position <= last_position:
            continue

        if section_number <= last_section:
            continue

        result.append(
            candidate
        )

        last_section = (
            section_number
        )

        last_position = (
            position
        )

    return result


# =========================================================
# BUILD SECTIONS
# =========================================================

def _build_sections(
    text: str,
    candidates: list[dict]
) -> dict[int, str]:

    sections = {}

    candidates = sorted(
        candidates,
        key=lambda item:
            item["start"]
    )

    for index, candidate in enumerate(
        candidates
    ):

        section_number = (
            candidate[
                "section_number"
            ]
        )

        start = (
            candidate[
                "start"
            ]
        )

        if (
            index + 1
            < len(candidates)
        ):

            end = (
                candidates[
                    index + 1
                ][
                    "start"
                ]
            )

        else:

            end = len(
                text
            )

        content = (
            text[
                start:
                end
            ]
            .strip()
        )

        if content:

            sections[
                section_number
            ] = content

    return sections


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def split_sds_sections(
    text: str
) -> dict[int, str]:

    text = _normalize_text(
        text
    )

    if not text:
        return {}

    # -----------------------------------------------------
    # Explicit headings
    # -----------------------------------------------------

    candidates = (
        _find_word_candidates(
            text
        )
    )

    candidates.extend(
        _find_legacy_candidates(
            text
        )
    )

    # -----------------------------------------------------
    # Initial ordered sequence
    # -----------------------------------------------------

    selected = (
        _choose_initial_sequence(
            candidates
        )
    )

    # -----------------------------------------------------
    # Recover actual missing sections
    # -----------------------------------------------------

    selected = (
        _recover_missing_sections(
            text,
            selected
        )
    )

    # -----------------------------------------------------
    # Reject later backward references such as a
    # "BÖLÜM 8" reference inside Section 16.
    # -----------------------------------------------------

    selected = (
        _final_sequence_filter(
            selected
        )
    )

    return _build_sections(
        text,
        selected
    )