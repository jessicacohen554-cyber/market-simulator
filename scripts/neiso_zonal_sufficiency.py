"""NEISO zonal-sufficiency test — zone-vs-hub spread duration curves (doc-08).

The design decision of the NEISO prompt pack (doc 08, prompt P10 step 2) asks
whether ISO-NE must be modelled with its load-pocket split (the 4-zone
topology) or whether a single copper-plate price is good enough. The evidence
is the **congestion between each load pocket and the system hub**: if the
day-ahead zonal LMPs track the .H.INTERNAL_HUB one system price suffices; if
they part by tens of $/MWh for a meaningful share of hours the topology
carries real information — for ISO-NE the Boston / SE-Mass import pockets and
the export-constrained Maine corner under summer peak. (Winter system-wide gas
spikes lift *all* zones together — a level effect, not a spread.)

The model zones come from ``scripts/data/derive_actual_lmp.py`` (the simple mean of
each model zone's constituent SMD load-zone sheets) and the hub is the
.H.INTERNAL_HUB ("ISO NE CA" sheet). The three reported spreads are the
prompt's Boston−Hub / CT−Hub / ME−Hub:

  * ``Boston-Hub``        Boston (NEMASSBOST) − hub
  * ``Connecticut-Hub``   Connecticut − hub
  * ``North-Hub``         North (ME/NH/VT, the Maine-led northern zone) − hub

For each, per year: the signed mean (pocket dear vs hub), the |spread|
duration-curve percentiles p50/p90/p99, the share of hours the absolute spread
exceeds $5 and $20, and where the > $20 hours concentrate (season /
hour-of-day). Day-ahead by default; ``--kind rt`` for real-time.

Usage:
    python scripts/neiso_zonal_sufficiency.py [--years 2023 2024 2025]
                                              [--kind da|rt] [--md]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# derive_actual_lmp lives in scripts/data/ since the 2026-07-18 reorg; this
# script is run directly (python scripts/<iso>_zonal_sufficiency.py), so only
# its own directory is on sys.path by default.
sys.path.insert(0, str(Path(__file__).resolve().parent / "data"))

from lib.zonal_sufficiency import analyze, render_concentration, render_table
from derive_actual_lmp import neiso_zone_hourly

# (zone_a, zone_b, label) — the prompt's Boston−Hub / CT−Hub / ME−Hub spreads.
# ME is the Maine-led North model zone (ME/NH/VT); the northern separation is
# the export-constrained Maine corner.
PAIRS = (
    ("Boston", "hub", "Boston-Hub"),
    ("Connecticut", "hub", "Connecticut-Hub"),
    ("North", "hub", "North-Hub"),
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--kind", choices=("da", "rt"), default="da")
    ap.add_argument(
        "--md", action="store_true", help="emit a markdown table (for the adequacy doc)"
    )
    args = ap.parse_args()
    stats, conc = analyze(neiso_zone_hourly, args.years, PAIRS, args.kind)
    if stats:
        print(render_table(stats, args.md))
        print()
        print(render_concentration(conc))


if __name__ == "__main__":
    main()
