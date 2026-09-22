"""SPP-71 — difference the ENSEMBLE coal synchronization floor against its own
same-HEAD control, per year, and score the PRE-REGISTERED predictions.

ZERO LP.  Reads only the two committed per-year bundles each shard pushed
(``spp71_<year>_ctl`` and ``spp71_<year>_arm``) plus the committed measured
actuals, so it can be re-run by anyone from git alone.

Both legs were solved in ONE shard container at ONE pinned HEAD
(6edc996d1051296b6fb62185df7b304adbc7f3d1) with a single ``--set``, so the
differencing is exact by construction and rule 29(b) form 4 is not relied on.

The pre-registered predictions and the five kill limbs are
``docs/handoffs/PRECOMMIT-spp-71-ensemble-sync-floor-2026-09-22.md`` §5-§6.
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

from scripts.probes._spp71_phase0 import (  # noqa: E402
    COAL_CLASSES,
    FUEL_MWH_CEILING,
    WIND_OFFER,
)

CAL = REPO / "results" / "calibration"

# Pre-registered per-year predictions (PRECOMMIT §5.1), so the RESULT scores
# itself rather than being graded after the fact.
PREREG = {
    #        hours@offer ctl -> predicted,  wind TWh removed, coal TWh added, dmean $
    2019: {"offer": (0, 9), "wind": 0.005, "coal": 0.006, "dmean": -0.03},
    2020: {"offer": (169, 254), "wind": 0.129, "coal": 0.197, "dmean": -0.29},
    2021: {"offer": (505, 566), "wind": 0.237, "coal": 0.269, "dmean": -0.22},
    2022: {"offer": (511, 572), "wind": 0.269, "coal": 0.303, "dmean": -0.22},
    2023: {"offer": (393, 439), "wind": 0.119, "coal": 0.154, "dmean": -0.16},
    2024: {"offer": (461, 517), "wind": 0.196, "coal": 0.265, "dmean": -0.20},
    2025: {"offer": (435, 491), "wind": 0.202, "coal": 0.255, "dmean": -0.18},
}
ACTUAL_NEG = {
    2019: 547,
    2020: 936,
    2021: 1108,
    2022: 995,
    2023: 992,
    2024: 1172,
    2025: 1018,
}


def _hourly(bundle: Path, name: str, year: int) -> pd.DataFrame:
    return pd.read_parquet(bundle / "hourly" / f"{name}_{year}.parquet")


def leg(bundle: Path, year: int) -> dict:
    ch = _hourly(bundle, "class_hourly", year)
    ch = ch[ch["pass"] == "P1"]
    piv = ch.pivot_table(
        index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
    ).fillna(0.0)

    def col(*names: str) -> np.ndarray:
        o = np.zeros(len(piv))
        for n in names:
            if n in piv.columns:
                o += piv[n].to_numpy(dtype=float)
        return o

    coal = col(*COAL_CLASSES)
    sy = _hourly(bundle, "system", year)
    sy = sy[sy["pass"] == "P1"]
    pz = sy.pivot_table(index="hour", columns="zone", values="price", observed=True)
    dz = sy.pivot_table(index="hour", columns="zone", values="demand", observed=True)
    P = pz.to_numpy(dtype=float)
    W = dz.to_numpy(dtype=float)
    W = W / W.sum(axis=1, keepdims=True)
    lw = (P * W).sum(axis=1)
    zmin = P.min(axis=1)
    spread = np.abs(P[:, 0] - P[:, 1]) if P.shape[1] == 2 else np.zeros(len(P))

    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    return {
        "twh": {k: float(piv[k].sum() / 1e6) for k in piv.columns},
        "coal_mw": coal,
        "price_lw": lw,
        "zone_min": zmin,
        "spread": spread,
        "slack": float(sy["slack"].sum()),
        "dump": float(sy["dump"].sum()),
        "ensemble": cfg.get("coal_sync_ensemble_level"),
        "cfg": cfg,
    }


def measured_coal_min(year: int) -> float:
    f = pd.read_parquet(REPO / "data" / "raw" / "SWPP_fueltype.parquet")
    f = f[(f["fueltype"] == "COL") & (f["period"].dt.year == year)]
    v = pd.to_numeric(f["value_mwh"], errors="coerce").to_numpy(dtype=float)
    v = v[np.isfinite(v)]
    v = v[v < FUEL_MWH_CEILING]
    return float(v.min()) if v.size else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    rows = []
    for y in args.years:
        c = leg(CAL / f"spp71_{y}_ctl", y)
        a = leg(CAL / f"spp71_{y}_arm", y)
        assert c["ensemble"] in (False, None), (
            f"{y}: control has ensemble={c['ensemble']}"
        )
        assert a["ensemble"] is True, f"{y}: arm has ensemble={a['ensemble']}"
        diff_keys = [
            k
            for k in set(c["cfg"]) | set(a["cfg"])
            if c["cfg"].get(k) != a["cfg"].get(k)
        ]
        off_c = int(np.isclose(c["zone_min"], WIND_OFFER, atol=1e-6).sum())
        off_a = int(np.isclose(a["zone_min"], WIND_OFFER, atol=1e-6).sum())
        rows.append(
            {
                "year": y,
                "single_delta": sorted(diff_keys),
                "coal_min_ctl": float(c["coal_mw"].min()),
                "coal_min_arm": float(a["coal_mw"].min()),
                "coal_p01_ctl": float(np.percentile(c["coal_mw"], 1)),
                "coal_p01_arm": float(np.percentile(a["coal_mw"], 1)),
                "coal_max_arm": float(a["coal_mw"].max()),
                "measured_coal_min": measured_coal_min(y),
                "offer_ctl": off_c,
                "offer_arm": off_a,
                "offer_pred": PREREG[y]["offer"][1],
                "actual_neg": ACTUAL_NEG[y],
                "neg_ctl": int((c["zone_min"] < 0).sum()),
                "neg_arm": int((a["zone_min"] < 0).sum()),
                "wind_ctl": c["twh"].get("wind", 0.0),
                "wind_arm": a["twh"].get("wind", 0.0),
                "wind_pred": -PREREG[y]["wind"],
                "coal_twh_ctl": sum(c["twh"].get(k, 0.0) for k in COAL_CLASSES),
                "coal_twh_arm": sum(a["twh"].get(k, 0.0) for k in COAL_CLASSES),
                "coal_pred": PREREG[y]["coal"],
                "mean_ctl": float(c["price_lw"].mean()),
                "mean_arm": float(a["price_lw"].mean()),
                "dmean_pred": PREREG[y]["dmean"],
                "cv_ctl": float(c["price_lw"].std() / abs(c["price_lw"].mean())),
                "cv_arm": float(a["price_lw"].std() / abs(a["price_lw"].mean())),
                "spread_ctl": float(c["spread"].mean()),
                "spread_arm": float(a["spread"].mean()),
                "slack_ctl": c["slack"],
                "slack_arm": a["slack"],
                "dump_ctl": c["dump"],
                "dump_arm": a["dump"],
                "twh_ctl": c["twh"],
                "twh_arm": a["twh"],
            }
        )

    print("\n=== SINGLE-DELTA CHECK (hard stop 3) ===")
    for r in rows:
        print(f"{r['year']}: differing scenario_config keys = {r['single_delta']}")

    print("\n=== P-0 THE STRUCTURAL LEG — fleet coal floor at the bottom ===")
    print(
        f"{'yr':>5} {'coal min ctl':>12} {'coal min arm':>12} {'measured min':>12} {'ctl/meas':>9} {'arm/meas':>9} | {'K-1 (arm<=meas)':>16}"
    )
    for r in rows:
        k1 = "PASS" if r["coal_min_arm"] <= r["measured_coal_min"] else "FAIL"
        print(
            f"{r['year']:>5} {r['coal_min_ctl']:>12.1f} {r['coal_min_arm']:>12.1f} "
            f"{r['measured_coal_min']:>12.1f} {r['coal_min_ctl'] / r['measured_coal_min']:>9.3f} "
            f"{r['coal_min_arm'] / r['measured_coal_min']:>9.3f} | {k1:>16}"
        )

    print("\n=== P-1 PRICE LEG — hours at the wind offer (-26.000) ===")
    print(
        f"{'yr':>5} {'ctl':>6} {'arm':>6} {'delta':>7} {'predicted':>10} {'actual neg':>11} {'gap closed':>11}"
    )
    for r in rows:
        closed = (r["offer_arm"] - r["offer_ctl"]) / max(
            1, r["actual_neg"] - r["offer_ctl"]
        )
        print(
            f"{r['year']:>5} {r['offer_ctl']:>6d} {r['offer_arm']:>6d} "
            f"{r['offer_arm'] - r['offer_ctl']:>+7d} {r['offer_pred']:>10d} "
            f"{r['actual_neg']:>11d} {100 * closed:>10.1f}%"
        )

    print("\n=== P-2 / P-5 VOLUME ===")
    print(
        f"{'yr':>5} {'wind ctl':>9} {'wind arm':>9} {'d wind':>8} {'pred':>7} | {'coal ctl':>9} {'coal arm':>9} {'d coal':>8} {'pred':>7}"
    )
    for r in rows:
        print(
            f"{r['year']:>5} {r['wind_ctl']:>9.3f} {r['wind_arm']:>9.3f} "
            f"{r['wind_arm'] - r['wind_ctl']:>+8.3f} {r['wind_pred']:>+7.3f} | "
            f"{r['coal_twh_ctl']:>9.3f} {r['coal_twh_arm']:>9.3f} "
            f"{r['coal_twh_arm'] - r['coal_twh_ctl']:>+8.3f} {r['coal_pred']:>+7.3f}"
        )

    print("\n=== P-3 PRICE LEVEL AND SHAPE, P-4 CONGESTION RENT ===")
    print(
        f"{'yr':>5} {'mean ctl':>9} {'mean arm':>9} {'d mean':>8} {'pred':>7} | {'cv ctl':>7} {'cv arm':>7} | {'spread ctl':>11} {'spread arm':>11}"
    )
    for r in rows:
        print(
            f"{r['year']:>5} {r['mean_ctl']:>9.3f} {r['mean_arm']:>9.3f} "
            f"{r['mean_arm'] - r['mean_ctl']:>+8.3f} {r['dmean_pred']:>+7.2f} | "
            f"{r['cv_ctl']:>7.3f} {r['cv_arm']:>7.3f} | "
            f"{r['spread_ctl']:>11.3f} {r['spread_arm']:>11.3f}"
        )

    print("\n=== SLACK / DUMP (protective) ===")
    for r in rows:
        print(
            f"{r['year']}: slack {r['slack_ctl']:.1f} -> {r['slack_arm']:.1f} MWh | "
            f"dump {r['dump_ctl']:.1f} -> {r['dump_arm']:.1f} MWh"
        )

    print("\n=== PER-CLASS TWh DELTA ===")
    classes = sorted({k for r in rows for k in r["twh_ctl"]})
    print(f"{'class':>14} " + " ".join(f"{r['year']:>9}" for r in rows))
    for k in classes:
        print(
            f"{k:>14} "
            + " ".join(
                f"{r['twh_arm'].get(k, 0.0) - r['twh_ctl'].get(k, 0.0):>+9.3f}"
                for r in rows
            )
        )

    if args.json_out:
        args.json_out.write_text(json.dumps(rows, indent=1, default=float))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
