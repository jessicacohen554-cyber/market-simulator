"""caiso-183 ARM B: the byte-equivalence, detection-identity and envelope legs.

Pre-registered in ``results/calibration/PRECHECK-caiso183-hedge-grain-2026-08-08.md``.
This instrument measures the Phase-0 obligations of the H-EDGE derive-**grain**
repair and refuses to write its record unless the fail-closed legs hold, so a
finding can never be assembled on a change that silently reached another ISO or
the detector.

Legs, in the order the PRECHECK fixes them:

* **BE-1** (§4) — the UNMODIFIED deriver at this head reproduces every committed
  extract. Reported for all six ISOs. MISO's mismatch is a **known pre-existing**
  condition disclosed in PRECHECK §4a (`FINDING-xiso2-…-2026-08-02` §4: a strict
  superset, +17 windows / 0 lost, all 2022 COAL, layup companion byte-identical)
  and is therefore reported, not treated as this session's defect.
* **BE-2** (§4, §4a) — with the hour-grain code present but the flag ABSENT, each
  ISO's extract is sha256-identical to **its own BE-1 output**. That
  self-comparison is the only one that isolates this change, and it is the
  binding form of gate **G-SIXISO**. The committed-file comparison is reported
  alongside.
* **BE-3** (§4) — for CAISO, DETECTION is unchanged: the hour-grain extract's
  base-column projection is identical to the day-grain extract, row for row, in
  the same order.
* **G-NOFIT** (§6) — the frozen detector constants are imported and diffed
  against their pre-registered committed values; no threshold may be re-valued.
* **G-DEPTH / G-DEPTH′** (§6a) — envelope depth (outage MW-hours per year, the
  caiso-180 ``envelope_depth`` definition) of the day-grain and hour-grain
  envelopes, scored against BOTH pre-registered readings.

Usage::

    python scripts/probes/_caiso183_hedge_grain.py \
        --be1-dir <dir> --be2-dir <dir> --treated <caiso hour-grain csv> \
        --out results/calibration/_caiso183_hedge_grain.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

RAW = REPO / "data/raw"
YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: Matrix column order; ERCOT's extract is the unsuffixed file.
ISOS: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

#: PRECHECK §3a. The two optional grain columns, in emission order.
HOUR_COLUMNS: tuple[str, str] = ("outage_start_hour", "outage_end_hour")

#: PRECHECK §6, gate G-NOFIT. The frozen identification constants and the values
#: they carry at this head's committed state (rule 23 `[R-FROZEN-DERIVE]`); a
#: move here is a re-valued threshold, which this session may not make.
FROZEN_CONSTANTS: dict[str, float] = {
    "_MIN_DAYS": 5.0,
    "_SMOOTH_DAYS": 7,
    "_CEILING_FRAC": 0.65,
    "_RUN_FLOOR_CF": 0.06,
    "_BASELOAD_CF": 0.55,
    "ST_GAS_CF_PEAK": 0.02,
}

#: PRECHECK §6a. caiso-180's committed envelope depths, M MW-h.
#: A0 = the committed (GUARD) envelope this session repairs; A1 = the superseded
#: PRE envelope that supplies the literal G-DEPTH floor.
A0_DEPTH_MWH: dict[int, float] = {2023: 36_679_915.2, 2024: 42_880_322.4, 2025: 55_429_857.6}
A1_DEPTH_MWH: dict[int, float] = {2023: 38_025_422.4, 2024: 38_803_483.2, 2025: 49_987_807.2}


class Failure(RuntimeError):
    """A pre-registered fail-closed leg did not hold; the record is not written."""


def extract_name(iso: str) -> str:
    """Return the standard extract filename for ``iso``."""
    return "campd-unit-outages.csv" if iso == "ERCOT" else f"campd-unit-outages-{iso}.csv"


def sha256_file(path: Path) -> str:
    """Return the sha256 of a file's exact bytes."""
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def be_ledger(be1_dir: Path, be2_dir: Path) -> dict:
    """BE-1 + BE-2: committed vs unmodified vs hour-grain-code-present bytes.

    ``be2_dir`` holds the extracts produced with the hour-grain code in the
    tree but **without** ``--hour-grain``, which is the state every non-CAISO
    ISO stays in. G-SIXISO binds on the ``be2 == be1`` self-comparison; the
    committed comparison is reported for completeness and carries MISO's
    disclosed pre-existing delta.
    """
    out: dict[str, dict] = {}
    for iso in ISOS:
        name = extract_name(iso)
        committed, b1, b2 = RAW / name, be1_dir / name, be2_dir / name
        for p in (committed, b1, b2):
            if not p.exists():
                raise Failure(f"{iso}: missing extract for the BE ledger — {p}")
        s_c, s_1, s_2 = sha256_file(committed), sha256_file(b1), sha256_file(b2)
        out[iso] = {
            "committed_sha": s_c,
            "be1_sha": s_1,
            "be2_sha": s_2,
            "be1_reproduces_committed": s_1 == s_c,
            "be2_identical_to_be1": s_2 == s_1,
            "be2_identical_to_committed": s_2 == s_c,
        }
    # G-SIXISO, the binding form: the code change moves no byte anywhere.
    moved = [i for i in ISOS if not out[i]["be2_identical_to_be1"]]
    if moved:
        raise Failure(
            f"G-SIXISO FAIL — the hour-grain code changed these ISOs' default "
            f"extracts: {moved}. The change is not byte-inert and the arm fails "
            f"(PRECHECK §4a)."
        )
    out["_gate_G_SIXISO"] = {
        "statement": "every ISO's flag-absent extract is sha256-identical to its own BE-1 output",
        "verdict": "PASS",
    }
    known = [i for i in ISOS if not out[i]["be1_reproduces_committed"]]
    out["_be1_committed_mismatches"] = known
    out["_be1_note"] = (
        "PRECHECK §4a disclosed MISO's BE-1 mismatch in advance (xiso-2 §4: strict "
        "superset, +17 windows / 0 lost, all 2022 COAL, layup companion "
        "byte-identical; root cause commit 5cd937407 filling the MISO EIA-930 2022 "
        "hole). It is a property of the committed MISO blob, not of this change — "
        "which is why G-SIXISO binds on the self-comparison above."
    )
    return out


