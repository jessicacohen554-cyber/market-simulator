"""nwppnext2 phase 0: footprint census of the UNCOUPLED Columbia/Snake mainstem. ZERO LP.

Reproduces every number in
``docs/handoffs/FINDING-nwppnext2-mainstem-census-2026-09-25.md`` from:

* the keeper's committed ``hourly/`` sidecars
  (``results/calibration/nwppnext_span``, keeper ``2026-09-25-nwpp-next-ferc714-partial``);
* the per-plant ``dispatch/<y>_P1.parquet`` of the seven NWPP-NEXT legs, which are
  NOT on ``main`` (rule 32(d)). At this writing they were read from shard commits
  (provenance only, rule 33(d) -- not a durability claim)::

      2019 37315fe2  2020 32c099ef  2021 3b26689e  2022 6afde394
      2023 7d97a5de  2024 30f673db  2025 b6a96c0c

  with ``git show <sha>:results/calibration/nwppnext_<y>/dispatch/<y>_P1.parquet``
  into ``--legs``;
* the pool EIA-930 benchmark, rebuilt at zero LP through
  ``build_calibration_reference._pool_hourly_benchmark`` (the same builder the
  bundle's shared ``eia930`` frame is made by);
* CROHMS hourly ``Power.Total`` (``data/raw/nwpp-hydro/crohms``, 2023-2025 only);
* the per-BA EIA-930 extracts (``data/raw/eia-930-hourly``) for the BPAT check.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwppnext2_mainstem_census.py --legs DIR
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = Path("results/calibration/nwppnext_span")
HYD = Path("data/raw/nwpp-hydro")
YEARS = tuple(range(2019, 2026))
N = 8760
COAL = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE")
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
# The nine mainstem plants with NO hourly water-balance row (NWPP-49 §5 / RESULT-nwpp-49):
# downstream of no coupled link. station -> EIA plant id.
UNCOUPLED = {"RRH": 3883, "WAN": 3888, "PRD": 3887, "MCN": 3084, "JDA": 3082,
             "TDA": 3895, "LWG": 6175, "LGS": 3926, "LMN": 3927}
COUPLED_D = {"CHJ": 3921, "WEL": 3886, "RIS": 6200, "BON": 3075, "IHR": 3925}
HEADS = {"GCL": 6163, "DWR": 840}


def _r(a, b):
    """Pearson r; NaN when either side is constant."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float("nan") if a.std() == 0 or b.std() == 0 else float(np.corrcoef(a, b)[0, 1])


def _split(x):
    """(daily-mean broadcast, within-day deviation) of an hourly 8760 vector."""
    x = np.asarray(x, float)[:N].reshape(-1, 24)
    dm = x.mean(1, keepdims=True)
    return np.repeat(dm.ravel(), 24), (x - dm).ravel()


def _month_idx():
    """Hour -> month (1..12) for a 365-day year."""
    return pd.date_range("2023-01-01", periods=N, freq="h").month.to_numpy()


def _dtd(x):
    """Day-to-day sd of daily means, net of each month's mean (the within-month daily term)."""
    d = np.asarray(x, float)[:N].reshape(-1, 24).mean(1)
    m = pd.date_range("2023-01-01", periods=365, freq="D").month.to_numpy()
    return float(pd.Series(d).groupby(m).transform(lambda s: s - s.mean()).std())


def _crohms(year):
    """station -> 8760 hourly Power.Total (MW), sentinels screened, gaps interpolated."""
    c = pd.read_parquet(HYD / "crohms" / "nwpp_crohms_hourly.parquet")
    c = c[c.series.str.startswith("Power") & (c.ts.dt.year == year)]
    chain = pd.read_csv(HYD / "nwpp_hydro_chain.csv").set_index("plant_id").max_mw_eia860
    out = {}
    for st, pid in {**UNCOUPLED, **COUPLED_D, **HEADS}.items():
        s = c[c.station == st].set_index("ts").value
        s = s[~s.index.duplicated()]
        s = s.where((s >= 0) & (s <= 1.1 * chain[pid]))
        idx = pd.date_range(f"{year}-01-01", periods=N, freq="h")
        out[st] = s.reindex(idx).interpolate(limit_direction="both").to_numpy(float)
    return out


def _bench(year):
    """Pool EIA-930 benchmark dict (the bundle's eia930 builder)."""
    from scripts.data.build_calibration_reference import _pool_hourly_benchmark
    return {k: np.asarray(v, float)[:N] for k, v in _pool_hourly_benchmark("NWPP", year).items()}


