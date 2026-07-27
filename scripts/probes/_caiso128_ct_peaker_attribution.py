"""caiso-128 derive: why the CAISO CT_PEAKER fleet never clears, per plant and zone.

Owner lead (2026-07-27): "CT peakers never run in my model when they do in
reality, and it's centralised in LA Basin and NP15 — Sentinel and Walnut Creek
the worst LA-Basin offenders, Panoche the worst in NP15; there must be an RA
commitment element."

Measurement-only (NO solve, nothing armed). Reads a FULL bundle's unit-hour
``dispatch/`` frame (a slim keeper bundle does not carry one — replay first),
the ``floors/<year>_P1.npz`` the P1 LP actually saw, a no-LP
``run_year(fleet_only=True)`` reconstruction for capability and offer prices,
CAMPD facility CEMS for the measured side, and eGRID PLNT for the published
plant heat rate. Answers four questions in order:

  1. PER-ZONE: is the CT under-dispatch locational, or fleet-wide?
  2. PER-PLANT: model vs CEMS energy, RUN-HOURS and peak MW, with tranches
     summed per plant-hour FIRST (a CT plant is 12 LP tranche units; taking a
     max over tranche ROWS reports one tranche's peak and understates the
     plant by ~10x).
  3. IS IT COMMITMENT? Hours of binding RA/bridge ``min_gen`` on each plant,
     straight from the floors npz — an RA must-offer element, if present,
     shows up here.
  4. IS IT PRICE? The plant's cheapest AVAILABLE tranche offer against the
     hour's CA lambda, and the tranche heat rates against the CEMS-measured
     near-full-load heat rate (heat input / gross load over hours above half
     the plant's observed peak — the loading-conditional rate an ENERGY offer
     should carry; startup fuel belongs in the startup cost, not here) and
     against the eGRID published plant rate.

Usage:
    PYTHONPATH=.:src:scripts:scripts/probes .venv/bin/python \
        scripts/probes/_caiso128_ct_peaker_attribution.py \
        --bundle results/probes/caiso127_replay --year 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

CAMPD = REPO / "data" / "raw" / "campd-facility-level"
EGRID = REPO / "data" / "raw" / "fleet-egrid" / "egrid2024_data.xlsx"
TRANCHES = REPO / "data" / "raw" / "_processed-legacy" / "thermal_tranches_CAISO.csv"
# LA-Basin facilityId -> ORISPL pins (the _caiso102_evening_merit crosswalk).
LA_BASIN = {"315": 62115, "335": 62116, "330": 57901}
# CEMS-visible model classes, in the order the cross-class summary reports them.
CEMS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "CT_PEAKER", "COAL")


def plant_names() -> dict[int, str]:
    """Return ``{plant_code: name}`` from the committed CAISO tranche artifact."""
    if not TRANCHES.exists():
        return {}
    frame = pd.read_csv(TRANCHES)
    return dict(zip(frame["plant_code"].astype(int), frame["name"].astype(str)))


def cems_plant_hourly(year: int) -> pd.DataFrame:
    """Return CAMPD CA facility CEMS aggregated to (plant, date, hour)."""
    frame = pd.read_parquet(
        CAMPD / f"CA_{year}.parquet",
        columns=["facilityId", "date", "hour", "grossLoad", "heatInput"],
    )
    fid = frame["facilityId"].astype(str)
    pc = pd.to_numeric(fid.map(LA_BASIN).fillna(pd.to_numeric(fid, errors="coerce")))
    return (
        frame.assign(pc=pc)
        .groupby(["pc", "date", "hour"], observed=True)[["grossLoad", "heatInput"]]
        .sum()
        .reset_index()
    )


def cems_stats(hourly: pd.DataFrame) -> pd.DataFrame:
    """Return per-plant CEMS energy, run-hours, peak MW and heat rates.

    ``hr_all`` is the annual heat input / gross load over generating hours;
    ``hr_load`` restricts to hours above half the plant's observed peak — the
    loading-conditional rate an energy offer should carry.
    """
    rows = []
    for pc, sub in hourly[hourly["grossLoad"] > 1.0].groupby("pc"):
        peak = float(sub["grossLoad"].max())
        hi = sub[sub["grossLoad"] > 0.5 * peak]
        rows.append(
            {
                "plant_code": int(pc),
                "cems_mwh": float(sub["grossLoad"].sum()),
                "cems_hrs": int(len(sub)),
                "cems_pk": peak,
                "hr_all": float(sub["heatInput"].sum() / sub["grossLoad"].sum()),
                "hr_load": (
                    float(hi["heatInput"].sum() / hi["grossLoad"].sum())
                    if len(hi)
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def egrid_heat_rates() -> dict[int, float]:
    """Return ``{ORISPL: PLHTRT}`` (MMBtu/MWh) from the eGRID plant sheet."""
    if not EGRID.exists():
        return {}
    frame = pd.read_excel(EGRID, sheet_name="PLNT24", skiprows=1)
    key = next(c for c in frame.columns if str(c).upper().startswith("ORISPL"))
    hrc = next((c for c in frame.columns if "HTRT" in str(c).upper()), None)
    if hrc is None:
        return {}
    ok = frame[[key, hrc]].dropna()
    return {int(k): float(v) / 1000.0 for k, v in zip(ok[key], ok[hrc])}


def model_plant_hourly(bundle: Path, year: int, klass: str) -> pd.DataFrame:
    """Return ``klass`` model dispatch summed over tranches per (plant, hour)."""
    frame = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["plant_code", "klass", "zone", "hour", "mw"],
    )
    frame = frame[frame["klass"] == klass]
    return (
        frame.groupby(["plant_code", "zone", "hour"], observed=True)["mw"]
        .sum()
        .reset_index()
    )


def cross_class_summary(
    bundle: Path, year: int, state: dict, cem: pd.DataFrame
) -> None:
    """Print the per-class dispatch ratio and offer-heat-rate error distribution.

    The scope question behind the CT lane: is the offer heat rate wrong across
    the whole thermal fleet, or only in some classes? ``HRerr`` is the plant's
    CHEAPEST tranche heat rate against its CEMS loading-conditional rate, so a
    class whose curve is built on a good rate reads ~0.
    """
    fa = state["fleet_arrays"]
    pcs = np.asarray(fa.plant_code)
    hr = np.asarray(fa.heat_rate, dtype=float)
    groups = np.asarray(list(fa.plant_group), dtype=object)
    cem_hr = dict(zip(cem["plant_code"], cem["hr_load"]))
    cem_mwh = dict(zip(cem["plant_code"], cem["cems_mwh"]))

    print(f"\n=== 0. {year} CROSS-CLASS scope: dispatch ratio + offer HR error ===")
    print(
        f"{'class':<12} {'mdl TWh':>8} {'CEMS TWh':>9} {'ratio':>6} | "
        f"{'plants':>6} {'p25':>5} {'p50':>5} {'p75':>5} {'cap-wtd':>8}"
    )
    for klass in CEMS_CLASSES:
        ph = model_plant_hourly(bundle, year, klass)
        if ph.empty:
            continue
        by_plant = ph.groupby("plant_code", observed=True)["mw"].sum()
        errs, wts = [], []
        for pc in by_plant.index:
            sel = np.flatnonzero((pcs == pc) & (groups == klass))
            ref = cem_hr.get(int(pc), float("nan"))
            if not len(sel) or not (ref == ref) or ref <= 0.0:
                continue
            errs.append(100.0 * (float(hr[sel].min()) / ref - 1.0))
            wts.append(float(fa.pmax[sel].sum()))
        e, w = np.asarray(errs), np.asarray(wts)
        meas = sum(cem_mwh.get(int(p), 0.0) for p in by_plant.index)
        q = np.percentile(e, [25, 50, 75]) if len(e) else [float("nan")] * 3
        cw = float(np.average(e, weights=w)) if len(e) else float("nan")
        print(
            f"{klass:<12} {by_plant.sum() / 1e6:>8.2f} {meas / 1e6:>9.2f} "
            f"{by_plant.sum() / max(meas, 1.0):>6.2f} | {len(e):>6} "
            f"{q[0]:>5.0f} {q[1]:>5.0f} {q[2]:>5.0f} {cw:>8.0f}"
        )
    print(
        "  ratio = model / CEMS energy; HRerr = cheapest-tranche heat rate vs the "
        "CEMS\n  loading-conditional rate, % (a class built on a good rate reads ~0)."
    )


def main() -> None:
    """Run the four-question attribution for one bundle-year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/probes/caiso127_replay")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--klass", default="CT_PEAKER", help="model class to drill into")
    args = ap.parse_args()
    bundle, year, klass = Path(args.bundle), args.year, args.klass

    from _caiso105_evening_q1_pin import fleet_state
    from _caiso125_overnight_attribution import ca_lambda, system_frame

    names = plant_names()
    state = fleet_state(bundle, year)
    cross_class_summary(bundle, year, state, cems_stats(cems_plant_hourly(year)))
    ph = model_plant_hourly(bundle, year, klass)
    mdl = (
        ph.groupby(["plant_code", "zone"], observed=True)
        .agg(
            mwh=("mw", "sum"),
            hrs=("mw", lambda s: int((s > 0.1).sum())),
            pk=("mw", "max"),
        )
        .reset_index()
    )
    cem = cems_stats(cems_plant_hourly(year))
    m = mdl.merge(cem, on="plant_code", how="left").fillna(
        {"cems_mwh": 0.0, "cems_hrs": 0, "cems_pk": 0.0}
    )

    print(f"\n=== 1. {year} {klass} by ZONE (GWh) — is it locational? ===")
    z = m.groupby("zone", observed=True).agg(
        mdl=("mwh", "sum"), cems=("cems_mwh", "sum")
    )
    z = (z / 1e3).assign(ratio=lambda x: x.mdl / x.cems.replace(0, np.nan))
    print(z.round(2).to_string())
    print(
        f"\n  fleet: model {m['mwh'].sum() / 1e6:.2f} TWh vs CEMS "
        f"{m['cems_mwh'].sum() / 1e6:.2f} TWh over {len(m)} plants"
    )

    print(f"\n=== 2. {year} per plant (tranches summed per plant-hour) ===")
    m = m.sort_values("cems_mwh", ascending=False)
    print(
        f"{'plant':>6} {'zone':>9} {'name':<32} {'mGWh':>7} {'m h':>5} {'m pk':>6} "
        f"{'cGWh':>7} {'c h':>5} {'c pk':>6}"
    )
    for _, r in m.head(args.top).iterrows():
        print(
            f"{int(r.plant_code):>6} {r.zone:>9} {names.get(int(r.plant_code), '')[:31]:<32} "
            f"{r.mwh / 1e3:>7.1f} {int(r.hrs):>5} {r.pk:>6.0f} "
            f"{r.cems_mwh / 1e3:>7.1f} {int(r.cems_hrs):>5} {r.cems_pk:>6.0f}"
        )

    # --- 3/4: commitment vs price, on the LP's own floors and offers --------
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    cap = fa.pmax[:, None] * np.asarray(fa.availability, dtype=float)
    ids, pcs = list(fa.unit_ids), np.asarray(fa.plant_code)
    hr = np.asarray(fa.heat_rate, dtype=float)
    lam = ca_lambda(system_frame(bundle, year))
    npz = np.load(bundle / "floors" / f"{year}_P1.npz")
    fpos = {str(u): i for i, u in enumerate(npz["unit_ids"])}
    min_gen = np.asarray(npz["min_gen"], dtype=float)
    eg = egrid_heat_rates()

    print(f"\n=== 3/4. {year} commitment vs price, top {args.top} by CEMS energy ===")
    print(
        f"{'plant':>6} {'LP MW':>6} {'avail h':>7} {'RAfloor h':>9} | "
        f"{'HRmin':>6} {'eGRID':>6} {'CEMS':>6} {'err%':>6} | "
        f"{'mc p50':>7} {'h mc<=lam':>10} {'CEMS h':>7}"
    )
    for _, r in m.head(args.top).iterrows():
        pc = int(r.plant_code)
        sel = np.flatnonzero(pcs == pc)
        if not len(sel):
            continue
        c = cap[sel]
        avail = (c.sum(axis=0) > 0.1).sum()
        floor = np.zeros(c.shape[1])
        for i in sel:
            j = fpos.get(ids[i])
            if j is not None:
                floor += min_gen[j]
        cheap = np.where(c > 0.1, mc[sel], np.inf).min(axis=0)
        ok = np.isfinite(cheap)
        hr_min = float(hr[sel].min())
        cems_hr = float(r.hr_load) if r.hr_load == r.hr_load else float("nan")
        err = 100.0 * (hr_min / cems_hr - 1.0) if cems_hr == cems_hr else float("nan")
        print(
            f"{pc:>6} {fa.pmax[sel].sum():>6.0f} {int(avail):>7} "
            f"{int((floor > 0.1).sum()):>9} | {hr_min:>6.2f} "
            f"{eg.get(pc, float('nan')):>6.2f} {cems_hr:>6.2f} {err:>6.0f} | "
            f"{np.median(cheap[ok]):>7.2f} {int((cheap[ok] <= lam[ok]).sum()):>10} "
            f"{int(r.cems_hrs):>7}"
        )
    print(
        "\n  HRmin = the plant's CHEAPEST tranche heat rate (MMBtu/MWh); CEMS = "
        "loading-conditional (>50 % of observed peak); err% = HRmin vs CEMS.\n"
        "  RAfloor h = hours any RA/bridge min_gen binds on the plant, from the "
        "P1 floors npz."
    )


if __name__ == "__main__":
    main()
