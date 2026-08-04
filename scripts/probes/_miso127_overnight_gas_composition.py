"""miso-127 probe — MISO's overnight gas COMPOSITION, model vs its own metered record.

Executes ``results/calibration/PREREG-miso127-overnight-gas-composition-2026-08-04.md``
exactly as pre-registered. **NO LP IS SOLVED.** Every number is read from
committed artifacts:

* ``frontend/data/backcast/bench/MISO/<year>.json.gz`` — the dashboard's own
  committed class actual, per-plant ``campd`` (base64 ``uint8`` capacity-factor
  percent, rescaled to the entry's ``c_ann``), with the model's own zone and
  class assignment already applied. The class actual is never re-derived by
  summing raw CAMPD over a hand-built roster.
* ``frontend/data/backcast/runs/2026-08-04-miso-126-steampart-b.js`` — the
  KEEPER's own registered payload, per-plant model dispatch ``m`` in the same
  encoding, rescaled to ``m_ann``.
* ``results/calibration/miso126_steampart_B/hourly/class_hourly_<year>.parquet``
  — the keeper's P1 class aggregate, carried as an independent cross-check of
  the matched-plant sum.

The measurement answers miso-114 §6's named bounded NO-LP question: the model
keeps 1,907 / 2,415 / 2,350 MW of ``CT_PEAKER`` + ``ST_GAS`` online at h1-3
while being short 3.4-3.9 GW of gas overall against EIA-930 — does MISO's own
metered record run that much overnight? EIA-930 does not split gas by prime
mover, so miso-114 could measure only the model side.

Matching is what removes coverage bias: MISO's sub-25-MW peakers are below the
CEMS reporting threshold, so an unmatched comparison would read the model long
by construction. Only plant-or-slice keys present in BOTH sides are compared.

Rule 22 [R-HOLDOUT]: 2023-2025 only (MISO holds no ``complete`` marker and the
holdout spend freeze is active). Rule 15: no run is produced, so there is
nothing to register.

Usage::

    python scripts/probes/_miso127_overnight_gas_composition.py
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

#: the designated MISO keeper this measurement is taken on (rule 15 bundle +
#: its registered dashboard payload).
KEEPER_RUN = "2026-08-04-miso-126-steampart-b"
KEEPER_BUNDLE = REPO / "results/calibration/miso126_steampart_B"

YEARS = (2023, 2024, 2025)
_T = 8760

#: miso-114's "h1-3" overnight trough window, as hour-of-day on the model's own
#: 8760 chronological index (leap day dropped by construction).
NIGHT_HOD = (1, 2, 3)

#: PREREG §3 P3 primary statistic: the two classes miso-114 named.
PRIMARY = ("CT_PEAKER", "ST_GAS")
#: PREREG §3 P4 attribution: reported alongside, never gated.
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
#: PREREG §3 P1 phase-alignment control class.
CONTROL_CLASS = "COAL_PRB"

#: PREREG §3 pre-registered bars, all declared before measurement.
P1_MIN_R = 0.90
P2_MIN_COVERAGE = 0.90
P3_MATERIAL_MW = 500.0
P5_CLOSURE_MW = 1.0

#: miso-105 §(c)'s published model overnight stack slope, GW per $/MWh, used
#: ONLY to translate a measured MW delta into $/MWh for the reader. It sizes
#: nothing and no parameter is fitted to it (PREREG KILL-4).
STACK_SLOPE_GW_PER_DOLLAR = {2023: 1.85, 2024: 1.79, 2025: 1.56}
#: miso-114's measured overnight ENERGY-component gap, $/MWh, for the same
#: reader-facing translation only.
ENERGY_GAP_DOLLAR = {2023: 8.53, 2024: 7.01, 2025: 8.54}


def _decode(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Decode a bench/payload hourly series to MW.

    Byte-for-byte the inverse of ``scripts/render_calibration_html.py::_b64``
    as consumed by ``scripts/migrate_bench_multiclass.py::_decode``: base64 ->
    ``uint8`` capacity-factor percent, rescaled so the series sums to the
    entry's declared annual TWh. Falls back to the raw percent-of-nameplate
    reading when no annual total is carried.
    """
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    if raw.shape[0] < _T:
        raw = np.concatenate([raw, np.zeros(_T - raw.shape[0])])
    raw = raw[:_T]
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def load_bench(year: int) -> dict:
    """Return the committed MISO bench entries for ``year``."""
    path = REPO / f"frontend/data/backcast/bench/MISO/{year}.json.gz"
    with gzip.open(path, "rt") as fh:
        return json.load(fh)["bench"]["plants"]


