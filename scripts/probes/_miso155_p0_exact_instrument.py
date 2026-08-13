"""miso-155 — the CT commitment instrument with the P0 **READ, not reconstructed**.

Pre-registration:
``results/calibration/PREREG-miso155-p0-exact-commitment-instrument-2026-08-13.md``
(pushed at ``a920c85``, blob ``07b12e5a``, verified byte-identical against the
FETCHED remote ref BEFORE any adjudicating statistic).

THE OBJECT (PREREG section 0). miso-154 built the CT commitment instrument and
left it gated on an uncertainty WIDER than its own bar: with no committed P0
pass, the markup's run-length source had to be reconstructed from P1 prices,
and bounding that proxy (T-9) gave spans of **21.7 / 20.9 / 18.4 pp** against
a bar only 20 pp wide — with both known biases pointing colder. A second
approximation (T-10, the v4 band series keyed on renewable POTENTIAL where the
sidecars carry only DISPATCHED) added a further **4.66-5.51 pp**.

The handoff offered two branches: (A) close the gap, or (B) charter the CT
offer level now at a widened +/-15 % bar. **This session takes (A)** — because
the P0 pattern is not unobservable, it is a quantity the model itself computes
at the P0->P1 seam and then discards, and widening a tolerance so an estimate
can clear it is what rule 14 ``[R-ACCURATE]`` exists to stop. (B) also does not
survive its own arithmetic: 2023's T-9 interval **[-28.98 %, -7.28 %]** is not
contained in [-15 %, +15 %].

WHAT CLOSES IT. ``--persist-p0-commitment`` (this session's build) writes two
additive, opt-in sidecars from the solve itself:

* ``hourly/p0_commitment_<year>.parquet`` — the bit-packed P0 on/off pattern,
  which is the COMPLETE input ``compute_monthly_markup`` draws from P0 (it
  touches the P0 dispatch only through ``find_runs(dispatch > 0.05 * pmax)``).
* ``hourly/startup_run_ratio_<year>.parquet`` — the ``(T,)`` conditional band
  series the markup was actually called with.

Rebuilding a surrogate dispatch ``pmax * unpacked`` and handing it to the
PRODUCTION ``compute_monthly_markup`` returns the bit-identical array the solve
used. **T-9 and T-10 both collapse to zero** — the handoff's option (A) only
claimed T-9.

THE LEGS (PREREG section 4), all scored on ``CT_PEAKER`` energy at the top-200
model-demand hours against the CONTROL's own ``class_hourly`` (T-16: the
persisted P0 belongs to this solve, so it must be validated against this
solve's P1):

* ``BASELINE`` — price-taking on ``mc_base``. Validity gate V1: must reproduce
  miso-153's published T-6b at +21.99 / +22.14 / +23.72 % to +/-0.01 pp.
* ``PROXY`` — miso-154's L1, reconstructed P0 + reconstructed v4, re-run on
  THIS bundle so the exact-vs-proxy delta is internally controlled (T-17).
* ``L1X`` — price-taking on the EXACT bid. **THE GATING LEG.**
* ``L1F`` — floors first, then price-taking on the headroom. Repairs L1's one
  known structural defect (price-taking cannot dispatch an out-of-merit
  min-gen floor). **Conditionally gating, and its admissibility is MEASURED,
  not chosen**: it counts only if out-of-merit floored CT energy at the
  top-200 hours is >= 5 % of control CT top-200 energy in >= 2 of 3 years.
* ``L2`` — merit-order. Reported, NEVER gates (it conserves the control's own
  hourly thermal total by construction).

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds neither marker.

Usage::

    PYTHONPATH=$PWD:$PWD/src .venv/bin/python \\
        scripts/probes/_miso155_p0_exact_instrument.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso154_ct_commitment as _m154  # noqa: E402

# The CONTROL bundle — the keeper replayed at HEAD with the single additive
# delta ``persist_p0_commitment=true``. Repointed on BOTH modules and AFTER
# importing _miso154 (which sets _m134.BUNDLE to the keeper at its own import),
# else the prices/class_hourly would come from one solve and the P0 from
# another (T-16).
BUNDLE = REPO / "results/calibration/miso155_p0_A"
KEEPER = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"control bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
_m154.BUNDLE = BUNDLE

from _miso154_ct_commitment import (  # noqa: E402
    BAR,
    TARGET,
    YearBasis,
    assemble_year,
    class_energy_residual,
    commitment_markup,
    markup_census,
    reconstruct_p0,
    reconstruct_p1_meritorder,
    reconstruct_p1_pricetaking,
)
from _miso134_ct_night_order_screen import keeper_config  # noqa: E402

YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/_miso155_p0_exact_instrument.json"

# V1 (PREREG section 7): miso-153's published T-6b, which miso-154 reproduced
# to +/-0.001 pp. The instrument must land on it again BEFORE any adjudicating
# statistic — the check that caught miso-154's truncated-checkout void run.
V1_PUBLISHED = {2023: 0.2199, 2024: 0.2214, 2025: 0.2372}
V1_TOL = 1e-4  # +/-0.01 pp
V1_NGEN = {2023: 2929, 2024: 2923, 2025: 2923}

# miso-154's published L1 (reconstructed P0 + reconstructed v4), for the
# exact-vs-proxy comparison and the S-WARMER trigger.
M154_L1 = {2023: -0.13212201330533474, 2024: -0.0752, 2025: -0.0447}
# miso-154 T-9 "never" bound — the markup CEILING. Nothing exact may be colder
# (S-CEILING).
M154_NEVER = {2023: -0.28975363505951107, 2024: -0.2411, 2025: -0.1865}

# PREREG section 4.2: L1F is admissible only if out-of-merit floored CT energy
# at the top-200 hours reaches this share of control CT top-200 energy in at
# least 2 of 3 years. Set from the mechanism, not the answer.
L1F_ADMIT_SHARE = 0.05
L1F_ADMIT_YEARS = 2


# ---------------------------------------------------------------------------
# Reading the exact P0 record
# ---------------------------------------------------------------------------


def read_p0_commitment(year: int, basis: YearBasis) -> tuple[np.ndarray, dict]:
    """Return the EXACT P0 surrogate dispatch for ``year``, plus its alignment.

    Rebuilds ``pmax[:, None] * unpacked_pattern`` from the control's own
    ``hourly/p0_commitment_<year>.parquet``. Because
    ``compute_monthly_markup`` compares ``dispatch > 0.05 * pmax``, this
    surrogate reproduces the recorded boolean exactly for every ``pmax > 0``
    row, so the production markup it drives is BIT-IDENTICAL to the one the
    solve used. The markup is READ, never re-implemented (T-8 intact).

    **NOT PRE-REGISTERED — the join is by ``unit_id``, not by position, and
    the reason is a discrepancy this sidecar is the first thing to expose.**
    The probe's reconstructed fleet and the SOLVE's own fleet are not the same
    size (MISO 2023: reconstruction 2,929 rows against a solve that dispatched
    2,787). A positional join would therefore have silently attributed one
    unit's run pattern to another. The join is on the identifier, every
    unmatched row on either side is counted and classed in the returned
    diagnostic, and rows the solve does not carry are recorded as never-on —
    which is what the model itself did with them: nothing.

    Returns ``(surrogate_dispatch, alignment_diagnostic)``.
    """
    df = pd.read_parquet(BUNDLE / f"hourly/p0_commitment_{year}.parquet")
    bits = np.stack([np.frombuffer(b, dtype=np.uint8) for b in df["on_bits"]])
    solve_on = np.unpackbits(bits, axis=1)[:, : basis.n_hours].astype(bool)
    solve_ids = [str(u) for u in df["unit_id"]]
    row_of = {u: i for i, u in enumerate(solve_ids)}
    if len(row_of) != len(solve_ids):
        raise SystemExit(f"P0 sidecar {year}: duplicate unit_id — join is unsafe")

    fleet_ids = [str(g.unit_id) for g in basis.fleet]
    n_gen = len(fleet_ids)
    on = np.zeros((n_gen, basis.n_hours), dtype=bool)
    matched = np.zeros(n_gen, dtype=bool)
    for i, uid in enumerate(fleet_ids):
        j = row_of.get(uid)
        if j is not None:
            on[i] = solve_on[j]
            matched[i] = True

    pmax = np.asarray(basis.arrays.pmax, dtype=np.float64)
    unmatched_by_class: dict[str, dict] = {}
    for k in sorted(set(basis.labels[~matched].tolist())):
        sel = (~matched) & (basis.labels == k)
        unmatched_by_class[k] = {
            "n": int(sel.sum()),
            "cap_mw": float(pmax[sel].sum()),
        }
    align = {
        "solve_fleet_rows": len(solve_ids),
        "probe_fleet_rows": n_gen,
        "matched": int(matched.sum()),
        "probe_only": int((~matched).sum()),
        "probe_only_cap_mw": float(pmax[~matched].sum()),
        "solve_only": int(len(solve_ids) - matched.sum()),
        "probe_only_by_class": unmatched_by_class,
        "target_matched": int((matched & (basis.labels == TARGET)).sum()),
        "target_total": int((basis.labels == TARGET).sum()),
        "target_probe_only_cap_mw": float(
            pmax[(~matched) & (basis.labels == TARGET)].sum()
        ),
    }
    return pmax[:, None] * on, align


def read_run_ratio(year: int, basis: YearBasis) -> np.ndarray | None:
    """Return the EXACT ``(T,)`` conditional band series, or ``None`` (v3)."""
    path = BUNDLE / f"hourly/startup_run_ratio_{year}.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path).sort_values("hour")
    ratio = df["run_ratio"].to_numpy(dtype=float)
    if ratio.size != basis.n_hours:
        raise SystemExit(
            f"run-ratio sidecar {year}: {ratio.size} hours vs {basis.n_hours}"
        )
    return ratio


# ---------------------------------------------------------------------------
# L1F — floors first, then price-taking
# ---------------------------------------------------------------------------


def _floor_matrix(basis: YearBasis) -> np.ndarray:
    """The control's own ``(n_gen, T)`` min-gen floor, clipped to availability."""
    mg = basis.arrays.min_gen
    if mg is None:
        floor = np.broadcast_to(
            np.asarray(basis.arrays.pmin, dtype=np.float64)[:, None],
            basis.availcap.shape,
        )
    else:
        floor = np.asarray(mg, dtype=np.float64)
    return np.minimum(floor, basis.availcap)


