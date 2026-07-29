"""Characterise the NYISO CT start-frequency defect BEFORE any lever is built.

The C3c lane's remaining candidates are all offer/commitment-side, and queue
item 2 (``docs/mechanism-testing-matrix.md`` §5.5) names the CT fleet's start
frequency as its head. The defect statement inherited from nyiso-89 is that the
model starts the CT fleet 2-5x LESS often than measured, and that 50-68 % of
measured CT energy clears BELOW its own SRMC.

Those two facts admit TWO INCOMPATIBLE lever families, and the charter requires
picking between them on evidence rather than by assumption:

* a **start-economics** story — the fleet's start costs are mispriced, so the
  marginal decision to start is wrong. Its instrument is
  ``tranche_startup_amortization`` (+ the v3 measured-run basis). Its
  signature is below-SRMC energy CONCENTRATED in a few short, high-value
  blocks: a unit recovers its start over a handful of hours and is willing to
  sit under SRMC in the rest of the block it already committed to.
* a **commitment/obligation** story — the fleet is online for a non-energy
  reason (DA block award, local reliability, AS carry), so no offer-side price
  can reach it. Its signature is below-SRMC energy SPREAD FLAT across many
  hours, and missing starts landing in hours the model ALREADY prices above
  the class SRMC (i.e. the model could have started on economics and did not).

This probe measures the discriminating statistics directly:

1. per-year plant-grain START COUNTS and RUN-LENGTH distributions, measured
   (CAMPD bench) vs model (the keeper's committed ``unit_hourly`` sidecars),
   over the SAME plant set so the counts are comparable;
2. WHERE the missing starts sit — month and hour-of-day;
3. the SRMC-vs-clearing-price distribution of measured CT energy, reported as a
   CONCENTRATION curve (what share of below-SRMC energy lives in the deepest
   1/5/10/25 % of its hours) against the flat-reference the same fleet's total
   energy traces;
4. the decisive test — in the hours carrying missing starts, does the model
   price ABOVE the plant's own SRMC (an economics defect: the model declined a
   start it could afford) or BELOW it (a commitment defect: no offer-side
   change can reach it)?

Everything is read from committed artifacts (rule 13/15): the keeper's own
hourly sidecars, the committed CAMPD bench, the committed measured CT heat-rate
table, the scored LMP parquet, and the keeper's OWN downstate-CT delivered-gas
seam — so the SRMC a plant is judged against is the cost the LP charges it. No
LP is solved and no measured outcome enters any model input; this is
scoring-side characterisation only.

CLOCK: the bench series, the LMP parquet and the model sidecars all share the
model's non-leap 8760 local-standard clock, so they are index-aligned with no
remap (the convention documented in ``nyiso88_peaker_economics``).

Usage::

    python scripts/probes/nyiso96_ct_start_characterization.py \
        --bundle results/calibration/nyiso92_hydro_envfloor \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402

from scripts.legitimacy_diagnostics import load_bench  # noqa: E402
from scripts.probes.nyiso88_peaker_economics import (  # noqa: E402
    downstate_ct_gas_hourly,
)

#: Committed NYISO hub DA/RT hourly price (the C-criteria scoring series).
LMP_PATH = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"

#: Classes this lane owns. CT_CHP is carried alongside CT_PEAKER because the
#: charter asks for both, and because a cogen's start decision is confounded by
#: its steam host — a difference that is itself evidence.
CT_CLASSES = ("CT_PEAKER", "CT_CHP")

#: Online threshold for a plant-grain start. Relative so a 32-unit barge plant
#: and a single-turbine site are treated alike; floored at 1 MW so LP dust and
#: CEMS rounding cannot manufacture a start.
ONLINE_FRAC = 0.01
ONLINE_FLOOR_MW = 1.0


def _online(mw: np.ndarray, cap: float) -> np.ndarray:
    """Return the boolean online mask for a plant's hourly MW series."""
    thresh = max(ONLINE_FLOOR_MW, ONLINE_FRAC * float(cap))
    return np.asarray(mw, dtype=float) > thresh


