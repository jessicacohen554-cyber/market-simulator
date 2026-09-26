#!/usr/bin/env python3
"""miso-274 phase 0 (zero LP): is the keeper's CC_REGULAR shortfall an AVAILABILITY or a MERIT object?

The miso-273 keeper (``results/calibration/miso273_span``) under-dispatches
CC_REGULAR by 8.85-13.69 TWh in 2021-2023. Two candidate roots:

* **availability** — the CC fleet is clipped (outage numerator/denominator
  basis at block plants, or a plant carried below its own measured output), so
  the LP *cannot* run CC in hours it needs it;
* **merit** — CC has headroom in those hours and the LP *chooses* coal.

For each year this rebuilds the keeper fleet (``run_year(fleet_only=True)``, the
miso-271 decomposition helpers) and joins its hourly CC_REGULAR available MW to
the keeper's committed ``hourly/class_hourly_<Y>.parquet`` dispatch. It reports:

* ``cc_avail_twh`` / ``cc_disp_twh`` and the actual (the bench C1 CC_REGULAR);
* ``binding_hours`` — hours CC dispatch is within 1 % of its availability;
* ``disp_in_binding_twh`` — CC energy dispatched in those hours;
* ``headroom_while_coal_econ_twh`` — CC headroom summed over hours in which the
  coal classes dispatch above their committed band (i.e. coal is on the margin
  while CC idles);
* a per-plant table of CC availability against EIA-923 net generation (CT/CA/CS
  prime movers) — a plant clipped below its own metered output is the miso-186
  Cottonwood pattern.

Usage::

    uv run python scripts/probes/_miso274_cc_phase0.py --years 2021 2022 2023 \
        --out results/calibration/_miso274_cc_phase0.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _miso271_cc_decomp as dec  # noqa: E402

dec.KEEPER = REPO / "results/calibration/miso273_span"
COAL = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC")
F923 = REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"


def hourly_fleet(year: int, hh: float) -> pd.DataFrame:
    """Hourly available MW per (class, band, plant) for the keeper fleet."""
    from scripts.run_calibration import run_year  # type: ignore

    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, {}))
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], 8760, axis=1)
    mw = pmax[:, None] * avail
    band = [
        "committed" if u.endswith("_committed") else u.rsplit("_", 1)[-1]
        for u in fa.unit_ids
    ]
    return pd.DataFrame(
        {
            "group": list(fa.plant_group),
            "band": band,
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "pmax": pmax,
        }
    ), mw


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    ref = _load_reference()
    g923 = pd.read_csv(F923)
    g923 = g923[g923.prime_mover.isin(["CA", "CT", "CS"])]
    res: dict[str, dict] = {}
    for y in args.years:
        meta, mw = hourly_fleet(y, _henry_hub_actual(ref, y))
        cc = (meta.group == "CC_REGULAR").to_numpy()
        cc_av = mw[cc].sum(axis=0)
        ch = pd.read_parquet(dec.KEEPER / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"].pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum"
        )
        cb = pd.read_parquet(dec.KEEPER / "hourly" / f"class_band_hourly_{y}.parquet")
        cb = cb[cb["pass"] == "P1"]
        cc_d = ch["CC_REGULAR"].reindex(range(8760)).fillna(0).to_numpy()
        coal_ncom = (
            cb[cb.klass.isin(COAL) & (cb.band != "committed")]
            .groupby("hour")
            .mw.sum()
            .reindex(range(8760))
            .fillna(0)
            .to_numpy()
        )
        bind = cc_d >= 0.99 * cc_av
        head = np.clip(cc_av - cc_d, 0, None)
        coal_margin = coal_ncom > 1.0
        # Per-plant availability vs EIA-923 net generation.
        pl = pd.DataFrame(
            {
                "plant_code": meta.plant_code[cc],
                "av": mw[cc].sum(axis=1),
                "mw": meta.pmax[cc],
            }
        )
        pl = pl.groupby("plant_code").sum()
        ng = g923[g923.year == y].groupby("plant_id").net_generation_mwh.sum()
        pl["ng"] = ng.reindex(pl.index).fillna(0.0)
        short = pl[pl.av < pl.ng]
        res[str(y)] = {
            "cc_mw": round(float(meta.pmax[cc].sum()), 1),
            "cc_avail_twh": round(float(cc_av.sum()) / 1e6, 3),
            "cc_disp_twh": round(float(cc_d.sum()) / 1e6, 3),
            "cc_923_ng_twh_same_plants": round(float(pl.ng.sum()) / 1e6, 3),
            "binding_hours": int(bind.sum()),
            "disp_in_binding_twh": round(float(cc_d[bind].sum()) / 1e6, 3),
            "coal_above_committed_hours": int(coal_margin.sum()),
            "coal_above_committed_twh": round(float(coal_ncom.sum()) / 1e6, 3),
            "headroom_while_coal_econ_twh": round(
                float(head[coal_margin].sum()) / 1e6, 3
            ),
            "cc_headroom_twh": round(float(head.sum()) / 1e6, 3),
            "plants_clipped_below_923": {
                int(k): {
                    "avail_twh": round(v.av / 1e6, 3),
                    "ng_twh": round(v.ng / 1e6, 3),
                    "mw": round(v.mw, 1),
                }
                for k, v in short.iterrows()
            },
            "clipped_shortfall_twh": round(float((short.ng - short.av).sum()) / 1e6, 3),
        }
        print(json.dumps({y: res[str(y)]}), flush=True)
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
