"""miso-220 offer-curve tables — the arm's ONLY declared delta, in one place.

**Owner ruling, 2026-09-05, which scopes this module.** The offer-curve band
multipliers ARE the intended channel for tuning on price and adjusting merit
order; **one config held across 2023-2025** is the discipline that makes that
legitimate rather than per-year fitting; and **steam gas is held as is** —
``ST_GAS`` and ``ST_GAS_INTERMEDIATE`` (the two duty-split halves of one steam-gas
cohort, split at miso-217), per the owner's answer of 2026-09-05.

Why the table is written out in full rather than derived from the keeper's config.
The keeper's ``run_config.json`` carries an ``offer_curve_by_group`` with a SINGLE
entry (``ST_GAS_INTERMEDIATE``); every other class resolves from the per-ISO curves
``backcast_config`` merges in at solve time, and ``replay_keeper --set`` applies
AFTER that merge (the documented seam). An arm that passes a partial table would
therefore silently drop every class it omits. So both tables below are FULL, and
``_miso220_liveness.py`` S-1 asserts that ``BASELINE_TABLE`` reproduces the
keeper's own ``mc`` byte-identically before any LP is spent — if it does not, the
arm carries an undeclared second delta and is void.

``BASELINE_TABLE`` is the keeper's own resolved table, recovered from the miso-218
bundle's recorded config by dividing its four band multipliers by that probe's
uniform 1.10. The recovery is checked at import: ``ST_GAS_INTERMEDIATE``'s row is
the one class the KEEPER records explicitly, and the derived row must match it
exactly (it does: 1.0 / 1.0 / 1.15 / 2.2).

``ARM_TABLE`` applies ``LIFT`` = 1.10 to the four band multipliers of every class
EXCEPT ``HELD_CLASSES``. Deliberately NOT scaled anywhere:

* ``phys_*`` keys — measured physics (the miso-217 coverage arm), never a tuning knob;
* ``econ_low_share`` / ``pct_peaking`` — structural tranche shares, so this arm is a
  pure LEVEL move and the peak-band reshape stays a separate, later question;
* the held steam-gas classes, entire.

Within-class band RATIOS are preserved exactly for every lifted class (a common
factor cancels), so fossil merit order is preserved WITHIN each lifted class; what
moves is the lifted classes against the held steam-gas ones, which is the intended
merit-order adjustment the ruling names.
"""

from __future__ import annotations

# The uniform factor applied to the four band multipliers of every non-held class.
LIFT: float = 1.10

# Steam gas, held at the keeper's own multipliers (owner ruling 2026-09-05).
HELD_CLASSES: frozenset[str] = frozenset({"ST_GAS", "ST_GAS_INTERMEDIATE"})

# The four band multipliers the lift touches. Everything else in a row is structural
# or measured and is carried through unchanged.
_BANDS: tuple[str, ...] = ("committed", "econ_low", "econ_high", "peak")

# The keeper's own resolved per-class offer curves (see module docstring for the
# recovery and the S-1 check that verifies it).
BASELINE_TABLE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 1.005, "econ_low": 0.95, "econ_high": 1.08, "peak": 2.25,
        "econ_low_share": 0.5, "pct_peaking": 8.0,
        "phys_committed": 1.005, "phys_econ_low": 0.887,
        "phys_econ_high": 1.008, "phys_peak": 2.25,
    },
    "CC_INTERMEDIATE": {
        "committed": 1.005, "econ_low": 0.95, "econ_high": 1.08, "peak": 2.25,
        "econ_low_share": 0.5, "pct_peaking": 8.0,
    },
    "CC_CHP": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.0, "peak": 2.25,
        "econ_low_share": 0.5, "pct_peaking": 8.0,
        "phys_committed": 1.508, "phys_econ_low": 0.995,
        "phys_econ_high": 1.017, "phys_peak": 2.25,
    },
    "CT_CHP": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.0, "peak": 1.0,
        "econ_low_share": 0.5,
        "phys_committed": 0.857, "phys_econ_low": 0.785,
        "phys_econ_high": 0.825, "phys_peak": 1.0,
    },
    "CT_PEAKER": {
        "committed": 1.025, "econ_low": 1.0, "econ_high": 1.0, "peak": 4.0,
        "econ_low_share": 0.526, "pct_peaking": 7.0,
        "phys_committed": 1.025, "phys_econ_low": 0.687,
        "phys_econ_high": 0.691, "phys_peak": 1.0,
    },
    "CT_INTERMEDIATE": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.2, "peak": 3.0,
        "econ_low_share": 0.5, "pct_peaking": 5.0,
    },
    "ST_GAS": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.0, "peak": 1.0,
        "econ_low_share": 0.5, "pct_peaking": 15.0,
        "phys_committed": 1.079, "phys_econ_low": 0.812,
        "phys_econ_high": 0.849, "phys_peak": 1.0,
    },
    "ST_GAS_INTERMEDIATE": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.15, "peak": 2.2,
        "econ_low_share": 0.5, "pct_peaking": 6.0,
    },
    "COAL_LIGNITE": {
        "committed": 1.0, "econ_low": 1.14, "econ_high": 1.15, "peak": 1.55,
        "econ_low_share": 0.556,
    },
    "COAL_PRB": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.19, "peak": 1.48,
        "econ_low_share": 0.556,
    },
    "COAL_BIT": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.1, "peak": 1.45,
        "econ_low_share": 0.55,
    },
    "COAL_WC": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.02, "peak": 1.2,
        "econ_low_share": 0.55,
    },
    "COAL": {
        "committed": 1.0, "econ_low": 1.0, "econ_high": 1.1, "peak": 1.45,
        "econ_low_share": 0.55,
    },
}

# The keeper records this ONE row explicitly; the derived baseline must match it.
_KEEPER_EXPLICIT_ST_GAS_INTERMEDIATE = {
    "committed": 1.0, "econ_low": 1.0, "econ_high": 1.15, "peak": 2.2,
    "econ_low_share": 0.5, "pct_peaking": 6.0,
}
assert BASELINE_TABLE["ST_GAS_INTERMEDIATE"] == _KEEPER_EXPLICIT_ST_GAS_INTERMEDIATE, (
    "derived baseline disagrees with the keeper's own recorded ST_GAS_INTERMEDIATE row"
)


def _lift(row: dict[str, float], factor: float) -> dict[str, float]:
    """Scale only the four band multipliers; carry phys_* and shares through unchanged."""
    return {k: (round(v * factor, 6) if k in _BANDS else v) for k, v in row.items()}


ARM_TABLE: dict[str, dict[str, float]] = {
    k: (dict(v) if k in HELD_CLASSES else _lift(v, LIFT))
    for k, v in BASELINE_TABLE.items()
}

# Ratio preservation within every lifted class, and exact hold on the steam-gas pair.
for _k, _row in BASELINE_TABLE.items():
    _arm = ARM_TABLE[_k]
    if _k in HELD_CLASSES:
        assert _arm == _row, f"{_k} must be byte-identical to the keeper"
        continue
    for _b in _BANDS:
        assert abs(_arm[_b] - _row[_b] * LIFT) < 1e-9, f"{_k}.{_b} lift is wrong"
    for _key, _val in _row.items():
        if _key not in _BANDS:
            assert _arm[_key] == _val, f"{_k}.{_key} must not move (structural/measured)"
