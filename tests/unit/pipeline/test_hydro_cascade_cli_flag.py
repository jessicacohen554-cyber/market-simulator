"""``--hydro-cascade-coupling`` on the calibration CLI (lane NWPP-40, 2026-09-16).

NWPP-36 built ``ScenarioConfig.hydro_cascade_coupling`` (owner ruling N3) with
no CLI surface: the only routes to arm it were a recipe, an ISOConfig default
override, or ``replay_keeper.py --set`` (which needs an existing bundle). The
first NWPP keeper arms it from ``scripts/run_calibration_full.py``, so the flag
rides the generic ``prb_overrides`` ScenarioConfig channel — the ERCOT-65 drift
class this pins: CLI spelling, config field and recorded name must agree.

Four legs, none of which runs a solve:

1. The parser carries the tri-state flag (``--hydro-cascade-coupling`` /
   ``--no-hydro-cascade-coupling``, default ``None``), captured from the real
   ``main()`` parser by intercepting ``parse_args`` — nothing after the parser
   is built executes.
2. The value reaches the ``prb_overrides`` dict under the exact field name
   (source-level, the same encoding the flag registry tests use).
3. ``hydro_cascade_coupling`` is a real ``ScenarioConfig`` field (rule 24).
4. Arming moves the cache key; the default does not (G8 as amended by N3).
"""

from __future__ import annotations

import argparse
import re

import pytest

from market_sim.config.scenarios import ScenarioConfig
from tests.helpers import REPO_ROOT

CLI = REPO_ROOT / "scripts" / "run_calibration_full.py"


class _ParserCaptured(Exception):
    def __init__(self, parser: argparse.ArgumentParser):
        self.parser = parser


def _capture_parser(monkeypatch) -> argparse.ArgumentParser:
    """Build ``main()``'s parser and stop at the first ``parse_args`` call."""
    from scripts import run_calibration_full as rcf

    def _raise(self, *_a, **_k):
        raise _ParserCaptured(self)

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", _raise)
    monkeypatch.setattr("sys.argv", ["run_calibration_full.py"])
    with pytest.raises(_ParserCaptured) as exc:
        rcf.main()
    return exc.value.parser


def test_flag_is_tristate_and_defaults_to_none(monkeypatch):
    parser = _capture_parser(monkeypatch)
    monkeypatch.undo()
    args = parser.parse_args(["--iso", "NWPP", "--year", "2024"])
    assert args.hydro_cascade_coupling is None
    on = parser.parse_args(["--hydro-cascade-coupling"])
    assert on.hydro_cascade_coupling is True
    off = parser.parse_args(["--no-hydro-cascade-coupling"])
    assert off.hydro_cascade_coupling is False


def test_flag_rides_the_prb_overrides_channel_under_the_field_name():
    src = CLI.read_text(encoding="utf-8")
    assert re.search(
        r'"hydro_cascade_coupling":\s*args\.hydro_cascade_coupling,', src
    ), "the flag must be routed into prb_overrides under the ScenarioConfig field name"


def test_field_exists_on_scenario_config():
    assert "hydro_cascade_coupling" in ScenarioConfig.__dataclass_fields__
    assert ScenarioConfig().hydro_cascade_coupling is False


def test_arming_moves_the_cache_key_and_the_default_does_not():
    base = ScenarioConfig(iso="NWPP", mode="backcast")
    assert (
        base.with_overrides(hydro_cascade_coupling=False).cache_key()
        == base.cache_key()
    )
    assert (
        base.with_overrides(hydro_cascade_coupling=True).cache_key() != base.cache_key()
    )


def test_hydro_cascade_sidecar_frame_shape_and_absence():
    """``_hydro_cascade_frame`` is None when the arrays are None, long otherwise."""
    import numpy as np
    from types import SimpleNamespace

    from scripts import run_calibration_full as rcf

    assert rcf._hydro_cascade_frame(2024, "P1", SimpleNamespace()) is None
    res = SimpleNamespace(
        hydro_cascade_spill=np.ones((2, 24)),
        hydro_cascade_storage=np.zeros((2, 24)),
        hydro_cascade_water_value=np.full((2, 24), 0.5),
        hydro_cascade_plant_codes=np.array([3921, 3075]),
    )
    f = rcf._hydro_cascade_frame(2024, "P1", res)
    assert len(f) == 48
    assert set(f.columns) == {
        "year",
        "pass",
        "plant_code",
        "hour",
        "spill_kcfs",
        "pond_kcfsh",
        "water_value",
    }
    assert sorted(f["plant_code"].unique().tolist()) == [3075, 3921]
    assert int(f["year"].iloc[0]) == 2024
