"""neiso-90 — refresh the NEISO out-of-training input-preparedness audit at HEAD.

Re-runs the per-year input walk that
``results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md`` §3.2 did,
for **2019 and 2020**, against HEAD — because four of that table's rows went
stale when neiso-88 (the ``load_demand`` correction) and neiso-89 (PR #3693:
``calibration_reference.json``, the 2019/2020 renewable-capacity CSVs, the
``derive_actual_tail`` widening) landed.

**This probe produces NO model output.** It resolves loaders and inspects
on-disk coverage only — no LP is constructed, no year is solved, scored or
registered. Under CLAUDE.md rule 22 as rewritten 2026-08-06 ("WHAT IS HELD OUT
IS THE *SCORE*, NEVER THE *DATA*") input inspection is unrestricted; the spend
is looking at an answer, which this never does.

Usage:
    uv run python scripts/probes/neiso90_final_prereq_audit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISO = "NEISO"
PROBE_YEARS = (2019, 2020)
CONTROL_YEAR = 2023  # an in-sample year, to prove the probe itself works

RAW = REPO / "data" / "raw"
VALID = RAW / "_validation-source"


def _ok(msg: str) -> tuple[str, str]:
    return ("OK", msg)


def _gap(msg: str) -> tuple[str, str]:
    return ("GAP", msg)


def _err(exc: Exception) -> tuple[str, str]:
    return ("ERR", f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# individual probes — each returns {year: (status, note)}
# ---------------------------------------------------------------------------


def probe_demand() -> dict[int, tuple[str, str]]:
    """``load_demand`` — the array ``runner.py:961`` actually builds the LP from.

    NOT ``load_demand_meta``, which is the summary helper neiso-87 §3.1 probed
    by mistake and which has no consumer in the solve path (neiso-88 §2.3).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.demand import load_demand

    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        try:
            arr = load_demand(ISO, y, get_iso_config(ISO))
            twh = float(arr.sum()) / 1.0e6
            out[y] = _ok(
                f"shape {arr.shape}, peak {arr.sum(axis=0).max():,.0f} MW, {twh:,.2f} TWh"
            )
        except Exception as e:  # noqa: BLE001 - probe reports, never raises
            out[y] = _err(e)
    return out


def probe_henry_hub() -> dict[int, tuple[str, str]]:
    """``_henry_hub_actual`` — the per-year gas price the keeper's config records."""
    out = {}
    try:
        from market_sim.pipeline.reference import henry_hub_actual, load_reference

        ref = load_reference()
    except Exception as e:  # noqa: BLE001
        return {y: _err(e) for y in (*PROBE_YEARS, CONTROL_YEAR)}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        try:
            out[y] = _ok(f"${henry_hub_actual(ref, y):.2f}/MMBtu")
        except Exception as e:  # noqa: BLE001
            out[y] = _err(e)
    return out


def probe_calibration_reference() -> dict[int, tuple[str, str]]:
    """``calibration_reference.json`` — the C1/C2 scoring target.

    Reads the exact ``isos.<ISO>.<year>`` path the scorer uses, not a
    fuzzy search: a false positive here would be the whole audit's headline.
    """
    p = VALID / "calibration_reference.json"
    if not p.exists():
        return {y: _gap("file absent") for y in (*PROBE_YEARS, CONTROL_YEAR)}
    doc = json.loads(p.read_text())
    block = (doc.get("isos") or {}).get(ISO) or {}
    hh = doc.get("henry_hub_actual") or {}
    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        rec = block.get(str(y))
        if not rec:
            out[y] = _gap(f"no isos.{ISO}.{y} block")
            continue
        out[y] = _ok(
            f"isos.{ISO}.{y}: {len(rec)} keys ({', '.join(sorted(rec)[:6])}"
            f"{'…' if len(rec) > 6 else ''}); henry_hub {'present' if str(y) in hh else 'ABSENT'}"
        )
    return out


def probe_renewable_capacity() -> dict[int, tuple[str, str]]:
    """``NEISO_<y>_renewable_capacity.csv`` — the renewable-bound input."""
    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        hits = list(RAW.rglob(f"{ISO}_{y}_renewable_capacity.csv"))
        if not hits:
            out[y] = _gap("file absent")
            continue
        df = pd.read_csv(hits[0])
        out[y] = _ok(f"{len(df)} rows — {hits[0].relative_to(REPO)}")
    return out


def probe_actual_tail() -> dict[int, tuple[str, str]]:
    """``actual_tail.json`` — the C3c benchmark part (TIER-GATED at emission)."""
    p = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"
    doc = json.loads(p.read_text()).get("isos", {}).get(ISO, {})
    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        rec = doc.get(str(y))
        out[y] = (
            _ok(
                f"rt_gt {rec['rt_gt']}h, da_gt {rec['da_gt']}h, cov {rec['rt_coverage']}"
            )
            if rec
            else _gap("no row — C3c SKIPs for this year")
        )
    return out


