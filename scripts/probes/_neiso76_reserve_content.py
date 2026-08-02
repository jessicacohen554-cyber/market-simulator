"""neiso-76 (b) — the nyiso-110 reserve-content decomposition, reproduced on
NEISO's OWN published ancillary prices. NO LP.

nyiso-110 decomposed NYISO's diurnal-amplitude miss and found it DOMINATED by
missing everyday reserve-price formation (measured DA spin > $1 in 100 % of
peak hours; the reserve differential owning 64-89 % of the missing DA swing).
**Rule 25: that verdict transfers nothing.** Whether NEISO's amplitude
decomposes the same way is NEISO's own question, and NEISO's answer has to be
measured on NEISO's own posted prices — which is what this probe does. The
construction is ported (peak/trough windows, differential vs missing swing,
passthrough slope, energy-basis restatement); every number is NEISO's.

Measured side — ISO Express **Final Hourly Reserve Zone Prices & Designations**
(report tree ``ancillary-hourly-rzpd-final``), CSV endpoint

    https://www.iso-ne.com/transform/csv/finalhourlyreserveprice?start=&end=

per hour-ending and reserve location: Ten-Minute Spinning (TMSR), Ten-Minute
Non-Spinning (TMNSR) and Total (30-minute, TMOR) reserve CLEARING prices plus
designated MW. Location ``7000`` = ROS, the system-wide row the model's own
reserve requirement consumes (``data/raw/NEISO-AS/requirements/README.md``).
TMSR is the top of ISO-NE's cascade — a spin provider's price internalises the
lower products — so it is the single-product opportunity-cost proxy, the same
role ``spin_10`` played at NYISO, and the conservative one.

**The structural asymmetry this probe exists to test.** These are REAL-TIME
reserve clearing prices. ISO-NE ran NO day-ahead ancillary-services market
before Day-Ahead Ancillary Services (DASI) went live 2025-03-01; NYISO has
posted DA spin every hour of every year on record. If NEISO's DA energy price
carries no reserve component by market design, then the DA half of NEISO's
amplitude gap CANNOT be the nyiso-110 defect, whatever the RT half does.

Model side — the keeper's own ``hourly/system_<year>.parquet`` (`reserve_price`
column, the co-optimization duals folded into the energy price by
construction), resolved through the live keeper store.

Rule 13: measured prices are the VALIDATION TARGET here and are never fed to a
solve. The raw window CSVs are gitignored; this probe regenerates them.

Usage:
    python scripts/probes/_neiso76_reserve_content.py --fetch   # ~36 requests
    python scripts/probes/_neiso76_reserve_content.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import NEISO_AS_DIR  # noqa: E402

RESERVE_DIR = NEISO_AS_DIR / "reserve-prices"
KEEPER_DIR = REPO / "frontend/data/backcast/keepers"
REGISTRY_DIR = REPO / "frontend/data/backcast/registry"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet"

CSV_ENDPOINT = "https://www.iso-ne.com/transform/csv/finalhourlyreserveprice"
REPORT_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/"
    "ancillary-hourly-rzpd-final"
)
#: Day-Ahead Ancillary Services (DASI) hourly requirements/prices/designations
#: — ISO-NE's DAY-AHEAD reserve clearing prices, published from go-live only.
DAAS_ENDPOINT = "https://www.iso-ne.com/transform/csv/daasreservedata"
#: System-wide reserve location ("Rest Of System"); the local reserve zones
#: (7001 SWCT / 7002 CT / 7003 NEMABSTN) carry 30-minute product only.
ROS_LOCATION = "7000"

#: The xiso-1 / charter windows, hours-BEGINNING (the model's 0-based clock).
PEAK_HOURS = (16, 17, 18, 19)
TROUGH_HOURS = (1, 2, 3, 4)

#: nyiso-110's body-censoring convention for the "is this event tail?" control.
CENSOR = 200.0

#: Non-leap month-start hours (the repo's fixed 8760 calendar).
_MONTH_START_HOUR = np.cumsum(
    [0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)]
)

#: ISO-NE Day-Ahead Ancillary Services (DASI) go-live — before this date there
#: is NO day-ahead reserve product, hence no DA reserve price to strip.
DASI_GO_LIVE = pd.Timestamp("2025-03-01")


def _hour_index(dates: pd.DatetimeIndex, he: np.ndarray) -> np.ndarray:
    """(local date, hour-ending) -> non-leap hour-of-year index; Feb 29 -> -1."""
    month = dates.month.to_numpy()
    day = dates.day.to_numpy()
    base = _MONTH_START_HOUR[month - 1]
    idx = base + (day - 1) * 24 + (np.asarray(he, int) - 1)
    return np.where((month == 2) & (day == 29), -1, idx)


# --------------------------------------------------------------------------
def _opener():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "neiso_fetch", REPO / "scripts" / "data" / "fetch_neiso_da_energy_offers.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._opener()


def fetch(years: list[int]) -> None:
    """Download one CSV per calendar month (the endpoint 500s on a bare day)."""
    import time
    import urllib.request

    RESERVE_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    for year in years:
        for month in range(1, 13):
            start = pd.Timestamp(year=year, month=month, day=1)
            end = start + pd.offsets.MonthEnd(0)
            dest = RESERVE_DIR / f"rzpd_final_{start:%Y%m%d}_{end:%Y%m%d}.csv"
            if dest.exists() and dest.stat().st_size > 1000:
                continue
            url = f"{CSV_ENDPOINT}?start={start:%Y%m%d}&end={end:%Y%m%d}"
            req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
            with opener.open(req, timeout=180) as resp:
                body = resp.read()
            if b"Reserve Zone Prices" not in body[:200]:
                raise SystemExit(f"unexpected response from {url}")
            dest.write_bytes(body)
            print(f"  fetched {dest.name} ({len(body):,} bytes)", flush=True)
            time.sleep(0.5)


def fetch_daas(years: list[int]) -> None:
    """Download the DAAS day-ahead reserve report, month by month.

    Coverage is measured, not assumed: months before DASI go-live return a
    header-only report (0 data rows) and are written anyway so the emptiness
    is on the record.
    """
    import time
    import urllib.request

    RESERVE_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    for year in years:
        if year < DASI_GO_LIVE.year:
            continue
        for month in range(1, 13):
            start = pd.Timestamp(year=year, month=month, day=1)
            end = start + pd.offsets.MonthEnd(0)
            dest = RESERVE_DIR / f"daas_{start:%Y%m%d}_{end:%Y%m%d}.csv"
            if dest.exists() and dest.stat().st_size > 400:
                continue
            url = f"{DAAS_ENDPOINT}?start={start:%Y%m%d}&end={end:%Y%m%d}"
            req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
            with opener.open(req, timeout=180) as resp:
                body = resp.read()
            dest.write_bytes(body)
            n = body.count(b'"D"')
            print(f"  fetched {dest.name} ({len(body):,} bytes, {n} rows)", flush=True)
            time.sleep(0.5)


def load_daas(years: list[int]) -> pd.DataFrame:
    """ROS hourly DAY-AHEAD reserve clearing prices (DASI), model 8760 clock."""
    rows = []
    for p in sorted(RESERVE_DIR.glob("daas_*.csv")):
        with p.open(newline="") as fh:
            for r in csv.reader(fh):
                if not r or r[0] != "D" or len(r) < 11:
                    continue
                if r[3].strip() != ROS_LOCATION:
                    continue
                he_raw = r[2].strip().upper()
                if he_raw.endswith("X"):
                    continue
                try:
                    rows.append(
                        (
                            pd.Timestamp(r[1]),
                            int(he_raw),
                            float(r[8] or 0.0),
                            float(r[9] or 0.0),
                            float(r[10] or 0.0),
                        )
                    )
                except ValueError:
                    continue
    if not rows:
        return pd.DataFrame(columns=["date", "he", "tmsr", "tmnsr", "total", "year", "hour"])
    df = pd.DataFrame(rows, columns=["date", "he", "tmsr", "tmnsr", "total"])
    df["year"] = df["date"].dt.year
    df = df[df["year"].isin(years)].copy()
    df["hour"] = _hour_index(pd.DatetimeIndex(df["date"]), df["he"].to_numpy())
    return df[df["hour"] >= 0].sort_values(["year", "hour"]).reset_index(drop=True)


def load_reserve(years: list[int]) -> pd.DataFrame:
    """ROS hourly reserve clearing prices on the model's 8760 calendar."""
    rows = []
    for p in sorted(RESERVE_DIR.glob("rzpd_final_*.csv")):
        with p.open(newline="") as fh:
            for r in csv.reader(fh):
                if not r or r[0] != "D" or len(r) < 7:
                    continue
                if r[3].strip() != ROS_LOCATION:
                    continue
                he_raw = r[2].strip().upper()
                if he_raw.endswith("X"):  # DST fall-back repeat: label-keyed drop
                    continue
                try:
                    rows.append(
                        (
                            pd.Timestamp(r[1]),
                            int(he_raw),
                            float(r[4] or 0.0),
                            float(r[5] or 0.0),
                            float(r[6] or 0.0),
                        )
                    )
                except ValueError:
                    continue
    if not rows:
        raise SystemExit(f"no reserve rows under {RESERVE_DIR} — run with --fetch")
    df = pd.DataFrame(rows, columns=["date", "he", "tmsr", "tmnsr", "total"])
    df["year"] = df["date"].dt.year
    df = df[df["year"].isin(years)].copy()
    df["hour"] = _hour_index(pd.DatetimeIndex(df["date"]), df["he"].to_numpy())
    return df[df["hour"] >= 0].sort_values(["year", "hour"]).reset_index(drop=True)


