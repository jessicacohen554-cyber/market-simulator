"""miso-76 Phase-A probe 1 — measured Midwest hub price-separation anatomy vs the flat model pool.

Derive-only (NO LP). Reads the committed D6 hub actuals
(``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``) and the
miso-75 keeper run payload, and prints:

- annual RT and DA hub means (MINN/ILLINOIS/INDIANA/MICHIGAN);
- hourly spread stats vs INDIANA.HUB (mean, MAE, p95, >$5/>$10/>$25 duration
  shares), RT and DA — the DA rows are the in-representation
  (hourly-LP-reachable) separation;
- monthly RT hub means (the miso-72 Jan-broadening context);
- the model side: the keeper payload's per-zone annual means (the flat pool).

Evidence for docs/handoffs/miso-nc-price-separation-design-2026-07.md §1.
Run: ``.venv/bin/python scripts/probes/_miso76_separation_anatomy.py``
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUALS = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
RUN_JS = REPO / "frontend/data/backcast/runs/2026-07-18-miso-75-manitoba-meritcap.js"
HUBS = ["MINN.HUB", "ILLINOIS.HUB", "INDIANA.HUB", "MICHIGAN.HUB"]


def _payload() -> dict:
    """Decode the keeper's gzip+base64 run payload."""
    m = re.search(r'"([A-Za-z0-9+/=]{100,})"', RUN_JS.read_text())
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def main() -> None:
    df = pd.read_parquet(ACTUALS)
    mw = df[df.hub.isin(HUBS)]

    for mk in ("rt", "da"):
        print(f"=== annual {mk.upper()} means by hub ===")
        print(mw.groupby(["year", "hub"])[mk].mean().unstack().round(2))
        piv = mw.pivot_table(index=["year", "hour"], columns="hub", values=mk)
        print(f"\n=== {mk.upper()} hourly spread vs INDIANA.HUB ===")
        for hub in ["MINN.HUB", "ILLINOIS.HUB", "MICHIGAN.HUB"]:
            s = piv[hub] - piv["INDIANA.HUB"]
            g = s.groupby(level="year")
            print(
                hub,
                "\n",
                pd.DataFrame(
                    {
                        "mean": g.mean().round(2),
                        "MAE": g.apply(lambda x: x.abs().mean()).round(2),
                        "p95abs": g.apply(lambda x: x.abs().quantile(0.95)).round(1),
                        ">$5%": g.apply(lambda x: (x.abs() > 5).mean() * 100).round(1),
                        ">$10%": g.apply(lambda x: (x.abs() > 10).mean() * 100).round(
                            1
                        ),
                        ">$25%": g.apply(lambda x: (x.abs() > 25).mean() * 100).round(
                            2
                        ),
                    }
                ),
            )

    # Monthly RT hub means (fixed-CST hour-of-year calendar, model clock).
    piv = mw.pivot_table(
        index=["year", "hour"], columns="hub", values="rt"
    ).reset_index()
    cal = {
        y: pd.date_range(f"{y}-01-01", periods=8760, freq="h")
        for y in (2023, 2024, 2025)
    }
    piv["month"] = [cal[int(y)][int(h)].month for y, h in zip(piv.year, piv.hour)]
    print("\n=== monthly RT hub means ===")
    print(piv.groupby(["year", "month"])[HUBS].mean().round(1).to_string())

    # Model side: the keeper's per-zone annual means (the flat pool).
    print("\n=== miso-75 keeper model per-zone annual mean LMP ===")
    pay = _payload()
    for y, ydat in sorted(pay["years"].items()):
        row = {z: e["p"] for z, e in ydat["lmp"].items() if z.startswith("MISO-")}
        mid = [v for z, v in row.items() if z != "MISO-South"]
        print(
            y,
            {z: round(v, 2) for z, v in row.items()},
            f"midwest span={max(mid) - min(mid):.2f}",
        )


if __name__ == "__main__":
    main()
