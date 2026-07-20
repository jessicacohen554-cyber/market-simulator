#!/usr/bin/env python
"""Score a T1-X crossover run (FF-0E, plan §2.2).

Consumes a bundle produced by ``scripts/run_capacity_hindcast.py --crossover``
(``results/hindcast/<run>/<iso>/<key>/`` with per-year ``year_<year>.parquet``
:class:`DispatchResult` + evolution ledgers, and a top-level ``meta.json`` whose
``kind == "crossover"``). Emits, into the bundle's ``<cache_dir>``:

* ``crossover_score.json`` — three parts:
  (a) **dispatch skill 2023-2025** vs the committed bench, side by side with the
      ISO's designated keeper backcast scores (the FC-4 *input-gap* columns:
      ``input_gap = |forecast_err| / |keeper_backcast_err|``);
  (b) **capacity events 2023-2025** vs the registry actuals, reusing
      :mod:`scripts.score_capacity_hindcast` verbatim (retirements / additions /
      CO2), in the SAME top-level shape the hindcast scorer emits so a crossover
      bundle also registers on the forecast-validation page
      (``scripts/register_hindcast.py`` reads ``sc.retirements.total_gw`` etc.);
  (c) **forward years (>= 2026)** — invariants / plausibility only. The scorer
      **structurally refuses** (raises) to read any bench or actual for any year
      >= 2026: :func:`_assert_scoreable_year` guards the top of every bench /
      actual loader path, so no H1-2026 file is ever opened (rule 22).
* ``docs/hindcast-reports/<run_id>-crossover-<date>.md`` — the report.

The dispatch-skill ``ypay`` is reconstructed **from the crossover DispatchResult
itself** (a crossover bundle is NOT the calibration bundle layout
:func:`render_calibration_html.build_payload` consumes — it has no
``system.parquet`` / ``dispatch/*.parquet`` / ``btm.parquet``, only the per-year
``year_<year>.parquet`` :class:`DispatchResult` + :class:`FleetContext`). Only
the reconstructible criteria are scored (C1 fuelmix, C3a price-mean, C3b
price-shape, C5a CO2); metrics that need artifacts a crossover bundle does not
carry (C2 system-volume EIA-930 family, C3c hourly scarcity tail, C4 per-plant
CAMPD hourly correlation, C7/C8 legitimacy diagnostics) are reported as DEFERRED
with the reason — never faked.

Nothing here is tuned and no LP is solved. Usage::

    python scripts/score_crossover.py --bundle results/hindcast/<run>
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from market_sim.model.dispatch import DispatchResult  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.results.outputs import (  # noqa: E402
    from_parquet,
    read_demand,
    read_fleet_context,
)

# The capacity-event scorers, reused verbatim (never modified here).
import score_capacity_hindcast as CH  # noqa: E402
import calibration_verdict as V  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from scripts.lib import backcast_artifacts as ba  # noqa: E402

# The ONLY years a crossover is scored for skill on. 2026/2027 are the crossover
# forward-driver years: invariants/plausibility only, and any bench/actual read
# for them is structurally refused (rule 22 quarantine).
SCORED_YEARS = (2023, 2024, 2025)
QUARANTINE_FROM = 2026  # >= this year: NO bench, NO actual, ever.

# Fixed non-leap month-hour edges — identical to the render basis
# (``render_calibration_html._CUM`` uses ``run_calibration_full._DAYS_IN_MONTH``,
# a 28-day February over a fixed 8760-hour year), so the reconstructed monthly
# price vectors align cell-for-cell with the committed bench monthly vectors.
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_CUM = np.cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])  # 13 edges, [0 .. 8760]

# Non-fossil / mixed fuel_type -> bench ``classFull`` key. Fossil gas/coal
# generators are keyed by their model ``plant_group`` (CC_REGULAR, COAL_PRB, …);
# this map covers the generators whose plant_group is empty in the taxonomy.
_FUEL_TO_CLASS = {
    "nuclear": "nuclear",
    "hydro": "hydro",
    "oil": "oil",
    "biomass": "biomass",
    "geothermal": "OTHER",
    "import": "imports",
    # Fallbacks used only when plant_groups is absent for a fossil generator:
    "coal": "COAL",
    "gas_cc": "CC_REGULAR",
    "gas_cc_ccs": "CC_REGULAR",
    "gas_ct": "CT_PEAKER",
    "gas_st": "ST_GAS",
    "hydrogen_ct": "CT_PEAKER",
    "hydrogen_ccgt": "CC_REGULAR",
}


# --------------------------------------------------------------------------- #
# Quarantine guard (rule 22) — refuse any >= 2026 bench/actual read
# --------------------------------------------------------------------------- #
def _assert_scoreable_year(year: int) -> int:
    """Raise for any year >= ``QUARANTINE_FROM``; return the int year otherwise.

    Called at the TOP of every bench / actual loader path so that no locked-test
    or forward-edge file (2026, H1-2026, …) is ever opened. The forward years are
    invariants/plausibility only (part c) — they never reach a bench or an
    actual. This is the structural half of the rule-22 quarantine.
    """
    y = int(year)
    if y >= QUARANTINE_FROM:
        raise ValueError(
            f"year {y} is quarantined (>= {QUARANTINE_FROM}: locked test / "
            "forward edge) — no bench or actual may be read for it (CLAUDE.md "
            "rule 22). Forward crossover years are invariants/plausibility only."
        )
    return y


# --------------------------------------------------------------------------- #
# Bench / actual loaders — each guarded before any file is opened
# --------------------------------------------------------------------------- #
def load_bench_year(iso: str, year: int) -> dict:
    """Committed bench payload for one ISO-year (``bench/<iso>/<year>.json.gz``).

    Mirrors :func:`calibration_verdict.load_artifacts`' bench loop (gzip + json,
    ``bench = obj["bench"]``), but keyed on a single explicit year that is
    ``_assert_scoreable_year``-guarded BEFORE the file is opened, so a
    ``2026.json.gz`` raises before ``gzip.open`` is ever reached.
    """
    _assert_scoreable_year(year)
    part = ba.BENCH / iso / f"{year}.json.gz"
    if not part.exists():
        raise SystemExit(f"no committed bench for {iso} {year}: {part}")
    obj = ba.load_bench_part(part)
    # Belt-and-braces: refuse if the part's own meta smuggles a >= 2026 year.
    for y in obj.get("meta", {}).get("years", []):
        _assert_scoreable_year(y)
    return obj.get("bench", {})


def load_bench(iso: str, years) -> dict[int, dict]:
    """``{year: bench_payload}`` for the given scoreable years."""
    return {int(y): load_bench_year(iso, y) for y in years}


def crossover_actual_co2(iso: str, years) -> dict[int, float]:
    """Facade over :func:`score_capacity_hindcast.actual_co2_by_year`, guarded.

    Asserts every requested year is scoreable BEFORE delegating to the CAMPD
    reader (which is itself restricted to 2023-2025), so a >= 2026 request raises
    before any CAMPD parquet is touched. Returns metric-tonne totals, filtered to
    the requested years.
    """
    for y in years:
        _assert_scoreable_year(y)
    full = CH.actual_co2_by_year(iso)  # CAMPD, internally 2023-2025 only
    return {int(y): full[int(y)] for y in years if int(y) in full}


# --------------------------------------------------------------------------- #
# ypay reconstruction from the crossover DispatchResult
# --------------------------------------------------------------------------- #
def build_gmmodel(res: DispatchResult, ctx) -> dict[str, float]:
    """Grid-delivered model generation mix ``{class: TWh}`` for one year.

    Fossil gas/coal generators are bucketed by their model ``plant_group``
    (``CC_REGULAR``/``COAL_PRB``/…, the same keys the bench ``classFull`` uses);
    non-fossil and unclassified generators by their ``fuel_type`` via
    :data:`_FUEL_TO_CLASS`. Wind/solar come from the dispatched renewable arrays.
    All grid-delivered (the LP dispatch is grid-only), matching the bench
    ``classFull`` basis (EIA-923 − BTM). TWh = MWh / 1e6.
    """
    dispatch = np.asarray(res.dispatch, dtype=float)
    gen_twh = dispatch.sum(axis=1) / 1e6  # (n_gen,)
    fuels = list(ctx.fuel_types)
    groups = list(ctx.plant_groups) if ctx.plant_groups else []
    gm: dict[str, float] = {}
    for g in range(dispatch.shape[0]):
        grp = groups[g] if g < len(groups) else ""
        if grp:  # fossil gas/coal plant-group class
            cls = grp
        else:
            ft = fuels[g] if g < len(fuels) else ""
            cls = _FUEL_TO_CLASS.get(ft, "OTHER")
        gm[cls] = gm.get(cls, 0.0) + float(gen_twh[g])
    gm["wind"] = (
        gm.get("wind", 0.0) + float(np.asarray(res.wind_dispatched).sum()) / 1e6
    )
    gm["solar"] = (
        gm.get("solar", 0.0) + float(np.asarray(res.solar_dispatched).sum()) / 1e6
    )
    return {k: round(v, 4) for k, v in gm.items()}


def build_lmp(res: DispatchResult, demand: np.ndarray | None) -> dict[str, dict]:
    """Per-zone LMP payload ``{zone: {p, d, pMon, dMon}}`` (load-weighted).

    ``p`` is the demand-weighted mean zonal LP dual, ``d`` the zone's total
    demand (TWh), ``pMon``/``dMon`` the same weighted price + demand weight per
    calendar month (Jan-Dec, fixed non-leap edges) — exactly the render's basis
    (:func:`render_calibration_html.build_payload`), so it feeds
    :func:`calibration_verdict.score_price_mean` / ``score_price_shape``
    unchanged. Zone keys are positional (``z0``…) — the scorers weight over
    ``lmp.values()`` and never key on the zone name. Returns ``{}`` when demand
    is unavailable (the caller then defers the load-weighted price metrics).
    """
    if demand is None:
        return {}
    prices = np.asarray(res.prices, dtype=float)  # (n_zones, T)
    dem = np.asarray(demand, dtype=float)  # (n_zones, T)
    nz, T = prices.shape
    lmp: dict[str, dict] = {}
    for z in range(nz):
        p = prices[z]
        d = dem[z] if z < dem.shape[0] else np.zeros(T)
        dtot = float(d.sum())
        pmean = float((p * d).sum() / dtot) if dtot > 0 else float(p.mean())
        p_mon: list = [None] * 12
        d_mon = [0.0] * 12
        for m in range(12):
            lo, hi = int(_CUM[m]), int(min(_CUM[m + 1], T))
            if lo >= T or hi <= lo:
                continue
            ps, ds = p[lo:hi], d[lo:hi]
            dd = float(ds.sum())
            p_mon[m] = (
                round(float((ps * ds).sum()) / dd, 2)
                if dd > 0
                else round(float(ps.mean()), 2)
            )
            d_mon[m] = round(dd / 1e6, 4)
        lmp[f"z{z}"] = {
            "p": round(pmean, 2),
            "d": round(dtot / 1e6, 4),
            "pMon": p_mon,
            "dMon": d_mon,
        }
    return lmp


def model_co2_mt_fullplant(gm: dict[str, float], ybench: dict) -> float | None:
    """Full-plant model CO2 (Mt), the SAME construction the keeper uses (C5a).

    ``Σ_class (gmModel[class] + btmClass[class]) × intensity[class]`` over the
    bench's per-class CO2 intensities — the render's ``_fossil_co2`` on the
    reconstructed mix (rubric v2.3 full-plant basis, measured BTM CHP added
    back). Using the bench intensities and BTM add-back keeps the forecast C5a on
    the identical basis as the keeper backcast C5a, so the input-gap isolates the
    generation-mix difference (which is exactly what C5a checks). ``None`` when
    the bench carries no CO2 intensities.
    """
    co2b = ybench.get("co2") or {}
    intensity = co2b.get("intensity") or {}
    if not intensity:
        return None
    btm = co2b.get("btmClass") or {}
    total = 0.0
    for cls, inten in intensity.items():
        twh = float(gm.get(cls, 0.0)) + float(btm.get(cls, 0.0))
        total += twh * float(inten)
    return round(total, 4)  # Mt


def model_co2_mt_physical(res: DispatchResult, ctx) -> float:
    """Grid-basis physical model CO2 (Mt) from dispatch × emission rate.

    Uses the model's OWN carbon rates (no bench, no BTM add-back). This is the
    quantity the capacity scorer reports and the only CO2 admissible for a
    forward (>= 2026) year, where no bench intensity may be read.
    """
    if res.emissions is not None:
        return round(float(np.asarray(res.emissions).sum()) / 1e6, 4)
    rate = np.asarray(ctx.emission_rate, dtype=float)
    gen_mwh = np.asarray(res.dispatch, dtype=float).sum(axis=1)
    return round(float((gen_mwh * rate).sum()) / 1e6, 4)


def build_ypay(bundle_dir: Path, year: int) -> tuple[dict, dict]:
    """Minimal per-year ``ypay`` for the crossover forecast run + extras.

    Returns ``(ypay, extras)`` where ``ypay`` carries the keys the reused
    scorers read — ``gmModel`` (C1/C5a), ``lmp`` (C3a/C3b), ``co2.model`` (C5a
    full-plant) — and ``extras`` carries reconstruction provenance
    (``physical_co2_mt``, ``has_demand``). Scoreable years only.
    """
    _assert_scoreable_year(year)
    p = bundle_dir / f"year_{year}.parquet"
    if not p.exists():
        raise SystemExit(f"missing crossover dispatch result: {p}")
    res = from_parquet(DispatchResult, p)
    ctx = read_fleet_context(p)
    demand = read_demand(p)
    gm = build_gmmodel(res, ctx)
    ypay = {
        "gmModel": gm,
        "lmp": build_lmp(res, demand),
        "co2": {},  # co2.model filled per-year against the bench intensities
    }
    extras = {
        "physical_co2_mt": model_co2_mt_physical(res, ctx),
        "has_demand": demand is not None,
        "n_gen": int(np.asarray(res.dispatch).shape[0]),
        "n_zones": int(np.asarray(res.prices).shape[0]),
    }
    return ypay, extras


# --------------------------------------------------------------------------- #
# Scalar-error extraction — applied IDENTICALLY to forecast and keeper records
# --------------------------------------------------------------------------- #
_SCORED = (PASS, FAIL, CAVEAT) = (V.PASS, V.FAIL, V.CAVEAT)


def _scalar(cid: str, recs: list[dict]) -> dict | None:
    """One comparable scalar error for a criterion-year from its record list.

    The same function runs on the forecast run's freshly-scored records and on
    the keeper's committed ``determine()`` records, so ``forecast_err`` and
    ``keeper_backcast_err`` are apples-to-apples. Returns ``None`` when the
    criterion is unscored (all SKIPPED / no numeric actual) for the year.

    * ``fuelmix`` (C1): aggregate absolute grid-delivered volume miss,
      ``Σ|model − actual|`` TWh over the gated (non-SKIPPED) class rows, plus the
      per-class detail.
    * ``price_mean`` (C3a): the gated record's fractional error ``(m−a)/a``.
    * ``price_shape`` (C3b): the record's monthly-price NRMSE (lower is better).
    * ``co2`` (C5a): the fractional error ``(m−a)/a``.
    """
    scored = [r for r in recs if r.get("status") in _SCORED]
    if cid == "fuelmix":
        rows = [
            r
            for r in scored
            if r.get("model") is not None and r.get("actual") is not None
        ]
        if not rows:
            return None
        per_class = {
            r["key"]: {
                "model": r["model"],
                "actual": r["actual"],
                "abs_twh": round(abs(float(r["model"]) - float(r["actual"])), 4),
                "status": r["status"],
            }
            for r in rows
        }
        agg = round(sum(d["abs_twh"] for d in per_class.values()), 4)
        return {"err": agg, "signed": agg, "unit": "TWh (Σ|Δ|)", "detail": per_class}
    # single-record criteria
    rows = [r for r in scored if r.get("key") in (None, "None")]
    if not rows:
        return None
    r = rows[0]
    if cid == "price_shape":
        nrmse = r.get("model")
        if nrmse is None:
            return None
        return {
            "err": round(float(nrmse), 4),
            "signed": round(float(nrmse), 4),
            "unit": "NRMSE",
        }
    m, a = r.get("model"), r.get("actual")
    signed = V._pct(m, a) if (m is not None and a is not None) else None
    if signed is None:
        return None
    return {
        "err": round(abs(signed), 4),
        "signed": round(signed, 4),
        "unit": "frac (|Δ|/actual)",
        "model": m,
        "actual": a,
    }


def _input_gap(forecast: dict | None, keeper: dict | None) -> float | str | None:
    """``|forecast_err| / |keeper_err|`` with a divide-by-zero-safe result.

    ``None`` when either side is unscored; ``"inf"`` when the keeper error is
    ~0 (a finite forecast error over a perfect keeper) so the JSON never carries
    a raw ``inf`` and never crashes on the divide.
    """
    if forecast is None or keeper is None:
        return None
    kf = abs(float(keeper["err"]))
    ff = abs(float(forecast["err"]))
    if kf < 1e-12:
        return 0.0 if ff < 1e-12 else "inf"
    return round(ff / kf, 3)


# --------------------------------------------------------------------------- #
# (a) Dispatch skill
# --------------------------------------------------------------------------- #
_METRIC_LABELS = {
    "fuelmix": "C1 fuel-mix (grid-delivered TWh)",
    "price_mean": "C3a system load-weighted mean LMP",
    "price_shape": "C3b monthly price NRMSE",
    "co2": "C5a system CO2 (full-plant basis)",
}
_DEFERRED = {
    "sysvol": "C2 EIA-930 family system-volume: needs the bench e930 family "
    "reconcile the crossover bundle does not carry in a scorer-ready form.",
    "price_tail": "C3c hourly scarcity tail: needs the ORDC/scarcity overlay "
    "payload (ordc.hoursGt200) the crossover DispatchResult does not carry.",
    "dispatch_corr": "C4 per-plant hourly correlation: needs the per-plant CAMPD "
    "b64 hourly bench + per-plant model hourly series (calibration-bundle only).",
    "shape": "C7 diurnal shape: needs the bundle's legitimacy_diagnostics.json "
    "(not produced for a crossover bundle).",
    "forced_share": "C8 forced-share: needs the bundle's legitimacy_diagnostics.json "
    "(not produced for a crossover bundle).",
}


def score_dispatch_skill(bundle_dir: Path, iso: str, keeper_run_id: str | None) -> dict:
    """Part (a): reconstructible dispatch skill vs bench + keeper input-gap."""
    bench = load_bench(iso, SCORED_YEARS)

    # Keeper backcast records (numeric per criterion-year), if a keeper exists.
    keeper_recs: dict[str, dict[int, list]] = {}
    keeper_note = None
    if keeper_run_id:
        try:
            kv = V.determine(keeper_run_id)
            for cid in _METRIC_LABELS:
                by_year: dict[int, list] = {}
                for r in kv["criteria"].get(cid, {}).get("records", []):
                    by_year.setdefault(int(r.get("year", -1)), []).append(r)
                keeper_recs[cid] = by_year
        except SystemExit as exc:  # missing keeper artifacts — degrade, don't crash
            keeper_note = f"keeper {keeper_run_id!r} not scorable: {exc}"
    else:
        keeper_note = f"no keeper registered for {iso} in keepers/{iso}.json"

    metrics: dict[str, dict] = {cid: {} for cid in _METRIC_LABELS}
    extras_by_year: dict[int, dict] = {}
    for year in SCORED_YEARS:
        if not (bundle_dir / f"year_{year}.parquet").exists():
            continue
        ypay, extras = build_ypay(bundle_dir, year)
        extras_by_year[year] = extras
        ybench = bench[year]

        # C5a needs co2.model on the full-plant basis (keeper's construction).
        full_co2 = model_co2_mt_fullplant(ypay["gmModel"], ybench)
        if full_co2 is not None:
            ypay["co2"] = {"model": full_co2}

        # Freshly score the forecast run with the reused scorers.
        fc_records = {
            "fuelmix": V.score_fuelmix(year, ypay, ybench, iso),
            "price_mean": [V.score_price_mean(year, ypay, ybench)],
            "price_shape": [V.score_price_shape(year, ypay, ybench)],
            "co2": [V.score_co2(year, ypay, ybench)],
        }
        for cid in _METRIC_LABELS:
            f_scalar = _scalar(cid, fc_records[cid])
            k_scalar = _scalar(cid, keeper_recs.get(cid, {}).get(year, []))
            row = {
                "forecast_err": None if f_scalar is None else f_scalar["err"],
                "forecast_signed": None if f_scalar is None else f_scalar.get("signed"),
                "keeper_backcast_err": None if k_scalar is None else k_scalar["err"],
                "input_gap": _input_gap(f_scalar, k_scalar),
                "unit": (f_scalar or k_scalar or {}).get("unit"),
                "forecast_status": _agg_status(fc_records[cid]),
            }
            if cid == "fuelmix" and f_scalar is not None:
                row["forecast_per_class"] = f_scalar["detail"]
            if cid == "co2":
                row["basis"] = "full-plant (bench intensities, BTM added back)"
            metrics[cid][str(year)] = row

    return {
        "keeper_run_id": keeper_run_id,
        "keeper_note": keeper_note,
        "metrics": metrics,
        "deferred": dict(_DEFERRED),
        "reconstruction": {
            "note": (
                "ypay rebuilt from year_<year>.parquet DispatchResult + "
                "FleetContext (crossover bundle is not the calibration-bundle "
                "layout build_payload consumes). gmModel/lmp/co2 grid-delivered; "
                "C5a on the keeper's full-plant basis via bench intensities."
            ),
            "per_year": {str(y): e for y, e in extras_by_year.items()},
        },
    }


def _agg_status(records: list[dict]) -> str:
    """FAIL > CAVEAT > PASS > SKIPPED aggregate of a criterion's year records."""
    statuses = {r.get("status") for r in records}
    for s in (V.FAIL, V.CAVEAT, V.PASS):
        if s in statuses:
            return s
    return V.SKIPPED


