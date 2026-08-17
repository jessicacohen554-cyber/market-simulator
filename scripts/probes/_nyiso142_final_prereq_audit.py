"""nyiso-142 — NYISO input-preparedness audit for the LOCKED-TEST years.

Answers the input half of the ``final`` readiness question (job 2 of the
nyiso-142 prompt): *could* NYISO's frozen keeper recipe be built and scored for
**2019** and **H1-2026**, the two touch-once locked-test years, if the owner
granted the one-shot? Modelled on ``scripts/probes/neiso90_final_prereq_audit.py``
(the NEISO precedent, ``ASSESSMENT-neiso87-declaration-2026-08-06.md`` §3.2).

**This probe produces NO model output.** It resolves loaders and inspects
on-disk coverage only — no LP is constructed, no year is solved, scored or
registered. Under CLAUDE.md rule 22 as rewritten 2026-08-06 ("WHAT IS HELD OUT
IS THE *SCORE*, NEVER THE *DATA*") input inspection is unrestricted; the spend
is looking at an answer, which this never does. The one place a measured
*actual* is reported (:func:`probe_actual_lmp`) is a property of the MARKET with
no model output on either side — the same disclosure neiso-87 §3 made, and the
fact the discrimination argument turns on.

Usage:
    PYTHONPATH=$PWD python scripts/probes/_nyiso142_final_prereq_audit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISO = "NYISO"
# The two locked-test years (CLAUDE.md rule 22). 2026 stands for H1-2026: the
# validation LMP series carries a half-year of coverage under year == 2026.
PROBE_YEARS = (2019, 2026)
CONTROL_YEAR = 2023  # in-sample, to prove the probe itself resolves

RAW = REPO / "data" / "raw"
VALID = RAW / "_validation-source"
ALL_YEARS = (*PROBE_YEARS, CONTROL_YEAR)


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
    """``load_demand`` — the array the LP energy balance is built from."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.demand import load_demand

    out = {}
    for y in ALL_YEARS:
        try:
            arr = load_demand(ISO, y, get_iso_config(ISO))
            twh = float(arr.sum()) / 1.0e6
            out[y] = _ok(
                f"shape {arr.shape}, peak {arr.sum(axis=0).max():,.0f} MW, {twh:,.2f} TWh"
            )
        except Exception as e:  # noqa: BLE001 - probe reports, never raises
            out[y] = _err(e)
    return out


def probe_backcast_config() -> dict[int, tuple[str, str]]:
    """Can the keeper's own recipe be BUILT for this year? (config only, no LP.)"""
    from market_sim.pipeline.backcast_config import backcast_config
    from market_sim.pipeline.reference import henry_hub_actual, load_reference

    ref = load_reference()
    out = {}
    for y in ALL_YEARS:
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
                f"plant_level={getattr(cfg, 'plant_level_fleet', None)}, "
                f"campd_bins={getattr(cfg, 'use_campd_bins', None)}"
            )
        except Exception as e:  # noqa: BLE001
            out[y] = _err(e)
    return out


def probe_henry_hub() -> dict[int, tuple[str, str]]:
    """``henry_hub_actual`` — the per-year gas price the keeper's config records."""
    out = {}
    try:
        from market_sim.pipeline.reference import henry_hub_actual, load_reference

        ref = load_reference()
    except Exception as e:  # noqa: BLE001
        return {y: _err(e) for y in ALL_YEARS}
    for y in ALL_YEARS:
        try:
            out[y] = _ok(f"${henry_hub_actual(ref, y):.2f}/MMBtu")
        except Exception as e:  # noqa: BLE001
            out[y] = _err(e)
    return out


def probe_calibration_reference() -> dict[int, tuple[str, str]]:
    """``calibration_reference.json`` — the C1/C2 scoring target."""
    p = VALID / "calibration_reference.json"
    if not p.exists():
        return {y: _gap("file absent") for y in ALL_YEARS}
    doc = json.loads(p.read_text())
    block = (doc.get("isos") or {}).get(ISO) or {}
    hh = doc.get("henry_hub_actual") or {}
    out = {}
    for y in ALL_YEARS:
        rec = block.get(str(y))
        if not rec:
            out[y] = _gap(f"no isos.{ISO}.{y} block")
            continue
        out[y] = _ok(
            f"{len(rec)} keys ({', '.join(sorted(rec)[:6])}"
            f"{'…' if len(rec) > 6 else ''}); "
            f"henry_hub {'present' if str(y) in hh else 'ABSENT'}"
        )
    return out


def probe_actual_lmp() -> dict[int, tuple[str, str]]:
    """The hub series C3a/C3b/C3c score against — and its DISCRIMINATING POWER.

    Reporting the actual >$300 count is an ACTUALS property: no model output
    exists on either side of it, so it is not a score. It is also the whole
    readiness question for a C3c-limited ISO — a year the market never took
    into scarcity cannot test the criterion the keeper is caveated on.
    """
    p = VALID / f"actual_lmp_hourly_{ISO}.parquet"
    if not p.exists():
        return {y: _gap("file absent") for y in ALL_YEARS}
    df = pd.read_parquet(p)
    out = {}
    for y in ALL_YEARS:
        d = df[df["year"].astype(int) == y]
        if d.empty:
            out[y] = _gap("no rows")
            continue
        rt = d["rt"].astype(float)
        out[y] = _ok(
            f"{len(d)} rows, rt cov {rt.notna().mean():.3f}, "
            f"mean ${rt.mean():.2f}, max ${rt.max():,.2f}, "
            f">$300: {int((rt > 300).sum())}h"
        )
    return out


