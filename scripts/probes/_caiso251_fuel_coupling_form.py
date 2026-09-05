"""caiso-251 PHASE 0 — the CAISO gas-offer FUEL-COUPLING FORM. ZERO LP.

Pre-registered in ``PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md``
(pushed to ``origin`` before this file was written and before any cell of the
object was measured). **NOTHING ARMED HERE — this stage builds no solve.**

The object (PRECOMMIT §0). The keeper arms ``gas_offer_net_revenue_margin``
(anchor $4.7964/MMBtu), which prices every CAMPD gas tranche carrying a
measured physical basis as

    offer = phys * HR_base * fuel(t)  +  (mult - phys) * HR_base * anchor

so the above-physical markup is a **fuel-INVARIANT $/MWh margin** (1,285
tranches, median $14.37/MWh on the keeper's 2025 solve log). That form's
identification is **NEISO's** 2022 holdout rotation. CAISO's OWN OASIS record
refutes fuel-invariance for CAISO (caiso-242 §3.5: the measured band multiplier
is FLAT across a 1.93x fuel swing, 21.3x flatter than the armed decomposition
requires), and caiso-229 §5 measured the consequence — the model CC floor
couples to the CA citygate at Theil-Sen **2.18 / 2.18 / 4.34 MMBtu/MWh** against
CAISO's **MEASURED DAM body coupling of 6.7-7.4**: the model is **UNDER-coupled
to fuel**, "because the affine ... form is ALREADY armed".

This stage measures the single-flag delta's footprint on the OFFER SURFACE
only, and runs **G-COUPLE**, the load-bearing structural gate whose failure
spends NO solve (PRECOMMIT §3.1).

Instrument: two on-recipe ``fleet_only`` rebuilds through the sanctioned path
(``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``, the caiso-248
repair) differing in ONE kwarg, ``gas_offer_margin``. Never by parameter name
(caiso-243 §10.4 / caiso-244 §7.7, CI-enforced).

Writes ``results/calibration/_caiso251_fuel_coupling_form.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso251_fuel_coupling_form.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "_caiso247_residual_regime_anatomy",
    REPO / "scripts/probes/_caiso247_residual_regime_anatomy.py",
)
C247 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C247)

BUNDLE = C247.BUNDLE
KEEPER_RUN_ID = C247.KEEPER_RUN_ID
OUT = REPO / "results/calibration/_caiso251_fuel_coupling_form.json"
YEARS = C247.YEARS
HOURS = C247.HOURS
CA_ZONES = C247.CA_ZONES
GAS_GROUPS = C247.GAS_GROUPS

#: rule 22 [R-HOLDOUT], fail-closed.
TRAINING_YEARS = frozenset({2023, 2024, 2025})

#: the keeper's resolved identification anchor, read from its own run_config.
ANCHOR = float(
    json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"][
        "gas_offer_margin_anchor"
    ]
)

#: G-COUPLE band (PRECOMMIT §1.2), fixed a priori and never re-picked.
COUPLE_BAND = (6.0, 8.0)
#: CAISO's MEASURED DAM body coupling (derive_caiso_offer_surface / caiso-153).
MEASURED_BODY_COUPLING = (6.7, 7.4)
#: caiso-229 §5's measured ARMED coupling, quoted not re-derived.
CAISO229_ARMED_COUPLING = {2023: 2.18, 2024: 2.18, 2025: 4.34}
#: the keeper's own 2025 solve-log compression count (G-FOOTPRINT).
KEEPER_COMPRESSED_TRANCHES_2025 = 1285

DAY_OF_HOUR = np.arange(HOURS) // 24


def rebuild(year: int, armed: bool) -> dict:
    """One on-recipe ``fleet_only`` rebuild; ``armed`` is the ONLY difference.

    The single-flag delta is applied to the SANCTIONED kwargs dict
    (``run_year_kwargs`` + ``derived_run_year_inputs``), never by rebuilding the
    recipe from parameter names.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.caiso import split_caiso_import_node_per_hub
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from run_calibration_full import _tranche_band
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(BUNDLE, year))
    if not armed:
        kwargs["gas_offer_margin"] = False  # THE single-flag delta
    clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year,
            meta["iso"],
            HOURS,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    gens = st.get("fleet") or []
    zone_names = list(
        split_caiso_import_node_per_hub(get_iso_config("CAISO")).zone_names
    )
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    fuel = np.asarray(st["fuel_prices"], dtype=float)
    if fuel.ndim == 1:
        fuel = np.tile(fuel[:, None], (1, HOURS))
    return {
        "mc": mc,
        "fuel": fuel,
        "avail": np.asarray(fa.availability, dtype=float),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "heat_rate": np.asarray(fa.heat_rate, dtype=float),
        "zone": np.array([zone_names[i] for i in fa.zone_idx], dtype=object),
        "group": np.array(
            [
                str(getattr(g, "plant_group", "") or "")
                or f"fuel:{getattr(g, 'fuel_type', 'unknown')}"
                for g in gens
            ],
            dtype=object,
        ),
        "band": np.array(
            [_tranche_band(u) for u in fa.unit_ids], dtype=object
        ),
        "log": buf.getvalue(),
    }


