"""SPP-70 — zero-LP sizing of the offer-curve band lever.

The question the headroom probe leaves open: SPP's keeper prices every band of
every material class at the SAME heat-rate multiplier (0.93), so no gas plant
has a rising offer curve at all.  Restoring a rising curve reprices whichever
band is marginal, so the lever is not inert a priori even though the top of the
stack is never reached.  This sizes it WITHOUT a solve.

Instrument: a merit-order reconstruction of the clearing price.  Per hour, sort
the LP's own thermal rows by ``mc_base[:, t]``, cumulate ``pmax * availability``,
and read the marginal cost at the thermal energy the LP actually served (from
the bundle's committed ``class_hourly``).  The reconstruction is VALIDATED
against the bundle's committed P1 price first -- a counterfactual is only quoted
where the instrument reproduces the incumbent.

The counterfactual re-derives ``mc`` with a different ``offer_curve_by_group``
band multiplier per (class, band), holding fuel price, VOM and the tranche
capacity split fixed, then re-reads the same merit order.  Because the keeper's
bands are uniform at 0.93, ``mc / 0.93 * m`` is the exact repriced band: the
fuel term scales with the multiplier and the VOM term does not, so both are
carried separately.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BUNDLES = {
    2019: "spp67_yearown_rung",
    2020: "spp67_yearown_rung",
    2021: "spp67_yearown_rung",
    2022: "spp67_yearown_rung",
    2023: "spp67_yearown_span",
    2024: "spp67_yearown_span",
    2025: "spp67_yearown_span",
}
THERMAL_PREFIXES = ("COAL", "CC_", "CT_", "ST_")

# The generic shipped curve (pipeline/backcast_config.py, the non-PJM /
# non-ERCOT branch — SPP takes the generic `else` on every one of these).
# Transcribed from source and reconciled against it by test, NOT from memory.
# Quoted here only to SIZE the lever: importing it into an SPP solve would
# carry ERCOT/PJM's fitted lineage across an ISO boundary (rule 25
# [R-ISO-SCOPE]), which this probe does NOT propose.
GENERIC = {
    "CC_REGULAR": {"committed": 0.92, "econlo": 1.06, "econhi": 1.27, "peak": 2.25},
    "CC_CHP": {"committed": 0.92, "econlo": 0.96, "econhi": 1.12, "peak": 2.25},
    "CT_PEAKER": {"committed": 1.55, "econlo": 1.27, "econhi": 1.98, "peak": 13.15},
    "CT_CHP": {"committed": 1.10, "econlo": 1.20, "econhi": 1.20, "peak": 1.40},
    "ST_GAS": {"committed": 0.81, "econlo": 1.05, "econhi": 1.40, "peak": 4.20},
}

# The rule-25-clean alternative: the IDENTITY on every band, which is what
# `_SPP_OFFER_CURVE` already gives SPP's COAL and what `_SOCO_IDENTITY_BANDS`
# gives every SOCO class. It removes the keeper's uniform 7 % discount and
# imports no other ISO's shape — but it is still FLAT, so it adds no slope.
IDENTITY = {
    c: {"committed": 1.0, "econlo": 1.0, "econhi": 1.0, "peak": 1.0}
    for c in ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
}

KEEPER_MULT = 0.93


def _bandkey(b: str) -> str:
    b = str(b)
    if b.startswith("peak"):
        return "peak"
    if b in ("econlo", "econ"):
        return "econlo"
    if b == "econhi":
        return "econhi"
    if b in ("committed", "commitcyc") or b.startswith("sync"):
        return "committed"
    return b


def clear(mc_t, cap_t, target):
    """Marginal cost at ``target`` MW of cumulated capacity, one hour."""
    o = np.argsort(mc_t)
    c = np.cumsum(cap_t[o])
    i = int(np.searchsorted(c, target))
    if i >= len(o):
        return float(mc_t[o[-1]]), True
    return float(mc_t[o[i]]), False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    y = args.year
    bundle = REPO / "results/calibration" / BUNDLES[y]

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from scripts.run_calibration_full import _coal_supply_class, _tranche_band

    state, _ = reconstruct_bundle_fleet(bundle, y, verbose=False)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], float)
    fuel = np.asarray(state["fuel_prices"], float)
    if fuel.ndim == 1:
        fuel = fuel[:, None]
    if fuel.shape[1] == 1:
        fuel = np.broadcast_to(fuel, mc.shape)
    pmax = np.asarray(fa.pmax, float)
    hr = np.asarray(fa.heat_rate, float)
    vom = np.asarray(fa.vom, float)
    avail = np.asarray(fa.availability, float)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], mc.shape)

    groups, codes = fa.plant_group, np.asarray(fa.plant_code)
    klass = [
        _coal_supply_class(int(codes[i]))
        if str(groups[i]) == "COAL"
        else str(groups[i])
        for i in range(len(fa.unit_ids))
    ]
    band = [_bandkey(_tranche_band(str(u))) for u in fa.unit_ids]
    th = np.array([k.startswith(THERMAL_PREFIXES) for k in klass])

    mc, cap = mc[th], (pmax[:, None] * avail)[th]
    fuelT, hrT, vomT = fuel[th], hr[th], vom[th]
    kl = np.array(klass, dtype=object)[th]
    bd = np.array(band, dtype=object)[th]
    T = mc.shape[1]

    # thermal energy the LP actually served, from the committed sidecar
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[
        (ch["pass"] == "P1") & ch["klass"].astype(str).str.startswith(THERMAL_PREFIXES)
    ]
    served = ch.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy()

    sysf = pd.read_parquet(bundle / "hourly" / f"system_{y}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    price = (
        sysf.groupby("hour")
        .apply(
            lambda g: np.average(g["price"], weights=g["demand"]), include_groups=False
        )
        .reindex(range(T))
        .to_numpy()
    )

    base = np.array([clear(mc[:, t], cap[:, t], served[t])[0] for t in range(T)])

    # counterfactual: reprice each (class, band) at another curve's multiplier.
    # the keeper's uniform 0.93 means fuel_term = mc - vom, so the repriced
    # fuel term is fuel_term / 0.93 * m.  Gas classes only — SPP's COAL keeps
    # the keeper's band whatever the arm, so the gas question is isolated.
    fuel_term = hrT[:, None] * fuelT
    other = mc - fuel_term - vomT[:, None]

    def reprice(curve):
        mult = np.full(mc.shape[0], KEEPER_MULT)
        for i in range(mc.shape[0]):
            g = curve.get(str(kl[i]))
            if g:
                mult[i] = g.get(str(bd[i]), KEEPER_MULT)
        return (fuel_term / KEEPER_MULT) * mult[:, None] + vomT[:, None] + other

    arms = {
        "GENERIC curve (gas)": reprice(GENERIC),
        "IDENTITY 1.0 (gas)": reprice(IDENTITY),
    }
    cfs = {
        nm: np.array([clear(m[:, t], cap[:, t], served[t])[0] for t in range(T)])
        for nm, m in arms.items()
    }
    cf = cfs["GENERIC curve (gas)"]

    def q(a):
        return dict(
            mean=float(np.mean(a)),
            p05=float(np.percentile(a, 5)),
            p50=float(np.percentile(a, 50)),
            p95=float(np.percentile(a, 95)),
            mx=float(np.max(a)),
            h100=int((a > 100).sum()),
            h200=int((a > 200).sum()),
        )

    print(f"\n=== SPP {y} — merit-order reconstruction, {BUNDLES[y]} ===")
    print(
        f"{'series':<34} {'mean':>8} {'p05':>8} {'p50':>8} {'p95':>8} {'max':>9} {'h>100':>6} {'h>200':>6}"
    )
    series = [
        ("committed LP price (P1)", price),
        ("reconstruction, keeper stack", base),
    ]
    series += [(f"reconstruction, {nm}", v) for nm, v in cfs.items()]
    for nm, a in series:
        s = q(a)
        print(
            f"{nm:<34} {s['mean']:>8.2f} {s['p05']:>8.2f} {s['p50']:>8.2f} {s['p95']:>8.2f} "
            f"{s['mx']:>9.2f} {s['h100']:>6} {s['h200']:>6}"
        )
    ok = np.isfinite(price) & np.isfinite(base)
    print(
        f"\nVALIDATION  reconstruction vs committed LP price: "
        f"r={np.corrcoef(price[ok], base[ok])[0, 1]:+.3f}  "
        f"mean err {np.mean(base[ok] - price[ok]):+.2f}  "
        f"MAE {np.mean(np.abs(base[ok] - price[ok])):.2f} $/MWh"
    )
    for nm, v in cfs.items():
        print(
            f"LEVER SIZE  {nm:<22} minus keeper stack: mean {np.mean(v - base):+.2f}, "
            f"p95 {np.percentile(v - base, 95):+.2f}, max {np.max(v - base):+.2f} $/MWh"
        )

    # which (class, band) is marginal in the incumbent
    print(
        "\nMARGINAL BAND CENSUS (incumbent stack) — share of hours each (class, band) sets the price"
    )
    idx = np.array(
        [
            int(
                np.argsort(mc[:, t])[
                    min(
                        int(
                            np.searchsorted(
                                np.cumsum(
                                    np.sort(mc[:, t]) * 0 + cap[np.argsort(mc[:, t]), t]
                                ),
                                served[t],
                            )
                        ),
                        mc.shape[0] - 1,
                    )
                ]
            )
            for t in range(T)
        ]
    )
    lab = pd.Series([f"{kl[i]}/{bd[i]}" for i in idx]).value_counts(normalize=True)
    for k, v in lab.head(8).items():
        print(f"    {k:<28} {100 * v:>5.1f}%")

    if args.out:
        args.out.write_text(
            json.dumps(
                {
                    "year": y,
                    "committed": q(price),
                    "base": q(base),
                    "cf": q(cf),
                    "val_r": float(np.corrcoef(price[ok], base[ok])[0, 1]),
                    "val_mae": float(np.mean(np.abs(base[ok] - price[ok]))),
                    "lever_mean": float(np.mean(cf - base)),
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
