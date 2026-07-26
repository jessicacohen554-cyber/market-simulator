"""pjm-124 no-LP pre-check: can scoping ``ramp10`` to committed-and-online capacity tighten PJM's reserve balance?

`docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §7 names two candidate
framings for PJM's reserve SUPPLY side and marks them "none validated here".
This probe adjudicates **framing 2**: scope the per-pool 10-minute deliverable
ramp bound to genuinely committed-and-online capacity instead of the
availability-scaled whole fleet.

The motivating measurement (pjm-120 §6): the keeper carries a **mean deliverable
10-min ramp of 38.1 GW** against a **~3.7 GW** Primary requirement — roughly 10x
slack — while PJM itself cleared 1,619 MW against a 2,515 MW Synchronized
requirement. With that much headroom no ORDC step can fire, and the keeper's own
persisted reserve dual confirms it: **0 hours >= $300 of 8,759**, max $210.99.

WHAT IS AND IS NOT SCOPABLE (Manual 11 sec 4.2, the tariff the keeper prices).
The keeper's balance families are **Primary** Reserve (RTO + Mid-Atlantic/
Dominion subzone). Primary = Synchronized + **Non-Synchronized**. Non-Sync
reserve is, by definition, capacity that is OFFLINE and can start and deliver
within 10 minutes — a fast-start CT. So a commitment-state scoping of a PRIMARY
balance may remove offline **non**-fast-start iron (a cold CC/ST backs nothing)
but may NOT remove offline fast-start iron. The scoped supply is therefore

    S_scoped(t) = SUM over [ online members  UNION  offline FAST-START members ]
                  of ramp10 x availability(t)

and it is bounded below, with **no P0 dispatch and no LP at all**, by the
fast-start term alone, since fast-start members count in either commitment
state:

    F(t) = SUM over FAST-START members of ramp10 x availability(t)     <= S_scoped(t)

That floor is the decisive number this probe computes. Two further
dispatch-free terms tighten it: ``MG`` (non-fast members carrying a positive
``min_gen`` floor in hour t are online by construction — P0 solves the same
floors) and ``DISP`` (a greedy lower bound on non-fast online capacity implied
by the keeper's own committed P1 class-hourly dispatch: a class producing D MW
must have at least D MW of iron synchronized, and the ramp-minimal way to
supply it is to load the lowest-ramp-ratio plants first).

    S_lower(t) = F(t) + max( MG(t), DISP(t) )        [rigorous lower bound]
    S_upper(t) = the keeper's own cap, 38.1 GW mean  [all non-fast online]

PRE-REGISTERED KILL CRITERIA (written and committed before the probe was first
run; framing 2 is REFUTED if any fails, and no solve is spent).

  K1 MAGNITUDE — the decisive gate. The ORDC prices only when the balance
     approaches binding, i.e. when supply falls toward the requirement R
     (~3.7 GW RTO Primary). Bands fixed in advance, evaluated on the RIGOROUS
     LOWER BOUND ``S_lower`` (the most favourable case for the mechanism):
       * PASS  — worth one A/B solve: annual-mean ``S_lower <= 3 x R`` (<= ~11
         GW) AND ``S_lower <= 2 x R`` (<= ~7.4 GW) in at least 50 hours of the
         year inside the tightest net-load bin.
       * PARTIAL — ``S_lower`` falls by >= 50% from the keeper's 38.1 GW but
         stays above 2 x R in the tight bin: the framing narrows the headroom
         without reaching the regime where a demand curve can price. Recorded
         as frontier evidence; NO solve.
       * KILL — ``S_lower`` stays above 3 x R: the mechanism provably cannot
         make the balance bind, because the capacity it is allowed to remove is
         not the capacity that creates the slack. NO solve.
     Rationale for reading the LOWER bound: if even the most generous
     accounting of what the mechanism can remove leaves the balance slack, the
     realistic (P0-derived) value — which is larger — cannot do better. The
     verdict is then valid without ever knowing the true P0 online pattern.

  K2 STATE-DEPENDENCE. The reduction must be commitment-state responsive, not a
     uniform haircut: the reduction FRACTION must differ by >= 10 pp between
     the slackest and the tightest net-load quartile. A within-10 pp uniform
     reduction is a level knob on the reserve cap (rule 1: never reach the
     right number through a mechanism that isn't real) and kills the arm
     regardless of K1. Note the physically expected SIGN is that the mechanism
     shaves MOST in slack hours (fewer plants online) and LEAST in tight hours
     (nearly everything online) — which is why K1 is evaluated in the tight
     bin, where the residual actually lives.

  K3 ADMISSIBILITY (rule 13). Every quantity entering the scoping must be
     derivable from the model's own P0 run pattern plus fleet physics. If any
     hour needs the MEASURED reserve clearing (or any other measured outcome)
     to decide who is online, the arm is inadmissible and dies on the spot.
     Asserted structurally: the probe's own arms are computed from
     ``FleetArrays`` + the rule-18 physics fast-start flags + committed model
     dispatch only, and the measured PJM series is read for the REQUIREMENT
     (a published Manual 13 reliability quantity, already in the keeper) and
     for nothing else.

Pure diagnostic, no LP. Usage:

    python scripts/probes/pjm124_ramp10_scope_precheck.py \
        results/calibration/pjm121_ccbelt --year 2025 \
        --json-out results/calibration/pjm124_precheck_2025.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
# REPO itself must be on the path so ``scripts.lib.clean_io`` resolves as a
# package — without it the data/clean readers silently fall back and the
# measured overlays (east interface cut, ramp capability) refuse to load.
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

#: K1 bands, fixed before the first run (see the module docstring).
K1_PASS_MEAN_REQ_MULTIPLE = 3.0
K1_PASS_TIGHT_REQ_MULTIPLE = 2.0
K1_PASS_TIGHT_MIN_HOURS = 50
K1_PARTIAL_MIN_REDUCTION_FRAC = 0.50

#: K2 band: minimum slack-vs-tight spread in the reduction fraction.
K2_MIN_BIN_SPREAD_PP = 10.0


def plant_online_physics(fleet_arrays):
    """Return ``(group_of, grp_fast, eligible)`` for the PJM reserve fleet.

    The commitment-state machinery of
    :func:`market_sim.pipeline.commitment._pjm_plant_online_pattern` evaluated
    with an all-idle synthetic P0, which leaves the plant grouping, the
    capacity-weighted rule-18 fast-start flags and the reserve-eligibility mask
    exactly as the solve derives them (the min-down bridge only ever ADDS online
    hours, so it cannot change any of the three). The online pattern itself is
    deliberately NOT used — this probe is dispatch-free by construction (K3).

    Args:
        fleet_arrays: The reconstructed keeper ``FleetArrays``.

    Returns:
        ``(group_of, grp_fast, eligible)`` — each unit's plant-group index, the
        per-group fast-start flags, and the reserve-eligibility mask.
    """
    from market_sim.pipeline.commitment import _pjm_plant_online_pattern

    idle = np.zeros((fleet_arrays.pmax.size, 1), dtype=float)
    _online, group_of, grp_fast, eligible = _pjm_plant_online_pattern(
        fleet_arrays, idle
    )
    return group_of, grp_fast, eligible


def member_ramp(fleet_arrays, gen_idx):
    """Return the ``(n_members, T)`` availability-scaled 10-min deliverable ramp.

    The same product the solve's pool bound sums
    (:func:`market_sim.model.reserves.spec.pjm_pergen_pool_ramp10`), kept at
    member granularity so the arms can mask it.

    Args:
        fleet_arrays: The reconstructed keeper ``FleetArrays``.
        gen_idx: Member row indices from ``pjm_pergen_structure``.

    Returns:
        ``(n_members, T)`` MW.
    """
    ramp = np.asarray(fleet_arrays.ramp10, dtype=float)[gen_idx]
    avail = np.asarray(fleet_arrays.availability, dtype=float)[gen_idx]
    return ramp[:, np.newaxis] * avail


def mingen_online_mw(fleet_arrays, gen_idx, ramp_t, nonfast):
    """Return ``(T,)`` ramp from non-fast members floored online by ``min_gen``.

    A ``min_gen``-floored unit-hour is online by construction — P0 solves the
    same floors, so ``P0 >= min_gen > 0`` there (the invariant
    :func:`~market_sim.pipeline.commitment.pjm_commitment_scoped_reserve_fleet`
    relies on). Dispatch-free.

    Args:
        fleet_arrays: The reconstructed keeper ``FleetArrays``.
        gen_idx: Member row indices.
        ramp_t: ``(n_members, T)`` availability-scaled ramp.
        nonfast: ``(n_members,)`` bool, members whose plant is not fast-start.

    Returns:
        ``(T,)`` MW.
    """
    mg = getattr(fleet_arrays, "min_gen", None)
    if mg is None:
        return np.zeros(ramp_t.shape[1], dtype=float)
    floored = np.asarray(mg, dtype=float)[gen_idx] > 0.0  # (n_members, T)
    return (ramp_t * (floored & nonfast[:, np.newaxis])).sum(axis=0)


def dispatch_implied_online_mw(fleet_arrays, gen_idx, ramp_t, nonfast, klass_mw):
    """Return ``(T,)`` ramp implied online by the keeper's own class dispatch.

    A class producing ``D`` MW in hour ``t`` must have at least ``D`` MW of iron
    synchronized. The RAMP-MINIMAL way to supply ``D`` is to load the members
    with the lowest ramp-to-capacity ratio first, so committing members in
    ascending ratio until their availability-scaled capacity covers ``D`` gives
    a rigorous LOWER bound on that class's online ramp contribution.

    Only NON-FAST members are counted (fast-start members are already in the
    ``F`` floor in either commitment state, so counting them here would
    double-count). The class's own fast-start capacity is first subtracted from
    ``D`` — that much of the production could have come from fast iron.

    Args:
        fleet_arrays: The reconstructed keeper ``FleetArrays``.
        gen_idx: Member row indices.
        ramp_t: ``(n_members, T)`` availability-scaled ramp.
        nonfast: ``(n_members,)`` bool.
        klass_mw: ``{klass: (T,) MW}`` from the bundle's committed P1
            ``class_hourly`` sidecar.

    Returns:
        ``(T,)`` MW.
    """
    T = ramp_t.shape[1]
    cap_t = (
        np.asarray(fleet_arrays.pmax, dtype=float)[gen_idx][:, np.newaxis]
        * np.asarray(fleet_arrays.availability, dtype=float)[gen_idx]
    )
    labels = member_klass(fleet_arrays)[gen_idx]
    out = np.zeros(T, dtype=float)
    for kl, dispatch in klass_mw.items():
        sel = labels == kl
        if not sel.any():
            continue
        # Production attributable to non-fast iron, after crediting every MW the
        # class's fast-start members could have produced.
        fast_cap = cap_t[sel & ~nonfast].sum(axis=0) if (sel & ~nonfast).any() else 0.0
        need = np.maximum(dispatch[:T] - fast_cap, 0.0)
        rows = np.flatnonzero(sel & nonfast)
        if rows.size == 0 or not np.any(need > 0.0):
            continue
        ratio = np.divide(
            ramp_t[rows].mean(axis=1),
            np.maximum(cap_t[rows].mean(axis=1), 1e-9),
        )
        order = rows[np.argsort(ratio, kind="stable")]
        cum_cap = np.cumsum(cap_t[order], axis=0)  # (k, T)
        cum_ramp = np.cumsum(ramp_t[order], axis=0)
        # First index whose cumulative capacity covers `need`, per hour.
        idx = (cum_cap < need[np.newaxis, :]).sum(axis=0)
        idx = np.minimum(idx, order.size - 1)
        contrib = np.where(need > 0.0, cum_ramp[idx, np.arange(T)], 0.0)
        # Never credit more than the class's own total non-fast ramp.
        out += np.minimum(contrib, cum_ramp[-1])
    return out


def member_klass(fleet_arrays):
    """Return the ``(n_gen,)`` class label matching the ``class_hourly`` sidecar.

    The same classification ``run_calibration_full._dispatch_frame`` writes into
    the dispatch frame the sidecar aggregates: a non-ERCOT per-plant row carries
    its real ``plant_group`` (CC_REGULAR, CT_PEAKER, ST_GAS, ...); everything
    else falls back to ``_model_class_for_unit``; a COAL row is split into its
    EIA-923 supply class (COAL_BIT / COAL_PRB / COAL_WC). Reusing the writer's
    own helpers keeps the label sets identical by construction.

    Args:
        fleet_arrays: The reconstructed keeper ``FleetArrays``.

    Returns:
        ``(n_gen,)`` object array of labels.
    """
    from market_sim.data.fleet import FUEL_TYPE_NAMES
    from run_calibration_full import (
        _coal_supply_class,
        _model_class_for_unit,
        _plant_codes_from_unit_ids,
    )

    unit_ids = list(fleet_arrays.unit_ids)
    fuels = [FUEL_TYPE_NAMES[i] for i in np.asarray(fleet_arrays.fuel_type_idx, int)]
    bins = list(np.asarray(fleet_arrays.efficiency_bin, dtype=object))
    groups = getattr(fleet_arrays, "plant_group", None)
    groups = (
        list(np.asarray(groups, dtype=object))
        if groups is not None
        else [""] * len(unit_ids)
    )
    codes = _plant_codes_from_unit_ids(unit_ids, numeric_head=True)
    out = []
    for g, uid in enumerate(unit_ids):
        k = groups[g] or _model_class_for_unit(uid, fuels[g], bins[g])
        if k == "COAL":
            k = _coal_supply_class(int(codes[g]))
        out.append(k)
    return np.asarray(out, dtype=object)


def class_hourly_mw(bundle: Path, year: int, hours: int) -> dict:
    """Return ``{klass: (hours,) MW}`` from the bundle's committed P1 sidecar.

    Args:
        bundle: The calibration bundle directory.
        year: Solve year.
        hours: Expected hour count.

    Returns:
        Mapping of class label to its hourly P1 dispatch. Empty when the
        sidecar is absent.
    """
    import pandas as pd

    path = Path(bundle) / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    out = {}
    for kl, grp in df.groupby("klass", observed=True):
        series = np.zeros(hours, dtype=float)
        hr = grp["hour"].to_numpy(dtype=int)
        keep = hr < hours
        series[hr[keep]] = grp["mw"].to_numpy(dtype=float)[keep]
        out[str(kl)] = series
    return out


def net_load_bins(state, hours: int, n_bins: int = 4):
    """Return the ``(hours,)`` net-load quartile index, 0 = slackest.

    Same LP-served net-load convention as the offer builders' call site
    (``run_calibration.run_year``), so the hour->bin mapping matches every other
    PJM probe.

    Args:
        state: ``run_year``'s ``fleet_only`` state dict.
        hours: Hour count.
        n_bins: Number of equal-population bins.

    Returns:
        ``(hours,)`` int bin index.
    """
    net = (
        state["demand"].sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )[:hours]
    q = np.quantile(net, np.linspace(0, 1, n_bins + 1)[1:-1])
    return np.searchsorted(q, net, side="right"), net


def main() -> int:
    """Compute the arms, evaluate K1-K3, print and persist the verdict."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, meta = reconstruct_bundle_fleet(args.bundle, args.year)
    fa, config = state["fleet_arrays"], state["config"]
    hours = int(meta["hours"])
    if getattr(fa, "ramp10", None) is None:
        raise SystemExit(
            "the reconstructed fleet carries no ramp10 — the reserve co-opt is "
            "not engaged and every arm below would be meaningless"
        )

    from market_sim.model.reserves.spec import pjm_pergen_structure
    from market_sim.results.scarcity import (
        load_pjm_measured_mad_reserve_requirement,
        load_pjm_measured_reserve_requirement,
    )

    gen_idx, col, n_r = pjm_pergen_structure(fa)
    group_of, grp_fast, _eligible = plant_online_physics(fa)
    fast = grp_fast[group_of[gen_idx]]
    nonfast = ~fast
    ramp_t = member_ramp(fa, gen_idx)[:, :hours]

    req = load_pjm_measured_reserve_requirement(args.year, hours)
    if req is None:
        raise SystemExit(
            f"no measured PJM Primary requirement for {args.year} — the K1 "
            "bands are stated as multiples of it and cannot be evaluated"
        )
    req_mad = load_pjm_measured_mad_reserve_requirement(args.year, hours)
    R = float(np.mean(req))

    # ---- arms -------------------------------------------------------------
    keeper = ramp_t.sum(axis=0)  # A: whole availability-scaled fleet
    F = ramp_t[fast].sum(axis=0)  # fast-start floor (either commitment state)
    MG = mingen_online_mw(fa, gen_idx, ramp_t, nonfast)
    klass_mw = class_hourly_mw(args.bundle, args.year, hours)
    DISP = (
        dispatch_implied_online_mw(fa, gen_idx, ramp_t, nonfast, klass_mw)
        if klass_mw
        else np.zeros(hours)
    )
    online_only_lower = np.maximum(MG, DISP)
    scoped_lower = F + online_only_lower
    scoped_upper = keeper

    print(
        f"\nPJM {args.year}: {n_r} pools / {gen_idx.size} member units; "
        f"{int(fast.sum())} fast-start members "
        f"({fa.pmax[gen_idx][fast].sum() / 1e3:.1f} GW nameplate)"
    )
    print(f"  measured Primary requirement (RTO): mean {R / 1e3:.2f} GW")
    if req_mad is not None:
        print(
            f"  measured Primary requirement (MAD): mean {req_mad.mean() / 1e3:.2f} GW"
        )
    print(f"  A keeper cap             mean {keeper.mean() / 1e3:7.2f} GW")
    print(
        f"  F fast-start floor       mean {F.mean() / 1e3:7.2f} GW  "
        f"({100 * F.mean() / keeper.mean():.1f}% of the keeper cap)"
    )
    print(f"  MG min-gen online        mean {MG.mean() / 1e3:7.2f} GW")
    print(f"  DISP dispatch-implied    mean {DISP.mean() / 1e3:7.2f} GW")
    print(
        f"  S_lower = F + max(MG,DISP) mean {scoped_lower.mean() / 1e3:5.2f} GW  "
        f"= {scoped_lower.mean() / R:.1f}x the requirement"
    )
    print(f"  S_upper (all online)     mean {scoped_upper.mean() / 1e3:7.2f} GW")
    # The STRICT variant, reported for the record and NOT a candidate: deleting
    # offline fast-start ramp from a PRIMARY balance prices Synchronized reserve
    # while calling it Primary (Manual 11 sec 4.2), i.e. it makes reserve
    # artificially scarce by a product mismatch (rule 1). Its own lower bound is
    # max(MG, DISP) — if even that stays well above the requirement, the whole
    # framing-2 family is closed in its admissible AND inadmissible forms.
    print(
        f"  [strict online-only, INADMISSIBLE] lower bound mean "
        f"{online_only_lower.mean() / 1e3:.2f} GW = "
        f"{online_only_lower.mean() / R:.1f}x the requirement"
    )

    # ---- K1 ---------------------------------------------------------------
    hour_bin, net = net_load_bins(state, hours)
    tight = hour_bin == hour_bin.max()
    tight_hours_under = int(
        (scoped_lower[tight] <= K1_PASS_TIGHT_REQ_MULTIPLE * R).sum()
    )
    mean_multiple = float(scoped_lower.mean() / R)
    reduction = 1.0 - float(scoped_lower.mean() / keeper.mean())
    k1_pass = (
        mean_multiple <= K1_PASS_MEAN_REQ_MULTIPLE
        and tight_hours_under >= K1_PASS_TIGHT_MIN_HOURS
    )
    k1_kill = mean_multiple > K1_PASS_MEAN_REQ_MULTIPLE
    k1 = "PASS" if k1_pass else ("PARTIAL" if not k1_kill else "KILL")
    if k1 == "KILL" and reduction >= K1_PARTIAL_MIN_REDUCTION_FRAC:
        k1 = "KILL (reduction material but still slack)"

    # ---- K2 ---------------------------------------------------------------
    frac = {}
    for b in range(int(hour_bin.max()) + 1):
        sel = hour_bin == b
        frac[b] = 100.0 * (1.0 - float(scoped_lower[sel].mean() / keeper[sel].mean()))
    spread = abs(frac[max(frac)] - frac[min(frac)])
    k2 = "PASS" if spread >= K2_MIN_BIN_SPREAD_PP else "KILL (uniform haircut)"

    # ---- K3 ---------------------------------------------------------------
    # Structural: every arm above is a function of FleetArrays (ramp10,
    # availability, pmax, min_gen), the rule-18 physics fast-start flags, and
    # the model's own committed P1 dispatch. No measured reserve clearing, no
    # measured price, no measured outcome enters. The measured PJM series is
    # read only for the REQUIREMENT (Manual 13, already the keeper's input).
    k3 = "PASS (fleet physics + model dispatch only)"

    print(
        "\n  net-load-bin reduction fraction (slack -> tight): "
        + ", ".join(f"bin{b} {frac[b]:.1f}%" for b in sorted(frac))
    )
    print(
        f"  tight-bin hours with S_lower <= {K1_PASS_TIGHT_REQ_MULTIPLE:.0f}x R: "
        f"{tight_hours_under} of {int(tight.sum())}"
    )
    print(
        f"\n  K1 MAGNITUDE      {k1}   (mean S_lower = {mean_multiple:.1f}x R; "
        f"reduction {100 * reduction:.1f}%)"
    )
    print(f"  K2 STATE-DEP      {k2}   (bin spread {spread:.1f} pp)")
    print(f"  K3 ADMISSIBILITY  {k3}")
    verdict = "SOLVE" if (k1 == "PASS" and k2 == "PASS") else "NO SOLVE"
    print(f"\n  VERDICT: {verdict}\n")

    report = {
        "probe": "pjm124_ramp10_scope_precheck",
        "bundle": str(args.bundle),
        "year": args.year,
        "pools": int(n_r),
        "members": int(gen_idx.size),
        "fast_members": int(fast.sum()),
        "fast_nameplate_gw": float(fa.pmax[gen_idx][fast].sum() / 1e3),
        "requirement_rto_mean_mw": R,
        "requirement_mad_mean_mw": (
            float(req_mad.mean()) if req_mad is not None else None
        ),
        "arms_mean_mw": {
            "A_keeper_cap": float(keeper.mean()),
            "F_fast_floor": float(F.mean()),
            "MG_mingen_online": float(MG.mean()),
            "DISP_dispatch_implied": float(DISP.mean()),
            "S_lower": float(scoped_lower.mean()),
            "S_upper": float(scoped_upper.mean()),
            "S_strict_online_only_lower": float(online_only_lower.mean()),
        },
        "s_lower_over_req_mean": mean_multiple,
        "s_strict_online_only_over_req_mean": float(online_only_lower.mean() / R),
        "reduction_frac": reduction,
        "reduction_frac_by_bin_pp": {str(b): frac[b] for b in sorted(frac)},
        "tight_bin_hours_under_2x_req": tight_hours_under,
        "tight_bin_hours": int(tight.sum()),
        "k1": k1,
        "k2": k2,
        "k3": k3,
        "verdict": verdict,
        "config_gates": {
            k: bool(getattr(config, k, False))
            for k in (
                "energy_reserve_coopt",
                "pjm_reserve_pergen",
                "pjm_reserve_supply_cap",
            )
        },
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2))
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
