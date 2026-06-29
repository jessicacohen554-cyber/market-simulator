/**
 * shared-header.js — SVG waveform header injection
 * Injects animated SVG waveform overlays into .header elements.
 * Reads data-header-variant attribute for variant selection.
 * Lazy-loads overlays for below-fold headers.
 */

(function () {
  'use strict';

  /**
   * Build an animated SVG overlay for the given variant.
   * @param {string} variant - One of: 'default' | 'energy-flow' | 'grid' | 'pulse'
   * @returns {string} SVG markup string
   */
  function buildSVG(variant) {
    const id = `wv-${Math.random().toString(36).slice(2, 8)}`;

    switch (variant) {
      case 'grid':
        return buildGridSVG(id);
      case 'pulse':
        return buildPulseSVG(id);
      case 'energy-flow':
        return buildEnergyFlowSVG(id);
      default:
        return buildDefaultSVG(id);
    }
  }

  /** Default variant — multi-layer energy waveforms */
  function buildDefaultSVG(id) {
    return `<svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 1440 280" preserveAspectRatio="none"
         aria-hidden="true" focusable="false"
         style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;opacity:0.55;">
      <defs>
        <linearGradient id="${id}-g1" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stop-color="#0EA5E9" stop-opacity="0.4"/>
          <stop offset="50%"  stop-color="#22C55E" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#6366F1" stop-opacity="0.3"/>
        </linearGradient>
        <linearGradient id="${id}-g2" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stop-color="#F59E0B" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#0EA5E9" stop-opacity="0.20"/>
        </linearGradient>
      </defs>

      <!-- Bottom wave layer — hydro/wind blue-green -->
      <path fill="url(#${id}-g1)" opacity="0.7">
        <animate attributeName="d" dur="18s" repeatCount="indefinite"
          values="
            M0,220 C240,180 480,260 720,200 C960,140 1200,220 1440,180 L1440,280 L0,280 Z;
            M0,200 C200,240 440,160 720,220 C1000,280 1240,160 1440,200 L1440,280 L0,280 Z;
            M0,220 C240,180 480,260 720,200 C960,140 1200,220 1440,180 L1440,280 L0,280 Z
          "/>
      </path>

      <!-- Middle wave — solar amber tint -->
      <path fill="url(#${id}-g2)" opacity="0.5">
        <animate attributeName="d" dur="13s" repeatCount="indefinite"
          values="
            M0,240 C360,200 720,260 1080,220 C1260,200 1380,240 1440,230 L1440,280 L0,280 Z;
            M0,230 C300,260 600,200 900,240 C1100,265 1300,220 1440,250 L1440,280 L0,280 Z;
            M0,240 C360,200 720,260 1080,220 C1260,200 1380,240 1440,230 L1440,280 L0,280 Z
          "/>
      </path>

      <!-- Heartbeat pulse lines — energy flow indicators -->
      <polyline
        points="0,180 120,180 150,140 170,210 190,160 220,180 1440,180"
        fill="none" stroke="#0EA5E9" stroke-width="1.2" stroke-opacity="0.35">
        <animate attributeName="stroke-opacity" dur="4s" repeatCount="indefinite"
          values="0.35;0.60;0.35"/>
      </polyline>

      <polyline
        points="0,200 300,200 340,155 360,230 390,175 430,200 1440,200"
        fill="none" stroke="#22C55E" stroke-width="0.9" stroke-opacity="0.25">
        <animate attributeName="stroke-opacity" dur="6s" repeatCount="indefinite"
          values="0.25;0.50;0.25"/>
      </polyline>

      <!-- Grid dots overlay -->
      <pattern id="${id}-dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
        <circle cx="1" cy="1" r="0.8" fill="rgba(255,255,255,0.08)"/>
      </pattern>
      <rect width="100%" height="100%" fill="url(#${id}-dots)"/>
    </svg>`;
  }

  /** Grid variant — circuit/grid lines */
  function buildGridSVG(id) {
    return `<svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 1440 280" preserveAspectRatio="none"
         aria-hidden="true" focusable="false"
         style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;opacity:0.45;">
      <defs>
        <pattern id="${id}-grid" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
          <path d="M60 0 L0 0 L0 60" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#${id}-grid)"/>

      <!-- Horizontal sweep lines -->
      <line x1="0" y1="80" x2="1440" y2="80" stroke="#0EA5E9" stroke-opacity="0.15" stroke-width="0.8"/>
      <line x1="0" y1="160" x2="1440" y2="160" stroke="#22C55E" stroke-opacity="0.12" stroke-width="0.6"/>
      <line x1="0" y1="220" x2="1440" y2="220" stroke="#6366F1" stroke-opacity="0.10" stroke-width="0.5"/>

      <!-- Animated flow dot on grid line -->
      <circle r="3" fill="#0EA5E9" opacity="0.7">
        <animate attributeName="cx" dur="8s" repeatCount="indefinite" from="0" to="1440"/>
        <animateTransform attributeName="transform" type="translate" dur="8s" repeatCount="indefinite"
          from="0,80" to="0,80"/>
      </circle>
    </svg>`;
  }

  /** Pulse variant — heartbeat / demand trace */
  function buildPulseSVG(id) {
    return `<svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 1440 280" preserveAspectRatio="none"
         aria-hidden="true" focusable="false"
         style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;opacity:0.50;">
      <defs>
        <linearGradient id="${id}-pg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stop-color="#0EA5E9" stop-opacity="0"/>
          <stop offset="100%" stop-color="#0EA5E9" stop-opacity="0.18"/>
        </linearGradient>
      </defs>

      <!-- Demand curve shape -->
      <path fill="url(#${id}-pg)">
        <animate attributeName="d" dur="12s" repeatCount="indefinite"
          values="
            M0,200 C100,200 180,120 260,100 C340,80 400,130 500,120 C600,110 700,90 800,95 C900,100 1000,130 1100,120 C1200,110 1320,180 1440,170 L1440,280 L0,280 Z;
            M0,210 C120,190 200,110 280,95 C360,80 440,120 540,110 C640,100 740,85 840,90 C940,95 1040,120 1140,115 C1240,110 1340,175 1440,165 L1440,280 L0,280 Z;
            M0,200 C100,200 180,120 260,100 C340,80 400,130 500,120 C600,110 700,90 800,95 C900,100 1000,130 1100,120 C1200,110 1320,180 1440,170 L1440,280 L0,280 Z
          "/>
      </path>

      <!-- Trace line -->
      <path fill="none" stroke="#0EA5E9" stroke-width="1.5" opacity="0.4">
        <animate attributeName="d" dur="12s" repeatCount="indefinite"
          values="
            M0,200 C100,200 180,120 260,100 C340,80 400,130 500,120 C600,110 700,90 800,95 C900,100 1000,130 1100,120 C1200,110 1320,180 1440,170;
            M0,210 C120,190 200,110 280,95 C360,80 440,120 540,110 C640,100 740,85 840,90 C940,95 1040,120 1140,115 C1240,110 1340,175 1440,165;
            M0,200 C100,200 180,120 260,100 C340,80 400,130 500,120 C600,110 700,90 800,95 C900,100 1000,130 1100,120 C1200,110 1320,180 1440,170
          "/>
      </path>
    </svg>`;
  }

  /** Energy-flow variant — multi-color fuel stacking */
  function buildEnergyFlowSVG(id) {
    return `<svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 1440 280" preserveAspectRatio="none"
         aria-hidden="true" focusable="false"
         style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;opacity:0.50;">
      <defs>
        <linearGradient id="${id}-ef1" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stop-color="#F59E0B" stop-opacity="0.30"/>
          <stop offset="100%" stop-color="#F59E0B" stop-opacity="0.10"/>
        </linearGradient>
        <linearGradient id="${id}-ef2" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stop-color="#22C55E" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#22C55E" stop-opacity="0.08"/>
        </linearGradient>
        <linearGradient id="${id}-ef3" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stop-color="#0EA5E9" stop-opacity="0.30"/>
          <stop offset="100%" stop-color="#6366F1" stop-opacity="0.20"/>
        </linearGradient>
      </defs>

      <!-- Solar layer -->
      <path fill="url(#${id}-ef1)">
        <animate attributeName="d" dur="14s" repeatCount="indefinite"
          values="
            M0,260 C360,240 720,210 1080,230 C1260,240 1380,255 1440,250 L1440,280 L0,280 Z;
            M0,255 C300,245 660,215 1020,235 C1200,245 1360,260 1440,255 L1440,280 L0,280 Z;
            M0,260 C360,240 720,210 1080,230 C1260,240 1380,255 1440,250 L1440,280 L0,280 Z
          "/>
      </path>

      <!-- Wind layer -->
      <path fill="url(#${id}-ef2)">
        <animate attributeName="d" dur="10s" repeatCount="indefinite"
          values="
            M0,240 C240,220 480,240 720,215 C960,190 1200,230 1440,220 L1440,280 L0,280 Z;
            M0,230 C280,210 520,235 760,210 C1000,185 1240,225 1440,215 L1440,280 L0,280 Z;
            M0,240 C240,220 480,240 720,215 C960,190 1200,230 1440,220 L1440,280 L0,280 Z
          "/>
      </path>

      <!-- Hydro/nuclear base layer -->
      <path fill="url(#${id}-ef3)">
        <animate attributeName="d" dur="20s" repeatCount="indefinite"
          values="
            M0,210 C360,190 720,205 1080,185 C1260,175 1380,200 1440,195 L1440,280 L0,280 Z;
            M0,205 C340,195 700,200 1060,180 C1240,170 1370,195 1440,190 L1440,280 L0,280 Z;
            M0,210 C360,190 720,205 1080,185 C1260,175 1380,200 1440,195 L1440,280 L0,280 Z
          "/>
      </path>
    </svg>`;
  }

  /**
   * Inject overlay SVG into a single .header element.
   * @param {Element} headerEl
   */
  function injectOverlay(headerEl) {
    if (headerEl.dataset.overlayInjected) return;
    headerEl.dataset.overlayInjected = 'true';

    const variant = headerEl.dataset.headerVariant || 'default';

    // Create or find overlay container
    let overlay = headerEl.querySelector('.header__overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'header__overlay';
      // Insert before first child (so content stays on top)
      headerEl.insertBefore(overlay, headerEl.firstChild);
    }

    overlay.innerHTML = buildSVG(variant);
  }

  /**
   * Set up IntersectionObserver for lazy-loading below-fold headers.
   */
  function initHeaders() {
    const headers = document.querySelectorAll('.header');
    if (!headers.length) return;

    // First header (typically above fold) — inject immediately
    injectOverlay(headers[0]);

    if (headers.length === 1) return;

    // Below-fold headers — lazy inject via IntersectionObserver
    if ('IntersectionObserver' in window) {
      const obs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            injectOverlay(entry.target);
            obs.unobserve(entry.target);
          }
        });
      }, { rootMargin: '200px 0px' });

      Array.from(headers).slice(1).forEach(h => obs.observe(h));
    } else {
      // Fallback: inject all
      Array.from(headers).slice(1).forEach(injectOverlay);
    }
  }

  // Expose for runtime variant switching (dev/debug use)
  window._switchHeaderVariant = function (headerEl, variant) {
    try {
      headerEl.dataset.headerVariant = variant;
      headerEl.dataset.overlayInjected = '';
      injectOverlay(headerEl);
    } catch (e) {
      console.warn('switchHeaderVariant failed:', e);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeaders);
  } else {
    initHeaders();
  }
})();
