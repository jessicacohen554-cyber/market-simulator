"""nyiso-243 — the chartered availability intake's PRE-REGISTERED KILL TEST.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). The only model-side call is a fleet-only
rebuild of the keeper's own recipe, which enters no LP.

The charter
(``docs/RESULT-nyiso242-cc-winter-refused-and-the-intake-charter-2026-09-20.md``
§2.5) refused the CAMPD cold-hour census because CAMPD meters what **ran**:
the fleet sat at a flat ~50 % of its own ceiling in *every* price condition,
which is a coincidence factor, not an availability signal. The charter's
requirement for a successor is a source that states **availability directly**,
and its binding gate is that the derived derate must **deepen with price**.

This probe runs that gate against NYISO MIS **P-27** masked generator bid data,
whose ``Upper Oper Limit`` (UOL) is the resource's own statement of what it
could produce in that hour. Gate thresholds are fixed in
``docs/PRECOMMIT-nyiso243-outage-intake-kill-test-2026-09-20.md`` §3, written
and committed before any price-conditioned number here was computed.

Three legs:

* **Leg 1 — does it deepen with price?** Self-normalized; uses no model
  quantity. Offered UOL in each extreme-price window against a **within-season**
  ordinary baseline (a shoulder-month maintenance trough is not a cold-snap
  signal). PASS needs a deficit ≥ 1,000 MW *and* monotonicity across the DA
  ladder $100 → $150 → $200 → $300.
* **Leg 2 — does it reach?** Measured offered UOL against the keeper's own
  believed-available fleet, whole-fleet to whole-fleet (masking forbids a
  thermal-only cut on the measured side). PASS needs the deficit in the winter
  cluster to exceed its ordinary-hour level by ≥ 1,000 MW, and it is reported
  against the 4,716 MW the object requires.
* **Leg 3 — the reserve control.** Diagnostic only, never a gate: how much
  offered-but-undispatched capacity carries a positive AS offer. This is the
  quantity that explains the predecessor's flat 50 %.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso243_offered_availability.py
    PYTHONPATH=.:src python3 scripts/probes/nyiso243_offered_availability.py --years 2022 --no-leg2
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
HUB = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
GENBIDS = REPO / "data" / "raw" / "nyiso-bid-data" / "genbids"
OUT = REPO / "results" / "calibration" / "_nyiso243_offered_availability.json"

THRESHOLD = 300.0
HOURS = 8760
WINTER = (1, 2, 12)
SUMMER = (6, 7, 8)

#: PRECOMMIT §3.2(a) / §3.3 — fixed before any conditioned number was computed.
DEFICIT_GATE_MW = 1000.0
#: FINDING-nyiso242 §3.2 — MW of idle sub-gate capacity in the 2022 winter cluster.
OBJECT_MW = 4716.0
#: The DA ladder of nyiso-242 §2.3, reproduced so the two instruments compare.
DA_LADDER = (100.0, 150.0, 200.0, 300.0)

_UOL = "Upper Oper Limit"
_AS_COLS = (
    "10 Min Non-Synch MW",
    "10 Min Spin MW",
    "30 Min Non-Synch MW",
    "30 Min Spin MW",
    "Regulation MW",
)
_USECOLS = ("Masked Gen ID", "Date Time", "Market", _UOL, "Fixed Min Gen MW", "On Dispatch", *_AS_COLS)


# ---------------------------------------------------------------------------
# The measured side — P-27 offered availability on the model's 8760 calendar
# ---------------------------------------------------------------------------
def _std_hour(ts_utc: pd.DatetimeIndex, year: int) -> np.ndarray:
    """Chronological EST hour-of-year, the calendar every hourly sidecar uses.

    Delegates to the gate's own mapper so the join convention is identical by
    construction rather than by reimplementation.
    """
    import sys

    sys.path.insert(0, str(REPO / "scripts" / "data"))
    from derive_actual_lmp import _STD_TZ, _std_hour_index  # noqa: PLC0415

    return _std_hour_index(ts_utc, year, _STD_TZ["NYISO"])


def offered_hourly(year: int) -> tuple[pd.DataFrame, dict]:
    """Hourly offered availability for ``year``, plus the UTC-assumption check.

    Returns a frame indexed 0..8759 with, per market, the fleet's summed
    ``Upper Oper Limit``, its offered AS MW, and the count of resources that
    submitted at all — a resource fully out of service simply has no row, which
    is itself an availability statement.
    """
    frames = []
    span: dict[str, list[str]] = {}
    for month in range(1, 13):
        path = GENBIDS / f"{year:04d}{month:02d}01biddata_genbids_csv.zip"
        if not path.exists():
            continue
        with zipfile.ZipFile(path) as z:
            name = z.namelist()[0]
            raw = pd.read_csv(
                io.BytesIO(z.read(name)),
                skipinitialspace=True,
                low_memory=False,
            )
        raw.columns = [c.strip() for c in raw.columns]
        raw = raw[[c for c in _USECOLS if c in raw.columns]].copy()
        raw["Market"] = raw["Market"].astype(str).str.strip()
        ts = pd.to_datetime(raw["Date Time"].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S")
        if month in (1, 7):
            span[f"{month:02d}"] = [str(ts.min()), str(ts.max())]
        raw["hour"] = _std_hour(pd.DatetimeIndex(ts).tz_localize("UTC"), year)
        frames.append(raw[raw["hour"] >= 0])

    if not frames:
        raise FileNotFoundError(f"no P-27 archives for {year} under {GENBIDS}")
    d = pd.concat(frames, ignore_index=True)
    d["as_mw"] = d[[c for c in _AS_COLS if c in d.columns]].fillna(0.0).sum(axis=1)

    out = pd.DataFrame(index=pd.RangeIndex(HOURS, name="hour"))
    for market in ("DAM", "HAM"):
        sub = d[d["Market"] == market]
        g = sub.groupby("hour")
        out[f"{market.lower()}_uol"] = g[_UOL].sum()
        out[f"{market.lower()}_as"] = g["as_mw"].sum()
        out[f"{market.lower()}_n"] = g["Masked Gen ID"].nunique()

    # The UTC assumption is load-bearing for every join below, so it is
    # CHECKED rather than asserted: a UTC-stamped January file must span
    # 05:00 -> 04:00 (EST = UTC-5) and July 04:00 -> 03:00 (EDT = UTC-4).
    check = {
        "jan_span": span.get("01"),
        "jul_span": span.get("07"),
        "utc_consistent": bool(
            span.get("01")
            and span.get("07")
            and span["01"][0].endswith("05:00:00")
            and span["07"][0].endswith("04:00:00")
        ),
        "hours_covered": int(out["dam_uol"].notna().sum()),
        "gens_max": int(np.nanmax(out["dam_n"].to_numpy(float))),
    }
    return out, check


# ---------------------------------------------------------------------------
# Windows — the gate's own price series, with a WITHIN-SEASON baseline
# ---------------------------------------------------------------------------
def windows(year: int) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    hub = pd.read_parquet(HUB)
    hub = hub[hub["year"] == year].sort_values("hour")
    rt = hub["rt"].to_numpy(float)[:HOURS]
    da = hub["da"].to_numpy(float)[:HOURS]
    n = len(rt)
    month = pd.date_range(f"{year}-01-01", periods=n, freq="h").month.to_numpy()

    sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"] != "NYISO_external")]
    mmax = sysf.groupby("hour")["price"].max().sort_index().to_numpy()[:n]
    missed = (rt > THRESHOLD) & (mmax <= THRESHOLD)

    idx = np.arange(n)
    win: dict[str, np.ndarray] = {}
    for season, months in (("winter", WINTER), ("summer", SUMMER)):
        insn = np.isin(month, months)
        med = np.nanmedian(rt[insn])
        # "Ordinary" = that season's own below-median hours. The baseline must
        # be within-season or a shoulder maintenance trough reads as a signal.
        win[f"ordinary_{season}"] = idx[insn & (rt < med)]
        win[f"missed_{season}"] = idx[insn & missed]
    win["ordinary_all"] = idx[rt < np.nanmedian(rt)]
    win["missed_all"] = idx[missed]
    for gate in DA_LADDER:
        win[f"da_gt_{gate:.0f}"] = idx[da > gate]
    win["rt_gt300_da_anticipated"] = idx[(rt > THRESHOLD) & (da > THRESHOLD)]
    win["rt_gt300_da_surprise"] = idx[(rt > THRESHOLD) & (da <= THRESHOLD)]
    return win, rt, da


# ---------------------------------------------------------------------------
# Legs
# ---------------------------------------------------------------------------
def _med(series: pd.Series, sel: np.ndarray) -> float | None:
    v = series.to_numpy(float)[sel]
    v = v[np.isfinite(v)]
    return float(np.median(v)) if len(v) else None


def leg1(off: pd.DataFrame, win: dict[str, np.ndarray], rt: np.ndarray, da: np.ndarray) -> dict:
    """Does offered availability deepen with price? (PRECOMMIT §3.2)"""
    rows: dict[str, dict] = {}
    for label, sel in win.items():
        if not len(sel):
            continue
        rows[label] = {
            "hours": int(len(sel)),
            "rt_median": round(float(np.nanmedian(rt[sel])), 2),
            "da_median": round(float(np.nanmedian(da[sel])), 2),
            "dam_uol_mw": _round(_med(off["dam_uol"], sel)),
            "ham_uol_mw": _round(_med(off["ham_uol"], sel)),
            "dam_gens": _round(_med(off["dam_n"], sel)),
            "ham_gens": _round(_med(off["ham_n"], sel)),
        }

    def deficit(label: str, base: str, market: str) -> float | None:
        a, b = rows.get(label), rows.get(base)
        key = f"{market}_uol_mw"
        if not a or not b or a[key] is None or b[key] is None:
            return None
        # Positive = LESS offered than the baseline, i.e. the direction the
        # object needs. Negative = MORE available in extreme hours.
        return round(b[key] - a[key], 1)

    out: dict = {"windows": rows, "deficit_vs_baseline_mw": {}}
    pairs = [
        ("missed_winter", "ordinary_winter"),
        ("missed_summer", "ordinary_summer"),
        ("missed_all", "ordinary_all"),
        ("rt_gt300_da_anticipated", "ordinary_all"),
        ("rt_gt300_da_surprise", "ordinary_all"),
        *[(f"da_gt_{g:.0f}", "ordinary_all") for g in DA_LADDER],
    ]
    for label, base in pairs:
        out["deficit_vs_baseline_mw"][label] = {
            m: deficit(label, base, m) for m in ("dam", "ham")
        }

    # THE GATE. Both conditions are the PRECOMMIT's, fixed before this ran.
    verdict: dict = {}
    for market in ("dam", "ham"):
        ladder = [out["deficit_vs_baseline_mw"].get(f"da_gt_{g:.0f}", {}).get(market) for g in DA_LADDER]
        have = [v for v in ladder if v is not None]
        monotone = all(b >= a - 1e-9 for a, b in zip(have, have[1:])) if len(have) > 1 else False
        peak = max((v for v in have), default=None)
        winter = out["deficit_vs_baseline_mw"]["missed_winter"][market]
        magnitude_ok = any(
            v is not None and v >= DEFICIT_GATE_MW for v in (winter, peak)
        )
        verdict[market] = {
            "ladder_deficit_mw": ladder,
            "ladder_monotone_nondecreasing": monotone,
            "winter_missed_deficit_mw": winter,
            "magnitude_ge_1000mw": magnitude_ok,
            "PASS": bool(monotone and magnitude_ok),
        }
    out["gate"] = verdict
    out["PASS"] = bool(verdict["dam"]["PASS"] or verdict["ham"]["PASS"])
    return out


def leg2(year: int, off: pd.DataFrame, win: dict[str, np.ndarray]) -> dict:
    """Measured offered availability against the keeper's believed fleet. (§3.3)"""
    from scripts.probes.nyiso242_tail_reachability import fleet_state

    st = fleet_state(year)
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    if av.ndim == 1:
        av = np.repeat(av[:, None], HOURS, axis=1)
    cap = pmax[:, None] * av
    klass = np.array([str(k) for k in fa.plant_group])

    # SCOPE. P-27 ``genbids`` carries NYCA *internal generators* only: external
    # transactions are a separate product (``tranbids``) and demand-side
    # resources are not bid generators at all. The keeper's fleet arrays carry
    # both — 7,110 MW of ``NYISO_external_*`` import tranches and 1,170 MW of
    # ``NYISO_DR_*`` in 2022 — so comparing the raw totals compares different
    # fleets. The DR rows are the worse of the two: SCR/EDRP is armed only in
    # emergency hours, so it switches ON exactly in the windows under study and
    # would read as a model "over-belief" that the measured side never had the
    # chance to state. Both are removed for the comparable scope; the all-in
    # total is kept beside it so the adjustment is visible rather than implicit.
    uid = np.array([str(u) for u in fa.unit_ids])
    external = np.char.startswith(uid, "NYISO_external") | np.char.startswith(uid, "NYISO_DR")
    believed_all = cap.sum(axis=0)
    believed = cap[~external].sum(axis=0)

    # The measured side is MASKED — no class, no fuel, no zone — so the
    # comparison can only be whole-fleet to whole-fleet. The composition is
    # reported so a reader can see exactly what is on each side of it rather
    # than take the aggregate on trust.
    composition = {
        k or "(unclassed)": round(float(np.median(cap[klass == k].sum(axis=0))), 1)
        for k in sorted(set(klass.tolist()))
    }
    composition["EXCLUDED_external_and_DR"] = round(
        float(np.median(cap[external].sum(axis=0))), 1
    )

    rows: dict[str, dict] = {}
    for label, sel in win.items():
        if not len(sel):
            continue
        sel = sel[sel < len(believed)]
        b = float(np.median(believed[sel]))
        rows.setdefault(label, {})["believed_mw"] = round(b, 1)
        rows[label]["believed_all_in_mw"] = round(float(np.median(believed_all[sel])), 1)
        for market in ("dam", "ham"):
            m = _med(off[f"{market}_uol"], sel)
            rows[label][f"{market}_offered_mw"] = _round(m)
            rows[label][f"{market}_gap_mw"] = round(b - m, 1) if m is not None else None

    out: dict = {
        "windows": rows,
        "believed_composition_mw_median": composition,
        "excess_gap_vs_ordinary_mw": {},
        "object_mw": OBJECT_MW,
    }
    for label, base in (("missed_winter", "ordinary_winter"), ("missed_summer", "ordinary_summer")):
        for market in ("dam", "ham"):
            a = rows.get(label, {}).get(f"{market}_gap_mw")
            c = rows.get(base, {}).get(f"{market}_gap_mw")
            out["excess_gap_vs_ordinary_mw"].setdefault(label, {})[market] = (
                round(a - c, 1) if a is not None and c is not None else None
            )
    winter = out["excess_gap_vs_ordinary_mw"].get("missed_winter", {})
    best = max((v for v in winter.values() if v is not None), default=None)
    out["winter_excess_gap_mw"] = best
    out["winter_excess_gap_pct_of_object"] = (
        round(100.0 * best / OBJECT_MW, 1) if best is not None else None
    )
    out["PASS"] = bool(best is not None and best >= DEFICIT_GATE_MW)
    return out


