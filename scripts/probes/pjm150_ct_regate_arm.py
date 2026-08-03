"""Drive the pjm-150 PJM CT heat-rate re-gate arm, enforcing the lane's rules.

Adapted from ``caiso160_nyiso_ct_arms.py``. **One arm, not two** — and that is
the whole result, not a shortcut:

``PREREG-pjm150`` §1 measures that the PJM keeper ``pjm147_chp_B`` solved at
basis ``217e5b1``, a DESCENDANT of the caiso-156 fix ``f6238a5``, so it already
consumed the CORRECTED artifact (md5 ``32c26167…``). Arm B's condition is
therefore the incumbent's condition and there is no A/B left to run. What
``pjm-147`` could NOT deliver is a bit-identity check: its own K2 gate failed by
construction because its comparison spanned two HEADs. So this arm replays the
keeper recipe COLD at THIS HEAD against the SAME artifact and diffs every P1
class-hour against the committed keeper — the charter's K2, and the first test
of the caiso-146 HEAD-drift item in PJM.

Three failure modes this script exists to make impossible:

1. **Stale cache.** ``ScenarioConfig.cache_key`` hashes config FIELDS ONLY, so a
   replay of the keeper's own recipe shares its key exactly and ``runner.py``
   would short-circuit onto any persisted tree (caiso-158 §4a). ``results/PJM``
   is scrubbed before the FIRST year of the chain. It is deliberately NOT
   scrubbed between chained years — the chain's later invocations byte-copy the
   earlier years via ``--reuse-solved`` and must not re-solve them.
2. **Wrong artifact.** The artifact is md5-verified against the expected blob
   immediately before each invocation. This arm installs nothing, so there is no
   restore path to get wrong; a mismatch means someone else moved the bytes.
3. **Silent recipe drift.** No ``--set`` on any invocation, so the config delta
   against the keeper is structurally zero rather than asserted.

Rule 12's per-year invocation chain keeps all three years in ONE bundle
(rule 16) while giving each year a fresh process — a PJM per-plant multi-zone LP
with ``ramp_limits=True`` peaks ~15.5 GB RSS, so heap fragmentation across years
is what OOMs the box, not any single year.

Usage::

    python scripts/probes/pjm150_ct_regate_arm.py --year 2023 \\
        --out pjm150_regate_y23
    python scripts/probes/pjm150_ct_regate_arm.py --year 2023 2024 \\
        --out pjm150_regate_y24 --reuse-from pjm150_regate_y23
    python scripts/probes/pjm150_ct_regate_arm.py --year 2023 2024 2025 \\
        --out pjm150_ctmeter_regate_A --reuse-from pjm150_regate_y24
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROCESSED = REPO / "data/raw/_processed-legacy"
KEEPER = REPO / "results/calibration/pjm147_chp_B"

#: Only the plant-level artifact reaches the LP (``campd_bins.py:266``); the
#: units file carries no pin for the same reason caiso-160 gave.
ARTIFACT = "campd_ct_heat_rates_PJM.csv"

#: md5 of the POST-FIX blob this arm must solve against — the same bytes the
#: keeper consumed. Measured from both blobs in ``PREREG-pjm150`` §1
#: (pre-fix ``8d48c2bb98d2ce044bed2a438d4b87ec``, applied cap-weighted
#: 11.5817 -> 11.6511).
EXPECTED_MD5 = "32c26167d83869cff798a2f5cb274106"

NOTE = (
    "pjm-150 K2 re-gate arm: the pjm-147 keeper recipe replayed COLD at HEAD "
    "against the SAME (corrected) CT heat-rate artifact it solved on "
    "(f6238a5, applied cap-weighted 11.6511). Zero config delta vs the keeper "
    "-- no --set. NOT an A/B arm: PREREG-pjm150 measures that the keeper "
    "already consumed the corrected bytes, so this single arm is both control "
    "and treatment, and its only question is bit-identity against the "
    "committed keeper across the 11 src/market_sim commits that landed after "
    "it solved (charter K2; the caiso-146 HEAD-drift item, untested in PJM)."
)


def md5(path: Path) -> str:
    """Return the hex md5 of a file's bytes."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def scrub_cache() -> None:
    """Remove the global per-ISO results tree so the next solve is cold.

    ``runner.py`` short-circuits on ``results/<ISO>/<cache_key>/`` and the cache
    key never sees an input artifact's bytes, so this is the ONLY thing standing
    between a recipe-identical replay and a silently reused solve.
    """
    tree = REPO / "results/PJM"
    if tree.exists():
        shutil.rmtree(tree)
        print(f"[cold] removed {tree.relative_to(REPO)}")
    else:
        print("[cold] results/PJM already absent")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--year",
        nargs="+",
        type=int,
        required=True,
        help="years for THIS invocation of the rule-12 chain; every year but "
        "the last is byte-copied forward from the PRIOR link's bundle",
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
        "already-solved years byte-copy forward. MUST NOT be --out: "
        "run_calibration_full._copy_reused_year shutil.copy2's each dispatch "
        "parquet from the source into the destination, so a self-reuse "
        "(--out-dir X --reuse-solved X) raises SameFileError. The chain "
        "therefore walks SEPARATE directories, which is what pjm-147 did "
        "(its meta records source_bundle pjm147_chp_B_y24).",
    )
    args = ap.parse_args()
    years = [int(y) for y in args.year]
    out_dir = REPO / "results/calibration" / args.out
    reuse = REPO / "results/calibration" / args.reuse_from if args.reuse_from else None
    if reuse is not None and reuse.resolve() == out_dir.resolve():
        raise SystemExit("--reuse-from must differ from --out (SameFileError)")

    got = md5(PROCESSED / ARTIFACT)
    if got != EXPECTED_MD5:
        raise SystemExit(
            f"CT artifact md5 {got} != expected {EXPECTED_MD5} -- refusing to "
            "solve against the wrong input"
        )
    print(f"[pjm-150] CT artifact verified: md5 {got}")

    if reuse is None:
        scrub_cache()
    else:
        print("[cold] chained invocation -- results/PJM kept for --reuse-solved")

    cmd = [
        sys.executable,
        "scripts/replay_keeper.py",
        str(KEEPER.relative_to(REPO)),
        "--out-dir",
        str(out_dir.relative_to(REPO)),
        "--years",
        *[str(y) for y in years],
        "--note",
        NOTE,
    ]
    if reuse is not None:
        cmd += ["--reuse-solved", str(reuse.relative_to(REPO))]

    print(f"[pjm-150] years={years} out={args.out} reuse={args.reuse_from}")
    subprocess.run(cmd, cwd=REPO, check=True)


if __name__ == "__main__":
    main()
