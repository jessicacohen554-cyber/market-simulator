"""nyiso-244 — the ``measured_offer_surface`` NYISO design pass (gates G1-G4).

ZERO LP (rule 32 ``[R-SHARD]`` (a)). The only model-side call is a ``fleet_only``
rebuild of the keeper's own recipe, which enters no LP; everything else reads
the keeper's committed sidecars and the P-27 bid corpus.

Every threshold below is fixed in
``docs/PRECOMMIT-nyiso244-measured-offer-surface-design-2026-09-20.md`` §3,
committed at ``2e5097a5`` before any number here was computed (rule 1
``[R-STRUCT]``).

Four measured gates:

* **G1 — rule 19 ``[R-ONE-MECH]``.** Enumerate every armed mechanism writing a
  NYISO peak-rung offer from the keeper's OWN ``run_config.json``, and decompose
  the peak rung's offer into the increments each one prices. The claim under
  test is that ``gas_offer_net_revenue_margin`` prices the REGISTERED markup
  ``(m - phys)`` at a fuel-invariant anchor while a conditional surface would
  price the MEASURED scarcity increment ``(M - m)`` at the hour's fuel -- two
  disjoint increments of one curve.
* **G2 — the masking blocker.** P-27 carries no class, fuel or zone. Select the
  quick-start cohort by NYISO's OWN published product definition (a 10-Minute
  Non-Synchronized Reserve offer means offline-to-full-output in 10 minutes) and
  validate it against the keeper's own fleet census on three pre-registered
  statistics V1/V2/V3.
* **G3 — REACH.** Only the offers of the IDLE SUB-GATE capacity can move the
  energy dual (nyiso-242 phase 0D). The shared kernel prices PEAK RUNGS ONLY, so
  measure how much of the 4,715.7 MW idle below $300 in the 2022 winter missed
  cluster sits on peak rungs of the cohort's classes.
* **G4 — rule 13 ``[R-MEASURED]``.** Re-measure the day-ahead conditioning driver
  on EVERY year the keeper carries, not just the two nyiso-243 measured.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso244_offer_surface_design.py
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
GENBIDS = REPO / "data" / "raw" / "nyiso-bid-data" / "genbids"
OUT = REPO / "results" / "calibration" / "_nyiso244_offer_surface_design.json"

HOURS = 8760
THRESHOLD = 300.0

# --- PRECOMMIT §3 thresholds. Fixed before any number here was computed. ------
#: G2 selector: share of a gen's DAM offered hours that must carry a 10-Min
#: Non-Synch reserve offer for it to count as quick-start (presence-not-accident).
NS10_PRESENCE = 0.50
#: G2 V1 — the two corpora must describe the same fleet.
V1_SCOPE_TOL = 0.15
#: G2 V2 — cohort MW within +-25 %, cohort count within +-30 % of the model CT family.
V2_MW_TOL = 0.25
V2_N_TOL = 0.30
#: G2 V3 — median relative gap of the length-aligned sorted capacity vectors.
V3_FINGERPRINT_TOL = 0.25
#: G3 — the surface-reachable share of the object that must be cleared.
G3_REACH_FRAC = 0.50
#: nyiso-242 §3.2 — idle sub-gate MW in the 2022 winter missed cluster.
OBJECT_MW = 4715.7
#: G4 — the day-ahead ladder, and how many of the four years must be monotone.
DA_LADDER = (100.0, 150.0, 200.0, 300.0)
G4_MIN_YEARS = 3

#: The model's CT family — the population a 10-minute quick-start cohort maps to.
CT_FAMILY = ("CT_PEAKER", "CT_INTERMEDIATE", "CT_CHP")
#: Rows that are not NYCA-internal bid generators (nyiso-243 §3 scope trap).
_NON_GENBID = ("NYISO_external", "NYISO_DR")


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------
def _rung_family(unit_id: str) -> str:
    """``mustrun`` / ``sync`` / ``committed`` / ``econ`` / ``peak`` / ``other``.

    The kernel keys on the unit-id's trailing band token exactly this way
    (``offer_surfaces._conditional_surface_markup``), so this reproduces its
    scope rather than re-deriving one.
    """
    sfx = str(unit_id).rpartition("_")[2]
    for fam in ("mustrun", "sync", "committed", "econ", "peak"):
        if sfx.startswith(fam):
            return fam
    return "other"


def _internal(unit_ids: np.ndarray) -> np.ndarray:
    keep = np.ones(len(unit_ids), dtype=bool)
    for pre in _NON_GENBID:
        keep &= ~np.char.startswith(unit_ids.astype(str), pre)
    return keep


def fleet_state(year: int):
    """Fleet-only rebuild of the keeper's recipe — no LP is entered."""
    from scripts.probes.nyiso242_tail_reachability import fleet_state as _fs

    return _fs(year)


