"""nyiso-242 item 3 — `cc_winter_capability_basis` on NYISO's OWN data (owner-selected, zero LP).

ZERO LP (rule 32 ``[R-SHARD]`` (a)). The cell is ``U`` in
``mechanism-matrix/NYISO.js:132`` with **no evidence string at all** — the one
untested member of the NYISO winter/availability family. The shared field
carries an in-code refusal (``scenarios.py:15239`` — *"REFUSED AT CAISO —
ARMED BY NO KEEPER, DO NOT ARM WITHOUT READING THIS"*, caiso-186 killed
pre-solve on its own ``G-NOCONTRA`` bar), but under rule 25 ``[R-ISO-SCOPE]``
a CAISO verdict can never fill NYISO's cell and a NYISO verdict must be
derived from NYISO's own market. So this probe reproduces the caiso-185/186
test on the NYISO fleet, from NYISO's own published ratings and its own CEMS.

Three questions, in the order that decides the cell:

**A — REACH AND DIRECTION.** What is each NYISO CC plant's published
``winter / nameplate``? The mechanism moves the capacity basis off nameplate
onto ``B = max(net_summer, winter)``, so a fleet whose winter rating sits
BELOW nameplate loses off-summer headroom (which is the direction the
nyiso-242 tail object wants) and one whose winter rating EXCEEDS nameplate
gains it (the wrong direction). caiso-186 measured 0.571–1.089 across 67
California CC plants, 55 below 1 and 8 above; nothing about that number
transfers.

**B — ADMISSIBILITY, which is the caiso-186 killer and is a PRECONDITION, not
a residual.** The refusal is a rule 19 ``[R-ONE-MECH]`` double count: in a
historic backcast a CC unit's availability starts at ``1 − WEFOR``, and where
``wefor_residual is None`` the full statistical CC WEFOR applies ON TOP of the
CAMPD outage overlay that already carries every real outage. Nameplate
headroom over the published rating silently absorbs that WEFOR; removing the
headroom makes the model assert an incapability the CEMS record refutes. The
NYISO keeper carries ``wefor_residual = None`` and ``cc_nameplate_summer_derate
= True`` (its ``wefor_multiplier`` is 0.7), so the trigger is present — this
measures whether it BITES on NYISO's own plants.

**C — THE CEMS CHECK** (a check, never an input — caiso-185 §4a: a demonstrated
peak is availability-INCLUSIVE, so it may not be written into ``capacity_mw``).
Off-summer p999 gross load against published winter and against nameplate.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso242_cc_winter_capability.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
#: NYISO's footprint state. CAMPD unit-level files are per state-year.
NYISO_STATES = ("NY",)
#: Months the incumbent `cc_nameplate_summer_derate` treats as summer.
SUMMER_MONTHS = (6, 7, 8, 9)


def nyiso_cc_plants(year: int) -> set[int]:
    """Plant codes the keeper's own fleet carries as CC_REGULAR / CC_CHP."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    st = run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
    fa = st["fleet_arrays"]
    codes = np.asarray(fa.plant_code)
    klass = np.array([str(k) for k in fa.plant_group])
    return {int(c) for c, k in zip(codes, klass) if k in ("CC_REGULAR", "CC_CHP")}


def ratings() -> pd.DataFrame:
    """Published EIA-860 nameplate / net-summer / winter per CC plant."""
    from market_sim.data.fleet.campd_bins import cc_summer_capacity, cc_winter_capacity

    summer = cc_summer_capacity()
    winter = cc_winter_capacity()
    rows = []
    for code, (nameplate, net_summer) in summer.items():
        w = winter.get(int(code))
        if w is None or w <= 0 or net_summer <= 0 or nameplate <= 0:
            continue
        rows.append(
            {
                "plant_code": int(code),
                "nameplate": float(nameplate),
                "net_summer": float(net_summer),
                "winter": float(w),
            }
        )
    df = pd.DataFrame(rows)
    df["basis_B"] = df[["net_summer", "winter"]].max(axis=1)
    df["winter_over_nameplate"] = df["winter"] / df["nameplate"]
    df["summer_over_nameplate"] = df["net_summer"] / df["nameplate"]
    # The headroom the incumbent nameplate basis leaves off-summer, which is
    # what silently absorbs the statistical WEFOR (question B).
    df["offsummer_headroom_frac"] = 1.0 - df["winter"] / df["nameplate"]
    return df


