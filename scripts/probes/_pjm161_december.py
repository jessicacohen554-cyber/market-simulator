"""pjm-161 Phase-0(b) cont.: is 2022's C3b failure the C1 object in price space?

``_pjm161_c3b_months.py`` shows 75 % of 2022's C3b squared error is DECEMBER
(model $69.65 vs actual $111.90) and that dropping that one month takes the
NRMSE from 0.196 to 0.110 — better than any in-sample year. December 2022 is
Winter Storm Elliott (23-26 Dec), PJM's largest forced-outage event on record.

This probe asks the two questions that follow:

  (1) Is the December miss concentrated in the Elliott window, or spread over
      the month? A concentrated miss is a scarcity/availability defect; a
      spread miss is a fuel-cost defect.
  (2) Does the SAME window carry a CC_REGULAR excess? If the model keeps gas
      capacity available through an event that forced ~46 GW off, then C3b's
      under-price and C1's gas excess are ONE defect, not two.

No LP, no scoring, no registration — committed sidecars and committed actuals.

Run:  uv run python scripts/probes/_pjm161_december.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CANON = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_PJM.parquet"
BUNDLE_OF = {
    2022: REPO / "results" / "calibration" / "pjm2022_touchpoint",
    2023: REPO / "results" / "calibration" / "pjm152_collapse_A",
    2024: REPO / "results" / "calibration" / "pjm152_collapse_A",
    2025: REPO / "results" / "calibration" / "pjm152_collapse_A",
}
E930 = REPO / "data" / "raw" / "eia-930-hourly" / "PJM hourly.parquet"


def model_clock(year: int) -> pd.DatetimeIndex:
    """The model's 8760-row local-time clock for a year (the LP's row order)."""
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    df = _eia_hourly_frame_filled("PJM", year)
    return pd.DatetimeIndex(df["Local time"])[:8760]


def model_system(year: int) -> pd.DataFrame:
    sy = pd.read_parquet(BUNDLE_OF[year] / "hourly" / f"system_{year}.parquet")
    sy = sy[(sy["pass"] == "P1") & (sy["zone"] != "PJM_external")]
    price = sy.pivot_table(index="hour", columns="zone", values="price")
    dem = sy.pivot_table(index="hour", columns="zone", values="demand")
    lw = (price * dem).sum(axis=1) / dem.sum(axis=1)
    return pd.DataFrame({"model_lw": lw, "model_dem": dem.sum(axis=1)}).reindex(
        range(8760)
    )


def actual_hourly(year: int) -> pd.DataFrame:
    d = pd.read_parquet(CANON)
    d = d[d["year"] == year].set_index("hour")[["rt", "da"]]
    return d.reindex(range(8760)).ffill().bfill()


def klass_hourly(year: int, klass: str) -> pd.Series:
    ch = pd.read_parquet(BUNDLE_OF[year] / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"] == klass)]
    return ch.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0)


def e930_hourly(year: int) -> pd.DataFrame:
    d = pd.read_parquet(E930)
    d = d[pd.to_datetime(d["Local date"]).dt.year == year].copy()
    d["lt"] = pd.to_datetime(d["Local time"])
    return d.set_index("lt")


def main() -> None:
    pd.set_option("display.width", 200)
    year = 2022
    clock = model_clock(year)
    m = model_system(year)
    a = actual_hourly(year)
    df = pd.DataFrame(
        {
            "t": clock,
            "model": m["model_lw"].to_numpy(),
            "rt": a["rt"].to_numpy(),
            "da": a["da"].to_numpy(),
            "cc": klass_hourly(year, "CC_REGULAR").to_numpy(),
            "coal": (
                klass_hourly(year, "COAL_BIT")
                + klass_hourly(year, "COAL_PRB")
                + klass_hourly(year, "COAL_WC")
            ).to_numpy(),
            "imp": klass_hourly(year, "import").to_numpy(),
            "vinc": klass_hourly(year, "VIRTUAL_INC").to_numpy(),
            "vdec": klass_hourly(year, "VIRTUAL_DEC").to_numpy(),
            "dem": m["model_dem"].to_numpy(),
        }
    ).set_index("t")
    df["resid"] = df["model"] - df["rt"]

    # actual gas from the 930 book, aligned on the same local clock
    e = e930_hourly(year)
    df["a_gas"] = pd.to_numeric(e["NG: NG"], errors="coerce").reindex(df.index).to_numpy()
    df["a_coal"] = pd.to_numeric(e["NG: COL"], errors="coerce").reindex(df.index).to_numpy()
    df["a_dem"] = pd.to_numeric(e["Demand"], errors="coerce").reindex(df.index).to_numpy()
    df["m_gas"] = (
        df["cc"]
        + klass_hourly(year, "CT_PEAKER").to_numpy()
        + klass_hourly(year, "ST_GAS").to_numpy()
        + klass_hourly(year, "CC_CHP").to_numpy()
        + klass_hourly(year, "CT_CHP").to_numpy()
    )

    print("=" * 96)
    print("PJM 2022 — where the December C3b miss lives (hourly, load-weighted model dual)")
    print("=" * 96)
    dec = df[df.index.month == 12]
    ell = dec[(dec.index.day >= 23) & (dec.index.day <= 26)]
    rest = dec[~((dec.index.day >= 23) & (dec.index.day <= 26))]
    for name, blk in (("DEC all", dec), ("Elliott 23-26", ell), ("Dec ex-Elliott", rest)):
        print(
            f"  {name:15s} n={len(blk):4d}  model {blk['model'].mean():8.2f}  "
            f"RT {blk['rt'].mean():8.2f}  resid {blk['resid'].mean():+8.2f}  "
            f"| Σresid·h {blk['resid'].sum()/1000:+8.1f} $k/MW"
        )
    # how much of the MONTH's mean-price gap does the 96-h window carry?
    gap_month = dec["resid"].mean()
    contrib_ell = ell["resid"].sum() / len(dec)
    print(
        f"\n  December mean resid {gap_month:+.2f} $/MWh; the 96-h Elliott window "
        f"contributes {contrib_ell:+.2f} ({100*contrib_ell/gap_month:.0f}% of it) "
        f"from {100*len(ell)/len(dec):.0f}% of the hours."
    )

    print()
    print("=" * 96)
    print("The same window in ENERGY — is the model keeping gas available through Elliott?")
    print("=" * 96)
    for name, blk in (("Elliott 23-26", ell), ("Dec ex-Elliott", rest), ("2022 all", df)):
        print(
            f"  {name:15s} model gas {blk['m_gas'].mean():8.0f} MW  930 gas "
            f"{blk['a_gas'].mean():8.0f} MW  Δ {blk['m_gas'].mean()-blk['a_gas'].mean():+8.0f}"
            f"  | model coal {blk['coal'].mean():7.0f}  930 coal {blk['a_coal'].mean():7.0f}"
            f"  Δ {blk['coal'].mean()-blk['a_coal'].mean():+7.0f}"
        )
    print()
    print(
        "  Elliott-window energy Δ (model−930), TWh:  gas "
        f"{(ell['m_gas']-ell['a_gas']).sum()/1e6:+.3f}   coal "
        f"{(ell['coal']-ell['a_coal']).sum()/1e6:+.3f}"
    )
    print(
        "  Whole-year   energy Δ (model−930), TWh:  gas "
        f"{(df['m_gas']-df['a_gas']).sum()/1e6:+.3f}   coal "
        f"{(df['coal']-df['a_coal']).sum()/1e6:+.3f}"
    )

    print()
    print("=" * 96)
    print("Scarcity: does the model price the event at all?")
    print("=" * 96)
    for thr in (200, 500, 1000):
        print(
            f"  hours > ${thr:5d}:  model {int((df['model']>thr).sum()):4d}   "
            f"RT actual {int((df['rt']>thr).sum()):4d}   DA actual {int((df['da']>thr).sum()):4d}"
            f"   | in Elliott: model {int((ell['model']>thr).sum()):3d} "
            f"RT {int((ell['rt']>thr).sum()):3d}"
        )
    print(f"  max model ${df['model'].max():.0f}  max RT ${df['rt'].max():.0f}")

    print()
    print("=" * 96)
    print("The virtual layer's own December position (TWh, + = net virtual DEMAND)")
    print("=" * 96)
    for name, blk in (
        ("2022 all", df),
        ("DEC all", dec),
        ("Elliott 23-26", ell),
        ("Jan-Nov", df[df.index.month < 12]),
    ):
        net = -(blk["vinc"].sum() + blk["vdec"].sum()) / 1e6
        print(f"  {name:15s} net {net:+7.3f} TWh   ({len(blk)} h)")

    payload = {
        "december": {
            "model_mean": float(dec["model"].mean()),
            "rt_mean": float(dec["rt"].mean()),
            "resid_mean": float(dec["resid"].mean()),
            "elliott_share_of_month_gap": float(contrib_ell / gap_month),
        },
        "elliott": {
            "hours": int(len(ell)),
            "model_mean": float(ell["model"].mean()),
            "rt_mean": float(ell["rt"].mean()),
            "gas_delta_twh": float((ell["m_gas"] - ell["a_gas"]).sum() / 1e6),
            "coal_delta_twh": float((ell["coal"] - ell["a_coal"]).sum() / 1e6),
        },
        "year_gas_delta_twh": float((df["m_gas"] - df["a_gas"]).sum() / 1e6),
        "virtual_net_twh": {
            "year": float(-(df["vinc"].sum() + df["vdec"].sum()) / 1e6),
            "december": float(-(dec["vinc"].sum() + dec["vdec"].sum()) / 1e6),
            "jan_nov": float(
                -(
                    df[df.index.month < 12]["vinc"].sum()
                    + df[df.index.month < 12]["vdec"].sum()
                )
                / 1e6
            ),
        },
    }
    dest = REPO / "results" / "calibration" / "_pjm161_december.json"
    dest.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"\nwrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
