"""caiso-184 ARM C: arm identity, the CONTROL noise floor, and the treated delta.

Pre-registered in ``results/calibration/PRECHECK-caiso184-capacity-basis-2026-08-08.md``
§8 (CONTROL). A thin driver over the **REUSED** ``_caiso180_arm_identity`` legs and
``_caiso183_arm_identity.check_arms_distinct`` — the charter requires reuse, not
re-implementation, and specifically requires the **hourly-signature** distinctness check
(caiso-180's derate-census check is invalid for a delta that does not change the extract).

Two arms, ONE delta, solved sequentially at one head (rule 12), each 2023 + 2024 + 2025
in one bundle (rule 16):

* **C0 CONTROL** — the ``2026-08-08-caiso-183-b1-hour`` keeper recipe replayed at this
  head with no config delta.
* **C1 TREATED** — the same recipe with ``unit_outage_lp_capacity_basis=True``.

**The config-identity leg is INVERTED relative to caiso-180/183 and must be, because
this session's delta IS a config field.** L1/L2 there assert the arms'
``scenario_config`` are identical; here they must differ in **exactly one key**. That
one-key predicate is the stronger statement — it proves no second lever moved — and it
is asserted rather than narrated.

**The CONTROL noise floor is measured at FULL precision, hour by hour**, and is quoted
BEFORE any treated delta is read (charter). caiso-183's correction is inherited: the
same-head control is **NOT** bit-zero — 2023/2024 churn on the **zero-demand** WECC
import nodes (LP alternate optima), which scored precision cannot see.

Usage::

    python scripts/probes/_caiso184_arm_identity.py

Writes ``results/calibration/_caiso184_arm_identity.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes import _caiso180_arm_identity as a180  # noqa: E402
from scripts.probes._caiso183_arm_identity import check_arms_distinct  # noqa: E402

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/caiso183_b1_hourgrain"
ARMS = {
    "B0": REPO / "results/calibration/caiso184_c0_control",
    "B1": REPO / "results/calibration/caiso184_c1_lpbasis",
}
OUT = REPO / "results/calibration/_caiso184_arm_identity.json"

#: The ONE key the treated arm is allowed to differ on.
DELTA_KEY = "unit_outage_lp_capacity_basis"

#: caiso-183's ADOPTED hour-grain CAISO extract. BOTH arms read these exact bytes —
#: this session re-derives nothing, so the sha ladder is an identity, not a ladder.
EXTRACT_SHA = "25360e90a9d11f32c293edf3224047da0d6fab447b551fac81b983e2da1166c6"


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def check_single_key_delta(present: dict[str, Path]) -> dict:
    """Assert the two arms differ in EXACTLY the one pre-registered key.

    Fail-closed in both directions: a second differing key means an unintended
    lever moved, and ZERO differing keys means the treated arm never armed the
    repair (or silently loaded the control's cache).
    """
    if sorted(present) != ["B0", "B1"]:
        return {"skipped": "both arms not present"}
    c0, c1 = _cfg(present["B0"]), _cfg(present["B1"])
    keys = set(c0) | set(c1)
    diff = sorted(k for k in keys if c0.get(k, "<absent>") != c1.get(k, "<absent>"))
    if diff != [DELTA_KEY]:
        raise a180.Failure(
            f"arms differ on {diff!r}; the charter licenses exactly [{DELTA_KEY!r}]"
        )
    return {
        "n_keys_compared": len(keys),
        "differing_keys": diff,
        "control_value": c0.get(DELTA_KEY),
        "treated_value": c1.get(DELTA_KEY),
        "verdict": "PASS — exactly one key, and it is the pre-registered delta",
    }


def _zone_price_frame(bundle: Path, year: int) -> pd.DataFrame | None:
    f = bundle / "hourly" / f"system_{year}.parquet"
    return pd.read_parquet(f) if f.exists() else None


def full_precision_delta(a: Path, b: Path, label: str) -> dict:
    """Hour-by-hour, full-precision zone-price comparison between two bundles.

    Reports the load-weighted level on each side, the raw drift, how many
    zone-hours differ AT ALL (no rounding), and splits the largest deltas by
    whether the zone carries CAISO demand — the caiso-183 correction, which found
    the big same-head deltas sitting entirely on the ZERO-DEMAND WECC import
    nodes, i.e. LP alternate optima rather than a price move.
    """
    out: dict = {"comparison": label, "years": {}}
    for year in YEARS:
        fa, fb = _zone_price_frame(a, year), _zone_price_frame(b, year)
        if fa is None or fb is None:
            continue
        cols = [c for c in ("zone", "hour", "price", "load") if c in fa.columns]
        if "price" not in cols:
            continue
        ka = fa[cols].sort_values([c for c in ("zone", "hour") if c in cols])
        kb = fb[cols].sort_values([c for c in ("zone", "hour") if c in cols])
        pa = pd.to_numeric(ka["price"]).to_numpy()
        pb = pd.to_numeric(kb["price"]).to_numpy()
        if pa.shape != pb.shape:
            out["years"][str(year)] = {"error": "shape mismatch", "a": pa.shape, "b": pb.shape}
            continue
        d = pb - pa
        rec: dict = {
            "zone_hours_total": int(pa.size),
            "zone_hours_differing": int((d != 0.0).sum()),
            "max_abs_delta_any_zone": float(np.abs(d).max()) if d.size else 0.0,
        }
        if "load" in cols:
            la = pd.to_numeric(ka["load"]).to_numpy()
            lw_a = float((pa * la).sum() / la.sum()) if la.sum() else float("nan")
            lw_b = float((pb * la).sum() / la.sum()) if la.sum() else float("nan")
            rec["load_weighted_lambda_a"] = round(lw_a, 10)
            rec["load_weighted_lambda_b"] = round(lw_b, 10)
            rec["drift_usd_per_mwh"] = round(lw_b - lw_a, 10)
            rec["drift_pct_of_level"] = (
                round((lw_b - lw_a) / lw_a, 10) if lw_a else float("nan")
            )
            carrying = la > 0.0
            rec["max_abs_delta_LOAD_CARRYING_zones"] = (
                float(np.abs(d[carrying]).max()) if carrying.any() else 0.0
            )
            rec["zero_load_zone_hours"] = int((~carrying).sum())
        out["years"][str(year)] = rec
    return out


def main() -> None:
    """Run every reused check against this session's arms, then write the record."""
    a180.ARMS = ARMS
    present = {a: b for a, b in ARMS.items() if (b / "run_config.json").exists()}
    if not present:
        sys.exit("no arm bundles found; solve the control first.")

    rec: dict = {
        "session": "caiso-184",
        "precheck": "results/calibration/PRECHECK-caiso184-capacity-basis-2026-08-08.md",
        "reused_instruments": [
            "scripts/probes/_caiso180_arm_identity.py (DOF ledger)",
            "scripts/probes/_caiso183_arm_identity.py (check_arms_distinct, hourly signature)",
        ],
        "delta": (
            f"ScenarioConfig.{DELTA_KEY} False -> True. NO data file changed; "
            f"both arms read campd-unit-outages-CAISO.csv sha256 {EXTRACT_SHA}."
        ),
        "config_identity_note": (
            "The caiso-180/183 config-IDENTITY leg is deliberately NOT run: this "
            "session's delta IS a ScenarioConfig field, so identity would fail by "
            "construction. It is replaced by the STRICTER single-key predicate "
            "below, which additionally proves no second lever moved."
        ),
        "arms_present": sorted(present),
        "partial_audit": sorted(present) != sorted(ARMS),
    }
    rec["single_key_delta"] = check_single_key_delta(present)
    rec["dof_ledger"] = a180.check_dof_ledger(present)
    rec["arm_distinctness"] = check_arms_distinct(present)
    if "B0" in present:
        rec["control_noise_floor"] = full_precision_delta(
            KEEPER, present["B0"], "keeper -> C0 CONTROL (same-head noise floor)"
        )
    if sorted(present) == ["B0", "B1"]:
        rec["treated_delta"] = full_precision_delta(
            present["B0"], present["B1"], "C0 CONTROL -> C1 TREATED"
        )

    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
