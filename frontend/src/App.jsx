import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import "./App.css";
import ReviewQueue from "./ReviewQueue";
import CoshhAssessment from "./CoshhAssessment";

const API_BASE_URL =
  "http://127.0.0.1:8000";


function formatDate(value) {
  if (!value) return "—";

  const date =
    new Date(
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


function formatDateTime(value) {
  if (!value) return "—";

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "tr-TR",
    {
      dateStyle:
        "medium",
      timeStyle:
        "short",
    }
  ).format(date);
}


function formatFileSize(bytes) {
  if (!bytes) {
    return "0 KB";
  }

  const mb =
    bytes /
    (1024 * 1024);

  if (mb >= 1) {
    return `${mb.toFixed(
      2
    )} MB`;
  }

  return `${(
    bytes / 1024
  ).toFixed(1)} KB`;
}


function formatProcessingStatus(
  status
) {
  const normalized =
    String(
      status || ""
    )
      .trim()
      .toLowerCase();

  const labels = {
    pending:
      "Bekliyor",

    processing:
      "İşleniyor",

    uploaded:
      "Yüklendi",

    classified:
      "Sınıflandırıldı",

    sections_extracted:
      "Bölümler Çıkarıldı",

    needs_review:
      "İnceleme Gerekli",

    failed:
      "Hata",

    completed:
      "Tamamlandı",
  };

  if (!normalized) {
    return "—";
  }

  return (
    labels[
      normalized
    ] ||
    status
  );
}


function getApiErrorMessage(
  data
) {
  if (!data) {
    return "İşlem sırasında bilinmeyen bir hata oluştu.";
  }

  if (
    typeof data.detail ===
    "string"
  ) {
    return data.detail;
  }

  if (
    data.detail &&
    typeof data.detail ===
      "object" &&
    typeof data.detail
      .message ===
      "string"
  ) {
    return (
      data.detail
        .message
    );
  }

  if (
    Array.isArray(
      data.detail
    )
  ) {
    return data.detail
      .map(
        (item) =>
          item.msg ||
          JSON.stringify(
            item
          )
      )
      .join(", ");
  }

  if (
    typeof data.message ===
    "string"
  ) {
    return data.message;
  }

  return "İşlem sırasında bir hata oluştu.";
}


function getIdentifier(
  identifiers,
  type
) {
  const found =
    identifiers?.find(
      (item) =>
        item
          .identifier_type
          ?.toUpperCase() ===
        type
    );

  return (
    found
      ?.identifier_value ||
    "—"
  );
}


function getStatus(
  chemical
) {
  if (
    chemical
      .sds_summary
      ?.needs_review_count >
    0
  ) {
    return {
      text:
        "İnceleme Gerekli",
      className:
        "review",
    };
  }

  if (
    !chemical
      .current_sds
  ) {
    return {
      text:
        "SDS Yok",
      className:
        "empty",
    };
  }

  const status =
    chemical
      .current_sds
      .processing_status;

  if (
    status ===
    "pending"
  ) {
    return {
      text:
        "Bekliyor",
      className:
        "pending",
    };
  }

  if (
    status ===
    "failed"
  ) {
    return {
      text:
        "Hata",
      className:
        "error",
    };
  }

  return {
    text:
      "Hazır",
    className:
      "ready",
  };
}


function normalizeList(
  value
) {
  if (
    Array.isArray(
      value
    )
  ) {
    return value.filter(
      (item) =>
        item !== null &&
        item !==
          undefined &&
        item !== ""
    );
  }

  if (
    value === null ||
    value ===
      undefined ||
    value === ""
  ) {
    return [];
  }

  return [value];
}


function TextList({
  value,
  emptyText =
    "Bilgi bulunmuyor.",
}) {
  const items =
    normalizeList(
      value
    );

  if (
    items.length ===
    0
  ) {
    return (
      <div className="sds-empty-text">
        {emptyText}
      </div>
    );
  }

  return (
    <ul className="sds-text-list">

      {
        items.map(
          (
            item,
            index
          ) => (

            <li
              key={`${String(
                item
              ).slice(
                0,
                40
              )}-${index}`}
            >
              {
                String(
                  item
                )
              }
            </li>

          )
        )
      }

    </ul>
  );
}


function DetailRow({
  label,
  value,
}) {
  return (
    <div className="detail-info-row">

      <span>
        {label}
      </span>

      <strong>
        {
          value ??
          "—"
        }
      </strong>

    </div>
  );
}


const PHYSICAL_PROPERTY_LABELS =
  [
    [
      "physical_state",
      "Fiziksel Hal",
    ],

    [
      "color",
      "Renk",
    ],

    [
      "odor",
      "Koku",
    ],

    [
      "ph",
      "pH",
    ],

    [
      "melting_freezing_point",
      "Erime / Donma Noktası",
    ],

    [
      "boiling_point",
      "Kaynama Noktası",
    ],

    [
      "flash_point",
      "Parlama Noktası",
    ],

    [
      "vapour_pressure",
      "Buhar Basıncı",
    ],

    [
      "density",
      "Yoğunluk",
    ],

    [
      "viscosity",
      "Viskozite",
    ],

    [
      "solubility",
      "Çözünürlük",
    ],

    [
      "flammability",
      "Alevlenebilirlik",
    ],

    [
      "explosive_properties",
      "Patlayıcı Özellikler",
    ],

    [
      "oxidising_properties",
      "Oksitleyici Özellikler",
    ],

    [
      "lower_explosion_limit",
      "Alt Patlama Sınırı",
    ],

    [
      "upper_explosion_limit",
      "Üst Patlama Sınırı",
    ],
  ];


function App() {
  const [
    currentView,
    setCurrentView,
  ] = useState(
    "dashboard"
  );

  const [
    chemicals,
    setChemicals,
  ] = useState([]);

  const [
    searchTerm,
    setSearchTerm,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const [
    selectedChemicalId,
    setSelectedChemicalId,
  ] = useState(null);

  const [
    selectedChemical,
    setSelectedChemical,
  ] = useState(null);

  const [
    sdsHistory,
    setSdsHistory,
  ] = useState(null);

  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);

  const [
    detailError,
    setDetailError,
  ] = useState("");

  const [
    selectedSdsId,
    setSelectedSdsId,
  ] = useState(null);

  const [
    selectedSdsDetail,
    setSelectedSdsDetail,
  ] = useState(null);

  const [
    sdsDetailLoading,
    setSdsDetailLoading,
  ] = useState(false);

  const [
    sdsDetailError,
    setSdsDetailError,
  ] = useState("");

  const [
    selectedFile,
    setSelectedFile,
  ] = useState(null);

  const [
    uploadLoading,
    setUploadLoading,
  ] = useState(false);

  const [
    uploadError,
    setUploadError,
  ] = useState("");

  const [
    uploadResult,
    setUploadResult,
  ] = useState(null);

  const [
    coshhInitialChemicalId,
    setCoshhInitialChemicalId,
  ] = useState("");

  const fileInputRef =
    useRef(null);


  const loadChemicals =
    useCallback(
      async () => {
        try {
          setLoading(
            true
          );

          setError(
            ""
          );

          const response =
            await fetch(
              `${API_BASE_URL}/chemicals/`
            );

          if (
            !response.ok
          ) {
            throw new Error(
              "Kimyasal listesi alınamadı."
            );
          }

          const list =
            await response.json();

          const detailed =
            await Promise.all(
              list.map(
                async (
                  chemical
                ) => {
                  try {
                    const detailResponse =
                      await fetch(
                        `${API_BASE_URL}/chemicals/${chemical.id}`
                      );

                    if (
                      !detailResponse.ok
                    ) {
                      return chemical;
                    }

                    return await detailResponse.json();

                  } catch {
                    return chemical;
                  }
                }
              )
            );

          setChemicals(
            detailed
          );

        } catch (
          requestError
        ) {
          console.error(
            requestError
          );

          setError(
            "Backend bağlantısı kurulamadı. FastAPI sunucusunun çalıştığını kontrol edin."
          );

        } finally {
          setLoading(
            false
          );
        }
      },
      []
    );


  useEffect(() => {
    loadChemicals();
  }, [
    loadChemicals,
  ]);


  useEffect(() => {
    if (
      !selectedChemicalId
    ) {
      return;
    }

    async function loadDetail() {
      try {
        setDetailLoading(
          true
        );

        setDetailError(
          ""
        );


        const [
          detailResponse,
          historyResponse,
        ] =
          await Promise.all(
            [
              fetch(
                `${API_BASE_URL}/chemicals/${selectedChemicalId}`
              ),

              fetch(
                `${API_BASE_URL}/chemicals/${selectedChemicalId}/sds`
              ),
            ]
          );


        if (
          !detailResponse.ok
        ) {
          throw new Error(
            "Kimyasal detay bilgisi alınamadı."
          );
        }


        if (
          !historyResponse.ok
        ) {
          throw new Error(
            "SDS revizyon geçmişi alınamadı."
          );
        }


        const detailData =
          await detailResponse.json();

        const historyData =
          await historyResponse.json();


        setSelectedChemical(
          detailData
        );

        setSdsHistory(
          historyData
        );

      } catch (
        requestError
      ) {
        console.error(
          requestError
        );

        setDetailError(
          "Kimyasal detayları yüklenirken bir hata oluştu."
        );

      } finally {
        setDetailLoading(
          false
        );
      }
    }


    loadDetail();

  }, [
    selectedChemicalId,
  ]);


  useEffect(() => {
    if (
      !selectedSdsId
    ) {
      return;
    }


    async function loadSdsDetail() {
      try {
        setSdsDetailLoading(
          true
        );

        setSdsDetailError(
          ""
        );

        setSelectedSdsDetail(
          null
        );


        const response =
          await fetch(
            `${API_BASE_URL}/sds/${selectedSdsId}/sections`
          );


        let responseData =
          null;


        try {
          responseData =
            await response.json();

        } catch {
          responseData =
            null;
        }


        if (
          !response.ok
        ) {
          throw new Error(
            getApiErrorMessage(
              responseData
            )
          );
        }


        setSelectedSdsDetail(
          responseData
        );

      } catch (
        requestError
      ) {
        console.error(
          requestError
        );

        setSdsDetailError(
          requestError.message ||
            "SDS detayları yüklenirken bir hata oluştu."
        );

      } finally {
        setSdsDetailLoading(
          false
        );
      }
    }


    loadSdsDetail();

  }, [
    selectedSdsId,
  ]);


  const filteredChemicals =
    useMemo(
      () => {
        const search =
          searchTerm
            .trim()
            .toLocaleLowerCase(
              "tr-TR"
            );

        if (!search) {
          return chemicals;
        }

        return chemicals.filter(
          (
            chemical
          ) => {
            const cas =
              getIdentifier(
                chemical.identifiers,
                "CAS"
              );

            const ec =
              getIdentifier(
                chemical.identifiers,
                "EC"
              );

            return [
              chemical.product_name,
              chemical.manufacturer,
              chemical.internal_code,
              cas,
              ec,
            ].some(
              (
                value
              ) =>
                value
                  ?.toLocaleLowerCase(
                    "tr-TR"
                  )
                  .includes(
                    search
                  )
            );
          }
        );
      },
      [
        chemicals,
        searchTerm,
      ]
    );


  const totalSdsDocuments =
    chemicals.reduce(
      (
        total,
        chemical
      ) =>
        total +
        (
          chemical
            .sds_summary
            ?.total_documents ||
          0
        ),
      0
    );


  const totalCurrentSds =
    chemicals.filter(
      (
        chemical
      ) =>
        chemical
          .current_sds
    ).length;


  const totalNeedsReview =
    chemicals.reduce(
      (
        total,
        chemical
      ) =>
        total +
        (
          chemical
            .sds_summary
            ?.needs_review_count ||
          0
        ),
      0
    );


  const totalWithoutCurrentSds =
    chemicals.filter(
      (
        chemical
      ) =>
        !chemical
          .current_sds
    ).length;


  const manufacturerReport =
    useMemo(
      () => {
        const counts =
          new Map();

        chemicals.forEach(
          (
            chemical
          ) => {
            const manufacturer =
              chemical
                .manufacturer
                ?.trim() ||
              "Üretici bilgisi yok";

            counts.set(
              manufacturer,
              (
                counts.get(
                  manufacturer
                ) ||
                0
              ) + 1
            );
          }
        );

        return Array.from(
          counts.entries()
        )
          .map(
            (
              [
                manufacturer,
                count,
              ]
            ) => ({
              manufacturer,
              count,
            })
          )
          .sort(
            (
              a,
              b
            ) =>
              b.count -
                a.count ||
              a.manufacturer.localeCompare(
                b.manufacturer,
                "tr-TR"
              )
          );
      },
      [
        chemicals,
      ]
    );


  const processingStatusReport =
    useMemo(
      () => {
        const counts =
          new Map();

        chemicals.forEach(
          (
            chemical
          ) => {
            const status =
              chemical
                .current_sds
                ?.processing_status ||
              "no_sds";

            counts.set(
              status,
              (
                counts.get(
                  status
                ) ||
                0
              ) + 1
            );
          }
        );

        return Array.from(
          counts.entries()
        )
          .map(
            (
              [
                status,
                count,
              ]
            ) => ({
              status,
              count,
            })
          )
          .sort(
            (
              a,
              b
            ) =>
              b.count -
              a.count
          );
      },
      [
        chemicals,
      ]
    );


  const recentCurrentSds =
    useMemo(
      () => {
        return chemicals
          .filter(
            (
              chemical
            ) =>
              chemical
                .current_sds
          )
          .map(
            (
              chemical
            ) => ({
              chemicalId:
                chemical.id,

              productName:
                chemical
                  .product_name ||
                "İsimsiz kimyasal",

              manufacturer:
                chemical
                  .manufacturer ||
                "—",

              sds:
                chemical
                  .current_sds,
            })
          )
          .sort(
            (
              a,
              b
            ) => {
              const dateA =
                new Date(
                  a.sds
                    .uploaded_at ||
                    0
                ).getTime();

              const dateB =
                new Date(
                  b.sds
                    .uploaded_at ||
                    0
                ).getTime();

              return (
                dateB -
                dateA
              );
            }
          )
          .slice(
            0,
            10
          );
      },
      [
        chemicals,
      ]
    );


  const attentionChemicals =
    useMemo(
      () =>
        chemicals.filter(
          (
            chemical
          ) =>
            !chemical
              .current_sds ||
            chemical
              .sds_summary
              ?.needs_review_count >
              0
        ),
      [
        chemicals,
      ]
    );


  function clearSdsDetailState() {
    setSelectedSdsId(
      null
    );

    setSelectedSdsDetail(
      null
    );

    setSdsDetailError(
      ""
    );
  }


  function resetDetail() {
    setSelectedChemicalId(
      null
    );

    setSelectedChemical(
      null
    );

    setSdsHistory(
      null
    );

    setDetailError(
      ""
    );

    clearSdsDetailState();
  }


  function scrollTop() {
    window.scrollTo({
      top: 0,
      behavior:
        "smooth",
    });
  }


  function showDashboard() {
    setCurrentView(
      "dashboard"
    );

    resetDetail();

    scrollTop();
  }


  function showInventory() {
    setCurrentView(
      "inventory"
    );

    resetDetail();

    scrollTop();
  }


  function showUpload() {
    setCurrentView(
      "upload"
    );

    resetDetail();

    scrollTop();
  }


  function showReview() {
    setCurrentView(
      "review"
    );

    resetDetail();

    scrollTop();
  }


  function showReports() {
    setCurrentView(
      "reports"
    );

    resetDetail();

    scrollTop();
  }


  function showCoshh() {
    setCoshhInitialChemicalId(
      ""
    );

    setCurrentView(
      "coshh"
    );

    resetDetail();

    scrollTop();
  }


  function openCoshhAssessment(
    chemicalId
  ) {
    setCoshhInitialChemicalId(
      chemicalId
    );

    setCurrentView(
      "coshh"
    );

    resetDetail();

    scrollTop();
  }


  function openChemicalDetail(
    chemicalId
  ) {
    setSelectedChemical(
      null
    );

    setSdsHistory(
      null
    );

    setDetailError(
      ""
    );

    clearSdsDetailState();

    setSelectedChemicalId(
      chemicalId
    );

    setCurrentView(
      "detail"
    );

    scrollTop();
  }


  function openSdsDetail(
    sdsId,
    chemicalId =
      selectedChemicalId
  ) {
    if (
      chemicalId &&
      chemicalId !==
        selectedChemicalId
    ) {
      setSelectedChemicalId(
        chemicalId
      );
    }

    setSelectedSdsId(
      sdsId
    );

    setSelectedSdsDetail(
      null
    );

    setSdsDetailError(
      ""
    );

    setCurrentView(
      "sdsDetail"
    );

    scrollTop();
  }


  function backToChemicalDetail() {
    clearSdsDetailState();

    if (
      selectedChemicalId
    ) {
      setCurrentView(
        "detail"
      );

    } else {
      setCurrentView(
        "inventory"
      );
    }

    scrollTop();
  }


  function handleFileChange(
    event
  ) {
    const file =
      event
        .target
        .files?.[0];

    setUploadError(
      ""
    );

    setUploadResult(
      null
    );


    if (!file) {
      setSelectedFile(
        null
      );

      return;
    }


    const isPdf =
      file.type ===
        "application/pdf" ||
      file.name
        .toLowerCase()
        .endsWith(
          ".pdf"
        );


    if (!isPdf) {
      setSelectedFile(
        null
      );

      setUploadError(
        "Lütfen PDF formatında bir SDS dosyası seçin."
      );

      if (
        fileInputRef.current
      ) {
        fileInputRef
          .current
          .value =
          "";
      }

      return;
    }


    setSelectedFile(
      file
    );
  }


  function clearSelectedFile() {
    setSelectedFile(
      null
    );

    setUploadError(
      ""
    );

    setUploadResult(
      null
    );

    if (
      fileInputRef.current
    ) {
      fileInputRef
        .current
        .value =
        "";
    }
  }


  async function handleUpload(
    event
  ) {
    event.preventDefault();


    if (
      !selectedFile
    ) {
      setUploadError(
        "Önce bir SDS PDF dosyası seçmelisiniz."
      );

      return;
    }


    try {
      setUploadLoading(
        true
      );

      setUploadError(
        ""
      );

      setUploadResult(
        null
      );


      const formData =
        new FormData();

      formData.append(
        "file",
        selectedFile
      );


      const response =
        await fetch(
          `${API_BASE_URL}/sds/upload`,
          {
            method:
              "POST",

            body:
              formData,
          }
        );


      let responseData =
        null;


      try {
        responseData =
          await response.json();

      } catch {
        responseData =
          null;
      }


      if (
        !response.ok
      ) {
        throw new Error(
          getApiErrorMessage(
            responseData
          )
        );
      }


      setUploadResult(
        responseData ||
          {
            success:
              true,
          }
      );


      setSelectedFile(
        null
      );


      if (
        fileInputRef.current
      ) {
        fileInputRef
          .current
          .value =
          "";
      }


      await loadChemicals();

    } catch (
      requestError
    ) {
      console.error(
        requestError
      );

      setUploadError(
        requestError.message ||
          "SDS yükleme işlemi sırasında bir hata oluştu."
      );

    } finally {
      setUploadLoading(
        false
      );
    }
  }


  function renderSidebar() {
    const inventoryActive =
      [
        "inventory",
        "detail",
        "sdsDetail",
      ].includes(
        currentView
      );


    return (
      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">
            G
          </div>

          <div>

            <h1>
              GEBKIM
            </h1>

            <p>
              SDS AI Platform
            </p>

          </div>

        </div>


        <nav className="navigation">

          <button
            className={`nav-item ${
              currentView ===
              "dashboard"
                ? "active"
                : ""
            }`}
            onClick={
              showDashboard
            }
          >
            <span>
              ⌂
            </span>

            Genel Bakış
          </button>


          <button
            className={`nav-item ${
              inventoryActive
                ? "active"
                : ""
            }`}
            onClick={
              showInventory
            }
          >
            <span>
              ◫
            </span>

            Kimyasal Envanteri
          </button>


          <button
            className={`nav-item ${
              currentView ===
              "upload"
                ? "active"
                : ""
            }`}
            onClick={
              showUpload
            }
          >
            <span>
              ⇧
            </span>

            SDS Yükle
          </button>


          <button
            className={`nav-item ${
              currentView ===
              "review"
                ? "active"
                : ""
            }`}
            onClick={
              showReview
            }
          >
            <span>
              !
            </span>

            İnceleme Gerekenler
          </button>


          <button
            className={`nav-item ${
              currentView ===
              "coshh"
                ? "active"
                : ""
            }`}
            onClick={
              showCoshh
            }
          >
            <span>
              ⚗
            </span>

            ILO/COSHH
          </button>


          <button
            className={`nav-item ${
              currentView ===
              "reports"
                ? "active"
                : ""
            }`}
            onClick={
              showReports
            }
          >
            <span>
              ▤
            </span>

            Raporlar
          </button>

        </nav>


        <div className="sidebar-footer">

          <div className="sidebar-footer-icon">
            ✓
          </div>

          <div>

            <strong>
              Sistem aktif
            </strong>

            <span>
              FastAPI bağlantısı aktif
            </span>

          </div>

        </div>

      </aside>
    );
  }


  if (
    currentView ===
    "dashboard"
  ) {
    return (
      <div className="app">

        {
          renderSidebar()
        }


        <main className="main-content">

          <header className="topbar">

            <div>

              <p className="eyebrow">
                GENEL BAKIŞ
              </p>

              <h2>
                SDS Yönetim Paneli
              </h2>

              <p className="page-description">
                Kimyasal envanterinin, SDS kayıtlarının ve
                inceleme durumlarının güncel özetini takip edin.
              </p>

            </div>


            <button
              className="primary-button"
              onClick={
                showUpload
              }
            >
              <span>
                ＋
              </span>

              Yeni SDS Yükle
            </button>

          </header>


          <section className="summary-grid">

            <div className="summary-card">

              <div className="summary-label">
                Toplam Kimyasal
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : chemicals.length
                }
              </div>

              <div className="summary-footnote">
                Envanterdeki toplam kayıt
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-label">
                Güncel SDS
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : totalCurrentSds
                }
              </div>

              <div className="summary-footnote">
                Güncel SDS bulunan kimyasal
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-label">
                İnceleme Gereken
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : totalNeedsReview
                }
              </div>

              <div className="summary-footnote">
                Manuel kontrol bekleyen kayıt
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-label">
                Toplam SDS Dokümanı
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : totalSdsDocuments
                }
              </div>

              <div className="summary-footnote">
                Tüm revizyonlar dahil
              </div>

            </div>

          </section>


          <section className="inventory-card">

            <div className="inventory-header">

              <div>

                <h3>
                  Hızlı İşlemler
                </h3>

                <p>
                  Sık kullanılan ekranlara hızlıca geçin.
                </p>

              </div>

            </div>


            <div className="upload-actions">

              <button
                className="primary-button"
                onClick={
                  showUpload
                }
              >
                SDS Yükle
              </button>


              <button
                className="secondary-button"
                onClick={
                  showInventory
                }
              >
                Kimyasal Envanteri
              </button>


              <button
                className="secondary-button"
                onClick={
                  showReview
                }
              >
                İnceleme Gerekenler
              </button>


              <button
                className="secondary-button"
                onClick={
                  showCoshh
                }
              >
                ILO/COSHH
              </button>


              <button
                className="secondary-button"
                onClick={
                  showReports
                }
              >
                Raporlar
              </button>

            </div>

          </section>


          <section className="inventory-card revision-history-card">

            <div className="inventory-header">

              <div>

                <h3>
                  Dikkat Gerektiren Kayıtlar
                </h3>

                <p>
                  İnceleme bekleyen veya güncel SDS kaydı bulunmayan kimyasallar.
                </p>

              </div>


              <div className="revision-count">
                {
                  attentionChemicals.length
                }{" "}
                kayıt
              </div>

            </div>


            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>
                      Kimyasal
                    </th>

                    <th>
                      Üretici
                    </th>

                    <th>
                      Durum
                    </th>

                    <th></th>
                  </tr>

                </thead>


                <tbody>

                  {
                    attentionChemicals
                      .slice(
                        0,
                        5
                      )
                      .map(
                        (
                          chemical
                        ) => {
                          const status =
                            getStatus(
                              chemical
                            );

                          return (
                            <tr
                              key={
                                chemical.id
                              }
                            >

                              <td>
                                <strong>
                                  {
                                    chemical
                                      .product_name
                                  }
                                </strong>
                              </td>

                              <td>
                                {
                                  chemical
                                    .manufacturer ||
                                  "—"
                                }
                              </td>

                              <td>

                                <span
                                  className={`status-badge ${status.className}`}
                                >

                                  <span className="status-dot" />

                                  {
                                    status.text
                                  }

                                </span>

                              </td>

                              <td>

                                <button
                                  className="detail-button"
                                  onClick={() =>
                                    openChemicalDetail(
                                      chemical.id
                                    )
                                  }
                                >
                                  Detay
                                  <span>
                                    →
                                  </span>
                                </button>

                              </td>

                            </tr>
                          );
                        }
                      )
                  }


                  {
                    !loading &&
                    attentionChemicals.length ===
                      0 && (

                      <tr>

                        <td colSpan="4">

                          <div className="empty-state">
                            Dikkat gerektiren kayıt bulunmuyor.
                          </div>

                        </td>

                      </tr>

                    )
                  }

                </tbody>

              </table>

            </div>

          </section>


          <section className="inventory-card revision-history-card">

            <div className="inventory-header">

              <div>

                <h3>
                  Son Güncel SDS Kayıtları
                </h3>

                <p>
                  En son yüklenen veya güncellenen güncel SDS kayıtları.
                </p>

              </div>

            </div>


            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>
                      Kimyasal
                    </th>

                    <th>
                      Üretici
                    </th>

                    <th>
                      Revizyon
                    </th>

                    <th>
                      İşlem Durumu
                    </th>

                    <th></th>
                  </tr>

                </thead>


                <tbody>

                  {
                    recentCurrentSds
                      .slice(
                        0,
                        5
                      )
                      .map(
                        (
                          item
                        ) => (

                          <tr
                            key={
                              item.sds.id
                            }
                          >

                            <td>

                              <strong>
                                {
                                  item.productName
                                }
                              </strong>

                            </td>

                            <td>
                              {
                                item.manufacturer
                              }
                            </td>

                            <td>
                              {
                                formatDate(
                                  item.sds
                                    .revision_date
                                )
                              }
                            </td>

                            <td>

                              <span className="processing-status">
                                {
                                  formatProcessingStatus(
                                    item.sds
                                      .processing_status
                                  )
                                }
                              </span>

                            </td>

                            <td>

                              <button
                                className="detail-button"
                                onClick={() =>
                                  openSdsDetail(
                                    item.sds.id,
                                    item.chemicalId
                                  )
                                }
                              >
                                Detay
                                <span>
                                  →
                                </span>
                              </button>

                            </td>

                          </tr>

                        )
                      )
                  }

                </tbody>

              </table>

            </div>

          </section>

        </main>

      </div>
    );
  }


  if (
    currentView ===
    "coshh"
  ) {
    return (
      <div className="app">

        {
          renderSidebar()
        }


        <main className="main-content">

          <CoshhAssessment
            chemicals={
              chemicals
            }
            apiBaseUrl={
              API_BASE_URL
            }
            initialChemicalId={
              coshhInitialChemicalId
            }
            onBackInventory={
              showInventory
            }
          />

        </main>

      </div>
    );
  }


  if (
    currentView ===
    "reports"
  ) {
    return (
      <div className="app">

        {
          renderSidebar()
        }


        <main className="main-content">

          <header className="topbar">

            <div>

              <p className="eyebrow">
                RAPORLAMA
              </p>

              <h2>
                Raporlar
              </h2>

              <p className="page-description">
                Kimyasal envanteri ve SDS kayıtlarının güncel
                durumunu tek ekranda takip edin.
              </p>

            </div>

          </header>


          <section className="summary-grid">

            <div className="summary-card">

              <div className="summary-label">
                Toplam Kimyasal
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : chemicals.length
                }
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-label">
                Toplam SDS Dokümanı
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : totalSdsDocuments
                }
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-label">
                İnceleme Gereken
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : totalNeedsReview
                }
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-label">
                Güncel SDS Olmayan
              </div>

              <div className="summary-value">
                {
                  loading
                    ? "—"
                    : totalWithoutCurrentSds
                }
              </div>

            </div>

          </section>


          <section className="inventory-card">

            <div className="inventory-header">

              <div>

                <h3>
                  Üretici Bazında Kimyasal Dağılımı
                </h3>

              </div>

            </div>


            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>
                      Üretici
                    </th>

                    <th>
                      Kimyasal Sayısı
                    </th>

                    <th>
                      Pay
                    </th>
                  </tr>

                </thead>


                <tbody>

                  {
                    manufacturerReport.map(
                      (
                        item
                      ) => (

                        <tr
                          key={
                            item.manufacturer
                          }
                        >

                          <td>

                            <strong>
                              {
                                item.manufacturer
                              }
                            </strong>

                          </td>

                          <td>
                            {
                              item.count
                            }
                          </td>

                          <td>

                            {
                              chemicals.length >
                              0
                                ? `${(
                                    (
                                      item.count /
                                      chemicals.length
                                    ) *
                                    100
                                  ).toFixed(
                                    1
                                  )}%`
                                : "0%"
                            }

                          </td>

                        </tr>

                      )
                    )
                  }

                </tbody>

              </table>

            </div>

          </section>


          <section className="inventory-card revision-history-card">

            <div className="inventory-header">

              <div>

                <h3>
                  Güncel SDS İşlem Durumları
                </h3>

              </div>

            </div>


            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>
                      İşlem Durumu
                    </th>

                    <th>
                      Kayıt Sayısı
                    </th>
                  </tr>

                </thead>


                <tbody>

                  {
                    processingStatusReport.map(
                      (
                        item
                      ) => (

                        <tr
                          key={
                            item.status
                          }
                        >

                          <td>

                            <span className="processing-status">

                              {
                                item.status ===
                                "no_sds"
                                  ? "SDS Yok"
                                  : formatProcessingStatus(
                                      item.status
                                    )
                              }

                            </span>

                          </td>

                          <td>
                            {
                              item.count
                            }
                          </td>

                        </tr>

                      )
                    )
                  }

                </tbody>

              </table>

            </div>

          </section>


          <section className="inventory-card revision-history-card">

            <div className="inventory-header">

              <div>

                <h3>
                  Son Güncel SDS Kayıtları
                </h3>

              </div>

            </div>


            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>
                      Kimyasal
                    </th>

                    <th>
                      Üretici
                    </th>

                    <th>
                      SDS
                    </th>

                    <th>
                      Revizyon
                    </th>

                    <th>
                      İşlem Durumu
                    </th>

                    <th></th>
                  </tr>

                </thead>


                <tbody>

                  {
                    recentCurrentSds.map(
                      (
                        item
                      ) => (

                        <tr
                          key={
                            item.sds.id
                          }
                        >

                          <td>

                            <strong>
                              {
                                item.productName
                              }
                            </strong>

                          </td>

                          <td>
                            {
                              item.manufacturer
                            }
                          </td>

                          <td>

                            <div className="sds-file-cell">
                              {
                                item.sds
                                  .original_filename ||
                                `SDS #${item.sds.id}`
                              }
                            </div>

                          </td>

                          <td>
                            {
                              formatDate(
                                item.sds
                                  .revision_date
                              )
                            }
                          </td>

                          <td>

                            <span className="processing-status">
                              {
                                formatProcessingStatus(
                                  item.sds
                                    .processing_status
                                )
                              }
                            </span>

                          </td>

                          <td>

                            <button
                              className="detail-button"
                              onClick={() =>
                                openSdsDetail(
                                  item.sds.id,
                                  item.chemicalId
                                )
                              }
                            >
                              Detay
                              <span>
                                →
                              </span>
                            </button>

                          </td>

                        </tr>

                      )
                    )
                  }

                </tbody>

              </table>

            </div>

          </section>

        </main>

      </div>
    );
  }


  if (
    currentView ===
    "review"
  ) {
    return (
      <div className="app">

        {
          renderSidebar()
        }

        <main className="main-content">

          <ReviewQueue
            chemicals={
              chemicals
            }
            apiBaseUrl={
              API_BASE_URL
            }
            onOpenChemical={
              openChemicalDetail
            }
            onOpenSds={
              openSdsDetail
            }
          />

        </main>

      </div>
    );
  }


  if (
    currentView ===
    "upload"
  ) {
    return (
      <div className="app">

        {
          renderSidebar()
        }


        <main className="main-content">

          <header className="detail-header">

            <div>

              <p className="eyebrow">
                SDS YÖNETİMİ
              </p>

              <h2>
                SDS Yükle
              </h2>

              <p className="page-description">
                Güvenlik Bilgi Formu PDF dosyasını sisteme yükleyin.
                Dosya backend tarafından analiz edilerek kimyasal ve
                SDS kayıtları oluşturulur.
              </p>

            </div>

          </header>


          <section className="upload-layout">

            <form
              className="upload-card"
              onSubmit={
                handleUpload
              }
            >

              <div className="upload-card-header">

                <div className="upload-icon">
                  ⇧
                </div>

                <div>

                  <h3>
                    Yeni SDS Dosyası
                  </h3>

                  <p>
                    Yalnızca PDF formatındaki Güvenlik Bilgi
                    Formlarını yükleyin.
                  </p>

                </div>

              </div>


              <label className="file-drop-area">

                <input
                  ref={
                    fileInputRef
                  }
                  className="file-input"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={
                    handleFileChange
                  }
                />

                <div className="file-drop-icon">
                  PDF
                </div>

                <strong>
                  {
                    selectedFile
                      ? "Dosya seçildi"
                      : "SDS PDF dosyasını seçin"
                  }
                </strong>

                <span>
                  Dosya seçmek için bu alana tıklayın
                </span>

              </label>


              {
                selectedFile && (

                  <div className="selected-file">

                    <div className="selected-file-icon">
                      PDF
                    </div>

                    <div className="selected-file-info">

                      <strong>
                        {
                          selectedFile.name
                        }
                      </strong>

                      <span>
                        {
                          formatFileSize(
                            selectedFile.size
                          )
                        }
                      </span>

                    </div>

                    <button
                      type="button"
                      className="remove-file-button"
                      onClick={
                        clearSelectedFile
                      }
                      disabled={
                        uploadLoading
                      }
                    >
                      Kaldır
                    </button>

                  </div>

                )
              }


              {
                uploadError && (

                  <div className="upload-message error-message">

                    <strong>
                      Yükleme başarısız
                    </strong>

                    <span>
                      {
                        uploadError
                      }
                    </span>

                  </div>

                )
              }


              {
                uploadResult && (

                  <div className="upload-message success-message">

                    <strong>
                      SDS başarıyla işlendi
                    </strong>

                    <span>
                      Dosya backend tarafından alındı ve işlem
                      tamamlandı. Kimyasal envanteri yenilendi.
                    </span>

                  </div>

                )
              }


              <div className="upload-actions">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={
                    showInventory
                  }
                >
                  Envantere Dön
                </button>


                <button
                  type="submit"
                  className="primary-button"
                  disabled={
                    !selectedFile ||
                    uploadLoading
                  }
                >

                  {
                    uploadLoading
                      ? "SDS İşleniyor..."
                      : "SDS'yi Yükle"
                  }

                </button>

              </div>

            </form>

          </section>

        </main>

      </div>
    );
  }


  if (
    currentView ===
      "sdsDetail" &&
    selectedSdsId
  ) {
    const storage =
      selectedSdsDetail
        ?.storage_info;

    const ppe =
      selectedSdsDetail
        ?.ppe_info;

    const physical =
      selectedSdsDetail
        ?.physical_properties;


    return (
      <div className="app">

        {
          renderSidebar()
        }


        <main className="main-content">

          <button
            className="back-button"
            onClick={
              backToChemicalDetail
            }
          >
            ← Kimyasal Detayına Dön
          </button>


          {
            sdsDetailLoading && (

              <section className="inventory-card">

                <div className="empty-state detail-loading">
                  SDS detayları yükleniyor...
                </div>

              </section>

            )
          }


          {
            !sdsDetailLoading &&
            sdsDetailError && (

              <section className="inventory-card">

                <div className="empty-state detail-error">
                  {
                    sdsDetailError
                  }
                </div>

              </section>

            )
          }


          {
            !sdsDetailLoading &&
            !sdsDetailError &&
            selectedSdsDetail && (
              <>

                <header className="detail-header sds-detail-header">

                  <div>

                    <p className="eyebrow">
                      SDS DETAYI
                    </p>

                    <h2>

                      {
                        selectedSdsDetail
                          .original_filename ||
                        `SDS #${selectedSdsId}`
                      }

                    </h2>

                    <p className="page-description">

                      SDS #
                      {
                        selectedSdsDetail
                          .sds_id
                      }

                      {" · "}

                      Kimyasal #
                      {
                        selectedSdsDetail
                          .chemical_id
                      }

                    </p>

                  </div>


                  <span
                    className={`status-badge status-large ${
                      selectedSdsDetail
                        .is_current
                        ? "ready"
                        : "empty"
                    }`}
                  >

                    <span className="status-dot" />

                    {
                      selectedSdsDetail
                        .is_current
                        ? "Güncel SDS"
                        : "Eski Revizyon"
                    }

                  </span>

                </header>


                <section className="sds-overview-grid">

                  <div className="detail-card">

                    <div className="detail-card-title">
                      Doküman Bilgileri
                    </div>


                    <div className="detail-info-list">

                      <DetailRow
                        label="SDS ID"
                        value={`#${selectedSdsDetail.sds_id}`}
                      />

                      <DetailRow
                        label="Kimyasal ID"
                        value={`#${selectedSdsDetail.chemical_id}`}
                      />

                      <DetailRow
                        label="Revizyon Tarihi"
                        value={
                          formatDate(
                            selectedSdsDetail.revision_date
                          )
                        }
                      />

                      <DetailRow
                        label="Hazırlanma Tarihi"
                        value={
                          formatDate(
                            selectedSdsDetail.preparation_date
                          )
                        }
                      />

                      <DetailRow
                        label="Versiyon"
                        value={
                          selectedSdsDetail.version ||
                          "—"
                        }
                      />

                      <DetailRow
                        label="İşlem Durumu"
                        value={
                          formatProcessingStatus(
                            selectedSdsDetail.processing_status
                          )
                        }
                      />

                      <DetailRow
                        label="Bölüm Sayısı"
                        value={
                          selectedSdsDetail.section_count ??
                          "—"
                        }
                      />

                    </div>

                  </div>


                  <div className="detail-card hazard-summary-card">

                    <div className="detail-card-title">
                      Tehlike Özeti
                    </div>


                    <div className="sds-code-group">

                      <span className="sds-code-label">
                        H Kodları
                      </span>

                      <div className="sds-code-list">

                        {
                          normalizeList(
                            selectedSdsDetail
                              .hazard_codes
                          ).map(
                            (
                              code
                            ) => (

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
                        }

                      </div>

                    </div>


                    <div className="sds-code-group">

                      <span className="sds-code-label">
                        GHS
                      </span>

                      <div className="sds-code-list">

                        {
                          normalizeList(
                            selectedSdsDetail
                              .ghs_codes
                          ).map(
                            (
                              code
                            ) => (

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
                        }

                      </div>

                    </div>

                  </div>

                </section>


                <section className="sds-section-card">

                  <div className="sds-section-heading">

                    <div>

                      <p className="eyebrow">
                        BÖLÜM 2
                      </p>

                      <h3>
                        Önlem Kodları
                      </h3>

                    </div>

                  </div>


                  <div className="sds-code-list precaution-code-list">

                    {
                      normalizeList(
                        selectedSdsDetail
                          .precautionary_codes
                      ).map(
                        (
                          code
                        ) => (

                          <span
                            className="sds-code precaution-code"
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
                    }

                  </div>

                </section>


                <section className="sds-section-card">

                  <div className="sds-section-heading">

                    <div>

                      <p className="eyebrow">
                        BÖLÜM 7
                      </p>

                      <h3>
                        Elleçleme ve Depolama
                      </h3>

                    </div>

                  </div>


                  {
                    storage
                      ? (

                        <div className="sds-detail-grid">

                          <div className="sds-detail-block">

                            <h4>
                              Güvenli Elleçleme
                            </h4>

                            <TextList
                              value={
                                storage
                                  .handling_precautions
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Depolama Koşulları
                            </h4>

                            <TextList
                              value={
                                storage
                                  .storage_conditions
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Uyumsuz Maddeler
                            </h4>

                            <TextList
                              value={
                                storage
                                  .incompatible_materials
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Yangın / Patlama Önlemleri
                            </h4>

                            <TextList
                              value={
                                storage
                                  .fire_explosion_precautions
                              }
                            />

                          </div>


                          <div className="sds-detail-block sds-detail-block-wide">

                            <h4>
                              Belirli Son Kullanım
                            </h4>

                            <TextList
                              value={
                                storage
                                  .specific_end_use
                              }
                            />

                          </div>

                        </div>

                      )
                      : (

                        <div className="sds-empty-text">
                          Bölüm 7 için yapılandırılmış veri bulunmuyor.
                        </div>

                      )
                  }

                </section>


                <section className="sds-section-card">

                  <div className="sds-section-heading">

                    <div>

                      <p className="eyebrow">
                        BÖLÜM 8
                      </p>

                      <h3>
                        Maruziyet Kontrolleri ve KKD
                      </h3>

                    </div>

                  </div>


                  {
                    ppe
                      ? (

                        <div className="sds-detail-grid">

                          <div className="sds-detail-block">

                            <h4>
                              Solunum Koruması
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .respiratory_protection
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              El Koruması
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .hand_protection
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Eldiven Malzemesi
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .glove_materials
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Eldiven Kalınlığı
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .glove_thickness
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Göz / Yüz Koruması
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .eye_face_protection
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Vücut Koruması
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .body_protection
                              }
                            />

                          </div>


                          <div className="sds-detail-block sds-detail-block-wide">

                            <h4>
                              Mühendislik Kontrolleri
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .engineering_controls
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Maruziyet Limitleri
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .exposure_limits
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              Hijyen Önlemleri
                            </h4>

                            <TextList
                              value={
                                ppe
                                  .hygiene_measures
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              DNEL
                            </h4>

                            <TextList
                              value={
                                ppe.dnel
                              }
                            />

                          </div>


                          <div className="sds-detail-block">

                            <h4>
                              PNEC
                            </h4>

                            <TextList
                              value={
                                ppe.pnec
                              }
                            />

                          </div>

                        </div>

                      )
                      : (

                        <div className="sds-empty-text">
                          Bölüm 8 için yapılandırılmış veri bulunmuyor.
                        </div>

                      )
                  }

                </section>


                <section className="sds-section-card">

                  <div className="sds-section-heading">

                    <div>

                      <p className="eyebrow">
                        BÖLÜM 9
                      </p>

                      <h3>
                        Fiziksel ve Kimyasal Özellikler
                      </h3>

                    </div>

                  </div>


                  {
                    physical
                      ? (

                        <div className="physical-properties-grid">

                          {
                            PHYSICAL_PROPERTY_LABELS.map(
                              (
                                [
                                  key,
                                  label,
                                ]
                              ) => (

                                <div
                                  className="physical-property-item"
                                  key={
                                    key
                                  }
                                >

                                  <span>
                                    {
                                      label
                                    }
                                  </span>

                                  <strong>
                                    {
                                      physical[
                                        key
                                      ] ||
                                      "—"
                                    }
                                  </strong>

                                </div>

                              )
                            )
                          }

                        </div>

                      )
                      : (

                        <div className="sds-empty-text">
                          Bölüm 9 için yapılandırılmış veri bulunmuyor.
                        </div>

                      )
                  }

                </section>


                <section className="sds-section-card raw-sections-card">

                  <div className="sds-section-heading">

                    <div>

                      <p className="eyebrow">
                        KAYNAK METİN
                      </p>

                      <h3>
                        Ham SDS Bölümleri
                      </h3>

                    </div>

                  </div>


                  <div className="raw-section-list">

                    {
                      selectedSdsDetail
                        .sections
                        ?.map(
                          (
                            section
                          ) => (

                            <details
                              className="raw-section-item"
                              key={
                                section
                                  .section_number
                              }
                            >

                              <summary>

                                Bölüm{" "}
                                {
                                  section
                                    .section_number
                                }

                              </summary>

                              <pre>
                                {
                                  section
                                    .content
                                }
                              </pre>

                            </details>

                          )
                        )
                    }

                  </div>

                </section>

              </>
            )
          }

        </main>

      </div>
    );
  }


  if (
    currentView ===
      "detail" &&
    selectedChemicalId
  ) {
    const status =
      selectedChemical
        ? getStatus(
            selectedChemical
          )
        : null;


    return (
      <div className="app">

        {
          renderSidebar()
        }


        <main className="main-content">

          <button
            className="back-button"
            onClick={
              showInventory
            }
          >
            ← Kimyasal Envanterine Dön
          </button>


          {
            detailLoading && (

              <section className="inventory-card">

                <div className="empty-state detail-loading">
                  Kimyasal detayları yükleniyor...
                </div>

              </section>

            )
          }


          {
            !detailLoading &&
            detailError && (

              <section className="inventory-card">

                <div className="empty-state detail-error">
                  {
                    detailError
                  }
                </div>

              </section>

            )
          }


          {
            !detailLoading &&
            !detailError &&
            selectedChemical && (
              <>

                <header className="detail-header">

                  <div>

                    <p className="eyebrow">
                      KİMYASAL DETAYI
                    </p>

                    <h2>
                      {
                        selectedChemical
                          .product_name
                      }
                    </h2>

                    <p className="page-description">
                      {
                        selectedChemical
                          .manufacturer ||
                        "Üretici bilgisi bulunmuyor"
                      }
                    </p>

                  </div>


                  {
                    status && (

                      <span
                        className={`status-badge status-large ${status.className}`}
                      >

                        <span className="status-dot" />

                        {
                          status.text
                        }

                      </span>

                    )
                  }

                </header>


                <section className="detail-grid">

                  <div className="detail-card">

                    <div className="detail-card-title">
                      Kimyasal Bilgileri
                    </div>


                    <div className="detail-info-list">

                      <DetailRow
                        label="Kimyasal ID"
                        value={`#${selectedChemical.id}`}
                      />

                      <DetailRow
                        label="Ürün Adı"
                        value={
                          selectedChemical.product_name
                        }
                      />

                      <DetailRow
                        label="Üretici"
                        value={
                          selectedChemical.manufacturer ||
                          "—"
                        }
                      />

                      <DetailRow
                        label="Dahili Kod"
                        value={
                          selectedChemical.internal_code ||
                          "—"
                        }
                      />

                      <DetailRow
                        label="Durum"
                        value={
                          selectedChemical.is_active
                            ? "Aktif"
                            : "Pasif"
                        }
                      />

                    </div>

                  </div>


                  <div className="detail-card">

                    <div className="detail-card-title">
                      Tanımlayıcılar
                    </div>


                    {
                      selectedChemical
                        .identifiers
                        ?.length >
                      0
                        ? (

                          <div className="identifier-detail-list">

                            {
                              selectedChemical
                                .identifiers
                                .map(
                                  (
                                    identifier
                                  ) => (

                                    <div
                                      className="identifier-detail-item"
                                      key={
                                        identifier.id
                                      }
                                    >

                                      <span>
                                        {
                                          identifier
                                            .identifier_type
                                        }
                                      </span>

                                      <strong>
                                        {
                                          identifier
                                            .identifier_value
                                        }
                                      </strong>

                                    </div>

                                  )
                                )
                            }

                          </div>

                        )
                        : (

                          <div className="detail-empty">
                            Tanımlayıcı bilgisi bulunmuyor.
                          </div>

                        )
                    }

                  </div>


                  <div className="detail-card current-sds-card">

                    <div className="detail-card-title">
                      Güncel SDS
                    </div>


                    {
                      selectedChemical
                        .current_sds
                        ? (
                          <>

                            <div className="detail-info-list">

                              <DetailRow
                                label="Doküman ID"
                                value={`#${selectedChemical.current_sds.id}`}
                              />

                              <DetailRow
                                label="Dosya Adı"
                                value={
                                  selectedChemical
                                    .current_sds
                                    .original_filename
                                }
                              />

                              <DetailRow
                                label="Revizyon Tarihi"
                                value={
                                  formatDate(
                                    selectedChemical
                                      .current_sds
                                      .revision_date
                                  )
                                }
                              />

                              <DetailRow
                                label="Hazırlanma Tarihi"
                                value={
                                  formatDate(
                                    selectedChemical
                                      .current_sds
                                      .preparation_date
                                  )
                                }
                              />

                              <DetailRow
                                label="Versiyon"
                                value={
                                  selectedChemical
                                    .current_sds
                                    .version ||
                                  "—"
                                }
                              />

                              <DetailRow
                                label="İşlem Durumu"
                                value={
                                  formatProcessingStatus(
                                    selectedChemical
                                      .current_sds
                                      .processing_status
                                  )
                                }
                              />

                              <DetailRow
                                label="Yüklenme Tarihi"
                                value={
                                  formatDateTime(
                                    selectedChemical
                                      .current_sds
                                      .uploaded_at
                                  )
                                }
                              />

                            </div>


                            <button
                              className="sds-open-button"
                              onClick={() =>
                                openSdsDetail(
                                  selectedChemical
                                    .current_sds
                                    .id,
                                  selectedChemical
                                    .id
                                )
                              }
                            >
                              SDS Detayını Gör
                              <span>
                                →
                              </span>
                            </button>

                          </>
                        )
                        : (

                          <div className="detail-empty">
                            Bu kimyasal için güncel SDS bulunmuyor.
                          </div>

                        )
                    }

                  </div>

                </section>


                <section className="inventory-card revision-history-card">

                  <div className="inventory-header">

                    <div>

                      <h3>
                        ILO / COSHH Değerlendirmesi
                      </h3>

                      <p>
                        Bu kimyasal için proses bazlı risk değerlendirme taslağı oluşturun.
                      </p>

                    </div>


                    <button
                      className="primary-button"
                      onClick={() =>
                        openCoshhAssessment(
                          selectedChemical.id
                        )
                      }
                    >
                      Değerlendirme Oluştur
                    </button>

                  </div>

                </section>


                <section className="inventory-card revision-history-card">

                  <div className="inventory-header">

                    <div>

                      <h3>
                        SDS Revizyon Geçmişi
                      </h3>

                      <p>
                        Bu kimyasal için sisteme yüklenmiş SDS dokümanları.
                      </p>

                    </div>


                    <div className="revision-count">

                      {
                        sdsHistory
                          ?.total_sds_documents ||
                        0
                      }

                      {" "}
                      doküman

                    </div>

                  </div>


                  <div className="table-wrapper">

                    <table>

                      <thead>

                        <tr>
                          <th>
                            ID
                          </th>

                          <th>
                            Dosya
                          </th>

                          <th>
                            Revizyon Tarihi
                          </th>

                          <th>
                            Versiyon
                          </th>

                          <th>
                            İşlem Durumu
                          </th>

                          <th>
                            Durum
                          </th>

                          <th>
                            Yüklenme Tarihi
                          </th>

                          <th></th>
                        </tr>

                      </thead>


                      <tbody>

                        {
                          sdsHistory
                            ?.sds_documents
                            ?.map(
                              (
                                sds
                              ) => (

                                <tr
                                  key={
                                    sds.id
                                  }
                                >

                                  <td>

                                    <strong>
                                      #
                                      {
                                        sds.id
                                      }
                                    </strong>

                                  </td>

                                  <td>

                                    <div className="sds-file-cell">
                                      {
                                        sds.original_filename
                                      }
                                    </div>

                                  </td>

                                  <td>
                                    {
                                      formatDate(
                                        sds.revision_date
                                      )
                                    }
                                  </td>

                                  <td>
                                    {
                                      sds.version ||
                                      "—"
                                    }
                                  </td>

                                  <td>

                                    <span className="processing-status">

                                      {
                                        formatProcessingStatus(
                                          sds.processing_status
                                        )
                                      }

                                    </span>

                                  </td>

                                  <td>

                                    {
                                      sds.is_current
                                        ? (

                                          <span className="current-badge">
                                            Güncel
                                          </span>

                                        )
                                        : (

                                          <span className="old-badge">
                                            Eski Revizyon
                                          </span>

                                        )
                                    }

                                  </td>

                                  <td>
                                    {
                                      formatDateTime(
                                        sds.uploaded_at
                                      )
                                    }
                                  </td>

                                  <td>

                                    <button
                                      className="detail-button"
                                      onClick={() =>
                                        openSdsDetail(
                                          sds.id,
                                          selectedChemical.id
                                        )
                                      }
                                    >
                                      Detay
                                      <span>
                                        →
                                      </span>
                                    </button>

                                  </td>

                                </tr>

                              )
                            )
                        }

                      </tbody>

                    </table>

                  </div>

                </section>

              </>
            )
          }

        </main>

      </div>
    );
  }


  return (
    <div className="app">

      {
        renderSidebar()
      }


      <main className="main-content">

        <header className="topbar">

          <div>

            <p className="eyebrow">
              KİMYASAL YÖNETİMİ
            </p>

            <h2>
              Kimyasal Envanteri
            </h2>

            <p className="page-description">
              Kimyasalları, SDS dokümanlarını ve revizyon
              durumlarını merkezi olarak yönetin.
            </p>

          </div>


          <button
            className="primary-button"
            onClick={
              showUpload
            }
          >
            <span>
              ＋
            </span>

            SDS Yükle
          </button>

        </header>


        <section className="summary-grid">

          <div className="summary-card">

            <div className="summary-label">
              Toplam Kimyasal
            </div>

            <div className="summary-value">
              {
                loading
                  ? "—"
                  : chemicals.length
              }
            </div>

            <div className="summary-footnote">
              Aktif kayıtlar
            </div>

          </div>


          <div className="summary-card">

            <div className="summary-label">
              Güncel SDS
            </div>

            <div className="summary-value">
              {
                loading
                  ? "—"
                  : totalCurrentSds
              }
            </div>

            <div className="summary-footnote">
              Güncel doküman
            </div>

          </div>


          <div className="summary-card">

            <div className="summary-label">
              İnceleme Bekleyen
            </div>

            <div className="summary-value">
              {
                loading
                  ? "—"
                  : totalNeedsReview
              }
            </div>

            <div className="summary-footnote">
              Kontrol gerektiren kayıt
            </div>

          </div>


          <div className="summary-card">

            <div className="summary-label">
              SDS Revizyonları
            </div>

            <div className="summary-value">
              {
                loading
                  ? "—"
                  : totalSdsDocuments
              }
            </div>

            <div className="summary-footnote">
              Toplam doküman
            </div>

          </div>

        </section>


        <section className="inventory-card">

          <div className="inventory-header">

            <div>

              <h3>
                Kimyasallar
              </h3>

              <p>
                Ürün adı, üretici veya CAS / EC numarası ile arama yapabilirsiniz.
              </p>

            </div>


            <div className="search-box">

              <span>
                ⌕
              </span>

              <input
                type="text"
                placeholder="Kimyasal ara..."
                value={
                  searchTerm
                }
                onChange={
                  (
                    event
                  ) =>
                    setSearchTerm(
                      event.target.value
                    )
                }
              />

            </div>

          </div>


          <div className="table-wrapper">

            <table>

              <thead>

                <tr>
                  <th>
                    Ürün
                  </th>

                  <th>
                    Üretici
                  </th>

                  <th>
                    CAS / EC
                  </th>

                  <th>
                    SDS Revizyonu
                  </th>

                  <th>
                    Durum
                  </th>

                  <th></th>
                </tr>

              </thead>


              <tbody>

                {
                  loading && (

                    <tr>

                      <td colSpan="6">

                        <div className="empty-state">
                          Kimyasallar yükleniyor...
                        </div>

                      </td>

                    </tr>

                  )
                }


                {
                  !loading &&
                  error && (

                    <tr>

                      <td colSpan="6">

                        <div className="empty-state detail-error">
                          {
                            error
                          }
                        </div>

                      </td>

                    </tr>

                  )
                }


                {
                  !loading &&
                  !error &&
                  filteredChemicals.map(
                    (
                      chemical
                    ) => {
                      const cas =
                        getIdentifier(
                          chemical.identifiers,
                          "CAS"
                        );

                      const ec =
                        getIdentifier(
                          chemical.identifiers,
                          "EC"
                        );

                      const status =
                        getStatus(
                          chemical
                        );


                      return (

                        <tr
                          key={
                            chemical.id
                          }
                        >

                          <td>

                            <div className="product-cell">

                              <div className="chemical-icon">
                                C
                              </div>

                              <div>

                                <strong>
                                  {
                                    chemical.product_name
                                  }
                                </strong>

                                <span>
                                  Kimyasal #
                                  {
                                    chemical.id
                                  }
                                </span>

                              </div>

                            </div>

                          </td>

                          <td>
                            {
                              chemical.manufacturer ||
                              "—"
                            }
                          </td>

                          <td>

                            <div className="identifier-cell">

                              <span>

                                <strong>
                                  CAS
                                </strong>

                                {
                                  cas
                                }

                              </span>


                              <span>

                                <strong>
                                  EC
                                </strong>

                                {
                                  ec
                                }

                              </span>

                            </div>

                          </td>

                          <td>

                            <div className="revision-cell">

                              <strong>
                                {
                                  formatDate(
                                    chemical
                                      .current_sds
                                      ?.revision_date
                                  )
                                }
                              </strong>

                              <span>

                                {
                                  chemical
                                    .current_sds
                                    ?.version
                                    ? `Versiyon ${chemical.current_sds.version}`
                                    : "Versiyon bilgisi yok"
                                }

                              </span>

                            </div>

                          </td>

                          <td>

                            <span
                              className={`status-badge ${status.className}`}
                            >

                              <span className="status-dot" />

                              {
                                status.text
                              }

                            </span>

                          </td>

                          <td>

                            <button
                              className="detail-button"
                              onClick={() =>
                                openChemicalDetail(
                                  chemical.id
                                )
                              }
                            >
                              Detay
                              <span>
                                →
                              </span>
                            </button>

                          </td>

                        </tr>

                      );
                    }
                  )
                }


                {
                  !loading &&
                  !error &&
                  filteredChemicals.length ===
                    0 && (

                    <tr>

                      <td colSpan="6">

                        <div className="empty-state">
                          Aramanızla eşleşen kimyasal bulunamadı.
                        </div>

                      </td>

                    </tr>

                  )
                }

              </tbody>

            </table>

          </div>

        </section>

      </main>

    </div>
  );
}


export default App;