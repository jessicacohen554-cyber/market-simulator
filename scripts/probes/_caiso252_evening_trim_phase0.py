"""caiso-252 phase 0 (ZERO LP): footprint of DISARMING ``caiso_dsw_daytime_evening_trim``.

Two on-recipe ``fleet_only`` rebuilds of the keeper differing in ONE config
override (the caiso-251 two-rebuild pattern): the daytime WEIM clean-transfer
row ``WECC_DSW_DSW_daytime_clean`` with the caiso-97 trim ON (hod 6-17, depth
4,994/5,563/5,770) vs OFF (hod 6-21, depth 5,441/5,762/5,998). Measures, per
year, the capability the disarm ADDS by hour-of-day, the hours it is armed in,
and — against the keeper's committed P1 duals and the measured raw Palo Verde
hub — how much of it would CLEAR (the row prices at the raw hub, so it clears
iff the SP15-side dual exceeds the hub): the pre-solve order of magnitude the
rule-29 screen gate is set against.

Output: ``results/calibration/_caiso252_evening_trim_phase0.json``.
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
OUT = REPO / "results/calibration/_caiso252_evening_trim_phase0.json"
YEARS = (2023, 2024, 2025)
T = 8760
HOD = np.arange(T) % 24
ROW = "WECC_DSW_DSW_daytime_clean"
EVE = (18, 19, 20, 21)


def rebuild(year: int, trim: bool) -> dict:
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(BUNDLE, year))
    bag = dict(kwargs["prb_overrides"])
    assert bag.get("caiso_dsw_daytime_evening_trim") is True, bag.get("caiso_dsw_daytime_evening_trim")
    bag["caiso_dsw_daytime_evening_trim"] = trim
    kwargs["prb_overrides"] = bag
    clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(year, meta["iso"], T, float(meta["gas_prices"][str(year)]), {},
                      fleet_only=True, **kwargs)
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], dtype=float)
    row = list(fa.unit_ids).index(ROW)
    cap = float(fa.pmax[row]) * np.asarray(fa.availability[row], float)
    return {"cap": cap, "mc": mc[row], "n_units": len(fa.unit_ids),
            "other_caps": {u: float(fa.pmax[i]) for i, u in enumerate(fa.unit_ids) if "WECC" in u}}


def main() -> None:
    hub = pd.read_parquet(REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet")
    res = {}
    for y in YEARS:
        on, off = rebuild(y, True), rebuild(y, False)
        d = off["cap"] - on["cap"]
        s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        lam = {z: g.set_index("hour")["price"].reindex(range(T)).to_numpy() for z, g in s.groupby("zone")}
        pv = hub[(hub["year"] == y) & (hub["hub"] == "PALOVRDE")].set_index("hour")["price"].reindex(range(T)).to_numpy()
        node = lam["WECC_DSW"]; sp = lam["SP15_rest"]
        armed = d > 1.0
        clears = armed & (sp > off["mc"] + 0.01)  # the row prices at raw hub + eps; clears iff the CA-side dual exceeds it
        other_moved = {u: (off["other_caps"][u], on["other_caps"][u]) for u in on["other_caps"] if abs(off["other_caps"][u] - on["other_caps"][u]) > 1e-6}
        res[y] = {
            "n_units_on_off": [on["n_units"], off["n_units"]],
            "added_cap_by_hod_mw": [float(d[HOD == h].mean()) for h in range(24)],
            "added_cap_twh": float(d.sum() / 1e6),
            "armed_hours": int(armed.sum()),
            "armed_hours_by_hod": [int(armed[HOD == h].sum()) for h in range(24)],
            "cap_on_by_hod": [float(on["cap"][HOD == h].mean()) for h in range(24)],
            "cap_off_by_hod": [float(off["cap"][HOD == h].mean()) for h in range(24)],
            "row_mc_mean_when_armed": float(off["mc"][armed].mean()) if armed.any() else None,
            "pv_hub_mean_when_armed": float(np.nanmean(pv[armed])) if armed.any() else None,
            "sp15_dual_mean_when_armed": float(sp[armed].mean()) if armed.any() else None,
            "wecc_dsw_dual_mean_when_armed": float(node[armed].mean()) if armed.any() else None,
            "share_armed_hours_clearing_at_committed_duals": float(clears.sum() / max(armed.sum(), 1)),
            "clearing_cap_twh_at_committed_duals": float(d[clears].sum() / 1e6),
            "clearing_cap_by_hod_mw": [float((d * clears)[HOD == h].mean()) for h in range(24)],
            "other_wecc_rows_moved": other_moved,
            "non_evening_hours_moved": int((np.abs(d) > 1.0)[~np.isin(HOD, EVE)].sum()),
        }
        r = res[y]
        print(f"\n===== {y}: units {r['n_units_on_off']} | disarm ADDS {r['added_cap_twh']:.3f} TWh of capability over {r['armed_hours']} h (non-evening moved: {r['non_evening_hours_moved']} h; other WECC rows moved: {list(other_moved)})")
        print("  added cap by hod:", [round(x) for x in r["added_cap_by_hod_mw"]])
        print("  armed hours by hod:", r["armed_hours_by_hod"])
        print(f"  when armed: row mc {r['row_mc_mean_when_armed']:.1f} | PV hub {r['pv_hub_mean_when_armed']:.1f} | SP15 dual {r['sp15_dual_mean_when_armed']:.1f} | WECC_DSW dual {r['wecc_dsw_dual_mean_when_armed']:.1f}")
        print(f"  clears at the KEEPER's committed duals in {r['share_armed_hours_clearing_at_committed_duals']:.2f} of armed hours -> {r['clearing_cap_twh_at_committed_duals']:.3f} TWh; by hod {[round(x) for x in r['clearing_cap_by_hod_mw']][16:24]}")
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
