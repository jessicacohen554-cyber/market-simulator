"""miso-177: the MISO measured online_rho consumed floorless (owner ruling).

Pins the post-ruling seam semantics the MISO re-gate keeper
`2026-08-22-miso-177-rho-measured` solves on: `RHO_CLIP = (0.0, 4.0)` (owner
ruling 2026-08-22, nyiso-145 decision-card option A) passes the measured
statistic through at its measured value — for MISO byte-exactly
0.17644175978069962 (`campd_online_reserve_rho_MISO.csv`) — with the cited
4.0 ceiling intact. Identification record:
`FINDING-miso177-rho-clip-floor-identification-2026-08-22.md`.
"""

import pytest

import market_sim.data.online_reserve_rho as orr

MISO_MEASURED_RHO = 0.17644175978069962


class TestPostRulingBand:
    def test_floor_is_deleted_ceiling_stays(self):
        assert orr.RHO_CLIP == (0.0, 4.0)

    def test_measured_value_passes_through(self):
        m = orr.OnlineReserveRho(
            iso="MISO",
            family_set="miso_reg_spin",
            mechanism="miso_reserve_online_gated",
            rho=MISO_MEASURED_RHO,
            rho_minload=0.6863,
            rho_fullhour=0.1705,
            online_unit_hours=5_276_357,
            campd_coverage_frac=0.9307,
            years="2023-2024-2025",
        )
        assert m.rho_used == pytest.approx(MISO_MEASURED_RHO, abs=0)

    def test_cited_ceiling_still_binds(self):
        m = orr.OnlineReserveRho(
            iso="X",
            family_set="f",
            mechanism="m",
            rho=5.0,
            rho_minload=1.0,
            rho_fullhour=1.0,
            online_unit_hours=1,
            campd_coverage_frac=1.0,
            years="2023",
        )
        assert m.rho_used == orr.RHO_CLIP[1]


class TestCommittedMisoArtifactWiring:
    """End-to-end on the committed artifact (skipped when not hydrated)."""

    def test_miso_keeper_coefficient(self):
        if not orr._artifact_path("MISO").exists():
            pytest.skip("MISO measured-rho artifact not hydrated in this profile")
        m = orr.load_online_rho("MISO", "miso_reg_spin")
        assert m is not None
        assert m.rho == pytest.approx(MISO_MEASURED_RHO, abs=1e-15)
        assert m.rho_used == pytest.approx(MISO_MEASURED_RHO, abs=1e-15)
