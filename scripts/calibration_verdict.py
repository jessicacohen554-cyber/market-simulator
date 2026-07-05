"""Reproducible calibration determination for an ISO backcast keeper.

Implements ``docs/calibration-determination-rubric.md``: reads a run's COMMITTED
artifacts only — the registry sidecar, the run payload, the per-(ISO, year)
benchmark parts, the bundle config, the bundle's calibration attestation, and
the bundle's legitimacy-diagnostics artifact (``legitimacy_diagnostics.json``,
written by ``scripts/legitimacy_diagnostics.py --json-out``, scored as C7
diurnal shape and C8 forced-energy share) — and emits a ``PASS`` /
``CAVEAT`` / ``FAIL`` per criterion plus one overall
determination in ``{CALIBRATED, CALIBRATED-WITH-CAVEATS, NOT-YET}``. It never
re-solves the LP and never touches the gitignored ``dispatch``/``system``
parquets, so re-running it on any keeper reproduces the verdict byte-for-byte.

The model side is the grid-delivered basis (grid LP dispatch, no behind-the-meter
CHP add-back); the actual side is EIA-923 minus the per-class BTM host supply
(``classFull``) and EIA-930 grid totals — model-grid vs actual-grid, the same
numbers the dashboard renders (``scripts/render_calibration_html.py``).

Stdlib-only (json, gzip, base64, re, math) so it runs anywhere the committed
artifacts are checked out, with no pandas / numpy / model import.

Usage:
    python scripts/calibration_verdict.py results/calibration/<name>
    python scripts/calibration_verdict.py --run-id <id>
    python scripts/calibration_verdict.py --json results/calibration/<name>
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "frontend" / "data" / "backcast"
REGISTRY_DIR = DATA_DIR / "registry"
RUNS_DIR = DATA_DIR / "runs"
BENCH_DIR = DATA_DIR / "bench"
# Per-year EIA-923 completeness parts (scripts/audit_eia923_completeness.py): the
# committed source of truth for which (ISO, class) actuals are complete enough to
# gate in a preliminary-vintage year. Stdlib-readable so this scorer stays
# pandas/numpy-free.
COMPLETENESS_DIR = DATA_DIR / "completeness"

# Statuses (per criterion-year and aggregated).
PASS, CAVEAT, FAIL, SKIPPED = "PASS", "CAVEAT", "FAIL", "SKIPPED"
# Failure classifications (rubric §1).
MODEL_MISS = "MODEL MISS"
MEASURED_LIMIT = "ACCEPTED MEASURED-INPUT LIMITATION"
# Overall determinations.
CALIBRATED = "CALIBRATED"
CALIBRATED_CAVEATS = "CALIBRATED-WITH-CAVEATS"
NOT_YET = "NOT-YET"

# --- fuel-family class membership (plant_taxonomy.classes_for_fuel930 roll-up) --
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL_CLASSES = ("COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC", "COAL")
# Classes excluded from the per-class fuel-mix gate (C1), each justified in the
# rubric: CT_CHP is a BTM peaker the grid LP zeroes by construction; OTHER /
# OTHER_FOSSIL are the mixed-plant reconciliation bucket, not merit-order classes.
FUELMIX_EXCLUDED = frozenset({"CT_CHP", "OTHER", "OTHER_FOSSIL"})

# --- tolerances (rubric §1) -------------------------------------------------
# C1 fuel-mix — the universal class gate (mirrors classInTol in the run
# explorer, docs/codebase-site/backcast-runs.html; supersedes the old ±5%/±1 TWh
# size-tiered band): a class passes iff BOTH (a) its grid-delivered volume miss
# |model−actual| is within min(2.0% of ISO total load, 8 TWh), AND (b) its
# share of total generation is within 3.0 percentage points of the actual share.
# The volume band scales with system size (≈2 pp of load) but is capped at an
# absolute 8 TWh so it can't balloon on large ISOs (2% of an 800 TWh system would
# be 16 TWh, letting a small class drift far on the margin). Applied uniformly
# across classes and ISOs; the share band stops a class passing on volume alone
# while still misrepresenting the mix. Using total LOAD (= gen + net imports)
# rather than generation so net-importing ISOs get the correct ≈2 pp band; for
# energy-only ISOs with no interchange, load = gen and the band is unchanged.
# 2026-07-02 rubric re-balance (docs/calibration-determination-rubric.md §1):
# loosened from 1.0%/5 TWh/1.5 pp — the old bands failed keepers on ±1–2 TWh
# small-class residuals that are TWh noise, not a structural miss, while a
# genuine structural miss (e.g. MISO CC_REGULAR +47 TWh / +7.7 pp) still FAILs
# the new bands by a wide margin. Paired with a TIGHTER C3 (price) gate below.
FUELMIX_VOL_LOAD_FRAC = 0.02  # volume band = 2.0% of ISO total load ...
FUELMIX_VOL_CAP_TWH = 8.0  # ... but never more than an absolute 8 TWh
FUELMIX_SHARE_PP = 3.0  # +/-3.0 share percentage points of total generation
# Non-fossil fuels whose grid actual comes from EIA-930 (not 923) for the
# system-total used by the share/volume bands (matches totalGen in the run
# explorer, docs/codebase-site/backcast-runs.html).
NONFOSSIL_FUELS = ("nuclear", "wind", "solar")

# D-10 free-class rescore (audit §7 D-10 / §4 L-rows): the per-ISO set of C1
# classes whose actual is a MEASURED REALIZATION the model is pinned to — so a C1
# pass there scores plumbing, not skill. Declared from the audit L-rows, not
# inferred (mirrors the D-5 overlay registry pattern):
#   L1 wind/solar (delivered-CF upper bound), L3 nuclear (measured monthly CF),
#   L6 hydro (monthly budgets) + MISO Manitoba firm imports, L4 CHP (measured
#   export floor), L2 NYISO net imports (measured reconciliation band).
# C1 only scores the fossil gas/coal families, so in practice the free-class
# rescore drops the CHP subclasses (CC_CHP / ST_CHP; CT_CHP is already
# C1-excluded); wind/solar/nuclear/hydro/imports are declared for provenance and
# excluded harmlessly (they are never C1 rows). No gate — the number itself is
# the deliverable (the audit's "pinned-class gate inflation" made visible).
_PINNED_CLASSES_COMMON = frozenset(
    {"wind", "solar", "nuclear", "hydro", "CC_CHP", "CT_CHP", "ST_CHP"}
)
PINNED_CLASSES_BY_ISO: dict[str, frozenset[str]] = {
    "ERCOT": _PINNED_CLASSES_COMMON,
    "CAISO": _PINNED_CLASSES_COMMON,
    "PJM": _PINNED_CLASSES_COMMON,
    "MISO": _PINNED_CLASSES_COMMON | {"imports"},  # L6 Manitoba firm-hydro block
    "NYISO": _PINNED_CLASSES_COMMON | {"imports"},  # L2 net-interchange band
    "NEISO": _PINNED_CLASSES_COMMON,
}

SYSVOL_TOL = 0.025  # +/-2.5% gas/coal family grid-delivered
SYSVOL_MIN_TWH = 10.0  # below this a family is immaterial: C1's per-class
# absolute band governs it, so the ±2.5% system-volume gate is N/A (e.g. NEISO
# coal ~0.3 TWh — a percent band on a near-zero family is pure noise).
DISP_MIN_TWH = 5.0  # below this a fleet's hourly r/NRMSE is degenerate (NEISO
# coal); the per-class C1 absolute band is the meaningful check, not correlation.
VINTAGE_RECONCILE_FRAC = 0.97  # render_calibration_html._VINTAGE_RECONCILE_FRAC
PRELIM_923_FROM_YEAR = 2025  # current-year preliminary EIA-923 vintage
# C3 price gate — TIGHTENED in the 2026-07-02 rubric re-balance (paired with the
# looser C1 above): price accuracy is the primary market signal the backcast is
# judged on, so C3 now sits at the tight end of the playbook's 5-10% band. The
# energy-only LP dual still structurally under-shoots the actual LMP (reserve /
# scarcity / uplift adders it does not model), but that known gap is what the
# structural reserve/scarcity mechanisms are for — it is no longer absorbed by a
# wide tolerance.
PRICE_MEAN_TOL = 0.05  # +/-5% mean LMP (tight end of playbook 5-10%; was 8%)
PRICE_SHAPE_NRMSE_MAX = 0.15  # monthly load-weighted price NRMSE (was 0.20)
TAIL_LO, TAIL_HI = 0.7, 1.5  # tail hours within [0.7x, 1.5x] of actual (was [0.5x, 2x])
DISP_R_FLOOR = 0.70  # fleet hourly pearson r floor (gas, coal)
DISP_NRMSE_MAX = 0.30  # fleet hourly NRMSE ceiling (gas, coal)
CO2_TOL = 0.07  # +/-7% vs eGRID
STORAGE_TOL = 0.30  # +/-30% storage throughput (cycling realism)
STORAGE_SHAPE_R_FLOOR = 0.50  # monthly discharge pearson r floor (both sides
# on the positive/discharge basis — see rubric §C5c 2026-07-03 alignment fix)
STORAGE_SHAPE_MIN_CV = 0.25  # C5c degeneracy guard: actual monthly-discharge
# coefficient of variation below this leaves no seasonal shape to correlate
# (a flat TRUE model would score r=0 and fail); the year is SKIPPED and C5b
# scores the volume. Mirrors C4's degenerate-correlation rule.
VRE_TOL = 0.10  # +/-10% advisory band for solar/wind (report-only)

# Per-ISO scarcity-tail definition (rubric §5): (threshold $/MWh).
TAIL_THRESHOLD = {
    "ERCOT": 200.0,
    "PJM": 200.0,
    "MISO": 200.0,
    "CAISO": 200.0,
    "NYISO": 300.0,
    "NEISO": 300.0,
}

# Governance: outage sources that are exogenous availability events (rubric C6.4).
EXOGENOUS_OUTAGE_SOURCES = frozenset({"historic", "statistical"})
# scenario_config flags that, if truthy, indicate a forbidden fitted mechanism
# (output-pinning / price-residual adder). Curated by exact name to avoid false
# positives on legitimate structural terms (e.g. wefor_residual, a renewable
# forecast-error term). Empty today; extend as such a flag is ever introduced.
FORBIDDEN_FLAGS: tuple[str, ...] = ()

# Caveat budget / quorum (rubric §2). Soft budget cut 3 -> 2 in the 2026-07-02
# re-balance (Option A): C3 stays SOFT, but with three price sub-criteria a
# 3-caveat budget let ALL of price (mean + shape + tail) be caveated away at
# once — 2 means at most two soft criteria may ride a documented caveat.
MAX_HARD_CAVEATS = 1
MAX_SOFT_CAVEATS = 2

# Criterion id -> (label, HARD?).
HARD = True
SOFT = False
CRITERIA = {
    "fuelmix": ("C1 fuel-mix by class (grid-delivered)", HARD),
    "sysvol": ("C2 system volume (gas/coal families)", HARD),
    "price_mean": ("C3a mean LMP", SOFT),
    "price_shape": ("C3b price duration/shape", SOFT),
    "price_tail": ("C3c price tail / scarcity", SOFT),
    "dispatch_corr": ("C4 fleet hourly dispatch correlation", SOFT),
    "co2": ("C5a CO2 vs eGRID", SOFT),
    "storage": ("C5b storage throughput", SOFT),
    "storage_shape": ("C5c storage dispatch shape", SOFT),
    "governance": ("C6 governance gate", HARD),
    "shape": ("C7 diurnal shape (D-1)", HARD),
    "forced_share": ("C8 forced-energy share (D-2)", HARD),
}


# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------
def _decode_run_js(text: str) -> dict:
    """Decode a ``runs/<id>.js`` payload (``window.BC.runGz[..]="<b64>"``)."""
    m = re.search(r'=\s*"([A-Za-z0-9+/=]+)"', text)
    if not m:
        raise ValueError("no gzip+base64 payload found in run js")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def resolve_run_id(arg: str) -> str:
    """Return the run id for a CLI arg that is either a run id or a bundle dir.

    A run id resolves when its sidecar exists. Otherwise ``arg`` is treated as a
    bundle path and matched against each sidecar's stored ``bundle`` field.
    """
    if (REGISTRY_DIR / f"{arg}.json").exists():
        return arg
    p = Path(arg)
    cand = {arg, p.name, str(p)}
    try:
        cand.add(str(p.resolve().relative_to(REPO)))
    except ValueError:
        pass
    for side in sorted(REGISTRY_DIR.glob("*.json")):
        rec = json.loads(side.read_text())
        if rec.get("bundle") in cand or Path(rec.get("bundle", "")).name == p.name:
            return rec["id"]
    raise SystemExit(
        f"could not resolve a registered run from {arg!r} "
        f"(no registry sidecar and no bundle match)."
    )


def load_artifacts(run_id: str) -> dict:
    """Load every committed artifact the scorer needs for ``run_id``.

    Returns ``{sidecar, payload, bench, config, attestation}``; ``bench`` is
    ``{year: bench_payload}`` and missing pieces are ``None`` so the scorer can
    SKIP rather than crash.
    """
    side_path = REGISTRY_DIR / f"{run_id}.json"
    if not side_path.exists():
        raise SystemExit(f"no registry sidecar for run id {run_id!r}.")
    sidecar = json.loads(side_path.read_text())
    iso = sidecar.get("iso", "ERCOT")

    run_js = RUNS_DIR / f"{run_id}.js"
    payload = _decode_run_js(run_js.read_text()) if run_js.exists() else None

    bench: dict[int, dict] = {}
    for part in sorted((BENCH_DIR / iso).glob("*.json.gz")) if iso else []:
        obj = json.loads(gzip.decompress(part.read_bytes()))
        for y in obj.get("meta", {}).get("years", []):
            bench[int(y)] = obj.get("bench", {})

    bundle_dir = REPO / sidecar["bundle"] if sidecar.get("bundle") else None
    config = None
    attestation = None
    if bundle_dir and bundle_dir.exists():
        rc = bundle_dir / "run_config.json"
        meta = bundle_dir / "meta.json"
        config = {
            "scenario_config": (
                json.loads(rc.read_text()).get("scenario_config", {})
                if rc.exists()
                else {}
            ),
            "meta": json.loads(meta.read_text()) if meta.exists() else {},
        }
        att = bundle_dir / "calibration_attestation.json"
        if att.exists():
            attestation = json.loads(att.read_text())
    legitimacy = None
    if bundle_dir and bundle_dir.exists():
        legit_path = bundle_dir / "legitimacy_diagnostics.json"
        if legit_path.exists():
            legitimacy = json.loads(legit_path.read_text())
    return {
        "sidecar": sidecar,
        "payload": payload,
        "bench": bench,
        "config": config,
        "attestation": attestation,
        "legitimacy": legitimacy,
    }


# ---------------------------------------------------------------------------
# Small numeric helpers (stdlib only)
# ---------------------------------------------------------------------------
def _pct(model: float, actual: float) -> float | None:
    """Signed fractional error ``(model-actual)/actual``; None when undefined."""
    if actual is None or abs(actual) < 1e-9:
        return None
    return (model - actual) / actual


def _wmean(pairs: list[tuple[float, float]]) -> float | None:
    """Demand-weighted mean of ``(value, weight)`` pairs."""
    w = sum(wt for _, wt in pairs)
    if w <= 0:
        return None
    return sum(v * wt for v, wt in pairs) / w


def _nrmse(model: list[float], actual: list[float]) -> float | None:
    """Normalised RMSE of two equal-length monthly vectors (skip None cells)."""
    cells = [(m, a) for m, a in zip(model, actual) if m is not None and a is not None]
    if not cells:
        return None
    mean_a = sum(a for _, a in cells) / len(cells)
    if abs(mean_a) < 1e-9:
        return None
    rmse = math.sqrt(sum((m - a) ** 2 for m, a in cells) / len(cells))
    return rmse / mean_a


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------
def _ledger_match(exceptions: list[dict], criterion: str, year: int, key: str | None):
    """Return the ledger entry matching (criterion, year, class/family) or None.

    ``key`` is the class (fuelmix) or family (sysvol/dispatch_corr); criteria
    without a sub-key match on (criterion, year) alone.
    """
    for e in exceptions or []:
        if e.get("criterion") != criterion or int(e.get("year", -1)) != int(year):
            continue
        ekey = e.get("klass") or e.get("family")
        if key is None or ekey is None or str(ekey) == str(key):
            return e
    return None


def _apply_ledger(rec: dict, exceptions: list[dict]) -> dict:
    """Reclassify an out-of-tolerance result to CAVEAT iff the ledger documents it.

    A FAIL with a matching ledger entry becomes a CAVEAT classified ACCEPTED
    MEASURED-INPUT LIMITATION; a FAIL without one stays a FAIL (MODEL MISS).
    """
    if rec["status"] != FAIL:
        return rec
    entry = _ledger_match(exceptions, rec["criterion"], rec["year"], rec.get("key"))
    if entry:
        rec["status"] = CAVEAT
        rec["classification"] = MEASURED_LIMIT
        rec["ledger_reason"] = entry.get("reason", "")
    return rec


# ---------------------------------------------------------------------------
# EIA-923 completeness map (per-year committed part)
# ---------------------------------------------------------------------------
_COMPLETENESS_CACHE: dict | None = None


def _completeness_map() -> dict:
    """Return ``{year: {iso: {class: record}}}`` from the committed parts.

    Reads every ``completeness/eia923_<year>.json`` produced by
    ``scripts/audit_eia923_completeness.py``. Cached after the first load.
    Returns an empty map when the directory is absent (no preliminary-year
    completeness has been audited yet — every class then falls back to the blanket
    preliminary-vintage skip).
    """
    global _COMPLETENESS_CACHE
    if _COMPLETENESS_CACHE is not None:
        return _COMPLETENESS_CACHE
    out: dict[int, dict] = {}
    if COMPLETENESS_DIR.exists():
        for part in sorted(COMPLETENESS_DIR.glob("eia923_*.json")):
            obj = json.loads(part.read_text())
            out[int(obj["year"])] = obj  # full part: carries isos + families
    _COMPLETENESS_CACHE = out
    return out


def class_is_gated(iso: str, klass: str, year: int) -> bool:
    """Whether (iso, class) has a complete-enough 923 actual to gate in ``year``.

    Complete-vintage years (those with no completeness part) always gate — only a
    preliminary vintage with an audited completeness part restricts gating to the
    verified-complete, verified-complete-family classes
    (:func:`audit_eia923_completeness.audit`'s ``gate`` flag).
    """
    cmap = _completeness_map()
    if year not in cmap:
        return True  # complete vintage / no preliminary audit -> gate as usual
    rec = cmap[year].get("isos", {}).get(iso.upper(), {}).get(klass)
    return bool(rec and rec.get("gate"))


def family_is_complete(iso: str, family: str, year: int) -> bool:
    """Whether ``family`` (``gas``/``coal``) is fully reported for (iso, year).

    Complete-vintage years (no completeness part) are always complete — C2 then
    defers to the per-class C1 gate as it always has. A preliminary year defers
    only the families the audit flagged complete; the rest fall back to the
    EIA-930 family aggregate gate.
    """
    cmap = _completeness_map()
    if year not in cmap:
        return True
    return bool(cmap[year].get("families", {}).get(iso.upper(), {}).get(family))


# ---------------------------------------------------------------------------
# Per-criterion scoring (one record per criterion-year, pre-ledger)
# ---------------------------------------------------------------------------
def _gen_totals(ypay: dict, ybench: dict) -> tuple[float, float]:
    """System model/actual TOTAL generation (TWh), grid-delivered.

    Mirrors ``totalGen`` in the run explorer (docs/codebase-site/
    backcast-runs.html) exactly so the verdict's C1 bands match
    the dashboard scorecard. Each benchmarked class is counted ONCE: ``classFull``
    now carries the grid-delivered actual for every class — fossil (EIA-923 − BTM
    CHP), nuclear (EIA-923) and the variable renewables wind/solar on the EIA-930
    grid basis (distribution-connected / net-metered BTM PV removed in
    ``render_calibration_html``, the same source-authority as
    :func:`results.calibration.actuals_source`). actual = Σ ``classFull``; model =
    Σ ``gmModel`` over those same class keys. The earlier ``+ EIA-930
    nuclear/wind/solar`` term double-counted the renewables and re-introduced the
    BTM-inflated EIA-923 solar through ``classFull``, inflating the share
    denominator (NEISO 2023 read a_gen ≈ 128 vs the true grid ≈ 97 TWh).
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    a_gen = sum(float(v) for v in cf.values())
    m_gen = sum(float(gm.get(g, 0.0)) for g in cf)  # over the classFull keys
    return m_gen, a_gen


def _total_load(ypay: dict, a_gen: float) -> float:
    """Total load served (TWh) = sum of zone demand from the LMP payload.

    For ISOs with scheduled interchange folded into demand (NEISO, NYISO, …),
    this equals generation + net imports — the correct denominator for the
    ≈1 pp volume band.  Falls back to ``a_gen`` when zone data is absent.
    """
    lmp = ypay.get("lmp", {})
    if not lmp:
        return a_gen
    return sum(float(z.get("d", 0.0)) for z in lmp.values())


def score_fuelmix(
    year: int, ypay: dict, ybench: dict, iso: str = "ERCOT"
) -> list[dict]:
    """C1 — per-class grid-delivered fuel-mix, the universal gate.

    A class passes iff BOTH its grid-delivered volume miss is within
    min(2.0% of ISO total load, 8 TWh) AND its share of total generation is
    within 3.0 pp of actual (the run explorer's ``classInTol`` on the
    gmModel/classFull basis).

    Gating is restricted to (ISO, class) pairs whose EIA-923 actual is VERIFIED
    COMPLETE for the year. A complete-vintage year (no committed completeness part)
    gates every benchmarked class as before. A PRELIMINARY-EIA-923 year (e.g. 2025
    today) gates only the classes the completeness audit
    (:mod:`scripts.audit_eia923_completeness`) flagged ``gate`` — a class whose own
    plants ALL reported AND whose whole fossil family reported (so the
    vintage-reconcile leaves its per-class actual un-scaled). Every other class is
    emitted SKIPPED (recorded, never a silent pass): its plant data is incomplete,
    so there is no trustworthy per-class actual to gate against. The C2 family
    system-volume gate still covers the skipped classes via the authoritative
    EIA-930 grid reconcile. The map auto-extends as a year's 923 finalises: re-run
    the audit and the now-complete classes begin gating with no code change.
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    m_gen, a_gen = _gen_totals(ypay, ybench)
    total_load = _total_load(ypay, a_gen)
    vol_band = min(FUELMIX_VOL_LOAD_FRAC * total_load, FUELMIX_VOL_CAP_TWH)
    out = []
    classes = [c for c in (*GAS_CLASSES, *COAL_CLASSES) if c not in FUELMIX_EXCLUDED]
    cmap_year = _completeness_map().get(year, {}).get("isos", {}).get(iso.upper(), {})
    for c in classes:
        a = cf.get(c)
        if a is None:
            continue  # class not benchmarked for this ISO-year
        a = float(a)
        m = float(gm.get(c, 0.0))
        d = m - a
        if m_gen > 0 and a_gen > 0:
            share_pp = 100.0 * m / m_gen - 100.0 * a / a_gen
        else:
            share_pp = None
        if not class_is_gated(iso, c, year):
            comp = cmap_year.get(c, {})
            why = comp.get("status", "incomplete")
            reasons = "; ".join(comp.get("reasons", [])) or "no per-class actual"
            rec = {
                "criterion": "fuelmix",
                "key": c,
                "year": year,
                "status": SKIPPED,
                "classification": None,
                "metric": f"{c} grid-delivered TWh + share of generation",
                "model": round(m, 3),
                "actual": round(a, 3),
                "share_pp": round(share_pp, 2) if share_pp is not None else None,
                "tol": None,
                "completeness": why,
                "magnitude": (
                    f"preliminary EIA-923 vintage: {why} plant data ({reasons}); "
                    "not gated — C2 family grid reconcile covers this class"
                ),
                "vintage_gap_twh": round(d, 3),  # report-only; does not gate
            }
            out.append(rec)
            continue
        vol_ok = a_gen > 0 and abs(d) <= vol_band
        share_ok = abs(share_pp) <= FUELMIX_SHARE_PP if share_pp is not None else True
        if vol_ok and share_ok:
            status, classification = PASS, None
        else:
            status, classification = FAIL, MODEL_MISS
        mag = f"{d:+.2f} TWh"
        if share_pp is not None:
            mag += f", share {share_pp:+.1f}pp"
        if status == FAIL:
            breach = "/".join(
                lab
                for lab, good in (("volume", vol_ok), ("share", share_ok))
                if not good
            )
            mag += f" ({breach} out of band)"
        rec = {
            "criterion": "fuelmix",
            "key": c,
            "year": year,
            "status": status,
            "classification": classification,
            "metric": f"{c} grid-delivered TWh + share of generation",
            "model": round(m, 3),
            "actual": round(a, 3),
            "share_pp": round(share_pp, 2) if share_pp is not None else None,
            "tol": (
                f"±min({FUELMIX_VOL_LOAD_FRAC * 100:.1f}% ISO-load, "
                f"{FUELMIX_VOL_CAP_TWH:g} TWh) = ±{vol_band:.2f} TWh "
                f"& ±{FUELMIX_SHARE_PP:g}pp share"
            ),
            "completeness": cmap_year.get(c, {}).get("status", "complete"),
            "magnitude": mag,
        }
        out.append(rec)
    return out


def score_sysvol(year: int, ypay: dict, ybench: dict, iso: str = "ERCOT") -> list[dict]:
    """C2 — gas/coal family system volume, folded into the per-class universal gate.

    For COMPLETE-VINTAGE years a family passes iff EVERY constituent fossil class
    is within the universal per-class gate (|model−actual| within the C1 volume
    band AND share within ±FUELMIX_SHARE_PP) — the same scale-relative band C1
    applies, evaluated per class rather than on the netted family aggregate. This
    retires the old ±2.5%-of-family percent band, which had two failure modes: it
    (a) INVENTED a family fail when a mid-size family's small absolute miss
    exceeded 2.5% of itself (e.g. ERCOT coal +1.75 TWh = +3.0% of a 58 TWh family,
    yet only +0.34 pp of generation and well inside the C1 volume band), and (b)
    MASKED a real per-class miss when offsetting class errors netted out across the
    family (e.g. a CT_PEAKER over-build cancelled by a CC under-build summing to
    ~0% at the family level). The per-class roll-up does neither: it nets nothing.

    For a PRELIMINARY-EIA-923 family — one the completeness audit flags as not
    fully reported (:func:`family_is_complete`) — there is no trustworthy per-class
    actual (missing plants under-report thermal; EIA-930 carries no per-class
    split), so the family aggregate vs the authoritative EIA-930 grid total is the
    only available volume check — retained here as the ±2.5% family fallback,
    explicitly scoped to the no-per-class-data case. A preliminary year whose
    family DID fully report (e.g. ERCOT coal 2025) defers to the C1 per-class gate
    exactly like a complete vintage — only the still-incomplete families fall back.
    """
    gm = ypay.get("gmModel", {})
    cf = ybench.get("classFull", {})
    e930 = ybench.get("e930", {})
    m_gen, a_gen = _gen_totals(ypay, ybench)
    total_load = _total_load(ypay, a_gen)
    vol_band = min(FUELMIX_VOL_LOAD_FRAC * total_load, FUELMIX_VOL_CAP_TWH)
    out = []
    for fam, classes in (("gas", GAS_CLASSES), ("coal", COAL_CLASSES)):
        scored = [c for c in classes if c not in FUELMIX_EXCLUDED]
        m = sum(float(gm.get(c, 0.0)) for c in scored)
        a923 = sum(float(cf.get(c, 0.0)) for c in scored)
        a930 = float(e930.get(fam, 0.0)) or None
        use_family_fallback = not family_is_complete(iso, fam, year)
        if max(a923, a930 or 0.0) < SYSVOL_MIN_TWH:
            out.append(
                _skip(
                    "sysvol",
                    year,
                    f"{fam} family immaterial (<{SYSVOL_MIN_TWH:g} TWh); "
                    "governed by the C1 per-class absolute band",
                    key=fam,
                )
            )
            continue
        if use_family_fallback:
            # EIA-930 NG:NG includes ALL gas-fired generation at the grid
            # meter (CC, CT, ST — including CHP exports), so the model sum
            # must also include every gas class, not just the C1-scored
            # subset.  The scored list excludes CT_CHP (a BTM class ungated
            # in C1), but omitting it here creates an apples-to-oranges gap
            # of ~6 TWh/yr in ERCOT.
            m_fam = sum(float(gm.get(c, 0.0)) for c in classes)
            actual = a930
            if fam == "gas" and actual is not None and "other" in e930:
                actual -= max(
                    0.0,
                    float(cf.get("OTHER", 0.0))
                    + float(cf.get("biomass", 0.0))
                    - float(e930.get("other", 0.0)),
                )
            reconciled = bool(actual and a923 < VINTAGE_RECONCILE_FRAC * actual)
            err = _pct(m_fam, actual) if actual else None
            ok = err is not None and abs(err) <= SYSVOL_TOL
            out.append(
                {
                    "criterion": "sysvol",
                    "key": fam,
                    "year": year,
                    "status": PASS if ok else (FAIL if err is not None else SKIPPED),
                    "classification": None if ok else MODEL_MISS,
                    "metric": f"{fam} family grid-delivered TWh (preliminary vintage)",
                    "model": round(m_fam, 2),
                    "actual": round(actual, 2) if actual else None,
                    "tol": f"±{SYSVOL_TOL * 100:.1f}% family (no per-class actual)",
                    "magnitude": f"{err * 100:+.1f}%" if err is not None else "n/a",
                    "source": "EIA-930 grid (preliminary-923 vintage)",
                    "vintage_reconciled": reconciled,
                }
            )
            continue
        breaches = [
            c
            for c in scored
            if cf.get(c) is not None
            and (
                abs(float(gm.get(c, 0.0)) - float(cf[c])) > vol_band
                or (
                    m_gen > 0
                    and a_gen > 0
                    and abs(
                        100.0 * float(gm.get(c, 0.0)) / m_gen
                        - 100.0 * float(cf[c]) / a_gen
                    )
                    > FUELMIX_SHARE_PP
                )
            )
        ]
        out.append(
            {
                "criterion": "sysvol",
                "key": fam,
                "year": year,
                "status": PASS,  # fully-reported family: governed by C1 per-class
                "classification": None,
                "metric": (
                    f"{fam} family — fully reported; per-class volume/share "
                    "governed by the C1 universal gate (no family netting/percent band)"
                ),
                "model": round(m, 2),
                "actual": round(a923, 2),
                "tol": (
                    f"per-class ±min({FUELMIX_VOL_LOAD_FRAC * 100:.1f}% ISO-load, "
                    f"{FUELMIX_VOL_CAP_TWH:g} TWh) = ±{vol_band:.2f} TWh "
                    f"& ±{FUELMIX_SHARE_PP:g}pp share (via C1)"
                ),
                "magnitude": (
                    "all classes in band (C1)"
                    if not breaches
                    else f"C1 flags: {', '.join(breaches)}"
                ),
                "source": "EIA-923 − BTM (grid-delivered), per-class via C1",
                "vintage_reconciled": False,
            }
        )
    return out


def score_price_mean(year: int, ypay: dict, ybench: dict) -> dict:
    """C3a — system load-weighted mean LMP vs actual RT (fallback DA).

    The gated benchmark is named in the record's ``metric`` (``vs RT`` /
    ``vs DA``): the model is structurally a real-time analogue (a
    perfect-foresight dispatch LP prices RT physics, not day-ahead risk
    premia), so RT is the honest benchmark and DA is only a fallback when no
    RT actual is committed. The DA comparison is surfaced separately as a
    non-gated diagnostic (:func:`score_price_mean_da_diagnostic`).
    """
    lmp = ypay.get("lmp", {})
    avg = ybench.get("avgLMP") or {}
    bench_kind = "RT" if avg.get("rt") is not None else "DA"
    actual = avg.get("rt", avg.get("da"))
    # Like-for-like calendar coverage: when the actual series is partial (its
    # monthly vector has empty months — e.g. CAISO 2023, whose Jan–Feb aged
    # out of OASIS retention), the committed actual mean only averages the
    # covered months, so the model side must be masked to the SAME months.
    # Comparing a full-year model mean (which correctly carries the $190
    # gas-crisis January) against a Mar–Dec actual is a coverage artifact,
    # not a price error. Full-coverage years are byte-identical.
    actual_mon = avg.get("rt_mon") if bench_kind == "RT" else avg.get("da_mon")
    covered = [i for i, v in enumerate(actual_mon or []) if v is not None]
    masked = bool(actual_mon) and 0 < len(covered) < 12
    if masked:
        pairs = []
        for z in lmp.values():
            p_mon = z.get("pMon") or [None] * 12
            d_mon = z.get("dMon") or [0.0] * 12
            pairs.extend((p_mon[i], d_mon[i]) for i in covered if p_mon[i] is not None)
    else:
        pairs = [
            (z.get("p"), z.get("d", 0.0))
            for z in lmp.values()
            if z.get("p") is not None
        ]
    model = _wmean(pairs) if pairs else None
    if model is None or actual is None:
        return _skip("price_mean", year, "no model or actual mean LMP")
    err = _pct(model, actual)
    ok = err is not None and abs(err) <= PRICE_MEAN_TOL
    label = "vs RT" if bench_kind == "RT" else "vs DA — no RT actual committed"
    if masked:
        label += f" (model masked to actual's {len(covered)}-month coverage)"
    return {
        "criterion": "price_mean",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": f"system load-weighted mean LMP $/MWh ({label})",
        "benchmark": bench_kind,
        "model": round(model, 2),
        "actual": round(actual, 2),
        "tol": f"±{PRICE_MEAN_TOL * 100:.0f}%",
        "magnitude": f"{err * 100:+.1f}%",
    }


def score_price_mean_da_diagnostic(year: int, ypay: dict, ybench: dict) -> dict | None:
    """C3a DA diagnostic — model mean LMP vs the DA actual, never gated.

    A perfect-foresight dispatch LP is a real-time analogue: the DA−RT spread
    (the DART risk premium — e.g. 2023 ERCOT DA $55.94 vs RT $48.36) is a
    forward risk premium the LP has no mechanism to price, and modeling it
    with offers/adders is forbidden (a fit to the price residual). C3a
    therefore gates on RT; this record makes the DA gap *visible* instead of
    hidden, as a SKIPPED (never PASS/FAIL) diagnostic row. Returns ``None``
    when the DA actual is absent or DA is already the gated fallback
    benchmark (no second series to diagnose).
    """
    avg = ybench.get("avgLMP") or {}
    rt, da = avg.get("rt"), avg.get("da")
    if rt is None or da is None:
        return None  # DA absent, or DA is already the gated benchmark
    lmp = ypay.get("lmp", {})
    # Mirror score_price_mean's partial-coverage masking (same calendar on
    # both sides when the DA actual has empty months).
    da_mon = avg.get("da_mon")
    covered = [i for i, v in enumerate(da_mon or []) if v is not None]
    if da_mon and 0 < len(covered) < 12:
        pairs = []
        for z in lmp.values():
            p_mon = z.get("pMon") or [None] * 12
            d_mon = z.get("dMon") or [0.0] * 12
            pairs.extend((p_mon[i], d_mon[i]) for i in covered if p_mon[i] is not None)
    else:
        pairs = [
            (z.get("p"), z.get("d", 0.0))
            for z in lmp.values()
            if z.get("p") is not None
        ]
    model = _wmean(pairs) if pairs else None
    if model is None:
        return None
    err = _pct(model, da)
    return {
        "criterion": "price_mean",
        "key": "da_diagnostic",
        "year": year,
        "status": SKIPPED,
        "classification": None,
        "metric": "mean LMP vs DA (diagnostic — DART premium, not gated)",
        "benchmark": "DA",
        "model": round(model, 2),
        "actual": round(float(da), 2),
        "tol": "not gated",
        "magnitude": (
            f"{err * 100:+.1f}% vs DA (DA−RT premium ${float(da) - float(rt):+.2f})"
        ),
    }


def score_price_shape(year: int, ypay: dict, ybench: dict) -> dict:
    """C3b — monthly load-weighted price NRMSE (quantitative shape metric)."""
    lmp = ypay.get("lmp", {})
    # Model monthly = demand-weighted across zones of pMon by dMon.
    model_mon: list[float | None] = []
    for mo in range(12):
        pairs = []
        for z in lmp.values():
            pm = (z.get("pMon") or [None] * 12)[mo]
            dm = (z.get("dMon") or [0.0] * 12)[mo]
            if pm is not None:
                pairs.append((pm, dm))
        model_mon.append(_wmean(pairs) if pairs else None)
    avg = ybench.get("avgLMP") or {}
    actual_mon = avg.get("rt_mon") or avg.get("da_mon")
    if actual_mon is None or all(v is None for v in model_mon):
        return _skip("price_shape", year, "no monthly model or actual LMP")
    nrmse = _nrmse(model_mon, actual_mon)
    if nrmse is None:
        return _skip("price_shape", year, "monthly NRMSE undefined")
    ok = nrmse <= PRICE_SHAPE_NRMSE_MAX
    return {
        "criterion": "price_shape",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": "monthly load-weighted price NRMSE",
        "model": round(nrmse, 3),
        "actual": None,
        "tol": f"≤{PRICE_SHAPE_NRMSE_MAX:.2f}",
        "magnitude": f"NRMSE {nrmse:.3f}",
    }


def score_price_tail(year: int, ypay: dict, iso: str) -> dict:
    """C3c — scarcity tail hours (model within [TAIL_LO x, TAIL_HI x] of actual)."""
    ordc = ypay.get("ordc")
    thr = TAIL_THRESHOLD.get(iso, 200.0)
    if not ordc or "hoursGt200" not in ordc:
        return _skip(
            "price_tail",
            year,
            f"hourly scarcity series not in committed payload (tail>${thr:.0f})",
        )
    h = ordc["hoursGt200"]
    actual, model = float(h.get("actual", 0)), float(h.get("model", 0))
    if actual <= 0:
        ok = model <= 0 or model < 50  # token guard against an invented tail
        mag = f"model {model:.0f}h vs actual ~0h (>${thr:.0f})"
    else:
        ratio = model / actual
        ok = TAIL_LO <= ratio <= TAIL_HI
        mag = f"model {model:.0f}h vs actual {actual:.0f}h ({ratio:.2f}×, >${thr:.0f})"
    return {
        "criterion": "price_tail",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": f"hours LMP > ${thr:.0f}/MWh",
        "model": model,
        "actual": actual,
        "tol": f"[{TAIL_LO:g}×, {TAIL_HI:g}×]",
        "magnitude": mag,
    }


def score_dispatch_corr(year: int, ypay: dict) -> list[dict]:
    """C4 — fleet hourly r/NRMSE floors for the gas and coal fleets."""
    rows = {r.get("fuel"): r for r in ypay.get("fuelRows", [])}
    out = []
    for fam in ("gas", "coal"):
        r = rows.get(fam, {})
        rr, nr = r.get("r"), r.get("nrmse")
        if rr is None and nr is None:
            out.append(
                _skip("dispatch_corr", year, f"{fam} hourly fit absent", key=fam)
            )
            continue
        twh = max(abs(r.get("m") or 0.0), abs(r.get("b") or 0.0))
        if twh < DISP_MIN_TWH:
            out.append(
                _skip(
                    "dispatch_corr",
                    year,
                    f"{fam} fleet immaterial (<{DISP_MIN_TWH:g} TWh); "
                    "hourly correlation degenerate",
                    key=fam,
                )
            )
            continue
        ok = (rr is not None and rr >= DISP_R_FLOOR) and (
            nr is not None and nr <= DISP_NRMSE_MAX
        )
        out.append(
            {
                "criterion": "dispatch_corr",
                "key": fam,
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": f"{fam} fleet hourly r / NRMSE",
                "model": f"r={rr} nrmse={nr}",
                "actual": None,
                "tol": f"r≥{DISP_R_FLOOR:.2f}, NRMSE≤{DISP_NRMSE_MAX:.2f}",
                "magnitude": f"r={rr}, NRMSE={nr}",
            }
        )
    return out


def score_co2(year: int, ypay: dict, ybench: dict) -> dict:
    """C5a — CO2 vs eGRID; SKIPPED unless an emissions actual is committed."""
    model = (ypay.get("co2") or {}).get("model")
    actual = (ybench.get("co2") or {}).get("egrid")
    if model is None or actual is None:
        return _skip("co2", year, "no CO2/eGRID actual in committed artifacts")
    err = _pct(model, actual)
    ok = err is not None and abs(err) <= CO2_TOL
    return {
        "criterion": "co2",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": "system CO2 vs eGRID",
        "model": model,
        "actual": actual,
        "tol": f"±{CO2_TOL * 100:.0f}%",
        "magnitude": f"{err * 100:+.1f}%" if err is not None else "n/a",
    }


def score_storage(year: int, ypay: dict, ybench: dict) -> dict:
    """C5b — storage throughput; SKIPPED when EIA-930 has no storage breakout."""
    model = (ypay.get("storage") or {}).get("throughput_twh")
    actual = (ybench.get("storage") or {}).get("throughput_twh")
    if actual is None:
        return _skip(
            "storage",
            year,
            "EIA-930 has no battery/pumped-storage breakout for this BA-year"
            + (f" (model discharged {model:.3f} TWh)" if model else ""),
        )
    if model is None:
        return _skip(
            "storage",
            year,
            "model storage throughput absent (legacy bundle without storage.parquet)"
            + f" (actual {actual:.3f} TWh)",
        )
    err = _pct(model, actual)
    ok = err is not None and abs(err) <= STORAGE_TOL
    return {
        "criterion": "storage",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": "storage discharge throughput TWh",
        "model": model,
        "actual": actual,
        "tol": f"±{STORAGE_TOL * 100:.0f}%",
        "magnitude": f"{err * 100:+.1f}%" if err is not None else "n/a",
    }


def score_storage_shape(year: int, ypay: dict, ybench: dict) -> dict:
    """C5c — monthly storage dispatch shape; SKIPPED when either side is absent."""
    model_mon = (ypay.get("storage") or {}).get("monthly_net_gwh")
    actual_mon = (ybench.get("storage") or {}).get("monthly_net_gwh")
    if actual_mon is None:
        return _skip(
            "storage_shape",
            year,
            "EIA-930 has no monthly storage dispatch breakout for this BA-year",
        )
    if model_mon is None:
        return _skip(
            "storage_shape",
            year,
            "model storage monthly dispatch absent (legacy bundle)",
        )
    if len(model_mon) != 12 or len(actual_mon) != 12:
        return _skip("storage_shape", year, "monthly vector length != 12")
    if any(x is None for x in model_mon) or any(x is None for x in actual_mon):
        return _skip(
            "storage_shape",
            year,
            "monthly vector has one or more missing (null) months",
        )
    m = [float(x) for x in model_mon]
    a = [float(x) for x in actual_mon]
    n = len(m)
    m_mean = sum(m) / n
    a_mean = sum(a) / n
    cov = sum((m[i] - m_mean) * (a[i] - a_mean) for i in range(n)) / n
    m_std = (sum((x - m_mean) ** 2 for x in m) / n) ** 0.5
    a_std = (sum((x - a_mean) ** 2 for x in a) / n) ** 0.5
    # Degeneracy guard (mirrors C4's <5 TWh rule): when the ACTUAL monthly
    # discharge is near-uniform (CV below the floor — e.g. NEISO 2025 PS,
    # CV≈0.14: Northfield cycles near-daily year-round on reserves/regulation),
    # there is no seasonal shape to correlate — the 12-point Pearson is set by
    # reporting noise, and a perfectly flat (i.e. TRUE) model would score
    # r = 0 and FAIL. A metric the truth itself cannot pass is degenerate, so
    # the year is SKIPPED (never a silent pass); the under/over-cycling volume
    # stays fully scored by C5b.
    if a_mean != 0.0 and a_std / abs(a_mean) < STORAGE_SHAPE_MIN_CV:
        return _skip(
            "storage_shape",
            year,
            f"actual monthly storage shape degenerate (CV="
            f"{a_std / abs(a_mean):.3f} < {STORAGE_SHAPE_MIN_CV}): near-uniform "
            "year-round cycling leaves no seasonal shape to correlate; volume "
            "is scored by C5b",
        )
    r = cov / (m_std * a_std) if m_std > 0 and a_std > 0 else 0.0
    ok = r >= STORAGE_SHAPE_R_FLOOR
    return {
        "criterion": "storage_shape",
        "key": None,
        "year": year,
        "status": PASS if ok else FAIL,
        "classification": None if ok else MODEL_MISS,
        "metric": "monthly discharge pearson r",
        "model": round(r, 3),
        "actual": None,
        "tol": f"r ≥ {STORAGE_SHAPE_R_FLOOR}",
        "magnitude": f"r={r:.3f}",
    }


_LEGIT_HOWTO = (
    "run scripts/legitimacy_diagnostics.py --bundle <dir> --iso <ISO> "
    "--json-out <dir>/legitimacy_diagnostics.json and commit it"
)


def score_shape(year: int, legit: dict | None) -> list[dict]:
    """C7 — diurnal shape (audit D-1), from the bundle's committed artifact.

    Reads ``<bundle>/legitimacy_diagnostics.json`` (written by
    ``scripts/legitimacy_diagnostics.py --json-out``) — the verdict never
    recomputes the diagnostic, so the S1 suite stays the single
    implementation. A gated peaker/intermediate class (per the artifact's
    ``d1_gated_classes``) FAILs the year when its hour-of-day profile
    correlation or off-peak CV ratio breaches the artifact's D-1 gates — the
    caiso-42 flat-floor signature (model CV 0.000 vs actual 0.35-0.45) that
    annual-volume bands cannot see. SKIPPED (never a silent pass) when the
    artifact or the year is absent.
    """
    if legit is None:
        return [
            _skip(
                "shape",
                year,
                f"no legitimacy_diagnostics.json in bundle — {_LEGIT_HOWTO}",
            )
        ]
    gates = legit.get("gates", {})
    rows = [
        r
        for r in legit.get("diagnostics", {}).get("D1", {}).get("rows", [])
        if int(r.get("year", -1)) == int(year) and r.get("gated")
    ]
    if not rows:
        return [
            _skip(
                "shape",
                year,
                "no gated-class D-1 rows for this year in legitimacy_diagnostics.json",
            )
        ]
    tol = (
        f"profile r ≥ {gates.get('d1_min_profile_r')} & off-peak CV ratio ≥ "
        f"{gates.get('d1_min_cv_ratio')} (h0-{gates.get('d1_offpeak_last_hour')})"
    )
    out = []
    for r in rows:
        ok = r.get("verdict") != "FAIL"
        out.append(
            {
                "criterion": "shape",
                "key": r.get("class"),
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": f"{r.get('class')} hour-of-day profile vs CAMPD (D-1)",
                "model": f"r={r.get('profile_r')} cv={r.get('model_offpeak_cv')}",
                "actual": f"cv={r.get('actual_offpeak_cv')}",
                "tol": tol,
                "magnitude": (
                    f"profile r {r.get('profile_r')}, off-peak CV ratio "
                    f"{r.get('cv_ratio')}"
                ),
            }
        )
    return out


def score_forced_share(year: int, legit: dict | None) -> list[dict]:
    """C8 — forced-energy share (audit D-2 / CLAUDE.md rule 20).

    Reads the D-2 per-class summary from the bundle's committed
    ``legitimacy_diagnostics.json``: the share of a class's energy dispatched
    AT a binding non-exempt ``min_gen`` floor (nuclear / CHP-steam /
    coal-take-or-pay mechanisms exempt). Gates: < 10 % for peaker classes,
    < 30 % for any merchant class — floors are commitment scaffolding, not
    the dispatch model. Rebuilt-floor shares (``lower_bound``) are flagged in
    the record: a PASS there is a lower bound, never an upper one. SKIPPED
    when the artifact or the year is absent.
    """
    if legit is None:
        return [
            _skip(
                "forced_share",
                year,
                f"no legitimacy_diagnostics.json in bundle — {_LEGIT_HOWTO}",
            )
        ]
    rows = [
        r
        for r in legit.get("diagnostics", {}).get("D2", {}).get("summary", [])
        if int(r.get("year", -1)) == int(year)
    ]
    if not rows:
        return [
            _skip(
                "forced_share",
                year,
                "no D-2 per-class summary for this year in legitimacy_diagnostics.json",
            )
        ]
    out = []
    for r in rows:
        ok = r.get("verdict") != "FAIL"
        lb = (
            " (rebuilt floors exclude the P1-dependent RA bridge — share is a lower bound)"
            if r.get("lower_bound")
            else ""
        )
        out.append(
            {
                "criterion": "forced_share",
                "key": r.get("class"),
                "year": year,
                "status": PASS if ok else FAIL,
                "classification": None if ok else MODEL_MISS,
                "metric": f"{r.get('class')} energy at binding non-exempt floors (D-2)",
                "model": r.get("forced_share"),
                "actual": None,
                "tol": f"< {float(r.get('limit', 0)) * 100:.0f}% of class energy",
                "magnitude": (
                    f"{float(r.get('forced_share', 0)) * 100:.1f}% forced "
                    f"({r.get('forced_twh')} of {r.get('class_total_twh')} TWh)" + lb
                ),
            }
        )
    return out


def _skip(criterion: str, year: int, reason: str, key: str | None = None) -> dict:
    """Build a SKIPPED record (recorded as not-scored, never a silent pass)."""
    return {
        "criterion": criterion,
        "key": key,
        "year": year,
        "status": SKIPPED,
        "classification": None,
        "metric": CRITERIA[criterion][0],
        "model": None,
        "actual": None,
        "tol": None,
        "magnitude": reason,
    }


def score_governance(config: dict | None, attestation: dict | None) -> dict:
    """C6 — governance gate (machine cross-check + required attestation).

    PASS iff config is clean (exogenous outage source, no forbidden flags) AND an
    attestation is present with all four assertions true. FAIL if the machine
    check trips or any assertion is false. UNATTESTED (-> NOT-YET) if no
    attestation file exists — a run cannot be certified unattested.
    """
    sc = (config or {}).get("scenario_config", {})
    meta = (config or {}).get("meta", {})
    outage = meta.get("outage_source") or sc.get("outage_source")
    machine_issues = []
    if outage is not None and outage not in EXOGENOUS_OUTAGE_SOURCES:
        machine_issues.append(
            f"outage_source={outage!r} is not an exogenous availability source"
        )
    for flag in FORBIDDEN_FLAGS:
        if sc.get(flag):
            machine_issues.append(f"forbidden fitted-mechanism flag active: {flag}")

    assertions = [
        "levers_trace_to_measured_input",
        "no_fit_to_price_residuals",
        "no_pinning_to_actuals",
        "outage_filter_exogenous_net_load",
    ]
    if attestation is None or not attestation.get("governance"):
        # A bundle whose attestation carries no governance block (e.g. only a
        # free_parameters DOF ledger) is exactly as unattested as one with no
        # file: nobody has asserted the four governance claims.
        status, detail = (
            "UNATTESTED",
            "no governance attestation in bundle"
            + ("" if attestation is None else " (attestation has no governance block)"),
        )
    else:
        gov = attestation.get("governance", {})
        false_asserts = [a for a in assertions if not gov.get(a, False)]
        if machine_issues:
            status, detail = FAIL, "; ".join(machine_issues)
        elif false_asserts:
            status, detail = FAIL, "attestation false: " + ", ".join(false_asserts)
        else:
            status = PASS
            detail = gov.get("attested_by", "attested")
    if attestation is None and machine_issues:
        detail = "; ".join(machine_issues) + "; and no attestation"
    return {
        "criterion": "governance",
        "key": None,
        "year": None,
        "status": status,
        "classification": None if status == PASS else MODEL_MISS,
        "metric": "every lever measured; no residual fit / pinning; exogenous outages",
        "model": None,
        "actual": None,
        "tol": "pass/fail",
        "magnitude": detail,
        "machine_issues": machine_issues,
    }


# ---------------------------------------------------------------------------
# Aggregation + determination
# ---------------------------------------------------------------------------
def _agg_status(records: list[dict]) -> str:
    """Aggregate per-year statuses for one criterion (FAIL>CAVEAT>PASS>SKIPPED)."""
    s = {r["status"] for r in records}
    if FAIL in s:
        return FAIL
    if CAVEAT in s:
        return CAVEAT
    if PASS in s:
        return PASS
    return SKIPPED


def free_class_score(iso: str, records: list[dict]) -> dict:
    """D-10 — recompute the C1 pass rate with the pinned classes excluded.

    ``records`` are the already-scored per-criterion records; this reads the C1
    (``fuelmix``) rows only. Returns both the all-class C1 pass rate and the
    "free-class" rate that excludes the ISO's pinned classes
    (:data:`PINNED_CLASSES_BY_ISO`) — the classes the audit L-rows show are
    pinned to a measured realization (wind/solar/nuclear/hydro/CHP/imports), so a
    pass there is plumbing. Pass = clean in-tolerance (``PASS``); the denominator
    is the gated (scored, non-``SKIPPED``) C1 rows. No gate — the number is the
    deliverable ("pinned-class gate inflation" made visible; audit §7 D-10).
    """
    pinned = PINNED_CLASSES_BY_ISO.get(iso.upper(), _PINNED_CLASSES_COMMON)
    scored = [
        r
        for r in records
        if r["criterion"] == "fuelmix" and r["status"] in (PASS, FAIL, CAVEAT)
    ]
    free = [r for r in scored if r.get("key") not in pinned]

    def _rate(rows: list[dict]) -> dict:
        return {
            "pass": sum(1 for r in rows if r["status"] == PASS),
            "total": len(rows),
        }

    all_rate, free_rate = _rate(scored), _rate(free)
    return {
        "iso": iso,
        "pinned_classes": sorted(pinned),
        "excluded_from_free": sorted(
            {r.get("key") for r in scored if r.get("key") in pinned}
        ),
        "all": all_rate,
        "free": free_rate,
        "headline": (
            f"C1 all {all_rate['pass']}/{all_rate['total']} · "
            f"free {free_rate['pass']}/{free_rate['total']}"
        ),
    }


def determine(run_id: str) -> dict:
    """Score one run from its committed artifacts (rubric §2)."""
    return determine_from_artifacts(run_id, load_artifacts(run_id))


def determine_from_artifacts(run_id: str, art: dict) -> dict:
    """Score one run's loaded artifacts and return the full verdict dict.

    Split out from :func:`determine` so the decision logic can be unit-tested on
    synthetic artifacts without reading files.
    """
    sidecar, payload, bench = art["sidecar"], art["payload"], art["bench"]
    iso = sidecar.get("iso", "ERCOT")
    exceptions = (art["attestation"] or {}).get("exceptions", [])

    target_years = [int(y) for y in sidecar.get("years", [])]
    scorable_years = sorted(int(y) for y in (payload or {}).get("years", {}))
    data_blocked = sorted(set(target_years) - set(scorable_years))

    # Score every criterion-year.
    records: list[dict] = []
    for year in scorable_years:
        ypay = payload["years"][str(year)]
        ybench = bench.get(year, {})
        records += score_fuelmix(year, ypay, ybench, iso)
        records += score_sysvol(year, ypay, ybench, iso)
        records.append(score_price_mean(year, ypay, ybench))
        da_diag = score_price_mean_da_diagnostic(year, ypay, ybench)
        if da_diag is not None:
            records.append(da_diag)
        records.append(score_price_shape(year, ypay, ybench))
        records.append(score_price_tail(year, ypay, iso))
        records += score_dispatch_corr(year, ypay)
        records.append(score_co2(year, ypay, ybench))
        records.append(score_storage(year, ypay, ybench))
        records.append(score_storage_shape(year, ypay, ybench))
        records += score_shape(year, art.get("legitimacy"))
        records += score_forced_share(year, art.get("legitimacy"))

    # Apply the exceptions ledger (FAIL -> CAVEAT where documented).
    for r in records:
        _apply_ledger(r, exceptions)

    gov = score_governance(art["config"], art["attestation"])

    # Aggregate per criterion.
    per_criterion: dict[str, dict] = {}
    for cid, (label, hard) in CRITERIA.items():
        if cid == "governance":
            per_criterion[cid] = {
                "label": label,
                "hard": hard,
                "status": gov["status"],
                "records": [gov],
            }
            continue
        recs = [r for r in records if r["criterion"] == cid]
        per_criterion[cid] = {
            "label": label,
            "hard": hard,
            "status": _agg_status(recs) if recs else SKIPPED,
            "records": recs,
        }

    # Caveat budget.
    hard_caveats = [
        c
        for cid, c in per_criterion.items()
        if c["hard"] and cid != "governance" and c["status"] == CAVEAT
    ]
    soft_caveats = [
        c for cid, c in per_criterion.items() if not c["hard"] and c["status"] == CAVEAT
    ]
    fails = [cid for cid, c in per_criterion.items() if c["status"] == FAIL]
    skipped_soft = [
        cid
        for cid, c in per_criterion.items()
        if not c["hard"] and c["status"] == SKIPPED
    ]
    # An unscored HARD criterion (e.g. C7/C8 when the bundle carries no
    # legitimacy_diagnostics.json) can never be a silent pass: it caps the
    # determination at CALIBRATED-WITH-CAVEATS, exactly like a skipped soft
    # criterion, and is named in the reasons.
    skipped_hard = [
        cid
        for cid, c in per_criterion.items()
        if c["hard"] and cid != "governance" and c["status"] == SKIPPED
    ]

    # Determination (rubric §2).
    reasons: list[str] = []
    if gov["status"] != PASS:
        determination = NOT_YET
        reasons.append(f"governance gate {gov['status']}: {gov['magnitude']}")
    elif fails:
        determination = NOT_YET
        reasons.append(
            "undocumented out-of-tolerance (FAIL) criteria: " + ", ".join(fails)
        )
    elif len(hard_caveats) > MAX_HARD_CAVEATS or len(soft_caveats) > MAX_SOFT_CAVEATS:
        determination = NOT_YET
        reasons.append(
            f"caveat budget exceeded (hard {len(hard_caveats)}/{MAX_HARD_CAVEATS}, "
            f"soft {len(soft_caveats)}/{MAX_SOFT_CAVEATS})"
        )
    else:
        n_caveats = len(hard_caveats) + len(soft_caveats)
        if (
            n_caveats == 0
            and not skipped_soft
            and not skipped_hard
            and not data_blocked
        ):
            determination = CALIBRATED
        else:
            determination = CALIBRATED_CAVEATS
            if n_caveats:
                reasons.append(f"{n_caveats} documented caveat(s)")
            if skipped_hard:
                reasons.append("unscored HARD criteria: " + ", ".join(skipped_hard))
            if skipped_soft:
                reasons.append("unscored soft criteria: " + ", ".join(skipped_soft))
            if data_blocked:
                reasons.append(
                    "data-blocked target year(s): " + ", ".join(map(str, data_blocked))
                )

    return {
        "run_id": run_id,
        "iso": iso,
        "label": sidecar.get("label", run_id),
        "target_years": target_years,
        "scorable_years": scorable_years,
        "data_blocked_years": data_blocked,
        "determination": determination,
        "reasons": reasons,
        "criteria": per_criterion,
        "free_class_score": free_class_score(iso, records),
        "caveats": {
            "hard": [c["label"] for c in hard_caveats],
            "soft": [c["label"] for c in soft_caveats],
            "budget": {"hard_max": MAX_HARD_CAVEATS, "soft_max": MAX_SOFT_CAVEATS},
        },
        "ledger_entries": exceptions,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
_MARK = {PASS: "✓", CAVEAT: "~", FAIL: "✗", SKIPPED: "·", "UNATTESTED": "?"}


def render_text(v: dict) -> str:
    """Render the verdict as a compact, auditable text block."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"CALIBRATION DETERMINATION: {v['determination']}")
    lines.append(f"  run {v['run_id']}  ({v['iso']}: {v['label']})")
    yrs = ", ".join(map(str, v["scorable_years"])) or "none"
    lines.append(f"  scorable years: {yrs}")
    if v["data_blocked_years"]:
        lines.append(
            "  data-blocked years: " + ", ".join(map(str, v["data_blocked_years"]))
        )
    lines.append("=" * 72)
    for cid, c in v["criteria"].items():
        gate = "HARD" if c["hard"] else "soft"
        lines.append(
            f"[{_MARK.get(c['status'], '?')}] {c['status']:7s} {gate:4s}  {c['label']}"
        )
        for r in c["records"]:
            if r["status"] == PASS:
                continue  # keep the block focused on what isn't a clean pass
            key = f" {r['key']}" if r.get("key") else ""
            yr = f" {r['year']}" if r.get("year") else ""
            cls = f"  [{r['classification']}]" if r.get("classification") else ""
            lines.append(f"        {r['status']:7s}{yr}{key}: {r['magnitude']}{cls}")
            if r.get("ledger_reason"):
                lines.append(f"          ledger: {r['ledger_reason']}")
    lines.append("-" * 72)
    fcs = v.get("free_class_score")
    if fcs:
        lines.append(f"D-10 free-class C1: {fcs['headline']}")
        if fcs.get("excluded_from_free"):
            lines.append(
                "  pinned (excluded from free): " + ", ".join(fcs["excluded_from_free"])
            )
    if v["reasons"]:
        lines.append("determination basis:")
        for rsn in v["reasons"]:
            lines.append(f"  - {rsn}")
    else:
        lines.append("determination basis: all criteria pass, governance attested.")
    lines.append("=" * 72)
    return "\n".join(lines)


def headline(v: dict) -> str:
    """One-line determination headline for the calibration-report skill output."""
    extra = f" — {v['reasons'][0]}" if v["reasons"] else ""
    return f"DETERMINATION: {v['determination']} [{v['iso']} {v['label']}]{extra}"


def main() -> None:
    """CLI: score one run (by bundle dir or run id) and print its determination."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "run",
        nargs="?",
        help="bundle dir (results/calibration/<name>) or a run id",
    )
    ap.add_argument("--run-id", help="run id (alternative to the positional bundle)")
    ap.add_argument("--json", action="store_true", help="emit the machine verdict JSON")
    args = ap.parse_args()
    target = args.run_id or args.run
    if not target:
        ap.error("provide a bundle dir or --run-id")
    run_id = args.run_id or resolve_run_id(target)
    verdict = determine(run_id)
    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print(render_text(verdict))
    # Exit nonzero on NOT-YET so a CI gate / the forecast-validation check can
    # assert on the determination directly.
    sys.exit(0 if verdict["determination"] != NOT_YET else 1)


if __name__ == "__main__":
    main()
