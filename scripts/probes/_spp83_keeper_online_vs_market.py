"""SPP-83 (zero LP): does the keeper clear on capacity SPP kept offline? (FINDING-spp-82 §7.1).

Record: ``docs/handoffs/FINDING-spp-83-keeper-clears-on-offline-capacity-2026-09-26.md``.

On SPP-82's exact sample hours (``_spp82_offered_not_setting.sample_days``: SPP-80's non-scarcity
RT upper tercile, ex-Feb, the ``--days`` days per month with most tercile hours) this measures the
keeper ``results/calibration/rspp_span``'s fleet, rebuilt ``fleet_only`` exactly as
``_spp81b_upper_tercile_marginal_unit.rebuild`` does (no LP), against SPP's published hourly
ONLINE capacity (``hourly-generation-capacity-by-fuel-type``, same parser as SPP-82):

* ``K_av``      — keeper available MW (``pmax x availability``), every fleet row (thermal, hydro,
  nuclear, ...; wind and solar are LP decision variables, not fleet rows, and C_th excludes
  them too);
* ``K10``       — of which offered (``mc_base``) in ``[lo, 500)``;
* ``K10_below`` — of which at or below the row's own zone P1 price (SPP-82's ``B10`` analogue);
* ``K_below``   — every available MW at or below the row's own zone P1 price;
* ``K_gen``     — keeper P1 generation of every non-wind/solar class (``class_hourly``).

The LP has no commitment state, so every available MW is "online" to it: ``K_av - C_th`` is
the capacity the keeper treats as dispatchable that SPP's market had offline.

Solves nothing. Usage:
``python scripts/probes/_spp83_keeper_online_vs_market.py --cache <dir> --zdir <dir> [--out <json>]``
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
from scripts.probes._spp81_residual_upper_tercile import frame, upper  # noqa: E402
from scripts.probes._spp81b_upper_tercile_marginal_unit import BUNDLE, rebuild  # noqa: E402
from scripts.probes._spp82_offered_not_setting import (
    gencap_hourly,
    genmix_th,
    sample_days,
)  # noqa: E402

FINDING = "docs/handoffs/FINDING-spp-83-keeper-clears-on-offline-capacity-2026-09-26.md"
PRICE_CAP = 500.0  # SPP-81b / SPP-82 stack ceiling, identical filter
GAS = ("gas_cc", "gas_ct", "gas_st")
VER_CLASSES = (
    "WIND",
    "SOLAR",
    "STORAGE",
    "BATTERY",
)  # class_hourly tokens excluded from K_gen


def year_frame(
    y: int, lmp, comp, n_days: int, lo: float, cache: Path, zdir: Path
) -> tuple[pd.DataFrame, dict]:
    """Per sampled hour: keeper quantities, SPP online capacity and generation."""
    ns = upper(frame(y, lmp, comp))
    ns = ns[~ns.scar].copy()
    days = set(sample_days(ns, n_days))
    H = np.array(sorted(h for h in ns.index if h // 24 in days))
    s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    P = s.pivot(index="hour", columns="zone", values="price")
    fl = rebuild(y, cache, False)
    r = pd.DataFrame(fl["rows"])
    zn = r.zone.to_numpy()
    cls = r.plant_group.replace("", np.nan).fillna(r.fuel_type).to_numpy()
    mc, av = fl["mc"][:, H], fl["avail"][:, H]
    pz = np.vstack(
        [P[z].reindex(H).to_numpy() if z in P else np.full(H.size, np.nan) for z in zn]
    )
    band = (mc >= lo) & (mc < PRICE_CAP)
    below = mc <= pz + 1e-6
    gas = np.isin(r.fuel_type.to_numpy(), GAS)
    coal = np.array([str(c).startswith("COAL") for c in cls])
    mecv = ns.mec.reindex(H).to_numpy()
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{y}.parquet")
    ch = ch[(ch["pass"] == "P1") & ~ch.klass.str.upper().str.startswith(VER_CLASSES)]
    kgen = ch.groupby("hour").mw.sum().reindex(H).to_numpy()
    Q = pd.DataFrame(
        {
            "K_av": av.sum(0),
            "K10": (av * band).sum(0),
            "K10_below": (av * band * below).sum(0),
            "K_below": (av * below).sum(0),
            "K_gen": kgen,
            "K_ge_price": (av * ~below).sum(0),
            "K_gas": av[gas].sum(0),
            "K_coal": av[coal].sum(0),
            "K10_below_mec": (av * band * (mc <= mecv + 1e-6)).sum(0),
        },
        index=H,
    )
    Q = Q.join(gencap_hourly(y, zdir)).join(genmix_th(y)).join(ns[["mec", "m"]])
    Q = Q.join(reclear(mc, av, gas, Q, lo))
    by_cls = pd.DataFrame(
        {"cls": cls, "av": av.mean(1), "av10b": (av * band * below).mean(1)}
    )
    by_cls["cls"] = by_cls.cls.map(lambda k: "COAL" if str(k).startswith("COAL") else k)
    info = {
        "classes_gw": (by_cls.groupby("cls")[["av", "av10b"]].sum() / 1e3)
        .round(3)
        .to_dict()
    }
    return Q, info


def merit_price(c: np.ndarray, w: np.ndarray, q: float) -> float:
    """System merit price: the offer of the MW that serves quantity ``q`` (``nan`` if short)."""
    o = np.argsort(c, kind="stable")
    cw = np.cumsum(w[o])
    j = np.searchsorted(cw, q - 1e-6)
    return float(c[o][j]) if j < o.size else np.nan


def reclear(
    mc: np.ndarray, av: np.ndarray, gas_rows: np.ndarray, Q: pd.DataFrame, lo: float
) -> pd.DataFrame:
    """Zero-LP bound: re-clear the keeper's own stack at its own thermal generation with the
    gas excess over SPP's online gas (``max(0, K_gas - C_gas)``) removed from its >= ``lo`` gas
    rows, CHEAPEST first (SPP-82's reading: the offline MW are cheap relative to MEC) or
    DEAREST first (the other bound). System-wide, one zone, hourly, no ramps: an instrument,
    not a solve. ``p_full`` is the same instrument on the unmodified stack (its fidelity check
    against the keeper's own P1 price)."""
    out = []
    for j, t in enumerate(Q.index):
        c, w, q = mc[:, j], av[:, j].astype(float), float(Q.K_gen.iat[j])
        ex = (
            max(0.0, float(Q.K_gas.iat[j] - Q.C_gas.iat[j]))
            if np.isfinite(Q.C_gas.iat[j])
            else np.nan
        )
        rec = {"p_full": merit_price(c, w, q), "gas_excess": ex}
        for lab, sgn in (("p_rm_cheap", 1.0), ("p_rm_dear", -1.0)):
            if not np.isfinite(ex):
                rec[lab] = np.nan
                continue
            w2 = w.copy()
            g = np.where(gas_rows & (c >= lo) & (c < PRICE_CAP) & (w > 0))[0]
            g = g[np.argsort(sgn * c[g], kind="stable")]
            left = ex
            for i in g:
                cut = min(w2[i], left)
                w2[i] -= cut
                left -= cut
                if left <= 0:
                    break
            rec[lab] = merit_price(c, w2, q)
        out.append(rec)
    return pd.DataFrame(out, index=Q.index)


def summarise(y: int, Q: pd.DataFrame) -> dict:
    """Per-year means over the sampled hours (GW) and the keeper-minus-market differences."""
    k = 1e3
    g = lambda c: float(Q[c].mean() / k) if c in Q and Q[c].notna().any() else None  # noqa: E731
    out = {
        "year": y,
        "n_hours": int(len(Q)),
        "n_hours_with_Cth": int(Q.C_th.notna().sum()) if "C_th" in Q else 0,
        "rt_mec": float(Q.mec.mean()),
        "model_p1": float(Q.m.mean()),
    }
    for c in (
        "K_av",
        "K10",
        "K10_below",
        "K_below",
        "K_ge_price",
        "K_gen",
        "C_th",
        "G_th",
        "K_gas",
        "C_gas",
        "K_coal",
        "C_coal",
        "K10_below_mec",
        "gas_excess",
    ):
        out[f"{c}_gw"] = g(c)
    if out["C_th_gw"] is not None:
        out["K_av_minus_Cth_gw"] = float((Q.K_av - Q.C_th).mean() / k)
        out["K10_below_minus_Cth_gw"] = float(
            (Q.K10_below - Q.C_th).clip(lower=0).mean() / k
        )
        out["K_below_minus_Cth_gw"] = float((Q.K_below - Q.C_th).mean() / k)
        out["K_hdr_gw"] = float((Q.K_av - Q.K_gen).mean() / k)
        out["spp_hdr_gw"] = float((Q.C_th - Q.G_th).mean() / k)
        out["K_gas_minus_Cgas_gw"] = float((Q.K_gas - Q.C_gas).mean() / k)
        out["K_coal_minus_Ccoal_gw"] = float((Q.K_coal - Q.C_coal).mean() / k)
        out["K_nongas_minus_Cnongas_gw"] = float(
            ((Q.K_av - Q.K_gas) - (Q.C_th - Q.C_gas)).mean() / k
        )
        for c in ("p_full", "p_rm_cheap", "p_rm_dear"):
            out[c] = float(Q[c].mean())
            out[f"{c}_n_short"] = int(Q[c].isna().sum())
        out["dp_rm_cheap"] = float((Q.p_rm_cheap - Q.p_full).mean())
        out["dp_rm_dear"] = float((Q.p_rm_dear - Q.p_full).mean())
    return out


def main() -> None:
    """Keeper-side split for the requested years; prints and writes JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years", nargs="+", type=int, default=[2019, 2020, 2021, 2022, 2023, 2024]
    )
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--lo", type=float, default=10.0)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--zdir", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    a.cache.mkdir(parents=True, exist_ok=True)
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    comp = pd.read_parquet(
        RAW_DATA_DIR
        / "_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet"
    )
    rows, infos = [], {}
    for y in a.years:
        Q, info = year_frame(y, lmp, comp, a.days, a.lo, a.cache, a.zdir)
        rows.append(summarise(y, Q))
        infos[y] = info
        print(f"{y} done ({len(Q)} hours)", flush=True)
    T = pd.DataFrame(rows).set_index("year")
    pd.set_option("display.width", 250)
    print(T.T.round(3).to_string())
    for y, i in infos.items():
        print(y, pd.DataFrame(i["classes_gw"]).to_string())
    if a.out:
        a.out.write_text(
            json.dumps(
                {
                    "lane": "SPP-83",
                    "date": "2026-09-26",
                    "probe": __file__.split("market-simulator/")[-1],
                    "finding": FINDING,
                    "per_year": rows,
                    "by_class": {str(k): v for k, v in infos.items()},
                },
                indent=1,
                default=float,
            )
        )


if __name__ == "__main__":
    main()
