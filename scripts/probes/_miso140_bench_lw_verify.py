"""miso-140 G-1/G-2: verify the refreshed MISO load-weighted actual comparator.

Re-runs the exact ``derive_actual_lmp._lw_fields`` path that produces the
``rt_lw``/``da_lw``/``*_lw_mon`` scoring comparator, and adjudicates the two
questions the miso-140 PREREG left open after pjm-160 B5 performed the
mechanical refresh:

* **G-1** — does the refreshed reference (``actual_lmp.json``) *reproduce* from
  the committed hourly parquet x today's ``eia_loader.load_demand``? This is the
  miso-137 G-0(i) test re-run against the NEW values.
* **G-2** — did the propagation into the committed bench parts
  (``frontend/data/backcast/bench/MISO/<year>.json.gz``) carry every ``*_lw``
  cell faithfully, and did it change NOTHING ELSE (the PREREG S3 blast-radius
  stop rule)?

Reads committed artifacts only. Solves nothing, writes nothing outside its own
JSON record. Training window 2023-2025 (rule 22).
"""

from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

YEARS = (2023, 2024, 2025)
ISO = "MISO"
BASES = ("rt", "da")
# The commit that performed the pjm-160 B5 propagation into the MISO bench
# parts; its parent is the pre-refresh state used for the confinement check.
REFRESH_COMMIT = "056eb164"
RECORD = REPO / "results" / "calibration" / "_miso140_bench_lw_verify.json"


def _bench_avglmp(year: int, ref: str | None = None) -> dict:
    """``avgLMP`` block of a committed MISO bench part, at HEAD or at ``ref``."""
    rel = f"frontend/data/backcast/bench/{ISO}/{year}.json.gz"
    if ref is None:
        raw = (REPO / rel).read_bytes()
    else:
        raw = subprocess.run(
            ["git", "show", f"{ref}:{rel}"],
            cwd=REPO,
            capture_output=True,
            check=True,
        ).stdout
    return json.loads(gzip.decompress(raw))["bench"]["avgLMP"]


def _bench_full(year: int, ref: str | None = None) -> dict:
    rel = f"frontend/data/backcast/bench/{ISO}/{year}.json.gz"
    if ref is None:
        raw = (REPO / rel).read_bytes()
    else:
        raw = subprocess.run(
            ["git", "show", f"{ref}:{rel}"],
            cwd=REPO,
            capture_output=True,
            check=True,
        ).stdout
    return json.loads(gzip.decompress(raw))


def _flatten(obj, prefix: str = "") -> dict:
    """Leaf-path -> scalar, for a whole-artifact structural comparison."""
    out: dict = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def _unrounded_rt_lw(year: int) -> float:
    """The 2025-RT fourth-decimal check the PREREG names (45.4555 +- 0.0005).

    Mirrors ``_lw_stats`` without its ``round(., 2)`` so the recompute can be
    compared to miso-137's published unrounded value.
    """
    import numpy as np
    import pandas as pd

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config import paths
    from market_sim.data.eia_loader import load_demand

    h = pd.read_parquet(paths.CALIBRATION_DIR / f"actual_lmp_hourly_{ISO}.parquet")
    h = h[h["year"] == int(year)].sort_values("hour")
    w = load_demand(ISO, int(year), get_iso_config(ISO)).sum(axis=0)
    out = {}
    for kind in BASES:
        dense = np.full(8760, np.nan)
        hr = h["hour"].to_numpy(int)
        ok = hr < 8760
        dense[hr[ok]] = h[kind].to_numpy(float)[ok]
        v = ~np.isnan(dense) & (w > 0)
        out[kind] = float((dense[v] * w[v]).sum() / w[v].sum())
    return out


