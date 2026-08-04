"""nyiso-122 — is the WINTER half of C3a-2025 a FUEL-LEVEL miss or a CONGESTION miss?

Phase 0 (``_nyiso122_c3a_2025_decomp.py``) split NYISO's 2025 C3a gap into a
summer half that is entirely the >$300 scarcity tail (C3c's object) and a winter
half (Jan+Feb, the $100-300 band) that is NOT the tail.  The pre-registration
proposed to test the winter half with ``nyiso_iroquois_winter_spread``, a monthly
gas-basis reallocation.

This probe is the ex-ante attribution that decides whether that arm can reach the
defect AT ALL, and it is run BEFORE the solve rather than after it.  A fuel-level
miss and a congestion miss have different signatures:

  * **fuel-level** -- every zone misses by a similar amount, because they all
    price off the same (mis-stated) marginal fuel;
  * **congestion** -- the model collapses several zones onto ONE price while the
    actual market shows a wide zonal spread, so the miss is concentrated in the
    import-constrained downstate zones and near zero upstate.

The two are distinguished here by measuring, in the target hours, (a) the model's
cross-zone price spread against the actual's, and (b) the per-zone gap.

Reads only committed artifacts: the keeper bundle's ``hourly/`` sidecars (rule 15)
and the committed per-zone monthly actuals in
``data/raw/_validation-source/actual_lmp.json``.  No LP, no derive, no solve.

Rule 22: training years only; ``YEARS`` is a hard filter.

Outputs ``results/calibration/_nyiso122_winter_zonal_spread.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS: tuple[int, ...] = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]
HOURS = 8760
# The five model load zones.  NYISO_external is the import node, not a load zone,
# and carries no benchmarked actual, so it is excluded from every spread here.
ZONES = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island")
WINTER = (1, 2)  # the months phase 0 localizes the non-tail miss to

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/nyiso120_c119_scopegate"
ACTUAL_JSON = REPO / "data/raw/_validation-source/actual_lmp.json"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
OUT = REPO / "results/calibration/_nyiso122_winter_zonal_spread.json"


def _model(year: int) -> pd.DataFrame:
    """P1 zonal price/demand frame for ``year``, indexed hour x zone."""
    df = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    if df["pass"].nunique() > 1:
        df = df[df["pass"] == df["pass"].max()]
    return df[df["zone"].isin(ZONES)]


def _actual_zonal_monthly(year: int) -> dict[str, list[float]]:
    """Committed per-zone monthly actual RT LMP for ``year``."""
    if year not in YEARS:
        raise SystemExit(f"REFUSED: {year} is out-of-training for NYISO (rule 22)")
    z = json.loads(ACTUAL_JSON.read_text())["NYISO"][str(year)]["zones"]
    return {k: z[k]["rt_mon"] for k in ZONES if k in z}


def measure(year: int) -> dict:
    """Zonal-spread vs level attribution for ``year``'s winter months."""
    m = _model(year)
    idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    m = m.assign(mo=idx.month.values[m["hour"].to_numpy() % HOURS])
    act = _actual_zonal_monthly(year)

    price = m.pivot_table(index="hour", columns="zone", values="price")
    dem = m.pivot_table(index="hour", columns="zone", values="demand")
    total_load = float(dem.to_numpy().sum())

    # ---- per-zone winter gap and its load-weighted contribution -------------
    zrows = []
    for z in ZONES:
        if z not in act:
            continue
        sub = m[m["zone"] == z]
        mm = sub.groupby("mo")["price"].mean().reindex(range(1, 13)).to_numpy()
        wm = sub.groupby("mo")["demand"].sum().reindex(range(1, 13)).to_numpy()
        am = np.array(act[z], dtype=float)
        contrib = float(sum(wm[k - 1] * (mm[k - 1] - am[k - 1]) for k in WINTER)) / total_load
        zrows.append(
            {
                "zone": z,
                "load_share_pct": round(100 * float(sub["demand"].sum()) / total_load, 2),
                "winter_model": [round(float(mm[k - 1]), 2) for k in WINTER],
                "winter_actual": [round(float(am[k - 1]), 2) for k in WINTER],
                "winter_gap": [round(float(mm[k - 1] - am[k - 1]), 2) for k in WINTER],
                "winter_contrib_usd_mwh": round(contrib, 3),
            }
        )

    # ---- THE DISCRIMINATOR: cross-zone spread, model vs actual -------------
    # A fuel-level miss preserves the zonal spread and shifts every zone; a
    # congestion miss collapses the model's spread while the actual's stays wide.
    winter_hours = m[m["mo"].isin(WINTER)]["hour"].unique()
    pw = price.loc[price.index.isin(winter_hours), list(ZONES)]
    mainland = [z for z in ZONES if z != "Long_Island"]
    spread_model = (pw[list(ZONES)].max(axis=1) - pw[list(ZONES)].min(axis=1)).to_numpy()
    spread_main = (pw[mainland].max(axis=1) - pw[mainland].min(axis=1)).to_numpy()
    am_mat = np.array([act[z] for z in ZONES if z in act], dtype=float)
    spread_actual_mon = [
        round(float(am_mat[:, k - 1].max() - am_mat[:, k - 1].min()), 2) for k in WINTER
    ]

    return {
        "year": year,
        "months": list(WINTER),
        "zones": zrows,
        "winter_gap_total_usd_mwh": round(sum(r["winter_contrib_usd_mwh"] for r in zrows), 3),
        "spread": {
            "model_all5_mean": round(float(np.nanmean(spread_model)), 3),
            "model_all5_median": round(float(np.nanmedian(spread_model)), 3),
            "model_mainland4_mean": round(float(np.nanmean(spread_main)), 3),
            "model_mainland4_median": round(float(np.nanmedian(spread_main)), 3),
            # share of winter hours in which the four mainland zones price
            # IDENTICALLY -- i.e. no internal constraint binds anywhere
            "mainland4_collapsed_pct": round(
                100 * float(np.mean(spread_main < 0.01)), 2
            ),
            "actual_all5_monthly": spread_actual_mon,
        },
    }


