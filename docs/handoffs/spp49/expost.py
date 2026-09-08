"""SPP-49 ex-post: difference the repaired tree's input arrays against the pre-edit arrays.

For every ISO-year census.py rebuilt twice (tag ``pre`` on the unedited tree, ``post`` on the
repaired tree, both fleet-only on the keeper's own recipe) this reports, per class: rows whose
fuel price moved, rows whose heat rate moved, MW, the capacity-weighted delta-mc, and the
re-clearing predictor on the ACTUAL post arrays — the realised version of PRECOMMIT §5. It also
runs the S2 identity check: every own-reported gas plant-month the screen flagged reads the state
reference in the post arrays, and every in-band month is byte-identical to pre.
"""
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from census import SCRATCH, KEEPERS, MONTH_H, reference, ref_month, LOW, HIGH, GAS_FUELS, CT_FLOOR  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from market_sim.data.eia923 import plant_month_price_grid  # noqa: E402
from market_sim.data.fuel.plant_prices import _load_monthly_cache  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/handoffs/spp49"
ref = reference()
costs = _load_monthly_cache(None)
plant_state = costs.groupby("plant_id")["state"].first()
rows_out, s2 = [], []
for pre_p in sorted(glob.glob(str(SCRATCH / "arrays_pre_*_*.npz"))):
    name = Path(pre_p).stem.replace("arrays_pre_", "")
    iso, year = name.rsplit("_", 1); year = int(year)
    post_p = SCRATCH / f"arrays_post_{iso}_{year}.npz"
    if not post_p.exists():
        print("no post arrays for", iso, year); continue
    a, b = np.load(pre_p), np.load(post_p)
    rows = pd.read_csv(SCRATCH / f"rows_pre_{iso}_{year}.csv"); rows_b = pd.read_csv(SCRATCH / f"rows_post_{iso}_{year}.csv")
    assert (rows.unit_id.to_numpy() == rows_b.unit_id.to_numpy()).all(), f"{iso} {year}: row identity moved"
    mc0, mc1 = a["mc"].astype(float), b["mc"].astype(float); f0, f1 = a["fuel"].astype(float), b["fuel"].astype(float)
    av = a["avail"].astype(float); assert np.array_equal(av, b["avail"]), "availability moved"
    hr0, hr1 = rows.heat_rate.to_numpy(), rows_b.heat_rate.to_numpy()
    pg = rows.plant_group.fillna("").astype(str); klass = pg.where(pg != "", rows.fuel_type.astype(str)).to_numpy()
    is_gas = rows.fuel_type.isin(GAS_FUELS).to_numpy()
    cap = rows.pmax.to_numpy()[:, None] * av
    fuel_moved = np.any(~np.isclose(f0, f1, rtol=1e-5, atol=1e-6), axis=1); hr_moved = ~np.isclose(hr0, hr1)
    for k in sorted(set(klass[is_gas])):
        sel = klass == k; w = cap[sel].sum()
        rows_out.append(dict(iso=iso, year=year, klass=k, rows=int(sel.sum()), mw=float(rows.pmax[sel].sum()),
                             fuel_rows=int((sel & fuel_moved).sum()), fuel_mw=float(rows.pmax[sel & fuel_moved].sum()),
                             hr_rows=int((sel & hr_moved).sum()), hr_mw=float(rows.pmax[sel & hr_moved].sum()),
                             d_mc_capwtd=float(((mc1 - mc0)[sel] * cap[sel]).sum() / w) if w else 0.0))
    # S2 identity on own-reported months (armed ISOs only)
    run_cfg = json.loads((REPO / "results/calibration" / KEEPERS[iso] / "run_config.json").read_text())
    armed = bool(run_cfg["scenario_config"].get("gas_plant_monthly_fuel_pricing"))
    grid = plant_month_price_grid(costs, year, "Natural Gas"); ok = bad = kept = not_carried = 0
    if armed:
        for g in np.flatnonzero(is_gas):
            pc = int(rows.plant_code[g]); own = grid.get(pc)
            if own is None: continue
            st = str(plant_state.get(pc, ""))
            for m in range(12):
                if np.isnan(own[m]): continue
                R, prov = ref_month(ref, st, year, m + 1)
                cells = MONTH_H == m
                if prov == "none" or R <= 0:
                    continue
                pre_mean = f0[g, cells].mean()
                if not np.isclose(pre_mean, own[m], rtol=1e-3, atol=1e-3):
                    # the keeper never carried the F923 print on this row: a downstream
                    # overlay (CAISO / NEISO hub basis) owns the cell, or a basis adder
                    # rides on top (PJM / MISO zonal basis) — test the SHIFT instead
                    shift = f1[g, cells].mean() - pre_mean
                    if own[m] < LOW * R or own[m] > HIGH * R:
                        if np.isclose(shift, R - own[m], rtol=1e-3, atol=1e-3): ok += 1
                        elif np.isclose(shift, 0.0, atol=1e-6): not_carried += 1
                        else: bad += 1
                    else:
                        if np.isclose(shift, 0.0, atol=1e-6): kept += 1
                        else: bad += 1
                    continue
                if own[m] < LOW * R or own[m] > HIGH * R:
                    # gas_daily_shape may ride on top: compare the month mean
                    if np.isclose(f1[g, cells].mean(), R, rtol=1e-4): ok += 1
                    else: bad += 1
                else:
                    if np.allclose(f0[g, cells], f1[g, cells]): kept += 1
                    else: bad += 1
    s2.append(dict(iso=iso, year=year, armed=armed, flagged_cells_at_reference=ok, in_band_cells_identical=kept,
                   flagged_but_overlaid_downstream=not_carried, violations=bad))
    # realised re-clearing predictor
    bundle = REPO / "results/calibration" / KEEPERS[iso]; ch_p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if ch_p.exists():
        ch = pd.read_parquet(ch_p); ch = ch[ch["pass"] == "P1"] if "pass" in ch.columns else ch
        D = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").sort_index()
        if len(D) == mc0.shape[1]:
            thermal = ~rows.fuel_type.isin(["hydro", "wind", "solar"]).to_numpy()
            non_th = {c for c in D.columns if c.lower() in ("wind", "solar", "hydro") or "stor" in c.lower() or "import" in c.lower() or "batt" in c.lower()}
            Dth = D[[c for c in D.columns if c not in non_th]].sum(axis=1).to_numpy(); capT = cap * thermal[:, None]; T = mc0.shape[1]
            def clear(mcx):
                order = np.argsort(mcx, axis=0, kind="stable"); cs = np.take_along_axis(capT, order, axis=0); cum = np.cumsum(cs, axis=0)
                alloc_s = np.clip(Dth[None, :] - (cum - cs), 0, cs); alloc = np.empty_like(alloc_s); np.put_along_axis(alloc, order, alloc_s, axis=0)
                ms = np.take_along_axis(mcx, order, axis=0); idx = np.argmax(cum >= Dth[None, :], axis=0); return alloc, ms[idx, np.arange(T)]
            a0, p0 = clear(mc0); a1, p1 = clear(mc1); lw = D.sum(axis=1).to_numpy()
            for r in rows_out:
                if r["iso"] == iso and r["year"] == year:
                    sel = klass == r["klass"]; r["realised_d_twh"] = float((a1[sel].sum() - a0[sel].sum()) / 1e6)
            for k in ("COAL",):
                sel = klass == k
                if sel.any(): rows_out.append(dict(iso=iso, year=year, klass=k, realised_d_twh=float((a1[sel].sum() - a0[sel].sum()) / 1e6)))
            s2[-1]["lw_price_ratio"] = float(np.average(p1, weights=lw) / np.average(p0, weights=lw))
df = pd.DataFrame(rows_out); df.to_csv(OUT / "expost_by_class.csv", index=False)
pd.set_option("display.width", 250)
print(pd.DataFrame(s2).to_string()); print(df.round(3).to_string())
