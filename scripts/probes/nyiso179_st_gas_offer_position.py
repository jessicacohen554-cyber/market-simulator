"""nyiso-179 phase 0 — the NYISO ``ST_GAS`` offer **POSITION**.

Discharges validators V1/V2 and gates G0, G1, G2, G3, G4 of
``results/calibration/PREREG-nyiso179-st-gas-offer-position.md``, committed with
this file BEFORE either ran. **Zero solves.** Every number comes from committed
artifacts, the keeper's own P1 sidecars, and the engine called directly.

THE OBJECT. nyiso-178 closed the availability type (its G1: the envelope binds
in 0/0/4 hours of 8,760) and the offer-SHAPE type (its G3: ``NEITHER``), and
handed forward an offer **POSITION** object: a near-uniform multiplicative
over-offer in 2023 and a TOP-WEIGHTED under-offer in 2025. This probe asks what
moves that position, on the LP's own marginal-cost array.

* **V1/V2** — instrument validation, read BEFORE any gate (PREREG §2.1).
* **G0** — is ``gas_st_committed_hr_mult`` LIVE on this keeper? (brief item 1)
* **G1** — is the OFFER what governs ``ST_GAS`` dispatch? (the type test)
* **G2** — rule 19: does the ARMED oil-parity cap REACH and BIND? (brief item 3)
* **G3** — is the un-grounded ``peak`` 4.20 where the missing MW sits? (item 2)
* **G4** — what moves the offer position BETWEEN years? (the chartered object)

CONSTRUCTION NOTE, disclosed (PREREG §2.1 discipline). The LP tranche suffix
vocabulary was read from ``fleet/assembly.py`` rather than assumed: a unit id is
``f"{bin_id}_{suffix}"`` with ``bin_id = f"{group}_{zone}_p{plant_code}"``
(+ an optional ``_r{YYYYMM}`` cohort tag), and the suffix set is
``mustrun / sync / committed / commitcyc / econlo / econhi / econ / econcNN /
peak`` — every one a SINGLE token with no underscore. The band is therefore
exactly ``unit_id.rsplit("_", 1)[-1]``. An earlier draft of this file split on
``econ_low`` / ``econ_high``, which match NOTHING in the LP and would have
silently collapsed the entire economic ramp into an ``other`` bucket, hollowing
out G3. Caught by code reading before this file was committed or run.

Run: PYTHONPATH=.:src python scripts/probes/nyiso179_st_gas_offer_position.py
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO,
)
from market_sim.data.fleet.campd_bins import _DEFAULT_HR_MULT_BY_GROUP  # noqa: E402
from market_sim.data.fleet.eia860 import dual_fuel_plant_groups  # noqa: E402
from market_sim.data.fleet.legacy_bins import assemble_mc  # noqa: E402
from market_sim.data.fuel import resolve_fuel_prices  # noqa: E402
from market_sim.data.outages import ST_GAS_PEAKER_PLANTS  # noqa: E402

# Reuse nyiso-178's VALIDATED instrument rather than re-deriving it (brief).
from scripts.probes.nyiso178_offer_side_idling import (  # noqa: E402
    HOURS,
    ISO,
    KEEPER,
    KLASS,
    YEARS,
    actual_price,
    lp_fleet,
    measured_hourly,
    model_hourly,
)

OUT = REPO / "results/calibration/_nyiso179_st_gas_offer_position.json"
N178 = REPO / "results/calibration/_nyiso178_offer_side_idling.json"

# ---------------------------------------------------------------------------
# Bars — ALL fixed in the PREREG before this file ran. None is movable.
# ---------------------------------------------------------------------------
V1_TOL = 1e-6  # V1: intra-bin implied base HR must agree to this rel. spread
V2_TOL = 0.001  # V2: envelope must agree with nyiso-178 within 0.1 %

G1_R_LO, G1_R_HI = 0.70, 1.43  # G1 two-sided offer-governed band
G2_REACH_BAR = 0.50  # G2 (a) capacity share keyed dual-fuel capable
G2_BIND_BAR = 0.05  # G2 (b) share of 2025 top-decile bin-hours capped
G3_OOM_SHARE_BAR = 0.40  # G3 peak band's share of top-decile OOM MW
G3_OOM_HOURS_BAR = 0.90  # G3 peak band OOM in >= this share of those hours
G4_CARRIER_BAR = 0.60  # G4 one channel >= this share of |dITM|

DECILES = 10
#: The two ends of the between-year decomposition (PREREG §3 G4).
Y0, Y1 = 2023, 2025


@lru_cache(maxsize=8)
def px_rt(year: int) -> tuple:
    """Cached ISO-level actual RT LBMP (PREREG §2: no zonal actual exists)."""
    return tuple(actual_price(year, "rt").tolist())


def price_rt(year: int) -> np.ndarray:
    return np.asarray(px_rt(year), dtype=float)


def _cfg_obj():
    from market_sim.config.scenarios import ScenarioConfig

    raw = json.load(open(KEEPER / "run_config.json"))
    return ScenarioConfig(**raw.get("scenario_config", raw))


def band_of(unit_id: str) -> str:
    """LP tranche band = the last underscore token (see module docstring)."""
    return str(unit_id).rsplit("_", 1)[-1]


def band_family(suffix: str) -> str:
    """Coarse family so the sliced econ ramp reports as one band."""
    if suffix.startswith("econ"):
        return "econ*" if suffix not in ("econlo", "econhi") else suffix
    return suffix


def bin_of(unit_id: str) -> str:
    return str(unit_id).rsplit("_", 1)[0]


def _model_zone_price(year: int, zones: list[str]) -> dict[str, np.ndarray]:
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    out = {}
    for z in zones:
        d = s[s["zone"] == z].set_index("hour")["price"].reindex(range(HOURS))
        out[z] = d.ffill().bfill().to_numpy(dtype=float)
    return out


def _decile_idx(px: np.ndarray) -> list[np.ndarray]:
    return np.array_split(np.argsort(px), DECILES)


def st_gas_base_hr(year: int, cfg_obj) -> dict:
    """{plant_code: hr_weighted} for ST_GAS, from the bins frame itself.

    PREREG §8.1: this is the exact base heat rate ``bins_to_fleet`` reads
    (``base_hr = float(b["hr_weighted"])``, ``assembly.py:713``), so V1(b)'s
    committed multiplier is measured against the LP's own base, not a value
    back-solved from another band.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.assembly import load_or_synthesize_bins

    ic = get_iso_config(ISO)
    bins = load_or_synthesize_bins(cfg_obj.with_overrides(weather_year=year),
                                   ISO, ic, [])
    sub = bins[bins["Plant_Group"] == KLASS]
    return {int(r.Plant_Code): float(r.hr_weighted) for r in sub.itertuples()}


