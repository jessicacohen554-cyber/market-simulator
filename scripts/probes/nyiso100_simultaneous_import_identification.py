"""nyiso-100: NYISO_simultaneous_import — rule-14 [R-ACCURATE] identification.

Matrix row ``nyiso_import_sil_retire``; the reconcile the nyiso-99
``import_shape_lever`` row reported-but-did-not-arm. **No LP.** This is the
build-time instrument that identifies the 4,350 MW external simultaneous-import
cap BEFORE any mechanism is chosen, in the shape nyiso-98/99 established
(``nyiso99_import_benchmark_provenance.py``).

The question this answers
-------------------------
``interchange.spec.EXTERNAL_SIMULTANEOUS_LIMITS["NYISO"]`` caps total
simultaneous flow across all four import-node border links at 4,350 MW, cited
to "NYISO Gold Book; IRM/LCR studies". nyiso-99 established the cap is
measurement-contradicted (the model tops out at exactly 4,350 MW while the real
system scheduled more) but held the reconcile back because **the sum of posted
per-interface limits is not a simultaneous limit** — it is the sum of parallel
paths the five-zone network collapses into one link, i.e. rule 14's named
misalignment clause. So the hard part is identification, not the edit.

Sections
--------
``provenance``
    Where 4,350 actually comes from. Tests the constant against the published
    NYISO capacity-deliverability table and against the Gold Book PDFs on disk.
``envelope``
    The measured simultaneous envelope from the two independent instruments —
    EIA-930 ``NYIS`` total interchange (metered) and NYISO MIS P-32 external
    schedules (scheduled) — plus the cross-validation that the P-32 sum is NYCA
    net interchange and not a double-count of the three HQ rows.
``ratings``
    The posted per-interface P-32 limits, crosswalked to the model's four
    border links, and the admissible interval for an aggregate cap.
``binding``
    WHEN the cap binds in the committed keeper bundle, and whether the monthly
    reconciliation band or the cap is what actually sets import volume. Needs
    ``--bundle``.

Rule 13: the measured flow series are used here to FALSIFY a posted constant
and to bound an admissible interval — never as a dispatch input, and no cap is
set from them (the reconcile retires the scalar rather than restating it).

Usage::

    PYTHONPATH=.:src python scripts/probes/nyiso100_simultaneous_import_identification.py
    PYTHONPATH=.:src python scripts/probes/nyiso100_simultaneous_import_identification.py \\
        --sections binding --bundle results/calibration/nyiso99_demandfix
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ISO = "NYISO"
YEARS = (2023, 2024, 2025)
IFACE_DIR = REPO / "data" / "raw" / "NYISO" / "interface-flows"
CAPDEL_CSV = REPO / "data" / "raw" / "capacity-deliverability" / "nyiso" / "nyiso.csv"
GOLDBOOKS = tuple(REPO / "data" / "raw" / "NYISO" / f"{y}-Gold-Book-Public.pdf" for y in YEARS)

# The eleven P-32 "SCH -" external schedule rows, crosswalked to the model
# border link (interchange.spec.IMPORT_NODE_LINKS["NYISO"]) whose physical tie
# set they belong to. Landing points: NYISO Gold Book external interconnections.
#   * Upstate_West   — the northern/western seams (HQ at Chateauguay/Cedars into
#     Zone D, IESO into Zones A/B).
#   * Capital_Hudson — the EASTERN AC seams landing east of Central-East (the
#     PJM Ramapo 345 kV ties into Zone G, the ISO-NE ties into Zones F/G).
#   * NYC / Long_Island — the downstate HVDC merchant ties at converter rating.
# The AC seams (OH-NY, PJ-NY, NE-NY) are NOT split between Upstate_West and
# Capital_Hudson here: the split is a modelling choice inside the topology, and
# this probe only needs the per-link totals for the two links whose tie sets are
# unambiguous (the point-to-point HVDC converters), where no parallel-path
# misalignment exists at all.
SCH_TO_LINK: dict[str, str] = {
    "SCH - HQ - NY": "AC_seams",
    "SCH - HQ_CEDARS": "AC_seams",
    "SCH - HQ_IMPORT_EXPORT": "AC_seams",
    "SCH - OH - NY": "AC_seams",
    "SCH - NE - NY": "AC_seams",
    "SCH - PJ - NY": "AC_seams",
    "SCH - PJM_HTP": "NYC",
    "SCH - PJM_VFT": "NYC",
    "SCH - PJM_NEPTUNE": "Long_Island",
    "SCH - NPX_CSC": "Long_Island",
    "SCH - NPX_1385": "Long_Island",
}

# interchange.spec.IMPORT_NODE_LINKS["NYISO"] — the model's four border links.
MODEL_LINK_TTC: dict[str, float] = {
    "Upstate_West": 3000.0,
    "Capital_Hudson": 1600.0,
    "NYC": 1000.0,
    "Long_Island": 1200.0,
}
SIL_MW = 4350.0
SENTINEL = 9999.0


def _p32(year: int) -> pd.DataFrame:
    """Return the P-32 hourly posting for ``year`` with sentinels nulled."""
    df = pd.read_csv(
        IFACE_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz",
        parse_dates=["interval_start_utc"],
    )
    df.loc[df.positive_limit_mw.abs() >= SENTINEL, "positive_limit_mw"] = np.nan
    df.loc[df.negative_limit_mw.abs() >= SENTINEL, "negative_limit_mw"] = np.nan
    return df


def _sch_pivots(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (flow, positive_limit) pivots over the eleven SCH- rows."""
    df = _p32(year)
    sch = df[df.interface.str.startswith("SCH - ")]
    flow = sch.pivot_table(
        index="interval_start_utc", columns="interface", values="flow_mw", aggfunc="mean"
    )
    lim = sch.pivot_table(
        index="interval_start_utc",
        columns="interface",
        values="positive_limit_mw",
        aggfunc="mean",
    )
    return flow, lim


