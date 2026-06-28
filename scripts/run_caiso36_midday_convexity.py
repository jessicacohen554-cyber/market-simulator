"""Driver: CAISO 36 — fix the reference-seam midday price-body over-price, 2023-25.

Builds on caiso 35 (caiso35_reference_seam) with NO new flags — the fix is
entirely in the seam's price SHAPE (config/constants.py INTERFACE_NEIGHBORS
["CAISO"] + data/neighbor_price.py), so every run lever is carried verbatim.

Why (caiso 35 residuals):

  caiso 35 got interchange volume right and is forward-native, but it regressed
  the CAISO price body badly: CA-zone avg LMP 100/63/69 vs actual 44/33/34
  (+128/+90/+104%), with 744 h >$200 in 2023 vs 21 actual. The real Palo Verde /
  Malin hub LMP crashes midday in the desert-SW solar glut (goes toward / through
  zero); caiso 35's reference price = (HH+basis)×HR×(net_load/mean)^1.0 floored at
  +5% of mean was too SMOOTH — it never crashed midday, so the body and annual
  mean inflated. Two compounding issues: (1) the DSW exponent 1.0 was too shallow
  and the +5% floor stopped the trough going low; (2) the 2023 hr_by_year anchors
  were inflated by partial OASIS coverage (~7,056 h, Jan–Feb aged out).

The caiso 36 fix (forward-native, responds to forward solar — NOT a fit):

  * DSW load_shape_exponent 1.0 → 2.5 — the convexity that reproduces the deep
    measured Palo-Verde midday crash (a price-vs-tightness convexity, blind to
    CAISO's flow; rule #11).
  * PNW load_shape_kind gross → net, exponent → 1.5 — the Malin/COI price is
    depressed midday by CA solar flooding the interface northbound, which a
    gross-load shape cannot reproduce (it held PNW midday at ~$40 vs measured
    ~$25-34). Net-load shaping captures the solar dip.
  * Midday floor lowered to a small negative (CAISO_NET_SHAPE_FLOOR_FRAC) with a
    sign-preserving power, so the deepest solar hours price slightly below zero
    (the desert-SW paying CAISO to absorb its surplus).
  * 2023 hr_by_year dropped (partial coverage) → falls back to marginal_heat_rate
    (the full-coverage 2024/25 gas-normalized ratio), cutting the 2023 over-price
    and scarcity-hour count.

  HR anchors re-derived AFTER the exponent/kind change (the K-factor moves):
  scripts/derive_caiso_seam_hr_by_year.py
    WECC_DSW (net, exp 2.5): hr_by_year 2024:10.57 / 2025:6.71, struct 8.64
    WECC_PNW (net, exp 1.5): hr_by_year 2024:20.08 / 2025:11.17, struct 15.62

  The CARB border carbon on the import leg is REAL and retained — the over-price
  was the missing midday SHAPE, not the carbon. All caiso 35 levers verbatim.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)


def main() -> int:
    out_dir = Path("results/calibration/caiso36_midday_convexity")
    reference = _load_reference()
    run_dir = solve_and_persist(
        [2023, 2024, 2025],
        "CAISO",
        8760,
        reference,
        commitment=False,
        screen_coal=True,
        run_dir=out_dir,
        outage_source="historic",
        # caiso 34/35 coal recipe (minimal CAISO coal, carried verbatim).
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        priced_interchange=True,
        # Reference-price seam (forward-native), carried verbatim from caiso 35.
        # The caiso 36 fix is entirely in the seam SHAPE (INTERFACE_NEIGHBORS
        # ["CAISO"] convexity + the net-load midday floor), so no flag changes.
        caiso_reference_price_seam=True,
        caiso_per_hub_intertie=False,
        caiso_corridor_atc_forward=True,
        note=(
            "caiso 36 midday-convexity fix: deepen the WECC reference-seam price "
            "shape so it crashes midday like the real Palo-Verde / Malin hubs, "
            "fixing the caiso 35 body over-price (CA-zone LMP +90-128%). DSW "
            "net-load exponent 1.0->2.5; PNW gross->net exp 1.5 (Malin is "
            "solar-depressed midday by CA northbound flow); midday floor lowered "
            "to a small negative so the deepest solar hours price below zero; "
            "2023 hr_by_year dropped (partial OASIS coverage) -> falls back to "
            "the full-coverage 2024/25 ratio. HR re-derived after the exponent "
            "change (derive_caiso_seam_hr_by_year.py): DSW 2024:10.57/2025:6.71 "
            "struct 8.64; PNW 2024:20.08/2025:11.17 struct 15.62. CARB border "
            "carbon retained. All other caiso 35 levers verbatim."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
