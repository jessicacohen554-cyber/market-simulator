#!/usr/bin/env python3
"""pjm-141 W6-T — WHICH TRANCHE sets the model's overnight (h01–h04) price.

`FINDING-pjm139` §W4 established what the overnight bottom-of-distribution miss
is **not**: not a floor-pinning artifact (the model prints 872 / 825 / 951
distinct overnight price levels at a 0.7–0.9 % modal share) and not `ST_GAS`
(0.9–1.9 % of overnight thermal energy). What it left open is the question this
probe answers:

    the h01–h04 stack is `CC_REGULAR` 66–69 % + `COAL_BIT` 23–26 % — but which
    **TRANCHE** of those two sets the clearing point?

Under `use_campd_bins` every plant enters the LP as a rising ladder of tranches
(`docs/binning-methodology.md`, `data.fleet.assembly.bins_to_fleet`):

  * ``mustrun``  — coal only; the take-or-pay / cycling floor, bid at
    VOM + carbon + NOx with the fuel cost sunk, so it is the CHEAPEST rung in
    the whole fleet and always in merit.
  * ``sync``     — the spot (non-contracted) half of the coal min-load split
    under ``coal_mustrun_online_pmin``; same min-load heat rate as ``mustrun``
    but bid at FULL SRMC.
  * ``committed`` — the part-load range when started; carries the start cost and
    min-run window.
  * ``econ``/``econcNN`` — incremental loading above part load, the plant's most
    efficient slice.
  * ``peak``/``peakN`` — duct-firing / overfire, heat rate scaled up.

The tranche identity therefore *is* the offer-level question: a price set by
``econ`` rungs says the model's overnight clearing point is ordinary
economic loading, while a price set by ``committed`` rungs says it is set by the
PART-LOAD heat-rate penalty of units the model has chosen to keep online.

Five measurements, **no LP**:

* **T1 — the marginal tranche census.** The pjm-138 §4.1 / pjm-122 marginal-set
  test (a unit is marginal when its own hourly offer equals its own zone's dual
  to within ``EPS``), reported by ``(class, tranche)`` and by tranche family,
  over h01–h04 (all-year and DJF) with the evening peak as a control so the
  overnight readout is never judged in isolation.
* **T2 — the offer-stack depth.** Where the model's available overnight supply
  actually sits relative to (a) its own dual and (b) PJM's own measured
  overnight p05. This distinguishes "the model has no offer cheap enough"
  (§W4's stated reading) from "the model has cheap offers but needs more MW than
  they cover".
* **T3 — idle-vs-dispatched by tranche.** Cheap capacity sitting IDLE beneath a
  dearer dual is the signature of something displacing it; cheap capacity fully
  loaded is the signature of a requirement that exceeds the cheap rungs.
* **T4 — the overnight requirement.** The model's own overnight thermal MW
  against the CAMPD measured actual from the committed bench payload. If the
  model burns more thermal overnight than PJM did, it stands higher on its own
  stack and the price is dearer with no offer-level defect at all.
* **T5 — the marginal-cost decomposition of the marginal rung**, so a successor
  chartering a lever knows which INPUT (heat rate, fuel price, VOM, carbon) it
  would have to move, and by how much, to reach PJM's overnight p05.

Fleet reconstruction reuses `_pjm138_marginal_ownership._keeper_fleet` verbatim
(`meta.json` → ``replay_keeper.build_kwargs`` → ``run_year(fleet_only=True)``),
so the offers censused are the offers the keeper solved on — never a
re-derivation that could drift. Measured hour keys come from
`_pjm138_mec_gap_shape`'s UTC-derived loaders (`FINDING-pjm138` §5: PJM's EPT
labels are not a valid interval key).

Usage
-----
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm141_overnight_tranche.py \
        --bundle results/calibration/pjm140_rampenv_B \
        --out results/probes/pjm141_overnight_tranche.json

Rebuilds one fleet per year (~4 GB, ~7 min); years are processed sequentially
and each year's arrays are released before the next.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

YEARS = (2023, 2024, 2025)
HOURS = 8760

#: h01–h04, the `FINDING-pjm139` §W4 window, verbatim.
OVERNIGHT = (1, 2, 3, 4)
#: The evening peak, carried as a CONTROL cell only — a tranche mix is not
#: interpretable without knowing what the same census says in a tight hour.
EVEPEAK = (16, 17, 18)

#: PJM's own measured overnight p05 system energy price, `FINDING-pjm139` §W4.
#: The target the model's cheapest overnight offer has to be able to reach.
MEASURED_OVERNIGHT_P05 = {2023: 13.32, 2024: 11.44, 2025: 17.02}

#: Tranche families, in merit order within a plant. The LP suffix is the last
#: `_`-delimited segment of `unit_id` (`data.fleet.assembly.bins_to_fleet`
#: builds `f"{bin_id}_{suffix}"`); multi-slice bands carry a numeric tail
#: (`econc00`, `committed01`, `peak2`), so the family is the PREFIX — matched
#: longest-first so `committed01` never resolves to `committed`'s prefix twice.
TRANCHE_FAMILIES = ("mustrun", "sync", "committed", "econ", "peak")

#: Model classes that can be marginal overnight. Reported as the whole thermal
#: set rather than pre-selected, so the readout cannot beg the question.
THERMAL_CLASSES = (
    "COAL_BIT",
    "COAL_PRB",
    "COAL_WC",
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)

OUT_PATH = Path("results/probes/pjm141_overnight_tranche.json")


def _load(name: str):
    """Import a sibling probe module by file path (they are not a package)."""
    path = REPO / "scripts" / "probes" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.lstrip("_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _tranche_of(unit_id: str) -> str:
    """The tranche family of one LP generator, from its `unit_id` suffix.

    `bins_to_fleet` names every CAMPD tranche `f"{bin_id}_{suffix}"` with
    `suffix` in {mustrun, sync, committed[NN], econ|econcNN, peak[N]}. A
    non-binned generator (legacy bin, renewable, import, virtual) has no such
    suffix and is reported as `_unbinned` rather than being silently forced into
    a family.
    """
    tail = str(unit_id).rsplit("_", 1)[-1]
    for fam in TRANCHE_FAMILIES:
        if tail.startswith(fam):
            return fam
    return "_unbinned"


def _hour_month(year: int) -> np.ndarray:
    """Calendar month per hour-of-year on the model's own 8760 EST clock."""
    idx = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    return idx.month.to_numpy()


