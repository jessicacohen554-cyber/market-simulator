"""nyiso-211 phase 0 — attribute the Cricket Valley CC_REGULAR deficit to a lineage step.

Zero-LP. Reads ONLY artifacts already committed to ``main``:

* ``results/calibration/_nyiso186_cc_attribution.json`` — the pruned nyiso-186
  control's per-plant ``model_mwh`` plus its own CAMPD column
  (``campd_cc_gross_mwh``), the only surviving plant-grain model side for that
  anchor.
* ``frontend/data/backcast/runs/<run_id>.js`` — the model's per-plant annual and
  monthly energy (``m_ann`` / ``m_mon``) for the three committed keeper-lineage
  runs nyiso-192 / nyiso-196 / nyiso-202.
* ``frontend/data/backcast/bench/NYISO/<year>.json.gz`` — measured plant energy
  (``c_ann``, CAMPD), the basis used on BOTH sides in EVERY year.
* ``results/calibration/<bundle>/hourly/class_hourly_<year>.parquet`` — the
  bundle's own CC_REGULAR class total, for the payload reconciliation identity.

Every year read here is in-sample (2023, 2024, 2025); 2022 is not read at all
(rule 22). No solve, no screen, no bundle, no registration.

Pre-registration:
``results/calibration/PREREG-nyiso211-cricket-valley-lineage-attribution.md``
(committed and pushed at the branch tip before this file was written).

Run::

    uv run python scripts/probes/nyiso211_cricket_lineage_attribution.py
"""

from __future__ import annotations

import gzip
import json
import statistics
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KLASS = "CC_REGULAR"
PASS = "P1"
YEARS = (2023, 2024, 2025)

# The committed keeper lineage, oldest first. The nyiso-186 control's bundle and
# payload were pruned under rule 15 keeper-only retention; its per-plant model
# side survives only in the committed attribution record.
CONTROL_RECORD = ROOT / "results/calibration/_nyiso186_cc_attribution.json"
ANCHORS = (
    ("nyiso-186", None, None),
    ("nyiso-192", "2026-09-05-nyiso-192-astoria-panel", "nyiso192_astoria_panel"),
    ("nyiso-196", "2026-09-06-nyiso-196-extract-basis", "nyiso196_extract_basis"),
    ("nyiso-202", "2026-09-06-nyiso-202-startup-aware", "nyiso202_startup_aware"),
)
# PREREG §2.1: two of the three steps are a single live flag; the first is lumped.
STEPS = (
    ("d1", "nyiso-186", "nyiso-192", "LUMPED — several promotions, bundles pruned"),
    ("d2", "nyiso-192", "nyiso-196", "unit_outage_extract_basis_share: False -> True"),
    ("d3", "nyiso-196", "nyiso-202", "nyiso_gas_bridge_startup_aware: False -> True"),
)

BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
RUNS = ROOT / "frontend/data/backcast/runs"
BUNDLES = ROOT / "results/calibration"

TARGET = "57185"  # Cricket Valley Energy, Capital_Hudson, 1,312 MW npl
PARTNER = "56940"  # CPV Valley Energy Center — the other newest H-class unit
OVERRUNNERS = ("2539", "56196", "55375")  # Bethlehem, Zeltmann, Astoria Energy

# Pre-registered thresholds (PREREG §3). None is selected here.
I1_REL_TOL = 0.02
I2_REL_TOL = 0.05
DOMINANCE = 0.60
P4_CV_MAX = 0.35
P5_MOVE_TWH = 0.5
P6_CV_MAX = 0.35
P7_PARTNER_FRAC = 0.25
P8_CLASS_TWH = 0.5


