"""COAL-SUB census: coal MW by resolved subclass, 9 ISOs x 2019-2025 (zero LP).

Owner instruction 2026-09-25 (verbatim): *"we need to completely eliminate the
class Coal From the model altogether all coal should be sorted into its
subclass"*. This aggregates the per-ISO-year snapshots written by
:mod:`coal_subclass_snapshot` (the designated keeper's recipe, rebuilt with
``fleet_only=True``) into the census the change is judged against: thermal coal
MW by resolved subclass, and the MW that resolved to NO subclass (the former
generic ``COAL`` bucket), with the plant list for each.

An ISO-year the keeper recipe cannot rebuild (a year outside the keeper span
whose solve inputs are absent — e.g. CAISO 2019-2021's supply-consistent
demand) falls back to the raw EIA-860 fleet load
(:func:`market_sim.data.fleet.load_fleet_from_csv` with ``year``), and the row
says which source it came from.

Every unresolved plant is additionally looked up in the committed EIA-860
generator parquets (operable + retired-within-window) for its units'
``energy_source`` codes, which is the evidence for the final-fallback subclass.

Usage::

    python scripts/probes/coal_subclass_census.py --snap <dir> --out <file.json> [--md <file.md>]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NWPP", "NYISO", "PJM", "SOCO", "SPP")
YEARS = tuple(range(2019, 2026))
SUBCLASSES = ("COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC")


def _raw_coal_units(iso: str, year: int) -> list[dict]:
    """Coal units of the raw EIA-860 fleet load for ``iso``/``year``."""
    from market_sim.config.plant_taxonomy import COAL_SUPPLY_TO_CLASS
    from market_sim.data.coal import coal_supply_class
    from market_sim.data.fleet import load_fleet_from_csv

    out = []
    for g in load_fleet_from_csv(iso, year=year):
        if g.fuel_type != "coal":
            continue
        pc = int(g.plant_code or 0)
        sup = coal_supply_class(pc) if pc else ""
        out.append(
            {
                "unit_id": g.unit_id,
                "plant_code": pc,
                "name": g.name,
                "pmax_mw": float(g.pmax_mw),
                "plant_group": g.plant_group,
                "resolved_supply": sup,
                "resolved_subclass": COAL_SUPPLY_TO_CLASS.get(sup, ""),
            }
        )
    return out


def _energy_sources(plant_codes: set[int]) -> dict[int, list[str]]:
    """EIA-860 coal-unit ``energy_source`` codes per plant (operable + retired)."""
    import pandas as pd

    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.fleet import (
        EIA_860_PARQUET_NAME,
        EIA_860_RETIRED_WINDOW_PARQUET_NAME,
    )

    out: dict[int, set[str]] = defaultdict(set)
    for name in (EIA_860_PARQUET_NAME, EIA_860_RETIRED_WINDOW_PARQUET_NAME):
        p = EIA_860_DIR / name
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        cols = [c for c in ("plant_id", "energy_source", "technology") if c in df.columns]
        df = df[cols]
        df = df[df["plant_id"].astype(int).isin(plant_codes)]
        for pid, src in zip(df["plant_id"], df["energy_source"]):
            out[int(pid)].add(str(src).strip().upper())
    return {k: sorted(v) for k, v in out.items()}


def main() -> None:
    """Aggregate the snapshots into the census JSON (and optional markdown)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snap", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--md", type=Path)
    a = ap.parse_args()

    rows = []
    unresolved_plants: dict[int, dict] = {}
    for iso in ISOS:
        for year in YEARS:
            snap = a.snap / f"{iso}_{year}.json"
            if snap.exists():
                units = json.loads(snap.read_text())["coal_units"]
                source = "keeper-recipe fleet_only rebuild"
            else:
                try:
                    units = _raw_coal_units(iso, year)
                    source = "raw EIA-860 fleet load (keeper recipe not rebuildable)"
                except Exception as exc:  # noqa: BLE001 — recorded, never hidden
                    rows.append({"iso": iso, "year": year, "source": f"FAILED: {exc}"})
                    continue
            mw = {s: 0.0 for s in SUBCLASSES}
            mw["UNRESOLVED"] = 0.0
            plants: dict[str, set] = defaultdict(set)
            for u in units:
                k = u["resolved_subclass"] or "UNRESOLVED"
                mw[k] += u["pmax_mw"]
                plants[k].add((u["plant_code"], u["name"]))
                if k == "UNRESOLVED":
                    rec = unresolved_plants.setdefault(
                        u["plant_code"], {"name": u["name"], "isos": set(), "years": set()}
                    )
                    rec["isos"].add(iso)
                    rec["years"].add(year)
            rows.append(
                {
                    "iso": iso,
                    "year": year,
                    "source": source,
                    "coal_rows": len(units),
                    "mw": {k: round(v, 3) for k, v in mw.items()},
                    "plants": {
                        k: sorted([f"{pc} {nm}" for pc, nm in v]) for k, v in plants.items()
                    },
                }
            )
    es = _energy_sources(set(unresolved_plants))
    for pc, rec in unresolved_plants.items():
        rec["energy_sources"] = es.get(pc, [])
        rec["isos"] = sorted(rec["isos"])
        rec["years"] = sorted(rec["years"])
    a.out.write_text(
        json.dumps(
            {"rows": rows, "unresolved_plants": {str(k): v for k, v in unresolved_plants.items()}},
            indent=1,
        )
    )
    if a.md:
        lines = [
            "| ISO | Year | Source | LIGNITE | PRB | BIT | WC | **UNRESOLVED** |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
        for r in rows:
            if "mw" not in r:
                lines.append(f"| {r['iso']} | {r['year']} | {r['source']} | | | | | |")
                continue
            m = r["mw"]
            src = "keeper" if r["source"].startswith("keeper") else "raw 860"
            lines.append(
                f"| {r['iso']} | {r['year']} | {src} | {m['COAL_LIGNITE']:,.1f} | "
                f"{m['COAL_PRB']:,.1f} | {m['COAL_BIT']:,.1f} | {m['COAL_WC']:,.1f} | "
                f"**{m['UNRESOLVED']:,.1f}** |"
            )
        lines += ["", "Unresolved plants (generic `COAL` bucket today):", ""]
        for pc, rec in sorted(unresolved_plants.items()):
            lines.append(
                f"- {pc} {rec['name']} — {', '.join(rec['isos'])} "
                f"{rec['years'][0]}-{rec['years'][-1]}; EIA-860 energy_source "
                f"{rec['energy_sources'] or 'NONE FOUND'}"
            )
        a.md.write_text("\n".join(lines) + "\n")
    print(json.dumps({r["iso"] + str(r["year"]): r.get("mw") for r in rows})[:4000])


if __name__ == "__main__":
    main()
