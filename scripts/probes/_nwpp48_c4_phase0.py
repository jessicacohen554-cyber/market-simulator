"""nwpp-48 phase 0: where NWPP's C4 coal-correlation miss lives. ZERO LP.

Reproduces every number in
``docs/handoffs/FINDING-nwpp-48-c4-phase0-2026-09-23.md`` from committed or
recoverable artifacts only:

* the keeper's committed ``hourly/`` sidecars
  (``results/calibration/nwpp47_gridwind_span``, rule 15 ``[R-DASHBOARD]``);
* its hash-verified shared inputs (EIA-930 benchmark, CAMPD plant-hourly),
  restored at zero LP with
  ``run_calibration_full.py --iso NWPP --restore-shared-inputs <bundle>``;
* CAMPD unit-level hourly (``data/raw/campd-unit-level/WY_<year>.parquet``);
* the per-plant ``dispatch/<year>_P1.parquet`` of the three NWPP-47 legs.
  Those are NOT on ``main`` (rule 32(d)); at this writing they were read from
  shard commits 28c30ecf / 9b490454 / 6e375b43 (provenance only, rule 33(d))
  into ``--legs`` with ``git show <sha>:results/calibration/
  nwpp47_gridwind_<y>/dispatch/<y>_P1.parquet``. Sections that need them are
  skipped when ``--legs`` is absent.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp48_c4_phase0.py [--legs DIR]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = Path("results/calibration/nwpp47_gridwind_span")
SHARED = Path("results/calibration/_shared/NWPP")
EIA930 = SHARED / "eia930-e539ed483b64.parquet"
CAMPD = SHARED / "campd-a5fde7813755.parquet"
YEARS = (2023, 2024, 2025)
COAL = ("COAL_BIT", "COAL_PRB", "COAL_WC")
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
JIM_BRIDGER = 8066
N = 8760


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, NaN when either vector is constant."""
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _split(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (daily-mean broadcast, within-day deviation) of an hourly vector."""
    x = x[: len(x) // 24 * 24].reshape(-1, 24)
    dm = x.mean(1, keepdims=True)
    return np.repeat(dm.ravel(), 24), (x - dm).ravel()


def _hourly(df: pd.DataFrame, key: str, val: str) -> np.ndarray:
    """Sum ``val`` by ``key`` onto a zero-filled 8760 vector."""
    return df.groupby(key)[val].sum().reindex(range(N), fill_value=0).to_numpy(float)


def _e930(e: pd.DataFrame, year: int, series: str) -> np.ndarray:
    """One EIA-930 NWPP series for one year."""
    return e[(e.year == year) & (e.series == series)].sort_values("hour").mw.to_numpy(float)[:N]


def price_structure() -> None:
    """(a) Distinct P1 prices and intra-day spread, per zone-year."""
    print("\n(a) P1 price structure")
    for y in YEARS:
        s = pd.read_parquet(BUNDLE / "hourly" / f"system_{y}.parquet")
        s = s[s["pass"] == "P1"].assign(day=lambda d: d.hour // 24, pr=lambda d: d.price.round(3))
        for z, g in s.groupby("zone"):
            nd = g.groupby("day").pr.nunique()
            rng = g.groupby("day").price.agg(lambda x: x.max() - x.min())
            hod = g.assign(h=g.hour % 24).groupby("h").price.mean()
            print(f"  {y} {z:12s} distinct/yr {g.pr.nunique():4d}  days w/ intra-day var "
                  f"{int((nd > 1).sum()):3d}  mean daily range ${rng.mean():5.2f}  "
                  f"mean-HOD amplitude ${hod.max() - hod.min():5.2f}")


def decomposition_and_ceilings(e: pd.DataFrame) -> None:
    """(c) r split into daily/intra terms and counterfactual r ceilings."""
    print("\n(c) coal r decomposition vs EIA-930 and counterfactual ceilings")
    print("  year  r   r_daily r_intra | actual var share daily/intra | "
          "r if intra perfect @model amp / @actual amp | r if daily perfect")
    for y in YEARS:
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
        m = _hourly(ch[(ch["pass"] == "P1") & ch.klass.isin(COAL)], "hour", "mw")
        a = _e930(e, y, "coal")
        md, mi = _split(m)
        ad, ai = _split(a)
        k = mi.std() / ai.std()
        print(f"  {y} {_r(m, a):.3f} {_r(md[::24], ad[::24]):.3f} {_r(mi, ai):.3f} | "
              f"{ad.var() / (ad.var() + ai.var()):.2f}/{ai.var() / (ad.var() + ai.var()):.2f} | "
              f"{_r(md + ai * k, a):.3f} / {_r(md + ai, a):.3f} | "
              f"{_r(ad * m.mean() / a.mean() + mi, a):.3f}")


def swing_absorption(e: pd.DataFrame) -> None:
    """Who carries the intra-day net-load swing, model vs EIA-930."""
    print("\n(b') intra-day sd (MW) and r_intra with EIA-930 net load (net_gen - wind - solar)")
    for y in YEARS:
        nl = _split(_e930(e, y, "net_gen") - _e930(e, y, "wind") - _e930(e, y, "solar"))[1]
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        sy = pd.read_parquet(BUNDLE / "hourly" / f"system_{y}.parquet")
        sy = sy[sy["pass"] == "P1"]
        row = [f"  {y} netload sd {nl.std():5.0f}"]
        for lab, ks, ser in (("hydro", ("hydro",), "hydro"), ("coal", COAL, "coal"), ("gas", GAS, "gas")):
            mi = _split(_hourly(ch[ch.klass.isin(ks)], "hour", "mw"))[1]
            ai = _split(_e930(e, y, ser))[1]
            row.append(f"{lab} sd {ai.std():5.0f}/{mi.std():5.0f} r {_r(ai, nl):.2f}/{_r(mi, nl):.2f}")
        for z in ("NWPP-EAST", "NWPP-NW"):
            p = sy[sy.zone == z].sort_values("hour").price.to_numpy()[:N]
            row.append(f"{z} lmp r {_r(_split(p)[1], nl):.2f}")
        print(" | ".join(row) + "   (act/mdl)")


def plant_attribution(e: pd.DataFrame, campd: pd.DataFrame, legs: Path) -> None:
    """(d) per-plant and per-zone model vs CAMPD, and single-plant substitution gains."""
    print("\n(d) per-plant: model vs CAMPD, and r gain from substituting one plant's "
          "CAMPD shape at the model's own energy")
    for y in YEARS:
        d = pd.read_parquet(legs / f"{y}_P1.parquet", columns=["unit_id", "plant_code", "klass", "zone", "hour", "mw"])
        d = d[d.klass.isin(COAL)]
        a = _e930(e, y, "coal")
        m = _hourly(d, "hour", "mw")
        base = _r(m, a)
        cy = campd[campd.year == y]
        rows = []
        for (p, z), g in d.groupby(["plant_code", "zone"], observed=True):
            mp = _hourly(g, "hour", "mw")
            cp = cy[cy.plant_id == p].set_index("hour").net_mw.reindex(range(N), fill_value=0).to_numpy(float).clip(0)
            if cp.sum() <= 0 or mp.sum() <= 0:
                continue
            resp = _hourly(g[g.unit_id.str.contains("_econ|_peak")], "hour", "mw")
            rows.append(dict(
                plant=p, zone=z, mdl_twh=mp.sum() / 1e6, act_twh=cp.sum() / 1e6,
                r=_r(mp, cp), r_intra=_r(_split(mp)[1], _split(cp)[1]),
                sd_intra=f"{_split(mp)[1].std():.0f}/{_split(cp)[1].std():.0f}",
                r_resp_bands=_r(resp, cp), gain=_r(m - mp + cp * mp.sum() / cp.sum(), a) - base,
            ))
        t = pd.DataFrame(rows).sort_values("gain", ascending=False)
        print(f"  {y}  base r {base:.3f}")
        print(t.round(3).to_string(index=False))
        u = pd.read_parquet(Path(f"data/raw/campd-unit-level/WY_{y}.parquet"))
        u = u[u.facilityId.astype(int) == JIM_BRIDGER].copy()
        u["h"] = ((pd.to_datetime(u.date) + pd.to_timedelta(u.hour, "h") - pd.Timestamp(f"{y}-01-01"))
                  / pd.Timedelta("1h")).astype(int)
        coal_units = sorted(k for k, v in u.groupby("unitId").primaryFuelInfo.agg(
            lambda s: s.mode().iloc[0]).items() if "Coal" in str(v))
        cu = _hourly(u[u.unitId.isin(coal_units)], "h", "grossLoad")
        jb = _hourly(d[d.plant_code == JIM_BRIDGER], "hour", "mw")
        print(f"  Jim Bridger coal units {coal_units}: CAMPD gross {cu.sum() / 1e6:.2f} TWh vs "
              f"model coal {jb.sum() / 1e6:.2f}; r if JB := coal-unit shape @model energy "
              f"{_r(m - jb + cu * jb.sum() / cu.sum(), a):.3f}")


def main() -> None:
    """Run every zero-LP section."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", type=Path, default=None,
                    help="dir holding <year>_P1.parquet from the NWPP-47 legs")
    args = ap.parse_args()
    e = pd.read_parquet(EIA930)
    price_structure()
    decomposition_and_ceilings(e)
    swing_absorption(e)
    if args.legs is not None:
        plant_attribution(e, pd.read_parquet(CAMPD), args.legs)
    else:
        print("\n(d) skipped: pass --legs (see module docstring)")


if __name__ == "__main__":
    main()