def cems_offsummer_peak(year: int, plants: set[int]) -> pd.DataFrame:
    """Off-summer p999 CAMPD gross load per plant — a CHECK, never an input."""
    frames = []
    for state in NYISO_STATES:
        p = REPO / "data" / "raw" / "campd-unit-level" / f"{state}_{year}.parquet"
        if not p.exists():
            continue
        cols = pd.read_parquet(p, columns=None).columns
        gl = next((c for c in cols if "gross" in c.lower() and "load" in c.lower()), None)
        pc = next((c for c in cols if c.lower() in ("plant code", "plant_code", "facility id")), None)
        dt = next((c for c in cols if "date" in c.lower()), None)
        if not (gl and pc and dt):
            return pd.DataFrame(columns=["plant_code", "offsummer_p999"])
        df = pd.read_parquet(p, columns=[pc, dt, gl])
        df = df[df[pc].isin(plants)]
        df["_m"] = pd.to_datetime(df[dt], errors="coerce").dt.month
        df = df[~df["_m"].isin(SUMMER_MONTHS)]
        frames.append(df.rename(columns={pc: "plant_code", gl: "gross"}))
    if not frames:
        return pd.DataFrame(columns=["plant_code", "offsummer_p999"])
    allf = pd.concat(frames, ignore_index=True)
    hourly = allf.groupby(["plant_code", allf.index // 1])["gross"].sum()
    g = allf.groupby("plant_code")["gross"].quantile(0.999).rename("offsummer_p999")
    return g.reset_index()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument(
        "--out", default=str(REPO / "results" / "calibration" / "_nyiso242_cc_winter.json")
    )
    args = ap.parse_args()

    plants = nyiso_cc_plants(args.year)
    r = ratings()
    ny = r[r["plant_code"].isin(plants)].copy()

    out: dict = {
        "year": args.year,
        "nyiso_cc_plants_in_fleet": len(plants),
        "with_both_published_ratings": int(len(ny)),
    }
    if len(ny):
        w = ny["winter_over_nameplate"]
        out["A_reach_and_direction"] = {
            "winter_over_nameplate_min": round(float(w.min()), 4),
            "winter_over_nameplate_median": round(float(w.median()), 4),
            "winter_over_nameplate_max": round(float(w.max()), 4),
            "plants_below_1": int((w < 1.0).sum()),
            "plants_at_or_above_1": int((w >= 1.0).sum()),
            # The MW the mechanism would remove (or add) off-summer, fleet-wide.
            "offsummer_mw_removed": round(float((ny["nameplate"] - ny["winter"]).sum()), 1),
            "fleet_nameplate_mw": round(float(ny["nameplate"].sum()), 1),
        }
        # B — does the WEFOR double count bite? Compare the off-summer headroom
        # the incumbent basis leaves against the statistical WEFOR the keeper
        # applies on top of the CAMPD overlay.
        cfg = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
        out["B_admissibility"] = {
            "wefor_residual": cfg.get("wefor_residual"),
            "wefor_multiplier": cfg.get("wefor_multiplier"),
            "cc_nameplate_summer_derate": cfg.get("cc_nameplate_summer_derate"),
            "trigger_present": cfg.get("wefor_residual") is None
            and bool(cfg.get("cc_nameplate_summer_derate")),
            "offsummer_headroom_frac_median": round(
                float(ny["offsummer_headroom_frac"].median()), 4
            ),
            "plants_with_headroom_below_5pct": int(
                (ny["offsummer_headroom_frac"] < 0.05).sum()
            ),
            "plants_with_negative_headroom": int(
                (ny["offsummer_headroom_frac"] < 0).sum()
            ),
        }
        out["per_plant"] = (
            ny.sort_values("winter_over_nameplate")[
                ["plant_code", "nameplate", "net_summer", "winter", "winter_over_nameplate"]
            ]
            .round(4)
            .to_dict("records")
        )

    print(json.dumps({k: v for k, v in out.items() if k != "per_plant"}, indent=2))
    if out.get("per_plant"):
        print("\nper-plant (sorted by winter/nameplate):")
        for row in out["per_plant"]:
            print(
                f"  {row['plant_code']:>6} nameplate={row['nameplate']:8.1f} "
                f"summer={row['net_summer']:8.1f} winter={row['winter']:8.1f} "
                f"w/n={row['winter_over_nameplate']:.4f}"
            )
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