def build_year(year: int, cfg_obj) -> dict:
    """Return the exact LP ST_GAS offer state for one year. Zero solve."""
    from market_sim.config.iso_configs import get_iso_config

    _gens, fa = lp_fleet(year, cfg_obj)
    grp = np.asarray([str(g or "") for g in fa.plant_group])
    idx = np.nonzero(grp == KLASS)[0]
    cfg_y = cfg_obj.with_overrides(weather_year=year)

    fuel = resolve_fuel_prices(cfg_y, fa, year)
    mc = assemble_mc(fa, fuel, 0.0, 0.0, so2=(fa.so2_rate, 0.0))

    # Input-side A/B for G2(b): the SAME call with the cap disarmed. No LP.
    cfg_nodf = cfg_obj.with_overrides(weather_year=year, dual_fuel_switching=False)
    fuel_nodf = resolve_fuel_prices(cfg_nodf, fa, year)

    zones = [z.name for z in get_iso_config(ISO).zones]
    zprice = _model_zone_price(year, zones)
    zone_of = [str(zones[int(fa.zone_idx[g])]) for g in idx]
    unit_id = [str(fa.unit_ids[g]) for g in idx]

    return {
        "idx": idx,
        "pmax": fa.pmax[idx],
        "vom": fa.vom[idx],
        "hr": fa.heat_rate[idx],
        "avail": fa.availability[idx, :],
        "mc": mc[idx, :],
        "fuel": fuel[idx, :],
        "fuel_nodf": fuel_nodf[idx, :],
        "p_model": np.vstack([zprice[z] for z in zone_of]),
        "unit_id": unit_id,
        "band": np.asarray([band_of(u) for u in unit_id]),
        "zone": np.asarray(zone_of),
        "plant_code": np.asarray([int(fa.plant_code[g]) for g in idx]),
    }


# ---------------------------------------------------------------------------
# V1 / V2 — instrument validation (PREREG §2.1). Read BEFORE any gate.
# ---------------------------------------------------------------------------
#: Which registered offer-curve key each LP band's heat rate is base_hr x.
_BAND_TO_OFFER_KEY = {
    "committed": "committed",
    "econlo": "econ_low",
    "econhi": "econ_high",
    "peak": "peak",
}


