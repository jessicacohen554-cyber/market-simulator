"""ercot-177: anatomy of the C3a-2023 underrun on the current ERCOT keeper.

Reads ONLY committed artifacts — the keeper bundle's `hourly/` sidecars (rule 15),
the committed actual-LMP series, and ERCOT's published ORDC/reserve series. **No
solve, no replay.**  Answers one question: *where, in hours and in dollars, does
the −32.4 % C3a-2023 miss actually live, and which price component owns it?*

Headline (see ``docs/DIAGNOSIS-ercot177-c3a2023-anatomy-2026-08-07.md``):

* **August + September carry 81.3 %** of the annual load-weighted $-gap; every
  non-summer month is within a few $/MWh and the overnight body is slightly
  OVER-priced.
* Inside Aug–Sep the **top 50 hours carry 80.6 %** of the gap and the top 100
  carry 103 % (>100 % because the model over-prices elsewhere).
* On those 50 hours the model's **scarcity adder is RIGHT** — model $107.92 vs
  ERCOT's own published RTORPA+RTORDPA $104.82 — and the **reserve level is
  right** (model 5,902 MW held vs ERCOT PRC 5,471 MW). **100.2 % of the miss is
  in the ENERGY STACK**: ERCOT's own SCED `system_lambda` averaged **$1,889.63**
  on those hours against the model's energy-only **$360.23**.
* The offer surface's top conditioning bin is the dilution:
  ``ercot_offer_surface_netload_pcts = [0.8, 0.9, 0.97]`` puts **263 hours**
  spanning actual **$198 (p50) → $5,046 (max)** under ONE measured ladder, while
  the tail population (actual > $200) is only the top **2.07 %** of the year.

Usage::

    python scripts/probes/ercot177_c3a2023_anatomy.py [--bundle DIR] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

#: Committed inputs. All three are artifacts of record — none is regenerated here.
DEFAULT_BUNDLE = REPO / "results/calibration/ercot176_control_A"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
ORDC_SERIES = REPO / "data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"

#: ERCOT 2023 actual RT load-weighted monthly means, from the committed
#: benchmark ``frontend/data/backcast/bench/ERCOT/2023.json.gz`` (`rt_lw_mon`).
ACTUAL_RT_LW_MON: tuple[float, ...] = (
    26.39,
    21.86,
    30.28,
    23.86,
    32.23,
    74.55,
    48.38,
    220.61,
    109.75,
    31.70,
    31.28,
    23.18,
)
ACTUAL_RT_LW_ANNUAL: float = 64.32

#: The summer months that carry the object.
SUMMER: tuple[int, ...] = (8, 9)

#: The keeper's own conditioning breakpoints (``ercot_offer_surface_netload_pcts``).
NETLOAD_PCTS: tuple[float, ...] = (0.0, 0.8, 0.9, 0.97, 1.0)

#: The C3c tail threshold, which defines the "tail population" the surface must price.
TAIL_THRESHOLD: float = 200.0


def _load(bundle: Path, year: int) -> pd.DataFrame:
    """Return an hourly frame joining model, actuals and ERCOT's published series."""
    sys_ = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    p1 = sys_[sys_["pass"] == "P1"]
    g = (
        p1.groupby("hour")
        .apply(
            lambda d: pd.Series(
                {
                    "mod": np.average(d["price"], weights=d["demand"]),
                    "load": d["demand"].sum(),
                    "ordc": d["ordc_adder"].max(),
                    "rtord": d["rtordpa_overlay"].max(),
                    "slack": d["slack"].sum(),
                }
            ),
            include_groups=False,
        )
        .sort_index()
    )
    act = pd.read_parquet(ACTUAL_LMP)
    act = act[act["year"] == year].sort_values("hour").reset_index(drop=True)
    n = min(len(g), len(act))
    g = g.iloc[:n].copy()
    g["act"] = act["rt"].to_numpy()[:n]

    meas = pd.read_parquet(str(ORDC_SERIES).format(year=year))
    meas = meas.sort_values("hour").reset_index(drop=True)
    for col in ("prc", "rtolcap", "rtorpa", "rtordpa", "system_lambda"):
        g[col] = meas[col].to_numpy()[:n]

    rf = pd.read_parquet(bundle / f"hourly/reserve_family_{year}.parquet")
    rf = rf[(rf["pass"] == "P1") & (rf["family"] == "ercot_ordc_total")].set_index(
        "hour"
    )
    g["held"] = rf["held_mw"].reindex(g.index).to_numpy()
    g["ordc_dual"] = rf["dual"].reindex(g.index).to_numpy()

    ch = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    for klass in ("wind", "solar"):
        srs = ch[ch["klass"] == klass].set_index("hour")["mw"]
        g[klass] = srs.reindex(g.index).fillna(0.0).to_numpy()
    g["netload"] = g["load"] - g["wind"] - g["solar"]

    clock = pd.date_range(f"{year}-01-01", periods=n, freq="h")
    g["mon"] = clock.month
    g["hod"] = clock.hour
    return g


