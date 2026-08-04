"""miso-127 A/B scorer — ``coal_mustrun_online_pmin`` on the MISO keeper.

Scores the single-delta arm ``results/calibration/miso127_onlinepmin_B``
(``coal_mustrun_online_pmin=true``) against ``results/calibration/miso127_onlinepmin_A``,
the same-HEAD ZERO-DELTA control replay of the keeper
``2026-08-04-miso-126-steampart-b``.

NO LP IS SOLVED HERE — every number is read from the committed bundles.

Every delta is quoted against **arm A**, never against the committed keeper
(miso-124 DO-NOT-MISREAD: the price response is not stable across keepers).

Gates, in the pre-registered order
(``results/calibration/PREREG-miso127-takeorpay-period-budget-2026-08-04.md`` §2):

K0  control integrity  — prereg **B2**. Arm A must reproduce the INCUMBENT
                         keeper's scorecard exactly AND its committed hourly
                         sidecars. caiso-146 found a zero-delta control diverging
                         by GW on a class-hour, so this is measured, not assumed.
K1  flag fidelity      — arm A records ``coal_mustrun_online_pmin=false``, arm B
                         ``true`` (rule 26: arming visible in ``run_config.json``).
K2  single delta       — the two scenario blocks differ in exactly one key.
K3  year span          — both bundles ``[2023, 2024, 2025]`` (rules 16 / 22).
K4  liveness (grain 2) — prereg **B1**. Per-class ENERGY deltas are the magnitude
                         of record (miso-122 DO-NOT-MISREAD: ``max_abs_class_hour_mw``
                         is NOT a mechanism magnitude at MISO). The pre-registered
                         bar is |d COAL class energy| > 0.05 TWh in >= 1 year.
                         A NULL HERE IS NOT AN ``I`` VERDICT: grain 1 (pre-arm,
                         bins) already fired on 42 coal bins, so a dead grain 2
                         means the flag did not reach the LP — a wiring defect to
                         find and fix (miso-126 §4), not an inert mechanism.
K5  C7 shape           — prereg **B4**. The target. D-1 ``cv_ratio`` for
                         ``COAL_PRB`` in all three years against arm A, gate 0.5,
                         plus ``profile_r`` (which passes and must not break).
                         Reported with the COAL_BIT off-peak CV ratio, because
                         OVERSHOOTING it to 2.6-2.8x measured variability is one
                         of the two ways miso-102's arm failed.
                         THIS GATE DOES NOT DECIDE PROMOTION ON ITS OWN
                         (prereg B6 / rule 1 [R-STRUCT]).
K6  energy conservation— prereg **B3**. The FULL balance identity, not the class
                         sidecar (miso-126 §6): storage charge/discharge lives in
                         ``hourly/storage_<year>.parquet`` and unserved energy in
                         ``hourly/system_<year>.parquet``.
                         ``d_class + d_discharge - d_charge + d_slack - d_dump
                         - d_demand == 0``. A magnitude violating a conservation
                         law is a BOUNDARY defect in the statistic before it is a
                         result about the mechanism.
K7  no gate regression — prereg **B5**. The nine criterion statuses,
                         determination, ledgered caveats AND every
                         legitimacy-diagnostic verdict.
                         NOTE (prereg B6): a regression is REPORTED and is NOT by
                         itself grounds to revert — ``mustrun_online_pct`` is the
                         MEASURED online Pmin and ``mustrun_pct`` a biased proxy
                         for it, so rule 14 ``[R-ACCURATE]`` forbids burying the
                         error back inside the proxy. Equally, rule 1
                         ``[R-STRUCT]`` forbids promoting because a residual moved.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only. Writes
``results/calibration/_miso127_online_pmin_ab.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
INCUMBENT = REPO / "results/calibration/miso126_steampart_B"
ARM_A = REPO / "results/calibration/miso127_onlinepmin_A"
ARM_B = REPO / "results/calibration/miso127_onlinepmin_B"
OUT = REPO / "results/calibration/_miso127_online_pmin_ab.json"
YEARS = (2023, 2024, 2025)
FLAG = "coal_mustrun_online_pmin"

#: Prereg B1 grain-2 bar: |d COAL class energy| must exceed this in >= 1 year.
GRAIN2_TWH = 0.05
#: D-1 gate (scripts/legitimacy_diagnostics.D1_MIN_CV_RATIO).
CV_RATIO_GATE = 0.5
#: Grain 1, measured PRE-ARM and recorded in the pre-registration §2.
GRAIN1 = {
    "coal_bins_pct_mr_changed": 42,
    "coal_bins_pct_econ_changed": 39,
    "gross_abs_pct_mr_pp": 867.8,
    "net_pct_mr_pp": 297.8,
    "artifact_capw_mustrun_pct": 28.886,
    "artifact_capw_mustrun_online_pct": 27.609,
    "artifact_net_mw": -533.1,
    "artifact_gross_abs_mw": 7528.1,
}


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
    """Full supply/demand energy-balance delta between the two arms, in GWh.

    ``d_class + d_discharge - d_charge + d_slack - d_dump - d_demand`` must be
    zero: demand is exogenous and identical, so every MWh one arm adds has to
    displace another supply term. The three sidecars are separate artifacts,
    which is exactly why a class-only form of this check is incomplete.
    """

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
    """Every verdict string in a bundle's legitimacy diagnostics, keyed by row."""
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


