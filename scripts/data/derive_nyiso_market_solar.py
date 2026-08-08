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

**THE SECOND DATE BASIS (nyiso-133,
``ScenarioConfig.nyiso_solar_registry_cod_dates``).** The artifact carries the
same registry on TWO published in-service date bases, in parallel columns:
``capacity_mw`` (the Gold Book ``In-Service Date``, unchanged) and
``capacity_mw_cod`` (EIA-860's capacity-weighted ``Operating Year`` /
``Operating Month`` for the crosswalked plant, falling back to the Gold Book date
where no EIA-860 record exists). Membership and nameplate stay **100 % Gold
Book** on both bases — only the month a plant's capacity switches on differs.

The Gold Book in-service date is a registration / interconnection-service date
and **leads the plant's metered commercial start**; EIA-860's ``Operating
Month`` matches it. Measured on this very registry against EIA-923 metered
monthly output (probe ``scripts/probes/_nyiso133_commissioning_ramp.py``, record
``results/calibration/_nyiso133_commissioning_ramp.json``): EIA-860's month
equals the first metered-output month in **11 of the 12 uncensored plants**,
while the Gold Book date leads by **+2 months on Morris Ridge (179 MW)**, +1 on
High River (90 MW) and East Point (50 MW) — and trails by 1 and 3 months on two
others, so the difference is signed both ways rather than a one-directional
correction. That is rule 14 ``[R-ACCURATE]``'s *reconciled-real-data* path: two
published registries disagree on one field and a third published series
adjudicates. Rule 23 ``[R-FROZEN-DERIVE]``: the trigger is that measurement, NOT
a residual — the swap makes the 2023 advisory band WORSE (+20.0 % -> +21.2 %)
while halving 2024's (+32.7 % -> +19.1 %).

**Rule 23 [R-FROZEN-DERIVE].** Re-run only when a new Gold Book vintage (or
EIA-860 vintage) lands. Never re-run against a residual.

**Rule 25 [R-ISO-SCOPE].** NYISO-only, from NYISO's own posting. The artifact
records the ISO and the loader hard-errors on a mismatch.

Usage::

    python scripts/data/derive_nyiso_market_solar.py

Writes ``data/raw/reference/nyiso-market-solar-capacity.csv``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
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

# EIA-860 operable generator schedule — the second published in-service date
# basis (nyiso-133). Same file the EIA-860 solar path already reads.
EIA860 = RAW_DIR / "eia-860" / "eia860_generator_operable.parquet"

# Gold Book Table III-2a PTID -> EIA plant code. An IDENTITY mapping between two
# published registries for the same physical plant, not a parameter: every row
# is verified below on nameplate agreement and an unverifiable row is DROPPED
# (it then keeps its Gold Book date) rather than guessed. Albany County Solar 2
# is mapped to None deliberately — EIA-860 carries only "Hecate Energy Albany
# County 1" at 20 MW, so unit 2 has no separate record to cross to.
PTID_TO_EIA: dict[int, int | None] = {
    323809: 65125,  # Puckett Solar          -> NY8 - Puckett Solar
    323808: 65123,  # Janis Solar            -> NY8 - Janis Solar
    323848: 68274,  # Morris Ridge Solar     -> Morris Ridge Solar
    323811: 65122,  # Branscomb Solar        -> NY8 - Branscomb Solar
    323812: 65124,  # Regan Solar            -> NY8 - Regan Solar
    323813: 65121,  # Grissom Solar          -> NY8 - Grissom Solar
    323810: 65839,  # Darby Solar            -> NY8 - Darby Solar
    323814: 65841,  # Stillwater Solar       -> NY8 - ELP Stillwater Solar
    323833: 64077,  # Albany County Solar 1  -> Hecate Energy Albany County 1
    323834: None,  # Albany County Solar 2  -> no separate EIA-860 record
    323815: 65840,  # Pattersonville Solar   -> NY8 - Teichos Pattersonville
    323840: 65805,  # East Point Solar       -> East Point Energy Center
    323847: 65765,  # High River Solar       -> High River Energy Center, LLC
    323691: 57589,  # Long Island Solar Farm -> Long Island Solar Farm LLC
    323806: 65679,  # Calverton Solar        -> Calverton Solar Energy Center
}

