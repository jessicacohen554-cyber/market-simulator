"""Derive the CAISO DA charge-allocation profile (M1, caiso-104).

Rule-23 derive for ``ScenarioConfig.caiso_charge_allocation_schedule`` (the
owner-granted caiso-103 belly ask, docs/handoffs/caiso-103-belly-allocation-
ask-2026-07-19.md): per year, the 24-value hour-of-day share of annual IFM
(day-ahead) fleet charge, plus ``da_frac`` — the DA-share of realized (RTD)
charge. The dispatch mechanism floors each day's fleet battery charge at
``alloc_share[hod] x da_frac x (day total charge)`` (the Fourier-Motzkin
elimination of the ask's per-day scheduled-volume variable ``S[d]``), so the
intra-day allocation follows the measured DAM conduct while the charge VOLUME
stays fully endogenous.

Source (committed raw; no model output): the CAISO Daily Energy Storage
Report quarterly xlsx (``data/raw/storage-as-awards/CAISO/storage-report-*
.xlsx``, ``market_output`` sheet), LESR rows only — the caiso-98/99/100/102
basis (HYBD excluded: combined-resource EN mixes PV). Clock: TRADE_DATE+HOUR
are prevailing-Pacific hour-ending physical-hour labels, hod = HOUR-1,
fall-back 25th hour and Feb-29 dropped (the ``_caiso102_charge_channels``
convention; measured statistics quoted in FINDING-caiso103 §1).

Statistics per year:
  * ``alloc_share[hod]`` = (annual IFM charge in hod) / (annual IFM charge),
    Σ_hod = 1 — statistic (A) of ``scripts/probes/_caiso103_alloc_stats.py``
    (fleet-size-invariant: pairwise cross-year r >= 0.994 across a 3.5x
    fleet).
  * ``da_frac`` = Σ min(chg_IFM, chg_RTD) / Σ chg_RTD — the DA-scheduled
    share of realized charge (FINDING-caiso102 §1: 0.840/0.799/0.760).

Forward semantics (owner sub-choice, caiso-104 session ruling): a solve year
beyond the derived span uses the LATEST measured year's row — the caiso-99
envelope precedent (latest-year carry), for the shape and ``da_frac`` alike.

Output: ``data/raw/reference/caiso-charge-allocation-profile.csv`` with
columns ``year, hod, alloc_share, da_frac`` (da_frac repeated per hod row for
a flat schema). Deterministic; re-derives only when the storage-report source
updates (rule 23).

Usage:
  python scripts/data/derive_caiso_charge_allocation.py [--cache <parquet>]
--cache points at a pre-parsed concat of the market_output sheets; without it
the xlsx are parsed (~5 min).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "storage-as-awards" / "CAISO"
OUT = REPO / "data" / "raw" / "reference" / "caiso-charge-allocation-profile.csv"
YEARS = (2023, 2024, 2025)


def load_market_output(cache: Path | None) -> pd.DataFrame:
    """All market_output rows from the quarterly storage-report xlsx."""
    if cache is not None:
        return pd.read_parquet(cache)
    frames = []
    for f in sorted(RAW.glob("storage-report-*.xlsx")):
        frames.append(pd.read_excel(f, sheet_name="market_output"))
    if not frames:
        raise FileNotFoundError(f"no storage-report-*.xlsx under {RAW}")
    return pd.concat(frames, ignore_index=True)


def hourly_pivot(mo: pd.DataFrame) -> pd.DataFrame:
    """LESR rows -> one row per (date, hod) with IFM/RTD EN (MW, hour-avg).

    The ``_caiso102_charge_channels`` convention: RTD 5-min intervals are
    hour-averaged, fall-back 25th hour and Feb-29 dropped.
    """
    d = mo[mo.RES_TYPE == "LESR"].copy()
    d["TRADE_DATE"] = pd.to_datetime(d["TRADE_DATE"])
    d = d[(d.TRADE_DATE.dt.month != 2) | (d.TRADE_DATE.dt.day != 29)]
    d["hod"] = d.HOUR - 1
    d = d[(d.hod >= 0) & (d.hod < 24)]
    d = d[d.TYPE == "EN"]
    g = d.groupby(["TRADE_DATE", "hod", "MARKET"], as_index=False).VALUE.mean()
    p = g.pivot_table(
        index=["TRADE_DATE", "hod"], columns="MARKET", values="VALUE", aggfunc="mean"
    )
    p.columns = [f"{m}_EN" for m in p.columns]
    return p.reset_index()


def main() -> int:
    cache = None
    args = sys.argv[1:]
    if "--cache" in args:
        cache = Path(args[args.index("--cache") + 1])
    p = hourly_pivot(load_market_output(cache))
    p["TRADE_DATE"] = pd.to_datetime(p["TRADE_DATE"])

    rows = []
    for year in YEARS:
        py = p[p.TRADE_DATE.dt.year == year]
        if py.empty:
            print(f"{year}: no storage-report coverage — skipped")
            continue
        # Zero-fill absent slots (the probe's full-grid fillna(0) convention:
        # an unreported slot contributes no charge to either market's sum).
        chg_ifm = np.clip(-np.nan_to_num(py["IFM_EN"].to_numpy(dtype=float)), 0.0, None)
        chg_rtd = np.clip(-np.nan_to_num(py["RTD_EN"].to_numpy(dtype=float)), 0.0, None)
        hod = py["hod"].to_numpy(dtype=int)
        ann_ifm = chg_ifm.sum()
        if ann_ifm <= 0.0:
            print(f"{year}: zero annual IFM charge — skipped")
            continue
        # da_frac: DA-scheduled share of realized charge, per-slot coverage
        # summed annually (min(chg_IFM, chg_RTD) — FINDING-caiso102 §1).
        cov = np.minimum(chg_ifm, chg_rtd)
        da_frac = float(cov.sum() / chg_rtd.sum())
        share = np.zeros(24)
        for h in range(24):
            share[h] = chg_ifm[hod == h].sum() / ann_ifm
        assert abs(share.sum() - 1.0) < 1e-9
        for h in range(24):
            rows.append(
                {
                    "year": year,
                    "hod": h,
                    "alloc_share": round(float(share[h]), 6),
                    "da_frac": round(da_frac, 4),
                }
            )
        belly = share[10:15].sum()
        print(
            f"{year}: da_frac {da_frac:.4f} | belly(10-14) share {belly:.3f} | "
            f"morning(6-9) {share[6:10].sum():.3f} | evening(17-21) "
            f"{share[17:22].sum():.3f}"
        )

    if not rows:
        print("nothing derived — no output written")
        return 1
    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
