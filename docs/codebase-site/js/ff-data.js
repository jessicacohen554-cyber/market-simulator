/**
 * ff-data.js — Shared data-loading module for the FORECAST dashboard pages
 * (Forecast Run Explorer + Forecast Program Status). ES module.
 *
 * Mirrors bc-data.js (the backcast loader) but over the SEPARATE forecast
 * namespace `frontend/data/forecast/` and the `window.FF` global — the two
 * namespaces never cross (plan §7.5: the backcast CI gates stay blind to
 * forecast ids). Wire format written by scripts/register_forecast_run.py:
 *
 *   manifest.js        window.FF.meta   + window.FF.manifest  (index + facets)
 *   runs/<id>.js       window.FF.runGz[<id>] = gzip+base64 full-detail payload
 *   program-status.js  window.FF.programStatus                (the §2.1b board)
 *
 * Data is loaded via <script> tags (not fetch) so the local file:// preview
 * works with no server — the same mechanism bc-data.js uses for manifest.js.
 * Shared numeric/format/hash helpers are re-used from bc-data.js (one impl).
 */

import { inflateGz, hashState, fmtNum, fmtPct, fmtDollars } from './bc-data.js';

// The frontend/ tree is copied verbatim into the deploy, so the ../../ path
// resolves both locally (repo checkout) and on the published site (_site).
let DATA_ROOT = '../../frontend/data/forecast';
const DATA_ROOT_FALLBACK = 'data/forecast';

let _meta = null;
let _manifest = null;
let _programStatus = null;
const _runCache = {};

function _ensureFF() {
  if (!window.FF) window.FF = {};
}

function _loadScript(url) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = url;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`Failed to load ${url}`));
    document.head.appendChild(s);
  });
}

let _rootProbed = false;
async function _probeDataRoot() {
  if (_rootProbed) return;
  _ensureFF();
  try {
    await _loadScript(`${DATA_ROOT}/manifest.js`);
  } catch {
    DATA_ROOT = DATA_ROOT_FALLBACK;
    await _loadScript(`${DATA_ROOT}/manifest.js`);
  }
  _rootProbed = true;
}

/** Load manifest.js → { meta, manifest }. */
async function loadManifest() {
  if (_manifest) return { meta: _meta, manifest: _manifest };
  await _probeDataRoot();
  _meta = window.FF.meta || null;
  _manifest = window.FF.manifest || [];
  return { meta: _meta, manifest: _manifest };
}

/** Lazy-load and decompress one run's full-detail payload by id. */
async function loadRun(id) {
  if (_runCache[id]) return _runCache[id];
  _ensureFF();
  await _probeDataRoot();
  if (!window.FF.runGz) window.FF.runGz = {};
  await _loadScript(`${DATA_ROOT}/runs/${id}.js`);
  const gz = window.FF.runGz[id];
  if (!gz) throw new Error(`Run ${id} not found after loading its payload`);
  const data = await inflateGz(gz);
  _runCache[id] = data;
  delete window.FF.runGz[id];
  return data;
}

/** Load the per-ISO program-status board (window.FF.programStatus). */
async function loadProgramStatus() {
  if (_programStatus) return _programStatus;
  await _probeDataRoot();
  _ensureFF();
  try {
    await _loadScript(`${DATA_ROOT}/program-status.js`);
  } catch {
    return null;
  }
  _programStatus = window.FF.programStatus || null;
  return _programStatus;
}

function getMeta() { return _meta; }
function getManifest() { return _manifest; }

export {
  DATA_ROOT,
  loadManifest, loadRun, loadProgramStatus,
  getMeta, getManifest,
  inflateGz, hashState, fmtNum, fmtPct, fmtDollars,
};