def _fill_order_key(band: str) -> tuple:
    """LP fill order: mustrun -> sync -> committed -> commitcyc -> econ -> peak."""
    fixed = {"mustrun": 0, "sync": 1, "committed": 2, "commitcyc": 3,
             "econlo": 4, "econhi": 5, "peak": 9}
    if band in fixed:
        return (fixed[band], 0)
    if band.startswith("econc"):
        try:
            return (6, int(band[5:]))
        except ValueError:
            return (6, 0)
    if band.startswith("econ"):
        return (6, 0)
    return (8, 0)


def v1_band_heat_rates(st: dict, offer: dict, base_hr: dict) -> dict:
    """(a) the offer ramp must RISE; (b) attribute each bin's pricing rule.

    REPAIRED (PREREG §8.1) after the first run returned ``UNAVAILABLE`` having
    checked ZERO bins: NYISO ``ST_GAS`` carries no ``econlo``/``econhi`` band at
    all — its economic ramp is sliced by ``offer_curves._econ_curve_steps`` into
    ``econc00..econcNN`` — so a validator keyed on the two-band names matched
    nothing. (a) now walks whatever bands are PRESENT in LP fill order; (b) now
    takes the base heat rate from the bins frame's own ``hr_weighted``, the
    exact quantity ``bins_to_fleet`` reads at ``assembly.py:713``, instead of
    back-solving it from a band that does not exist. The bar is unchanged.

    * **(a) is the instrument check and CAN FAIL** — heat rate must be
      non-decreasing across the fill order, the rising-ramp contract every
      pricing route obeys. This is what breaks if §7.1's band parsing is wrong.
    * **(b) is a REPORT and cannot fail** — the committed band's realised
      multiplier against the registered class value, and the MW split across
      the three pricing routes (class curve / per-plant sheet / bypass).
    """
    per_bin: dict[str, list[tuple[tuple, str, float]]] = {}
    for i, uid in enumerate(st["unit_id"]):
        b = st["band"][i]
        per_bin.setdefault(bin_of(uid), []).append(
            (_fill_order_key(b), b, float(st["hr"][i]))
        )

    checked = violations = 0
    worst = 0.0
    example = None
    for bin_id, items in per_bin.items():
        seq = [hr for _k, _b, hr in sorted(items)]
        if len(seq) < 2:
            continue
        checked += 1
        for lo, hi in zip(seq, seq[1:]):
            if hi < lo - 1e-9:
                violations += 1
                worst = max(worst, (lo - hi) / max(lo, 1e-9))
                if example is None:
                    example = {"bin": bin_id,
                               "bands": [b for _k, b, _h in sorted(items)],
                               "heat_rates": [round(h, 4) for h in seq]}
                break

    mw_curve = mw_other = mw_bypass = 0.0
    ratios = []
    for i, uid in enumerate(st["unit_id"]):
        if st["band"][i] != "committed":
            continue
        cap = float(st["pmax"][i])
        if int(st["plant_code"][i]) in ST_GAS_PEAKER_PLANTS:
            mw_bypass += cap
            continue
        base = base_hr.get(int(st["plant_code"][i]))
        if not base:
            continue
        r = float(st["hr"][i]) / float(base)
        ratios.append(r)
        if abs(r - float(offer["committed"])) <= V1_TOL:
            mw_curve += cap
        else:
            mw_other += cap

    return {
        "a_rising_ramp": {
            "n_bins_checked": checked,
            "n_bins_violating": violations,
            "worst_relative_inversion": round(worst, 9),
            "example_violation": example,
            "verdict": "PASS" if (checked and violations == 0)
                       else ("FAIL" if checked else "UNAVAILABLE"),
        },
        "b_pricing_rule_attribution_REPORT": {
            "tolerance": V1_TOL,
            "base_hr_source": "bins frame hr_weighted (assembly.py:713)",
            "committed_mw_priced_by_class_curve": round(mw_curve, 1),
            "committed_mw_priced_elsewhere": round(mw_other, 1),
            "committed_mw_bypassed_st_gas_peaker": round(mw_bypass, 1),
            "committed_hr_mult_min_max": [
                round(float(min(ratios)), 6) if ratios else None,
                round(float(max(ratios)), 6) if ratios else None,
            ],
        },
        "verdict": "PASS" if (checked and violations == 0)
                   else ("FAIL" if checked else "UNAVAILABLE"),
    }