def reconstruct_p1_floorsfirst(basis: YearBasis, mc_bid: np.ndarray) -> np.ndarray:
    """**L1F** — dispatch every floor, then price-take on the headroom only.

    L1 (price-taking) has one known structural defect: it CANNOT dispatch an
    out-of-merit min-gen floor, so it under-reproduces any heavily floored
    class by construction — miso-154 measured this on ``ST_GAS`` (47 % forced,
    reading -11.8 / -17.0 / -19.4 %). L1F repairs exactly that one thing and
    nothing else: the floor is always served, and price-taking fills only the
    capacity above it.

    Unlike L2 this does NOT conserve the control's hourly thermal total, so a
    good L1F number is not an artifact of its own clearing.
    """
    floor = _floor_matrix(basis)
    headroom = np.maximum(basis.availcap - floor, 0.0)
    in_merit = (mc_bid <= basis.zprice) & (headroom > 1e-6)
    return floor + np.where(in_merit, headroom, 0.0)


def floored_out_of_merit_share(
    basis: YearBasis, mc_bid: np.ndarray, klass: str = TARGET
) -> dict:
    """**PREREG section 4.2** — is L1F admissible at all?

    Measures the floored ``klass`` MW at the top-200 hours whose own bid is
    ABOVE the zonal price — i.e. exactly the energy price-taking structurally
    cannot see — as a share of the control's ``klass`` top-200 energy. Below
    the pre-registered threshold, L1F is arithmetically ~L1X and must not be
    quoted whatever it reads.
    """
    sel = basis.labels == klass
    floor = _floor_matrix(basis)[sel][:, basis.top]
    out_of_merit = mc_bid[sel][:, basis.top] > basis.zprice[sel][:, basis.top]
    forced = float(np.where(out_of_merit, floor, 0.0).sum())
    control = (
        float(basis.class_hourly.loc[klass].to_numpy()[basis.top].sum())
        if klass in basis.class_hourly.index
        else 0.0
    )
    return {
        "out_of_merit_floored_mwh": forced,
        "control_top200_mwh": control,
        "share": forced / control if control else None,
        "threshold": L1F_ADMIT_SHARE,
        "admissible_this_year": bool(control and forced / control >= L1F_ADMIT_SHARE),
    }