def _starts(online: np.ndarray) -> np.ndarray:
    """Return indices of off->on transitions (hour 0 counts as a start if on)."""
    prev = np.concatenate([[False], online[:-1]])
    return np.flatnonzero(online & ~prev)


def _run_lengths(online: np.ndarray) -> list[int]:
    """Return the list of consecutive-online block lengths."""
    if not online.any():
        return []
    idx = np.flatnonzero(online)
    splits = np.flatnonzero(np.diff(idx) > 1)
    blocks = np.split(idx, splits + 1)
    return [int(len(b)) for b in blocks]


def measured_loaded_heat_rate_table(iso: str) -> dict[int, float]:
    """Return {plant_code: measured loaded NET heat rate} from the committed table.

    This is the very artifact the keeper prices CT_PEAKER with
    (``measured_ct_heat_rates=True``, nyiso-89), so an SRMC built on it is the
    LP's own cost rather than a new estimate.
    """
    path = PROCESSED_DIR / f"campd_ct_heat_rates_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    # ``heat_rate`` is the NET-basis column the model applies (``heat_rate_gross``
    # is the raw CEMS ratio before the parasitic conversion), and only
    # ``flag == 'ok'`` rows are applied — mirror both so this SRMC is the LP's.
    df = df[df["flag"] == "ok"]
    return {int(r["plant_code"]): float(r["heat_rate"]) for _, r in df.iterrows()
            if np.isfinite(r["heat_rate"])}


def model_fleet_view(year: int) -> tuple[dict[int, str], dict[int, float], float]:
    """Return ({plant: class}, {plant: model heat rate}, class median VOM)."""
    gens = load_fleet_from_csv("NYISO", get_iso_config("NYISO"), year=year)
    groups: dict[int, set[str]] = collections.defaultdict(set)
    hr_num: dict[int, float] = collections.defaultdict(float)
    hr_den: dict[int, float] = collections.defaultdict(float)
    voms: list[float] = []
    for g in gens:
        code = int(getattr(g, "plant_code", 0) or 0)
        group = getattr(g, "plant_group", "") or ""
        if not code or not group:
            continue
        groups[code].add(group)
        if group in CT_CLASSES:
            pmax = float(getattr(g, "pmax_mw", 0.0) or 0.0)
            hr_num[code] += pmax * float(getattr(g, "heat_rate", 0.0) or 0.0)
            hr_den[code] += pmax
            voms.append(float(getattr(g, "vom", 0.0) or 0.0))
    # A plant is attributed to a CT class only when EVERY model unit there is
    # that class — a mixed steam/CT facility's plant-grain start is not a CT
    # start, and attributing it would contaminate the count.
    pure = {c: next(iter(s)) for c, s in groups.items()
            if len(s) == 1 and next(iter(s)) in CT_CLASSES}
    hr = {c: hr_num[c] / hr_den[c] for c in pure if hr_den[c] > 0}
    return pure, hr, float(np.median(voms)) if voms else 5.0


def model_plant_hourly(bundle: Path, year: int) -> tuple[dict[int, np.ndarray],
                                                         dict[int, str],
                                                         dict[int, float]]:
    """Return per-plant model MW, zone and capacity from the keeper sidecar."""
    path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
    df = pd.read_parquet(path)
    df = df[df["plant_group"].isin(CT_CLASSES)]
    df["plant_code"] = df["plant_code"].astype(int)
    mw: dict[int, np.ndarray] = {}
    zone: dict[int, str] = {}
    cap: dict[int, float] = {}
    for code, g in df.groupby("plant_code"):
        series = g.groupby("hour")["mw"].sum()
        arr = np.zeros(8760)
        arr[series.index.to_numpy()] = series.to_numpy()
        mw[int(code)] = arr
        zone[int(code)] = str(g["zone"].iloc[0])
        cap[int(code)] = float(g.groupby("unit_id")["cap_mw"].first().sum())
    return mw, zone, cap