def band_family(label: str) -> str:
    """Collapse the LP tranche suffix onto the offer-curve BAND it belongs to.

    The suffix itself comes from the SHIPPED authority
    (``run_calibration_full._tranche_band``, the same closed vocabulary the
    ``class_band_hourly`` sidecar is written with) — never from a local
    heuristic. The families are the offer curve's own bands:
    ``mustrun`` / ``committed`` (with its ``commitcyc`` / ``sync*`` cycling and
    synchronised limbs) / ``econ`` (``econ``, ``econlo``, ``econhi``,
    ``econc00..``) / ``peak`` (``peak``, ``peak2..``).
    """
    s = str(label)
    if s.startswith("mustrun"):
        return "mustrun"
    if s.startswith(("committed", "commitcyc", "sync")):
        return "committed"
    if s.startswith("peak"):
        return "peak"
    if s.startswith("econ"):
        return "econ"
    return s or "unlabelled"


def g_ident(a: dict, d: dict) -> dict:
    """The delta IS ``(mult - phys) * HR_base * (fuel - anchor)``, exactly.

    ``(mult - phys) * HR_base`` is a per-tranche CONSTANT, so
    ``delta[g,t] / (fuel[g,t] - anchor)`` must not vary with ``t``. That is a
    parameter-free identity test: it needs no access to the phys_* keys.
    """
    delta = d["mc"] - a["mc"]
    touched = np.abs(delta).max(axis=1) > 1e-9
    den = a["fuel"] - ANCHOR
    ok = np.abs(den) > 1e-6
    worst = 0.0
    n_tested = 0
    kvals = np.full(delta.shape[0], np.nan)
    for g in np.flatnonzero(touched):
        sel = ok[g]
        if sel.sum() < 2:
            continue
        k = delta[g, sel] / den[g, sel]
        kvals[g] = float(np.median(k))
        worst = max(worst, float(np.max(np.abs(k - np.median(k)))))
        n_tested += 1
    return {
        "n_tranches_touched": int(touched.sum()),
        "n_tranches_identity_tested": n_tested,
        "max_within_tranche_spread_of_k_mmbtu_per_mwh": round(worst, 12),
        "anchor_usd_per_mmbtu": ANCHOR,
        "pass": bool(worst <= 1e-6),
    }, touched, kvals


def footprint(a: dict, d: dict, touched: np.ndarray, year: int) -> dict:
    grp = a["group"]
    non_gas = sorted({str(g) for g in grp[touched] if str(g) not in GAS_GROUPS})
    by_group = {}
    for gname in sorted({str(x) for x in grp[touched]}):
        sel = touched & (grp == gname)
        by_group[gname] = {
            "n_tranches": int(sel.sum()),
            "capacity_mw": round(float(a["pmax"][sel].sum()), 1),
        }
    return {
        "n_tranches_touched": int(touched.sum()),
        "keeper_log_count_2025": KEEPER_COMPRESSED_TRANCHES_2025,
        "non_gas_groups_touched": non_gas,
        "by_group": by_group,
        "pass": bool(
            not non_gas
            and (year != 2025 or int(touched.sum()) == KEEPER_COMPRESSED_TRANCHES_2025)
        ),
    }