# A crosswalk row survives only when the two registries agree on nameplate to
# within this band. Wide enough to absorb an AC/DC rating convention difference
# (Morris Ridge is 179.0 Gold Book vs 177.0 EIA-860), narrow enough that a
# wrong plant cannot pass. A failing row is DROPPED, never rescaled.
CROSSWALK_MW_TOLERANCE: tuple[float, float] = (0.75, 1.34)

# Month assumed when EIA-860 knows a unit's operating YEAR but not its month —
# the same mid-year convention data.cod_ramp.COD_FALLBACK_MONTH applies.
COD_FALLBACK_MONTH: int = 7


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


def _eia860_cod_dates(reg: pd.DataFrame) -> pd.Series:
    """Return each registry PTID's EIA-860 commercial-operation date (or NaT).

    The plant's date is the **capacity-weighted** mean of its EIA-860 units'
    ``(Operating Year, Operating Month)``, the same reduction
    :func:`market_sim.data.cod_ramp._load_cod_map` applies, so a multi-unit
    plant lands on the date the bulk of its nameplate came online. A row is
    returned only when the crosswalk is verified: the plant must be in
    :data:`PTID_TO_EIA`, present in EIA-860, and agree with the Gold Book
    nameplate within :data:`CROSSWALK_MW_TOLERANCE`. Every other PTID gets
    ``NaT`` and keeps its published Gold Book date.

    Args:
        reg: The union registry from :func:`build_registry` (needs ``ptid`` and
            ``nameplate_mw``).

    Returns:
        A ``Timestamp``/``NaT`` series indexed like *reg*.
    """
    e860 = pd.read_parquet(EIA860)
    e860 = e860[e860["Status"].astype(str).str.strip().str.upper() == "OP"]
    dates: list[pd.Timestamp] = []
    for _, row in reg.iterrows():
        code = PTID_TO_EIA.get(int(row["ptid"]))
        sub = e860[e860["Plant Code"] == code] if code is not None else e860.iloc[:0]
        if sub.empty:
            dates.append(pd.NaT)
            continue
        cap = pd.to_numeric(sub["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0)
        oy = pd.to_numeric(sub["Operating Year"], errors="coerce")
        om = pd.to_numeric(sub["Operating Month"], errors="coerce").fillna(
            COD_FALLBACK_MONTH
        )
        known = oy.notna()
        ratio = float(cap.sum()) / float(row["nameplate_mw"])
        lo, hi = CROSSWALK_MW_TOLERANCE
        if not known.any() or not (lo <= ratio <= hi):
            dates.append(pd.NaT)
            continue
        weights = cap[known].to_numpy()
        if weights.sum() <= 0.0:
            weights = np.ones(int(known.sum()))
        continuous = oy[known].to_numpy() + (om[known].to_numpy() - 1.0) / 12.0
        mean = float(np.average(continuous, weights=weights))
        year = int(np.floor(mean))
        month = min(max(int(round((mean - year) * 12.0)) + 1, 1), 12)
        dates.append(pd.Timestamp(year=year, month=month, day=1))
    return pd.Series(dates, index=reg.index, dtype="datetime64[ns]")


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
        ``capacity_mw`` / ``n_units`` (the Gold Book in-service date basis) and
        ``capacity_mw_cod`` / ``n_units_cod`` (the EIA-860 ``Operating Month``
        basis, nyiso-133). The two bases differ ONLY in the month a unit's
        capacity switches on — membership and nameplate are identical.
    """
    model_zones = sorted(set(_ZONE_TO_MODEL.values()))
    reg = reg.assign(model_zone=reg["zone"].map(_ZONE_TO_MODEL))
    # EIA-860 date where the crosswalk verifies, published Gold Book date
    # otherwise — an unmatched unit is never given an invented date.
    cod = _eia860_cod_dates(reg)
    reg = reg.assign(in_service_cod=cod.fillna(reg["in_service"]))
    rows: list[dict] = []
    for year in YEARS:
        for month in range(1, 13):
            month_end = pd.Timestamp(
                year=year, month=month, day=1
            ) + pd.offsets.MonthEnd(0)
            # Registration ends after the last vintage that lists the unit;
            # a unit listed in the final vintage stays registered to the end.
            registered = reg[reg["last_vintage"] >= year]
            live = registered[registered["in_service"] <= month_end]
            live_cod = registered[registered["in_service_cod"] <= month_end]
            by_zone = live.groupby("model_zone")["nameplate_mw"].agg(["sum", "size"])
            by_zone_cod = live_cod.groupby("model_zone")["nameplate_mw"].agg(
                ["sum", "size"]
            )
            for mz in model_zones:
                rows.append(
                    {
                        "year": year,
                        "month": month,
                        "model_zone": mz,
                        "capacity_mw": round(float(by_zone["sum"].get(mz, 0.0)), 3),
                        "n_units": int(by_zone["size"].get(mz, 0)),
                        "capacity_mw_cod": round(
                            float(by_zone_cod["sum"].get(mz, 0.0)), 3
                        ),
                        "n_units_cod": int(by_zone_cod["size"].get(mz, 0)),
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

    cod = _eia860_cod_dates(reg)
    matched = int(cod.notna().sum())
    print(
        f"\nEIA-860 crosswalk (nyiso-133): {matched}/{len(reg)} units verified; "
        f"{len(reg) - matched} keep their Gold Book date"
    )
    for (_, row), date in zip(reg.iterrows(), cod):
        if pd.isna(date):
            continue
        lead = (date.year - row["in_service"].year) * 12 + (
            date.month - row["in_service"].month
        )
        if lead:
            print(
                f"    {row['station']:24s} {row['nameplate_mw']:6.1f} MW  "
                f"gold book {row['in_service']:%Y-%m} -> EIA-860 {date:%Y-%m} "
                f"({lead:+d} mo)"
            )

    monthly = monthly_capacity(reg)
    print("\nISO-total registered PV capacity by month (MW), gold-book basis:")
    tot = monthly.groupby(["year", "month"])["capacity_mw"].sum().unstack()
    print(tot.round(1).to_string())
    print("\nmean-monthly MW by basis:")
    means = monthly.groupby("year")[["capacity_mw", "capacity_mw_cod"]].sum() / 12.0
    for year, row in means.iterrows():
        print(
            f"    {year}: gold book {row['capacity_mw']:8.2f}   "
            f"EIA-860 {row['capacity_mw_cod']:8.2f}   "
            f"ratio {row['capacity_mw_cod'] / row['capacity_mw']:.4f}"
        )

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
            "# TWO PUBLISHED DATE BASES, same membership and same nameplate (nyiso-133,\n"
            "#   ScenarioConfig.nyiso_solar_registry_cod_dates):\n"
            "#     capacity_mw     — Gold Book 'In-Service Date' (a registration /\n"
            "#                       interconnection-service date), the historical basis;\n"
            "#     capacity_mw_cod — EIA-860 capacity-weighted Operating Year/Month for\n"
            "#                       the crosswalked plant, which matches the first\n"
            "#                       METERED month of output in 11 of 12 uncensored\n"
            "#                       plants (EIA-923); Gold Book date where unmatched.\n"
            "#   Evidence: results/calibration/_nyiso133_commissioning_ramp.json.\n"
            "# Regenerate: python scripts/data/derive_nyiso_market_solar.py\n"
            "iso,year,month,model_zone,capacity_mw,n_units,capacity_mw_cod,n_units_cod\n"
        )
        monthly.assign(iso="NYISO")[
            [
                "iso",
                "year",
                "month",
                "model_zone",
                "capacity_mw",
                "n_units",
                "capacity_mw_cod",
                "n_units_cod",
            ]
        ].to_csv(fh, index=False, header=False)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
