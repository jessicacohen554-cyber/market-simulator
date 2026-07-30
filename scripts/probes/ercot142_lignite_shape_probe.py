"""ERCOT-142 Phase 1 — diagnose the C7 2023 COAL_LIGNITE diurnal-shape miss.

No LP, no solve, no parameter touched. Reads only committed artifacts:

* the MEASURED side — the CAMPD bench
  (``frontend/data/backcast/bench/ERCOT/<year>.json.gz``), the same measured
  per-plant hourly series D-1 scores against;
* the MODEL side — the keeper bundle's committed class hourly sidecar
  (``hourly/class_hourly_<year>.parquet``, P1 rows).

The C7 failure under test is the keeper's own committed
``legitimacy_diagnostics.json`` row **2023 COAL_LIGNITE profile r 0.769 <
0.80** (``cv_ratio`` 0.535 clears its 0.50 gate; 2024/2025 pass both legs).

What it prints, in order:

1. **Basis check** — the class-aggregate reproduction of D-1's ``profile_r``
   against the committed artifact value, so every later number is known to sit
   on the gate's own basis (or the divergence is stated).
2. **The annual hour-of-day profiles**, model vs measured, normalised.
3. **The seasonal decomposition** — per-season ``profile_r`` and off-peak CV,
   which is where the named "coal seasonal split" companion is tested: if one
   annual basis is carrying two regimes, the season-wise correlations separate.
4. **Measured lignite unit conduct** — per-plant hour-of-day capacity factor by
   season, the driver evidence any mechanism proposal must cite (rule 17
   ``[R-FLOOR-WINDOW]`` (a)).

Usage::

    python scripts/probes/ercot142_lignite_shape_probe.py \
        --bundle results/calibration/ercot140_coal_peak_arm

Rule notes: this is measurement only (rules 13/14 ``[R-MEASURED]`` — measured
conduct read as driver evidence, never fed back as an answer key), ERCOT-scoped
(rule 25 ``[R-ISO-SCOPE]``), and touches training years 2023-2025 only
(rule 22 ``[R-HOLDOUT]``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.legitimacy_diagnostics import (  # noqa: E402
    D1_OFFPEAK_LAST_HOUR,
    d1_shape_metrics,
    load_bench,
)

KLASS = "COAL_LIGNITE"
YEARS = (2023, 2024, 2025)

# Meteorological seasons on hour-of-year indices. ERCOT's coal duty splits on
# the summer peak season (ERCOT's own ORDC/peak-season convention is Jun-Sep);
# the four-way split is reported so the season boundary is read off the data
# rather than assumed.
SEASONS = {
    "winter": (12, 1, 2),
    "spring": (3, 4, 5),
    "summer": (6, 7, 8),
    "fall": (9, 10, 11),
}


def hour_months(year: int) -> np.ndarray:
    """Return the calendar month (1-12) of each hour-of-year index."""
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return idx.month.to_numpy()


def profile(x: np.ndarray) -> np.ndarray:
    """Hour-of-day mean profile (24 points) of an hourly series."""
    n = (x.size // 24) * 24
    return x[:n].reshape(-1, 24).mean(axis=0)


def offpeak_cv(prof: np.ndarray) -> float:
    """CV of the profile over off-peak hours h0-D1_OFFPEAK_LAST_HOUR."""
    off = prof[: D1_OFFPEAK_LAST_HOUR + 1]
    m = float(off.mean())
    return float(off.std() / m) if m > 1e-9 else 0.0


def corr(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r between two profiles; 0.0 when either is constant."""
    if a.std() <= 0.0 or b.std() <= 0.0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def measured_lignite(repo: Path, year: int) -> dict[str, np.ndarray]:
    """Return {plant key: measured hourly MW} for the CAMPD lignite plants."""
    bench = load_bench(repo, "ERCOT", year)
    return {
        pid: np.asarray(p["mw"], dtype=float)
        for pid, p in bench.items()
        if p.get("group") == KLASS
    }


