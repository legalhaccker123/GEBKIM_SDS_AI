import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import * as XLSX from "xlsx";

import {
  calculateCoshhAnalysis,
} from "./coshhEngine";


function normalizeList(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }

  if (!value) {
    return [];
  }

  return [value];
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(
    `${value}T00:00:00`
  );

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "tr-TR"
  ).format(date);
}


function createEmptyForm() {
  return {
    process_name: "",
    department: "",
    exposed_workers: "",
    occupational_exposure_limit: "",
    process_description: "",
    amount_value: "",
    amount_unit: "kg",
    usage_scale: "",
    physical_form: "",
    dustiness: "",
    process_temperature: "",
    exposure_duration: "",
    exposure_frequency: "",
    closed_system: "",
    local_exhaust: "",
    general_ventilation: "",
    existing_ppe: "",
    existing_controls: "",
  };
}


function safeFileName(value) {
  return String(
    value || "kimyasal"
  )
    .replace(
      /[<>:"/\\|?*]/g,
      "_"
    )
    .replace(
      /\s+/g,
      "_"
    )
    .slice(
      0,
      80
    );
}


function getIdentifierValue(
  chemical,
  type
) {
  if (!chemical) {
    return "—";
  }

  const possibleLists = [
    chemical.identifiers,
    chemical.chemical_identifiers,
  ];


  for (
    const list
    of possibleLists
  ) {
    if (
      Array.isArray(list)
    ) {
      const record =
        list.find(
          (item) =>
            String(
              item.identifier_type ||
              item.type ||
              ""
            )
              .trim()
              .toUpperCase() ===
            type.toUpperCase()
        );

      if (record) {
        return (
          record.identifier_value ||
          record.value ||
          "—"
        );
      }
    }
  }


  if (
    type.toUpperCase() ===
    "CAS"
  ) {
    return (
      chemical.cas_number ||
      chemical.cas ||
      "—"
    );
  }


  return "—";
}


const controlStyle = {
  width: "100%",
  minHeight: "44px",
  border: "1px solid #d7dce2",
  borderRadius: "10px",
  padding: "10px 12px",
  font: "inherit",
  background: "#ffffff",
  boxSizing: "border-box",
};


const textareaStyle = {
  ...controlStyle,
  minHeight: "105px",
  resize: "vertical",
};


const fieldStyle = {
  display: "grid",
  gap: "8px",
};


const gridStyle = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(240px, 1fr))",
  gap: "18px",
};


const analysisCardStyle = {
  border: "1px solid #dde2e8",
  borderRadius: "12px",
  padding: "18px",
  background: "#ffffff",
};


const analysisTitleStyle = {
  fontSize: "12px",
  fontWeight: "700",
  color: "#687381",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  marginBottom: "8px",
};


const analysisValueStyle = {
  fontSize: "20px",
  fontWeight: "700",
  color: "#20262d",
};


const tableStyle = {
  width: "100%",
  minWidth: "1700px",
  borderCollapse: "collapse",
  fontSize: "13px",
};


const tableHeaderStyle = {
  border: "1px solid #d9dee5",
  padding: "10px",
  background: "#f5f7f9",
  textAlign: "left",
  verticalAlign: "top",
  fontWeight: "700",
};


const tableCellStyle = {
  border: "1px solid #d9dee5",
  padding: "10px",
  verticalAlign: "top",
  lineHeight: "1.45",
};


