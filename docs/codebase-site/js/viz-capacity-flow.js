/**
 * viz-capacity-flow.js — V16 animated 6-step capacity evolution flowchart
 * Used on: capacity-evolution.html
 *
 * Animated flowchart: six connected boxes representing the annual capacity
 * evolution loop. Play/step controls advance through steps one at a time.
 */

import {
  responsiveChart,
  cssColor,
  addTooltip,
} from './chart-utils.js';

document.addEventListener('DOMContentLoaded', initCapacityFlow);

const STEPS = [
  {
    id: 'known-ret',
    label: 'Known\nRetirements',
    short: 'Known Ret.',
    color: '#EF4444',
    icon: '🔻',
    description: 'Drop units past their scheduled retirement date. These are firm closures announced to the ISO — regulatory deadlines, fuel-supply expirations, or owner decisions already filed.',
  },
  {
    id: 'econ-ret',
    label: 'Economic\nRetirements',
    short: 'Econ. Ret.',
    color: '#F97316',
    icon: '📉',
    description: 'Screen each thermal unit\'s inframarginal energy margin against its going-forward FOM cost. If margin < FOM for N consecutive years (coal: 1yr, gas-CT: 2yr, gas-CC: 3yr), the unit retires — subject to a reliability floor.',
  },
  {
    id: 'known-add',
    label: 'Known\nAdditions',
    short: 'Known Add.',
    color: '#22C55E',
    icon: '🏗️',
    description: 'Add units from the EIA-860 proposed pipeline that are construction-committed. These are real projects with signed interconnection agreements and financing — not speculative filings.',
  },
  {
    id: 'ccs-retro',
    label: 'CCS\nRetrofits',
    short: 'CCS Retro.',
    color: '#0EA5E9',
    icon: '🔄',
    description: 'Screen existing gas-CC units with ≥15 years remaining life for CCS retrofit. If simple payback < remaining life, retrofit proceeds — capped at 3 GW/yr/ISO, gated on ccs_retrofit_available_year.',
  },
  {
    id: 'econ-entry',
    label: 'Economic\nNew Entry',
    short: 'New Entry',
    color: '#6366F1',
    icon: '⚡',
    description: 'Compare each technology\'s LCOE (with Wright\'s-Law learning) against expected revenue from the prior year\'s price distribution. Technologies that clear the hurdle enter a per-tech queue with annual build caps.',
  },
  {
    id: 'reserve-margin',
    label: 'Reserve-Margin\nBackstop',
    short: 'Backstop',
    color: '#F59E0B',
    icon: '🛡️',
    description: 'After all market-driven changes, check whether firm capacity meets the planning reserve margin (peak × 1.15). If short, force-build gas-CT units to close the gap — the reliability floor.',
  },
];

