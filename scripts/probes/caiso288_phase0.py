#!/usr/bin/env python3
"""caiso-288 phase 0 — WHERE the CAISO 2022 C3a miss lives, and what the
citygate coverage repair is worth. ZERO LP.

Every number in ``docs/PRECOMMIT-caiso288-citygate-catchup-tables-2026-09-20.md``
§0, §3 and §4 is produced here, from committed artifacts only:

* the keeper's own hourly sidecars (``caiso287_instr_2022/hourly/``) — price,
  demand and ``marginal_emission_rate`` per zone-hour;
* the committed hourly actual (``data/raw/_validation-source/
  actual_lmp_hourly_CAISO.parquet``) and the committed bench annual ``rt_lw``;
* the PRODUCTION delivered-gas loader (``fuel.hubs._caiso_hub_daily_gas_prices``
  under the keeper's own flags), run against the repaired citygate CSV and
  against the pre-repair copy the caller supplies.

Usage:
    python scripts/probes/caiso288_phase0.py --prerepair /tmp/citygate_prerepair.csv

``--prerepair`` is the control series, recovered with
``git show <sha>:data/raw/gas-prices/caiso_citygate_daily.csv``. Omit it to run
the decomposition legs only.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import CAISO_CITYGATE_TRANSPORT_ADDER  # noqa: E402
from market_sim.data.fuel.hubs import _caiso_hub_daily_gas_prices  # noqa: E402

BUNDLE = REPO / "results/calibration/caiso287_instr_2022/hourly"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
BENCH = REPO / "frontend/data/backcast/bench/CAISO/2022.json.gz"
OUT = REPO / "results/calibration/_caiso288_phase0.json"

#: CAISO CC_REGULAR cap-weighted base heat rate, MMBtu/MWh — the model's own
#: fleet basis (derive_caiso_offer_surface._fleet_geometry; the 7.44 cited in
#: backcast_config._CAISO_OFFER_CURVE's grounding comment). Used ONLY to convert
#: a measured $/MMBtu gas delta into a $/MWh marginal-cost delta for the
#: pre-registered band; nothing is fitted with it.
CC_HR = 7.44

#: A non-zero marginal emission rate means a carbon-emitting (gas) unit set the
#: price in that zone-hour. The committed ``marginal_emission_rate`` sidecar is
#: caiso-287's append; 0.02 tCO2/MWh is far below any gas class's rate and far
#: above float noise, so the split is insensitive to the cut.
FOSSIL_MER = 0.02

_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class _Cfg:
    """The keeper's own gas-path flags, read from its committed run_config."""

    iso = "CAISO"
    hours = 8760
    caiso_citygate_spot_level = True
    caiso_citygate_spot_coverage = True
    caiso_citygate_flow_date = True
    gas_hub_basis_overlay = True
    gas_hub_basis_daily = False


def delivered_gas(year: int, citygate_path: str | None) -> np.ndarray:
    """Delivered CAISO citygate $/MMBtu, hourly, through the production loader."""
    cfg = _Cfg()
    cfg.hours = 8784 if year % 4 == 0 else 8760
    series = _caiso_hub_daily_gas_prices(
        cfg, year, None, None, citygate_path, spot_level=True, spot_coverage=True
    )
    if series is None:
        raise RuntimeError(f"no delivered-gas series for {year}")
    return series + CAISO_CITYGATE_TRANSPORT_ADDER


def load_keeper_2022() -> dict[str, np.ndarray]:
    """System price, demand and marginal emission rate, load-weighted hourly.

    G-ZONE: the load-weighting set is the zones that CARRY load. The two WECC
    import nodes have zero demand, so they carry zero weight — reproduced here
    rather than assumed, because a ``fleet_only`` rebuild's ``config.zones`` is
    ``None`` and a consumer that falls through to ``sorted(unique)`` reads every
    price from the wrong zone (the caiso-286 §4 defect).
    """
    sys_df = pd.read_parquet(BUNDLE / "system_2022.parquet")
    price = sys_df.pivot_table(index="hour", columns="zone", values="price")
    demand = sys_df.pivot_table(index="hour", columns="zone", values="demand")
    mer = sys_df.pivot_table(index="hour", columns="zone", values="marginal_emission_rate")
    load_zones = [z for z in demand.columns if demand[z].sum() > 0]
    p, d = price[load_zones].to_numpy(), demand[load_zones].to_numpy()
    return {
        "price": (p * d).sum(1) / d.sum(1),
        "demand": d.sum(1),
        "mer": (mer[load_zones].to_numpy() * d).sum(1) / d.sum(1),
        "zones": load_zones,
    }


def month_index(hours: int) -> np.ndarray:
    edges = np.cumsum([0] + [24 * n for n in _DAYS])
    return np.clip(np.searchsorted(edges, np.arange(hours), side="right") - 1, 0, 11)


