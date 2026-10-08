import {
  useEffect,
  useState,
} from "react";


function formatDate(dateValue) {
  if (!dateValue) {
    return "—";
  }

  const date = new Date(
    `${dateValue}T00:00:00`
  );

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return dateValue;
  }

  return new Intl.DateTimeFormat(
    "tr-TR"
  ).format(date);
}


function ReviewQueue({
  chemicals,
  apiBaseUrl,
  onOpenChemical,
  onOpenSds,
}) {
  const [
    reviewItems,
    setReviewItems,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  useEffect(() => {
    let cancelled = false;


    async function loadReviewItems() {
      try {
        setLoading(true);
        setError("");

        /*
         * Önce sadece gerçekten inceleme kaydı
         * bulunan kimyasalları seçiyoruz.
         *
         * Böylece tüm kimyasallar için gereksiz
         * SDS geçmişi isteği atmıyoruz.
         */
        const candidates =
          chemicals.filter(
            (chemical) =>
              (
                chemical
                  .sds_summary
                  ?.needs_review_count ||
                0
              ) > 0
          );


        if (
          candidates.length === 0
        ) {
          if (!cancelled) {
            setReviewItems([]);
          }

          return;
        }


        const results =
          await Promise.all(
            candidates.map(
              async (
                chemical
              ) => {
                try {
                  const response =
                    await fetch(
                      `${apiBaseUrl}/chemicals/${chemical.id}/sds`
                    );


                  if (
                    !response.ok
                  ) {
                    return [];
                  }


                  const data =
                    await response.json();


                  const documents =
                    data.sds_documents ||
                    [];


                  return documents

                    .filter(
                      (sds) =>
                        sds.processing_status ===
                        "needs_review"
                    )

                    .map(
                      (sds) => ({
                        chemicalId:
                          chemical.id,

                        productName:
                          chemical.product_name,

                        manufacturer:
                          chemical.manufacturer,

                        internalCode:
                          chemical.internal_code,

                        sds,
                      })
                    );

                } catch (
                  requestError
                ) {
                  console.error(
                    requestError
                  );

                  return [];
                }
              }
            )
          );


        if (!cancelled) {
          setReviewItems(
            results.flat()
          );
        }

      } catch (
        requestError
      ) {
        console.error(
          requestError
        );

        if (!cancelled) {
          setError(
            "İnceleme kayıtları yüklenirken bir hata oluştu."
          );
        }

      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }


    loadReviewItems();


    return () => {
      cancelled = true;
    };

  }, [
    chemicals,
    apiBaseUrl,
  ]);


  return (
    <>
      <header className="topbar review-page-header">

        <div>

          <p className="eyebrow">
            KALİTE KONTROLÜ
          </p>

          <h2>
            İnceleme Gerekenler
          </h2>

          <p className="page-description">
            Otomatik SDS analizinde manuel kontrol
            gerektiren kayıtları burada inceleyebilirsiniz.
          </p>

        </div>


        <div className="review-summary-badge">

          <strong>
            {
              loading
                ? "—"
                : reviewItems.length
            }
          </strong>

          <span>
            bekleyen kayıt
          </span>

        </div>

      </header>


      <section className="inventory-card review-card">

        <div className="inventory-header">

          <div>

            <h3>
              Kontrol Bekleyen SDS'ler
            </h3>

            <p>
              Sistem emin olmadığı SDS'leri otomatik
              olarak burada işaretler.
            </p>

          </div>

        </div>


        <div className="table-wrapper">

          <table>

            <thead>

              <tr>
                <th>Kimyasal</th>
                <th>SDS</th>
                <th>Revizyon</th>
                <th>Versiyon</th>
                <th>Durum</th>
                <th></th>
              </tr>

            </thead>


            <tbody>

              {loading && (

                <tr>

                  <td colSpan="6">

                    <div className="empty-state">
                      İnceleme kayıtları yükleniyor...
                    </div>

                  </td>

                </tr>

              )}


              {!loading &&
                error && (

                  <tr>

                    <td colSpan="6">

                      <div className="empty-state detail-error">
                        {error}
                      </div>

                    </td>

                  </tr>

                )}


              {!loading &&
                !error &&
                reviewItems.map(
                  (item) => (

                    <tr
                      key={
                        item.sds.id
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
                                item.productName
                              }
                            </strong>

                            <span>
                              Kimyasal #
                              {
                                item.chemicalId
                              }
                            </span>

                          </div>

                        </div>

                      </td>


                      <td>

                        <div className="review-sds-cell">

                          <strong>
                            SDS #
                            {
                              item.sds.id
                            }
                          </strong>

                          <span>
                            {
                              item.sds
                                .original_filename ||
                              "Dosya adı bulunmuyor"
                            }
                          </span>

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
                        {
                          item.sds
                            .version ||
                          "—"
                        }
                      </td>


                      <td>

                        <span className="status-badge review">

                          <span className="status-dot">
                          </span>

                          İnceleme Gerekli

                        </span>

                      </td>


                      <td>

                        <div className="review-actions">

                          <button
                            className="detail-button"
                            onClick={() =>
                              onOpenChemical(
                                item.chemicalId
                              )
                            }
                          >
                            Kimyasal
                          </button>


                          <button
                            className="review-primary-button"
                            onClick={() =>
                              onOpenSds(
                                item.sds.id,
                                item.chemicalId
                              )
                            }
                          >
                            SDS'yi İncele
                            <span>→</span>
                          </button>

                        </div>

                      </td>

                    </tr>

                  )
                )}


              {!loading &&
                !error &&
                reviewItems.length ===
                  0 && (

                  <tr>

                    <td colSpan="6">

                      <div className="review-empty-state">

                        <div className="review-empty-icon">
                          ✓
                        </div>

                        <strong>
                          İnceleme bekleyen SDS bulunmuyor
                        </strong>

                        <span>
                          Otomatik kontrolden geçen SDS
                          kayıtlarında şu anda manuel
                          inceleme gerektiren bir durum yok.
                        </span>

                      </div>

                    </td>

                  </tr>

                )}

            </tbody>

          </table>

        </div>

      </section>
    </>
  );
}


export default ReviewQueue;