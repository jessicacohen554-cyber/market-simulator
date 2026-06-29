/**
 * viz-price-duration.js — V13
 * Price-duration curve for the Solving & Pricing page.
 * Loads data/price-duration.json and renders a D3 step-line chart with:
 *   - Log-scale toggle
 *   - Hover crosshair + tooltip
 *   - Three annotated price regions (scarcity, baseload, surplus)
 *   - Responsive via ResizeObserver
 */

import { responsiveChart, addTooltip, margin, styleAxisDark } from './chart-utils.js';

/* ---------------------------------------------------------------------------
   Constants
   --------------------------------------------------------------------------- */

const CONTAINER_ID = 'v13-pdc';

const REGIONS = [
  {
    label: 'Scarcity tail',
    sub: '>$95/MWh — peaking units, VOLL events',
    hourEnd: 95,
    color: '#F87171',
    textColor: '#FCA5A5',
    anchorX: 47,
    anchorY: 150,
  },
  {
    label: 'Baseload plateau',
    sub: '$25–$45/MWh — thermal sets the price',
    hourStart: 1565,
    hourEnd: 5765,
    color: '#60A5FA',
    textColor: '#93C5FD',
    anchorX: 3665,
    anchorY: 36,
  },
  {
    label: 'Renewable surplus',
    sub: '<$15/MWh — wind/solar excess',
    hourStart: 8215,
    hourEnd: 8485,
    color: '#34D399',
    textColor: '#6EE7B7',
    anchorX: 8350,
    anchorY: 10,
  },
];

/* ---------------------------------------------------------------------------
   Data helpers
   --------------------------------------------------------------------------- */

/**
 * Expand the compressed JSON segments into a step-function point array.
 * Each segment (hours_at_level + price) becomes two points: (startHour, price)
 * and (endHour, price), creating a staircase shape.
 *
 * @param {Array} segments - from price-duration.json .prices_sorted_descending
 * @returns {Array<{hour: number, price: number}>}
 */
function expandSegments(segments) {
  const pts = [];
  let cumHour = 0;
  for (const seg of segments) {
    pts.push({ hour: cumHour, price: seg.price_per_mwh });
    cumHour += seg.hours_at_level;
    pts.push({ hour: cumHour, price: seg.price_per_mwh });
  }
  return pts;
}

/* ---------------------------------------------------------------------------
   Chart
   --------------------------------------------------------------------------- */

let logScale = false;
let chartData = null;
let redrawFn = null;

