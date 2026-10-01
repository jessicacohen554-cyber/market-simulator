"""SPP-91 stage 2 (ZERO LP): is SPP-90's flat on-line coal shortfall reserve headroom or nodal congestion?

Record: ``docs/records/spp/FINDING-spp-91-flat-coal-headroom-2026-09-27.md``.

Reads stage 1 (``_spp91_flat_coal_series.py``: per plant x hour flat shortfall ``F``), the committed SPP
RTBM operating-reserve cleared MW (``spp_rtbm_or_cleared_hourly.parquet``, SPP-81) and MCPs
(``data/raw/spp-or-mcp``), the plant-node RT LMPs fetched by ``_spp91_node_lmp_fetch.py``, and the
SPP-89 stacks (keeper per-plant coal offer ``mc_base``). All hours with the actual system RT LMP >= $30.

(a) reserves: size bound (system reg-up + spin cleared MW vs F), hourly co-movement of F with cleared
    reg-up + spin MW and with the reg-up / spin MCPs, raw and within-week demeaned; F by hub-LMP band.
(b) congestion: for the mapped plants, share of flat-F MWh in hours where the plant's own node LMP is
    below the keeper's own top coal offer for that plant (economically backed down at its node) or below
    $25; node - hub spread in F hours vs other in-money hours; SPP North - South hub spread.

Usage: ``python scripts/probes/_spp91_flat_coal_tests.py --flat-dir <d> --node-dir <d> --stack-dir <d> --out <json>``
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts" / "data"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from fetch_spp_or_cleared import model_hour  # noqa: E402
from scripts.probes._spp90_coal_inmoney_conduct import COAL  # noqa: E402
from scripts.probes._spp91_node_lmp_fetch import PLANTS  # noqa: E402

YEARS = range(2019, 2026)
_MSTART = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])


def node_matrix(df: pd.DataFrame, y: int) -> dict[str, np.ndarray]:
    """Hourly LMP per location on the model clock (fixed CST hour-beginning; published HE is CPT)."""
    d = df[df["ptype"] == "LMP"].copy()
    # The MONTHLY-SL Date/HE label is GMT hour-ENDING (verified: -7 h reproduces the committed
    # model-clock hub series actual_lmp_hourly_zonal_SPP.parquet exactly, r = 1.000, 2019/2023/2025).
    t = pd.to_datetime(d["date"]) + pd.to_timedelta(d["he"], unit="h") - pd.Timedelta(hours=7)
    ok = (t.dt.year == y) & ~((t.dt.month == 2) & (t.dt.day == 29))
    d, t = d[ok], t[ok]
    idx = (_MSTART[t.dt.month.to_numpy() - 1] + t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    d = d.assign(i=idx)
    out = {}
    for l, g in d.groupby("loc"):
        a = np.full(8760, np.nan)
        s = g.groupby("i")["value"].mean()
        a[s.index.to_numpy()] = s.to_numpy()
        out[l] = a
    return out


def mcp_hourly(y: int) -> pd.DataFrame | None:
    """Hourly mean (over reserve zones and intervals) RT reg-up and spin MCP, model clock."""
    p = RAW_DATA_DIR / f"spp-or-mcp/RTBM_MCP_{y}.csv.zip"
    if not p.exists():
        return None
    z = zipfile.ZipFile(p)
    d = pd.read_csv(z.open(z.namelist()[0]), skipinitialspace=True)
    d.columns = [c.strip().upper().replace(" ", "_") for c in d.columns]
    d["i"] = model_hour(d["GMTINTERVALEND"], y)
    d = d[d["i"] >= 0]
    return d.groupby("i")[["REGUPSERVICE", "SPIN"]].mean().reindex(range(8760)).set_axis(["RegUPService", "Spin"], axis=1)


def corr(a, b) -> float | None:
    """Pearson r over finite pairs."""
    k = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[k], b[k])[0, 1]) if k.sum() > 30 and np.std(a[k]) > 0 and np.std(b[k]) > 0 else None


def year_tests(y: int, fd: Path, nd: Path, sd: Path, orc: pd.DataFrame) -> dict:
    """All tests for one year."""
    z = np.load(fd / f"flat_{y}.npz")
    codes, F, ON, lmp = z["codes"], z["F"].astype(float), z["ON"].astype(float), z["lmp"]
    m = lmp >= 30
    Fs = F.sum(0)
    wk = np.arange(8760) // 168
    r: dict = {"year": y, "hours": int(m.sum()), "F_gw": Fs[m].mean() / 1e3, "ON_gw": ON.sum(0)[m].mean() / 1e3}
    # F by hub-LMP band: a reserve/headroom hold should persist as price rises; a node-economic backdown should shrink
    for lab, b in (("30_45", (lmp >= 30) & (lmp < 45)), ("45_60", (lmp >= 45) & (lmp < 60)),
                   ("60_100", (lmp >= 60) & (lmp < 100)), ("ge100", lmp >= 100)):
        r[f"F_share_ON_{lab}"] = float(Fs[b].sum() / ON.sum(0)[b].sum()) if b.sum() else None
        r[f"hours_{lab}"] = int(b.sum())
    # ---- (a) reserves ----
    o = orc[orc.year == y].set_index("hour").reindex(range(8760))
    rs = (o["regup"] + o["spin"]).to_numpy(float)
    r["regup_spin_gw"] = float(np.nanmean(rs[m])) / 1e3
    r["regup_spin_ramp_gw"] = float(np.nanmean((rs + o["rampup"].fillna(0).to_numpy(float))[m])) / 1e3
    r["F_over_regup_spin"] = r["F_gw"] / r["regup_spin_gw"]
    dm = lambda x: x - pd.Series(np.where(m, x, np.nan)).groupby(wk).transform("mean").to_numpy()  # noqa: E731
    Fm = np.where(m, Fs, np.nan)
    r["r_F_regupspin"] = corr(Fm, np.where(m, rs, np.nan))
    r["r_F_regupspin_wk"] = corr(dm(Fm), dm(np.where(m, rs, np.nan)))
    mc = mcp_hourly(y)
    if mc is not None:
        for c in ("RegUPService", "Spin"):
            v = np.where(m, mc[c].to_numpy(float), np.nan)
            r[f"r_F_{c}"] = corr(Fm, v)
            r[f"r_F_{c}_wk"] = corr(dm(Fm), dm(v))
            r[f"{c}_mcp_mean"] = float(np.nanmean(v))
    # ---- (b) congestion ----
    s = np.load(sd / f"stack_{y}.npz", allow_pickle=False)
    coal = np.isin(s["klass"], COAL)
    nodes = node_matrix(pd.read_parquet(nd / f"lmp_{y}.parquet"), y)
    hubN, hubS = nodes.get("SPPNORTH_HUB"), nodes.get("SPPSOUTH_HUB")
    r["hub_rt_vs_system_r"] = corr((hubN + hubS) / 2, lmp) if hubN is not None else None  # system series is not a hub average
    r["NS_spread_F_weighted"] = float(np.nansum((hubN - hubS)[m] * Fs[m]) / Fs[m].sum()) if hubN is not None else None
    r["NS_spread_inmoney"] = float(np.nanmean((hubN - hubS)[m])) if hubN is not None else None
    tot = below_mc = below25 = spread_F = spread_n = cover = 0.0
    spread_nonF, n_nonF = 0.0, 0
    per = {}
    for c, locs in PLANTS.items():
        if c not in codes:
            continue
        have = [nodes[l] for l in locs if l in nodes]
        if not have:
            continue
        nl = np.nanmean(np.vstack(have), axis=0)
        i = int(np.flatnonzero(codes == c)[0])
        f = np.where(m, F[i], 0.0)
        rows = coal & (s["codes"] == c)
        top = s["mc"][rows].max(axis=0).astype(float) if rows.any() else np.full(8760, np.nan)
        hub = np.where(np.isfinite(hubN), (hubN + hubS) / 2, lmp) if hubN is not None else lmp
        k = np.isfinite(nl)
        tot += f[k].sum()
        cover += f.sum()
        below_mc += f[k & (nl < top)].sum()
        below25 += f[k & (nl < 25)].sum()
        spread_F += ((nl - hub) * f)[k].sum()
        on = m & k & (ON[i] > 0)
        nf = on & (F[i] < 1)
        spread_nonF += (nl - hub)[nf].sum()
        n_nonF += int(nf.sum())
        per[int(c)] = {"F_mw": float(f.mean() * 8760 / max(m.sum(), 1)),
                       "share_node_below_topmc": float(f[k & (nl < top)].sum() / max(f[k].sum(), 1)),
                       "node_minus_hub_Fwtd": float(((nl - hub) * f)[k].sum() / max(f[k].sum(), 1)),
                       "node_minus_hub_onnoF": float(np.nanmean((nl - hub)[nf])) if nf.any() else None,
                       "r_Fshare_nodeLMP_wk": corr(dm(np.where(on, F[i] / np.maximum(ON[i], 1), np.nan)),
                                                  dm(np.where(on, nl, np.nan)))}
    r["mapped_share_of_F"] = cover / max(np.where(m, Fs, 0).sum(), 1)
    r["share_F_node_below_topmc"] = below_mc / max(tot, 1)
    r["share_F_node_below_25"] = below25 / max(tot, 1)
    r["node_minus_hub_Fwtd"] = spread_F / max(tot, 1)
    r["node_minus_hub_on_noF"] = spread_nonF / max(n_nonF, 1)
    r["plants"] = per
    return r


def main() -> int:
    """Run every year, print headlines, write JSON."""
    ap = argparse.ArgumentParser()
    for k in ("flat-dir", "node-dir", "stack-dir"):
        ap.add_argument(f"--{k}", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    a = ap.parse_args()
    orc = pd.read_parquet(RAW_DATA_DIR / "_validation-source/spp_rtbm_or_cleared_hourly.parquet")
    res = {}
    for y in a.years:
        r = year_tests(y, a.flat_dir, a.node_dir, a.stack_dir, orc)
        res[y] = r
        print(y, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != "plants"}, flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"lane": "SPP-91", "per_year": res}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