def v2_envelope_agreement(env_twh: dict[int, float]) -> dict:
    """Reconstructed envelope must match nyiso-178's committed number."""
    if not N178.exists():
        return {"verdict": "UNAVAILABLE", "reason": f"{N178.name} absent"}
    rec = json.load(open(N178))
    g1 = rec.get("G1", {})
    per = g1.get("per_year", g1)
    rows, worst = [], 0.0
    for y in YEARS:
        prev = per.get(str(y), per.get(y, {})) or {}
        ref = prev.get("envelope_twh")
        if ref is None:
            continue
        rel = abs(env_twh[y] - float(ref)) / max(abs(float(ref)), 1e-9)
        worst = max(worst, rel)
        rows.append({"year": y, "nyiso178_twh": round(float(ref), 4),
                     "nyiso179_twh": round(env_twh[y], 4),
                     "rel_diff": round(rel, 6)})
    return {
        "tolerance": V2_TOL,
        "per_year": rows,
        "max_rel_diff": round(worst, 6) if rows else None,
        "verdict": ("PASS" if rows and worst <= V2_TOL
                    else ("FAIL" if rows else "UNAVAILABLE")),
    }


# ---------------------------------------------------------------------------
# G0 — is gas_st_committed_hr_mult LIVE? (brief item 1)
# ---------------------------------------------------------------------------
def g0_committed_mult(st: dict, cfg_obj, offer: dict, v1: dict) -> dict:
    """Is the 1.32 ``ScenarioConfig`` scalar reachable on THIS keeper?

    STRUCTURAL, not inferred from heat rates.
    ``gas_st_committed_hr_mult`` is consumed at exactly one site,
    ``offer_curves.split_gas_tranches``, which ``bins_to_fleet`` calls ONLY from
    its non-CAMPD ``else`` limb (``assembly.py:1912``) under
    ``not use_campd_bins and config.gas_offer_curve`` — the same limb whose coal
    sibling was deleted as unreachable at ercot-188. A ``use_campd_bins`` keeper
    never enters it, so the scalar cannot price a single MW.

    The separate ``ST_GAS_PEAKER_PLANTS`` bypass (which routes a bin to the
    class-default 1.15 / the CAISO measured registry) is reported alongside,
    because it is the ONLY other way an ``ST_GAS`` committed band escapes the
    registered curve.
    """
    scalar = float(getattr(cfg_obj, "gas_st_committed_hr_mult", float("nan")))
    use_campd = bool(getattr(cfg_obj, "use_campd_bins", False))
    gas_offer_curve = bool(getattr(cfg_obj, "gas_offer_curve", False))
    legacy_path_entered = (not use_campd) and gas_offer_curve

    plants = sorted({int(p) for p in st["plant_code"]})
    bypassed = [p for p in plants if p in ST_GAS_PEAKER_PLANTS]
    mw_bypassed = (
        float(st["pmax"][np.isin(st["plant_code"], bypassed)].sum())
        if bypassed else 0.0
    )
    attrib = v1["b_pricing_rule_attribution_REPORT"]

    return {
        "scalar_gas_st_committed_hr_mult": scalar,
        "consumed_only_by": "offer_curves.split_gas_tranches",
        "call_site_gate": "assembly.py:1912 — not use_campd_bins and gas_offer_curve",
        "keeper_use_campd_bins": use_campd,
        "keeper_gas_offer_curve": gas_offer_curve,
        "legacy_path_entered": legacy_path_entered,
        "keeper_plant_level_fleet": bool(getattr(cfg_obj, "plant_level_fleet", False)),
        "gas_st_committed_hr_override": getattr(
            cfg_obj, "gas_st_committed_hr_override", None
        ),
        "registered_curve_committed": float(offer["committed"]),
        "class_default_hr_mult": float(_DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"]),
        "measured_nyiso_avg_committed_p50": 1.104,
        "registered_phys_committed": offer.get("phys_committed"),
        "n_st_gas_plants": len(plants),
        "n_bypassed_st_gas_peaker_plants": len(bypassed),
        "bypassed_mw": round(mw_bypassed, 1),
        "committed_mw_priced_by_class_curve": attrib[
            "committed_mw_priced_by_class_curve"
        ],
        "committed_mw_priced_elsewhere": attrib["committed_mw_priced_elsewhere"],
        "committed_hr_mult_min_max": attrib["committed_hr_mult_min_max"],
        "nyiso_in_measured_registry": ISO in ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO,
        "verdict": "LIVE" if legacy_path_entered else "INERT",
    }


# ---------------------------------------------------------------------------
# G1 — is the OFFER what governs dispatch? (the type test)
# ---------------------------------------------------------------------------
def g1_offer_governed(states: dict) -> dict:
    per_year = {}
    for y in YEARS:
        st = states[y]
        cap = st["pmax"][:, None] * st["avail"]
        itm = np.where(st["mc"] <= st["p_model"], cap, 0.0).sum(axis=0)
        env = cap.sum(axis=0)
        mo = model_hourly(y, KLASS)
        r = mo / np.maximum(itm, 1.0)
        top = _decile_idx(price_rt(y))[-1]
        per_year[y] = {
            "median_R": round(float(np.median(r)), 4),
            "mean_R_top_decile": round(float(r[top].mean()), 4),
            # PREREG §8.2 REPORT — the aggregate ratio, stable where the
            # mean-of-ratios blows up. The BAR is still read on the two
            # statistics above; this is reported alongside, never in place.
            "aggregate_R_all_hours_REPORT": round(
                float(mo.sum() / max(itm.sum(), 1.0)), 4
            ),
            "aggregate_R_top_decile_REPORT": round(
                float(mo[top].sum() / max(itm[top].sum(), 1.0)), 4
            ),
            "mean_itm_model_mw": round(float(itm.mean()), 1),
            "mean_model_mw": round(float(mo.mean()), 1),
            "mean_envelope_mw": round(float(env.mean()), 1),
            "mean_itm_top_decile_mw": round(float(itm[top].mean()), 1),
            "mean_model_top_decile_mw": round(float(mo[top].mean()), 1),
            "hours_itm_below_1mw": int((itm < 1.0).sum()),
        }
    ok = all(
        G1_R_LO <= per_year[y]["median_R"] <= G1_R_HI
        and G1_R_LO <= per_year[y]["mean_R_top_decile"] <= G1_R_HI
        for y in YEARS
    )
    return {
        "bar": {"R_low": G1_R_LO, "R_high": G1_R_HI},
        "per_year": per_year,
        "verdict": "OFFER-GOVERNED" if ok else "NOT-OFFER-GOVERNED",
    }


# ---------------------------------------------------------------------------
# G2 — rule 19: does the ARMED oil-parity cap REACH and BIND? (brief item 3)
# ---------------------------------------------------------------------------
def g2_dual_fuel(states: dict) -> dict:
    capable = dual_fuel_plant_groups()
    reach, binding = {}, {}
    for y in YEARS:
        st = states[y]
        keyed = np.asarray(
            [(int(p), KLASS) in capable for p in st["plant_code"]], dtype=bool
        )
        cap_total = float(st["pmax"].sum())
        cap_keyed = float(st["pmax"][keyed].sum())
        reach[y] = {
            "st_gas_lp_capacity_mw": round(cap_total, 1),
            "dual_fuel_capable_mw": round(cap_keyed, 1),
            "reach_share": round(cap_keyed / max(cap_total, 1e-9), 4),
            "n_bins": int(len(st["pmax"])),
            "n_bins_capable": int(keyed.sum()),
            "capable_plant_codes": sorted(
                {int(p) for p, k in zip(st["plant_code"], keyed) if k}
            ),
            "incapable_plant_codes": sorted(
                {int(p) for p, k in zip(st["plant_code"], keyed) if not k}
            ),
        }
        relief = st["fuel_nodf"] - st["fuel"]  # >= 0 where the cap bites
        bound = relief > 1e-9
        top = _decile_idx(price_rt(y))[-1]
        w = st["pmax"][:, None] * st["avail"]
        wt, rt_ = w[:, top], relief[:, top]
        binding[y] = {
            "share_bin_hours_capped": round(float(bound.mean()), 5),
            "share_top_decile_bin_hours_capped": round(
                float(bound[:, top].mean()), 5
            ),
            "mw_weighted_mean_relief_usd_per_mmbtu": round(
                float((relief * w).sum() / max(w.sum(), 1e-9)), 4
            ),
            "mw_weighted_mean_relief_top_decile": round(
                float((rt_ * wt).sum() / max(wt.sum(), 1e-9)), 4
            ),
            "max_relief_usd_per_mmbtu": round(float(relief.max()), 4),
            "mean_uncapped_gas_top_decile": round(
                float((st["fuel_nodf"][:, top] * wt).sum() / max(wt.sum(), 1e-9)), 4
            ),
            "mean_delivered_top_decile": round(
                float((st["fuel"][:, top] * wt).sum() / max(wt.sum(), 1e-9)), 4
            ),
        }
    r25 = reach[2025]["reach_share"]
    b25 = binding[2025]["share_top_decile_bin_hours_capped"]
    if r25 < G2_REACH_BAR:
        verdict = "WIRING GAP"
    elif b25 >= G2_BIND_BAR:
        verdict = "LINE CLOSED"
    else:
        verdict = "REACHES BUT INERT"
    return {
        "bars": {"reach": G2_REACH_BAR, "top_decile_binding": G2_BIND_BAR},
        "reach": reach,
        "binding": binding,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# G3 — is the un-grounded peak 4.20 where the missing MW sits? (brief item 2)
# ---------------------------------------------------------------------------
def g3_band_attribution(states: dict) -> dict:
    per_year = {}
    for y in YEARS:
        st = states[y]
        px = price_rt(y)
        top = _decile_idx(px)[-1]
        fam = np.asarray([band_family(b) for b in st["band"]])
        cap = st["pmax"][:, None] * st["avail"]
        itm = st["mc"] <= px[None, :]
        rows = {}
        for b in sorted(set(fam.tolist())):
            m = fam == b
            capt = cap[m][:, top]
            itmt = itm[m][:, top]
            rows[b] = {
                "capacity_mw": round(float(st["pmax"][m].sum()), 1),
                "mean_available_mw_top_decile": round(float(capt.sum(axis=0).mean()), 1),
                "mean_itm_mw_top_decile": round(
                    float(np.where(itmt, capt, 0.0).sum(axis=0).mean()), 1
                ),
                "mean_oom_mw_top_decile": round(
                    float(np.where(~itmt, capt, 0.0).sum(axis=0).mean()), 1
                ),
                "share_top_decile_hours_oom": round(float((~itmt).mean()), 4),
                "mean_mc_top_decile": round(float(st["mc"][m][:, top].mean()), 2),
            }
        tot_oom = sum(v["mean_oom_mw_top_decile"] for v in rows.values())
        per_year[y] = {
            "mean_actual_price_top_decile": round(float(px[top].mean()), 2),
            "mean_model_mw_top_decile": round(
                float(model_hourly(y, KLASS)[top].mean()), 1
            ),
            "mean_measured_mw_top_decile": round(
                float(measured_hourly(y, KLASS)[top].mean()), 1
            ),
            "total_oom_mw_top_decile": round(tot_oom, 1),
            "total_itm_at_actual_price_mw_top_decile": round(
                sum(v["mean_itm_mw_top_decile"] for v in rows.values()), 1
            ),
            "peak_share_of_oom": round(
                rows.get("peak", {}).get("mean_oom_mw_top_decile", 0.0)
                / max(tot_oom, 1e-9), 4
            ),
            "by_band": rows,
        }
    p25, p23 = per_year[2025], per_year[2023]
    peak25 = p25["by_band"].get("peak", {})
    peak23 = p23["by_band"].get("peak", {})
    implicated = (
        p25["peak_share_of_oom"] >= G3_OOM_SHARE_BAR
        and peak25.get("share_top_decile_hours_oom", 0.0) >= G3_OOM_HOURS_BAR
        and peak23.get("share_top_decile_hours_oom", 0.0) >= G3_OOM_HOURS_BAR
    )
    return {
        "bars": {"oom_share": G3_OOM_SHARE_BAR, "oom_hours": G3_OOM_HOURS_BAR},
        "per_year": per_year,
        "verdict": "PEAK-IMPLICATED" if implicated else "PEAK-EXONERATED",
    }


# ---------------------------------------------------------------------------
# G4 — what moves the offer position BETWEEN years? (the chartered object)
# ---------------------------------------------------------------------------
def g4_between_year(states: dict) -> dict:
    """Shapley-symmetric two-point decomposition of dITM_actual(2023->2025)."""
    a, b = states[Y0], states[Y1]
    # Align on the common bin set by unit id so a MEMBERSHIP change cannot
    # masquerade as a fuel or availability effect.
    ia = {u: i for i, u in enumerate(a["unit_id"])}
    ib = {u: i for i, u in enumerate(b["unit_id"])}
    common = sorted(set(ia) & set(ib))
    sa = np.asarray([ia[u] for u in common])
    sb = np.asarray([ib[u] for u in common])

    hr = {Y0: a["hr"][sa], Y1: b["hr"][sb]}
    vom = {Y0: a["vom"][sa], Y1: b["vom"][sb]}
    fuel = {Y0: a["fuel"][sa], Y1: b["fuel"][sb]}
    avail = {Y0: a["avail"][sa], Y1: b["avail"][sb]}
    pmax = {Y0: a["pmax"][sa], Y1: b["pmax"][sb]}
    price = {Y0: price_rt(Y0), Y1: price_rt(Y1)}

    # The BAND channel: heat rate and VOM are structural (band multiplier x
    # base HR) and must be constant across years. Measured, not assumed.
    band_drift = float(np.abs(hr[Y1] - hr[Y0]).max())
    vom_drift = float(np.abs(vom[Y1] - vom[Y0]).max())

    def itm(f_y: int, a_y: int, p_y: int) -> float:
        # Bands held at their Y0 (structural) values throughout, which
        # band_drift above certifies is a no-op.
        mc = hr[Y0][:, None] * fuel[f_y] + vom[Y0][:, None]
        cap = pmax[a_y][:, None] * avail[a_y]
        return float(np.where(mc <= price[p_y][None, :], cap, 0.0).sum(axis=0).mean())

    base = itm(Y0, Y0, Y0)
    full = itm(Y1, Y1, Y1)
    d_total = full - base

    orders = [("FUEL", "PRICE", "AVAIL"), ("AVAIL", "PRICE", "FUEL")]
    contrib: dict[str, list[float]] = {"FUEL": [], "PRICE": [], "AVAIL": []}
    for order in orders:
        cur = {"FUEL": Y0, "PRICE": Y0, "AVAIL": Y0}
        prev = itm(cur["FUEL"], cur["AVAIL"], cur["PRICE"])
        for ch in order:
            cur[ch] = Y1
            now = itm(cur["FUEL"], cur["AVAIL"], cur["PRICE"])
            contrib[ch].append(now - prev)
            prev = now
    mws = {ch: round(float(np.mean(v)), 1) for ch, v in contrib.items()}
    shares = {
        ch: round(float(np.mean(v)) / max(abs(d_total), 1e-9), 4)
        for ch, v in contrib.items()
    }
    top_ch = max(shares, key=lambda c: abs(shares[c]))
    return {
        "bar": G4_CARRIER_BAR,
        "n_common_bins": len(common),
        "n_bins_only_2023": int(len(ia) - len(common)),
        "n_bins_only_2025": int(len(ib) - len(common)),
        "band_heat_rate_max_drift": round(band_drift, 9),
        "band_vom_max_drift": round(vom_drift, 9),
        "itm_actual_mean_mw_2023": round(base, 1),
        "itm_actual_mean_mw_2025": round(full, 1),
        "delta_itm_actual_mw": round(d_total, 1),
        "channel_contribution_mw": mws,
        "channel_share_of_abs_delta": shares,
        "carrier": top_ch,
        "verdict": ("CARRIER IDENTIFIED"
                    if abs(shares[top_ch]) >= G4_CARRIER_BAR else "DIFFUSE"),
        # PREREG §8.3 — the shares sum to 1.000 by construction but are NOT
        # fractions when the net delta is small against the channel magnitudes.
        "share_denominator_is_small": bool(
            abs(d_total) < 0.5 * max(abs(v) for v in mws.values())
        ),
        "shares_interpretable_as_fractions": bool(
            abs(d_total) >= 0.5 * max(abs(v) for v in mws.values())
        ),
    }


def main() -> None:
    cfg_obj = _cfg_obj()
    offer = dict(cfg_obj.offer_curve_by_group["ST_GAS"])

    states = {y: build_year(y, cfg_obj) for y in YEARS}
    base_hr = st_gas_base_hr(2023, cfg_obj)
    env_twh = {
        y: float((states[y]["pmax"][:, None] * states[y]["avail"]).sum()) / 1e6
        for y in YEARS
    }

    v1 = v1_band_heat_rates(states[2023], offer, base_hr)
    v2 = v2_envelope_agreement(env_twh)

    rec = {
        "session": "nyiso-179",
        "prereg": "results/calibration/PREREG-nyiso179-st-gas-offer-position.md",
        "keeper": "2026-09-02-nyiso-177-vintage-matched",
        "bundle": str(KEEPER.relative_to(REPO)),
        "solves": 0,
        "registered_offer_curve_ST_GAS": offer,
        "envelope_twh": {y: round(v, 4) for y, v in env_twh.items()},
        "V1_band_heat_rates": v1,
        "V2_envelope_agreement": v2,
    }

    if v1["verdict"] == "FAIL" or v2["verdict"] == "FAIL":
        rec["GATES"] = "NOT READ — instrument validation failed (PREREG §2.1)"
        OUT.write_text(json.dumps(rec, indent=2, default=str))
        print(json.dumps({"V1": v1, "V2": v2}, indent=2, default=str))
        print("\nINSTRUMENT VALIDATION FAILED — gates not read (PREREG §2.1).")
        return

    rec["G0"] = g0_committed_mult(states[2023], cfg_obj, offer, v1)
    rec["G1"] = g1_offer_governed(states)
    rec["G2"] = g2_dual_fuel(states)
    rec["G3"] = g3_band_attribution(states)
    rec["G4"] = g4_between_year(states)

    OUT.write_text(json.dumps(rec, indent=2, default=str))

    ramp = v1["a_rising_ramp"]
    print(f"V1 {v1['verdict']}  rising-ramp bins {ramp['n_bins_checked']} "
          f"violating {ramp['n_bins_violating']}")
    print(f"   pricing rule: {v1['b_pricing_rule_attribution_REPORT']}")
    print(f"V2 {v2['verdict']}  max rel diff {v2.get('max_rel_diff')}")
    g0 = rec["G0"]
    print(f"\nG0 {g0['verdict']}  legacy path entered "
          f"{g0['legacy_path_entered']}  bypassed plants "
          f"{g0['n_bypassed_st_gas_peaker_plants']}/{g0['n_st_gas_plants']}  "
          f"committed mult range {g0['committed_hr_mult_min_max']}")
    print(f"\nG1 {rec['G1']['verdict']}")
    for y in YEARS:
        p = rec["G1"]["per_year"][y]
        print(f"  {y}  median R {p['median_R']:.3f}  top-decile R "
              f"{p['mean_R_top_decile']:.3f}  [agg all {p['aggregate_R_all_hours_REPORT']:.3f} "
              f"top {p['aggregate_R_top_decile_REPORT']:.3f}]  ITM {p['mean_itm_model_mw']:.0f} "
              f" model {p['mean_model_mw']:.0f}  env {p['mean_envelope_mw']:.0f}"
              f"  | top-dec ITM {p['mean_itm_top_decile_mw']:.0f} model "
              f"{p['mean_model_top_decile_mw']:.0f}")
    print(f"\nG2 {rec['G2']['verdict']}")
    for y in YEARS:
        r, bd = rec["G2"]["reach"][y], rec["G2"]["binding"][y]
        print(f"  {y}  reach {r['reach_share']:.3f} "
              f"({r['dual_fuel_capable_mw']:.0f}/{r['st_gas_lp_capacity_mw']:.0f} MW)"
              f"  capped {bd['share_bin_hours_capped']:.4f}  top-dec "
              f"{bd['share_top_decile_bin_hours_capped']:.4f}  relief "
              f"{bd['mw_weighted_mean_relief_top_decile']:.3f} $/MMBtu"
              f"  gas {bd['mean_uncapped_gas_top_decile']:.2f} -> "
              f"{bd['mean_delivered_top_decile']:.2f}")
    print(f"\nG3 {rec['G3']['verdict']}")
    for y in YEARS:
        p = rec["G3"]["per_year"][y]
        print(f"  {y}  price {p['mean_actual_price_top_decile']:.1f}  model "
              f"{p['mean_model_mw_top_decile']:.0f}  measured "
              f"{p['mean_measured_mw_top_decile']:.0f}  ITM@actual "
              f"{p['total_itm_at_actual_price_mw_top_decile']:.0f}  OOM "
              f"{p['total_oom_mw_top_decile']:.0f}  peak-share "
              f"{p['peak_share_of_oom']:.3f}")
        for bnd, v in p["by_band"].items():
            print(f"      {bnd:<10} cap {v['capacity_mw']:>7.0f}  ITM "
                  f"{v['mean_itm_mw_top_decile']:>7.0f}  OOM "
                  f"{v['mean_oom_mw_top_decile']:>7.0f}  oom-hrs "
                  f"{v['share_top_decile_hours_oom']:.3f}  mc "
                  f"{v['mean_mc_top_decile']:.1f}")
    g4 = rec["G4"]
    print(f"\nG4 {g4['verdict']}  carrier {g4['carrier']}  "
          f"band drift hr {g4['band_heat_rate_max_drift']} "
          f"vom {g4['band_vom_max_drift']}")
    print(f"  ITM_actual {g4['itm_actual_mean_mw_2023']:.0f} -> "
          f"{g4['itm_actual_mean_mw_2025']:.0f} MW "
          f"(d {g4['delta_itm_actual_mw']:.0f})")
    print(f"  contributions {g4['channel_contribution_mw']}")
    print(f"  shares        {g4['channel_share_of_abs_delta']}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