# ---------------------------------------------------------------------------
# Per-year driver
# ---------------------------------------------------------------------------


def _per_class(basis: YearBasis, disp: np.ndarray) -> dict:
    """Every assembled thermal class's residual — so a CT 'fix' that wrecks
    another class cannot pass unseen (the miso-154 section 6 addition)."""
    return {
        k: class_energy_residual(basis, disp, k)["top200"]
        for k in _m154._thermal_classes(basis)
    }


def run_year(cfg, year: int) -> dict:
    """Measure every leg for one year. Returns the record for ``year``."""
    basis = assemble_year(cfg, year)
    rec: dict = {
        "n_gen": len(basis.fleet),
        "top200_demand_gw_mean": float(basis.demand[basis.top].mean() / 1e3),
    }

    # --- V1: the validity gate, computed FIRST -----------------------------
    baseline = reconstruct_p1_pricetaking(basis, basis.mc_base)
    rec["V1_baseline_pricetaking_mc_base"] = class_energy_residual(basis, baseline)

    # --- the exact P0 and the exact band series ----------------------------
    p0_exact, align = read_p0_commitment(year, basis)
    rec["ALIGN_fleet"] = align
    ratio_exact = read_run_ratio(year, basis)
    markup_exact = commitment_markup(basis, p0_exact, cfg, run_ratio_t=ratio_exact)
    mc_bid_exact = basis.mc_base + markup_exact

    # T-12: the round trip, asserted on real data, not just in the unit test.
    on = p0_exact > 0.0
    rec["T12_p0_pattern"] = {
        "on_cells": int(on.sum()),
        "on_share": float(on.mean()),
        "gens_never_on": int((~on.any(axis=1)).sum()),
        "gens_always_on": int(on.all(axis=1).sum()),
        "zero_pmax_rows": int((np.asarray(basis.arrays.pmax) <= 0.0).sum()),
    }

    # T-10, now MEASURED rather than bounded: exact vs reconstructed v4.
    ratio_recon = basis.run_ratio_t
    rec["T10_band_series"] = {
        "exact_present": ratio_exact is not None,
        "recon_present": ratio_recon is not None,
        "exact_top200_mean": (
            float(ratio_exact[basis.top].mean()) if ratio_exact is not None else None
        ),
        "recon_top200_mean": (
            float(ratio_recon[basis.top].mean()) if ratio_recon is not None else None
        ),
        "max_abs_diff": (
            float(np.abs(ratio_exact - ratio_recon).max())
            if (ratio_exact is not None and ratio_recon is not None)
            else None
        ),
    }

    # --- T-17: the PROXY leg, re-run on THIS bundle ------------------------
    p0_proxy = reconstruct_p0(basis, "pricetaking")
    markup_proxy = commitment_markup(basis, p0_proxy, cfg, run_ratio_t=ratio_recon)
    rec["PROXY_L1"] = class_energy_residual(
        basis, reconstruct_p1_pricetaking(basis, basis.mc_base + markup_proxy)
    )
    rec["markup_census_exact"] = markup_census(basis, markup_exact)
    rec["markup_census_proxy"] = markup_census(basis, markup_proxy)

    # --- L1X: THE GATING LEG ----------------------------------------------
    l1x = reconstruct_p1_pricetaking(basis, mc_bid_exact)
    rec["L1X_pricetaking_exact_bid"] = class_energy_residual(basis, l1x)
    rec["per_class_L1X"] = _per_class(basis, l1x)

    # --- NOT PRE-REGISTERED: the fleet-ALIGNED legs ------------------------
    # The reconstruction dispatches capacity the model does not carry (see
    # ALIGN_fleet). Restricting every leg to the units the SOLVE actually has
    # is the like-for-like fleet; reported alongside, never substituted for
    # the as-published basis, so the V1 comparison stays honest.
    in_solve = np.zeros(len(basis.fleet), dtype=bool)
    solve_ids = set(
        str(u)
        for u in pd.read_parquet(
            BUNDLE / f"hourly/p0_commitment_{year}.parquet", columns=["unit_id"]
        )["unit_id"]
    )
    for i, g in enumerate(basis.fleet):
        in_solve[i] = str(g.unit_id) in solve_ids
    mask = in_solve[:, None]
    rec["ALIGNED_baseline"] = class_energy_residual(basis, baseline * mask)
    rec["ALIGNED_L1X"] = class_energy_residual(basis, l1x * mask)
    rec["ALIGNED_per_class_L1X"] = _per_class(basis, l1x * mask)

    # --- L1F: conditionally gating, admissibility measured -----------------
    rec["L1F_admissibility"] = floored_out_of_merit_share(basis, mc_bid_exact)
    l1f = reconstruct_p1_floorsfirst(basis, mc_bid_exact)
    rec["L1F_floorsfirst"] = class_energy_residual(basis, l1f)
    rec["per_class_L1F"] = _per_class(basis, l1f)
    rec["ALIGNED_L1F"] = class_energy_residual(basis, l1f * mask)

    # --- L2: reported, never gates ----------------------------------------
    rec["L2_meritorder"] = class_energy_residual(
        basis, reconstruct_p1_meritorder(basis, mc_bid_exact)
    )
    return rec


