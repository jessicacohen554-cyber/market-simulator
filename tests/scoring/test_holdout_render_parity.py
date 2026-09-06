"""Tests for rule 30 [R-TOUCHPOINT-FOLD](a) as AMENDED 2026-09-06 — a folded
held-out year renders AS a year, with no special designation.

The owner instruction, verbatim: *"the formatting on the html dashboard for
holdout years shouldn't be any different than the 3 training years, it should
show the results in the report view on run explorer and does not need a special
designation."* Genealogy: ``docs/governance/rule-history.md`` §14.

WHAT THIS GUARD IS FOR. Rule 30(a) previously MANDATED the opposite — that a
folded year render as a column of a separate *Validation Touchpoints* panel —
so the amendment's failure mode is not a typo, it is a later lane reading the
pre-amendment rule (or the §12 text it superseded) and "restoring" the panel as
a regression fix. Every assertion below therefore pins a property the amendment
CREATED, so restoring the old rendering reds this file rather than passing.

WHY STATIC SOURCE ASSERTIONS. The behaviour was verified for real by rendering
all six ISO keeper pages in headless Chromium (see the rule-history section);
this file is the cheap CI-runnable residue of that, not a substitute for it. It
pins the three seams the render depends on:

  1. the Report's year set is ``selectableYears()`` (own + folded), not
     ``runYears()`` (own only) — the single line that made folded years absent
     from every report table and chart;
  2. ``selectableYears()`` sorts GLOBALLY, so NEISO reads 2020…2025 rather than
     the concatenated 2023,2024,2025,2020,2021,2022;
  3. the removed render paths are GONE, not merely unreferenced (rule 26
     [R-DELETE]: a dead render path is a re-armable answer).

AMENDED SAME DAY (owner instruction, verbatim): *"Delete the stupid per year
determination from the run explorer I do not need narrative from you in my
results viewing ANYWHERE I just want the scores and charts and make it so every
iso with holdout years run has them SHOW up in the report."* So the run
explorer's Report is SCORES AND CHARTS ONLY, and rule 22's tier caveat — which
the first amendment kept here as a footnote — moves entirely to the Calibration
Status page's per-year table, the surface rule 30(b) already owns. This file now
pins BOTH halves: the fold still folds (so every ISO's held-out years render as
ordinary year columns), and no narrative panel may come back.

Each assertion is accompanied by a negative control in
``TestGuardActuallyGuards`` that mutates the source back toward the
pre-amendment shape and asserts the corresponding check FAILS — the neiso-102
lesson (*a guard test that passes is not a guard*) applied to a guard written
the same day as the change it protects.
"""

import re
import unittest

from tests.helpers import REPO_ROOT

RUNS_JS = REPO_ROOT / "docs" / "codebase-site" / "js" / "backcast-runs.js"

# Symbols the amendment DELETED. Each one rendered a per-year designation:
# the combined/single touchpoint panels and their verdict vocabulary, the
# tier-label map behind the dropdown suffix and the panel headers, the
# "<year> is a held-out year" provenance banner, and the panel's block reader.
REMOVED_SYMBOLS = (
    "renderHoldoutPanelCombined",
    "renderHoldoutPanel",
    "HOLDOUT_VERDICT",
    "holdoutYearBanner",
    "TIER_LABEL",
    "foldedHoldoutBlocks",
    # Deleted 2026-09-06 by the same-day narrative-strip instruction. Each one
    # rendered PROSE into the results view: the run-definition panel (whose
    # registry text had become a per-year determination essay), the ablation
    # twin + market story, and the auto-generated diagnostic findings.
    "populateAblationDelta",
    "diagFindings",
    "ablationDelta",
)

# Prose the Report must never render again. Matched as literal substrings of the
# source because each is the panel's own visible heading or CSS hook.
REMOVED_PROSE = (
    "Run Definition",
    "Rule 22 — held-out years",
    "Zero-forcing ablation twin",
    "Market story",
    "bc-narration",
    "Auto-generated findings",
)

