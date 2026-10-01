"""SPP-90 (ZERO LP): why does SPP's coal fleet deliver only ~0.83-0.92 of the keeper's available MW
in the money?

Record: ``docs/records/spp/FINDING-spp-90-coal-inmoney-conduct-2026-09-27.md``.

Reads the SPP-89 stage-1 stacks (``_spp89_stack_dump.py``: keeper ``spp86_arm_span`` rebuilt
``fleet_only``, no LP) and CAMPD CEMS unit-hourly data. For every keeper coal plant (COAL_PRB +
COAL_LIGNITE rows) and every hour it forms, on the GROSS basis (the keeper's coal basis, SPP-87):

* ``K``   keeper available MW, ``sum(pmax x availability)`` over the plant's coal rows;
* ``A``   CEMS gross MW of the plant's coal units;
* ``ON``  the plant's on-line capability: sum over units with ``opTime > 0`` of the unit's
          demonstrated capability ``D_u`` (per-year p99 of its hourly gross load when fully on);
* ``OFF`` ``sum(D_u)`` over units with ``opTime == 0``.

``K - A`` is split exactly into
``(K - sum D_u)`` [keeper rating vs demonstrated]  +  ``OFF`` [units offline, candidate 3]  +
``(ON - A)`` [on line below demonstrated capability, candidates 1/2/4], and ``ON - A`` is further
split by hour context: first 12 h after a unit start, within 6 h of an actual-LMP < $25 hour
(ramp, candidate 4), and SUSTAINED (neither), the latter by season (candidate 2, ambient).
OFF is split by whether the keeper already removes that unit's MW (keeper K below its rating).

All in hours with the ACTUAL system RT LMP >= $60 and >= $30. Solves nothing.

Usage: ``python scripts/probes/_spp90_coal_inmoney_conduct.py --stack-dir <dir> --out <json>``
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.probes._spp72_demand_tightness import CST_OFFSET_H, model_clock_index  # noqa: E402
from scripts.probes._spp73_commitment_reach import MST_STATES, SPP_STATES  # noqa: E402

YEARS = range(2019, 2026)
COAL = ("COAL_PRB", "COAL_LIGNITE")
START_H = 12      # hours after a unit start counted as start-up ramp
LOWP_H = 6        # hours after an actual-LMP < LOWP hour counted as post-trough ramp
LOWP = 25.0
SUMMER = (6, 7, 8, 9)
BUNDLE = REPO / "results/calibration/spp86_arm_span"


def cems_units(y: int, codes: set[int]) -> pd.DataFrame:
    """CEMS coal unit-hours for the keeper's coal plants, on the model clock (slot 0..8759)."""
    clock = model_clock_index(y)
    slot = pd.Series(np.arange(8760), index=(clock - pd.Timedelta(hours=CST_OFFSET_H)).tz_localize(None))
    fr = []
    for st in SPP_STATES:
        p = RAW_DATA_DIR / f"campd-unit-level/{st}_{y}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["facilityId", "unitId", "date", "hour", "opTime", "grossLoad",
                                        "heatInput", "primaryFuelInfo"])
        d["fid"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d["fid"].isin(codes) & d["primaryFuelInfo"].astype(str).str.lower().str.contains("coal")]
        if d.empty:
            continue
        ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
        if st in MST_STATES:
            ts = ts + pd.Timedelta(hours=1)
        s = slot.reindex(ts.to_numpy()).to_numpy()
        ok = np.isfinite(s)
        d = d[ok].assign(t=s[ok].astype(int))
        fr.append(d[["fid", "unitId", "t", "opTime", "grossLoad", "heatInput"]])
    d = pd.concat(fr)
    d["u"] = d["fid"].astype(int).astype(str) + ":" + d["unitId"].astype(str)
    return d


