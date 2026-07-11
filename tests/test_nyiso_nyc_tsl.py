"""Tests for the NYISO Zone-J (NYC) LCR/TSL import-cap mechanism (nyiso-61).

``apply_nyiso_nyc_tsl_import_cap`` (``config.nyiso_nyc_lcr_tsl``) replaces the
Lower_Hudson->NYC (Dunwoodie-South) link's 3,900 MW energy-TTC estimate with the
published NYC-locality import limit
(``data/raw/capacity-deliverability/nyiso/nyiso.csv``: 2,875 MW every capability
year) inside the HB14-21 design-condition window, keeping the physical rating
elsewhere. The Zone-J analog of the Zone-K cap (test_nyiso_li_tsl.py); it is a
transmission limit, not a min_gen floor, so there is no floor-exclusion pairing.
"""

import numpy as np
import pytest


from market_sim.config.iso_configs import get_iso_config
from market_sim.model.transmission import (
    NYISO_SELFSUPPLY_FLOOR_HOURS,
    apply_nyiso_nyc_tsl_import_cap,
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


def _nyc_link_idx(iso_config) -> int:
    return next(
        i
        for i, ln in enumerate(iso_config.links)
        if (ln.from_zone, ln.to_zone) == ("Lower_Hudson", "NYC")
    )


class TestNycTslImportCap:
    def test_in_window_capped_at_published_limit(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        out = apply_nyiso_nyc_tsl_import_cap(ttc, iso_config, "NYISO", 2023, T)
        assert out.shape == (T, len(iso_config.links))
        nyc = _nyc_link_idx(iso_config)
        hod = np.arange(T) % 24
        in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
        # 2023 -> capability year 2023/2024 -> published NYC import limit 2,875 MW.
        np.testing.assert_allclose(out[in_window, nyc], 2875.0)
        # Off-window hours keep the physical 3,900 MW rating.
        np.testing.assert_allclose(out[~in_window, nyc], iso_config.links[nyc].ttc_mw)

    def test_capability_year_rows_resolve(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        nyc = _nyc_link_idx(iso_config)
        on = NYISO_SELFSUPPLY_FLOOR_HOURS[0]
        # Every capability year publishes 2,875 MW for NYC.
        for year in (2023, 2024, 2025):
            out = apply_nyiso_nyc_tsl_import_cap(ttc, iso_config, "NYISO", year, T)
            assert out[on, nyc] == pytest.approx(2875.0)

    def test_other_links_untouched(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        out = apply_nyiso_nyc_tsl_import_cap(ttc, iso_config, "NYISO", 2023, T)
        nyc = _nyc_link_idx(iso_config)
        for i in range(len(iso_config.links)):
            if i == nyc:
                continue
            np.testing.assert_allclose(out[:, i], ttc[i])

    def test_respects_tighter_existing_hourly_limit(self):
        """A pre-existing per-hour limit below the TSL is not loosened."""
        iso_config = _nyiso_cfg()
        n = len(iso_config.links)
        nyc = _nyc_link_idx(iso_config)
        ttc_t = np.full((T, n), 999999.0)
        ttc_t[:, nyc] = 100.0  # tighter than the 2,875 MW TSL
        out = apply_nyiso_nyc_tsl_import_cap(ttc_t, iso_config, "NYISO", 2023, T)
        np.testing.assert_allclose(out[:, nyc], 100.0)

    def test_non_nyiso_unchanged(self):
        iso_config = _nyiso_cfg()
        ttc = np.array([ln.ttc_mw for ln in iso_config.links], dtype=float)
        out = apply_nyiso_nyc_tsl_import_cap(ttc, iso_config, "ERCOT", 2023, T)
        assert out is ttc
