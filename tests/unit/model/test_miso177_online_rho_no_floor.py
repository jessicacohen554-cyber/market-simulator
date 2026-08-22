"""miso-177 measured-value rho treatment (``miso_online_rho_no_floor``).

The seam contract for the refuted-floor treatment
(FINDING-miso177-rho-clip-floor-identification-2026-08-22.md): armed, the
MISO gated branch consumes the CAMPD-measured ``online_rho`` bounded by the
cited 4.0 ceiling alone; default, the ``RHO_CLIP``-banded value is
byte-identical to the pre-field behaviour; armed with no measured artifact,
the seam hard-errors instead of silently identifying a different coefficient.
The shared band itself is untouched at every polarity (rule 25).
"""

import numpy as np
import pytest

import market_sim.data.online_reserve_rho as orr
from market_sim.model.reserves import spec as reserves_spec


def _measured(rho: float) -> orr.OnlineReserveRho:
    return orr.OnlineReserveRho(
        iso="MISO",
        family_set="miso_reg_spin",
        mechanism="miso_reserve_online_gated",
        rho=rho,
        rho_minload=0.6863,
        rho_fullhour=0.1705,
        online_unit_hours=5_276_357,
        campd_coverage_frac=0.9307,
        years="2023-2024-2025",
    )


class TestRhoUsedNoFloorProperty:
    def test_measured_value_passes_through_unfloored(self):
        m = _measured(0.17644175978069962)
        assert m.rho_used == orr.RHO_CLIP[0]  # the banded read still floors
        assert m.rho_used_no_floor == pytest.approx(0.17644175978069962, abs=0)

    def test_cited_ceiling_still_binds(self):
        m = _measured(5.0)
        assert m.rho_used_no_floor == orr.RHO_CLIP[1]

    def test_shared_band_is_untouched(self):
        # The band ruling remains the owner's nyiso-145 decision card: the
        # treatment adds a read, never re-bands.
        assert orr.RHO_CLIP == (0.5, 4.0)


class TestIdentifiedOnlineRhoTreatment:
    _fleet = None  # the measured path never touches fleet arrays

    def test_default_is_the_banded_value(self, monkeypatch):
        monkeypatch.setattr(
            orr, "load_online_rho", lambda iso, family_set: _measured(0.1764)
        )
        got = reserves_spec._identified_online_rho(
            self._fleet, np.array([], dtype=int), iso="MISO", family_set="miso_reg_spin"
        )
        assert got == orr.RHO_CLIP[0]

    def test_armed_consumes_the_measurement_exactly(self, monkeypatch):
        monkeypatch.setattr(
            orr,
            "load_online_rho",
            lambda iso, family_set: _measured(0.17644175978069962),
        )
        got = reserves_spec._identified_online_rho(
            self._fleet,
            np.array([], dtype=int),
            iso="MISO",
            family_set="miso_reg_spin",
            measured_no_floor=True,
        )
        assert got == pytest.approx(0.17644175978069962, abs=0)

    def test_armed_without_artifact_hard_errors(self, monkeypatch):
        monkeypatch.setattr(orr, "load_online_rho", lambda iso, family_set: None)
        with pytest.raises(ValueError, match="miso_online_rho_no_floor"):
            reserves_spec._identified_online_rho(
                self._fleet,
                np.array([], dtype=int),
                iso="MISO",
                family_set="miso_reg_spin",
                measured_no_floor=True,
            )


class TestCommittedMisoArtifactWiring:
    """End-to-end on the committed artifact (skipped when not hydrated)."""

    def test_committed_miso_row_under_both_treatments(self):
        if not orr._artifact_path("MISO").exists():
            pytest.skip("MISO measured-rho artifact not hydrated in this profile")
        m = orr.load_online_rho("MISO", "miso_reg_spin")
        assert m is not None
        assert m.rho == pytest.approx(0.17644175978069962, abs=1e-15)
        assert m.rho_used == 0.5
        assert m.rho_used_no_floor == pytest.approx(0.17644175978069962, abs=1e-15)


class TestScenarioConfigSurface:
    def test_field_exists_and_defaults_off(self):
        from market_sim.config.scenarios import ScenarioConfig

        assert (
            ScenarioConfig.__dataclass_fields__["miso_online_rho_no_floor"].default
            is False
        )
