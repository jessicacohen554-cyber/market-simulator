"""Rule 19 plant partition between SOCO's campaign floor and the ST_GAS per-plant must-run floor (soco-83).

Owner ruling 2026-09-28 ("Partition by plant"): a plant whose ST_GAS rows already
carry ``MECH_ST_GAS_MUSTRUN_PER_PLANT`` in ``min_gen_mechanism`` is left to that
floor, and the campaign floor covers only the others. Trivial fleet, detector
stubbed: the test pins WHICH rows the campaign detector is handed.
"""

from types import SimpleNamespace

import numpy as np

from market_sim.data.floor_mechanisms import MECH_ST_GAS_MUSTRUN_PER_PLANT
from market_sim.pipeline import commitment as pc

T = 24


def _gen(code):
    return SimpleNamespace(fuel_type="gas_st", plant_group="ST_GAS", plant_code=code)


def _run(monkeypatch, mech):
    """Run the campaign floor on plants 1 and 2; return the per-row levels handed to the detector."""
    import market_sim.data.gas_st_campaign as gsc
    import market_sim.model.commitment as mc

    entry = SimpleNamespace(min_load_frac=0.1, min_run_hours=48, sync_share=0.8)
    monkeypatch.setattr(
        gsc, "load_gas_st_campaign_params", lambda iso: {1: entry, 2: entry}
    )
    seen = {}

    def fake_detector(p0, fa, fleet, *a, min_load_frac_by_gen=None, **k):
        seen["frac"] = np.asarray(min_load_frac_by_gen).copy()
        return np.where(min_load_frac_by_gen[:, None] > 0, 10.0, 0.0) * np.ones((1, T))

    monkeypatch.setattr(mc, "caiso_ra_mustoffer_min_gen", fake_detector)
    fleet = [_gen(1), _gen(2)]
    fa = SimpleNamespace(pmax=np.array([100.0, 100.0]), min_gen_mechanism=mech)
    floor = pc._soco_gas_st_campaign_floor("SOCO", fleet, fa, np.zeros((2, T)))
    return seen.get("frac"), floor


def test_no_mustrun_floor_campaign_covers_both(monkeypatch):
    frac, floor = _run(monkeypatch, np.zeros((2, T), dtype=np.int8))
    assert frac.tolist() == [0.1, 0.1]
    assert floor is not None and (floor > 0).all()


def test_mustrun_plant_is_left_to_its_own_floor(monkeypatch):
    mech = np.zeros((2, T), dtype=np.int8)
    mech[0, 5] = MECH_ST_GAS_MUSTRUN_PER_PLANT
    frac, floor = _run(monkeypatch, mech)
    assert frac.tolist() == [0.0, 0.1]
    assert (floor[0] == 0).all() and (floor[1] > 0).all()


def test_every_plant_under_mustrun_makes_campaign_inert(monkeypatch):
    mech = np.full((2, T), MECH_ST_GAS_MUSTRUN_PER_PLANT, dtype=np.int8)
    frac, floor = _run(monkeypatch, mech)
    assert frac is None and floor is None


def test_absent_attribution_is_byte_identical(monkeypatch):
    frac, _ = _run(monkeypatch, None)
    assert frac.tolist() == [0.1, 0.1]
