"""miso-70 probe: declared-window ELMP emergency-tier pricing (F5, composed).

Replays the MISO keeper (``miso68_cottonwood_mothballs``) meta.json STRICTLY
via ``replay_keeper.build_kwargs`` (the sanctioned single-source recipe
reconstruction) and applies the F5 composition through the generic
``prb_overrides`` ScenarioConfig channel:

    main : unit_outage_maxgen_events = True            (M-2, measured derates)
           maxgen_emergency_tier_pricing = True        (F5, tier price formation)
    base : (nothing added)                same-box unchanged-recipe replica

The frozen design (``docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md``)
pre-declares this composition as the deciding probe: the tier-alone arm is
analytically dispatch-inert on the keeper stack (the keeper prints ZERO hours
with max zonal dual > $200 in all of 2023 and 2025, and its 2024 Aug-26
window hours clear $44-50 ISO-weighted — an unbounded $500-priced slack is
dominated everywhere it exists), and M-2-alone is already adjudicated
(miso-69, REJECTED on the C3b-2024 shape breach: 6 window hours at
$1,841-1,985 vs actual $169 DA). The composition is the structural claim:
measured event-window availability truth (M-2) + the SOM-documented tier
offer floors ($500 Tier 1 at Warning/Step 1, $1,000 Tier 2 at Step 2+ —
2023 SOM fn.21 = 2024/2025 SOM fn.17) = MISO's declared-window price
formation. Zero fitted scalars; windows/levels/regions are the maxgen-events
registry's rows (F4 — never reconstructed from prices).

Pre-registered bands (design §3): C3b-2024 -> [0.124, 0.16] (projection
0.127-0.138; veto <= 0.20); C3b-2023/2025 mechanism-only <= +0.005;
C3c 2023/2024/2025 -> [0,3] / [4,10] / [1,8] model hours > $200 (the tier
treatment caps declared-window formation, it never engages — C3c-2025
staying ~1h does NOT refute the design, §4.5). Refutation criteria §4 only;
no new fallback after reading.

The base is the DRIFT CONTROL: the mechanism-only footprint is main - base
(both solved in THIS box / code state), never main - the registered miso-68
bundle. No zero-forcing ablation twin (rule 20 as amended 2026-07-14).

PER-YEAR + REUSE (RAM <=16 GB): each invocation solves exactly ONE new LP.
Sequence (per variant):

    python scripts/probes/_miso70_tier_pricing.py <main|base> \\
        --out-dir <acc>/y2023 --years 2023
    python scripts/probes/_miso70_tier_pricing.py <main|base> \\
        --out-dir <acc>/y2024 --years 2023,2024 --reuse-solved <acc>/y2023
    python scripts/probes/_miso70_tier_pricing.py <main|base> \\
        --out-dir <acc>/final --years 2023,2024,2025 --reuse-solved <acc>/y2024

The final 3-year bundle is ``<acc>/final`` (rule 16 — one bundle, all years).
Years ALWAYS sequential within a run (rule 12); on this 15 GB box the main
and base variants also run back to back, never concurrently.

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

KEEPER = REPO / "results" / "calibration" / "miso68_cottonwood_mothballs"


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
    # Sanity: the base recipe MUST be the miso-68 keeper (the miso-67 ST_GAS
    # p25 recipe + carry_operating_mothballs) — the F5 composition stacks on
    # THAT.
    prb = kwargs.get("prb_overrides") or {}
    if not (
        prb.get("st_gas_mustrun_per_plant")
        and prb.get("st_gas_mustrun_p25_level")
        and prb.get("unit_outage_short_windows")
    ):
        raise SystemExit(
            "miso-68 meta missing st_gas_mustrun_per_plant/st_gas_mustrun_p25_level/"
            "unit_outage_short_windows in prb_overrides — wrong base bundle"
        )
    if not kwargs.get("carry_operating_mothballs"):
        raise SystemExit(
            "miso-68 meta missing carry_operating_mothballs — wrong base bundle"
        )
    if prb.get("unit_outage_maxgen_events") or prb.get("maxgen_emergency_tier_pricing"):
        raise SystemExit(
            "base recipe already arms the F5 composition — the probe delta "
            "would be a no-op; wrong base bundle"
        )

    if args.mode == "main":
        # The composition under test: M-2 measured derates + F5 tier pricing.
        prb = dict(prb)
        prb["unit_outage_maxgen_events"] = True
        prb["maxgen_emergency_tier_pricing"] = True
        kwargs["prb_overrides"] = prb

    note = (
        f"miso-70 ({args.mode}) -- declared-window ELMP emergency-tier "
        "pricing (F5 of the MISO price-formation lane), COMPOSED with the M-2 "
        "measured derates: the miso-68 keeper recipe plus "
        "unit_outage_maxgen_events (CAMPD revealed unit derates inside the "
        "declared capacity-emergency windows, miso-69's channel) plus "
        "maxgen_emergency_tier_pricing (NEW: inside a maxgen-events registry "
        "window declared at Max Gen Warning or higher, the declared region's "
        "zones reprice the load slack from the $2,000 bid cap to min(voll, "
        "tier floor) — $500 Tier 1 at Warning/Step 1, $1,000 Tier 2 at "
        "Step 2+, the SOM-footnoted ELMP emergency-supply offer floors; the "
        "RBDC/zonal-ORDC curves are never edited). Active windows: "
        "Aug-24-2023 Step-2A ($1,000, 12h footprint), Aug-26-2024 Warning "
        "($500, 7h footprint), Jun-23-2025 Step-1 + Jun-24-2025 Warning "
        "($500, 48h Midwest), Jul-29-2025 Warning ($500, 24h footprint); "
        "advisory/alert rows carry no pricing effect (2023 SOM p.10-11 "
        "ladder: only Warning+ adds margin). Tier-alone is analytically "
        "dispatch-inert on the keeper stack (payload proof, design §2); "
        "M-2-alone is miso-69 (REJECTED, C3b-2024 0.203). The composition "
        "tests: measured availability truth + documented tier price "
        "formation = declared-window prices. Zero fitted scalars — the two "
        "$ floors are cited tariff/SOM values, the unbounded within-window "
        "depth is identified by the ladder's own declaration discipline "
        "(2023 SOM p.11), windows/levels/regions are the registry's (F4). "
        "Pre-registered bands (design §3): C3b-2024 [0.124,0.16] "
        "(projection 0.127-0.138, veto 0.20); C3c 2023/24/25 [0,3]/[4,10]/"
        "[1,8]. base = unchanged-recipe same-box drift control "
        "(mechanism-only = main - base). No ablation twin (rule 20 amended "
        "2026-07-14). Design: docs/handoffs/miso-f5-scarcity-depth-design-"
        "2026-07.md; parent docs/handoffs/miso-price-formation-design-"
        "2026-07.md §5/F5."
    )

    kwargs["years"] = years
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["reuse_solved"] = Path(args.reuse_solved) if args.reuse_solved else None
    kwargs["note"] = note

    print(
        f"miso-70 {args.mode}: years={years} out={args.out_dir} "
        f"reuse={args.reuse_solved} "
        f"composition={'ON (maxgen+tier)' if args.mode == 'main' else 'off'}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
