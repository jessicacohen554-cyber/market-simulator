"""caiso-171 — the CAISO frontier / `complete`-declaration assessment instrument.

NO LP, NO SOLVE, NO NETWORK, NO INTAKE. Every number this probe prints is read
from **committed artifacts** — the CAISO keeper bundle's own sidecars and
attestation, the other ISOs' keeper attestations, `data/raw` inventories and the
committed mechanism matrix. It exists so the assessment
`results/calibration/ASSESSMENT-caiso171-frontier-2026-08-04.md` is re-checkable
in seconds on any checkout, and so a later session can re-run it to see whether
any of the three standing walls has moved.

It answers the four assessment questions with numbers rather than assertions:

* **F1 keeper state** — determination inputs: ledgered caveat count, FAIL count,
  and the non-protective ledger budget, off `calibration_attestation.json`.
* **F2 DOF ledger** — `n_entries` / `n_residual` for CAISO **and** for the three
  ISOs that already hold a rule-22 `complete` marker, split into the five-entry
  cross-ISO residual CORE that every ISO carries and the ISO-SPECIFIC residual
  remainder. The ISO-specific count is the comparable number; the core is not a
  CAISO property and must not be quoted as one.
* **F3 the N-S congestion majority (KNOWN-OPEN #1)** — measured `NP15-ZP26` from
  CAISO's own published DAM components (`LMP = MCE + MCC + MCL`, so the hub basis
  is exactly `dMCC + dMCL`) against the keeper's own zonal duals. Annual means
  only: a mean is **clock-invariant**, which sidesteps the Feb-29 / local-vs-UTC
  alignment defect `FINDING-caiso168` §clock flagged for any probe pairing a
  measured series to model hours.
* **F4 the intra-SP15 corridor (Arm B wall)** — the model-side separation on the
  CURRENT keeper. `FINDING-caiso165` recorded `LA_BASIN - SP15_rest` separating in
  **0.00 %** of belly hours; that was measured on the **caiso-164** keeper and is
  STALE for caiso-166, which arms the measured loss zones. This re-measures it and
  characterises what the separation now is (a proportional loss wedge, or real
  congestion) via the dispersion of the ratio `(p_a - p_b) / p_b`.

Usage::

    PYTHONPATH=.:src python scripts/probes/caiso171_frontier_assessment.py
    PYTHONPATH=.:src python scripts/probes/caiso171_frontier_assessment.py --json out.json

Exit status is informational (0 unless an input is missing); this is a reporting
instrument, not a gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
YEARS = (2023, 2024, 2025)

#: Keeper bundle directories, resolved from the dashboard registry at the time of
#: writing (caiso-171, 2026-08-04). CAISO is the subject; the other four are the
#: DOF comparison basis.
BUNDLES = {
    "CAISO": "caiso166_measured_loss_zones",
    "PJM": "pjm152_collapse_A",
    "NYISO": "nyiso120_c119_scopegate",
    "NEISO": "neiso_c156_meter_screen_B",
    "MISO": "miso126_steampart_B",
}

#: ISOs holding a rule-22 `complete` (VALIDATION-tier) marker as of 2026-08-04.
COMPLETE_MARKER_ISOS = ("NEISO", "NYISO", "PJM")

#: The five residual DOF entries EVERY ISO's ledger carries. These are properties
#: of the shared offer/wind machinery, not of any one ISO's calibration, so the
#: comparable statistic is the ISO-SPECIFIC remainder, never the raw n_residual.
CORE_RESIDUAL = {
    "offer_curve_by_group",
    "offer_curve_committed_below_floor",
    "offer_curve_smoothing",
    "COAL_SIGMOID_DEFAULTS",
    "wefor_multiplier",
}


def _strip_key(name: str) -> str:
    """Return a DOF entry name with its ``[ISO]`` / ``['key']`` subscript removed."""
    return re.sub(r"\[.*?\]|\{.*?\}", "", name).strip()


def _attestation(bundle: str) -> dict:
    """Load a bundle's committed calibration attestation."""
    return json.loads((CAL / bundle / "calibration_attestation.json").read_text())


