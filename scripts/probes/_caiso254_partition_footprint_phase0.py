"""caiso-254 phase 0 (ZERO LP): the class-partition repair's own FOOTPRINT, F(y).

Registered in ``results/calibration/ADDENDUM-caiso254-partition-repair-screen-2026-09-06.md``
§3.1, which fixes both the estimator and what it is used for **before** it is
run: F(y) NAMES the rule-29 screen year, and it contains no price actual, no
residual and no criterion. The screen year is ``argmax_y F(y)`` and nothing
else — naming it on the biggest residual, or on which year a gate can see,
is the fitted-mechanism selection rule 1 ``[R-STRUCT]`` exists to forbid.

Construction (the caiso-251/252 two-rebuild pattern, ~90 s per arm):
two on-recipe ``fleet_only`` rebuilds of the keeper differing ONLY in which
``caiso_offer_curve_measured.json`` is on disk — the frozen artifact vs the
repaired one — differenced on the model's own offer array ``mc_base``. Nothing
is reimplemented: the pricing arithmetic is whatever ``bins_to_fleet`` does, so
the footprint is the model's, not this file's reading of it.

    F(y) = sum over GAS tranches of  pmax[u] * mean_t |dmc[u, t]|   (MW * $/MWh)
    X(y) = count of gas tranche PAIRS whose merit order crosses

NULL CONTROL: ``--null`` points both arms at the SAME artifact. F must come
back exactly 0.0 and X exactly 0; anything else means the harness itself is
non-deterministic and no footprint it reports can be trusted.

Output: ``results/calibration/_caiso254_partition_footprint_phase0.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso254_partition_footprint_phase0.py --null
    PYTHONPATH=.:src uv run python scripts/probes/_caiso254_partition_footprint_phase0.py \
        --repaired data/raw/_validation-source/caiso_offer_curve_measured.REPAIRED.json
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/caiso252_b1_notrim"
LIVE = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
OUT = REPO / "results/calibration/_caiso254_partition_footprint_phase0.json"
YEARS = (2023, 2024, 2025)
T = 8760

#: Tranche ids of the five CAISO gas classes the repair can reach. Matched as
#: substrings of the LP unit id, which carries "<PLANT>_<CLASS>_<band>".
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")


def _rebuild(year: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """One on-recipe ``fleet_only`` rebuild -> (mc_base, pmax, unit_ids)."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(BUNDLE, year))
    clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    return (
        np.asarray(st["mc_base"], dtype=float),
        np.asarray(fa.pmax, dtype=float),
        list(fa.unit_ids),
    )


def _arm(year: int, artifact: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Rebuild with ``artifact`` swapped in as the measured surface, then restore."""
    backup = LIVE.with_suffix(".json.caiso254bak")
    shutil.copy2(LIVE, backup)
    try:
        if artifact.resolve() != LIVE.resolve():
            shutil.copy2(artifact, LIVE)
        return _rebuild(year)
    finally:
        shutil.move(backup, LIVE)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--repaired",
        type=Path,
        default=None,
        help="the re-derived artifact; omit with --null for the null control",
    )
    ap.add_argument(
        "--null",
        action="store_true",
        help="point BOTH arms at the frozen artifact; F must be exactly 0",
    )
    a = ap.parse_args()
    if not a.null and a.repaired is None:
        ap.error("pass --repaired <path> or --null")
    arm_b = LIVE if a.null else a.repaired
    if not arm_b.exists():
        raise SystemExit(f"repaired artifact not found: {arm_b}")

    res: dict = {"null_control": bool(a.null), "arm_b": str(arm_b), "years": {}}
    for y in YEARS:
        mc_a, pmax, ids = _arm(y, LIVE)
        mc_b, pmax_b, ids_b = _arm(y, arm_b)
        if ids != ids_b:
            raise SystemExit(
                f"{y}: the two arms built DIFFERENT fleets "
                f"({len(ids)} vs {len(ids_b)} units) — the repair is supposed to "
                "reprice tranches, never add or drop them"
            )
        gas = np.array([any(c in u for c in GAS_CLASSES) for u in ids])
        dmc = mc_b - mc_a
        # mean_t |dmc| per unit; mc_base is (n_units, T) but tolerate 1-D.
        per_unit = np.abs(dmc).mean(axis=1) if dmc.ndim == 2 else np.abs(dmc)
        f = float((per_unit[gas] * pmax[gas]).sum())
        # X: merit-order crossings among gas tranches, on the hour-mean offer.
        m_a = mc_a.mean(axis=1) if mc_a.ndim == 2 else mc_a
        m_b = mc_b.mean(axis=1) if mc_b.ndim == 2 else mc_b
        ga, gb = m_a[gas], m_b[gas]
        n = len(ga)
        iu = np.triu_indices(n, 1)
        crossings = int(
            (np.sign(ga[iu[0]] - ga[iu[1]]) != np.sign(gb[iu[0]] - gb[iu[1]])).sum()
        )
        moved = np.abs(per_unit) > 1e-9
        res["years"][y] = {
            "F_mw_usd_per_mwh": round(f, 3),
            "X_merit_crossings": crossings,
            "n_gas_tranches": int(gas.sum()),
            "n_tranches_moved": int(moved.sum()),
            "n_nongas_tranches_moved": int((moved & ~gas).sum()),
            "max_abs_dmc_usd_per_mwh": round(float(np.abs(per_unit).max()), 4),
            "gas_cap_gw": round(float(pmax[gas].sum() / 1e3), 3),
        }
        r = res["years"][y]
        print(
            f"{y}: F={r['F_mw_usd_per_mwh']:,.1f} MW*$/MWh  X={r['X_merit_crossings']}  "
            f"moved {r['n_tranches_moved']}/{r['n_gas_tranches']} gas "
            f"({r['n_nongas_tranches_moved']} NON-gas)  max|dmc|={r['max_abs_dmc_usd_per_mwh']}"
        )

    if a.null:
        bad = {
            y: v
            for y, v in res["years"].items()
            if v["F_mw_usd_per_mwh"] != 0.0 or v["X_merit_crossings"] != 0
        }
        res["null_control_verdict"] = "PASS" if not bad else "FAIL"
        print(
            "NULL CONTROL: PASS — the harness is deterministic"
            if not bad
            else f"NULL CONTROL: FAIL — {bad}"
        )
    else:
        best = max(res["years"], key=lambda y: res["years"][y]["F_mw_usd_per_mwh"])
        res["screen_year"] = int(best)
        print(f"SCREEN YEAR = argmax F(y) = {best}")
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
