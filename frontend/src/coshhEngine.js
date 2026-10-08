// ==========================================================
// GEBKIM SDS AI PLATFORM
// ILO / COSHH CONTROL BANDING ENGINE
// ==========================================================
//
// Temel metodoloji:
// - HSE COSHH Essentials
// - ILO International Chemical Control Toolkit
//
// Bu motor;
// 1. H kodlarından inhalasyon Hazard Group A-E belirler.
// 2. Skin/Eye "S" uyarısını belirler.
// 3. Kullanılan miktarı Small / Medium / Large sınıflandırır.
// 4. Katılar için dustiness kullanır.
// 5. Sıvılar için boiling point + process temperature ile
//    volatility hesaplar.
// 6. Control Approach CA1-CA4 üretir.
// 7. Genel kontrol önerilerini üretir.
//
// NOT:
// Karışım konsantrasyon kuralları bu V1 motorunda
// uygulanmamaktadır.
// ==========================================================


// ==========================================================
// HAZARD GROUP DEFINITIONS
// ==========================================================

const HAZARD_GROUPS = {
  A: [
    "H304",
    "H315",
    "H319",
    "H336",
    "EUH066",
    "EU66",
  ],

  B: [
    "H302",
    "H312",
    "H332",
    "H371",
  ],

  C: [
    "H301",
    "H311",
    "H314",
    "H317",
    "H318",
    "H331",
    "H335",
    "H370",
    "H373",
    "EUH071",
    "EU71",
  ],

  D: [
    "H300",
    "H310",
    "H330",
    "H351",
    "H360",
    "H361",
    "H362",
    "H372",
  ],

  E: [
    "H334",
    "H340",
    "H341",
    "H350",
    "EUH070",
    "EU70",
  ],
};


// En yüksek öncelik E'dir.
const HAZARD_PRIORITY = [
  "E",
  "D",
  "C",
  "B",
  "A",
];


// ==========================================================
// SKIN / EYE RISK
// ==========================================================
//
// Grup S, inhalasyon Hazard Group A-E'nin yerine geçmez.
// Ek bir skin/eye kontrol gereksinimidir.
// ==========================================================

const SKIN_EYE_CODES = [
  "H310",
  "H311",
  "H312",
  "H314",
  "H315",
  "H317",
  "H318",
  "H319",
  "EUH070",
  "EU70",
];


// ==========================================================
// CONTROL APPROACH NAMES
// ==========================================================

const CONTROL_APPROACHES = {
  1: {
    code: "CA1",
    title: "Genel Havalandırma",
    description:
      "İyi endüstriyel hijyen uygulamaları ve yeterli genel havalandırma.",
    genericSheet: "G100",
  },

  2: {
    code: "CA2",
    title: "Mühendislik Kontrolü / Lokal Emiş",
    description:
      "Kaynağa yakın mühendislik kontrolü veya lokal emiş havalandırması (LEV) uygulanmalıdır.",
    genericSheet: "G200",
  },

  3: {
    code: "CA3",
    title: "Kapalı Sistem / Containment",
    description:
      "Proses mümkün olduğunca kapalı sistem içerisinde yürütülmelidir.",
    genericSheet: "G300",
  },

  4: {
    code: "CA4",
    title: "Uzman Tavsiyesi / Özel Kontrol",
    description:
      "Özel kontrol önlemleri ve yetkin iş hijyeni / İSG uzmanı değerlendirmesi gereklidir.",
    genericSheet: "G400",
  },
};


// ==========================================================
// NORMALIZATION
// ==========================================================

function normalizeCode(value) {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "");
}


function normalizeList(values) {
  if (!Array.isArray(values)) {
    if (!values) {
      return [];
    }

    values = [values];
  }

  return [
    ...new Set(
      values
        .map(normalizeCode)
        .filter(Boolean)
    ),
  ];
}


// ==========================================================
// HAZARD GROUP
// ==========================================================

