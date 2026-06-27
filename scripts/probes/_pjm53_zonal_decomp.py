"""pjm-53 validation: per-zone LMP spread, CC/bit by zone, net export.

Confirms the zonal gas basis lever opened the west-cheap / east-dear spread:
PJM should no longer clear as a single copper-plate (0.000 zonal spread). The
per-zone LMP spread IS the binding-link signal — congestion across a TTC link
shows up as an LMP difference across it, so east > west zonal LMP confirms the
Central_PA→EMAAC / SWMAAC→EMAAC interfaces bind.

Usage: python scripts/probes/_pjm53_zonal_decomp.py [bundle_dir]
"""

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))
from market_sim.config.iso_configs import get_iso_config  # noqa: E402

BUNDLE = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else (_ROOT / "results" / "calibration" / "pjm53_zonalgas")
)
WEST = ["PJM_ComEd", "PJM_AEP_Ohio", "PJM_ATSI", "PJM_West_APS", "PJM_Central_PA"]
EAST = ["PJM_EMAAC", "PJM_SWMAAC", "PJM_Dominion"]


def main() -> int:
    load_share = {z.name: z.load_share for z in get_iso_config("PJM").zones}
    for year in (2023, 2024, 2025):
        path = BUNDLE / "dispatch" / f"{year}_P1.parquet"
        if not path.exists():
            print(f"{year}: no dispatch parquet at {path}")
            continue
        df = pd.read_parquet(path)
        real = df[df["zone"].isin(load_share)]  # drop external/import pseudo-zones

        # Per-zone mean LMP (each zone's lmp is constant across its units/hours
        # within a zone-hour, so the per-zone mean over all rows = mean over hours).
        zlmp = real.groupby("zone")["lmp"].mean()
        lw = sum(zlmp[z] * load_share[z] for z in zlmp.index) / sum(
            load_share[z] for z in zlmp.index
        )
        spread = zlmp.max() - zlmp.min()
        west_lmp = sum(zlmp[z] for z in WEST) / len(WEST)
        east_lmp = sum(zlmp[z] for z in EAST) / len(EAST)

        print(f"\n===== PJM {year} =====")
        print(
            f"load-weighted LMP ${lw:.2f}  |  zonal spread ${spread:.2f}  "
            f"(0.00 = copper-plate)"
        )
        print(
            f"  WEST mean ${west_lmp:.2f}   EAST mean ${east_lmp:.2f}   "
            f"east-west ${east_lmp - west_lmp:+.2f}"
        )
        for z in WEST + EAST:
            tag = "W" if z in WEST else "E"
            print(f"   [{tag}] {z:18} ${zlmp[z]:.2f}")

        # CC_REGULAR and COAL_BIT TWh by zone (the over/under-run symptoms).
        for klass in ("CC_REGULAR", "COAL_BIT"):
            sub = real[real["klass"] == klass]
            if sub.empty:
                continue
            by = sub.groupby("zone")["mw"].sum() / 1e6
            print(
                f"  {klass} TWh by zone: total {by.sum():.1f}  "
                + "  ".join(
                    f"{z.replace('PJM_', '')}={by[z]:.1f}"
                    for z in by.sort_values(ascending=False).index[:5]
                )
            )

        # Net export from the priced external reference pseudo-gens.
        ref = df[df["unit_id"].astype(str).str.startswith("PJM_external_ref")]
        if not ref.empty:
            uid = ref["unit_id"].astype(str)
            exp = ref[uid.str.contains("refexp")]["mw"].sum()
            imp = ref[uid.str.contains("refimp")]["mw"].sum()
            net_export = (-exp - imp) / 1e6
            print(
                f"  net export {net_export:+.1f} TWh "
                f"(refexp {-exp / 1e6:+.1f}, refimp {-imp / 1e6:+.1f})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
