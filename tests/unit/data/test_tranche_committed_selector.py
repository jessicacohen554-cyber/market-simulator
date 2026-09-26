"""The bin builder's committed share rides the full CAMPD artifact selector pair (NYISO-NEXT-3).

``campd_bins.fleet_to_bins`` read ``thermal_tranche_overrides`` with ``per_unit`` only, so
under ``campd_outage_merit_order_guard`` a bin's committed_pct came off the UNGUARDED
``-perunit-`` tranche artifact while every other tranche consumer read ``-perunitmerit-``
(rule 19 ``[R-ONE-MECH]``: one availability basis per LP).
"""

from __future__ import annotations

import pandas as pd
import pytest

import market_sim.data.fleet.campd_bins as cb


class _Cfg:
    """Minimal config stub: attributes are flags, absent -> False."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ({}, (False, False)),
        ({"campd_per_unit_attribution": True}, (True, False)),
        (
            {
                "campd_per_unit_attribution": True,
                "campd_outage_merit_order_guard": True,
            },
            (True, True),
        ),
        # merit_guard has no meaning without per_unit (campd_attribution_selectors).
        ({"campd_outage_merit_order_guard": True}, (False, False)),
    ],
)
def test_fleet_to_bins_passes_the_selector_pair(monkeypatch, flags, expected):
    """The committed-share read receives (per_unit, merit_guard) exactly as the accessor."""
    seen = []

    def _record(iso, coal_online_pmin=False, per_unit=False, merit_guard=False):
        seen.append((per_unit, merit_guard))
        return {}

    monkeypatch.setattr(cb, "thermal_tranche_overrides", _record)
    cb.fleet_to_bins([], "NYISO", _Cfg(**flags))
    assert seen == [expected]


def test_merit_guard_reads_the_guarded_committed_share(monkeypatch, tmp_path):
    """With both flags armed the committed share is the '-perunitmerit-' artifact's."""
    cols = {"name": "P", "status": "ok", "mustrun_pct": 0.0}
    pd.DataFrame(
        [{"plant_code": 1, "plant_group": "ST_GAS", "committed_pct": 30.0, **cols}]
    ).to_csv(tmp_path / "thermal_tranches-perunit-NYISO.csv", index=False)
    pd.DataFrame(
        [{"plant_code": 1, "plant_group": "ST_GAS", "committed_pct": 9.0, **cols}]
    ).to_csv(tmp_path / "thermal_tranches-perunitmerit-NYISO.csv", index=False)
    monkeypatch.setattr(cb, "PROCESSED_DIR", tmp_path)
    cb.thermal_tranche_overrides.cache_clear()
    seen = []
    orig = cb.thermal_tranche_overrides

    def _spy(*a, **k):
        out = orig(*a, **k)
        seen.append(out)
        return out

    monkeypatch.setattr(cb, "thermal_tranche_overrides", _spy)
    try:
        cb.fleet_to_bins(
            [],
            "NYISO",
            _Cfg(campd_per_unit_attribution=True, campd_outage_merit_order_guard=True),
        )
    finally:
        orig.cache_clear()
    assert seen == [{(1, "ST_GAS"): (9.0, 0.0)}]
