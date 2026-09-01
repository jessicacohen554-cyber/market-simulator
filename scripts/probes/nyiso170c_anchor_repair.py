"""nyiso-170c — the coincidence tests REPAIRED onto the four admissible classes.

ZERO SOLVE. Imports its instruments from ``nyiso170_merit_order_coincidence``.

Rule 22 ``[R-HOLDOUT]``: every year read is 2023, 2024 or 2025.
Rule 13 ``[R-MEASURED]``: CAMPD enters as conduct identification only.

Why this exists
---------------
nyiso-170b gate H1 FAILED, and the failure is an instrument fact, not a model
fact. Measured on the CAMPD NY 2025 extract:

* **ST_CHP** — five CEMS-registered steam units at EIA-860 CHP plants, all
  reporting **0.000 TWh** for the year, against a committed benchmark of
  0.800 TWh. The anchored measured series is identically zero, so nyiso-170's
  over-run group silently carried the model's ENTIRE ST_CHP output as error.
* **CT_CHP** — a SINGLE CEMS unit, 0.483 TWh gross against a benchmark of
  2.383 TWh (anchor factor 4.9). One unit cannot stand for the class's hourly
  conduct.

Both classes are below or outside Part-75 CEMS coverage, so CAMPD cannot
identify their hourly conduct at all. The remaining four — CC_CHP, CC_REGULAR,
CT_PEAKER, ST_GAS — anchor at 0.84-1.50 and ARE identifiable, and they are
exactly the four the session brief names. This probe re-runs nyiso-170's
coincidence gates on that admissible set, restating every share against the
FOUR-class gas total so the decomposition stays an identity.

This is a repair of a contaminated instrument, not a re-specification chosen
after seeing a result: the contaminated classes were named by nyiso-170b's own
pre-registered validity gate, before this file was written.

PRE-REGISTERED GATES
--------------------
**J1 — REPAIRED G1a.** ``OVER`` = the model-minus-measured error over
{CC_CHP, CC_REGULAR}; ``UNDER`` = minus the same over {CT_PEAKER, ST_GAS}.
Pearson r, and ``matched_share`` against a 999-fold circular-shift null.
COINCIDENT iff matched_share >= 0.60 AND above the null p95, in all three years.

**J2 — REPAIRED G2.** CC share of the four-class gas increment on hours whose
load rises > 200 MW, model vs measured. SUPPORTED iff the model's CC share
exceeds the measured share in all three years.

**J3 — REPAIRED LEVEL/MIX.** The exact ``delta = s_meas*dG + ds*G_model``
decomposition restated on the four-class total. MIX CARRIES iff the mix term is
>= 60 % of |level| + |mix| for both groups in all three years.

**J4 — WITHIN-LOAD COINCIDENCE (the fairest form of the brief's question).**
Inside each model-load decile, Pearson r between OVER and UNDER. This removes
the load channel from the coincidence test exactly as nyiso-170b H2 removed it
from the price test, so the two are symmetric. COINCIDENT iff the mean
within-decile r is positive and at least 6 of 10 deciles are positive, in all
three years.

**J5 — CEMS COVERAGE RECORD.** Per class: CEMS unit count, gross TWh, benchmark
TWh, anchor factor. No gate; it is the citable statement of which NYISO classes
CAMPD can and cannot identify.

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso170c_anchor_repair.py``
Writes: ``results/calibration/_nyiso170c_anchor_repair.json``
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

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.probes.nyiso170_merit_order_coincidence import (  # noqa: E402
    GAS_CLASSES,
    LOAD_RISE_MW,
    N_NULL,
    NULL_SEED,
    UNIT_KIND,
    YEARS,
    bench_classes,
    build_series,
    campd_frame,
    chp_plants,
    keeper_system,
)

OUT = REPO / "results/calibration/_nyiso170c_anchor_repair.json"

#: The four classes CAMPD can identify (nyiso-170b H1).
OVER4 = ("CC_CHP", "CC_REGULAR")
UNDER4 = ("CT_PEAKER", "ST_GAS")
ADMISSIBLE = OVER4 + UNDER4

J1_MATCHED_MIN = 0.60
J3_MIX_SHARE_MIN = 0.60
J4_MIN_DECILES = 6


def measure_j1(model: dict, meas: dict) -> dict:
    """J1 — repaired literal coincidence, against a circular-shift null."""
    over = np.sum([model[k] - meas[k] for k in OVER4], axis=0)
    under = -np.sum([model[k] - meas[k] for k in UNDER4], axis=0)
    op, up = np.clip(over, 0, None), np.clip(under, 0, None)
    denom = float(op.sum())
    matched = float(np.minimum(op, up).sum()) / denom if denom else 0.0
    rng = np.random.default_rng(NULL_SEED)
    null = np.array(
        [
            float(np.minimum(op, np.roll(up, int(s))).sum()) / denom
            for s in rng.integers(1, 8760, size=N_NULL)
        ]
    )
    p95 = float(np.percentile(null, 95))
    return dict(
        pearson_r=round(float(np.corrcoef(over, under)[0, 1]), 4),
        matched_share=round(matched, 4),
        null_median=round(float(np.median(null)), 4),
        null_p95=round(p95, 4),
        excess_over_null_median=round(matched - float(np.median(null)), 4),
        J1_coincident=bool(matched >= J1_MATCHED_MIN and matched > p95),
    )


def measure_j2(model: dict, meas: dict, load: np.ndarray) -> dict:
    """J2 — repaired revealed marginal class on the four-class increment."""
    dl = np.diff(load)
    up = dl > LOAD_RISE_MW
    out = {}
    for nm, src in (("model", model), ("measured", meas)):
        tot = np.sum([src[k] for k in ADMISSIBLE], axis=0)
        dt = float(np.diff(tot)[up].sum())
        out[nm] = {
            k: (round(float(np.diff(src[k])[up].sum()) / dt, 4) if dt else None)
            for k in ADMISSIBLE
        }
        out[nm]["_increment_mw"] = round(dt, 1)
        out[nm]["_cc_share"] = (
            round(float(sum(np.diff(src[k])[up].sum() for k in OVER4)) / dt, 4) if dt else None
        )
    out["n_rising_hours"] = int(up.sum())
    out["J2_model_cc_heavier"] = bool(
        (out["model"]["_cc_share"] or 0) > (out["measured"]["_cc_share"] or 0)
    )
    return out


def measure_j3(year: int, model: dict, meas: dict) -> dict:
    """J3 — the exact level/mix identity restated on the four-class total."""
    gm = np.sum([model[k] for k in ADMISSIBLE], axis=0)
    gx = np.sum([meas[k] for k in ADMISSIBLE], axis=0)
    dG = gm - gx
    rows, group = {}, {"over": [0.0, 0.0], "under": [0.0, 0.0]}
    for k in ADMISSIBLE:
        sx = np.divide(meas[k], gx, out=np.zeros(8760), where=gx > 0)
        sm = np.divide(model[k], gm, out=np.zeros(8760), where=gm > 0)
        lvl, mix = sx * dG, (sm - sx) * gm
        d = model[k] - meas[k]
        rows[k] = dict(
            delta_twh=round(float(d.sum()) / 1e6, 4),
            level_term_twh=round(float(lvl.sum()) / 1e6, 4),
            mix_term_twh=round(float(mix.sum()) / 1e6, 4),
            identity_residual_twh=round(float((lvl + mix - d).sum()) / 1e6, 8),
        )
        g = "over" if k in OVER4 else "under"
        group[g][0] += float(lvl.sum())
        group[g][1] += float(mix.sum())
    grp = {
        g: dict(
            level_term_twh=round(v[0] / 1e6, 4),
            mix_term_twh=round(v[1] / 1e6, 4),
            mix_share_of_abs=round(abs(v[1]) / max(abs(v[0]) + abs(v[1]), 1e-9), 4),
        )
        for g, v in group.items()
    }
    return dict(
        by_class=rows,
        by_group=grp,
        four_class_model_twh=round(float(gm.sum()) / 1e6, 4),
        four_class_measured_twh=round(float(gx.sum()) / 1e6, 4),
        four_class_delta_pct=round(float(dG.sum()) / float(gx.sum()) * 100, 2),
        J3_mix_carries=bool(
            grp["over"]["mix_share_of_abs"] >= J3_MIX_SHARE_MIN
            and grp["under"]["mix_share_of_abs"] >= J3_MIX_SHARE_MIN
        ),
    )


def measure_j4(model: dict, meas: dict, load: np.ndarray) -> dict:
    """J4 — coincidence inside each load decile, the load channel removed."""
    over = np.sum([model[k] - meas[k] for k in OVER4], axis=0)
    under = -np.sum([model[k] - meas[k] for k in UNDER4], axis=0)
    order = np.argsort(load)
    rows, npos = [], 0
    for k in range(10):
        idx = order[int(8760 * k / 10) : int(8760 * (k + 1) / 10)]
        r = float(np.corrcoef(over[idx], under[idx])[0, 1])
        rows.append(dict(decile=k, load_mw=round(float(load[idx].mean()), 1), r=round(r, 4)))
        npos += int(r > 0)
    mean_r = float(np.mean([r["r"] for r in rows]))
    return dict(
        within_decile=rows,
        mean_within_decile_r=round(mean_r, 4),
        deciles_positive=npos,
        J4_coincident=bool(mean_r > 0 and npos >= J4_MIN_DECILES),
    )


def measure_j5(year: int, chpset: set[int]) -> dict:
    """J5 — the CEMS coverage record for every gas class."""
    d = campd_frame(year)
    bench = bench_classes(year)
    _, _, raw = build_series(year, chpset)
    rows = {}
    for k in GAS_CLASSES:
        kind, is_chp = UNIT_KIND[k]
        ut = d["_ut"]
        sel = (
            ut.str.contains("fired|boiler", case=False)
            if kind == "STEAM"
            else ut.str.contains(kind)
        )
        inchp = d["_fid"].isin(chpset)
        sel = sel & (inchp if is_chp else ~inchp)
        gross = float(raw[k].sum()) / 1e6
        b = float(bench.get(k, 0.0))
        rows[k] = dict(
            cems_units=int(d.loc[sel, "_fid"].nunique()),
            cems_gross_twh=round(gross, 4),
            bench_twh=round(b, 4),
            anchor_scale=(round(b / gross, 4) if gross > 0 else None),
            identifiable=bool(k in ADMISSIBLE),
        )
    return dict(
        by_class=rows,
        admissible=list(ADMISSIBLE),
        inadmissible=[k for k in GAS_CLASSES if k not in ADMISSIBLE],
    )


def main() -> None:
    chpset = chp_plants()
    rec: dict = {
        "probe": "nyiso170c_anchor_repair",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "years": list(YEARS),
        "note": (
            "Zero solve. Re-runs nyiso-170's coincidence gates on the four gas "
            "classes CAMPD can identify, after nyiso-170b's pre-registered "
            "validity gate H1 named ST_CHP (5 CEMS units, 0.000 TWh) and "
            "CT_CHP (1 unit, anchor 4.9) as unidentifiable. Gates "
            "pre-registered in the module docstring and committed before the "
            "probe was run."
        ),
        "gate_thresholds": dict(
            J1_matched_min=J1_MATCHED_MIN,
            J3_mix_share_min=J3_MIX_SHARE_MIN,
            J4_min_deciles=J4_MIN_DECILES,
            load_rise_mw=LOAD_RISE_MW,
            n_null=N_NULL,
            null_seed=NULL_SEED,
        ),
        "by_year": {},
    }

    for year in YEARS:
        model, meas, _ = build_series(year, chpset)
        load, _ = keeper_system(year)
        J1 = measure_j1(model, meas)
        J2 = measure_j2(model, meas, load)
        J3 = measure_j3(year, model, meas)
        J4 = measure_j4(model, meas, load)
        J5 = measure_j5(year, chpset)
        rec["by_year"][str(year)] = {
            "J1_repaired_coincidence": J1,
            "J2_repaired_revealed_marginal": J2,
            "J3_repaired_level_mix": J3,
            "J4_within_load_coincidence": J4,
            "J5_cems_coverage": J5,
        }
        print(f"\n{year}")
        print(
            f"  J1 matched {J1['matched_share']:.3f}  null p95 {J1['null_p95']:.3f}"
            f"  r {J1['pearson_r']:+.3f}   COINCIDENT: {J1['J1_coincident']}"
        )
        print(
            f"  J2 CC share of 4-class increment: model {J2['model']['_cc_share']:.3f}"
            f" vs measured {J2['measured']['_cc_share']:.3f}   SUPPORTED: {J2['J2_model_cc_heavier']}"
        )
        for g in ("over", "under"):
            v = J3["by_group"][g]
            print(
                f"  J3 {g:<5} level {v['level_term_twh']:+7.3f}  mix {v['mix_term_twh']:+7.3f}"
                f"  mix share {v['mix_share_of_abs']:.3f}"
            )
        print(f"     4-class total error {J3['four_class_delta_pct']:+.2f}%   MIX CARRIES: {J3['J3_mix_carries']}")
        print(
            f"  J4 mean within-decile r {J4['mean_within_decile_r']:+.3f}"
            f"  positive {J4['deciles_positive']}/10   COINCIDENT: {J4['J4_coincident']}"
        )

    print("\n  J5 CEMS coverage (2025):")
    for k, v in rec["by_year"]["2025"]["J5_cems_coverage"]["by_class"].items():
        print(
            f"     {k:<11} units {v['cems_units']:>3}  gross {v['cems_gross_twh']:>7.3f}"
            f"  bench {v['bench_twh']:>7.3f}  anchor {v['anchor_scale']}"
            f"  identifiable {v['identifiable']}"
        )

    ys = rec["by_year"]
    rec["verdict"] = dict(
        J1_coincident_all_years=all(ys[str(y)]["J1_repaired_coincidence"]["J1_coincident"] for y in YEARS),
        J2_supported_all_years=all(
            ys[str(y)]["J2_repaired_revealed_marginal"]["J2_model_cc_heavier"] for y in YEARS
        ),
        J3_mix_carries_all_years=all(ys[str(y)]["J3_repaired_level_mix"]["J3_mix_carries"] for y in YEARS),
        J4_coincident_all_years=all(
            ys[str(y)]["J4_within_load_coincidence"]["J4_coincident"] for y in YEARS
        ),
    )
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\n  VERDICT {json.dumps(rec['verdict'])}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    raise SystemExit(main())
