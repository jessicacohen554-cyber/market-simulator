#!/usr/bin/env python
"""Score the entry-signal DISARM probe's ledger against the L-1 predictions.

The adjudicating measurement named by ``docs/FINDING-entry-signal-l1-2026-08.md``
§4 item 2 / §5: re-run the ERCOT 2021-2025 T1-H capacity hindcast at the
registered ``ercot-2021-2025-realized-t1h-refresh`` posture with ONE flag
changed — ``entry_lookahead_reprice=False`` — which arms the existing duals
fallback so every capacity screen reads the run's OWN prior-year hourly zonal
LP duals instead of the zone-flat MC-step signal.

This probe reads three committed/produced bundles and emits one artifact:

* the DISARM arm (the treatment),
* a CONTROL arm re-solved at the registered posture from the SAME source tree,
  so the disarm delta is measured against a like-for-like re-solve rather than
  against a bundle solved on an older tree (the control also re-derives the
  reserve-margin trajectory, which the registered bundle does not commit), and
* the registered bundle's committed ``score.json``, as the provenance anchor.

Why a control arm exists at all: the registered bundle commits no evolution
ledgers (repo policy — ``.gitignore`` §9: "bundle internals are reproducible
from the recorded config"), so its per-step entry decisions and reserve margins
are otherwise only available as the L-1b *reconstruction*. Re-solving the
shipped posture recovers them as measurement. It doubles as the adjudicating
control for re-solve determinism (see ``resolve_determinism`` below).

The predictions scored here are PRE-REGISTERED — committed in
``results/calibration/entry_signal_l1_dual_replay_ercot.json`` and tabulated in
the L-1 finding §1.2-§1.4 — before this solve existed.

Usage::

    uv run python scripts/probes/entry_signal_disarm_ledger_compare.py \\
        --disarm results/hindcast/ercot-2021-2025-realized-t1h-disarm \\
        --control results/hindcast/ercot-2021-2025-realized-t1h-control \\
        --registered results/hindcast/ercot-2021-2025-realized-t1h-refresh \\
        --out results/calibration/entry_signal_disarm_ledger_ercot.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ISO = "ERCOT"
# Entering-year reserve margins of the REGISTERED run as quoted by the L-1b
# probe (scripts/probes/entry_signal_l1b_allocator_counterfactual.py:135) and
# the finding's B-2 row. Kept ONLY as the provenance anchor for the reconstructed
# trajectory; this probe's own comparison uses the control arm's measured
# ledgers, which need no anchor.
REGISTERED_RM_PCT_RECONSTRUCTED = {2022: 19.0, 2023: 8.5, 2024: 14.7, 2025: 25.2}


def bundle_key_dir(bundle: Path) -> Path:
    """Return the single per-ISO cache-key directory inside a bundle."""
    keys = [p for p in sorted((bundle / ISO).iterdir()) if p.is_dir()]
    if len(keys) != 1:
        raise SystemExit(f"expected exactly one cache key under {bundle / ISO}")
    return keys[0]


def read_ledgers(bundle: Path) -> dict[int, dict]:
    """Load ``evolution_<year>.json`` for one bundle, keyed by year."""
    out: dict[int, dict] = {}
    for p in sorted(bundle_key_dir(bundle).glob("evolution_*.json")):
        out[int(p.stem.split("_")[1])] = json.loads(p.read_text())
    if not out:
        raise SystemExit(
            f"no evolution ledgers under {bundle} — the bundle's internals are "
            "gitignored, so this probe must run in the session that solved it"
        )
    return out


def step_rows(ledgers: dict[int, dict]) -> dict[str, dict]:
    """Per-ledger-year entry decisions, storage build by tech, and RM."""
    rows: dict[str, dict] = {}
    for year, led in sorted(ledgers.items()):
        storage: dict[str, float] = {}
        for add in led.get("storage_additions") or []:
            storage[add["tech"]] = storage.get(add["tech"], 0.0) + float(add["mw"])
        rm = led.get("reserve_margin")
        rows[str(year)] = {
            "bridge": bool(led.get("bridge")),
            "reserve_margin_pct": None if rm is None else round(100.0 * rm, 2),
            "entry_decided_mw_by_tech": {
                k: round(float(v), 1)
                for k, v in (led.get("entry_decided_mw_by_tech") or {}).items()
            },
            "storage_decided_mw_by_tech": {
                k: round(v, 1) for k, v in sorted(storage.items())
            },
            "peak_demand_mw": led.get("peak_demand_mw"),
            "n_retirements": len(led.get("retirements") or []),
        }
    return rows


def score_block(bundle: Path) -> dict:
    """The bundle's committed score.json."""
    return json.loads((bundle_key_dir(bundle) / "score.json").read_text())


def additions_table(*, actual_from: dict, arms: dict[str, dict]) -> dict:
    """Per-tech actual/model GW and |error| GW for each arm, side by side."""
    techs = list(actual_from["additions"]["by_tech"])
    out: dict[str, dict] = {}
    for tech in techs:
        row: dict = {
            "actual_gw": actual_from["additions"]["by_tech"][tech]["actual_gw"]
        }
        for label, sc in arms.items():
            cell = sc["additions"]["by_tech"].get(tech, {})
            model = cell.get("model_gw")
            row[label] = {
                "model_gw": model,
                "err_frac": cell.get("err_frac"),
                "band": cell.get("band"),
                "abs_err_gw": (
                    None
                    if model is None
                    else round(abs(model - row["actual_gw"]), 3)
                ),
            }
        out[tech] = row
    return out


