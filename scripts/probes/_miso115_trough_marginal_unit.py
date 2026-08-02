"""miso-115 Phase-1 probe — is MISO's overnight trough marginal unit mis-specified?

NO LP IS SOLVED. Every number is read from committed artifacts:

* the keeper bundle ``results/calibration/miso109_hy_level_B`` —
  ``hourly/class_hourly_<year>.parquet`` (P1 class dispatch, the model side),
* ``data/raw/campd-unit-level/{STATE}_{YEAR}.parquet`` — CAMPD hourly unit
  gross load, carrying ``unitType`` + ``primaryFuelInfo`` (the prime-mover
  split EIA-930 cannot give, which is why miso-114 could measure only the
  model side),
* the EIA-860 generator parquet, via :func:`load_fleet_from_csv`, for the
  ``balancing_authority_code == "MISO"`` plant set and the model's own class
  capacities.

The pre-registered question, gates and kills are in
``results/calibration/PREREG-miso115-trough-marginal-unit-2026-08-02.md``,
written and committed BEFORE this probe was run:

    Measure MISO's CAMPD-observed CT_PEAKER + ST_GAS generation at h1-h3,
    2023-2025, against the model's 1,907 / 2,415 / 2,350 MW.

**RECORD NOTE (miso-116, 2026-08-02) — numbers below are UNCHANGED and this
file is left exactly as it ran; two of the results it produced are withdrawn.**
See ``results/calibration/FINDING-miso116-chp-floor-deriver-2026-08-02.md``:

* The **CHP** ratios (``CC_CHP`` 2.156/2.246/2.555 and the §3 gas
  reconciliation) divide CAMPD ``grossLoad`` -- the WHOLE plant, host steam
  load included -- by ``class_hourly.mw``, which for a CHP class is
  GRID-FACING ONLY (``fleet/assembly.py`` removes the behind-the-meter share as
  capacity; the bench closes the basis on the actual side instead). Basis-
  matched, ``CC_CHP`` R = 1.062/1.123/1.234: there is no CC-cogen deficit. The
  three MERCHANT classes -- the pre-registered verdict scope -- are unaffected,
  since they carry no BTM hold-out.
* :func:`model_fleet` calls ``load_fleet_from_csv`` WITHOUT
  ``measured_chp_heat_rates``, which defaults to False while the keeper arms
  it, so the §4 ``CC_CHP`` "6.76 MMBtu/MWh" is the pre-correction eGRID
  steam-credited rate. The keeper's own value is 8.77 against a measured 8.83.
  ``CT_PEAKER`` is unaffected (the keeper does not arm ``measured_ct_heat_rates``),
  so §4's CT_PEAKER pricing error stands as published.

A probe that scores against a keeper should build its model side from that
keeper's ``run_config.json`` (as ``_miso116_chp_floor_deriver_audit.py`` does).

Design notes that matter for the comparison being apples-to-apples:

* The model quantity is ``class_hourly.mw`` — **generation**, not committed
  capacity (miso-114's "online" wording notwithstanding). The CAMPD comparable
  is therefore hourly ``grossLoad``, not nameplate.
* ``grossLoad`` is GROSS; the model's ``mw`` is NET. Gross exceeds net by
  auxiliary load (~2-5 % CT, ~5-8 % steam), so the CAMPD side is biased UP.
  That bias is conservative: it makes a "materially less" verdict harder to
  reach, never easier.
* The comparison is **plant-matched**. The model's ``CT_PEAKER`` / ``ST_GAS``
  classes exclude cogens (which live in ``CT_CHP`` / ``ST_CHP``), so matching
  on the model's own plant set keeps the CHP boundary identical on both
  sides. Within a matched plant, only CAMPD units whose measured technology
  family agrees are summed, which is how ``derive_campd_marginal_hr`` handles
  facilities that report several technologies.

Rule 24 [R-REGISTRY]: every crosswalk is the repo's own —
:func:`market_sim.data.campd.states_for_iso` (which CAMPD state extracts feed
MISO), :func:`market_sim.data.campd._hour_index_8760` (the CAMPD -> 8760 model
calendar map, which drops Feb 29 per rule 8 [R-8760]),
:func:`scripts.lib.bench_multiclass.unit_family` (CAMPD ``unitType`` +
``primaryFuelInfo`` -> technology family) and ``ISO_TO_BA_CODE`` via the
EIA-860 fleet loader (MISO membership is by balancing-authority code, never by
state). No hand map is introduced.

Rule 22 [R-HOLDOUT]: 2023-2025 only. MISO holds no calibration-complete
marker, so no holdout year is read. Rule 15: no run is produced.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.bench_multiclass import unit_family  # noqa: E402
from market_sim.config.paths import CAMPD_UNIT_LEVEL_DIR  # noqa: E402
from market_sim.data.campd import _hour_index_8760, states_for_iso  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402

BUNDLE = ROOT / "results/calibration/miso109_hy_level_B"
YEARS = (2023, 2024, 2025)
TROUGH = (1, 2, 3)
# Model class -> the CAMPD technology family a unit of that class must report.
# CC_REGULAR is not part of the pre-registered verdict (which is scored on
# CT_PEAKER + ST_GAS only); it is measured because the verdict's arithmetic
# forces a consequence. miso-114 measured a 3.4-3.9 GW overnight gas hole; if
# CT + ST are reproduced, the hole must sit in combined cycle, and that is
# checkable inside CAMPD by the same construction rather than by subtracting
# two different sources.
PAIRS = {
    "CT_PEAKER": "CT",
    "ST_GAS": "ST_GAS",
    "CC_REGULAR": "CC",
    # The CHP classes close the Phase-1c gas reconciliation: they are the only
    # gas capacity left once the three merchant classes are matched.
    "CC_CHP": "CC",
    "CT_CHP": "CT",
    "ST_CHP": "ST_GAS",
}
VERDICT_CLASSES = ("CT_PEAKER", "ST_GAS")
UNIT_COLS = [
    "stateCode",
    "facilityId",
    "unitId",
    "date",
    "hour",
    "opTime",
    "grossLoad",
    "heatInput",
    "unitType",
    "primaryFuelInfo",
]


def model_fleet(year: int) -> pd.DataFrame:
    """MISO's modelled fleet for ``year`` as one row per LP generator.

    Rows come from the EIA-860 generator parquet filtered to
    ``balancing_authority_code == "MISO"`` (rule 24 [R-REGISTRY]: BA code, not
    state), so ``plant_code`` is exactly the plant set the LP dispatches.
    """
    gens = load_fleet_from_csv("MISO", year=year)
    return pd.DataFrame(
        [
            {
                "plant_code": int(g.plant_code),
                "klass": str(g.plant_group),
                "pmax_mw": float(g.pmax_mw),
                "heat_rate": float(g.heat_rate),
                "state": str(g.state),
            }
            for g in gens
            if g.plant_code is not None
        ]
    )


def model_trough_mw(year: int) -> dict[str, float]:
    """Keeper-bundle P1 generation at h1-h3, by class (MW, mean over hours)."""
    c = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    wide = c.pivot_table(index="hour", columns="klass", values="mw")
    trough = wide[(wide.index % 24).isin(TROUGH)]
    return {k: float(trough[k].mean()) for k in PAIRS if k in wide.columns}


def campd_miso_units(year: int, plant_codes: set[int]) -> pd.DataFrame:
    """CAMPD hourly unit rows for MISO-fleet plants, on the model's calendar.

    Reads only the state extracts that feed MISO, filters each to the
    BA-resolved plant set as it is read (so the full multi-state hourly frame
    is never materialised), tags each unit with its measured technology family
    and maps the CAMPD clock onto the model's 8760-hour index.
    """
    frames = []
    for state in states_for_iso("MISO"):
        path = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            print(f"    [warn] missing CAMPD extract {path.name}")
            continue
        df = pd.read_parquet(path, columns=UNIT_COLS)
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(plant_codes)]
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["plant_code"] = out["facilityId"].astype(int)
    dt = pd.to_datetime(out["date"])
    out["hoy"] = _hour_index_8760(dt.dt.month, dt.dt.day, out["hour"])
    out = out[out["hoy"] >= 0]  # rule 8 [R-8760]: Feb 29 dropped
    out["family"] = [
        unit_family(t, f)
        for t, f in zip(out["unitType"], out["primaryFuelInfo"], strict=True)
    ]
    out["grossLoad"] = out["grossLoad"].fillna(0.0)
    out["opTime"] = out["opTime"].fillna(0.0)
    out["heatInput"] = out["heatInput"].fillna(0.0)
    return out


def phase_1b(fleet: pd.DataFrame, campd: pd.DataFrame, model_mw: dict) -> None:
    """Robustness sensitivity + the measured trough heat rate.

    Two questions the headline ratio cannot answer on its own:

    1. **Mixed-plant sensitivity.** 39 % of model ``ST_GAS`` capacity sits on a
       plant carrying another model class. If a matched plant's CAMPD steam
       unit is really the HRSG of a combined cycle, its output would inflate
       the measured ``ST_GAS``. Re-running on single-class plants only bounds
       that contamination.
    2. **Measured heat rate at the trough.** Once the *quantity* is confirmed
       right, the level offset is a price question, and the price of these
       units is ``heat_rate x fuel + vom``. ``heatInput / grossLoad`` is the
       measured GROSS heat rate; the model's is NET, and gross understates net
       (same fuel, more MWh in the denominator), so a measured value already
       *below* the model's understates the true gap.
    """
    print("\n  -- Phase 1b: robustness + measured heat rate " + "-" * 30)
    grp = fleet.groupby("plant_code")["klass"].nunique()
    single = set(grp[grp == 1].index)

    for klass, fam in PAIRS.items():
        sub = fleet[fleet["klass"] == klass]
        plants = set(sub["plant_code"].unique())
        u = campd[campd["plant_code"].isin(plants) & (campd["family"] == fam)]
        tr = u[(u["hoy"] % 24).isin(TROUGH)]
        n = tr["hoy"].nunique()

        # (1) single-class-plant sensitivity
        tr_s = tr[tr["plant_code"].isin(single)]
        cap_all = float(sub["pmax_mw"].sum())
        cap_s = float(sub[sub["plant_code"].isin(single)]["pmax_mw"].sum())
        meas_s = float(tr_s["grossLoad"].sum()) / n if n else 0.0
        # scale the single-class measurement up to full class capacity, so the
        # comparison stays against the whole modelled class
        scaled = meas_s * (cap_all / cap_s) if cap_s else float("nan")
        mdl = model_mw.get(klass, float("nan"))

        # (2) measured gross heat rate at the trough
        gl = float(tr["grossLoad"].sum())
        hi = float(tr["heatInput"].sum())
        hr_meas = hi / gl if gl > 0 else float("nan")
        hr_model = float(
            np.average(sub["heat_rate"], weights=sub["pmax_mw"].clip(lower=1e-9))
        )
        print(
            f"    {klass:<10s} single-class-plant R = "
            f"{(scaled / mdl if mdl else float('nan')):.3f} "
            f"(on {cap_s / cap_all:.0%} of class capacity, scaled to full)"
        )
        # (3) the weighting confound. hr_model is CAPACITY-weighted over the
        # whole class; hr_meas is GENERATION-weighted over units that actually
        # ran overnight, which selects the efficient tail. Two controls:
        # the same measured units over ALL 8760 h (does the trough select?),
        # and the model heat rate restricted to plants that ever ran (does the
        # class average carry never-running junk?).
        gl_a = float(u["grossLoad"].sum())
        hr_all = float(u["heatInput"].sum()) / gl_a if gl_a > 0 else float("nan")
        ran = set(u[u["grossLoad"] > 0]["plant_code"].unique())
        sub_ran = sub[sub["plant_code"].isin(ran)]
        hr_model_ran = (
            float(
                np.average(
                    sub_ran["heat_rate"], weights=sub_ran["pmax_mw"].clip(lower=1e-9)
                )
            )
            if not sub_ran.empty
            else float("nan")
        )
        print(
            f"    {klass:<10s} trough heat rate: measured GROSS "
            f"{hr_meas:5.2f} vs model NET {hr_model:5.2f} MMBtu/MWh "
            f"-> model is {hr_model / hr_meas - 1:+.1%}"
        )
        print(
            f"    {klass:<10s}   controls: measured all-hours {hr_all:5.2f} "
            f"(trough selection {hr_meas / hr_all - 1:+.1%}) | "
            f"model over ever-running plants {hr_model_ran:5.2f} "
            f"(class-average bias {hr_model / hr_model_ran - 1:+.1%})"
        )


def phase_1c(year: int, fleet: pd.DataFrame, campd: pd.DataFrame) -> None:
    """Reconcile the three sources' overnight gas, because they disagree.

    miso-114 measured a 3.4-3.9 GW overnight gas hole (model minus EIA-930
    ``NG: NG``). This probe finds the model reproduces CC, CT and ST gas at
    CAMPD-covered plants to within ~5 %. Both cannot be describing the same
    quantity, so the three bases are put side by side rather than left in
    contradiction: the model's ALL-gas classes, CAMPD's metered gas at MISO
    fleet plants, and EIA-930's reported MISO gas net generation.
    """
    gas_classes = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP")
    c = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    wide = c.pivot_table(index="hour", columns="klass", values="mw")
    tr = wide[(wide.index % 24).isin(TROUGH)]
    model_gas = float(sum(tr[k].mean() for k in gas_classes if k in wide.columns))

    # CAMPD: every metered gas-family unit at a MISO-fleet plant, no class match
    gas_fams = {"CC", "CT", "ST_GAS"}
    u = campd[campd["family"].isin(gas_fams)]
    trc = u[(u["hoy"] % 24).isin(TROUGH)]
    n = trc["hoy"].nunique()
    campd_gas = float(trc["grossLoad"].sum()) / n if n else float("nan")

    path = ROOT / "data/raw/eia-930-hourly/MISO hourly.parquet"
    e930 = float("nan")
    if path.exists():
        d = pd.read_parquet(path)
        # Same construction as the miso-114 probe: "Local time", leap day
        # dropped, single-hour holes interpolated, then a chronological index
        # so hour % 24 is the same slice both sides use.
        d["ts"] = pd.to_datetime(d["Local time"])
        d = d[
            (d["ts"] >= pd.Timestamp(f"{year}-01-01"))
            & (d["ts"] < pd.Timestamp(f"{year + 1}-01-01"))
        ].copy()
        d = d[~((d.ts.dt.month == 2) & (d.ts.dt.day == 29))].reset_index(drop=True)
        num = d.select_dtypes(include=[float, int]).columns
        d[num] = d[num].interpolate(limit_direction="both")
        d["hoy"] = np.arange(len(d))
        e930 = float(d[(d["hoy"] % 24).isin(TROUGH)]["NG: NG"].mean())

    print(
        f"    Phase 1c gas reconciliation (h1-3, MW): model all-gas {model_gas:7,.0f}"
        f" | CAMPD metered {campd_gas:7,.0f} | EIA-930 NG:NG {e930:7,.0f}"
    )
    print(
        f"      model - CAMPD {model_gas - campd_gas:+7,.0f} | "
        f"model - EIA930 {model_gas - e930:+7,.0f} | "
        f"CAMPD - EIA930 {campd_gas - e930:+7,.0f}"
    )


def main() -> None:
    print("=" * 78)
    print("miso-115 Phase-1 — MISO trough marginal unit: measured vs modelled")
    print("=" * 78)
    print(
        "\nPre-registered decision rule (R = measured/model):\n"
        "  MIS-SPECIFIED  R <= 0.60 in >=2/3 years AND R < 1 in all 3\n"
        "  COMPARABLE     R >= 0.75 in >=2/3 years\n"
        "  INCONCLUSIVE   otherwise -> refuse, no charter\n"
    )

    ratios: dict[str, list[float]] = {k: [] for k in PAIRS}
    combined_ratios: list[float] = []

    for year in YEARS:
        print("\n" + "-" * 78)
        print(f"YEAR {year}")
        print("-" * 78)

        fleet = model_fleet(year)
        model_mw = model_trough_mw(year)

        # --- K2 footprint: MISO membership is BA-coded, not state-coded ------
        miso_plants = set(fleet["plant_code"].unique())
        print(
            f"\n  MISO fleet (BA code): {len(miso_plants)} plants, "
            f"{fleet['pmax_mw'].sum():,.0f} MW across "
            f"{fleet['state'].nunique()} states"
        )

        campd = campd_miso_units(year, miso_plants)
        if campd.empty:
            print("  [FATAL] no CAMPD rows matched the MISO fleet")
            return

        # Plants carrying more than one model class: their CAMPD units are
        # apportioned by measured family, so report the exposure (K5).
        grp = fleet.groupby("plant_code")["klass"].nunique()
        mixed = set(grp[grp > 1].index)

        year_meas = 0.0
        year_model = 0.0
        for klass, fam in PAIRS.items():
            sub = fleet[fleet["klass"] == klass]
            plants = set(sub["plant_code"].unique())
            cap_model = float(sub["pmax_mw"].sum())

            u = campd[campd["plant_code"].isin(plants)]
            u_fam = u[u["family"] == fam]

            # --- K1 coverage: model capacity with ANY matching CAMPD unit ----
            covered = set(u_fam["plant_code"].unique())
            cap_covered = float(sub[sub["plant_code"].isin(covered)]["pmax_mw"].sum())
            cov = cap_covered / cap_model if cap_model else float("nan")

            # --- K5 mapping fidelity: matched plants' units that disagree ----
            fam_mw = u.groupby("family")["grossLoad"].sum()
            tot_mw = float(fam_mw.sum())
            agree = float(fam_mw.get(fam, 0.0)) / tot_mw if tot_mw else float("nan")

            trough = u_fam[(u_fam["hoy"] % 24).isin(TROUGH)]
            n_hours = trough["hoy"].nunique()
            meas = float(trough["grossLoad"].sum()) / n_hours if n_hours else 0.0
            mdl = model_mw.get(klass, float("nan"))
            r = meas / mdl if mdl else float("nan")
            ratios[klass].append(r)
            if klass in VERDICT_CLASSES:  # the pre-registered scope
                year_meas += meas
                year_model += mdl

            mixed_cap = float(sub[sub["plant_code"].isin(mixed)]["pmax_mw"].sum())
            print(
                f"\n  {klass:<10s} model {mdl:7,.0f} MW | measured {meas:7,.0f} MW"
                f" | R = {r:.3f}"
            )
            print(
                f"    K1 coverage  {cov:6.1%} of model capacity "
                f"({cap_covered:,.0f} / {cap_model:,.0f} MW) "
                f"across {len(covered)}/{len(plants)} plants"
            )
            print(
                f"    K5 family    {agree:6.1%} of matched-plant CAMPD MWh is "
                f"'{fam}'  (other families: "
                + ", ".join(
                    f"{k}={v / tot_mw:.1%}" for k, v in fam_mw.items() if k != fam
                )
                + ")"
            )
            print(
                f"    K5 mixed     {mixed_cap / cap_model:6.1%} of model capacity "
                "sits on a multi-class plant"
            )
            print(
                f"    trough hours {n_hours} | units {u_fam['unitId'].nunique()} "
                f"| plant-hours with opTime>0: "
                f"{(trough['opTime'] > 0).mean():.1%}"
            )

        rc = year_meas / year_model if year_model else float("nan")
        combined_ratios.append(rc)
        print(
            f"\n  COMBINED CT_PEAKER+ST_GAS  model {year_model:7,.0f} MW | "
            f"measured {year_meas:7,.0f} MW | R = {rc:.3f}"
        )

        # --- K3 clock sanity: the measured diurnal shape must trough here ----
        hod = campd.groupby(campd["hoy"] % 24)["grossLoad"].mean()
        print(
            f"    K3 clock: CAMPD MISO fossil diurnal min at h{int(hod.idxmin())}, "
            f"max at h{int(hod.idxmax())} "
            f"(trough window h1-3 is {'CONSISTENT' if hod.idxmin() <= 5 else 'INCONSISTENT'})"
        )

        phase_1b(fleet, campd, model_mw)
        phase_1c(year, fleet, campd)

    # ------------------------------------------------------------------ #
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    for klass in PAIRS:
        rs = ratios[klass]
        print(f"  {klass:<10s} R = " + " / ".join(f"{r:.3f}" for r in rs))
    print(
        "  COMBINED (pre-registered scope: CT_PEAKER+ST_GAS)   R = "
        + " / ".join(f"{r:.3f}" for r in combined_ratios)
    )

    r = np.array(combined_ratios)
    if (r <= 0.60).sum() >= 2 and (r < 1).all():
        v = "MIS-SPECIFIED -> charter Phase 2 (single-delta A/B)"
    elif (r >= 0.75).sum() >= 2:
        v = "COMPARABLE -> pricing question on the same units; REFUSE, no solve"
    else:
        v = "INCONCLUSIVE -> defaults to refuse; no charter"
    print(f"\n  Pre-registered verdict: {v}")


if __name__ == "__main__":
    main()
