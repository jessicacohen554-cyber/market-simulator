#!/usr/bin/env python
"""ERCOT-138 Phase 1 — which side of the coal-vs-gas RANKING is wrong ABOVE
coal min-load: the coal committed/econ bands, or the gas CC bands?

The lane the ERCOT-137 falsifier routed here
(``docs/PRECOMMIT-ercot137-coal-margin-offer-2026-07-29.md`` §3, OUTCOME
header). With the coal min-load PRICE measured-correct (the net-margin form,
keeper ``2026-07-29-ercot137-coal-margin-measured``) and the fleet on the
MEASURED availability envelope, coal still over-loads actual in EVERY RT price
band >= $15 by ~7-13 pp, band-UNIFORMLY (G1 3/21; C1 coal +6.2/+8.8/+8.6 TWh),
displaced ~1:1 from gas (``DIAGNOSIS-ercot134`` §§6/10: corr(dCoal, dGas)
-0.93..-0.97). A band-uniform over-run at a *correct* bottom is a **ranking**
defect: the order in which the two classes' incremental MW enter merit.

**The question, and why it is answerable with no LP.** A ranking is a property
of the two OFFER CURVES, not of a dispatch. Both sides are already on disk:

* MEASURED — the 60-Day SCED disclosure's ``Submitted TPO`` three-part offers
  carry COAL **and** the CC control on one corpus, one loader, one ONLINE
  convention (``ercot123_coal_sced_reach``; the reach question it closed and
  the curve bottom ``ercot136_coal_headroom_conduct`` measured are both read
  from that same frame). The loaders are **IMPORTED, never re-implemented** —
  the ERCOT-135 charter's requirement, so the two lanes cannot drift onto
  different corpora.
* MODEL — the bid array at the exact LP seam, captured by the
  ``ercot135_coal_merit_order`` abort-early replay pattern, extended to record
  **every** class rather than coal alone. No LP matrix is built and no year is
  solved.

**The one convention** (§2 below states it formally). Both sides are put on the
*capability* convention — cumulative MW available at or below a price, as a
share of the class's own capability, with the min-load block counted at every
price because it is not price-responsive on either side:

    cap_share(p) = [ minload + offered_MW(<= p) ] / capability

and its ``above-min-load`` twin, which is what this lane actually asks about:

    inc_share(p) = offered_MW(<= p) / (capability - minload)

Measured: ``minload = LSL``, ``capability = HSL``, offered = the submitted TPO
curve. Model: ``minload = min_gen[g,t]`` (the floors), ``capability =
pmax[g] x availability[g,t]``, offered = each tranche's remaining MW at its own
bid. The ``capability`` denominator is HSL on BOTH sides, so the AS reservation
is inside the denominator for both and no HASL/HSL rebasing is needed; the
committed ERCOT-123/136 HASL-denominated "floored" grid is reproduced alongside
as a footing check (§A), so this probe's measured half is demonstrably the same
curve as the one already on the record.

**MATCHED HOURS — the sampling upgrade this probe makes.** ERCOT-135/136
compared an *annual* model statistic to a *probe-day* measured one. Here the
model bid is evaluated on EXACTLY the (delivery-day, hour) pairs each SCED
subset covers — 25/22/22/10 days, hours 11-22 for three of the four subsets —
so the fuel-price and sigmoid seasonality that moves the model's coal and gas
bids within a year cannot enter as a sampling artifact.

**What decides (a) vs (b).** Two classes x two sides gives four curves. The
ranking statistic is the *difference of the two classes' curves* on each side:

    rank(p) = cap_share_COAL(p) - cap_share_CC(p)

``rank_model(p) - rank_measured(p) > 0`` at a price means the model puts more
coal ahead of gas than the real market does at that price. §D attributes that
gap to its two additive legs — the coal leg ``model_COAL - measured_COAL`` and
the gas leg ``-(model_CC - measured_CC)`` — and whichever leg carries it is the
answer: (a) coal too cheap, or (b) gas too dear. Both legs are reported for
every price and every subset; nothing is pooled away.

Sections
--------
A  footing check — the committed ERCOT-136 B2 "floored" grid, reproduced
B  MEASURED capability/incremental curves, COAL and CC, matched hours
C  MODEL capability/incremental curves, COAL and CC, on the SAME hours
D  the RANKING decomposition on the capability-SHARE convention
E  **THE VERDICT** — matched-band BID quantiles + the spread decomposition,
   denominator-free, so §5's ONLINE-restriction asymmetry cannot drive it
H  SAME-PLANTS robustness — §E restricted to crosswalked plants on BOTH sides
J  WHICH gas mechanism — the margin form's own delta vs the band multipliers
F  dispatch-side corroboration from the keeper's COMMITTED class_hourly
G  rule 19 [R-ONE-MECH] enumeration — what prices each class above min-load

§E and §H carry the verdict; §D is reported for completeness and is the one
section the ONLINE-vs-available asymmetry does move (see ``limits`` in the
emitted JSON).

Rule scope
----------
No LP is built, no year is solved, nothing is registered, no ``ScenarioConfig``
field or solve path is touched, no keeper file is touched, and no year outside
{2023, 2024, 2025} is read (rule 22 ``[R-HOLDOUT]``). Nothing here is tuned and
nothing here is a mechanism: every number is either a measured corpus read on
an already-accepted convention or the model's own construction read back at its
own seam (rules 13/23).

SAMPLING — carried on every measured number
-------------------------------------------
The on-disk SCED subsets are probe days, not a full span: 79 delivery days
across **2024-2025 only** (no 2023 SCED exists on disk), and three of the four
subsets sample hours 11-22 only. December-2025 intervals are dropped by the
shared loader (ERCOT's schema revision drops ``HASL`` and the AS award block).
Every statistic is reported **split by day-family (tail vs control)** so the
deliberate price-based day selection is its own robustness control. The 2023
model curve is reported for the record and explicitly marked unmatched.

Usage
-----
    python scripts/probes/ercot138_coal_gas_ranking.py [--json-out PATH]
                                                       [--years 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO / "src"), str(_REPO), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ERCOT-123's loader, class map, ONLINE status set and TPO column names are
# IMPORTED, never re-implemented (the ERCOT-135 charter's footing requirement).
from ercot123_coal_sced_reach import (  # noqa: E402
    SUBSETS,
    TPO_MW,
    TPO_PR,
    _hour_of_year,
    load_sced,
)

#: The ERCOT keeper whose offer surface this probe reads. ercot137 —
#: 2026-07-29-ercot137-coal-margin-measured, promoted 2026-07-29.
KEEPER_BUNDLE = _REPO / "results" / "calibration" / "ercot137_margin_arm"

#: The committed ERCOT-136 artifact, read for the §A footing check only.
ERCOT136_ARTIFACT = (
    _REPO / "results" / "calibration" / "ercot136_coal_headroom_conduct.json"
)

OUT_JSON = _REPO / "results" / "calibration" / "ercot138_coal_gas_ranking.json"

#: Scratch run dir for the abort-early replay (never written — the capture
#: raises before ``run_energy_solve`` builds its first matrix).
SCRATCH = _REPO / "results" / "calibration" / "_ercot138_scratch"

#: Model plant groups that map onto the SCED corpus's ``CC`` control class.
#: ERCOT-123's ``TYPE_TO_CLASS`` maps CCGT90/CCLE90 -> CC, matching
#: ``derive_dam_offer_hrmults.CC_RESOURCE_TYPES`` — the merchant CC lineage. The
#: model's CC_CHP rows are reported as a sensitivity in §C, never pooled in.
MODEL_CC_GROUPS: tuple[str, ...] = ("CC_REGULAR",)
# Every coal subclass (COAL-SUB, 2026-09-25: the fleet's coal plant_group is
# its subclass; this tuple was ("COAL",) while the fleet carried the bare class).
MODEL_COAL_GROUPS: tuple[str, ...] = ("COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC")

#: Price grid. The lane's own bands are ercot127's fixed edges (15/20/25/30/35/
#: 50); $4.50 is kept as an edge because it is the RETIRED tranche-1 bid the
#: ERCOT-137 margin form replaced, so its column shows that retirement landing.
GRID: tuple[float, ...] = (
    0.0, 4.5, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0, 100.0,
)

#: Quantiles for the §E matched-band bid comparison.
QS: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90)

#: A tranche/interval counts as carrying capacity above this level (MW).
CAP_EPS = 1e-6

YEARS: tuple[int, ...] = (2023, 2024, 2025)


class _Captured(Exception):
    """Raised to abort a replay once the offer seam has been recorded."""


# --------------------------------------------------------------------------
# model side — the offer surface at the LP seam (abort-early replay, no LP)
# --------------------------------------------------------------------------
def _keeper_kwargs(year: int) -> dict:
    """Return ``solve_and_persist`` kwargs for the ercot137 keeper at ``year``.

    Built from the COMMITTED bundle's ``meta.json`` through ``replay_keeper``,
    so the captured surface is the keeper's own recipe rather than a lookalike.
    """
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf

    meta = json.loads((KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = SCRATCH / str(year)
    return kwargs


def capture_offer_surface(year: int) -> dict:
    """Capture the WHOLE fleet's offer surface at the last pre-LP seam.

    Patches ``scripts.run_calibration.run_energy_solve`` — the call that owns
    the P0/P1 pair — records its inputs and aborts before it builds anything.
    At that point ``mc_base`` has had every base-cost offer reform applied in
    order (``assemble_mc`` -> EACs -> ``apply_coal_tranches`` -> ``apply_gas_
    offer_margin`` -> the ERCOT conditional/cleared-share surfaces' P1 markup
    assembled into ``mc_bid_adjust``), so coal and gas are final and mutually
    comparable — which capturing at ``apply_coal_tranches`` alone (the
    ERCOT-135 seam) is NOT, because the gas margin runs after it.

    **The patch target is the copy imported into** ``scripts.run_calibration``
    (line 120, called from its own ``run_year``), NOT ``market_sim.pipeline.
    solve``; patching the source module would leave the imported name bound to
    the real function — the same trap ``ercot135_coal_merit_order`` records for
    ``apply_coal_tranches``.

    Returns parallel arrays over ALL generator rows: ``unit_id``,
    ``plant_group``, ``fuel_type``, ``plant_code``, ``pmax``, plus the
    ``(n_gen, T)`` ``availability``, ``min_gen`` and ``mc_base``, and the
    P1-only ``mc_bid_adjust`` (``None`` when no surface is armed).
    """
    from scripts import run_calibration as rc
    from scripts import run_calibration_full as rcf

    real = rc.run_energy_solve
    real_coal = rc.apply_coal_tranches
    box: dict = {}

    def _pre_spy(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config=None):
        # ``apply_coal_tranches`` is the FIRST offer reform after ``assemble_mc``
        # + ``apply_eac_to_mc``, so ``mc`` on entry is the pre-reform physical
        # cost (tranche HR x delivered fuel + VOM + carbon + NOx). Recording it
        # here — and the delivered fuel price it was built from, which no later
        # seam receives — is what makes the §J physical/markup split possible.
        box["mc_pre"] = np.asarray(mc, dtype=float).copy()
        box["fuel_price"] = np.asarray(fuel_prices, dtype=float).mean(axis=1)
        box["heat_rate"] = np.asarray(fleet_arrays.heat_rate, dtype=float).copy()
        box["vom"] = np.asarray(fleet_arrays.vom, dtype=float).copy()
        real_coal(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config)

    def _spy(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kw):
        n_gen = len(fleet_arrays.unit_ids)
        avail = np.asarray(fleet_arrays.availability, dtype=float)
        if avail.ndim == 1:  # scalar-availability fleets broadcast to (n_gen, T)
            avail = np.repeat(avail[:, None], mc_base.shape[1], axis=1)
        mg = fleet_arrays.min_gen
        if mg is None:
            mg = np.repeat(
                np.asarray(fleet_arrays.pmin, dtype=float)[:, None],
                mc_base.shape[1],
                axis=1,
            )
        adj = kw.get("mc_bid_adjust")
        box.update(
            unit_id=[str(u) for u in fleet_arrays.unit_ids],
            plant_group=[str(getattr(g, "plant_group", "") or "") for g in fleet],
            fuel_type=[str(getattr(g, "fuel_type", "") or "") for g in fleet],
            plant_code=np.array(
                [int(getattr(g, "plant_code", 0) or 0) for g in fleet], dtype=int
            ),
            pmax=np.asarray(fleet_arrays.pmax, dtype=float),
            availability=avail,
            min_gen=np.asarray(mg, dtype=float),
            mc_base=np.asarray(mc_base, dtype=float),
            mc_bid_adjust=(None if adj is None else np.asarray(adj, dtype=float)),
            n_gen=n_gen,
        )
        raise _Captured

    rc.run_energy_solve = _spy
    rc.apply_coal_tranches = _pre_spy
    try:
        rcf.solve_and_persist(**_keeper_kwargs(year))
    except _Captured:
        pass
    finally:
        rc.run_energy_solve = real
        rc.apply_coal_tranches = real_coal
    if not box:
        raise RuntimeError(f"offer seam never reached for {year}")
    return box


def _tranche_role(unit_id: str) -> str:
    """Classify a model row by the tranche suffix its unit id carries.

    The CAMPD per-plant binner names rows ``<GROUP>_<zone>_p<code>_<role>``
    with roles ``mustrun`` / ``committed`` / ``econc<NN>`` (or ``econ``) /
    ``peak<N>``. Roles are read, never inferred from price, so a repriced band
    keeps its identity (rule 18 ``[R-PHYSICS]`` in spirit: classify on the
    construction, not on the number that came out).
    """
    tail = unit_id.rsplit("_", 1)[-1]
    if tail == "mustrun":
        return "mustrun"
    if tail == "committed":
        return "committed"
    if tail.startswith("econ"):
        return "econ"
    if tail.startswith("peak"):
        return "peak"
    return "other"


def model_curves(
    cap: dict,
    hours: np.ndarray,
    groups: tuple[str, ...],
    roles: tuple[str, ...] | None = None,
) -> dict:
    """Build one class's model supply curves on the shared convention.

    ``hours`` selects the matched hour-of-year indices. Every quantity is
    summed over (row, hour), i.e. MW-hours — the model analogue of the
    measured side's resource-interval MW, so a 750 MW row-hour and a 90 MW
    row-hour are weighted the way they actually enter merit.

    ``roles`` optionally restricts to a subset of tranche roles — the lane asks
    about the **committed/econ** bands specifically, and restricting to them
    drops the model's ``peak`` rungs, whose measured counterpart cannot be
    isolated inside a submitted curve. Reported both ways so the verdict can be
    seen not to hinge on the choice.

    Returns the capability/incremental cumulative shares on :data:`GRID`, the
    class totals, and the cap-weighted bid quantiles of the incremental MW.
    """
    grp = np.array(cap["plant_group"])
    sel = np.isin(grp, list(groups))
    if roles is not None:
        role_all = np.array([_tranche_role(u) for u in cap["unit_id"]])
        sel = sel & np.isin(role_all, list(roles))
    rows = np.flatnonzero(sel)
    if rows.size == 0:
        return {}
    pmax = cap["pmax"][rows][:, None]
    avail = cap["availability"][rows][:, hours]
    mg = cap["min_gen"][rows][:, hours]
    bid = cap["mc_base"][rows][:, hours]
    adj = cap.get("mc_bid_adjust")
    bid_p1 = bid if adj is None else bid + adj[rows][:, hours]

    capability = pmax * avail                      # MW available, per row-hour
    minload = np.minimum(mg, capability)           # floors can't exceed capability
    incremental = np.maximum(capability - minload, 0.0)

    cap_tot = float(capability.sum())
    min_tot = float(minload.sum())
    inc_tot = float(incremental.sum())
    if cap_tot <= CAP_EPS:
        return {}

    def _curve(b: np.ndarray) -> tuple[list[float], list[float]]:
        capsh, incsh = [], []
        for p in GRID:
            offered = float(incremental[b <= p].sum())
            capsh.append((min_tot + offered) / cap_tot)
            incsh.append(offered / inc_tot if inc_tot > CAP_EPS else float("nan"))
        return capsh, incsh

    cap_base, inc_base = _curve(bid)
    cap_p1, inc_p1 = _curve(bid_p1)

    role = np.array([_tranche_role(u) for u in np.array(cap["unit_id"])[rows]])
    by_role = {}
    for r in ("mustrun", "committed", "econ", "peak"):
        m = role == r
        if not m.any():
            continue
        by_role[r] = {
            "cap_share_of_class": round(float(capability[m].sum() / cap_tot), 4),
            "bid_capwtd_p50": round(
                float(_wq(bid[m].ravel(), capability[m].ravel(), (0.50,))[0]), 3
            ),
        }

    return {
        "n_rows": int(rows.size),
        "n_plants": int(len({int(c) for c in cap["plant_code"][rows] if c})),
        "capability_MWh": round(cap_tot, 1),
        "minload_of_capability": round(min_tot / cap_tot, 4),
        "incremental_of_capability": round(inc_tot / cap_tot, 4),
        "cap_share": {f"<={p:g}": round(v, 4) for p, v in zip(GRID, cap_base)},
        "inc_share": {f"<={p:g}": round(v, 4) for p, v in zip(GRID, inc_base)},
        "cap_share_p1": {f"<={p:g}": round(v, 4) for p, v in zip(GRID, cap_p1)},
        "inc_share_p1": {f"<={p:g}": round(v, 4) for p, v in zip(GRID, inc_p1)},
        "inc_bid_q": {
            f"p{int(q * 100)}": round(v, 3)
            for q, v in zip(
                QS, _wq(bid.ravel(), incremental.ravel(), QS)
            )
        },
        "inc_bid_q_p1": {
            f"p{int(q * 100)}": round(v, 3)
            for q, v in zip(
                QS, _wq(bid_p1.ravel(), incremental.ravel(), QS)
            )
        },
        "by_role": by_role,
    }


# --------------------------------------------------------------------------
# measured side — the SCED submitted TPO curves, same convention
# --------------------------------------------------------------------------
def _wq(values: np.ndarray, weights: np.ndarray, qs: tuple[float, ...]) -> list[float]:
    """Capacity-weighted quantiles (ERCOT-136's convention, same arithmetic)."""
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not ok.any():
        return [float("nan")] * len(qs)
    v, w = values[ok], weights[ok]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w) / w.sum()
    return [float(np.interp(q, cw, v)) for q in qs]


