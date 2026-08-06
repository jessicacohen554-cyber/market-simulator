#!/usr/bin/env python3
"""pjm-159 probe: reproduce every measurement in the PJM FINAL-declaration assessment.

Companion to ``results/calibration/ASSESSMENT-pjm159-final-declaration-2026-08-06.md``.
Four independent readiness checks, each printing the evidence the assessment
cites:

* **B1** — locked-test-year solvability: on-disk year coverage of the three
  inputs every PJM solve hard-requires (``calibration_reference.json`` PJM
  block, ``PJM_<y>_renewable_capacity.csv``, and the demand-profile artifact
  ``load_demand`` reads).
* **B2** — frozen-recipe reproducibility: the year keys of
  ``PJM_SEAM_LADDER_BY_YEAR`` and the rule-19 alternative that fires outside
  them, plus the two pooled-vintage overlays and the DA-virtual corpus.
* **B3** — the C3a scoring basis: per-year ``rt_lw``/``da_lw``/``rt``/``da``
  coverage in the committed bench parts, and the keeper's own gated C3a
  restated on the legacy equal-hour basis it would be forced onto outside
  2023-2025.
* **B4** — the DA-RT basis regime: PJM's measured DA-RT spread every committed
  year, which sets the ``pjm_da_virtual_bids`` layer's C1 contribution.

**Rule 22.** Nothing here solves, scores or registers any year. The
out-of-training figures are reads of MEASURED committed artifacts with no model
output on either side (the pjm-157 / pjm-158 §1 class of read) — present
precisely to size a governance risk WITHOUT spending the year. The only model
numbers are the keeper's own IN-SAMPLE 2023-2025 gated C3a, read from the
committed bundle via the committed-artifacts-only scorer.

Stdlib only (json, gzip, csv, re, pathlib, subprocess) so it runs in a bare
container with no numpy/pandas — the same posture as
``scripts/calibration_verdict.py``.

Usage::

    python scripts/probes/_pjm159_final_readiness.py
    python scripts/probes/_pjm159_final_readiness.py --json
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

KEEPER_RUN_ID = "2026-08-04-pjm-152-collapse"
KEEPER_BUNDLE = REPO / "results/calibration/pjm152_collapse_A"
BENCH_DIR = REPO / "frontend/data/backcast/bench/PJM"
CALREF = REPO / "data/raw/_validation-source/calibration_reference.json"
RENEW_GLOB = "PJM_*_renewable_capacity.csv"
RENEW_DIR = REPO / "data/raw/_validation-source"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp.json"
SPEC_PY = REPO / "src/market_sim/model/interchange/spec.py"
IMPORT_NODES_PY = REPO / "src/market_sim/model/interchange/import_nodes.py"
RAMP_LIB = REPO / "scripts/lib/ramp_capability/__init__.py"
CT_HR = REPO / "data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv"
DA_VIRTUALS = REPO / "data/raw/pjm-da-virtuals"

TRAIN_YEARS = (2023, 2024, 2025)
VALIDATION_YEAR = 2022
LOCKED_YEARS = (2019, 2026)  # 2026 = H1-2026
#: C3a PASS band, ``calibration_verdict.PRICE_MEAN_TOL`` (v2.3 owner amendment
#: 2026-07-09). Mirrored rather than imported so this probe stays stdlib-only
#: and cannot drift the scorer.
PRICE_MEAN_TOL = 0.10


# --------------------------------------------------------------------------
# B1 — can the locked-test years be solved at all?
# --------------------------------------------------------------------------
def check_solvability() -> dict:
    """Year coverage of the three inputs every PJM solve hard-requires.

    Returns:
        Mapping with the per-input year lists and the per-year verdict for the
        validation and locked years.
    """
    calref_years = sorted(
        int(y) for y in json.loads(CALREF.read_text())["isos"]["PJM"]
    )
    renew_years = sorted(
        int(m.group(1))
        for p in RENEW_DIR.glob(RENEW_GLOB)
        if (m := re.search(r"PJM_(\d{4})_renewable_capacity\.csv$", p.name))
    )
    # The demand-profile artifact is parquet and this probe is stdlib-only, so
    # its coverage is taken from the register's measured statement rather than
    # re-read here (docs/holdout-data-equivalency-register-2026-07.md §PJM:
    # "MISSING 2018-2020 (cross-ISO F3 blocker)"; 2021-2025 present).
    demand_years = [2021, 2022, 2023, 2024, 2025]

    out = {
        "calibration_reference_PJM_years": calref_years,
        "renewable_capacity_years": renew_years,
        "demand_profile_years_per_register": demand_years,
        "per_year": {},
    }
    for yr in (VALIDATION_YEAR, *LOCKED_YEARS):
        missing = []
        if yr not in calref_years:
            missing.append("calibration_reference.json isos.PJM")
        if yr not in renew_years:
            missing.append(f"PJM_{yr}_renewable_capacity.csv")
        if yr not in demand_years:
            missing.append("eia_demand_profiles.parquet (load_demand)")
        out["per_year"][yr] = {
            "solvable": not missing,
            "missing": missing,
        }
    return out


# --------------------------------------------------------------------------
# B2 — does the frozen keeper recipe reproduce outside 2023-2025?
# --------------------------------------------------------------------------
def check_recipe_reproducibility() -> dict:
    """Year-keyed and vintage-pooled inputs among the keeper's armed flags.

    Returns:
        Mapping describing the seam-ladder year keys, the rule-19 alternative
        that fires outside them, the pooled-vintage overlays and the
        DA-virtual corpus state.
    """
    spec = SPEC_PY.read_text().splitlines()
    start = next(
        i for i, ln in enumerate(spec) if ln.startswith("PJM_SEAM_LADDER_BY_YEAR")
    )
    ladder_years: list[int] = []
    depth = 0
    for ln in spec[start:]:
        depth += ln.count("{") - ln.count("}")
        if m := re.match(r"^    (\d{4}):", ln):
            ladder_years.append(int(m.group(1)))
        if depth == 0 and ladder_years:
            break

    nodes = IMPORT_NODES_PY.read_text()
    gate = "year in PJM_SEAM_LADDER_BY_YEAR" in nodes
    alternative = "if not _pjm_ladder_active and inject_reference_price_firm_export" in nodes

    pooled = re.search(r"POOLED_VINTAGES:.*?=\s*\((.*?)\)", RAMP_LIB.read_text())
    ramp_vintages = (
        [int(x) for x in re.findall(r"\d{4}", pooled.group(1))] if pooled else []
    )

    # csv.reader, not str.split: the artifact's `source` column is a quoted
    # provenance sentence containing commas, so naive splitting misaligns.
    with CT_HR.open(newline="") as fh:
        ct_spans = sorted({row["years"] for row in csv.DictReader(fh)})

    corpus = sorted(p.name for p in DA_VIRTUALS.glob("*.parquet"))

    keeper_flags = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    armed = {
        k: bool(keeper_flags["scenario_config"].get(k))
        for k in (
            "pjm_seam_measured_ladder",
            "measured_ramp_capability",
            "measured_ct_heat_rates",
            "pjm_da_virtual_bids",
        )
    }
    return {
        "keeper_armed": armed,
        "PJM_SEAM_LADDER_BY_YEAR_years": ladder_years,
        "ladder_gated_on_year": gate,
        "rule19_alternative_fires_outside": alternative,
        "ramp_capability_POOLED_VINTAGES": ramp_vintages,
        "ct_heat_rate_vintage_spans": ct_spans,
        "da_virtual_corpus_files_on_disk": len(corpus),
    }


# --------------------------------------------------------------------------
# B3 / B4 — the price bench: basis coverage, basis restatement, DA-RT regime
# --------------------------------------------------------------------------
def _bench_avg_lmp(year: int) -> dict | None:
    """The committed bench part's ``avgLMP`` block for a PJM year, or None."""
    p = BENCH_DIR / f"{year}.json.gz"
    if not p.exists():
        return None
    with gzip.open(p) as fh:
        return (json.load(fh).get("bench") or {}).get("avgLMP") or {}


