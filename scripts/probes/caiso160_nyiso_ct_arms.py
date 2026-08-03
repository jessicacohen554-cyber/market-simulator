"""Drive the caiso-160 NYISO CT heat-rate A/B, enforcing the lane's pipeline rules.

Both arms replay the nyiso-113 keeper recipe (`scripts/replay_keeper.py`, no
``--set``) at the SAME HEAD, differing only in the bytes of
``data/raw/_processed-legacy/campd_ct_heat_rates_NYISO{,_units}.csv``:

* arm A control   -- the PRE-FIX artifact, restored from ``f6238a5^``
* arm B treatment -- the POST-FIX artifact committed on main

Three failure modes this script exists to make impossible, each one a rule the
lane learned the hard way (PREREG-caiso160 sections 3-4):

1. **Stale cache.** ``ScenarioConfig.cache_key`` hashes config FIELDS ONLY, so
   two arms that differ solely in an input artifact share a key and
   ``runner.py`` would short-circuit arm B onto arm A's persisted tree
   (caiso-158 section 4a). ``results/NYISO`` is scrubbed before EVERY arm.
2. **Wrong artifact.** The swap is verified by md5 against the expected blob
   immediately before the solve starts, and the post-fix artifact is restored
   in a ``finally`` so an aborted arm A can never leave the pre-fix bytes on
   disk for arm B to consume.
3. **Silent recipe drift.** Neither arm passes ``--set``, so the config delta
   against the keeper is structurally zero rather than asserted.

Usage:
    python scripts/probes/caiso160_nyiso_ct_arms.py --arm A
    python scripts/probes/caiso160_nyiso_ct_arms.py --arm B
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
KEEPER = REPO / "results/calibration/nyiso113_lilocational_B"

# The commit that applied the physical band at the hour (caiso-156 fix); its
# parent therefore holds the pre-fix artifact the control arm needs.
FIX_COMMIT = "f6238a5"

STEMS = ("campd_ct_heat_rates_NYISO.csv", "campd_ct_heat_rates_NYISO_units.csv")

# md5 of the plant-level artifact each arm MUST solve against, measured from
# both blobs in PREREG-caiso160 section 2. The units file carries no md5 pin
# because only the plant file reaches the LP (campd_bins.py:266).
ARMS = {
    "A": {
        "bundle": "nyiso160_ctmeter_control_A",
        "md5": "749f4ffff41f05fa9b67b6f011b770ec",
        "note": (
            "caiso-160 arm A (control): nyiso-113 keeper recipe replayed at "
            "HEAD against the PRE-FIX CT heat-rate artifact (f6238a5^, "
            "cap-weighted 12.0769). Zero config delta vs the keeper -- no "
            "--set. Cold solve. Isolates the CT correction from the seven "
            "src/market_sim commits that landed after the keeper solved."
        ),
    },
    "B": {
        "bundle": "nyiso160_ctmeter_screen_B",
        "md5": "6fb854399825925c5bc020e136ca50f8",
        "note": (
            "caiso-160 arm B (treatment): nyiso-113 keeper recipe replayed at "
            "HEAD against the POST-FIX CT heat-rate artifact (hour-grain "
            "physical band applied, cap-weighted 12.4355). Zero config delta "
            "vs the keeper -- no --set. Cold solve. The promotion candidate."
        ),
    },
}


def md5(path: Path) -> str:
    """Return the hex md5 of a file's bytes."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def install_prefix_artifact(stash: Path) -> None:
    """Overwrite the CT artifacts with their pre-fix blobs, stashing HEAD's."""
    stash.mkdir(parents=True, exist_ok=True)
    for stem in STEMS:
        shutil.copy2(PROCESSED / stem, stash / stem)
        blob = subprocess.run(
            ["git", "show", f"{FIX_COMMIT}^:data/raw/_processed-legacy/{stem}"],
            cwd=REPO,
            check=True,
            capture_output=True,
        ).stdout
        (PROCESSED / stem).write_bytes(blob)


def restore_artifact(stash: Path) -> None:
    """Put HEAD's (post-fix) CT artifacts back, whatever happened to the arm."""
    for stem in STEMS:
        if (stash / stem).is_file():
            shutil.copy2(stash / stem, PROCESSED / stem)


def scrub_cache() -> None:
    """Remove the global per-ISO results tree so the next solve is cold.

    ``runner.py`` short-circuits on ``results/<ISO>/<cache_key>/`` and the
    cache key never sees an input artifact's bytes, so this is the ONLY thing
    standing between a value-identical arm pair and a silently reused solve.
    """
    tree = REPO / "results/NYISO"
    if tree.exists():
        shutil.rmtree(tree)
        print(f"[cold] removed {tree.relative_to(REPO)}")
    else:
        print("[cold] results/NYISO already absent")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    args = ap.parse_args()

    spec = ARMS[args.arm]
    out_dir = REPO / "results/calibration" / spec["bundle"]
    stash = REPO / f".caiso160_artifact_stash_{args.arm}"

    try:
        if args.arm == "A":
            install_prefix_artifact(stash)

        got = md5(PROCESSED / STEMS[0])
        if got != spec["md5"]:
            raise SystemExit(
                f"arm {args.arm}: CT artifact md5 {got} != expected "
                f"{spec['md5']} -- refusing to solve against the wrong input"
            )
        print(f"[arm {args.arm}] CT artifact verified: md5 {got}")

        scrub_cache()

        cmd = [
            sys.executable,
            "scripts/replay_keeper.py",
            str(KEEPER.relative_to(REPO)),
            "--out-dir",
            str(out_dir.relative_to(REPO)),
            "--note",
            spec["note"],
        ]
        print(f"[arm {args.arm}] {' '.join(cmd[:4])} ...")
        subprocess.run(cmd, cwd=REPO, check=True)
    finally:
        # Non-negotiable: arm B must never inherit arm A's pre-fix bytes, so
        # the restore runs even if the solve raised.
        if args.arm == "A":
            restore_artifact(stash)
            shutil.rmtree(stash, ignore_errors=True)
            print(f"[arm A] restored post-fix artifact: md5 {md5(PROCESSED / STEMS[0])}")


if __name__ == "__main__":
    main()
