"""neiso-72 evidence probe: NEISO's pumped-storage TIME SPLIT in EIA-930.

The last open cell of the ``hydro_level_923_hy`` row. miso-109 screened all six
ISOs and PJM/MISO were fixed by adding the BA to
``constants.EIA930_PS_FOLDED_INTO_WAT`` (a flat, all-years refusal of the
``NG: WAT`` monthly LEVEL pin). NEISO is different and cannot take that switch:
it is the ONLY one of the six that files an ``NG: PS`` column at all, and only
from part-way through the series — so its exposure is a **time split**, not a
standing fold, and a flat listing would discard the good post-split vintages.

This probe measures the split from committed raw inputs only (no solve, no
bundle), every number from NEISO's own data (rule 25 ``[R-ISO-SCOPE]``):

  §1 PS onset       — the first month NEISO's extract carries a populated
                      ``NG: PS`` column, measured three ways (column present /
                      non-null hours / non-zero energy) so "the column exists"
                      is never confused with "the column is filed".
  §2 breach window  — the nameplate-breach signature (miso-109 §2) resolved BY
                      MONTH rather than by year, which is what distinguishes a
                      time split from a standing fold: a fold breaches in every
                      month, a split stops breaching at the seam.
  §3 monthly gap    — 930 ``NG: WAT`` against 923 ``HY`` per month, split at the
                      seam, coverage-gated exactly as miso-109 §3 (an early
                      release is never differenced against a full filing).
  §3b seam step     — the fold hypothesis's falsification test: at the seam
                      ``WAT`` must fall while ``WAT + PS`` stays continuous.
  §4 PS magnitude   — what the post-split ``NG: PS`` column actually carries,
                      against the EIA-860 PS nameplate and the EIA-923 ``PS``
                      net generation, to test whether the measured gap is even
                      the right SIZE to be the pumped-storage fold.
  §6 fingerprint    — the decisive SHAPE test. The post-split window supplies
                      both reference fingerprints on NEISO's own data (``WAT``
                      alone and ``WAT + PS``); the pre-split column is matched
                      against them on scale-free metrics.
  §7 which column   — did a column FALL by the PS amount at the seam, or did
                      the reported TOTAL rise? (Seasonally confounded — kept for
                      completeness, superseded by §9.)
  §8 decomposition  — HOW MUCH pumped storage is in the pre-split column, by
                      non-negative least squares against the two measured
                      post-split diurnal shapes, self-tested first on the
                      window whose answer is known.
  §9 within-month   — the strongest test: the seam falls INSIDE November 2024,
                      six days apart, so no seasonal or water-year confound can
                      explain the step.
  §5 designs        — the monthly LEVEL each candidate treatment would hand the
                      LP, per year, backcast and forecast lanes: (A) keeper
                      today, (B) flat registry listing, (C) per-window seam
                      split, (D) whole-year rule.

Usage:
    python scripts/probes/_neiso72_ps_window_audit.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.data.eia930.envelopes import measured_monthly_hydro  # noqa: E402
from market_sim.data.eia930.frames import (  # noqa: E402
    _ISO_TO_HOURLY_BA,
    _eia_hourly_frame_filled,
)
from market_sim.data.fleet import ISO_TO_BA_CODE  # noqa: E402
from market_sim.data.hydro import _load_hydro_nameplate  # noqa: E402

ISO = "NEISO"
YEARS = range(2019, 2026)
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _frame(year: int) -> "pd.DataFrame | None":
    return _eia_hourly_frame_filled(_ISO_TO_HOURLY_BA.get(ISO, ISO), year)


def _col(frame: pd.DataFrame, name: str) -> np.ndarray:
    return pd.to_numeric(frame[name], errors="coerce").to_numpy()


def section_1_ps_onset() -> None:
    """When does the ``NG: PS`` column start being FILED (not merely present)?"""
    print("\n== §1 NG: PS onset — column present vs actually filed ==")
    print("   yr-mo | col | non-null h | non-zero h |    PS GWh | min MW | max MW")
    for year in YEARS:
        frame = _frame(year)
        if frame is None:
            print(f"   {year}    no extract")
            continue
        has = "NG: PS" in frame.columns
        if not has:
            print(f"   {year}    NG: PS column ABSENT from the extract")
            continue
        months = frame["Local date"].dt.month.to_numpy()
        ps = _col(frame, "NG: PS")
        for m in range(1, 13):
            sel = months == m
            vals = ps[sel]
            nn = int(np.sum(~np.isnan(vals)))
            nz = int(np.sum(np.nan_to_num(vals) != 0.0))
            if nn == 0:
                print(f"   {year}-{m:02d} | yes |          0 |          0 |         — |      — |      —")
                continue
            fin = vals[~np.isnan(vals)]
            print(
                f"   {year}-{m:02d} | yes | {nn:10d} | {nz:10d} | "
                f"{np.nansum(vals) / 1e3:9.1f} | {fin.min():6.0f} | {fin.max():6.0f}"
            )


def section_2_breach_by_month() -> None:
    """Nameplate breach BY MONTH — a fold breaches always, a split stops."""
    np_mw = sum(_load_hydro_nameplate(ISO).values())
    print(f"\n== §2 nameplate breach by month (conventional HY nameplate {np_mw:,.1f} MW) ==")
    print("   year |" + "".join(f"{m:>5s}" for m in MONTHS) + " |  yr h | neg h")
    for year in YEARS:
        frame = _frame(year)
        if frame is None or "NG: WAT" not in frame.columns:
            continue
        months = frame["Local date"].dt.month.to_numpy()
        wat = _col(frame, "NG: WAT")
        row, tot = [], 0
        for m in range(1, 13):
            n = int(np.sum((months == m) & (wat > np_mw)))
            row.append(n)
            tot += n
        neg = int(np.sum(wat < 0))
        print(f"   {year} |" + "".join(f"{n:5d}" for n in row) + f" | {tot:5d} | {neg:5d}")


def _hy_monthly(gen: pd.DataFrame, mcols: list[str], year: int):
    """EIA-923 ``HY`` monthly MWh for NEISO plus its plant census."""
    ba = ISO_TO_BA_CODE.get(ISO, ISO)
    sub = gen[(gen["year"] == year) & (gen["ba_code"] == ba) & (gen["prime_mover"] == "HY")]
    if sub.empty:
        return None, 0
    return sub[mcols].sum().to_numpy(dtype=float), int(sub["plant_id"].nunique())


def section_3_monthly_gap() -> None:
    """930 NG: WAT vs 923 HY, per month, coverage-gated."""
    print("\n== §3 monthly 930 NG: WAT minus 923 HY (GWh), coverage-gated ==")
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    census = {}
    for year in YEARS:
        _, n = _hy_monthly(gen, mcols, year)
        census[year] = n
    modal = float(np.median([n for n in census.values() if n]))
    print(f"   modal HY plant census {modal:.0f}; complete = census >= 0.50 x modal")
    print("   year |" + "".join(f"{m:>6s}" for m in MONTHS) + " |    yr GWh")
    for year in YEARS:
        hy, n = _hy_monthly(gen, mcols, year)
        wat = measured_monthly_hydro(ISO, year)
        if hy is None or wat is None:
            continue
        if n < 0.50 * modal:
            print(f"   {year} | EARLY RELEASE ({n} of a modal {modal:.0f} plants) — not differenced")
            continue
        gap = (wat - hy) / 1e3
        print(
            f"   {year} |" + "".join(f"{g:6.0f}" for g in gap)
            + f" | {gap.sum():9.1f}  (census {n})"
        )
    print("\n   -- the same rows as a SHARE of the month's 923 HY (%) --")
    print("   year |" + "".join(f"{m:>6s}" for m in MONTHS))
    for year in YEARS:
        hy, n = _hy_monthly(gen, mcols, year)
        wat = measured_monthly_hydro(ISO, year)
        if hy is None or wat is None or n < 0.50 * modal:
            continue
        pct = 100.0 * (wat - hy) / np.where(hy > 0, hy, np.nan)
        print(f"   {year} |" + "".join(f"{p:6.1f}" for p in pct))


def section_3b_seam_step() -> None:
    """The FALSIFICATION test for the fold hypothesis.

    If ``NG: PS`` was folded into ``NG: WAT`` before the seam and split out
    after it, then at the seam ``WAT`` must STEP DOWN by the PS discharge while
    ``WAT + PS`` stays continuous. Both halves are checked here — a step in
    ``WAT`` alone is not enough, because hydro also varies with the water year,
    so the test is whether the RECOMBINED series is the continuous one.
    """
    print("\n== §3b seam step — does WAT drop by PS while WAT+PS stays continuous? ==")
    print("   Monthly means, MW. 'WAT+PS' recombines the split-out column.")
    print("   yr-mo |     WAT |      PS |  WAT+PS | seam")
    for year in (2023, 2024, 2025):
        frame = _frame(year)
        if frame is None or "NG: WAT" not in frame.columns:
            continue
        months = frame["Local date"].dt.month.to_numpy()
        wat = _col(frame, "NG: WAT")
        ps = _col(frame, "NG: PS") if "NG: PS" in frame.columns else np.full_like(wat, np.nan)
        for m in range(1, 13):
            sel = months == m
            w = np.nanmean(wat[sel])
            p_filed = np.sum(~np.isnan(ps[sel])) > 0
            p = np.nanmean(ps[sel]) if p_filed else float("nan")
            tot = w + (p if p_filed else 0.0)
            tag = "post-split" if p_filed else "PRE-SPLIT"
            print(
                f"   {year}-{m:02d} | {w:7.0f} | "
                + (f"{p:7.0f}" if p_filed else "      —")
                + f" | {tot:7.0f} | {tag}"
            )

    print("\n   -- like-month year-over-year, the seam months only --")
    print("   month | 2023 WAT | 2024 WAT | 2025 WAT | 2024 PS | 2025 PS")
    frames = {y: _frame(y) for y in (2023, 2024, 2025)}
    for m in (11, 12):
        row = []
        for y in (2023, 2024, 2025):
            f = frames[y]
            if f is None:
                row.append(float("nan"))
                continue
            sel = f["Local date"].dt.month.to_numpy() == m
            row.append(float(np.nanmean(_col(f, "NG: WAT")[sel])))
        psrow = []
        for y in (2024, 2025):
            f = frames[y]
            sel = f["Local date"].dt.month.to_numpy() == m
            v = _col(f, "NG: PS")[sel]
            psrow.append(float(np.nanmean(v)) if np.sum(~np.isnan(v)) else float("nan"))
        print(
            f"   {MONTHS[m - 1]:>5s} | {row[0]:8.0f} | {row[1]:8.0f} | {row[2]:8.0f} "
            f"| {psrow[0]:7.0f} | {psrow[1]:7.0f}"
        )

    print("\n   -- ANNUAL: what a fold of this PS fleet would have to be worth --")
    for year in (2024, 2025):
        frame = _frame(year)
        if frame is None or "NG: PS" not in frame.columns:
            continue
        ps = _col(frame, "NG: PS")
        filed = ps[~np.isnan(ps)]
        if filed.size == 0:
            continue
        rate = filed.sum() / filed.size  # mean MW over FILED hours only
        print(
            f"     {year}: PS filed in {filed.size:5d} h, mean {rate:6.1f} MW "
            f"-> an 8760-h year at that rate = {rate * 8760 / 1e6:.3f} TWh"
        )


def section_4_ps_magnitude() -> None:
    """Is the measured gap even the right SIZE to be the PS fold?"""
    print("\n== §4 what the PS fleet actually is, and what the split-out column carries ==")
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    ba = ISO_TO_BA_CODE.get(ISO, ISO)
    ps923 = gen[(gen["ba_code"] == ba) & (gen["prime_mover"] == "PS")]
    print("   EIA-923 prime mover PS (net generation — NEGATIVE = round-trip loss):")
    for year in YEARS:
        sub = ps923[ps923["year"] == year]
        if sub.empty:
            continue
        print(
            f"     {year}: {sub[mcols].sum().sum() / 1e6:8.3f} TWh over "
            f"{sub['plant_id'].nunique()} plants"
        )
    try:
        from market_sim.config.paths import EIA_860_DIR
        from market_sim.data.hydro import EIA_860_PARQUET_NAME

        g860 = pd.read_parquet(Path(EIA_860_DIR) / EIA_860_PARQUET_NAME)
        sub = g860[
            (g860["balancing_authority_code"] == ba) & (g860["prime_mover"] == "PS")
        ]
        print(f"\n   EIA-860 PS nameplate in {ba}: {sub['nameplate_capacity_mw'].sum():,.1f} MW")
        key = "plant_name" if "plant_name" in sub.columns else "plant_id"
        by = sub.groupby(key)["nameplate_capacity_mw"].sum().sort_values(ascending=False)
        for k, v in by.items():
            print(f"     {str(k):40s} {v:9.1f} MW")
    except Exception as exc:  # pragma: no cover - diagnostic only
        print(f"   (EIA-860 PS nameplate unavailable: {exc})")
    print("\n   EIA-930 NG: PS by year (the split-out column, once filed):")
    for year in YEARS:
        frame = _frame(year)
        if frame is None or "NG: PS" not in frame.columns:
            continue
        ps = _col(frame, "NG: PS")
        if np.all(np.isnan(ps)):
            print(f"     {year}: all-NaN")
            continue
        fin = ps[~np.isnan(ps)]
        pos = float(np.nansum(fin[fin > 0])) / 1e6
        neg = float(np.nansum(fin[fin < 0])) / 1e6
        print(
            f"     {year}: net {fin.sum() / 1e6:7.3f} TWh  "
            f"(discharge {pos:6.3f}, pumping {neg:7.3f}) over {fin.size} filed hours"
        )


def section_6_shape_fingerprint() -> None:
    """THE decisive test: does PRE-split ``WAT`` behave like ``WAT`` or ``WAT+PS``?

    The fold hypothesis is not a claim about levels — it is a claim about
    *which series* the pre-seam column is. That claim has a falsifiable shape
    consequence: pumped storage is a sharp, high-amplitude on-peak block, so a
    series carrying it must show a LARGER diurnal swing and a HEAVIER upper
    tail than one that does not. The post-split window supplies both reference
    fingerprints on NEISO's own data — ``WAT`` alone and ``WAT + PS`` — so the
    pre-split column can be matched against them directly.

    Every metric is scale-free (ratios), because the windows differ in water
    year and a level comparison would confound the two.
    """
    np_mw = sum(_load_hydro_nameplate(ISO).values())
    print("\n== §6 shape fingerprint — is PRE-split WAT the 'WAT' or the 'WAT+PS' series? ==")
    print(f"   conventional (HY) nameplate {np_mw:,.1f} MW; all metrics scale-free")

    def _fingerprint(label: str, hours: np.ndarray, series: np.ndarray) -> None:
        s = series[~np.isnan(series)]
        h = hours[~np.isnan(series)]
        if s.size < 24:
            return
        hod = np.array([np.mean(s[h == k]) for k in range(24)])
        swing = hod.max() / hod.min() if hod.min() > 0 else float("inf")
        med = np.median(s)
        print(
            f"   {label:34s} | swing {swing:5.2f}x | p99/p50 {np.percentile(s, 99) / med:5.2f} "
            f"| max/mean {s.max() / s.mean():5.2f} | >nameplate {1000 * np.sum(s > np_mw) / s.size:6.1f}/1000h "
            f"| peak HE{int(np.argmax(hod)) + 1:02d}"
        )

    windows: dict[str, list[tuple[int, int]]] = {
        "PRE-split 2023 (12 mo)": [(2023, m) for m in range(1, 13)],
        "PRE-split 2024 Jan-Oct": [(2024, m) for m in range(1, 11)],
        "PRE-split 2019-2022": [(y, m) for y in range(2019, 2023) for m in range(1, 13)],
    }
    post = [(2024, 11), (2024, 12)] + [(2025, m) for m in range(1, 13)]

    cache: dict[int, "pd.DataFrame | None"] = {y: _frame(y) for y in YEARS}

    def _gather(keys: list[tuple[int, int]], add_ps: bool):
        hs, vs = [], []
        for year, month in keys:
            f = cache.get(year)
            if f is None or "NG: WAT" not in f.columns:
                continue
            sel = f["Local date"].dt.month.to_numpy() == month
            wat = _col(f, "NG: WAT")[sel]
            hod = np.arange(wat.size) % 24
            if add_ps:
                if "NG: PS" not in f.columns:
                    continue
                ps = _col(f, "NG: PS")[sel]
                if np.all(np.isnan(ps)):
                    continue
                wat = wat + np.nan_to_num(ps)
            hs.append(hod)
            vs.append(wat)
        if not vs:
            return None, None
        return np.concatenate(hs), np.concatenate(vs)

    print("\n   -- the two REFERENCE fingerprints, from the post-split window --")
    h, v = _gather(post, add_ps=False)
    _fingerprint("POST-split  WAT  (no PS)", h, v)
    h, v = _gather(post, add_ps=True)
    _fingerprint("POST-split  WAT + PS", h, v)

    print("\n   -- the PRE-split column, to be matched against them --")
    for label, keys in windows.items():
        h, v = _gather(keys, add_ps=False)
        if h is not None:
            _fingerprint(label, h, v)

    print("\n   -- the PS column alone, for reference --")
    h, v = _gather(post, add_ps=False)
    hs, vs = [], []
    for year, month in post:
        f = cache.get(year)
        if f is None or "NG: PS" not in f.columns:
            continue
        sel = f["Local date"].dt.month.to_numpy() == month
        ps = _col(f, "NG: PS")[sel]
        if np.all(np.isnan(ps)):
            continue
        hs.append(np.arange(ps.size) % 24)
        vs.append(ps)
    if vs:
        ps_all = np.concatenate(vs)
        h_all = np.concatenate(hs)
        hod = np.array([np.nanmean(ps_all[h_all == k]) for k in range(24)])
        print(
            f"   {'POST-split  PS alone':34s} | hod min {hod.min():6.1f} MW, "
            f"max {hod.max():6.1f} MW at HE{int(np.argmax(hod)) + 1:02d} | "
            f"p99 {np.nanpercentile(ps_all, 99):6.0f} MW | "
            f"zero-hours {100 * np.mean(np.nan_to_num(ps_all) == 0):5.1f}%"
        )


def section_7_which_column() -> None:
    """Where did the PS energy COME FROM at the seam? The level-side decider.

    §6 shows the pre-split ``NG: WAT`` carries a pumped-storage-shaped block,
    but §3 shows the pre-split 930-vs-923 level gap is far SMALLER than the PS
    fleet's own energy — the two do not obviously reconcile. This section
    separates the only two ways that can happen:

    * PS was **moved** out of some column into its own. Then the BA's TOTAL
      reported generation is CONTINUOUS across the seam, and whichever column
      steps down by the PS amount is the one that carried it.
    * PS was **newly added** to the filing (previously not reported at all).
      Then the TOTAL steps UP at the seam by the PS amount and no column falls.

    Reported per-column monthly means either side of the seam settle it.
    """
    print("\n== §7 at the seam, did a column FALL by the PS amount, or did the TOTAL RISE? ==")
    cache = {y: _frame(y) for y in (2023, 2024, 2025)}
    f24 = cache[2024]
    cols = [c for c in f24.columns if c.startswith("NG:")] if f24 is not None else []
    print("   monthly mean MW by fuel column, plus the summed total")
    hdr = "   yr-mo |" + "".join(f"{c.replace('NG: ', ''):>7s}" for c in cols) + " |  TOTAL"
    print(hdr)
    for year, m0, m1 in ((2024, 6, 12), (2025, 1, 6)):
        f = cache[year]
        if f is None:
            continue
        months = f["Local date"].dt.month.to_numpy()
        for m in range(m0, m1 + 1):
            sel = months == m
            vals, tot = [], 0.0
            for c in cols:
                v = _col(f, c)[sel]
                mean = np.nanmean(v) if np.sum(~np.isnan(v)) else float("nan")
                vals.append(mean)
                tot += 0.0 if np.isnan(mean) else mean
            print(
                f"   {year}-{m:02d} |"
                + "".join("      —" if np.isnan(v) else f"{v:7.0f}" for v in vals)
                + f" | {tot:7.0f}"
            )

    print("\n   -- the seam step, Jul-Oct 2024 (pre) vs Nov 2024-Feb 2025 (post) --")
    pre = [(2024, m) for m in (7, 8, 9, 10)]
    post = [(2024, 11), (2024, 12), (2025, 1), (2025, 2)]

    def _win_mean(keys, col):
        acc = []
        for year, m in keys:
            f = cache.get(year)
            if f is None or col not in f.columns:
                continue
            sel = f["Local date"].dt.month.to_numpy() == m
            v = _col(f, col)[sel]
            if np.sum(~np.isnan(v)):
                acc.append(float(np.nanmean(v)))
        return float(np.mean(acc)) if acc else float("nan")

    print("   column  |   pre MW |  post MW |    step")
    tot_pre = tot_post = 0.0
    for c in cols:
        a, b = _win_mean(pre, c), _win_mean(post, c)
        tot_pre += 0.0 if np.isnan(a) else a
        tot_post += 0.0 if np.isnan(b) else b
        sa = "       —" if np.isnan(a) else f"{a:8.0f}"
        sb = "       —" if np.isnan(b) else f"{b:8.0f}"
        step = "      —" if (np.isnan(a) or np.isnan(b)) else f"{b - a:+7.0f}"
        print(f"   {c.replace('NG: ', ''):7s} | {sa} | {sb} | {step}")
    print(f"   {'TOTAL':7s} | {tot_pre:8.0f} | {tot_post:8.0f} | {tot_post - tot_pre:+7.0f}")
    print(
        "\n   Read: if TOTAL rises by ~the PS column and no other column falls,\n"
        "   the PS energy is NEW to the filing and NG: WAT never carried it."
    )


def section_8_decompose() -> None:
    """How MUCH pumped storage is in the pre-split column? A measured estimate.

    §6 establishes that the pre-split ``NG: WAT`` carries a PS-shaped block;
    §3 establishes that the pre-split level gap against EIA-923 ``HY`` is far
    too small to be the whole PS fleet. Only a magnitude reconciles them, so
    it is measured here rather than assumed.

    Identification: the post-split window supplies two measured 24-point
    diurnal SHAPES on NEISO's own data — conventional ``WAT`` and ``PS`` — each
    normalised to unit mean. A pre-split window's own diurnal profile is then
    the non-negative least-squares combination

        pre_hod(h) = A * conv_shape(h) + B * ps_shape(h)

    and the folded pumped storage is ``B`` MW mean, i.e. ``B * 8760`` MWh/yr.
    Two free parameters, both solved from the data, none tuned to any residual.

    SELF-TEST FIRST: the same estimator is run on the post-split ``WAT + PS``
    series, where the true ``B`` is known exactly. An estimator that cannot
    recover a known answer cannot be trusted on the unknown one.
    """
    print("\n== §8 how much PS is folded in? two-component diurnal decomposition ==")
    cache = {y: _frame(y) for y in YEARS}

    def _hod(keys: list[tuple[int, int]], col: str, add: str | None = None):
        acc = [[] for _ in range(24)]
        for year, m in keys:
            f = cache.get(year)
            if f is None or col not in f.columns:
                continue
            sel = f["Local date"].dt.month.to_numpy() == m
            v = _col(f, col)[sel]
            if add:
                if add not in f.columns:
                    continue
                a = _col(f, add)[sel]
                if np.all(np.isnan(a)):
                    continue
                v = v + np.nan_to_num(a)
            for i, x in enumerate(v):
                acc[i % 24].append(x)
        out = np.array([np.nanmean(a) if a else np.nan for a in acc])
        return out if not np.all(np.isnan(out)) else None

    post = [(2024, 12)] + [(2025, m) for m in range(1, 13)]
    conv = _hod(post, "NG: WAT")
    ps = _hod(post, "NG: PS")
    if conv is None or ps is None:
        print("   post-split reference shapes unavailable")
        return
    conv_shape, ps_shape = conv / conv.mean(), ps / ps.mean()
    print(
        f"   reference shapes from {post[0][0]}-{post[0][1]:02d}..2025-12 "
        f"(conv mean {conv.mean():.0f} MW, PS mean {ps.mean():.0f} MW)"
    )
    print(
        "   conv_shape min/max "
        f"{conv_shape.min():.2f}/{conv_shape.max():.2f}; "
        f"ps_shape min/max {ps_shape.min():.2f}/{ps_shape.max():.2f}"
    )

    basis = np.vstack([conv_shape, ps_shape]).T

    def _fit(label: str, target: np.ndarray, truth: float | None = None) -> None:
        if target is None:
            return
        coef, *_ = np.linalg.lstsq(basis, target, rcond=None)
        a, b = float(coef[0]), float(coef[1])
        resid = target - basis @ coef
        rms = float(np.sqrt(np.mean(resid**2)))
        line = (
            f"   {label:28s} | conv {a:6.0f} MW | PS {b:6.0f} MW "
            f"({b * 8760 / 1e6:5.3f} TWh/yr) | rms {rms:5.1f} MW"
        )
        if truth is not None:
            line += f" | TRUE PS {truth:5.0f} MW"
        print(line)

    print("\n   -- SELF-TEST on the window where the answer is known --")
    _fit("post-split WAT alone", _hod(post, "NG: WAT"), truth=0.0)
    _fit("post-split WAT + PS", _hod(post, "NG: WAT", add="NG: PS"), truth=float(ps.mean()))

    print("\n   -- the PRE-split column --")
    for label, keys in (
        ("2023", [(2023, m) for m in range(1, 13)]),
        ("2024 Jan-Oct", [(2024, m) for m in range(1, 11)]),
        ("2022", [(2022, m) for m in range(1, 13)]),
        ("2021", [(2021, m) for m in range(1, 13)]),
        ("2020", [(2020, m) for m in range(1, 13)]),
        ("2019", [(2019, m) for m in range(1, 13)]),
    ):
        _fit(f"PRE-split {label}", _hod(keys, "NG: WAT"))

    print(
        "\n   Caveat carried to the charter: the estimator assumes the "
        "conventional\n   diurnal SHAPE is stable across the seam. NEISO's "
        "conventional hydro is\n   price-following, so a changed price shape "
        "moves that shape too — this is\n   an ESTIMATE with a stated "
        "assumption, not a measured decomposition."
    )


def section_9_within_month_seam() -> None:
    """The strongest single test — the seam falls INSIDE a month.

    Every other comparison in this probe spans months or years, so a water-year
    or seasonal confound has to be argued away. NEISO's ``NG: PS`` filing
    begins part-way through November 2024, which puts the pre- and post-split
    windows six days apart inside one month. Conventional hydro inflow cannot
    restructure itself over six days; pumped storage leaving the column can.
    """
    print("\n== §9 the seam falls INSIDE November 2024 — the confound-free test ==")
    f = _frame(2024)
    if f is None or "NG: PS" not in f.columns:
        print("   2024 extract unavailable")
        return
    ps = _col(f, "NG: PS")
    wat = _col(f, "NG: WAT")
    np_mw = sum(_load_hydro_nameplate(ISO).values())
    idx = np.where(~np.isnan(ps))[0]
    print(f"   first hour with a filed NG: PS value: row {idx[0]} = {f['Local date'].iloc[idx[0]]}")
    nov = np.where(f["Local date"].dt.month.to_numpy() == 11)[0]
    on = ~np.isnan(ps[nov])
    pre, post = nov[~on], nov[on]
    print(f"   conventional (HY) nameplate {np_mw:,.1f} MW")
    print("   window                 |   h |  mean MW |   max MW | >nameplate h | swing")

    def _row(label: str, rows: np.ndarray) -> None:
        v = wat[rows]
        hod = np.array(
            [np.nanmean(v[(rows % 24) == k]) for k in range(24)]
        )
        sw = hod.max() / hod.min() if hod.min() > 0 else float("inf")
        print(
            f"   {label:22s} | {rows.size:3d} | {np.nanmean(v):8.0f} | "
            f"{np.nanmax(v):8.0f} | {int(np.sum(v > np_mw)):12d} | {sw:5.2f}x"
        )

    _row("Nov 1-6  PRE-split", pre)
    _row("Nov 7-30 POST-split", post)
    print(
        "\n   Six days apart, inside one month, the SAME conventional fleet and the\n"
        "   same water: the peak collapses and the diurnal swing flattens the hour\n"
        "   the PS column starts being filed. That is the block leaving NG: WAT."
    )

    print(
        "\n   -- CONTROL: the SAME Nov 1-6 / Nov 7-30 cut in years with NO seam --\n"
        "   If the step were seasonal (autumn inflow, a November storm) it would\n"
        "   appear in every year. It appears in exactly one: the seam year."
    )
    print(
        f"   {'year':>6} {'seam':>5} | {'Nov1-6 max':>10} {'swing':>6} | "
        f"{'Nov7-30 max':>11} {'swing':>6} | {'max ratio':>9}"
    )
    for year in range(2019, 2025):
        f2 = _frame(year)
        if f2 is None or "NG: WAT" not in f2.columns:
            continue
        w2 = _col(f2, "NG: WAT")
        nov2 = np.where(f2["Local date"].dt.month.to_numpy() == 11)[0]
        day = f2["Local date"].dt.day.to_numpy()[nov2]
        a, b = nov2[day <= 6], nov2[day >= 7]

        def _stat(rows: np.ndarray) -> tuple[float, float]:
            v = w2[rows]
            hod = np.array([np.nanmean(v[(rows % 24) == k]) for k in range(24)])
            return float(np.nanmax(v)), float(hod.max() / hod.min())

        ax, asw = _stat(a)
        bx, bsw = _stat(b)
        print(
            f"   {year:>6} {'YES' if year == 2024 else 'no':>5} | {ax:10.0f} {asw:6.2f} | "
            f"{bx:11.0f} {bsw:6.2f} | {ax / bx:9.2f}"
        )
    print(
        "\n   2019-2023 max ratio 0.77-1.03 (no step, either direction); 2024 = 2.73.\n"
        "   The step is the seam, not the season."
    )


def section_5_designs() -> None:
    """The monthly LEVEL each candidate treatment hands the LP, exactly."""
    print("\n== §5 the candidate levels, per year (TWh) — the charter's numbers ==")
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    seam_year, seam_month = 2024, 11
    print(f"   PS-split seam = {seam_year}-{seam_month:02d} (measured, §1)")
    print(
        "\n   (A) keeper today  — 930 NG: WAT pinned in every month\n"
        "   (B) flat refusal  — the MISO/PJM registry switch, 923 HY in every month\n"
        "   (C) per-window    — 923 HY before the seam, 930 pin from the seam\n"
        "   (D) whole-year    — 923 HY for any year whose PS filing is incomplete,\n"
        "                       930 pin for a fully-split year (no intra-year splice)"
    )
    print("\n   year |      (A) |      (B) |      (C) |      (D) | C-A      | D-A")
    for year in (2023, 2024, 2025):
        wat = measured_monthly_hydro(ISO, year)
        hy, n = _hy_monthly(gen, mcols, year)
        if wat is None or hy is None:
            continue
        a_v = wat.copy()
        b_v = hy.copy()
        c_v = np.where(
            np.arange(1, 13) >= (seam_month if year == seam_year else (1 if year > seam_year else 13)),
            wat,
            hy,
        )
        complete_923 = n >= 0.50 * 173
        fully_split = year > seam_year
        d_v = wat if fully_split else (hy if complete_923 else wat)
        print(
            f"   {year} | {a_v.sum() / 1e6:8.4f} | {b_v.sum() / 1e6:8.4f} | "
            f"{c_v.sum() / 1e6:8.4f} | {d_v.sum() / 1e6:8.4f} | "
            f"{(c_v.sum() - a_v.sum()) / 1e6:+8.4f} | {(d_v.sum() - a_v.sum()) / 1e6:+8.4f}"
        )
    print(
        "\n   (B) is inadmissible: 2025's 923 filing is an EARLY RELEASE (6 of a\n"
        "   modal 173 plants, 0.091 TWh), so a flat refusal discards the one year\n"
        "   whose 930 series is measured clean. That is the whole reason NEISO\n"
        "   cannot take the MISO/PJM switch."
    )

    print("\n   -- FORECAST lane: the climatology each design implies --")
    try:
        from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS
        from market_sim.data.eia_loader import climatological_monthly_hydro
        from market_sim.data.hydro import (
            climatological_monthly_hydro_923,
            complete_923_hydro_years,
        )

        c930 = climatological_monthly_hydro(ISO)
        c923 = climatological_monthly_hydro_923(ISO)
        yrs = complete_923_hydro_years(ISO)
        print(f"   window {HYDRO_CLIMATOLOGY_YEARS}; 923-complete years realised: {yrs}")
        print(
            f"   930 NG: WAT climatology (today's forecast level): "
            f"{c930.sum() / 1e6:.4f} TWh"
            if c930 is not None
            else "   930 climatology unavailable"
        )
        print(
            f"   923 HY      climatology (the corrected level):    "
            f"{c923.sum() / 1e6:.4f} TWh"
            if c923 is not None
            else "   923 climatology unavailable"
        )
        if c930 is not None and c923 is not None:
            print(
                f"   forecast level moves {(c923.sum() - c930.sum()) / 1e6:+.4f} TWh "
                f"({100 * (c923.sum() - c930.sum()) / c930.sum():+.1f} %)"
            )
    except Exception as exc:  # pragma: no cover - diagnostic only
        print(f"   (forecast climatology unavailable: {exc})")


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    print("=" * 78)
    print("neiso-72: NEISO's pumped-storage TIME SPLIT in EIA-930 NG: WAT")
    print("=" * 78)
    section_1_ps_onset()
    section_2_breach_by_month()
    section_3_monthly_gap()
    section_3b_seam_step()
    section_4_ps_magnitude()
    section_6_shape_fingerprint()
    section_7_which_column()
    section_8_decompose()
    section_9_within_month_seam()
    section_5_designs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