def _verdict(years: dict) -> dict:
    """Apply PREREG section 6's branch table to the measured legs."""

    def _clears(leg: str) -> list[int]:
        return [
            y
            for y, r in years.items()
            if r[leg]["top200"]["resid"] is not None
            and abs(r[leg]["top200"]["resid"]) <= BAR
        ]

    l1x_ok = _clears("L1X_pricetaking_exact_bid")
    admit_years = [
        y for y, r in years.items() if r["L1F_admissibility"]["admissible_this_year"]
    ]
    l1f_admissible = len(admit_years) >= L1F_ADMIT_YEARS
    l1f_ok = _clears("L1F_floorsfirst") if l1f_admissible else []

    if len(l1x_ok) == 3:
        branch = "C-CLEAR"
    elif l1f_admissible and len(l1f_ok) == 3:
        branch = "C-FLOOR"
    elif max(len(l1x_ok), len(l1f_ok)) == 2:
        branch = "C-PARTIAL"
    else:
        branch = "C-FAIL"

    triggers = {
        "S-CEILING": [
            y
            for y, r in years.items()
            if r["L1X_pricetaking_exact_bid"]["top200"]["resid"] < M154_NEVER[y] - 1e-9
        ],
        "S-WARMER": all(
            years[y]["L1X_pricetaking_exact_bid"]["top200"]["resid"] > M154_L1[y]
            for y in years
        ),
        "S-INERT": [
            y
            for y, r in years.items()
            if abs(
                r["markup_census_exact"]["cap_weighted_mean_per_mwh"]
                - r["markup_census_proxy"]["cap_weighted_mean_per_mwh"]
            )
            < 0.01 * max(r["markup_census_proxy"]["cap_weighted_mean_per_mwh"], 1e-12)
        ],
    }
    return {
        "branch": branch,
        "bar": BAR,
        "L1X_years_clearing": l1x_ok,
        "L1F_admissible": l1f_admissible,
        "L1F_admissible_years": admit_years,
        "L1F_years_clearing": l1f_ok,
        "triggers": triggers,
    }


