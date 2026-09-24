"""Tests for audit_keepers E13 — keeper-only retention of an ISO's REGISTERED SET.

Rule 35 ``[R-PROMOTE]`` (f). The rule exists because the duty it enforces was
real but unowned: rule 15 ``[R-DASHBOARD]`` has required keeper-only retention
since 2026-09-05, and defers the sweep to "the next registration". Nobody owned
"next time". Measured 2026-09-12, before the clean-out: **47 registered runs
against 7 designated keepers**, 33 of them superseded — and ``audit_keepers``
PASSED, because no check looked at the ISO's registered *set*. E1 looks at the
keeper's own three stores; E12 looks at the shard's live run-id pointers; a
superseded run sitting beside the keeper is invisible to both.

WHAT THIS GUARD PINS, and why each half matters:

* an unstamped non-keeper run FAILS — the plain "promotion did not prune" case;
* a run whose ``holdout.keeper`` stamp names a SINCE-SUPERSEDED keeper FAILS
  too. A dangling stamp is treated as unstamped deliberately, because rule 30
  ``[R-TOUCHPOINT-FOLD]`` (a) already renders one that way: the fold drops it,
  so the year silently leaves the ISO's report. Passing it here would let the
  exact silent loss rule 35 (c) forbids survive the audit;
* a run stamped to the LIVE keeper PASSES — that is a folded rung the keeper
  needs (rule 30 (a)), not litter, and pruning it is what would break the ISO;
* the check never reaches another ISO's rows. Keeper lanes are strictly per-ISO
  (``keepers/README.md``), so a check that swept across ISOs would red every
  lane for its neighbour's state;
* the returned YEAR SET is the union over keeper-owned runs. Rule 35 (b)/(c)
  turn on that number — a promotion must not shrink it, and (b) requires it
  read BEFORE the prune destroys the evidence — so it is asserted, not incidental.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_keepers import orphan_run_findings

KEEPER = "2026-09-12-nyiso229-hourgrain-span"
FORMER = "2026-09-09-nyiso-221-fuelvintage-span"


def _write(
    registry: Path, run_id: str, iso: str, years: list[int], stamp: str | None = None
) -> None:
    """Write one registry sidecar with the fields E13 reads."""
    rec: dict = {"id": run_id, "iso": iso, "years": years}
    if stamp:
        rec["holdout"] = {"keeper": stamp}
    (registry / f"{run_id}.json").write_text(json.dumps(rec))


def test_keeper_and_folded_rung_are_owned(tmp_path: Path) -> None:
    """The keeper plus a run stamped to it is a CLEAN set, and carries both years."""
    _write(tmp_path, KEEPER, "NYISO", [2023, 2024, 2025])
    _write(tmp_path, "tp2022", "NYISO", [2022], stamp=KEEPER)

    findings, years = orphan_run_findings("NYISO", KEEPER, tmp_path)

    assert findings == []
    assert years == [2022, 2023, 2024, 2025]


def test_superseded_keeper_left_registered_fails(tmp_path: Path) -> None:
    """The plain unswept-promotion case: a former keeper still on the site."""
    _write(tmp_path, KEEPER, "NYISO", [2023, 2024, 2025])
    _write(tmp_path, FORMER, "NYISO", [2023, 2024, 2025])

    findings, years = orphan_run_findings("NYISO", KEEPER, tmp_path)

    assert len(findings) == 1
    assert FORMER in findings[0]
    assert "prune_iso_runs.py --iso NYISO" in findings[0]
    # the orphan's years never enter the keeper's set
    assert years == [2023, 2024, 2025]


def test_stamp_to_superseded_keeper_is_treated_as_unstamped(tmp_path: Path) -> None:
    """A DANGLING holdout stamp fails — rule 30(a) already renders it as unstamped.

    This is the half that keeps rule 35(c)'s silent-loss case out: the fold drops
    such a run, so its year leaves the ISO's report with nothing complaining.
    """
    _write(tmp_path, KEEPER, "NYISO", [2023, 2024, 2025])
    _write(tmp_path, "old-tp2022", "NYISO", [2022], stamp=FORMER)

    findings, years = orphan_run_findings("NYISO", KEEPER, tmp_path)

    assert len(findings) == 1
    assert "old-tp2022" in findings[0]
    assert FORMER in findings[0], "the finding names the stale keeper it points at"
    assert 2022 not in years, "a dangling rung's year is NOT credited to the keeper"


def test_other_isos_are_never_swept(tmp_path: Path) -> None:
    """Per-ISO scope: another ISO's rows are neither failed nor counted."""
    _write(tmp_path, KEEPER, "NYISO", [2023, 2024, 2025])
    _write(tmp_path, "pjm-keeper", "PJM", [2020, 2021])
    _write(tmp_path, "miso-orphan", "MISO", [2019])

    findings, years = orphan_run_findings("NYISO", KEEPER, tmp_path)

    assert findings == []
    assert years == [2023, 2024, 2025]
    assert 2019 not in years and 2020 not in years


def test_iso_match_is_case_insensitive(tmp_path: Path) -> None:
    """A sidecar written with a lowercase iso is still this ISO's row."""
    _write(tmp_path, KEEPER, "nyiso", [2023, 2024, 2025])
    _write(tmp_path, "stray", "NYISO", [2022])

    findings, years = orphan_run_findings("NYISO", KEEPER, tmp_path)

    assert len(findings) == 1 and "stray" in findings[0]
    assert years == [2023, 2024, 2025], "the lowercase keeper row was still read"


def test_empty_registry_is_clean(tmp_path: Path) -> None:
    """No rows is not a failure — it is an ISO with nothing registered."""
    assert orphan_run_findings("NYISO", KEEPER, tmp_path) == ([], [])