def main() -> None:
    from scripts.data import derive_actual_lmp as dal

    rec: dict = {"iso": ISO, "years": list(YEARS), "g1": {}, "g2": {}, "gates": {}}

    committed_ref = json.loads((dal.OUT).read_text())[ISO]

    # ---- G-1: the reference reproduces from today's inputs -----------------
    g1_cells = g1_bad = 0
    for y in YEARS:
        fresh = dal._lw_fields(ISO, y)
        assert fresh is not None, f"{ISO} {y}: deriver returned no lw fields"
        comm = committed_ref[str(y)]
        row: dict = {"annual": {}, "monthly_mismatches": [], "unrounded": {}}
        for kind in BASES:
            k = f"{kind}_lw"
            row["annual"][k] = {
                "fresh": fresh.get(k),
                "committed": comm.get(k),
                "match": fresh.get(k) == comm.get(k),
            }
            g1_cells += 1
            g1_bad += int(fresh.get(k) != comm.get(k))
            fm, cm = fresh.get(f"{k}_mon") or [], comm.get(f"{k}_mon") or []
            for i in range(12):
                g1_cells += 1
                fv = fm[i] if i < len(fm) else None
                cv = cm[i] if i < len(cm) else None
                if fv != cv:
                    g1_bad += 1
                    row["monthly_mismatches"].append(
                        {
                            "field": f"{k}_mon",
                            "month": i + 1,
                            "fresh": fv,
                            "committed": cv,
                        }
                    )
        row["unrounded"] = {k: round(v, 4) for k, v in _unrounded_rt_lw(y).items()}
        rec["g1"][str(y)] = row

    # ---- G-2: propagation into the bench, and its confinement --------------
    g2_cells = g2_bad = 0
    for y in YEARS:
        avg = _bench_avglmp(y)
        comm = committed_ref[str(y)]
        row = {"annual": {}, "monthly_mismatches": []}
        for kind in BASES:
            k = f"{kind}_lw"
            row["annual"][k] = {
                "bench": avg.get(k),
                "reference": comm.get(k),
                "match": avg.get(k) == comm.get(k),
            }
            g2_cells += 1
            g2_bad += int(avg.get(k) != comm.get(k))
            bm, cm = avg.get(f"{k}_mon") or [], comm.get(f"{k}_mon") or []
            for i in range(12):
                g2_cells += 1
                bv = bm[i] if i < len(bm) else None
                cv = cm[i] if i < len(cm) else None
                if bv != cv:
                    g2_bad += 1
                    row["monthly_mismatches"].append(
                        {
                            "field": f"{k}_mon",
                            "month": i + 1,
                            "bench": bv,
                            "reference": cv,
                        }
                    )
        # confinement: every leaf that moved in the refresh commit must be *_lw
        pre = _flatten(_bench_full(y, f"{REFRESH_COMMIT}^"))
        post = _flatten(_bench_full(y))
        moved = [
            k
            for k in set(pre) | set(post)
            if pre.get(k, "\0<absent>") != post.get(k, "\0<absent>")
        ]
        non_lw = sorted(k for k in moved if "_lw" not in k)
        row["leaves_total"] = len(post)
        row["leaves_moved"] = len(moved)
        row["leaves_moved_non_lw"] = non_lw
        g2_bad += len(non_lw)
        rec["g2"][str(y)] = row

    rec["gates"] = {
        "G1_reference_reproduces": {
            "cells": g1_cells,
            "mismatches": g1_bad,
            "verdict": "PASS" if g1_bad == 0 else "FAIL",
        },
        "G2_propagation_faithful_and_confined": {
            "cells": g2_cells,
            "mismatches": g2_bad,
            "verdict": "PASS" if g2_bad == 0 else "FAIL",
        },
    }

    RECORD.write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(rec["gates"], indent=2))
    for y in YEARS:
        a = rec["g1"][str(y)]["annual"]
        u = rec["g1"][str(y)]["unrounded"]
        print(
            f"  {y}: rt_lw fresh {a['rt_lw']['fresh']} vs committed "
            f"{a['rt_lw']['committed']} | da_lw {a['da_lw']['fresh']} vs "
            f"{a['da_lw']['committed']} | unrounded rt {u['rt']} da {u['da']}"
        )
    print(f"wrote {RECORD}")


if __name__ == "__main__":
    main()