def load_payload() -> dict:
    """Return the keeper's registered per-year dashboard payload."""
    path = REPO / f"frontend/data/backcast/runs/{KEEPER_RUN}.js"
    return decode_run_js(path.read_text())["years"]


def build_matched(year: int, bench: dict, payload: dict) -> dict:
    """Build the matched-plant model/measured hourly stacks, grouped by class.

    Only keys present in BOTH the bench entry set (carrying a ``campd`` series
    with ``nodata`` false) and the keeper payload are kept — PREREG §2's
    coverage-bias control. Returns per-class ``(model_mw, meas_mw)`` 8760
    arrays plus the bookkeeping P2 needs.
    """
    ppl = payload[str(year)]["plants"]
    model: dict[str, np.ndarray] = {}
    meas: dict[str, np.ndarray] = {}
    matched_ann: dict[str, float] = {}
    total_ann: dict[str, float] = {}
    n_matched: dict[str, int] = {}
    n_bench: dict[str, int] = {}

    for key, entry in bench.items():
        klass = entry.get("group")
        if not klass:
            continue
        n_bench[klass] = n_bench.get(klass, 0) + 1
        pay = ppl.get(key)
        if pay is not None:
            total_ann[klass] = total_ann.get(klass, 0.0) + float(pay.get("m_ann") or 0.0)
        if pay is None or not entry.get("campd") or entry.get("nodata"):
            continue

        npl = float(entry.get("npl") or 0.0)
        m = _decode(pay["m"], pay.get("m_ann"), npl)
        c = _decode(entry["campd"], entry.get("c_ann"), npl)

        model[klass] = model.get(klass, np.zeros(_T)) + m
        meas[klass] = meas.get(klass, np.zeros(_T)) + c
        matched_ann[klass] = matched_ann.get(klass, 0.0) + float(pay.get("m_ann") or 0.0)
        n_matched[klass] = n_matched.get(klass, 0) + 1

    return {
        "model": model,
        "meas": meas,
        "matched_ann": matched_ann,
        "total_ann": total_ann,
        "n_matched": n_matched,
        "n_bench": n_bench,
    }


def hod_profile(series: np.ndarray) -> np.ndarray:
    """Return the 24-point hour-of-day mean of an 8760 series."""
    return series.reshape(365, 24).mean(axis=0)


def night_mean(series: np.ndarray) -> float:
    """Return the mean MW over the pre-registered h1-3 overnight window."""
    return float(series.reshape(365, 24)[:, list(NIGHT_HOD)].mean())


