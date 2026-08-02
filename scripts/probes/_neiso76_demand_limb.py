"""neiso-76 — the charter's K3 DEMAND-LIMB gate, measured. NO LP.

Charter §4 K3 has two halves and the demand limb runs only behind both:

  (i)  EXISTENCE (the nyiso-94 blocker): ISO-NE must publish a SUBMITTED
       priced DA demand/virtual book — price axis + MW, hourly, 2023-25.
       Cleared-only MW kills it.
  (ii) THE miso-105 λ0-ATTRACTOR TEST: if the book's crossing price
       reproduces the DA clearing price to <= $2 AND its stiffness against
       the model stack's elasticity implies >= 30 % of hourly price
       displacement supplied by the bid curve, the limb dies (rules 1/13 —
       the model's price would become the measured book's price).

Half (i) is answered by ``_neiso76_dabid_phase0.py --check-demand-book``.
This probe answers half (ii) on ISO-NE's own three published reports:

* **submitted book** — Day-Ahead Energy Market Demand Historical Demand Bid
  Report, ``transform/csv/hbdayaheaddemandbid?start=YYYYMMDD`` (one operating
  day; masked participant/location; Bid Type FIXED / PRICE / INC / DEC with up
  to 50 (price, MW) segments).
* **cleared quantity** — Day-Ahead Energy Market Hourly Demand Report,
  ``transform/csv/hourlydayaheaddemand?start=&end=`` (published hourly DA
  cleared demand MWh).
* **cleared price** — the committed hub actual ``da`` column.

λ0 is the price at which the submitted book's own quantity equals the
published cleared quantity — i.e. the price the book itself says the market
cleared at. The test compares λ0 to the price the market actually posted.

LADDER SEMANTICS ARE IDENTIFIED, NOT ASSUMED (the miso-105 discipline). The
report does not say whether ``Segment n MW`` is an INCREMENTAL block or a
CUMULATIVE quantity, and it publishes no cleared-MW column to settle it the
way MISO's file did, so all four readings (incremental/cumulative ×
INC-virtual-supply netted or not) are evaluated and the one that reproduces
the published cleared quantity/price is reported as the identification. If
none does, that is a REAL result: the semantics are unidentifiable from the
public file and K3(ii) cannot fire on it.

Sample: the 15th of every month 2023-2025 plus the five 2025 C3c event days
(41 operating days). Phase-0 is a measurement, not a derive — a full-corpus
pull is a Phase-1 cost and is not spent here.

Rule 13: measured prices are the validation target; nothing here feeds a solve.

Usage:
    python scripts/probes/_neiso76_demand_limb.py --fetch
    python scripts/probes/_neiso76_demand_limb.py
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

BID_DIR = NEISO_AS_DIR / "da-demand-bids"
OFFER_DIR = NEISO_AS_DIR / "da-energy-offers"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet"

BID_ENDPOINT = "https://www.iso-ne.com/transform/csv/hbdayaheaddemandbid"
CLEARED_ENDPOINT = "https://www.iso-ne.com/transform/csv/hourlydayaheaddemand"
REPORT_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/pricing/-/tree/"
    "day-ahead-energy-offer-data"
)

_MONTH_START_HOUR = np.cumsum(
    [0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)]
)

EVENT_DAYS = ("20250623", "20250624", "20250625", "20250728", "20250729")

#: The charter's stiffness band: dMW/d$ measured over +/- this many $/MWh
#: around λ0 (a local slope, not a global fit).
STIFF_BAND = 5.0


def sample_days(years=(2023, 2024, 2025)) -> list[str]:
    days = [f"{y}{m:02d}15" for y in years for m in range(1, 13)]
    return sorted(set(days) | set(EVENT_DAYS))


def _hour_index(date: pd.Timestamp, he: int) -> int:
    base = int(_MONTH_START_HOUR[date.month - 1])
    if date.month == 2 and date.day == 29:
        return -1
    return base + (date.day - 1) * 24 + (he - 1)


def _opener():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "neiso_fetch", REPO / "scripts" / "data" / "fetch_neiso_da_energy_offers.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._opener()


def fetch(days: list[str]) -> None:
    import time
    import urllib.request

    BID_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    for day in days:
        dest = BID_DIR / f"hbdayaheaddemandbid_{day}.csv"
        if dest.exists() and dest.stat().st_size > 5000:
            continue
        url = f"{BID_ENDPOINT}?start={day}"
        req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
        try:
            with opener.open(req, timeout=180) as resp:
                dest.write_bytes(resp.read())
            print(f"  bids {day}: {dest.stat().st_size:,} bytes", flush=True)
            time.sleep(0.4)
        except Exception as e:
            print(f"  ERROR bids {day}: {e}", flush=True)
            opener = _opener()
    # cleared demand: one file per month covering the sampled days
    months = sorted({d[:6] for d in days})
    for ym in months:
        start = pd.Timestamp(f"{ym}01")
        end = start + pd.offsets.MonthEnd(0)
        dest = BID_DIR / f"cleared_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        if dest.exists() and dest.stat().st_size > 1000:
            continue
        url = f"{CLEARED_ENDPOINT}?start={start:%Y%m%d}&end={end:%Y%m%d}"
        req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
        with opener.open(req, timeout=180) as resp:
            dest.write_bytes(resp.read())
        print(f"  cleared {ym}: {dest.stat().st_size:,} bytes", flush=True)
        time.sleep(0.4)


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


def parse_bids(path: Path) -> dict:
    """(hour-ending) -> dict of the day's submitted demand-side ladders.

    Returns per hour: ``fixed`` MW (unpriced), and (price, MW) segment lists
    for the price-sensitive physical (``PRICE``), virtual load (``DEC``) and
    virtual supply (``INC``) books.
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
            rec = day.setdefault(
                he, {"fixed": 0.0, "PRICE": [], "DEC": [], "INC": []}
            )
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


