"""SOCO-70 phase 0 (ZERO LP): what measured COAL rows for the five unmeasured plants would do.

Rule 32 ``[R-SHARD]`` (a): never solves. Three instruments, all at zero LP:

1. ``census`` — per unmeasured coal plant and year, the plant's own CEMS coal-unit
   conduct (CAMPD ``primaryFuelInfo`` names coal): gross TWh, synchronized hours,
   loading when synchronized, p25 CF when online, online fraction — against the
   keeper leg (``results/calibration/soco69_<Y>``) and the committed benchmark.
2. ``fleet`` — two ``fleet_only`` rebuilds per year on the keeper's OWN recipe
   (bundle ``soco69_span`` meta + ``derived_run_year_inputs``): the incumbent
   ``thermal_tranches_SOCO.csv`` and the candidate artifact (``--candidate``, the
   incumbent plus the ``--coal-unit-coverage`` rows). Differenced per (unit) on
   pmax / mc_base / min_gen / availability; every unit outside the five plants
   must be byte-identical (asserted).
3. ``greedy`` — a PRICE-TAKER estimate on the keeper's committed hourlies. Each
   affected plant's tranches are re-dispatched against the keeper leg's zone
   price: a tranche runs at its available capacity where its offer (fleet_only
   mc_base, plus — for a ``_committed`` tranche of a plant with NO must-run
   tranche — the P1 start markup measured on the keeper leg, which the
   ``coal_warm_committed`` exemption removes where a must-run tranche exists) is at
   or below the price, and a positive ``min_gen`` floor always runs. The plant
   delta then displaces (or is refilled by) the other dispatchable thermal units
   of the keeper leg, most-expensive-running first (or cheapest-headroom first),
   exactly the soco-69 greedy's refill rule. Reported per class with C1 pp and a
   C4 coal NRMSE re-score of the adjusted COAL hourly series.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_soco70_phase0.py census
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco70_phase0.py fleet --candidate <csv>
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco70_phase0.py greedy --candidate <csv>
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
LEG = _ROOT / "results/calibration/soco69_{y}"
SPAN = _ROOT / "results/calibration/soco69_span"
BENCH = _ROOT / "frontend/data/backcast/bench/SOCO/{y}.json.gz"
INCUMBENT = _ROOT / "data/raw/_processed-legacy/thermal_tranches_SOCO.csv"
PLANTS = {3: "AL", 26: "AL", 641: "FL", 6052: "GA", 6073: "MS"}
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
T = 8760
CLASSFULL_KEYS = (
    "CC_REGULAR",
    "CT_PEAKER",
    "ST_GAS",
    "COAL_BIT",
    "COAL_PRB",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
)
#: dispatchable thermal classes that absorb the plant delta (soco-69 greedy's set, declared ex ante).
REFILL = (
    "CC_REGULAR",
    "CT_PEAKER",
    "ST_GAS",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "COAL_WC",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "oil",
)


# ---------------------------------------------------------------------------
# 1. census
# ---------------------------------------------------------------------------
def cems_coal(plant: int, year: int) -> np.ndarray:
    """8760 CEMS gross MW over the plant's coal-labelled units (0 where not reported)."""
    st = PLANTS[plant]
    d = pd.read_parquet(
        _ROOT / f"data/raw/campd-unit-level/{st}_{year}.parquet",
        columns=[
            "facilityId",
            "unitId",
            "date",
            "hour",
            "grossLoad",
            "primaryFuelInfo",
        ],
    )
    d = d[d.facilityId.astype(str) == str(plant)]
    coal_units = set(
        d[d.primaryFuelInfo.astype(str).str.contains("Coal")].unitId.astype(str)
    )
    d = d[d.unitId.astype(str).isin(coal_units)]
    out = np.zeros(T)
    if d.empty:
        return out
    h = ((d.date - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + d.hour).to_numpy()
    ok = (h >= 0) & (h < T)
    np.add.at(
        out, h[ok].astype(int), np.nan_to_num(d.grossLoad.to_numpy(dtype=float))[ok]
    )
    return out


def bench_plant(year: int) -> dict[int, float]:
    """Benchmark (EIA-923 boundary) coal TWh per plant."""
    b = json.load(gzip.open(str(BENCH).format(y=year)))["bench"]["plants"]
    out: dict[int, float] = {}
    for key, v in b.items():
        if not str(v.get("group", "")).startswith("COAL"):
            continue
        em = v.get("e_mon") or v.get("c_mon")
        if em is None:
            continue
        code = int(str(key).split(":")[0])
        out[code] = out.get(code, 0.0) + float(np.nansum(em[:12])) / 1e3
    return out


def model_plant(year: int) -> pd.DataFrame:
    """Keeper-leg coal MW and capacity per (plant, hour)."""
    u = pd.read_parquet(
        Path(str(LEG).format(y=year)) / f"hourly/unit_hourly_{year}.parquet",
        columns=["plant_code", "plant_group", "hour", "mw", "cap_mw"],
    )
    u = u[u.plant_group.astype(str).str.startswith("COAL")]
    return u.groupby(["plant_code", "hour"], observed=True)[["mw", "cap_mw"]].sum()


def main_census() -> None:
    """Print the per-plant, per-year census."""
    rows = []
    for y in YEARS:
        b = bench_plant(y)
        m = model_plant(y)
        for p in PLANTS:
            a = cems_coal(p, y)
            mp = m.loc[p] if p in m.index.get_level_values(0) else None
            cap = (
                mp.cap_mw.reindex(range(T)).fillna(0).to_numpy()
                if mp is not None
                else np.zeros(T)
            )
            mw = (
                mp.mw.reindex(range(T)).fillna(0).to_numpy()
                if mp is not None
                else np.zeros(T)
            )
            npl = cap.max() if cap.max() > 0 else np.nan
            syn = a > 0.01 * (npl if np.isfinite(npl) else 1.0)
            rows.append(
                dict(
                    year=y,
                    plant=p,
                    bench_twh=round(b.get(p, 0.0), 3),
                    cems_gross_twh=round(a.sum() / 1e6, 3),
                    model_twh=round(mw.sum() / 1e6, 3),
                    np_mw=round(npl, 1) if np.isfinite(npl) else None,
                    sync_h=int(syn.sum()),
                    online_frac=round(syn.mean(), 3),
                    load_when_sync=round(float(a[syn].mean() / npl), 3)
                    if syn.any() and np.isfinite(npl)
                    else None,
                    p25_on=round(float(np.percentile(a[syn] / npl, 25)), 3)
                    if syn.any() and np.isfinite(npl)
                    else None,
                    model_on_h=int((mw > 1).sum()),
                    model_avail_h=int((cap > 1).sum()),
                    cems_sync_while_model_unavail_h=int((syn & (cap <= 1)).sum()),
                )
            )
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(t.to_string(index=False))


# ---------------------------------------------------------------------------
# 2. fleet_only rebuilds
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def artifact(path: Path | None):
    """Swap the SOCO thermal-tranche artifact in place for the duration (restored after)."""
    if path is None:
        yield
        return
    backup = INCUMBENT.with_suffix(".csv.soco70bak")
    shutil.copyfile(INCUMBENT, backup)
    try:
        shutil.copyfile(path, INCUMBENT)
        yield
    finally:
        shutil.move(str(backup), INCUMBENT)


def rebuild(year: int, candidate: Path | None) -> dict:
    """fleet_only rebuild on the keeper recipe; returns per-unit arrays."""
    sys.path.insert(0, str(_ROOT / "scripts"))
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches
    from market_sim.data.fleet import campd_bins

    meta = json.loads((SPAN / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    with artifact(candidate):
        clear_fleet_caches()
        for fn in (
            "thermal_tranche_overrides",
            "thermal_tranche_online_frac",
            "thermal_tranche_peaking",
        ):
            f = getattr(campd_bins, fn, None)
            if f is not None and hasattr(f, "cache_clear"):
                f.cache_clear()
        with (
            contextlib.redirect_stderr(io.StringIO()),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            st = run_year(
                year,
                meta["iso"],
                T,
                float(meta["gas_prices"][str(year)]),
                {},
                fleet_only=True,
                **kw,
            )
    fa = st["fleet_arrays"]
    return dict(
        unit_ids=list(map(str, fa.unit_ids)),
        pmax=np.asarray(fa.pmax, float),
        mc=np.asarray(st["mc_base"], float),
        min_gen=np.asarray(fa.min_gen, float),
        avail=np.asarray(fa.availability, float),
        plant=np.asarray(fa.plant_code),
    )


def _rows(r: dict) -> pd.DataFrame:
    ids = r["unit_ids"]
    mc = r["mc"] if r["mc"].ndim == 2 else np.repeat(r["mc"][:, None], T, axis=1)
    mg = (
        r["min_gen"]
        if r["min_gen"].ndim == 2
        else np.repeat(r["min_gen"][:, None], T, axis=1)
    )
    return pd.DataFrame(
        dict(
            unit_id=ids,
            plant=r["plant"],
            pmax=r["pmax"],
            mc_med=np.median(mc, axis=1),
            floor_twh=mg.sum(axis=1) / 1e6,
            avail_mean=r["avail"].mean(axis=1),
        )
    )


def main_fleet(candidate: Path, years: list[int]) -> dict:
    """Difference incumbent vs candidate fleet_only arrays per year."""
    out = {}
    for y in years:
        a, b = rebuild(y, None), rebuild(y, candidate)
        ra, rb = _rows(a), _rows(b)

        def five(r: pd.DataFrame) -> np.ndarray:
            return (
                np.isin(r.plant.to_numpy(), list(PLANTS))
                & r.unit_id.str.startswith("COAL")
            ).to_numpy()

        ia = {u: i for i, u in enumerate(a["unit_ids"])}
        ib = {u: i for i, u in enumerate(b["unit_ids"])}
        rest = [u for u, m in zip(ra.unit_id, five(ra)) if not m]
        rest_b = [u for u, m in zip(rb.unit_id, five(rb)) if not m]
        other_same = rest == rest_b and all(
            np.array_equal(
                np.asarray(a[k])[[ia[u] for u in rest]],
                np.asarray(b[k])[[ib[u] for u in rest]],
            )
            for k in ("pmax", "mc", "min_gen", "avail")
        )
        print(
            f"\n===== {y}  units {len(ra)} -> {len(rb)}  outside the five coal plants byte-identical: {other_same}"
        )
        cmp = ra[five(ra)].merge(
            rb[five(rb)], on=["unit_id", "plant"], how="outer", suffixes=("_k", "_c")
        )
        print(cmp.sort_values("unit_id").round(3).to_string(index=False))
        out[y] = dict(k=a, c=b, other_same=other_same)
    return out


# ---------------------------------------------------------------------------
# 3. greedy
# ---------------------------------------------------------------------------
def greedy(year: int, arm: dict) -> dict:
    """Price-taker re-dispatch of the five plants, refill/displace on the keeper leg."""
    leg = Path(str(LEG).format(y=year))
    u = pd.read_parquet(
        leg / f"hourly/unit_hourly_{year}.parquet",
        columns=[
            "unit_id",
            "plant_code",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    u["unit_id"] = u.unit_id.astype(str)
    u["g"] = u.plant_group.astype(str)
    s = pd.read_parquet(
        leg / f"hourly/system_{year}.parquet", columns=["zone", "hour", "price"]
    )
    price = s.groupby("hour").price.mean().reindex(range(T)).to_numpy()
    mine = u.g.str.startswith("COAL") & u.plant_code.isin(list(PLANTS))
    old = u[mine]
    # keeper P1 start markup on the unmeasured plants' _committed tranche (P1 mc - econlo mc)
    k_mc = old.pivot_table(index="hour", columns="unit_id", values="mc", observed=True)
    ids, pmax, mc_c = arm["unit_ids"], arm["pmax"], arm["mc"]
    mg = (
        arm["min_gen"]
        if arm["min_gen"].ndim == 2
        else np.repeat(arm["min_gen"][:, None], T, axis=1)
    )
    av = arm["avail"]
    new_by_plant = {}
    for p in PLANTS:
        idx = [
            i
            for i, x in enumerate(ids)
            if x.startswith("COAL") and int(arm["plant"][i]) == p
        ]
        if not idx:
            continue
        has_mr = any(ids[i].endswith("_mustrun") for i in idx)
        tot = np.zeros(T)
        for i in idx:
            cap = pmax[i] * av[i]
            off = mc_c[i] if mc_c.ndim == 2 else np.full(T, mc_c[i])
            if ids[i].endswith("_committed") and not has_mr:
                c_id, e_id = ids[i], ids[i].replace("_committed", "_econlo")
                if c_id in k_mc and e_id in k_mc:
                    off = (
                        off
                        + (k_mc[c_id] - k_mc[e_id])
                        .reindex(range(T))
                        .fillna(0)
                        .to_numpy()
                    )
            run = np.where(off <= price + 1e-6, cap, 0.0)
            tot += np.maximum(run, np.minimum(mg[i], cap))
        new_by_plant[p] = tot
    old_by_plant = old.groupby(["plant_code", "hour"]).mw.sum()
    delta_t = np.zeros(T)
    plant_delta = {}
    grp = {
        p: str(old[old.plant_code == p].g.iloc[0])
        for p in new_by_plant
        if (old.plant_code == p).any()
    }
    for p, new in new_by_plant.items():
        o = (
            old_by_plant.loc[p].reindex(range(T)).fillna(0).to_numpy()
            if p in old_by_plant.index.get_level_values(0)
            else np.zeros(T)
        )
        plant_delta[p] = (new.sum() - o.sum()) / 1e6
        delta_t += new - o
    # displacement (delta>0): back down running REFILL units, most expensive first
    oth = u[u.g.isin(REFILL) & ~mine].copy()
    down = oth[oth.mw > 0.01][["hour", "g", "mc", "mw"]].sort_values(
        ["hour", "mc"], ascending=[True, False]
    )
    down["cum"] = down.groupby("hour").mw.cumsum()
    need = np.clip(delta_t, 0, None)[down.hour.to_numpy()]
    prev = down.cum.to_numpy() - down.mw.to_numpy()
    down["take"] = np.clip(need - prev, 0, down.mw.to_numpy())
    up = oth.assign(head=(oth.cap_mw - oth.mw).clip(lower=0))
    up = up[(up["head"] > 0.01)][["hour", "g", "mc", "head"]].sort_values(
        ["hour", "mc"]
    )
    up["cum"] = up.groupby("hour")["head"].cumsum()
    need2 = np.clip(-delta_t, 0, None)[up.hour.to_numpy()]
    prev2 = up.cum.to_numpy() - up["head"].to_numpy()
    up["take"] = np.clip(need2 - prev2, 0, up["head"].to_numpy())
    d = (
        up.groupby("g")["take"].sum().sub(down.groupby("g")["take"].sum(), fill_value=0)
    ) / 1e6
    for p, dp in plant_delta.items():
        d[grp[p]] = d.get(grp[p], 0.0) + dp
    unmet = (
        np.clip(delta_t, 0, None).sum()
        - down["take"].sum()
        + np.clip(-delta_t, 0, None).sum()
        - up["take"].sum()
    ) / 1e6
    coal_other = np.zeros(T)
    for frame, sign in ((up, 1.0), (down, -1.0)):
        f = frame[frame.g.str.startswith("COAL")]
        coal_other += (
            sign
            * f.groupby("hour")["take"].sum().reindex(range(T)).fillna(0).to_numpy()
        )
    return dict(
        delta=d.to_dict(),
        plant_delta=plant_delta,
        unmet=unmet,
        coal_delta_t=delta_t + coal_other,
    )


def c1_rows(year: int, delta: dict) -> pd.DataFrame:
    """Keeper C1 rows with the greedy delta applied."""
    b = json.load(gzip.open(str(BENCH).format(y=year)))["bench"]["classFull"]
    c = pd.read_parquet(SPAN / f"hourly/class_hourly_{year}.parquet")
    mm = c.groupby(c.klass.astype(str)).mw.sum() / 1e6
    tot = sum(float(v) for v in b.values())
    rows = []
    for k in CLASSFULL_KEYS:
        a = float(b.get(k, 0.0))
        m0 = float(mm.get(k, 0.0))
        m1 = m0 + float(delta.get(k, 0.0))
        rows.append(
            dict(
                cls=k,
                actual=a,
                keeper=m0,
                arm=m1,
                pp0=100 * (m0 - a) / tot,
                pp1=100 * (m1 - a) / tot,
            )
        )
    return pd.DataFrame(rows)


def c4_coal(year: int, coal_delta_t: np.ndarray) -> tuple[float, float, float, float]:
    """C4 coal (r, NRMSE) keeper vs keeper+greedy, render_calibration_html's construction.

    Model = every coal class's hourly MW (the span's class_hourly), actual = the
    EIA-930 ``coal`` series from the keeper's restored shared input
    (``run_calibration_full --restore-shared-inputs results/calibration/soco69_span``).
    The greedy's hourly coal delta (the five plants plus any other coal unit it
    displaced or refilled) is added to the keeper series.
    """
    sys.path.insert(0, str(_ROOT / "scripts"))
    from scripts.lib.bundle_io import require_bundle_input

    e = pd.read_parquet(require_bundle_input(SPAN, "eia930"))
    e = (
        e[(e.year == year) & (e.series == "coal")]
        .sort_values("hour")["mw"]
        .to_numpy(float)[:T]
    )
    c = pd.read_parquet(SPAN / f"hourly/class_hourly_{year}.parquet")
    c = c[c.klass.astype(str).str.startswith("COAL")]
    m0 = c.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
    m1 = m0 + coal_delta_t

    def fit(m: np.ndarray) -> tuple[float, float]:
        return float(np.corrcoef(m, e)[0, 1]), float(
            np.sqrt(((m - e) ** 2).mean()) / e.mean()
        )

    (r0, n0), (r1, n1) = fit(m0), fit(m1)
    return r0, n0, r1, n1


def main_greedy(candidate: Path, years: list[int]) -> None:
    """Rebuild the arm's fleet and print the greedy class / C1 table per year."""
    for y in years:
        arm = rebuild(y, candidate)
        g = greedy(y, arm)
        r0, n0, r1, n1 = c4_coal(y, g["coal_delta_t"])
        print(
            f"  C4 coal: keeper r={r0:.3f} nrmse={n0:.3f}  ->  arm~ r={r1:.3f} nrmse={n1:.3f}"
        )
        print(
            f"\n===== {y}  plant deltas TWh "
            + "  ".join(f"{p}:{v:+.3f}" for p, v in g["plant_delta"].items())
            + f"  unabsorbed {g['unmet']:.3f}"
        )
        print(
            "  class delta TWh: "
            + "  ".join(
                f"{k} {v:+.3f}" for k, v in sorted(g["delta"].items()) if abs(v) > 1e-4
            )
        )
        print(c1_rows(y, g["delta"]).round(3).to_string(index=False))


# ---------------------------------------------------------------------------
# 4. post-solve comparison (zero LP): the soco-70 legs against the keeper legs.
# ---------------------------------------------------------------------------
ARM_LEG = _ROOT / "results/calibration/soco70_{y}"
KEYS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB", "CC_CHP", "CT_CHP", "ST_CHP",
        "nuclear", "hydro", "wind", "solar")


def compare(year: int) -> dict:
    """Class deltas, unserved, plant coal TWh and the PRECOMMIT §5(2) cap_mw identity for one year."""
    k, a = Path(str(LEG).format(y=year)), Path(str(ARM_LEG).format(y=year))
    ck = pd.read_parquet(k / f"hourly/class_hourly_{year}.parquet")
    ca = pd.read_parquet(a / f"hourly/class_hourly_{year}.parquet")
    d = (ca.groupby(ca.klass.astype(str)).mw.sum() - ck.groupby(ck.klass.astype(str)).mw.sum()) / 1e6
    sk = pd.read_parquet(k / f"hourly/system_{year}.parquet", columns=["slack"]).slack.sum()
    sa = pd.read_parquet(a / f"hourly/system_{year}.parquet", columns=["slack"]).slack.sum()
    cols = ["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw"]
    uk = pd.read_parquet(k / f"hourly/unit_hourly_{year}.parquet", columns=cols)
    ua = pd.read_parquet(a / f"hourly/unit_hourly_{year}.parquet", columns=cols)

    def five(u: pd.DataFrame) -> pd.Series:
        return u.plant_group.astype(str).str.startswith("COAL") & u.plant_code.isin(list(PLANTS))

    ok_ = uk[~five(uk)].sort_values(["unit_id", "hour"])
    oa_ = ua[~five(ua)].sort_values(["unit_id", "hour"])
    cap_same = list(ok_.unit_id.astype(str)) == list(oa_.unit_id.astype(str)) and np.array_equal(
        ok_.cap_mw.to_numpy(), oa_.cap_mw.to_numpy()
    )
    pk = uk[five(uk)].groupby("plant_code").mw.sum() / 1e6
    pa = ua[five(ua)].groupby("plant_code").mw.sum() / 1e6
    mrk = uk[uk.unit_id.astype(str).str.endswith("_mustrun") & uk.plant_code.isin([703, 6002, 6257])].groupby("plant_code").mw.sum() / 1e6
    mra = ua[ua.unit_id.astype(str).str.endswith("_mustrun") & ua.plant_code.isin([703, 6002, 6257])].groupby("plant_code").mw.sum() / 1e6
    return dict(delta=d, slack=(sk, sa), cap_same=cap_same, plant=(pk, pa), measured_mr=(mrk, mra))


def main_compare(years: list[int]) -> None:
    """Print the post-solve comparison for every year."""
    rows = []
    for y in years:
        r = compare(y)
        rows.append({"year": y, **{k: round(float(r["delta"].get(k, 0.0)), 3) for k in KEYS},
                     "slack_k": round(r["slack"][0], 1), "slack_a": round(r["slack"][1], 1)})
        pk, pa = r["plant"]
        mk, ma = r["measured_mr"]
        print(f"{y}: other-unit cap_mw identical {r['cap_same']}  plant coal TWh keeper->arm "
              + "  ".join(f"{p}:{pk.get(p, 0):.3f}->{pa.get(p, 0):.3f}" for p in PLANTS)
              + "  | measured mustrun " + "  ".join(f"{p}:{mk.get(p, 0):.3f}->{ma.get(p, 0):.3f}" for p in (703, 6002, 6257)))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["census", "fleet", "greedy", "compare"])
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    a = ap.parse_args()
    if a.mode == "census":
        main_census()
    elif a.mode == "fleet":
        main_fleet(a.candidate, a.years)
    elif a.mode == "greedy":
        main_greedy(a.candidate, a.years)
    else:
        main_compare(a.years)
