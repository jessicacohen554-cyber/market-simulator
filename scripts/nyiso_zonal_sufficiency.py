"""NYISO zonal-sufficiency test — zone-spread duration curves (doc-07 DD1).

Design decision 1 of the NYISO prompt pack (doc 07, prompt P10 step 2) asks
whether NYISO must be modelled with its downstate split (the 5-zone topology)
or whether a single copper-plate price is good enough. The evidence is the
**congestion between the model zones**: if the day-ahead zonal LBMPs rarely
diverge one system price suffices; if they part by tens of $/MWh for a
meaningful share of hours the topology carries real information a single zone
would miss — which for NYISO is the persistent upstate-cheap / downstate-dear
separation across the UPNY-SENY and Long Island interfaces.

The model zones come from ``scripts/data/derive_actual_lmp.py`` (the simple mean of
each model zone's constituent NYISO internal zones), so the three reported
spreads are the prompt's J−A / K−A / F−A in model-zone terms:

  * ``J-A``  NYC − Upstate_West       (zone J vs the upstate zone)
  * ``K-A``  Long_Island − Upstate_West
  * ``F-A``  Capital_Hudson − Upstate_West

For each, per year: the signed mean (which zone is dear), the |spread|
duration-curve percentiles p50/p90/p99, and the share of hours the absolute
spread exceeds $5 and $20, plus where the > $20 hours concentrate (season /
hour-of-day). Day-ahead by default (the cleaner hourly congestion signal,
matching ``caiso_zonal_sufficiency.py``); ``--kind rt`` for real-time.

Usage:
    python scripts/nyiso_zonal_sufficiency.py [--years 2023 2024 2025]
                                              [--kind da|rt] [--md]
"""

from __future__ import annotations

import argparse
import sys

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
# derive_actual_lmp lives in scripts/data/ since the 2026-07-18 reorg; add it so
# the sibling import below resolves when the script is run directly.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))

from scripts.lib.zonal_sufficiency import (  # noqa: E402
    analyze,
    render_concentration,
    render_table,
)
from derive_actual_lmp import nyiso_zone_hourly  # noqa: E402

# (zone_a, zone_b, label) — the prompt's J−A / K−A / Capital−A spreads in
# model-zone terms (Upstate_West is zone A's aggregate).
PAIRS = (
    ("NYC", "Upstate_West", "J-A"),
    ("Long_Island", "Upstate_West", "K-A"),
    ("Capital_Hudson", "Upstate_West", "F-A"),
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--kind", choices=("da", "rt"), default="da")
    ap.add_argument(
        "--md", action="store_true", help="emit a markdown table (for the adequacy doc)"
    )
    args = ap.parse_args()
    stats, conc = analyze(nyiso_zone_hourly, args.years, PAIRS, args.kind)
    if stats:
        print(render_table(stats, args.md))
        print()
        print(render_concentration(conc))


if __name__ == "__main__":
    main()
