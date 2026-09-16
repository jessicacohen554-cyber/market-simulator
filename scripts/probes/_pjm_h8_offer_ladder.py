"""pjm-h8 phase 0 — PJM coal's COMMITTED band against PJM's OWN MEASURED offers. ZERO LP.

Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP.

THE QUESTION pjm-h6 AND pjm-h7 LEFT OPEN. pjm-h6 measured that raising PJM's COAL
``committed`` band from its registered 0.548 to the CAMPD ``avg_committed_p50`` 0.916
costs **26.318 TWh** of COAL_BIT; pjm-h7 measured that re-centring the bituminous
sigmoid recovers only **15.8 %** of it, and reported the remaining ~22 TWh as an
unidentified defect the registered band was "silently carrying".

**BOTH COMPARISONS WERE MADE AGAINST A COST BASIS.** ``avg_committed_p50`` is a measured
*operating heat rate* out of CAMPD — what a unit BURNS at min load. The parameter it was
compared to is a **BID** by its own declaration (``backcast_config.py`` calls these
price-calibrated multipliers, not literal heat rates; pjm-h5 measured that 10 of PJM's
11 registered classes sit below their ``avg_committed_p50`` and that the sign INVERTS on
the econ bands — a price-taking-min-load / marked-up-increment shape). A cost basis
cannot adjudicate a bid parameter, and no prior session in this chain used an offer one.

**THE OFFER BASIS ALREADY EXISTS, IS COMMITTED, AND THIS KEEPER ALREADY TRUSTS IT ONE
TRANCHE UP.** ``data/raw/_validation-source/pjm_offer_midcurve_condbinned.json`` is
derived from PJM DataMiner2's ``energy_market_offers`` feed (36 month-files, 2023-2025,
multipliers only — the prices carry a redistribution restriction), and
``pjm_offer_midcurve_conditional`` is ARMED on the keeper: it prices the mapped classes'
``econ*`` tranches, and the LONG_RUN classes' ``peak`` tranche, AT that measured level.
Its own docstring states the exclusion:

    "Committed / must-run / sync tranches are never touched (their pricing is owned by
     the coal take-or-pay/passthrough sigmoids and the commitment scaffolding)."

So PJM coal's ``committed`` block is **the one rung of its own offer stack that is not
disciplined by PJM's own published offers**, and it is exactly the rung h6/h7 fought over.

WHAT THIS PROBE DOES. For each band of PJM's coal stack it reports (a) the model's bid,
(b) the measured offer level **at that same row's own within-plant capacity share**, and
(c) the ratio — using the model's OWN ``_pjm_midcurve_context`` /
``_pjm_midcurve_row_target``, so the target is byte-for-byte the one the mechanism would
apply if the row were in scope. Nothing here is constructed by this probe, nothing is
swept, and no parameter is proposed: it measures a gap that is already implied by two
artifacts the keeper already carries (rule 1 ``[R-STRUCT]``, rule 21 ``[R-DOF]``).

The comparison is reported in **implied gas heat rate** (``price / delivered_gas_day``),
the measured artifact's own unit, so it is invariant to the delivered COAL price level
and to the entire pjm-170 / pjm-h7 sigmoid dispute (``gas_mid`` 3.40 vs 4.58 vs 7.08).

STATED LIMIT, not buried: ``mc_base`` is the **P0** base-cost array. The mid-curve
mechanism is P1-only, so the *econ/peak* rows below are shown BEFORE it prices them —
which is why they read cheap against measured and why only the ``committed``/``mustrun``
rows, which no P1 mechanism ever touches, carry a gap that survives into P1.

Run: ``python3 scripts/probes/_pjm_h8_offer_ladder.py 2023 2024 2025``
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

#: PJM's keeper is PARTITIONED (pjm-h7 §3): 2020-2022 solve the `pjm_d4_4_TP`
#: recipe, 2023-2025 the `pjm_d4_4_A` carve-out. Each year is built on its OWN
#: recipe. The MEASURED artifact covers 2023-2025, so those are the overlayable
#: years; 2020-2022 would read the surface's pooled fallback and are not run.
BUNDLE_FOR_YEAR = {
    2020: "pjm_d4_4_TP",
    2021: "pjm_d4_4_TP",
    2022: "pjm_d4_4_TP",
    2023: "pjm_d4_4_A",
    2024: "pjm_d4_4_A",
    2025: "pjm_d4_4_A",
}

COAL_CLASSES = ("COAL", "COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE")


def build(year: int) -> dict:
    """Build the keeper's fleet for *year* on its own recipe. ZERO LP."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    # Declared simplification inherited from pjm-h4 §2 / pjm-h6 §2 / pjm-h7 §3.
    # Here it is not even a diff: ONE leg per year is built and its shape read.
    kw["pjm_da_virtual_bids"] = False
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _suffix(unit_id: str) -> str:
    return unit_id.rsplit("_", 1)[-1]