STATUS_JS = REPO_ROOT / "docs" / "codebase-site" / "js" / "calibration-status.js"


def source() -> str:
    return RUNS_JS.read_text(encoding="utf-8")


def render_report_body(src: str) -> str:
    """The body of ``renderReport`` up to the next top-level function."""
    start = src.index("function renderReport(")
    nxt = src.find("\n    function ", start + 1)
    return src[start : nxt if nxt != -1 else len(src)]


def selectable_years_body(src: str) -> str:
    start = src.index("function selectableYears(")
    nxt = src.find("\n    function ", start + 1)
    return src[start : nxt if nxt != -1 else len(src)]


# --- the checks, factored so the negative controls can run them on mutated text


def check_report_uses_selectable_years(src: str) -> bool:
    body = render_report_body(src)
    return bool(re.search(r"const\s+years\s*=\s*selectableYears\(\)", body))


def check_report_does_not_use_run_years(src: str) -> bool:
    body = render_report_body(src)
    return not re.search(r"const\s+years\s*=\s*runYears\(\)", body)


def check_selectable_years_sorted(src: str) -> bool:
    return ".sort(" in selectable_years_body(src)


def check_removed_symbols_absent(src: str) -> list[str]:
    return [s for s in REMOVED_SYMBOLS if re.search(rf"\b{s}\b", src)]


def check_removed_prose_absent(src: str) -> list[str]:
    return [t for t in REMOVED_PROSE if t in src]


def check_rule22_tier_reading_on_status_page(src: str) -> bool:
    """Rule 22's reading must live SOMEWHERE — it is the status page's job now.

    The run explorer no longer marks a held-out year at all (owner instruction
    2026-09-06), so the only thing standing between a validation number and
    being quoted as a certified out-of-sample skill number is the Calibration
    Status page's per-year table: a Tier column plus the line that says a
    held-out row is reported, not gating. That is rule 30(b)'s surface and it is
    what this check pins.
    """
    return "Held-out years are reported, not gating" in src and "Tier" in src


class TestHoldoutRendersAsAnOrdinaryYear(unittest.TestCase):
    def setUp(self):
        self.src = source()

    def test_report_year_set_includes_folded_holdout_years(self):
        """The Report covers what the year selector offers — own AND folded."""
        self.assertTrue(
            check_report_uses_selectable_years(self.src),
            "renderReport must build its year set from selectableYears() so a "
            "folded held-out year is an ordinary year column (rule 30(a) as "
            "amended 2026-09-06).",
        )

    def test_report_does_not_narrow_to_the_runs_own_years(self):
        """``runYears()`` here is exactly the pre-amendment defect."""
        self.assertTrue(
            check_report_does_not_use_run_years(self.src),
            "renderReport must NOT use runYears(): that omits every folded "
            "held-out year from the report's tables and charts.",
        )

    def test_selectable_years_is_globally_sorted(self):
        """Concatenating own+held is ascending only by accident."""
        self.assertTrue(
            check_selectable_years_sorted(self.src),
            "selectableYears() must sort globally — otherwise NEISO reads "
            "2023,2024,2025,2020,2021,2022 in both the dropdown and the report.",
        )

    def test_designation_render_paths_are_deleted_not_orphaned(self):
        """Rule 26 [R-DELETE]: a dead render path is a re-armable answer."""
        still = check_removed_symbols_absent(self.src)
        self.assertEqual(
            still,
            [],
            f"pre-amendment designation render path(s) present again: {still}. "
            "Rule 30(a) was amended 2026-09-06 — do not restore the Validation "
            "Touchpoints panel, the year-selector tier suffix, or the held-out "
            "banner (rule-history §14).",
        )

    def test_report_renders_no_narrative_prose(self):
        """Scores and charts only — owner instruction 2026-09-06."""
        still = check_removed_prose_absent(self.src)
        self.assertEqual(
            still,
            [],
            f"narrative panel(s) present again in the run explorer: {still}. "
            "The Report is scores and charts only; the run definition, the "
            "rule-22 footnote, the ablation twin / market story and the "
            "auto-generated diagnostics were DELETED, not hidden.",
        )

    def test_rule22_tier_reading_lives_on_the_status_page(self):
        """Rule 22's substance survives the strip — on rule 30(b)'s surface."""
        self.assertTrue(
            check_rule22_tier_reading_on_status_page(
                STATUS_JS.read_text(encoding="utf-8")
            ),
            "The Calibration Status page must keep its per-year Tier column and "
            "the 'reported, not gating' line: with the run explorer stripped of "
            "every designation, it is the only surface that stops a validation "
            "number being read as a certified out-of-sample skill number "
            "(rule 22, rule 30(b)).",
        )

    def test_the_fold_plumbing_itself_is_untouched(self):
        """The amendment changed RENDERING only — the fold still folds."""
        for sym in ("foldTargetOf", "holdoutCompanions", "ensureHoldoutYear"):
            self.assertRegex(
                self.src,
                rf"function\s+{sym}\b",
                f"{sym} is the rule-30 fold plumbing and must survive the "
                "presentation amendment (the stamp, the run-list hiding and "
                "the deep-link redirect all depend on it).",
            )


