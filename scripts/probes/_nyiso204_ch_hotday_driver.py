"""nyiso-204 phase 0 (d) — the rule-17 [R-FLOOR-WINDOW] DRIVER test for the hot step.

ZERO LP. Reads CAMPD unit-level hourly ``grossLoad`` and the same zone TMAX
series the floor engine itself gates on.

WHY THIS TEST AND NOT THE ANNUAL CENSUS. nyiso-203b's census establishes that
Danskammer 2480 and Roseton 8006 are economically laid up *on the year*: every
(year, block) cell at a zero median, online 2.9 % / 14.6 %. That is the
nyiso-140 criterion, and it was identified against a PERSISTENT 24 h BASE limb —
a floor whose driver claim is "this class runs all the time".

The live Capital_Hudson limb makes a DIFFERENT claim: ``tmax 31.1`` is a
design-cooling-day commitment, so its driver evidence is "this class commits on
hot days". Rule 17 requires the exclusion argument be made against THAT driver,
and the precedent does not supply it — nyiso-140's own Port Jefferson **ran on
hot days** (P(on) 0.932 at tmax >= 30 C, mean 166.2 MW): it was in the wrong
limb, not a dead plant. A plant can be laid up on the year and still be exactly
what a hot-day step is for.

So this probe asks the only question that licenses the exclusion from THIS limb:
on the limb's own flagged hours (zone TMAX > 31.1 C), do 2480 and 8006 run?

Reported per plant per year, on flagged hours and for contrast on all hours:
P(online), mean MW, median MW, and max MW. Bethlehem 2625 — the non-candidate
that absorbs ~96-99 % of this limb's floor — is measured alongside as the
positive control: a plant that DOES answer the hot-day driver.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RAW = ROOT / "data" / "raw"
OUT = ROOT / "results" / "calibration" / "_nyiso204_ch_hotday_driver.json"
PHASE0 = ROOT / "results" / "calibration" / "_nyiso204_ch_layup_phase0.json"

ZONE = "Capital_Hudson"
THRESHOLD = 31.1  # the limb's own gate, deg C
YEARS = (2023, 2024, 2025)
CANDIDATES = {2480: "Danskammer", 8006: "Roseton"}
CONTROL = {2625: "Bethlehem Energy Center"}
TARGETS = {**CANDIDATES, **CONTROL}


def main() -> int:
    from market_sim.data.eia930.weather import iso_zone_tmax

    binding = {
        y: v.get("binding_hours_by_plant", {})
        for y, v in json.loads(PHASE0.read_text())["years"].items()
    }

    rec: dict = {
        "probe": "nyiso-204 phase 0 (d) — hot-step driver test",
        "zero_lp": True,
        "zone": ZONE,
        "threshold_c": THRESHOLD,
        "gate": "zone TMAX > threshold (the limb's own day gate)",
        "candidates": {str(k): v for k, v in CANDIDATES.items()},
        "control": {str(k): v for k, v in CONTROL.items()},
        "years": {},
    }

    for year in YEARS:
        hours = 8784 if year % 4 == 0 else 8760
        wx = iso_zone_tmax("NYISO", year, hours, zone=ZONE)
        if wx is None:
            raise SystemExit(f"no weather for {ZONE} {year}")
        tmax, _ = wx
        flagged = np.asarray(tmax) > THRESHOLD

        c = pd.read_parquet(RAW / "campd-unit-level" / f"NY_{year}.parquet")
        c = c[c["facilityId"].astype(int).isin(TARGETS)].copy()
        c["code"] = c["facilityId"].astype(int)
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        g = c.groupby(["code", "ts"])["grossLoad"].sum().reset_index()

        # Map each timestamp onto the run horizon's hour index, exactly as the
        # engine's hourly broadcast does (hour-of-year from Jan 1).
        origin = pd.Timestamp(year=year, month=1, day=1)
        g["h"] = ((g["ts"] - origin) / pd.Timedelta(hours=1)).astype(int)
        g = g[(g["h"] >= 0) & (g["h"] < hours)]

        yr: dict = {"flagged_hours": int(flagged.sum()), "plants": {}}
        for code, name in TARGETS.items():
            p = g[g["code"] == code]
            series = np.zeros(hours, dtype=float)
            series[p["h"].to_numpy()] = p["grossLoad"].to_numpy(dtype=float)
            covered = np.zeros(hours, dtype=bool)
            covered[p["h"].to_numpy()] = True

            def stats(mask):
                v = series[mask]
                cov = covered[mask]
                if v.size == 0:
                    return {"n": 0}
                return {
                    "n": int(v.size),
                    "n_reported": int(cov.sum()),
                    "p_online": float((v > 0).mean()),
                    "mean_mw": float(v.mean()),
                    "median_mw": float(np.median(v)),
                    "max_mw": float(v.max()),
                }

            # The exact hours D-4 scores: where THIS limb actually raised this
            # plant's min_gen (phase 0 (a)/(b)'s committed masks). The step flags
            # a whole hot day for the ZONE, but cheapest-first only BINDS a unit
            # once the cheaper rows are exhausted, so the flagged and binding
            # sets are different questions and are reported separately rather
            # than conflated.
            bmask = np.zeros(hours, dtype=bool)
            idx = binding.get(str(year), {}).get(str(code), [])
            if idx:
                arr = np.asarray(idx, dtype=int)
                bmask[arr[arr < hours]] = True

            yr["plants"][str(code)] = {
                "name": name,
                "is_candidate": code in CANDIDATES,
                "on_flagged_hours": stats(flagged),
                "on_binding_hours": stats(bmask) if bmask.any() else {"n": 0},
                "all_hours": stats(np.ones(hours, dtype=bool)),
            }
        rec["years"][str(year)] = yr

        print(f"=== {year}  flagged (TMAX > {THRESHOLD} C): {int(flagged.sum())} h")
        for code, name in TARGETS.items():
            f = yr["plants"][str(code)]["on_flagged_hours"]
            a = yr["plants"][str(code)]["all_hours"]
            tag = "CAND" if code in CANDIDATES else "ctrl"
            b = yr["plants"][str(code)]["on_binding_hours"]
            bstr = (
                f"binding({b['n']:>3}h): P(on) {b['p_online']:.3f} mean {b['mean_mw']:7.1f}"
                if b.get("n")
                else "binding(  0h): --"
            )
            print(
                f"  {tag} {code:>5} {name[:22]:<22} flagged: P(on) {f['p_online']:.3f} "
                f"mean {f['mean_mw']:7.1f} max {f['max_mw']:7.1f} | {bstr} | "
                f"all-yr: P(on) {a['p_online']:.3f} mean {a['mean_mw']:6.1f}"
            )

    OUT.write_text(json.dumps(rec, indent=2) + "\n")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
