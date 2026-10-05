"""closeout-MISO-w3e: MISO joins EIA930_GAS_FOLD_REFUTED (bench-only).

MISO's EIA-930 gas cell is measured not to carry a geothermal/biomass fold:
930 gas sits 13-28 TWh BELOW the EIA-923 gas generation of MISO-BA plants in
every year 2019-2025 (SOCO-60's test), and the fold F the deflation would
subtract (OTHER + biomass - 930 Other) is chp=Y host energy the BA never
meters. With the measured CHP shares the 923 grid fossil total then reconciles
to RAW 930 gas+coal inside the deadband, so the combined reconcile no longer
fires for MISO.
"""

from __future__ import annotations

import importlib.util

import pytest

from scripts.lib import benchmark_semantics as bs
from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "rch_miso_fold", str(REPO_ROOT / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)

# 2019 MISO, measured-share basis (FINDING-closeout-miso-w3e-bench-reconciliation
# system table): gas+coal family 443.2 TWh pre-reconcile; EIA-930 gas 191.0 +
# coal 238.9 = 429.9; Other 6.74; bench OTHER 11.46 + biomass 9.37 (F = 14.09).
E930_2019 = {"gas": 190.995, "coal": 238.927, "other": 6.74}
NONFOSSIL_2019 = {"OTHER": 11.4599, "biomass": 9.3674}


def _classfull(total: float) -> dict[str, float]:
    """A two-class fossil family summing to ``total`` plus the 2019 non-fossil rows."""
    return {"CC_CHP": 30.0, "COAL_PRB": round(total - 30.0, 4), **NONFOSSIL_2019}


def test_miso_fold_is_refuted():
    """MISO's deflation is zero; the measured geo/biomass term is untouched."""
    assert "MISO" in bs.EIA930_GAS_FOLD_REFUTED
    assert bs.gas_foldin_deflation(dict(NONFOSSIL_2019), E930_2019, "MISO") == 0.0
    assert bs.geo_biomass_outside_930_other(dict(NONFOSSIL_2019), E930_2019) == (
        pytest.approx(14.0873, abs=1e-3)
    )


def test_reconcile_does_not_fire_for_miso_2019():
    """443.2 against raw 429.9 is inside the 0.97 deadband: no scale for MISO."""
    cf = _classfull(443.2)
    before = dict(cf)
    rch.reconcile_vintage_classes(cf, dict(E930_2019), "MISO")
    assert cf == before


def test_same_numbers_fire_under_a_folding_ba():
    """The identical 2019 numbers on a BA whose fold is not refuted scale down to 415.8."""
    cf = _classfull(443.2)
    rch.reconcile_vintage_classes(cf, dict(E930_2019), "PJM")
    fam = cf["CC_CHP"] + cf["COAL_PRB"]
    assert fam == pytest.approx(429.922 - 14.0873, abs=0.01)


@pytest.mark.parametrize(
    "year,family,e930",
    [
        (2020, 394.1, 389.0),
        (2021, 428.7, 420.1),
        (2022, 426.7, 425.5),
        (2023, 414.5, 416.2),
        (2024, 416.2, 419.2),
        (2025, 425.4, 425.3),
    ],
)
def test_measured_vs_930_table_is_in_band(year, family, e930):
    """Every year of the measured-vs-930 table sits inside the reconcile deadband."""
    frac = bs.VINTAGE_RECONCILE_FRAC
    assert frac * e930 <= family <= e930 / frac


def test_other_isos_unchanged():
    """Only MISO is added; every other ISO keeps its prior deflation behaviour."""
    assert bs.EIA930_GAS_FOLD_REFUTED == frozenset({"SOCO", "CAISO", "MISO"})
    for iso in ("ERCOT", "PJM", "NYISO", "NEISO", "SPP", "NWPP"):
        assert bs.gas_foldin_deflation(dict(NONFOSSIL_2019), E930_2019, iso) > 0.0
