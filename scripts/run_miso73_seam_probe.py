"""Driver: MISO 73 — seam-envelope merit-cap composition-fix probe (G-23 lane).

Replays the promoted MISO keeper ``2026-07-18-miso-72-winter`` recipe (bundle
``results/calibration/miso72_winter_citygate``) verbatim via
:func:`scripts.replay_keeper.build_kwargs` — the strict meta.json snapshot, which
carries the full keeper structure through its ``prb_overrides`` channel
(``miso_winter_citygate_daily`` etc.) — and composes ONE change:

  ``--merit-cap`` -> ``miso_seam_envelope_merit_cap=True`` (via prb_overrides).

The **base** run (no ``--merit-cap``) is the same-box drift control: a
byte-faithful keeper replay, so ``main − base`` isolates the composition fix.
The fix applies the measured seam deliverability envelope with merit-order
(waterfall) band bounds instead of the uniform per-band derate — the G-23
residual root cause (the uniform-derate replay reproduces the keeper's solved
priced-seam net ±0.12 TWh in all three years; frozen charter
``docs/handoffs/miso-g23-seam-envelope-composition-design-2026-07.md``). Zero
new parameters; the envelope values, percentile, Q-Q ladder rungs and band
grid are byte-unchanged.

Memory note (CLAUDE.md rule 1/12): the MISO per-plant multi-zone energy+reserve
co-opt LP peaks ~14-16 GB per year; run this SOLO (never concurrent with another
per-plant solve) with ``MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1
MARKET_SIM_HIGHS_THREADS=1``. Years solve SEQUENTIALLY (never parallelized).
Holdout (rule 22): 2023-2025 only — MISO has no calibration-complete marker.
``--years`` narrows the span ONLY for a throwaway memory/correctness smoke
(never a registered single-year keeper, rule 16).

Usage:
    MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1 MARKET_SIM_HIGHS_THREADS=1 \\
      python scripts/run_miso73_seam_probe.py --merit-cap --out-dir <dir>
    MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1 MARKET_SIM_HIGHS_THREADS=1 \\
      python scripts/run_miso73_seam_probe.py --out-dir <dir>            # base
    python scripts/run_miso73_seam_probe.py --report-only --out-dir <dir>
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

# Reproducibility pin (mirrors replay_keeper.py / run_miso72_winter_probe.py):
# force cross-year LP warm-start OFF so each per-year process is basis-independent
# and the main/base pair is a clean same-box comparison. Set BEFORE importing the
# solve core.
os.environ.setdefault("MARKET_SIM_WARMSTART_XYEAR", "0")

import run_calibration_full as rcf  # noqa: E402
from scripts.replay_keeper import build_kwargs  # noqa: E402
from scripts.run_calibration_full import report_run  # noqa: E402

_KEEPER_BUNDLE = _REPO / "results/calibration/miso72_winter_citygate"

_NOTE_MAIN = (
    "MISO 73 seam-envelope merit-cap composition fix (miso_seam_envelope_merit_"
    "cap): miso-72-winter keeper recipe re-solved at HEAD + the G-23 composition "
    "fix — the measured (month x hod) seam deliverability envelope applied with "
    "merit-order (waterfall) band bounds (band k keeps clip(cap-(k-1)*step, 0, "
    "step); cheap base rungs full-width; seam total = min(cap, limit) exactly) "
    "instead of the uniform per-band derate, under which the seam reaches its "
    "cap only when the price clears the MOST EXPENSIVE Q-Q rung. Restores the "
    "measured ladder's price-to-depth pairing. Zero new parameters; envelope "
    "values, percentile, ladder rungs and band grid byte-unchanged. Recipe "
    "byte-unchanged vs miso-72; the only delta is the composition semantics."
)
_NOTE_BASE = (
    "MISO 73 base (same-box drift control): byte-faithful replay of the "
    "miso-72-winter keeper recipe at HEAD, merit-cap OFF. main − base isolates "
    "miso_seam_envelope_merit_cap."
)


def _solve(
    out_dir: Path,
    merit_cap: bool,
    years: list[int],
    reuse_solved: Path | None = None,
) -> Path:
    """Replay the miso-72 keeper recipe into ``out_dir``; ``merit_cap`` adds the fix.

    ``reuse_solved`` (the per-year+reuse pattern, RAM ≤16 GB — the _miso71/72
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
        # Compose the fix on the keeper structure via the generic prb_overrides
        # channel (recorded into run_config.json — rule 24), applied LAST so it
        # wins over the (default-off) base flag. Copy the dict first:
        # build_kwargs maps meta's coal_prb_sigmoid_overrides to prb_overrides
        # by reference, so a bare mutation would edit the shared meta object.
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
        help="Enable miso_seam_envelope_merit_cap (main); omit for the base control.",
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
