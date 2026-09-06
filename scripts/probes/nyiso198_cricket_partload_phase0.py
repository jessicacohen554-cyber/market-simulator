"""nyiso-198 PHASE 0 (NO LP) — Cricket Valley 57185's part-load bucket (b-)
decomposed into the THREE candidate measured objects, on committed artifacts
only (rule 29 ``[R-SCREEN]`` step 0; control = the keeper's committed bundle,
rule 29(b) form 4).

The nyiso-196 repair moved Cricket Valley from +0.80 TWh above its 2024 meter to
0.53 TWh under it, and handed forward bucket ``(b-)`` -- the plant-hours where
BOTH the model and the meter are online but the model runs BELOW the meter
(371 -> 906 GWh in 2024).  A part-load deficit has exactly four possible owners
inside this LP, and every one of them is decidable without a solve because the
LP's own upper and lower bounds are reconstructible from the bundle:

    pmin[g,t]  <=  P[g,t]  <=  pmax[g] * availability[g,t]

so for the plant, in every ``(b-)`` hour, the model's MW sits in exactly one of:

  * **CAP-SCOPE**  -- at the envelope AND no outage active (``availability == 1``):
    the LP simply does not carry enough capacity at this plant.  Object = the
    capacity basis (``cc_capacity_reconcile`` p99.9 cap, the net-summer bin).
  * **CAP-OUTAGE** -- at the envelope AND an outage derate is active: the
    committed ``-perunitmerit-`` extract's window is what holds the plant down.
    Object = the outage series (window timing / removed share).
  * **FLOOR**      -- at the commitment-bridge min-gen floor and below the
    envelope: the LP would be OFF and the floor is the only thing running it.
    Object = ``nyiso_gas_commitment_bridge``'s ``min_load_frac``.
  * **MERIT**      -- strictly interior: the LP had headroom, was not floored,
    and chose not to use it.  Object = offer position (a ``CC_REGULAR`` band
    multiplier -- rule 1 carve-out, owner ruling required).

Only one of those four has a lever this lane may pre-register, and this probe
says which one carries the energy.  It also runs the contradiction test that
made nyiso-196 an object at all: in the CAP-OUTAGE hours, does the METER exceed
the derated envelope the extract handed the LP?  A meter above the extract's own
availability is a measured-input contradiction (rule 14 ``[R-ACCURATE]``); a
meter below it is not.

Nothing here is gated on any residual.  Writes
``results/calibration/_nyiso198_cricket_partload_phase0.json``.

Usage::

    python scripts/probes/nyiso198_cricket_partload_phase0.py [--years 2023 2024 2025]
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
PLANT = 57185
PLANT_KEY = "57185"
CLASS = "CC_REGULAR"
T = 8760
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
#: "online" threshold, identical to the nyiso-196 decomposition.
ON_FRAC = 0.01
#: at-envelope / at-floor tolerances (fractions of the hour's own bound).
CAP_TOL = 0.99
FLOOR_TOL = 1.02
#: an outage is "active" when the plant's capacity-weighted availability is
#: below this; the extract's smallest CC block is 1/3 of a plant.
AVAIL_ON = 0.999


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


def _hod() -> np.ndarray:
    return np.arange(T) % 24


def _r(x, n=1):
    return round(float(x), n)


def year_block(yr: int) -> dict:
    state, meta = reconstruct_bundle_fleet(BUNDLE, yr)
    fa = state["fleet_arrays"]
    mc_base = np.asarray(state["mc_base"])
    pcode = np.asarray(fa.plant_code)
    idx = [i for i in range(len(pcode)) if int(pcode[i]) == PLANT]
    if not idx:
        return {"year": yr, "error": "plant not in fleet"}

    avail = np.asarray(fa.availability)
    pmax = np.asarray(fa.pmax)
    pmin_a = np.asarray(fa.pmin)
    uids = list(fa.unit_ids)
    grp = list(getattr(fa, "group", []) or [])

    def av_row(i):
        return avail[i] if avail.ndim > 1 else np.full(T, float(avail[i]))

    def mc_row(i):
        return mc_base[i] if mc_base.ndim > 1 else np.full(T, float(mc_base[i]))

    units = []
    env = np.zeros(T)
    pmin_env = np.zeros(T)
    for i in idx:
        av = av_row(i)
        mc = mc_row(i)
        env += float(pmax[i]) * av
        # the LP's own pmin is only enforced where the unit is available
        pmin_env += float(pmin_a[i]) * (av > 0)
        units.append(
            {
                "unit_id": uids[i],
                "group": grp[i] if i < len(grp) else "",
                "pmax_mw": _r(pmax[i], 2),
                "pmin_mw": _r(pmin_a[i], 2),
                "heat_rate": _r(fa.heat_rate[i], 4),
                "mc_base_mean": _r(np.mean(mc), 3),
                "avail_mean": _r(np.mean(av), 4),
                "avail_min": _r(np.min(av), 4),
                "hours_derated": int((av < AVAIL_ON).sum()),
            }
        )
    pmax_tot = float(sum(float(pmax[i]) for i in idx))
    avail_w = env / pmax_tot if pmax_tot else np.zeros(T)

    # ---- the keeper's own hourly dispatch and the meter, same basis --------
    run = decode_run_js((ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text())
    bench = json.load(gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz"))["bench"]
    b = bench["plants"][PLANT_KEY]
    npl = float(b["npl"])
    addback = float(b.get("btm") or 0.0) * 1e6 / T
    m = _series(run["years"][str(yr)]["plants"][PLANT_KEY], "m", "m_ann", npl)
    lp = np.clip(m - addback, 0.0, None)
    c = _series(b, "campd", "c_ann", npl)

    zone = b.get("zone")
    sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
    lmp = sysp.pivot(index="hour", columns="zone", values="price")[zone].to_numpy()[:T]

    on_m = lp > ON_FRAC * npl
    on_c = c > ON_FRAC * npl
    both = on_m & on_c
    bminus = both & (lp < c)
    def_mw = np.where(bminus, c - lp, 0.0)

    # ---- classify every (b-) hour by which LP bound is binding -------------
    at_env = lp >= CAP_TOL * env
    outage_active = avail_w < AVAIL_ON
    at_floor = (~at_env) & (pmin_env > 0) & (lp <= FLOOR_TOL * pmin_env)

    cls = np.full(T, "", dtype=object)
    cls[bminus & at_env & ~outage_active] = "CAP_SCOPE"
    cls[bminus & at_env & outage_active] = "CAP_OUTAGE"
    cls[bminus & ~at_env & at_floor] = "FLOOR"
    cls[bminus & ~at_env & ~at_floor] = "MERIT"

    def agg(tag):
        s = bminus & (cls == tag)
        return {
            "hours": int(s.sum()),
            "deficit_gwh": _r(def_mw[s].sum() / 1e3, 1),
            "share_of_bminus_gwh": _r(
                100.0 * def_mw[s].sum() / def_mw.sum() if def_mw.sum() else 0.0, 1
            ),
            "mean_model_mw": _r(lp[s].mean() if s.any() else 0.0),
            "mean_meter_mw": _r(c[s].mean() if s.any() else 0.0),
            "mean_envelope_mw": _r(env[s].mean() if s.any() else 0.0),
            "mean_lmp": _r(lmp[s].mean() if s.any() else 0.0, 2),
        }

    # ---- the rule-14 contradiction test on the CAP_OUTAGE hours -----------
    co = bminus & (cls == "CAP_OUTAGE")
    meter_above_env = co & (c > env)
    # and, for completeness, over ALL hours the extract derates the plant
    der = outage_active & on_c
    out = {
        "year": yr,
        "zone": zone,
        "lp_units": units,
        "lp_pmax_total_mw": _r(pmax_tot, 2),
        "bench_npl_mw": npl,
        "meter_peak_mw": _r(c.max()),
        "meter_p999_mw": _r(np.percentile(c, 99.9)),
        "btm_addback_gwh": _r(float(b.get("btm") or 0.0) * 1e3, 1),
        "annual": {
            "model_lp_gwh": _r(lp.sum() / 1e3, 1),
            "meter_campd_gross_gwh": _r(c.sum() / 1e3, 1),
            "eia923_net_gwh": _r(float(b.get("e_ann") or 0.0) * 1e3, 1),
            "envelope_gwh": _r(env.sum() / 1e3, 1),
            "net_model_minus_meter_gwh": _r((lp.sum() - c.sum()) / 1e3, 1),
        },
        "buckets": {
            "a_model_on_meter_off_gwh": _r(lp[on_m & ~on_c].sum() / 1e3, 1),
            "bplus_gwh": _r(np.where(both & (lp > c), lp - c, 0.0).sum() / 1e3, 1),
            "bminus_gwh": _r(def_mw.sum() / 1e3, 1),
            "c_meter_on_model_off_gwh": _r(c[on_c & ~on_m].sum() / 1e3, 1),
            "bminus_hours": int(bminus.sum()),
        },
        "bminus_by_binding_lp_bound": {
            "CAP_SCOPE": agg("CAP_SCOPE"),
            "CAP_OUTAGE": agg("CAP_OUTAGE"),
            "FLOOR": agg("FLOOR"),
            "MERIT": agg("MERIT"),
        },
        "contradiction_test_rule14": {
            "cap_outage_hours": int(co.sum()),
            "cap_outage_hours_meter_above_envelope": int(meter_above_env.sum()),
            "cap_outage_energy_meter_above_envelope_gwh": _r(
                np.where(meter_above_env, c - env, 0.0).sum() / 1e3, 1
            ),
            "all_derated_hours_meter_online": int(der.sum()),
            "all_derated_hours_meter_above_envelope": int((der & (c > env)).sum()),
            "all_derated_energy_meter_above_envelope_gwh": _r(
                np.where(der & (c > env), c - env, 0.0).sum() / 1e3, 1
            ),
            "mean_availability_when_derated": _r(
                avail_w[outage_active].mean() if outage_active.any() else 1.0, 4
            ),
            "hours_derated": int(outage_active.sum()),
        },
        "capacity_scope_test": {
            "lp_pmax_total_mw": _r(pmax_tot, 2),
            "meter_hours_above_lp_pmax": int((c > pmax_tot).sum()),
            "meter_energy_above_lp_pmax_gwh": _r(
                np.where(c > pmax_tot, c - pmax_tot, 0.0).sum() / 1e3, 1
            ),
        },
    }

    # ---- MERIT detail: where does the LMP sit against the plant's stack? ---
    mrt = bminus & (cls == "MERIT")
    if mrt.any():
        # the marginal (cheapest not-fully-dispatched) tranche is not directly
        # observable per-unit from the payload (plant-grain series), so report
        # the plant's assembled offer ladder against the hour's LMP instead.
        ladder = sorted(
            [(u["mc_base_mean"], u["unit_id"], u["pmax_mw"]) for u in units]
        )
        mcs = np.array([mc_row(i) for i in idx])  # (n_units, T)
        order = np.argsort([np.mean(mc_row(i)) for i in idx])
        cum = np.zeros(T)
        clears_at = np.full(T, np.nan)
        for k in order:
            i = idx[k]
            av = av_row(i)
            mck = mc_row(i)
            cap_k = float(pmax[i]) * av
            # capacity of tranches whose offer the LMP clears
            cum = cum + np.where(mck <= lmp, cap_k, 0.0)
        out["merit_detail"] = {
            "offer_ladder_mc_base_mean": [
                {"unit": u[1], "mc": u[0], "pmax_mw": u[2]} for u in ladder
            ],
            "mean_lmp_in_merit_hours": _r(lmp[mrt].mean(), 2),
            "mean_in_money_capacity_mw": _r(cum[mrt].mean()),
            "mean_model_mw": _r(lp[mrt].mean()),
            "mean_meter_mw": _r(c[mrt].mean()),
            "hours_model_below_in_money_capacity": int(
                (mrt & (lp < 0.99 * cum)).sum()
            ),
            "deficit_gwh_where_meter_above_in_money_capacity": _r(
                np.where(mrt & (c > cum), c - cum, 0.0).sum() / 1e3, 1
            ),
            "deficit_gwh_where_meter_below_in_money_capacity": _r(
                np.where(mrt & (c <= cum), def_mw, 0.0).sum() / 1e3, 1
            ),
        }
        hod = _hod()
        mon = _month_of_hour()
        out["merit_detail"]["deficit_gwh_by_hod"] = {
            str(h): _r(def_mw[mrt & (hod == h)].sum() / 1e3, 2) for h in range(24)
        }
        out["merit_detail"]["deficit_gwh_by_month"] = {
            str(mo): _r(def_mw[mrt & (mon == mo)].sum() / 1e3, 2) for mo in range(1, 13)
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    a = ap.parse_args()
    out = {
        "session": "nyiso-198",
        "status": "PHASE 0 — NO LP, MEASUREMENT ONLY (rule 29 step 0)",
        "keeper": KEEPER_ID,
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "plant": PLANT,
        "class": CLASS,
        "question": (
            "Cricket Valley 57185 bucket (b-) — which LP bound is binding in the "
            "hours the model runs below the meter: the capacity basis "
            "(CAP_SCOPE), the committed outage extract (CAP_OUTAGE), the "
            "commitment bridge floor (FLOOR), or the offer position (MERIT)?"
        ),
        "years": {},
    }
    for yr in a.years:
        out["years"][str(yr)] = year_block(yr)
        print(f"[nyiso-198] {yr} done", flush=True)
    dest = ROOT / "results/calibration/_nyiso198_cricket_partload_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
