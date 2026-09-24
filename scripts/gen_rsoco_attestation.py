"""R-SOCO: write ``calibration_attestation.json`` for the corrected-backcast-input span.

Layered on :mod:`scripts.gen_soco60b_attestation`. That module runs first on this
bundle, so every inherited claim is re-verified by execution: the SOCO-58 postures,
the offer-curve identity, the hydro budgets, the B1 plant boundary and the B2
gas-fold refusal. This module then verifies the lane's input corrections against
the keeper ``2026-09-24-soco61-dark-unit``
(``docs/handoffs/r-soco/PRECOMMIT-r-soco-2026-09-24.md`` §5):

* every F1/F2 field is True in the resolved config. The fields are
  ``eia860_vintage_tracks_solve_year``, ``measured_chp_heat_rates``,
  ``unit_outage_short_windows``, ``unit_outage_short_windows_gas`` and
  ``unit_partial_outage_windows``, plus the keeper's inherited measured /
  dark-unit fields;
* every outage input the run READ (``resolved_inputs``) is hashed, and its
  sha256 is matched against the file on disk;
* every offer-curve override / delta is empty (no price tuning; SOCO has no
  price benchmark).

Usage::

    python3 scripts/build_dof_ledger.py --iso SOCO results/calibration/<bundle>
    python3 scripts/gen_soco60b_attestation.py --bundle results/calibration/<bundle>
    python3 scripts/gen_rsoco_attestation.py --bundle results/calibration/<bundle>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.probes.rsoco_compose_span import LANE_TRUE, STD_EXTRACT  # noqa: E402

#: The lane's new ledger entries: each is a categorical switch onto a measured
#: input, with zero scalars (rules 21/24).
NEW_ENTRIES = {
    "eia860_vintage_tracks_solve_year": "Each solve year reads its own EIA-860 release (vintage_<Y>; canonical where none exists) with its own eGRID-<Y> heat rates. Owner instruction 2026-09-24; F1.",
    "measured_chp_heat_rates": "Power-only CHP heat rate (PLHTIAN + CHPCHTI) / PLNGENAN from the solve year's own eGRID vintage (F1 artifact chp_power_only_heat_rates_SOCO).",
    "unit_outage_short_windows": "CAMPD sub-5-day baseload-coal full stops (campd-unit-outages-short-SOCO.csv) and, riding the same row, unit-grain partial-derate plateaus (campd-partial-outages-SOCO.csv, unit_partial_outage_windows). Frozen deriver, F2 2019-2025 coverage.",
    "unit_outage_short_windows_gas": "CAMPD sub-5-day gas-side full stops under the merit-order guard (campd-unit-outages-shortgas-SOCO.csv). Frozen deriver, F2.",
}


def verify(bundle: Path) -> dict:
    """Raise unless the bundle carries exactly the lane's posture; return evidence."""
    cfg = json.loads((bundle / "run_config.json").read_text())
    sc = cfg["scenario_config"]
    off = [f for f in LANE_TRUE if sc.get(f) is not True]
    if off:
        raise SystemExit(f"not armed: {off}")
    flags = cfg.get("calibration_flags") or {}
    for k in ("offer_curve_overrides", "offer_curve_deltas"):
        if flags.get(k) not in (None, {}):
            raise SystemExit(f"{k} is not empty: {flags.get(k)}")
    ri = cfg.get("resolved_inputs") or {}
    if (ri.get("campd_unit_outages") or {}).get("path") != STD_EXTRACT:
        raise SystemExit(f"std extract is not {STD_EXTRACT}")
    hashes = {}
    for key, rec in sorted(ri.items()):
        if "outage" not in key or not isinstance(rec, dict) or not rec.get("path"):
            continue
        p = _ROOT / rec["path"]
        if not p.exists():
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if rec.get("sha256") and rec["sha256"] != sha:
            raise SystemExit(f"{key}: run read sha {rec['sha256']}, disk {sha}")
        hashes[key] = {"path": rec["path"], "sha256": sha[:16]}
    return {"outage_inputs": hashes}


def main() -> None:
    """Verify the lane posture, then rewrite the governance text and ledger entries."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    a = ap.parse_args()
    bundle = Path(a.bundle)
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text())
    if (
        att.get("schema") != "calibration-attestation/v1"
        or "free_parameters" not in att
    ):
        raise SystemExit("run build_dof_ledger.py and gen_soco60b_attestation.py first")
    ev = verify(bundle)
    print(json.dumps(ev, indent=1))
    inherited = att["governance"]["attested_by"]
    ins = "; ".join(
        f"{k} {v['path']} ({v['sha256']})" for k, v in ev["outage_inputs"].items()
    )
    att["governance"]["attested_by"] = (
        "R-SOCO (lane; audit AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24 §5.3.8). "
        "Against keeper 2026-09-24-soco61-dark-unit, the only changes are the owner-"
        "mandated backcast INPUT corrections. They are machine-verified by execution "
        "in scripts/gen_rsoco_attestation.py: the year-matched EIA-860 vintage (2023 -> "
        "vintage_2023, 2024 -> vintage_2024, 2025 -> canonical) with year-matched eGRID "
        "heat rates (F1); measured power-only CHP heat rates (F1); and the CAMPD "
        "short-coal, short-gas and unit-partial outage families (F2). Outage inputs "
        f"read, sha256-verified against disk: {ins}. RULES 13/14: every input is a "
        "measured physical availability or heat-rate record that regenerates for "
        "any year; nothing measured about dispatch is fed back. RULES 21/24/25: "
        "each is a categorical registered ScenarioConfig switch onto SOCO's own "
        "data, n_scalars 0. RULE 1(c): NO offer-curve band moved; every "
        "offer_curve_by_group band is the keeper's (1.0), and AUTHORIZED PRICE "
        "TUNING IS DECLARED NONE (SOCO has no price benchmark). INHERITED, "
        "re-verified on this bundle by gen_soco60b_attestation.py: " + inherited
    )
    att["disclosures"]["precommit"] = (
        "docs/handoffs/r-soco/PRECOMMIT-r-soco-2026-09-24.md"
    )
    att["disclosures"]["rsoco_scope"] = (
        "2023-2025 only. SOCO has no 2019-2022 EIA-930 / FERC-714 / seam / gas-hub / "
        "solar-shape inputs (the addition plan's manifest row 9 never landed), so "
        "those years cannot be solved; routed as a data-intake lane. Residual "
        "class-table heat rates: Dahlberg (7709) and Hartwell (54538), 1,045 MW CT. "
        "Both file CAMPD under different CAMD facility ids (7765 / 70454), an "
        "EPA-EIA crosswalk defect that is routed, not fixed here."
    )
    fp = att["free_parameters"]
    names = {e["name"] for e in fp["entries"]}
    for name, basis in NEW_ENTRIES.items():
        if name not in names:
            fp["entries"].append(
                {
                    "name": name,
                    "value": True,
                    "identification": "measured-physical",
                    "n_scalars": 0,
                    "basis": basis,
                }
            )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {att_path} (n_entries={fp['n_entries']}, n_residual={fp['n_residual']})"
    )


if __name__ == "__main__":
    main()
