"""miso-224 phase 0 (part 4) — the PRE-SOLVE arithmetic: what does re-pricing gas at
marginal commodity do to the body price, before any LP is spent?

Zero-solve. Rebuilds the keeper's fleet and offer basis (``build_year``, the
miso-220 instrument) and, for every hour, clears the STATIC merit stack twice:

* at the keeper's own ``mc_base`` (the P0 bid basis);
* at ``mc_base + (spot - delivered) x heat_rate`` on GAS rows only — the arm's
  offer basis, every other row untouched.

The static clearing price for an hour is the ``mc`` of the last tranche needed to
meet that hour's committed fleet dispatch ``Q_h`` (the P1 ``class_hourly`` sum over
the classes the assembled fleet carries — thermal, nuclear, hydro, oil, biomass;
wind/solar/import excluded), read from the keeper's own sidecar. Congestion,
floors, reserves and the P1 startup adder are outside a static stack, so the
instrument first reports its OWN error — static price at the keeper's basis vs the
keeper's committed P1 price — and the prediction is the DIFFERENCE between the two
static clearings, which cancels whatever is common to both.

What it yields, per hour set: the predicted price change (mean, p10, p90), the
predicted change in the marginal class (who holds the margin at spot), and the
predicted coal-vs-gas dispatch swap at the margin. These are the numbers a
rule-29 screen gate is set against, written BEFORE the solve.

Spot = the measured Chicago Citygate daily hub (monthly mean; MISO-South rows at
Henry Hub monthly), the same comparator as part 3.

Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only. No LP is solved; nothing is minted.

Usage::

    MISO224_YEARS=2024 python3 scripts/probes/_miso224_static_remerit_phase0.py
"""

from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
_m134.BUNDLE = KEEPER

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso221_peak_shape_phase0 import _band, _r  # noqa: E402
from _miso224_floor_anatomy_phase0 import actual_mec, actual_zone_price  # noqa: E402
from _miso224_marginal_frequency_phase0 import CARRYING, keeper_prices  # noqa: E402
from _miso224_offer_decomposition_phase0 import _month_of_hour, spot_gas_by_month  # noqa: E402

OUT = REPO / "results/calibration/_miso224_static_remerit.json"
YEARS = tuple(int(v) for v in os.environ.get("MISO224_YEARS", "2023,2024,2025").split(","))
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
ZONE = "MISO-Indiana"
FLEET_CLASSES = ("CC_CHP", "CC_REGULAR", "COAL", "COAL_BIT", "COAL_LIGNITE", "COAL_PRB", "CT_CHP",
                 "CT_PEAKER", "OTHER", "ST_CHP", "ST_GAS", "biomass", "hydro", "nuclear", "oil")
COAL_CLASSES = ("COAL", "COAL_BIT", "COAL_LIGNITE", "COAL_PRB")


def hh_by_month(year: int) -> np.ndarray:
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_monthly.csv")
    hh = hh[hh["year"] == year].set_index("month")["price_usd_mmbtu"]
    return np.array([float(hh.get(m, np.nan)) for m in range(1, 13)])


def fleet_dispatch(year: int) -> np.ndarray:
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"].isin(FLEET_CLASSES))]
    return c.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)


def static_clear(mc_h: np.ndarray, cap_h: np.ndarray, q: float, klass: np.ndarray, is_gas: np.ndarray, is_coal: np.ndarray):
    """(price, marginal class, gas MW in merit, coal MW in merit) at static demand q."""
    order = np.argsort(mc_h, kind="stable")
    cum = np.cumsum(cap_h[order])
    k = int(np.searchsorted(cum, q))
    k = min(k, len(order) - 1)
    inm = order[: k + 1]
    return float(mc_h[order[k]]), str(klass[order[k]]), float(cap_h[inm][is_gas[inm]].sum()), float(cap_h[inm][is_coal[inm]].sum())