export function determineHazardGroup(
  hazardCodes
) {
  const codes =
    normalizeList(
      hazardCodes
    );


  if (codes.length === 0) {
    return {
      group: null,
      matchedCodes: [],
      status: "needs_review",
      note:
        "Sağlık tehlikesi H kodu bulunamadığı için Hazard Group belirlenemedi.",
    };
  }


  for (
    const group
    of HAZARD_PRIORITY
  ) {
    const matchedCodes =
      codes.filter(
        (code) =>
          HAZARD_GROUPS[
            group
          ].includes(
            code
          )
      );


    if (
      matchedCodes.length >
      0
    ) {
      return {
        group,
        matchedCodes,
        status: "calculated",
        note:
          `Hazard Group ${group}, en yüksek tehlike grubuna karşılık gelen H kodlarına göre belirlendi.`,
      };
    }
  }


  return {
    group: null,
    matchedCodes: [],
    status: "needs_review",
    note:
      "Mevcut H kodları COSHH Essentials A-E tablosunda eşleştirilemedi. Uzman incelemesi gerekli.",
  };
}


// ==========================================================
// SKIN / EYE RISK
// ==========================================================

export function determineSkinEyeRisk(
  hazardCodes
) {
  const codes =
    normalizeList(
      hazardCodes
    );


  const matchedCodes =
    codes.filter(
      (code) =>
        SKIN_EYE_CODES.includes(
          code
        )
    );


  return {
    required:
      matchedCodes.length >
      0,

    group:
      matchedCodes.length >
        0
        ? "S"
        : null,

    matchedCodes,

    guidanceSheets:
      matchedCodes.length >
        0
        ? [
            "S100",
            "S101",
            "S102",
          ]
        : [],

    note:
      matchedCodes.length >
        0
        ? "Cilt/göz teması açısından ek kontrol tedbirleri değerlendirilmelidir."
        : "Ek Grup S göstergesi tespit edilmedi.",
  };
}


// ==========================================================
// AMOUNT / SCALE OF USE
// ==========================================================
//
// ILO yaklaşımı:
// Small  -> grams / millilitres
// Medium -> kilograms / litres
// Large  -> tonnes / cubic metres
// ==========================================================

export function determineAmountBand(
  amountValue,
  amountUnit
) {
  const numericAmount =
    Number(
      amountValue
    );

  const unit =
    String(
      amountUnit || ""
    )
      .trim()
      .toLowerCase();


  if (
    !Number.isFinite(
      numericAmount
    ) ||
    numericAmount <= 0
  ) {
    return {
      band: null,
      status: "needs_review",
      note:
        "Geçerli kullanılan miktar girilmedi.",
    };
  }


  if (
    [
      "g",
      "gram",
      "grams",
      "ml",
    ].includes(
      unit
    )
  ) {
    return {
      band: "Small",
      label: "Küçük",
      status: "calculated",
      note:
        "Gram / mililitre ölçeği.",
    };
  }


  if (
    [
      "kg",
      "kilogram",
      "kilograms",
      "l",
      "lt",
      "litre",
      "liter",
    ].includes(
      unit
    )
  ) {
    return {
      band: "Medium",
      label: "Orta",
      status: "calculated",
      note:
        "Kilogram / litre ölçeği.",
    };
  }


  if (
    [
      "ton",
      "tonne",
      "tonnes",
      "t",
      "m3",
      "m³",
    ].includes(
      unit
    )
  ) {
    return {
      band: "Large",
      label: "Büyük",
      status: "calculated",
      note:
        "Ton / metreküp ölçeği.",
    };
  }


  return {
    band: null,
    status: "needs_review",
    note:
      "Miktar birimi ILO kullanım ölçeğiyle eşleştirilemedi.",
  };
}


// ==========================================================
// DUSTINESS
// ==========================================================

