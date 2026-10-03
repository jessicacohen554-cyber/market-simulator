"""PJM-NEXT-30 (ZERO LP): COAL_BIT in-money loading gap, decomposed per plant.

Readings fixed ex ante in
``docs/records/pjm/FINDING-pjm-next-30-coalbit-inmoney-loading-2026-10-03.md`` §1.
Hours ``H_y`` are the NEXT-29 S2 hours (real implied HR >= ``HI_HR``); plants are the
NEXT-29 S2 set (keeper COAL_BIT plants with a bench CAMPD record). Per plant-hour the
gap ``D = M - A`` (model P1 MW minus bench CAMPD net MW) splits into four ordered pieces:

1. basis   = M - min(M, Y)           (Y = annual p99 of A)
2. derate  = min(M, Y) - min(M, W)   (W = max of A over the 168-h block)
3. offline = min(M, W) - A, A == 0
4. loading = min(M, W) - A, A > 0

plus the same pieces with ``K`` (available cap_mw) in place of ``M`` (dispatch-independent
twin), the unit-dark share of pieces 2 + 3 (CAMPD unit-level ``opTime == 0`` on any unit of
the plant), per-plant concentration, and the IMM reserve bound (2019-21).

Writes ``results/phase0/pjm/_pjmnext30_coalbit_loading.json``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
sys.path.insert(0, str(REPO))
from _pjmnext28_sunk_noload import _parquet, gas_daily  # noqa: E402
from _pjmnext29_coalbit_bins import GROUP, HI_HR, T, campd_by_plant  # noqa: E402
from _pjmnext29_lowhour_setters import real_low_hours  # noqa: E402

OUT = REPO / "results/phase0/pjm/_pjmnext30_coalbit_loading.json"
UNIT_DIR = REPO / "data/raw/campd-unit-level"
RESERVE_CSV = REPO / "results/phase0/pjm/_pjmco_0c_som_sec10_reserve_by_unit_type.csv"
YEARS = tuple(range(2019, 2026))
FAIL = (2019, 2020, 2021, 2022, 2025)
PASS = (2023, 2024)
POOL = (2019, 2020, 2021)
#: Revealed-capability block (hours) and annual quantile, FINDING §1.
BLOCK = 168
Q_YEAR = 0.99
PIECES = ("basis", "derate", "offline", "loading")


def unit_dark(y: int, plants: list[int]) -> pd.DataFrame:
    """Hour-of-year x plant flag: any CAMPD unit of the plant reports ``opTime == 0``."""
    keep = set(plants)
    fr = []
    for f in sorted(UNIT_DIR.glob(f"*_{y}.parquet")):
        t = ds.dataset(str(f), format="parquet").to_table(
            columns=["facilityId", "unitId", "date", "hour", "opTime"]
        )
        x = t.to_pandas()
        x["facilityId"] = pd.to_numeric(x["facilityId"], errors="coerce")
        fr.append(x[x["facilityId"].isin(keep)])
    d = pd.concat(fr, ignore_index=True)
    d["hoy"] = (
        pd.to_datetime(d["date"]) - pd.Timestamp(f"{y}-01-01")
    ).dt.days * 24 + d["hour"].astype(int)
    d = d[(d["hoy"] >= 0) & (d["hoy"] < T)]
    d["dark"] = (d["opTime"].fillna(0.0) <= 0.0).astype(np.int8)
    return d.groupby(["facilityId", "hoy"])["dark"].max().unstack(0)


def pieces(
    m: np.ndarray, a: np.ndarray, yq: float, w: np.ndarray
) -> dict[str, np.ndarray]:
    """The four ordered pieces of ``m - a`` (arrays over the plant's H_y hours)."""
    my = np.minimum(m, yq)
    mw = np.minimum(m, w)
    rest = mw - a
    on = a > 0
    return {
        "basis": m - my,
        "derate": my - mw,
        "offline": np.where(on, 0.0, rest),
        "loading": np.where(on, rest, 0.0),
    }


def reserve_bound(y: int) -> float | None:
    """IMM coal-held reserve MW (Tier-1 + Tier-2 + regulation), FINDING §1."""
    r = pd.read_csv(RESERVE_CSV)
    r = r[r["year"] == y]

    def v(metric: str, cat: str) -> float | None:
        s = r[(r["metric"] == metric) & (r["category"] == cat)]["value"]
        return float(s.iloc[0]) if len(s) else None

    t1, t2 = v("rto_avg_tier1_mw", "all"), v("rto_avg_tier2_mw", "all")
    s1, s2 = v("tier1_pct_by_mw", "Steam - Coal"), v("tier2_pct_by_mw", "Steam - Coal")
    rc = v("regulation_settled_mw", "Coal")
    if None in (t1, t2, s1, s2, rc):
        return None
    return t1 * s1 / 100 + t2 * s2 / 100 + rc / T


def run_year(y: int, gas: pd.Series) -> dict:
    """Decompose one year."""
    rl = real_low_hours(y, gas).reindex(range(T))
    hr = (rl["p_real"] / rl["gas"]).to_numpy()
    hi = np.where(hr >= HI_HR)[0]
    um = _parquet(
        f"unit_marginal_{y}.parquet",
        columns=["plant_code", "hour", "mw", "cap_mw"],
        filters=[("plant_group", "=", GROUP)],
    )
    um = um.groupby(["plant_code", "hour"], observed=True)[["mw", "cap_mw"]].sum()
    mw = um["mw"].unstack(0).reindex(range(T)).fillna(0.0)
    cap = um["cap_mw"].unstack(0).reindex(range(T)).fillna(0.0)
    cp = campd_by_plant(y)
    plants = sorted(set(cp) & set(mw.columns))
    dark = unit_dark(y, plants).reindex(range(T))

    tot = {f"{b}_{k}": 0.0 for b in ("M", "K") for k in PIECES}
    dark_mwh = 0.0
    rows = []
    for p in plants:
        a_all = cp[p]
        yq = float(np.quantile(a_all, Q_YEAR))
        wblk = (
            pd.Series(a_all).groupby(np.arange(T) // BLOCK).transform("max").to_numpy()
        )
        a, w = a_all[hi], wblk[hi]
        pm = pieces(mw[p].to_numpy()[hi], a, yq, w)
        pk = pieces(cap[p].to_numpy()[hi], a, yq, w)
        if p in dark.columns:
            dk = dark[p].to_numpy()[hi] == 1
            dark_mwh += float((pm["derate"] + pm["offline"])[dk].sum())
            matched = True
        else:
            matched = False
        row = {
            "plant": int(p),
            "gap_mw": float((mw[p].to_numpy()[hi] - a).mean()) if len(hi) else 0.0,
            "cap_mw": float(cap[p].to_numpy()[hi].mean()) if len(hi) else 0.0,
            "unit_matched": matched,
        }
        for k in PIECES:
            tot[f"M_{k}"] += float(pm[k].sum())
            tot[f"K_{k}"] += float(pk[k].sum())
            row[k] = float(pm[k].mean()) if len(hi) else 0.0
        rows.append(row)

    n = max(len(hi), 1)
    k_tot = float(cap[plants].to_numpy()[hi].sum())
    gap = sum(tot[f"M_{k}"] for k in PIECES)
    rows.sort(key=lambda r: -r["gap_mw"])
    top = rows[:10]
    return {
        "year": y,
        "hours": int(len(hi)),
        "plants": len(plants),
        "unmatched_unit_level": [r["plant"] for r in rows if not r["unit_matched"]],
        "model_mw": round(float(mw[plants].to_numpy()[hi].sum()) / n),
        "cap_mw": round(k_tot / n),
        "campd_mw": round(float(sum(cp[p][hi].sum() for p in plants)) / n),
        "gap_mw": round(gap / n),
        "pieces_mw": {k: round(tot[f"M_{k}"] / n) for k in PIECES},
        "pieces_per_cap": {k: round(tot[f"M_{k}"] / k_tot, 4) for k in PIECES},
        "twin_pieces_mw": {k: round(tot[f"K_{k}"] / n) for k in PIECES},
        "twin_per_cap": {k: round(tot[f"K_{k}"] / k_tot, 4) for k in PIECES},
        "unit_dark_share_of_derate_offline": round(
            dark_mwh / max(tot["M_derate"] + tot["M_offline"], 1e-9), 3
        ),
        "top10": [
            {kk: (round(v, 1) if isinstance(v, float) else v) for kk, v in r.items()}
            for r in top
        ],
        "top10_gap_share": round(sum(r["gap_mw"] for r in top) * n / gap, 3)
        if gap
        else None,
        "top10_pieces_mw": {k: round(sum(r[k] for r in top)) for k in PIECES},
        "reserve_bound_mw": (
            round(reserve_bound(y)) if reserve_bound(y) is not None else None
        ),
    }


def readings(res: dict[int, dict]) -> dict:
    """Apply the FINDING §1 decision rules (no thresholds re-chosen here)."""
    pooled = {
        k: sum(res[y]["pieces_mw"][k] * res[y]["hours"] for y in POOL) for k in PIECES
    }
    g = sum(pooled.values())
    share = {k: round(v / g, 3) for k, v in pooled.items()}
    order = sorted(PIECES, key=lambda k: -share[k])
    r1 = order[0] if share[order[0]] >= 0.5 else f"mixed ({order[0]}, {order[1]})"

    def diff(key: str, k: str) -> float:
        f = np.mean([res[y][key][k] for y in FAIL if y in res])
        p = np.mean([res[y][key][k] for y in PASS if y in res])
        return round(float(f - p), 4)

    r2 = {}
    for k in PIECES:
        dm, dk = diff("pieces_per_cap", k), diff("twin_per_cap", k)
        r2[k] = {
            "M_fail_minus_pass": dm,
            "K_fail_minus_pass": dk,
            "verdict": (
                ("level" if abs(dk) >= 0.03 else "binding-only")
                if dm >= 0.03
                else "not discriminating"
            ),
        }
    top_share = np.mean([res[y]["top10_gap_share"] for y in POOL])
    top_p = {k: sum(res[y]["top10_pieces_mw"][k] for y in POOL) for k in PIECES}
    top_lead = max(top_p, key=top_p.get)
    r3 = {
        "top10_gap_share_mean_2019_21": round(float(top_share), 3),
        "top10_lead_piece": top_lead,
        "verdict": "concentrated"
        if top_share >= 0.6 and top_lead == order[0]
        else "not concentrated",
    }
    r4 = {
        y: {
            "reserve_bound_mw": res[y]["reserve_bound_mw"],
            "loading_mw": res[y]["pieces_mw"]["loading"],
            "ratio": round(
                res[y]["reserve_bound_mw"] / res[y]["pieces_mw"]["loading"], 3
            )
            if res[y]["reserve_bound_mw"] and res[y]["pieces_mw"]["loading"] > 0
            else None,
        }
        for y in POOL
    }
    r4_v = (
        "not the operand"
        if all(v["ratio"] is not None and v["ratio"] < 0.25 for v in r4.values())
        else "cannot exclude"
    )
    return {
        "R1": {"pooled_share_2019_21": share, "verdict": r1},
        "R2": r2,
        "R3": r3,
        "R4": {"by_year": r4, "verdict": r4_v},
    }


def main(years: list[int]) -> None:
    """Run every year, apply the readings, write the JSON."""
    import json

    gas = gas_daily()
    res = {}
    for y in years:
        r = run_year(y, gas)
        res[y] = r
        print(
            f"{y}: H={r['hours']} M={r['model_mw']} K={r['cap_mw']} A={r['campd_mw']} "
            f"gap={r['gap_mw']} pieces={r['pieces_mw']} twin={r['twin_pieces_mw']} "
            f"dark={r['unit_dark_share_of_derate_offline']} top10={r['top10_gap_share']} "
            f"resv={r['reserve_bound_mw']} unmatched={len(r['unmatched_unit_level'])}",
            flush=True,
        )
    out = {
        "probe": "PJM-NEXT-30 COAL_BIT in-money loading decomposition (zero LP)",
        "keeper_bundle": "results/calibration/w0_pjm_span",
        "block_hours": BLOCK,
        "q_year": Q_YEAR,
        "hi_hr": HI_HR,
        "method": __doc__,
        "years": [res[y] for y in years],
    }
    if all(y in res for y in FAIL + PASS):
        out["readings"] = readings(res)
        print(json.dumps(out["readings"], indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
