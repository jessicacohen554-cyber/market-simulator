"""D-2's plant class is a ROW-COUNT vote over LP tranches (nyiso-232, ZERO LP).

The evidence behind
``docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md``.

``scripts/legitimacy_diagnostics.py::aggregate_floors_by_plant`` labels each plant
with the "most common non-empty unit group" among its LP rows. How many rows a
class contributes is a property of the OFFER CURVE's band structure, not of the
plant — so collapsing a class's econ smoothing ladder can flip a mixed plant's
whole dispatch between class denominators and trip C8 (protective tier, zero
caveat budget) with no physical change at all.

Two modes, both zero-LP:

* ``census`` (default) — reads every committed ``floors/<year>_P1.npz`` and counts
  mixed plants whose label is FLIPPABLE, i.e. halving the winner's row count (the
  measured ladder-collapse effect) loses it the vote. No fleet rebuild, no ISO
  data profile, so it runs for every ISO whose bundle is committed.
* ``compare <ctl-bundle> <arm-bundle> <year>`` — names the plants that actually
  flip between two legs, with their row counts on each side.

Run: ``python3 scripts/probes/_nyiso232_d2_plant_class_vote.py [census|compare ...]``
"""

from __future__ import annotations

import collections
import glob
import sys

import numpy as np


def _plant_groups(npz_path: str):
    """Return ``{plant_code: Counter(non-empty group -> row count)}``."""
    z = np.load(npz_path, allow_pickle=True)
    if "plant_group" not in z.files:
        return None
    pc = np.asarray(z["plant_code"])
    keep = pc > 0
    pc = pc[keep]
    pg = np.asarray(z["plant_group"]).astype(str)[keep]
    out: dict[int, collections.Counter] = {}
    for c in np.unique(pc):
        out[int(c)] = collections.Counter(x for x in pg[pc == c] if x != "")
    return out


def census() -> None:
    print(
        "FRAGILITY CENSUS — plants whose D-2 class label a band-structure change could flip."
    )
    print(
        f"{'bundle / year':52s} {'plants':>7s} {'mixed':>6s} {'margin<=2':>10s} {'flippable':>10s}"
    )
    for f in sorted(glob.glob("results/calibration/*/floors/*_P1.npz")):
        g = _plant_groups(f)
        if g is None:
            print(f"  {f}: no plant_group array")
            continue
        mixed = narrow = flip = 0
        for cnt in g.values():
            top = cnt.most_common()
            if len(top) < 2:
                continue
            mixed += 1
            (_, n1), (_, n2) = top[0], top[1]
            if n1 - n2 <= 2:
                narrow += 1
            if n1 / 2.0 <= n2:  # the measured 8-band -> 4-band collapse
                flip += 1
        lbl = (
            f.replace("results/calibration/", "")
            .replace("/floors/", "  ")
            .replace("_P1.npz", "")
        )
        print(f"{lbl:52s} {len(g):7d} {mixed:6d} {narrow:10d} {flip:10d}")


def compare(ctl: str, arm: str, year: int) -> None:
    gc = _plant_groups(f"{ctl}/floors/{year}_P1.npz")
    ga = _plant_groups(f"{arm}/floors/{year}_P1.npz")
    if gc is None or ga is None:
        raise SystemExit("a bundle carries no plant_group array")

    def label(cnt):
        return cnt.most_common(1)[0][0] if cnt else ""

    flips = [
        p
        for p in sorted(set(gc) | set(ga))
        if label(gc.get(p, collections.Counter()))
        != label(ga.get(p, collections.Counter()))
    ]
    print(f"plants whose D-2 class label FLIPS between the legs ({year}): {len(flips)}")
    for p in flips:
        print(
            f"\n  plant {p}:  CTL '{label(gc.get(p, collections.Counter()))}'"
            f"  ->  ARM '{label(ga.get(p, collections.Counter()))}'"
        )
        print(f"      CTL row counts: {dict(gc.get(p, {}))}")
        print(f"      ARM row counts: {dict(ga.get(p, {}))}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    else:
        census()
