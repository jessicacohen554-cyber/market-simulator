"""miso-161 — the LAST un-adjudicated admissible availability quantity, measured:
does the MOM record's DAILY grain add anything at the peak beyond the armed
seasonal share?

NO SOLVE. NO ScenarioConfig FIELD. NO CELL VERDICT. The miso-160 keeper arms
``summer_wefor_share_override = 1.0599`` — the pooled Jun–Sep/annual ratio of
MISO's published MOM unplanned offline MW (owner provenance decision,
``docs/handoffs/miso-outage-grain-data-ask-2026-07.md`` §9). The seasonal share
spreads that ratio FLAT across Jun–Sep. The record itself is DAILY (§2C), so
one measured question remains before the availability channel is exhausted:
**on the actual top-200 model-demand days, does the measured unplanned offline
MW sit above or below the Jun–Sep mean the armed share already applies — and
by how much?**

Basis: identical to the miso-160 derive (region ``"MISO"``, causes
``Derated+Forced+Unplanned``, the production loader
``miso_outage_mw_series``, model non-leap clock). The top-200 window is the
D-3/decomposition window: the 200 highest ISO-demand hours of the keeper's own
committed P1 solve (six carry zones).

Scope notes, fixed before the numbers were read:

* This is an IDENTIFICATION MEASUREMENT for materiality, not a mechanism
  build. Whatever it reads, arming a daily fleet-uniform shape would ALSO need
  its own owner amendment — §9 amends §2a to fleet grain for exactly ONE
  deliverable (the scalar), and §9's own text preserves the miso-85/87
  closures (the uniform daily ENVELOPE rebasis is `R` at miso-85/86 and the
  attribution split is refuted-at-charter at miso-87).
* The materiality yardstick is the miso-160 episode itself: −3.46/−3.59/−3.67
  GW of Jun–Sep capability moved C3a by +0.60 pp in 2025. The daily-shape
  increment at the peak is read against that measured price-response scale.

Rule 22 ``[R-HOLDOUT]``: 2023–2025 only; MISO holds neither marker.

Usage::

    PYTHONPATH=$PWD:$PWD/src .venv/bin/python \\
        scripts/probes/_miso161_peakday_outage_shape.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.data.miso_outages import miso_outage_mw_series  # noqa: E402

# The armed override's own basis (the miso-160 derive, PREREG §3): unplanned
# GADS EFOR-family buckets, system region.
UNPLANNED = ("Derated", "Forced", "Unplanned")
REGION = "MISO"
YEARS = (2023, 2024, 2025)
BUNDLE = REPO / "results/calibration/miso160_wefor_B"
OUT = REPO / "results/calibration/_miso161_peakday_outage_shape.json"
CARRY = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)
# miso-160 FINDING §4: measured Jun–Sep capability reach (GW) and the C3a-2025
# response (+0.60 pp) — the price-response scale the increment is read against.
M160_REACH_GW = {2023: 3.46, 2024: 3.59, 2025: 3.67}
M160_C3A_2025_PP = 0.60


def main() -> dict:
    out: dict = {
        "basis": {
            "region": REGION,
            "cause_types": list(UNPLANNED),
            "loader": "market_sim.data.miso_outages.miso_outage_mw_series",
            "window": "top-200 ISO-demand hours of the keeper's committed P1",
            "keeper": "2026-08-16-miso-160-wefor-shape",
        },
        "years": {},
    }
    for year in YEARS:
        s = miso_outage_mw_series(year, region=REGION, cause_types=UNPLANNED)
        assert s.any(), f"no MOM rows for {year}"
        idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
        mo = idx.month.to_numpy()
        junsep = (mo >= 6) & (mo <= 9)

        sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
        sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"].isin(CARRY))]
        dem = (
            sysf.pivot_table(index="hour", columns="zone", values="demand")
            .sum(axis=1)
            .to_numpy()
        )
        top200 = np.zeros(8760, bool)
        top200[np.argsort(-dem)[:200]] = True

        ann = float(s.mean())
        js = float(s[junsep].mean())
        t200 = float(s[top200].mean())
        ratio = t200 / js
        # The increment the flat seasonal share misses at the peak, in MW.
        inc_mw = t200 - js
        rec = {
            "annual_mean_offline_mw": ann,
            "junsep_mean_offline_mw": js,
            "top200_mean_offline_mw": t200,
            "top200_hours_in_junsep": int((top200 & junsep).sum()),
            "top200_over_junsep_ratio": ratio,
            "peak_increment_beyond_seasonal_share_mw": inc_mw,
            "m160_junsep_reach_gw": M160_REACH_GW[year],
        }
        if year == 2025:
            # Bounded price-response read: the miso-160 episode moved C3a-2025
            # +0.60 pp per 3.67 GW of Jun–Sep-wide removal; the daily increment
            # is peak-scoped (200 h, not 2,928 h), so scaling its MW against
            # the episode's GW→pp slope OVERSTATES it. Reported as an upper
            # bound, never as a prediction.
            rec["c3a_2025_upper_bound_pp"] = (
                abs(inc_mw) / (M160_REACH_GW[2025] * 1000.0) * M160_C3A_2025_PP
            )
        out["years"][str(year)] = rec
        print(
            f"{year}: annual {ann/1e3:.2f} GW | Jun-Sep {js/1e3:.2f} GW | "
            f"top200 {t200/1e3:.2f} GW | ratio {ratio:.4f} | "
            f"increment {inc_mw/1e3:+.2f} GW",
            flush=True,
        )
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
