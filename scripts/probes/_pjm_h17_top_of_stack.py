"""pjm-h17 phase 0 — is PJM's price gap a TOP-OF-CURVE defect? ZERO LP.

Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP.

THE LANE'S PROPOSED LEVER was "read the MEASURED TOP of the offer curve,
conditioned on tightness" — extend the armed mid-curve surface to the
``peak*`` rungs it excludes (``ScenarioConfig.pjm_offer_midcurve_peak_segments``,
which already exists and is default-off).

THE THREE THINGS THAT HAVE TO BE TRUE for such a lever to re-slope the stack,
each measured here against the keeper's OWN committed artifacts and its OWN
fleet build:

  (A) the measured top belt must sit ABOVE the model's fitted peak band
      (a LEVEL-form replacement that lowers the rung cannot lift a tail);
  (B) the peak rungs must actually CLEAR in the hours the model is short
      (a row that never sets the dual cannot move it — the pjm-99 inertness
      result, re-measured on the current keeper); and
  (C) the model must be CAPACITY-TIGHT in the market's high-price hours
      (if the clearing point never reaches the top of the stack, repricing
      the top of the stack is inert by construction).

Reported with AVAILABILITY-AWARE headroom: ``cap x availability[g, t]`` per
hour from the model's own FleetArrays, never a max-over-year proxy, so an
"idle" MW is one the LP could actually have dispatched in that hour.

Nothing here is swept, nothing is proposed, and no parameter is constructed:
every number is either a committed sidecar or the keeper's own fleet build
(rule 1 ``[R-STRUCT]``, rule 21 ``[R-DOF]``).

Run: ``python3 scripts/probes/_pjm_h17_top_of_stack.py 2023 2024 2025``
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPO = Path(__file__).resolve().parents[2]

#: The current keeper is ONE recipe over 2023-2025 (span) plus a folded touchpoint
#: bundle over 2020-2022. Only the measured years are overlaid here.
BUNDLE_FOR_YEAR = {
    2020: "pjm_h15_coalwindow_touchpoint",
    2021: "pjm_h15_coalwindow_touchpoint",
    2022: "pjm_h15_coalwindow_touchpoint",
    2023: "pjm_h15_coalwindow_span",
    2024: "pjm_h15_coalwindow_span",
    2025: "pjm_h15_coalwindow_span",
}

NONDISP = {
    "wind",
    "solar",
    "nuclear",
    "hydro",
    "import",
    "biomass",
    "VIRTUAL_INC",
    "VIRTUAL_DEC",
    "OTHER",
    "storage",
}

#: The fleet build's ``efficiency_bin`` vocabulary and the committed sidecar's
#: ``klass`` (``klass_base`` in the unit-hour frame) are NOT the same alphabet,
#: and joining them naively manufactures phantom headroom. Measured at PJM 2024:
#: ``efficiency_bin`` carries ONE ``COAL`` bin (521 rows, 49,371.7 MW) which the
#: sidecar splits by rank into COAL_BIT / COAL_PRB / COAL_WC, and a ``default``
#: bin (691 rows, 58,106 MW) that is oil (507) + import (80) + hydro (72) +
#: nuclear (32) — three of which are already in NONDISP under their sidecar
#: names. Left unmapped those two bins read 0 % utilised and inflate "idle" by
#: ~62 GW. The fleet side is therefore keyed by ``Generator.fuel_type`` for the
#: coal roll-up and the ``default`` split, never by the bin label.
COAL_SIDECAR_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE", "COAL")


def build(year: int) -> dict:
    """Build the keeper's fleet for *year* on its own recipe. ZERO LP."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    kw["pjm_da_virtual_bids"] = False  # declared simplification, pjm-h8 §2
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _suffix(unit_id: str) -> str:
    return unit_id.rsplit("_", 1)[-1]


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
    )
    out: dict = {"what": __doc__.splitlines()[0], "years": {}}

    for y in years:
        t0 = time.time()
        res = build(y)
        cfg, fleet = res["config"], res["fleet"]
        fa = res["fleet_arrays"]
        mc = np.asarray(res["mc_base"], dtype=float)
        if mc.ndim == 1:
            mc = mc[:, None] * np.ones((1, 8760))

        from market_sim.data.fleet.offer_surfaces import (
            _PJM_MIDCURVE_SEGMENT_OF,
            _pjm_midcurve_context,
            _pjm_midcurve_row_target,
        )

        net_load = (
            res["demand"].sum(axis=0)
            - (res["solar_cap"][:, None] * res["solar_cf"]).sum(axis=0)
            - (res["wind_cap"][:, None] * res["wind_cf"]).sum(axis=0)
        )
        ctx = _pjm_midcurve_context(
            fa,
            fleet,
            mc,
            np.asarray(net_load, float),
            cfg,
            y,
            set(_PJM_MIDCURVE_SEGMENT_OF.values()),
        )
        gas = np.asarray(ctx.gas_day, float)
        share_of = {g: s for g, s, _sfx, _seg in ctx.rows}
        seg_of = {g: seg for g, _s, _sfx, seg in ctx.rows}

        pmax = np.asarray(fa.pmax, float)
        avail = np.asarray(fa.availability, float)
        if avail.ndim == 1:
            avail = avail[:, None] * np.ones((1, mc.shape[1]))
        klass = np.array([g.efficiency_bin for g in fleet])
        sfx = np.array([_suffix(g.unit_id) for g in fleet])

        # Market's top-1% hours, the lane's own window.
        a = act[act.year == y].sort_values("hour")["rt"].to_numpy(float)
        hi = np.argsort(a)[-88:]

        fuel = np.array([str(getattr(g, "fuel_type", "")) for g in fleet])
        # Dispatchable thermal ONLY: coal + gas + oil, by FUEL, so the
        # ``default`` bin's import/hydro/nuclear rows are excluded by what they
        # are rather than by a bin label that does not describe them.
        disp = np.isin(fuel, ["coal", "gas_cc", "gas_ct", "gas_st", "oil"])
        av_cap = pmax[:, None] * avail  # (n_gen, T)
        yr: dict = {
            "bundle": BUNDLE_FOR_YEAR[y],
            "gas_mean": float(gas.mean()),
            "market_top1pct_mean_lmp": float(a[hi].mean()),
        }

        # (A) measured belt vs model fitted bid, PEAK rungs only.
        rows_a = {}
        for k in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT"):
            sel = np.where(disp & (klass == k) & np.char.startswith(sfx, "peak"))[0]
            if sel.size == 0:
                continue
            mdl, mea, cw = [], [], []
            for g in sel:
                seg = seg_of.get(g)
                if seg is None or seg not in ctx.tables:
                    continue
                tgt = _pjm_midcurve_row_target(ctx, seg, share_of[g])
                mdl.append(float(np.median(mc[g, :] / gas)))
                mea.append(float(np.nanmedian(tgt / gas)))
                cw.append(float(pmax[g]))
            if not cw:
                continue
            cw = np.array(cw)
            mdl = np.array(mdl)
            mea = np.array(mea)
            rows_a[k] = {
                "mw": float(cw.sum()),
                "model_implied_gas_hr": float((mdl * cw).sum() / cw.sum()),
                "measured_implied_gas_hr": float((mea * cw).sum() / cw.sum()),
                "measured_over_model": float((mea * cw).sum() / (mdl * cw).sum()),
            }
        yr["A_peak_rung_model_vs_measured"] = rows_a

        # (B)/(C) availability-aware headroom in the market's top-1% hours.
        b = pd.read_parquet(
            REPO / f"results/calibration/{BUNDLE_FOR_YEAR[y]}/hourly"
            f"/class_band_hourly_{y}.parquet"
        )
        b = b[b["pass"] == "P1"]
        used_by_class = (
            b[~b.klass.isin(NONDISP)]
            .pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
            .fillna(0.0)
            .sort_index()
        )
        per_class = {}
        # Fleet bin -> the sidecar class(es) that carry its dispatch.
        bins = sorted(set(klass[disp]))
        for k in bins:
            sel = np.where(disp & (klass == k))[0]
            av = av_cap[sel][:, hi].sum(axis=0).mean()
            if k == "COAL":
                cols = [c for c in COAL_SIDECAR_CLASSES if c in used_by_class.columns]
            elif k == "default":
                # Only the oil rows of this bin are dispatchable thermal; the
                # sidecar carries them under the pooled ``oil`` class.
                cols = [c for c in ("oil",) if c in used_by_class.columns]
            else:
                cols = [c for c in (k,) if c in used_by_class.columns]
            us = used_by_class[cols].sum(axis=1).to_numpy()[hi].mean() if cols else 0.0
            if av < 200:
                continue
            per_class[k] = {
                "available_mw": float(av),
                "dispatched_mw": float(us),
                "idle_mw": float(av - us),
                "utilisation": float(us / av) if av else None,
                "sidecar_classes": cols,
            }
        yr["C_headroom_market_top1pct"] = per_class
        yr["C_total"] = {
            "available_mw": float(sum(v["available_mw"] for v in per_class.values())),
            "dispatched_mw": float(sum(v["dispatched_mw"] for v in per_class.values())),
            "idle_mw": float(sum(v["idle_mw"] for v in per_class.values())),
        }
        # (B) peak-rung dispatch over the WHOLE year, from the sidecar.
        pk = (
            b[b.band.str.startswith("peak")].groupby("klass")["mw"].agg(["max", "mean"])
        )
        yr["B_peak_band_dispatch_mw"] = {
            str(k): {"max_h": float(r["max"]), "mean_h": float(r["mean"])}
            for k, r in pk.iterrows()
        }
        yr["build_s"] = round(time.time() - t0, 1)
        out["years"][str(y)] = yr
        print(f"[{y}] built in {yr['build_s']}s", flush=True)

    dest = REPO / "results/calibration/_pjm_h17_top_of_stack.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
