/**
 * chart-utils.js — D3 v7 helper module for Codebase Explorer
 *
 * Import as ES module:
 *   import { responsiveChart, cssColor, fuelColorScale, isoColorScale,
 *            addTooltip, formatMW, formatPrice, formatPct } from './chart-utils.js';
 *
 * Requires D3 v7 loaded globally (window.d3) or imported externally.
 */

/* ---------------------------------------------------------------------------
   1. responsiveChart — ResizeObserver wrapper
   --------------------------------------------------------------------------- */

/**
 * Attach a ResizeObserver to `containerSelector` and call `drawFn(width, height)`
 * on initial render and on every resize (debounced 80ms).
 *
 * @param {string} containerSelector - CSS selector for the chart container element
 * @param {function(width:number, height:number):void} drawFn - called with px dimensions
 * @returns {{ disconnect: function }} - call disconnect() to clean up the observer
 */
export function responsiveChart(containerSelector, drawFn) {
  const container = typeof containerSelector === 'string'
    ? document.querySelector(containerSelector)
    : containerSelector;

  if (!container) {
    console.warn(`responsiveChart: no element matches "${containerSelector}"`);
    return { disconnect: () => {} };
  }

  let rafId = null;
  let lastW = 0, lastH = 0;

  function draw() {
    const w = container.clientWidth;
    const h = container.clientHeight || Math.round(w * 0.5);
    if (w === lastW && h === lastH) return;
    lastW = w;
    lastH = h;
    drawFn(w, h);
  }

  // Debounced via rAF so we never fire mid-reflow
  const obs = new ResizeObserver(() => {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(draw);
  });

  obs.observe(container);
  draw(); // initial render

  return {
    disconnect() {
      obs.disconnect();
      if (rafId) cancelAnimationFrame(rafId);
    },
  };
}

/* ---------------------------------------------------------------------------
   2. cssColor — Read CSS custom property from :root
   --------------------------------------------------------------------------- */

/**
 * Read a CSS custom property value from the document root.
 *
 * @param {string} varName - e.g. '--hydro' or '--iso-pjm'
 * @returns {string} The resolved color string (e.g. '#0EA5E9')
 */
export function cssColor(varName) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();
}

/* ---------------------------------------------------------------------------
   3. fuelColorScale — D3 ordinal scale for fuel types
   --------------------------------------------------------------------------- */

/**
 * Returns a D3 ordinal scale mapping canonical fuel-type strings to
 * Observatory CSS color vars.
 *
 * @returns {d3.ScaleOrdinal}
 */
export function fuelColorScale() {
  const fuel = {
    solar:       cssColor('--solar')       || '#F59E0B',
    wind:        cssColor('--wind')        || '#22C55E',
    offshore:    cssColor('--offshore')    || '#009688',
    hydro:       cssColor('--hydro')       || '#0EA5E9',
    nuclear:     cssColor('--nuclear')     || '#6366F1',
    'fossil-gas':  cssColor('--fossil-gas')  || '#6B7280',
    gas:           cssColor('--fossil-gas')  || '#6B7280',
    'fossil-coal': cssColor('--fossil-coal') || '#374151',
    coal:          cssColor('--fossil-coal') || '#374151',
    storage:     cssColor('--storage')     || '#E67E22',
    battery:     cssColor('--storage')     || '#E67E22',
    oil:         cssColor('--oil')         || '#92400E',
    ccs:         cssColor('--ccs')         || '#26A69A',
    hydrogen:    cssColor('--hydrogen')    || '#10B981',
    geothermal:  cssColor('--geothermal')  || '#D97706',
  };

  return d3.scaleOrdinal()
    .domain(Object.keys(fuel))
    .range(Object.values(fuel))
    .unknown('#94A3B8');
}

/* ---------------------------------------------------------------------------
   4. isoColorScale — D3 ordinal scale for ISOs
   --------------------------------------------------------------------------- */

/**
 * Returns a D3 ordinal scale mapping ISO names to Observatory ISO CSS vars.
 *
 * @returns {d3.ScaleOrdinal}
 */
export function isoColorScale() {
  const iso = {
    caiso:  cssColor('--iso-caiso')  || '#F59E0B',
    CAISO:  cssColor('--iso-caiso')  || '#F59E0B',
    ercot:  cssColor('--iso-ercot')  || '#22C55E',
    ERCOT:  cssColor('--iso-ercot')  || '#22C55E',
    pjm:    cssColor('--iso-pjm')    || '#0EA5E9',
    PJM:    cssColor('--iso-pjm')    || '#0EA5E9',
    nyiso:  cssColor('--iso-nyiso')  || '#E91E63',
    NYISO:  cssColor('--iso-nyiso')  || '#E91E63',
    neiso:  cssColor('--iso-neiso')  || '#9C27B0',
    NEISO:  cssColor('--iso-neiso')  || '#9C27B0',
    miso:   cssColor('--iso-miso')   || '#F97316',
    MISO:   cssColor('--iso-miso')   || '#F97316',
    spp:    cssColor('--iso-spp')    || '#14B8A6',
    SPP:    cssColor('--iso-spp')    || '#14B8A6',
    soco:   cssColor('--iso-soco')   || '#6366F1',
    SOCO:   cssColor('--iso-soco')   || '#6366F1',
  };

  return d3.scaleOrdinal()
    .domain(Object.keys(iso))
    .range(Object.values(iso))
    .unknown('#94A3B8');
}

