"""The data-profile ISO tokens attribute SPP's files without stealing ERCOT's.

SPP plan §7 gate G3 (``docs/multi-iso/spp-addition-plan-2026-09.md``): a bare
``spp`` token would also match ERCOT's settlement-point LMP zips
(``DAMLZHBSPP_<year>.zip`` — "DAM LZ/HB settlement point prices"), so every SPP
token in ``configs/data-profiles.yaml`` is delimiter-bounded. These tests pin
the trap on the names that motivated it, through the same ``iso_for_name`` /
``owner_of`` functions ``scripts/hydrate_data.py`` classifies the tree with.
"""

from __future__ import annotations

import re

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


# --- SOCO (registered 2026-09-14, lane SOCO-20; SOCO plan §7 gate G3) --------


def test_soco_profile_and_token_exist(isos):
    manifest = hydrate_data.load_manifest()
    assert "SOCO" in isos and isos["SOCO"]["tokens"] == ["soco"]
    assert manifest["profiles"]["soco"]["iso"] == "SOCO"


@pytest.mark.parametrize(
    "name",
    ["SOCO_fueltype.parquet", "SOCO_region.parquet", "soco-planning"],
)
def test_soco_owned_names_attribute_to_soco(isos, name):
    assert hydrate_data.iso_for_name(name, isos) == "SOCO"


def test_soco_token_collides_with_no_other_raw_name(isos):
    """G3, measured on the real tree: `soco` is a substring of NO non-SOCO
    `data/raw` name, so every name it claims is SOCO's own (unlike SPP's
    `spp` in ERCOT's `DAMLZHBSPP_*`). Reads trees only (partial-clone safe)."""
    paths = [p for _, p in hydrate_data.raw_entries()]
    if not paths:
        pytest.skip("no data/raw at HEAD")
    soco_named = {
        seg for p in paths for seg in p.split("/")[2:] if "soco" in seg.lower()
    }
    # A COLLISION is `soco` embedded in a longer word (`socorro`, `prosocol`);
    # a SOCO-owned name carries it as a delimited token at any position. The
    # original stem check (`startswith("soco")` or `_soco_`) was narrower than
    # the naming conventions SOCO intakes then used — suffix-delimited
    # `campd-unit-outages-perunit-SOCO.meta.json`, `thermal_tranches_SOCO.csv`
    # — every one of them SOCO's own (Y-30, 2026-09-24, measured on the tree).
    token = re.compile(r"(?<![a-z])soco(?![a-z])")
    for seg in soco_named:
        assert token.search(seg.lower()), seg


def test_no_earlier_iso_claims_a_soco_name(isos):
    """Symmetric safety: no other ISO's tokens match SOCO's names."""
    pre_soco = {k: v for k, v in isos.items() if k != "SOCO"}
    for name in ("SOCO_fueltype.parquet", "SOCO_region.parquet", "soco-planning"):
        assert hydrate_data.iso_for_name(name, pre_soco) is None