def _monthly(g: pd.DataFrame) -> dict:
    """Load-weighted model vs actual by month, and each month's share of the $-gap."""
    rows, total = [], 0.0
    for m in range(1, 13):
        d = g[g["mon"] == m]
        mod = float(np.average(d["mod"], weights=d["load"]))
        gap = (ACTUAL_RT_LW_MON[m - 1] - mod) * float(d["load"].sum())
        rows.append(
            {
                "month": m,
                "model_lw": mod,
                "actual_lw": ACTUAL_RT_LW_MON[m - 1],
                "gap_dollars": gap,
            }
        )
        total += gap
    for r in rows:
        r["share_of_annual_gap"] = r["gap_dollars"] / total
    return {"months": rows, "total_gap_dollars": total}


def _component_split(top: pd.DataFrame) -> dict:
    """Split the miss into an ENERGY-STACK term and a SCARCITY-ADDER term.

    ERCOT's published RT price decomposes as ``system_lambda + RTORPA + RTORDPA``;
    the model's as ``price = energy_only + ordc_adder + rtordpa_overlay``.  Both
    sides are therefore compared component-for-component on the same basis.
    """
    mod_adder = float((top["ordc"] + top["rtord"]).mean())
    act_adder = float((top["rtorpa"] + top["rtordpa"]).mean())
    mod_energy = float((top["mod"] - top["ordc"] - top["rtord"]).mean())
    act_energy = float(top["system_lambda"].mean())
    d_energy, d_adder = act_energy - mod_energy, act_adder - mod_adder
    tot = d_energy + d_adder
    return {
        "model_price": float(top["mod"].mean()),
        "actual_price": float(top["act"].mean()),
        "model_energy_only": mod_energy,
        "actual_system_lambda": act_energy,
        "model_adder": mod_adder,
        "actual_adder": act_adder,
        "energy_term": d_energy,
        "adder_term": d_adder,
        "energy_share": d_energy / tot,
        "adder_share": d_adder / tot,
        "model_reserve_held_mw": float(top["held"].mean()),
        "actual_prc_mw": float(top["prc"].mean()),
        "model_ordc_dual": float(top["ordc_dual"].mean()),
        "model_shed_hours": int((top["slack"] > 1).sum()),
    }


