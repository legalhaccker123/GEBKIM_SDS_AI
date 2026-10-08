import re

from app.services.data_quality import (
    is_meaningful_value,
    normalize_quality_text,
)


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_line(
    line: str
) -> str:

    line = line.strip()

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


def get_clean_lines(
    text: str
) -> list[str]:

    result = []

    for raw_line in text.splitlines():

        line = clean_line(
            raw_line
        )

        if line:
            result.append(
                line
            )

    return result


def unique_strings(
    values: list[str]
) -> list[str]:

    result = []
    seen = set()

    for value in values:

        value = normalize_quality_text(
            value
        )

        if not value:
            continue

        key = value.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(
            value
        )

    return result


# =========================================================
# LABEL NORMALIZATION
# =========================================================

def normalize_label(
    label: str
) -> str:

    label = clean_line(
        label
    )

    label = re.sub(
        r"^\d+(?:\.\d+)*\.?\s*",
        "",
        label
    )

    label = re.sub(
        r"\s*:\s*$",
        "",
        label
    )

    return label.strip().lower()


def label_matches(
    text: str,
    aliases: list[str]
) -> bool:

    normalized = normalize_label(
        text
    )

    for alias in aliases:

        alias_normalized = (
            normalize_label(
                alias
            )
        )

        if normalized == alias_normalized:
            return True

    return False


# =========================================================
# FIND LABEL AT START OF LINE
# =========================================================

def find_matching_alias(
    line: str,
    aliases: list[str]
) -> str | None:

    cleaned = clean_line(
        line
    )

    # Remove subsection numbering:
    # 8.2.2.1 Göz Korunması
    cleaned_without_number = re.sub(
        r"^\d+(?:\.\d+)*\.?\s*",
        "",
        cleaned
    )

    aliases_sorted = sorted(
        aliases,
        key=len,
        reverse=True
    )

    for alias in aliases_sorted:

        pattern = re.compile(
            rf"^{re.escape(alias)}"
            rf"(?:\s*:|\s|$)",
            flags=re.IGNORECASE
        )

        if pattern.search(
            cleaned_without_number
        ):

            return alias

    return None


# =========================================================
# INLINE LABEL/VALUE
#
# Examples:
# Renk: Beyaz
# Renk Beyaz
# =========================================================

def extract_inline_value(
    line: str,
    aliases: list[str]
) -> str | None:

    cleaned = clean_line(
        line
    )

    cleaned = re.sub(
        r"^\d+(?:\.\d+)*\.?\s*",
        "",
        cleaned
    )

    aliases_sorted = sorted(
        aliases,
        key=len,
        reverse=True
    )

    for alias in aliases_sorted:

        # LABEL : VALUE
        match = re.match(
            rf"^{re.escape(alias)}"
            rf"\s*:\s*(.+)$",
            cleaned,
            flags=re.IGNORECASE
        )

        if match:

            value = normalize_quality_text(
                match.group(1)
            )

            if is_meaningful_value(
                value
            ):
                return value

        # LABEL VALUE
        match = re.match(
            rf"^{re.escape(alias)}"
            rf"\s+(.+)$",
            cleaned,
            flags=re.IGNORECASE
        )

        if match:

            value = normalize_quality_text(
                match.group(1)
            )

            # Avoid returning ":" as value
            if is_meaningful_value(
                value
            ):
                return value

    return None


# =========================================================
# NEXT LINE VALUE
#
# Example:
# Renk
# Beyaz
# =========================================================

def extract_next_line_value(
    lines: list[str],
    index: int,
    all_aliases: list[str]
) -> str | None:

    if index + 1 >= len(lines):
        return None

    candidate = normalize_quality_text(
        lines[
            index + 1
        ]
    )

    if not is_meaningful_value(
        candidate
    ):
        return None

    # If next line itself is another label,
    # don't use it as a value.
    if find_matching_alias(
        candidate,
        all_aliases
    ):

        return None

    return candidate


# =========================================================
# GENERIC SINGLE-FIELD EXTRACTION
# =========================================================

