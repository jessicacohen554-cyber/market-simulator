"""soco-68 phase 0 (ZERO LP): decompose SOCO's CC capability gap per plant.

After soco-67, measured CC net output still exceeds the keeper's CC_REGULAR
availability at plant-hour grain. This probe splits that excess, per plant and
hour, into two channels that different levers own (rule 19 ``[R-ONE-MECH]``):

* **(a) CAPABILITY BASIS** -- ``max(0, cems_net - pmax)``: the plant measurably
  ran above the LP's *nameplate/summer* ceiling. Owned by the pmax basis
  (summer vs winter vs nameplate, the always-on CC nameplate guard's "trusted
  bound", a ``cc_capacity_reconcile`` table).
* **(b) AVAILABILITY** -- ``max(0, min(cems_net, pmax) - avail)``: the plant ran
  inside its ceiling but the LP had derated it (outage windows, COD ramp,
  maintenance shape, temperature derate).

Inputs: the keeper's own fleet (``run_year(fleet_only=True)`` on the committed
``soco67_span`` recipe -- G-DRIFT shows the LP input bit-identical at HEAD),
the EIA-860 vintage the solve year reads (``eia860_vintage_tracks_solve_year``),
and CAMPD unit-level CEMS for the facility's *combined-cycle* units only
(``unitType`` contains "combined cycle"), gross x 0.97 -> net (the soco-67
convention). The CC nameplate-guard log lines are captured so a clipped plant
shows its pre-clip sum and its bound.

Writes ``<out>/cc_capability_<year>.csv`` and prints the per-plant table.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco68_cc_capability.py \
        --years 2023 2024 --out <dir>
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/soco67_span"
T = 8760
NET_OVER_GROSS = 0.97  # soco-67 FINDING §2 convention (CEMS gross x 0.97)
STATES = ("AL", "GA", "MS", "FL")
CC_PM = ("CT", "CA", "CS")
GUARD_RE = re.compile(
    r"CC plant (\d+) fleet pmax sum ([\d.]+) MW exceeds trusted bound ([\d.]+) MW \((\w[\w ]*);"
)


class _Grab(logging.Handler):
    """Collect every log message emitted during the fleet build."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.msgs: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.msgs.append(record.getMessage())


def build_fleet(year: int, sets: dict | None = None) -> tuple[dict, list[str]]:
    """fleet_only rebuild of one keeper year; returns (state, log messages)."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year

    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(BUNDLE), year))
    for k, v in (sets or {}).items():
        # structural flags ride the prb_overrides bag (replay_keeper docstring)
        if k in kw:
            kw[k] = v
        else:
            kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), k: v}
    clear_fleet_caches()
    grab = _Grab()
    root = logging.getLogger()
    root.addHandler(grab)
    old = root.level
    root.setLevel(logging.DEBUG)
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            st = run_year(
                year,
                meta["iso"],
                T,
                float(meta["gas_prices"][str(year)]),
                {},
                fleet_only=True,
                **kw,
            )
    finally:
        root.removeHandler(grab)
        root.setLevel(old)
    return st, grab.msgs


def eia860_cc(year: int, plants: list[int]) -> pd.DataFrame:
    """Per-plant CC nameplate / summer / winter sums from the solve-year vintage."""
    vdir = REPO / f"data/raw/eia-860/vintage_{year}"
    path = vdir / "eia860_generator_operable.parquet"
    if not path.exists():
        path = REPO / "data/raw/eia-860/eia860_generator_operable.parquet"
    g = pd.read_parquet(path)
    code = pd.to_numeric(g["Plant Code"], errors="coerce")
    g = g[code.isin(plants) & g["Prime Mover"].isin(CC_PM)].copy()
    g["Plant Code"] = pd.to_numeric(g["Plant Code"]).astype(int)
    for c in (
        "Nameplate Capacity (MW)",
        "Summer Capacity (MW)",
        "Winter Capacity (MW)",
    ):
        g[c] = pd.to_numeric(g[c], errors="coerce")
    g["cod"] = pd.to_numeric(
        g["Operating Year"], errors="coerce"
    ) * 100 + pd.to_numeric(g["Operating Month"], errors="coerce")
    agg = g.groupby("Plant Code").agg(
        n_gen=("Generator ID", "size"),
        nameplate=("Nameplate Capacity (MW)", "sum"),
        summer=("Summer Capacity (MW)", "sum"),
        winter=("Winter Capacity (MW)", "sum"),
        summer_nan=("Summer Capacity (MW)", lambda s: int(s.isna().sum())),
        last_cod=("cod", "max"),
        name=("Plant Name", "first"),
    )
    agg.index = agg.index.astype(int)
    agg.attrs["vintage_path"] = str(path.relative_to(REPO))
    return agg


def cems_cc_hourly(year: int, plants: set[int]) -> dict[int, np.ndarray]:
    """Hourly net MW (gross x 0.97) over each facility's combined-cycle units."""
    out: dict[int, np.ndarray] = {}
    for st in STATES:
        p = REPO / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(
            p, columns=["facilityId", "unitId", "date", "hour", "grossLoad", "unitType"]
        )
        d = d[d.facilityId.astype(int).isin(plants)]
        d = d[d.unitType.astype(str).str.lower().str.contains("combined cycle")]
        if d.empty:
            continue
        dt = pd.to_datetime(d["date"])
        d = d[~((dt.dt.month == 2) & (dt.dt.day == 29))]
        dt = pd.to_datetime(d["date"])
        doy = (dt - pd.Timestamp(year=year, month=1, day=1)).dt.days
        if year % 4 == 0:
            doy = doy - ((dt.dt.month > 2).astype(int))
        h = (doy * 24 + d["hour"].astype(int)).to_numpy()
        ok = (h >= 0) & (h < T)
        d = d.iloc[np.where(ok)[0]]
        h = h[ok]
        for fac, idx in d.groupby("facilityId").indices.items():
            arr = out.setdefault(int(fac), np.zeros(T))
            np.add.at(
                arr, h[idx], np.nan_to_num(d["grossLoad"].to_numpy(dtype=float)[idx])
            )
    return {k: np.nan_to_num(v) * NET_OVER_GROSS for k, v in out.items()}