export function determineDustiness(
  dustiness
) {
  const value =
    String(
      dustiness || ""
    )
      .trim()
      .toLocaleLowerCase(
        "tr-TR"
      );


  if (
    [
      "düşük",
      "dusuk",
      "low",
    ].includes(
      value
    )
  ) {
    return {
      band: "Low",
      label: "Düşük",
      status: "calculated",
    };
  }


  if (
    [
      "orta",
      "medium",
    ].includes(
      value
    )
  ) {
    return {
      band: "Medium",
      label: "Orta",
      status: "calculated",
    };
  }


  if (
    [
      "yüksek",
      "yuksek",
      "high",
    ].includes(
      value
    )
  ) {
    return {
      band: "High",
      label: "Yüksek",
      status: "calculated",
    };
  }


  return {
    band: null,
    label: null,
    status: "needs_review",
    note:
      "Katı kimyasal için tozluluk seviyesi seçilmelidir.",
  };
}


// ==========================================================
// NUMBER PARSER
// ==========================================================

function parseNumericValue(
  value
) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }


  if (
    typeof value ===
    "number"
  ) {
    return Number.isFinite(
      value
    )
      ? value
      : null;
  }


  const text =
    String(value)
      .replace(",", ".")
      .trim();


  const match =
    text.match(
      /-?\d+(?:\.\d+)?/
    );


  if (!match) {
    return null;
  }


  const number =
    Number(
      match[0]
    );


  return Number.isFinite(
    number
  )
    ? number
    : null;
}


// ==========================================================
// VOLATILITY
// ==========================================================
//
// HSE:
// Room temperature:
// BP <= 50°C       -> High
// BP >50 <=150°C   -> Medium
// BP >150°C        -> Low
//
// Heating/cooling:
// BP <= 2*PT + 10          -> High
// BP >= 5*PT + 50          -> Low
// Between                   -> Medium
// ==========================================================

export function determineVolatility({
  boilingPoint,
  processTemperature,
}) {
  const bp =
    parseNumericValue(
      boilingPoint
    );


  const providedPt =
    parseNumericValue(
      processTemperature
    );


  const pt =
    providedPt ??
    25;


  if (bp === null) {
    return {
      band: null,
      label: null,
      processTemperature:
        pt,
      boilingPoint: null,
      status: "needs_review",
      note:
        "Kaynama noktası bulunamadığı için uçuculuk hesaplanamadı.",
    };
  }


  // Gaz veya çok düşük kaynama
  // noktası olan maddeler için
  // standart COSHH Essentials
  // yaklaşımı yeterli değildir.
  if (bp <= 20) {
    return {
      band: null,
      label: null,
      processTemperature:
        pt,
      boilingPoint: bp,
      status: "special_case",
      note:
        "Kaynama noktası 20 °C veya altında. Madde gaz/buhar fazında olabilir; standart COSHH Essentials değerlendirmesi uygun olmayabilir.",
    };
  }


  const highLimit =
    2 * pt + 10;

  const lowLimit =
    5 * pt + 50;


  if (
    bp <= highLimit
  ) {
    return {
      band: "High",
      label: "Yüksek",
      processTemperature:
        pt,
      boilingPoint: bp,
      status: "calculated",
      note:
        "Kaynama noktası ve proses sıcaklığına göre yüksek uçuculuk.",
    };
  }


  if (
    bp >= lowLimit
  ) {
    return {
      band: "Low",
      label: "Düşük",
      processTemperature:
        pt,
      boilingPoint: bp,
      status: "calculated",
      note:
        "Kaynama noktası ve proses sıcaklığına göre düşük uçuculuk.",
    };
  }


  return {
    band: "Medium",
    label: "Orta",
    processTemperature:
      pt,
    boilingPoint: bp,
    status: "calculated",
    note:
      "Kaynama noktası ve proses sıcaklığına göre orta uçuculuk.",
  };
}


// ==========================================================
// CONTROL APPROACH MATRIX
// ==========================================================
//
// Matriste:
// Low         = low dustiness / volatility
// MediumSolid = medium dustiness
// MediumLiquid= medium volatility
// High        = high dustiness / volatility
// ==========================================================

