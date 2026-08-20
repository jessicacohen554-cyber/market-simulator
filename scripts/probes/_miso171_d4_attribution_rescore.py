"""miso-171 carry-forward (a) — before/after re-score of the D-4 plant-grain class-attribution repair (READ-ONLY on committed bundles, no LP).

The instrument defect (miso-169 §5 ask 2 → miso-170 K-1 forensic → the
miso-171 charter item (a)): ``legitimacy_diagnostics.aggregate_floors_by_plant``
labels a plant with its most-common unit group, so a mixed-class site's floor
in one class is charged to another class's C8 budget and provenance legs (the
live case: plant 1104's CT_PEAKER netload floor convicted under ST_GAS's D-4
conduct row). The repair (FloorClassMatrix, this session) attributes each
at-floor plant-hour to the class of the unit CARRYING the floor — the same
maximum-composition rule the plant-hour mechanism already uses.

This harness measures the repair's effect on EVERY ISO's designated keeper:

  for each keeper bundle:
    committed  = the bundle's committed legitimacy_diagnostics.json (frozen)
    before     = D2/D4 regenerated at HEAD-without-the-repair
    after      = D2/D4 regenerated at HEAD-with-the-repair
    (before and after share the same rebuilt-floors/payload baseline, so
     their delta isolates the repair; the committed file may differ from
     both on the known rebuild-path artifacts — chp_steam floors and the
     P1-dependent RA bridge are absent from a fleet_only rebuild — which is
     disclosed, pre-existing, and NOT this repair's effect.)
    verdict(x) = scripts/calibration_verdict.py --json with the bundle's
                 legitimacy_diagnostics.json swapped to x IN PLACE
                 (restored afterwards; the bundle is byte-identical after
                 the run).

Emits results/calibration/_miso171_d4_attribution_rescore.json with, per ISO:
the determination + C8 per-(class, year) statuses under all three variants,
the D-2 class-share deltas, and the D-4 row deltas. Any before->after
determination change is a REPORTED FLIP (an owner escalation when it is not
MISO, per the charter).

Usage:
  python3 scripts/probes/_miso171_d4_attribution_rescore.py \
      --variants-dir <dir with <iso>_before.json / <iso>_after.json> \
      [--isos MISO PJM ...]
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "calibration" / "_miso171_d4_attribution_rescore.json"

KEEPERS_DIR = ROOT / "frontend" / "data" / "backcast" / "keepers"
REGISTRY_DIR = ROOT / "frontend" / "data" / "backcast" / "registry"
ISOS = ("ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO")


def keeper_bundle(iso: str) -> tuple[str, Path]:
    """(run_id, bundle dir) of the ISO's designated keeper."""
    run_id = json.loads((KEEPERS_DIR / f"{iso}.json").read_text())["keeper"]
    reg = json.loads((REGISTRY_DIR / f"{run_id}.json").read_text())
    return run_id, ROOT / reg["bundle"]


def run_verdict(bundle: Path) -> dict:
    """calibration_verdict --json on the bundle as it currently sits on disk."""
    # calibration_verdict uses its exit code as the gate signal (nonzero on a
    # NOT-YET), so success is "stdout parses", not "exit 0".
    proc = subprocess.run(
        [sys.executable, "scripts/calibration_verdict.py", str(bundle), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"calibration_verdict failed on {bundle}: rc={proc.returncode} "
            f"stderr tail: {proc.stderr[-500:]}"
        )


def verdict_summary(v: dict) -> dict:
    fs = v["criteria"]["forced_share"]
    return {
        "determination": v["determination"],
        "reasons": v["reasons"],
        "c8_status": fs["status"],
        "c8_records": {
            f"{r['year']}:{r['key']}": r["status"] for r in fs["records"]
        },
    }


def d2_shares(diag: dict) -> dict:
    return {
        f"{r['year']}:{r['class']}": (r["forced_share"], r["verdict"])
        for r in diag["D2"]["summary"]
    }


def d4_verdicts(diag: dict) -> dict:
    out = {}
    for r in diag["D4"]["rows"]:
        key = f"{r['year']}:{r['floor']}:{r.get('check', 'window')}:{r.get('plant', '')}"
        out[key] = r["verdict"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants-dir", type=Path, required=True)
    ap.add_argument("--isos", nargs="*", default=list(ISOS))
    args = ap.parse_args()

    record: dict = {"session": "miso-171", "isos": {}}
    flips: list[str] = []
    for iso in args.isos:
        run_id, bundle = keeper_bundle(iso)
        legit_path = bundle / "legitimacy_diagnostics.json"
        committed_text = legit_path.read_text()
        committed = json.loads(committed_text)
        variants: dict[str, dict] = {}
        irec: dict = {"run_id": run_id, "bundle": str(bundle.relative_to(ROOT))}
        try:
            for name in ("before", "after"):
                vpath = args.variants_dir / f"{iso.lower()}_{name}.json"
                if not vpath.exists():
                    irec[f"{name}_missing"] = str(vpath)
                    continue
                regen = json.loads(vpath.read_text())
                merged = copy.deepcopy(committed)
                merged["diagnostics"]["D2"] = regen["diagnostics"]["D2"]
                merged["diagnostics"]["D4"] = regen["diagnostics"]["D4"]
                variants[name] = merged
            irec["verdicts"] = {"committed": verdict_summary(run_verdict(bundle))}
            for name, merged in variants.items():
                legit_path.write_text(json.dumps(merged, indent=1) + "\n")
                irec["verdicts"][name] = verdict_summary(run_verdict(bundle))
        finally:
            legit_path.write_text(committed_text)

        if {"before", "after"} <= set(irec.get("verdicts", {})):
            vb, va = irec["verdicts"]["before"], irec["verdicts"]["after"]
            bdiag = variants["before"]["diagnostics"]
            adiag = variants["after"]["diagnostics"]
            sb, sa = d2_shares(bdiag), d2_shares(adiag)
            irec["d2_share_deltas"] = {
                k: {"before": sb.get(k), "after": sa.get(k)}
                for k in sorted(set(sb) | set(sa))
                if sb.get(k) != sa.get(k)
            }
            db, da = d4_verdicts(bdiag), d4_verdicts(adiag)
            irec["d4_row_deltas"] = {
                k: {"before": db.get(k), "after": da.get(k)}
                for k in sorted(set(db) | set(da))
                if db.get(k) != da.get(k)
            }
            irec["c8_record_flips"] = {
                k: {"before": vb["c8_records"].get(k), "after": va["c8_records"].get(k)}
                for k in sorted(set(vb["c8_records"]) | set(va["c8_records"]))
                if vb["c8_records"].get(k) != va["c8_records"].get(k)
            }
            if vb["determination"] != va["determination"]:
                flips.append(
                    f"{iso}: {vb['determination']} -> {va['determination']}"
                )
        record["isos"][iso] = irec

    record["determination_flips_before_to_after"] = flips
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for iso, irec in record["isos"].items():
        v = irec.get("verdicts", {})
        line = f"{iso:6s}"
        for name in ("committed", "before", "after"):
            if name in v:
                line += f"  {name}={v[name]['determination']}/C8:{v[name]['c8_status']}"
        print(line)
        for k, d in (irec.get("c8_record_flips") or {}).items():
            print(f"        C8 {k}: {d['before']} -> {d['after']}")
    print(
        "DETERMINATION FLIPS (before->after):",
        flips if flips else "none",
    )


if __name__ == "__main__":
    main()