def measured_curves(df: pd.DataFrame) -> dict:
    """Build one class's measured supply curves on the shared convention.

    Per online resource-interval the submitted three-part offer is a set of
    (price, cumulative-MW) breakpoints. ``Submitted TPO-MW{k}`` is cumulative
    from zero, so the MW offered at or below price ``p`` is the largest
    ``TPO-MW{k}`` whose ``TPO-Price{k} <= p``, **clipped into the incremental
    range** ``[LSL, HSL]`` so the min-load block is not double-counted: the
    part of the curve below ``LSL`` is min-load, which this convention counts
    at every price on both sides.

    ``capability = HSL`` — the same denominator the model side uses, so the AS
    reservation sits inside the denominator on both sides and no HASL rebasing
    enters. §A separately reproduces the committed HASL-denominated grid.
    """
    P = df[TPO_PR].to_numpy(float)
    M = df[TPO_MW].to_numpy(float)
    hsl = df["HSL"].to_numpy(float)
    lsl = np.clip(df["LSL"].to_numpy(float), 0.0, None)
    lsl = np.minimum(lsl, hsl)
    inc_range = np.maximum(hsl - lsl, 0.0)

    cap_tot = float(hsl.sum())
    min_tot = float(lsl.sum())
    inc_tot = float(inc_range.sum())

    capsh, incsh = [], []
    for p in GRID:
        ok = np.isfinite(P) & np.isfinite(M) & (P <= p)
        mw = np.where(ok, M, 0.0).max(axis=1)
        # Clip into [LSL, HSL]: below LSL is min-load (already counted),
        # above HSL is not deliverable capability.
        offered = np.clip(mw, lsl, hsl) - lsl
        capsh.append((min_tot + float(offered.sum())) / cap_tot)
        incsh.append(float(offered.sum()) / inc_tot if inc_tot > CAP_EPS else np.nan)

    # Incremental-MW bid quantiles: each curve STEP contributes its own MW at
    # its own price, so the distribution is over MW, not over intervals.
    step_pr, step_mw = [], []
    prev = lsl.copy()
    order = np.argsort(np.where(np.isfinite(P), P, np.inf), axis=1)
    for k in range(P.shape[1]):
        idx = order[:, k]
        pk = np.take_along_axis(P, idx[:, None], axis=1).ravel()
        mk = np.take_along_axis(M, idx[:, None], axis=1).ravel()
        mk = np.clip(np.where(np.isfinite(mk), mk, prev), lsl, hsl)
        step = np.maximum(mk - prev, 0.0)
        good = np.isfinite(pk) & (step > 0)
        step_pr.append(pk[good])
        step_mw.append(step[good])
        prev = np.maximum(prev, mk)
    sp = np.concatenate(step_pr) if step_pr else np.array([])
    sm = np.concatenate(step_mw) if step_mw else np.array([])

    return {
        "res_hours": int(len(df)),
        "resources": int(df["Resource Name"].nunique()),
        "capability_MW": round(cap_tot, 1),
        "minload_of_capability": round(min_tot / cap_tot, 4),
        "incremental_of_capability": round(inc_tot / cap_tot, 4),
        "cap_share": {f"<={p:g}": round(v, 4) for p, v in zip(GRID, capsh)},
        "inc_share": {f"<={p:g}": round(v, 4) for p, v in zip(GRID, incsh)},
        "inc_bid_q": {
            f"p{int(q * 100)}": round(v, 3) for q, v in zip(QS, _wq(sp, sm, QS))
        },
        "offered_share_of_incremental": round(
            float(sm.sum()) / inc_tot if inc_tot > CAP_EPS else float("nan"), 4
        ),
    }