def f1_keeper_state() -> dict:
    """F1 — the CAISO keeper's ledger state, off its committed attestation."""
    att = _attestation(BUNDLES["CAISO"])
    exc = att.get("exceptions", {})
    rows = exc.get("entries", exc) if isinstance(exc, dict) else exc
    out = {"ledgered": [], "raw_exceptions_type": type(exc).__name__}
    if isinstance(rows, list):
        for e in rows:
            if isinstance(e, dict):
                out["ledgered"].append(
                    {k: e.get(k) for k in ("criterion", "year", "disposition", "kind") if k in e}
                )
    out["governance_keys"] = sorted(att.get("governance", {}).keys())
    return out


def f2_dof() -> dict:
    """F2 — cross-ISO DOF ledger comparison, core vs ISO-specific residual."""
    rows = {}
    for iso, bundle in BUNDLES.items():
        fp = _attestation(bundle)["free_parameters"]
        residual = [
            e["name"] for e in fp.get("entries", []) if e.get("identification") == "residual"
        ]
        specific = [n for n in residual if _strip_key(n) not in CORE_RESIDUAL]
        rows[iso] = {
            "n_entries": fp.get("n_entries"),
            "n_residual": fp.get("n_residual"),
            "n_core_residual": len(residual) - len(specific),
            "n_iso_specific_residual": len(specific),
            "iso_specific": specific,
            "holds_complete_marker": iso in COMPLETE_MARKER_ISOS,
        }
    return rows


def f3_ns_basis() -> dict:
    """F3 — measured vs model ``NP15-ZP26``, and the congestion share of the miss.

    Annual means only (clock-invariant). The measured side decomposes exactly
    because CAISO publishes ``MCE``/``MCC``/``MCL`` and ``MCE`` is one system
    reference identical at every node.
    """
    out = {}
    for year in YEARS:
        dam = pd.read_csv(REPO / "data/raw/lmp-data/CAISO" / f"CAISO_dam_hourly_{year}.csv")
        piv = dam.pivot_table(
            index="interval_start_gmt", columns="node", values=["LMP", "MCC", "MCL"]
        )
        north, south = "TH_NP15_GEN-APND", "TH_ZP26_GEN-APND"
        d_lmp = float((piv["LMP"][north] - piv["LMP"][south]).mean())
        d_mcc = float((piv["MCC"][north] - piv["MCC"][south]).mean())
        d_mcl = float((piv["MCL"][north] - piv["MCL"][south]).mean())

        sysf = CAL / BUNDLES["CAISO"] / "hourly" / f"system_{year}.parquet"
        zon = pd.read_parquet(sysf).pivot_table(index="hour", columns="zone", values="price")
        diff = zon["NP15"] - zon["ZP26"]

        out[year] = {
            "measured_basis": d_lmp,
            "measured_dMCC": d_mcc,
            "measured_dMCL": d_mcl,
            "measured_congestion_share": abs(d_mcc) / (abs(d_mcc) + abs(d_mcl)),
            "model_basis": float(diff.mean()),
            "model_separated_pct": float((diff.abs() > 1e-6).mean() * 100),
            "model_share_of_measured": float(diff.mean()) / d_lmp if d_lmp else float("nan"),
        }
    return out


