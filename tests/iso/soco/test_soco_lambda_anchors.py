"""SOCO seam ``hr_by_year`` anchors from neighbour FERC 714 lambdas (lane soco-98).

Pins the repairs of FINDING-soco-33 §7 R-1 / R-2 and the registry they produce:

* the per-ISO anchor map of ``scripts/data/derive_neighbor_hr_by_year.py``
  carries a ``SOCO`` entry — MISO-South's zonal LMP for ``SOCO_MISO`` and a
  ``ferc714_lambda`` anchor (the neighbour's own Sch. 6 system lambda) for the
  five non-market seams; ``SOCO_SCEG`` / ``SOCO_FPL`` are reported unanchored;
* a lambda anchor takes the annual mean with filed zeros dropped;
* ``derive_neighbor_hr_elasticity.py`` reads the SAME per-ISO map and fails
  closed for an ISO with none (it used to exit 0 with an empty table);
* the registered ``hr_by_year`` IS the producer's output (integration, skipped
  without the committed data);
* every SOCO block stays default-off, so no keeper reads the anchors.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

from market_sim.config.interchange_config import (
    INTERFACE_NEIGHBORS,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    REFERENCE_PRICE_DEFAULT_ISOS,
)
from market_sim.config.paths import CALIBRATION_DIR, FERC_714_DIR
from market_sim.data.neighbor_price import neighbor_heat_rate

_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "scripts" / "data"

_LAMBDA_SEAMS = ("SOCO_TVA", "SOCO_DUK", "SOCO_SC", "SOCO_FPC", "SOCO_TAL", "SOCO_FPL")
_YEARS = list(range(2019, 2026))


def _load(stem: str):
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    spec = importlib.util.spec_from_file_location(stem, _SCRIPTS / f"{stem}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def producer():
    return _load("derive_neighbor_hr_by_year")


@pytest.fixture(scope="module")
def blocks() -> dict[str, object]:
    return {n.name: n for n in INTERFACE_NEIGHBORS["SOCO"]}


def test_soco_anchor_map_kinds(producer):
    anchors = producer.NEIGHBOR_LMP_ANCHORS["SOCO"]
    assert anchors["SOCO_MISO"] == producer.Anchor("zonal_MISO", ("MISO-South",))
    for name in _LAMBDA_SEAMS:
        assert anchors[name].kind == "ferc714_lambda", name
        assert anchors[name].product == name.removeprefix("SOCO_"), name
    assert set(producer.unanchored("SOCO")) == {"SOCO_SCEG"}


def test_lambda_anchor_is_the_annual_mean_without_filed_zeros(
    producer, tmp_path, monkeypatch
):
    import market_sim.data.ferc714 as ferc714

    stamps = pd.date_range("2023-01-01", periods=4, freq="h")
    pd.DataFrame(
        {
            "ba_code": "TAL",
            "report_year": 2023,
            "datetime_utc": stamps.astype(str),
            "system_lambda_usd_mwh": [10.0, 0.0, 20.0, 30.0],
            "respondent_id_ferc714": 140,
            "eia_utility_id": 18445,
            "source": "xbrl",
        }
    ).to_csv(tmp_path / ferc714.FERC714_NEIGHBOR_SYSTEM_LAMBDA_FILE, index=False)
    monkeypatch.setattr(ferc714, "FERC_714_DIR", tmp_path)
    anchor = producer.Anchor("TAL", kind="ferc714_lambda")
    assert producer._measured_mean_lmp(anchor, 2023) == pytest.approx(20.0)
    assert producer._measured_mean_lmp(anchor, 2024) is None


def _write_lambda(tmp_path, monkeypatch, series: dict[int, list[float]]) -> None:
    import market_sim.data.ferc714 as ferc714

    frames = [
        pd.DataFrame(
            {
                "ba_code": "FPL",
                "report_year": year,
                "datetime_utc": pd.date_range(
                    f"{year}-01-01", periods=len(vals), freq="h"
                ).astype(str),
                "system_lambda_usd_mwh": vals,
                "respondent_id_ferc714": 171,
                "eia_utility_id": 6452,
                "source": "xbrl",
            }
        )
        for year, vals in series.items()
    ]
    pd.concat(frames).to_csv(
        tmp_path / ferc714.FERC714_NEIGHBOR_SYSTEM_LAMBDA_FILE, index=False
    )
    monkeypatch.setattr(ferc714, "FERC_714_DIR", tmp_path)


def test_a_refiled_year_is_refused_and_reported(producer, tmp_path, monkeypatch):
    """A year equal to an earlier one at whole-dollar rounding is a re-filing."""
    first = [13.02, 16.04, 24.33, 17.6]
    _write_lambda(
        tmp_path,
        monkeypatch,
        {2019: first, 2020: [9.3, 12.4, 21.8, 14.0], 2021: [13.0, 16.0, 24.0, 18.0]},
    )
    assert producer.duplicate_filing_of("FPL", 2021) == 2019
    assert producer.duplicate_filing_of("FPL", 2020) is None
    assert producer.duplicate_filing_of("FPL", 2019) is None  # the original stands


def test_unknown_anchor_kind_is_refused(producer):
    with pytest.raises(ValueError):
        producer._measured_mean_lmp(producer.Anchor("TVA", kind="guess"), 2023)


def test_elasticity_fit_fails_closed_without_an_anchor_map():
    elastic = _load("derive_neighbor_hr_elasticity")
    with pytest.raises(KeyError):
        elastic.derive("NWPP", [2023, 2024])


def test_soco_blocks_stay_default_off_and_backcast_years_keep_their_cells(blocks):
    assert "SOCO" not in REFERENCE_PRICE_DEFAULT_ISOS
    assert "SOCO" not in PRICED_INTERCHANGE_DEFAULT_ISOS
    assert blocks["SOCO_SCEG"].hr_by_year is None
    assert 2021 not in blocks["SOCO_FPL"].hr_by_year  # duplicate filing refused
    for name, block in blocks.items():
        # Every backcast year is tabulated: the forward value never reaches it.
        for year, hr in (block.hr_by_year or {}).items():
            assert neighbor_heat_rate(block, year) == hr, (name, year)


def test_forward_years_price_off_the_seam_own_flat_mean(blocks):
    """Owner ruling 2026-10-02 (FINDING-soco-100 §7), lane soco-101."""
    for name, block in blocks.items():
        forward = neighbor_heat_rate(block, 2030)
        if block.hr_by_year:
            assert forward == block.forward_heat_rate, name
            assert block.forward_heat_rate != block.marginal_heat_rate, name
        else:
            assert block.forward_heat_rate is None, name
            assert forward == block.marginal_heat_rate, name
        # The forward-skill "flat" path reprices a backcast year off the same value.
        assert neighbor_heat_rate(block, 2024, forward_skill="flat") == forward, name
    # 2021 is untabulated for FPL (refused re-filing): it falls to the forward mean.
    fpl = blocks["SOCO_FPL"]
    assert neighbor_heat_rate(fpl, 2021) == fpl.forward_heat_rate


def test_registry_forward_heat_rate_is_the_producer_output(blocks):
    """forward_heat_rate IS the producer's output (rule 23: re-derivable, not typed)."""
    forward = _load("derive_neighbor_forward_hr")
    table = forward.derive("SOCO")
    assert set(table) == set(blocks)
    for name, value in table.items():
        assert blocks[name].forward_heat_rate == value, name
    with pytest.raises(KeyError):
        forward.derive("PJM")  # no ruling outside SOCO


