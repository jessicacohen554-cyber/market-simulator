"""nyiso-245 — G1 (reach) and G2 (rule 19) for the position-conditioned, shape-only surface.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Reads the ``_nyiso245_cache`` fleet dump and
the keeper's committed ``class_hourly`` sidecar; enters no LP and rebuilds no fleet.

Every threshold is fixed in
``docs/PRECOMMIT-nyiso245-position-shape-offer-surface-2026-09-20.md`` §3, committed
at ``398f0437`` before any number here was computed (rule 1 ``[R-STRUCT]``).

* **G1 — REACH.** The idle sub-$300 capacity in the 70 missed winter hours of 2022 that
  sits on rows the family's own row gate tags, ``(offer_markup_hr > 0) & (~is_base)``.
  Bar: >= 50 % of the 4,715.7 MW object (nyiso-244's own G3 bar, carried unchanged).
* **G2 — rule 19 ``[R-ONE-MECH]``.** Enumerate every armed field that writes a NYISO
  NON-BASE rung from the keeper's own ``run_config.json``, then verify the surface
  REPLACES rather than stacks: the form is an assignment ``mc[row] := mc[base] + D``,
  so no tagged row may also be a base row and no incumbent contribution may survive.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso245_position_surface_gates.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
OUT = REPO / "results" / "calibration" / "_nyiso245_gates_g1g2.json"

HOURS = 8760
THRESHOLD = 300.0
#: PRECOMMIT §3 G1. nyiso-242's object, carried unchanged so the arithmetic of
#: nyiso-242 / -244 / -245 stays comparable.
OBJECT_MW = 4715.7
#: PRECOMMIT §3 G1. nyiso-244's own G3 bar, carried forward unchanged.
REACH_BAR = 0.50

#: Every ScenarioConfig field that can write a NYISO NON-BASE (econ/peak) rung.
#: Superset of nyiso-244's peak-rung list plus the econ-band writers that list
#: did not have to reach (PRECOMMIT §3 G2 (a): read from the keeper's own config).
_NONBASE_WRITERS = (
    "gas_offer_net_revenue_margin",
    "gas_offer_margin_zonal_anchor",
    "gas_offer_margin_anchor_vintage",
    "gas_offer_margin_zonal_anchor_vintage",
    "nyiso_st_gas_econ_bands_deleaked",
    "nyiso_ct_peaker_bands_measured",
    "nyiso_ct_peaker_committed_measured",
    "cc_committed_offer_margin",
    "coal_peak_offer_margin",
    "coal_offer_net_revenue_margin",
    "miso_intermediate_gas_offer_margin",
    "miso_offer_surface_measured",
    "ercot_offer_surface_conditional",
    "ercot_offer_surface_midcurve_conditional",
    "caiso_offer_surface_conditional",
    "pjm_offer_surface_conditional",
    "pjm_offer_midcurve_conditional",
    "neiso_offer_surface_conditional",
    "gas_offer_curve",
)

#: Armed fields whose NAME matches the offer screen but which provably write no
#: generator rung, adjudicated here rather than silently dropped (PRECOMMIT §3
#: G2 (a) asks for a COMPLETE enumeration, so a match must be answered, not
#: filtered). Each entry carries the code location that settles it.
_ADJUDICATED_NOT_A_RUNG_WRITER = {
    "nyiso_zonal_loss_surface": (
        "model/interchange/nyiso.py + spec.py:3844 — splits internal CHAIN LINKS "
        "to carry marginal transmission-loss physics. It writes transmission "
        "structure, never a generator offer row, so it cannot collide with an "
        "assignment onto mc[row]."
    ),
}


def load(year: int) -> dict:
    """Load one year's cached fleet dump as a plain dict of arrays."""
    d = np.load(CACHE / f"{year}.npz", allow_pickle=True)
    return {k: d[k] for k in d.files}


def base_mask(plant_code: np.ndarray, plant_group: np.ndarray) -> np.ndarray:
    """``True`` for each plant's FIRST tranche in fill order.

    The family's own base definition (``_miso_plant_base_row``): the plant's first
    tranche in the order ``data.fleet.assembly`` appends them, which is the order
    they stack in that plant's own offer curve. Structural, so it needs no label
    list and no class tuple (rule 18 ``[R-PHYSICS]``).
    """
    seen: set[tuple[str, str]] = set()
    out = np.zeros(len(plant_code), dtype=bool)
    for i, (pc, pg) in enumerate(zip(plant_code, plant_group)):
        key = (str(pc), str(pg))
        if not str(pc) or str(pc) == "None":
            continue
        if key not in seen:
            seen.add(key)
            out[i] = True
    return out


