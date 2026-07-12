"""miso-61 RDT anchors vs the MEASURED pbc binding record (no solve).

Upgrades the RDT anchor set from SOM annual aggregates to the measured
`transfer-constraint-binding` clean series (MISO {da,rt}_pbc intake,
2026-07-12): DA hourly / RT 5-minute shadow-price records per direction.

Two deliberate basis corrections vs `_miso59_rdt_anchors.py` (kept in-repo
for same-script continuity with the miso-59/60 disclosures):

1. NET corridor basis — `flows.parquet` carries one row per (link, hour)
   and the TCDC representation splits each RDT direction into three
   parallel priced tiers, so per-direction totals must SUM tiers per hour.
   The legacy probe's `% of hours` figures are on a tier-ROWS basis where
   the TCDC is armed (3x deflated) and its mean-flowing MW is ~the free
   tier's mean; its cross-run DELTAS remain valid same-script comparisons.
2. Same-basis measured anchors — the SOM's ">25% of RT intervals" (2024)
   counts the RDT+RPE constraint FAMILY (IMM Summer-2025 quarterly p.29
   splits "Tx Only"/"Both"/"RPE Only"); the pbc series is the RDT-proper
   record (RT ~7.5% of 2024 intervals). The model's single RDT constraint
   stands in for the whole family (the RPE limit is unpublished), so its
   binding frequency is expected BETWEEN the pbc RDT-proper record and the
   SOM family figure; model zonal separation compares against measured
   |shadow| PLUS the unobserved RPE contribution (2024 SOM §III.B).

Usage: python scripts/probes/_miso61_rdt_anchors.py <bundle_dir>
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib import clean_io  # noqa: E402

# RDT contract limits and the modeled 92% default derate (constants.MISO_RDT_*)
NS_LIMIT, SN_LIMIT, DERATE = 3000.0, 2500.0, 0.92
# Midwest zone set used for the IMM-style Midwest-South separation (the
# FINDING §10 note's construction: mean of the four Midwest model zones).
MIDWEST_ZONES = ["MISO-Illinois", "MISO-Indiana", "MISO-West", "MISO-Plains"]
# Jun-Aug hour span in the fixed non-leap 8760 clock.
SUMMER = slice(3624, 5832)
# First TCDC step price — a measured DA shadow pinned here marks flow in
# real violation within (100%, 102%] of the modeled limit.
STEP1 = 40.0


def _measured(year: int) -> dict:
    """Measured pbc anchors for one year from the clean series."""
    out: dict = {}
    for market in ("da", "rt"):
        try:
            df = clean_io.read_clean(
                "transfer-constraint-binding", iso="MISO", year=year, market=market
            )
        except FileNotFoundError:
            continue
        per_hr = 1.0 if market == "da" else 1.0 / 12.0
        for direction, g in df.groupby("direction"):
            sp = g["shadow_price_usd_mwh"]
            out[(market, direction)] = {
                "bind_h": len(g) * per_hr,
                "mean_abs_shadow": float(sp.abs().mean()),
                "plateau_h": float((sp <= -STEP1 + 1e-9).sum() * per_hr),
                "deep_h": float((sp < -STEP1 - 1e-6).sum() * per_hr),
            }
    return out


def main(bundle: Path) -> None:
    flows = pd.read_parquet(bundle / "flows.parquet")
    flows = flows[flows["pass"] == "P1"]

    # NET corridor basis: sum the parallel TCDC tier links per hour.
    def net(fz: str, tz: str, year: int) -> pd.Series:
        g = flows[
            (flows.from_zone == fz) & (flows.to_zone == tz) & (flows.year == year)
        ]
        return g.groupby("hour").mw.sum()

    for year in sorted(flows.year.unique()):
        sn = net("MISO-South", "MISO-Plains", year)
        ns = net("MISO-Plains", "MISO-South", year)
        d = pd.read_parquet(
            bundle / "dispatch" / f"{year}_P1.parquet",
            columns=["zone", "hour", "lmp", "unit_id"],
        )
        zl = d.groupby(["zone", "hour"], observed=True).lmp.first().unstack(0)
        sep_plains = zl["MISO-Plains"] - zl["MISO-South"]
        mw_cols = [z for z in MIDWEST_ZONES if z in zl.columns]
        sep_mw = zl[mw_cols].mean(axis=1) - zl["MISO-South"]

        sn_mod, ns_mod = DERATE * SN_LIMIT, DERATE * NS_LIMIT
        sn_bind = sn >= sn_mod - 1.0
        ns_bind = ns >= ns_mod - 1.0
        sn_viol = sn > sn_mod + 1.0
        ns_viol = ns > ns_mod + 1.0

        print(f"== {year} (net corridor basis) ==")
        for tag, f, bind, viol, mod in (
            ("S->N", sn, sn_bind, sn_viol, sn_mod),
            ("N->S", ns, ns_bind, ns_viol, ns_mod),
        ):
            flowing = f[f > 1.0]
            print(
                f"  {tag} mean-flowing {flowing.mean() if len(flowing) else 0:7.0f} MW"
                f" | flows {len(flowing) / 8760 * 100:5.1f}% h"
                f" | binds(>= {mod:.0f}) {int(bind.sum()):4d} h"
                f" | violates {int(viol.sum()):4d} h"
            )
        for tag, bind in (("S->N", sn_bind), ("N->S", ns_bind)):
            hrs = bind[bind].index
            if len(hrs):
                sp = sep_plains.loc[sep_plains.index.intersection(hrs)]
                sm = sep_mw.loc[sep_mw.index.intersection(hrs)]
                sign = 1.0 if tag == "S->N" else -1.0
                print(
                    f"  model separation when {tag} binding:"
                    f" Plains-South ${sign * sp.mean():+.2f}"
                    f" | Midwest-South ${sign * sm.mean():+.2f}"
                )
        print(
            f"  summer mean Midwest-South separation: ${sep_mw.iloc[SUMMER].mean():+.2f}"
            f" (Plains-South ${sep_plains.iloc[SUMMER].mean():+.2f}; IMM 2025: $9.31)"
        )
        aug = zl.iloc[5088:5832].mean(axis=None)
        print(f"  August mean LMP (all zones): ${aug:.2f}")

        m = _measured(int(year))
        if m:
            print("  measured pbc (RDT-proper; family binds MORE via RPE):")
            for (market, direction), v in sorted(m.items()):
                tag = "S->N" if direction == "S_to_N" else "N->S"
                print(
                    f"    {market} {tag}: binds {v['bind_h']:7.1f} h-eq"
                    f" | mean|shadow| ${v['mean_abs_shadow']:5.2f}"
                    f" | at-$40-plateau {v['plateau_h']:5.1f} h-eq"
                    f" | deeper {v['deep_h']:5.1f} h-eq"
                )
        else:
            print("  measured pbc: clean series not found (run the curation)")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
