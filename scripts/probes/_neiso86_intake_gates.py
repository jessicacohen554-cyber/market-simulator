#!/usr/bin/env python3
"""Evaluate the neiso-86 pre-registered intake gates V1-V5. **BUILDS NO LP.**

Scores the NEISO gas-basis intake against the gates fixed in advance in
``results/calibration/PREREG-neiso86-gas-basis-intake-2026-08-06.md`` (written and
committed BEFORE any data byte was edited). Every check is pure data inspection or
a byte comparison against the pre-intake blobs read from git -- no dispatch solve,
no scoring, no registration, consistent with rule 22 channel 1 (intake is validated
no-LP only) and with the ACTIVE holdout spend freeze.

    V1  seasonality sign: winter(Jan,Feb,Dec) - summer(Jun,Jul,Aug) > 0
    V2  in-sample invariance: NEISO 2023-2025 rows and every pre-existing
        Algonquin-daily row byte-identical before and after
    V3  level plausibility: corrected hub month >= measured EIA-923 ISO-month
        delivered cost in Jan/Feb/Dec
    V4  no residual fitting (process gate; reported, asserted by inspection)
    V5  cross-ISO non-interference: no non-NEISO row changes

Usage::

    PYTHONPATH=src python scripts/probes/_neiso86_intake_gates.py
"""

from __future__ import annotations

import csv
import io
import json
import subprocess
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
BASIS_REL = "data/raw/gas_basis_by_iso_month.csv"
AGT_REL = "data/raw/gas-prices/algonquin_citygate_daily.csv"
HH_REL = "data/raw/gas-prices/henry_hub_monthly.csv"

AUTHORIZED_YEARS = [2018, 2019, 2020, 2021, 2022, 2026]
IN_SAMPLE_YEARS = [2023, 2024, 2025]
WINTER = (1, 2, 12)
SUMMER = (6, 7, 8)
# Pre-intake baseline commit: the PREREG commit, which touched no data file.
BASE_REF = "HEAD"


def _git_show(ref: str, rel: str) -> str:
    """Return a file's contents at a git ref.

    Args:
        ref: Git revision.
        rel: Repo-relative path.

    Returns:
        The blob's text.
    """
    return subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _rows(text: str) -> list[dict[str, str]]:
    """Parse basis-CSV text into dict rows.

    Args:
        text: CSV contents.

    Returns:
        One dict per data row.
    """
    return list(csv.DictReader(io.StringIO(text)))


def _basis_by_month(rows: list[dict[str, str]], iso: str, year: int) -> np.ndarray:
    """Return a 12-vector of ``basis_usd_mmbtu`` for one ISO-year (NaN where absent).

    Args:
        rows: Parsed basis rows.
        iso: ISO identifier.
        year: Calendar year.

    Returns:
        Length-12 array indexed by month-1.
    """
    out = np.full(12, np.nan)
    for row in rows:
        if row["iso"] == iso and int(row["year"]) == year:
            out[int(row["month"]) - 1] = float(row["basis_usd_mmbtu"])
    return out


def _is_proxy(source: str) -> bool:
    """Return whether a row's ``source`` field is the rejected EIA N3050 proxy.

    Anchors on the source string's prefix: a bare ``N3050`` substring test
    mis-flags the ``NEISO,2025,8`` row, whose text *rejects* the proxy and cites
    the interpolated measured index instead (the neiso-85 correction).

    Args:
        source: The row's ``source`` field.

    Returns:
        True when the row is proxy-sourced.
    """
    return source.strip().upper().startswith("EIA N3050")


