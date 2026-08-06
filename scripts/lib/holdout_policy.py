"""Single home for the holdout-quarantine policy constants (CLAUDE.md rule 22).

``CALIBRATION_YEARS`` is the in-sample training window (2023-2025) — the ONLY
years tuned against (rule 22 train/validation/locked-test split). Any solve,
score, or registration touching a year outside it is a designated holdout and is
gated on a per-ISO marker in ``MARKER_FILE``.

TWO-TIER MARKERS (owner decision 2026-07-31)
--------------------------------------------
Rule 22 has always defined THREE year tiers, but the gates enforced only ONE
marker: any ``complete`` entry authorized every out-of-training year at once —
the iterable 2022 validation ladder AND the touch-once 2019 / H1-2026 locked
test. Rule 22 said so itself ("the CI gate is tier-agnostic — it enforces the
marker, not the validation/locked distinction, which is a discipline clause").
That made the most expensive, least reversible spend in the whole policy
reachable on the same declaration as the cheapest one.

The marker file now carries two INDEPENDENT blocks, and the gates below select
by the tier of the year being touched:

  ``complete``  → **validation tier** (2022 and its backward ladder). Iterable
                  by design: a miss may send you back to re-tune 2023-2025 and
                  re-solve. NOT training — a validation number is model-
                  SELECTION evidence, never a certified out-of-sample skill
                  number.
  ``final``     → **locked-test tier** (2019, H1-2026). Touch-once, ever: scored
                  EXACTLY ONCE per ISO with the frozen keeper config, recorded
                  whatever it is, and no calibration change may respond to it.

An ISO in ``complete`` but not ``final`` may spend its validation ladder and
NOTHING else. Absence from ``final`` is deliberately ambiguous between "not yet
granted" and "already spent, never re-grantable" — the marker file's per-ISO
``locked_test`` note is what distinguishes them, and a session must read it
rather than infer a grant from the absence.

The freeze (``holdout-freeze.json``) outranks both blocks and is checked first.

Imported by the three rule-22 gates so the window, tiers and marker path are
defined exactly once instead of triplicated behind a cross-file parity test:

  * ``run_calibration_full.enforce_holdout_year_gate`` (the ``--year`` gate),
  * ``legitimacy_diagnostics.run_d6_quarantine`` (the ``--keepers`` CI gate),
  * ``audit_keepers`` (the H1 governance gate).

Stdlib-only (no imports) — consumed by the deploy/CI paths that run on a bare
``python3``.
"""

from __future__ import annotations

CALIBRATION_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})

# Repo-relative path (POSIX form). Consumers join it onto the repo root
# (``repo / MARKER_FILE``) or wrap it in a Path for ``.name`` — a plain string
# so both the message text and the join are identical across the three gates.
MARKER_FILE: str = "frontend/data/backcast/calibration-complete.json"

# Holdout SPEND FREEZE file (rule 22): while its ``active`` key is true, NO
# out-of-training year may be solved/scored/registered for ANY ISO — the
# freeze outranks both marker blocks. Value-equal to
# ``run_calibration_full.HOLDOUT_FREEZE_FILE`` (kept as a separate literal per
# this repo's existing convention; a parity test asserts they agree). This
# module stays import-free, so consumers do their own json read of the file.
FREEZE_FILE: str = "frontend/data/backcast/holdout-freeze.json"

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

# Which marker block authorizes which tier.
TIER_MARKER_BLOCK: dict[str, str] = {
    TIER_VALIDATION: "complete",
    TIER_LOCKED: "final",
}

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
    """Return the rule-22 violations in a proposed hindcast solve-year set.

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
            f"{sorted(HINDCAST_SEED_YEARS)}; rule 22)"
        )
    return out


def tier_for_year(year: int) -> str:
    """Return the rule-22 tier of ``year``.

    Fails CLOSED: a year in none of the three enumerated sets (a future year, a
    pre-2018 year nobody has laddered yet) is treated as ``locked_test``, the
    strictest tier — so an unanticipated year can never be spent on the weaker
    validation marker.

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


def split_breach_by_tier(years) -> dict[str, list[int]]:
    """Group out-of-training ``years`` by the marker tier each one needs.

    Args:
        years: Iterable of years (any mix of tiers; train years are dropped).

    Returns:
        ``{tier: sorted_years}`` for the non-train tiers actually present.
        Empty when every year is in the training window.
    """
    out: dict[str, list[int]] = {}
    for y in sorted({int(y) for y in years}):
        tier = tier_for_year(y)
        if tier == TIER_TRAIN:
            continue
        out.setdefault(tier, []).append(y)
    return out


def marker_blocks(marker_doc: dict) -> dict[str, dict]:
    """Return ``{tier: {iso: entry}}`` from a loaded marker document.

    A missing block reads as empty — an absent ``final`` block authorizes no
    locked test for anyone, which is the intended fail-closed default.

    Args:
        marker_doc: Parsed ``calibration-complete.json`` (or ``{}``).

    Returns:
        ``{TIER_VALIDATION: {...}, TIER_LOCKED: {...}}``.
    """
    doc = marker_doc or {}
    return {tier: (doc.get(block) or {}) for tier, block in TIER_MARKER_BLOCK.items()}


def authorized(marker_doc: dict, iso: str, tier: str) -> bool:
    """Return whether ``iso`` carries the marker that authorizes ``tier``.

    Args:
        marker_doc: Parsed ``calibration-complete.json`` (or ``{}``).
        iso: Model ISO id.
        tier: ``TIER_VALIDATION`` or ``TIER_LOCKED``.

    Returns:
        True iff the tier's marker block names the ISO. Always False for a tier
        with no marker block (fail closed).
    """
    return iso in marker_blocks(marker_doc).get(tier, {})