def probe_actual_lmp() -> dict[int, tuple[str, str]]:
    """The hub series ``actual_tail`` is DERIVED from (the upstream of C3c/C3a)."""
    p = VALID / f"actual_lmp_hourly_{ISO}.parquet"
    if not p.exists():
        return {y: _gap("file absent") for y in (*PROBE_YEARS, CONTROL_YEAR)}
    df = pd.read_parquet(p)
    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        d = df[df["year"].astype(int) == y]
        if d.empty:
            out[y] = _gap("no rows")
            continue
        rt = d["rt"].astype(float)
        out[y] = _ok(
            f"{len(d)} h, cov {rt.notna().mean():.3f}, "
            f"max ${rt.max():,.2f}, mean ${rt.mean():.2f}, >$300: {int((rt > 300).sum())}h"
        )
    return out


_DATE_HINTS = ("date", "start", "period", "timestamp")


def _year_coverage(paths, year_col_candidates=("year", "Year", "YEAR")):
    """Read the first existing path and report whether it carries each year.

    Falls back from an explicit year column to the first date-like column
    (``outage_start`` on the CAMPD windows, ``period`` on the EIA-930
    parquets), so a file with no ``year`` column still reports real coverage
    instead of a bare "present".
    """
    for p in paths:
        if not p.exists():
            continue
        df = (
            pd.read_csv(p, comment="#", low_memory=False)
            if p.suffix == ".csv"
            else pd.read_parquet(p)
        )
        for c in year_col_candidates:
            if c in df.columns:
                yr = pd.to_numeric(df[c], errors="coerce").dropna().astype(int)
                return p, yr.value_counts().to_dict()
        for c in df.columns:
            if any(h in str(c).lower() for h in _DATE_HINTS):
                yr = pd.to_datetime(df[c], errors="coerce", utc=True).dt.year
                counts = yr.dropna().astype(int).value_counts().to_dict()
                if counts:
                    return p, counts
        return p, None
    return None, None


def probe_file(label: str, patterns: list[str]) -> dict[int, tuple[str, str]]:
    """Generic per-year coverage probe over the first matching on-disk file."""
    paths = [q for pat in patterns for q in sorted(RAW.rglob(pat))]
    p, counts = _year_coverage(paths)
    if p is None:
        return {
            y: _gap(f"{label}: no file matching {patterns}")
            for y in (*PROBE_YEARS, CONTROL_YEAR)
        }
    if counts is None:
        return {
            y: _ok(f"{p.name} present (no year column)")
            for y in (*PROBE_YEARS, CONTROL_YEAR)
        }
    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        n = counts.get(y, 0)
        out[y] = _ok(f"{n} rows in {p.name}") if n else _gap(f"no {y} rows in {p.name}")
    return out


def probe_backcast_config() -> dict[int, tuple[str, str]]:
    """Can the keeper's own recipe be BUILT for this year? (config only, no LP.)

    ``backcast_config`` is what ``run_year`` calls to assemble the per-year
    ScenarioConfig; if it constructs, every year-keyed default inside it
    resolved. Flags mirror the keeper's ``calibration_flags``.
    """
    from market_sim.pipeline.backcast_config import backcast_config
    from market_sim.pipeline.reference import henry_hub_actual, load_reference

    ref = load_reference()
    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        try:
            cfg = backcast_config(
                y,
                ISO,
                8760,
                henry_hub_actual(ref, y),
                commitment_screen_coal=True,
                coal_prb_passthrough=1.0,
                outage_source="historic",
                coal_mustrun_per_plant=True,
            )
            out[y] = _ok(
                f"built; gas ${cfg.gas_price_override:.2f}, "
                f"campd_bins={getattr(cfg, 'use_campd_bins', None)}, "
                f"plant_level={getattr(cfg, 'plant_level_fleet', None)}, "
                f"winter_fuel_mustrun={getattr(cfg, 'neiso_winter_fuel_mustrun', None)}"
            )
        except Exception as e:  # noqa: BLE001
            out[y] = _err(e)
    return out


def probe_hydro() -> dict[int, tuple[str, str]]:
    """neiso-72's hydro window — EIA-923 monthly budget x EIA-860 nameplate."""
    from market_sim.data.hydro import load_hydro_budget

    out = {}
    for y in (*PROBE_YEARS, CONTROL_YEAR):
        try:
            b = load_hydro_budget(ISO, y)
            tot = float(b.monthly_energy.sum()) / 1.0e6
            out[y] = _ok(
                f"{len(b.plant_ids)} plants, {tot:,.2f} TWh budget, "
                f"max {float(b.max_mw.sum()):,.0f} MW"
            )
        except Exception as e:  # noqa: BLE001
            out[y] = _err(e)
    return out


