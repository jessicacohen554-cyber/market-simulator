"""Cross-ISO measurement of the D-2 capacity-weighted plant-class vote (nyiso-233, ZERO LP).

The evidence behind ``docs/FINDING-nyiso233-d2-capacity-weighted-vote-2026-09-13.md``
and the landing recorded in
``results/calibration/PRECOMMIT-nyiso233-d2-capacity-weighted-vote.md``.

``scripts/legitimacy_diagnostics.py::aggregate_floors_by_plant`` labelled each
plant by its most common non-empty unit group counted in LP ROWS until
2026-09-13. Row count is a property of the offer curve's band structure, not of
the plant, so a ladder collapse could move a site's whole dispatch between class
denominators and flip C8 (``docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md``).
The repair weights the vote by ``pmax``. This probe measures what that does, on
every bundle in the repository carrying a committed ``floors/<year>_P1.npz``.

Three modes, all zero-LP (``run_year(fleet_only=True)`` builds a fleet, not an LP):

* ``equiv`` — asserts the refactored accumulator reproduces the PRE-nyiso-233
  row-count labels bit-for-bit when no ``pmax`` is supplied. This is what
  licenses reading every other number here as a basis change rather than a
  code change.
* ``labels`` (default) — per bundle-year, the plants whose label moves
  row-count -> capacity, with the row counts and capacities that decided each.
* ``stop`` — the PRECOMMIT's pre-registered stop conditions S1/S2/S3.

Run: ``python3 scripts/probes/_nyiso233_d2_capacity_vote_measure.py [mode] [bundle...]``
"""

from __future__ import annotations

import collections
import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")

from scripts.legitimacy_diagnostics import (  # noqa: E402
    _backfill_pmax,
    aggregate_floors_by_plant,
)

BUNDLES = [
    "results/calibration/nyiso232_deleak_span",
    "results/calibration/caiso279_ablate_dswcouple_span",
    "results/calibration/soco15_spp_arm",
]


def _legacy_labels(arrays: dict) -> dict[int, str]:
    """The PRE-nyiso-233 vote, transcribed verbatim from the superseded code."""
    plant_code = np.asarray(arrays["plant_code"])
    keep = plant_code > 0
    groups = np.asarray(arrays["plant_group"]).astype(str)[keep]
    pc = plant_code[keep]
    order = np.argsort(pc, kind="stable")
    groups, pc = groups[order], pc[order]
    starts = np.flatnonzero(np.r_[True, pc[1:] != pc[:-1]])
    bounds = np.r_[starts, pc.size]
    out = {}
    for i in range(starts.size):
        block = slice(bounds[i], bounds[i + 1])
        nonempty = groups[block][groups[block] != ""]
        if nonempty.size:
            vals, counts = np.unique(nonempty, return_counts=True)
            out[int(pc[starts[i]])] = str(vals[counts.argmax()])
        else:
            out[int(pc[starts[i]])] = ""
    return out


def _years(bundle: Path) -> list[int]:
    return sorted(
        int(Path(f).name.split("_")[0])
        for f in glob.glob(str(bundle / "floors" / "*_P1.npz"))
    )


def _load(bundle: Path, year: int) -> dict:
    with np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _iso(bundle: Path) -> str:
    return json.loads((bundle / "meta.json").read_text())["iso"]


def equiv(bundles: list[str]) -> None:
    """S3 half one: the refactor is a no-op when no pmax is supplied."""
    print("EQUIVALENCE — refactored accumulator vs the superseded row-count vote\n")
    bad = 0
    for b in bundles:
        bundle = Path(b)
        for year in _years(bundle):
            arr = _load(bundle, year)
            assert "pmax" not in arr, f"{b} {year} already carries pmax"
            _, _, _, groups, _ = aggregate_floors_by_plant(arr)
            pc = np.asarray(arr["plant_code"])
            keys = sorted({int(c) for c in pc if c > 0})
            new = dict(zip(keys, [str(g) for g in groups[: len(keys)]]))
            old = _legacy_labels(arr)
            diff = {k: (old[k], new[k]) for k in old if old[k] != new.get(k)}
            bad += len(diff)
            print(
                f"  {_iso(bundle):6s} {year}  plants={len(old):4d}  label diffs={len(diff)}"
            )
            for k, v in list(diff.items())[:5]:
                print(f"      plant {k}: old={v[0]!r} new={v[1]!r}")
    print(
        f"\n{'PASS' if bad == 0 else 'FAIL'} — {bad} label difference(s) on the no-pmax path"
    )