function draw(container, data, width, height) {
  const m = margin({ top: 32, right: 48, bottom: 44, left: 64 });
  const innerW = width - m.left - m.right;
  const innerH = height - m.top - m.bottom;

  // Clear
  d3.select(container).selectAll('*').remove();

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('role', 'img')
    .attr('aria-label', 'Price-duration curve: 8,760 hourly prices sorted descending');

  svg.append('title').text('Price-duration curve');
  svg.append('desc').text(
    'All hours of the year sorted from highest to lowest price. ' +
    'Shows the scarcity tail, baseload plateau, and renewable surplus trough.'
  );

  const g = svg.append('g')
    .attr('transform', `translate(${m.left},${m.top})`);

  // Scales
  const maxHour = d3.max(data, d => d.hour) || 8760;
  const xScale = d3.scaleLinear().domain([0, maxHour]).range([0, innerW]);

  const prices = data.map(d => d.price);
  const minPrice = d3.min(prices);
  const maxPrice = d3.max(prices);

  let yScale;
  if (logScale) {
    const logMin = Math.max(1, minPrice); // clamp negatives for log
    yScale = d3.scaleLog()
      .domain([logMin, maxPrice])
      .range([innerH, 0])
      .clamp(true)
      .nice();
  } else {
    yScale = d3.scaleLinear()
      .domain([Math.min(0, minPrice), maxPrice])
      .range([innerH, 0])
      .nice();
  }

  // Background: subtle region bands
  const regionDefs = [
    { x0: 0,    x1: 95,   color: 'rgba(248,113,113,0.07)' },
    { x0: 1565, x1: 5765, color: 'rgba(96,165,250,0.06)'  },
    { x0: 8215, x1: maxHour, color: 'rgba(52,211,153,0.07)' },
  ];
  regionDefs.forEach(r => {
    g.append('rect')
      .attr('x', xScale(r.x0))
      .attr('width', Math.max(0, xScale(r.x1) - xScale(r.x0)))
      .attr('y', 0)
      .attr('height', innerH)
      .attr('fill', r.color)
      .attr('pointer-events', 'none');
  });

  // Grid lines
  const yTicks = yScale.ticks(6);
  g.selectAll('.grid-y')
    .data(yTicks)
    .join('line')
    .attr('class', 'grid-y')
    .attr('x1', 0).attr('x2', innerW)
    .attr('y1', d => yScale(d)).attr('y2', d => yScale(d))
    .attr('stroke', 'rgba(255,255,255,0.07)')
    .attr('stroke-dasharray', '3,3');

  // Zero line
  if (!logScale && minPrice < 0) {
    g.append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', yScale(0)).attr('y2', yScale(0))
      .attr('stroke', 'rgba(255,255,255,0.20)')
      .attr('stroke-width', 0.8)
      .attr('stroke-dasharray', '4,4');
  }

  // X axis
  const xAxis = d3.axisBottom(xScale)
    .ticks(6)
    .tickFormat(d => d === 0 ? '0' : `${d3.format(',')(d)} h`);
  const xG = g.append('g').attr('transform', `translate(0,${innerH})`).call(xAxis);
  styleAxisDark(xG);

  // Y axis
  const yAxis = d3.axisLeft(yScale)
    .ticks(6)
    .tickFormat(d => `$${d}`);
  const yG = g.append('g').call(yAxis);
  styleAxisDark(yG);

  // Axis labels
  g.append('text')
    .attr('x', innerW / 2)
    .attr('y', innerH + 38)
    .attr('text-anchor', 'middle')
    .attr('fill', 'rgba(255,255,255,0.45)')
    .attr('font-size', '11px')
    .attr('font-family', "'DM Sans', sans-serif")
    .text('Hours sorted descending by price (rank)');

  g.append('text')
    .attr('transform', `rotate(-90)`)
    .attr('x', -(innerH / 2))
    .attr('y', -50)
    .attr('text-anchor', 'middle')
    .attr('fill', 'rgba(255,255,255,0.45)')
    .attr('font-size', '11px')
    .attr('font-family', "'DM Sans', sans-serif")
    .text('Price ($/MWh)');

  // Line generator
  const lineGen = d3.line()
    .x(d => xScale(d.hour))
    .y(d => {
      if (logScale && d.price < 1) return yScale(1); // clamp negatives
      return yScale(d.price);
    })
    .defined(d => !(logScale && d.price < 1));

  // Area fill under curve
  const areaGen = d3.area()
    .x(d => xScale(d.hour))
    .y0(innerH)
    .y1(d => {
      if (logScale && d.price < 1) return yScale(1);
      return yScale(d.price);
    })
    .defined(d => !(logScale && d.price < 1));

  // Gradient definition
  const gradId = `pdc-grad-${Math.random().toString(36).slice(2,7)}`;
  const defs = svg.append('defs');
  const grad = defs.append('linearGradient')
    .attr('id', gradId)
    .attr('x1', '0').attr('y1', '0').attr('x2', '1').attr('y2', '0');
  grad.append('stop').attr('offset', '0%').attr('stop-color', '#F87171').attr('stop-opacity', '0.35');
  grad.append('stop').attr('offset', '15%').attr('stop-color', '#FB923C').attr('stop-opacity', '0.20');
  grad.append('stop').attr('offset', '60%').attr('stop-color', '#60A5FA').attr('stop-opacity', '0.12');
  grad.append('stop').attr('offset', '95%').attr('stop-color', '#34D399').attr('stop-opacity', '0.18');
  grad.append('stop').attr('offset', '100%').attr('stop-color', '#34D399').attr('stop-opacity', '0.10');

  // Clip path
  const clipId = `pdc-clip-${Math.random().toString(36).slice(2,7)}`;
  defs.append('clipPath').attr('id', clipId)
    .append('rect').attr('width', innerW).attr('height', innerH);

  const chartG = g.append('g').attr('clip-path', `url(#${clipId})`);

  // Area
  chartG.append('path')
    .datum(data)
    .attr('d', areaGen)
    .attr('fill', `url(#${gradId})`)
    .attr('pointer-events', 'none');

  // Line
  chartG.append('path')
    .datum(data)
    .attr('d', lineGen)
    .attr('fill', 'none')
    .attr('stroke', '#60A5FA')
    .attr('stroke-width', 2)
    .attr('pointer-events', 'none');

  // Annotations
  const annotData = [
    { label: 'Scarcity tail', sub: '>$95 · scarcity pricing', hour: 47, price: 200, color: '#F87171' },
    { label: 'Baseload plateau', sub: '$25–$45 · thermal marginal', hour: 3665, price: 36, color: '#93C5FD' },
    { label: 'Renewable surplus', sub: '<$15 · wind/solar excess', hour: 8340, price: 9, color: '#6EE7B7' },
  ];

  annotData.forEach(ann => {
    const px = xScale(ann.hour);
    const py = logScale && ann.price < 1 ? yScale(1) : yScale(ann.price);

    if (px < 0 || px > innerW || py < 0 || py > innerH) return;

    const ag = g.append('g').attr('pointer-events', 'none');

    // Dot
    ag.append('circle').attr('cx', px).attr('cy', py).attr('r', 4)
      .attr('fill', ann.color).attr('opacity', 0.9);

    // Label box
    const isLeft = px < innerW * 0.6;
    const lx = isLeft ? px + 10 : px - 10;
    const anchor = isLeft ? 'start' : 'end';

    ag.append('text')
      .attr('x', lx).attr('y', py - 8)
      .attr('text-anchor', anchor)
      .attr('fill', ann.color)
      .attr('font-size', '10px')
      .attr('font-weight', '700')
      .attr('font-family', "'DM Sans', sans-serif")
      .text(ann.label);

    ag.append('text')
      .attr('x', lx).attr('y', py + 5)
      .attr('text-anchor', anchor)
      .attr('fill', 'rgba(255,255,255,0.50)')
      .attr('font-size', '8.5px')
      .attr('font-family', "'DM Sans', sans-serif")
      .text(ann.sub);
  });

  // Hover crosshair + tooltip
  const tooltip = addTooltip('tooltip');

  const bisector = d3.bisector(d => d.hour).left;

  const overlay = g.append('rect')
    .attr('width', innerW)
    .attr('height', innerH)
    .attr('fill', 'transparent')
    .attr('cursor', 'crosshair');

  const crossV = g.append('line')
    .attr('y1', 0).attr('y2', innerH)
    .attr('stroke', 'rgba(255,255,255,0.35)')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')
    .attr('pointer-events', 'none')
    .attr('opacity', 0);

  const crossDot = g.append('circle')
    .attr('r', 5)
    .attr('fill', '#60A5FA')
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .attr('pointer-events', 'none')
    .attr('opacity', 0);

  overlay.on('mousemove', function (event) {
    const [mx] = d3.pointer(event);
    const hour = xScale.invert(mx);
    const idx = bisector(data, hour, 1);
    const d0 = data[idx - 1];
    const d1 = data[idx];
    if (!d0 && !d1) return;
    const d = !d1 ? d0 : !d0 ? d1 :
      (hour - d0.hour < d1.hour - hour ? d0 : d1);

    const px = xScale(d.hour);
    const py = logScale && d.price < 1 ? yScale(1) : yScale(d.price);

    crossV.attr('x1', px).attr('x2', px).attr('opacity', 1);
    crossDot.attr('cx', px).attr('cy', py).attr('opacity', 1);

    // Compute approximate rank (hours from left)
    const rank = Math.round(d.hour) + 1;

    tooltip.show(`
      <div class="tooltip__title">Hour rank ${rank}</div>
      <div class="tooltip__row">
        <span class="tooltip__key">Price</span>
        <span class="tooltip__val">${d.price >= 0 ? '$' : '-$'}${Math.abs(d.price).toFixed(0)}/MWh</span>
      </div>
      <div class="tooltip__row">
        <span class="tooltip__key">Hour</span>
        <span class="tooltip__val">${Math.round(d.hour).toLocaleString()}</span>
      </div>
    `, event);
  });

  overlay.on('mouseleave', function () {
    crossV.attr('opacity', 0);
    crossDot.attr('opacity', 0);
    tooltip.hide();
  });
}

