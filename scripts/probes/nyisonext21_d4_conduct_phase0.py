"""NYISO-NEXT-21 phase 0 (zero LP): what is wrong behind the keeper's D-4 unit-conduct FAIL rows.

For each (year, plant) the keeper's committed ``legitimacy_diagnostics.json`` fails on the
per-unit conduct rider, this probe decodes the plant's hourly MODEL output (the registered run
payload, ``frontend/data/backcast/runs/<id>.js``) and its hourly MEASURED CAMPD output (the
committed bench part, ``frontend/data/backcast/bench/NYISO/<year>.json.gz``) — both uint8 % of
the plant's EIA-860 nameplate — and asks three questions, zero LP:

1. COMMITMENT: is the model running the unit when the real unit is off for a whole day or more?
   Every model-on / meter-zero hour is classified by the length of the MEASURED off-stretch that
   contains it: shorter than the unit's class min-down (a stretch the bridge's physics says the
   unit cannot take), min-down..24 h, or > 24 h (the unit was genuinely decommitted — the model's
   own run pattern is wrong upstream of any bridge).
2. PHYSICS: does the plant's own measured conduct contradict the class min-down / min-run the
   bridge applies? Share of measured off-gaps between two measured runs that are SHORTER than the
   class min-down, and share of measured runs shorter than the bridge's class min-run.
3. LEVEL: annual model vs measured energy and on-hours.

Read-only over committed artifacts; writes ``results/calibration/_nyisonext21_d4_conduct_phase0.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import numpy as np

from market_sim.config.constants import CC_COMMITMENT_PARAMS, ST_GAS_COMMITMENT_PARAMS
from market_sim.model.commitment import find_runs

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "frontend/data/backcast/runs"
BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
OUT = ROOT / "results/calibration/_nyisonext21_d4_conduct_phase0.json"
KEEPER_SPAN = "2026-09-30-nyisonext18-retiree-carry-span"
KEEPER_2021 = "2026-09-30-nyisonext18-retiree-carry-2021"
BUNDLES = {
    "nyisonext18_2021": ROOT / "results/calibration/nyisonext18_2021",
    "nyisonext18_span": ROOT / "results/calibration/nyisonext18_span",
}
# Bridge class parameters as armed in the keeper recipe (run_config.json).
BRIDGE_MIN_RUN = {"CC_REGULAR": 21.0, "ST_GAS": 13.0}
# A meter reading at or below this CF% counts as off (uint8 1 % resolution).
OFF_CF = 0.5


def _payload(run_id: str) -> dict:
    """Decode a registered run payload (``window.BC.runGz[...] = "<b64 gzip json>"``)."""
    s = (RUNS / f"{run_id}.js").read_text()
    b64 = s.split('="', 1)[1].rsplit('"', 1)[0]
    return json.loads(gzip.decompress(base64.b64decode(b64)))


def _u8(blob: str) -> np.ndarray:
    """Decode a base64 uint8 CF% series to float."""
    return np.frombuffer(base64.b64decode(blob), dtype=np.uint8).astype(float)


def _class_min_down(group: str, heat_rate: float | None) -> float:
    """Class min-down from the commitment table; CC defaults to the efficient row."""
    table = CC_COMMITMENT_PARAMS if group == "CC_REGULAR" else ST_GAS_COMMITMENT_PARAMS
    hr = (
        heat_rate if heat_rate is not None else (6.9 if group == "CC_REGULAR" else 11.0)
    )
    for cutoff, p in table:
        if hr < cutoff:
            return float(p["min_down_hours"])
    return float(table[-1][1]["min_down_hours"])


def _off_stretch_len(on: np.ndarray) -> np.ndarray:
    """Per hour: length of the measured OFF stretch containing it (0 where on)."""
    out = np.zeros(on.shape[0])
    for s, e in find_runs(~on):
        out[s:e] = e - s
    return out


def analyse(
    year: int, key: str, group: str, model_cf: np.ndarray, bench_p: dict
) -> dict:
    """Return the three-question census for one (year, plant slice)."""
    npl = float(bench_p["npl"])
    meas_cf = _u8(bench_p["campd"])
    m_on = model_cf > OFF_CF
    a_on = meas_cf > OFF_CF
    md = _class_min_down(group, None)
    stretch = _off_stretch_len(a_on)
    mismatch = m_on & ~a_on
    cls = {
        "lt_min_down": int(np.sum(mismatch & (stretch < md))),
        "min_down_to_24h": int(np.sum(mismatch & (stretch >= md) & (stretch <= 24))),
        "gt_24h": int(np.sum(mismatch & (stretch > 24))),
    }
    a_runs = find_runs(a_on)
    gaps = [s2 - e1 for (_, e1), (s2, _) in zip(a_runs[:-1], a_runs[1:])]
    run_lens = [e - s for s, e in a_runs]
    m_runs = find_runs(m_on)
    mr = BRIDGE_MIN_RUN.get(group)
    return {
        "year": year,
        "key": key,
        "group": group,
        "npl_mw": npl,
        "model_twh": round(float(model_cf.sum()) * npl / 100 / 1e6, 4),
        "measured_twh": round(float(meas_cf.sum()) * npl / 100 / 1e6, 4),
        "model_on_hours": int(m_on.sum()),
        "measured_on_hours": int(a_on.sum()),
        "model_runs": len(m_runs),
        "measured_runs": len(a_runs),
        "class_min_down_h": md,
        "bridge_min_run_h": mr,
        "model_on_meter_zero_hours": int(mismatch.sum()),
        "model_on_meter_zero_by_measured_off_stretch": cls,
        "share_in_gt24h_off": round(cls["gt_24h"] / max(1, int(mismatch.sum())), 3),
        "measured_gaps": len(gaps),
        "measured_gap_share_lt_min_down": round(float(np.mean(np.array(gaps) < md)), 3)
        if gaps
        else None,
        "measured_gap_median_h": float(np.median(gaps)) if gaps else None,
        "measured_run_median_h": float(np.median(run_lens)) if run_lens else None,
        "measured_run_share_lt_bridge_min_run": (
            round(float(np.mean(np.array(run_lens) < mr)), 3)
            if (run_lens and mr)
            else None
        ),
    }


def main() -> None:
    """Census every failing D-4 unit-conduct row of the keeper."""
    fails = []
    for bdir in BUNDLES.values():
        d4 = json.loads((bdir / "legitimacy_diagnostics.json").read_text())[
            "diagnostics"
        ]["D4"]
        fails += [r for r in d4["rows"] if r["verdict"] == "FAIL"]
    pay = {KEEPER_SPAN: _payload(KEEPER_SPAN), KEEPER_2021: _payload(KEEPER_2021)}
    rows = []
    for r in fails:
        y = int(r["year"])
        run = KEEPER_2021 if y == 2021 else KEEPER_SPAN
        mech, group = [x.strip() for x in r["floor"].split("×")]
        plants = pay[run]["years"][str(y)]["plants"]
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        key = r["plant"] if r["plant"] in plants else f"{r['plant']}:{group}"
        if key not in plants or key not in bench:
            rows.append(
                {"year": y, "plant": r["plant"], "mechanism": mech, "error": "no slice"}
            )
            continue
        out = analyse(y, key, group, _u8(plants[key]["m"]), bench[key])
        out.update(
            mechanism=mech,
            plant_name=bench[key].get("name"),
            zone=bench[key].get("zone"),
            d4_floored_twh=r["floored_twh"],
            d4_binding_hours=r["binding_hours"],
            d4_measured_zero_share=r["measured_zero_share"],
        )
        rows.append(out)
    OUT.write_text(
        json.dumps({"probe": "nyisonext21_d4_conduct_phase0", "rows": rows}, indent=1)
    )
    for o in rows:
        print(json.dumps(o))


if __name__ == "__main__":
    main()
