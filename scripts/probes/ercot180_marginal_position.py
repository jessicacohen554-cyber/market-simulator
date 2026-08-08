"""ercot-180 §8: the marginal-position DIAGNOSTIC (prompt-1 lever B, no LP).

Pre-registered in PRECOMMIT-ercot180-top-scoped-grain-2026-08-08.md §8 and run
AFTER the form-(b) adjudication (which resolved EXHAUSTED-AT-IDENTIFICATION —
no arm was built, so the standing keeper control is the model side).

QUESTION (the twice-measured P-2 residual): at the top-100 missed 2023 hours,
does reality's marginal price form at a POSITION far up the accepted
resource's own submitted curve, while the model's marginal row sits at a
systematically lower position on its class curve? If yes — measured — the
remaining C3a-2023 residual belongs to a QUANTITY-POSITION instrument
(ercot-181 charter), not to more conditioning grain. If the wedge is ≈ 0, the
quantity-position lane is REFUTED BEFORE IT OPENS (precommit P-7).

DIAGNOSTIC LICENSE: this probe READS residuals (hour selection = largest
demand-weighted actual-minus-control gaps) — licensed for diagnosis and
charter-sizing ONLY (the DIAGNOSIS-ercot177 class); its output is barred from
parameter identification (rule 13's diagnostic-probe clause). NO LP, NO
mechanism, NO ScenarioConfig field, NO scalar.

Constructions and disclosed approximations:

* CORPUS side (delivery-2023 NP3-965, wall-derive parsers): per 5-min
  interval, per ON merchant-gas resource (CC/CT — the disclosure classes; a
  non-gas marginal resource is invisible to this proxy, biasing the wedge
  LOW), the SCED2 step price at Base Point (the last accepted MW), HCAP-
  clipped. The interval's MARGINAL PROXY is the max step-price-at-BP over
  resources with 0 < BP < curve top; its POSITION is BP / curve-top MW.
* MODEL side (keeper control bundle, gate-off compose at HEAD — byte-equal to
  the registered control): P1 surface bids = mc_base + composed mc_bid_adjust
  (startup amortization not included — small vs the top-hour magnitudes,
  disclosed); model price = load-weighted zonal P1 price. The marginal row =
  the highest-bid row with bid <= model price (+1e-6); its class position
  q_mod = share of its class's pmax at strictly lower bids (static pmax,
  un-derated — disclosed).
* POSITION WEDGE per hour: q_act − q_mod; PRICE SHARE EXPLAINED = the same
  marginal resource's curve read at q_mod vs at q_act, over the actual−model
  price gap: [P_curve(q_act) − P_curve(q_mod)] / [RT_actual − P_model].

Output: results/calibration/ercot180_marginal_position.json.
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
    _gas_day_series,
)
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _READ_COLS,
    _SCED2_MW,
    _SCED2_PR,
    _STD_TZ,
    CLASS_OF_RESTYPE,
    _coerce_sced_numeric,
    _delivery_year_rows,
    _sced_source_files,
)

BUNDLE = REPO / "results/calibration/ercot176_control_A"
OUT = REPO / "results/calibration/ercot180_marginal_position.json"
YEAR = 2023
TOP_N = 100


def _model_hourly() -> pd.DataFrame:
    """Load-weighted model system price + demand + actual RT, hour-indexed."""
    sysd = pd.read_parquet(BUNDLE / "hourly" / f"system_{YEAR}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    g = sysd.groupby("hour").apply(
        lambda d: pd.Series(
            {
                "p_mod": float(np.average(d["price"], weights=d["demand"])),
                "demand": float(d["demand"].sum()),
            }
        )
    )
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    act = act[act["year"] == YEAR].set_index("hour")
    g["rt"] = act["rt"].reindex(g.index)
    g["gap_w"] = (g["rt"] - g["p_mod"]) * g["demand"]
    return g


def _corpus_marginal(hours: set[int]) -> pd.DataFrame:
    """Per (interval): marginal proxy price, its position, class, curve reads."""
    gas_day = _gas_day_series()
    rows: list[pd.DataFrame] = []
    for path in _sced_source_files(YEAR):
        df = pd.read_parquet(path, columns=_READ_COLS)
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
        dates = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)][keep]
        gd = gas_day.reindex(pd.DatetimeIndex(dates)).to_numpy(float)
        df = _coerce_sced_numeric(df)
        MW = df[_SCED2_MW].to_numpy(float)
        PR = np.minimum(df[_SCED2_PR].to_numpy(float), HCAP_USD_MWH)
        valid = np.isfinite(MW) & np.isfinite(PR)
        top = np.where(valid, MW, -np.inf).max(axis=1)
        bp = df["Base Point"].to_numpy(float)
        inside = np.isfinite(bp) & (bp > 0) & np.isfinite(top) & (bp < top)

        def _price_at(frac_mw: np.ndarray) -> np.ndarray:
            """Step price at the first valid step whose MW >= frac_mw."""
            m = np.where(valid, MW, np.inf)
            idx = np.argmax(m >= frac_mw[:, None], axis=1)
            has = (m >= frac_mw[:, None]).any(axis=1)
            p = PR[np.arange(len(df)), idx]
            return np.where(has, p, np.nan)

        p_bp = _price_at(bp)
        rows.append(
            pd.DataFrame(
                {
                    "hoy": hoy[inside],
                    "ts": df["SCED Time Stamp"].to_numpy()[inside],
                    "cls": df["Resource Type"]
                    .map(CLASS_OF_RESTYPE)
                    .to_numpy()[inside],
                    "p_bp": p_bp[inside],
                    "pos": (bp / top)[inside],
                    "top": top[inside],
                    "gas": gd[inside],
                    # full curves kept as row index for the q_mod re-read
                    "mw_row": [MW[i] for i in np.flatnonzero(inside)],
                    "pr_row": [PR[i] for i in np.flatnonzero(inside)],
                    "valid_row": [valid[i] for i in np.flatnonzero(inside)],
                }
            )
        )
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def _model_marginal(hours: list[int]) -> dict[int, dict]:
    """Model marginal row/class/position at each hour, from the keeper state."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sp178", REPO / "scripts/probes/ercot178_contpct_seamproof.py"
    )
    sp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sp)
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(
        BUNDLE, YEAR, required_flags=sp.ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    composed, _mask, _parts = sp._compose(state, state["config"], YEAR)
    bids = state["mc_base"] + (composed if composed is not None else 0.0)
    fleet = state["fleet"]
    pmax = state["fleet_arrays"].pmax
    classes = np.array(
        [getattr(g, "plant_group", None) or "" for g in fleet], dtype=object
    )
    sysd = _model_hourly()
    out: dict[int, dict] = {}
    for h in hours:
        p_mod = float(sysd.loc[h, "p_mod"])
        b = bids[:, h]
        under = b <= p_mod + 1e-6
        if not under.any():
            out[h] = {"p_mod": p_mod, "q_mod": None, "cls": None}
            continue
        gi = int(np.flatnonzero(under)[np.argmax(b[under])])
        cls = str(classes[gi])
        in_cls = classes == cls
        cap_below = float(pmax[in_cls & (b < b[gi] - 1e-9)].sum())
        cap_all = float(pmax[in_cls].sum())
        out[h] = {
            "p_mod": p_mod,
            "marginal_bid": float(b[gi]),
            "cls": cls,
            "q_mod": cap_below / cap_all if cap_all > 0 else None,
        }
    return out


def main() -> int:
    sysd = _model_hourly()
    top = sysd.sort_values("gap_w", ascending=False).head(TOP_N)
    hours = [int(h) for h in top.index]
    print(f"top-{TOP_N} gap hours: rt mean {top['rt'].mean():.1f} vs model "
          f"{top['p_mod'].mean():.1f}")

    corpus = _corpus_marginal(set(hours))
    model = _model_marginal(hours)

    per_hour: list[dict] = []
    for h in hours:
        sub = corpus[corpus["hoy"] == h]
        mh = model[h]
        rec = {
            "hour": h,
            "rt": float(sysd.loc[h, "rt"]),
            "p_mod": mh["p_mod"],
            "cls_mod": mh["cls"],
            "q_mod": mh["q_mod"],
        }
        if len(sub) and mh["q_mod"] is not None:
            # interval-level marginal proxy: argmax price-at-BP per timestamp
            idx = sub.groupby("ts")["p_bp"].idxmax().dropna()
            m = sub.loc[idx]
            q_mod = float(mh["q_mod"])
            p_at_qmod = []
            for _i, r in m.iterrows():
                mwv = np.where(r["valid_row"], r["mw_row"], np.inf)
                target = q_mod * r["top"]
                j = int(np.argmax(mwv >= target))
                p_at_qmod.append(
                    float(r["pr_row"][j]) if (mwv >= target).any() else np.nan
                )
            m = m.assign(p_at_qmod=p_at_qmod)
            rec.update(
                {
                    "n_intervals": int(len(m)),
                    "p_marg_corpus_med": float(m["p_bp"].median()),
                    "q_act_med": float(m["pos"].median()),
                    "mult_marg_med": float((m["p_bp"] / m["gas"]).median()),
                    "cls_marg_mode": m["cls"].mode().iat[0] if len(m) else None,
                    "p_curve_at_qmod_med": float(
                        np.nanmedian(m["p_at_qmod"].to_numpy(float))
                    ),
                }
            )
            gap = rec["rt"] - rec["p_mod"]
            pos_leg = rec["p_marg_corpus_med"] - rec["p_curve_at_qmod_med"]
            rec["position_wedge"] = (
                rec["q_act_med"] - rec["q_mod"] if rec["q_mod"] is not None else None
            )
            rec["gap"] = gap
            rec["share_explained_by_position"] = (
                pos_leg / gap if gap and np.isfinite(pos_leg) else None
            )
        per_hour.append(rec)

    scored = [
        r
        for r in per_hour
        if r.get("share_explained_by_position") is not None
        and np.isfinite(r["share_explained_by_position"])
    ]
    shares = np.array([r["share_explained_by_position"] for r in scored])
    wedges = np.array(
        [r["position_wedge"] for r in scored if r["position_wedge"] is not None]
    )
    gaps = np.array([r["gap"] for r in scored])
    summary = {
        "n_hours_scored": len(scored),
        "gap_mean_usd": float(gaps.mean()) if len(gaps) else None,
        "q_act_median": float(np.median([r["q_act_med"] for r in scored]))
        if scored
        else None,
        "q_mod_median": float(np.median([r["q_mod"] for r in scored]))
        if scored
        else None,
        "position_wedge_median": float(np.median(wedges)) if len(wedges) else None,
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
        "marginal_multiplier_median": float(
            np.median([r["mult_marg_med"] for r in scored])
        )
        if scored
        else None,
    }
    record = {
        "probe": "ercot180_marginal_position",
        "precommit": "docs/PRECOMMIT-ercot180-top-scoped-grain-2026-08-08.md §8",
        "license": (
            "DIAGNOSTIC ONLY (reads residuals for hour selection); output "
            "barred from parameter identification (rule 13 diagnostic clause)"
        ),
        "bundle": str(BUNDLE.relative_to(REPO)),
        "year": YEAR,
        "top_n": TOP_N,
        "disclosures": [
            "corpus proxy restricted to disclosure gas classes (CC/CT): a "
            "non-gas marginal resource is invisible, biasing the wedge LOW",
            "model bids = mc_base + surface mc_bid_adjust (P1 startup "
            "amortization not included)",
            "model class position uses static pmax (un-derated)",
            "q_mod mapped onto the corpus resource's own curve as a fraction "
            "of its curve-top MW (normalized-position crosswalk)",
        ],
        "summary": summary,
        "per_hour": per_hour,
    }
    OUT.write_text(json.dumps(record, indent=1))
    print(json.dumps(summary, indent=1))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
