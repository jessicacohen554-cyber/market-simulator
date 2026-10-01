"""SPP-105 (zero LP): the keeper's hourly GAS unavailability by class and component, against SPP's
own published hourly Natural Gas outage, with the scarce-hour (upper-tercile RT) cut.

Record: ``docs/records/spp/DESIGN-spp-105-gas-family-outage-2026-09-30.md``.

Rebuilds the designated keeper ``results/calibration/spp100_arm_span`` ``fleet_only`` per year
(``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``, no LP) under three DECOMPOSITION variants
(instruments, never configs), all on SPP-104's outage-type basis (the flat GADS performance
derate and the flat summer ambient class derate zeroed, since SPP's CROW report does not carry
ambient derates -- MMU Dec 2025 s3.3.1.2):

* ``full``   -- WEFOR (x wefor_multiplier, seasonal split) + shoulder POF + CAMPD event windows;
* ``nowefor`` -- the statistical WEFOR zeroed too (POF + CAMPD windows);
* ``event``  -- every statistical term zeroed (CAMPD event windows only).

so ``full - nowefor`` is the statistical WEFOR and ``nowefor - event`` the POF. Per gas class it
reports annual, body (RT < p67) and upper-tercile (p67 <= RT < p99, Feb excluded -- SPP-84's cut)
means, monthly and hour-of-day profiles, and the hourly / daily correlation of the keeper's gas
total with SPP's published total.

Leg R (``--reclear``): SPP-84's gas-only re-clear instrument (merit-clear the keeper's own stack at
its own non-VER P1 generation, system-wide, one zone, no ramps; only deltas used) applied to the
candidate carriers of the DESIGN doc's s4, each a deterministic function of inputs fixed before
this probe ran.

SPP published outage: portal ``capacity-of-generation-on-outage`` year zips ``o<y>.zip`` (2019-24)
plus ``o2025.zip`` assembled from the 2025 daily CSVs
(``?path=%2F2025%2F<MM>%2FCapacity-Gen-Outage-<YYYYMMDD>.csv``; the 2025 year zip is 0 bytes).
Solves nothing. Usage:
``python scripts/probes/_spp105_gas_outage_hourly_phase0.py --cache <dir> --outage <dir> --out <json>``
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp84_published_outage_rebasis import (  # noqa: E402
    load_outage_zips,
    merit,
    spp_outage_on_model_clock,
)

DESIGN = "docs/records/spp/DESIGN-spp-105-gas-family-outage-2026-09-30.md"
BUNDLE = REPO_ROOT / "results/calibration/spp100_arm_span"
YEARS = tuple(range(2019, 2026))
GAS = ("gas_cc", "gas_ct", "gas_st")
VER = ("WIND", "SOLAR", "STORAGE", "BATTERY")
EDGE_H = 30 * 24
VARIANTS = ("full", "nowefor", "event")


def rebuild(y: int, cache: Path, variant: str) -> dict:
    """``fleet_only`` rebuild of keeper year ``y`` under one decomposition variant (cached)."""
    p = cache / f"spp105_{y}_{variant}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from market_sim.data.fleet import arrays as _arr

    orig_out, orig_sum = _arr._thermal_outage, dict(_arr._SUMMER_CLASS_DERATE)

    def _patched(c, a):
        pof, wefor, _derate = orig_out(c, a)
        if variant == "full":
            return pof, wefor, 0.0
        if variant == "nowefor":
            return pof, 0.0, 0.0
        return 0.0, 0.0, 0.0

    _arr._thermal_outage = _patched
    _arr._SUMMER_CLASS_DERATE.clear()
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    finally:
        _arr._thermal_outage = orig_out
        _arr._SUMMER_CLASS_DERATE.clear()
        _arr._SUMMER_CLASS_DERATE.update(orig_sum)
    fa = st["fleet_arrays"]
    keys = ("unit_id", "fuel_type", "plant_group", "zone", "plant_code", "online_year")
    out = {
        "rows": [{k: getattr(g, k, None) for k in keys} for g in st["fleet"]],
        "pmax": np.asarray(fa.pmax, dtype=np.float32),
        "availability": np.asarray(fa.availability, dtype=np.float32),
    }
    if variant == "full":
        out["mc"] = np.asarray(st["mc_base"], dtype=np.float32)
    p.write_bytes(pickle.dumps(out))
    return out


def rebuild_rated(y: int, cache: Path) -> dict:
    """The keeper's own rebuild (every component, rated basis): the re-clear's base stack."""
    p = cache / f"spp105_{y}_rated.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    fa = st["fleet_arrays"]
    out = {
        "pmax": np.asarray(fa.pmax, dtype=np.float32),
        "availability": np.asarray(fa.availability, dtype=np.float32),
        "mc": np.asarray(st["mc_base"], dtype=np.float32),
    }
    p.write_bytes(pickle.dumps(out))
    return out


ARMS = {
    # carrier A through the EXISTING fields (no new code): the statistical WEFOR
    # cap at 0 on the CAMPD-covered gas classes
    "A": {
        "wefor_residual": 0.0,
        "wefor_residual_groups": frozenset(
            {"CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"}
        ),
    },
    # carrier B as built: ScenarioConfig.spp_gas_crow_residual_outage
    "B": {"spp_gas_crow_residual_outage": True},
}


def rebuild_armed(y: int, cache: Path, arm: str) -> dict:
    """The keeper's rebuild with one BUILT arm set (rated basis): the census of the code path."""
    p = cache / f"spp105_{y}_arm{arm}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from market_sim.config.scenarios import ScenarioConfig

    orig = ScenarioConfig.__post_init__

    def _armed(self):
        for k, v in ARMS[arm].items():
            object.__setattr__(self, k, v)
        orig(self)

    ScenarioConfig.__post_init__ = _armed
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    finally:
        ScenarioConfig.__post_init__ = orig
    for k, v in ARMS[arm].items():
        assert getattr(st["config"], k) == v, (k, getattr(st["config"], k))
    fa = st["fleet_arrays"]
    out = {
        "pmax": np.asarray(fa.pmax, dtype=np.float32),
        "availability": np.asarray(fa.availability, dtype=np.float32),
    }
    p.write_bytes(pickle.dumps(out))
    return out