def labels(bundles: list[str]) -> None:
    print("LABEL MOVES — row-count vote -> capacity-weighted vote\n")
    for b in bundles:
        bundle = Path(b)
        iso = _iso(bundle)
        for year in _years(bundle):
            arr = _load(bundle, year)
            old = _legacy_labels(arr)
            arr2 = _backfill_pmax(arr, bundle, iso, year)
            if arr2.get("pmax") is None:
                print(f"  {iso} {year}: NO pmax — row-count fallback, not measurable")
                continue
            pc = np.asarray(arr2["plant_code"])
            pg = np.asarray(arr2["plant_group"]).astype(str)
            pm = np.asarray(arr2["pmax"], dtype=float)
            cap = collections.defaultdict(lambda: collections.defaultdict(float))
            cnt = collections.defaultdict(collections.Counter)
            for c, g, m in zip(pc, pg, pm):
                if c > 0 and g:
                    cap[int(c)][g] += max(m, 0.0)
                    cnt[int(c)][g] += 1
            _, _, _, groups, _ = aggregate_floors_by_plant(arr2)
            keys = sorted({int(c) for c in pc if c > 0})
            new = dict(zip(keys, [str(g) for g in groups[: len(keys)]]))
            mixed = [k for k in keys if len(cap[k]) > 1]
            flips = [k for k in keys if old[k] != new[k]]
            print(
                f"  {iso:6s} {year}  plants={len(keys):4d}  mixed={len(mixed):3d}  FLIPS={len(flips)}"
            )
            for k in flips:
                c = dict(cap[k])
                ratio = max(c.values()) / max(min(c.values()), 1e-9)
                print(
                    f"      plant {k:>6}: rows {dict(cnt[k])} -> {old[k]:11s} | "
                    f"cap { ({g: round(v, 1) for g, v in c.items()}) } -> {new[k]:11s} ({ratio:.1f}x)"
                )


def stop(bundles: list[str]) -> None:
    """The PRECOMMIT's pre-registered stop conditions."""
    print("STOP CONDITIONS (PRECOMMIT-nyiso233 section 5)\n")
    s1 = s2 = s3 = 0
    rows = 0
    for b in bundles:
        bundle = Path(b)
        iso = _iso(bundle)
        for year in _years(bundle):
            arr = _load(bundle, year)
            old = _legacy_labels(arr)
            arr2 = _backfill_pmax(arr, bundle, iso, year)
            if arr2.get("pmax") is None:
                s3 += 1
                print(f"  S3 {iso} {year}: pmax backfill FAILED")
                continue
            pm = np.asarray(arr2["pmax"], dtype=float)
            pc = np.asarray(arr2["plant_code"])
            pg = np.asarray(arr2["plant_group"]).astype(str)
            rows += len(pm)
            # S1 — capacity must discriminate: a classified plant whose rows all
            # carry zero pmax cannot be voted on by capacity.
            zero = [
                int(c)
                for c in np.unique(pc[pc > 0])
                if (pg[pc == c] != "").any() and pm[(pc == c) & (pg != "")].sum() <= 0
            ]
            s1 += len(zero)
            # S2 — the #1488 fix must not regress: no plant may lose a non-empty
            # label to ''.
            _, _, _, groups, _ = aggregate_floors_by_plant(arr2)
            keys = sorted({int(c) for c in pc if c > 0})
            new = dict(zip(keys, [str(g) for g in groups[: len(keys)]]))
            lost = [k for k in keys if old[k] != "" and new[k] == ""]
            s2 += len(lost)
            print(
                f"  {iso:6s} {year}  rows={len(pm):5d}  S1 zero-capacity plants={len(zero)}  "
                f"S2 labels lost to ''={len(lost)}  S3 backfill=OK"
            )
    print(
        f"\nS1 {'FIRES' if s1 else 'clear'} ({s1})   S2 {'FIRES' if s2 else 'clear'} ({s2})   "
        f"S3 {'FIRES' if s3 else 'clear'} ({s3})   rows backfilled={rows}"
    )


if __name__ == "__main__":
    mode = (
        sys.argv[1]
        if len(sys.argv) > 1 and not sys.argv[1].startswith("results/")
        else "labels"
    )
    args = [a for a in sys.argv[1:] if a.startswith("results/")] or BUNDLES
    {"equiv": equiv, "labels": labels, "stop": stop}[mode](args)