function CoshhAssessment({
  chemicals,
  apiBaseUrl,
  initialChemicalId = "",
  onBackInventory,
}) {
  const [
    selectedChemicalId,
    setSelectedChemicalId,
  ] = useState("");

  const [
    sdsDetail,
    setSdsDetail,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    form,
    setForm,
  ] = useState(
    createEmptyForm()
  );

  const [
    draft,
    setDraft,
  ] = useState(null);

  const resultRef =
    useRef(null);


  const eligibleChemicals =
    useMemo(
      () =>
        chemicals.filter(
          (chemical) => {
            if (
              !chemical
                .current_sds
                ?.id
            ) {
              return false;
            }

            const productName =
              String(
                chemical
                  .product_name ||
                  ""
              )
                .trim()
                .toLocaleLowerCase(
                  "tr-TR"
                );

            const manufacturer =
              String(
                chemical
                  .manufacturer ||
                  ""
              )
                .trim()
                .toLocaleLowerCase(
                  "tr-TR"
                );

            const invalidProductNames =
              [
                "",
                "string",
                "test",
                "test product",
              ];

            const invalidManufacturers =
              [
                "string",
                "test manufacturer",
              ];

            if (
              invalidProductNames.includes(
                productName
              )
            ) {
              return false;
            }

            if (
              invalidManufacturers.includes(
                manufacturer
              )
            ) {
              return false;
            }

            return true;
          }
        ),
      [
        chemicals,
      ]
    );


  const selectedChemical =
    useMemo(
      () =>
        chemicals.find(
          (chemical) =>
            String(
              chemical.id
            ) ===
            String(
              selectedChemicalId
            )
        ) || null,
      [
        chemicals,
        selectedChemicalId,
      ]
    );


  function updateField(
    field,
    value
  ) {
    setForm(
      (current) => ({
        ...current,
        [field]: value,
      })
    );

    setDraft(null);
  }


  async function prepareChemical(
    chemicalId
  ) {
    const normalizedId =
      chemicalId
        ? Number(
            chemicalId
          )
        : "";

    setSelectedChemicalId(
      normalizedId
    );

    setSdsDetail(null);
    setDraft(null);
    setError("");

    setForm(
      createEmptyForm()
    );


    if (!normalizedId) {
      return;
    }


    const chemical =
      chemicals.find(
        (item) =>
          Number(
            item.id
          ) ===
          normalizedId
      );


    if (!chemical) {
      setError(
        "Seçilen kimyasal bulunamadı."
      );

      return;
    }


    if (
      !chemical
        .current_sds
        ?.id
    ) {
      setError(
        "Bu kimyasal için güncel SDS bulunmuyor."
      );

      return;
    }


    try {
      setLoading(true);


      const response =
        await fetch(
          `${apiBaseUrl}/sds/${chemical.current_sds.id}/sections`
        );


      let data = null;


      try {
        data =
          await response.json();
      } catch {
        data = null;
      }


      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "SDS bilgileri alınamadı."
        );
      }


      setSdsDetail(
        data
      );


      const sourceState =
        String(
          data
            ?.physical_properties
            ?.physical_state ||
            ""
        ).toLocaleLowerCase(
          "tr-TR"
        );


      let detectedForm = "";


      if (
        sourceState.includes(
          "sıvı"
        ) ||
        sourceState.includes(
          "sivi"
        )
      ) {
        detectedForm =
          "Sıvı";
      } else if (
        sourceState.includes(
          "katı"
        ) ||
        sourceState.includes(
          "kati"
        ) ||
        sourceState.includes(
          "toz"
        )
      ) {
        detectedForm =
          "Katı";
      } else if (
        sourceState.includes(
          "gaz"
        ) ||
        sourceState.includes(
          "buhar"
        )
      ) {
        detectedForm =
          "Gaz";
      }


      setForm(
        (current) => ({
          ...current,
          physical_form:
            detectedForm,
        })
      );

    } catch (
      requestError
    ) {
      console.error(
        requestError
      );

      setError(
        requestError.message ||
          "SDS bilgileri yüklenirken hata oluştu."
      );

    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    if (
      initialChemicalId
    ) {
      prepareChemical(
        initialChemicalId
      );
    }
  }, [
    initialChemicalId,
  ]);


  useEffect(() => {
    if (
      draft &&
      resultRef.current
    ) {
      const timer =
        setTimeout(
          () => {
            resultRef.current
              ?.scrollIntoView({
                behavior:
                  "smooth",
                block:
                  "start",
              });
          },
          150
        );

      return () =>
        clearTimeout(
          timer
        );
    }
  }, [
    draft,
  ]);


  function handleSubmit(
    event
  ) {
    event.preventDefault();

    setError("");


    if (!selectedChemical) {
      setError(
        "Önce değerlendirme yapılacak kimyasalı seçin."
      );

      return;
    }


    if (
      !selectedChemical
        .current_sds
    ) {
      setError(
        "Değerlendirme için güncel SDS gereklidir."
      );

      return;
    }


    if (
      !form
        .process_name
        .trim()
    ) {
      setError(
        "Proses / faaliyet adını girin."
      );

      return;
    }


    if (
      !form.amount_value
    ) {
      setError(
        "Kullanılan miktarı girin."
      );

      return;
    }


    if (
      !form.physical_form
    ) {
      setError(
        "Fiziksel formu seçin."
      );

      return;
    }


    if (
      form.physical_form ===
        "Katı" &&
      !form.dustiness
    ) {
      setError(
        "Katı kimyasal için tozluluk seviyesini seçin."
      );

      return;
    }


    const hazardCodes =
      normalizeList(
        sdsDetail
          ?.hazard_codes
      );


    const precautionaryCodes =
      normalizeList(
        sdsDetail
          ?.precautionary_codes
      );


    const ghsCodes =
      normalizeList(
        sdsDetail
          ?.ghs_codes
      );


    const physicalState =
      sdsDetail
        ?.physical_properties
        ?.physical_state ||
      "";


    const boilingPoint =
      sdsDetail
        ?.physical_properties
        ?.boiling_point ||
      "";


    const analysis =
      calculateCoshhAnalysis({
        hazardCodes,
        amountValue:
          form.amount_value,
        amountUnit:
          form.amount_unit,
        physicalForm:
          form.physical_form,
        dustiness:
          form.dustiness,
        boilingPoint,
        processTemperature:
          form.process_temperature,
        existingControls:
          form.existing_controls,
      });


    const newDraft = {
      created_at:
        new Date()
          .toISOString(),

      chemical_id:
        selectedChemical.id,

      product_name:
        selectedChemical
          .product_name,

      manufacturer:
        selectedChemical
          .manufacturer,

      cas_number:
        getIdentifierValue(
          selectedChemical,
          "CAS"
        ),

      sds_id:
        selectedChemical
          .current_sds
          .id,

      revision_date:
        selectedChemical
          .current_sds
          .revision_date,

      version:
        selectedChemical
          .current_sds
          .version,

      hazard_codes:
        hazardCodes,

      precautionary_codes:
        precautionaryCodes,

      ghs_codes:
        ghsCodes,

      physical_state:
        physicalState,

      boiling_point:
        boilingPoint,

      form: {
        ...form,
      },

      analysis,
    };


    setDraft(
      newDraft
    );
  }


  function exportDraftToExcel() {
    if (!draft) {
      setError(
        "Önce değerlendirme taslağı oluşturun."
      );

      return;
    }


    const analysis =
      draft.analysis;


    const analysisRows = [
      [
        "Tehlikeli Madde",
        "CAS No",
        "Maruziyet Sınır Değeri",
        "Kullanılan Bölüm",
        "Maruz Kalan Çalışan / Görev",
        "H Kodları",
        "GHS",
        "Tehlike Grubu",
        "Günlük Kullanım Miktarı",
        "Miktar Grubu",
        "Fiziksel Form",
        "Tozluluk / Uçuculuk",
        "Kaynama Noktası",
        "Proses Sıcaklığı",
        "Cilt / Göz Grubu",
        "Kontrol Yaklaşımı",
        "Kontrol Rehberi",
        "Mevcut Kontroller",
        "Önerilen Kontrol Faaliyetleri",
        "Değerlendirme Durumu",
      ],

      [
        draft.product_name ||
          "—",

        draft.cas_number ||
          "—",

        draft.form
          .occupational_exposure_limit ||
          "—",

        draft.form
          .department ||
          "—",

        draft.form
          .exposed_workers ||
          "—",

        draft.hazard_codes
          .join(", ") ||
          "—",

        draft.ghs_codes
          .join(", ") ||
          "—",

        analysis
          .hazardGroup ||
          "İnceleme gerekli",

        `${draft.form.amount_value} ${draft.form.amount_unit}`,

        analysis
          .amountLabel ||
          "—",

        draft.form
          .physical_form ||
          "—",

        analysis
          .exposureLabel ||
          "—",

        draft.boiling_point ||
          "—",

        draft.form
          .process_temperature
          ? `${draft.form.process_temperature} °C`
          : "—",

        analysis
          .skinEyeGroup ||
          "—",

        analysis
          .controlApproach
          ? `${analysis.controlApproach} - ${analysis.controlApproachTitle}`
          : "Uzman incelemesi",

        analysis
          .controlGuidanceSheet ||
          "—",

        [
          draft.form
            .closed_system
            ? `Kapalı sistem: ${draft.form.closed_system}`
            : "",

          draft.form
            .local_exhaust
            ? `LEV: ${draft.form.local_exhaust}`
            : "",

          draft.form
            .general_ventilation
            ? `Genel havalandırma: ${draft.form.general_ventilation}`
            : "",

          draft.form
            .existing_ppe
            ? `KKD: ${draft.form.existing_ppe}`
            : "",

          draft.form
            .existing_controls ||
            "",
        ]
          .filter(Boolean)
          .join("\n"),

        analysis
          .recommendations
          .join("\n"),

        analysis.status,
      ],
    ];


    const analysisSheet =
      XLSX.utils.aoa_to_sheet(
        analysisRows
      );


    analysisSheet[
      "!cols"
    ] = [
      { wch: 28 },
      { wch: 18 },
      { wch: 24 },
      { wch: 24 },
      { wch: 28 },
      { wch: 24 },
      { wch: 20 },
      { wch: 18 },
      { wch: 22 },
      { wch: 18 },
      { wch: 18 },
      { wch: 22 },
      { wch: 20 },
      { wch: 20 },
      { wch: 18 },
      { wch: 30 },
      { wch: 20 },
      { wch: 45 },
      { wch: 60 },
      { wch: 30 },
    ];


    const summaryRows = [
      [
        "GEBKİM SDS AI PLATFORM",
        "",
      ],

      [
        "ILO / COSHH KİMYASAL MARUZİYET RİSK DEĞERLENDİRMESİ",
        "",
      ],

      [
        "",
        "",
      ],

      [
        "Kimyasal",
        draft.product_name ||
          "—",
      ],

      [
        "Üretici",
        draft.manufacturer ||
          "—",
      ],

      [
        "CAS No",
        draft.cas_number ||
          "—",
      ],

      [
        "SDS ID",
        draft.sds_id,
      ],

      [
        "SDS Revizyon",
        formatDate(
          draft.revision_date
        ),
      ],

      [
        "",
        "",
      ],

      [
        "Proses / Faaliyet",
        draft.form
          .process_name,
      ],

      [
        "Bölüm",
        draft.form
          .department ||
          "—",
      ],

      [
        "Maruz Kalan Çalışan / Görev",
        draft.form
          .exposed_workers ||
          "—",
      ],

      [
        "Maruziyet Sınır Değeri",
        draft.form
          .occupational_exposure_limit ||
          "—",
      ],

      [
        "Kullanılan Miktar",
        `${draft.form.amount_value} ${draft.form.amount_unit}`,
      ],

      [
        "Fiziksel Form",
        draft.form
          .physical_form,
      ],

      [
        "Tozluluk",
        draft.form
          .dustiness ||
          "—",
      ],

      [
        "Kaynama Noktası",
        draft.boiling_point ||
          "—",
      ],

      [
        "Proses Sıcaklığı",
        draft.form
          .process_temperature
          ? `${draft.form.process_temperature} °C`
          : "—",
      ],

      [
        "",
        "",
      ],

      [
        "Tehlike Grubu",
        draft.analysis
          .hazardGroup ||
          "Belirlenemedi",
      ],

      [
        "Tehlike Grubu ile Eşleşen H Kodları",
        draft.analysis
          .hazardMatchedCodes
          ?.join(", ") ||
          "—",
      ],

      [
        "Miktar Grubu",
        draft.analysis
          .amountLabel ||
          "—",
      ],

      [
        "Tozluluk / Uçuculuk Grubu",
        draft.analysis
          .exposureLabel ||
          "—",
      ],

      [
        "Cilt / Göz Grubu",
        draft.analysis
          .skinEyeGroup ||
          "—",
      ],

      [
        "Kontrol Yaklaşımı",
        draft.analysis
          .controlApproach
          ? `${draft.analysis.controlApproach} - ${draft.analysis.controlApproachTitle}`
          : "Belirlenemedi",
      ],

      [
        "Kontrol Rehberi",
        draft.analysis
          .controlGuidanceSheet ||
          "—",
      ],

      [
        "Skin Rehberleri",
        draft.analysis
          .skinGuidanceSheets
          ?.join(", ") ||
          "—",
      ],

      [
        "Analiz Durumu",
        draft.analysis.status,
      ],

      [
        "",
        "",
      ],

      [
        "H Kodları",
        draft.hazard_codes
          .join(", ") ||
          "—",
      ],

      [
        "P Kodları",
        draft.precautionary_codes
          .join(", ") ||
          "—",
      ],

      [
        "GHS Kodları",
        draft.ghs_codes
          .join(", ") ||
          "—",
      ],

      [
        "",
        "",
      ],

      [
        "Metodoloji",
        draft.analysis.methodology,
      ],

      [
        "Uyarı",
        draft.analysis.disclaimer,
      ],
    ];


    const summarySheet =
      XLSX.utils.aoa_to_sheet(
        summaryRows
      );


    summarySheet[
      "!cols"
    ] = [
      { wch: 38 },
      { wch: 85 },
    ];


    const recommendationRows = [
      [
        "No",
        "Önerilen Kontrol Faaliyeti",
      ],

      ...draft.analysis
        .recommendations
        .map(
          (
            recommendation,
            index
          ) => [
            index + 1,
            recommendation,
          ]
        ),
    ];


    if (
      recommendationRows.length ===
      1
    ) {
      recommendationRows.push([
        1,
        "Öneri oluşturulamadı. Uzman incelemesi gerekli.",
      ]);
    }


    const recommendationSheet =
      XLSX.utils.aoa_to_sheet(
        recommendationRows
      );


    recommendationSheet[
      "!cols"
    ] = [
      { wch: 10 },
      { wch: 100 },
    ];


    const hazardsRows = [
      [
        "Kategori",
        "Kod",
      ],

      ...draft.hazard_codes.map(
        (code) => [
          "H Kodu",
          code,
        ]
      ),

      ...draft.precautionary_codes.map(
        (code) => [
          "P Kodu",
          code,
        ]
      ),

      ...draft.ghs_codes.map(
        (code) => [
          "GHS Kodu",
          code,
        ]
      ),
    ];


    if (
      hazardsRows.length ===
      1
    ) {
      hazardsRows.push([
        "Bilgi",
        "Tehlike kodu bulunamadı.",
      ]);
    }


    const hazardSheet =
      XLSX.utils.aoa_to_sheet(
        hazardsRows
      );


    hazardSheet[
      "!cols"
    ] = [
      { wch: 20 },
      { wch: 30 },
    ];


    const workbook =
      XLSX.utils.book_new();


    XLSX.utils.book_append_sheet(
      workbook,
      analysisSheet,
      "COSHH Analiz Tablosu"
    );


    XLSX.utils.book_append_sheet(
      workbook,
      summarySheet,
      "Değerlendirme Özeti"
    );


    XLSX.utils.book_append_sheet(
      workbook,
      recommendationSheet,
      "Kontrol Faaliyetleri"
    );


    XLSX.utils.book_append_sheet(
      workbook,
      hazardSheet,
      "H-P-GHS Kodları"
    );


    const fileName =
      `ILO_COSHH_${safeFileName(
        draft.product_name
      )}_${safeFileName(
        draft.form.process_name
      )}.xlsx`;


    XLSX.writeFile(
      workbook,
      fileName
    );
  }


  const hazardCodes =
    normalizeList(
      sdsDetail
        ?.hazard_codes
    );


  const ghsCodes =
    normalizeList(
      sdsDetail
        ?.ghs_codes
    );


  const physicalState =
    sdsDetail
      ?.physical_properties
      ?.physical_state ||
    "—";


  const boilingPoint =
    sdsDetail
      ?.physical_properties
      ?.boiling_point ||
    "—";


  return (
    <>

      <header className="topbar">

        <div>

          <p className="eyebrow">
            KİMYASAL RİSK YÖNETİMİ
          </p>

          <h2>
            ILO / COSHH Değerlendirmesi
          </h2>

          <p className="page-description">
            SDS verileri ile proses, kullanım ve maruziyet
            bilgilerini birleştirerek kontrol banding esaslı
            kimyasal risk değerlendirmesi oluşturun.
          </p>

        </div>


        <button
          type="button"
          className="secondary-button"
          onClick={
            onBackInventory
          }
        >
          Kimyasal Envanteri
        </button>

      </header>


      <section className="inventory-card">

        <div className="inventory-header">

          <div>

            <h3>
              Değerlendirilecek Kimyasal
            </h3>

            <p>
              Yalnızca güncel SDS kaydı bulunan
              geçerli kimyasallar listelenir.
            </p>

          </div>

        </div>


        <div
          style={{
            maxWidth:
              "900px",
          }}
        >

          <label
            style={
              fieldStyle
            }
          >

            <strong>
              Kimyasal
            </strong>

            <select
              style={
                controlStyle
              }
              value={
                selectedChemicalId
              }
              onChange={
                (event) =>
                  prepareChemical(
                    event
                      .target
                      .value
                  )
              }
            >

              <option value="">
                Kimyasal seçin...
              </option>


              {
                eligibleChemicals.map(
                  (chemical) => (

                    <option
                      key={
                        chemical.id
                      }
                      value={
                        chemical.id
                      }
                    >

                      {
                        chemical
                          .product_name
                      }

                      {
                        chemical
                          .manufacturer
                          ? ` — ${chemical.manufacturer}`
                          : ""
                      }

                      {
                        chemical
                          .current_sds
                          ?.revision_date
                          ? ` — SDS: ${formatDate(
                              chemical
                                .current_sds
                                .revision_date
                            )}`
                          : ""
                      }

                    </option>

                  )
                )
              }

            </select>

          </label>

        </div>

      </section>


      {
        loading && (

          <section className="inventory-card revision-history-card">

            <div className="empty-state detail-loading">
              SDS verileri hazırlanıyor...
            </div>

          </section>

        )
      }


      {
        error && (

          <section className="inventory-card revision-history-card">

            <div className="empty-state detail-error">
              {error}
            </div>

          </section>

        )
      }


      {
        selectedChemical && (
          <>

            <section className="detail-grid">

              <div className="detail-card">

                <div className="detail-card-title">
                  Kimyasal / SDS Kaynağı
                </div>


                <div className="detail-info-list">

                  <div className="detail-info-row">
                    <span>
                      Ürün Adı
                    </span>

                    <strong>
                      {
                        selectedChemical
                          .product_name
                      }
                    </strong>
                  </div>


                  <div className="detail-info-row">
                    <span>
                      Üretici
                    </span>

                    <strong>
                      {
                        selectedChemical
                          .manufacturer ||
                        "—"
                      }
                    </strong>
                  </div>


                  <div className="detail-info-row">
                    <span>
                      CAS No
                    </span>

                    <strong>
                      {
                        getIdentifierValue(
                          selectedChemical,
                          "CAS"
                        )
                      }
                    </strong>
                  </div>


                  <div className="detail-info-row">
                    <span>
                      Güncel SDS
                    </span>

                    <strong>
                      #
                      {
                        selectedChemical
                          .current_sds
                          ?.id
                      }
                    </strong>
                  </div>


                  <div className="detail-info-row">
                    <span>
                      Revizyon
                    </span>

                    <strong>
                      {
                        formatDate(
                          selectedChemical
                            .current_sds
                            ?.revision_date
                        )
                      }
                    </strong>
                  </div>


                  <div className="detail-info-row">
                    <span>
                      Versiyon
                    </span>

                    <strong>
                      {
                        selectedChemical
                          .current_sds
                          ?.version ||
                        "—"
                      }
                    </strong>
                  </div>

                </div>

              </div>


              <div className="detail-card hazard-summary-card">

                <div className="detail-card-title">
                  SDS'den Otomatik Alınan Veriler
                </div>


                <div className="detail-info-list">

                  <div className="detail-info-row">
                    <span>
                      Fiziksel Hal
                    </span>

                    <strong>
                      {
                        physicalState
                      }
                    </strong>
                  </div>


                  <div className="detail-info-row">
                    <span>
                      Kaynama Noktası
                    </span>

                    <strong>
                      {
                        boilingPoint
                      }
                    </strong>
                  </div>

                </div>


                <div className="sds-code-group">

                  <span className="sds-code-label">
                    H Kodları
                  </span>

                  <div className="sds-code-list">

                    {
                      hazardCodes.length > 0
                        ? hazardCodes.map(
                            (code) => (

                              <span
                                className="sds-code hazard-code"
                                key={
                                  code
                                }
                              >
                                {
                                  code
                                }
                              </span>

                            )
                          )
                        : (

                          <span className="sds-empty-text">
                            H kodu bulunamadı.
                          </span>

                        )
                    }

                  </div>

                </div>


                <div className="sds-code-group">

                  <span className="sds-code-label">
                    GHS Kodları
                  </span>

                  <div className="sds-code-list">

                    {
                      ghsCodes.length > 0
                        ? ghsCodes.map(
                            (code) => (

                              <span
                                className="sds-code ghs-code"
                                key={
                                  code
                                }
                              >
                                {
                                  code
                                }
                              </span>

                            )
                          )
                        : (

                          <span className="sds-empty-text">
                            GHS kodu bulunamadı.
                          </span>

                        )
                    }

                  </div>

                </div>

              </div>

            </section>


            <form
              className="inventory-card revision-history-card"
              onSubmit={
                handleSubmit
              }
            >

              <div className="inventory-header">

                <div>

                  <h3>
                    Proses ve Maruziyet Bilgileri
                  </h3>

                  <p>
                    SDS'de bulunmayan işyeri kullanım ve
                    maruziyet bilgilerini girin.
                  </p>

                </div>

              </div>


              <div
                style={
                  gridStyle
                }
              >

                <label style={fieldStyle}>
                  <strong>
                    Proses / Faaliyet Adı *
                  </strong>

                  <input
                    style={controlStyle}
                    type="text"
                    value={
                      form.process_name
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "process_name",
                          event.target.value
                        )
                    }
                    placeholder="Örn. ham madde besleme"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Kullanılan Bölüm
                  </strong>

                  <input
                    style={controlStyle}
                    type="text"
                    value={
                      form.department
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "department",
                          event.target.value
                        )
                    }
                    placeholder="Örn. Tartım / Karışım"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Maruz Kalan Çalışan / Görev
                  </strong>

                  <input
                    style={controlStyle}
                    type="text"
                    value={
                      form.exposed_workers
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "exposed_workers",
                          event.target.value
                        )
                    }
                    placeholder="Örn. Boya Vernik Operatörü"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Maruziyet Sınır Değeri
                  </strong>

                  <input
                    style={controlStyle}
                    type="text"
                    value={
                      form.occupational_exposure_limit
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "occupational_exposure_limit",
                          event.target.value
                        )
                    }
                    placeholder="Örn. TWA 8 saat: 100 ppm"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Kullanılan Miktar *
                  </strong>

                  <input
                    style={controlStyle}
                    type="number"
                    min="0"
                    step="any"
                    value={
                      form.amount_value
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "amount_value",
                          event.target.value
                        )
                    }
                    placeholder="Örn. 25"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Miktar Birimi
                  </strong>

                  <select
                    style={controlStyle}
                    value={
                      form.amount_unit
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "amount_unit",
                          event.target.value
                        )
                    }
                  >

                    <option value="kg">
                      kg
                    </option>

                    <option value="ton">
                      ton
                    </option>

                    <option value="g">
                      g
                    </option>

                    <option value="L">
                      L
                    </option>

                    <option value="mL">
                      mL
                    </option>

                  </select>
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Fiziksel Form *
                  </strong>

                  <select
                    style={controlStyle}
                    value={
                      form.physical_form
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "physical_form",
                          event.target.value
                        )
                    }
                  >

                    <option value="">
                      Seçin...
                    </option>

                    <option value="Sıvı">
                      Sıvı
                    </option>

                    <option value="Katı">
                      Katı
                    </option>

                    <option value="Gaz">
                      Gaz / Buhar
                    </option>

                    <option value="Diğer">
                      Diğer
                    </option>

                  </select>
                </label>


                {
                  form.physical_form ===
                    "Katı" && (

                    <label style={fieldStyle}>
                      <strong>
                        Tozluluk *
                      </strong>

                      <select
                        style={controlStyle}
                        value={
                          form.dustiness
                        }
                        onChange={
                          (event) =>
                            updateField(
                              "dustiness",
                              event.target.value
                            )
                        }
                      >

                        <option value="">
                          Seçin...
                        </option>

                        <option value="Düşük">
                          Düşük
                        </option>

                        <option value="Orta">
                          Orta
                        </option>

                        <option value="Yüksek">
                          Yüksek
                        </option>

                      </select>
                    </label>

                  )
                }


                <label style={fieldStyle}>
                  <strong>
                    Proses Sıcaklığı (°C)
                  </strong>

                  <input
                    style={controlStyle}
                    type="number"
                    step="any"
                    value={
                      form
                        .process_temperature
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "process_temperature",
                          event.target.value
                        )
                    }
                    placeholder="Örn. 25"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Maruziyet Süresi
                  </strong>

                  <input
                    style={controlStyle}
                    type="text"
                    value={
                      form
                        .exposure_duration
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "exposure_duration",
                          event.target.value
                        )
                    }
                    placeholder="Örn. 30 dakika / işlem"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Kullanım / Maruziyet Sıklığı
                  </strong>

                  <input
                    style={controlStyle}
                    type="text"
                    value={
                      form
                        .exposure_frequency
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "exposure_frequency",
                          event.target.value
                        )
                    }
                    placeholder="Örn. günde 2 kez"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Kapalı Sistem
                  </strong>

                  <select
                    style={controlStyle}
                    value={
                      form.closed_system
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "closed_system",
                          event.target.value
                        )
                    }
                  >

                    <option value="">
                      Seçin...
                    </option>

                    <option value="Evet">
                      Evet
                    </option>

                    <option value="Hayır">
                      Hayır
                    </option>

                    <option value="Kısmen">
                      Kısmen
                    </option>

                  </select>
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Lokal Emiş / LEV
                  </strong>

                  <select
                    style={controlStyle}
                    value={
                      form.local_exhaust
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "local_exhaust",
                          event.target.value
                        )
                    }
                  >

                    <option value="">
                      Seçin...
                    </option>

                    <option value="Var">
                      Var
                    </option>

                    <option value="Yok">
                      Yok
                    </option>

                    <option value="Bilinmiyor">
                      Bilinmiyor
                    </option>

                  </select>
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Genel Havalandırma
                  </strong>

                  <select
                    style={controlStyle}
                    value={
                      form
                        .general_ventilation
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "general_ventilation",
                          event.target.value
                        )
                    }
                  >

                    <option value="">
                      Seçin...
                    </option>

                    <option value="Yeterli">
                      Yeterli
                    </option>

                    <option value="Yetersiz">
                      Yetersiz
                    </option>

                    <option value="Bilinmiyor">
                      Bilinmiyor
                    </option>

                  </select>
                </label>

              </div>


              <div
                style={{
                  ...gridStyle,
                  marginTop:
                    "18px",
                }}
              >

                <label style={fieldStyle}>
                  <strong>
                    Proses Açıklaması
                  </strong>

                  <textarea
                    style={textareaStyle}
                    value={
                      form
                        .process_description
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "process_description",
                          event.target.value
                        )
                    }
                    placeholder="Kimyasalın proseste nasıl kullanıldığını açıklayın."
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Mevcut KKD
                  </strong>

                  <textarea
                    style={textareaStyle}
                    value={
                      form.existing_ppe
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "existing_ppe",
                          event.target.value
                        )
                    }
                    placeholder="Örn. nitril eldiven, gözlük, yüz siperi"
                  />
                </label>


                <label style={fieldStyle}>
                  <strong>
                    Mevcut Kontrol Tedbirleri
                  </strong>

                  <textarea
                    style={textareaStyle}
                    value={
                      form
                        .existing_controls
                    }
                    onChange={
                      (event) =>
                        updateField(
                          "existing_controls",
                          event.target.value
                        )
                    }
                    placeholder="Mevcut mühendislik ve organizasyonel kontrolleri yazın."
                  />
                </label>

              </div>


              <div
                className="upload-message"
                style={{
                  marginTop:
                    "20px",
                }}
              >

                <strong>
                  Değerlendirme kapsamı
                </strong>

                <span>
                  Sistem ILO / COSHH control banding yaklaşımına
                  göre bir ön değerlendirme oluşturur. Nihai
                  işyeri risk değerlendirmesi uzman incelemesi,
                  proses doğrulaması ve gerektiğinde maruziyet
                  ölçümleriyle tamamlanmalıdır.
                </span>

              </div>


              <div
                className="upload-actions"
                style={{
                  marginTop:
                    "22px",
                }}
              >

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    prepareChemical(
                      selectedChemical.id
                    )
                  }
                >
                  Formu Temizle
                </button>


                <button
                  type="submit"
                  className="primary-button"
                >
                  ILO / COSHH Analizini Oluştur
                </button>

              </div>

            </form>


            {
              draft && (

                <section
                  ref={resultRef}
                  className="sds-section-card"
                  style={{
                    scrollMarginTop:
                      "24px",
                  }}
                >

                  <div className="sds-section-heading">

                    <div>

                      <p className="eyebrow">
                        ILO / COSHH ANALİZ SONUCU
                      </p>

                      <h3>
                        Kimyasal Maruziyet Risk Değerlendirmesi
                      </h3>

                    </div>


                    <span className="status-badge review status-large">

                      <span className="status-dot" />

                      {
                        draft
                          .analysis
                          .status
                      }

                    </span>

                  </div>


                  <div
                    style={{
                      display:
                        "grid",
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(190px, 1fr))",
                      gap:
                        "14px",
                      marginBottom:
                        "24px",
                    }}
                  >

                    <div style={analysisCardStyle}>
                      <div style={analysisTitleStyle}>
                        Tehlike Grubu
                      </div>

                      <div style={analysisValueStyle}>
                        {
                          draft
                            .analysis
                            .hazardGroup ||
                          "—"
                        }
                      </div>
                    </div>


                    <div style={analysisCardStyle}>
                      <div style={analysisTitleStyle}>
                        Miktar Grubu
                      </div>

                      <div style={analysisValueStyle}>
                        {
                          draft
                            .analysis
                            .amountLabel ||
                          "—"
                        }
                      </div>
                    </div>


                    <div style={analysisCardStyle}>
                      <div style={analysisTitleStyle}>
                        Tozluluk / Uçuculuk
                      </div>

                      <div style={analysisValueStyle}>
                        {
                          draft
                            .analysis
                            .exposureLabel ||
                          "—"
                        }
                      </div>
                    </div>


                    <div style={analysisCardStyle}>
                      <div style={analysisTitleStyle}>
                        Cilt / Göz Grubu
                      </div>

                      <div style={analysisValueStyle}>
                        {
                          draft
                            .analysis
                            .skinEyeGroup ||
                          "—"
                        }
                      </div>
                    </div>


                    <div style={analysisCardStyle}>
                      <div style={analysisTitleStyle}>
                        Kontrol Yaklaşımı
                      </div>

                      <div style={analysisValueStyle}>
                        {
                          draft
                            .analysis
                            .controlApproach ||
                          "—"
                        }
                      </div>

                      <div
                        style={{
                          marginTop:
                            "6px",
                          fontSize:
                            "13px",
                          color:
                            "#687381",
                        }}
                      >
                        {
                          draft
                            .analysis
                            .controlApproachTitle ||
                          ""
                        }
                      </div>
                    </div>


                    <div style={analysisCardStyle}>
                      <div style={analysisTitleStyle}>
                        Kontrol Rehberi
                      </div>

                      <div style={analysisValueStyle}>
                        {
                          draft
                            .analysis
                            .controlGuidanceSheet ||
                          "—"
                        }
                      </div>
                    </div>

                  </div>


                  <div
                    style={{
                      overflowX:
                        "auto",
                      marginBottom:
                        "24px",
                    }}
                  >

                    <table style={tableStyle}>

                      <thead>

                        <tr>

                          <th style={tableHeaderStyle}>
                            Tehlikeli Madde
                          </th>

                          <th style={tableHeaderStyle}>
                            CAS No
                          </th>

                          <th style={tableHeaderStyle}>
                            Maruziyet Sınır Değeri
                          </th>

                          <th style={tableHeaderStyle}>
                            Kullanılan Bölüm
                          </th>

                          <th style={tableHeaderStyle}>
                            Maruz Kalan Çalışan
                          </th>

                          <th style={tableHeaderStyle}>
                            H Kodları
                          </th>

                          <th style={tableHeaderStyle}>
                            GHS
                          </th>

                          <th style={tableHeaderStyle}>
                            Tehlike Grubu
                          </th>

                          <th style={tableHeaderStyle}>
                            Günlük Kullanım
                          </th>

                          <th style={tableHeaderStyle}>
                            Miktar Grubu
                          </th>

                          <th style={tableHeaderStyle}>
                            Fiziksel Form
                          </th>

                          <th style={tableHeaderStyle}>
                            Tozluluk / Uçuculuk
                          </th>

                          <th style={tableHeaderStyle}>
                            Kontrol Yaklaşımı
                          </th>

                          <th style={tableHeaderStyle}>
                            Kontrol Rehberi
                          </th>

                        </tr>

                      </thead>


                      <tbody>

                        <tr>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .product_name
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .cas_number
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .form
                                .occupational_exposure_limit ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .form
                                .department ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .form
                                .exposed_workers ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .hazard_codes
                                .join(", ") ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .ghs_codes
                                .join(", ") ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .analysis
                                .hazardGroup ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .form
                                .amount_value
                            }{" "}
                            {
                              draft
                                .form
                                .amount_unit
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .analysis
                                .amountLabel ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .form
                                .physical_form
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .analysis
                                .exposureLabel ||
                              "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .analysis
                                .controlApproach
                                ? `${draft.analysis.controlApproach} - ${draft.analysis.controlApproachTitle}`
                                : "—"
                            }
                          </td>

                          <td style={tableCellStyle}>
                            {
                              draft
                                .analysis
                                .controlGuidanceSheet ||
                              "—"
                            }
                          </td>

                        </tr>

                      </tbody>

                    </table>

                  </div>


                  <section className="detail-grid">

                    <div className="detail-card">

                      <div className="detail-card-title">
                        Analiz Detayları
                      </div>


                      <div className="detail-info-list">

                        <div className="detail-info-row">
                          <span>
                            Eşleşen Tehlike Kodları
                          </span>

                          <strong>
                            {
                              draft
                                .analysis
                                .hazardMatchedCodes
                                ?.join(", ") ||
                              "—"
                            }
                          </strong>
                        </div>


                        <div className="detail-info-row">
                          <span>
                            Grup S Kodları
                          </span>

                          <strong>
                            {
                              draft
                                .analysis
                                .skinEyeCodes
                                ?.join(", ") ||
                              "—"
                            }
                          </strong>
                        </div>


                        <div className="detail-info-row">
                          <span>
                            Kaynama Noktası
                          </span>

                          <strong>
                            {
                              draft
                                .boiling_point ||
                              "—"
                            }
                          </strong>
                        </div>


                        <div className="detail-info-row">
                          <span>
                            Proses Sıcaklığı
                          </span>

                          <strong>
                            {
                              draft
                                .form
                                .process_temperature
                                ? `${draft.form.process_temperature} °C`
                                : "—"
                            }
                          </strong>
                        </div>


                        <div className="detail-info-row">
                          <span>
                            Maruziyet Sınıflandırması
                          </span>

                          <strong>
                            {
                              draft
                                .analysis
                                .exposureNote ||
                              "—"
                            }
                          </strong>
                        </div>

                      </div>

                    </div>


                    <div className="detail-card">

                      <div className="detail-card-title">
                        Mevcut Kontroller
                      </div>


                      <div className="detail-info-list">

                        <div className="detail-info-row">
                          <span>
                            Kapalı Sistem
                          </span>

                          <strong>
                            {
                              draft
                                .form
                                .closed_system ||
                              "—"
                            }
                          </strong>
                        </div>


                        <div className="detail-info-row">
                          <span>
                            Lokal Emiş / LEV
                          </span>

                          <strong>
                            {
                              draft
                                .form
                                .local_exhaust ||
                              "—"
                            }
                          </strong>
                        </div>


                        <div className="detail-info-row">
                          <span>
                            Genel Havalandırma
                          </span>

                          <strong>
                            {
                              draft
                                .form
                                .general_ventilation ||
                              "—"
                            }
                          </strong>
                        </div>


                        <div className="detail-info-row">
                          <span>
                            Mevcut KKD
                          </span>

                          <strong>
                            {
                              draft
                                .form
                                .existing_ppe ||
                              "—"
                            }
                          </strong>
                        </div>

                      </div>

                    </div>

                  </section>


                  <div
                    className="detail-card"
                    style={{
                      marginTop:
                        "20px",
                    }}
                  >

                    <div className="detail-card-title">
                      Önerilen Kontrol Faaliyetleri
                    </div>


                    {
                      draft
                        .analysis
                        .recommendations
                        .length >
                        0
                        ? (

                          <ol
                            style={{
                              margin:
                                "12px 0 0",
                              paddingLeft:
                                "22px",
                              lineHeight:
                                "1.7",
                            }}
                          >

                            {
                              draft
                                .analysis
                                .recommendations
                                .map(
                                  (
                                    recommendation,
                                    index
                                  ) => (

                                    <li
                                      key={
                                        `${recommendation}-${index}`
                                      }
                                    >
                                      {
                                        recommendation
                                      }
                                    </li>

                                  )
                                )
                            }

                          </ol>

                        )
                        : (

                          <p className="page-description">
                            Kontrol önerisi oluşturulamadı.
                          </p>

                        )
                    }

                  </div>


                  {
                    draft
                      .analysis
                      .warnings
                      .length >
                      0 && (

                      <div
                        className="upload-message"
                        style={{
                          marginTop:
                            "20px",
                        }}
                      >

                        <strong>
                          Uzman incelemesi gereken noktalar
                        </strong>

                        <span>
                          {
                            draft
                              .analysis
                              .warnings
                              .join(
                                " • "
                              )
                          }
                        </span>

                      </div>

                    )
                  }


                  <div
                    className="upload-message"
                    style={{
                      marginTop:
                        "20px",
                    }}
                  >

                    <strong>
                      Metodoloji notu
                    </strong>

                    <span>
                      {
                        draft
                          .analysis
                          .disclaimer
                      }
                    </span>

                  </div>


                  <div
                    className="upload-actions"
                    style={{
                      marginTop:
                        "22px",
                    }}
                  >

                    <button
                      type="button"
                      className="primary-button"
                      onClick={
                        exportDraftToExcel
                      }
                    >
                      Excel'e Aktar
                    </button>

                  </div>

                </section>

              )
            }

          </>
        )
      }

    </>
  );
}


export default CoshhAssessment;