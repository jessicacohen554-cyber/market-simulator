"""Driver: NEISO 54 — CT_PEAKER evening-ramp drag + ST_GAS→Component-B consolidation.

The neiso-53 keeper recipe (`2026-07-07-neiso53-winter-fuelsec-coldsnap`,
docs/handoffs/neiso-calibration-complete-memo-2026-07.md §1) re-solved on the
current data tree so it absorbs ONE structural correction that lives entirely in
base data (`reliability_floor_coeffs_NEISO.csv`) — the recipe (CLI flags) is
byte-unchanged and the only delta vs neiso-53 is the NEISO extreme-day
reliability drag:

1. **CT_PEAKER evening-ramp reliability drag** (headline). Within the
   `reliability_floor` engine, NEISO CT_PEAKER now carries evening-windowed
   [15,21] tmax/netload limbs at `commit_frac × min_stable` (0.38): on a hot
   design-cooling or high-net-load day the simple-cycle peakers are committed for
   local Resource Adequacy through the afternoon-evening net-load ramp (cooling
   load climbs while solar collapses at sunset), the hours their measured CAMPD CF
   genuinely rises with the driver. 5 limbs enabled (Boston tmax+netload,
   Connecticut tmax+netload, North netload) where real (ρ≥0.3, n≥30,
   commit>baseline); the cold (tmin) limbs derive below-gate and ship disabled.
   Replaces the all-24h CT limbs scrubbed 2026-07-05 (D-4 off-window / rule 18);
   the evening window fixes the off-window binding and the diurnal-flattening.
   CT_PEAKER is ~0.4 % of ISO load (<2 %), so its 26-30 % in-window forced share
   is reported-not-gated (rule 20 v2.1 materiality floor).
2. **ST_GAS → Component B consolidation** (rule 14/19). The lone 81 MW NEISO
   ST_GAS unit sits inside a 491 MW mixed CAMPD facility (code 546), so no clean
   pure-play commitment signal can be measured; its (now-visible, disabled)
   reliability limbs are placeholders. With no *enabled* ST_GAS netload limb, the
   existing run_calibration reconciliation keeps ST_GAS inside the winter
   fuel-security must-run (Component B), which floors the model's 81 MW ST_GAS
   all-day on Nov-Mar cold days (WRP/IEP/OFSA posture) — ONE program-grounded
   mechanism for the ST_GAS phenomenon, replacing the contaminated all-day netload
   limb it superseded.

Recipe = the neiso-53 keeper CLI (the neiso-50 base — `--commitment
--reliability-floor --hydro-backfill-year 2024 --hydro-eia930-monthly
--gas-hub-basis-daily --scarcity-price-overlay --tranche-startup-amortization` —
plus the three winter fuel-security mechanisms `--neiso-gas-coldsnap-derate
--neiso-winter-fuel-inventory --neiso-winter-fuel-mustrun`). `--commitment` runs
the ARCHIVED P2 pass the frozen neiso-53 keeper used, so it is unlocked here with
`--enable-legacy-p2` to keep the drag the *only* delta vs neiso-53 (a clean A/B);
no new P2 dependency is introduced.

Holdout discipline (CLAUDE.md rule 22): NEISO is calibration-complete
(marker 2026-07-07, keeper neiso-53). This driver re-tunes ONLY the train tier
(2023-2025). The locked-test one-shot (2019, H1-2026) was scored on neiso-53 and
STANDS — it is NOT re-scored for neiso-54.

Memory (task guidance): all three years solve SEQUENTIALLY in ONE process behind
`MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=2` — without the arena cap the 2nd year OOMs
on a ≤15 GB host (PJM's 3-year run peaked 12.7 GB with the cap). The year loop in
`runner.py` is intentionally sequential (rule 1); this driver never parallelizes
years.

Usage:
    python scripts/run_neiso54_steamgas_ct_drag.py                 # solve + report
    python scripts/run_neiso54_steamgas_ct_drag.py --report-only   # score only
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

_DEFAULT_OUT = _REPO / "results" / "calibration" / "neiso54_steamgas_ct_drag"

# The neiso-53 keeper recipe (docs/handoffs/neiso-calibration-complete-memo-2026-07.md
# §1). Every other config value is a NEISO CLI/backcast default (coal PRB sigmoid +
# tiered ON by default, oil-burn-budget default-ON for NEISO, etc.).
_RECIPE_FLAGS = [
    "--commitment",
    "--enable-legacy-p2",  # unlock the archived P2 the frozen neiso-53 keeper used
    "--reliability-floor",
    "--hydro-backfill-year",
    "2024",
    "--hydro-eia930-monthly",
    "--gas-hub-basis-daily",
    "--scarcity-price-overlay",
    "--tranche-startup-amortization",
    "--neiso-gas-coldsnap-derate",
    "--neiso-winter-fuel-inventory",
    "--neiso-winter-fuel-mustrun",
]

_YEARS = ["2023", "2024", "2025"]


def _solve(out_dir: Path) -> None:
    """Solve NEISO 2023-2025 with the neiso-53 recipe into ``out_dir``.

    Shells out to ``run_calibration_full.py`` (the documented reproduce path) so
    every NEISO default is applied identically to neiso-53; the only delta is the
    committed ``reliability_floor_coeffs_NEISO.csv`` drag. All three years run in
    ONE process behind the memory caps (task guidance).
    """
    env = dict(os.environ)
    env.setdefault("MALLOC_ARENA_MAX", "2")
    env.setdefault("OMP_NUM_THREADS", "2")
    cmd = [
        sys.executable,
        str(_REPO / "scripts" / "run_calibration_full.py"),
        "--iso",
        "NEISO",
        "--year",
        *_YEARS,
        *_RECIPE_FLAGS,
        "--out-dir",
        str(out_dir),
    ]
    print("+ MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=2 \\\n  " + " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(_REPO), env=env)


def _report(out_dir: Path) -> None:
    """Score the existing bundle over all years (verdict + metrics)."""
    subprocess.run(
        [
            sys.executable,
            str(_REPO / "scripts" / "calibration_verdict.py"),
            str(out_dir),
        ],
        check=False,
        cwd=str(_REPO),
    )


def main() -> int:
    """CLI: solve NEISO 2023-2025 into ``--out-dir`` (or ``--report-only``)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Skip solving; just score the existing bundle over all years.",
    )
    args = ap.parse_args()

    if not args.report_only:
        _solve(args.out_dir)
    _report(args.out_dir)
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