# ---------------------------------------------------------------------------
# G1 — rule 19 [R-ONE-MECH]: enumerate the armed peak-rung writers, decompose
# ---------------------------------------------------------------------------
#: Every ScenarioConfig field that can write a gas peak-rung offer, checked
#: against the keeper's own run_config rather than from memory (PRECOMMIT G1a).
_PEAK_WRITERS = (
    "gas_offer_net_revenue_margin",
    "gas_offer_margin_zonal_anchor",
    "gas_offer_margin_anchor_vintage",
    "gas_offer_margin_zonal_anchor_vintage",
    "cc_committed_offer_margin",
    "coal_peak_offer_margin",
    "nyiso_ct_peaker_bands_measured",
    "nyiso_ct_peaker_committed_measured",
    "nyiso_st_gas_econ_bands_deleaked",
    "gas_offer_curve",
    "miso_intermediate_gas_offer_margin",
    "ercot_offer_surface_conditional",
    "caiso_offer_surface_conditional",
    "pjm_offer_surface_conditional",
    "neiso_offer_surface_conditional",
)


def g1_rule19(config: dict) -> dict:
    """Enumerate-and-reconcile, measured on the keeper's own registered bands."""
    curves = config.get("offer_curve_by_group") or {}
    armed = {k: config.get(k) for k in _PEAK_WRITERS if config.get(k)}
    anchors = config.get("gas_offer_margin_anchor_by_zone") or {}
    iso_anchor = config.get("gas_offer_margin_anchor")

    per_class = {}
    for cls, band in curves.items():
        if "peak" not in band:
            continue
        m = float(band["peak"])
        phys = band.get("phys_peak")
        registered_markup_hr = None if phys is None else round(m - float(phys), 6)
        per_class[cls] = {
            "peak_mult_m": m,
            "phys_peak": None if phys is None else float(phys),
            # The increment gas_offer_net_revenue_margin reprices: (m - phys).
            # A class with no phys_* key is NEUTRAL by the field's own
            # construction ("phys = its own multiplier -> zero markup").
            "gonrm_registered_markup_hr": registered_markup_hr,
            "gonrm_inert_on_peak": registered_markup_hr in (None, 0.0),
        }
        # The realised fuel-invariant $/MWh the armed mechanism hands this
        # class's peak rung at a reference HR of 1 MMBtu/MWh, per zone anchor.
        if registered_markup_hr:
            per_class[cls]["gonrm_markup_usd_per_hr_unit_by_zone"] = {
                z: round(registered_markup_hr * float(a), 4) for z, a in anchors.items()
            } or {"ISO": round(registered_markup_hr * float(iso_anchor or 0.0), 4)}

    return {
        "armed_peak_writers": armed,
        "per_class": per_class,
        "decomposition": {
            "note": (
                "A peak rung's offer decomposes into three DISJOINT increments: "
                "phys*HR*fuel(t) (physical burn), (m-phys)*HR*anchor (the "
                "REGISTERED markup, which gas_offer_net_revenue_margin reprices "
                "to fuel-invariant), and (M-m)*HR*fuel(t) (the MEASURED scarcity "
                "increment a conditional surface would add). No MW is priced "
                "twice: GONRM never touches (M-m) and the surface never touches "
                "(m-phys). Overlap is 0 BY CONSTRUCTION, not by tolerance."
            ),
            "surface_increment": "(M - m) * HR_base * fuel(t)",
            "gonrm_increment": "(m - phys) * HR_base * anchor",
            "overlap": 0.0,
            "declared_construction_limit": (
                "The shared kernel prices the scarcity increment (M-m) "
                "MULTIPLICATIVELY, i.e. it tracks the hour's fuel. GONRM's own "
                "grounding argues real bidders express scarcity in $ terms, so a "
                "fuel-invariant form of the SAME measured increment is a "
                "legitimate successor question. Declared, not resolved here."
            ),
        },
    }


