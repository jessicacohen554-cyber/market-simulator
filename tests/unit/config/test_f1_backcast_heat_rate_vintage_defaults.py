"""F1: vintage-matched eGRID heat rates, per-year measured rates, backcast defaults.

docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5.1 item 7.
Trivial cases first (a synthetic eGRID table, a one-plant artifact), then the
committed-config key stability of the six backcast-default flips.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from market_sim.config import scenarios as scen
from market_sim.config.scenarios import (
    ScenarioConfig,
    cache_key_drop_defaults,
    registration_time_default,
)
from market_sim.data import egrid
from market_sim.data.fleet import campd_bins

REPO = Path(__file__).resolve().parents[3]

F1_FIELDS = (
    "eia860_vintage_tracks_solve_year",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
)


# --------------------------------------------------------------------------- #
# 1. The vintage-aware join and its fallback order
# --------------------------------------------------------------------------- #
@pytest.fixture
def table() -> pd.DataFrame:
    """Plant 1 in every vintage; 2 in 2019 + 2023 only; 3 in 2021 only; 4 nowhere."""
    t = pd.DataFrame(
        {
            2019: {1: 10.19, 2: 9.19},
            2021: {1: 10.21, 3: 7.21},
            2023: {1: 10.23, 2: 9.23},
        }
    )
    t.index.name = "plant_id"
    return t


def test_same_year_vintage_wins(table):
    hr, src = egrid.resolve_plant_heat_rates(pd.Series([1]), 2021, table=table)
    assert hr.iloc[0] == 10.21 and src.iloc[0] == 2021


def test_nearest_vintage_fallback_tie_goes_earlier(table):
    # Plant 2 is absent from 2021; 2019 and 2023 are both two years away and
    # the tie goes to the EARLIER vintage.
    hr, src = egrid.resolve_plant_heat_rates(pd.Series([2]), 2021, table=table)
    assert hr.iloc[0] == 9.19 and src.iloc[0] == 2019


def test_nearest_vintage_by_distance(table):
    hr, src = egrid.resolve_plant_heat_rates(pd.Series([3]), 2023, table=table)
    assert hr.iloc[0] == 7.21 and src.iloc[0] == 2021


def test_class_table_only_when_absent_from_every_vintage(table):
    hr, src = egrid.resolve_plant_heat_rates(pd.Series([4]), 2021, table=table)
    assert pd.isna(hr.iloc[0]) and pd.isna(src.iloc[0])


def test_per_row_targets(table):
    # The retiree join: each unit its own last operating year.
    hr, src = egrid.resolve_plant_heat_rates(
        pd.Series([1, 1, 2]), pd.Series([2019, 2023, 2021]), table=table
    )
    assert list(hr) == [10.19, 10.23, 9.19]
    assert list(src) == [2019, 2023, 2019]


def test_eia860_dir_vintage_mapping():
    base = Path("data/raw/eia-860")
    assert egrid.egrid_vintage_for_eia860_dir(base / "vintage_2021") == 2021
    # The canonical snapshot joins the latest released vintage (no eGRID 2025).
    assert egrid.egrid_vintage_for_eia860_dir(base) == max(egrid._EGRID_FILES)
    assert egrid.egrid_sheet_name("PLNT", 2019) == "PLNT19"


def test_join_and_retiree_vintages(table, monkeypatch):
    from scripts.data import process_eia860 as pe

    monkeypatch.setattr(egrid, "_PLANT_HR_TABLE", table)
    df = pd.DataFrame(
        {"plant_id": [1, 2, 4], "planned_retirement_year": [2019, 2021, 2023]}
    )
    pe._join_egrid_heat_rate(df, pe.retiree_egrid_vintages(df))
    assert list(df["heat_rate"].iloc[:2]) == [10.19, 9.19]
    assert pd.isna(df["heat_rate"].iloc[2])


def test_rejoin_touches_only_heat_rate(table, monkeypatch, tmp_path):
    from scripts.data import process_eia860 as pe

    monkeypatch.setattr(egrid, "_PLANT_HR_TABLE", table)
    vdir = tmp_path / "vintage_2021"
    vdir.mkdir()
    path = vdir / "eia860_generators.parquet"
    before = pd.DataFrame({"plant_id": [1, 2, 3], "generator_id": ["a", "b", "c"]})
    before.to_parquet(path, index=False)
    pe.rejoin_heat_rate_in_place(path)
    after = pd.read_parquet(path)
    pd.testing.assert_frame_equal(after[["plant_id", "generator_id"]], before)
    assert list(after["heat_rate"]) == [10.21, 9.19, 7.21]


# --------------------------------------------------------------------------- #
# 2. The per-year measured artifact reader
# --------------------------------------------------------------------------- #
def test_measured_rate_map_year_then_pooled(tmp_path):
    path = tmp_path / "art.csv"
    pd.DataFrame(
        {
            "plant_code": [1, 2, 1, 2],
            "year": [0, 0, 2021, 2021],
            "heat_rate": [9.0, 10.0, 9.5, 11.0],
            "flag": ["ok", "ok", "ok", "below_physical_band"],
        }
    ).to_csv(path, index=False)
    assert campd_bins._measured_rate_map(path, None) == {1: 9.0, 2: 10.0}
    # 2021's own ok row wins for plant 1; plant 2's 2021 row is flagged, so
    # its pooled rate stands.
    assert campd_bins._measured_rate_map(path, 2021) == {1: 9.5, 2: 10.0}
    assert campd_bins._measured_rate_map(path, 2019) == {1: 9.0, 2: 10.0}


def test_pre_f1_artifact_reads_as_pooled(tmp_path):
    path = tmp_path / "old.csv"
    pd.DataFrame({"plant_code": [1], "heat_rate": [9.0], "flag": ["ok"]}).to_csv(
        path, index=False
    )
    assert campd_bins._measured_rate_map(path, 2021) == {1: 9.0}


# --------------------------------------------------------------------------- #
# 3. Backcast-only defaults: forecast / hindcast byte-identical
# --------------------------------------------------------------------------- #
def test_backcast_defaults_on():
    cfg = ScenarioConfig(mode="backcast")
    assert all(getattr(cfg, f) is True for f in F1_FIELDS)


@pytest.mark.parametrize(
    "kwargs", [{}, {"mode": "forecast"}, {"mode": "forecast", "hindcast": True}]
)
def test_coerced_off_outside_backcast(kwargs):
    cfg = ScenarioConfig(**kwargs)
    assert all(getattr(cfg, f) is False for f in F1_FIELDS)
    # Even an explicit True cannot arm them outside a backcast.
    armed = ScenarioConfig(**kwargs, **{f: True for f in F1_FIELDS})
    assert all(getattr(armed, f) is False for f in F1_FIELDS)


def test_forecast_key_byte_identical():
    explicit_off = ScenarioConfig(**{f: False for f in F1_FIELDS})
    assert ScenarioConfig().cache_key() == explicit_off.cache_key()
    hind = {"mode": "forecast", "hindcast": True}
    assert (
        ScenarioConfig(**hind).cache_key()
        == ScenarioConfig(**hind, **{f: False for f in F1_FIELDS}).cache_key()
    )


def test_explicit_false_reaches_pre_f1_backcast_posture():
    off = ScenarioConfig(mode="backcast", **{f: False for f in F1_FIELDS})
    assert all(getattr(off, f) is False for f in F1_FIELDS)
    assert off.cache_key() != ScenarioConfig(mode="backcast").cache_key()


def test_flips_are_declared_and_frozen_drop_value_unmoved():
    flips = {name: new for _, name, new in scen._CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS}
    drop = cache_key_drop_defaults()
    for f in F1_FIELDS:
        assert flips.get(f) == "True", f
        assert drop[f] is False, f
        assert registration_time_default(f) is False, f


# --------------------------------------------------------------------------- #
# 4. Every committed keeper run_config keeps its key
# --------------------------------------------------------------------------- #
def _keeper_ids(node) -> set[str]:
    """Every ``keeper`` / ``run_id`` string value in a keeper shard."""
    out: set[str] = set()
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("keeper", "run_id") and isinstance(v, str):
                out.add(v)
            else:
                out |= _keeper_ids(v)
    elif isinstance(node, list):
        for v in node:
            out |= _keeper_ids(v)
    return out


def _keeper_run_configs() -> list[Path]:
    out: set[Path] = set()
    for shard in (REPO / "frontend/data/backcast/keepers").glob("*.json"):
        for rid in _keeper_ids(json.loads(shard.read_text())):
            reg = REPO / "frontend/data/backcast/registry" / f"{rid}.json"
            if not reg.is_file():
                continue
            bundle = json.loads(reg.read_text()).get("bundle")
            if bundle:
                out |= set(
                    (REPO / "results/calibration" / Path(bundle).name).glob(
                        "run_config*.json"
                    )
                )
    return sorted(out)


def test_keeper_run_configs_found():
    assert len(_keeper_run_configs()) >= 9


@pytest.mark.parametrize(
    "path", _keeper_run_configs(), ids=lambda p: f"{p.parent.name}/{p.name}"
)
def test_keeper_key_unmoved_by_the_flips(path):
    """A keeper payload hashes the same before and after F1.

    Under (b'-1) a registered field drops from the hash at its FROZEN
    declaration (False, unchanged by F1), and a field ABSENT from a payload is
    what it was at registration (also False). So the pre-F1 construction of the
    payload — every one of the six present at its recorded value, else at its
    registration-time default — must hash exactly as the payload does now.
    """
    from scripts.lib.key_provenance import head_key

    payload = json.loads(path.read_text())["scenario_config"]
    pre_f1 = dict(payload)
    for f in F1_FIELDS:
        pre_f1.setdefault(f, registration_time_default(f))
    assert head_key(payload) == head_key(pre_f1)
    # And the recorded values survive a backcast rebuild (no coercion of an
    # explicit value inside a backcast).
    if payload.get("mode") == "backcast":
        rebuilt = ScenarioConfig(
            mode="backcast", **{f: payload[f] for f in F1_FIELDS if f in payload}
        )
        for f in F1_FIELDS:
            if f in payload:
                assert getattr(rebuilt, f) == payload[f], f
