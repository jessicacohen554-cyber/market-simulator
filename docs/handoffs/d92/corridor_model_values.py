#!/usr/bin/env python3
"""Reconstruct the FC-5 disposition table's 54 ``model_value`` cells from a
committed ``full_horizon_summary.json``.

capx D92 measurement helper (rule 29 phase 0 — zero LP). The FC-5 disposition
table is hand-authored and carries a frozen ``model_value`` per row keyed to
one bundle (``model_source.cache_key``). Nothing in the repository recomputes
those cells, so re-basing the table onto another bundle has no instrument. This
module implements each row's own ``model_basis`` string literally and is
VALIDATED by reproducing the committed table from the bundle it declares — a
row this module cannot reproduce is never re-based by D92.

Not standing tooling: it is the measurement record for
``docs/handoffs/FINDING-capx-d92-2026-09-10.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: The PS residual the D29 classification note fixes (MW), read from the
#: disposition's own ``model_source.storage_ps_residual_gw``.
_MW_PER_GW = 1000.0


def _traj(summary: dict) -> dict[int, dict]:
    return {int(r["year"]): r for r in (summary.get("trajectory") or []) if r.get("year")}


def _cap(row: dict) -> dict[str, float]:
    return {str(k): float(v) for k, v in (row.get("capacity_by_fuel_mw") or {}).items()}


def _gen(row: dict) -> dict[str, float]:
    return {str(k): float(v) for k, v in (row.get("generation_by_fuel_mwh") or {}).items()}


def model_values(summary: dict, year: int, ps_residual_gw: float) -> dict[str, float]:
    """Every quantity the NEISO T3 disposition scores, for one target year."""
    row = _traj(summary)[year]
    cap, gen = _cap(row), _gen(row)
    ps_mw = ps_residual_gw * _MW_PER_GW
    storage_power = float(row.get("storage_power_mw") or 0.0)
    total_gen = float(row.get("total_gen_mwh") or 0.0)
    imports_gen = gen.get("import", 0.0)
    cap_no_import = sum(v for k, v in cap.items() if k != "import")
    ren_gen = sum(gen.get(f, 0.0) for f in ("wind", "solar", "hydro", "biomass"))
    gas_gen = sum(gen.get(f, 0.0) for f in ("gas_cc", "gas_cc_ccs", "gas_ct", "gas_st"))
    return {
        "capacity:total": (cap_no_import + storage_power) / _MW_PER_GW,
        "capacity:coal": cap.get("coal", 0.0) / _MW_PER_GW,
        "capacity:gas_cc": (cap.get("gas_cc", 0.0) + cap.get("gas_cc_ccs", 0.0)) / _MW_PER_GW,
        "capacity:fossil_peaker_steam": (
            cap.get("gas_ct", 0.0) + cap.get("gas_st", 0.0) + cap.get("oil", 0.0)
        ) / _MW_PER_GW,
        "capacity:nuclear": cap.get("nuclear", 0.0) / _MW_PER_GW,
        "capacity:hydro": cap.get("hydro", 0.0) / _MW_PER_GW,
        "capacity:solar": cap.get("solar", 0.0) / _MW_PER_GW,
        "capacity:wind_total": cap.get("wind", 0.0) / _MW_PER_GW,
        "capacity:storage": (storage_power - ps_mw) / _MW_PER_GW,
        "capacity:pumped_storage": ps_mw / _MW_PER_GW,
        "capacity:biomass_waste": cap.get("biomass", 0.0) / _MW_PER_GW,
        "co2": float(row.get("co2_mt") or 0.0),
        "generation:total": (total_gen - imports_gen) / 1e6,
        "generation:coal": gen.get("coal", 0.0) / 1e6,
        "generation:gas": gas_gen / 1e6,
        "generation:nuclear": gen.get("nuclear", 0.0) / 1e6,
        "generation:oil": gen.get("oil", 0.0) / 1e6,
        "generation:renewables": ren_gen / 1e6,
    }


def reproduce(disposition: dict, summary: dict, tol: float = 5e-4) -> list[dict]:
    """One record per disposition row: committed value, reconstruction, match."""
    ps = float(disposition["model_source"].get("storage_ps_residual_gw") or 0.0)
    out = []
    cache: dict[int, dict[str, float]] = {}
    for r in disposition["rows"]:
        y = int(r["target_year"])
        if y not in cache:
            cache[y] = model_values(summary, y, ps)
        got = cache[y].get(r["quantity"])
        want = float(r["model_value"])
        out.append(
            {
                "quantity": r["quantity"],
                "year": y,
                "committed": want,
                "reconstructed": None if got is None else round(got, 4),
                "match": got is not None and abs(round(got, 4) - want) <= tol,
            }
        )
    return out


def main(argv: list[str]) -> int:
    disp = json.loads(Path(argv[1]).read_text())
    summ = json.loads(Path(argv[2]).read_text())
    recs = reproduce(disp, summ)
    ok = sum(1 for r in recs if r["match"])
    print(f"reproduced {ok}/{len(recs)} committed model_value cells")
    for r in recs:
        if not r["match"]:
            print(f"  MISS {r['quantity']:32} @{r['year']}  committed={r['committed']} got={r['reconstructed']}")
    return 0 if ok == len(recs) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