def _measured_mec(year: int, p138, p137) -> np.ndarray:
    """PJM's RTO-uniform measured system energy price, UTC-keyed."""
    comp = p138._measured_components_est(year, p137)
    dom = "PJM_Dominion"
    return comp["mec"][dom].to_numpy(float)


def _bench_thermal_hourly(year: int) -> dict[str, np.ndarray]:
    """Measured hourly MW per CC/CT/ST family from the COMMITTED bench payload.

    Same decode as `_pjm139_winter_ramp._bench_bucket_hourly`: the per-plant
    CAMPD actual is `round(100 x mw / nameplate)` uint8 base64, so quantization
    is 1 % of each plant's nameplate. Read at the FLEET AGGREGATE only — never
    per plant — which is what T4 needs.
    """
    import base64
    import gzip

    path = REPO / "frontend/data/backcast/bench/PJM" / f"{year}.json.gz"
    with gzip.open(path) as fh:
        bench = json.load(fh)["bench"]["plants"]

    bucket_of = {
        "CC_REGULAR": "CC",
        "CC_CHP": "CC",
        "CT_PEAKER": "CT",
        "CT_CHP": "CT",
        "COAL_BIT": "ST",
        "COAL_PRB": "ST",
        "COAL_WC": "ST",
        "COAL": "ST",
        "ST_GAS": "ST",
        "ST_CHP": "ST",
    }
    out = {b: np.zeros(HOURS) for b in ("CC", "CT", "ST")}
    n = 0
    for rec in bench.values():
        if not isinstance(rec, dict):
            continue
        b = bucket_of.get(str(rec.get("group")))
        if b is None or not rec.get("campd"):
            continue
        raw = np.frombuffer(base64.b64decode(rec["campd"]), dtype=np.uint8).astype(float)
        mw = raw[:HOURS] / 100.0 * float(rec.get("npl") or 0.0)
        out[b][: len(mw)] += mw
        n += 1
    out["_plants"] = n  # type: ignore[assignment]
    return out


