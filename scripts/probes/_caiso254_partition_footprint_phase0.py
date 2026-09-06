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

INSTRUMENT CORRECTION (caiso-255, 2026-09-06 — made by CODE INSPECTION, before
the repaired artifact existed and therefore before any statistic of it could be
seen; the caiso-254 §5.1 precedent)
------------------------------------------------------------------------------
As first written this probe swapped ONE artifact, ``caiso_offer_curve_measured
.json``. The derive writes TWO, and the keeper consumes both: it carries
``caiso_offer_surface_conditional = True``, and ``data/fleet/offer_surfaces.py
::_COND_SURFACE_SPECS["CAISO"]`` reads ``caiso_offer_surface_condbinned.json``
for CC_REGULAR + CT_PEAKER. Two consequences, both fixed here:

1. **Arm B was a HYBRID** — repaired static bands over the FROZEN conditional
   ladder — which is a configuration no solve would ever run. Both artifacts
   are now swapped together.
2. **The footprint was blind to the P1 channel.** ``mc_base`` is the assembled
   **P0** objective; the conditional ladder is a **P1-only** markup built at
   ``run_calibration.py:4333``, after the ``fleet_only`` exit. Since P1 is THE
   main run and the pass every run is scored on, a footprint read off
   ``mc_base`` alone cannot see half of what the repair moves.

**What is NOT changed: the screen-year rule.** ``F`` keeps its registered
definition and ``argmax_y F`` still names the year. ``F_p1`` (mc_base + the
conditional markup) is reported BESIDE it. If the two argmaxes disagree, that
is recorded as a power caveat on the screen and the REGISTERED statistic still
governs — choosing the other year after seeing both would be exactly the
selection §3.1 exists to forbid.

NULL CONTROL: ``--null`` points both arms at the SAME artifacts. F, F_p1 and X
must come back exactly 0.0 / 0.0 / 0; anything else means the harness itself is
non-deterministic and no footprint it reports can be trusted.

Output: ``results/calibration/_caiso254_partition_footprint_phase0.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso254_partition_footprint_phase0.py --null
    PYTHONPATH=.:src uv run python scripts/probes/_caiso254_partition_footprint_phase0.py \
        --repaired data/raw/_validation-source/caiso_offer_curve_measured.REPAIRED.json \
        --repaired-cond data/raw/_validation-source/caiso_offer_surface_condbinned.REPAIRED.json
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
#: The SECOND artifact the derive writes and the keeper consumes. INSTRUMENT
#: CORRECTION (caiso-255, by code inspection BEFORE any repaired statistic
#: existed — the caiso-254 §5.1 precedent): as first written this probe swapped
#: the STATIC bands only, so arm B was a HYBRID (repaired bands + the FROZEN
#: conditional ladder), which is not the configuration the screen would solve.
#: The keeper carries `caiso_offer_surface_conditional = True` and the CAISO
#: spec reads this file for CC_REGULAR + CT_PEAKER
#: (`data/fleet/offer_surfaces.py::_COND_SURFACE_SPECS["CAISO"]`), and the
#: derive rewrites it from the same repartitioned buckets. Both are swapped now.
LIVE_COND = REPO / "data/raw/_validation-source/caiso_offer_surface_condbinned.json"
OUT = REPO / "results/calibration/_caiso254_partition_footprint_phase0.json"
YEARS = (2023, 2024, 2025)
T = 8760

#: Tranche ids of the five CAISO gas classes the repair can reach. Matched as
#: substrings of the LP unit id, which carries "<PLANT>_<CLASS>_<band>".
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")


