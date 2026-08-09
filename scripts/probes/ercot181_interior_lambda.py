"""ercot-181 §1: the interior price-at-BP clustering instrument (I-1/I-2/I-3).

Pre-registered in PRECOMMIT-ercot181-quantity-position-2026-08-09.md §1, run
AFTER the §5 M-0/M-1 geometric adjudication (its own ordering clause). NO LP,
NO mechanism, NO ScenarioConfig field, NO scalar.

DIAGNOSTIC LICENSE (rule 13's diagnostic-probe clause): Base Points are
realized dispatch outcomes and I-2's hour selection reads the committed
ercot-180 residual-selected top-100 list, so this probe is a DIAGNOSTIC in
its entirety — its output is barred from parameter identification and from
every mechanism input.

I-1 — per 5-minute interval of the residual-blind population (2023 hours with
within-year net-load rank > 0.97, ``_netload_pct`` — the artifacts' own
conditioner): an INTERIOR resource is ON-status merchant gas (CC/CT) with
LDL < BP < HDL (strictly inside the ramp-feasible envelope) and
first-SCED2-step MW < BP < min(top-step MW, HASL) (strictly inside its own
submitted curve). SCED optimality prices every such resource's step at BP at
the system lambda, so their HCAP-clipped price-at-BP values should cluster:
lambda-hat = median, dispersion = IQR. Bars (precommit §1, fixed ex ante):
I-B1 coverage >= 60 % of population intervals with >= 3 interior resources;
I-B2 median IQR/lambda-hat <= 0.25; I-B3 median hourly
|lambda-hat - RT_actual| / RT_actual <= 0.25.

I-2 — the ercot-180 top-100 position statistics re-run with the marginal
resource = the interior resource whose price-at-BP is nearest lambda-hat
(replacing the saturating max-price-at-BP envelope); q_mod / p_mod / gap are
read from the COMMITTED ercot180_marginal_position.json per-hour records, so
the two instruments differ only in the marginal identification.

I-3 — the quantity-position wedge from the corpus side: per covered interval,
the ON-fleet loading distribution (BP / curve-top) and the
cheap-but-unaccepted MW mass (offered below lambda-hat, above BP, within
HASL) that reality's 5-minute ramp-feasible SCED left undispatched.

Output: results/calibration/ercot181_interior_lambda.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    _MONTH_START_HOUR,
    _netload_pct,
)
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _SCED2_MW,
    _SCED2_PR,
    _STD_TZ,
    CLASS_OF_RESTYPE,
    _delivery_year_rows,
    _sced_source_files,
)

OUT = REPO / "results/calibration/ercot181_interior_lambda.json"
E180 = REPO / "results/calibration/ercot180_marginal_position.json"
YEAR = 2023
RANK_BAR = 0.97  # the frozen top-bin edge (residual-blind population)
# I-1 admissibility bars — instrument constants (precommit §1, never swept)
IB1_COVERAGE = 0.60
IB1_MIN_INTERIOR = 3
IB2_REL_IQR = 0.25
IB3_REL_ERR = 0.25

_COLS = [
    "SCED Time Stamp",
    "Resource Type",
    "Telemetered Resource Status",
    "HASL",
    "HDL",
    "LDL",
    "Base Point",
] + [c for pair in zip(_SCED2_MW, _SCED2_PR) for c in pair]


def _stream(hours: set[int]) -> pd.DataFrame:
    """Per (interval, ON merchant-gas resource): curve reads + interior flag."""
    rows: list[pd.DataFrame] = []
    for path in _sced_source_files(YEAR):
        df = pd.read_parquet(path, columns=_COLS)
        df = _delivery_year_rows(df, YEAR)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.str.startswith("ON")].copy()
        if df.empty:
            continue
        ts = pd.to_datetime(df["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert(_STD_TZ)
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        df = df.loc[np.asarray(ok)].copy()
        if df.empty:
            continue
        hoy = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        keep = np.isin(hoy, list(hours))
        if not keep.any():
            continue
        df = df.loc[keep].copy()
        hoy = hoy[keep]
        for c in ["HASL", "HDL", "LDL", "Base Point"] + _SCED2_MW + _SCED2_PR:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        MW = df[_SCED2_MW].to_numpy(float)
        PR = np.minimum(df[_SCED2_PR].to_numpy(float), HCAP_USD_MWH)
        valid = np.isfinite(MW) & np.isfinite(PR)
        n = len(df)
        top = np.where(valid, MW, -np.inf).max(axis=1)
        first_mw = np.where(valid, MW, np.inf).min(axis=1)
        bp = df["Base Point"].to_numpy(float)
        hasl = df["HASL"].to_numpy(float)
        hdl = df["HDL"].to_numpy(float)
        ldl = df["LDL"].to_numpy(float)

        def _price_at(q_mw: np.ndarray) -> np.ndarray:
            m = np.where(valid, MW, np.inf)
            hit = m >= q_mw[:, None]
            idx = np.argmax(hit, axis=1)
            p = PR[np.arange(n), idx]
            return np.where(hit.any(axis=1), p, np.nan)

        def _mw_below(price: np.ndarray) -> np.ndarray:
            """Largest step MW whose price < the interval's lambda-hat."""
            below = valid & (PR < price[:, None])
            m = np.where(below, MW, -np.inf).max(axis=1)
            return np.where(np.isfinite(m), m, 0.0)

        p_bp = _price_at(bp)
        on_curve = (
            np.isfinite(bp)
            & np.isfinite(top)
            & (bp > 0)
            & np.isfinite(p_bp)
        )
        interior = (
            on_curve
            & np.isfinite(hdl)
            & np.isfinite(ldl)
            & (bp > ldl)
            & (bp < hdl)
            & np.isfinite(first_mw)
            & (bp > first_mw)
            & (bp < np.minimum(top, np.where(np.isfinite(hasl), hasl, np.inf)))
        )
        rows.append(
            pd.DataFrame(
                {
                    "hoy": hoy,
                    "ts": df["SCED Time Stamp"].to_numpy(),
                    "cls": df["Resource Type"].map(CLASS_OF_RESTYPE).to_numpy(),
                    "p_bp": p_bp,
                    "pos": np.where(top > 0, bp / top, np.nan),
                    "top": top,
                    "bp": bp,
                    "hasl": hasl,
                    "interior": interior,
                    "on_curve": on_curve,
                    # per-row curve kept for I-2 curve reads + I-3 mass
                    "mw_row": list(MW),
                    "pr_row": list(PR),
                    "valid_row": list(valid),
                }
            )
        )
    return (
        pd.concat(rows, ignore_index=True)
        if rows
        else pd.DataFrame()
    )