def analyse_year(year: int) -> dict:
    cfg = keeper_config()
    raw_fleet, fleet, arrays, fuel_prices, mc, zone_names = build_year(cfg, year)
    n = len(fleet)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    fuel_name = np.array([str(getattr(g, "fuel_type", "") or "").lower() for g in fleet])
    is_gas = np.array([f.startswith("gas") for f in fuel_name])
    is_coal = np.isin(klass, COAL_CLASSES) | (fuel_name == "coal")
    zone = np.array([str(g.zone) for g in fleet])
    south = zone == "MISO-South"
    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    fp = np.asarray(fuel_prices, float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    hr = np.asarray(arrays.heat_rate, float)
    moh = _month_of_hour() - 1
    spot_mw = spot_gas_by_month(year)[moh]      # Midwest: Chicago Citygate
    spot_s = hh_by_month(year)[moh]             # South: Henry Hub
    spot = np.where(south[:, None], spot_s[None, :], spot_mw[None, :])
    delta = np.where(is_gas[:, None], (spot - fp) * hr[:, None], 0.0)
    mc_arm = mc + delta

    q = fleet_dispatch(year)
    p_keeper = keeper_prices(year)[ZONE].to_numpy(float)
    mec, _, _ = actual_mec(year)
    act = actual_zone_price(year)[ZONE].to_numpy(float)

    p0 = np.full(HOURS, np.nan); p1 = np.full(HOURS, np.nan)
    k0 = np.full(HOURS, "", dtype=object); k1 = np.full(HOURS, "", dtype=object)
    g0 = np.zeros(HOURS); g1 = np.zeros(HOURS); c0 = np.zeros(HOURS); c1 = np.zeros(HOURS)
    for h in range(HOURS):
        cap_h = pmax * avail[:, h]
        live = cap_h > 1.0
        idx = np.flatnonzero(live)
        p0[h], k0[h], g0[h], c0[h] = static_clear(mc[idx, h], cap_h[idx], q[h], klass[idx], is_gas[idx], is_coal[idx])
        p1[h], k1[h], g1[h], c1[h] = static_clear(mc_arm[idx, h], cap_h[idx], q[h], klass[idx], is_gas[idx], is_coal[idx])
    dp = p1 - p0
    ok = np.isfinite(mec)
    sets = {"all": ok, "body": ok & (p_keeper <= np.percentile(p_keeper, 90)),
            "tail_top10": ok & (p_keeper > np.percentile(p_keeper, 90)),
            "actual_hub_lt_20": ok & np.isfinite(act) & (act < 20.0),
            "model_bottom_decile": ok & (p_keeper <= np.percentile(p_keeper, 10))}
    pct = np.percentile(mec[ok], np.arange(0, 101, 10))
    for d in range(10):
        sets[f"mec_d{d + 1}"] = ok & (mec >= pct[d]) & ((mec < pct[d + 1]) if d < 9 else (mec <= pct[d + 1]))
    rec = {"n_tranches": int(n), "zone": ZONE, "by_set": {}}
    for name, m in sets.items():
        if not m.any():
            rec["by_set"][name] = {"n": 0}
            continue
        rec["by_set"][name] = {
            "n": int(m.sum()),
            "keeper_p1_mean": _r(p_keeper[m].mean()), "mec_mean": _r(mec[m].mean()),
            "static_at_keeper_basis_mean": _r(p0[m].mean()),
            "instrument_error_static_minus_p1": _r((p0 - p_keeper)[m].mean()),
            "static_at_spot_basis_mean": _r(p1[m].mean()),
            "predicted_delta_mean": _r(dp[m].mean()), "predicted_delta_p10": _r(np.percentile(dp[m], 10)),
            "predicted_delta_p50": _r(np.median(dp[m])), "predicted_delta_p90": _r(np.percentile(dp[m], 90)),
            "predicted_p1_mean_if_delta_holds": _r((p_keeper + dp)[m].mean()),
            "gap_to_mec_before": _r((p_keeper - mec)[m].mean()), "gap_to_mec_after": _r((p_keeper + dp - mec)[m].mean()),
            "marginal_gas_share_before": _r(np.mean([str(k).startswith(("CC", "CT", "ST_GAS")) for k in k0[m]]), 3),
            "marginal_gas_share_after": _r(np.mean([str(k).startswith(("CC", "CT", "ST_GAS")) for k in k1[m]]), 3),
            "marginal_coal_share_before": _r(np.mean([str(k).startswith("COAL") for k in k0[m]]), 3),
            "marginal_coal_share_after": _r(np.mean([str(k).startswith("COAL") for k in k1[m]]), 3),
            "gas_in_merit_mw_delta": _r((g1 - g0)[m].mean(), 0), "coal_in_merit_mw_delta": _r((c1 - c0)[m].mean(), 0),
        }
    del raw_fleet, fleet, arrays, fuel_prices, mc, mc_arm, fp
    gc.collect()
    return rec


def main() -> int:
    rec = {"probe": "miso-224 phase 0 part 4 - static re-merit prediction of the marginal-commodity gas arm",
           "keeper": "2026-09-05-miso-220-nonsteam-lift", "bundle": str(KEEPER.relative_to(REPO)), "solved": False, "by_year": {}}
    if OUT.exists():
        try:
            rec["by_year"] = json.loads(OUT.read_text()).get("by_year", {})
        except Exception:  # noqa: BLE001
            pass
    for y in YEARS:
        rec["by_year"][str(y)] = analyse_year(y)
        for s in ("body", "tail_top10", "actual_hub_lt_20", "mec_d1", "mec_d5", "mec_d9"):
            r = rec["by_year"][str(y)]["by_set"][s]
            print(f"  {y} {s:17s} n={r['n']} P1 {r['keeper_p1_mean']} static0 {r['static_at_keeper_basis_mean']} (err {r['instrument_error_static_minus_p1']}) "
                  f"dP mean {r['predicted_delta_mean']} p10/p50/p90 {r['predicted_delta_p10']}/{r['predicted_delta_p50']}/{r['predicted_delta_p90']} "
                  f"gap {r['gap_to_mec_before']} -> {r['gap_to_mec_after']} | gas-marg {r['marginal_gas_share_before']}->{r['marginal_gas_share_after']} "
                  f"coal-merit dMW {r['coal_in_merit_mw_delta']}", flush=True)
        OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
