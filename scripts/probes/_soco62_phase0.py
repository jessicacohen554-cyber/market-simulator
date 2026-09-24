"""SOCO-62 phase 0 (ZERO LP): measure the three routed leads for the 2023 CT_PEAKER/ST_GAS split.

Reads the keeper ``2026-09-24-soco61-dark-unit``'s per-plant legs
``results/calibration/soco61_arm_<Y>`` (gitignored; recovered at zero LP with
``git fetch origin <sha> && git checkout <sha> -- results/calibration/soco61_arm_<Y>``
from the SOCO-61 shard SHAs), the committed composite's hourlies, the committed
SOCO benchmark (``frontend/data/backcast/bench/SOCO``), CAMPD unit-level hourly and
the committed CAMPD heat-rate artifacts. Never solves (rule 32 ``[R-SHARD]`` (a)).

Subcommands:

* ``plants``  -- per plant, CT_PEAKER + ST_GAS: model TWh, availability TWh, online
  hours (plant MW > 1), capacity-weighted ``mc``, EIA-923 net (benchmark boundary).
* ``decomp``  -- the four campaign-duty ST_GAS plants' deficit split into a
  COMMITMENT-HOURS part and a LOADING part (lead 1).
* ``floorcap`` -- the most energy a commitment floor at the registered campaign
  level could add if every measured synchronized hour were committed (lead 1).
* ``ctbasis`` -- CT loaded (>= 0.8 x p95) vs operating (opTime >= 0.99) heat-rate
  basis at SOCO's CT plants (the ST sibling is on the operating basis).
* ``monthly`` -- model minus benchmark by month for CC / COAL / CT / ST (lead 3).
* ``parasitic`` -- in-memory SOCO parasitic-factor census (the shared artifact
  carries no SOCO row); nothing is written to the shared file.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts"), str(_ROOT / "scripts/data")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LEG = _ROOT / "results/calibration/soco61_arm_{y}"
SPAN = _ROOT / "results/calibration/soco61_dark_unit_span"
BENCH = _ROOT / "frontend/data/backcast/bench/SOCO/{y}.json.gz"
CAMPAIGN = _ROOT / "data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv"
CT_HR = _ROOT / "data/raw/_processed-legacy/campd_ct_heat_rates_SOCO.csv"
ST_HR = _ROOT / "data/raw/_processed-legacy/campd_st_heat_rates_SOCO.csv"
STATES = ("AL", "GA", "MS")
CLASSES = ("CT_PEAKER", "ST_GAS")


def bench_plants(year: int) -> dict:
    """The committed benchmark's per-plant block for ``year``."""
    return json.load(gzip.open(str(BENCH).format(y=year)))["bench"]["plants"]


def bench_plant_twh(year: int) -> dict[tuple[str, int], float]:
    """Benchmark annual TWh keyed by (group, plant_code) at the benchmark boundary."""
    out: dict[tuple[str, int], float] = {}
    for key, v in bench_plants(year).items():
        code = int(str(key).split(":")[0])
        em = v.get("e_mon") or v.get("c_mon")
        if em is None:
            continue
        out[(v["group"], code)] = out.get((v["group"], code), 0.0) + float(np.nansum(em[:12])) / 1e3
    return out


def plants(year: int) -> pd.DataFrame:
    """Per-plant CT_PEAKER/ST_GAS model vs benchmark (TWh), online hours and mc."""
    d = pd.read_parquet(Path(str(LEG).format(y=year)) / f"dispatch/{year}_P1.parquet",
                        columns=["unit_id", "plant_code", "klass", "hour", "mw"])
    u = pd.read_parquet(Path(str(LEG).format(y=year)) / f"hourly/unit_hourly_{year}.parquet",
                        columns=["unit_id", "hour", "cap_mw", "mc"])
    d = d[d.klass.isin(CLASSES)].merge(u, on=["unit_id", "hour"], how="left")
    ph = d.groupby(["klass", "plant_code", "hour"], observed=True).agg(mw=("mw", "sum"), cap=("cap_mw", "sum"))
    g = ph.groupby(level=[0, 1], observed=True).agg(
        model_twh=("mw", lambda s: s.sum() / 1e6),
        avail_twh=("cap", lambda s: s.sum() / 1e6),
        online_h=("mw", lambda s: int((s > 1).sum())),
    )
    g["mc_capw"] = d.groupby(["klass", "plant_code"], observed=True).apply(
        lambda x: np.average(x.mc, weights=x.cap_mw + 1e-9), include_groups=False)
    bt = bench_plant_twh(year)
    g["bench_twh"] = [bt.get((k, int(p)), 0.0) for k, p in g.index]
    g["err"] = g.model_twh - g.bench_twh
    return g


