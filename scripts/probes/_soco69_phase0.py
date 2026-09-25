"""SOCO-69 phase 0 (ZERO LP): decompose the ST_GAS under-dispatch per plant and year.

Reads the keeper ``2026-09-25-soco68-summer-basis``'s per-year shard legs
``results/calibration/soco68_<Y>`` (gitignored; recovered at zero LP with
``git fetch origin claude/soco68-<Y>`` and ``git checkout <sha> --
results/calibration/soco68_<Y>`` from the SOCO-68 shard SHAs), the committed SOCO
benchmark (``frontend/data/backcast/bench/SOCO``) and CAMPD unit-level hourly for the
boiler units the committed ``campd_st_heat_rates_SOCO_units.csv`` attributes to
ST_GAS. Never solves (rule 32 ``[R-SHARD]`` (a)).

The deficit at a plant, ``D = sum_t (k * A_t - M_t)``, is split EXACTLY over a
partition of the plant's hours (declared before reading any number):

* ``A_t`` = CEMS gross MW summed over the plant's ST_GAS boiler units; ``k`` = the
  plant's benchmark net TWh / its CEMS gross TWh (the benchmark boundary), so
  ``sum k*A_t`` IS the benchmark plant row. CEMS-synchronized: ``A_t > 1 MW``.
* ``M_t`` = model P1 MW over the plant's ST_GAS tranches; ``C_t`` = the tranche
  availability (``cap_mw``) summed; model-online ``M_t > 1 MW``.

Legs (each is ``sum (kA - M)`` over its hours):

* **(c) avail** — CEMS synced, model availability ``C_t < 1`` (outage window/dark).
* **(a) hours** — CEMS synced, model available but OFF. Sub-split by the merit gap
  ``g_t = mc_committed_t - price_t`` of the plant's cheapest tranche:
  ``a<=1`` / ``a1-3`` / ``a3-6`` / ``a>6`` $/MWh (in a pure LP an available tranche
  is off only when ``g >= 0``; the gap is how far out of merit it sat).
* **(b) load** — both online; with ``(b_cap)`` the part in hours the model sat at
  its availability ceiling (``M >= 0.98 C``) while CEMS was above it (capability /
  basis) and ``(b_econ)`` the rest (loaded below its ceiling: merit order).
* **(e) extra** — model online, CEMS off (negative: energy the model makes that
  the plant did not).

(d) merit order is therefore read off the ``a`` gap bands and ``b_econ``; (c) off
``avail`` and ``b_cap``. The legs sum to ``D`` to float precision (asserted).
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
LEG = _ROOT / "results/calibration/soco68_{y}"
BENCH = _ROOT / "frontend/data/backcast/bench/SOCO/{y}.json.gz"
ST_UNITS = _ROOT / "data/raw/_processed-legacy/campd_st_heat_rates_SOCO_units.csv"
STATES = ("AL", "GA", "MS")
CEMS_STATES = ("AL", "GA", "MS", "FL")  # Crist (641) is in Pensacola, FL
GAP_BANDS = (1.0, 3.0, 6.0)  # $/MWh, declared ex ante


def bench_st(year: int) -> dict[int, float]:
    """Benchmark ST_GAS TWh per plant at the benchmark boundary."""
    b = json.load(gzip.open(str(BENCH).format(y=year)))["bench"]["plants"]
    out: dict[int, float] = {}
    for key, v in b.items():
        if v["group"] != "ST_GAS":
            continue
        em = v.get("e_mon") or v.get("c_mon")
        if em is None:
            continue
        code = int(str(key).split(":")[0])
        out[code] = out.get(code, 0.0) + float(np.nansum(em[:12])) / 1e3
    return out


def cems_st(year: int) -> pd.DataFrame:
    """CEMS gross MW per (plant, hour-of-year) over the ST_GAS boiler units."""
    u = pd.read_csv(ST_UNITS, dtype={"unit_id": str})
    keep = set(zip(u.plant_code.astype(int), u.unit_id.astype(str)))
    fr = []
    for st in CEMS_STATES:
        d = pd.read_parquet(_ROOT / f"data/raw/campd-unit-level/{st}_{year}.parquet",
                            columns=["facilityId", "unitId", "date", "hour", "grossLoad"])
        d["facilityId"] = pd.to_numeric(d.facilityId, errors="coerce").astype("Int64")
        m = [(int(f), str(x)) in keep if pd.notna(f) else False for f, x in zip(d.facilityId, d.unitId)]
        fr.append(d[m])
    d = pd.concat(fr)
    d["h"] = ((d.date - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + d.hour).astype(int)
    d = d[(d.h >= 0) & (d.h < 8760)]
    g = d.groupby(["facilityId", "h"]).grossLoad.sum(min_count=1).fillna(0.0)
    return g.rename("cems").reset_index().rename(columns={"facilityId": "plant_code", "h": "hour"})


def model_st(year: int) -> pd.DataFrame:
    """Model P1 MW, availability and committed-tranche mc per (plant, hour), with zone price."""
    leg = Path(str(LEG).format(y=year))
    u = pd.read_parquet(leg / f"hourly/unit_hourly_{year}.parquet",
                        columns=["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"])
    u = u[u.plant_group == "ST_GAS"].copy()
    u["unit_id"] = u.unit_id.astype(str)
    u["zone"] = u.zone.astype(str)
    g = u.groupby(["plant_code", "hour"]).agg(mw=("mw", "sum"), cap=("cap_mw", "sum"), zone=("zone", "first"))
    uc = u[u.cap_mw > 0].groupby(["plant_code", "hour"]).mc.min().rename("mc_min")
    g = g.join(uc)
    s = pd.read_parquet(leg / f"hourly/system_{year}.parquet", columns=["zone", "hour", "price"])
    g = g.reset_index().merge(s, on=["zone", "hour"], how="left")
    return g


def decompose(year: int) -> pd.DataFrame:
    """Per-plant exact partition of the ST_GAS deficit (TWh)."""
    b = bench_st(year)
    c = cems_st(year)
    m = model_st(year)
    rows = []
    for p in sorted(set(b) | set(m.plant_code.unique())):
        mp = m[m.plant_code == p].set_index("hour")
        cp = c[c.plant_code == p].set_index("hour").cems
        idx = pd.RangeIndex(8760)
        A = cp.reindex(idx).fillna(0.0).to_numpy()
        M = mp.mw.reindex(idx).fillna(0.0).to_numpy()
        C = mp.cap.reindex(idx).fillna(0.0).to_numpy()
        gap = (mp.mc_min - mp.price).reindex(idx).to_numpy()
        bt = b.get(p, 0.0) * 1e6
        k = bt / A.sum() if A.sum() > 0 else 0.0
        kA = k * A
        r = kA - M
        syn, on, av = A > 1.0, M > 1.0, C > 1.0
        leg = {
            "avail": syn & ~av,
            "a<=1": syn & av & ~on & (gap <= GAP_BANDS[0]),
            "a1-3": syn & av & ~on & (gap > GAP_BANDS[0]) & (gap <= GAP_BANDS[1]),
            "a3-6": syn & av & ~on & (gap > GAP_BANDS[1]) & (gap <= GAP_BANDS[2]),
            "a>6": syn & av & ~on & ((gap > GAP_BANDS[2]) | np.isnan(gap)),
            "b_cap": syn & on & (M >= 0.98 * C) & (kA > M),
            "b_econ": syn & on & ~((M >= 0.98 * C) & (kA > M)),
            "extra": ~syn & on,
        }
        rest = ~np.logical_or.reduce(list(leg.values()))
        row = dict(plant=p, bench=bt / 1e6, model=M.sum() / 1e6, D=r.sum() / 1e6, k=k,
                   H_cems=int(syn.sum()), H_mod=int(on.sum()), H_avail=int(av.sum()),
                   H_syn_unavail=int((syn & ~av).sum()), H_syn_off=int((syn & av & ~on).sum()))
        for name, mask in leg.items():
            row[name] = r[mask].sum() / 1e6
        row["other"] = r[rest].sum() / 1e6
        assert abs(sum(row[n] for n in list(leg) + ["other"]) - row["D"]) < 1e-6
        if A.sum() <= 0 and bt > 0:  # no CEMS boiler series for this plant (e.g. Crist 641)
            row["D"] = (bt - M.sum()) / 1e6
            row["other"] += bt / 1e6
        # loading when both on (MW)
        both = syn & on
        row["L_cems"] = kA[both].mean() if both.any() else np.nan
        row["L_mod"] = M[both].mean() if both.any() else np.nan
        row["C_mean_on"] = C[both].mean() if both.any() else np.nan
        row["gap_p50_off"] = np.nanmedian(gap[syn & av & ~on]) if (syn & av & ~on).any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2020, 2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--csv", type=Path, default=None)
    a = ap.parse_args()
    pd.set_option("display.width", 260)
    out = []
    for y in a.years:
        t = decompose(y)
        t.insert(0, "year", y)
        out.append(t)
        print(f"\n===== {y} =====")
        print(t.drop(columns="year").round(3).to_string(index=False))
        s = t[["bench", "model", "D", "avail", "a<=1", "a1-3", "a3-6", "a>6", "b_cap", "b_econ", "extra", "other"]].sum()
        print("TOTAL " + "  ".join(f"{k} {v:.3f}" for k, v in s.items()))
    if a.csv:
        pd.concat(out).to_csv(a.csv, index=False)



# ---------------------------------------------------------------------------
# Census + greedy for the chosen lever, coal_mustrun_requires_measured_row.
# ---------------------------------------------------------------------------
TRANCHES = _ROOT / "data/raw/_processed-legacy/thermal_tranches_SOCO.csv"
CLASSFULL_KEYS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB", "CC_CHP", "CT_CHP", "ST_CHP")
#: classes whose economic headroom may refill removed must-run MW (declared ex ante):
#: dispatchable thermal only -- hydro/storage/nuclear/renewables are energy- or
#: availability-limited and never refill at the margin.
REFILL = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC",
          "CC_CHP", "CT_CHP", "ST_CHP", "oil")


def measured_coal() -> set[int]:
    """Plant codes carrying a measured COAL row in thermal_tranches_SOCO.csv."""
    t = pd.read_csv(TRANCHES)
    return set(t[t.plant_group == "COAL"].plant_code.astype(int))


def greedy(year: int) -> dict:
    """Remove the unmeasured coal must-run slab hour by hour and refill cheapest-first.

    Removed MW per hour = the _mustrun tranche output at every coal plant with no
    measured row. That capacity is re-offered at the plant's own econ-low mc (the
    arm moves it to the economic band). Refill candidates: every REFILL-class tranche
    with headroom (cap - mw) whose mc is at or above the hour's zone price (a tranche
    below price with headroom is held by a constraint the greedy cannot see, so it is
    not counted). Cheapest first, zone-agnostic (SOCO's three zones never separate).
    """
    leg = Path(str(LEG).format(y=year))
    u = pd.read_parquet(leg / f"hourly/unit_hourly_{year}.parquet",
                        columns=["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"])
    u["unit_id"] = u.unit_id.astype(str)
    u["g"] = u.plant_group.astype(str)
    s = pd.read_parquet(leg / f"hourly/system_{year}.parquet", columns=["zone", "hour", "price"])
    price = s.groupby("hour").price.mean().reindex(range(8760)).to_numpy()
    meas = measured_coal()
    coal = u.g.str.startswith("COAL")
    mr = coal & u.unit_id.str.endswith("_mustrun") & ~u.plant_code.isin(meas)
    removed = u[mr].groupby("hour").mw.sum().reindex(range(8760)).fillna(0.0).to_numpy()
    # freed capacity re-offered at the plant's econ-low mc
    econ = u[coal & u.unit_id.str.endswith("_econlo")].set_index(["plant_code", "hour"]).mc
    fr = u[mr][["plant_code", "hour", "cap_mw", "g"]].copy()
    fr["mc"] = [econ.get((p, h), np.nan) for p, h in zip(fr.plant_code, fr.hour)]
    fr["head"] = fr.cap_mw
    fr["mw"] = 0.0
    fr["freed"] = True
    c = u[u.g.isin(REFILL) & ~mr].copy()
    c["head"] = (c.cap_mw - c.mw).clip(lower=0.0)
    c = c[(c["head"] > 0.01) & (c.mc >= price[c.hour.to_numpy()] - 0.01)]
    c["freed"] = False
    cand = pd.concat([c[["plant_code", "hour", "g", "mc", "head", "freed"]],
                      fr[["plant_code", "hour", "g", "mc", "head", "freed"]]]).dropna(subset=["mc"])
    cand = cand.sort_values(["hour", "mc"])
    cand["cum"] = cand.groupby("hour")["head"].cumsum()
    need = removed[cand.hour.to_numpy()]
    prev = cand.cum.to_numpy() - cand["head"].to_numpy()
    cand["take"] = np.clip(need - prev, 0.0, cand["head"].to_numpy())
    add = cand.groupby("g")["take"].sum() / 1e6
    rem = u[mr].groupby("g").mw.sum() / 1e6
    unmet = (removed - cand.groupby("hour")["take"].sum().reindex(range(8760)).fillna(0.0).to_numpy()).clip(min=0)
    delta = add.sub(rem, fill_value=0.0)
    # new marginal mc (the price proxy) where refill happened
    return dict(removed_twh=removed.sum() / 1e6, delta=delta.to_dict(), unmet_twh=unmet.sum() / 1e6,
                freed_self_twh=cand[cand.freed]["take"].sum() / 1e6)


def c1_rows(year: int, delta: dict) -> pd.DataFrame:
    """Keeper C1 class rows (composite span + committed bench) with the greedy delta applied."""
    b = json.load(gzip.open(str(BENCH).format(y=year)))["bench"]["classFull"]
    c = pd.read_parquet(_ROOT / f"results/calibration/soco68_span/hourly/class_hourly_{year}.parquet")
    mm = c.groupby(c.klass.astype(str)).mw.sum() / 1e6
    tot = sum(float(v) for v in b.values())
    rows = []
    for k in CLASSFULL_KEYS:
        a = float(b.get(k, 0.0))
        m0 = float(mm.get(k, 0.0))
        m1 = m0 + float(delta.get(k, 0.0))
        rows.append(dict(cls=k, actual=a, keeper=m0, arm=m1, d0=m0 - a, d1=m1 - a,
                         pp0=100 * (m0 - a) / tot, pp1=100 * (m1 - a) / tot, band_twh=0.03 * tot))
    return pd.DataFrame(rows)


def main_greedy(years: list[int]) -> None:
    """Print the census/greedy table for every year."""
    for y in years:
        g = greedy(y)
        print(f"\n===== {y}  removed {g['removed_twh']:.3f} TWh  refilled-by-freed-self {g['freed_self_twh']:.3f}"
              f"  unmet {g['unmet_twh']:.3f}")
        print("  class delta TWh: " + "  ".join(f"{k} {v:+.3f}" for k, v in sorted(g["delta"].items())))
        print(c1_rows(y, g["delta"]).round(3).to_string(index=False))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "greedy":
    main_greedy([int(a) for a in sys.argv[2:]] or [2019, 2020, 2021, 2022, 2023, 2024, 2025])
    sys.exit(0)


if __name__ == "__main__":
    main()
