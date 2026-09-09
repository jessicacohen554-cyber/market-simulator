"""SPP-51c phase 0 (zero LP): the oversupply water-fill allocation's own footprint.

Builds the instrument declared in PRECOMMIT-spp-51c-2026-09-09.md section 2.2 outside
the LP and measures legs F-1..F-5 plus the screen-year selection rule, against the
committed measured actual RT LMP series. No solve, no bundle, no registration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import renewables as R
from market_sim.data.eia930.demand import load_demand

ISO = "SPP"
YEARS = (2023, 2024, 2025)
ACTUAL_LMP = RAW_DATA_DIR / "_validation-source" / f"actual_lmp_hourly_{ISO}.parquet"


def water_fill(nl_mw, headroom_mw, target_mwh):
    """Return (curt_mw, lambda) solving sum(min(relu(lam - NL), H)) = target."""
    lo, hi = float(nl_mw.min()) - 1.0, float(nl_mw.max()) + 1.0
    cap_total = float(np.minimum(np.maximum(hi - nl_mw, 0.0), headroom_mw).sum())
    if cap_total < target_mwh:
        return None, None  # F-1 instrument failure: no root
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        tot = float(np.minimum(np.maximum(mid - nl_mw, 0.0), headroom_mw).sum())
        if tot < target_mwh:
            lo = mid
        else:
            hi = mid
    lam = 0.5 * (lo + hi)
    return np.minimum(np.maximum(lam - nl_mw, 0.0), headroom_mw), lam


def main() -> None:
    cfg = ScenarioConfig(mode="backcast", hindcast=False)
    iso_cfg = get_iso_config(ISO)
    zone_names = iso_cfg.zone_names
    rate_info = R._reference_curtailment_rate(ISO, "wind")
    rate = rate_info[0]
    lmp = pd.read_parquet(ACTUAL_LMP)
    out = {"reference_rate": rate, "years": {}}

    for year in YEARS:
        gen = R.load_eia_hourly_renewable_gen(ISO, year)
        wind = np.asarray(gen["wind"], dtype=float)
        solar = np.asarray(gen.get("solar", np.zeros(HOURS_PER_YEAR)), dtype=float)
        monthly = R._eia860_monthly_capacity(ISO, "wind", zone_names, year)
        cap_online = monthly.sum(axis=0)[R._hour_to_month_index(HOURS_PER_YEAR)]
        load = load_demand(ISO, year, iso_cfg).sum(axis=0)

        # today's flat rule
        flat = wind / (1.0 - rate)
        target = float(flat.sum() - wind.sum())          # C, the frozen annual energy
        headroom = np.maximum(cap_online - wind, 0.0)
        nl = load - wind - solar
        curt, lam = water_fill(nl, headroom, target)
        if curt is None:
            out["years"][year] = {"F1_root": False}
            continue
        pot = wind + curt

        # measured-negative hours on the committed actual series
        sub = lmp[lmp["year"] == year] if "year" in lmp.columns else lmp
        rt_raw = sub.sort_values("hour")["rt"].to_numpy(dtype=float)[:HOURS_PER_YEAR]
        # CLOCK REPAIR (this lane's finding, direction fixed by SOLAR NOON and by
        # SPP's own UTC-stamped GenMix, NOT by any residual): the committed SPP
        # sidecar is indexed on UTC while the model's EIA-930 frame is Central
        # PREVAILING time, so sidecar row t+offset(t) is the price the model's
        # hour t faced. offset = 6 h CST / 5 h CDT.
        idx = pd.date_range(f"{year}-01-01", periods=HOURS_PER_YEAR, freq="h",
                            tz="America/Chicago")
        off = np.where([bool(t.dst().total_seconds()) for t in idx], 5, 6)
        src = np.arange(HOURS_PER_YEAR) + off
        rt = np.full(HOURS_PER_YEAR, np.nan)
        ok_src = src < HOURS_PER_YEAR
        rt[ok_src] = rt_raw[src[ok_src]]
        neg = np.isfinite(rt) & (rt < 0.0)
        neg_mis = np.isfinite(rt_raw) & (rt_raw < 0.0)

        alloc = curt > 1e-9
        row = {
            "F1_root": True,
            "F1_identity_rel_err": float(abs(pot.sum() - flat.sum()) / flat.sum()),
            "F1_pot_ge_delivered": bool((pot >= wind - 1e-9).all()),
            "C_TWh": target / 1e6,
            "delivered_TWh": float(wind.sum()) / 1e6,
            "measured_neg_hours": int(neg.sum()),
            # F-2 concentration: share of C landing in the measured-negative hours
            "F2_share_in_neg_pct": float(curt[neg].sum() / curt.sum() * 100.0),
            "F2_uniform_share_pct": float(neg.sum() / HOURS_PER_YEAR * 100.0),
            "F2_flat_rule_share_pct": float(wind[neg].sum() / wind.sum() * 100.0),
            "F2_share_MISALIGNED_pct": float(curt[neg_mis].sum() / curt.sum() * 100.0),
            "neg_hours_misaligned": int(neg_mis.sum()),
            "neg_set_overlap_pct": float((neg & neg_mis).sum() / max(neg.sum(),1) * 100.0),
            # F-3 breadth
            "F3_alloc_hours": int(alloc.sum()),
            # F-4 reach: mean lift of the bound over today's flat bound, in neg hours
            "F4_mean_lift_neg_MW": float((pot - flat)[neg].mean()),
            "F4_mean_bound_neg_MW": float(pot[neg].mean()),
            "F4_flat_bound_neg_MW": float(flat[neg].mean()),
            "F4_delivered_neg_MW": float(wind[neg].mean()),
            # F-5 lambda, reported not set
            "F5_lambda_GW": lam / 1e3,
            "nl_mean_GW": float(nl.mean()) / 1e3,
            "nl_p10_GW": float(np.percentile(nl, 10)) / 1e3,
            # screen-year selection rule: largest reallocated energy
            "reallocated_TWh": float(np.abs(pot - flat).sum()) / 1e6,
            "alloc_hours_that_are_neg": int((alloc & neg).sum()),
            "neg_hours_that_are_alloc_pct": float((alloc & neg).sum() / neg.sum() * 100.0),
            "max_pot_MW": float(pot.max()),
            "cap_online_max_MW": float(cap_online.max()),
            "binding_cap_hours": int((curt >= headroom - 1e-6).sum()),
        }
        out["years"][year] = row

    print(json.dumps(out, indent=1))
    Path("results/calibration/_spp51c_phase0_aligned.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