class TestGuardActuallyGuards(unittest.TestCase):
    """Negative controls: mutate the source back toward the pre-amendment
    rendering and assert each check FAILS. Without these, every assertion above
    could be passing for a reason unrelated to what it claims to protect."""

    def setUp(self):
        self.src = source()

    def test_report_check_fails_when_narrowed_to_run_years(self):
        """Mutate renderReport's OWN year line back to runYears().

        Spliced through render_report_body rather than str.replace: the string
        ``const years = selectableYears();`` appears TWICE in the file (the run
        loader at ~line 972 sets it too), so a bare replace(..., 1) silently
        mutates the loader and leaves renderReport untouched — a negative
        control that proves nothing. This assertion caught exactly that in its
        own first draft.
        """
        body = render_report_body(self.src)
        mutated_body = body.replace(
            "const years = selectableYears();", "const years = runYears();", 1
        )
        self.assertNotEqual(mutated_body, body, "mutation did not apply")
        mutated = self.src.replace(body, mutated_body, 1)
        self.assertFalse(check_report_uses_selectable_years(mutated))
        self.assertFalse(check_report_does_not_use_run_years(mutated))

    def test_sort_check_fails_on_a_bare_concatenation(self):
        body = selectable_years_body(self.src)
        mutated = self.src.replace(
            body,
            "function selectableYears() { return [...runYears(), "
            "...holdoutYears()]; }\n",
            1,
        )
        self.assertNotEqual(mutated, self.src, "mutation did not apply")
        self.assertFalse(check_selectable_years_sorted(mutated))

    def test_removed_symbol_check_fires_on_a_restored_panel(self):
        mutated = (
            self.src + "\n    function renderHoldoutPanelCombined(b) { return ''; }\n"
        )
        self.assertEqual(
            check_removed_symbols_absent(mutated), ["renderHoldoutPanelCombined"]
        )

    def test_prose_check_fires_on_a_restored_narrative_panel(self):
        mutated = self.src + '\n      html += `<h2>Run Definition</h2>`;\n'
        self.assertEqual(check_removed_prose_absent(mutated), ["Run Definition"])

    def test_status_tier_check_fires_when_the_reading_is_dropped(self):
        src = STATUS_JS.read_text(encoding="utf-8")
        mutated = src.replace("Held-out years are reported, not gating", "", 1)
        self.assertNotEqual(mutated, src, "mutation did not apply")
        self.assertFalse(check_rule22_tier_reading_on_status_page(mutated))


if __name__ == "__main__":
    unittest.main()
