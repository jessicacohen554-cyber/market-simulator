"""Measure whether NWPP hydro behaviour changed across the 1997 Pacific Northwest
Coordination Agreement's termination (2024-09-15).

Lane NWPP-38 (desk r#7 charter, 2026-09-16). **Zero LP** (rule 32 `[R-SHARD]`).
This is a MEASUREMENT, not a mechanism: nothing here is tuned, no residual is
consulted, and no `ScenarioConfig` field is read or written (rules 1, 13, 23).

Context. `docs/handoffs/FINDING-nwpp-32-2026-09-14.md` §4 established that the PNCA
-- the instrument that defines *"Period means a calendar month"*, i.e. the accounting
period the repo's hydro budget already uses -- **terminated 2024-09-15, inside the
2023-2025 scored window, with no successor text found**. There is no successor
instrument to model to, so there is no code fix; what is missing is evidence about
whether the termination changed observable behaviour at all. This script produces it.

Design (fixed before any metric was computed; see the FINDING's identification section):

* TREATED  = BPAT CHPD DOPD GCPD -- 92.6 / 97.1 / 100 / 100 % of each balancing
  authority's conventional-hydro nameplate sits on the coordinated Columbia system.
* CONTROL  = PGE TPWR PACW -- 100 % `INDEPENDENT_OR_TRIBUTARY` in the budget
  artifact's own `chain` column (Deschutes/Willamette/Clackamas, Nisqually/Cowlitz,
  Lewis/Rogue), hydraulically outside the PNCA's coordination object.
* REPORTED, IN NEITHER GROUP = IPCO SCL AVA NWMT (mixed coordinated/independent).
* EXCLUDED = WAUW PACE NEVP (FINDING-nwpp-32 §3.2 population mismatch), AVRN GRID
  (no hydro), PSEI (its 2019-2020 `NG: WAT` is unusable -- see the screen below).

Every metric is **scale-free**, so the monthly energy level -- which the model's
monthly budget already fixes by construction -- divides out and cannot drive a result.

Screen. Lane NWPP-37's repair of the EIA-930 fuel-column seam had NOT landed at this
script's base sha, so the defective hours are screened HERE: a defective hour is
`|NG: WAT| > 1.15 x` the balancing authority's EIA-860 conventional-hydro nameplate,
or `< -0.05 x` it, or NaN. Defective hours are DROPPED, never imputed, and the whole
local day is dropped from every day-level metric. EIA's own `(Adjusted)` hydro column
is carried only as a robustness check: it is imputed as well as screened, so it cannot
be the primary series for a measurement about SHAPE.

Usage
-----
    python scripts/data/measure_nwpp_pnca_discontinuity.py

Writes, under `data/raw/nwpp-hydro/`:
    nwpp_pnca_day_metrics.parquet  per balancing authority x local day
    nwpp_pnca_month_metrics.csv  per balancing authority x month
    nwpp_pnca_links.csv          per adjacent-pair x month (coupling r and lag)
and prints every table the FINDING reports.
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

TREATED = ["BPAT", "CHPD", "DOPD", "GCPD"]
CONTROL = ["PGE", "TPWR", "PACW"]
MIXED = ["IPCO", "SCL", "AVA", "NWMT"]
ALL_BAS = TREATED + CONTROL + MIXED

#: The instrument date. 1997 Pacific Northwest Coordination Agreement section 1(a),
#: read in NWPP-32 (`docs/handoffs/FINDING-nwpp-32-2026-09-14.md` §4).
PNCA_TERMINATION = pd.Timestamp("2024-09-15")

#: EIA-930 legacy taxonomy (through 2024 H1) and the mid-2024 revamp. Pumped storage
#: is broken out separately only in the new one; measured here, the new taxonomy's
#: pumped-storage column is null in **every** hour of **every** NWPP balancing
#: authority, so the two hydro columns are the same basis on this footprint and the
#: taxonomy switch cannot masquerade as an instrument effect.
_LEGACY_HYDRO = "Net Generation (MW) from Hydropower and Pumped Storage"
_NEW_HYDRO = "Net Generation (MW) from Hydropower Excluding Pumped Storage"
_NEW_PS = "Net Generation (MW) from Pumped Storage"

#: Defect thresholds, as multiples of the balancing authority's own nameplate.
_DEFECT_HIGH = 1.15
_DEFECT_NEG = -0.05

#: (t_{.975,n-1} + t_{.80,n-1}) * sqrt(1 + 1/n) for n = 5 pre-period observations --
#: the multiplier on the pre-period SD that gives the minimum effect detectable at
#: alpha = 0.05 two-sided with 80 % power when one new draw is tested against n.
_MDE_K5 = float((stats.t.ppf(0.975, 4) + stats.t.ppf(0.80, 4)) * np.sqrt(1 + 1 / 5))


def ba_nameplate_930_basis() -> pd.Series:
    """Conventional-hydro nameplate per balancing authority, on the EIA-930 basis.

    EIA-860 files Priest Rapids (plant 3887) under BPAT; EIA-930 generates it inside
    GCPD (`FINDING-nwpp-32-2026-09-14.md` §3.2). The screen compares a 930 series to
    a nameplate, so the 930 assignment is the right one.
    """
    budget = pd.read_parquet(RAW_DATA_DIR / "nwpp-hydro" / "nwpp_hydro_budget.parquet")
    budget = budget[budget.year == 2023]
    ba930 = np.where(budget.plant_id == 3887, "GCPD", budget.ba_code)
    return budget.assign(ba930=ba930).groupby("ba930")["max_mw_eia860"].sum()


def load_panel(first_year: int = 2019, last_year: int = 2025) -> pd.DataFrame:
    """Build the per-balancing-authority hourly hydro panel from the BALANCE archive.

    The committed per-BA wide extracts (`data/raw/eia-930-hourly/<BA> hourly.parquet`)
    start at 2023 for the NWPP balancing authorities, which leaves only one pre-period
    year. The BALANCE archive the extracts were themselves derived from covers 2019
    onwards for all 62 balancing authorities, so the pre-period is extended here by the
    same derive -- and checked against the committed extract on the overlap by
    :func:`verify_against_committed_extract`, which must report zero mismatches.
    """
    frames = []
    for path in sorted(
        glob.glob(str(RAW_DATA_DIR / "eia-930" / "EIA930_BALANCE_*.parquet"))
    ):
        tag = re.search(r"BALANCE_(\d{4})_", path)
        if tag is None or not (first_year <= int(tag.group(1)) <= last_year):
            continue
        names = set(pq.ParquetFile(path).schema_arrow.names)
        hydro = _LEGACY_HYDRO if _LEGACY_HYDRO in names else _NEW_HYDRO
        adjusted = f"{hydro} (Adjusted)"
        want = [
            "Balancing Authority",
            "UTC Time at End of Hour",
            "Local Time at End of Hour",
            hydro,
        ]
        if adjusted in names:
            want.append(adjusted)
        if _NEW_PS in names:
            want.append(_NEW_PS)
        frame = pd.read_parquet(path, columns=want)
        frame = frame[frame["Balancing Authority"].isin(ALL_BAS)].copy()
        frame = frame.rename(
            columns={
                "Balancing Authority": "ba",
                "UTC Time at End of Hour": "utc",
                "Local Time at End of Hour": "local",
                hydro: "wat",
                adjusted: "wat_adj",
            }
        )
        if "wat_adj" not in frame:
            frame["wat_adj"] = np.nan
        frame["ps"] = frame[_NEW_PS] if _NEW_PS in frame else np.nan
        frame["taxonomy"] = "legacy" if hydro == _LEGACY_HYDRO else "new"
        frames.append(frame[["ba", "utc", "local", "wat", "wat_adj", "ps", "taxonomy"]])

    panel = pd.concat(frames, ignore_index=True)
    panel["utc"] = pd.to_datetime(panel["utc"], utc=True, format="mixed")
    panel["local"] = pd.to_datetime(panel["local"].str.slice(0, 19), format="mixed")
    panel = panel.sort_values(["ba", "utc"]).drop_duplicates(
        ["ba", "utc"], keep="first"
    )
    panel["date"] = panel["local"].dt.normalize()
    panel["year"] = panel["date"].dt.year
    panel = panel[panel.year.between(first_year, last_year)].reset_index(drop=True)

    nameplate = ba_nameplate_930_basis()
    panel["np_mw"] = panel.ba.map(nameplate)
    panel["flag_high"] = panel.wat.abs() > _DEFECT_HIGH * panel.np_mw
    panel["flag_neg"] = panel.wat < _DEFECT_NEG * panel.np_mw
    panel["flag_nan"] = panel.wat.isna()
    panel["defect"] = panel.flag_high | panel.flag_neg | panel.flag_nan
    panel["bad_day"] = (
        panel.groupby(["ba", "date"])["defect"].transform("max").astype(bool)
    )
    return panel


def verify_against_committed_extract(panel: pd.DataFrame) -> int:
    """Return the number of hours where the derive disagrees with NWPP-11's extract.

    Must be zero. The derive re-does, for 2019-2022, exactly what
    `build_nwpp_ba_hourly_from_balance.py` did for 2023-2025, so the overlap is the
    test that nothing about the construction drifted.
    """
    mismatches = 0
    for ba in sorted(panel.ba.unique()):
        path = RAW_DATA_DIR / "eia-930-hourly" / f"{ba} hourly.parquet"
        if not path.exists():
            continue
        committed = pd.read_parquet(path, columns=["UTC time", "NG: WAT"])
        committed["utc"] = pd.to_datetime(committed["UTC time"], utc=True)
        merged = panel[panel.ba == ba].merge(committed[["utc", "NG: WAT"]], on="utc")
        delta = (
            merged.wat.astype("float64") - merged["NG: WAT"].astype("float64")
        ).abs()
        mismatches += int((delta > 1e-6).sum())
    return mismatches


def day_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    """Day-level shaping metrics on clean, complete local days.

    ``D1`` diurnal amplitude ``(max - min) / mean`` of the 24 hourly MW.
    ``D2`` intraday ramp ``mean |dP/dt| / mean P``.
    """
    clean = panel[~panel.bad_day]
    day = (
        clean.groupby(["ba", "date"])
        .agg(
            n=("wat", "size"),
            mean=("wat", "mean"),
            mx=("wat", "max"),
            mn=("wat", "min"),
        )
        .reset_index()
    )
    day = day[day.n == 24]
    ramped = clean.sort_values(["ba", "utc"]).copy()
    ramped["absdelta"] = ramped.groupby(["ba", "date"])["wat"].diff().abs()
    day = day.merge(
        ramped.groupby(["ba", "date"])["absdelta"].mean().reset_index(name="absramp"),
        on=["ba", "date"],
    )
    day["D1"] = (day.mx - day.mn) / day["mean"]
    day["D2"] = day.absramp / day["mean"]
    day["year"] = day.date.dt.year
    day["month"] = day.date.dt.month
    return day


def month_metrics(panel: pd.DataFrame, day: pd.DataFrame) -> pd.DataFrame:
    """Month-level shaping metrics, on months carrying at least 26 clean days.

    ``M1`` within-month coefficient of variation of daily energy.
    ``M2`` ``(p95 - p5) / mean`` of the hourly MW.
    """
    per_month = (
        day.groupby(["ba", "year", "month"])
        .agg(ndays=("date", "size"), M1=("mean", lambda s: s.std(ddof=1) / s.mean()))
        .reset_index()
    )
    clean = panel[~panel.bad_day]
    hourly = (
        clean.groupby(
            [
                "ba",
                clean.date.dt.year.rename("year"),
                clean.date.dt.month.rename("month"),
            ]
        )["wat"]
        .agg(
            mean="mean", p95=lambda s: s.quantile(0.95), p05=lambda s: s.quantile(0.05)
        )
        .reset_index()
    )
    hourly["M2"] = (hourly.p95 - hourly.p05) / hourly["mean"]
    out = per_month.merge(
        hourly[["ba", "year", "month", "mean", "M2"]], on=["ba", "year", "month"]
    )
    return out[out.ndays >= 26]


def link_metrics(panel: pd.DataFrame, links: list[tuple[str, str]]) -> pd.DataFrame:
    """Per link-month hourly coupling, after removing each series' own shape.

    Each balancing authority's month-by-hour-of-day mean profile is subtracted first,
    so ``r0`` measures co-movement of the DEVIATIONS -- the hydraulic signal -- rather
    than the shared diurnal profile any two load-following hydro systems would share.
    ``lag`` is the argmax of the cross-correlation over |lag| <= 6 h.
    """
    clean = panel[~panel.defect]
    wide = clean.pivot_table(index="utc", columns="ba", values="wat").sort_index()
    rows = []
    for upstream, downstream in links:
        pair = wide[[upstream, downstream]].dropna()
        keys = [pair.index.year, pair.index.month]
        for (year, month), grp in pair.groupby(keys):
            if len(grp) < 600:
                continue
            hod = grp.index.hour
            a = grp[upstream].to_numpy(dtype=float).copy()
            b = grp[downstream].to_numpy(dtype=float).copy()
            for arr in (a, b):
                for h in range(24):
                    mask = hod == h
                    if mask.any():
                        arr[mask] -= arr[mask].mean()
            if a.std() == 0 or b.std() == 0:
                continue
            best_r, best_lag = -2.0, 0
            for lag in range(-6, 7):
                x = a[: len(a) - lag] if lag > 0 else (a[-lag:] if lag < 0 else a)
                y = b[lag:] if lag > 0 else (b[:lag] if lag < 0 else b)
                if len(x) < 500:
                    continue
                r = float(np.corrcoef(x, y)[0, 1])
                if r > best_r:
                    best_r, best_lag = r, lag
            rows.append(
                dict(
                    link=f"{upstream}->{downstream}",
                    year=int(year),
                    month=int(month),
                    r0=float(np.corrcoef(a, b)[0, 1]),
                    rmax=best_r,
                    lag=best_lag,
                    n=len(grp),
                )
            )
    return pd.DataFrame(rows)


def window_contrast(day: pd.DataFrame) -> pd.DataFrame:
    """Design A: the seasonal contrast whose boundary IS the termination date.

    ``Delta = metric(Sep 15 - Nov 28) - metric(Jul 1 - Sep 14)``. In 2024 that boundary
    is 2024-09-15 itself; in 2019-2023 the same calendar contrast is a PLACEBO, and
    those five placebos are what the 2024 contrast is scored against. Seasonality is
    differenced out by construction, and the two windows sit either side of one date,
    so a level change in the water year cancels to first order.
    """
    rows = []
    for ba in sorted(day.ba.unique()):
        d = day[day.ba == ba]
        for year in range(2019, 2026):
            a = d[
                (d.date >= pd.Timestamp(year, 7, 1))
                & (d.date <= pd.Timestamp(year, 9, 14))
            ]
            b = d[
                (d.date >= pd.Timestamp(year, 9, 15))
                & (d.date <= pd.Timestamp(year, 11, 28))
            ]
            if len(a) < 60 or len(b) < 60:
                continue
            rows.append(
                dict(
                    ba=ba,
                    year=year,
                    dD1=b.D1.mean() - a.D1.mean(),
                    dD2=b.D2.mean() - a.D2.mean(),
                )
            )
    return pd.DataFrame(rows)


def post_window(day: pd.DataFrame) -> pd.DataFrame:
    """Design B: the metric over Sep 15 - Dec 31, the window the termination opens.

    Unlike design A this is a LEVEL in one window rather than a contrast across the date,
    so it is the more exposed of the two to the water year -- which is why it is reported
    beside design A and the hydrology-controlled design D rather than on its own.
    """
    rows = []
    for ba in sorted(day.ba.unique()):
        d = day[day.ba == ba]
        for year in range(2019, 2026):
            w = d[
                (d.date >= pd.Timestamp(year, 9, 15))
                & (d.date <= pd.Timestamp(year, 12, 31))
            ]
            if len(w) < 90:
                continue
            rows.append(
                dict(
                    ba=ba,
                    year=year,
                    D1=w.D1.mean(),
                    D2=w.D2.mean(),
                    lvl=w["mean"].mean(),
                    TWh=w["mean"].mean() * 8760 / 1e6,
                )
            )
    return pd.DataFrame(rows)


def local_jump(day: pd.DataFrame, metric: str, halfwidth: int = 28) -> pd.DataFrame:
    """Design A-RD: the LOCAL discontinuity at Sep 15, with a linear trend either side.

    Fitting ``metric ~ 1 + x + post + x*post`` over a narrow window removes the year's
    seasonal path, so the estimated ``post`` coefficient is a jump rather than a
    seasonal difference. The 2019-2023 jumps at the same calendar date are the
    reference distribution -- which is the honest one, because a jump estimated at an
    arbitrary date is never exactly zero.
    """
    rows = []
    for ba in sorted(day.ba.unique()):
        d = day[day.ba == ba]
        row = {"ba": ba}
        for year in range(2019, 2026):
            t0 = pd.Timestamp(year, 9, 15)
            w = d[
                (d.date >= t0 - pd.Timedelta(days=halfwidth))
                & (d.date < t0 + pd.Timedelta(days=halfwidth))
            ].copy()
            if len(w) < 2 * halfwidth - 6:
                row[year] = np.nan
                continue
            x = (w.date - t0).dt.days.to_numpy(dtype=float)
            post = (x >= 0).astype(float)
            design = np.column_stack([np.ones(len(w)), x, post, x * post])
            beta, *_ = np.linalg.lstsq(
                design, w[metric].to_numpy(dtype=float), rcond=None
            )
            row[year] = beta[2]
        rows.append(row)
    return pd.DataFrame(rows).set_index("ba")


def boundary_excess(day: pd.DataFrame) -> pd.DataFrame:
    """The test aimed at the instrument's own content: does the calendar month matter?

    The PNCA's operative definition is *"Period means a calendar month"*. If a
    calendar-month accounting period binds and then stops binding, the month BOUNDARY
    should stop being a special place in the daily-energy series. Daily energy is
    normalised by a CENTRED 31-day rolling mean -- deliberately NOT by the calendar
    month's own mean, which would inject a mechanical step at every boundary and was
    measured to inflate this ratio from ~1.2 to ~2.5 when tried that way. The statistic
    is ``mean |day-to-day step| on month-end days / the same on days 11-19``; 1.0 means
    the boundary is not special at all.
    """
    rows = []
    for ba in sorted(day.ba.unique()):
        s = day[day.ba == ba].sort_values("date").set_index("date")["mean"]
        s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
        z = s / s.rolling(31, center=True, min_periods=25).mean()
        step = (z.shift(-1) - z).abs()
        f = pd.DataFrame({"step": step.to_numpy()}, index=z.index)
        f["is_end"] = f.index.to_series().dt.is_month_end.to_numpy()
        f["is_mid"] = f.index.to_series().dt.day.between(11, 19).to_numpy()
        f["year"] = f.index.year
        f["half"] = np.where(f.index.month <= 6, "H1", "H2")
        for (year, half), grp in f.groupby(["year", "half"]):
            ends = grp.loc[grp.is_end, "step"].dropna()
            mids = grp.loc[grp.is_mid, "step"].dropna()
            if len(ends) < 4 or len(mids) < 25:
                continue
            rows.append(
                dict(ba=ba, year=year, half=half, ratio=ends.mean() / mids.mean())
            )
    return pd.DataFrame(rows)


def placebo_table(
    values: pd.DataFrame, pre_years=(2019, 2020, 2021, 2022, 2023)
) -> pd.DataFrame:
    """Score each post year against the pre-period distribution, with the MDE beside it.

    ``MDE`` is the minimum effect this comparison could detect at alpha = 0.05
    two-sided and 80 % power. A deviation smaller than it is a NULL, not a small
    effect -- which is the distinction this lane exists to make.
    """
    pre = values[list(pre_years)]
    out = pd.DataFrame(
        {"pre_mean": pre.mean(axis=1), "pre_sd": pre.std(axis=1, ddof=1)}
    )
    out["MDE"] = _MDE_K5 * out.pre_sd
    for year in (2024, 2025):
        if year in values:
            out[f"y{year}"] = values[year]
            out[f"z{year % 100}"] = (values[year] - out.pre_mean) / out.pre_sd
    return out


def did(frame: pd.DataFrame, metric: str, water_control: bool = True):
    """Two-way-fixed-effects difference-in-differences with year-clustered errors.

    Balancing-authority and calendar-month fixed effects; ``T_post`` is the treated x
    post interaction. ``water_control`` adds ``log(month mean MW)``, which is the
    explicit separation of the instrument from the water year: hydrology enters the
    shaping metric through the level, so conditioning on the level is what stops a wet
    or dry year being read as a change in operating regime. Errors are clustered on
    the year, the level at which treatment varies -- G = 7, which is the binding
    constraint on this lane's power and is reported as such.
    """
    d = frame.dropna(subset=[metric, "loglvl"])
    design = pd.concat(
        [
            pd.Series(1.0, index=d.index, name="const"),
            pd.get_dummies(d.ba, prefix="ba", drop_first=True).astype(float),
            pd.get_dummies(d.month, prefix="mo", drop_first=True).astype(float),
        ],
        axis=1,
    )
    design["post"] = d.post.to_numpy()
    design["T_post"] = (d["T"] * d.post).to_numpy()
    if water_control:
        design["loglvl"] = d.loglvl.to_numpy()
    x = design.to_numpy(dtype=float)
    y = d[metric].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    xtxi = np.linalg.pinv(x.T @ x)
    meat = np.zeros((x.shape[1], x.shape[1]))
    years = d.year.to_numpy()
    for year in np.unique(years):
        mask = years == year
        u = x[mask].T @ resid[mask]
        meat += np.outer(u, u)
    n_clusters = len(np.unique(years))
    n, k = x.shape
    cov = xtxi @ meat @ xtxi * (n_clusters / (n_clusters - 1)) * ((n - 1) / (n - k))
    i = list(design.columns).index("T_post")
    return beta[i], float(np.sqrt(cov[i, i])), n_clusters, float(d[metric].mean()), n


def _panel_for_did(day: pd.DataFrame, month: pd.DataFrame, cut: int) -> pd.DataFrame:
    per_month = (
        day.groupby(["ba", "year", "month"])
        .agg(
            D1=("D1", "mean"),
            D2=("D2", "mean"),
            lvl=("mean", "mean"),
            nd=("date", "size"),
        )
        .reset_index()
    )
    per_month = per_month[per_month.nd >= 26]
    frame = month.merge(
        per_month[["ba", "year", "month", "D1", "D2", "lvl"]],
        on=["ba", "year", "month"],
    )
    frame = frame[frame.ba.isin(TREATED + CONTROL)].copy()
    frame["T"] = frame.ba.isin(TREATED).astype(float)
    frame["t"] = frame.year * 12 + frame.month
    frame["post"] = (frame.t > cut).astype(float)
    frame["loglvl"] = np.log(frame.lvl)
    return frame[frame.t != cut]  # the straddling month is dropped, never split


def main() -> None:
    out_dir = RAW_DATA_DIR / "nwpp-hydro"
    panel = load_panel()
    mismatches = verify_against_committed_extract(panel)
    print(
        f"derive vs committed NWPP-11 extract: {mismatches} mismatched hours (must be 0)"
    )
    print(
        f"pumped-storage column non-null rows on this footprint: {int(panel.ps.notna().sum())}"
    )
    print("\ndefective hours by balancing authority x year:")
    print(panel.groupby(["ba", "year"])["defect"].sum().unstack().to_string())

    day = day_metrics(panel)
    month = month_metrics(panel, day)
    links = link_metrics(
        panel,
        [
            ("BPAT", "DOPD"),
            ("DOPD", "CHPD"),
            ("CHPD", "GCPD"),
            ("BPAT", "GCPD"),
            ("PGE", "TPWR"),
            ("PGE", "PACW"),
            ("TPWR", "PACW"),
        ],
    )
    day.to_parquet(out_dir / "nwpp_pnca_day_metrics.parquet", index=False)
    month.to_csv(out_dir / "nwpp_pnca_month_metrics.csv", index=False)
    links.to_csv(out_dir / "nwpp_pnca_links.csv", index=False)

    order = TREATED + CONTROL + MIXED
    print("\n=== design C: full-calendar-year metrics, scored against 2019-2023 ===")
    annual = (
        day.groupby(["ba", "year"])
        .agg(D1=("D1", "mean"), D2=("D2", "mean"))
        .reset_index()
    )
    annual_m = (
        month.groupby(["ba", "year"])
        .agg(M1=("M1", "mean"), M2=("M2", "mean"))
        .reset_index()
    )
    annual = annual.merge(annual_m, on=["ba", "year"])
    for metric in ["D1", "D2", "M1", "M2"]:
        pivot = annual.pivot_table(index="ba", columns="year", values=metric).reindex(
            order
        )
        print(f"\n-- {metric} --")
        print(placebo_table(pivot).round(4).to_string())

    print(
        "\n=== design A: Delta = metric(Sep 15-Nov 28) - metric(Jul 1-Sep 14), 2024 boundary = the date ==="
    )
    contrast = window_contrast(day)
    for metric in ["dD1", "dD2"]:
        pivot = contrast.pivot_table(index="ba", columns="year", values=metric).reindex(
            order
        )
        print(f"\n-- {metric} --")
        print(placebo_table(pivot).round(4).to_string())

    print("\n=== design B: metric over Sep 15 - Dec 31, scored against 2019-2023 ===")
    window = post_window(day)
    for metric in ["D1", "D2", "lvl", "TWh"]:
        pivot = window.pivot_table(index="ba", columns="year", values=metric).reindex(
            order
        )
        print(f"\n-- {metric} --")
        print(placebo_table(pivot).round(4).to_string())

    print(
        "\n=== design A-RD: local jump at Sep 15 (+-28 d, linear trend either side) ==="
    )
    for metric in ["D1", "D2"]:
        jumps = local_jump(day, metric).reindex(order)
        print(f"\n-- {metric} --")
        print(
            pd.concat(
                [jumps.round(4), placebo_table(jumps).round(4)], axis=1
            ).to_string()
        )

    print(
        "\n=== month-boundary excess: is the calendar month still a special place? ==="
    )
    bnd = boundary_excess(day)
    for half in ("H2", "H1"):
        pivot = (
            bnd[bnd.half == half]
            .pivot_table(index="ba", columns="year", values="ratio")
            .reindex(order)
        )
        print(f"\n-- {half} (1.0 = the month boundary is not special at all) --")
        print(placebo_table(pivot).round(3).to_string())

    print("\n=== link structure: hourly r of deviations, and lag in hours ===")
    for metric in ["r0", "lag"]:
        pivot = links.pivot_table(
            index="link", columns="year", values=metric, aggfunc="mean"
        )
        print(f"\n-- {metric} --")
        print(placebo_table(pivot).round(4).to_string())

    print("\n=== design D: month-panel DiD, errors clustered on the year ===")
    frame = _panel_for_did(day, month, cut=2024 * 12 + 9)
    for metric in ["D1", "D2", "M1", "M2"]:
        for water in (False, True):
            b, se, g, mu, n = did(frame, metric, water)
            k = stats.t.ppf(0.975, g - 1) + stats.t.ppf(0.80, g - 1)
            crit = stats.t.ppf(0.975, g - 1)
            tag = "with water control " if water else "no water control   "
            print(
                f"{metric:3s} {tag} T_post {b:+.4f}  se {se:.4f}  "
                f"95% CI [{b - crit * se:+.4f},{b + crit * se:+.4f}]  "
                f"MDE {k * se:.4f} = {100 * k * se / mu:.1f}% of mean {mu:.3f}  n={n}"
            )

    print(
        "\n=== placebo termination dates: the same estimator, a fake date, +-2 y window ==="
    )
    rows = []
    for year in (2020, 2021, 2022, 2023, 2024):
        cut = year * 12 + 9
        window = _panel_for_did(day, month, cut)
        window = window[(window.t >= cut - 24) & (window.t <= cut + 24)]
        row = {"fake_date": f"{year}-09-15", "is_real": year == 2024}
        for metric in ["D1", "D2", "M1", "M2"]:
            b, se, *_ = did(window, metric, water_control=True)
            row[metric] = b
            row[f"{metric}_t"] = b / se
        rows.append(row)
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    print(
        f"\nPNCA termination: {PNCA_TERMINATION.date()}   artifacts written to {out_dir}"
    )


if __name__ == "__main__":
    main()
