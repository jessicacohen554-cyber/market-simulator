"""ercot-214 G-SPUR-2023 Phase-0 (read-only, no LP): the spill identified
against the spurious hours themselves, from committed artifacts only.

Consumes the two registered ercot-213 bundles' ``hourly/`` sidecars
(``2026-08-16-ercot213-arm-pubanchor`` = the keeper, ``-ctl-headbase`` = its
control), the committed actual-RT parquet, and the published NP6-905-CD
telemetry. Solves nothing and modifies nothing.

Four measurements, in order:

1. **Enumerate + decompose.** The keeper's 17 and the control's 9 spurious
   2023 hours on the standing ``_ercot173_ab`` conventions (demand-weighted
   P1 system price; spurious = model in [150, 500] & actual RT < $150), each
   decomposed into the raw LP energy dual (lambda) vs ``ordc_adder`` vs
   ``rtordpa_overlay``, joined to the ``ercot_ordc_total`` family row and the
   published RTORPA/RTOLCAP/RTOFFCAP/PRC/actual at the same hour.
2. **The counterpart decomposition, exact.** In every adder-writing hour the
   recovered all-tier supply-cap dual splits as
   ``gamma_all(t) = k(t) * (VOLL / ercot_as_n_ramp) + gamma_fam(t)`` with
   integer ``k`` — the AS-product shortfall-ramp step (the
   ``nyiso_rcpf_product_shortfall_steps`` first step is VOLL/12 = $416.67)
   plus the ORDC total family's own balance-row dual. One capped reserve MW
   serves the product row and the total row simultaneously, so the cap dual
   is their SUM; the published-anchor formula then rescales the whole sum
   into the written adder.
3. **The real market at those hours.** Published settled RTORPA in the model's
   contaminated deep hours (ramp step k >= 1, adder > $100).
4. **The exact counterfactual.** Because the anchor is post-solve additive
   (it moves no MW), re-pointing the counterpart to the ORDC component alone
   — ``gamma' = min(gamma_all, gamma_fam)``, i.e. dropping the ramp term —
   re-scores the armed member EXACTLY from the committed bytes:
   ``adder'(t) = min(gamma'(t) * (VOLL - lambda(t)) / VOLL, VOLL - lambda(t))``
   and ``price'(z,t) = price(z,t) - ordc_adder(t) + adder'(t)``.

Usage::

    python scripts/probes/ercot214_gspur_phase0.py \
        [--out results/calibration/ercot214_gspur_phase0.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ARM = REPO / "results/calibration/ercot213_anchor_B"
CTL = REPO / "results/calibration/ercot213_control_A"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
DEFAULT_OUT = REPO / "results/calibration/ercot214_gspur_phase0.json"
YEARS = (2023, 2024, 2025)
MID_BAND = (150.0, 500.0)
VOLL = 5000.0  # the keeper's registered ordc_voll (run_config.json)
N_RAMP = 12  # the keeper's registered ercot_as_n_ramp (run_config.json)
RAMP_STEP = VOLL / N_RAMP  # $416.67 — the AS shortfall-ramp first step
# Published settled RTORPA incidence >$1 / >$100 h (ercot-212 Phase-0 §1).
PUBLISHED = {2023: (294, 17), 2024: (78, 4), 2025: (14, 0)}
C3C_ACTUAL = {2023: 181, 2024: 53, 2025: 31}
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _date(year: int, h: int) -> tuple[str, int]:
    """Model fixed non-leap clock hour -> (date string, hour-of-day CST)."""
    d, hod = divmod(int(h), 24)
    m = 0
    while d >= MONTH_DAYS[m]:
        d -= MONTH_DAYS[m]
        m += 1
    return f"{year}-{m + 1:02d}-{d + 1:02d}", hod


def _member(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Per-hour series for one bundle-year: price, lambda, adder, overlay,
    the ercot_ordc_total family row, and the recovered cap dual."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")].copy()
    overlay = np.zeros(len(df))
    for col in ("rtordpa_overlay", "dam_as_overlay", "ordc_adder"):
        if col in df.columns:
            overlay = overlay + df[col].to_numpy(float)
    df["lam_z"] = df["price"].to_numpy(float) - overlay

    def dw(col: str) -> np.ndarray:
        num = (df[col] * df["demand"]).groupby(df["hour"]).sum()
        den = df.groupby("hour")["demand"].sum()
        return (num / den).reindex(range(8760)).to_numpy(float)

    out = {
        "price": dw("price"),
        "lam": dw("lam_z"),
        "adder": df.groupby("hour")["ordc_adder"].first().reindex(range(8760)).to_numpy(float),
        "rtordpa_ov": df.groupby("hour")["rtordpa_overlay"].first().reindex(range(8760)).to_numpy(float)
        if "rtordpa_overlay" in df.columns
        else np.zeros(8760),
    }
    rf = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    rf = rf[(rf["pass"] == "P1") & (rf["family"] == "ercot_ordc_total")]
    for col in ("dual", "requirement_mw", "held_mw", "shortfall_mw"):
        out[f"fam_{col}"] = (
            rf.groupby("hour")[col].sum().reindex(range(8760)).fillna(0.0).to_numpy(float)
        )
    head = np.maximum(VOLL - out["lam"], 0.0)
    rescale = head / VOLL
    with np.errstate(divide="ignore", invalid="ignore"):
        out["gamma_all"] = np.where(rescale > 1e-12, out["adder"] / rescale, 0.0)
    out["head"] = head
    out["rescale"] = rescale
    return out


def _stats(m: np.ndarray, a: np.ndarray) -> dict:
    ok = np.isfinite(m) & np.isfinite(a)
    mm, aa = m[ok], a[ok]
    hi = aa > 200.0
    return {
        "c3a_hub_pct": round(float((mm.mean() - aa.mean()) / aa.mean() * 100.0), 2),
        "nrmse": round(float(np.sqrt(np.mean((mm - aa) ** 2)) / aa.mean()), 4),
        "spurious": int(((mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & (aa < MID_BAND[0])).sum()),
        "tail_model": int((mm > 200.0).sum()),
        "tail_caught": int((hi & (mm > 200.0)).sum()),
        "model_mean": round(float(mm.mean()), 3),
    }


def _spur_hours(m: np.ndarray, a: np.ndarray) -> list[int]:
    mm = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    return [
        int(h)
        for h in np.where((mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & (aa < MID_BAND[0]))[0]
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    act_all = pd.read_parquet(ACTUAL_LMP)
    out: dict = {
        "_provenance": {
            "scorer": "scripts/probes/ercot214_gspur_phase0.py",
            "keeper": str(ARM),
            "control": str(CTL),
            "conventions": "_ercot173_ab demand-weighted P1 price; spurious = model in [150,500] & actual rt < 150",
            "voll": VOLL,
            "n_ramp": N_RAMP,
            "ramp_step_usd": round(RAMP_STEP, 2),
        },
        "spurious_2023": {},
        "counterpart_decomposition": {},
        "counterfactual_repoint": {},
    }

    # --- 1. Enumerate + decompose the 2023 spurious hours, both members.
    year = 2023
    a23 = act_all[act_all.year == year].set_index("hour")["rt"].reindex(range(8760)).to_numpy()
    da23 = act_all[act_all.year == year].set_index("hour")["da"].reindex(range(8760)).to_numpy()
    pub23 = (
        pd.read_parquet(REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet")
        .set_index("hour")
        .reindex(range(8760))
    )
    members = {"keeper": _member(ARM, year), "control": _member(CTL, year)}
    spur = {k: _spur_hours(v["price"], a23) for k, v in members.items()}
    out["spurious_2023"]["keeper_hours"] = spur["keeper"]
    out["spurious_2023"]["control_hours"] = spur["control"]
    out["spurious_2023"]["shared"] = sorted(set(spur["keeper"]) & set(spur["control"]))
    out["spurious_2023"]["keeper_only"] = sorted(set(spur["keeper"]) - set(spur["control"]))
    out["spurious_2023"]["control_only"] = sorted(set(spur["control"]) - set(spur["keeper"]))
    for name, m in members.items():
        rows = []
        for h in spur[name]:
            date, hod = _date(year, h)
            rows.append(
                {
                    "h": h,
                    "date": date,
                    "hod_cst": hod,
                    "model_price": round(float(m["price"][h]), 2),
                    "lambda": round(float(m["lam"][h]), 2),
                    "ordc_adder": round(float(m["adder"][h]), 2),
                    "rtordpa_overlay": round(float(m["rtordpa_ov"][h]), 2),
                    "gamma_all": round(float(m["gamma_all"][h]), 2),
                    "gamma_fam": round(float(m["fam_dual"][h]), 2),
                    "fam_req_mw": round(float(m["fam_requirement_mw"][h]), 0),
                    "fam_held_mw": round(float(m["fam_held_mw"][h]), 0),
                    "fam_short_mw": round(float(m["fam_shortfall_mw"][h]), 0),
                    "actual_rt": round(float(a23[h]), 2),
                    "actual_da": round(float(da23[h]), 2),
                    "pub_rtorpa": round(float(pub23["rtorpa"][h]), 2),
                    "pub_rtordpa": round(float(pub23["rtordpa"][h]), 2),
                    "pub_rtolcap": round(float(pub23["rtolcap"][h]), 0),
                    "pub_rtoffcap": round(float(pub23["rtoffcap"][h]), 0),
                    "pub_prc": round(float(pub23["prc"][h]), 0),
                }
            )
        out["spurious_2023"][f"{name}_rows"] = rows
    k = members["keeper"]
    out["spurious_2023"]["classification"] = {
        "energy_made_lambda_ge_150": int(sum(1 for h in spur["keeper"] if k["lam"][h] >= 150.0)),
        "adder_made_lambda_lt_150": int(
            sum(1 for h in spur["keeper"] if k["lam"][h] < 150.0 and k["price"][h] >= 150.0)
        ),
    }

    # --- 2-4. Decomposition + published census + exact counterfactual, per year.
    for yr in YEARS:
        a = act_all[act_all.year == yr].set_index("hour")["rt"].reindex(range(8760)).to_numpy()
        pub = (
            pd.read_parquet(REPO / f"data/raw/ercot/ercot_{yr}_ordc_reserves_hourly.parquet")
            .set_index("hour")
            .reindex(range(8760))
        )
        rtorpa = np.nan_to_num(pub["rtorpa"].to_numpy(float))
        m = members["keeper"] if yr == 2023 else _member(ARM, yr)
        writing = m["adder"] > 1e-9
        resid = m["gamma_all"] - m["fam_dual"]
        kstep = np.round(resid / RAMP_STEP)
        exact = np.abs(resid - kstep * RAMP_STEP) < 0.5
        hist = {
            int(s): int(c)
            for s, c in zip(*np.unique(kstep[writing & exact].astype(int), return_counts=True))
        }
        contaminated = writing & (kstep >= 1)
        deep = contaminated & (m["adder"] > 100.0)
        out["counterpart_decomposition"][str(yr)] = {
            "writing_hours": int(writing.sum()),
            "decomposition_exact_hours": int((writing & exact).sum()),
            "ramp_step_histogram": hist,
            "contaminated_hours": int(contaminated.sum()),
            "contaminated_deep_hours_adder_gt100": int(deep.sum()),
            "deep_published_rtorpa_p50": round(float(np.median(rtorpa[deep])), 1) if deep.any() else None,
            "deep_published_rtorpa_gt100_h": int((rtorpa[deep] > 100.0).sum()) if deep.any() else 0,
            "deep_actual_rt_p50": round(float(np.nanmedian(a[deep])), 1) if deep.any() else None,
            "deep_gamma_all_p50": round(float(np.median(m["gamma_all"][deep])), 1) if deep.any() else None,
            "deep_gamma_fam_p50": round(float(np.median(m["fam_dual"][deep])), 1) if deep.any() else None,
        }
        gamma_new = np.minimum(m["gamma_all"], m["fam_dual"])
        adder_new = np.minimum(gamma_new * m["rescale"], m["head"])
        price_new = m["price"] - m["adder"] + adder_new
        s_arm, s_new = _stats(m["price"], a), _stats(price_new, a)
        out["counterfactual_repoint"][str(yr)] = {
            "arm": s_arm,
            "repointed": s_new,
            "repointed_spurious_hours": _spur_hours(price_new, a),
            "adder_incidence_nonzero_gt1_gt100": {
                "arm": [int((m["adder"] > 0).sum()), int((m["adder"] > 1).sum()), int((m["adder"] > 100).sum())],
                "repointed": [int((adder_new > 1e-9).sum()), int((adder_new > 1).sum()), int((adder_new > 100).sum())],
                "published_settled_gt1_gt100": list(PUBLISHED[yr]),
            },
            "gcap_violations_repointed": int((adder_new - m["head"] > 1e-6).sum()),
            "max_adder_arm_vs_repointed": [round(float(m["adder"].max()), 2), round(float(adder_new.max()), 2)],
            "tail_actual": C3C_ACTUAL[yr],
        }

    args.out.write_text(json.dumps(out, indent=1) + "\n")
    brief = {
        "spurious_2023": {
            kk: out["spurious_2023"][kk]
            for kk in ("keeper_hours", "control_hours", "keeper_only", "classification")
        },
        "counterpart_decomposition": out["counterpart_decomposition"],
        "counterfactual_repoint": {
            y: {
                "arm": v["arm"],
                "repointed": v["repointed"],
                "incidence": v["adder_incidence_nonzero_gt1_gt100"],
            }
            for y, v in out["counterfactual_repoint"].items()
        },
    }
    print(json.dumps(brief, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
