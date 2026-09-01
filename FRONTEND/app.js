(() => {
  "use strict";

  const API_URL = "http://127.0.0.1:8001/analyze-photo";
  const MIN_FILES = 2;
  const MAX_FILES = 5;
  const MODEL_LABEL = "Vision AI";
  const MAX_OPEN_RECS = 1;
  const LOADING_STEPS = [
    "Подготавливаем фотографии",
    "Определяем состояние травы",
    "Ищем признаки сорняков и стресса",
    "Анализируем плотность и цвет",
    "Формируем рекомендации",
  ];
  const PRIORITY_IDS = [
    "apply_fungicide",
    "water_increase",
    "full_weed_control",
    "spot_weed_control",
    "overseed",
    "apply_fertilizer",
    "mow_lawn",
  ];

  const STATE_LABELS = {
    dryness: "Сухость",
    pale_grass: "Бледная трава",
    weed_presence: "Сорняки",
    weed_type: "Тип сорняков",
    weed_density: "Плотность сорняков",
    fungal_signs: "Признаки грибка",
    thin_lawn: "Редкий газон",
    bare_spots: "Проплешины",
    needs_mowing: "Требуется кошение",
    moss_presence: "Мох",
    soil_issue: "Проблема почвы",
    confidence: "Уверенность анализа",
  };

  const VALUE_LABELS = {
    true: "Да",
    false: "Нет",
    low: "Низкая",
    medium: "Средняя",
    high: "Высокая",
    broadleaf: "Широколиственные",
    grass: "Злаковые",
    mixed: "Смешанные",
  };

  const ACTION_COPY = {
    apply_fertilizer: {
      icon: "🌿",
      title: "Подкормите газон",
      tip: "Вносите удобрение перед поливом или перед дождём.",
      productKind: "fertilizer",
      warnings: ["Дозировку и способ внесения смотрите в инструкции выбранного удобрения."],
    },
    spot_weed_control: {
      icon: "🌿",
      title: "Удалите сорняки вручную или точечно",
      tip: "Обрабатывайте только отдельные сорняки в сухую безветренную погоду, не попадая на окружающую газонную траву.",
      productKind: "herbicide",
      prependProducts: ["Ручная прополка"],
      warnings: [
        "Перед применением проверьте, разрешено ли выбранное средство для использования на газоне.",
        "Дозировку, способ применения и меры безопасности смотрите в инструкции выбранного препарата.",
      ],
    },
    full_weed_control: {
      icon: "🌿",
      title: "Обработайте газон от сорняков",
      tip: "Обрабатывайте в сухую безветренную погоду и не скашивайте газон сразу после обработки.",
      productKind: "herbicide",
      warnings: [
        "Перед применением проверьте, разрешено ли выбранное средство для использования на газоне.",
        "Дозировку, способ применения и меры безопасности смотрите в инструкции выбранного препарата.",
      ],
    },
    overseed: {
      icon: "🌱",
      title: "Подсейте газон",
      tip: "После подсева поддерживайте почву влажной.",
      productKind: "seed",
      beforeTipNotes: [
        "Для лучшего результата перед подсевом рекомендуется провести скарификацию газона. Это улучшает контакт семян с почвой и повышает всхожесть.",
      ],
      warnings: [],
    },
    water_increase: {
      icon: "💧",
      title: "Увеличьте полив",
      tip: "Лучше поливать редко, но обильно, утром или вечером.",
      productKind: null,
      warnings: [],
    },
    water_reduce: {
      icon: "💧",
      title: "Сократите полив",
      tip: "Дайте почве просохнуть между поливами, чтобы снизить риск грибка.",
      productKind: null,
      warnings: [],
    },
    mow_lawn: {
      icon: "✂️",
      title: "Покосите газон",
      tip: "Не срезайте более одной трети высоты травы за один раз.",
      productKind: null,
      warnings: [],
    },
    apply_fungicide: {
      icon: "🛡️",
      title: "Обработайте газон от болезней",
      tip: "Сначала уменьшите влажность и улучшите проветривание участка.",
      productKind: "herbicide",
      warnings: [
        "Дозировку, способ применения и меры безопасности смотрите в инструкции выбранного препарата.",
      ],
    },
    aeration: {
      icon: "🪴",
      title: "Проведите аэрацию почвы",
      tip: "После аэрации полезно пройтись граблями и при необходимости подсеять траву.",
      productKind: null,
      warnings: [],
    },
    dethatching: {
      icon: "🧹",
      title: "Уберите войлок",
      tip: "Удаляйте войлок в сухую погоду, не повреждая корни слишком глубоко.",
      productKind: null,
      warnings: [],
    },
    improve_drainage: {
      icon: "🌧️",
      title: "Улучшите дренаж",
      tip: "Проверьте понижения рельефа и места, где вода застаивается после дождя.",
      productKind: null,
      warnings: [],
    },
    reduce_shade: {
      icon: "☀️",
      title: "Увеличьте доступ света",
      tip: "Аккуратно проредите нижние ветви деревьев и кустарников над газоном.",
      productKind: null,
      warnings: [],
    },
    soil_improvement: {
      icon: "🪨",
      title: "Улучшите почву",
      tip: "Вносите органику тонким слоем и равномерно распределяйте по участку.",
      productKind: null,
      warnings: [],
    },
    mowing_adjust: {
      icon: "✂️",
      title: "Скорректируйте стрижку",
      tip: "В жару поднимайте высоту кошения, чтобы снизить стресс газона.",
      productKind: null,
      warnings: [],
    },
  };

  const STATE_ORDER = [
    "dryness", "pale_grass", "weed_presence", "weed_type", "weed_density",
    "fungal_signs", "thin_lawn", "bare_spots", "needs_mowing", "moss_presence",
    "soil_issue", "confidence",
  ];

  const PROBLEM_TRUE_KEYS = new Set([
    "dryness", "pale_grass", "weed_presence", "fungal_signs", "thin_lawn",
    "bare_spots", "needs_mowing", "moss_presence",
  ]);

  const CATEGORY_PHRASES = {
    "Азотное удобрение": "Азотные удобрения для газона",
    "Мочевина (карбамид)": "Мочевина (карбамид) для газона",
    "Аммиачная селитра": "Аммиачная селитра для газона",
    "Комплексное удобрение NPK (сбалансированное)": "Комплексные удобрения NPK для газона",
    "Комплексное удобрение с микроэлементами": "Комплексные удобрения с микроэлементами",
    "Осеннее фосфорно-калийное удобрение": "Осенние фосфорно-калийные удобрения для газона",
    "Суперфосфат": "Суперфосфат для подкормки газона",
    "Сульфат калия": "Сульфат калия для газона",
    "Железо (сульфат или хелат)": "Препараты железа для газона",
    "Компост": "Компост для улучшения почвы газона",
    "Биогумус": "Биогумус для газона",
    "Древесная зола": "Древесная зола для газона",
    "Селективный гербицид против двудольных сорняков":
      "Селективные гербициды для газона против двудольных сорняков",
    "Комбинированный селективный гербицид":
      "Комбинированные селективные гербициды для газона",
    "Гербицид против злаковых сорняков": "Гербициды для газона против злаковых сорняков",
    "Неселективный гербицид (сплошного действия)": "Неселективные гербициды сплошного действия",
    "Контактный гербицид": "Контактные гербициды",
    "Системный гербицид": "Системные гербициды для газона",
    "Довсходовый гербицид": "Довсходовые гербициды",
    "Послевсходовый гербицид": "Послевсходовые гербициды для газона",
    "Средство против мха (на основе железа)": "Средства против мха на основе железа",
    "Точечная обработка гербицидом": "Точечная обработка гербицидом",
    "Универсальная травосмесь": "Универсальные травосмеси для газона",
    "Спортивная травосмесь": "Спортивные травосмеси",
    "Теневая травосмесь": "Теневые травосмеси",
    "Декоративная (партерная) травосмесь": "Декоративные (партерные) травосмеси",
    "Травосмесь для подсева": "Травосмеси для подсева и ремонта газона",
  };

  const els = {
    startLayout: document.getElementById("startLayout"),
    resultsLayout: document.getElementById("resultsLayout"),
    dropzone: document.getElementById("dropzone"),
    fileInput: document.getElementById("fileInput"),
    previews: document.getElementById("previews"),
    previewsCompact: document.getElementById("previewsCompact"),
    counter: document.getElementById("counterValue"),
    analyzeBtn: document.getElementById("analyzeBtn"),
    clearBtn: document.getElementById("clearBtn"),
    loadingOverlay: document.getElementById("loadingOverlay"),
    loadingStep: document.getElementById("loadingStep"),
    alert: document.getElementById("alert"),
    toast: document.getElementById("toast"),
    stateGrid: document.getElementById("stateGrid"),
    summaryBox: document.getElementById("summaryBox"),
    recommendations: document.getElementById("recommendations"),
    expandAllBtn: document.getElementById("expandAllBtn"),
    collapseAllBtn: document.getElementById("collapseAllBtn"),
    analysisStatusPill: document.getElementById("analysisStatusPill"),
    analysisStatusText: document.getElementById("analysisStatusText"),
    modelName: document.getElementById("modelName"),
    newAnalysisBtn: document.getElementById("newAnalysisBtn"),
    downloadReportBtn: document.getElementById("downloadReportBtn"),
    openGuideBtn: document.getElementById("openGuideBtn"),
    guideModal: document.getElementById("guideModal"),
    guideBodyStart: document.getElementById("guideBodyStart"),
    guideBodyModal: document.getElementById("guideBodyModal"),
    guideTemplate: document.getElementById("guideTemplate"),
    workspace: document.getElementById("workspace"),
    bgLayer: document.querySelector(".bg-layer"),
  };

  /** @type {{ id: string, file: File, url: string }[]} */
  let selectedFiles = [];
  /** @type {object|null} */
  let lastResult = null;
  let toastTimer = null;
  let stepTimer = null;
  let stepIndex = 0;
  let analyzing = false;
  let allRecommendationsExpanded = false;

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function formatValue(key, value) {
    if (value === null || value === undefined || value === "") return "Не определено";
    if (typeof value === "boolean") return value ? "Да" : "Нет";
    if (key === "confidence" && typeof value === "number") return `${Math.round(value * 100)}%`;
    if (VALUE_LABELS[value] != null) return VALUE_LABELS[value];
    return String(value);
  }

  function setAppState(state) {
    document.body.classList.remove("app--start", "app--loading", "app--results");
    document.body.classList.remove("app-state-start", "app-state-loading", "app-state-results");
    document.body.classList.add(`app--${state}`);

    if (state === "start") {
      els.downloadReportBtn.disabled = true;
      allRecommendationsExpanded = false;
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else if (state === "results") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  function setAnalysisStatus(mode) {
    els.analysisStatusPill.classList.remove("is-done", "is-loading");
    if (mode === "loading") {
      els.analysisStatusPill.classList.add("is-loading");
      els.analysisStatusText.textContent = "Анализ…";
    } else if (mode === "done") {
      els.analysisStatusPill.classList.add("is-done");
      els.analysisStatusText.textContent = "Анализ завершён";
    } else {
      els.analysisStatusText.textContent = "Готов к анализу";
    }
  }

  function showToast(message) {
    els.toast.textContent = message;
    els.toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove("is-visible"), 3200);
  }

  function showAlert(message) {
    els.alert.textContent = message;
    els.alert.classList.add("is-visible");
  }

  function hideAlert() {
    els.alert.classList.remove("is-visible");
    els.alert.textContent = "";
  }

  function getActionCopy(rec, lawnState) {
    const fromMap = ACTION_COPY[rec && rec.id];
    const base = fromMap
      ? {
          ...fromMap,
          warnings: [...(fromMap.warnings || [])],
          prependProducts: [...(fromMap.prependProducts || [])],
          beforeTipNotes: [...(fromMap.beforeTipNotes || [])],
        }
      : {
          icon: "🌿",
          title: (rec && rec.name) || "Рекомендация",
          tip: "Следуйте инструкции на упаковке выбранного средства и учитывайте погоду.",
          productKind: null,
          warnings: [],
          prependProducts: [],
          beforeTipNotes: [],
        };

    const state = lawnState && typeof lawnState === "object" ? lawnState : {};
    if (rec && rec.id === "spot_weed_control" && state.weed_presence === true && state.weed_density === "low") {
      base.title = "Удалите сорняки вручную или точечно";
      if (!base.prependProducts.includes("Ручная прополка")) {
        base.prependProducts = ["Ручная прополка", ...base.prependProducts];
      }
    }
    return base;
  }

  function buildWhyText(rec, lawnState) {
    const state = lawnState && typeof lawnState === "object" ? lawnState : {};
    const id = rec && rec.id;
    if (id === "apply_fertilizer") {
      if (state.pale_grass) return "Трава выглядит бледной и ей не хватает питания.";
      if (state.thin_lawn) return "Газон выглядит редким, подкормка поможет восстановить силу травы.";
      if (state.slow_growth) return "Рост травы замедлен, поэтому полезно восполнить питание.";
      return "По состоянию газона видно, что ему не хватает питания.";
    }
    if (id === "spot_weed_control") {
      if (state.weed_density === "low") {
        return "На фотографии обнаружено небольшое количество сорняков. При низкой плотности предпочтительна ручная прополка. При необходимости можно точечно обработать отдельные растения подходящим гербицидом.";
      }
      return "На фотографии обнаружены отдельные сорняки. При необходимости можно точечно обработать отдельные растения подходящим гербицидом.";
    }
    if (id === "full_weed_control") {
      if (state.weed_density === "high") return "На участке высокая плотность сорняков, нужна обработка всего газона.";
      if (state.weed_density === "medium") return "Сорняки заметны на значительной части участка.";
      return "На газоне обнаружены сорняки, нужна более широкая обработка.";
    }
    if (id === "overseed") {
      if (state.bare_spots && state.thin_lawn) return "Обнаружены проплешины и разреженный газон.";
      if (state.bare_spots) return "Обнаружены проплешины, которые нужно закрыть подсевом.";
      if (state.thin_lawn) return "Газон разрежен и требует подсева для восстановления плотности.";
      return "Обнаружены проплешины или разреженный газон.";
    }
    if (id === "water_increase") return "Газон выглядит пересушенным.";
    if (id === "water_reduce") return "Есть признаки избыточной влаги на участке.";
    if (id === "mow_lawn") return "Газон достиг высоты, при которой рекомендуется кошение.";
    if (id === "apply_fungicide") return "На фото есть признаки грибкового поражения.";
    if (id === "aeration") return "Почва выглядит уплотнённой, корням не хватает воздуха.";
    if (id === "dethatching") return "На газоне накопился слой войлока, мешающий росту.";
    if (id === "improve_drainage") return "На участке возможны проблемы с отводом воды.";
    if (id === "reduce_shade") return "Газону не хватает света для полноценного роста.";
    if (id === "soil_improvement") return "Состояние почвы нужно улучшить для более крепкого газона.";
    if (id === "mowing_adjust") return "Текущий режим стрижки стоит скорректировать.";
    if (rec && rec.description) return rec.description;
    return "По результатам анализа это действие поможет улучшить состояние газона.";
  }

  function isCommercialProduct(item) {
    if (!item || typeof item !== "object") return false;
    if (item.product_type === "commercial_product") return true;
    return typeof item.id === "string" && /_prod_/.test(item.id);
  }

  function formatCategoryPhrase(name) {
    if (!name) return "";
    if (CATEGORY_PHRASES[name]) return CATEGORY_PHRASES[name];
    if (/удобрение$/i.test(name)) return name.replace(/удобрение$/i, "удобрения для газона");
    if (/гербицид$/i.test(name)) return name.replace(/гербицид$/i, "гербициды для газона");
    if (/травосмесь$/i.test(name)) return name.replace(/травосмесь$/i, "травосмеси");
    return name;
  }

  function cleanProductName(name) {
    if (!name) return "";
    return name.replace(/,\s*(ВР|ВДГ|ВРК|СК|КЭ|СП|КС)\s*$/i, "").trim();
  }

  function partitionKnowledgeItems(items, prependProducts) {
    const extras = [];
    const categories = [];
    const products = [];
    (prependProducts || []).forEach((label) => {
      if (label && !extras.includes(label)) extras.push(label);
    });
    if (Array.isArray(items)) {
      items.forEach((item) => {
        if (!item || typeof item !== "object") return;
        const name = typeof item.name === "string" ? item.name.trim() : "";
        if (!name) return;
        if (isCommercialProduct(item)) {
          const productName = cleanProductName(name);
          if (productName && !products.includes(productName)) products.push(productName);
          return;
        }
        const phrase = formatCategoryPhrase(name);
        if (phrase && !categories.includes(phrase)) categories.push(phrase);
      });
    }
    return {
      extras: extras.slice(0, 3),
      categories: categories.slice(0, 4),
      products: products.slice(0, 4),
    };
  }

  function renderBulletList(items, marker) {
    return `<ul>${items
      .map((label) => `<li><span class="check" aria-hidden="true">${marker}</span>${escapeHtml(label)}</li>`)
      .join("")}</ul>`;
  }

  function getProductSectionLabels(productKind) {
    if (productKind === "herbicide") {
      return { main: "Что можно сделать", category: "Если решите использовать гербицид", products: "Подходящие средства" };
    }
    if (productKind === "fertilizer") {
      return { main: "Что использовать", category: "Что использовать", products: "Подходящие удобрения" };
    }
    if (productKind === "seed") {
      return { main: "Что использовать", category: "Что использовать", products: "Подходящие травосмеси" };
    }
    return { main: "Что можно сделать", category: "По типу", products: "Подходящие средства" };
  }

  function renderProducts(items, productKind, prependProducts) {
    const { extras, categories, products } = partitionKnowledgeItems(items, prependProducts);
    if (!extras.length && !categories.length && !products.length) return "";
    const labels = getProductSectionLabels(productKind);
    const bothGroups = categories.length > 0 && products.length > 0;
    let body = "";
    if (extras.length) body += renderBulletList(extras, "✓");
    if (bothGroups) {
      if (productKind === "herbicide") {
        body += `<div><strong>${escapeHtml(labels.category)}</strong></div>`;
        body += renderBulletList(categories, "•");
      } else {
        body += renderBulletList(categories, "•");
      }
      body += `<div><strong>${escapeHtml(labels.products)}</strong></div>`;
      body += renderBulletList(products, "✓");
    } else if (categories.length) {
      body += renderBulletList(categories, "•");
    } else if (products.length) {
      if (extras.length) body += `<div><strong>${escapeHtml(labels.products)}</strong></div>`;
      body += renderBulletList(products, "✓");
    }
    return `<div class="rec-products"><h4>${escapeHtml(labels.main)}</h4>${body}</div>`;
  }

  function renderBeforeTipNotes(notes) {
    if (!Array.isArray(notes) || !notes.length) return "";
    return `<div class="rec-warning"><div class="rec-warning-label">⚠️ Важно</div>${notes
      .map((text) => `<p>${escapeHtml(text)}</p>`).join("")}</div>`;
  }

  function renderWarnings(warnings) {
    if (!Array.isArray(warnings) || !warnings.length) return "";
    return `<div class="rec-warning"><div class="rec-warning-label">⚠️ Важно</div>${warnings
      .map((text) => `<p>${escapeHtml(text)}</p>`).join("")}</div>`;
  }

  function buildSummary(finalState) {
    const s = finalState || {};
    const parts = [];
    if (s.dryness && s.thin_lawn) parts.push("Газон выглядит пересушенным и разреженным");
    else if (s.dryness) parts.push("Газон выглядит пересушенным");
    else if (s.thin_lawn) parts.push("Газон выглядит разреженным");
    if (s.pale_grass) parts.push("трава бледная");
    if (s.bare_spots) parts.push("есть проплешины");
    if (s.weed_presence) {
      if (s.weed_density === "low") parts.push("обнаружено небольшое количество сорняков");
      else if (s.weed_density === "medium") parts.push("сорняки заметны на части участка");
      else if (s.weed_density === "high") parts.push("высокая плотность сорняков");
      else parts.push("обнаружены сорняки");
    }
    if (s.needs_mowing) parts.push("требуется кошение");
    if (s.moss_presence) parts.push("есть признаки мха");
    if (s.fungal_signs) parts.push("есть признаки грибка");
    const negatives = [];
    if (!s.fungal_signs) negatives.push("грибка");
    if (!s.moss_presence) negatives.push("мха");
    if (negatives.length === 2) parts.push(`признаков ${negatives.join(" и ")} не найдено`);
    else if (negatives.length === 1 && (s.dryness || s.weed_presence || s.thin_lawn)) {
      parts.push(`признаков ${negatives[0]} не найдено`);
    }
    if (!parts.length) {
      return "По текущим снимкам серьёзных проблем не выявлено. Газон выглядит в целом стабильно.";
    }
    let text = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
    for (let i = 1; i < parts.length; i += 1) {
      const chunk = parts[i].charAt(0).toUpperCase() + parts[i].slice(1);
      text += i === parts.length - 1 ? `. ${chunk}.` : `. ${chunk}`;
    }
    if (!text.endsWith(".")) text += ".";
    return text.replace(/\.\./g, ".");
  }

  function chipTone(key, value) {
    if (key === "confidence" || key === "weed_type" || key === "soil_issue") return "is-info";
    if (key === "weed_density") {
      if (value === "high") return "is-bad";
      if (value === "medium" || value === "low") return "is-warn";
      return "is-info";
    }
    if (PROBLEM_TRUE_KEYS.has(key)) {
      if (value === true) return key === "needs_mowing" || key === "pale_grass" ? "is-warn" : "is-bad";
      if (value === false) return "is-ok";
    }
    if (value === true) return "is-warn";
    if (value === false) return "is-ok";
    return "is-info";
  }

  function renderState(finalState) {
    els.summaryBox.textContent = buildSummary(finalState);
    const keys = [
      ...STATE_ORDER.filter((key) => key in finalState),
      ...Object.keys(finalState).filter((key) => !STATE_ORDER.includes(key)),
    ];

    const mainKeys = keys.filter((key) => key !== "soil_issue" && key !== "confidence");
    const analysisKeys = keys.filter((key) => key === "soil_issue" || key === "confidence");

    const chipHtml = (key) => {
      const value = finalState[key];
      return `<div class="state-chip ${chipTone(key, value)}">
        <div class="state-chip-head">
          <span class="state-chip-dot" aria-hidden="true"></span>
          <span class="label">${escapeHtml(STATE_LABELS[key] || key)}</span>
        </div>
        <span class="value">${escapeHtml(formatValue(key, value))}</span>
      </div>`;
    };

    els.stateGrid.innerHTML = [
      ...mainKeys.map(chipHtml),
      analysisKeys.length ? '<div class="state-grid-subhead">Результаты анализа</div>' : "",
      ...analysisKeys.map(chipHtml),
    ].filter(Boolean).join("");
  }

  function priorityRank(id) {
    const idx = PRIORITY_IDS.indexOf(id);
    return idx === -1 ? 100 : idx;
  }

  function renderRecommendations(recommendations, lawnState) {
    if (!Array.isArray(recommendations) || !recommendations.length) {
      els.recommendations.innerHTML =
        '<p class="panel-empty" style="margin:0">Специальных рекомендаций нет — газон в хорошем состоянии.</p>';
      return;
    }

    const sorted = [...recommendations].sort(
      (a, b) => priorityRank(a && a.id) - priorityRank(b && b.id)
    );

    allRecommendationsExpanded = false;

    els.recommendations.innerHTML = sorted
      .map((rec, index) => {
        if (!rec || typeof rec !== "object") return "";
        const copy = getActionCopy(rec, lawnState);
        const why = buildWhyText(rec, lawnState);
        const products = renderProducts(rec.knowledge_items, copy.productKind, copy.prependProducts);
        const beforeTip = renderBeforeTipNotes(copy.beforeTipNotes);
        const warnings = renderWarnings(copy.warnings);
        const isOpen = index === 0;

        return `
          <article class="rec-item ${isOpen ? "is-open" : ""}" data-rec-id="${escapeHtml(rec.id || String(index))}">
            <button type="button" class="rec-item-toggle" aria-expanded="${isOpen}">
              <span class="rec-icon" aria-hidden="true">${copy.icon}</span>
              <span class="rec-head-text">
                <h3>${escapeHtml(copy.title)}</h3>
                <p>${escapeHtml(why)}</p>
              </span>
              <span class="rec-chevron" aria-hidden="true">▾</span>
            </button>
            <div class="rec-body">
              ${products}
              ${beforeTip}
              <div class="rec-tip">
                <div class="rec-tip-label">💡 Совет</div>
                <p>${escapeHtml(copy.tip)}</p>
              </div>
              ${warnings}
            </div>
          </article>`;
      })
      .filter(Boolean)
      .join("");
  }

  function getOpenRecItems() {
    return Array.from(els.recommendations.querySelectorAll(".rec-item.is-open"));
  }

  function setItemOpen(item, open) {
    item.classList.toggle("is-open", open);
    const btn = item.querySelector(".rec-item-toggle");
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function setRecsExpanded(expanded) {
    allRecommendationsExpanded = expanded;
    const items = Array.from(els.recommendations.querySelectorAll(".rec-item"));
    items.forEach((item) => setItemOpen(item, expanded));
    if (expanded) {
      els.recommendations.scrollTop = 0;
    }
  }

  function expandAllRecommendations() {
    setRecsExpanded(true);
  }

  function collapseAllRecommendations() {
    setRecsExpanded(false);
  }

  function isValidCount() {
    return selectedFiles.length >= MIN_FILES && selectedFiles.length <= MAX_FILES;
  }

  function startLoadingSteps() {
    stepIndex = 0;
    els.loadingStep.textContent = LOADING_STEPS[0];
    clearInterval(stepTimer);
    stepTimer = setInterval(() => {
      stepIndex = (stepIndex + 1) % LOADING_STEPS.length;
      els.loadingStep.style.opacity = "0";
      setTimeout(() => {
        els.loadingStep.textContent = LOADING_STEPS[stepIndex];
        els.loadingStep.style.opacity = "1";
      }, 160);
    }, 1600);
  }

  function stopLoadingSteps() {
    clearInterval(stepTimer);
    stepTimer = null;
  }

  function setLoading(isLoading) {
    analyzing = isLoading;
    els.loadingOverlay.hidden = !isLoading;
    els.analyzeBtn.disabled = isLoading || !isValidCount();
    els.clearBtn.disabled = isLoading;
    els.dropzone.style.pointerEvents = isLoading ? "none" : "";
    if (isLoading) {
      document.body.classList.add("app--loading");
      setAnalysisStatus("loading");
      startLoadingSteps();
    } else {
      document.body.classList.remove("app--loading");
      stopLoadingSteps();
    }
  }

  function previewHtml() {
    return selectedFiles
      .map(
        (item) => `
        <div class="preview-card">
          <img src="${escapeHtml(item.url)}" alt="Фото газона">
          <button class="remove-btn" type="button" data-remove="${escapeHtml(item.id)}" aria-label="Удалить фото">×</button>
        </div>`
      )
      .join("");
  }

  function renderPreviews() {
    const html = selectedFiles.length ? previewHtml() : "";
    els.previews.innerHTML = html;
    if (els.previewsCompact) {
      els.previewsCompact.innerHTML = selectedFiles.length
        ? selectedFiles
            .map(
              (item) => `
              <div class="preview-card">
                <img src="${escapeHtml(item.url)}" alt="Фото газона">
              </div>`
            )
            .join("")
        : "";
    }
  }

  function updateUiState() {
    els.counter.textContent = String(selectedFiles.length);
    els.analyzeBtn.disabled = analyzing || !isValidCount();
    renderPreviews();
  }

  function revokeUrls() {
    selectedFiles.forEach((item) => URL.revokeObjectURL(item.url));
  }

  function resetToStart() {
    revokeUrls();
    selectedFiles = [];
    lastResult = null;
    els.fileInput.value = "";
    hideAlert();
    els.recommendations.innerHTML = "";
    els.stateGrid.innerHTML = "";
    els.summaryBox.textContent = "";
    setAppState("start");
    setAnalysisStatus("ready");
    updateUiState();
  }

  function addFiles(fileList) {
    hideAlert();
    const incoming = Array.from(fileList || []).filter(
      (file) => file.type.startsWith("image/")
    );
    if (!incoming.length) {
      showAlert("Выберите изображения JPG или PNG.");
      return;
    }
    const room = MAX_FILES - selectedFiles.length;
    if (room <= 0) {
      showAlert("Можно загрузить не больше 5 фотографий.");
      return;
    }
    incoming.slice(0, room).forEach((file) => {
      selectedFiles.push({
        id: `${file.name}-${file.size}-${file.lastModified}-${Math.random()}`,
        file,
        url: URL.createObjectURL(file),
      });
    });
    if (incoming.length > room) {
      showAlert("Добавлены только первые доступные фотографии. Максимум — 5.");
    }
    updateUiState();
  }

  function removeFile(id) {
    const index = selectedFiles.findIndex((item) => item.id === id);
    if (index === -1) return;
    URL.revokeObjectURL(selectedFiles[index].url);
    selectedFiles.splice(index, 1);
    hideAlert();
    updateUiState();
  }

  function downloadReport() {
    if (!lastResult || !lastResult.final_state) {
      showAlert("Сначала выполните анализ, чтобы скачать отчёт.");
      return;
    }
    const state = lastResult.final_state;
    const recs = Array.isArray(lastResult.recommendations) ? lastResult.recommendations : [];
    const lines = [
      "GreenScan — отчёт по состоянию газона",
      `Дата: ${new Date().toLocaleString("ru-RU")}`,
      `Модель: ${MODEL_LABEL}`,
      "",
      "Краткое резюме",
      buildSummary(state),
      "",
      "Диагноз",
    ];
    Object.keys(state).forEach((key) => {
      lines.push(`- ${STATE_LABELS[key] || key}: ${formatValue(key, state[key])}`);
    });
    lines.push("", "Рекомендации");
    recs.forEach((rec, i) => {
      const copy = getActionCopy(rec, state);
      lines.push(`${i + 1}. ${copy.title}`);
      lines.push(`   ${buildWhyText(rec, state)}`);
      const parts = partitionKnowledgeItems(rec.knowledge_items, copy.prependProducts);
      parts.extras.forEach((x) => lines.push(`   • ${x}`));
      parts.categories.forEach((x) => lines.push(`   • ${x}`));
      parts.products.forEach((x) => lines.push(`   ✓ ${x}`));
      (copy.beforeTipNotes || []).forEach((n) => lines.push(`   Важно: ${n}`));
      lines.push(`   Совет: ${copy.tip}`);
      (copy.warnings || []).forEach((w) => lines.push(`   Важно: ${w}`));
      lines.push("");
    });

    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `greenscan-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast("Отчёт скачан");
  }

  async function analyze() {
    hideAlert();
    if (analyzing) return;
    if (!isValidCount()) {
      showAlert("Выберите от 2 до 5 фотографий газона.");
      return;
    }

    const formData = new FormData();
    selectedFiles.forEach((item) => formData.append("files", item.file));
    setLoading(true);

    let response;
    try {
      response = await fetch(API_URL, { method: "POST", body: formData });
    } catch (_error) {
      setLoading(false);
      setAnalysisStatus("ready");
      showAlert("Не удалось выполнить анализ. Попробуйте ещё раз позже.");
      return;
    }

    let data;
    try {
      data = await response.json();
    } catch (_error) {
      setLoading(false);
      setAnalysisStatus("ready");
      showAlert("Не удалось выполнить анализ. Попробуйте ещё раз позже.");
      return;
    }

    setLoading(false);

    if (!response.ok || (data && data.error) || !data || !data.final_state) {
      setAnalysisStatus("ready");
      const detail = data && (data.detail || data.error);
      showAlert(
        typeof detail === "string" && detail.trim()
          ? detail
          : "Не удалось выполнить анализ. Попробуйте ещё раз позже."
      );
      return;
    }

    lastResult = data;
    els.downloadReportBtn.disabled = false;
    setAppState("results");
    setAnalysisStatus("done");
    renderPreviews();
    renderState(data.final_state);
    renderRecommendations(data.recommendations, data.final_state);
    showToast("Анализ успешно завершён");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function mountGuideContent(target) {
    const tpl = els.guideTemplate.content.cloneNode(true);
    target.innerHTML = "";
    target.appendChild(tpl);
    const imgWrap = target.querySelector("[data-guide-image]");
    const cssWrap = target.querySelector("[data-guide-css]");
    const img = target.querySelector(".guide-image");
    if (!img || !imgWrap || !cssWrap) return;
    img.onload = () => {
      imgWrap.hidden = false;
      cssWrap.hidden = true;
    };
    img.onerror = () => {
      imgWrap.hidden = true;
      cssWrap.hidden = false;
    };
    const src = img.getAttribute("src");
    img.src = "";
    img.src = src;
  }

  function openGuideModal() {
    els.guideModal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeGuideModal() {
    els.guideModal.hidden = true;
    document.body.style.overflow = "";
  }

  function probeBackground() {
    const img = new Image();
    img.onload = () => els.bgLayer && els.bgLayer.classList.add("has-image");
    img.onerror = () => els.bgLayer && els.bgLayer.classList.remove("has-image");
    img.src = "FRONTEND/assets/grass-background.webp";
  }

  function bindEvents() {
    els.modelName.textContent = MODEL_LABEL;

    els.dropzone.addEventListener("click", () => els.fileInput.click());
    els.dropzone.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        els.fileInput.click();
      }
    });

    els.fileInput.addEventListener("change", (event) => {
      addFiles(event.target.files);
      els.fileInput.value = "";
    });

    ["dragenter", "dragover"].forEach((name) => {
      els.dropzone.addEventListener(name, (event) => {
        event.preventDefault();
        event.stopPropagation();
        els.dropzone.classList.add("is-dragover");
      });
    });
    ["dragleave", "drop"].forEach((name) => {
      els.dropzone.addEventListener(name, (event) => {
        event.preventDefault();
        event.stopPropagation();
        els.dropzone.classList.remove("is-dragover");
      });
    });
    els.dropzone.addEventListener("drop", (event) => {
      addFiles(event.dataTransfer && event.dataTransfer.files);
    });

    els.previews.addEventListener("click", (event) => {
      const button = event.target.closest("[data-remove]");
      if (!button) return;
      removeFile(button.getAttribute("data-remove"));
    });

    els.recommendations.addEventListener("click", (event) => {
      const toggle = event.target.closest(".rec-item-toggle");
      if (!toggle) return;
      const item = toggle.closest(".rec-item");
      if (!item) return;
      const willOpen = !item.classList.contains("is-open");

      if (allRecommendationsExpanded) {
        // После «Показать все» одиночный клик выходит из режима и работает как accordion
        allRecommendationsExpanded = false;
        getOpenRecItems().forEach((openItem) => {
          if (openItem !== item) setItemOpen(openItem, false);
        });
        setItemOpen(item, willOpen);
        return;
      }

      // Одновременно открыта максимум одна карточка
      getOpenRecItems().forEach((openItem) => {
        if (openItem !== item) setItemOpen(openItem, false);
      });
      setItemOpen(item, willOpen);
    });

    els.expandAllBtn.addEventListener("click", expandAllRecommendations);
    els.collapseAllBtn.addEventListener("click", collapseAllRecommendations);
    els.analyzeBtn.addEventListener("click", analyze);
    els.clearBtn.addEventListener("click", () => {
      if (analyzing) return;
      resetToStart();
    });
    els.newAnalysisBtn.addEventListener("click", () => {
      resetToStart();
      showToast("Готово к новому анализу");
    });
    els.downloadReportBtn.addEventListener("click", downloadReport);
    els.openGuideBtn.addEventListener("click", openGuideModal);

    els.guideModal.addEventListener("click", (event) => {
      if (event.target.closest("[data-close-modal]")) closeGuideModal();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !els.guideModal.hidden) closeGuideModal();
    });
  }

  mountGuideContent(els.guideBodyStart);
  mountGuideContent(els.guideBodyModal);
  bindEvents();
  probeBackground();
  setAppState("start");
  setAnalysisStatus("ready");
  updateUiState();
})();