def extract_field_value(
    lines: list[str],
    aliases: list[str],
    all_aliases: list[str] | None = None
) -> str | None:

    if all_aliases is None:
        all_aliases = aliases

    for index, line in enumerate(lines):

        alias = find_matching_alias(
            line,
            aliases
        )

        if not alias:
            continue

        inline = extract_inline_value(
            line,
            aliases
        )

        if inline:
            return inline

        next_value = (
            extract_next_line_value(
                lines,
                index,
                all_aliases
            )
        )

        if next_value:
            return next_value

    return None


# =========================================================
# COLUMN / TABLE LAYOUT
#
# Example:
#
# Fiziksel Hali :
# Renk :
# Koku :
# Yoğunluk :
#
# sıvı
# renksiz
# solvent
# 0,840
# =========================================================

def extract_column_layout(
    lines: list[str],
    field_aliases: dict[str, list[str]],
    min_labels: int = 3
) -> dict[str, str]:

    result = {}

    all_aliases = []

    for aliases in field_aliases.values():
        all_aliases.extend(
            aliases
        )

    index = 0

    while index < len(lines):

        labels_found = []
        cursor = index

        # ---------------------------------------------
        # Consecutive label block
        # ---------------------------------------------

        while cursor < len(lines):

            line = lines[cursor]

            matched_field = None

            for field_name, aliases in (
                field_aliases.items()
            ):

                alias = find_matching_alias(
                    line,
                    aliases
                )

                if not alias:
                    continue

                # Important:
                # only treat it as a column label if
                # there is no meaningful inline value.
                inline = extract_inline_value(
                    line,
                    aliases
                )

                if inline:
                    matched_field = None
                    break

                matched_field = field_name
                break

            if not matched_field:
                break

            labels_found.append(
                matched_field
            )

            cursor += 1

        if len(labels_found) < min_labels:

            index += 1
            continue

        # ---------------------------------------------
        # Values after label block
        # ---------------------------------------------

        values = []

        value_cursor = cursor

        while (
            value_cursor < len(lines)
            and len(values)
            < len(labels_found)
        ):

            candidate = normalize_quality_text(
                lines[
                    value_cursor
                ]
            )

            if not candidate:

                value_cursor += 1
                continue

            # Next SDS section / subsection
            if re.match(
                r"^(?:BÖLÜM|SECTION)\s+\d+",
                candidate,
                flags=re.IGNORECASE
            ):
                break

            # Another recognized property label
            if find_matching_alias(
                candidate,
                all_aliases
            ):

                break

            if is_meaningful_value(
                candidate
            ):

                values.append(
                    candidate
                )

            value_cursor += 1

        # ---------------------------------------------
        # Map labels -> values
        # ---------------------------------------------

        if len(values) >= 2:

            for field_name, value in zip(
                labels_found,
                values
            ):

                if (
                    field_name
                    not in result
                    and is_meaningful_value(
                        value
                    )
                ):

                    result[
                        field_name
                    ] = value

            index = value_cursor
            continue

        index += 1

    return result


# =========================================================
# SEMANTIC BLOCK EXTRACTION
#
# Used in Section 7 / 8.
# =========================================================

def extract_semantic_block(
    text: str,
    aliases: list[str],
    stop_aliases: list[str] | None = None,
    stop_patterns: list[str] | None = None
) -> list[str]:

    lines = get_clean_lines(
        text
    )

    if stop_aliases is None:
        stop_aliases = []

    if stop_patterns is None:
        stop_patterns = []

    all_stop_aliases = (
        stop_aliases
    )

    for index, line in enumerate(lines):

        alias = find_matching_alias(
            line,
            aliases
        )

        if not alias:
            continue

        result = []

        inline = extract_inline_value(
            line,
            aliases
        )

        if inline:
            result.append(
                inline
            )

        for next_line in lines[
            index + 1:
        ]:

            if find_matching_alias(
                next_line,
                all_stop_aliases
            ):
                break

            if any(
                re.match(
                    pattern,
                    next_line,
                    flags=re.IGNORECASE
                )
                for pattern in stop_patterns
            ):
                break

            result.append(
                next_line
            )

        return unique_strings(
            result
        )

    return []