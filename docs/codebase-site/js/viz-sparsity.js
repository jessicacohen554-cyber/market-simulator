/**
 * viz-sparsity.js — V8 Constraint Matrix Sparsity Pattern
 * Interactive D3 SVG visualization of the LP block-diagonal structure.
 * Schematic only — no JSON file; dimensions computed from variable counts.
 */
(function () {
  'use strict';

  /* ── Schematic model dimensions (representative ERCOT-sized instance) ─── */
  const T_SHOW = 7;   // hours displayed (illustrative slice of 8760)

  const VAR_GROUPS = [
    { id: 'P',     label: 'P[g,t]',   n: 22, color: '#4B5563', textColor: '#fff',
      desc: 'Thermal generation',  bounds: '[P_min·avail, P_max·avail]', dim: 'n_gen' },
    { id: 'W',     label: 'W[z,t]',   n: 5,  color: '#22C55E', textColor: '#fff',
      desc: 'Wind dispatched',     bounds: '[0,  CF_wind × cap]',        dim: 'n_zones' },
    { id: 'S',     label: 'S[z,t]',   n: 5,  color: '#F59E0B', textColor: '#fff',
      desc: 'Solar dispatched',    bounds: '[0,  CF_solar × cap]',       dim: 'n_zones' },
    { id: 'Chg',   label: 'Chg[s,t]', n: 8,  color: '#E67E22', textColor: '#fff',
      desc: 'Storage charge',      bounds: '[0,  P_chg_max]',            dim: 'n_storage' },
    { id: 'Dis',   label: 'Dis[s,t]', n: 8,  color: '#D97706', textColor: '#fff',
      desc: 'Storage discharge',   bounds: '[0,  P_dis_max]',            dim: 'n_storage' },
    { id: 'SOC',   label: 'SOC[s,t]', n: 8,  color: '#92400E', textColor: '#fff',
      desc: 'State of charge',     bounds: '[SOC_min, E_cap]',           dim: 'n_storage' },
    { id: 'Flow',  label: 'Flow[l,t]',n: 6,  color: '#0EA5E9', textColor: '#fff',
      desc: 'Transmission flow',   bounds: '[-TTC, +TTC]',               dim: 'n_links' },
    { id: 'Slack', label: 'Slk[z,t]', n: 5,  color: '#DC2626', textColor: '#fff',
      desc: 'Unserved energy',     bounds: '[0, ∞)',                      dim: 'n_zones' },
    { id: 'Dump',  label: 'Dmp[z,t]', n: 5,  color: '#6366F1', textColor: '#fff',
      desc: 'Overgen curtailment', bounds: '[0, ∞)',                      dim: 'n_zones' },
  ];

  const ROW_GROUPS = [
    { id: 'eb',  label: 'Energy Balance', n: 5, color: '#0369A1',
      desc: 'n_zones equality rows — dual variable = LMP ($/MWh)',
      long: 'Core market-clearing constraint. One equality row per zone per hour. The dual of each row is the Locational Marginal Price at that zone.' },
    { id: 'soc', label: 'Storage SOC',    n: 8, color: '#C2410C',
      desc: 'n_storage equality rows — SOC dynamics',
      long: 'SOC[t] − SOC[t−1] − η_chg·Chg[t] + Dis[t]/η_dis = 0. Cyclic boundary ties SOC[T] back to SOC[0]. Creates cross-hour off-diagonal blocks.' },
  ];

  /* Sparsity pattern: which blocks are nonzero.
     prevHour=true → this block is the off-diagonal coupling (SOC[t-1] in row t). */
  const SPARSITY = [
    { row: 'eb',  col: 'P',    alpha: 0.50 },
    { row: 'eb',  col: 'W',    alpha: 0.82 },
    { row: 'eb',  col: 'S',    alpha: 0.82 },
    { row: 'eb',  col: 'Chg',  alpha: 0.55 },
    { row: 'eb',  col: 'Dis',  alpha: 0.55 },
    { row: 'eb',  col: 'Flow', alpha: 0.68 },
    { row: 'eb',  col: 'Slack',alpha: 0.82 },
    { row: 'eb',  col: 'Dump', alpha: 0.82 },
    { row: 'soc', col: 'Chg',  alpha: 0.82 },
    { row: 'soc', col: 'Dis',  alpha: 0.82 },
    { row: 'soc', col: 'SOC',  alpha: 0.82 },
    { row: 'soc', col: 'SOC',  alpha: 0.48, prevHour: true },  // off-diagonal coupling
  ];

  const CPH = VAR_GROUPS.reduce((s, v) => s + v.n, 0);   // columns per hour
  const RPH = ROW_GROUPS.reduce((s, r) => s + r.n, 0);   // rows per hour

  /* ── Column / row offset lookups ──────────────────────────────────────── */
  const colOff = {};
  let _c = 0;
  VAR_GROUPS.forEach(vg => { colOff[vg.id] = _c; _c += vg.n; });

  const rowOff = {};
  let _r = 0;
  ROW_GROUPS.forEach(rg => { rowOff[rg.id] = _r; _r += rg.n; });

  /* ── Public API ────────────────────────────────────────────────────────── */
  window.VizSparsity = { init };

  function init(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    build(container);
    if ('ResizeObserver' in window) {
      let raf;
      const ro = new ResizeObserver(() => {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => build(container));
      });
      ro.observe(container);
    }
  }

  /* ── Tooltip ────────────────────────────────────────────────────────────── */
  function getTooltip() {
    let el = document.getElementById('sparsity-tt');
    if (!el) {
      el = document.createElement('div');
      el.id = 'sparsity-tt';
      el.style.cssText = [
        'position:fixed;pointer-events:none;z-index:9999;',
        'background:rgba(10,18,38,.96);color:#fff;',
        'border:1px solid rgba(255,255,255,.14);border-radius:10px;',
        'padding:10px 14px;font-size:.75rem;line-height:1.55;',
        'box-shadow:0 8px 24px rgba(0,0,0,.45);max-width:260px;',
        'opacity:0;transition:opacity 140ms ease;',
      ].join('');
      document.body.appendChild(el);
    }
    return el;
  }

  /* ── Main render ────────────────────────────────────────────────────────── */
  function build(container) {
    container.innerHTML = '';
    const W = container.clientWidth || 700;

    /* Layout constants */
    const LABEL_W  = 112;  // px reserved for row labels on left
    const TOP_PAD  = 48;   // px for column group labels at top
    const BOT_PAD  = 54;   // px for hour labels + variable labels at bottom
    const CELL     = Math.max(3, Math.min(9, Math.floor((W - LABEL_W - 12) / (CPH * T_SHOW))));
    const matW     = CPH * T_SHOW * CELL;
    const matH     = RPH * T_SHOW * CELL;
    const SVG_W    = LABEL_W + matW + 12;
    const SVG_H    = TOP_PAD + matH + BOT_PAD;

    const svg = d3.select(container)
      .append('svg')
      .attr('viewBox', `0 0 ${SVG_W} ${SVG_H}`)
      .attr('width', '100%')
      .attr('height', SVG_H)
      .attr('aria-label', 'Constraint matrix sparsity pattern — block-diagonal Kronecker structure')
      .style('display', 'block')
      .style('overflow', 'visible');

    /* Clipping for the matrix area */
    const clipId = 'sp-clip-' + Math.random().toString(36).slice(2, 7);
    svg.append('defs').append('clipPath').attr('id', clipId)
      .append('rect').attr('x', 0).attr('y', 0).attr('width', matW).attr('height', matH);

    /* Background */
    svg.append('rect')
      .attr('x', LABEL_W).attr('y', TOP_PAD)
      .attr('width', matW).attr('height', matH)
      .attr('fill', '#F8F9FC');

    /* Zoom group */
    const gOuter = svg.append('g').attr('transform', `translate(${LABEL_W},${TOP_PAD})`);
    const gClip  = gOuter.append('g').attr('clip-path', `url(#${clipId})`);
    const g      = gClip.append('g').attr('class', 'sp-inner');

    /* D3 zoom */
    const zoom = d3.zoom()
      .scaleExtent([0.4, 14])
      .translateExtent([[-matW * 0.5, -matH * 0.5], [matW * 1.5, matH * 1.5]])
      .on('zoom', ev => g.attr('transform', ev.transform));
    gOuter.call(zoom);
    /* Invisible hit-area rect so zoom works everywhere inside matrix */
    gOuter.append('rect')
      .attr('width', matW).attr('height', matH)
      .attr('fill', 'none').attr('pointer-events', 'all');

    /* ── Draw sparsity blocks ────────────────────────────────────────────── */
    const tt    = getTooltip();
    const cells = [];  // { x, y, w, h, meta } for hit-testing

    for (let t = 0; t < T_SHOW; t++) {
      SPARSITY.forEach(sp => {
        const colT = sp.prevHour ? t - 1 : t;
        if (colT < 0) return;  // skip hour 0's back-reference (cyclic handled conceptually)

        const rg = ROW_GROUPS.find(r => r.id === sp.row);
        const vg = VAR_GROUPS.find(v => v.id === sp.col);
        if (!rg || !vg) return;

        const col0 = colT * CPH + colOff[sp.col];
        const row0 = t * RPH + rowOff[sp.row];
        const px   = col0 * CELL;
        const py   = row0 * CELL;
        const bw   = vg.n * CELL - 0.5;
        const bh   = rg.n * CELL - 0.5;

        const fillColor = sp.prevHour ? d3.color(rg.color).copy({ opacity: sp.alpha }) : d3.color(rg.color).copy({ opacity: sp.alpha });
        const meta = {
          row: rg.label, col: vg.label,
          rowDesc: rg.desc, colDesc: vg.desc,
          colBounds: vg.bounds, colDim: vg.dim,
          prevHour: sp.prevHour, t,
          rg, vg,
        };

        g.append('rect')
          .attr('x', px).attr('y', py)
          .attr('width', bw).attr('height', bh)
          .attr('fill', rg.color)
          .attr('opacity', sp.alpha)
          .attr('rx', 0.5)
          .attr('class', 'sp-block')
          .attr('data-t', t)
          .on('mouseover', function (event) {
            d3.select(this).attr('opacity', Math.min(1, sp.alpha + 0.25));
            tt.style.opacity = '1';
            const prefix = sp.prevHour ? '⬡ Cross-hour coupling: ' : '';
            tt.innerHTML = `
              <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:.8rem;margin-bottom:5px;color:${rg.color};">${prefix}${rg.label} × ${vg.label}</div>
              <div style="margin-bottom:4px;opacity:.8;">Hour t = ${t + 1}${sp.prevHour ? `, columns from t = ${t}` : ''}</div>
              <div><span style="opacity:.6;">Constraint:</span> ${rg.desc}</div>
              <div><span style="opacity:.6;">Variable:</span> ${vg.desc}</div>
              <div><span style="opacity:.6;">Bounds:</span> <code style="font-family:monospace;font-size:.72rem;">${vg.bounds}</code></div>
              <div><span style="opacity:.6;">Size:</span> ${rg.n} × ${vg.n} (${rg.n * vg.n} nonzeros)</div>
            `;
          })
          .on('mousemove', function (event) {
            const m = 14, tw = tt.offsetWidth, th = tt.offsetHeight;
            const vw = window.innerWidth, vh = window.innerHeight;
            let left = event.clientX + m, top = event.clientY + m;
            if (left + tw > vw - 8) left = event.clientX - tw - m;
            if (top  + th > vh - 8) top  = event.clientY - th - m;
            tt.style.left = Math.max(8, left) + 'px';
            tt.style.top  = Math.max(8, top)  + 'px';
          })
          .on('mouseleave', function () {
            d3.select(this).attr('opacity', sp.alpha);
            tt.style.opacity = '0';
          });
      });

      /* Hour block separators */
      if (t > 0) {
        const sx = t * CPH * CELL;
        g.append('line')
          .attr('x1', sx).attr('x2', sx)
          .attr('y1', 0).attr('y2', matH)
          .attr('stroke', 'rgba(0,0,0,.15)').attr('stroke-width', 0.5).attr('pointer-events', 'none');
        const sy = t * RPH * CELL;
        g.append('line')
          .attr('x1', 0).attr('x2', matW)
          .attr('y1', sy).attr('y2', sy)
          .attr('stroke', 'rgba(0,0,0,.15)').attr('stroke-width', 0.5).attr('pointer-events', 'none');
      }

      /* Hour label above each block */
      g.append('text')
        .attr('x', t * CPH * CELL + (CPH * CELL) / 2)
        .attr('y', -8)
        .attr('text-anchor', 'middle')
        .attr('font-family', "'DM Sans', sans-serif")
        .attr('font-size', Math.max(8, Math.min(11, CELL * 3)))
        .attr('fill', '#566370')
        .text(`t=${t + 1}`);
    }

    /* Matrix border */
    gOuter.append('rect')
      .attr('width', matW).attr('height', matH)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0,0,0,.18)').attr('stroke-width', 1)
      .attr('pointer-events', 'none');

    /* ── Row group labels (left side) ──────────────────────────────────── */
    const labG = svg.append('g').attr('transform', `translate(0,${TOP_PAD})`);
    for (let t = 0; t < T_SHOW; t++) {
      ROW_GROUPS.forEach(rg => {
        const y0 = (t * RPH + rowOff[rg.id]) * CELL;
        const blockH = rg.n * CELL;
        /* Only label the first repetition to avoid clutter */
        if (t > 0 && CELL < 5) return;
        if (blockH < 8) return;
        labG.append('text')
          .attr('x', LABEL_W - 6)
          .attr('y', y0 + blockH / 2)
          .attr('text-anchor', 'end')
          .attr('dominant-baseline', 'middle')
          .attr('font-family', "'DM Sans', sans-serif")
          .attr('font-size', Math.max(7, Math.min(10, CELL * 1.5)))
          .attr('fill', rg.color)
          .attr('font-weight', '600')
          .text(t === 0 ? rg.label : '·');
      });
    }

    /* ── Variable group labels (bottom) ─────────────────────────────────── */
    const botY = TOP_PAD + matH + 12;
    const varLabG = svg.append('g');
    VAR_GROUPS.forEach(vg => {
      const x0 = LABEL_W + colOff[vg.id] * CELL;
      const bw  = vg.n * CELL;
      if (bw < 10) return;
      varLabG.append('text')
        .attr('x', x0 + bw / 2)
        .attr('y', botY + 4)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'hanging')
        .attr('font-family', "'JetBrains Mono', monospace")
        .attr('font-size', Math.max(6, Math.min(9, CELL * 1.3)))
        .attr('fill', vg.color)
        .attr('font-weight', '500')
        .text(vg.label);
    });

    /* Annotation: off-diagonal coupling arrow */
    const prevT = 2;  // illustrate on t=3
    const prevSocCol0 = prevT * CPH + colOff['SOC'];
    const curSOCRow0  = (prevT + 1) * RPH + rowOff['soc'];
    if (CELL >= 4) {
      const ax = LABEL_W + prevSocCol0 * CELL + (VAR_GROUPS.find(v => v.id === 'SOC').n * CELL) / 2;
      const ay = TOP_PAD + curSOCRow0 * CELL + (ROW_GROUPS.find(r => r.id === 'soc').n * CELL) / 2;
      svg.append('text')
        .attr('x', ax - 2).attr('y', ay - 8)
        .attr('text-anchor', 'middle')
        .attr('font-family', "'DM Sans', sans-serif")
        .attr('font-size', 8).attr('fill', '#92400E')
        .text('SOC[t−1]');
    }

    /* Footer note */
    svg.append('text')
      .attr('x', LABEL_W)
      .attr('y', TOP_PAD + matH + BOT_PAD - 6)
      .attr('font-family', "'DM Sans', sans-serif")
      .attr('font-size', 9).attr('fill', '#94A3B8')
      .text(`Showing ${T_SHOW} of 8,760 hours — block-diagonal Kronecker structure. Scroll to zoom, drag to pan.`);
  }
})();
