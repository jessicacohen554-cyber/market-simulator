"""NWPP-NEXT-2 item 5 (ZERO LP): why does the keeper dispatch CT_PEAKER short of actual?

Keeper ``2026-09-25-nwpp-next-ferc714-partial`` (bundle ``results/calibration/nwppnext_span``).
No solve is run. Inputs, all committed or pure functions of committed data:

* the keeper's ``hourly/`` sidecars (class dispatch, class-band dispatch, zonal P1 price, demand);
* the benchmark frames rebuilt through ``run_calibration_full.build_benchmark_frames`` (the SINGLE
  benchmark builder, rule 19) — EIA-923 per (plant, class) = the C1 ``classFull`` basis, and the
  per-plant CAMPD hourly net frame (hourly actual shape);
* the keeper fleet rebuilt via the sanctioned ``replay_keeper.run_year_kwargs`` +
  ``derived_run_year_inputs`` + ``run_year(..., fleet_only=True)`` path (pmax, availability, the
  assembled ``mc_base`` offers, zone, plant_group);
* the committed run payload (per-plant model annual MWh).

Run: ``python3 scripts/probes/_nwppnext2_ctpeaker_diag.py [<year> ...]``. Intermediate frames are
cached under ``$NWPPNEXT2_CACHE`` (default ``/tmp/nwppnext2_cache``) — never in the repo.
"""

from __future__ import annotations

import base64
import gzip
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

BUNDLE = Path("results/calibration/nwppnext_span")
RUN_ID = "2026-09-25-nwpp-next-ferc714-partial"
CACHE = Path(os.environ.get("NWPPNEXT2_CACHE", "/tmp/nwppnext2_cache"))
KLASS = "CT_PEAKER"
T = 8760


