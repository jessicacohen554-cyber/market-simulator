"""soco-86 zero-LP census: does ``mustrun_layup_window_mask`` move SOCO's must-run floors?

Rule 32 ``[R-SHARD]`` (a): never solves. Two ``fleet_only`` rebuilds per year on the
incumbent keeper's OWN recipe (``results/calibration/soco93_span`` through
``replay_keeper.run_year_kwargs``, the sanctioned reconstruction): the keeper as
recorded, and the keeper plus ``mustrun_layup_window_mask=True`` routed through the
same ``coal_prb_sigmoid_overrides`` bag every soco-83/85 structural flag rides.
Reports, per year, whether ``min_gen`` / ``availability`` / ``pmax`` / ``mc_base``
differ for any unit, and the floor TWh of the three soco-83 ST_GAS floor plants
(Gaston 26, Yates 728, Watson 2049).

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco86_layup_census.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(_ROOT / "scripts"), str(_ROOT / "src"), str(_ROOT)]

SPAN = (
    _ROOT / "results/calibration/soco93_span"
)  # repointed soco-93 (rule 35 prune of soco92_span)
FLOOR_PLANTS = (26, 728, 2049)
T = 8760


def rebuild(year: int, mask: bool) -> dict:
    """``fleet_only`` rebuild of the keeper recipe, optionally with the lay-up mask armed."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = copy.deepcopy(json.loads((SPAN / "meta.json").read_text()))
    if mask:
        meta["coal_prb_sigmoid_overrides"]["mustrun_layup_window_mask"] = True
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    clear_fleet_caches()
    log = io.StringIO()
    with contextlib.redirect_stderr(log), contextlib.redirect_stdout(io.StringIO()):
        import logging

        h = logging.StreamHandler(log)
        logging.getLogger().addHandler(h)
        logging.getLogger().setLevel(logging.INFO)
        try:
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
            logging.getLogger().removeHandler(h)
    fa = st["fleet_arrays"]
    armed = [
        ln
        for ln in log.getvalue().splitlines()
        if "mustrun_layup_window_mask ARMED" in ln
    ]
    return dict(
        ids=list(map(str, fa.unit_ids)),
        plant=np.asarray(fa.plant_code),
        pmax=np.asarray(fa.pmax, float),
        mc=np.asarray(st["mc_base"], float),
        min_gen=np.asarray(fa.min_gen, float),
        avail=np.asarray(fa.availability, float),
        armed=armed,
    )


def _mg(r: dict) -> np.ndarray:
    """(units, T) min_gen, broadcasting a 1-D floor over the year."""
    mg = r["min_gen"]
    return mg if mg.ndim == 2 else np.repeat(mg[:, None], T, 1)


