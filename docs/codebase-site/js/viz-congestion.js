/**
 * viz-congestion.js — V15: Congestion & price separation chart
 *
 * Two-line price chart (zone_north_lmp / zone_houston_lmp) over illustrative
 * 9-hour window. Shaded band highlights hours when flow binds the TTC.
 * Flow-vs-TTC bar chart + hour scrubber below the price chart.
 *
 * Data: data/congestion-example.json
 * Mount: #viz-congestion
 */

import { addTooltip, cssColor, margin, styleAxis } from './chart-utils.js';

const DATA_URL = 'data/congestion-example.json';
const MOUNT_ID = 'viz-congestion';

const COLOR_NORTH   = '#0EA5E9';   /* sky blue  */
const COLOR_HOUSTON = '#E91E63';   /* pink/red  */
const COLOR_BAND    = '#F59E0B';   /* amber     */
const COLOR_FLOW    = '#0EA5E9';
const COLOR_TTC     = '#EF4444';

async function init() {
  const container = document.getElementById(MOUNT_ID);
  if (!container) return;

  let data;
  try {
    const resp = await fetch('data/congestion-example.json');
    data = await resp.json();
  } catch (e) {
    container.innerHTML = '<p style="color:#94A3B8;padding:2rem;text-align:center">Could not load congestion data.</p>';
    return;
  }

  const hours = data.hours || [];
  if (!hours.length) return;

  renderPriceChart(container, hours);
  renderFlowBar(container, hours);
  setupScrubber(container, hours);
}

/* ---------------------------------------------------------------------------
   Price chart
   --------------------------------------------------------------------------- */
