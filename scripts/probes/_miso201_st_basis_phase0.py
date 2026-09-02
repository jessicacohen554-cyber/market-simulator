"""miso-201 phase 0 — the ST-SIDE BASIS CENSUS: is the lever LIVE?

The charter (miso-201) inherits its object from FINDING-miso200 section 8 item 1: an
ST_GAS/ST_CHP analogue of ``unit_outage_lp_capacity_basis``, which is CC-only
(``outages._CC_NAMEPLATE_BASIS_GROUPS == ("CC_REGULAR", "CC_CHP")``) and so can
never reach a steam bin.

**The charter's explicit caution, and what this probe is built to answer.** At the
two facilities miso-200 measured — Ninemile Point 1403 and Moselle 2070 — the
steam bin's pre-clip overflow has ZERO dispatch consequence, because the units
carrying the windows are EXACTLY the units in the bin: a concurrent full stop means
the bin genuinely is 100 % out, and availability 0.0000 is the physically correct
value. Chartering this as "fix the 1403 overflow" would therefore build an inert
lever. The charter instead requires the GENERAL census FIRST:

    measure where a steam bin's overflow is NOT already landing on the correct
    answer -- i.e. bins whose overflow comes from units that are only PART of the
    bin. That census decides whether the lever is live.

That is N-3, this probe's deliverable and its verdict.

Measurements
------------
* **N-1 REPRODUCTION (a gate, not a report).** The production entry point
  ``unit_outage_derate_factors`` returns ``clip(1 - v, 0, 1)`` and so HIDES the
  pre-clip share ``v`` the census needs. ``v`` is therefore reconstructed here
  from the production code path -- the same ``cap`` denominator map, the same
  ``_generic_unit_outage_target`` routing, the same fleet-status filter, the same
  ``unit_outage_event_window`` reconstruction -- and every reconstructed bin is
  ASSERTED to reproduce the production array EXACTLY. A reconstruction that does
  not reproduce production measures nothing (the charter's instrument note; the
  discipline miso-200 applied on 121 bins).
* **N-2 NUMERATOR BASIS.** Joins each extract row to its EIA-860 generator row and
  reports, per ``capacity_source``, the numerator against that unit's published
  nameplate and net-summer capacity. This is what identifies WHICH side of the
  ratio is off basis.
* **N-3 THE OVERFLOW CENSUS (the deliverable).** Every bin-year-overlay whose
  pre-clip share exceeds 1.0, classified INERT vs LIVE by the charter's own test,
  with a RIGOROUS LOWER BOUND on the capability wrongly removed where it is LIVE.
* **N-4 COUNTERFACTUAL.** What the pre-clip share becomes when the numerator is put
  on the denominator's basis, so the repair's reach is measured before it is built.

Nothing here is fitted and nothing is tuned: every quantity is either published
EIA-860 data, the committed extract, or the production code's own output.

Run:  PYTHONPATH=src python3 scripts/probes/_miso201_st_basis_phase0.py
Writes: results/calibration/_miso201_st_basis_phase0.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.data import outages
from market_sim.data.fleet import load_fleet_from_csv, load_retired_within_window

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760

# The steam bins the charter's object covers. ST_GAS/ST_CHP are exactly the
# groups _CC_NAMEPLATE_BASIS_GROUPS cannot reach.
STEAM_GROUPS = ("ST_GAS", "ST_CHP")

# The keeper recipe (results/calibration/miso200_unitroute_B/run_config.json).
# These are read off the committed keeper, never chosen here.
KEEPER = dict(
    cc_steam_part_reclass=False,
    cc_nameplate_basis=False,  # unit_outage_lp_capacity_basis
    fleet_status_scope=True,  # unit_outage_fleet_status_scope
    mixed_gas_routing=True,  # unit_outage_mixed_gas_routing
    per_unit_crosswalk=False,  # campd_per_unit_attribution
)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_miso201_st_basis_phase0.json"
EIA860 = REPO / "data" / "raw" / "eia-860" / "eia860_generator_operable.parquet"


def _norm_unit_id(uid: object) -> str:
    """Upper-cased alphanumeric-only unit id — the deriver's own normalisation.

    Copied from ``scripts/data/derive_campd_unit_outages._norm_unit_id`` so the
    crosswalk this probe builds joins on exactly the key the extract was built
    with.
    """
    return re.sub(r"[^0-9A-Za-z]", "", str(uid)).upper()


def eia_unit_index() -> tuple[dict, dict]:
    """Return ``(exact, by_digits)`` maps to ``(nameplate_mw, summer_mw)``.

    Mirrors ``derive_campd_unit_outages.build_capacity_index`` key-for-key (the
    ``exact`` normalised-id map plus the ``by_digits`` trailing-digit map used
    only when a single generator at the plant carries those digits), but carries
    the published NET SUMMER capacity alongside the nameplate — the two bases
    whose gap this probe is measuring.
    """
    raw = pd.read_parquet(
        EIA860,
        columns=[
            "Plant Code",
            "Generator ID",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
            "Prime Mover",
        ],
    )
    raw = raw.dropna(subset=["Generator ID"]).copy()
    nameplate = pd.to_numeric(raw["Nameplate Capacity (MW)"], errors="coerce")
    summer = pd.to_numeric(raw["Summer Capacity (MW)"], errors="coerce")
    exact: dict[tuple[int, str], tuple[float, float]] = {}
    by_digits: dict[tuple[int, str], list[tuple[float, float]]] = {}
    for i, (pid, gid) in enumerate(
        zip(raw["Plant Code"], raw["Generator ID"], strict=False)
    ):
        np_mw = float(nameplate.iloc[i]) if pd.notna(nameplate.iloc[i]) else float("nan")
        su_mw = float(summer.iloc[i]) if pd.notna(summer.iloc[i]) else float("nan")
        if not (np_mw > 0.0):
            continue
        try:
            key_pid = int(pid)
        except (TypeError, ValueError):
            continue
        full = _norm_unit_id(gid)
        exact[(key_pid, full)] = (np_mw, su_mw)
        digits = re.sub(r"\D", "", full)
        if digits:
            by_digits.setdefault((key_pid, digits), []).append((np_mw, su_mw))
    return exact, by_digits


def lookup_unit(
    exact: dict, by_digits: dict, plant: int, unit_id: object
) -> tuple[float, float] | None:
    """Resolve one extract row's unit to its EIA-860 ``(nameplate, summer)``.

    Exact normalised-id hit first, then the trailing-digit map but ONLY when it
    is unambiguous (a single generator at the plant carries those digits) —
    the deriver's own rule, so this probe never invents a join the extract
    itself would not have made.
    """
    full = _norm_unit_id(unit_id)
    if (plant, full) in exact:
        return exact[(plant, full)]
    digits = re.sub(r"\D", "", full)
    if digits:
        cands = by_digits.get((plant, digits))
        if cands is not None and len(cands) == 1:
            return cands[0]
    return None


def fleet_units_by_bin() -> dict[tuple[int, str], list[tuple[str, float]]]:
    """Return ``{(plant_code, plant_group): [(unit_id, pmax_mw), ...]}``.

    Built from the SAME fleet load ``outages._iso_plant_capacity`` uses — the
    denominator's own basis — so the per-unit roster and the bin denominator
    can never disagree about what is in the bin.
    """
    iso_config = get_iso_config(ISO)
    fleet = load_fleet_from_csv(
        ISO, iso_config, cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"]
    ) + load_retired_within_window(ISO, iso_config)
    out: dict[tuple[int, str], list[tuple[str, float]]] = {}
    for g in fleet:
        code = int(g.plant_code)
        if code <= 0 or not g.plant_group:
            continue
        out.setdefault((code, str(g.plant_group)), []).append(
            (str(getattr(g, "unit_id", "")), float(g.pmax_mw))
        )
    return out


def reconstruct_preclip(
    df: pd.DataFrame, year: int, cap: dict
) -> tuple[dict, dict]:
    """Return ``(sums, contributors)`` — the pre-clip share and who made it.

    Reproduces ``outages._unit_outage_factors_from_events`` line for line for the
    non-ERCOT branch, additionally recording, per bin, each contributing row's
    hour mask and removed MW so the census can ask WHICH units are out in a
    given hour. ``sums[bin]`` is the pre-clip ``v``; production returns
    ``clip(1 - v, 0, 1)``, which N-1 asserts against.
    """
    has_derate = "derate_factor" in df.columns
    has_hours = outages._has_hour_grain(df)
    status_idx = (
        outages._fleet_status_index(ISO) if KEEPER["fleet_status_scope"] else None
    )
    sums: dict[tuple[int, str], np.ndarray] = {}
    contrib: dict[tuple[int, str], list[dict]] = {}
    for r in df.itertuples(index=False):
        tgt = outages._generic_unit_outage_target(
            int(r.facility_id), r.unit_id, r.plant_group
        )
        if tgt is None or tgt not in cap:
            continue
        if status_idx is not None:
            st = status_idx.get(int(r.facility_id), {}).get(
                str(r.unit_id).strip().upper()
            )
            if st is not None and st != "OP":
                continue
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        removed_frac = 1.0
        if has_derate:
            dfac = r.derate_factor
            if pd.isna(dfac):
                continue
            removed_frac = min(max(1.0 - float(dfac), 0.0), 1.0)
            if removed_frac <= 0.0:
                continue
        w_start, w_stop = outages.unit_outage_event_window(r, has_hours)
        mask = outages.outage_hour_mask(w_start, w_stop, year, HOURS)
        if not mask.any():
            continue
        arr = sums.setdefault(tgt, np.zeros(HOURS))
        share = removed_frac * float(ucap) / cap[tgt]
        arr[mask] += share
        contrib.setdefault(tgt, []).append(
            {
                "unit_id": str(r.unit_id),
                "removed_mw": removed_frac * float(ucap),
                "mask": mask,
            }
        )
    return sums, contrib


def reconstruct_preclip_maxgen(
    df: pd.DataFrame, year: int, cap: dict
) -> tuple[dict, dict]:
    """``reconstruct_preclip``'s maxgen twin — a SEPARATE accumulator, faithfully.

    ``unit_outage_maxgen_derate_factors`` does NOT share
    ``_unit_outage_factors_from_events``: its rows carry a measured ``derate_mw``
    (removed MW, not a full-stop unit capacity) over an hour-granular half-open
    ``[window_start, window_end)``, it is class-agnostic (no CT exclusion) and it
    applies no fleet-status filter. Reproducing it with the std accumulator would
    silently measure the wrong object, so it gets its own reconstruction, line for
    line against the production loop.
    """
    sums: dict[tuple[int, str], np.ndarray] = {}
    contrib: dict[tuple[int, str], list[dict]] = {}
    for r in df.itertuples(index=False):
        code = int(r.facility_id)
        g = (
            ""
            if r.plant_group is None
            or (isinstance(r.plant_group, float) and np.isnan(r.plant_group))
            else str(r.plant_group)
        )
        if code in outages._FLEET_GROUP_OVERRIDE:
            tgt = (code, outages._FLEET_GROUP_OVERRIDE[code])
        elif not g or g == "OTHER":
            continue
        else:
            tgt = (code, g)
        if tgt not in cap:
            continue
        removed = float(r.derate_mw)
        if not removed > 0.0 or pd.isna(removed):
            continue
        mask = outages.outage_hour_mask(r.window_start, r.window_end, year, HOURS)
        if not mask.any():
            continue
        arr = sums.setdefault(tgt, np.zeros(HOURS))
        arr[mask] += removed / cap[tgt]
        contrib.setdefault(tgt, []).append(
            {"unit_id": str(r.unit_id), "removed_mw": removed, "mask": mask}
        )
    return sums, contrib


def run_n5(overlays, cap, roster, exact, by_digits) -> dict:
    """Size the basis object: production vs LP-basis-aligned availability, in GWh.

    For every steam bin and year, rebuilds the pre-clip share with each row's
    removed MW put on the fleet's own ``pmax_mw`` basis (fail-closed where the
    unit does not resolve), and integrates the resulting availability difference
    against the bin's LP capacity. Positive ``gwh`` = capability the production
    basis wrongly REMOVES and the alignment gives back.
    """
    f_exact, f_digits = fleet_unit_index(roster)
    out: dict = {
        "joinability": {},
        "by_year": {},
        "bins": [],
        "netzero_separate": {},
    }
    joined = unjoined = 0
    unresolved_ids: dict[str, int] = {}
    per_year: dict[int, float] = {y: 0.0 for y in YEARS}
    per_bin: dict[tuple, dict] = {}
    nz_year: dict[int, float] = {y: 0.0 for y in YEARS}

    for overlay, df in overlays.items():
        num_col = "unit_capacity_mw" if overlay == "std5d" else "derate_mw"
        for year in YEARS:
            prod_sums: dict[tuple[int, str], np.ndarray] = {}
            algn_sums: dict[tuple[int, str], np.ndarray] = {}
            nz_sums: dict[tuple[int, str], np.ndarray] = {}
            has_hours = outages._has_hour_grain(df) if overlay == "std5d" else False
            status_idx = (
                outages._fleet_status_index(ISO)
                if (overlay == "std5d" and KEEPER["fleet_status_scope"])
                else None
            )
            for r in df.itertuples(index=False):
                code = int(r.facility_id)
                if overlay == "std5d":
                    tgt = outages._generic_unit_outage_target(
                        code, r.unit_id, r.plant_group
                    )
                else:
                    g = (
                        ""
                        if r.plant_group is None
                        or (isinstance(r.plant_group, float) and np.isnan(r.plant_group))
                        else str(r.plant_group)
                    )
                    if code in outages._FLEET_GROUP_OVERRIDE:
                        tgt = (code, outages._FLEET_GROUP_OVERRIDE[code])
                    elif not g or g == "OTHER":
                        tgt = None
                    else:
                        tgt = (code, g)
                if tgt is None or tgt not in cap:
                    continue
                if tgt[1] not in STEAM_GROUPS:
                    continue
                if status_idx is not None:
                    st = status_idx.get(code, {}).get(str(r.unit_id).strip().upper())
                    if st is not None and st != "OP":
                        continue
                raw = getattr(r, num_col, None)
                if raw is None or pd.isna(raw) or float(raw) <= 0.0:
                    continue
                removed_frac = 1.0
                if overlay == "std5d" and "derate_factor" in df.columns:
                    dfac = r.derate_factor
                    if pd.isna(dfac):
                        continue
                    removed_frac = min(max(1.0 - float(dfac), 0.0), 1.0)
                    if removed_frac <= 0.0:
                        continue
                if overlay == "std5d":
                    w0, w1 = outages.unit_outage_event_window(r, has_hours)
                else:
                    w0, w1 = r.window_start, r.window_end
                mask = outages.outage_hour_mask(w0, w1, year, HOURS)
                if not mask.any():
                    continue
                prod_mw = removed_frac * float(raw)
                algn = aligned_numerator(f_exact, f_digits, code, tgt[1], r.unit_id)
                if algn is None:
                    unjoined += 1
                    uid = str(r.unit_id)
                    unresolved_ids[uid] = unresolved_ids.get(uid, 0) + 1
                    algn_mw = prod_mw  # fail closed
                    if _norm_unit_id(uid).startswith(SYNTHETIC_UNIT_PREFIX):
                        nz_sums.setdefault(tgt, np.zeros(HOURS))[mask] += (
                            prod_mw / cap[tgt]
                        )
                else:
                    joined += 1
                    algn_mw = removed_frac * float(algn)
                prod_sums.setdefault(tgt, np.zeros(HOURS))[mask] += prod_mw / cap[tgt]
                algn_sums.setdefault(tgt, np.zeros(HOURS))[mask] += algn_mw / cap[tgt]

            for key in prod_sums:
                a_prod = np.clip(1.0 - prod_sums[key], 0.0, 1.0)
                a_algn = np.clip(1.0 - algn_sums[key], 0.0, 1.0)
                d = float(np.sum(a_algn - a_prod) * cap[key] / 1000.0)
                if abs(d) < 1e-9:
                    continue
                per_year[year] += d
                rec = per_bin.setdefault(
                    (int(key[0]), str(key[1])),
                    {
                        "plant": int(key[0]),
                        "group": str(key[1]),
                        "bin_cap_mw": round(float(cap[key]), 4),
                        "gwh_by_year": {str(y): 0.0 for y in YEARS},
                    },
                )
                rec["gwh_by_year"][str(year)] = round(
                    rec["gwh_by_year"][str(year)] + d, 4
                )
            for key in nz_sums:
                a_z = np.clip(1.0 - nz_sums[key], 0.0, 1.0)
                nz_year[year] += float(np.sum(1.0 - a_z) * cap[key] / 1000.0)

    out["joinability"] = {
        "rows_joined_to_fleet_unit": joined,
        "rows_failed_closed": unjoined,
        "join_rate": round(joined / max(1, joined + unjoined), 4),
        "top_unresolved_unit_ids": sorted(
            unresolved_ids.items(), key=lambda kv: -kv[1]
        )[:15],
    }
    out["by_year"] = {str(y): round(per_year[y], 4) for y in YEARS}
    out["bins"] = sorted(
        per_bin.values(),
        key=lambda r: -sum(abs(v) for v in r["gwh_by_year"].values()),
    )
    out["netzero_separate"] = {
        "gwh_removed_by_year": {str(y): round(nz_year[y], 4) for y in YEARS},
        "note": (
            "Whole-plant eia923_netzero lay-up rows, reported SEPARATELY: their "
            "unit_capacity_mw is the plant's total nameplate standing for a "
            "whole-plant lay-up, so they are a different object from the "
            "per-unit basis gap and are never aligned here (fail-closed)."
        ),
    }
    return out


def resolve_bin_alignment(cap, roster, df_all):
    """Return ``(eligible_bins, pairmap, diagnostics)`` for the BIN-SCOPED design.

    The alignment is applied **all-or-nothing per bin**: a steam bin is eligible
    only when EVERY extract unit that ever appears in it resolves 1-1 onto a
    DISTINCT fleet unit of that same bin. Three resolution routes, in order, all
    zero-DOF:

    1. exact normalised-generator-id hit;
    2. an UNAMBIGUOUS trailing-digit hit (a single fleet unit in the bin carries
       those digits) — the deriver's own rule;
    3. a unique 1-1 RESIDUAL pairing: exactly one extract unit and exactly one
       fleet unit are left over, so the pairing is forced, not chosen. (This is
       what resolves Ninemile Point 1403, whose CAMPD unit ``4`` cannot match
       EIA generator ``6(4)`` on digits.)

    A bin with any unresolved unit is left ENTIRELY untouched. That is the point:
    a half-aligned bin — some units on the LP basis, some on EIA nameplate — is
    less coherent than either basis alone, so partial application is refused
    rather than counted. Eligibility is computed over the WHOLE extract, so it is
    a static property of the bin and does not shift with the years solved.
    """
    f_exact, f_digits = fleet_unit_index(roster)
    bin_units: dict[tuple[int, str], set[str]] = {}
    for r in df_all.itertuples(index=False):
        t = outages._generic_unit_outage_target(
            int(r.facility_id), r.unit_id, r.plant_group
        )
        if t is None or t not in cap or t[1] not in STEAM_GROUPS:
            continue
        bin_units.setdefault(t, set()).add(str(r.unit_id))

    eligible: set[tuple[int, str]] = set()
    pairmap: dict[tuple[int, str, str], float] = {}
    diag: list[dict] = []
    for (plant, group), uids in sorted(bin_units.items()):
        fleet = roster.get((plant, group), [])
        gid_pmax = {
            _norm_unit_id(u.split("_", 1)[1] if "_" in u else u): pm
            for u, pm in fleet
        }
        local: dict[str, float] = {}
        unresolved: list[str] = []
        for u in uids:
            full = _norm_unit_id(u)
            if full.startswith(SYNTHETIC_UNIT_PREFIX):
                unresolved.append(u)
                continue
            if (plant, group, full) in f_exact:
                local[u] = f_exact[(plant, group, full)]
                continue
            digits = re.sub(r"\D", "", full)
            cands = f_digits.get((plant, group, digits)) if digits else None
            if cands is not None and len(cands) == 1:
                local[u] = cands[0]
            else:
                unresolved.append(u)
        used = {_norm_unit_id(u) for u in local}
        unmatched = [g for g in gid_pmax if g not in used]
        paired = False
        if len(unresolved) == 1 and len(unmatched) == 1:
            local[unresolved[0]] = gid_pmax[unmatched[0]]
            unresolved = []
            paired = True
        ok = not unresolved
        if ok:
            eligible.add((plant, group))
            for u, pm in local.items():
                pairmap[(plant, group, u)] = pm
        diag.append(
            {
                "plant": int(plant),
                "group": str(group),
                "bin_cap_mw": round(float(cap[(plant, group)]), 4),
                "n_fleet_units": len(fleet),
                "n_extract_units": len(uids),
                "eligible": ok,
                "used_residual_pairing": paired,
                "unresolved_extract_units": sorted(unresolved),
                "unmatched_fleet_units": sorted(unmatched),
                "has_synthetic_row": any(
                    _norm_unit_id(u).startswith(SYNTHETIC_UNIT_PREFIX) for u in uids
                ),
            }
        )
    return eligible, pairmap, diag


def run_n6_n7(cap, roster, df_all) -> dict:
    """The BUILDABLE lever, measured: bin-scoped alignment coverage and GWh.

    N-6 is the coverage (which bins the all-or-nothing rule admits, and WHY the
    rest are refused — the taxonomy of the refusals is itself a result). N-7 is
    the size: production availability against aligned availability, integrated
    against each bin's LP capacity. Positive GWh = capability the production
    basis wrongly REMOVES and the alignment gives back.
    """
    eligible, pairmap, diag = resolve_bin_alignment(cap, roster, df_all)
    has_hours = outages._has_hour_grain(df_all)
    status_idx = (
        outages._fleet_status_index(ISO) if KEEPER["fleet_status_scope"] else None
    )
    per_year = {y: 0.0 for y in YEARS}
    per_bin: dict[tuple[int, str], dict] = {}
    for year in YEARS:
        prod: dict[tuple[int, str], np.ndarray] = {}
        algn: dict[tuple[int, str], np.ndarray] = {}
        for r in df_all.itertuples(index=False):
            t = outages._generic_unit_outage_target(
                int(r.facility_id), r.unit_id, r.plant_group
            )
            if t is None or t not in cap or t not in eligible:
                continue
            if status_idx is not None:
                st = status_idx.get(int(r.facility_id), {}).get(
                    str(r.unit_id).strip().upper()
                )
                if st is not None and st != "OP":
                    continue
            u = r.unit_capacity_mw
            if pd.isna(u) or float(u) <= 0.0:
                continue
            w0, w1 = outages.unit_outage_event_window(r, has_hours)
            m = outages.outage_hour_mask(w0, w1, year, HOURS)
            if not m.any():
                continue
            prod.setdefault(t, np.zeros(HOURS))[m] += float(u) / cap[t]
            algn.setdefault(t, np.zeros(HOURS))[m] += (
                pairmap[(t[0], t[1], str(r.unit_id))] / cap[t]
            )
        for t in prod:
            d = float(
                np.sum(np.clip(1 - algn[t], 0, 1) - np.clip(1 - prod[t], 0, 1))
                * cap[t]
                / 1000.0
            )
            if abs(d) < 1e-9:
                continue
            per_year[year] += d
            per_bin.setdefault(
                t, {"plant": t[0], "group": t[1], "bin_cap_mw": round(cap[t], 4),
                    "gwh_by_year": {str(y): 0.0 for y in YEARS}}
            )["gwh_by_year"][str(year)] = round(d, 4)
    touched_cap = sum(d["bin_cap_mw"] for d in diag)
    elig_cap = sum(d["bin_cap_mw"] for d in diag if d["eligible"])
    return {
        "design": (
            "bin-scoped all-or-nothing: a steam bin is aligned onto the LP's own "
            "per-unit pmax basis only when every extract unit in it resolves 1-1 "
            "onto a distinct fleet unit of that bin; otherwise untouched."
        ),
        "steam_bins_touched": len(diag),
        "steam_bins_eligible": sum(1 for d in diag if d["eligible"]),
        "cap_mw_touched": round(touched_cap, 1),
        "cap_mw_eligible": round(elig_cap, 1),
        "cap_share_eligible": round(elig_cap / touched_cap, 4) if touched_cap else None,
        "gwh_by_year": {str(y): round(per_year[y], 4) for y in YEARS},
        "per_bin": sorted(
            per_bin.values(),
            key=lambda r: -max(abs(v) for v in r["gwh_by_year"].values()),
        ),
        "bin_diagnostics": sorted(diag, key=lambda d: -d["bin_cap_mw"]),
    }


def main() -> None:
    cap = outages._iso_plant_capacity(
        ISO, KEEPER["cc_steam_part_reclass"], KEEPER["cc_nameplate_basis"]
    )
    roster = fleet_units_by_bin()
    exact, by_digits = eia_unit_index()

    std_path = outages.unit_outage_csv_for_iso(
        ISO, KEEPER["mixed_gas_routing"], KEEPER["per_unit_crosswalk"]
    )
    maxgen_path = outages.unit_outage_maxgen_csv_for_iso(
        ISO, KEEPER["mixed_gas_routing"]
    )

    overlays: dict[str, pd.DataFrame] = {}
    std = outages._load_unit_outage_events(std_path, ISO)
    overlays["std5d"] = std[std["duration_days"] >= outages.UNIT_OUTAGE_MIN_DAYS]
    if maxgen_path is not None and Path(maxgen_path).exists():
        overlays["maxgen"] = pd.read_csv(maxgen_path)

    report: dict = {
        "probe": "_miso201_st_basis_phase0",
        "session": "miso-201",
        "keeper_bundle": "results/calibration/miso200_unitroute_B",
        "keeper_run_id": "2026-09-02-miso-200-unitroute",
        "keeper_args": dict(KEEPER),
        "extracts": {
            "std5d": str(std_path.relative_to(REPO)),
            "maxgen": (
                str(Path(maxgen_path).relative_to(REPO))
                if maxgen_path is not None and Path(maxgen_path).exists()
                else None
            ),
        },
        "n1": {},
        "n2": {},
        "n3": {},
        "n4": {},
    }

    # ---- N-1 reproduction gate + N-3 census -------------------------------
    n1: dict = {"checked": 0, "mismatched": [], "status": None}
    census: list[dict] = []
    for overlay, df in overlays.items():
        for year in YEARS:
            if overlay == "std5d":
                sums, contrib = reconstruct_preclip(df, year, cap)
            else:
                sums, contrib = reconstruct_preclip_maxgen(df, year, cap)
            # Production arrays for this overlay/year, at the keeper's args.
            if overlay == "std5d":
                prod = outages.unit_outage_derate_factors(
                    year,
                    HOURS,
                    outages.BINS_CSV_DEFAULT,
                    iso=ISO,
                    cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"],
                    cc_nameplate_basis=KEEPER["cc_nameplate_basis"],
                    fleet_status_scope=KEEPER["fleet_status_scope"],
                    mixed_gas_routing=KEEPER["mixed_gas_routing"],
                    per_unit_crosswalk=KEEPER["per_unit_crosswalk"],
                )
            else:
                prod = outages.unit_outage_maxgen_derate_factors(
                    year,
                    HOURS,
                    iso=ISO,
                    cc_steam_part_reclass=KEEPER["cc_steam_part_reclass"],
                    cc_nameplate_basis=KEEPER["cc_nameplate_basis"],
                    mixed_gas_routing=KEEPER["mixed_gas_routing"],
                )
            rebuilt = {k: np.clip(1.0 - v, 0.0, 1.0) for k, v in sums.items()}
            if set(rebuilt) != set(prod):
                n1["mismatched"].append(
                    {
                        "overlay": overlay,
                        "year": year,
                        "reason": "bin key set differs",
                        "only_rebuilt": sorted(
                            f"{p}:{g}" for p, g in set(rebuilt) - set(prod)
                        )[:10],
                        "only_prod": sorted(
                            f"{p}:{g}" for p, g in set(prod) - set(rebuilt)
                        )[:10],
                    }
                )
            for key in sorted(set(rebuilt) & set(prod)):
                n1["checked"] += 1
                if not np.array_equal(rebuilt[key], prod[key]):
                    n1["mismatched"].append(
                        {
                            "overlay": overlay,
                            "year": year,
                            "bin": f"{key[0]}:{key[1]}",
                            "max_abs_diff": float(
                                np.max(np.abs(rebuilt[key] - prod[key]))
                            ),
                        }
                    )

            # ---- N-3: the overflow census, on this overlay/year ------------
            for key, v in sums.items():
                plant, group = key
                over = v > 1.0 + 1e-12
                if not over.any():
                    continue
                units = roster.get(key, [])
                unit_caps = sorted((c for _, c in units), reverse=True)
                n_fleet = len(units)
                h_star = int(np.argmax(v))
                # Contributors in the peak-overflow hour.
                active = [
                    c["unit_id"] for c in contrib.get(key, []) if c["mask"][h_star]
                ]
                n_contrib = len(set(active))
                # A RIGOROUS lower bound on the capability wrongly removed: at
                # most n_contrib fleet units can be out, so at least the sum of
                # the bin's SMALLEST (n_fleet - n_contrib) units is still there.
                # Clipping to 0.0 removes that too.
                if n_contrib < n_fleet:
                    phantom_mw = float(sum(unit_caps[n_contrib:]))
                else:
                    phantom_mw = 0.0
                # Hours where the clip actually bites (v >= 1 => availability 0).
                zero_hours = int(np.sum(v >= 1.0 - 1e-12))
                census.append(
                    {
                        "overlay": overlay,
                        "year": year,
                        "plant": int(plant),
                        "group": str(group),
                        "steam": group in STEAM_GROUPS,
                        "bin_cap_mw": round(float(cap[key]), 4),
                        "n_fleet_units": n_fleet,
                        "fleet_unit_caps": [round(c, 4) for c in unit_caps],
                        "max_preclip_share": round(float(v.max()), 6),
                        "hours_over_1": int(over.sum()),
                        "hours_clipped_to_zero": zero_hours,
                        "peak_hour": h_star,
                        "n_contributors_at_peak": n_contrib,
                        "contributors_at_peak": sorted(set(active)),
                        "verdict": (
                            "LIVE" if n_contrib < n_fleet else "INERT_UNITS_ARE_BIN"
                        ),
                        "phantom_mw_lower_bound": round(phantom_mw, 4),
                        "phantom_gwh_lower_bound": round(
                            phantom_mw * zero_hours / 1000.0, 4
                        ),
                    }
                )
    n1["status"] = "PASS" if not n1["mismatched"] else "FAIL"
    report["n1"] = n1

    # ---- N-2 numerator basis ---------------------------------------------
    rows = []
    for overlay, df in overlays.items():
        for r in df.itertuples(index=False):
            grp = str(getattr(r, "plant_group", "") or "")
            hit = lookup_unit(exact, by_digits, int(r.facility_id), r.unit_id)
            raw_num = (
                getattr(r, "unit_capacity_mw", None)
                if overlay == "std5d"
                else getattr(r, "derate_mw", None)
            )
            ucap = float(raw_num) if raw_num is not None and pd.notna(raw_num) else None
            rows.append(
                {
                    "overlay": overlay,
                    "group": grp,
                    "source": str(getattr(r, "capacity_source", "")),
                    "num": ucap,
                    "nameplate": hit[0] if hit else None,
                    "summer": hit[1] if hit else None,
                }
            )
    nb = pd.DataFrame(rows)
    n2: dict = {"by_source": {}, "steam_by_source": {}}
    for scope, frame in (
        ("by_source", nb),
        ("steam_by_source", nb[nb["group"].isin(STEAM_GROUPS)]),
    ):
        for src, sub in frame.groupby("source"):
            joined = sub.dropna(subset=["num", "summer"])
            joined = joined[joined["summer"] > 0]
            n2[scope][str(src)] = {
                "rows": int(len(sub)),
                "eia_joined": int(len(joined)),
                "median_num_over_summer": (
                    round(float((joined["num"] / joined["summer"]).median()), 6)
                    if len(joined)
                    else None
                ),
                "median_num_over_nameplate": (
                    round(
                        float(
                            (
                                joined["num"]
                                / joined["nameplate"].where(joined["nameplate"] > 0)
                            ).median()
                        ),
                        6,
                    )
                    if len(joined)
                    else None
                ),
            }
    report["n2"] = n2

    # ---- N-3 rollup -------------------------------------------------------
    steam = [c for c in census if c["steam"]]
    live_steam = [c for c in steam if c["verdict"] == "LIVE"]
    live_bins = sorted({(c["plant"], c["group"]) for c in live_steam})
    report["n3"] = {
        "overflow_cells_all_groups": len(census),
        "overflow_cells_steam": len(steam),
        "steam_cells_live": len(live_steam),
        "steam_cells_inert": len(steam) - len(live_steam),
        "distinct_live_steam_bins": [f"{p}:{g}" for p, g in live_bins],
        "phantom_gwh_lower_bound_by_year": {
            str(y): round(
                sum(c["phantom_gwh_lower_bound"] for c in live_steam if c["year"] == y),
                4,
            )
            for y in YEARS
        },
        "verdict": "LEVER_LIVE" if live_steam else "LEVER_INERT",
        "cells": sorted(
            census,
            key=lambda c: (-c["max_preclip_share"], c["plant"], c["year"]),
        ),
    }

    report["n5"] = run_n5(overlays, cap, roster, exact, by_digits)
    report["n6_n7"] = run_n6_n7(cap, roster, overlays["std5d"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, default=str))
    print(f"N-1 reproduction: {n1['status']} ({n1['checked']} bins checked)")
    if n1["mismatched"]:
        print(json.dumps(n1["mismatched"][:5], indent=1, default=str))
    print(
        f"N-3 census: {len(steam)} steam overflow cells, "
        f"{len(live_steam)} LIVE -> {report['n3']['verdict']}"
    )
    n5 = report["n5"]
    print(
        "N-5 basis alignment (steam bins, GWh capability returned): "
        + ", ".join(f"{y}={v}" for y, v in n5["by_year"].items())
        + f"  [join rate {n5['joinability']['join_rate']}]"
    )
    n67 = report["n6_n7"]
    print(
        f"N-6 coverage: {n67['steam_bins_eligible']}/{n67['steam_bins_touched']} "
        f"steam bins eligible ({n67['cap_mw_eligible']:.0f} of "
        f"{n67['cap_mw_touched']:.0f} MW, {100*n67['cap_share_eligible']:.1f}%)"
    )
    print(
        "N-7 buildable lever (GWh capability returned): "
        + ", ".join(f"{y}={v:+.1f}" for y, v in n67["gwh_by_year"].items())
    )
    print(f"wrote {OUT.relative_to(REPO)}")




# ---------------------------------------------------------------------------
# N-5 / N-6 — the ALIGNMENT COUNTERFACTUAL and the LIVE-cell taxonomy.
#
# N-3's count-based liveness test answers the charter's question as the charter
# posed it, but it is NOT the size of the object, for two reasons the census
# itself surfaced:
#
#  1. **The clip hides only the extreme.** A basis-inflated numerator over-removes
#     in EVERY hour a steam unit is out, whether or not the bin's total share
#     crosses 1.0. Two of four units out at a 1.18x-inflated numerator removes
#     ~18 % too much capability and never overflows, so N-3 never sees it. The
#     honest magnitude is the availability difference integrated over all hours,
#     not the overflow.
#  2. **N-3's test false-positives on a synthetic plant-level row.** The
#     `eia923_netzero` family (unit_id `NET0-923`) carries ONE row whose
#     `unit_capacity_mw` is the WHOLE PLANT's nameplate, standing for a
#     whole-plant lay-up. Counting it as "one unit out of two" flags the bin LIVE
#     when zeroing it may well be correct. It is a different object and is
#     separated here rather than absorbed.
#
# The alignment measured here is the repair as it would actually be built: each
# extract row's removed MW is put on THE LP'S OWN BASIS — the fleet unit's
# `pmax_mw`, which is precisely the capacity the availability multiplier is
# applied to. That makes the ratio dimensionally consistent by construction
# (a bin all of whose units are out lands on exactly 1.0, never 1.13), and it is
# zero-DOF: no scalar is chosen, the number is the fleet's own.
# ---------------------------------------------------------------------------

SYNTHETIC_UNIT_PREFIX = "NET0"


def fleet_unit_index(
    roster: dict[tuple[int, str], list[tuple[str, float]]],
) -> tuple[dict, dict]:
    """Return ``(exact, by_digits)`` maps from a bin's fleet units to their pmax.

    Keyed ``(plant, group, normalised_generator_id)`` so a join can never pull a
    capacity across a bin boundary. Fleet unit ids are ``"<plant>_<gen id>"``;
    the plant prefix is stripped before normalisation so the key is the EIA
    generator id the extract's CAMPD unit id has to match.
    """
    exact: dict[tuple[int, str, str], float] = {}
    by_digits: dict[tuple[int, str, str], list[float]] = {}
    for (plant, group), units in roster.items():
        for uid, pmax in units:
            gid = uid.split("_", 1)[1] if "_" in uid else uid
            full = _norm_unit_id(gid)
            exact[(plant, group, full)] = pmax
            digits = re.sub(r"\D", "", full)
            if digits:
                by_digits.setdefault((plant, group, digits), []).append(pmax)
    return exact, by_digits


def aligned_numerator(
    f_exact: dict, f_digits: dict, plant: int, group: str, unit_id: object
) -> float | None:
    """Return the fleet ``pmax_mw`` of the extract row's unit, or ``None``.

    FAILS CLOSED: an unresolvable unit id (including every synthetic
    plant-level ``NET0-923`` row) returns ``None`` and the caller leaves the
    production numerator untouched, so the counterfactual can only ever
    UNDER-state the repair's reach — never overstate it.
    """
    full = _norm_unit_id(unit_id)
    if full.startswith(SYNTHETIC_UNIT_PREFIX):
        return None
    if (plant, group, full) in f_exact:
        return f_exact[(plant, group, full)]
    digits = re.sub(r"\D", "", full)
    if digits:
        cands = f_digits.get((plant, group, digits))
        if cands is not None and len(cands) == 1:
            return cands[0]
    return None


if __name__ == "__main__":
    main()