def be3_detection_identity(day_csv: Path, hour_csv: Path) -> dict:
    """BE-3: CAISO detection is unchanged; only the expressed grain differs.

    Asserts the hour-grain extract's base-column projection is identical to the
    day-grain extract — same row count, same values, **same order** — so no
    window was added, dropped, moved or re-dated. A failure means the change
    reached the detector, i.e. the settled caiso-181 depth object, and the arm
    stops (PRECHECK §2, §8 stop condition 2).
    """
    day = pd.read_csv(day_csv)
    hour = pd.read_csv(hour_csv)
    missing = [c for c in HOUR_COLUMNS if c not in hour.columns]
    if missing:
        raise Failure(f"BE-3: the hour-grain extract is missing {missing}")
    if list(day.columns) != [c for c in hour.columns if c not in HOUR_COLUMNS]:
        raise Failure(
            f"BE-3 FAIL — base column set/order changed: {list(day.columns)} vs "
            f"{[c for c in hour.columns if c not in HOUR_COLUMNS]}"
        )
    proj = hour[list(day.columns)]
    if len(proj) != len(day):
        raise Failure(f"BE-3 FAIL — row count {len(proj)} vs {len(day)}")
    if not proj.reset_index(drop=True).equals(day.reset_index(drop=True)):
        diff = (proj.reset_index(drop=True) != day.reset_index(drop=True)).sum()
        raise Failure(f"BE-3 FAIL — base columns differ: {diff[diff > 0].to_dict()}")

    tuples_day = list(zip(day.facility_id, day.unit_id, day.outage_start, day.outage_end))
    tuples_hour = list(
        zip(hour.facility_id, hour.unit_id, hour.outage_start, hour.outage_end)
    )
    if tuples_day != tuples_hour:
        raise Failure("BE-3 FAIL — (plant, unit, start-day, end-day) tuples/order moved")

    h0, h1 = hour[HOUR_COLUMNS[0]], hour[HOUR_COLUMNS[1]]
    if not ((h0 >= 0) & (h0 <= 23) & (h1 >= 0) & (h1 <= 23)).all():
        raise Failure("BE-3 FAIL — an emitted hour lies outside [0, 23]")
    return {
        "rows": int(len(day)),
        "base_columns_identical": True,
        "row_order_identical": True,
        "hours_in_range": True,
        "windows_by_year": {
            str(y): int((pd.to_datetime(day.outage_start).dt.year == y).sum())
            for y in YEARS
        },
        "start_hour_nonzero_share": round(float((h0 != 0).mean()), 4),
        "end_hour_not_23_share": round(float((h1 != 23).mean()), 4),
        "verdict": "PASS",
    }


