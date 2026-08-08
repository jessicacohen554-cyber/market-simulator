"""miso-143 gate G-A1 / G-A2 — the PRICE-ANCHORED offer ladder and the
MERIT-ORDER GAIN (PREREG P3, P4, P5, P8), under BRANCH-INSTRUMENT-FAIL.

**Why this instrument and not the one G-A0 tried.**  The pre-registered footing
gate (``_miso143_footing.py``, P1) **FAILED**: a copperplate merit-order clear
of the rebuilt stack against the model's own hourly thermal requirement
under-prices the keeper's committed P1 price by **~$9-13/MWh** in every year and
both windows, at a median |Δ| of ~$9.7-10.0 against a $4.00 bar fixed in
advance.  The startup-markup bracket moves it by $0.25.  The PREREG named this
outcome, fixed its bar before the number was seen, and pre-committed the
landing place:

> **BRANCH-INSTRUMENT-FAIL** — the stack is not trustworthy for **levels**.
> Report **gaps only** (differences survive a level bias that points cannot),
> give the gain as a **bound** with its own caveat.

**The bar is NOT moved and the failed reading is NOT discarded** — it is
reported at full magnitude in the finding.  What changes is the *construction*:
this probe never reconstructs a clearing quantity at all.  It anchors the
ladder at the keeper's **OWN committed P1 price** (a committed artifact) and
measures only **differences above that anchor** — which is what the merit-order
channel is made of, and what a level bias cannot corrupt.

**§1 also tests WHY the footing failed**, so a failed gate becomes a finding
rather than a shrug: the copperplate hypothesis (a system-wide merit order
over-uses cheap capacity that MISO's zonal network cannot actually deliver, so
the true marginal unit sits higher up the stack) predicts the under-price grows
with the hour's zonal price spread.  Measured, not asserted.

**THE MEASUREMENTS**

*G-A1(a)* — SRMC distribution of the **coal tranches marginal at the anchor**
(offer within a band below the hour's own P1 price).

*G-A1(b)* — SRMC of the **gas tranches immediately above** them, in the same
hour: the next rungs of the same ladder.

*G-A2 / P5* — the **true within-hour ladder slope** above the anchor, at +1 /
+2 / +5 GW.  This is a NEW instrument: miso-142's binned curve is *empirical*
and mixes hours with different availability and fuel, so the two can disagree
and the disagreement would itself be the finding.  **P5 is two-sided.**

*G-A1(c) / P4* — **THE HEADLINE GAIN.**  Displace ``D`` MW of in-merit coal and
let the ladder above the anchor re-absorb it at constant thermal quantity;
``Δ = P' − P``.  ``D`` is set by the **MEASURED** fuel-mix miss, never by the
price residual (TRAP 6): the scorer's own C2-2025 coal excess **+4.2 %** is the
headline, and miso-142's EIA-930 hourly read **+14.6 %** is carried as a
**separately-labelled** second endpoint — two named instruments, never one
mixed number (TRAP 3).

**TWO REPLACEMENT-SUPPLY BOUNDS, because the direction of bias decides a
branch.**  Above-anchor *capability* overstates what is really available (the
copperplate surplus the footing gate just exposed), which biases Δ **DOWN** —
conservative for a MATERIAL verdict but **anti-conservative for a CLOSE**.  So
both are reported:

* ``cap`` — replacement supply = raw above-anchor capability.  **Lower bound
  on Δ.**
* ``idle`` — that capability scaled by each class's OWN measured idle fraction
  (class capability − class P1 dispatch, from the keeper's sidecar).  **Upper
  bound on Δ.**

A branch that is the same at both bounds stands on either; one that is not is
called on the conservative side and said so.

Usage::

    .venv/bin/python scripts/probes/_miso143_ladder.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import (  # noqa: E402
    COAL_COLS,
    GAS_COLS,
    HOURS,
    THERMAL_COLS,
    YEARS,
    KEEPER,
    fleet_state,
    hygiene,
    klass_of,
    markup_ceiling,
    sidecar_classes,
    sidecar_price,
    windows,
)

OUT = REPO / "results/calibration/_miso143_ladder.json"

# The measured displacement sizes -- BOTH from measured fuel-mix misses, and
# each labelled with its own instrument (TRAP 3: never averaged, never mixed).
DISPLACEMENTS = {
    # The SCORER's own C2 basis (EIA-923).  2025 coal +4.2 %; the 2023/2024
    # rows are the same criterion's readings in those years.
    "c2_eia923": {2023: -0.024, 2024: -0.023, 2025: +0.042},
    # miso-142's EIA-930 hourly read in W1 2025.  Carried for 2025 ONLY --
    # inventing 2023/2024 companions it never measured would be fabrication.
    "eia930_w1_2025": {2025: +0.146},
}
# Band below the anchor within which a tranche counts as "marginal" (a price
# band, not a quantity threshold; reported at three widths so the answer is not
# an artifact of one).
MARGINAL_BANDS = (2.0, 5.0, 10.0)
LADDER_GW = (1.0, 2.0, 5.0)
# miso-142 §3's MODEL-side empirical binned-curve slopes ($/MWh per GW), per
# (year, window), transcribed from its committed table.  P5 compares this
# session's within-hour LADDER against the SAME SIDE's empirical curve -- model
# vs model, one instrument against another (never against the actual-side
# curve, which would be a basis crossing, TRAP 3).
MISO142_EMPIRICAL_SLOPE = {
    (2023, "W1_jun_jul_h8_20"): 0.507,
    (2023, "JJA_h12_17"): 0.583,
    (2024, "W1_jun_jul_h8_20"): 0.447,
    (2024, "JJA_h12_17"): 0.491,
    (2025, "W1_jun_jul_h8_20"): 0.635,
    (2025, "JJA_h12_17"): 0.637,
}


def _ladder(
    offer: np.ndarray, cap: np.ndarray, anchor: float, rows: np.ndarray | None = None
) -> tuple:
    """Sorted (offer, cumulative capability) strictly ABOVE ``anchor``.

    ``rows`` optionally restricts the ladder to a sub-population (e.g. the gas
    rows for G-A1(b)).  The restriction DROPS the other rows outright rather
    than pricing them at infinity: an infinity that survives into a percentile
    is indistinguishable from a real answer, and a sub-population ladder that
    runs out must say so through ``_price_at``'s ``reachable`` flag, never
    through a sentinel that looks like a number.
    """
    sel = offer > anchor
    if rows is not None:
        sel = sel & rows
    o, c = offer[sel], cap[sel]
    k = np.argsort(o, kind="stable")
    return o[k], np.cumsum(c[k])


def _price_at(o: np.ndarray, cum: np.ndarray, mw: float, anchor: float) -> tuple:
    """Offer level reached after absorbing ``mw`` up the ladder.

    Returns ``(price, reachable)``.  ``reachable`` is False when the ladder
    above the anchor does not hold ``mw`` at all, in which case the ladder's
    own top is returned -- never an extrapolation (a flat model must not be
    credited with a tail it never reaches).
    """
    if o.size == 0:
        return anchor, False
    j = int(np.searchsorted(cum, mw, side="left"))
    if j >= o.size:
        return float(o[-1]), False
    return float(o[j]), True


def year_block(year: int) -> dict:
    st = fleet_state(year)
    gens, fa = st["fleet"], st["fleet_arrays"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    mk = markup_ceiling(gens, fa, st["config"])
    cap = fa.pmax[:, None] * fa.availability
    kl = klass_of(gens)

    # TRAP 5 -- every class read here must be non-empty in the FLEET.
    for k in ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"):
        assert (kl == k).sum() > 0, f"class {k!r} has ZERO fleet rows (TRAP 5)"
    is_coal = kl == "COAL"
    is_gas = np.isin(kl, list(GAS_COLS))

    piv = sidecar_classes(year)
    thermal = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
    coal_disp = piv[list(COAL_COLS)].sum(axis=1).to_numpy(float)
    price, _ = sidecar_price(year)

    # ---- P8: the EFFECTIVE fuel passthrough carried in the offer ----------
    # (offer - VOM) / (heat_rate x delivered fuel).  MISO carries no carbon or
    # NOx price in this keeper, which is ASSERTED rather than assumed -- if it
    # ever did, this identity would silently mis-attribute the adder to fuel.
    cfg = st["config"]
    assert not float(getattr(cfg, "nox_price", 0.0) or 0.0), "NOx price nonzero"
    fp = np.asarray(st["fuel_prices"], dtype=float)
    den = fa.heat_rate[:, None] * fp
    pt = np.divide(
        mc0 - fa.vom[:, None], den, out=np.full_like(mc0, np.nan), where=den > 1e-9
    )

    # ---- per-class measured IDLE fraction, for the `idle` bound ------------
    # class capability comes from the rebuilt fleet; class dispatch from the
    # keeper's own sidecar.  TRAP 4: the coal alias is explicit and asserted.
    def class_idle_frac(hrs: np.ndarray) -> dict:
        out = {}
        for k in sorted(set(kl.tolist())):
            rows = kl == k
            if not rows.any():
                continue
            cols = COAL_COLS if k == "COAL" else ((k,) if k in piv.columns else ())
            if not cols:
                continue
            capability = float(cap[rows][:, hrs].sum())
            disp = float(sum(piv[c].to_numpy(float)[hrs].sum() for c in cols))
            out[k] = float(np.clip(1.0 - disp / max(1e-9, capability), 0.0, 1.0))
        return out

    # The measured actual price, on miso-137's VERIFIED instrument, reused not
    # rebuilt (DO-NOT-REDO: no third derivation of the *_lw comparator).  Used
    # ONLY as the target level for the "GW to reach the actual price" reading;
    # every other number in this probe is model-only.
    from _miso137_c3a_gap_decomposition import actual_hourly, model_hourly

    rt_actual, _da = actual_hourly(year)
    _h, _p, w_model, _z = model_hourly(year)

    yr: dict = {"n_gen": len(gens)}
    for wname, sel in windows().items():
        ok = sel & np.isfinite(price) & np.isfinite(thermal) & (thermal > 0)
        hrs = np.nonzero(ok)[0]
        # BOTH sides load-weighted over hours, on the model's own demand --
        # C3a's own basis.  Mixing a load-weighted actual against an unweighted
        # model mean would be a basis crossing inside a single subtraction
        # (TRAP 3), which is exactly the kind of quiet error this lane's method
        # bars exist to catch.
        _af = np.isfinite(rt_actual[hrs])
        _w = w_model[hrs]
        actual_lw = float(
            (rt_actual[hrs][_af] * _w[_af]).sum() / max(1e-9, _w[_af].sum())
        )
        model_lw = float((price[hrs] * _w).sum() / max(1e-9, _w.sum()))
        # The same weight is used for every window mean below, so the gain and
        # the deficit it is compared against are on ONE basis.
        wgt = _w / max(1e-9, _w.sum())
        idle = class_idle_frac(hrs)
        idle_vec = np.array([idle.get(k, 0.0) for k in kl], dtype=float)

        blk: dict = {
            "n_hours": int(hrs.size),
            "anchor_lw_price": round(model_lw, 3),
            "actual_lw_price": round(actual_lw, 3),
            "deficit_usd_per_mwh": round(model_lw - actual_lw, 3),
            "mean_thermal_mw": round(float(np.mean(thermal[hrs])), 1),
            "class_idle_frac": {k: round(v, 4) for k, v in sorted(idle.items())},
        }

        for tag, off in (("lo", mc0), ("hi", mc0 + mk[:, None])):
            marg_coal_srmc: list[float] = []
            marg_coal_mw: list[float] = []
            gas_above: dict[float, list[float]] = {g: [] for g in LADDER_GW}
            slope: dict[float, list[float]] = {g: [] for g in LADDER_GW}
            band_counts = {b: 0 for b in MARGINAL_BANDS}
            band_mw = {b: [] for b in MARGINAL_BANDS}
            gains: dict[str, list[float]] = {}
            passthrough: list[float] = []
            gas_unreached = {g: 0 for g in LADDER_GW}
            gw_to_actual: list[float] = []
            gw_to_actual_unreached = 0
            below: list[float] = []

            for t in hrs:
                o_t, c_t, a = off[:, t], cap[:, t], float(price[t])

                # ---- G-A1(a): coal tranches marginal AT THE ANCHOR --------
                for b in MARGINAL_BANDS:
                    m = is_coal & (o_t <= a) & (o_t >= a - b) & (c_t > 0)
                    band_counts[b] += int(m.sum())
                    band_mw[b].append(float(c_t[m].sum()))
                m2 = is_coal & (o_t <= a) & (o_t >= a - MARGINAL_BANDS[1]) & (c_t > 0)
                if m2.any():
                    marg_coal_srmc.append(
                        float(np.average(o_t[m2], weights=c_t[m2]))
                    )
                    marg_coal_mw.append(float(c_t[m2].sum()))
                    # P8 -- effective fuel passthrough of the MARGINAL coal,
                    # read back out of the OFFER ITSELF rather than from the
                    # input parameter: (offer - VOM) / (HR x delivered fuel).
                    # That measures what the tranche actually bids, which is
                    # the quantity the merit order responds to.
                    passthrough.append(
                        float(np.average(pt[m2, t], weights=c_t[m2]))
                    )

                # ---- G-A1(b) + G-A2: the ladder ABOVE the anchor ----------
                o_up, cum_up = _ladder(o_t, c_t, a)
                o_g, cum_g = _ladder(o_t, c_t, a, rows=is_gas)
                for g in LADDER_GW:
                    p_up, _ = _price_at(o_up, cum_up, g * 1000.0, a)
                    slope[g].append((p_up - a) / g)
                    p_gas, ok_gas = _price_at(o_g, cum_g, g * 1000.0, a)
                    if ok_gas:
                        gas_above[g].append(p_gas)
                    else:
                        gas_unreached[g] += 1

                # ---- miso-142's arithmetic, REDONE on the true ladder -----
                # How many GW up the model's OWN within-hour ladder does it
                # take to reach the window's measured actual price?  miso-142
                # asked this of its EMPIRICAL binned curve; the two instruments
                # are on the same side (the model) and may disagree, which is
                # exactly what P5 tests.
                j = int(np.searchsorted(o_up, actual_lw, side="left"))
                if j < o_up.size:
                    gw_to_actual.append(float(cum_up[j]) / 1000.0)
                else:
                    gw_to_actual_unreached += 1

                # ---- WHY the G-A0 footing failed: cheap IDLE capability ---
                # Capability offered AT OR BELOW the model's own clearing
                # price, against the thermal MW actually served.  A large
                # excess means the model is NOT clearing merit-order -- cheap
                # capability sits idle below its own price -- which is what a
                # copperplate clear cannot see and is the alternative to the
                # (refuted) congestion story.
                below.append(float(c_t[o_t <= a].sum()))

                # ---- G-A1(c): the merit-order GAIN, both bounds -----------
                for dname, dmap in DISPLACEMENTS.items():
                    if year not in dmap or dmap[year] <= 0:
                        continue
                    frac = dmap[year] / (1.0 + dmap[year])  # excess -> removal
                    D = float(coal_disp[t]) * frac
                    for bound, cc in (
                        ("cap", c_t),
                        ("idle", c_t * idle_vec),
                    ):
                        # Replacement supply excludes coal (it is what is being
                        # displaced) -- the substitution is coal -> everything
                        # else, and in this stack that is overwhelmingly gas.
                        sup = np.where(is_coal, 0.0, cc)
                        o_r, cum_r = _ladder(o_t, sup, a)
                        p_new, reach = _price_at(o_r, cum_r, D, a)
                        gains.setdefault(f"{dname}|{bound}", []).append(
                            p_new - a if reach else p_new - a
                        )
                        gains.setdefault(f"{dname}|{bound}|reach", []).append(
                            1.0 if reach else 0.0
                        )

            def _m(x):
                """Load-weighted window mean, on C3a's own weight (see above).

                Falls back to the unweighted mean only when the series is
                shorter than the window (a sub-population that is absent in
                some hours, e.g. the marginal-coal SRMC), where the C3a weight
                does not align row-for-row.
                """
                if not len(x):
                    return None
                if len(x) == wgt.size:
                    return round(float(np.dot(np.asarray(x, dtype=float), wgt)), 4)
                return round(float(np.mean(x)), 4)

            blk[tag] = {
                "marginal_coal": {
                    "srmc_mean_usd_mwh": _m(marg_coal_srmc),
                    "mw_mean": _m(marg_coal_mw),
                    "hours_with_marginal_coal": len(marg_coal_srmc),
                    "hours_share": round(len(marg_coal_srmc) / max(1, hrs.size), 4),
                    "band_tranche_counts": {
                        str(b): band_counts[b] for b in MARGINAL_BANDS
                    },
                    "band_mw_mean": {
                        str(b): _m(band_mw[b]) for b in MARGINAL_BANDS
                    },
                    "p8_effective_fuel_passthrough": _m(passthrough),
                },
                "gas_srmc_above_anchor": {
                    f"+{int(g)}GW": _m(gas_above[g]) for g in LADDER_GW
                },
                "gas_ladder_unreached_hours": {
                    f"+{int(g)}GW": gas_unreached[g] for g in LADDER_GW
                },
                "p3_srmc_gap_gas_minus_coal": (
                    round(_m(gas_above[1.0]) - _m(marg_coal_srmc), 4)
                    if marg_coal_srmc and gas_above[1.0]
                    else None
                ),
                "p5_ladder_slope_usd_per_gw": {
                    f"+{int(g)}GW": _m(slope[g]) for g in LADDER_GW
                },
                "p5_miso142_empirical_slope": MISO142_EMPIRICAL_SLOPE[
                    (year, wname)
                ],
                "p5_vs_miso142_empirical_ratio": (
                    round(
                        _m(slope[1.0]) / MISO142_EMPIRICAL_SLOPE[(year, wname)], 4
                    )
                    if slope[1.0]
                    else None
                ),
                "gw_up_ladder_to_reach_actual_price": {
                    "target_usd_mwh": round(actual_lw, 3),
                    "mean_gw": _m(gw_to_actual),
                    "median_gw": (
                        round(float(np.median(gw_to_actual)), 4)
                        if gw_to_actual
                        else None
                    ),
                    "unreached_hours": gw_to_actual_unreached,
                    "reached_hours": len(gw_to_actual),
                },
                "footing_failure_diagnostic": {
                    "capability_at_or_below_anchor_mw": _m(below),
                    "thermal_served_mw": round(float(np.mean(thermal[hrs])), 1),
                    "excess_cheap_capability_mw": (
                        round(_m(below) - float(np.mean(thermal[hrs])), 1)
                        if below
                        else None
                    ),
                },
                "p4_gain_usd_per_mwh": {
                    k: _m(v) for k, v in gains.items() if not k.endswith("|reach")
                },
                # 2023/2024 are EMPTY BY MEASUREMENT, not by omission: on the
                # scorer's own C2 basis the model UNDER-runs coal in both
                # (-2.4 %, -2.3 %), so the displacement reverses sign and a
                # coal->gas substitution is not the counterfactual there at
                # all.  That the over-run exists ONLY in 2025 is the object.
                "p4_displacement_direction": {
                    k: ("coal OVER-run -> displace to gas" if v.get(year, 0) > 0
                        else "coal UNDER-run -> no coal->gas displacement"
                        if year in v
                        else "not measured for this year")
                    for k, v in DISPLACEMENTS.items()
                },
                "p4_gain_reachable_frac": {
                    k.replace("|reach", ""): _m(v)
                    for k, v in gains.items()
                    if k.endswith("|reach")
                },
            }
        yr[wname] = blk
    return yr


def congestion_diagnostic(year: int) -> dict:
    """WHY the G-A0 footing failed — the copperplate hypothesis, measured.

    A system-wide merit order over-uses cheap capacity MISO's zonal network
    cannot actually deliver, so the LP's true marginal unit sits higher up the
    stack than a copperplate clear puts it.  That predicts the under-price
    GROWS with the hour's zonal price spread.  Measured on the keeper's own
    committed per-zone P1 prices; asserted nowhere.
    """
    foot = json.loads(
        (REPO / "results/calibration/_miso143_footing.json").read_text()
    )
    df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    if "pass" in df:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    spread = (
        df.groupby("hour")["price"].max() - df.groupby("hour")["price"].min()
    ).reindex(range(HOURS)).to_numpy(float)

    st = fleet_state(year)
    gens, fa = st["fleet"], st["fleet_arrays"]
    mc0 = np.asarray(st["mc_base"], dtype=float)
    cap = fa.pmax[:, None] * fa.availability
    piv = sidecar_classes(year)
    thermal = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
    price, _ = sidecar_price(year)

    from _miso143_stack import clear_many

    sel = windows()["JJA_h12_17"]
    ok = sel & np.isfinite(price) & np.isfinite(thermal) & (thermal > 0)
    hrs = np.nonzero(ok)[0]
    p_hat, _row = clear_many(mc0, cap, thermal[hrs], hrs)
    under = price[hrs] - p_hat  # positive = copperplate clear under-prices
    sp = spread[hrs]
    fin = np.isfinite(under) & np.isfinite(sp)
    r = float(np.corrcoef(sp[fin], under[fin])[0, 1]) if fin.sum() > 2 else float("nan")
    q = np.quantile(sp[fin], [0.0, 0.25, 0.5, 0.75, 1.0])
    terc = []
    for lo, hi in zip(q[:-1], q[1:]):
        m = fin & (sp >= lo) & (sp <= hi)
        terc.append(
            {
                "zonal_spread_range": [round(float(lo), 2), round(float(hi), 2)],
                "n": int(m.sum()),
                "mean_underprice": round(float(np.mean(under[m])), 3),
            }
        )
    return {
        "window": "JJA_h12_17",
        "n_hours": int(hrs.size),
        "mean_underprice_usd_mwh": round(float(np.mean(under[fin])), 3),
        "mean_zonal_price_spread_usd_mwh": round(float(np.mean(sp[fin])), 3),
        "pearson_r_spread_vs_underprice": round(r, 4),
        "by_spread_quartile": terc,
        "footing_median_abs_err": foot["years"][str(year)]["windows"]["JJA_h12_17"][
            "lo"
        ]["median_abs_err"],
    }


def main() -> None:
    hygiene()
    res = {
        "prereg": "results/calibration/PREREG-miso143-coal-gas-merit-order-2026-08-08.md",
        "gate": "G-A1 (merit-order gain) + G-A2 (true ladder slope), under "
        "BRANCH-INSTRUMENT-FAIL",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "posture": "NO SOLVE -- run_year(fleet_only=True) offer stack, anchored "
        "on the keeper's OWN committed P1 price",
        "branch": "BRANCH-INSTRUMENT-FAIL fired at G-A0 (P1 median|err| 9.998 vs "
        "the 4.00 bar; r 0.853 vs 0.85). The bar is NOT moved and the failed "
        "reading is reported at full magnitude; per the PREREG this instrument "
        "reports GAPS ONLY and the gain as a BOUND, never a point.",
        "displacements": {
            "c2_eia923": "the SCORER's own C2 basis (EIA-923); 2025 coal +4.2 %",
            "eia930_w1_2025": "miso-142's EIA-930 hourly W1 read, 2025 ONLY "
            "(+14.6 %) -- a separately labelled endpoint, never averaged with "
            "the C2 reading (TRAP 3)",
        },
        "bounds": {
            "cap": "replacement supply = raw above-anchor capability -> LOWER "
            "bound on the gain (overstates deliverable supply)",
            "idle": "that capability x each class's measured idle fraction -> "
            "UPPER bound on the gain",
        },
        "miso142_empirical_slope_usd_per_gw": {
            f"{y}|{w}": v for (y, w), v in MISO142_EMPIRICAL_SLOPE.items()
        },
        "years": {},
        "congestion_diagnostic": {},
    }
    for y in YEARS:
        res["years"][str(y)] = year_block(y)
    res["congestion_diagnostic"]["2025"] = congestion_diagnostic(2025)
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
