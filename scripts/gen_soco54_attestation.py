"""Write the SOCO-54 calibration attestation (schema ``calibration-attestation/v1``).

Lane SOCO-54 armed exactly ONE mechanism — ``gas_plant_monthly_fuel_pricing``
turned **OFF** — as a rule 1 ``[R-STRUCT]`` / rule 14 ``[R-ACCURATE]`` input-basis
repair. The field predates this lane by years and ships ``False`` by default; SOCO
inherited it ON. This lane wrote NO ``ScenarioConfig`` field and added NO free
parameter.

**THE CLAIM, stated once here and machine-checked below.** A dispatch offer is a
MARGINAL cost. The EIA-923 Schedule-2 print is an AVERAGE DELIVERED CONTRACT cost
— demand charges, reserved transport and a negotiated multiplier amortized over
the month's takes. At SOCO the two differ by enough to invert the merit order:
the over-dispatched merchant turbines price at $2.06-2.40/MMBtu against SOCO's own
gas steam at $2.78-3.76 on the SAME 10-12 MMBtu/MWh machines, and seven plants
carry ONE common monthly shape times a plant-constant multiplier (ratio CV
<= 0.0008) spanning x1.0000 to x1.8279. Hartwell's print sits BELOW Henry Hub in
eleven of twelve months of 2023, which no delivered gas can be, and the model
burns 4x-160x the gas these plants actually procured at the price the procurement
established. With the field off, every SOCO gas unit prices on the measured
realized Henry Hub level plus SOCO's OWN measured EIA-923 delivered-gas basis
(``GAS_BASIS_DIFFERENTIAL["SOCO"] = 0.64``, SOCO-20) — **measured to measured**,
re-aggregated to the grain at which a marginal dispatch decision is made, which
is rule 14's misalignment clause verbatim. The reasoning is MISO-224's, DERIVED
HERE FROM SOCO'S OWN DATA and never transferred (rules 25 / 28(d)); MISO's own
applier is MISO-scoped by hard error and is not touched.

See ``PRECOMMIT-soco-54-2026-09-20.md`` §§1-8 and
``ADDENDUM-soco54-the-fallback-basis-2026-09-20.md``.

The four governance assertions are asserted by the LANE. Every one is a factual
claim about this bundle and each is machine-verified against its own
``run_config.json`` by :func:`_verify`, which raises rather than writing a false
assertion. ``owner_attestation`` records honestly that the owner has NOT attested
this run in session.

NO ``authorized_price_tuning`` KEY IS WRITTEN. ``calibration_verdict.py`` validates
any present value as a STRUCTURED rule-1 declaration, so prose there fails C6. The
declared-NONE statement lives in ``authorized_price_tuning_declared`` prose, which
is the SOCO-53/53c/53d/53e/53f/53g convention.

Run: ``python scripts/gen_soco54_attestation.py``
"""

from __future__ import annotations

import json
from pathlib import Path

BUNDLE = Path("results/calibration/soco54_marginal_gas")

#: The four price-tuning bands rule 1 [R-STRUCT]'s carve-out names. The other
#: offer_curve_by_group keys (econ_low_share, pct_peaking) are STRUCTURAL shares
#: the carve-out EXCLUDES and are not 1.0 on any ISO.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")

#: SOCO's keeper recipe (2026-09-20-soco53f-measured-coal-hr), carried forward
#: unchanged. ``gas_plant_monthly_fuel_pricing`` is this lane's single delta and
#: is asserted separately, to False.
KEEPER_RECIPE = (
    "measured_ct_heat_rates",
    "egrid_family_heat_rates",
    "measured_st_heat_rates",
    "soco_gas_st_campaign_commitment",
    "measured_coal_heat_rates",
)


def _verify(sc: dict) -> None:
    """Raise unless every governance assertion is true of this bundle."""
    oc = sc.get("offer_curve_by_group") or {}
    if not oc:
        raise SystemExit("offer_curve_by_group absent — cannot verify the bands")
    for band in PRICE_TUNING_BANDS:
        vals = {oc[g][band] for g in oc if band in oc[g]}
        if vals != {1.0}:
            raise SystemExit(f"band {band} is not the identity: {sorted(vals)}")
    if sc.get("offer_curve_overrides") or sc.get("offer_curve_deltas"):
        raise SystemExit("offer-curve overrides/deltas present")
    if sc.get("offer_curve_smoothing") or sc.get("curve_smoothing"):
        raise SystemExit("offer-curve smoothing set")
    if sc.get("outage_source") != "historic":
        raise SystemExit(f"outage_source not exogenous: {sc.get('outage_source')}")

    # --- the single delta, asserted to the side of the A/B this lane solved
    if sc.get("gas_plant_monthly_fuel_pricing"):
        raise SystemExit(
            "gas_plant_monthly_fuel_pricing is ON — this bundle is the CONTROL, "
            "not the SOCO-54 arm"
        )
    # `--set` routes this field through the generic prb_overrides channel, which
    # meta.json records as a coal_prb_sigmoid_overrides diff and audit_keepers
    # E11 flags. Benign (PRECOMMIT-soco-54 §7) — but the RESOLVED value must stay
    # null, or the override bag leaked into the PRB sigmoid registry for real.
    if sc.get("coal_prb_sigmoid_overrides") not in (None, {}):
        raise SystemExit(
            "resolved coal_prb_sigmoid_overrides is "
            f"{sc.get('coal_prb_sigmoid_overrides')!r}, expected null"
        )
    # The COAL print path is NOT this lane's object and must be untouched, or the
    # arm is not the single gas-side delta it claims to be (rule 19).
    if not sc.get("coal_plant_monthly_pricing"):
        raise SystemExit(
            "coal_plant_monthly_pricing is OFF — this lane moves the GAS print "
            "path only, and the coal path must be carried forward unchanged"
        )
    if sc.get("coal_prb_proxy_own_iso"):
        raise SystemExit(
            "coal_prb_proxy_own_iso is armed — that is SOCO-53g's open candidate, "
            "not this lane's recipe"
        )
    for name in KEEPER_RECIPE:
        if not sc.get(name):
            raise SystemExit(
                f"{name} is not armed — the keeper's recipe is not carried"
            )
    # ...and nothing ELSE from the upstream lanes the G-DRIFT audit classified
    # INERT may be on, or that audit does not describe this run.
    for name in (
        "mid_vintage_exit_carry",
        "benchmark_membership_vintage_union",
        "nyiso_ct_peaker_committed_measured",
        "caiso_citygate_blackout_bridge",
        "miso_gas_marginal_commodity_pricing",
        "gas_hub_basis_overlay",
        "gas_electric_power_monthly_level",
        "gas_monthly_actuals",
    ):
        if sc.get(name):
            raise SystemExit(f"{name} is armed — not this lane's recipe")