def _metered_net_import(year: int) -> np.ndarray:
    """EIA-930 NYIS net import (MW, import-positive) on the model's 8760 clock.

    The repo's canonical accessor (``eia_loader.nyiso_net_interchange``,
    export-positive) — the same series the LP's monthly reconciliation band and
    the scorer see. Used for every statistic quoted on the model's own clock
    (annual max, hours over the cap, the binding section).
    """
    from market_sim.data.eia_loader import nyiso_net_interchange

    export_pos = nyiso_net_interchange(year)
    if export_pos is None:
        return np.full(8760, np.nan)
    return -np.asarray(export_pos, dtype=float).reshape(-1)


def _metered_utc(year: int) -> pd.Series:
    """EIA-930 NYIS net import (MW, import-positive), UTC-timestamp indexed.

    Kept separate from :func:`_metered_net_import` on purpose. The cross-
    validation against P-32 must join on UTC timestamps, never positionally:
    the model clock is 8,760 h even in leap-year 2024, while P-32 posts all
    8,784, so positional alignment silently shears the two series apart after
    Feb 29 (r 0.906 -> 0.774). This reads the raw parquet, whose ``TI`` column
    is UTC-stamped. Its 2025 coverage ends 2025-03-31, so the 2025 correlation
    is reported on Q1 only and labelled as such.
    """
    e = pd.read_parquet(REPO / "data" / "raw" / "NYIS_region.parquet")
    ti = e[e.type == "TI"].set_index("period").value_mwh.sort_index()
    return -ti[ti.index.year == year]


# ---------------------------------------------------------------------------
# provenance
# ---------------------------------------------------------------------------


def section_provenance() -> None:
    """Test 4,350 against the published NYISO tables and the Gold Book."""
    print("=" * 78)
    print("PROVENANCE — where does 4,350 MW come from?")
    print("=" * 78)

    cap = pd.read_csv(CAPDEL_CSV)
    imp = cap[(cap.metric == "import_limit")][
        ["delivery_year", "area", "value_mw", "source_doc"]
    ]
    print("\nPublished NYISO Locality Bulk Power Transmission Limits (import_limit):")
    print(imp.to_string(index=False))

    hits = imp[np.isclose(imp.value_mw.astype(float), SIL_MW)]
    print(f"\nRows matching the model constant {SIL_MW:.0f} MW exactly: {len(hits)}")
    for _, r in hits.iterrows():
        print(
            f"  -> area={r.area!r}  delivery_year={r.delivery_year}  "
            f"source={r.source_doc}"
        )
    if len(hits):
        gj = imp[imp.area == "G-J"].sort_values("delivery_year")
        series = " / ".join(f"{v:.0f}" for v in gj.value_mw.astype(float))
        print(
            f"\n  The G-J series MOVES by capability year: {series} "
            f"({', '.join(gj.delivery_year)})."
        )
        print(
            "  The model constant is FROZEN at the 2024/2025 value across all "
            "three solve years."
        )
        print(
            "  G-J is an INTERNAL New York boundary (Load Zones G,H,I,J), NOT "
            "the external NYCA seam."
        )

    print("\nGold Book (the cited source) — does it publish an external SIL?")
    try:
        import pdfplumber
    except ImportError:  # pragma: no cover - probe convenience
        print("  [pdfplumber not installed; skipping PDF extraction]")
        return
    for pdf_path in GOLDBOOKS:
        if not pdf_path.exists():
            print(f"  {pdf_path.name}: NOT ON DISK")
            continue
        with pdfplumber.open(pdf_path) as pdf:
            n_sil = 0
            redacted = False
            for pg in pdf.pages:
                t = pg.extract_text() or ""
                if "Simultaneous Import" in t or "Simultaneous Transfer" in t:
                    n_sil += 1
                if "Table VI-1" in t and "redacted" in t.lower():
                    redacted = True
            print(
                f"  {pdf_path.name}: pages naming a Simultaneous Import/Transfer "
                f"limit = {n_sil}; Table VI-1 redacted as CEII = {redacted}"
            )


