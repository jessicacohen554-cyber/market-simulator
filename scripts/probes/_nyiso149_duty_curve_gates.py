"""nyiso-149 — pre-registered A/B gates for the CHP lay-up duty CURVE (ARM F).

Scores PREREG-nyiso149-chp-duty-curve-2026-08-22.md §4 from committed/solved
artifacts only:

* IDENT — the base replay's bit-identity to the registered
  ``2026-08-20-nyiso-147a-chp-btm`` (max |Δprice| over every zone-hour, per
  year, against the registered bundle's committed hourly sidecars);
* F-K1 exactness — the arm's run_config differs in exactly one field;
* F-K2 liveness — band composition at the LP entry grain: the fleet each run's
  recorded config builds (no LP) has the census plants offering committed = 0,
  peak ≈ pct_peak·pmax, offered ≈ (pct_econ+pct_peak)·pmax, and zero
  non-census CHP plants with changed tranche composition;
* F-K3 graded conduct — per plant-year model CHP energy (dispatch parquets)
  vs the plant's own CAMPD gross meter: meter ≥ 20 GWh → multiple ∈
  [0.25, 2.5]; meter < 20 GWh → |model − meter| ≤ 40 GWh; plus the graded
  signature (cohort model energy highest in 2025);
* F-K4 — zero NEW failing D-1/D-2/D-4 rows vs the base's committed
  legitimacy_diagnostics (the arm's regenerated one is compared by
  (diagnostic, klass/mechanism, year) failing-row keys).

F-K5 (criteria) is read from ``calibration_verdict.py`` after registration —
the scorer is the authority, not this probe. F-K6 quantities are REPORTED.

Writes ``results/calibration/_nyiso149_duty_curve_gates.json``.
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

from market_sim.config.paths import CAMPD_UNIT_LEVEL_DIR, PROCESSED_DIR  # noqa: E402
from market_sim.data.campd import states_for_iso  # noqa: E402

ISO = "NYISO"
YEARS = (2023, 2024, 2025)
BASE = REPO / "results/calibration/nyiso149_base"
ARM = REPO / "results/calibration/nyiso149_armF"
REGISTERED_BASE = REPO / "results/calibration/nyiso147_armA"
OUT = REPO / "results/calibration/_nyiso149_duty_curve_gates.json"
CHP_GROUPS = ("CC_CHP", "CT_CHP", "ST_CHP")
METER_FLOOR_GWH = 20.0
MULT_LO, MULT_HI = 0.25, 2.5
ABS_GAP_GWH = 40.0


def census() -> dict[int, dict]:
    import csv

    with (PROCESSED_DIR / "chp_layup_census_NYISO.csv").open(newline="") as fh:
        return {
            int(r["plant_code"]): r
            for r in csv.DictReader(fh)
            if r["laid_up"].lower() == "true"
        }


def duty() -> dict[int, tuple[float, float]]:
    from market_sim.data.chp_layup import load_chp_duty_curve

    return load_chp_duty_curve(ISO)


def _p1(df: pd.DataFrame) -> pd.DataFrame:
    if "pass" in df.columns:
        passes = set(df["pass"].astype(str))
        keep = "P2" if "P2" in passes else "P1"
        return df[df["pass"].astype(str) == keep]
    return df


def ident_check() -> dict:
    """Max |Δ zonal price| of the fresh base vs the registered 147a sidecars."""
    out = {}
    fresh_all = pd.read_parquet(BASE / "system.parquet")
    for year in YEARS:
        fresh = _p1(fresh_all[fresh_all["year"] == year])
        reg = _p1(
            pd.read_parquet(REGISTERED_BASE / "hourly" / f"system_{year}.parquet")
        )
        f = fresh.pivot_table(index="hour", columns="zone", values="price")
        r = reg.pivot_table(index="hour", columns="zone", values="price")
        common = [c for c in f.columns if c in r.columns]
        d = float((f[common] - r[common]).abs().to_numpy().max())
        out[year] = round(d, 10)
    return out


def k1_exactness() -> dict:
    b = json.loads((BASE / "run_config.json").read_text())
    a = json.loads((ARM / "run_config.json").read_text())

    def flat(d, prefix=""):
        o = {}
        for k, v in d.items():
            if isinstance(v, dict):
                o.update(flat(v, f"{prefix}{k}."))
            else:
                o[f"{prefix}{k}"] = v
        return o

    fb, fa = flat(b), flat(a)
    # Provenance keys (when the solve ran, free-text notes) are metadata, not
    # config — excluded from the exactness diff (PREREG §7).
    _PROVENANCE = ("timestamp", "note", "git.", "hostname")
    diffs = {
        k: (fb.get(k), fa.get(k))
        for k in set(fb) | set(fa)
        if fb.get(k) != fa.get(k)
        and not any(k == p or k.startswith(p) or k.endswith("." + p) for p in _PROVENANCE)
    }
    ok = set(diffs) <= {
        "chp_layup_duty_curve",
        "scenario_config.chp_layup_duty_curve",
        "calibration_flags.chp_layup_duty_curve",
    } and any("chp_layup_duty_curve" in k for k in diffs)
    return {"pass": bool(ok), "diffs": {k: list(v) for k, v in diffs.items()}}


def _fleet_caps(run_dir: Path) -> dict[int, dict[str, float]]:
    """Tranche caps per CHP plant from the run's recorded config (no LP)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import load_fleet_from_csv
    from market_sim.data.fleet.assembly import bins_to_fleet
    from market_sim.data.fleet.campd_bins import fleet_to_bins

    rc = json.loads((run_dir / "run_config.json").read_text())
    sc = rc.get("scenario_config") or {}
    fields = set(ScenarioConfig.__dataclass_fields__)
    cfg = ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})
    iso_config = get_iso_config(ISO)
    gens = load_fleet_from_csv(ISO, iso_config, year=2024)
    bins = fleet_to_bins(gens, ISO, cfg)
    fleet, _ = bins_to_fleet(bins, sorted({g.zone for g in gens}), cfg)
    out: dict[int, dict[str, float]] = {}
    for g in fleet:
        if g.plant_group in CHP_GROUPS and g.plant_code > 0:
            d = out.setdefault(int(g.plant_code), {})
            tranche = g.unit_id.rsplit("_", 1)[-1]
            key = (
                "peak"
                if tranche.startswith("peak") or "_peak" in g.unit_id
                else ("committed" if "_committed" in g.unit_id else "other")
            )
            d[key] = d.get(key, 0.0) + float(g.pmax_mw)
            d["total"] = d.get("total", 0.0) + float(g.pmax_mw)
    return out


