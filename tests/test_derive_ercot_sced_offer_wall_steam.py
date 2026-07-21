"""Trivial-case + committed-artifact tests for the RT steam wall derive.

Covers ``scripts/data/derive_ercot_sced_offer_wall_steam.py`` (the ERCOT-92
steam leg of the ERCOT-86 RT/SCED spare-offer wall construction): the
fleet-scope splitter at trivial scale (unknown-name hard error, fleet vs
disclosed non-fleet split, NaN-HSL null-not-NaN discipline), the resource-name
map's integrity against the model's own ST_GAS fleet registry, and — when the
committed artifact is present — its geometry (shared DAM bin edges/quantiles),
year scoping (2023-2025 training window, no pooled fallback), fleet-scope
disclosure, and the measured mid-band relationship (RT steam upper rungs above
the DAM steam ladder's — the ERCOT-84/86 measured-cheap-DAM-basis finding, on
steam). The CC/CT RT artifact's ST-free invariant stays where it lives
(``test_ercot_offer_surface_cleared_share_rt``) — this sibling artifact is the
steam-owner seam's own basis, rule 19.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.data import derive_ercot_sced_offer_wall_steam as steam

REPO = Path(__file__).resolve().parents[1]
_ST_JSON = (
    REPO / "data/raw/_validation-source/ercot_sced_offer_wall_steam_condbinned.json"
)
_DAM_JSON = REPO / "data/raw/_validation-source/ercot_dam_cleared_share_condbinned.json"
_CBA = REPO / "data/raw/reference/custom-bin-assignments.csv"


def _frame(names, statuses=None, hasl=100.0, bp=0.0, hsl=100.0):
    """Minimal gas-steam SCED frame: one row per name (trivial-case scale)."""
    n = len(names)
    return pd.DataFrame(
        {
            "Resource Name": names,
            "Telemetered Resource Status": statuses if statuses else ["ON"] * n,
            "HASL": [hasl] * n,
            "HSL": [hsl] * n,
            "Base Point": [bp] * n,
        }
    )


# ---------------------------------------------------------------------------
# _scope_fleet at trivial scale
# ---------------------------------------------------------------------------


def test_unknown_resource_is_hard_error():
    """A gas-steam name in neither map forces a review, never a silent drop."""
    df = _frame(["BRAUNIG_VHB1", "NEWSTEAM_X1"])
    with pytest.raises(ValueError, match="NEWSTEAM_X1"):
        steam._scope_fleet(df)


def test_fleet_scope_splits_and_discloses():
    df = _frame(
        ["BRAUNIG_VHB1", "STEAM_STEAM_2", "STEAM_STEAM_2"],
        statuses=["ON", "ON", "OFF"],
        hasl=80.0,
        bp=30.0,
    )
    fleet, excluded = steam._scope_fleet(df)
    assert list(fleet["Resource Name"]) == ["BRAUNIG_VHB1"]
    assert set(excluded) == {"STEAM_STEAM_2"}
    assert excluded["STEAM_STEAM_2"]["rows"] == 2
    # only the ON row contributes spare: HASL 80 - BP 30
    assert excluded["STEAM_STEAM_2"]["on_spare_mw_sum"] == 50.0
    assert excluded["STEAM_STEAM_2"]["max_hsl_mw"] == 100.0


def test_excluded_all_nan_hsl_is_null_not_nan():
    """Never-telemetered HSL must serialize as null (strict JSON), not NaN."""
    df = _frame(["DOWGEN_DOW_ST65"], hasl=np.nan, hsl=np.nan)
    _, excluded = steam._scope_fleet(df)
    assert excluded["DOWGEN_DOW_ST65"]["max_hsl_mw"] is None
    assert excluded["DOWGEN_DOW_ST65"]["on_spare_mw_sum"] == 0.0
    json.loads(json.dumps(excluded), parse_constant=pytest.fail)


def test_fleet_only_frame_has_empty_disclosure():
    fleet, excluded = steam._scope_fleet(_frame(["WAP_WAP_G1", "CBY_CBY_G2"]))
    assert len(fleet) == 2
    assert excluded == {}


# ---------------------------------------------------------------------------
# Resource-name map integrity vs the model's own fleet registry
# ---------------------------------------------------------------------------


def test_map_targets_are_model_fleet_plants():
    cba = pd.read_csv(_CBA)
    st_plants = set(cba.loc[cba["Plant_Group"] == "ST_GAS", "Plant_Name"])
    mapped = set(steam.FLEET_PLANT_OF_RESOURCE.values())
    assert mapped <= st_plants
    # the only model plant with no corpus presence is CFB (zero CEMS operation)
    assert st_plants - mapped == {"CFB Power Plant"}
    assert not set(steam.FLEET_PLANT_OF_RESOURCE) & steam.NON_FLEET_RESOURCES


# ---------------------------------------------------------------------------
# Committed-artifact checks (the real derive output, when present)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _ST_JSON.exists(), reason="steam RT artifact not derived")
def test_artifact_shares_dam_bin_geometry():
    st = json.loads(_ST_JSON.read_text())
    dam = json.loads(_DAM_JSON.read_text())
    assert (
        st["_provenance"]["netload_pct_edges"]
        == dam["_provenance"]["netload_pct_edges"]
    )
    assert (
        st["_provenance"]["ladder_quantiles"] == dam["_provenance"]["ladder_quantiles"]
    )


@pytest.mark.skipif(not _ST_JSON.exists(), reason="steam RT artifact not derived")
def test_artifact_is_year_scoped_st_only():
    st = json.loads(_ST_JSON.read_text())
    assert set(st) == {"_provenance", "ST"}
    assert "pooled" not in st["ST"], "no pooled fallback by design (rule 13)"
    years = set(st["ST"]["years"])
    # 2023 included since the full-year NP3-965 intake (2026-07-21): the owner
    # authorized extending the SCED basis to 2023, lifting the earlier
    # post-Uri regime bar. Training window only — no 2022/2026 holdout years.
    assert years <= {"2023", "2024", "2025"}


@pytest.mark.skipif(not _ST_JSON.exists(), reason="steam RT artifact not derived")
def test_artifact_fleet_scope_disclosed():
    st = json.loads(_ST_JSON.read_text())
    prov = st["_provenance"]
    assert prov["fleet_scope"]["resource_map"] == steam.FLEET_PLANT_OF_RESOURCE
    assert prov["classes"] == {"ST": list(steam.ST_RESTYPES)}
    for year in st["ST"]["years"]:
        cov = prov["coverage"][year]
        assert cov["plants"], "per-plant coverage must be disclosed"
        assert "excluded_non_fleet" in cov
        assert cov["fleet_plants_absent"] == []


@pytest.mark.skipif(not _ST_JSON.exists(), reason="steam RT artifact not derived")
def test_artifact_midband_upper_rungs_exceed_dam_st():
    """The steam RT spare's mid-band upper rungs stand above the DAM ladder.

    The ERCOT-84/86 finding measured on steam: over the mid-band bins
    (p80-p97, indices -3/-2 on the shared 7-bin geometry) the top rung (q90)
    of the RT steam surface strictly exceeds the DAM steam ladder's — the DAM
    basis is structurally cheap for the band-hour increment.
    """
    st = json.loads(_ST_JSON.read_text())
    dam = json.loads(_DAM_JSON.read_text())
    for year, tbl in st["ST"]["years"].items():
        dam_tbl = dam["ST"]["years"].get(year)
        if dam_tbl is None:
            continue
        for b in (-3, -2):
            assert tbl["ladder"][b][-1][1] > dam_tbl["ladder"][b][-1][1]