def measured_npl(repo: Path, year: int) -> dict[str, float]:
    """Return {plant key: nameplate MW} for the CAMPD lignite plants."""
    bench = load_bench(repo, "ERCOT", year)
    return {
        pid: float(p.get("npl") or 0.0)
        for pid, p in bench.items()
        if p.get("group") == KLASS
    }


def model_lignite(bundle: Path, year: int) -> np.ndarray:
    """Return the keeper's P1 COAL_LIGNITE class-total hourly MW."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    df = pd.read_parquet(path)
    sub = df[(df["klass"] == KLASS) & (df["pass"] == "P1")]
    return (
        sub.sort_values("hour")
        .groupby("hour", observed=True)["mw"]
        .sum()
        .to_numpy(dtype=float)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        default="results/calibration/ercot140_coal_peak_arm",
        help="keeper bundle directory (committed slim bundle is enough)",
    )
    args = ap.parse_args()
    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle

    print("=" * 78)
    print("ERCOT-142 Phase 1 — COAL_LIGNITE diurnal shape (measurement only)")
    print(f"bundle: {bundle}")
    print("=" * 78)

    # ---------------------------------------------------------------- basis
    print("\n[1] BASIS CHECK — class-aggregate reproduction of D-1 profile_r")
    print("    (committed artifact: 2023 0.769 / 2024 0.973 / 2025 0.964)")
    print(f"    {'year':<6}{'r(class-agg)':>14}{'cv_ratio':>10}"
          f"{'model_cv':>10}{'actual_cv':>11}")
    series = {}
    for year in YEARS:
        meas = measured_lignite(REPO, year)
        act = np.sum(list(meas.values()), axis=0)
        mod = model_lignite(bundle, year)
        n = min(mod.size, act.size)
        mod, act = mod[:n], act[:n]
        series[year] = (mod, act)
        r, cv_m, cv_a = d1_shape_metrics(mod, act)
        ratio = cv_m / cv_a if cv_a > 1e-9 else float("nan")
        print(f"    {year:<6}{r:>14.3f}{ratio:>10.3f}{cv_m:>10.3f}{cv_a:>11.3f}")
    print("    NOTE: D-1 pairs PER PLANT against the bench then aggregates;")
    print("    this is the class aggregate. A close match means the miss is a")
    print("    class-shape property, not a pairing artifact.")

    # ------------------------------------------------------- annual profile
    print("\n[2] ANNUAL HOUR-OF-DAY PROFILE, model vs measured (share of daily mean)")
    for year in YEARS:
        mod, act = series[year]
        pm, pa = profile(mod), profile(act)
        pmn, pan = pm / pm.mean(), pa / pa.mean()
        print(f"\n    --- {year} (model mean {pm.mean():,.0f} MW / "
              f"measured {pa.mean():,.0f} MW) ---")
        print("    h  " + " ".join(f"{h:>5}" for h in range(24)))
        print("    mod" + " ".join(f"{v:>5.2f}" for v in pmn))
        print("    act" + " ".join(f"{v:>5.2f}" for v in pan))
        print("    dif" + " ".join(f"{v:>5.2f}" for v in (pmn - pan)))

    # ------------------------------------------------------ seasonal split
    print("\n[3] SEASONAL DECOMPOSITION — is one annual basis carrying two regimes?")
    for year in YEARS:
        mod, act = series[year]
        months = hour_months(year)[: mod.size]
        print(f"\n    --- {year} ---")
        print(f"    {'season':<9}{'r':>8}{'cv_ratio':>10}{'mod_cv':>9}"
              f"{'act_cv':>9}{'mod_MW':>10}{'act_MW':>10}{'m/a':>7}")
        for name, mths in SEASONS.items():
            sel = np.isin(months, mths)
            # Whole days only, so the hour-of-day profile is balanced.
            m_s, a_s = mod[sel], act[sel]
            k = (m_s.size // 24) * 24
            if k == 0:
                continue
            pm, pa = profile(m_s[:k]), profile(a_s[:k])
            r = corr(pm, pa)
            cvm, cva = offpeak_cv(pm), offpeak_cv(pa)
            ratio = cvm / cva if cva > 1e-9 else float("nan")
            print(f"    {name:<9}{r:>8.3f}{ratio:>10.3f}{cvm:>9.3f}"
                  f"{cva:>9.3f}{pm.mean():>10,.0f}{pa.mean():>10,.0f}"
                  f"{pm.mean() / max(pa.mean(), 1e-9):>7.2f}")

    # ------------------------------------------- measured unit conduct (CF)
    print("\n[4] MEASURED CAMPD LIGNITE UNIT CONDUCT — hour-of-day CF by season")
    print("    (driver evidence; the model is not involved in this block)")
    for year in YEARS:
        meas = measured_lignite(REPO, year)
        npl = measured_npl(REPO, year)
        months = hour_months(year)
        print(f"\n    --- {year} ---")
        for pid in sorted(meas):
            mw = meas[pid]
            cap = npl.get(pid, 0.0)
            if cap <= 0:
                continue
            m = months[: mw.size]
            print(f"    plant {pid} (npl {cap:,.0f} MW)")
            for name, mths in SEASONS.items():
                sel = np.isin(m, mths)
                k = (mw[sel].size // 24) * 24
                if k == 0:
                    continue
                pcf = profile(mw[sel][:k]) / cap
                print(f"      {name:<7}" + " ".join(f"{v:>4.2f}" for v in pcf))

    # The feasibility blocks below are the ex-ante falsifiers: they bound what
    # ANY mechanism in this class could buy, before a solve is spent.
    uniform_reshape_feasibility(bundle)
    price_keyed_feasibility(bundle)
    fine_sweep(bundle)
    print("\n" + "=" * 78)
    return 0




# ---------------------------------------------------------------------------
# Phase 1b — the uniform-driver feasibility test (no LP, no parameter change)
# ---------------------------------------------------------------------------
#
# Established above: the C7 miss is ONE cell (2023 COAL_LIGNITE profile_r
# 0.769 < 0.80) and it is carried by ONE plant, Oak Grove (6180, 70 % of
# lignite nameplate), whose MEASURED conduct two-shifts between its 0.45
# min-load floor and ~0.88 CF in summer/fall 2023 and runs FLAT in 2024-2025
# (measured day-minus-night CF gap: 0.144/0.248 in summer/fall 2023 vs
# <=0.072 and ~0.00 in 2024/2025).
#
# Any admissible mechanism (rule 13 [R-MEASURED]) keys off a driver that
# regenerates for a forward year. A driver cannot be "the year is 2023" — that
# is an answer key with no forward analogue. So an admissible mechanism applies
# its response UNIFORMLY across the three training years. This function tests
# whether ANY such uniform mechanism can clear the gate: it moves Oak Grove's
# energy from night toward day with one shared amplitude in all three years
# (energy-preserving per plant-year, so C1 volume is untouched by construction)
# and reports every year's class profile_r.
#
# This is a test of the MECHANISM CLASS, not a fit: no amplitude is adopted and
# nothing is written back. It is the ex-ante falsifier for the whole lane.


def uniform_reshape_feasibility(bundle: Path) -> None:
    """Sweep a uniform night->day reshaping of Oak Grove; print class D-1 r."""
    import json

    from scripts.legitimacy_diagnostics import load_payload_plants

    sidecar = json.loads(
        (
            REPO
            / "frontend/data/backcast/registry"
            / "2026-07-30-ercot140-coal-peak-offer.json"
        ).read_text()
    )
    print("\n[5] UNIFORM-DRIVER FEASIBILITY — can one shared amplitude clear 2023")
    print("    without breaking 2024/2025? (energy-preserving; no LP, nothing kept)")
    print("    gate: profile_r >= 0.80   |   keeper: 0.769 / 0.973 / 0.964")
    print(f"\n    {'alpha':>7}" + "".join(f"{y:>12}" for y in YEARS)
          + f"{'all pass?':>11}")

    per_year = {}
    for year in YEARS:
        bench = load_bench(REPO, "ERCOT", year)
        pp = load_payload_plants(REPO, sidecar, year, bench)
        lig = {p for p, v in bench.items() if v.get("group") == KLASS}
        act = np.sum(
            [np.asarray(bench[p]["mw"], dtype=float)[:8760] for p in lig], axis=0
        )
        og = pp["6180"][:8760].copy()
        rest = np.sum(
            [pp[p][:8760] for p in lig if p != "6180" and p in pp], axis=0
        )
        npl = bench["6180"]["npl"]
        hod = pd.date_range(f"{year}-01-01", periods=8760, freq="h").hour.to_numpy()
        per_year[year] = (og, rest, act, npl, hod)

    for alpha in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
        rs, ok = [], True
        for year in YEARS:
            og, rest, act, npl, hod = per_year[year]
            floor = 0.45 * npl  # the plant's own measured min-load level
            night = hod <= 8
            day = (hod >= 10) & (hod <= 22)
            new = og.copy()
            # Back the plant down toward its own measured floor at night...
            cut = alpha * np.maximum(og[night] - floor, 0.0)
            new[night] = og[night] - cut
            # ...and return exactly that energy to the day hours, capped at
            # nameplate so the reshaping stays physical.
            if day.sum() > 0 and cut.sum() > 0:
                room = np.maximum(npl - og[day], 0.0)
                if room.sum() > 0:
                    new[day] = og[day] + room * (cut.sum() / room.sum())
            mod = new + rest
            r, _, _ = d1_shape_metrics(mod, act[: mod.size])
            rs.append(r)
            if r < 0.80:
                ok = False
        print(f"    {alpha:>7.2f}" + "".join(f"{r:>12.3f}" for r in rs)
              + f"{('YES' if ok else 'no'):>11}")
    print("\n    Reading: 2023 needs a LARGE uniform backdown to clear 0.80; the")
    print("    same amplitude is applied to 2024/2025, whose measured plants do")
    print("    NOT two-shift, so watch whether those two fall through the gate.")


def price_keyed_feasibility(bundle: Path) -> None:
    """The FAIR feasibility test: a price-keyed, forward-native backdown.

    The fixed night-window reshaping in :func:`uniform_reshape_feasibility`
    asserts a clock-hour window, which rule 17 ``[R-FLOOR-WINDOW]`` would
    reject on its own. The admissible form of this mechanism is *economic*:
    an online lignite unit backs toward its own measured min-load in the
    cheapest hours of each day and loads up in the dearest — keyed to the
    model's OWN hourly zonal price, so it regenerates in any forecast year and
    responds to changed conditions (rule 13 ``[R-MEASURED]``).

    This sweeps the depth of that response with ONE shared parameter across
    2023-2025 (an admissible driver cannot know which year it is) and reports
    every year's class ``profile_r``. Energy-preserving per plant-year, so C1
    volume is untouched by construction. Nothing is adopted or written back.
    """
    import json

    from scripts.legitimacy_diagnostics import load_payload_plants

    sidecar = json.loads(
        (
            REPO
            / "frontend/data/backcast/registry"
            / "2026-07-30-ercot140-coal-peak-offer.json"
        ).read_text()
    )
    print("\n[6] PRICE-KEYED FEASIBILITY — the forward-native form of the lever")
    print("    (back Oak Grove toward its 0.45 floor in the k cheapest hours of")
    print("     each day by the model's OWN North-zone price; energy-preserving)")
    print("    gate: profile_r >= 0.80   |   keeper: 0.769 / 0.973 / 0.964")

    per_year = {}
    for year in YEARS:
        bench = load_bench(REPO, "ERCOT", year)
        pp = load_payload_plants(REPO, sidecar, year, bench)
        lig = {p for p, v in bench.items() if v.get("group") == KLASS}
        act = np.sum(
            [np.asarray(bench[p]["mw"], dtype=float)[:8760] for p in lig], axis=0
        )
        og = pp["6180"][:8760]
        rest = np.sum([pp[p][:8760] for p in lig if p != "6180" and p in pp], axis=0)
        sysdf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        price = (
            sysdf[sysdf["zone"] == bench["6180"]["zone"]]
            .sort_values("hour")["price"]
            .to_numpy(dtype=float)[:8760]
        )
        per_year[year] = (og, rest, act, bench["6180"]["npl"], price)

    print(f"\n    {'k_cheap_h':>10}{'depth':>7}" + "".join(f"{y:>10}" for y in YEARS)
          + f"{'all pass?':>11}")
    for k_cheap in (4, 6, 8, 10):
        for depth in (0.25, 0.5, 1.0):
            rs, ok = [], True
            for year in YEARS:
                og, rest, act, npl, price = per_year[year]
                floor = 0.45 * npl
                new = og.copy()
                nd = og.size // 24
                p_d = price[: nd * 24].reshape(nd, 24)
                o_d = new[: nd * 24].reshape(nd, 24).copy()
                order = np.argsort(p_d, axis=1)
                for d in range(nd):
                    cheap = order[d, :k_cheap]
                    dear = order[d, k_cheap:]
                    cut = depth * np.maximum(o_d[d, cheap] - floor, 0.0)
                    o_d[d, cheap] -= cut
                    room = np.maximum(npl - o_d[d, dear], 0.0)
                    if room.sum() > 0 and cut.sum() > 0:
                        o_d[d, dear] += room * (cut.sum() / room.sum())
                new[: nd * 24] = o_d.reshape(-1)
                mod = new + rest
                r, _, _ = d1_shape_metrics(mod, act[: mod.size])
                rs.append(r)
                if r < 0.80:
                    ok = False
            print(f"    {k_cheap:>10}{depth:>7.2f}"
                  + "".join(f"{r:>10.3f}" for r in rs)
                  + f"{('YES' if ok else 'no'):>11}")


def fine_sweep(bundle: Path) -> None:
    """Fine low-end sweep of the fixed-window amplitude (is there a window?)."""
    import json

    from scripts.legitimacy_diagnostics import load_payload_plants

    sidecar = json.loads(
        (
            REPO
            / "frontend/data/backcast/registry"
            / "2026-07-30-ercot140-coal-peak-offer.json"
        ).read_text()
    )
    print("\n[7] FINE LOW-END SWEEP — is there ANY feasible amplitude window?")
    per_year = {}
    for year in YEARS:
        bench = load_bench(REPO, "ERCOT", year)
        pp = load_payload_plants(REPO, sidecar, year, bench)
        lig = {p for p, v in bench.items() if v.get("group") == KLASS}
        act = np.sum(
            [np.asarray(bench[p]["mw"], dtype=float)[:8760] for p in lig], axis=0
        )
        hod = pd.date_range(f"{year}-01-01", periods=8760, freq="h").hour.to_numpy()
        per_year[year] = (
            pp["6180"][:8760],
            np.sum([pp[p][:8760] for p in lig if p != "6180" and p in pp], axis=0),
            act,
            bench["6180"]["npl"],
            hod,
        )
    print(f"    {'alpha':>7}" + "".join(f"{y:>10}" for y in YEARS) + f"{'all?':>7}")
    for alpha in (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15):
        rs, ok = [], True
        for year in YEARS:
            og, rest, act, npl, hod = per_year[year]
            floor = 0.45 * npl
            night, day = hod <= 8, (hod >= 10) & (hod <= 22)
            new = og.copy()
            cut = alpha * np.maximum(og[night] - floor, 0.0)
            new[night] = og[night] - cut
            room = np.maximum(npl - og[day], 0.0)
            if room.sum() > 0 and cut.sum() > 0:
                new[day] = og[day] + room * (cut.sum() / room.sum())
            r, _, _ = d1_shape_metrics(new + rest, act[: og.size])
            rs.append(r)
            if r < 0.80:
                ok = False
        print(f"    {alpha:>7.2f}" + "".join(f"{r:>10.3f}" for r in rs)
              + f"{('YES' if ok else 'no'):>7}")


if __name__ == "__main__":
    raise SystemExit(main())