def measured_floored_footing(df: pd.DataFrame) -> dict:
    """A — the committed ERCOT-136 B2 'floored' row, recomputed here.

    ``supply(p) = clip(max{MW_k : price_k <= p}, LSL, HASL)`` with
    ``supply(-inf) = LSL``, over denominator ``HASL`` — the ERCOT-136 §B2
    ``floored`` arithmetic verbatim (which is itself ERCOT-123 §5's). Note the
    cap is **HASL**, not HSL: the part of a submitted curve that reaches above
    the AS-reduced limit is not deliverable and does not count. Reproducing it
    on this probe's own code is the footing check — a divergence here would mean
    this lane is not reading the same curve the record already carries.
    """
    P = df[TPO_PR].to_numpy(float)
    M = df[TPO_MW].to_numpy(float)
    hsl = df["HSL"].to_numpy(float)
    hasl = np.clip(df["HASL"].to_numpy(float), 0.0, hsl)
    lsl = np.clip(df["LSL"].to_numpy(float), 0.0, hsl)
    denom = float(hasl.sum())
    out = {}
    prev = lsl.copy()
    for p in (0.0, 4.5, 15.0, 20.0, 25.0):
        ok = np.isfinite(P) & np.isfinite(M) & (P <= p)
        sup = np.max(np.where(ok, M, -np.inf), axis=1)
        sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), lsl, hasl)
        sup = np.maximum(sup, prev)  # monotone across edges
        out[f"<={p:g}"] = round(float(sup.sum()) / denom, 6)
        prev = sup
    return out


