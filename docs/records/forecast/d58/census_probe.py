"""capx D58 census probe — the PJM sector census, zero LP.

Reproduces the D53 design §0.2-§0.4 method on PJM, reading COMMITTED artifacts
only: the D57 arm A hindcast ledgers (the on-recipe posture bundle), the
EIA-860 2020-vintage plant + generator tables, and the committed scoring
target ``capacity_actuals_pjm.csv``. No LP, no screen, no evolution is run and
the fleet loader is not called.

Outputs ``census_probe.json`` beside this file.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a"
V2020 = ROOT / "data/raw/eia-860/vintage_2020"
ACTUALS = ROOT / "data/raw/_validation-source/capacity_actuals_pjm.csv"

UTILITY_SECTOR = 1
# The screen's candidate fuels (capacity_evolution.retirements._THERMAL_FOM).
THERMAL = {"coal", "gas_cc", "gas_ct", "gas_st", "gas_cc_ccs", "oil", "nuclear"}

_PLANT_RE = re.compile(r"_p(\d+)_")
_LEGACY_RE = re.compile(r"^(\d+)_")


def plant_code(unit_id: str) -> int | None:
    """Plant code from a unit id, both fleet grains.

    CAMPD-binned tranches carry ``..._p<code>_<tranche>``; legacy per-unit rows
    (PJM's oil fleet is unit-grain here) carry ``<code>_<generator>`` — the two
    shapes D53 design §10 names. ``Generator.plant_code`` is populated on both
    paths, so this reconstructs the same join key the gate itself uses.
    """
    m = _PLANT_RE.search(unit_id)
    if m:
        return int(m.group(1))
    m = _LEGACY_RE.match(unit_id)
    return int(m.group(1)) if m else None


def sectors() -> dict[int, int]:
    df = pd.read_parquet(V2020 / "eia860_plant.parquet", columns=["Plant Code", "Sector"])
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


def regulatory_status() -> dict[int, str]:
    df = pd.read_parquet(V2020 / "eia860_plant.parquet")
    col = next((c for c in df.columns if c.strip().lower() == "regulatory status"), None)
    if col is None:
        return {}
    df = df.dropna(subset=["Plant Code", col])
    return {int(c): str(s).strip() for c, s in zip(df["Plant Code"], df[col])}


def fleet_by_sector(sec: dict[int, int]) -> dict:
    """PJM operable thermal nameplate by fuel x sector at the 2020 vintage."""
    from market_sim.data.fleet.eia860 import _map_fuel_type  # noqa: PLC0415

    df = pd.read_parquet(V2020 / "eia860_generators.parquet")
    ba, st, pc = "balancing_authority_code", "status", "plant_id"
    cap, et, pm = "nameplate_capacity_mw", "energy_source", "prime_mover"
    sub = df[(df[ba].astype(str).str.strip() == "PJM") & (df[st].astype(str).str.strip() == "OP")]
    out: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for _, r in sub.iterrows():
        try:
            fuel = _map_fuel_type(str(r["technology"]), str(r[et]), str(r[pm]))
        except Exception:
            fuel = None
        if fuel not in THERMAL:
            continue
        s = sec.get(int(r[pc]))
        key = str(s) if s is not None else "unknown"
        out[fuel][key] += float(r[cap] or 0.0)
    return {f: dict(sorted(v.items())) for f, v in sorted(out.items())}


def failing_by_sector(sec: dict[int, int]) -> dict:
    """The screen's failing set (decided + entry_capped) by sector x fuel."""
    res: dict[str, dict] = {}
    for year in (2021, 2022, 2023, 2024, 2025):
        p = BUNDLE / f"evolution_{year}.json"
        if not p.exists():
            continue
        led = json.loads(p.read_text())
        ev = led.get("pipeline_events") or []
        # The failing set of THIS year's screen is its `decided` (admitted by
        # the reliability floor's admission cap) plus its `entry_capped` rows
        # (failed the bar, retained by the floor). `executed` / `re_confirmed`
        # / `reversed` are pipeline follow-ups on earlier decisions and are
        # counted separately. (`decided_year` stamps the PRIOR-results year the
        # screen priced on, not the screen's own evolution year.)
        fail = [e for e in ev if e.get("event") in ("decided", "entry_capped")]
        by_sector: dict[str, float] = defaultdict(float)
        by_fuel_sector: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        rows_by_sector: dict[str, int] = defaultdict(int)
        decided_by_sector: dict[str, float] = defaultdict(float)
        for e in fail:
            code = plant_code(e["unit_id"])
            s = sec.get(code) if code else None
            key = str(s) if s is not None else "unknown"
            mw = float(e.get("mw") or 0.0)
            by_sector[key] += mw
            by_fuel_sector[e.get("fuel", "?")][key] += mw
            rows_by_sector[key] += 1
            if e.get("event") == "decided":
                decided_by_sector[key] += mw
        total = sum(by_sector.values())
        s1 = by_sector.get("1", 0.0)
        res[str(year)] = {
            "rows": len(fail),
            "mw": round(total, 3),
            "mw_by_sector": {k: round(v, 3) for k, v in sorted(by_sector.items())},
            "rows_by_sector": dict(sorted(rows_by_sector.items())),
            "decided_mw_by_sector": {
                k: round(v, 3) for k, v in sorted(decided_by_sector.items())
            },
            "mw_by_fuel_sector": {
                f: {k: round(v, 3) for k, v in sorted(d.items())}
                for f, d in sorted(by_fuel_sector.items())
            },
            "sector1_share": round(s1 / total, 5) if total else None,
            "gated_out_mw": round(s1, 3),
            "post_gate_mw": round(total - s1, 3),
            # headroom: what the admission cap actually admitted this screen
            "admitted_decided_mw": round(
                sum(float(e.get("mw") or 0.0) for e in ev if e.get("event") == "decided"),
                3,
            ),
            "capped_mw": round(
                sum(float(e.get("mw") or 0.0) for e in ev if e.get("event") == "entry_capped"),
                3,
            ),
            "event_counts": {
                k: sum(1 for e in ev if e.get("event") == k)
                for k in ("decided", "entry_capped", "executed", "re_confirmed", "reversed")
            },
        }
    return res


def cohort_by_sector(sec: dict[int, int]) -> dict:
    """The real PJM exit cohort 2021-2025 by fuel x sector (committed target)."""
    if not ACTUALS.exists():
        return {"error": f"missing {ACTUALS}"}
    df = pd.read_csv(ACTUALS, comment="#")
    cols = {c.strip().lower(): c for c in df.columns}
    kind = cols.get("kind")
    sub = df[df[kind].astype(str).str.strip() == "retirement"] if kind else df
    ycol = cols.get("year")
    if ycol:
        sub = sub[(sub[ycol] >= 2021) & (sub[ycol] <= 2025)]
    pcol = cols.get("plant_id") or cols.get("plant code") or cols.get("plant_code")
    fcol = cols.get("fuel") or cols.get("fuel_type")
    mcol = cols.get("mw") or cols.get("capacity_mw")
    out: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    plants: dict[str, list] = defaultdict(list)
    for _, r in sub.iterrows():
        try:
            code = int(r[pcol])
        except Exception:
            code = None
        s = sec.get(code) if code else None
        key = str(s) if s is not None else "unknown"
        fuel = str(r[fcol]).strip() if fcol else "?"
        mw = float(r[mcol] or 0.0) if mcol else 0.0
        out[fuel][key] += mw
        plants[fuel].append((code, key, mw, int(r[ycol]) if ycol else None))
    res = {}
    for fuel, d in sorted(out.items()):
        tot = sum(d.values())
        res[fuel] = {
            "mw_by_sector": {k: round(v, 1) for k, v in sorted(d.items())},
            "total_mw": round(tot, 1),
            "sector1_share": round(d.get("1", 0.0) / tot, 3) if tot else None,
        }
    return {"by_fuel": res, "columns": list(df.columns)}


def main() -> None:
    sec = sectors()
    reg = regulatory_status()
    # §0.1 equivalence check on the PJM-relevant population
    xtab: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for code, s in sec.items():
        xtab[str(s)][reg.get(code, "unknown")] += 1
    payload = {
        "source": {
            "bundle": str(BUNDLE.relative_to(ROOT)),
            "vintage": "eia-860/vintage_2020",
            "actuals": str(ACTUALS.relative_to(ROOT)),
        },
        "sector_x_regstatus_all_plants": {
            k: dict(sorted(v.items())) for k, v in sorted(xtab.items())
        },
        "pjm_fleet_by_fuel_sector": fleet_by_sector(sec),
        "failing_by_sector": failing_by_sector(sec),
        "real_cohort_by_sector": cohort_by_sector(sec),
    }
    out = Path(__file__).with_name("census_probe.json")
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
