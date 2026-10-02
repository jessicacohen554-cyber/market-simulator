"""W0 E.8 / E.6: BA membership is decided at LOAD time, never at derive time."""

from __future__ import annotations

import pandas as pd

from market_sim.data.fleet import models
from market_sim.data.fleet.models import (
    generator_footprint_mask,
    program_footprint_mask,
)


def _frame():
    return pd.DataFrame(
        {
            "plant_id": [1, 2, 3, 4],
            "balancing_authority_code": ["MISO", "FPL", "DOPD", "BPAT"],
            "nerc_region": ["MRO", "SERC", "TRE", "WECC"],
        }
    )


def test_unregistered_ba_rows_do_not_leak_into_a_region():
    df = _frame()
    assert df[generator_footprint_mask("MISO", df)]["plant_id"].tolist() == [1]


def test_nwpp_nerc_key_applies_at_load_time():
    df = _frame()
    # DOPD is an NWPP member code, but plant 3 sits in TRE: out at load time.
    nwpp = df[generator_footprint_mask("NWPP", df)]["plant_id"].tolist()
    assert 3 not in nwpp and 4 in nwpp


def test_legacy_table_without_nerc_column_is_exact_on_ba():
    df = _frame().drop(columns="nerc_region")
    assert 3 in df[generator_footprint_mask("NWPP", df)]["plant_id"].tolist()


def test_registering_a_ba_needs_no_regeneration(monkeypatch):
    df = _frame()
    monkeypatch.setitem(models.ISO_TO_BA_CODES, "SOCO", ("SOCO", "FPL"))
    assert df[generator_footprint_mask("SOCO", df)]["plant_id"].tolist() == [2]


def test_program_mask_is_the_derive_time_predicate():
    df = _frame()
    assert df[program_footprint_mask(df)]["plant_id"].tolist() == [1, 4]
