"""PJM-NEXT-24 card 1 (zero LP): one loading-vs-margin curve for coal and CT, real vs keeper.

NEXT-20/22 found the keeper's coal loading-vs-margin response steeper than real coal's;
NEXT-23 found the same for CT_PEAKER across plants (cheap CTs over-run, dear ones under-run).
This puts both classes on ONE axis, per plant-hour:

    margin = actual PJM price (system RT, and DA) - the plant's keeper offer

The offer is the capacity-weighted mean P1 ``mc`` over the plant's LP tranches in that hour
(``unit_marginal_<y>``) - set by fuel, heat rate and bands, not by dispatch, so it is the same
for the model and the real plant. Loading = output / the plant's LP available capacity
(``cap_mw``), with model output from the keeper and real output from the C1 bench (EIA-923
net annual, CAMPD hourly shape). The keeper's own-price curve (margin on its zonal price) is
reported beside it: an LP responds to its own price as a step.

Per class (COAL = COAL_*, CT = CT_PEAKER) and year, by margin bin: plant-hours, real and model
loading, real and model TWh. Summary per class-year:

- ``contrast``: loading(+10..+40) - loading(-40..-10) (how steep the response is);
- ``m_half``: the margin where loading crosses half its in-money level (linear interpolation);
- ``oom_share``: share of energy produced at margin < 0.

Writes ``results/phase0/pjm/_pjmnext24_loading_margin.json``.
Run: ``python3 scripts/probes/_pjmnext24_loading_margin.py``
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
OUT = REPO / "results/phase0/pjm/_pjmnext24_loading_margin.json"
YEARS = range(2019, 2026)
T = 8760
EDGES = (-1e9, -40, -20, -10, -5, 0, 5, 10, 20, 40, 1e9)


def klass(group: str) -> str | None:
    """COAL for every COAL_* subclass, CT for CT_PEAKER, else None."""
    if group.startswith("COAL"):
        return "COAL"
    return "CT" if group == "CT_PEAKER" else None


def bench(y: int) -> dict[tuple[int, str], np.ndarray]:
    """C1 bench hourly real net output (MW, clipped at 0) per (plant code, class)."""
    bp = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    out: dict[tuple[int, str], np.ndarray] = {}
    for key, b in bp.items():
        k = klass(str(b.get("group")))
        if k is None or b.get("nodata") in (True, "True") or not b.get("campd"):
            continue
        raw = str(b.get("pcode") or key).split(":")[0]
        if not raw.isdigit():
            continue
        ann = max(float(b.get("e_ann") or b.get("c_ann") or 0.0), 0.0)
        mw = _dec(b["campd"], ann)[:T]
        out[(int(raw), k)] = out.get((int(raw), k), 0) + mw
    return out


def plant_hours(y: int, act: pd.DataFrame) -> pd.DataFrame:
    """Keeper plant-hours for coal + CT joined to the bench, with offer and three margins."""
    cols = ["plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    u = u[u.hour < T]
    u["k"] = u.plant_group.astype(str).map(klass)
    u = u[u.k.notna() & (u.cap_mw > 0)]
    u["capmc"] = u.cap_mw * u.mc
    p = (
        u.groupby(["plant_code", "k", "hour"], observed=True)
        .agg(mw=("mw", "sum"), cap=("cap_mw", "sum"), capmc=("capmc", "sum"))
        .reset_index()
    )
    p["offer"] = p.capmc / p.cap
    zone = u.groupby("plant_code", observed=True).zone.first().astype(str)
    p["zone"] = p.plant_code.map(zone)
    s = pd.read_parquet(HOURLY / f"system_{y}.parquet")
    pz = s.pivot_table(index="hour", columns="zone", values="price").reindex(range(T))
    pzl = pz.stack().rename("pz").reset_index()
    p = p.merge(pzl, on=["hour", "zone"], how="left")
    a = act[act.year == y].sort_values("hour")
    h = p.hour.to_numpy()
    p["m_rt"] = a.rt.to_numpy()[:T][h] - p.offer
    p["m_da"] = a.da.to_numpy()[:T][h] - p.offer
    p["m_pz"] = p.pz - p.offer
    b = bench(y)
    real = np.full(len(p), np.nan)
    for (code, k), idx in p.groupby(["plant_code", "k"], observed=True).indices.items():
        r = b.get((int(code), k))
        if r is not None:
            real[idx] = r[p.hour.to_numpy()[idx]]
    p["real"] = real
    return p[p.real.notna()]


def curve(p: pd.DataFrame, col: str) -> list[dict]:
    """Loading and energy by margin bin on margin column ``col``."""
    rows = []
    b = pd.cut(p[col], EDGES, right=False)
    for iv, g in p.groupby(b, observed=False):
        cap = g.cap.sum()
        rows.append(
            {
                "bin": f"{iv.left:g}..{iv.right:g}",
                "plant_hours": len(g),
                "real_load": round(float(g.real.sum() / cap), 3) if cap else None,
                "model_load": round(float(g.mw.sum() / cap), 3) if cap else None,
                "real_twh": round(float(g.real.sum()) / 1e6, 2),
                "model_twh": round(float(g.mw.sum()) / 1e6, 2),
            }
        )
    return rows


def _m_half(rows: list[dict], key: str) -> float | None:
    """Margin where loading crosses half of its +10..+40 level (bin mid-points)."""
    mids = np.array([-50, -30, -15, -7.5, -2.5, 2.5, 7.5, 15, 30, 50], dtype=float)
    lv = np.array([r[key] if r[key] is not None else np.nan for r in rows])
    top = np.nanmean(lv[7:9])
    half = 0.5 * top
    for i in range(len(lv) - 1):
        if lv[i] < half <= lv[i + 1]:
            return round(
                float(
                    mids[i]
                    + (half - lv[i]) * (mids[i + 1] - mids[i]) / (lv[i + 1] - lv[i])
                ),
                1,
            )
    return None


def summary(rows: list[dict], p: pd.DataFrame, col: str) -> dict:
    """Contrast, half-loading margin and out-of-money energy share, real vs model."""
    out = {}
    for who, key, e in (("real", "real_load", "real"), ("model", "model_load", "mw")):
        lv = [r[key] for r in rows]
        lo = np.nanmean([v for v in lv[1:3] if v is not None])
        hi = np.nanmean([v for v in lv[7:9] if v is not None])
        out[who] = {
            "load_-40..-10": round(float(lo), 3),
            "load_+10..+40": round(float(hi), 3),
            "contrast": round(float(hi - lo), 3),
            "m_half": _m_half(rows, key),
            "oom_share": round(float(p.loc[p[col] < 0, e].sum() / p[e].sum()), 3),
        }
    return out


def main() -> None:
    """Every year, both classes, three margin axes."""
    act = pd.read_parquet(ACTUAL)
    out: dict = {"what": "PJM-NEXT-24 card 1: loading vs margin, coal and CT. ZERO LP."}
    for y in YEARS:
        p = plant_hours(y, act)
        for k, g in p.groupby("k"):
            d: dict = {"plants": int(g.plant_code.nunique())}
            for col in ("m_rt", "m_da", "m_pz"):
                rows = curve(g, col)
                d[col] = {"curve": rows, "summary": summary(rows, g, col)}
            out.setdefault(k, {})[str(y)] = d
            s = d["m_rt"]["summary"]
            print(y, k, d["plants"], "RT:", s["real"], "|", s["model"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