def deltas(a: dict, d: dict, touched: np.ndarray, year: int) -> dict:
    """Offer delta by class x band, on THREE weightings (PRECOMMIT §2)."""
    delta = d["mc"] - a["mc"]
    avail = a["avail"] > 0.01
    dom = np.isin(a["zone"], list(CA_ZONES))
    bands = np.array([band_family(b) for b in a["band"]], dtype=object)

    cb = pd.read_parquet(BUNDLE / "hourly" / f"class_band_hourly_{year}.parquet")
    cb = cb[cb["pass"] == "P1"]
    disp = {
        (str(k), band_family(str(b))): g["mw"].sum()
        for (k, b), g in cb.groupby(["klass", "band"], observed=True)
    }
    agg_disp: dict[tuple[str, str], float] = {}
    for key, v in disp.items():
        agg_disp[key] = agg_disp.get(key, 0.0) + float(v)

    out: dict[str, dict] = {}
    for gname in GAS_GROUPS:
        for bname in ("committed", "econ", "peak"):
            sel = touched & dom & (a["group"] == gname) & (bands == bname)
            if not sel.any():
                continue
            dsel = np.where(avail[sel], delta[sel], np.nan)
            cap = a["pmax"][sel]
            fin = np.isfinite(dsel)
            if not fin.any():
                # every tranche of this class-band is unavailable all year
                out[f"{gname}:{bname}"] = {
                    "n_tranches": int(sel.sum()),
                    "capacity_mw": round(float(cap.sum()), 1),
                    "delta_unweighted_usd_per_mwh": None,
                    "delta_capacity_weighted_usd_per_mwh": None,
                    "model_dispatch_twh": round(agg_disp.get((gname, bname), 0.0) / 1e6, 4),
                    "note": "no available hour in the year",
                }
                continue
            unweighted = float(np.nanmean(dsel))
            capw = float(
                np.nansum(dsel * cap[:, None]) / np.nansum(fin * cap[:, None])
            )
            out[f"{gname}:{bname}"] = {
                "n_tranches": int(sel.sum()),
                "capacity_mw": round(float(cap.sum()), 1),
                "delta_unweighted_usd_per_mwh": round(unweighted, 4),
                "delta_capacity_weighted_usd_per_mwh": round(capw, 4),
                "model_dispatch_twh": round(agg_disp.get((gname, bname), 0.0) / 1e6, 4),
            }
    return out


def couple(a: dict, d: dict, year: int) -> dict:
    """G-COUPLE — Theil-Sen slope of the class's cheapest available offer on
    its own delivered gas, per day, ARMED vs DISARMED.

    Estimator and regressor are BOTH the repo's own (caiso-153: Theil-Sen, not
    OLS, because the Jan-2023 citygate tail levers an OLS slope; the delivered
    series is the model's own ``fuel_prices`` — the CA-composite citygate with
    the armed hub overlay, i.e. the same series the derive regressed on).
    Neither is chosen here.
    """
    avail = a["avail"] > 0.01
    dom = np.isin(a["zone"], list(CA_ZONES))
    bands = np.array([band_family(b) for b in a["band"]], dtype=object)
    res: dict[str, dict] = {}
    for gname in ("CC_REGULAR", "CT_PEAKER"):
        for stat, sel in (
            ("econ", dom & (a["group"] == gname) & (bands == "econ")),
            ("floor_any_band", dom & (a["group"] == gname)),
        ):
            if not sel.any():
                continue
            row = {}
            for tag, fl in (("armed", a), ("disarmed", d)):
                mc = np.where(avail[sel], fl["mc"][sel], np.nan)
                with np.errstate(all="ignore"):
                    cheapest = np.nanmin(mc, axis=0)
                gas = np.nanmedian(np.where(avail[sel], a["fuel"][sel], np.nan), axis=0)
                dfr = pd.DataFrame(
                    {"d": DAY_OF_HOUR, "p": cheapest, "g": gas}
                ).dropna()
                daily = dfr.groupby("d").median()
                if len(daily) < 30:
                    continue
                sl, ic, lo, hi = theilslopes(
                    daily["p"].to_numpy(), daily["g"].to_numpy(), 0.95
                )
                row[tag] = {
                    "theilsen_slope_mmbtu_per_mwh": round(float(sl), 3),
                    "ci95": [round(float(lo), 3), round(float(hi), 3)],
                    "intercept_usd_per_mwh": round(float(ic), 3),
                    "n_days": int(len(daily)),
                }
            res[f"{gname}:{stat}"] = row
    # POST-REGISTRATION characterisation (not a scored prediction): each class's
    # coupling as a RATIO to its own measured base heat rate. CAISO's measured
    # DAM body coupling is 0.9-1.0 x base_hr (derive_caiso_offer_surface), and
    # the base HRs are CC 7.442 / CT 10.862 MMBtu/MWh (the same artifact).
    BASE_HR = {"CC_REGULAR": 7.442, "CT_PEAKER": 10.862}
    ratios: dict[str, dict] = {}
    for gname, bhr in BASE_HR.items():
        cell = res.get(f"{gname}:econ", {})
        ratios[gname] = {
            "base_hr_mmbtu_per_mwh": bhr,
            "armed_over_base_hr": (
                round(cell["armed"]["theilsen_slope_mmbtu_per_mwh"] / bhr, 3)
                if "armed" in cell
                else None
            ),
            "disarmed_over_base_hr": (
                round(cell["disarmed"]["theilsen_slope_mmbtu_per_mwh"] / bhr, 3)
                if "disarmed" in cell
                else None
            ),
        }
    econ_cc = res.get("CC_REGULAR:econ", {}).get("disarmed", {})
    slope = econ_cc.get("theilsen_slope_mmbtu_per_mwh")
    return {
        "by_class_stat": res,
        "coupling_over_own_base_hr_POST_REGISTRATION": ratios,
        "gate_statistic": "CC_REGULAR:econ disarmed Theil-Sen slope",
        "gate_band": list(COUPLE_BAND),
        "measured_dam_body_coupling": list(MEASURED_BODY_COUPLING),
        "caiso229_armed_reference": CAISO229_ARMED_COUPLING[year],
        "value": slope,
        "pass": bool(
            slope is not None and COUPLE_BAND[0] <= slope <= COUPLE_BAND[1]
        ),
    }


