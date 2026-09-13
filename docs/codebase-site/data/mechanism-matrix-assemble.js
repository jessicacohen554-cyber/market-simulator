/* Cross-ISO mechanism matrix — browser-side shard assembler.
 *
 * Load order (mechanism-matrix.html): mechanism-matrix.js (the BASE:
 * window.MECH_MATRIX_BASE), then every per-ISO shard
 * mechanism-matrix/<ISO>.js (window.MECH_MATRIX_SHARDS.<ISO>), then this
 * file, which reconstitutes the legacy monolith shape the renderer reads:
 *
 *   window.MECH_MATRIX = { version, updated, isos, keepers, gates,
 *                          categories, rows: [{…, cells, fc?, ev?,
 *                          iso_notes?}] }
 *
 * Python twin: scripts/lib/mech_matrix.py::assemble — keep the two in sync.
 * Assembly rules: cells/fc strings are built in isos[] order from the shard
 * entries; a per-ISO fc left unset falls back to that ISO's backcast cell
 * (the legacy "no fc string ⇒ forecast = backcast" convention); shard ev
 * strings land under the ISO's letter (E/C/P/M/N/Q) after the base row's
 * cross-ISO ev keys. A missing shard or a shard missing a mechanism id is a
 * hard error (loud console + no window.MECH_MATRIX), exactly like the
 * pre-shard file's behavior on a syntax error — the CI guard
 * (scripts/check_mechanism_matrix.py) keeps that from ever landing.
 */
(function () {
  // Accept EITHER anchor. The committed base file has assigned
  // `window.MECH_MATRIX` since before the 2026-08-11 shard migration and has
  // never carried `_BASE`, so reading `_BASE` alone aborted this assembler on
  // every page load: it logged "base file failed to load", returned, and the
  // renderer then read `r.cells` off the un-assembled base (undefined) — i.e.
  // the rendered matrix page has shown no cells since the migration. CI never
  // saw it because scripts/check_mechanism_matrix.py and the pytest twins go
  // through the PYTHON assembler (scripts/lib/mech_matrix.py), which parses
  // `window.MECH_MATRIX` correctly. Repaired at SPP-21 2026-09-06 (owner
  // authorization in session; docs/handoffs/FINDING-spp-21-2026-09-06.md §5),
  // tolerating both spellings so a later lane may rename the base to `_BASE`
  // without re-breaking the page. NO data, cell or verdict is touched.
  var B = window.MECH_MATRIX_BASE || window.MECH_MATRIX;
  var S = window.MECH_MATRIX_SHARDS || {};
  if (!B) { console.error('mechanism-matrix: base file failed to load'); return; }
  var EV_KEY = { ERCOT: 'E', CAISO: 'C', PJM: 'P', MISO: 'M', NYISO: 'N', NEISO: 'Q', SPP: 'S', SOCO: 'O' };
  var missing = B.isos.filter(function (iso) { return !S[iso]; });
  if (missing.length) {
    console.error('mechanism-matrix: missing shard(s): ' + missing.join(', ') +
      ' — expected data/mechanism-matrix/<ISO>.js');
    return;
  }
  var keepers = {}, gates = {}, updated = String(B.updated || '');
  B.isos.forEach(function (iso) {
    keepers[iso] = S[iso].keeper || '';
    gates[iso] = S[iso].gates || '';
    var u = String(S[iso].updated || '');
    if (u > updated) updated = u;
  });
  var bad = [];
  var rows = B.rows.map(function (r) {
    var cells = '', fc = '', anyFc = false, ev = null, isoNotes = null, k;
    B.isos.forEach(function (iso) {
      var e = (S[iso].cells || {})[r.id];
      if (!e || !e.cell) { bad.push(iso + ':' + r.id); cells += '?'; fc += '?'; return; }
      cells += e.cell;
      if (e.fc) { anyFc = true; fc += e.fc; } else { fc += e.cell; }
      if (e.ev) { ev = ev || {}; ev[EV_KEY[iso]] = e.ev; }
      if (e.note) { isoNotes = isoNotes || {}; isoNotes[iso] = e.note; }
    });
    var out = {};
    for (k in r) { if (k !== 'ev') out[k] = r[k]; }
    out.cells = cells;
    if (anyFc) out.fc = fc;
    if (r.ev) {
      var merged = {};
      for (k in r.ev) merged[k] = r.ev[k];          // cross-ISO keys first
      if (ev) { for (k in ev) merged[k] = ev[k]; }  // then per-ISO letters
      out.ev = merged;
    } else if (ev) { out.ev = ev; }
    if (isoNotes) out.iso_notes = isoNotes;
    return out;
  });
  if (bad.length) {
    console.error('mechanism-matrix: shard entries missing for ' + bad.length +
      ' (iso, mechanism) cell(s): ' + bad.slice(0, 8).join(', ') +
      (bad.length > 8 ? ', …' : '') + ' — run scripts/check_mechanism_matrix.py');
    return;
  }
  window.MECH_MATRIX = {
    version: B.version,
    updated: updated,
    isos: B.isos,
    keepers: keepers,
    gates: gates,
    categories: B.categories,
    rows: rows
  };
})();