def _lag(model, actual, span=6):
    """Integer hour shift s maximising r(model[t], actual[t+s]); returns (s, r)."""
    best = max(range(-span, span + 1), key=lambda s: _r(model, np.roll(actual, -s)))
    return best, _r(model, np.roll(actual, -best))


def run(legs: Path) -> dict:
    """Compute the census; print a table per section and return a JSON record."""
    rec: dict = {}
    chain = pd.read_csv(HYD / "nwpp_hydro_chain.csv")
    links = pd.read_csv(HYD / "nwpp_hydro_cascade_links.csv")
    rec["links"] = links[["link", "u_station", "d_station", "coupled", "reason"]].to_dict("records")
    ba = (pd.read_parquet(HYD / "nwpp_hydro_budget.parquet")[["plant_id", "ba_code"]]
          .drop_duplicates("plant_id").set_index("plant_id").ba_code)
    mon = _month_idx()
    print("\n(1) year | coal r / r_d / r_i | coal sd_intra m/a, dtd m/a | hydro sd_intra m/a, "
          "dtd m/a | r(cres,hres) all/daily/intra | beta | U9 share of model hydro intra var")
    for y in YEARS:
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        g = lambda ks: ch[ch.klass.isin(ks)].groupby("hour").mw.sum().reindex(range(N), fill_value=0).to_numpy(float)
        mc, mh, mg = g(COAL), g(("hydro",)), g(GAS)
        b = _bench(y)
        ac, ah, ag = b["coal"], b["hydro"], b["gas"]
        cres, hres, gres = mc - ac, mh - ah, mg - ag
        cd, ci = _split(cres); hd, hi = _split(hres)
        d = pd.read_parquet(legs / f"{y}_P1.parquet", columns=["plant_code", "klass", "hour", "mw"])
        d = d[d.klass == "hydro"]
        pp = d.groupby(["plant_code", "hour"]).mw.sum().unstack(fill_value=0.0)
        u9 = pp.reindex(list(UNCOUPLED.values())).fillna(0).sum().reindex(range(N), fill_value=0).to_numpy()
        _, u9i = _split(u9); _, mhi = _split(mh)
        bpat_m = pp[pp.index.map(lambda p: ba.get(p) == "BPAT")].sum().reindex(range(N), fill_value=0).to_numpy()
        e = pd.read_parquet("data/raw/eia-930-hourly/BPAT hourly.parquet")
        # fixed Pacific standard time (UTC-8), reindexed to a full 8760
        t = pd.to_datetime(e["UTC time"]) - pd.Timedelta(hours=8)
        e = pd.Series(e["NG: WAT"].to_numpy(float), index=t)
        e = e[~e.index.duplicated()].reindex(pd.date_range(f"{y}-01-01", periods=N, freq="h"))
        e = e.interpolate(limit_direction="both").to_numpy()
        row = dict(
            coal_r=_r(mc, ac), coal_r_daily=_r(_split(mc)[0][::24], _split(ac)[0][::24]),
            coal_r_intra=_r(_split(mc)[1], _split(ac)[1]),
            coal_sdi_m=_split(mc)[1].std(), coal_sdi_a=_split(ac)[1].std(),
            coal_dtd_m=_dtd(mc), coal_dtd_a=_dtd(ac),
            hyd_sdi_m=mhi.std(), hyd_sdi_a=_split(ah)[1].std(), hyd_dtd_m=_dtd(mh), hyd_dtd_a=_dtd(ah),
            hyd_r=_r(mh, ah), hyd_energy_m_twh=mh.sum() / 1e6, hyd_energy_a_twh=ah.sum() / 1e6,
            r_ch=_r(cres, hres), r_ch_daily=_r(cd[::24], hd[::24]), r_ch_intra=_r(ci, hi),
            r_cg=_r(cres, gres), beta_c_on_h=float(np.polyfit(hres, cres, 1)[0]),
            cres_abs_twh=np.abs(cres).sum() / 1e6, hres_abs_twh=np.abs(hres).sum() / 1e6,
            u9_sdi_m=u9i.std(), u9_dtd_m=_dtd(u9), u9_share_hyd_intra_var=float(np.cov(u9i, mhi)[0, 1] / mhi.var()),
            u9_energy_m_twh=u9.sum() / 1e6,
            bpat_sdi_m=_split(bpat_m)[1].std(), bpat_sdi_a=_split(e)[1].std(),
            bpat_dtd_m=_dtd(bpat_m), bpat_dtd_a=_dtd(e),
        )
        # (3) counterfactual ceilings, 2023-2025 (CROHMS exists only there)
        if y >= 2023:
            cr = _crohms(y)
            a9 = sum(cr[s] for s in UNCOUPLED)
            s, rl = _lag(u9, a9)
            a9 = np.roll(a9, -s)
            # scale the measured shape to the model's own plant-month energy (a coupling
            # conserves each monthly budget), per plant, then sum
            a9s = np.zeros(N)
            for st, pid in UNCOUPLED.items():
                m = pp.loc[pid].reindex(range(N), fill_value=0).to_numpy() if pid in pp.index else np.zeros(N)
                a = np.roll(cr[st], -s)
                for k in range(1, 13):
                    w = mon == k
                    a9s[w] += a[w] * (m[w].sum() / a[w].sum() if a[w].sum() > 0 else 0.0)
            delta = a9s - u9  # extra mainstem MW if it followed the measured shape
            eh = np.abs(_split(ah)[1]).sum()
            row.update(
                crohms_lag_h=s, u9_r_vs_crohms=rl,
                u9_sdi_a=_split(a9)[1].std(), u9_dtd_a=_dtd(a9), u9_energy_a_twh=a9.sum() / 1e6,
                u9_r_intra=_r(u9i, _split(a9)[1]),
                u9_reshape_twh=np.abs(delta).sum() / 1e6,
                r_cres_u9res=_r(cres, u9 - a9s), r_cres_u9res_intra=_r(ci, _split(u9 - a9s)[1]),
                r_cres_u9res_daily=_r(cd[::24], _split(u9 - a9s)[0][::24]),
                hyd_intra_abs_a_twh=eh / 1e6,
                coal_r_cf_u9_all_to_coal=_r(mc - delta, ac),
                coal_r_cf_u9_coal_share=_r(mc - delta * mc.sum() / (mc.sum() + mg.sum()), ac),
                coal_r_cf_poolhydro_all_to_coal=_r(mc - (ah * mh.sum() / ah.sum() - mh), ac),
            )
        rec[y] = {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in row.items()}
        q = rec[y]
        print(f"  {y} {q['coal_r']:.3f}/{q['coal_r_daily']:.3f}/{q['coal_r_intra']:.3f} | "
              f"{q['coal_sdi_m']:.0f}/{q['coal_sdi_a']:.0f} {q['coal_dtd_m']:.0f}/{q['coal_dtd_a']:.0f} | "
              f"{q['hyd_sdi_m']:.0f}/{q['hyd_sdi_a']:.0f} {q['hyd_dtd_m']:.0f}/{q['hyd_dtd_a']:.0f} | "
              f"{q['r_ch']:.3f}/{q['r_ch_daily']:.3f}/{q['r_ch_intra']:.3f} | {q['beta_c_on_h']:.3f} | "
              f"{q['u9_share_hyd_intra_var']:.3f}")
    print(json.dumps({y: rec[y] for y in YEARS}, indent=1))
    # (1b) per-plant intra-day sd, model / CROHMS, 2023-2025
    print("\n(1b) plant | MW | group | intra-day sd model/actual (MW) 2023, 2024, 2025 | ratio mean")
    mw = chain.set_index("plant_id").max_mw_eia860
    per = {}
    for grp, sts in (("uncoupled", UNCOUPLED), ("coupled_down", COUPLED_D), ("head", HEADS)):
        for st, pid in sts.items():
            vals = []
            for y in (2023, 2024, 2025):
                d = pd.read_parquet(legs / f"{y}_P1.parquet", columns=["plant_code", "hour", "mw"],
                                    filters=[("plant_code", "==", pid)])
                m = d.groupby("hour").mw.sum().reindex(range(N), fill_value=0).to_numpy()
                a = np.roll(_crohms(y)[st], -1)
                vals.append((_split(m)[1].std(), _split(a)[1].std()))
            ratio = float(np.mean([m / a for m, a in vals]))
            per[st] = dict(plant_id=pid, mw=float(mw[pid]), group=grp, sd=vals, ratio=round(ratio, 3))
            print(f"  {st} {pid} {mw[pid]:7.1f} {grp:12s} " +
                  " ".join(f"{m:5.0f}/{a:4.0f}" for m, a in vals) + f"  {ratio:.2f}")
    rec["per_plant"] = per
    return rec


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    rec = run(a.legs)
    if a.out:
        a.out.write_text(json.dumps(rec, indent=1, default=str))


if __name__ == "__main__":
    main()