def analyse(year: int) -> dict:
    if year not in TRAINING_YEARS:
        raise SystemExit(f"rule 22 [R-HOLDOUT]: {year} is outside 2023-2025")
    a = rebuild(year, armed=True)
    d = rebuild(year, armed=False)
    ident, touched, kvals = g_ident(a, d)
    return {
        "G_IDENT": ident,
        "G_FOOTPRINT": footprint(a, d, touched, year),
        "G_COUPLE": couple(a, d, year),
        "G_HOLDOUT": {"year": year, "pass": year in TRAINING_YEARS},
        "offer_deltas": deltas(a, d, touched, year),
        "delta_sign_census": {
            "share_of_gas_tranche_hours_delta_positive": round(
                float(
                    (
                        (d["mc"] - a["mc"])[touched] > 1e-9
                    ).mean()
                ),
                4,
            ),
            "share_of_hours_any_touched_tranche_positive": round(
                float((((d["mc"] - a["mc"])[touched] > 1e-9).any(axis=0)).mean()), 4
            ),
            "delivered_gas_median_usd_per_mmbtu": round(
                float(np.nanmedian(a["fuel"][touched])), 4
            ),
            "hours_share_gas_above_anchor": round(
                float((np.nanmedian(a["fuel"][touched], axis=0) > ANCHOR).mean()), 4
            ),
        },
        "implied_markup_hr_mmbtu_per_mwh": {
            "median": round(float(np.nanmedian(kvals[touched])), 4),
            "p90": round(float(np.nanpercentile(kvals[touched], 90)), 4),
            "max": round(float(np.nanmax(kvals[touched])), 4),
        },
    }


def main() -> None:
    out = {
        "_provenance": {
            "session": "caiso-251 phase 0 (gas-offer fuel-coupling FORM, ZERO LP)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": KEEPER_RUN_ID,
            "precommit": "PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md",
            "delta": "single kwarg gas_offer_margin True -> False on the sanctioned recipe",
            "anchor_usd_per_mmbtu": ANCHOR,
            "note": "NOTHING ARMED, NO SOLVE at this stage.",
        },
        "years": {},
    }
    for y in YEARS:
        r = analyse(y)
        out["years"][y] = r
        print(f"\n===== {y} =====")
        print(f"  G-IDENT {r['G_IDENT']['pass']} {r['G_IDENT']}")
        print(f"  G-FOOTPRINT {r['G_FOOTPRINT']['pass']} touched {r['G_FOOTPRINT']['n_tranches_touched']} non-gas {r['G_FOOTPRINT']['non_gas_groups_touched']}")
        print(f"     by group: { {k: v['n_tranches'] for k, v in r['G_FOOTPRINT']['by_group'].items()} }")
        print(f"  G-COUPLE {r['G_COUPLE']['pass']} value {r['G_COUPLE']['value']} band {r['G_COUPLE']['gate_band']} (caiso-229 armed ref {r['G_COUPLE']['caiso229_armed_reference']})")
        for k, v in r["G_COUPLE"]["by_class_stat"].items():
            print(f"     {k:26s} armed {v.get('armed',{}).get('theilsen_slope_mmbtu_per_mwh')} -> disarmed {v.get('disarmed',{}).get('theilsen_slope_mmbtu_per_mwh')}")
        print("  offer deltas ($/MWh, capacity-weighted):")
        for k, v in r["offer_deltas"].items():
            fmt = lambda x: "     n/a" if x is None else f"{x:8.3f}"  # noqa: E731
            print(
                f"     {k:22s} n {v['n_tranches']:4d} cap {v['capacity_mw']:9.1f} "
                f"capw {fmt(v['delta_capacity_weighted_usd_per_mwh'])} "
                f"unw {fmt(v['delta_unweighted_usd_per_mwh'])} "
                f"disp {v['model_dispatch_twh']:7.3f} TWh"
            )
        print("  sign census:", r["delta_sign_census"])
        print("  implied (mult-phys)*HR:", r["implied_markup_hr_mmbtu_per_mwh"])
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
