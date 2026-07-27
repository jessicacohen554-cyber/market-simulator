"""pjm-133 A/B gate scorer: `hydro_budget_nameplate_aware` vs same-HEAD control.

Scores EXACTLY the gates pre-registered in
``results/calibration/PREREG-pjm133-hydro-budget-nameplate-aware-2026-07-27.md``
— P1/P2/P3/P4 and K1..K5 — and nothing else. It reads only committed artifacts:
the two solved bundles' ``hourly/*.parquet`` sidecars and
``legitimacy_diagnostics.json``, the committed ``bench/PJM/<year>.json.gz``
benchmark parts, raw EIA-860/923/930 through the no-LP ``build_hydro_fleet``
path, and (optionally) the two arms' ``calibration_verdict.py --json`` outputs
for the rubric-level kills. **No LP is built or solved.**

Split of responsibilities, mirroring caiso-130's scorer:

* **P1/P2/P4/K5** are bundle-internal and need no registration — they come from
  the class hourlies plus the same ``build_hydro_fleet`` diff the precheck used.
* **P3** reads both arms' ``legitimacy_diagnostics.json`` (generate it for BOTH
  arms before scoring — caiso-130 hit the vacuous-pass trap here).
* **K1/K2/K3/K4** are rubric-level and are scored from the two verdict JSONs,
  which exist once both arms are registered (rule 15, in-session).

Usage:
    PYTHONPATH=.:src:scripts/probes .venv/bin/python \
        scripts/probes/_pjm133_nameplate_ab.py \
        --control results/calibration/pjm133_control_A \
        --arm     results/calibration/pjm133_nameplate_B \
        [--control-verdict A.json --arm-verdict B.json]
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.hydro import build_hydro_fleet, hours_per_month  # noqa: E402

YEARS = (2023, 2024, 2025)
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "PJM"
SEAM_ZONE = "PJM_external"
WINDOWS: dict[str, range] = {
    "overnight": range(0, 7),
    "belly": range(9, 16),
    "evening": range(17, 22),
    "late": range(22, 24),
}
KEEPER_HYDRO = dict(backfill_year=2024, eia930_monthly=True, ror_split=False, min_flow_floor=False)

# --- pre-registered thresholds (PREREG §5-§6). Nothing here is tunable. ------
P1_DELIVERY_FRAC = 0.60  # PRIMARY size limb
P3_D2_MOVE_PP = 2.0  # max D-2 forced-share move per class per year
K1_C3A_PP = 0.75  # max increase in |C3a error|, pp
K2_C1_TWH = 0.50  # max increase in sum |C1 gap| over gated classes, TWh
K3_CO2_PP = 1.0  # max increase in |C5a error|, pp
K3_CO2_BAND_PP = 7.0  # C5a target band
IDENTITY_TOL_MWH = 1e-6  # P2 month-total identity
BASIS_TOL_MW = 1e-6  # arm-A-reproduces-keeper basis check


def class_pivot(bundle: Path, year: int) -> pd.DataFrame:
    """Return a bundle's P1 class dispatch as an (hour x class) pivot (MW)."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot_table(
        index="hour", columns="klass", values="mw", observed=True
    ).sort_index()


