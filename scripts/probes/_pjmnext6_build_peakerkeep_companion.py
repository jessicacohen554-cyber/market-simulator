"""PJM-NEXT-6 card 1 — build the '-rederive-peakerkeep-unitfuel-' companion. ZERO LP.

Owner ruling 2026-09-27 ("Split"): the F2 full HEAD re-derive, with the listed
gas-steam peakers' (ST_GAS_PEAKER_PLANTS) measured full-dark dead-period windows
KEPT. The construction is the F2 companion's own, step for step, with ONE switch:

1. derive_campd_unit_outages.py --iso PJM --years 2019..2025
   --membership-vintage-union [--keep-listed-peaker-dead-periods]
2. rows starting outside 2019-2025 carried verbatim from
   campd-unit-outages-memberrepair-PJM.csv, placed FIRST (2018 raw CAMPD is not
   in the repo);
3. build_outage_unit_fuel_routing.build_companion.

Step 0 (the control) re-runs the construction WITHOUT the switch and asserts it
reproduces the committed F2 companion byte-for-byte (sha256 a77386d8...), so the
only difference between the two files is the switch.

Usage: python3 scripts/probes/_pjmnext6_build_peakerkeep_companion.py --scratch DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scripts.data.build_outage_unit_fuel_routing import build_companion  # noqa: E402

RAW = REPO / "data" / "raw"
F2 = RAW / "campd-unit-outages-rederive-unitfuel-PJM.csv"
F2_SHA = "a77386d8facb25714edaa825b47e8f30f438b843b736d8633696f894e707ee6a"
OUT = RAW / "campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def _derive(scratch: Path, keep: bool) -> pd.DataFrame:
    """Run the HEAD deriver into ``scratch`` and return its extract."""
    out = scratch / ("split.csv" if keep else "f2_repro.csv")
    cmd = [
        sys.executable,
        str(REPO / "scripts/data/derive_campd_unit_outages.py"),
        "--iso",
        "PJM",
        "--years",
        *map(str, YEARS),
        "--membership-vintage-union",
        "--out",
        str(out),
    ]
    if keep:
        cmd.append("--keep-listed-peaker-dead-periods")
    if not out.exists():
        subprocess.run(cmd, check=True, cwd=REPO)
    return pd.read_csv(out)


def _assemble(derived: pd.DataFrame) -> bytes:
    """Carry out-of-span incumbent rows first, then fuel-route; return CSV bytes."""
    inc = pd.read_csv(RAW / "campd-unit-outages-memberrepair-PJM.csv")
    carry = inc[~pd.to_datetime(inc.outage_start).dt.year.between(YEARS[0], YEARS[-1])]
    base = pd.concat([carry, derived], ignore_index=True)
    comp, _ = build_companion(base)
    return comp.to_csv(index=False).encode()


def main() -> None:
    """Build the companion after proving the control reproduces F2 byte-for-byte."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scratch", required=True, type=Path)
    args = ap.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    ctrl = _assemble(_derive(args.scratch, keep=False))
    assert hashlib.sha256(ctrl).hexdigest() == F2_SHA, "control does not reproduce F2"
    body = _assemble(_derive(args.scratch, keep=True))
    OUT.write_bytes(body)
    sha = hashlib.sha256(body).hexdigest()
    frame = pd.read_csv(OUT)
    by_year = pd.to_datetime(frame.outage_start).dt.year.value_counts().sort_index()
    meta = json.loads((F2.with_suffix(".meta.json")).read_text())
    meta.update(
        artifact=OUT.name,
        artifact_rows=int(len(frame)),
        artifact_sha256=sha,
        windows_by_start_year={str(k): int(v) for k, v in by_year.items()},
    )
    meta["derive_invocation"]["keep_listed_peaker_dead_periods"] = True
    meta.pop("pjm_next5_construction", None)
    meta["pjm_next6_construction"] = {
        "session": "PJM-NEXT-6 card 1, 2026-09-27 (owner ruling 'Split')",
        "deriver_invocation": "derive_campd_unit_outages.py --iso PJM --years 2019..2025 "
        "--membership-vintage-union --keep-listed-peaker-dead-periods",
        "control": f"same construction without the switch reproduces {F2.name} sha256 {F2_SHA}",
        "span_rows": "2019-2025 from the HEAD re-derive; out-of-span rows carried verbatim "
        "from campd-unit-outages-memberrepair-PJM.csv, placed first",
        "post_step": "scripts/data/build_outage_unit_fuel_routing.build_companion",
        "selected_by": "ScenarioConfig.unit_outage_rederive_peaker_windows "
        "(with unit_outage_full_rederive + membership_repair + unit_fuel_routing)",
        "record": "docs/records/pjm/PRECOMMIT-pjm-next-6-card1-f2-split-2026-09-27.md",
    }
    OUT.with_suffix(".meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n"
    )
    print(f"wrote {OUT.name} rows={len(frame)} sha256={sha}")


if __name__ == "__main__":
    main()
