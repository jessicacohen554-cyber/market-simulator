"""CAISO daytime no-wedge — post-hoc fine-grain refinement (companion to the frozen gate).

Companion to ``derive_caiso_daytime_wedge.py`` (the pre-registered daytime
no-wedge gate, three coarse hod blocks x season). That gate showed G1 (no
wedge) PASSES in every daytime trigger-OFF cell. Two coarse-block artifacts
need a finer look before an import-lever disposition can be trusted:

DISCLOSED SEQUENCING (honesty, the caiso-86b prohibition + the caiso-93
``derive_caiso_overnight_clean_depth.py`` precedent): BOTH refinements below
were identified AFTER the coarse gate results were seen — they are NOT
pre-registered. Nothing here is a gate; every threshold in the frozen gate
(parity x1.03+4, wedge 0.428xCARB, band <=+4, CV<=0.20, LOYO<=25%) is
untouched. This script only re-slices the SAME measured spreads for
interpretation, and prints context — it changes no verdict mechanically.

  Refinement A — the afternoon_eve (hod 15-21) coarse block straddles two very
  different sub-regimes: the afternoon (hod 15-17), the tightest daytime hours
  where reality DOES sometimes price a wedge (a genuine "leave alone", rule 1),
  and the evening peak (hod 18-21), which is measured-clean but whose MODEL
  residual flips sign by season (autumn OVER-priced +7-12 per the 2026-07-16
  autumn diagnosis; non-autumn/annual UNDER-priced -5.8/-4.1/-1.2 per the
  keeper hod ladder — a clean-import lever there would OVERSHOOT). The coarse
  cell's median-PASS masks this; the split exposes it.

  Refinement B — the belly (hod 10-14) coarse block is 66-90 % caiso-87
  trigger-ON. Those trigger-ON hours are the West-wide solar-glut regime where
  the HUB ITSELF is cheap (p50 0.7-20 $/MWh) and actual clears slightly ABOVE
  the cheap hub — i.e. reality's midday floor tracks the cheap hub, and the
  battery-charge / low-hub sub-regime lives HERE, in the caiso-87 trigger-ON
  belly (off-limits to this import lane by the hard constraint; a separate
  storage charter). Only the thin trigger-OFF belly slice clears at raw-hub
  parity and is import-relevant.

All legs are the frozen committed constructions (see
``derive_caiso_daytime_wedge.py`` docstring). NO LP is run.

Usage: .venv/bin/python scripts/derive_caiso_daytime_finegrain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from derive_caiso_import_tranches import YEARS, hub_prices  # noqa: E402
from market_sim.config.constants import STATE_CARBON_PRICE_BY_ISO  # noqa: E402
from market_sim.config.interchange_config import (  # noqa: E402
    CAISO_DSW_SURPLUS_REMOTE_VOM,
    CAISO_IMPORT_DELIVERY_BASIS,
    CARB_UNSPECIFIED_IMPORT_EF,
)
from market_sim.data.fuel import socal_citygate_weekly_hourly  # noqa: E402

ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
)
HOURS = 8760
HR_CCGT = 0.37 / 0.0531
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.repeat(np.arange(1, 13), [d * 24 for d in _DAYS])
AUTUMN_MONTHS = (9, 10, 11, 12)


def _load():
    hub = hub_prices()
    act = (
        pd.read_parquet(ACTUAL_LMP)
        .set_index(["year", "hour"])
        .reindex(
            pd.MultiIndex.from_product([YEARS, range(HOURS)], names=["year", "hour"])
        )
    )
    return hub, act


def _med(mask: np.ndarray, x: np.ndarray) -> float:
    v = x[mask & np.isfinite(x)]
    return float(np.median(v)) if v.size else float("nan")


def main() -> None:
    """Print the two post-hoc fine-grain refinements (report-only, no gate)."""
    wheel_mult, wheel_add = CAISO_IMPORT_DELIVERY_BASIS["DSW_CCGT"]
    hub, act = _load()
    hod = np.arange(HOURS) % 24
    autumn = np.isin(MONTH_OF_HOUR, AUTUMN_MONTHS)

    print(
        "=== Refinement A: afternoon (15-17) vs evening peak (18-21), trigger-OFF ==="
    )
    print("   (afternoon carries real wedge; evening peak is measured-clean but model")
    print(
        "    residual flips sign by season — see the FINDING for the overshoot caveat)\n"
    )
    for label, (h0, h1) in (("afternoon_15_17", (15, 17)), ("evepeak_18_21", (18, 21))):
        blk = (hod >= h0) & (hod <= h1)
        for sn, sm in (("autumn", autumn), ("non_autumn", ~autumn)):
            print(f"  {label} x {sn}:")
            for y in YEARS:
                pv = hub.loc[y]["PALOVRDE"].to_numpy()
                gas = np.asarray(socal_citygate_weekly_hourly(y, HOURS))
                da = act.loc[y]["da"].to_numpy()
                wedge = (
                    CARB_UNSPECIFIED_IMPORT_EF * STATE_CARBON_PRICE_BY_ISO["CAISO"][y]
                )
                meas = np.isfinite(pv)
                off = (
                    blk
                    & sm
                    & meas
                    & ~(meas & (pv < HR_CCGT * gas + CAISO_DSW_SURPLUS_REMOTE_VOM))
                )
                sda = (da - (pv * (1 + wheel_mult) + wheel_add))[off & np.isfinite(da)]
                if not sda.size:
                    print(f"     {y}: (no OFF hours)")
                    continue
                rawh = (da - pv)[off & np.isfinite(da)]
                print(
                    f"     {y}: n_off={sda.size:4d} deliv-DA med {np.median(sda):+6.1f} | "
                    f"raw-hub med {np.median(rawh):+5.1f} | parity(<=+4) {(sda <= 4).mean():4.0%} | "
                    f"wedge(>={wedge - 2:.0f}) {(sda >= wedge - 2).mean():4.0%}"
                )
            print()

    print(
        "=== Refinement B: belly (10-14) trigger-ON vs OFF — where the low-hub/battery regime lives ==="
    )
    print(
        "   (trigger-ON = West solar glut, HUB itself cheap, actual clears just above it;"
    )
    print(
        "    that is caiso-87 territory + the storage charter, NOT this import lane)\n"
    )
    belly = (hod >= 10) & (hod <= 14)
    for y in YEARS:
        pv = hub.loc[y]["PALOVRDE"].to_numpy()
        gas = np.asarray(socal_citygate_weekly_hourly(y, HOURS))
        da = act.loc[y]["da"].to_numpy()
        meas = np.isfinite(pv)
        on = meas & (pv < HR_CCGT * gas + CAISO_DSW_SURPLUS_REMOTE_VOM)
        for sn, sm in (("autumn", autumn), ("all", np.ones(HOURS, bool))):
            c = belly & sm & meas
            on_c, off_c = c & on, c & ~on
            print(
                f"  {y} {sn:6s}: ON n={int(on_c.sum()):4d} actual_med {_med(on_c, da):5.1f} "
                f"hub_med {_med(on_c, pv):5.1f} (da-hub {_med(on_c, da - pv):+5.1f}) | "
                f"OFF n={int(off_c.sum()):4d} actual_med {_med(off_c, da):5.1f} "
                f"hub_med {_med(off_c, pv):5.1f} (da-hub {_med(off_c, da - pv):+5.1f})"
            )
    print("\nNO LP run. Report-only companion; the FINDING carries the disposition.")


if __name__ == "__main__":
    main()