def year_block(y: int, sd: Path, lmp_all: pd.DataFrame) -> dict:
    """Decompose K - A for one year."""
    z = np.load(sd / f"stack_{y}.npz", allow_pickle=False)
    kl, codes, cap, pmax = z["klass"], z["codes"], z["cap"].astype(float), z["pmax"]
    r = np.isin(kl, COAL)
    pc = sorted(set(codes[r].tolist()))
    K = {c: cap[r & (codes == c)].sum(axis=0) for c in pc}
    Kp = {c: float(pmax[r & (codes == c)].sum()) for c in pc}
    T = cap.shape[1]
    lmp = lmp_all[lmp_all.year == y].set_index("hour")["rt"].reindex(range(T)).to_numpy(float)
    d = cems_units(y, set(pc))
    units = sorted(d["u"].unique())
    ui = {u: i for i, u in enumerate(units)}
    n = len(units)
    G = np.zeros((n, T))
    ON = np.zeros((n, T), bool)
    FULL = np.zeros((n, T), bool)
    iu = d["u"].map(ui).to_numpy()
    tt = d["t"].to_numpy()
    G[iu, tt] = d["grossLoad"].fillna(0).to_numpy()
    op = d["opTime"].fillna(0).to_numpy()
    ON[iu, tt] = op > 0
    FULL[iu, tt] = op >= 0.999
    # heat-input-only units (grossLoad blank): unmetered, reported and excluded from D
    nogross = d.groupby("u")["grossLoad"].apply(lambda s: s.notna().sum() == 0)
    ufid = np.array([int(u.split(":")[0]) for u in units])
    D = np.array([np.percentile(G[i][FULL[i] & (G[i] > 0)], 99) if (FULL[i] & (G[i] > 0)).any() else 0.0
                  for i in range(n)])
    Dmax = G.max(axis=1)
    # hour context per unit
    start = ON & ~np.concatenate([np.zeros((n, 1), bool), ON[:, :-1]], axis=1)
    since = np.full((n, T), 10_000)
    last = np.full(n, -10_000)
    for t in range(T):  # per-unit event clock (probe, not LP construction)
        last = np.where(start[:, t], t, last)
        since[:, t] = t - last
    lowp = pd.Series(lmp < LOWP).rolling(LOWP_H, min_periods=1).max().shift(1).fillna(0).to_numpy(bool)
    month = pd.date_range(f"{y}-01-01", periods=T, freq="h").month.to_numpy()
    summer = np.isin(month, SUMMER)
    out = {"year": y, "plants": {}, "buckets": {}}
    Ksum = np.sum([K[c] for c in pc], axis=0)
    for lab, m in (("ge60", lmp >= 60), ("ge30", lmp >= 30), ("30_60", (lmp >= 30) & (lmp < 60))):
        h = int(m.sum())
        onsh = (np.where(ON, D[:, None], 0) - G).clip(min=0)  # on line below D (clip: rare >p99 hours)
        ov = (G - np.where(ON, D[:, None], 0)).clip(min=0)
        st_ = ON & (since < START_H)
        rp = ON & ~st_ & lowp[None, :]
        sus = ON & ~st_ & ~lowp[None, :]
        offmw = np.where(~ON, D[:, None], 0.0)
        b = {
            "hours": h,
            "K_gw": Ksum[m].mean() / 1e3,
            "Kpmax_gw": sum(Kp.values()) / 1e3,
            "sumD_gw": D.sum() / 1e3,
            "A_gw": G[:, m].sum(axis=0).mean() / 1e3,
            "ON_gw": np.where(ON, D[:, None], 0)[:, m].sum(axis=0).mean() / 1e3,
            "OFF_gw": offmw[:, m].sum(axis=0).mean() / 1e3,
            "onshort_gw": onsh[:, m].sum(axis=0).mean() / 1e3,
            "over_D_gw": ov[:, m].sum(axis=0).mean() / 1e3,
            "onshort_start_gw": np.where(st_, onsh, 0)[:, m].sum(axis=0).mean() / 1e3,
            "onshort_ramp_gw": np.where(rp, onsh, 0)[:, m].sum(axis=0).mean() / 1e3,
            "onshort_sustained_gw": np.where(sus, onsh, 0)[:, m].sum(axis=0).mean() / 1e3,
            "onshort_sustained_summer_gw": np.where(sus & summer[None, :], onsh, 0)[:, m & summer].sum(axis=0).mean() / 1e3
            if (m & summer).any() else None,
            "onshort_sustained_nonsummer_gw": np.where(sus & ~summer[None, :], onsh, 0)[:, m & ~summer].sum(axis=0).mean() / 1e3
            if (m & ~summer).any() else None,
            "ON_summer_gw": np.where(ON, D[:, None], 0)[:, m & summer].sum(axis=0).mean() / 1e3 if (m & summer).any() else None,
            "ON_nonsummer_gw": np.where(ON, D[:, None], 0)[:, m & ~summer].sum(axis=0).mean() / 1e3 if (m & ~summer).any() else None,
            "sus_loading": float(G[:, m][sus[:, m]].sum() / np.where(sus, D[:, None], 0)[:, m].sum()),
            "sus_loading_p50_unit": None,
        }
        # sustained loading per unit (G/D in sustained in-money hours), capacity-weighted median
        lu = []
        for i in range(n):
            s = sus[i] & m
            if s.sum() >= 50 and D[i] > 0:
                lu.append((float(np.median(G[i][s] / D[i])), D[i]))
        if lu:
            v, w = np.array(lu).T
            o = np.argsort(v)
            b["sus_loading_p50_unit"] = float(v[o][np.searchsorted(np.cumsum(w[o]), w.sum() / 2)])
        b["share_A_over_K"] = b["A_gw"] / b["K_gw"]
        out["buckets"][lab] = b
    # ---- second level: weekly demonstrated capability (candidate 1 vs dispatch) ----
    wk = (np.arange(T) // 168)
    inm = lmp >= 30
    W = np.zeros((n, T))
    for w in np.unique(wk):
        s = wk == w
        sel = ON[:, s] & inm[None, s]
        g = np.where(sel, G[:, s], -1.0)
        cnt = sel.sum(axis=1)
        cap_w = np.where(cnt >= 10, g.max(axis=1), D)   # too few in-money on-line hours: fall back to D
        W[:, s] = np.minimum(cap_w, D)[:, None]
    dG = np.diff(G, axis=1, prepend=G[:, :1])
    Ksum_p = {c: K[c] for c in pc}
    for lab, m in (("ge60", lmp >= 60), ("ge30", lmp >= 30)):
        b = out["buckets"][lab]
        onsh = np.where(ON, (D[:, None] - G).clip(min=0), 0.0)
        derate = np.where(ON, (D[:, None] - W).clip(min=0), 0.0)
        derate = np.minimum(derate, onsh)
        below_w = onsh - derate
        b["onshort_weekcap_derate_gw"] = derate[:, m].sum(axis=0).mean() / 1e3
        b["onshort_below_weekcap_gw"] = below_w[:, m].sum(axis=0).mean() / 1e3
        rising = ON & (dG > 0.05 * D[:, None])
        flat_low = ON & (np.abs(dG) <= 0.02 * D[:, None])
        b["below_weekcap_rising_gw"] = np.where(rising, below_w, 0)[:, m].sum(axis=0).mean() / 1e3
        b["below_weekcap_flat_gw"] = np.where(flat_low, below_w, 0)[:, m].sum(axis=0).mean() / 1e3
        # plant level: K vs weekly on-line capability Cw and A
        pos = neg = 0.0
        offpos = 0.0
        for c in pc:
            ix = np.flatnonzero(ufid == c)
            Cw = np.where(ON[ix], W[ix], 0).sum(axis=0)
            Dall = np.where(ON[ix], D[ix][:, None], 0).sum(axis=0)
            d_ = Ksum_p[c] - Cw
            pos += np.clip(d_, 0, None)[m].mean()
            neg += np.clip(d_, None, 0)[m].mean()
            offpos += np.clip(Ksum_p[c] - Dall, 0, None)[m].mean()
        b["K_minus_Cw_pos_gw"] = pos / 1e3   # keeper offers MW above the week's demonstrated on-line capability
        b["K_minus_Cw_neg_gw"] = neg / 1e3   # keeper removes MW the fleet demonstrably had on line
        b["K_minus_ONd_pos_gw"] = offpos / 1e3  # keeper available above on-line units' D (offline units kept)
        b["Cw_gw"] = np.where(ON, W, 0)[:, m].sum(axis=0).mean() / 1e3
    # ---- keeper P1 coal (gross basis, SPP-87) against K and A, per actual-LMP bucket ----
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[(ch["pass"] == "P1") & ch["klass"].astype(str).isin(COAL)]
    M = ch.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy()
    for lab, m in (("ge60", lmp >= 60), ("ge30", lmp >= 30), ("30_60", (lmp >= 30) & (lmp < 60))):
        b = out["buckets"][lab]
        b["M_gw"] = M[m].mean() / 1e3
        b["share_M_over_K"] = b["M_gw"] / b["K_gw"]
        b["M_minus_A_twh"] = (b["M_gw"] - b["A_gw"]) * int(m.sum()) / 1e3
    # ---- measured up-ramp capability (candidate 4): per unit, hourly up-steps while fully on ----
    both = FULL[:, 1:] & FULL[:, :-1]
    ups, wts = [], []
    for i in range(n):
        if both[i].sum() >= 200 and D[i] > 0:
            ups.append(np.percentile(np.diff(G[i])[both[i]] / D[i], 99))
            wts.append(D[i])
    out["ramp_up_p99_capwtd"] = float(np.average(ups, weights=wts)) if ups else None
    # per plant, >= $60 hours
    m = lmp >= 60
    for c in pc:
        ix = np.flatnonzero(ufid == c)
        Ac = G[ix][:, m].sum(axis=0)
        ONc = np.where(ON[ix], D[ix][:, None], 0)[:, m].sum(axis=0)
        out["plants"][c] = {
            "Kpmax": Kp[c], "sumD": float(D[ix].sum()), "sumDmax": float(Dmax[ix].sum()),
            "units": len(ix), "nogross_units": int(sum(bool(nogross.get(units[i], False)) for i in ix)),
            "K_ge60": float(K[c][m].mean()), "A_ge60": float(Ac.mean()), "ON_ge60": float(ONc.mean()),
            "K_zero_share_ge60": float((K[c][m] < 1).mean()),
            "all_off_share_ge60": float((ONc < 1).mean()),
        }
    return out


def main() -> int:
    """Run every year, print the decomposition, write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    a = ap.parse_args()
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    res = {}
    for y in a.years:
        r = year_block(y, a.stack_dir, lmp)
        res[y] = r
        for lab, b in r["buckets"].items():
            print(y, lab, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in b.items()}, flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
