"""SPP-107 shard self-check: the SPP keeper replayed with the repaired MMU carrier (arm EXR).

Run by each SPP-107 shard AFTER its solve and BEFORE it pushes (rule 32 hard stops). Zero LP.
Pre-registered in ``docs/records/spp/PRECOMMIT-spp-107-mmu-carrier-repair-2026-10-02.md``.

Arm ``EXR`` = ``spp_mmu_offer_unavailability = true`` + ``spp_mmu_offer_repair = true``.

Checks 1-9 are ``_spp106_shard_check.py``'s, run unchanged with the arm swapped (recipe = the keeper
plus EXACTLY the two fields; gas price; pinned input hashes; resolved outage / tranche artifacts;
topology; ``dispatch/<Y>_P1.parquet``; the 1416 remap; the MMU table hash; armed). Added here, read
from the leg's P1 per-unit layer (``hourly/unit_marginal_<Y>.parquet``, else ``unit_hourly``):

10. **pool present** -- exactly one ``emergency_band`` row per zone (SPP-North, SPP-South).
11. **pool offer** -- every P1 pool offer equals the LP's shed price minus epsilon (no markup reached it).
12. **scarcity only** -- every pool unit-hour above 0.5 MW sits in a zone-hour whose P1 price is at
    least the pool offer minus $1/MWh (the pool never clears an economic hour).

Reported (never a push blocker): pool MWh and hours by zone, and everything check 1-9 reports.

Usage::

    python scripts/probes/_spp107_shard_check.py --year 2024 --leg results/calibration/spp107EXR_2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scripts.probes._spp106_shard_check as base  # noqa: E402

ARM = {"spp_mmu_offer_unavailability": True, "spp_mmu_offer_repair": True}
ZONES = ["SPP-North", "SPP-South"]
POOL_TOL_MW = 0.5
PRICE_TOL = 1.0


def pool_checks(leg: Path, year: int) -> bool:
    """Checks 10-12 on the leg's P1 per-unit layer; prints a readout and returns pass/fail."""
    import pandas as pd

    from market_sim.config.constants import STORAGE_TIEBREAKER_EPSILON
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.pipeline.spec import shed_penalty_voll

    offer = shed_penalty_voll(ScenarioConfig(iso="SPP"), get_iso_config("SPP")) - (
        STORAGE_TIEBREAKER_EPSILON
    )
    src = None
    for name in (f"unit_marginal_{year}.parquet", f"unit_hourly_{year}.parquet"):
        if (leg / "hourly" / name).exists():
            src = leg / "hourly" / name
            break
    if src is None:
        print("POOL CHECK: FAIL -- no unit_marginal / unit_hourly sidecar")
        return False
    u = pd.read_parquet(src, filters=[("fuel", "==", "emergency_band")])
    u = u[u["pass"].astype(str) == "P1"]
    ok = True
    zones = sorted(u.zone.astype(str).unique())
    n_ids = u.unit_id.astype(str).nunique()
    if zones != ZONES or n_ids != len(ZONES):
        print(f"POOL PRESENT CHECK: FAIL -- zones {zones}, {n_ids} unit ids")
        return False
    print(f"POOL PRESENT CHECK: PASS -- {sorted(u.unit_id.astype(str).unique())}")
    if "mc" not in u:
        print("POOL OFFER CHECK: FAIL -- no mc column")
        ok = False
    else:
        dev = float((u.mc.astype(float) - offer).abs().max())
        ok &= dev < 1e-2
        print(
            f"POOL OFFER CHECK: {'PASS' if dev < 1e-2 else 'FAIL'} -- max |mc - {offer:.3f}| {dev:.4f}"
        )
    s = pd.read_parquet(leg / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"][["zone", "hour", "price", "slack"]]
    on = u[u.mw.astype(float) > POOL_TOL_MW].astype({"zone": str})
    j = on.merge(s.astype({"zone": str}), on=["zone", "hour"], how="left")
    bad = j[j.price < offer - PRICE_TOL]
    if len(bad):
        print(
            f"SCARCITY-ONLY CHECK: FAIL -- {len(bad)} pool unit-hours below {offer - PRICE_TOL:.2f} $/MWh"
        )
        print(bad.head(10).to_string())
        ok = False
    else:
        print(
            f"SCARCITY-ONLY CHECK: PASS -- {len(j)} pool unit-hours, all at the shed price"
        )
    for z in ZONES:
        zz = u[u.zone.astype(str) == z]
        print(
            f"pool {z}: {float(zz.mw.sum()):.1f} MWh in {int((zz.mw > POOL_TOL_MW).sum())} h; "
            f"capacity mean {float(zz.cap_mw.mean()):.0f} MW"
        )
    return ok


def main() -> int:
    """CLI entry point: the SPP-106 checks with the EXR arm, then the pool checks."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--leg", required=True)
    ap.add_argument("--keeper", default=base.KEEPER)
    a = ap.parse_args()
    base.ARMS = {"EXR": ARM}
    argv = sys.argv
    sys.argv = [
        argv[0],
        "--arm",
        "EXR",
        "--year",
        str(a.year),
        "--leg",
        a.leg,
        "--keeper",
        a.keeper,
    ]
    try:
        rc = base.main()
    finally:
        sys.argv = argv
    ok = pool_checks(ROOT / a.leg, a.year) and rc == 0
    print("SPP-107 SHARD CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