def f4_intra_sp15() -> dict:
    """F4 — the intra-SP15 corridors on the CURRENT keeper (Arm B premise re-check).

    A separation whose ``(p_a - p_b) / p_b`` ratio has near-zero dispersion is a
    proportional LOSS wedge, not congestion: the corridor is still not binding.
    """
    out = {}
    for year in YEARS:
        sysf = CAL / BUNDLES["CAISO"] / "hourly" / f"system_{year}.parquet"
        zon = pd.read_parquet(sysf).pivot_table(index="hour", columns="zone", values="price")
        hod = zon.index % 24
        belly = (hod >= 9) & (hod <= 16)  # Pacific 09-16, the caiso-165 window
        per_year = {}
        for a, b in (("LA_BASIN", "SP15_rest"), ("SDGE", "SP15_rest")):
            diff = (zon[a] - zon[b])[belly]
            ratio = diff / zon[b][belly].replace(0, pd.NA).astype(float)
            per_year[f"{a}-{b}"] = {
                "belly_separated_pct": float((diff.abs() > 1e-6).mean() * 100),
                "belly_mean": float(diff.mean()),
                "belly_sd": float(diff.std()),
                "ratio_mean": float(ratio.mean()),
                "ratio_sd": float(ratio.std()),
            }
        out[year] = per_year
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, help="also write the full record to this path")
    args = ap.parse_args(argv)

    record: dict = {"probe": "caiso171_frontier_assessment", "keeper_bundle": BUNDLES["CAISO"]}

    print("=" * 78)
    print("F1  CAISO keeper ledger state (committed attestation)")
    print("=" * 78)
    record["f1_keeper_state"] = f1_keeper_state()
    for row in record["f1_keeper_state"]["ledgered"]:
        print(f"  ledgered: {row}")
    if not record["f1_keeper_state"]["ledgered"]:
        print("  (exception rows not in list form — see calibration_verdict.py for the scored view)")

    print()
    print("=" * 78)
    print("F2  DOF ledger — CAISO vs the ISOs that already hold a `complete` marker")
    print("=" * 78)
    record["f2_dof"] = f2_dof()
    print(f"{'ISO':7}{'entries':>8}{'resid':>7}{'core':>6}{'ISO-SPEC':>9}  marker  iso-specific entries")
    for iso, r in record["f2_dof"].items():
        mark = "yes" if r["holds_complete_marker"] else "NO "
        names = ", ".join(r["iso_specific"]) or "-"
        print(
            f"{iso:7}{r['n_entries']:>8}{r['n_residual']:>7}{r['n_core_residual']:>6}"
            f"{r['n_iso_specific_residual']:>9}  {mark}     {names}"
        )
    print("  NOTE: the 5-entry CORE is shared machinery, not a CAISO property.")
    print("        The comparable statistic is the ISO-SPECIFIC column.")

    print()
    print("=" * 78)
    print("F3  KNOWN-OPEN #1 — the N-S congestion majority, on the CURRENT keeper")
    print("=" * 78)
    record["f3_ns_basis"] = f3_ns_basis()
    print(
        f"{'yr':6}{'meas basis':>11}{'dMCC':>9}{'dMCL':>9}{'cong%':>8}"
        f"{'model':>9}{'sep%':>8}{'model/meas':>12}"
    )
    for year, r in record["f3_ns_basis"].items():
        print(
            f"{year:<6}{r['measured_basis']:>+11.3f}{r['measured_dMCC']:>+9.3f}"
            f"{r['measured_dMCL']:>+9.3f}{r['measured_congestion_share']:>7.1%}"
            f"{r['model_basis']:>+9.3f}{r['model_separated_pct']:>7.2f}%"
            f"{r['model_share_of_measured']:>11.1%}"
        )

    print()
    print("=" * 78)
    print("F4  Arm B premise re-check — intra-SP15 corridors, CURRENT keeper")
    print("=" * 78)
    record["f4_intra_sp15"] = f4_intra_sp15()
    for year, corridors in record["f4_intra_sp15"].items():
        for name, r in corridors.items():
            kind = (
                "proportional LOSS wedge (ratio sd < 0.01)"
                if r["ratio_sd"] < 0.01 and r["belly_separated_pct"] > 50
                else "not a pure loss wedge"
                if r["belly_separated_pct"] > 50
                else "essentially unseparated"
            )
            print(
                f"  {year} {name:24} sep {r['belly_separated_pct']:6.2f}%  "
                f"mean {r['belly_mean']:+7.3f}  ratio sd {r['ratio_sd']:8.5f}  -> {kind}"
            )

    if args.json:
        args.json.write_text(json.dumps(record, indent=1))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