def main() -> None:
    """Run every year, apply the branch table, write the record."""
    cfg = keeper_config()
    years = {y: run_year(cfg, y) for y in YEARS}

    v1 = {
        y: {
            "measured": years[y]["V1_baseline_pricetaking_mc_base"]["top200"]["resid"],
            "published": V1_PUBLISHED[y],
            "delta_pp": 100.0
            * (
                years[y]["V1_baseline_pricetaking_mc_base"]["top200"]["resid"]
                - V1_PUBLISHED[y]
            ),
            "n_gen": years[y]["n_gen"],
            "n_gen_published": V1_NGEN[y],
            "pass": bool(
                abs(
                    years[y]["V1_baseline_pricetaking_mc_base"]["top200"]["resid"]
                    - V1_PUBLISHED[y]
                )
                <= V1_TOL
                and years[y]["n_gen"] == V1_NGEN[y]
            ),
        }
        for y in YEARS
    }

    record = {
        "prereg": "PREREG-miso155-p0-exact-commitment-instrument-2026-08-13.md",
        "bundle": BUNDLE.name,
        "keeper": KEEPER.name,
        "V1_validity_gate": v1,
        "verdict": _verdict(years),
        "years": {str(y): years[y] for y in YEARS},
    }
    OUT.write_text(json.dumps(record, indent=2, default=float))

    print(f"V1 validity gate: {'PASS' if all(v['pass'] for v in v1.values()) else 'FAIL'}")
    for y in YEARS:
        print(
            f"  {y}: baseline {v1[y]['measured']:+.5f} vs published "
            f"{v1[y]['published']:+.4f}  ({v1[y]['delta_pp']:+.4f} pp)  "
            f"n_gen {v1[y]['n_gen']}/{v1[y]['n_gen_published']}"
        )
    print()
    for y in YEARS:
        r = years[y]
        print(
            f"{y}: PROXY {r['PROXY_L1']['top200']['resid']:+.4f} | "
            f"L1X {r['L1X_pricetaking_exact_bid']['top200']['resid']:+.4f} | "
            f"L1F {r['L1F_floorsfirst']['top200']['resid']:+.4f} "
            f"(admit share {r['L1F_admissibility']['share']}) | "
            f"L2 {r['L2_meritorder']['top200']['resid']:+.4f}"
        )
    print()
    print(json.dumps(record["verdict"], indent=2, default=float))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
