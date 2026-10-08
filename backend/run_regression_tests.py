import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

TEST_SCRIPT = BASE_DIR / "test_sds_file.py"


# =========================================================
# REGRESSION CASES
# =========================================================
#
# Buraya yalnız gerçekten doğruladığımız sonuçları koyuyoruz.
#
# Böylece parser daha sonra değiştirilirse:
#
# - H kodu kayboldu mu?
# - P kodu parçalandı mı?
# - Section splitter bozuldu mu?
# - CAS yanlış bölüme taşındı mı?
# - Section 7 / 8 / 9 tekrar bozuldu mu?
#
# otomatik olarak göreceğiz.
# =========================================================

REGRESSION_CASES = [
    {
        "name": "ICL BK2307",

        "pdf": (
            "uploads/"
            "983c798b8be6488e962b616f48b9a6ac.pdf"
        ),

        "checks": {

            # =============================================
            # DOCUMENT STRUCTURE
            # =============================================

            "section_count": 16,

            "section_numbers": [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
            ],

            # =============================================
            # SECTION 1
            # =============================================

            "section_1.product_name":
                "Potassium tripolyphosphate, solution 50%, low iron",

            "section_1.product_code":
                "BK2307",

            "section_1.ufi":
                "V873-MN1G-R608-8F3C; F2D6-U05E-800G-VATG",

            "section_1.cas_numbers": [],

            # =============================================
            # SECTION 2
            # =============================================

            "section_2.hazard_codes": {
                "mode": "set",
                "value": [
                    "H315",
                    "H319",
                    "H290",
                ],
            },

            "section_2.precautionary_codes": {
                "mode": "set",
                "value": [
                    "P280",
                    "P234",
                    "P305+P351+P338",
                    "P332+P313",
                    "P337+P313",
                    "P302+P352",
                ],
            },

            "section_2.signal_word":
                "Dikkat",

            # =============================================
            # SECTION 3
            # =============================================

            "section_3.cas_numbers": {
                "mode": "set",
                "value": [
                    "1310-58-3",
                ],
            },

            # =============================================
            # SECTION 7
            # =============================================

            "section_7.specific_end_use":
                "Belirli bir gereklilik yoktur.",

            "section_7.raw_subsection_7_1": {
                "mode": "not_empty",
            },

            "section_7.raw_subsection_7_2": {
                "mode": "not_empty",
            },

            "section_7.raw_subsection_7_3": {
                "mode": "not_empty",
            },

            "section_7.storage_conditions": {
                "mode": "contains",
                "value":
                    "Kapları kuru, serin ve iyi havalandırılan "
                    "bir yerde",
            },

            # =============================================
            # SECTION 8
            # =============================================

            "section_8.hand_protection": {
                "mode": "contains",
                "value":
                    "Sızdırmayan eldivenler Uygun eldiven giyin",
            },

            "section_8.eye_face_protection": {
                "mode": "contains",
                "value":
                    "emniyet gözlükleri",
            },

            "section_8.body_protection": {
                "mode": "contains",
                "value":
                    "Uzun kollu giysiler.",
            },

            "section_8.engineering_controls": {
                "mode": "contains",
                "value":
                    "Göz yıkama istasyonları",
            },

            # =============================================
            # SECTION 9
            # =============================================

            "section_9.ph":
                "~11.4",

            "section_9.melting_freezing_point":
                "< 0",

            "section_9.boiling_point":
                "> 100 °C",

            "section_9.vapour_pressure":
                "23hPa (20°C)",

            "section_9.density":
                "1.56 g/cm3",

            "section_9.solubility":
                "Tamamen karışabilir",

            # =============================================
            # REVISION
            # =============================================

            "revision.preparation_date":
                None,

            "revision.revision_date":
                "2021-07-15",

            "revision.version":
                "3",

            # =============================================
            # INGESTION
            # =============================================

            "ingestion_summary.is_probable_sds":
                True,

            "ingestion_summary.section_count":
                16,

            "ingestion_summary.parsed_data.product_code":
                "BK2307",

            "ingestion_summary.parsed_data.cas_numbers":
                [],

            "ingestion_summary.parsed_data.component_cas_numbers": {
                "mode": "set",
                "value": [
                    "1310-58-3",
                ],
            },

            "ingestion_summary.parsed_data.hazard_codes": {
                "mode": "set",
                "value": [
                    "H315",
                    "H319",
                    "H290",
                ],
            },

            "ingestion_summary.parsed_data.precautionary_codes": {
                "mode": "set",
                "value": [
                    "P280",
                    "P234",
                    "P305+P351+P338",
                    "P332+P313",
                    "P337+P313",
                    "P302+P352",
                ],
            },

            "ingestion_summary.parsed_data.signal_word":
                "Dikkat",

            "ingestion_summary.revision_data.revision_date":
                "2021-07-15",

            "ingestion_summary.revision_data.version":
                "3",
        },
    },
]


