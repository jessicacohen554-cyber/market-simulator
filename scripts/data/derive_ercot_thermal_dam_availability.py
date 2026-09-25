"""Derive ERCOT measured thermal availability from the 60-Day DAM disclosure.

The thermal-fleet analogue of ``derive_ercot_nuclear_availability.py`` (ERCOT-56),
at TWO grains from the same source rows:

* CLASS-day (the original, ``--out``): for each covered model class
  (CC_REGULAR, CT_PEAKER, ST_GAS) and each delivery day, the DAM-registered
  fleet's measured availability fraction

      avail(class, day) = sum_sites live_HSL(day) / sum_sites rating

* CLASS-hour (``--hourly-out``, added ERCOT-96 2026-07-22): the same fraction
  per delivery HOUR (``Hour Ending`` 1-24),

      avail(class, day, he) = sum_sites live_HSL(day, he) / sum_sites rating

  keeping the hourly ambient-derate shape the day mean discards. The ERCOT-95
  diagnosis (docs/handoffs/ercot95-scarcity-tail-diagnosis-2026-07.md Finding
  6) measured the day-flat overlay handing the model a +216 MW mean (+433 p90,
  +578 max) CC+CT phantom on the 181 actual 2023 RT tail hours — real HSL dips
  below the day mean exactly in the hod 13-19 window where the missing tail
  sits (and exceeds it overnight). Same source, finer grain — a rule-13
  measured re-derive, not a new parameter (rule 23: this is a grain/schema
  extension; the disclosure source files are unchanged).

In both grains a combined-cycle plant's alternative registered configurations
are config-collapsed to physical trains (a site's live capability is the max
non-OUT config HSL; its rating the max config rating), an ``OUT`` resource
contributes zero, and an ``OFF`` (uncommitted but startable) resource
contributes its reported HSL — commitment state is not an availability event.
``rating`` is the site's 98th-percentile HSL across its non-OUT, non-zero rows
of the delivery year (robust to jack-bus zeros and one-off test values). The
hourly denominator counts the sites present at that (date, HE) so partial-hour
coverage (DST short day, a resource's missing rows) cannot bias the fraction
down; an entirely uncovered (date, HE) is emitted empty -> NaN -> the caller
keeps the statistical availability there, hour by hour.

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
thermal fleet DAM resolves cleanly by ``Resource Type``: CC (CCGT90/CCLE90),
CT_PEAKER (SCGT90/SCLE90), ST_GAS (the gas-steam types GSREH/GSSUP/GSNONR —
added 2026-07-18, the measured-availability backcast re-architecture) and —
added 2026-07-24, ERCOT-110 — COAL (the single coal/lignite type ``CLLIG``).
The DAM disclosure carries no CHP flag, and the private-use-network cogens are
partly behind-the-meter / absent from the disclosure, so a DAM class fraction
would MISSTATE the CHP classes (CC_CHP/CT_CHP/ST_CHP) — those keep the measured
CAMPD unit-outage windows + the ``wefor_residual`` short-outage residual instead
(the mode-aware measured stack, no statistical WEFOR, but not a DAM smear).

**Coal (ERCOT-110).** ``CLLIG`` is the ONE coal Resource Type the disclosure
publishes and it carries no fuel-BASIN attribute — and the ERCOT LP has no
basin-level coal class either: ``custom-bin-assignments.csv`` assigns the whole
coal fleet ``Plant_Group = COAL``, and ``bins_to_fleet`` puts that verbatim on
each ``Generator.plant_group`` (the COAL_PRB / COAL_LIGNITE split is applied
only at REPORTING time, from ``coal_supply_class``, in
``run_calibration_full._dispatch_frame``). Source grain and model grain
therefore agree exactly, and this file emits the single class ``COAL``. Emitting
the supply-rank split would be strictly worse than useless: the apply seam
matches ``g.plant_group == cls``, so a ``COAL_PRB`` key would match no
generator and the overlay would be SILENTLY INERT.

WHICH coal unit is derated is carried by the PLANT grain instead, keyed by EIA
plant code through the reviewed DAM-site -> EIA-plant crosswalk
(``ercot-dam-coal-site-seeds.csv`` -> ``ercot-dam-plant-crosswalk.csv``). All
26 coal sites (13.5 GW p98, 97 % of the model's 14.0 GW ERCOT coal nameplate)
crosswalk onto all 10 modelled coal plants, so the plant grain covers the coal
fleet with no unmapped residual — full allocation, zero smear.

The earlier exclusion rationale ("carried at unit grain by the CAMPD windows")
did not survive contact with the data: CAMPD windows are a >=5-day full-stop
detector and miss both the partial summer HSL derate and long single-unit
mothballs (W A Parish G8 reads OUT/zero for ~96 % of 2023 while the model
carries its 610 MW as fully available all year).

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the disclosure source
files update; never because a residual moved. Re-derivation commits must cite
the data change. (The 2026-07-18 ST_GAS addition and the 2026-07-24 COAL
addition are CLASS-SCOPE changes, not residual re-fits — the source files are
unchanged; each widens coverage to a class previously left on the statistical /
CAMPD stack.)

* SITE-hour (``--site-hourly-out``, added ERCOT-97 2026-07-22): the same
  config-collapsed live/rating intermediate emitted per (class, site, date,
  Hour Ending) — one row per physical train per delivery hour, columns
  ``live_mw`` (clipped live HSL) and ``rating_mw`` (the site p98 rating). This
  is the plant×hour input: the DAM-site -> EIA-plant crosswalk
  (``build_ercot_dam_resource_crosswalk.py``) maps accepted sites onto plant
  codes, and ``ercot_thermal_dam_availability_plant`` caps each crosswalked
  plant's tranches at its own measured site-hour fraction while the class-hour
  water-fill still lands the class total on the measured class fraction
  (redistribution, zero fitted parameters). Same source rows as the two class
  grains — a rule-13/23 grain extension, not a new parameter.

Usage::

    python scripts/data/derive_ercot_thermal_dam_availability.py \
        [--years 2023 2024 2025] [--out data/raw/ercot-thermal-dam-availability.csv] \
        [--hourly-out data/raw/ercot-thermal-dam-availability-hourly.csv] \
        [--site-hourly-out data/raw/ercot-thermal-dam-availability-site-hourly.parquet]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import (  # noqa: E402
    RAW_DATA_DIR,
    ercot_dam_disclosure_files,
)

DEFAULT_OUT = RAW_DATA_DIR / "ercot-thermal-dam-availability.csv"
DEFAULT_HOURLY_OUT = RAW_DATA_DIR / "ercot-thermal-dam-availability-hourly.csv"
DEFAULT_SITE_HOURLY_OUT = (
    RAW_DATA_DIR / "ercot-thermal-dam-availability-site-hourly.parquet"
)

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
# them — they keep CAMPD windows + wefor_residual; rule 14) and coal (CLLIG,
# added ERCOT-110 2026-07-24: the disclosure's single coal/lignite type mapped
# onto the model's single COAL plant_group — same grain on both sides; see the
# module docstring). Still excludes oil/DSL (trivial MW) and nuclear (its own
# measured overlay, ercot_nuclear_unit_availability).
RESTYPE_TO_CLASS: dict[str, str] = {
    "CCGT90": "CC_REGULAR",
    "CCLE90": "CC_REGULAR",
    "SCGT90": "CT_PEAKER",
    "SCLE90": "CT_PEAKER",
    "GSREH": "ST_GAS",
    "GSSUP": "ST_GAS",
    "GSNONR": "ST_GAS",
    # The disclosure's ONE coal/lignite type, onto the model's ONE coal
    # plant_group. Neither side carries a fuel basin at dispatch grain (the
    # COAL_PRB / COAL_LIGNITE split is reporting-only), so the mapping is
    # exact; the plant grain places WHICH coal unit is derated.
    "CLLIG": "COAL",
}

# CC resource-name grammar: ``<MNEMONIC>_<CCTAG><train#>_<config#>`` — one DAM
# row per registered CONFIGURATION of a physical train; alternates of one train
# never run together (config-collapse — the May-2024 outage-forensics recipe,
# DIAGNOSIS-ercot-may2024 §2). The site key is the TRAIN (``GUADG_CC1``), never
# the bare mnemonic: truncating at the config TAG aliased two physical trains
# (``GUADG_CC1_*`` + ``GUADG_CC2_*`` -> ``GUADG``) onto one site whose max()
# collapse made a single-train outage arithmetically invisible — owner ruling
# #9, repaired 2026-08-12 under signature A1 (ercot-149 §3.1/§6.1;
# docs/PRECOMMIT-ercot191-a1-dam-deriver-2026-08-12.md §1a). With train-grain
# sites the existing site-summing aggregations become the SUM of per-train
# maxes the diagnosis names. Verified against all 310 unique CC resource names
# across both disclosure lanes: every one matches _CC_TRAIN_RE.
_CC_TRAIN_RE = re.compile(r"^(?P<train>.+_(?:CC|CCU|GT|ST)\d*)_\d+$")
_CC_CONFIG_TAGS = ("_CC", "_CCU", "_GT", "_ST")

_RATING_QUANTILE = 0.98  # robust site rating: p98 of non-OUT, non-zero HSL


def _site(name: str, rtype: str) -> str:
    """Collapse a CC config resource name to its physical-train site key."""
    if rtype in ("CCGT90", "CCLE90"):
        m = _CC_TRAIN_RE.match(name)
        if m:
            return m.group("train")
        # Fallback for a name outside the corpus grammar (none observed):
        # the pre-ruling-#9 tag truncation.
        for tag in _CC_CONFIG_TAGS:
            i = name.rfind(tag)
            if i > 0:
                return name[:i]
        return name.rsplit("_", 1)[0]
    return name  # simple-cycle resources are the physical unit


def _load_year(year: int) -> pd.DataFrame:
    """Read every Gen_Resource disclosure row whose DELIVERY date is ``year``.

    The 60-day publication lag spills a year's Nov-Dec deliveries into the
    following year's first file, so both ``<year>`` and ``<year+1>`` LABEL
    years are scanned and filtered on the Delivery Date column. File
    resolution goes through :func:`paths.ercot_dam_disclosure_files`, which
    covers BOTH registered disclosure directories — the MIS-fetcher lane
    (``data/raw/ercot``, 2023-2026) and the annual-archive lane
    (``data/raw/ercot-AS``, 2018-2022) — so a delivery year is assembled from
    whichever lane published it (2022's Nov-Dec tail, for instance, comes from
    the MIS lane's label-2023 fragment while its Jan-Oct comes from the
    archive lane).
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
        for path in ercot_dam_disclosure_files("Gen_Resource_Data", y):
            df = pd.read_parquet(path, columns=cols)
            df = df[df["Resource Type"].isin(RESTYPE_TO_CLASS)]
            dt = pd.to_datetime(df["Delivery Date"])
            df = df[dt.dt.year == year]
            if not df.empty:
                frames.append(df)
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)


