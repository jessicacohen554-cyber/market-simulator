"""miso-224 phase 0 (part 3) — WHICH LAYER of the marginal offer carries the body wedge?

Zero-solve. Rebuilds the designated keeper's OWN fleet and offer basis
(``2026-09-05-miso-220-nonsteam-lift``, bundle ``miso220_nonsteamlift_B``) via
``_miso134_ct_night_order_screen.build_year`` (the miso-220 instrument), finds the
tranche that brackets the committed P1 price at the C3a zone (MISO-Indiana) in
EVERY hour (the part-2 construction), and decomposes that tranche's offer into its
layers against the measured system energy price (MEC = LMP - MCC - MLC, the hub
csv; part 1's construction).

THE IDENTITY, per hour (all $/MWh)::

    model_price - MEC  =  (model_price - mc_base)          # P1 startup adder (residual)
                        + (mc_base - srmc_model_fuel)       # MARKUP layer: band multipliers,
                                                            #   coal tranche ladder, gas net-
                                                            #   revenue margin, anchored spread
                        + (srmc_model_fuel - srmc_spot_fuel)# FUEL-CONVENTION layer (gas only):
                                                            #   EIA-923 average delivered cost
                                                            #   vs Henry Hub month + Chicago
                                                            #   citygate basis (spot commodity)
                        + (srmc_spot_fuel - MEC)            # RESIDUAL: the model's marginal
                                                            #   unit, at spot fuel, is still
                                                            #   dearer than reality's marginal
                                                            #   (merit order / imports / HR)

``srmc_model_fuel`` is ``assemble_mc`` on the resolved delivered fuel (heat rate x
fuel + VOM + NOx/SO2), i.e. the offer basis BEFORE ``apply_coal_tranches`` /
``apply_gas_offer_margin`` / band multipliers. ``srmc_spot_fuel`` re-prices GAS
tranches only, at the month's Henry Hub mean plus the MISO row of
``data/raw/gas_basis_by_iso_month.csv`` (EIA IL citygate - HH); coal and every
other fuel keep their delivered price (no spot comparator exists), so for them the
fuel-convention layer is identically zero.

Each layer is reported by hour set (body, actual-hub < $20, MEC decile) as a mean
contribution, and by the marginal tranche's class-band, so a successor can read
"the +$X body wedge is $a markup, $b fuel convention, $c residual, and the markup
half sits on COAL|econ / CC_REGULAR|econ". The fuel-convention layer is reported
because miso-212 sized it and left it in owner court; nothing here arms it.

Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only. No LP is solved; nothing is minted.

Usage::

    MISO224_YEARS=2024 python3 scripts/probes/_miso224_offer_decomposition_phase0.py
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
from _miso224_marginal_frequency_phase0 import CARRYING, EPS, PRICE_TIE, keeper_prices  # noqa: E402
from market_sim.data.fleet import assemble_mc  # noqa: E402

OUT = REPO / "results/calibration/_miso224_offer_decomposition.json"
YEARS = tuple(int(v) for v in os.environ.get("MISO224_YEARS", "2023,2024,2025").split(","))
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
ZONE = "MISO-Indiana"
MONTH_LENS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
GAS_FUELS = {"gas", "natural_gas", "ng", "natural gas"}


def _month_of_hour() -> np.ndarray:
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[:HOURS]


def spot_gas_by_month(year: int) -> np.ndarray:
    """(12,) monthly mean of the measured Chicago Citygate daily SPOT, $/MMBtu.

    ``data/raw/gas-prices/miso_citygate_daily.csv`` — the "Chicago" row of the EIA
    Natural Gas Weekly Update spot table (the traded hub index, NOT the EIA
    N3050IL3 utility-citygate survey that ``gas_basis_by_iso_month.csv`` proxies,
    which sits $1-2/MMBtu above the hub because it carries LDC transport). This is
    the marginal-commodity comparator miso-212 named ("HH spot + variable
    transport"), read at the hub. Months with no print fall back to Henry Hub.
    """
    cg = pd.read_csv(REPO / "data/raw/gas-prices/miso_citygate_daily.csv", parse_dates=["date"])
    cg = cg[cg["date"].dt.year == year]
    by_m = cg.groupby(cg["date"].dt.month)["chicago_citygate_usd_mmbtu"].mean()
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_monthly.csv")
    hh = hh[hh["year"] == year].set_index("month")["price_usd_mmbtu"]
    return np.array([float(by_m.get(m, hh.get(m, np.nan))) for m in range(1, 13)])


def _agg(mask: np.ndarray, cols: dict[str, np.ndarray]) -> dict:
    if not mask.any():
        return {"n": 0}
    return {"n": int(mask.sum()), **{k: _r(np.nanmean(v[mask]), 2) for k, v in cols.items()}}


def analyse_year(year: int) -> dict:
    cfg = keeper_config()
    raw_fleet, fleet, arrays, fuel_prices, mc, zone_names = build_year(cfg, year)
    n = len(fleet)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    band = np.array([_band(g.unit_id) for g in fleet])
    key = np.array([f"{k}|{b}" for k, b in zip(klass, band)])
    fuel_name = np.array([str(getattr(g, "fuel_type", "") or "").lower() for g in fleet])
    # Fleet fuel_type labels are 'gas_cc' / 'gas_ct' / 'gas_st' (measured on the
    # assembled fleet); the prefix is the gas test.
    is_gas = np.array([f.startswith("gas") or f in GAS_FUELS for f in fuel_name])
    zone = np.array([str(g.zone) for g in fleet])
    zi = {z: i for i, z in enumerate(zone_names)}
    gz = np.array([zi.get(z, -1) for z in zone])
    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    fp = np.asarray(fuel_prices, float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    # Offer basis BEFORE tranches / margins / multipliers.
    srmc = np.asarray(assemble_mc(arrays, fp, 0.0, cfg.nox_price, so2=(arrays.so2_rate, cfg.so2_price)), float)
    if srmc.ndim == 1:
        srmc = np.tile(srmc[:, None], (1, HOURS))
    # Gas tranches re-priced at spot commodity (HH month + MISO basis).
    spot = spot_gas_by_month(year)[_month_of_hour() - 1]                 # (H,)
    hr = np.asarray(arrays.heat_rate, float)
    fp_spot = fp.copy()
    fp_spot[is_gas, :] = spot[None, :]
    srmc_spot = srmc + (fp_spot - fp) * hr[:, None]                     # fuel layer only

    prices = keeper_prices(year)
    P = prices[CARRYING].to_numpy(float)
    j = CARRYING.index(ZONE)
    mec, _, _ = actual_mec(year)
    act = actual_zone_price(year)[ZONE].to_numpy(float)

    p_h = P[:, j]
    m_key = np.full(HOURS, "", dtype=object)
    mcb = np.full(HOURS, np.nan); sr = np.full(HOURS, np.nan); srs = np.full(HOURS, np.nan)
    fuel_m = np.full(HOURS, np.nan); fuel_s = np.full(HOURS, np.nan); hr_m = np.full(HOURS, np.nan)
    gas_m = np.zeros(HOURS, bool)
    for h in range(HOURS):
        cap_h = pmax * avail[:, h]
        live = cap_h > 1.0
        mc_h = mc[:, h]
        p = p_h[h]
        grp = [zi[CARRYING[k]] for k in range(len(CARRYING)) if abs(P[h, k] - p) <= PRICE_TIE]
        elig = live & np.isin(gz, grp) & (mc_h <= p + EPS)
        if not elig.any():
            continue
        i = int(np.flatnonzero(elig)[np.argmax(mc_h[elig])])
        m_key[h] = key[i]; mcb[h] = mc_h[i]; sr[h] = srmc[i, h]; srs[h] = srmc_spot[i, h]
        fuel_m[h] = fp[i, h]; fuel_s[h] = fp_spot[i, h]; hr_m[h] = hr[i]; gas_m[h] = bool(is_gas[i])

    layers = {
        "model_price": p_h, "mec": mec, "gap_model_minus_mec": p_h - mec,
        "L0_startup_adder": p_h - mcb,
        "L1_markup": mcb - sr,
        "L2_fuel_convention_gas": sr - srs,
        "L3_residual_vs_mec": srs - mec,
        "marginal_fuel_model": fuel_m, "marginal_fuel_spot": fuel_s, "marginal_hr": hr_m,
        "markup_ratio": mcb / np.where(sr > 0, sr, np.nan),
    }
    ok = np.isfinite(mec) & np.isfinite(mcb)
    sets = {
        "all": ok,
        "body": ok & (p_h <= np.percentile(p_h, 90)),
        "actual_hub_lt_20": ok & np.isfinite(act) & (act < 20.0),
        "model_bottom_decile": ok & (p_h <= np.percentile(p_h, 10)),
    }
    pct = np.percentile(mec[ok], np.arange(0, 101, 10))
    for d in range(10):
        sets[f"mec_d{d + 1}"] = ok & (mec >= pct[d]) & ((mec < pct[d + 1]) if d < 9 else (mec <= pct[d + 1]))
    rec = {"n_tranches": int(n), "zone": ZONE, "by_set": {}, "by_marginal_class_band": {}}
    for name, m in sets.items():
        row = _agg(m, layers)
        row["marginal_is_gas_share"] = _r(gas_m[m].mean(), 3) if m.any() else None
        rec["by_set"][name] = row
    # by marginal class-band within the body: each band's share of the body wedge
    body = sets["body"]
    for k in np.unique(m_key[body]):
        m = body & (m_key == k)
        row = _agg(m, layers)
        row["share_of_body_hours"] = _r(m.sum() / body.sum(), 4)
        row["share_of_body_gap"] = _r(np.nansum((p_h - mec)[m]) / np.nansum((p_h - mec)[body]), 4)
        rec["by_marginal_class_band"][str(k)] = row
    rec["by_marginal_class_band"] = dict(sorted(rec["by_marginal_class_band"].items(),
                                                key=lambda kv: -(kv[1].get("share_of_body_hours") or 0)))
    # Fleet-level (capacity-weighted) view of the same layers, so the marginal read
    # can be checked against the whole stack: mean markup ratio by class-band.
    cw = {}
    for k in np.unique(key):
        s = key == k
        cap = (pmax[s, None] * avail[s, :]).sum()
        if cap <= 0:
            continue
        w = pmax[s, None] * avail[s, :]
        cw[str(k)] = {"cap_mw_mean": _r((pmax[s] * avail[s, :].mean(axis=1)).sum(), 0),
                      "markup_ratio_cw": _r(float((mc[s, :] / np.where(srmc[s, :] > 0, srmc[s, :], np.nan) * w).sum() / cap), 3),
                      "srmc_cw": _r(float((srmc[s, :] * w).sum() / cap), 2),
                      "mc_base_cw": _r(float((mc[s, :] * w).sum() / cap), 2),
                      "fuel_conv_cw": _r(float(((srmc[s, :] - srmc_spot[s, :]) * w).sum() / cap), 2)}
    rec["fleet_capweighted_by_class_band"] = cw
    spot_m = spot_gas_by_month(year)
    rec["spot_gas_by_month"] = [_r(v, 3) for v in spot_m]
    # The delivered-vs-spot gap by month for the CC fleet (cap-weighted): where in
    # the year the fuel-convention layer lives.
    moh = _month_of_hour()
    cc = np.array([f == "gas_cc" for f in fuel_name])
    w_cc = pmax[cc, None] * avail[cc, :]
    fuel_cc_m = []
    for m in range(1, 13):
        hm = moh == m
        ww = w_cc[:, hm]
        fuel_cc_m.append(_r(float((fp[cc][:, hm] * ww).sum() / max(ww.sum(), 1e-9)), 3))
    rec["cc_fleet_delivered_fuel_by_month_cw"] = fuel_cc_m
    rec["cc_fleet_delivered_minus_spot_by_month"] = [_r(a - b, 3) for a, b in zip(fuel_cc_m, spot_m)]
    del raw_fleet, fleet, arrays, fuel_prices, mc, srmc, srmc_spot, fp, fp_spot
    gc.collect()
    return rec


def main() -> int:
    rec = {"probe": "miso-224 phase 0 part 3 - layers of the marginal offer against the MEC",
           "keeper": "2026-09-05-miso-220-nonsteam-lift", "bundle": str(KEEPER.relative_to(REPO)),
           "solved": False, "by_year": {}}
    if OUT.exists():
        try:
            rec["by_year"] = json.loads(OUT.read_text()).get("by_year", {})
        except Exception:  # noqa: BLE001
            pass
    for y in YEARS:
        rec["by_year"][str(y)] = analyse_year(y)
        bs = rec["by_year"][str(y)]["by_set"]
        for s in ("body", "actual_hub_lt_20", "mec_d1", "mec_d3", "mec_d5", "mec_d8"):
            r = bs[s]
            print(f"  {y} {s}: n={r['n']} gap {r['gap_model_minus_mec']} = adder {r['L0_startup_adder']} + markup {r['L1_markup']} "
                  f"+ fuelconv {r['L2_fuel_convention_gas']} + residual {r['L3_residual_vs_mec']} | fuel model {r['marginal_fuel_model']} spot {r['marginal_fuel_spot']} gas-share {r['marginal_is_gas_share']}", flush=True)
        for k, r in list(rec["by_year"][str(y)]["by_marginal_class_band"].items())[:6]:
            print(f"    {k}: hours {r['share_of_body_hours']} gapshare {r['share_of_body_gap']} markup {r['L1_markup']} fuelconv {r['L2_fuel_convention_gas']} resid {r['L3_residual_vs_mec']} ratio {r['markup_ratio']}")
        OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