# =========================================================
# DICTIONARY PATH
# =========================================================

def get_nested_value(
    data: dict,
    path: str
) -> Any:

    current: Any = data

    for key in path.split("."):

        if not isinstance(
            current,
            dict
        ):
            raise KeyError(
                path
            )

        if key not in current:
            raise KeyError(
                path
            )

        current = current[key]

    return current


# =========================================================
# JSON EXTRACTION FROM test_sds_file.py OUTPUT
# =========================================================

def extract_result_json(
    stdout: str
) -> dict:

    marker = (
        "PARSER RESULT"
    )

    marker_position = stdout.find(
        marker
    )

    if marker_position == -1:

        raise RuntimeError(
            "PARSER RESULT başlığı bulunamadı."
        )

    remaining = stdout[
        marker_position
        + len(marker):
    ]

    json_start = remaining.find(
        "{"
    )

    if json_start == -1:

        raise RuntimeError(
            "Parser çıktısında JSON başlangıcı bulunamadı."
        )

    json_text = remaining[
        json_start:
    ]

    decoder = json.JSONDecoder()

    try:

        result, _ = decoder.raw_decode(
            json_text
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Parser çıktısındaki JSON okunamadı: "
            f"{exc}"
        ) from exc

    if not isinstance(
        result,
        dict
    ):

        raise RuntimeError(
            "Parser sonucu dictionary değil."
        )

    return result


# =========================================================
# RUN EXISTING TEST SCRIPT
# =========================================================

def run_parser(
    pdf_path: Path
) -> dict:

    env = os.environ.copy()

    # Windows terminal / redirected stdout can otherwise
    # fall back to cp1252 and fail on Turkish characters
    # such as İ, Ş, Ğ, ı.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    process = subprocess.run(
        [
            sys.executable,
            str(
                TEST_SCRIPT
            ),
            str(
                pdf_path
            ),
        ],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if process.returncode != 0:

        error_text = (
            process.stderr.strip()
            or process.stdout.strip()
        )

        raise RuntimeError(
            "test_sds_file.py başarısız oldu.\n"
            + error_text
        )

    return extract_result_json(
        process.stdout
    )


# =========================================================
# COMPARISON HELPERS
# =========================================================

def normalize_for_set(
    value: Any
) -> set:

    if value is None:
        return set()

    if isinstance(
        value,
        list
    ):

        return {
            str(item).strip()
            for item in value
        }

    return {
        str(value).strip()
    }


def value_contains(
    actual: Any,
    expected: str
) -> bool:

    expected_folded = (
        expected.casefold()
    )

    if isinstance(
        actual,
        list
    ):

        for item in actual:

            if (
                expected_folded
                in str(
                    item
                ).casefold()
            ):
                return True

        return False

    if actual is None:
        return False

    return (
        expected_folded
        in str(
            actual
        ).casefold()
    )


# =========================================================
# SINGLE CHECK
# =========================================================

def check_value(
    actual: Any,
    expected: Any
) -> tuple[bool, str]:

    # -----------------------------------------------------
    # SPECIAL CHECK MODE
    # -----------------------------------------------------

    if isinstance(
        expected,
        dict
    ) and "mode" in expected:

        mode = expected[
            "mode"
        ]

        # =============================================
        # SET COMPARISON
        # =============================================

        if mode == "set":

            expected_set = (
                normalize_for_set(
                    expected.get(
                        "value"
                    )
                )
            )

            actual_set = (
                normalize_for_set(
                    actual
                )
            )

            if (
                actual_set
                == expected_set
            ):

                return (
                    True,
                    ""
                )

            return (
                False,
                (
                    f"beklenen={sorted(expected_set)!r}, "
                    f"gelen={sorted(actual_set)!r}"
                )
            )

        # =============================================
        # CONTAINS
        # =============================================

        if mode == "contains":

            expected_value = str(
                expected.get(
                    "value",
                    ""
                )
            )

            if value_contains(
                actual,
                expected_value
            ):

                return (
                    True,
                    ""
                )

            return (
                False,
                (
                    f"'{expected_value}' bulunamadı. "
                    f"gelen={actual!r}"
                )
            )

        # =============================================
        # NOT EMPTY
        # =============================================

        if mode == "not_empty":

            if actual is None:

                return (
                    False,
                    "değer None"
                )

            if isinstance(
                actual,
                str
            ):

                if actual.strip():

                    return (
                        True,
                        ""
                    )

                return (
                    False,
                    "boş string"
                )

            if isinstance(
                actual,
                (
                    list,
                    dict,
                    tuple,
                    set,
                )
            ):

                if len(actual) > 0:

                    return (
                        True,
                        ""
                    )

                return (
                    False,
                    "boş koleksiyon"
                )

            return (
                True,
                ""
            )

        return (
            False,
            f"Bilinmeyen test modu: {mode}"
        )

    # -----------------------------------------------------
    # NORMAL EQUALITY
    # -----------------------------------------------------

    if actual == expected:

        return (
            True,
            ""
        )

    return (
        False,
        (
            f"beklenen={expected!r}, "
            f"gelen={actual!r}"
        )
    )


