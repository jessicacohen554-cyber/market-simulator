"""caiso-183 P0-3: snapshot the unit-outage loader's masks for a before/after proof.

The ARM B repair (`PRECHECK-caiso183-hedge-grain-2026-08-08.md` §3b) makes
``market_sim.data.outages`` consume optional ``outage_start_hour`` /
``outage_end_hour`` columns **when present** and fall back to the incumbent
day-granular reconstruction **when absent**. P0-3 requires that the fallback be
**bit-identical** to today's behaviour for every ISO and every solve year.

A bit-identity claim is only worth what its reference is worth, so this script
captures the reference from the **UNMODIFIED** loader, before the repair is
written, and writes a deterministic digest per (ISO, year). The same script run
after the repair — against the same day-granular committed extracts — must
reproduce every digest exactly.

Two consumers are covered, because both carry the ``outage_end + 1 day``
convention the repair replaces:

* :func:`market_sim.data.outages.unit_outage_derate_factors` — the availability
  multipliers the LP actually reads;
* :func:`market_sim.data.outages.unit_outage_active_units` — the window-layer
  unit membership masks.

Usage::

    python scripts/probes/_caiso183_loader_snapshot.py --out <path.json>
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

import numpy as np  # noqa: E402

#: Every ISO whose keeper can read a CAMPD unit-outage extract.
ISOS: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

#: The solve years P0-3 covers. 2023-2025 is the training window every ISO
#: scores on; the wider CAISO span is added separately so the re-derived
#: 2018-2026 extract is exercised over its whole length.
SOLVE_YEARS: tuple[int, ...] = (2023, 2024, 2025)
CAISO_FULL_YEARS: tuple[int, ...] = (2018, 2019, 2020, 2021, 2022, 2026)


def _digest_factor_map(factors: dict[tuple[int, str], np.ndarray]) -> dict:
    """Return a deterministic digest of a ``{(plant, group): (hours,)}`` map.

    Keys are sorted so the digest is insertion-order independent, and each
    array is hashed from its raw ``float64`` bytes — an exact bit-level
    fingerprint, not a rounded summary.
    """
    h = hashlib.sha256()
    keys = sorted(factors, key=lambda k: (int(k[0]), str(k[1])))
    total = 0.0
    for k in keys:
        arr = np.ascontiguousarray(factors[k], dtype=np.float64)
        h.update(f"{int(k[0])}|{k[1]}|".encode())
        h.update(arr.tobytes())
        total += float((1.0 - arr).sum())
    return {
        "n_keys": len(keys),
        "derate_mw_hours_unweighted": round(total, 6),
        "sha256": h.hexdigest(),
    }


def _digest_unit_map(units: dict[tuple[int, str], dict[str, np.ndarray]]) -> dict:
    """Return a deterministic digest of the ``unit_outage_active_units`` map."""
    h = hashlib.sha256()
    n_units = 0
    true_hours = 0
    for k in sorted(units, key=lambda k: (int(k[0]), str(k[1]))):
        for uid in sorted(units[k]):
            arr = np.ascontiguousarray(units[k][uid], dtype=bool)
            h.update(f"{int(k[0])}|{k[1]}|{uid}|".encode())
            h.update(arr.tobytes())
            n_units += 1
            true_hours += int(arr.sum())
    return {"n_units": n_units, "true_hours": true_hours, "sha256": h.hexdigest()}


def snapshot() -> dict:
    """Return the loader digest for every (ISO, year) P0-3 covers."""
    from market_sim.data import outages as ox

    out: dict[str, dict[str, dict]] = {}
    for iso in ISOS:
        years = list(SOLVE_YEARS)
        if iso == "CAISO":
            years = sorted({*SOLVE_YEARS, *CAISO_FULL_YEARS})
        per_year: dict[str, dict] = {}
        for year in years:
            # lru_cache is keyed on the arguments, not on the file contents, so
            # a snapshot taken across an on-disk change must clear it first.
            ox.unit_outage_derate_factors.cache_clear()
            ox.unit_outage_active_units.cache_clear()
            factors = ox.unit_outage_derate_factors(year, iso=iso)
            units = ox.unit_outage_active_units(year, iso=iso)
            per_year[str(year)] = {
                "derate_factors": _digest_factor_map(factors),
                "active_units": _digest_unit_map(units),
            }
        out[iso] = per_year
    return out


def main() -> None:
    """Write the loader snapshot, or diff against a previously written one."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="Destination JSON path.")
    ap.add_argument(
        "--compare",
        default=None,
        help="Existing snapshot JSON to diff against; exits non-zero on any "
        "digest mismatch (the P0-3 bit-identity assertion).",
    )
    args = ap.parse_args()

    snap = snapshot()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(snap, indent=1, sort_keys=True))
    print(f"wrote loader snapshot -> {args.out}")

    if args.compare:
        ref = json.loads(Path(args.compare).read_text())
        bad: list[str] = []
        for iso, years in ref.items():
            for year, ent in years.items():
                got = snap.get(iso, {}).get(year)
                if got is None:
                    bad.append(f"{iso} {year}: missing from new snapshot")
                    continue
                for leg in ("derate_factors", "active_units"):
                    if got[leg]["sha256"] != ent[leg]["sha256"]:
                        bad.append(
                            f"{iso} {year} {leg}: {ent[leg]['sha256'][:12]} -> "
                            f"{got[leg]['sha256'][:12]}"
                        )
        if bad:
            print("\nP0-3 FAIL — loader fallback is NOT bit-identical:")
            for b in bad:
                print(f"  {b}")
            raise SystemExit(1)
        n = sum(len(v) for v in ref.values())
        print(f"P0-3 PASS — all {n} (ISO, year) digests bit-identical, both legs")


if __name__ == "__main__":
    main()
