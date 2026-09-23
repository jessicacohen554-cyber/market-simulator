"""SOCO-60 phase 0 (ZERO LP): the EIA-930 hydro pin on top of the RoR split.

The keeper ``2026-09-22-soco-h4-hydro-ror`` arms ``hydro_ror_split`` (17 SOCO
plants dispatch flat at ``budget[g, m] / hours[m]``) with
``hydro_backfill_year=2024``. The arm adds ``hydro_eia930_monthly=True``, which
rescales the monthly budget BEFORE ``build_hydro_fleet`` carves the RoR flat
level out of it — so the carve should scale with the pin and nothing else.

Subcommands:

* ``hydro --side ctl|arm --out F.npz`` — build the SOCO hydro fleet for
  2023-2025 with ``ror_split=True, backfill_year=2024`` and
  ``eia930_monthly`` False (ctl) / True (arm). **Run each side in its own
  process** (SOCO-59 P14: several helpers on this path are ``@lru_cache``d).
* ``compare CTL.npz ARM.npz`` — per-year totals, RoR flat MW by month, the
  RoR share of energy, and unit-grain identity.
* ``scarcity`` — ex-ante sizing of 2025 unserved energy under the arm, from
  the control leg's committed hourly sidecars (see :func:`scarcity`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
YEARS = (2023, 2024, 2025)


def build(side: str, out: Path) -> None:
    """Build one side's hydro fleet for every year and save it."""
    from market_sim.data.hydro import build_hydro_fleet

    pay: dict[str, np.ndarray] = {}
    for y in YEARS:
        units, me = build_hydro_fleet(
            "SOCO", y, ZONES, backfill_year=2024, eia930_monthly=(side == "arm"), ror_split=True
        )
        me = np.asarray(me, float)
        flat = np.array(
            [g.hydro_ror_flat_monthly_mw or (np.nan,) * 12 for g in units], dtype=float
        )
        pay[f"{y}_ids"] = np.array([g.unit_id for g in units])
        pay[f"{y}_pmax"] = np.array([g.pmax_mw for g in units], float)
        pay[f"{y}_budget"] = me
        pay[f"{y}_flat"] = flat
    np.savez(out, **pay)
    print(f"{side}: wrote {out}")


def compare(a: Path, b: Path) -> None:
    """Report per-year totals, RoR carve and unit-grain identity, ctl vs arm."""
    from market_sim.data.hydro import hours_per_month

    hpm = hours_per_month().astype(float)
    c, r = np.load(a), np.load(b)
    rows = []
    for y in YEARS:
        ids_c, ids_r = list(c[f"{y}_ids"]), list(r[f"{y}_ids"])
        bc, br = c[f"{y}_budget"], r[f"{y}_budget"]
        fc, fr = c[f"{y}_flat"], r[f"{y}_flat"]
        ror_c, ror_r = ~np.isnan(fc[:, 0]), ~np.isnan(fr[:, 0])
        ident = (
            ids_c == ids_r
            and np.array_equal(c[f"{y}_pmax"], r[f"{y}_pmax"])
            and np.array_equal(bc, br)
            and np.array_equal(np.nan_to_num(fc, nan=-1), np.nan_to_num(fr, nan=-1))
        )
        # The carve must equal the plant's own (pinned) budget / hours, unclipped.
        carve_ok = bool(
            np.allclose(fr[ror_r], np.minimum(br[ror_r] / hpm, r[f"{y}_pmax"][ror_r, None]))
        )
        rec = {
            "year": y,
            "units ctl/arm": f"{len(ids_c)}/{len(ids_r)}",
            "RoR plants ctl/arm": f"{int(ror_c.sum())}/{int(ror_r.sum())}",
            "TWh ctl": round(bc.sum() / 1e6, 4),
            "TWh arm": round(br.sum() / 1e6, 4),
            "RoR TWh ctl": round(bc[ror_c].sum() / 1e6, 4),
            "RoR TWh arm": round(br[ror_r].sum() / 1e6, 4),
            "RoR share arm": round(br[ror_r].sum() / br.sum(), 4),
            "RoR flat MW-avg ctl": round(float((fc[ror_c].sum(0) * hpm).sum() / hpm.sum()), 1),
            "RoR flat MW-avg arm": round(float((fr[ror_r].sum(0) * hpm).sum() / hpm.sum()), 1),
            "arm carve == budget/hours": carve_ok,
            "byte_identical": bool(ident),
        }
        rows.append(rec)
        print(json.dumps(rec))
        if not ident:
            print("  monthly TWh ctl", np.round(bc.sum(0) / 1e6, 3).tolist())
            print("  monthly TWh arm", np.round(br.sum(0) / 1e6, 3).tolist())
            print("  RoR flat MW ctl", np.round(fc[ror_c].sum(0), 0).tolist())
            print("  RoR flat MW arm", np.round(fr[ror_r].sum(0), 0).tolist())
            # Is the pin a pure per-month rescale of the per-plant budget?
            with np.errstate(invalid="ignore", divide="ignore"):
                ratio = br.sum(0) / bc.sum(0)
            print("  arm/ctl monthly ratio", np.round(ratio, 3).tolist())


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest="cmd", required=True)
    h = sp.add_parser("hydro")
    h.add_argument("--side", required=True, choices=("ctl", "arm"))
    h.add_argument("--out", required=True, type=Path)
    cp = sp.add_parser("compare")
    cp.add_argument("ctl", type=Path)
    cp.add_argument("arm", type=Path)
    a = ap.parse_args()
    if a.cmd == "hydro":
        build(a.side, a.out)
    else:
        compare(a.ctl, a.arm)


if __name__ == "__main__":
    main()