def probe_reserve_requirements() -> dict[int, tuple[str, str]]:
    """The reserve requirements the keeper actually holds to.

    The keeper runs ``neiso_dynamic_reserve_requirements=False`` (Limb A
    dormant), so its requirements are the PUBLISHED STATIC constants in
    ``model/reserves/spec.py`` — year-independent by construction, hence
    identical for 2019/2020 and the tuned years. The measured hourly series
    (``load_neiso_reserve_requirements``) is deliberately NOT probed as a
    prerequisite: it is an unarmed mechanism whose clean partition is absent
    for the tuned years too.
    """
    from market_sim.model.reserves.spec import NEISO_RCPF_PRODUCTS

    fams = ", ".join(f"{n} {mw:,.0f} MW" for n, mw, *_ in NEISO_RCPF_PRODUCTS)
    return {
        y: _ok(f"static (year-independent): {fams}")
        for y in (*PROBE_YEARS, CONTROL_YEAR)
    }


def probe_parasitic() -> dict[int, tuple[str, str]]:
    """The parasitic net/gross factors, as the SOLVE PATH actually reads them.

    ``fleet.campd_bins._ramp_parasitic_factor_map`` — the only solve-path
    consumer — reads the **pooled ``year == 0`` rows only**. The artifact's
    per-year rows (2022-2025) are the derive's intermediate and have no
    consumer, so this input is year-independent and 2019/2020 are not
    disadvantaged. neiso-87 §3.2 flagged the missing per-year rows as a ⚠;
    on the code path they are not a gap at all.
    """
    from market_sim.data.fleet.campd_bins import _ramp_parasitic_factor_map

    try:
        m = _ramp_parasitic_factor_map()
    except Exception as e:  # noqa: BLE001
        return {y: _err(e) for y in (*PROBE_YEARS, CONTROL_YEAR)}
    note = f"pooled year==0 map: {len(m)} plants (year-independent by construction)"
    return {
        y: (_ok(note) if m else _gap("pooled map empty"))
        for y in (*PROBE_YEARS, CONTROL_YEAR)
    }


PROBES = [
    ("load_demand (LP demand array)", probe_demand),
    ("backcast_config (the keeper recipe, built)", probe_backcast_config),
    ("load_hydro_budget (neiso-72 window)", probe_hydro),
    ("load_neiso_reserve_requirements", probe_reserve_requirements),
    ("henry_hub_actual (per-year gas price)", probe_henry_hub),
    ("calibration_reference.json (C1/C2 target)", probe_calibration_reference),
    ("actual_lmp_hourly_NEISO (C3a/C3b/C3c upstream)", probe_actual_lmp),
    ("actual_tail.json (C3c benchmark part)", probe_actual_tail),
    ("NEISO_<y>_renewable_capacity.csv", probe_renewable_capacity),
    (
        "gas_basis_by_iso_month.csv",
        lambda: probe_file("gas basis", ["gas_basis_by_iso_month.csv"]),
    ),
    (
        "algonquin_citygate_daily.csv",
        lambda: probe_file("AGT daily", ["algonquin_citygate_daily.csv"]),
    ),
    (
        "campd-unit-outages-NEISO.csv",
        lambda: probe_file("outages", ["campd-unit-outages-NEISO.csv"]),
    ),
    (
        "plant_emission_rates_v2",
        lambda: probe_file("emis v2", ["plant_emission_rates_v2*"]),
    ),
    ("fossil_co2_rates", lambda: probe_file("co2", ["fossil_co2_rates*"])),
    ("parasitic_load_factors (pooled map)", lambda: probe_parasitic()),
    (
        "capacity_actuals_neiso.csv",
        lambda: probe_file("cap actuals", ["capacity_actuals_neiso.csv"]),
    ),
    (
        "EIA-930 ISNE_fueltype",
        lambda: probe_file("930 fuel", ["ISNE_fueltype.parquet"]),
    ),
    ("EIA-930 ISNE_region", lambda: probe_file("930 region", ["ISNE_region.parquet"])),
]


def main() -> None:
    print(
        f"neiso-90 input-preparedness audit @ HEAD — {ISO}, years {PROBE_YEARS} "
        f"(control {CONTROL_YEAR})"
    )
    print("=" * 100)
    rows = {}
    for label, fn in PROBES:
        try:
            res = fn()
        except Exception as e:  # noqa: BLE001
            res = {y: _err(e) for y in (*PROBE_YEARS, CONTROL_YEAR)}
        rows[label] = res
        print(f"\n### {label}")
        for y in (*PROBE_YEARS, CONTROL_YEAR):
            st, note = res.get(y, ("?", "not probed"))
            print(f"  {y}  [{st:3s}]  {note}")
    out = REPO / "results" / "calibration" / "_neiso90_prereq_audit.json"
    out.write_text(
        json.dumps(
            {lbl: {str(y): list(v) for y, v in r.items()} for lbl, r in rows.items()},
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"\nwrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
