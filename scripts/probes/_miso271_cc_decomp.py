#!/usr/bin/env python3
"""miso-271 phase 0 (zero LP): decompose the CC_REGULAR move, keeper vs rmiso_b_span.

Fleet-only rebuilds (``run_year(fleet_only=True)``) of the designated keeper's
recipe (``results/calibration/rmiso_b_span``, R-MISO arm B), toggling the
R-MISO input corrections one family at a time:

* ``B``      — the keeper recipe as registered (every flag on);
* ``noV``    — ``eia860_vintage_tracks_solve_year`` off (canonical snapshot);
* ``noH``    — ``measured_{cc,coal,st}_heat_rates`` off;
* ``noG``    — ``unit_outage_short_windows_gas`` off;
* ``K``      — all R-MISO flips off (the miso-268 posture at HEAD).

Per variant, per LP unit it records ``plant_code``, ``plant_group`` (the
class the dispatch frame labels it with), ``pmax``, available MWh
(``pmax x availability`` over the year) and heat rate, and writes one parquet
per (year, variant). A plant-level diff is then a pandas groupby away.

Usage::

    uv run python scripts/probes/_miso271_cc_decomp.py --years 2023 --out-dir X
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.data.fleet.models import FUEL_TYPE_MAP  # noqa: E402
from scripts.replay_keeper import (  # noqa: E402
    config_partition_overlay,
    derived_run_year_inputs,
    run_year_kwargs,
)
from scripts.run_calibration import run_year  # noqa: E402

KEEPER = REPO / "results/calibration/rmiso_b_span"
HR = ("measured_cc_heat_rates", "measured_coal_heat_rates", "measured_st_heat_rates")
VARIANTS: dict[str, dict] = {
    "B": {},
    "noV": {"eia860_vintage_tracks_solve_year": False, "mid_vintage_exit_carry": False},
    "noH": {k: False for k in HR},
    "noG": {"unit_outage_short_windows_gas": False},
    "noW": {"wefor_residual": 0.0, "wefor_residual_groups": ["CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"]},
    "noO": {"outage_source": "statistical"},
    "K": {
        "eia860_vintage_tracks_solve_year": False,
        "mid_vintage_exit_carry": False,
        "unit_outage_short_windows_gas": False,
        "unit_partial_outage_windows": False,
        **{k: False for k in HR},
    },
}


def recipe(year: int, flips: dict) -> dict:
    """The keeper's ``run_year`` kwargs for ``year`` with ``flips`` applied."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
    kw["prb_overrides"].update(config_partition_overlay(meta, year))
    kw.update(derived_run_year_inputs(KEEPER, year))
    params = set(inspect.signature(run_year).parameters)
    from market_sim.config.scenarios import ScenarioConfig

    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    for k, v in flips.items():
        if k in params:
            kw[k] = v
        if k in fields:
            kw["prb_overrides"][k] = v
    return kw


def unit_frame(year: int, hh: float, flips: dict) -> tuple[pd.DataFrame, dict]:
    """Fleet-only rebuild; one row per LP unit."""
    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **recipe(year, flips))
    cfg, fa = st["config"], st["fleet_arrays"]
    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    avail = np.asarray(fa.availability, dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    df = pd.DataFrame(
        {
            "unit_id": list(fa.unit_ids),
            "plant_code": np.asarray(fa.plant_code),
            "group": list(fa.plant_group) if fa.plant_group is not None else "",
            "fuel": [inv.get(int(i), "?") for i in fa.fuel_type_idx],
            "pmax": pmax,
            "avail_mwh": (pmax[:, None] * avail).sum(axis=1)
            if avail.ndim == 2
            else pmax * avail * 8760,
            "heat_rate": np.asarray(fa.heat_rate, dtype=float),
            "mc_mean": np.asarray(st["mc_base"], dtype=float).reshape(len(pmax), -1).mean(axis=1)
            if st.get("mc_base") is not None
            else np.nan,
        }
    )
    flags = {
        k: getattr(cfg, k, None)
        for k in (
            "eia860_vintage_tracks_solve_year",
            "eia860_vintage_year",
            "mid_vintage_exit_carry",
            *HR,
            "unit_outage_short_windows_gas",
            "unit_partial_outage_windows",
        )
    }
    return df, flags


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2023])
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    ref = _load_reference()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for y in args.years:
        hh = _henry_hub_actual(ref, y)
        for v in args.variants:
            df, flags = unit_frame(y, hh, VARIANTS[v])
            df.to_parquet(out / f"{y}_{v}.parquet", index=False)
            cc = df[df["group"] == "CC_REGULAR"]
            print(
                json.dumps(
                    {
                        "year": y,
                        "variant": v,
                        "flags": flags,
                        "cc_regular_mw": round(float(cc.pmax.sum()), 1),
                        "cc_regular_avail_twh": round(float(cc.avail_mwh.sum()) / 1e6, 3),
                        "cc_regular_hr_capw": round(
                            float((cc.heat_rate * cc.pmax).sum() / max(cc.pmax.sum(), 1)), 4
                        ),
                    },
                    default=str,
                ),
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
