"""nyiso-176: the ``campd_per_unit_attribution`` gate over BOTH CAMPD inputs.

The two CAMPD-derived solve inputs each attribute a MIXED plant's measured
conduct by a proxy rather than by the units' own meters, and the two proxies
differ: ``derive_thermal_tranches._fleet_nameplate_and_group`` gives a plant's
facility-summed CAMPD net to "the group holding the most nameplate", while
``derive_campd_unit_outages._resolve_unit_group`` short-circuits on a
last-writer-wins facility group. ``ScenarioConfig.campd_per_unit_attribution``
selects the ``-perunit-`` companion of BOTH, written by
``--per-unit-attribution`` / ``--per-unit-crosswalk`` through the single shared
``scripts/lib/campd_measured_classes`` crosswalk.

These tests pin the five things the gate must be: DEFAULT-OFF, BYTE-INERT while
off, FALLING BACK when a companion has not been derived, COMPLETE (it reaches
EVERY reader of the tranche artifact — the invariant that stops a solve from
reading two artifact vintages at once), and COUPLED (one field moves both
artifacts, rule 19 ``[R-ONE-MECH]``).
"""

from __future__ import annotations

import ast
from pathlib import Path

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.campd_bins import thermal_tranche_csv_for_iso
from market_sim.data.outages import unit_outage_csv_for_iso

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "src" / "market_sim"


class TestDefaultOffAndInert:
    def test_field_defaults_off(self):
        assert ScenarioConfig(iso="NYISO").campd_per_unit_attribution is False

    def test_tranche_path_unchanged_while_off(self):
        for iso in ("NYISO", "ERCOT", "CAISO", "PJM", "MISO", "NEISO"):
            assert thermal_tranche_csv_for_iso(iso).name == (
                f"thermal_tranches_{iso}.csv"
            )

    def test_outage_path_unchanged_while_off(self):
        assert unit_outage_csv_for_iso("NYISO").name == ("campd-unit-outages-NYISO.csv")
        assert unit_outage_csv_for_iso("ERCOT").name == "campd-unit-outages.csv"


class TestCompanionSelection:
    def test_tranche_companion_selected_when_present(self, tmp_path, monkeypatch):
        import market_sim.data.fleet.campd_bins as cb

        monkeypatch.setattr(cb, "PROCESSED_DIR", tmp_path)
        (tmp_path / "thermal_tranches_NYISO.csv").write_text("plant_code\n")
        (tmp_path / "thermal_tranches-perunit-NYISO.csv").write_text("plant_code\n")
        assert cb.thermal_tranche_csv_for_iso("NYISO", True).name == (
            "thermal_tranches-perunit-NYISO.csv"
        )

    def test_tranche_falls_back_when_companion_absent(self, tmp_path, monkeypatch):
        import market_sim.data.fleet.campd_bins as cb

        monkeypatch.setattr(cb, "PROCESSED_DIR", tmp_path)
        (tmp_path / "thermal_tranches_ERCOT.csv").write_text("plant_code\n")
        assert cb.thermal_tranche_csv_for_iso("ERCOT", True).name == (
            "thermal_tranches_ERCOT.csv"
        )

    def test_outage_companion_selected_when_present(self, tmp_path, monkeypatch):
        import market_sim.data.outages as om

        base = tmp_path / "campd-unit-outages.csv"
        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", base)
        (tmp_path / "campd-unit-outages-perunit-NYISO.csv").write_text("x\n")
        assert om.unit_outage_csv_for_iso("NYISO", per_unit_crosswalk=True).name == (
            "campd-unit-outages-perunit-NYISO.csv"
        )

    def test_outage_falls_back_when_companion_absent(self, tmp_path, monkeypatch):
        import market_sim.data.outages as om

        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        assert om.unit_outage_csv_for_iso("MISO", per_unit_crosswalk=True).name == (
            "campd-unit-outages-MISO.csv"
        )

    def test_per_unit_outranks_mixed_gas_routing(self, tmp_path, monkeypatch):
        """Both companions present: the WIDER repair wins.

        ``-unitroute-`` repairs a strict subset of the same object and is
        measurably wrong where the two disagree (nyiso-175b K3), so it must
        never shadow ``-perunit-``.
        """
        import market_sim.data.outages as om

        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        (tmp_path / "campd-unit-outages-perunit-NYISO.csv").write_text("x\n")
        (tmp_path / "campd-unit-outages-unitroute-NYISO.csv").write_text("x\n")
        assert (
            om.unit_outage_csv_for_iso(
                "NYISO", mixed_gas_routing=True, per_unit_crosswalk=True
            ).name
            == "campd-unit-outages-perunit-NYISO.csv"
        )


class TestGateCompleteness:
    """THE load-bearing invariant: no reader may bypass the resolver.

    A solve that read the ``-perunit-`` artifact through some readers and the
    incumbent through others would mix two artifact vintages inside one LP —
    silently, and in a way no output would reveal. The guarantee is structural:
    every read of ``thermal_tranches_<ISO>.csv`` in ``src/`` goes through
    :func:`thermal_tranche_csv_for_iso`, so a new reader added later cannot
    quietly reintroduce a hardcoded path.
    """

    def test_no_hardcoded_tranche_path_outside_the_resolver(self):
        offenders = []
        for path in SRC.rglob("*.py"):
            for i, line in enumerate(path.read_text().splitlines(), 1):
                if 'f"thermal_tranches_{iso' in line and "base = " not in line:
                    offenders.append(f"{path.relative_to(REPO)}:{i}")
        assert not offenders, (
            "these read the tranche artifact without the resolver, so the "
            f"campd_per_unit_attribution gate cannot reach them: {offenders}"
        )

    def test_every_tranche_reader_takes_the_selector(self):
        """Each cached reader that resolves the path exposes ``per_unit``."""
        tree = ast.parse((SRC / "data/fleet/campd_bins.py").read_text())
        missing = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            src = ast.unparse(node)
            if "thermal_tranche_csv_for_iso(" not in src:
                continue
            if node.name == "thermal_tranche_csv_for_iso":
                continue
            args = {a.arg for a in node.args.args}
            # ``assert_thermal_tranche_coverage`` reads the gate off ``config``.
            if "per_unit" not in args and "config" not in args:
                missing.append(node.name)
        assert not missing, f"readers with no way to receive the gate: {missing}"