def bench_frames() -> dict[str, pd.DataFrame]:
    """EIA-923 + CAMPD benchmark frames for every bundle year (cached)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = {}
    names = ("eia923", "campd")
    if all((CACHE / f"{n}.parquet").exists() for n in names):
        return {n: pd.read_parquet(CACHE / f"{n}.parquet") for n in names}
    import scripts.run_calibration_full as RCF

    _, frames = RCF.build_benchmark_frames(BUNDLE)
    for n in names:
        frames[n].to_parquet(CACHE / f"{n}.parquet", index=False)
        out[n] = frames[n]
    return out


def fleet(year: int) -> dict:
    """Keeper fleet for ``year`` (zero LP), reduced to what this probe needs (cached)."""
    f = CACHE / f"fleet_{year}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=True)
        return {k: z[k] for k in z.files}
    import scripts.run_calibration as RC
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    o = RC.run_year(
        year, meta["iso"], T, meta.get("gas_price"), {}, fleet_only=True, **kw
    )
    fa = o["fleet_arrays"]
    mc = np.asarray(o["mc_base"], dtype=np.float32)
    av = np.asarray(fa.availability, dtype=np.float32)
    if av.ndim == 1:
        av = np.tile(av[:, None], (1, T))
    d = dict(
        unit_ids=np.array(list(fa.unit_ids), dtype=str),
        plant_code=np.asarray(fa.plant_code, dtype=np.int64),
        plant_group=np.array([str(g) for g in fa.plant_group], dtype=str),
        pmax=np.asarray(fa.pmax, dtype=np.float32),
        heat_rate=np.asarray(fa.heat_rate, dtype=np.float32),
        vom=np.asarray(fa.vom, dtype=np.float32),
        zone=np.array([o["iso_config"].zone_names[i] for i in fa.zone_idx], dtype=str),
        avail=av,
        mc=mc,
        pmin=np.asarray(fa.pmin, dtype=np.float32),
    )
    np.savez_compressed(f, **d)
    return d


def payload_plants(year: int) -> dict[str, float]:
    """Per-plant model annual TWh from the committed run payload."""
    s = Path(f"frontend/data/backcast/runs/{RUN_ID}.js").read_text()
    b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    d = json.loads(gzip.decompress(base64.b64decode(b)))
    return {k: float(v["m_ann"]) for k, v in d["years"][str(year)]["plants"].items()}


def bench_classfull(year: int) -> dict:
    """The committed C1 bench part for ``year``."""
    return json.load(gzip.open(f"frontend/data/backcast/bench/NWPP/{year}.json.gz"))[
        "bench"
    ]


def _q(x, qs=(0.1, 0.5, 0.9)):
    return " / ".join(f"{np.quantile(x, q):.1f}" for q in qs)


def analyse(year: int, e923: pd.DataFrame, campd: pd.DataFrame) -> None:
    H = BUNDLE / "hourly"
    ch = pd.read_parquet(H / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"].pivot_table(
        index="hour", columns="klass", values="mw", observed=True
    )
    sysf = pd.read_parquet(H / f"system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    price = sysf.pivot_table(index="hour", columns="zone", values="price")
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand")
    sysdem = dem.sum(axis=1).to_numpy()
    bench = bench_classfull(year)
    cf_ct = float(bench["classFull"].get(KLASS, 0.0))
    mod_ct = ch[KLASS].to_numpy() if KLASS in ch else np.zeros(T)
    print(
        f"\n{'=' * 90}\nYEAR {year}   C1 CT_PEAKER  model {mod_ct.sum() / 1e6:.3f}  classFull {cf_ct:.3f}  "
        f"Δ {mod_ct.sum() / 1e6 - cf_ct:+.3f} TWh\n{'=' * 90}"
    )

    # ---------------- actual hourly CT from CAMPD, scaled by the 923 CT share ----------------
    e = e923[e923["year"] == year] if "year" in e923 else e923
    ey = e.groupby(["plant_id", "klass"])["annual_mwh"].sum().unstack(fill_value=0.0)
    ct_pl = ey[ey.get(KLASS, 0) > 0]
    share = (ct_pl[KLASS] / ey.loc[ct_pl.index].clip(lower=0).sum(axis=1)).clip(0, 1)
    cy = campd[campd["year"] == year] if "year" in campd else campd
    cy = cy[cy["plant_id"].isin(share.index)]
    piv = (
        cy.pivot_table(index="hour", columns="plant_id", values="net_mw", aggfunc="sum")
        .reindex(range(T))
        .fillna(0.0)
    )
    act_ct = (piv * share.reindex(piv.columns).to_numpy()).sum(axis=1).to_numpy()
    cov = act_ct.sum() / 1e6
    ct923_campd = float(ct_pl.loc[ct_pl.index.isin(piv.columns), KLASS].sum()) / 1e6
    print(
        f"  EIA-923 CT_PEAKER plants: {len(ct_pl)}  923 CT total {ct_pl[KLASS].sum() / 1e6:.3f} TWh; "
        f"of which CAMPD-reporting {piv.shape[1]} plants = {ct923_campd:.3f} TWh; CAMPD-scaled hourly {cov:.3f} TWh"
    )
    # rescale the CAMPD shape to the 923 CT total of the CAMPD plants (shape only), for profile work
    act = act_ct * (ct923_campd / cov) if cov > 0 else act_ct
    mod = mod_ct.copy()

    # ---------------- Q1 concentration: by load quintile / top hours / hour of day ----------------
    order = np.argsort(sysdem)
    qs = np.array_split(order, 5)
    print(
        "  Q1 by model system-demand quintile (TWh):  model / actual(CAMPD-shape, 923-level on CAMPD plants) / Δ"
    )
    for i, idx in enumerate(qs):
        print(
            f"    Q{i + 1}: {mod[idx].sum() / 1e6:6.3f} / {act[idx].sum() / 1e6:6.3f} / {(mod[idx] - act[idx]).sum() / 1e6:+6.3f}"
        )
    top = order[-876:]
    lw_price = (price * dem).sum(axis=1).to_numpy() / sysdem
    ptop = np.argsort(lw_price)[-876:]
    print(
        f"  top-10% load hours:  model {mod[top].sum() / 1e6:.3f} act {act[top].sum() / 1e6:.3f} "
        f"(share of annual: model {mod[top].sum() / max(mod.sum(), 1):.1%}, act {act[top].sum() / max(act.sum(), 1):.1%})"
    )
    print(
        f"  top-10% price hours: model {mod[ptop].sum() / 1e6:.3f} act {act[ptop].sum() / 1e6:.3f} "
        f"(share: model {mod[ptop].sum() / max(mod.sum(), 1):.1%}, act {act[ptop].sum() / max(act.sum(), 1):.1%})"
    )
    hod = np.arange(T) % 24
    mh = np.array([mod[hod == h].mean() for h in range(24)])
    ah = np.array([act[hod == h].mean() for h in range(24)])
    print(
        "  hour-of-day mean MW (model | actual):  "
        + " ".join(
            f"{h}:{mh[h]:.0f}|{ah[h]:.0f}" for h in (0, 4, 8, 12, 16, 18, 20, 22)
        )
    )
    mon = (np.arange(T) // 730).clip(0, 11)
    print(
        "  monthly TWh (model|actual): "
        + " ".join(
            f"{m + 1}:{mod[mon == m].sum() / 1e6:.2f}|{act[mon == m].sum() / 1e6:.2f}"
            for m in range(12)
        )
    )
    print(f"  hourly r(model, actual) = {np.corrcoef(mod, act)[0, 1]:.3f}")

    # ---------------- Q2 envelope / CF / hours online ----------------
    fl = fleet(year)
    ci = np.where(fl["plant_group"] == KLASS)[0]
    env = (fl["pmax"][ci, None] * fl["avail"][ci]).sum(axis=0)
    pm = float(fl["pmax"][ci].sum())
    print(
        f"  Q2 model CT_PEAKER rows {len(ci)}  Σpmax {pm:,.0f} MW  mean avail {env.mean() / pm:.3f}  "
        f"envelope {env.sum() / 1e6:.2f} TWh  dispatched {mod.sum() / 1e6:.3f} TWh  CF {mod.sum() / pm / T:.3%}"
    )
    print(
        f"    hours model CT>1 MW: {(mod > 1).sum()}   hours at ≥95% of envelope: {(mod >= 0.95 * env).sum()}"
    )
    # actual cap-weighted: CAMPD CT plants
    pl_on = (piv > 1).sum(axis=0)
    print(
        f"    actual CAMPD CT plants: median hours on {int(pl_on.median())}, mean {pl_on.mean():.0f}; "
        f"hours any CT >1 MW {(act > 1).sum()}; actual CF on model CT Σpmax {act_ct.sum() / pm / T:.3%} (CAMPD-only), "
        f"{cf_ct * 1e6 / pm / T:.3%} (classFull)"
    )

    # ---------------- Q3 merit: CT offer vs zonal price ----------------
    zones = list(price.columns)
    mc_ct = fl["mc"][ci]
    mcv = mc_ct if mc_ct.ndim == 2 else np.tile(mc_ct[:, None], (1, T))
    zp = np.stack([price[z].to_numpy() for z in fl["zone"][ci]])  # (n_ct, T)
    econ = zp >= mcv - 1e-6
    econ_env = (fl["pmax"][ci, None] * fl["avail"][ci] * econ).sum() / 1e6
    print(
        f"    CT rows: mean mc {np.average(mcv.mean(axis=1), weights=fl['pmax'][ci]):.2f} $/MWh (cap-wtd), "
        f"p10/p50/p90 unit mean-mc {_q(mcv.mean(axis=1))}"
    )
    print(
        f"    economic envelope (hours zonal price ≥ unit mc) = {econ_env:.3f} TWh vs dispatched {mod.sum() / 1e6:.3f}"
    )
    for z in zones:
        zi = np.where(fl["zone"][ci] == z)[0]
        if len(zi) == 0:
            continue
        p = price[z].to_numpy()
        mz = mcv[zi].mean(axis=1)
        print(
            f"    {z:12s} CT Σpmax {fl['pmax'][ci][zi].sum():7.0f}  mc p10/p50/p90 {_q(mz)}  "
            f"price p10/p50/p90/max {_q(p)} / {p.max():.1f}  distinct prices {len(np.unique(np.round(p, 2)))}  "
            f"hrs price≥p50 CT mc {(p >= np.median(mz)).sum()}"
        )
    # hours actual CT ran hard: model price vs CT mc, and what the model ran instead
    hard = act >= np.quantile(act, 0.9)
    lp = lw_price[hard]
    print(
        f"    actual-CT top-decile hours ({hard.sum()}): model load-wtd price p10/p50/p90 {_q(lp)}; "
        f"cap-wtd CT mc {np.average(mcv[:, hard].mean(axis=1), weights=fl['pmax'][ci]):.2f}"
    )
    # class offers for comparison
    for k in ("CC_REGULAR", "ST_GAS", "COAL_BIT", "COAL_PRB", "CT_CHP", "CC_CHP"):
        kk = np.where(fl["plant_group"] == k)[0]
        if len(kk):
            mk = fl["mc"][kk]
            mk = mk.mean(axis=1) if mk.ndim == 2 else mk
            print(
                f"      {k:10s} Σpmax {fl['pmax'][kk].sum():7.0f} cap-wtd mc {np.average(mk, weights=fl['pmax'][kk]):6.2f} "
                f"envelope {(fl['pmax'][kk, None] * fl['avail'][kk]).sum() / 1e6:6.2f} TWh  dispatched {ch[k].sum() / 1e6 if k in ch else 0:6.2f}  "
                f"classFull {bench['classFull'].get(k, 0):6.2f}"
            )
    # CT heat rate vs CC heat rate
    hr_ct = np.average(fl["heat_rate"][ci], weights=fl["pmax"][ci])
    kk = np.where(fl["plant_group"] == "CC_REGULAR")[0]
    print(
        f"    cap-wtd heat rate CT {hr_ct:.2f} vs CC_REGULAR {np.average(fl['heat_rate'][kk], weights=fl['pmax'][kk]):.2f} MMBtu/MWh"
    )
    # band view
    cb = pd.read_parquet(H / f"class_band_hourly_{year}.parquet")
    cb = cb[(cb["pass"] == "P1") & (cb["klass"] == KLASS)]
    print(
        "    CT dispatch by band (TWh): "
        + ", ".join(
            f"{b}={g['mw'].sum() / 1e6:.3f}"
            for b, g in cb.groupby("band", observed=True)
        )
    )
    bnd = pd.Series([u.rpartition("_")[2] for u in fl["unit_ids"][ci]])
    for b in sorted(bnd.unique()):
        bi = ci[(bnd == b).to_numpy()]
        mb = fl["mc"][bi]
        mb = mb.mean(axis=1) if mb.ndim == 2 else mb
        print(
            f"      band {b:10s} Σpmax {fl['pmax'][bi].sum():7.0f} cap-wtd mc {np.average(mb, weights=fl['pmax'][bi]):6.2f} "
            f"env {(fl['pmax'][bi, None] * fl['avail'][bi]).sum() / 1e6:.2f} TWh"
        )

    # ---------------- Q4 per-plant classification ----------------
    pp = payload_plants(year)
    top10 = ct_pl[KLASS].sort_values(ascending=False).head(12)
    print(
        "  Q4 top EIA-923 CT_PEAKER plants: plant | 923 CT GWh | 923 other-class GWh | model classes (Σpmax) | model zone | model TWh (payload)"
    )
    for pid, v in top10.items():
        other = {
            k: round(x / 1e3) for k, x in ey.loc[pid].items() if k != KLASS and x > 1e3
        }
        um = fl["plant_code"] == pid
        mcls = {}
        for g, p in zip(fl["plant_group"][um], fl["pmax"][um]):
            mcls[g] = mcls.get(g, 0.0) + float(p)
        mz = sorted(set(fl["zone"][um]))
        mt = {k: v2 for k, v2 in pp.items() if k.split(":")[0] == str(pid)}
        print(
            f"    {pid:6d} | {v / 1e3:7.0f} | {other} | {{{', '.join(f'{g}:{p:.0f}' for g, p in mcls.items())}}} | {mz} | {mt}"
        )
    # misclassification census
    m_plants_ct = set(fl["plant_code"][ci].tolist())
    a_plants_ct = set(ct_pl.index.astype(int).tolist())
    only_a = a_plants_ct - m_plants_ct
    only_m = m_plants_ct - a_plants_ct
    miss = ct_pl.loc[ct_pl.index.isin(list(only_a)), KLASS].sum() / 1e6
    in_fleet = set(fl["plant_code"].tolist())
    miss_absent = (
        ct_pl.loc[
            ct_pl.index.isin([p for p in only_a if p not in in_fleet]), KLASS
        ].sum()
        / 1e6
    )
    print(
        f"    923-CT plants not CT in model: {len(only_a)} ({miss:.3f} TWh 923 CT; of which absent from fleet entirely {miss_absent:.3f} TWh)"
    )
    for p in sorted(only_a, key=lambda p: -ct_pl.loc[p, KLASS])[:8]:
        um = fl["plant_code"] == p
        print(
            f"      {p}: 923 CT {ct_pl.loc[p, KLASS] / 1e3:.0f} GWh; model groups {sorted(set(fl['plant_group'][um]))} Σpmax {fl['pmax'][um].sum():.0f}"
        )
    print(
        f"    model CT plants with no 923 CT: {len(only_m)}  Σpmax {fl['pmax'][ci][np.isin(fl['plant_code'][ci], list(only_m))].sum():.0f} MW"
    )
    # per-plant offer / CF table for the top actual CT plants (model CT rows only)
    print(
        "  Q4b plant | HR MMBtu/MWh | mc p50 $/MWh | implied fuel p50 $/MMBtu | Σpmax | act CF (923) | model CF (payload)"
    )
    for pid, v in top10.items():
        um = np.where((fl["plant_code"] == pid) & (fl["plant_group"] == KLASS))[0]
        if len(um) == 0:
            continue
        pmx = fl["pmax"][um].sum()
        mcm = np.median(fl["mc"][um], axis=1) if fl["mc"].ndim == 2 else fl["mc"][um]
        fuel = (mcm - fl["vom"][um]) / np.maximum(fl["heat_rate"][um], 1e-6)
        mt = sum(
            v2
            for k, v2 in pp.items()
            if k.split(":")[0] == str(pid) and (":" not in k or k.endswith(KLASS))
        )
        print(
            f"    {pid:6d} | {np.average(fl['heat_rate'][um], weights=fl['pmax'][um]):5.2f} | "
            f"{np.average(mcm, weights=fl['pmax'][um]):6.1f} | {np.average(fuel, weights=fl['pmax'][um]):5.2f} | {pmx:5.0f} | "
            f"{v / pmx / T:6.1%} | {mt * 1e6 / pmx / T:6.1%}"
        )
    # ---------------- DIAGNOSTIC reference price (NOT a benchmark: WEIM gate verdict NO) ----------------
    wf = Path("data/raw/nwpp-weim/weim_hourly_by_ba.parquet")
    if wf.exists() and year >= 2023:
        w = pd.read_parquet(wf)
        w = w[w["year"] == year]
        zmap = {
            "NWPP-NW": ["BPAT", "PSEI", "SCL", "TPWR"],
            "NWPP-OR": ["PGE", "PACW"],
            "NWPP-INLAND": ["IPCO", "AVA", "NWMT"],
            "NWPP-EAST": ["PACE"],
            "NWPP-SNV": ["NEVP"],
        }
        wz = {
            z: w[w["baa"].isin(b)]
            .groupby("hour")["lmp"]
            .mean()
            .reindex(range(T))
            .to_numpy()
            for z, b in zmap.items()
        }
        zc = np.stack([wz[z] for z in fl["zone"][ci]])
        ok = np.isfinite(zc)
        avail_mw = fl["pmax"][ci, None] * fl["avail"][ci]
        econ_w = ((zc >= mcv) & ok) * avail_mw
        econ_m = (econ & ok) * avail_mw
        okh = np.isfinite(zc).any(axis=0)
        print(
            f"  WEIM-RTPD diagnostic ({okh.sum()} priced hours): CT economic energy if the zone cleared at the WEIM price "
            f"{econ_w.sum() / 1e6:.3f} TWh vs at the model price {econ_m.sum() / 1e6:.3f} TWh "
            f"(model dispatched in those hours {mod[okh].sum() / 1e6:.3f}; actual CT (923-level, CAMPD plants) {act[okh].sum() / 1e6:.3f})"
        )
        for z in zmap:
            h = np.isfinite(wz[z])
            print(
                f"    {z:12s} mean price WEIM {np.nanmean(wz[z]):6.1f}  model(same hrs) {price[z].to_numpy()[h].mean():6.1f}  "
                f"WEIM p90 {np.nanquantile(wz[z], 0.9):6.1f} model p90 {np.quantile(price[z].to_numpy()[h], 0.9):6.1f}"
            )
        mc_ = pd.read_parquet("data/raw/nwpp-weim/midc_peak_daily.parquet")
        mc_ = mc_[pd.to_datetime(mc_["delivery_start"]).dt.year == year]
        print(
            f"    Mid-C Peak ICE daily wavg mean {mc_['wavg'].mean():.1f} $/MWh (n={len(mc_)}); "
            f"model NWPP-NW HE7-22 weekday mean {price['NWPP-NW'].to_numpy()[(hod >= 6) & (hod < 22)].mean():.1f}"
        )
    # ---------------- fossil ledger vs classFull ----------------
    fam = {
        "coal": ["COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE"],
        "gas": ["CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"],
    }
    led = {
        f: (
            sum(ch[k].sum() / 1e6 for k in ks if k in ch),
            sum(bench["classFull"].get(k, 0) for k in ks),
        )
        for f, ks in fam.items()
    }
    print(
        "  fossil ledger model/classFull/Δ TWh: "
        + "  ".join(f"{f} {m:.2f}/{a:.2f}/{m - a:+.2f}" for f, (m, a) in led.items())
        + f"  | 923→930 reconcile scale {cf_ct / max(ct_pl[KLASS].sum() / 1e6, 1e-9):.3f}"
    )
    print(
        "  gas-class Δ: "
        + " ".join(
            f"{k} {ch[k].sum() / 1e6 - bench['classFull'].get(k, 0):+.2f}"
            for k in fam["gas"]
            if k in ch
        )
    )
    # ---------------- Q5 headroom below CT ----------------
    cc = np.where(fl["plant_group"] == "CC_REGULAR")[0]
    cc_env = (fl["pmax"][cc, None] * fl["avail"][cc]).sum(axis=0)
    cc_head = cc_env - ch["CC_REGULAR"].to_numpy()
    print(
        f"  Q5 CC_REGULAR hourly headroom (envelope − dispatch): p1/p10/p50 {np.quantile(cc_head, 0.01):.0f} / "
        f"{np.quantile(cc_head, 0.1):.0f} / {np.median(cc_head):.0f} MW; hours headroom < 1,100 MW: {(cc_head < 1100).sum()}; "
        f"< 2,000 MW: {(cc_head < 2000).sum()}"
    )
    for z in zones:
        czi = cc[fl["zone"][cc] == z]
        tzi = ci[fl["zone"][ci] == z]
        if len(czi) == 0:
            continue
        mcc = fl["mc"][czi]
        mcc = mcc.mean(axis=1) if mcc.ndim == 2 else mcc
        mct = fl["mc"][tzi]
        mct = mct.mean(axis=1) if mct.ndim == 2 else mct
        print(
            f"    {z:12s} CC Σpmax {fl['pmax'][czi].sum():6.0f} mc p10/p50/p90 {_q(mcc)} | CT mc p50 {np.median(mct) if len(mct) else float('nan'):.1f}"
        )


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    bf = bench_frames()
    e923, campd = bf["eia923"], bf["campd"]
    for y in years:
        analyse(y, e923, campd)


if __name__ == "__main__":
    main()