# =========================================================
# RUN ONE CASE
# =========================================================

def run_case(
    case: dict
) -> dict:

    name = case[
        "name"
    ]

    pdf_path = (
        BASE_DIR
        / case[
            "pdf"
        ]
    )

    result = {
        "name": name,
        "status": "PASS",
        "passed": 0,
        "failed": 0,
        "errors": [],
    }

    if not pdf_path.exists():

        result[
            "status"
        ] = "ERROR"

        result[
            "errors"
        ].append(
            "PDF bulunamadı: "
            + str(
                pdf_path
            )
        )

        return result

    try:

        parser_result = (
            run_parser(
                pdf_path
            )
        )

    except Exception as exc:

        result[
            "status"
        ] = "ERROR"

        result[
            "errors"
        ].append(
            str(
                exc
            )
        )

        return result

    for (
        path,
        expected
    ) in case[
        "checks"
    ].items():

        try:

            actual = (
                get_nested_value(
                    parser_result,
                    path
                )
            )

        except KeyError:

            result[
                "failed"
            ] += 1

            result[
                "errors"
            ].append(
                f"{path}: ALAN BULUNAMADI"
            )

            continue

        passed, message = (
            check_value(
                actual,
                expected
            )
        )

        if passed:

            result[
                "passed"
            ] += 1

        else:

            result[
                "failed"
            ] += 1

            result[
                "errors"
            ].append(
                f"{path}: {message}"
            )

    if (
        result[
            "failed"
        ] > 0
    ):

        result[
            "status"
        ] = "FAIL"

    return result


# =========================================================
# PRINT
# =========================================================

def print_case_result(
    result: dict
) -> None:

    status = result[
        "status"
    ]

    name = result[
        "name"
    ]

    if status == "PASS":

        symbol = "[PASS]"

    elif status == "FAIL":

        symbol = "[FAIL]"

    else:

        symbol = "[ERROR]"

    print(
        f"{symbol} {name}"
    )

    print(
        f"       Başarılı kontrol: "
        f"{result['passed']}"
    )

    print(
        f"       Başarısız kontrol: "
        f"{result['failed']}"
    )

    if result[
        "errors"
    ]:

        for error in result[
            "errors"
        ]:

            print(
                f"       - {error}"
            )

    print()


# =========================================================
# MAIN
# =========================================================

def main() -> int:

    print(
        "=" * 70
    )

    print(
        "GEBKIM SDS REGRESSION TESTS"
    )

    print(
        "=" * 70
    )

    print()

    if not TEST_SCRIPT.exists():

        print(
            "[ERROR] test_sds_file.py bulunamadı:"
        )

        print(
            TEST_SCRIPT
        )

        return 1

    results = []

    for case in REGRESSION_CASES:

        result = run_case(
            case
        )

        results.append(
            result
        )

        print_case_result(
            result
        )

    total = len(
        results
    )

    passed = sum(
        1
        for result in results
        if result[
            "status"
        ] == "PASS"
    )

    failed = sum(
        1
        for result in results
        if result[
            "status"
        ] == "FAIL"
    )

    errors = sum(
        1
        for result in results
        if result[
            "status"
        ] == "ERROR"
    )

    print(
        "=" * 70
    )

    print(
        "ÖZET"
    )

    print(
        "=" * 70
    )

    print(
        f"Toplam test : {total}"
    )

    print(
        f"PASS        : {passed}"
    )

    print(
        f"FAIL        : {failed}"
    )

    print(
        f"ERROR       : {errors}"
    )

    print()

    if (
        failed == 0
        and errors == 0
    ):

        print(
            "TÜM REGRESSION TESTLERİ BAŞARILI."
        )

        return 0

    print(
        "REGRESSION HATASI VAR."
    )

    return 1


if __name__ == "__main__":

    raise SystemExit(
        main()
    )