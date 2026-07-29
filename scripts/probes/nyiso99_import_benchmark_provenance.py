"""nyiso-99: NYISO import hourly shape — benchmark audit + provenance gate.

Matrix §5.5 item 9 (import hourly shape, r_hr 0.45-0.61). No LP: this is the
build-time instrument that audits the SCORING TARGET before any mechanism is
chosen, in the shape nyiso-98 established
(``scripts/probes/nyiso98_nuclear_availability_provenance.py``).

Why this runs first
-------------------
nyiso-98 proved the EIA-930 ``NYIS`` feed posts reporting gaps as **exactly
0.0 MW** in the source parquet (not NaN, and not produced by the repo's
``_eia_hourly_frame_filled`` gap-bridging, which emits NaN). In ``NG: NUC``
that was 1,179 h (2023) / 380 h (2024) / 117 h (2025), and gap-masking
**inverted** the published r_day ordering — the lever queue's stated defect
did not exist as described. Item 9's target is a different series on the same
feed, so the same falsification is owed before a mechanism is chosen. The
audit is extended to ``NG: WAT`` and ``NG: OIL`` (the other two component
series nyiso-92 attributed against; ``NG: OIL`` r_day 0.07 is the loudest
remaining suspect).

Falsification instruments — both independent of EIA-930, both measured, both
already intaken under the 2026-07-10 owner authorization:

* **imports** — NYISO MIS **P-32** External Limits & Flows
  (``data/raw/NYISO/interface-flows``). The eleven ``SCH -`` rows are the
  external schedules; their hourly sum is NYCA net import measured at the
  ties, independently of EIA-930's BA-level accounting.
* **hydro / oil** — NYISO MIS **P-63** Real-Time Fuel Mix
  (``data/raw/NYISO/fuel-mix``). NYCA-total generation by NYISO's own
  seven-category taxonomy.

Rule 13: both are used here ONLY to falsify the benchmark, never as a
dispatch input. The measured net-interchange series is the scored outcome and
is forbidden as an input either way.

Sections
--------
``census``
    Zero-block and flat-block census of the four EIA-930 ``NYIS`` series on
    the model's 8760-hour clock, with the whole-row dropout structure
    (EIA-930 drops entire rows, which the reindex returns as NaN, separately
    from the exactly-0.0 artifact).
``falsify``
    Each candidate gap hour tested against its independent instrument. A
    suspect hour is FALSIFIED (a reporting artifact) when the instrument
    shows material activity the EIA-930 series reports as zero.
``baseline``
    The item-9 statistic itself — model-vs-target r_hr / r_day — reported
    RAW and GAP-MASKED, so the mechanism decision is taken against a target
    the audit has cleared. Needs ``--bundle``.

Usage::

    PYTHONPATH=.:src python scripts/probes/nyiso99_import_benchmark_provenance.py
    PYTHONPATH=.:src python scripts/probes/nyiso99_import_benchmark_provenance.py \\
        --sections baseline --bundle results/calibration/nyiso98_nucavail
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
BA = "NYIS"
YEARS = (2023, 2024, 2025)
IFACE_DIR = REPO / "data" / "raw" / "NYISO" / "interface-flows"
FUELMIX_DIR = REPO / "data" / "raw" / "NYISO" / "fuel-mix"

# The EIA-930 NYIS component series nyiso-92 attributed the hourly-r loss
# against, each with the independent instrument that can falsify a zero.
AUDIT_SERIES: tuple[tuple[str, str], ...] = (
    ("Total interchange", "P-32 external schedules"),
    ("NG: WAT", "P-63 Hydro"),
    ("NG: OIL", "P-63 Other Fossil Fuels"),
    ("NG: NUC", "(nyiso-98 reference)"),
)

# A flat run this long or longer is reported by the census. Four hours of a
# bit-identical MW value on a 5-minute-aggregated feed is not a market
# outcome; it is a hold-last-value artifact until an instrument says otherwise.
FLAT_RUN_MIN_HOURS = 4

# Material-activity thresholds for the falsification, in MW. A zero that the
# instrument contradicts by less than this is inside the two feeds' own
# accounting/rounding difference and is NOT called falsified.
FALSIFY_MW = {"Total interchange": 100.0, "NG: WAT": 100.0, "NG: OIL": 25.0}


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, 0.0 when either side is constant (no shape to correlate)."""
    if a.std() <= 0.0 or b.std() <= 0.0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _blocks(mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous ``(start, length)`` runs of True in ``mask``."""
    out: list[tuple[int, int]] = []
    start: int | None = None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            out.append((start, i - start))
            start = None
    if start is not None:
        out.append((start, len(mask) - start))
    return out


def eia_frame(year: int) -> pd.DataFrame:
    """The EIA-930 ``NYIS`` hourly frame on the model's 8760-hour clock."""
    from market_sim.data.eia930 import frames as fr

    frame = fr._eia_hourly_frame_filled(BA, year)
    if frame is None:
        raise RuntimeError(f"no EIA-930 frame for {BA} {year}")
    return frame.iloc[:8760]


def measured_import(year: int) -> np.ndarray:
    """EIA-930 measured NYCA net import MW, hour-of-year (positive = import).

    ``Total interchange`` is net **export** in the EIA sign convention, so the
    import series nyiso-92 scores against is its negation.
    """
    return -np.nan_to_num(eia_frame(year)["Total interchange"].to_numpy(float))


def _on_model_clock(ser: pd.Series, year: int) -> np.ndarray:
    """Reindex a UTC-stamped MIS series onto the EIA frame's 8760-hour clock.

    Aligning on UTC (not local time) is exact: the DST fall-back hour repeats
    a LOCAL stamp, which would collapse two distinct hours into one and leave
    the year 8,759 rows long. The EIA-930 frame is itself built on a UTC
    index, so joining there puts both feeds on literally the same hours.
    """
    idx = pd.DatetimeIndex(eia_frame(year)["UTC time"])
    if idx.tz is None:
        ser = ser.tz_localize(None)
    return ser.reindex(idx).to_numpy(float)


def p32_net_import(year: int) -> np.ndarray:
    """P-32 measured NYCA net import MW on the model's clock (positive = in).

    Sums the eleven external ``SCH -`` schedules. Internal transfer interfaces
    (TOTAL EAST, UPNY CONED, ...) are cutsets inside NYCA and are excluded.
    """
    df = pd.read_csv(IFACE_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz")
    df = df[df["interface"].str.startswith("SCH - ")]
    ts = pd.to_datetime(df["interval_start_utc"], utc=True)
    return _on_model_clock(df.assign(ts=ts).groupby("ts")["flow_mw"].sum(), year)


def p63_fuel(year: int, category: str) -> np.ndarray:
    """P-63 measured NYCA generation MW for one fuel category, model clock."""
    df = pd.read_csv(FUELMIX_DIR / f"NYISO_fuelmix_hourly_{year}.csv.gz")
    df = df[df["fuel_category"] == category]
    ts = pd.to_datetime(df["interval_start_utc"], utc=True)
    return _on_model_clock(df.assign(ts=ts).groupby("ts")["gen_mw"].sum(), year)


def instrument(year: int, column: str) -> np.ndarray | None:
    """The independent falsification instrument for one EIA-930 column."""
    if column == "Total interchange":
        return p32_net_import(year)
    if column == "NG: WAT":
        return p63_fuel(year, "Hydro")
    if column == "NG: OIL":
        return p63_fuel(year, "Other Fossil Fuels")
    return None


def suspect_mask(frame: pd.DataFrame, column: str) -> tuple[np.ndarray, np.ndarray]:
    """``(zero_mask, flat_mask)`` — the two artifact signatures nyiso-98 named.

    ``zero_mask`` is the exactly-0.0 signature (the nuclear artifact).
    ``flat_mask`` is a bit-identical run of at least
    :data:`FLAT_RUN_MIN_HOURS` hours at a NON-zero value (hold-last-value).
    """
    raw = frame[column].to_numpy(float)
    v = np.nan_to_num(raw)
    zero = (v == 0.0) & ~np.isnan(raw)
    same = np.r_[False, v[1:] == v[:-1]]
    flat = np.zeros(len(v), bool)
    for start, length in _blocks(same):
        if length + 1 >= FLAT_RUN_MIN_HOURS and v[start] != 0.0:
            flat[start - 1 : start + length] = True
    return zero, flat


def section_census() -> None:
    """Zero/flat-block census of the audited EIA-930 series."""
    print("\n=== census — EIA-930 NYIS artifact signatures (8760-h model clock) ===")
    print(
        f"{'year':<6}{'series':<20}{'NaN':>6}{'zero_h':>8}{'zero_blk':>9}"
        f"{'longest':>8}{'flat_h':>8}{'flat_blk':>9}{'longest':>8}"
    )
    for year in YEARS:
        frame = eia_frame(year)
        for column, _ in AUDIT_SERIES:
            zero, flat = suspect_mask(frame, column)
            zb, fb = _blocks(zero), _blocks(flat)
            print(
                f"{year:<6}{column:<20}"
                f"{int(frame[column].isna().sum()):>6}"
                f"{int(zero.sum()):>8}{len(zb):>9}"
                f"{max((n for _, n in zb), default=0):>8}"
                f"{int(flat.sum()):>8}{len(fb):>9}"
                f"{max((n for _, n in fb), default=0):>8}"
            )
    print(
        "\n  NaN = whole EIA-930 rows absent, returned by the reindex "
        "(a KNOWN gap, already excluded by np.nan_to_num at every consumer)."
    )
    print(
        "  zero_h/flat_h = the nyiso-98 artifact class: values PRESENT in the "
        "source that may not be real. These are what section `falsify` tests."
    )


def section_falsify() -> None:
    """Test every suspect hour against its independent measured instrument."""
    print("\n=== falsify — suspect EIA-930 hours vs independent instruments ===")
    for column, inst_name in AUDIT_SERIES:
        if column == "NG: NUC":
            continue
        thresh = FALSIFY_MW[column]
        print(f"\n-- {column}  vs  {inst_name}  (material = |inst| > {thresh:.0f} MW)")
        print(
            f"{'year':<6}{'agree_r':>9}{'agree_MW':>10}{'suspect_h':>11}"
            f"{'falsified':>11}{'confirmed':>11}{'inst_p50':>10}"
        )
        for year in YEARS:
            frame = eia_frame(year)
            eia = np.nan_to_num(frame[column].to_numpy(float))
            if column == "Total interchange":
                eia = -eia
            inst = instrument(year, column)
            assert inst is not None
            # An hour is testable only where BOTH feeds report. The instrument
            # reindex can itself leave gaps; those hours judge nothing.
            clean = ~frame[column].isna().to_numpy() & ~np.isnan(inst)
            zero, flat = suspect_mask(frame, column)
            susp = (zero | flat) & clean
            # Agreement on the NON-suspect hours establishes the instrument is
            # measuring the same quantity before it is used to judge a gap.
            ok = clean & ~susp
            hit = np.abs(inst[susp]) > thresh if susp.any() else np.zeros(0, bool)
            print(
                f"{year:<6}{_r(eia[ok], inst[ok]):>9.3f}"
                f"{float(np.mean(eia[ok] - inst[ok])):>10.1f}"
                f"{int(susp.sum()):>11}{int(hit.sum()):>11}"
                f"{int(susp.sum() - hit.sum()):>11}"
                f"{(float(np.median(np.abs(inst[susp]))) if susp.any() else 0.0):>10.1f}"
            )
        print(
            "  agree_r/agree_MW = hourly r and mean bias on the CLEAN hours "
            "(the instrument's own validation)."
        )
        print(
            "  falsified = suspect hours the instrument contradicts (artifact); "
            "confirmed = suspect hours the instrument corroborates (real)."
        )


def model_import(bundle: Path, year: int) -> np.ndarray:
    """Model hourly import-node MW from the bundle's P1 class sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == "import")]
    return df.sort_values("hour")["mw"].to_numpy(float)[:8760]


def section_baseline(bundle: Path) -> None:
    """Item 9's own statistic, raw and gap-masked, plus the shape layers."""
    print(f"\n=== baseline — import shape vs target ({bundle.name}) ===")
    print(
        f"{'year':<6}{'modTWh':>8}{'actTWh':>8}{'r_hr':>7}{'r_hr_msk':>9}"
        f"{'r_day':>7}{'r_dy_msk':>9}{'r_prof':>8}{'r_wday':>8}{'r_p32':>7}"
    )
    for year in YEARS:
        frame = eia_frame(year)
        act = measured_import(year)
        mod = model_import(bundle, year)
        zero, flat = suspect_mask(frame, "Total interchange")
        keep = ~(zero | flat) & ~frame["Total interchange"].isna().to_numpy()
        md, ad = mod.reshape(365, 24), act.reshape(365, 24)
        kd = keep.reshape(365, 24).all(1)
        print(
            f"{year:<6}{mod.sum() / 1e6:>8.2f}{act.sum() / 1e6:>8.2f}"
            f"{_r(mod, act):>7.3f}{_r(mod[keep], act[keep]):>9.3f}"
            f"{_r(md.sum(1), ad.sum(1)):>7.3f}"
            f"{_r(md.sum(1)[kd], ad.sum(1)[kd]):>9.3f}"
            f"{_r(md.mean(0), ad.mean(0)):>8.3f}"
            f"{_r((md - md.mean(1, keepdims=True)).ravel(), (ad - ad.mean(1, keepdims=True)).ravel()):>8.3f}"
            f"{_r(mod, p32_net_import(year)):>7.3f}"
        )
    print(
        "  r_hr_msk/r_dy_msk = the same statistic with every suspect hour "
        "(and, daily, every day holding one) dropped."
    )
    print("  r_p32 = model vs the INDEPENDENT P-32 instrument — a target cross-check.")


def main(argv: list[str] | None = None) -> int:
    """Run the requested audit sections."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sections",
        nargs="+",
        default=["census", "falsify"],
        choices=["census", "falsify", "baseline"],
    )
    parser.add_argument("--bundle", type=Path, default=None)
    args = parser.parse_args(argv)

    if "census" in args.sections:
        section_census()
    if "falsify" in args.sections:
        section_falsify()
    if "baseline" in args.sections:
        if args.bundle is None:
            print("\n(baseline needs --bundle)")
            return 2
        section_baseline(args.bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
