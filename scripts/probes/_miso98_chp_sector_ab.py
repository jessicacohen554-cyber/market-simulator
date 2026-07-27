"""miso-98 A/B driver: MISO CHP ``chp_sector`` absent (A) vs measured (B).

The single delta is the ``chp_sector`` column of
``data/raw/_processed-legacy/thermal_tranches_MISO.csv`` — all-NaN in arm A
(the pre-``f883346`` blob, so ``data.chp.chp_btm_pct`` falls through to the
unsourced ``CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0`` /
``CHP_ST_BTM_PCT = 90.0`` defaults) vs the merged EIA-860-sourced column on 104
rows (arm B).  Every other column of that artifact, and every other file in the
tree, is byte-identical between the arms — verified before each solve.  See
``results/calibration/FINDING-miso97-chp-sector-btm-2026-07.md`` §5.1 for the
pre-registered prediction this A/B is run against.

**Arm A cannot be the registered ``miso88_egrid_hr`` bundle.**  miso-92 §7
records that post-CAMPD-envelope-correction replays do not reproduce the
keeper's registered numbers, so both arms are same-HEAD replays of the keeper
recipe and only the arm-vs-arm delta is quoted.

The keeper recipe is rebuilt from ``miso88_egrid_hr/meta.json`` rather than from
``run_config.json``'s ``calibration_flags`` — the latter is a curated ~35-key
subset that omits ~170 non-default kwargs this keeper actually solved with, and
a mis-specified arm mis-attributes the delta rather than measuring it.
``meta.json`` records every ``solve_and_persist`` kwarg (1:1 by name bar the
four renames below), the same reconstruction ``_neiso_tempderate_ab.py`` uses.

MISO is the tightest ISO on memory (14.34-14.41 GB single-year peak on a 15 GB
box, miso-92 §7), so this driver solves **one fresh year per process** and
chains the cumulative bundle forward with ``--reuse-solved``.  Never invoke it
with more than one unsolved year.

Usage (one process per stage, sequentially — never two MISO solves at once):

    python scripts/probes/_miso98_chp_sector_ab.py --arm A --years 2023 \
        --out results/calibration/miso98_chp_sector_A_y23
    python scripts/probes/_miso98_chp_sector_ab.py --arm A --years 2023 2024 \
        --out results/calibration/miso98_chp_sector_A_y2324 \
        --reuse-from results/calibration/miso98_chp_sector_A_y23
    python scripts/probes/_miso98_chp_sector_ab.py --arm A --years 2023 2024 2025 \
        --out results/calibration/miso98_chp_sector_A \
        --reuse-from results/calibration/miso98_chp_sector_A_y2324
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

RESULTS = REPO / "results" / "calibration"
KEEPER = RESULTS / "miso88_egrid_hr"
TRANCHES = REPO / "data" / "raw" / "_processed-legacy" / "thermal_tranches_MISO.csv"

# The two arm variants, materialised by ``--variant-dir`` (default: the session
# scratchpad).  Hashes are asserted before every solve so a half-restored tree
# cannot silently solve the wrong arm — the miso-94 §5 contamination trap.
ARM_FILES = {"A": "tranches_MISO_ARM_A.csv", "B": "tranches_MISO_ARM_B.csv"}
ARM_SHA = {
    "A": "ccbcc69def70843a0e98c0a53fda37a402322eaf390aa5aa0e6e1832aeb7326e",
    "B": "31949ee5e13475db7611c2c6f15175626e17d414df534fab9179be66614280d8",
}

# meta.json key -> solve_and_persist kwarg name, where they differ.
_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# meta.json keys that are recorded provenance/derived values, not kwargs.
_SKIP = {
    "timestamp",
    "iso",
    "years",
    "hours",
    "passes",
    "commitment",  # passed explicitly below (keeper value, unchanged)
    "gas_prices",  # re-derived internally from reference + years
    "coal_plant_monthly_pricing",  # derived from backcast_config, not a kwarg
    "td_loss_factor",  # derived from backcast_config, not a kwarg
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
    "shared_inputs",
    "environment",
    "reuse",
    "git_sha",
    "highspy_version",
}


def _sha256(path: Path) -> str:
    """Hex SHA-256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def keeper_kwargs() -> dict:
    """Rebuild the miso-88 keeper's ``solve_and_persist`` kwargs from meta.json."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    sig = set(inspect.signature(solve_and_persist).parameters)
    kwargs = {}
    for key, value in meta.items():
        if key in _SKIP:
            continue
        pname = _RENAME.get(key, key)
        if pname not in sig:
            raise SystemExit(f"unmapped meta.json key: {key!r}")
        kwargs[pname] = value
    return kwargs


def arm_tranches(arm: str, variant_dir: Path) -> None:
    """Put arm ``arm``'s tranche artifact in place and assert its hash."""
    src = variant_dir / ARM_FILES[arm]
    if _sha256(src) != ARM_SHA[arm]:
        raise SystemExit(f"arm {arm} variant {src} has the wrong hash")
    shutil.copyfile(src, TRANCHES)
    live = _sha256(TRANCHES)
    if live != ARM_SHA[arm]:
        raise SystemExit(f"tranche artifact did not take arm {arm}: {live}")
    print(f"[arm {arm}] thermal_tranches_MISO.csv sha256={live}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=("A", "B"), required=True)
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reuse-from", type=Path, default=None)
    ap.add_argument(
        "--variant-dir",
        type=Path,
        default=Path("/tmp/claude-0/-home-user-market-simulator")
        / "202c4f03-9dd2-501c-8680-226c204c13af"
        / "scratchpad"
        / "ab",
    )
    args = ap.parse_args()

    arm_tranches(args.arm, args.variant_dir)
    kwargs = keeper_kwargs()
    args.out.mkdir(parents=True, exist_ok=True)

    arm_desc = (
        "chp_sector all-NaN (pre-f883346 blob), so BTM falls through to the "
        "unsourced merchant 35.0 / ST 90.0 defaults"
        if args.arm == "A"
        else "chp_sector = the measured EIA-860 sector on 104 rows"
    )
    note = (
        f"miso-98 CHP sector A/B, arm {args.arm} ({arm_desc}). "
        "SINGLE DELTA vs the other arm: the chp_sector column of "
        "thermal_tranches_MISO.csv; every other column and file byte-identical. "
        "Keeper recipe (2026-07-25-miso-88-egrid-hr) rebuilt from meta.json. "
        "Evidence: results/calibration/FINDING-miso97-chp-sector-btm-2026-07.md"
    )

    solve_and_persist(
        list(args.years),
        "MISO",
        8760,
        _load_reference(),
        run_dir=args.out,
        commitment=False,
        reuse_solved=args.reuse_from,
        note=note,
        **kwargs,
    )
    print(f"DONE arm {args.arm} years={args.years} -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
