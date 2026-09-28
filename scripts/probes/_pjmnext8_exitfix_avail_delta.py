"""PJM-NEXT-8 card 2 zero-LP: available-MWh delta of the exit-cohort repair, per plant.

For each year, two ``fleet_only`` rebuilds of the keeper recipe
(``pjmnext7_vs_span``) — flag off and ``unit_outage_exit_cohort_repair`` on —
and the difference of ``pmax x availability`` summed per (plant, class). The
model's own per-plant energy and the bench CAMPD/EIA-923 energy are joined so
the prediction can bound the dispatch effect. No LP.

Run: ``uv run python scripts/probes/_pjmnext8_exitfix_avail_delta.py 2019 [...]``
Writes ``results/calibration/_pjmnext8_exitfix_avail_delta_<year>.json``.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/pjmnext7_vs_span"


def _avail_mwh(y: int, armed: bool) -> tuple[dict, dict]:
    """Per (plant_code, class): annual available MWh and hourly available MW."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, y))
    kw["pjm_da_virtual_bids"] = False  # demand-side overlay, inert for availability
    if armed:
        kw["prb_overrides"] = {
            **(kw.get("prb_overrides") or {}),
            "unit_outage_exit_cohort_repair": True,
        }
    r = run_year(y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
    fa = r["fleet_arrays"]
    av = np.asarray(fa.availability, float)
    mwh = np.asarray(fa.pmax, float) * (
        av.sum(axis=1) if av.ndim == 2 else av * av.shape[0]
    )
    hourly_mw = np.asarray(fa.pmax, float)[:, None] * (
        av if av.ndim == 2 else av[:, None]
    )
    out: dict[tuple[str, str], float] = {}
    hourly: dict[tuple[str, str], np.ndarray] = {}
    pcs = np.asarray(fa.plant_code).astype(str)
    cls = np.asarray(fa.plant_group).astype(str)
    for i, key in enumerate(zip(pcs, cls)):
        out[key] = out.get(key, 0.0) + float(mwh[i])
        hourly[key] = hourly.get(key, 0.0) + hourly_mw[i]
    return out, hourly


def _model_hourly(y: int) -> dict[str, np.ndarray]:
    """Registered keeper per-plant hourly model MW (payload CF bytes rescaled)."""
    import base64
    import gzip
    import re

    js = REPO / "frontend/data/backcast/runs/2026-09-28-pjm-next-7-virtual.js"
    b64 = re.search(r'="([A-Za-z0-9+/=]+)"', js.read_text()).group(1)
    plants = json.loads(gzip.decompress(base64.b64decode(b64)))["years"][str(y)][
        "plants"
    ]
    out = {}
    for k, v in plants.items():
        raw = np.frombuffer(base64.b64decode(v["m"]), dtype=np.uint8).astype(float)
        t = raw.sum()
        if v.get("m_ann") and t > 0:
            out[k] = raw * (float(v["m_ann"]) * 1e6 / t)
    return out


def main() -> None:
    """Print and write the per-plant availability delta for each year."""
    logging.disable(logging.CRITICAL)
    for y in [int(a) for a in sys.argv[1:]]:
        (off, _), (on, on_h) = _avail_mwh(y, False), _avail_mwh(y, True)
        model = _model_hourly(y)
        rows = []
        for k in sorted(set(off) | set(on)):
            d = on.get(k, 0.0) - off.get(k, 0.0)
            if abs(d) <= 1.0:
                continue
            m = model.get(k[0], model.get(f"{k[0]}:{k[1]}"))
            over = None
            if m is not None and k in on_h:
                n = min(len(m), len(on_h[k]))
                over = float(np.clip(m[:n] - on_h[k][:n], 0, None).sum()) / 1e6
            rows.append(
                {
                    "plant": k[0],
                    "class": k[1],
                    "off_twh": off.get(k, 0.0) / 1e6,
                    "delta_twh": d / 1e6,
                    "model_above_repaired_twh": over,
                }
            )
        by_cls: dict[str, float] = {}
        for rw in rows:
            by_cls[rw["class"]] = by_cls.get(rw["class"], 0.0) + rw["delta_twh"]
        gross: dict[str, float] = {}
        for rw in rows:
            gross[rw["class"]] = gross.get(rw["class"], 0.0) + (
                rw["model_above_repaired_twh"] or 0.0
            )
        print(
            y, "avail", {c: round(v, 3) for c, v in sorted(by_cls.items())}, flush=True
        )
        print(
            y,
            "gross phantom",
            {c: round(v, 3) for c, v in sorted(gross.items())},
            flush=True,
        )
        for rw in sorted(rows, key=lambda r_: r_["delta_twh"])[:12]:
            print(
                "   ",
                rw["plant"],
                rw["class"],
                round(rw["off_twh"], 3),
                round(rw["delta_twh"], 3),
                rw["model_above_repaired_twh"],
            )
        dest = REPO / f"results/calibration/_pjmnext8_exitfix_avail_delta_{y}.json"
        dest.write_text(
            json.dumps({"year": y, "by_class_twh": by_cls, "rows": rows}, indent=1)
        )


if __name__ == "__main__":
    main()