def check_frozen_constants() -> dict:
    """G-NOFIT: the frozen detector constants are unmoved (rule 23)."""
    from scripts.lib import outage_detect as od

    got: dict[str, object] = {}
    moved: list[str] = []
    for name, expect in FROZEN_CONSTANTS.items():
        if not hasattr(od, name):
            # The plateau constants live in the partial-outage deriver.
            from scripts.data import derive_partial_outages as dpo

            val = getattr(dpo, name, None)
        else:
            val = getattr(od, name)
        got[name] = val
        if val is None or float(val) != float(expect):
            moved.append(f"{name}: {val} != {expect}")
    if moved:
        raise Failure(f"G-NOFIT FAIL — frozen constants re-valued: {moved}")
    return {"values": {k: float(v) for k, v in got.items()}, "verdict": "PASS"}


def envelope_depth(csv: Path) -> dict[int, dict]:
    """Return per-year envelope depth for one extract, caiso-180's definition.

    Outage MW-hours = Σ (window hours clipped to the year) × ``unit_capacity_mw``.
    When the extract carries the optional hour columns the window is the
    DETECTED one, ``[start + h0, end + h1 + 1h)``; otherwise it is the incumbent
    day-granular reconstruction ``[start, end + 1 day)`` — the same loader
    convention, so the two depths are directly comparable.
    """
    d = pd.read_csv(csv)
    s = pd.to_datetime(d.outage_start)
    e = pd.to_datetime(d.outage_end)
    if all(c in d.columns for c in HOUR_COLUMNS):
        s = s + pd.to_timedelta(d[HOUR_COLUMNS[0]].fillna(0).astype(int), unit="h")
        e = e + pd.to_timedelta(d[HOUR_COLUMNS[1]].fillna(23).astype(int) + 1, unit="h")
    else:
        e = e + pd.Timedelta(days=1)
    out: dict[int, dict] = {}
    for y in YEARS:
        y0, y1 = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")
        lo, hi = s.clip(lower=y0), e.clip(upper=y1)
        hrs = ((hi - lo).dt.total_seconds() / 3600).clip(lower=0)
        m = hrs > 0
        out[y] = {
            "windows": int(m.sum()),
            "outage_mw_hours": round(float((hrs[m] * d.unit_capacity_mw[m]).sum()), 1),
        }
    return out


