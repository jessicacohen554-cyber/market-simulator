#!/usr/bin/env python
"""Score a T1-X crossover run (FF-0E, plan §2.2).

Consumes a bundle produced by ``scripts/run_capacity_hindcast.py --crossover``
(``results/hindcast/<run>/<iso>/<key>/`` with per-year ``year_<year>.parquet``
:class:`DispatchResult` + evolution ledgers, and a top-level ``meta.json`` whose
``kind == "crossover"``). Emits, into the bundle's ``<cache_dir>``:

* ``crossover_score.json`` — three parts, plus the FC-4 rubric contract
  (``refusal_marker`` + the flat ``metrics`` list
  :func:`scripts.forecast_verdict.score_fc4` reads; folded in from the FF-2D
  session's committed adapter, since deleted — see :func:`rubric_metrics`):
  (a) **dispatch skill 2023-2025** vs the committed bench, side by side with the
      ISO's designated keeper backcast scores (the FC-4 *input-gap* columns:
      ``input_gap = |forecast_err| / |keeper_backcast_err|``), including the
      ``gas_twh``/``coal_twh`` family-volume rows FC-4 bands at ±5 %;
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
CAMPD hourly correlation, C8 legitimacy diagnostics) are reported as DEFERRED
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
_REPO_BOOT = Path(__file__).resolve().parent.parent  # repo root: canonical
if str(_REPO_BOOT) not in sys.path:  # scripts.* sibling imports on direct run
    sys.path.insert(0, str(_REPO_BOOT))

from market_sim.config.plant_taxonomy import COAL_ARTIFACT_FAMILY  # noqa: E402
from market_sim.model.dispatch import DispatchResult  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.results.outputs import (  # noqa: E402
    from_parquet,
    read_demand,
    read_fleet_context,
)

# The capacity-event scorers, reused verbatim (never modified here).
from scripts import calibration_verdict as V  # noqa: E402
from scripts import score_capacity_hindcast as CH  # noqa: E402

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
    "coal": COAL_ARTIFACT_FAMILY,  # family token, resolved to the subclass below
    "gas_cc": "CC_REGULAR",
    "gas_cc_ccs": "CC_REGULAR",
    "gas_ct": "CT_PEAKER",
    "gas_st": "ST_GAS",
    "hydrogen_ct": "CT_PEAKER",
    "hydrogen_ccgt": "CC_REGULAR",
}


# --------------------------------------------------------------------------- #
# Quarantine guard (rule 22) — refuse any bench/actual read outside 2023-2025
# --------------------------------------------------------------------------- #
def _assert_scoreable_year(year: int) -> int:
    """Raise for any year outside ``SCORED_YEARS``; return the int otherwise.

    Called at the TOP of every bench / actual loader path so that no
    out-of-training file is ever opened. The upper bound refuses the locked
    test / forward edge (2026, H1-2026, …) — forward crossover years are
    invariants/plausibility only (part c). The lower bound (FH-1, symmetric by
    design) refuses anything below the training window: a T1-FF window may
    SOLVE 2021 as a seed, but the seed is never scored and no pre-2023 bench
    or actual is ever read (validation/locked tiers both live below 2023 —
    scripts/lib/holdout_policy.py; scoring never leaves 2023-2025).
    """
    y = int(year)
    if y >= QUARANTINE_FROM:
        raise ValueError(
            f"year {y} is quarantined (>= {QUARANTINE_FROM}: locked test / "
            "forward edge) — no bench or actual may be read for it (CLAUDE.md "
            "rule 22). Forward crossover years are invariants/plausibility only."
        )
    if y < min(SCORED_YEARS):
        raise ValueError(
            f"year {y} is below the scoring window (< {min(SCORED_YEARS)}) — "
            "no bench or actual may be read for it (CLAUDE.md rule 22; FH-1 "
            "symmetric lower bound: hindcast seed years are solved, never "
            "scored)."
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
def build_gmmodel(res: DispatchResult, ctx, iso: str) -> dict[str, float]:
    """Grid-delivered model generation mix ``{class: TWh}`` for one year.

    Fossil gas/coal generators are bucketed by their model ``plant_group``
    (``CC_REGULAR``/``COAL_PRB``/…, the same keys the bench ``classFull`` uses);
    non-fossil and unclassified generators by their ``fuel_type`` via
    :data:`_FUEL_TO_CLASS`. Wind/solar come from the dispatched renewable arrays.
    All grid-delivered (the LP dispatch is grid-only), matching the bench
    ``classFull`` basis (EIA-923 − BTM). TWh = MWh / 1e6.

    A generator landing on the generic ``COAL`` class (the crossover fleet
    carries its whole coal fleet that way — the canonical
    ``plant_taxonomy`` class, which no bench keys on) is split to its supply
    class (``COAL_PRB``/``COAL_LIGNITE``/``COAL_BIT``/``COAL_WC``) through
    the SAME chain the keeper backcast uses:
    ``run_calibration_full._coal_supply_class`` on the plant code parsed from
    the unit id (``_plant_codes_from_unit_ids``) — one taxonomy chain, no
    second map (rule 19 ``[R-ONE-MECH]``). This is the third bridge over the
    model-vs-bench class-grain seam :func:`_family_volume` documents (the
    first two: the family rows there; ``PLANT_GROUP_MEMBERS`` in
    ``calibration_verdict``, rubric v2.8). Unsplit, the model's whole coal
    fleet was invisible to :func:`model_co2_mt_fullplant` (which iterates
    the bench's intensity keys) and read 0.0 in every C1 coal-rank row — the
    FC-4 co2 defect traced in
    ``docs/handoffs/FINDING-capx-d5-crossover-co2-2026-08-30.md``. A plant
    the chain cannot resolve stays generic ``COAL`` — the keeper's own
    residual bucket, so the two lanes remain on one basis.
    """
    # Lazy import: the canonical coal-rank chain + unit-id plant-code parse
    # live in the calibration runner (a heavy sibling); imported at call time
    # so module import stays light (same pattern as register_hindcast's lazy
    # check_forecast_invariants import).
    from scripts.run_calibration_full import (  # noqa: PLC0415
        _coal_supply_class,
        _plant_codes_from_unit_ids,
    )

    dispatch = np.asarray(res.dispatch, dtype=float)
    gen_twh = dispatch.sum(axis=1) / 1e6  # (n_gen,)
    fuels = list(ctx.fuel_types)
    groups = list(ctx.plant_groups) if ctx.plant_groups else []
    # numeric_head off for ERCOT — its CAMPD unit ids carry a ``p{code}``
    # token, and its nuclear shares the ``{code}_{gen}`` shape without being
    # plant-code keyed. The exact call run_calibration_full._dispatch_frame
    # makes, so the crossover and the keeper parse codes identically.
    plant_codes = _plant_codes_from_unit_ids(
        list(ctx.unit_ids), numeric_head=iso.upper() != "ERCOT"
    )
    gm: dict[str, float] = {}
    for g in range(dispatch.shape[0]):
        grp = groups[g] if g < len(groups) else ""
        if grp:  # fossil gas/coal plant-group class
            cls = grp
        else:
            ft = fuels[g] if g < len(fuels) else ""
            cls = _FUEL_TO_CLASS.get(ft, "OTHER")
        if cls == COAL_ARTIFACT_FAMILY:
            # A group-less coal row, or a bundle recorded before COAL-SUB
            # (2026-09-25) whose fleet carried the bare class: resolve the
            # plant's rank; a plant the chain cannot resolve keeps the legacy
            # token, the historical residual bucket (never a wrong rank).
            cls = _coal_supply_class(int(plant_codes[g])) or COAL_ARTIFACT_FAMILY
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


def build_ypay(bundle_dir: Path, year: int, iso: str) -> tuple[dict, dict]:
    """Minimal per-year ``ypay`` for the crossover forecast run + extras.

    Returns ``(ypay, extras)`` where ``ypay`` carries the keys the reused
    scorers read — ``gmModel`` (C1/C5a), ``lmp`` (C3a/C3b), ``co2.model`` (C5a
    full-plant) — and ``extras`` carries reconstruction provenance
    (``physical_co2_mt``, ``has_demand``). Scoreable years only. ``iso``
    steers the coal supply-class split (:func:`build_gmmodel`).
    """
    _assert_scoreable_year(year)
    p = bundle_dir / f"year_{year}.parquet"
    if not p.exists():
        raise SystemExit(f"missing crossover dispatch result: {p}")
    res = from_parquet(DispatchResult, p)
    ctx = read_fleet_context(p)
    demand = read_demand(p)
    gm = build_gmmodel(res, ctx, iso)
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


# FC-4's family-volume rows (rubric §2 FC-4.2, ±5% commercial band) are the
# GAS and COAL families of the C1 per-class taxonomy, summed. Membership and
# exclusions are the calibration scorer's own — never a second list to drift
# (rule 19 [R-ONE-MECH]); ``FUELMIX_EXCLUDED`` drops the same BTM/reconciliation
# buckets C1 itself never gates.
_FAMILY_CLASSES: dict[str, tuple[str, ...]] = {
    "gas_twh": tuple(c for c in V.GAS_CLASSES if c not in V.FUELMIX_EXCLUDED),
    # Coal FAMILY keys: the subclasses plus the legacy bare-COAL row a bundle
    # solved before COAL-SUB (2026-09-25) carries — read, never gated.
    "coal_twh": tuple(c for c in V.COAL_FAMILY_KEYS if c not in V.FUELMIX_EXCLUDED),
}


def _family_volume(
    model_by_class: dict,
    actual_by_class: dict,
    classes: tuple[str, ...],
    iso: str,
    year: int,
) -> dict | None:
    """Fractional family-volume error, summed at FAMILY grain on both sides.

    FC-4 bands ``gas_twh``/``coal_twh`` as FRACTIONS of the family's actual
    volume, which the C1 per-class records carry but do not aggregate — the gap
    FF-2D reported as uncovered and routed here (L-VAL follow-up (b)).

    **Aggregated from the class dicts, NOT from the C1 records, because the two
    sides are not always on the same class GRAIN.** A crossover bundle runs the
    legacy equal-width heat-rate bins (``use_campd_bins=False``), so its whole
    coal fleet reports in one unsplit ``COAL`` bucket, while the bench splits
    coal into ``COAL_PRB``/``COAL_LIGNITE``/``COAL_BIT``/``COAL_WC``. C1 never
    emits a record for either side of that mismatch (the model's ``COAL`` is
    unbenchmarked; the bench's split classes have no model), so aggregating the
    records would report a model coal volume of ZERO — a 100 % error that is a
    scoring artifact, not a dispatch result (ERCOT 2023: 39.2 TWh read as 0.0
    against a 60.4 TWh actual). Summing each side over the whole family
    reconciles the grain, which is exactly what the family row means and the
    documented rule 14 ``[R-ACCURATE]`` case: real data defined on a different
    boundary than our representation, reconciled rather than discarded.

    Completeness is read from the SAME predicate C1 gates on
    (:func:`calibration_verdict.class_is_gated`): a family with any
    preliminary-vintage member is emitted ``gated: False``, named in
    ``incomplete_classes`` and reported as UNCOVERED rather than banded (see
    :func:`rubric_metrics`) — never silently passed.

    Args:
        model_by_class: Model TWh by class (``ypay["gmModel"]``, or the keeper's
            per-class record models).
        actual_by_class: Actual TWh by class (``ybench["classFull"]``, or the
            keeper's per-class record actuals).
        classes: The family's class keys.
        iso: ISO identifier (completeness lookup).
        year: Scored year (completeness lookup).

    Returns:
        The family volume record, or ``None`` when the family has no actual for
        this ISO-year.
    """
    present = [c for c in classes if c in model_by_class or c in actual_by_class]
    if not present:
        return None
    model = sum(float(model_by_class.get(c, 0.0) or 0.0) for c in present)
    actual = sum(float(actual_by_class.get(c, 0.0) or 0.0) for c in present)
    if actual <= 0.0:
        return None
    incomplete = sorted(
        c
        for c in present
        if c in actual_by_class and not V.class_is_gated(iso, c, year)
    )
    signed = (model - actual) / actual
    return {
        "model_twh": round(model, 3),
        "actual_twh": round(actual, 3),
        "err": round(abs(signed), 4),
        "signed": round(signed, 4),
        "unit": "frac (|Δ|/actual family TWh)",
        "classes": sorted(present),
        "model_only_classes": sorted(
            c for c in present if c in model_by_class and c not in actual_by_class
        ),
        "incomplete_classes": incomplete,
        "gated": not incomplete,
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
    # (C7 diurnal shape retired from the rubric by the v3.1 owner amendment
    # 2026-08-06 — no longer a criterion, so nothing to defer.)
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
    family: dict[str, dict] = {fam: {} for fam in _FAMILY_CLASSES}
    extras_by_year: dict[int, dict] = {}
    for year in SCORED_YEARS:
        if not (bundle_dir / f"year_{year}.parquet").exists():
            continue
        ypay, extras = build_ypay(bundle_dir, year, iso)
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

        # FC-4 family-volume rows (gas_twh / coal_twh), aggregated at FAMILY
        # grain on both sides — the forecast from its own gmModel against the
        # bench's classFull, the keeper from its committed per-class records
        # (whose grain is already the bench's). See _family_volume for why the
        # C1 records cannot carry this.
        k_fuelmix = keeper_recs.get("fuelmix", {}).get(year, [])
        k_model = {
            r["key"]: r["model"] for r in k_fuelmix if r.get("model") is not None
        }
        k_actual = {
            r["key"]: r["actual"] for r in k_fuelmix if r.get("actual") is not None
        }
        for fam, classes in _FAMILY_CLASSES.items():
            f_fam = _family_volume(
                ypay["gmModel"], ybench.get("classFull", {}), classes, iso, year
            )
            k_fam = _family_volume(k_model, k_actual, classes, iso, year)
            if f_fam is None and k_fam is None:
                continue
            family[fam][str(year)] = {
                "forecast_err": None if f_fam is None else f_fam["err"],
                "forecast_signed": None if f_fam is None else f_fam["signed"],
                "keeper_backcast_err": None if k_fam is None else k_fam["err"],
                "input_gap": _input_gap(f_fam, k_fam),
                "unit": (f_fam or k_fam or {}).get("unit"),
                "gated": bool(f_fam and f_fam["gated"]),
                "forecast_detail": f_fam,
                "keeper_detail": k_fam,
            }

    return {
        "keeper_run_id": keeper_run_id,
        "keeper_note": keeper_note,
        "metrics": metrics,
        "family_volume": family,
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


# The rubric's pre-registered FC-4 metric names (forecast_verdict.
# CROSSOVER_COMMERCIAL) that this emitter's criteria map onto. ``price_shape``
# (NRMSE) and the aggregate ``fuelmix`` (TWh Σ|Δ|) have no fractional
# counterpart in the rubric and are deliberately absent — reported in the score
# and the report, never re-keyed onto a band they do not mean.
_RUBRIC_METRIC_NAMES = {"price_mean": "price", "co2": "co2"}


def rubric_metrics(dispatch: dict) -> tuple[list[dict], list[str]]:
    """Flatten the dispatch skill onto the rubric's FC-4 ``metrics`` contract.

    Returns ``(metrics, uncovered)`` where ``metrics`` is the flat
    ``[{metric, year, forecast_abs_err_frac, keeper_abs_err_frac}]`` list
    :func:`scripts.forecast_verdict.score_fc4` bands, and ``uncovered`` names
    every rubric row this run cannot score, with the reason.

    Folded in from the FF-2D scoring session's committed adapter
    (``scripts/_ff2d_crossover_adapter.py``, now deleted — rule 26
    ``[R-DELETE]``), which wrote a sibling ``crossover_score.rubric.json``
    because a findings-only session would not edit this core scorer. Two
    changes beyond that re-keying, both routed here as L-VAL follow-ups:

    * the ``refusal_marker`` FC-4 row 1 requires is now emitted by
      :func:`score_crossover` itself, so the quarantine the loaders already
      enforce structurally is also stated in the artifact;
    * the ``gas_twh``/``coal_twh`` family-volume rows FC-4 bands at ±5 % are
      emitted (:func:`_family_volume`). A family with an incomplete-vintage
      member is listed in ``uncovered`` instead of banded — the row is
      reported as not-scored, never silently passed.

    Nothing here changes a threshold, a band or a skill number.
    """
    metrics: list[dict] = []
    uncovered: list[str] = []
    for cid, name in _RUBRIC_METRIC_NAMES.items():
        for year in SCORED_YEARS:
            row = dispatch["metrics"].get(cid, {}).get(str(year))
            if not row or row.get("forecast_err") is None:
                uncovered.append(f"{name} {year}: criterion unscored for this run")
                continue
            k = row.get("keeper_backcast_err")
            metrics.append(
                {
                    "metric": name,
                    "year": year,
                    "forecast_abs_err_frac": abs(float(row["forecast_err"])),
                    "keeper_abs_err_frac": None if k is None else abs(float(k)),
                }
            )
    for fam in _FAMILY_CLASSES:
        for year in SCORED_YEARS:
            row = dispatch.get("family_volume", {}).get(fam, {}).get(str(year))
            if not row or row.get("forecast_err") is None:
                uncovered.append(f"{fam} {year}: family not benchmarked for this ISO")
                continue
            if not row.get("gated"):
                bad = ", ".join(
                    (row.get("forecast_detail") or {}).get("incomplete_classes", [])
                )
                uncovered.append(
                    f"{fam} {year}: preliminary EIA-923 vintage — incomplete "
                    f"class actual(s) [{bad}] would bias the family total; "
                    "reported, not banded"
                )
                continue
            k = row.get("keeper_backcast_err")
            metrics.append(
                {
                    "metric": fam,
                    "year": year,
                    "forecast_abs_err_frac": abs(float(row["forecast_err"])),
                    "keeper_abs_err_frac": None if k is None else abs(float(k)),
                }
            )
    return metrics, uncovered


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
def retirement_decisions_in_window(ledgers: dict, last_scored_year: int) -> dict:
    """Report-only decided-in-window retirement diagnostic (NEISO-RC-R R4).

    The executed-MW retirement score is blind to LAG CENSORING: a decision the
    screen takes inside the scored window whose per-fuel execution lag lands
    the exit past it (coal's 3-year lag can never execute inside a 2023-start
    window) is invisible — the model "decided the right thing" and still
    scores a miss. This block reports the DECISION grain alongside the
    executed grain (the retirement mirror of the signed D-9(ii)
    decision-basis additions), banded by nothing: per fuel, the MW decided at
    a ``decided_year <= last_scored_year``, split into executed-in-window,
    lag-censored (``execute_year > last_scored_year``, still pending at the
    ledger horizon), and reversed-before-execution. Reads the ledgers'
    ``pipeline_events`` (the FFR-5A bar decomposition recorder); a bundle
    whose ledgers carry no pipeline events (pre-recorder, or the legacy
    retirement rule) degrades to an explicit note — absence is recorded,
    never fabricated. Requires the crossover bundle to COMMIT its evolution
    ledgers (the R4 tracked-set change; the capxd14-era bundles committed
    none, which is why this censoring was unobservable there —
    FINDING-capx-neiso-rc-phase0-2026-08-30.md §6 R4).
    """
    decided: dict[str, dict] = {}
    outcomes: dict[str, str] = {}
    any_events = False
    for year in sorted(ledgers):
        led = ledgers[year] or {}
        for e in led.get("pipeline_events", []) or []:
            any_events = True
            ev = e.get("event")
            uid = str(e.get("unit_id"))
            if ev == "decided" and int(e.get("decided_year", year)) <= last_scored_year:
                decided[uid] = {
                    "unit_id": uid,
                    "fuel": e.get("fuel"),
                    "mw": float(e.get("mw") or 0.0),
                    "decided_year": int(e.get("decided_year", year)),
                    "execute_year": (
                        int(e["execute_year"])
                        if e.get("execute_year") is not None
                        else None
                    ),
                }
            elif ev in ("executed", "retired", "reversed") and uid in decided:
                outcomes[uid] = "reversed" if ev == "reversed" else "executed"
    if not any_events:
        return {
            "note": (
                "no pipeline_events in the run's ledgers — either the bundle "
                "commits no evolution ledgers (the pre-R4 crossover tracked "
                "set) or the run predates the FFR-5A recorder / used the "
                "legacy retirement rule; decided-in-window censoring is "
                "unobservable for it (reported as absent, never fabricated)"
            ),
            "per_fuel": None,
        }
    per_fuel: dict[str, dict] = {}
    for uid, d in decided.items():
        f = d["fuel"] or "?"
        row = per_fuel.setdefault(
            f,
            {
                "decided_mw": 0.0,
                "executed_in_window_mw": 0.0,
                "lag_censored_mw": 0.0,
                "reversed_mw": 0.0,
                "n_decided": 0,
            },
        )
        row["decided_mw"] += d["mw"]
        row["n_decided"] += 1
        if outcomes.get(uid) == "reversed":
            row["reversed_mw"] += d["mw"]
        elif d["execute_year"] is not None and d["execute_year"] > last_scored_year:
            row["lag_censored_mw"] += d["mw"]
        else:
            row["executed_in_window_mw"] += d["mw"]
    return {
        "decision": (
            "NEISO-RC-R R4 (2026-08-31) — report-only decision-grain "
            "retirement diagnostic; the retirement mirror of the signed "
            "D-9(ii) decision-basis additions. Nothing bands on it."
        ),
        "last_scored_year": last_scored_year,
        "per_fuel": {
            f: {k: (round(v, 1) if isinstance(v, float) else v) for k, v in row.items()}
            for f, row in sorted(per_fuel.items())
        },
        "lag_censored_units": sorted(
            (
                d
                for uid, d in decided.items()
                if outcomes.get(uid) != "reversed"
                and d["execute_year"] is not None
                and d["execute_year"] > last_scored_year
            ),
            key=lambda d: -d["mw"],
        )[:25],
    }


def score_capacity_events(
    cache_dir: Path, iso: str, bundle: Path | None = None
) -> dict:
    """Part (b): retirements / additions / CO2, 2023-2025, vs registry actuals.

    Reuses :mod:`scripts.score_capacity_hindcast` unchanged. Model ledger events
    are restricted to <= 2025 (a crossover ledger spans 2023-2027) so no forward
    event is scored against nonexistent actuals — and no >= 2026 actual is read.
    Emitted at the TOP LEVEL of ``crossover_score.json`` in the SAME shape the
    hindcast scorer produces (``retirements`` / ``additions`` / ``co2``), so
    ``scripts/register_hindcast.py`` consumes a crossover bundle unchanged.

    **Additions basis (owner decision D-9(ii), 2026-08-04).** Additions are
    attributed to the year the model DECIDED to build, not the COD year, and
    the basis is passed explicitly rather than inherited from the scorer's
    default — a basis-implicit verdict is the record-provenance defect class.
    The ``<= 2025`` window filter composes with it exactly: a pipeline
    commissioning at 2026/2027 drops both its ledger addition and its
    decision-basis reversal (same year, equal and opposite), while its
    ``decided`` row stays inside the window — so no forward event is scored and
    no in-window decision is lost.

    Args:
        cache_dir: The run's cache directory (ledgers + parquets).
        iso: ISO code.
        bundle: The bundle out-dir, for the ``run_config.yaml`` the basis block
            is checked against. ``None`` records the gate as unverifiable.
    """
    ledgers = load_ledgers_for_run(cache_dir)
    try:
        actuals = CH.load_actuals(iso)
    except SystemExit as exc:
        # No committed capacity-actuals target for this ISO (FH-4-CAISO:
        # capacity_actuals_caiso.csv has never been built — data/raw/
        # _validation-source carries ERCOT/MISO/NEISO/NYISO/PJM only). Degrade
        # exactly like the missing-keeper path in score_dispatch_skill: record
        # the absence explicitly and score nothing against a target that does
        # not exist. The co2 block stays scored — its actual comes from the
        # bench, not this file. Downstream readers already tolerate the None
        # blocks (forecast_verdict._collect_hindcast_bands isinstance-guards;
        # write_report and the register_hindcast page branch on the note).
        model_co2 = {str(k): v for k, v in CH.model_co2_by_year(cache_dir).items()}
        actual_co2 = {
            str(k): v for k, v in crossover_actual_co2(iso, SCORED_YEARS).items()
        }
        return {
            "capacity_events_note": (
                f"capacity events not scored — no committed exit/addition "
                f"target exists for {iso} ({exc}); reported as absent, never "
                "fabricated"
            ),
            "retirements": None,
            "additions": None,
            "additions_cod_basis": None,
            "additions_basis": None,
            "co2": {
                "model": model_co2,
                "actual": actual_co2,
                "actual_basis": CH.actual_co2_basis(iso),
            },
        }
    mret = CH.model_retirements(ledgers)
    madd = CH.model_additions(ledgers, basis=CH.ADDITIONS_BASIS_DECISION)
    madd_cod = CH.model_additions(ledgers, basis=CH.ADDITIONS_BASIS_COD)
    # Restrict model events to the scored window (no forward events vs actuals).
    if not mret.empty:
        mret = mret[mret["year"] <= max(SCORED_YEARS)]
    if not madd.empty:
        madd = madd[madd["year"] <= max(SCORED_YEARS)]
    if not madd_cod.empty:
        madd_cod = madd_cod[madd_cod["year"] <= max(SCORED_YEARS)]

    # Gate membership is the REACHABLE set (owner decision D-24) — the same
    # rule as the hindcast scorer, read off the same committed evidence, so one
    # run's recall verdict never depends on which of the two scorers produced
    # it. A crossover bundle with no run_config falls back to the fail-closed
    # pre-D-24 denominator, exactly as the hindcast path does.
    solved = CH.load_solved_scenario_config(bundle)
    reach = CH.classify_exit_reachability(
        iso,
        actuals,
        vintage_cutoff=CH.vintage_cutoff_of(None, solved),
        solved_config=solved,
    )
    ret = CH.score_retirements(mret, actuals, reach)

    # NEISO-RC-R R3(ii) (2026-08-31; FINDING-capx-neiso-rc-phase0 §2.1/§6):
    # the plain-hindcast retirement target is the FULL actuals window
    # (2021-2025), which is coherent for a vintage-2020 hindcast but
    # basis-misaligned for a crossover — a unit that physically ceased at or
    # before the run's fleet-vintage year does not exist in the run's fleet
    # and NO channel can exit it. Reported SIDE BY SIDE per the signed
    # D-9(ii) additions pattern: the default ``retirements`` block above is
    # NOT replaced (no committed verdict re-bases silently); this block scores
    # the SAME model events against the vintage-consistent target (actual
    # retirement rows with physical-cessation year > the vintage year), with
    # reachability re-classified on that target.
    vintage_year = CH.vintage_cutoff_of(None, solved).year
    is_ret = actuals["kind"] == "retirement"
    act_vint = actuals[~is_ret | (actuals["year"] > vintage_year)]
    excluded_ret = actuals[is_ret & (actuals["year"] <= vintage_year)]
    reach_vint = CH.classify_exit_reachability(
        iso,
        act_vint,
        vintage_cutoff=CH.vintage_cutoff_of(None, solved),
        solved_config=solved,
    )
    ret_vint = CH.score_retirements(mret, act_vint, reach_vint)
    ret_basis = {
        "decision": (
            "NEISO-RC-R R3(ii), 2026-08-31 — dual-basis reporting per the "
            "D-9(ii) additions pattern; executing "
            "FINDING-capx-neiso-rc-phase0-2026-08-30.md §6 R3(ii)"
        ),
        "default_basis": (
            "full-window actuals (the plain-hindcast target; kept as the "
            "'retirements' block, unchanged)"
        ),
        "vintage_basis": (
            f"actual retirement rows with physical-cessation year > "
            f"{vintage_year} (the run's EIA-860 fleet-vintage year: an exit at "
            f"or before it pre-dates the fleet snapshot and is unreachable by "
            f"construction)"
        ),
        "vintage_year": vintage_year,
        "excluded_pre_vintage_mw": round(float(excluded_ret["mw"].sum()), 1),
        "excluded_pre_vintage_rows": int(len(excluded_ret)),
    }

    ret_decisions = retirement_decisions_in_window(ledgers, max(SCORED_YEARS))

    add = CH.score_additions(madd, actuals, basis=CH.ADDITIONS_BASIS_DECISION)
    add_cod = CH.score_additions(madd_cod, actuals, basis=CH.ADDITIONS_BASIS_COD)
    add_basis = CH.additions_basis_record(
        ledgers,
        CH.ADDITIONS_BASIS_DECISION,
        CH.load_solved_config(bundle) if bundle is not None else None,
    )
    model_co2 = {
        str(k): v for k, v in CH.model_co2_by_year(cache_dir).items()
    }  # 2023-2025 only, physical basis
    actual_co2 = {str(k): v for k, v in crossover_actual_co2(iso, SCORED_YEARS).items()}
    return {
        "retirements": ret,
        "retirements_vintage_basis": ret_vint,
        "retirement_target_basis": ret_basis,
        "retirement_decisions_in_window": ret_decisions,
        "additions": add,
        "additions_cod_basis": add_cod,
        "additions_basis": add_basis,
        "co2": {
            "model": model_co2,
            "actual": actual_co2,
            "actual_basis": CH.actual_co2_basis(iso),
        },
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
# --rescore-co2-grain — zero-solve FC-4 co2 class-grain repair on a committed
# crossover_score.json (dispatch parquets NOT required; T-R8 --rescore pattern)
# --------------------------------------------------------------------------- #
def bench_coal_intensity(ybench: dict) -> float:
    """The bench's actual-coal-CO2-weighted mean coal intensity (t/MWh).

    ``Σ_r i_r·w_r / Σ_r w_r`` over the bench's coal-rank intensity keys
    (``COAL_*``), with each rank weighted by its actual full-plant CO2
    ``w_r = (classFull_r + btmClass_r) × i_r`` — the same full-plant basis the
    FC-4 co2 metric scores on. 0.0 when the bench carries no coal intensity
    (e.g. NYISO), which a caller must treat as "no coal to value".
    """
    co2b = ybench.get("co2") or {}
    inten = co2b.get("intensity") or {}
    btm = co2b.get("btmClass") or {}
    cf = ybench.get("classFull") or {}
    ranks = [c for c in inten if c.startswith("COAL_")]
    w = {
        c: (float(cf.get(c) or 0.0) + float(btm.get(c) or 0.0)) * float(inten[c])
        for c in ranks
    }
    tot = sum(w.values())
    if tot <= 0.0:
        return 0.0
    return sum(float(inten[c]) * w[c] for c in ranks) / tot


def coal_grain_rescore(bundle: Path, report_dir: Path) -> dict:
    """Repair the FC-4 co2 rows of a committed ``crossover_score.json`` in place.

    The committed crossover bundles carry only their score JSON (the dispatch
    parquets are gitignored by design), so the :func:`build_gmmodel` supply-class
    split cannot re-run on them. This mode applies the SAME grain repair at
    family grain, from committed artifacts alone (FINDING-capx-d5-crossover-co2
    §5.1 option (b) arithmetic, the documented rule 14 ``[R-ACCURATE]``
    boundary-reconcile case — the construction :func:`_family_volume` already
    uses for the volume rows): the model's unsplit ``COAL`` energy (coal-family
    ``model_twh`` minus the split-rank model rows, all committed) is valued at
    :func:`bench_coal_intensity` and added to the scored model CO2
    ``S = egrid × (1 + forecast_signed)`` (the exact identity of the committed
    row). Everything else — family volume rows, C1 records, price metrics,
    keeper columns — is left byte-untouched: the repair touches ONLY the co2
    seam, and an ISO with no coal family (NYISO, the control) is a structural
    no-op. Re-banding reuses :func:`calibration_verdict.score_co2` verbatim.
    No LP is solved and no model input changes (rule 13 ``[R-MEASURED]`` —
    scorer-side only).
    """
    meta = json.loads((bundle / "meta.json").read_text())
    if meta.get("kind") not in ("crossover", "full_forward"):
        raise SystemExit(
            f"{bundle}/meta.json is kind={meta.get('kind')!r} — "
            "--rescore-co2-grain only applies to crossover/full_forward scores."
        )
    iso = meta["iso"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle / iso / meta["cache_key"]
    score_path = cache_dir / "crossover_score.json"
    if not score_path.exists():
        raise SystemExit(f"no committed crossover score to rescore: {score_path}")
    score = json.loads(score_path.read_text())
    ds = score["dispatch_skill"]

    per_year: dict[str, dict] = {}
    for year in SCORED_YEARS:
        row = ds["metrics"].get("co2", {}).get(str(year))
        if not row or row.get("forecast_signed") is None:
            continue
        ybench = load_bench_year(iso, year)
        egrid = (ybench.get("co2") or {}).get("egrid")
        if egrid is None:
            continue
        # Committed model coal energy the broken grain dropped: the family
        # model total minus whatever already sits on split-rank rows (0.0 in
        # every affected bundle; absent entirely for a no-coal ISO).
        fam = ds.get("family_volume", {}).get("coal_twh", {}).get(str(year)) or {}
        det = fam.get("forecast_detail") or {}
        pc = (
            ds["metrics"]
            .get("fuelmix", {})
            .get(str(year), {})
            .get("forecast_per_class", {})
        )
        split_twh = sum(
            float(v.get("model") or 0.0) for k, v in pc.items() if k.startswith("COAL_")
        )
        unsplit_twh = max(0.0, float(det.get("model_twh") or 0.0) - split_twh)
        ibar = bench_coal_intensity(ybench)
        if unsplit_twh > 0.0 and ibar <= 0.0:
            raise SystemExit(
                f"{iso} {year}: {unsplit_twh:.2f} TWh unsplit model COAL but "
                "the bench carries no coal intensity to value it — refusing "
                "to drop it silently."
            )
        old_signed = float(row["forecast_signed"])
        s_before = float(egrid) * (1.0 + old_signed)  # exact committed identity
        s_after = s_before + ibar * unsplit_twh
        rec = V.score_co2(year, {"co2": {"model": round(s_after, 4)}}, ybench)
        new_signed = V._pct(s_after, float(egrid))
        row["forecast_signed"] = round(new_signed, 4)
        row["forecast_err"] = round(abs(new_signed), 4)
        row["forecast_status"] = rec["status"]
        k = row.get("keeper_backcast_err")
        row["input_gap"] = _input_gap(
            {"err": abs(new_signed)}, None if k is None else {"err": k}
        )
        row["basis"] = (
            "full-plant (bench intensities, BTM added back); unsplit model "
            "COAL valued at the bench's actual-coal-CO2-weighted mean coal "
            "intensity (class-grain rescore)"
        )
        for m in score.get("metrics", []):
            if m.get("metric") == "co2" and int(m.get("year", -1)) == year:
                m["forecast_abs_err_frac"] = round(abs(new_signed), 4)
        per_year[str(year)] = {
            "unsplit_coal_twh": round(unsplit_twh, 3),
            "coal_intensity_t_per_mwh": round(ibar, 4),
            "model_co2_mt_before": round(s_before, 4),
            "model_co2_mt_after": round(s_after, 4),
            "signed_before": round(old_signed, 4),
            "signed_after": round(new_signed, 4),
            "status_after": rec["status"],
        }

    # Report-only basis hygiene (FINDING §2.3): label the capacity-track co2
    # block's CAMPD footprint basis so it is never again decomposed against
    # the FC-4 eGRID rows in the same file.
    if isinstance(score.get("co2"), dict):
        score["co2"]["actual_basis"] = CH.actual_co2_basis(iso)

    score["rescore_co2_grain"] = {
        "task": "crossover-co2-grain-repair",
        "note": (
            "FC-4 co2 class-grain repair (FINDING-capx-d5-crossover-co2 "
            "2026-08-30 §5.1): the model's unsplit COAL family energy, "
            "dropped by the bench-intensity-key iteration, valued at the "
            "bench's actual-coal-CO2-weighted mean coal intensity. Zero "
            "solve; committed artifacts only; family volume rows and C1 "
            "records untouched."
        ),
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "per_year": per_year,
    }
    score_path.write_text(json.dumps(score, indent=2))

    # Append the re-score section to the committed report (T-R8 pattern).
    reports = sorted(report_dir.glob(f"{bundle.name}-crossover-*.md"))
    if reports and per_year:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        L = ["", f"## Re-score — FC-4 co2 class-grain repair ({stamp})", ""]
        L.append(
            "Zero-solve rescore of the committed score: the model's unsplit "
            "`COAL` family energy (dropped from the scored CO2 by the "
            "bench-intensity-key iteration) is valued at the bench's "
            "actual-coal-CO2-weighted mean coal intensity. Volume/price rows "
            "untouched. See `rescore_co2_grain` in `crossover_score.json`."
        )
        L.append("")
        L.append(
            "| year | co2 signed before | after | unsplit COAL TWh | ī_coal | status |"
        )
        L.append("|---|--:|--:|--:|--:|:--|")
        for y, d in per_year.items():
            L.append(
                f"| {y} | {d['signed_before']:+.1%} | {d['signed_after']:+.1%} "
                f"| {d['unsplit_coal_twh']} | {d['coal_intensity_t_per_mwh']} "
                f"| {d['status_after']} |"
            )
        rp = reports[-1]
        rp.write_text(rp.read_text().rstrip() + "\n" + "\n".join(L) + "\n")
        print(f"[rescore-co2] report appended: {rp}")

    for y, d in per_year.items():
        print(
            f"[rescore-co2] {iso} {y}: {d['signed_before']:+.1%} -> "
            f"{d['signed_after']:+.1%} (unsplit {d['unsplit_coal_twh']} TWh "
            f"@ {d['coal_intensity_t_per_mwh']} t/MWh) {d['status_after']}"
        )
    if not per_year:
        print(f"[rescore-co2] {iso} {bundle.name}: no scorable co2 rows — no-op")
    print(f"[rescore-co2] score.json: {score_path}")
    return score


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
    # Family-volume rows (FC-4 gas_twh / coal_twh, ±5% commercial band).
    fam_block = score["dispatch_skill"].get("family_volume") or {}
    if any(fam_block.values()):
        L.append("### Family volume (FC-4 `gas_twh` / `coal_twh`)")
        L.append("")
        L.append(
            "| family | year | model TWh | actual TWh | forecast err | "
            "keeper backcast err | input-gap | banded |"
        )
        L.append("|---|--:|--:|--:|--:|--:|--:|:--|")
        for fam, by_year in fam_block.items():
            for year in SCORED_YEARS:
                row = by_year.get(str(year))
                if not row:
                    continue
                det = row.get("forecast_detail") or {}
                ig = (
                    _fmt(row["input_gap"], ".2f")
                    if not isinstance(row["input_gap"], str)
                    else row["input_gap"]
                )
                L.append(
                    f"| `{fam}` | {year} | {det.get('model_twh', '—')} | "
                    f"{det.get('actual_twh', '—')} | "
                    f"{_fmt(row['forecast_err'], '+.1%')} | "
                    f"{_fmt(row['keeper_backcast_err'], '+.1%')} | {ig} | "
                    f"{'yes' if row.get('gated') else 'NO — reported only'} |"
                )
        L.append("")
    if score.get("metrics_uncovered"):
        L.append("**Rubric rows NOT covered by this run** (reported, never a pass):")
        for why in score["metrics_uncovered"]:
            L.append(f"- {why}")
        L.append("")
    L.append("**Deferred metrics** (not reconstructible from a crossover bundle):")
    for k, why in score["dispatch_skill"]["deferred"].items():
        L.append(f"- `{k}` — {why}")
    L.append("")
    # (b) capacity events
    L.append("## (b) Capacity events 2023-2025 vs registry actuals")
    L.append("")
    if score.get("capacity_events_note"):
        # ISO with no committed capacity-actuals target (FH-4-CAISO degrade):
        # the absence is the record — no table is fabricated.
        L.append(f"> {score['capacity_events_note']}")
        L.append("")
    else:
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
            f"{'n/a' if rr.get('n_a') else _fmt(rr['recall'], '.0%')} | {rr['band']} |"
        )
        # NEISO-RC-R R3(ii): the vintage-consistent retirement basis, side by
        # side with the plain full-window row above (never replacing it).
        vb = score.get("retirements_vintage_basis")
        tb = score.get("retirement_target_basis") or {}
        if isinstance(vb, dict) and vb.get("total_gw"):
            vtg = vb["total_gw"]
            L.append(
                f"| thermal GW retired (vintage-consistent target, exits > "
                f"{tb.get('vintage_year', '?')}) | {vtg['actual']} | "
                f"{vtg['model']} | {_fmt(vtg['err_frac'], '+.0%')} | "
                f"{vtg['band']} | "
            )
        L.append(
            f"| total additions | — | {score['additions']['model_total_gw']} GW | "
            f"(actual {score['additions']['actual_total_gw']} GW) | — |"
        )
        L.append("")
        L.extend(
            CH.render_reachability_section(score["retirements"].get("reachability"), rr)
        )
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
    """Score a crossover / full-forward bundle end to end (score.json + report).

    A T1-FF ``full_forward`` bundle (FH-1, hindcast-forward plan §2) rides the
    IDENTICAL scoring path — same benches, same keeper comparison, same
    ``input_gap`` construction, same 2023-2025 two-sided scoring bound; its
    window simply contains no >= 2026 forward years, so the part-(c)
    invariants block is empty.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    if meta.get("kind") not in ("crossover", "full_forward"):
        raise SystemExit(
            f"{bundle}/meta.json is kind={meta.get('kind')!r}, not 'crossover' "
            "or 'full_forward' — use scripts/score_capacity_hindcast.py for a "
            "plain hindcast."
        )
    iso = meta["iso"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle / iso / meta["cache_key"]

    keeper_run_id = _load_keepers().get(iso)

    dispatch = score_dispatch_skill(cache_dir, iso, keeper_run_id)
    capacity = score_capacity_events(cache_dir, iso, bundle)
    forward = forward_invariants(cache_dir, meta)

    run_id = bundle.name
    rubric, uncovered = rubric_metrics(dispatch)
    score = {
        "run_id": run_id,
        "iso": iso,
        "kind": meta.get("kind"),
        "variant": meta.get("variant"),
        # T1-FF provenance (None on a plain crossover): the pre-registered arm
        # + weather posture ride into the score so the three-way read (keeper
        # -> Arm R -> Arm K) never infers an arm from the gas path.
        "arm": meta.get("arm"),
        "base_year": meta.get("base_year"),
        "weather_posture": meta.get("weather_posture"),
        "vintage_year": meta.get("vintage_year"),
        "crossover_forward_year": meta.get("crossover_forward_year"),
        "scored_years": list(SCORED_YEARS),
        "forward_years": forward["years"],
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # FC-4 rubric contract (forecast_verdict --tier t1x reads these two
        # directly; the FF-2D adapter that used to synthesize them is deleted).
        # Row 1 wants the >=2026 refusal marker: SERIALIZED from the same
        # constants _assert_scoreable_year enforces, so the artifact states the
        # quarantine the loaders already make structural.
        "refusal_marker": {
            "read_ge_2026": False,
            "scored_max_year": max(SCORED_YEARS),
            "scored_min_year": min(SCORED_YEARS),
            "quarantine_from": QUARANTINE_FROM,
            "enforced_by": "score_crossover._assert_scoreable_year (every bench "
            "/ actual loader path, before any file is opened)",
        },
        # Row 2 wants a flat metric list on the rubric's own names.
        "metrics": rubric,
        "metrics_uncovered": uncovered,
        # (a)
        "dispatch_skill": dispatch,
        # (b) — TOP LEVEL, hindcast-scorer shape (register_hindcast compatibility)
        "retirements": capacity["retirements"],
        # NEISO-RC-R R3(ii)/R4 additive blocks (absent on the degrade path).
        **{
            k: capacity[k]
            for k in (
                "retirements_vintage_basis",
                "retirement_target_basis",
                "retirement_decisions_in_window",
            )
            if k in capacity
        },
        "additions": capacity["additions"],
        "additions_cod_basis": capacity["additions_cod_basis"],
        "additions_basis": capacity["additions_basis"],
        "co2": capacity["co2"],
        # Present only on the missing-capacity-target degrade (FH-4-CAISO):
        # carried to the top level so write_report / the registered sidecar /
        # the forecast-validation page all read one address.
        **(
            {"capacity_events_note": capacity["capacity_events_note"]}
            if capacity.get("capacity_events_note")
            else {}
        ),
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
    print(
        f"[crossover]   FC-4 rubric rows: {len(rubric)} banded, "
        f"{len(uncovered)} uncovered"
    )
    for why in uncovered:
        print(f"[crossover]     uncovered: {why}")
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
    parser.add_argument(
        "--rescore-co2-grain",
        action="store_true",
        help=(
            "Zero-solve FC-4 co2 class-grain repair on the committed "
            "crossover_score.json (no dispatch parquets needed): value the "
            "model's unsplit COAL family energy at the bench's actual-coal-"
            "CO2-weighted mean intensity and re-band. Appends a re-score "
            "section to the existing report. No LP, no model input change."
        ),
    )
    args = parser.parse_args(argv)
    if args.rescore_co2_grain:
        coal_grain_rescore(args.bundle, args.report_dir)
        return 0
    score_crossover(args.bundle, args.report_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
