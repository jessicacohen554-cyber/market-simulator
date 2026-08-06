"""Derive NYISO's front-of-meter (market-generator) solar capacity by model zone.

**What this fixes.** The model distributes NYISO solar capacity from the EIA-860
utility-scale operable schedule, which lists every NY solar plant >= 1 MW —
including the ~2 GW of **distribution-connected NY-Sun community solar** that is
not a NYISO market generator. That energy is already **netted out of the EIA-930
``NYIS`` demand series** the model uses as load (EIA-930 ``NYIS`` ``NG: SUN`` is
identically zero in every hour of 2023-2025 — nyiso-106 measured 8,760/8,760 zero
hours, "structurally absent (NY grid solar is overwhelmingly distribution-
connected / net-metered)"). Carrying it a second time as a grid-supply decision
variable is a **double count**: the same MWh is removed from demand and added to
supply.

**The instrument.** NYISO's Gold Book *Table III-2a — NYISO Market Generators*
is NYISO's own registry of the generators that participate in its market, with a
PTID, a load zone (A-K), a published nameplate rating and a published in-service
date for every unit. A NY solar plant is a NYISO grid-supply resource **iff NYISO
registers it there**; everything else reduces net load. That membership test is an
identity with no freedom in it.

**Zero free parameters.** Three published columns and nothing else: the zone
letter (crosswalked by the same A-K -> five-zone aggregation the rest of the
codebase uses, ``data.nyiso_demand_response._ZONE_TO_MODEL``), the ``Name Plate
Rating`` MW, and the ``In-Service Date``. The monthly ramp is the same
construction :func:`market_sim.data.renewables._eia860_monthly_capacity` already
applies to EIA-860 — a plant contributes its nameplate from its in-service month
onward — so this is a **basis swap on one input**, not a new mechanism. No
percentile, no threshold, no scalar is chosen anywhere.

**Independent validation of the level (computed before the correction was
built).** The Gold Book's own prior-year ``Net Energy`` column against this
script's own mid-year registered capacity gives a capacity factor of **12.9 %
(2023)** and **13.9 % (2024)** — physical utility-PV, and within a point of the
0.133 mean CF the model's (nyiso-75 donor-repaired) NYISO solar profile already
carries. The SHAPE and the CF level were already right; only the **capacity
basis** was wrong. That is what makes this an input repair rather than a retune.

**Rule 13 [R-MEASURED] admissibility.** The output is an INPUT (which plants are
NYISO market generators, and how big they are), never an outcome. It regenerates
for a forward year from the same registry — a newly interconnecting plant enters
on its in-service date — and it responds to changed conditions (a build wave
raises it). It is not the measured solar *generation* series and it is not
capped at delivered output: the LP still dispatches and curtails solar
endogenously against this capacity.

**Rule 23 [R-FROZEN-DERIVE].** Re-run only when a new Gold Book vintage lands.
Never re-run against a residual.

**Rule 25 [R-ISO-SCOPE].** NYISO-only, from NYISO's own posting. The artifact
records the ISO and the loader hard-errors on a mismatch.

Usage::

    python scripts/data/derive_nyiso_market_solar.py

Writes ``data/raw/reference/nyiso-market-solar-capacity.csv``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.nyiso_demand_response import _ZONE_TO_MODEL  # noqa: E402

# Gold Book vintage -> workbook. Vintage N states the year-N capability and the
# year-(N-1) net energy, so the union across vintages plus each row's published
# in-service date is a complete registry history over the solve window.
GOLD_BOOKS: dict[int, str] = {
    2023: "2023-NYCA-Generators.xlsx",
    2024: "2024-NYCA-Generators.xlsx",
    2025: "2025-NYCA-Existing-Generating-Facilities.xlsx",
}

SHEET: str = "Table III-2a"  # "NYISO Market Generators" — III-2b is non-market

# Column positions in Table III-2a's data block (the workbook's own header rows
# are merged cells that pandas cannot resolve, so the block is read headerless
# from the first data row and addressed positionally; the layout is stable
# across all three vintages and is asserted below).
COL_STATION, COL_ZONE, COL_PTID = 2, 3, 4
COL_INSERVICE, COL_NAMEPLATE = 8, 9
COL_UNIT_TYPE, COL_FUEL1 = 15, 16
SKIPROWS: int = 8

YEARS: tuple[int, ...] = (2023, 2024, 2025)
OUT = RAW_DIR / "reference" / "nyiso-market-solar-capacity.csv"


def _read_pv_rows(vintage: int, workbook: str) -> pd.DataFrame:
    """Return the PV rows of one Gold Book vintage's market-generator table.

    Args:
        vintage: Gold Book vintage year (the workbook's own reporting year).
        workbook: Workbook filename under ``data/raw/NYISO``.

    Returns:
        One row per registered PV unit with ``ptid``, ``station``, ``zone``
        (NYISO letter zone), ``in_service`` and ``nameplate_mw``.

    Raises:
        ValueError: if the positional column layout does not hold for this
            vintage (a changed workbook layout must fail loudly, never be
            silently mis-read).
    """
    df = pd.read_excel(
        RAW_DIR / "NYISO" / workbook, sheet_name=SHEET, header=None, skiprows=SKIPROWS
    )
    pv = df[df[COL_UNIT_TYPE].astype(str).str.upper().eq("PV")].copy()
    if pv.empty:
        raise ValueError(f"{workbook}: no PV rows at column {COL_UNIT_TYPE}")
    bad_fuel = ~pv[COL_FUEL1].astype(str).str.upper().eq("SUN")
    bad_zone = ~pv[COL_ZONE].astype(str).str.strip().str.upper().isin(_ZONE_TO_MODEL)
    if bad_fuel.any() or bad_zone.any():
        raise ValueError(
            f"{workbook}: Table III-2a column layout moved — "
            f"{int(bad_fuel.sum())} PV row(s) without fuel SUN, "
            f"{int(bad_zone.sum())} without an A-K zone letter"
        )
    out = pd.DataFrame(
        {
            "ptid": pv[COL_PTID].astype(float).astype(int),
            "station": pv[COL_STATION].astype(str).str.strip(),
            "zone": pv[COL_ZONE].astype(str).str.strip().str.upper(),
            "in_service": pd.to_datetime(pv[COL_INSERVICE]),
            "nameplate_mw": pd.to_numeric(pv[COL_NAMEPLATE], errors="raise").astype(
                float
            ),
            "vintage": vintage,
        }
    )
    return out


def build_registry() -> pd.DataFrame:
    """Return the union registry of NYISO market-generator PV units.

    A unit is registered from its published in-service date. The union is keyed
    by PTID across every vintage; where vintages disagree on nameplate (a
    re-rating) the LATEST vintage that lists the unit wins, and the last vintage
    listing it bounds its registration (a unit dropped from a later vintage
    deregistered at that vintage's year-start).

    Returns:
        One row per PTID with ``station``, ``zone``, ``in_service``,
        ``nameplate_mw``, ``first_vintage`` and ``last_vintage``.
    """
    frames = [_read_pv_rows(v, wb) for v, wb in sorted(GOLD_BOOKS.items())]
    allrows = pd.concat(frames, ignore_index=True).sort_values("vintage")
    reg = allrows.groupby("ptid", as_index=False).agg(
        station=("station", "last"),
        zone=("zone", "last"),
        in_service=("in_service", "min"),
        nameplate_mw=("nameplate_mw", "last"),
        first_vintage=("vintage", "min"),
        last_vintage=("vintage", "max"),
    )
    return reg.sort_values(["zone", "in_service", "ptid"]).reset_index(drop=True)


def monthly_capacity(reg: pd.DataFrame) -> pd.DataFrame:
    """Expand the registry into per-(year, month, model zone) capacity MW.

    A unit contributes its full nameplate in every month from its in-service
    month through the last month its registration covers — the same
    month-of-commercial-operation ramp the EIA-860 path applies. Model zones
    with no registered solar are emitted explicitly at 0.0 MW so the artifact is
    a complete grid (the loader must never have to infer a missing zone).

    Args:
        reg: The union registry from :func:`build_registry`.

    Returns:
        Long-form frame with ``year``, ``month``, ``model_zone``,
        ``capacity_mw`` and ``n_units``.
    """
    model_zones = sorted(set(_ZONE_TO_MODEL.values()))
    reg = reg.assign(model_zone=reg["zone"].map(_ZONE_TO_MODEL))
    rows: list[dict] = []
    for year in YEARS:
        for month in range(1, 13):
            stamp = pd.Timestamp(year=year, month=month, day=1)
            # Registration ends after the last vintage that lists the unit;
            # a unit listed in the final vintage stays registered to the end.
            live = reg[
                (reg["in_service"] <= stamp + pd.offsets.MonthEnd(0))
                & (reg["last_vintage"] >= year)
            ]
            by_zone = live.groupby("model_zone")["nameplate_mw"].agg(["sum", "size"])
            for mz in model_zones:
                cap = float(by_zone["sum"].get(mz, 0.0))
                n = int(by_zone["size"].get(mz, 0))
                rows.append(
                    {
                        "year": year,
                        "month": month,
                        "model_zone": mz,
                        "capacity_mw": round(cap, 3),
                        "n_units": n,
                    }
                )
    return pd.DataFrame(rows)


def main() -> int:
    """Build the artifact and write it, printing the registry and the totals."""
    reg = build_registry()
    print(
        f"NYISO market-generator PV registry: {len(reg)} units, "
        f"{reg['nameplate_mw'].sum():.1f} MW nameplate (union 2023-2025)"
    )
    print(reg.to_string(index=False))

    monthly = monthly_capacity(reg)
    print("\nISO-total registered PV capacity by month (MW):")
    tot = monthly.groupby(["year", "month"])["capacity_mw"].sum().unstack()
    print(tot.round(1).to_string())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write(
            "# NYISO front-of-meter (market-generator) solar capacity by model zone.\n"
            "# SOURCE: NYISO Gold Book Table III-2a 'NYISO Market Generators',\n"
            "#   vintages 2023 / 2024 / 2025 (data/raw/NYISO/*.xlsx) — published\n"
            "#   nameplate rating MW, published in-service date, published A-K load\n"
            "#   zone, crosswalked by data.nyiso_demand_response._ZONE_TO_MODEL.\n"
            "# WHY: EIA-860 utility-scale NY solar includes ~2 GW of distribution-\n"
            "#   connected NY-Sun community solar that is NOT a NYISO market\n"
            "#   generator and is already netted out of the EIA-930 NYIS demand\n"
            "#   series (NYIS 'NG: SUN' is identically zero, nyiso-106). Carrying it\n"
            "#   as grid supply double-counts it.\n"
            "# ZERO FREE PARAMETERS. Rule 13 input, rule 23 frozen (re-derive only on\n"
            "#   a new Gold Book vintage), rule 25 NYISO-only.\n"
            "# Regenerate: python scripts/data/derive_nyiso_market_solar.py\n"
            "iso,year,month,model_zone,capacity_mw,n_units\n"
        )
        monthly.assign(iso="NYISO")[
            ["iso", "year", "month", "model_zone", "capacity_mw", "n_units"]
        ].to_csv(fh, index=False, header=False)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