# --------------------------------------------------------------------------- #
# (b) Capacity events — reuse score_capacity_hindcast verbatim
# --------------------------------------------------------------------------- #
def score_capacity_events(cache_dir: Path, iso: str) -> dict:
    """Part (b): retirements / additions / CO2, 2023-2025, vs registry actuals.

    Reuses :mod:`scripts.score_capacity_hindcast` unchanged. Model ledger events
    are restricted to <= 2025 (a crossover ledger spans 2023-2027) so no forward
    event is scored against nonexistent actuals — and no >= 2026 actual is read.
    Emitted at the TOP LEVEL of ``crossover_score.json`` in the SAME shape the
    hindcast scorer produces (``retirements`` / ``additions`` / ``co2``), so
    ``scripts/register_hindcast.py`` consumes a crossover bundle unchanged.
    """
    ledgers = load_ledgers_for_run(cache_dir)
    actuals = CH.load_actuals(iso)
    mret = CH.model_retirements(ledgers)
    madd = CH.model_additions(ledgers)
    # Restrict model events to the scored window (no forward events vs actuals).
    if not mret.empty:
        mret = mret[mret["year"] <= max(SCORED_YEARS)]
    if not madd.empty:
        madd = madd[madd["year"] <= max(SCORED_YEARS)]

    ret = CH.score_retirements(mret, actuals)
    add = CH.score_additions(madd, actuals)
    model_co2 = {
        str(k): v for k, v in CH.model_co2_by_year(cache_dir).items()
    }  # 2023-2025 only, physical basis
    actual_co2 = {str(k): v for k, v in crossover_actual_co2(iso, SCORED_YEARS).items()}
    return {
        "retirements": ret,
        "additions": add,
        "co2": {"model": model_co2, "actual": actual_co2},
    }