# --------------------------------------------------------------------------
# sections
# --------------------------------------------------------------------------
def load_frames() -> dict[str, tuple[pd.DataFrame, dict]]:
    """Load every SCED probe-day subset through ERCOT-123's own loader."""
    out = {}
    for tag, _yr, _fam in SUBSETS:
        r = load_sced(tag)
        if r is not None:
            out[tag] = r
    return out


def section_a(frames) -> list[dict]:
    """A — footing: the committed ERCOT-136 B2 floored grid, reproduced."""
    committed = {
        (r["year"], r["family"], r["class"]): r
        for r in json.loads(ERCOT136_ARTIFACT.read_text())["B2_supply_grid"]
        if r["conv"] == "floored"
    }
    rows = []
    for tag, yr, fam in SUBSETS:
        if tag not in frames:
            continue
        df = frames[tag][0]
        for cls in ("COAL", "CC"):
            sub = df[df["cls"] == cls]
            if sub.empty:
                continue
            mine = measured_floored_footing(sub)
            ref = committed.get((yr, fam, cls), {})
            row = {"year": yr, "family": fam, "class": cls}
            worst = 0.0
            for k, v in mine.items():
                rv = ref.get(k)
                row[f"mine{k}"] = v
                row[f"ref{k}"] = None if rv is None else round(float(rv), 6)
                if rv is not None:
                    worst = max(worst, abs(v - float(rv)))
            row["max_abs_dev"] = round(worst, 8)
            rows.append(row)
    return rows


def section_bc(frames, captures: dict[int, dict]) -> tuple[list[dict], list[dict]]:
    """B/C — measured and model curves, per subset, on the MATCHED hours."""
    measured, model = [], []
    for tag, yr, fam in SUBSETS:
        if tag not in frames:
            continue
        df = frames[tag][0]
        hours = np.unique(_hour_of_year(df["ts"]))
        hours = hours[(hours >= 0) & (hours < 8760)]
        for cls, groups in (("COAL", MODEL_COAL_GROUPS), ("CC", MODEL_CC_GROUPS)):
            sub = df[df["cls"] == cls]
            if not sub.empty:
                measured.append(
                    {"year": yr, "family": fam, "class": cls, "subset": tag,
                     **measured_curves(sub)}
                )
            if yr in captures:
                mc = model_curves(captures[yr], hours, groups)
                if mc:
                    model.append(
                        {"year": yr, "family": fam, "class": cls, "subset": tag,
                         "matched_hours": int(hours.size), **mc}
                    )
        # CC_CHP sensitivity — reported, never pooled into the CC control.
        if yr in captures:
            mc = model_curves(captures[yr], hours, ("CC_REGULAR", "CC_CHP"))
            if mc:
                model.append(
                    {"year": yr, "family": fam, "class": "CC+CHP(sens)",
                     "subset": tag, "matched_hours": int(hours.size), **mc}
                )
    return measured, model


