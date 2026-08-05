"""nyiso-127 Phase 0 — identify the eight NY-NJ PARs and measure the split.

Reproduces, from the committed intake alone (`data/raw/NYISO/par-data/`), the
three Phase-0 results the nyiso-127 addendum rests on:

1. **Identification.** All eight PARs the NY-NJ posting names resolve to a
   published PTID by exact match against MIS P-33 ``outSched``'s
   ``Equipment Name``. Zero identification freedom.
2. **Corroboration.** A PAR that ``outSched`` says is out measures exactly zero
   flow in P-34 ``ParFlows``. Two independent NYISO postings, same answer.
3. **The split.** Applying the posting's own outage-reallocation rule hour by
   hour gives the availability-conditioned share landing in each model zone —
   which is NOT the flat 47 / 21 / 32 the nameplate percentages imply.

No LP, no model output, 2023-2025 only.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR
from market_sim.data.nyiso_par_attribution import (
    PAR_REGISTRY,
    par_out_mask,
    zone_shares,
)

PAR_DIR = RAW_DIR / "NYISO" / "par-data"
YEARS = (2023, 2024, 2025)


def main() -> None:
    """Print the Phase-0 identification, corroboration and split."""
    outages = pd.read_csv(
        PAR_DIR / "NYISO_par_outages.csv", parse_dates=["outage_start", "outage_end"]
    )
    record: dict = {"probe": "_nyiso127_par_phase0", "years": list(YEARS)}

    print("=== 1. IDENTIFICATION — posting PAR -> published PTID (outSched Equipment Name) ===")
    for ptid, (par, name, interface, share) in PAR_REGISTRY.items():
        seen = name in set(outages.loc[outages["ptid"] == ptid, "equipment_name"])
        print(
            f"   {interface:6s} PAR {par:5s} PTID {ptid:>9d}  {name:32s} "
            f"share {share:.0%}  in outSched: {'YES' if seen else 'no'}"
        )
    print()

    print("=== 2. CORROBORATION — outSched state vs measured ParFlows ===")
    print(f"{'PTID':>9s} {'PAR':>5s} {'hours out':>10s} {'mean MW':>9s} {'|max| MW':>9s} {'h |flow|>0.5':>13s}")
    corr: dict = {}
    for year in YEARS:
        flows = pd.read_csv(
            PAR_DIR / f"NYISO_par_flows_hourly_{year}.csv.gz",
            parse_dates=["interval_start_local"],
        )
        index = pd.date_range(
            pd.Timestamp(year, 1, 1), pd.Timestamp(year + 1, 1, 1), freq="h", inclusive="left"
        )
        print(f" -- {year} --")
        for ptid, (par, _n, _i, _s) in PAR_REGISTRY.items():
            f = flows[flows["ptid"] == ptid]["flow_mw"]
            nout = int(par_out_mask(outages, ptid, index).sum())
            live = float((f.abs() > 0.5).mean()) if len(f) else float("nan")
            print(
                f"{ptid:>9d} {par:>5s} {nout:>10d} {f.mean():9.2f} {f.abs().max():9.1f} "
                f"{live:12.1%}"
            )
            corr[f"{year}|{ptid}"] = {"hours_out": nout, "share_hours_flowing": round(live, 4)}
    record["corroboration"] = corr
    print()

    print("=== 3. THE SPLIT — availability-conditioned share of PJM-AC interchange ===")
    print(f"{'year':6s} {'Capital_Hudson (G)':>20s} {'NYC (J)':>10s} {'Upstate_West (A)':>18s}")
    split: dict = {}
    for year in YEARS:
        sh = zone_shares(outages, year)
        total = sum(v for v in sh.values())
        assert np.allclose(total, 1.0), "shares must sum to 1.0 in every hour"
        print(
            f"{year:<6d} {sh['Capital_Hudson'].mean():19.1%} {sh['NYC'].mean():9.1%} "
            f"{sh['Upstate_West'].mean():17.1%}"
        )
        split[str(year)] = {z: round(float(v.mean()), 4) for z, v in sh.items()}
    record["mean_zone_share"] = split
    print()
    print("   the flat split the parent PREREG pre-emptively refused:  G 47 %   J 21 %   A 32 %")

    dest = "results/calibration/_nyiso127_par_phase0.json"
    with open(dest, "w") as fh:
        json.dump(record, fh, indent=2)
    print(f"\nrecord -> {dest}")


if __name__ == "__main__":
    main()