async function initCapacityFlow() {
  const container = document.getElementById('capacity-flow-container');
  if (!container) return;

  const state = { activeStep: -1, playing: false, timer: null };

  function draw(width, height) {
    d3.select(container).selectAll('svg').remove();

    const isMobile = width < 600;
    const m = { top: 20, right: 20, bottom: 20, left: 20 };
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('role', 'img')
      .attr('aria-label', 'Six-step capacity evolution flowchart');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    const defs = svg.append('defs');
    defs.append('marker')
      .attr('id', 'flow-arrow')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 10)
      .attr('refY', 5)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,0 L10,5 L0,10 Z')
      .attr('fill', 'rgba(148,163,184,0.6)');

    const n = STEPS.length;
    let boxW, boxH, positions;

    if (isMobile) {
      boxW = Math.min(w * 0.75, 200);
      boxH = 52;
      const gap = (h - n * boxH) / (n - 1);
      positions = STEPS.map((_, i) => ({
        x: (w - boxW) / 2,
        y: i * (boxH + Math.max(gap, 12)),
      }));
    } else {
      const cols = 3;
      const rows = 2;
      boxW = Math.min((w - 80) / cols, 190);
      boxH = 60;
      const gapX = (w - cols * boxW) / (cols - 1);
      const gapY = (h - rows * boxH) / (rows - 1);
      positions = STEPS.map((_, i) => {
        const row = Math.floor(i / cols);
        const col = row === 0 ? i : (cols - 1) - (i - cols);
        return {
          x: col * (boxW + gapX),
          y: row * (boxH + Math.max(gapY, 40)),
        };
      });
    }

    // Draw connecting arrows
    for (let i = 0; i < n - 1; i++) {
      const from = positions[i];
      const to = positions[i + 1];
      const fromCx = from.x + boxW / 2;
      const fromCy = from.y + boxH / 2;
      const toCx = to.x + boxW / 2;
      const toCy = to.y + boxH / 2;

      let x1, y1, x2, y2;
      if (isMobile) {
        x1 = fromCx; y1 = from.y + boxH;
        x2 = toCx; y2 = to.y;
      } else if (i === 2) {
        x1 = from.x + boxW; y1 = fromCy;
        x2 = to.x + boxW; y2 = toCy;
      } else if (Math.abs(fromCy - toCy) < 5) {
        const goingRight = toCx > fromCx;
        x1 = goingRight ? from.x + boxW : from.x;
        y1 = fromCy;
        x2 = goingRight ? to.x : to.x + boxW;
        y2 = toCy;
      } else {
        x1 = fromCx; y1 = from.y + boxH;
        x2 = toCx; y2 = to.y;
      }

      const arrow = g.append('line')
        .attr('class', `flow-arrow flow-arrow-${i}`)
        .attr('x1', x1).attr('y1', y1)
        .attr('x2', x2).attr('y2', y2)
        .attr('stroke', 'rgba(148,163,184,0.4)')
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#flow-arrow)');

      if (state.activeStep >= i + 1) {
        arrow.attr('stroke', STEPS[i].color).attr('stroke-opacity', 0.8);
      }
    }

    // Loop-back arrow (step 6 -> step 1 for next year)
    if (!isMobile) {
      const last = positions[n - 1];
      const first = positions[0];
      const loopPath = `M${last.x},${last.y + boxH / 2} ` +
        `Q${-30},${(last.y + first.y + boxH) / 2} ${first.x},${first.y + boxH / 2}`;
      g.append('path')
        .attr('d', loopPath)
        .attr('fill', 'none')
        .attr('stroke', 'rgba(148,163,184,0.2)')
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '6,4')
        .attr('marker-end', 'url(#flow-arrow)');
      g.append('text')
        .attr('x', -10)
        .attr('y', (last.y + first.y + boxH) / 2)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', 'rgba(148,163,184,0.5)')
        .attr('font-family', "'DM Sans', sans-serif")
        .attr('transform', `rotate(-90, -10, ${(last.y + first.y + boxH) / 2})`)
        .text('Next Year →');
    }

    // Draw step boxes
    STEPS.forEach((step, i) => {
      const pos = positions[i];
      const isActive = i === state.activeStep;
      const isPast = i < state.activeStep;

      const box = g.append('g')
        .attr('class', `step-box step-box-${i}`)
        .attr('transform', `translate(${pos.x},${pos.y})`)
        .style('cursor', 'pointer');

      // Background rect
      box.append('rect')
        .attr('width', boxW)
        .attr('height', boxH)
        .attr('rx', 10)
        .attr('fill', isActive ? step.color : (isPast ? step.color : 'rgba(30,41,59,0.6)'))
        .attr('fill-opacity', isActive ? 0.25 : (isPast ? 0.12 : 1))
        .attr('stroke', isActive ? step.color : (isPast ? step.color : 'rgba(148,163,184,0.25)'))
        .attr('stroke-width', isActive ? 2.5 : (isPast ? 1.5 : 1))
        .attr('stroke-opacity', isActive ? 1 : (isPast ? 0.6 : 1));

      // Step number badge
      box.append('circle')
        .attr('cx', 18)
        .attr('cy', 16)
        .attr('r', 10)
        .attr('fill', isActive ? step.color : (isPast ? step.color : 'rgba(148,163,184,0.3)'))
        .attr('fill-opacity', isActive ? 0.9 : (isPast ? 0.5 : 0.6));

      box.append('text')
        .attr('x', 18)
        .attr('y', 20)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '700')
        .attr('fill', isActive ? '#fff' : (isPast ? '#fff' : 'rgba(255,255,255,0.7)'))
        .attr('font-family', "'DM Sans', sans-serif")
        .text(i + 1);

      // Label
      const lines = step.short.split('\n');
      lines.forEach((line, li) => {
        box.append('text')
          .attr('x', 36)
          .attr('y', boxH / 2 + (li - (lines.length - 1) / 2) * 16 + 1)
          .attr('font-size', isMobile ? '11px' : '13px')
          .attr('font-weight', '600')
          .attr('fill', isActive ? '#F1F5F9' : (isPast ? 'rgba(241,245,249,0.75)' : 'rgba(241,245,249,0.55)'))
          .attr('font-family', "'DM Sans', sans-serif")
          .text(line);
      });

      // Click handler
      box.on('click', () => {
        state.activeStep = i;
        updateExplanation(state.activeStep);
        draw(width, height);
      });
    });
  }

  function updateExplanation(stepIdx) {
    const panel = document.getElementById('step-explanation');
    if (!panel) return;

    if (stepIdx < 0 || stepIdx >= STEPS.length) {
      panel.innerHTML = '<p class="step-prompt">Click a step or press Play to walk through the six-step annual capacity evolution loop.</p>';
      return;
    }

    const step = STEPS[stepIdx];
    panel.innerHTML = `
      <div class="step-detail" style="border-left: 3px solid ${step.color}; padding-left: 16px;">
        <div class="step-detail__header">
          <span class="step-detail__icon">${step.icon}</span>
          <strong>Step ${stepIdx + 1}: ${step.label.replace('\n', ' ')}</strong>
        </div>
        <p>${step.description}</p>
      </div>
    `;
  }

  // Play/step controls
  const playBtn = document.getElementById('flow-play');
  const stepBtn = document.getElementById('flow-step');
  const resetBtn = document.getElementById('flow-reset');

  if (stepBtn) {
    stepBtn.addEventListener('click', () => {
      stopPlaying(state);
      state.activeStep = (state.activeStep + 1) % STEPS.length;
      updateExplanation(state.activeStep);
      const w = container.clientWidth;
      const h = container.clientHeight || Math.round(w * 0.5);
      draw(w, h);
    });
  }

  if (playBtn) {
    playBtn.addEventListener('click', () => {
      if (state.playing) {
        stopPlaying(state);
        playBtn.textContent = '▶ Play';
        return;
      }
      state.playing = true;
      playBtn.textContent = '⏸ Pause';

      function advance() {
        if (!state.playing) return;
        state.activeStep = (state.activeStep + 1) % STEPS.length;
        updateExplanation(state.activeStep);
        const w = container.clientWidth;
        const h = container.clientHeight || Math.round(w * 0.5);
        draw(w, h);
        state.timer = setTimeout(advance, 1800);
      }
      advance();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      stopPlaying(state);
      if (playBtn) playBtn.textContent = '▶ Play';
      state.activeStep = -1;
      updateExplanation(-1);
      const w = container.clientWidth;
      const h = container.clientHeight || Math.round(w * 0.5);
      draw(w, h);
    });
  }

  function stopPlaying(s) {
    s.playing = false;
    if (s.timer) { clearTimeout(s.timer); s.timer = null; }
  }

  updateExplanation(-1);
  responsiveChart(container, (w, h) => draw(w, h));
}

export { STEPS };
