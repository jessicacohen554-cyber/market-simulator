#!/usr/bin/env python
"""Derive NWPP per-zone gas-basis rows from the COMMITTED per-plant EIA-923 series.

Builds ``data/raw/nwpp_zonal_gas_hub.csv`` — the NWPP analogue of the committed
``{pjm,miso,caiso,ercot,spp}_zonal_gas_hub.csv`` tables, on exactly their schema
(``zone,year,basis_vs_hh_usd_mmbtu,hub,source``), so
``market_sim.data.fuel.basis.meanzero._load_zonal_gas_hub`` reads it with no new
parsing code.

Landed 2026-09-14 by lane **NWPP-33**
(``docs/multi-iso/nwpp-addition-plan-2026-09.md`` §5 row NWPP-33; FINDING
``docs/handoffs/FINDING-nwpp-33-2026-09-14.md``). Full provenance, the hub
attribution evidence and the caveats: ``data/raw/nwpp_zonal_gas_hub.SOURCES.md``.

Why this footprint gets a per-zone table at all
-----------------------------------------------
NWPP-12 measured a **2.51x internal gas spread** across the footprint
(NorthWestern Montana burns gas at 40 % of PacifiCorp East's price), so a single
``NWPP`` hub is not a simplification but an error the size of the fuel cost
itself (``data/raw/gas-prices/SOURCES_nwpp_gas.md`` §1).

Where the numbers come from, and why not a hub series
-----------------------------------------------------
Every sibling table proxies its zones with a published HUB or a per-STATE EIA
series. NWPP cannot and does not need to:

* **Cannot** — Stanfield, Opal and Kern River have no free public daily or
  monthly series reachable from this repo, established rather than assumed by
  NWPP-12 (EIA's Weekly Update spot table carries four points, none of them
  these; the dnav spot series is Henry Hub only; the ICE workbook path 404s).
  Only **Sumas** is committed, and it prices one of the five zones.
  Synthesising the other three from a neighbouring hub is the substitution
  rule 13 ``[R-MEASURED]`` forbids and plan gate **G17** refuses by name.
* **Does not need to** — the finest-grain measured input is already committed:
  ``data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`` (EIA-923
  Schedule 2), per plant per month, ``price_per_mmbtu`` and ``quantity``. Under
  rule 14 ``[R-ACCURATE]`` the delivered price the zone's own plants actually
  paid beats a state proxy for a state that is 30 % of the zone (which is what
  SPP-North has to live with). Coverage here is **complete**: all five zones,
  all twelve months, all three years — no gap and no fallback row.

Construction (one rule, no per-zone or per-year choices)::

    price_z,m   = Σ_p price_{p,m} · quantity_{p,m} / Σ_p quantity_{p,m}
    basis_z,y   = mean over the 12 months m of ( price_z,m − HenryHub_m )

Quantity-weighting **within** a month is what the zone actually paid that month;
averaging the twelve monthly *basis* values **equally** is the month-balanced
convention every sibling table uses, so a heavy-burn winter cannot pull the
annual level toward the winter basis. Henry Hub is the committed
``data/raw/gas-prices/henry_hub_monthly.csv``. Plants are assigned to zones by
``zone_assignment.build_zone_lookup("NWPP")`` — the ruled BA-keyed map, the same
key the fleet and the renewable capacity use.

**January 2023 is real and it is not removed.** The western winter 2022-23 gas
event puts January 2023 at $39.66 (EAST) / $34.61 (SNV) / $21.38 (OR) /MMBtu
against a $3.27 Henry Hub, and it dominates every zone's 2023 row. That is a
measured physical market event, so it stays: dropping a month because it is
inconvenient is exactly the residual-driven selection rules 1 ``[R-STRUCT]``
and 13 forbid. The SOURCES file reports the January-excluded number beside it so
the distortion is **visible rather than buried**, and states plainly that the
2023 row is a one-month-dominated annual mean.

Nothing here is fitted to any residual, and the LEVEL never reaches a solve
anyway: the mean-zero applier re-centres to a gas-capacity-weighted mean of zero
(the PJM/MISO/CAISO/ERCOT convention), so only the measured cross-zonal spread
can move dispatch.

**No applier is armed for NWPP.** This lane lands a measured table and a
registered filename, not a mechanism: registering the path constant
(``meanzero.NWPP_ZONAL_GAS_HUB_PATH``) and any applier lives under ``src/`` and
is outside this lane's boundary, so no ``ScenarioConfig`` field is added, nothing
reads this yet, and no keeper's ``cache_key`` moves (plan §7 gate G8). Arming is
routed to NWPP-DESK — see the FINDING §5.

Usage::

    python scripts/data/derive_nwpp_zonal_gas_hub.py            # derive + write CSV
    python scripts/data/derive_nwpp_zonal_gas_hub.py --dry-run  # print only
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.zone_assignment import build_zone_lookup

ISO = "NWPP"
OUT_PATH: Path = RAW_DATA_DIR / "nwpp_zonal_gas_hub.csv"
EIA923_PATH: Path = (
    RAW_DATA_DIR / "_processed-legacy" / "eia923_monthly_fuel_costs.parquet"
)
HENRY_HUB_PATH: Path = RAW_DATA_DIR / "gas-prices" / "henry_hub_monthly.csv"
YEARS: tuple[int, ...] = (2023, 2024, 2025)
FUEL_GROUP = "Natural Gas"

# Each zone's PHYSICAL pricing point, from the EIA-860 ``Natural Gas Pipeline
# Name 1`` census (nwpp-data-audit.md §7.2) as re-measured and EXTENDED by this
# lane's read of ``Pipeline Notes`` — which closes the one attribution the audit
# left provisional. Named MW behind each label is in the SOURCES file. This
# string is documentation carried on the row: the VALUE beside it is the
# measured EIA-923 delivered price, never a quote from the named hub.
ZONE_HUB: dict[str, str] = {
    # Northwest Pipeline GP, 2,036.8 MW named — the Canadian-border receipt
    # point of that system IS Sumas, which EIA itself calls "the main pricing
    # point for natural gas in the Pacific Northwest".
    "NWPP-NW": "Sumas / Northwest Pipeline",
    # GTN 1,490.2 MW + "Pacific Gas" 1,319.3 MW; GTN's interconnect with
    # Northwest Pipeline is Stanfield, in this zone's own territory.
    "NWPP-OR": "Stanfield / GTN",
    # THE MIXED ZONE, and it is labelled as mixed rather than resolved to its
    # larger half: Northwest Pipeline 762.2 MW (Williams/Rockies-sourced, IPCO)
    # against GTN 554.3 MW plus NorthWestern's own LDC 261.6 MW (NWMT). The two
    # members' delivered prices differ by 2.15x (NWMT $1.815, IPCO $3.903 per
    # MMBtu over 2023-2025), so the zone average describes NEITHER member. A
    # split is a zoning change, which is owner-ruled territory (card N5) and not
    # this lane's to make; the caveat is declared instead.
    "NWPP-INLAND": "MIXED: Opal/Northwest Pipeline (IPCO) + Stanfield/GTN and "
    "NorthWestern LDC (NWMT)",
    # Rockies. The audit called this provisional because 1,174.1 MW was filed as
    # "Other - please explain in pipeline notes"; this lane read the notes:
    # 1,164.1 MW is Jim Bridger 1-2, "gas supply from Williams Gas Supply", and
    # 10.0 MW is Hurricane City Power on "Enbridge (formerly Dominion Energy)",
    # i.e. Questar's successor. With Questar's own 152.4 MW and Colorado
    # Interstate's 2.2 MW that is 1,328.7 of 1,695.3 named MW (78.4 %) on the
    # Rockies complex. NOT provisional any more.
    "NWPP-EAST": "Opal / Rockies (Williams, Questar-Enbridge)",
    # Kern River 4,747.1 MW directly, plus Southwest Gas 3,419.1 MW as the LDC
    # downstream of Kern River / El Paso. Unambiguous.
    "NWPP-SNV": "Kern River",
}

SOURCE_TEMPLATE = (
    "EIA-923 Schedule 2 per-plant delivered natural-gas price "
    "(data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet), "
    "quantity-weighted across the zone's plants within each month, minus the "
    "Henry Hub monthly mean; month-balanced over {months} monthly observations "
    "from {plants} plant(s). Zone assignment: the ruled BA-keyed map "
    "(zone_assignment.build_zone_lookup('NWPP')). Derived by "
    "scripts/data/derive_nwpp_zonal_gas_hub.py (lane NWPP-33); see "
    "data/raw/nwpp_zonal_gas_hub.SOURCES.md{note}"
)
JAN_2023_NOTE = (
    " -- NOTE: this 2023 row is dominated by the western winter 2022-23 gas "
    "event (January {jan:.2f} $/MMBtu against a {hh:.2f} Henry Hub); the "
    "January-excluded basis is {ex:.3f}. The month is REAL and is not removed"
)


def load_zone_months() -> pd.DataFrame:
    """Return per-zone, per-month delivered gas price and Henry Hub, 2023-2025.

    Returns:
        A frame with ``zone``, ``year``, ``month``, ``price`` (quantity-weighted
        $/MMBtu across the zone's plants), ``hh`` ($/MMBtu), ``plants`` and
        ``quantity``.

    Raises:
        FileNotFoundError: if either committed source is absent.
    """
    for path in (EIA923_PATH, HENRY_HUB_PATH):
        if not path.exists():
            raise FileNotFoundError(f"required committed source missing: {path}")
    lookup = build_zone_lookup(ISO)
    frame = pd.read_parquet(EIA923_PATH)
    frame = frame[frame["fuel_group"] == FUEL_GROUP].copy()
    frame["zone"] = frame["plant_id"].map(lookup)
    frame = frame[
        frame["zone"].notna()
        & frame["year"].isin(YEARS)
        & frame["price_per_mmbtu"].notna()
        & (frame["quantity"] > 0)
    ]
    grouped = frame.groupby(["zone", "year", "month"]).apply(
        lambda d: pd.Series(
            {
                "price": float(np.average(d["price_per_mmbtu"], weights=d["quantity"])),
                "plants": int(d["plant_id"].nunique()),
                "quantity": float(d["quantity"].sum()),
            }
        ),
        include_groups=False,
    )
    henry = pd.read_csv(HENRY_HUB_PATH).set_index(["year", "month"])["price_usd_mmbtu"]
    grouped = grouped.reset_index()
    grouped["hh"] = [
        float(henry.loc[(int(r.year), int(r.month))]) for r in grouped.itertuples()
    ]
    return grouped


def build_rows(months: pd.DataFrame) -> list[dict[str, object]]:
    """Collapse the per-zone monthly frame into one CSV row per zone-year.

    Args:
        months: The frame :func:`load_zone_months` returns.

    Returns:
        Rows on the shared hub-table schema, ordered by zone then year.
    """
    zone_names = get_iso_config(ISO).zone_names
    rows: list[dict[str, object]] = []
    for zone in zone_names:
        for year in YEARS:
            sub = months[(months["zone"] == zone) & (months["year"] == year)]
            if sub.empty:
                continue
            basis = (sub["price"] - sub["hh"]).mean()
            note = ""
            if year == 2023:
                january = sub[sub["month"] == 1]
                rest = sub[sub["month"] != 1]
                if not january.empty and not rest.empty:
                    note = JAN_2023_NOTE.format(
                        jan=float(january["price"].iloc[0]),
                        hh=float(january["hh"].iloc[0]),
                        ex=float((rest["price"] - rest["hh"]).mean()),
                    )
            rows.append(
                {
                    "zone": zone,
                    "year": int(year),
                    "basis_vs_hh_usd_mmbtu": round(float(basis), 3),
                    "hub": ZONE_HUB[zone],
                    "source": SOURCE_TEMPLATE.format(
                        months=len(sub),
                        plants=int(sub["plants"].max()),
                        note=note,
                    ),
                }
            )
    return rows


def report(months: pd.DataFrame, rows: list[dict[str, object]]) -> None:
    """Print the table and the gas-capacity-weighted mean-zero spread.

    The LEVEL of these rows never reaches a solve — the mean-zero applier
    re-centres them — so the number a reader should judge is the re-centred
    cross-zonal spread, printed here beside the raw basis.
    """
    zone_names = get_iso_config(ISO).zone_names
    print(f"\n=== {ISO} per-zone gas basis vs Henry Hub ($/MMBtu) ===")
    table = {(r["zone"], r["year"]): r["basis_vs_hh_usd_mmbtu"] for r in rows}
    header = "  {:12s}".format("zone") + "".join(f"{y:>10d}" for y in YEARS)
    print(header)
    for zone in zone_names:
        line = f"  {zone:12s}"
        for year in YEARS:
            value = table.get((zone, year))
            line += f"{value:10.3f}" if value is not None else f"{'--':>10s}"
        print(line)
    for year in YEARS:
        values = np.array(
            [table[(z, year)] for z in zone_names if (z, year) in table], dtype=float
        )
        if values.size:
            centred = values - values.mean()
            print(
                f"  {year} equal-weight mean-zero spread: "
                f"{centred.min():+.3f} .. {centred.max():+.3f} "
                f"(range {centred.max() - centred.min():.3f} $/MMBtu)"
            )
    burned = months.groupby("zone")["quantity"].sum()
    print("\n  MMBtu burned 2023-2025 by zone:")
    for zone in zone_names:
        if zone in burned:
            print(f"    {zone:12s} {burned[zone]:,.0f}")


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    """Write the hub table on the shared five-column schema."""
    fields = ["zone", "year", "basis_vs_hh_usd_mmbtu", "hub", "source"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print without writing")
    args = parser.parse_args(argv)
    months = load_zone_months()
    rows = build_rows(months)
    report(months, rows)
    if args.dry_run:
        print("\n(dry run: nothing written)")
        return 0
    write_csv(rows, OUT_PATH)
    print(f"\nwrote {len(rows)} row(s) -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
