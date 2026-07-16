"""miso-68 probe: mothballed-but-operating re-carry (the Cottonwood lane).

Replays the MISO keeper (``miso67_stgas_vlr_level``) meta.json STRICTLY via
``replay_keeper.build_kwargs`` (the sanctioned single-source recipe
reconstruction — no lossy channel; miso-50..53 regression closure) and applies
ONE single-delta override through its dedicated solve kwarg:

    main : carry_operating_mothballs = True   (the re-carry channel under test)
    base : (nothing added)                    same-box unchanged-recipe replica

The mechanism (charter ``docs/handoffs/miso-cc-vintage-undercarry-plan-
2026-07.md`` §5/§7, scoped option (a) + the vintage-status oracle): re-carry
each OA unit the canonical snapshot's OP filter drops for solve year Y iff it
is OP in the year-matched EIA-860 vintage_<Y> — EIA's own contemporaneous
status, zero fitted DOF. Per-unit, ISO-agnostic, backcast-only. For MISO this
re-carries Cottonwood 55358's four OA units (~572.6 MW vintage_2023 /
~568.7 MW vintage_2024, CC_REGULAR, MISO-South — the CAMPD-demonstrated
capability behind the keeper's sole C1 fail, CC_REGULAR-2023 volume −9.79)
plus ~35 MW of small partial-mothball plants the general rule sweeps up.
2025 has no committed vintage: nothing is carried (the accepted 2025
under-carry, charter §10 owner default). Never a CAMPD-MWh pin, never a MW
offset (rules 1/11/13).

The base is the DRIFT CONTROL: the mechanism-only footprint is main - base
(both solved in THIS box / code state), never main - the registered miso-67
bundle (the miso-66 drift lesson). No zero-forcing ablation twin (rule 20 as
amended 2026-07-14).

PER-YEAR + REUSE (RAM <=16 GB, charter §8): each invocation solves exactly
ONE new LP. Pass the accumulating year list, the destination dir, and the
prior step's dir as ``--reuse-solved``; the years already present are
byte-copied and only the newest year is solved. Sequence (per variant):

    python scripts/probes/_miso68_cottonwood_mothballs.py <main|base> \\
        --out-dir <acc>/y2023 --years 2023
    python scripts/probes/_miso68_cottonwood_mothballs.py <main|base> \\
        --out-dir <acc>/y2024 --years 2023,2024 --reuse-solved <acc>/y2023
    python scripts/probes/_miso68_cottonwood_mothballs.py <main|base> \\
        --out-dir <acc>/final --years 2023,2024,2025 --reuse-solved <acc>/y2024

The final 3-year bundle is ``<acc>/final`` (rule 16 — one bundle, all years).
Years ALWAYS sequential within a run (rule 12).

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

KEEPER = REPO / "results" / "calibration" / "miso67_stgas_vlr_level"


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
    # Sanity: the base recipe MUST be the miso-67 keeper (the ST_GAS p25 level
    # riding prb_overrides) — the mechanism-only delta stacks on THAT recipe.
    prb = kwargs.get("prb_overrides") or {}
    if not (
        prb.get("st_gas_mustrun_per_plant") and prb.get("st_gas_mustrun_p25_level")
    ):
        raise SystemExit(
            "miso-67 meta missing st_gas_mustrun_per_plant/st_gas_mustrun_p25_level "
            "in prb_overrides — wrong base bundle"
        )
    if kwargs.get("carry_operating_mothballs"):
        raise SystemExit(
            "base recipe already arms carry_operating_mothballs — the probe "
            "delta would be a no-op; wrong base bundle"
        )

    if args.mode == "main":
        # The single delta under test: the mothballed-but-operating re-carry.
        kwargs["carry_operating_mothballs"] = True

    note = (
        f"miso-68 ({args.mode}) -- mothballed-but-operating re-carry (the "
        "Cottonwood lane): the miso-67 keeper recipe plus the gated "
        "carry_operating_mothballs channel — re-carry each OA unit the "
        "canonical 2025ER snapshot's OP filter drops for solve year Y iff it "
        "is OP in the year-matched EIA-860 vintage_<Y> (the zero-DOF "
        "vintage-status availability oracle; a unit truly idle in Y is OA in "
        "vintage_<Y> too). Per-unit: Cottonwood 55358's partial mothball "
        "(4 of 8 units OA, ~572.6 MW vintage_2023 / ~568.7 MW vintage_2024, "
        "CC_REGULAR MISO-South; CAMPD shows the OA CTs running 88-91% of "
        "2023 hours) re-carries only its OA-but-operating units; 2025 has no "
        "committed vintage and carries nothing (accepted under-carry, "
        "charter owner default). Targets the keeper's sole C1 fail "
        "CC_REGULAR-2023 volume (-9.79) at its root (the ~570 MW fleet "
        "under-carry the 2026-07-16 bisect exposed) — real units at "
        "availability bounds, never a CAMPD-MWh pin or a MW offset (rules "
        "1/11/13). Zero fitted scalars. base = unchanged-recipe same-box "
        "drift control (mechanism-only = main - base). No ablation twin "
        "(rule 20 amended 2026-07-14). Design: "
        "docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md §5-§8."
    )

    kwargs["years"] = years
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["reuse_solved"] = Path(args.reuse_solved) if args.reuse_solved else None
    kwargs["note"] = note

    print(
        f"miso-68 {args.mode}: years={years} out={args.out_dir} "
        f"reuse={args.reuse_solved} "
        f"mothballs={'ON' if args.mode == 'main' else 'off'}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
