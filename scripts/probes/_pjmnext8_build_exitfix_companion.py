"""PJM-NEXT-8 card 2 — build the '-rederive-peakerkeep-exitfix-unitfuel-' companion. ZERO LP.

Owner card 2026-09-28 ("Build + solve"): the exit-cohort repair of the CAMPD
unit-outage layer (docs/FINDING-pjm-next-7-coal-phase0-2026-09-28.md §3). The
construction is the keeper's own (PJM-NEXT-6, step for step) with ONE switch:

1. derive_campd_unit_outages.py --iso PJM --years 2019..2025
   --membership-vintage-union --keep-listed-peaker-dead-periods
   [--exit-cohort-repair]
2. rows starting outside 2019-2025 carried verbatim from
   campd-unit-outages-memberrepair-PJM.csv, placed FIRST;
3. build_outage_unit_fuel_routing.build_companion.

Step 0 (the control) runs the construction WITHOUT the switch and asserts it
reproduces the keeper's committed companion byte-for-byte (sha256 5171a5fb...),
so the switch is the only difference. Carried out-of-span rows get an empty
``exit_ym`` (no dated bin exists outside the span).

Usage: uv run python scripts/probes/_pjmnext8_build_exitfix_companion.py --scratch DIR
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
KEEPER = RAW / "campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv"
KEEPER_SHA = "5171a5fb37bbd2a535a7f8cbde5ae06d735186d520a4620fcfe84f9f1e8d1ae9"
OUT = RAW / "campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def _derive(scratch: Path, repair: bool) -> pd.DataFrame:
    """Run the HEAD deriver into ``scratch`` and return its extract."""
    out = scratch / ("exitfix.csv" if repair else "split.csv")
    cmd = [
        sys.executable,
        str(REPO / "scripts/data/derive_campd_unit_outages.py"),
        "--iso",
        "PJM",
        "--years",
        *map(str, YEARS),
        "--membership-vintage-union",
        "--keep-listed-peaker-dead-periods",
        "--out",
        str(out),
    ]
    if repair:
        cmd.append("--exit-cohort-repair")
    if not out.exists():
        subprocess.run(cmd, check=True, cwd=REPO)
    return pd.read_csv(
        out, dtype={"exit_ym": str}, keep_default_na=False, na_values=[""]
    )


def _assemble(derived: pd.DataFrame) -> bytes:
    """Carry out-of-span incumbent rows first, then fuel-route; return CSV bytes."""
    inc = pd.read_csv(RAW / "campd-unit-outages-memberrepair-PJM.csv")
    carry = inc[~pd.to_datetime(inc.outage_start).dt.year.between(YEARS[0], YEARS[-1])]
    base = pd.concat([carry, derived], ignore_index=True)
    comp, _ = build_companion(base)
    return comp.to_csv(index=False).encode()


def main() -> None:
    """Build the companion after proving the control reproduces the keeper file."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scratch", required=True, type=Path)
    args = ap.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    ctrl = _assemble(_derive(args.scratch, repair=False))
    assert hashlib.sha256(ctrl).hexdigest() == KEEPER_SHA, (
        "control does not reproduce keeper"
    )
    print("control reproduces the keeper companion byte-for-byte")
    body = _assemble(_derive(args.scratch, repair=True))
    OUT.write_bytes(body)
    sha = hashlib.sha256(body).hexdigest()
    frame = pd.read_csv(OUT)
    by_year = pd.to_datetime(frame.outage_start).dt.year.value_counts().sort_index()
    meta = json.loads(KEEPER.with_suffix(".meta.json").read_text())
    meta.update(
        artifact=OUT.name,
        artifact_rows=int(len(frame)),
        artifact_sha256=sha,
        windows_by_start_year={str(k): int(v) for k, v in by_year.items()},
    )
    meta["derive_invocation"]["exit_cohort_repair"] = True
    meta.pop("pjm_next6_construction", None)
    meta["pjm_next8_construction"] = {
        "session": "PJM-NEXT-8 card 2, 2026-09-28 (owner card 'Build + solve')",
        "deriver_invocation": "derive_campd_unit_outages.py --iso PJM --years 2019..2025 "
        "--membership-vintage-union --keep-listed-peaker-dead-periods --exit-cohort-repair",
        "control": f"same construction without the switch reproduces {KEEPER.name} sha256 {KEEPER_SHA}",
        "span_rows": "2019-2025 from the HEAD re-derive; out-of-span rows carried verbatim "
        "from campd-unit-outages-memberrepair-PJM.csv, placed first",
        "post_step": "scripts/data/build_outage_unit_fuel_routing.build_companion",
        "selected_by": "ScenarioConfig.unit_outage_exit_cohort_repair "
        "(on top of unit_outage_rederive_peaker_windows)",
        "builder": "scripts/probes/_pjmnext8_build_exitfix_companion.py",
    }
    OUT.with_suffix(".meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n"
    )
    print(f"wrote {OUT.name} rows={len(frame)} sha256={sha}")


if __name__ == "__main__":
    main()