# VOCABULARY. The committed bench and the run payloads share one key space, in
# which a plant that splits across groups is keyed ``<code>:<group>`` (2500 and
# 50292 in NYISO CC_REGULAR) and every other plant by its plain code. The
# nyiso-186 record keys every plant plainly, so its row for a split plant covers
# BOTH groups and is not comparable to a CC_REGULAR-only bench row. Those plants
# are therefore EXCLUDED from every nyiso-186 comparison and the exclusion is
# reported; bench and payload keys are never folded, because folding would add a
# split plant's CC_CHP energy into the CC_REGULAR class sum. Construction only;
# no threshold moved, and the five watched plants are plain-keyed everywhere.
def split_keyed(code: str) -> bool:
    """True if this bench key names one group of a plant that splits across groups."""
    return ":" in str(code)


# --------------------------------------------------------------------------- #
# measured side — CAMPD, one basis on both sides in every year (PREREG §2.2)
# --------------------------------------------------------------------------- #
def bench_campd(year: int) -> dict[str, dict]:
    """Measured CC_REGULAR plant energy (TWh, CAMPD) from the committed bench."""
    bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["plants"]
    return {
        code: {
            "name": bp.get("name"),
            "zone": bp.get("zone"),
            "npl_mw": bp.get("npl"),
            "campd_twh": float(bp.get("c_ann") or 0.0),
        }
        for code, bp in bench.items()
        if bp.get("group") == KLASS
    }


# --------------------------------------------------------------------------- #
# model side — one row per anchor
# --------------------------------------------------------------------------- #
def control_model(year: int) -> dict[str, dict]:
    """nyiso-186 control per-plant model energy plus its own CAMPD column."""
    rec = json.load(CONTROL_RECORD.open())["years"][str(year)]["plants"]

    def _twh(value: object) -> float | None:
        """The record carries nulls for plants with no measured counterpart."""
        return None if value is None else float(value) / 1e6

    return {
        str(p["plant"]): {
            "model_twh": _twh(p.get("model_mwh")),
            "campd_own_twh": _twh(p.get("campd_cc_gross_mwh")),
            "e923_own_twh": _twh(p.get("e923_cc_mwh")),
        }
        for p in rec
    }


def payload_model(run_id: str, year: int) -> dict[str, float]:
    """Per-plant model energy (TWh) from a committed run payload."""
    payload = decode_run_js((RUNS / f"{run_id}.js").read_text())
    plants = payload["years"][str(year)]["plants"]
    return {code: float(mp.get("m_ann") or 0.0) for code, mp in plants.items()}


def bundle_class_twh(bundle: str, year: int) -> float:
    """The bundle's own CC_REGULAR P1 class total (TWh) from class_hourly."""
    df = pd.read_parquet(BUNDLES / bundle / "hourly" / f"class_hourly_{year}.parquet")
    sel = df[(df["pass"] == PASS) & (df["klass"] == KLASS)]
    return float(sel["mw"].sum() / 1e6)


def _cv(values: list[float]) -> float | None:
    """Coefficient of variation (population stdev / |mean|); None if mean is 0."""
    mean = statistics.mean(values)
    if not mean:
        return None
    return statistics.pstdev(values) / abs(mean)


