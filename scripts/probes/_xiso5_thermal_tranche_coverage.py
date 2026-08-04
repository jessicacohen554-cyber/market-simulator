"""XISO-5 Phase 0 — cross-ISO `thermal_tranches_<ISO>.csv` coverage census (NO LP).

Adjudicates the three populations that hide under the single label
"thermal-tranche coverage gap", from **committed bytes only**: the five
committed artifacts, the frozen deriver source, the six designated keepers'
``run_config.json``, and their committed ``legitimacy_diagnostics.json``.
Nothing is solved, scored, registered or re-derived (rule 22 freeze ACTIVE;
rule 23 — no source-data change is cited, so no regeneration is licensed).

Four questions, one per section of the finding:

* **Q1 (design vs gap)** — is the all-ISO CHP ``online_frac`` zero a DESIGN
  choice? Decided by ``derive_thermal_tranches._ONLINE_FRAC_GROUPS``, which the
  emit expression gates on, and cross-checked against the CHP rows that reach
  the same ``status="ok"`` emit path and still publish nothing.
* **Q2 (PJM ST_GAS 0/10 vs MISO ST_GAS 16/16)** — the emit condition is a pure
  function of ``plant_group`` plus a denominator that any row with
  ``online_hours > 0`` necessarily clears, so a HEAD re-derivation CANNOT leave
  an ``ok`` row of an emitting group blank. Every such blank row is therefore a
  row the committed artifact does not reproduce at HEAD.
* **Q3 (rule 23 gate)** — reported, not computed: this script prints the
  admissibility question and the precedent, and the finding decides it.
* **Q4 (blast radius)** — which columns each ISO's CURRENT keeper actually
  consumes, from that keeper's own ``run_config.json`` gates, plus the forced
  energy the artifact-fed mechanisms carry in its committed D-2 rows.

Usage:
    python scripts/probes/_xiso5_thermal_tranche_coverage.py
    python scripts/probes/_xiso5_thermal_tranche_coverage.py --json OUT.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TRANCHES = REPO / "data" / "raw" / "_processed-legacy"
DERIVER = REPO / "scripts" / "data" / "derive_thermal_tranches.py"
KEEPER_DIR = REPO / "frontend" / "data" / "backcast" / "keepers"
REGISTRY = REPO / "frontend" / "data" / "backcast" / "registry"

ISOS: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

# Groups the deriver may emit a row for at all.
THERMAL_GROUPS: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "COAL",
)
CHP_GROUPS: frozenset[str] = frozenset({"CC_CHP", "CT_CHP", "ST_CHP"})

# Artifact column -> (runtime consumer, the ScenarioConfig gate that arms it).
# "" gate = consumed unconditionally wherever use_campd_bins is on.
COLUMN_CONSUMERS: dict[str, list[tuple[str, str]]] = {
    "committed_pct": [
        ("fleet/campd_bins.py::thermal_tranche_overrides -> bins_to_fleet", ""),
        ("model/reserves/spec.py::_min_stable_headroom", ""),
    ],
    "mustrun_pct": [
        ("fleet/campd_bins.py::thermal_tranche_overrides -> bins_to_fleet", ""),
    ],
    "mustrun_online_pct": [
        (
            "fleet/campd_bins.py::thermal_tranche_overrides (online-Pmin select)",
            "coal_mustrun_online_pmin",
        ),
    ],
    "online_frac:COAL": [
        ("fleet/assembly.py::coal_sync_online_frac", "coal_sync_srmc_tranche"),
    ],
    "online_frac:CC_REGULAR": [
        ("fleet/assembly.py::cc_mustrun_online_frac", "cc_mustrun_per_plant"),
    ],
    "online_frac:ST_GAS": [
        ("fleet/assembly.py::cc_mustrun_online_frac", "st_gas_mustrun_per_plant"),
    ],
    "p25_cf": [
        ("fleet/arrays.py::thermal_tranche_p25_level", "st_gas_mustrun_p25_level"),
    ],
    "peaking_pct": [
        ("fleet/campd_bins.py::thermal_tranche_peaking", "cc_peaking_per_plant"),
    ],
    "chp_pmin_cf": [("data/chp.py::chp_pmin_cf -> chp_grid_pmin_mw", "chp_steam_following")],
    "steam_level_cf": [
        (
            "fleet/assembly.py:611 via thermal_tranche_chp_steam_level",
            "chp_steam_floor_p25",
        ),
    ],
}

# D-2 mechanism ids whose parameters come out of thermal_tranches_<ISO>.csv.
ARTIFACT_FED_MECHS: frozenset[str] = frozenset(
    {"cc_mustrun_per_plant", "st_gas_mustrun_per_plant", "coal_mustrun", "chp_steam"}
)

GATE_FLAGS: tuple[str, ...] = (
    "use_campd_bins",
    "plant_level_fleet",
    "coal_mustrun_online_pmin",
    "coal_sync_srmc_tranche",
    "cc_mustrun_per_plant",
    "st_gas_mustrun_per_plant",
    "st_gas_mustrun_p25_level",
    "cc_peaking_per_plant",
    "chp_steam_following",
    "chp_steam_floor_p25",
)


def deriver_online_frac_groups() -> list[str]:
    """Read ``_ONLINE_FRAC_GROUPS`` out of the frozen deriver source.

    Parsed rather than imported so the census needs none of the deriver's heavy
    dependencies (CAMPD loaders, outage extracts) and cannot accidentally run it.
    """
    src = DERIVER.read_text()
    m = re.search(
        r"_ONLINE_FRAC_GROUPS:\s*frozenset\[str\]\s*=\s*frozenset\(\s*\{([^}]*)\}",
        src,
        re.S,
    )
    if not m:  # pragma: no cover - the constant is frozen; a miss is a real change
        raise RuntimeError("_ONLINE_FRAC_GROUPS not found in the deriver source")
    return sorted(re.findall(r'"([A-Z_]+)"', m.group(1)))


def keeper_ids() -> dict[str, str]:
    """Return ``{iso: designated keeper run id}`` from the sharded keeper store."""
    return {
        iso: json.loads((KEEPER_DIR / f"{iso}.json").read_text())["keeper"]
        for iso in ISOS
    }


def keeper_bundles(keepers: dict[str, str]) -> dict[str, Path]:
    """Resolve each keeper run id to its committed bundle directory."""
    out: dict[str, Path] = {}
    for iso, run_id in keepers.items():
        reg = json.loads((REGISTRY / f"{run_id}.json").read_text())
        out[iso] = REPO / reg["bundle"]
    return out


def coverage_census(emit_groups: list[str]) -> dict[str, dict]:
    """Per-ISO artifact census: schema generation + per-group online_frac coverage.

    ``blank_ok_emitting`` is the load-bearing number — ``status="ok"`` rows of a
    group the deriver DOES emit ``online_frac`` for, that carry no value. At HEAD
    the emit condition cannot produce one (see the module docstring), so it counts
    rows the committed artifact does not reproduce.
    """
    out: dict[str, dict] = {}
    for iso in ISOS:
        path = TRANCHES / f"thermal_tranches_{iso}.csv"
        if not path.exists():
            out[iso] = {"artifact": None, "note": "no artifact (ERCOT: custom-bin-assignments.csv)"}
            continue
        df = pd.read_csv(path)
        has_of = "online_frac" in df.columns
        groups: dict[str, dict] = {}
        blank_ok_emitting = 0
        for group in THERMAL_GROUPS:
            sub = df[df["plant_group"] == group]
            if sub.empty:
                continue
            ok = sub[sub["status"] == "ok"]
            frac = pd.to_numeric(sub.get("online_frac"), errors="coerce") if has_of else None
            nonzero = int((frac.fillna(0) > 0).sum()) if frac is not None else 0
            blank_ok = (
                int(pd.to_numeric(ok.get("online_frac"), errors="coerce").isna().sum())
                if has_of
                else len(ok)
            )
            if group in emit_groups:
                blank_ok_emitting += blank_ok
            groups[group] = {
                "rows": int(len(sub)),
                "ok_rows": int(len(ok)),
                "online_frac_nonzero": nonzero,
                "ok_rows_blank_online_frac": blank_ok,
                "deriver_emits_online_frac": group in emit_groups,
            }
        out[iso] = {
            "artifact": path.relative_to(REPO).as_posix(),
            "rows": int(len(df)),
            "schema_generation": {
                col: (col in df.columns)
                for col in (
                    "mustrun_online_pct",
                    "online_frac",
                    "chp_btm_pct",
                    "steam_level_cf",
                )
            },
            "max_online_hours": int(pd.to_numeric(df["online_hours"], errors="coerce").max()),
            "groups": groups,
            # Rows a HEAD re-derivation WOULD populate and the committed file does not.
            "ok_rows_blank_in_emitting_groups": blank_ok_emitting,
        }
    return out


def keeper_gates(bundles: dict[str, Path]) -> dict[str, dict[str, object]]:
    """Per-ISO armed state of every gate that reads a thermal-tranche column."""
    out: dict[str, dict[str, object]] = {}
    for iso, bundle in bundles.items():
        cfg = json.loads((bundle / "run_config.json").read_text())
        merged = {**cfg.get("calibration_flags", {}), **cfg.get("scenario_config", {})}
        out[iso] = {flag: merged.get(flag, "<absent>") for flag in GATE_FLAGS}
    return out


def forced_energy(bundles: dict[str, Path]) -> dict[str, list[dict]]:
    """D-2 rows for the mechanisms whose parameters come from the artifact."""
    out: dict[str, list[dict]] = {}
    for iso, bundle in bundles.items():
        diag = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
        out[iso] = [
            {
                "mechanism": r["mechanism"],
                "class": r["class"],
                "year": r["year"],
                "forced_twh": r["forced_twh"],
                "share_of_class": r["share_of_class"],
            }
            for r in diag["diagnostics"]["D2"]["rows"]
            if r["mechanism"] in ARTIFACT_FED_MECHS
        ]
    return out


def blast_radius(
    gates: dict[str, dict[str, object]], cov: dict[str, dict]
) -> dict[str, dict[str, list[str]]]:
    """Per ISO: which artifact columns its CURRENT keeper actually reads.

    Three buckets, because an armed gate over a column its ISO's artifact does
    not carry is NOT a live consumer — it is a **silent no-op**, and that latent
    class is the point of the census (a future lane arming the gate would get
    nothing and no error).
    """
    out: dict[str, dict[str, list[str]]] = {}
    for iso, flags in gates.items():
        present = cov[iso].get("schema_generation") or {}
        has_artifact = cov[iso].get("artifact") is not None
        live: list[str] = []
        silent: list[str] = []
        dormant: list[str] = []
        for column, consumers in COLUMN_CONSUMERS.items():
            armed = any(gate == "" or flags.get(gate) is True for _, gate in consumers)
            base = column.split(":", 1)[0]
            # A column is readable only if the ISO has an artifact and, for the
            # columns whose presence varies by schema generation, that column.
            readable = has_artifact and present.get(base, True)
            if not armed:
                dormant.append(column)
            elif readable:
                live.append(column)
            else:
                silent.append(column)
        out[iso] = {
            # ERCOT has no artifact BY DESIGN — its per-plant committed/must-run/
            # CHP values come from custom-bin-assignments.csv and the hardcoded
            # fleet maps (CC_REGULAR_COMMITTED_PCT_BY_PLANT, COAL_MUSTRUN_BY_PLANT,
            # CHP_PMIN_CF_BY_PLANT). Its armed gates are NOT silent no-ops; they
            # read a different, intentional source, so they are reported apart.
            "artifact_source": "hardcoded ERCOT maps" if not has_artifact else "artifact",
            "consumed_by_keeper": sorted(live),
            "armed_but_column_absent": sorted(silent) if has_artifact else [],
            "armed_off_artifact_by_design": sorted(silent) if not has_artifact else [],
            "dormant": sorted(dormant),
        }
    return out


def main() -> None:
    """Run the census and print the four sections of the finding."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default=None, help="write the full record to this path")
    args = ap.parse_args()

    emit_groups = deriver_online_frac_groups()
    keepers = keeper_ids()
    bundles = keeper_bundles(keepers)
    cov = coverage_census(emit_groups)
    gates = keeper_gates(bundles)
    radius = blast_radius(gates, cov)
    d2 = forced_energy(bundles)

    print("=" * 78)
    print("Q1 — is the CHP online_frac zero DESIGN or GAP?")
    print("=" * 78)
    print(f"derive_thermal_tranches._ONLINE_FRAC_GROUPS = {emit_groups}")
    print(f"CHP groups in that set: {sorted(CHP_GROUPS & set(emit_groups)) or 'NONE'}")
    for iso in ISOS:
        c = cov[iso]
        if c.get("artifact") is None:
            continue
        chp_ok = sum(
            g["ok_rows"] for name, g in c["groups"].items() if name in CHP_GROUPS
        )
        chp_nz = sum(
            g["online_frac_nonzero"] for name, g in c["groups"].items() if name in CHP_GROUPS
        )
        print(f"  {iso:6s} CHP status=ok rows reaching the emit path: {chp_ok:3d}  publishing online_frac: {chp_nz}")

    print()
    print("=" * 78)
    print("Q2 — rows the committed artifact does NOT reproduce at HEAD")
    print("=" * 78)
    hdr = f"{'ISO':6s} {'rows':>5s} {'max_on_h':>9s} {'mo_pct':>7s} {'of':>4s} {'btm':>4s} {'steam':>6s} {'blank ok/emitting':>18s}"
    print(hdr)
    print("-" * len(hdr))
    for iso in ISOS:
        c = cov[iso]
        if c.get("artifact") is None:
            print(f"{iso:6s} {'—':>5s}  (no artifact — {c['note']})")
            continue
        s = c["schema_generation"]
        print(
            f"{iso:6s} {c['rows']:5d} {c['max_online_hours']:9d} "
            f"{str(s['mustrun_online_pct'])[0]:>7s} {str(s['online_frac'])[0]:>4s} "
            f"{str(s['chp_btm_pct'])[0]:>4s} {str(s['steam_level_cf'])[0]:>6s} "
            f"{c['ok_rows_blank_in_emitting_groups']:18d}"
        )
    print()
    for iso in ISOS:
        c = cov[iso]
        if c.get("artifact") is None:
            continue
        gaps = [
            f"{name} {g['ok_rows_blank_online_frac']}/{g['ok_rows']}"
            for name, g in c["groups"].items()
            if g["deriver_emits_online_frac"] and g["ok_rows_blank_online_frac"]
        ]
        print(f"  {iso:6s} blank emitting-group ok rows: {', '.join(gaps) if gaps else 'NONE'}")

    print()
    print("=" * 78)
    print("Q3 — rule 23 [R-FROZEN-DERIVE] gate")
    print("=" * 78)
    print("  A re-derivation needs a CITED SOURCE-DATA change. Precedent: miso-95")
    print("  ruled the tranche staleness a CODE axis ('rule 23's data-change trigger")
    print("  never fired') and returned PROVENANCE-BLOCKED; xiso-2 measured the only")
    print("  later input move (MISO outage extract) as 2022-ONLY, with 2023-2025")
    print("  identical row-for-row. This census cites NO source-data change.")
    print("  => NO REGENERATION IS LICENSED. Diagnosis only.")

    print()
    print("=" * 78)
    print("Q4 — blast radius: columns each CURRENT keeper actually reads")
    print("=" * 78)
    hdr = f"{'flag':28s}" + "".join(f"{i:>8s}" for i in ISOS)
    print(hdr)
    print("-" * len(hdr))
    for flag in GATE_FLAGS:
        print(f"{flag:28s}" + "".join(f"{str(gates[i][flag]):>8s}" for i in ISOS))
    print()
    for iso in ISOS:
        r = radius[iso]
        print(f"  {iso:6s} LIVE:            {', '.join(r['consumed_by_keeper']) or '-'}")
        if r["armed_off_artifact_by_design"]:
            print(
                f"  {'':6s} BY DESIGN off hardcoded maps: "
                f"{', '.join(r['armed_off_artifact_by_design'])}"
            )
        print(f"  {'':6s} SILENT NO-OP:    {', '.join(r['armed_but_column_absent']) or '-'}")
        print(f"  {'':6s} dormant:         {', '.join(r['dormant'])}")
    print()
    print("  Artifact-fed forced energy in each keeper's committed D-2 rows (TWh/yr):")
    for iso in ISOS:
        by_mech: dict[str, list[float]] = {}
        for r in d2[iso]:
            by_mech.setdefault(r["mechanism"], []).append(r["forced_twh"])
        summary = ", ".join(
            f"{m} {min(v):.2f}-{max(v):.2f}" for m, v in sorted(by_mech.items())
        )
        print(f"    {iso:6s} {summary or 'none'}")

    record = {
        "session": "xiso-5",
        "date": "2026-08-04",
        "deriver_online_frac_groups": emit_groups,
        "keepers": keepers,
        "coverage": cov,
        "keeper_gates": gates,
        "blast_radius": radius,
        "artifact_fed_d2_rows": d2,
        "column_consumers": {k: v for k, v in COLUMN_CONSUMERS.items()},
    }
    if args.json:
        Path(args.json).write_text(json.dumps(record, indent=2, sort_keys=True))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
