"""Drive the pjm-151 PJM seam-envelope attribution arm (PREREG-pjm151).

Adapted from ``pjm150_ct_regate_arm.py``. **One arm, not two**, and PREREG-pjm151
K2 says why: pjm-150 measured the keeper reproducing bit-identically at HEAD
``01b6a6a`` (max |dMW| = 0.000000 over 499,320 P1 class-hours), only two
``src/market_sim/`` commits have landed since, and both are provably PJM-inert by
inspection (``5b04fab`` is docstring text in ``model/reserves/spec.py``;
``fcdcac0`` adds one NYISO entry to the cache-key defaults ledger). The session's
own change is a default-OFF flag whose entire effect sits inside
``if by_neighbor:``. So the CONTROL is the committed keeper bundle and only the
TREATMENT needs a solve.

The single delta, and nothing else, is
``pjm_seam_envelope_by_neighbor=true``: build each reference-price seam's measured
deliverability envelope from THAT SEAM'S OWN ties instead of summing a
per-model-ZONE envelope over the neighbour's ``border_zones``.

Three failure modes this script exists to make impossible:

1. **Stale cache.** ``ScenarioConfig.cache_key`` hashes config FIELDS ONLY, so it
   never sees an input artifact's bytes; ``results/PJM`` is scrubbed before the
   FIRST year of the chain (and deliberately NOT between chained years, whose
   later invocations byte-copy earlier years via ``--reuse-solved``).
2. **A missing hard input.** ``pjm_da_virtual_bids`` is armed on the keeper and
   ``virtual_bids.py`` hard-fails without ``data/raw/pjm-da-virtuals/`` (gitignored,
   empty on a fresh container). Checked up front rather than 8 minutes into a solve.
3. **Silent recipe drift.** Exactly one ``--set``, asserted here in one place, so
   the config delta against the keeper is auditable rather than narrated.

Rule 12's per-year invocation chain keeps all three years in ONE bundle (rule 16)
while giving each year a fresh process — a PJM per-plant multi-zone LP with
``ramp_limits=True`` peaks ~15.5 GB RSS, so heap fragmentation across years is what
OOMs the box, not any single year. ``--out-dir X --reuse-solved X`` raises
``shutil.SameFileError`` in ``run_calibration_full._copy_reused_year``, so the chain
walks SEPARATE directories and this script refuses a self-reuse up front.

Usage::

    python scripts/probes/pjm151_seam_arm.py --year 2023 --out pjm151_seam_y23
    python scripts/probes/pjm151_seam_arm.py --year 2023 2024 \\
        --out pjm151_seam_y24 --reuse-from pjm151_seam_y23
    python scripts/probes/pjm151_seam_arm.py --year 2023 2024 2025 \\
        --out pjm151_seam_B --reuse-from pjm151_seam_y24
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/pjm147_chp_B"
VIRTUALS = REPO / "data/raw/pjm-da-virtuals"

#: The ONE pre-registered delta (PREREG-pjm151 §4).
DELTA = "pjm_seam_envelope_by_neighbor=true"

NOTE = (
    "pjm-151 arm B: PJM reference-price seam deliverability envelopes built "
    "PER-NEIGHBOUR from each seam's own ties (spec.PJM_TIE_NEIGHBOR) instead of "
    "summing a per-model-ZONE envelope over the neighbour's border_zones. Rule 14 "
    "[R-ACCURATE] internal-consistency repair of keeper-note item 12, off-queue as "
    "a NEW measured identification (rule 28a) -- the PJM price-formation frontier "
    "is owner-declared and this is not a price lever. ZERO new parameters: the "
    "tie->interface map is an identity read off PJM's own tie labels. Measured ex "
    "ante at p90: the legacy TVA export cap ran 124x/53x/40x the direct one and "
    "never bound, LGEE's 33x/42x/26x; the legacy LGEE import cap is 0 MW against a "
    "measured 518/539/549 MW, so the repair loosens as well as tightens. NYISO "
    "reproduces at 1.00x -- the control. Single delta vs keeper pjm147_chp_B: " + DELTA
)


def scrub_cache() -> None:
    """Remove the global per-ISO results tree so the next solve is cold.

    ``runner.py`` short-circuits on ``results/<ISO>/<cache_key>/`` and the cache key
    never sees an input artifact's bytes, so this is the ONLY thing standing between
    a recipe-near-identical replay and a silently reused solve.
    """
    tree = REPO / "results/PJM"
    if tree.exists():
        shutil.rmtree(tree)
        print(f"[cold] removed {tree.relative_to(REPO)}")
    else:
        print("[cold] results/PJM already absent")


def check_virtuals(years: list[int]) -> None:
    """Fail fast when the keeper's DA virtual-bid feed is not on disk.

    ``data/raw/pjm-da-virtuals/`` is gitignored and README-only on a fresh
    container; ``pjm_da_virtual_bids`` is armed on the keeper and
    ``virtual_bids.py`` correctly raises ``FileNotFoundError`` rather than
    no-opping. Refetch with ``scripts/data/fetch_pjm_da_virtuals.py``.
    """
    missing = [
        y for y in years if not list(VIRTUALS.glob(f"hrl_da_incs_decs_{y}_*.parquet"))
    ]
    if missing:
        raise SystemExit(
            f"data/raw/pjm-da-virtuals has no hrl_da_incs_decs parquet for "
            f"{missing} — the keeper arms pjm_da_virtual_bids and the loader "
            "hard-fails. Run: uv run python scripts/data/fetch_pjm_da_virtuals.py "
            "--years 2023 2024 2025 --feeds hrl_da_incs_decs"
        )
    n = len(list(VIRTUALS.glob("*.parquet")))
    print(f"[pjm-151] DA virtual-bid feed present: {n} parquet(s)")


def main() -> None:
    """Run one link of the rule-12 chain for pjm-151 arm B."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--year",
        nargs="+",
        type=int,
        required=True,
        help="years for THIS invocation of the rule-12 chain; every year but the "
        "last is byte-copied forward from the PRIOR link's bundle",
    )
    ap.add_argument(
        "--out",
        required=True,
        help="bundle dir for THIS link, relative to results/calibration",
    )
    ap.add_argument(
        "--reuse-from",
        default=None,
        help="prior link's bundle dir (relative to results/calibration) whose "
        "already-solved years byte-copy forward. MUST NOT equal --out.",
    )
    args = ap.parse_args()

    years = [int(y) for y in args.year]
    bad = [y for y in years if y not in (2023, 2024, 2025)]
    if bad:
        raise SystemExit(
            f"rule 22 [R-HOLDOUT]: {bad} is outside the 2023-2025 training tier; "
            "PJM holds `complete` (2022 only) and is absent from `final`"
        )

    out_dir = REPO / "results/calibration" / args.out
    reuse = REPO / "results/calibration" / args.reuse_from if args.reuse_from else None
    if reuse is not None and reuse.resolve() == out_dir.resolve():
        raise SystemExit("--reuse-from must differ from --out (SameFileError)")

    check_virtuals(years)

    if reuse is None:
        scrub_cache()
    else:
        print("[cold] chained invocation — results/PJM kept for --reuse-solved")

    cmd = [
        sys.executable,
        "scripts/replay_keeper.py",
        str(KEEPER.relative_to(REPO)),
        "--out-dir",
        str(out_dir.relative_to(REPO)),
        "--years",
        *[str(y) for y in years],
        "--set",
        DELTA,
        "--note",
        NOTE,
    ]
    if reuse is not None:
        cmd += ["--reuse-solved", str(reuse.relative_to(REPO))]

    print(f"[pjm-151] years={years} out={args.out} reuse={args.reuse_from}")
    print(f"[pjm-151] single delta: {DELTA}")
    subprocess.run(cmd, cwd=REPO, check=True)


if __name__ == "__main__":
    main()
