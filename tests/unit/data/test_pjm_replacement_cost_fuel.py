"""PJM-NEXT-13: replacement-cost fuel (IMM regional spot + measured transport).

Pinned here, on a trivial fleet with synthetic reference tables:

* flag off -> ``None`` and the prices are byte-untouched;
* gas rows take ``hub[region, month] + v`` as their monthly LEVEL and keep their
  own within-month shape; external-zone rows are never repriced;
* coal rows take ``sum s_b (spot_b + t_b) + s_u x current``;
* rule 25 (non-PJM armed), rule 19 (a coal passthrough sigmoid armed) and a year
  with no IMM series all raise;
* the field is registered, default-off and dropped from the cache key;
* the model's zone map is the derive's zone map (``v`` is measured against the hub
  it is added to).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fuel.basis import pjm_replacement as R

ZONES = [
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
]
HOURS = 24 * 59  # January + February: two monthly levels


@pytest.fixture()
def tables(tmp_path, monkeypatch):
    """Synthetic IMM spot, gas transport and coal tables; the module cache cleared."""
    rows = [
        "iso,year,period,fleet_segment,metric,value,unit,source_doc,source_page,note"
    ]
    for seg, base in (
        ("east_gas", 2.0),
        ("west_gas", 1.5),
        ("production_gas", 1.0),
        ("napp_coal", 2.2),
    ):
        for m in range(1, 13):
            rows.append(
                f"PJM,2024,month_{m:02d},{seg},{R.IMM_SPOT_METRIC},{base + 0.1 * m},usd_per_mmbtu,x,1,n"
            )
    spot = tmp_path / "som.csv"
    spot.write_text("\n".join(rows) + "\n")
    gas = tmp_path / "gas.csv"
    gas.write_text("# c\nplant_id,group,v_usd_mmbtu\n101,CC_REGULAR,0.25\n")
    (tmp_path / "gas.pool.csv").write_text(
        "rung,key,v_usd_mmbtu\ngroup,CC_REGULAR,0.40\npjm,__PJM__,0.50\n"
    )
    coal = tmp_path / "coal.csv"
    coal.write_text(
        "# c\nplant_id,group,year,spot_segment,share,transport_usd_mmbtu\n"
        "201,COAL_BIT,2024,napp_coal,0.6,0.5\n201,COAL_BIT,2024,UNPRICED,0.4,\n"
    )
    monkeypatch.setattr(R, "IMM_SPOT_PATH", spot)
    monkeypatch.setattr(R, "GAS_TRANSPORT_PATH", gas)
    monkeypatch.setattr(R, "COAL_REPLACEMENT_PATH", coal)
    R._CACHE.clear()
    yield
    R._CACHE.clear()


def _fleet():
    gens = [
        Generator(
            unit_id="A", name="A", zone="PJM_EMAAC", fuel_type="gas_cc", pmax_mw=400.0
        ),
        Generator(
            unit_id="B",
            name="B",
            zone="PJM_West_APS",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="C", name="C", zone="PJM_AEP_Ohio", fuel_type="coal", pmax_mw=600.0
        ),
    ]
    fa = generators_to_fleet_arrays(gens, ZONES, hours=HOURS)
    fa.plant_code = np.array([101, 102, 201])
    fa.plant_group = np.array(["CC_REGULAR", "CC_REGULAR", "COAL_BIT"], dtype=object)
    return fa


def _cfg(**kw):
    return ScenarioConfig(
        iso="PJM", hours=HOURS, mode="backcast", pjm_replacement_cost_fuel=True, **kw
    )


def test_registered_default_off_and_key_stable():
    assert ScenarioConfig().pjm_replacement_cost_fuel is False
    assert cache_key_drop_defaults()["pjm_replacement_cost_fuel"] is False
    base = ScenarioConfig(iso="PJM", mode="backcast")
    assert (
        base.cache_key()
        != base.with_overrides(pjm_replacement_cost_fuel=True).cache_key()
    )


def test_flag_off_is_a_no_op(tables):
    fa = _fleet()
    fp = np.full((fa.n_gen, HOURS), 3.0)
    assert (
        R.apply_pjm_replacement_cost_fuel(fp, fa, ScenarioConfig(iso="PJM"), 2024)
        is None
    )
    np.testing.assert_array_equal(fp, 3.0)


def test_gas_level_replaced_shape_kept_and_coal_blend(tables):
    fa = _fleet()
    shape = 1.0 + 0.1 * np.sin(np.arange(HOURS) / 5.0)
    fp = np.vstack([3.0 * shape, 3.0 * shape, np.full(HOURS, 4.0)])
    mask = R.apply_pjm_replacement_cost_fuel(fp, fa, _cfg(), 2024)
    assert mask.all()
    jan = slice(0, 24 * 31)
    # EMAAC -> east_gas Jan 2.1, own v 0.25; West_APS -> production Jan 1.1, group pool 0.40
    assert fp[0, jan].mean() == pytest.approx(2.35)
    assert fp[1, jan].mean() == pytest.approx(1.5)
    feb = slice(24 * 31, HOURS)
    assert fp[0, feb].mean() == pytest.approx(2.2 + 0.25)
    ratio = fp[0, jan] / fp[0, jan].mean()
    np.testing.assert_allclose(ratio, shape[jan] / shape[jan].mean())
    # coal: 0.6 x (napp Jan 2.3 + 0.5) + 0.4 x 4.0
    assert fp[2, jan].mean() == pytest.approx(0.6 * 2.8 + 0.4 * 4.0)


def test_guards(tables):
    fa = _fleet()
    fp = np.full((fa.n_gen, HOURS), 3.0)
    with pytest.raises(ValueError, match="rule 25"):
        R.apply_pjm_replacement_cost_fuel(
            fp,
            fa,
            ScenarioConfig(iso="MISO", mode="backcast", pjm_replacement_cost_fuel=True),
            2024,
        )
    with pytest.raises(ValueError, match="rule 19"):
        R.apply_pjm_replacement_cost_fuel(
            fp, fa, _cfg(coal_bit_passthrough_sigmoid=True), 2024
        )
    with pytest.raises(ValueError, match="fail closed"):
        R.apply_pjm_replacement_cost_fuel(fp, fa, _cfg(), 2030)


def test_zone_map_matches_the_derive():
    import importlib.util
    from pathlib import Path

    p = (
        Path(__file__).resolve().parents[3]
        / "scripts/data/derive_pjm_replacement_fuel.py"
    )
    spec = importlib.util.spec_from_file_location("_derive_pjm_repl", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.ZONE_GAS_REGION == R.PJM_ZONE_GAS_REGION