def decomp(year: int) -> pd.DataFrame:
    """ST_GAS deficit at the campaign-duty plants = commitment-hours part + loading part.

    Actual synchronized hours are the campaign artifact's own per-year counts;
    actual loading = benchmark TWh / synchronized hours; model loading = model
    TWh / model online hours. hours-part = (H_act - H_mod) x L_act;
    loading-part = H_mod x (L_act - L_mod). The two sum to the deficit exactly.
    """
    camp = pd.read_csv(CAMPAIGN)
    camp = camp[camp.flag == "ok"]
    g = plants(year).loc["ST_GAS"]
    rows = []
    for _, r in camp.iterrows():
        per = dict(s.split(":") for s in r.per_year.split(";"))
        h_act = int(per[str(year)].split("h")[0])
        p = int(r.plant_code)
        e_a, e_m, h_m = g.loc[p, "bench_twh"], g.loc[p, "model_twh"], g.loc[p, "online_h"]
        la, lm = e_a / h_act, e_m / h_m
        rows.append(dict(plant=p, name=r.plant_name, H_act=h_act, H_mod=h_m,
                         L_act_mw=la * 1e6, L_mod_mw=lm * 1e6,
                         hours_part=(h_act - h_m) * la, loading_part=h_m * (la - lm),
                         deficit=e_a - e_m))
    return pd.DataFrame(rows)


def floorcap(year: int) -> pd.DataFrame:
    """Max energy a floor at the registered campaign level adds over the model's own online hours."""
    camp = pd.read_csv(CAMPAIGN)
    camp = camp[camp.flag == "ok"]
    dc = decomp(year).set_index("plant")
    out = []
    for _, r in camp.iterrows():
        p = int(r.plant_code)
        extra_h = max(0, dc.loc[p, "H_act"] - dc.loc[p, "H_mod"])
        out.append(dict(plant=p, extra_hours=extra_h, floor_mw=r.min_load_frac * r.class_capacity_mw,
                        floor_twh=extra_h * r.min_load_frac * r.class_capacity_mw / 1e6))
    return pd.DataFrame(out)


def ctbasis() -> pd.DataFrame:
    """CT operating-hour vs loaded-hour heat rate, per plant, pooled 2023-2025, gross basis."""
    codes = set(pd.read_csv(CT_HR).plant_code)
    fr = []
    for st in STATES:
        for y in (2023, 2024, 2025):
            d = pd.read_parquet(_ROOT / f"data/raw/campd-unit-level/{st}_{y}.parquet",
                                columns=["facilityId", "unitId", "opTime", "grossLoad", "heatInput", "unitType"])
            d["facilityId"] = pd.to_numeric(d.facilityId, errors="coerce")
            fr.append(d[d.facilityId.isin(codes) & (d.unitType == "Combustion turbine")])
    d = pd.concat(fr)
    d = d[(d.grossLoad > 0) & (d.heatInput > 0)]
    d = d[(d.heatInput / d.grossLoad).between(6.0, 25.0)]  # the CT deriver's own physical band
    rows = []
    for (f, _u), g in d.groupby(["facilityId", "unitId"]):
        p95 = np.percentile(g.grossLoad, 95)
        loaded, oper = g[g.grossLoad >= 0.8 * p95], g[g.opTime >= 0.99]
        if len(loaded) < 50 or oper.empty:
            continue
        rows.append(dict(plant=int(f), gwh=g.grossLoad.sum() / 1e3,
                         hr_loaded=loaded.heatInput.sum() / loaded.grossLoad.sum(),
                         hr_oper=oper.heatInput.sum() / oper.grossLoad.sum()))
    r = pd.DataFrame(rows)
    p = r.groupby("plant").apply(lambda x: pd.Series(dict(
        gwh=x.gwh.sum(), hr_loaded=np.average(x.hr_loaded, weights=x.gwh),
        hr_oper=np.average(x.hr_oper, weights=x.gwh))), include_groups=False)
    p["oper_over_loaded"] = p.hr_oper / p.hr_loaded
    return p