def main() -> None:
    res = {
        "probe": "nyiso-122 winter zonal-spread attribution (no LP)",
        "keeper": "2026-08-04-nyiso-120-c119-scope",
        "question": "is the Jan+Feb C3a miss a FUEL-LEVEL miss or a CONGESTION miss?",
        "years": list(YEARS),
        "results": [measure(y) for y in YEARS],
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    for r in res["results"]:
        print(f"=== {r['year']}  Jan+Feb total gap {r['winter_gap_total_usd_mwh']:+.3f} $/MWh")
        print(
            f"  {'zone':<16}{'load%':>7}{'Jan mod':>9}{'Jan act':>9}{'Feb mod':>9}"
            f"{'Feb act':>9}{'contrib':>10}"
        )
        for z in r["zones"]:
            print(
                f"  {z['zone']:<16}{z['load_share_pct']:7.1f}"
                f"{z['winter_model'][0]:9.2f}{z['winter_actual'][0]:9.2f}"
                f"{z['winter_model'][1]:9.2f}{z['winter_actual'][1]:9.2f}"
                f"{z['winter_contrib_usd_mwh']:+10.3f}"
            )
        s = r["spread"]
        print(
            f"  SPREAD  model all-5 mean {s['model_all5_mean']:.2f} / median "
            f"{s['model_all5_median']:.2f} | mainland-4 mean {s['model_mainland4_mean']:.2f}"
            f" / median {s['model_mainland4_median']:.2f}"
        )
        print(
            f"          mainland-4 COLLAPSED to one price in "
            f"{s['mainland4_collapsed_pct']:.1f}% of winter hours"
            f" | ACTUAL all-5 monthly spread {s['actual_all5_monthly']}"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
