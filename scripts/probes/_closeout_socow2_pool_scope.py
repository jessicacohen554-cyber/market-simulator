"""closeout-SOCO-w2 zero-LP census: how much of the SOCO BA's generation is owned inside Southern's pool companies.

Plan docs/backcast-closeout-plan-2026-10.md §3.8 step 3 (ledger quality, no gate). The C3a/C3b benchmark is the
Southern Company Services FERC-714 Sch. 6 system lambda (the pool's incremental cost under the IIC); the model
dispatches the whole SOCO balancing authority. This census splits SOCO-BA EIA-923 net generation per year by owner:
Southern operating companies (Alabama, Georgia, Mississippi, Gulf Power), Southern Power, and non-Southern owners
(co-owners such as Oglethorpe / MEAG / Dalton, and IPPs). Ownership is the EIA-860 owner schedule of the solve
year's vintage, capacity-weighted per plant; a plant absent from the owner schedule is wholly owned by its operator.

Output: docs/records/soco/closeout-soco-w2/pool_scope.csv. No LP.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs/records/soco/closeout-soco-w2"
OPCO = re.compile(r"^(Alabama Power|Georgia Power|Mississippi Power|Gulf Power)", re.I)
SPC = re.compile(r"^Southern Power", re.I)


def owner_class(name: str) -> str:
    """Return the pool class of an EIA-860 owner/operator name."""
    if OPCO.search(str(name)):
        return "southern_opco"
    if SPC.search(str(name)):
        return "southern_power"
    return "non_southern"


def plant_shares(y: int) -> pd.DataFrame:
    """Return per-plant capacity-weighted ownership share by class from the year-``y`` EIA-860 vintage."""
    v = REPO / f"data/raw/eia-860/vintage_{min(y, 2025)}"
    gen = pd.read_parquet(v / "eia860_generator_operable.parquet")
    cap_col = next(c for c in gen.columns if "Nameplate Capacity" in c)
    gen = gen[["Plant Code", "Generator ID", "Utility Name", cap_col]].rename(
        columns={cap_col: "cap"}
    )
    gen["cap"] = pd.to_numeric(gen.cap, errors="coerce").fillna(0.0)
    own = pd.read_parquet(v / "eia860_owner.parquet")
    own["pct"] = pd.to_numeric(own["Percent Owned"], errors="coerce").fillna(0.0)
    own = own[["Plant Code", "Generator ID", "Owner Name", "pct"]]
    g = gen.merge(own, on=["Plant Code", "Generator ID"], how="left")
    g["Owner Name"] = g["Owner Name"].fillna(g["Utility Name"])
    g["pct"] = g.pct.where(g.pct > 0, 1.0)
    g["w"] = g.cap * g.pct
    g["cls"] = g["Owner Name"].map(owner_class)
    s = g.groupby(["Plant Code", "cls"]).w.sum().unstack(fill_value=0.0)
    return s.div(s.sum(axis=1), axis=0)


def main() -> None:
    """Write the per-year owner-class split of SOCO-BA net generation (all fuels and thermal only)."""
    gen = pd.read_parquet(
        REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
    )
    rows = []
    for y in range(2019, 2026):
        e = gen[(gen.year == y) & (gen.ba_code == "SOCO")]
        sh = plant_shares(y)
        for scope, sel in (
            ("all", e),
            ("thermal", e[~e.fuel_type.isin(["WAT", "SUN", "WND"])]),
        ):
            p = sel.groupby("plant_id").netgen_annual_mwh.sum()
            w = sh.reindex(p.index)
            missing = w.isna().all(axis=1)
            w = w.fillna(0.0)
            tot = p.sum()
            row = dict(
                year=y,
                scope=scope,
                total_twh=round(tot / 1e6, 2),
                unmatched_twh=round(p[missing].sum() / 1e6, 2),
            )
            for c in ("southern_opco", "southern_power", "non_southern"):
                v = (w.get(c, 0.0) * p).sum() if c in w else 0.0
                row[f"{c}_twh"] = round(v / 1e6, 2)
                row[f"{c}_pct"] = round(100 * v / tot, 1)
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "pool_scope.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