def _mw_at_price_below(r: pd.Series, price: float) -> float:
    """Largest step MW of row ``r`` priced strictly below ``price``."""
    mwv = np.where(r["valid_row"] & (r["pr_row"] < price), r["mw_row"], -np.inf)
    m = mwv.max()
    return float(m) if np.isfinite(m) else 0.0


def _price_at_frac(r: pd.Series, frac_mw: float) -> float:
    mwv = np.where(r["valid_row"], r["mw_row"], np.inf)
    hit = mwv >= frac_mw
    if not hit.any():
        return float("nan")
    return float(r["pr_row"][int(np.argmax(hit))])


def main() -> int:
    pct = _netload_pct(YEAR)
    pop_hours = {int(h) for h in np.flatnonzero(pct > RANK_BAR)}
    e180 = json.loads(E180.read_text())
    top100 = {int(r["hour"]): r for r in e180["per_hour"]}
    all_hours = pop_hours | set(top100)
    print(
        f"population: {len(pop_hours)} rank>{RANK_BAR} hours; "
        f"top-100 union adds {len(all_hours) - len(pop_hours)}"
    )
    corpus = _stream(all_hours)
    print(f"streamed {len(corpus)} ON gas resource-intervals")

    # ---------------- I-1: interval clustering + bars ----------------
    iv_recs: list[dict] = []
    for (hoy, ts), sub in corpus.groupby(["hoy", "ts"], sort=False):
        ints = sub[sub["interior"] & np.isfinite(sub["p_bp"])]
        rec = {
            "hoy": int(hoy),
            "ts": str(ts),
            "n_on": int(len(sub)),
            "n_interior": int(len(ints)),
        }
        if len(ints):
            v = ints["p_bp"].to_numpy(float)
            rec["lam"] = float(np.median(v))
            rec["iqr"] = float(np.percentile(v, 75) - np.percentile(v, 25))
        iv_recs.append(rec)
    iv = pd.DataFrame(iv_recs)
    pop_iv = iv[iv["hoy"].isin(pop_hours)]
    covered = pop_iv[pop_iv["n_interior"] >= IB1_MIN_INTERIOR]
    ib1 = float(len(covered) / len(pop_iv)) if len(pop_iv) else 0.0
    rel_iqr = (covered["iqr"] / covered["lam"]).replace(
        [np.inf, -np.inf], np.nan
    )
    ib2 = float(np.nanmedian(rel_iqr)) if len(covered) else None

    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    act = act[act["year"] == YEAR].set_index("hour")["rt"]
    lam_hour = covered.groupby("hoy")["lam"].median()
    both = pd.DataFrame({"lam": lam_hour, "rt": act.reindex(lam_hour.index)}).dropna()
    ib3 = (
        float(np.median((both["lam"] - both["rt"]).abs() / both["rt"].abs()))
        if len(both)
        else None
    )
    i1 = {
        "population_hours": len(pop_hours),
        "population_intervals": int(len(pop_iv)),
        "IB1_coverage": ib1,
        "IB1_pass": ib1 >= IB1_COVERAGE,
        "IB2_median_rel_iqr": ib2,
        "IB2_pass": (ib2 is not None and ib2 <= IB2_REL_IQR),
        "IB3_median_rel_err_vs_rt": ib3,
        "IB3_hours_scored": int(len(both)),
        "IB3_pass": (ib3 is not None and ib3 <= IB3_REL_ERR),
        "lambda_hour_median_usd": float(both["lam"].median()) if len(both) else None,
        "rt_hour_median_usd": float(both["rt"].median()) if len(both) else None,
    }
    i1["INSTRUMENT_ADMISSIBLE"] = bool(
        i1["IB1_pass"] and i1["IB2_pass"] and i1["IB3_pass"]
    )

    # ---------------- I-2: sharpened top-100 position statistics ----------------
    i2_hours: list[dict] = []
    for h, r180 in sorted(top100.items()):
        sub = corpus[(corpus["hoy"] == h) & corpus["interior"]]
        q_mod = r180.get("q_mod")
        rec = {
            "hour": h,
            "rt": r180["rt"],
            "p_mod": r180["p_mod"],
            "q_mod": q_mod,
            "gap": r180.get("gap"),
        }
        if len(sub) and q_mod is not None:
            picks = []
            for _ts, ivs in sub.groupby("ts", sort=False):
                v = ivs["p_bp"].to_numpy(float)
                lam = np.median(v)
                k = int(np.argmin(np.abs(v - lam)))
                r = ivs.iloc[k]
                picks.append(
                    {
                        "lam": float(lam),
                        "p_marg": float(r["p_bp"]),
                        "q_act": float(r["pos"]),
                        "cls": str(r["cls"]),
                        "p_at_qmod": _price_at_frac(r, q_mod * r["top"]),
                    }
                )
            if picks:
                pk = pd.DataFrame(picks)
                rec.update(
                    {
                        "n_intervals": int(len(pk)),
                        "lam_med": float(pk["lam"].median()),
                        "p_marg_med": float(pk["p_marg"].median()),
                        "q_act_med": float(pk["q_act"].median()),
                        "cls_marg_mode": pk["cls"].mode().iat[0],
                        "p_curve_at_qmod_med": float(
                            np.nanmedian(pk["p_at_qmod"].to_numpy(float))
                        ),
                        "position_wedge": float(pk["q_act"].median()) - q_mod,
                    }
                )
                gap = rec.get("gap")
                if gap:
                    pos_leg = rec["p_marg_med"] - rec["p_curve_at_qmod_med"]
                    rec["share_explained_by_position"] = (
                        float(pos_leg / gap) if np.isfinite(pos_leg) else None
                    )
        i2_hours.append(rec)
    sc = [
        r
        for r in i2_hours
        if r.get("share_explained_by_position") is not None
        and np.isfinite(r["share_explained_by_position"])
    ]
    shares = np.array([r["share_explained_by_position"] for r in sc])
    gaps = np.array([r["gap"] for r in sc])
    i2 = {
        "n_hours_scored": len(sc),
        "q_act_median": float(np.median([r["q_act_med"] for r in sc])) if sc else None,
        "q_mod_median": float(np.median([r["q_mod"] for r in sc])) if sc else None,
        "position_wedge_median": float(
            np.median([r["position_wedge"] for r in sc])
        )
        if sc
        else None,
        "lam_med_median_usd": float(np.median([r["lam_med"] for r in sc]))
        if sc
        else None,
        "share_explained_by_position": {
            "p25": float(np.percentile(shares, 25)) if len(shares) else None,
            "p50": float(np.percentile(shares, 50)) if len(shares) else None,
            "p75": float(np.percentile(shares, 75)) if len(shares) else None,
            "gap_weighted_mean": float(
                np.average(np.clip(shares, -5, 5), weights=np.abs(gaps))
            )
            if len(shares)
            else None,
        },
        "envelope_comparison": {
            "e180_q_act_median": e180["summary"]["q_act_median"],
            "e180_share_p50_saturating": e180["summary"][
                "share_explained_by_position"
            ]["p50"],
        },
    }

    # ---------------- I-3: fleet loading + cheap-but-unaccepted mass ----------------
    i3_iv: list[dict] = []
    lam_by_iv = {
        (r["hoy"], r["ts"]): r.get("lam")
        for r in iv_recs
        if r.get("lam") is not None and r["n_interior"] >= IB1_MIN_INTERIOR
    }
    for (hoy, ts), sub in corpus[corpus["hoy"].isin(pop_hours)].groupby(
        ["hoy", "ts"], sort=False
    ):
        lam = lam_by_iv.get((hoy, ts))
        if lam is None:
            continue
        oc = sub[sub["on_curve"]]
        if not len(oc):
            continue
        unacc = 0.0
        for _i, r in oc.iterrows():
            m_cheap = _mw_at_price_below(r, lam)
            ceil = min(
                m_cheap,
                r["hasl"] if np.isfinite(r["hasl"]) else np.inf,
            )
            unacc += max(0.0, ceil - r["bp"])
        pos = oc["pos"].to_numpy(float)
        i3_iv.append(
            {
                "hoy": int(hoy),
                "lam": float(lam),
                "pos_med": float(np.nanmedian(pos)),
                "pos_p25": float(np.nanpercentile(pos, 25)),
                "pos_p75": float(np.nanpercentile(pos, 75)),
                "unaccepted_below_lam_mw": float(unacc),
            }
        )
    i3df = pd.DataFrame(i3_iv)
    i3 = (
        {
            "n_intervals": int(len(i3df)),
            "fleet_pos_median": float(i3df["pos_med"].median()),
            "fleet_pos_p25_median": float(i3df["pos_p25"].median()),
            "fleet_pos_p75_median": float(i3df["pos_p75"].median()),
            "unaccepted_below_lam_mw_p25": float(
                i3df["unaccepted_below_lam_mw"].quantile(0.25)
            ),
            "unaccepted_below_lam_mw_p50": float(
                i3df["unaccepted_below_lam_mw"].median()
            ),
            "unaccepted_below_lam_mw_p75": float(
                i3df["unaccepted_below_lam_mw"].quantile(0.75)
            ),
        }
        if len(i3df)
        else {"n_intervals": 0}
    )

    record = {
        "probe": "ercot181_interior_lambda",
        "precommit": "docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md §1",
        "license": (
            "DIAGNOSTIC ONLY: Base Points are realized dispatch outcomes and "
            "I-2 reuses the committed residual-selected top-100 hours; output "
            "barred from parameter identification and every mechanism input "
            "(rule 13 diagnostic clause)"
        ),
        "year": YEAR,
        "rank_bar": RANK_BAR,
        "bars": {
            "IB1": [IB1_COVERAGE, IB1_MIN_INTERIOR],
            "IB2": IB2_REL_IQR,
            "IB3": IB3_REL_ERR,
        },
        "I1": i1,
        "I2": i2,
        "I2_per_hour": i2_hours,
        "I3": i3,
    }
    OUT.write_text(json.dumps(record, indent=1))
    print(json.dumps({"I1": i1, "I2": i2, "I3": i3}, indent=1))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
