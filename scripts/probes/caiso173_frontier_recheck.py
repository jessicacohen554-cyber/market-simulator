"""caiso-173 — the CAISO frontier RE-CHECK instrument, on the post-caiso-172 ledger.

NO LP, NO SOLVE, NO NETWORK, NO INTAKE. Every number this probe prints is read
from **committed artifacts** — the CAISO keeper bundle's own sidecars and
attestation, the other ISOs' keeper attestations resolved LIVE from the dashboard
registry, `data/raw` inventories, `constants.py` and the committed mechanism
matrix. It exists so the assessment
`results/calibration/ASSESSMENT-caiso173-frontier-2026-08-04.md` is re-checkable
in seconds on any checkout.

It is the successor to `caiso171_frontier_assessment.py` and differs from it in
four ways that matter:

* **G0 (NEW) — the FFR-4D epoch gate.** `caiso-171` predates cache epoch
  **2026-08-04c** (`docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md`,
  merged as PR #3562). This probe measures, rather than asserts, whether the
  designated keeper was solved before or after the epoch: it checks the keeper's
  own recorded `git_sha` against the epoch commit, and checks whether the keeper's
  `run_config.json` carries the `storage_measured_base_fleet` field at all. A
  keeper whose config predates the field is PRE-EPOCH and its committed metrics
  were produced on the flat 8,000 MW battery scalar.
* **Bundles are resolved from the registry, never hardcoded.** caiso-171 pinned
  `BUNDLES` as literals; three of its four comparison ISOs have promoted new
  keepers since, so those literals now describe stale runs. F2's cross-ISO table
  is only honest if it reads whatever each ISO's `keepers/<ISO>.json` currently
  designates.
* **F5 (NEW) — the evidence census is executed**, not quoted: the §5.2 closure
  documents are resolved on disk and line-counted.
* **F6 (NEW) — MWD-TAC materiality**, measured off the committed TAC load series
  rather than carried as caiso-172's ~0.9 % estimate.

F1–F4 reproduce caiso-171's checks unchanged in construction, so the two records
are directly comparable.

Usage::

    PYTHONPATH=.:src python scripts/probes/caiso173_frontier_recheck.py
    PYTHONPATH=.:src python scripts/probes/caiso173_frontier_recheck.py --json out.json

Exit status is informational (0 unless an input is missing); this is a reporting
instrument, not a gate.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
REG = REPO / "frontend" / "data" / "backcast" / "registry"
KEEPERS = REPO / "frontend" / "data" / "backcast" / "keepers"
YEARS = (2023, 2024, 2025)

#: The ISOs whose DOF ledgers form the comparison basis. Bundles are NOT pinned
#: here — see `resolve_bundle`; caiso-171's pinned literals went stale within a
#: day when NYISO/NEISO/MISO promoted.
COMPARISON_ISOS = ("CAISO", "PJM", "NYISO", "NEISO", "MISO")

#: ISOs holding a rule-22 `complete` (VALIDATION-tier) marker. Read from the
#: marker file rather than hardcoded, but this is the expected set as of
#: 2026-08-05.
_EXPECTED_COMPLETE = ("NEISO", "NYISO", "PJM")

#: The five residual DOF entries EVERY ISO's ledger carries. Properties of the
#: shared offer/wind machinery, not of any one ISO's calibration, so the
#: comparable statistic is the ISO-SPECIFIC remainder, never the raw n_residual.
CORE_RESIDUAL = {
    "offer_curve_by_group",
    "offer_curve_committed_below_floor",
    "offer_curve_smoothing",
    "COAL_SIGMOID_DEFAULTS",
    "wefor_multiplier",
}

#: FFR-4D's epoch commit (the head of `claude/caiso-fleet-capacity-shortfall-rahkb5`),
#: and the `ScenarioConfig` field it introduced. A keeper `run_config.json` that
#: does not carry the field was solved before the field existed.
FFR4D_HEAD = "58c22e32"
EPOCH_FIELD = "storage_measured_base_fleet"
EPOCH_TAG = "2026-08-04c"

#: The measured CAISO battery fleet at year-end, FFR-4D §5 (EIA-860 2025 Early
#: Release), against the flat forecast scalar every pre-epoch CAISO backcast ran.
FFR4D_MEASURED_BATTERY_MW = {2023: 7492.4, 2024: 11131.3, 2025: 15448.4}
PRE_EPOCH_FLAT_SCALAR_MW = 8000.0

#: The §5.2 queue closure documents caiso-171 §1.1 verified 16/16, plus the two
#: caiso-172 added. Globs, because dates are in the filenames.
EVIDENCE_GLOBS = (
    "FINDING-caiso144-*.md",
    "FINDING-caiso167-*.md",
    "FINDING-caiso142*.md",
    "FINDING-caiso143*.md",
    "FINDING-caiso170-*.md",
    "FINDING-caiso169-*.md",
    "FINDING-caiso149-*.md",
    "FINDING-caiso136-*.md",
    "FINDING-caiso146-*.md",
    "FINDING-caiso147-*.md",
    "FINDING-caiso148-*.md",
    "FINDING-caiso153-*.md",
    "FINDING-caiso165*.md",
    "FINDING-caiso164*.md",
    "FINDING-caiso163*.md",
    "FINDING-caiso157*.md",
    "FINDING-caiso172-*.md",
    "PRECHECK-caiso172-*.md",
    "ASSESSMENT-caiso171-*.md",
)


def _strip_key(name: str) -> str:
    """Return a DOF entry name with its ``[ISO]`` / ``['key']`` subscript removed."""
    return re.sub(r"\[.*?\]|\{.*?\}", "", name).strip()


def resolve_bundle(iso: str) -> tuple[str, str]:
    """Return ``(run_id, bundle_dir)`` for an ISO's CURRENTLY designated keeper.

    Reads `keepers/<ISO>.json` then that run's registry sidecar, so the answer
    tracks promotions instead of going stale the way a pinned literal does.
    """
    run_id = json.loads((KEEPERS / f"{iso}.json").read_text())["keeper"]
    bundle = json.loads((REG / f"{run_id}.json").read_text())["bundle"]
    return run_id, bundle


def _attestation(bundle: str) -> dict:
    """Load a bundle's committed calibration attestation."""
    return json.loads((REPO / bundle / "calibration_attestation.json").read_text())