def main() -> None:
    """Run the per-plant decomposition for each requested year."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tag", default="", help="suffix for output files (ablation arms)")
    ap.add_argument(
        "--set",
        action="append",
        default=[],
        help="k=v ScenarioConfig override (json value)",
    )
    a = ap.parse_args()
    sets = {k: json.loads(v) for k, v in (x.split("=", 1) for x in a.set)}
    a.out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for y in a.years:
        st, msgs = build_fleet(y, sets)
        fa = st["fleet_arrays"]
        cls = np.asarray(fa.plant_group).astype(str)
        plant = np.asarray(fa.plant_code).astype(int)
        pmax = np.asarray(fa.pmax, float)
        av = np.asarray(fa.availability, float)
        if av.ndim == 1:
            av = np.repeat(av[:, None], T, axis=1)
        cc = np.where(cls == "CC_REGULAR")[0]
        plants = sorted(set(plant[cc].tolist()))
        guard = {}
        for m in msgs:
            g = GUARD_RE.search(m)
            if g and "SOCO" in m:
                guard[int(g.group(1))] = (
                    float(g.group(2)),
                    float(g.group(3)),
                    g.group(4),
                )
        for m in msgs:
            if "CC plant" in m or "trusted bound" in m:
                print("  [log]", m)
        e860 = eia860_cc(y, plants)
        cems = cems_cc_hourly(y, set(plants))
        rows = []
        for p in plants:
            idx = cc[plant[cc] == p]
            pm = float(pmax[idx].sum())
            avh = (pmax[idx, None] * av[idx]).sum(axis=0)
            c = cems.get(p, np.zeros(T))
            a_basis = np.maximum(0.0, c - pm)
            b_avail = np.maximum(0.0, np.minimum(c, pm) - avh)
            on = c > 1.0
            r = {
                "plant": p,
                "name": e860.name.get(p, ""),
                "lp_pmax": pm,
                "nameplate": float(e860.nameplate.get(p, np.nan)),
                "summer": float(e860.summer.get(p, np.nan)),
                "winter": float(e860.winter.get(p, np.nan)),
                "summer_nan_rows": int(e860.summer_nan.get(p, 0)),
                "guard_presum": guard.get(p, (np.nan,))[0],
                "guard_bound": guard.get(p, (np.nan, np.nan))[1],
                "guard_kind": guard.get(p, (None, None, ""))[2],
                "cems_p95": float(np.percentile(c[on], 95)) if on.any() else 0.0,
                "cems_p999": float(np.percentile(c[on], 99.9)) if on.any() else 0.0,
                "cems_max": float(c.max()),
                "cems_twh": c.sum() / 1e6,
                "avail_twh": avh.sum() / 1e6,
                "pmax_twh": pm * T / 1e6,
                "h_above_pmax": int((c > pm + 1e-6).sum()),
                "exc_basis_twh": a_basis.sum() / 1e6,
                "exc_avail_twh": b_avail.sum() / 1e6,
            }
            r["exc_total_twh"] = r["exc_basis_twh"] + r["exc_avail_twh"]
            rows.append(r)
        df = pd.DataFrame(rows).sort_values("exc_total_twh", ascending=False)
        df.to_csv(a.out / f"cc_capability_{y}{a.tag}.csv", index=False)
        # census: class availability TWh + per-unit availability for the arm diff
        cls_av = {}
        for c in np.unique(cls):
            ii = np.where(cls == c)[0]
            cls_av[c] = float((pmax[ii, None] * av[ii]).sum() / 1e6)
        np.savez_compressed(
            a.out / f"fleet_{y}{a.tag}.npz",
            unit_ids=np.asarray(list(map(str, fa.unit_ids))),
            cls=cls,
            plant=plant,
            pmax=pmax,
            avail=(pmax[:, None] * av).astype(np.float32),
            mc=np.asarray(st["mc_base"], dtype=np.float32),
        )
        pd.set_option("display.width", 250)
        print(f"\n=== {y}  (860: {e860.attrs['vintage_path']}) ===")
        print(df.round(2).to_string(index=False))
        tot = df[["exc_basis_twh", "exc_avail_twh", "exc_total_twh"]].sum()
        print("TOTAL", tot.round(3).to_dict())
        summary[y] = {k: round(float(v), 4) for k, v in tot.items()}
        summary[y]["guard_clipped"] = {str(k): v for k, v in guard.items()}
        summary[y]["class_avail_twh"] = {k: round(v, 4) for k, v in cls_av.items()}
    (a.out / f"cc_capability_summary{a.tag}.json").write_text(
        json.dumps(summary, indent=1)
    )


if __name__ == "__main__":
    main()
