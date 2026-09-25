"""Build the ``-memberrepair-`` companion of an ISO's standard CAMPD outage extract.

PJM-NEXT-2 (rule 14 [R-ACCURATE]). The committed standard extract
(``data/raw/campd-unit-outages-<ISO>.csv``) was derived against one fleet
membership, so a facility outside it was never scanned and carries no window in
any year. This builder writes the companion consumed under
``ScenarioConfig.unit_outage_membership_repair``:

    companion = committed extract (UNCHANGED, byte-for-byte rows)
              + every row of a fresh re-derive whose facility_id has NO row
                anywhere in the committed extract.

The re-derive is the standard deriver with ``--membership-vintage-union`` (and
the COAL-SUB artifact-token membership fix), e.g.::

    python3 scripts/data/derive_campd_unit_outages.py --iso PJM \\
        --years 2018 2019 2020 2021 2022 2023 2024 2025 2026 \\
        --membership-vintage-union --out /tmp/rederive.csv
    python3 scripts/data/build_outage_membership_repair.py --iso PJM \\
        --rederive /tmp/rederive.csv

Only never-scanned facilities are added: a facility the committed extract
already carries is never re-derived here, so the extract-drift question for
existing rows (card 4) is untouched. Zero free parameters.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))


def build_companion(base: pd.DataFrame, rederive: pd.DataFrame) -> pd.DataFrame:
    """Return ``base`` plus the ``rederive`` rows of facilities absent from ``base``."""
    if list(base.columns) != list(rederive.columns):
        raise SystemExit(
            f"column mismatch: base {list(base.columns)} vs rederive "
            f"{list(rederive.columns)}"
        )
    never = set(rederive["facility_id"]) - set(base["facility_id"])
    added = rederive[rederive["facility_id"].isin(never)]
    return pd.concat([base, added], ignore_index=True)


def main() -> None:
    """CLI entry point."""
    from market_sim.data.outages import unit_outage_csv_for_iso

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--rederive", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    base_path = unit_outage_csv_for_iso(args.iso)
    out = args.out or base_path.with_name(
        f"campd-unit-outages-memberrepair-{args.iso.upper()}.csv"
    )
    base = pd.read_csv(base_path)
    rederive = pd.read_csv(args.rederive)
    comp = build_companion(base, rederive)
    comp.to_csv(out, index=False)
    added = comp.iloc[len(base) :]
    print(
        f"{out}: {len(base)} committed rows + {len(added)} added rows across "
        f"{added['facility_id'].nunique()} never-scanned facilities"
    )
    print(
        added.groupby(["facility_id", "facility_name", "plant_group"])
        .size()
        .to_string()
    )


if __name__ == "__main__":
    main()