# ---------------------------------------------------------------------------
# envelope
# ---------------------------------------------------------------------------


def section_envelope() -> None:
    """The measured simultaneous envelope from both independent instruments."""
    print("\n" + "=" * 78)
    print("ENVELOPE — what did the real system simultaneously import?")
    print("=" * 78)
    for year in YEARS:
        flow, _ = _sch_pivots(year)
        sched = flow.sum(axis=1)
        metered = _metered_net_import(year)  # model clock
        # Cross-validation joins on UTC timestamps, never positionally.
        mu = _metered_utc(year).reindex(sched.index)
        ok = mu.notna() & sched.notna()
        a, b = sched[ok], mu[ok]
        r = float(np.corrcoef(a, b)[0, 1])
        partial = " (Q1 only — raw TI coverage ends 2025-03-31)" if int(ok.sum()) < 8000 else ""
        print(f"\n--- {year} ---")
        print(
            f"  P-32 scheduled  : max {sched.max():7.0f}  p99 {sched.quantile(.99):7.0f}"
            f"  mean {sched.mean():6.0f}   h > {SIL_MW:.0f}: {(sched > SIL_MW).sum():4d}"
        )
        print(
            f"  EIA-930 metered : max {np.nanmax(metered):7.0f}  p99 "
            f"{np.nanpercentile(metered, 99):7.0f}  mean {np.nanmean(metered):6.0f}   "
            f"h > {SIL_MW:.0f}: {int((metered > SIL_MW).sum()):4d}"
        )
        print(
            f"  cross-validation (P-32 sum IS NYCA net interchange, not a "
            f"double-count of the 3 HQ rows): n={int(ok.sum())} r={r:.3f} "
            f"bias {float((a - b).mean()):+.0f} MW on a {float(b.mean()):.0f} MW "
            f"mean{partial}"
        )
        print(
            f"  VERDICT: the cap {SIL_MW:.0f} MW lies "
            f"{'BELOW' if SIL_MW < np.nanmax(metered) else 'above'} the metered "
            f"simultaneous maximum -> falsified as a physical external bound."
        )


# ---------------------------------------------------------------------------
# ratings
# ---------------------------------------------------------------------------