def main() -> None:
    campd = {y: bench_campd(y) for y in YEARS}
    ctrl = {y: control_model(y) for y in YEARS}
    pay = {
        name: {y: payload_model(run_id, y) for y in YEARS}
        for name, run_id, _ in ANCHORS
        if run_id
    }

    # ---- I1: the 186 anchor's measured side is the bench's ------------------
    i1_rows, i1_worst, i1_nocol = [], 0.0, 0
    i1_split = sorted({c for y in YEARS for c in campd[y] if split_keyed(c)})
    for y in YEARS:
        for code, c in ctrl[y].items():
            b = campd[y].get(code)
            if b is None:
                continue
            own, ben = c["campd_own_twh"], b["campd_twh"]
            if own is None:
                i1_nocol += 1
                continue
            rel = abs(own - ben) / own if own else float("inf")
            i1_worst = max(i1_worst, rel)
            if rel > I1_REL_TOL:
                i1_rows.append(
                    {
                        "year": y,
                        "plant": code,
                        "name": b["name"],
                        "bench_campd_twh": round(ben, 4),
                        "record_campd_twh": round(own, 4),
                        "rel": round(rel, 4),
                    }
                )
    i1 = {
        "tol": I1_REL_TOL,
        "worst_rel": round(i1_worst, 4),
        "n_violations": len(i1_rows),
        "n_record_rows_without_campd_column": i1_nocol,
        "split_keyed_plants_excluded_from_186_anchor": i1_split,
        "violations": i1_rows[:20],
        "PASS": not i1_rows,
    }

    # ---- I2: payload plant sum vs the bundle's own class total --------------
    i2_rows = []
    for name, run_id, bundle in ANCHORS:
        if not run_id:
            continue
        for y in YEARS:
            # Sum only the CC_REGULAR plants the bench identifies, to match the
            # class scope; the class_hourly total is the same class.
            psum = sum(pay[name][y].get(code, 0.0) for code in campd[y])
            cls = bundle_class_twh(bundle, y)
            rel = abs(psum - cls) / cls if cls else float("inf")
            i2_rows.append(
                {
                    "anchor": name,
                    "year": y,
                    "payload_plant_sum_twh": round(psum, 4),
                    "class_hourly_twh": round(cls, 4),
                    "rel": round(rel, 4),
                    "PASS": bool(rel <= I2_REL_TOL),
                }
            )
    i2 = {"tol": I2_REL_TOL, "rows": i2_rows, "PASS": all(r["PASS"] for r in i2_rows)}

    # ---- the per-plant, per-anchor gap table (CAMPD basis both sides) -------
    def gap(anchor: str, code: str, year: int) -> float | None:
        meas = campd[year].get(code)
        if meas is None:
            return None
        if anchor == "nyiso-186":
            c = ctrl[year].get(code)
            return None if c is None else c["model_twh"] - meas["campd_twh"]
        return pay[anchor][year].get(code, 0.0) - meas["campd_twh"]

    def model(anchor: str, code: str, year: int) -> float | None:
        if anchor == "nyiso-186":
            c = ctrl[year].get(code)
            return None if c is None else c["model_twh"]
        return pay[anchor][year].get(code)

    watch = (TARGET, PARTNER) + OVERRUNNERS
    for y in YEARS:
        raw = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        for code in watch:
            assert code in raw, f"watch plant {code} is not plain-keyed in bench {y}"
    table: dict[str, dict] = {}
    for code in watch:
        meta = next(
            (campd[y][code] for y in YEARS if code in campd[y]),
            {"name": None, "zone": None, "npl_mw": None},
        )
        per_year = {}
        for y in YEARS:
            gaps = {a: gap(a, code, y) for a, _, _ in ANCHORS}
            models = {a: model(a, code, y) for a, _, _ in ANCHORS}
            deltas = {}
            for key, lo, hi, _ in STEPS:
                a, b = gaps[lo], gaps[hi]
                deltas[key] = None if (a is None or b is None) else round(b - a, 4)
            total = (
                None
                if (gaps["nyiso-186"] is None or gaps["nyiso-202"] is None)
                else round(gaps["nyiso-202"] - gaps["nyiso-186"], 4)
            )
            per_year[y] = {
                "campd_twh": round(campd[y][code]["campd_twh"], 4)
                if code in campd[y]
                else None,
                "model_twh": {a: (None if v is None else round(v, 4)) for a, v in models.items()},
                "gap_twh": {a: (None if v is None else round(v, 4)) for a, v in gaps.items()},
                "step_delta_twh": deltas,
                "total_delta_twh": total,
            }
        table[code] = {**meta, "years": per_year}

    # ---- P1 / P2 / P3: attribution on 57185, 2023 --------------------------
    d2023 = table[TARGET]["years"][2023]["step_delta_twh"]
    have_all = all(v is not None for v in d2023.values())
    S = sum(abs(v) for v in d2023.values()) if have_all else None
    shares = (
        {k: round(abs(v) / S, 4) for k, v in d2023.items()} if have_all and S else {}
    )
    p1 = bool(have_all and S and shares.get("d2", 0) >= DOMINANCE and d2023["d2"] < 0)
    p2 = bool(have_all and S and shares.get("d1", 0) >= DOMINANCE)
    d3_dominant = bool(have_all and S and shares.get("d3", 0) >= DOMINANCE)
    p3 = bool(have_all and not p1 and not p2)
    verdict = (
        "P1 (unit_outage_extract_basis_share dominant)"
        if p1
        else "P2 (upstream of nyiso-192)"
        if p2
        else "P3 (diffuse)"
    )

    # ---- PREREG §3.1 I1-failure fallback: the payload-only lineage ----------
    # Declared consequence of an I1 failure: Delta_1 is not comparable, so the
    # attribution is reported on 192 -> 196 -> 202, where both steps are single
    # live flags and both anchors share one key space and one measured side.
    fallback = {}
    for y in YEARS:
        d = table[TARGET]["years"][y]["step_delta_twh"]
        s_pay = abs(d["d2"]) + abs(d["d3"])
        g = table[TARGET]["years"][y]["gap_twh"]
        fallback[y] = {
            "d2_twh": d["d2"],
            "d3_twh": d["d3"],
            "d2_share_of_payload_movement": round(abs(d["d2"]) / s_pay, 4)
            if s_pay
            else None,
            "gap_before_d2_twh": g["nyiso-192"],
            "gap_after_d2_twh": g["nyiso-196"],
            "sign_flips_at_d2": bool(
                g["nyiso-192"] is not None
                and g["nyiso-196"] is not None
                and g["nyiso-192"] >= 0
                and g["nyiso-196"] < 0
            ),
        }

    # ---- P4: the repair is year-flat while the deficit grows ---------------
    d2_by_year = [table[TARGET]["years"][y]["step_delta_twh"]["d2"] for y in YEARS]
    d2_cv = _cv(d2_by_year) if all(v is not None for v in d2_by_year) else None
    keeper_gap = [table[TARGET]["years"][y]["gap_twh"]["nyiso-202"] for y in YEARS]
    grows = all(
        keeper_gap[i] is not None
        and keeper_gap[i + 1] is not None
        and abs(keeper_gap[i + 1]) > abs(keeper_gap[i])
        for i in range(len(keeper_gap) - 1)
    )
    p4 = bool(d2_cv is not None and d2_cv <= P4_CV_MAX and grows)

    # ---- P5: the lineage did not move the persistent over-runners ----------
    p5_rows = [
        {
            "plant": c,
            "name": table[c]["name"],
            "total_delta_2023_twh": table[c]["years"][2023]["total_delta_twh"],
        }
        for c in OVERRUNNERS
    ]
    p5 = all(
        r["total_delta_2023_twh"] is not None
        and abs(r["total_delta_2023_twh"]) < P5_MOVE_TWH
        for r in p5_rows
    )

    # ---- P7: does CPV Valley move with Cricket Valley at d2? ---------------
    d2_t = table[TARGET]["years"][2023]["step_delta_twh"]["d2"]
    d2_p = table[PARTNER]["years"][2023]["step_delta_twh"]["d2"]
    p7 = (
        None
        if (d2_t is None or d2_p is None or not d2_t)
        else bool(abs(d2_p) <= P7_PARTNER_FRAC * abs(d2_t))
    )

    # ---- P8: class-grain redistribution vs level ---------------------------
    def class_gap(anchor: str, year: int) -> float | None:
        """Class-grain gap over the plants COMPARABLE at this anchor.

        The nyiso-186 anchor cannot see a split-keyed plant's CC_REGULAR half,
        so its comparison set drops those plants; the payload anchors are
        reported on BOTH sets so the exclusion's size is visible.
        """
        codes = [c for c in campd[year] if not split_keyed(c)]
        meas = sum(campd[year][c]["campd_twh"] for c in codes)
        if anchor == "nyiso-186":
            m = sum(
                (ctrl[year].get(c) or {}).get("model_twh") or 0.0 for c in codes
            )
        else:
            m = sum(pay[anchor][year].get(c, 0.0) for c in codes)
        return m - meas

    def class_gap_full(anchor: str, year: int) -> float | None:
        """Class-grain gap over EVERY bench plant; undefined at the 186 anchor."""
        if anchor == "nyiso-186":
            return None
        meas = sum(v["campd_twh"] for v in campd[year].values())
        return sum(pay[anchor][year].get(c, 0.0) for c in campd[year]) - meas

    p8_rows = {
        y: {
            "gap_twh": {
                a: round(class_gap(a, y), 4) for a, _, _ in ANCHORS
            },
            "gap_full_set_twh": {
                a: (None if class_gap_full(a, y) is None else round(class_gap_full(a, y), 4))
                for a, _, _ in ANCHORS
            },
            "total_delta_twh": round(class_gap("nyiso-202", y) - class_gap("nyiso-186", y), 4),
        }
        for y in YEARS
    }
    p8 = abs(p8_rows[2023]["total_delta_twh"]) <= P8_CLASS_TWH

    out = {
        "session": "nyiso-211",
        "prereg": "results/calibration/PREREG-nyiso211-cricket-valley-lineage-attribution.md",
        "basis": "CAMPD (bench c_ann) on both sides in every year; E-923 not used",
        "years": list(YEARS),
        "anchors": [{"name": n, "run_id": r, "bundle": b} for n, r, b in ANCHORS],
        "steps": [{"key": k, "from": a, "to": b, "flag": f} for k, a, b, f in STEPS],
        "I1_control_measured_basis": i1,
        "I2_payload_reconciliation": i2,
        "plant_table": table,
        "P1_P2_P3_attribution_57185_2023": {
            "step_delta_twh": d2023,
            "S_abs_sum_twh": None if S is None else round(S, 4),
            "shares": shares,
            "dominance_bar": DOMINANCE,
            "P1_fires": p1,
            "P2_fires": p2,
            "P3_fires": p3,
            "d3_dominant_note": d3_dominant,
            "verdict": verdict,
        },
        "PREREG_I1_fallback_payload_only_lineage": {
            "why": "I1 failed, so PREREG §3.1 voids Delta_1's comparability; "
            "192 -> 196 -> 202 is the declared fallback",
            "by_year": fallback,
        },
        "P4_repair_flat_while_deficit_grows": {
            "d2_by_year_twh": d2_by_year,
            "d2_cv": None if d2_cv is None else round(d2_cv, 4),
            "cv_bar": P4_CV_MAX,
            "keeper_gap_by_year_twh": keeper_gap,
            "deficit_grows_monotonically": grows,
            "P4_fires": p4,
        },
        "P5_overrunner_control": {"bar_twh": P5_MOVE_TWH, "rows": p5_rows, "P5_holds": p5},
        "P7_partner_move": {
            "d2_57185_twh": d2_t,
            "d2_56940_twh": d2_p,
            "frac_bar": P7_PARTNER_FRAC,
            "plant_specific_reading": p7,
        },
        "P8_class_grain": {"bar_twh": P8_CLASS_TWH, "rows": p8_rows, "P8_holds": p8},
    }

    dest = ROOT / "results/calibration/_nyiso211_cricket_lineage_attribution.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["I1_control_measured_basis"], indent=1))
    print(json.dumps(out["I2_payload_reconciliation"], indent=1))
    print(json.dumps(out["P1_P2_P3_attribution_57185_2023"], indent=1))
    print(json.dumps(out["PREREG_I1_fallback_payload_only_lineage"], indent=1))
    print(json.dumps(out["P4_repair_flat_while_deficit_grows"], indent=1))
    print(json.dumps(out["P5_overrunner_control"], indent=1))
    print(json.dumps(out["P7_partner_move"], indent=1))
    print(json.dumps(out["P8_class_grain"], indent=1))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