def k2_liveness() -> dict:
    dc = duty()
    base_caps = _fleet_caps(BASE)
    arm_caps = _fleet_caps(ARM)
    plants, ok = {}, True
    for code, (pe_mw, pp_mw) in sorted(dc.items()):
        a = arm_caps.get(code, {})
        # MW contract (PREREG §7): the artifact's MW ARE the wanted caps.
        want_total = pe_mw + pp_mw
        want_peak = pp_mw
        got_total = a.get("total", 0.0)
        got_peak = a.get("peak", 0.0)
        row_ok = (
            abs(got_total - want_total) <= 0.1
            and abs(got_peak - want_peak) <= 0.1
            and a.get("committed", 0.0) == 0.0
        )
        ok &= row_ok
        plants[code] = {
            "want_total_mw": round(want_total, 2),
            "got_total_mw": round(got_total, 2),
            "want_peak_mw": round(want_peak, 2),
            "got_peak_mw": round(got_peak, 2),
            "committed_mw": round(a.get("committed", 0.0), 2),
            "ok": row_ok,
        }
    moved = {
        c: {"base": base_caps.get(c), "arm": arm_caps.get(c)}
        for c in set(base_caps) | set(arm_caps)
        if c not in dc
        and {
            k: round(v, 3) for k, v in (base_caps.get(c) or {}).items()
        }
        != {k: round(v, 3) for k, v in (arm_caps.get(c) or {}).items()}
    }
    ok &= not moved
    return {"pass": bool(ok), "plants": plants, "non_census_moved": moved}


def campd_meter() -> dict[int, dict[int, float]]:
    """Per plant-year CAMPD gross GWh for the census plants."""
    codes = set(duty())
    out: dict[int, dict[int, float]] = {c: {} for c in codes}
    for year in YEARS:
        for state in states_for_iso(ISO):
            p = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not p.exists():
                continue
            df = pd.read_parquet(p, columns=["facilityId", "grossLoad"])
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            for code, g in df.groupby("facilityId"):
                out[int(code)][year] = out[int(code)].get(year, 0.0) + float(
                    pd.to_numeric(g["grossLoad"], errors="coerce").fillna(0.0).sum()
                    / 1000.0
                )
    return out