def _gated_basis(avg: dict) -> tuple[str, str, bool]:
    """Mirror ``calibration_verdict.score_price_mean``'s v2.4 basis ladder.

    Returns:
        ``(benchmark_kind, bench_key, is_load_weighted)`` — ``rt_lw`` >
        ``da_lw`` > ``rt`` > ``da``, exactly as the scorer selects.
    """
    if avg.get("rt_lw") is not None:
        return "RT", "rt_lw", True
    if avg.get("da_lw") is not None:
        return "DA", "da_lw", True
    if avg.get("rt") is not None:
        return "RT", "rt", False
    return "DA", "da", False


def check_price_basis(keeper_c3a: dict[int, float]) -> dict:
    """Per-year bench basis coverage, and the keeper's C3a restated on ``rt``.

    Args:
        keeper_c3a: ``{year: model load-weighted mean LMP}`` from the keeper's
            own committed verdict (in-sample only).

    Returns:
        Mapping with per-year basis coverage and, for each in-sample year, the
        gated-vs-legacy C3a error pair plus whether the band verdict flips.
    """
    rows = {}
    for year in sorted({VALIDATION_YEAR, *TRAIN_YEARS}):
        avg = _bench_avg_lmp(year)
        if avg is None:
            continue
        kind, key, lw = _gated_basis(avg)
        row = {
            "da": avg.get("da"),
            "rt": avg.get("rt"),
            "da_lw": avg.get("da_lw"),
            "rt_lw": avg.get("rt_lw"),
            "gated_benchmark": f"{kind} ({'load-weighted' if lw else 'LEGACY equal-hour'})",
            "gated_key": key,
        }
        if avg.get("rt_lw") is not None and avg.get("rt") is not None:
            row["lw_uplift_usd"] = round(avg["rt_lw"] - avg["rt"], 3)
            row["lw_uplift_pct"] = round(100 * (avg["rt_lw"] / avg["rt"] - 1), 2)
        model = keeper_c3a.get(year)
        if model is not None and avg.get("rt_lw") and avg.get("rt"):
            e_lw = 100 * (model / avg["rt_lw"] - 1)
            e_leg = 100 * (model / avg["rt"] - 1)
            bar = 100 * PRICE_MEAN_TOL
            row["c3a_model"] = model
            row["c3a_err_gated_pct"] = round(e_lw, 2)
            row["c3a_err_legacy_pct"] = round(e_leg, 2)
            row["c3a_verdict_gated"] = "PASS" if abs(e_lw) <= bar else "FAIL"
            row["c3a_verdict_legacy"] = "PASS" if abs(e_leg) <= bar else "FAIL"
            row["verdict_flips_on_basis"] = (
                row["c3a_verdict_gated"] != row["c3a_verdict_legacy"]
            )
        rows[year] = row
    return rows


