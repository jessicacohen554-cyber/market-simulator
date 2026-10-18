"""Zero-LP effect table of the SPP EIA-930 stale-snapshot repair (R22 / R23).

Lane UC-SPP-DATAFIX. For each SPP zone-year 2019-2025: masked hours, energy
and peak of the solve demand (``load_demand``), mean net interchange in the
masked hours, and wind / solar delivered energy
(``load_eia_hourly_renewable_gen``), BEFORE (repair spec unregistered) and
AFTER (registered). "Before" is checked against the keeper bundle's own
hourly demand (``results/calibration/closeout_spp_nuc_span/hourly``) when that
bundle is on disk. Prints a markdown table and writes JSON to ``--out``.

Run: ``uv run python -m scripts.probes.spp_stale_snapshot_effect --out <json>``
(needs the clean ``iso-area-load`` / ``counterparty-interchange`` /
``iso-genmix`` SPP partitions).
"""

from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.data import stale_snapshot as ss
from market_sim.data.eia930 import load_demand
from market_sim.data.eia930.actuals import load_eia_hourly_renewable_gen
from market_sim.data.eia930.envelopes import spp_net_interchange

YEARS = tuple(range(2019, 2026))
KEEPER_HOURLY = Path("results/calibration/closeout_spp_nuc_span/hourly")


GAPS: dict[tuple[int, str], int] = {}
PROVENANCE: list[pd.DataFrame] = []


def _require_or_record(values, mask, what, iso, year):
    """Probe-only: record a masked hour with no replacement instead of raising.

    The production repair RAISES (``stale_snapshot._require``); the table
    leaves such hours at their EIA-930 value and reports the count.
    """
    bad = mask & ~np.isfinite(values)
    if bad.any():
        GAPS[(year, what)] = int(bad.sum())


@contextmanager
def _repair(enabled: bool):
    """Temporarily (un)register the SPP stale-snapshot spec."""
    saved = dict(ss.STALE_SNAPSHOT_SPECS)
    if not enabled:
        ss.STALE_SNAPSHOT_SPECS.pop("SPP", None)
    ss.reset_caches()
    real_require = ss._require
    ss._require = _require_or_record
    try:
        yield
    finally:
        ss._require = real_require
        ss.STALE_SNAPSHOT_SPECS.clear()
        ss.STALE_SNAPSHOT_SPECS.update(saved)
        ss.reset_caches()


def _inputs(year: int, enabled: bool) -> dict:
    """Demand / interchange / renewables for one year with the repair on or off."""
    cfg = get_iso_config("SPP")
    with _repair(enabled):
        return {
            "demand": load_demand("SPP", year, cfg),
            "ti": spp_net_interchange(year),
            "gen": load_eia_hourly_renewable_gen("SPP", year),
        }


#: FINDING-spp-south-demand-flatruns-2026-10-18 §4 ΔGWh (Fix A with 3(a):
#: load leg from HOURLY_LOAD, interchange linearly interpolated across the run).
FINDING_S4_DELTA_GWH: dict[tuple[int, str], int] = {
    (2019, "SPP-North"): 278,
    (2019, "SPP-South"): 520,
    (2020, "SPP-North"): 45,
    (2020, "SPP-South"): 59,
    (2021, "SPP-North"): 440,
    (2021, "SPP-South"): 269,
    (2022, "SPP-North"): 2,
    (2022, "SPP-South"): 3,
    (2023, "SPP-North"): 9,
    (2023, "SPP-South"): 11,
    (2024, "SPP-North"): 158,
    (2024, "SPP-South"): 77,
    (2025, "SPP-North"): -176,
    (2025, "SPP-South"): -319,
}


def _load_leg_only(year: int, mask: np.ndarray) -> np.ndarray:
    """Zonal demand with the repaired load leg and the FINDING's 3(a) interchange.

    Reproduces FINDING §4's construction: weights and system load repaired,
    ``Total interchange`` linearly interpolated across each masked run from
    the bracketing unmasked hours (the FINDING's labelled estimate, used here
    only to check the load leg; the production repair uses measured legs).
    """
    from market_sim.data.eia930.demand import _load_spp_hourly_demand, load_zone_weights

    cfg = get_iso_config("SPP")
    with _repair(False):
        ti = spp_net_interchange(year)
    ti_interp = pd.Series(np.where(mask, np.nan, ti)).interpolate().bfill().ffill()
    with _repair(True):
        weights = load_zone_weights("SPP", year, cfg)
        system = _load_spp_hourly_demand(year)
    return weights * (system + ti_interp.to_numpy())[None, :]


