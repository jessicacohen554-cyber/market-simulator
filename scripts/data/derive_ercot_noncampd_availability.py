"""Derive per-plant availability for the CAMPD-blind ERCOT gas fleet (ERCOT-71).

The ERCOT-70 supply-mix decomposition named the moderate-tightness
under-priced hours' phantom cheap supply as +1.2-1.7 GW of CC_REGULAR
concentrated in a handful of ERCOT gas plants that carry ZERO rows in the
TX CAMPD (CEMS) extract — Kiamichi 55501 (OK-sited/switchable, outside the
TX state extract), Hidalgo 55545, Arthur Von Rosenberg 7512, EG178 56233
(all ``has_campd_data=False``). The model's measured availability stack is
structurally BLIND to them: the CAMPD-derived unit-outage overlay
(``data.outages.outage_masks_for_year`` / ``unit_outage_derate_factors``)
has no CEMS rows to build windows from, so these plants ride flat statistical
WEFOR/POF availability — the model dispatches Hidalgo 434-499 MW on every
May-2024 target window while EIA-923 shows it generated 0.0 MWh in all of
April+May 2024, and it runs Kiamichi at ~full 1,224 MW while ERCOT's own
day-ahead disclosure shows Kiamichi only 0.30-0.44 available to ERCOT in
April/May (it commits its two trains to SPP).

This derive restores their measured availability from two composed measured
identifications, ONE per plant (rule 19):

(a) 60-Day DAM disclosure PER-PLANT live availability -- the primary signal
    for the plants unambiguously identifiable in the disclosure
    (``ercot_noncampd_dam_crosswalk.csv``: Kiamichi, Hidalgo, AVR). Per plant
    settlement point the 10-config offer resources are collapsed to the
    physical train (max non-OUT HSL per settlement-point-hour; an ``OUT``
    resource contributes zero -- ERCOT marks a switchable unit OUT when it
    serves SPP), and Kiamichi's two parallel trains (``KMCHI_CC1`` +
    ``KMCHI_CC2``) are SUMMED across settlement points (never max-collapsed --
    they run simultaneously). ``avail(plant, day) = live_MW(day) / rating``,
    rating = Sigma_SP p98 of the SP's config-collapsed non-OUT HSL. This is the
    per-plant grain of ``derive_ercot_thermal_dam_availability.py`` (the
    ERCOT-67 class-day series), same source family and admissibility, and it
    measures Kiamichi's switchable ERCOT-share directly.

(b) EIA-923 zero-generation MONTHS -> full-plant outage windows, for any
    CAMPD-blind gas plant NOT covered by the disclosure crosswalk (the coarse
    backstop). A month a plant PRESENT in EIA-923 generated ZERO net MWh is a
    physical availability event; NON-zero months are left at the statistical
    availability (a ZERO-MONTH identification, never a monthly-level pin --
    rule 14).

Admissibility (rules 12/13/14/23/24):
* Both sources are published, measured, plant-keyed physical/market
  availability quantities -- never a price, never the model's own output.
* The CAMPD-blind plant set is DERIVED programmatically (model gas plants
  absent from the TX CAMPD extract), never a hardcoded per-plant list
  (rule 24). The disclosure resource->plant crosswalk is an auditable
  reference artifact with provenance (QSE + substation + EIA-860 county),
  not a tuning channel.
* Scoped to blind plants only so the CAMPD overlay stays the SOLE availability
  mechanism for the covered fleet (rule 19, surgical scope).
* Backcast overlay behind the mode-aware seam (the statistical stack is the
  forward analogue); forecast years age the fleet on their EIA-860 dates.
* FROZEN against residuals (rule 23): re-derive ONLY when the 60-Day DAM
  disclosure, EIA-923, the TX CAMPD extract, or the model fleet vintage
  updates -- never because a residual moved.

Usage::

    python scripts/data/derive_ercot_noncampd_availability.py [--years 2023 2024 2025]
        [--out data/raw/ercot-noncampd-availability.csv]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

EIA923_MONTHLY = (
    REPO / "data" / "raw" / "_processed-legacy" / "eia923_monthly_generation.parquet"
)
CROSSWALK_CSV = REPO / "data" / "raw" / "reference" / "ercot_noncampd_dam_crosswalk.csv"
DAM_DIR = REPO / "data" / "raw" / "ercot"
DEFAULT_OUT = REPO / "data" / "raw" / "ercot-noncampd-availability.csv"

_MONTH_COLS = [
    f"netgen_{m}_mwh"
    for m in (
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    )
]
# Model gas plant groups (the classes the CAMPD outage overlay would otherwise
# carry). Blind plants in these groups are the leg-A scope.
_GAS_PREFIXES = ("CC_", "CT_", "ST_")
_ZERO_TOL = 1.0  # MWh: |monthly net gen| below this is a zero-generation month
_RATING_QUANTILE = 0.98  # robust settlement-point rating: p98 of non-OUT HSL
_AVAIL_EMIT_MAX = 0.98  # emit a disclosure daily row only where it derates
_DAM_CC_TYPES = ("CCGT90", "CCLE90")


def _load_crosswalk() -> dict[int, list[str]]:
    """Return ``{plant_code: [settlement_point, ...]}`` from the reference CSV."""
    if not CROSSWALK_CSV.exists():
        return {}
    df = pd.read_csv(CROSSWALK_CSV)
    return {
        int(r.plant_code): [s.strip() for s in str(r.dam_settlement_points).split(";")]
        for r in df.itertuples(index=False)
    }


def _blind_gas_plants(year: int) -> dict[int, tuple[str, str]]:
    """Return ``{plant_code: (plant_name, plant_group)}`` for model gas plants
    with ZERO rows in the TX CAMPD extract for ``year`` (the CAMPD-blind set).

    The model fleet is authoritative for which plants are dispatched and their
    class; the TX CAMPD hourly extract is authoritative for which plants the
    CEMS-derived outage overlay can see. The set difference (gas plants in the
    fleet, absent from CAMPD) is exactly the availability blind spot.
    """
    iso = get_iso_config("ERCOT")
    gens = load_fleet_from_csv("ERCOT", iso, year=year)
    gas: dict[int, tuple[str, str]] = {}
    for g in gens:
        grp = str(g.plant_group or "")
        pc = int(g.plant_code)
        if pc > 0 and grp.startswith(_GAS_PREFIXES):
            gas.setdefault(pc, (str(getattr(g, "plant_name", "") or ""), grp))
    campd_df = campd.load_campd_hourly(["TX"], [year])
    campd_plants = set(int(p) for p in campd_df["plant_id"].unique())
    return {pc: meta for pc, meta in gas.items() if pc not in campd_plants}


def _load_disclosure_cc(year: int) -> pd.DataFrame:
    """Return CC 60-Day DAM disclosure rows delivered in ``year``.

    Both ``<year>`` and ``<year+1>`` files are scanned (the 60-day publication
    lag spills Nov-Dec deliveries into the next year's first file) and filtered
    on the Delivery Date column.
    """
    cols = [
        "Delivery Date",
        "Hour Ending",
        "Resource Type",
        "Settlement Point Name",
        "HSL",
        "Resource Status",
    ]
    frames: list[pd.DataFrame] = []
    for y in (year, year + 1):
        for p in sorted(
            DAM_DIR.glob(
                f"60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{y}_*.parquet"
            )
        ):
            d = pd.read_parquet(p, columns=cols)
            d = d[d["Resource Type"].isin(_DAM_CC_TYPES)]
            dt = pd.to_datetime(d["Delivery Date"])
            d = d[dt.dt.year == year]
            if not d.empty:
                frames.append(d)
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)


def _disclosure_daily_availability(
    disc: pd.DataFrame, settlement_points: list[str]
) -> pd.Series | None:
    """Return a ``date -> availability`` Series for one plant, or ``None``.

    Per settlement point the 10-config offer resources are collapsed to the
    physical train (max non-OUT HSL per settlement-point-hour; ``OUT`` -> 0),
    the SP rating is the p98 of its config-collapsed non-OUT non-zero HSL, live
    capability is clipped at that rating, and the plant is the SUM across
    settlement points (so a two-train site like Kiamichi is summed, never
    max-collapsed). ``avail = plant_live_MW(day) / plant_rating``, clipped
    [0, 1].
    """
    sub = disc[disc["Settlement Point Name"].isin(settlement_points)].copy()
    if sub.empty:
        return None
    sub["HSL"] = pd.to_numeric(sub["HSL"], errors="coerce")
    sub["date"] = pd.to_datetime(sub["Delivery Date"]).dt.normalize()
    sub["out"] = sub["Resource Status"].astype(str).eq("OUT")
    sub["hsl_live"] = np.where(sub["out"], 0.0, sub["HSL"])
    keys = ["Settlement Point Name", "date", "Hour Ending"]
    # Config-collapse WITHIN each settlement point (max over configs per hour).
    live_sph = sub.groupby(keys)["hsl_live"].max()
    ok = sub[~sub["out"] & (sub["HSL"] > 0.0)]
    if ok.empty:
        return None
    rating_sp = (
        ok.groupby(keys)["HSL"]
        .max()
        .groupby("Settlement Point Name")
        .quantile(_RATING_QUANTILE)
    )
    live_sph = np.minimum(
        live_sph, rating_sp.reindex(live_sph.index.droplevel([1, 2])).to_numpy()
    )
    live_spd = live_sph.groupby(["Settlement Point Name", "date"]).mean()
    live_pd = live_spd.groupby("date").sum()
    rating_plant = float(rating_sp.sum())
    if rating_plant <= 0.0:
        return None
    return (live_pd / rating_plant).clip(0.0, 1.0)


def _zero_month_windows(
    plant_code: int, name: str, group: str, year: int, e923: pd.DataFrame
) -> list[dict]:
    """Return merged EIA-923 zero-month outage windows for one plant.

    Only fires when the plant is PRESENT in EIA-923 for ``year`` (a missing
    plant row is a data-coverage gap, NOT a measured zero -> skipped, so the
    statistical availability stands). Consecutive zero months merge into a
    single window ``[first-of-first-month, first-of-(last-month+1)]`` (the
    ``outage_end`` is the exclusive return-to-service instant, matching
    ``data.outages.outage_hour_mask``).
    """
    sub = e923[(e923["plant_id"] == plant_code) & (e923["year"] == year)]
    if sub.empty:
        return []
    monthly = [float(sub[c].sum()) for c in _MONTH_COLS]
    zero_months = [m for m in range(1, 13) if abs(monthly[m - 1]) < _ZERO_TOL]
    if not zero_months:
        return []
    rows: list[dict] = []
    run_start: int | None = None
    prev: int | None = None
    for m in zero_months + [None]:  # sentinel flushes the last run
        if run_start is None:
            run_start, prev = m, m
            continue
        if m == prev + 1:
            prev = m
            continue
        end_month = prev + 1
        end_year = year + (1 if end_month > 12 else 0)
        end_month = 1 if end_month > 12 else end_month
        rows.append(
            {
                "year": year,
                "plant_code": plant_code,
                "plant_name": name,
                "plant_group": group,
                "outage_start": f"{year}-{run_start:02d}-01",
                "outage_end": f"{end_year}-{end_month:02d}-01",
                "avail": 0.0,
                "source": "eia923_zero_month",
            }
        )
        run_start, prev = m, m
    return rows


def _disclosure_windows(
    plant_code: int, name: str, group: str, year: int, avail: pd.Series
) -> list[dict]:
    """Daily availability rows (one per DERATED day) for a disclosure plant."""
    rows: list[dict] = []
    for d, a in avail.items():
        if not np.isfinite(a) or a >= _AVAIL_EMIT_MAX:
            continue  # full-availability day: statistical stands (no cap needed)
        day = pd.Timestamp(d)
        rows.append(
            {
                "year": year,
                "plant_code": plant_code,
                "plant_name": name,
                "plant_group": group,
                "outage_start": day.strftime("%Y-%m-%d"),
                "outage_end": (day + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                "avail": round(float(a), 4),
                "source": "dam_disclosure",
            }
        )
    return rows


def derive_year(
    year: int,
    e923: pd.DataFrame,
    blind: dict[int, tuple[str, str]],
    crosswalk: dict[int, list[str]],
) -> list[dict]:
    """Return all leg-A availability rows for one delivery year.

    Scoped to the disclosure-crosswalk plants ONLY (the ERCOT-70-named blind CC
    phantoms — Kiamichi, Hidalgo, AVR), so the CAMPD overlay stays the sole
    availability mechanism for every other plant (rule 19, surgical scope; a
    blanket EIA-923 zero-month rule over the ~180 blind gas plants wrongly
    zeroes out-of-merit peakers whose zero months are economic, not outages).
    Each crosswalk plant gets TWO composed measured signals, min-combined by the
    reader: (a) per-plant DAM daily availability (primary; captures partial
    derates like Kiamichi's switchable ERCOT-share), (b) an EIA-923 zero-month
    backstop (guards any disclosure-coverage hole). A crosswalk plant that is
    NOT blind in a given year (it gained CAMPD rows) is skipped — the CAMPD
    overlay owns it.
    """
    rows: list[dict] = []
    disc = _load_disclosure_cc(year) if crosswalk else pd.DataFrame()
    for pc, sps in sorted(crosswalk.items()):
        if pc not in blind:
            continue  # has CAMPD rows this year -> CAMPD overlay owns it (rule 19)
        name, grp = blind[pc]
        avail = _disclosure_daily_availability(disc, sps)
        if avail is not None:
            rows += _disclosure_windows(pc, name, grp, year, avail)
        rows += _zero_month_windows(pc, name, grp, year, e923)  # backstop
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    e923 = pd.read_parquet(EIA923_MONTHLY)
    crosswalk = _load_crosswalk()
    print(f"disclosure crosswalk: {sorted(crosswalk)}")
    rows: list[dict] = []
    for y in args.years:
        blind = _blind_gas_plants(y)
        yr_rows = derive_year(y, e923, blind, crosswalk)
        rows += yr_rows
        disc_pc = sorted(pc for pc in blind if pc in crosswalk)
        n_disc = len(
            {r["plant_code"] for r in yr_rows if r["source"] == "dam_disclosure"}
        )
        n_zero = sum(1 for r in yr_rows if r["source"] == "eia923_zero_month")
        print(
            f"{y}: {len(blind)} CAMPD-blind gas plant(s); disclosure plants "
            f"{disc_pc} ({n_disc} covered); {len(yr_rows)} row(s) "
            f"({n_zero} EIA-923 zero-month window(s))"
        )
        # per-plant monthly availability summary (disclosure plants)
        for pc in disc_pc:
            pr = [r for r in yr_rows if r["plant_code"] == pc]
            if pr and pr[0]["source"] == "dam_disclosure":
                by_mo: dict[int, list[float]] = {}
                for r in pr:
                    by_mo.setdefault(pd.Timestamp(r["outage_start"]).month, []).append(
                        r["avail"]
                    )
                mo = {m: round(float(np.mean(v)), 2) for m, v in sorted(by_mo.items())}
                print(
                    f"    {pc} {pr[0]['plant_name'][:24]:<24} derated-day avail by mo: {mo}"
                )
    cols = [
        "year",
        "plant_code",
        "plant_name",
        "plant_group",
        "outage_start",
        "outage_end",
        "avail",
        "source",
    ]
    df = pd.DataFrame(rows, columns=cols).sort_values(
        ["year", "plant_code", "outage_start"]
    )
    args.out.write_text(df.to_csv(index=False))
    print(f"wrote {args.out} ({len(df)} row(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
