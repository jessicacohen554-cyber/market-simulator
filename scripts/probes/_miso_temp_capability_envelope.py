"""Measure the MISO thermal fleet's hot-hour capability envelope from CEMS.

The MISO port of ``_ercot_temp_capability_envelope.py`` /
``_pjm_temp_capability_envelope.py`` — the rule-24 own-fleet validation
flagged for MISO when the PJM fleet refuted the ``temp_dependent_derate``
literature slopes (2026-07-10 calibration-log entry: "MISO's
``miso-49-tempderate`` keeper predates both refutations — flagged for its
own rule-24 own-fleet check as follow-up"). Tests whether the per-class
temperature curves (CT 1.26 %/degC, CC 0.76 %/degC, ST_GAS 0.54 %/degC
above the 15 degC rating point; COAL 0.40 %/degC above 25 degC) have any
signature in the MISO fleet's own measured hourly output. ERCOT's and PJM's
fleets both refuted the slopes (flat envelopes, ~0 or positive
scarcity-hour slopes) and the mechanism exited both keepers.

Port differences from the PJM probe (method identical otherwise):

* **Class/zone mapping** comes from the model's own MISO plant-level fleet
  build (``fleet.load_fleet_from_csv("MISO", ...)``) — the exact
  ``plant_group`` / ``zone`` assignment the derate consumes. Dominant-group
  purity guard >= 90 % of plant thermal MW, as in the PJM probe.
* **COAL is included.** Unlike the gas-only ERCOT/PJM checks, MISO's derate
  cuts COAL additively (no net-summer reshape anchor: the raw curve is a
  pure hot-hour capacity deletion on a ~55 GW class), so the coal envelope
  is load-bearing for the August scarcity question. The model-curve row for
  COAL is normalized at its own 25 degC onset.
* **CAMPD footprint** is the MISO-state file set (MN WI IA IL IN MI MO AR
  LA MS ND SD TX KY MT), inner-joined to the fleet map (membership + group
  + zone in one join keeps only model-MISO plants).
* **Scarcity-hour slope** uses MISO's measured RT (> $200 and > $100, both
  reported with sample sizes, as in the PJM probe).

Diagnostic analysis only — no LP, no solve. Usage:
    python scripts/probes/_miso_temp_capability_envelope.py [YEAR ...]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import iso_zone_tmax  # noqa: E402

CAMPD_DIR = REPO / "data" / "raw" / "campd-unit-level"
LMP_PARQUET = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
)
EIA860_PARQUET = REPO / "data" / "raw" / "eia-860" / "eia860_generator_operable.parquet"

# CAMPD state files covering the MISO footprint.
MISO_STATES = (
    "MN",
    "WI",
    "IA",
    "IL",
    "IN",
    "MI",
    "MO",
    "AR",
    "LA",
    "MS",
    "ND",
    "SD",
    "TX",
    "KY",
    "MT",
)

# MISO summer TMAX bins (reference bin first; zone maxima ~32-40 degC).
REF_BIN = (24, 30)
TBINS = [(24, 28), (28, 30), (30, 32), (32, 34), (34, 36), (36, 40)]
# (slope per degC, onset/reference degC) — mirrors fleet.py _TD_PARAMS.
MODEL_SLOPES = {
    "CC_REGULAR": (0.0076, 15.0),
    "CC_CHP": (0.0076, 15.0),
    "CT_PEAKER": (0.0126, 15.0),
    "ST_GAS": (0.0054, 15.0),
    "COAL": (0.0040, 25.0),
}
GROUPS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "COAL")

# Dominant-group purity threshold for multi-group plants.
GROUP_PURITY = 0.90


def _miso_plant_map() -> pd.DataFrame:
    """Plant → (plant_group, zone) from the model's own MISO fleet build.

    One row per plant whose dominant group carries >= GROUP_PURITY of its
    thermal MW; the group/zone are exactly what the temp derate consumes.
    """
    import logging

    logging.disable(logging.WARNING)
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    gens = load_fleet_from_csv("MISO", get_iso_config("MISO"), year=2023)
    rows = [
        {
            "plantid": int(str(g.unit_id).split("_")[0]),
            "group": g.plant_group,
            "zone": g.zone,
            "mw": float(g.pmax_mw),
        }
        for g in gens
        if g.plant_group in GROUPS and str(g.unit_id).split("_")[0].isdigit()
    ]
    df = pd.DataFrame(rows)
    cap = df.groupby(["plantid", "group"], as_index=False).agg(
        mw=("mw", "sum"), zone=("zone", "first")
    )
    tot = cap.groupby("plantid")["mw"].transform("sum")
    cap = cap[cap["mw"] / tot >= GROUP_PURITY]
    return cap.rename(columns={"group": "Plant_Group"})[
        ["plantid", "Plant_Group", "zone"]
    ]


def _summer_frame(year: int, pmap: pd.DataFrame) -> pd.DataFrame:
    """CAMPD MISO-footprint hourly gross load, class/zone-joined, TMAX-tagged, Jun-Sep."""
    frames = []
    for st in MISO_STATES:
        path = CAMPD_DIR / f"{st}_{year}.parquet"
        if not path.exists():
            print(f"   (no CAMPD file {path.name} — state skipped)")
            continue
        d = pd.read_parquet(
            path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce").astype(
            "Int64"
        )
        d = d.merge(pmap, left_on="facilityId", right_on="plantid", how="inner").drop(
            columns="plantid"
        )
        if len(d):
            frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    d["doy"] = pd.to_datetime(d["date"]).dt.dayofyear
    d["hoy"] = (d["doy"] - 1) * 24 + d["hour"].astype(int)
    tmax = {}
    for z in d["zone"].unique():
        t = iso_zone_tmax("MISO", year, 8760, zone=z)
        if t is not None and t[0] is not None:
            tmax[z] = np.asarray(t[0], dtype=float)
    d = d[d["zone"].isin(tmax)].copy()
    tcol = np.full(len(d), np.nan)
    hoy = d["hoy"].to_numpy()
    for z, arr in tmax.items():
        m = (d["zone"] == z).to_numpy() & (hoy < 8760)
        tcol[m] = arr[hoy[m]]
    d["T"] = tcol
    return d[(d["doy"] >= 152) & (d["doy"] <= 273)].dropna(subset=["T"])


def main(years: list[int]) -> None:
    """Print the measured envelope vs the model curve for each year/class."""
    pmap = _miso_plant_map()
    print(
        "MISO plant map (dominant-group >= "
        f"{GROUP_PURITY:.0%}): "
        + ", ".join(f"{g}={int((pmap['Plant_Group'] == g).sum())}" for g in GROUPS)
    )
    summers = {}
    for year in years:
        summer = _summer_frame(year, pmap)
        summers[year] = summer
        key = ["facilityId", "unitId"]
        ref = (
            summer[(summer["T"] >= REF_BIN[0]) & (summer["T"] <= REF_BIN[1])]
            .groupby(key)["grossLoad"]
            .quantile(0.995)
            .rename("ref")
        )
        summer = summer.merge(ref.reset_index(), on=key)
        summer = summer[summer["ref"] >= 20.0]
        summer["ratio"] = summer["grossLoad"] / summer["ref"]
        print(f"== {year} measured capability envelope (p98 ratio per TMAX bin) ==")
        print("   T bins: " + " | ".join(f"{lo}-{hi}" for lo, hi in TBINS))
        for grp in GROUPS:
            g = summer[summer["Plant_Group"] == grp]
            cells = []
            for lo, hi in TBINS:
                s = g[(g["T"] >= lo) & (g["T"] < hi)]
                cells.append(
                    f"{s['ratio'].quantile(0.98):.3f}" if len(s) > 500 else "  -- "
                )
            n = g.groupby(key).ngroups
            print(f"   {grp:11s} ({n:3d} units): " + " | ".join(cells))
        ref_mid = (REF_BIN[0] + REF_BIN[1]) / 2
        for grp, (slope, onset) in MODEL_SLOPES.items():
            mids = [(lo + hi) / 2 for lo, hi in TBINS]
            ref_m = 1.0 - slope * max(0.0, ref_mid - onset)
            row = " | ".join(
                f"{(1 - slope * max(0.0, m - onset)) / ref_m:.3f}" for m in mids
            )
            print(f"   model {grp:11s} (slope {slope}, onset {onset:.0f}C): " + row)
        _rating_lower_bound(summer, year)
    _scarcity_hour_slope(years, summers)


def _rating_lower_bound(summer: pd.DataFrame, year: int) -> None:
    """Assumption-free lower-bound test: hot-hour PRODUCTION vs the rating.

    Production can never exceed capability, so a plant that PRODUCES >= x%
    of its EIA-860 net-summer rating while zone TMAX >= 34 degC has
    demonstrated that capability at that temperature (36+ also reported).
    Gross-vs-net blurs the ratio upward by the ~2-5 % station load; the
    >= 1.00x share is robust to that.
    """
    g860 = pd.read_parquet(EIA860_PARQUET)
    g860["sc"] = pd.to_numeric(g860["Summer Capacity (MW)"], errors="coerce")
    g860["pc"] = pd.to_numeric(g860["Plant Code"], errors="coerce")
    ns = g860.groupby("pc")["sc"].sum().rename("net_summer")
    ph = summer.groupby(["facilityId", "Plant_Group", "hoy"], as_index=False).agg(
        gross=("grossLoad", "sum"), T=("T", "first")
    )
    ph = ph.merge(ns.reset_index(), left_on="facilityId", right_on="pc", how="inner")
    ph = ph[ph["net_summer"] >= 20.0]
    for tmin in (34.0, 36.0):
        hot = ph[ph["T"] >= tmin].copy()
        if not len(hot):
            print(f"   -- {year} lower-bound test: no TMAX>={tmin:.0f}C hours --")
            continue
        hot["r"] = hot["gross"] / hot["net_summer"]
        print(
            f"   -- {year} lower-bound test: production at TMAX>={tmin:.0f}C "
            "vs net-summer rating --"
        )
        for grp in GROUPS:
            pm = (
                hot[hot["Plant_Group"] == grp]
                .groupby("facilityId")
                .agg(maxr=("r", "max"), ns=("net_summer", "first"))
            )
            if not len(pm):
                continue
            w95 = float(pm.loc[pm["maxr"] >= 0.95, "ns"].sum() / pm["ns"].sum())
            w100 = float(pm.loc[pm["maxr"] >= 1.00, "ns"].sum() / pm["ns"].sum())
            print(
                f"   {grp:11s}: plants={len(pm):3d} median max-output/rating "
                f"{pm['maxr'].median():.3f} | capacity proven >=0.95x: {w95:.0%} "
                f">=1.00x: {w100:.0%}"
            )


def _scarcity_hour_slope(years: list[int], summers: dict[int, pd.DataFrame]) -> None:
    """Derive the capability-vs-TMAX slope from scarcity hours only.

    Max-incentive derivation: in hours with actual RT above the threshold
    every available unit is priced to run at true capability, so the
    output-vs-temperature relation of ONLINE plants (producing > 30 % of
    rating) measures the capability slope with no at-max assumption. MISO's
    system RT clears $200 rarely, so the $100 threshold is also reported
    with its sample size.
    """
    g860 = pd.read_parquet(EIA860_PARQUET)
    g860["sc"] = pd.to_numeric(g860["Summer Capacity (MW)"], errors="coerce")
    g860["pc"] = pd.to_numeric(g860["Plant Code"], errors="coerce")
    ns = g860.groupby("pc")["sc"].sum().rename("net_summer")
    lmp = pd.read_parquet(LMP_PARQUET)
    frames = []
    for year in years:
        s = summers[year]
        ph = s.groupby(["facilityId", "Plant_Group", "hoy"], as_index=False).agg(
            gross=("grossLoad", "sum"), T=("T", "first")
        )
        a = lmp[lmp["year"] == year].set_index("hour")
        rt = np.full(8784, np.nan)
        rt[a.index.to_numpy()] = a["rt"].to_numpy(float)
        ph["rt"] = rt[np.clip(ph["hoy"].to_numpy(), 0, 8783)]
        frames.append(ph)
    ph = pd.concat(frames).merge(
        ns.reset_index(), left_on="facilityId", right_on="pc", how="inner"
    )
    ph = ph[ph["net_summer"] >= 20.0]
    ph["r"] = ph["gross"] / ph["net_summer"]
    tb = [(26, 30), (30, 32), (32, 34), (34, 36), (36, 40)]
    for thresh in (200.0, 100.0):
        sc = ph[ph["rt"] > thresh]
        on = sc[sc["r"] > 0.30]
        print(
            f"   -- scarcity-hour (RT>${thresh:.0f}) capability slope, years "
            f"{years}; plant-hours={len(on):,} --"
        )
        if len(on) < 2000:
            print("      (sample too thin for a slope — bins only)")
        for grp in GROUPS:
            g = on[on["Plant_Group"] == grp]
            cells, pts = [], []
            for lo, hi in tb:
                s = g[(g["T"] >= lo) & (g["T"] < hi)]
                if len(s) > 200:
                    p90 = float(s["r"].quantile(0.90))
                    cells.append(f"{p90:.3f}")
                    pts.append(((lo + hi) / 2, p90))
                else:
                    cells.append("  -- ")
            fit = ""
            hot = [(m, v) for m, v in pts if m >= 30.0]
            if len(hot) >= 3:
                x = np.array([m for m, _ in hot])
                yv = np.array([v for _, v in hot])
                b = np.polyfit(x, yv, 1)[0]
                fit = (
                    f"  fitted slope {b * 100:+.2f} %/degC "
                    f"(model -{MODEL_SLOPES[grp][0] * 100:.2f})"
                )
            print(f"   {grp:11s} p90 online r by T " + " | ".join(cells) + fit)


if __name__ == "__main__":
    yrs = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    main(yrs)
