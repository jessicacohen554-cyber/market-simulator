"""Tests for ``derive_pjm_offer_midcurve --merge-into-existing`` (PJM-NEXT-4 card 1).

The merge path adds new delivery-year ladders to the committed surface and must
leave every existing year entry, the pooled forward ladder and the existing
provenance untouched (rule 23 `[R-FROZEN-DERIVE]`).
"""

from __future__ import annotations

import json

import pytest

from scripts.data.derive_pjm_offer_midcurve import _merge_into_existing


def _doc(years: list[str], val: float) -> dict:
    lad = [[[0.05, val], [0.95, val + 1.0]]]
    return {
        "_provenance": {
            "source": f"years {years}",
            "segment_units": {"LONG_RUN": 1},
            "month_coverage": {y: {"months_expected": 12, "files": 12} for y in years},
            "n_month_files_parsed": 12 * len(years),
        },
        "LONG_RUN": {"years": {y: lad for y in years}, "pooled": lad},
    }


def test_merge_adds_year_and_keeps_existing(tmp_path):
    """A new year is inserted in order; old years, pooled and provenance survive verbatim."""
    path = tmp_path / "surface.json"
    old = _doc(["2020", "2021"], 7.0)
    path.write_text(json.dumps(old, indent=1))
    merged = _merge_into_existing(path, _doc(["2019"], 5.0), [2019])
    assert list(merged["LONG_RUN"]["years"]) == ["2019", "2020", "2021"]
    assert merged["LONG_RUN"]["years"]["2019"][0][0][1] == 5.0
    assert merged["LONG_RUN"]["pooled"] == old["LONG_RUN"]["pooled"]
    for y in ("2020", "2021"):
        assert merged["LONG_RUN"]["years"][y] == old["LONG_RUN"]["years"][y]
    prov = dict(merged["_provenance"])
    added = prov.pop("merged_year_derives")
    assert prov == old["_provenance"]
    assert added[0]["years"] == [2019]


def test_merge_refuses_existing_year(tmp_path):
    """Re-deriving a year the surface already carries is refused, never overwritten."""
    path = tmp_path / "surface.json"
    path.write_text(json.dumps(_doc(["2020"], 7.0), indent=1))
    with pytest.raises(SystemExit):
        _merge_into_existing(path, _doc(["2020"], 5.0), [2020])