def _rebuild(year: int) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    """One on-recipe ``fleet_only`` rebuild -> (mc_base, pmax, unit_ids, markup).

    ``mc_base`` is the assembled **P0** objective, which is the only channel the
    STATIC bands (`caiso_offer_curve_measured.json`) reach. The conditional
    ladder (`caiso_offer_surface_condbinned.json`) is a **P1-only** markup built
    at `run_calibration.py:4333` and is NOT part of the `fleet_only` payload —
    so a footprint read off ``mc_base`` alone is blind to half of what the
    repair moves, and P1 is the pass every run is scored on. The markup is
    therefore rebuilt here from the same arrays the orchestrator hands it, using
    the orchestrator's own net-load expression verbatim.
    """
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
    mc_base = np.asarray(st["mc_base"], dtype=float)

    # The P1-only conditional markup, built exactly as run_calibration.py:4327
    # builds it (same gate, same net-load expression, same call).
    markup = np.zeros_like(np.atleast_2d(mc_base))
    cfg = st["config"]
    if getattr(cfg, "caiso_offer_surface_conditional", False):
        from market_sim.data.fleet import build_caiso_offer_surface_conditional_markup

        demand, wind_cf, wind_cap = st["demand"], st["wind_cf"], st["wind_cap"]
        solar_cf, solar_cap = st["solar_cf"], st["solar_cap"]
        net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        m = build_caiso_offer_surface_conditional_markup(
            fa, st["fleet"], st["fuel_prices"], net_load, cfg
        )
        if m is not None:
            markup = np.asarray(m, dtype=float)

    return mc_base, np.asarray(fa.pmax, dtype=float), list(fa.unit_ids), markup