def section_d(measured: list[dict], model: list[dict]) -> list[dict]:
    """D — THE VERDICT: the ranking gap and its coal / gas legs.

    ``rank(p) = cap_share_COAL(p) - cap_share_CC(p)`` is how far ahead of gas
    the class sits at price ``p``. The model-minus-measured difference of that
    statistic decomposes EXACTLY into two additive legs::

        rank_model - rank_meas = (COAL_model - COAL_meas)   <- the coal leg
                               - (CC_model   - CC_meas)     <- the gas leg

    so at every price the two legs sum to the gap and the larger one names the
    defective side. Positive coal leg = model coal offered cheaper than the real
    coal fleet offers itself. Positive gas leg = model CC offered DEARER than
    the real CC fleet offers itself (the sign is flipped by the minus above, so
    a positive gas leg always means "gas priced too dear" in ranking terms).
    """
    def _key(r):
        return (r["year"], r["family"], r["class"])

    m_meas = {_key(r): r for r in measured}
    m_mod = {_key(r): r for r in model}
    rows = []
    for yr, fam in sorted({(r["year"], r["family"]) for r in measured}):
        for p in GRID:
            key = f"<={p:g}"
            try:
                cm = m_meas[(yr, fam, "COAL")]["cap_share"][key]
                gm = m_meas[(yr, fam, "CC")]["cap_share"][key]
                cM = m_mod[(yr, fam, "COAL")]["cap_share"][key]
                gM = m_mod[(yr, fam, "CC")]["cap_share"][key]
                cM1 = m_mod[(yr, fam, "COAL")]["cap_share_p1"][key]
                gM1 = m_mod[(yr, fam, "CC")]["cap_share_p1"][key]
            except KeyError:
                continue
            coal_leg = cM - cm
            gas_leg = -(gM - gm)
            coal_leg1 = cM1 - cm
            gas_leg1 = -(gM1 - gm)
            rows.append(
                {
                    "year": yr, "family": fam, "price": p,
                    "rank_measured": round(cm - gm, 4),
                    "rank_model": round(cM - gM, 4),
                    "rank_gap": round((cM - gM) - (cm - gm), 4),
                    "coal_leg": round(coal_leg, 4),
                    "gas_leg": round(gas_leg, 4),
                    "coal_leg_share": (
                        round(abs(coal_leg) / (abs(coal_leg) + abs(gas_leg)), 3)
                        if (abs(coal_leg) + abs(gas_leg)) > 1e-9 else None
                    ),
                    "rank_gap_p1": round((cM1 - gM1) - (cm - gm), 4),
                    "coal_leg_p1": round(coal_leg1, 4),
                    "gas_leg_p1": round(gas_leg1, 4),
                }
            )
    return rows


def section_e(
    frames, captures: dict[int, dict]
) -> tuple[list[dict], list[dict]]:
    """E — THE HEADLINE: the matched-band BID comparison, model vs measured.

    This is the lane's decisive instrument and it is **denominator-free** —
    unlike the §B/§C share curves it does not depend on how much capability
    each side counts, so the ONLINE-restriction asymmetry declared in §C's
    limits cannot drive it.

    The object, per class and per subset: the **capacity-weighted distribution
    of the price attached to a MW of ABOVE-MIN-LOAD capability**. Measured, that
    is each submitted-TPO curve STEP contributing its own MW at its own price,
    clipped into ``[LSL, HSL]``. Model, that is each tranche-hour contributing
    ``pmax x availability - min_gen`` MW at its own bid. Same quantiles, same
    weighting, same hours.

    The ranking then reads directly in dollars::

        spread(q)   = bid_q_COAL(q) - bid_q_CC(q)        (per side)
        spread_gap  = spread_model(q) - spread_measured(q)
                    = [COAL_model - COAL_meas] - [CC_model - CC_meas]
                    =      coal_leg           -      gas_leg

    A NEGATIVE ``spread_gap`` means the model prices coal cheaper *relative to
    gas* than the real market does — coal ranks ahead of gas too often, which is
    the ERCOT-137 residual. The two legs say which side owns it: ``coal_leg``
    is how much dearer/cheaper the model's coal band is than the real coal
    fleet's own conduct, ``gas_leg`` the same for CC. The bigger ``|leg|`` is
    the answer to (a)-vs-(b), and the legs are computed against each class's OWN
    measured conduct, so neither can be blamed for the other's error.

    The model side is reported on THREE variants, all on the same measured
    baseline: ``all`` (every incremental tranche), ``committed_econ`` (the bands
    the lane names — drops the peak rungs), and ``p1`` (``all`` plus the armed
    P1-only ERCOT offer surfaces, which are gas-side markups).
    """
    detail, verdict = [], []
    for tag, yr, fam in SUBSETS:
        if tag not in frames or yr not in captures:
            continue
        df = frames[tag][0]
        hours = np.unique(_hour_of_year(df["ts"]))
        hours = hours[(hours >= 0) & (hours < 8760)]
        meas, mod = {}, {}
        for cls, groups in (("COAL", MODEL_COAL_GROUPS), ("CC", MODEL_CC_GROUPS)):
            sub = df[df["cls"] == cls]
            if sub.empty:
                continue
            meas[cls] = measured_curves(sub)["inc_bid_q"]
            m_all = model_curves(captures[yr], hours, groups)
            m_ce = model_curves(
                captures[yr], hours, groups, roles=("committed", "econ")
            )
            mod[cls] = {
                "all": m_all["inc_bid_q"],
                "p1": m_all["inc_bid_q_p1"],
                "committed_econ": m_ce["inc_bid_q"] if m_ce else {},
            }
            for q in QS:
                qk = f"p{int(q * 100)}"
                detail.append(
                    {
                        "year": yr, "family": fam, "class": cls, "q": qk,
                        "measured": meas[cls][qk],
                        "model_all": m_all["inc_bid_q"][qk],
                        "model_committed_econ": (
                            m_ce["inc_bid_q"][qk] if m_ce else None
                        ),
                        "model_p1": m_all["inc_bid_q_p1"][qk],
                        "delta_all": round(
                            m_all["inc_bid_q"][qk] - meas[cls][qk], 3
                        ),
                        "delta_committed_econ": (
                            round(m_ce["inc_bid_q"][qk] - meas[cls][qk], 3)
                            if m_ce else None
                        ),
                        "delta_p1": round(
                            m_all["inc_bid_q_p1"][qk] - meas[cls][qk], 3
                        ),
                    }
                )
        if not {"COAL", "CC"} <= set(meas):
            continue
        for q in QS:
            qk = f"p{int(q * 100)}"
            for variant in ("all", "committed_econ", "p1"):
                if not mod["COAL"].get(variant) or not mod["CC"].get(variant):
                    continue
                coal_leg = mod["COAL"][variant][qk] - meas["COAL"][qk]
                gas_leg = mod["CC"][variant][qk] - meas["CC"][qk]
                sp_meas = meas["COAL"][qk] - meas["CC"][qk]
                sp_mod = mod["COAL"][variant][qk] - mod["CC"][variant][qk]
                verdict.append(
                    {
                        "year": yr, "family": fam, "q": qk, "variant": variant,
                        "spread_measured": round(sp_meas, 3),
                        "spread_model": round(sp_mod, 3),
                        "spread_gap": round(sp_mod - sp_meas, 3),
                        "coal_leg": round(coal_leg, 3),
                        "gas_leg": round(gas_leg, 3),
                        "owner": (
                            "GAS" if abs(gas_leg) > abs(coal_leg) else "COAL"
                        ),
                        "gas_leg_share": round(
                            abs(gas_leg) / (abs(gas_leg) + abs(coal_leg)), 3
                        ) if (abs(gas_leg) + abs(coal_leg)) > 1e-9 else None,
                    }
                )
    return detail, verdict


