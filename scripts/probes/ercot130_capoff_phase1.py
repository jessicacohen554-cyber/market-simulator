"""ERCOT-130 Phase 1 — the ex-ante bound on the min-config UPPER bound (cap-off).

Measures, on the CURRENT KEEPER (``2026-07-28-ercot129-conditional-coal-min``,
bundle ``results/calibration/ercot129_conditional``), the size of the residual
leg ERCOT-129 left open: **category B** — coal plant-hours where the plant's
own available capacity cannot reach its minimum online configuration, so the
ERCOT-129 floor correctly drops to zero and the LP is free to run the plant at
a physically undeliverable level.

Availability is EXOGENOUS DATA, so it is captured from the real fleet-array
build path (``runner.generators_to_fleet_arrays``) under the keeper's own
recipe — no LP is built and no year is solved. Per-plant dispatch comes from
the keeper's committed dashboard run payload, exactly as the ERCOT-128 probe's
sections A-G do (rule 15 ``[R-DASHBOARD]``: the payload, not a replay).

Usage:
    python scripts/probes/ercot130_capoff_phase1.py --capture   # fleet arrays
    python scripts/probes/ercot130_capoff_phase1.py             # score
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

os.environ.setdefault("MARKET_SIM_WARMSTART_XYEAR", "0")

KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot129_conditional"
KEEPER_RUN_ID = "2026-07-28-ercot129-conditional-coal-min"
MIN_CONFIG_CSV = REPO / "data" / "raw" / "_processed-legacy" / "coal_min_config_ERCOT.csv"
CACHE = REPO / "results" / "calibration" / "_ercot130_avail_cache"
YEARS = (2023, 2024, 2025)


class _Captured(BaseException):
    """Sentinel raised to abort the run once the fleet arrays exist."""


def min_config_table() -> dict[int, float]:
    """Per-plant ``min_u MinLoad_u`` (MW) from the frozen EIA-860 artifact."""
    df = pd.read_csv(MIN_CONFIG_CSV)
    return {int(r.plant_code): float(r.min_config_mw) for r in df.itertuples()}


def capture_availability(year: int) -> None:
    """Build the keeper's fleet arrays for ``year`` and persist coal availability.

    Monkeypatches the runner's fleet-array constructor, records the coal rows'
    ``availability x pmax`` summed per plant code, then aborts the run before
    any LP is constructed.
    """
    # The LIVE fleet-array call is the copy imported into ``scripts
    # .run_calibration`` (line 76), NOT ``market_sim.runner`` — patching the
    # latter lets the whole year solve.
    from scripts import replay_keeper as rk
    from scripts import run_calibration as rc
    from scripts import run_calibration_full as rcf

    meta = json.loads((KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = CACHE / f"_scratch_{year}"

    real = rc.generators_to_fleet_arrays
    box: dict = {}

    def _spy(generators, zone_names, **kw):
        fa = real(generators, zone_names, **kw)
        codes = np.array(
            [int(getattr(g, "plant_code", 0) or 0) for g in generators], dtype=int
        )
        is_coal = np.array(
            [str(getattr(g, "fuel_type", "")) == "coal" for g in generators], dtype=bool
        )
        box["codes"] = codes
        box["is_coal"] = is_coal
        box["avail"] = np.asarray(fa.availability, dtype=np.float32)
        box["pmax"] = np.asarray(fa.pmax, dtype=np.float64)
        raise _Captured

    rc.generators_to_fleet_arrays = _spy
    try:
        rcf.solve_and_persist(**kwargs)
    except _Captured:
        pass
    finally:
        rc.generators_to_fleet_arrays = real

    codes, is_coal = box["codes"], box["is_coal"]
    avail, pmax = box["avail"], box["pmax"]
    plants = sorted({int(c) for c in codes[is_coal] if c})
    stack = np.zeros((len(plants), avail.shape[1]), dtype=np.float32)
    caps = np.zeros(len(plants), dtype=np.float64)
    for i, code in enumerate(plants):
        rows = np.flatnonzero(is_coal & (codes == code))
        stack[i] = (avail[rows] * pmax[rows, None]).sum(axis=0)
        caps[i] = float(pmax[rows].sum())
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        CACHE / f"avail_{year}.npz",
        plants=np.asarray(plants, dtype=int),
        avail_cap=stack,
        pmax_total=caps,
    )
    print(f"[capture] {year}: {len(plants)} coal plants, {stack.shape[1]} hours")


def load_payload_dispatch(year: int) -> tuple[dict[int, np.ndarray], dict[int, float]]:
    """Per-plant hourly model MW and model capacity from the keeper payload."""
    src = REPO / "frontend" / "data" / "backcast" / "runs" / f"{KEEPER_RUN_ID}.js"
    blob = re.search(r'"(H4sI[^"]+)"', src.read_text()).group(1)
    payload = json.loads(gzip.decompress(base64.b64decode(blob)))
    bench_p = REPO / "frontend" / "data" / "backcast" / "bench" / "ERCOT" / f"{year}.json.gz"
    with gzip.open(bench_p) as fh:
        bench = json.load(fh)["bench"]["plants"]
    mw: dict[int, np.ndarray] = {}
    cap: dict[int, float] = {}
    for code, rec in payload["years"][str(year)]["plants"].items():
        grp = str(bench.get(code, {}).get("group", ""))
        if not grp.startswith("COAL"):
            continue
        npl = float(bench[code]["npl"])
        mw[int(code)] = (
            np.frombuffer(base64.b64decode(rec["m"]), dtype=np.uint8).astype(float)
            * npl / 100.0
        )
        cap[int(code)] = npl
    return mw, cap


def score() -> dict:
    """Phase 1 legs (a) category-B size, (b) C1 cost bound, per year."""
    mc = min_config_table()
    out: dict = {}
    for year in YEARS:
        npz = np.load(CACHE / f"avail_{year}.npz")
        plants = [int(c) for c in npz["plants"]]
        avail_cap = npz["avail_cap"].astype(float)
        pmax_total = npz["pmax_total"].astype(float)
        mw, cap = load_payload_dispatch(year)

        rows = []
        tot_online = 0
        tot_b_hours = 0
        tot_b_energy = 0.0
        tot_impossible = 0
        for i, code in enumerate(plants):
            if code not in mc or code not in mw:
                continue
            level = mc[code]
            disp = mw[code][: avail_cap.shape[1]]
            ac = avail_cap[i][: len(disp)]
            online = disp > 1.0
            infeasible = ac < level - 1e-6
            catb = online & infeasible
            impossible = online & (disp < level - 1e-6)
            tot_online += int(online.sum())
            tot_b_hours += int(catb.sum())
            tot_b_energy += float(disp[catb].sum())
            tot_impossible += int(impossible.sum())
            rows.append(
                {
                    "plant": code,
                    "min_config_mw": level,
                    "model_cap_mw": round(cap.get(code, 0.0), 1),
                    "fleet_pmax_mw": round(pmax_total[i], 1),
                    "online_h": int(online.sum()),
                    "catB_h": int(catb.sum()),
                    "catB_gwh": round(float(disp[catb].sum()) / 1e3, 2),
                    "impossible_h": int(impossible.sum()),
                    "catB_share_of_impossible": (
                        round(float((catb & impossible).sum()) / max(int(impossible.sum()), 1), 3)
                    ),
                }
            )
        out[str(year)] = {
            "plants": rows,
            "online_plant_hours": tot_online,
            "catB_plant_hours": tot_b_hours,
            "catB_share_of_online": round(tot_b_hours / max(tot_online, 1), 4),
            "catB_energy_twh": round(tot_b_energy / 1e6, 4),
            "impossible_plant_hours": tot_impossible,
            "catB_share_of_impossible": round(tot_b_hours / max(tot_impossible, 1), 4),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", action="store_true",
                    help="build the keeper fleet arrays and cache coal availability")
    ap.add_argument("--year", type=int, default=None, help="capture only this year")
    ap.add_argument("--out", type=Path, default=None, help="write the score JSON here")
    args = ap.parse_args()
    if args.capture:
        for y in ([args.year] if args.year else list(YEARS)):
            capture_availability(int(y))
        return
    res = score()
    txt = json.dumps(res, indent=2)
    if args.out:
        args.out.write_text(txt)
    for y in YEARS:
        r = res[str(y)]
        print(
            f"{y}: online {r['online_plant_hours']:,}  "
            f"catB {r['catB_plant_hours']:,} "
            f"({100*r['catB_share_of_online']:.2f}% of online)  "
            f"energy {r['catB_energy_twh']:.4f} TWh  "
            f"impossible {r['impossible_plant_hours']:,}  "
            f"catB/impossible {100*r['catB_share_of_impossible']:.1f}%"
        )
    if args.out:
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
