"""nyiso-232 phase 0 (ZERO LP): exact ST_GAS offer-array delta for the band repair.

Rebuilds the designated keeper's fleet on its own recipe via the SANCTIONED
``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``), once as the CONTROL and once with the
candidate ``ST_GAS`` band substitution applied to ``offer_curve_by_group``,
and diffs the assembled P0 marginal-cost array row-for-row.

Answers, for the PRECOMMIT and before any solve (rule 29 ``[R-SCREEN]``
clause 0):

* which rows move, and whether ANY row outside NYISO ``ST_GAS`` econ bands does
  (the confinement claim);
* the exact $/MWh delta per band, and whether it is fuel-INVARIANT (which is
  what the ``gas_offer_net_revenue_margin`` decomposition predicts: the repair
  removes only ``markup_hr x anchor``, leaving ``phys x HR x fuel`` untouched);
* that ``pmax`` and ``availability`` are untouched (max|d| exactly 0).

Run: ``python3 scripts/probes/_nyiso232_st_gas_phase0.py <year> [<year> ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nyiso231_anchor_span")

# The candidate construction, declared here so the probe cannot be re-pointed
# silently: ST_GAS committed/econ_low/econ_high := the rule-25 NEUTRAL 1.0 band,
# the same remedy `_NYISO_OFFER_CURVE` applied to CC_REGULAR.econ_high (1.21 ->
# 1.00) and to CT_PEAKER.econ_low/econ_high in the SAME audit (C-13, B-NYI-1).
# `peak` AND `committed` are EXCLUDED, exactly as nyiso-199 excluded them on
# CT_PEAKER (whose registered state IS econ_low/econ_high 1.0 beside a non-neutral
# committed 1.35 and peak 4.0):
#   * `peak` 4.20 is the $1,000-offer-cap scarcity WALL the file states it as, not
#     the reach construction;
#   * `committed` 1.05 sits BELOW its own measured `phys_committed` 1.104, so its
#     markup clips to 0 in BOTH legs -- the leaked reach never reaches a margin
#     there. What the multiplier still does is scale FUEL, so moving it to 1.0
#     would price the steam min-load block 9.4 % below its own measured burn on no
#     ground at all. Measured in this probe's first pass: -$4.09/MWh, fuel-scaled.
ARM_ST_GAS = {"econ_low": 1.0, "econ_high": 1.0}


def build(year: int, arm: bool):
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))

    # `_NYISO_OFFER_CURVE` is deep-merged ON TOP of `config.offer_curve_by_group`
    # inside `backcast_config`, so the recipe kwarg cannot carry the arm — the
    # registry entry itself is what the gated field will edit, and it is what the
    # probe edits here, restoring it afterwards.
    import importlib

    _bc = importlib.import_module("market_sim.pipeline.backcast_config")

    saved = dict(_bc._NYISO_OFFER_CURVE["ST_GAS"])
    try:
        if arm:
            _bc._NYISO_OFFER_CURVE["ST_GAS"].update(ARM_ST_GAS)
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        _bc._NYISO_OFFER_CURVE["ST_GAS"].clear()
        _bc._NYISO_OFFER_CURVE["ST_GAS"].update(saved)


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2022]
    out: dict[str, dict] = {}
    for y in years:
        ctl = build(y, arm=False)
        arm = build(y, arm=True)
        res = compare(ctl, arm)
        out[str(y)] = res
        print(f"\n===== {y} =====")
        print(
            f"  rows {res['n_rows_ctl']} -> {res['n_rows_arm']}  "
            f"(ST_GAS {res['n_st_ctl']} -> {res['n_st_arm']}; "
            f"non-ST_GAS {res['n_other_ctl']} -> {res['n_other_arm']})"
        )
        print(
            f"  NON-ST_GAS offer max|d|     ${res['other_mc_maxabs']:.10f}/MWh  "
            f"(rows matched {res['other_matched']})"
        )
        print(f"  NON-ST_GAS pmax max|d|       {res['other_pmax_maxabs']:.10f} MW")
        print(
            f"  ST_GAS pmax total {res['st_pmax_ctl']:.4f} -> {res['st_pmax_arm']:.4f} MW  "
            f"(d {res['st_pmax_arm'] - res['st_pmax_ctl']:+.6f})"
        )
        print("  ST_GAS band composition:")
        for b in sorted(set(res["st_bands_ctl"]) | set(res["st_bands_arm"])):
            print(
                f"      {b:16s} ctl n={res['st_bands_ctl'].get(b, 0):3d}  "
                f"arm n={res['st_bands_arm'].get(b, 0):3d}"
            )
        print("  ST_GAS capacity-weighted mean offer $/MWh (over all hours):")
        print(
            f"      ctl ${res['st_cwmean_ctl']:8.4f}   arm ${res['st_cwmean_arm']:8.4f}   "
            f"d ${res['st_cwmean_arm'] - res['st_cwmean_ctl']:+8.4f}"
        )
        print("  ST_GAS per-band mean offer $/MWh:")
        for b, v in sorted(res["st_band_mean_ctl"].items()):
            print(f"      ctl {b:16s} ${v:9.4f}")
        for b, v in sorted(res["st_band_mean_arm"].items()):
            print(f"      arm {b:16s} ${v:9.4f}")
        print(
            f"  fuel-invariance of the ST_GAS econ delta: {res['econ_fuel_invariant_note']}"
        )

    dest = Path("results/calibration/_nyiso232_st_gas_phase0.json")
    dest.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {dest}")


def _rows(state):
    fa = state["fleet_arrays"]
    ids = [str(u) for u in fa.unit_ids]
    klass = [str(k) for k in fa.plant_group]
    return (
        ids,
        klass,
        np.asarray(fa.pmax),
        np.asarray(state["mc_base"]),
        np.asarray(state["fuel_prices"]),
    )


def compare(ctl, arm) -> dict:
    ic, kc, pc, mc, fc = _rows(ctl)
    ia, ka, pa, ma, fa_ = _rows(arm)

    st_c = [n for n, k in zip(ic, kc) if k == "ST_GAS"]
    st_a = [n for n, k in zip(ia, ka) if k == "ST_GAS"]

    # NON-ST_GAS confinement: match by unit id, compare offers and pmax.
    idx_c = {n: i for i, (n, k) in enumerate(zip(ic, kc)) if k != "ST_GAS"}
    idx_a = {n: i for i, (n, k) in enumerate(zip(ia, ka)) if k != "ST_GAS"}
    shared = sorted(set(idx_c) & set(idx_a))
    o_mc = max(
        (float(np.abs(ma[idx_a[n]] - mc[idx_c[n]]).max()) for n in shared), default=0.0
    )
    o_pm = max((float(abs(pa[idx_a[n]] - pc[idx_c[n]])) for n in shared), default=0.0)

    def band_of(uid: str) -> str:
        tail = uid.rsplit("_", 1)[-1]
        return "".join(ch for ch in tail if not ch.isdigit()) or tail

    def bands(ids, klass):
        d: dict[str, int] = {}
        for n, k in zip(ids, klass):
            if k == "ST_GAS":
                d[band_of(n)] = d.get(band_of(n), 0) + 1
        return d

    def cw(ids, klass, pmax, mcm):
        sel = [i for i, k in enumerate(klass) if k == "ST_GAS"]
        w = pmax[sel]
        if w.sum() <= 0:
            return 0.0
        return float((mcm[sel].mean(axis=1) * w).sum() / w.sum())

    def band_mean(ids, klass, mcm):
        acc: dict[str, list[float]] = {}
        for i, (n, k) in enumerate(zip(ids, klass)):
            if k == "ST_GAS":
                acc.setdefault(band_of(n), []).append(float(mcm[i].mean()))
        return {b: float(np.mean(v)) for b, v in acc.items()}

    # Fuel-invariance: for ST_GAS units present in BOTH legs under the same band
    # family, the margin mechanism predicts a constant $/MWh shift.
    note = "n/a (band families differ between legs)"
    cb, ab = bands(ic, kc), bands(ia, ka)
    common = set(cb) & set(ab) & {"committed", "peak"}
    if common:
        spreads = []
        for n in set(st_c) & set(st_a):
            if band_of(n) in common:
                dv = ma[ia.index(n)] - mc[ic.index(n)]
                spreads.append(float(dv.max() - dv.min()))
        if spreads:
            note = (
                f"{sorted(common)} rows: max within-row spread "
                f"{max(spreads):.10f} $/MWh over {len(spreads)} rows"
            )

    return {
        "n_rows_ctl": len(ic),
        "n_rows_arm": len(ia),
        "n_st_ctl": len(st_c),
        "n_st_arm": len(st_a),
        "n_other_ctl": len(ic) - len(st_c),
        "n_other_arm": len(ia) - len(st_a),
        "other_matched": len(shared),
        "other_mc_maxabs": o_mc,
        "other_pmax_maxabs": o_pm,
        "st_pmax_ctl": float(sum(pc[i] for i, k in enumerate(kc) if k == "ST_GAS")),
        "st_pmax_arm": float(sum(pa[i] for i, k in enumerate(ka) if k == "ST_GAS")),
        "st_bands_ctl": cb,
        "st_bands_arm": ab,
        "st_cwmean_ctl": cw(ic, kc, pc, mc),
        "st_cwmean_arm": cw(ia, ka, pa, ma),
        "st_band_mean_ctl": band_mean(ic, kc, mc),
        "st_band_mean_arm": band_mean(ia, ka, ma),
        "econ_fuel_invariant_note": note,
    }


if __name__ == "__main__":
    main()
