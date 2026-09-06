"""R-AZ: the rule-22 tier marker is re-checked at REGISTRATION, not only at launch.

Owner ruling R-AZ (audit-program director sitting 2026-09-06, card "Marker
gate": *"Re-check at registration"*). The launch-time gate
(``run_calibration_full.enforce_holdout_year_gate``, pinned by
``tests/scoring/test_holdout_year_gate.py``) reads the marker once, when the LP
starts — so a multi-hour solve can outlive the authorization it launched under.
Z-6 is the case
(``docs/handoffs/holdout-2022-completeness-ercot-nyiso-2026-09-05.md`` §1a): a
NYISO 2022 validation-tier solve launched under the D56-R ``complete`` marker,
``main`` withdrew that marker (nyiso-193) while the LP ran, and only the lane's
own discipline kept the run un-registered at merge.

These tests pin the second check at the seam where a run's solve years become a
committed sidecar (``dashboard_add_run.enforce_registration_marker_gate``) and
the policy it delegates to
(``holdout_policy.registration_refusals``). Hermetic: every marker/freeze
document is written into ``tmp_path``, never the committed one — except the
final class, which REPLAYS the committed holdout-year sidecars read-only.
"""

import json
import sys
from pathlib import Path

import pytest
from scripts import calibration_verdict as cv
from scripts import dashboard_add_run as dar
from scripts.lib import holdout_policy as hp
from tests.helpers import REPO_ROOT

# Minimal synthetic verdict, so main()'s post-registration scorer call runs
# against no committed artifacts (same stub the ercot-193 sidecar test uses).
STUB_VERDICT = {
    "run_id": "2099-01-01-tb2",
    "iso": "NYISO",
    "label": "tb2",
    "target_years": [2022],
    "scorable_years": [2022],
    "data_blocked_years": [],
    "rubric_version": 1,
    "determination": "NOT-YET",
    "reasons": [],
    "notes": [],
    "criteria": {},
    "caveats": [],
    "grade_summary": None,
    "free_class_score": None,
}

# The committed freeze's current shape: locked test frozen, validation lifted
# (2026-08-26 owner ruling, program-director sitting card 6).
FREEZE_LOCKED_ONLY = {"active": True, "scope": {"tiers": ["locked_test"]}}
NO_FREEZE: dict = {}


def _repo(
    tmp_path: Path,
    *,
    complete: dict | None = None,
    final: dict | None = None,
    freeze: dict | None = None,
) -> Path:
    """Build a tmp repo root carrying only the two policy documents."""
    root = tmp_path / "repo"
    (root / "frontend" / "data" / "backcast").mkdir(parents=True, exist_ok=True)
    (root / hp.MARKER_FILE).write_text(
        json.dumps({"complete": complete or {}, "final": final or {}})
    )
    if freeze is not None:
        (root / hp.FREEZE_FILE).write_text(json.dumps(freeze))
    return root


class TestRegistrationRefusalsPolicy:
    """The policy function itself — no filesystem, no CLI."""

    def test_in_sample_years_never_refuse(self):
        """2023-2025 registration is untouched, marker file or not."""
        for years in ([2023, 2024, 2025], [2024], [2023, 2025]):
            assert hp.registration_refusals(years, "NYISO", {}, {}) == []
            assert (
                hp.registration_refusals(years, "NYISO", {}, FREEZE_LOCKED_ONLY) == []
            )

    def test_validation_year_passes_for_a_complete_iso(self):
        marker = {"complete": {"NEISO": {"declared": "2026-08-06"}}}
        assert (
            hp.registration_refusals([2022], "NEISO", marker, FREEZE_LOCKED_ONLY) == []
        )

    def test_validation_year_refused_when_marker_withdrawn(self):
        """The Z-6 shape: the ISO is absent from `complete` at registration."""
        marker = {"complete": {"NEISO": {}}, "withdrawn": {"NYISO": {}}}
        refusals = hp.registration_refusals([2022], "NYISO", marker, FREEZE_LOCKED_ONLY)
        assert len(refusals) == 1
        msg = refusals[0]
        assert "NYISO" in msg and "2022" in msg
        assert "validation-tier" in msg
        assert "'complete'" in msg
        assert "REGISTRATION" in msg

    def test_locked_test_refused_for_every_iso_while_frozen(self):
        """The freeze outranks the marker — even a `final` ISO is refused."""
        for iso, marker in (
            ("NEISO", {"final": {"NEISO": {}}}),
            ("ERCOT", {"complete": {"ERCOT": {}}}),
            ("CAISO", {}),
        ):
            for year in (2019, 2026):
                refusals = hp.registration_refusals(
                    [year], iso, marker, FREEZE_LOCKED_ONLY
                )
                assert len(refusals) == 1, (iso, year)
                assert "locked_test-tier" in refusals[0]
                assert "FREEZE" in refusals[0]

    def test_unenumerated_year_fails_closed_to_locked_test(self):
        """2018 / 2027 are in no tier set — the strictest tier governs."""
        for year in (2018, 2027):
            refusals = hp.registration_refusals(
                [year], "ERCOT", {"complete": {"ERCOT": {}}}, FREEZE_LOCKED_ONLY
            )
            assert len(refusals) == 1, year
            assert "locked_test-tier" in refusals[0]

    def test_active_freeze_without_scope_covers_validation_too(self):
        """Fail-closed: an unparseable scope on an ACTIVE freeze freezes all."""
        marker = {"complete": {"ERCOT": {}}}
        for freeze in ({"active": True}, {"active": True, "scope": {"tiers": []}}):
            refusals = hp.registration_refusals([2022], "ERCOT", marker, freeze)
            assert len(refusals) == 1
            assert "FREEZE" in refusals[0]

    def test_mixed_span_names_every_unmet_tier(self):
        """A run spanning both holdout tiers is refused on both, in-sample aside."""
        refusals = hp.registration_refusals(
            [2019, 2022, 2023], "CAISO", {}, FREEZE_LOCKED_ONLY
        )
        assert len(refusals) == 2
        tiers = " ".join(refusals)
        assert "validation-tier" in tiers and "locked_test-tier" in tiers
        assert "2023" not in tiers

    def test_no_documents_at_all_refuses_every_holdout_year(self):
        assert hp.registration_refusals([2022], "MISO", {}, {}) != []
        assert hp.registration_refusals([2019], "MISO", {}, {}) != []


