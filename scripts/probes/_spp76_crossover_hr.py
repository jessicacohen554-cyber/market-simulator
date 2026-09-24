"""SPP-76 — does swapping in CAMPD-measured heat rates move the coal/gas crossover? (zero LP)

Pre-registered in ``docs/handoffs/PRECOMMIT-spp-76-crossover-heat-rates-2026-09-24.md``
(pushed at ``27874eb7`` before any number below was read).

Per year, rebuilds the bundle's fleet with no LP (``reconstruct_bundle_fleet``, one
interpreter per year) and:

1. reports, per class (CC_REGULAR / ST_GAS / COAL_PRB / COAL_LIGNITE), the capacity-weighted
   base heat rate the loader assigned (``fleet_arrays.heat_rate`` carries the band multiplier;
   the artifact's ``model_heat_rate_egrid`` is the pre-multiplier base) against the measured
   net operating heat rate from the SPP artifacts written by the existing derives
   (``derive_campd_{cc,gas_st,coal}_heat_rates.py --iso SPP``);
2. computes the class-mean crossover gas price
   ``g* = (c * HR_coal + VOM_coal - VOM_cc) / HR_cc`` with model vs measured HR;
3. re-dispatches, per hour, the thermal energy the LP actually served (committed
   ``class_hourly`` P1) in merit order over ALL thermal rows' ``mc_base`` and
   ``pmax * availability`` — once as built (the proxy's own baseline) and once with every
   covered row's fuel term scaled by ``hr_measured / hr_model`` for its (plant, class).
   ``dcoal = proxy(measured) - proxy(model)``. Proxy fidelity against P1 class energy is
   reported beside it (SPP-70's validated instrument, re-used).

Only rows whose plant carries ``flag == 'ok'`` in the artifact are swapped — exactly the
rows the armed field would reprice. VOM, fuel price and tranche capacity are held.

Usage: ``uv run python scripts/probes/_spp76_crossover_hr.py --year 2022 --hr-dir <dir> --out <json>``
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
    **{y: "hydro5_spp_floor_rung" for y in (2019, 2020, 2021, 2022)},
    **{y: "hydro5_spp_floor_span" for y in (2023, 2024, 2025)},
}
# Hard-stop gas prices (lane brief): a rebuild on any other price is the wrong recipe.
GAS = {
    2019: 2.57,
    2020: 2.03,
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}
THERMAL_PREFIXES = ("COAL", "CC_", "CT_", "ST_")
ARTIFACT_CLASS = {"CC_REGULAR": "cc", "ST_GAS": "gas_st"}  # COAL* -> "coal"
REPORT_CLASSES = ("CC_REGULAR", "ST_GAS", "COAL_PRB", "COAL_LIGNITE", "CT_PEAKER")


def _artifact_key(klass: str) -> str | None:
    """Which measured artifact reprices a row of ``klass`` (None = not covered)."""
    if klass.startswith("COAL"):
        return "coal"
    return ARTIFACT_CLASS.get(klass)


def load_measured(hr_dir: Path, tag: str) -> dict[str, dict[int, tuple[float, float]]]:
    """``{artifact: {plant: (hr_measured_net, hr_model_base)}}`` over ``flag == 'ok'`` rows."""
    out: dict[str, dict[int, tuple[float, float]]] = {}
    for key in ("cc", "gas_st", "coal"):
        df = pd.read_csv(hr_dir / f"{key}_{tag}.csv")
        df = df[df["flag"] == "ok"]
        out[key] = {
            int(r.plant_code): (float(r.heat_rate), float(r.model_heat_rate_egrid))
            for r in df.itertuples()
        }
    return out


def merit_dispatch(mc: np.ndarray, cap: np.ndarray, served: np.ndarray) -> np.ndarray:
    """Per-row annual MWh when each hour's ``served`` MW is stacked in ``mc`` order."""
    n, T = mc.shape
    energy = np.zeros(n)
    for t in range(T):  # probe only, never LP construction ([R-VECTOR] n/a)
        o = np.argsort(mc[:, t], kind="stable")
        c = cap[o, t]
        cum = np.cumsum(c)
        take = np.clip(served[t] - (cum - c), 0.0, c)
        energy[o] += take
    return energy