def test_seam_own_flat_mean_is_equal_weight_over_present_cells():
    forward = _load("derive_neighbor_forward_hr")
    assert forward.seam_own_flat_mean(None) is None
    assert forward.seam_own_flat_mean({}) is None
    assert forward.seam_own_flat_mean({2019: 6.0, 2022: 7.0, 2025: 8.5}) == 7.17


def test_no_other_iso_registers_a_forward_heat_rate():
    for iso, neighbors in INTERFACE_NEIGHBORS.items():
        if iso == "SOCO":
            continue
        for block in neighbors:
            assert block.forward_heat_rate is None, (iso, block.name)


_DATA = (
    FERC_714_DIR / "soco_neighbor_hourly_system_lambda_2019_2025.csv",
    CALIBRATION_DIR / "actual_lmp_hourly_zonal_MISO.parquet",
)


@pytest.mark.skipif(
    not all(p.is_file() for p in _DATA), reason="SOCO seam anchor data not hydrated"
)
def test_registry_is_the_producer_output(producer, blocks):
    """The registry IS the producer's output (rule 23: re-derivable, not typed)."""
    shapeless: dict[str, list[int]] = {}
    try:
        table = producer.derive("SOCO", _YEARS, shapeless=shapeless)
    except FileNotFoundError as exc:  # EIA-930 shape extracts not hydrated
        pytest.skip(str(exc))
    for name, per_year in table.items():
        assert blocks[name].hr_by_year == per_year, name
    assert set(table) == {"SOCO_MISO", *_LAMBDA_SEAMS}
