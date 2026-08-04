"""Drive the pjm-152 rule-26 collapse arm: re-solve the keeper recipe at HEAD.

pjm-151 shipped the per-neighbour seam-envelope construction behind
``ScenarioConfig.pjm_seam_envelope_by_neighbor`` **only** so its A/B could be a
single delta on an ISO with zero caveat budget. With the repair promoted, the
flag and the zone-summed branch it guards are a re-armable broken version still
parsing — exactly what rule 26 ``[R-DELETE]`` forbids. pjm-152 collapses them:
the construction is unconditional, the parameter, the branch, the three config
registrations and the ``run_calibration.py`` plumbing are deleted.

**The collapse changes the keeper's cache key** (the field left
``_CACHE_KEY_OPTIONAL_FIELDS``, and an ARMED optional field is in the hash), so
it cannot be asserted byte-identical — it has to be *proven*. This driver
re-solves the keeper's own recipe cold at the collapsed HEAD; the companion
scorer ``pjm152_collapse_gates.py`` diffs every P1 class-hour against
``results/calibration/pjm151_seam_B/hourly/class_hourly_<year>.parquet``.

**The gate is single and absolute: max |dMW| = 0.000000 on all three years.**
Anything else means the collapse changed behaviour and is a stop-the-line event.

There is no ``--set`` here and there must never be one: the arm IS the keeper
recipe. The one unavoidable difference is that the keeper's ``meta.json``
records ``pjm_seam_envelope_by_neighbor: true`` inside its ``prb_overrides``
channel, and that key no longer names a ``ScenarioConfig`` field —
``dataclasses.replace`` would raise. So this script materialises a stripped
recipe view of the keeper's meta, asserts that removing THAT ONE KEY is the only
edit, and replays from it.

Rule 12's per-year invocation chain keeps all three years in ONE bundle (rule
16) while giving each year a fresh process — a PJM per-plant multi-zone LP with
``ramp_limits=True`` peaks ~15.5 GB RSS. ``--out-dir X --reuse-solved X`` raises
``shutil.SameFileError``, so the chain walks SEPARATE directories and this
script refuses a self-reuse up front.

Usage::

    python scripts/probes/pjm152_collapse_arm.py --year 2023 --out pjm152_collapse_y23
    python scripts/probes/pjm152_collapse_arm.py --year 2023 2024 \\
        --out pjm152_collapse_y24 --reuse-from pjm152_collapse_y23
    python scripts/probes/pjm152_collapse_arm.py --year 2023 2024 2025 \\
        --out pjm152_collapse_A --reuse-from pjm152_collapse_y24
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/pjm151_seam_B"
VIRTUALS = REPO / "data/raw/pjm-da-virtuals"

#: The single key the collapse retires. It rides the generic ``prb_overrides``
#: channel in the keeper's meta.json (recorded there by ``--set`` at pjm-151).
RETIRED_KEY = "pjm_seam_envelope_by_neighbor"

#: Where the stripped recipe view is materialised. Deterministic, so each link
#: of the chain rebuilds the same bytes.
RECIPE_DIR = REPO / "results/calibration/_pjm152_keeper_recipe"

NOTE = (
    "pjm-152 arm A: the pjm-151 keeper recipe re-solved COLD at the collapsed "
    "HEAD. Rule 26 [R-DELETE] follow-up owed by pjm-151: "
    "pjm_seam_envelope_by_neighbor, the by_neighbor parameter, the zone-summed "
    "branch, the _CACHE_KEY_OPTIONAL_FIELDS / defaults-ledger / TIER_TAGS "
    "entries and the run_calibration.py plumbing are DELETED and the "
    "per-neighbour envelope construction is unconditional. NOT a mechanism "
    "change and NOT a lever: zero recipe deltas, and the collapse is proven "
    "rather than asserted -- the gate is max |dMW| = 0.000000 against "
    "results/calibration/pjm151_seam_B on every P1 class-hour of all three "
    "years. The collapse moves the cache key (an armed optional field was in "
    "the hash and the field is now gone), which is exactly why a cold re-solve "
    "is required instead of an assertion. Off-queue under rule 28(a): PJM's "
    "lever queue is EMPTY and its price-formation frontier is owner-declared "
    "(pjm-142); this is chartered debt discharge, not a successor."
)


def build_stripped_recipe() -> Path:
    """Materialise the keeper's meta.json with the retired key removed.

    Asserts that removing exactly that one key is the ONLY edit, so the replay
    cannot silently carry a second delta. Returns the recipe bundle dir.
    """
    meta = json.loads((KEEPER / "meta.json").read_text())
    channel = "coal_prb_sigmoid_overrides"
    overrides = meta.get(channel) or {}
    if RETIRED_KEY not in overrides:
        raise SystemExit(
            f"{KEEPER.name}/meta.json has no {RETIRED_KEY} in {channel} — this "
            "driver exists to strip it; the keeper is not the expected one"
        )
    if overrides[RETIRED_KEY] is not True:
        raise SystemExit(
            f"{RETIRED_KEY} is {overrides[RETIRED_KEY]!r} on the keeper, not "
            "True — the collapse makes the ARMED path unconditional, so a "
            "keeper that did not arm it is not the right control"
        )
    stripped = dict(meta)
    stripped[channel] = {k: v for k, v in overrides.items() if k != RETIRED_KEY}

    # The edit must be exactly one key in exactly one channel.
    assert set(stripped) == set(meta), "top-level meta keys must not move"
    for k in meta:
        if k == channel:
            continue
        assert stripped[k] == meta[k], f"unexpected edit to meta key {k!r}"
    assert set(overrides) - set(stripped[channel]) == {RETIRED_KEY}
    assert not set(stripped[channel]) - set(overrides)

    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    (RECIPE_DIR / "meta.json").write_text(json.dumps(stripped, indent=2) + "\n")
    print(
        f"[pjm-152] stripped recipe -> {RECIPE_DIR.relative_to(REPO)}/meta.json "
        f"(removed {channel}.{RETIRED_KEY}=True; {len(meta)} top-level keys "
        f"unchanged)"
    )
    return RECIPE_DIR


def scrub_cache() -> None:
    """Remove the global per-ISO results tree so the next solve is cold.

    ``runner.py`` short-circuits on ``results/<ISO>/<cache_key>/`` and the cache
    key hashes CONFIG FIELDS ONLY — it never sees an input artifact's bytes, and
    here it has moved anyway. Scrubbed before the FIRST year of the chain, and
    deliberately NOT between chained years (whose later invocations byte-copy
    earlier years via ``--reuse-solved``).
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
    ``virtual_bids.py`` correctly raises rather than no-opping.
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
    print(f"[pjm-152] DA virtual-bid feed present: {n} parquet(s)")


def main() -> None:
    """Run one link of the rule-12 chain for the pjm-152 collapse arm."""
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
    recipe = build_stripped_recipe()

    if reuse is None:
        scrub_cache()
    else:
        print("[cold] chained invocation — results/PJM kept for --reuse-solved")

    cmd = [
        sys.executable,
        "scripts/replay_keeper.py",
        str(recipe.relative_to(REPO)),
        "--out-dir",
        str(out_dir.relative_to(REPO)),
        "--years",
        *[str(y) for y in years],
        "--note",
        NOTE,
    ]
    if reuse is not None:
        cmd += ["--reuse-solved", str(reuse.relative_to(REPO))]

    print(f"[pjm-152] years={years} out={args.out} reuse={args.reuse_from}")
    print("[pjm-152] ZERO --set: the arm IS the keeper recipe at the collapsed HEAD")
    subprocess.run(cmd, cwd=REPO, check=True)


if __name__ == "__main__":
    main()