class TestSplitChildWholeNameMatch:
    """The whole-name limb for split-directory children (lane SPP-34, R-4).

    A split directory's child IS the ISO label — ``lmp-data/ERCOT``,
    ``zone-specific-demand/SPP``, ``load-forecast/spp``. Because SPP's tokens
    are delimiter-bounded to dodge ``DAMLZHBSPP_*.zip``, none of them matched a
    bare ``SPP`` / ``spp`` directory name, so those two subtrees classified
    ``shared`` — hydrated by every profile instead of only by ``spp``.
    ``iso_for_split_child`` tries whole-name equality first, which closes the
    gap without re-admitting the substring trap.
    """

    @pytest.mark.parametrize("name", ["SPP", "spp", "Spp", " spp "])
    def test_exact_child_name_resolves_to_spp(self, isos, name):
        assert hydrate_data.iso_for_split_child(name, isos) == "SPP"
        # The plain token matcher is what could NOT do this — the reason the
        # limb exists. If this ever starts passing, the tokens changed and the
        # DAMLZHBSPP trap needs re-checking.
        assert hydrate_data.iso_for_name(name, isos) is None

    @pytest.mark.parametrize("iso", ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"])
    def test_every_other_iso_still_resolves_by_whole_name(self, isos, iso):
        assert hydrate_data.iso_for_split_child(iso, isos) == iso
        assert hydrate_data.iso_for_split_child(iso.lower(), isos) == iso

    def test_the_trap_is_still_shut(self, isos):
        """Whole-name equality does not re-admit the ERCOT settlement zips."""
        for name in ("DAMLZHBSPP_2023.zip", "RTMLZHBSPP_2025.zip"):
            assert hydrate_data.iso_for_split_child(name, isos) != "SPP"

    def test_spp_split_children_are_spp_owned_end_to_end(self, isos):
        paths = [
            "data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv",
            "data/raw/zone-specific-demand/MISO/x.csv",
            "data/raw/load-forecast/spp/spp.csv",
            "data/raw/load-forecast/miso/miso.csv",
            "data/raw/lmp-data/DAMLZHBSPP_2023.zip",
            "data/raw/lmp-data/ERCOT/x.csv",
        ]
        splits = hydrate_data.split_dirs(paths, isos)
        assert {"zone-specific-demand", "load-forecast", "lmp-data"} <= splits
        assert hydrate_data.owner_of(paths[0], isos, splits) == "SPP"
        assert hydrate_data.owner_of(paths[1], isos, splits) == "MISO"
        assert hydrate_data.owner_of(paths[2], isos, splits) == "SPP"
        assert hydrate_data.owner_of(paths[3], isos, splits) == "MISO"
        # ...and the ERCOT zip is still not SPP's.
        assert hydrate_data.owner_of(paths[4], isos, splits) != "SPP"

    @pytest.mark.parametrize("name", ["SOCO", "soco"])
    def test_soco_split_children_resolve_by_whole_name_and_by_token(self, isos, name):
        """SOCO (registered 2026-09-14, SOCO-20) needs no delimiter bounding:
        the bare `soco` token matches its split children AND the whole-name
        limb agrees, so no attribution moves between the two."""
        assert hydrate_data.iso_for_split_child(name, isos) == "SOCO"
        assert hydrate_data.iso_for_name(name, isos) == "SOCO"

    def test_no_six_iso_attribution_moves_on_the_real_tree(self, isos):
        """Nothing but SPP changes owner: the limb is additive over HEAD.

        Reads trees only (``raw_entries`` is ``ls-tree``), so it is safe in a
        blobless partial clone — see the ``hydrate_data`` module docstring.
        """
        paths = [p for _, p in hydrate_data.raw_entries()]
        if not paths:
            pytest.skip("no data/raw at HEAD")
        splits = hydrate_data.split_dirs(paths, isos)
        moved = {}
        for path in paths:
            seg = path.split("/")
            if len(seg) < 4 or seg[2] not in splits:
                continue
            after = hydrate_data.iso_for_split_child(seg[3], isos)
            before = hydrate_data.iso_for_name(seg[3], isos)
            if after != before:
                moved.setdefault((before, after), set()).add(seg[2] + "/" + seg[3])
        assert all(after == "SPP" for (_, after) in moved), moved


class TestNwppTokens:
    """NWPP (lane NWPP-20, 2026-09-14): the worst token trap yet measured.

    Bare ``ava`` / ``grid`` / ``pge`` / ``wpp`` / ``scl`` would each steal other
    regions' files (plan §7 gate G3, re-measured at the lane's base sha), so
    every one of those five is claimed only through its delimiter-bounded
    EIA-930 file form; the pool name and the other twelve BA codes are clean.
    """

    REFUSED_BARE = ("ava", "grid", "pge", "wpp", "scl")

    def test_nwpp_profile_and_tokens_exist(self, isos):
        manifest = hydrate_data.load_manifest()
        assert "NWPP" in isos and isos["NWPP"]["tokens"]
        assert manifest["profiles"]["nwpp"]["iso"] == "NWPP"
        tokens = {t.lower() for t in isos["NWPP"]["tokens"]}
        for bare in self.REFUSED_BARE:
            assert bare not in tokens, bare

    @pytest.mark.parametrize(
        "name",
        [
            "BPAT hourly.parquet",
            "NEVP interchange hourly.parquet",
            "AVA hourly.parquet",
            "GRID interchange hourly.parquet",
            "PGE hourly.parquet",
            "SCL hourly.parquet",
            "nwpp-weim",
            "nwpp-hydro",
            "nwpp-planning",
            "SOURCES_nwpp_gas.md",
        ],
    )
    def test_nwpp_files_are_nwpp_owned(self, isos, name):
        assert hydrate_data.iso_for_name(name, isos) == "NWPP"

    @pytest.mark.parametrize(
        "name",
        [
            "ercot-nuclear-availability.csv",  # bare `ava`
            "nuclear-availability-CAISO.csv",  # bare `ava`
            "fleet-egrid",  # bare `grid`
            "egrid_family_heat_rates_NYISO.csv",  # bare `grid`
            "pge-helms-ps-plant-2008",  # bare `pge` (CAISO's Helms record)
            "SWPP_fueltype.parquet",  # bare `wpp` (SPP's file)
            "2_DAY_SCED_AS_DISCLOSURE_2day_Agg_SCED_AS_Offers_NSPIN_2026.parquet",  # `scl`
        ],
    )
    def test_the_trap_names_are_never_nwpp_owned(self, isos, name):
        assert hydrate_data.iso_for_name(name, isos) != "NWPP"

    def test_split_child_whole_name_resolves(self, isos):
        assert hydrate_data.iso_for_split_child("nwpp", isos) == "NWPP"
        assert hydrate_data.iso_for_split_child("NWPP", isos) == "NWPP"
