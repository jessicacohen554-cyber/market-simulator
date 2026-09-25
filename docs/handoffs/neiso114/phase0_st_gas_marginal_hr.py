"""neiso-114 phase 0 (zero LP): the NEISO ST_GAS marginal-HR bands re-derived on the CORRECTED class.

The keeper's ST_GAS offer bands (0.79 / 0.85 / 0.89 registered, x0.9547 fossil
scalar = 0.754 / 0.811 / 0.850) are ``marg_{committed,econ_low,econ_high}_p50 x
1.223`` from ``scripts/data/derive_campd_marginal_hr.py --iso NEISO`` — whose
ST_GAS class, read from ``bin_assignments_NEISO.csv`` (the canonical 2025ER
fleet), is Montville 546 ALONE (n=2 CEMS units). The corrected fleet (R-NEISO,
year-matched EIA-860 vintages) carries Middletown 562, Newington 8002, New Haven
Harbor 6156 and West Springfield 1642 as ST_GAS as well. This probe applies the
derive's OWN per-unit construction (``derive_unit_bands``, unchanged) to the
corrected class membership, pooled over the scored CEMS years 2019-2025, and
reports the cap-weighted p50s two ways:

* ``class``  — normalised by the class cap-weighted base HR, the derive's
  convention (base = the corrected class's plant heat rates, capacity-weighted);
* ``own``    — each unit normalised by its OWN steady-state average heat rate
  (sum heatInput / sum grossLoad), i.e. the ratio the model applies when it
  multiplies each plant's own heat rate by the band.

Zero LP; reads only CAMPD unit-level parquet.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

import derive_campd_marginal_hr as d  # noqa: E402

# Corrected-fleet ST_GAS plants (phase0_offer_census, union over 2019-2024
# vintage fleets, >= 50 MW). Montville 546 is the keeper's original sample.
CORRECTED = {
    546: "Montville",
    562: "Middletown",
    8002: "Newington",
    6156: "New Haven Harbor",
    1642: "West Springfield",
}
YEARS = tuple(range(2019, 2026))
REACH = 1.223  # NEISO's own CC reach ratio, _NEISO_OFFER_CURVE ST_GAS comment


def main() -> int:
    camp = d.load_campd("NEISO", YEARS)
    camp = camp[camp["facilityId"].isin(CORRECTED)]
    camp = camp[camp["unitType"].map(lambda t: d._unit_family(t) == "ST")].copy()
    camp["uid"] = camp["facilityId"].astype(str) + "_" + camp["unitId"].astype(str)
    rows = []
    for uid, u in camp.groupby("uid"):
        own = float(u["heatInput"].sum() / u["grossLoad"].sum())
        # Normalised by the unit's OWN average HR (the derive's plausibility
        # window 0 < m < 5 is on the ratio); rescaled to absolute MMBtu/MWh.
        r = d.derive_unit_bands(u, own)
        if r is None:
            continue
        for b in ("committed", "econ_low", "econ_high"):
            r[f"marg_{b}"] = r[f"marg_{b}"] * own
            r[f"avg_{b}"] = r[f"avg_{b}"] * own
        r.update(
            uid=uid, plant=int(u["facilityId"].iloc[0]), hours=len(u), own_avg_hr=own
        )
        rows.append(r)
    pu = pd.DataFrame(rows)
    out = {"units": pu.round(4).to_dict("records")}
    for label, sel in (
        ("montville_only", pu["plant"] == 546),
        ("corrected_class", pu["plant"] > 0),
    ):
        s = pu[sel]
        class_base = float(np.average(s["own_avg_hr"], weights=s["cap"]))
        res = {"n_units": int(len(s)), "class_base_hr": round(class_base, 3)}
        for b in ("committed", "econ_low", "econ_high"):
            m = s[f"marg_{b}"].to_numpy(float)
            ok = np.isfinite(m)
            res[f"class_{b}_p50"] = round(
                d._wquantile(m[ok] / class_base, s["cap"].to_numpy(float)[ok], 0.5), 3
            )
            res[f"own_{b}_p50"] = round(
                d._wquantile(
                    m[ok] / s["own_avg_hr"].to_numpy(float)[ok],
                    s["cap"].to_numpy(float)[ok],
                    0.5,
                ),
                3,
            )
        for k in ("class", "own"):
            res[f"{k}_bands_x_reach"] = [
                round(res[f"{k}_{b}_p50"] * REACH, 3)
                for b in ("committed", "econ_low", "econ_high")
            ]
        out[label] = res
    print(json.dumps({k: v for k, v in out.items() if k != "units"}, indent=1))
    print(
        pu[
            [
                "uid",
                "hours",
                "cap",
                "own_avg_hr",
                "marg_committed",
                "marg_econ_low",
                "marg_econ_high",
            ]
        ]
        .round(3)
        .to_string()
    )
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
