"""R-CAISO-8 (ZERO LP): the 2021 corridor census, before vs after the partial-year hub.

Reuses ``_rcaiso7_dsw_import_census.census_year`` unchanged on two bundles:
the R-CAISO-6 2021 leg (shard commit ``e419162a``, the fold as registered) and
the R-CAISO-8 2021 leg (``results/calibration/rcaiso8_A_2021``, shard commit
``2b93619a``). Writes ``results/calibration/_rcaiso8/object1_2021_corridors.json``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso8_2021_corridor_census.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [".", "src", "scripts", "scripts/probes"]
from _rcaiso7_dsw_import_census import _extract, census_year  # noqa: E402
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

NEW = Path("results/calibration/rcaiso8_A_2021")
OUT = Path("results/calibration/_rcaiso8/object1_2021_corridors.json")


def main() -> None:
    """Census 2021 on the fold leg and the R-CAISO-8 leg; write both."""
    meas = corridor_net_import(years=(2021,))
    with tempfile.TemporaryDirectory() as tmp:
        before = census_year(_extract(Path(tmp), 2021), 2021, meas)
    after = census_year(NEW, 2021, meas)
    res = {"fold_rcaiso6": before, "rcaiso8": after}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    for k, r in res.items():
        print(k, json.dumps(r["corridors"], default=float), json.dumps(r["sd_pocket"], default=float))
        print("  first-order add", r["first_order_add_twh_total"])


if __name__ == "__main__":
    main()
