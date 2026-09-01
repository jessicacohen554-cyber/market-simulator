"""nyiso-170b — POST-HOC ADVERSARIAL CONTROLS on the nyiso-170 phase-0 result.

ZERO SOLVE. Same instruments as ``nyiso170_merit_order_coincidence.py``, which
it imports rather than re-implements, so both probes measure the same objects.

Rule 22 ``[R-HOLDOUT]``: every year read is 2023, 2024 or 2025.
Rule 13 ``[R-MEASURED]``: CAMPD enters as conduct identification only.

Why this exists
---------------
nyiso-170 returned a SPLIT result: the coincidence gates G1a (and G2 in 2023)
FAILED, while the C3a price-linkage gate G3 PASSED in all three years by
$10.65-$14.26/MWh. **These controls exist to attack G3, the probe's own
positive finding**, and to characterise WHY G1a failed rather than leaving it a
bare null. Every gate below can only weaken or qualify nyiso-170's claims; none
can rescue a failed one. Written and committed BEFORE being run.

THE CONFOUND G3 MUST SURVIVE. Both the CC-share excess ``ds_CC`` and the
model-minus-actual price gap are functions of system load: at high load the
model has CC headroom the market did not use, and at high load the model
under-prices because of the nyiso-167 gain deficit. A monotone gap-vs-ds_CC
ladder is therefore exactly what a pure load artifact would also produce. G3
means nothing until the load channel is removed.

PRE-REGISTERED GATES
--------------------
**H1 — ANCHOR VALIDITY.** Each measured class is scaled by one factor,
benchmark_TWh / CAMPD_TWh. A factor far from 1 means CAMPD's coverage of that
class is not the benchmark's population, and the class's HOURLY shape is then
carrying a coverage artifact. VALID iff every gas class's factor is in
[0.7, 1.5]; classes outside are named and their conclusions flagged.

**H2 — THE DECISIVE CONTROL: is G3 a load artifact?** Two independent removals
of the load channel:
  (a) WITHIN-LOAD-DECILE. Inside each of the ten model-load deciles, split the
      876 hours into ds_CC quartiles and take top-minus-bottom price gap. Load
      varies little inside a decile, so a surviving spread is not load.
  (b) PARTIAL CORRELATION. Residualise both ds_CC and the gap on
      [load, load^2, load^3] by OLS and correlate the residuals.
  G3 SURVIVES iff, in ALL THREE years, at least 6 of 10 deciles show a
  within-decile spread <= -$2/MWh AND the partial correlation is negative.
  If it does not survive, **the C3a linkage claim of nyiso-170 is WITHDRAWN**
  and the object is a C1-tier volume object only.

**H3 — WHERE THE MIX ERROR LIVES.** ds_CC by load-percentile band, with each
band's share of the annual mix term. Characterisation, no gate: it says whether
the composition error sits in the 50-90 band that carries 73 % of the 2025 C3a
deficit (nyiso-168) or somewhere else.

**H4 — THE TWO-OBJECTS READING.** For each group, the dispatch-weighted mean
load percentile at which its error accumulates, plus each class's error by
duration band. nyiso-169b measured the CC_CHP over-run at the BOTTOM of its own
duration curve. SUPPORTED iff the over-run group's error-weighted mean load
percentile sits at least 10 points BELOW the under-run group's in all three
years — i.e. the two are objects in different parts of the duration curve, which
is a positive explanation for G1a's failure rather than a bare null.

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso170b_displacement_controls.py``
Writes: ``results/calibration/_nyiso170b_displacement_controls.json``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyiso170_merit_order_coincidence import (  # noqa: E402
    BANDS,
    GAS_CLASSES,
    OVER_CLASSES,
    UNDER_CLASSES,
    YEARS,
    bench_classes,
    build_series,
    chp_plants,
    keeper_system,
)
import pandas as pd  # noqa: E402

from scripts.probes.nyiso170_merit_order_coincidence import ACTUAL_HOURLY  # noqa: E402

OUT = REPO / "results/calibration/_nyiso170b_displacement_controls.json"

#: Pre-registered thresholds.
H1_SCALE_LO, H1_SCALE_HI = 0.7, 1.5
H2_SPREAD_MAX = -2.0
H2_MIN_DECILES = 6
H4_PCTL_GAP_MIN = 10.0

#: Duration bands for H4, as percentiles of the class's own sorted output.
DUR_BANDS = ((0, 5), (5, 25), (25, 50), (50, 75), (75, 100))


def measure_h1(year: int, chpset: set[int]) -> dict:
    """H1 — the benchmark/CAMPD anchor factor for every gas class."""
    _, _, raw = build_series(year, chpset)
    bench = bench_classes(year)
    rows, bad = {}, []
    for k in GAS_CLASSES:
        gross = float(raw[k].sum()) / 1e6
        b = float(bench.get(k, 0.0))
        sc = (b / gross) if gross > 0 else None
        rows[k] = dict(
            campd_gross_twh=round(gross, 4),
            bench_twh=round(b, 4),
            anchor_scale=(round(sc, 4) if sc is not None else None),
        )
        if sc is None or not (H1_SCALE_LO <= sc <= H1_SCALE_HI):
            bad.append(k)
    return dict(by_class=rows, out_of_range=bad, H1_valid=not bad)


def _resid(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """OLS residual of ``y`` on ``X`` (design already carries an intercept)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def measure_h2(model: dict, meas: dict, load, mprice, da) -> dict:
    """H2 — remove the load channel two independent ways and re-test G3."""
    gm = np.sum([model[k] for k in GAS_CLASSES], axis=0)
    gx = np.sum([meas[k] for k in GAS_CLASSES], axis=0)
    cm = np.divide(model["CC_CHP"] + model["CC_REGULAR"], gm, out=np.zeros(8760), where=gm > 0)
    cx = np.divide(meas["CC_CHP"] + meas["CC_REGULAR"], gx, out=np.zeros(8760), where=gx > 0)
    ds = cm - cx
    gap = mprice - da
    ok = np.isfinite(gap) & np.isfinite(ds)

    order = np.argsort(load)
    dec_rows, n_pass = [], 0
    for k in range(10):
        idx = order[int(8760 * k / 10) : int(8760 * (k + 1) / 10)]
        idx = idx[ok[idx]]
        if len(idx) < 40:
            dec_rows.append(dict(decile=k, n=len(idx), spread=None))
            continue
        o = idx[np.argsort(ds[idx])]
        q = max(len(o) // 4, 1)
        sp = float(np.mean(gap[o[-q:]]) - np.mean(gap[o[:q]]))
        dec_rows.append(
            dict(
                decile=k,
                n=len(idx),
                load_mw=round(float(load[idx].mean()), 1),
                ds_lo=round(float(ds[o[:q]].mean()), 4),
                ds_hi=round(float(ds[o[-q:]].mean()), 4),
                gap_lo=round(float(np.mean(gap[o[:q]])), 2),
                gap_hi=round(float(np.mean(gap[o[-q:]])), 2),
                spread=round(sp, 2),
            )
        )
        if sp <= H2_SPREAD_MAX:
            n_pass += 1

    L = load[ok]
    X = np.column_stack([np.ones(L.size), L, L**2, L**3])
    rs, rg = _resid(ds[ok], X), _resid(gap[ok], X)
    partial = float(np.corrcoef(rs, rg)[0, 1])
    raw_r = float(np.corrcoef(ds[ok], gap[ok])[0, 1])

    return dict(
        within_decile=dec_rows,
        deciles_passing=n_pass,
        raw_corr_ds_gap=round(raw_r, 4),
        partial_corr_ds_gap_given_load=round(partial, 4),
        corr_ds_load=round(float(np.corrcoef(ds[ok], L)[0, 1]), 4),
        corr_gap_load=round(float(np.corrcoef(gap[ok], L)[0, 1]), 4),
        H2_survives=bool(n_pass >= H2_MIN_DECILES and partial < 0),
    )


def measure_h3(model: dict, meas: dict, load) -> dict:
    """H3 — where in the load distribution the within-gas mix error sits."""
    gm = np.sum([model[k] for k in GAS_CLASSES], axis=0)
    gx = np.sum([meas[k] for k in GAS_CLASSES], axis=0)
    cm = np.divide(model["CC_CHP"] + model["CC_REGULAR"], gm, out=np.zeros(8760), where=gm > 0)
    cx = np.divide(meas["CC_CHP"] + meas["CC_REGULAR"], gx, out=np.zeros(8760), where=gx > 0)
    ds = cm - cx
    mix_cc = ds * gm
    order = np.argsort(load)
    tot = float(mix_cc.sum())
    rows = []
    for lo, hi in BANDS:
        idx = order[int(8760 * lo / 100) : int(8760 * hi / 100)]
        rows.append(
            dict(
                pct_lo=lo,
                pct_hi=hi,
                n=len(idx),
                load_mw=round(float(load[idx].mean()), 1),
                ds_cc=round(float(ds[idx].mean()), 4),
                mix_twh=round(float(mix_cc[idx].sum()) / 1e6, 4),
                share_of_mix_pct=(round(float(mix_cc[idx].sum()) / tot * 100, 1) if tot else None),
            )
        )
    return dict(bands=rows, total_cc_mix_twh=round(tot / 1e6, 4))


def measure_h4(model: dict, meas: dict, load) -> dict:
    """H4 — the load percentile at which each group's error accumulates."""
    pct = np.empty(8760)
    pct[np.argsort(load)] = np.arange(8760) / 8760 * 100

    def wmean(err: np.ndarray) -> float | None:
        w = np.abs(err)
        return float((pct * w).sum() / w.sum()) if w.sum() > 0 else None

    over = np.sum([model[k] - meas[k] for k in OVER_CLASSES], axis=0)
    under = np.sum([meas[k] - model[k] for k in UNDER_CLASSES], axis=0)
    po, pu = wmean(np.clip(over, 0, None)), wmean(np.clip(under, 0, None))

    per_class = {}
    for k in GAS_CLASSES:
        d = model[k] - meas[k]
        s = np.sort(model[k])[::-1], np.sort(meas[k])[::-1]
        bands = []
        for lo, hi in DUR_BANDS:
            a, b = int(8760 * lo / 100), int(8760 * hi / 100)
            dm, dx = float(s[0][a:b].mean()), float(s[1][a:b].mean())
            bands.append(
                dict(
                    band=f"{lo}-{hi}",
                    model_mw=round(dm, 1),
                    measured_mw=round(dx, 1),
                    delta_pct=(round((dm - dx) / dx * 100, 1) if dx else None),
                )
            )
        per_class[k] = dict(
            err_weighted_load_pctl=(round(wmean(np.clip(d, 0, None)), 1) if (d > 0).any() else None),
            deficit_weighted_load_pctl=(
                round(wmean(np.clip(-d, 0, None)), 1) if (d < 0).any() else None
            ),
            duration_bands=bands,
        )

    return dict(
        over_group_err_weighted_load_pctl=(round(po, 1) if po else None),
        under_group_err_weighted_load_pctl=(round(pu, 1) if pu else None),
        separation_pctl_points=(round(pu - po, 1) if (po and pu) else None),
        by_class=per_class,
        H4_two_objects=bool(po is not None and pu is not None and (pu - po) >= H4_PCTL_GAP_MIN),
    )


def main() -> None:
    chpset = chp_plants()
    act = pd.read_parquet(ACTUAL_HOURLY)
    rec: dict = {
        "probe": "nyiso170b_displacement_controls",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "years": list(YEARS),
        "note": (
            "Zero solve. POST-HOC ADVERSARIAL controls on nyiso-170. H2 exists "
            "to attack nyiso-170's own passing gate G3 by removing the load "
            "channel; H4 characterises why the coincidence gate G1a failed. "
            "Gates pre-registered in the module docstring, committed before "
            "the probe was run."
        ),
        "gate_thresholds": dict(
            H1_scale_range=[H1_SCALE_LO, H1_SCALE_HI],
            H2_spread_max_usd=H2_SPREAD_MAX,
            H2_min_deciles=H2_MIN_DECILES,
            H4_pctl_gap_min=H4_PCTL_GAP_MIN,
        ),
        "by_year": {},
    }

    for year in YEARS:
        model, meas, _ = build_series(year, chpset)
        load, mprice = keeper_system(year)
        a = act[act["year"] == year].sort_values("hour")
        da = a["da"].to_numpy(float)

        H1 = measure_h1(year, chpset)
        H2 = measure_h2(model, meas, load, mprice, da)
        H3 = measure_h3(model, meas, load)
        H4 = measure_h4(model, meas, load)
        rec["by_year"][str(year)] = {
            "H1_anchor_validity": H1,
            "H2_load_confound_control": H2,
            "H3_mix_by_load_band": H3,
            "H4_two_objects": H4,
        }

        print(f"\n{year}")
        print(
            f"  H1 anchors "
            + "  ".join(f"{k}:{H1['by_class'][k]['anchor_scale']}" for k in GAS_CLASSES)
            + f"   VALID: {H1['H1_valid']}"
        )
        print(
            f"  H2 within-load-decile spreads "
            + " ".join(
                f"{r['spread'] if r['spread'] is not None else 'na'}" for r in H2["within_decile"]
            )
        )
        print(
            f"     passing {H2['deciles_passing']}/10   raw r {H2['raw_corr_ds_gap']:+.3f}"
            f"   partial r|load {H2['partial_corr_ds_gap_given_load']:+.3f}"
            f"   G3 SURVIVES: {H2['H2_survives']}"
        )
        print(
            "  H3 ds_CC by band "
            + " ".join(f"{r['pct_lo']}-{r['pct_hi']}:{r['ds_cc']:+.3f}" for r in H3["bands"])
        )
        print(
            f"  H4 over-run at load pctl {H4['over_group_err_weighted_load_pctl']} vs "
            f"under-run {H4['under_group_err_weighted_load_pctl']} "
            f"(sep {H4['separation_pctl_points']})   TWO OBJECTS: {H4['H4_two_objects']}"
        )

    ys = rec["by_year"]
    rec["verdict"] = dict(
        H1_valid_all_years=all(ys[str(y)]["H1_anchor_validity"]["H1_valid"] for y in YEARS),
        H2_G3_survives_all_years=all(
            ys[str(y)]["H2_load_confound_control"]["H2_survives"] for y in YEARS
        ),
        H4_two_objects_all_years=all(ys[str(y)]["H4_two_objects"]["H4_two_objects"] for y in YEARS),
    )
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\n  VERDICT {json.dumps(rec['verdict'])}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    raise SystemExit(main())