def probe_actual_tail() -> dict[int, tuple[str, str]]:
    """``actual_tail.json`` — the C3c benchmark part (TIER-GATED at emission)."""
    p = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"
    doc = json.loads(p.read_text()).get("isos", {}).get(ISO, {})
    out = {}
    for y in ALL_YEARS:
        rec = doc.get(str(y))
        out[y] = (
            _ok(f"rt_gt {rec['rt_gt']}h, da_gt {rec['da_gt']}h, cov {rec['rt_coverage']}")
            if rec
            else _gap("no row — C3c SKIPs for this year")
        )
    return out


def probe_fleet_regime() -> dict[int, tuple[str, str]]:
    """REGIME DRIFT — the model's nuclear fleet against the year's actual output.

    Rule 22 says to grade a pre-2020 locked test against regime drift rather
    than raw MAE. For NYISO the drift is dominated by one event: Indian Point
    2 and 3 (~2,060 MW downstate) retired 2020-04 and 2021-04. The model's
    fleet is built from the ``EIA860_OPERABLE_VINTAGE`` (2025) snapshot, so it
    carries only the four surviving upstate reactors. Compare that capacity's
    plausible output against NYISO's OWN published fuel mix for the year —
    both sides are inputs/actuals, no model output is involved.
    """
    eia = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generator_operable.parquet")
    ny = eia[(eia["State"] == "NY") & eia["Technology"].astype(str).str.contains(
        "Nuclear", case=False, na=False
    )]
    fleet_mw = float(pd.to_numeric(ny["Nameplate Capacity (MW)"], errors="coerce").sum())

    out = {}
    for y in ALL_YEARS:
        path = REPO / f"data/raw/NYISO/fuel-mix/NYISO_fuelmix_hourly_{y}.csv.gz"
        if not path.exists():
            out[y] = _gap(f"no published fuel mix for {y}")
            continue
        mix = pd.read_csv(path)
        nuc = float(
            mix.loc[mix["fuel_category"] == "Nuclear", "gen_mw"].sum()
        ) / 1.0e6
        implied = fleet_mw * 8760 * 0.92 / 1.0e6  # ~92 % CF, the 2023-25 realised level
        short = nuc - implied
        note = (
            f"model fleet {len(ny)} reactors / {fleet_mw:,.0f} MW -> ~{implied:.1f} TWh; "
            f"NYISO published actual {nuc:.2f} TWh; shortfall {short:+.2f} TWh"
        )
        out[y] = _gap(note) if short > 2.0 else _ok(note)
    return out


def probe_eia860_restorability() -> dict[int, tuple[str, str]]:
    """Can EIA-860 restore a unit that had RETIRED by the operable vintage?

    ``EIA860_OPERABLE_VINTAGE`` is a 2025 snapshot. A NY unit that retired
    before it is only representable if some file carries it. Indian Point 2/3
    (~2,060 MW of downstate Zone-H nuclear, retired 2020-04 and 2021-04) is the
    load-bearing case for a 2019 backcast, so it is probed by name.
    """
    import glob

    found = []
    for p in glob.glob(str(RAW / "eia-860" / "eia860_generator*.parquet")):
        df = pd.read_parquet(p)
        namecol = next(
            (c for c in df.columns if str(c).lower().replace("_", " ") == "plant name"),
            None,
        )
        if namecol is None:
            continue
        hit = df[df[namecol].astype(str).str.contains("Indian Point", case=False, na=False)]
        if len(hit):
            found.append(f"{Path(p).name}: {len(hit)} rows")
    note = (
        f"Indian Point present in {'; '.join(found)}"
        if found
        else "Indian Point ABSENT from every eia860_generator*.parquet in data/raw"
    )
    return {
        y: (_ok(note) if found else (_gap(note) if y < 2022 else _ok(note + " (post-retirement year — not needed)")))
        for y in ALL_YEARS
    }


_DATE_HINTS = ("date", "start", "period", "timestamp")


def _year_coverage(paths, year_col_candidates=("year", "Year", "YEAR")):
    """Read the first existing path and report whether it carries each year."""
    for p in paths:
        if not p.exists():
            continue
        try:
            df = (
                pd.read_csv(p, comment="#", low_memory=False)
                if p.suffix == ".csv"
                else pd.read_parquet(p)
            )
        except Exception:  # noqa: BLE001
            return p, None
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
        return {y: _gap(f"{label}: no file matching {patterns}") for y in ALL_YEARS}
    if counts is None:
        return {y: _ok(f"{p.name} present (no year column)") for y in ALL_YEARS}
    out = {}
    for y in ALL_YEARS:
        n = counts.get(y, 0)
        out[y] = _ok(f"{n} rows in {p.name}") if n else _gap(f"no {y} rows in {p.name}")
    return out


