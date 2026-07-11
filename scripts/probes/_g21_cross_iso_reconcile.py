"""Cross-ISO: gas/coal family on CAMPD (CEMS) vs 923-grid vs EIA-930, to see what
switching the reconcile target from 930 to CAMPD/923 would do per ISO."""

import sys
import json
import gzip

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, ".")
import pandas as pd
import run_calibration_full as rcf
from market_sim.data.eia923 import load_monthly_generation
from market_sim.config.iso_configs import get_iso_config

gen = load_monthly_generation()
factors = rcf._parasitic_factor_map()
gas_cls = [
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "OTHER_FOSSIL",
]
coal_cls = ["COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE", "COAL"]


def group_map(iso, cfg, yr):
    if iso == "ERCOT":
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import load_campd_bins

        b = load_campd_bins(ScenarioConfig().campd_bins_path)
        return dict(zip(b["Plant_Code"].astype(int), b["Plant_Group"]))
    return rcf._fleet_group_by_code(iso, cfg, yr)


ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
print(
    f"{'ISO':<7}{'yr':<6}{'gas923g':>8}{'gas930':>8}{'g923-930':>9} | {'coalCEMS':>9}{'coal923':>8}{'coal930':>8}{'c930-CEMS':>10}"
)
for iso in ISOS:
    try:
        cfg = get_iso_config(iso)
        pjm_ids = rcf._iso_plant_ids(iso)
        for yr in (2023, 2024, 2025):
            e923 = rcf._benchmark_eia923_frame(yr, gen, iso, None, {}, None)
            gbc = group_map(iso, cfg, yr)
            btmf = rcf._btm_frame(
                yr,
                "P1",
                gen,
                btm_backfill_year=2024,
                campd_active=None,
                iso=iso,
                group_by_code=(gbc if iso != "ERCOT" else None),
            )
            btm_cls = (
                btmf.groupby("klass")["btm_twh"].sum()
                if len(btmf)
                else pd.Series(dtype=float)
            )
            e = e923.groupby("klass")["annual_mwh"].sum() / 1e6
            g923 = sum(float(e.get(k, 0)) - float(btm_cls.get(k, 0)) for k in gas_cls)
            c923 = sum(float(e.get(k, 0)) - float(btm_cls.get(k, 0)) for k in coal_cls)
            b = json.loads(
                gzip.open(f"frontend/data/backcast/bench/{iso}/{yr}.json.gz").read()
            )["bench"]
            g930 = b["e930"].get("gas", 0)
            c930 = b["e930"].get("coal", 0)
            # CAMPD coal (CEMS truth)
            c = rcf._campd_hourly_frame(yr, iso, factors, 8760)
            if c is not None:
                cp = c.groupby("plant_id")["net_mw"].sum() / 1e6
                campd_coal = sum(
                    float(t)
                    for pid, t in cp.items()
                    if pid in pjm_ids and str(gbc.get(int(pid), "")).startswith("COAL")
                )
            else:
                campd_coal = float("nan")
            print(
                f"{iso:<7}{yr:<6}{g923:8.1f}{g930:8.1f}{g923 - g930:+9.1f} | {campd_coal:9.1f}{c923:8.1f}{c930:8.1f}{c930 - campd_coal:+10.1f}"
            )
    except Exception as ex:
        print(f"{iso:<7} ERROR {ex}")