#: Resource-name -> EIA plant code, from the COMMITTED ERCOT DAM crosswalk.
#: Only ``accepted == 1`` rows are used; a rejected match is a rejected match.
_XWALK = _REPO / "data" / "raw" / "reference" / "ercot-dam-plant-crosswalk.csv"


def _resource_to_plant() -> list[tuple[str, int]]:
    """Longest-first (settlement point, plant code) pairs for the §H join.

    A SCED ``Resource Name`` extends its settlement point with a unit suffix
    (``BASTEN_CC1`` -> ``BASTEN_CC1_2``), so the join is a longest-prefix match
    rather than an equality — sorted longest-first so ``KMCHI_CC2`` can never be
    swallowed by a shorter ``KMCHI`` entry.
    """
    xw = pd.read_csv(_XWALK)
    xw = xw[xw["accepted"] == 1]
    pairs = set()
    for _, r in xw.iterrows():
        for sp in str(r["settlement_points"]).split(";"):
            sp = sp.strip()
            if sp:
                pairs.add((sp, int(r["plant_code"])))
    return sorted(pairs, key=lambda t: -len(t[0]))


def section_h(frames, captures: dict[int, dict]) -> list[dict]:
    """H — SAME-PLANTS robustness: §E rerun on the crosswalked plants only.

    The §E verdict compares two fleets that are *nominally* the same class but
    are not literally the same units — the model carries 10 coal / 41-42 CC
    plants, the measured corpus 25-26 coal / 150-177 SCED resources. This
    section removes that objection where the committed ERCOT DAM crosswalk lets
    it: both sides are restricted to the SAME EIA plant codes and the bid
    comparison is recomputed.

    Coverage is bounded and reported per row, not assumed: the crosswalk's
    accepted matches reach roughly half of measured coal HSL (4 plants) and
    about a fifth of measured CC HSL (12 plants). A sign agreement here is a
    real check on the §E verdict; a coverage-weighted magnitude is not claimed.
    """
    pairs = _resource_to_plant()

    def _to_plant(name: str) -> int:
        for sp, pc in pairs:
            if name == sp or name.startswith(sp + "_"):
                return pc
        return 0

    rows = []
    for tag, yr, fam in SUBSETS:
        if tag not in frames or yr not in captures:
            continue
        df = frames[tag][0].copy()
        df["pc"] = [_to_plant(str(n)) for n in df["Resource Name"]]
        hours = np.unique(_hour_of_year(df["ts"]))
        hours = hours[(hours >= 0) & (hours < 8760)]
        cap = captures[yr]
        legs = {}
        for cls, groups in (("COAL", MODEL_COAL_GROUPS), ("CC", MODEL_CC_GROUPS)):
            sub = df[(df["cls"] == cls) & (df["pc"] > 0)]
            if sub.empty:
                continue
            codes = set(int(c) for c in sub["pc"].unique())
            grp = np.array(cap["plant_group"])
            keep = np.isin(grp, list(groups)) & np.isin(cap["plant_code"], list(codes))
            if not keep.any():
                continue
            sub_cap = dict(cap)
            idx = np.flatnonzero(keep)
            sub_cap["plant_group"] = list(np.array(cap["plant_group"])[idx])
            sub_cap["unit_id"] = list(np.array(cap["unit_id"])[idx])
            sub_cap["plant_code"] = cap["plant_code"][idx]
            sub_cap["pmax"] = cap["pmax"][idx]
            sub_cap["availability"] = cap["availability"][idx]
            sub_cap["min_gen"] = cap["min_gen"][idx]
            sub_cap["mc_base"] = cap["mc_base"][idx]
            sub_cap["mc_bid_adjust"] = (
                None if cap["mc_bid_adjust"] is None else cap["mc_bid_adjust"][idx]
            )
            mm = measured_curves(sub)
            md = model_curves(sub_cap, hours, groups)
            if not md:
                continue
            legs[cls] = (mm, md)
            all_hsl = df[df["cls"] == cls]["HSL"].sum()
            for q in QS:
                qk = f"p{int(q * 100)}"
                rows.append(
                    {
                        "year": yr, "family": fam, "class": cls, "q": qk,
                        "n_plants_model": md["n_plants"],
                        "meas_HSL_coverage": round(
                            float(sub["HSL"].sum() / all_hsl), 3
                        ),
                        "measured": mm["inc_bid_q"][qk],
                        "model": md["inc_bid_q"][qk],
                        "delta": round(md["inc_bid_q"][qk] - mm["inc_bid_q"][qk], 3),
                    }
                )
        if {"COAL", "CC"} <= set(legs):
            for q in QS:
                qk = f"p{int(q * 100)}"
                cl = legs["COAL"][1]["inc_bid_q"][qk] - legs["COAL"][0]["inc_bid_q"][qk]
                gl = legs["CC"][1]["inc_bid_q"][qk] - legs["CC"][0]["inc_bid_q"][qk]
                rows.append(
                    {
                        "year": yr, "family": fam, "class": "-VERDICT-", "q": qk,
                        "coal_leg": round(cl, 3), "gas_leg": round(gl, 3),
                        "owner": "GAS" if abs(gl) > abs(cl) else "COAL",
                    }
                )
    return rows


