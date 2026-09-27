"""``unit_outage_full_rederive``: the full HEAD re-derive of PJM's outage extracts (PJM-NEXT-5).

The gate selects the ``-rederive-unitfuel-`` standard companion (replacing the
``-memberrepair-unitfuel-`` file of the same family) and the ``-short-rederive-``
short-coal companion. Default off, byte-inert off, falls back when not derived.
"""

from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_full_rederive is False

    def test_dropped_from_the_cache_key_at_its_default(self):
        assert cache_key_drop_defaults()["unit_outage_full_rederive"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_full_rederive=True)
        assert base.cache_key() != armed.cache_key()


def _lay(tmp_path, monkeypatch, *names):
    import market_sim.data.outages as om

    monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
    for n in names:
        (tmp_path / n).write_text("x\n")
    return om


_FAMILY = (
    "campd-unit-outages-memberrepair-PJM.csv",
    "campd-unit-outages-memberrepair-unitfuel-PJM.csv",
    "campd-unit-outages-rederive-unitfuel-PJM.csv",
)


class TestStandardSelector:
    """Replaces the unit-fuel file of the same family; needs that family armed."""

    def test_selects_the_companion(self, tmp_path, monkeypatch):
        om = _lay(tmp_path, monkeypatch, *_FAMILY)
        path = om.unit_outage_csv_for_iso(
            "PJM", membership_repair=True, unit_fuel_routing=True, full_rederive=True
        )
        assert path.name == "campd-unit-outages-rederive-unitfuel-PJM.csv"

    def test_off_keeps_the_unitfuel_extract(self, tmp_path, monkeypatch):
        om = _lay(tmp_path, monkeypatch, *_FAMILY)
        path = om.unit_outage_csv_for_iso(
            "PJM", membership_repair=True, unit_fuel_routing=True
        )
        assert path.name == "campd-unit-outages-memberrepair-unitfuel-PJM.csv"

    def test_needs_unit_fuel_routing(self, tmp_path, monkeypatch):
        om = _lay(tmp_path, monkeypatch, *_FAMILY)
        path = om.unit_outage_csv_for_iso(
            "PJM", membership_repair=True, full_rederive=True
        )
        assert path.name == "campd-unit-outages-memberrepair-PJM.csv"

    def test_falls_back_when_not_derived(self, tmp_path, monkeypatch):
        om = _lay(tmp_path, monkeypatch, *_FAMILY[:2])
        path = om.unit_outage_csv_for_iso(
            "PJM", membership_repair=True, unit_fuel_routing=True, full_rederive=True
        )
        assert path.name == "campd-unit-outages-memberrepair-unitfuel-PJM.csv"


class TestShortSelector:
    """The short-coal companion moves with the same field."""

    def test_selects_the_short_companion(self, tmp_path, monkeypatch):
        om = _lay(
            tmp_path,
            monkeypatch,
            "campd-unit-outages-short-PJM.csv",
            "campd-unit-outages-short-rederive-PJM.csv",
        )
        path = om.unit_outage_short_csv_for_iso("PJM", full_rederive=True)
        assert path.name == "campd-unit-outages-short-rederive-PJM.csv"

    def test_off_and_fallback_keep_the_incumbent(self, tmp_path, monkeypatch):
        om = _lay(tmp_path, monkeypatch, "campd-unit-outages-short-PJM.csv")
        assert om.unit_outage_short_csv_for_iso("PJM").name == "campd-unit-outages-short-PJM.csv"
        assert (
            om.unit_outage_short_csv_for_iso("PJM", full_rederive=True).name
            == "campd-unit-outages-short-PJM.csv"
        )
