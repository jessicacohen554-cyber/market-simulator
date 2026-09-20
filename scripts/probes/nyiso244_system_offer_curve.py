"""nyiso-244 — the SYSTEM offer curve, model against measured, in the missed tail hours.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). The only model-side call is a ``fleet_only``
rebuild of the keeper's own recipe.

**Why this measurement and not another cohort attempt.** The design pass
(``nyiso244_offer_surface_design.py``) refused the peak-rung offer-surface form on
REACH: 74.5 % of the idle sub-gate capacity sits on **econ** rungs and only 14.5 %
on the peak rungs the shared kernel prices. It also failed the cohort validation,
because P-27 is masked. This probe answers the successor's question **without any
cohort at all**: compare the two fleets' AGGREGATE offer curves. A system offer
curve is class-free, so masking cannot block it, and it says not just *that* the
model's curve is too cheap but *where* in the curve it is too cheap.

Both sides are NYCA-internal generators, the nyiso-243 §3 scope correction applied
(``NYISO_external_*`` import tranches and ``NYISO_DR_*`` excluded model-side;
P-27 ``genbids`` is internal-only by construction).

* **measured** — cumulative MW whose submitted 12-block offer price is at or below
  P, from P-27 DAM, plus the UOL headroom above the last priced block.
* **model** — cumulative ``pmax x availability`` whose assembled P1 offer
  (``mc_base``, every pricing overlay applied) is at or below P.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso244_system_offer_curve.py
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
GENBIDS = REPO / "data" / "raw" / "nyiso-bid-data" / "genbids"
OUT = REPO / "results" / "calibration" / "_nyiso244_system_offer_curve.json"

HOURS = 8760
#: The price grid the two curves are evaluated on. Deliberately a GRID, not a
#: fitted knot set: nothing here is selected, and no threshold gates anything.
GRID = (0.0, 25.0, 50.0, 75.0, 100.0, 150.0, 200.0, 300.0, 500.0, 1000.0)
_MW_COLS = [f"Dispatch MW{i}" for i in range(1, 13)]
_PX_COLS = [f"Dispatch $/MW{i}" for i in range(1, 13)]
_NON_GENBID = ("NYISO_external", "NYISO_DR")


def measured_curve(year: int, market: str = "DAM") -> pd.DataFrame:
    """Hourly cumulative measured MW offered AT OR BELOW each grid price."""
    acc: list[pd.DataFrame] = []
    from scripts.probes.nyiso243_offered_availability import _std_hour

    for month in range(1, 13):
        path = GENBIDS / f"{year:04d}{month:02d}01biddata_genbids_csv.zip"
        if not path.exists():
            continue
        with zipfile.ZipFile(path) as z:
            raw = pd.read_csv(
                io.BytesIO(z.read(z.namelist()[0])),
                skipinitialspace=True,
                low_memory=False,
            )
        raw.columns = [c.strip() for c in raw.columns]
        raw = raw[raw["Market"].astype(str).str.strip() == market]
        if raw.empty:
            continue
        ts = pd.to_datetime(
            raw["Date Time"].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S"
        )
        hour = _std_hour(pd.DatetimeIndex(ts).tz_localize("UTC"), year)
        mw = raw[_MW_COLS].to_numpy(float)
        px = raw[_PX_COLS].to_numpy(float)
        out = {"hour": hour}
        for p in GRID:
            out[f"le_{p:.0f}"] = np.where((px <= p) & np.isfinite(mw), mw, 0.0).max(axis=1)
        frame = pd.DataFrame(out)
        acc.append(frame[frame["hour"] >= 0].groupby("hour").sum())
    if not acc:
        raise FileNotFoundError(f"no P-27 archives for {year}")
    return pd.concat(acc).groupby(level=0).sum().reindex(range(HOURS))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    from scripts.probes.nyiso242_tail_reachability import missed_mask
    from scripts.probes.nyiso244_offer_surface_design import fleet_state

    year = args.year
    st = fleet_state(year)
    fa = st["fleet_arrays"]
    uid = np.array([str(u) for u in fa.unit_ids])
    keep = np.ones(len(uid), dtype=bool)
    for pre in _NON_GENBID:
        keep &= ~np.char.startswith(uid, pre)
    pmax = np.asarray(fa.pmax, dtype=float)[keep]
    av = np.asarray(fa.availability, dtype=float)
    if av.ndim == 1:
        av = np.repeat(av[:, None], HOURS, axis=1)
    av = av[keep]
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    mc = mc[keep]

    missed, month = missed_mask(year)
    idx = np.arange(len(missed))
    wins = {
        "winter_missed": idx[missed & np.isin(month, (1, 2, 12))],
        "ordinary_winter": idx[~missed & np.isin(month, (1, 2, 12))],
        "all_8760": idx,
    }
    meas = measured_curve(year)

    result: dict = {
        "year": year,
        "grid": list(GRID),
        "note": (
            "Class-free: a SYSTEM offer curve needs no cohort, so P-27's masking "
            "cannot block it. Model side is NYCA-internal rows only (external "
            "import tranches and DR excluded, nyiso-243 section 3)."
        ),
        "windows": {},
    }
    for label, sel in wins.items():
        sel = sel[sel < mc.shape[1]]
        if not len(sel):
            continue
        cap = pmax[:, None] * av[:, sel]
        px = mc[:, sel]
        rec = {"hours": int(len(sel)), "model_mw_le": {}, "measured_mw_le": {}, "gap_mw": {}}
        for p in GRID:
            m = float(np.median(((px <= p) * cap).sum(axis=0)))
            col = meas[f"le_{p:.0f}"].to_numpy(float)[sel]
            col = col[np.isfinite(col)]
            q = float(np.median(col)) if len(col) else float("nan")
            rec["model_mw_le"][f"{p:.0f}"] = round(m, 1)
            rec["measured_mw_le"][f"{p:.0f}"] = round(q, 1)
            rec["gap_mw"][f"{p:.0f}"] = round(m - q, 1)
        result["windows"][label] = rec
        print(f"\n=== {label}  n={len(sel)}")
        print(f"{'price':>8s} {'model MW<=P':>13s} {'measured MW<=P':>15s} {'model-measured':>16s}")
        for p in GRID:
            k = f"{p:.0f}"
            print(
                f"{p:8.0f} {rec['model_mw_le'][k]:13.1f} {rec['measured_mw_le'][k]:15.1f} "
                f"{rec['gap_mw'][k]:16.1f}"
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
