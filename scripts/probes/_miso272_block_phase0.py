#!/usr/bin/env python3
"""miso-272 phase 0 (zero LP): what the keeper carries at the seven block-on-one-row plants.

Fleet-only rebuild (``run_year(fleet_only=True)``) of the designated MISO keeper
recipe (``results/calibration/miso271_span``) via the miso-271 decomposition
helpers, re-pointed at that keeper. Per year, per plant in :data:`BLOCK_PLANTS`
(the census of ``docs/PRECOMMIT-miso272-*.md`` §2: an EIA-860 CA row whose summer
rating exceeds its own nameplate while every CT sibling's summer is blank), it
reports carried pmax, class and available energy, beside the plant's reported
EIA-860 summer total. Also dumps the full unit frame per (year, variant) for the
coal WEFOR-stack decomposition.

Usage::

    uv run python scripts/probes/_miso272_block_phase0.py --years 2019 2023 --out-dir X
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import _miso271_cc_decomp as dec  # noqa: E402

dec.KEEPER = REPO / "results/calibration/miso271_span"
BLOCK_PLANTS = (1004, 55218, 55220, 55380, 55418, 55467, 55620)
COAL = ["COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC"]
VARIANTS = {
    "B": {},
    # statistical WEFOR retired on coal too (the candidate-2 upper bound)
    "noWc": {"wefor_residual": 0.0, "wefor_residual_groups": ["CC_REGULAR", "ST_CHP", "ST_GAS", *COAL]},
    # every CAMPD overlay off (what the measured windows remove)
    "noO": {"outage_source": "statistical"},
    # short-coal windows off
    "noSc": {"unit_outage_short_windows": False},
    # the miso-272 arm: CC blocks rated on one row reconciled
    "BLK": {"cc_block_summer_rating": True},
}


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2023])
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    ref = _load_reference()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for y in args.years:
        hh = _henry_hub_actual(ref, y)
        for v in args.variants:
            df, _ = dec.unit_frame(y, hh, VARIANTS[v])
            df.to_parquet(out / f"{y}_{v}.parquet", index=False)
            if v in ("B", "BLK"):
                blk = df[df.plant_code.isin(BLOCK_PLANTS)]
                rows = (
                    blk.groupby(["plant_code", "group"])
                    .agg(pmax=("pmax", "sum"), avail_twh=("avail_mwh", lambda s: s.sum() / 1e6), n=("unit_id", "size"))
                    .round(3)
                    .reset_index()
                )
                print(json.dumps({"year": y, "variant": v, "block_plants": rows.to_dict("records")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
