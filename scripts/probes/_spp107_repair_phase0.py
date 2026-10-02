"""SPP-107 (zero LP): the repaired MMU offer-side carrier against carrier EX as built (SPP-106).

Record: ``docs/records/spp/DESIGN-spp-107-mmu-carrier-repair-2026-10-02.md``.

Two construction repairs to ``ScenarioConfig.spp_mmu_offer_unavailability`` (SPP-106 RESULT §7):

1. **Multiplicative bands.** EX subtracts ``share x RATED pmax`` from every fossil row's availability, even on
   a unit already partially outaged. The MMU measures against the derated amount (report §3.1.2), so the band
   is ``share x AVAILABLE MW``: ``a -> a x (1 - share)``.
2. **Economic -> emergency band in scarcity only.** EX removes that band outright. The MMU: those MW "are only
   accessible when SPP anticipates or identifies a reliability issue". Repaired, the band (``eco share x the
   unit's post-outage available MW``) is pooled per zone and offered at ``voll - storage epsilon``: it clears
   only where the zone would otherwise shed load.

Arms (all instruments; never configs):

* ``K``   -- the keeper's own rebuild (rated basis);
* ``EX``  -- carrier EX as built (``spp_mmu_offer_unavailability = true``, the code path, not a re-derivation);
* ``M``   -- repair (1) only: every band multiplicative, the eco->emer band still removed;
* ``MS``  -- repairs (1) + (2): ``M`` with the eco->emer slice returned as a zonal pool at the scarcity price.

Legs per year:

* ``reclear`` -- SPP-84's single-zone merit re-clear at the keeper's own non-VER P1 generation (Δprice vs ``K``
  over all hours and the upper tercile; short hours; min fossil margin). The pool, priced at ``voll - eps``,
  enters only after every economic MW, so it moves price only in hours that would otherwise be short.
* ``south`` -- SPP-South dispatchable capacity, arm minus keeper, in the keeper's own South-slack hours and in
  the EX solve's short events (2022-05-19, 2024-10-21 13-17h, 2025-12-21 10-13h; SPP-106 RESULT §7), plus the
  year minimum over the keeper's 200 tightest South hours (largest South price).

Solves nothing. ``uv run python scripts/probes/_spp107_repair_phase0.py --cache <dir> --out <json>``
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
from scripts.probes._spp84_published_outage_rebasis import merit  # noqa: E402
from scripts.probes._spp105_gas_outage_hourly_phase0 import (  # noqa: E402
    BUNDLE,
    class_of,
    edge_mask,
    hour_meta,
    rebuild_rated,
)
from scripts.probes._spp106_offer_unavailability_phase0 import (  # noqa: E402
    family,
    p1_series,
)

DESIGN = "docs/records/spp/DESIGN-spp-107-mmu-carrier-repair-2026-10-02.md"
YEARS = tuple(range(2019, 2026))
SOUTH = "SPP-South"
# EX solve's short events (SPP-106 RESULT §1 / §7): (year, month, day, first hour, last hour) local model hours
EX_EVENTS = {
    2022: (5, 19, 0, 23),
    2024: (10, 21, 13, 17),
    2025: (12, 21, 10, 13),
}
EX_EVENT_UNSERVED_MWH = {2022: 420.0, 2024: 3737.0, 2025: 1568.0}


def rebuild_ex(y: int, cache: Path) -> dict:
    """The armed rebuild (EX as built), capturing availability just before the MMU bands run."""
    p = cache / f"spp107_{y}_ex.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import arrays as _arr
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    orig_post, orig_bands = ScenarioConfig.__post_init__, _arr._apply_spp_mmu_bands
    seen: dict = {}

    def _armed(self):
        object.__setattr__(self, "spp_mmu_offer_unavailability", True)
        orig_post(self)

    def _capture(generators, availability, pmax, hours, year):
        seen["pre"] = np.array(availability[:, :hours], dtype=np.float32)
        orig_bands(generators, availability, pmax, hours, year)
        seen["post"] = np.array(availability[:, :hours], dtype=np.float32)

    ScenarioConfig.__post_init__ = _armed
    _arr._apply_spp_mmu_bands = _capture
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    finally:
        ScenarioConfig.__post_init__ = orig_post
        _arr._apply_spp_mmu_bands = orig_bands
    assert st["config"].spp_mmu_offer_unavailability
    fa = st["fleet_arrays"]
    keys = ("unit_id", "fuel_type", "plant_group", "zone", "plant_code", "online_year")
    out = {
        "rows": [{k: getattr(g, k, None) for k in keys} for g in st["fleet"]],
        "pmax": np.asarray(fa.pmax, dtype=np.float32),
        "pre": seen["pre"],
        "post": seen["post"],
        "ex": np.asarray(fa.availability, dtype=np.float32),
        "voll": float(st["config"].voll),
    }
    p.write_bytes(pickle.dumps(out))
    return out


def arms(y: int, cache: Path) -> dict:
    """Per-row hourly available MW for K / EX / M, the MS pool per row, and row metadata."""
    from market_sim.data.fleet.arrays import _hour_to_month_index
    from market_sim.data.spp_mmu_unavailability import mmu_shares

    k = rebuild_rated(y, cache)
    x = rebuild_ex(y, cache)
    rows = x["rows"]
    ft = np.array([r["fuel_type"] for r in rows])
    cls = class_of(rows)
    fam = family(ft, cls)
    fos = np.isin(
        ft, ("gas_cc", "gas_ct", "gas_st", "coal", "oil")
    ) | np.char.startswith(cls.astype(str), "COAL")
    pm = x["pmax"].astype(float)
    assert np.allclose(pm, k["pmax"].astype(float)), (
        "row order differs between rebuilds"
    )
    sh = mmu_shares(y)
    amb = sh.ambient_mw / float(pm[fos].sum())
    summer = np.isin(_hour_to_month_index(8760), (5, 6, 7, 8))
    pre = x["pre"].astype(float)
    # Steps after the bands (the COD ramp masks unit-months) carried as a per-row-hour factor.
    post, fin = x["post"].astype(float), x["ex"].astype(float)
    down = np.where(
        post > 1e-9, fin / np.maximum(post, 1e-9), (k["availability"] > 0).astype(float)
    )
    # EX re-derived from the captured pre-band availability must equal the built path.
    cut = np.full(8760, sh.above_emer + sh.eco_to_emer)
    cut[summer] += amb
    ex_re = np.where(fos[:, None], np.maximum(0.0, pre - cut[None, :]), pre)
    built_err = float(np.abs(ex_re - post).max())
    cut_ne = np.full(8760, sh.above_emer)
    cut_ne[summer] += amb
    m_avail = down * np.where(
        fos[:, None], pre * (1.0 - cut_ne[None, :] - sh.eco_to_emer), pre
    )
    pool = down * np.where(fos[:, None], pre * sh.eco_to_emer, 0.0)
    return {
        "rows": rows,
        "fam": fam,
        "fos": fos,
        "zone": np.array([r["zone"] for r in rows]),
        "pm": pm,
        "mc": k["mc"].astype(float),
        "K": pm[:, None] * k["availability"].astype(float),
        "EX": pm[:, None] * x["ex"].astype(float),
        "M": pm[:, None] * m_avail,
        "pool": pm[:, None] * pool,
        "voll": x["voll"],
        "built_err": built_err,
        "shares": sh,
        "live": ~np.array([edge_mask(a) for a in k["availability"]]),
    }


def reclear(y: int, A: dict, meta: pd.DataFrame, q: np.ndarray) -> dict:
    """Single-zone merit re-clear at keeper non-VER P1 generation: K vs EX / M / MS."""
    mc = A["mc"]
    pool_tot = A["pool"].sum(0)
    stacks = {"K": A["K"], "EX": A["EX"], "M": A["M"]}
    price = {kk: np.full(8760, np.nan) for kk in ("K", "EX", "M", "MS")}
    for h in range(8760):
        if not np.isfinite(q[h]):
            continue
        for kk, a in stacks.items():
            price[kk][h] = merit(mc[:, h], a[:, h], q[h])
        # MS: M's economic stack, then the pool at voll - eps (only reached when M is short)
        price["MS"][h] = (
            price["M"][h]
            if np.isfinite(price["M"][h])
            else (A["voll"] if A["M"][:, h].sum() + pool_tot[h] >= q[h] else np.nan)
        )
    segs = {
        "all": meta.rt.notna().to_numpy(),
        "upper": (meta.seg == "upper").to_numpy(),
    }
    fos = A["fos"]
    out: dict = {"short_hours": {}, "min_margin_gw": {}}
    for kk in ("K", "EX", "M", "MS"):
        a = A["M"] if kk == "MS" else A[kk]
        margin = a.sum(0) + (pool_tot if kk == "MS" else 0.0) - q
        out["short_hours"][kk] = int(np.isnan(price[kk][np.isfinite(q)]).sum())
        out["min_margin_gw"][kk] = round(float(np.nanmin(margin) / 1e3), 3)
    for kk in ("EX", "M", "MS"):
        for sn, m in segs.items():
            # deltas over hours where both stacks clear economically (scarcity hours excluded, as SPP-106)
            ok = (
                m
                & np.isfinite(price["K"])
                & np.isfinite(price[kk])
                & (price[kk] < A["voll"])
            )
            ok &= np.isfinite(price["EX"]) & np.isfinite(price["M"])
            out[f"d_{sn}_{kk}"] = round(
                float((price[kk][ok] - price["K"][ok]).mean()), 3
            )
        a = A["M"] if kk == "MS" else A[kk]
        out[f"d_fossil_upper_gw_{kk}"] = round(
            float(((a[fos] - A["K"][fos]).sum(0))[segs["upper"]].mean() / 1e3), 3
        )
    return out


def south(y: int, A: dict) -> dict:
    """SPP-South dispatchable capacity, arm minus keeper, in the scarcity hours that matter."""
    s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    s = (
        s[(s["pass"] == "P1") & (s.zone == SOUTH)]
        .set_index("hour")
        .reindex(range(8760))
    )
    slack = s.slack.fillna(0.0).to_numpy()
    price = s.price.to_numpy()
    zs = A["zone"] == SOUTH
    cap = {
        "K": A["K"][zs].sum(0),
        "EX": A["EX"][zs].sum(0),
        "M": A["M"][zs].sum(0),
        "MS": A["M"][zs].sum(0) + A["pool"][zs].sum(0),
    }
    t = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    out: dict = {
        "keeper_slack_hours": int((slack > 1e-6).sum()),
        "keeper_slack_mwh": round(float(slack.sum()), 1),
    }

    def block(m: np.ndarray, tag: str) -> None:
        if not m.any():
            return
        out[tag] = {
            "n": int(m.sum()),
            "keeper_south_avail_mw": round(float(cap["K"][m].mean()), 0),
            **{
                f"d_{kk}_mw_mean": round(float((cap[kk] - cap["K"])[m].mean()), 0)
                for kk in ("EX", "M", "MS")
            },
            **{
                f"d_{kk}_mw_min": round(float((cap[kk] - cap["K"])[m].min()), 0)
                for kk in ("EX", "M", "MS")
            },
            "MS_minus_EX_mw_min": round(float((cap["MS"] - cap["EX"])[m].min()), 0),
            "M_minus_EX_mw_min": round(float((cap["M"] - cap["EX"])[m].min()), 0),
            "pool_mw_mean": round(float(A["pool"][zs].sum(0)[m].mean()), 0),
        }

    block(slack > 1e-6, "keeper_slack")
    if y in EX_EVENTS:
        mo, d, h0, h1 = EX_EVENTS[y]
        block(
            (t.month == mo) & (t.day == d) & (t.hour >= h0) & (t.hour <= h1), "ex_event"
        )
        out["ex_event_unserved_mwh"] = EX_EVENT_UNSERVED_MWH[y]
    tight = np.argsort(-np.nan_to_num(price, nan=-1e9))[:200]
    m = np.zeros(8760, bool)
    m[tight] = True
    block(m, "tight200")
    return out


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
            "lane": "SPP-107",
            "design": DESIGN,
            "bundle": str(BUNDLE.relative_to(REPO_ROOT)),
        }
    )
    res.setdefault("years", {})
    for y in a.years:
        A = arms(y, a.cache)
        meta = hour_meta(y, lmp)
        q, _ch, _p1 = p1_series(y)
        sh = A["shares"]
        res["years"][str(y)] = {
            "mmu_year": sh.year_used,
            "shares": {
                "above_emer": sh.above_emer,
                "eco_to_emer": sh.eco_to_emer,
                "ambient_mw": sh.ambient_mw,
            },
            "ex_built_vs_rederived_max_abs": A["built_err"],
            "reclear": reclear(y, A, meta, q),
            "south": south(y, A),
        }
        a.out.write_text(json.dumps(res, indent=1, default=float))
        print(y, "done", flush=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
