"""miso-139 — the CEILING of the ambient-derate family, under ANY admissible convention.

PREREG ``PREREG-miso139-ambient-derate-class-scope-2026-08-06.md`` @ ``6263f43d``.

G-0 refuses both implemented conventions.  The named successor — a SUMMER-mean
anchor, the only convention consistent with a net-summer ``pmax`` basis — is a
mechanism change this session is not chartered to make.  But its REACH is
bounded from MISO's own measured inputs without building it: under a summer
anchor the within-summer capability swing is exactly

    swing_aft(k)   = slope_k * (T_aft   - T_summer_mean)      [derate]
    swing_night(k) = slope_k * (T_summer_mean - T_night)      [uprate]

with ``slope_k`` the G-1 EIA-860 identification and the temperatures the G-0(a)
measured zone anchors.  That bound is compared against the model's OWN measured
idle headroom in the same window (G-2).  Nothing is sized to a residual: this is
an upper bound on a mechanism's reach, computed from weather and registration
data alone (rules 1 / 21 / 24).

Reads ``_miso139_derate_gates.json`` + ``_miso139_g2_binding.json``; writes
``_miso139_successor_bound.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
GATES = REPO / "results/calibration/_miso139_derate_gates.json"
G2 = REPO / "results/calibration/_miso139_g2_binding.json"
OUT = REPO / "results/calibration/_miso139_successor_bound.json"

ARMED = ("CT_PEAKER", "CC_REGULAR")


def main() -> None:
    g = json.loads(GATES.read_text())
    g2 = json.loads(G2.read_text())
    slopes = g["g1_miso_own_slopes"]

    rows = {r["zone"] + "|" + str(r["year"]): r for r in g["g0a_weather"]["rows"]}
    out: dict = {
        "prereg": "PREREG-miso139-... @ 6263f43d",
        "what": (
            "upper bound on the reach of the ambient-derate family under the "
            "named successor convention (SUMMER-mean anchor), from MISO's own "
            "measured weather + EIA-860 identification. Not a mechanism; a ceiling."
        ),
        "slopes_used": slopes,
        "years": {},
    }
    for y in ("2023", "2024", "2025"):
        # capacity-weighted zone spread is not available here, so the bound uses
        # the unweighted zone range AND the zone mean, and reports both.
        aft = [
            rows[f"{z}|{y}"]["aft_minus_summer_c"]
            for z in g["g0a_weather"]["zones"]
            if f"{z}|{y}" in rows
        ]
        nig = [
            -rows[f"{z}|{y}"]["night_minus_summer_c"]
            for z in g["g0a_weather"]["zones"]
            if f"{z}|{y}" in rows
        ]
        rec: dict = {
            "dT_aft_above_summer_c": {
                "mean": float(np.mean(aft)),
                "min": float(np.min(aft)),
                "max": float(np.max(aft)),
            },
            "dT_night_below_summer_c": {
                "mean": float(np.mean(nig)),
                "min": float(np.min(nig)),
                "max": float(np.max(nig)),
            },
            "classes": {},
        }
        gy = g2["years"][y]["classes"]
        for k in ARMED:
            s = slopes[k]
            w = gy[k]["A_misoslope|summer_aft"]
            cap = w["mean_capability_mw"]
            head = w["mean_headroom_mw"]
            rec["classes"][k] = {
                "slope_per_c": s,
                "swing_aft_frac": s * float(np.mean(aft)),
                "swing_night_frac": s * float(np.mean(nig)),
                "mean_capability_mw": cap,
                "successor_removal_aft_mw": s * float(np.mean(aft)) * cap,
                "successor_uprate_night_mw": s
                * float(np.mean(nig))
                * gy[k]["A_misoslope|summer_night"]["mean_capability_mw"],
                "own_idle_headroom_aft_mw": head,
                "removal_over_headroom": (s * float(np.mean(aft)) * cap) / head,
            }
        tot_rem = sum(v["successor_removal_aft_mw"] for v in rec["classes"].values())
        cushion = (
            sum(v["own_idle_headroom_aft_mw"] for v in rec["classes"].values())
            + g2["years"][y]["cushion"]["summer_aft"]["coal_unloaded_mw_mean"]
        )
        rec["total_successor_removal_aft_mw"] = tot_rem
        rec["total_idle_cushion_aft_mw"] = cushion
        rec["cushion_over_removal"] = cushion / tot_rem
        out["years"][y] = rec
    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT}")
    for y, r in out["years"].items():
        print(
            f"{y}: successor removal {r['total_successor_removal_aft_mw']:.0f} MW "
            f"vs idle cushion {r['total_idle_cushion_aft_mw']:.0f} MW "
            f"({r['cushion_over_removal']:.1f}x)"
        )


if __name__ == "__main__":
    main()