def keeper_bundle() -> tuple[str, Path]:
    kid = json.loads((KEEPER_DIR / "NEISO.json").read_text())["keeper"]
    bundle = json.loads((REGISTRY_DIR / f"{kid}.json").read_text())["bundle"]
    return kid, REPO / bundle


def model_price(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """(load-weighted P1 price, load-weighted reserve dual) on the 8760 clock.

    Identical load-weighting to ``_xiso1_diurnal_amplitude_audit.model_price``
    (the C3a basis), extended to carry the reserve column alongside.
    """
    df = pd.read_parquet(
        bundle / "hourly" / f"system_{year}.parquet",
        columns=["pass", "zone", "hour", "price", "demand", "reserve_price"],
    )
    d = df[df["pass"] == "P1"]
    h = d["hour"].to_numpy(int)
    w = np.maximum(d["demand"].to_numpy(float), 0.0)
    T = int(h.max()) + 1
    den = np.bincount(h, weights=w, minlength=T)
    out = []
    for col in ("price", "reserve_price"):
        num = np.bincount(h, weights=d[col].to_numpy(float) * w, minlength=T)
        simple = np.bincount(h, weights=d[col].to_numpy(float), minlength=T)
        cnt = np.maximum(np.bincount(h, minlength=T), 1)
        out.append(np.where(den > 0, num / np.maximum(den, 1e-9), simple / cnt)[:8760])
    return out[0], out[1]


def measured(year: int, kind: str) -> np.ndarray:
    df = pd.read_parquet(ACTUAL)
    d = df[df["year"].astype(int) == year].sort_values("hour")
    return pd.to_numeric(d[kind], errors="coerce").to_numpy(float)[:8760]


def _win(arr: np.ndarray, hours: tuple[int, ...]) -> float:
    """Mean of ``arr`` over the given hours-of-day across the year."""
    m = arr[: 365 * 24].reshape(365, 24)[:, list(hours)]
    return float(np.nanmean(m))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args(argv)

    if args.fetch:
        fetch(args.years)
        fetch_daas(args.years)

    rsv = load_reserve(args.years)
    kid, bundle = keeper_bundle()
    print(f"keeper: {kid}\nbundle: {bundle.relative_to(REPO)}")
    print(
        f"reserve rows: {len(rsv):,} ROS hours "
        f"({rsv.groupby('year').size().to_dict()})"
    )

    print("\n=== A — the model's reserve pricing vs NEISO's own posted prices ===")
    print(
        f"{'':<44}"
        + "".join(f"{y:>12}" for y in args.years)
    )
    rows: dict[str, list] = {}
    series = {}
    for y in args.years:
        p_model, r_model = model_price(bundle, y)
        g = rsv[rsv["year"] == y]
        r_meas = np.full(8760, np.nan)
        r_meas[g["hour"].to_numpy()] = g["tmsr"].to_numpy()
        r_tot = np.full(8760, np.nan)
        r_tot[g["hour"].to_numpy()] = g["total"].to_numpy()
        series[y] = {
            "p_model": p_model,
            "r_model": r_model,
            "r_meas": r_meas,
            "r_tot": r_tot,
            "da": measured(y, "da"),
            "rt": measured(y, "rt"),
        }
        pk = r_meas[: 365 * 24].reshape(365, 24)[:, list(PEAK_HOURS)]
        rows.setdefault("model reserve dual > 0 (hours of 8,760)", []).append(
            f"{int(np.nansum(r_model > 1e-9)):>12,}"
        )
        rows.setdefault("model dual, peak-window mean", []).append(
            f"${_win(r_model, PEAK_HOURS):>11.2f}"
        )
        rows.setdefault("measured RT TMSR, peak-window mean", []).append(
            f"${_win(r_meas, PEAK_HOURS):>11.2f}"
        )
        rows.setdefault("  — share of peak-window hours > $1", []).append(
            f"{np.nanmean(pk > 1.0) * 100:>11.1f}%"
        )
        rows.setdefault("  — $200-censored", []).append(
            f"${_win(np.minimum(r_meas, CENSOR), PEAK_HOURS):>11.2f}"
        )
        rows.setdefault("measured RT TMSR, trough-window mean", []).append(
            f"${_win(r_meas, TROUGH_HOURS):>11.2f}"
        )
        rows.setdefault("measured RT TMSR, all-hours mean", []).append(
            f"${np.nanmean(r_meas):>11.2f}"
        )
        rows.setdefault("measured RT TOTAL(30-min), all-hours mean", []).append(
            f"${np.nanmean(r_tot):>11.2f}"
        )
        rows.setdefault("measured RT TMSR, hours > $1 (of 8,760)", []).append(
            f"{int(np.nansum(r_meas > 1.0)):>12,}"
        )
    for k, v in rows.items():
        print(f"{k:<44}" + "".join(v))

    print("\n=== B — the swing arithmetic (nyiso-110 §2 construction) ===")
    print(
        "  reserve differential = measured peak-window minus trough-window TMSR;"
        "\n  missing swing = (actual peak-trough) minus (model peak-trough)."
        "\n  NOTE: the DA row divides by the DA missing swing but uses the"
        "\n  REAL-TIME differential — ISO-NE posts no DA reserve price before"
        "\n  DASI (§D/§F), so the DA row is an UPPER-BOUND proxy, not a measured"
        "\n  DA reserve content. §F measures the DA content where it exists."
    )
    print(
        f"{'basis':<6}{'':<26}" + "".join(f"{y:>10}" for y in args.years)
    )
    for basis in ("da", "rt"):
        diffs, misses, shares = [], [], []
        for y in args.years:
            s = series[y]
            r_diff = _win(s["r_meas"], PEAK_HOURS) - _win(s["r_meas"], TROUGH_HOURS)
            a_sw = _win(s[basis], PEAK_HOURS) - _win(s[basis], TROUGH_HOURS)
            m_sw = _win(s["p_model"], PEAK_HOURS) - _win(s["p_model"], TROUGH_HOURS)
            miss = a_sw - m_sw
            diffs.append(f"{r_diff:>10.2f}")
            misses.append(f"{miss:>10.2f}")
            shares.append(f"{r_diff / miss * 100:>9.1f}%" if miss else f"{'--':>10}")
        print(f"{basis.upper():<6}{'reserve differential':<26}" + "".join(diffs))
        print(f"{'':<6}{'missing swing':<26}" + "".join(misses))
        print(f"{'':<6}{'share owned by reserve':<26}" + "".join(shares))

    print("\n=== C — passthrough: hourly peak-window miss regressed on TMSR ===")
    for basis in ("da", "rt"):
        line = []
        for y in args.years:
            s = series[y]
            miss = (s[basis] - s["p_model"])[: 365 * 24].reshape(365, 24)[
                :, list(PEAK_HOURS)
            ].ravel()
            r = np.minimum(s["r_meas"], CENSOR)[: 365 * 24].reshape(365, 24)[
                :, list(PEAK_HOURS)
            ].ravel()
            ok = np.isfinite(miss) & np.isfinite(r)
            if ok.sum() < 100 or np.std(r[ok]) < 1e-9:
                line.append(f"{'n/a':>22}")
                continue
            slope, _ = np.polyfit(r[ok], miss[ok], 1)
            corr = float(np.corrcoef(r[ok], miss[ok])[0, 1])
            line.append(f"  slope {slope:+.2f} r {corr:+.2f}")
        print(f"  {basis.upper()} $200-censored: " + "".join(line))

    print("\n=== D — the DA-side structural check (DASI go-live 2025-03-01) ===")
    print(
        "  ISO-NE cleared NO day-ahead reserve product before DASI, so the DA\n"
        "  LMP carries no reserve content to strip in 2023, 2024 or Jan-Feb 2025."
    )
    for y in args.years:
        s = series[y]
        pre = np.ones(8760, bool)
        if y == DASI_GO_LIVE.year:
            cut = int(_hour_index(pd.DatetimeIndex([DASI_GO_LIVE]), np.array([1]))[0])
            pre[cut:] = False
        elif y > DASI_GO_LIVE.year:
            pre[:] = False
        share_pre = pre.mean() * 100
        print(
            f"    {y}: {share_pre:.0f}% of hours are pre-DASI "
            f"(no DA reserve product by market design)"
        )

    print("\n=== E — energy-basis restatement (nyiso-110 §2.1 construction) ===")
    print(
        "  Strip the measured RT reserve content from the RT actual and the\n"
        "  model's own folded dual from the model price, then compare\n"
        "  energy-only to energy-only. BOUNDING: the reserve price passes into\n"
        "  the LMP only where a reserve-capable unit is marginal, so this\n"
        "  strips AT MOST the true content."
    )
    print(
        f"{'year':>6}{'RT energy trough err':>22}{'RT energy peak err':>20}"
        f"{'RT energy swing share':>23}"
    )
    for y in args.years:
        s = series[y]
        a_e = s["rt"] - np.nan_to_num(s["r_meas"])
        m_e = s["p_model"] - s["r_model"]
        tr = _win(m_e, TROUGH_HOURS) - _win(a_e, TROUGH_HOURS)
        pk = _win(m_e, PEAK_HOURS) - _win(a_e, PEAK_HOURS)
        a_sw = _win(a_e, PEAK_HOURS) - _win(a_e, TROUGH_HOURS)
        m_sw = _win(m_e, PEAK_HOURS) - _win(m_e, TROUGH_HOURS)
        print(
            f"{y:>6}{tr:>+22.2f}{pk:>+20.2f}"
            f"{(m_sw / a_sw * 100 if a_sw else float('nan')):>22.1f}%"
        )

    # ---------------------------------------------------------------- §F
    daas = load_daas(args.years)
    print("\n=== F — the MEASURED day-ahead reserve content, where it exists ===")
    if daas.empty:
        print("  no DAAS rows on disk — run with --fetch")
        return 0
    cov = daas.groupby("year").agg(rows=("hour", "size"), first=("date", "min"))
    print(
        "  DAAS coverage (measured, not assumed): "
        + "; ".join(
            f"{int(y)}: {int(r.rows):,} ROS hours from {r.first:%Y-%m-%d}"
            for y, r in cov.iterrows()
        )
    )
    for y in sorted(daas["year"].unique()):
        y = int(y)
        s = series[y]
        g = daas[daas["year"] == y]
        da_r = np.full(8760, np.nan)
        da_r[g["hour"].to_numpy()] = g["tmsr"].to_numpy()
        live = np.isfinite(da_r)  # the post-go-live window, hour-exact
        mask = np.zeros((365, 24), bool)
        mask[: 365 * 24 // 24] = live[: 365 * 24].reshape(365, 24)

        def w(arr, hours, m=mask):
            a = np.where(m, arr[: 365 * 24].reshape(365, 24), np.nan)
            return float(np.nanmean(a[:, list(hours)]))

        pk_hours = np.where(mask, da_r[: 365 * 24].reshape(365, 24), np.nan)[
            :, list(PEAK_HOURS)
        ]
        r_diff = w(da_r, PEAK_HOURS) - w(da_r, TROUGH_HOURS)
        a_sw = w(s["da"], PEAK_HOURS) - w(s["da"], TROUGH_HOURS)
        m_sw = w(s["p_model"], PEAK_HOURS) - w(s["p_model"], TROUGH_HOURS)
        miss = a_sw - m_sw
        miss_h = (s["da"] - s["p_model"])[: 365 * 24].reshape(365, 24)[
            :, list(PEAK_HOURS)
        ].ravel()
        r_h = np.minimum(da_r, CENSOR)[: 365 * 24].reshape(365, 24)[
            :, list(PEAK_HOURS)
        ].ravel()
        ok = np.isfinite(miss_h) & np.isfinite(r_h)
        slope, _ = np.polyfit(r_h[ok], miss_h[ok], 1) if ok.sum() > 100 else (np.nan, 0)
        corr = float(np.corrcoef(r_h[ok], miss_h[ok])[0, 1]) if ok.sum() > 100 else np.nan
        # energy-basis restatement on the DA basis, post-go-live hours only
        a_e = s["da"] - np.nan_to_num(da_r)
        m_e = s["p_model"] - s["r_model"]
        e_a_sw = w(a_e, PEAK_HOURS) - w(a_e, TROUGH_HOURS)
        e_m_sw = w(m_e, PEAK_HOURS) - w(m_e, TROUGH_HOURS)
        print(f"  {y} (post-go-live hours only, n={int(live.sum()):,}):")
        print(
            f"    DA TMSR peak-window ${w(da_r, PEAK_HOURS):.2f} · trough-window "
            f"${w(da_r, TROUGH_HOURS):.2f} · all-hours ${np.nanmean(da_r):.2f} · "
            f"share of peak hours > $1 {np.nanmean(pk_hours > 1.0) * 100:.1f}%"
        )
        print(
            f"    reserve differential ${r_diff:.2f} vs DA missing swing "
            f"${miss:.2f} -> share owned by reserve "
            f"{r_diff / miss * 100:.1f}%" if miss else "    (no swing)"
        )
        print(f"    passthrough slope {slope:+.2f} (r {corr:+.2f})")
        print(
            f"    energy-basis: model DA energy swing is "
            f"{e_m_sw / e_a_sw * 100:.1f}% of the reserve-stripped actual's"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
