"""PJM-NEXT-22 card 1 (zero LP): which coal plants carry 2025's COAL_BIT over-run vs 2024?

Keeper P1 per-unit layer (``unit_marginal_<y>``) vs the C1 bench (EIA-923 net, ``e_ann``) per
coal plant, every year 2019-2025. For each plant-year:

- ``model`` / ``bench`` TWh and the over-run (model - bench);
- ``cap`` mean available MW in the LP (``cap_mw``), the model and real capacity factor on it;
- ``mc`` the plant's MW-weighted P1 offer, ``rt`` PJM actual RT (system) weighted by the bench
  profile, and ``margin`` = mean actual RT - mean offer over all hours (an annual merit proxy).

The 2025 - 2024 over-run delta is split into plants present in both years (and within those by
zone and by margin bin) and plants present in only one (fleet change). A plant's real profile is
the bench's CAMPD shape rescaled to EIA-923 (``_dec``), used for the hourly split by RT margin.

Writes ``results/phase0/pjm/_pjmnext22_coal_2025_plants.json``.
Run: ``python3 scripts/probes/_pjmnext22_coal_2025_plants.py``
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext16_cc_loading import _dec  # noqa: E402

HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext22_coal_2025_plants.json"
YEARS = range(2019, 2026)
T = 8760
MARGIN_BINS = ((-1e9, 0.0), (0.0, 5.0), (5.0, 15.0), (15.0, 1e9))


def plants_year(y: int, rt: np.ndarray) -> pd.DataFrame:
    """Per coal plant: model/bench TWh, LP capacity, offer, margin and hourly split by margin."""
    cols = ["plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    u = u[u.plant_group.astype(str).str.startswith("COAL") & (u.hour < T)].copy()
    u["mwmc"] = u.mw * u.mc
    u["capmc"] = u.cap_mw * u.mc
    p = (
        u.groupby(["plant_code", "hour"], observed=True)[
            ["mw", "cap_mw", "mwmc", "capmc"]
        ]
        .sum()
        .reset_index()
    )
    meta = u.groupby("plant_code", observed=True).agg(
        zone=("zone", "first"), group=("plant_group", "first")
    )
    bp = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    bench_by_code: dict[int, dict] = {}
    for key, b in bp.items():
        if not str(b.get("group", "")).startswith("COAL"):
            continue
        raw = str(b.get("pcode") or key).split(":")[0]
        if raw.isdigit():
            bench_by_code[int(raw)] = b
    rows = []
    for code, g in p.groupby("plant_code"):
        mw = np.zeros(T)
        cap = np.zeros(T)
        cmc = np.zeros(T)
        h = g.hour.to_numpy()
        mw[h] = g.mw.to_numpy()
        cap[h] = g.cap_mw.to_numpy()
        cmc[h] = g.capmc.to_numpy()
        # Offer per hour: capacity-weighted across the plant's tranches (independent of dispatch).
        offer = np.where(cap > 0, cmc / np.where(cap > 0, cap, 1), np.nan)
        b = bench_by_code.get(int(code))
        real = np.zeros(T)
        benched = False
        if b and b.get("nodata") not in (True, "True") and b.get("campd"):
            real = _dec(b["campd"], b.get("e_ann") or b.get("c_ann"))
            benched = True
        e_ann = float(b.get("e_ann") or 0.0) if b else 0.0
        margin_h = rt - offer
        r = {
            "plant_code": int(code),
            "name": (b or {}).get("name", ""),
            "zone": str(meta.loc[code, "zone"]),
            "group": str(meta.loc[code, "group"]),
            "benched": benched,
            "model_twh": mw.sum() / 1e6,
            "bench_twh": real.sum() / 1e6 if benched else e_ann,
            "cap_mw": cap.mean(),
            "offer": float(np.nanmean(offer)),
            "rt_margin": float(np.nanmean(margin_h)),
        }
        for lo, hi in MARGIN_BINS:
            mk = (margin_h >= lo) & (margin_h < hi)
            tag = f"m{lo:g}_{hi:g}".replace("-1e+09", "-inf").replace("1e+09", "inf")
            r[f"{tag}_model"] = mw[mk].sum() / 1e6
            r[f"{tag}_bench"] = real[mk].sum() / 1e6
            r[f"{tag}_cap"] = cap[mk].sum() / 1e6
        rows.append(r)
    df = pd.DataFrame(rows)
    df["over"] = df.model_twh - df.bench_twh
    df["cf_model"] = df.model_twh * 1e6 / (df.cap_mw * T).where(df.cap_mw > 0)
    df["cf_real"] = df.bench_twh * 1e6 / (df.cap_mw * T).where(df.cap_mw > 0)
    df["year"] = y
    return df


def main() -> None:
    """Every year, then the 2025 - 2024 attribution."""
    act = pd.read_parquet(ACTUAL)
    frames = []
    summary: dict = {}
    for y in YEARS:
        rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
        d = plants_year(y, rt)
        frames.append(d)
        summary[str(y)] = {
            "plants": int(len(d)),
            "model_twh": round(d.model_twh.sum(), 2),
            "bench_twh": round(d.bench_twh.sum(), 2),
            "over_twh": round(d.over.sum(), 2),
            "cap_gw": round(d.cap_mw.sum() / 1e3, 2),
            "cf_model": round(d.model_twh.sum() * 1e6 / (d.cap_mw.sum() * T), 3),
            "cf_real": round(d.bench_twh.sum() * 1e6 / (d.cap_mw.sum() * T), 3),
            "rt_mean": round(float(rt.mean()), 2),
            "offer_capw": round(float((d.offer * d.cap_mw).sum() / d.cap_mw.sum()), 2),
        }
        print(y, summary[str(y)])
    allp = pd.concat(frames, ignore_index=True)

    # Over-run by margin bin, every year (model vs real loading on LP capacity).
    by_margin = {}
    for y in YEARS:
        d = allp[allp.year == y]
        row = {}
        for lo, hi in MARGIN_BINS:
            tag = f"m{lo:g}_{hi:g}".replace("-1e+09", "-inf").replace("1e+09", "inf")
            m, b, c = (
                d[f"{tag}_model"].sum(),
                d[f"{tag}_bench"].sum(),
                d[f"{tag}_cap"].sum(),
            )
            row[tag] = {
                "over": round(m - b, 2),
                "cf_model": round(m / c, 3) if c else None,
                "cf_real": round(b / c, 3) if c else None,
                "cap_twh": round(c, 1),
            }
        by_margin[str(y)] = row

    # 2025 vs 2024 attribution.
    a, b = (
        allp[allp.year == 2024].set_index("plant_code"),
        allp[allp.year == 2025].set_index("plant_code"),
    )
    both = a.index.intersection(b.index)
    only24, only25 = a.index.difference(b.index), b.index.difference(a.index)
    att = {
        "delta_over_total": round(b.over.sum() - a.over.sum(), 2),
        "both": {
            "n": int(len(both)),
            "delta_over": round(b.loc[both].over.sum() - a.loc[both].over.sum(), 2),
            "delta_model": round(
                b.loc[both].model_twh.sum() - a.loc[both].model_twh.sum(), 2
            ),
            "delta_bench": round(
                b.loc[both].bench_twh.sum() - a.loc[both].bench_twh.sum(), 2
            ),
            "delta_cap_gw": round(
                (b.loc[both].cap_mw.sum() - a.loc[both].cap_mw.sum()) / 1e3, 2
            ),
        },
        "only_2024": {
            "n": int(len(only24)),
            "names": a.loc[only24].name.tolist(),
            "model": round(a.loc[only24].model_twh.sum(), 2),
            "bench": round(a.loc[only24].bench_twh.sum(), 2),
            "over": round(a.loc[only24].over.sum(), 2),
        },
        "only_2025": {
            "n": int(len(only25)),
            "names": b.loc[only25].name.tolist(),
            "model": round(b.loc[only25].model_twh.sum(), 2),
            "bench": round(b.loc[only25].bench_twh.sum(), 2),
            "over": round(b.loc[only25].over.sum(), 2),
        },
    }
    j = pd.DataFrame(
        {
            "name": b.loc[both].name,
            "zone": b.loc[both].zone,
            "group": b.loc[both].group,
            "cap24": a.loc[both].cap_mw,
            "cap25": b.loc[both].cap_mw,
            "over24": a.loc[both].over,
            "over25": b.loc[both].over,
            "model24": a.loc[both].model_twh,
            "model25": b.loc[both].model_twh,
            "bench24": a.loc[both].bench_twh,
            "bench25": b.loc[both].bench_twh,
            "offer24": a.loc[both].offer,
            "offer25": b.loc[both].offer,
            "margin24": a.loc[both].rt_margin,
            "margin25": b.loc[both].rt_margin,
        }
    )
    j["d_over"] = j.over25 - j.over24
    j = j.sort_values("d_over", ascending=False)
    att["by_zone"] = (
        j.groupby("zone")[["d_over", "over24", "over25"]]
        .sum()
        .round(2)
        .sort_values("d_over")
    ).to_dict(orient="index")
    j["d_margin"] = j.margin25 - j.margin24
    att["by_margin_change"] = {
        lab: round(float(j[mk].d_over.sum()), 2)
        for lab, mk in (
            ("margin_up_gt5", j.d_margin > 5),
            ("margin_up_0_5", (j.d_margin > 0) & (j.d_margin <= 5)),
            ("margin_down", j.d_margin <= 0),
        )
    }
    att["top_plants"] = j.head(15).round(2).reset_index().to_dict(orient="records")
    att["bottom_plants"] = j.tail(5).round(2).reset_index().to_dict(orient="records")
    att["concentration"] = {
        "top5_share_of_delta": round(float(j.d_over.head(5).sum() / j.d_over.sum()), 3),
        "top15_share_of_delta": round(
            float(j.d_over.head(15).sum() / j.d_over.sum()), 3
        ),
        "plants_with_d_over_gt_0.2": int((j.d_over > 0.2).sum()),
    }

    # Per-plant over-run, every year, for the 2025 top plants (is 2025 like 2019-21 for them?).
    top = j.head(10).index
    att["top10_over_by_year"] = {
        str(int(c)): {
            "name": b.loc[c, "name"],
            **{
                str(y): round(
                    float(allp[(allp.year == y) & (allp.plant_code == c)].over.sum()), 2
                )
                for y in YEARS
            },
        }
        for c in top
    }

    out = {
        "what": "PJM-NEXT-22 card 1: per-plant coal over-run, 2025 vs 2024. ZERO LP.",
        "summary": summary,
        "by_margin": by_margin,
        "attribution_2025_vs_2024": att,
    }
    print(json.dumps(by_margin, indent=0))
    print(
        json.dumps(
            {k: v for k, v in att.items() if k != "top10_over_by_year"},
            indent=0,
            default=str,
        )
    )
    print(json.dumps(att["top10_over_by_year"], indent=0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
