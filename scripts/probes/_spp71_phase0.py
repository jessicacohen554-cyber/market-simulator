"""SPP-71 (card R-bc) phase 0 — WHERE DOES THE MODEL'S PRICE-FORMING CURTAILMENT
COME FROM, AND WHAT IS STOPPING IT?  ZERO LP.

The R-bc charter (``FINDING-spp-64`` §9) asks for a reduced-form curtailment that
enters as an LP row "whose dual reaches the zonal price", so that the curtailment
and the negative-price hour are ONE event.  This probe measures the three
quantities that decide whether such a row can exist and what shape it must have,
entirely off keeper 14's COMMITTED bundles plus the committed measured actuals:

* **A. The coal synchronization floor's COVERAGE.**  SPP's keeper already carries
  the only mechanism that can make wind marginal (``coal_mustrun_online_pmin`` +
  ``coal_sync_srmc_tranche``, SPP-51).  ``RESULT-spp-51`` measured its minimum at
  0.15-2.53 % of the class's own annual max against a real PRB fleet at
  8.1-17.5 %.  Re-measured here on keeper 14 (a DIFFERENT run), against the same
  measured EIA-930 SWPP COL series, per year.

* **B. The DISPLACEMENT LADDER.**  Raising a coal floor does not curtail wind
  until every cheaper-to-displace dispatchable MW is gone.  Per hour this reports
  the gas-fleet MW standing between the coal floor and the wind — the buffer any
  supply-side floor must exhaust before the price can reach the wind offer.

* **C. The PRICE FLOOR EVENT COUNT.**  Model hours at exactly the wind offer
  (-26.000) and below zero, on the hub-equivalent construction the C3c benchmark
  uses (``FINDING-spp-29`` §1: ``actual_lmp_hourly_SPP.rt`` equals the two-hub
  mean to 6.1e-05 $/MWh), against the measured actual.

Alignment note (brief trap (e)): the model is a flat 8760 and EIA-930 carries
8784 in a leap year.  Every statistic here is an ORDER statistic or an annual
COUNT over the year, never an hour-wise join, so no fixed-CST re-indexing is
performed and none is needed.  Trap (f): the one corrupt 3,589,445 MWh SWPP WND
hour in 2023 is guarded by a physical ceiling on every fuel series read.
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

COAL_CLASSES = ("COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC")
# The dispatchable fleet that sits between the coal floor and the wind: every
# gas/oil class the LP can back down.  CHP is included because its grid tranche
# is dispatchable in this LP; it is reported separately so the buffer can be
# read with and without it.
GAS_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")
OTHER_DISPATCH = ("oil",)
# The wind offer the LP applies flat to the whole SPP fleet (= -ira_ptc_wind).
WIND_OFFER = -26.0
# Physical ceiling used only to reject the known-corrupt SWPP hour (trap (f)):
# SPP's all-time peak demand is ~53 GW, so no single fuel hour can exceed this.
FUEL_MWH_CEILING = 100_000.0


def _bundle_hourly(year: int, name: str) -> pd.DataFrame:
    path = (
        REPO
        / "results"
        / "calibration"
        / BUNDLES[year]
        / "hourly"
        / f"{name}_{year}.parquet"
    )
    return pd.read_parquet(path)


def _measured_fuel(year: int, fuel: str) -> np.ndarray:
    """Measured EIA-930 SWPP hourly MWh for one fuel type, corrupt hours dropped."""
    f = pd.read_parquet(REPO / "data" / "raw" / "SWPP_fueltype.parquet")
    f = f[(f["fueltype"] == fuel) & (f["period"].dt.year == year)]
    v = pd.to_numeric(f["value_mwh"], errors="coerce").to_numpy(dtype=float)
    v = v[np.isfinite(v)]
    return v[v < FUEL_MWH_CEILING]


def _stats(v: np.ndarray) -> dict:
    if v.size == 0:
        return {}
    mx = float(np.max(v))
    return {
        "n": int(v.size),
        "min": float(np.min(v)),
        "p01": float(np.percentile(v, 1)),
        "p05": float(np.percentile(v, 5)),
        "median": float(np.median(v)),
        "max": mx,
        "min_over_max": float(np.min(v) / mx) if mx > 0 else float("nan"),
        "p01_over_max": float(np.percentile(v, 1) / mx) if mx > 0 else float("nan"),
        "p05_over_max": float(np.percentile(v, 5) / mx) if mx > 0 else float("nan"),
    }


def year_report(year: int) -> dict:
    ch = _bundle_hourly(year, "class_hourly")
    ch = ch[ch["pass"] == "P1"]
    piv = ch.pivot_table(
        index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
    )
    piv = piv.fillna(0.0)

    def col(*names: str) -> np.ndarray:
        out = np.zeros(len(piv), dtype=float)
        for n in names:
            if n in piv.columns:
                out += piv[n].to_numpy(dtype=float)
        return out

    coal = col(*COAL_CLASSES)
    gas = col(*GAS_CLASSES)
    chp = col(*CHP_CLASSES)
    other = col(*OTHER_DISPATCH)
    wind = col("wind")
    solar = col("solar")
    demand_sys = _bundle_hourly(year, "system")
    demand_sys = demand_sys[demand_sys["pass"] == "P1"]

    # --- A. the floor as PLACED (coal mustrun + sync bands) -------------------
    cb = _bundle_hourly(year, "class_band_hourly")
    cb = cb[(cb["pass"] == "P1") & (cb["klass"].isin(COAL_CLASSES))]
    floor_bands = cb[cb["band"].isin(("mustrun", "sync"))]
    placed = (
        floor_bands.groupby("hour", observed=True)["mw"]
        .sum()
        .reindex(piv.index, fill_value=0.0)
    ).to_numpy(dtype=float)

    # --- C. price, on the hub-equivalent (two-zone mean) construction ---------
    pz = demand_sys.pivot_table(
        index="hour", columns="zone", values="price", observed=True
    )
    hub = pz.mean(axis=1).to_numpy(dtype=float)
    zone_min = pz.min(axis=1).to_numpy(dtype=float)
    act = pd.read_parquet(
        REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_SPP.parquet"
    )
    act = act[act["year"] == year]
    art = pd.to_numeric(act["rt"], errors="coerce").dropna().to_numpy(dtype=float)

    # --- B. the displacement ladder ------------------------------------------
    net_load = (
        demand_sys.groupby("hour", observed=True)["demand"].sum().to_numpy(dtype=float)
    )
    net_load = net_load - wind - solar
    order = np.argsort(net_load, kind="stable")
    buckets = {}
    for label, k in (("lowest_100", 100), ("lowest_500", 500), ("lowest_1000", 1000)):
        idx = order[:k]
        buckets[label] = {
            "gas_mean_mw": float(np.mean(gas[idx])),
            "gas_p50_mw": float(np.median(gas[idx])),
            "gas_min_mw": float(np.min(gas[idx])),
            "chp_mean_mw": float(np.mean(chp[idx])),
            "oil_mean_mw": float(np.mean(other[idx])),
            "coal_mean_mw": float(np.mean(coal[idx])),
            "coal_floor_placed_mean_mw": float(np.mean(placed[idx])),
            "hub_price_mean": float(np.mean(hub[idx])),
            "hours_at_wind_offer": int(
                np.sum(np.isclose(zone_min, WIND_OFFER, atol=1e-6)[idx])
            ),
        }

    measured_coal = _measured_fuel(year, "COL")
    measured_wind = _measured_fuel(year, "WND")

    return {
        "year": year,
        "bundle": BUNDLES[year],
        "A_coal_floor_coverage": {
            "model_coal_class_mw": _stats(coal),
            "model_coal_floor_placed_mw": _stats(placed),
            "measured_eia930_COL_mwh": _stats(measured_coal),
            "model_floor_zero_hours": int(np.sum(placed <= 1e-6)),
        },
        "B_displacement_ladder": buckets,
        "C_price": {
            "model_hub_negative_hours": int(np.sum(hub < 0.0)),
            "model_hub_min": float(np.min(hub)),
            "model_anyzone_at_wind_offer_hours": int(
                np.sum(np.isclose(zone_min, WIND_OFFER, atol=1e-6))
            ),
            "model_anyzone_negative_hours": int(np.sum(zone_min < 0.0)),
            "model_zone_min_price": float(np.min(zone_min)),
            "actual_rt_negative_hours": int(np.sum(art < 0.0)),
            "actual_rt_min": float(np.min(art)) if art.size else float("nan"),
        },
        "D_volume_twh": {
            "model_wind": float(wind.sum() / 1e6),
            "measured_wind": float(measured_wind.sum() / 1e6),
            "model_coal": float(coal.sum() / 1e6),
            "measured_coal": float(measured_coal.sum() / 1e6),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=sorted(BUNDLES))
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    rows = [year_report(y) for y in args.years]

    print(
        "\n=== A. COAL FLOOR COVERAGE — model class MW vs the placed floor vs measured ==="
    )
    hdr = f"{'yr':>5} {'coal min':>9} {'coal p01':>9} {'coal max':>9} {'min/max':>8} {'p01/max':>8} | {'floor min':>9} {'floor max':>9} {'floor=0 h':>9} | {'meas min/max':>12} {'meas p01/max':>12}"
    print(hdr)
    for r in rows:
        a = r["A_coal_floor_coverage"]
        c, f, m = (
            a["model_coal_class_mw"],
            a["model_coal_floor_placed_mw"],
            a["measured_eia930_COL_mwh"],
        )
        print(
            f"{r['year']:>5} {c['min']:>9.1f} {c['p01']:>9.1f} {c['max']:>9.1f} "
            f"{c['min_over_max']:>8.4f} {c['p01_over_max']:>8.4f} | "
            f"{f['min']:>9.1f} {f['max']:>9.1f} {a['model_floor_zero_hours']:>9d} | "
            f"{m['min_over_max']:>12.4f} {m['p01_over_max']:>12.4f}"
        )

    print(
        "\n=== B. DISPLACEMENT LADDER — MW standing between the coal floor and the wind ==="
    )
    print(
        f"{'yr':>5} {'bucket':>12} {'gas mean':>9} {'gas p50':>9} {'gas min':>9} {'chp':>7} {'oil':>6} {'coal':>9} {'floor':>9} {'hub $':>8} {'@offer h':>9}"
    )
    for r in rows:
        for label, b in r["B_displacement_ladder"].items():
            print(
                f"{r['year']:>5} {label:>12} {b['gas_mean_mw']:>9.1f} {b['gas_p50_mw']:>9.1f} "
                f"{b['gas_min_mw']:>9.1f} {b['chp_mean_mw']:>7.1f} {b['oil_mean_mw']:>6.1f} "
                f"{b['coal_mean_mw']:>9.1f} {b['coal_floor_placed_mean_mw']:>9.1f} "
                f"{b['hub_price_mean']:>8.2f} {b['hours_at_wind_offer']:>9d}"
            )

    print("\n=== C. PRICE FLOOR EVENTS ===")
    print(
        f"{'yr':>5} {'hub neg h':>10} {'hub min':>9} {'zone@-26 h':>11} {'zone neg h':>11} {'zone min':>9} | {'actual neg h':>13} {'actual min':>11}"
    )
    for r in rows:
        c = r["C_price"]
        print(
            f"{r['year']:>5} {c['model_hub_negative_hours']:>10d} {c['model_hub_min']:>9.2f} "
            f"{c['model_anyzone_at_wind_offer_hours']:>11d} {c['model_anyzone_negative_hours']:>11d} "
            f"{c['model_zone_min_price']:>9.3f} | {c['actual_rt_negative_hours']:>13d} {c['actual_rt_min']:>11.2f}"
        )

    print("\n=== D. VOLUME (TWh) ===")
    print(
        f"{'yr':>5} {'wind model':>11} {'wind meas':>10} {'wind d':>8} {'coal model':>11} {'coal meas':>10} {'coal d':>8}"
    )
    for r in rows:
        d = r["D_volume_twh"]
        print(
            f"{r['year']:>5} {d['model_wind']:>11.3f} {d['measured_wind']:>10.3f} "
            f"{d['model_wind'] - d['measured_wind']:>8.3f} {d['model_coal']:>11.3f} "
            f"{d['measured_coal']:>10.3f} {d['model_coal'] - d['measured_coal']:>8.3f}"
        )

    if args.json_out:
        args.json_out.write_text(json.dumps(rows, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
