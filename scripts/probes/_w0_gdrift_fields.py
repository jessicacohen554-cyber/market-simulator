"""W0 G-DRIFT (rule 29 (b)), zero LP: which W0 hunk is LIVE in which ISO.

For one keeper bundle and year, rebuild the recipe ``fleet_only`` at the
``recorded`` posture (each W0 field at its recorded value, else its
registration-time default), then once per W0 field with ONLY that field armed,
and hash every LP-visible fleet array plus the assembled P0 ``mc_base``. A
field whose arm moves no hash is INERT in that ISO-year (the measurement is
the reason); one that moves any is LIVE and earns the phase-3 span. The
all-fields ``w0`` posture is hashed too. Writes
``W0-census/<ISO>/gdrift_<Y>.json``.

Usage::

    python scripts/probes/_w0_gdrift_fields.py --bundle results/calibration/miso280_span \\
        --year 2023 --out <json> [--set pjm_da_virtual_bids=false]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for _p in (".", "scripts", "src"):
    sys.path.insert(0, str(REPO / _p))


def _hashes(res: dict) -> dict[str, str]:
    """sha256 (12 hex) of every array-valued FleetArrays field and ``mc_base``."""
    out: dict[str, str] = {}
    for key, value in vars(res["fleet_arrays"]).items():
        try:
            arr = np.ascontiguousarray(np.asarray(value))
        except Exception:
            continue
        if arr.dtype == object:
            arr = np.asarray([str(x) for x in arr.ravel()])
        out[key] = hashlib.sha256(arr.tobytes()).hexdigest()[:12]
    mc = np.ascontiguousarray(np.asarray(res["mc_base"], dtype=float))
    out["mc_base"] = hashlib.sha256(mc.tobytes()).hexdigest()[:12]
    return out


def _build(bundle: Path, year: int, arm: dict, extra: dict) -> dict[str, str]:
    from build_fleet_census import rebuild_fleet

    return _hashes(rebuild_fleet(bundle, year, "recorded", {**arm, **extra}))


def main(argv: list[str] | None = None) -> int:
    """Toggle each W0 field alone against the recorded posture; write the table."""
    from market_sim.config import scenarios as scen

    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--set", action="append", default=[], metavar="FIELD=JSON")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    extra = {k: json.loads(v) for k, v in (s.split("=", 1) for s in args.set)}
    fields = tuple(scen._W0_BACKCAST_DEFAULT_FIELDS)
    base = _build(args.bundle, args.year, {}, extra)
    rows = {}
    for field in fields:
        try:
            moved = _build(args.bundle, args.year, {field: True}, extra)
            diff = sorted(k for k in base if moved.get(k) != base[k])
            rows[field] = {"verdict": "LIVE" if diff else "INERT", "moved": diff}
        except Exception as exc:  # a refusal is itself a finding
            rows[field] = {"verdict": "REFUSED", "error": str(exc)[:300]}
    every = _build(args.bundle, args.year, {f: True for f in fields}, extra)
    out = {
        "bundle": args.bundle.name,
        "year": args.year,
        "overrides": extra,
        "fields": rows,
        "all_w0": {
            "verdict": "LIVE" if every != base else "INERT",
            "moved": sorted(k for k in base if every.get(k) != base[k]),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({f: r["verdict"] for f, r in rows.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