def demand_at(rec: dict, lam: float, cumulative: bool, net_inc: bool) -> float:
    """The submitted book's quantity at price ``lam``."""
    q = rec["fixed"]
    for key in ("PRICE", "DEC"):
        segs = rec[key]
        if not segs:
            continue
        if cumulative:
            take = [w for p, w in segs if p >= lam]
            q += max(take) if take else 0.0
        else:
            q += sum(w for p, w in segs if p >= lam)
    if net_inc and rec["INC"]:
        if cumulative:
            take = [w for p, w in rec["INC"] if p <= lam]
            q -= max(take) if take else 0.0
        else:
            q -= sum(w for p, w in rec["INC"] if p <= lam)
    return q


def lam0(rec: dict, target: float, cumulative: bool, net_inc: bool) -> float:
    """Price at which the book's quantity equals ``target`` (bisection).

    The book's quantity is non-increasing in price, so a plain bisection on
    [-150, 2000] $/MWh (the ISO-NE offer floor/cap bracket) locates it.
    """
    lo, hi = -150.0, 2000.0
    if demand_at(rec, hi, cumulative, net_inc) > target:
        return np.nan  # book never falls to the cleared quantity
    if demand_at(rec, lo, cumulative, net_inc) < target:
        return np.nan  # book never reaches it
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if demand_at(rec, mid, cumulative, net_inc) >= target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def parse_offers_stack(path: Path) -> dict:
    """(hour-ending) -> sorted (price, dMW) supply ladder from the offer book."""
    out: dict[int, list] = {}
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
            try:
                he = int(he_raw.rstrip("X"))
            except ValueError:
                continue
            for k in range(13, 33, 2):
                pv = r[k] if k < len(r) else ""
                mv = r[k + 1] if k + 1 < len(r) else ""
                if pv in ("", None) or mv in ("", None):
                    continue
                try:
                    p, w = float(pv), float(mv)
                except ValueError:
                    continue
                if w > 0:
                    out.setdefault(he, []).append((p, w))
    return out