def effect(year: int) -> dict:
    """One year's before/after rows."""
    cfg = get_iso_config("SPP")
    before, after = _inputs(year, False), _inputs(year, True)
    mask = ss.demand_stale_mask("SPP", year)
    out: dict = {"year": year, "masked_h": int(mask.sum()), "zones": {}}
    keeper = KEEPER_HOURLY / f"system_{year}.parquet"
    kd = None
    if keeper.exists():
        k = pd.read_parquet(keeper, columns=["pass", "zone", "hour", "demand"])
        kd = k[k["pass"] == "P1"].pivot(index="hour", columns="zone", values="demand")
    load_leg = _load_leg_only(year, mask)
    for i, zone in enumerate(cfg.zone_names):
        b, a = before["demand"][i], after["demand"][i]
        row = {
            "energy_twh": [b.sum() / 1e6, a.sum() / 1e6],
            "delta_gwh": (a.sum() - b.sum()) / 1e3,
            "peak_mw": [float(b.max()), float(a.max())],
            "masked_mean_abs_delta_mw": float(np.abs(a - b)[mask].mean())
            if mask.any()
            else 0.0,
            "masked_max_abs_delta_mw": float(np.abs(a - b)[mask].max())
            if mask.any()
            else 0.0,
        }
        row["load_leg_delta_gwh"] = (load_leg[i].sum() - b.sum()) / 1e3
        row["finding_s4_delta_gwh"] = FINDING_S4_DELTA_GWH.get((year, zone))
        if kd is not None:
            row["before_vs_keeper_max_abs_mw"] = float(
                np.abs(kd[zone].to_numpy() - b).max()
            )
        out["zones"][zone] = row
    out["interchange_masked_mean_mw"] = [
        float(before["ti"][mask].mean()) if mask.any() else 0.0,
        float(after["ti"][mask].mean()) if mask.any() else 0.0,
    ]
    prov = ss.stale_snapshot_provenance("SPP", year)
    omitted = prov["interchange_legs_omitted"].str.split(";").explode()
    out["interchange_residual_h"] = {
        k: int(v) for k, v in omitted[omitted != ""].value_counts().items()
    }
    out["interchange_stale_kept_h"] = int(
        (prov["interchange_source"] == "eia_stale_kept").sum()
    )
    out["wind_stale_kept_h"] = int((prov["wind_source"] == "eia_stale_kept").sum())
    out["solar_stale_kept_h"] = int((prov["solar_source"] == "eia_stale_kept").sum())
    PROVENANCE.append(prov.assign(year=year))
    for fuel, col in (("wind", "NG: WND"), ("solar", "NG: SUN")):
        fm = ss.fuel_stale_mask("SPP", year, col)
        b, a = before["gen"][fuel], after["gen"][fuel]
        out[fuel] = {
            "masked_h": int(fm.sum()),
            "energy_twh": [b.sum() / 1e6, a.sum() / 1e6],
            "delta_gwh": (a.sum() - b.sum()) / 1e3,
        }
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--provenance",
        type=Path,
        default=None,
        help="write the per-hour provenance CSV",
    )
    args = ap.parse_args()
    rows = [effect(y) for y in YEARS]
    args.out.write_text(json.dumps(rows, indent=1, default=float))
    if args.provenance is not None:
        args.provenance.parent.mkdir(parents=True, exist_ok=True)
        cols = ["year", *PROVENANCE[0].columns.drop("year")]
        pd.concat(PROVENANCE, ignore_index=True)[cols].to_csv(
            args.provenance, index=False
        )
    print(
        "| Year | Zone | Masked h | Energy TWh before → after | ΔGWh | Peak MW before → after | Mean / max abs Δ in masked h (MW) |"
    )
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        for z, v in r["zones"].items():
            print(
                f"| {r['year']} | {z.replace('SPP-', '')} | {r['masked_h']} | "
                f"{v['energy_twh'][0]:.1f} → {v['energy_twh'][1]:.1f} | {v['delta_gwh']:+.0f} | "
                f"{v['peak_mw'][0]:,.0f} → {v['peak_mw'][1]:,.0f} | "
                f"{v['masked_mean_abs_delta_mw']:,.0f} / {v['masked_max_abs_delta_mw']:,.0f} |"
            )
    print("\n| Year | Zone | Load-leg ΔGWh (FINDING §4 method) | FINDING §4 ΔGWh |")
    print("|---|---|---|---|")
    for r in rows:
        for z, v in r["zones"].items():
            print(
                f"| {r['year']} | {z.replace('SPP-', '')} | {v['load_leg_delta_gwh']:+.0f} | {v['finding_s4_delta_gwh']:+d} |"
            )
    print(
        "\n| Year | Interchange mean in masked h, MW before → after | Residual legs (h) | Wind masked h | Wind TWh before → after (ΔGWh) | Solar masked h | Solar TWh before → after (ΔGWh) |"
    )
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        w, s = r["wind"], r["solar"]
        print(
            f"| {r['year']} | {r['interchange_masked_mean_mw'][0]:+,.0f} → {r['interchange_masked_mean_mw'][1]:+,.0f} | "
            f"{r['interchange_residual_h'] or '—'}{' + stale TI kept ' + str(r['interchange_stale_kept_h']) + ' h' if r['interchange_stale_kept_h'] else ''} | {w['masked_h']}{' (' + str(r['wind_stale_kept_h']) + ' kept stale)' if r['wind_stale_kept_h'] else ''} | {w['energy_twh'][0]:.2f} → {w['energy_twh'][1]:.2f} ({w['delta_gwh']:+.0f}) | "
            f"{s['masked_h']}{' (' + str(r['solar_stale_kept_h']) + ' kept stale)' if r['solar_stale_kept_h'] else ''} | {s['energy_twh'][0]:.2f} → {s['energy_twh'][1]:.2f} ({s['delta_gwh']:+.0f}) |"
        )
    keeper_gap = max(
        v.get("before_vs_keeper_max_abs_mw", 0.0)
        for r in rows
        for v in r["zones"].values()
    )
    print(f"\nmasked hours left unrepaired (no measured replacement): {GAPS or 'none'}")
    print(
        f"\nmax |before − keeper bundle demand| over all zone-hours: {keeper_gap:.6f} MW"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
