"""nyiso-160 touchpoint-prep audit — HEAD-replay identity check of the NYISO keeper.

Leg 2 of the winter locational intake (INTAKE-SPEC-nyiso156 §2) STOPPED WITH
CAUSE this session: the owner answered that the MyNYISO AORR files cannot be
produced.  Per the nyiso-160 handoff, the lane pivots to the touchpoint-prep
audit: verify the designated keeper ``2026-08-30-nyiso-159-loss-surface``
(bundle ``nyiso159_lossarm_B``) replays byte-identically at HEAD via the
zero-delta ``scripts/replay_keeper.py`` path, and surface any drift (the G1
drift class of nyiso-155 §4) so it can be closed before any future touchpoint
work.  NO mechanism is tested, armed, disarmed or re-scoped; freeze ACTIVE
(2023–2025 only).

Checks, all on committed-format artifacts (the nyiso-155/157/159 readers):

* **A1 replay identity** — per year, max abs divergence between the replay
  and the keeper bundle on every hourly sidecar the slim bundle carries:
  ``system`` (zonal price / slack / dump / demand / reserve_price),
  ``class_hourly`` (per-class MW), ``reserve_family`` (dual / requirement /
  held / shortfall), ``storage`` (charge / discharge).  Byte-identity in the
  scored objects reads as 0.0 everywhere.
* **A2 scorecard reproduction** — C3a on the committed-anchor basis
  (the nyiso-156 arithmetic) for the replay, against the keeper's committed
  per-year C3a; tolerance ±0.2 pp (the K6 class).
* **A3 recipe identity** — the recorded config surface (scenario block merged
  over flat meta keys, the nyiso-155 template) diffed key-by-key; volatile
  provenance keys (timestamp, note, git shas, environment) excluded.  A
  zero-delta replay must show ZERO differing levers.  One diff class is
  adjudicated rather than failed, fail-closed: a key ABSENT from the
  keeper's recorded surface whose replay value equals the field's
  REGISTERED ``ScenarioConfig`` default (read from the live class, never
  hardcoded here) is **schema growth** — the recorded surface widened when
  a later session registered a new default-off field (rule 24 makes every
  new tunable appear in the recording), not a lever moved on this recipe.
  Schema-growth keys are reported by name; any other mismatch (value vs
  value, or a replay value differing from the registered default) is
  recipe drift and fails the leg.

Output: ``results/calibration/_nyiso160_tpaudit.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
KEEPER = ROOT / "results/calibration/nyiso159_lossarm_B"
REPLAY = ROOT / "results/calibration/nyiso160_tpaudit_replay"
OUT = ROOT / "results/calibration/_nyiso160_tpaudit.json"

YEARS = (2023, 2024, 2025)

#: Committed RT load-weighted actuals (the nyiso-156 anchor; scorer basis).
ACTUAL_RT_LW = {2023: 32.25, 2024: 38.12, 2025: 66.43}

#: Keeper committed per-year C3a (%), from _nyiso159_loss_ab_gates.json /
#: the promotion record (arm B).
KEEPER_C3A = {2023: 2.35, 2024: -1.21, 2025: -11.48}

#: K6-class tolerance on scorecard reproduction (pp).
C3A_TOL_PP = 0.2

#: Hourly sidecars and their (key columns, value columns).
SIDECARS = {
    "system": (["zone", "hour"], ["price", "slack", "dump", "demand", "reserve_price"]),
    "class_hourly": (["klass", "hour"], ["mw"]),
    "reserve_family": (["family", "reserve_class", "hour"], ["dual", "requirement_mw", "held_mw", "shortfall_mw"]),
    "storage": (["tech", "hour"], ["charge_mw", "discharge_mw"]),
}

#: Provenance keys excluded from the recipe diff (nyiso-155 template).
VOLATILE_META = {
    "timestamp",
    "note",
    "years",
    "shared_inputs",
    "git_sha",
    "basis_sha",
    "environment",
    "highspy_version",
    "run_note",
}


def _p1(bundle: Path, name: str, year: int) -> pd.DataFrame:
    """One bundle-year hourly sidecar, P1 rows only."""
    frame = pd.read_parquet(bundle / "hourly" / f"{name}_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _sidecar_max_delta(name: str, year: int) -> dict:
    """Max abs divergence per value column, keeper vs replay, aligned on keys."""
    keys, vals = SIDECARS[name]
    left = _p1(KEEPER, name, year).set_index(keys).sort_index()
    right = _p1(REPLAY, name, year).set_index(keys).sort_index()
    out: dict = {"rows_keeper": int(len(left)), "rows_replay": int(len(right))}
    for col in vals:
        if col not in left.columns or col not in right.columns:
            out[col] = None
            continue
        lj, rj = left[col].align(right[col], join="inner")
        out[col] = round(float((lj - rj).abs().max()), 6) if len(lj) else None
    return out


def _ny_zones(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop any external interchange node rows."""
    return frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]


