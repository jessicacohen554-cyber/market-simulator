"""neiso-75 charter input: decompose the NEISO C3c miss — systemic diurnal
amplitude vs NEISO-local scarcity/winter formation. NO LP.

The NEISO keeper (`2026-07-31-neiso-72-hy-window`) prints ZERO model hours
> $300/MWh against an actual RT tail of 15 / 8 / 20 h (2023/24/25) — the single
ledgered C3c caveat. xiso-1 established that the keeper's diurnal price
amplitude is 23–34 % of measured (the worst of six ISOs) and the xiso-1
standing order blocks storage-side price-shape levers until that systemic
defect closes. The charter question this probe answers: **how much of the C3c
tail miss is the systemic amplitude defect, and how much is NEISO-local
scarcity/winter price formation the amplitude lane would never produce?**

Method — read-only decomposition on the keeper's committed hourly sidecars +
the committed hub actuals (the xiso-1 loaders, imported, not re-implemented;
`pass == "P1"`, delivered price, load-weighted C3a basis; measured side
`actual_lmp_hourly_NEISO.parquet` on the same non-leap 8760 calendar):

For each hour ``h`` on day ``d``, split each series into a DAILY LEVEL (that
day's 24-h mean) and a WITHIN-DAY DEVIATION from it, and form three
counterfactual model prices:

* **CF-A "gain restored" (the systemic-defect counterfactual):**
  ``m_dm[d] + G_y * (m[h] - m_dm[d])`` with ``G_y`` = the year's measured/model
  hour-of-day mean-range ratio (the exact xiso-1 statistic, recomputed here as
  a loader check). This is what the keeper's price would look like if the
  SYSTEMIC defect — the compressed daily-cycle gain — were fully closed, with
  daily levels and within-day shape otherwise the model's own.
* **CF-B "shape graft" (upper bound of ALL within-day mechanisms):**
  ``m_dm[d] + (a[h] - a_dm[d])`` — the actual's own within-day deviation on
  the model's daily level. No within-day mechanism (amplitude, intraday
  scarcity adder, RT transient formation) can do better while daily levels
  stay the model's, so tail hours CF-B does NOT cross are attributable to
  missing DAILY-LEVEL formation (fuel-spike / event-day level), not to any
  within-day defect.
* **CF-C "level graft" (daily-level/event mechanisms):**
  ``a_dm[d] + (m[h] - m_dm[d])`` — the actual's daily level with the model's
  own compressed within-day deviation. Tail hours CF-C crosses are closable by
  an event-day LEVEL mechanism alone (e.g. cold-snap fuel/scarcity lifting the
  whole day) even with the amplitude defect left open.

CF-B + CF-C jointly partition each missed tail hour into: within-day-closable,
level-closable, either, or JOINT-ONLY (needs both). CF-A isolates the share of
the within-day half that the *systemic* (daily-cycle gain) defect explains —
the remainder of the within-day half is event-hour deviation far beyond the
daily cycle (RT scarcity formation), which is local, not systemic.

Admissibility: an audit of committed artifacts, not a mechanism — nothing is
fed back into any solve, so rule 13 `[R-MEASURED]` is not engaged (the xiso-1 /
neiso-74 disposition). Rule 25: every number is NEISO's own. Years 2023–2025
only (rule 22 `[R-HOLDOUT]`: training window; nothing outside it is read).

Run:  python scripts/probes/_neiso75_c3c_decomposition.py
Record: results/calibration/PROBE-neiso75-c3c-decomposition-2026-08-02.txt
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]

# Import the xiso-1 probe's loaders so this decomposition is byte-for-byte the
# same construction (keeper store lookup, P1 filter, load-weighting, calendar).
_X1 = REPO / "scripts/probes/_xiso1_diurnal_amplitude_audit.py"
_spec = importlib.util.spec_from_file_location("_xiso1", _X1)
_x1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_x1)

YEARS = (2023, 2024, 2025)
THRESHOLD = 300.0  # TAIL_THRESHOLD["NEISO"], scripts/calibration_verdict.py
# C3c gate arithmetic (scripts/calibration_verdict.py TAIL_LO/HI/SMALL_COUNT):
# actual >= 10 -> model in [0.5x, 2x]; actual < 10 -> |model-actual| <= 10.
TAIL_LO, TAIL_HI, TAIL_SMALL = 0.5, 2.0, 10

# Season buckets matching the keeper attestation's anatomy labels
# (winter = Dec/Jan/Feb, summer = Jun..Sep incl. the Sep-2023 events,
# shoulder = the rest — reproduces the ledger's 10/5, 7/1, 7/11/2 splits).
_WINTER, _SUMMER = {12, 1, 2}, {6, 7, 8, 9}


def hour_date(k: int) -> tuple[int, int, int]:
    """Map hour index ``k`` (0..8759) to (month, day, hour-of-day).

    The model calendar is non-leap local standard time with Feb 29 dropped
    (`scripts/data/derive_actual_lmp.py`), so a fixed non-leap template year
    dates every hour of every model year.
    """
    d = dt.datetime(2023, 1, 1) + dt.timedelta(hours=int(k))
    return d.month, d.day, d.hour


def season(month: int) -> str:
    """Attestation-consistent season bucket for a calendar month."""
    if month in _WINTER:
        return "WIN"
    if month in _SUMMER:
        return "SUM"
    return "SHL"


def hod_range(price: np.ndarray) -> float:
    """xiso-1's amplitude statistic: range of the 365-day hour-of-day means.

    NaN-robust like `_xiso1.stats` (NEISO 2023 carries one missing measured
    hour, the Nov DST fall-back): missing hours are excluded from the means.
    """
    prof = np.nanmean(price[: 365 * 24].reshape(365, 24), axis=0)
    return float(np.nanmax(prof) - np.nanmin(prof))


def daily_mean(price: np.ndarray) -> np.ndarray:
    """Per-day 24-h mean (NaN-excluded), repeated back onto the hourly grid."""
    dm = np.nanmean(price[: 365 * 24].reshape(365, 24), axis=1)
    return np.repeat(dm, 24)


def gate(model_count: float, actual_count: float) -> str:
    """C3c verdict for a model tail count against the RT actual count."""
    if actual_count < TAIL_SMALL:
        ok = abs(model_count - actual_count) <= TAIL_SMALL
    else:
        ok = TAIL_LO * actual_count <= model_count <= TAIL_HI * actual_count
    return "PASS" if ok else "FAIL"


def main() -> int:
    """Run the decomposition and print the charter tables."""
    out = []

    def p(s: str = "") -> None:
        out.append(s)
        print(s)

    ks = _x1.keepers()
    kid, bundle = ks["NEISO"]
    p("neiso-75 — C3c decomposition: systemic amplitude vs local scarcity/winter (no LP)")
    p(f"keeper: {kid}  bundle: {bundle.relative_to(REPO)}")
    p(f"threshold: ${THRESHOLD:.0f}/MWh (RT actual = the gated basis, rubric v2.7)")

    grand = {}
    for year in YEARS:
        m = _x1.model_price(bundle, year)  # P1 delivered, load-weighted
        rt = _x1.measured_price("NEISO", year, "rt")
        da = _x1.measured_price("NEISO", year, "da")
        assert m is not None and rt is not None and da is not None

        # ---- loader check: reproduce the xiso-1 NEISO row exactly ----------
        lvl = 100.0 * (np.nanmean(m) - np.nanmean(da)) / np.nanmean(da)
        amp_da = hod_range(m) / hod_range(da)
        amp_rt = hod_range(m) / hod_range(rt)
        p(f"\n{'=' * 78}\n{year}  loader check — level vs DA {lvl:+.1f} %, "
          f"amplitude {100 * amp_da:.1f} % of DA / {100 * amp_rt:.1f} % of RT "
          f"(xiso-1 row reproduced)")
        p(f"  hour-of-day mean ranges: model ${hod_range(m):.2f}, "
          f"DA ${hod_range(da):.2f}, RT ${hod_range(rt):.2f} "
          f"(gap vs DA ${hod_range(da) - hod_range(m):.2f})")

        m_dm, rt_dm, da_dm = daily_mean(m), daily_mean(rt), daily_mean(da)
        g_rt, g_da = 1.0 / amp_rt, 1.0 / amp_da

        # Counterfactual price vectors, full 8760 (defined in the docstring).
        cfa = m_dm + g_rt * (m - m_dm)          # gain restored (systemic), RT basis
        cfa_da = m_dm + g_da * (m - m_dm)       # gain restored, DA-basis control
        cfb = m_dm + (rt - rt_dm)               # shape graft (within-day UB)
        cfc = rt_dm + (m - m_dm)                # level graft (event-day level)

        tail = np.where(rt > THRESHOLD)[0]
        da_tail = set(np.where(da > THRESHOLD)[0].tolist())
        p(f"actual RT tail {len(tail)} h (DA tail {len(da_tail)} h); "
          f"model >$300: {int((m > THRESHOLD).sum())} h, model max ${m.max():.0f}")
        # DA diagnostic row (report-only in the rubric): what a DA-formation
        # mechanism would target, and how close the keeper already is there.
        if da_tail:
            dl = sorted(da_tail)
            p(f"  DA-tail diagnostic: {len(dl)} h, {len(da_tail & set(tail.tolist()))} "
            f"also in the RT tail; model at those hours "
            f"${min(m[h] for h in dl):.0f}-${max(m[h] for h in dl):.0f}; "
            f"CF-A crosses {sum(1 for h in dl if cfa[h] > THRESHOLD)}/{len(dl)}")

        p(f"\n  per-hour decomposition of the {len(tail)} missed RT tail hours:")
        p("  date      hod seas   RT$    DA$  model$  m_dm$  rtdm$  DAvis"
          "  CF-A$  CF-B$  CF-C$  closable-by")
        rows = []
        for h in tail:
            mo, dy, hod = hour_date(h)
            sea = season(mo)
            davis = h in da_tail
            xa, xb, xc = cfa[h] > THRESHOLD, cfb[h] > THRESHOLD, cfc[h] > THRESHOLD
            if xb and xc:
                cls = "either"
            elif xb:
                cls = "within-day"
            elif xc:
                cls = "level-only"
            else:
                cls = "JOINT-ONLY"
            rows.append((sea, davis, xa, xb, xc, cls))
            p(f"  {mo:02d}-{dy:02d}  {hod:5d} {sea:4s} {rt[h]:6.0f} {da[h]:6.0f}"
              f" {m[h]:7.0f} {m_dm[h]:6.0f} {rt_dm[h]:6.0f}  {str(davis):5s}"
              f" {cfa[h]:6.0f} {cfb[h]:6.0f} {cfc[h]:6.0f}  {cls}"
              f"{'  [CF-A crosses]' if xa else ''}")

        # Per-event-day daily levels: separates "model misses the DA day
        # level" (in representation — fuel/formation) from "DA itself misses
        # the RT day" (the DA-RT wedge the rubric calls out of representation
        # for a realized-weather hourly LP).
        p("\n  per-event-day daily levels (all days carrying RT tail hours):")
        p("  day     n_tail  m_dm$  da_dm$  rt_dm$   (da-m)$  (rt-da)$")
        for d in sorted({int(h) // 24 for h in tail}):
            hs = [h for h in tail if h // 24 == d]
            mo, dy, _ = hour_date(d * 24)
            mdm, ddm, rdm = m_dm[d * 24], da_dm[d * 24], rt_dm[d * 24]
            p(f"  {mo:02d}-{dy:02d}  {len(hs):5d} {mdm:7.0f} {ddm:7.0f}"
              f" {rdm:7.0f}   {ddm - mdm:+7.0f}  {rdm - ddm:+7.0f}")

        # ---- aggregate shares ---------------------------------------------
        n = len(tail)
        na = sum(r[2] for r in rows)
        nb = sum(r[3] for r in rows)
        nc = sum(r[4] for r in rows)
        nj = sum(r[5] == "JOINT-ONLY" for r in rows)
        p(f"\n  hour-matched shares of the {n}-h RT tail:")
        p(f"    CF-A gain-restored (SYSTEMIC amplitude defect closed) crosses: "
          f"{na}/{n}")
        p(f"    CF-B any-within-day upper bound crosses:                       "
          f"{nb}/{n}")
        p(f"    CF-C event-day level alone crosses:                            "
          f"{nc}/{n}")
        p(f"    JOINT-ONLY (needs level AND within-day together):              "
          f"{nj}/{n}")

        # Full-year counterfactual tail COUNTS (C3c gates the count, not the
        # hour match) + the gate each would produce.
        p("\n  full-8760 counterfactual tail counts vs the C3c gate "
          f"(actual {n}, band {gate_band(n)}):")
        for name, v in (("keeper", m), ("CF-A gain restored (RT)", cfa),
                        ("CF-A gain restored (DA ctrl)", cfa_da),
                        ("CF-B within-day UB", cfb),
                        ("CF-C event-level graft", cfc)):
            cnt = int((v > THRESHOLD).sum())
            p(f"    {name:30s} {cnt:4d} h  -> {gate(cnt, n)}")

        # Mis-timed-tail check (the caiso-144 hazard): where do CF-A's
        # crossing hours actually FALL? A count that passes the gate while
        # landing off the real events is an invented tail, not a fix.
        xa_set = set(np.where(cfa > THRESHOLD)[0].tolist())
        on_ev = len(xa_set & set(tail.tolist()))
        p(f"    CF-A placement: {on_ev}/{len(xa_set)} crossing hours land ON "
          f"actual RT tail hours; crossings by day:")
        by_day: dict[str, int] = {}
        for h in sorted(xa_set):
            mo, dy, _ = hour_date(h)
            by_day[f"{mo:02d}-{dy:02d}"] = by_day.get(f"{mo:02d}-{dy:02d}", 0) + 1
        p("      " + (", ".join(f"{d} x{c}" for d, c in by_day.items())
                      if by_day else "(none)"))

        # Required within-day gain at the missed hours CF-A does NOT close:
        # (300 - m_dm) / (m - m_dm), vs the systemic gain G. A required gain
        # far above G means the hour is not the daily-cycle defect but event
        # formation (scarcity adders / RT transients) on top of it.
        need = []
        for h in tail:
            if cfa[h] > THRESHOLD:
                continue
            dev = m[h] - m_dm[h]
            need.append((THRESHOLD - m_dm[h]) / dev if dev > 1e-6 else np.inf)
        if need:
            fin = [x for x in need if np.isfinite(x)]
            p(f"    gain needed at the {len(need)} CF-A-missed hours "
              f"(systemic G = {g_rt:.2f}): median "
              f"{np.median(fin) if fin else float('nan'):.1f}x, "
              f"{sum(1 for x in need if not np.isfinite(x))} hours have "
              f"non-positive model deviation (no gain closes them)")

        # Seasonal / DA-visibility cut of the missed hours.
        for sea in ("WIN", "SUM", "SHL"):
            sub = [r for r in rows if r[0] == sea]
            if sub:
                p(f"    [{sea}] {len(sub):2d} h: CF-A {sum(r[2] for r in sub)}, "
                  f"CF-B {sum(r[3] for r in sub)}, CF-C {sum(r[4] for r in sub)}, "
                  f"JOINT-ONLY {sum(r[5] == 'JOINT-ONLY' for r in sub)}, "
                  f"DA-visible {sum(r[1] for r in sub)}")
        grand[year] = rows

    # ------------------------------------------------------------- summary
    p(f"\n{'=' * 78}\nGRAND SUMMARY (43 RT tail hours, 2023-2025)")
    allr = [r for rows in grand.values() for r in rows]
    n = len(allr)
    p(f"  CF-A (systemic gain restored) crosses:  {sum(r[2] for r in allr)}/{n}")
    p(f"  CF-B (any within-day, upper bound):     {sum(r[3] for r in allr)}/{n}")
    p(f"  CF-C (event-day level alone):           {sum(r[4] for r in allr)}/{n}")
    p(f"  JOINT-ONLY:                             "
      f"{sum(r[5] == 'JOINT-ONLY' for r in allr)}/{n}")
    p(f"  DA-visible:                             {sum(r[1] for r in allr)}/{n}")

    rec = REPO / "results/calibration/PROBE-neiso75-c3c-decomposition-2026-08-02.txt"
    rec.write_text("\n".join(out) + "\n")
    print(f"\n[record written: {rec.relative_to(REPO)}]")
    return 0


def gate_band(actual: int) -> str:
    """Human-readable C3c pass band for an actual RT count."""
    if actual < TAIL_SMALL:
        return f"|model-{actual}| <= {TAIL_SMALL}"
    return f"[{TAIL_LO * actual:.0f}, {TAIL_HI * actual:.0f}] h"


if __name__ == "__main__":
    sys.exit(main())
