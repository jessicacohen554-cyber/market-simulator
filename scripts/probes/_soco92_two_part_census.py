"""soco-92 Track B (zero LP): does a coherent TWO-PART cost construction explain
SOCO's night lambda gap, measured from unit data and never from lambda?

Owner ruling 2026-09-29 (soco-91 card, "Reopen two-part cost"): design CC
incremental cost + no-load and CT start/no-load as ONE construction for the pure-LP
P1, values ex ante from CAMPD/EIA, one config for all 7 years; greedy-bound it on
the keeper. Rule 32 ``[R-SHARD]`` (a): this never solves.

``census``  — SOCO's own CEMS record (``data/raw/campd-unit-level``, AL/GA/MS/FL),
             the soco-85 CC unit set (plants the CC derive flags ``ok``) and the
             soco-85 per-unit normalized-quadratic input-output fit (pooled
             2019-2025, ``_soco85_cc_incremental._unit_row`` construction). Per
             hour, every online CC unit's load position ``x = (gl - LSL)/(HSL -
             LSL)`` and its INCREMENTAL heat rate ``dH/dP`` at that position,
             normalized to its own measured average (``hr_gross``). Aggregated on
             soco-91's hour sets (night = low-40 % lambda at 00-05 CST, afternoon =
             top-20 % at 12-18 CST). Lambda selects the HOURS only; no value is
             read off it. CAMPD hours are local standard time: GA is shifted to
             CST (-1 h); AL/MS/FL are CST.

``greedy``  — the perfect-hindsight COMMITMENT bound. The soco-91 restack
             instrument (non-must-run fossil, ``mc_base``, ``pmax x availability``,
             keeper class-band demand, baseline-differenced, re-scored through
             ``calibration_verdict``) with the CC_REGULAR block replaced by the
             two-part pool: online capacity ``U = f_on(t) x cap`` from the
             MEASURED CC online fraction, a sunk min-load block ``LSL/HSL x U``,
             and four incremental segments above LSL priced at the measured
             pooled curve (x = 0 / 0.5 / 0.9 -> 0.81 / 1.00 / 1.21 of average,
             soco-85 §2), offline capacity withdrawn. The ONE thing a pure LP must
             supply itself — the online state — is taken from measurement, so
             this bounds what any commitment-posture construction can reach.

Usage::

    uv run python scripts/probes/_soco92_two_part_census.py census --out DIR
    uv run python scripts/probes/_soco92_two_part_census.py greedy --out DIR
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]

YEARS = tuple(range(2019, 2026))
T = 8760
CAMPD = ROOT / "data/raw/campd-unit-level"
LEGACY = ROOT / "data/raw/_processed-legacy"
STATE_SHIFT = {"GA": -1, "AL": 0, "MS": 0, "FL": 0}  # local standard -> CST
# soco-85 §2 pooled cap-weighted p50 incremental / own-average at x = 0, 0.5, 0.9
INC_X = np.array([0.0, 0.5, 0.9])
INC_R = np.array([0.81, 1.00, 1.21])
SEG_X = np.array([0.125, 0.375, 0.625, 0.875])  # four equal segments above LSL


def _load(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S85 = _load("s85", "scripts/probes/_soco85_cc_incremental.py")
S91 = _load("s91", "scripts/probes/_soco91_intraday_census.py")


def inc_ratio(x: np.ndarray) -> np.ndarray:
    """Pooled measured incremental / average ratio at load position x (linear, extrapolated)."""
    x = np.asarray(x, float)
    lo = INC_R[0] + (INC_R[1] - INC_R[0]) / 0.5 * x
    hi = INC_R[1] + (INC_R[2] - INC_R[1]) / 0.4 * (x - 0.5)
    return np.where(x <= 0.5, lo, hi)


def fits() -> pd.DataFrame:
    """Per-unit pooled quadratic I/O fit on the soco-85 CC unit set."""
    dm = S85._dm()
    units = pd.read_csv(
        LEGACY / "campd_cc_heat_rates_SOCO_units.csv", dtype={"unit_id": str}
    )
    plant = pd.read_csv(LEGACY / "campd_cc_heat_rates_SOCO.csv")
    ok = set(plant[(plant.year == 0) & (plant.flag == "ok")].plant_code)
    units = units[units.plant_code.isin(ok)]
    camp = dm.load_campd("SOCO", YEARS)
    camp["unitId"] = camp["unitId"].astype(str)
    camp = camp.merge(
        units[["plant_code", "unit_id", "hr_gross"]],
        left_on=["facilityId", "unitId"],
        right_on=["plant_code", "unit_id"],
    )
    rows = []
    for (pc, uid), g in camp.groupby(["plant_code", "unit_id"]):
        gl = g["grossLoad"].to_numpy(float)
        hi = g["heatInput"].to_numpy(float)
        if len(gl) < 500:
            continue
        lsl, hsl = np.percentile(gl, dm.LSL_PCT), np.percentile(gl, dm.HSL_PCT)
        if hsl <= lsl:
            continue
        c2, c1, c0 = np.polyfit((gl - lsl) / (hsl - lsl), hi, 2)
        rows.append(
            dict(
                plant=int(pc),
                unit=str(uid),
                base=float(g.hr_gross.iloc[0]),
                lsl=lsl,
                hsl=hsl,
                c2=c2,
                c1=c1,
                c0=c0,
            )
        )
    return pd.DataFrame(rows)


def hourly(year: int, fit: pd.DataFrame) -> dict:
    """Per-hour CC fleet state on the CST dense 8760 (Feb 29 dropped)."""
    frames = []
    for st, sh in STATE_SHIFT.items():
        p = CAMPD / f"{st}_{year}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(
            p,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "opTime",
                "grossLoad",
                "heatInput",
            ],
        )
        d["unitId"] = d["unitId"].astype(str)
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d.dropna(subset=["facilityId"]).astype({"facilityId": int})
        d = d.merge(fit, left_on=["facilityId", "unitId"], right_on=["plant", "unit"])
        if d.empty:
            continue
        ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"] + sh, unit="h")
        d = d[ts.dt.year == year].copy()
        ts = ts[ts.dt.year == year]
        leap = (ts.dt.month == 2) & (ts.dt.day == 29)
        d, ts = d[~leap.to_numpy()], ts[~leap]
        doy = ts.dt.dayofyear.to_numpy() - 1
        doy = doy - ((ts.dt.is_leap_year) & (ts.dt.month > 2)).to_numpy()
        d["t"] = doy * 24 + ts.dt.hour.to_numpy()
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    on = (d.grossLoad > 0) & (d.opTime > 0)
    d = d[on].copy()
    rng = d.hsl - d.lsl
    d["x"] = (d.grossLoad - d.lsl) / rng
    d["inc"] = (2 * d.c2 * d.x + d.c1) / rng / d.base
    d["avg"] = (d.heatInput / d.grossLoad) / d.base
    ss = d[d.opTime >= 0.95]
    g = ss.groupby("t")
    out = dict(
        inc=g.apply(lambda z: np.average(z.inc, weights=z.grossLoad)),
        avg=g.apply(lambda z: np.average(z.avg, weights=z.grossLoad)),
        x=g.apply(lambda z: np.average(z.x, weights=z.hsl)),
        low=g.apply(lambda z: z.hsl[z.x < 0.25].sum() / z.hsl.sum()),
    )
    ga = d.groupby("t")
    out["gen"] = ga.grossLoad.sum()
    out["on_hsl"] = ga.hsl.sum()
    tot = fit.hsl.sum()
    res = {k: v.reindex(range(T)).to_numpy(float) for k, v in out.items()}
    res["f_on"] = np.nan_to_num(res["on_hsl"]) / tot
    return res


def sets(year: int):
    """soco-91 hour sets on lambda (hour selection only)."""
    lam = S91.lambda_cst(year)
    q40, q80 = np.quantile(lam, [0.4, 0.8])
    hod = np.arange(T) % 24
    night = (lam <= q40) & (hod <= 5)
    aft = (lam > q80) & (hod >= 12) & (hod <= 18)
    return lam, night, aft


def census(out: Path) -> None:
    """Measured CC operating point and incremental ratio on soco-91's hour sets."""
    fit = fits()
    print(
        f"fitted units {len(fit)}, plants {fit.plant.nunique()}, HSL {fit.hsl.sum():.0f} MW"
    )
    rows = []
    for y in YEARS:
        h = hourly(y, fit)
        _lam, n, a = sets(y)
        r = dict(year=y)
        for nm, m in (("night", n), ("aft", a), ("all", np.ones(T, bool))):
            r[f"{nm}_inc"] = round(float(np.nanmean(h["inc"][m])), 3)
            r[f"{nm}_avg"] = round(float(np.nanmean(h["avg"][m])), 3)
            r[f"{nm}_x"] = round(float(np.nanmean(h["x"][m])), 3)
            r[f"{nm}_lowshare"] = round(float(np.nanmean(h["low"][m])), 3)
            r[f"{nm}_f_on"] = round(float(np.nanmean(h["f_on"][m])), 3)
            r[f"{nm}_load"] = round(
                float(np.nansum(h["gen"][m]) / max(np.nansum(h["on_hsl"][m]), 1)), 3
            )
        rows.append(r)
        print(json.dumps(r))
        np.savez(out / f"cc92_{y}.npz", **h)
    pd.DataFrame(rows).to_csv(out / "soco92_cc_night_census.csv", index=False)