# --------------------------------------------------------------------------- #
# (c) Forward years — invariants / plausibility only (NO bench, NO actual)
# --------------------------------------------------------------------------- #
def forward_invariants(bundle_dir: Path, meta: dict) -> dict:
    """Part (c): plausibility of the >= 2026 forward years — no skill scored.

    Reads only the model's OWN forecast output (``year_<year>.parquet`` — never a
    bench or actual, which are rule-22 quarantined for these years) to record
    cheap invariants: non-negative dispatch, model-only physical CO2 (Mt), total
    grid generation (TWh). Skill against measured actuals is NOT computed.
    """
    start = int(meta.get("start_year", 2023))
    end = int(meta.get("end_year", 2027))
    fwd = [y for y in range(start, end + 1) if y >= QUARANTINE_FROM]
    per_year: dict[str, dict] = {}
    for year in fwd:
        p = bundle_dir / f"year_{year}.parquet"
        if not p.exists():
            continue
        res = from_parquet(DispatchResult, p)
        ctx = read_fleet_context(p)
        disp = np.asarray(res.dispatch, dtype=float)
        prices = np.asarray(res.prices, dtype=float)
        per_year[str(year)] = {
            "model_co2_mt": model_co2_mt_physical(res, ctx),  # model-only, physical
            "total_gen_twh": round(float(disp.sum()) / 1e6, 3),
            "wind_twh": round(float(np.asarray(res.wind_dispatched).sum()) / 1e6, 3),
            "solar_twh": round(float(np.asarray(res.solar_dispatched).sum()) / 1e6, 3),
            "dispatch_nonneg": bool(disp.min() >= -1e-6),
            "price_finite": bool(np.isfinite(prices).all()),
            "n_gen": int(disp.shape[0]),
        }
    return {
        "years": fwd,
        "scored": False,
        "note": (
            "invariants / plausibility only — years >= "
            f"{QUARANTINE_FROM} are quarantined (locked test / forward edge, "
            "rule 22); no bench or actual is read and no skill is scored. Numbers "
            "below are model-only forecast output (physical CO2, grid generation)."
        ),
        "per_year": per_year,
    }


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt(x, spec="+.1%"):
    return "—" if x is None else (x if isinstance(x, str) else format(x, spec))


