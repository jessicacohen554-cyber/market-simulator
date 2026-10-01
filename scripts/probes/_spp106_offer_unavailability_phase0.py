"""SPP-106 (zero LP): the keeper's upper-tercile fossil headroom against the SPP MMU's offer-side
unavailability classes, and SPP-84 re-clear predictions for each class as a candidate carrier.

Record: ``docs/handoffs/DESIGN-spp-106-offer-side-unavailability-2026-10-01.md``.

Source: SPP MMU, "Unavailable Generation Capacity in SPP Markets: Causes and Impacts" (published
2025-12-19), https://spp.org/documents/75563/unavailable%20generation%20capacity%20in%20spp%20markets%20causes%20and%20impacts.pdf
Only the figures the report states as numbers (Fig 12 table, Fig 11 table, prose) are exact; the
annual MW of Figs 3, 4, 16 and 17 are DIGITIZED here from the page images (+/- ~100 MW). Coverage is
2020-2024 only; the report gives no hourly, unit or class (CC / CT / ST) split, and only the
reliability-status class is split by fuel (Fig 3).

Legs:

* ``headroom`` -- per year, the keeper's available fossil MW (``fleet_only`` rebuild, every keeper
  component) minus its own P1 generation, by family (gas CC / CT / ST, coal), over the body
  (RT < p67), upper tercile (p67 <= RT < p99, Feb excluded; SPP-84's cut) and top 1 %, with the
  upper-tercile month and hour-of-day mix.
* ``reclear`` -- SPP-84's gas+coal merit re-clear of the keeper's own stack at its own non-VER P1
  generation, under each carrier below (INSTRUMENTS, never configs). Only deltas are used.

Carriers (``f_y`` = MMU class MW / MMU rated conventional MW for year y; 2019 takes 2020's value
and 2025 takes 2024's -- the hold rule is the only choice and is fixed here, before any number):

* ``E``  -- rule-19 REPLACEMENT of the keeper's flat GADS performance derate and flat summer class
  derate on fossil rows by the MMU's "capacity above emergency maximum" share (both bands), flat,
  plus the MMU's unreported ambient derate MW-days spread over Jun-Sep pro rata to pmax.
* ``EX`` -- ``E`` plus the MMU's "between economic and emergency maximum" share, flat on every
  fossil row (the MW SPP reaches only in an emergency).
* ``R_dear`` / ``R_pro`` / ``R_cheap`` -- the keeper plus the MMU's GAS reliability-commitment-status
  MW (Fig 3) removed as WHOLE gas rows: dearest first, pro rata to pmax, cheapest first. The MMU
  does not say WHICH units; the three are the bounds of that unidentified allocation.
* ``EXR_pro`` -- ``EX`` and ``R_pro`` together.

Solves nothing. Usage:
``uv run python scripts/probes/_spp106_offer_unavailability_phase0.py --cache <dir> --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp84_published_outage_rebasis import merit  # noqa: E402
from scripts.probes._spp105_gas_outage_hourly_phase0 import (  # noqa: E402
    BUNDLE,
    VER,
    class_of,
    edge_mask,
    hour_meta,
    rebuild,
    rebuild_rated,
)

DESIGN = "docs/handoffs/DESIGN-spp-106-offer-side-unavailability-2026-10-01.md"
YEARS = tuple(range(2019, 2026))
GAS = ("gas_cc", "gas_ct", "gas_st")
FOSSIL = (*GAS, "coal", "oil")

# MMU Dec 2025, MW. DIGITIZED from Figs 16 / 17 / 3 unless noted (+/- ~100 MW).
MMU = {
    # Fig 16 dashed line: rated conventional capacity
    "rated_conv": {2020: 67300, 2021: 65900, 2022: 66000, 2023: 63400, 2024: 64800},
    # Fig 17: between economic and emergency maximum
    "eco_emer": {2020: 1750, 2021: 1650, 2022: 1800, 2023: 1800, 2024: 1750},
    # Fig 17: above emergency maximum, both bands (<10 MW + >10 MW); Fig 4 line agrees
    "above_emer": {2020: 2500, 2021: 1500, 2022: 1700, 2023: 1950, 2024: 1700},
    # Fig 17: reliability commitment status, all fuels
    "reliability_all": {2020: 1650, 2021: 2550, 2022: 2700, 2023: 2650, 2024: 2900},
    # Fig 3 grey squares: reliability status, natural gas only
    "reliability_gas": {2020: 1050, 2021: 1220, 2022: 1240, 2023: 1300, 2024: 1920},
    # Fig 12 table (EXACT): ambient derate, average MW on derate days x number of days
    "ambient_mw_on_days": {2020: 338, 2021: 185, 2022: 367, 2023: 422, 2024: 340},
    "ambient_days": {2020: 115, 2021: 122, 2022: 134, 2023: 116, 2024: 112},
}
JUN_SEP_DAYS = 122


def mmu(key: str, y: int) -> float:
    """MMU value for year ``y`` under the fixed hold rule (2019 <- 2020, 2025 <- 2024)."""
    d = MMU[key]
    return float(d[min(max(y, min(d)), max(d))])


def stack(y: int, cache: Path) -> dict:
    """Keeper stack (rated basis) and the no-flat-derate variant, with row metadata."""
    base = rebuild_rated(y, cache)
    nd = rebuild(
        y, cache, "full"
    )  # SPP-105 'full' = keeper less flat perf + summer derate
    rows = nd["rows"]
    ft = np.array([r["fuel_type"] for r in rows])
    pm = base["pmax"].astype(float)
    av0 = pm[:, None] * base["availability"].astype(float)
    avn = pm[:, None] * nd["availability"].astype(float)
    return {
        "rows": rows,
        "ft": ft,
        "cls": class_of(rows),
        "pm": pm,
        "av0": av0,
        "avn": avn,
        "mc": base["mc"].astype(float),
        "live": ~np.array([edge_mask(a) for a in avn]),
    }


def family(ft: np.ndarray, cls: np.ndarray) -> np.ndarray:
    """gas_cc / gas_ct / gas_st / coal / oil / other per row."""
    out = np.where(np.isin(ft, FOSSIL), ft, "other").astype(object)
    out[np.char.startswith(cls.astype(str), "COAL")] = "coal"
    return out


def p1_series(y: int) -> tuple[np.ndarray, pd.DataFrame, np.ndarray]:
    """Keeper non-VER P1 generation per hour, P1 class frame, load-weighted P1 price."""
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{y}.parquet")
    ch = ch[ch["pass"] == "P1"]
    nv = ch[~ch.klass.astype(str).str.upper().str.startswith(VER)]
    q = nv.groupby("hour").mw.sum().reindex(range(8760)).to_numpy()
    s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    p1 = (
        ((s.price * s.demand).groupby(s.hour).sum() / s.groupby("hour").demand.sum())
        .reindex(range(8760))
        .to_numpy()
    )
    return q, ch, p1


CLASS_FAMILY = {
    "CC_REGULAR": "gas_cc",
    "CC_CHP": "gas_cc",
    "CT_PEAKER": "gas_ct",
    "CT_CHP": "gas_ct",
    "ST_GAS": "gas_st",
    "ST_CHP": "gas_st",
}


def headroom(y: int, st: dict, ch: pd.DataFrame, meta: pd.DataFrame) -> dict:
    """Keeper available minus P1 generation, by fossil family and price segment (GW)."""
    fam = family(st["ft"], st["cls"])
    segs = {
        "body": (meta.seg == "body").to_numpy(),
        "upper": (meta.seg == "upper").to_numpy(),
        "top1": meta.top1.to_numpy(),
    }
    ch = ch.assign(
        fam=ch.klass.astype(str).map(
            lambda k: CLASS_FAMILY.get(k, "coal" if k.startswith("COAL") else k)
        )
    )
    out: dict = {}
    for f in ("gas_cc", "gas_ct", "gas_st", "coal"):
        av = st["av0"][fam == f].sum(0)
        gen = (
            ch[ch.fam == f].groupby("hour").mw.sum().reindex(range(8760)).fillna(0.0)
        ).to_numpy()
        rated = np.where(st["live"][fam == f], st["pm"][fam == f, None], 0.0).sum(0)
        out[f] = {
            k: {
                "rated": round(float(rated[m].mean() / 1e3), 3),
                "avail": round(float(av[m].mean() / 1e3), 3),
                "gen": round(float(gen[m].mean() / 1e3), 3),
                "headroom": round(float((av - gen)[m].mean() / 1e3), 3),
            }
            for k, m in segs.items()
        }
    up = segs["upper"]
    out["upper_month_share"] = [
        round(float((up & (meta.mon.to_numpy() == m)).sum() / up.sum()), 3)
        for m in range(1, 13)
    ]
    out["upper_hod_share"] = [
        round(float((up & (meta.hod.to_numpy() == h)).sum() / up.sum()), 3)
        for h in range(24)
    ]
    return out


def carriers(y: int, st: dict) -> dict:
    """Each carrier's (rows x 8760) available MW. Deterministic; no tunable."""
    fam = family(st["ft"], st["cls"])
    fos = fam != "other"
    gas = np.isin(fam, ("gas_cc", "gas_ct", "gas_st"))
    pm, live = st["pm"], st["live"]
    rc = mmu("rated_conv", y)
    a_above = mmu("above_emer", y) / rc
    a_eco = mmu("eco_emer", y) / rc
    # ambient: MW-days on Jun-Sep, pro rata to live fossil pmax
    amb_mw = mmu("ambient_mw_on_days", y) * mmu("ambient_days", y) / JUN_SEP_DAYS
    t = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    summer = np.isin(t.month, (6, 7, 8, 9))
    live_fos_mw = np.where(live & fos[:, None], pm[:, None], 0.0)
    amb = (
        np.where(summer[None, :], live_fos_mw, 0.0)
        * amb_mw
        / np.maximum(live_fos_mw.sum(0), 1.0)[None, :]
    )

    def cut(av: np.ndarray, share: float) -> np.ndarray:
        return np.where(
            live & fos[:, None], np.maximum(0.0, av - share * pm[:, None]), av
        )

    e = st["av0"].copy()
    e[fos] = st["avn"][fos]  # remove the flat perf + summer derate on fossil rows
    e = np.maximum(0.0, cut(e, a_above) - amb)
    ex = cut(e, a_eco)

    def reliab(av: np.ndarray, order: str) -> np.ndarray:
        target = mmu("reliability_gas", y)
        gi = np.flatnonzero(gas & (pm > 0))
        a = av.copy()
        if order == "pro":
            share = target / pm[gi].sum()
            a[gi] = a[gi] * (1.0 - share)
            return a
        mmc = np.nanmean(np.where(live[gi], st["mc"][gi], np.nan), 1)
        idx = gi[np.argsort(mmc if order == "cheap" else -mmc, kind="stable")]
        took = 0.0
        for g in idx:
            if took >= target:
                break
            a[g] = 0.0
            took += pm[g]
        return a

    return {
        "E": e,
        "EX": ex,
        "R_dear": reliab(st["av0"], "dear"),
        "R_pro": reliab(st["av0"], "pro"),
        "R_cheap": reliab(st["av0"], "cheap"),
        "EXR_pro": reliab(ex, "pro"),
    }