def _retag(att: dict, sc: dict) -> None:
    """Re-tag the two offer-curve DOF entries, as SOCO-40..53g did.

    ``build_dof_ledger.py`` tags ``offer_curve_by_group`` and
    ``offer_curve_smoothing`` ``residual`` by default, because on every other
    ISO they ARE the rule-1 price-tuning surface. On SOCO they cannot be: the
    identity 1.0 on all four bands is not a tuned value, and there is no price
    residual in existence to have tuned it against. The re-tag is therefore a
    statement about THIS bundle, and it is re-verified by execution here rather
    than inherited — :func:`_verify` has already raised if any band is off the
    identity or any override, delta or smoothing is set.
    """
    fp = att.get("free_parameters")
    if not fp:
        raise SystemExit(
            "free_parameters absent — run "
            "`PYTHONPATH=src python3 scripts/build_dof_ledger.py --iso SOCO "
            f"{BUNDLE}` first"
        )
    oc = sc.get("offer_curve_by_group") or {}
    bands = {
        band: sorted({oc[g][band] for g in oc if band in oc[g]})
        for band in PRICE_TUNING_BANDS
    }
    for entry in fp["entries"]:
        if entry["name"] == "offer_curve_by_group":
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                "All four price-tuning bands (committed / econ_low / econ_high / "
                f"peak) are at the identity 1.0 on all {len(oc)} groups — "
                "machine-verified by gen_soco54_attestation._verify, which raises "
                f"otherwise: the distinct values per band are {bands}. "
                "offer_curve_overrides and offer_curve_deltas are null. The two "
                "non-identity keys, econ_low_share and pct_peaking, are NOT the "
                "authorized channel — rule 1's carve-out excludes structural shares "
                "— and arrive verbatim from the ISO-agnostic GENERIC_BASE_OFFER_CURVE. "
                "There is no soco.py delta module, so rule 25 [R-ISO-SCOPE] holds by "
                "construction."
            )
        elif entry["name"] == "offer_curve_smoothing":
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                "Unset on this run — both offer_curve_smoothing and curve_smoothing "
                "are null (machine-verified). Nothing was tuned because nothing was "
                "set."
            )
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    fp["retag_note"] = (
        "SOCO-54 re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40/53/53c/53d/53e/53f/53g used and "
        "re-verified here by execution. n_entries 3 / n_residual 1, UNCHANGED from "
        "the keeper: this lane added NO free parameter, and no ScenarioConfig field "
        "either — gas_plant_monthly_fuel_pricing predates this lane by years, ships "
        "bool = False as its DECLARED DEFAULT, and this lane returns SOCO to that "
        "default, so no cache key moves at any default. "
        "IT IS A ZERO-DOF SELECTION, NOT A VALUE: the flag chooses WHICH measured "
        "aggregation of the SAME EIA-923 Schedule-2 receipts prices a gas unit — the "
        "plant's own monthly contract print, or the footprint-wide quantity-weighted "
        "delivered basis over Henry Hub (GAS_BASIS_DIFFERENTIAL['SOCO'] = 0.64, "
        "registered by SOCO-20 on 2026-09-14 from those same receipts). Nothing is "
        "fitted, scaled, offset or swept, and there is no price residual in existence "
        "it could have been fitted to. DECLARED AGAINST THIS ENTRY because it cuts "
        "against the lane: that basis constant is the 2024 value (+0.64) applied to "
        "every year against a measured +0.49 / +0.64 / +0.65, so 2023 carries "
        "+0.15 $/MMBtu, about +$1.65/MWh, on EVERY gas unit alike — a common level "
        "shift, which cannot move CT_PEAKER against ST_GAS but can move the gas block "
        "against coal. Making it per-year is a rule 23 [R-FROZEN-DERIVE] "
        "re-derivation on source data and is ROUTED, not taken here "
        "(ADDENDUM-soco54-the-fallback-basis-2026-09-20.md §3). The single remaining "
        "residual entry is the inherited wefor_multiplier, untouched here."
    )
