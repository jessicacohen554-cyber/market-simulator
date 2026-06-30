/**
 * bc-data.js — Shared data-loading module for backcast pages.
 * Wraps inflate/load/utility functions so Run Explorer and Calibration Status
 * share one API. ES module.
 */

const DATA_ROOT = 'data/backcast';

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

let _meta = null;
let _benchGz = null;
let _completeness = null;
let _status = null;
let _keepers = null;
const _runCache = {};

function _ensureBC() {
  if (!window.BC) window.BC = {};
}

async function _loadScript(url) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = url;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`Failed to load ${url}`));
    document.head.appendChild(s);
  });
}

/** Decompress a base64-encoded gzip string → JSON object. */
function inflateGz(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const ds = new DecompressionStream('gzip');
  const writer = ds.writable.getWriter();
  writer.write(bytes);
  writer.close();
  return new Response(ds.readable).text().then(t => JSON.parse(t));
}

/** Load manifest.js (meta), benchmark.js, completeness.js. Returns meta object. */
async function initBC() {
  _ensureBC();
  if (_meta) return _meta;

  await _loadScript(`${DATA_ROOT}/manifest.js`);
  _meta = window.BC.meta;

  await Promise.all([
    _loadScript(`${DATA_ROOT}/benchmark.js`),
    _loadScript(`${DATA_ROOT}/completeness.js`),
  ]);
  _benchGz = window.BC.benchGz;
  _completeness = window.BC.completeness;

  return _meta;
}

/** Load status.js only (for Calibration Status page). */
async function loadStatus() {
  _ensureBC();
  if (_status) return _status;
  await _loadScript(`${DATA_ROOT}/status.js`);
  _status = window.BC.status;
  return _status;
}

/** Load keepers.json. */
async function loadKeepers() {
  if (_keepers) return _keepers;
  const resp = await fetch(`${DATA_ROOT}/keepers.json`);
  _keepers = await resp.json();
  return _keepers;
}

/** Lazy-load a single run's data by id. Returns decompressed run object. */
async function loadRun(id) {
  if (_runCache[id]) return _runCache[id];
  _ensureBC();
  if (!window.BC.runGz) window.BC.runGz = {};
  await _loadScript(`${DATA_ROOT}/runs/${id}.js`);
  const gz = window.BC.runGz[id];
  if (!gz) throw new Error(`Run ${id} not found after loading script`);
  const data = await inflateGz(gz);
  _runCache[id] = data;
  delete window.BC.runGz[id];
  return data;
}

/** Load a run registry sidecar JSON. */
async function loadRegistry(id) {
  const resp = await fetch(`${DATA_ROOT}/registry/${id}.json`);
  return resp.json();
}

/** Get meta object (must call initBC first). */
function getMeta() { return _meta; }
function getBenchGz() { return _benchGz; }
function getCompleteness() { return _completeness; }

/** Get all ISO names from meta. */
function isoList() {
  return _meta ? Object.keys(_meta) : [];
}

/** Get zones for an ISO. */
function isoZones(iso) {
  return _meta?.[iso]?.zones || [];
}

/** Get years for an ISO. */
function isoYears(iso) {
  return _meta?.[iso]?.years || [];
}

/** Get fuel groups for an ISO. */
function isoGroups(iso) {
  return _meta?.[iso]?.groups || [];
}

/** Get group label map for an ISO. */
function isoGroupLabels(iso) {
  return _meta?.[iso]?.groupLabel || {};
}

/** Decompress benchmark data for an ISO. */
async function loadBench(iso) {
  if (!_benchGz?.[iso]) return null;
  return inflateGz(_benchGz[iso]);
}

/** Pearson correlation coefficient. */
function pearson(x, y) {
  const n = Math.min(x.length, y.length);
  if (n < 2) return NaN;
  let sx = 0, sy = 0, sxy = 0, sx2 = 0, sy2 = 0;
  for (let i = 0; i < n; i++) {
    sx += x[i]; sy += y[i];
    sxy += x[i] * y[i];
    sx2 += x[i] * x[i];
    sy2 += y[i] * y[i];
  }
  const num = n * sxy - sx * sy;
  const den = Math.sqrt((n * sx2 - sx * sx) * (n * sy2 - sy * sy));
  return den === 0 ? 0 : num / den;
}

/** Normalized RMSE (by range). */
function nrmse(actual, model) {
  const n = Math.min(actual.length, model.length);
  if (n < 1) return NaN;
  let sse = 0, mn = Infinity, mx = -Infinity;
  for (let i = 0; i < n; i++) {
    const d = model[i] - actual[i];
    sse += d * d;
    if (actual[i] < mn) mn = actual[i];
    if (actual[i] > mx) mx = actual[i];
  }
  const range = mx - mn;
  return range === 0 ? 0 : Math.sqrt(sse / n) / range;
}

/** ISO color CSS variable name. */
function isoColorVar(iso) {
  return `--iso-${iso.toLowerCase()}`;
}

/** Format helpers. */
function fmtPct(v, digits = 1) {
  return (v * 100).toFixed(digits) + '%';
}

function fmtNum(v, digits = 0) {
  return Number(v).toLocaleString('en-US', { maximumFractionDigits: digits });
}

function fmtDollars(v, digits = 2) {
  return '$' + Number(v).toFixed(digits);
}

/** URL hash state manager. */
const hashState = {
  get() {
    const params = {};
    const hash = window.location.hash.slice(1);
    if (!hash) return params;
    hash.split('&').forEach(pair => {
      const [k, v] = pair.split('=').map(decodeURIComponent);
      if (k) params[k] = v || '';
    });
    return params;
  },
  set(params) {
    const parts = [];
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') {
        parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
      }
    }
    const newHash = parts.join('&');
    if (window.location.hash.slice(1) !== newHash) {
      history.replaceState(null, '', '#' + newHash);
    }
  },
  update(key, value) {
    const p = hashState.get();
    if (value === undefined || value === null || value === '') {
      delete p[key];
    } else {
      p[key] = value;
    }
    hashState.set(p);
  }
};

export {
  DATA_ROOT, MONTHS,
  initBC, loadStatus, loadKeepers, loadRun, loadRegistry, loadBench,
  inflateGz,
  getMeta, getBenchGz, getCompleteness,
  isoList, isoZones, isoYears, isoGroups, isoGroupLabels,
  isoColorVar, pearson, nrmse,
  fmtPct, fmtNum, fmtDollars,
  hashState,
};
