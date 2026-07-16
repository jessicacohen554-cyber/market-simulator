"""miso-69 probe: declared-event-window revealed derates (M-2, composed).

Replays the MISO keeper (``miso68_cottonwood_mothballs``) meta.json STRICTLY
via ``replay_keeper.build_kwargs`` (the sanctioned single-source recipe
reconstruction) and applies ONE single-delta override through the generic
``prb_overrides`` ScenarioConfig channel:

    main : unit_outage_maxgen_events = True   (the M-2 channel under test)
    base : (nothing added)                    same-box unchanged-recipe replica

The mechanism (design ``docs/handoffs/miso-price-formation-design-2026-07.md``
§3/M-2, registry adjudications ``docs/handoffs/miso-maxgen-registry-findings-
2026-07.md``): CAMPD revealed unit derates INSIDE the ISO's declared
capacity-emergency windows only (``maxgen-events`` registry, 8 qualifying
windows -> 5 event blocks 2023-2025), under the frozen identification guards
(declared-window scope clipped to the declared start/end; $150 DA in-merit
certificate, region-scoped hubs; ±45-day capability basis with
best-event-hour credit; disjointness vs the std/short extracts; NO
control-day screen). Extract: ``data/raw/campd-unit-outages-maxgen-MISO.csv``
(``scripts/derive_campd_maxgen_outages.py``). Zero fitted scalars — every
number is a declared instrument, a measured price certificate, or a measured
CAMPD capability. Never an outcome pin: dispatch inside windows stays free
above the derate; prices are never touched directly (rules 1/11/13).

The base is the DRIFT CONTROL: the mechanism-only footprint is main - base
(both solved in THIS box / code state), never main - the registered miso-68
bundle. No zero-forcing ablation twin (rule 20 as amended 2026-07-14).

PER-YEAR + REUSE (RAM <=16 GB): each invocation solves exactly ONE new LP.
Sequence (per variant):

    python scripts/probes/_miso69_maxgen_derates.py <main|base> \\
        --out-dir <acc>/y2023 --years 2023
    python scripts/probes/_miso69_maxgen_derates.py <main|base> \\
        --out-dir <acc>/y2024 --years 2023,2024 --reuse-solved <acc>/y2023
    python scripts/probes/_miso69_maxgen_derates.py <main|base> \\
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
    # p25 recipe + carry_operating_mothballs) — the M-2 delta stacks on THAT.
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
    if prb.get("unit_outage_maxgen_events"):
        raise SystemExit(
            "base recipe already arms unit_outage_maxgen_events — the probe "
            "delta would be a no-op; wrong base bundle"
        )

    if args.mode == "main":
        # The single delta under test: declared-event-window revealed derates.
        prb = dict(prb)
        prb["unit_outage_maxgen_events"] = True
        kwargs["prb_overrides"] = prb

    note = (
        f"miso-69 ({args.mode}) -- declared-event-window revealed derates "
        "(M-2 of the MISO price-formation lane): the miso-68 keeper recipe "
        "plus the gated unit_outage_maxgen_events channel — CAMPD revealed "
        "unit derates inside the ISO's DECLARED capacity-emergency windows "
        "only (maxgen-events registry, 8 qualifying windows -> 5 event "
        "blocks: Aug-24-2023 Step-2A, Aug-26-2024 Warning, Jun-23/24-2025 "
        "EEA1+Warning (Midwest), Jul-24-2025 Capacity Advisory, "
        "Jul-28/29-2025 Advisory+Alert+Warning), under the frozen guards "
        "(declared-window scope; $150 DA in-merit certificate, "
        "region-scoped; ±45-day capability basis with best-event-hour "
        "credit; disjointness vs std/short extracts asserted; no "
        "control-day screen). Class-agnostic — the only channel that can "
        "carry the measured CT/CC event-window leg. Targets the phantom "
        "event-window headroom behind C3a-2025 Jun/Jul and the C3c-2025 "
        "in-window tail hours (26/38); C3c-2024 expectation retired "
        "(Jan-2024 carries no declaration — registry findings §1). Zero "
        "fitted scalars; availability truth, never an outcome pin (rules "
        "1/11/13). base = unchanged-recipe same-box drift control "
        "(mechanism-only = main - base). No ablation twin (rule 20 amended "
        "2026-07-14). Design: docs/handoffs/miso-price-formation-design-"
        "2026-07.md §3/M-2 + docs/handoffs/miso-maxgen-registry-findings-"
        "2026-07.md."
    )

    kwargs["years"] = years
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["reuse_solved"] = Path(args.reuse_solved) if args.reuse_solved else None
    kwargs["note"] = note

    print(
        f"miso-69 {args.mode}: years={years} out={args.out_dir} "
        f"reuse={args.reuse_solved} "
        f"maxgen={'ON' if args.mode == 'main' else 'off'}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