const CONTROL_MATRIX = {
  A: {
    Small: {
      Low: 1,
      MediumSolid: 1,
      MediumLiquid: 1,
      High: 1,
    },

    Medium: {
      Low: 1,
      MediumSolid: 1,
      MediumLiquid: 1,
      High: 2,
    },

    Large: {
      Low: 1,
      MediumSolid: 2,
      MediumLiquid: 1,
      High: 2,
    },
  },


  B: {
    Small: {
      Low: 1,
      MediumSolid: 1,
      MediumLiquid: 1,
      High: 1,
    },

    Medium: {
      Low: 1,
      MediumSolid: 2,
      MediumLiquid: 2,
      High: 2,
    },

    Large: {
      Low: 1,
      MediumSolid: 3,
      MediumLiquid: 2,
      High: 3,
    },
  },


  C: {
    Small: {
      Low: 1,
      MediumSolid: 1,
      MediumLiquid: 2,
      High: 2,
    },

    Medium: {
      Low: 2,
      MediumSolid: 3,
      MediumLiquid: 3,
      High: 3,
    },

    Large: {
      Low: 2,
      MediumSolid: 4,
      MediumLiquid: 4,
      High: 4,
    },
  },


  D: {
    Small: {
      Low: 2,
      MediumSolid: 2,
      MediumLiquid: 3,
      High: 3,
    },

    Medium: {
      Low: 3,
      MediumSolid: 4,
      MediumLiquid: 4,
      High: 4,
    },

    Large: {
      Low: 3,
      MediumSolid: 4,
      MediumLiquid: 4,
      High: 4,
    },
  },


  E: {
    Small: {
      Low: 4,
      MediumSolid: 4,
      MediumLiquid: 4,
      High: 4,
    },

    Medium: {
      Low: 4,
      MediumSolid: 4,
      MediumLiquid: 4,
      High: 4,
    },

    Large: {
      Low: 4,
      MediumSolid: 4,
      MediumLiquid: 4,
      High: 4,
    },
  },
};


// ==========================================================
// CONTROL APPROACH CALCULATION
// ==========================================================

export function determineControlApproach({
  hazardGroup,
  amountBand,
  physicalForm,
  exposureBand,
}) {
  if (
    !hazardGroup ||
    !amountBand ||
    !physicalForm ||
    !exposureBand
  ) {
    return {
      number: null,
      code: null,
      title:
        "Hesaplanamadı",
      status:
        "needs_review",
      note:
        "Kontrol yaklaşımı için gerekli girdiler eksik.",
    };
  }


  const physical =
    String(
      physicalForm
    )
      .trim()
      .toLocaleLowerCase(
        "tr-TR"
      );


  const isSolid =
    physical === "katı" ||
    physical === "kati" ||
    physical === "solid";


  const isLiquid =
    physical === "sıvı" ||
    physical === "sivi" ||
    physical === "liquid";


  if (
    !isSolid &&
    !isLiquid
  ) {
    return {
      number: 4,
      ...CONTROL_APPROACHES[
        4
      ],
      status:
        "special_case",
      note:
        "Gaz veya diğer fiziksel formlar için standart COSHH Essentials matrisi doğrudan uygulanamaz. Uzman değerlendirmesi önerilir.",
    };
  }


  let matrixColumn =
    exposureBand;


  if (
    exposureBand ===
    "Medium"
  ) {
    matrixColumn =
      isSolid
        ? "MediumSolid"
        : "MediumLiquid";
  }


  const approachNumber =
    CONTROL_MATRIX
      ?.[hazardGroup]
      ?.[amountBand]
      ?.[matrixColumn];


  if (
    !approachNumber
  ) {
    return {
      number: null,
      code: null,
      title:
        "Hesaplanamadı",
      status:
        "needs_review",
      note:
        "COSHH kontrol matrisiyle eşleşme oluşturulamadı.",
    };
  }


  return {
    number:
      approachNumber,

    ...CONTROL_APPROACHES[
      approachNumber
    ],

    status:
      "calculated",

    note:
      `Hazard Group ${hazardGroup}, ${amountBand} kullanım ölçeği ve ${exposureBand} maruziyet potansiyeline göre hesaplandı.`,
  };
}


