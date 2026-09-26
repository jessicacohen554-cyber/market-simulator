"""The outage deriver folds CAMPD stack-duplicate twins (NYISO-NEXT-2).

``campd.CAMPD_STACK_DUPLICATE_UNITS`` names rows whose ``grossLoad`` repeats their
primary's (Astoria 8906 ``32SH``/``52SH``). Detecting on the duplicate books one
generator twice; the deriver must drop it, and the committed NYISO hour-grain
merit-guarded extract pair must carry no duplicate id.
"""

from __future__ import annotations

import pandas as pd

from market_sim.config.paths import RAW_DIR
from market_sim.data import campd
from scripts.data import derive_campd_unit_outages as d

_DUPES = {u for pairs in campd.CAMPD_STACK_DUPLICATE_UNITS.values() for u in pairs}


def test_unit_gross_years_ignores_the_duplicate_twin(monkeypatch):
    """A duplicate row's gross never marks its own id as producing."""
    frame = pd.DataFrame(
        {
            "facilityId": [8906, 8906, 8906],
            "unitId": ["31RH", "32SH", "20"],
            "grossLoad": [300.0, 300.0, 0.0],
        }
    )
    monkeypatch.setattr(d, "_load_unit_year", lambda state, year: frame.copy())
    got = d._unit_gross_years(["NY"], [2023])
    assert (8906, "31RH", 2023) in got
    assert not any(u in _DUPES for _, u, _ in got)


def test_committed_nyiso_hour_grain_pair_has_no_stack_duplicates():
    """The re-derived extract pair books Astoria once, on its physical basis."""
    for name in (
        "campd-unit-outages-perunitmerithour-NYISO.csv",
        "campd-unit-outages-layup-perunitmerithour-NYISO.csv",
    ):
        df = pd.read_csv(RAW_DIR / name)
        ast = df[df["facility_id"] == 8906]
        assert not set(ast["unit_id"].astype(str)) & _DUPES, name
        # 20 + 31RH + 51RH + the GT: ~934 MW, never the double-counted ~1,705.
        assert ast["plant_capacity_mw"].max() < 1000.0, name
