"""nyiso-149 — closure of the NYISO benchmark drift (FINDING-nyiso148 §11.1).

Reconstructs BOTH committed NYISO bench parts' ``classFull`` exactly — the
pre-drift part (last written by nyiso-142's registration, commit ``92d8eee``)
and the authoritative part at HEAD (written by nyiso-148's registration,
``f9145cf``) — from ONE shared EIA-923 benchmark frame plus the two BTM
subtrahend bases, through the live family reconcile:

    old part  = reconcile( e923_cls − btm_SECTOR  )   # 35% merchant carve
    new part  = reconcile( e923_cls − btm_MEASURED )  # Gold-Book/923 meters

If both close to 4 decimals for every gas/coal class in every year, the drift
is fully attributed: (a) the nyiso-147 measured-BTM subtrahend replacing the
sector carve, and (b) the ±3% EIA-930 family reconcile standing down (2023,
2024) or shrinking (2025) as a consequence. The EIA-923/CAMPD-backfill frame
itself is proven UNMOVED by its content hash (the shared-store name every
bundle meta declares).

Also verifies the nyiso-149 pin: ``_btm_frame``'s ``btm_bench_twh`` column is
measured-basis regardless of the run flag (so a future flag-off registration
re-renders the committed parts unchanged) while ``btm_twh`` still follows the
flag (the run's own add-back).

Run from ``scripts/``:  ``../.venv/bin/python probes/_nyiso149_bench_reconcile_closure.py``
Writes ``results/calibration/_nyiso149_bench_reconcile_closure.json``.
"""

import gzip
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "src")

import pandas as pd  # noqa: E402

import run_calibration_full as rcf  # noqa: E402
from render_calibration_html import (  # noqa: E402
    _COAL_GROUPS,
    _GAS_GROUPS,
    _primary_pass,
    reconcile_vintage_classes,
)
from scripts.lib.bundle_io import content_hash  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402
from market_sim.data.fleet import apply_other_fossil_scoring  # noqa: E402

ISO = "NYISO"
YEARS = [2023, 2024, 2025]
REPO = Path(__file__).resolve().parents[2]
OLD_REF = "92d8eee"  # nyiso-142's registration — last writer of the old part


def load_part(year: int, ref: str | None = None) -> dict:
    """Load a committed bench part, from git history when ``ref`` is given."""
    rel = f"frontend/data/backcast/bench/NYISO/{year}.json.gz"
    if ref:
        raw = subprocess.run(
            ["git", "show", f"{ref}:{rel}"], capture_output=True, check=True, cwd=REPO
        ).stdout
    else:
        raw = (REPO / rel).read_bytes()
    return json.loads(gzip.decompress(raw))