/* ---------------------------------------------------------------------------
   5. addTooltip — Create a positioned tooltip <div>
   --------------------------------------------------------------------------- */

/**
 * Create (or reuse) a floating tooltip div with show/hide API.
 *
 * @param {string} [className='tooltip'] - CSS class for the tooltip element
 * @returns {{ el: HTMLElement, show(html:string, event:MouseEvent):void, hide():void }}
 */
export function addTooltip(className = 'tooltip') {
  // Reuse existing or create new
  let el = document.querySelector(`.${className}`);
  if (!el) {
    el = document.createElement('div');
    el.className = className;
    document.body.appendChild(el);
  }

  let hideTimer = null;

  function show(html, event) {
    if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    el.innerHTML = html;
    el.classList.add('visible');
    position(event);
  }

  function position(event) {
    if (!event) return;
    const margin = 14;
    const tipW = el.offsetWidth;
    const tipH = el.offsetHeight;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let left = event.clientX + margin;
    let top  = event.clientY + margin;

    if (left + tipW > vw - 8)  left = event.clientX - tipW - margin;
    if (top  + tipH > vh - 8)  top  = event.clientY - tipH - margin;

    el.style.left = `${Math.max(8, left)}px`;
    el.style.top  = `${Math.max(8, top)}px`;
  }

  function hide() {
    hideTimer = setTimeout(() => { el.classList.remove('visible'); }, 80);
  }

  // Track mouse for repositioning
  document.addEventListener('mousemove', e => {
    if (el.classList.contains('visible')) position(e);
  });

  return { el, show, hide, position };
}

/* ---------------------------------------------------------------------------
   6. Number formatters
   --------------------------------------------------------------------------- */

const _mwFmt  = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
const _mwhFmt = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
const _priceFmt = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 1,
});
const _pctFmt = new Intl.NumberFormat('en-US', {
  style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1,
});

/**
 * Format a MW/GW value compactly.
 * @param {number} value - value in MW
 * @returns {string} e.g. "12.4 GW", "850 MW"
 */
export function formatMW(value) {
  if (Math.abs(value) >= 1000) {
    return `${(value / 1000).toFixed(1)} GW`;
  }
  return `${Math.round(value)} MW`;
}

/**
 * Format a MWh/GWh value compactly.
 * @param {number} value - value in MWh
 * @returns {string} e.g. "4.2 TWh", "850 GWh"
 */
export function formatMWh(value) {
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(1)} TWh`;
  if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(1)} GWh`;
  return `${Math.round(value)} MWh`;
}

/**
 * Format a price in $/MWh.
 * @param {number} value
 * @returns {string} e.g. "$45.20/MWh"
 */
export function formatPrice(value) {
  const abs = Math.abs(value);
  const formatted = abs < 10
    ? `$${value.toFixed(2)}`
    : `$${Math.round(value)}`;
  return `${formatted}/MWh`;
}

/**
 * Format a ratio as a percentage.
 * @param {number} value - 0–1 fraction
 * @returns {string} e.g. "42.3%"
 */
export function formatPct(value) {
  return _pctFmt.format(value);
}

/**
 * Format a year range or single year.
 * @param {number} year
 * @returns {string}
 */
export function formatYear(year) {
  return String(Math.round(year));
}

/* ---------------------------------------------------------------------------
   7. Axis helpers
   --------------------------------------------------------------------------- */

/**
 * Create a D3 axis with the Observatory style (no domain line, light ticks).
 *
 * @param {'x'|'y'} axis - axis direction
 * @param {d3.Scale} scale
 * @param {object} [opts]
 * @param {number} [opts.ticks=5]
 * @param {function} [opts.tickFormat]
 * @returns {d3.Axis}
 */
export function makeAxis(axis, scale, opts = {}) {
  const fn = axis === 'x' ? d3.axisBottom(scale) : d3.axisLeft(scale);
  fn.ticks(opts.ticks || 5);
  if (opts.tickFormat) fn.tickFormat(opts.tickFormat);
  fn.tickSize(opts.tickSize !== undefined ? opts.tickSize : -3);
  return fn;
}

/**
 * Apply Observatory axis styling to an SVG <g> selection.
 * @param {d3.Selection} g - the axis <g>
 */
export function styleAxis(g) {
  g.select('.domain').remove();
  g.selectAll('.tick line')
    .attr('stroke', 'rgba(0,0,0,0.12)')
    .attr('stroke-dasharray', '3,3');
  g.selectAll('.tick text')
    .attr('fill', '#566370')
    .attr('font-size', '11px')
    .attr('font-family', "'DM Sans', sans-serif");
}

/**
 * Apply Observatory axis styling for dark-background SVGs.
 * @param {d3.Selection} g
 */
export function styleAxisDark(g) {
  g.select('.domain').remove();
  g.selectAll('.tick line')
    .attr('stroke', 'rgba(255,255,255,0.15)')
    .attr('stroke-dasharray', '3,3');
  g.selectAll('.tick text')
    .attr('fill', 'rgba(255,255,255,0.55)')
    .attr('font-size', '11px')
    .attr('font-family', "'DM Sans', sans-serif");
}

/* ---------------------------------------------------------------------------
   8. Margin convention helper
   --------------------------------------------------------------------------- */

/**
 * Standard Observatory chart margin object.
 *
 * @param {object} [overrides]
 * @returns {{ top:number, right:number, bottom:number, left:number }}
 */
export function margin(overrides = {}) {
  return { top: 16, right: 20, bottom: 36, left: 52, ...overrides };
}