def resolve_determinism(control: dict, registered: dict) -> dict:
    """Is a same-key re-solve bit-reproducible on the committed score?

    This is the control for work item 2's byte-identity question. The CAISO
    dump run differs from its registered bundle in the CO2 aggregate alone
    while every fleet metric is identical, and the candidate explanations are
    (a) the ``entry_screen_diagnostics`` flag perturbing dispatch — which would
    falsify its documented contract — or (b) LP re-solve nondeterminism, which
    would be a property of re-solving at all and NOT attributable to the flag.

    The control arm decides it: it re-solves the SHIPPED ERCOT posture at the
    registered cache key, changing NOTHING. Any CO2 drift it shows is (b) by
    construction, because there is no flag in play.
    """
    out: dict = {"same_cache_key": None, "co2_by_year": {}, "fleet_metrics_identical": None}
    ctrl_co2 = (control.get("co2") or {}).get("model") or {}
    reg_co2 = (registered.get("co2") or {}).get("model") or {}
    for year in sorted(set(ctrl_co2) | set(reg_co2)):
        c, r = ctrl_co2.get(year), reg_co2.get(year)
        out["co2_by_year"][year] = {
            "registered_t": r,
            "control_t": c,
            "delta_t": None if (c is None or r is None) else round(c - r, 3),
            "rel_delta": (
                None if (c is None or r is None or not r) else round((c - r) / r, 8)
            ),
        }
    out["fleet_metrics_identical"] = all(
        control.get(k) == registered.get(k)
        for k in ("additions", "retirements", "retirements_is", "bands")
    )
    return out


def main() -> None:
    """CLI entry point: emit the disarm-vs-control comparison as one artifact."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--disarm", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--registered", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    disarm, control, registered = (
        REPO / args.disarm,
        REPO / args.control,
        REPO / args.registered,
    )
    sc_d, sc_c, sc_r = (score_block(b) for b in (disarm, control, registered))
    meta_d = json.loads((disarm / "meta.json").read_text())
    meta_c = json.loads((control / "meta.json").read_text())
    meta_r = json.loads((registered / "meta.json").read_text())

    result = {
        "probe": "entry_signal_disarm_ledger_compare",
        "finding": "docs/FINDING-entry-signal-disarm-2026-08.md",
        "charter": "docs/FINDING-entry-signal-l1-2026-08.md §4 item 2 / §5",
        "iso": ISO,
        "arms": {
            "disarm": {
                "bundle": args.disarm,
                "cache_key": meta_d["cache_key"],
                "entry_lookahead_reprice": meta_d["entry_lookahead_reprice"],
                "capacity_screen_unified_lookahead": meta_d[
                    "capacity_screen_unified_lookahead"
                ],
                "capacity_screen_scarcity_restoration": meta_d[
                    "capacity_screen_scarcity_restoration"
                ],
                "solved_years": meta_d["solved_years"],
                "bridged_years": meta_d["bridged_years"],
            },
            "control": {
                "bundle": args.control,
                "cache_key": meta_c["cache_key"],
                "entry_lookahead_reprice": meta_c["entry_lookahead_reprice"],
                "solved_years": meta_c["solved_years"],
                "bridged_years": meta_c["bridged_years"],
            },
            "registered": {
                "bundle": args.registered,
                "cache_key": meta_r["cache_key"],
                "entry_lookahead_reprice": meta_r["entry_lookahead_reprice"],
            },
        },
        "posture_check": {
            "control_reproduces_registered_key": (
                meta_c["cache_key"] == meta_r["cache_key"]
            ),
            "disarm_differs_only_in_reprice": (
                meta_d["cache_key"] != meta_r["cache_key"]
                and meta_d["entry_lookahead_reprice"] is False
                and meta_r["entry_lookahead_reprice"] is True
            ),
            "same_solve_span": (
                meta_d["solved_years"] == meta_r["solved_years"]
                and meta_d["bridged_years"] == meta_r["bridged_years"]
            ),
        },
        "ledger": {
            "disarm": step_rows(read_ledgers(disarm)),
            "control": step_rows(read_ledgers(control)),
        },
        "reserve_margin_reconstructed_registered": REGISTERED_RM_PCT_RECONSTRUCTED,
        "additions": additions_table(
            actual_from=sc_r, arms={"registered": sc_r, "control": sc_c, "disarm": sc_d}
        ),
        "retirements_total_gw": {
            "actual": sc_r["retirements"]["total_gw"]["actual"],
            "registered": sc_r["retirements"]["total_gw"]["model"],
            "control": sc_c["retirements"]["total_gw"]["model"],
            "disarm": sc_d["retirements"]["total_gw"]["model"],
        },
        "resolve_determinism_control": resolve_determinism(sc_c, sc_r),
        "dump_production": {
            "registered_npz": len(list(bundle_key_dir(registered).glob("*.npz"))),
            "disarm_npz": len(list(bundle_key_dir(disarm).glob("*.npz"))),
            "note": (
                "the screen-signal dump is emitted inside the reprice gate "
                "(runner.py: the `_screen_signal_for` body), so a disarmed run "
                "emits none — the signal the screens read becomes econ_prices "
                "itself, recoverable from the run's own hourly outputs rather "
                "than from a dedicated dump"
            ),
        },
    }

    out_path = (
        Path(args.out) if Path(args.out).is_absolute() else REPO / args.out
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {out_path}")
    pc = result["posture_check"]
    print(f"posture_check: {pc}")
    if not all(pc.values()):
        raise SystemExit(
            "posture check FAILED — the arms are not the single-flag pair this "
            "probe claims to compare"
        )


if __name__ == "__main__":
    main()