class TestEnforceRegistrationMarkerGate:
    """The dashboard_add_run seam, reading both documents off disk."""

    def test_complete_iso_registering_2022_passes(self, tmp_path):
        root = _repo(
            tmp_path, complete={"NEISO": {"declared": "x"}}, freeze=FREEZE_LOCKED_ONLY
        )
        dar.enforce_registration_marker_gate("NEISO", [2022], root)

    def test_same_iso_with_the_marker_withdrawn_is_refused(self, tmp_path):
        """Identical run, marker gone — this is the whole point of R-AZ."""
        root = _repo(tmp_path, complete={}, freeze=FREEZE_LOCKED_ONLY)
        with pytest.raises(SystemExit) as exc:
            dar.enforce_registration_marker_gate("NEISO", [2022], root)
        msg = str(exc.value)
        assert "REGISTRATION REFUSED" in msg
        assert "R-AZ" in msg and "rule 22" in msg
        assert "NEISO" in msg and "2022" in msg and "validation-tier" in msg
        assert "no bypass flag" in msg

    def test_locked_test_year_refused_for_every_iso_under_the_freeze(self, tmp_path):
        root = _repo(
            tmp_path,
            complete={"ERCOT": {}, "NEISO": {}, "PJM": {}},
            final={"NEISO": {}},
            freeze=FREEZE_LOCKED_ONLY,
        )
        for iso in ("ERCOT", "NEISO", "PJM", "CAISO", "MISO", "NYISO"):
            with pytest.raises(SystemExit, match="locked_test-tier"):
                dar.enforce_registration_marker_gate(iso, [2019], root)

    def test_in_sample_registration_untouched(self, tmp_path):
        """No marker file, no freeze file, 2023-2025: nothing to check."""
        root = tmp_path / "bare"
        root.mkdir()
        dar.enforce_registration_marker_gate("MISO", [2023, 2024, 2025], root)
        dar.enforce_registration_marker_gate("MISO", [], root)

    def test_missing_marker_file_fails_closed(self, tmp_path):
        """An absent calibration-complete.json authorizes nothing."""
        root = tmp_path / "bare2"
        root.mkdir()
        with pytest.raises(SystemExit, match="validation-tier"):
            dar.enforce_registration_marker_gate("PJM", [2022], root)

    def test_repo_defaults_to_the_module_root(self, tmp_path, monkeypatch):
        """Called with no repo, it reads dar.REPO at call time (not import)."""
        root = _repo(tmp_path, complete={}, freeze=FREEZE_LOCKED_ONLY)
        monkeypatch.setattr(dar, "REPO", root)
        with pytest.raises(SystemExit, match="validation-tier"):
            dar.enforce_registration_marker_gate("NYISO", [2022])