def main() -> None:
    """Evaluate and print all five gates."""
    before = _rows(_git_show(BASE_REF, BASIS_REL))
    after = _rows((REPO_ROOT / BASIS_REL).read_text())
    hh = {
        (int(r["year"]), int(r["month"])): float(r["price_usd_mmbtu"])
        for r in _rows(_git_show(BASE_REF, HH_REL))
    }
    verdicts: dict[str, str] = {}
    report: dict[str, object] = {}

    # ---------------------------------------------------------------- V1
    print("=" * 88)
    print("V1  SEASONALITY SIGN — winter(Jan,Feb,Dec) - summer(Jun,Jul,Aug) > 0")
    print("=" * 88)
    v1_rows, v1_pass = [], True
    for year in AUTHORIZED_YEARS:
        b_new = _basis_by_month(after, "NEISO", year)
        b_old = _basis_by_month(before, "NEISO", year)
        w_new = np.nanmean(b_new[list(np.array(WINTER) - 1)])
        s_new = np.nanmean(b_new[list(np.array(SUMMER) - 1)])
        w_old = np.nanmean(b_old[list(np.array(WINTER) - 1)])
        s_old = np.nanmean(b_old[list(np.array(SUMMER) - 1)])
        if np.isnan(s_new) or np.isnan(w_new):
            print(f"  {year}: NOT EVALUABLE (incomplete months) — see V1b")
            v1_rows.append({"year": year, "evaluable": False})
            continue
        delta_new, delta_old = w_new - s_new, w_old - s_old
        ok = delta_new > 0
        v1_pass &= ok
        print(
            f"  {year}: before {delta_old:>+8.2f}  ->  after {delta_new:>+8.2f}"
            f"   {'PASS' if ok else 'FAIL'}"
        )
        v1_rows.append(
            {"year": year, "evaluable": True, "before": round(float(delta_old), 4),
             "after": round(float(delta_new), 4), "pass": bool(ok)}
        )
    # V1b: 2026 substitute (declared in the PREREG, weaker, reported as such).
    b26 = _basis_by_month(after, "NEISO", 2026)
    v1b = float(np.nanmean(b26[[0, 1]])) - float(np.nanmean(b26[[3, 4]]))
    print(f"\n  V1b 2026 substitute  mean(Jan,Feb) - mean(Apr,May) = {v1b:>+8.2f}"
          f"   {'PASS' if v1b > 0 else 'FAIL'}  (weaker check — NOT V1)")
    verdicts["V1"] = "PASS" if v1_pass else "FAIL"
    verdicts["V1b_2026"] = "PASS" if v1b > 0 else "FAIL"
    report["V1"] = v1_rows
    report["V1b_2026"] = round(v1b, 4)

    # ---------------------------------------------------------------- V2
    print("\n" + "=" * 88)
    print("V2  IN-SAMPLE INVARIANCE — NEISO 2023-2025 + pre-existing AGT rows byte-identical")
    print("=" * 88)

    def _neiso_lines(text: str, years: list[int]) -> list[str]:
        keep = []
        for line in text.splitlines():
            parts = line.split(",", 3)
            if len(parts) >= 3 and parts[0] == "NEISO" and parts[1].isdigit():
                if int(parts[1]) in years:
                    keep.append(line)
        return keep

    in_before = _neiso_lines(_git_show(BASE_REF, BASIS_REL), IN_SAMPLE_YEARS)
    in_after = _neiso_lines((REPO_ROOT / BASIS_REL).read_text(), IN_SAMPLE_YEARS)
    v2_basis = in_before == in_after
    print(f"  NEISO {IN_SAMPLE_YEARS} basis rows: {len(in_before)} before, "
          f"{len(in_after)} after — {'IDENTICAL' if v2_basis else 'CHANGED'}")

    agt_before = _git_show(BASE_REF, AGT_REL).splitlines()
    agt_after = (REPO_ROOT / AGT_REL).read_text().splitlines()
    agt_after_set = set(agt_after)
    lost = [ln for ln in agt_before if ln not in agt_after_set]
    v2_agt = not lost
    print(f"  Algonquin daily: {len(agt_before)} pre-existing lines, "
          f"{len(agt_after)} now, {len(lost)} lost — "
          f"{'ALL PRESERVED' if v2_agt else 'ROWS LOST'}")
    if lost:
        for ln in lost[:5]:
            print(f"     LOST: {ln}")
    verdicts["V2"] = "PASS" if (v2_basis and v2_agt) else "FAIL"
    report["V2"] = {
        "basis_in_sample_identical": bool(v2_basis),
        "agt_rows_before": len(agt_before),
        "agt_rows_after": len(agt_after),
        "agt_rows_lost": len(lost),
    }

    # ---------------------------------------------------------------- V3
    print("\n" + "=" * 88)
    print("V3  LEVEL PLAUSIBILITY — corrected hub month >= measured EIA-923 in Jan/Feb/Dec")
    print("=" * 88)
    import market_sim.data.fuel.plant_prices as pp  # noqa: E402
    from market_sim.config.scenarios import ScenarioConfig  # noqa: E402

    v3_rows, v3_pass = [], True
    print(f"  {'ym':>8} {'hub(before)':>12} {'hub(after)':>11} {'EIA-923':>9}  verdict")
    for year in AUTHORIZED_YEARS:
        cfg = ScenarioConfig(iso="NEISO", start_year=year, end_year=year)
        e923 = pp.iso_monthly_gas_prices(cfg, year)
        if e923 is None:
            print(f"  {year}: NOT EVALUABLE (no EIA-923 receipts)")
            v3_rows.append({"year": year, "evaluable": False})
            continue
        b_new = _basis_by_month(after, "NEISO", year)
        b_old = _basis_by_month(before, "NEISO", year)
        for month in WINTER:
            hh_m = hh.get((year, month))
            if hh_m is None or np.isnan(b_new[month - 1]) or np.isnan(e923[month - 1]):
                continue
            hub_new = hh_m + b_new[month - 1]
            hub_old = hh_m + b_old[month - 1]
            ref = float(e923[month - 1])
            ok = hub_new >= ref
            v3_pass &= ok
            print(f"  {year}-{month:02d} {hub_old:>12.2f} {hub_new:>11.2f} {ref:>9.2f}"
                  f"  {'PASS' if ok else 'FAIL'}"
                  f"{'   (was FAIL)' if hub_old < ref else ''}")
            v3_rows.append({
                "year": year, "month": month, "hub_before": round(hub_old, 3),
                "hub_after": round(hub_new, 3), "eia923": round(ref, 3),
                "pass": bool(ok), "was_pass": bool(hub_old >= ref),
            })
    verdicts["V3"] = "PASS" if v3_pass else "FAIL"
    report["V3"] = v3_rows

    # ---------------------------------------------------------------- V5
    print("\n" + "=" * 88)
    print("V5  CROSS-ISO NON-INTERFERENCE — no non-NEISO row changes")
    print("=" * 88)

    def _non_neiso(text: str) -> list[str]:
        return [ln for ln in text.splitlines() if not ln.startswith("NEISO,")]

    nn_before = _non_neiso(_git_show(BASE_REF, BASIS_REL))
    nn_after = _non_neiso((REPO_ROOT / BASIS_REL).read_text())
    v5 = nn_before == nn_after
    isos = sorted({ln.split(",", 1)[0] for ln in nn_before if "," in ln} - {"iso"})
    print(f"  non-NEISO lines: {len(nn_before)} before, {len(nn_after)} after — "
          f"{'IDENTICAL' if v5 else 'CHANGED'}")
    print(f"  ISOs untouched: {', '.join(isos)}")
    verdicts["V5"] = "PASS" if v5 else "FAIL"
    report["V5"] = {"identical": bool(v5), "isos_untouched": isos}

    # -------------------------------------------------- residual proxy census
    print("\n" + "=" * 88)
    print("RESIDUAL — NEISO rows still sourced from the rejected EIA N3050 proxy")
    print("=" * 88)
    residual: dict[int, list[int]] = {}
    for row in after:
        if row["iso"] == "NEISO" and _is_proxy(row["source"]):
            residual.setdefault(int(row["year"]), []).append(int(row["month"]))
    for year in sorted(residual):
        tag = "NOT AUTHORIZED" if year not in AUTHORIZED_YEARS else "UNOBTAINABLE — DECLARED"
        print(f"  {year}: months {sorted(residual[year])}  [{tag}]")
    if not residual:
        print("  (none)")
    report["residual_proxy_rows"] = {str(k): sorted(v) for k, v in residual.items()}

    # ---------------------------------------------------------------- summary
    print("\n" + "=" * 88)
    for gate, verdict in verdicts.items():
        print(f"  {gate:<10} {verdict}")
    print("  V4         PASS (process gate — commits cite the data change only;")
    print("             source chosen by boundary correctness, fixed pre-intake)")
    print("=" * 88)
    report["verdicts"] = verdicts
    out = REPO_ROOT / "results" / "calibration" / "_neiso86_intake_gates.json"
    out.write_text(json.dumps(report, indent=1))
    print(f"\nwrote {out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