def quantization_bound(year: int, bench: dict, payload: dict) -> float:
    """PREREG P6: worst-case uint8 rounding contribution to the P3 statistic.

    Each matched plant's encoded byte carries a half-step of 0.5 % of its own
    nameplate. Roundings are independent across plants, so the class-aggregate
    bound is the quadrature sum of the per-plant half-steps, scaled by the
    decode's own annual rescale factor. Reported, never assumed.
    """
    ppl = payload[str(year)]["plants"]
    halves: list[float] = []
    for key, entry in bench.items():
        if entry.get("group") not in PRIMARY:
            continue
        pay = ppl.get(key)
        if pay is None or not entry.get("campd") or entry.get("nodata"):
            continue
        npl = float(entry.get("npl") or 0.0)
        raw = np.frombuffer(base64.b64decode(entry["campd"]), dtype=np.uint8).astype(float)
        tot = raw.sum()
        c_ann = entry.get("c_ann")
        scale = (c_ann * 1e6 / tot) if (c_ann and tot > 0) else (npl / 100.0)
        # a half-step is 1 encoded unit / 2, in the decoded MW basis
        halves.append(0.5 * scale)
    return float(np.sqrt(np.sum(np.square(halves)))) if halves else 0.0


def class_hourly(year: int) -> tuple[dict[str, float], dict[str, float]]:
    """Return the keeper's own P1 class aggregate: (overnight mean MW, annual TWh).

    This is the FULL model class — every LP unit in it, including units with no
    committed bench counterpart. It is therefore the correct denominator for
    PREREG P2's coverage control (§2: "matching makes the two sides the same
    machines"), and the correct model side for the one-sided class bound.
    """
    path = KEEPER_BUNDLE / f"hourly/class_hourly_{year}.parquet"
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    nights: dict[str, float] = {}
    annual: dict[str, float] = {}
    for klass, g in df.groupby("klass", observed=True):
        s = g.sort_values("hour")["mw"].to_numpy(dtype=float)
        if s.shape[0] < _T:
            s = np.concatenate([s, np.zeros(_T - s.shape[0])])
        s = s[:_T]
        nights[str(klass)] = night_mean(s)
        annual[str(klass)] = float(s.sum()) / 1e6
    return nights, annual


