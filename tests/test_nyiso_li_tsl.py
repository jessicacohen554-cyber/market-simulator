"""Tests for the NYISO Zone-K LCR/TSL import-cap mechanism (issue #1345).

``apply_nyiso_li_tsl_import_cap`` replaces the Long_Island 0.45 self-supply
energy floor (``config.nyiso_li_lcr_tsl``): the NYC->Long_Island link is
capped at the published locality import limit
(``data/raw/capacity-deliverability/nyiso/nyiso.csv``) inside the HB14-21
design-condition window and keeps its physical rating elsewhere; the floor
injection skips Long_Island via ``exclude_zones`` so the two mechanisms never
stack (rule 19).
"""

import numpy as np
import pytest


from market_sim.config.constants import NYISO_LOCAL_SELFSUPPLY_FRAC
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.model.transmission import (
    NYISO_SELFSUPPLY_FLOOR_HOURS,
    apply_nyiso_li_tsl_import_cap,
    inject_nyiso_local_selfsupply,
)

T = 48  # two days — covers the window twice


@pytest.fixture(autouse=True, scope="module")
def _clean_capdel(tmp_path_factory):
    """Curate the real committed NYISO capacity-deliverability raw CSV into a
    tmp CLEAN_DIR so the published import-limit read works without touching
    the repo's (disposable, gitignored) clean tree."""
    from scripts import curate_capacity_deliverability as curate_cd
    from scripts.lib import clean_io

    tmp = tmp_path_factory.mktemp("capdel_clean")
    orig = clean_io.paths.CLEAN_DIR
    clean_io.paths.CLEAN_DIR = tmp
    try:
        curate_cd.curate(isos=["NYISO"])
        yield
    finally:
        clean_io.paths.CLEAN_DIR = orig


def _nyiso_cfg():
    return get_iso_config("NYISO")


def _li_link_idx(iso_config) -> int:
    return next(
        i
        for i, ln in enumerate(iso_config.links)
        if (ln.from_zone, ln.to_zone) == ("NYC", "Long_Island")
    )


class TestTslImportCap:
    def test_in_window_capped_at_published_limit(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        out = apply_nyiso_li_tsl_import_cap(ttc, iso_config, "NYISO", 2023, T)
        assert out.shape == (T, len(iso_config.links))
        li = _li_link_idx(iso_config)
        hod = np.arange(T) % 24
        in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
        # 2023 -> capability year 2023/2024 -> published LI import limit 325 MW.
        np.testing.assert_allclose(out[in_window, li], 325.0)
        # Off-window hours keep the physical rating.
        np.testing.assert_allclose(out[~in_window, li], iso_config.links[li].ttc_mw)

    def test_capability_year_rows_resolve(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        li = _li_link_idx(iso_config)
        on = NYISO_SELFSUPPLY_FLOOR_HOURS[0]
        # 2024/25 and 2025/26 both publish 275 MW.
        for year in (2024, 2025):
            out = apply_nyiso_li_tsl_import_cap(ttc, iso_config, "NYISO", year, T)
            assert out[on, li] == pytest.approx(275.0)

    def test_other_links_untouched(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        out = apply_nyiso_li_tsl_import_cap(ttc, iso_config, "NYISO", 2023, T)
        li = _li_link_idx(iso_config)
        for i in range(len(iso_config.links)):
            if i == li:
                continue
            np.testing.assert_allclose(out[:, i], ttc[i])

    def test_respects_tighter_existing_hourly_limit(self):
        """A pre-existing per-hour limit below the TSL is not loosened."""
        iso_config = _nyiso_cfg()
        n = len(iso_config.links)
        li = _li_link_idx(iso_config)
        ttc_t = np.full((T, n), 999999.0)
        ttc_t[:, li] = 100.0  # tighter than the 325 MW TSL
        out = apply_nyiso_li_tsl_import_cap(ttc_t, iso_config, "NYISO", 2023, T)
        np.testing.assert_allclose(out[:, li], 100.0)

    def test_non_nyiso_unchanged(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        out = apply_nyiso_li_tsl_import_cap(ttc, iso_config, "ERCOT", 2023, T)
        assert out is ttc


class TestFloorExclusion:
    def _fa(self):
        return FleetArrays(
            pmax=np.array([500.0, 300.0, 200.0]),
            pmin=np.zeros(3),
            heat_rate=np.array([7.0, 10.0, 12.0]),
            vom=np.zeros(3),
            emission_rate=np.zeros(3),
            nox_rate=np.zeros(3),
            so2_rate=np.zeros(3),
            zone_idx=np.array([0, 1, 1]),  # NYC=0, Long_Island=1
            fuel_type_idx=np.array(
                [
                    FUEL_TYPE_MAP["gas_cc"],
                    FUEL_TYPE_MAP["gas_st"],
                    FUEL_TYPE_MAP["gas_ct"],
                ]
            ),
            availability=np.ones((3, T)),
            unit_ids=["NYC_cc", "LI_st", "LI_ct"],
            efficiency_bin=np.zeros(3, dtype=int),
            plant_code=np.zeros(3, dtype=int),
        )

    def test_exclude_zones_skips_li_floor(self):
        fa = self._fa()
        demand = np.zeros((2, T))
        demand[1, :] = 400.0
        applied = inject_nyiso_local_selfsupply(
            fa,
            "NYISO",
            demand,
            ["NYC", "Long_Island"],
            exclude_zones=frozenset({"Long_Island"}),
        )
        # Long_Island is the only configured pocket, so nothing is applied and
        # no min_gen floor exists — the TSL cap owns LI this run.
        assert not applied
        assert fa.min_gen is None

    def test_default_exclusion_is_byte_identical(self):
        fa_a, fa_b = self._fa(), self._fa()
        demand = np.zeros((2, T))
        demand[1, :] = 400.0
        a = inject_nyiso_local_selfsupply(fa_a, "NYISO", demand, ["NYC", "Long_Island"])
        b = inject_nyiso_local_selfsupply(
            fa_b, "NYISO", demand, ["NYC", "Long_Island"], exclude_zones=frozenset()
        )
        assert a and b
        np.testing.assert_array_equal(fa_a.min_gen, fa_b.min_gen)
        frac = NYISO_LOCAL_SELFSUPPLY_FRAC["Long_Island"]
        on = NYISO_SELFSUPPLY_FLOOR_HOURS[0]
        assert fa_a.min_gen[1, on] + fa_a.min_gen[2, on] == pytest.approx(frac * 400.0)