def _wshare(err, dem, mask, total_gap):
    return float((err[mask] * dem[mask]).sum() / dem.sum() / total_gap * 100)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prerepair", default=None,
                    help="the CONTROL citygate CSV (git show <sha>:<path>)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    k = load_keeper_2022()
    mp, dem, mer = k["price"], k["demand"], k["mer"]
    act = pd.read_parquet(ACTUAL)
    act = act[act.year == 2022].set_index("hour")
    rt = act["rt"].reindex(range(8760)).to_numpy(float)
    da = act["da"].reindex(range(8760)).to_numpy(float)
    bench = json.load(gzip.open(BENCH))["bench"]["avgLMP"]

    model = float(np.average(mp, weights=dem))
    err = mp - rt
    gap = float(np.average(err, weights=dem))
    doc: dict = {
        "run": "caiso-288 phase 0",
        "keeper": "2026-09-19-caiso-287-mer-keeper",
        "bundle_2022": "caiso287_instr_2022",
        "load_zones": k["zones"],
        "c3a_2022": {
            "model": round(model, 4),
            "bench_rt_lw": bench["rt_lw"],
            "bench_da_lw": bench["da_lw"],
            "pct_vs_rt": round(100 * (model - bench["rt_lw"]) / bench["rt_lw"], 3),
            "pct_vs_da": round(100 * (model - bench["da_lw"]) / bench["da_lw"], 3),
            "gap_model_weighted": round(gap, 4),
        },
    }

    # --- WHERE: net-load decile (the belly question) ---
    cls = pd.read_parquet(BUNDLE / "class_hourly_2022.parquet")

    def klass(name):
        return (cls[cls.klass == name].set_index("hour")["mw"]
                .reindex(range(8760)).fillna(0).to_numpy())

    netload = dem - klass("wind") - klass("solar")
    dec = pd.qcut(netload, 10, labels=False)
    doc["gap_share_by_netload_decile"] = {
        f"d{i}": round(_wshare(err, dem, dec == i, gap), 3) for i in range(10)
    }
    doc["gap_share_belly_d0"] = doc["gap_share_by_netload_decile"]["d0"]
    doc["gap_share_shoulder_d1_d4"] = round(
        _wshare(err, dem, (dec >= 1) & (dec <= 4), gap), 3)

    # --- WHERE: month, and December's nine days ---
    mo = month_index(8760)
    doc["gap_share_by_month"] = {
        f"m{m + 1:02d}": round(_wshare(err, dem, mo == m, gap), 3) for m in range(12)
    }
    dec23 = np.zeros(8760, bool)
    dec23[8760 - 9 * 24:] = True
    doc["gap_share_dec23_31"] = round(_wshare(err, dem, dec23, gap), 3)
    jan_nov = mo != 11
    doc["c3a_2022_jan_nov_only_pct"] = round(
        100 * (np.average(mp[jan_nov], weights=dem[jan_nov])
               - np.average(rt[jan_nov], weights=dem[jan_nov]))
        / np.average(rt[jan_nov], weights=dem[jan_nov]), 3)
    doc["fossil_marginal_share_december"] = round(
        100 * float((mer[mo == 11] >= FOSSIL_MER).mean()), 3)

    # --- THE REPAIR: footprint and the pre-registered band ---
    if args.prerepair:
        foot = {}
        for year in (2022, 2023, 2024, 2025):
            ctrl = delivered_gas(year, args.prerepair)
            arm = delivered_gas(year, None)
            d = arm - ctrl
            moved = ~np.isclose(d, 0.0, atol=1e-9) & ~np.isnan(d)
            foot[str(year)] = {
                "hours_moved": int(moved.sum()),
                "ctrl_mean": round(float(np.nanmean(ctrl)), 4),
                "arm_mean": round(float(np.nanmean(arm)), 4),
                "mean_delta": round(float(np.nanmean(d)), 4),
                "max_pos": round(float(np.nanmax(d)), 4),
                "max_neg": round(float(np.nanmin(d)), 4),
            }
        doc["gas_footprint"] = foot

        d22 = delivered_gas(2022, None) - delivered_gas(2022, args.prerepair)
        dmc = d22 * CC_HR
        fossil = mer >= FOSSIL_MER
        upper = float(np.average(mp + np.where(fossil, dmc, 0.0), weights=dem))
        doc["band"] = {
            "cc_heat_rate_mmbtu_per_mwh": CC_HR,
            "lower_model": round(model, 4),
            "lower_c3a_pct": round(100 * (model - bench["rt_lw"]) / bench["rt_lw"], 3),
            "upper_model": round(upper, 4),
            "upper_c3a_pct": round(100 * (upper - bench["rt_lw"]) / bench["rt_lw"], 3),
            "width_usd_per_mwh": round(upper - model, 4),
        }
        for label, mask in (("gas_down", d22 < -1e-9), ("gas_up", d22 > 1e-9)):
            doc["band"][label] = {
                "hours": int(mask.sum()),
                "pct_of_load": round(100 * float(dem[mask].sum() / dem.sum()), 3),
                "mean_dgas_usd_mmbtu": round(float(d22[mask].mean()), 3),
                "mean_dmc_usd_mwh": round(float(dmc[mask].mean()), 3),
                "fossil_marginal_pct": round(100 * float(fossil[mask].mean()), 2),
                "observed_model_minus_rt": round(
                    float(np.average(err[mask], weights=dem[mask])), 3),
            }

    args.out.write_text(json.dumps(doc, indent=1) + "\n")
    print(json.dumps(doc, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
