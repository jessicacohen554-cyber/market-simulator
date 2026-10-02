"""PJM-NEXT-25 card 1 (zero LP): which coal plants make the keeper's 2019-21 response steep?

NEXT-24 found the keeper's coal within-plant loading contrast 2.2-3x real in 2019-21 and
1.2-1.7x in 2022-25. This splits the coal fleet by where its tranche structure comes from:

- ``measured_row``: the plant has a row in ``thermal_tranches_PJM.csv`` (CAMPD-derived
  must-run / committed / online fraction);
- ``default_bins``: no row, so ``bins_to_fleet`` gives it the class fallback (no must-run,
  a thin committed block, ~0.93 of capacity in the econ ramp).

Per cohort and year: plants, capacity, model and real TWh, NEXT-24's within-plant contrast
(``_pjmnext24_within_across.within``, actual-RT margin) and the pooled contrast. Also the
keeper's per-plant tranche shares by cohort (from ``unit_marginal_<y>`` tranche maxima) and
whether a default-bin plant has CAMPD operation in the year (bench ``campd`` present).

Writes ``results/phase0/pjm/_pjmnext25_coal_cohort.json``.
Run: ``python3 scripts/probes/_pjmnext25_coal_cohort.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext24_loading_margin import ACTUAL, HOURLY, T, YEARS, plant_hours  # noqa: E402
from _pjmnext24_within_across import within  # noqa: E402

TRANCHES = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
OUT = REPO / "results/phase0/pjm/_pjmnext25_coal_cohort.json"
TR_RE = r"_(committed|econ|mustrun|peak|sync)[a-z]*\d*$"


def tranche_shares(y: int) -> pd.DataFrame:
    """Per coal plant: tranche capacity shares (sum of per-unit hourly maxima)."""
    u = pd.read_parquet(
        HOURLY / f"unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "cap_mw"],
    )
    u = u[(u.hour < T) & u.plant_group.astype(str).str.startswith("COAL")]
    mx = u.groupby(["plant_code", "unit_id"], observed=True).cap_mw.max().reset_index()
    mx["tr"] = mx.unit_id.astype(str).str.extract(TR_RE)[0]
    pv = mx.pivot_table(
        index="plant_code", columns="tr", values="cap_mw", aggfunc="sum"
    ).fillna(0.0)
    tot = pv.sum(axis=1)
    sh = pv.div(tot, axis=0)
    sh["mw"] = tot
    return sh[tot > 0]


def pooled(g: pd.DataFrame) -> tuple[float, float]:
    """Pooled loading(+10..+40) - loading(-40..-10), real and model."""
    lo = g[(g.m_rt >= -40) & (g.m_rt < -10)]
    hi = g[(g.m_rt >= 10) & (g.m_rt < 40)]
    if lo.cap.sum() == 0 or hi.cap.sum() == 0:
        return float("nan"), float("nan")
    return (
        float(hi.real.sum() / hi.cap.sum() - lo.real.sum() / lo.cap.sum()),
        float(hi.mw.sum() / hi.cap.sum() - lo.mw.sum() / lo.cap.sum()),
    )


def main() -> None:
    """Every year, both cohorts."""
    t = pd.read_csv(TRANCHES)
    measured = set(t[t.plant_group.astype(str).str.contains("COAL")].plant_code)
    act = pd.read_parquet(ACTUAL)
    out: dict = {
        "what": "PJM-NEXT-25 card 1: coal response by tranche-row cohort. ZERO LP.",
        "measured_rows": len(measured),
        "years": {},
    }
    for y in YEARS:
        p = plant_hours(y, act)
        p = p[p.k == "COAL"]
        sh = tranche_shares(y)
        coh = np.where(p.plant_code.isin(measured), "measured_row", "default_bins")
        d: dict = {}
        for c, g in p.groupby(coh):
            pr, pm = pooled(g)
            s = sh[sh.index.isin(g.plant_code.unique())]
            w = s.mw / s.mw.sum()
            d[c] = {
                "plants": int(g.plant_code.nunique()),
                "cap_gw": round(float(s.mw.sum()) / 1e3, 2),
                "model_twh": round(float(g.mw.sum()) / 1e6, 2),
                "real_twh": round(float(g.real.sum()) / 1e6, 2),
                "model_minus_real_twh": round(
                    float(g.mw.sum() - g.real.sum()) / 1e6, 2
                ),
                "within_contrast_rt": within(g, "m_rt"),
                "pooled_contrast_rt": {"real": round(pr, 3), "model": round(pm, 3)},
                "tranche_share_capwtd": {
                    k: round(float((w * s[k]).sum()), 3)
                    for k in ("mustrun", "sync", "committed", "econ", "peak")
                    if k in s
                },
            }
        dflt = sorted(
            set(p.plant_code[~p.plant_code.isin(measured)].astype(int).tolist())
        )
        d["default_bin_plants"] = {
            str(c): round(float(sh.mw.get(c, 0.0)), 1) for c in dflt
        }
        out["years"][str(y)] = d
        print(
            y,
            {
                k: (v["cap_gw"], v["model_minus_real_twh"], v["within_contrast_rt"])
                for k, v in d.items()
                if k != "default_bin_plants"
            },
            flush=True,
        )
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
