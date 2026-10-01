"""SPP-99 splice CONTROL (zero LP): the HEAD derivers, SPP remap rows stripped, reproduce each incumbent.

Record: ``docs/records/spp/PRECOMMIT-spp-99-remap-rederive-2026-09-28.md``. The miso-280 discipline
(``scripts/data/build_campd_split_remap_companions.py``): a ``-splitremap-`` companion is the
incumbent with the remap plants' lines swapped for the SAME deriver's lines, so it carries the
remap delta and nothing else only if that deriver, run with the remap entries REMOVED, reproduces
the incumbent's lines for those plants. This probe runs each family's deriver in-process with the
ten SPP-98 ``campd.CAMPD_UNIT_PLANT_REMAP`` rows deleted, splices the output into the incumbent
exactly as the builder does, and checks the result is the incumbent byte-for-byte.

Usage: ``python scripts/probes/_spp99_splice_control.py --fresh-dir <dir> [--family ...]``
"""

from __future__ import annotations

import argparse
import hashlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

#: The SPP-98 rows (both sides are SPP plants; every other ISO's entries are kept).
SPP_ROWS = (
    (1416, "CTG-6A"), (1416, "CTG-6B"), (3006, "7"), (3006, "8"), (762, "3"), (762, "4"),
    (63628, "5A-1"), (63628, "5A-2"), (63628, "5B-1"), (63628, "5B-2"),
)  # fmt: skip
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def _run_stripped(argv: list[str]) -> None:
    """Run a deriver script in-process with the SPP remap rows deleted."""
    from market_sim.data import campd

    for k in SPP_ROWS:
        campd.CAMPD_UNIT_PLANT_REMAP.pop(k, None)
    old = sys.argv
    sys.argv = argv
    try:
        runpy.run_path(argv[0], run_name="__main__")
    finally:
        sys.argv = old


def main() -> int:
    """Derive the stripped control of one family (child mode) or check all (parent mode)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh-dir", type=Path, required=True)
    ap.add_argument(
        "--family", nargs="+", default=["stdbase", "stdmask", "cc", "tranches"]
    )
    ap.add_argument(
        "--derive", help="child mode: derive this family's control and exit"
    )
    a = ap.parse_args()
    import scripts.data.build_campd_split_remap_companions as b

    if a.derive:
        fam = a.derive
        years = b.tranche_years("SPP") if fam == "tranches" else YEARS
        out = a.fresh_dir / f"control-{fam}.csv"
        cmd = b.derive_command(fam, "SPP", years, out)[1:]
        if fam == "tranches":
            cmd.remove("--split-remap-denominator")  # the incumbent's own denominator
        _run_stripped(cmd)
        return 0
    import subprocess

    ok = True
    for fam in a.family:
        out = a.fresh_dir / f"control-{fam}.csv"
        if not out.exists():
            subprocess.run(
                [
                    sys.executable,
                    __file__,
                    "--fresh-dir",
                    str(a.fresh_dir),
                    "--derive",
                    fam,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        inc = b.incumbent_path(fam, "SPP")
        years = b.tranche_years("SPP") if fam == "tranches" else YEARS
        plant_col, year_col, anchors = b._KEYS[fam]
        text, counts = b.splice(
            inc.read_text(),
            out.read_text(),
            b.remap_plants(),
            plant_col,
            year_col,
            set(years) if year_col else None,
            anchors,
        )
        same = text == inc.read_text()
        ok &= same
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        print(
            f"CONTROL {fam}: {'PASS' if same else 'FAIL'} -- {inc.name} {counts} sha {h}"
        )
    print("SPLICE CONTROL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