// ==========================================================
// CONTROL RECOMMENDATIONS
// ==========================================================

function createRecommendations({
  controlApproach,
  skinEyeRisk,
  physicalForm,
  existingControls,
}) {
  const recommendations =
    [];


  if (
    controlApproach
      ?.number === 1
  ) {
    recommendations.push(
      "Çalışma alanında yeterli genel havalandırma sağlayın."
    );

    recommendations.push(
      "Kimyasalın gereksiz açıkta kalmasını ve dökülmesini önleyin."
    );

    recommendations.push(
      "İyi endüstriyel hijyen uygulamalarını sürdürün."
    );
  }


  if (
    controlApproach
      ?.number === 2
  ) {
    recommendations.push(
      "Kimyasalın açığa çıktığı noktada lokal emiş havalandırması (LEV) kullanın."
    );

    recommendations.push(
      "Emiş sisteminin kimyasal kaynağına mümkün olduğunca yakın olmasını sağlayın."
    );

    recommendations.push(
      "LEV sisteminin bakım ve performans kontrollerini planlı olarak gerçekleştirin."
    );
  }


  if (
    controlApproach
      ?.number === 3
  ) {
    recommendations.push(
      "Prosesi mümkün olduğunca tamamen kapalı sistem içerisinde yürütün."
    );

    recommendations.push(
      "Transfer ve dolum noktalarında kapalı bağlantılar tercih edin."
    );

    recommendations.push(
      "Bakım ve arıza durumları için kontrollü müdahale prosedürü oluşturun."
    );
  }


  if (
    controlApproach
      ?.number === 4
  ) {
    recommendations.push(
      "Yetkin iş hijyeni / İSG uzmanından prosese özgü değerlendirme alın."
    );

    recommendations.push(
      "Maruziyet ölçümü ve sağlık gözetimi gereksinimini değerlendirin."
    );

    recommendations.push(
      "İkame, tam kapalı sistem ve ileri mühendislik kontrollerini değerlendirin."
    );
  }


  if (
    skinEyeRisk
      ?.required
  ) {
    recommendations.push(
      "Cilt ve göz temasını önleyecek uygun kimyasal koruyucu eldiven, gözlük/yüz siperi ve koruyucu giysi seçimini değerlendirin."
    );

    recommendations.push(
      "Cilt/göz temasına yönelik S100, S101 ve S102 kontrol rehberlerini dikkate alın."
    );
  }


  const existing =
    String(
      existingControls ||
      ""
    ).trim();


  if (!existing) {
    recommendations.push(
      "Mevcut kontrol tedbirleri kayıt altına alınmamış; değerlendirme tamamlanmadan önce mevcut kontroller doğrulanmalıdır."
    );
  }


  const physical =
    String(
      physicalForm ||
      ""
    ).toLocaleLowerCase(
      "tr-TR"
    );


  if (
    physical === "katı" ||
    physical === "kati"
  ) {
    recommendations.push(
      "Toz oluşumunu azaltacak çalışma yöntemleri ve temizlik prosedürleri uygulayın; kuru süpürme gibi toz kaldıran yöntemlerden kaçının."
    );
  }


  return [
    ...new Set(
      recommendations
    ),
  ];
}


// ==========================================================
// MAIN ANALYSIS
// ==========================================================

