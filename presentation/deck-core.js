(() => {
  const slides = Array.from(document.querySelectorAll('.slide'));
  if (!slides.length) return;

  const deckEl = document.querySelector('.deck');
  const progressFill = document.getElementById('progressFill');
  const counterEl = document.getElementById('slideCounter');
  const btnPrev = document.getElementById('btnPrev');
  const btnNext = document.getElementById('btnNext');
  const btnFs = document.getElementById('btnFs');
  const dotsRoot = document.getElementById('navDots');
  const btnDrawer = document.getElementById('btnDrawer');
  const drawer = document.getElementById('drawer');
  const backdrop = document.getElementById('drawerBackdrop');
  const btnCloseDrawer = document.getElementById('btnCloseDrawer');
  const drawerList = document.getElementById('drawerList');
  const lightbox = document.getElementById('lightbox');
  const lbImg = document.getElementById('lbImg');
  const lbCap = document.getElementById('lbCap');

  // Controles de configuración ⚙️
  const btnConfig = document.getElementById('btnConfig');
  const configPanel = document.getElementById('configPanel');
  const btnCloseConfig = document.getElementById('btnCloseConfig');
  const btnToggleAnim = document.getElementById('btnToggleAnim');
  const btnPrintPdf = document.getElementById('btnPrintPdf');
  const btnResetCfg = document.getElementById('btnResetCfg');

  let current = 0;

  // 1. Paneles multimedia (.media-panel): soporta galería data-images O vistas mixtas .media-view (Código <-> Gráfica)
  slides.forEach((slide) => {
    const panel = slide.querySelector('.media-panel');
    if (!panel) return;

    const capEl = panel.querySelector('.media-caption');
    const cntEl = panel.querySelector('.img-counter');
    const prevBtn = panel.querySelector('.img-prev');
    const nextBtn = panel.querySelector('.img-next');

    const raw = panel.dataset.images;
    if (raw) {
      let items = [];
      try { items = JSON.parse(raw); } catch { items = []; }
      if (!items.length) return;

      let imgIdx = 0;
      const stage = panel.querySelector('.media-stage');
      const imgEl = panel.querySelector('.media-stage img');

      const renderImg = () => {
        const item = items[imgIdx];
        if (imgEl) {
          imgEl.style.opacity = '0.35';
          imgEl.src = item.src;
          imgEl.alt = item.caption || '';
          imgEl.onload = () => { imgEl.style.opacity = '1'; };
        }
        if (capEl) capEl.textContent = item.caption || '';
        if (cntEl) cntEl.textContent = `${imgIdx + 1} / ${items.length}`;
      };

      if (items.length <= 1) {
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
      } else {
        prevBtn?.addEventListener('click', (e) => {
          e.stopPropagation();
          imgIdx = (imgIdx - 1 + items.length) % items.length;
          renderImg();
        });
        nextBtn?.addEventListener('click', (e) => {
          e.stopPropagation();
          imgIdx = (imgIdx + 1) % items.length;
          renderImg();
        });
      }

      stage?.addEventListener('click', () => {
        if (!lightbox || !lbImg) return;
        lbImg.src = items[imgIdx].src;
        if (lbCap) lbCap.textContent = items[imgIdx].caption || '';
        lightbox.classList.add('open');
      });

      slide._stepImage = (dir) => {
        if (items.length <= 1) return;
        imgIdx = (imgIdx + dir + items.length) % items.length;
        renderImg();
      };

      renderImg();
      return;
    }

    const views = Array.from(panel.querySelectorAll('.media-view'));
    if (!views.length) return;
    let vIdx = 0;

    const renderView = () => {
      views.forEach((v, i) => {
        v.style.display = i === vIdx ? 'flex' : 'none';
      });
      if (capEl) capEl.textContent = views[vIdx].dataset.caption || '';
      if (cntEl) cntEl.textContent = `${vIdx + 1} / ${views.length}`;
    };

    if (views.length <= 1) {
      if (prevBtn) prevBtn.style.display = 'none';
      if (nextBtn) nextBtn.style.display = 'none';
    } else {
      prevBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        vIdx = (vIdx - 1 + views.length) % views.length;
        renderView();
      });
      nextBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        vIdx = (vIdx + 1) % views.length;
        renderView();
      });
    }

    views.forEach((v) => {
      if (v.classList.contains('img-box')) {
        v.addEventListener('click', () => {
          const img = v.querySelector('img');
          if (!img || !lightbox || !lbImg) return;
          lbImg.src = img.src;
          if (lbCap) lbCap.textContent = v.dataset.caption || '';
          lightbox.classList.add('open');
        });
      }
    });

    slide._stepImage = (dir) => {
      if (views.length <= 1) return;
      vIdx = (vIdx + dir + views.length) % views.length;
      renderView();
    };

    renderView();
  });

  // 2. Motor declarativo de secuencias por estado ([data-stepper])
  document.querySelectorAll('[data-stepper]').forEach((stepper) => {
    const steps = Array.from(stepper.querySelectorAll('[data-step]'));
    if (!steps.length) return;
    const statusEl = stepper.querySelector('[data-step-status]');
    const btnStepNext = stepper.querySelector('[data-step-next]');
    const btnStepPrev = stepper.querySelector('[data-step-prev]');
    const btnStepReset = stepper.querySelector('[data-step-reset]');
    const defaultMsg = statusEl?.dataset.stepDefault || statusEl?.innerHTML || '';
    let idx = -1;

    const renderStep = () => {
      steps.forEach((node, i) => {
        node.classList.toggle('is-focus', idx === i);
        node.classList.toggle('is-dim', idx !== -1 && idx !== i);
      });
      if (statusEl) {
        if (idx === -1) {
          statusEl.innerHTML = defaultMsg;
        } else {
          const msg = steps[idx].dataset.stepMsg || `Paso ${idx + 1} / ${steps.length}`;
          statusEl.innerHTML = `<strong>${msg}</strong>`;
        }
      }
    };

    btnStepNext?.addEventListener('click', () => {
      idx = idx === -1 ? 0 : (idx + 1) % steps.length;
      renderStep();
    });
    btnStepPrev?.addEventListener('click', () => {
      idx = idx <= 0 ? steps.length - 1 : idx - 1;
      renderStep();
    });
    btnStepReset?.addEventListener('click', () => {
      idx = -1;
      renderStep();
    });

    renderStep();
  });

  // 3. Puntos agrupados por sección + índice lateral
  const groups = new Map();
  slides.forEach((s, idx) => {
    const g = s.dataset.group || '0';
    const color = s.dataset.color || '#1e293b';
    const title = s.dataset.title || `Diapositiva ${idx + 1}`;
    const isSep = s.dataset.kind === 'title';

    if (!groups.has(g)) {
      const grpEl = document.createElement('div');
      grpEl.className = 'dot-group';
      dotsRoot?.appendChild(grpEl);
      groups.set(g, grpEl);
    }

    if (dotsRoot) {
      const dot = document.createElement('button');
      dot.className = 'nav-dot' + (isSep ? ' is-section' : '');
      dot.style.setProperty('--dot-c', color);
      dot.title = `${idx + 1}. ${title}`;
      dot.setAttribute('aria-label', dot.title);
      dot.addEventListener('click', () => goTo(idx));
      groups.get(g).appendChild(dot);
    }

    if (drawerList) {
      const item = document.createElement('button');
      item.className = 'drawer-item' + (isSep ? ' is-sep' : '');
      item.innerHTML = `
        <span class="drawer-swatch" style="background:${color}"></span>
        <span class="drawer-num">${String(idx + 1).padStart(2, '0')}</span>
        <span class="drawer-title">${title}</span>
      `;
      item.addEventListener('click', () => {
        goTo(idx);
        toggleDrawer(false);
      });
      drawerList.appendChild(item);
    }
  });

  const allDots = Array.from(document.querySelectorAll('.nav-dot'));
  const allDrawerItems = Array.from(document.querySelectorAll('.drawer-item'));

  function parseHashSlide() {
    const m = window.location.hash.match(/^#slide=(\d+)$/i);
    if (!m) return null;
    const idx = parseInt(m[1], 10) - 1;
    return idx >= 0 && idx < slides.length ? idx : null;
  }

  function goTo(index, syncHash = true) {
    if (index < 0 || index >= slides.length) return;
    slides[current].classList.remove('active');
    allDots[current]?.classList.remove('active');
    allDots[current]?.removeAttribute('aria-current');
    allDrawerItems[current]?.classList.remove('active');
    allDrawerItems[current]?.removeAttribute('aria-current');

    current = index;
    const activeSlide = slides[current];
    activeSlide.classList.add('active');
    allDots[current]?.classList.add('active');
    allDots[current]?.setAttribute('aria-current', 'step');
    allDrawerItems[current]?.classList.add('active');
    allDrawerItems[current]?.setAttribute('aria-current', 'step');

    const color = activeSlide.dataset.color || '#1e293b';
    document.documentElement.style.setProperty('--accent', color);

    const pct = ((current + 1) / slides.length) * 100;
    if (progressFill) progressFill.style.width = `${pct}%`;
    if (counterEl) counterEl.textContent = `${String(current + 1).padStart(2, '0')} / ${slides.length}`;

    if (btnPrev) btnPrev.disabled = current === 0;
    if (btnNext) btnNext.disabled = current === slides.length - 1;

    if (syncHash) {
      const targetHash = `#slide=${current + 1}`;
      if (window.location.hash !== targetHash) {
        try { history.replaceState(null, '', targetHash); } catch {}
      }
    }
  }

  function toggleDrawer(force) {
    if (!drawer || !backdrop) return;
    const open = typeof force === 'boolean' ? force : !drawer.classList.contains('open');
    drawer.classList.toggle('open', open);
    backdrop.classList.toggle('open', open);
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  // 5. Configuración ⚙️ persistente en localStorage
  const CFG_KEY = 'uhzielDeckConfig';
  const defaultCfg = {
    theme: 'light',
    navPos: 'bottom',
    anim: 'on',
    scaleAll: 1,
    scaleTitle: 1,
    scaleBody: 1,
    scaleMeta: 1,
  };

  let cfg = { ...defaultCfg };
  try {
    const saved = JSON.parse(localStorage.getItem(CFG_KEY) || 'null');
    if (saved) cfg = { ...defaultCfg, ...saved };
  } catch {}

  const clamp = (v, min, max) => Math.min(max, Math.max(min, Math.round(v * 100) / 100));

  function applyConfig() {
    const root = document.documentElement;
    root.dataset.theme = cfg.theme;
    root.dataset.navPos = cfg.navPos;
    root.dataset.anim = cfg.anim;
    root.style.setProperty('--scale-all', cfg.scaleAll);
    root.style.setProperty('--scale-title', cfg.scaleTitle);
    root.style.setProperty('--scale-body', cfg.scaleBody);
    root.style.setProperty('--scale-meta', cfg.scaleMeta);

    document.querySelectorAll('.cfg-pills').forEach((grp) => {
      const key = grp.dataset.cfgGroup;
      grp.querySelectorAll('.cfg-pill').forEach((pill) => {
        pill.classList.toggle('active', pill.dataset.val === cfg[key]);
      });
    });

    const syncSlider = (idRng, idVal, val) => {
      const elR = document.getElementById(idRng);
      const elV = document.getElementById(idVal);
      if (elR) elR.value = val;
      if (elV) elV.textContent = `${Math.round(val * 100)}%`;
    };
    syncSlider('rngScaleAll', 'valScaleAll', cfg.scaleAll);
    syncSlider('rngScaleTitle', 'valScaleTitle', cfg.scaleTitle);
    syncSlider('rngScaleBody', 'valScaleBody', cfg.scaleBody);
    syncSlider('rngScaleMeta', 'valScaleMeta', cfg.scaleMeta);

    if (btnToggleAnim) {
      btnToggleAnim.textContent = cfg.anim === 'on' ? '✨ Animaciones: ON' : '⏸ Animaciones: OFF';
    }
    try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch {}
  }

  function toggleConfig(force) {
    if (!configPanel || !btnConfig) return;
    const isHidden = configPanel.hasAttribute('hidden');
    const open = typeof force === 'boolean' ? force : isHidden;
    if (open) configPanel.removeAttribute('hidden');
    else configPanel.setAttribute('hidden', '');
    btnConfig.setAttribute('aria-expanded', String(open));
  }

  document.querySelectorAll('.cfg-pills').forEach((grp) => {
    const key = grp.dataset.cfgGroup;
    grp.addEventListener('click', (e) => {
      const pill = e.target.closest('.cfg-pill');
      if (!pill) return;
      cfg[key] = pill.dataset.val;
      applyConfig();
    });
  });

  document.querySelectorAll('.cfg-step').forEach((btn) => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.target;
      const delta = parseFloat(btn.dataset.delta);
      cfg[key] = clamp(cfg[key] + delta, 0.82, 1.36);
      applyConfig();
    });
  });

  [
    ['rngScaleAll', 'scaleAll', 0.82, 1.36],
    ['rngScaleTitle', 'scaleTitle', 0.82, 1.35],
    ['rngScaleBody', 'scaleBody', 0.82, 1.35],
    ['rngScaleMeta', 'scaleMeta', 0.82, 1.35],
  ].forEach(([id, key, min, max]) => {
    document.getElementById(id)?.addEventListener('input', (e) => {
      cfg[key] = clamp(parseFloat(e.target.value), min, max);
      applyConfig();
    });
  });

  btnToggleAnim?.addEventListener('click', () => {
    cfg.anim = cfg.anim === 'on' ? 'off' : 'on';
    applyConfig();
  });
  btnPrintPdf?.addEventListener('click', () => {
    toggleConfig(false);
    window.print();
  });
  btnResetCfg?.addEventListener('click', () => {
    cfg = { ...defaultCfg };
    applyConfig();
  });

  btnPrev?.addEventListener('click', () => goTo(current - 1));
  btnNext?.addEventListener('click', () => goTo(current + 1));
  btnFs?.addEventListener('click', toggleFullscreen);
  btnDrawer?.addEventListener('click', () => { toggleConfig(false); toggleDrawer(); });
  btnCloseDrawer?.addEventListener('click', () => toggleDrawer(false));
  backdrop?.addEventListener('click', () => toggleDrawer(false));
  btnConfig?.addEventListener('click', () => { toggleDrawer(false); toggleConfig(); });
  btnCloseConfig?.addEventListener('click', () => toggleConfig(false));
  lightbox?.addEventListener('click', () => lightbox.classList.remove('open'));

  document.addEventListener('keydown', (e) => {
    if (lightbox?.classList.contains('open')) {
      if (e.key === 'Escape') lightbox.classList.remove('open');
      return;
    }
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ' || e.key === 'PageDown') {
      if (['INPUT', 'TEXTAREA', 'BUTTON'].includes(document.activeElement?.tagName) && e.key === ' ') return;
      e.preventDefault();
      goTo(current + 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp' || e.key === 'PageUp') {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
      e.preventDefault();
      goTo(current - 1);
    } else if (e.key === 'f' || e.key === 'F') {
      toggleFullscreen();
    } else if (e.key === 'm' || e.key === 'M' || e.key === 'i' || e.key === 'I') {
      toggleConfig(false);
      toggleDrawer();
    } else if (e.key === 'c' || e.key === 'C') {
      toggleDrawer(false);
      toggleConfig();
    } else if (e.key === ']') {
      slides[current]._stepImage?.(1);
    } else if (e.key === '[') {
      slides[current]._stepImage?.(-1);
    } else if (e.key === 'Escape') {
      toggleDrawer(false);
      toggleConfig(false);
    }
  });

  // 6. Swipe táctil no intrusivo (ignora bloques de código, tablas e inputs)
  let touchStartX = 0;
  let touchStartY = 0;
  let touchIgnore = false;

  deckEl?.addEventListener('touchstart', (e) => {
    if (e.touches.length !== 1) { touchIgnore = true; return; }
    const target = e.target;
    touchIgnore = Boolean(target.closest('.code-pre, pre, table, input, button, a, .media-panel, [data-no-swipe]'));
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }, { passive: true });

  deckEl?.addEventListener('touchend', (e) => {
    if (touchIgnore || e.changedTouches.length !== 1) return;
    if (lightbox?.classList.contains('open') || drawer?.classList.contains('open')) return;
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;
    if (Math.abs(dx) > 64 && Math.abs(dx) > Math.abs(dy) * 1.8) {
      goTo(dx < 0 ? current + 1 : current - 1);
    }
  }, { passive: true });

  window.addEventListener('hashchange', () => {
    const h = parseHashSlide();
    if (h !== null && h !== current) goTo(h, false);
  });

  applyConfig();
  const initial = parseHashSlide();
  goTo(initial !== null ? initial : 0, false);
})();