def pjm_lambda_and_demand(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (demand-weighted hourly lambda, hourly PJM-internal demand)."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[(frame["pass"] == "P1") & (frame["zone"] != SEAM_ZONE)]
    num = (frame["price"] * frame["demand"]).groupby(frame["hour"]).sum()
    den = frame["demand"].groupby(frame["hour"]).sum()
    return (num / den).sort_index().to_numpy(float), den.sort_index().to_numpy(float)


def bench(year: int) -> dict:
    """Return the committed C1/C5a benchmark payload for a PJM year."""
    with gzip.open(BENCH / f"{year}.json.gz") as handle:
        return json.load(handle)["bench"]


def moved_energy(year: int) -> float:
    """Return the flag's re-allocated MWh for a year (no LP)."""
    zone_names = get_iso_config("PJM").zone_names
    common = dict(
        zone_names=zone_names,
        backfill_year=KEEPER_HYDRO["backfill_year"],
        eia930_monthly=KEEPER_HYDRO["eia930_monthly"],
        forecast_budget=False,
        ror_split=KEEPER_HYDRO["ror_split"],
        min_flow_floor=KEEPER_HYDRO["min_flow_floor"],
    )
    _ua, mon_a = build_hydro_fleet("PJM", year, nameplate_aware_target=False, **common)
    _ub, mon_b = build_hydro_fleet("PJM", year, nameplate_aware_target=True, **common)
    return float(np.maximum(mon_b - mon_a, 0.0).sum())


def budget_identity(year: int) -> dict:
    """Return the P2/K5 identity facts for a year (no LP)."""
    zone_names = get_iso_config("PJM").zone_names
    common = dict(
        zone_names=zone_names,
        backfill_year=KEEPER_HYDRO["backfill_year"],
        eia930_monthly=KEEPER_HYDRO["eia930_monthly"],
        forecast_budget=False,
        ror_split=KEEPER_HYDRO["ror_split"],
        min_flow_floor=KEEPER_HYDRO["min_flow_floor"],
    )
    units_a, mon_a = build_hydro_fleet("PJM", year, nameplate_aware_target=False, **common)
    units_b, mon_b = build_hydro_fleet("PJM", year, nameplate_aware_target=True, **common)
    hpm = hours_per_month().astype(float)
    cap = np.array([u.pmax_mw for u in units_a], dtype=float)[:, None] * hpm[None, :]
    return {
        "n_plants_a": len(units_a),
        "n_plants_b": len(units_b),
        "month_total_drift_mwh": float(np.abs(mon_b.sum(axis=0) - mon_a.sum(axis=0)).max()),
        "over_mwh_a": float(np.maximum(0.0, mon_a - cap).sum()),
        "over_mwh_b": float(np.maximum(0.0, mon_b - cap).sum()),
        "over_pm_b": int((np.maximum(0.0, mon_b - cap) > 1e-9).sum()),
    }


def basis_check(control: Path, keeper: Path) -> dict:
    """Max hourly |A - keeper| per class, all years (the PREREG §6 precondition)."""
    out: dict[int, dict] = {}
    for year in YEARS:
        a, k = class_pivot(control, year), class_pivot(keeper, year)
        shared = sorted(set(a.columns) & set(k.columns))
        deltas = {c: float(np.abs(a[c].to_numpy(float) - k[c].to_numpy(float)).max()) for c in shared}
        out[year] = {
            "max_abs_delta_mw": max(deltas.values()) if deltas else float("nan"),
            "hydro_max_abs_delta_mw": deltas.get("hydro", float("nan")),
            "classes_compared": len(shared),
            "classes_only_in_one_arm": sorted(set(a.columns) ^ set(k.columns)),
        }
    return out


def score_p1(control: Path, arm: Path) -> dict:
    """P1 PRIMARY — the hydro volume deficit closes, all three years."""
    print("=== P1 (PRIMARY) — C1 hydro volume closes, direction + size ===")
    out: dict[int, dict] = {}
    verdicts = []
    for year in YEARS:
        a = float(class_pivot(control, year)["hydro"].sum() / 1e6)
        b = float(class_pivot(arm, year)["hydro"].sum() / 1e6)
        actual = float(bench(year)["classFull"]["hydro"])
        moved = moved_energy(year) / 1e6
        need = P1_DELIVERY_FRAC * moved
        direction = (b > a) and (abs(b - actual) < abs(a - actual))
        size = (b - a) >= need
        ok = direction and size
        verdicts.append(ok)
        out[year] = {
            "model_a_twh": a,
            "model_b_twh": b,
            "actual_twh": actual,
            "gap_a_twh": a - actual,
            "gap_b_twh": b - actual,
            "rise_twh": b - a,
            "moved_twh": moved,
            "delivered_share": (b - a) / moved if moved else float("nan"),
            "need_twh": need,
            "direction_ok": bool(direction),
            "size_ok": bool(size),
            "pass": bool(ok),
        }
        print(
            f"  {year}: hydro {a:6.3f} -> {b:6.3f} TWh (rise {b - a:+6.3f}, "
            f"{100.0 * (b - a) / moved:5.1f} % of the {moved:.3f} TWh re-allocation, "
            f"need >= {need:+.3f}) | gap {a - actual:+6.3f} -> {b - actual:+6.3f} "
            f"=> {'PASS' if ok else 'FAIL'}"
        )
    print(f"  P1 verdict: {'PASS' if all(verdicts) else 'FAIL'} (all three years required)")
    return {"years": out, "pass": bool(all(verdicts))}


def score_p2_k5(arm: Path) -> dict:
    """P2/K5 — the mechanism identity and no silent structural change."""
    print("\n=== P2 / K5 — mechanism identity, no silent structural change ===")
    out: dict[int, dict] = {}
    verdicts = []
    for year in YEARS:
        idn = budget_identity(year)
        ok = (
            idn["n_plants_a"] == idn["n_plants_b"]
            and idn["month_total_drift_mwh"] < IDENTITY_TOL_MWH
            and idn["over_mwh_b"] < 1e-6
            and idn["over_pm_b"] == 0
        )
        verdicts.append(ok)
        out[year] = {**idn, "pass": bool(ok)}
        print(
            f"  {year}: plants {idn['n_plants_a']}/{idn['n_plants_b']} | month drift "
            f"{idn['month_total_drift_mwh']:.2e} MWh | undeliverable "
            f"{idn['over_mwh_a'] / 1e3:7.1f} -> {idn['over_mwh_b']:.1f} GWh over "
            f"{idn['over_pm_b']} plant-months => {'PASS' if ok else 'FAIL'}"
        )
    print(f"  P2/K5 verdict: {'PASS' if all(verdicts) else 'FAIL'}")
    return {"years": out, "pass": bool(all(verdicts))}


def _diag_rows(bundle: Path, block: str) -> list[dict]:
    """Return a bundle's ``legitimacy_diagnostics.json`` rows for one D-block."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return []
    doc = json.loads(path.read_text())
    return list(doc.get("diagnostics", {}).get(block, {}).get("rows", []) or [])


def _d2_shares(bundle: Path) -> dict:
    """Return {(year, class, mechanism): share_of_class} from a bundle's D-2 rows."""
    return {
        (row.get("year"), row.get("class", ""), row.get("mechanism")): float(row.get("share_of_class", 0.0))
        for row in _diag_rows(bundle, "D2")
    }


def _d4_offwindow(bundle: Path) -> dict:
    """Return {(year, floor): offwindow_share} from a bundle's D-4 rows."""
    return {
        (row.get("year"), row.get("floor")): float(row.get("offwindow_share", 0.0))
        for row in _diag_rows(bundle, "D4")
    }


def score_p3(control: Path, arm: Path) -> dict:
    """P3 — D-2 forced shares and D-4 off-window binding stay clean."""
    print("\n=== P3 — mechanism accounting (D-2 forced share, D-4 off-window) ===")
    a, b = _d2_shares(control), _d2_shares(arm)
    if not a or not b:
        print(
            "  MISSING legitimacy_diagnostics.json in one or both arms — P3 cannot be\n"
            "  scored. Generate it for BOTH arms before quoting any P3 result\n"
            "  (this is the caiso-130 vacuous-pass trap; it is reported, never passed)."
        )
        return {"pass": None, "reason": "legitimacy_diagnostics.json absent"}
    moves, worst = {}, 0.0
    for key in sorted(set(a) | set(b), key=str):
        delta_pp = 100.0 * (b.get(key, 0.0) - a.get(key, 0.0))
        moves[str(key)] = delta_pp
        worst = max(worst, abs(delta_pp))
        if abs(delta_pp) > 0.05:
            print(
                f"  D-2 {key}: {100.0 * a.get(key, 0.0):6.2f} -> "
                f"{100.0 * b.get(key, 0.0):6.2f} pp ({delta_pp:+.2f})"
            )
    hydro_b = {k: v for k, v in b.items() if (k[1] or "") == "hydro"}
    hydro_ok = all(abs(v) < 1e-9 for v in hydro_b.values()) if hydro_b else True

    d4a, d4b = _d4_offwindow(control), _d4_offwindow(arm)
    d4_worst, d4_rows = 0.0, {}
    for key in sorted(set(d4a) | set(d4b), key=str):
        delta = d4b.get(key, 0.0) - d4a.get(key, 0.0)
        d4_rows[str(key)] = {"a": d4a.get(key), "b": d4b.get(key), "delta": delta}
        d4_worst = max(d4_worst, delta)
        if delta > 1e-9:
            print(f"  D-4 {key}: off-window {d4a.get(key):.4f} -> {d4b.get(key):.4f} (+{delta:.4f})")
    d4_ok = d4_worst <= 1e-9

    ok = worst <= P3_D2_MOVE_PP and hydro_ok and d4_ok
    print(
        f"  worst D-2 move {worst:.2f} pp (bound {P3_D2_MOVE_PP}) | hydro forced share "
        f"{'stays 0.0 %' if hydro_ok else 'NON-ZERO — K5 breach'} | worst D-4 off-window "
        f"increase {d4_worst:+.4f} => {'PASS' if ok else 'FAIL'}"
    )
    return {
        "pass": bool(ok),
        "worst_move_pp": worst,
        "hydro_forced_zero": bool(hydro_ok),
        "d4_worst_increase": d4_worst,
        "moves": moves,
        "d4": d4_rows,
    }


def score_p4(control: Path, arm: Path) -> dict:
    """P4 — destination attribution. REPORTED, not gated (PREREG §3/§5)."""
    from market_sim.data.eia930.envelopes import _hydro_wat_month_hod

    print("\n=== P4 — destination of the freed water (REPORTED, NOT GATED) ===")
    out: dict[int, dict] = {}
    for year in YEARS:
        ha = class_pivot(control, year)["hydro"].to_numpy(float)
        hb = class_pivot(arm, year)["hydro"].to_numpy(float)
        meas = _hydro_wat_month_hod("PJM", year)["mw"].to_numpy(float)[: len(ha)]
        hod = np.arange(len(ha)) % 24
        rise = float(np.mean(hb - ha))
        row = {"annual_rise_mw": rise}
        print(f"  {year}: annual rise {rise:+.1f} MW")
        for name, win in WINDOWS.items():
            sel = np.isin(hod, list(win))
            d = float(np.mean((hb - ha)[sel]))
            # Share of the annual energy rise landing in this window.
            share = float(((hb - ha)[sel].sum()) / max((hb - ha).sum(), 1e-9))
            row[f"delta_{name}_mw"] = d
            row[f"share_{name}"] = share
            row[f"gap_a_{name}_mw"] = float(np.nanmean((ha - meas)[sel]))
            row[f"gap_b_{name}_mw"] = float(np.nanmean((hb - meas)[sel]))
            print(
                f"      {name:>9}: {d:+8.1f} MW ({100.0 * share:5.1f} % of the rise) | "
                f"gap vs measured WAT {np.nanmean((ha - meas)[sel]):+8.1f} -> "
                f"{np.nanmean((hb - meas)[sel]):+8.1f} MW  [PS-confounded, see PREREG §3]"
            )
        out[year] = row
    return {"years": out, "gated": False}


def _verdict_levels(path: Path | None) -> dict:
    """Return {criterion: {year: (model, actual, status)}} from a verdict JSON."""
    if path is None or not Path(path).exists():
        return {}
    doc = json.loads(Path(path).read_text())
    out: dict[str, dict] = {
        "price_mean": {},
        "co2": {},
        "fuelmix": {},  # gated records only (status limbs)
        "fuelmix_all": {},  # every reported record, gated or SKIPPED (K2 magnitude)
        "_status": {},
    }
    for cid, block in doc.get("criteria", {}).items():
        out["_status"][cid] = block.get("status")
        for rec in block.get("records", []):
            year = rec.get("year")
            model, actual = rec.get("model"), rec.get("actual")
            if cid == "fuelmix" and model is not None and actual is not None:
                out["fuelmix_all"].setdefault(year, {})[rec.get("key")] = (
                    model,
                    actual,
                    rec.get("status"),
                )
            if rec.get("status") == "SKIPPED":
                continue
            if cid in ("price_mean", "co2") and rec.get("key") in (None, ""):
                out[cid][year] = (model, actual, rec.get("status"))
            elif cid == "fuelmix":
                out["fuelmix"].setdefault(year, {})[rec.get("key")] = (
                    model,
                    actual,
                    rec.get("status"),
                )
    out["determination"] = doc.get("determination")
    return out


def _pct_err(model, actual) -> float:
    return abs(float(model) / float(actual) - 1.0) * 100.0


def score_kills(
    va: Path | None, vb: Path | None, control_bundle: Path, arm_bundle: Path
) -> dict:
    """K1..K4 — the rubric-level kills, from the two arms' verdict JSONs.

    K2's magnitude limb also needs the two bundles' own hydro volumes, because
    hydro is not a C1 record (PREREG §2) and must nonetheless be inside the sum.
    """
    print("\n=== K1..K4 — rubric-level kills ===")
    a, b = _verdict_levels(va), _verdict_levels(vb)
    if not a or not b:
        print(
            "  verdict JSON missing for one or both arms — register both arms\n"
            "  (rule 15) and re-run with --control-verdict/--arm-verdict."
        )
        return {"pass": None, "reason": "verdict JSON absent"}
    res: dict[str, dict] = {}

    # K1 — C3a guard.
    k1_ok, k1 = True, {}
    for year in YEARS:
        if year not in a["price_mean"] or year not in b["price_mean"]:
            continue
        ea = _pct_err(*a["price_mean"][year][:2])
        eb = _pct_err(*b["price_mean"][year][:2])
        ok = (eb - ea) <= K1_C3A_PP
        k1_ok &= ok
        k1[year] = {"err_a_pp": ea, "err_b_pp": eb, "move_pp": eb - ea, "pass": bool(ok)}
        print(
            f"  K1 C3a {year}: |err| {ea:5.2f} -> {eb:5.2f} pp (move {eb - ea:+5.2f}, "
            f"bound {K1_C3A_PP:+.2f}) model {a['price_mean'][year][0]:.2f} -> "
            f"{b['price_mean'][year][0]:.2f} => {'ok' if ok else 'KILL'}"
        )
    res["K1"] = {"years": k1, "pass": bool(k1_ok)}

    # K2 — volume collateral. The magnitude limb runs over the eight C1 fossil
    # classes PLUS hydro, using every REPORTED model/actual pair whether gated
    # or SKIPPED (all of PJM's 2025 C1 is skipped for the preliminary EIA-923
    # vintage, so a gated-only sum would pass 2025 vacuously — PREREG §2/§6).
    # Hydro is in the sum on purpose: C1 scores fossil only, so a fossil-only
    # sum would worsen by the full displacement as pure arithmetic.
    k2_ok, k2 = True, {}
    for year in YEARS:
        ca, cb = a["fuelmix_all"].get(year, {}), b["fuelmix_all"].get(year, {})
        shared = sorted(set(ca) & set(cb))
        sa = sum(abs(ca[k][0] - ca[k][1]) for k in shared)
        sb = sum(abs(cb[k][0] - cb[k][1]) for k in shared)
        # Hydro leg, from the bundles' own class hourlies against the benchmark.
        ha = float(class_pivot(control_bundle, year)["hydro"].sum() / 1e6)
        hb = float(class_pivot(arm_bundle, year)["hydro"].sum() / 1e6)
        hact = float(bench(year)["classFull"]["hydro"])
        sa += abs(ha - hact)
        sb += abs(hb - hact)
        flips = [
            k
            for k in shared
            if ca[k][2] == "PASS" and cb[k][2] == "FAIL"
        ]
        ok = (sb - sa) <= K2_C1_TWH and not flips
        k2_ok &= ok
        k2[year] = {
            "sum_abs_gap_a_twh": sa,
            "sum_abs_gap_b_twh": sb,
            "move_twh": sb - sa,
            "n_fossil_classes": len(shared),
            "hydro_gap_a_twh": ha - hact,
            "hydro_gap_b_twh": hb - hact,
            "pass_to_fail": flips,
            "pass": bool(ok),
        }
        print(
            f"  K2 vol {year}: sum|gap| over {len(shared)} fossil + hydro {sa:7.3f} -> "
            f"{sb:7.3f} TWh (move {sb - sa:+6.3f}, bound {K2_C1_TWH:+.2f}) "
            f"PASS->FAIL {flips or 'none'} => {'ok' if ok else 'KILL'}"
        )
    res["K2"] = {"years": k2, "pass": bool(k2_ok)}

    # K3 — C5a CO2.
    k3_ok, k3 = True, {}
    for year in YEARS:
        if year not in a["co2"] or year not in b["co2"]:
            continue
        ea, eb = _pct_err(*a["co2"][year][:2]), _pct_err(*b["co2"][year][:2])
        ok = (eb - ea) <= K3_CO2_PP and eb <= K3_CO2_BAND_PP
        k3_ok &= ok
        k3[year] = {"err_a_pp": ea, "err_b_pp": eb, "move_pp": eb - ea, "pass": bool(ok)}
        print(
            f"  K3 CO2 {year}: |err| {ea:5.2f} -> {eb:5.2f} pp (move {eb - ea:+5.2f}, "
            f"bound {K3_CO2_PP:+.2f}, band {K3_CO2_BAND_PP:.0f}) => {'ok' if ok else 'KILL'}"
        )
    res["K3"] = {"years": k3, "pass": bool(k3_ok)}

    # K4 — rubric non-regression.
    regress = [
        cid
        for cid, st in a["_status"].items()
        if st == "PASS" and b["_status"].get(cid) == "FAIL"
    ]
    res["K4"] = {
        "pass": not regress,
        "regressed": regress,
        "determination_a": a.get("determination"),
        "determination_b": b.get("determination"),
    }
    print(
        f"  K4 rubric: A {a.get('determination')} -> B {b.get('determination')} | "
        f"PASS->FAIL {regress or 'none'} => {'ok' if not regress else 'KILL'}"
    )
    res["pass"] = bool(res["K1"]["pass"] and res["K2"]["pass"] and res["K3"]["pass"] and res["K4"]["pass"])
    return res


def main() -> None:
    logging.basicConfig(level=logging.ERROR)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument("--keeper", type=Path, default=REPO / "results" / "calibration" / "pjm121_ccbelt")
    ap.add_argument("--control-verdict", type=Path)
    ap.add_argument("--arm-verdict", type=Path)
    ap.add_argument("--json-out", type=Path, default=REPO / "results" / "probes" / "pjm133_ab.json")
    args = ap.parse_args()

    print("=== BASIS — does arm A reproduce the committed keeper digit-for-digit? ===")
    basis = basis_check(args.control, args.keeper)
    for year, row in basis.items():
        print(
            f"  {year}: max |A - keeper| over {row['classes_compared']} classes "
            f"{row['max_abs_delta_mw']:.6f} MW (hydro {row['hydro_max_abs_delta_mw']:.6f}) "
            f"=> {'CLEAN' if row['max_abs_delta_mw'] < BASIS_TOL_MW else 'BASIS CAVEAT'}"
        )
    print()

    out = {
        "basis": basis,
        "P1": score_p1(args.control, args.arm),
        "P2_K5": score_p2_k5(args.arm),
        "P3": score_p3(args.control, args.arm),
        "P4": score_p4(args.control, args.arm),
        "kills": score_kills(args.control_verdict, args.arm_verdict, args.control, args.arm),
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