# ---------------------------------------------------------------------------
# G2 — the masking blocker: the cohort and its validation
# ---------------------------------------------------------------------------
_CENSUS_COLS = (
    "Masked Gen ID",
    "Market",
    "Upper Oper Limit",
    "Fixed Min Gen MW",
    "Zero Start-Up Cost",
    "On Dispatch",
    "10 Min Non-Synch Cost",
    "10 Min Spin Cost",
    "30 Min Non-Synch Cost",
    "30 Min Spin Cost",
    "Regulation MW",
)


def p27_census(year: int, market: str = "DAM") -> pd.DataFrame:
    """Per masked gen: capacity, min-gen, start-up and AS-product signatures."""
    frames: list[pd.DataFrame] = []
    for month in range(1, 13):
        path = GENBIDS / f"{year:04d}{month:02d}01biddata_genbids_csv.zip"
        if not path.exists():
            continue
        with zipfile.ZipFile(path) as z:
            raw = pd.read_csv(
                io.BytesIO(z.read(z.namelist()[0])),
                skipinitialspace=True,
                low_memory=False,
            )
        raw.columns = [c.strip() for c in raw.columns]
        raw = raw[raw["Market"].astype(str).str.strip() == market]
        if raw.empty:
            continue
        frames.append(raw[[c for c in _CENSUS_COLS if c in raw.columns]])
    if not frames:
        raise FileNotFoundError(f"no P-27 archives for {year}")
    d = pd.concat(frames, ignore_index=True)

    uol = d["Upper Oper Limit"].to_numpy(float)
    gid = d["Masked Gen ID"]
    g = d.groupby(gid)
    cen = pd.DataFrame(
        {
            "uol_max": g["Upper Oper Limit"].max(),
            "uol_p50": g["Upper Oper Limit"].median(),
            "rows": g.size(),
        }
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        mg = np.where(uol > 0, d["Fixed Min Gen MW"].to_numpy(float) / uol, np.nan)
    cen["mingen_frac_p50"] = pd.Series(mg, index=d.index).groupby(gid).median()
    cen["zero_startup_rate"] = (
        d["Zero Start-Up Cost"].astype(str).str.strip().eq("Y").groupby(gid).mean()
    )
    cen["on_dispatch_rate"] = (
        d["On Dispatch"].astype(str).str.strip().eq("Y").groupby(gid).mean()
    )
    # THE SELECTOR. A 10-Min Non-Synch reserve OFFER is NYISO's own statement
    # that the resource reaches full output from OFFLINE within 10 minutes. The
    # reserve MW columns of P-27 are 100 % null (PRECOMMIT §5), so presence is
    # read from the offer's COST column -- presence of an offer, not its size.
    cen["ns10_offer_rate"] = d["10 Min Non-Synch Cost"].notna().groupby(gid).mean()
    cen["sp10_offer_rate"] = d["10 Min Spin Cost"].notna().groupby(gid).mean()
    cen["ns30_offer_rate"] = d["30 Min Non-Synch Cost"].notna().groupby(gid).mean()
    cen["reg_offer_rate"] = d["Regulation MW"].notna().groupby(gid).mean()
    return cen


def g2_cohort(year: int, cen: pd.DataFrame, fa) -> dict:
    """Select the quick-start cohort and run V1/V2/V3 against the model fleet."""
    uid = np.array([str(u) for u in fa.unit_ids])
    pmax = np.asarray(fa.pmax, dtype=float)
    klass = np.array([str(k) for k in fa.plant_group])
    internal = _internal(uid)

    # The model side is per-TRANCHE; a P-27 masked gen is a PLANT. Collapse the
    # model's tranches to their plant key so the two sides count the same object.
    def _plant_key(u: str) -> str:
        parts = str(u).split("_")
        return "_".join(parts[:-1]) if len(parts) > 1 else str(u)

    plant = np.array([_plant_key(u) for u in uid])
    model = pd.DataFrame(
        {"plant": plant[internal], "klass": klass[internal], "pmax": pmax[internal]}
    )
    by_plant = model.groupby("plant").agg(
        pmax=("pmax", "sum"), klass=("klass", lambda s: s.iloc[0])
    )
    model_internal_mw = float(by_plant["pmax"].sum())
    ct = by_plant[by_plant["klass"].isin(CT_FAMILY)]
    model_ct_mw = float(ct["pmax"].sum())
    model_ct_n = int(len(ct))

    p27_mw = float(cen["uol_max"].sum())
    coh = cen[cen["ns10_offer_rate"] >= NS10_PRESENCE]
    cohort_mw = float(coh["uol_max"].sum())
    cohort_n = int(len(coh))

    v1 = abs(p27_mw - model_internal_mw) / model_internal_mw
    v2_mw = abs(cohort_mw - model_ct_mw) / model_ct_mw if model_ct_mw else np.inf
    v2_n = abs(cohort_n - model_ct_n) / model_ct_n if model_ct_n else np.inf

    a = np.sort(coh["uol_max"].to_numpy(float))[::-1]
    b = np.sort(ct["pmax"].to_numpy(float))[::-1]
    k = min(len(a), len(b))
    if k:
        denom = np.maximum(np.abs(b[:k]), 1e-9)
        v3 = float(np.median(np.abs(a[:k] - b[:k]) / denom))
    else:
        v3 = float("inf")

    return {
        "year": year,
        "selector": {
            "definition": (
                "a masked gen carrying a 10-Min Non-Synchronized Reserve OFFER in "
                f">= {NS10_PRESENCE:.0%} of its DAM offered hours. NYISO's own "
                "product definition: offline to full output within 10 minutes."
            ),
            "presence_bar": NS10_PRESENCE,
        },
        "p27": {"gens": int(len(cen)), "installed_mw": round(p27_mw, 1)},
        "model": {
            "internal_plants": int(len(by_plant)),
            "internal_mw": round(model_internal_mw, 1),
            "ct_family_plants": model_ct_n,
            "ct_family_mw": round(model_ct_mw, 1),
        },
        "cohort": {
            "gens": cohort_n,
            "mw": round(cohort_mw, 1),
            "uol_max_p50": round(float(coh["uol_max"].median()), 1) if cohort_n else None,
            "mingen_frac_p50": round(float(coh["mingen_frac_p50"].median()), 3)
            if cohort_n
            else None,
            "on_dispatch_rate_p50": round(float(coh["on_dispatch_rate"].median()), 3)
            if cohort_n
            else None,
        },
        "model_ct_unit_mw_p50": round(float(ct["pmax"].median()), 1) if model_ct_n else None,
        "V1_scope": {"value": round(v1, 4), "tol": V1_SCOPE_TOL, "PASS": bool(v1 <= V1_SCOPE_TOL)},
        "V2_size": {
            "mw_rel": round(float(v2_mw), 4),
            "n_rel": round(float(v2_n), 4),
            "mw_tol": V2_MW_TOL,
            "n_tol": V2_N_TOL,
            "PASS": bool(v2_mw <= V2_MW_TOL and v2_n <= V2_N_TOL),
        },
        "V3_fingerprint": {
            "median_rel_gap": round(v3, 4),
            "tol": V3_FINGERPRINT_TOL,
            "PASS": bool(v3 <= V3_FINGERPRINT_TOL),
        },
    }


# ---------------------------------------------------------------------------
# G3 — REACH: where the idle sub-gate capacity actually sits
# ---------------------------------------------------------------------------
def g3_reach(year: int, st) -> dict:
    """Idle-below-$300 MW decomposed by class AND rung family.

    Construction, stated because it is a choice: per class and hour the class's
    OWN committed P1 dispatch (``class_hourly``) is served by its CHEAPEST rows,
    so the idle set is the class's most expensive available capacity. Everything
    of that idle set whose offer is below the gate is what a pricing mechanism
    would have to lift; everything of THAT on a peak rung is what the shared
    kernel can actually reach.
    """
    from scripts.probes.nyiso242_tail_reachability import _is_thermal, missed_mask

    fa = st["fleet_arrays"]
    uid = np.array([str(u) for u in fa.unit_ids])
    pmax = np.asarray(fa.pmax, dtype=float)
    klass = np.array([str(k) for k in fa.plant_group])
    av = np.asarray(fa.availability, dtype=float)
    if av.ndim == 1:
        av = np.repeat(av[:, None], HOURS, axis=1)
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    fam = np.array([_rung_family(u) for u in uid])

    missed, month = missed_mask(year)
    idx = np.arange(len(missed))
    sel = idx[missed & np.isin(month, (1, 2, 12))]
    sel = sel[sel < mc.shape[1]]
    if not len(sel):
        return {"year": year, "hours": 0}

    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    gen = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")

    rows: dict[str, dict] = {}
    tot_idle = tot_idle_sub = tot_peak_sub = 0.0
    for cls in sorted(set(klass.tolist())):
        if not _is_thermal(cls):
            continue
        rsel = klass == cls
        if not rsel.any() or cls not in gen.columns:
            continue
        cap = pmax[rsel][:, None] * av[np.ix_(rsel, sel)]  # (n_rows, n_hours)
        px = mc[np.ix_(rsel, sel)]
        fm = fam[rsel]
        gvec = gen[cls].reindex([int(i) for i in sel]).to_numpy(float)
        gvec = np.nan_to_num(gvec)

        # Serve the class's own dispatch from its cheapest rows; the residual is idle.
        order = np.argsort(px, axis=0, kind="stable")
        cap_s = np.take_along_axis(cap, order, axis=0)
        px_s = np.take_along_axis(px, order, axis=0)
        fam_s = fm[order]
        cum = np.cumsum(cap_s, axis=0)
        served = np.clip(gvec[None, :] - (cum - cap_s), 0.0, cap_s)
        idle = cap_s - served
        sub = px_s < THRESHOLD

        idle_mw = float(np.median(idle.sum(axis=0)))
        idle_sub = float(np.median((idle * sub).sum(axis=0)))
        peak_sub = float(np.median((idle * sub * (fam_s == "peak")).sum(axis=0)))
        by_fam = {
            f: round(float(np.median((idle * sub * (fam_s == f)).sum(axis=0))), 1)
            for f in ("mustrun", "sync", "committed", "econ", "peak", "other")
        }
        rows[cls] = {
            "available_mw": round(float(np.median(cap.sum(axis=0))), 1),
            "dispatched_mw": round(float(np.median(gvec)), 1),
            "idle_mw": round(idle_mw, 1),
            "idle_below_gate_mw": round(idle_sub, 1),
            "idle_below_gate_on_peak_rungs_mw": round(peak_sub, 1),
            "idle_below_gate_by_rung_family_mw": by_fam,
        }
        tot_idle += idle_mw
        tot_idle_sub += idle_sub
        tot_peak_sub += peak_sub

    ct_peak_sub = sum(
        rows[c]["idle_below_gate_on_peak_rungs_mw"] for c in CT_FAMILY if c in rows
    )
    return {
        "year": year,
        "window": "winter_missed",
        "hours": int(len(sel)),
        "object_mw": OBJECT_MW,
        "by_class": rows,
        "total_idle_mw": round(tot_idle, 1),
        "total_idle_below_gate_mw": round(tot_idle_sub, 1),
        "total_idle_below_gate_on_peak_rungs_mw": round(tot_peak_sub, 1),
        "ct_family_idle_below_gate_on_peak_rungs_mw": round(ct_peak_sub, 1),
        "G3_all_class_peak_reach_frac": round(tot_peak_sub / OBJECT_MW, 4),
        "G3_ct_family_peak_reach_frac": round(ct_peak_sub / OBJECT_MW, 4),
        "G3_bar": G3_REACH_FRAC,
        "PASS_all_class_peak": bool(tot_peak_sub / OBJECT_MW >= G3_REACH_FRAC),
        "PASS_ct_family_peak": bool(ct_peak_sub / OBJECT_MW >= G3_REACH_FRAC),
    }


# ---------------------------------------------------------------------------
# G4 — rule 13: the DA conditioning driver on every keeper year
# ---------------------------------------------------------------------------
def g4_conditioning(years: tuple[int, ...]) -> dict:
    """MW offered above $300 across the DA ladder, per year."""
    from scripts.probes.nyiso243_measured_offer_stack import offer_stack_hourly
    from scripts.probes.nyiso243_offered_availability import windows

    out: dict = {"ladder": list(DA_LADDER), "min_years": G4_MIN_YEARS, "years": {}}
    mono = 0
    for year in years:
        win, _rt, da = windows(year)
        stack = offer_stack_hourly(year, "DAM")
        v = stack["above_300"].to_numpy(float)
        rec = {}
        seq = []
        for p in DA_LADDER:
            sel = np.where(da[: len(v)] > p)[0]
            x = v[sel]
            x = x[np.isfinite(x)]
            m = float(np.median(x)) if len(x) else float("nan")
            rec[f"da_gt_{p:.0f}"] = {"hours": int(len(x)), "offered_above_300_mw": round(m, 1)}
            seq.append(m)
        ok = all(b >= a for a, b in zip(seq, seq[1:]) if np.isfinite(a) and np.isfinite(b))
        rec["monotone"] = bool(ok)
        mono += int(ok)
        out["years"][str(year)] = rec
        print(f"  G4 {year}: {[round(s, 1) for s in seq]} monotone={ok}", flush=True)
    out["monotone_years"] = mono
    out["PASS"] = bool(mono >= G4_MIN_YEARS)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023, 2024, 2025])
    ap.add_argument("--reach-year", type=int, default=2022)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    config = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    result: dict = {
        "precommit": "docs/PRECOMMIT-nyiso244-measured-offer-surface-design-2026-09-20.md",
        "precommit_sha": "2e5097a5",
        "bundle": str(BUNDLE.relative_to(REPO)),
    }

    print("G1 — rule 19 enumerate-and-reconcile", flush=True)
    result["G1_rule19"] = g1_rule19(config)
    for cls, rec in result["G1_rule19"]["per_class"].items():
        print(
            f"  {cls:20s} m={rec['peak_mult_m']:.3f} phys={rec['phys_peak']} "
            f"registered_markup_hr={rec['gonrm_registered_markup_hr']} "
            f"inert={rec['gonrm_inert_on_peak']}",
            flush=True,
        )

    print(f"\nG3 — reach, {args.reach_year} winter missed cluster (fleet rebuild)", flush=True)
    st = fleet_state(args.reach_year)
    result["G3_reach"] = g3_reach(args.reach_year, st)
    r = result["G3_reach"]
    for cls, rec in sorted(
        r.get("by_class", {}).items(), key=lambda kv: -kv[1]["idle_below_gate_mw"]
    ):
        print(
            f"  {cls:20s} avail={rec['available_mw']:8.1f} gen={rec['dispatched_mw']:8.1f} "
            f"idle<gate={rec['idle_below_gate_mw']:8.1f} of which peak-rung="
            f"{rec['idle_below_gate_on_peak_rungs_mw']:7.1f}",
            flush=True,
        )
    print(
        f"  TOTAL idle<gate={r['total_idle_below_gate_mw']} peak-rung="
        f"{r['total_idle_below_gate_on_peak_rungs_mw']} "
        f"(all-class {r['G3_all_class_peak_reach_frac']:.1%}, "
        f"CT-family {r['G3_ct_family_peak_reach_frac']:.1%}; bar {G3_REACH_FRAC:.0%})",
        flush=True,
    )

    print("\nG2 — cohort census + validation", flush=True)
    cen = p27_census(args.reach_year)
    result["G2_cohort"] = g2_cohort(args.reach_year, cen, st["fleet_arrays"])
    g2 = result["G2_cohort"]
    print(
        f"  P-27 {g2['p27']['gens']} gens / {g2['p27']['installed_mw']} MW  vs  model "
        f"{g2['model']['internal_plants']} plants / {g2['model']['internal_mw']} MW",
        flush=True,
    )
    print(
        f"  cohort {g2['cohort']['gens']} gens / {g2['cohort']['mw']} MW  vs  model CT "
        f"{g2['model']['ct_family_plants']} / {g2['model']['ct_family_mw']} MW",
        flush=True,
    )
    for k in ("V1_scope", "V2_size", "V3_fingerprint"):
        print(f"  {k}: {g2[k]}", flush=True)

    print("\nG4 — rule 13 conditioning on every keeper year", flush=True)
    result["G4_conditioning"] = g4_conditioning(tuple(args.years))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