def write_report(score: dict, report_path: Path) -> None:
    """Render the crossover markdown report."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    iso = score["iso"]
    L: list[str] = []
    L.append(f"# T1-X crossover — {iso} ({score['run_id']})")
    L.append("")
    L.append(
        f"_Generated {stamp} · FF-0E · plan §2.2 · vintage "
        f"{score.get('vintage_year')} · forward boundary "
        f"{score.get('crossover_forward_year')} · keeper "
        f"`{score['dispatch_skill'].get('keeper_run_id')}`_"
    )
    L.append("")
    L.append(
        "Crossover forecast-mode run: **2023-2025** on realized inputs scored for "
        "dispatch skill + capacity events; **forward years (>= 2026)** are "
        "invariants/plausibility only — the scorer structurally refuses to read "
        "any bench or actual for them (rule 22). Nothing here is tuned; no LP was "
        "solved."
    )
    L.append("")
    # (a) dispatch skill
    L.append("## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)")
    L.append("")
    if score["dispatch_skill"].get("keeper_note"):
        L.append(f"> keeper note: {score['dispatch_skill']['keeper_note']}")
        L.append("")
    L.append(
        "`input_gap = |forecast_err| / |keeper_backcast_err|` — the "
        "backcast→forecast input gap (1.0 = forecast drivers reproduce the "
        "backcast-overlay skill; > 1 = forecast is worse)."
    )
    L.append("")
    L.append(
        "| metric | year | forecast err | keeper backcast err | input-gap | status |"
    )
    L.append("|---|--:|--:|--:|--:|:--|")
    for cid, label in _METRIC_LABELS.items():
        for year in SCORED_YEARS:
            row = score["dispatch_skill"]["metrics"].get(cid, {}).get(str(year))
            if not row:
                continue
            unit = row.get("unit") or ""
            frac = "frac" in unit or unit == ""
            fe = _fmt(
                row["forecast_err"],
                "+.1%" if frac and cid in ("price_mean", "co2") else ".3f",
            )
            ke = _fmt(
                row["keeper_backcast_err"],
                "+.1%" if frac and cid in ("price_mean", "co2") else ".3f",
            )
            ig = (
                _fmt(row["input_gap"], ".2f")
                if not isinstance(row["input_gap"], str)
                else row["input_gap"]
            )
            L.append(
                f"| {label} | {year} | {fe} | {ke} | {ig} | {row.get('forecast_status')} |"
            )
    L.append("")
    L.append("**Deferred metrics** (not reconstructible from a crossover bundle):")
    for k, why in score["dispatch_skill"]["deferred"].items():
        L.append(f"- `{k}` — {why}")
    L.append("")
    # (b) capacity events
    L.append("## (b) Capacity events 2023-2025 vs registry actuals")
    L.append("")
    tg = score["retirements"]["total_gw"]
    rr = score["retirements"]["unit_recall_gt300"]
    L.append("| metric | actual | model | err | band |")
    L.append("|---|--:|--:|--:|:--|")
    L.append(
        f"| thermal GW retired | {tg['actual']} | {tg['model']} | "
        f"{_fmt(tg['err_frac'], '+.0%')} | {tg['band']} |"
    )
    L.append(
        f"| unit recall >300MW | {rr['n_big_actual']} units | {rr['matched']} matched | "
        f"{_fmt(rr['recall'], '.0%')} | {rr['band']} |"
    )
    L.append(
        f"| total additions | — | {score['additions']['model_total_gw']} GW | "
        f"(actual {score['additions']['actual_total_gw']} GW) | — |"
    )
    L.append("")
    # (c) forward invariants
    fi = score["forward_invariants"]
    L.append("## (c) Forward years (>= 2026) — invariants / plausibility only")
    L.append("")
    L.append(f"> {fi['note']}")
    L.append("")
    if fi["per_year"]:
        L.append(
            "| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |"
        )
        L.append("|---|--:|--:|:--|:--|")
        for y, d in fi["per_year"].items():
            L.append(
                f"| {y} | {d['model_co2_mt']} | {d['total_gen_twh']} | "
                f"{d['dispatch_nonneg']} | {d['price_finite']} |"
            )
    else:
        L.append("_No forward-year parquet in the bundle._")
    L.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(L))


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def _load_keepers() -> dict:
    """Per-ISO keeper map from the sharded store (legacy monolith fallback)."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from scripts.lib import keeper_store

    return keeper_store.keeper_ids(REPO)