def section_j(captures: dict[int, dict], frames) -> list[dict]:
    """J — WHICH mechanism carries the model's dear gas: the margin form, or
    the band multipliers underneath it?

    §E says the model's CC incremental bid runs dear against the CC fleet's own
    conduct. Two armed mechanisms could own that, and they route to different
    Phase-2 levers, so the split is measured rather than assumed.

    **Read the column names literally — none of them is "physical cost."** The
    tranche heat rate the LP costs on is ALREADY offer-loaded: the binner builds
    each band as ``base_HR x offer_multiplier``
    (``offer_curve_by_group['CC_REGULAR']``: committed 0.998, econ_low 0.723,
    econ_high 1.324, peak 4.576) against a separate PHYSICAL ladder
    (``phys_committed`` 1.006, ``phys_econ_low`` 0.825, ``phys_econ_high`` 0.95,
    ``phys_peak`` 2.25) used for burn and emissions. So:

    * ``pre_margin_p50`` — the bid on ENTRY to the first offer reform, i.e.
      ``offer_HR x delivered_fuel + VOM + carbon + NOx``. Offer-loaded already.
    * ``margin_delta_*`` — ``mc_base - mc_pre``, i.e. what
      ``gas_offer_net_revenue_margin`` (and, for coal, the ERCOT-137 margin
      form) actually CHANGED. This isolates the margin form's own contribution
      from the multipliers it sits on top of.
    * ``offer_hr_capwtd`` / ``phys_hr_capwtd`` — the capacity-weighted OFFER and
      PHYSICAL heat rates of the same rows, so the band multipliers' own
      contribution is visible next to the margin form's.

    A ``margin_delta`` near zero with a dear bid means the margin form is NOT
    the owner and the band multipliers are — which is the Phase-2-relevant
    distinction, because those two are different levers with different
    identifications.
    """
    rows = []
    for tag, yr, fam in SUBSETS:
        if tag not in frames or yr not in captures:
            continue
        df = frames[tag][0]
        hours = np.unique(_hour_of_year(df["ts"]))
        hours = hours[(hours >= 0) & (hours < 8760)]
        cap = captures[yr]
        if "mc_pre" not in cap:
            continue
        grp = np.array(cap["plant_group"])
        role_all = np.array([_tranche_role(u) for u in cap["unit_id"]])
        for cls, groups in (("COAL", MODEL_COAL_GROUPS), ("CC", MODEL_CC_GROUPS)):
            keep = np.isin(grp, list(groups)) & np.isin(
                role_all, ["committed", "econ"]
            )
            idx = np.flatnonzero(keep)
            if idx.size == 0:
                continue
            avail = cap["availability"][idx][:, hours]
            mg = cap["min_gen"][idx][:, hours]
            capa = cap["pmax"][idx][:, None] * avail
            inc = np.maximum(capa - np.minimum(mg, capa), 0.0)
            pre = cap["mc_pre"][idx][:, hours]
            base = cap["mc_base"][idx][:, hours]
            hr = cap["heat_rate"][idx]
            fp = cap["fuel_price"][idx]
            w = inc.ravel()
            pm = cap["pmax"][idx]
            offer_hr = float((hr * pm).sum() / pm.sum())
            phys_hr = _phys_hr_capwtd(cap, idx, role_all[idx], cls)
            rows.append(
                {
                    "year": yr, "family": fam, "class": cls,
                    "pre_margin_p50": round(_wq(pre.ravel(), w, (0.50,))[0], 3),
                    "bid_p50": round(_wq(base.ravel(), w, (0.50,))[0], 3),
                    "margin_delta_p25": round(
                        _wq((base - pre).ravel(), w, (0.25,))[0], 3
                    ),
                    "margin_delta_p50": round(
                        _wq((base - pre).ravel(), w, (0.50,))[0], 3
                    ),
                    "margin_delta_p75": round(
                        _wq((base - pre).ravel(), w, (0.75,))[0], 3
                    ),
                    "offer_hr_capwtd": round(offer_hr, 3),
                    "phys_hr_capwtd": (
                        None if phys_hr is None else round(phys_hr, 3)
                    ),
                    "offer_over_phys": (
                        None if not phys_hr else round(offer_hr / phys_hr, 3)
                    ),
                    "fuel_capwtd": round(float((fp * pm).sum() / pm.sum()), 3),
                }
            )
    return rows


def _phys_hr_capwtd(
    cap: dict, idx: np.ndarray, roles: np.ndarray, cls: str
) -> float | None:
    """Capacity-weighted PHYSICAL heat rate of the selected rows.

    Recovered by dividing each row's offer-loaded heat rate by its band's OFFER
    multiplier and re-multiplying by the band's PHYSICAL one, both read from the
    keeper's own ``offer_curve_by_group``. The econ rows carry an econ_low /
    econ_high split (``econ_low_share``), so the econ band uses the share-
    weighted pair rather than either endpoint. Returns ``None`` when the group
    publishes no ``phys_*`` ladder (ERCOT COAL does not — its bands are priced
    through the passthrough sigmoids, not a physical multiplier ladder).
    """
    grp = "CC_REGULAR" if cls == "CC" else "COAL"
    oc = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())[
        "scenario_config"
    ]["offer_curve_by_group"].get(grp, {})
    if not any(k.startswith("phys_") for k in oc):
        return None
    share = float(oc.get("econ_low_share", 0.5))
    pairs = {
        "committed": (oc.get("committed"), oc.get("phys_committed")),
        "econ": (
            share * oc.get("econ_low", 1.0) + (1 - share) * oc.get("econ_high", 1.0),
            share * oc.get("phys_econ_low", 1.0)
            + (1 - share) * oc.get("phys_econ_high", 1.0),
        ),
    }
    hr = cap["heat_rate"][idx]
    pm = cap["pmax"][idx]
    num = 0.0
    for r, (om, phm) in pairs.items():
        m = roles == r
        if not m.any() or not om or not phm:
            continue
        num += float(((hr[m] / om) * phm * pm[m]).sum())
    return num / float(pm.sum()) if pm.sum() else None


def section_f() -> list[dict]:
    """F — dispatch-side corroboration from the keeper's COMMITTED sidecars.

    Read, never re-solved (rule 15's keeper-sidecar clause): the ercot137
    bundle's ``hourly/class_hourly_<year>.parquet``. Reports each class's P1
    energy and, for coal and the gas classes, the load-weighted share of hours
    in which the class is at/near its own annual maximum — the ranking's
    dispatch fingerprint.
    """
    rows = []
    for year in YEARS:
        f = KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(f)
        d = d[d["pass"] == "P1"]
        tot = d.groupby("klass")["mw"].sum() / 1e6  # TWh
        # The sidecar splits coal by rank (COAL_PRB / COAL_LIGNITE) — there is
        # no bare "COAL" key. Summing the two is what the C1 class gate scores.
        coal = float(sum(tot.get(k, 0.0) for k in ("COAL_PRB", "COAL_LIGNITE")))
        cc = float(sum(tot.get(k, 0.0) for k in ("CC_REGULAR", "CC_CHP")))
        gas = cc + float(
            sum(tot.get(k, 0.0) for k in
                ("CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"))
        )
        rows.append(
            {
                "year": year,
                "coal_TWh": round(coal, 3),
                "cc_TWh": round(cc, 3),
                "gas_TWh": round(gas, 3),
                "coal_share_of_thermal": round(coal / (coal + gas), 4),
                "coal_over_cc": round(coal / cc, 4) if cc else None,
                "by_class_TWh": {k: round(float(v), 3) for k, v in tot.items()},
            }
        )
    return rows


