/* Lógica ligera de Lightbox para gráficas y demo interactiva de POST /predict */

(() => {
  // 1. Lightbox para cualquier .chart-img-wrap con data-lightbox-img
  const lightbox = document.getElementById('lightbox');
  const lbImg = document.getElementById('lbImg');
  const lbCap = document.getElementById('lbCap');

  document.querySelectorAll('[data-lightbox-img]').forEach((wrap) => {
    wrap.addEventListener('click', () => {
      const img = wrap.querySelector('img');
      if (!img || !lightbox || !lbImg) return;
      lbImg.src = img.src;
      if (lbCap) lbCap.textContent = wrap.dataset.caption || img.alt || '';
      lightbox.classList.add('open');
    });
  });

  // 2. Demo interactiva en Slide 1.3 (con fallback verificado si no hay servidor levantado)
  const PRESETS = {
    vip: {
      customer_id: 14646,
      recency_days: 12,
      frequency: 18,
      monetary: 6450,
      total_items: 1200,
      unique_products: 95,
      tenure_days: 240,
      cancellation_count: 0,
      is_uk: 'Internacional',
      fallback: {
        segmento_rfm: 'VIP Campeón',
        probabilidad_recompra: 0.9522,
        probabilidad_fuga: 0.0478,
        prediccion_recompra: 1,
        nivel_retencion: 'Alta Fidelidad',
        factores_clave: [
          'Compra reciente (12 días desde última visita)',
          'Alta recurrencia (18 boletas históricas)',
          'Alto valor acumulado ($6,450 USD)',
          'Relación madura (240 días de antigüedad)',
        ],
        accion_comercial:
          'Ofrecer venta cruzada premium o envío prioritario sin necesidad de descuento agresivo.',
      },
    },
    riesgo: {
      customer_id: 17850,
      recency_days: 145,
      frequency: 2,
      monetary: 180,
      total_items: 24,
      unique_products: 6,
      tenure_days: 35,
      cancellation_count: 1,
      is_uk: 'UK',
      fallback: {
        segmento_rfm: 'Dormido / Ocasional',
        probabilidad_recompra: 0.307,
        probabilidad_fuga: 0.693,
        prediccion_recompra: 0,
        nivel_retencion: 'Riesgo de Fuga',
        factores_clave: [
          'Inactividad prolongada (145 días sin comprar)',
          'Baja frecuencia histórica (2 compras)',
          'Registra 1 cancelación(es) previa(s)',
        ],
        accion_comercial:
          'ALERTA DE RETENCIÓN: entregar cupón de 10 %–15 % en caja para incentivar próxima compra.',
      },
    },
  };

  const fields = [
    'recency_days',
    'frequency',
    'monetary',
    'total_items',
    'unique_products',
    'tenure_days',
    'cancellation_count',
    'is_uk',
  ];

  const presetBtns = document.querySelectorAll('[data-preset]');
  const btnRun = document.getElementById('btnRunDemo');
  const statusEl = document.getElementById('demoStatus');
  const probEl = document.getElementById('demoProb');
  const barEl = document.getElementById('demoBar');
  const segEl = document.getElementById('demoSeg');
  const titleEl = document.getElementById('demoTitle');
  const factorsEl = document.getElementById('demoFactors');
  const actionEl = document.getElementById('demoAction');

  let activePreset = 'vip';

  function renderResult(res, sourceLabel) {
    const pct = (res.probabilidad_recompra * 100).toFixed(2);
    if (probEl) probEl.textContent = `${pct} %`;
    if (barEl) barEl.style.setProperty('--w', `${Math.round(res.probabilidad_recompra * 100)}%`);
    if (segEl) {
      segEl.textContent = `${res.segmento_rfm} · ${res.nivel_retencion}`;
      segEl.classList.toggle('risk', res.prediccion_recompra === 0);
    }
    if (titleEl) {
      titleEl.textContent =
        res.prediccion_recompra === 1
          ? `Recompra probable en 90 días (predicción = 1 · fuga ${(res.probabilidad_fuga * 100).toFixed(2)} %)`
          : `Alerta de abandono (predicción = 0 · fuga ${(res.probabilidad_fuga * 100).toFixed(2)} %)`;
    }
    if (factorsEl) {
      factorsEl.innerHTML = res.factores_clave.map((f) => `<li>${f}</li>`).join('');
    }
    if (actionEl) actionEl.textContent = res.accion_comercial;
    if (statusEl) statusEl.textContent = sourceLabel;
  }

  function applyPreset(key) {
    const p = PRESETS[key];
    if (!p) return;
    activePreset = key;
    presetBtns.forEach((b) => b.classList.toggle('active', b.dataset.preset === key));
    fields.forEach((f) => {
      const el = document.getElementById(`in_${f}`);
      if (el) el.value = String(p[f]);
    });
    renderResult(p.fallback, `Ejemplo verificado #${p.customer_id} (POST /predict)`);
  }

  presetBtns.forEach((btn) => {
    btn.addEventListener('click', () => applyPreset(btn.dataset.preset));
  });

  btnRun?.addEventListener('click', async () => {
    const payload = {
      customer_id: PRESETS[activePreset].customer_id,
      recency_days: Number(document.getElementById('in_recency_days')?.value || 12),
      frequency: Number(document.getElementById('in_frequency')?.value || 1),
      monetary: Number(document.getElementById('in_monetary')?.value || 100),
      total_items: Number(document.getElementById('in_total_items')?.value || 10),
      unique_products: Number(document.getElementById('in_unique_products')?.value || 5),
      tenure_days: Number(document.getElementById('in_tenure_days')?.value || 60),
      cancellation_count: Number(document.getElementById('in_cancellation_count')?.value || 0),
      is_uk: document.getElementById('in_is_uk')?.value || 'Internacional',
    };
    if (statusEl) statusEl.textContent = 'Consultando http://127.0.0.1:38420/predict ...';
    try {
      const r = await fetch('http://127.0.0.1:38420/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      renderResult(data, `Respuesta en vivo (${data.tiempo_inferencia_ms} ms)`);
    } catch {
      renderResult(
        PRESETS[activePreset].fallback,
        'Servidor local apagado: mostrando ejemplo verificado (abre ABRIR_SISTEMA.bat)'
      );
    }
  });
})();