def _arm(
    year: int, artifact: Path, cond: Path | None = None
) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    """Rebuild with ``artifact`` (+ ``cond``) swapped in, then restore both.

    BOTH artifacts move together: the derive writes them from the same
    repartitioned buckets, so swapping only one would build a hybrid that no
    solve would ever run (see ``LIVE_COND``).
    """
    pairs = [(LIVE, artifact)] + ([(LIVE_COND, cond)] if cond is not None else [])
    backups = []
    try:
        for live, src in pairs:
            bak = live.with_suffix(".json.caiso254bak")
            shutil.copy2(live, bak)
            backups.append((live, bak))
            if src.resolve() != live.resolve():
                shutil.copy2(src, live)
        return _rebuild(year)
    finally:
        for live, bak in backups:
            shutil.move(bak, live)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--repaired",
        type=Path,
        default=None,
        help="the re-derived artifact; omit with --null for the null control",
    )
    ap.add_argument(
        "--repaired-cond",
        type=Path,
        default=None,
        help="the re-derived CONDITIONAL ladder (caiso_offer_surface_condbinned"
        ".json). The keeper consumes it and the derive rewrites it from the same "
        "repartitioned buckets, so it is swapped alongside --repaired; omitting "
        "it builds a hybrid arm and is refused unless --null",
    )
    ap.add_argument(
        "--null",
        action="store_true",
        help="point BOTH arms at the frozen artifact; F must be exactly 0",
    )
    a = ap.parse_args()
    if not a.null and a.repaired is None:
        ap.error("pass --repaired <path> or --null")
    if not a.null and a.repaired_cond is None:
        ap.error(
            "pass --repaired-cond <path> too: the keeper carries "
            "caiso_offer_surface_conditional=True, so a static-only swap builds "
            "a configuration no solve would run"
        )
    arm_b = LIVE if a.null else a.repaired
    arm_b_cond = LIVE_COND if a.null else a.repaired_cond
    for p in (arm_b, arm_b_cond):
        if not p.exists():
            raise SystemExit(f"repaired artifact not found: {p}")

    res: dict = {
        "null_control": bool(a.null),
        "arm_b": str(arm_b),
        "arm_b_cond": str(arm_b_cond),
        "channels": {
            "F_mw_usd_per_mwh": (
                "REGISTERED statistic (ADDENDUM-caiso254 §3.1): the P0 offer "
                "array mc_base, which is the channel the STATIC bands reach"
            ),
            "F_p1_mw_usd_per_mwh": (
                "INSTRUMENT EXTENSION (caiso-255, by code inspection before any "
                "repaired statistic existed): mc_base + the P1-only conditional "
                "ladder markup — the offer P1 actually clears on, and P1 is the "
                "pass every run is scored on"
            ),
            "screen_year_rule": (
                "argmax_y F (the REGISTERED statistic) governs. F_p1 is reported "
                "beside it; if the two argmaxes DISAGREE that is reported as a "
                "power caveat and the registered statistic still names the year — "
                "picking the other one after seeing both is selection"
            ),
        },
        "years": {},
    }
    for y in YEARS:
        mc_a, pmax, ids, mk_a = _arm(y, LIVE, LIVE_COND)
        mc_b, pmax_b, ids_b, mk_b = _arm(y, arm_b, arm_b_cond)
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
        # The P1 offer = P0 objective + the conditional ladder markup. Reported
        # beside the registered statistic, never in place of it.
        p1_a, p1_b = np.atleast_2d(mc_a) + mk_a, np.atleast_2d(mc_b) + mk_b
        per_unit_p1 = np.abs(p1_b - p1_a).mean(axis=1)
        f_p1 = float((per_unit_p1[gas] * pmax[gas]).sum())
        mk_delta = float(np.abs(mk_b - mk_a).max())

        moved = np.abs(per_unit) > 1e-9
        res["years"][y] = {
            "F_mw_usd_per_mwh": round(f, 3),
            "F_p1_mw_usd_per_mwh": round(f_p1, 3),
            "max_abs_cond_markup_delta": round(mk_delta, 4),
            "n_tranches_moved_p1": int((per_unit_p1 > 1e-9).sum()),
            "X_merit_crossings": crossings,
            "n_gas_tranches": int(gas.sum()),
            "n_tranches_moved": int(moved.sum()),
            "n_nongas_tranches_moved": int((moved & ~gas).sum()),
            "max_abs_dmc_usd_per_mwh": round(float(np.abs(per_unit).max()), 4),
            "gas_cap_gw": round(float(pmax[gas].sum() / 1e3), 3),
        }
        r = res["years"][y]
        print(
            f"{y}: F={r['F_mw_usd_per_mwh']:,.1f} F_p1={r['F_p1_mw_usd_per_mwh']:,.1f} "
            f"MW*$/MWh  X={r['X_merit_crossings']}  "
            f"moved {r['n_tranches_moved']}/{r['n_gas_tranches']} gas "
            f"({r['n_nongas_tranches_moved']} NON-gas)  max|dmc|={r['max_abs_dmc_usd_per_mwh']}"
        )

    if a.null:
        bad = {
            y: v
            for y, v in res["years"].items()
            if v["F_mw_usd_per_mwh"] != 0.0
            or v["F_p1_mw_usd_per_mwh"] != 0.0
            or v["X_merit_crossings"] != 0
        }
        res["null_control_verdict"] = "PASS" if not bad else "FAIL"
        print(
            "NULL CONTROL: PASS — the harness is deterministic"
            if not bad
            else f"NULL CONTROL: FAIL — {bad}"
        )
    else:
        best = max(res["years"], key=lambda y: res["years"][y]["F_mw_usd_per_mwh"])
        best_p1 = max(
            res["years"], key=lambda y: res["years"][y]["F_p1_mw_usd_per_mwh"]
        )
        res["screen_year"] = int(best)
        res["screen_year_p1_channel"] = int(best_p1)
        res["channels_agree"] = bool(best == best_p1)
        print(f"SCREEN YEAR = argmax F(y) = {best}  (F_p1 argmax = {best_p1})")
        if best != best_p1:
            print(
                "CAVEAT: the registered statistic and the P1-channel extension "
                "name DIFFERENT years. The REGISTERED statistic governs; the "
                "divergence is a power caveat on the screen, not a licence to "
                "pick the other year."
            )
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