def section_ratings() -> None:
    """Posted per-interface limits crosswalked to the model's border links."""
    print("\n" + "=" * 78)
    print("RATINGS — posted per-interface limits vs the model's border links")
    print("=" * 78)
    for year in YEARS:
        _, lim = _sch_pivots(year)
        med = lim.median()
        by_link: dict[str, float] = {}
        for iface, link in SCH_TO_LINK.items():
            if iface in med.index:
                by_link[link] = by_link.get(link, 0.0) + float(med[iface])
        print(f"\n--- {year} (median posted positive limit, MW) ---")
        for iface in sorted(med.index):
            print(f"    {iface:<26} {med[iface]:7.0f}   -> {SCH_TO_LINK.get(iface,'?')}")
        print(f"  posted sum (ALL paths)          {med.sum():7.0f}"
              "   <- rule-14 MISALIGNED: parallel paths, not a simultaneous limit")
        for link in ("NYC", "Long_Island"):
            print(
                f"  {link:<14} posted {by_link.get(link, 0.0):6.0f}  vs model link TTC "
                f"{MODEL_LINK_TTC[link]:6.0f}   <- point-to-point HVDC, no "
                f"parallel-path ambiguity"
            )
        print(f"  AC_seams       posted {by_link.get('AC_seams', 0.0):6.0f}  vs model "
              f"{MODEL_LINK_TTC['Upstate_West'] + MODEL_LINK_TTC['Capital_Hudson']:6.0f}"
              "   <- behind the internal Central-East chain the topology carries")

        hourly_sum = lim.sum(axis=1)
        lo = float(np.nanmax(_metered_net_import(year)))
        hi = float(med.sum())
        print(
            f"  ADMISSIBLE INTERVAL for an aggregate cap: [{lo:.0f} (metered "
            f"simultaneous max, a measured lower bound), {hi:.0f} (posted-rating "
            f"upper bound)]"
        )
        print(
            f"    min over hours of the posted sum: {hourly_sum.min():.0f} MW "
            f"(outage-tightened worst hour)"
        )
        link_sum = sum(MODEL_LINK_TTC.values())
        inside = lo <= link_sum <= hi
        print(
            f"    model border-link sum {link_sum:.0f} MW is "
            f"{'INSIDE' if inside else 'OUTSIDE'} the interval; the current "
            f"scalar {SIL_MW:.0f} MW is "
            f"{'INSIDE' if lo <= SIL_MW <= hi else 'OUTSIDE'} it."
        )


# ---------------------------------------------------------------------------
# binding
# ---------------------------------------------------------------------------


def section_binding(bundle: Path) -> None:
    """When does the cap bind, and what actually sets import volume?"""
    from market_sim.data.eia_loader import nyiso_net_interchange
    from market_sim.data.fleet import _hour_to_month_index

    print("\n" + "=" * 78)
    print(f"BINDING — how the cap acts in {bundle}")
    print("=" * 78)
    for year in YEARS:
        f = bundle / "hourly" / f"class_hourly_{year}.parquet"
        if not f.exists():
            print(f"  {year}: no class_hourly sidecar, skipped")
            continue
        d = pd.read_parquet(f)
        imp = d[d.klass == "import"].sort_values("hour").mw.to_numpy()
        meas = -np.asarray(nyiso_net_interchange(year), dtype=float).reshape(-1)[: len(imp)]
        hod = np.arange(len(imp)) % 24
        at = imp >= SIL_MW - 0.5
        night = np.isin(hod, (21, 22, 23, 0, 1, 2, 3))
        peak = np.isin(hod, (16, 17, 18))
        print(f"\n--- {year} ---")
        print(
            f"  model import max {imp.max():.0f} (cap {SIL_MW:.0f})  "
            f"hours AT cap {int(at.sum())}"
        )
        if at.sum():
            print(
                f"    of those, h21-h03: {int((at & night).sum())} "
                f"({100 * (at & night).sum() / at.sum():.0f}%)   "
                f"h16-h18: {int((at & peak).sum())} "
                f"({100 * (at & peak).sum() / at.sum():.0f}%)"
            )
            print(
                f"    real system imported LESS than the cap in "
                f"{int((meas[at] <= SIL_MW).sum())}/{int(at.sum())} = "
                f"{100 * (meas[at] <= SIL_MW).mean():.0f}% of cap-bound hours"
            )
        mi = _hour_to_month_index(len(imp))
        ratio = np.bincount(mi, weights=imp) / np.bincount(mi, weights=meas)
        print(
            f"  monthly reconciliation band (+-2%): at UPPER edge in "
            f"{int((ratio >= 1.0195).sum())}/12 months "
            f"-> VOLUME is set by the band, the cap only shapes the hourly "
            f"allocation"
        )


def main(argv: list[str] | None = None) -> int:
    """Run the requested probe sections."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--sections",
        nargs="+",
        default=["provenance", "envelope", "ratings"],
        choices=["provenance", "envelope", "ratings", "binding", "all"],
    )
    ap.add_argument("--bundle", type=Path, default=None)
    args = ap.parse_args(argv)
    secs = (
        ["provenance", "envelope", "ratings", "binding"]
        if "all" in args.sections
        else args.sections
    )
    if "provenance" in secs:
        section_provenance()
    if "envelope" in secs:
        section_envelope()
    if "ratings" in secs:
        section_ratings()
    if "binding" in secs:
        if args.bundle is None:
            print("\n[binding] needs --bundle; skipped")
        else:
            section_binding(args.bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
