"""Close-out CAISO w2, G-DRIFT (ZERO LP): fingerprint the keeper recipe's solve inputs at the checked-out SHA.

Rule 29(b): the incumbent keeper's legs were solved at ``566bc8fa``; the arm
shards solve at a later main. This rebuilds the keeper recipe
(``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` +
``run_year(fleet_only=True)``, the sanctioned zero-LP rebuild) for each year and
hashes every array the fleet-only exit returns — per-unit pmax / availability /
mc (P0 objective, every pricing overlay applied), demand, renewable CF and
capacity, wind/solar offers, storage power caps — so the SAME script run in a
worktree at each SHA yields a per-component INERT / LIVE verdict.
``--set KEY=JSON`` applies a ScenarioConfig override (the arm).

Usage (run from the repo root of the SHA under test)::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w2_gdrift_fingerprint.py \
        --bundle /abs/path/results/calibration/closeout_caiso_w1_a2_span --years 2019 ... --out fp.json
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [".", "src", "scripts"]


def _h(x) -> str | None:
    """Stable hash of an array-like (rounded to 1e-9 to ignore float noise)."""
    if x is None:
        return None
    if isinstance(x, dict):
        return hashlib.sha256(
            json.dumps(
                {str(k): _h(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
            ).encode()
        ).hexdigest()[:16]
    a = np.asarray(x)
    if a.dtype.kind in "fc":
        a = np.round(a.astype(float), 9)
    elif a.dtype.kind == "O":
        return hashlib.sha256(repr(a.tolist()).encode()).hexdigest()[:16]
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:16]


def fingerprint(bundle: Path, year: int, overrides: dict) -> dict:
    """Fleet-only rebuild of the keeper recipe for ``year`` and per-component hashes."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if overrides:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"].update(overrides)
    r = run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )
    fa = r["fleet_arrays"]
    order = np.argsort(np.asarray(fa.unit_ids, dtype=object).astype(str))
    ids = list(np.asarray(fa.unit_ids, dtype=object).astype(str)[order])
    out = {
        "n_units": len(ids),
        "unit_ids": _h(np.array(ids, dtype=object)),
        "pmax": _h(np.asarray(fa.pmax)[order]),
        "availability": _h(np.asarray(fa.availability)[order]),
        "mc_base": _h(
            np.asarray(r["mc_base"])[order] if np.ndim(r["mc_base"]) else r["mc_base"]
        ),
        "demand": _h(r["demand"]),
        "wind_cf": _h(r["wind_cf"]),
        "wind_cap": _h(r["wind_cap"]),
        "solar_cf": _h(r["solar_cf"]),
        "solar_cap": _h(r["solar_cap"]),
        "wind_mc": _h(r["wind_mc"]),
        "solar_mc": _h(r["solar_mc"]),
        "storage_power_cap": _h(r["storage_power_cap"]),
        "zones": list(getattr(r["iso_config"], "zone_names", []) or []),
    }
    # per-unit energy capability and mean mc, to localise any LIVE difference
    cap = np.asarray(fa.pmax)[:, None] * np.asarray(fa.availability)
    mc = np.asarray(r["mc_base"])
    out["unit_cap_twh"] = {
        u: round(float(cap[i].sum() / 1e6), 6) for u, i in zip(ids, order)
    }
    if mc.ndim == 2:
        out["unit_mc_mean"] = {
            u: round(float(mc[i].mean()), 6) for u, i in zip(ids, order)
        }
    out["demand_twh"] = round(float(np.asarray(r["demand"]).sum() / 1e6), 6)
    return out


def main() -> None:
    """Fingerprint every requested year and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--set", dest="sets", action="append", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ov = {k: json.loads(v) for k, v in (s.split("=", 1) for s in a.sets)}
    res = {}
    for y in a.years:
        res[str(y)] = fingerprint(Path(a.bundle), y, ov)
        print(
            y,
            {k: v for k, v in res[str(y)].items() if not k.startswith("unit_")},
            flush=True,
        )
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
