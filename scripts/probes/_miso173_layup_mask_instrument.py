#!/usr/bin/env python3
"""miso-173 pre-solve identification + prediction instrument (NO LP).

The object: the per-plant must-run floors bind inside the plants' own MEASURED
lay-up windows — the merit-order guard's economic-lay-up extract
(``campd-unit-outages-layup-MISO.csv``), which the outage pipeline removed from
the availability envelope on the express charter that the LP declines an
economically idle unit on its own economics. The keeper then FORCES those very
plants on inside those very windows (MISO 1402's 2023 D-4 conduct FAIL is the
live case). The repair under test is ``ScenarioConfig.mustrun_layup_window_mask``
(miso-173): the floor's per-hour clip basis becomes
``pmax x max(0, availability - layup_share)``.

Everything here is computed from COMMITTED artifacts before any solve:

* the keeper's own ``hourly/system_<year>.parquet`` demand (window ranking),
* the raw outage / maxgen / lay-up extracts through the model's OWN loaders
  (``market_sim.data.outages``), so routing, denominators and window clipping
  are the engine's, not a restatement,
* the committed p25 measured-MW levels + pooled ``online_frac`` window sizes,
* the keeper's committed ``legitimacy_diagnostics.json`` D-4 rows (at-floor
  energy + conduct baselines),
* the committed CAMPD bench per-plant meter
  (``frontend/data/backcast/bench/MISO/<year>.json.gz``).

Outputs ``results/calibration/_miso173_layup_mask_instrument.json``:

* stage 1 — census: lay-up windows x live floored ST_GAS plants,
* stage 2 — per plant-year floor-VOLUME predictions est_ctrl / est_arm (TWh)
  on the window-hours ``min(level, cap)`` construction whose floor-energy half
  miso-172 verified exact to four decimals,
* stage 3 — predicted at-floor (D-4 ``floored_twh``) movements via the volume
  ratio, with the +/-50 % bands the prereg freezes (the at-floor-rate-fixed
  instrument, REPORTED per the miso-172 section 4 lesson; the KILL band is the
  volume basis),
* stage 4 — the honest conduct-rider prediction: each floored plant-year's
  metered zero-share over its UNMASKED window hours (window grain; miso-172
  measured binding-set concentration beating the window-grain prediction by
  ~12 pp, so this is a conservative bound for 1402-2023).

Usage::

    python3 scripts/probes/_miso173_layup_mask_instrument.py \
        [--keeper results/calibration/miso172_p25mw] [--json-out PATH]
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
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.data.outages import (  # noqa: E402
    unit_layup_removed_fractions,
    unit_outage_derate_factors,
    unit_outage_maxgen_derate_factors,
)

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
MECH_LABEL = "st_gas_mustrun_per_plant × ST_GAS"


def _pkg():
    import market_sim.data.fleet as fleet_pkg

    return fleet_pkg


def _system_load(keeper: Path, year: int) -> np.ndarray:
    df = pd.read_parquet(keeper / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    load = df.groupby("hour")["demand"].sum().sort_index().to_numpy()
    assert load.size == HOURS, load.size
    return load


def _d4_conduct_rows(keeper: Path) -> list[dict]:
    d = json.loads((keeper / "legitimacy_diagnostics.json").read_text())
    return [
        r
        for r in d["diagnostics"]["D4"]["rows"]
        if r.get("check") == "unit-conduct" and r.get("floor") == MECH_LABEL
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keeper", default="results/calibration/miso172_p25mw")
    ap.add_argument(
        "--json-out",
        default="results/calibration/_miso173_layup_mask_instrument.json",
    )
    args = ap.parse_args()
    keeper = REPO / args.keeper

    fleet_pkg = _pkg()
    levels = fleet_pkg.thermal_tranche_p25_measured_level(ISO)
    fracs = fleet_pkg.thermal_tranche_online_frac(ISO)
    from market_sim.data.bridge_layup_exclusions import load_layup_exclusions

    excluded = load_layup_exclusions(ISO)

    # Live floored ST_GAS plants: measured level > 0, pooled window > 0, not in
    # the lay-up membership census — the same qualification the engine applies.
    live = sorted(
        pc
        for (pc, grp), lvl in levels.items()
        if grp == "ST_GAS"
        and lvl > 0.0
        and fracs.get((pc, grp), 0.0) > 0.0
        and pc not in excluded
    )

    from market_sim.data.outages import _iso_plant_capacity

    cap_map = _iso_plant_capacity(ISO)

    from legitimacy_diagnostics import bench_plant_view, load_bench  # noqa: E402

    d4_rows = _d4_conduct_rows(keeper)
    d4 = {(int(r["year"]), int(r["plant"])): r for r in d4_rows}

    out: dict = {
        "schema": "miso173-layup-mask-instrument-v1",
        "keeper": str(keeper.relative_to(REPO)),
        "live_floored_st_gas_plants": live,
        "census": {},
        "volume_predictions": {},
        "at_floor_predictions": {},
        "conduct_predictions": {},
        "mechanism_totals": {},
    }

    for year in YEARS:
        load = _system_load(keeper, year)
        rank = np.argsort(-load, kind="stable")
        ofac = unit_outage_derate_factors(year, HOURS, iso=ISO)
        mfac = unit_outage_maxgen_derate_factors(year, HOURS, iso=ISO)
        lay = unit_layup_removed_fractions(year, HOURS, iso=ISO)
        bench = bench_plant_view(load_bench(REPO, ISO, year))

        year_rows = {}
        tot_ctrl = tot_arm = 0.0
        pred_dfloor = 0.0
        for pc in live:
            key = (pc, "ST_GAS")
            level = levels[key]
            frac = fracs[key]
            capn = cap_map.get(key, 0.0)
            if capn <= 0.0:
                continue
            k = int(round(frac * HOURS))
            win = np.zeros(HOURS, dtype=bool)
            win[rank[:k]] = True
            avail = np.ones(HOURS)
            if key in ofac:
                avail = avail * ofac[key]
            if key in mfac:
                avail = avail * mfac[key]
            lu = lay.get(key, np.zeros(HOURS))
            cap_ctrl = capn * avail
            cap_arm = capn * np.maximum(0.0, avail - lu)
            est_ctrl = float(np.minimum(level, cap_ctrl)[win].sum()) / 1e6
            est_arm = float(np.minimum(level, cap_arm)[win].sum()) / 1e6
            ratio = est_arm / est_ctrl if est_ctrl > 0 else 1.0
            masked_win_h = int((win & (lu > 0)).sum())
            row = {
                "level_mw": level,
                "online_frac": frac,
                "window_h": k,
                "layup_hours_in_window": masked_win_h,
                "est_ctrl_twh": round(est_ctrl, 6),
                "est_arm_twh": round(est_arm, 6),
                "volume_ratio": round(ratio, 6),
            }
            d4r = d4.get((year, pc))
            if d4r is not None:
                floored = float(d4r["floored_twh"])
                row["d4_floored_twh_ctrl"] = floored
                row["d4_floored_twh_pred"] = round(floored * ratio, 4)
                pred_dfloor += floored * (ratio - 1.0)
            # Conduct prediction over UNMASKED window hours (window grain).
            b = bench.get(str(pc))
            if b is not None:
                meas = np.asarray(b["mw"], dtype=float)[:HOURS]
                arm_win = win & (np.minimum(level, cap_arm) > 0)
                ctrl_win = win & (np.minimum(level, cap_ctrl) > 0)
                if meas.size == HOURS and arm_win.any() and ctrl_win.any():
                    row["zero_share_ctrl_window"] = round(
                        float((meas[ctrl_win] <= 0.0).mean()), 4
                    )
                    row["zero_share_arm_window"] = round(
                        float((meas[arm_win] <= 0.0).mean()), 4
                    )
            year_rows[str(pc)] = row
            tot_ctrl += est_ctrl
            tot_arm += est_arm
        out["volume_predictions"][str(year)] = year_rows
        d_vol = tot_arm - tot_ctrl
        out["mechanism_totals"][str(year)] = {
            "est_ctrl_twh": round(tot_ctrl, 6),
            "est_arm_twh": round(tot_arm, 6),
            "delta_volume_twh": round(d_vol, 6),
            "pred_delta_at_floor_twh": round(pred_dfloor, 4),
            "at_floor_band_lo": round(1.5 * pred_dfloor, 4),
            "at_floor_band_hi": round(0.5 * pred_dfloor, 4),
        }
        # Census: raw lay-up windows for the live plants.
        lay_csv = pd.read_csv(
            REPO / "data/raw/campd-unit-outages-layup-MISO.csv",
            parse_dates=["outage_start", "outage_end"],
        )
        w = lay_csv[
            (lay_csv.facility_id.isin(live))
            & (lay_csv.plant_group == "ST_GAS")
            & (lay_csv.outage_end >= pd.Timestamp(f"{year}-01-01"))
            & (lay_csv.outage_start <= pd.Timestamp(f"{year}-12-31"))
        ]
        out["census"][str(year)] = {
            str(pc): {
                "windows": int((w.facility_id == pc).sum()),
                "unit_days": round(float(w[w.facility_id == pc].duration_days.sum()), 1),
            }
            for pc in live
            if (w.facility_id == pc).any()
        }

    dst = REPO / args.json_out
    dst.write_text(json.dumps(out, indent=1))
    print(f"wrote {dst}")
    for year in YEARS:
        t = out["mechanism_totals"][str(year)]
        print(
            f"{year}: vol {t['est_ctrl_twh']:.4f} -> {t['est_arm_twh']:.4f} TWh "
            f"(d={t['delta_volume_twh']:+.4f}); pred d at-floor "
            f"{t['pred_delta_at_floor_twh']:+.4f} TWh"
        )
        r1402 = out["volume_predictions"][str(year)].get("1402")
        if r1402:
            print(
                f"  1402: ratio {r1402['volume_ratio']:.3f}, zero-share "
                f"{r1402.get('zero_share_ctrl_window')} -> "
                f"{r1402.get('zero_share_arm_window')} (window grain)"
            )


if __name__ == "__main__":
    main()