def section_g() -> list[dict]:
    """G — rule 19 ``[R-ONE-MECH]``: what prices each class ABOVE min-load.

    Enumerated from the keeper's own ``run_config.json`` so the list is the
    armed configuration, not a recollection. This is the replace-or-reconcile
    ledger any Phase-2 mechanism must be checked against.
    """
    sc = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())["scenario_config"]
    def _g(k, default=None):
        return sc.get(k, default)
    return [
        {"class": "COAL", "band": "committed+econ", "mechanism":
         "coal PRB/lignite supply passthrough sigmoids",
         "detail": f"prb floor {_g('coal_prb_passthrough_floor')} / lignite floor "
                   f"{_g('coal_lignite_passthrough_floor')}; tiered="
                   f"{_g('coal_prb_passthrough_tiered')}",
         "status": "ARMED"},
        {"class": "COAL", "band": "econ", "mechanism": "coal_econ_marginal_hr_bound",
         "detail": f"{_g('coal_econ_marginal_hr_bound')} (ERCOT-115; floors the "
                   f"economic band's heat rate)", "status": "ARMED"},
        {"class": "COAL", "band": "min-load", "mechanism":
         "coal_offer_net_revenue_margin",
         "detail": f"level {_g('coal_offer_margin_level')} / anchor "
                   f"{_g('coal_offer_margin_anchor')} — ERCOT-137 keeper, CLOSED",
         "status": "ARMED (closed lane)"},
        {"class": "COAL", "band": "min-load", "mechanism":
         "ercot_coal_min_config_floor + coal_mustrun_per_plant",
         "detail": "the two FLOORS (not price mechanisms)", "status": "ARMED"},
        {"class": "CC", "band": "committed+econ", "mechanism":
         "gas_offer_net_revenue_margin",
         "detail": f"anchor {_g('gas_offer_margin_anchor')} $/MMBtu — the all-six "
                   f"measured margin form", "status": "ARMED"},
        {"class": "CC", "band": "committed+econ+peak", "mechanism":
         "offer_curve_by_group CC_REGULAR band multipliers",
         "detail": str(_g("offer_curve_by_group", {}).get("CC_REGULAR", {})),
         "status": "ARMED"},
        {"class": "CC", "band": "econ (P1 only)", "mechanism":
         "ercot_offer_surface_cleared_share (+_rt)",
         "detail": f"{_g('ercot_offer_surface_cleared_share')} / rt="
                   f"{_g('ercot_offer_surface_cleared_share_rt')} mode="
                   f"{_g('ercot_offer_surface_cleared_share_rt_mode')}",
         "status": "ARMED"},
        {"class": "CC", "band": "peak (P1 only)", "mechanism":
         "ercot_offer_surface_conditional",
         "detail": f"{_g('ercot_offer_surface_conditional')} — the peak-band "
                   f"scarcity wall markup", "status": "ARMED"},
        {"class": "CC", "band": "commitment", "mechanism":
         "ercot_gas_commitment_bridge",
         "detail": f"{_g('ercot_gas_commitment_bridge')} @ min_load_frac "
                   f"{_g('ercot_gas_bridge_min_load_frac')}", "status": "ARMED"},
    ]


def _show(title: str, obj) -> None:
    print(f"\n=== {title} ===")
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        df = pd.DataFrame(obj)
        drop = [c for c in df.columns if df[c].apply(lambda v: isinstance(v, dict)).any()]
        with pd.option_context("display.width", 250, "display.max_columns", 60):
            print(df.drop(columns=drop).to_string(index=False))
    else:
        print(obj)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path, default=OUT_JSON)
    ap.add_argument("--years", type=int, nargs="*", default=[2024, 2025])
    args = ap.parse_args(argv)

    frames = load_frames()
    if not frames:
        print("no SCED subsets on disk", file=sys.stderr)
        return 2

    captures = {}
    for year in args.years:
        print(f"[capture] {year} offer seam ...", file=sys.stderr)
        captures[year] = capture_offer_surface(year)

    a = section_a(frames)
    measured, model = section_bc(frames, captures)
    d = section_d(measured, model)
    e_detail, e_verdict = section_e(frames, captures)
    h = section_h(frames, captures)
    j = section_j(captures, frames)
    f = section_f()
    g = section_g()

    _show("A footing — floored grid vs committed ERCOT-136 B2", a)
    _show("B measured curves (capability convention, matched hours)",
          [{k: v for k, v in r.items() if k != "inc_share"} for r in measured])
    _show("C model curves (same convention, MATCHED hours)",
          [{k: v for k, v in r.items() if k != "inc_share"} for r in model])
    _show("D ranking decomposition — capability-share convention", d)
    _show("E1 matched-band BID comparison ($/MWh, incremental MW)", e_detail)
    _show("E2 THE VERDICT — spread decomposition", e_verdict)
    _show("H SAME-PLANTS robustness (crosswalked plants only)", h)
    _show("J margin-form delta vs band multipliers (committed+econ)", j)
    _show("F dispatch-side (committed keeper sidecars)", f)
    _show("G rule-19 enumeration", g)

    out = {
        "lane": "ercot138-coal-gas-ranking",
        "phase": 1,
        "no_lp": True,
        "keeper": "2026-07-29-ercot137-coal-margin-measured",
        "convention": {
            "cap_share": "(minload + offered<=p) / capability",
            "inc_share": "offered<=p / (capability - minload)",
            "measured": "minload=LSL, capability=HSL, offered=Submitted TPO clipped to [LSL,HSL]",
            "model": "minload=min_gen, capability=pmax*availability, offered=tranche MW at its bid",
            "hours": "MATCHED — model evaluated on each subset's own (day, hour) set",
        },
        "coverage": {t: c for t, (_df, c) in frames.items()},
        "limits": [
            "MEASURED is ONLINE-restricted (ERCOT-123's telemetered status set); "
            "the MODEL side carries every available tranche, committed or not. "
            "That asymmetry moves the §B/§C capability SHARES (measured min-load "
            "is 0.42-0.58 of capability, the model's 0.00-0.18) and is why the "
            "verdict rests on §E's denominator-free BID comparison, not on §D.",
            "The ERCOT gas commitment bridge's min_gen floor is injected INSIDE "
            "run_energy_solve (the P0->P1 seam), i.e. AFTER this capture — so the "
            "model's CC min-load share here is its pre-bridge value. The bridge "
            "moves min_gen, never mc, so no BID number in §E is affected.",
            "The P1 startup amortization (compute_monthly_markup) needs P0 run "
            "lengths and so is absent from every model bid here; the ARMED P1 "
            "offer surfaces ARE included in the 'p1' variant. The markup is "
            "non-negative and lands overwhelmingly on gas cycling classes, so "
            "omitting it can only UNDERSTATE how dear the model's gas is.",
            "No 2023 SCED disclosure exists on disk, so 2023 has no measured "
            "counterpart and is not scored here (rule 22 is untouched either "
            "way — 2023 is a training year).",
        ],
        "A_footing": a,
        "B_measured": measured,
        "C_model": model,
        "D_ranking": d,
        "E_bid_detail": e_detail,
        "E_verdict": e_verdict,
        "H_same_plants": h,
        "J_physical_vs_markup": j,
        "F_dispatch": f,
        "G_rule19": g,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