def _run_config(bundle: str) -> dict:
    """Load a bundle's committed run configuration."""
    return json.loads((REPO / bundle / "run_config.json").read_text())


def g0_epoch_gate(bundle: str) -> dict:
    """G0 — is the designated CAISO keeper PRE- or POST- cache epoch 2026-08-04c?

    Three independent signals, all off committed state:

    1. Is FFR-4D's head an ancestor of `origin/main` (i.e. has the epoch landed)?
    2. Was the keeper's own recorded `git_sha` solved before that head?
    3. Does the keeper's `run_config.json` carry `storage_measured_base_fleet`
       at all? A config without the field predates it — the strongest signal,
       because it needs no git history to interpret.
    """

    def _git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=REPO, capture_output=True, text=True, check=False
            ).stdout.strip()
        except OSError:  # pragma: no cover - git always present in this repo
            return ""

    def _is_ancestor(a: str, b: str) -> bool | None:
        r = subprocess.run(
            ["git", "merge-base", "--is-ancestor", a, b],
            cwd=REPO,
            capture_output=True,
            check=False,
        )
        return r.returncode == 0 if r.returncode in (0, 1) else None

    rc = _run_config(bundle)
    cfg = rc.get("scenario_config", {})
    keeper_sha = rc.get("git_sha") or cfg.get("git_sha") or ""

    epoch_merged = _is_ancestor(FFR4D_HEAD, "origin/main")
    keeper_predates = _is_ancestor(keeper_sha, FFR4D_HEAD) if keeper_sha else None

    out = {
        "epoch_tag": EPOCH_TAG,
        "ffr4d_head": FFR4D_HEAD,
        "ffr4d_merged_into_main": epoch_merged,
        "keeper_git_sha": keeper_sha,
        "keeper_sha_subject": _git("log", "-1", "--format=%s", keeper_sha) if keeper_sha else "",
        "keeper_sha_predates_epoch": keeper_predates,
        "epoch_field": EPOCH_FIELD,
        "epoch_field_in_keeper_run_config": EPOCH_FIELD in cfg,
        "epoch_field_in_current_scenarios_py": EPOCH_FIELD
        in (REPO / "src/market_sim/config/scenarios.py").read_text(),
    }
    # The verdict. The run_config signal is authoritative: a keeper solved on a
    # tree without the field cannot have honoured it.
    out["keeper_is_pre_epoch"] = bool(epoch_merged) and not out["epoch_field_in_keeper_run_config"]
    out["fleet_shortfall_mw"] = {
        y: round(mw - PRE_EPOCH_FLAT_SCALAR_MW, 1) for y, mw in FFR4D_MEASURED_BATTERY_MW.items()
    }
    out["fleet_shortfall_pct_of_measured"] = {
        y: round(100.0 * (mw - PRE_EPOCH_FLAT_SCALAR_MW) / mw, 1)
        for y, mw in FFR4D_MEASURED_BATTERY_MW.items()
    }
    return out


