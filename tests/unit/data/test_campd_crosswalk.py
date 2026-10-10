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


def test_camd_to_eia_plant_resolution_order():
    """Remap first, then the unanimous unit grain, then the facility grain, else the id."""
    import numpy as np
    import pandas as pd

    from market_sim.data.campd_crosswalk import camd_to_eia_plant

    cw = pd.DataFrame(
        [
            (10, "A", 110, "epa"),  # unit grain, unanimous
            (10, "A", 110, "pudl"),
            (10, "B", 10, "epa"),
            (20, "X", 220, "epa"),  # facility grain (every row of 20 -> 220)
            (30, "Q", 9, "epa"),  # disagreement naming the shared code: keep 30
            (30, "Q", 30, "pudl"),
            (40, "R", 1, "epa"),  # disagreement not naming it: falls to facility,
            (40, "R", 2, "pudl"),  # which is ambiguous too: keep 40
        ],
        columns=["camd_plant", "camd_unit", "eia_plant", "source"],
    )
    fac = np.array([10, 10, 20, 30, 40, 50, 60])
    uid = np.array(["A", "B", "Z", "Q", "R", "S", "T"])
    got = camd_to_eia_plant(fac, uid, cw, remap={(60, "T"): 660, (10, "B"): 555})
    assert got.tolist() == [110, 555, 220, 30, 40, 50, 660]
