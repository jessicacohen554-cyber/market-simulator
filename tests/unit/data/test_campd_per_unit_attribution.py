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


class TestResolvedInputsProvenance:
    """The run_config must name the bytes the run actually consumed.

    A bundle whose ``resolved_inputs`` names the incumbent artifact for a run
    that read a companion is the exact reproducibility failure this session
    diagnosed, one level up: the record would be wrong rather than merely
    absent.
    """

    class _Cfg:
        iso = "NYISO"
        outage_source = "historic"
        unit_outage_mixed_gas_routing = False
        campd_per_unit_attribution = False

    class _CfgOn(_Cfg):
        campd_per_unit_attribution = True

    def test_both_blocks_follow_the_gate(self):
        from market_sim.data.resolved_inputs import (
            _campd_unit_outages_block,
            _thermal_tranche_block,
        )

        off_t = _thermal_tranche_block(self._Cfg(), "NYISO")["path"]
        on_t = _thermal_tranche_block(self._CfgOn(), "NYISO")["path"]
        off_o = _campd_unit_outages_block(self._Cfg(), "NYISO")["path"]
        on_o = _campd_unit_outages_block(self._CfgOn(), "NYISO")["path"]
        assert off_t.endswith("thermal_tranches_NYISO.csv")
        assert on_t.endswith("thermal_tranches-perunit-NYISO.csv")
        assert off_o.endswith("campd-unit-outages-NYISO.csv")
        assert on_o.endswith("campd-unit-outages-perunit-NYISO.csv")

    def test_ercot_tranche_block_reports_unarmed(self):
        """ERCOT runs the CAMPD bin sheet and has no tranche artifact."""
        from market_sim.data.resolved_inputs import _thermal_tranche_block

        assert _thermal_tranche_block(self._CfgOn(), "ERCOT")["armed"] is False


