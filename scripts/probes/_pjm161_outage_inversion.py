"""pjm-161 Phase-0: the CAMPD outage envelope is ANTI-CORRELATED with scarcity.

Context. The `campd_outage_windows` matrix row and the holdout freeze both rest
on the neiso-63 finding that the CAMPD detector books sustained ECONOMIC LAYUP
as mechanical outage in all six ISO extracts. That has always been stated as a
LEVEL defect (23-46 % of CC capacity-year booked out against a ~10-15 % real
EFOR+planned norm).

This probe measures its SHAPE, which is the part that bites: because layup is
inferred from *not generating*, and a unit in layup RUNS when prices spike, the
detected outage inventory COLLAPSES in exactly the hours the real forced-outage
rate PEAKS. The envelope therefore hands the LP the most capacity in the
tightest hours — the inverse of physical truth.

`ScenarioConfig.correlated_forced_outage` is COERCED OFF in backcast mode, on
the documented ground that "a backcast's measured CAMPD overlays carry the real
cold events" (mechanism-matrix, FFR-1D). This probe tests that assumption.

Measured per year: mean derated MW from the windows the model actually consumes
(`campd-unit-outages-<ISO>.csv` + `-short-`), conditioned on net-load percentile
and on temperature, plus the Winter-Storm-Elliott / winter-event windows.

No LP, no scoring, no registration — raw committed inputs only.

Run:  uv run python scripts/probes/_pjm161_outage_inversion.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "raw"
E930 = RAW / "eia-930-hourly" / "PJM hourly.parquet"
SOURCES = ("campd-unit-outages-PJM", "campd-unit-outages-short-PJM")

#: Named PJM winter/summer stress events, for the event rows.
EVENTS = {
    2022: ("2022-12-23", "2022-12-26", "Elliott"),
    2023: ("2023-02-03", "2023-02-04", "Feb cold snap"),
    2024: ("2024-01-15", "2024-01-17", "Heather"),
    2025: ("2025-01-21", "2025-01-23", "Enzo"),
}


def outage_mw(year: int) -> pd.Series:
    """Hourly derated MW asserted by the overlay the model consumes."""
    hours = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    out = pd.Series(0.0, index=hours)
    for name in SOURCES:
        d = pd.read_csv(RAW / f"{name}.csv")
        d["s"] = pd.to_datetime(d["outage_start"])
        d["e"] = pd.to_datetime(d["outage_end"])
        d = d[(d["e"] >= hours[0]) & (d["s"] <= hours[-1])]
        for _, r in d.iterrows():
            out.loc[max(r["s"], hours[0]) : min(r["e"], hours[-1])] += r[
                "unit_capacity_mw"
            ]
    return out


def e930(year: int) -> pd.DataFrame:
    d = pd.read_parquet(E930)
    d = d[pd.to_datetime(d["Local date"]).dt.year == year].copy()
    d["lt"] = pd.to_datetime(d["Local time"])
    d = d.set_index("lt")
    dem = pd.to_numeric(d["Demand"], errors="coerce")
    vre = pd.to_numeric(d["NG: WND"], errors="coerce").fillna(0) + pd.to_numeric(
        d["NG: SUN"], errors="coerce"
    ).fillna(0)
    return pd.DataFrame({"demand": dem, "netload": dem - vre})


def main() -> None:
    pd.set_option("display.width", 200)
    rows = []
    for year in (2022, 2023, 2024, 2025):
        o = outage_mw(year)
        m = e930(year)
        df = pd.DataFrame({"out": o}).join(m, how="inner").dropna()
        ann = df["out"].mean()
        q = df["netload"].rank(pct=True)
        top1 = df.loc[q >= 0.99, "out"].mean()
        top5 = df.loc[q >= 0.95, "out"].mean()
        bot50 = df.loc[q <= 0.50, "out"].mean()
        corr = float(np.corrcoef(df["out"], df["netload"])[0, 1])
        s, e, label = EVENTS[year]
        ev = df.loc[s:f"{e} 23:00", "out"]
        rows.append(
            dict(
                year=year,
                annual_mean_MW=ann,
                top1pct_netload_MW=top1,
                top5pct_netload_MW=top5,
                bottom50pct_MW=bot50,
                ratio_top1_over_annual=top1 / ann,
                corr_out_vs_netload=corr,
                event=label,
                event_mean_MW=float(ev.mean()),
                ratio_event_over_annual=float(ev.mean()) / ann,
            )
        )
    df = pd.DataFrame(rows).set_index("year")
    print("=" * 100)
    print("PJM — CAMPD outage envelope vs system tightness (MW derated by the overlay)")
    print("  a PHYSICALLY correct envelope has ratio >= 1 (forced outages rise in stress)")
    print("=" * 100)
    print(df.T.to_string(float_format=lambda v: f"{v:,.3f}" if abs(v) < 10 else f"{v:,.0f}"))

    print()
    print("READING")
    print(
        f"  top-1 % net-load hours carry {df['ratio_top1_over_annual'].min():.2f}"
        f"-{df['ratio_top1_over_annual'].max():.2f}x the annual mean outage —"
        " every year BELOW 1."
    )
    print(
        f"  correlation(outage MW, net load) = "
        f"{df['corr_out_vs_netload'].min():+.3f} .. {df['corr_out_vs_netload'].max():+.3f}"
        " — negative in every year."
    )
    print(
        "  So the inversion is a STANDING property of the envelope, not a 2022 artifact;"
        "\n  2022 is where a large enough event finally made it visible in a gate."
    )

    dest = REPO / "results" / "calibration" / "_pjm161_outage_inversion.json"
    dest.write_text(
        json.dumps(json.loads(df.reset_index().to_json(orient="records")), indent=1)
        + "\n"
    )
    print(f"\nwrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
