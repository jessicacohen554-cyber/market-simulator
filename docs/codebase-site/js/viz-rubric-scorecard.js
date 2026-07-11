/**
 * viz-rubric-scorecard.js — Calibration Rubric page
 * Interactive C1–C8 tiered scorecard for the Calibration Rubric narrative page.
 *
 * Loads data/rubric-scorecard-v2.json (an illustrative rubric-v2.4 scorecard;
 * criteria/tiers/thresholds mirror scripts/calibration_verdict.py) and renders a
 * collapsible table:
 *   - one row per scored criterion id (C1, C2, C3a/b/c, C4, C5a/b/c, C6, C7, C8)
 *   - colour-coded by tier (load-bearing / supporting / protective)
 *   - PASS / CAVEAT / GROUNDED / SKIP / FAIL status badges
 *   - click a row to expand its note; "Expand all" toggles every row
 *   - a determination summary bar reading the JSON's determination block
 *
 * Plain IIFE (no D3, no ES-module import) so it loads via a normal <script src>
 * tag and degrades to a clear message if the fetch fails.
 */

(function () {
  'use strict';

  const CONTAINER_ID = 'rubric-scorecard';
  const DATA_URL = 'data/rubric-scorecard-v2.json';

  // Tier → label + accent. Load-bearing certifies the intended uses directly;
  // supporting is informative sub-annual dynamics; protective are the
  // anti-self-deception gates (calibration_verdict.py TIER_* constants).
  const TIERS = {
    'load-bearing': { label: 'Load-bearing', cls: 'tier-load' },
    'supporting': { label: 'Supporting', cls: 'tier-support' },
    'protective': { label: 'Protective', cls: 'tier-protect' },
  };

  // Status → badge label + class. GROUNDED is the C8 grounded-above-budget
  // clean PASS (rubric v2.2); SKIP is a recorded not-scored row (never a silent
  // pass). FAIL is defined for the legend even when the example carries none.
  const STATUS = {
    PASS: { label: 'PASS', cls: 'st-pass' },
    CAVEAT: { label: 'CAVEAT', cls: 'st-caveat' },
    GROUNDED: { label: 'GROUNDED', cls: 'st-grounded' },
    SKIP: { label: 'SKIP', cls: 'st-skip' },
    FAIL: { label: 'FAIL', cls: 'st-fail' },
  };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /** Format a numeric actual/modeled cell, or an em dash when null. */
  function num(v) {
    if (v === null || v === undefined) return '<span class="rs-null">—</span>';
    return esc(v);
  }

  function statusBadge(status) {
    const s = STATUS[status] || { label: status, cls: 'st-skip' };
    return `<span class="rs-badge ${s.cls}">${esc(s.label)}</span>`;
  }

  function tierChip(tier) {
    const t = TIERS[tier] || { label: tier, cls: 'tier-support' };
    return `<span class="rs-tier ${t.cls}">${esc(t.label)}</span>`;
  }

  /** Build the determination summary bar from the JSON's determination block. */
  function summaryBar(det, meta) {
    if (!det) return '';
    const verdict = det.verdict || '—';
    const vcls =
      verdict === 'CALIBRATED'
        ? 'det-cal'
        : verdict === 'NOT-YET'
        ? 'det-not'
        : 'det-cav';
    const chips = [
      det.caveats_commercial_band != null
        ? `<span class="rs-tally"><b>${det.caveats_commercial_band}</b> commercial-band <span class="rs-tally__sub">(unbudgeted)</span></span>`
        : '',
      det.caveats_ledgered != null
        ? `<span class="rs-tally"><b>${det.caveats_ledgered}</b> ledgered <span class="rs-tally__sub">/ ${det.budgets ? det.budgets.MAX_LEDGERED_CAVEATS : 3}</span></span>`
        : '',
      det.protective_caveats != null
        ? `<span class="rs-tally"><b>${det.protective_caveats}</b> protective <span class="rs-tally__sub">/ ${det.budgets ? det.budgets.MAX_PROTECTIVE_CAVEATS : 1}</span></span>`
        : '',
    ]
      .filter(Boolean)
      .join('');
    return `
      <div class="rs-summary">
        <div class="rs-summary__verdict">
          <span class="rs-summary__label">Determination</span>
          <span class="rs-badge ${vcls} rs-badge--lg">${esc(verdict)}</span>
        </div>
        <div class="rs-summary__tallies">${chips}</div>
      </div>`;
  }

  function rowHTML(row, idx) {
    const hasActual = row.actual !== null && row.actual !== undefined;
    return `
      <tbody class="rs-group ${STATUS[row.status] ? STATUS[row.status].cls : ''}">
        <tr class="rs-row" data-idx="${idx}" role="button" tabindex="0"
            aria-expanded="false" aria-controls="rs-note-${idx}">
          <td class="rs-crit">${esc(row.crit)}</td>
          <td class="rs-name">
            <span class="rs-name__txt">${esc(row.name)}</span>
            <span class="rs-chev" aria-hidden="true">▸</span>
          </td>
          <td>${tierChip(row.tier)}</td>
          <td class="rs-val">${hasActual ? num(row.actual) : '<span class="rs-null">n/a</span>'}</td>
          <td class="rs-val">${num(row.modeled)}</td>
          <td class="rs-status">${statusBadge(row.status)}</td>
        </tr>
        <tr class="rs-detail" id="rs-note-${idx}" hidden>
          <td colspan="6">
            <div class="rs-detail__inner">
              <div class="rs-detail__meta">
                <span class="rs-detail__units"><b>Units:</b> ${esc(row.units || '—')}</span>
                <span class="rs-detail__thresh"><b>Coded threshold:</b> <code>${esc(row.threshold || '—')}</code></span>
              </div>
              <p class="rs-detail__note">${esc(row.note || '')}</p>
            </div>
          </td>
        </tr>
      </tbody>`;
  }

  function render(container, data) {
    const rows = (data.rows || []).map(rowHTML).join('');
    const rm = data.run_metadata || {};
    const illustrative = (data._meta && data._meta.illustrative) !== false;

    container.innerHTML = `
      ${summaryBar(data.determination, data._meta)}
      <div class="rs-toolbar">
        <div class="rs-legend">
          <span class="rs-legend__group">
            ${tierChip('load-bearing')}${tierChip('supporting')}${tierChip('protective')}
          </span>
          <span class="rs-legend__group">
            ${statusBadge('PASS')}${statusBadge('CAVEAT')}${statusBadge('GROUNDED')}${statusBadge('SKIP')}${statusBadge('FAIL')}
          </span>
        </div>
        <button type="button" class="rs-expand-all" aria-pressed="false">Expand all</button>
      </div>
      <div class="rs-table-wrap">
        <table class="rs-table">
          <thead>
            <tr>
              <th class="rs-crit">Crit</th>
              <th>Criterion</th>
              <th>Tier</th>
              <th class="rs-val">Actual</th>
              <th class="rs-val">Modeled</th>
              <th class="rs-status">Status</th>
            </tr>
          </thead>
          ${rows}
        </table>
      </div>
      ${
        illustrative
          ? `<p class="rs-illustrative">Illustrative single-ISO-year excerpt (${esc(
              rm.iso || 'EXAMPLE'
            )} ${esc(
              rm.year || ''
            )}) — proportions faithful to rubric v${esc(
              rm.rubric_version || '2.4'
            )}, not raw solver output. Real keepers score every bundle year (2023–2025) together. Live per-run verdicts render on the <a href="calibration-status.html">Calibration Status</a> and <a href="backcast-runs.html">Run Explorer</a> pages.</p>`
          : ''
      }`;

    wireEvents(container);
  }

  function toggleRow(row, force) {
    const idx = row.getAttribute('data-idx');
    const detail = row.parentNode.querySelector('#rs-note-' + idx);
    if (!detail) return;
    const open = force === undefined ? detail.hasAttribute('hidden') : force;
    if (open) {
      detail.removeAttribute('hidden');
      row.setAttribute('aria-expanded', 'true');
      row.classList.add('is-open');
    } else {
      detail.setAttribute('hidden', '');
      row.setAttribute('aria-expanded', 'false');
      row.classList.remove('is-open');
    }
  }

  function wireEvents(container) {
    const rows = container.querySelectorAll('.rs-row');
    rows.forEach((row) => {
      row.addEventListener('click', () => toggleRow(row));
      row.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleRow(row);
        }
      });
    });

    const expandAll = container.querySelector('.rs-expand-all');
    if (expandAll) {
      expandAll.addEventListener('click', () => {
        const isExpanding = expandAll.getAttribute('aria-pressed') !== 'true';
        rows.forEach((row) => toggleRow(row, isExpanding));
        expandAll.setAttribute('aria-pressed', String(isExpanding));
        expandAll.textContent = isExpanding ? 'Collapse all' : 'Expand all';
      });
    }
  }

  async function init() {
    const container = document.getElementById(CONTAINER_ID);
    if (!container) return;
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      render(container, data);
    } catch (err) {
      container.innerHTML = `
        <div class="rs-error">
          Could not load the scorecard data
          (<code>${esc(DATA_URL)}</code>: ${esc(err.message)}).
          The interactive table needs to be served over HTTP — open the site
          through a local server or the deployed GitHub Pages build.
        </div>`;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