def greedy(out: Path, arm: str) -> None:
    """Perfect-hindsight commitment bound through the soco-91 restack + verdict."""
    import calibration_verdict as cv
    from market_sim.config.constants import VOM

    vom_cc = float(VOM["gas_cc"]) if not isinstance(VOM["gas_cc"], dict) else 2.0
    rows = []
    art = cv.load_artifacts("2026-09-29-soco87-gas-hh-monthly")
    for y in YEARS:
        h = dict(np.load(out / f"cc92_{y}.npz"))
        f = S91.rebuild(y, out)
        band = f["band"]
        sel = np.isin(f["klass"], S91.RESTACK) & (band != "mustrun")
        cap, mc, k = (
            f["cap"][sel].astype(float),
            f["mc"][sel].astype(float),
            f["klass"][sel],
        )
        cb = pd.read_parquet(S91.SPAN / f"hourly/class_band_hourly_{y}.parquet")
        cb = cb[
            (cb["pass"] == "P1") & cb.klass.isin(S91.RESTACK) & (cb.band != "mustrun")
        ]
        dem = cb.groupby("hour").mw.sum().reindex(range(T), fill_value=0.0).to_numpy()
        g0, p0 = S91._greedy(dem, cap, mc)

        cc = k == "CC_REGULAR"
        f_on = np.clip(np.nan_to_num(h["f_on"]), 0.0, 1.0)
        mlf = 0.60  # soco-85 §2 measured LSL / HSL (cap-weighted p50)
        if arm == "posture_mload":
            # online capacity sized so the model's CC fleet runs at the MEASURED
            # hourly fleet loading (gen / online HSL): CC energy is preserved to
            # first order and only the offer SHAPE at the operating point moves.
            dcc = g0[cc].sum(0)
            ld = np.clip(np.nan_to_num(h["gen"] / h["on_hsl"], nan=1.0), mlf, 1.0)
            tot = cap[cc].sum(0)
            Uc = np.minimum(tot, dcc / ld)
            U = cap[cc] * np.divide(Uc, tot, out=np.zeros(T), where=tot > 0)[None, :]
            f_on = None
        if arm == "posture":
            # f_on is online / nameplate HSL, so it already carries outages:
            # apply it to NAMEPLATE (max over the year of pmax x availability)
            # and never exceed the hour's available capacity (no double count).
            nam = cap[cc].max(axis=1, keepdims=True)
            U = np.minimum(cap[cc], nam * f_on[None, :])
        if arm in ("posture", "posture_mload"):
            sunk = (mlf * U).sum(0)
            seg_w = (1 - mlf) / len(SEG_X)
            caps, mcs = [cap[~cc]], [mc[~cc]]
            for xm in SEG_X:
                caps.append(seg_w * U)
                mcs.append(vom_cc + inc_ratio(xm) * (mc[cc] - vom_cc))
            cap1, mc1 = np.vstack(caps), np.vstack(mcs)
            k1 = np.concatenate([k[~cc]] + [k[cc]] * len(SEG_X))
            dem1 = np.clip(dem - sunk, 0.0, None)
            g1, p1 = S91._greedy(dem1, cap1, mc1)
        elif arm == "incr_only":  # incremental segments, NO commitment state
            caps, mcs = [cap[~cc]], [mc[~cc]]
            for xm in (0.0,) + tuple(SEG_X):
                w = mlf if xm == 0.0 else (1 - mlf) / len(SEG_X)
                caps.append(w * cap[cc])
                mcs.append(vom_cc + inc_ratio(xm) * (mc[cc] - vom_cc))
            cap1, mc1 = np.vstack(caps), np.vstack(mcs)
            k1 = np.concatenate([k[~cc]] + [k[cc]] * 5)
            g1, p1 = S91._greedy(dem, cap1, mc1)
            sunk = np.zeros(T)
        dp = p1 - p0
        dcls = {c: float((g1[k1 == c].sum() - g0[k == c].sum()) / 1e6) for c in set(k)}
        if arm in ("posture", "posture_mload"):
            dcls["CC_REGULAR"] += float(sunk.sum() / 1e6)

        s = pd.read_parquet(S91.SPAN / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"].sort_values(["zone", "hour"])
        zn = sorted(s.zone.unique())
        Dz = np.vstack([s[s.zone == z].demand.to_numpy() for z in zn])
        ypay = copy.deepcopy(art["payload"]["years"][str(y)])
        yb = art["bench"].get(y, {})
        base = {
            r["key"]: r
            for r in cv.score_fuelmix(y, ypay, yb, "SOCO")
            if r["status"] != "SKIPPED"
        }
        c3a0 = cv.score_price_mean(y, ypay, yb, "SOCO")
        c3b0 = cv.score_price_shape(y, ypay, yb, "SOCO")
        for c, dv in dcls.items():
            if c in ypay["gmModel"]:
                ypay["gmModel"][c] = float(ypay["gmModel"][c]) + dv
        for zi, z in enumerate(zn):
            if z not in ypay["lmp"]:
                continue
            d, zz = Dz[zi], ypay["lmp"][z]
            zz["p"] = float(zz["p"]) + float((dp * d).sum() / d.sum())
            zz["pMon"] = [
                float(pm)
                + float(
                    (dp[S91.MONTH == i] * d[S91.MONTH == i]).sum()
                    / d[S91.MONTH == i].sum()
                )
                if pm is not None
                else None
                for i, pm in enumerate(zz["pMon"])
            ]
        arm_r = {
            r["key"]: r
            for r in cv.score_fuelmix(y, ypay, yb, "SOCO")
            if r["status"] != "SKIPPED"
        }
        c3a1 = cv.score_price_mean(y, ypay, yb, "SOCO")
        c3b1 = cv.score_price_shape(y, ypay, yb, "SOCO")
        lam, n, a = sets(y)
        r = dict(
            year=y,
            arm=arm,
            dp_night=round(float(dp[n].mean()), 2),
            dp_aft=round(float(dp[a].mean()), 2),
            dp_all=round(float(dp.mean()), 2),
            c3a=f"{c3a0['magnitude']} {c3a0['status']} -> {c3a1['magnitude']} {c3a1['status']}",
            c3b=f"{c3b0.get('model')} {c3b0['status']} -> {c3b1.get('model')} {c3b1['status']}",
            c1=" | ".join(
                f"{c} {base[c]['magnitude']}->{arm_r[c]['magnitude']} {arm_r[c]['status']}"
                for c in S91.C1_KEYS
                if c in base and c in arm_r
            ),
            dcls={c: round(v, 2) for c, v in dcls.items() if abs(v) > 0.05},
        )
        rows.append(r)
        print(json.dumps(r))
    (out / f"soco92_greedy_{arm}.json").write_text(json.dumps(rows, indent=1))


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=("census", "greedy"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--arm", default="posture", choices=("posture", "posture_mload", "incr_only")
    )
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.cmd == "census":
        census(args.out)
    else:
        greedy(args.out, args.arm)


if __name__ == "__main__":
    main()