def model_zone_price(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Return the keeper's own hourly LP price per zone."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    out: dict[str, np.ndarray] = {}
    for z, g in df.groupby("zone", observed=True):
        s = g.groupby("hour")["price"].mean()
        arr = np.zeros(8760)
        arr[s.index.to_numpy()] = s.to_numpy()
        out[str(z)] = arr
    return out


def concentration(weight: np.ndarray, depth: np.ndarray) -> dict[str, float]:
    """Return the share of *weight* carried by the deepest quantiles of *depth*.

    ``weight`` is MWh per hour and ``depth`` the per-hour severity used to rank
    (here: how far below SRMC the hour clears). A start-amortization story
    concentrates its below-SRMC energy in few hours; a standing commitment
    obligation spreads it flat. Reporting the curve rather than one number lets
    the reader see WHICH it is instead of taking a verdict on trust.
    """
    live = weight > 0
    if not live.any():
        return {}
    w, d = weight[live], depth[live]
    order = np.argsort(-d)
    w_sorted = w[order]
    cum = np.cumsum(w_sorted) / w_sorted.sum()
    n = len(w_sorted)
    out = {}
    for q in (0.01, 0.05, 0.10, 0.25, 0.50):
        k = max(1, int(round(q * n)))
        out[f"top{int(q * 100)}pct_share"] = round(float(cum[k - 1]), 4)
    out["n_hours"] = int(n)
    return out


def analyse(bundle: Path, year: int) -> dict:
    """Return the full characterisation for one year."""
    pure, model_hr, vom = model_fleet_view(year)
    meas_hr = measured_loaded_heat_rate_table("NYISO")
    bench = load_bench(REPO, "NYISO", year)
    m_mw, m_zone, m_cap = model_plant_hourly(bundle, year)
    prices = model_zone_price(bundle, year)
    gas_by_zone = downstate_ct_gas_hourly(year) or {}

    lmp = pd.read_parquet(LMP_PATH)
    lmp = lmp[lmp["year"] == year].sort_values("hour")
    rt = lmp["rt"].to_numpy(dtype=float)[:8760]

    # ---- assemble the comparable plant set -----------------------------
    # Bench keys are bare "<code>" or "<code>:<KLASS>" slices; a CT plant that
    # is pure in the model fleet has a single slice, so aggregating by code is
    # exact for this population.
    bench_mw: dict[int, np.ndarray] = collections.defaultdict(lambda: np.zeros(8760))
    bench_cap: dict[int, float] = collections.defaultdict(float)
    bench_group: dict[int, str] = {}
    for pid, rec in bench.items():
        code = int(str(pid).split(":")[0])
        if rec["group"] not in CT_CLASSES:
            continue
        bench_mw[code] += np.asarray(rec["mw"], dtype=float)[:8760]
        bench_cap[code] += float(rec["npl"] or 0.0)
        bench_group[code] = rec["group"]

    per_class: dict[str, dict] = {}
    rows: list[dict] = []
    for klass in CT_CLASSES:
        codes = sorted(c for c, k in pure.items()
                       if k == klass and c in bench_mw and c in m_mw)
        if not codes:
            continue
        agg = {
            "plants": len(codes),
            "measured_starts": 0, "model_starts": 0,
            "measured_online_h": 0, "model_online_h": 0,
            "measured_twh": 0.0, "model_twh": 0.0,
            "measured_runs": [], "model_runs": [],
        }
        # month x hour-of-day start maps
        meas_map = np.zeros((12, 24))
        mod_map = np.zeros((12, 24))
        # decisive-test accumulators
        above_srmc = below_srmc = 0
        hod = np.arange(8760) % 24
        month = ((np.arange(8760) // 24) // 30.4375).astype(int).clip(0, 11)

        for code in codes:
            cap = max(bench_cap[code], m_cap.get(code, 0.0))
            b_on = _online(bench_mw[code], cap)
            m_on = _online(m_mw[code], cap)
            b_st, m_st = _starts(b_on), _starts(m_on)
            agg["measured_starts"] += len(b_st)
            agg["model_starts"] += len(m_st)
            agg["measured_online_h"] += int(b_on.sum())
            agg["model_online_h"] += int(m_on.sum())
            agg["measured_twh"] += float(bench_mw[code].sum()) / 1e6
            agg["model_twh"] += float(m_mw[code].sum()) / 1e6
            agg["measured_runs"] += _run_lengths(b_on)
            agg["model_runs"] += _run_lengths(m_on)
            for i in b_st:
                meas_map[month[i], hod[i]] += 1
            for i in m_st:
                mod_map[month[i], hod[i]] += 1

            # ---- decisive test: missing starts vs the model's own price ----
            hr = meas_hr.get(code, model_hr.get(code, np.nan))
            if not np.isfinite(hr):
                continue
            gas = gas_by_zone.get(m_zone.get(code, ""))
            if gas is None and gas_by_zone:
                gas = np.mean(list(gas_by_zone.values()), axis=0)
            if gas is None:
                continue
            srmc = gas * hr + vom
            price = prices.get(m_zone.get(code, ""))
            if price is None:
                continue
            missing = b_on & ~m_on
            above_srmc += int((missing & (price >= srmc)).sum())
            below_srmc += int((missing & (price < srmc)).sum())

            rows.append({
                "plant": code, "class": klass, "zone": m_zone.get(code),
                "cap_mw": round(cap, 1),
                "meas_starts": len(b_st), "model_starts": len(m_st),
                "meas_gwh": round(float(bench_mw[code].sum()) / 1e3, 1),
                "model_gwh": round(float(m_mw[code].sum()) / 1e3, 1),
                "meas_median_run": (float(np.median(_run_lengths(b_on)))
                                    if _run_lengths(b_on) else 0.0),
                "model_median_run": (float(np.median(_run_lengths(m_on)))
                                     if _run_lengths(m_on) else 0.0),
            })

        def _dist(runs: list[int]) -> dict:
            if not runs:
                return {"n": 0}
            a = np.asarray(runs, dtype=float)
            return {"n": int(a.size), "median": float(np.median(a)),
                    "mean": round(float(a.mean()), 2),
                    "p90": float(np.percentile(a, 90)),
                    "max": float(a.max())}

        per_class[klass] = {
            "plants": agg["plants"],
            "starts": {"measured": agg["measured_starts"],
                       "model": agg["model_starts"],
                       "ratio": round(agg["measured_starts"]
                                      / max(1, agg["model_starts"]), 2)},
            "online_hours": {"measured": agg["measured_online_h"],
                             "model": agg["model_online_h"]},
            "energy_twh": {"measured": round(agg["measured_twh"], 3),
                           "model": round(agg["model_twh"], 3)},
            "run_length": {"measured": _dist(agg["measured_runs"]),
                           "model": _dist(agg["model_runs"])},
            "missing_start_hours_vs_model_price": {
                "model_price_ABOVE_srmc": above_srmc,
                "model_price_BELOW_srmc": below_srmc,
                "share_above": round(above_srmc / max(1, above_srmc + below_srmc), 4),
            },
            "starts_by_hod": {
                "measured": meas_map.sum(axis=0).round(1).tolist(),
                "model": mod_map.sum(axis=0).round(1).tolist(),
            },
            "starts_by_month": {
                "measured": meas_map.sum(axis=1).round(1).tolist(),
                "model": mod_map.sum(axis=1).round(1).tolist(),
            },
        }

    # ---- measured SRMC-vs-price distribution & concentration ------------
    # Fleet-level, CT_PEAKER only (the class the lane owns), on the plants that
    # carry a measured heat rate so the SRMC is measured end-to-end.
    codes = sorted(c for c, k in pure.items()
                   if k == "CT_PEAKER" and c in bench_mw and c in meas_hr)
    fleet_mw = np.zeros(8760)
    fleet_cost = np.zeros(8760)
    for code in codes:
        gas = gas_by_zone.get(m_zone.get(code, ""))
        if gas is None and gas_by_zone:
            gas = np.mean(list(gas_by_zone.values()), axis=0)
        if gas is None:
            continue
        fleet_mw += bench_mw[code]
        fleet_cost += bench_mw[code] * (gas * meas_hr[code] + vom)
    srmc = np.divide(fleet_cost, fleet_mw, out=np.zeros(8760), where=fleet_mw > 0)
    live = fleet_mw > 0
    margin = np.where(live, rt - srmc, 0.0)
    below = live & (margin < 0)
    below_energy = np.where(below, fleet_mw, 0.0)

    econ = {
        "plants_scored": len(codes),
        "measured_twh": round(float(fleet_mw.sum()) / 1e6, 3),
        "hours_online": int(live.sum()),
        "hours_below_srmc": int(below.sum()),
        "energy_share_below_srmc": round(
            float(below_energy.sum() / max(1e-9, fleet_mw.sum())), 4),
        "mean_margin_usd_mwh": round(
            float(np.average(margin[live], weights=fleet_mw[live])), 2) if live.any() else None,
        # Concentration of the BELOW-SRMC energy across its own hours, ranked by
        # depth. Compare with the flat reference below.
        "below_srmc_concentration": concentration(below_energy, -margin),
        # Flat reference: the same fleet's TOTAL energy ranked by the same depth
        # measure. If the two curves are close, the below-SRMC energy is not
        # specially concentrated — it is just what the fleet does.
        "total_energy_concentration_same_rank": concentration(
            np.where(live, fleet_mw, 0.0), -margin),
    }

    return {"year": year, "per_class": per_class, "measured_economics": econ,
            "plant_rows": sorted(rows, key=lambda r: -r["meas_gwh"])[:25]}


def main(argv: list[str] | None = None) -> int:
    """Print (and optionally dump) the characterisation for each year."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path,
                   default=REPO / "results/calibration/nyiso92_hydro_envfloor")
    p.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    p.add_argument("--json-out", type=Path)
    args = p.parse_args(argv)

    out = {"bundle": str(args.bundle), "years": {}}
    for year in args.years:
        res = analyse(args.bundle, year)
        out["years"][str(year)] = res
        print(f"\n{'=' * 72}\n{year}\n{'=' * 72}")
        for klass, d in res["per_class"].items():
            s, r = d["starts"], d["run_length"]
            print(f"\n[{klass}]  plants={d['plants']}")
            print(f"  starts      measured {s['measured']:6d}   "
                  f"model {s['model']:6d}   ratio {s['ratio']}x")
            print(f"  online h    measured {d['online_hours']['measured']:6d}   "
                  f"model {d['online_hours']['model']:6d}")
            print(f"  energy TWh  measured {d['energy_twh']['measured']:6.3f}   "
                  f"model {d['energy_twh']['model']:6.3f}")
            print(f"  run len     measured med={r['measured'].get('median')} "
                  f"mean={r['measured'].get('mean')} p90={r['measured'].get('p90')}"
                  f"   |   model med={r['model'].get('median')} "
                  f"mean={r['model'].get('mean')} p90={r['model'].get('p90')}")
            m = d["missing_start_hours_vs_model_price"]
            print(f"  MISSING-START HOURS: model price ABOVE srmc "
                  f"{m['model_price_ABOVE_srmc']:6d}  BELOW {m['model_price_BELOW_srmc']:6d}"
                  f"   share_above={m['share_above']}")
        e = res["measured_economics"]
        print(f"\n[measured CT_PEAKER economics]  plants={e['plants_scored']} "
              f"twh={e['measured_twh']}")
        print(f"  online h {e['hours_online']}  below-SRMC h {e['hours_below_srmc']}"
              f"  energy share below SRMC {e['energy_share_below_srmc']}")
        print(f"  mean margin {e['mean_margin_usd_mwh']} $/MWh")
        print(f"  below-SRMC energy concentration : {e['below_srmc_concentration']}")
        print(f"  total-energy same-rank reference: {e['total_energy_concentration_same_rank']}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
