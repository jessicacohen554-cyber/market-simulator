"""miso-132(b) A/B scorer — the CC committed-band MEASURED RE-GROUNDING on the MISO keeper.

Scores the single-mechanism arm ``results/calibration/miso132_ccmin_B``
(``CC_REGULAR.committed`` 1.20 → 1.005 and ``CC_INTERMEDIATE.committed``
0.92 → 1.005, the measured ``avg_committed_p50``) against
``results/calibration/miso132_ccmin_A``, the same-HEAD ZERO-DELTA control replay of
the keeper ``2026-08-04-miso-127-onlinepmin``.

NO LP IS SOLVED HERE — every number is read from the committed bundles.

Every delta is quoted against **arm A**, never against the committed keeper
(miso-124 DO-NOT-MISREAD: the price response is not stable across keepers).

Gates, in the pre-registered order
(``results/calibration/PREREG-miso132b-cc-committed-band-regrounding-2026-08-05.md`` §3):

K0  control integrity  — arm A must reproduce the INCUMBENT keeper's scorecard AND
                         its committed hourly sidecars (caiso-146 found a zero-delta
                         control diverging by GW on a class-hour, so this is measured).
K1  band fidelity      — arm A carries the registered 1.20 / 0.92, arm B the measured
                         1.005 / 1.005, both visible in ``run_config.json`` (rule 26).
K2  single mechanism   — the two scenario blocks differ ONLY inside
                         ``offer_curve_by_group``, and only in the two ``committed``
                         entries.
K3  year span          — both bundles ``[2023, 2024, 2025]`` (rules 16 / 22).
K4  liveness (grain 2) — per-class ENERGY deltas are the magnitude of record
                         (miso-122 DO-NOT-MISREAD: ``max_abs_class_hour_mw`` is NOT a
                         mechanism magnitude at MISO). Bar: |d CC class energy| >
                         0.05 TWh in >= 1 year. A null is a WIRING DEFECT to find,
                         not an ``I`` verdict — the pre-check already measured the
                         bands' capacity.
K5  C1 16/16           — the C1 criterion must stay 16/16.
K6  COAL_BIT no-overshoot — the miso-102 signature: COAL_BIT off-peak cv_ratio must
                         not exceed 1.60, and its C7 status must not regress.
K7  full balance       — the FULL identity, not the class sidecar (miso-126 §6):
                         ``d_class + d_discharge - d_charge + d_slack - d_dump
                         - d_demand == 0``.
K8  R_tot floor 0.90   — the miso-131 P3 convention. COAL_PRB ``R_tot`` >= 0.90 in
                         all three years: a cv_ratio gain bought by inflating raw
                         off-peak dispersion is not the organisation fix claimed.
                         Requires both arms' dashboard payloads (the D-1 matched
                         frame), so it is scored AFTER registration.
K9  no forced energy   — the arm changes a PRICE, not a floor: no new D-2 forcing
                         id, no class's forced share rising.

TARGET (reported whichever way it goes, prereg §3): C7 ``COAL_PRB`` ``cv_ratio`` via
``R_dfrac`` — quote ``R_dfrac``, NEVER raw variance (miso-128 DO-NOT-MISREAD) —
with the July-night price bias and the miso-130 freeze channel alongside.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only. Writes
``results/calibration/_miso132b_cc_committed_ab.json``.
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

INCUMBENT = REPO / "results/calibration/miso127_onlinepmin_B"
ARM_A = REPO / "results/calibration/miso132_ccmin_A"
ARM_B = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso132b_cc_committed_ab.json"
YEARS = (2023, 2024, 2025)

REGROUND_CLASSES = ("CC_REGULAR", "CC_INTERMEDIATE")
MEASURED_COMMITTED = 1.005
REGISTERED_BEFORE = {"CC_REGULAR": 1.20, "CC_INTERMEDIATE": 0.92}

#: Prereg K4 grain-2 bar: |d CC class energy| must exceed this in >= 1 year.
GRAIN2_TWH = 0.05
#: D-1 gate (scripts/legitimacy_diagnostics.D1_MIN_CV_RATIO).
CV_RATIO_GATE = 0.5
#: Prereg K6 bar — the miso-102 COAL_BIT overshoot signature.
COAL_BIT_CV_CEILING = 1.60
#: Prereg K8 bar — the miso-131 P3 convention.
R_TOT_FLOOR = 0.90

MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MONTH_OF_HOUR = np.concatenate(
    [np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)]
)
HOD = np.tile(np.arange(24), 365)
JULY_NIGHT = (MONTH_OF_HOUR == 7) & (HOD <= 5)


def _scenario(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _classes(bundle: Path, year: int) -> pd.DataFrame:
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return (
        c[c["pass"] == "P1"]
        .pivot_table(index="hour", columns="klass", values="mw")
        .sort_index()
    )


def _system(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return (
        s.pivot_table(index="hour", columns="zone", values="price").sort_index(),
        s.pivot_table(index="hour", columns="zone", values="demand").sort_index(),
    )


def _balance(year: int) -> dict:
    """Full supply/demand energy-balance delta between the two arms, in GWh."""

    def totals(bundle: Path) -> dict[str, float]:
        c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
        s = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
        q = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        c, s, q = c[c["pass"] == "P1"], s[s["pass"] == "P1"], q[q["pass"] == "P1"]
        return {
            "class": float(c["mw"].sum()) / 1e3,
            "discharge": float(s["discharge_mw"].sum()) / 1e3,
            "charge": float(s["charge_mw"].sum()) / 1e3,
            "slack": float(q["slack"].sum()) / 1e3,
            "dump": float(q["dump"].sum()) / 1e3,
            "demand": float(q["demand"].sum()) / 1e3,
        }

    a, b = totals(ARM_A), totals(ARM_B)
    d = {k: b[k] - a[k] for k in a}
    residual = (
        d["class"] + d["discharge"] - d["charge"] + d["slack"] - d["dump"] - d["demand"]
    )
    return {
        "class_delta_gwh": round(d["class"], 6),
        "discharge_delta_gwh": round(d["discharge"], 6),
        "charge_delta_gwh": round(d["charge"], 6),
        "slack_delta_gwh": round(d["slack"], 6),
        "dump_delta_gwh": round(d["dump"], 6),
        "demand_delta_gwh": round(d["demand"], 6),
        "residual_gwh": round(residual, 6),
    }


def _diagnostic_verdicts(bundle: Path) -> dict:
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {}
    diags = json.loads(path.read_text()).get("diagnostics", {})
    out: dict[str, str] = {}
    for block, payload in diags.items():
        rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or "verdict" not in row:
                continue
            key = "|".join(
                str(row.get(f))
                for f in ("year", "klass", "class", "mechanism", "driver", "check")
                if f in row
            )
            out[f"{block}:{key}"] = str(row["verdict"])
    return out


def _rows(bundle: Path, block: str) -> list[dict]:
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return []
    diags = json.loads(path.read_text()).get("diagnostics", {})
    for name, payload in diags.items():
        if name.replace("-", "") != block.replace("-", ""):
            return payload.get("rows", []) if isinstance(payload, dict) else payload
    return (diags.get(block, {}) or {}).get("rows", [])


def _d1_rows(bundle: Path, klass: str) -> dict[str, dict]:
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {}
    diags = json.loads(path.read_text()).get("diagnostics", {})
    out: dict[str, dict] = {}
    for block, payload in diags.items():
        if not isinstance(payload, dict) or block.replace("-", "") != "D1":
            continue
        for row in payload.get("rows", []):
            if row.get("class") == klass:
                out[str(row.get("year"))] = row
    return out


def _d2_forced(bundle: Path) -> dict:
    """Per (year, class) forced share and the set of forcing mechanism ids."""
    out: dict[str, dict] = {}
    ids: set[str] = set()
    for row in _rows(bundle, "D2"):
        if not isinstance(row, dict):
            continue
        key = f"{row.get('year')}|{row.get('class') or row.get('klass')}"
        mech = row.get("mechanism") or row.get("driver")
        if mech:
            ids.add(str(mech))
        share = row.get("forced_share")
        if share is None:
            share = row.get("forced_pct")
        if share is not None:
            prev = out.get(key, {}).get("forced_share")
            out[key] = {
                "forced_share": max(float(share), prev) if prev is not None
                else float(share)
            }
    return {"by_class_year": out, "mechanism_ids": sorted(ids)}


def _scorecard(bundle: Path) -> dict:
    path = bundle / "metrics.json"
    if not path.exists():
        return {"determination": None, "criteria": {}, "caveats": None}
    m = json.loads(path.read_text())
    return {
        "determination": m.get("determination"),
        "criteria": {
            k: (v or {}).get("status") for k, v in (m.get("criteria") or {}).items()
        },
        "criteria_detail": m.get("criteria") or {},
        "caveats": sorted(m.get("caveats") or []),
    }


def _c1_fraction(card: dict) -> str | None:
    """The C1 '16/16'-style sub-check tally, wherever the scorecard records it."""
    c1 = (card.get("criteria_detail") or {}).get("C1") or {}
    for key in ("detail", "summary", "note", "value", "score"):
        v = c1.get(key)
        if isinstance(v, str) and "/" in v:
            return v
    passed, total = c1.get("n_pass"), c1.get("n_total")
    if passed is not None and total is not None:
        return f"{passed}/{total}"
    return None


def _rdfrac(bundle_payload_id: str, year: int) -> dict | None:
    """COAL_PRB R_tot / R_dfrac / R_level via the miso-128 decomposition.

    Uses the D-1 MATCHED frame (bench x dashboard payload), which is why it runs
    only after both arms are registered. Returns ``None`` when the payload is
    absent so the scorer degrades to a reported gap rather than a crash.
    """
    try:
        from probes import _miso128_c7_diurnal_organization as M128
    except Exception:
        return None
    sidecar = (
        REPO / "frontend/data/backcast/registry" / f"{bundle_payload_id}.json"
    )
    if not sidecar.exists():
        return None
    try:
        bench, model = M128.load_sides(year, json.loads(sidecar.read_text()))
        keys = M128.matched_keys(bench, model, "COAL_PRB")
        if not keys:
            return None
        m = M128.class_series(keys, lambda k: model[k])
        a = M128.class_series(keys, lambda k: bench[k]["mw"])
        d = M128.decompose(m, a)
        return {
            "R_tot": d["R_tot"],
            "R_dfrac": d["R_dfrac"],
            "R_level": d["R_level"],
            "cv_ratio": d["cv_ratio"],
            "n_matched_plants": len(keys),
        }
    except Exception as exc:  # pragma: no cover — reported, never fatal
        return {"error": f"{type(exc).__name__}: {exc}"}


def main() -> None:  # noqa: C901 — one linear gate sequence, kept together
    sa, sb = _scenario(ARM_A), _scenario(ARM_B)
    diff = {
        k: (sa.get(k), sb.get(k)) for k in set(sa) | set(sb) if sa.get(k) != sb.get(k)
    }
    ma = json.loads((ARM_A / "meta.json").read_text())
    mb = json.loads((ARM_B / "meta.json").read_text())
    payload_ids = json.loads(
        (REPO / "results/calibration/_miso132b_run_ids.json").read_text()
    ) if (REPO / "results/calibration/_miso132b_run_ids.json").exists() else {}

    res: dict = {
        "session": "miso-132(b)",
        "prereg": (
            "results/calibration/"
            "PREREG-miso132b-cc-committed-band-regrounding-2026-08-05.md"
        ),
        "incumbent_keeper": {
            "bundle": INCUMBENT.name,
            "run_id": "2026-08-04-miso-127-onlinepmin",
        },
        "arm_A": {"bundle": ARM_A.name, "delta": "none (same-HEAD zero-delta control)"},
        "arm_B": {
            "bundle": ARM_B.name,
            "delta": (
                "offer_curve_by_group CC_REGULAR.committed 1.20 -> 1.005 and "
                "CC_INTERMEDIATE.committed 0.92 -> 1.005"
            ),
        },
        "mechanism": {
            "what": (
                "rule-14 [R-ACCURATE] proxy-for-measurand swap: both CC committed "
                "(min-stable-load) bands take the fleet's OWN measured min-load "
                "block-average burn, avg_committed_p50 = 1.005 (n=103 CC units, "
                "cap-weighted, miso_campd_marginal_hr_summary.csv), replacing a "
                "generic part-load-premium claim (1.20) and a generic default "
                "(0.92) that backcast_config.py itself calls 'an unphysical, "
                "artificially-cheap min-load block'. ZERO free parameters."
            ),
            "both_cohorts_note": (
                "Both keys move together deliberately: moving only CC_REGULAR "
                "(cheaper) or only CC_INTERMEDIATE (dearer) would be CHOOSING the "
                "direction — the forbidden path. One measurand, one mechanism."
            ),
        },
    }

    # ---- K0: control integrity --------------------------------------------
    inc, ctl = _scorecard(INCUMBENT), _scorecard(ARM_A)
    sidecar_max = {}
    for year in YEARS:
        try:
            ci, cc = _classes(INCUMBENT, year), _classes(ARM_A, year)
            cc = cc.reindex(columns=ci.columns, fill_value=0.0)
            sidecar_max[str(year)] = float(np.abs((cc - ci).to_numpy()).max())
        except FileNotFoundError:
            sidecar_max[str(year)] = None
    scorecard_same = (
        inc["determination"] == ctl["determination"]
        and inc["criteria"] == ctl["criteria"]
        and inc["caveats"] == ctl["caveats"]
    )
    res["K0_control_integrity"] = {
        "incumbent": {k: inc[k] for k in ("determination", "criteria", "caveats")},
        "control": {k: ctl[k] for k in ("determination", "criteria", "caveats")},
        "scorecard_identical": scorecard_same,
        "max_abs_class_hour_mw_vs_incumbent": sidecar_max,
        "note": (
            "A non-zero sidecar delta is a HEAD-drift finding about the incumbent "
            "bundle, NOT a result of this session's mechanism, and is reported as "
            "such (caiso-146)."
        ),
        "verdict": "PASS" if scorecard_same else "FAIL",
    }

    # ---- K1 / K2 / K3 ------------------------------------------------------
    oc_a = (sa.get("offer_curve_by_group") or {})
    oc_b = (sb.get("offer_curve_by_group") or {})
    bands = {
        cls: {
            "arm_A": (oc_a.get(cls) or {}).get("committed"),
            "arm_B": (oc_b.get(cls) or {}).get("committed"),
            "registered_before": REGISTERED_BEFORE[cls],
            "measured": MEASURED_COMMITTED,
        }
        for cls in REGROUND_CLASSES
    }
    k1_ok = all(
        abs(float(v["arm_A"]) - v["registered_before"]) < 1e-9
        and abs(float(v["arm_B"]) - MEASURED_COMMITTED) < 1e-9
        for v in bands.values()
        if v["arm_A"] is not None and v["arm_B"] is not None
    ) and len(bands) == len(REGROUND_CLASSES)
    res["K1_band_fidelity"] = {"bands": bands, "verdict": "PASS" if k1_ok else "FAIL"}

    # The only differing scenario key must be offer_curve_by_group, and inside it
    # only the two committed entries.
    band_diff: dict[str, dict] = {}
    for cls in sorted(set(oc_a) | set(oc_b)):
        a_bands, b_bands = oc_a.get(cls) or {}, oc_b.get(cls) or {}
        for band in sorted(set(a_bands) | set(b_bands)):
            if a_bands.get(band) != b_bands.get(band):
                band_diff.setdefault(cls, {})[band] = [
                    a_bands.get(band), b_bands.get(band)
                ]
    expected = {cls: {"committed"} for cls in REGROUND_CLASSES}
    single = list(diff) == ["offer_curve_by_group"] and {
        c: set(b) for c, b in band_diff.items()
    } == expected
    res["K2_single_mechanism"] = {
        "differing_scenario_keys": sorted(diff),
        "offer_curve_band_diff": band_diff,
        "verdict": "PASS" if single else "FAIL",
    }
    res["K3_year_span"] = {
        "arm_A_years": ma.get("years"),
        "arm_B_years": mb.get("years"),
        "verdict": "PASS"
        if ma.get("years") == mb.get("years") == [2023, 2024, 2025]
        else "FAIL",
    }

    # ---- K4 / K7: liveness and the full balance ---------------------------
    max_dmw, max_dlmp, d_sys, energy, price_hours = {}, {}, {}, {}, {}
    cc_energy, net_energy, balance, night = {}, {}, {}, {}
    for year in YEARS:
        ca, cb = _classes(ARM_A, year), _classes(ARM_B, year)
        cb = cb.reindex(columns=ca.columns, fill_value=0.0)
        d = cb - ca
        pa, dem = _system(ARM_A, year)
        pb, _ = _system(ARM_B, year)
        zc = [c for c in pa.columns if str(c).startswith("MISO")]
        dl = (pb[zc] - pa[zc]).to_numpy()

        max_dmw[str(year)] = float(np.abs(d.to_numpy()).max())
        max_dlmp[str(year)] = float(np.abs(dl).max())
        wa = (pa[zc] * dem[zc]).sum(axis=1) / dem[zc].sum(axis=1)
        wb = (pb[zc] * dem[zc]).sum(axis=1) / dem[zc].sum(axis=1)
        d_sys[str(year)] = float((wb - wa).mean())
        energy[str(year)] = {
            k: round(float(v) / 1e3, 6) for k, v in d.sum().items() if abs(v) > 1e-6
        }  # GWh
        cc_energy[str(year)] = {
            k: round(float(d[k].sum()) / 1e6, 6)  # TWh
            for k in ("CC_REGULAR", "CC_CHP")
            if k in d.columns
        }
        net_energy[str(year)] = round(float(d.to_numpy().sum()) / 1e3, 6)
        price_hours[str(year)] = {
            "hours_with_any_zonal_delta": int((np.abs(dl).max(axis=1) > 1e-9).sum()),
            "zone_hours_price_rose": int((dl > 1e-9).sum()),
            "zone_hours_price_fell": int((dl < -1e-9).sum()),
        }
        balance[str(year)] = _balance(year)
        # The mechanism's own channel: the July-night level the miso-130 freeze
        # statistic keys on.
        na = wa.to_numpy()[:8760][JULY_NIGHT]
        nb = wb.to_numpy()[:8760][JULY_NIGHT]
        night[str(year)] = {
            "july_night_lw_price_A": float(na.mean()),
            "july_night_lw_price_B": float(nb.mean()),
            "d_july_night_lw_price": float(nb.mean() - na.mean()),
            "d_july_night_p10": float(
                np.percentile(nb, 10) - np.percentile(na, 10)
            ),
        }

    cc_total_twh = {y: round(sum(v.values()), 6) for y, v in cc_energy.items()}
    grain2_live = any(abs(v) > GRAIN2_TWH for v in cc_total_twh.values())
    res["K4_liveness_grain2"] = {
        "cc_class_energy_delta_twh": cc_energy,
        "cc_total_delta_twh": cc_total_twh,
        "class_energy_delta_gwh": energy,
        "max_abs_class_hour_mw": max_dmw,
        "max_abs_class_hour_mw_note": (
            "NOT a mechanism magnitude at MISO (miso-122 DO-NOT-MISREAD). Read "
            "cc_class_energy_delta_twh."
        ),
        "max_zonal_abs_dlmp": max_dlmp,
        "d_system_lw_price_usd_mwh": d_sys,
        "price_delta_hours": price_hours,
        "grain2_bar_twh": GRAIN2_TWH,
        "wiring_note": (
            "offer_curve_overrides deep-merges into config.offer_curve_by_group "
            "and the RESOLVED curve is recorded in run_config.json, so K1 already "
            "proves the band reached the config. A dead grain 2 with K1 PASS is a "
            "downstream wiring defect to find (miso-126 §4), not an I verdict."
        ),
        "verdict": "LIVE" if grain2_live else "INERT",
    }
    res["max_zonal_abs_dlmp"] = max_dlmp
    res["mechanism_price_channel"] = {
        "july_night": night,
        "note": (
            "The miso-130 channel: the July-night level sets which share of the "
            "PRB econ ladder is priced out of the diurnal wave. Reported whichever "
            "way it moves (prereg §2 two-sided prior: net DEARER was expected)."
        ),
    }

    res["K7_full_balance"] = {
        "net_class_energy_delta_gwh": net_energy,
        "full_balance_residual_gwh": {
            y: v["residual_gwh"] for y, v in balance.items()
        },
        "components_gwh": balance,
        "tolerance_gwh": 0.5,
        "rule": (
            "demand is exogenous and identical in both arms, so supply must "
            "re-balance exactly: d_class + d_discharge - d_charge + d_slack "
            "- d_dump - d_demand == 0"
        ),
        "boundary_note": (
            "The class sidecar is NOT the whole balance (miso-126 §6): storage and "
            "unserved energy live in separate sidecars."
        ),
        "verdict": "PASS"
        if all(abs(v["residual_gwh"]) <= 0.5 for v in balance.values())
        and all(v["demand_delta_gwh"] == 0.0 for v in balance.values())
        else "FAIL",
    }

    # ---- the TARGET: C7 COAL_PRB, and K6 / K8 -----------------------------
    d1 = {
        klass: {"control": _d1_rows(ARM_A, klass), "arm": _d1_rows(ARM_B, klass)}
        for klass in ("COAL_PRB", "COAL_BIT")
    }
    prb_ctl, prb_arm = d1["COAL_PRB"]["control"], d1["COAL_PRB"]["arm"]
    cv_move = {
        y: {
            "control": (prb_ctl.get(y) or {}).get("cv_ratio"),
            "arm": (prb_arm.get(y) or {}).get("cv_ratio"),
        }
        for y in sorted(set(prb_ctl) | set(prb_arm))
    }
    arm_cv = [v["arm"] for v in cv_move.values() if v["arm"] is not None]
    rdf = {
        str(y): {
            "control": _rdfrac(payload_ids.get("arm_A", ""), y),
            "arm": _rdfrac(payload_ids.get("arm_B", ""), y),
        }
        for y in YEARS
    }
    res["TARGET_c7_coal_prb"] = {
        "cv_ratio": cv_move,
        "profile_r": {
            y: {
                "control": (prb_ctl.get(y) or {}).get("profile_r"),
                "arm": (prb_arm.get(y) or {}).get("profile_r"),
            }
            for y in sorted(set(prb_ctl) | set(prb_arm))
        },
        "decomposition": rdf,
        "decomposition_note": (
            "QUOTE R_dfrac, NEVER raw variance (miso-128 DO-NOT-MISREAD). "
            "cv_ratio = R_tot x R_dfrac x R_level; the 2025 failure is the "
            "R_dfrac (organisation) term."
        ),
        "gate": CV_RATIO_GATE,
        "all_years_pass": bool(arm_cv) and all(v >= CV_RATIO_GATE for v in arm_cv),
        "promotion_note": (
            "rule 1 [R-STRUCT] / prereg §3: this does NOT decide promotion on its "
            "own. Arm B replaces two ungrounded multipliers with the fleet's own "
            "measured value, so it is the more faithful configuration whichever "
            "way this moves."
        ),
    }

    bit_ctl, bit_arm = d1["COAL_BIT"]["control"], d1["COAL_BIT"]["arm"]
    bit_cv = {
        y: {
            "control": (bit_ctl.get(y) or {}).get("cv_ratio"),
            "arm": (bit_arm.get(y) or {}).get("cv_ratio"),
        }
        for y in sorted(set(bit_ctl) | set(bit_arm))
    }
    bit_vals = [v["arm"] for v in bit_cv.values() if v["arm"] is not None]
    bit_status_regressed = any(
        (bit_ctl.get(y) or {}).get("verdict") == "pass"
        and (bit_arm.get(y) or {}).get("verdict") not in (None, "pass")
        for y in bit_cv
    )
    res["K6_coal_bit_no_overshoot"] = {
        "cv_ratio": bit_cv,
        "ceiling": COAL_BIT_CV_CEILING,
        "status_regressed": bit_status_regressed,
        "note": (
            "the miso-102 signature: overshooting COAL_BIT to 2.6-2.8x measured "
            "off-peak variability is one of the two ways that arm failed."
        ),
        "verdict": "PASS"
        if not bit_status_regressed
        and all(v <= COAL_BIT_CV_CEILING for v in bit_vals)
        else "FAIL",
    }

    r_tot_arm = [
        (rdf[str(y)]["arm"] or {}).get("R_tot")
        for y in YEARS
        if isinstance(rdf[str(y)]["arm"], dict)
    ]
    r_tot_known = [v for v in r_tot_arm if isinstance(v, (int, float))]
    res["K8_r_tot_floor"] = {
        "floor": R_TOT_FLOOR,
        "arm_R_tot": {str(y): (rdf[str(y)]["arm"] or {}).get("R_tot") for y in YEARS},
        "control_R_tot": {
            str(y): (rdf[str(y)]["control"] or {}).get("R_tot") for y in YEARS
        },
        "note": (
            "the miso-131 P3 convention. R_tot was already 0.952 with no room, so "
            "a cv_ratio gain bought by inflating raw off-peak dispersion is not "
            "the organisation fix this lane claims."
        ),
        "verdict": (
            "PASS"
            if r_tot_known and all(v >= R_TOT_FLOOR for v in r_tot_known)
            else ("FAIL" if r_tot_known else "UNSCORED (payloads absent)")
        ),
    }

    # ---- K5: C1 16/16 ------------------------------------------------------
    arm = _scorecard(ARM_B)
    res["K5_c1_16_of_16"] = {
        "control_status": ctl["criteria"].get("C1"),
        "arm_status": arm["criteria"].get("C1"),
        "control_tally": _c1_fraction(ctl),
        "arm_tally": _c1_fraction(arm),
        "verdict": "PASS"
        if ctl["criteria"].get("C1") == arm["criteria"].get("C1")
        and (
            _c1_fraction(ctl) is None or _c1_fraction(ctl) == _c1_fraction(arm)
        )
        else "FAIL",
    }

    # ---- K9: no forced energy ---------------------------------------------
    fa, fb = _d2_forced(ARM_A), _d2_forced(ARM_B)
    new_ids = sorted(set(fb["mechanism_ids"]) - set(fa["mechanism_ids"]))
    risen = {
        k: [fa["by_class_year"].get(k, {}).get("forced_share"),
            v.get("forced_share")]
        for k, v in fb["by_class_year"].items()
        if v.get("forced_share") is not None
        and fa["by_class_year"].get(k, {}).get("forced_share") is not None
        and v["forced_share"] > fa["by_class_year"][k]["forced_share"] + 1e-6
    }
    res["K9_no_forced_energy"] = {
        "new_forcing_mechanism_ids": new_ids,
        "forced_share_risen": risen,
        "note": (
            "the arm changes a PRICE, not a floor — no min_gen is added, so no "
            "new forcing id and no rising forced share is expected."
        ),
        "verdict": "PASS" if not new_ids and not risen else "FAIL",
    }

    # ---- scorecard movement (reported, never a revert trigger) ------------
    crit = {
        name: {
            "control": ctl["criteria"].get(name),
            "arm": arm["criteria"].get(name),
            "changed": ctl["criteria"].get(name) != arm["criteria"].get(name),
        }
        for name in sorted(set(ctl["criteria"]) | set(arm["criteria"]))
    }
    va, vb = _diagnostic_verdicts(ARM_A), _diagnostic_verdicts(ARM_B)
    res["scorecard_movement"] = {
        "determination": {"control": ctl["determination"], "arm": arm["determination"]},
        "ledgered_caveats": {"control": ctl["caveats"], "arm": arm["caveats"]},
        "criteria": crit,
        "criteria_changed": [n for n, v in crit.items() if v["changed"]],
        "diagnostic_verdict_changes": {
            k: [va.get(k), vb.get(k)]
            for k in sorted(set(va) | set(vb))
            if va.get(k) != vb.get(k)
        },
        "note": (
            "prereg §3: a regression is REPORTED and is NOT grounds to revert to "
            "0.92/1.20 — rule 14 [R-ACCURATE] forbids burying the error back "
            "inside the proxy; rule 1 [R-STRUCT] equally forbids promoting "
            "because a residual moved."
        ),
    }

    gates = {
        k: v["verdict"]
        for k, v in res.items()
        if isinstance(v, dict) and "verdict" in v
    }
    res["gates"] = gates
    blocking = (
        "K0_control_integrity",
        "K1_band_fidelity",
        "K2_single_mechanism",
        "K3_year_span",
        "K7_full_balance",
        "K9_no_forced_energy",
    )
    res["blocking_gates_pass"] = all(gates.get(g) == "PASS" for g in blocking)

    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for k, v in gates.items():
        print(f"  {k:>26}: {v}")
    print(f"  {'BLOCKING GATES':>26}: "
          f"{'PASS' if res['blocking_gates_pass'] else 'FAIL'}")
    print("\n  CC class energy delta (TWh):", cc_total_twh)
    print("  C7 COAL_PRB cv_ratio:", json.dumps(cv_move))
    print("  July-night lw price delta:",
          {y: round(v["d_july_night_lw_price"], 3) for y, v in night.items()})


if __name__ == "__main__":
    main()