def edge_mask(a: np.ndarray) -> np.ndarray:
    """True on leading / trailing all-zero runs of >= 30 days (COD / retirement)."""
    m = np.zeros(a.size, bool)
    nz = np.flatnonzero(a > 0)
    if nz.size == 0:
        m[:] = True
        return m
    if nz[0] >= EDGE_H:
        m[: nz[0]] = True
    if a.size - 1 - nz[-1] >= EDGE_H:
        m[nz[-1] + 1 :] = True
    return m


def hour_meta(y: int, lmp: pd.DataFrame) -> pd.DataFrame:
    """Per model hour: month, local hour-of-day, RT price and the SPP-84 segment labels."""
    t = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    rt = lmp[lmp.year == y].set_index("hour").rt.reindex(range(8760)).to_numpy()
    m = pd.DataFrame({"mon": t.month, "hod": t.hour, "rt": rt})
    ok = m.rt.notna() & (m.mon != 2)
    q67, q99 = m.loc[ok, "rt"].quantile([0.67, 0.99])
    m["seg"] = np.where(
        ~m.rt.notna(),
        "na",
        np.where(
            (m.mon != 2) & (m.rt >= q67) & (m.rt < q99),
            "upper",
            np.where(m.rt < q67, "body", "other"),
        ),
    )
    m["top1"] = ok & (m.rt >= q99)
    return m


def class_of(rows: list[dict]) -> np.ndarray:
    """Plant-group class label per row (fuel type when the group is blank)."""
    r = pd.DataFrame(rows)
    return r.plant_group.replace("", np.nan).fillna(r.fuel_type).to_numpy()


