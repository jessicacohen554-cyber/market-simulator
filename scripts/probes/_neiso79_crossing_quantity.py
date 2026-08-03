"""neiso-79 — reconcile the CROSSING QUANTITY for the neiso-76 §D traversal. NO LP.

neiso-76 §D crossed ISO-NE's real submitted DA offer book at the real hourly
quantity (EIA-930 ISNE demand) and got an hour-of-day price range of
$17.03 / $21.11 / $24.06 -- 66 / 73 / 54 % of the measured DA range, peaking
HE20-21 -- against the keeper's own $7.03 / $6.82 / $13.30 (27.1 / 23.6 /
29.9 %). It reported against interest that the read is DEPTH-SENSITIVE: a flat
3 GW import allowance halves it to 36 / 34 / 31 %, only 4-7 pp above the
keeper. Direction survived; magnitude did not. The reconciliation it named but
did not do -- "cleared demand net of scheduled imports and cleared virtual
supply" -- is this probe.

THE CONSTRUCTION (prereg §2, frozen before any statistic was computed).
ISO-NE's day-ahead market clears one energy balance per hour:

    internal generator supply  Q_gen(λ)
  + cleared imports           Q_imp(λ)     [IMPORT rows, da-import-export]
  + cleared virtual supply    Q_inc(λ)     [INC bid type, da-demand-bids]
  = cleared physical demand + cleared virtual load + cleared exports

so the crossing quantity for the internal book, q*(λ) = Q_cleared_dem −
Q_imp(λ) − Q_inc(λ), is PRICE-DEPENDENT: not a quantity to look up but a fixed
point to solve. Equivalently and identically -- and this is what the probe
does -- cross the COMBINED supply book (internal offers + import offers + INC
virtuals) against the single vertical line Q_cleared_dem. **There is no free
depth parameter**, which is exactly what dissolves the neiso-76 sensitivity:
import depth clears endogenously off a measured priced book instead of being
assumed at 3 GW.

ISO-NE publishes NO day-ahead cleared external-transaction or net-interchange
series (verified against the full ISO Express Pricing / Grid / Load & Demand
trees and Web Services v1.1 -- see data/raw/NEISO-AS/da-import-export/README).
EIA-930 interchange is ACTUAL NET interchange, a different quantity at a
different grain, and is NOT substituted for it (rule 14 [R-ACCURATE]).

THE COMPOSITION OF THE PUBLISHED CLEARED SERIES IS IDENTIFIED, NOT ASSUMED
(the miso-105 discipline neiso-76 used for the ladder semantics): all four
admissible compositions C1-C4 are crossed, and the one reproducing the posted
DA hub LMP best -- pooled median |λ* − DA|, lowest in all three years -- is
reported as the identification. Selection is on a MEASURED PRICE, never on
C3b/C3c movement or any residual (rules 13 / 23 / prereg KQ5).

Ladder semantics of the import book, identified from the file: each row is an
independent (price, MW) block for one hour (645 of 1,280 (customer, origin,
destination, hour, direction, type) keys carry multiple rows), so MW are
incremental block widths -- the same convention the offer and demand books
use. ``FIXED`` transactions carry a blank price and are self-scheduled:
price-insensitive supply (IMPORT) or demand (EXPORT).

Kill rules KQ1-KQ5: results/calibration/PREREG-neiso79-crossing-quantity-2026-08-03.md

Rule 13: every price here is a validation target; nothing feeds a solve.
Rule 22: train years 2023-2025 only.

Usage:
    python scripts/probes/_neiso79_crossing_quantity.py
    python scripts/probes/_neiso79_crossing_quantity.py --max-days 60   # smoke
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import NEISO_AS_DIR  # noqa: E402

OFFER_DIR = NEISO_AS_DIR / "da-energy-offers"
BID_DIR = NEISO_AS_DIR / "da-demand-bids"
IMPEXP_DIR = NEISO_AS_DIR / "da-import-export"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet"
KEEPER_HOURLY = REPO / "results/calibration/neiso72_hy_window_B/hourly"

YEARS = (2023, 2024, 2025)

#: ISO-NE's offer floor / cap bracket -- the bisection domain and the price at
#: which self-scheduled (``FIXED``) blocks enter the ladder. -$150/MWh is the
#: measured minimum of the submitted DISPATCHABLE import price distribution and
#: the floor the neiso-76 demand-limb probe bisects from; $2,000/MWh is its
#: ceiling. No statistic depends on the exact bracket -- it only has to contain
#: every submitted price, which is asserted at parse time.
PRICE_FLOOR = -150.0
PRICE_CAP = 2000.0

#: A source file below this size is a stub / empty posting, not an operating
#: day (the documented publication-gap pattern of all three reports).
MIN_REAL_BYTES = 5_000

#: neiso-76 §D anchors and the keeper's own, as a share of the measured DA
#: hour-of-day range. Reported beside every corrected number (prereg §2.3).
ANCHOR_DA_HOD = {2023: 25.96, 2024: 28.96, 2025: 44.47}
ANCHOR_N76_DEMAND = {2023: 17.03, 2024: 21.11, 2025: 24.06}
ANCHOR_N76_DEMAND_3GW = {2023: 9.44, 2024: 9.73, 2025: 13.75}
ANCHOR_KEEPER = {2023: 7.03, 2024: 6.82, 2025: 13.30}

#: prereg §3: a year is reportable only with >= 300 operating days present in
#: ALL THREE books; below 200 it gets no headline share at all.
MIN_DAYS_FULL = 300
MIN_DAYS_ANY = 200

#: prereg KQ3: no composition reaching this pooled median |λ* − DA| in all
#: three years means the crossing is not identified against the market price.
KQ3_BAR = 10.00

#: prereg KQ2 / KQ4 bars.
KQ2_SHARE_BAR = 0.40
KQ4_PP_BAR = 5.0


# --------------------------------------------------------------------------
# parsers -- one operating day at a time; only per-hour ladders are held
# --------------------------------------------------------------------------
def _reprice_must_take(
    segs: list[tuple[float, float]], must_take: float
) -> list[tuple[float, float]]:
    """Re-price an asset's cheapest ``must_take`` MW to the offer floor.

    ``Must Take Energy`` is energy the asset will produce whatever the price
    clears at -- self-scheduled, inflexible output.  Measured on the corpus,
    EVERY unit-hour carrying it has ``Unit Status = MUST_RUN`` and its own
    segment ladder already spans ``Economic Maximum`` (seg_total/EcoMax p25
    1.00, median 1.057), so the must-take MW are a SUBSET of the ladder, not
    an addition to it: adding them as extra supply would double-count.  What
    is wrong in the naive read is the PRICE axis, not the quantity -- those MW
    clear at any price and so belong at the bottom of the stack.  This splits
    the asset's own cheapest blocks up to ``must_take`` and re-prices them to
    ``PRICE_FLOOR``, conserving total MW exactly.  No free parameter.
    """
    if must_take <= 0.0 or not segs:
        return segs
    out: list[tuple[float, float]] = []
    left = must_take
    for p, w in sorted(segs):
        if left <= 0.0:
            out.append((p, w))
        elif w <= left:
            out.append((PRICE_FLOOR, w))
            left -= w
        else:
            out.append((PRICE_FLOOR, left))
            out.append((p, w - left))
            left = 0.0
    return out


def parse_offers(
    path: Path,
) -> tuple[dict[int, list], dict[int, list]]:
    """(hour-ending) -> internal generator supply ladders [(price, dMW), ...].

    Returns two ladders for the same day: the FROZEN construction (the
    neiso-76 selection verbatim -- ``Economic Maximum`` > 0, asset status in
    {ECONOMIC, MUST_RUN}, the ten (price, MW) segment pairs as incremental
    block widths) and the MT variant, identical except that each asset's
    ``Must Take Energy`` MW are re-priced to the floor (see
    ``_reprice_must_take``).  Both are reported; the MT variant is disclosed
    as a post-hoc refinement (prereg KQ5).
    """
    base: dict[int, list[tuple[float, float]]] = {}
    mt: dict[int, list[tuple[float, float]]] = {}
    with path.open(newline="") as fh:
        for r in csv.reader(fh):
            if not r or r[0] != "D" or len(r) < 36:
                continue
            try:
                eco_max = float(r[7] or 0.0)
            except ValueError:
                continue
            if eco_max <= 0.0 or r[35].strip() not in ("ECONOMIC", "MUST_RUN"):
                continue
            he_raw = r[2].strip().upper()
            # The DST fall-back repeat hour ("02X") is dropped here exactly as
            # the demand-bid and import/export parsers drop it, and as the
            # committed label-keyed 8760 actual has no row for it. Merging it
            # into HE02 (the neiso-76 rstrip) would double-count supply on one
            # day a year against demand that had already dropped it.
            if he_raw.endswith("X"):
                continue
            try:
                he = int(he_raw)
            except ValueError:
                continue
            segs: list[tuple[float, float]] = []
            for k in range(13, 33, 2):
                pv = r[k] if k < len(r) else ""
                mv = r[k + 1] if k + 1 < len(r) else ""
                if pv in ("", None) or mv in ("", None):
                    continue
                try:
                    p, w = float(pv), float(mv)
                except ValueError:
                    continue
                if w > 0.0:
                    segs.append((p, w))
            if not segs:
                continue
            try:
                must_take = float(r[5] or 0.0)
            except ValueError:
                must_take = 0.0
            base.setdefault(he, []).extend(segs)
            mt.setdefault(he, []).extend(_reprice_must_take(segs, must_take))
    return base, mt


def parse_impexp(path: Path) -> dict[int, dict]:
    """(hour-ending) -> the day's submitted external book.

    Per hour: ``imp_fixed`` MW (self-scheduled imports -- price-insensitive
    supply), ``imp`` [(price, MW)] (DISPATCHABLE imports -- priced supply),
    ``exp_fixed`` MW (self-scheduled exports -- price-insensitive demand) and
    ``exp`` [(price, MW)] (DISPATCHABLE exports -- priced demand, clearing when
    the price is at or above the LMP).
    """
    day: dict[int, dict] = {}
    with path.open(newline="") as fh:
        for r in csv.reader(fh):
            if not r or r[0] != "D" or len(r) < 12:
                continue
            he_raw = r[2].strip().upper()
            if he_raw.endswith("X"):
                continue
            try:
                he = int(he_raw)
                w = float(r[11])
            except ValueError:
                continue
            if w <= 0.0:
                continue
            rec = day.setdefault(
                he, {"imp_fixed": 0.0, "imp": [], "exp_fixed": 0.0, "exp": []}
            )
            is_import = r[8].strip() == "IMPORT"
            pv = r[10].strip()
            if not pv:  # FIXED / self-scheduled: no price axis
                rec["imp_fixed" if is_import else "exp_fixed"] += w
                continue
            try:
                p = float(pv)
            except ValueError:
                continue
            rec["imp" if is_import else "exp"].append((p, w))
    return day


def parse_bids(path: Path) -> dict[int, dict]:
    """(hour-ending) -> the day's submitted demand-side book.

    The neiso-76 demand-limb parser verbatim: ``fixed`` MW (unpriced physical),
    and (price, MW) ladders for price-sensitive physical demand (``PRICE``),
    virtual load (``DEC``) and virtual supply (``INC``).
    """
    day: dict[int, dict] = {}
    with path.open(newline="") as fh:
        for r in csv.reader(fh):
            if not r or r[0] != "D" or len(r) < 10:
                continue
            he_raw = r[2].strip().upper()
            if he_raw.endswith("X"):
                continue
            try:
                he = int(he_raw)
            except ValueError:
                continue
            bt = r[6].strip()
            rec = day.setdefault(he, {"fixed": 0.0, "PRICE": [], "DEC": [], "INC": []})
            for k in range(8, len(r) - 1, 2):
                pv, mv = r[k], r[k + 1]
                if mv in ("", None):
                    continue
                try:
                    w = float(mv)
                except ValueError:
                    continue
                if pv in ("", None):
                    rec["fixed"] += w
                    continue
                try:
                    p = float(pv)
                except ValueError:
                    continue
                if bt in rec:
                    rec[bt].append((p, w))
    return day


def load_cleared() -> dict:
    """(date, hour-ending) -> published DA cleared demand MWh."""
    out = {}
    for p in sorted(BID_DIR.glob("cleared_*.csv")):
        with p.open(newline="") as fh:
            for r in csv.reader(fh):
                if not r or r[0] != "D" or len(r) < 4:
                    continue
                he = r[2].strip().upper()
                if he.endswith("X"):
                    continue
                try:
                    out[(pd.Timestamp(r[1]), int(he))] = float(r[3])
                except ValueError:
                    continue
    return out


# --------------------------------------------------------------------------
# the crossing
# --------------------------------------------------------------------------
#: The four admissible compositions of the published cleared-demand series
#: (prereg §2.2). Each maps to (include INC virtual supply, include priced +
#: fixed exports on the demand line, subtract self-scheduled imports from the
#: demand line instead of adding them to supply).
COMPOSITIONS = {
    "C1": dict(inc=True, exports=False, imp_fixed_as_demand=False),
    "C2": dict(inc=True, exports=True, imp_fixed_as_demand=False),
    "C3": dict(inc=False, exports=False, imp_fixed_as_demand=False),
    "C4": dict(inc=True, exports=False, imp_fixed_as_demand=True),
}


def supply_at(
    lam: float,
    gen: list,
    ext: dict,
    bid: dict,
    *,
    inc: bool,
    imports: bool,
    imp_fixed_as_demand: bool,
) -> float:
    """Total submitted supply MW clearing at price ``lam`` (blocks with p <= lam)."""
    q = sum(w for p, w in gen if p <= lam)
    if imports:
        if not imp_fixed_as_demand:
            q += ext["imp_fixed"]
        q += sum(w for p, w in ext["imp"] if p <= lam)
    if inc and bid is not None:
        q += sum(w for p, w in bid["INC"] if p <= lam)
    return q


def demand_at(
    lam: float,
    q_cleared: float,
    ext: dict,
    *,
    exports: bool,
    imports: bool,
    imp_fixed_as_demand: bool,
) -> float:
    """The demand-side vertical line at price ``lam``.

    The published cleared-demand series is the base; a composition may add
    cleared exports (self-scheduled plus priced bids at or above ``lam``) or
    net self-scheduled imports out of it.
    """
    q = q_cleared
    if exports:
        q += ext["exp_fixed"] + sum(w for p, w in ext["exp"] if p >= lam)
    if imports and imp_fixed_as_demand:
        q -= ext["imp_fixed"]
    return q


def cross(
    gen: list,
    ext: dict,
    bid: dict,
    q_cleared: float,
    *,
    inc: bool,
    exports: bool,
    imports: bool,
    imp_fixed_as_demand: bool,
) -> float:
    """Bisect for the price at which submitted supply meets the demand line.

    Supply is non-decreasing in price and the demand line non-increasing, so
    ``supply - demand`` is non-decreasing and a plain bisection on
    [PRICE_FLOOR, PRICE_CAP] locates the crossing. Returns NaN when the books
    never cross inside the bracket (an hour the submitted book cannot clear at
    the published quantity) -- reported, never imputed.
    """
    kw_s = dict(inc=inc, imports=imports, imp_fixed_as_demand=imp_fixed_as_demand)
    kw_d = dict(exports=exports, imports=imports, imp_fixed_as_demand=imp_fixed_as_demand)

    def gap(lam: float) -> float:
        return supply_at(lam, gen, ext, bid, **kw_s) - demand_at(
            lam, q_cleared, ext, **kw_d
        )

    if gap(PRICE_CAP) < 0.0 or gap(PRICE_FLOOR) > 0.0:
        return np.nan
    lo, hi = PRICE_FLOOR, PRICE_CAP
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if gap(mid) >= 0.0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------
# corpus assembly
# --------------------------------------------------------------------------
def _real(path: Path) -> bool:
    return path.exists() and path.stat().st_size > MIN_REAL_BYTES


def common_days(years=YEARS) -> list[str]:
    """Operating days published in ALL THREE books (the binding intersection)."""
    days = []
    for y in years:
        for d in pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D"):
            tag = f"{d:%Y%m%d}"
            if (
                _real(OFFER_DIR / f"hbdayaheadenergyoffer_{tag}.csv")
                and _real(BID_DIR / f"hbdayaheaddemandbid_{tag}.csv")
                and _real(IMPEXP_DIR / f"hbdayaheadimpexp_{tag}.csv")
            ):
                days.append(tag)
    return days


#: Cumulative hour offset of each month's start in the committed label-keyed
#: 8760 actual (Feb-29 dropped) -- the neiso-76 ``_hour_index`` construction.
_MONTH_START_HOUR = np.cumsum(
    [0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)]
)


def _hour_index(date: pd.Timestamp, he: int) -> int:
    """(operating day, hour-ending) -> row index in the label-keyed 8760."""
    if date.month == 2 and date.day == 29:
        return -1
    base = int(_MONTH_START_HOUR[date.month - 1])
    return base + (date.day - 1) * 24 + (he - 1)


def demand_lookup(years=YEARS) -> dict:
    """(operating day, hour-ending) -> measured ISNE demand MW (EIA-930).

    The neiso-76 §D crossing quantity, carried here ONLY as a control: it lets
    the same probe reproduce that traversal on THIS sample, so the corrected
    number can be compared like-for-like and the effect of changing the
    QUANTITY is separated from the effect of changing the SAMPLE.
    """
    from market_sim.data.eia_loader import _eia_hourly_frame

    out = {}
    for year in years:
        df = _eia_hourly_frame("ISNE", year)
        if df is None:
            raise SystemExit(f"EIA-930 ISNE {year}: no clean 8760 frame")
        local = pd.DatetimeIndex(df["Local time"])
        for day, he, mw in zip(
            local.normalize(), local.hour + 1, df["Demand"].to_numpy(float)
        ):
            out[(day, int(he))] = float(mw)
    return out


def da_lookup() -> dict:
    """(year, 8760 hour index) -> posted DA hub LMP (the committed actual)."""
    act = pd.read_parquet(ACTUAL)
    return {
        (int(y), int(h)): float(v)
        for y, h, v in zip(act["year"], act["hour"], act["da"])
    }


def run(days: list[str]) -> pd.DataFrame:
    """Cross every composition on every hour of ``days``; one row per hour."""
    da = da_lookup()
    cleared = load_cleared()
    eia = demand_lookup()
    rows = []
    for i, tag in enumerate(days, 1):
        day = pd.Timestamp(tag)
        gen_d, gen_mt_d = parse_offers(OFFER_DIR / f"hbdayaheadenergyoffer_{tag}.csv")
        ext_d = parse_impexp(IMPEXP_DIR / f"hbdayaheadimpexp_{tag}.csv")
        bid_d = parse_bids(BID_DIR / f"hbdayaheaddemandbid_{tag}.csv")
        for he in range(1, 25):
            gen = gen_d.get(he)
            ext = ext_d.get(he)
            bid = bid_d.get(he)
            q_cl = cleared.get((day, he))
            if not gen or ext is None or bid is None or q_cl is None:
                continue
            hidx = _hour_index(day, he)
            rec = {
                "day": day,
                "he": he,
                "year": day.year,
                "q_cleared": q_cl,
                "da": da.get((day.year, hidx), np.nan) if hidx >= 0 else np.nan,
                "imp_fixed": ext["imp_fixed"],
                "imp_priced": sum(w for _, w in ext["imp"]),
                "exp_fixed": ext["exp_fixed"],
                "exp_priced": sum(w for _, w in ext["exp"]),
                "inc_mw": sum(w for _, w in bid["INC"]),
                "gen_mw": sum(w for _, w in gen),
            }
            gen_mt = gen_mt_d.get(he, gen)
            for name, cfg in COMPOSITIONS.items():
                rec[name] = cross(gen, ext, bid, q_cl, imports=True, **cfg)
                # the disclosed post-hoc MT variant (prereg KQ5), same crossing
                rec[f"{name}mt"] = cross(gen_mt, ext, bid, q_cl, imports=True, **cfg)
            # KQ4: the same crossing with the import book removed entirely.
            for tag_v, g_v in (("", gen), ("mt", gen_mt)):
                rec[f"C1{tag_v}_noimp"] = cross(
                    g_v, ext, bid, q_cl, imports=False, **COMPOSITIONS["C1"]
                )
            # CONTROL: the neiso-76 §D traversal itself, on THIS sample --
            # the internal book alone crossed at EIA-930 demand and at
            # demand - 3 GW.  Separates the quantity change from the sample
            # change; it is not a composition and is never selected.
            d_mw = eia.get((day, he))
            for tag_v, off in (("n76", 0.0), ("n76_3gw", 3000.0)):
                rec[tag_v] = (
                    cross(
                        gen,
                        ext,
                        bid,
                        float(d_mw) - off,
                        imports=False,
                        inc=False,
                        exports=False,
                        imp_fixed_as_demand=False,
                    )
                    if d_mw is not None and np.isfinite(d_mw)
                    else np.nan
                )
            rows.append(rec)
        if i % 100 == 0:
            print(f"  ... {i}/{len(days)} days", flush=True)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def hod_stats(df: pd.DataFrame, col: str) -> dict[int, dict]:
    """Per year: hour-of-day mean profile range, and the hour of its max."""
    out = {}
    for y, g in df.groupby("year"):
        prof = g.groupby("he")[col].mean().dropna()
        if prof.empty:
            continue
        out[int(y)] = {
            "range": float(prof.max() - prof.min()),
            "peak_he": int(prof.idxmax()),
            "trough_he": int(prof.idxmin()),
            "n": int(g[col].notna().sum()),
        }
    return out


def fit_stats(df: pd.DataFrame, col: str) -> dict[int, dict]:
    """Per year: median/mean |λ* − DA| and the share of hours within $2."""
    out = {}
    for y, g in df.groupby("year"):
        e = (g[col] - g["da"]).abs().dropna()
        if e.empty:
            continue
        out[int(y)] = {
            "median": float(e.median()),
            "mean": float(e.mean()),
            "within2": float((e <= 2.0).mean()),
            "n": int(e.size),
        }
    return out


def share(rng: float, year: int) -> float:
    return rng / ANCHOR_DA_HOD[year]




def scored_years(df: pd.DataFrame) -> list[int]:
    """Years carrying enough operating days to be scored at all (prereg §3).

    A year below ``MIN_DAYS_ANY`` days in the three-book intersection "is not
    given a headline share at all", so it must not drive the identification or
    the kill rules either -- it is reported separately as under-floor.
    """
    days = df.groupby("year")["day"].nunique()
    return [y for y in YEARS if int(days.get(y, 0)) >= MIN_DAYS_ANY]


def _identify(df: pd.DataFrame, suffix: str) -> tuple[str, bool, dict]:
    """Pick the composition reproducing the posted DA best (prereg §2.2).

    Returns ``(best, identified, fits)``; ``identified`` is True only when the
    same composition wins in every scored year.
    """
    fits = {c: fit_stats(df, c + suffix) for c in COMPOSITIONS}
    years = scored_years(df)
    best = min(
        COMPOSITIONS,
        key=lambda c: np.mean([fits[c][y]["median"] for y in years if y in fits[c]]),
    )
    winners = {
        y: min(COMPOSITIONS, key=lambda c: fits[c][y]["median"])
        for y in years
        if all(y in fits[c] for c in COMPOSITIONS)
    }
    return best, len(set(winners.values())) == 1, fits


def _fit_table(fits: dict, label: str) -> None:
    """Print the per-year identification table for one construction family."""
    print(f"\n  --- {label} ---")
    print("  " + f"{'comp':<5} " + "".join(f"{y} median  within$2   " for y in YEARS))
    for c in COMPOSITIONS:
        line = f"  {c:<5} "
        for y in YEARS:
            f = fits[c].get(y)
            line += (
                f"{f['median']:11.2f} {f['within2']:8.1%}   "
                if f
                else f"{'--':>11} {'--':>8}   "
            )
        print(line)


def _hod_table(df: pd.DataFrame, col: str, label: str) -> dict[int, dict]:
    """Print the corrected hour-of-day range beside all three anchors."""
    st = hod_stats(df, col)
    print(f"\n  --- {label} ---")
    print(
        f"    {'year':<6}{'hod range':>11}{'peak':>7}{'share':>9}"
        f"{'  n76 dem':>10}{'  n76-3GW':>10}{'  keeper':>9}{'  n hrs':>8}"
    )
    for y in sorted(st):
        s = st[y]
        print(
            f"    {y:<6}{s['range']:11.2f}{('HE%d' % s['peak_he']):>7}"
            f"{share(s['range'], y):9.1%}"
            f"{share(ANCHOR_N76_DEMAND[y], y):10.1%}"
            f"{share(ANCHOR_N76_DEMAND_3GW[y], y):10.1%}"
            f"{share(ANCHOR_KEEPER[y], y):9.1%}{s['n']:8d}"
        )
    return st


def _kill_rules(df: pd.DataFrame, col: str, noimp_col: str, label: str) -> None:
    """Score the pre-registered kill rules on one construction.

    Only years clearing the prereg §3 day floor are scored; an under-floor
    year cannot decide a kill rule it is not reportable for.
    """
    keep_years = scored_years(df)
    print(f"\n  --- KILL RULES on {label} (years scored: {keep_years}) ---")
    if len(keep_years) < len(YEARS):
        print(
            f"    NOTE: {len(keep_years)}/{len(YEARS)} years reportable, so the"
            ' ">= 2 of 3 years" kill rules are UNDECIDED, not passed.'
        )
    df = df[df["year"].isin(keep_years)]
    st = hod_stats(df, col)
    shares = {y: share(st[y]["range"], y) for y in st}
    keep = {y: share(ANCHOR_KEEPER[y], y) for y in st}
    n_le = sum(1 for y in st if shares[y] <= keep[y])
    print(
        f"    KQ1 (lane kill; <= keeper in >=2 yrs): {n_le}/{len(st)} -> "
        + ("FIRES -- TRAVERSAL LANE REFUTED" if n_le >= 2 else "does NOT fire")
    )
    n_lo = sum(1 for y in st if shares[y] < KQ2_SHARE_BAR)
    print(
        f"    KQ2 (direction-only; <{KQ2_SHARE_BAR:.0%} in >=2 yrs): {n_lo}/{len(st)} -> "
        + (
            "FIRES -- report as DIRECTION-ONLY"
            if n_lo >= 2
            else "does NOT fire -- MAGNITUDE SURVIVES"
        )
    )
    st_ni = hod_stats(df, noimp_col)
    worst = 0.0
    for y in sorted(st):
        if y not in st_ni:
            continue
        pp = abs(shares[y] - share(st_ni[y]["range"], y)) * 100.0
        worst = max(worst, pp)
        print(
            f"    KQ4 {y}: imports {st[y]['range']:6.2f} ({shares[y]:5.1%})"
            f"  vs none {st_ni[y]['range']:6.2f} "
            f"({share(st_ni[y]['range'], y):5.1%})  delta {pp:5.1f} pp"
        )
    print(
        f"    KQ4 (<{KQ4_PP_BAR:.0f} pp = immaterial): worst {worst:.1f} pp -> "
        + (
            "FIRES -- import reconciliation IMMATERIAL"
            if worst < KQ4_PP_BAR
            else "does NOT fire -- the import book does real work"
        )
    )


def main(argv: list[str] | None = None) -> int:
    """Run the reconciliation and print the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-days", type=int, default=None, help="smoke-test cap")
    args = ap.parse_args(argv)

    days = common_days()
    by_year = pd.Series([int(d[:4]) for d in days]).value_counts().sort_index()
    print("=== corpus: operating days present in ALL THREE books (prereg §3) ===")
    for y in YEARS:
        n = int(by_year.get(y, 0))
        flag = (
            "OK"
            if n >= MIN_DAYS_FULL
            else ("UNDER-SAMPLED" if n >= MIN_DAYS_ANY else "NO HEADLINE (prereg §3)")
        )
        print(f"  {y}: {n:4d} days   {flag}")
    if args.max_days:
        days = days[:: max(1, len(days) // args.max_days)][: args.max_days]
        print(f"  (SMOKE TEST: {len(days)} days -- not a reportable result)")

    print(f"\ncrossing {len(days)} operating days ...", flush=True)
    df = run(days)
    print(f"  {len(df):,} hours crossed")

    print("\n=== §2.2 IDENTIFICATION: which composition reproduces the posted DA? ===")
    print(
        "  selection statistic: pooled median |lambda* - DA| per year;"
        f" prereg KQ3 bar ${KQ3_BAR:.2f}"
    )
    best, ident, fits = _identify(df, "")
    _fit_table(fits, "FROZEN construction (prereg §2.1, neiso-76 offer selection)")
    best_mt, ident_mt, fits_mt = _identify(df, "mt")
    _fit_table(
        fits_mt,
        "MT variant -- DISCLOSED POST-HOC (prereg KQ5): each asset's"
        " Must Take Energy MW re-priced to the floor",
    )

    years = scored_years(df)
    for lbl, b, i_, f in (
        ("FROZEN", best, ident, fits),
        ("MT", best_mt, ident_mt, fits_mt),
    ):
        under = all(f[b].get(y, {}).get("median", 1e9) < KQ3_BAR for y in years)
        print(
            f"\n  {lbl}: best {b};  "
            + ("IDENTIFIED" if i_ else "UNIDENTIFIED (same winner not in all years)")
            + f";  KQ3 (<${KQ3_BAR:.2f} all years): "
            + ("passes" if under else "FIRES -- crossing not identified vs the market")
        )

    print("\n=== §2.3 THE CORRECTED CROSSING: hour-of-day range ===")
    _hod_table(df, best, f"FROZEN, composition {best}")
    _hod_table(df, best_mt + "mt", f"MT variant, composition {best_mt}")

    print(
        "\n=== CONTROL: the neiso-76 §D traversal itself, recomputed on THIS"
        " sample ==="
    )
    print(
        "  (internal book alone crossed at EIA-930 demand -- separates the"
        " QUANTITY change from the SAMPLE change)"
    )
    _hod_table(df, "n76", "neiso-76 §D read: at EIA-930 demand")
    _hod_table(df, "n76_3gw", "neiso-76 §D read: at demand - 3 GW")

    print("\n=== KILL RULES (prereg §4) ===")
    _kill_rules(df, best, "C1_noimp", f"FROZEN / {best}")
    _kill_rules(df, best_mt + "mt", "C1mt_noimp", f"MT / {best_mt}")

    print("\n=== depth diagnostics (report-only) ===")
    for y, g in df.groupby("year"):
        print(
            f"  {y}: cleared dem {g['q_cleared'].mean():8.0f} MW | imports submitted"
            f" fixed {g['imp_fixed'].mean():6.0f} + priced {g['imp_priced'].mean():6.0f}"
            f" | exports {g['exp_fixed'].mean():6.0f} + {g['exp_priced'].mean():6.0f}"
            f" | INC {g['inc_mw'].mean():6.0f} | gen offered {g['gen_mw'].mean():7.0f}"
        )
    print("\n=== signed bias of the crossing vs the posted DA (report-only) ===")
    for lbl, c in (("FROZEN", best), ("MT", best_mt + "mt")):
        for y, g in df.groupby("year"):
            d = (g[c] - g["da"]).dropna()
            print(
                f"  {lbl:<6} {y}: mean {d.mean():+8.2f}  median {d.median():+8.2f}"
                f"  |  no crossing in bracket {g[c].isna().mean():.2%}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
