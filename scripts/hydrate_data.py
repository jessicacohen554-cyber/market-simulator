#!/usr/bin/env python3
"""Hydrate a session's ``data/raw`` subtrees on demand in a partial clone.

WHY
    The repo's pack is ~7.4 GiB and ~99% of it is blobs LIVE at the tip of main
    (measured 2026-08-13: 7.37 GiB live of a 7.44 GiB pack — only 82 MB of the
    pack is dead history). A full clone must transfer all of it and stalls
    through the environment's egress proxy. A **blobless partial clone** avoids
    that entirely: the commit/tree graph downloads in seconds and file blobs are
    fetched only when a path is actually checked out.

    That leaves one question per session: which ``data/raw`` subtrees does THIS
    lane need? This script answers it from ``configs/data-profiles.yaml`` — a
    lane names a profile and gets exactly that profile's data, nothing else.

USAGE
    python3 scripts/hydrate_data.py --list              # profiles and coverage
    python3 scripts/hydrate_data.py --show              # what is hydrated now
    python3 scripts/hydrate_data.py --profile ercot     # hydrate ERCOT + shared
    python3 scripts/hydrate_data.py --profile code      # drop data/raw entirely
    python3 scripts/hydrate_data.py --profile ercot --dry-run

ATTRIBUTION
    Every path under ``data/raw`` is attributed to one ISO, or to ``shared`` when
    it is cross-ISO. Attribution is DERIVED from the tree at HEAD — nothing is
    enumerated by hand, so a newly-added subtree is picked up automatically:

      1. ``data/raw/<child>``     — if ``<child>`` carries an ISO token, the whole
                                    subtree belongs to that ISO.
      2. ``data/raw/<child>/<x>`` — otherwise, if ``<child>`` holds ISO-named
                                    subdirectories it is a *split* directory
                                    (``lmp-data``, ``zone-specific-demand``,
                                    ``storage-as-awards``, ...) and each entry is
                                    attributed on its own name — by **whole-name
                                    equality first**, token match second
                                    (``iso_for_split_child``).
      3. anything else            — ``shared``, hydrated by every data profile.

    Split directories are detected, not listed, so a directory that becomes
    per-ISO later needs no edit here.

    Rule 2's whole-name limb exists because an ISO's tokens may be deliberately
    delimiter-bounded to dodge a substring collision, which then makes them miss
    a bare directory name: SPP's tokens avoid ERCOT's ``DAMLZHBSPP_*.zip``, so
    ``zone-specific-demand/SPP`` and ``load-forecast/spp`` matched nothing and
    fell through to ``shared`` (over-hydrated, never missing). See
    :func:`iso_for_split_child`.

PARTIAL-CLONE SAFETY — the trap this script exists to avoid
    In a blobless clone, ANY git command that reads a missing blob silently
    fetches it. ``git cat-file --batch-check='%(objectsize:disk)'`` over the
    whole tree therefore downloads every byte of ``data/raw`` — the exact
    outcome this tool is meant to prevent. (Verified 2026-08-13: with
    ``GIT_NO_LAZY_FETCH=1`` the same command fails with "could not fetch ... from
    promisor remote", proving the unguarded call was fetching.)

    So this script reads **trees only**. The file list comes from ``ls-tree``,
    which never touches blob contents, and sizes come from
    ``cat-file --batch-all-objects``, which enumerates objects already local and
    fetches nothing. Sizes are consequently *unknown* for not-yet-hydrated paths
    in a partial clone — reported honestly rather than bought by downloading the
    repo. Never add a call here that resolves a blob by name.

NOTES
    * Idempotent — the pattern set is rebuilt from the profile each run.
    * Safe in a FULL clone: hydration is a no-op there (every blob is local) and
      nothing changes unless ``--force`` is passed.
    * Never modifies tracked content. It only changes which paths are present in
      the working tree, which is a checkout concern, not a solve input.

See ``docs/fast-clone.md`` for the clone recipe this complements.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "configs" / "data-profiles.yaml"
RAW_PREFIX = "data/raw"
SHARED = "shared"


def _git(*args: str, check: bool = True, stdin: str | None = None) -> str:
    """Run a git command in the repo root and return its stdout.

    Runs with ``GIT_NO_LAZY_FETCH=1`` so that a stray read of a missing blob
    fails loudly instead of silently downloading it (see module docstring).
    """
    env = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
        input=stdin,
        env=env,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _git_fetching(*args: str) -> str:
    """Run a git command that is ALLOWED to fetch blobs (the hydration itself)."""
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def load_manifest() -> dict:
    """Load and return the parsed data-profile manifest."""
    with MANIFEST.open() as fh:
        return yaml.safe_load(fh)


def raw_entries() -> list[tuple[str, str]]:
    """Return ``(blob_sha, path)`` for every file under ``data/raw`` at HEAD.

    Reads tree objects only — safe in a blobless partial clone.
    """
    out = _git(
        "ls-tree", "-r", "--format=%(objectname) %(path)", "HEAD", f"{RAW_PREFIX}/"
    )
    entries = []
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            entries.append((parts[0], parts[1]))
    return entries


def local_sizes() -> dict[str, int]:
    """Return packed size for every object ALREADY LOCAL in this clone.

    Uses ``--batch-all-objects``, which enumerates the object database and never
    fetches. Objects absent from a partial clone simply do not appear.
    """
    out = _git(
        "cat-file",
        "--batch-all-objects",
        "--batch-check=%(objectname) %(objectsize:disk)",
    )
    sizes = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            sizes[parts[0]] = int(parts[1])
    return sizes


def iso_for_name(name: str, isos: dict) -> str | None:
    """Return the ISO owning ``name`` by token match, or None when cross-ISO."""
    low = name.lower()
    for iso, spec in isos.items():
        if any(tok.lower() in low for tok in spec["tokens"]):
            return iso
    return None


def iso_for_split_child(name: str, isos: dict) -> str | None:
    """Return the ISO owning a *split-directory child* ``name``, or None.

    Same question as :func:`iso_for_name`, but for the one position where the
    directory name IS the ISO label — ``lmp-data/ERCOT``,
    ``zone-specific-demand/SPP``, ``load-forecast/spp``. There a **whole-name**
    match is both stronger and safer than the substring token match, so it is
    tried first and the token match only backs it up.

    Why the extra limb exists (lane SPP-34, 2026-09-07; routed item R-4 of
    ``docs/handoffs/FINDING-spp-20-2026-09-06.md`` §5). SPP's tokens are
    deliberately delimiter-bounded — ``swpp``, ``spp-``, ``_spp.``, ``-spp.``,
    ``/spp/`` — because a bare ``spp`` token would also claim ERCOT's
    settlement-point zips ``DAMLZHBSPP_<year>.zip`` (plan §7 gate G3). But a
    bare directory NAME carries no delimiter, so ``zone-specific-demand/SPP``
    and ``load-forecast/spp`` matched none of them and fell through to
    ``shared`` — over-hydrated for every profile, never missing, but wrong.
    Whole-name equality closes that without re-admitting the trap:
    ``DAMLZHBSPP_2023.zip`` is not equal to ``SPP``.
    """
    exact = name.strip().lower()
    for iso in isos:
        if exact == iso.lower():
            return iso
    return iso_for_name(name, isos)


def split_dirs(paths: list[str], isos: dict) -> set[str]:
    """Return ``data/raw`` children that hold per-ISO subdirectories.

    A directory qualifies when at least one immediate child is ISO-named —
    by whole name or by token (:func:`iso_for_split_child`).
    Detected rather than configured, so it stays correct as the tree grows.
    """
    grandchildren: dict[str, set[str]] = {}
    for path in paths:
        seg = path.split("/")
        if len(seg) > 4:  # data/raw/<child>/<grandchild>/...
            grandchildren.setdefault(seg[2], set()).add(seg[3])
    return {
        child
        for child, kids in grandchildren.items()
        if any(iso_for_split_child(k, isos) for k in kids)
    }


def owner_of(path: str, isos: dict, splits: set[str]) -> str:
    """Attribute one ``data/raw`` file path to an ISO or to ``shared``."""
    seg = path.split("/")
    if len(seg) < 3:
        return SHARED
    child = seg[2]
    direct = iso_for_name(child, isos)
    if direct:
        return direct
    if child in splits and len(seg) > 3:
        nested = iso_for_split_child(seg[3], isos)
        if nested:
            return nested
    return SHARED


def profile_isos(profile: dict, manifest: dict) -> set[str]:
    """Return the ISO set a profile hydrates beyond ``shared``."""
    kind = profile.get("data", "none")
    if kind == "iso":
        return {profile["iso"]}
    if kind == "all":
        return set(manifest["isos"])
    return set()


def resolve_files(profile_name: str, manifest: dict, paths: list[str]) -> list[str]:
    """Return every ``data/raw`` file path a profile wants hydrated."""
    profiles = manifest["profiles"]
    if profile_name not in profiles:
        raise SystemExit(
            f"unknown profile {profile_name!r}. Known: {', '.join(sorted(profiles))}"
        )
    profile = profiles[profile_name]
    if profile.get("data", "none") == "none":
        return []
    isos = manifest["isos"]
    splits = split_dirs(paths, isos)
    keep = profile_isos(profile, manifest) | {SHARED}
    return [p for p in paths if owner_of(p, isos, splits) in keep]


def build_patterns(files: list[str], all_paths: list[str]) -> list[str]:
    """Build a compact non-cone sparse-checkout pattern set for ``files``.

    Whole directories collapse to one directory pattern when every file beneath
    them is wanted; otherwise individual files are listed. Keeps the set small
    so each pattern maps to one batched fetch.
    """
    patterns = ["/*", f"!/{RAW_PREFIX}/"]
    if not files:
        return patterns

    wanted = set(files)
    by_dir: dict[str, set[str]] = {}
    for path in all_paths:
        by_dir.setdefault(path.rsplit("/", 1)[0], set()).add(path)

    covered: set[str] = set()
    for directory in sorted(by_dir):
        if by_dir[directory] <= wanted and not any(
            directory.startswith(c + "/") for c in covered
        ):
            patterns.append(f"/{directory}/")
            covered.add(directory)

    for path in sorted(wanted):
        if not any(path.startswith(c + "/") for c in covered):
            patterns.append(f"/{path}")
    return patterns


def is_partial_clone() -> bool:
    """Return True when this clone was made with a blob filter (promisor remote)."""
    return bool(_git("config", "--get", "remote.origin.promisor", check=False).strip())


def human(nbytes: int) -> str:
    """Format a byte count as a compact human-readable string."""
    value = float(nbytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:,.1f} {unit}"
        value /= 1024
    return f"{value:,.1f} GB"


def cmd_list(manifest: dict) -> None:
    """Print every profile with its file count and (where known) byte size."""
    entries = raw_entries()
    paths = [p for _, p in entries]
    sizes = local_sizes()
    by_path = {p: sizes.get(sha) for sha, p in entries}
    known = sum(1 for v in by_path.values() if v is not None)
    partial = known < len(paths)

    isos = manifest["isos"]
    splits = split_dirs(paths, isos)

    print(f"\ndata/raw at HEAD: {len(paths):,} files")
    print(f"split directories detected: {', '.join(sorted(splits)) or 'none'}")
    if partial:
        print(
            f"NOTE: partial clone — byte sizes known for {known:,}/{len(paths):,} "
            "files\n      (only what is already local; nothing is fetched to measure)"
        )

    label = "SIZE (approx)" if partial else "SIZE"
    print(f"\n{'PROFILE':<10} {'FILES':>8} {label:>14}   DESCRIPTION")
    print("-" * 78)
    for name, spec in manifest["profiles"].items():
        files = resolve_files(name, manifest, paths)
        if partial:
            # Measuring for real would fetch the data the profile exists to
            # avoid, so fall back to the manifest's recorded figure.
            shown = f"~{spec.get('approx_gb', 0):g} GB"
        else:
            shown = human(sum(by_path[f] for f in files if by_path[f] is not None))
        desc = " ".join(spec["description"].split())
        if len(desc) > 34:
            desc = desc[:31] + "..."
        print(f"{name:<10} {len(files):>8,} {shown:>14}   {desc}")
    print("\nHydrate with:  python3 scripts/hydrate_data.py --profile <name>\n")


def cmd_show() -> None:
    """Print the clone's current sparse-checkout and partial-clone state."""
    print(
        f"\npartial (blobless) clone : {'yes' if is_partial_clone() else 'no — full clone'}"
    )
    sparse = _git("sparse-checkout", "list", check=False).strip()
    if not sparse:
        print("sparse-checkout          : not enabled (entire tree checked out)")
    else:
        lines = sparse.splitlines()
        print(f"sparse-checkout patterns : {len(lines)}")
    raw = REPO_ROOT / RAW_PREFIX
    present = sorted(p.name for p in raw.glob("*")) if raw.is_dir() else []
    print(f"data/raw subtrees present: {len(present)}")
    print()


