"""Year classification for the calibration rubric.

``CALIBRATION_YEARS`` is the in-sample training window (2023-2025).
:func:`tier_for_year` labels any year train / validation / locked_test.

**THIS MODULE NO LONGER AUTHORIZES ANYTHING.** ``[R-HOLDOUT]`` — the three-tier
holdout regime and every gate that enforced it — was REMOVED on 2026-09-09 by
owner instruction ("Remove the holdout year rule"). Gone with it: the
``complete`` / ``final`` markers as spend authorizations, ``holdout-freeze.json``,
the ``--holdout-authorized`` flag, the ``run_calibration_full`` year gate, the
``dashboard_add_run`` registration marker gate, the D-6 quarantine, the
``audit_keepers`` M1 marker check and the CI ``quarantine-gates`` job. **Any year
may be solved, scored and registered freely.**

What survives here is a PURE CLASSIFIER carrying no permission meaning, kept
because two live consumers still need to know which side of the training window
a year sits on:

  * ``calibration_verdict._apply_c3c_standing_rule`` — rule 22's ordinal now
    carries ``[R-C3C]``, whose v3.6 limb drops the lone-failure condition on an
    out-of-training year. Measured at the removal over all 15 registered runs
    carrying an out-of-training year: 0 determination flips.
  * ``rubric_consts`` and the dashboard — labelling a year's tier for display.

The hindcast window helpers (``HINDCAST_*``,
``hindcast_solve_year_violations``) are a SEPARATE forecast-program concern and
are untouched by the removal.

Stdlib-only (no imports) — consumed by the deploy/CI paths that run on a bare
``python3``.
"""

from __future__ import annotations

CALIBRATION_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})

# Tier names. Also the keys of TIER_MARKER_BLOCK below.
TIER_TRAIN = "train"
TIER_VALIDATION = "validation"
TIER_LOCKED = "locked_test"

# Rule 22's locked test, verbatim: "Locked test = 2019 and H1-2026". 2026 is
# the forward-edge test; only a BACKCAST of H1-2026 (or scoring against measured
# H1-2026 actuals) is quarantined — forecast-mode runs spanning 2026+ use no
# measured actuals and are not restricted, so they never reach this gate.
LOCKED_TEST_YEARS: frozenset[int] = frozenset({2019, 2026})

# Rule 22's validation ladder: "2022, extensible backward as a staged ladder
# (2022 -> 2020-2022 -> earlier as data lands and is authorized)". Enumerated
# rather than open-ended so that adding a rung is an explicit, reviewable edit.
#
# 2018 REMOVED 2026-08-06 (owner decision, session neiso-86: "drop 2018 from
# solve years then and have it be 2019-2025 for all ISOs to keep things
# simpler"). The program's working span is now 2019-2025 and the ladder's
# earliest rung is 2020. This is a RESTRICTION, not a relaxation: with 2018
# absent from every enumerated set, `year_tier` falls through to its
# fail-closed default and treats it as LOCKED-TEST tier, so 2018 needs a
# `final` marker no ISO holds and is unsolvable in practice.
#
# The substantive reason 2018 is not merely "simpler" to drop: NEISO's 2018
# gas basis is UNREPAIRABLE at present. neiso-86 replaced the seasonally
# inverted EIA N3050MA3 proxy with the measured ISO-NE MA index for 2019-2022,
# but ISO-NE migrated its newswire mid-2018 and the March-June 2018 recaps were
# never carried over (WP archive jumps 2018-03-26 -> 2018-08-24, legacy
# /updates/ URLs 301 to the homepage, no Wayback capture). Those four rows
# remain proxy-sourced, and June-2018 (+6.2124) is one of the inverted summer
# values -- so a 2018 solve would fire the summer inversion in the worst month.
# See results/calibration/FINDING-neiso86-gas-basis-intake-2026-08-06.md 5.1.
VALIDATION_YEARS: frozenset[int] = frozenset({2020, 2021, 2022})

# ---------------------------------------------------------------------------
# Capacity-hindcast carve-outs (FH-1 — moved here out of prose, hindcast-
# forward plan §5.2: "asserted today only in prose and a local
# _validate_window"). These are the ONLY out-of-training allowances the
# vintage-seeded hindcast harness (scripts/run_capacity_hindcast.py) carries,
# and they are marker-free BY DESIGN: a 2021 SEED solve prices the first
# evolution step and is never scored; a BRIDGE year is evolved but never
# solved, its data never read. Anything else out-of-training needs the tier
# marker machinery above — the harness fails closed.
# ---------------------------------------------------------------------------

# Seed years: solvable by the hindcast harness, never scored. (T1-H solves
# 2021 to seed the price/margin signal for the 2022→2023 evolution.)
HINDCAST_SEED_YEARS: frozenset[int] = frozenset({2021})

# Bridge years: a hindcast window may SPAN them, evolving the fleet across,
# but never solves them or reads their data (2022 = validation-tier bridge;
# 2026 = locked-test/forward edge, un-bridged only by a crossover that solves
# it as a forecast-mode year reading no measured actuals). Mirrors
# market_sim.runner.HINDCAST_BRIDGE_YEARS — src must not import scripts, so
# the runner keeps its own constant and tests assert the parity.
HINDCAST_BRIDGE_YEARS: frozenset[int] = frozenset({2022, 2026})

# The full solvable set for a plain (or full-forward T1-FF) hindcast window:
# the training years plus the seed. NOT a scoring set — scoring is
# CALIBRATION_YEARS only, both bounds (the >=2026 refusal and the FH-1
# symmetric <2023 lower bound in scripts/score_crossover.py).
HINDCAST_SOLVE_YEARS: frozenset[int] = CALIBRATION_YEARS | HINDCAST_SEED_YEARS


def hindcast_solve_year_violations(years) -> list[str]:
    """Return the violations in a proposed hindcast solve-year set.

    The fail-closed check behind the harness's window validation: every
    proposed SOLVE year must be either a training year or an enumerated seed
    year; each violation names the year's tier so the refusal is
    self-explaining. Bridge years must not be passed here — they are never
    solve years (the harness skips them before this check).

    Args:
        years: Iterable of proposed solve years (bridges already excluded).

    Returns:
        Human-readable violation strings; empty when the set is legal.
    """
    out: list[str] = []
    for y in sorted({int(y) for y in years}):
        if y in HINDCAST_SOLVE_YEARS:
            continue
        tier = tier_for_year(y)
        out.append(
            f"year {y} is not a hindcast-solvable year (tier: {tier}; "
            f"allowed: training {sorted(CALIBRATION_YEARS)} + seed "
            f"{sorted(HINDCAST_SEED_YEARS)})"
        )
    return out


def tier_for_year(year: int) -> str:
    """Return the tier label of ``year`` (classification only, no permission).

    A year in none of the enumerated sets (a future year, a pre-2018 year) is
    labelled ``locked_test``. This is now a LABEL only: nothing refuses a solve,
    score or registration on the strength of it (``[R-HOLDOUT]`` removed
    2026-09-09).

    Args:
        year: Solve/score/registration year.

    Returns:
        One of ``TIER_TRAIN`` / ``TIER_VALIDATION`` / ``TIER_LOCKED``.
    """
    year = int(year)
    if year in CALIBRATION_YEARS:
        return TIER_TRAIN
    if year in VALIDATION_YEARS:
        return TIER_VALIDATION
    return TIER_LOCKED