class TestMeritOrderGuardSelector:
    """nyiso-177: the lay-up guard is the SECOND half of the same selector.

    ``campd_outage_merit_order_guard`` picks the ``-perunitmerit-`` pair — the
    same per-unit attribution derived against a merit-order-guarded outage
    extract. A tranche row's statistics are computed over an outage-derated
    denominator, so the two artifacts must move together or a solve carries two
    availability bases inside one LP. These pin the same five properties the
    per-unit gate has: default-off, byte-inert off, falling back, complete, and
    coupled.
    """

    def test_field_defaults_off(self):
        assert ScenarioConfig(iso="NYISO").campd_outage_merit_order_guard is False

    def test_inert_without_the_per_unit_gate(self):
        """The guarded companions exist only on the per-unit routing."""
        from market_sim.data.fleet.campd_bins import campd_attribution_selectors

        cfg = ScenarioConfig(iso="NYISO", campd_outage_merit_order_guard=True)
        assert campd_attribution_selectors(cfg) == (False, False)
        assert thermal_tranche_csv_for_iso("NYISO", False, True).name == (
            "thermal_tranches_NYISO.csv"
        )
        assert unit_outage_csv_for_iso("NYISO", merit_order_guard=True).name == (
            "campd-unit-outages-NYISO.csv"
        )

    def test_selector_pair_is_armed_only_together(self):
        from market_sim.data.fleet.campd_bins import campd_attribution_selectors

        both = ScenarioConfig(
            iso="NYISO",
            campd_per_unit_attribution=True,
            campd_outage_merit_order_guard=True,
        )
        assert campd_attribution_selectors(both) == (True, True)
        pu_only = ScenarioConfig(iso="NYISO", campd_per_unit_attribution=True)
        assert campd_attribution_selectors(pu_only) == (True, False)

    def test_guarded_companions_selected_when_present(self, tmp_path, monkeypatch):
        import market_sim.data.fleet.campd_bins as cb
        import market_sim.data.outages as om

        monkeypatch.setattr(cb, "PROCESSED_DIR", tmp_path)
        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        for n in (
            "thermal_tranches_NYISO.csv",
            "thermal_tranches-perunit-NYISO.csv",
            "thermal_tranches-perunitmerit-NYISO.csv",
        ):
            (tmp_path / n).write_text("plant_code\n")
        for n in (
            "campd-unit-outages-perunit-NYISO.csv",
            "campd-unit-outages-perunitmerit-NYISO.csv",
        ):
            (tmp_path / n).write_text("x\n")
        assert cb.thermal_tranche_csv_for_iso("NYISO", True, True).name == (
            "thermal_tranches-perunitmerit-NYISO.csv"
        )
        assert om.unit_outage_csv_for_iso(
            "NYISO", per_unit_crosswalk=True, merit_order_guard=True
        ).name == ("campd-unit-outages-perunitmerit-NYISO.csv")

    def test_falls_back_to_the_unguarded_companion_when_absent(
        self, tmp_path, monkeypatch
    ):
        """An ISO with no guarded companion keeps the unguarded one."""
        import market_sim.data.fleet.campd_bins as cb
        import market_sim.data.outages as om

        monkeypatch.setattr(cb, "PROCESSED_DIR", tmp_path)
        monkeypatch.setattr(om, "UNIT_OUTAGE_CSV", tmp_path / "campd-unit-outages.csv")
        (tmp_path / "thermal_tranches_MISO.csv").write_text("plant_code\n")
        (tmp_path / "thermal_tranches-perunit-MISO.csv").write_text("plant_code\n")
        (tmp_path / "campd-unit-outages-perunit-MISO.csv").write_text("x\n")
        assert cb.thermal_tranche_csv_for_iso("MISO", True, True).name == (
            "thermal_tranches-perunit-MISO.csv"
        )
        assert om.unit_outage_csv_for_iso(
            "MISO", per_unit_crosswalk=True, merit_order_guard=True
        ).name == ("campd-unit-outages-perunit-MISO.csv")

    def test_every_tranche_reader_takes_the_guard_too(self):
        """Completeness, same invariant as the per-unit gate's own test."""
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
            if "merit_guard" not in args and "config" not in args:
                missing.append(node.name)
        assert not missing, f"readers with no way to receive the guard: {missing}"

    def test_registered_for_the_run_config(self):
        """Rule 24 [R-REGISTRY]: the tunable reaches run_config.json."""
        from market_sim.config.scenarios import (
            _CACHE_KEY_OPTIONAL_FIELDS,
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
        )

        assert "campd_outage_merit_order_guard" in _CACHE_KEY_OPTIONAL_FIELDS
        assert (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["campd_outage_merit_order_guard"]
            == "False"
        )


class TestFleetGroupOverrideDisarmedOnTheRepairedPath:
    """nyiso-177 repair 1, rule 19 [R-ONE-MECH].

    ``_FLEET_GROUP_OVERRIDE`` enumerates per plant the very defect the per-unit
    crosswalk repairs generally. On the repaired path it is redundant — and
    actively wrong, because it drags a mixed plant's correctly-routed CC units
    onto the steam bin, leaving the CC bin with no derate at all. It must be
    disarmed there and ONLY there: on the incumbent extract it is load-bearing.
    """

    def test_override_still_applies_on_the_incumbent_path(self):
        from market_sim.data.outages import _generic_unit_outage_target

        assert _generic_unit_outage_target(2500, "30", "CC_REGULAR") == (
            2500,
            "ST_GAS",
        )

    def test_override_disarmed_on_the_per_unit_path(self):
        from market_sim.data.outages import _generic_unit_outage_target

        assert _generic_unit_outage_target(
            2500, "UCC001", "CC_REGULAR", per_unit_crosswalk=True
        ) == (2500, "CC_REGULAR")
        assert _generic_unit_outage_target(
            2500, "30", "ST_GAS", per_unit_crosswalk=True
        ) == (2500, "ST_GAS")

    def test_ct_exclusion_survives_both_paths(self):
        from market_sim.data.outages import _generic_unit_outage_target

        for pu in (False, True):
            assert (
                _generic_unit_outage_target(
                    2500, "X", "CT_PEAKER", per_unit_crosswalk=pu
                )
                is None
            )