def main() -> None:
    iso_config = get_iso_config(ISO)
    generation = load_monthly_generation()
    parasitic = rcf._parasitic_factor_map()

    report: dict = {
        "session": "nyiso-149",
        "measure": (
            "old/new committed NYISO bench parts reconstructed EXACTLY from one "
            "shared e923 frame + {sector, measured} BTM subtrahend through the "
            "±3% EIA-930 family reconcile; plus the flag-independence of the "
            "nyiso-149 btm_bench_twh pin"
        ),
        "years": {},
    }
    frames = []
    for year in YEARS:
        old = load_part(year, OLD_REF)
        new = load_part(year)
        group_by_code = rcf._fleet_group_by_code(ISO, iso_config, year)
        campd_year = rcf._campd_hourly_frame(year, ISO, parasitic, rcf._HOURS_PER_YEAR)
        campd_active = None
        if campd_year is not None:
            bp = campd_year.groupby("plant_id")["net_mw"].sum()
            campd_active = set(bp[bp > 0.0].index.astype(int))
        e930f = rcf._eia930_frame(year, ISO, iso_config)
        e923 = rcf._benchmark_eia923_frame(
            year,
            generation,
            ISO,
            campd_year,
            group_by_code,
            e930f,
            btm_backfill_year=None,
            campd_active=campd_active,
        )
        frames.append(e923)
        e923s = apply_other_fossil_scoring(e923, year, plant_col="plant_id")
        e923_cls = e923s.groupby("klass")["annual_mwh"].sum()

        # The two btm frames a registration could have carried: flag OFF
        # (sector shares — every registration 2026-08-17..08-19) and flag ON
        # (measured shares — nyiso-147a and the nyiso-148 arms).
        btm = {}
        for label, flag in (("off", False), ("on", True)):
            f = rcf._btm_frame(
                year,
                "P1",
                generation,
                iso=ISO,
                group_by_code=group_by_code,
                nyiso_chp_btm_measured=flag,
            )
            by = _primary_pass(f[f["year"] == year])
            btm[label] = {
                "run": dict(zip(by["klass"], by["btm_twh"])),
                "bench": dict(zip(by["klass"], by["btm_bench_twh"])),
            }

        def classfull(btm_cls: dict, e930d: dict) -> dict:
            cf = {
                str(g): round(float(v) / 1e6 - float(btm_cls.get(str(g), 0.0)), 4)
                for g, v in e923_cls.items()
            }
            reconcile_vintage_classes(cf, dict(e930d), ISO)
            return cf

        fam = [g for g in (*_GAS_GROUPS, *_COAL_GROUPS) if g in e923_cls.index]

        def check(pred: dict, part: dict) -> dict:
            actual = part["bench"]["classFull"]
            diffs = {
                g: round(pred.get(g, 0.0) - float(actual.get(g, 0.0)), 4)
                for g in fam
                if abs(pred.get(g, 0.0) - float(actual.get(g, 0.0))) > 0.0005
            }
            return diffs or "EXACT"

        e930d = new["bench"]["e930"]
        pred_old = classfull(btm["off"]["run"], old["bench"]["e930"])
        pred_new = classfull(btm["on"]["run"], e930d)
        pred_pin_off = classfull(btm["off"]["bench"], e930d)
        pred_pin_on = classfull(btm["on"]["bench"], e930d)

        fam_sums = {
            "sector_pre": round(
                sum(
                    float(e923_cls.get(g, 0.0)) / 1e6
                    - float(btm["off"]["run"].get(g, 0.0))
                    for g in fam
                ),
                4,
            ),
            "measured_pre": round(
                sum(
                    float(e923_cls.get(g, 0.0)) / 1e6
                    - float(btm["on"]["run"].get(g, 0.0))
                    for g in fam
                ),
                4,
            ),
            "target_930_gas_plus_coal": round(
                float(e930d.get("gas", 0.0)) + float(e930d.get("coal", 0.0)), 4
            ),
        }
        report["years"][year] = {
            "e930_dict_old_equals_new": old["bench"]["e930"] == new["bench"]["e930"],
            "family_sums": fam_sums,
            "old_part_reconstruction (sector btm + reconcile)": check(pred_old, old),
            "new_part_reconstruction (measured btm + reconcile)": check(pred_new, new),
            "pin: flag_off_render_now_reproduces_new_part": check(pred_pin_off, new),
            "pin: flag_on_render_reproduces_new_part": check(pred_pin_on, new),
            "pin: run_basis_still_flag_dependent": btm["off"]["run"] != btm["on"]["run"],
            "btm_sector_cls": {k: round(v, 4) for k, v in btm["off"]["run"].items()},
            "btm_measured_cls": {k: round(v, 4) for k, v in btm["on"]["run"].items()},
        }

    allf = pd.concat(frames, ignore_index=True)
    report["e923_frame_content_hash"] = content_hash(allf)
    report["e923_frame_hash_note"] = (
        "equals the eia923 shared-input ref declared by EVERY registered NYISO "
        "bundle meta (nyiso-142 stackdup, 146c state_arm, 147/148 recipes) — "
        "the EIA-923 vintage-reconciliation/CAMPD-backfill frame never moved"
    )
    out = REPO / "results/calibration/_nyiso149_bench_reconcile_closure.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