def model_energy(run_dir: Path) -> dict[int, dict[int, float]]:
    codes = set(duty())
    out: dict[int, dict[int, float]] = {c: {} for c in codes}
    for year in YEARS:
        p = run_dir / "dispatch" / f"{year}_P1.parquet"
        df = pd.read_parquet(p, columns=["plant_code", "klass", "mw"])
        df = df[df["plant_code"].isin(codes) & df["klass"].isin(CHP_GROUPS)]
        for code, g in df.groupby("plant_code"):
            out[int(code)][year] = float(g["mw"].sum()) / 1000.0
    return out


def k3_conduct() -> dict:
    meter = campd_meter()
    base_e = model_energy(BASE)
    arm_e = model_energy(ARM)
    rows, ok = [], True
    for code in sorted(meter):
        for year in YEARS:
            m = meter[code].get(year, 0.0)
            a = arm_e[code].get(year, 0.0)
            b = base_e[code].get(year, 0.0)
            if m >= METER_FLOOR_GWH:
                mult = a / m if m > 0 else float("inf")
                row_ok = MULT_LO <= mult <= MULT_HI
                basis = f"mult={mult:.2f}"
            else:
                row_ok = abs(a - m) <= ABS_GAP_GWH
                basis = f"absgap={abs(a - m):.1f}"
            ok &= row_ok
            rows.append(
                {
                    "plant": code,
                    "year": year,
                    "meter_gwh": round(m, 1),
                    "base_gwh": round(b, 1),
                    "arm_gwh": round(a, 1),
                    "basis": basis,
                    "ok": row_ok,
                }
            )
    cohort_by_year = {
        y: round(sum(arm_e[c].get(y, 0.0) for c in arm_e), 1) for y in YEARS
    }
    graded = cohort_by_year[2025] == max(cohort_by_year.values())
    ok &= graded
    return {
        "pass": bool(ok),
        "rows": rows,
        "cohort_arm_gwh_by_year": cohort_by_year,
        "graded_signature_2025_highest": graded,
    }


def _failing_keys(diag: dict) -> set[str]:
    """Normalized failure identities from diagnostics.{D1,D2,D4}.failures.

    The magnitude tail of each failure string is stripped (a share that moves
    a little is the same failure, not a new one): D4 keys keep the
    ``<year> <mechanism> × <class>: plant <id>`` head, D1/D2 keep the text
    before the first colon (e.g. ``2024 ST_GAS``).
    """
    keys = set()
    for name in ("D1", "D2", "D4"):
        for f in diag.get("diagnostics", {}).get(name, {}).get("failures", []) or []:
            head = str(f).split(" is floored")[0]
            if " is floored" not in str(f):
                head = str(f).split(":")[0]
            keys.add(f"{name}|{head.strip()}")
    return keys


def k4_conduct_rows() -> dict:
    base_d = json.loads((REGISTERED_BASE / "legitimacy_diagnostics.json").read_text())
    arm_d = json.loads((ARM / "legitimacy_diagnostics.json").read_text())
    base_k, arm_k = _failing_keys(base_d), _failing_keys(arm_d)
    new = arm_k - base_k
    return {
        "pass": not new,
        "new_failing_rows": sorted(new),
        "cleared_rows": sorted(base_k - arm_k),
    }


def k6_reported() -> dict:
    out = {}
    for label, run_dir in (("base", BASE), ("arm", ARM)):
        sys_df = pd.read_parquet(run_dir / "system.parquet")
        for year in YEARS:
            s = _p1(sys_df[sys_df["year"] == year])
            lw = float((s["price"] * s["demand"]).sum() / s["demand"].sum())
            out[f"{label}_{year}_lw"] = round(lw, 2)
    return out


def main() -> None:
    report = {
        "session": "nyiso-149",
        "prereg": "PREREG-nyiso149-chp-duty-curve-2026-08-22.md",
        "ident_max_abs_dprice": ident_check(),
        "F-K1": k1_exactness(),
        "F-K2": k2_liveness(),
        "F-K3": k3_conduct(),
        "F-K4": k4_conduct_rows(),
        "F-K6_reported": k6_reported(),
    }
    report["all_gates_pass"] = all(
        report[k]["pass"] for k in ("F-K1", "F-K2", "F-K3", "F-K4")
    )
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
