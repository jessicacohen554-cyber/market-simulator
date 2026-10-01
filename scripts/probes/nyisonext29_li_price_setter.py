"""NYISO-NEXT-29 phase 0 (ZERO LP): what sets the Zone-K price in the capped hours?

Reads the NEXT-26 arm-A legs (all-hours Zone-K TSL, ``nyiso_li_tsl_all_hours``)
and splits every hour in which ``NYC>Long_Island`` sits at its 940 MW cap into
three regimes by the state of the other Zone-K import path, the external
``NYISO_external>Long_Island`` link (Neptune + CSC + 1385):

* ``ext_free``  -- the external link is strictly inside its hourly bounds, so
  by LP duality ``price_K = price_ext + mu_month`` where ``mu_month`` is the
  dual of that link's monthly energy band (``nyiso_import_landing_band``).
  Verified: the within-month std of ``price_K - price_ext`` is reported.
* ``ext_cap``   -- the external link is at its hourly cap; K is then set by an
  LI resource (the marginal LI units are counted by plant group).
* ``ext_zero``  -- the external link is at zero.

Against measured: the hourly P-32 schedule on the same three ties
(``nyiso-interface-flows``) and the DA zonal LBMP (K, J, with the published
congestion component). Every number is a diagnostic; nothing here feeds a
solve (rule 13).

Usage: uv run python scripts/probes/nyisonext29_li_price_setter.py \
    --legs <dir holding nyisonext26_<y>/> --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "probes"))
from nyisonext26_li_gap import da_components  # noqa: E402

FLOWS = REPO / "data/clean/nyiso-interface-flows/NYISO"
LI_TIES = ("SCH - PJM_NEPTUNE", "SCH - NPX_CSC", "SCH - NPX_1385")
CAB = "NYC>Long_Island"
EXT = "NYISO_external>Long_Island"
CAB_LIMIT_MW = 940.0  # nyiso_li_tsl_all_hours: the published Zone-K TSL
TOL_MW = 0.5
YEARS = (2021, 2022, 2023, 2024, 2025)


def grid(year: int) -> pd.DatetimeIndex:
    """The 8760 local grid the NEXT-26 probes align DA to."""
    return pd.date_range(f"{year}-01-01", periods=8760, freq="h")


def measured_ties(year: int) -> pd.DataFrame:
    """Hourly measured net schedule and posted import limit on the LI ties."""
    f = pd.read_parquet(FLOWS / f"nyiso-interface-flows_{year}.parquet")
    f = f[f.interface.isin(LI_TIES)]
    g = f.groupby("interval_start_local")[["flow_mw", "positive_limit_mw"]].sum()
    return g.reindex(grid(year)).ffill()


def model_frames(leg: Path, year: int):
    """Model prices (zone pivot), link frame and LI unit rows for one leg."""
    n = pd.read_parquet(leg / "hourly" / f"network_{year}.parquet")
    n = n[n["pass"] == "P1"]
    s = pd.read_parquet(leg / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot(index="hour", columns="zone", values="price").reindex(range(8760))
    u = pd.read_parquet(leg / "hourly" / f"unit_hourly_{year}.parquet")
    u = u[(u["pass"] == "P1") & (u.zone == "Long_Island")]
    return p, n, u


def link(n: pd.DataFrame, name: str, col: str) -> np.ndarray:
    """One link's hourly column on the 8760 grid."""
    return n[n.name == name].set_index("hour")[col].reindex(range(8760)).to_numpy()


SEASONS = {"winter": (1, 2, 12), "spring": (3, 4, 5), "summer": (6, 7, 8), "fall": (9, 10, 11)}  # fmt: skip


def spread_split(err: np.ndarray, capped: np.ndarray, mo: np.ndarray) -> dict:
    """Where the annual K-over-J spread miss (model - DA, $/MWh x h) sits."""
    tot = float(np.nansum(err))
    out = {
        "annual_spread_err": round(float(np.nanmean(err)), 2),
        "share_in_uncapped_h": round(float(np.nansum(err[~capped])) / tot, 3),
    }
    for s, ms in SEASONS.items():
        m = np.isin(mo, ms) & ~capped
        out[f"uncapped_{s}_err"] = round(float(np.nanmean(err[m])), 2)
    return out


FLOW_BINS = (-1e9, 300.0, 500.0, 700.0, 900.0, CAB_LIMIT_MW - TOL_MW, 1e9)


def cong_by_flow(cab: np.ndarray, cong: np.ndarray, spread: np.ndarray) -> dict:
    """DA K-over-J congestion and model spread binned by model NYC>LI flow."""
    b = pd.cut(
        cab,
        FLOW_BINS,
        labels=["<300", "300-500", "500-700", "700-900", "900-cap", "cap"],
    )
    d = pd.DataFrame({"b": b, "cong": cong, "spr": spread})
    g = d.groupby("b", observed=False).agg(
        n=("cong", "size"), da_cong=("cong", "mean"), model_spread=("spr", "mean")
    )
    return {k: {c: round(float(v), 2) for c, v in r.items()} for k, r in g.iterrows()}


