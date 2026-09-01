"""Tests for the forecast gate-(a) provenance guard (audit board F-5).

``scripts/check_gate_a_provenance.py`` FAILS when an
``isos.<ISO>.gate.a_keeper_marker`` row cites a keeper the ISO has superseded,
or asserts a rule-22 marker state that disagrees with
``calibration-complete.json``. It exists because four of six rows were stale at
the 2026-08-31 audit pin — ERCOT's verdict-flippingly so — and no instrument
could see it: ``check_forecast_staleness.py`` reads only
``forecast-provenance/v1`` field names, which the gate-(a) block deliberately
avoids.

These tests pin both checks, the fail-closed posture on unparseable rows, and —
the boundary that matters most — that the guard reads NO determination. ERCOT's
live two-value case (ISO-level partition rollup CALIBRATED, run-level NOT-YET)
gets its own test: a guard that picked either value would be a second,
competing instrument for the program's most contested reading.
"""

import json

from scripts import check_gate_a_provenance as cgap


def _detail(keeper, complete, final, extra=""):
    return (
        f"keeper {keeper} (full-span 2023-2025, rule 16); {extra}"
        f"marker complete={complete} final={final}. "
        f"Gate (a) test is charter §2.1b(2)(a)."
    )


def _row(keeper, complete, final, status="fail", extra=""):
    return {"status": status, "detail": _detail(keeper, complete, final, extra)}


def test_matching_row_is_clean():
    """Identity and marker state both agree — nothing to report."""
    problems = cgap.check_iso(
        "PJM",
        _row("2026-08-15-pjm-162-inputclock", True, False, status="pass"),
        "2026-08-15-pjm-162-inputclock",
        (True, False),
    )
    assert problems == []


def test_superseded_keeper_fails():
    """The F-5 identity half: a row keyed to a keeper the ISO has moved past."""
    problems = cgap.check_iso(
        "MISO",
        _row("2026-08-22-miso-177-rho-measured", False, False),
        "2026-08-30-miso-191-bexit",
        (False, False),
    )
    assert len(problems) == 1
    assert "SUPERSEDED" in problems[0]
    assert "2026-08-30-miso-191-bexit" in problems[0]


def test_wrong_marker_state_fails():
    """The F-5 verdict-flipping half: ERCOT read complete=False while holding it."""
    problems = cgap.check_iso(
        "ERCOT",
        _row("2026-08-25-234-eastex-identity", False, False),
        "2026-08-25-234-eastex-identity",
        (True, False),
    )
    assert len(problems) == 1
    assert "claims marker complete=False" in problems[0]
    assert "complete=True" in problems[0]


def test_pass_status_without_the_complete_marker_fails():
    """`complete` membership is NECESSARY for gate (a) — a pass without it lies."""
    problems = cgap.check_iso(
        "CAISO",
        _row("2026-08-26-caiso-220-c1-crosswalk", False, False, status="pass"),
        "2026-08-26-caiso-220-c1-crosswalk",
        (False, False),
    )
    assert any("ABSENT from the `complete` block" in p for p in problems)


def test_fail_status_on_a_complete_iso_is_not_second_guessed():
    """`complete` is necessary, not sufficient — a fail there is not this guard's call.

    The charter also requires a full-span keeper, so deriving the pass/fail is
    the records lane's job. Checking the converse would make this a second
    verdict instrument.
    """
    problems = cgap.check_iso(
        "ERCOT",
        _row("2026-08-25-234-eastex-identity", True, False, status="fail"),
        "2026-08-25-234-eastex-identity",
        (True, False),
    )
    assert problems == []


def test_unparseable_keeper_citation_fails_closed():
    """An unverifiable row is not a verified row."""
    problems = cgap.check_iso(
        "PJM",
        {"status": "fail", "detail": "marker complete=False final=False."},
        "k",
        (False, False),
    )
    assert any("names no keeper id" in p for p in problems)


def test_unparseable_marker_claim_fails_closed():
    """Same posture on the marker half."""
    problems = cgap.check_iso(
        "PJM",
        {"status": "fail", "detail": "keeper 2026-01-01-x-y is designated."},
        "2026-01-01-x-y",
        (False, False),
    )
    assert any("states no marker claim" in p for p in problems)


def test_a_rekey_note_does_not_masquerade_as_the_citation():
    """The row's SUBJECT is the first keeper id; a `RE-KEYED from <old>` is history.

    Every repaired row carries its predecessor's id in the prose, so anchoring
    on anything but the first match would read the superseded id as current.
    """
    detail = (
        "keeper 2026-08-30-nyiso-159-loss-surface (full-span 2023-2025, rule 16; "
        "RE-KEYED here from 2026-08-30-nyiso-157-par-attribution, which it "
        "superseded); marker complete=False final=False."
    )
    problems = cgap.check_iso(
        "NYISO",
        {"status": "fail", "detail": detail},
        "2026-08-30-nyiso-159-loss-surface",
        (False, False),
    )
    assert problems == []


def test_the_guard_reads_no_determination():
    """THE BOUNDARY. Determination prose never changes the verdict.

    Determinations come from build_status.py's partition-aware rollup. The same
    row is checked three times with three different determination claims —
    including a self-contradictory one — and the guard is silent every time,
    because it never looks.
    """
    for determination in ("NOT-YET", "CALIBRATED", "CALIBRATED and NOT-YET"):
        detail = (
            f"keeper 2026-08-25-234-eastex-identity (full-span 2023-2025, rule 16); "
            f"determination {determination}; marker complete=True final=False."
        )
        problems = cgap.check_iso(
            "ERCOT",
            {"status": "pass", "detail": detail},
            "2026-08-25-234-eastex-identity",
            (True, False),
        )
        assert problems == [], determination


def test_ercot_two_value_determination_case_is_correct_by_construction():
    """ERCOT's live case: ISO-level CALIBRATED, run-level NOT-YET, both real.

    A guard that forced either to be "the" determination would be wrong here.
    This one is correct because it reads neither — the row passes on identity
    and marker state alone.
    """
    detail = (
        "keeper 2026-08-25-234-eastex-identity (full-span 2023-2025, rule 16); "
        "ISO-level determination CALIBRATED under the ercot-246 two-config "
        "partition rollup, while the registered run-level determination is "
        "NOT-YET; marker complete=True final=False."
    )
    problems = cgap.check_iso(
        "ERCOT",
        {"status": "pass", "detail": detail},
        "2026-08-25-234-eastex-identity",
        (True, False),
    )
    assert problems == []


def test_marker_membership_ignores_underscore_notes(tmp_path):
    """`final` holds only `_note` — that is what an EMPTY block looks like."""
    doc = {
        "complete": {"ERCOT": {}, "PJM": {}, "_note": "prose"},
        "final": {"_note": "no ISO has ever spent a locked-test year"},
    }
    membership = cgap.marker_membership(doc)
    assert membership == {"ERCOT": (True, False), "PJM": (True, False)}


def test_designated_keepers_skips_the_index_shard(tmp_path):
    """`index.json` is display order, not an ISO."""
    d = tmp_path / "keepers"
    d.mkdir()
    (d / "PJM.json").write_text(json.dumps({"iso": "PJM", "keeper": "k1"}))
    (d / "index.json").write_text(json.dumps({"note": "display order"}))
    assert cgap.designated_keepers(d) == {"PJM": "k1"}


def test_live_board_passes():
    """The committed board must satisfy the guard — this is the gate itself."""
    assert cgap.main([]) == 0
