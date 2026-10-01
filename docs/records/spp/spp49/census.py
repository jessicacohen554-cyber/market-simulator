"""SPP-49 phase 0 (zero LP): the two input-seam repairs measured on every ISO's keeper.

For each ISO the designated keeper's fleet is rebuilt with ``run_year(fleet_only=True)``
on the keeper's own recipe (``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``
— the only sanctioned fleet-only reconstruction) and the LP's OWN input arrays are read:
``mc_base``, ``fuel_prices``, ``availability`` (n_gen x 8760). No LP is solved.

Two censuses and one prediction, per ISO and year:

SEAM 1 — the EIA-923 own-month gas-price plausibility screen. For every gas row priced
from its OWN plant-month (``plant_month_price_grid``), the month is read against the
plant's state's EIA delivered-to-electric-power price (``N3045<ST>3``, $/Mcf / 1.036 —
the repo's ``_MCF_TO_MMBTU``; the plant's state from the F923 frame, never the fleet).
A month outside [LOW x R, HIGH x R] is flagged (low, of which negative separately; high);
a month whose reference is unpublished falls to ``N3045US3`` (counted); a month whose
reference is <= 0 cannot be banded and is left unscreened (counted). The construction is
declared in PRECOMMIT-spp-49 §2 before this ran; the band is never selected on anything.

SEAM 2 — the simple-cycle heat-rate floor. A plant whose EIA-860 operating rows are ALL
simple-cycle prime movers (``GT`` or ``IC`` — no steam cycle anywhere at the plant, so
no heat recovery can lift its annual rate above a bare turbine's) and whose eGRID plant
rate (the frame's ``heat_rate``) is below ``HEAT_RATE_BINS["gas_ct"]["aero"]`` is
flagged; its fleet rows and MW are counted. The reconciled value is the floor itself
(clamp) — the smallest repair that resolves the impossibility, the mirror of the CC
ceiling's condition 4.

PREDICTION — zero-LP, from the arrays alone: the screened fuel price ``fuel'`` on the
flagged own-reported rows and the floored heat rate ``hr'`` on the flagged CT rows give
``mc' = mc + hr x (fuel' - fuel) + (hr' - hr) x fuel'``. Reported: capacity-weighted
mean delta-mc per class, MW touched, and — where the keeper's committed hourly sidecars
exist — the re-clearing predictor (the SPP-46 / merit-order-lane construction, zones
POOLED here: the keeper's hourly thermal dispatch re-cleared against the re-priced
stack), for the DIRECTION and ORDER OF MAGNITUDE of the class-energy response. The
predictor is a bound, never a number to be matched (SPP-46 §5.2).

Gap-filled (nearby-pool) rows are left untouched in the ex-ante arithmetic; the pool
they draw from is rebuilt from screened months by the repair, so the ex-post rebuild
(``--post``) measures that second-order effect by differencing the repaired arrays
against the pre-edit arrays saved here.

Usage:
    uv run python docs/handoffs/spp49/census.py --iso SPP [--years 2023 2024 2025]
    uv run python docs/handoffs/spp49/census.py --iso ALL
    uv run python docs/handoffs/spp49/census.py --iso SPP --post   # after the edit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "docs/handoffs/spp49"
SCRATCH = Path(
    "/tmp/claude-0/-home-user-market-simulator/69eb6bae-6a21-5168-9aa6-aef31b40ec2d/scratchpad/spp49"
)
SCRATCH.mkdir(parents=True, exist_ok=True)

KEEPERS = {
    "CAISO": "caiso260_demand_vintage",
    "ERCOT": "ercot256_five_year_keeper",
    "MISO": "miso243_sppair_K",
    "NEISO": "neiso106_offerlevel",
    "NYISO": "nyiso213_summer_seam",
    "PJM": "pjm_debugb_inputclock_A",
    "SPP": "spp43_screened_B",
}
YEARS = (2023, 2024, 2025)
#: Recipe keys switched OFF for the fleet-only rebuild only, with the reason.
#: pjm_da_virtual_bids needs the gitignored PJM DataMiner2 virtual-bid corpus
#: (non-member redistribution restriction; absent from this checkout). It is a
#: DEMAND-SIDE overlay cleared in the LP and never reaches the fleet, the fuel
#: prices or the heat rates this census reads, so the arrays are identical
#: with it off. Stated, not silent.
REBUILD_OVERRIDES: dict[str, dict] = {"PJM": {"pjm_da_virtual_bids": False}}
LOW, HIGH = 0.5, 2.0  # the declared band (PRECOMMIT §2.1); never selected on anything
MCF_TO_MMBTU = 1.036  # market_sim.data.fuel.basis.ercot._MCF_TO_MMBTU
CT_FLOOR = 9.0  # HEAT_RATE_BINS["gas_ct"]["aero"] (constants.py, EIA Table 8)
SIMPLE_CYCLE_PM = {"GT", "IC"}  # EIA-860 prime movers with no steam cycle
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_H = np.repeat(np.arange(12), [d * 24 for d in MONTH_DAYS])
GAS_FUELS = ("gas_cc", "gas_ct", "gas_st", "gas_cc_ccs")
TOL = 0.25


def reference() -> dict[tuple[str, int, int], float]:
    """{(state, year, month): $/MMBtu} from the fetched N3045 workbooks (NaN-free)."""
    df = pd.read_csv(SCRATCH.parent / "n3045" / "n3045_all.csv")
    df = df.dropna(subset=["price_usd_mcf"])
    return {
        (r.state, int(r.year), int(r.month)): float(r.price_usd_mcf) / MCF_TO_MMBTU
        for r in df.itertuples()
    }


def ref_month(ref, state: str, year: int, month: int) -> tuple[float, str]:
    """Reference for a state-month: (value, provenance in {state, us, none})."""
    v = ref.get((state, year, month))
    if v is not None:
        return v, "state"
    v = ref.get(("US", year, month))
    if v is not None:
        return v, "us"
    return float("nan"), "none"


def rebuild(iso: str, year: int, tag: str) -> tuple[pd.DataFrame, dict]:
    """Rebuild the keeper fleet for one year; cache the rows + arrays in scratch."""
    rows_p = SCRATCH / f"rows_{tag}_{iso}_{year}.csv"
    arr_p = SCRATCH / f"arrays_{tag}_{iso}_{year}.npz"
    if rows_p.exists() and arr_p.exists():
        z = np.load(arr_p)
        return pd.read_csv(rows_p), {k: z[k] for k in z.files}
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / KEEPERS[iso]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    kw.update(REBUILD_OVERRIDES.get(iso, {}))
    gp = meta["gas_prices"].get(str(year))
    if gp is None:
        raise SystemExit(f"{iso} {year}: keeper meta carries no gas price for the year")
    r = run_year(year, iso, 8760, float(gp), {}, fleet_only=True, **kw)
    fleet, fa = r["fleet"], r["fleet_arrays"]
    mc, fp, av = r["mc_base"], r["fuel_prices"], fa.availability
    recs = []
    for g, gen in enumerate(fleet):
        a = av[g]
        recs.append(
            dict(
                g=g,
                unit_id=gen.unit_id,
                plant_code=int(gen.plant_code or 0),
                name=gen.name,
                zone=gen.zone,
                plant_group=gen.plant_group or "",
                fuel_type=gen.fuel_type,
                efficiency_bin=getattr(gen, "efficiency_bin", "") or "",
                pmax=float(gen.pmax_mw),
                heat_rate=float(fa.heat_rate[g]),
                vom=float(fa.vom[g]),
                state=str(getattr(gen, "state", "") or ""),
                mc_mean=float(mc[g].mean()),
                fuel_mean=float(fp[g].mean()),
                avail_mean=float(a.mean()),
            )
        )
    rows = pd.DataFrame(recs)
    rows.to_csv(rows_p, index=False)
    arrays = dict(
        mc=mc.astype(np.float32),
        fuel=fp.astype(np.float32),
        avail=av.astype(np.float32),
        demand=np.asarray(r["demand"]).astype(np.float32),
    )
    np.savez_compressed(arr_p, **arrays)
    return rows, arrays


def ct_only_plants(iso_plants: set[int]) -> pd.DataFrame:
    """Per plant: whether every OP EIA-860 row is prime mover GT, and the eGRID rate."""
    from market_sim.config.paths import active_eia860_dir
    from market_sim.data.fleet.eia860 import EIA_860_PARQUET_NAME

    df = pd.read_parquet(
        active_eia860_dir() / EIA_860_PARQUET_NAME,
        columns=["plant_id", "prime_mover", "status", "heat_rate", "energy_source",
                 "net_summer_capacity_mw", "nameplate_capacity_mw", "operating_year"],
    )
    df = df[df["status"].astype(str).str.strip().str.upper() == "OP"]
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df = df[df["plant_id"].isin(iso_plants)]
    pm = df["prime_mover"].astype(str).str.strip().str.upper()
    g = df.assign(is_gt=pm.isin(SIMPLE_CYCLE_PM)).groupby("plant_id").agg(
        n_rows=("is_gt", "size"),
        all_gt=("is_gt", "all"),
        heat_rate=("heat_rate", "first"),
        nameplate=("nameplate_capacity_mw", "sum"),
        summer=("net_summer_capacity_mw", "sum"),
        vintage_min=("operating_year", "min"),
        vintage_max=("operating_year", "max"),
    )
    return g


def census_year(iso: str, year: int, ref, tag: str, post: bool) -> dict:
    from market_sim.config.constants import HEAT_RATE_BINS
    from market_sim.data.eia923 import plant_month_price_grid
    from market_sim.data.fuel.plant_prices import _load_monthly_cache

    rows, arr = rebuild(iso, year, tag)
    mc, fuel, av = arr["mc"].astype(float), arr["fuel"].astype(float), arr["avail"].astype(float)
    # Seam 1 is reachable only where the keeper arms per-plant gas pricing (the
    # seam's own gate); the plant-month census is still reported for an unarmed
    # ISO ("if armed"), but its arrays carry no F923 price to screen.
    run_cfg = json.loads((REPO / "results/calibration" / KEEPERS[iso] / "run_config.json").read_text())
    seam1_armed = bool(run_cfg["scenario_config"].get("gas_plant_monthly_fuel_pricing"))
    n, T = mc.shape
    costs = _load_monthly_cache(None)
    plant_state = costs.groupby("plant_id")["state"].first()
    grid = plant_month_price_grid(costs, year, "Natural Gas")
    pg = rows.plant_group.fillna("").astype(str)
    klass = pg.where(pg != "", rows.fuel_type.astype(str)).to_numpy()
    is_gas = rows.fuel_type.isin(GAS_FUELS).to_numpy()
    gas_plants = set(int(p) for p in rows.plant_code[is_gas] if p > 0)
    gas_mw = float(rows.pmax[is_gas].sum())

    # ---- SEAM 1: plant-month census over the ISO's gas plants that own-report
    pm_rows = []
    fuel_s = fuel.copy()
    row_flag = np.zeros(n, dtype="<U8")
    for pc in sorted(gas_plants):
        own = grid.get(pc)
        if own is None:
            continue
        st = str(plant_state.get(pc, ""))
        for m in range(12):
            if np.isnan(own[m]):
                continue
            R, prov = ref_month(ref, st, year, m + 1)
            if prov == "none":
                kind = "unscreened_no_ref"
            elif R <= 0:
                kind = "unscreened_nonpos_ref"
            elif own[m] < 0:
                kind = "negative"
            elif own[m] < LOW * R:
                kind = "low"
            elif own[m] > HIGH * R:
                kind = "high"
            else:
                kind = "in_band"
            pm_rows.append(dict(iso=iso, year=year, plant_code=pc, state=st, month=m + 1,
                                own=float(own[m]), ref=R, ref_prov=prov, kind=kind))
            if kind in ("negative", "low", "high"):
                hit = (rows.plant_code.to_numpy() == pc) & is_gas
                if seam1_armed:
                    fuel_s[np.ix_(hit, MONTH_H == m)] = R
                for g in np.flatnonzero(hit):
                    row_flag[g] = kind if row_flag[g] in ("", "in_band") else row_flag[g]
    pmdf = pd.DataFrame(pm_rows)
    # ---- SEAM 2: CT-only plants below the floor
    hr = rows.heat_rate.to_numpy().astype(float)
    hr_s = hr.copy()
    ct = ct_only_plants(gas_plants)
    ct_hit = ct[(ct.all_gt) & (ct.heat_rate.astype(float) < CT_FLOOR)]
    ct_near = ct[(ct.all_gt) & (ct.heat_rate.astype(float) < CT_FLOOR) & (ct.heat_rate.astype(float) >= 8.0)]
    ct_rows = np.zeros(n, dtype=bool)
    for pc, r in ct_hit.iterrows():
        # only a row whose CARRIED rate is below the floor moves: the CAMPD-bin
        # path (ERCOT) carries tranche rates measured from CEMS, not the eGRID
        # plant rate, so a flagged plant can have rows the clamp never touches
        hit = (rows.plant_code.to_numpy() == int(pc)) & is_gas & (hr < CT_FLOOR)
        ct_rows |= hit
        # the repair clamps the plant rate to the floor (PRECOMMIT §2.2)
        hr_s[hit] = np.maximum(hr[hit], CT_FLOOR)
    # ---- PREDICTION from the arrays
    mc_s = mc + hr[:, None] * (fuel_s - fuel) + (hr_s - hr)[:, None] * fuel_s
    cap = rows.pmax.to_numpy()[:, None] * av
    touched = np.any(fuel_s != fuel, axis=1) | ct_rows
    by_class = []
    for k in sorted(set(klass[is_gas])):
        sel = (klass == k)
        w = cap[sel].sum()
        d = ((mc_s - mc)[sel] * cap[sel]).sum() / w if w else np.nan
        by_class.append(dict(iso=iso, year=year, klass=k, rows=int(sel.sum()),
                             mw=float(rows.pmax[sel].sum()),
                             rows_touched=int((sel & touched).sum()),
                             mw_touched=float(rows.pmax[sel & touched].sum()),
                             d_mc_capwtd=float(d),
                             d_mc_touched_capwtd=float(((mc_s - mc)[sel & touched] * cap[sel & touched]).sum()
                                                       / max(cap[sel & touched].sum(), 1e-9))))
    # ---- re-clearing predictor (pooled zones) where the keeper's sidecars exist
    pred = {}
    bundle = REPO / "results/calibration" / KEEPERS[iso]
    ch_p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if ch_p.exists():
        ch = pd.read_parquet(ch_p)
        if "pass" in ch.columns:
            ch = ch[ch["pass"] == "P1"]
        D = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").sort_index()
        if len(D) == T:
            thermal = ~rows.fuel_type.isin(["hydro", "wind", "solar"]).to_numpy()
            kl = set(klass[thermal])
            non_thermal = {c for c in D.columns if c.lower() in ("wind", "solar", "hydro")
                           or "stor" in c.lower() or "import" in c.lower() or "batt" in c.lower()}
            Dth = D[[c for c in D.columns if c not in non_thermal]].sum(axis=1).to_numpy()
            capT = cap * thermal[:, None]

            def clear(mc_arm):
                order = np.argsort(mc_arm, axis=0, kind="stable")
                cs = np.take_along_axis(capT, order, axis=0)
                cum = np.cumsum(cs, axis=0)
                before = cum - cs
                alloc_s = np.clip(Dth[None, :] - before, 0, cs)
                alloc = np.empty_like(alloc_s)
                np.put_along_axis(alloc, order, alloc_s, axis=0)
                ms = np.take_along_axis(mc_arm, order, axis=0)
                idx = np.argmax(cum >= Dth[None, :], axis=0)
                return alloc, ms[idx, np.arange(T)]

            a0, p0 = clear(mc)
            a1, p1 = clear(mc_s)
            load_w = D.sum(axis=1).to_numpy()
            for k in sorted(kl):
                sel = klass == k
                kcols = [c for c in D.columns if c == k or (k == "COAL" and c.startswith("COAL"))]
                pred[k] = dict(base_twh=float(a0[sel].sum() / 1e6), keeper_twh=float(D[kcols].sum().sum() / 1e6) if kcols else np.nan,
                               d_twh=float((a1[sel].sum() - a0[sel].sum()) / 1e6))
            pred["_thermal_cols"] = sorted(c for c in D.columns if c not in non_thermal)
            pred["_lw_price_ratio"] = float(np.average(p1, weights=load_w) / np.average(p0, weights=load_w))
    counts = pmdf.kind.value_counts().to_dict() if len(pmdf) else {}
    # MW of gas rows whose plant carries at least one flagged month, by kind
    mw_by_kind = {}
    if len(pmdf):
        for kind in ("negative", "low", "high"):
            pcs = set(pmdf[pmdf.kind == kind].plant_code)
            mw_by_kind[kind] = float(rows.pmax[is_gas & rows.plant_code.isin(pcs).to_numpy()].sum())
    summary = dict(
        iso=iso, year=year, seam1_armed=seam1_armed, gas_rows=int(is_gas.sum()), gas_mw=gas_mw,
        **{f"mw_plants_with_{k}": v for k, v in mw_by_kind.items()},
        gas_plants=len(gas_plants), own_reporting_plants=int(pmdf.plant_code.nunique()) if len(pmdf) else 0,
        plant_months=int(len(pmdf)), **{f"pm_{k}": int(v) for k, v in counts.items()},
        ref_us_fallback_months=int((pmdf.ref_prov == "us").sum()) if len(pmdf) else 0,
        flagged_plants=int(pmdf[pmdf.kind.isin(["negative", "low", "high"])].plant_code.nunique()) if len(pmdf) else 0,
        seam1_rows=int((np.any(fuel_s != fuel, axis=1)).sum()),
        seam1_mw=float(rows.pmax[np.any(fuel_s != fuel, axis=1)].sum()),
        seam1_mw_share=float(rows.pmax[np.any(fuel_s != fuel, axis=1)].sum() / gas_mw) if gas_mw else 0.0,
        ct_only_plants=int(ct.all_gt.sum()), ct_only_below_floor=int(len(ct_hit)),
        ct_only_between_8_and_floor=int(len(ct_near)),
        ct_only_below_6=int((ct_hit.heat_rate.astype(float) < 6.0).sum()),
        seam2_rows=int(ct_rows.sum()), seam2_mw=float(rows.pmax[ct_rows].sum()),
        seam2_mw_share=float(rows.pmax[ct_rows].sum() / gas_mw) if gas_mw else 0.0,
        seam2_plants=[dict(plant_code=int(pc), heat_rate=float(r.heat_rate), nameplate=float(r.nameplate),
                           fleet_mw=float(rows.pmax[(rows.plant_code == pc)].sum()),
                           fleet_mw_below_floor=float(rows.pmax[(rows.plant_code == pc) & (hr < CT_FLOOR)].sum()),
                           vintage=[int(r.vintage_min), int(r.vintage_max)]) for pc, r in ct_hit.iterrows()],
    )
    pmdf.to_csv(OUT / f"seam1_plant_months_{iso}_{year}.csv", index=False)
    return dict(summary=summary, by_class=by_class, pred=pred)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    ap.add_argument("--post", action="store_true", help="rebuild on the repaired tree (tag post)")
    a = ap.parse_args()
    tag = "post" if a.post else "pre"
    isos = list(KEEPERS) if a.iso == "ALL" else [a.iso]
    ref = reference()
    pd.set_option("display.width", 250)
    for iso in isos:
        for year in a.years:
            try:
                res = census_year(iso, year, ref, tag, a.post)
            except SystemExit as e:
                print(f"SKIP {iso} {year}: {e}")
                continue
            (OUT / f"census_{tag}_{iso}_{year}.json").write_text(json.dumps(res, indent=1, default=float))
            s = res["summary"]
            print(f"\n=== {iso} {year} ({tag}) ===")
            print({k: v for k, v in s.items() if k != "seam2_plants"})
            print("seam2 plants:", s["seam2_plants"])
            print(pd.DataFrame(res["by_class"]).round(3).to_string())
            if res["pred"]:
                print("re-clearing predictor (pooled):", {k: (v if not isinstance(v, dict) else {kk: round(vv, 2) for kk, vv in v.items()}) for k, v in res["pred"].items()})


if __name__ == "__main__":
    main()
