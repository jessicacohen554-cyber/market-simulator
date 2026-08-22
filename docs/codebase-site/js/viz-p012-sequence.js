/**
 * viz-p012-sequence.js — V12
 * Animated P0→P1 two-solve step-through diagram.
 * P0 and P1 are the only two passes (CLAUDE.md "Dispatch & Commitment"); the
 * historical third pass P2 is archived behind --enable-legacy-p2 and is
 * deliberately NOT a step here.
 * Self-contained; no D3 dependency.
 */

(function () {
  'use strict';

  /* -------------------------------------------------------------------------
     Data: step definitions
     ----------------------------------------------------------------------- */

  const STEPS = [
    {
      id: 'p0',
      label: 'P0',
      title: 'Base MC Dispatch',
      eyebrow: 'Pass 1 of 2',
      colorVar: '--wind',       // green
      colorHex: '#22C55E',
      colorBg: 'rgba(34,197,94,0.10)',
      borderActive: '#22C55E',
      description:
        'The LP solves with each generator’s fuel-cost-only marginal cost — ' +
        'heat_rate × fuel_price + VOM + carbon. No startup markup yet. ' +
        'The resulting dispatch reveals how long each CC and CT unit actually ' +
        'runs, measured per calendar month.',
      badge: 'model/commitment.py · base_mc',
      arrowLabel: 'extract run lengths →',
      buildSVG: buildP0SVG,
    },
    {
      id: 'p1',
      label: 'P1',
      title: 'Bid MC Dispatch',
      eyebrow: 'Pass 2 of 2',
      colorVar: '--hydro',      // blue
      colorHex: '#0EA5E9',
      colorBg: 'rgba(14,165,233,0.10)',
      borderActive: '#0EA5E9',
      description:
        'compute_monthly_markup() amortises each unit’s startup cost across ' +
        'its measured run length: μ = startup_cost ÷ avg_run_length. ' +
        'P1 re-solves with bid_mc = base_mc + μ. The dual on each zone’s ' +
        'energy-balance constraint is the clearing price — the LMP.',
      badge: 'commitment.py · bid_mc · sets LMPs · the scored run',
      arrowLabel: null,
      buildSVG: buildP1SVG,
    },
  ];

  /* -------------------------------------------------------------------------
     SVG Illustrations
     ----------------------------------------------------------------------- */

  function buildP0SVG() {
    return `
<svg viewBox="0 0 220 118" xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="P0 base-cost dispatch bar chart">
  <title>P0 base-cost dispatch</title>
  <defs>
    <marker id="p0-arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="rgba(255,255,255,0.45)"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="220" height="118" fill="transparent"/>

  <!-- Y-axis -->
  <line x1="30" y1="8" x2="30" y2="90" stroke="rgba(255,255,255,0.20)" stroke-width="1"/>
  <!-- Y axis label -->
  <text x="6" y="50" font-size="9" fill="rgba(255,255,255,0.50)"
        font-family="DM Sans,sans-serif" text-anchor="middle"
        transform="rotate(-90,6,50)">$/MWh</text>

  <!-- X-axis -->
  <line x1="30" y1="90" x2="215" y2="90" stroke="rgba(255,255,255,0.20)" stroke-width="1"/>
  <text x="122" y="103" font-size="8" fill="rgba(255,255,255,0.45)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Merit order →</text>

  <!-- Bars: wind, nuclear, coal, gas-CC, gas-CT -->
  <!-- Wind: zero MC, tall capacity, $0 -->
  <rect x="34" y="58" width="28" height="32" fill="#22C55E" rx="2" opacity="0.85"/>
  <text x="48" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Wind</text>
  <text x="48" y="55" font-size="7" fill="#22C55E"
        font-family="DM Sans,sans-serif" text-anchor="middle">~$0</text>

  <!-- Nuclear: low MC, high capacity -->
  <rect x="68" y="50" width="28" height="40" fill="#6366F1" rx="2" opacity="0.85"/>
  <text x="82" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Nucl.</text>
  <text x="82" y="47" font-size="7" fill="#6366F1"
        font-family="DM Sans,sans-serif" text-anchor="middle">~$22</text>

  <!-- Coal: moderate MC -->
  <rect x="102" y="43" width="28" height="47" fill="#4B5563" rx="2" opacity="0.85"/>
  <text x="116" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Coal</text>
  <text x="116" y="40" font-size="7" fill="rgba(255,255,255,0.65)"
        font-family="DM Sans,sans-serif" text-anchor="middle">~$32</text>

  <!-- Gas-CC: mid MC -->
  <rect x="136" y="34" width="28" height="56" fill="#6B7280" rx="2" opacity="0.85"/>
  <text x="150" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Gas-CC</text>
  <text x="150" y="31" font-size="7" fill="rgba(255,255,255,0.65)"
        font-family="DM Sans,sans-serif" text-anchor="middle">~$42</text>

  <!-- Gas-CT: high MC -->
  <rect x="170" y="22" width="28" height="68" fill="#9CA3AF" rx="2" opacity="0.70"/>
  <text x="184" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Gas-CT</text>
  <text x="184" y="19" font-size="7" fill="rgba(255,255,255,0.65)"
        font-family="DM Sans,sans-serif" text-anchor="middle">~$68</text>

  <!-- Demand line at Gas-CC level -->
  <line x1="30" y1="36" x2="215" y2="36"
        stroke="#F59E0B" stroke-width="1.2" stroke-dasharray="5,3" opacity="0.70"/>
  <text x="213" y="33" font-size="7" fill="#F59E0B"
        font-family="DM Sans,sans-serif" text-anchor="end">demand</text>
</svg>`;
  }

  function buildP1SVG() {
    return `
<svg viewBox="0 0 220 118" xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="P1 bid-cost dispatch with startup markup">
  <title>P1 bid-cost dispatch with startup markup</title>
  <defs>
    <pattern id="p1-hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="4" stroke="#F59E0B" stroke-width="1.8" opacity="0.70"/>
    </pattern>
  </defs>

  <!-- Background -->
  <rect width="220" height="118" fill="transparent"/>

  <!-- Y-axis -->
  <line x1="30" y1="8" x2="30" y2="90" stroke="rgba(255,255,255,0.20)" stroke-width="1"/>
  <text x="6" y="50" font-size="9" fill="rgba(255,255,255,0.50)"
        font-family="DM Sans,sans-serif" text-anchor="middle"
        transform="rotate(-90,6,50)">$/MWh</text>

  <!-- X-axis -->
  <line x1="30" y1="90" x2="215" y2="90" stroke="rgba(255,255,255,0.20)" stroke-width="1"/>
  <text x="122" y="103" font-size="8" fill="rgba(255,255,255,0.45)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Merit order →</text>

  <!-- Wind (same as P0) -->
  <rect x="34" y="58" width="28" height="32" fill="#22C55E" rx="2" opacity="0.85"/>
  <text x="48" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Wind</text>

  <!-- Nuclear (same) -->
  <rect x="68" y="50" width="28" height="40" fill="#6366F1" rx="2" opacity="0.85"/>
  <text x="82" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Nucl.</text>

  <!-- Coal (same, no markup) -->
  <rect x="102" y="43" width="28" height="47" fill="#4B5563" rx="2" opacity="0.85"/>
  <text x="116" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Coal</text>

  <!-- Gas-CC base cost -->
  <rect x="136" y="42" width="28" height="48" fill="#6B7280" rx="2" opacity="0.85"/>
  <!-- Gas-CC markup layer (hatched amber) -->
  <rect x="136" y="28" width="28" height="14" fill="url(#p1-hatch)" rx="2" opacity="0.9"/>
  <rect x="136" y="28" width="28" height="14" fill="none" stroke="#F59E0B"
        stroke-width="0.8" rx="2" opacity="0.60"/>
  <text x="136" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="start" dx="2">Gas-CC</text>

  <!-- μ label with brace -->
  <line x1="166" y1="28" x2="178" y2="28" stroke="#F59E0B" stroke-width="0.8" opacity="0.80"/>
  <line x1="166" y1="42" x2="178" y2="42" stroke="#F59E0B" stroke-width="0.8" opacity="0.80"/>
  <line x1="177" y1="28" x2="177" y2="42" stroke="#F59E0B" stroke-width="0.8" opacity="0.80"/>
  <text x="180" y="36" font-size="8" fill="#F59E0B"
        font-family="DM Sans,sans-serif">μ</text>

  <!-- Gas-CT base cost -->
  <rect x="170" y="30" width="28" height="60" fill="#9CA3AF" rx="2" opacity="0.70"/>
  <!-- Gas-CT markup -->
  <rect x="170" y="14" width="28" height="16" fill="url(#p1-hatch)" rx="2" opacity="0.9"/>
  <rect x="170" y="14" width="28" height="16" fill="none" stroke="#F59E0B"
        stroke-width="0.8" rx="2" opacity="0.60"/>
  <text x="184" y="112" font-size="7.5" fill="rgba(255,255,255,0.55)"
        font-family="DM Sans,sans-serif" text-anchor="middle">Gas-CT</text>

  <!-- Demand line (same position) -->
  <line x1="30" y1="36" x2="215" y2="36"
        stroke="#F59E0B" stroke-width="1.2" stroke-dasharray="5,3" opacity="0.70"/>
  <text x="213" y="33" font-size="7" fill="#F59E0B"
        font-family="DM Sans,sans-serif" text-anchor="end">demand</text>

  <!-- Price = dual annotation -->
  <text x="32" y="21" font-size="7.5" fill="#0EA5E9"
        font-family="DM Sans,sans-serif">LMP = dual →</text>
  <line x1="30" y1="18" x2="215" y2="18"
        stroke="#0EA5E9" stroke-width="1" opacity="0.60"/>
</svg>`;
  }

  /* -------------------------------------------------------------------------
     Build UI
     ----------------------------------------------------------------------- */

  function buildHTML(containerId) {
    const wrap = document.getElementById(containerId);
    if (!wrap) return;

    wrap.innerHTML = `
<div class="p012-diagram" role="region" aria-label="P0 to P1 solve sequence">

  <!-- Panels row -->
  <div class="p012-panels" id="${containerId}-panels">
    ${STEPS.map((s, i) => `
    <div class="p012-panel${i === 0 ? ' p012-panel--active' : ''}"
         id="${containerId}-panel-${i}"
         data-step="${i}"
         role="button"
         tabindex="0"
         aria-pressed="${i === 0}"
         aria-label="${s.label}: ${s.title}">
      <div class="p012-panel__eyebrow">${s.eyebrow}</div>
      <div class="p012-panel__header">
        <span class="p012-panel__label" style="color:${s.colorHex}">${s.label}</span>
        <span class="p012-panel__title">${s.title}</span>
      </div>
      <div class="p012-panel__svg" aria-hidden="true">${s.buildSVG()}</div>
      <p class="p012-panel__desc">${s.description}</p>
      <div class="p012-panel__badge">${s.badge}</div>
    </div>
    ${i < STEPS.length - 1 ? `
    <div class="p012-arrow" id="${containerId}-arrow-${i}" aria-hidden="true">
      <div class="p012-arrow__label">${s.arrowLabel}</div>
      <svg viewBox="0 0 40 40" class="p012-arrow__svg">
        <defs>
          <marker id="${containerId}-ah${i}" markerWidth="8" markerHeight="8"
                  refX="7" refY="4" orient="auto">
            <path d="M0,1 L8,4 L0,7 Z" fill="rgba(255,255,255,0.50)"/>
          </marker>
        </defs>
        <line x1="4" y1="20" x2="34" y2="20"
              stroke="rgba(255,255,255,0.35)" stroke-width="1.5"
              stroke-dasharray="5,3"
              marker-end="url(#${containerId}-ah${i})"
              class="p012-arrow__line"/>
      </svg>
    </div>` : ''}
    `).join('')}
  </div>

  <!-- Controls -->
  <div class="p012-controls" role="group" aria-label="Step navigation">
    <button class="p012-btn p012-btn--prev" id="${containerId}-prev"
            aria-label="Previous step" disabled>
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" aria-hidden="true">
        <path d="M10 3L5 8l5 5"/>
      </svg>
      Prev
    </button>

    <div class="p012-dots" role="tablist" aria-label="Steps">
      ${STEPS.map((s, i) => `
      <button class="p012-dot${i === 0 ? ' p012-dot--active' : ''}"
              id="${containerId}-dot-${i}"
              role="tab"
              aria-selected="${i === 0}"
              aria-label="Step ${i + 1}: ${s.title}"
              data-step="${i}">
      </button>`).join('')}
    </div>

    <div class="p012-step-label" id="${containerId}-step-label" aria-live="polite">
      Step 1 of ${STEPS.length} — ${STEPS[0].title}
    </div>

    <button class="p012-btn p012-btn--next" id="${containerId}-next"
            aria-label="Next step">
      Next
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" aria-hidden="true">
        <path d="M6 3l5 5-5 5"/>
      </svg>
    </button>
  </div>
</div>`;
  }

  /* -------------------------------------------------------------------------
     State machine
     ----------------------------------------------------------------------- */

  function initController(containerId) {
    let current = 0;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const prevBtn = document.getElementById(`${containerId}-prev`);
    const nextBtn = document.getElementById(`${containerId}-next`);
    const stepLabel = document.getElementById(`${containerId}-step-label`);

    function goTo(step) {
      if (step < 0 || step >= STEPS.length) return;
      const prev = current;
      current = step;
      updatePanels(prev, current);
      updateControls();
    }

    function updatePanels(from, to) {
      STEPS.forEach((s, i) => {
        const panel = document.getElementById(`${containerId}-panel-${i}`);
        if (!panel) return;
        panel.classList.toggle('p012-panel--active', i === to);
        panel.classList.toggle('p012-panel--done', i < to);
        panel.classList.toggle('p012-panel--upcoming', i > to);
        panel.setAttribute('aria-pressed', i === to ? 'true' : 'false');

        // Animate enter if advancing
        if (i === to && !reducedMotion && from !== to) {
          panel.classList.add('p012-panel--entering');
          setTimeout(() => panel.classList.remove('p012-panel--entering'), 500);
        }
      });

      // Animate arrows
      STEPS.forEach((s, i) => {
        const arrow = document.getElementById(`${containerId}-arrow-${i}`);
        if (!arrow) return;
        arrow.classList.toggle('p012-arrow--active', i < to);
        arrow.classList.toggle('p012-arrow--current', i === to - 1);
      });

      // Update dots
      STEPS.forEach((s, i) => {
        const dot = document.getElementById(`${containerId}-dot-${i}`);
        if (!dot) return;
        dot.classList.toggle('p012-dot--active', i === to);
        dot.classList.toggle('p012-dot--done', i < to);
        dot.setAttribute('aria-selected', i === to ? 'true' : 'false');
      });

      if (stepLabel) {
        stepLabel.textContent = `Step ${to + 1} of ${STEPS.length} — ${STEPS[to].title}`;
      }
    }

    function updateControls() {
      if (prevBtn) {
        prevBtn.disabled = current === 0;
        prevBtn.setAttribute('aria-disabled', current === 0 ? 'true' : 'false');
      }
      if (nextBtn) {
        nextBtn.disabled = current === STEPS.length - 1;
        nextBtn.setAttribute('aria-disabled', current === STEPS.length - 1 ? 'true' : 'false');
      }
    }

    // Button listeners
    if (prevBtn) prevBtn.addEventListener('click', () => goTo(current - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => goTo(current + 1));

    // Panel click to navigate directly
    STEPS.forEach((s, i) => {
      const panel = document.getElementById(`${containerId}-panel-${i}`);
      if (!panel) return;
      panel.addEventListener('click', () => goTo(i));
      panel.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          goTo(i);
        }
      });
    });

    // Dot buttons
    STEPS.forEach((s, i) => {
      const dot = document.getElementById(`${containerId}-dot-${i}`);
      if (!dot) return;
      dot.addEventListener('click', () => goTo(i));
    });

    // Keyboard arrow navigation on dots
    const dotsEl = document.querySelector(`#${containerId} .p012-dots`);
    if (dotsEl) {
      dotsEl.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') goTo(current + 1);
        if (e.key === 'ArrowLeft') goTo(current - 1);
      });
    }

    updateControls();
  }

  /* -------------------------------------------------------------------------
     CSS injection
     ----------------------------------------------------------------------- */

  function injectStyles() {
    if (document.getElementById('p012-styles')) return;
    const style = document.createElement('style');
    style.id = 'p012-styles';
    style.textContent = `
/* P012 Sequence Diagram */
.p012-diagram {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 32px 0 8px;
  user-select: none;
}

.p012-panels {
  display: flex;
  align-items: stretch;
  gap: 0;
}

/* Panel */
.p012-panel {
  flex: 1;
  min-width: 0;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
  transition: border-color 300ms ease, background 300ms ease,
              opacity 300ms ease, transform 300ms ease, box-shadow 300ms ease;
  opacity: 0.45;
  transform: scale(0.97);
  position: relative;
  outline: none;
}

.p012-panel:focus-visible {
  outline: 2px solid rgba(14,165,233,0.70);
  outline-offset: 2px;
}

.p012-panel--active {
  opacity: 1;
  transform: scale(1);
  background: rgba(255,255,255,0.07);
  border-color: rgba(255,255,255,0.22);
  box-shadow: 0 4px 24px rgba(0,0,0,0.25),
              inset 0 1px 0 rgba(255,255,255,0.08);
}

.p012-panel--done {
  opacity: 0.60;
  transform: scale(0.97);
}

.p012-panel--entering {
  animation: p012-slide-in 0.45s cubic-bezier(0.22,1,0.36,1) both;
}

@keyframes p012-slide-in {
  from { opacity: 0.30; transform: scale(0.93) translateY(6px); }
  to   { opacity: 1;    transform: scale(1)    translateY(0);   }
}

.p012-panel__eyebrow {
  font-size: 0.63rem;
  font-weight: 700;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.38);
  font-family: 'DM Sans', sans-serif;
}

.p012-panel__header {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.p012-panel__label {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
}

.p012-panel__title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.88rem;
  font-weight: 700;
  color: rgba(255,255,255,0.85);
  line-height: 1.3;
}

.p012-panel__svg {
  border-radius: 8px;
  background: rgba(0,0,0,0.18);
  overflow: hidden;
  flex-shrink: 0;
}

.p012-panel__svg svg {
  display: block;
  width: 100%;
  height: auto;
}

.p012-panel__desc {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.68);
  line-height: 1.6;
  font-family: 'DM Sans', sans-serif;
  flex: 1;
}

.p012-panel__badge {
  font-size: 0.68rem;
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  color: rgba(255,255,255,0.35);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 4px;
  padding: 3px 8px;
  align-self: flex-start;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* Arrow connector */
.p012-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  gap: 4px;
  flex-shrink: 0;
  width: 56px;
  opacity: 0.45;
  transition: opacity 300ms ease;
}

.p012-arrow--active { opacity: 0.85; }

.p012-arrow--current .p012-arrow__line {
  animation: p012-dash-flow 1.2s linear infinite;
}

@keyframes p012-dash-flow {
  to { stroke-dashoffset: -20; }
}

.p012-arrow__label {
  font-size: 0.60rem;
  color: rgba(255,255,255,0.45);
  font-family: 'DM Sans', sans-serif;
  text-align: center;
  line-height: 1.3;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  white-space: nowrap;
  letter-spacing: 0.02em;
}

.p012-arrow__svg {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  rotate: 90deg;
}

@media (min-width: 769px) {
  .p012-arrow__svg { rotate: 0deg; }
  .p012-arrow__label { writing-mode: horizontal-tb; }
  .p012-arrow { width: 64px; }
}

/* Controls */
.p012-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.p012-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 8px;
  color: rgba(255,255,255,0.80);
  font-size: 0.82rem;
  font-weight: 600;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: background 150ms ease, border-color 150ms ease, color 150ms ease;
}

.p012-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.14);
  color: #fff;
  border-color: rgba(255,255,255,0.22);
}

.p012-btn:disabled {
  opacity: 0.30;
  cursor: not-allowed;
}

.p012-btn svg { width: 14px; height: 14px; }

.p012-btn--next {
  background: rgba(14,165,233,0.18);
  border-color: rgba(14,165,233,0.35);
  color: #7DD3FC;
  margin-left: auto;
}

.p012-btn--next:hover:not(:disabled) {
  background: rgba(14,165,233,0.28);
  border-color: rgba(14,165,233,0.55);
  color: #BAE6FD;
}

/* Step dots */
.p012-dots {
  display: flex;
  align-items: center;
  gap: 8px;
}

.p012-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.18);
  border: none;
  cursor: pointer;
  padding: 0;
  transition: background 200ms ease, transform 200ms ease;
}

.p012-dot--done {
  background: rgba(255,255,255,0.45);
}

.p012-dot--active {
  background: #0EA5E9;
  transform: scale(1.35);
}

.p012-dot:hover:not(.p012-dot--active) {
  background: rgba(255,255,255,0.35);
  transform: scale(1.15);
}

.p012-step-label {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.50);
  font-family: 'DM Sans', sans-serif;
}

/* Responsive: stack panels vertically on narrow screens */
@media (max-width: 768px) {
  .p012-panels {
    flex-direction: column;
    gap: 12px;
  }
  .p012-arrow {
    width: auto;
    flex-direction: row;
    padding: 4px 0;
    height: 40px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .p012-panel, .p012-arrow { transition: none; }
  .p012-panel--entering { animation: none; }
  .p012-arrow--current .p012-arrow__line { animation: none; }
}
    `;
    document.head.appendChild(style);
  }

  /* -------------------------------------------------------------------------
     Entry point
     ----------------------------------------------------------------------- */

  function init() {
    const CONTAINER_ID = 'v12-sequence';
    const el = document.getElementById(CONTAINER_ID);
    if (!el) return;

    injectStyles();
    buildHTML(CONTAINER_ID);
    initController(CONTAINER_ID);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