def _lw_lambda(bundle: Path, year: int) -> float:
    """NYISO demand-weighted mean lambda (the nyiso-156 anchor arithmetic)."""
    ny = _ny_zones(_p1(bundle, "system", year))
    return round(float((ny["price"] * ny["demand"]).sum() / ny["demand"].sum()), 4)


def _c3a_pct(bundle: Path, year: int) -> float:
    """C3a on the committed-anchor basis (reproduces the scorer, nyiso-156)."""
    return round(100.0 * (_lw_lambda(bundle, year) / ACTUAL_RT_LW[year] - 1.0), 2)


def _config_block(bundle: Path) -> dict:
    """Recorded config: scenario block merged over flat meta keys (nyiso-155)."""
    block: dict = {}
    cfg_path = bundle / "run_config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())
        block.update(cfg.get("scenario_config", {}) or {})
    meta_path = bundle / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        for k, v in meta.items():
            if k in VOLATILE_META:
                continue
            block[k] = v
    return block


def _scenario_default(key: str):
    """Registered ScenarioConfig default for one field (sentinel if absent)."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    for field in dataclasses.fields(ScenarioConfig):
        if field.name == key:
            if field.default is not dataclasses.MISSING:
                return field.default
            if field.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
                return field.default_factory()  # type: ignore[misc]
            return _NO_DEFAULT
    return _NO_DEFAULT


_NO_DEFAULT = object()


def _recipe_diff() -> dict:
    """Key-by-key diff of the recorded config surfaces.

    A key absent from the keeper's surface whose replay value equals the
    field's registered ScenarioConfig default is classified schema growth
    (see module docstring); everything else differing is recipe drift.
    """
    a, b = _config_block(KEEPER), _config_block(REPLAY)
    drift: dict = {}
    schema_growth: dict = {}
    for k in sorted(set(a) | set(b)):
        if a.get(k) == b.get(k):
            continue
        if k not in a and k in b and b[k] == _scenario_default(k):
            schema_growth[k] = {"replay_recorded_default": b[k]}
        else:
            drift[k] = {"keeper": a.get(k), "replay": b.get(k)}
    return {
        "n_differing_levers": len(drift),
        "differing_levers": drift,
        "n_schema_growth_keys": len(schema_growth),
        "schema_growth_keys": schema_growth,
    }


def main() -> int:
    """Run the audit and write the JSON record; exit 1 on any drift."""
    a1 = {
        str(y): {name: _sidecar_max_delta(name, y) for name in SIDECARS}
        for y in YEARS
    }
    max_price = {
        str(y): a1[str(y)]["system"]["price"] for y in YEARS
    }
    identical = all(
        v == 0.0
        for year_block in a1.values()
        for sc in year_block.values()
        for k, v in sc.items()
        if k not in ("rows_keeper", "rows_replay") and v is not None
    )

    a2 = {}
    a2_pass = True
    for y in YEARS:
        rep = _c3a_pct(REPLAY, y)
        keep = _c3a_pct(KEEPER, y)
        delta_committed = round(rep - KEEPER_C3A[y], 2)
        row = {
            "replay_c3a_pct": rep,
            "keeper_recomputed_c3a_pct": keep,
            "keeper_committed_c3a_pct": KEEPER_C3A[y],
            "delta_vs_committed_pp": delta_committed,
            "replay_lw_lambda": _lw_lambda(REPLAY, y),
            "keeper_lw_lambda": _lw_lambda(KEEPER, y),
        }
        a2[str(y)] = row
        if abs(delta_committed) > C3A_TOL_PP:
            a2_pass = False

    a3 = _recipe_diff()
    a3_pass = a3["n_differing_levers"] == 0

    record = {
        "probe": "nyiso-160 touchpoint-prep audit (HEAD replay identity)",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "keeper_bundle": "results/calibration/nyiso159_lossarm_B",
        "replay_bundle": "results/calibration/nyiso160_tpaudit_replay",
        "leg2_status": (
            "STOPPED WITH CAUSE — owner cannot produce the MyNYISO AORR files "
            "(INTAKE-SPEC-nyiso156 §2); no substitute winter mechanism invented "
            "(nyiso-158 §1.4)"
        ),
        "A1_replay_identity": {
            "per_year_sidecar_max_abs_delta": a1,
            "max_zonal_dlmp": max_price,
            "byte_identical_scored_objects": identical,
        },
        "A2_scorecard_reproduction": {
            "tolerance_pp": C3A_TOL_PP,
            "per_year": a2,
            "passed": a2_pass,
        },
        "A3_recipe_identity": {**a3, "passed": a3_pass},
        "verdict": {
            "replays_identically": bool(identical and a2_pass and a3_pass),
            "drift_class": None if identical else "G1 (nyiso-155 §4 class)",
        },
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps(record["verdict"], indent=1))
    print(f"wrote {OUT}")
    return 0 if record["verdict"]["replays_identically"] else 1


if __name__ == "__main__":
    sys.exit(main())
