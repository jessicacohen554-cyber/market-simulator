#!/usr/bin/env python3
"""nyiso-147 phase 0b — WHAT prices Upstate_West in the control keeper's 2023.

Phase 0a (`_nyiso147_upstate_price_phase0.py`) located the whole C3a-2023 +9.2%
in Upstate_West (+$8.77/MWh lw gap, +30.8% zone-annual; downstate ~right) and
showed the model separates the Central-East seam in only 28.5% of hours at a
mean $3.26 (actual: $9.44 annual mean spread) — AND that even in separated
hours the model's west clears at ~$30.8, far above the actual west annual mean
of $25.32 on a Tenn Z4 200L hub at $1.82/MMBtu (SOM Figure A-6). So the object
is the WEST'S OWN MARGINAL COST, not only the seam. This probe decomposes it.

**No LP is solved.** The fleet/offer arrays are rebuilt EXACTLY as the control
solved them (`replay_keeper.build_kwargs` -> `run_year(fleet_only=True)`, the
nyiso-109/pjm-138 interceptor, verbatim), and the marginal census reads the
control's own committed P1 duals.

Measurements (per year):
  A. Per-zone gas-fleet delivered fuel price (capacity-weighted, annual + by
     month) vs the measured SOM hub table (data/raw/nyiso_zonal_gas_hub.csv).
     Tests the "2023 upstate fuel basis" candidate directly.
  B. Upstate_West marginal census — which (plant_group, tranche) rows set the
     west dual, in ALL hours and in the CE-separated subset — with the
     burn / VOM / residual-markup decomposition of the marginal offer.
  C. The west gas supply ladder: per-row annual-mean offer, MW, heat rate,
     fuel price, sorted by offer — the merit order the west clears on.
  D. Allegany 7784 anatomy (the cohort's taxonomy question): its rows' class,
     tranche multipliers, heat rate, fuel price, offers.
  E. Import rows homed on/near the west: offer level and marginal share
     (nyiso_import_hub_prices prices interchange — if import rungs set the
     west dual, the level lives there, not in the gas stack).

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso147_upstate_offer_anatomy.py \
        --bundle results/calibration/nyiso146_control --years 2023 \
        --out results/calibration/_nyiso147_upstate_offer_anatomy.json
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HOURS = 8760
MODEL_ZONES = (
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
)
TRANCHE_FAMILIES = ("mustrun", "sync", "committed", "econ", "peak")
EPS = 1.0  # pjm-122 / pjm-138 §4.1 marginal-set tolerance, $/MWh


class _FleetCaptured(Exception):
    """Control-flow signal: the fleet arrays are built, unwind before the LP."""


def _keeper_fleet(bundle: Path, year: int) -> dict:
    """Rebuild the EXACT fleet/offer arrays the keeper solved against — no LP.

    Verbatim reuse of `_nyiso109_trough_offer_stack._keeper_fleet` (itself the
    `_pjm138_marginal_ownership` machinery) so the offers censused are the
    offers the control solved on, never a re-derivation that could drift.
    """
    spec = importlib.util.spec_from_file_location(
        "_replay_keeper", REPO / "scripts" / "replay_keeper.py"
    )
    rk = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(rk)

    from scripts import run_calibration
    from scripts import run_calibration_full as rcf

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", HOURS))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = bundle

    captured: dict = {}
    real_run_year = run_calibration.run_year

    def _intercept(*args, **kw):
        kw["fleet_only"] = True
        captured["state"] = real_run_year(*args, **kw)
        raise _FleetCaptured

    run_calibration.run_year = _intercept
    rcf.run_year = _intercept
    try:
        rcf.solve_and_persist(**kwargs)
    except _FleetCaptured:
        pass
    finally:
        run_calibration.run_year = real_run_year
        rcf.run_year = real_run_year

    if "state" not in captured:
        raise SystemExit("fleet reconstruction did not reach run_year")
    return captured["state"]


def _tranche_of(unit_id: str) -> str:
    suffix = str(unit_id).rsplit("_", 1)[-1]
    for family in sorted(TRANCHE_FAMILIES, key=len, reverse=True):
        if suffix.startswith(family):
            return family
    return "_unbinned"


def _model_zonal(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["zone"].isin(MODEL_ZONES)]
    if "pass" in sysf.columns and "P1" in set(sysf["pass"]):
        sysf = sysf[sysf["pass"] == "P1"]
    stamps = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    sysf = sysf.assign(ts=stamps[sysf["hour"].to_numpy()])
    price = sysf.pivot_table(index="ts", columns="zone", values="price", aggfunc="mean")
    dem = sysf.pivot_table(index="ts", columns="zone", values="demand", aggfunc="mean")
    return price[list(MODEL_ZONES)], dem[list(MODEL_ZONES)]


def _hub_table() -> dict[tuple[str, int], float]:
    df = pd.read_csv(REPO / "data" / "raw" / "nyiso_zonal_gas_hub.csv")
    return {
        (str(r.zone), int(r.year)): float(r.hub_usd_mmbtu) for r in df.itertuples()
    }


GAS_FUELS = ("gas", "gas_cc", "gas_ct", "gas_st", "natural_gas")


def _decomp(mc, burn, vom, hr, fuel_px, wgt) -> dict | None:
    tot = float(wgt.sum())
    if tot <= 0:
        return None
    return {
        "cap_weighted_offer": round(float((mc * wgt).sum() / tot), 4),
        "cap_weighted_burn": round(float((burn * wgt).sum() / tot), 4),
        "cap_weighted_vom": round(
            float((np.broadcast_to(vom[:, None], mc.shape) * wgt).sum() / tot), 4
        ),
        "cap_weighted_residual_markup": round(
            float(((mc - burn - vom[:, None]) * wgt).sum() / tot), 4
        ),
        "cap_weighted_heat_rate": round(
            float((np.broadcast_to(hr[:, None], mc.shape) * wgt).sum() / tot), 4
        ),
        "cap_weighted_fuel_price": round(float((fuel_px * wgt).sum() / tot), 4),
    }


def probe_year(bundle: Path, year: int, hubs: dict) -> dict:
    state = _keeper_fleet(bundle, year)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    avail = np.asarray(fa.pmax, dtype=float)[:, None] * np.asarray(
        fa.availability, dtype=float
    )
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], HOURS, axis=1)
    fuel_px = np.asarray(state.get("fuel_prices"), dtype=float)
    if fuel_px.ndim == 1:
        fuel_px = np.repeat(fuel_px[:, None], HOURS, axis=1)
    hr = np.asarray(fa.heat_rate, dtype=float)
    vom = np.asarray(fa.vom, dtype=float)
    burn = hr[:, None] * fuel_px
    zone_idx = np.asarray(fa.zone_idx, dtype=int)
    groups = np.array(
        [str(g) if g else "?" for g in np.asarray(fa.plant_group, dtype=object)],
        dtype=object,
    )
    unit_ids = np.asarray(fa.unit_ids, dtype=object)
    tranches = np.array([_tranche_of(u) for u in unit_ids], dtype=object)
    fuel_names = np.asarray(fa.fuel_types if hasattr(fa, "fuel_types") else [], dtype=object)
    # fuel type per row via fuel_type_idx if the names table exists
    fuel_type_idx = np.asarray(fa.fuel_type_idx, dtype=int)
    if fuel_names.size:
        row_fuel = fuel_names[fuel_type_idx]
    else:
        row_fuel = np.array(["?"] * len(hr), dtype=object)
    is_gas = np.array([str(f).lower().startswith("gas") or "gas" in str(f).lower() for f in row_fuel])

    price, dem = _model_zonal(bundle, year)
    duals = price.to_numpy(float).T  # (n_zones, T) in MODEL_ZONES order
    n_zones = duals.shape[0]
    internal = zone_idx < n_zones

    out: dict = {"n_rows": int(len(hr)), "n_internal": int(internal.sum())}

    # ── A. per-zone gas delivered fuel price vs SOM hub ────────────────────
    per_zone = {}
    for zi, zname in enumerate(MODEL_ZONES):
        rows = internal & (zone_idx == zi) & is_gas
        if not rows.any():
            continue
        w = avail[rows]
        fp = fuel_px[rows]
        cw = float((fp * w).sum() / w.sum()) if w.sum() > 0 else float("nan")
        mon = []
        stamps = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
        for m in range(1, 13):
            k = stamps.month == m
            wm = w[:, k]
            mon.append(round(float((fp[:, k] * wm).sum() / wm.sum()), 3) if wm.sum() > 0 else None)
        per_zone[zname] = {
            "gas_rows": int(rows.sum()),
            "cap_weighted_fuel_price": round(cw, 4),
            "monthly": mon,
            "som_hub_annual": hubs.get((zname, year)),
        }
    out["A_zone_gas_fuel_price"] = per_zone

    # ── B. Upstate_West marginal census ─────────────────────────────────────
    w_dual = duals[0]  # Upstate_West first in MODEL_ZONES
    ch_dual = duals[1]
    sep = (ch_dual - w_dual) > 0.01
    west_rows = internal & (zone_idx == 0)
    row_dual = np.broadcast_to(w_dual[None, :], mc.shape)
    live = west_rows[:, None] & (avail > 0.0)
    marginal = live & (np.abs(mc - row_dual) <= EPS)

    def census(window: np.ndarray) -> dict:
        m = marginal & window[None, :]
        wgt = np.where(m, avail, 0.0)
        by_pair: dict[str, int] = {}
        for g in sorted(set(groups[west_rows])):
            for fam in list(TRANCHE_FAMILIES) + ["_unbinned"]:
                sel = (groups == g) & (tranches == fam)
                n = int(m[sel].sum())
                if n:
                    by_pair[f"{g}:{fam}"] = n
        total = int(m.sum())
        detected = int((m.any(axis=0)).sum())
        return {
            "marginal_unit_hours": total,
            "west_hours_with_west_marginal": detected,
            "window_hours": int(window.sum()),
            "top_pairs": dict(sorted(by_pair.items(), key=lambda kv: -kv[1])[:10]),
            "decomposition": _decomp(mc, burn, vom, hr, fuel_px, wgt),
        }

    out["B_west_marginal_all_hours"] = census(np.ones(HOURS, dtype=bool))
    out["B_west_marginal_separated_hours"] = census(sep)
    out["B_sep_share"] = round(float(sep.mean()), 4)

    # ── C. west gas supply ladder (annual-mean offer per row) ──────────────
    rows = np.nonzero(west_rows)[0]
    ladder = []
    for r in rows:
        aw = avail[r]
        if aw.sum() <= 0:
            continue
        ladder.append(
            {
                "unit_id": str(unit_ids[r]),
                "plant_group": str(groups[r]),
                "tranche": str(tranches[r]),
                "fuel": str(row_fuel[r]),
                "mw_mean": round(float(aw.mean()), 1),
                "heat_rate": round(float(hr[r]), 3),
                "fuel_price_mean": round(float(fuel_px[r].mean()), 3),
                "vom": round(float(vom[r]), 2),
                "offer_mean": round(float(mc[r].mean()), 2),
            }
        )
    ladder.sort(key=lambda d: d["offer_mean"])
    out["C_west_ladder"] = ladder

    # ── D. Allegany 7784 anatomy ────────────────────────────────────────────
    alle = [d for d in ladder if "7784" in d["unit_id"] or "llegany" in d["plant_group"]]
    out["D_allegany_rows"] = alle

    # ── E. external/import rows ────────────────────────────────────────────
    ext_rows = ~internal
    imp = []
    for r in np.nonzero(ext_rows)[0]:
        aw = avail[r]
        if aw.sum() <= 0:
            continue
        imp.append(
            {
                "unit_id": str(unit_ids[r]),
                "plant_group": str(groups[r]),
                "mw_mean": round(float(aw.mean()), 1),
                "offer_mean": round(float(mc[r].mean()), 2),
                "offer_p10": round(float(np.percentile(mc[r], 10)), 2),
                "offer_p90": round(float(np.percentile(mc[r], 90)), 2),
            }
        )
    imp.sort(key=lambda d: d["offer_mean"])
    out["E_external_rows"] = imp[:40]

    del state, fa, mc, avail, fuel_px, burn
    gc.collect()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default="results/calibration/nyiso146_control")
    ap.add_argument("--years", nargs="+", type=int, default=[2023])
    ap.add_argument(
        "--out", default="results/calibration/_nyiso147_upstate_offer_anatomy.json"
    )
    args = ap.parse_args()
    bundle = REPO / args.bundle if not Path(args.bundle).is_absolute() else Path(args.bundle)
    hubs = _hub_table()
    out = {"bundle": str(args.bundle), "eps": EPS, "years": {}}
    for year in args.years:
        print(f"== {year} ==", flush=True)
        out["years"][str(year)] = probe_year(bundle, year, hubs)
        dst = REPO / args.out
        dst.write_text(json.dumps(out, indent=1))
        print(f"wrote {dst}", flush=True)


if __name__ == "__main__":
    main()