def _band(unit_id: str) -> str:
    s = _suffix(unit_id)
    if s.startswith("econ"):
        return "econ"
    if s.startswith("peak"):
        return "peak"
    return s


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    out: dict = {
        "what": (
            "model bid vs PJM's OWN measured offer level at the same within-plant "
            "capacity share, in implied gas heat rate (price / delivered gas day)"
        ),
        "measured_source": "data/raw/_validation-source/pjm_offer_midcurve_condbinned.json",
        "years": {},
    }

    for y in years:
        t0 = time.time()
        res = build(y)
        cfg = res["config"]
        fleet = res["fleet"]
        mc = np.asarray(res["mc_base"], dtype=float)
        if mc.ndim == 1:
            mc = mc[:, None]

        from market_sim.data.fleet.offer_surfaces import (
            _PJM_MIDCURVE_SEGMENT_OF,
            _pjm_midcurve_context,
            _pjm_midcurve_row_target,
        )

        # The builder's OWN LP-served net-load convention, copied from its call
        # site (run_calibration.py::run_year) so the hour->bin mapping here is
        # identical to the armed mechanism's.
        net_load = (
            res["demand"].sum(axis=0)
            - (res["solar_cap"][:, None] * res["solar_cf"]).sum(axis=0)
            - (res["wind_cap"][:, None] * res["wind_cf"]).sum(axis=0)
        )

        # The model's OWN context: same surface file, same net-load binning, same
        # within-plant capacity-share ladder the armed mechanism uses. Built over
        # EVERY mapped segment so no row is excluded by a scope this probe chose.
        ctx = _pjm_midcurve_context(
            res["fleet_arrays"],
            fleet,
            mc,
            np.asarray(net_load, dtype=float),
            cfg,
            y,
            set(_PJM_MIDCURVE_SEGMENT_OF.values()),
        )
        gas = np.asarray(ctx.gas_day, dtype=float)

        df = pd.DataFrame(
            {
                "row": np.arange(len(fleet)),
                "unit_id": [g.unit_id for g in fleet],
                "group": [g.efficiency_bin for g in fleet],
                "cap": [float(g.pmax_mw) for g in fleet],
                "band": [_band(g.unit_id) for g in fleet],
            }
        )
        share_of = {g: s for g, s, _sfx, _seg in ctx.rows}
        seg_of = {g: seg for g, _s, _sfx, seg in ctx.rows}

        # Model bid and measured target, per row, in implied-gas-HR units.
        model_hr = np.full(len(df), np.nan)
        meas_hr = np.full(len(df), np.nan)
        for g in df["row"].to_numpy():
            model_hr[g] = float(np.median(mc[g, :] / gas))
            seg = seg_of.get(g)
            if seg is None or seg not in ctx.tables:
                continue
            tgt = _pjm_midcurve_row_target(ctx, seg, share_of[g])
            meas_hr[g] = float(np.nanmedian(tgt / gas))
        df["share"] = [share_of.get(g, np.nan) for g in df["row"]]
        df["segment"] = [seg_of.get(g) for g in df["row"]]
        df["model_hr"] = model_hr
        df["meas_hr"] = meas_hr

        def capwtd(sub: pd.DataFrame, col: str) -> float:
            ok = sub[np.isfinite(sub[col])]
            if ok.empty or ok["cap"].sum() == 0:
                return float("nan")
            return float((ok[col] * ok["cap"]).sum() / ok["cap"].sum())

        def band_table(sub: pd.DataFrame) -> dict:
            bands: dict = {}
            for b, s in sub.groupby("band"):
                m, q = capwtd(s, "model_hr"), capwtd(s, "meas_hr")
                bands[str(b)] = {
                    "mw": float(s["cap"].sum()),
                    "n_rows": int(len(s)),
                    "share_capwtd": capwtd(s, "share"),
                    "model_implied_gas_hr": m,
                    "measured_implied_gas_hr": q,
                    "model_over_measured": (
                        float(m / q) if q and np.isfinite(q) else None
                    ),
                    "priced_by_midcurve_in_P1": bool(b in ("econ", "peak")),
                }
            return bands

        have = df["share"].notna()
        # COAL and ST_GAS are the two model classes inside the measured LONG_RUN
        # segment. Reporting them SEPARATELY is the control for the one confound
        # that could manufacture this result: the measured segment is coal PLUS
        # gas-steam, and gas-steam bids dearer, so a coal-only comparison against
        # a blended ladder is biased high. If the band-to-band PATTERN repeats in
        # ST_GAS, the pattern cannot be the admixture (which is common to every
        # share of one segment and so cannot bend one band and not another).
        views = {
            "COAL": df[have & df["group"].isin(COAL_CLASSES)],
            "ST_GAS": df[have & (df["group"] == "ST_GAS")],
            "CC_REGULAR": df[have & (df["group"] == "CC_REGULAR")],
            "CT_PEAKER": df[have & (df["group"] == "CT_PEAKER")],
        }
        coal = views["COAL"]

        yr = {
            "bundle": BUNDLE_FOR_YEAR[y],
            "gas_mean": float(gas.mean()),
            "coal_mw": float(coal["cap"].sum()),
            "year_tables": sorted(ctx.year_tables),
            "bands": band_table(coal),
            "by_class": {k: band_table(v) for k, v in views.items()},
        }
        yr["elapsed_s"] = round(time.time() - t0, 1)
        out["years"][str(y)] = yr

        print(
            f"\n[{y}]  built {yr['elapsed_s']}s  gas_mean={yr['gas_mean']:.3f}  "
            f"coal {yr['coal_mw']:.0f} MW  year_tables={yr['year_tables']}"
        )
        for cls, bands in yr["by_class"].items():
            print(f"  -- {cls} --")
            print(
                f"   {'band':<10}{'MW':>9}{'share':>7}{'model':>9}{'measured':>10}"
                f"{'mod/meas':>10}   P1-priced?"
            )
            for b in ("mustrun", "committed", "econ", "peak"):
                if b not in bands:
                    continue
                r = bands[b]
                mo = r["model_over_measured"]
                print(
                    f"   {b:<10}{r['mw']:>9.0f}{r['share_capwtd']:>7.3f}"
                    f"{r['model_implied_gas_hr']:>9.3f}"
                    f"{r['measured_implied_gas_hr']:>10.3f}"
                    f"{(f'{mo:.3f}' if mo else '   -   '):>10}   "
                    f"{'YES (midcurve)' if r['priced_by_midcurve_in_P1'] else 'NO -- excl'}"
                )

    dest = REPO / "results/calibration/_pjm_h8_offer_ladder.json"
    # MERGE, never overwrite (pjm-h7 §"two repo defects"): a run over a SUBSET of
    # years must not clobber a fuller artifact already at this fixed path.
    if dest.exists():
        try:
            prior = json.loads(dest.read_text())
        except json.JSONDecodeError:
            prior = {}
        merged = dict(prior.get("years") or {})
        merged.update({str(k): v for k, v in out["years"].items()})
        out["years"] = merged
    dest.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {dest.relative_to(REPO)} (years {sorted(out['years'])})")


if __name__ == "__main__":
    main()
