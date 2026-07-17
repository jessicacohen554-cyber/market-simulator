"""miso-71 probe: Midwest sub-regional reserve-holding family (engagement depth).

Replays the PROMOTED MISO keeper (``miso70_tier_pricing``) meta.json STRICTLY
via ``replay_keeper.build_kwargs`` (the sanctioned single-source recipe
reconstruction) and applies ONE new mechanism through the generic
``prb_overrides`` ScenarioConfig channel:

    main : miso_midwest_subregional_reserves = True   (the Midwest family)
    base : (nothing added)                same-box unchanged-keeper-recipe replica

The frozen design (``docs/handoffs/miso-engagement-depth-design-2026-07.md``,
Fable Phase A) pre-declares this as the deciding probe. The market-wide MISO
RBDC family is congestion-blind (zone_mask = all ones), so a cost-minimizing LP
can satisfy the measured market-wide reserve requirement with reserve parked in
the RDT-trapped MISO-South surplus and convert every Midwest MW of headroom to
energy in a Midwest event — reality could do neither and held ~1.0-2.5 GW of OR
in the Midwest through the deep windows (measured, design §2b). Leg (a) forces
the MEASURED Midwest (North+Central) OR reservation to sit IN the 5 physical
Midwest zones, priced at the published $200 RPE demand value
(constants.MISO_RPE_DEMAND_VALUE), reserve_class 0 nested — closing the
ledgered "RPE Only" STR-scarcity gap (miso_rpe_pricing DOF entry). ENERGY-SIDE:
it does NOT make the reserve curves fire (design §2c); the family dual sits at
the re-dispatch opportunity cost in almost every hour and reaches $200 only
where the M-2-thinned Midwest fleet cannot hold the measured (feasible)
requirement. Zero fitted scalars — the series is measured, the $200 is a cited
constant, the zone list is topology.

Pre-registered expected-delta bands (design §5, committed BEFORE the solve):
C3b-2025 <= 0.20 ABSOLUTE (standing veto; keeper 0.184), expected [0.160,0.195];
C3b-2024 [0.118,0.135]; C3b-2023 [0.077,0.105]. C3c RT-basis (in-window /
measured-scarce hours only): 2025 [1,26] (the [44,176] PASS band is NOT
claimed — Jul-28 40-min transient + isolated RT singles are out of
representation, R5), 2024 [4,12], 2023 [1,6]. C3a-2025 [-14.5,-10.0] direction
up; C3a-2024 [-8.5,-5.0] PASS. Reserve fidelity (R2): family dual <= $25 in
>=99% of hours, dual >= $200 in <= 20 h/yr ALL inside declared windows or
measured-RT-scarce hours. R3: family dual > $50 in any Jan-14-17-2024 hour is
wrong-driver (measured reserve MCPs there ~$3). DOF: main 25/2, base 24/2.
Refutation criteria R1-R6 (design §6) are the ONLY fallbacks; no retune.

The base is the DRIFT CONTROL: the mechanism-only footprint is main - base
(both solved in THIS box / code state), never main - the registered miso-70
bundle. No zero-forcing ablation twin (rule 20 as amended 2026-07-14).

PER-YEAR + REUSE (RAM <=16 GB): each invocation solves exactly ONE new LP.
Sequence (per variant):

    python scripts/probes/_miso71_midwest_reserves.py <main|base> \\
        --out-dir <acc>/y2023 --years 2023
    python scripts/probes/_miso71_midwest_reserves.py <main|base> \\
        --out-dir <acc>/y2024 --years 2023,2024 --reuse-solved <acc>/y2023
    python scripts/probes/_miso71_midwest_reserves.py <main|base> \\
        --out-dir <acc>/final --years 2023,2024,2025 --reuse-solved <acc>/y2024

The final 3-year bundle is ``<acc>/final`` (rule 16 — one bundle, all years).
Years ALWAYS sequential within a run (rule 12); on this 15 GB box the main and
base variants also run back to back, never concurrently. Solve BASE first
(the design §4.2 phantom-parking pre-read runs on the base).

Rule 22: MISO has no calibration-complete marker -> 2023/2024/2025 ONLY.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# Reproducibility pin (mirrors replay_keeper.py): force cross-year LP warm-start
# OFF so per-year processes are basis-independent and the main/base pair is a
# clean same-box comparison. Set BEFORE importing the solve core.
os.environ.setdefault("MARKET_SIM_WARMSTART_XYEAR", "0")

import run_calibration_full as rcf  # noqa: E402
from replay_keeper import build_kwargs  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso70_tier_pricing"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["main", "base"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--years", required=True, help="comma-separated, e.g. 2023,2024")
    ap.add_argument("--reuse-solved", default=None)
    args = ap.parse_args()

    years = [int(y) for y in args.years.split(",")]
    for y in years:
        if y not in (2023, 2024, 2025):
            raise SystemExit(f"rule 22: MISO year {y} is out of the 2023-2025 window")

    meta = json.loads((KEEPER / "meta.json").read_text())
    if meta.get("iso") != "MISO":
        raise SystemExit(f"wrong base bundle iso={meta.get('iso')!r} (expected MISO)")

    kwargs = build_kwargs(meta)
    # Sanity: the base recipe MUST be the PROMOTED miso-70 keeper (miso-68
    # lineage + the F5 composition, both now keeper structure). The miso-70
    # probe REJECTED the two maxgen flags (they were its delta under test);
    # here we REQUIRE them (design §4/§7.6 — they are keeper structure now).
    prb = kwargs.get("prb_overrides") or {}
    if not (
        prb.get("st_gas_mustrun_per_plant")
        and prb.get("st_gas_mustrun_p25_level")
        and prb.get("unit_outage_short_windows")
    ):
        raise SystemExit(
            "miso-70 meta missing st_gas_mustrun_per_plant/st_gas_mustrun_p25_level/"
            "unit_outage_short_windows in prb_overrides — wrong base bundle"
        )
    if not kwargs.get("carry_operating_mothballs"):
        raise SystemExit(
            "miso-70 meta missing carry_operating_mothballs — wrong base bundle"
        )
    if not (
        prb.get("unit_outage_maxgen_events")
        and prb.get("maxgen_emergency_tier_pricing")
    ):
        raise SystemExit(
            "miso-70 keeper recipe missing unit_outage_maxgen_events / "
            "maxgen_emergency_tier_pricing — the F5 composition is keeper "
            "structure now; wrong base bundle (rule 15 keeper drift)"
        )
    if prb.get("miso_midwest_subregional_reserves"):
        raise SystemExit(
            "base recipe already arms the Midwest family — the probe delta "
            "would be a no-op; wrong base bundle"
        )
    # The measured-requirement intake MUST be on (the Midwest family consumes
    # its "MISO-Midwest" leg; the flag falls back to within-region MSSC only in
    # forecast mode). Recorded as a top-level solve kwarg, not prb_overrides.
    if not kwargs.get("miso_measured_reserve_requirements"):
        raise SystemExit(
            "miso-70 keeper missing miso_measured_reserve_requirements — the "
            "Midwest family's measured basis would be unavailable; wrong bundle"
        )

    if args.mode == "main":
        # The single new mechanism under test: the Midwest sub-regional family.
        prb = dict(prb)
        prb["miso_midwest_subregional_reserves"] = True
        kwargs["prb_overrides"] = prb

    note = (
        f"miso-71 ({args.mode}) -- Midwest sub-regional reserve-holding family "
        "(the engagement-depth lane), the miso-70 keeper recipe plus "
        "miso_midwest_subregional_reserves (NEW: the MEASURED Midwest "
        "(North+Central) cleared OR reservation held IN the 5 physical Midwest "
        "zones (MISO-West/Plains/Illinois/Indiana/East), priced at a single "
        "shortfall step = the published $200/MWh RPE demand value "
        "(constants.MISO_RPE_DEMAND_VALUE, 2024 SOM III.B), reserve_class 0 "
        "nested inside the market-wide RBDC — a Midwest reserve MW counts "
        "toward both). Closes the congestion-blind market-wide family's "
        "phantom-South-parking gap (the ledgered 'RPE Only' under-shoot): a "
        "cost-min LP otherwise parks the market-wide requirement in the "
        "RDT-trapped South surplus and converts Midwest headroom to energy in "
        "a Midwest event, removing ~2 GW of phantom Midwest supply. ENERGY-SIDE "
        "— does NOT make the reserve curves fire (the per-zone ORDC ladder is "
        "measured-refuted; the family dual sits at re-dispatch opportunity cost "
        "in ~every hour and reaches $200 only where the M-2-thinned fleet "
        "cannot hold the measured feasible requirement). Zero fitted scalars "
        "(measured series + cited $200 + topology zone list). Pre-registered "
        "bands (design §5): C3b-2025 <=0.20 ABS veto (expect [0.160,0.195]); "
        "C3c RT 2025 [1,26] (the [44,176] PASS NOT claimed — R5 honesty band); "
        "C3a-2025 [-14.5,-10.0] up. Reserve fidelity (R2): dual <=$25 in >=99% "
        "of hours, >=$200 in <=20 h/yr all in declared/measured-scarce hours; "
        "R3: Jan-14-17-2024 dual >$50 is wrong-driver. base = unchanged-recipe "
        "same-box drift control (mechanism-only = main - base). No ablation "
        "twin (rule 20 amended 2026-07-14). Design: docs/handoffs/"
        "miso-engagement-depth-design-2026-07.md; parents miso-f5-scarcity-"
        "depth / miso-price-formation."
    )

    kwargs["years"] = years
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["reuse_solved"] = Path(args.reuse_solved) if args.reuse_solved else None
    kwargs["note"] = note

    print(
        f"miso-71 {args.mode}: years={years} out={args.out_dir} "
        f"reuse={args.reuse_solved} "
        f"midwest_family={'ON' if args.mode == 'main' else 'off'}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
