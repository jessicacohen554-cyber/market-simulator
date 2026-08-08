"""caiso-184 P0-3 — byte-equivalence proof for the LP-capacity-basis denominator repair.

Pre-registered in ``results/calibration/PRECHECK-caiso184-capacity-basis-2026-08-08.md``
§6 (pushed and blob-verified, sha256 ``33fa2093...``, BEFORE the repair was written).
Discipline inherited verbatim from ``FINDING-ercot174`` §1 (BE-1/BE-2/BE-3).

* **BE-1** — with the change present and the gate **ABSENT**, ``_iso_plant_capacity``
  returns a map identical to the incumbent for **all six ISOs**. The incumbent is
  recomputed here from the same fleet by the same arithmetic, so the comparison needs no
  snapshot file and cannot rot.
* **BE-2 / G-SIXISO** — the gate is a ``ScenarioConfig`` field read per run, so an ISO
  moves only if **its own** config arms it. Two legs: (a) every ISO's flag-ABSENT map is
  identical to its flag-explicitly-False map, i.e. the ``lru_cache`` key extension cannot
  leak an armed map into an unarmed caller; (b) armed, **zero non-CC bins move in any
  ISO** — the repair's reach is exactly the groups ``fleet_to_bins`` raises. NOTE: the
  armed CC bins DO move, by construction; an earlier form of this leg compared the armed
  map to the unarmed one for the non-CAISO ISOs, which is not a byte-equivalence
  statement at all (it would only pass if the repair did nothing), and it is restated
  here rather than re-scored.
* **BE-1 REFERENCE** — the pre-change digests below were measured on the ACTUAL
  pre-change tree (``git stash`` of the three touched sources, digest, ``git stash pop``),
  not reconstructed. All six ISOs are byte-identical post-change with the gate absent.

* **BE-3** — **no data file is re-derived or rewritten.** sha256 ledger over every
  committed ``campd-unit-outages-*.csv``.
* **G-MONO** — armed, no bin's denominator may FALL (nameplate >= net summer), so no
  removed fraction can rise.
* **G-BASIS corroboration** — armed, the raised denominator is compared to the extract's
  OWN ``plant_capacity_mw`` (which the deriver builds from the same ``derate_mw``
  capacities as the numerator), over single-plant_group facilities.

Usage::

    python scripts/probes/_caiso184_be_proof.py

Writes ``results/calibration/_caiso184_be_proof.json``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _generic_unit_outage_target,
    _iso_plant_capacity,
    unit_outage_csv_for_iso,
)

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

# BE-1 reference: `_iso_plant_capacity(iso)` digests measured on the PRE-CHANGE tree
# (the three touched sources stashed), so this leg compares against the real incumbent
# rather than against a reconstruction of it.
PRE_CHANGE_DIGESTS: dict[str, str] = {
    "ERCOT": "aeff7dc961bc2c3aae223df1657bf5a3dd679427507be0d1cc9b342dd6bbd227",
    "CAISO": "44334bee8a321664985f8dff67a5b801cf3dc17ea4fa97b9bb30a1e8b8f03fd3",
    "PJM": "6d15643f68d6607ddf2a9b8864e68b79febe9158f20c37fb3b4032d088831523",
    "MISO": "23bcdfe2ba184b9ee6a4ce5d0c96950e01510290f626097245bc3944b3362ae5",
    "NYISO": "ad789486acfa7efbb3ff882452e7364924569f06532e53bd6c111d4911d0f7f0",
    "NEISO": "543dbf14b0a20304652b17a97550b5aff798a4fb3dfe6eb38fd4efe300741624",
}
OUT = REPO / "results" / "calibration" / "_caiso184_be_proof.json"
_CC_GROUPS = ("CC_REGULAR", "CC_CHP")


def _digest(cap: dict) -> str:
    """Stable sha256 over a ``{(plant, group): MW}`` map at full precision."""
    payload = "\n".join(
        f"{k[0]}|{k[1]}|{v!r}" for k, v in sorted(cap.items(), key=lambda x: (x[0][0], x[0][1]))
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def main() -> None:
    out: dict = {
        "precheck_sha256": (
            "33fa2093a8a253982f816a56c420515d4a5ddebbcf2ad1432974a15ccbce9a23"
        ),
        "be1_gate_absent": {},
        "be2_gate_armed": {},
        "be3_extract_sha256": {},
        "g_mono": {},
        "g_basis_corroboration": {},
    }

    for iso in ISOS:
        off = _iso_plant_capacity(iso)
        off_explicit = _iso_plant_capacity(iso, False, False)
        on = _iso_plant_capacity(iso, False, True)
        out["be1_gate_absent"][iso] = {
            "n_bins": len(off),
            "digest": _digest(off),
            "identical_to_explicit_false": _digest(off) == _digest(off_explicit),
            "identical_to_pre_change_tree": _digest(off) == PRE_CHANGE_DIGESTS[iso],
        }
        moved = {k: (off[k], on[k]) for k in off if abs(on[k] - off[k]) > 1e-9}
        out["be2_gate_armed"][iso] = {
            "digest": _digest(on),
            "n_bins_moved": len(moved),
            "n_bins_moved_non_cc": sum(1 for k in moved if k[1] not in _CC_GROUPS),
        }
        out["g_mono"][iso] = {
            "n_bins_denominator_fell": sum(
                1 for k in off if on[k] < off[k] - 1e-9
            ),
        }

    for path in sorted((RAW_DATA_DIR).glob("campd-unit-outages*.csv")):
        out["be3_extract_sha256"][path.name] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

    # G-BASIS corroboration, CAISO only (rule 25): the armed denominator against
    # the extract's own same-basis plant capacity, over single-group facilities.
    off = _iso_plant_capacity("CAISO")
    on = _iso_plant_capacity("CAISO", False, True)
    df = pd.read_csv(unit_outage_csv_for_iso("CAISO"))
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    gpf = df.groupby("facility_id")["plant_group"].nunique()
    single = set(gpf[gpf == 1].index)
    rows = []
    seen = set()
    for r in df.itertuples(index=False):
        tgt = _generic_unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if (
            tgt is None
            or tgt in seen
            or tgt[1] not in _CC_GROUPS
            or int(r.facility_id) not in single
            or tgt not in off
        ):
            continue
        seen.add(tgt)
        ext = float(r.plant_capacity_mw)
        if ext <= 0:
            continue
        rows.append(
            {
                "plant_code": tgt[0],
                "plant_group": tgt[1],
                "capacity_source": str(r.capacity_source),
                "extract_plant_capacity_mw": ext,
                "denominator_off": round(off[tgt], 3),
                "denominator_on": round(on[tgt], 3),
                "ratio_ext_over_off": round(ext / off[tgt], 4),
                "ratio_ext_over_on": round(ext / on[tgt], 4),
            }
        )
    eia_rows = [r for r in rows if r["capacity_source"].startswith("eia_")]
    out["g_basis_corroboration"] = {
        "n_bins": len(rows),
        "median_ratio_ext_over_off": round(
            float(pd.Series([r["ratio_ext_over_off"] for r in rows]).median()), 4
        ),
        "median_ratio_ext_over_on": round(
            float(pd.Series([r["ratio_ext_over_on"] for r in rows]).median()), 4
        ),
        "n_eia_sourced_bins": len(eia_rows),
        "n_eia_sourced_bins_ratio_exactly_1": sum(
            1 for r in eia_rows if abs(r["ratio_ext_over_on"] - 1.0) < 5e-4
        ),
        "rows": rows,
    }

    verdicts = {
        "BE_1": (
            "PASS"
            if all(
                v["identical_to_explicit_false"] and v["identical_to_pre_change_tree"]
                for v in out["be1_gate_absent"].values()
            )
            else "FAIL"
        ),
        "BE_2_G_SIXISO": (
            "PASS"
            if all(
                out["be1_gate_absent"][i]["identical_to_pre_change_tree"]
                for i in ISOS
                if i != "CAISO"
            )
            and all(
                out["be2_gate_armed"][i]["n_bins_moved_non_cc"] == 0 for i in ISOS
            )
            else "FAIL"
        ),
        "G_MONO": (
            "PASS"
            if all(v["n_bins_denominator_fell"] == 0 for v in out["g_mono"].values())
            else "FAIL"
        ),
        "non_cc_bins_moved_anywhere": sum(
            v["n_bins_moved_non_cc"] for v in out["be2_gate_armed"].values()
        ),
    }
    out["verdicts"] = verdicts
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(verdicts, indent=2))
    for iso in ISOS:
        b = out["be2_gate_armed"][iso]
        print(f"{iso:7} armed: bins moved = {b['n_bins_moved']:4d} (non-CC {b['n_bins_moved_non_cc']})")
    g = out["g_basis_corroboration"]
    print(
        f"\nG-BASIS: median extract/denominator  OFF={g['median_ratio_ext_over_off']}  "
        f"ON={g['median_ratio_ext_over_on']}  "
        f"({g['n_eia_sourced_bins_ratio_exactly_1']}/{g['n_eia_sourced_bins']} "
        "EIA-sourced bins at exactly 1.000)"
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