def reclear(
    y: int, st: dict, meta: pd.DataFrame, q: np.ndarray, p1: np.ndarray
) -> dict:
    """SPP-84 re-clear: keeper stack vs each carrier; price deltas, margins, short hours."""
    fam = family(st["ft"], st["cls"])
    fos = fam != "other"
    cand = carriers(y, st)
    mc, av0 = st["mc"], st["av0"]
    pf = np.full(8760, np.nan)
    pc = {k: np.full(8760, np.nan) for k in cand}
    for h in range(8760):
        if not np.isfinite(q[h]):
            continue
        pf[h] = merit(mc[:, h], av0[:, h], q[h])
        for k, a in cand.items():
            pc[k][h] = merit(mc[:, h], a[:, h], q[h])
    segs = {
        "all": meta.rt.notna().to_numpy(),
        "body": (meta.seg == "body").to_numpy(),
        "upper": (meta.seg == "upper").to_numpy(),
        "top1": meta.top1.to_numpy(),
    }
    res: dict = {
        "year": y,
        "short_hours_keeper": int(np.isnan(pf[np.isfinite(q)]).sum()),
    }
    margin0 = av0.sum(0) - q
    res["keeper_min_margin_gw"] = round(float(np.nanmin(margin0) / 1e3), 3)
    for k, a in cand.items():
        d_fos = (av0[fos] - a[fos]).sum(0)
        margin = a.sum(0) - q
        r = {
            "short_hours": int(np.isnan(pc[k][np.isfinite(q)]).sum()),
            "min_margin_gw": round(float(np.nanmin(margin) / 1e3), 3),
            "hours_margin_lt_1gw": int((margin < 1e3).sum()),
        }
        for sn, m in segs.items():
            ok = m & np.isfinite(pf) & np.isfinite(pc[k])
            r[sn] = {
                "n": int(ok.sum()),
                "d_price": round(float((pc[k][ok] - pf[ok]).mean()), 3)
                if ok.any()
                else None,
                "d_fossil_avail_gw": round(float(d_fos[m].mean() / 1e3), 3),
            }
        res[k] = r
    ok = segs["all"] & np.isfinite(pf)
    res["rt_mean"] = round(float(meta.rt[ok].mean()), 3)
    res["p1_mean"] = round(float(np.nanmean(p1[ok])), 3)
    res["p_reclear_minus_p1"] = round(float((pf[ok] - p1[ok]).mean()), 3)
    up = segs["upper"] & np.isfinite(pf)
    res["upper_rt_mean"] = round(float(meta.rt[up].mean()), 3)
    res["upper_p1_mean"] = round(float(np.nanmean(p1[up])), 3)
    return res


def main() -> None:
    """Run both legs for every year; write JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    a = ap.parse_args()
    a.cache.mkdir(parents=True, exist_ok=True)
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    res = json.loads(a.out.read_text()) if a.out.exists() else {}
    res.update(
        {
            "lane": "SPP-106",
            "design": DESIGN,
            "bundle": str(BUNDLE.relative_to(REPO_ROOT)),
            "mmu_digitized": {
                k: {str(y): v for y, v in d.items()} for k, d in MMU.items()
            },
        }
    )
    res.setdefault("headroom", {})
    res.setdefault("reclear", {})
    for y in a.years:
        st = stack(y, a.cache)
        meta = hour_meta(y, lmp)
        q, ch, p1 = p1_series(y)
        res["headroom"][str(y)] = headroom(y, st, ch, meta)
        res["reclear"][str(y)] = reclear(y, st, meta, q, p1)
        a.out.write_text(json.dumps(res, indent=1, default=float))
        print(y, "done", flush=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
