"""Derive ERCOT measured class-day thermal availability from the 60-Day DAM disclosure.

The thermal-fleet analogue of ``derive_ercot_nuclear_availability.py`` (ERCOT-56),
at CLASS-day grain: for each covered model class (CC_REGULAR, CT_PEAKER, ST_GAS)
and each delivery day, the DAM-registered fleet's measured availability fraction

    avail(class, day) = sum_sites live_HSL(day) / sum_sites rating

where a combined-cycle plant's alternative registered configurations are
config-collapsed to physical trains (a site's live capability is the max
non-OUT config HSL; its rating the max config rating), an ``OUT`` resource
contributes zero, and an ``OFF`` (uncommitted but startable) resource
contributes its reported HSL — commitment state is not an availability event.
``rating`` is the site's 98th-percentile HSL across its non-OUT, non-zero rows
of the delivery year (robust to jack-bus zeros and one-off test values).

Provenance / admissibility (CLAUDE.md rules 13/14): the 60-Day DAM disclosure
Gen_Resource HSL + Resource Status is an ERCOT-published, unit-resolved MW
capability quantity — a physical/market availability measurement, never a
price. The June/Sep-2023 scarcity-formation forensics
(docs/DIAGNOSIS-ercot-june2023-scarcity-formation-2026-07.md) measured the
statistical WEFOR/EFOR stack carrying the gas fleet 13-22 % derated at the
summer-evening reserve margin while this disclosure shows the same fleet at
~97 % of ratings — the phantom reserve-shortfall that over-formed June-2023
(+22 %) and Sep-2023 (+15/19 %) prices. In backcast mode the measured class-day
fraction REPLACES (by rescale, not stacking) the statistical estimate of the
same quantity; the model's own discrete outage windows stay as the within-class
distribution. Forecast years keep the statistical stack — the expected-value
analogue that regenerates from forward drivers (the G4 mode-aware seam).

**Class scope (rule 14 alignment).** The covered classes are the grid-registered
gas fleet DAM resolves cleanly by ``Resource Type``: CC (CCGT90/CCLE90),
CT_PEAKER (SCGT90/SCLE90) and — added 2026-07-18, the measured-availability
backcast re-architecture — ST_GAS (the gas-steam types GSREH/GSSUP/GSNONR). The
DAM disclosure carries no CHP flag, and the private-use-network cogens are
partly behind-the-meter / absent from the disclosure, so a DAM class fraction
would MISSTATE the CHP classes (CC_CHP/CT_CHP/ST_CHP) — those keep the measured
CAMPD unit-outage windows + the ``wefor_residual`` short-outage residual instead
(the mode-aware measured stack, no statistical WEFOR, but not a DAM smear).
COAL is likewise excluded: its few large lignite units are already carried at
unit grain by the CAMPD windows, where a class-day smear would misplace which
unit is out. So this file covers exactly {CC_REGULAR, CT_PEAKER, ST_GAS}.

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the disclosure source
files update; never because a residual moved. Re-derivation commits must cite
the data change. (The 2026-07-18 ST_GAS addition is a CLASS-SCOPE change, not a
residual re-fit — the source files are unchanged; it widens coverage to the
gas-steam class the measured-availability backcast re-architecture now sources
from DAM.)

Usage::

    python scripts/data/derive_ercot_thermal_dam_availability.py \
        [--years 2023 2024 2025] [--out data/raw/ercot-thermal-dam-availability.csv]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DAM_DIR = REPO / "data" / "raw" / "ercot"
DEFAULT_OUT = REPO / "data" / "raw" / "ercot-thermal-dam-availability.csv"

# DAM Resource Type -> covered model class. Scope covers the grid-registered gas
# fleet DAM resolves cleanly by Resource Type: CC (CCGT90/CCLE90), CT_PEAKER
# (SCGT90/SCLE90) and ST_GAS (the gas-steam types GSREH/GSSUP/GSNONR — added
# 2026-07-18 with the measured-availability backcast re-architecture, replacing
# the ST_GAS statistical WEFOR with its measured DAM class-day availability;
# ST_GAS's drag-floor structure governs its DISPATCH shape, not its top-line
# availability, so the measured availability and the drag mask are orthogonal —
# rule 19 one-mechanism-per-phenomenon is preserved). Deliberately excludes the
# CHP classes (the disclosure carries no CHP flag and its private-use-network
# cogens are partly behind-the-meter, so a DAM class fraction would misstate
# them — they keep CAMPD windows + wefor_residual; rule 14), coal (its few large
# lignite units are carried at unit grain by the CAMPD windows, where a class
# smear would misplace which unit is out), oil/DSL (trivial MW), and nuclear
# (its own measured overlay, ercot_nuclear_unit_availability).
RESTYPE_TO_CLASS: dict[str, str] = {
    "CCGT90": "CC_REGULAR",
    "CCLE90": "CC_REGULAR",
    "SCGT90": "CT_PEAKER",
    "SCLE90": "CT_PEAKER",
    "GSREH": "ST_GAS",
    "GSSUP": "ST_GAS",
    "GSNONR": "ST_GAS",
}

# CC configuration suffixes: a resource name up to the config tag names the
# physical train ("site"); alternates never run together (config-collapse —
# the May-2024 outage-forensics recipe, DIAGNOSIS-ercot-may2024 §2).
_CC_CONFIG_TAGS = ("_CC", "_CCU", "_GT", "_ST")

_RATING_QUANTILE = 0.98  # robust site rating: p98 of non-OUT, non-zero HSL


def _site(name: str, rtype: str) -> str:
    """Collapse a CC config resource name to its physical-train site key."""
    if rtype in ("CCGT90", "CCLE90"):
        for tag in _CC_CONFIG_TAGS:
            i = name.rfind(tag)
            if i > 0:
                return name[:i]
        return name.rsplit("_", 1)[0]
    return name  # simple-cycle resources are the physical unit


def _load_year(year: int) -> pd.DataFrame:
    """Read every Gen_Resource disclosure row whose DELIVERY date is ``year``.

    The 60-day publication lag spills a year's Nov-Dec deliveries into the
    following year's first file, so both ``<year>`` and ``<year+1>`` files are
    scanned and filtered on the Delivery Date column.
    """
    cols = [
        "Delivery Date",
        "Hour Ending",
        "Resource Name",
        "Resource Type",
        "HSL",
        "Resource Status",
    ]
    frames: list[pd.DataFrame] = []
    for y in (year, year + 1):
        for path in sorted(DAM_DIR.glob(f"*60d_DAM_Gen_Resource_Data_{y}_*.parquet")):
            df = pd.read_parquet(path, columns=cols)
            df = df[df["Resource Type"].isin(RESTYPE_TO_CLASS)]
            dt = pd.to_datetime(df["Delivery Date"])
            df = df[dt.dt.year == year]
            if not df.empty:
                frames.append(df)
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)


def derive_year(year: int) -> pd.DataFrame:
    """Return the class-day availability frame for one delivery year."""
    df = _load_year(year)
    if df.empty:
        return pd.DataFrame(columns=["date", "class", "rating_mw", "live_mw", "avail"])
    df["cls"] = df["Resource Type"].map(RESTYPE_TO_CLASS)
    df["site"] = [_site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])]
    df["date"] = pd.to_datetime(df["Delivery Date"]).dt.normalize()
    df["out"] = df["Resource Status"].eq("OUT")

    # Site rating: p98 of the site's config-collapsed hourly HSL over the
    # year's non-OUT, non-zero rows (max config HSL per site-hour first, so a
    # small alternate config cannot drag the train's rating down).
    ok = df[~df["out"] & (df["HSL"] > 0.0)]
    site_hour = ok.groupby(["cls", "site", "date", "Hour Ending"])["HSL"].max()
    rating = site_hour.groupby(["cls", "site"]).quantile(_RATING_QUANTILE)

    # Live capability per site-hour: max HSL across non-OUT configs (an OUT
    # config contributes zero; a fully-OUT site has no non-OUT rows -> 0).
    live = df.copy()
    live["hsl_live"] = np.where(live["out"], 0.0, live["HSL"])
    live_sh = live.groupby(["cls", "site", "date", "Hour Ending"])["hsl_live"].max()
    # Clip at the site rating so brief emergency/over-rating reads cannot push
    # a day's fraction above 1.
    live_sh = np.minimum(
        live_sh, rating.reindex(live_sh.index.droplevel([2, 3])).values
    )
    live_day = live_sh.groupby(["cls", "site", "date"]).mean()

    # Class-day totals over the sites present that day.
    live_cd = live_day.groupby(["cls", "date"]).sum()
    present = live_day.reset_index()[["cls", "site", "date"]]
    present["rating"] = rating.reindex(
        pd.MultiIndex.from_frame(present[["cls", "site"]])
    ).values
    rating_cd = present.groupby(["cls", "date"])["rating"].sum()

    out = pd.DataFrame(
        {
            "rating_mw": rating_cd.round(1),
            "live_mw": live_cd.reindex(rating_cd.index).round(1),
        }
    )
    out["avail"] = (out["live_mw"] / out["rating_mw"]).clip(0.0, 1.0).round(4)
    out = out.reset_index().rename(columns={"cls": "class"})
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out[["date", "class", "rating_mw", "live_mw", "avail"]]


def main() -> None:
    """Derive and write the class-day availability CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    frames = [derive_year(y) for y in args.years]
    out = pd.concat(frames, ignore_index=True).sort_values(["date", "class"])
    args.out.write_text(out.to_csv(index=False))
    for y in args.years:
        yr = out[out["date"].str.startswith(str(y))]
        for cls, g in yr.groupby("class"):
            print(
                f"{y} {cls}: {len(g)} days, avail p5/p50/p95 = "
                f"{g['avail'].quantile(0.05):.3f}/{g['avail'].median():.3f}/"
                f"{g['avail'].quantile(0.95):.3f}, rating ~{g['rating_mw'].median():.0f} MW"
            )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
