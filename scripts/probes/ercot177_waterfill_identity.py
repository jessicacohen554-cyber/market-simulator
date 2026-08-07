"""ercot-177: prove the ERCOT measured-DAM water-fill ERASES any pre-overlay derate.

Establishes the rule-19 ``[R-ONE-MECH]`` ground recorded in
``results/calibration/FINDING-ercot177-temp-derate-refused-2026-08-07.md`` §3.

The claim
---------
``ScenarioConfig.temp_dependent_derate`` is applied in
:func:`market_sim.data.fleet.arrays._availability_matrix` (``arrays.py:817-878``).
The measured-DAM overlay ``ercot_thermal_dam_availability`` (+ ``_hourly``,
``_plant``) is applied **later**, in ``_apply_outage_overlays``
(``arrays.py:1310-1459``) — call order ``arrays.py:2632`` then ``:2636``.  Its
class-HOUR water-fill drives the cap-weighted class-hour mean availability to
the measured target ``t`` in BOTH branches, **independently of the pre-overlay
availability**::

    restore (t >= cur):  a' = a + lam * (ceil - a),  lam = (t-cur)/(ceil_mean-cur)
                         mean(a') = cur + lam*(ceil_mean-cur) = t
    remove  (t <  cur):  a' = a * (t/cur)
                         mean(a') = cur * (t/cur)     = t

so a temperature derate applied first is arithmetically erased at the class-hour
mean, surviving only as a WITHIN-class (here purely zonal) redistribution — and
with ``_plant`` armed, not even that for crosswalked plants, which are pinned to
their own measured site-hour fraction.  In the saturated branch (``t`` above the
ceiling mean, ``lam`` clipped to 1) ``a' = ceil`` for every unit and the arm is
bit-identical to the control.

Scope and honesty
-----------------
This is a proof of an ARITHMETIC PROPERTY of the committed code, run on
synthetic arrays.  :func:`_overlay` is a verbatim transcription of
``arrays.py:1430-1447``.  It is **NOT** a fleet measurement, and ercot-177 took
no fleet measurement: the lever was refused ex-ante on the prior ERCOT record
(owner closure 2026-07-09), of which this is an independent corroboration.

Usage::

    python scripts/probes/ercot177_waterfill_identity.py
"""

from __future__ import annotations

import numpy as np

#: Synthetic class: unit count and hours.  Sizes are arbitrary — the identity is
#: exact for any shape, and the seeds only fix the printed residuals.
_N_UNITS: int = 40
_N_HOURS: int = 500

#: Literature CT slope (``ScenarioConfig.temp_derate_slope_ct``) and ISO rating
#: point (``temp_derate_ref_c``), used ONLY to give the erased derate a
#: realistic magnitude.  Neither is proposed for ERCOT (rule 25 — ERCOT's own
#: measured slope is ~0/negative; FINDING §2).
_SLOPE_CT: float = 0.0126
_REF_C: float = 15.0


def _overlay(
    avail: np.ndarray, target: np.ndarray, cap: np.ndarray, ceil: np.ndarray
) -> np.ndarray:
    """Return availability after the class-HOUR DAM water-fill.

    Verbatim transcription of ``arrays.py:1430-1447``.

    Args:
        avail: ``(n_units, n_hours)`` pre-overlay availability.
        target: ``(n_hours,)`` measured DAM fraction; ``NaN`` where uncovered.
        cap: ``(n_units,)`` unit capacities (the water-fill's weights).
        ceil: ``(n_units,)`` per-unit forced-derate ceiling
            (``BIN_FORCED_DERATE_BY_YEAR``, 1.0 by default).

    Returns:
        ``(n_units, n_hours)`` post-overlay availability.
    """
    cap_sum = float(cap.sum())
    cur = (avail * cap[:, None]).sum(axis=0) / cap_sum
    covered = np.isfinite(target)
    restore = covered & (target >= cur)
    remove = covered & (target < cur)
    ceil_mean = float((ceil * cap).sum()) / cap_sum
    lam = np.clip((target - cur) / np.maximum(ceil_mean - cur, 1e-9), 0.0, 1.0)
    new = avail.copy()
    new[:, restore] = avail[:, restore] + lam[None, restore] * np.maximum(
        ceil[:, None] - avail[:, restore], 0.0
    )
    mu = np.where(remove, target / np.maximum(cur, 1e-9), 1.0)
    new[:, remove] = avail[:, remove] * mu[None, remove]
    return np.minimum(new, ceil[:, None])


def main() -> int:
    """Run the identity checks and print their residuals."""
    rng = np.random.default_rng(0)
    cap = rng.uniform(50.0, 800.0, _N_UNITS)
    cap_sum = float(cap.sum())
    ceil = np.ones(_N_UNITS)

    control = rng.uniform(0.35, 1.0, (_N_UNITS, _N_HOURS))
    target = rng.uniform(0.40, 0.95, _N_HOURS)

    # A temperature derate applied EARLIER: per-class slope x per-ZONE hourly
    # dry-bulb, so within a class the only variation is zonal (3 zones here).
    zone = rng.integers(0, 3, _N_UNITS)
    zone_curve = 1.0 - _SLOPE_CT * np.maximum(
        0.0, rng.uniform(10.0, 40.0, (3, _N_HOURS)) - _REF_C
    )
    armed = np.clip(control * zone_curve[zone, :], 0.0, 1.0)

    print("=== the water-fill lands on the measured target either way ===")
    for label, avail in (("control", control), ("arm (temp-derated)", armed)):
        post = _overlay(avail, target, cap, ceil)
        mean = (post * cap[:, None]).sum(axis=0) / cap_sum
        print(
            f"  {label:20s} max |class-hour mean - target| = "
            f"{np.abs(mean - target).max():.3e}"
        )

    post_c = _overlay(control, target, cap, ceil)
    post_a = _overlay(armed, target, cap, ceil)
    mean_delta = ((post_a - post_c) * cap[:, None]).sum(axis=0) / cap_sum
    print("\n=== what survives is within-class redistribution ONLY ===")
    print(f"  per-unit  max |arm - control| = {np.abs(post_a - post_c).max():.3e}")
    print(f"  cap-wtd class-hour mean delta = {np.abs(mean_delta).max():.3e}  <- zero")

    # Saturated branch: target above the ceiling mean -> lam clipped to 1 -> the
    # arm and the control are bit-identical, not merely equal in the mean.
    saturated = np.full(_N_HOURS, 1.5)
    delta_sat = np.abs(
        _overlay(armed, saturated, cap, ceil) - _overlay(control, saturated, cap, ceil)
    ).max()
    print("\n=== saturated branch (t > ceiling mean) ===")
    print(f"  per-unit  max |arm - control| = {delta_sat:.3e}  <- exactly zero")

    assert np.abs(mean_delta).max() < 1e-12, "class-hour mean is not erased"
    assert delta_sat == 0.0, "saturated branch is not bit-identical"
    print("\nALL_ASSERTIONS_PASS = true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