def f1_keeper_state(bundle: str) -> dict:
    """F1 — the CAISO keeper's ledger state, off its committed attestation."""
    att = _attestation(bundle)
    exc = att.get("exceptions", {})
    rows = exc.get("entries", exc) if isinstance(exc, dict) else exc
    out: dict = {"ledgered": [], "raw_exceptions_type": type(exc).__name__}
    if isinstance(rows, list):
        for e in rows:
            if isinstance(e, dict):
                out["ledgered"].append(
                    {k: e.get(k) for k in ("criterion", "year", "disposition", "kind") if k in e}
                )
    out["governance_keys"] = sorted(att.get("governance", {}).keys())
    return out


def f2_dof() -> dict:
    """F2 — cross-ISO DOF ledger comparison, core vs ISO-specific residual.

    THE headline caiso-171 §3 rested on ("CAISO carries the most ISO-specific
    residual DOF of any ISO measured", at 4). caiso-172 closed one, so this
    re-measures the whole table rather than decrementing CAISO's cell — the
    comparison ISOs have promoted too.
    """
    complete = _complete_marker_isos()
    rows = {}
    for iso in COMPARISON_ISOS:
        run_id, bundle = resolve_bundle(iso)
        fp = _attestation(bundle)["free_parameters"]
        residual = [
            e["name"] for e in fp.get("entries", []) if e.get("identification") == "residual"
        ]
        specific = [n for n in residual if _strip_key(n) not in CORE_RESIDUAL]
        rows[iso] = {
            "keeper": run_id,
            "bundle": bundle,
            "n_entries": fp.get("n_entries"),
            "n_residual": fp.get("n_residual"),
            "n_core_residual": len(residual) - len(specific),
            "n_iso_specific_residual": len(specific),
            "iso_specific": specific,
            "holds_complete_marker": iso in complete,
        }
    return rows


def _complete_marker_isos() -> tuple[str, ...]:
    """ISOs currently carrying a rule-22 VALIDATION-tier `complete` marker."""
    fp = REPO / "frontend" / "data" / "backcast" / "calibration-complete.json"
    if not fp.exists():
        return _EXPECTED_COMPLETE
    doc = json.loads(fp.read_text())
    block = doc.get("complete", {})
    if isinstance(block, dict):
        return tuple(sorted(block.keys()))
    if isinstance(block, list):
        return tuple(sorted(e.get("iso", "") for e in block if isinstance(e, dict)))
    return _EXPECTED_COMPLETE