def _bin_dilution(g: pd.DataFrame) -> dict:
    """Actual-vs-model price inside each net-load conditioning bin, and inside the top one."""
    q = [float(g["netload"].quantile(e)) for e in NETLOAD_PCTS]
    bins = []
    for i in range(len(NETLOAD_PCTS) - 1):
        hi_mask = (
            g["netload"] <= q[i + 1]
            if i == len(NETLOAD_PCTS) - 2
            else g["netload"] < q[i + 1]
        )
        d = g[(g["netload"] >= q[i]) & hi_mask]
        bins.append(
            {
                "bin": f"p{NETLOAD_PCTS[i] * 100:.0f}-p{NETLOAD_PCTS[i + 1] * 100:.0f}",
                "hours": int(len(d)),
                "actual_p50": float(d["act"].median()),
                "actual_p90": float(d["act"].quantile(0.9)),
                "actual_max": float(d["act"].max()),
                "actual_mean": float(d["act"].mean()),
                "model_mean": float(d["mod"].mean()),
            }
        )
    inner = []
    for lo, hi in ((0.97, 0.99), (0.99, 0.995), (0.995, 1.0)):
        a, b = g["netload"].quantile(lo), g["netload"].quantile(hi)
        d = g[(g["netload"] >= a) & (g["netload"] <= b)]
        inner.append(
            {
                "slice": f"p{lo * 100:.1f}-p{hi * 100:.1f}",
                "hours": int(len(d)),
                "actual_mean": float(d["act"].mean()),
                "model_mean": float(d["mod"].mean()),
                "ratio": float(d["act"].mean() / max(d["mod"].mean(), 1.0)),
            }
        )
    n_tail = int((g["act"] > TAIL_THRESHOLD).sum())
    return {
        "bins": bins,
        "top_bin_split": inner,
        "tail_hours": n_tail,
        "tail_share_of_year": n_tail / len(g),
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--top-n", type=int, default=50)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    g = _load(args.bundle, args.year)
    ann = float(np.average(g["mod"], weights=g["load"]))
    print(f"=== C3a-{args.year} anatomy (keeper bundle {args.bundle.name}) ===")
    print(
        f"model lw {ann:.2f}  actual lw {ACTUAL_RT_LW_ANNUAL:.2f}  "
        f"-> {100 * (ann - ACTUAL_RT_LW_ANNUAL) / ACTUAL_RT_LW_ANNUAL:+.1f}%\n"
    )

    mon = _monthly(g)
    print("month  model_lw  actual_lw   share of annual $-gap")
    for r in mon["months"]:
        print(
            f"  {r['month']:2d}   {r['model_lw']:8.2f} {r['actual_lw']:10.2f}   "
            f"{100 * r['share_of_annual_gap']:6.1f}%"
        )
    summer_share = sum(
        r["share_of_annual_gap"] for r in mon["months"] if r["month"] in SUMMER
    )
    print(f"\nAug+Sep share of the annual gap: {100 * summer_share:.1f}%\n")

    s = g[g["mon"].isin(SUMMER)]
    order = (s["act"] - s["mod"]).sort_values(ascending=False)
    conc = {k: float(order.head(k).sum() / order.sum()) for k in (10, 25, 50, 100, 200)}
    for k, v in conc.items():
        print(f"  top {k:4d} Aug-Sep gap-hours carry {100 * v:5.1f}%")

    top = s.loc[order.head(args.top_n).index]
    comp = _component_split(top)
    print(f"\n--- TOP-{args.top_n} Aug-Sep hours: model vs ERCOT published ---")
    print(
        f"  RT price        model {comp['model_price']:9.2f}   actual {comp['actual_price']:9.2f}"
    )
    print(
        f"  energy-only     model {comp['model_energy_only']:9.2f}   actual "
        f"{comp['actual_system_lambda']:9.2f}   <- system_lambda"
    )
    print(
        f"  scarcity adder  model {comp['model_adder']:9.2f}   actual {comp['actual_adder']:9.2f}"
    )
    print(
        f"  reserve MW      model {comp['model_reserve_held_mw']:9.0f}   actual "
        f"{comp['actual_prc_mw']:9.0f}   <- PRC"
    )
    print(
        f"  ENERGY term {comp['energy_term']:9.2f} ({100 * comp['energy_share']:.1f}%)   "
        f"ADDER term {comp['adder_term']:9.2f} ({100 * comp['adder_share']:.1f}%)"
    )

    dil = _bin_dilution(g)
    print("\n--- offer-surface conditioning bins ---")
    for b in dil["bins"]:
        print(
            f"  {b['bin']:>10s} {b['hours']:5d} h   act p50 {b['actual_p50']:7.1f}  "
            f"max {b['actual_max']:7.0f}  mean {b['actual_mean']:7.1f}   mod mean {b['model_mean']:7.1f}"
        )
    print("  inside the top bin:")
    for r in dil["top_bin_split"]:
        print(
            f"    {r['slice']:>12s} {r['hours']:4d} h   act {r['actual_mean']:8.1f}   "
            f"mod {r['model_mean']:8.1f}   {r['ratio']:.2f}x short"
        )
    print(
        f"  tail population (> ${TAIL_THRESHOLD:.0f}): {dil['tail_hours']} h = "
        f"top {100 * dil['tail_share_of_year']:.2f}% of the year"
    )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "year": args.year,
                    "bundle": args.bundle.name,
                    "model_lw_annual": ann,
                    "actual_lw_annual": ACTUAL_RT_LW_ANNUAL,
                    "monthly": mon,
                    "summer_share_of_gap": summer_share,
                    "concentration": conc,
                    "component_split": comp,
                    "bin_dilution": dil,
                },
                indent=1,
            )
        )
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