def check_dart_regime() -> dict:
    """PJM's measured DA-RT spread every committed year (measured data only).

    Returns:
        ``{year: {da, rt, spread, ...}}`` — the term that sets the DA-virtual
        layer's C1 contribution, `-(DA-RT) x gain`.
    """
    p = json.loads(ACTUAL_LMP.read_text())["PJM"]
    out = {}
    for y in sorted(p, key=int):
        v = p[y]
        da, rt = v.get("da"), v.get("rt")
        dalw, rtlw = v.get("da_lw"), v.get("rt_lw")
        out[int(y)] = {
            "da": da,
            "rt": rt,
            "spread": None if da is None or rt is None else round(da - rt, 3),
            "spread_lw": (
                None if dalw is None or rtlw is None else round(dalw - rtlw, 3)
            ),
            "tier": (
                "train"
                if int(y) in TRAIN_YEARS
                else "validation" if int(y) == VALIDATION_YEAR
                else "locked" if int(y) in LOCKED_YEARS
                else "outside-grant"
            ),
        }
    return out


def keeper_gated_c3a() -> dict[int, float]:
    """The keeper's own gated C3a model levels, from the committed scorer.

    In-sample 2023-2025 only. Runs ``calibration_verdict.py --json``, which
    reads committed artifacts and never solves.

    Returns:
        ``{year: model load-weighted mean LMP $/MWh}``.
    """
    import subprocess

    res = subprocess.run(
        [
            "python3",
            str(REPO / "scripts/calibration_verdict.py"),
            "--json",
            "--run-id",
            KEEPER_RUN_ID,
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=True,
    )
    d = json.loads(res.stdout)
    return {
        r["year"]: r["model"]
        for r in d["criteria"]["price_mean"]["records"]
        if r.get("key") is None and r.get("model") is not None
    }


def main() -> None:
    """Print all four readiness checks."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    c3a_model = keeper_gated_c3a()
    result = {
        "probe": "pjm-159 final-declaration readiness",
        "keeper": KEEPER_RUN_ID,
        "B1_solvability": check_solvability(),
        "B2_recipe_reproducibility": check_recipe_reproducibility(),
        "B3_price_basis": check_price_basis(c3a_model),
        "B4_dart_regime": check_dart_regime(),
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    b1 = result["B1_solvability"]
    print("=" * 74)
    print("B1 — can the out-of-training years be solved?")
    print("=" * 74)
    print(f"  calibration_reference.json isos.PJM : {b1['calibration_reference_PJM_years']}")
    print(f"  PJM_<y>_renewable_capacity.csv      : {b1['renewable_capacity_years']}")
    print(f"  eia_demand_profiles (per register)  : {b1['demand_profile_years_per_register']}")
    for yr, v in b1["per_year"].items():
        tag = "SOLVABLE" if v["solvable"] else "BLOCKED"
        print(f"  {yr}: {tag}")
        for m in v["missing"]:
            print(f"        missing: {m}")

    b2 = result["B2_recipe_reproducibility"]
    print()
    print("=" * 74)
    print("B2 — does the frozen keeper recipe reproduce outside 2023-2025?")
    print("=" * 74)
    print(f"  keeper armed flags                  : {b2['keeper_armed']}")
    print(f"  PJM_SEAM_LADDER_BY_YEAR years       : {b2['PJM_SEAM_LADDER_BY_YEAR_years']}")
    print(f"  ladder gated on `year in ...`       : {b2['ladder_gated_on_year']}")
    print(f"  rule-19 firm-export floor fires     : {b2['rule19_alternative_fires_outside']}"
          "   <- a DIFFERENT mechanism outside the ladder years")
    print(f"  ramp_capability POOLED_VINTAGES     : {b2['ramp_capability_POOLED_VINTAGES']}")
    print(f"  measured_ct_heat_rates vintages     : {b2['ct_heat_rate_vintage_spans']}")
    print(f"  pjm-da-virtuals parquets on disk    : {b2['da_virtual_corpus_files_on_disk']}"
          "   (loader RAISES on a missing month)")

    print()
    print("=" * 74)
    print("B3 — the C3a scoring basis (rt_lw > da_lw > rt > da), band +/-10%")
    print("=" * 74)
    print("  yr    da      rt    da_lw   rt_lw   gated basis                 "
          "C3a gated / legacy")
    for yr, r in result["B3_price_basis"].items():
        def f(x):
            return "  --  " if x is None else f"{x:6.2f}"
        tail = ""
        if "c3a_err_gated_pct" in r:
            tail = (
                f"   {r['c3a_err_gated_pct']:+.1f}% {r['c3a_verdict_gated']}"
                f" / {r['c3a_err_legacy_pct']:+.1f}% {r['c3a_verdict_legacy']}"
                + ("  <- FLIPS" if r["verdict_flips_on_basis"] else "")
            )
        print(f"  {yr} {f(r['da'])} {f(r['rt'])} {f(r['da_lw'])} {f(r['rt_lw'])}"
              f"  {r['gated_benchmark']:<26}{tail}")

    print()
    print("=" * 74)
    print("B4 — PJM's measured DA-RT spread by year (sets the layer's C1 term)")
    print("=" * 74)
    print("  yr      da      rt   DA-RT   DA-RT_lw   tier")
    for yr, r in result["B4_dart_regime"].items():
        sp = "  --  " if r["spread"] is None else f"{r['spread']:+6.2f}"
        splw = "   --   " if r["spread_lw"] is None else f"{r['spread_lw']:+8.2f}"
        print(f"  {yr}  {r['da']:6.2f}  {r['rt']:6.2f}  {sp}  {splw}   {r['tier']}")


if __name__ == "__main__":
    main()