def depth_gates(day_csv: Path, hour_csv: Path) -> dict:
    """G-DEPTH (literal) and G-DEPTH′ (delta form), both as pre-registered §6a."""
    day = envelope_depth(day_csv)
    hour = envelope_depth(hour_csv)
    rows: dict[str, dict] = {}
    literal_fail, delta_fail = [], []
    for y in YEARS:
        removed = day[y]["outage_mw_hours"] - hour[y]["outage_mw_hours"]
        allowed = abs(A0_DEPTH_MWH[y] - A1_DEPTH_MWH[y])
        lit_ok = hour[y]["outage_mw_hours"] >= A1_DEPTH_MWH[y]
        baseline_lit_ok = day[y]["outage_mw_hours"] >= A1_DEPTH_MWH[y]
        rows[str(y)] = {
            "day_grain_depth_mwh": day[y]["outage_mw_hours"],
            "hour_grain_depth_mwh": hour[y]["outage_mw_hours"],
            "removed_mwh": round(removed, 1),
            "removed_share_of_day_depth": round(
                removed / day[y]["outage_mw_hours"], 6
            )
            if day[y]["outage_mw_hours"]
            else 0.0,
            "G_DEPTH_literal_floor_mwh": A1_DEPTH_MWH[y],
            "G_DEPTH_literal_pass": bool(lit_ok),
            "G_DEPTH_literal_baseline_pass": bool(baseline_lit_ok),
            "G_DEPTH_prime_allowance_mwh": round(allowed, 1),
            "G_DEPTH_prime_pass": bool(removed <= allowed),
        }
        if not lit_ok:
            literal_fail.append(y)
        if removed > allowed:
            delta_fail.append(y)
    return {
        "per_year": rows,
        "G_DEPTH_prime_verdict": "FAIL" if delta_fail else "PASS",
        "G_DEPTH_prime_years_failed": [str(y) for y in delta_fail],
        "G_DEPTH_literal_verdict": "FAIL" if literal_fail else "PASS",
        "G_DEPTH_literal_years_below_floor": [str(y) for y in literal_fail],
        "note": (
            "PRECHECK §6a pre-registered BOTH readings before measurement, because "
            "the literal floor's 2023 leg is already breached by the UNREPAIRED "
            "baseline (A0 36.68 M < A1 38.03 M): the regeneration REMOVED depth "
            "that year, so the gate's premise does not hold there. G-DEPTH′ is the "
            "binding form and is well-defined in all three years."
        ),
    }


def main() -> None:
    """Run every Phase-0 leg and write the pre-registered record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--be1-dir", required=True, help="Unmodified-deriver outputs.")
    ap.add_argument("--be2-dir", required=True, help="Hour-grain code, flag ABSENT.")
    ap.add_argument("--treated", required=True, help="CAISO --hour-grain extract.")
    ap.add_argument("--out", required=True, help="Destination JSON.")
    args = ap.parse_args()

    be1_dir, be2_dir = Path(args.be1_dir), Path(args.be2_dir)
    treated = Path(args.treated)
    day_caiso = be1_dir / extract_name("CAISO")

    record = {
        "session": "caiso-183",
        "precheck": "results/calibration/PRECHECK-caiso183-hedge-grain-2026-08-08.md",
        "recipe": "--years 2018 … 2026 --merit-order-guard",
        "be_ledger": be_ledger(be1_dir, be2_dir),
        "be3_detection_identity": be3_detection_identity(day_caiso, treated),
        "G_NOFIT": check_frozen_constants(),
        "depth": depth_gates(day_caiso, treated),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(record, indent=1, sort_keys=False))
    print(f"wrote {args.out}")
    # G-DEPTH is reported, not stop-the-line: the evidence is written FIRST and
    # the non-zero exit carries the refusal, so a failed gate can never be lost
    # by the instrument dying before it records why. (The raise-before-write form
    # was replaced AFTER the 2023 leg fired, and moved no bar — the allowance,
    # the floor and the verdict are exactly as pre-registered.)
    failed = record["depth"]["G_DEPTH_prime_years_failed"]
    for iso in ISOS:
        e = record["be_ledger"][iso]
        print(
            f"  {iso:>6}  BE-1 vs committed {'OK ' if e['be1_reproduces_committed'] else 'DIFF'}"
            f"   BE-2 vs BE-1 {'OK' if e['be2_identical_to_be1'] else 'DIFF'}"
        )
    for y, r in record["depth"]["per_year"].items():
        print(
            f"  {y}: depth {r['day_grain_depth_mwh'] / 1e6:.2f}M -> "
            f"{r['hour_grain_depth_mwh'] / 1e6:.2f}M  (removed "
            f"{r['removed_mwh'] / 1e6:.3f}M = {r['removed_share_of_day_depth']:.2%}, "
            f"G-DEPTH′ allowance {r['G_DEPTH_prime_allowance_mwh'] / 1e6:.2f}M)"
        )
    if failed:
        raise SystemExit(
            f"\nG-DEPTH′ FAIL in {failed} — the repair removes more depth than "
            f"the regeneration added that year (PRECHECK §6a). Reported at full "
            f"magnitude; the bar is NOT moved."
        )


if __name__ == "__main__":
    main()
