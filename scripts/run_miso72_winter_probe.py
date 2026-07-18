"""Driver: MISO 72 — winter fuel-security citygate daily overlay probe.

Replays the promoted MISO keeper ``2026-07-17-miso-71-midwest`` recipe (bundle
``results/calibration/miso71_midwest``) verbatim via
:func:`scripts.replay_keeper.build_kwargs` — the strict meta.json snapshot, which
carries the full keeper structure through its ``prb_overrides`` channel
(``miso_midwest_subregional_reserves`` etc.) — and composes ONE new mechanism:

  ``--winter`` -> ``miso_winter_citygate_daily=True`` (via prb_overrides).

The **base** run (no ``--winter``) is the same-box drift control: a byte-faithful
keeper replay, so ``main − base`` isolates the winter overlay. The overlay, in
Dec/Jan/Feb, reprices the Chicago-hub zones' gas units at the measured Chicago
Citygate daily shape (flow-date, mean-preserving), superseding the national HH
``gas_daily_shape`` in those cells — closing the Jan-14-17-2024 Winter Storm
Heather gas tail (design ``docs/handoffs/miso-winter-fuel-security-design-2026-07.md``).

Memory note (CLAUDE.md rule 1/12): the MISO per-plant multi-zone energy+reserve
co-opt LP peaks ~14-16 GB per year; run this SOLO (never concurrent with another
per-plant solve) with ``MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1
MARKET_SIM_HIGHS_THREADS=1`` so glibc returns freed heap between years — this is
what lets all three years fit in ONE process on a 15 GB host. Years solve
SEQUENTIALLY inside ``solve_and_persist`` (never parallelized). Holdout (rule 22):
2023-2025 only — MISO has no calibration-complete marker, so 2022/2019/H1-2026
are quarantined. ``--years`` narrows the span ONLY for a throwaway memory/
correctness smoke (never a registered single-year keeper, rule 16).

Usage:
    MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1 MARKET_SIM_HIGHS_THREADS=1 \\
      python scripts/run_miso72_winter_probe.py --winter --out-dir <dir>
    MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1 MARKET_SIM_HIGHS_THREADS=1 \\
      python scripts/run_miso72_winter_probe.py --out-dir <dir>            # base
    python scripts/run_miso72_winter_probe.py --winter --years 2024 --out-dir <smoke>
    python scripts/run_miso72_winter_probe.py --report-only --out-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

# Reproducibility pin (mirrors replay_keeper.py / _miso71_midwest_reserves.py):
# force cross-year LP warm-start OFF so each per-year process is basis-independent
# and the main/base pair is a clean same-box comparison. Set BEFORE importing the
# solve core.
os.environ.setdefault("MARKET_SIM_WARMSTART_XYEAR", "0")

import run_calibration_full as rcf  # noqa: E402
from scripts.replay_keeper import build_kwargs  # noqa: E402
from scripts.run_calibration_full import report_run  # noqa: E402

_KEEPER_BUNDLE = _REPO / "results/calibration/miso71_midwest"

_NOTE_MAIN = (
    "MISO 72 winter fuel-security citygate daily overlay (miso_winter_citygate_"
    "daily): miso-71-midwest keeper recipe re-solved at HEAD + the winter overlay "
    "— in Dec/Jan/Feb, reprice the Chicago-hub zones' (MISO-Illinois/Indiana/East) "
    "gas units at the measured Chicago Citygate daily shape (miso_citygate_daily."
    "csv, flow-date-placed, mean-preserving), superseding the national HH "
    "gas_daily_shape in those cells. Closes the Jan-14-17-2024 Winter Storm Heather "
    "gas tail. Zero fitted scalars (measured daily series + published Chicago-zone "
    "assignment). Recipe byte-unchanged vs miso-71; the only delta is the overlay."
)
_NOTE_BASE = (
    "MISO 72 base (same-box drift control): byte-faithful replay of the "
    "miso-71-midwest keeper recipe at HEAD, winter overlay OFF. main − base "
    "isolates miso_winter_citygate_daily."
)


def _solve(
    out_dir: Path,
    winter: bool,
    years: list[int],
    reuse_solved: Path | None = None,
) -> Path:
    """Replay the miso-71 keeper recipe into ``out_dir``; ``winter`` adds the overlay.

    ``reuse_solved`` (the per-year+reuse pattern, RAM ≤16 GB — the _miso71
    precedent): a prior accumulating bundle whose already-solved years are loaded
    and skipped, so each invocation solves exactly ONE new LP in a fresh process.
    The one-process all-three-years path OOMs on the year-3 co-opt peak at HEAD.
    """
    meta = json.loads((_KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs["years"] = years
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out_dir
    kwargs["reuse_solved"] = Path(reuse_solved) if reuse_solved else None
    kwargs["note"] = _NOTE_MAIN if winter else _NOTE_BASE
    if winter:
        # Compose the winter overlay on the keeper structure via the generic
        # prb_overrides channel (recorded into run_config.json — rule 24), applied
        # LAST so it wins over the (default-off) base flag. Copy the dict first:
        # build_kwargs maps meta's coal_prb_sigmoid_overrides to prb_overrides by
        # reference, so a bare mutation would edit the shared meta object.
        prb = dict(kwargs.get("prb_overrides") or {})
        prb["miso_winter_citygate_daily"] = True
        kwargs["prb_overrides"] = prb
    print(
        f"replaying {_KEEPER_BUNDLE.name} recipe -> {out_dir} "
        f"(years {years}, winter={winter}, reuse={reuse_solved})"
    )
    return rcf.solve_and_persist(**kwargs)


def main() -> int:
    """CLI: solve the requested years into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--winter",
        action="store_true",
        help="Enable miso_winter_citygate_daily (main); omit for the base control.",
    )
    ap.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2023, 2024, 2025],
        help="Solve span. In the per-year+reuse pattern this is the CUMULATIVE "
        "span (e.g. 2023 2024 with --reuse-solved <y2023>); reuse skips the "
        "already-solved years so exactly one new LP solves. A lone year is a "
        "throwaway smoke — never register a single-year bundle (rule 16).",
    )
    ap.add_argument(
        "--reuse-solved",
        type=Path,
        default=None,
        help="Prior accumulating bundle to reuse solved years from (RAM ≤16 GB: "
        "one fresh year per process). Configs must match (main→main, base→base).",
    )
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Skip solving; just score the existing (complete) bundle. Scoring is "
        "decoupled from solving so each solve process stays lean — run this as a "
        "SEPARATE pass on the final 3-year bundle.",
    )
    args = ap.parse_args()

    if args.report_only:
        report_run(args.out_dir, band_width=0.10)
    else:
        _solve(
            args.out_dir,
            winter=args.winter,
            years=args.years,
            reuse_solved=args.reuse_solved,
        )
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