/* ---------------------------------------------------------------------------
   Bootstrap
   --------------------------------------------------------------------------- */

async function init() {
  const container = document.getElementById(CONTAINER_ID);
  if (!container) return;

  // Load data
  let rawData;
  try {
    const res = await fetch('data/price-duration.json');
    rawData = await res.json();
  } catch (e) {
    console.error('viz-price-duration: failed to load data', e);
    container.innerHTML = '<p style="color:rgba(255,255,255,0.5);padding:20px;text-align:center;">Data unavailable</p>';
    return;
  }

  chartData = expandSegments(rawData.prices_sorted_descending);

  // Set up toggle button
  const toggleBtn = document.getElementById('v13-log-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      logScale = !logScale;
      toggleBtn.textContent = logScale ? 'Linear scale' : 'Log scale';
      toggleBtn.setAttribute('aria-pressed', logScale ? 'true' : 'false');
      if (redrawFn) redrawFn();
    });
  }

  // Responsive chart
  const handle = responsiveChart(container, (w, h) => {
    const chartH = Math.max(280, Math.min(h, 420));
    draw(container, chartData, w, chartH);
  });

  // Store redraw reference (calls the observer which fires drawFn)
  redrawFn = () => {
    const w = container.clientWidth;
    const chartH = Math.max(280, Math.min(container.clientHeight || w * 0.5, 420));
    draw(container, chartData, w, chartH);
  };
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
