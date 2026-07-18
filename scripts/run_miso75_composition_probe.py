"""Driver: MISO 75 — {Manitoba seam + seam-envelope merit-cap} composition probe.

Replays the promoted MISO keeper ``2026-07-18-miso-74-manitoba-seam`` recipe
(bundle ``results/calibration/miso74_manitoba_seam``) verbatim via
:func:`scripts.replay_keeper.build_kwargs` — the strict meta.json snapshot, which
carries the full keeper structure through its ``prb_overrides`` channel
(``miso_winter_citygate_daily``, ``miso_manitoba_seam``, …) — and composes ONE
change:

  ``--merit-cap`` -> ``miso_seam_envelope_merit_cap=True`` (via prb_overrides).

Both mechanisms are already merged, default-off, and flow through the SAME
``transmission.inject_miso_seam_flow_limit`` path (no fork): the keeper's
``miso_manitoba_seam`` puts the two-way MHEB seam's bands into the working seam
set, and ``miso_seam_envelope_merit_cap`` selects the merit-order (waterfall)
envelope semantics — ``ub_k = clip(cap-(k-1)*step, 0, step)`` — over EVERY seam
including Manitoba, in place of the uniform per-band derate. This is the
pre-registered composition of the miso-74 Manitoba seam and the miso-73 merit
cap (miso-74 charter §3d/§8, miso-73 charter §5 R1): the merit cap restores the
priced-seam import volume the uniform derate suppressed (PJM -5.6/-8.3/-8.9,
South export +2.8/+2.6/+3.1 TWh), closing the miso-74 keeper's net-interchange
gap (-5.46/-7.38/-7.27 TWh); the hypothesis is that Manitoba's 2025 supply
removal (which un-flattened C3b-2025 0.183->0.181) keeps C3b <= 0.20 where the
merit cap alone flattened it to 0.200. Zero new parameters — a semantics gate,
no scalars. Frozen charter:
``docs/handoffs/miso-manitoba-meritcap-composition-design-2026-07.md``.

The **base** run (no ``--merit-cap``) is the same-box drift control: a
byte-faithful miso-74 keeper replay (Manitoba on, merit cap OFF — the keeper's
setting), so ``main - base`` isolates the merit-cap semantics on the Manitoba
base.

Memory note (CLAUDE.md rule 1/12): the MISO per-plant multi-zone energy+reserve
co-opt LP peaks ~14-16 GB per year; run this SOLO (never concurrent with another
per-plant solve) with ``MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1
MARKET_SIM_HIGHS_THREADS=1``. Years solve SEQUENTIALLY (never parallelized).
Holdout (rule 22): 2023-2025 only — MISO has no calibration-complete marker.
``--years`` narrows the span ONLY for a throwaway memory/correctness smoke
(never a registered single-year keeper, rule 16).

Usage:
    MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1 MARKET_SIM_HIGHS_THREADS=1 \\
      python scripts/run_miso75_composition_probe.py --merit-cap --out-dir <dir>
    MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1 MARKET_SIM_HIGHS_THREADS=1 \\
      python scripts/run_miso75_composition_probe.py --out-dir <dir>          # base
    python scripts/run_miso75_composition_probe.py --report-only --out-dir <dir>
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

# Reproducibility pin (mirrors replay_keeper.py / run_miso74_manitoba_probe.py):
# force cross-year LP warm-start OFF so each per-year process is basis-independent
# and the main/base pair is a clean same-box comparison. Set BEFORE importing the
# solve core.
os.environ.setdefault("MARKET_SIM_WARMSTART_XYEAR", "0")

import run_calibration_full as rcf  # noqa: E402
from scripts.replay_keeper import build_kwargs  # noqa: E402
from scripts.run_calibration_full import report_run  # noqa: E402

_KEEPER_BUNDLE = _REPO / "results/calibration/miso74_manitoba_seam"

_NOTE_MAIN = (
    "MISO 75 {Manitoba seam + merit-cap} composition (miso_manitoba_seam + "
    "miso_seam_envelope_merit_cap): miso-74-manitoba-seam keeper recipe re-solved "
    "at HEAD + the merit-cap semantics. The measured seam deliverability envelope "
    "is applied as a merit-order (waterfall) ceiling ub_k=clip(cap-(k-1)*step,0,"
    "step) over EVERY seam (PJM/SPP/South AND the two-way Manitoba seam) via the "
    "shared inject_miso_seam_flow_limit path (no fork), replacing the uniform "
    "per-band derate that suppressed priced-seam imports. Restores the PJM/South "
    "import volume (the keeper's -5.46/-7.38/-7.27 TWh net-interchange gap) while "
    "Manitoba's 2025 supply removal aims to hold C3b<=0.20 where the merit cap "
    "alone flattened it to 0.200. Zero new parameters (a composition-semantics "
    "gate). Recipe otherwise byte-unchanged vs miso-74; the only delta is the "
    "merit-cap flag."
)
_NOTE_BASE = (
    "MISO 75 base (same-box drift control): byte-faithful replay of the "
    "miso-74-manitoba-seam keeper recipe at HEAD, Manitoba two-way seam intact, "
    "seam-envelope merit-cap OFF (the keeper's uniform per-band derate). "
    "main - base isolates the merit-cap semantics on the Manitoba base."
)


def _solve(
    out_dir: Path,
    merit_cap: bool,
    years: list[int],
    reuse_solved: Path | None = None,
) -> Path:
    """Replay the miso-74 keeper recipe into ``out_dir``; ``merit_cap`` composes.

    ``reuse_solved`` (the per-year+reuse pattern, RAM ≤16 GB — the _miso71..74
    precedent): a prior accumulating bundle whose already-solved years are loaded
    and skipped, so each invocation solves exactly ONE new LP in a fresh process.
    """
    meta = json.loads((_KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs["years"] = years
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out_dir
    kwargs["reuse_solved"] = Path(reuse_solved) if reuse_solved else None
    kwargs["note"] = _NOTE_MAIN if merit_cap else _NOTE_BASE
    if merit_cap:
        # Compose the merit cap on the keeper structure via the generic
        # prb_overrides channel (recorded into run_config.json — rule 24),
        # applied LAST so it wins over the (default-off) base flag. Copy the dict
        # first: build_kwargs maps meta's coal_prb_sigmoid_overrides to
        # prb_overrides by reference, so a bare mutation would edit the shared
        # meta object.
        prb = dict(kwargs.get("prb_overrides") or {})
        prb["miso_seam_envelope_merit_cap"] = True
        kwargs["prb_overrides"] = prb
    print(
        f"replaying {_KEEPER_BUNDLE.name} recipe -> {out_dir} "
        f"(years {years}, merit_cap={merit_cap}, reuse={reuse_solved})"
    )
    return rcf.solve_and_persist(**kwargs)


def main() -> int:
    """CLI: solve the requested years into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--merit-cap",
        action="store_true",
        help="Enable miso_seam_envelope_merit_cap (main); omit for the base "
        "control (the keeper's uniform per-band derate).",
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
        help="Skip solving; just score the existing (complete) bundle.",
    )
    args = ap.parse_args()

    if args.report_only:
        report_run(args.out_dir, band_width=0.10)
    else:
        _solve(
            args.out_dir,
            merit_cap=args.merit_cap,
            years=args.years,
            reuse_solved=args.reuse_solved,
        )
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
