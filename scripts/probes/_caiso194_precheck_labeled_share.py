"""caiso-194 PRECHECK probe: the G-SHARE labeled-subset anchor, computed pre-measurement.

GATESPEC-caiso194-hydro-ror-split-2026-08-11 §3 G-SHARE requires the
capacity-weighted NON-SHAPEABLE share of the EHA ``Mode``-LABELED subset to be
computed and committed BEFORE the completion rules (curator rules 2-5) run on
the unlabeled remainder. This probe computes exactly that anchor and nothing
else: it applies ONLY curator rule 1 (the published EHA ``Mode`` label), so no
completion rule and no model residual can reach the number it prints.

Deliberately NOT computed here: any classification of the Mode-NaN remainder.
Reading that before the anchor is committed is the ordering violation the gate
exists to prevent.

Also reports the G-COVER denominator (CAISO conventional-hydro nameplate on the
model's own EIA-860 fleet basis) so the coverage arithmetic is pre-registered
against a fixed denominator rather than one chosen after the partition exists.

Usage:
  PYTHONPATH=.:src uv run python scripts/probes/_caiso194_precheck_labeled_share.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from scripts.data.curate_hydro_plant_modes import (  # noqa: E402
    EHA_XLSX,
    MODE_SHAPEABLE,
    _load_eha,
)

BA_CODE = "CISO"


def labeled_subset_share(raw_root: Path) -> dict:
    """Return the capacity-weighted non-shapeable share of the LABELED subset.

    Applies curator rule 1 only. Aggregated to the EIA plant-id grain the
    curator writes, so the anchor and the full-population measurement it gates
    are the same statistic on the same grain.
    """
    eha = _load_eha(raw_root, BA_CODE)
    eha["plant_id"] = eha["EIA_PtID"].astype(int)

    labeled = eha[eha["Mode"].isin(MODE_SHAPEABLE)].copy()
    labeled["shapeable"] = labeled["Mode"].map(MODE_SHAPEABLE).astype(bool)

    # Same EIA plant-id aggregation as the curator: shapeable if ANY
    # constituent EHA plant is; capacities sum.
    rows = (
        labeled.groupby("plant_id")
        .agg(ch_mw=("CH_MW", "sum"), shapeable=("shapeable", "any"))
        .reset_index()
    )
    total_mw = float(rows["ch_mw"].sum())
    nonshapeable_mw = float(rows.loc[~rows["shapeable"], "ch_mw"].sum())

    return {
        "ba_code": BA_CODE,
        "source": EHA_XLSX,
        "eha_rows_ciso_conventional": int(len(eha)),
        "eha_rows_mode_labeled": int(len(labeled)),
        "eha_rows_mode_unlabeled": int(len(eha) - len(labeled)),
        "labeled_plants_eia_grain": int(len(rows)),
        "labeled_total_ch_mw": round(total_mw, 3),
        "labeled_nonshapeable_ch_mw": round(nonshapeable_mw, 3),
        "labeled_nonshapeable_share_pct": round(100.0 * nonshapeable_mw / total_mw, 4),
        "mode_value_counts": {
            str(k): int(v) for k, v in eha["Mode"].value_counts(dropna=False).items()
        },
    }


def cover_denominator() -> dict:
    """Return the G-COVER denominator: the model's own EIA-860 hydro fleet basis.

    Uses the same loader the dispatch path uses
    (:func:`market_sim.data.hydro._load_hydro_nameplate`) — conventional hydro
    (prime mover ``HY``) in BA ``CISO``, pumped storage excluded — so the
    coverage denominator is fixed to the fleet the mechanism actually acts on,
    before the partition that would be measured against it exists.
    """
    from market_sim.data.hydro import _load_hydro_nameplate

    nameplate = _load_hydro_nameplate("CAISO")
    total = float(sum(nameplate.values()))
    return {
        "basis": "EIA-860 generator parquet, prime_mover=HY, BA=CISO, PS excluded",
        "plants": int(len(nameplate)),
        "nameplate_mw": round(total, 3),
        "gcover_bar_90pct_mw": round(0.9 * total, 3),
    }


def main() -> int:
    """CLI entry point."""
    raw_root = paths.RAW_DIR
    anchor = labeled_subset_share(raw_root)
    anchor["gcover_denominator"] = cover_denominator()
    print(json.dumps(anchor, indent=2, sort_keys=True))
    share = anchor["labeled_nonshapeable_share_pct"]
    print(
        f"\nG-SHARE ANCHOR (labeled subset, capacity-weighted non-shapeable): "
        f"{share:.4f} %"
    )
    print(f"G-SHARE admissible band for the full population: {share - 10:.4f} % .. {share + 10:.4f} %")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