class TestMainRefusesBeforeWritingAnything:
    """A refused registration must leave no sidecar, payload or bench part."""

    def _wire(self, tmp_path, monkeypatch, *, complete, years):
        fake_repo = _repo(tmp_path, complete=complete, freeze=FREEZE_LOCKED_ONLY)
        bundle = fake_repo / "results" / "calibration" / "tb2"
        bundle.mkdir(parents=True)
        (bundle / "meta.json").write_text(
            json.dumps({"iso": "NYISO", "years": years}) + "\n"
        )
        registry = fake_repo / "frontend" / "data" / "backcast" / "registry"
        monkeypatch.setattr(dar, "REPO", fake_repo)
        monkeypatch.setattr(dar, "REGISTRY_DIR", registry)
        monkeypatch.setattr(dar, "CALIB_ROOT", fake_repo / "results" / "calibration")
        entry = {
            "id": "2099-01-01-tb2",
            "iso": "NYISO",
            "label": "tb2",
            "years": years,
            "file": "frontend/data/backcast/runs/2099-01-01-tb2.js",
        }
        monkeypatch.setattr(dar.rb, "manifest_entry", lambda label, b: dict(entry))
        generated: list = []
        monkeypatch.setattr(
            dar.rb, "generate", lambda runs, years=None: generated.append(runs)
        )
        monkeypatch.setattr(cv, "determine", lambda rid: dict(STUB_VERDICT))
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "dashboard_add_run.py",
                "--label",
                "tb2",
                "--bundle",
                "results/calibration/tb2",
                "--no-prune",
            ],
        )
        return fake_repo, registry, generated

    def test_withdrawn_marker_blocks_the_whole_registration(
        self, tmp_path, monkeypatch
    ):
        fake_repo, registry, generated = self._wire(
            tmp_path, monkeypatch, complete={}, years=[2022]
        )
        with pytest.raises(SystemExit, match="REGISTRATION REFUSED"):
            dar.main()
        assert not (registry / "2099-01-01-tb2.json").exists()
        assert not (fake_repo / "frontend/data/backcast/runs").exists()
        assert generated == [], "the payload renderer must never be reached"

    def test_marker_present_registers_the_same_2022_run(self, tmp_path, monkeypatch):
        fake_repo, registry, generated = self._wire(
            tmp_path, monkeypatch, complete={"NYISO": {"declared": "x"}}, years=[2022]
        )
        dar.main()
        assert (registry / "2099-01-01-tb2.json").exists()
        assert generated, "the payload renderer runs once the gate passes"


class TestCommittedHoldoutSidecarsStillValid:
    """Every holdout-year run at HEAD must pass the new check when replayed."""

    def test_all_committed_out_of_window_sidecars_pass(self):
        marker = json.loads((REPO_ROOT / hp.MARKER_FILE).read_text())
        freeze = json.loads((REPO_ROOT / hp.FREEZE_FILE).read_text())
        checked = []
        for path in sorted(
            (REPO_ROOT / "frontend/data/backcast/registry").glob("*.json")
        ):
            rec = json.loads(path.read_text())
            years = [int(y) for y in (rec.get("years") or [])]
            if set(years) <= hp.CALIBRATION_YEARS:
                continue
            iso = rec["iso"]
            refusals = hp.registration_refusals(years, iso, marker, freeze)
            assert refusals == [], f"{path.name}: {refusals}"
            checked.append((path.stem, iso, sorted(years)))
        # The FOUR rule-32 validation touchpoints on main at 2026-09-06. A new
        # holdout run adds a row here; a row VANISHING means a registered
        # holdout bundle was pruned or its years changed.
        #
        # WAS 5 until 2026-09-06 (session ercot-251). ERCOT had registered BOTH
        # halves of its two-config keeper on 2022 (run249 forward, run250
        # carve-out), so one held-out year was claimed twice on one keeper. The
        # owner ruled -- verbatim: "Register and fold the better performing one
        # into the keeper there's no reason to keep 2 configs" -- and run249 was
        # pruned from all three stores, leaving run250 folded into
        # 2026-09-05-ercot248-two-config-keeper. This tripwire fired exactly as
        # designed and the drop is the RECORDED decision, not a silent loss:
        # frontend/data/backcast/calibration-complete.json
        # (complete.ERCOT.config_2022_designation, which the same ruling
        # superseded), docs/calibration-log/ercot.md (ercot-251) and
        # docs/FINDING-ercot249-250-2022-touchpoint-2026-09-05.md Addendum 1
        # carry the pruned arm's numbers; git history carries its bytes.
        assert len(checked) >= 4, checked
        assert {iso for _, iso, _ in checked} <= {"ERCOT", "NEISO", "PJM"}, (
            "every registered holdout run must belong to a `complete` ISO"
        )
        assert all(
            hp.tier_for_year(y) == hp.TIER_VALIDATION
            for _, _, years in checked
            for y in years
        ), "no locked-test year has ever been registered (rule 22)"
