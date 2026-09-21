"""pjm-h15 phase 0 — the COVERED coal cohort's POOLED-VINTAGE window, measured.

Zero LP. pjm-h14 repaired the UNCOVERED coal cohort (no artifact row -> a 45 %
must-run tranche held in all 8,760 h). The COVERED 29 plants still carry ONE
pooled ``online_frac``, measured on 2023-2025, applied as EVERY solve year's
commitment window -- so 2020-2022 are windowed on a share measured in years the
plants had not yet reached, and the in-window years carry the other two years'
average.

What this probe establishes, all from committed artifacts and the FROZEN
estimator (rule 23 [R-FROZEN-DERIVE]: ``derive_thermal_tranche_online_frac_by_year``
IMPORTS ``derive_thermal_tranches`` rather than restating it; nothing is
re-derived and no committed value moves):

 1. the pooled-vs-own-year gap per covered coal plant per year;
 2. the WINDOW each fraction implies against the keeper's OWN committed system
    load (``hourly/system_<year>.parquet``), which is the identical series
    ``arrays._compose_min_gen_floors`` ranks hours by;
 3. the CAMPD conduct over each window -- the D-4 statistic's own operand --
    under the pooled window and under the own-year window;
 4. the PREDICTOR'S OWN STANDING: the committed D-4 rows' ``binding_hours``
    against this probe's ``k``, so the gate below is written knowing how much
    of D-4 a pre-solve window can and cannot see (pjm-h14 correction #3).

Usage:
    python3 scripts/probes/pjm_h15_coalwindow_phase0.py \
        --by-year /tmp/claude-0/h15/by_year_PJM.csv [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data import campd  # noqa: E402
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402

POOLED = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
SPAN = REPO / "results/calibration/pjm_h14_coalmustrun_span"
TOUCH = REPO / "results/calibration/pjm_h14_coalmustrun_touchpoint"
YEARS = list(range(2020, 2026))
FORCE_ALL = 0.99  # withholding._COAL_SYNC_FORCE_ALL


def bundle_for(year: int) -> Path:
    return SPAN if year >= 2023 else TOUCH


def system_load(year: int) -> np.ndarray:
    """The keeper's own hourly system load — zonal demand summed, P1."""
    df = pd.read_parquet(bundle_for(year) / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    s = df.groupby("hour")["demand"].sum().sort_index()
    return s.to_numpy(dtype=float)


def window_hours(load: np.ndarray, frac: float) -> np.ndarray:
    """The top-k hours by system load — ``_compose_min_gen_floors``'s own rule."""
    if frac >= FORCE_ALL:
        return np.arange(len(load))
    k = int(round(frac * len(load)))
    if k <= 0:
        return np.empty(0, dtype=int)
    return np.argsort(-load, kind="stable")[:k]


def conduct(series: np.ndarray, hrs: np.ndarray) -> tuple[float, float]:
    """(median measured MW, zero-share) over ``hrs`` — the D-4 conduct operand."""
    if hrs.size == 0:
        return float("nan"), float("nan")
    v = series[hrs]
    return float(np.median(v)), float((v <= 0.0).mean())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--by-year", required=True)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    pooled = pd.read_csv(POOLED)
    pooled = pooled[(pooled.plant_group == "COAL") & (pooled.get("status", "ok") == "ok")]
    pmap: dict[int, float] = {}
    for r in pooled.itertuples(index=False):
        try:
            f = float(r.online_frac)
        except (TypeError, ValueError):
            continue
        if f == f:
            pmap[int(r.plant_code)] = f

    by = pd.read_csv(args.by_year)
    by = by[by.plant_group == "COAL"]
    omap = {
        (int(r.plant_code), int(r.year)): float(r.online_frac)
        for r in by.itertuples(index=False)
        if float(r.online_frac) == float(r.online_frac)
    }
    nameplate = {int(r.plant_code): float(r.nameplate_mw) for r in by.itertuples(index=False)}

    states = campd.states_for_iso("PJM")
    factors = dtt._parasitic_factor_map()

    rows: list[dict] = []
    for year in YEARS:
        load = system_load(year)
        df = campd.load_campd_hourly(states, [year])
        net = campd.plant_hourly_net(df, factors, year)
        for code, pf in sorted(pmap.items()):
            of = omap.get((code, year))
            if of is None:
                continue
            series = net.get(code)
            if series is None:
                continue
            series = np.asarray(series, dtype=float)[: len(load)]
            if len(series) < len(load):
                series = np.pad(series, (0, len(load) - len(series)))
            hp, ho = window_hours(load, pf), window_hours(load, of)
            mp, zp = conduct(series, hp)
            mo, zo = conduct(series, ho)
            rows.append(
                dict(
                    year=year,
                    plant=code,
                    nameplate_mw=round(nameplate.get(code, 0.0), 1),
                    pooled=round(pf, 3),
                    own=round(of, 3),
                    d_frac=round(of - pf, 3),
                    k_pooled=int(hp.size),
                    k_own=int(ho.size),
                    med_pooled=round(mp, 2),
                    zero_pooled=round(zp, 4),
                    med_own=round(mo, 2),
                    zero_own=round(zo, 4),
                    metered_twh=round(float(series.sum()) / 1e6, 4),
                )
            )
    d = pd.DataFrame(rows)
    pd.set_option("display.width", 220)

    print("### 1. The window each fraction implies, and the CAMPD conduct over it\n")
    print("    med_* = median measured plant MW over the window the fraction asserts")
    print("    (D-4's own operand; D-4 scores BINDING hours, a subset -- see section 4)\n")
    print(d.to_string(index=False))

    print("\n### 2. WHERE THE POOLED WINDOW CONVICTS AND THE OWN-YEAR WINDOW DOES NOT\n")
    flip = d[(d.med_pooled <= 0.0) & (d.med_own > 0.0)]
    hold = d[(d.med_pooled <= 0.0) & (d.med_own <= 0.0)]
    born = d[(d.med_pooled > 0.0) & (d.med_own <= 0.0)]
    print(f"    pooled-window zero-median plant-years : {int((d.med_pooled <= 0).sum())}")
    print(f"    own-year-window zero-median plant-years: {int((d.med_own <= 0).sum())}")
    print(f"    REPAIRED (zero -> positive): {len(flip)}   UNMOVED: {len(hold)}   NEW: {len(born)}")
    for nm, sub in (("REPAIRED", flip), ("UNMOVED", hold), ("NEW", born)):
        if len(sub):
            print(f"\n    {nm}:")
            print(sub[["year", "plant", "pooled", "own", "k_pooled", "k_own",
                       "med_pooled", "med_own", "zero_pooled", "zero_own"]].to_string(index=False))

    print("\n### 3. FOOTPRINT: asserted coal floor-hours, pooled vs own-year\n")
    fp = d.groupby("year").agg(
        plants=("plant", "count"),
        k_pooled=("k_pooled", "sum"),
        k_own=("k_own", "sum"),
        mean_d_frac=("d_frac", "mean"),
        max_abs_d=("d_frac", lambda s: float(np.abs(s).max())),
    )
    fp["d_hours"] = fp.k_own - fp.k_pooled
    fp["d_pct"] = (100.0 * fp.d_hours / fp.k_pooled).round(2)
    print(fp.round(4).to_string())

    print("\n### 4. THE PREDICTOR'S OWN STANDING — committed D-4 binding_hours vs this probe's k\n")
    dj = json.loads((SPAN / "legitimacy_diagnostics.json").read_text())
    d4 = [r for r in dj["diagnostics"]["D4"]["rows"]
          if r["floor"] == "coal_mustrun" and r["check"] == "unit-conduct"]
    chk = []
    for r in d4:
        code, yr = int(r["plant"]), int(r["year"])
        m = d[(d.plant == code) & (d.year == yr)]
        if m.empty:
            continue
        m = m.iloc[0]
        chk.append(dict(year=yr, plant=code, k_pooled=int(m.k_pooled),
                        d4_binding=int(r["binding_hours"]),
                        ratio=round(int(r["binding_hours"]) / max(1, int(m.k_pooled)), 3),
                        d4_median=float(r["measured_median_mw"]),
                        probe_med_pooled=float(m.med_pooled),
                        d4_verdict=r["verdict"]))
    c = pd.DataFrame(chk)
    print(c.to_string(index=False))
    over = c[c.d4_binding > c.k_pooled]
    print(f"\n    binding_hours <= k_pooled on {len(c) - len(over)}/{len(c)} committed rows "
          f"(the window is a strict SUPERSET of the binding set; {len(over)} exception(s))")
    print(f"    ratio binding/k: min {c.ratio.min():.3f} median {c.ratio.median():.3f} max {c.ratio.max():.3f}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(
            dict(rows=rows, footprint=fp.reset_index().to_dict("records"),
                 standing=chk), indent=1))
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