def main() -> None:
    """Print the per-year keeper-vs-mask array diff and the floor-plant TWh."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    a = ap.parse_args()
    for y in a.years:
        k, m = rebuild(y, False), rebuild(y, True)
        same_ids = k["ids"] == m["ids"]
        diffs = {
            f: (not same_ids) or not np.array_equal(k[f], m[f])
            for f in ("pmax", "mc", "min_gen", "avail")
        }
        fk, fm = _mg(k), _mg(m)
        moved = [
            u
            for i, u in enumerate(k["ids"])
            if same_ids and not np.array_equal(fk[i], fm[i])
        ]
        fp = {
            p: (fk[k["plant"] == p].sum() / 1e6, fm[m["plant"] == p].sum() / 1e6)
            for p in FLOOR_PLANTS
        }
        print(
            f"{y}: units {len(k['ids'])}; array differs {diffs}; floor rows moved {len(moved)} {moved[:8]}"
        )
        print(f"      armed log: {m['armed'][:1]}")
        print(
            "      floor TWh keeper->mask "
            + ", ".join(f"{p}: {a_:.3f}->{b_:.3f}" for p, (a_, b_) in fp.items())
        )


if __name__ == "__main__" and not {"--offline", "--excess"} & set(sys.argv):
    main()


#: CEMS state per floor plant; boiler units only (the model's ST_GAS row — CTs excluded).
STATE = {26: "AL", 728: "GA", 2049: "MS"}
SPELL_BINS = ((0, 24, "<1 d"), (24, 120, "1-5 d"), (120, 10**6, ">=5 d"))


def cems_boiler_online(plant: int, year: int) -> np.ndarray:
    """8760 bool: any of the plant's gas BOILER units reports grossLoad > 0 in CEMS."""
    import pandas as pd

    d = pd.read_parquet(
        _ROOT / f"data/raw/campd-unit-level/{STATE[plant]}_{year}.parquet",
        columns=[
            "facilityId",
            "date",
            "hour",
            "grossLoad",
            "primaryFuelInfo",
            "unitType",
        ],
    )
    d = d[
        (d.facilityId.astype(str) == str(plant))
        & d.primaryFuelInfo.astype(str).str.contains("Natural Gas")
        & ~d.unitType.astype(str).str.contains("turbine", case=False)
    ]
    h = ((d.date - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + d.hour).to_numpy()
    ok = (h >= 0) & (h < T) & (np.nan_to_num(d.grossLoad.to_numpy(float)) > 0)
    on = np.zeros(T, bool)
    on[h[ok].astype(int)] = True
    return on


def spell_len(off: np.ndarray) -> np.ndarray:
    """Per hour: length of the consecutive-offline spell containing it (0 when online)."""
    out = np.zeros(T, int)
    x = np.diff(np.concatenate(([0], off.astype(int), [0])))
    for s, e in zip(np.flatnonzero(x == 1), np.flatnonzero(x == -1)):
        out[s:e] = e - s
    return out


def main_offline(years: list[int]) -> None:
    """Floor MWh in CEMS-offline hours per plant-year, split by offline-spell length."""
    print(
        "year plant floorTWh offTWh off% "
        + " ".join(b[2] for b in SPELL_BINS)
        + "  (TWh)"
    )
    tot = np.zeros(2 + len(SPELL_BINS))
    for y in years:
        k = rebuild(y, False)
        mg = (
            k["min_gen"]
            if k["min_gen"].ndim == 2
            else np.repeat(k["min_gen"][:, None], T, 1)
        )
        for p in FLOOR_PLANTS:
            rows = (k["plant"] == p) & np.array(["ST_GAS" in u for u in k["ids"]])
            f = mg[rows].sum(axis=0)
            off = ~cems_boiler_online(p, y)
            sl = spell_len(off)
            parts = [f[(sl >= lo) & (sl < hi)].sum() / 1e6 for lo, hi, _ in SPELL_BINS]
            v = np.array([f.sum() / 1e6, f[off].sum() / 1e6, *parts])
            tot += v
            print(
                f"{y} {p:5d} {v[0]:.3f} {v[1]:.3f} {100 * v[1] / max(v[0], 1e-9):5.1f} "
                + " ".join(f"{x:.3f}" for x in parts)
            )
    print(
        f"ALL        {tot[0]:.3f} {tot[1]:.3f} {100 * tot[1] / tot[0]:5.1f} "
        + " ".join(f"{x:.3f}" for x in tot[2:])
    )


if __name__ == "__main__" and "--offline" in sys.argv:
    sys.argv.remove("--offline")
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    main_offline(ap.parse_args().years)


def cems_boiler_gross(plant: int, year: int) -> np.ndarray:
    """8760 CEMS gross MW summed over the plant's gas BOILER units."""
    import pandas as pd

    d = pd.read_parquet(
        _ROOT / f"data/raw/campd-unit-level/{STATE[plant]}_{year}.parquet",
        columns=[
            "facilityId",
            "date",
            "hour",
            "grossLoad",
            "primaryFuelInfo",
            "unitType",
        ],
    )
    d = d[
        (d.facilityId.astype(str) == str(plant))
        & d.primaryFuelInfo.astype(str).str.contains("Natural Gas")
        & ~d.unitType.astype(str).str.contains("turbine", case=False)
    ]
    h = ((d.date - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + d.hour).to_numpy()
    ok = (h >= 0) & (h < T)
    out = np.zeros(T)
    np.add.at(out, h[ok].astype(int), np.nan_to_num(d.grossLoad.to_numpy(float))[ok])
    return out


def main_excess(years: list[int]) -> None:
    """Floor MWh above measured CEMS gross output: share of floor energy the meter does not carry."""
    tot = np.zeros(3)
    for y in years:
        k = rebuild(y, False)
        mg = (
            k["min_gen"]
            if k["min_gen"].ndim == 2
            else np.repeat(k["min_gen"][:, None], T, 1)
        )
        for p in FLOOR_PLANTS:
            rows = (k["plant"] == p) & np.array(["ST_GAS" in u for u in k["ids"]])
            f = mg[rows].sum(axis=0)
            g = cems_boiler_gross(p, y)
            v = np.array([f.sum(), np.clip(f - g, 0, None).sum(), (f > 0).sum()])
            tot += v
            print(
                f"{y} {p:5d} floor {v[0] / 1e6:.3f} TWh  above-meter {v[1] / 1e6:.3f} TWh ({100 * v[1] / max(v[0], 1):.1f} %)  floor-hours {int(v[2])}"
            )
    print(
        f"ALL floor {tot[0] / 1e6:.3f} above-meter {tot[1] / 1e6:.3f} ({100 * tot[1] / tot[0]:.1f} %)"
    )


if __name__ == "__main__" and "--excess" in sys.argv:
    main_excess(list(range(2019, 2026)))