export function calculateCoshhAnalysis({
  hazardCodes = [],
  amountValue,
  amountUnit,
  physicalForm,
  dustiness,
  boilingPoint,
  processTemperature,
  existingControls = "",
}) {
  const hazard =
    determineHazardGroup(
      hazardCodes
    );


  const skinEye =
    determineSkinEyeRisk(
      hazardCodes
    );


  const amount =
    determineAmountBand(
      amountValue,
      amountUnit
    );


  const normalizedPhysical =
    String(
      physicalForm ||
      ""
    )
      .trim()
      .toLocaleLowerCase(
        "tr-TR"
      );


  const isSolid =
    normalizedPhysical ===
      "katı" ||
    normalizedPhysical ===
      "kati" ||
    normalizedPhysical ===
      "solid";


  const isLiquid =
    normalizedPhysical ===
      "sıvı" ||
    normalizedPhysical ===
      "sivi" ||
    normalizedPhysical ===
      "liquid";


  let exposure = {
    band: null,
    label: null,
    status:
      "needs_review",
    note:
      "Fiziksel forma göre maruziyet potansiyeli hesaplanamadı.",
  };


  if (isSolid) {
    exposure =
      determineDustiness(
        dustiness
      );
  }


  if (isLiquid) {
    exposure =
      determineVolatility({
        boilingPoint,
        processTemperature,
      });
  }


  const control =
    determineControlApproach({
      hazardGroup:
        hazard.group,

      amountBand:
        amount.band,

      physicalForm,

      exposureBand:
        exposure.band,
    });


  const recommendations =
    createRecommendations({
      controlApproach:
        control,

      skinEyeRisk:
        skinEye,

      physicalForm,

      existingControls,
    });


  const warnings = [];


  if (
    !hazard.group
  ) {
    warnings.push(
      "Hazard Group belirlenemedi."
    );
  }


  if (
    !amount.band
  ) {
    warnings.push(
      "Kullanım miktarı sınıflandırılamadı."
    );
  }


  if (
    !exposure.band
  ) {
    warnings.push(
      "Tozluluk / uçuculuk sınıflandırılamadı."
    );
  }


  if (
    normalizedPhysical ===
      "gaz" ||
    normalizedPhysical ===
      "gas"
  ) {
    warnings.push(
      "COSHH Essentials standart yaklaşımı gazları değerlendirmek için tasarlanmamıştır."
    );
  }


  if (
    hazard.group === "E"
  ) {
    warnings.push(
      "Hazard Group E için uzman tavsiyesi gereklidir."
    );
  }


  const needsReview =
    warnings.length > 0 ||
    control.status !==
      "calculated";


  return {
    hazardGroup:
      hazard.group,

    hazardMatchedCodes:
      hazard.matchedCodes,

    skinEyeGroup:
      skinEye.group,

    skinEyeRequired:
      skinEye.required,

    skinEyeCodes:
      skinEye.matchedCodes,

    amountBand:
      amount.band,

    amountLabel:
      amount.label,

    exposureBand:
      exposure.band,

    exposureLabel:
      exposure.label,

    exposureNote:
      exposure.note,

    boilingPoint:
      exposure.boilingPoint ??
      parseNumericValue(
        boilingPoint
      ),

    processTemperature:
      exposure.processTemperature ??
      parseNumericValue(
        processTemperature
      ),

    controlApproach:
      control.code,

    controlApproachNumber:
      control.number,

    controlApproachTitle:
      control.title,

    controlApproachDescription:
      control.description,

    controlGuidanceSheet:
      control.genericSheet,

    skinGuidanceSheets:
      skinEye.guidanceSheets,

    recommendations,

    warnings,

    needsReview,

    status:
      needsReview
        ? "Uzman incelemesi gerekli"
        : "Ön değerlendirme tamamlandı",

    methodology:
      "ILO International Chemical Control Toolkit / HSE COSHH Essentials control banding",

    disclaimer:
      "Bu sonuç kontrol banding esaslı bir ön değerlendirmedir. İşyeri risk değerlendirmesi, maruziyet ölçümleri, mesleki maruziyet sınırları ve uzman değerlendirmesinin yerine geçmez.",
  };
}