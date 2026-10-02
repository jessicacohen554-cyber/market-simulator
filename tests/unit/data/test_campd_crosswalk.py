"""W0 Q7: every hand CEMS->EIA remap is confirmed by the crosswalk of record or cited."""

from __future__ import annotations

from market_sim.data.campd_crosswalk import (
    CAMPD_REMAP_OVERRIDE_CITATIONS,
    classify_remap_rows,
)


def test_every_remap_row_is_confirmed_or_a_cited_override():
    rows = classify_remap_rows()
    assert not rows.empty
    bad = rows[(rows["status"] != "confirmed") & ~rows["cited_override"]]
    assert bad.empty, bad.to_string()


def test_a_contradicted_row_is_never_silently_kept():
    rows = classify_remap_rows({(3, "1"): 999999})  # Barry unit 1 -> wrong plant
    assert rows.iloc[0]["status"] == "contradicted"
    assert not rows.iloc[0]["cited_override"]


def test_citations_name_their_record():
    assert all(len(v) > 40 for v in CAMPD_REMAP_OVERRIDE_CITATIONS.values())
