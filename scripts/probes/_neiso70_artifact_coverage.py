"""neiso-70 STEP 1 probe: coverage, selection and reach of BOTH measured
heat-rate artifacts, before any arm is armed.

No LP. Modelled on ``_caiso146_ct_hr_coverage.py`` (CT) and
``_caiso147_chp_coverage.py`` (CHP), merged so one run answers the same
questions for both levers on NEISO's own fleet (rule 25 ``[R-ISO-SCOPE]`` —
nothing is transferred from CAISO/PJM/NYISO/MISO; this derives NEISO's own
numbers).

Reported per artifact, per the session's STEP 1 contract:

1. Row count, and how many rows the loader actually applies (``flag == "ok"``)
   versus each distinct exclusion cause.
2. Capacity coverage of the target class AND — the number that matters for an
   offer swap — the covered share of the class's own metered CAMPD energy.
3. Adverse selection: covered vs uncovered capacity-weighted incumbent rate.
4. Direction and size of the capacity-weighted move, reported in BOTH
   directions so a one-sided or two-sided result is measured rather than
   assumed to mirror any precedent ISO.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_neiso70_artifact_coverage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

ISO = "NEISO"
YEARS = (2023, 2024, 2025)
CT_CLASS = "CT_PEAKER"
CHP_CLASSES = ("CC_CHP", "CT_CHP")
CT_UNIT_TYPE = "combustion turbine"
UNIT_DIR = RAW_DIR / "campd-unit-level"


def model_class_plants(target: str) -> pd.DataFrame:
    """Per-plant capacity and capacity-weighted incumbent heat rate for ``target``.

    The incumbent rate is read off the SHIPPED fleet, i.e. after every boundary
    repair the loader applies, so the "model" side of the comparison is what
    the LP would actually have charged.
    """
    fleet = load_fleet_from_csv(ISO, get_iso_config(ISO))
    rows: list[dict] = []
    for gen in fleet:
        if gen.plant_group != target:
            continue
        rows.append(
            {
                "plant_code": int(gen.plant_code or 0),
                "name": gen.name,
                "pmax_mw": float(gen.pmax_mw),
                "heat_rate": float(gen.heat_rate),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["hr_mw"] = df["heat_rate"] * df["pmax_mw"]
    out = df.groupby("plant_code", as_index=False).agg(
        pmax_mw=("pmax_mw", "sum"), hr_mw=("hr_mw", "sum"), name=("name", "first")
    )
    out["model_hr"] = out["hr_mw"] / out["pmax_mw"]
    return out.drop(columns="hr_mw").sort_values("pmax_mw", ascending=False)


def campd_energy(ct_only: bool) -> tuple[pd.DataFrame, set[int]]:
    """Pooled CAMPD metered gross MWh per plant over ``YEARS``.

    ``ct_only`` restricts to ``unitType == 'Combustion turbine'`` rows, which is
    the right denominator for the CT artifact (a mixed facility contributes only
    its turbines). The CHP artifact is plant-grain, so it uses the whole plant.
    Returns the energy frame and every facility id seen in the extracts, so an
    uncovered plant can be attributed to the Part-75 boundary rather than to a
    screen failure.
    """
    frames: list[pd.DataFrame] = []
    all_ids: set[int] = set()
    cols = ["facilityId", "unitId", "unitType", "grossLoad"]
    for state in campd.states_for_iso(ISO):
        for year in YEARS:
            path = UNIT_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(path, columns=cols)
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            all_ids |= set(df["facilityId"].dropna().astype(int).tolist())
            if ct_only:
                df = df[
                    df["unitType"].astype(str).str.strip().str.casefold()
                    == CT_UNIT_TYPE
                ]
            if not df.empty:
                frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["plant_code", "campd_gross_mwh"]), all_ids
    pooled = pd.concat(frames, ignore_index=True).dropna(subset=["grossLoad"])
    pooled = pooled[pooled["grossLoad"] > 0.0]
    energy = (
        pooled.groupby("facilityId", as_index=False)["grossLoad"]
        .sum()
        .rename(columns={"facilityId": "plant_code", "grossLoad": "campd_gross_mwh"})
    )
    energy["plant_code"] = energy["plant_code"].astype(int)
    return energy, all_ids


def report_ct() -> None:
    """Coverage / selection / direction for the measured CT loaded-rate artifact."""
    art = pd.read_csv(PROCESSED_DIR / f"campd_ct_heat_rates_{ISO}.csv")
    units = pd.read_csv(PROCESSED_DIR / f"campd_ct_heat_rates_{ISO}_units.csv")
    fleet = model_class_plants(CT_CLASS)
    ct_energy, campd_ids = campd_energy(ct_only=True)
    ok = art[art["flag"] == "ok"]

    print("=" * 78)
    print(f"LEVER 1 — measured_ct_heat_rates  ({CT_CLASS})")
    print("=" * 78)
    print(
        f"1. ARTIFACT — {len(art)} plant rows, {len(ok)} applied (flag=='ok'), "
        f"{len(art) - len(ok)} flagged out by the physical band"
    )
    print(f"   per-unit detail rows: {len(units)}")
    if len(art) != len(ok):
        print(art[art["flag"] != "ok"].to_string(index=False))
    print(f"   flag census: {art['flag'].value_counts().to_dict()}")

    total_mw = float(fleet["pmax_mw"].sum())
    cov_mw = float(ok["class_capacity_mw"].sum())
    merged = fleet.merge(ct_energy, on="plant_code", how="left")
    merged["campd_gross_mwh"] = merged["campd_gross_mwh"].fillna(0.0)
    merged["covered"] = merged["plant_code"].isin(set(ok["plant_code"]))
    e_tot = float(merged["campd_gross_mwh"].sum())
    e_cov = float(merged.loc[merged["covered"], "campd_gross_mwh"].sum())

    print(
        f"\n2. COVERAGE — capacity {cov_mw:,.0f} / {total_mw:,.0f} MW "
        f"({100 * cov_mw / total_mw:.1f} %), plants {len(ok)} / {len(fleet)}"
    )
    print(
        f"   metered CAMPD CT energy {e_cov / 1e6:,.3f} / {e_tot / 1e6:,.3f} TWh "
        f"({100 * e_cov / e_tot if e_tot else float('nan'):.1f} % of the class's "
        f"own measured energy)"
    )

    print("\n3. EXCLUSIONS — why each uncovered plant is uncovered")
    unc = merged[~merged["covered"]].copy()

    def _cause(r: pd.Series) -> str:
        if int(r["plant_code"]) not in campd_ids:
            return "A_no_campd_account"
        if float(r["campd_gross_mwh"]) <= 0.0:
            return "B_campd_but_no_CT_unit"
        return "C_no_loaded_window"

    if not unc.empty:
        unc["cause"] = unc.apply(_cause, axis=1)
        grp = unc.groupby("cause").agg(
            plants=("plant_code", "size"),
            mw=("pmax_mw", "sum"),
            campd_gwh=("campd_gross_mwh", lambda s: s.sum() / 1e3),
        )
        grp["pct_class_mw"] = 100 * grp["mw"] / total_mw
        print(grp.to_string())
        print("\n   uncovered plants, largest 15:")
        print(
            unc.sort_values("pmax_mw", ascending=False)
            .head(15)[
                [
                    "plant_code",
                    "name",
                    "pmax_mw",
                    "model_hr",
                    "campd_gross_mwh",
                    "cause",
                ]
            ]
            .to_string(index=False)
        )
        print(
            f"\n   uncovered size profile: median {unc['pmax_mw'].median():.1f} MW, "
            f"p90 {unc['pmax_mw'].quantile(0.9):.1f} MW, "
            f"max {unc['pmax_mw'].max():.1f} MW"
        )
        print(
            f"   covered   size profile: median "
            f"{merged.loc[merged['covered'], 'pmax_mw'].median():.1f} MW"
        )
        cov_hr = np.average(
            merged.loc[merged["covered"], "model_hr"],
            weights=merged.loc[merged["covered"], "pmax_mw"],
        )
        unc_hr = np.average(unc["model_hr"], weights=unc["pmax_mw"])
        print(
            f"   ADVERSE SELECTION — incumbent HR covered cap-wt {cov_hr:.3f} "
            f"vs uncovered cap-wt {unc_hr:.3f} MMBtu/MWh "
            f"(delta {unc_hr - cov_hr:+.3f})"
        )

    print("\n4. DISTRIBUTION — measured vs model, BOTH directions")
    d = ok.copy()
    d["delta"] = d["heat_rate"] - d["model_heat_rate_egrid"]
    cheaper, dearer = d[d["delta"] < 0], d[d["delta"] > 0]
    print(
        f"   cheaper (measured < model): {len(cheaper)} plants, "
        f"{cheaper['class_capacity_mw'].sum():,.0f} MW"
    )
    print(
        f"   dearer  (measured > model): {len(dearer)} plants, "
        f"{dearer['class_capacity_mw'].sum():,.0f} MW"
    )
    print(
        f"   |delta| > 0.5 MMBtu/MWh: {(d['delta'].abs() > 0.5).sum()} plants; "
        f"> 1.0: {(d['delta'].abs() > 1.0).sum()}"
    )
    w = d["class_capacity_mw"].to_numpy(float)
    capwt = np.average(d["delta"], weights=w)
    print(
        f"   capacity-weighted delta {capwt:+.3f} MMBtu/MWh "
        f"({100 * capwt / np.average(d['model_heat_rate_egrid'], weights=w):+.1f} %)"
    )
    g = d["gross_mwh"].to_numpy(float)
    print(
        f"   generation-weighted delta "
        f"{np.average(d['delta'], weights=g):+.3f} MMBtu/MWh"
    )
    print(
        f"   ratio model/measured: min {d['model_over_measured'].min():.3f}, "
        f"median {d['model_over_measured'].median():.3f}, "
        f"max {d['model_over_measured'].max():.3f}"
    )
    print("\n   every applied row, by |delta| x capacity:")
    d["impact"] = d["delta"].abs() * d["class_capacity_mw"]
    print(
        d.sort_values("impact", ascending=False)[
            [
                "plant_code",
                "plant_name",
                "class_capacity_mw",
                "n_units",
                "loaded_hours",
                "heat_rate",
                "model_heat_rate_egrid",
                "delta",
            ]
        ].to_string(index=False)
    )


def report_chp() -> None:
    """Coverage / selection / direction for the measured CHP power-only artifact."""
    art = pd.read_csv(PROCESSED_DIR / f"chp_power_only_heat_rates_{ISO}.csv")
    energy, _ = campd_energy(ct_only=False)
    emap = dict(zip(energy["plant_code"], energy["campd_gross_mwh"]))
    art["campd_mwh"] = art["plant_code"].astype(int).map(emap).fillna(0.0)

    print("\n" + "=" * 78)
    print(f"LEVER 2 — measured_chp_heat_rates  ({'/'.join(CHP_CLASSES)})")
    print("=" * 78)
    ok = art[art["flag"] == "ok"]
    print(
        f"1. ARTIFACT — {len(art)} (plant, class) rows, {len(ok)} applied "
        f"(flag=='ok'), {len(art) - len(ok)} excluded"
    )
    print(f"   flag census: {art['flag'].value_counts().to_dict()}")

    print("\n2. COVERAGE by class — capacity AND the class's own metered energy")
    for cls in CHP_CLASSES:
        s = art[art["plant_group"] == cls]
        if s.empty:
            continue
        sok = s[s["flag"] == "ok"]
        cap_c, cap_t = sok["class_capacity_mw"].sum(), s["class_capacity_mw"].sum()
        # Energy is metered per PLANT: credit it once per plant, not once per row.
        e_ok = sok.drop_duplicates("plant_code")["campd_mwh"].sum()
        e_all = s.drop_duplicates("plant_code")["campd_mwh"].sum()
        print(
            f"   {cls}: {len(sok)}/{len(s)} rows  {cap_c:.0f}/{cap_t:.0f} MW "
            f"({100 * cap_c / cap_t if cap_t else float('nan'):.1f} %)  |  "
            f"metered CAMPD energy {e_ok / 1e6:.3f}/{e_all / 1e6:.3f} TWh "
            f"({100 * e_ok / e_all if e_all else float('nan'):.1f} %)"
        )

    print("\n3. ADVERSE SELECTION (eGRID CREDITED rate, cap-weighted)")
    for cls in CHP_CLASSES:
        s = art[art["plant_group"] == cls]
        for lab, sub in (
            ("covered ", s[s.flag == "ok"]),
            ("excluded", s[s.flag != "ok"]),
        ):
            sub = sub[np.isfinite(sub.heat_rate_credited) & (sub.class_capacity_mw > 0)]
            if sub.empty:
                continue
            w = sub["class_capacity_mw"]
            print(
                f"   {cls} {lab}: n={len(sub):>3} {w.sum():7.1f} MW  "
                f"credited {np.average(sub.heat_rate_credited, weights=w):6.3f}  "
                f"thermal_share "
                f"{np.average(sub.thermal_share.fillna(0), weights=w):.3f}"
            )

    print("\n4. DIRECTION — applied rows, per class, BOTH directions")
    for cls in CHP_CLASSES:
        sok = art[(art["plant_group"] == cls) & (art["flag"] == "ok")]
        if sok.empty:
            continue
        w = sok["class_capacity_mw"].to_numpy(float)
        inc = np.average(sok["model_heat_rate"], weights=w)
        new = np.average(sok["heat_rate"], weights=w)
        dearer = int((sok["heat_rate"] > sok["model_heat_rate"]).sum())
        cheaper = int((sok["heat_rate"] < sok["model_heat_rate"]).sum())
        print(
            f"   {cls}: cap-wt {inc:.3f} -> {new:.3f} MMBtu/MWh "
            f"({100 * (new - inc) / inc:+.1f} %); {dearer} dearer / "
            f"{cheaper} cheaper of {len(sok)} applied"
        )
        print(
            sok[
                [
                    "plant_code",
                    "plant_name",
                    "class_capacity_mw",
                    "thermal_share",
                    "model_heat_rate",
                    "heat_rate",
                    "cems_vs_egrid_total",
                ]
            ].to_string(index=False)
        )

    print("\n5. not_unfired_topping — the EPA-envelope exclusions")
    nt = art[art["flag"] == "not_unfired_topping"]
    if not nt.empty:
        print(
            f"   n={len(nt)}  {nt['class_capacity_mw'].sum():.0f} MW  "
            f"thermal_share min {nt['thermal_share'].min():.3f} "
            f"median {nt['thermal_share'].median():.3f} "
            f"max {nt['thermal_share'].max():.3f} (gate 0.50)"
        )
        print(
            f"   power-only rate they WOULD have taken: median "
            f"{nt['heat_rate'].median():.2f}, max {nt['heat_rate'].max():.1f} "
            f"MMBtu/MWh"
        )


def main() -> int:
    """Print the STEP 1 coverage/selection report for both NEISO artifacts."""
    report_ct()
    report_chp()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