def summarize(leg: Path, year: int) -> dict:
    """Regime split, price-setter census and measured comparison for one year."""
    p, n, u = model_frames(leg, year)
    mo = grid(year).month.to_numpy()
    cab = link(n, CAB, "mw")
    ext, ext_cap = link(n, EXT, "mw"), link(n, EXT, "limit_up")
    mk, mj, mx = (p[z].to_numpy() for z in ("Long_Island", "NYC", "NYISO_external"))
    capped = cab >= CAB_LIMIT_MW - TOL_MW
    free = (ext > TOL_MW) & (ext < ext_cap - TOL_MW)
    at_cap = ext >= ext_cap - TOL_MW
    at_zero = ext <= TOL_MW

    c = da_components(year)
    da_k, da_j = c["lbmp"]["LONGIL"].to_numpy(), c["lbmp"]["N.Y.C."].to_numpy()
    da_cong_kj = (-(c["cong"]["LONGIL"] - c["cong"]["N.Y.C."])).to_numpy()
    meas = measured_ties(year)
    m_flow, m_lim = meas.flow_mw.to_numpy(), meas.positive_limit_mw.to_numpy()

    # Marginal LI units: strictly inside bounds with ~zero reduced cost.
    mg = u[(u.mw > TOL_MW) & (u.mw < u.cap_mw - TOL_MW) & (u.red_cost.abs() < 0.05)]
    marg_grp = mg.groupby("hour").plant_group.agg(
        lambda s: "|".join(sorted({str(x) or "oil/other" for x in s}))
    )
    marg_grp = marg_grp.reindex(range(8760))

    wedge = mk - mx
    wstd = pd.Series(wedge[free]).groupby(mo[free]).std().fillna(0.0)

    def mu(x, m):
        return round(float(np.nanmean(x[m])), 2) if m.any() else None

    def reg(m: np.ndarray) -> dict:
        return {
            "n_h": int(m.sum()),
            "share_of_capped": round(float(m.sum() / max(capped.sum(), 1)), 3),
            "spread_model": mu(mk - mj, m), "spread_da": mu(da_k - da_j, m),
            "da_cong_kj": mu(da_cong_kj, m),
            "err_K_vs_DA": mu(mk - da_k, m), "err_J_vs_DA": mu(mj - da_j, m),
            "ext_flow_model": mu(ext, m), "ext_cap_model": mu(ext_cap, m),
            "ext_flow_measured": mu(m_flow, m), "ext_posted_limit": mu(m_lim, m),
            "li_unit_marginal_share": round(float(marg_grp[m].notna().mean()), 3) if m.any() else None,
            "marginal_group_share": {k: round(float(v), 3) for k, v in marg_grp[m].value_counts(normalize=True).head(5).items()},
        }  # fmt: skip

    near = lambda f, cap: f >= 0.95 * cap  # noqa: E731
    ok = ~np.isnan(da_k) & ~np.isnan(m_flow)
    return {
        "year": year,
        "capped_h": int(capped.sum()),
        "wedge_within_month_std_max": round(float(wstd.max()), 3),
        "monthly_wedge_mu": {int(k): round(float(v), 1) for k, v in pd.Series(wedge[free]).groupby(mo[free]).mean().items()},
        "regime": {"ext_free": reg(capped & free), "ext_cap": reg(capped & at_cap),
                   "ext_zero": reg(capped & at_zero), "all_capped": reg(capped),
                   "uncapped": reg(~capped)},
        "ext_shape": {
            "model_mean": round(float(np.nanmean(ext)), 1),
            "measured_mean": round(float(np.nanmean(m_flow)), 1),
            "model_share_h_ge95pct_cap": round(float(np.mean(near(ext, ext_cap))), 3),
            "measured_share_h_ge95pct_posted": round(float(np.nanmean(near(m_flow, m_lim))), 3),
            "measured_share_h_ge95pct_model_cap": round(float(np.nanmean(near(m_flow, ext_cap))), 3),
            "model_std": round(float(np.nanstd(ext)), 1),
            "measured_std": round(float(np.nanstd(m_flow)), 1),
            "corr_model_flow_vs_model_K": round(float(np.corrcoef(ext, mk)[0, 1]), 3),
            "corr_measured_flow_vs_DA_K": round(float(np.corrcoef(m_flow[ok], da_k[ok])[0, 1]), 3),
        },
        "da_cong_by_model_cab_flow": cong_by_flow(cab, da_cong_kj, mk - mj),
        "spread_miss_split": spread_split(mk - mj - (da_k - da_j), capped, mo),
        "monthly_twh": {
            "model": [round(float(ext[mo == x].sum()) / 1e6, 3) for x in range(1, 13)],
            "measured": [round(float(np.nansum(m_flow[mo == x])) / 1e6, 3) for x in range(1, 13)],
        },
    }  # fmt: skip


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    res = {
        "lane": "NYISO-NEXT-29",
        "source": "NEXT-26 arm-A legs claude/nyisonext26-<y> @ 4213945e",
        "years": [summarize(a.legs / f"nyisonext26_{y}", y) for y in YEARS],
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1))
    print(a.out)


if __name__ == "__main__":
    main()