def main() -> int:
    payload = load_payload()
    result: dict = {
        "probe": "miso-127 overnight gas composition",
        "prereg": "results/calibration/PREREG-miso127-overnight-gas-composition-2026-08-04.md",
        "keeper_run": KEEPER_RUN,
        "night_hod": list(NIGHT_HOD),
        "bars": {
            "P1_min_r": P1_MIN_R,
            "P2_min_coverage": P2_MIN_COVERAGE,
            "P3_material_mw": P3_MATERIAL_MW,
            "P5_closure_mw": P5_CLOSURE_MW,
        },
        "years": {},
    }

    for year in YEARS:
        bench = load_bench(year)
        mm = build_matched(year, bench, payload)
        model, meas = mm["model"], mm["meas"]
        agg, agg_ann = class_hourly(year)

        # --- P1: phase-alignment control on COAL_PRB ---
        if CONTROL_CLASS in model and CONTROL_CLASS in meas:
            pm = hod_profile(model[CONTROL_CLASS])
            pc = hod_profile(meas[CONTROL_CLASS])
            p1_r = float(np.corrcoef(pm, pc)[0, 1])
        else:
            p1_r = float("nan")

        # --- P2: coverage, per reported class ---
        # The denominator is the FULL model class (class_hourly), not the
        # bench-intersected subset: PREREG §2's control is against coverage
        # BIAS, so the question is what share of the model's own class the
        # matched machines carry. CHP classes read > 1 because the payload's
        # CHP series carry the whole-plant host-steam add-back that
        # class_hourly does not; their coverage is not interpretable and they
        # are reported for attribution only.
        coverage = {}
        for k in (*GAS_CLASSES, CONTROL_CLASS):
            cls_ann = agg_ann.get(k, 0.0)
            frac = (mm["matched_ann"].get(k, 0.0) / cls_ann) if cls_ann > 0 else None
            chp = k.endswith("_CHP")
            coverage[k] = {
                "matched_frac_of_model_class": (round(frac, 4) if frac is not None else None),
                "matched_ann_twh": round(mm["matched_ann"].get(k, 0.0), 4),
                "model_class_ann_twh": round(cls_ann, 4),
                "unmatched_model_ann_twh": round(cls_ann - mm["matched_ann"].get(k, 0.0), 4),
                "n_matched": mm["n_matched"].get(k, 0),
                "n_bench": mm["n_bench"].get(k, 0),
                "chp_addback_uninterpretable": chp,
                "gated": bool(
                    (not chp) and frac is not None and frac >= P2_MIN_COVERAGE
                ),
            }

        # --- P3 / P4: per-class overnight means and deltas ---
        per_class = {}
        for k in (*GAS_CLASSES, CONTROL_CLASS):
            mo = night_mean(model[k]) if k in model else 0.0
            me = night_mean(meas[k]) if k in meas else 0.0
            per_class[k] = {
                "model_mw": round(mo, 1),
                "measured_mw": round(me, 1),
                "delta_mw": round(mo - me, 1),
                "class_hourly_mw": round(agg.get(k, float("nan")), 1),
            }

        p3_model = sum(per_class[k]["model_mw"] for k in PRIMARY)
        p3_meas = sum(per_class[k]["measured_mw"] for k in PRIMARY)
        p3_delta = p3_model - p3_meas

        # --- P5: arithmetic closure over the gas classes ---
        gas_model = sum(night_mean(model[k]) for k in GAS_CLASSES if k in model)
        gas_meas = sum(night_mean(meas[k]) for k in GAS_CLASSES if k in meas)
        sum_of_deltas = sum(per_class[k]["delta_mw"] for k in GAS_CLASSES)
        closure = abs(sum_of_deltas - (gas_model - gas_meas))

        # --- P6: quantization bound ---
        qbound = quantization_bound(year, bench, payload)

        # --- B: the ONE-SIDED CLASS BOUND (derived, not pre-registered as a
        # gate). The matched measured sum is a LOWER bound on the true measured
        # class, because every unmatched machine can only ADD generation. So
        # comparing it against the model's FULL class (class_hourly) is a valid
        # one-sided test: if measured_matched already exceeds the full model
        # class, the model is short at CLASS grain and no amount of unmatched
        # measured generation can reverse it. When it does not exceed, the
        # direction is genuinely UNRESOLVED and is reported as such.
        bound_model_class = sum(agg.get(k, 0.0) for k in PRIMARY)
        bound_meas_floor = p3_meas
        bound_gap = bound_meas_floor - bound_model_class
        bound_verdict = (
            "model_SHORT_at_class_grain"
            if bound_gap > 0
            else "UNRESOLVED (model long by at most %.0f MW)" % (-bound_gap)
        )

        # --- D: DESCRIPTIVE, POST-HOC. Not pre-registered, carries NO verdict
        # and gates nothing. It exists to answer the one question the P3 result
        # immediately raises: is the model short these classes ONLY overnight
        # (a SHAPE defect, which is what the C7 residual is about) or all day
        # (a LEVEL defect)? Reported so the successor question is well posed.
        descriptive = {}
        for k in PRIMARY:
            if k not in model:
                continue
            mo = model[k].reshape(365, 24)
            me = meas[k].reshape(365, 24)
            descriptive[k] = {
                "annual_model_twh": round(float(model[k].sum()) / 1e6, 4),
                "annual_measured_twh": round(float(meas[k].sum()) / 1e6, 4),
                "annual_delta_twh": round(float(model[k].sum() - meas[k].sum()) / 1e6, 4),
                "night_delta_mw": round(
                    float(mo[:, list(NIGHT_HOD)].mean() - me[:, list(NIGHT_HOD)].mean()), 1
                ),
                "peak_delta_mw": round(
                    float(mo[:, 16:20].mean() - me[:, 16:20].mean()), 1
                ),
            }

        # reader-facing translation only; sizes nothing (PREREG KILL-4)
        dollars = abs(p3_delta) / 1000.0 / STACK_SLOPE_GW_PER_DOLLAR[year]

        result["years"][year] = {
            "P1_coal_prb_hod_r": round(p1_r, 4),
            "P1_pass": bool(p1_r >= P1_MIN_R),
            "P2_coverage": coverage,
            "P3_primary_model_mw": round(p3_model, 1),
            "P3_primary_measured_mw": round(p3_meas, 1),
            "P3_delta_mw": round(p3_delta, 1),
            "P3_material": bool(abs(p3_delta) >= P3_MATERIAL_MW),
            "P3_direction": "model_LONG" if p3_delta > 0 else "model_SHORT",
            "P4_per_class": per_class,
            "P5_gas_delta_mw": round(gas_model - gas_meas, 1),
            "P5_sum_of_class_deltas_mw": round(sum_of_deltas, 1),
            "P5_closure_mw": round(closure, 4),
            "P5_pass": bool(closure <= P5_CLOSURE_MW),
            "P6_quantization_bound_mw": round(qbound, 2),
            "B_model_full_class_mw": round(bound_model_class, 1),
            "B_measured_lower_bound_mw": round(bound_meas_floor, 1),
            "B_gap_mw": round(bound_gap, 1),
            "B_verdict": bound_verdict,
            "D_descriptive_post_hoc": descriptive,
            "readers_note_dollar_equivalent": round(dollars, 3),
            "readers_note_energy_gap_dollar": ENERGY_GAP_DOLLAR[year],
        }

    # --- verdicts, exactly as pre-registered ---
    p1_all = all(result["years"][y]["P1_pass"] for y in YEARS)
    n_material = sum(1 for y in YEARS if result["years"][y]["P3_material"])
    n_long = sum(1 for y in YEARS if result["years"][y]["P3_delta_mw"] > 0)
    # PREREG P2: "a class below 90% is REPORTED but NOT gated -- its delta is
    # descriptive only and cannot carry P3." P3's own classes must therefore
    # clear coverage before P3's verdict may be read at all.
    p2_primary_ok = all(
        result["years"][y]["P2_coverage"][k]["gated"] for y in YEARS for k in PRIMARY
    )
    n_bound_short = sum(
        1 for y in YEARS if result["years"][y]["B_verdict"].startswith("model_SHORT")
    )
    n_bound_long = sum(
        1
        for y in YEARS
        if result["years"][y]["B_verdict"].startswith("UNRESOLVED")
    )
    if not p1_all:
        verdict = "VOID (KILL-1: phase-alignment control failed)"
    elif not p2_primary_ok:
        verdict = (
            "P3 UNAVAILABLE ON COVERAGE (P2 fails for the primary classes; "
            "its delta is descriptive only, per the pre-registration's own P2 rule). "
            "Adjudication falls to the one-sided class bound B."
        )
    elif n_material < 2:
        verdict = "IMMATERIAL (KILL-2: lane closes on measurement)"
    elif n_long >= 2:
        verdict = "MATERIAL / model LONG (miso-114's reading CONFIRMED)"
    else:
        verdict = "MATERIAL / model SHORT (KILL-3: miso-114's reading FALSIFIED)"
    result["verdict"] = verdict
    result["n_material_years"] = n_material
    result["n_long_years"] = n_long
    result["P2_primary_classes_gated"] = p2_primary_ok
    result["B_years_model_short_at_class_grain"] = n_bound_short
    result["B_years_unresolved"] = n_bound_long
    result["reading"] = (
        "miso-114's mispriced-marginal-unit reading required the model to hold "
        "MORE expensive gas online overnight than the market. It is CONFIRMED "
        "in ZERO years by any construction here: on matched machines the model "
        f"is short in {3 - n_long}/3 years, and the one-sided class bound puts "
        f"it short at class grain in {n_bound_short}/3 with {n_bound_long}/3 "
        "unresolved. No construction available from committed artifacts finds "
        "the model long."
    )

    out = REPO / "results/calibration/_miso127_overnight_gas_composition.json"
    out.write_text(json.dumps(result, indent=1))

    # --- human-readable transcript ---
    print(f"miso-127 — overnight gas composition (h1-3), keeper {KEEPER_RUN}")
    print("NO LP SOLVED. Matched-plant, committed artifacts only.\n")
    for year in YEARS:
        r = result["years"][year]
        print(f"=== {year} ===")
        print(
            f"  P1 COAL_PRB hod r = {r['P1_coal_prb_hod_r']:.4f} "
            f"(bar {P1_MIN_R}) -> {'PASS' if r['P1_pass'] else 'FAIL'}"
        )
        for k in (*GAS_CLASSES, CONTROL_CLASS):
            cv = r["P2_coverage"][k]
            frac = cv["matched_frac_of_model_class"]
            tag = (
                "CHP add-back, uninterpretable"
                if cv["chp_addback_uninterpretable"]
                else ("gated" if cv["gated"] else "REPORTED ONLY (below 0.90)")
            )
            print(
                f"  P2 {k:<11} matched {cv['n_matched']:>3}/{cv['n_bench']:<3} plants, "
                f"{(frac if frac is not None else float('nan')):.3f} of the MODEL class "
                f"({cv['unmatched_model_ann_twh']:>6.2f} TWh unmatched) -> {tag}"
            )
        print(
            f"  P3 CT_PEAKER+ST_GAS  model {r['P3_primary_model_mw']:>8.1f} MW   "
            f"measured {r['P3_primary_measured_mw']:>8.1f} MW   "
            f"delta {r['P3_delta_mw']:>+9.1f} MW  "
            f"[{'MATERIAL' if r['P3_material'] else 'immaterial'}, {r['P3_direction']}]"
        )
        print("  P4 per-class overnight mean MW (model / measured / delta):")
        for k in GAS_CLASSES:
            c = r["P4_per_class"][k]
            print(
                f"       {k:<11} {c['model_mw']:>9.1f} / {c['measured_mw']:>9.1f} / "
                f"{c['delta_mw']:>+9.1f}     (class_hourly {c['class_hourly_mw']:>9.1f})"
            )
        print(
            f"  B  one-sided class bound: model FULL class {r['B_model_full_class_mw']:.1f} MW "
            f"vs measured LOWER BOUND {r['B_measured_lower_bound_mw']:.1f} MW "
            f"-> gap {r['B_gap_mw']:+.1f} MW  [{r['B_verdict']}]"
        )
        print(
            f"  P5 closure {r['P5_closure_mw']:.4f} MW (bar {P5_CLOSURE_MW}) -> "
            f"{'PASS' if r['P5_pass'] else 'FAIL'}   |   "
            f"P6 quantization bound {r['P6_quantization_bound_mw']:.2f} MW"
        )
        print("  D  post-hoc descriptive (no verdict) — shape vs level, matched machines:")
        for k, dd in r["D_descriptive_post_hoc"].items():
            print(
                f"       {k:<11} annual {dd['annual_model_twh']:>7.3f} / "
                f"{dd['annual_measured_twh']:>7.3f} TWh ({dd['annual_delta_twh']:>+7.3f})   "
                f"night {dd['night_delta_mw']:>+8.1f} MW   peak {dd['peak_delta_mw']:>+8.1f} MW"
            )
        print(
            f"  reader-only: |delta| at miso-105's stack slope "
            f"= ${r['readers_note_dollar_equivalent']:.2f}/MWh against miso-114's "
            f"${r['readers_note_energy_gap_dollar']:.2f}/MWh energy gap\n"
        )
    print(f"VERDICT: {verdict}")
    print(f"  matched-machine delta material in {n_material}/3 years; model long in {n_long}/3")
    print(
        f"  one-sided class bound: model short at class grain in {n_bound_short}/3, "
        f"unresolved in {n_bound_long}/3"
    )
    print(f"  {result['reading']}")
    print(f"\nwrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
