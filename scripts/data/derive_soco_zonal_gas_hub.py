#!/usr/bin/env python
"""Derive SOCO per-zone gas-basis rows from the COMMITTED per-plant EIA-923 series.

Builds ``data/raw/soco_zonal_gas_hub.csv`` — the SOCO analogue of the committed
``{pjm,miso,caiso,ercot,spp,nwpp}_zonal_gas_hub.csv`` tables, on exactly their
schema (``zone,year,basis_vs_hh_usd_mmbtu,hub,source``), so
``market_sim.data.fuel.basis.meanzero._load_zonal_gas_hub`` reads it with no new
parsing code.

Landed 2026-09-16 by lane **SOCO-32**
(``docs/multi-iso/soco-addition-plan-2026-09.md`` §5 row SOCO-32; FINDING
``docs/handoffs/FINDING-soco-32-2026-09-16.md``). Full provenance, the
route comparison and the caveats: ``data/raw/soco_zonal_gas_hub.SOURCES.md``.

There is no traded index to use, and that is measured, not assumed
-----------------------------------------------------------------
SOCO-12 swept both free EIA routes that feed the other regions' daily series and
returned a documented NO: the Natural Gas Weekly Update's compact spot table
carries exactly Henry Hub, New York, Chicago and Cal. Comp. Avg. — no Southeast
row — and the daily *Select Spot Prices* region map has no Southeast region at
all (``docs/handoffs/FINDING-soco-12-2026-09-13.md`` §4). The daily index at
SOCO's own basis is a paywalled ICE/NGI product. So the ``hub`` column here
names the **transport system** the zone sits on, and the VALUE beside it is the
measured delivered price the zone's own plants paid — never a quote from the
named system.

Why the per-plant EIA-923 route and not SOCO-12's state series
--------------------------------------------------------------
SOCO-12 committed the EIA *delivered to electric power* state series
(``N3045{AL,GA,MS}3``) and said explicitly that what SOCO-32 does about its gap
is "a declared modelling choice in its own derivation". This is that
declaration, and it rests on rule 14 ``[R-ACCURATE]`` with two measured
reasons — neither of which is a residual:

1. **The state boundary is NOT the zone boundary for SOCO_AL.** Card S3's zone
   map puts the six SERC **Florida-panhandle** plants in ``SOCO_AL`` (they
   interconnect west). Two of them burn gas — Gulf Clean Energy Center and
   Lansing Smith, **54.3 TBtu/yr, 22 % of the zone's gas burn** — and they pay a
   basis of **+1.77 / +1.77 / +1.63** $/MMBtu against the Alabama plants'
   **+0.70 / +0.60 / +0.56**, a persistent ~$1.10 premium on a different
   delivered market. An Alabama state series cannot see them at all, so it
   understates the zone's gas cost by ~$0.40/MMBtu every year. This is exactly
   the "defined on a different boundary than our zones" case rule 14 names, and
   the accurate input is the zone's own plants.
2. **The state series does not cover the backcast.** EIA publishes nothing for
   **GA or MS after 2024-12** (SOCO-12 §4), so a state-series table would stop
   at 2024 and hand 2025 either a missing row — no basis for the third backcast
   year — or, worse, an AL-only row that lets GA and MS default to 0.0 and
   fabricates a ~$0.75/MMBtu spread out of a publication gap. That is the trap
   SPP-32 refused for the same reason. EIA-923 covers all three zones through
   2025.

And where the two routes CAN be compared they agree. For ``SOCO_GA`` and
``SOCO_MS`` — the two zones whose boundary really is the state line — the
per-plant basis lands within **0.04 $/MMBtu** of the state series once the
series' ``$/Mcf`` is converted at EIA's pipeline-quality heat content
(1.037 MMBtu/Mcf):

    SOCO_GA 2023  0.539 vs 0.582   |  2024  0.706 vs 0.672
    SOCO_MS 2023  0.166 vs 0.193   |  2024  0.393 vs 0.422

``--cross-check`` re-derives that table. Note in passing that it also settles the
unit question the sibling tables leave open: the *converted* series is the one
that matches, so the raw ``$/Mcf``-minus-``$/MMBtu`` convention those tables use
carries a ~3.5 % level bias. EIA-923 is natively ``$/MMBtu`` and needs no
conversion at all, which is a third reason to prefer it.

Construction (one rule, no per-zone or per-year choices)::

    price_z,m   = SUM_p price_{p,m} * quantity_{p,m} / SUM_p quantity_{p,m}
    basis_z,y   = mean over the 12 months m of ( price_z,m - HenryHub_m )

Quantity-weighting **within** a month is what the zone actually paid that month;
averaging the twelve monthly *basis* values **equally** is the month-balanced
convention every sibling table uses, so a heavy-burn winter cannot pull the
annual level toward the winter basis. Henry Hub is the committed
``data/raw/gas-prices/henry_hub_monthly.csv``. Plants are assigned to zones by
``zone_assignment.build_zone_lookup("SOCO")`` — the ruled card-S3 FIPS-state
partition, the same key the fleet, the load shares and the solar shape use.

Nothing here is fitted to any residual (there is none — SOCO has no keeper), and
the LEVEL never reaches a solve anyway: the mean-zero applier re-centres to a
gas-capacity-weighted mean of zero (the PJM/MISO/CAISO/ERCOT convention), so
only the measured cross-zonal spread could ever move dispatch.

**No applier is armed for SOCO.** This lane lands a measured table and a
registered filename, not a mechanism: registering the path constant adds no
``ScenarioConfig`` field and moves no cache key (plan §7 gate **G8**). Arming it
is SOCO-40's or a later lever's call.

Run:
    python scripts/data/derive_soco_zonal_gas_hub.py [--dry-run] [--cross-check]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402

ISO = "SOCO"
OUT_PATH: Path = RAW_DATA_DIR / "soco_zonal_gas_hub.csv"
EIA923_PATH: Path = (
    RAW_DATA_DIR / "_processed-legacy" / "eia923_monthly_fuel_costs.parquet"
)
HENRY_HUB_PATH: Path = RAW_DATA_DIR / "gas-prices" / "henry_hub_monthly.csv"
GAS_PRICES_DIR: Path = RAW_DATA_DIR / "gas-prices"
YEARS: tuple[int, ...] = (2023, 2024, 2025)
FUEL_GROUP = "Natural Gas"

# EIA's pipeline-quality heat content, used ONLY by --cross-check to put
# SOCO-12's ``$/Mcf`` state series on the ``$/MMBtu`` footing EIA-923 already
# has. No committed value depends on it.
MMBTU_PER_MCF: float = 1.037

# The transport system each zone's delivered price sits on. Documentation
# carried on the row, sourced from SOCO-12's document sweep, NOT a quoted index
# (the module docstring's first section: no free Southeast index exists):
#   * Southern Natural Gas (SNG) is the system-wide transporter and Southern
#     Company Gas holds a 50 % equity interest in it (10-K FY2025 Item 1);
#   * Transco reaches northwest Georgia through the jointly-owned Dalton
#     Pipeline, a 115-mile Transco extension leased through 2042 (10-K Item 2
#     note (e)).
# SOCO_AL is labelled MIXED rather than resolved to its larger half, the NWPP
# convention for the same situation: the FL-panhandle plants are a fifth of the
# zone's burn at a ~$1.10/MMBtu premium, so the zone average describes neither
# half on its own. Splitting the zone is a topology change and owner-ruled
# territory (card S3), not this lane's to make; the caveat is declared instead.
ZONE_HUB: dict[str, str] = {
    "SOCO_AL": (
        "MIXED: Southern Natural Gas / Transco Zone 4 (AL) + FL-panhandle "
        "delivered (20-25% of the zone's burn; the year's exact share is in "
        "the source note)"
    ),
    "SOCO_GA": "Southern Natural Gas / Transco Zone 4 (GA, Dalton lateral)",
    "SOCO_MS": "Southern Natural Gas / Transco Zone 4 (MS)",
}

SOURCE_TEMPLATE = (
    "EIA-923 Schedule 2 per-plant delivered natural-gas price "
    "(data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet), "
    "quantity-weighted across the zone's plants within each month, minus the "
    "Henry Hub monthly mean; month-balanced over {months} monthly observations "
    "from {plants} plant(s). Zone assignment: the ruled card-S3 FIPS-state map "
    "(zone_assignment.build_zone_lookup('SOCO')). Derived by "
    "scripts/data/derive_soco_zonal_gas_hub.py (lane SOCO-32); see "
    "data/raw/soco_zonal_gas_hub.SOURCES.md{note}"
)
AL_MIX_NOTE = (
    " -- NOTE: this zone spans two delivered markets. Its Alabama plants pay "
    "{al:.3f} and its two FL-panhandle plants (Gulf Clean Energy Center, "
    "Lansing Smith; {fl_share:.0%} of the zone's {year} gas burn) pay "
    "{fl:.3f} $/MMBtu over Henry Hub. Both are REAL and neither is removed; the "
    "row is their burn-weighted blend"
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
    frame = _zone_plant_months()
    grouped = (
        frame.groupby(["zone", "year", "month"])
        .apply(
            lambda d: pd.Series(
                {
                    "price": float(
                        np.average(d["price_per_mmbtu"], weights=d["quantity"])
                    ),
                    "plants": int(d["plant_id"].nunique()),
                    "quantity": float(d["quantity"].sum()),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    henry = _henry_hub()
    grouped["hh"] = [
        float(henry.loc[(int(r.year), int(r.month))]) for r in grouped.itertuples()
    ]
    return grouped


def _zone_plant_months() -> pd.DataFrame:
    """Return the zone-tagged EIA-923 gas rows for the covered years."""
    for path in (EIA923_PATH, HENRY_HUB_PATH):
        if not path.exists():
            raise FileNotFoundError(f"required committed source missing: {path}")
    lookup = build_zone_lookup(ISO)
    frame = pd.read_parquet(EIA923_PATH)
    frame = frame[frame["fuel_group"] == FUEL_GROUP].copy()
    frame["zone"] = frame["plant_id"].map(lookup)
    return frame[
        frame["zone"].notna()
        & frame["year"].isin(YEARS)
        & frame["price_per_mmbtu"].notna()
        & (frame["quantity"] > 0)
    ]


def _henry_hub() -> pd.Series:
    """Return the committed Henry Hub monthly series indexed by (year, month)."""
    return pd.read_csv(HENRY_HUB_PATH).set_index(["year", "month"])["price_usd_mmbtu"]


def _soco_al_split(year: int) -> tuple[float, float, float] | None:
    """Return ``(alabama_basis, florida_basis, florida_burn_share)`` for a year.

    The number behind :data:`AL_MIX_NOTE`. ``None`` when the zone carries no
    Florida rows in that year (which would make the note vacuous).
    """
    frame = _zone_plant_months()
    frame = frame[(frame["zone"] == "SOCO_AL") & (frame["year"] == year)]
    if frame.empty:
        return None
    plants = pd.read_parquet(RAW_DATA_DIR / "eia-860" / "eia860_plant.parquet")[
        ["Plant Code", "State"]
    ].rename(columns={"Plant Code": "plant_id"})
    frame = frame.merge(plants, on="plant_id", how="left")
    florida = frame["State"] == "FL"
    if not florida.any() or florida.all():
        return None
    henry = _henry_hub()

    def _basis(sub: pd.DataFrame) -> float:
        monthly = sub.groupby("month").apply(
            lambda d: float(np.average(d["price_per_mmbtu"], weights=d["quantity"])),
            include_groups=False,
        )
        return float(
            np.mean(
                [px - float(henry.loc[(year, int(m))]) for m, px in monthly.items()]
            )
        )

    share = float(frame.loc[florida, "quantity"].sum() / frame["quantity"].sum())
    return _basis(frame[~florida]), _basis(frame[florida]), share


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
            if zone == "SOCO_AL":
                split = _soco_al_split(year)
                if split is not None:
                    note = AL_MIX_NOTE.format(
                        al=split[0], fl=split[1], fl_share=split[2], year=year
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


def cross_check() -> None:
    """Print the per-plant basis beside SOCO-12's state series. CHANGES NOTHING.

    The evidence for this derive's route choice (module docstring): where the
    zone boundary really is the state line the two agree, and where it is not
    (``SOCO_AL``, which carries the FL panhandle) they cannot.
    """
    henry = _henry_hub()
    print("\n=== route cross-check: EIA-923 per-plant vs SOCO-12's state series ===")
    print(
        "  zone/state    year   923 basis   state($/Mcf)  state(conv)   923-conv   "
        "months"
    )
    months = load_zone_months()
    for zone, state in (("SOCO_AL", "AL"), ("SOCO_GA", "GA"), ("SOCO_MS", "MS")):
        path = GAS_PRICES_DIR / f"eia_delivered_gas_{state}_monthly_2023-2025.csv"
        if not path.exists():
            print(f"  {zone:12s} state series absent ({path.name})")
            continue
        series = pd.read_csv(path)
        series["year"] = series["period"].str[:4].astype(int)
        series["month"] = series["period"].str[5:7].astype(int)
        series["value"] = pd.to_numeric(series["value"], errors="coerce")
        series = series[series["value"].notna()]
        for year in YEARS:
            own = months[(months["zone"] == zone) & (months["year"] == year)]
            state_year = series[series["year"] == year]
            own_basis = (
                float((own["price"] - own["hh"]).mean()) if not own.empty else np.nan
            )
            if state_year.empty:
                print(
                    f"  {zone:12s} {year}   {own_basis:9.3f}   "
                    f"{'NOT PUBLISHED':>27s}{'':>12s}{0:>8d}"
                )
                continue
            hh_year = np.array(
                [
                    float(henry.loc[(year, int(m))])
                    for m in state_year["month"].to_numpy()
                ]
            )
            raw = float((state_year["value"].to_numpy() - hh_year).mean())
            conv = float(
                (state_year["value"].to_numpy() / MMBTU_PER_MCF - hh_year).mean()
            )
            print(
                f"  {zone:12s} {year}   {own_basis:9.3f}   {raw:12.3f}  "
                f"{conv:11.3f}  {own_basis - conv:+9.3f}   {len(state_year):5d}"
            )


def report(months: pd.DataFrame, rows: list[dict[str, object]]) -> None:
    """Print the table and the equal-weight mean-zero spread.

    The LEVEL of these rows never reaches a solve — the mean-zero applier
    re-centres them — so the number a reader should judge is the re-centred
    cross-zonal spread, printed here beside the raw basis.
    """
    zone_names = get_iso_config(ISO).zone_names
    print(f"\n=== {ISO} per-zone gas basis vs Henry Hub ($/MMBtu) ===")
    table = {(r["zone"], r["year"]): r["basis_vs_hh_usd_mmbtu"] for r in rows}
    print("  {:12s}".format("zone") + "".join(f"{y:>10d}" for y in YEARS))
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
    parser.add_argument(
        "--cross-check",
        action="store_true",
        help="also print the per-plant basis beside SOCO-12's state series",
    )
    args = parser.parse_args(argv)
    months = load_zone_months()
    rows = build_rows(months)
    report(months, rows)
    if args.cross_check:
        cross_check()
    if args.dry_run:
        print(f"\n  (dry run — {OUT_PATH} not written)")
        return 0
    write_csv(rows, OUT_PATH)
    print(f"\n  wrote {OUT_PATH} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