def probe_hydro() -> dict[int, tuple[str, str]]:
    """``load_hydro_budget`` — EIA-923 monthly budget x EIA-860 nameplate."""
    from market_sim.data.hydro import load_hydro_budget

    out = {}
    for y in ALL_YEARS:
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


def probe_nyiso_reserves() -> dict[int, tuple[str, str]]:
    """The measured NYISO reserve requirements the keeper's ORDC span rests on."""
    try:
        from market_sim.data.nyiso_reserve_requirements import (
            load_nyiso_reserve_requirements,
        )
    except Exception as e:  # noqa: BLE001
        return {y: _err(e) for y in ALL_YEARS}
    out = {}
    for y in ALL_YEARS:
        try:
            r = load_nyiso_reserve_requirements(y, 8760)
            out[y] = _ok(f"resolved: {len(r)} families")
        except Exception as e:  # noqa: BLE001
            out[y] = _err(e)
    return out


def probe_market_solar() -> dict[int, tuple[str, str]]:
    """``load_market_solar_monthly`` — the keeper arms the registry/COD basis."""
    try:
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.nyiso_market_solar import load_market_solar_monthly

        zone_names = list(get_iso_config(ISO).zone_names)
    except Exception as e:  # noqa: BLE001
        return {y: _err(e) for y in ALL_YEARS}
    out = {}
    for y in ALL_YEARS:
        try:
            v = load_market_solar_monthly(ISO, y, zone_names)
            # The loader returns None for a year the registry has no rows for —
            # it does not raise, so an unguarded call reads as a false OK.
            out[y] = (
                _gap("returns None — no market-solar registry rows for this year")
                if v is None
                else _ok(f"{len(v)} entries")
            )
        except Exception as e:  # noqa: BLE001
            out[y] = _err(e)
    return out


def probe_renewable_capacity() -> dict[int, tuple[str, str]]:
    """``NYISO_<y>_renewable_capacity.csv`` — the renewable-bound input.

    Probed by PER-YEAR FILE EXISTENCE, not by a year column: the artifact is one
    file per year with no year column, so the generic coverage probe would read
    only the first match and report a false GAP on the control year.
    """
    out = {}
    for y in ALL_YEARS:
        hits = list(RAW.rglob(f"{ISO}_{y}_renewable_capacity.csv"))
        if not hits:
            out[y] = _gap("file absent")
            continue
        out[y] = _ok(f"{len(pd.read_csv(hits[0]))} rows — {hits[0].relative_to(REPO)}")
    return out


PROBES = [
    ("load_demand (LP demand array)", probe_demand),
    ("backcast_config (the keeper recipe, built)", probe_backcast_config),
    ("build_fleet (REGIME DRIFT — capacity by class)", probe_fleet_regime),
    ("EIA-860 restorability of pre-vintage retirees", probe_eia860_restorability),
    ("load_hydro_budget", probe_hydro),
    ("load_nyiso_reserve_requirements", probe_nyiso_reserves),
    ("nyiso_market_solar (keeper arms the COD basis)", probe_market_solar),
    ("henry_hub_actual (per-year gas price)", probe_henry_hub),
    ("calibration_reference.json (C1/C2 target)", probe_calibration_reference),
    (f"actual_lmp_hourly_{ISO} (C3a/C3b/C3c upstream)", probe_actual_lmp),
    ("actual_tail.json (C3c benchmark part)", probe_actual_tail),
    (f"{ISO}_<y>_renewable_capacity.csv", probe_renewable_capacity),
    (
        "gas_basis_by_iso_month.csv",
        lambda: probe_file("gas basis", ["gas_basis_by_iso_month.csv"]),
    ),
    (
        "campd-unit-outages-NYISO.csv",
        lambda: probe_file("outages", ["campd-unit-outages-NYISO.csv"]),
    ),
    (
        "plant_emission_rates_v2",
        lambda: probe_file("emis v2", ["plant_emission_rates_v2.parquet"]),
    ),
    (
        "NYISO interface flows",
        lambda: probe_file("interface", ["NYISO_interface_flows_hourly_*.csv.gz"]),
    ),
    ("EIA-930 NYIS_fueltype", lambda: probe_file("930 fuel", ["NYIS_fueltype.parquet"])),
    ("EIA-930 NYIS_region", lambda: probe_file("930 region", ["NYIS_region.parquet"])),
]


def main() -> None:
    print(
        f"nyiso-142 locked-test input-preparedness audit @ HEAD — {ISO}, "
        f"years {PROBE_YEARS} (control {CONTROL_YEAR})"
    )
    print("=" * 100)
    rows = {}
    for label, fn in PROBES:
        try:
            res = fn()
        except Exception as e:  # noqa: BLE001
            res = {y: _err(e) for y in ALL_YEARS}
        rows[label] = res
        print(f"\n### {label}")
        for y in ALL_YEARS:
            st, note = res.get(y, ("?", "not probed"))
            print(f"  {y}  [{st:3s}]  {note}")
    out = REPO / "results" / "calibration" / "_nyiso142_prereq_audit.json"
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
