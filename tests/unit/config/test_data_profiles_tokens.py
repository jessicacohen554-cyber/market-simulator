"""The data-profile ISO tokens attribute SPP's files without stealing ERCOT's.

SPP plan §7 gate G3 (``docs/multi-iso/spp-addition-plan-2026-09.md``): a bare
``spp`` token would also match ERCOT's settlement-point LMP zips
(``DAMLZHBSPP_<year>.zip`` — "DAM LZ/HB settlement point prices"), so every SPP
token in ``configs/data-profiles.yaml`` is delimiter-bounded. These tests pin
the trap on the names that motivated it, through the same ``iso_for_name`` /
``owner_of`` functions ``scripts/hydrate_data.py`` classifies the tree with.
"""

from __future__ import annotations

import pytest

from scripts import hydrate_data


@pytest.fixture(scope="module")
def isos() -> dict:
    return hydrate_data.load_manifest()["isos"]


def test_spp_profile_and_tokens_exist(isos):
    manifest = hydrate_data.load_manifest()
    assert "SPP" in isos and isos["SPP"]["tokens"]
    assert manifest["profiles"]["spp"]["iso"] == "SPP"
    # No SPP token is the bare `spp` (or `SPP`) substring — that is the trap.
    assert "spp" not in {t.lower() for t in isos["SPP"]["tokens"]}


@pytest.mark.parametrize(
    "name",
    ["SWPP hourly.parquet", "SWPP interchange hourly.parquet", "SWPP_fueltype.parquet"],
)
def test_swpp_balancing_authority_files_are_spp_owned(isos, name):
    """The EIA-930 / EIA-860 balancing-authority code SWPP attributes to SPP."""
    assert hydrate_data.iso_for_name(name, isos) == "SPP"


@pytest.mark.parametrize(
    "name",
    [
        "spp-planning",
        "spp-hsl",
        "spp-genmix",
        "spp-binding-constraints",
        "spp-or-mcp",
        "spp-hourly-load",
    ],
)
def test_spp_corpus_directories_are_spp_owned(isos, name):
    assert hydrate_data.iso_for_name(name, isos) == "SPP"


@pytest.mark.parametrize("name", ["DAMLZHBSPP_2023.zip", "DAMLZHBSPP_2024.zip"])
def test_ercot_settlement_point_zips_are_not_spp_owned(isos, name):
    """G3: the ERCOT settlement-point zips must never be claimed by SPP."""
    assert hydrate_data.iso_for_name(name, isos) != "SPP"


def test_ercot_zip_paths_keep_their_pre_spp_owner(isos):
    """Path-level attribution: the zips sit DIRECTLY under the ``lmp-data`` split
    directory (``data/raw/lmp-data/DAMLZHBSPP_<year>.zip``), so the split-child
    rule name-tests the zip itself — exactly where a bare ``spp`` token would
    have stolen them. Their owner must be what it was before SPP registered
    (``shared``, by the same rule), never SPP.
    """
    paths = [
        "data/raw/lmp-data/DAMLZHBSPP_2023.zip",
        "data/raw/lmp-data/DAMLZHBSPP_2024.zip",
        "data/raw/lmp-data/ERCOT/x.csv",
        "data/raw/lmp-data/MISO/x.csv",
    ]
    splits = hydrate_data.split_dirs(paths, isos)
    pre_spp = {k: v for k, v in isos.items() if k != "SPP"}
    for path in paths[:2]:
        owner = hydrate_data.owner_of(path, isos, splits)
        assert owner != "SPP"
        assert owner == hydrate_data.owner_of(path, pre_spp, splits)


def test_no_other_iso_claims_an_spp_name(isos):
    """Symmetric safety: no earlier ISO's tokens match the SPP names above."""
    for name in ("SWPP hourly.parquet", "spp-planning"):
        assert hydrate_data.iso_for_name(name, isos) == "SPP"
