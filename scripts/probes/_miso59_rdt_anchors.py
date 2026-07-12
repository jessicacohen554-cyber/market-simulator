"""miso-59 success-gate check: RDT anchors + August LMPs from a bundle's own
persisted artifacts (flows.parquet + dispatch parquets). No solve.

Anchors (FINDING §11 / miso-58 log entry):
- 2023/2024 S->N mean flow vs measured 917/1,108 MW (2023 SOM §IV.E, 2024 §II.E)
- 2024 S->N binding frequency vs measured >25% of intervals (2024 SOM §III.B)
- separation-when-binding (Plains−South LMP when S->N at its derated limit)
  vs measured ~$3 (2024) / $9.31 summer-2025
- 2025 direction: N->S vs S->N mean/binding (miso-58 baseline: N->S 1,350 MW
  29% binding, S->N 322 MW 4%)
- August 2023/24 mean LMP (hold within a few $ of miso-58: +0.5/+0.5 monthly)

Usage: python scripts/probes/_miso59_rdt_anchors.py <bundle_dir>
"""

import sys
from pathlib import Path

import pandas as pd

# RDT contract limits and the modeled 92% default derate (constants.MISO_RDT_*)
NS_LIMIT, SN_LIMIT, DERATE = 3000.0, 2500.0, 0.92


def main(bundle: Path) -> None:
    flows = pd.read_parquet(bundle / "flows.parquet")
    flows = flows[flows["pass"] == "P1"]
    rdt_ns = flows[(flows.from_zone == "MISO-Plains") & (flows.to_zone == "MISO-South")]
    rdt_sn = flows[(flows.from_zone == "MISO-South") & (flows.to_zone == "MISO-Plains")]
    for year in sorted(flows.year.unique()):
        ns = rdt_ns[rdt_ns.year == year].set_index("hour").mw
        sn = rdt_sn[rdt_sn.year == year].set_index("hour").mw
        d = pd.read_parquet(
            bundle / "dispatch" / f"{year}_P1.parquet",
            columns=["zone", "hour", "lmp", "unit_id"],
        )
        zl = d.groupby(["zone", "hour"], observed=True).lmp.first().unstack(0)
        sep = zl["MISO-Plains"] - zl["MISO-South"]
        sn_bind = sn >= DERATE * SN_LIMIT - 1.0
        ns_bind = ns >= DERATE * NS_LIMIT - 1.0
        sn_flow = sn[sn > 1.0]
        ns_flow = ns[ns > 1.0]
        print(f"== {year} ==")
        print(
            f"  S->N mean-flowing {sn_flow.mean() if len(sn_flow) else 0:7.0f} MW"
            f" (flows {len(sn_flow) / len(sn) * 100:4.1f}% h,"
            f" binds {sn_bind.sum() / max(len(sn_flow), 1) * 100:4.1f}% of flowing"
            f" / {sn_bind.mean() * 100:4.1f}% of all h)"
        )
        print(
            f"  N->S mean-flowing {ns_flow.mean() if len(ns_flow) else 0:7.0f} MW"
            f" (flows {len(ns_flow) / len(ns) * 100:4.1f}% h,"
            f" binds {ns_bind.sum() / max(len(ns_flow), 1) * 100:4.1f}% of flowing"
            f" / {ns_bind.mean() * 100:4.1f}% of all h)"
        )
        if sn_bind.any():
            bind_hours = sn_bind[sn_bind].index
            sep_bind = sep.loc[sep.index.intersection(bind_hours)]
            print(
                f"  separation when S->N binding: ${sep_bind.mean():.2f}"
                f" (Plains−South; Midwest dearer positive — SOM anchor ~$3)"
            )
        # summer separation (Jun-Aug hours 3624-5832 in a non-leap year)
        smr = slice(3624, 5832)
        print(f"  summer mean Midwest−South separation: ${sep.iloc[smr].mean():+.2f}")
        # August mean LMP (demand-unweighted zonal mean, h 5088-5832)
        aug = zl.iloc[5088:5832].mean(axis=None)
        print(f"  August mean LMP (all zones): ${aug:.2f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
