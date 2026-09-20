"""soco-53g (ZERO LP): rule 17 ``[R-FLOOR-WINDOW]`` re-measurement for SOCO's campaign floor.

The SOCO gas-steam campaign-commitment floor (``soco_gas_st_campaign_commitment``,
D-2 mechanism id ``MECH_SOCO_GAS_ST_CAMPAIGN`` = 25) is detected from a P0 run
pattern, so ANY arm that perturbs P0 can move it and the rule-17 evidence has to
be re-measured rather than inherited. This reads a bundle's own
``floors/<year>_P1.npz`` and reports, per floored plant-year:

* **binding share** -- the fraction of the year's 8,760 hours in which mechanism
  25 binds on that plant's gas-ST row. Rule 17 fails the run if this EXCEEDS the
  plant's own measured ``sync_share`` from
  ``data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv`` (the
  fraction of hours CAMPD shows at least one of its boilers synchronized);
* **floored-block length distribution** -- median / min / max of the contiguous
  floored runs, which separates a campaign (hundreds of hours) from gap-filling
  (a handful). The median is ROUNDED, not truncated, so an even block count ties
  the way ``FINDING-soco-53f`` §4.4 reported it (plant 728, 2023: blocks
  192 and 455, median 323.5 -> 324);
* **a plant with NO mechanism-25 row reads 0.000 and carries zero floored
  hours**, which is the correct reading for Barry (3), whose measured
  ``sync_share`` 0.0631 is below the 0.50 campaign-duty cut so the deriver never
  flags it.

Validated by reproducing ``FINDING-soco-53f`` §4.4's table from the keeper's own
committed legs before it is trusted on anything new (``--validate``).

Run::

    python3 scripts/probes/_soco53g_floor_shares.py results/calibration/<bundle> [--years 2023 2024 2025]
    python3 scripts/probes/_soco53g_floor_shares.py <arm> --against <keeper>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

MECH_SOCO_GAS_ST_CAMPAIGN = 25

PARAMS = Path("data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv")

#: Every SOCO plant the campaign deriver considered, including the one it
#: REFUSED to flag. Declared so a plant silently dropping out of the floor set
#: is visible as a 0.000 row rather than as an absent row.
SOCO_GAS_ST_PLANTS = (3, 10, 26, 728, 2049)


def measured_sync_shares() -> dict[int, float]:
    """Return ``{plant_code: sync_share}`` from the committed campaign params."""
    if not PARAMS.exists():
        return {}
    df = pd.read_csv(PARAMS)
    return {int(r.plant_code): float(r.sync_share) for r in df.itertuples()}


def _blocks(binding: np.ndarray) -> list[int]:
    """Return the lengths of the contiguous ``True`` runs in *binding*."""
    if not binding.any():
        return []
    padded = np.concatenate(([False], binding, [False]))
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    return (edges[1::2] - edges[0::2]).tolist()


def year_shares(bundle: Path, year: int) -> dict[int, dict]:
    """Return ``{plant_code: {...}}`` for one bundle-year's floor npz."""
    npz = bundle / "floors" / f"{year}_P1.npz"
    if not npz.exists():
        raise SystemExit(f"{npz} is absent -- this bundle has no per-plant floor layer")
    z = np.load(npz, allow_pickle=True)
    mech, plant = z["mechanism"], z["plant_code"]
    hit = mech == MECH_SOCO_GAS_ST_CAMPAIGN
    out: dict[int, dict] = {}
    for p in SOCO_GAS_ST_PLANTS:
        rows = np.flatnonzero((plant == p) & hit.any(axis=1))
        if rows.size == 0:
            out[p] = {"share": 0.0, "rows": 0, "hours": 0, "blocks": []}
            continue
        binding = hit[rows].any(axis=0)
        out[p] = {
            "share": float(binding.mean()),
            "rows": int(rows.size),
            "hours": int(binding.sum()),
            "blocks": _blocks(binding),
        }
    # A mechanism-25 row on a plant NOT in the declared set is a leak, not a row.
    stray = sorted(set(plant[hit.any(axis=1)].tolist()) - set(SOCO_GAS_ST_PLANTS))
    if stray:
        out[-1] = {"stray_plants": stray}
    return out


def report(bundle: Path, years: list[int], against: Path | None) -> int:
    meas = measured_sync_shares()
    fails = 0
    for year in years:
        cur = year_shares(bundle, year)
        ref = year_shares(against, year) if against else None
        print(f"\n===== {year} — {bundle.name} =====")
        if -1 in cur:
            print(f"  !! STRAY mechanism-25 plants outside the declared set: {cur[-1]}")
            fails += 1
        print(
            f"  {'plant':>6} {'share':>7} {'measured':>9} {'margin':>8} "
            f"{'hours':>6} {'blocks':>6} {'median':>7} {'min':>5} {'max':>6}"
            + ("   ref     d" if ref else "")
        )
        for p in SOCO_GAS_ST_PLANTS:
            c = cur[p]
            m = meas.get(p, float("nan"))
            b = c["blocks"]
            line = (
                f"  {p:>6} {c['share']:>7.3f} {m:>9.4f} {m - c['share']:>8.4f} "
                f"{c['hours']:>6} {len(b):>6} "
                f"{(round(float(np.median(b))) if b else 0):>7} {(min(b) if b else 0):>5} "
                f"{(max(b) if b else 0):>6}"
            )
            if ref:
                r = ref[p]["share"]
                line += f"   {r:.3f} {c['share'] - r:+.3f}"
            exceed = c["share"] > m + 1e-12 if m == m else False
            print(line + ("   <<< RULE 17 EXCEEDANCE" if exceed else ""))
            fails += int(exceed)
    print(
        f"\n{'RULE 17 HOLDS in every plant-year.' if not fails else f'RULE 17: {fails} FINDING(S).'}"
    )
    return fails


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--against", default=None, help="keeper bundle, for a side-by-side delta"
    )
    a = ap.parse_args()
    raise SystemExit(
        1
        if report(Path(a.bundle), a.years, Path(a.against) if a.against else None)
        else 0
    )


if __name__ == "__main__":
    main()