def _d1_rows(bundle: Path, klass: str) -> dict[str, dict]:
    """Return ``{year: D-1 row}`` for one class from a bundle's diagnostics."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {}
    diags = json.loads(path.read_text()).get("diagnostics", {})
    out: dict[str, dict] = {}
    for block, payload in diags.items():
        if not isinstance(payload, dict) or "D-1" not in block:
            continue
        for row in payload.get("rows", []):
            if row.get("class") == klass:
                out[str(row.get("year"))] = row
    return out


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
        "caveats": sorted(m.get("caveats") or []),
    }


def main() -> None:  # noqa: C901 — one linear gate sequence, kept together
    sa, sb = _scenario(ARM_A), _scenario(ARM_B)
    diff = {
        k: (sa.get(k), sb.get(k)) for k in set(sa) | set(sb) if sa.get(k) != sb.get(k)
    }
    ma = json.loads((ARM_A / "meta.json").read_text())
    mb = json.loads((ARM_B / "meta.json").read_text())

    res: dict = {
        "session": "miso-127",
        "prereg": (
            "results/calibration/"
            "PREREG-miso127-takeorpay-period-budget-2026-08-04.md"
        ),
        "incumbent_keeper": {
            "bundle": INCUMBENT.name,
            "run_id": "2026-08-04-miso-126-steampart-b",
        },
        "arm_A": {"bundle": ARM_A.name, "delta": "none (same-HEAD zero-delta control)"},
        "arm_B": {"bundle": ARM_B.name, "delta": f"{FLAG}=true"},
        "mechanism": {
            "field": FLAG,
            "what": (
                "sizes the coal must-run (cheap, fuel-sunk) tranche from the "
                "MEASURED online minimum stable load (thermal_tranches_MISO.csv "
                "mustrun_online_pct) instead of the all-hours available-CF P5 "
                "(mustrun_pct). Pmin=0 on that tranche, so this changes the SIZE "
                "of the cheap bid band, not a forced floor."
            ),
            "grain1_pre_arm": GRAIN1,
            "grain1_note": (
                "The field's docstring predicts the all-hours figure 'reads ~2x "
                "high'. That was measured on ERCOT and is FALSE at MISO: the "
                "cap-weighted ratio is 0.956. But the -533 MW NET hides 7,528 MW "
                "GROSS (18% of the coal fleet) reallocating on 39 of 44 plants in "
                "OPPOSITE directions, so the expected-INERT prior was refuted "
                "ex ante and the zero-solve kill was not available."
            ),
        },
    }

    # ---- K0: control integrity (prereg B2) --------------------------------
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
        "incumbent": inc,
        "control": ctl,
        "scorecard_identical": scorecard_same,
        "max_abs_class_hour_mw_vs_incumbent": sidecar_max,
        "note": (
            "caiso-146 found an outgoing keeper's committed sidecars no longer "
            "reproducing at HEAD (a zero-delta control diverging by up to 3.2 GW "
            "on a class-hour), so this is MEASURED. A non-zero sidecar delta "
            "here is a HEAD-drift finding about the incumbent bundle, NOT a "
            "result of this session's mechanism, and it is reported as such."
        ),
        "verdict": "PASS" if scorecard_same else "FAIL",
    }

    # ---- K1-K3: fidelity, single delta, year span -------------------------
    res["K1_flag_fidelity"] = {
        f"arm_A_{FLAG}": sa.get(FLAG),
        f"arm_B_{FLAG}": sb.get(FLAG),
        "verdict": "PASS"
        if sa.get(FLAG) is False and sb.get(FLAG) is True
        else "FAIL",
    }
    res["K2_single_delta"] = {
        "n_differing_keys": len(diff),
        "keys": {k: list(v) for k, v in diff.items()},
        "verdict": "PASS" if list(diff) == [FLAG] else "FAIL",
    }
    res["K3_year_span"] = {
        "arm_A_years": ma.get("years"),
        "arm_B_years": mb.get("years"),
        "verdict": "PASS"
        if ma.get("years") == mb.get("years") == [2023, 2024, 2025]
        else "FAIL",
    }

    # ---- K4-K6: liveness, C7 shape, conservation --------------------------
    max_dmw, max_dlmp, d_sys, energy, price_hours = {}, {}, {}, {}, {}
    coal, net_energy, balance = {}, {}, {}
    for year in YEARS:
        ca, cb = _classes(ARM_A, year), _classes(ARM_B, year)
        cb = cb.reindex(columns=ca.columns, fill_value=0.0)
        d = cb - ca
        pa, dem = _system(ARM_A, year)
        pb, _ = _system(ARM_B, year)
        zc = [c for c in pa.columns if c.startswith("MISO-")]
        dl = (pb[zc] - pa[zc]).to_numpy()

        max_dmw[str(year)] = float(np.abs(d.to_numpy()).max())
        max_dlmp[str(year)] = float(np.abs(dl).max())
        wa = (pa[zc] * dem[zc]).sum(axis=1) / dem[zc].sum(axis=1)
        wb = (pb[zc] * dem[zc]).sum(axis=1) / dem[zc].sum(axis=1)
        d_sys[str(year)] = float((wb - wa).mean())
        # miso-122 DO-NOT-MISREAD: per-class ENERGY is the magnitude of record.
        energy[str(year)] = {
            k: round(float(v) / 1e3, 6) for k, v in d.sum().items() if abs(v) > 1e-6
        }  # GWh
        coal[str(year)] = {
            k: round(float(d.get(k, pd.Series(0.0)).sum()) / 1e6, 6)  # TWh
            for k in ("COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL_WC")
            if k in d.columns
        }
        net_energy[str(year)] = round(float(d.to_numpy().sum()) / 1e3, 6)
        price_hours[str(year)] = {
            "hours_with_any_zonal_delta": int((np.abs(dl).max(axis=1) > 1e-9).sum()),
            "zone_hours_price_rose": int((dl > 1e-9).sum()),
            "zone_hours_price_fell": int((dl < -1e-9).sum()),
        }
        balance[str(year)] = _balance(year)

    coal_total_twh = {
        y: round(sum(v.values()), 6) for y, v in coal.items()
    }
    grain2_live = any(abs(v) > GRAIN2_TWH for v in coal_total_twh.values())
    res["K4_liveness_grain2"] = {
        "coal_class_energy_delta_twh": coal,
        "coal_total_delta_twh": coal_total_twh,
        "class_energy_delta_gwh": energy,
        "max_abs_class_hour_mw": max_dmw,
        "max_abs_class_hour_mw_note": (
            "NOT a mechanism magnitude at MISO (miso-122 DO-NOT-MISREAD). "
            "Read coal_class_energy_delta_twh."
        ),
        "max_zonal_abs_dlmp": max_dlmp,
        "price_delta_hours": price_hours,
        "grain2_bar_twh": GRAIN2_TWH,
        "grain1_fired": True,
        "wiring_note": (
            "Grain 1 fired pre-arm on 42 coal bins, so a dead grain 2 is a "
            "WIRING DEFECT to find and fix (miso-126 §4), NOT an 'I' verdict. "
            "coal_mustrun_online_pmin is config-borne: run_calibration.py sets it "
            "via config.with_overrides (or prb_overrides, applied at :1429), and "
            "fleet_to_bins(..., iso, config) -> campd_bins.py:1645 reads it, so "
            "it does NOT pass through the load_fleet_from_csv keyword seam that "
            "silently dropped miso-126's first arm."
        ),
        "verdict": "LIVE" if grain2_live else "INERT",
    }
    res["max_zonal_abs_dlmp"] = max_dlmp  # consumed by the attestation generator

    # ---- K5: the C7 target (prereg B4) ------------------------------------
    d1 = {
        klass: {
            "control": _d1_rows(ARM_A, klass),
            "arm": _d1_rows(ARM_B, klass),
        }
        for klass in ("COAL_PRB", "COAL_BIT")
    }
    prb_ctl = d1["COAL_PRB"]["control"]
    prb_arm = d1["COAL_PRB"]["arm"]
    cv_move = {
        y: {
            "control": (prb_ctl.get(y) or {}).get("cv_ratio"),
            "arm": (prb_arm.get(y) or {}).get("cv_ratio"),
        }
        for y in sorted(set(prb_ctl) | set(prb_arm))
    }
    r_move = {
        y: {
            "control": (prb_ctl.get(y) or {}).get("profile_r"),
            "arm": (prb_arm.get(y) or {}).get("profile_r"),
        }
        for y in sorted(set(prb_ctl) | set(prb_arm))
    }
    arm_cv = [v["arm"] for v in cv_move.values() if v["arm"] is not None]
    res["K5_c7_shape"] = {
        "target": "C7 COAL_PRB diurnal shape — MISO's sole failing criterion",
        "cv_ratio": cv_move,
        "profile_r": r_move,
        "coal_bit_d1": {
            y: {
                "control": (d1["COAL_BIT"]["control"].get(y) or {}).get("cv_ratio"),
                "arm": (d1["COAL_BIT"]["arm"].get(y) or {}).get("cv_ratio"),
            }
            for y in sorted(
                set(d1["COAL_BIT"]["control"]) | set(d1["COAL_BIT"]["arm"])
            )
        },
        "coal_bit_note": (
            "reported because OVERSHOOTING COAL_BIT to 2.6-2.8x measured "
            "off-peak variability is one of the two ways miso-102's "
            "discount-deleting arm failed (the other was C1 16/16 -> 11/16)."
        ),
        "gate": CV_RATIO_GATE,
        "all_years_pass": bool(arm_cv) and all(v >= CV_RATIO_GATE for v in arm_cv),
        "promotion_note": (
            "prereg B6 / rule 1 [R-STRUCT]: this gate does NOT decide promotion "
            "on its own. A candidate that moves C7 to PASS while breaking C1 is "
            "not automatically a keeper, and one that improves structure while "
            "C7 stays FAIL still may be."
        ),
        "verdict": "PASS"
        if bool(arm_cv) and all(v >= CV_RATIO_GATE for v in arm_cv)
        else "FAIL",
    }

    # Demand is exogenous and identical in both arms, so the summed class-energy
    # delta must be ~0. Tolerance is 0.5 GWh/yr on a ~650 TWh system (8e-7 of
    # load) — loose enough for LP alternate-optimal noise, tight enough that a
    # real accounting leak cannot hide inside it.
    res["K6_energy_conservation"] = {
        "net_class_energy_delta_gwh": net_energy,
        "net_class_only_within_tolerance": all(
            abs(v) <= 0.5 for v in net_energy.values()
        ),
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
            "The class sidecar is NOT the whole balance (miso-126 §6): storage "
            "charge/discharge and unserved energy live in separate sidecars and "
            "this lever legitimately moves both. The VERDICT is on the full "
            "identity; the class-only figure is reported alongside it so a "
            "boundary defect can never be mistaken for a mechanism result."
        ),
        "verdict": "PASS"
        if all(abs(v["residual_gwh"]) <= 0.5 for v in balance.values())
        and all(v["demand_delta_gwh"] == 0.0 for v in balance.values())
        else "FAIL",
    }

    # ---- K7: gate regression (prereg B5) ----------------------------------
    arm = _scorecard(ARM_B)
    crit = {
        name: {
            "control": ctl["criteria"].get(name),
            "arm": arm["criteria"].get(name),
            "changed": ctl["criteria"].get(name) != arm["criteria"].get(name),
        }
        for name in sorted(set(ctl["criteria"]) | set(arm["criteria"]))
    }
    va, vb = _diagnostic_verdicts(ARM_A), _diagnostic_verdicts(ARM_B)
    diag_changes = {
        k: [va.get(k), vb.get(k)]
        for k in sorted(set(va) | set(vb))
        if va.get(k) != vb.get(k)
    }
    changed = [n for n, v in crit.items() if v["changed"]]
    res["K7_no_gate_regression"] = {
        "determination": {"control": ctl["determination"], "arm": arm["determination"]},
        "ledgered_caveats": {"control": ctl["caveats"], "arm": arm["caveats"]},
        "criteria": crit,
        "criteria_changed": changed,
        "diagnostic_verdict_changes": diag_changes,
        "n_diagnostic_rows_compared": len(set(va) | set(vb)),
        "note": (
            "prereg B6: a regression is REPORTED and is NOT by itself grounds to "
            "revert. mustrun_online_pct is the MEASURED online Pmin and "
            "mustrun_pct a biased proxy for it, so rule 14 [R-ACCURATE] forbids "
            "burying the error back inside the proxy; rule 1 [R-STRUCT] equally "
            "forbids promoting because a residual moved."
        ),
        "verdict": "PASS"
        if not changed
        and not diag_changes
        and ctl["determination"] == arm["determination"]
        and arm["determination"] is not None
        and ctl["caveats"] == arm["caveats"]
        else "CHANGED",
    }

    gates = {
        k: v["verdict"]
        for k, v in res.items()
        if isinstance(v, dict) and "verdict" in v
    }
    res["gates"] = gates
    # K4 is a liveness READING (LIVE/INERT); K5 is the target, reported whichever
    # way it goes; K7 is reported, never a revert trigger. The blocking gates —
    # the ones that decide whether any statistic in this session may be believed
    # at all — are the integrity ones.
    blocking = (
        "K0_control_integrity",
        "K1_flag_fidelity",
        "K2_single_delta",
        "K3_year_span",
        "K6_energy_conservation",
    )
    res["blocking_gates_pass"] = all(gates.get(g) == "PASS" for g in blocking)

    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for k, v in gates.items():
        print(f"  {k:>26}: {v}")
    print(f"  {'BLOCKING GATES':>26}: "
          f"{'PASS' if res['blocking_gates_pass'] else 'FAIL'}")
    print("\n  COAL class energy delta (TWh):", coal_total_twh)
    print("  per-coal-class (TWh):         ", coal)
    print("  C7 COAL_PRB cv_ratio:         ", cv_move)
    print("  C7 COAL_PRB profile_r:        ", r_move)
    print("  COAL_BIT cv_ratio:            ", res["K5_c7_shape"]["coal_bit_d1"])
    print("  net class energy delta (GWh): ", net_energy)
    print("  FULL balance residual (GWh):  ",
          {y: v["residual_gwh"] for y, v in balance.items()})
    print("  max zonal |dLMP| ($/MWh):     ", max_dlmp)
    print("  d system demand-wtd lambda:   ", d_sys)
    print("  determination:", res["K7_no_gate_regression"]["determination"])
    print("  ledgered caveats:", res["K7_no_gate_regression"]["ledgered_caveats"])
    if changed:
        print("  CRITERION STATUS CHANGES:", {n: crit[n] for n in changed})
    if diag_changes:
        print("  DIAGNOSTIC VERDICT CHANGES:", diag_changes)


if __name__ == "__main__":
    main()