def _load_prep(year: int) -> pd.DataFrame:
    """:func:`_load_year` plus the derived ``cls``/``site``/``date``/``out`` columns."""
    df = _load_year(year)
    if df.empty:
        return df
    df["cls"] = df["Resource Type"].map(RESTYPE_TO_CLASS)
    df["site"] = [_site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])]
    df["date"] = pd.to_datetime(df["Delivery Date"]).dt.normalize()
    df["out"] = df["Resource Status"].eq("OUT")
    return df


def _inyear_rating(df: pd.DataFrame) -> pd.Series:
    """Per-(cls, site) p98 rating over the year's non-OUT, non-zero rows.

    Site rating: p98 of the site's config-collapsed hourly HSL (max config HSL
    per site-hour first, so a small alternate config cannot drag the train's
    rating down).
    """
    ok = df[~df["out"] & (df["HSL"] > 0.0)]
    site_hour = ok.groupby(["cls", "site", "date", "Hour Ending"])["HSL"].max()
    return site_hour.groupby(["cls", "site"]).quantile(_RATING_QUANTILE)


def derive_year(
    year: int, rating_fallback: "pd.Series | None" = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return the (class-day, class-hour, site-hour) availability frames.

    All three grains come from the SAME config-collapsed site-hour live/rating
    intermediate, so the hourly file's day mean reconciles with the day file
    up to the per-HE present-site denominator (an uncovered HE drops out of
    the day mean's numerator AND the hourly row entirely), and the site-hour
    frame is that intermediate itself — its per-(class, date, HE) live/rating
    sum over sites reproduces the class-hour fraction exactly.

    ``rating_fallback`` is the ruling-#8 multi-year rating basis (signature
    A1; ERCOT-148 §5.1/§6.2, PRECOMMIT-ercot191 §1c): a (cls, site) with NO
    in-year rating — every row of the delivery year OUT or zero-HSL — takes
    its rating from the fallback (built by :func:`derive_years` from the
    nearest other derived year), so an all-year-OUT site enters BOTH sides of
    every grain with live 0 instead of vanishing (Martin Lake U1 2025: COP
    ``OUT`` all 8,760 h @ 815 MW was invisible to the COAL fraction and the
    plant pin). In-year ratings always take precedence, so where the current
    basis produced a number the output is unchanged; a site with no non-OUT
    row in ANY derived year remains absent (nothing measurable to rate).
    """
    empty_day = pd.DataFrame(columns=["date", "class", "rating_mw", "live_mw", "avail"])
    empty_hr = pd.DataFrame(
        columns=["date", "class"] + [f"he{h:02d}" for h in range(1, 25)]
    )
    empty_sh = pd.DataFrame(
        columns=["date", "class", "site", "he", "live_mw", "rating_mw"]
    )
    df = _load_prep(year)
    if df.empty:
        return empty_day, empty_hr, empty_sh

    rating = _inyear_rating(df)
    if rating_fallback is not None and not rating_fallback.empty:
        rating = rating.combine_first(rating_fallback)

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
    day_frame = out[["date", "class", "rating_mw", "live_mw", "avail"]]

    # ------------------------------------------------------------- class-hour
    # Same intermediate, per-HE: numerator = sum of live site-HE MW; the
    # denominator counts only the sites PRESENT at that (date, HE) (a fully-OUT
    # site still carries rows, so it stays in the denominator with live 0; a
    # site with no row at that HE — DST short hour, a data gap — drops from
    # both sides so partial coverage cannot bias the fraction).
    sh = live_sh.rename("live").reset_index()
    sh["rating_site"] = rating.reindex(
        pd.MultiIndex.from_frame(sh[["cls", "site"]])
    ).values
    ch = sh.groupby(["cls", "date", "Hour Ending"])[["live", "rating_site"]].sum()
    ch["avail"] = (ch["live"] / ch["rating_site"]).clip(0.0, 1.0).round(4)
    wide = ch["avail"].unstack("Hour Ending")
    # HE 1-24 on the model clock; drop any out-of-range HE (a DST 25th hour
    # would arrive as HE 25 in some vintages — not observed in this corpus).
    wide = wide.reindex(columns=range(1, 25))
    wide.columns = [f"he{h:02d}" for h in wide.columns]
    wide = wide.reset_index().rename(columns={"cls": "class"})
    wide["date"] = wide["date"].dt.strftime("%Y-%m-%d")
    hour_frame = wide[["date", "class"] + [f"he{h:02d}" for h in range(1, 25)]]

    # ------------------------------------------------------------- site-hour
    # The plant×hour input (ERCOT-97): one row per physical train per delivery
    # hour, carrying the clipped live HSL and the site p98 rating. This is the
    # SAME ``sh`` intermediate the class-hour grain sums over sites — so a
    # crosswalked plant's Σ live_mw / Σ rating_mw over its mapped sites is the
    # plant's measured availability fraction, and the residual (unmapped) sites
    # still reconcile to the class-hour total. Emitted as parquet (one delivery
    # year is ~2.5 M rows; CSV would be ~150 MB/yr).
    site_frame = sh.rename(
        columns={
            "cls": "class",
            "Hour Ending": "he",
            "rating_site": "rating_mw",
            "live": "live_mw",
        }
    ).copy()
    site_frame["date"] = site_frame["date"].dt.strftime("%Y-%m-%d")
    site_frame["he"] = site_frame["he"].astype(int)
    site_frame["live_mw"] = site_frame["live_mw"].round(2)
    site_frame["rating_mw"] = site_frame["rating_mw"].round(2)
    site_frame = site_frame[(site_frame["he"] >= 1) & (site_frame["he"] <= 24)][
        ["date", "class", "site", "he", "live_mw", "rating_mw"]
    ].reset_index(drop=True)
    return day_frame, hour_frame, site_frame


def derive_years(
    years: list[int],
) -> list[tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    """Derive every year with the ruling-#8 cross-year rating fallback.

    Pass 1 computes each year's in-year (cls, site) rating; pass 2 derives
    each year with a fallback assembled from the OTHER years' in-year ratings,
    nearest year first (tie -> the earlier year: a destroyed unit's
    last-operating rating is the physical basis). In-year ratings always win
    (:func:`derive_year`), so the fallback engages only where the in-year
    basis is empty.
    """
    ratings: dict[int, pd.Series] = {}
    for y in years:
        df = _load_prep(y)
        ratings[y] = _inyear_rating(df) if not df.empty else pd.Series(dtype=float)
        del df
    triples: list[tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = []
    for y in years:
        fb: "pd.Series | None" = None
        for yy in sorted((o for o in years if o != y), key=lambda o: (abs(o - y), o)):
            r = ratings[yy]
            if r.empty:
                continue
            fb = r if fb is None else fb.combine_first(r)
        triples.append(derive_year(y, rating_fallback=fb))
    return triples


def main() -> None:
    """Derive and write the class-day + class-hour availability CSVs."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--hourly-out", type=Path, default=DEFAULT_HOURLY_OUT)
    ap.add_argument("--site-hourly-out", type=Path, default=DEFAULT_SITE_HOURLY_OUT)
    ap.add_argument(
        "--write-years",
        type=int,
        nargs="+",
        default=None,
        help="MERGE mode: derive over --years (the rating-fallback pool) but "
        "write only these years' rows, keeping every other year already in the "
        "outputs byte-frozen. Default (unset) keeps the historical behaviour of "
        "writing exactly --years, now also MERGED: rows of years outside "
        "--years are preserved instead of dropped. R-ERCOT-2 (2026-09-25): the "
        "former full-file REPLACE is how the 2018-2020 back-years recorded in "
        "calibration-complete.json's intake_log went missing from main.",
    )
    args = ap.parse_args()

    write_years = [int(y) for y in (args.write_years or args.years)]
    triples = derive_years(list(args.years))

    def _merge_csv(path: Path, new: pd.DataFrame) -> pd.DataFrame:
        """Keep existing rows of years not being written; replace the rest."""
        new = new[new["date"].str[:4].astype(int).isin(write_years)]
        if not path.exists():
            return new
        old = pd.read_csv(path)
        old = old[~old["date"].astype(str).str[:4].astype(int).isin(write_years)]
        return pd.concat([old, new], ignore_index=True)

    out = _merge_csv(
        args.out, pd.concat([p[0] for p in triples], ignore_index=True)
    ).sort_values(["date", "class"])
    args.out.write_text(out.to_csv(index=False))
    hourly = _merge_csv(
        args.hourly_out, pd.concat([p[1] for p in triples], ignore_index=True)
    ).sort_values(["date", "class"])
    args.hourly_out.write_text(hourly.to_csv(index=False))
    site_hourly = pd.concat([p[2] for p in triples], ignore_index=True)
    site_hourly = site_hourly[
        site_hourly["date"].astype(str).str[:4].astype(int).isin(write_years)
    ]
    if args.site_hourly_out.exists():
        old_site = pd.read_parquet(args.site_hourly_out)
        old_site = old_site[
            ~old_site["date"].astype(str).str[:4].astype(int).isin(write_years)
        ]
        site_hourly = pd.concat([old_site, site_hourly], ignore_index=True)
    site_hourly = site_hourly.sort_values(["date", "class", "site", "he"])
    args.site_hourly_out.parent.mkdir(parents=True, exist_ok=True)
    site_hourly.to_parquet(args.site_hourly_out, index=False)
    he_cols = [f"he{h:02d}" for h in range(1, 25)]
    for y in write_years:
        yr = out[out["date"].str.startswith(str(y))]
        for cls, g in yr.groupby("class"):
            print(
                f"{y} {cls}: {len(g)} days, avail p5/p50/p95 = "
                f"{g['avail'].quantile(0.05):.3f}/{g['avail'].median():.3f}/"
                f"{g['avail'].quantile(0.95):.3f}, rating ~{g['rating_mw'].median():.0f} MW"
            )
        hy = hourly[hourly["date"].str.startswith(str(y))]
        for cls, g in hy.groupby("class"):
            vals = g[he_cols].to_numpy(dtype=float)
            import numpy as _np

            print(
                f"{y} {cls} hourly: {len(g)} days x 24, coverage "
                f"{_np.isfinite(vals).mean():.1%}, intra-day spread "
                f"(day max-min) median {_np.nanmedian(_np.nanmax(vals, axis=1) - _np.nanmin(vals, axis=1)):.3f}"
            )
    print(f"wrote {args.out}")
    print(f"wrote {args.hourly_out}")
    for y in write_years:
        sy = site_hourly[site_hourly["date"].str.startswith(str(y))]
        print(
            f"{y} site-hour: {len(sy)} rows, "
            f"{sy['site'].nunique()} sites x {sy['date'].nunique()} days"
        )
    print(f"wrote {args.site_hourly_out}")


if __name__ == "__main__":
    main()