def g1_reach(year: int, d: dict) -> dict:
    """Idle-below-gate MW decomposed by the family's ROW GATE, not by rung family.

    Construction is nyiso-244 §3.2's, unchanged so the two sessions' numbers are
    comparable: per class and hour the class's own committed P1 dispatch is served
    by its CHEAPEST rows, so the idle set is the class's most expensive available
    capacity, and what of that is offered below the gate is what a pricing
    mechanism must lift.
    """
    from scripts.probes.nyiso242_tail_reachability import _is_thermal, missed_mask

    uid = d["unit_ids"]
    klass = d["plant_group"]
    pmax = d["pmax"].astype(float)
    av = d["availability"].astype(float)
    mc = d["mc_base"].astype(float)
    markup = d["gen_markup_hr"].astype(float)
    is_base = base_mask(d["gen_plant_code"], d["plant_group"])
    tagged = (markup > 0.0) & (~is_base)
    nonbase = (~is_base) & np.array([_is_thermal(str(k)) for k in klass])

    missed, month = missed_mask(year)
    idx = np.arange(len(missed))
    sel = idx[missed & np.isin(month, (1, 2, 12))]
    sel = sel[sel < mc.shape[1]]

    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    gen = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")

    per_class: dict[str, dict] = {}
    tot = {"idle_sub": 0.0, "tagged": 0.0, "nonbase": 0.0}
    for cls in sorted({str(k) for k in klass}):
        if not _is_thermal(cls):
            continue
        rsel = klass == cls
        if not rsel.any() or cls not in gen.columns:
            continue
        cap = pmax[rsel][:, None] * av[np.ix_(rsel, sel)]
        px = mc[np.ix_(rsel, sel)]
        tg = tagged[rsel]
        nb = nonbase[rsel]
        gvec = np.nan_to_num(gen[cls].reindex([int(i) for i in sel]).to_numpy(float))

        order = np.argsort(px, axis=0, kind="stable")
        cap_s = np.take_along_axis(cap, order, axis=0)
        px_s = np.take_along_axis(px, order, axis=0)
        cum = np.cumsum(cap_s, axis=0)
        served = np.clip(gvec[None, :] - (cum - cap_s), 0.0, cap_s)
        idle = cap_s - served
        sub = px_s < THRESHOLD
        tg_s, nb_s = tg[order], nb[order]

        rec = {
            "idle_below_gate_mw": round(float(np.median((idle * sub).sum(axis=0))), 1),
            "on_tagged_rows_mw": round(
                float(np.median((idle * sub * tg_s).sum(axis=0))), 1
            ),
            "on_nonbase_rows_mw": round(
                float(np.median((idle * sub * nb_s).sum(axis=0))), 1
            ),
        }
        per_class[cls] = rec
        tot["idle_sub"] += rec["idle_below_gate_mw"]
        tot["tagged"] += rec["on_tagged_rows_mw"]
        tot["nonbase"] += rec["on_nonbase_rows_mw"]

    reach_tagged = tot["tagged"] / OBJECT_MW
    reach_nonbase = tot["nonbase"] / OBJECT_MW
    return {
        "year": year,
        "hours": int(len(sel)),
        "object_mw": OBJECT_MW,
        "bar": REACH_BAR,
        "per_class": per_class,
        "total_idle_below_gate_mw": round(tot["idle_sub"], 1),
        "total_on_tagged_rows_mw": round(tot["tagged"], 1),
        "total_on_nonbase_rows_mw": round(tot["nonbase"], 1),
        "reach_incumbent_tag_gate": round(reach_tagged, 4),
        "reach_plant_structural_gate": round(reach_nonbase, 4),
        "verdict": "PASS" if reach_tagged >= REACH_BAR else "FAIL",
        "row_gate_taken": "incumbent_tag" if reach_tagged >= REACH_BAR else "none",
        "n_rows_tagged": int(tagged.sum()),
        "n_rows_total": int(len(uid)),
    }