def score_crossover(bundle: Path, report_dir: Path) -> dict:
    """Score a crossover bundle end to end; write the score.json + report."""
    meta = json.loads((bundle / "meta.json").read_text())
    if meta.get("kind") != "crossover":
        raise SystemExit(
            f"{bundle}/meta.json is kind={meta.get('kind')!r}, not 'crossover' — "
            "use scripts/score_capacity_hindcast.py for a plain hindcast."
        )
    iso = meta["iso"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle / iso / meta["cache_key"]

    keeper_run_id = _load_keepers().get(iso)

    dispatch = score_dispatch_skill(cache_dir, iso, keeper_run_id)
    capacity = score_capacity_events(cache_dir, iso)
    forward = forward_invariants(cache_dir, meta)

    run_id = bundle.name
    score = {
        "run_id": run_id,
        "iso": iso,
        "kind": "crossover",
        "variant": meta.get("variant"),
        "vintage_year": meta.get("vintage_year"),
        "crossover_forward_year": meta.get("crossover_forward_year"),
        "scored_years": list(SCORED_YEARS),
        "forward_years": forward["years"],
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # (a)
        "dispatch_skill": dispatch,
        # (b) — TOP LEVEL, hindcast-scorer shape (register_hindcast compatibility)
        "retirements": capacity["retirements"],
        "additions": capacity["additions"],
        "co2": capacity["co2"],
        "bands": CH.BANDS,
        # (c)
        "forward_invariants": forward,
    }
    (cache_dir / "crossover_score.json").write_text(json.dumps(score, indent=2))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = report_dir / f"{run_id}-crossover-{stamp}.md"
    write_report(score, report_path)

    print(f"[crossover] {iso} {run_id}: keeper={keeper_run_id}")
    for cid, label in _METRIC_LABELS.items():
        cells = []
        for year in SCORED_YEARS:
            r = dispatch["metrics"].get(cid, {}).get(str(year))
            if r:
                cells.append(f"{year}:gap={r['input_gap']}")
        print(f"[crossover]   {label}: " + ", ".join(cells))
    print(f"[crossover] score.json: {cache_dir / 'crossover_score.json'}")
    print(f"[crossover] report:     {report_path}")
    return score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        required=True,
        help="run_capacity_hindcast --crossover out-dir (holds meta.json).",
    )
    parser.add_argument(
        "--report-dir", type=Path, default=Path("docs/hindcast-reports")
    )
    args = parser.parse_args(argv)
    score_crossover(args.bundle, args.report_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
