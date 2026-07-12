"""caiso-78 STEP-0: decompose what holds CC online through the evening ramp.

The caiso-77 keeper cleared C1-2024 by making the contracted import base
must-flow, but CT_PEAKER stayed byte-flat (-2.0/-2.5/-0.8 TWh same-fleet)
and C1-2023 CC_REGULAR is still +4.50 TWh over. The session task's STEP-0
question: WHICH mechanism keeps model CC online through the evening ramp
(summer h17-20, winter mornings h5-7) while reality serves those hours with
CT starts — RA-bridge floors? min-down/commitment physics? offer-band
ordering vs CT?

This is a DIAGNOSTIC probe (rule 15): no solve, no derivation, no writes.
Model side = the committed caiso-77 keeper run payload (the scorers' own
decode path, byte-consistent with the committed gates). Actual side =
CAMPD CA unit-level gross load RESTRICTED to the bench plant set (same
fleet both sides — the 2026-07-11 contamination correction).

Stage 1 (default, payload + CAMPD only):
  A. window ledger  — CC_REGULAR / CT_PEAKER model vs actual mean GW in the
     summer-evening, winter-morning and overnight windows;
  B. cycling stats  — starts/yr, median run length, share of plant-days
     with an overnight off, model vs actual (the LP-never-cycles check);
  C. phantom CC     — model CC MW in ramp-window hours from plants whose
     ACTUAL output that hour is offline (< 5% npl): the "serves the ramp
     with CC that reality had off" quantity;
  D. swap hours     — hours where actual CT exceeds model CT by >200 MW:
     count, window concentration, and the CC counter-delta in those hours.

Stage 2 (``--fleet``, per year; fleet-only rebuild, LP never built):
  E. offer bands    — capacity-weighted mc_base (the assembled P0 objective,
     G-22 convention: the SAME prices the LP solved on) for CC_REGULAR vs
     CT_PEAKER in the ramp windows;
  F. ordering/headroom — per ramp-window hour: the model's marginal CC
     offer at its payload dispatch, the cheapest CT offer, and the GW of
     idle CC capacity priced BELOW the cheapest CT ("CC headroom under
     CT"): if that headroom covers the CT deficit in ~all hours, the
     under-run is pure offer-band ordering, no floor involved;
  G. markup arithmetic — the P0-run-length startup amortization CC actually
     carries in the keeper (startup / model run length ~ 0 when CC never
     stops) vs the counterfactual amortization over the plant's MEASURED
     CAMPD run length: does re-ordering CC vs CT become possible at real
     cycling horizons? (ex-ante magnitude check, the caiso-70/71 method —
     decide with arithmetic before burning a solve).

Usage:
    python scripts/probes/_caiso78_step0_ramp_mechanism.py
    python scripts/probes/_caiso78_step0_ramp_mechanism.py --fleet --years 2023
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import scripts.legitimacy_diagnostics as L  # noqa: E402
from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP  # noqa: E402
from market_sim.data.fleet import eia923_dominant_class_by_plant  # noqa: E402
from market_sim.model.commitment import find_runs  # noqa: E402

HOURS = 8760
RUN_ID = "2026-07-12-caiso-77-firm-selfschedule"
BUNDLE = REPO / "results" / "calibration" / "caiso77_firm_selfschedule"
CLASSES = ("CC_REGULAR", "CT_PEAKER")

# Ramp windows from the caiso-77 FINDING §2 locus: the CT under-run sits in
# the summer evening ramp and the winter morning shoulder. Overnight is the
# CC-flatness (C1 residual) window. hod windows are half-open [lo, hi).
SUMMER_MONTHS = frozenset({6, 7, 8, 9})
WINTER_MONTHS = frozenset({11, 12, 1, 2})
W_EVENING = (17, 21)
W_MORNING = (5, 8)
W_OVERNIGHT = (0, 6)

_MONTH_START_HOUR = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]
_HOUR_MONTH = np.zeros(HOURS, dtype=int)
for _m in range(12):
    _end = _MONTH_START_HOUR[_m + 1] if _m < 11 else HOURS
    _HOUR_MONTH[_MONTH_START_HOUR[_m] : _end] = _m + 1
_HOUR_HOD = np.arange(HOURS) % 24


def _window_mask(months: frozenset[int] | None, hod: tuple[int, int]) -> np.ndarray:
    """Boolean (8760,) mask for a month-set x hour-of-day window."""
    m = (
        np.ones(HOURS, dtype=bool)
        if months is None
        else np.isin(_HOUR_MONTH, list(months))
    )
    return m & (_HOUR_HOD >= hod[0]) & (_HOUR_HOD < hod[1])


def _hoy(date: pd.Series, hour: pd.Series) -> np.ndarray:
    """Map (date, 0-based hour) to non-leap hour-of-year (Feb 29 -> -1)."""
    m = date.dt.month.to_numpy(dtype=int)
    d = date.dt.day.to_numpy(dtype=int)
    h = np.asarray(hour, dtype=int)
    base = np.array(_MONTH_START_HOUR)[m - 1]
    return np.where((m == 2) & (d == 29), -1, base + (d - 1) * 24 + h)


def actual_by_plant(year: int, bench: dict[str, dict]) -> dict[str, np.ndarray]:
    """Measured per-plant hourly MW for the bench-restricted CC/CT fleet.

    Same construction as ``caiso_belly_commitment_probe.actual_cc_mw`` (the
    corrected, bench-restricted basis) but returning per-plant series for
    both target classes instead of a fleet sum.
    """
    dom = eia923_dominant_class_by_plant(year)
    bench_ids = {int(pid) for pid in bench if str(pid).isdigit()}
    path = REPO / "data" / "raw" / "campd-unit-level" / f"CA_{year}.parquet"
    raw = pd.read_parquet(
        path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
    ).dropna(subset=["grossLoad"])
    raw["fac"] = pd.to_numeric(raw["facilityId"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["fac"])
    raw["eff"] = [
        CAMPD_UNIT_PLANT_REMAP.get((int(f), str(u)), int(f))
        for f, u in zip(raw["fac"], raw["unitId"])
    ]
    raw["klass"] = [dom.get(pc) for pc in raw["eff"]]
    raw = raw[raw["klass"].isin(CLASSES) & raw["eff"].isin(bench_ids)]
    hoy = _hoy(pd.to_datetime(raw["date"]), raw["hour"].astype(int))
    ok = (hoy >= 0) & (hoy < HOURS)
    raw = raw[ok].copy()
    raw["hoy"] = hoy[ok]
    out: dict[str, np.ndarray] = {}
    for pid, grp in raw.groupby("eff"):
        out[str(pid)] = (
            grp.groupby("hoy")["grossLoad"]
            .sum()
            .reindex(range(HOURS), fill_value=0.0)
            .to_numpy()
        )
    return out


def model_by_plant(year: int, bench: dict[str, dict]) -> dict[str, np.ndarray]:
    """Model per-plant hourly MW from the keeper payload, target classes only."""
    sidecar = {"file": f"frontend/data/backcast/runs/{RUN_ID}.js"}
    plants = L.load_payload_plants(REPO, sidecar, year, bench)
    return {
        pid: arr[:HOURS]
        for pid, arr in plants.items()
        if bench.get(pid, {}).get("group") in CLASSES
    }


def _class_sum(series: dict[str, np.ndarray], bench: dict, klass: str) -> np.ndarray:
    """Fleet-sum hourly MW over the plants of one class."""
    tot = np.zeros(HOURS)
    for pid, arr in series.items():
        if bench.get(pid, {}).get("group") == klass:
            tot[: len(arr)] += arr[:HOURS]
    return tot


def _cycling_stats(
    series: dict[str, np.ndarray], bench: dict, klass: str
) -> tuple[float, float, float]:
    """(starts/yr fleet total, cap-wtd median run h, share plant-days w/ overnight off).

    Online threshold = max(5% npl, 1 MW) — the markup convention
    (``compute_monthly_markup``: dispatch > 5% pmax counts as running).
    """
    starts_total = 0.0
    med_runs: list[tuple[float, float]] = []  # (median run, weight=npl)
    off_days = 0
    plant_days = 0
    overnight = _window_mask(None, W_OVERNIGHT).reshape(365, 24)[
        :, W_OVERNIGHT[0] : W_OVERNIGHT[1]
    ]
    for pid, arr in series.items():
        if bench.get(pid, {}).get("group") != klass:
            continue
        npl = bench[pid]["npl"]
        thr = max(0.05 * npl, 1.0)
        on = arr[:HOURS] >= thr
        if not on.any():
            continue
        runs = find_runs(on)
        starts_total += len(runs)
        med_runs.append((float(np.median([e - s for s, e in runs])), npl))
        daily = on.reshape(365, 24)
        ran_day = daily.any(axis=1)
        overnight_off = ~daily[:, W_OVERNIGHT[0] : W_OVERNIGHT[1]].any(axis=1)
        # a "cycling day": the plant ran that day but was dark overnight
        off_days += int((ran_day & overnight_off).sum())
        plant_days += int(ran_day.sum())
    if not med_runs:
        return 0.0, 0.0, 0.0
    runs_arr = np.array([r for r, _ in med_runs])
    w = np.array([w for _, w in med_runs])
    order = np.argsort(runs_arr)
    cum = np.cumsum(w[order])
    med = float(runs_arr[order][np.searchsorted(cum, 0.5 * cum[-1])])
    return starts_total, med, (off_days / plant_days if plant_days else 0.0)


def stage1(years: list[int]) -> dict[int, dict]:
    """Payload+CAMPD decomposition (A-D). Returns per-year context for stage 2."""
    ctx: dict[int, dict] = {}
    win_defs = {
        "sum-eve h17-20": _window_mask(SUMMER_MONTHS, W_EVENING),
        "win-morn h5-7": _window_mask(WINTER_MONTHS, W_MORNING),
        "overnight h0-5": _window_mask(None, W_OVERNIGHT),
    }
    for year in years:
        bench = L.load_bench(REPO, "CAISO", year)
        model = model_by_plant(year, bench)
        actual = actual_by_plant(year, bench)
        ctx[year] = {"bench": bench, "model": model, "actual": actual}

        print(f"\n=== {year} — A. window ledger (mean GW, model / actual / a-m) ===")
        for wname, mask in win_defs.items():
            row = []
            for klass in CLASSES:
                m = _class_sum(model, bench, klass)[mask].mean() / 1e3
                a = _class_sum(actual, bench, klass)[mask].mean() / 1e3
                row.append(f"{klass}: {m:5.2f}/{a:5.2f}/{a - m:+5.2f}")
            print(f"  {wname:14s} | " + " | ".join(row))

        print(
            f"=== {year} — B. cycling (starts/yr, cap-wtd median run h, overnight-off day share) ==="
        )
        for klass in CLASSES:
            for side, series in (("model", model), ("actual", actual)):
                st, med, offsh = _cycling_stats(series, bench, klass)
                print(
                    f"  {klass:10s} {side:6s}: starts {st:6.0f}  med-run {med:6.1f} h  overnight-off {offsh:5.1%}"
                )

        print(f"=== {year} — C. phantom-committed CC in ramp windows ===")
        for wname, mask in list(win_defs.items())[:2]:
            phantom = 0.0
            total = 0.0
            for pid, arr in model.items():
                if bench.get(pid, {}).get("group") != "CC_REGULAR":
                    continue
                thr = max(0.05 * bench[pid]["npl"], 1.0)
                act = actual.get(pid)
                off = np.ones(HOURS, dtype=bool) if act is None else act < thr
                phantom += arr[mask & off].sum()
                total += arr[mask].sum()
            nh = mask.sum()
            print(
                f"  {wname:14s}: model CC from actually-OFF plants "
                f"{phantom / nh / 1e3:5.2f} GW mean ({phantom / max(total, 1):5.1%} of model window CC)"
            )

        mct = _class_sum(model, bench, "CT_PEAKER")
        act_ct = _class_sum(actual, bench, "CT_PEAKER")
        mcc = _class_sum(model, bench, "CC_REGULAR")
        acc = _class_sum(actual, bench, "CC_REGULAR")
        swap = (act_ct - mct) > 200.0
        print(
            f"=== {year} — D. CT-swap hours (actual CT - model CT > 200 MW): {int(swap.sum())} h ==="
        )
        if swap.any():
            for wname, mask in win_defs.items():
                share = (swap & mask).sum() / swap.sum()
                print(f"  in {wname:14s}: {share:5.1%} of swap hours")
            print(
                f"  mean deltas in swap hours: CT {(act_ct - mct)[swap].mean():+6.0f} MW under, "
                f"CC {(mcc - acc)[swap].mean():+6.0f} MW over (model-actual)"
            )
        ctx[year]["swap"] = swap
    return ctx


# ---------------------------------------------------------------------------
# Stage 2 — fleet-only rebuild (no LP): offer bands, ordering, markup math
# ---------------------------------------------------------------------------

_META_RENAME = {
    "commitment": "commitment_enabled",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}


def _fleet_state(year: int) -> dict:
    """run_year(fleet_only=True) with the caiso-77 bundle's own meta flags.

    Same reconstruction as ``legitimacy_diagnostics.load_or_rebuild_floors``
    but with the sigmoid-override key renames applied (meta stores
    ``coal_prb_sigmoid_overrides``; the run_year param is ``prb_overrides`` —
    the generic scenario-override channel every caiso-7x structural flag
    rides in on, so dropping it would rebuild a DIFFERENT recipe).
    """
    import inspect

    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {}
    for k, v in meta.items():
        k2 = _META_RENAME.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
    gas_prices = meta["gas_prices"]
    gas_price = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
    return run_year(
        year,
        "CAISO",
        int(meta.get("hours", HOURS)),
        gas_price,
        {},
        fleet_only=True,
        **kwargs,
    )


def stage2(year: int, ctx: dict) -> None:
    """Offer bands (E), ordering/headroom (F), markup arithmetic (G)."""
    from market_sim.model.commitment import _startup_cost

    state = _fleet_state(year)
    fa = state["fleet_arrays"]
    fleet = state["fleet"]
    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    groups = np.array(
        [
            str(g)
            for g in (fa.plant_group if fa.plant_group is not None else [""] * fa.n_gen)
        ]
    )
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], HOURS, axis=1)
    pmax = np.asarray(fa.pmax, dtype=float)
    cc = groups == "CC_REGULAR"
    ct = groups == "CT_PEAKER"
    bench, model = ctx["bench"], ctx["model"]
    print(f"\n=== {year} — E. offer bands (cap-wtd $/MWh, annual) ===")
    for name, m_ in (("CC_REGULAR", cc), ("CT_PEAKER", ct)):
        w = (pmax[m_, None] * avail[m_]).ravel()
        v = mc[m_].ravel()
        qs = _wquant(v, w, (0.1, 0.5, 0.9))
        print(
            f"  {name:10s}: n_units {m_.sum():3d}  cap {pmax[m_].sum() / 1e3:5.1f} GW  "
            f"mc p10/p50/p90 = {qs[0]:6.2f}/{qs[1]:6.2f}/{qs[2]:6.2f}"
        )

    for wname, months, hod in (
        ("sum-eve", SUMMER_MONTHS, W_EVENING),
        ("win-morn", WINTER_MONTHS, W_MORNING),
    ):
        mask = _window_mask(months, hod)
        hrs = np.flatnonzero(mask)
        mcc_payload = _class_sum(model, bench, "CC_REGULAR")
        act_ct = _class_sum(ctx["actual"], bench, "CT_PEAKER")
        mct_payload = _class_sum(model, bench, "CT_PEAKER")
        marg_cc, cheap_ct, head_under_ct, deficit = [], [], [], []
        for t in hrs:
            cap_t = pmax * avail[:, t]
            # model's marginal CC offer: walk the CC supply curve to the
            # payload's dispatched CC quantity
            ci = np.flatnonzero(cc & (cap_t > 0))
            order = ci[np.argsort(mc[ci, t])]
            cum = np.cumsum(cap_t[order])
            q = mcc_payload[t]
            j = int(np.searchsorted(cum, min(q, cum[-1] if cum.size else 0.0)))
            j = min(j, len(order) - 1)
            m_marg = mc[order[j], t] if order.size else np.nan
            ti = np.flatnonzero(ct & (cap_t > 0))
            c_ct = mc[ti, t].min() if ti.size else np.nan
            # idle CC capacity priced below the cheapest CT
            below = order[mc[order, t] < c_ct] if ti.size else order
            head = max(cap_t[below].sum() - q, 0.0)
            marg_cc.append(m_marg)
            cheap_ct.append(c_ct)
            head_under_ct.append(head)
            deficit.append(max(act_ct[t] - mct_payload[t], 0.0))
        marg_cc, cheap_ct = np.array(marg_cc), np.array(cheap_ct)
        head_under_ct, deficit = np.array(head_under_ct), np.array(deficit)
        covered = (head_under_ct >= deficit) | (deficit <= 0)
        print(f"=== {year} — F. ordering/headroom, {wname} ({len(hrs)} h) ===")
        print(
            f"  marginal CC offer p50 {np.nanmedian(marg_cc):6.2f}  cheapest CT p50 {np.nanmedian(cheap_ct):6.2f}  "
            f"CT cheaper than marginal CC in {np.nanmean((cheap_ct < marg_cc).astype(float)):5.1%} of h"
        )
        print(
            f"  idle CC priced under cheapest CT: p50 {np.median(head_under_ct) / 1e3:5.2f} GW; "
            f"covers the hour's CT deficit in {covered.mean():5.1%} of h"
        )

    # G. startup amortization arithmetic (CC_REGULAR)
    print(
        f"=== {year} — G. CC startup amortization: model-run vs measured-run ($/MWh, cap-wtd) ==="
    )
    hr_arr = np.asarray(fa.heat_rate, dtype=float)
    actual = ctx["actual"]
    cur, cf, wts = [], [], []
    for g in np.flatnonzero(cc):
        gen = fleet[g]
        su = _startup_cost(gen, float(hr_arr[g]))
        if su <= 0:
            continue
        pid = str(int(fa.plant_code[g])) if fa.plant_code[g] > 0 else None
        marr = model.get(pid)
        aarr = actual.get(pid)
        thr = max(0.05 * pmax[g], 1.0)
        m_runs = find_runs((marr if marr is not None else np.zeros(1)) >= thr)
        a_runs = find_runs((aarr if aarr is not None else np.zeros(1)) >= thr)
        m_med = float(np.median([e - s for s, e in m_runs])) if m_runs else 0.0
        a_med = float(np.median([e - s for s, e in a_runs])) if a_runs else 0.0
        if a_med <= 0:
            continue
        cur.append(su / max(m_med, 1.0))
        cf.append(su / max(a_med, 1.0))
        wts.append(pmax[g])
    cur, cf, wts = np.array(cur), np.array(cf), np.array(wts)
    if cur.size:
        print(
            f"  current  (model P0 runs): p50 {_wquant(cur, wts, (0.5,))[0]:6.2f}  "
            f"p90 {_wquant(cur, wts, (0.9,))[0]:6.2f}"
        )
        print(
            f"  measured (CAMPD runs)   : p50 {_wquant(cf, wts, (0.5,))[0]:6.2f}  "
            f"p90 {_wquant(cf, wts, (0.9,))[0]:6.2f}"
        )
        gap = mc[ct].mean() - mc[cc].mean() if ct.any() else np.nan
        print(
            f"  mean CT-CC base-mc gap: {gap:6.2f} $/MWh — measured-run amortization "
            f"re-orders CC vs CT for the share of CC capacity whose counterfactual "
            f"markup exceeds the gap: {float(wts[cf > gap].sum() / wts.sum()):5.1%}"
        )


def _wquant(v: np.ndarray, w: np.ndarray, qs: tuple[float, ...]) -> list[float]:
    """Weighted quantiles (simple cumulative-weight rule)."""
    v, w = np.asarray(v, float).ravel(), np.asarray(w, float).ravel()
    ok = np.isfinite(v) & (w > 0)
    v, w = v[ok], w[ok]
    if v.size == 0:
        return [float("nan")] * len(qs)
    order = np.argsort(v)
    cum = np.cumsum(w[order])
    return [float(v[order][np.searchsorted(cum, q * cum[-1])]) for q in qs]


def main() -> None:
    """CLI entry: stage 1 always; stage 2 per requested year with --fleet."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--fleet", action="store_true", help="run stage 2 (fleet-only rebuild; no LP)"
    )
    args = ap.parse_args()
    print(f"caiso-78 STEP-0 ramp-mechanism decomposition — model = {RUN_ID}")
    ctx = stage1(args.years)
    if args.fleet:
        for year in args.years:
            stage2(year, ctx[year])


if __name__ == "__main__":
    main()
