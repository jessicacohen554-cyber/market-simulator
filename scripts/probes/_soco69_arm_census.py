"""SOCO-69 arm census (ZERO LP): fleet_only rebuilds, keeper recipe vs + coal_mustrun_requires_measured_row.

Rebuilds each year's LP fleet on the soco-68 keeper's own recipe (``replay_keeper``'s
``run_year_kwargs`` + ``derived_run_year_inputs``) twice -- as recorded, and with
``coal_mustrun_requires_measured_row=True`` on the generic ScenarioConfig override
channel -- and differences every LP-visible array per unit. Never solves (rule 32
``[R-SHARD]`` (a)).

Usage::

    PYTHONPATH=.:src:scripts python scripts/probes/_soco69_arm_census.py [years...]
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BUNDLE = _ROOT / "results/calibration/soco68_span"
FIELD = "coal_mustrun_requires_measured_row"


def build(year: int, arm: bool) -> dict:
    """fleet_only rebuild on the keeper recipe, optionally with the arm field on."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(BUNDLE), year))
    if arm:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"][FIELD] = True
    clear_fleet_caches()
    log = io.StringIO()
    with contextlib.redirect_stderr(log):
        st = run_year(year, meta["iso"], 8760, float(meta["gas_prices"][str(year)]), {},
                      fleet_only=True, **kw)
    fa = st["fleet_arrays"]
    mg = np.asarray(fa.min_gen)
    av = np.asarray(fa.availability)
    pm = np.asarray(fa.pmax, dtype=float)
    return dict(
        ids=[str(u) for u in fa.unit_ids],
        group=[str(g) for g in fa.plant_group],
        plant=np.asarray(fa.plant_code, dtype=int),
        pmax=pm,
        min_gen_twh=(mg.sum(axis=1) if mg.ndim == 2 else mg * 8760) / 1e6,
        avail_twh=((av * pm[:, None]).sum(axis=1) if av.ndim == 2 else av * pm * 8760) / 1e6,
        mc=np.asarray(st["mc_base"], dtype=float).reshape(len(fa.unit_ids), -1).mean(axis=1),
    )


def main() -> None:
    """Print per-year moved units and class-level availability/min-gen deltas."""
    years = [int(a) for a in sys.argv[1:]] or [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    pd.set_option("display.width", 250)
    for y in years:
        k, a = build(y, False), build(y, True)
        ka = pd.DataFrame({key: k[key] for key in ("ids", "group", "plant", "pmax", "min_gen_twh", "avail_twh", "mc")})
        aa = pd.DataFrame({key: a[key] for key in ("ids", "group", "plant", "pmax", "min_gen_twh", "avail_twh", "mc")})
        m = ka.merge(aa, on="ids", how="outer", suffixes=("_k", "_a"), indicator=True)
        only = m[m._merge != "both"]
        b = m[m._merge == "both"].copy()
        num = ("pmax", "min_gen_twh", "avail_twh", "mc")
        moved = b[np.logical_or.reduce([~np.isclose(b[f"{c}_k"], b[f"{c}_a"], atol=1e-9) for c in num])]
        print(f"\n===== {y}: units keeper {len(ka)} arm {len(aa)}  only-in-one {len(only)}  moved {len(moved)}")
        if len(only):
            print(only[["ids", "_merge", "pmax_k", "pmax_a", "avail_twh_k", "avail_twh_a"]].round(3).to_string(index=False))
        if len(moved):
            print(moved[["ids", "pmax_k", "pmax_a", "min_gen_twh_k", "min_gen_twh_a", "avail_twh_k", "avail_twh_a",
                         "mc_k", "mc_a"]].round(3).to_string(index=False))
        cls = lambda d, s: d.groupby(f"group_{s}")[[f"avail_twh_{s}", f"min_gen_twh_{s}"]].sum()  # noqa: E731
        c = cls(m.dropna(subset=["group_k"]), "k").join(cls(m.dropna(subset=["group_a"]), "a"), how="outer")
        c.columns = ["avail_k", "mingen_k", "avail_a", "mingen_a"]
        c["d_avail"] = c.avail_a - c.avail_k
        c["d_mingen"] = c.mingen_a - c.mingen_k
        print(c[(c.d_avail.abs() > 1e-6) | (c.d_mingen.abs() > 1e-6)].round(3).to_string())


if __name__ == "__main__":
    main()
