"""D11-R: margin-exhaustion volume rule A/B — arm vs control, ERCOT T1-H.

Compares the ``entry_margin_exhaustion`` treatment against a same-tree
control (both solved by THIS session on one HEAD): posture verification
(exactly one ``run_config`` field differs), per-step entry/storage decisions,
the ledger reserve-margin path with its swings (the B-2 cobweb survival
check), the four committed terminal-RM anchors, and the additions-band table
from each bundle's ``score.json``.

Anchors quoted (committed citations, never recomputed here):
* shipped control 25.19 % / disarm 40.24 % / forward-expectation 40.38 % —
  ``docs/FINDING-entry-signal-forward-expectation-2026-08-25.md`` §2.1;
* L-1b offline margin-exhaustion 18.7 % —
  ``docs/FINDING-entry-signal-l1-2026-08.md`` §2.3 (its open-loop offline
  reconstruction, NOT the same instrument as a live solve).

Usage::

    uv run python scripts/probes/entry_volume_rule_compare.py \
        --arm results/hindcast/ercot-2021-2025-realized-t1h-d11r-exhaustion \
        --control results/hindcast/ercot-2021-2025-realized-t1h-d11r-control \
        --out results/calibration/entry_volume_rule_ab_ercot.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ISO = "ERCOT"

# Committed terminal-RM anchors (see module docstring for citations).
ANCHORS_TERMINAL_RM_PCT = {
    "shipped_control_committed": 25.19,
    "disarm_raw_duals_committed": 40.24,
    "forward_expectation_committed": 40.38,
    "l1b_offline_margin_exhaustion": 18.7,
}
# Registered RM swings (pp) for the B-2 comparison rows
# (entry_signal_l1 finding §2.3).
REGISTERED_SWINGS_PP = [-10.5, +6.2, +10.5]
L1B_OFFLINE_SWINGS_PP = [-10.5, +1.6, +8.6]


def key_dir(bundle: Path) -> Path:
    """The single cache-key directory under ``<bundle>/ERCOT``."""
    keys = [p for p in sorted((bundle / ISO).iterdir()) if p.is_dir()]
    if len(keys) != 1:
        raise SystemExit(f"expected exactly one cache key under {bundle / ISO}")
    return keys[0]


def read_ledgers(bundle: Path) -> dict[int, dict]:
    """Load ``evolution_<year>.json`` for one bundle, keyed by year."""
    out: dict[int, dict] = {}
    for p in sorted(key_dir(bundle).glob("evolution_*.json")):
        out[int(p.stem.split("_")[1])] = json.loads(p.read_text())
    if not out:
        raise SystemExit(
            f"no evolution ledgers under {bundle} — this probe must run in "
            "the session that solved the bundle (internals are gitignored)"
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


def rm_path(rows: dict[str, dict]) -> dict:
    """RM path over the ledger years, swings, terminal value."""
    years = sorted(rows)
    path = {y: rows[y]["reserve_margin_pct"] for y in years}
    vals = [v for v in path.values() if v is not None]
    swings = [
        round(b - a, 2)
        for a, b in zip(vals, vals[1:])
        if a is not None and b is not None
    ]
    return {
        "path_pct": path,
        "swings_pp": swings,
        "terminal_rm_pct": vals[-1] if vals else None,
    }


def config_delta(arm: Path, control: Path) -> dict:
    """Every scenario_config field that differs between the two bundles."""
    a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    c = json.loads((control / "run_config.json").read_text())["scenario_config"]
    keys = sorted(set(a) | set(c))
    diff = {
        k: {"control": c.get(k), "arm": a.get(k)}
        for k in keys
        if a.get(k) != c.get(k)
    }
    return diff


def score_block(bundle: Path) -> dict | None:
    """The bundle's score.json, if the session scored it."""
    p = key_dir(bundle) / "score.json"
    return json.loads(p.read_text()) if p.exists() else None


def main() -> None:
    """CLI entry: verify posture, compare arms, emit the A/B record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument(
        "--expect-delta",
        default="entry_margin_exhaustion",
        help=(
            "Comma-separated run_config booleans that must be the EXACT "
            "arm-vs-control delta, each False -> True. Default is the D11-R "
            "single field; the D12-C confirmation pair (Q10, capx director "
            "ledger §0l.2) passes "
            "entry_margin_exhaustion,entry_forward_reserve_leg — the TWO "
            "fields as the single logical delta."
        ),
    )
    args = ap.parse_args()
    arm = args.arm if args.arm.is_absolute() else REPO / args.arm
    control = args.control if args.control.is_absolute() else REPO / args.control
    expected = sorted(f for f in args.expect_delta.split(",") if f)

    delta = config_delta(arm, control)
    if sorted(delta) != expected or not all(
        delta[f]["arm"] is True and delta[f]["control"] is False for f in expected
    ):
        raise SystemExit(
            "posture verification FAILED — the arms must differ in exactly "
            f"{expected} (each False -> True); got {json.dumps(delta)}"
        )

    rows_c = step_rows(read_ledgers(control))
    rows_a = step_rows(read_ledgers(arm))
    rm_c = rm_path(rows_c)
    rm_a = rm_path(rows_a)

    # B-2 survival: the oscillation's sign pattern must survive in the arm —
    # the L-1b precommit's red-flag test is an implementation that kills it.
    signs_a = [s > 0 for s in rm_a["swings_pp"]]
    signs_reg = [s > 0 for s in REGISTERED_SWINGS_PP]
    b2_survives = signs_a == signs_reg and any(
        abs(s) > 1.0 for s in rm_a["swings_pp"]
    )

    out = {
        "probe": "entry_volume_rule_compare",
        "lane": "D11-R (docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md)",
        "iso": ISO,
        "bundles": {"control": str(control), "arm": str(arm)},
        "posture": {
            "expected_delta": expected,
            "config_delta": delta,
            "cache_keys": {
                "control": json.loads((control / "meta.json").read_text())[
                    "cache_key"
                ],
                "arm": json.loads((arm / "meta.json").read_text())["cache_key"],
            },
        },
        "steps": {"control": rows_c, "arm": rows_a},
        "rm": {"control": rm_c, "arm": rm_a},
        "anchors_terminal_rm_pct": ANCHORS_TERMINAL_RM_PCT,
        "registered_swings_pp": REGISTERED_SWINGS_PP,
        "l1b_offline_swings_pp": L1B_OFFLINE_SWINGS_PP,
        "b2_cobweb_survives_in_arm": b2_survives,
        "score": {"control": score_block(control), "arm": score_block(arm)},
    }
    out_path = args.out if args.out.is_absolute() else REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {out_path}")
    print("terminal RM: control", rm_c["terminal_rm_pct"], "arm", rm_a["terminal_rm_pct"])
    print("arm swings:", rm_a["swings_pp"], "B-2 survives:", b2_survives)


if __name__ == "__main__":
    main()