def _model_class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class MW per hour from the keeper's committed sidecar."""
    cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    return (
        cls.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(HOURS))
        .fillna(0.0)
    )


def _year(bundle: Path, year: int, own, p138, p137) -> dict:
    """All five measurements for one year, on one fleet reconstruction."""
    state = own._keeper_fleet(bundle, year)
    fa = state["fleet_arrays"]

    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    avail = np.asarray(fa.pmax, dtype=float)[:, None] * np.asarray(
        fa.availability, dtype=float
    )

    unit_ids = [str(u) for u in getattr(fa, "unit_ids", [])]
    if len(unit_ids) != mc.shape[0]:
        raise SystemExit(
            f"unit_ids ({len(unit_ids)}) does not align with mc rows ({mc.shape[0]})"
        )
    tranche = np.array([_tranche_of(u) for u in unit_ids], dtype=object)
    grp = np.array(
        [str(g) if g else "?" for g in np.asarray(fa.plant_group, dtype=object)],
        dtype=object,
    )

    price, lw, _netload = own._model_prices(bundle, year)
    zones = list(price.columns)
    from market_sim.config.iso_configs import get_iso_config

    all_zone_names = list(get_iso_config("PJM").zone_names)
    zi = np.asarray(fa.zone_idx, dtype=int)
    zone_name = np.array(
        [all_zone_names[i] if i < len(all_zone_names) else own.EXTERNAL_ZONE for i in zi],
        dtype=object,
    )
    internal = np.isin(zone_name, zones)
    dual = np.zeros_like(mc)
    for z in zones:
        m = zone_name == z
        if m.any():
            dual[m, :] = price[z].to_numpy(float)[None, :]

    hod = np.arange(HOURS) % 24
    month = _hour_month(year)
    djf = np.isin(month, (12, 1, 2))
    mec = _measured_mec(year, p138, p137)
    target = MEASURED_OVERNIGHT_P05[year]

    thermal = np.isin(grp, THERMAL_CLASSES) & internal

    cells = {
        "overnight_h01_h04": np.isin(hod, OVERNIGHT),
        "djf_overnight_h01_h04": np.isin(hod, OVERNIGHT) & djf,
        "evepeak_h16_h18_CONTROL": np.isin(hod, EVEPEAK),
    }

    out: dict[str, dict] = {
        "fleet": {
            "lp_generators": int(mc.shape[0]),
            "internal": int(internal.sum()),
            "thermal_internal": int(thermal.sum()),
            "tranche_rows": {
                f: int(((tranche == f) & internal).sum()) for f in TRANCHE_FAMILIES
            },
            "unbinned_rows": int(((tranche == "_unbinned") & internal).sum()),
            "thermal_capacity_gw_by_tranche": {
                f: float(
                    np.asarray(fa.pmax, dtype=float)[thermal & (tranche == f)].sum() / 1e3
                )
                for f in TRANCHE_FAMILIES
            },
        },
        "measured_overnight_p05_target": target,
        "cells": {},
    }

    for lab, sel in cells.items():
        sub_mc = mc[:, sel]
        sub_av = avail[:, sel]
        sub_du = dual[:, sel]
        live = internal[:, None] & (sub_av > 1.0)

        # ---- T1 the marginal census -------------------------------------
        at = live & (np.abs(sub_mc - sub_du) <= own.EPS)
        n_at = at.sum(axis=0)
        good = n_at > 0
        by_pair: dict[str, float] = {}
        by_tranche: dict[str, float] = {}
        by_class: dict[str, float] = {}
        if good.any():
            w = at[:, good].astype(float) / n_at[good][None, :]
            per_unit = w.mean(axis=1) * 100.0  # count share, pjm-122's construction
            for k in sorted(set(grp[internal])):
                s = float(per_unit[grp == k].sum())
                if s > 0.05:
                    by_class[k] = s
            for f in list(TRANCHE_FAMILIES) + ["_unbinned"]:
                s = float(per_unit[tranche == f].sum())
                if s > 0.05:
                    by_tranche[f] = s
            for k in sorted(set(grp[internal])):
                for f in list(TRANCHE_FAMILIES) + ["_unbinned"]:
                    s = float(per_unit[(grp == k) & (tranche == f)].sum())
                    if s > 0.05:
                        by_pair[f"{k}:{f}"] = s

        # ---- T2 the offer-stack depth ------------------------------------
        # Capacity-weighted MC quantiles over the AVAILABLE thermal stack, plus
        # the MW available below (a) the model's own dual and (b) PJM's p05.
        th_live = thermal[:, None] & (sub_av > 1.0)
        mcv = sub_mc[th_live]
        avv = sub_av[th_live]
        nh = int(sel.sum())
        order = np.argsort(mcv)
        cum = np.cumsum(avv[order])
        tot = cum[-1] if cum.size else 0.0

        def _cap_q(q: float) -> float:
            """Capacity-weighted quantile of the available thermal offer stack."""
            if tot <= 0:
                return float("nan")
            i = int(np.searchsorted(cum, q * tot))
            return float(mcv[order][min(i, mcv.size - 1)])

        below_target_mw = float(avv[mcv < target].sum() / nh) if nh else 0.0
        below_dual_mw = float(avv[mcv < sub_du[th_live]].sum() / nh) if nh else 0.0
        cheapest_mw = float(avv[mcv <= _cap_q(0.02)].sum() / nh) if nh else 0.0

        # ---- T3 idle vs dispatched by tranche ---------------------------
        # Available MW per tranche family, and the share of it whose own offer
        # sits BELOW the hour's dual (i.e. capacity the LP had every economic
        # reason to load). A large in-merit-but-not-marginal block is normal;
        # what matters is whether a CHEAP family is capacity-exhausted.
        stack: dict[str, dict] = {}
        for f in TRANCHE_FAMILIES:
            fm = thermal & (tranche == f)
            if not fm.any():
                continue
            a = avail[fm][:, sel]
            m_ = mc[fm][:, sel]
            d_ = dual[fm][:, sel]
            liv = a > 1.0
            if not liv.any():
                continue
            stack[f] = {
                "avail_gw_mean": float(a.sum() / nh / 1e3),
                "mc_p05": float(np.percentile(m_[liv], 5)),
                "mc_p50": float(np.percentile(m_[liv], 50)),
                "mc_p95": float(np.percentile(m_[liv], 95)),
                "in_merit_gw_mean": float(a[liv & (m_ < d_)].sum() / nh / 1e3),
                "above_dual_gw_mean": float(a[liv & (m_ > d_)].sum() / nh / 1e3),
                "avail_gw_below_target": float(a[liv & (m_ < target)].sum() / nh / 1e3),
            }

        out["cells"][lab] = {
            "hours": nh,
            "hours_with_a_marginal_unit": int(good.sum()),
            "detection_rate_pct": float(good.mean() * 100) if nh else 0.0,
            "mean_model_dual_lw": float(lw[sel].mean()),
            "mean_measured_mec": float(np.nanmean(mec[sel])),
            "T1_marginal_count_share_pct_by_class_tranche": dict(
                sorted(by_pair.items(), key=lambda kv: -kv[1])
            ),
            "T1_marginal_count_share_pct_by_tranche": dict(
                sorted(by_tranche.items(), key=lambda kv: -kv[1])
            ),
            "T1_marginal_count_share_pct_by_class": dict(
                sorted(by_class.items(), key=lambda kv: -kv[1])
            ),
            "T2_stack": {
                "thermal_avail_gw_mean": float(tot / nh / 1e3) if nh else 0.0,
                "mc_capacity_weighted_p00": float(mcv.min()) if mcv.size else None,
                "mc_capacity_weighted_p02": _cap_q(0.02),
                "mc_capacity_weighted_p05": _cap_q(0.05),
                "mc_capacity_weighted_p10": _cap_q(0.10),
                "mc_capacity_weighted_p25": _cap_q(0.25),
                "mc_capacity_weighted_p50": _cap_q(0.50),
                "avail_gw_below_measured_p05_target": below_target_mw / 1e3,
                "avail_gw_below_own_dual": below_dual_mw / 1e3,
                "avail_gw_at_or_below_p02_offer": cheapest_mw / 1e3,
            },
            "T3_by_tranche": stack,
        }

    # ---- T4 the overnight requirement -----------------------------------
    piv = _model_class_hourly(bundle, year)
    bench = _bench_thermal_hourly(year)
    night = np.isin(hod, OVERNIGHT)
    mdl_fam = {
        "CC": ["CC_REGULAR", "CC_CHP"],
        "CT": ["CT_PEAKER", "CT_CHP"],
        "ST": ["COAL_BIT", "COAL_PRB", "COAL_WC", "ST_GAS", "ST_CHP"],
    }
    t4: dict[str, dict] = {"bench_plants_decoded": int(bench["_plants"])}  # type: ignore[arg-type]
    m_tot = a_tot = 0.0
    for fam, klasses in mdl_fam.items():
        mv = sum(
            piv[k].to_numpy(float) for k in klasses if k in piv.columns
        )
        mv = np.zeros(HOURS) if np.isscalar(mv) else np.asarray(mv, float)
        av = bench[fam]
        t4[fam] = {
            "model_gw_overnight": float(mv[night].mean() / 1e3),
            "measured_gw_overnight": float(av[night].mean() / 1e3),
            "delta_gw": float((mv[night].mean() - av[night].mean()) / 1e3),
        }
        m_tot += mv[night].mean()
        a_tot += av[night].mean()
    t4["THERMAL_TOTAL"] = {
        "model_gw_overnight": float(m_tot / 1e3),
        "measured_gw_overnight": float(a_tot / 1e3),
        "delta_gw": float((m_tot - a_tot) / 1e3),
        "model_over_measured": float(m_tot / a_tot) if a_tot else None,
    }
    # Non-thermal overnight supply, for attribution of any thermal excess.
    for k in ("nuclear", "wind", "solar", "hydro", "import", "biomass", "oil", "OTHER"):
        if k in piv.columns:
            t4[f"model_{k}_gw_overnight"] = float(piv[k].to_numpy(float)[night].mean() / 1e3)
    out["T4_overnight_requirement"] = t4

    # ---- T5 what the marginal rung is made of ---------------------------
    # For the overnight window, the capacity-weighted mean offer of the tranche
    # family that owns the largest marginal share, and the gap that family's
    # offer would have to close to reach PJM's p05. Reported so a successor
    # charters against an INPUT, not against the residual.
    ov = out["cells"]["overnight_h01_h04"]
    top = next(iter(ov["T1_marginal_count_share_pct_by_class_tranche"]), None)
    t5: dict[str, object] = {"dominant_marginal_class_tranche": top}
    if top is not None:
        k, f = top.split(":")
        fm = (grp == k) & (tranche == f) & internal
        sel = np.isin(hod, OVERNIGHT)
        a = avail[fm][:, sel]
        m_ = mc[fm][:, sel]
        liv = a > 1.0
        t5.update(
            {
                "units": int(fm.sum()),
                "capacity_gw": float(np.asarray(fa.pmax, float)[fm].sum() / 1e3),
                "offer_cap_weighted_mean": float((m_[liv] * a[liv]).sum() / a[liv].sum()),
                "offer_p05": float(np.percentile(m_[liv], 5)),
                "offer_p50": float(np.percentile(m_[liv], 50)),
                "gap_p05_to_measured_target": float(
                    np.percentile(m_[liv], 5) - target
                ),
                "model_overnight_dual_lw": float(lw[np.isin(hod, OVERNIGHT)].mean()),
                "measured_overnight_mec": float(
                    np.nanmean(mec[np.isin(hod, OVERNIGHT)])
                ),
            }
        )
    out["T5_marginal_rung_composition"] = t5

    # ---- T6 does ANY tranche's own offer vary within the day? -------------
    # The load-bearing claim, measured rather than inferred. Three candidate
    # hour-varying inputs exist in the offer path: the delivered-gas day series
    # (`gas_daily_shape` — `FINDING-pjm139` §2 measured its within-day σ at
    # ≤ 4.4e-16, i.e. flat), the fuel-INVARIANT net-revenue margin
    # (`gas_offer_net_revenue_margin`, hour-invariant by construction) and the
    # mid-curve conduct surface (`pjm_offer_midcurve_segments`, keyed on a
    # net-load TIGHTNESS bin). If the tranche's own offer has no diurnal
    # variation, then the model's entire intra-day price variation must come
    # from merit-order traversal — which is what the amplitude result measures.
    #
    # Reported as the per-unit σ of its own offer WITHIN each calendar day
    # (averaged over days and units), and the same units' mean offer in the two
    # windows, so a diurnal offer difference cannot hide inside an annual mean.
    doy = np.arange(HOURS) // 24
    t6: dict[str, object] = {}
    for lab, fam in (("dominant_rung", None), ("all_thermal", "all")):
        if fam is None:
            if top is None:
                continue
            k, f = top.split(":")
            fm = (grp == k) & (tranche == f) & internal
        else:
            fm = thermal
        if not fm.any():
            continue
        m_ = mc[fm]
        a_ = avail[fm]
        # Within-day σ per unit-day, averaged over unit-days with live capacity.
        sig = []
        for d in range(0, 365):
            h = doy == d
            if h.sum() < 24:
                continue
            blk = m_[:, h]
            live = (a_[:, h] > 1.0).all(axis=1)
            if live.any():
                sig.append(blk[live].std(axis=1))
        within_day_sigma = float(np.concatenate(sig).mean()) if sig else float("nan")
        nsel = np.isin(hod, OVERNIGHT)
        psel = np.isin(hod, EVEPEAK)
        lv = a_ > 1.0
        wn = (m_[:, nsel] * a_[:, nsel])[lv[:, nsel]].sum() / a_[:, nsel][lv[:, nsel]].sum()
        wp = (m_[:, psel] * a_[:, psel])[lv[:, psel]].sum() / a_[:, psel][lv[:, psel]].sum()
        t6[lab] = {
            "units": int(fm.sum()),
            "mean_within_day_offer_sigma": within_day_sigma,
            "cap_wtd_offer_h01_h04": float(wn),
            "cap_wtd_offer_h16_h18": float(wp),
            "diurnal_offer_delta": float(wp - wn),
        }
    out["T6_offer_diurnal_variation"] = t6

    del state, fa, mc, avail, dual
    gc.collect()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=REPO / "results/calibration/pjm140_rampenv_B",
        help="keeper bundle to census (default: the pjm-140 keeper)",
    )
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=list(YEARS),
        help="years to census (default: %(default)s)",
    )
    args = ap.parse_args(argv)

    own = _load("_pjm138_marginal_ownership")
    p138 = _load("_pjm138_mec_gap_shape")
    p137 = p138._load_p137()

    payload: dict[str, dict] = {}
    for year in args.years:
        print(f"pjm-141 W6-T {year}: rebuilding keeper fleet (no LP) …", flush=True)
        payload[str(year)] = _year(args.bundle, int(year), own, p138, p137)
        ov = payload[str(year)]["cells"]["overnight_h01_h04"]
        print(
            f"  {year} h01-h04 dual {ov['mean_model_dual_lw']:.2f} vs MEC "
            f"{ov['mean_measured_mec']:.2f} | tranche "
            f"{ov['T1_marginal_count_share_pct_by_tranche']}",
            flush=True,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"bundle": str(args.bundle), "years": payload}, indent=2))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
