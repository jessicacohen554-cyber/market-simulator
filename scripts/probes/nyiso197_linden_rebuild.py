"""nyiso-197 PHASE 0 part 2 (NO LP) — the keeper's own Linden 50006 fleet
representation, and the four step-2 candidate measured objects adjudicated on
committed artifacts.

Rebuilds the keeper's fleet with ``scripts.lib.bundle_fleet`` on its committed
``meta.json`` (rule 29 ``[R-SCREEN]`` step 0; control = the keeper's committed
bundle, form 4) and measures:

* **R-1 capacity ladder** — every LP unit the fleet carries for plant 50006:
  ``pmax``, tranche, heat rate, ``mc_base`` — against the four published
  capability statements for the same station (EIA-860 nameplate / summer,
  the CAMPD observed peak the outage extract uses as its ``plant_capacity_mw``,
  and the NYISO Gold Book Table III-2a station capability MW / SUM / WIN and
  net capability SUM.1 / WIN.1).
* **R-2 envelope vs price** — the keeper's own hourly Linden dispatch (payload
  minus its flat CHP add-back) against the rebuilt availability envelope: the
  share of hours at the envelope (capacity-bound) versus below it
  (price-following), and, in the below-envelope hours, whether the NYC LMP
  clears the plant's assembled committed-tranche offer.
* **R-3 delivered gas** — the delivered gas price the keeper assembled for the
  Linden units against the committed measured NYC hub monthly
  (``transco_z6_iroquois_monthly.csv``, Transco Z6 NY), with the plant's own
  EIA-860 pipeline field alongside.
* **R-4 duty / lay-up reach** — whether plant 50006 is inside the armed
  ``chp_layup_duty_curve`` cohort at all.

Writes ``results/calibration/_nyiso197_linden_rebuild_<year>.json``.

Usage::

    python scripts/probes/nyiso197_linden_rebuild.py [--year 2024]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
PLANT = 50006
PLANT_KEY = "50006"
T = 8760
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
#: NYISO Gold Book Table III-2a, station "Linden Cogen" (PTID 23786, Zone J) —
#: read verbatim from the committed editions (2024 -> CY2023, 2025 -> CY2024).
GOLD_BOOK = {
    2023: {
        "edition": "2024-NYCA-Generators.xlsx",
        "mw": 800.0,
        "cap_sum": 790.8,
        "cap_win": 924.9,
        "net_sum": 737.1,
        "net_win": 806.8,
        "net_energy_gwh": 4390.7,
    },
    2024: {
        "edition": "2025-NYCA-Existing-Generating-Facilities.xlsx",
        "mw": 800.0,
        "cap_sum": 790.8,
        "cap_win": 924.9,
        "net_sum": 748.2,
        "net_win": 793.5,
        "net_energy_gwh": 4288.7,
    },
}


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _series(entry: dict, key_bytes: str, key_ann: str, npl: float) -> np.ndarray:
    raw = _dec(entry[key_bytes])[:T]
    if raw.size < T:
        raw = np.pad(raw, (0, T - raw.size))
    ann = entry.get(key_ann)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    return raw * npl / 100.0


def _month_of_hour() -> np.ndarray:
    m = np.zeros(T, dtype=int)
    for i in range(12):
        m[MONTH_STARTS[i] : MONTH_STARTS[i + 1]] = i + 1
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    a = ap.parse_args()
    yr = a.year

    state, meta = reconstruct_bundle_fleet(BUNDLE, yr)
    fa = state["fleet_arrays"]
    mc_base = np.asarray(state["mc_base"])

    pcode = np.asarray(fa.plant_code)
    idx = [i for i in range(len(pcode)) if int(pcode[i]) == PLANT]
    avail = np.asarray(fa.availability)
    pmax = np.asarray(fa.pmax)
    hr = np.asarray(fa.heat_rate)
    pmin_a = np.asarray(fa.pmin)
    uids = list(fa.unit_ids)
    fuel_prices = state.get("fuel_prices")

    units = []
    for i in idx:
        av = avail[i] if avail.ndim > 1 else np.full(T, float(avail[i]))
        mc = mc_base[i] if mc_base.ndim > 1 else np.full(T, float(mc_base[i]))
        units.append(
            {
                "row": i,
                "unit_id": uids[i],
                "pmax_mw": round(float(pmax[i]), 2),
                "pmin_mw": round(float(pmin_a[i]), 2),
                "heat_rate": round(float(hr[i]), 4),
                "mc_base_mean": round(float(np.mean(mc)), 3),
                "mc_base_p10": round(float(np.percentile(mc, 10)), 3),
                "mc_base_p90": round(float(np.percentile(mc, 90)), 3),
                "avail_mean": round(float(np.mean(av)), 4),
                "avail_min": round(float(np.min(av)), 4),
            }
        )
    pmax_tot = sum(u["pmax_mw"] for u in units)
    env = np.zeros(T)
    for i in idx:
        av = avail[i] if avail.ndim > 1 else np.full(T, float(avail[i]))
        env += float(pmax[i]) * av

    # keeper hourly (payload minus its own flat CHP add-back)
    run = decode_run_js(
        (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    )
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz")
    )["bench"]
    b = bench["plants"][PLANT_KEY]
    npl = float(b["npl"])
    m = _series(run["years"][str(yr)]["plants"][PLANT_KEY], "m", "m_ann", npl)
    c = _series(b, "campd", "c_ann", npl)
    addback = float(b["btm"]) * 1e6 / T
    lp = np.clip(m - addback, 0.0, None)

    sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
    lmp = sysp.pivot(index="hour", columns="zone", values="price")["NYC"].to_numpy()[:T]

    at_env = lp >= 0.99 * env
    below = ~at_env
    # committed tranche = the cheapest Linden row that carries capacity
    cheap = min(units, key=lambda u: u["mc_base_mean"]) if units else None
    i_cheap = cheap["row"] if cheap else None
    mc_cheap = (
        (mc_base[i_cheap] if mc_base.ndim > 1 else np.full(T, float(mc_base[i_cheap])))
        if i_cheap is not None
        else np.zeros(T)
    )
    dear = max(units, key=lambda u: u["mc_base_mean"]) if units else None
    i_dear = dear["row"] if dear else None
    mc_dear = (
        (mc_base[i_dear] if mc_base.ndim > 1 else np.full(T, float(mc_base[i_dear])))
        if i_dear is not None
        else np.zeros(T)
    )

    gb = GOLD_BOOK.get(yr)
    month = _month_of_hour()
    hub = pd.read_csv(ROOT / "data/raw/gas-prices/transco_z6_iroquois_monthly.csv")
    hub["y"] = hub.date.str.slice(0, 4).astype(int)
    hub["m"] = hub.date.str.slice(5, 7).astype(int)
    hub_y = hub[hub.y == yr].set_index("m").transco_z6_ny_usd_mmbtu.to_dict()
    fp_month = None
    if fuel_prices is not None:
        fp = np.asarray(fuel_prices)
        if fp.ndim > 1 and i_cheap is not None:
            g_fp = fp[i_cheap]
        else:
            g_fp = fp if fp.ndim == 1 and fp.size == T else None
        if g_fp is not None and np.asarray(g_fp).size == T:
            g_fp = np.asarray(g_fp)
            fp_month = {
                str(mo): round(float(g_fp[month == mo].mean()), 4)
                for mo in range(1, 13)
            }

    from market_sim.data.chp_layup import load_chp_duty_curve, load_chp_layup_census

    out = {
        "session": "nyiso-197",
        "status": "PHASE 0 part 2 — NO LP, MEASUREMENT ONLY",
        "keeper": KEEPER_ID,
        "year": yr,
        "R1_capacity_ladder": {
            "lp_units": units,
            "lp_pmax_total_mw": round(pmax_tot, 2),
            "eia860_nameplate_mw": 974.1,
            "eia860_summer_mw": 904.2,
            "campd_observed_peak_mw_extract_basis": 1272.0
            if yr == 2024
            else (1275.0 if yr == 2023 else 1240.0),
            "campd_hourly_max_mw_meter": round(float(c.max()), 1),
            "measured_btm_share_pct": 22.21,
            "goldbook": gb,
            "lp_pmax_over_goldbook_net_sum": (
                round(pmax_tot / gb["net_sum"], 4) if gb else None
            ),
        },
        "R2_envelope_vs_price": {
            "lp_annual_gwh": round(float(lp.sum()) / 1e3, 1),
            "envelope_annual_gwh": round(float(env.sum()) / 1e3, 1),
            "goldbook_net_energy_gwh": gb["net_energy_gwh"] if gb else None,
            "lp_minus_goldbook_gwh": (
                round(float(lp.sum()) / 1e3 - gb["net_energy_gwh"], 1) if gb else None
            ),
            "lp_cf_on_lp_pmax": round(float(lp.sum()) / (pmax_tot * T), 4),
            "goldbook_cf_on_goldbook_net_sum": (
                round(gb["net_energy_gwh"] * 1e3 / (gb["net_sum"] * T), 4)
                if gb
                else None
            ),
            "hours_at_envelope": int(at_env.sum()),
            "hours_below_envelope": int(below.sum()),
            "energy_at_envelope_gwh": round(float(lp[at_env].sum()) / 1e3, 1),
            "headroom_below_envelope_gwh": round(
                float((env - lp)[below].sum()) / 1e3, 1
            ),
            "below_env_share_nyc_lmp_clears_cheapest_tranche": round(
                float((lmp[below] > mc_cheap[below]).mean()), 4
            ),
            "below_env_share_nyc_lmp_clears_dearest_tranche": round(
                float((lmp[below] > mc_dear[below]).mean()), 4
            ),
            "nyc_lmp_mean": round(float(lmp.mean()), 2),
            "cheapest_tranche": cheap["unit_id"] if cheap else None,
            "cheapest_tranche_mc_mean": cheap["mc_base_mean"] if cheap else None,
            "dearest_tranche": dear["unit_id"] if dear else None,
            "dearest_tranche_mc_mean": dear["mc_base_mean"] if dear else None,
        },
        "R3_delivered_gas": {
            "eia860_pipeline_1": "TRANSCONTINENTAL GAS PIPELINE",
            "eia860_plant_state_county": "NJ / Union (Linden)",
            "model_zone": b.get("zone"),
            "committed_nyc_hub_monthly_usd_mmbtu": {
                str(k): round(float(v), 4) for k, v in sorted(hub_y.items())
            },
            "lp_delivered_gas_monthly_usd_mmbtu": fp_month,
            "note": (
                "the model charges the NYC-zone hub (Transco Z6 NY, the NYC "
                "citygate); the plant is physically in Linden NJ on Transco "
                "Zone 6 NON-NY. No Z6 non-NY series is committed in this repo."
            ),
        },
        "R4_duty_reach": {
            "chp_layup_duty_curve_armed": bool(meta.get("chp_layup_duty_curve")),
            "plant_in_layup_census": PLANT in load_chp_layup_census("NYISO"),
            "plant_in_duty_curve": PLANT in load_chp_duty_curve("NYISO"),
        },
    }
    dest = ROOT / f"results/calibration/_nyiso197_linden_rebuild_{yr}.json"
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2)[:4000])
    print(f"wrote {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
