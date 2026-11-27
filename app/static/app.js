(() => {
  let fxRate = 3.481;
  let sampleCustomers = [];
  let cart = [];
  let usedReco = false;
  let contextData = null;
  let activeProduct = null;
  let activeCategory = "";
  let auditMode = false;
  let projectionChart = null;
  let lastDetailRecos = [];
  let lastCartRecos = [];
  const apiLogs = [];

  const fxBadge = document.getElementById("fxBadge");
  const holidayBadge = document.getElementById("holidayBadge");
  const searchForm = document.getElementById("searchForm");
  const searchInput = document.getElementById("searchInput");
  const categorySelect = document.getElementById("categorySelect");
  const categoryChips = document.getElementById("categoryChips");
  const productGrid = document.getElementById("productGrid");
  const catalogCount = document.getElementById("catalogCount");
  const catalogHeading = document.getElementById("catalogHeading");
  const searchSuggestionBanner = document.getElementById("searchSuggestionBanner");

  const auditToggleBtn = document.getElementById("auditToggleBtn");
  const auditToggleLabel = document.getElementById("auditToggleLabel");
  const auditContextBar = document.getElementById("auditContextBar");

  const storeCatalogView = document.getElementById("storeCatalogView");
  const productDetailView = document.getElementById("productDetailView");

  const cartCustomerSelect = document.getElementById("cartCustomerSelect");
  const cartBadgeCount = document.getElementById("cartBadgeCount");
  const drawerCount = document.getElementById("drawerCount");
  const cartItemsList = document.getElementById("cartItemsList");
  const recoList = document.getElementById("recoList");
  const recoModeBadge = document.getElementById("recoModeBadge");
  const totalUsdEl = document.getElementById("totalUsd");
  const totalPenEl = document.getElementById("totalPen");
  const checkoutBtn = document.getElementById("checkoutBtn");
  const checkoutFeedback = document.getElementById("checkoutFeedback");

  const cartDrawer = document.getElementById("cartDrawer");
  const cartBackdrop = document.getElementById("cartBackdrop");
  const toastEl = document.getElementById("toastNotice");
  const siteHeader = document.querySelector(".site-header");

  // Header inteligente en móviles: se oculta al bajar (rápido o lento) y reaparece al subir
  let lastScrollY = window.scrollY || 0;
  let scrollAcc = 0;
  let scrollTicking = false;
  window.addEventListener(
    "scroll",
    () => {
      if (scrollTicking) return;
      scrollTicking = true;
      window.requestAnimationFrame(() => {
        const y = Math.max(0, window.scrollY || window.pageYOffset || 0);
        const dy = y - lastScrollY;
        lastScrollY = y;

        if (window.innerWidth > 860 || !siteHeader) {
          siteHeader?.classList.remove("nav-hidden");
          scrollAcc = 0;
          scrollTicking = false;
          return;
        }

        scrollAcc = (dy > 0 && scrollAcc < 0) || (dy < 0 && scrollAcc > 0) ? dy : scrollAcc + dy;
        const headerH = siteHeader.offsetHeight || 160;
        const activeTag = document.activeElement?.tagName;
        const headerTyping = siteHeader.contains(document.activeElement) && (activeTag === "INPUT" || activeTag === "SELECT");
        const drawerOpen = cartDrawer && !cartDrawer.hidden;

        if (y <= 32 || headerTyping || drawerOpen) {
          siteHeader.classList.remove("nav-hidden");
          scrollAcc = 0;
        } else if (scrollAcc > 14 && y > headerH) {
          siteHeader.classList.add("nav-hidden");
          scrollAcc = 0;
        } else if (scrollAcc < -12) {
          siteHeader.classList.remove("nav-hidden");
          scrollAcc = 0;
        }
        scrollTicking = false;
      });
    },
    { passive: true }
  );

  window.addEventListener("resize", () => {
    if (window.innerWidth > 860) siteHeader?.classList.remove("nav-hidden");
  });

  function logApiCall(endpoint, purpose, summary) {
    const now = new Date().toLocaleTimeString("es-PE", { hour12: false });
    apiLogs.unshift({ time: now, endpoint, purpose, summary });
    if (apiLogs.length > 25) apiLogs.pop();
    const tbody = document.getElementById("apiLogBody");
    if (tbody) {
      tbody.innerHTML = apiLogs
        .map(
          (l) => `
        <tr>
          <td><code>${l.time}</code></td>
          <td><strong>${l.endpoint}</strong></td>
          <td>${l.purpose}</td>
          <td>${l.summary}</td>
        </tr>`
        )
        .join("");
    }
  }

  const CAT_THEME = {
    "Cocina y Mesa": { bg: "#fff7ed", fg: "#c2410c", accent: "#fdba74" },
    "Hogar y Decoración": { bg: "#f0fdf4", fg: "#15803d", accent: "#86efac" },
    "Bolsos y Viaje": { bg: "#eff6ff", fg: "#1d4ed8", accent: "#93c5fd" },
    "Oficina y Papelería": { bg: "#f5f3ff", fg: "#6d28d9", accent: "#c4b5fd" },
    "Regalos y Eventos": { bg: "#fdf2f8", fg: "#be185d", accent: "#f9a8d4" },
    "Accesorios y Varios": { bg: "#f0f9ff", fg: "#0369a1", accent: "#7dd3fc" }
  };

  function getProductSvg(prod) {
    const desc = (prod.description || "").toLowerCase();
    const theme = CAT_THEME[prod.category] || { bg: "#f8fafc", fg: "#334155", accent: "#cbd5e1" };
    let glyph = `<rect x="26" y="28" width="44" height="42" rx="8" fill="${theme.accent}" stroke="${theme.fg}" stroke-width="3"/><path d="M26 42h44M48 28v42" stroke="${theme.fg}" stroke-width="2.8"/>`;
    if (desc.includes("teacup") || desc.includes("mug") || desc.includes("cake") || desc.includes("tin")) {
      glyph = `<path d="M24 38h36v18a14 14 0 0 1-14 14h-8a14 14 0 0 1-14-14V38z" fill="${theme.accent}" stroke="${theme.fg}" stroke-width="3"/><path d="M60 42h7a6 6 0 0 1 0 12h-7" fill="none" stroke="${theme.fg}" stroke-width="3"/><path d="M20 74h44" stroke="${theme.fg}" stroke-width="3.2" stroke-linecap="round"/>`;
    } else if (desc.includes("bag") || desc.includes("tote") || desc.includes("box")) {
      glyph = `<path d="M26 36h44l-4 36H30l-4-36z" fill="${theme.accent}" stroke="${theme.fg}" stroke-width="3" stroke-linejoin="round"/><path d="M36 36v-6a12 12 0 0 1 24 0v6" fill="none" stroke="${theme.fg}" stroke-width="3"/>`;
    } else if (desc.includes("heart") || desc.includes("love") || desc.includes("bunting")) {
      glyph = `<path d="M48 72S22 55 22 37a14 14 0 0 1 26-7 14 14 0 0 1 26 7c0 18-26 35-26 35z" fill="${theme.accent}" stroke="${theme.fg}" stroke-width="3" stroke-linejoin="round"/>`;
    } else if (desc.includes("light") || desc.includes("lantern") || desc.includes("candle") || desc.includes("holder")) {
      glyph = `<rect x="30" y="30" width="36" height="40" rx="6" fill="${theme.accent}" stroke="${theme.fg}" stroke-width="3"/><path d="M48 20v10M48 42c4 5 4 11 0 14-4-3-4-9 0-14z" fill="#fbbf24" stroke="${theme.fg}" stroke-width="2.5"/>`;
    } else if (desc.includes("clock") || desc.includes("watch") || desc.includes("alarm")) {
      glyph = `<circle cx="48" cy="49" r="22" fill="${theme.accent}" stroke="${theme.fg}" stroke-width="3"/><path d="M48 36v14l9 6" fill="none" stroke="${theme.fg}" stroke-width="3" stroke-linecap="round"/>`;
    }
    return `<svg viewBox="0 0 96 96" aria-hidden="true"><rect x="4" y="4" width="88" height="88" rx="18" fill="${theme.bg}"/>${glyph}</svg>`;
  }

  function showToast(msg) {
    toastEl.textContent = msg;
    toastEl.hidden = false;
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => {
      toastEl.hidden = true;
    }, 2400);
  }

  // Switch Modo Auditoría IA (separa vista limpia de cliente vs explicación interna)
  function applyAuditVisibility() {
    auditToggleBtn.classList.toggle("active", auditMode);
    auditToggleBtn.setAttribute("aria-pressed", String(auditMode));
    auditToggleLabel.textContent = auditMode ? "Modo Auditoría IA: ON" : "Modo Auditoría IA: OFF";
    auditContextBar.hidden = !auditMode;

    const detailBadge = document.getElementById("detailRecoMode");
    const detailExp = document.getElementById("detailAuditExplainer");
    if (detailBadge) detailBadge.hidden = !auditMode;
    if (detailExp) detailExp.hidden = !auditMode;
    if (recoModeBadge) recoModeBadge.hidden = !auditMode;

    if (activeProduct) renderDetailRecommendations(activeProduct, lastDetailRecos);
    renderCartRecommendations(lastCartRecos);
  }

  auditToggleBtn.addEventListener("click", () => {
    auditMode = !auditMode;
    applyAuditVisibility();
    showToast(
      auditMode
        ? "Modo Auditoría IA activado: ahora ves fórmulas, APIs y aporte al negocio."
        : "Vista Cliente normal restaurada."
    );
  });

  function switchTab(tabName) {
    document.querySelectorAll(".nav-tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tabName));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${tabName}`));
    if (tabName === "gerencia") {
      loadInvoices();
      renderManagementView();
    }
  }

  document.querySelectorAll(".nav-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.dataset.tab === "tienda") showCatalogView();
      switchTab(btn.dataset.tab);
    });
  });

  document.getElementById("brandLogoBtn").addEventListener("click", () => {
    activeCategory = "";
    searchInput.value = "";
    categorySelect.value = "";
    syncCategoryChips();
    showCatalogView();
    switchTab("tienda");
    loadProducts();
  });

  function openCartDrawer() {
    cartDrawer.hidden = false;
    cartBackdrop.hidden = false;
  }

  function closeCartDrawer() {
    cartDrawer.hidden = true;
    cartBackdrop.hidden = true;
  }

  document.getElementById("openCartBtn").addEventListener("click", openCartDrawer);
  document.getElementById("closeCartBtn").addEventListener("click", closeCartDrawer);
  cartBackdrop.addEventListener("click", closeCartDrawer);

  function showCatalogView() {
    productDetailView.hidden = true;
    storeCatalogView.hidden = false;
  }

  document.getElementById("backToCatalogBtn").addEventListener("click", showCatalogView);

  function syncCategoryChips() {
    document.querySelectorAll(".sub-chip").forEach((ch) => {
      ch.classList.toggle("active", ch.dataset.cat === activeCategory);
    });
  }

  async function initContext() {
    const resp = await fetch("/api/context");
    contextData = await resp.json();
    const ext = contextData.external;
    fxRate = Number(ext.usd_to_pen || 3.481);

    logApiCall("GET /api/context + APIs Externas", "Cargar tipo de cambio USD→PEN, feriados de Perú y analítica base", `USD/PEN = ${fxRate.toFixed(3)} (${ext.fx_source})`);

    fxBadge.textContent = `1 USD = S/ ${fxRate.toFixed(3)}`;
    holidayBadge.textContent = ext.is_holiday
      ? `Feriado hoy: ${ext.holiday_name}`
      : `Próx. feriado: ${ext.next_holiday}`;

    categoryChips.innerHTML = `<button type="button" class="sub-chip active" data-cat="">Todas</button>`;
    contextData.categories.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      categorySelect.appendChild(opt);

      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "sub-chip";
      chip.dataset.cat = c;
      chip.textContent = c;
      categoryChips.appendChild(chip);
    });

    categoryChips.querySelectorAll(".sub-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        activeCategory = chip.dataset.cat;
        categorySelect.value = activeCategory;
        syncCategoryChips();
        showCatalogView();
        switchTab("tienda");
        loadProducts();
      });
    });

    sampleCustomers = contextData.sample_customers || [];
    cartCustomerSelect.innerHTML = "";
    sampleCustomers.forEach((c, idx) => {
      const opt = document.createElement("option");
      opt.value = idx;
      opt.textContent = `CLI-${c.CustomerID} · ${c.segmento}`;
      cartCustomerSelect.appendChild(opt);
    });

    const presetRoot = document.getElementById("presetCustChips");
    const seenSeg = new Set();
    sampleCustomers.forEach((c) => {
      if (seenSeg.has(c.segmento)) return;
      seenSeg.add(c.segmento);
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip-cust";
      b.textContent = `${c.segmento} (#${c.CustomerID})`;
      b.addEventListener("click", () => {
        document.getElementById("fRecency").value = c.recency_days;
        document.getElementById("fFreq").value = c.frequency;
        document.getElementById("fMonetary").value = c.monetary;
        document.getElementById("fItems").value = c.total_items;
        document.getElementById("fUnique").value = c.unique_products;
        document.getElementById("fTenure").value = c.tenure_days;
        document.getElementById("fCancels").value = c.cancellation_count;
        document.getElementById("fMarket").value = c.is_uk;
        runCustomerPrediction();
      });
      presetRoot.appendChild(b);
    });

    if (sampleCustomers.length) {
      scoreSelectedCartCustomer(0);
      runCustomerPrediction();
    }

    // KPIs Gerencia
    if (contextData.eda && contextData.metrics) {
      document.getElementById("kpiCatalogSkus").textContent = `${contextData.catalog_summary.active_skus} / ${Number(contextData.eda.unique_products).toLocaleString()}`;
      document.getElementById("kpiTotalRevenue").textContent = `$${(Number(contextData.eda.total_revenue) / 1e6).toFixed(2)}M`;
      document.getElementById("kpiRules").textContent = Number(contextData.metrics.association_rules_count).toLocaleString();
    }
  }

  async function scoreSelectedCartCustomer(idx) {
    const c = sampleCustomers[idx];
    if (!c) return;
    const resp = await fetch("/api/predict-customer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: c.CustomerID,
        recency_days: c.recency_days,
        frequency: c.frequency,
        monetary: c.monetary,
        total_items: c.total_items,
        unique_products: c.unique_products,
        tenure_days: c.tenure_days,
        cancellation_count: c.cancellation_count,
        is_uk: c.is_uk
      })
    });
    const out = await resp.json();
    const segBadge = document.getElementById("cartCustSeg");
    segBadge.textContent = out.segmento_rfm;
    segBadge.classList.toggle("risk", out.prediccion_recompra === 0);
    document.getElementById("cartCustProb").textContent = `${(out.probabilidad_recompra * 100).toFixed(1)} %`;
    document.getElementById("cartCustAction").textContent = out.accion_comercial;
  }

  cartCustomerSelect.addEventListener("change", (e) => {
    scoreSelectedCartCustomer(Number(e.target.value));
  });

  // ==================== BUSCADOR REAL (SOLO CON ENTER O BOTÓN) ====================
  async function loadProducts() {
    const q = searchInput.value.trim();
    const cat = categorySelect.value;
    activeCategory = cat;
    syncCategoryChips();

    const resp = await fetch(`/api/products?q=${encodeURIComponent(q)}&category=${encodeURIComponent(cat)}&limit=28`);
    const data = await resp.json();

    if (q) {
      logApiCall("GET /api/products", `Buscar "${q}" (modo: ${data.match_mode})`, `${data.total} resultado(s)`);
    }

    searchSuggestionBanner.hidden = true;
    let listToShow = data.products || [];

    if (data.match_mode === "aproximado" && data.suggestion) {
      searchSuggestionBanner.hidden = false;
      searchSuggestionBanner.innerHTML = `No hubo coincidencia exacta para "<strong>${q}</strong>". ¿Quisiste decir <strong>"${data.suggestion}"</strong>? Mostrando ${listToShow.length} productos similares.`;
    } else if (data.match_mode === "sinonimo_es" && data.suggestion) {
      searchSuggestionBanner.hidden = false;
      searchSuggestionBanner.innerHTML = `Traducción inteligente activada (<strong>${data.suggestion}</strong>): encontramos ${data.total} producto(s) reales del catálogo.`;
    } else if (data.match_mode === "promocion_alternativa") {
      searchSuggestionBanner.hidden = false;
      searchSuggestionBanner.innerHTML = `No encontramos coincidencia directa para "<strong>${q}</strong>", pero como tienda te promocionamos los artículos más buscados en esta categoría:`;
      listToShow = data.fallback_products || [];
    }

    catalogHeading.textContent = q
      ? `Resultados para "${q}"`
      : cat
        ? `Categoría: ${cat}`
        : "Productos destacados en NovaMarket Perú";
    catalogCount.textContent =
      data.total > 0
        ? `Mostrando ${listToShow.length} de ${data.total} productos disponibles`
        : `Mostrando ${listToShow.length} productos promocionados`;

    productGrid.innerHTML = "";
    listToShow.forEach((p, idx) => {
      const card = document.createElement("article");
      card.className = "prod-card";
      const pen = (p.price_usd * fxRate).toFixed(2);
      const badge = idx < 3 && !q ? `<span class="prod-badge-top">Más vendido</span>` : "";

      card.innerHTML = `
        <div class="prod-thumb" role="button" tabindex="0">
          ${badge}
          ${getProductSvg(p)}
        </div>
        <span class="prod-cat">${p.category}</span>
        <h2 class="prod-title">${p.description}</h2>
        <div class="prod-rating">
          <span class="stars">★★★★★</span>
          <span>(${p.invoice_count.toLocaleString()} compras)</span>
        </div>
        <div class="prod-price-block">
          <div class="prod-price-pen">S/ ${pen}</div>
          <div class="prod-price-usd">$${p.price_usd.toFixed(2)} USD · SKU #${p.stock_code}</div>
        </div>
        <div class="prod-actions">
          <button type="button" class="btn-outline btn-detail">Ver detalle</button>
          <button type="button" class="btn-amazon-amber btn-add">+ Agregar</button>
        </div>
      `;

      card.querySelector(".prod-thumb").addEventListener("click", () => openProductDetail(p));
      card.querySelector(".prod-title").addEventListener("click", () => openProductDetail(p));
      card.querySelector(".btn-detail").addEventListener("click", () => openProductDetail(p));
      card.querySelector(".btn-add").addEventListener("click", () => {
        addToCart(p, 1, false);
        showToast(`Agregado al carrito: ${p.description}`);
      });

      productGrid.appendChild(card);
    });
  }

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    showCatalogView();
    switchTab("tienda");
    loadProducts();
  });

  // Limpiar búsqueda solo si el usuario borra todo y limpia con la X
  searchInput.addEventListener("search", () => {
    if (!searchInput.value.trim()) {
      showCatalogView();
      switchTab("tienda");
      loadProducts();
    }
  });

  categorySelect.addEventListener("change", () => {
    showCatalogView();
    switchTab("tienda");
    loadProducts();
  });

  // ==================== DETALLE DEL PRODUCTO + RECOMENDACIONES ABAJO ====================
  function renderDetailRecommendations(prod, items) {
    const recoGrid = document.getElementById("detailRecoGrid");
    const recoMode = document.getElementById("detailRecoMode");
    const recoSub = document.getElementById("detailRecoSub");
    const explainer = document.getElementById("detailAuditExplainer");

    const rulesCount = items.filter((r) => r.match_type === "regla_asociacion").length;
    recoMode.textContent = rulesCount > 0 ? `${rulesCount} Regla(s) + Respaldo Comercial` : "Promoción por Categoría y Top Ventas";
    recoSub.textContent = auditMode
      ? `Motor 1 ordena primero productos con mayor Confianza × Lift y completa hasta 4 tarjetas para promocionar siempre.`
      : `Complementos recomendados para acompañar "${prod.description}"`;

    if (auditMode) {
      const topRule = items.find((r) => r.match_type === "regla_asociacion");
      if (topRule) {
        const extraPen = (topRule.consequent_price_usd * fxRate).toFixed(2);
        explainer.innerHTML = `
          <strong>Explicación interna (<code>POST /api/recommend</code> para SKU #${prod.stock_code}):</strong><br/>
          Se buscó en las <code>18,532</code> boletas históricas qué compraron junto con <strong>${prod.description}</strong>.
          El #1 es <strong>${topRule.consequent_name}</strong>: salieron juntos en <strong>${topRule.co_purchases} boletas</strong>
          (<strong>Confianza ${(topRule.confidence * 100).toFixed(1)} %</strong> · <strong>Lift ${topRule.lift}×</strong> más probable que por azar).<br/>
          <em>Aporte al negocio:</em> si 1 de cada 5 clientes agrega este complemento, suma <strong>+S/ ${extraPen}</strong> extra por pedido sin publicidad adicional.
        `;
      } else {
        explainer.innerHTML = `
          <strong>Explicación interna (<code>POST /api/recommend</code> para SKU #${prod.stock_code}):</strong><br/>
          Este producto no tuvo reglas fuertes por encima del filtro (Confianza ≥ 15 % y Lift ≥ 1.5×); por regla de negocio, la tienda <strong>nunca deja vacía la vitrina</strong> y promociona automáticamente los complementos más vendidos de <strong>${prod.category}</strong>.
        `;
      }
    }

    recoGrid.innerHTML = "";
    items.forEach((rec) => {
      const pObj = {
        stock_code: rec.consequent,
        description: rec.consequent_name,
        category: rec.consequent_category || prod.category,
        price_usd: rec.consequent_price_usd,
        invoice_count: rec.co_purchases || 100
      };
      const isRule = rec.match_type === "regla_asociacion";
      const auditTag = auditMode
        ? isRule
          ? `<div class="reco-audit-note">Regla: ${rec.co_purchases} compras juntas · Conf ${(rec.confidence * 100).toFixed(1)}% · Lift ${rec.lift}×</div>`
          : `<div class="reco-audit-note fallback">${rec.based_on}</div>`
        : "";

      const card = document.createElement("div");
      card.className = "reco-card";
      card.innerHTML = `
        <div class="prod-thumb" style="height:130px" role="button" tabindex="0">
          ${getProductSvg(pObj)}
        </div>
        ${auditTag}
        <h3 class="prod-title">${pObj.description}</h3>
        <div class="prod-price-pen" style="font-size:18px">S/ ${(pObj.price_usd * fxRate).toFixed(2)}</div>
        <div class="prod-actions">
          <button type="button" class="btn-outline btn-detail">Ver</button>
          <button type="button" class="btn-amazon-amber btn-add">+ Agregar</button>
        </div>
      `;

      const openTarget = () => openProductDetail(pObj);
      card.querySelector(".prod-thumb").addEventListener("click", openTarget);
      card.querySelector(".prod-title").addEventListener("click", openTarget);
      card.querySelector(".btn-detail").addEventListener("click", openTarget);
      card.querySelector(".btn-add").addEventListener("click", () => {
        addToCart(pObj, 1, true);
        showToast(`Agregado al carrito: ${pObj.description}`);
      });
      recoGrid.appendChild(card);
    });
  }

  async function openProductDetail(prod) {
    activeProduct = prod;
    storeCatalogView.hidden = true;
    productDetailView.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });

    document.getElementById("detailBreadcrumb").textContent = `Inicio › ${prod.category} › ${prod.description}`;
    document.getElementById("detailVisual").innerHTML = getProductSvg(prod);
    document.getElementById("detailSku").textContent = prod.stock_code;
    document.getElementById("detailCategoryPill").textContent = prod.category;
    document.getElementById("detailTitle").textContent = prod.description;
    document.getElementById("detailStats").textContent = `${prod.invoice_count.toLocaleString()} compras históricas`;
    document.getElementById("detailPricePen").textContent = `S/ ${(prod.price_usd * fxRate).toFixed(2)}`;
    document.getElementById("detailPriceUsd").textContent = `Equivalente internacional: $${prod.price_usd.toFixed(2)} USD (Tasa en vivo: S/ ${fxRate.toFixed(3)})`;
    document.getElementById("detailSpecCat").textContent = prod.category;
    document.getElementById("detailSpecPop").textContent = `Presente en ${prod.invoice_count.toLocaleString()} boletas reales`;
    document.getElementById("detailQty").value = "1";

    const resp = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart_codes: [prod.stock_code], limit: 4 })
    });
    const data = await resp.json();
    lastDetailRecos = data.recommendations || [];
    logApiCall("POST /api/recommend", `Recomendar complementos para SKU #${prod.stock_code}`, `${lastDetailRecos.length} producto(s) (${data.mode})`);
    renderDetailRecommendations(prod, lastDetailRecos);
  }

  document.getElementById("detailAddBtn").addEventListener("click", () => {
    if (!activeProduct) return;
    const qty = Number(document.getElementById("detailQty").value || 1);
    addToCart(activeProduct, qty, false);
    showToast(`Se agregó (${qty}) al carrito: ${activeProduct.description}`);
  });

  document.getElementById("detailBuyNowBtn").addEventListener("click", () => {
    if (!activeProduct) return;
    const qty = Number(document.getElementById("detailQty").value || 1);
    addToCart(activeProduct, qty, false);
    openCartDrawer();
  });

  // ==================== CARRITO + CHECKOUT ====================
  function addToCart(prod, qty, isFromReco) {
    if (isFromReco) usedReco = true;
    const existing = cart.find((c) => c.stock_code === prod.stock_code);
    if (existing) existing.quantity += qty;
    else {
      cart.push({
        stock_code: prod.stock_code,
        description: prod.description,
        price_usd: prod.price_usd,
        quantity: qty
      });
    }
    checkoutFeedback.textContent = "";
    renderCart();
  }

  function renderCartRecommendations(recs) {
    recoList.innerHTML = "";
    recs.forEach((rec) => {
      const el = document.createElement("div");
      el.className = "drawer-reco-item";
      const auditSub =
        auditMode && rec.lift !== null
          ? `Conf: ${(rec.confidence * 100).toFixed(0)}% · Lift: ${rec.lift}× · S/ ${(rec.consequent_price_usd * fxRate).toFixed(2)}`
          : `S/ ${(rec.consequent_price_usd * fxRate).toFixed(2)}`;
      el.innerHTML = `
        <div>
          <strong>${rec.consequent_name}</strong>
          <span>${auditSub}</span>
        </div>
        <button type="button" class="btn-mini-add">+ Agregar</button>
      `;
      el.querySelector(".btn-mini-add").addEventListener("click", () => {
        addToCart(
          {
            stock_code: rec.consequent,
            description: rec.consequent_name,
            price_usd: rec.consequent_price_usd
          },
          1,
          true
        );
      });
      recoList.appendChild(el);
    });
  }

  async function renderCart() {
    const totalCount = cart.reduce((acc, item) => acc + item.quantity, 0);
    cartBadgeCount.textContent = totalCount;
    drawerCount.textContent = totalCount;

    if (!cart.length) {
      cartItemsList.innerHTML = `<p class="empty-cart-msg">Tu carrito está vacío. Explora el catálogo para agregar productos.</p>`;
      totalUsdEl.textContent = "$0.00";
      totalPenEl.textContent = "S/ 0.00";
      checkoutBtn.disabled = true;
    } else {
      let sumUsd = 0;
      cartItemsList.innerHTML = "";
      cart.forEach((item, idx) => {
        sumUsd += item.price_usd * item.quantity;
        const row = document.createElement("div");
        row.className = "cart-row";
        row.innerHTML = `
          <div style="flex:1">
            <div class="cart-row-title">${item.description}</div>
            <div class="cart-row-meta">${item.quantity} × $${item.price_usd.toFixed(2)} USD (S/ ${(item.price_usd * fxRate).toFixed(2)})</div>
          </div>
          <div class="cart-qty-ctrl">
            <button type="button" class="cart-qty-btn btn-dec">−</button>
            <strong>${item.quantity}</strong>
            <button type="button" class="cart-qty-btn btn-inc">+</button>
            <button type="button" class="cart-qty-btn btn-del">✕</button>
          </div>
        `;
        row.querySelector(".btn-dec").addEventListener("click", () => {
          if (item.quantity > 1) item.quantity -= 1;
          else cart.splice(idx, 1);
          if (!cart.length) usedReco = false;
          renderCart();
        });
        row.querySelector(".btn-inc").addEventListener("click", () => {
          item.quantity += 1;
          renderCart();
        });
        row.querySelector(".btn-del").addEventListener("click", () => {
          cart.splice(idx, 1);
          if (!cart.length) usedReco = false;
          renderCart();
        });
        cartItemsList.appendChild(row);
      });
      totalUsdEl.textContent = `$${sumUsd.toFixed(2)}`;
      totalPenEl.textContent = `S/ ${(sumUsd * fxRate).toFixed(2)}`;
      checkoutBtn.disabled = false;
    }

    const resp = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart_codes: cart.map((c) => c.stock_code), limit: 3 })
    });
    const rData = await resp.json();
    lastCartRecos = rData.recommendations || [];
    recoModeBadge.textContent = rData.mode === "reglas_asociacion" ? "Reglas + Respaldo" : "Top Tienda";
    renderCartRecommendations(lastCartRecos);
  }

  document.getElementById("clearCartBtn").addEventListener("click", () => {
    cart = [];
    usedReco = false;
    renderCart();
  });

  checkoutBtn.addEventListener("click", async () => {
    const cust = sampleCustomers[Number(cartCustomerSelect.value)] || { CustomerID: 99999 };
    const seg = document.getElementById("cartCustSeg").textContent || "Cliente Leal";
    const resp = await fetch("/api/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: cust.CustomerID,
        segmento: seg,
        items: cart.map(({ stock_code, description, quantity, price_usd }) => ({
          stock_code,
          description,
          quantity,
          price_usd
        })),
        used_recommendation: usedReco
      })
    });
    if (resp.ok) {
      const b = await resp.json();
      logApiCall("POST /api/checkout", "Registrar compra en SQLite + convertir USD→PEN", `Boleta #${b.id} · S/ ${b.total_pen.toFixed(2)} (IA=${b.used_recommendation ? "Sí" : "No"})`);
      checkoutFeedback.textContent = `Compra confirmada · Boleta #${b.id} (S/ ${b.total_pen.toFixed(2)})`;
      cart = [];
      usedReco = false;
      renderCart();
      showToast(`Compra registrada: Boleta #${b.id}`);
    }
  });

  // ==================== GERENCIA: PROYECCIÓN PASADO -> FUTURO + SIMULADOR ====================
  function updateProjectionAndSim() {
    if (!contextData || !contextData.eda?.monthly_series) return;

    // Tomar los 12 meses completos (2010-12 a 2011-11) + proyectar 3 meses futuros
    const seriesFull = contextData.eda.monthly_series.filter((m) => m.month !== "2011-12");
    const recent3 = seriesFull.slice(-3);
    const avgRecentRev = recent3.reduce((s, r) => s + r.revenue, 0) / Math.max(1, recent3.length);

    const upsellPct = Number(document.getElementById("simUpsellPct").value) / 100;
    const rescuePct = Number(document.getElementById("simRescuePct").value) / 100;
    document.getElementById("simUpsellVal").textContent = `${Math.round(upsellPct * 100)} %`;
    document.getElementById("simRescueVal").textContent = `${Math.round(rescuePct * 100)} %`;

    // Aporte 1: Venta cruzada (~18% de aumento en ticket en las boletas que adoptan recomendación)
    const monthlyUpsellGain = avgRecentRev * upsellPct * 0.18;

    // Aporte 2: Rescate de clientes 'En Riesgo' usando su gasto promedio real
    const riskSeg = (contextData.segment_details || []).find((s) => s.segmento === "En Riesgo");
    const riskCount = riskSeg ? riskSeg.customers : 1024;
    const riskAvgMonetary = riskSeg ? riskSeg.avg_monetary : 600;
    // Asumimos recuperación trimestral con cupón (descontando 12% de margen del cupón en 1 compra promedio)
    const ticketProxy = riskSeg ? riskAvgMonetary / Math.max(1, riskSeg.avg_frequency) : 250;
    const quarterRescueGain = riskCount * rescuePct * ticketProxy * 0.88;
    const monthlyRescueGain = quarterRescueGain / 3.0;

    const quarterBase = avgRecentRev * 3.0;
    const quarterUpsell = monthlyUpsellGain * 3.0;
    const totalExtraUsd = quarterUpsell + quarterRescueGain;
    const totalExtraPen = totalExtraUsd * fxRate;

    document.getElementById("simBaseTotal").textContent = `$${Math.round(quarterBase).toLocaleString()} USD`;
    document.getElementById("simUpsellGain").textContent = `+$${Math.round(quarterUpsell).toLocaleString()} USD`;
    document.getElementById("simRescueGain").textContent = `+$${Math.round(quarterRescueGain).toLocaleString()} USD`;
    document.getElementById("simTotalExtraPen").textContent = `+S/ ${Math.round(totalExtraPen).toLocaleString()}`;
    document.getElementById("simTotalExtraUsd").textContent = `+$${Math.round(totalExtraUsd).toLocaleString()} USD en 3 meses`;

    const labels = [...seriesFull.map((m) => m.month), "Proy. Mes +1", "Proy. Mes +2", "Proy. Mes +3"];
    const histData = [...seriesFull.map((m) => Math.round(m.revenue)), null, null, null];

    const lastHist = seriesFull[seriesFull.length - 1].revenue;
    const baseProj = new Array(seriesFull.length - 1).fill(null).concat([
      Math.round(lastHist),
      Math.round(avgRecentRev),
      Math.round(avgRecentRev * 1.01),
      Math.round(avgRecentRev * 1.02)
    ]);

    const iaMonthly = avgRecentRev + monthlyUpsellGain + monthlyRescueGain;
    const iaProj = new Array(seriesFull.length - 1).fill(null).concat([
      Math.round(lastHist),
      Math.round(iaMonthly),
      Math.round(iaMonthly * 1.03),
      Math.round(iaMonthly * 1.06)
    ]);

    const ctx = document.getElementById("chartProjection");
    if (!ctx || typeof Chart === "undefined") return;

    if (projectionChart) {
      projectionChart.data.datasets[1].data = baseProj;
      projectionChart.data.datasets[2].data = iaProj;
      projectionChart.update();
      return;
    }

    projectionChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Histórico Real (USD)",
            data: histData,
            borderColor: "#1e293b",
            backgroundColor: "rgba(30, 41, 59, 0.08)",
            fill: true,
            tension: 0.25,
            borderWidth: 2.5
          },
          {
            label: "Proyección Sin IA (Base)",
            data: baseProj,
            borderColor: "#94a3b8",
            borderDash: [6, 5],
            tension: 0.2,
            borderWidth: 2
          },
          {
            label: "Proyección Con Minería de Datos",
            data: iaProj,
            borderColor: "#059669",
            backgroundColor: "rgba(5, 150, 105, 0.10)",
            fill: true,
            tension: 0.25,
            borderWidth: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: {
              color: "#475569",
              callback: (v) => `$${Math.round(v / 1000)}k`
            },
            grid: { color: "#e2e8f0" }
          },
          x: { ticks: { color: "#334155", maxRotation: 35 } }
        },
        plugins: {
          legend: { position: "bottom", labels: { color: "#334155", font: { weight: "600" } } }
        }
      }
    });
  }

  document.getElementById("simUpsellPct").addEventListener("input", updateProjectionAndSim);
  document.getElementById("simRescuePct").addEventListener("input", updateProjectionAndSim);

  async function renderManagementView() {
    updateProjectionAndSim();

    // Inventario por categoría usando /api/products?limit=150 una sola vez
    const catBody = document.getElementById("categoryInventoryBody");
    if (!catBody.dataset.loaded) {
      const resp = await fetch("/api/products?limit=150");
      const data = await resp.json();
      const byCat = {};
      (data.products || []).forEach((p) => {
        if (!byCat[p.category]) byCat[p.category] = { count: 0, units: 0, sumPrice: 0 };
        byCat[p.category].count += 1;
        byCat[p.category].units += Number(p.units_sold || 0);
        byCat[p.category].sumPrice += Number(p.price_usd || 0);
      });
      catBody.innerHTML = Object.entries(byCat)
        .sort((a, b) => b[1].units - a[1].units)
        .map(
          ([cat, st]) => `
          <tr>
            <td><strong>${cat}</strong></td>
            <td>${st.count} SKUs</td>
            <td>${st.units.toLocaleString()}</td>
            <td>S/ ${((st.sumPrice / st.count) * fxRate).toFixed(2)}</td>
          </tr>`
        )
        .join("");
      catBody.dataset.loaded = "1";
    }

    // Tabla de Segmentos RFM reales con acción empresarial
    const segStrategyMap = {
      "VIP Campeón": "Venta cruzada premium y envío rápido sin rebajar precio.",
      "Cliente Leal": "Recomendar complementos nuevos y programas de puntos.",
      "En Riesgo": "Enviar cupón 10–15 % de rescate antes de abandono.",
      "Dormido / Ocasional": "Reactivación en feriados / catálogo estacional."
    };
    const segBody = document.getElementById("segmentStrategyBody");
    const segDetails = contextData?.segment_details || [];
    segBody.innerHTML = segDetails
      .map(
        (s) => `
        <tr>
          <td><strong>${s.segmento}</strong></td>
          <td>${s.customers.toLocaleString()}</td>
          <td>$${s.avg_monetary.toLocaleString()}</td>
          <td><strong>${(s.repurchase_rate * 100).toFixed(1)} %</strong></td>
          <td>${segStrategyMap[s.segmento] || "--"}</td>
        </tr>`
      )
      .join("");
  }

  async function loadInvoices() {
    const resp = await fetch("/api/invoices");
    const data = await resp.json();
    document.getElementById("kpiNewBoletas").textContent = data.count;
    document.getElementById("kpiSqlSub").textContent = `${data.with_recommendation} boletas incluyeron recomendación IA.`;
    document.getElementById("boletasTotalBadge").textContent = `Total: $${data.total_usd.toFixed(2)} / S/ ${data.total_pen.toFixed(2)} (${data.with_recommendation} con IA)`;

    const tbody = document.getElementById("boletasTableBody");
    if (!data.invoices.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="empty-cell">Aún no hay boletas registradas desde la tienda.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.invoices
      .map(
        (b) => `
      <tr>
        <td><strong>#${b.id}</strong></td>
        <td>CLI-${b.customer_id}</td>
        <td><span class="seg-badge">${b.segmento}</span></td>
        <td>${b.items_count}</td>
        <td>${b.used_recommendation ? "Sí" : "No"}</td>
        <td>$${b.total_usd.toFixed(2)}</td>
        <td><strong>S/ ${b.total_pen.toFixed(2)}</strong></td>
        <td>${b.exchange_rate}</td>
        <td>${b.creado_en}</td>
      </tr>`
      )
      .join("");
  }

  // ==================== EVALUADOR RFM (USO INTERNO) ====================
  async function runCustomerPrediction() {
    const payload = {
      recency_days: Number(document.getElementById("fRecency").value),
      frequency: Number(document.getElementById("fFreq").value),
      monetary: Number(document.getElementById("fMonetary").value),
      total_items: Number(document.getElementById("fItems").value),
      unique_products: Number(document.getElementById("fUnique").value),
      tenure_days: Number(document.getElementById("fTenure").value),
      cancellation_count: Number(document.getElementById("fCancels").value),
      is_uk: document.getElementById("fMarket").value
    };
    const resp = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const out = await resp.json();
    logApiCall("POST /predict", "Clasificar cliente (K-Means + RandomForest)", `${out.segmento_rfm} (${(out.probabilidad_recompra * 100).toFixed(1)}% recompra)`);

    const recPct = (out.probabilidad_recompra * 100).toFixed(1);
    const fugPct = (out.probabilidad_fuga * 100).toFixed(1);
    const segEl = document.getElementById("rfmSegOut");
    segEl.textContent = out.segmento_rfm;
    segEl.classList.toggle("risk", out.prediccion_recompra === 0);
    document.getElementById("rfmLatency").textContent = `${out.tiempo_inferencia_ms} ms`;
    document.getElementById("rfmProbRecompra").textContent = `${recPct} %`;
    document.getElementById("rfmProbFuga").textContent = `${fugPct} %`;
    document.getElementById("rfmMeterFill").style.width = `${recPct}%`;
    document.getElementById("rfmNivelOut").textContent = `Clasificación: ${out.nivel_retencion}`;

    const ul = document.getElementById("rfmFactorsOut");
    ul.innerHTML = "";
    out.factores_clave.forEach((f) => {
      const li = document.createElement("li");
      li.textContent = f;
      ul.appendChild(li);
    });
    document.getElementById("rfmActionOut").textContent = out.accion_comercial;
  }

  document.getElementById("predictCustBtn").addEventListener("click", runCustomerPrediction);

  (async () => {
    await initContext();
    await loadProducts();
    await renderCart();
  })();
})();
