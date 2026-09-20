"""nyiso-242 addendum — the reserve channel's own measured CEILING, and it is short in EVERY window.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). This probe exists to correct a
recommendation this session published and then refuted: that the **2025 summer
cluster** was "the one window price formation could actually reach".

That recommendation rested on a REACHABILITY measure — 2025's summer missed
hours carry only 899 MW of idle sub-gate capacity at 94.9 % fleet utilisation,
so the LP sits near the top of its own stack. That is true and it is the wrong
question on its own. It says the LP could clear HIGHER; it says nothing about
whether the top of the stack is anywhere near the price the market actually
made. Those are different questions and conflating them is the error.

**THE BOUND.** ``score_price_tail`` scores the SETTLEMENT price — energy LMP
plus the published reserve/scarcity overlay (G-20a) — so the reserve channel's
contribution is capped by what NYISO's reserve market ever pays. nyiso-115
measured that on NYISO's **own posted zonal Day-Ahead ancillary-service prices**
(``data/raw/NYISO-AS/NYISO_as_da_<year>.csv``, probe
``_nyiso115_nyc_rcpf_curve_screen.py``), by differencing nested regions
(NYCA ⊃ East ⊃ SENY ⊃ NYC) to isolate each region's own adder:

* **NYC** — never exceeds **$25.00** in 26,301 hours of 2023–2025; the 10-minute
  product stacks to exactly **$50.00** in precisely the hours the 30-minute one
  sits at $25.00 (5/5, 16/16, 98/98), since a 10-minute reserve also satisfies
  the 30-minute requirement.
* **SENY** — caps at exactly **$40**, never its modelled $500.
* **East** — isolated adder max **$27 / $36 / $46**, never approaching its
  modelled $775.
* **Long Island** — no material adder in any hour of any year.

So the largest locational stack a NYISO zone can ever collect is
**$50 + $40 + $46 = $136/MWh**. Granting the model that entire stack in every
missed hour is a deliberate over-grant: it is the measured maximum, applied
universally, on top of the model's own energy dual.

If the model is STILL short of the actual price under that over-grant, the
reserve channel cannot close the gap — not by better curves, not by step
functions instead of ramps, not by a steeper ORDC. That is the question this
probe answers, and it answers it for every window rather than only the one that
happened to look reachable.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso242_reserve_ceiling_bound.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
HUB = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
THRESHOLD = 300.0
#: Per-region maxima NYISO's OWN posted DA AS prices ever reach (nyiso-115,
#: transcribed in model/reserves/spec.py:504-524). NOT the modelled RCPF
#: penalties ($500 SENY / $775 East), which the measured market never pays.
NYC_STACK, SENY_MAX, EAST_MAX = 50.0, 40.0, 46.0
CEILING_STACK = NYC_STACK + SENY_MAX + EAST_MAX


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023, 2024, 2025])
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "_nyiso242_reserve_ceiling_bound.json"),
    )
    args = ap.parse_args()

    hub = pd.read_parquet(HUB)
    out: dict = {
        "measured_region_maxima": {
            "nyc_10min_plus_30min": NYC_STACK,
            "seny": SENY_MAX,
            "east": EAST_MAX,
            "long_island": 0.0,
        },
        "ceiling_stack_usd_mwh": CEILING_STACK,
        "source": "nyiso-115, NYISO's own posted zonal DA AS prices; spec.py:504-524",
        "years": {},
    }
    print(f"measured max locational reserve stack anywhere in NYISO: ${CEILING_STACK:.0f}/MWh\n")
    print(
        f"{'year / window':24s}{'n':>5}{'energy dual':>13}{'+resv now':>11}"
        f"{'+CEILING':>10}{'actual':>9}{'STILL SHORT':>13}"
    )
    for year in args.years:
        s = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
        s = s[(s["pass"] == "P1") & (s["zone"] != "NYISO_external")]
        mx = s.pivot_table(index="hour", columns="zone", values="price").max(axis=1).to_numpy()
        rp = (
            s.pivot_table(index="hour", columns="zone", values="reserve_price")
            .max(axis=1)
            .to_numpy()
        )
        h = hub[hub["year"] == year].sort_values("hour")["rt"].to_numpy()
        n = min(len(mx), len(h))
        mx, rp, h = mx[:n], rp[:n], h[:n]
        month = pd.date_range(f"{year}-01-01", periods=n, freq="h").month.to_numpy()
        miss = (h > THRESHOLD) & (mx <= THRESHOLD)
        rec: dict = {}
        for lbl, sel in (
            ("all_missed", miss),
            ("winter", miss & np.isin(month, (1, 2, 12))),
            ("summer", miss & np.isin(month, (6, 7, 8))),
        ):
            if not sel.any():
                continue
            energy = float(np.median(mx[sel]))
            with_now = float(np.median(mx[sel] + rp[sel]))
            with_ceiling = float(np.median(mx[sel] + CEILING_STACK))
            actual = float(np.median(h[sel]))
            rec[lbl] = {
                "hours": int(sel.sum()),
                "energy_dual_median": round(energy, 1),
                "plus_reserve_as_modelled": round(with_now, 1),
                "plus_measured_ceiling": round(with_ceiling, 1),
                "actual_median": round(actual, 1),
                "still_short_usd_mwh": round(actual - with_ceiling, 1),
                "ceiling_closes_gap": bool(with_ceiling >= actual),
            }
            print(
                f"{str(year) + ' ' + lbl:24s}{sel.sum():5d}{energy:13.1f}{with_now:11.1f}"
                f"{with_ceiling:10.1f}{actual:9.1f}{actual - with_ceiling:13.1f}"
            )
        out["years"][str(year)] = rec

    print(
        "\n'+CEILING' grants the model the LARGEST locational reserve stack NYISO's own posted"
        "\nAS market has ever paid, in every hour. It is an upper bound on the channel, never a"
        "\nproposal. Where 'STILL SHORT' is positive the reserve channel cannot close the gap."
    )
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
