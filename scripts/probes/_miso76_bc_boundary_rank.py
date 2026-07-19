"""miso-76 Phase-A probe 3 — where measured MISO DA congestion sits, by model-zone boundary.

Derive-only (NO LP). Downloads MISO's public ANNUAL consolidated Day-Ahead
binding-constraints histories (``YYYY_da_bc_HIST.csv``, 2023-2025 train window
only, rule 22), maps each binding branch's From/To control areas onto the six
model zones via the LBA crosswalk below, and ranks zone boundaries by
constraint-hours and total |shadow price| mass.

Phase-A finding (2026-07-19 run): DA congestion is dominated by WITHIN-zone
branch constraints (West-internal alone 20-26% of Σ|SP|) plus external/seam
constraints (20-32%); clean between-model-zone corridor pairs barely register.
Together with the report carrying NO MW limits, this refutes the
corridor-cap mechanism family (charter §3 M1) at the data layer: per-corridor
caps could only be an invented apportionment (scope doc D4).

Shadow prices here are the ANSWER class (rule 13) — this probe uses them only
to LOCATE and RANK measured congestion for validation targets, never as a
model input.

Run: ``.venv/bin/python scripts/probes/_miso76_bc_boundary_rank.py --cache-dir /tmp/miso76_bc``
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://docs.misoenergy.org/marketreports"
YEARS = (2023, 2024, 2025)  # train window ONLY (rule 22)

# MISO local balancing authority -> model zone (docs/multi-iso/
# miso-zonal-refinement-scope.md sub-BA groups). External CAs (SPP/AECI/TVA/
# PJM sides of seam constraints) -> EXT; unrecognized -> EXT.
CA2Z = {
    "NSP": "West",
    "OTP": "West",
    "MDU": "West",
    "GRE": "West",
    "MP": "West",
    "SMP": "West",
    "DPC": "West",
    "ALTW": "Plains",
    "MEC": "Plains",
    "MPW": "Plains",
    "AMMO": "Plains",
    "AMIL": "Illinois",
    "CWLP": "Illinois",
    "SIPC": "Illinois",
    "IPL": "Indiana",
    "NIPS": "Indiana",
    "CIN": "Indiana",
    "SIGE": "Indiana",
    "HE": "Indiana",
    "DEI": "Indiana",
    "BREC": "Indiana",
    "OVEC": "Indiana",
    "CONS": "East",
    "METC": "East",
    "DECO": "East",
    "ITCT": "East",
    "WEC": "East",
    "ALTE": "East",
    "WPS": "East",
    "MGE": "East",
    "UPPC": "East",
    "MIUP": "East",
    "EES": "South",
    "EAI": "South",
    "CLEC": "South",
    "LAFA": "South",
    "LEPA": "South",
    "SME": "South",
    "LAGN": "South",
}
_CA_PAT = re.compile(r"\(\w+/([^/]+)/([^)]+)\)")


def _zone_pair(branch: str) -> str:
    """Map a branch's ``(type/FromCA/ToCA)`` suffix to a sorted zone-pair key."""
    m = _CA_PAT.search(str(branch))
    if not m:
        return "?"
    a, b = m.group(1).strip(), m.group(2).strip()
    za = CA2Z.get(a, "EXT")
    zb = za if b in ("*", "") else CA2Z.get(b, "EXT")
    return "|".join(sorted({za, zb}))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", required=True, help="download/cache directory")
    args = ap.parse_args()
    cache = Path(args.cache_dir)
    cache.mkdir(parents=True, exist_ok=True)

    for y in YEARS:
        dest = cache / f"{y}_da_bc_HIST.csv"
        if not dest.exists() or dest.stat().st_size == 0:
            with urllib.request.urlopen(f"{BASE}/{y}_da_bc_HIST.csv", timeout=300) as r:
                dest.write_bytes(r.read())
        df = pd.read_csv(dest, skiprows=2, low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        bcol = next(c for c in df.columns if c.startswith("Branch"))
        spcol = next(c for c in df.columns if "Shadow" in c)
        sp = pd.to_numeric(
            df[spcol].astype(str).str.replace(r"[\$\(\),]", "", regex=True),
            errors="coerce",
        ).abs()
        out = (
            pd.DataFrame({"z": df[bcol].map(_zone_pair), "sp": sp})
            .groupby("z")
            .agg(chours=("sp", "size"), sp_mass=("sp", "sum"))
            .sort_values("sp_mass", ascending=False)
        )
        out["share%"] = (100 * out.sp_mass / out.sp_mass.sum()).round(1)
        out["sp_mass"] = (out.sp_mass / 1000).round(1)
        print(
            f"=== DA {y} (rows {len(df)}) — constraint-hours + Σ|SP| (k$-h) by zone boundary ==="
        )
        print(out.head(12).to_string())
        print()


if __name__ == "__main__":
    main()