def main() -> int:
    """Run one year and write its JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--hr-dir", type=Path, required=True)
    ap.add_argument("--tag", default="pooled", help="artifact suffix: pooled | 1922")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    y = args.year
    bundle = REPO / "results/calibration" / BUNDLES[y]

    from scripts.lib.bundle_fleet import bundle_gas_price, reconstruct_bundle_fleet
    from scripts.run_calibration_full import _coal_supply_class

    meta_gas = bundle_gas_price(json.loads((bundle / "meta.json").read_text()), y)
    if abs(meta_gas - GAS[y]) > 0.005:
        raise SystemExit(f"HARD STOP: {y} bundle gas {meta_gas} != brief {GAS[y]}")

    state, _ = reconstruct_bundle_fleet(bundle, y, verbose=False)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], float)
    fuel = np.asarray(state["fuel_prices"], float)
    if fuel.ndim == 1:
        fuel = fuel[:, None]
    fuel = np.broadcast_to(fuel, mc.shape)
    pmax = np.asarray(fa.pmax, float)
    hr = np.asarray(fa.heat_rate, float)
    vom = np.asarray(fa.vom, float)
    avail = np.asarray(fa.availability, float)
    if avail.ndim == 1:
        avail = avail[:, None]
    avail = np.broadcast_to(avail, mc.shape)
    codes = np.asarray(fa.plant_code).astype(int)
    groups = fa.plant_group
    klass = np.array(
        [
            _coal_supply_class(int(codes[i]))
            if str(groups[i]) == "COAL"
            else str(groups[i])
            for i in range(len(fa.unit_ids))
        ],
        dtype=object,
    )
    th = np.array([str(k).startswith(THERMAL_PREFIXES) for k in klass])

    measured = load_measured(args.hr_dir, args.tag)
    ratio = np.ones(len(klass))
    covered = np.zeros(len(klass), bool)
    for i in np.flatnonzero(th):
        key = _artifact_key(str(klass[i]))
        if key and int(codes[i]) in measured[key]:
            m, b = measured[key][int(codes[i])]
            ratio[i], covered[i] = m / b, True

    # ---- 1. heat rates by class (row base HR = fa.heat_rate / band multiplier; the band
    # multiplier is uniform 0.93 in both keeper and rung so class means are reported on
    # fa.heat_rate / 0.93 and cross-checked against the artifact's own model column).
    hr_rows = {}
    for k in REPORT_CLASSES:
        s = th & (klass == k)
        if not s.any():
            continue
        w = pmax[s]
        hr_rows[k] = {
            "pmax_mw": float(w.sum()),
            "covered_mw": float(w[covered[s]].sum()),
            "hr_offer_cw": float(np.average(hr[s], weights=w)),
            "hr_offer_cw_measured": float(np.average(hr[s] * ratio[s], weights=w)),
            "fuel_cw": float(np.average(fuel[s].mean(axis=1), weights=w)),
            "vom_cw": float(np.average(vom[s], weights=w)),
            "mc_cw": float(np.average(mc[s].mean(axis=1), weights=w)),
            "mc_cw_measured": float(
                np.average(
                    (mc[s] + hr[s, None] * fuel[s] * (ratio[s, None] - 1.0)).mean(
                        axis=1
                    ),
                    weights=w,
                )
            ),
        }

    # ---- 2. class-mean crossover gas price (PRB vs CC_REGULAR), on offer HRs (0.93 cancels)
    cc, prb = hr_rows["CC_REGULAR"], hr_rows["COAL_PRB"]

    def gstar(hc, hp):
        """Gas price where mean CC offer = mean PRB offer (fuel held at class means)."""
        return (prb["fuel_cw"] * hp + prb["vom_cw"] - cc["vom_cw"]) / hc

    xover = {
        "model": gstar(cc["hr_offer_cw"], prb["hr_offer_cw"]),
        "measured": gstar(cc["hr_offer_cw_measured"], prb["hr_offer_cw_measured"]),
        "cc_delivered_fuel_cw": cc["fuel_cw"],
    }

    # ---- 3. merit re-dispatch of the served thermal energy
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[
        (ch["pass"] == "P1") & ch["klass"].astype(str).str.startswith(THERMAL_PREFIXES)
    ]
    T = mc.shape[1]
    served = ch.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy()
    p1 = (ch.groupby("klass")["mw"].sum() / 1e6).to_dict()

    idx = np.flatnonzero(th)
    mcT, capT = mc[idx], (pmax[:, None] * avail)[idx]
    mc_meas = mcT + (hr[idx, None] * fuel[idx]) * (ratio[idx, None] - 1.0)
    e0 = merit_dispatch(mcT, capT, served)
    e1 = merit_dispatch(mc_meas, capT, served)
    kl = klass[idx]
    classes = sorted(set(kl.tolist()))
    proxy = {
        k: {
            "p1_twh": float(p1.get(k, 0.0)),
            "proxy_model_twh": float(e0[kl == k].sum() / 1e6),
            "proxy_measured_twh": float(e1[kl == k].sum() / 1e6),
            "delta_twh": float((e1[kl == k].sum() - e0[kl == k].sum()) / 1e6),
        }
        for k in classes
    }

    # SPP-41 ordering metric: share of CC_REGULAR MW (annual mean mc) above the dearest PRB row
    def behind(mcs):
        cm = mcs.mean(axis=1)
        s_cc, s_prb = kl == "CC_REGULAR", kl == "COAL_PRB"
        top = cm[s_prb].max()
        w = capT[s_cc].mean(axis=1)
        return float(w[cm[s_cc] > top].sum() / w.sum())

    out = {
        "year": y,
        "bundle": BUNDLES[y],
        "gas_price": meta_gas,
        "tag": args.tag,
        "heat_rates": hr_rows,
        "crossover_gas_price": xover,
        "cc_share_behind_all_prb": {"model": behind(mcT), "measured": behind(mc_meas)},
        "served_twh": float(served.sum() / 1e6),
        "proxy": proxy,
    }
    args.out.write_text(json.dumps(out, indent=1))
    print(
        json.dumps(
            {
                k: out[k]
                for k in ("year", "crossover_gas_price", "cc_share_behind_all_prb")
            }
        )
    )
    for k in REPORT_CLASSES:
        if k in proxy:
            print(k, proxy[k])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
