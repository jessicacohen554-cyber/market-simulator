"""soco-67 phase 0 (ZERO LP): attribute the 2023 CT_PEAKER over-dispatch on the keeper.

Rebuilds the keeper's own fleet (``run_year(fleet_only=True)`` on the committed
bundle recipe — G-DRIFT showed every LP input bit-identical at HEAD) and joins it
to the keeper's committed hourlies (class_hourly / class_band_hourly) and the
per-plant hourly dispatch carried in the registered run payload, against CAMPD
unit-level CEMS. Writes ``results/calibration/_soco67/phase0_<year>.json``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_soco67_phase0.py --years 2023 2024
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import gzip
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/rsocob2_boundary_span"
RUN_ID = "2026-09-25-r-soco-b2-boundary"
OUT = REPO / "results/calibration/_soco67"
T = 8760


def load_payload() -> dict:
    """Decode the registered run payload (gzip+base64 JS) into a dict."""
    s = (REPO / f"frontend/data/backcast/runs/{RUN_ID}.js").read_text()
    b = re.search(r'="([^"]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def build_fleet(year: int, sets: dict | None = None) -> dict:
    """fleet_only rebuild of one keeper year; returns the state dict."""
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
    with contextlib.redirect_stderr(io.StringIO()):
        st = run_year(
            year, meta["iso"], T, float(meta["gas_prices"][str(year)]), {},
            fleet_only=True, **kw,
        )
    return st


def main() -> None:
    """Run the attribution for each requested year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024])
    ap.add_argument("--tag", default="", help="suffix for the per-plant npz (ablation arms)")
    ap.add_argument("--clip", action="append", default=[],
                    help="PLANT:UNIT:YYYY-MM-DD -- clip that unit's outage windows to start no earlier than the date (pre-COD ablation)")
    ap.add_argument("--set", action="append", default=[], help="k=v ScenarioConfig override (json value) for an ablation rebuild")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.clip:
        from market_sim.data import outages as _o

        clips = [(int(p), str(u), pd.Timestamp(d)) for p, u, d in (c.split(":") for c in a.clip)]
        _orig = _o._load_unit_outage_events

        def _clipped(csv_path, iso):
            df = _orig(csv_path, iso)
            if df is None:
                return df
            df = df.copy()
            s0 = pd.to_datetime(df["outage_start"])
            keep = pd.Series(True, index=df.index)
            for p, u, d in clips:
                m = (df["facility_id"].astype(int) == p) & (df["unit_id"].astype(str) == u)
                late = m & (s0 < d)
                df.loc[late, "outage_start"] = d.strftime("%Y-%m-%d")
                e0 = pd.to_datetime(df["outage_end"])
                keep &= ~(m & (e0 <= d))
                df.loc[late, "duration_days"] = (e0[late] - d).dt.total_seconds() / 86400
            print(f"  [clip] {csv_path.name}: {int((~keep).sum())} rows dropped", flush=True)
            return df[keep]

        _o._load_unit_outage_events = _clipped
    for y in a.years:
        sets = {k: json.loads(v) for k, v in (x.split('=', 1) for x in a.set)}
        st = build_fleet(y, sets)
        fa = st["fleet_arrays"]
        mc = np.asarray(st["mc_base"], dtype=float)
        pmax = np.asarray(fa.pmax, float)
        av = np.asarray(fa.availability, float)
        if av.ndim == 1:
            av = np.repeat(av[:, None], T, axis=1)
        mcm = mc.mean(axis=1) if mc.ndim == 2 else mc
        df = pd.DataFrame({
            "unit": list(map(str, fa.unit_ids)),
            "plant": np.asarray(getattr(fa, "plant_code", getattr(fa, "plant_id", np.zeros(len(pmax))))),
            "cls": np.asarray(fa.plant_group).astype(str),
            "zone": np.asarray(getattr(fa, "zone", getattr(fa, "zone_id", [""] * len(pmax)))).astype(str),
            "pmax": pmax,
            "avail_mwh": (pmax[:, None] * av).sum(axis=1),
            "mc_mean": mcm,
            "hr": np.asarray(fa.heat_rate, float),
            "vom": np.asarray(fa.vom, float),
            "min_gen_mwh": np.asarray(fa.min_gen, float).sum(axis=1) if np.ndim(fa.min_gen) == 2 else np.asarray(fa.min_gen, float) * T,
        })
        df.to_parquet(OUT / f"fleet_{y}{a.tag}.parquet")
        cap_cls = {}
        for c in df.cls.unique():
            idx = np.where(df.cls.values == c)[0]
            cap_cls[c] = (pmax[idx, None] * av[idx]).sum(axis=0)
        np.savez_compressed(OUT / f"avail_cls_{y}{a.tag}.npz", **cap_cls)
        # per-(plant, class) hourly availability MW for the gas classes
        keys = {}
        for (p, c), g in df[df.cls.isin(["CC_REGULAR", "CT_PEAKER", "ST_GAS"])].groupby(["plant", "cls"]):
            idx = g.index.values
            keys[f"{int(p)}|{c}"] = (pmax[idx, None] * av[idx]).sum(axis=0).astype(np.float32)
        np.savez_compressed(OUT / f"avail_plant_{y}{a.tag}.npz", **keys)
        print(y, "units", len(df), "written")


if __name__ == "__main__":
    main()