function renderPriceChart(container, hours) {
  const chartEl = container.querySelector('.congestion-price-chart');
  if (!chartEl) return;

  const m = margin({ top: 24, right: 24, bottom: 36, left: 56 });
  const W = chartEl.clientWidth || 700;
  const H = 260;
  const iW = W - m.left - m.right;
  const iH = H - m.top - m.bottom;

  const svg = d3.select(chartEl)
    .append('svg')
    .attr('width', '100%')
    .attr('height', H)
    .attr('viewBox', `0 0 ${W} ${H}`);

  const g = svg.append('g').attr('transform', `translate(${m.left},${m.top})`);

  /* Scales */
  const xScale = d3.scalePoint()
    .domain(hours.map(d => d.hour))
    .range([0, iW])
    .padding(0.3);

  const allPrices = hours.flatMap(d => [d.zone_north_lmp, d.zone_houston_lmp]);
  const yScale = d3.scaleLinear()
    .domain([0, d3.max(allPrices) * 1.12])
    .range([iH, 0])
    .nice();

  /* Shaded congestion band */
  const constrained = hours.filter(d => d.flow_constrained);
  if (constrained.length) {
    const bandData = [];
    let inBand = false;
    let bandStart = null;
    hours.forEach((d, i) => {
      if (d.flow_constrained && !inBand) {
        inBand = true;
        bandStart = i;
      } else if (!d.flow_constrained && inBand) {
        bandData.push({ start: bandStart, end: i - 1 });
        inBand = false;
        bandStart = null;
      }
    });
    if (inBand) bandData.push({ start: bandStart, end: hours.length - 1 });

    bandData.forEach(band => {
      const hFrom = hours[band.start];
      const hTo   = hours[band.end];
      const xFrom = xScale(hFrom.hour);
      const xTo   = xScale(hTo.hour);
      const bandW = xTo - xFrom + xScale.step() * (1 - xScale.padding());

      g.append('rect')
        .attr('x', xFrom - xScale.step() * (1 - xScale.padding()) * 0.5)
        .attr('y', 0)
        .attr('width', Math.max(bandW, xScale.step()))
        .attr('height', iH)
        .attr('fill', COLOR_BAND)
        .attr('opacity', 0.10)
        .attr('rx', 3);

      /* "Binding" label */
      g.append('text')
        .attr('x', xFrom + (xTo - xFrom) / 2)
        .attr('y', 10)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '700')
        .attr('font-family', 'DM Sans, sans-serif')
        .attr('fill', COLOR_BAND)
        .attr('opacity', 0.85)
        .text('BINDING');
    });
  }

  /* Grid lines */
  g.append('g')
    .attr('class', 'grid')
    .call(
      d3.axisLeft(yScale)
        .ticks(5)
        .tickSize(-iW)
        .tickFormat('')
    )
    .call(gg => {
      gg.select('.domain').remove();
      gg.selectAll('.tick line')
        .attr('stroke', 'rgba(255,255,255,0.06)')
        .attr('stroke-dasharray', '3,3');
    });

  /* Lines */
  const lineNorth = d3.line()
    .x(d => xScale(d.hour))
    .y(d => yScale(d.zone_north_lmp))
    .curve(d3.curveMonotoneX);

  const lineHouston = d3.line()
    .x(d => xScale(d.hour))
    .y(d => yScale(d.zone_houston_lmp))
    .curve(d3.curveMonotoneX);

  g.append('path')
    .datum(hours)
    .attr('fill', 'none')
    .attr('stroke', COLOR_NORTH)
    .attr('stroke-width', 2.5)
    .attr('d', lineNorth);

  g.append('path')
    .datum(hours)
    .attr('fill', 'none')
    .attr('stroke', COLOR_HOUSTON)
    .attr('stroke-width', 2.5)
    .attr('stroke-dasharray', '6 3')
    .attr('d', lineHouston);

  /* Dots */
  [
    { key: 'zone_north_lmp',   color: COLOR_NORTH   },
    { key: 'zone_houston_lmp', color: COLOR_HOUSTON },
  ].forEach(({ key, color }) => {
    g.selectAll(`.dot-${key}`)
      .data(hours)
      .join('circle')
      .attr('class', `dot-${key}`)
      .attr('cx', d => xScale(d.hour))
      .attr('cy', d => yScale(d[key]))
      .attr('r', 4)
      .attr('fill', color)
      .attr('stroke', '#111827')
      .attr('stroke-width', 1.5);
  });

  /* Annotation arrow: "When the link binds, prices diverge" */
  const bindHour = hours.find(d => d.flow_constrained);
  if (bindHour) {
    const ax = xScale(bindHour.hour);
    const ay = yScale((bindHour.zone_north_lmp + bindHour.zone_houston_lmp) / 2);

    g.append('line')
      .attr('x1', ax + 22)
      .attr('y1', ay - 10)
      .attr('x2', ax + 60)
      .attr('y2', ay - 32)
      .attr('stroke', 'rgba(255,255,255,0.35)')
      .attr('stroke-width', 1);

    g.append('text')
      .attr('x', ax + 64)
      .attr('y', ay - 38)
      .attr('font-size', '9.5px')
      .attr('font-weight', '600')
      .attr('font-family', 'DM Sans, sans-serif')
      .attr('fill', 'rgba(255,255,255,0.65)')
      .text('Prices diverge');
  }

  /* Axes */
  g.append('g')
    .attr('transform', `translate(0,${iH})`)
    .call(d3.axisBottom(xScale)
      .tickFormat(d => `H${d}`)
    )
    .call(gg => {
      gg.select('.domain').remove();
      gg.selectAll('.tick line').remove();
      gg.selectAll('.tick text')
        .attr('fill', 'rgba(241,245,249,0.50)')
        .attr('font-size', '10px')
        .attr('font-family', 'DM Sans, sans-serif');
    });

  g.append('g')
    .call(d3.axisLeft(yScale)
      .ticks(5)
      .tickFormat(d => `$${d}`)
    )
    .call(gg => {
      gg.select('.domain').remove();
      gg.selectAll('.tick line').remove();
      gg.selectAll('.tick text')
        .attr('fill', 'rgba(241,245,249,0.50)')
        .attr('font-size', '10px')
        .attr('font-family', 'DM Sans, sans-serif');
    });

  /* Y-axis label */
  g.append('text')
    .attr('transform', `rotate(-90)`)
    .attr('x', -iH / 2)
    .attr('y', -44)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-family', 'DM Sans, sans-serif')
    .attr('fill', 'rgba(241,245,249,0.40)')
    .text('LMP ($/MWh)');

  /* Tooltip interaction via vertical probe */
  const probe = g.append('line')
    .attr('class', 'probe')
    .attr('y1', 0)
    .attr('y2', iH)
    .attr('stroke', 'rgba(255,255,255,0.25)')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '4 3')
    .attr('opacity', 0);

  const tip = addTooltip('tooltip');

  svg.on('mousemove', (event) => {
    const [mx] = d3.pointer(event, g.node());
    const step = xScale.step();
    const closest = hours.reduce((best, d) => {
      const dx = Math.abs(xScale(d.hour) - mx);
      return dx < Math.abs(xScale(best.hour) - mx) ? d : best;
    }, hours[0]);

    const px = xScale(closest.hour);
    probe.attr('x1', px).attr('x2', px).attr('opacity', 1);

    let html = `<div class="tooltip__title">Hour ${closest.hour}</div>`;
    html += `<div class="tooltip__row"><span class="tooltip__key"><span class="tooltip__swatch" style="background:${COLOR_NORTH}"></span>North LMP</span><span class="tooltip__val">$${closest.zone_north_lmp}/MWh</span></div>`;
    html += `<div class="tooltip__row"><span class="tooltip__key"><span class="tooltip__swatch" style="background:${COLOR_HOUSTON}"></span>Houston LMP</span><span class="tooltip__val">$${closest.zone_houston_lmp}/MWh</span></div>`;
    if (closest.price_spread > 0) {
      html += `<div class="tooltip__row"><span class="tooltip__key">Spread</span><span class="tooltip__val" style="color:${COLOR_BAND}">+$${closest.price_spread}/MWh</span></div>`;
    }
    html += `<div class="tooltip__row"><span class="tooltip__key">Flow</span><span class="tooltip__val">${(closest.net_flow_n_to_h / 1000).toFixed(1)} GW ${closest.flow_constrained ? '🔒' : ''}</span></div>`;
    tip.show(html, event);
  });

  svg.on('mouseleave', () => {
    probe.attr('opacity', 0);
    tip.hide();
  });
}