def supply_stiffness(stack: list, lam: float, band: float = STIFF_BAND) -> float:
    """MW of supply between lam-band and lam+band, per $ — the local slope."""
    if not stack:
        return np.nan
    mw = sum(w for p, w in stack if lam - band <= p <= lam + band)
    return mw / (2.0 * band)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args(argv)

    days = sample_days()
    if args.fetch:
        fetch(days)

    cleared = load_cleared()
    act = pd.read_parquet(ACTUAL)
    da = {
        (int(y), int(h)): float(v)
        for y, h, v in zip(act["year"], act["hour"], act["da"])
    }

    files = [p for d in days if (p := BID_DIR / f"hbdayaheaddemandbid_{d}.csv").exists()]
    files = [p for p in files if p.stat().st_size > 5000]
    print(f"sample: {len(files)} of {len(days)} operating days present")

    variants = [
        ("incremental, INC netted", False, True),
        ("incremental, INC ignored", False, False),
        ("cumulative,  INC netted", True, True),
        ("cumulative,  INC ignored", True, False),
    ]
    rows = {name: [] for name, _, _ in variants}
    stiff_rows = []
    virt_rows = []
    for p in files:
        date = pd.Timestamp(p.stem.split("_")[1])
        book = parse_bids(p)
        off_path = OFFER_DIR / f"hbdayaheadenergyoffer_{date:%Y%m%d}.csv"
        stacks = parse_offers_stack(off_path) if off_path.exists() else {}
        for he, rec in sorted(book.items()):
            q = cleared.get((date, he))
            hidx = _hour_index(date, he)
            price = da.get((date.year, hidx))
            if q is None or price is None or hidx < 0:
                continue
            for name, cum, net in variants:
                lam = lam0(rec, q, cum, net)
                if np.isfinite(lam):
                    rows[name].append((lam, price))
            # net virtual position AT THE POSTED PRICE (the PJM premise test):
            # DEC (virtual load) that would clear minus INC (virtual supply)
            # that would clear, incremental reading.
            dec = sum(w for p, w in rec["DEC"] if p >= price)
            inc = sum(w for p, w in rec["INC"] if p <= price)
            virt_rows.append((date.year, he - 1, dec - inc, dec, inc))
            lam_best = lam0(rec, q, False, True)
            if np.isfinite(lam_best) and stacks.get(he):
                d_lo = demand_at(rec, price + STIFF_BAND, False, True)
                d_hi = demand_at(rec, price - STIFF_BAND, False, True)
                stiff_rows.append(
                    (
                        (d_hi - d_lo) / (2.0 * STIFF_BAND),
                        supply_stiffness(stacks[he], price),
                        rec["fixed"],
                        q,
                        price,
                    )
                )

    print("\n=== K3(ii)a — does the book's own crossing price λ0 reproduce the")
    print("    posted DA clearing price? (charter bar: <= $2 to KILL the limb) ===")
    print(f"{'ladder reading':<28}{'n hours':>9}{'med |λ0-DA|':>13}{'mean':>9}{'<= $2':>8}")
    for name, _, _ in variants:
        v = np.asarray(rows[name], float)
        if not len(v):
            print(f"{name:<28}{0:>9}{'--':>13}")
            continue
        err = np.abs(v[:, 0] - v[:, 1])
        print(
            f"{name:<28}{len(v):>9,}{np.median(err):>13.2f}{err.mean():>9.2f}"
            f"{np.mean(err <= 2.0) * 100:>7.1f}%"
        )

    print("\n=== K3(ii)b — stiffness and the displacement share ===")
    print(
        "  demand stiffness = MW of submitted price-sensitive + virtual demand"
        "\n  within +/- $5 of the posted price, per $; supply stiffness the same"
        "\n  on the submitted OFFER book. share = D / (D + S)."
    )
    if stiff_rows:
        s = np.asarray(stiff_rows, float)
        ok = np.isfinite(s[:, 0]) & np.isfinite(s[:, 1]) & ((s[:, 0] + s[:, 1]) > 0)
        d_st, s_st = s[ok, 0] / 1000.0, s[ok, 1] / 1000.0  # GW per $
        share = d_st / (d_st + s_st)
        print(
            f"  n = {ok.sum():,} hours | demand stiffness median "
            f"{np.median(d_st):.3f} GW/$ | supply stiffness median "
            f"{np.median(s_st):.3f} GW/$"
        )
        print(
            f"  displacement share: median {np.median(share) * 100:.1f}% | "
            f"mean {share.mean() * 100:.1f}% | share of hours >= 30 % "
            f"{np.mean(share >= 0.30) * 100:.1f}%"
        )
        print(
            f"  book composition: fixed (unpriced) demand is "
            f"{np.median(s[ok, 2] / s[ok, 3]) * 100:.1f}% of the published"
            f" cleared quantity (median hour)"
        )
    else:
        print("  no hours with both books present")

    print("\n=== K3(ii)c — MATERIALITY: is the PJM premise true at NEISO? ===")
    print(
        "  PJM's lever runs on +7-11 GW of net DEC at the top summer hours"
        "\n  (matrix da_virtual_bids). Net virtual = submitted DEC that would"
        "\n  clear at the posted price minus submitted INC that would."
    )
    if virt_rows:
        v = pd.DataFrame(
            virt_rows, columns=["year", "hour", "net", "dec", "inc"]
        )
        print(
            f"{'year':>6}{'peak-window net':>17}{'trough-window net':>19}"
            f"{'differential':>14}{'implied $ of spread':>21}"
        )
        s_med = (
            np.median(np.asarray(stiff_rows, float)[:, 1]) / 1000.0
            if stiff_rows
            else np.nan
        )
        for y, g in v.groupby("year"):
            pk = g[g["hour"].isin([16, 17, 18, 19])]["net"].mean() / 1000.0
            tr = g[g["hour"].isin([1, 2, 3, 4])]["net"].mean() / 1000.0
            dgw = pk - tr
            usd = dgw / s_med if np.isfinite(s_med) and s_med > 0 else np.nan
            print(
                f"{int(y):>6}{pk:>+16.2f}G{tr:>+18.2f}G{dgw:>+13.2f}G"
                f"{usd:>+20.2f}"
            )
        print(
            f"  supply stack slope used: {1.0 / s_med:.2f} $/GW "
            f"(median measured supply stiffness {s_med:.3f} GW/$)"
        )
        print(
            "  hour-of-day mean net virtual (GW), HE01-24:\n    "
            + " ".join(
                f"{v[v['hour'] == h]['net'].mean() / 1000.0:+.2f}"
                for h in range(24)
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