def year_decomp(y: int, cache: Path, o: pd.DataFrame, lmp: pd.DataFrame) -> dict:
    """Hourly gas unavailability by class x component vs SPP's published gas outage."""
    fl = {v: rebuild(y, cache, v) for v in VARIANTS}
    rows = fl["full"]["rows"]
    ft = np.array([r["fuel_type"] for r in rows])
    cls = class_of(rows)
    gas = np.isin(ft, GAS)
    pm = fl["full"]["pmax"].astype(float)
    av = {v: pm[:, None] * fl[v]["availability"].astype(float) for v in VARIANTS}
    live = ~np.array([edge_mask(a) for a in av["event"]])
    un = {v: np.where(live, pm[:, None] - av[v], 0.0) for v in VARIANTS}
    comp = {
        "wefor": un["full"] - un["nowefor"],
        "pof": un["nowefor"] - un["event"],
        "event": un["event"],
    }
    meta = hour_meta(y, lmp)
    sp = spp_outage_on_model_clock(o, y)["Natural Gas MW"].to_numpy()
    out: dict = {"year": y, "n_upper": int((meta.seg == "upper").sum())}
    segs = {
        "all": np.ones(8760, bool),
        "body": (meta.seg == "body").to_numpy(),
        "upper": (meta.seg == "upper").to_numpy(),
        "top1": meta.top1.to_numpy(),
    }

    def seg_means(x: np.ndarray) -> dict:
        return {
            k: round(float(np.nanmean(x[m]) / 1e3), 3) if m.any() else None
            for k, m in segs.items()
        }

    out["spp_gas_gw"] = seg_means(sp)
    tot = un["full"][gas].sum(0)
    out["keeper_gas_gw"] = seg_means(tot)
    out["keeper_minus_spp_gw"] = seg_means(tot - sp)
    out["spp_coverage"] = round(float(np.isfinite(sp).mean()), 4)
    ok = np.isfinite(sp)
    out["corr_hourly"] = round(float(np.corrcoef(tot[ok], sp[ok])[0, 1]), 3)
    d = pd.DataFrame({"k": tot, "s": sp, "day": np.arange(8760) // 24}).dropna()
    dd = d.groupby("day").mean()
    out["corr_daily"] = round(float(dd.k.corr(dd.s)), 3)
    # SPP's own intra-day variation vs its day mean (is the published series flat within a day?)
    out["spp_intraday_sd_gw"] = round(float(d.groupby("day").s.std().mean() / 1e3), 3)
    out["spp_monthly_gw"] = [
        round(float(np.nanmean(sp[meta.mon.to_numpy() == m]) / 1e3), 3)
        for m in range(1, 13)
    ]
    out["keeper_monthly_gw"] = [
        round(float(tot[meta.mon.to_numpy() == m].mean() / 1e3), 3)
        for m in range(1, 13)
    ]
    out["upper_share_by_month"] = [
        round(
            float(
                (segs["upper"] & (meta.mon.to_numpy() == m)).sum()
                / max(segs["upper"].sum(), 1)
            ),
            3,
        )
        for m in range(1, 13)
    ]
    out["classes"] = {}
    for c in sorted(set(cls[gas])):
        sel = gas & (cls == c)
        live_mw = np.where(live[sel], pm[sel][:, None], 0.0).sum(0)
        out["classes"][c] = {
            "n_rows": int(sel.sum()),
            "live_pmax_gw": round(float(live_mw.mean() / 1e3), 3),
            **{f"{k}_gw": seg_means(v[sel].sum(0)) for k, v in comp.items()},
            "total_gw": seg_means(un["full"][sel].sum(0)),
            "total_monthly_gw": [
                round(
                    float(
                        un["full"][sel].sum(0)[meta.mon.to_numpy() == m].mean() / 1e3
                    ),
                    3,
                )
                for m in range(1, 13)
            ],
        }
    out["component_gw"] = {k: seg_means(v[gas].sum(0)) for k, v in comp.items()}
    return out


def reclear(
    y: int, cache: Path, o: pd.DataFrame, lmp: pd.DataFrame, carriers: dict
) -> dict:
    """SPP-84 Leg C re-clear (gas only) for each candidate carrier; deltas vs the keeper stack.

    ``carriers`` maps a name to a callable ``(ctx) -> avail`` returning the candidate's (rows x
    8760) available-MW array; ``ctx`` holds the keeper's rated availability, the decomposition
    components and SPP's published gas series.
    """
    base = rebuild_rated(y, cache)
    pm = base["pmax"].astype(float)
    av0 = pm[:, None] * base["availability"].astype(float)
    mc = base["mc"].astype(float)
    fl = {v: rebuild(y, cache, v) for v in VARIANTS}
    rows = fl["full"]["rows"]
    ft = np.array([r["fuel_type"] for r in rows])
    gas = np.isin(ft, GAS)
    ctx = {
        "cache": cache,
        "y": y,
        "pm": pm,
        "av0": av0,
        "gas": gas,
        "cls": class_of(rows),
        "un": {
            v: pm[:, None] * (1 - fl[v]["availability"].astype(float)) for v in VARIANTS
        },
        "live": ~np.array(
            [edge_mask(a) for a in pm[:, None] * fl["event"]["availability"]]
        ),
        "spp": spp_outage_on_model_clock(o, y)["Natural Gas MW"].to_numpy(),
    }
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{y}.parquet")
    ch = ch[(ch["pass"] == "P1") & ~ch.klass.str.upper().str.startswith(VER)]
    q = ch.groupby("hour").mw.sum().reindex(range(8760)).to_numpy()
    s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    p1 = (
        ((s.price * s.demand).groupby(s.hour).sum() / s.groupby("hour").demand.sum())
        .reindex(range(8760))
        .to_numpy()
    )
    meta = hour_meta(y, lmp)
    cand = {k: f(ctx) for k, f in carriers.items()}
    res: dict = {"year": y}
    pf = np.full(8760, np.nan)
    pc = {k: np.full(8760, np.nan) for k in cand}
    short = {k: 0 for k in ("full", *cand)}
    for t in range(8760):
        if not np.isfinite(q[t]):
            continue
        pf[t] = merit(mc[:, t], av0[:, t], q[t])
        short["full"] += int(not np.isfinite(pf[t]))
        for k, a in cand.items():
            pc[k][t] = merit(mc[:, t], a[:, t], q[t])
            short[k] += int(not np.isfinite(pc[k][t]))
    segs = {
        "all": meta.rt.notna().to_numpy(),
        "body": (meta.seg == "body").to_numpy(),
        "upper": (meta.seg == "upper").to_numpy(),
    }
    for k, a in cand.items():
        dgas = (av0[gas] - a[gas]).sum(0)  # added gas unavailability, MW
        rk = {"short_hours": short[k]}
        for sn, m in segs.items():
            ok = m & np.isfinite(pf) & np.isfinite(pc[k])
            rk[sn] = {
                "n": int(ok.sum()),
                "d_price": round(float((pc[k][ok] - pf[ok]).mean()), 3),
                "d_gas_unavail_gw": round(float(dgas[m].mean() / 1e3), 3),
            }
        res[k] = rk
    res["short_hours_keeper_stack"] = short["full"]
    res["diag"] = {
        k: {kk: round(vv, 4) for kk, vv in v.items()}
        for k, v in ctx.get("diag", {}).items()
    }
    ok = segs["all"] & np.isfinite(pf)
    res["p_full_minus_p1"] = round(float((pf[ok] - p1[ok]).mean()), 3)
    res["rt_mean"] = round(float(meta.rt[ok].mean()), 3)
    res["p1_mean"] = round(float(np.nanmean(p1[ok])), 3)
    return res


def main() -> None:
    """Run the decomposition (and, with ``--reclear``, the re-clear legs); write JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--outage", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    ap.add_argument("--reclear", action="store_true")
    a = ap.parse_args()
    a.cache.mkdir(parents=True, exist_ok=True)
    o = load_outage_zips(a.outage)
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    res: dict = {
        "lane": "SPP-105",
        "design": DESIGN,
        "bundle": str(BUNDLE.relative_to(REPO_ROOT)),
    }
    prev = json.loads(a.out.read_text()) if a.out.exists() else {}
    res["decomp"] = prev.get("decomp", {})
    for y in a.years:
        if str(y) not in res["decomp"]:
            res["decomp"][str(y)] = year_decomp(y, a.cache, o, lmp)
            print(y, "decomp done", flush=True)
    if a.reclear:
        from scripts.probes._spp105_carriers import CARRIERS

        res["reclear"] = {
            str(y): reclear(y, a.cache, o, lmp, CARRIERS) for y in a.years
        }
    a.out.write_text(json.dumps(res, indent=1, default=float))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