def f3_ns_basis(bundle: str) -> dict:
    """F3 — measured vs model ``NP15-ZP26``, and the congestion share of the miss.

    Annual means only (clock-invariant), so the `FINDING-caiso168` Feb-29 /
    local-vs-UTC alignment defect cannot touch it. The measured side decomposes
    exactly because CAISO publishes ``MCE``/``MCC``/``MCL`` and ``MCE`` is one
    system reference identical at every node.
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

        sysf = REPO / bundle / "hourly" / f"system_{year}.parquet"
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


def f4_intra_sp15(bundle: str) -> dict:
    """F4 — the intra-SP15 corridors on the CURRENT keeper (Arm B premise re-check).

    A separation whose ``(p_a - p_b) / p_b`` ratio has near-zero dispersion is a
    proportional LOSS wedge, not congestion: the corridor is still not binding.
    """
    out = {}
    for year in YEARS:
        sysf = REPO / bundle / "hourly" / f"system_{year}.parquet"
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


def f5_evidence_census() -> dict:
    """F5 — the §5.2 closure documents, resolved on disk and line-counted."""
    rows = []
    for pat in EVIDENCE_GLOBS:
        hits = sorted(CAL.glob(pat))
        for h in hits:
            rows.append(
                {"glob": pat, "file": h.name, "lines": len(h.read_text().splitlines())}
            )
        if not hits:
            rows.append({"glob": pat, "file": None, "lines": 0})
    return {
        "n_globs": len(EVIDENCE_GLOBS),
        "n_resolved": sum(1 for r in rows if r["file"]),
        "n_missing": sum(1 for r in rows if not r["file"]),
        "rows": rows,
    }


def f6_mwd_tac() -> dict:
    """F6 — MWD-TAC materiality, MEASURED off the committed TAC load series.

    caiso-172 §1.1 opened this as ``~208 MW, ~0.9 % of ISO load``. Here the
    committed series is read directly: which TAC areas it carries, and how far
    the four modelled utility TACs fall short of the ``CA ISO-TAC`` total. That
    residual is the unmodelled remainder and MWD is its dominant term.
    """
    out = {}
    for year in YEARS:
        fp = REPO / "data/raw/zone-specific-demand/CAISO" / f"CAISO_tac_load_hourly_{year}.csv"
        d = pd.read_csv(fp)
        areas = sorted(d["tac_area"].unique())
        piv = d.pivot_table(index="interval_start_gmt", columns="tac_area", values="mw")
        modelled = [a for a in areas if a != "CA ISO-TAC"]
        total = piv["CA ISO-TAC"]
        resid = total - piv[modelled].sum(axis=1)
        out[year] = {
            "areas_in_committed_series": areas,
            "has_MWD_TAC": any("MWD" in a.upper() for a in areas),
            "iso_total_mean_mw": float(total.mean()),
            "modelled_sum_mean_mw": float(piv[modelled].sum(axis=1).mean()),
            "unmodelled_residual_mean_mw": float(resid.mean()),
            "unmodelled_residual_pct_of_iso": float(100.0 * resid.mean() / total.mean()),
        }
    return out


def f7_weights_table() -> dict:
    """F7 — the live `CAISO_TAC_ZONE_WEIGHTS`, to confirm what F6's gap is against."""
    from market_sim.config.constants import CAISO_TAC_ZONE_WEIGHTS

    return {
        "keys": sorted(CAISO_TAC_ZONE_WEIGHTS),
        "has_MWD_TAC": any("MWD" in k.upper() for k in CAISO_TAC_ZONE_WEIGHTS),
        "table": {k: dict(v) for k, v in CAISO_TAC_ZONE_WEIGHTS.items()},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, help="also write the full record to this path")
    args = ap.parse_args(argv)

    keeper_id, keeper_bundle = resolve_bundle("CAISO")
    record: dict = {
        "probe": "caiso173_frontier_recheck",
        "keeper_run_id": keeper_id,
        "keeper_bundle": keeper_bundle,
    }

    print("=" * 78)
    print("G0  THE FFR-4D EPOCH GATE — is the designated keeper pre- or post-epoch?")
    print("=" * 78)
    record["g0_epoch_gate"] = g0 = g0_epoch_gate(keeper_bundle)
    print(f"  keeper                     {keeper_id}")
    print(f"  epoch                      {g0['epoch_tag']}  (FFR-4D head {g0['ffr4d_head']})")
    print(f"  FFR-4D merged into main?   {g0['ffr4d_merged_into_main']}")
    print(f"  keeper git_sha             {g0['keeper_git_sha']}  ({g0['keeper_sha_subject']})")
    print(f"  keeper sha predates epoch? {g0['keeper_sha_predates_epoch']}")
    print(f"  `{EPOCH_FIELD}` in keeper run_config?  {g0['epoch_field_in_keeper_run_config']}")
    print(f"  `{EPOCH_FIELD}` in current scenarios.py? {g0['epoch_field_in_current_scenarios_py']}")
    print(f"  >>> KEEPER IS PRE-EPOCH: {g0['keeper_is_pre_epoch']}")
    print("  battery fleet the keeper did NOT see (measured minus the flat 8,000 MW scalar):")
    for y in YEARS:
        print(
            f"    {y}  measured {FFR4D_MEASURED_BATTERY_MW[y]:>9,.1f} MW   "
            f"shortfall {g0['fleet_shortfall_mw'][y]:>+9,.1f} MW  "
            f"({g0['fleet_shortfall_pct_of_measured'][y]:+.1f}% of measured)"
        )

    print()
    print("=" * 78)
    print("F1  CAISO keeper ledger state (committed attestation)")
    print("=" * 78)
    record["f1_keeper_state"] = f1_keeper_state(keeper_bundle)
    for row in record["f1_keeper_state"]["ledgered"]:
        print(f"  ledgered: {row}")
    if not record["f1_keeper_state"]["ledgered"]:
        print("  (exception rows not in list form — see calibration_verdict.py for the scored view)")

    print()
    print("=" * 78)
    print("F2  DOF ledger — CAISO vs the ISOs that already hold a `complete` marker")
    print("     (bundles resolved LIVE from the registry, not pinned)")
    print("=" * 78)
    record["f2_dof"] = f2_dof()
    print(
        f"{'ISO':7}{'entries':>8}{'resid':>7}{'core':>6}{'ISO-SPEC':>9}  marker  iso-specific entries"
    )
    for iso, r in record["f2_dof"].items():
        mark = "yes" if r["holds_complete_marker"] else "NO "
        names = ", ".join(r["iso_specific"]) or "-"
        print(
            f"{iso:7}{r['n_entries']:>8}{r['n_residual']:>7}{r['n_core_residual']:>6}"
            f"{r['n_iso_specific_residual']:>9}  {mark}     {names}"
        )
    print("  NOTE: the 5-entry CORE is shared machinery, not a CAISO property.")
    print("        The comparable statistic is the ISO-SPECIFIC column.")
    _spec = {i: r["n_iso_specific_residual"] for i, r in record["f2_dof"].items()}
    _max = max(_spec.values())
    _top = sorted(i for i, v in _spec.items() if v == _max)
    record["f2_verdict"] = {
        "caiso_iso_specific": _spec["CAISO"],
        "max_iso_specific": _max,
        "isos_at_max": _top,
        "caiso_is_sole_highest": _top == ["CAISO"],
        "caiso_is_at_or_above_all": _spec["CAISO"] >= _max,
    }
    print(
        f"  >>> CAISO ISO-specific = {_spec['CAISO']}; max across measured ISOs = {_max} "
        f"({', '.join(_top)}). CAISO sole highest? {record['f2_verdict']['caiso_is_sole_highest']}"
    )

    print()
    print("=" * 78)
    print("F3  KNOWN-OPEN #1 — the N-S congestion majority, on the CURRENT keeper")
    print("=" * 78)
    record["f3_ns_basis"] = f3_ns_basis(keeper_bundle)
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
    record["f4_intra_sp15"] = f4_intra_sp15(keeper_bundle)
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

    print()
    print("=" * 78)
    print("F5  Evidence census — the §5.2 closure documents, resolved on disk")
    print("=" * 78)
    record["f5_evidence"] = f5_evidence_census()
    for r in record["f5_evidence"]["rows"]:
        state = f"{r['lines']:>4} ln" if r["file"] else "MISSING"
        print(f"  {state}  {r['file'] or r['glob']}")
    print(
        f"  >>> {record['f5_evidence']['n_resolved']} resolved, "
        f"{record['f5_evidence']['n_missing']} missing"
    )

    print()
    print("=" * 78)
    print("F6/F7  MWD-TAC — the demand-input gap caiso-172 opened, MEASURED")
    print("=" * 78)
    record["f6_mwd_tac"] = f6_mwd_tac()
    record["f7_weights"] = f7_weights_table()
    for year, r in record["f6_mwd_tac"].items():
        print(
            f"  {year}  areas={len(r['areas_in_committed_series'])}  MWD present? "
            f"{r['has_MWD_TAC']}   ISO total {r['iso_total_mean_mw']:>9,.1f} MW   "
            f"modelled {r['modelled_sum_mean_mw']:>9,.1f} MW   "
            f"UNMODELLED {r['unmodelled_residual_mean_mw']:>+8,.1f} MW "
            f"({r['unmodelled_residual_pct_of_iso']:+.2f}%)"
        )
    print(f"  committed series areas: {record['f6_mwd_tac'][YEARS[-1]]['areas_in_committed_series']}")
    print(f"  CAISO_TAC_ZONE_WEIGHTS keys: {record['f7_weights']['keys']}")
    print(f"  weights table carries MWD-TAC? {record['f7_weights']['has_MWD_TAC']}")

    if args.json:
        args.json.write_text(json.dumps(record, indent=1, default=str))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
