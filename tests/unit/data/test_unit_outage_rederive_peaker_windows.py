"""``unit_outage_rederive_peaker_windows``: the F2 re-derive with listed-peaker windows kept (PJM-NEXT-6).

The gate selects the ``-rederive-peakerkeep-unitfuel-`` companion, replacing the
``-rederive-unitfuel-`` file it is a variant of. Default off, byte-inert off,
meaningful only with ``full_rederive``, falls back when not derived.
"""

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_rederive_peaker_windows is False

    def test_dropped_from_the_cache_key_at_its_default(self):
        assert cache_key_drop_defaults()["unit_outage_rederive_peaker_windows"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_rederive_peaker_windows=True)
        assert base.cache_key() != armed.cache_key()


_FAMILY = (
    "campd-unit-outages-memberrepair-PJM.csv",
    "campd-unit-outages-memberrepair-unitfuel-PJM.csv",
    "campd-unit-outages-rederive-unitfuel-PJM.csv",
    "campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv",
)


def _lay(tmp_path, monkeypatch, *names):
    import market_sim.data.outages as om

    monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
    for n in names:
        (tmp_path / n).write_text("x\n")
    return om


_ARMED = dict(membership_repair=True, unit_fuel_routing=True, full_rederive=True)


def test_selects_the_companion(tmp_path, monkeypatch):
    om = _lay(tmp_path, monkeypatch, *_FAMILY)
    path = om.unit_outage_csv_for_iso("PJM", rederive_peaker_windows=True, **_ARMED)
    assert path.name == "campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv"


def test_off_keeps_the_f2_file(tmp_path, monkeypatch):
    om = _lay(tmp_path, monkeypatch, *_FAMILY)
    path = om.unit_outage_csv_for_iso("PJM", **_ARMED)
    assert path.name == "campd-unit-outages-rederive-unitfuel-PJM.csv"


def test_needs_full_rederive(tmp_path, monkeypatch):
    om = _lay(tmp_path, monkeypatch, *_FAMILY)
    path = om.unit_outage_csv_for_iso(
        "PJM",
        membership_repair=True,
        unit_fuel_routing=True,
        rederive_peaker_windows=True,
    )
    assert path.name == "campd-unit-outages-memberrepair-unitfuel-PJM.csv"


def test_falls_back_when_not_derived(tmp_path, monkeypatch):
    om = _lay(tmp_path, monkeypatch, *_FAMILY[:3])
    path = om.unit_outage_csv_for_iso("PJM", rederive_peaker_windows=True, **_ARMED)
    assert path.name == "campd-unit-outages-rederive-unitfuel-PJM.csv"