def leg3(off: pd.DataFrame, win: dict[str, np.ndarray]) -> dict:
    """Reserve control — diagnostic only, never a gate. (§3.4)"""
    rows = {}
    for label in ("missed_winter", "missed_summer", "missed_all", "ordinary_all"):
        sel = win.get(label)
        if sel is None or not len(sel):
            continue
        rows[label] = {
            m: {
                "uol_mw": _round(_med(off[f"{m}_uol"], sel)),
                "as_offered_mw": _round(_med(off[f"{m}_as"], sel)),
            }
            for m in ("dam", "ham")
        }
    return rows


def _round(v: float | None, nd: int = 1) -> float | None:
    return None if v is None or not np.isfinite(v) else round(float(v), nd)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2025])
    ap.add_argument("--no-leg2", action="store_true", help="Skip the fleet rebuild.")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    result: dict = {
        "precommit": "docs/PRECOMMIT-nyiso243-outage-intake-kill-test-2026-09-20.md",
        "source": "NYISO MIS P-27 masked generator bid data (Upper Oper Limit)",
        "gate_mw": DEFICIT_GATE_MW,
        "object_mw": OBJECT_MW,
        "years": {},
    }
    for year in args.years:
        off, check = offered_hourly(year)
        win, rt, da = windows(year)
        rec: dict = {"source_check": check, "leg1": leg1(off, win, rt, da), "leg3": leg3(off, win)}
        if not args.no_leg2:
            rec["leg2"] = leg2(year, off, win)
        result["years"][str(year)] = rec
        print(f"{year}: leg1 PASS={rec['leg1']['PASS']}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
