/**
 * calibration-status.js — Calibration Status page module
 * (docs/codebase-site/calibration-status.html).
 *
 * Extracted verbatim from that page's inline <script type="module"> (Wave 5C,
 * 2026-07-25): the body is byte-for-byte the former inline block, indent
 * included. The ONE required edit is the bc-data import specifier
 * ('./js/bc-data.js' -> './bc-data.js'), because an external module resolves
 * relative specifiers against the MODULE url, not the document url.
 */
    import { loadStatus, isoColorVar, hashState, fmtPct, fmtNum } from './bc-data.js';

    /* -----------------------------------------------------------------------
       Helpers
       ----------------------------------------------------------------------- */

    /** Map determination string to CSS modifier class. */
    function detClass(det) {
      if (!det) return 'det-not';
      const d = det.toUpperCase();
      if (d === 'CALIBRATED') return 'det-cal';
      if (d.includes('CAVEAT')) return 'det-cav';
      return 'det-not';
    }

    /** Human-readable determination label. */
    function detLabel(det) {
      if (!det) return 'NOT CALIBRATED';
      const d = det.toUpperCase();
      if (d === 'CALIBRATED') return 'CALIBRATED';
      if (d.includes('CAVEAT')) return 'WITH CAVEATS';
      if (d === 'NOT-YET') return 'NOT YET';
      return 'NOT CALIBRATED';
    }

    /** Is the owner's "frontier achieved" designation live (declared and not
        withdrawn)? A withdrawn frontier (e.g. ERCOT/NYISO after the 2026-07-19
        phantom-outage re-audit) must render as if there were no frontier at
        all — the block is kept in keepers/<ISO>.json for lineage, not display. */
    function frontierActive(keeper) {
      return !!(keeper.frontier && keeper.frontier.declared && !keeper.frontier.withdrawn);
    }

    /** Determination as displayed. When frontier is live, a CALIBRATED-WITH-
        CAVEATS keeper is shown as the clean "CALIBRATED" headline — the
        remaining misses are the owner-declared, research-backed representation-
        frontier caveats (documented as footnotes in the frontier note + the
        criteria table), not headline-downgrading failures. A NOT-YET keeper is
        never upgraded: the green headline requires every miss to be a documented
        caveat, so an ISO with any undocumented FAIL still reads NOT YET. */
    function effectiveDet(keeper) {
      const det = keeper.determination;
      if (frontierActive(keeper) && det && det.toUpperCase().includes('CAVEAT')) {
        return 'CALIBRATED';
      }
      return det;
    }

    /** Return glyph + color class for criterion status. */
    function criterionGlyph(status) {
      if (!status) return { glyph: '—', cls: '' };
      const s = status.toUpperCase();
      if (s === 'PASS')    return { glyph: '✓', cls: 'clr-good' };
      if (s === 'FAIL')    return { glyph: '✗', cls: 'clr-bad' };
      if (s === 'CAVEAT')  return { glyph: '!',      cls: 'clr-ok' };
      if (s === 'SKIPPED') return { glyph: '—',  cls: 'bc-mute' };
      if (s === 'REPORTED') return { glyph: '·', cls: 'bc-mute' };
      return { glyph: '?', cls: '' };
    }

    /** Status badge CSS modifier for inline badges. */
    function statusBadgeClass(status) {
      if (!status) return 'det-not';
      const s = status.toUpperCase();
      if (s === 'PASS')   return 'det-cal';
      if (s === 'CAVEAT') return 'det-cav';
      return 'det-not';
    }

    /** Status badge label. */
    function statusLabel(status) {
      if (!status) return 'N/A';
      const s = status.toUpperCase();
      if (s === 'SKIPPED') return 'SKIP';
      return s;
    }

    /** Canonical criterion display order. (C5b/C5c storage criteria were
        removed from the rubric — v2.7 owner amendment 2026-07-16; verdicts
        no longer carry them.) */
    const CRITERIA_ORDER = [
      'sysvol', 'fuelmix', 'price_mean', 'price_shape', 'price_tail',
      'dispatch_corr', 'co2',
      'shape', 'forced_share', 'governance'
    ];

    /** Ordered criteria entries from a keeper. */
    function orderedCriteria(criteria) {
      const entries = [];
      for (const key of CRITERIA_ORDER) {
        if (criteria[key]) entries.push([key, criteria[key]]);
      }
      // Include any extras not in CRITERIA_ORDER
      for (const [key, val] of Object.entries(criteria)) {
        if (!CRITERIA_ORDER.includes(key)) entries.push([key, val]);
      }
      return entries;
    }

    /** Tier label for a criterion (rubric v2); falls back to v1 hard/soft. */
    function tierLabel(crit) {
      if (crit.tier) return crit.tier.toUpperCase();
      return crit.hard ? 'HARD GATE' : 'SOFT';
    }

    /** Short criterion code for marks display. */
    function shortCode(key, crit) {
      const label = crit.label || key;
      // Extract the C-number pattern like "C1", "C3a", "C5b"
      const m = label.match(/C\d+[a-z]?/);
      return m ? m[0] : key.slice(0, 3).toUpperCase();
    }

    /** Escape HTML entities. */
    function esc(str) {
      if (!str) return '';
      const d = document.createElement('div');
      d.textContent = String(str);
      return d.innerHTML;
    }

    /* Owner-declared CONFIG PARTITION (two-config keeper structure, owner
       ruling 2026-08-26): the ISO's training window is covered by more than
       one designated config, each scored on its own span. Every config's span
       and determination is on the page — the year table's Config column shows
       which config covers which year, and the Notes disclosure carries the
       ruling and each config's registered full-span determination, so no half
       of a partition is ever laundered out of view. */
    function partitionConfigs(keeper) {
      const cp = keeper.config_partition;
      return (cp && cp.configs && cp.configs.length) ? cp.configs : null;
    }

    /** Compact year-span label: [2024,2025] -> "2024–25", [2023] -> "2023". */
    function spanLabel(years) {
      if (!years || !years.length) return '';
      if (years.length === 1) return String(years[0]);
      const a = years[0], b = years[years.length - 1];
      return `${a}–${String(b).slice(-2)}`;
    }

    /** Format model/actual values for display. */
    function fmtVal(v) {
      if (v === null || v === undefined) return '—';
      if (typeof v === 'string') return esc(v);
      return Number(v).toLocaleString('en-US', { maximumFractionDigits: 3 });
    }

    /* -----------------------------------------------------------------------
       Render: ISO Card Grid
       ----------------------------------------------------------------------- */

    function renderCards(keepers) {
      const grid = document.getElementById('cardGrid');
      grid.innerHTML = '';

      keepers.forEach(keeper => {
        const dc = detClass(effectiveDet(keeper));
        const card = document.createElement('div');
        card.className = `cs-card ${dc}`;
        card.tabIndex = 0;
        card.setAttribute('role', 'button');
        card.setAttribute('aria-label', `${keeper.iso} — ${detLabel(effectiveDet(keeper))}`);
        card.dataset.iso = keeper.iso;

        // Color accent from ISO palette
        const colorVar = isoColorVar(keeper.iso);

        // Header. ONE determination badge, always — the ISO's train-tier
        // verdict (already the worst designated-config read for a partitioned
        // keeper). Per-year and per-config detail belongs in the one year table
        // in the detail pane, not in a second badge dialect up here.
        let html = `
          <div class="cs-card-header">
            <span class="cs-iso-name" style="color: var(${colorVar})">${esc(keeper.iso)}</span>
            <span class="cs-badges">
              ${frontierActive(keeper) ? `<span class="cs-badge det-frontier" title="Frontier achieved ${esc(keeper.frontier.declared || '')}">FRONTIER</span>` : ''}
              <span class="cs-badge ${dc}">${detLabel(effectiveDet(keeper))}</span>
            </span>
          </div>`;

        if (keeper.run_id) {
          const runLink = `backcast-runs.html#iso=${encodeURIComponent(keeper.iso)}&run=${encodeURIComponent(keeper.run_id)}`;
          html += `
          <div class="cs-keeper-info">
            Keeper: <a class="run-id-link" href="${runLink}" title="View in Run Explorer">${esc(keeper.label || keeper.run_id)}</a>
          </div>`;
        }

        // Years — training years, then held-out years in the same line and the
        // same format; the tier is the only thing that differs.
        const yrs = keeper.years || [];
        const tr = [...new Set(yrs.filter(r => r.tier === 'training').map(r => r.year))];
        const ho = [...new Set(yrs.filter(r => r.tier !== 'training').map(r => r.year))];
        if (tr.length || (keeper.scorable_years || []).length) {
          html += `<div class="cs-keeper-info">Years: ${(tr.length ? tr : keeper.scorable_years).join(', ')}${
            ho.length ? ` &middot; held out ${ho.join(', ')}` : ''}</div>`;
        }

        if (keeper.grade_summary) {
          const g = keeper.grade_summary;
          html += `<div class="cs-keeper-info">Grade: ${g.target_grade}/${g.scored} target &middot; ${g.commercial_grade} commercial-band &middot; ${g.ledgered} ledgered${g.fails ? ` &middot; ${g.fails} fail` : ''}</div>`;
        }

        // Mini criteria marks
        const criteria = orderedCriteria(keeper.criteria);
        html += `<div class="cs-marks">`;
        for (const [key, crit] of criteria) {
          const g = criterionGlyph(crit.status);
          html += `
            <div class="cs-mark" title="${esc(crit.label)}: ${crit.status || 'N/A'}">
              <span class="code">${shortCode(key, crit)}</span>
              <span class="glyph ${g.cls}">${g.glyph}</span>
            </div>`;
        }
        html += `</div>`;

        // View details link
        html += `<div class="cs-open-link" style="margin-top: 10px;">View details &rarr;</div>`;

        card.innerHTML = html;

        // Click handler
        card.addEventListener('click', (e) => {
          // Don't intercept clicks on the run-id link
          if (e.target.closest('.run-id-link')) return;
          selectCard(keeper.iso, keepers);
        });
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            selectCard(keeper.iso, keepers);
          }
        });

        grid.appendChild(card);
      });
    }

    /* -----------------------------------------------------------------------
       Render: Select Card & Detail
       ----------------------------------------------------------------------- */

    function selectCard(iso, keepers) {
      // Update card selection
      document.querySelectorAll('.cs-card').forEach(c => {
        c.classList.toggle('selected', c.dataset.iso === iso);
      });

      // Update hash
      hashState.update('iso', iso);

      // Find keeper
      const keeper = keepers.find(k => k.iso === iso);
      if (!keeper) return;

      renderDetail(keeper);

      // Scroll detail into view
      const pane = document.getElementById('detailPane');
      setTimeout(() => {
        pane.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 50);
    }

    /* -----------------------------------------------------------------------
       Render: Detail Pane
       ----------------------------------------------------------------------- */

    function renderDetail(keeper) {
      const pane = document.getElementById('detailPane');
      const configs = partitionConfigs(keeper);
      const dc = detClass(effectiveDet(keeper));
      const colorVar = isoColorVar(keeper.iso);

      let html = `<div class="bc-panel">`;

      // Header — one determination badge (see renderCards).
      html += `
        <div class="cs-results-header">
          <span class="cs-iso-name" style="color: var(${colorVar})">${esc(keeper.iso)}</span>
          <span class="cs-badges">
            ${frontierActive(keeper) ? `<span class="cs-badge det-frontier">FRONTIER${keeper.frontier.declared ? ' ' + esc(keeper.frontier.declared) : ''}</span>` : ''}
            <span class="cs-badge ${dc}">${detLabel(effectiveDet(keeper))}</span>
          </span>
        </div>`;

      // ONE uniform year table — every year this keeper has been scored on,
      // training and held out, in the same rows and the same columns. It
      // replaces the three bespoke blocks that used to sit here (config
      // partition, holdout touchpoint, holdout ladder): a partitioned keeper's
      // designated config per year is just the Config column, and a rule-22
      // touchpoint is just a row with a different tier.
      //
      // Held-out rows are REPORTED, never gating (rule 22, as amended
      // 2026-09-05): the determination above is the train-tier verdict and a
      // held-out year that degrades does NOT downgrade the ISO. The line under
      // the table says so, rather than leaving a reader to infer that a NOT-YET
      // row beside a CALIBRATED headline is a contradiction.
      const years = keeper.years || [];
      if (years.length) {
        const TIER_TXT = { training: 'training', validation: 'validation holdout', locked_test: 'locked test' };
        const anyRole = years.some(r => r.role);
        // Years the model priced but that carry NO measured LMP reference on
        // disk, so C3a/C3b/C3c are unscoreable there for ABSENCE OF A REFERENCE
        // rather than for passing (miso-256). Reported only — it gates nothing.
        // Without it an unverifiable year reads as cleaner than one that could
        // be checked and missed: MISO 2020 shows CALIBRATED-WITH-CAVEATS partly
        // BECAUSE its price criteria could not be scored at all.
        const noRef = new Set((keeper.price_reference_blocked_years || []).map(Number));
        const rows = years.map(r => {
          const runLink = `backcast-runs.html#iso=${encodeURIComponent(keeper.iso)}&run=${encodeURIComponent(r.run_id)}`;
          const det = String(r.determination || '—');
          const cls = det === 'CALIBRATED' ? 'clr-good' : (det.includes('NOT') ? 'clr-bad' : 'clr-ok');
          return `<tr${(r.reasons || []).length ? ` title="${esc(r.reasons.join('; '))}"` : ''}>
            <td class="num">${esc(String(r.year))}</td>
            <td>${esc(TIER_TXT[r.tier] || r.tier || '—')}</td>
            ${anyRole ? `<td>${esc(r.role || '—')}</td>` : ''}
            ${noRef.size ? `<td>${noRef.has(Number(r.year)) ? '<span class="bc-mute" title="No measured LMP reference on disk for this ISO-year — C3a/C3b/C3c unscoreable, not passing">none</span>' : 'yes'}</td>` : ''}
            <td class="${cls}" style="font-weight:600">${esc(det)}</td>
            <td style="font-size:0.72rem"><a class="run-id-link" href="${runLink}">${esc(r.src || r.run_id)}</a></td>
          </tr>`;
        }).join('');
        html += `
        <div class="bc-table-wrap" style="margin-top:10px">
          <table style="font-size:0.82rem;width:100%">
            <thead><tr><th>Year</th><th>Tier</th>${anyRole ? '<th>Config</th>' : ''}${noRef.size ? '<th>Price ref</th>' : ''}<th>Determination</th><th>Run</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
        <p class="bc-mute" style="font-size:0.75rem;margin:6px 0 0">Held-out years are reported, not gating &mdash; the ISO determination is the 2023&ndash;2025 verdict (rule&nbsp;22).${noRef.size ? ` Price ref <em>none</em> (${[...noRef].sort().join(', ')}): no measured LMP series exists on disk for those years, so C3a/C3b/C3c are <strong>unscoreable there, not passing</strong>.` : ''}</p>`;
      }

      // Reasons — only when something FAILED. On a clean or caveated run they
      // merely restate the caveat line below, which is the same sentence twice.
      const fails = (keeper.grade_summary || {}).fails || 0;
      if (fails && keeper.reasons && keeper.reasons.length) {
        html += `<div class="cs-reason" style="margin-top: 8px;">`;
        keeper.reasons.forEach(r => {
          html += `<p style="margin: 4px 0;">${esc(r)}</p>`;
        });
        html += `</div>`;
      }

      // Caveats summary (rubric v2: three kinds — protective ledgered,
      // non-protective ledgered, and unbudgeted commercial-band autos).
      if (keeper.caveats) {
        const c = keeper.caveats;
        const prot = c.protective || [];
        const ledg = c.ledgered || [];
        const band = c.commercial_band || [];
        if (prot.length || ledg.length || band.length) {
          const budget = c.budget || {};
          html += `<div style="margin: 10px 0 16px; font-size: 0.82rem;">`;
          if (band.length) {
            html += `<p><span class="cs-tag tag-lim">COMMERCIAL BAND</span> ${band.map(esc).join(', ')}
              <span style="opacity:.7">(inside the published commercial-grade band, outside target — listed, unbudgeted)</span></p>`;
          }
          if (ledg.length) {
            html += `<p style="margin-top: 4px;"><span class="cs-tag tag-lim">LEDGERED</span> ${ledg.map(esc).join(', ')}
              ${budget.ledgered_max ? ` (budget: ${ledg.length} / ${budget.ledgered_max})` : ''}</p>`;
          }
          if (prot.length) {
            html += `<p style="margin-top: 4px;"><span class="cs-tag tag-miss">PROTECTIVE LEDGERED</span> ${prot.map(esc).join(', ')}
              ${budget.protective_max ? ` (budget: ${prot.length} / ${budget.protective_max})` : ''}</p>`;
          }
          html += `</div>`;
        }
      }

      // ONE collapsed disclosure for every declarative note attached to this
      // keeper — the owner-signed frontier/standing-note/config-partition text
      // and the two REPORTED-only diagnostics (D-10 free-class C1, D-7
      // statistical-mode gap). None of it gates, and none of it restates a
      // magnitude: the criteria tables below carry every number at full
      // magnitude from the scorer. It used to be six always-open prose blocks
      // above the results; it is one line until a reader asks for it.
      const notes = [];
      if (configs) {
        const cp = keeper.config_partition;
        const list = configs.map(c =>
          `<li>${esc(spanLabel(c.years))} <strong>${esc(c.role || '')}</strong> &mdash; ${esc(c.label || '')}
           (${esc(c.determination)}; registered full-span ${esc((c.registered_years || []).join(', '))}: ${esc(c.registered_determination || c.determination)})</li>`
        ).join('');
        notes.push(`<p><strong>Config partition${cp.declared ? ' ' + esc(cp.declared) : ''}.</strong>
          Owner ruling, verbatim: &ldquo;${esc(cp.ruling || '')}&rdquo;</p>
          <ul style="margin:4px 0 0 18px">${list}</ul>
          ${cp.coverage_invariant ? `<p style="opacity:.85">${esc(cp.coverage_invariant)}</p>` : ''}`);
      }
      if (keeper.determination_basis) {
        notes.push(`<p><strong>Determination basis.</strong> ${esc(keeper.determination_basis)}</p>`);
      }
      if (frontierActive(keeper) && keeper.frontier.note) {
        notes.push(`<p><strong>Frontier ${esc(keeper.frontier.declared || '')}.</strong> ${esc(keeper.frontier.note)}</p>`);
      }
      if (keeper.frontier_touchpoint && keeper.frontier_touchpoint.note) {
        const ft = keeper.frontier_touchpoint;
        const yrs = (ft.years || []).join(', ');
        notes.push(`<p><strong>Touchpoint ${esc(ft.declared || '')}.</strong>
          Folded held-out rungs${yrs ? ' ' + esc(yrs) : ''}: <strong>${esc(ft.determination || '')}</strong>
          &mdash; ${esc(ft.note)}</p>`);
      }
      if (keeper.standing_note && keeper.standing_note.note) {
        const sn = keeper.standing_note;
        const probeLink = sn.probe_run_id
          ? ` <a class="run-id-link" href="backcast-runs.html#iso=${encodeURIComponent(keeper.iso)}&run=${encodeURIComponent(sn.probe_run_id)}">${esc(sn.probe_run_id)}</a>`
          : '';
        notes.push(`<p><strong>Standing note${sn.declared ? ' ' + esc(sn.declared) : ''}.</strong> ${esc(sn.note)}${probeLink}</p>`);
      }
      if (keeper.free_class_score) {
        const f = keeper.free_class_score;
        notes.push(`<p><strong>D-10 free-class C1 (reported).</strong> ${esc(f.headline)}${
          (f.excluded_from_free || []).length ? ` &mdash; pinned classes excluded: ${f.excluded_from_free.map(esc).join(', ')}` : ''}</p>`);
      }
      if (keeper.statmode_d7) {
        const s = keeper.statmode_d7;
        const probeLink = s.probe_run_id
          ? ` <a class="run-id-link" href="backcast-runs.html#iso=${encodeURIComponent(keeper.iso)}&run=${encodeURIComponent(s.probe_run_id)}">probe</a>`
          : '';
        notes.push(`<p><strong>D-7 statistical-mode gap (reported).</strong>
          ${esc(String(s.keeper_fails))} fails with overlays on &rarr; ${esc(String(s.statmode_fails))} with them off.${probeLink}${
          s.stale ? ' <em>(measured against a prior keeper — re-measure)</em>' : ''}</p>`);
      }
      if (notes.length) {
        html += `
        <details class="cs-detail" style="margin-top: 4px;">
          <summary><span>Notes</span><span class="cs-gate">${notes.length} &middot; declarative, non-gating</span></summary>
          <div style="padding: 14px; font-size: 0.82rem;">${notes.join('')}</div>
        </details>`;
      }

      // Expandable criterion sections
      const criteria = orderedCriteria(keeper.criteria);
      for (const [key, crit] of criteria) {
        const g = criterionGlyph(crit.status);
        const sbClass = statusBadgeClass(crit.status);
        const gateLabel = tierLabel(crit);

        html += `
        <details class="cs-detail">
          <summary>
            <span>${esc(crit.label || key)}</span>
            <span class="cs-gate">${gateLabel}</span>
            <span class="cs-badge ${sbClass}">${statusLabel(crit.status)}</span>
          </summary>
          <div style="padding: 14px;">`;

        // Records table
        if (crit.records && crit.records.length) {
          html += renderRecordsTable(crit.records);
        } else {
          html += `<p class="bc-mute" style="font-size: 0.82rem;">No test records available.</p>`;
        }

        html += `</div></details>`;
      }

      // Reported-only streams (rubric v3.5 `reported` block: C5a co2 since
      // v2.9, D-A diurnal amplitude since v3.5). Same expandable presentation
      // as the criteria above; the REPORTED badge is a disclosure, never a
      // verdict — these contribute no status and no caveat budget, so they
      // render after every gating criterion and outside the marks strip.
      for (const [key, rep] of Object.entries(keeper.reported || {})) {
        html += `
        <details class="cs-detail">
          <summary>
            <span>${esc(rep.label || key)}</span>
            <span class="cs-gate">REPORTED-ONLY</span>
            <span class="cs-badge det-rep">REPORTED</span>
          </summary>
          <div style="padding: 14px;">`;
        if (rep.records && rep.records.length) {
          html += renderRecordsTable(rep.records);
        } else {
          html += `<p class="bc-mute" style="font-size: 0.82rem;">No records available.</p>`;
        }
        html += `</div></details>`;
      }

      // Ledger entries
      if (keeper.ledger_entries && keeper.ledger_entries.length) {
        html += `
        <details class="cs-detail" style="margin-top: 4px;">
          <summary>
            <span>Ledger entries</span>
            <span class="cs-gate">${keeper.ledger_entries.length} entries</span>
          </summary>
          <div style="padding: 14px;">`;

        for (const entry of keeper.ledger_entries) {
          const year = entry.year ? `<b>${entry.year}</b> ` : '';
          const crit = entry.criterion ? `<span class="cs-tag tag-lim">${esc(entry.criterion)}</span> ` : '';
          html += `<div class="cs-ledger">${year}${crit}${esc(entry.reason)}</div>`;
        }

        html += `</div></details>`;
      }

      // Link to Run Explorer
      if (keeper.run_id) {
        const runLink = `backcast-runs.html#iso=${encodeURIComponent(keeper.iso)}&run=${encodeURIComponent(keeper.run_id)}`;
        html += `<p class="cs-open-link" style="margin-top: 16px;"><a href="${runLink}">View full results in Run Explorer &rarr;</a></p>`;
      }

      html += `</div>`;
      pane.innerHTML = html;
    }

    /* -----------------------------------------------------------------------
       Render: Records Table
       ----------------------------------------------------------------------- */

    function renderRecordsTable(records) {
      // Determine which columns have data. Held-out years are folded into this
      // same table by build_status.py (rule 30 [R-TOUCHPOINT-FOLD]) and get NO
      // special treatment here — a year is a row. The only extra column is
      // `src`, and only when more than one run contributed rows (a partitioned
      // keeper, or a touchpoint bundle beside the keeper), so the reader can
      // tell which config produced which number.
      const hasKey = records.some(r => r.key);
      const hasModel = records.some(r => r.model !== null && r.model !== undefined);
      const hasActual = records.some(r => r.actual !== null && r.actual !== undefined);
      const hasSrc = new Set(records.map(r => r.src).filter(Boolean)).size > 1;

      let html = `<div class="bc-table-wrap"><table>`;

      // Header
      html += `<thead><tr>`;
      html += `<th>Year</th>`;
      if (hasSrc) html += `<th>Run</th>`;
      if (hasKey) html += `<th>Key</th>`;
      html += `<th>Metric</th>`;
      if (hasModel) html += `<th style="text-align:right">Model</th>`;
      if (hasActual) html += `<th style="text-align:right">Actual</th>`;
      html += `<th style="text-align:right">Magnitude</th>`;
      html += `<th>Tol</th>`;
      html += `<th style="text-align:center">Status</th>`;
      html += `</tr></thead>`;

      // Body
      html += `<tbody>`;
      for (const r of records) {
        const g = criterionGlyph(r.status);
        const rowClass = r.status === 'FAIL' ? ' style="background: #fdecea;"' :
                         r.status === 'CAVEAT' ? ' style="background: #fef6e7;"' : '';
        html += `<tr${rowClass}>`;
        html += `<td class="num">${r.year || '—'}</td>`;
        if (hasSrc) html += `<td style="font-size:0.72rem">${esc(r.src) || ''}</td>`;
        if (hasKey) html += `<td>${esc(r.key) || ''}</td>`;
        html += `<td>${esc(r.metric)}</td>`;
        if (hasModel) html += `<td class="num">${fmtVal(r.model)}</td>`;
        if (hasActual) html += `<td class="num">${fmtVal(r.actual)}</td>`;
        html += `<td class="num">${esc(r.magnitude)}</td>`;
        html += `<td>${esc(r.tol)}</td>`;
        html += `<td style="text-align:center"><span class="${g.cls}" style="font-weight:800">${g.glyph}</span></td>`;
        html += `</tr>`;
      }
      html += `</tbody></table></div>`;

      return html;
    }

    /* -----------------------------------------------------------------------
       Render: Reference (rubric table + commercial-grade benchmark anchors)
       -----------------------------------------------------------------------
       Both are REFERENCE, not this page's subject: they are the same for every
       ISO and change only when the scorer's constants do. They render collapsed
       under one panel, and the prose that used to introduce them lives on
       calibration-rubric.html, which is the page for it. */

    function renderReference(status) {
      const section = document.getElementById('methodologySection');
      if (!section) return;
      let html = `<div class="bc-panel">
        <h2>Reference</h2>
        <p class="panel-sub">Derived live from the scorer's constants.
          Full rubric write-up: <a href="calibration-rubric.html">Calibration Rubric</a>.</p>`;

      if (status.rubric && status.rubric.length) {
        html += `<details class="cs-detail">
          <summary><span>Criteria &amp; tolerances</span><span class="cs-gate">${status.rubric.length} criteria</span></summary>
          <div style="padding: 14px;"><div class="bc-table-wrap"><table>
            <thead><tr><th>Criterion</th><th>Tier</th><th>Measures</th><th>Tolerance (target / commercial)</th><th>Source</th></tr></thead>
            <tbody>`;
        for (const r of status.rubric) {
          html += `<tr>
            <td style="white-space:nowrap; font-weight:700;">${esc(r.label || r.id)}</td>
            <td><span class="cs-gate">${esc(tierLabel(r))}</span></td>
            <td style="white-space:normal; max-width:300px;">${esc(r.measures)}</td>
            <td style="white-space:normal; max-width:180px;">${esc(r.tol)}</td>
            <td style="white-space:normal; max-width:220px; font-size:0.72rem; color:var(--text-muted);">${esc(r.source)}</td>
          </tr>`;
        }
        html += `</tbody></table></div></div></details>`;
      }

      const b = status.benchmark;
      if (b && b.rows && b.rows.length) {
        html += `<details class="cs-detail">
          <summary><span>Commercial-grade band anchors</span><span class="cs-gate">${b.rows.length} rows</span></summary>
          <div style="padding: 14px;"><div class="bc-table-wrap"><table>
            <thead><tr><th>Criterion</th><th>Target band (PASS)</th><th>Commercial band (auto caveat)</th><th>Best published comparable</th></tr></thead>
            <tbody>`;
        for (const r of b.rows) {
          html += `<tr>
            <td style="white-space:nowrap; font-weight:700;">${esc(r.criterion)}</td>
            <td style="white-space:normal;">${esc(r.target)}</td>
            <td style="white-space:normal;">${esc(r.commercial)}</td>
            <td style="white-space:normal; max-width:420px; font-size:0.78rem;">${esc(r.published)}</td>
          </tr>`;
        }
        html += `</tbody></table></div></div></details>`;
      }

      if (status.methodology && status.methodology.length) {
        html += `<details class="cs-detail">
          <summary><span>Scoring notes</span><span class="cs-gate">${status.methodology.length} notes</span></summary>
          <div style="padding: 14px;"><div class="cs-method-grid">`;
        for (const m of status.methodology) {
          html += `<div class="cs-method-card"><h4>${esc(m.head)}</h4><p>${esc(m.body)}</p></div>`;
        }
        html += `</div></div></details>`;
      }

      html += `</div>`;
      section.innerHTML = html;
    }

    /* -----------------------------------------------------------------------
       Boot
       ----------------------------------------------------------------------- */

    async function boot() {
      try {
        const status = await loadStatus();

        // Generation timestamp
        document.getElementById('genStamp').textContent =
          status.generated ? `Generated ${status.generated}` : 'Calibration overview across all ISOs';

        // Build cards
        const keepers = status.keepers || [];
        renderCards(keepers);

        // Render benchmark comparison + methodology
        renderReference(status);

        // Auto-select from hash or first ISO
        const hash = hashState.get();
        const targetIso = hash.iso || (keepers.length ? keepers[0].iso : null);
        if (targetIso) {
          selectCard(targetIso, keepers);
        }

        // Listen for hash changes (back/forward)
        window.addEventListener('hashchange', () => {
          const h = hashState.get();
          if (h.iso) selectCard(h.iso, keepers);
        });

      } catch (err) {
        console.error('Calibration status load failed:', err);
        document.getElementById('genStamp').textContent = 'Failed to load calibration data.';
        document.getElementById('genStamp').classList.add('clr-bad');
      }
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', boot);
    } else {
      boot();
    }