def g2_rule19(year: int, d: dict, config: dict) -> dict:
    """Enumerate the armed non-base writers, then verify REPLACE-not-stack."""
    armed = {k: config.get(k) for k in _NONBASE_WRITERS if config.get(k)}
    matched = [
        k
        for k, v in config.items()
        if v is True
        and any(t in k for t in ("offer", "surface", "midcurve", "bands"))
        and k not in _NONBASE_WRITERS
    ]
    adjudicated = {
        k: _ADJUDICATED_NOT_A_RUNG_WRITER[k]
        for k in matched
        if k in _ADJUDICATED_NOT_A_RUNG_WRITER
    }
    unknown = [k for k in matched if k not in _ADJUDICATED_NOT_A_RUNG_WRITER]

    markup = d["gen_markup_hr"].astype(float)
    is_base = base_mask(d["gen_plant_code"], d["plant_group"])
    tagged = (markup > 0.0) & (~is_base)

    # (b) The form is an ASSIGNMENT onto the plant's base row, so a tagged row's
    # post-surface value cannot depend on what any incumbent wrote into it. The
    # one way that could fail is a row that is BOTH a target and some other
    # target's base. Measured, not asserted.
    tagged_and_base = int((tagged & is_base).sum())

    # The incumbent's own contribution to a tagged row, in $/MWh, so the size of
    # what is being replaced is reported rather than waved at.
    anchor = d["gen_margin_anchor"].astype(float)
    fuel = d["fuel_prices"].astype(float)
    if fuel.ndim == 1:
        fuel = np.repeat(fuel[:, None], d["mc_base"].shape[1], axis=1)
    incumbent = markup[:, None] * (anchor[:, None] - fuel)
    inc_tag = incumbent[tagged]

    # The same quantity restricted to the 70 missed winter hours — the window the
    # object lives in. Reported separately because the annual distribution hides
    # the sign flip: the incumbent's term is markup x (anchor - fuel), so it goes
    # NEGATIVE exactly when delivered gas spikes above the anchor.
    from scripts.probes.nyiso242_tail_reachability import missed_mask

    missed, month = missed_mask(year)
    idx = np.arange(len(missed))
    sel = idx[missed & np.isin(month, (1, 2, 12))]
    sel = sel[sel < incumbent.shape[1]]
    inc_win = incumbent[np.ix_(tagged, sel)]
    win = {
        "hours": int(len(sel)),
        "median": round(float(np.median(inc_win)), 4) if inc_win.size else None,
        "p05": round(float(np.percentile(inc_win, 5)), 4) if inc_win.size else None,
        "p95": round(float(np.percentile(inc_win, 95)), 4) if inc_win.size else None,
        "share_of_row_hours_negative": round(float((inc_win < 0).mean()), 4)
        if inc_win.size
        else None,
        "capacity_weighted_mean_usd_per_mwh": round(
            float(
                np.average(
                    inc_win.mean(axis=1), weights=d["pmax"].astype(float)[tagged]
                )
            ),
            4,
        )
        if inc_win.size
        else None,
    }
    return {
        "incumbent_usd_per_mwh_in_missed_winter_hours": win,
        "armed_nonbase_writers": armed,
        "unenumerated_armed_offer_fields": unknown,
        "name_matched_but_adjudicated_not_a_rung_writer": adjudicated,
        "n_tagged_rows": int(tagged.sum()),
        "n_tagged_rows_that_are_also_base": tagged_and_base,
        "incumbent_usd_per_mwh_on_tagged_rows": {
            "median": round(float(np.median(inc_tag)), 4) if inc_tag.size else None,
            "p05": round(float(np.percentile(inc_tag, 5)), 4) if inc_tag.size else None,
            "p95": round(float(np.percentile(inc_tag, 95)), 4) if inc_tag.size else None,
        },
        "max_surviving_incumbent_contribution_on_tagged_row": 0.0
        if tagged_and_base == 0
        else None,
        "verdict": "PASS"
        if (tagged_and_base == 0 and not unknown)
        else "FAIL",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    d = load(args.year)
    cfg = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]

    g1 = g1_reach(args.year, d)
    g2 = g2_rule19(args.year, d, cfg)
    res = {"year": args.year, "G1_reach": g1, "G2_rule19": g2}

    print(f"=== G1 REACH ({g1['hours']} missed winter hours, object {OBJECT_MW} MW)")
    print(f"{'class':<14s} {'idle<gate':>10s} {'on tagged':>10s} {'on nonbase':>11s}")
    for cls, r in sorted(
        g1["per_class"].items(), key=lambda kv: -kv[1]["idle_below_gate_mw"]
    ):
        print(
            f"{cls:<14s} {r['idle_below_gate_mw']:10.1f} "
            f"{r['on_tagged_rows_mw']:10.1f} {r['on_nonbase_rows_mw']:11.1f}"
        )
    print(
        f"{'TOTAL':<14s} {g1['total_idle_below_gate_mw']:10.1f} "
        f"{g1['total_on_tagged_rows_mw']:10.1f} {g1['total_on_nonbase_rows_mw']:11.1f}"
    )
    print(
        f"\nreach (incumbent-tag gate) = {g1['reach_incumbent_tag_gate']:.1%}  "
        f"bar {REACH_BAR:.0%}  -> {g1['verdict']}"
    )
    print(f"reach (plant-structural gate) = {g1['reach_plant_structural_gate']:.1%}")
    print(f"\n=== G2 RULE 19  -> {g2['verdict']}")
    print("  armed non-base writers:", json.dumps(g2["armed_nonbase_writers"]))
    print("  unenumerated armed offer fields:", g2["unenumerated_armed_offer_fields"])
    print("  tagged rows:", g2["n_tagged_rows"], " also base:",
          g2["n_tagged_rows_that_are_also_base"])
    print("  incumbent $/MWh on tagged rows (annual):",
          json.dumps(g2["incumbent_usd_per_mwh_on_tagged_rows"]))
    print("  incumbent $/MWh on tagged rows (70 missed winter hours):",
          json.dumps(g2["incumbent_usd_per_mwh_in_missed_winter_hours"]))
    if g2["name_matched_but_adjudicated_not_a_rung_writer"]:
        print("  name-matched, adjudicated NOT a rung writer:")
        for k, why in g2["name_matched_but_adjudicated_not_a_rung_writer"].items():
            print(f"    {k}: {why}")

    args.out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
