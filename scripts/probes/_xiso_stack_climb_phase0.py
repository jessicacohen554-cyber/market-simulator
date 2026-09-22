"""xiso phase 0 — does the LP CLIMB its own thermal stack? ZERO LP, every ISO.

Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP.
Pre-registration (every definition, and the verdict threshold, fixed before any
number was computed): ``docs/PRECOMMIT-xiso-stack-climb-attribution-2026-09-22.md``.

THE HYPOTHESIS. ``price_tail`` (C3c) is a ledgered caveat in five ISOs and a FAIL
in a sixth, and has never been attributed. Two lanes measured the same candidate
cause on 2026-09-21 — PJM (``FINDING-pjm-h15-…`` §4) and SPP
(``RESULT-spp-70-…`` §0/§4) — and both times it was the reason an offer-curve
lever was REFUSED at zero LP: **the tail is not missing because the stack lacks
height, it is missing because the clearing point never climbs it.** This probe
generalises both measurements into ONE ISO-agnostic form and runs it over every
ISO's designated keeper.

WHAT IS MEASURED, per ISO-year, in the market's top-1 % hours (PRECOMMIT §3.6):

  1. availability-aware idle thermal (MW and %), total and per class;
  2. per-class utilisation;
  3. the highest AVAILABLE offer vs the model clearing price vs the market price;
  4. capacity offered ABOVE the clearing price (the SPP-70 metric, computed by a
     different route than (1) so the two cross-check);
  5. whole-year dispatch of every ``peak*`` band (the PJM §3 inertness measure).

THE ALPHABET TRAP IS REMOVED, NOT ROUTED AROUND. The fleet's ``efficiency_bin``
and the sidecar's ``klass`` are different vocabularies, and joining them naively
inflated PJM's idle block by ~62 GW (83 GW / 59 % instead of 27 GW / 26 %). The
PJM probe keyed the fleet side on ``Generator.fuel_type`` to dodge it. Here the
fleet side is keyed on the SIDECAR WRITER'S OWN derivation
(``run_calibration_full.py:410-430``) — ``plant_group`` (or
``_model_class_for_unit`` for ERCOT / groupless rows), then ``_coal_supply_class``
for COAL — which is EXACTLY the ``klass_base`` that ``class_band_hourly`` writes
into its ``klass`` column (``:753-758``). Same function, same inputs ⇒ exact
alphabet, ISO-agnostic, ERCOT's ``efficiency_bin`` path carried for free.
``class_band_hourly`` is also the correct sidecar for that key: ``class_hourly``
relabels a dual-fuel unit's oil hours into the pooled ``oil`` class and would
undercount gas.

Three reconciliation gates (PRECOMMIT §3.7) run BEFORE any number is emitted; an
ISO-year that fails one is marked UNRECONCILED and excluded from the verdict.

One year per interpreter — the fleet loaders are ``@lru_cache``d on arguments,
never on file contents (the SPP-70 trap (b)).

Run:  python3 scripts/probes/_xiso_stack_climb_phase0.py --iso PJM --year 2024 \
          --bundle results/calibration/pjm_h15_coalwindow_span --out <dir>
      python3 scripts/probes/_xiso_stack_climb_phase0.py --report --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

#: PRECOMMIT §3.3 — thermal by MODEL FUEL TYPE, fixed before measuring because
#: the choice moves the answer. Oil is IN, matching the PJM precedent exactly
#: (its 27,393 MW includes ~4 GW of oil at 0-6 % utilisation).
THERMAL_FUELS = ("coal", "gas_cc", "gas_cc_ccs", "gas_ct", "gas_st", "oil")

#: PRECOMMIT §2.1 — SOCO and NWPP are price-unscored by owner registration
#: (calibration_verdict.py:755-765, :1200): no LMP, no DA, no hourly index, no
#: actual_lmp_hourly_<ISO>.parquet, and C3c is never scored. Their top-1 % window
#: is taken on the model's own demand instead, declared as a substitution — a
#: TIGHTNESS window, not a price window.
NO_PRICE_ISOS = ("SOCO", "NWPP")

#: DECLARED SIMPLIFICATIONS — gates turned OFF for the rebuild because their
#: source corpus is GITIGNORED BY LICENSING and cannot be hydrated in any
#: session (not merely absent). Each is recorded into the output JSON so the
#: RESULT states it rather than burying it. Established precedent: the pjm-h15
#: probe carries the identical ``pjm_da_virtual_bids = False`` line.
#:
#: Why it cannot move THIS measurement: virtual INC/DEC enter the LP as pseudo
#: units in their own classes; they add no thermal row, change no thermal
#: ``pmax`` or ``availability``, and the dispatch side is read from the keeper's
#: COMMITTED sidecar, which was written WITH them. The thermal available /
#: dispatched / offer arrays are therefore untouched.
DECLARED_OFF = {
    "pjm_da_virtual_bids": (
        "data/raw/pjm-da-virtuals/ is gitignored under PJM DataMiner2's "
        "non-member redistribution restriction (its README; docs/data-licensing.md "
        "§4) — re-fetch only, never hydratable. Same line as the pjm-h15 probe."
    ),
}


def _sidecar_klass(state, iso: str) -> np.ndarray:
    """Per-row ``klass_base`` — the sidecar writer's OWN derivation.

    Reproduces ``run_calibration_full.py:410-430`` exactly, so the fleet side and
    ``class_band_hourly``'s ``klass`` column share one alphabet by construction
    rather than by a mapping table (PRECOMMIT §3.4).
    """
    from scripts.run_calibration_full import (
        _coal_supply_class,
        _model_class_for_unit,
        _plant_codes_from_unit_ids,
    )

    fleet, fa = state["fleet"], state["fleet_arrays"]
    unit_ids = [str(u) for u in fa.unit_ids]
    fuels = [str(getattr(g, "fuel_type", "")) for g in fleet]
    bins = [str(getattr(g, "efficiency_bin", "")) for g in fleet]
    pg = getattr(fa, "plant_group", None)
    pgroups = [str(x) if x else "" for x in (pg if pg is not None else [])]
    is_ercot = iso == "ERCOT"
    codes = _plant_codes_from_unit_ids(unit_ids, numeric_head=not is_ercot)

    out = []
    for g in range(len(unit_ids)):
        if not is_ercot and g < len(pgroups) and pgroups[g]:
            k = pgroups[g]
        else:
            k = _model_class_for_unit(unit_ids[g], fuels[g], bins[g])
        if k == "COAL":
            k = _coal_supply_class(int(codes[g]))
        out.append(k)
    return np.array(out, dtype=object)


def _as_2d(a, n: int, T: int) -> np.ndarray:
    """Broadcast a ``(n,)`` or ``(n, T)`` array to ``(n, T)``."""
    a = np.asarray(a, dtype=float)
    if a.ndim == 1:
        a = a[:, None] * np.ones((1, T))
    return a[:n, :T]


def _market_rt(iso: str, year: int, T: int) -> np.ndarray | None:
    """NaN-padded ``(T,)`` actual RT series, or ``None`` when the ISO has none."""
    p = REPO / f"data/raw/_validation-source/actual_lmp_hourly_{iso}.parquet"
    if not p.exists():
        return None
    d = pd.read_parquet(p)
    d = d[d["year"] == int(year)]
    if d.empty:
        return None
    out = np.full(T, np.nan)
    h = d["hour"].to_numpy(int)
    m = (h >= 0) & (h < T)
    out[h[m]] = d["rt"].to_numpy(float)[m]
    return out


def _rebuild(bundle: Path, year: int):
    """Rebuild the keeper's fleet with no LP, fidelity-guarded.

    Uses the sanctioned pieces individually — ``full_run_year_kwargs`` (the
    widened mapping, never ``derive_pjm_ordc_overlay._run_year_kwargs``, which
    drops 38 flags), ``derived_run_year_inputs`` (the bundle-recovered inputs a
    ``fleet_only`` rebuild must splat), and ``assert_reconstruction_fidelity``
    (hard-fails on a dropped gate) — rather than ``reconstruct_bundle_fleet``,
    only so :data:`DECLARED_OFF` can be applied WHERE IT IS VISIBLE instead of
    being hidden inside a shared helper. Every guard the sanctioned wrapper runs
    is run here, on the same inputs.
    """
    from scripts.lib.bundle_fleet import (
        assert_reconstruction_fidelity,
        bundle_gas_price,
        ensure_probe_path,
        full_run_year_kwargs,
    )

    ensure_probe_path()
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((Path(bundle) / "meta.json").read_text())
    kw = full_run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    applied = {}
    for flag, reason in DECLARED_OFF.items():
        if kw.get(flag) or meta.get(flag):
            kw[flag] = False
            applied[flag] = reason
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kw
    )
    assert_reconstruction_fidelity(meta, state["config"])
    return state, meta, applied


def measure(iso: str, year: int, bundle: Path) -> dict:
    """Measure one ISO-year. ZERO LP."""
    t0 = time.time()
    state, meta, applied = _rebuild(bundle, year)
    fa = state["fleet_arrays"]
    n = len(fa.unit_ids)
    mc = np.asarray(state["mc_base"], dtype=float)
    T = int(mc.shape[1]) if mc.ndim == 2 else int(meta.get("hours", 8760))
    mc = _as_2d(mc, n, T)
    av_cap = _as_2d(fa.pmax, n, T) * _as_2d(fa.availability, n, T)

    klass = _sidecar_klass(state, iso)
    fuel = np.array([str(getattr(g, "fuel_type", "")) for g in state["fleet"]])
    therm = np.isin(fuel, THERMAL_FUELS)

    # ---- dispatch + prices, from the keeper's COMMITTED sidecars ----
    cb = pd.read_parquet(bundle / f"hourly/class_band_hourly_{year}.parquet")
    cb = cb[cb["pass"] == "P1"]
    disp = (
        cb.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(T))
        .fillna(0.0)
        .sort_index()
    )
    sysf = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    wsum = sysf.groupby("hour").apply(
        lambda d: float(np.average(d["price"], weights=np.maximum(d["demand"], 1e-9))),
        include_groups=False,
    )
    price = wsum.reindex(range(T)).to_numpy(float)
    load = sysf.groupby("hour")["demand"].sum().reindex(range(T)).to_numpy(float)

    # ---- PRECOMMIT §3.2: the top-1 % window ----
    nh = max(1, int(round(0.01 * T)))
    rt = _market_rt(iso, year, T)
    if rt is not None:
        rank, basis = np.where(np.isnan(rt), -np.inf, rt), "market RT"
    else:
        rank, basis = load, "model load (declared substitution, PRECOMMIT §2.1)"
    hi = np.argsort(rank)[-nh:]

    # ---- PRECOMMIT §3.7: reconciliation gates, BEFORE any number ----
    sidecar_classes = set(map(str, disp.columns))
    fleet_classes = sorted({str(k) for k in klass[therm]})
    g1 = [
        k
        for k in fleet_classes
        if k not in sidecar_classes and av_cap[therm & (klass == k)].sum() > 0
    ]
    uncovered = {
        c: float(disp[c].to_numpy()[hi].mean())
        for c in sorted(sidecar_classes - set(fleet_classes))
        if float(disp[c].to_numpy()[hi].mean()) != 0.0
    }

    per_class, g3 = {}, []
    for k in fleet_classes:
        sel = therm & (klass == k)
        av = float(av_cap[sel][:, hi].sum(axis=0).mean())
        us = float(disp[k].to_numpy()[hi].mean()) if k in sidecar_classes else 0.0
        if av <= 0 and us <= 0:
            continue
        if us > av * 1.005 and us - av > 1.0:
            g3.append({"klass": k, "available_mw": av, "dispatched_mw": us})
        per_class[k] = {
            "available_mw": av,
            "dispatched_mw": us,
            "idle_mw": av - us,
            "utilisation": (us / av) if av > 0 else None,
        }

    tot_av = sum(v["available_mw"] for v in per_class.values())
    tot_us = sum(v["dispatched_mw"] for v in per_class.values())

    # ---- (4) the SPP-70 metric: capacity offered ABOVE the clearing price ----
    above = float(
        np.where(mc[therm][:, hi] > price[hi][None, :], av_cap[therm][:, hi], 0.0)
        .sum(axis=0)
        .mean()
    )
    live = av_cap[therm][:, hi] > 0
    mc_hi = np.where(live, mc[therm][:, hi], -np.inf)
    highest = float(np.nanmean(np.max(mc_hi, axis=0)))

    # ---- (5) whole-year peak-band dispatch ----
    pk = cb[cb["band"].astype(str).str.startswith("peak")]
    peak = {
        str(k): {"max_h": float(r["max"]), "mean_h": float(r["mean"])}
        for k, r in pk.groupby("klass", observed=True)["mw"].agg(["max", "mean"]).iterrows()
        if float(r["max"]) > 0 or str(k) in fleet_classes
    }

    return {
        "iso": iso,
        "year": year,
        "bundle": str(bundle.relative_to(REPO)),
        "hours": T,
        "window_hours": nh,
        "window_basis": basis,
        "declared_simplifications": applied,
        "reconciled": not (g1 or g3),
        "gates": {"G1_fleet_class_not_in_sidecar": g1,
                  "G2_sidecar_classes_uncovered_mw": uncovered,
                  "G3_dispatch_exceeds_available": g3},
        "thermal_top1pct": {
            "available_mw": tot_av,
            "dispatched_mw": tot_us,
            "idle_mw": tot_av - tot_us,
            "idle_pct": (100.0 * (tot_av - tot_us) / tot_av) if tot_av > 0 else None,
            "above_clearing_mw": above,
            "above_clearing_pct": (100.0 * above / tot_av) if tot_av > 0 else None,
        },
        "per_class": per_class,
        "prices": {
            "model_clearing": float(np.nanmean(price[hi])),
            "market_rt": (float(np.nanmean(rt[hi])) if rt is not None else None),
            "highest_available_offer": highest,
            "model_clearing_annual_mean": float(np.nanmean(price)),
            "market_rt_annual_mean": (float(np.nanmean(rt)) if rt is not None else None),
        },
        "peak_band_dispatch_mw": peak,
        "build_s": round(time.time() - t0, 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso")
    ap.add_argument("--year", type=int)
    ap.add_argument("--bundle")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.report:
        rows = [json.loads(p.read_text()) for p in sorted(out.glob("*.json"))
                if p.name != "_report.json"]
        (out / "_report.json").write_text(json.dumps(rows, indent=1))
        print(f"{len(rows)} ISO-years -> {out/'_report.json'}")
        return

    r = measure(a.iso, a.year, REPO / a.bundle)
    (out / f"{a.iso}_{a.year}.json").write_text(json.dumps(r, indent=1))
    t = r["thermal_top1pct"]
    mkt = r["prices"]["market_rt"]
    mkt_s = f"${mkt:.1f}" if mkt is not None else "n/a"
    print(
        f"[{a.iso} {a.year}] idle {t['idle_mw']:,.0f} MW ({t['idle_pct']:.1f}%)  "
        f"above-clearing {t['above_clearing_pct']:.1f}%  "
        f"model ${r['prices']['model_clearing']:.1f} vs market {mkt_s}  "
        f"highest-offer ${r['prices']['highest_available_offer']:.1f}  "
        f"reconciled={r['reconciled']}  {r['build_s']}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