/* ---------------------------------------------------------------------------
   Flow bar chart
   --------------------------------------------------------------------------- */
function renderFlowBar(container, hours) {
  const chartEl = container.querySelector('.congestion-flow-chart');
  if (!chartEl) return;

  const m = margin({ top: 16, right: 24, bottom: 36, left: 56 });
  const W = chartEl.clientWidth || 700;
  const H = 130;
  const iW = W - m.left - m.right;
  const iH = H - m.top - m.bottom;

  const svg = d3.select(chartEl)
    .append('svg')
    .attr('width', '100%')
    .attr('height', H)
    .attr('viewBox', `0 0 ${W} ${H}`);

  const g = svg.append('g').attr('transform', `translate(${m.left},${m.top})`);

  const xScale = d3.scaleBand()
    .domain(hours.map(d => d.hour))
    .range([0, iW])
    .padding(0.25);

  const maxTTC = d3.max(hours, d => d.ttc_limit);
  const yScale = d3.scaleLinear()
    .domain([0, maxTTC * 1.05])
    .range([iH, 0]);

  /* TTC line */
  const yTTC = yScale(hours[0].ttc_limit);
  g.append('line')
    .attr('x1', 0).attr('x2', iW)
    .attr('y1', yTTC).attr('y2', yTTC)
    .attr('stroke', COLOR_TTC)
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '5 3')
    .attr('opacity', 0.70);

  g.append('text')
    .attr('x', iW - 4)
    .attr('y', yTTC - 5)
    .attr('text-anchor', 'end')
    .attr('font-size', '9px')
    .attr('font-weight', '700')
    .attr('font-family', 'DM Sans, sans-serif')
    .attr('fill', COLOR_TTC)
    .attr('opacity', 0.75)
    .text(`TTC = ${(hours[0].ttc_limit / 1000).toFixed(0)} GW`);

  /* Flow bars */
  g.selectAll('.flow-bar')
    .data(hours)
    .join('rect')
    .attr('class', 'flow-bar')
    .attr('x', d => xScale(d.hour))
    .attr('y', d => yScale(d.net_flow_n_to_h))
    .attr('width', xScale.bandwidth())
    .attr('height', d => iH - yScale(d.net_flow_n_to_h))
    .attr('fill', d => d.flow_constrained ? COLOR_BAND : COLOR_FLOW)
    .attr('fill-opacity', d => d.flow_constrained ? 0.80 : 0.50)
    .attr('rx', 2);

  /* X axis */
  g.append('g')
    .attr('transform', `translate(0,${iH})`)
    .call(d3.axisBottom(xScale).tickFormat(d => `H${d}`))
    .call(gg => {
      gg.select('.domain').remove();
      gg.selectAll('.tick line').remove();
      gg.selectAll('.tick text')
        .attr('fill', 'rgba(241,245,249,0.45)')
        .attr('font-size', '9.5px')
        .attr('font-family', 'DM Sans, sans-serif');
    });

  /* Y axis */
  g.append('g')
    .call(d3.axisLeft(yScale)
      .ticks(3)
      .tickFormat(d => `${(d / 1000).toFixed(0)} GW`)
    )
    .call(gg => {
      gg.select('.domain').remove();
      gg.selectAll('.tick line').remove();
      gg.selectAll('.tick text')
        .attr('fill', 'rgba(241,245,249,0.45)')
        .attr('font-size', '9px')
        .attr('font-family', 'DM Sans, sans-serif');
    });
}

/* ---------------------------------------------------------------------------
   Hour scrubber — highlights selected hour in both charts
   --------------------------------------------------------------------------- */
function setupScrubber(container, hours) {
  const input = container.querySelector('.hour-scrubber');
  const label = container.querySelector('.scrubber-hour-label');
  const flowVal = container.querySelector('.scrubber-flow-val');
  const spreadVal = container.querySelector('.scrubber-spread-val');

  if (!input || !label) return;

  input.min = 1;
  input.max = hours.length;
  input.value = 1;

  function update(idx) {
    const d = hours[idx] || hours[0];
    if (label)    label.textContent = `Hour ${d.hour} — ${d.datetime || ''}`;
    if (flowVal)  flowVal.textContent = `${(d.net_flow_n_to_h / 1000).toFixed(1)} GW`;
    if (spreadVal) {
      if (d.flow_constrained) {
        spreadVal.textContent = `$${d.price_spread}/MWh ⚠ binding`;
        spreadVal.style.color = '#F59E0B';
      } else {
        spreadVal.textContent = 'No congestion';
        spreadVal.style.color = 'rgba(241,245,249,0.50)';
      }
    }

    /* Highlight dots in price chart */
    const priceSvg = container.querySelector('.congestion-price-chart svg');
    if (priceSvg) {
      d3.select(priceSvg).selectAll('circle')
        .attr('r', (pd, i, nodes) => {
          const circleHour = pd.hour;
          return circleHour === d.hour ? 6 : 4;
        })
        .attr('stroke-width', (pd) => pd.hour === d.hour ? 2.5 : 1.5);
    }
  }

  input.addEventListener('input', () => update(+input.value - 1));
  update(0);
}

/* Boot */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
