"""PJM-NEXT-20 card 1 (zero LP): does the same low-end price gap move more coal in 2019-2021?

Hypothesis (NEXT-19 RESULT §2): the keeper's price is too high in sub-$25 hours in every
year, and in 2019-2021 (coal and CC costs within ~$3) that gap moves far more coal than in
2023-2024. Tested at plant-hour grain on COAL_* only, keeper P1 (``unit_marginal_<y>``):

- ``gap``: the coal unit's own zone price minus PJM actual RT (system), coal-MW weighted.
- ``underwater`` plant-hour: the plant's MW-weighted model offer ``mc`` exceeds actual RT,
  i.e. at the actual price the model's own coal offer would not clear.
- Per plant-hour, model MW vs the C1 bench's CAMPD profile rescaled to EIA-923 (``_dec``).
  The coal over-run (model - bench, TWh) is split into underwater and above-water hours,
  within the keeper's coal-set hours (marginal weight >= 0.5 on COAL_*, NEXT-19) and the
  other (coal-inframarginal) hours.

Confirmed iff the underwater over-run carries the 2019-2021 excess and is small in
2023-2024 while the price gap itself is no larger in 2019-2021 (same error, more coal moved).

Writes ``results/phase0/pjm/_pjmnext20_coal_price_response.json``.
Run: ``python3 scripts/probes/_pjmnext20_coal_price_response.py``
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
from _pjmnext19_coalset_balance import _coal_set_mask  # noqa: E402

HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext20_coal_price_response.json"
YEARS = range(2019, 2026)
T = 8760
LOW_RT = 25.0  # $/MWh, the NEXT-17/19 "sub-$25" low-end hour


def _wq(x: np.ndarray, w: np.ndarray, q: float) -> float:
    """Weighted quantile."""
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][np.searchsorted(c, q * c[-1])])


def year(y: int) -> dict:
    """One year's coal price-response split."""
    cols = ["plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    u = u[u.plant_group.astype(str).str.startswith("COAL") & (u.hour < T)]
    s = pd.read_parquet(
        HOURLY / f"system_{y}.parquet", columns=["zone", "hour", "price"]
    )
    s = s[s.hour < T]
    u = u.merge(s, on=["zone", "hour"], how="left")
    act = pd.read_parquet(ACTUAL)
    rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
    coal_set = _coal_set_mask(y)

    u["mwmc"] = u.mw * u.mc
    u["mwp"] = u.mw * u.price
    p = u.groupby(["plant_code", "hour"], observed=True)[
        ["mw", "cap_mw", "mwmc", "mwp"]
    ].sum()
    p = p.reset_index()
    plants = sorted(p.plant_code.unique())
    model = np.zeros((len(plants), T))
    mcw = np.full((len(plants), T), np.nan)
    pidx = {c: i for i, c in enumerate(plants)}
    ii = p.plant_code.map(pidx).to_numpy()
    hh = p.hour.to_numpy()
    model[ii, hh] = p.mw.to_numpy()
    cap = np.zeros_like(model)
    cap[ii, hh] = p.cap_mw.to_numpy()
    on = p.mw.to_numpy() > 0
    mcw[ii[on], hh[on]] = (p.mwmc / p.mw).to_numpy()[on]
    # Plants with no output in an hour: use the plant's annual MW-weighted offer.
    ann = (
        p.groupby("plant_code").mwmc.sum() / p.groupby("plant_code").mw.sum()
    ).reindex(plants)
    mcw = np.where(np.isnan(mcw), ann.to_numpy()[:, None], mcw)

    bench = np.zeros_like(model)
    bp = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    covered = np.zeros(len(plants), bool)
    for key, b in bp.items():
        if not str(b.get("group", "")).startswith("COAL"):
            continue
        code = (
            int(b.get("pcode") or key) if str(b.get("pcode") or key).isdigit() else None
        )
        if code not in pidx or b.get("nodata") in (True, "True") or not b.get("campd"):
            continue
        bench[pidx[code]] = _dec(b["campd"], b.get("e_ann") or b.get("c_ann"))
        covered[pidx[code]] = True

    m, a = model[covered], bench[covered]
    under = mcw[covered] > rt[None, :]
    res: dict = {"plants_model": len(plants), "plants_benched": int(covered.sum())}
    res["model_twh"] = round(float(model.sum()) / 1e6, 2)
    res["benched_model_twh"] = round(float(m.sum()) / 1e6, 2)
    res["bench_twh"] = round(float(a.sum()) / 1e6, 2)

    # Price gap, coal-MW weighted (unit's own zone price vs system RT).
    w = u.mw.to_numpy()
    g = (u.price.to_numpy() - rt[u.hour.to_numpy()])[w > 0]
    lo = rt[u.hour.to_numpy()][w > 0] < LOW_RT
    w = w[w > 0]
    res["gap_model_minus_rt"] = {
        "median_all": round(_wq(g, w, 0.5), 2),
        "median_rt_lt_25": round(_wq(g[lo], w[lo], 0.5), 2) if lo.any() else None,
        "coal_twh_in_rt_lt_25": round(float(w[lo].sum()) / 1e6, 2),
    }
    for name, hm in (("coal_set", coal_set), ("other", ~coal_set)):
        d = {}
        for tag, mk in (("underwater", under), ("abovewater", ~under)):
            mk = mk & hm[None, :]
            mm, aa = float(m[mk].sum()) / 1e6, float(a[mk].sum()) / 1e6
            d[tag] = {
                "model": round(mm, 2),
                "bench": round(aa, 2),
                "gap": round(mm - aa, 2),
            }
        res[name] = d
    # Above-water over-run by margin (RT - offer) and by the real plant's state.
    margin = rt[None, :] - mcw[covered]
    aw = ~under
    full = m >= 0.98 * cap[covered]
    split = {}
    for lo_, hi_ in ((0, 5), (5, 15), (15, 1e9)):
        mk = aw & (margin >= lo_) & (margin < hi_)
        split[f"{lo_}-{hi_ if hi_ < 1e9 else 'inf'}"] = round(
            float((m - a)[mk].sum()) / 1e6, 2
        )
    res["abovewater_by_margin"] = split
    # Net loading on the model's available cap, real plant on, by margin bin (bench = EIA-923 net).
    ld = {}
    cc = cap[covered]
    for lo_, hi_ in ((-1e9, 0), (0, 5), (5, 15), (15, 1e9)):
        mk = (margin >= lo_) & (margin < hi_) & (a > 0) & (cc > 0)
        tag = f"{lo_ if lo_ > -1e9 else '-inf'}..{hi_ if hi_ < 1e9 else 'inf'}"
        ld[tag] = {
            "model": round(float(m[mk].sum() / cc[mk].sum()), 3),
            "bench": round(float(a[mk].sum() / cc[mk].sum()), 3),
            "twh_gap": round(float((m - a)[mk].sum()) / 1e6, 2),
        }
    res["real_on_net_loading_by_margin"] = ld
    res["abovewater_by_state"] = {
        "real_off": round(float((m - a)[aw & (a <= 0)].sum()) / 1e6, 2),
        "real_on": round(float((m - a)[aw & (a > 0)].sum()) / 1e6, 2),
        "model_full": round(float((m - a)[aw & full].sum()) / 1e6, 2),
        "model_part": round(float((m - a)[aw & ~full & (m > 0)].sum()) / 1e6, 2),
        "model_off": round(float((m - a)[aw & (m <= 0)].sum()) / 1e6, 2),
        "real_on_loading_model_vs_bench": [
            round(
                float(
                    m[aw & (a > 0) & (m > 0)].sum()
                    / cap[covered][aw & (a > 0) & (m > 0)].sum()
                ),
                3,
            ),
            round(
                float(
                    a[aw & (a > 0) & (m > 0)].sum()
                    / cap[covered][aw & (a > 0) & (m > 0)].sum()
                ),
                3,
            ),
        ],
    }
    # Underwater depth: how far RT sits below the plant's offer, model-MW weighted.
    mk = under & (m > 0)
    depth = (mcw[covered] - rt[None, :])[mk]
    res["underwater_depth_median"] = (
        round(_wq(depth, m[mk], 0.5), 2) if mk.any() else None
    )
    res["underwater_rt_lt_25_share"] = (
        round(float(m[mk & (rt[None, :] < LOW_RT)].sum() / m[mk].sum()), 3)
        if mk.any()
        else None
    )
    return res


def main() -> None:
    """Every year."""
    out: dict = {
        "what": "PJM-NEXT-20 card 1: coal over-run by underwater plant-hour. ZERO LP."
    }
    for y in YEARS:
        r = year(y)
        out[str(y)] = r
        print(
            y,
            r["gap_model_minus_rt"],
            "| other uw/aw gap",
            r["other"]["underwater"]["gap"],
            r["other"]["abovewater"]["gap"],
            "| set uw/aw",
            r["coal_set"]["underwater"]["gap"],
            r["coal_set"]["abovewater"]["gap"],
            "| margin",
            r["abovewater_by_margin"],
            r["abovewater_by_state"],
            "| bench cov",
            r["benched_model_twh"],
            "/",
            r["model_twh"],
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
