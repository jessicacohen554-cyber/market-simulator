"""Tests for the backcast→forecast parity check (FR-22 / FFR-1E).

Trivial cases first per the repo testing pattern: a synthetic ``ScenarioConfig``
source and a synthetic one-field keeper posture, then the real seven-keeper sweep
and the nyiso-102 regression (``docs/FINDING-nyiso102-d5-parity-wiring-2026-07-30.md``).

No LP anywhere — the checker is pure ``ast`` + ``json``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts import check_forecast_parity as cfp
from scripts.lib import forecast_parity_registry as reg

REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Trivial: the defaults parser
# ---------------------------------------------------------------------------

TRIVIAL_CONFIG_SRC = '''
from dataclasses import dataclass, field

@dataclass
class ScenarioConfig:
    """Trivial config."""

    a_flag: bool = False
    a_level: float = 1.0
    a_path: str = "mid"
    a_map: dict = field(default_factory=dict)
    a_list: list = field(default_factory=lambda: ["x"])
    a_derived: str = str(SOME_PATH / "x.csv")
'''


def test_defaults_parse_literals_factories_and_unresolved():
    defaults = cfp.scenario_defaults(TRIVIAL_CONFIG_SRC)
    assert defaults["a_flag"] is False
    assert defaults["a_level"] == 1.0
    assert defaults["a_path"] == "mid"
    assert defaults["a_map"] == {}
    assert defaults["a_list"] == ["x"]
    # A default the parser cannot evaluate is UNRESOLVED, never silently
    # equal — so such a field always needs a registry row.
    assert defaults["a_derived"] is cfp.UNRESOLVED
    assert cfp._equal("anything", cfp.UNRESOLVED) is False


def test_armed_fields_is_the_non_default_set():
    defaults = cfp.scenario_defaults(TRIVIAL_CONFIG_SRC)
    rc = {"scenario_config": {"a_flag": True, "a_level": 1.0, "a_path": "mid"}}
    assert cfp.armed_fields(rc, defaults) == {"a_flag": True}


def test_armed_fields_does_not_confuse_bool_and_number():
    defaults = cfp.scenario_defaults(TRIVIAL_CONFIG_SRC)
    # True == 1 in Python; a flag flipped on must not read as "default 1.0".
    rc = {"scenario_config": {"a_level": True}}
    assert "a_level" in cfp.armed_fields(rc, defaults)


# ---------------------------------------------------------------------------
# Trivial: the source scan and its exclusions
# ---------------------------------------------------------------------------


def _scan_one(tmp_path: Path, rel: str, src: str, fields: set[str]):
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(src)
    return cfp.scan_sources(tmp_path, frozenset(fields), paths=[path])


def test_scan_finds_attr_getattr_and_string_reads(tmp_path):
    src = (
        "def build(config):\n"
        "    x = config.a_flag\n"
        "    y = getattr(config, 'a_level', None)\n"
        "    return apply(config, config_field='a_path')\n"
    )
    sites = _scan_one(tmp_path, "m.py", src, {"a_flag", "a_level", "a_path"})
    assert sites["a_flag"][0].kind == "attr"
    assert sites["a_level"][0].kind == "attr"
    assert sites["a_path"][0].kind == "string"


def test_scan_ignores_self_reads_and_docstrings(tmp_path):
    src = (
        "class ScenarioConfig:\n"
        "    def check(self):\n"
        '        """Mentions a_path in prose."""\n'
        "        return self.a_flag\n"
    )
    sites = _scan_one(tmp_path, "m.py", src, {"a_flag", "a_path"})
    assert sites == {}


def test_scan_drops_reads_inside_archived_functions(tmp_path, monkeypatch):
    """A read inside the archived P2 pass is not evidence of a live path.

    This is the nyiso-102 trap: ``run_commitment_pass`` names
    ``nyiso_local_selfsupply`` in its ``preserve_min_gen`` chain while the
    mechanism itself was unwired in forecast. Counting it would have made this
    very check green on the incident that motivated it.
    """
    src = "def run_commitment_pass(cfg):\n    return getattr(cfg, 'a_flag', False)\n"
    monkeypatch.setattr(
        reg, "ARCHIVED_FUNCTIONS", frozenset({("m.py", "run_commitment_pass")})
    )
    assert _scan_one(tmp_path, "m.py", src, {"a_flag"}) == {}


def test_backcast_role_sources_are_not_forecast_evidence(tmp_path, monkeypatch):
    src = "def run_year(config):\n    return config.a_flag\n"
    monkeypatch.setattr(reg, "SOURCE_ROLES", {"b.py": "backcast"})
    sites = _scan_one(tmp_path, "b.py", src, {"a_flag"})
    assert sites["a_flag"], "the site is recorded"
    assert not cfp.forecast_evidence("a_flag", sites), "but it is not (a) evidence"


# ---------------------------------------------------------------------------
# Trivial: one-field synthetic keeper postures through the real registry
# ---------------------------------------------------------------------------


def _synthetic(tmp_path: Path, **fields) -> Path:
    path = tmp_path / "run_config.json"
    path.write_text(json.dumps({"scenario_config": fields}))
    return path


def _sweep(tmp_path: Path, **fields):
    reports, _ = cfp.run(REPO, extra_configs=[("TEST", _synthetic(tmp_path, **fields))])
    return {v.field: v for v in reports[0].verdicts}


def test_single_armed_wired_mechanism_passes(tmp_path):
    v = _sweep(tmp_path, nyiso_local_selfsupply=True)["nyiso_local_selfsupply"]
    assert v.status == "FORECAST_WIRED"
    assert cfp.reg.FORECAST_ORCHESTRATOR in v.detail


def test_single_declared_backcast_only_mechanism_passes(tmp_path):
    v = _sweep(tmp_path, pjm_congestion=True)["pjm_congestion"]
    assert v.status == "BACKCAST_ONLY"


def test_parameter_of_unarmed_parent_is_inert(tmp_path):
    v = _sweep(tmp_path, caiso_gas_floor_frac=0.8)["caiso_gas_floor_frac"]
    assert v.status == "INERT"


def test_parameter_inherits_an_armed_parent_disposition(tmp_path):
    got = _sweep(tmp_path, miso_seam_flow_limit=True, miso_seam_envelope_merit_cap=True)
    assert got["miso_seam_envelope_merit_cap"].status == "BACKCAST_ONLY"


def test_unaccounted_mechanism_fails_loud(tmp_path):
    """An armed field with neither (a) nor (b) is the failure this check exists for.

    The victim is chosen from the tree rather than hard-coded, so the test
    keeps working as mechanisms get wired or declared.
    """
    defaults = cfp.scenario_defaults((REPO / cfp._CONFIG_REL).read_text())
    sites = cfp.scan_sources(REPO, frozenset(defaults))
    victims = [
        name
        for name in sorted(defaults)
        if not cfp.forecast_evidence(name, sites)
        and reg.declaration_for(name) is None
        and defaults[name] is False
    ]
    assert victims, "no undeclared backcast-only field left to exercise the failure"
    victim = victims[0]

    v = _sweep(tmp_path, **{victim: True})[victim]
    assert v.status == "UNACCOUNTED"

    rc = _synthetic(tmp_path, **{victim: True})
    assert cfp.main(["--keeper-config", f"TEST={rc}"]) == 1


# ---------------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------------


def test_registry_is_internally_valid():
    defaults = cfp.scenario_defaults((REPO / cfp._CONFIG_REL).read_text())
    sites = cfp.scan_sources(REPO, frozenset(defaults))
    assert cfp.check_registry(REPO, defaults, sites) == []


def test_every_declaration_carries_a_reason():
    for row in reg.DECLARATIONS:
        assert row.why.strip(), row.fields


def test_declaration_rejects_an_unknown_disposition():
    with pytest.raises(ValueError):
        reg.ParityDeclaration(fields=("x",), disposition="MAYBE", why="no")


def test_stale_backcast_only_declaration_is_rejected(monkeypatch):
    """Declaring a field that IS forecast-wired must fail, so (b) cannot rot.

    Without this, a mechanism wired forward later would keep a permanent
    "backcast-only by design" exemption and the check would go blind to it.
    """
    defaults = cfp.scenario_defaults((REPO / cfp._CONFIG_REL).read_text())
    sites = cfp.scan_sources(REPO, frozenset(defaults))
    stale = reg.ParityDeclaration(
        fields=("nyiso_local_selfsupply",),
        disposition=reg.BACKCAST_ONLY,
        why="pretend it never went forward",
        evidence=("src/market_sim/runner.py",),
    )
    monkeypatch.setattr(reg, "DECLARATIONS", (stale,))
    failures = cfp.check_registry(REPO, defaults, sites)
    assert any("stale declaration" in f for f in failures)


def test_dynamic_consumer_patterns_are_anchored_and_narrow():
    """A loose pattern would hand forecast evidence to fields nobody reads."""
    for dyn in reg.DYNAMIC_CONSUMERS:
        ast.parse(f"re.fullmatch(r'''{dyn.pattern}''', 'x')")  # syntactically sane
        assert "(.*)" not in dyn.pattern and ".*" not in dyn.pattern


# ---------------------------------------------------------------------------
# The real seven-keeper sweep (six ISOs until SPP-20 registered SPP, 2026-09-06)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def keeper_sweep():
    return cfp.run(REPO)


# FR-22 CLOSED 2026-09-06 (session Y-18,
# docs/handoffs/FINDING-y18-fr22-parity-2026-09-06.md). The two long-open
# unaccounted fields were adjudicated on their own merits against rule 13
# ``[R-MEASURED]`` and landed on OPPOSITE dispositions, which is why the pin
# below is now empty rather than merely shorter:
#
#   * ``ercot_storage_as_soc_reserve`` -> BACKCAST_ONLY. Its measured awards are
#     a per-historical-year 60-Day-DAM corpus with no forward artifact, and its
#     forecast substitute (``ercot_storage_as_endogenous``) is named in the
#     function docstring AND enforced by a mutual-exclusion validator.
#   * ``nyiso_seam_deliverability_envelope`` -> GAP. Its own module asserts
#     rule-13 forward regeneration verbatim, so BACKCAST_ONLY was REFUSED; it is
#     filed beside its rule-19 superseding twin ``nyiso_seam_par_attribution``,
#     which owner ruling R-X reserves to the forecast desk.
#
# The assertion is now the strong form — ZERO unaccounted, in every ISO — so the
# property FR-22 protects ("a new keeper mechanism cannot quietly fork the two
# paths") is enforced without an exemption list to rot. A newly-armed mechanism
# with no consumer and no declaration reds this test immediately.


def test_all_nine_keepers_resolve(keeper_sweep):
    # NINE since SOCO and NWPP carry designated keepers (keeper shards
    # frontend/data/backcast/keepers/{SOCO,NWPP}.json). Both resolve CLEAN --
    # 45 / 43 armed, 0 UNACCOUNTED (Y-29 read, 2026-09-24) -- so they add no
    # exemption and the strong zero-unaccounted form below applies to them
    # unchanged. Rule 26 [R-DELETE]: the seven-ISO set and the function's own
    # "seven" name are replaced, not hedged (owner ruling R-BE, director board
    # v43, 2026-09-25; proposal docs/handoffs/FINDING-y29-promotion-provenance-
    # 2026-09-24.md §4; executed by audit lane Y-31).
    #
    # SEVEN since SPP-20 registered SPP as the seventh ISO (2026-09-06) and the
    # SPP desk designated a keeper: the sweep reads the keeper shards, so SPP
    # entered it the moment frontend/data/backcast/keepers/SPP.json landed and
    # the six-ISO set assertion went stale by construction. Extended (not
    # relaxed) by SPP-38: SPP resolves CLEAN at 2026-09-07 -- 34 armed, 34
    # FORECAST_WIRED, 0 alias / 0 backcast-only / 0 inert / 0 GAP / 0
    # UNACCOUNTED on 2026-09-07-spp-2-crosswalk-hydro -- so it adds no exemption
    # and the strong zero-unaccounted form below applies to it unchanged. Rule
    # 26 [R-DELETE]: the six-ISO set and the function's own "six" name are
    # replaced, not hedged with an SPP special case.
    # (docs/handoffs/FINDING-spp-38-2026-09-07.md §3, row 5.)
    reports, registry_failures = keeper_sweep
    assert registry_failures == []
    assert {r.iso for r in reports} == {
        "ERCOT",
        "PJM",
        "CAISO",
        "NYISO",
        "NEISO",
        "MISO",
        "SPP",
        "SOCO",
        "NWPP",
    }
    for rep in reports:
        assert rep.errors == [], rep.iso
        assert rep.verdicts, f"{rep.iso}: no armed mechanisms read — sweep is blind"
        unaccounted = sorted(v.field for v in rep.by_status("UNACCOUNTED"))
        assert not unaccounted, (
            f"{rep.iso}: {unaccounted} armed in the keeper with no "
            "forecast-orchestrator consumer and no registry declaration — "
            "resolve it or declare it in scripts/lib/forecast_parity_registry.py"
        )


def test_check_exits_zero_on_the_current_keepers():
    assert cfp.main([]) == 0


def test_strict_gaps_mode_fails_while_gaps_are_open():
    """The filed gaps are real; --strict-gaps is how a session opts into failing."""
    assert cfp.main(["--strict-gaps"]) == 1


def test_nyiso_downstate_family_is_forecast_wired(keeper_sweep):
    """Regression for nyiso-102: the three downstate mechanisms must pass (a).

    They were wired into ``runner.py`` on 2026-07-30; if any of them regresses
    to backcast-only, this fails rather than waiting for the next accident.
    """
    reports, _ = keeper_sweep
    nyiso = next(r for r in reports if r.iso == "NYISO")
    got = {v.field: v for v in nyiso.verdicts}
    for name in ("nyiso_local_selfsupply", "nyiso_li_lcr_tsl", "nyiso_nyc_lcr_tsl"):
        assert got[name].status == "FORECAST_WIRED", name
        assert got[name].detail.startswith("orchestrator @"), name


def test_markdown_report_covers_every_iso(keeper_sweep, tmp_path):
    reports, failures = keeper_sweep
    text = cfp.render_markdown(reports, failures)
    for rep in reports:
        assert rep.iso in text and rep.run_id in text
