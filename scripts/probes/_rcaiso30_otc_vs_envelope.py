"""R-CAISO-30 probe (zero LP): OASIS intertie OTC vs the armed CAISO corridor envelope.

Reads the curated ``transfer-interface-limits`` CAISO partition (OASIS
TRNS_USAGE) and prints, per year, (1) per-ITC import-direction seasonal TTC vs
hourly OTC derate statistics for the largest ITCs, and (2) the PNW comparison:
import OTC summed over a PROVISIONAL ITC set (MALIN500_ISL + NOB_ITC +
CASCADE_ITC) against ``measured_corridor_flow_envelope('CAISO', y, 8760)``
WECC_PNW (the p95 EIA-930 net-import envelope armed on the keeper).
Descriptive only: the ITC -> corridor crosswalk is not identified (ITCs are
tie points, the envelope is BA-to-BA net interchange). Record:
docs/handoffs/r-caiso-30/FINDING-r-caiso-30-2026-10-01.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402
from market_sim.data.eia930.envelopes import measured_corridor_flow_envelope  # noqa: E402

PNW_ITCS = ("MALIN500_ISL", "NOB_ITC", "CASCADE_ITC")
UNLIMITED = 99999.0  # OASIS sentinel


def _load(year: int) -> pd.DataFrame:
    """CAISO partition for ``year`` with the series name split into columns."""
    path = (
        paths.CLEAN_DIR
        / "transfer-interface-limits"
        / "CAISO"
        / f"transfer-interface-limits_{year}.parquet"
    )
    c = pd.read_parquet(path)
    c[["itc", "dir", "tag"]] = c["interface"].str.split("|", expand=True)
    return c


def main() -> None:
    """Print the derate table and the PNW OTC-vs-envelope comparison."""
    for y in (2023, 2024, 2025):
        c = _load(y)
        imp = (
            c[c["dir"] == "I"]
            .pivot_table(index=["itc", "hour"], columns="tag", values="limit_mw")
            .reset_index()
        )
        imp = imp[imp["TTC"] < UNLIMITED]
        g = imp.assign(
            der=(imp["TTC"] - imp["OTC"]).clip(lower=0), d=imp["OTC"] < imp["TTC"]
        ).groupby("itc")
        tab = g.agg(
            TTC=("TTC", "median"),
            OTC=("OTC", "median"),
            pct_derated=("d", "mean"),
            mean_derate=("der", "mean"),
            TRM=("TRM", "mean"),
        )
        print(
            f"== {y}\n{tab.sort_values('TTC', ascending=False).head(12).round(2).to_string()}"
        )
        env = measured_corridor_flow_envelope("CAISO", y, 8760)
        sub = c[(c["dir"] == "I") & (c["tag"] == "OTC") & c["itc"].isin(PNW_ITCS)]
        otc = sub.groupby("hour")["limit_mw"].sum()
        sched = sub.groupby("hour")["transfer_mw"].sum()
        e = pd.Series(env["WECC_PNW"])[otc.index]
        print(
            f"PNW {y}: hours {len(otc)} | OTC sum mean {otc.mean():.0f} p05 {otc.quantile(0.05):.0f} | "
            f"envelope mean {e.mean():.0f} max {e.max():.0f} | env>OTC {100 * (e > otc).mean():.1f}% | "
            f"DAM sched mean {sched.mean():.0f} p95 {sched.quantile(0.95):.0f}, sched>env {100 * (sched > e).mean():.1f}%"
        )


if __name__ == "__main__":
    main()