def monthly(year: int) -> pd.DataFrame:
    """Model minus benchmark, GWh by month, CC_REGULAR / COAL / CT_PEAKER / ST_GAS."""
    act: dict[str, np.ndarray] = {}
    for _k, v in bench_plants(year).items():
        g = "COAL" if v["group"].startswith("COAL") else v["group"]
        em = v.get("e_mon") or v.get("c_mon")
        if em is None:
            continue
        act.setdefault(g, np.zeros(12))
        act[g] += np.nan_to_num(np.array(em[:12], float))
    c = pd.read_parquet(SPAN / f"hourly/class_hourly_{year}.parquet")
    c["mo"] = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(c.hour, unit="h")).dt.month
    k = c.klass.astype(str)
    c["k"] = k.where(~k.str.startswith("COAL"), "COAL")
    mm = c.groupby(["k", "mo"]).mw.sum().unstack(0) / 1e3
    return pd.DataFrame({g: mm[g].to_numpy() - act[g] for g in ("CC_REGULAR", "COAL", "CT_PEAKER", "ST_GAS")},
                        index=range(1, 13))


def parasitic() -> pd.DataFrame:
    """SOCO pooled parasitic factors computed in memory (the shared artifact carries none)."""
    import derive_parasitic_load as dp
    from market_sim.data import campd
    from market_sim.data.eia923 import load_monthly_generation

    df = campd.load_campd_hourly(list(STATES), [2023, 2024, 2025])
    gen = load_monthly_generation()
    net = campd.eia923_combustion_net(gen[gen["year"].isin([2023, 2024, 2025])])
    p = campd.compute_parasitic_factors(campd.annual_plant_totals(df), net,
                                        plant_groups=dp._registry_plant_groups())
    pool = p[p.year == 0][["plant_id", "parasitic_factor", "source", "flag"]]
    used = pd.concat([pd.read_csv(CT_HR).assign(cls="CT_PEAKER"), pd.read_csv(ST_HR).assign(cls="ST_GAS")])
    return used[["cls", "plant_code", "plant_name", "parasitic_factor"]].merge(
        pool, left_on="plant_code", right_on="plant_id", how="left", suffixes=("_applied", "_measured"))


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=("plants", "decomp", "floorcap", "ctbasis", "monthly", "parasitic"))
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024])
    a = ap.parse_args()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 200)
    if a.cmd == "ctbasis":
        t = ctbasis()
        print(t.round(3).to_string())
        print(f"gen-weighted oper/loaded {np.average(t.oper_over_loaded, weights=t.gwh):.4f}")
        return
    if a.cmd == "parasitic":
        t = parasitic()
        print(t.round(4).to_string(index=False))
        print(t.flag.value_counts(dropna=False).to_string())
        return
    for y in a.years:
        print(f"\n===== {y} =====")
        if a.cmd == "plants":
            t = plants(y)
            print(t.round(3).sort_values(["err"]).to_string())
            print(t.groupby(level=0, observed=True)[["model_twh", "bench_twh", "err"]].sum().round(3).to_string())
        elif a.cmd == "decomp":
            t = decomp(y)
            print(t.round(3).to_string(index=False))
            print(f"TOTAL hours_part {t.hours_part.sum():.3f}  loading_part {t.loading_part.sum():.3f}"
                  f"  deficit {t.deficit.sum():.3f} TWh")
        elif a.cmd == "floorcap":
            t = floorcap(y)
            print(t.round(3).to_string(index=False))
            print(f"TOTAL floor-level energy at full measured sync {t.floor_twh.sum():.3f} TWh")
        else:
            t = monthly(y)
            print(t.round(0).T.to_string())
            print(t.sum().round(0).to_string())


if __name__ == "__main__":
    main()
