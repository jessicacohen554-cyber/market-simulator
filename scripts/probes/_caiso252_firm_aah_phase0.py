"""caiso-252 phase 0 (ZERO LP) for the RA-import availability-assessment-hour arm.

On-recipe ``fleet_only`` rebuild of the keeper (``replay_keeper.run_year_kwargs``
+ ``derived_run_year_inputs``, caiso-248 §8.1) to read the CAISO firm import
rows' capability, self-schedule floor and offer, hour by hour, against the
keeper's committed WECC node duals — so the footprint of pricing the firm RA
import blocks as price-takers in the availability assessment hours (AAH,
CPUC D.20-06-028: RA imports self-schedule or bid ≤ $0/MWh in AAH; AAH = HE17–21
on non-holiday weekdays, CAISO tariff §40.9.2 / DMM 2025 §16) is measured
before anything is coded or solved.

Output: ``results/calibration/_caiso252_firm_aah_phase0.json``.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/caiso251_arm_nomargin"
OUT = REPO / "results/calibration/_caiso252_firm_aah_phase0.json"
YEARS = (2023, 2024, 2025)
T = 8760
HOD = np.arange(T) % 24
AAH_HOURS = (16, 17, 18, 19, 20)  # hours BEGINNING 16..20 == HE17..HE21
# NERC holidays (the CAISO off-peak / AAH "non-holiday" calendar): New Year's,
# Memorial, Independence, Labor, Thanksgiving, Christmas — observed dates.
HOLIDAYS = {
    2023: ["2023-01-02", "2023-05-29", "2023-07-04", "2023-09-04", "2023-11-23", "2023-12-25"],
    2024: ["2024-01-01", "2024-05-27", "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25"],
    2025: ["2025-01-01", "2025-05-26", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25"],
}
FIRM = ("PNW_hydro_base", "DSW_solar_PV")


def aah_mask(year: int) -> np.ndarray:
    """(T,) bool — AAH hours on the model's non-leap local clock."""
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    days = days[~((days.month == 2) & (days.day == 29))]
    assert len(days) == 365
    hol = {pd.Timestamp(d) for d in HOLIDAYS[year]}
    wk = np.array([(d.weekday() < 5) and (d not in hol) for d in days])
    m = np.zeros(T, dtype=bool)
    for i, ok in enumerate(wk):
        if ok:
            for h in AAH_HOURS:
                m[i * 24 + h] = True
    return m


def rebuild(year: int) -> dict:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.caiso import split_caiso_import_node_per_hub
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(BUNDLE, year))
    clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(year, meta["iso"], T, float(meta["gas_prices"][str(year)]), {},
                      fleet_only=True, **kwargs)
    fa = st["fleet_arrays"]
    zones = list(split_caiso_import_node_per_hub(get_iso_config("CAISO")).zone_names)
    mc = np.asarray(st["mc_base"], dtype=float)
    return {"fa": fa, "mc": mc, "zones": zones}


def duals(year: int) -> dict[str, np.ndarray]:
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return {z: g.set_index("hour")["price"].reindex(range(T)).to_numpy() for z, g in s.groupby("zone")}


def main() -> None:
    res = {}
    for y in YEARS:
        rb = rebuild(y)
        fa, mc = rb["fa"], rb["mc"]
        lam = duals(y)
        m = aah_mask(y)
        rows = {}
        for row, uid in enumerate(fa.unit_ids):
            for name in FIRM:
                if uid.endswith("_" + name):
                    zone = uid[: -len(name) - 1]
                    cap = float(fa.pmax[row]) * np.asarray(fa.availability[row], float)
                    floor = np.asarray(fa.min_gen[row], float) if getattr(fa, "min_gen", None) is not None else np.zeros(T)
                    offer = mc[row]
                    node = lam.get(zone)
                    headroom = cap - floor
                    priced_out = (node < offer) if node is not None else np.zeros(T, bool)
                    rows[uid] = {
                        "zone": zone, "pmax": float(fa.pmax[row]),
                        "offer_mean": float(offer.mean()), "offer_min": float(offer.min()), "offer_max": float(offer.max()),
                        "cap_by_hod": [float(cap[HOD == h].mean()) for h in range(24)],
                        "floor_by_hod": [float(floor[HOD == h].mean()) for h in range(24)],
                        "node_dual_by_hod": [float(node[HOD == h].mean()) for h in range(24)] if node is not None else None,
                        "aah": {
                            "n_hours": int(m.sum()),
                            "cap_twh": float(cap[m].sum() / 1e6), "floor_twh": float(floor[m].sum() / 1e6),
                            "headroom_twh": float(headroom[m].sum() / 1e6),
                            "headroom_mean_mw": float(headroom[m].mean()),
                            "share_hours_priced_out": float(priced_out[m].mean()),
                            "headroom_twh_in_priced_out_hours": float(headroom[m & priced_out].sum() / 1e6),
                            "node_dual_mean": float(node[m].mean()) if node is not None else None,
                        },
                        "non_aah": {
                            "share_hours_priced_out": float(priced_out[~m].mean()),
                            "headroom_twh_in_priced_out_hours": float(headroom[~m & priced_out].sum() / 1e6),
                        },
                    }
        res[y] = {"aah_hours": int(m.sum()), "rows": rows,
                  "unit_ids_firm_like": [u for u in fa.unit_ids if "WECC" in u][:40]}
        print(f"\n===== {y}: AAH hours {int(m.sum())}")
        for uid, r in rows.items():
            a = r["aah"]
            print(f"  {uid}: pmax {r['pmax']:.0f} offer {r['offer_min']:.1f}..{r['offer_max']:.1f} | AAH cap {a['cap_twh']:.3f} TWh floor {a['floor_twh']:.3f} headroom {a['headroom_twh']:.3f} ({a['headroom_mean_mw']:.0f} MW) | priced-out share {a['share_hours_priced_out']:.2f} -> deliverable {a['headroom_twh_in_priced_out_hours']:.3f} TWh | node dual {a['node_dual_mean']:.1f} | non-AAH priced-out {r['non_aah']['share_hours_priced_out']:.2f}")
            print("     cap/hod  ", [round(x) for x in r["cap_by_hod"]])
            print("     floor/hod", [round(x) for x in r["floor_by_hod"]])
            print("     dual/hod ", [round(x) for x in r["node_dual_by_hod"]] if r["node_dual_by_hod"] else None)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
