"""Derive NWPP's per-fuel-family annual plant-basis energy (EIA-923 basis).

Writes ``data/raw/reference/nwpp_plant_basis_energy.csv`` — one row per
``(year, family)`` — the annual energy the ``nwpp_demand_plant_basis`` served
schedule anchors each EIA-930 fuel family to (owner ruling on
``FINDING-nwpp-45`` §8 = framing 2, session NWPP-NEXT-3, 2026-09-25: *anchor the
demand construction to the same plant basis C1 scores on — EIA-930 hourly shape,
EIA-923 plant energy*).

Source: the committed NWPP benchmark parts
``frontend/data/backcast/bench/NWPP/<year>.json.gz``, field ``bench.classFull`` —
the grid-delivered EIA-923 per-class plant totals of the footprint's plants
(BTM subtracted, CAMPD-backfilled, variable renewables on the EIA-930 grid
series), which is flag-independent by construction
(``render_calibration_html``: "the shared part is stable across runs").
Each class maps to exactly one EIA-930 fuel family (:data:`CLASS_FAMILY`); an
unmapped class FAILS (it would otherwise silently drop out of the anchor).
On a preliminary EIA-923 vintage only the repaired fossil families are
written (:data:`PRELIMINARY_VINTAGE_FAMILIES`); an absent family is left on
EIA-930 by the anchor.

Frozen against residuals (rule 23 ``[R-FROZEN-DERIVE]``): re-run only when a
bench part's SOURCE data changes, and cite that change in the commit. The CSV
records each part's sha256 so a drift is visible.

Run: ``python3 scripts/data/derive_nwpp_plant_basis_energy.py``
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia930.envelopes import (  # noqa: E402
    NWPP_PLANT_BASIS_CLASS_FAMILY as CLASS_FAMILY,
)
from market_sim.data.eia930.envelopes import (  # noqa: E402
    NWPP_PLANT_BASIS_ENERGY_PATH,
)

BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench" / "NWPP"
COMPLETENESS_DIR = REPO / "frontend" / "data" / "backcast" / "completeness"

# On a PRELIMINARY EIA-923 vintage (a year with a committed completeness part,
# written by scripts/audit_eia923_completeness.py) the benchmark repairs only
# the audited fossil families (render_calibration_html.reconcile_vintage_classes
# and the CEMS anchor); every other class is the raw, incomplete preliminary
# survey (NWPP 2025 OTHER+biomass+oil 4.27 TWh against 8.17-8.85 in every
# complete year). Only these families are therefore a plant basis on such a
# year; the rest are omitted, which leaves them on EIA-930 (rule 14).
PRELIMINARY_VINTAGE_FAMILIES: frozenset[str] = frozenset({"COL", "NG"})


def is_preliminary(year: int) -> bool:
    """Whether ``year``'s EIA-923 vintage is preliminary (a completeness part exists)."""
    return (COMPLETENESS_DIR / f"eia923_{int(year)}.json").exists()


def derive() -> list[dict]:
    """Return the ``(year, family, twh, source, source_sha256)`` rows."""
    rows: list[dict] = []
    for part in sorted(BENCH_DIR.glob("[0-9][0-9][0-9][0-9].json.gz")):
        year = int(part.name[:4])
        raw = part.read_bytes()
        class_full = json.loads(gzip.decompress(raw))["bench"]["classFull"]
        unmapped = sorted(set(class_full) - set(CLASS_FAMILY))
        if unmapped:
            raise ValueError(
                f"NWPP {year}: classFull classes with no family {unmapped}"
            )
        totals: dict[str, float] = {}
        for klass, twh in class_full.items():
            fam = CLASS_FAMILY[klass]
            totals[fam] = totals.get(fam, 0.0) + float(twh)
        sha = hashlib.sha256(raw).hexdigest()
        prelim = is_preliminary(year)
        for fam in sorted(totals):
            if prelim and fam not in PRELIMINARY_VINTAGE_FAMILIES:
                continue
            rows.append(
                {
                    "year": year,
                    "family": fam,
                    "twh": f"{totals[fam]:.4f}",
                    "source": f"frontend/data/backcast/bench/NWPP/{part.name}:bench.classFull",
                    "source_sha256": sha,
                }
            )
    return rows


def main() -> None:
    """Write the CSV and print the per-year totals."""
    rows = derive()
    NWPP_PLANT_BASIS_ENERGY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NWPP_PLANT_BASIS_ENERGY_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["year", "family", "twh", "source", "source_sha256"]
        )
        w.writeheader()
        w.writerows(rows)
    by_year: dict[int, float] = {}
    for r in rows:
        by_year[r["year"]] = by_year.get(r["year"], 0.0) + float(r["twh"])
    for y, t in sorted(by_year.items()):
        print(f"{y}: {t:.3f} TWh")
    print(f"wrote {NWPP_PLANT_BASIS_ENERGY_PATH.relative_to(REPO)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