def cmd_hydrate(profile: str, manifest: dict, dry_run: bool, force: bool) -> None:
    """Apply a profile's sparse-checkout pattern set to this clone."""
    entries = raw_entries()
    paths = [p for _, p in entries]
    files = resolve_files(profile, manifest, paths)
    patterns = build_patterns(files, paths)

    if not is_partial_clone() and not force:
        print(
            "\nThis is a FULL clone — every blob is already local, so hydrating\n"
            "changes nothing except which files sit in the working tree.\n"
            "Re-run with --force to apply the sparse set anyway, or start a\n"
            "partial clone (see docs/fast-clone.md).\n"
        )
        return

    print(f"\nprofile: {profile}")
    print(f"data/raw: {len(files):,} files")
    print(f"sparse patterns: {len(patterns)}")
    if dry_run:
        print("\n--dry-run, not applying. First 20 patterns:")
        for pat in patterns[:20]:
            print(f"    {pat}")
        if len(patterns) > 20:
            print(f"    ... and {len(patterns) - 20} more")
        print()
        return

    # Apply ONE pattern per call. Two measured traps:
    #   * Never follow with `git checkout -- .` — a pathspec checkout
    #     materializes skip-worktree entries, force-fetching blobs OUTSIDE the
    #     profile (.git grew to 2.6 GB hydrating a 1.3 GB profile).
    #   * Never hand git the whole set in one `set` — ~115 non-cone patterns at
    #     once degenerates into per-file fetches and did not finish in 10 min.
    #     One directory at a time is a single batched fetch each (29 MB in 2 s,
    #     666 MB in 23 s).
    base = ["/*", f"!/{RAW_PREFIX}/"]
    data_patterns = [p for p in patterns if p not in base]
    _git_fetching("sparse-checkout", "set", "--no-cone", *base)

    for index, pattern in enumerate(data_patterns, start=1):
        print(f"  [{index}/{len(data_patterns)}] {pattern}", flush=True)
        _git_fetching("sparse-checkout", "add", pattern)
    print("applied.")
    cmd_show()


def main() -> int:
    """Parse arguments and dispatch to the requested sub-command."""
    parser = argparse.ArgumentParser(
        description="Hydrate data/raw subtrees on demand in a partial clone."
    )
    parser.add_argument("--profile", help="profile from configs/data-profiles.yaml")
    parser.add_argument(
        "--list", action="store_true", help="list profiles and coverage"
    )
    parser.add_argument("--show", action="store_true", help="show current clone state")
    parser.add_argument("--dry-run", action="store_true", help="print patterns only")
    parser.add_argument(
        "--force", action="store_true", help="apply even in a full clone"
    )
    args = parser.parse_args()

    manifest = load_manifest()
    if args.list:
        cmd_list(manifest)
    elif args.show:
        cmd_show()
    elif args.profile:
        cmd_hydrate(args.profile, manifest, args.dry_run, args.force)
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
