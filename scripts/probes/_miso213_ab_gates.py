"""miso-213 A/B scorer — WRITTEN AND COMMITTED BLIND, before the arm's numbers.

===============================================================================
LINEAGE
===============================================================================
Built on ``_miso210_ab_gates.py`` (kills-silent ordered BEFORE inertness,
inertness on VALUE MOVEMENT, the miso-200 vacuous-pass trap closed).

===============================================================================
WHAT CHANGES HERE: the delta IS a ScenarioConfig field, and the control is
the keeper itself
===============================================================================
* **S-0 control integrity** — the CONTROL is the committed keeper bundle
  ``miso210_clock_B`` (no re-solve, per the charter): bit-identity of the
  replay channel was established at miso-210 (its S-0, 9 sidecars,
  ``max_abs_diff`` 0.0) and is INHERITED here; the scorer verifies the
  keeper's committed sidecars exist and quotes the miso-210 S-0 record.
* **S-1 single delta** — the two legs' ``scenario_config`` blocks differ in
  EXACTLY ``{miso_zonal_gas_basis_skip_923_priced: False -> True}``; the
  ``git.sha`` differs (the arm carries the code). Any other diff VOIDS.
* **S-2 placement liveness** — read from the post-code L-5 block of the
  phase-0 record: on the keeper's own fleet chain every cell the production
  print path wrote has an arm price equal to ``F_nobasis`` and every unmasked
  cell keeps the keeper's ``F`` (zero-solve, off the production
  ``resolve_fuel_prices``).

S-0's K-gates (K-1..K-6) are the miso-202/210 gates unchanged, thresholds
frozen from the keeper's own committed verdict. C3a and C8 are reported at
full magnitude and are NEVER gates (rule 1 [R-STRUCT]).

===============================================================================
THE PRE-REGISTERED OBJECT GATES (PREREG §3 P-5), 2025 real S->N binding
SHOULDER hours; control values from the committed miso-211 record, arm values
from the arm's fresh network / unit_hourly sidecars via the miso-211 readers
===============================================================================
  O-1 South boundary net (model into-South inflow)  +0.05 -> [-0.6, -0.1] GW
  O-2 S->N corridor flow mean                        357  -> [450, 1000] MW
  O-3 S->N free-tier binding share                   2.8 % -> [4, 12] %
  O-4 Indiana - South zonal spread mean             -0.16 -> [+0.3, +3] $/MWh
  O-5 South gas dispatch                            15.56 -> [15.9, 16.4] GW
  O-6 Midwest gas dispatch change (ISO gas classes minus South gas)
                                                          [-0.8, -0.2] GW
The object gates are SCORED (inside/outside the band) but are not kills: the
promotion rule (PREREG §4) reads S-1 and K-1..K-5 only.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso213_ab_gates.py

Record: ``results/calibration/_miso213_ab_gates.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso210_clock_B"
CONTROL = KEEPER  # the charter: the keeper IS the control, never re-solved
ARM = REPO / "results" / "calibration" / "miso213_layering_B"
PHASE0 = REPO / "results" / "calibration" / "_miso213_basis_layering.json"
M210 = REPO / "results" / "calibration" / "_miso210_ab_gates.json"
M211 = REPO / "results" / "calibration" / "_miso211_rdt_binding_state.json"
OUT = REPO / "results" / "calibration" / "_miso213_ab_gates.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
FIELD = "miso_zonal_gas_basis_skip_923_priced"
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")

# --- FROZEN, from the PREREG (§3 P-6 / §4). Stated before the arm's numbers. --
C1_BAND_TWH = 8.00
# class|year -> (keeper face TWh, headroom), read off the miso-210 keeper's OWN
# committed verdict (its arm faces, FINDING-miso210 §3 K-1).
K1_NAMED = {
    "ST_GAS|2024": (-7.486, 0.514),
    "CC_REGULAR|2024": (+6.940, 1.060),
    "ST_GAS|2025": (-6.686, 1.314),
    "COAL_PRB|2025": (-4.907, 3.093),
    "ST_GAS|2023": (-3.516, 4.484),
    "CC_REGULAR|2023": (-3.408, 4.592),
    "CC_REGULAR|2025": (-2.177, 5.823),
}
INERT_EPS = {"c1_twh": 0.010, "c3a_pp": 0.010, "c3b": 0.0005, "c8_share": 0.0005}
# PREREG §3 P-5: aggregate gas TWh moves < 0.3 TWh/yr; ST_GAS +0.1..+0.5;
# CC_REGULAR -0.1..-0.5; C3a by year, by mechanism.
PREREG_C3A = {
    2023: {"lo": -0.5, "hi": -0.05},
    2024: {"lo": -0.5, "hi": -0.05},
    2025: {"lo": 0.2, "hi": 1.5},
}
PREREG_C1 = {"ST_GAS": (0.1, 0.5), "CC_REGULAR": (-0.5, -0.1)}
OBJECT_BANDS = {
    "O1_south_net_inflow_gw": (-0.6, -0.1),
    "O2_s2n_flow_mean_mw": (450.0, 1000.0),
    "O3_s2n_free_tier_share": (0.04, 0.12),
    "O4_spread_indiana_minus_south": (0.3, 3.0),
    "O5_south_gas_gw": (15.9, 16.4),
    "O6_midwest_gas_delta_gw": (-0.8, -0.2),
}


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--json",
            str(bundle),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _crit_status(v: dict) -> dict:
    out = {}
    for name, block in (v.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"] = (
                rec.get("status")
            )
    return out


def _c1(v: dict) -> dict:
    out = {}
    for rec in (v.get("criteria", {}).get("fuelmix") or {}).get("records", []):
        k, y = rec.get("key"), rec.get("year")
        if k is None or y is None:
            continue
        try:
            out[f"{k}|{y}"] = float(rec["model"]) - float(rec["actual"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _c3a(v: dict) -> dict:
    out = {}
    for rec in v["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def _c3b(v: dict) -> dict:
    return {
        int(r["year"]): float(r["model"])
        for r in v["criteria"]["price_shape"]["records"]
        if r.get("key") is None and r.get("model") is not None
    }


def _led(b: Path) -> dict:
    p = b / "legitimacy_diagnostics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _rows(b: Path, block: str) -> list:
    return ((_led(b).get("diagnostics") or {}).get(block) or {}).get("rows", []) or []


def _d4_fail_keys(b: Path) -> set:
    return {
        (r.get("year"), r.get("check"), r.get("floor"), r.get("plant"))
        for r in _rows(b, "D4")
        if str(r.get("verdict", "pass")).lower() != "pass"
    }


def _d1(b: Path, klass: str = "ST_GAS") -> dict:
    return {
        int(r["year"]): {
            "profile_r": r.get("profile_r"),
            "cv_ratio": r.get("cv_ratio"),
            "verdict": r.get("verdict"),
        }
        for r in _rows(b, "D1")
        if r.get("class") == klass
    }


def _c8_share(b: Path, klass: str = "ST_GAS") -> dict:
    out: dict = {}
    for r in _rows(b, "D2"):
        if r.get("class") != klass:
            continue
        y = int(r["year"])
        out[y] = out.get(y, 0.0) + float(r.get("forced_twh") or 0.0)
    tot: dict = {}
    for r in _rows(b, "D2"):
        if r.get("class") == klass and r.get("class_total_twh"):
            tot[int(r["year"])] = float(r["class_total_twh"])
    return {y: (out[y] / tot[y] if tot.get(y) else None) for y in out}


# ------------------------------------------------------------------- gates
def s0_inherited() -> dict:
    """S-0 -- the control is the keeper; bit-identity inherited from miso-210."""
    present, missing = 0, []
    for year in YEARS:
        for stem in ("class_hourly", "system", "reserve_family"):
            if (KEEPER / "hourly" / f"{stem}_{year}.parquet").exists():
                present += 1
            else:
                missing.append(f"{stem}_{year}")
    m210 = json.loads(M210.read_text()) if M210.exists() else {}
    s0 = m210.get("S0") or {}
    return {
        "control_is_keeper_bundle": CONTROL == KEEPER,
        "keeper_sidecars_present": present,
        "missing": missing,
        "miso210_s0": {
            "sidecars_checked": s0.get("sidecars_checked"),
            "max_abs_diff": s0.get("max_abs_diff"),
            "passed": s0.get("passed"),
        },
        "passed": bool(not missing and s0.get("passed") is True),
    }


def s1_single_delta() -> dict:
    rc_c = json.loads((CONTROL / "run_config.json").read_text())
    rc_a = json.loads((ARM / "run_config.json").read_text())
    ca, cb = rc_c["scenario_config"], rc_a["scenario_config"]
    diffs = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
    sha_c = (rc_c.get("git") or {}).get("sha")
    sha_a = (rc_a.get("git") or {}).get("sha")
    return {
        "n_fields": len(set(ca) | set(cb)),
        "config_diffs": diffs,
        "control_value": ca.get(FIELD),
        "arm_value": cb.get(FIELD),
        "git_sha": {"control": sha_c, "arm": sha_a},
        "passed": (
            diffs == [FIELD]
            and ca.get(FIELD) in (False, None)
            and cb.get(FIELD) is True
            and sha_c != sha_a
        ),
    }


def s2_from_phase0() -> dict:
    ph = json.loads(PHASE0.read_text()) if PHASE0.exists() else {}
    l5 = ph.get("L5_arm_liveness") or {}
    return {
        "source": "L5_arm_liveness block of _miso213_basis_layering.json (post-code, zero-solve)",
        "years": {
            y: {
                "masked_cells_equal_F_nobasis_share": v.get(
                    "masked_cells_equal_F_nobasis_share"
                ),
                "unmasked_cells_equal_keeper_F_share": v.get(
                    "unmasked_cells_equal_keeper_F_share"
                ),
                "production_mask_share": v.get("production_mask_share"),
                "gas_cells_changed_share": v.get("gas_cells_changed_share"),
            }
            for y, v in (l5.get("years") or {}).items()
        },
        "passed": bool(l5.get("passed", False)),
    }


def kills(vc: dict, va: dict) -> dict:
    out: dict = {}
    c1c, c1a = _c1(vc), _c1(va)
    exits, named = [], {}
    max_move = {"key": None, "abs_twh": 0.0}
    for k in sorted(set(c1c) | set(c1a)):
        b, a = c1c.get(k), c1a.get(k)
        if b is None or a is None:
            continue
        if abs(a - b) > max_move["abs_twh"]:
            max_move = {"key": k, "abs_twh": round(abs(a - b), 4)}
        if abs(b) <= C1_BAND_TWH and abs(a) > C1_BAND_TWH:
            exits.append({"class_year": k, "control": round(b, 3), "arm": round(a, 3)})
    for k, (pre, head) in K1_NAMED.items():
        named[k] = {
            "prereg_control": pre,
            "prereg_headroom": head,
            "measured_control": round(c1c[k], 3) if c1c.get(k) is not None else None,
            "measured_arm": round(c1a[k], 3) if c1a.get(k) is not None else None,
            "band_exit": bool(c1a.get(k) is not None and abs(c1a[k]) > C1_BAND_TWH),
        }
    out["K1"] = {
        "band_twh": C1_BAND_TWH,
        "largest_class_year_move": max_move,
        "named_ex_ante": named,
        "all_band_exits": exits,
        "passed": not exits,
    }

    b3c, b3a = _c3b(vc), _c3b(va)
    sc, sa = _crit_status(vc), _crit_status(va)
    c3b_flip = [
        k
        for k in sc
        if k.startswith("price_shape")
        and sc[k] == "PASS"
        and sa.get(k) not in (None, "PASS")
    ]
    out["K2"] = {
        "control": b3c,
        "arm": b3a,
        "pass_to_fail": c3b_flip,
        "passed": not c3b_flip,
    }

    d4_rows = {"control": len(_rows(CONTROL, "D4")), "arm": len(_rows(ARM, "D4"))}
    d4_scorable = d4_rows["control"] > 0 and d4_rows["arm"] > 0
    new_d4 = sorted(map(str, _d4_fail_keys(ARM) - _d4_fail_keys(CONTROL)))
    out["K3"] = {
        "d4_row_counts": d4_rows,
        "scorable": d4_scorable,
        "new_d4_failures": new_d4 if d4_scorable else None,
        "cleared": (
            sorted(map(str, _d4_fail_keys(CONTROL) - _d4_fail_keys(ARM)))
            if d4_scorable
            else None
        ),
        "status": "SCORED" if d4_scorable else "UNSCORED — a leg carries no D4 rows",
        "passed": (not new_d4) if d4_scorable else None,
    }

    d1c, d1a = _d1(CONTROL), _d1(ARM)
    d1_rows = {"control": len(_rows(CONTROL, "D1")), "arm": len(_rows(ARM, "D1"))}
    d1_scorable = d1_rows["control"] > 0 and d1_rows["arm"] > 0
    d1_flip = [
        y
        for y in d1c
        if str(d1c[y].get("verdict", "")).lower() == "pass"
        and str(d1a.get(y, {}).get("verdict", "")).lower() != "pass"
    ]
    out["K4"] = {
        "d1_row_counts": d1_rows,
        "scorable": d1_scorable,
        "control": d1c,
        "arm": d1a,
        "pass_to_fail": d1_flip if d1_scorable else None,
        "status": "SCORED" if d1_scorable else "UNSCORED — a leg carries no D1 rows",
        "passed": (not d1_flip) if d1_scorable else None,
    }

    flips = [
        {"record": k, "control": sc[k], "arm": sa.get(k)}
        for k in sorted(sc)
        if sc[k] == "PASS" and sa.get(k) not in (None, "PASS")
    ]
    out["K5"] = {"pass_to_non_pass": flips, "passed": not flips}

    def _att(b: Path) -> dict:
        p = b / "calibration_attestation.json"
        return json.loads(p.read_text()) if p.exists() else {}

    ac_, aa_ = _att(CONTROL), _att(ARM)
    n_c = len((ac_.get("free_parameters") or {}).get("entries") or [])
    n_a = len((aa_.get("free_parameters") or {}).get("entries") or [])
    att = n_c > 0 and n_a > 0
    out["K6"] = {
        "attestation_entries": {"control": n_c, "arm": n_a},
        "prereg": "no new ledger entry (41 -> 41): a boolean scope on an existing measured input, zero free parameters",
        "status": "SCORED"
        if att
        else "UNSCORED — a leg carries no attestation entries",
        "passed": (n_a == n_c) if att else None,
    }
    return out


def movement(vc: dict, va: dict) -> dict:
    """Inertness measured on VALUE MOVEMENT, not on status identity."""
    c1c, c1a = _c1(vc), _c1(va)
    ac, aa = _c3a(vc), _c3a(va)
    bc, ba = _c3b(vc), _c3b(va)
    sc8, sa8 = _c8_share(CONTROL), _c8_share(ARM)
    d_c1 = {k: round(c1a[k] - c1c[k], 4) for k in sorted(set(c1c) & set(c1a))}
    d_c3a = {y: round(aa[y] - ac[y], 4) for y in sorted(set(ac) & set(aa))}
    d_c3b = {y: round(ba[y] - bc[y], 5) for y in sorted(set(bc) & set(ba))}
    d_c8 = {
        y: (
            round(sa8[y] - sc8[y], 5)
            if sa8.get(y) is not None and sc8.get(y) is not None
            else None
        )
        for y in sorted(set(sc8) | set(sa8))
    }
    moved = (
        any(abs(v) > INERT_EPS["c1_twh"] for v in d_c1.values())
        or any(abs(v) > INERT_EPS["c3a_pp"] for v in d_c3a.values())
        or any(abs(v) > INERT_EPS["c3b"] for v in d_c3b.values())
        or any(v is not None and abs(v) > INERT_EPS["c8_share"] for v in d_c8.values())
    )
    c3a_scored = {
        y: {
            "delta_pp": d_c3a.get(y),
            "prereg_band": PREREG_C3A[y],
            "inside": (
                None
                if d_c3a.get(y) is None
                else bool(PREREG_C3A[y]["lo"] <= d_c3a[y] <= PREREG_C3A[y]["hi"])
            ),
        }
        for y in PREREG_C3A
    }
    gas_twh = {}
    for y in YEARS:
        tot = sum(d_c1.get(f"{c}|{y}", 0.0) for c in GAS_CLASSES)
        gas_twh[y] = {
            "d_gas_classes_twh": round(tot, 4),
            "inside_prereg_lt_0.3": bool(abs(tot) < 0.3),
            "ST_GAS": d_c1.get(f"ST_GAS|{y}"),
            "ST_GAS_inside": (
                None
                if d_c1.get(f"ST_GAS|{y}") is None
                else bool(
                    PREREG_C1["ST_GAS"][0]
                    <= d_c1[f"ST_GAS|{y}"]
                    <= PREREG_C1["ST_GAS"][1]
                )
            ),
            "CC_REGULAR": d_c1.get(f"CC_REGULAR|{y}"),
            "CC_REGULAR_inside": (
                None
                if d_c1.get(f"CC_REGULAR|{y}") is None
                else bool(
                    PREREG_C1["CC_REGULAR"][0]
                    <= d_c1[f"CC_REGULAR|{y}"]
                    <= PREREG_C1["CC_REGULAR"][1]
                )
            ),
        }
    return {
        "epsilons": INERT_EPS,
        "d_c1_twh": d_c1,
        "c1_prereg_scored": gas_twh,
        "c3a_control": ac,
        "c3a_arm": aa,
        "d_c3a_pp": d_c3a,
        "c3a_prereg_scored": c3a_scored,
        "d_c3b": d_c3b,
        "c8_share_control": sc8,
        "c8_share_arm": sa8,
        "d_c8_share": d_c8,
        "status_map_identical": _crit_status(vc) == _crit_status(va),
        "arm_moved_values": moved,
    }


# ------------------------------------------------------------ object gates
def _iso_gas_gw(bundle: Path, year: int, hours: np.ndarray) -> float:
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & ch["klass"].isin(GAS_CLASSES)]
    tot = ch.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy()
    return float(tot[hours].mean()) / 1e3


def object_gates() -> dict:
    """The six pre-registered object gates, 2025 SHOULDER (all years/pops reported)."""
    import _miso211_rdt_binding_state as p  # the miso-211 readers, re-pointed to ARM

    m211 = json.loads(M211.read_text())["years"]
    out: dict = {"bands": OBJECT_BANDS, "years": {}}
    p.KEEPER = ARM  # network_/unit_hourly_/system_ sidecars of the ARM
    mon = p.m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    for year in YEARS:
        ind_act, _south = p.actual_hubs(year)
        pbc = p.pbc_hourly(year, "RDT_SO_MW")
        a = ind_act[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        pops = {"SHOULDER": shoulder, "TAIL": tail}
        has_net = (ARM / "hourly" / f"network_{year}.parquet").exists()
        has_uh = (ARM / "hourly" / f"unit_hourly_{year}.parquet").exists()
        cor = p.corridor(year) if has_net else None
        price, _lw, _dem, _sl = p.zone_prices(year)
        spread = price["MISO-Indiana"].to_numpy() - price["MISO-South"].to_numpy()
        fams, _gen_s = p.south_generation(year) if has_uh else ({}, None)
        yrec: dict = {}
        for k, idx in pops.items():
            rb = idx[pbc["any"][idx]]
            if rb.size == 0:
                continue
            ctrl_r1 = m211[str(year)]["r1_corridor"][k]["lp_in_real_s2n_hours"]
            ctrl_r2 = m211[str(year)]["r2b_south_boundary"][k]
            free_bind = (
                (cor["s2n_free_flow"] >= p.FREE_S2N - p.BIND_TOL)
                if cor is not None
                else None
            )
            arm_vals = {
                "O1_south_net_inflow_gw": (
                    round(
                        p._m(
                            cor["n2s_flow"] - cor["s2n_flow"] + cor["ext_south_flow"],
                            rb,
                        )
                        / 1e3,
                        3,
                    )
                    if cor is not None
                    else None
                ),
                "O2_s2n_flow_mean_mw": round(p._m(cor["s2n_flow"], rb), 1)
                if cor is not None
                else None,
                "O3_s2n_free_tier_share": round(p._share(rb, free_bind), 4)
                if cor is not None
                else None,
                "O4_spread_indiana_minus_south": round(p._m(spread, rb), 3),
                "O5_south_gas_gw": round(
                    p._m(fams.get("Gas", np.zeros(HOURS)), rb) / 1e3, 3
                )
                if has_uh
                else None,
            }
            ctrl_vals = {
                "O1_south_net_inflow_gw": ctrl_r2["model_south_net_inflow_gw_mean"],
                "O2_s2n_flow_mean_mw": ctrl_r1["s2n_flow_mean_mw"],
                "O3_s2n_free_tier_share": ctrl_r1["s2n_at_free_tier_share"],
                "O4_spread_indiana_minus_south": ctrl_r1[
                    "spread_indiana_minus_south_mean"
                ],
                "O5_south_gas_gw": ctrl_r2["south_gen_by_fuel_gw_model"]["Gas"],
            }
            iso_gas_c = _iso_gas_gw(CONTROL, year, rb)
            iso_gas_a = _iso_gas_gw(ARM, year, rb)
            mw_c = iso_gas_c - float(ctrl_vals["O5_south_gas_gw"])
            mw_a = (
                iso_gas_a - float(arm_vals["O5_south_gas_gw"])
                if arm_vals["O5_south_gas_gw"] is not None
                else None
            )
            gates = {}
            for g, (lo, hi) in OBJECT_BANDS.items():
                if g == "O6_midwest_gas_delta_gw":
                    val = None if mw_a is None else round(mw_a - mw_c, 3)
                    gates[g] = {
                        "control_midwest_gas_gw": round(mw_c, 3),
                        "arm_midwest_gas_gw": None if mw_a is None else round(mw_a, 3),
                        "iso_gas_classes_gw": {
                            "control": round(iso_gas_c, 3),
                            "arm": round(iso_gas_a, 3),
                        },
                        "delta": val,
                        "band": [lo, hi],
                        "inside": None if val is None else bool(lo <= val <= hi),
                    }
                else:
                    val = arm_vals[g]
                    gates[g] = {
                        "control": ctrl_vals[g],
                        "arm": val,
                        "band": [lo, hi],
                        "inside": None if val is None else bool(lo <= val <= hi),
                    }
            yrec[k] = {"hours_real_s2n": int(rb.size), "gates": gates}
        out["years"][year] = yrec
    return out


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso213-zonal-basis-layering-2026-09-05.md §3-§4 @ a1a4a48",
        "keeper_at_open": "2026-09-04-miso-210-clock",
        "delta": f"ScenarioConfig.{FIELD} False -> True on the keeper recipe (replay_keeper --set); the arm carries the code that threads the print-derived-cell mask",
        "control": CONTROL.name + " (the keeper itself; not re-solved)",
        "arm": ARM.name,
        "scorer_written_and_committed_before_any_arm_result": True,
        "c3a_is_never_a_gate": "rule 1 [R-STRUCT]; reported at full magnitude with the PREREG sign beside it",
    }
    out["S0"] = s0_inherited()
    print(
        "S-0",
        "PASS — inherited (control = keeper; miso-210 bit-identity)"
        if out["S0"]["passed"]
        else f"NOT ESTABLISHED {out['S0']}",
    )
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else f"VOID {out['S1']}")
    out["S2"] = s2_from_phase0()
    print(
        "S-2",
        "PASS — arm fuel prices live on the keeper chain"
        if out["S2"]["passed"]
        else "NOT LIVE",
    )

    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    out.update(kills(vc, va))
    out["movement"] = movement(vc, va)
    for k in ("K1", "K2", "K3", "K4", "K5", "K6"):
        pk = out[k]["passed"]
        print(k, "PASS" if pk is True else ("UNSCORED" if pk is None else "KILL"))
    try:
        out["object_gates"] = object_gates()
        og = (
            out["object_gates"]["years"]
            .get(2025, {})
            .get("SHOULDER", {})
            .get("gates", {})
        )
        for g, v in og.items():
            print(
                g,
                v.get("control", v.get("control_midwest_gas_gw")),
                "->",
                v.get("arm", v.get("delta")),
                "inside" if v.get("inside") else "OUTSIDE",
            )
    except Exception as exc:  # noqa: BLE001 — reported, never a kill
        out["object_gates"] = {"error": repr(exc)}
        print("object gates: ERROR", repr(exc))

    fired = [k for k in ("K1", "K2", "K3", "K4", "K5") if out[k]["passed"] is False]
    out["kills_fired"] = fired
    moved = out["movement"]["arm_moved_values"]
    if not out["S1"]["passed"]:
        out["verdict"] = (
            "VOID — not a single delta; the A/B does not measure the repair"
        )
    elif fired:
        out["verdict"] = (
            f"KILL FIRED ({', '.join(fired)}) — reported at full magnitude and NOT "
            "renegotiated. Under the owner's standing structural-integrity bar this is "
            "an OWNER DECISION, not an automatic reject; the scorer does not promote."
        )
    elif moved:
        out["verdict"] = (
            "KILLS SILENT and the arm MOVED values -> keeper candidate, PROMOTED as a "
            "structural rule-19 repair (PREREG §4). C3a is reported at full magnitude "
            "and is NEVER the justification."
        )
    else:
        out["verdict"] = (
            "INERT — no scored VALUE moved beyond epsilon. Per PREREG §4 the repair is "
            "STILL promoted (a double-counted premium is wrong at any magnitude), "
            "disclosed as inert."
        )
    print("VERDICT:", out["verdict"])
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
