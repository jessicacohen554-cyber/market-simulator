"""nyiso-206 phase 0 — does ``cheapest_first`` deliver the physics that
``floor_pct = commit_frac x min_stable_pct`` asserts on the Capital_Hudson ``ST_GAS`` limb?

ZERO LP. A construction audit, not a level choice and not an operator choice.

THE QUESTION. ``scripts/data/derive_reliability_coeffs.py``'s own module docstring documents
what the coefficient means, and it is a PER-UNIT physics statement with a commitment count on
top: ``min_stable_pct`` is *"the class's physical min-stable level (Pmin/Pmax) of a COMMITTED
unit ... once committed it sits at this physical Pmin"* (ST_GAS 0.12, WWSIS-2 Table 7, via
``constants.MIN_STABLE_PCT_PHYSICAL``), and ``commit_frac`` is *"the share of the class's
nameplate that is online on temperature-flagged days — a commitment count"* (0.8105). So
``floor_pct = 0.0973`` asserts: on a design cooling day ~81 % of the class's nameplate is
committed and EACH COMMITTED UNIT SITS AT 12 % OF ITS OWN CAPACITY.

The delivery mechanism is ``model/interchange/core.py::_distribute_group_floor``, whose per-row
cap in the fill is ``cap_r = pmax[r] * availability[r, :]`` — the row's FULL available capacity,
NOT ``min_stable_pct x cap_r``. ``pro_rata``'s branch instead floors every row at
``frac x cap_r = 0.0973 x cap_r``, which is below 0.12 for every row and so never asserts more
than the physics does. The two operators are therefore NOT symmetric with respect to the
coefficient's construction, and that is a different fact from the one nyiso-205 adjudicated.

WHAT THIS IS NOT.
  * NOT the operator question. nyiso-205 CONFIRMED ``cheapest_first`` and REFUTED ``pro_rata``
    on 9-of-9 g/a evidence plus a decisive rule-17 leg; DO-NOT-REDO. That verdict is about
    WHICH units the floor lands on. This probe asks AT WHAT LEVEL, relative to each row's own
    physical minimum stable point, it is placed on the rows the fill reaches.
  * NOT the membership question (nyiso-204 / 204b, refused twice; DO-NOT-REDO).
  * NOT a re-derivation of ``floor_pct`` (rule 23 ``[R-FROZEN-DERIVE]`` — no source data has
    updated, and none is consulted for a level). Nothing here proposes a value.
  * NOT a patch. ``_distribute_group_floor`` is the shared kernel behind 37 of 50 live floor
    limbs program-wide (ERCOT 5/5, MISO 12/12, NEISO 6/6, PJM 14/14 by dataclass default), so
    any repair is owner court, not a single-ISO lane's (rule 25 ``[R-ISO-SCOPE]``).

THE MEASUREMENT (PREREG ``results/calibration/PREREG-nyiso206-ch-fill-level-basis.md`` §4).
On the limb's own binding window — rebuilt from the engine's own code path (``iso_zone_tmax``
-> ``tmax > 31.1 C`` -> ``_bridge_flagged_runs(48)``), whose 504 / 432 / 600 h counts are
RE-VERIFIED before anything else is computed and a mismatch ABORTS — and on the keeper bundle's
own ``fleet_only`` reconstruction:

1. the row-level intensity ``i = floor / cap_r`` over every (row, hour) cell the fill raises
   above ``pmin``, banded at ``i >= 0.999`` (pinned at full availability), ``[0.12, 0.999)``
   (above min-stable, not pinned) and ``< 0.12`` (at or below min-stable);
2. the same three bands in FORCED ENERGY (``sum max(0, floor - pmin)``), so a rare-but-large
   band cannot hide behind a cell count nor a frequent-but-tiny one be inflated by it;
3. per plant and per row, so the answer says WHICH rows are pinned;
4. the ``pro_rata`` counterfactual on the same statistic — reported to calibrate the scale only.
   It is ARITHMETICALLY FORCED (``i == 0.0973 < 0.12`` for every raised row), so it is NOT
   evidence and the finding says so;
5. the aggregate identity ``sum floor == 0.0973 x sum cap_r`` per binding hour, to six decimals.
   If it fails, every intensity number is meaningless and the probe reports that instead;
6. (PREREG addendum A, declared before any number was read) the MIN-STABLE-CAPPED counterfactual:
   the same cheapest-first fill with each row capped at ``min_stable_pct x cap_r``. Reported as
   a SIZING for the owner card, explicitly NOT proposed and NOT screened. It is always feasible
   because ``floor_pct 0.0973 < min_stable_pct 0.12``, and the committed share it needs is a
   direct read on whether the delivered commitment count matches ``commit_frac``.

Every band statistic is reported over the three pre-registered hour cuts — the bridged binding
window (the limb's own, off which the verdict is read), the unbridged ``tmax > 31.1`` flagged
hours, and the binding window narrowed to h14-21 — and per year, never pooled.

Diagnostic only. Arms nothing, edits nothing, registers nothing; the registry is read, never
patched, and no CSV and no ``src/market_sim/`` file is touched.

Reproduce: ``uv run python scripts/probes/_nyiso206_ch_fill_level_basis.py``.
Writes ``results/calibration/_nyiso206_ch_fill_level_basis.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.bundle_fleet import (  # noqa: E402
    ensure_probe_path,
    reconstruct_bundle_fleet,
)

ensure_probe_path()

BUNDLE = ROOT / "results" / "calibration" / "nyiso202_startup_aware"
KEEPER_ID = "2026-09-06-nyiso-202-startup-aware"
ISO = "NYISO"
ZONE = "Capital_Hudson"
KLASS = "ST_GAS"
THRESHOLD_C = 31.1  # the limb's own day gate
MIN_EVENT_HOURS = 48  # _STEAM_MIN_EVENT_HOURS, applied to ST_GAS by the loader
FLOOR_PCT = 0.0973  # commit_frac 0.8105 x min_stable_pct 0.12 (frozen, rule 23)
COMMIT_FRAC = 0.8105  # the coefficient's commitment-count factor
MIN_STABLE_PCT = 0.12  # constants.MIN_STABLE_PCT_PHYSICAL["ST_GAS"], WWSIS-2 Table 7
YEARS = (2023, 2024, 2025)
# The binding-hour counts two committed probes already reproduce on this limb
# (_nyiso204b_ch_exclusion_variants.py, _nyiso205_ch_fill_operator.py). A mismatch
# means the reconstruction moved and every number below would be off-object.
EXPECTED_BINDING_HOURS = {2023: 504, 2024: 432, 2025: 600}
NAMES = {
    2625: "Bowline Generating Station",
    8006: "Roseton Generating LLC",
    2480: "Danskammer Generating Station",
}
PINNED = 0.999  # i >= PINNED counts as pinned at full available capacity
EPS = 1e-9
OUT = ROOT / "results" / "calibration" / "_nyiso206_ch_fill_level_basis.json"


def _limb_masks(year: int, hours: int) -> dict[str, np.ndarray]:
    """Return the limb's three pre-registered hour sets, on the engine's own code path.

    ``binding`` is the mask the engine actually applies (the bridged run mask) and the
    one the verdict is read off; ``flagged`` is the raw day gate before bridging;
    ``binding_h14_21`` narrows the binding window to the evening peak hours this
    (zone, class)'s own ``CH_ST_ev`` ramp family targets (disarmed on the keeper).
    Identical to ``_nyiso205_ch_fill_operator._limb_masks`` by intent — the cuts were
    pre-registered there and are carried forward unchanged so the two sessions'
    numbers are read on the same hours.
    """
    from market_sim.data.eia_loader import iso_zone_tmax
    from market_sim.model.interchange.core import _bridge_flagged_runs

    wx = iso_zone_tmax(ISO, year, hours, zone=ZONE)
    if wx is None:
        raise SystemExit(f"no weather for {ZONE} {year}")
    tmax, _ = wx
    flagged = np.asarray(tmax) > THRESHOLD_C
    binding = _bridge_flagged_runs(flagged, MIN_EVENT_HOURS)
    hod = np.arange(hours) % 24
    peak = binding & (hod >= 14) & (hod <= 21)
    return {"binding": binding, "flagged": flagged, "binding_h14_21": peak}


def _cheapest_first_floor(
    pmax: np.ndarray,
    availability: np.ndarray,
    pmin: np.ndarray,
    heat_rate: np.ndarray,
    frac: np.ndarray,
) -> np.ndarray:
    """Run the SHIPPED cheapest-first kernel on the limb's rows and return its floor.

    The kernel touches only ``pmax``/``availability``/``pmin``/``heat_rate``/``min_gen``
    (and allocates ``min_gen_mechanism``), each indexed by ``rows`` — so calling it on a
    row-sliced shim with ``rows = arange(n)`` is exact, not a re-implementation.
    ``min_gen`` starts at ``pmin`` exactly as ``_apply_frac`` initialises it.
    """
    from market_sim.model.interchange.core import _distribute_group_floor

    n, hours = availability.shape
    shim = SimpleNamespace(
        pmax=pmax,
        availability=availability,
        pmin=pmin,
        heat_rate=heat_rate,
        min_gen=np.broadcast_to(pmin[:, None], (n, hours)).copy(),
        min_gen_mechanism=None,
    )
    _distribute_group_floor(shim, np.arange(n), frac, hours)
    return shim.min_gen


def _pro_rata_floor(
    pmax: np.ndarray, availability: np.ndarray, pmin: np.ndarray, frac: np.ndarray
) -> np.ndarray:
    """Return the ``pro_rata`` branch's composed floor — ``_apply_frac``'s else-branch."""
    n, hours = availability.shape
    floor = np.broadcast_to(pmin[:, None], (n, hours)).copy()
    np.maximum(floor, frac * (pmax[:, None] * availability), out=floor)
    return floor


def _min_stable_capped_floor(
    pmax: np.ndarray,
    availability: np.ndarray,
    pmin: np.ndarray,
    heat_rate: np.ndarray,
    frac: np.ndarray,
) -> np.ndarray:
    """Cheapest-first fill with each row capped at ``min_stable_pct x cap_r``.

    The counterfactual of PREREG addendum A — the fill the coefficient's own
    construction describes: commit units in merit order, each at its physical minimum
    stable level, until the zonal target is met. Mirrors ``_distribute_group_floor``
    exactly but for the per-row cap. SIZING ONLY: not proposed, not screened, and not a
    patch (rule 25 — the shipped kernel is shared by five other ISOs).

    Always feasible on this limb because ``floor_pct 0.0973 < min_stable_pct 0.12``, so
    the target is met by committing ``floor_pct / min_stable_pct`` of available capacity
    — which is ``commit_frac`` by construction.
    """
    n, hours = availability.shape
    cap = pmax[:, None] * availability
    target = frac * cap.sum(axis=0)
    floor = np.broadcast_to(pmin[:, None], (n, hours)).copy()
    remaining = target.copy()
    order = np.argsort(heat_rate, kind="stable")
    for r in order:
        take = np.minimum(remaining, MIN_STABLE_PCT * cap[r, :])
        np.maximum(floor[r, :], take, out=floor[r, :])
        remaining = remaining - take
    return floor


def _band_stats(
    floor: np.ndarray, cap: np.ndarray, pmin: np.ndarray, mask: np.ndarray
) -> dict:
    """Band the raised (row, hour) cells by intensity ``i = floor / cap_r``.

    A cell is *raised* when the floor sits above the row's own ``pmin`` on an hour in
    ``mask`` with positive available capacity. Bands are reported both as a share of
    raised CELLS and as a share of the FORCED ENERGY ``max(0, floor - pmin)`` they
    carry, because the two can disagree and only reporting both is honest.
    """
    sub_floor = floor[:, mask]
    sub_cap = cap[:, mask]
    forced = np.maximum(sub_floor - pmin[:, None], 0.0)
    live = (sub_cap > EPS) & (forced > EPS)
    if not live.any():
        return {
            "raised_cells": 0,
            "forced_mwh": 0.0,
            "bands": {},
            "intensity_mean_cellwt": None,
            "intensity_mean_mwwt": None,
            "intensity_max": None,
        }
    inten = np.divide(sub_floor, sub_cap, out=np.zeros_like(sub_floor), where=sub_cap > EPS)
    i_live = inten[live]
    f_live = forced[live]
    bands = {
        "pinned_ge_0.999": i_live >= PINNED,
        "above_minstable_0.12_to_0.999": (i_live >= MIN_STABLE_PCT) & (i_live < PINNED),
        "at_or_below_minstable_lt_0.12": i_live < MIN_STABLE_PCT,
    }
    tot_cells = int(live.sum())
    tot_mwh = float(f_live.sum())
    out = {
        "raised_cells": tot_cells,
        "forced_mwh": tot_mwh,
        "intensity_mean_cellwt": float(i_live.mean()),
        "intensity_mean_mwwt": (
            float((i_live * f_live).sum() / tot_mwh) if tot_mwh > 0 else None
        ),
        "intensity_max": float(i_live.max()),
        "bands": {},
    }
    for name, sel in bands.items():
        cells = int(sel.sum())
        mwh = float(f_live[sel].sum())
        out["bands"][name] = {
            "cells": cells,
            "cell_share": cells / tot_cells if tot_cells else 0.0,
            "forced_mwh": mwh,
            "energy_share": mwh / tot_mwh if tot_mwh > 0 else 0.0,
        }
    return out


def main() -> int:
    """Measure the fill-level basis question on 2023-2025 and write the JSON record."""
    from market_sim.config.iso_configs import get_iso_config

    rec: dict = {
        "session": "nyiso-206",
        "status": "ZERO LP — one fleet_only reconstruction per year, no solve, nothing patched",
        "keeper": KEEPER_ID,
        "question": (
            "floor_pct = commit_frac x min_stable_pct is identified as a per-unit min-stable "
            "physics with a commitment count on top. _distribute_group_floor fills each row to "
            "its FULL available capacity. Does the delivery preserve the coefficient's meaning?"
        ),
        "not_this": (
            "NOT the operator question (nyiso-205: cheapest_first CONFIRMED, pro_rata REFUTED, "
            "DO-NOT-REDO) and NOT the membership (nyiso-204/204b, refused twice). No level is "
            "re-derived or proposed; no shared kernel is edited (rule 25)."
        ),
        "limb": {
            "zone": ZONE,
            "plant_class": KLASS,
            "driver": "tmax",
            "threshold_c": THRESHOLD_C,
            "floor_pct": FLOOR_PCT,
            "commit_frac": COMMIT_FRAC,
            "min_stable_pct": MIN_STABLE_PCT,
            "min_event_hours": MIN_EVENT_HOURS,
            "distribution_live": "cheapest_first (CSV column EMPTY -> dataclass default)",
        },
        "years": {},
    }

    for year in YEARS:
        state, meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
        fa = state["fleet_arrays"]
        zone_names = [z.name for z in get_iso_config(meta["iso"]).zones]
        z_idx = zone_names.index(ZONE)
        sel = (
            (np.asarray(fa.plant_group) == KLASS)
            & (fa.zone_idx == z_idx)
            & (fa.pmax > 0.0)
        )
        rows = np.flatnonzero(sel)
        hours = int(fa.availability.shape[1])
        pmax = fa.pmax[rows]
        pmin = fa.pmin[rows]
        hr = fa.heat_rate[rows]
        availability = fa.availability[rows, :]
        codes = np.asarray(fa.plant_code)[rows].astype(int)

        masks = _limb_masks(year, hours)
        n_bind = int(masks["binding"].sum())
        if n_bind != EXPECTED_BINDING_HOURS[year]:
            raise SystemExit(
                f"{year}: binding hours {n_bind} != expected "
                f"{EXPECTED_BINDING_HOURS[year]} — the limb window moved; aborting so no "
                "off-object number is written"
            )
        frac = np.where(masks["binding"], FLOOR_PCT, 0.0)
        cap = pmax[:, None] * availability

        cf = _cheapest_first_floor(pmax, availability, pmin, hr, frac)
        pr = _pro_rata_floor(pmax, availability, pmin, frac)
        ms = _min_stable_capped_floor(pmax, availability, pmin, hr, frac)

        # (5) the aggregate identity — if this fails every intensity number is meaningless.
        m = masks["binding"]
        tgt = (FLOOR_PCT * cap.sum(axis=0))[m]
        ident = {
            "target_mwh": float(tgt.sum()),
            "cheapest_first_delivered_mwh": float(cf[:, m].sum() - pmin.sum() * m.sum()),
            "max_abs_hourly_gap_mw": float(
                np.abs(cf[:, m].sum(axis=0) - pmin.sum() - tgt).max()
            ),
        }

        yr: dict = {
            "n_rows": int(rows.size),
            "hours_binding": n_bind,
            "hours_flagged_unbridged": int(masks["flagged"].sum()),
            "hours_binding_h14_21": int(masks["binding_h14_21"].sum()),
            "class_nameplate_mw": float(pmax.sum()),
            "pmin_over_pmax_max": float((pmin / np.maximum(pmax, EPS)).max()),
            "aggregate_identity": ident,
            "cuts": {},
            "per_row_binding": [],
            "per_plant_binding": {},
            "min_stable_capped_counterfactual": {},
        }

        # (1)(2) the banded intensity, over all three pre-registered cuts, per operator.
        for cut, mask in masks.items():
            yr["cuts"][cut] = {
                "hours": int(mask.sum()),
                "cheapest_first": _band_stats(cf, cap, pmin, mask),
                "pro_rata_arithmetically_forced": _band_stats(pr, cap, pmin, mask),
            }

        # (3) per row and per plant, on the binding window the verdict is read off.
        cf_forced = np.maximum(cf - pmin[:, None], 0.0)[:, m]
        cap_m = cap[:, m]
        inten = np.divide(
            cf[:, m], cap_m, out=np.zeros_like(cap_m), where=cap_m > EPS
        )
        live = (cap_m > EPS) & (cf_forced > EPS)
        for j in range(rows.size):
            if not live[j].any():
                continue
            ij = inten[j][live[j]]
            yr["per_row_binding"].append(
                {
                    "plant_code": int(codes[j]),
                    "plant": NAMES.get(int(codes[j]), str(codes[j])),
                    "pmax_mw": float(pmax[j]),
                    "heat_rate": float(hr[j]),
                    "raised_hours": int(live[j].sum()),
                    "pinned_hours": int((ij >= PINNED).sum()),
                    "forced_mwh": float(cf_forced[j][live[j]].sum()),
                    "intensity_mean": float(ij.mean()),
                    "intensity_max": float(ij.max()),
                }
            )
        for c in sorted(set(int(x) for x in codes)):
            r = codes == c
            sub_live = live[r]
            sub_forced = cf_forced[r]
            sub_int = inten[r]
            pinned_e = float(sub_forced[sub_live & (sub_int >= PINNED)].sum())
            yr["per_plant_binding"][str(c)] = {
                "name": NAMES.get(c, str(c)),
                "nameplate_mw": float(pmax[r].sum()),
                "n_rows": int(r.sum()),
                "raised_cells": int(sub_live.sum()),
                "pinned_cells": int((sub_live & (sub_int >= PINNED)).sum()),
                "forced_mwh": float(sub_forced[sub_live].sum()),
                "forced_mwh_at_pinned": pinned_e,
            }

        # (6) the min-stable-capped counterfactual — SIZING for the owner card only.
        ms_forced = np.maximum(ms - pmin[:, None], 0.0)
        ms_committed = (ms[:, m] > pmin[:, None] + EPS) & (cap_m > EPS)
        committed_cap = np.where(ms_committed, cap_m, 0.0).sum(axis=0)
        tot_cap = cap_m.sum(axis=0)
        yr["min_stable_capped_counterfactual"] = {
            "note": (
                "NOT PROPOSED, NOT SCREENED, NOT A PATCH — a sizing for the owner card. "
                "The shipped kernel is shared by 37 of 50 program-wide limbs (rule 25)."
            ),
            "target_met": bool(
                np.abs(ms[:, m].sum(axis=0) - pmin.sum() - tgt).max() < 1e-6
            ),
            "max_abs_hourly_gap_mw": float(
                np.abs(ms[:, m].sum(axis=0) - pmin.sum() - tgt).max()
            ),
            "forced_mwh": float(ms_forced[:, m].sum()),
            "cheapest_first_forced_mwh": float(cf_forced[live].sum()),
            "committed_capacity_share_mean": float(
                (committed_cap[tot_cap > EPS] / tot_cap[tot_cap > EPS]).mean()
            ),
            "commit_frac_asserted": COMMIT_FRAC,
            "bands": _band_stats(ms, cap, pmin, m),
            "per_plant_forced_mwh": {
                str(c): float(ms_forced[codes == c][:, m].sum())
                for c in sorted(set(int(x) for x in codes))
            },
        }

        rec["years"][str(year)] = yr

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}")
    for y, d in rec["years"].items():
        b = d["cuts"]["binding"]["cheapest_first"]["bands"]
        print(
            f"{y}: raised cells {d['cuts']['binding']['cheapest_first']['raised_cells']}, "
            f"pinned cell share {b['pinned_ge_0.999']['cell_share']:.3f}, "
            f"pinned energy share {b['pinned_ge_0.999']['energy_share']:.3f}, "
            f"mean intensity (MW-wt) "
            f"{d['cuts']['binding']['cheapest_first']['intensity_mean_mwwt']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
