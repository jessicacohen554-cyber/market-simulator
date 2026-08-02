"""Derive the gas-offer net-revenue margin ANCHOR ($/MMBtu) for an ISO.

The identification constant of the ``gas_offer_net_revenue_margin`` mechanism
(``constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO``; design doc
``docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md``): the mean of
the model's own merit-order delivered-gas series
(:func:`market_sim.data.fuel.trajectories._gas_series` — measured EIA Henry
Hub monthly × the ISO's measured hub basis, the exact series the registered
``offer_curve_by_group`` band multipliers were calibrated against) over the
training window 2023–2025. At ``fuel == anchor`` the reformed offer reduces
EXACTLY to the registered band multiplier, so the anchor is the point where
the multiplicative and fixed-margin forms are observationally equivalent —
the identification point, not a tunable.

Rule-23 frozen derive: re-run ONLY when the underlying gas source data
changes (``data/raw/gas-prices/`` workbooks — Henry Hub monthly/daily, the
ISO hub basis series — or the EIA-923 ISO-month receipts), and cite that data
change in the re-derivation commit. NEVER because a price residual moved.

It is a REPORTING / derivation tool only — default-off in every solve path.
The single model artifact it informs is the hand-set
``GAS_OFFER_MARGIN_ANCHOR_BY_ISO`` entry in ``config/constants.py`` (cited
back to this script), consumed by the harness only under
``--gas-offer-margin``.

With ``--net-revenue-check`` it also prints the per-band fixed margins the
anchor implies for the ISO's registered curve (markup × base_HR × anchor) and
the Potomac-SOM-style peaker cross-check — the offer-side analogue of
``model/capacity_evolution/retirements.py``'s net-revenue screen: the
scarcity margin's implied cost-recovery run-hours,
``fixed_om_gas_ct × 1000 / margin``. Documentation only; never a tuning
channel.

Usage::

    python scripts/data/derive_gas_offer_margin_anchor.py --iso NEISO
    python scripts/data/derive_gas_offer_margin_anchor.py --iso NEISO --net-revenue-check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fuel.trajectories import _gas_series  # noqa: E402

# Training window (CLAUDE.md rule 22: 2023–2025 is the ONLY tuned-against
# span) with the measured EIA annual Henry Hub spot averages every keeper
# recipe carries (calibration_flags.gas_prices — EIA Natural Gas Spot Price,
# Henry Hub, annual averages). The override only levels months the measured
# ISO-month / hub-basis overlays leave uncovered.
TRAIN_WINDOW_HH: dict[int, float] = {2023: 2.54, 2024: 2.19, 2025: 3.52}

# Per-ISO gas flag recipe for the delivered series — mirrors the calibration
# harness (each ISO's KEEPER backcast_config gas overlay): monthly EIA-923
# actuals + the ISO's measured hub/basis overlay. The daily within-month shape
# (gas_daily_shape / gas_hub_basis_daily) is mean-preserved to the monthly hub
# level by construction, so the ANNUAL mean — hence the anchor — is identical
# with or without the daily leg; the daily flags are carried only to mirror the
# keeper exactly. Each entry is the True gas-flag set of the ISO's keeper
# run_config.json (2026-07-23 keepers: ercot99 / pjm-gasshape-interpfix /
# caiso-102 / miso-81 / nyiso-70 / neiso-61), so the anchor is derived on the
# exact delivered-gas series the registered offer_curve_by_group multipliers
# were calibrated against (rule 24 — anchors never cross ISO boundaries).
GAS_SERIES_FLAGS: dict[str, dict[str, bool]] = {
    # ERCOT keeper (ercot99, still the ercot149 lineage's series): annual Henry
    # Hub + seasonality only — no monthly actuals, no hub-basis overlay (E1:
    # ERCOT stays on annual + shape). The keeper's gas_hh_monthly_shape /
    # gas_daily_shape are exactly mean-preserving (hour-weighted monthly shape;
    # per-month daily shape), so the ANNUAL mean — hence the anchor — is
    # identical without them. Its ercot_zonal_gas_basis arming is deliberately
    # NOT here: that flag also perturbs _gas_series itself (the flat EP level
    # term), so it is handled via ZONAL_FLAG_PERTURBS_SERIES — the base series
    # keeps this recipe and the applier call carries the keeper's arming.
    "ERCOT": {
        "gas_seasonality": True,
    },
    # PJM keeper: --gas-monthly-actuals (its keeper passes it explicitly) +
    # the mean-preserving daily HH shape. No citygate/basin hub overlay. The
    # zonal-basis flag mirrors the keeper (pjm-143b run_config
    # pjm_zonal_gas_basis=true) and is required so ZONAL_BASIS_APPLIERS["PJM"]
    # fires when :func:`derive_zonal_anchors` applies the runtime transform —
    # it does not change ``_gas_series`` (the basis applies on the (n_gen, T)
    # array, never the ISO series), so the ISO anchor is unchanged by it.
    "PJM": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_daily_shape": True,
        "pjm_zonal_gas_basis": True,
    },
    # CAISO keeper: monthly actuals + the SoCal/PG&E Citygate hub-basis overlay
    # (the measured CA trading hub the marginal CC prices off) + daily shape.
    "CAISO": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_hub_basis_overlay": True,
        "gas_daily_shape": True,
    },
    # MISO keeper: per-plant EIA-923 monthly level with the mean-preserving
    # daily HH swing on top (no ISO-month actuals flag, no hub overlay).
    "MISO": {
        "gas_seasonality": True,
        "gas_daily_shape": True,
    },
    # NYISO keeper: monthly actuals + the (mean-zero) zonal pipeline-hub basis +
    # the Transco Z6 daily hub overlay + daily shape.
    "NYISO": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_hub_basis_overlay": True,
        "gas_hub_basis_daily": True,
        "gas_daily_shape": True,
        "nyiso_zonal_gas_basis": True,
    },
    "NEISO": {
        "gas_seasonality": True,
        "gas_monthly_actuals": True,
        "gas_hub_basis_overlay": True,
        "gas_hub_basis_daily": True,
    },
}


def derive_anchor(iso: str) -> tuple[dict[int, float], float]:
    """Return ({year: delivered mean}, window anchor) for ``iso``."""
    if iso not in GAS_SERIES_FLAGS:
        raise SystemExit(
            f"{iso}: no delivered-gas series recipe registered in this derive "
            "script — add the ISO's calibration gas flags (mirroring "
            "backcast_config) before deriving an anchor (rule 24: anchors "
            "never cross ISO boundaries)"
        )
    base = ScenarioConfig(
        iso=iso, mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS[iso]
    )
    year_means: dict[int, float] = {}
    for year, hh in sorted(TRAIN_WINDOW_HH.items()):
        series = _gas_series(
            base.with_overrides(gas_price_override=hh), year, HOURS_PER_YEAR
        )
        year_means[year] = float(np.nanmean(series))
    anchor = float(np.mean(list(year_means.values())))
    return year_means, anchor


#: ISOs whose keeper applies a PER-ZONE delivered-gas basis, so the ISO-level
#: series :func:`derive_anchor` reads is NOT the price their units actually pay.
#: Only these ISOs have a zone-resolved anchor to derive; every other ISO's
#: unit fuel IS the ISO series, so its single anchor is already identified at
#: the grain the mechanism's own definition requires. Rule 25 — an entry here is
#: that ISO's own measured basis table and never transfers.
ZONAL_BASIS_ISOS: frozenset[str] = frozenset({"NYISO", "PJM", "ERCOT"})

#: The subset of :data:`ZONAL_BASIS_ISOS` whose applier is the shared
#: CAPACITY-WEIGHTED MEAN-ZERO core (``data.fuel.basis.meanzero``): the raw
#: per-zone basis is re-centred by subtracting the GAS-CAPACITY-weighted mean
#: over the fleet's gas rows, so the calibrated fleet-aggregate level is
#: preserved and only the cross-zonal spread opens. For these ISOs the runtime
#: transform depends on the solve's own per-zone gas capacity, so the zonal
#: derivation must carry the SOLVE's fleet weights — supplied via
#: ``--weights-bundle`` (the keeper bundle whose ``meta.json`` fleet recipe is
#: rebuilt no-LP through ``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``,
#: the same reconstruction every no-LP pre-check uses). NYISO's applier is
#: absolute (reference-zone-anchored offsets, no weighting), so its synthetic
#: one-row-per-zone fleet measures the transform exactly and needs no bundle.
#: ERCOT's applier (``basis.ercot.apply_ercot_zonal_gas_basis``) is its own
#: module, not the ``meanzero`` core, but it re-centres the same way (the
#: per-zone EIA-923 basis minus the gas-capacity-weighted fleet mean) and ADDS
#: a flat measured LEVEL correction (the TX delivered-to-electric-power basis
#: replacing the flat GAS_BASIS_DIFFERENTIAL scalar), so it belongs here: the
#: transform depends on the solve's own per-zone gas capacity.
CAPWEIGHTED_ZONAL_ISOS: frozenset[str] = frozenset({"PJM", "ERCOT"})

#: ISOs whose zonal-basis config flag ALSO perturbs the ISO-level series
#: :func:`derive_anchor` reads: ``ercot_zonal_gas_basis`` adds the flat
#: EP-basis level correction inside ``_gas_series`` itself (the coal-sigmoid
#: reference path, ``trajectories.py``), while the merit order receives the
#: SAME correction exactly once — from ``apply_ercot_zonal_gas_basis`` on the
#: ``(n_gen, T)`` array. Arming the flag on the config the BASE series is read
#: with would therefore double-count the level term. For these ISOs the base
#: series keeps the registered ISO-anchor recipe (:data:`GAS_SERIES_FLAGS`,
#: flag off) and the APPLIER call uses the reconstructed keeper config — which
#: arms the flag exactly as the solve did, haircut/floor arming included. PJM's
#: and NYISO's flags never touch ``_gas_series``, so they stay in
#: :data:`GAS_SERIES_FLAGS` and their paths are unchanged.
ZONAL_FLAG_PERTURBS_SERIES: frozenset[str] = frozenset({"ERCOT"})

#: Per-ISO flags the reconstructed weights bundle MUST arm for the zonal
#: derivation to be measuring the keeper's own transform (checked on the
#: reconstructed config, hard-fail on drift — the GAS_SERIES_FLAGS contract
#: extended to flags that live outside the base-series recipe).
ZONAL_KEEPER_REQUIRED_FLAGS: dict[str, tuple[str, ...]] = {
    "ERCOT": ("ercot_zonal_gas_basis",),
}


def derive_zonal_anchors(
    iso: str,
    weights_bundle: Path | None = None,
) -> tuple[dict[str, dict[int, float]], dict[str, float]]:
    """Return ({zone: {year: delivered mean}}, {zone: anchor}) for ``iso``.

    The zone-resolved identification point of ``gas_offer_net_revenue_margin``.
    :func:`derive_anchor` reads ``_gas_series``, which is ISO-level: it carries
    the hub overlay but NOT the per-zone basis, which the solve applies later on
    the ``(n_gen, T)`` array. So on an ISO with a zonal basis the single anchor
    is NOT the level every unit pays — and ``apply_gas_offer_margin``'s
    ``markup_hr × (anchor − fuel)`` then hands units a margin shift their band
    multipliers were never calibrated to carry. The mechanism's own identity —
    *at ``fuel == anchor`` the reformed offer reduces EXACTLY to the registered
    band multiplier* — is a statement about a unit's OWN delivered fuel, so the
    anchor has to be measured on the same series that unit's fuel comes from.
    Two applier conventions exist, with opposite defect geometry:

    * **NYISO** (``basis.nyiso.apply_nyiso_zonal_gas_basis``): absolute offsets
      anchored so the REFERENCE zone is unchanged and every other zone shifts
      strictly DOWN — the ISO anchor is the reference (maximum) level and the
      defect is one-sided over-marking. The applier ignores capacity, so a
      synthetic one-gas-row-per-zone fleet measures its transform exactly.
    * **Capacity-weighted mean-zero** (:data:`CAPWEIGHTED_ZONAL_ISOS`; the
      ``basis.meanzero`` core, PJM): each zone's measured basis has the
      GAS-CAPACITY-weighted fleet mean subtracted, so the aggregate level is
      preserved and the defect is TWO-SIDED — premium zones under-marked,
      discount zones over-marked, centred on the ISO anchor. The transform
      depends on the solve's own per-zone gas capacity, so ``weights_bundle``
      (the keeper bundle) is REQUIRED: its per-year fleet is rebuilt no-LP via
      ``scripts.lib.bundle_fleet.reconstruct_bundle_fleet`` and the runtime
      applier is called on that real fleet.

    Both paths apply the RUNTIME transform (never a re-derivation of it) to the
    same delivered series the ISO anchor is derived from, so the zonal levels
    here are by construction the levels the solve prices those units at.

    Rule-23 frozen derive, exactly like :func:`derive_anchor`: re-run ONLY when
    the underlying gas source data changes (``data/raw/gas-prices/`` workbooks,
    the ISO hub-basis series, the per-zone hub table, or — for a
    capacity-weighted ISO — the keeper fleet recipe the weights are read from),
    and cite that data change in the re-derivation commit. NEVER because a
    price residual moved.
    """
    if iso not in ZONAL_BASIS_ISOS:
        raise SystemExit(
            f"{iso}: no per-zone delivered-gas basis is armed on this ISO's "
            "keeper, so its single anchor is already identified at the grain "
            "its units' fuel is drawn at — there is no zonal anchor to derive "
            "(rule 25: never transfer another ISO's zonal table)"
        )
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX
    from market_sim.data.fuel.basis import ZONAL_BASIS_APPLIERS

    zone_names = list(get_iso_config(iso).zone_names)
    base = ScenarioConfig(
        iso=iso, mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS[iso]
    )
    apply_basis = ZONAL_BASIS_APPLIERS[iso]
    by_zone: dict[str, dict[int, float]] = {z: {} for z in zone_names}

    if iso in CAPWEIGHTED_ZONAL_ISOS:
        if weights_bundle is None:
            raise SystemExit(
                f"{iso}: its zonal-basis applier re-centres on the "
                "GAS-CAPACITY-weighted fleet mean, so the runtime transform "
                "depends on the solve's own fleet — pass --weights-bundle "
                "<keeper bundle> so the per-year weights are the keeper's own "
                "fleet build (reconstruct_bundle_fleet, no LP), never a "
                "synthetic approximation"
            )
        from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

        empty_zone_years: dict[str, list[int]] = {z: [] for z in zone_names}
        for year, hh in sorted(TRAIN_WINDOW_HH.items()):
            state, meta = reconstruct_bundle_fleet(
                Path(weights_bundle), year, verbose=True
            )
            if meta.get("iso", "").upper() != iso:
                raise SystemExit(
                    f"--weights-bundle is a {meta.get('iso')} bundle, not {iso}"
                )
            fleet = state["fleet_arrays"]
            rec_cfg = state["config"]
            # The weights bundle must price gas exactly the way this recipe
            # does — a drifted keeper gas recipe would identify the anchor on
            # a series the solve never prices (the GAS_SERIES_FLAGS comment's
            # contract, now checked instead of assumed).
            for flag in GAS_SERIES_FLAGS[iso]:
                if bool(getattr(rec_cfg, flag, False)) is not True:
                    raise SystemExit(
                        f"--weights-bundle does not arm {flag}, but the "
                        f"registered {iso} delivered-series recipe does — "
                        "re-align GAS_SERIES_FLAGS with the keeper before "
                        "deriving (rule 24: the anchor is identified on the "
                        "keeper's own delivered series)"
                    )
            # Flags outside the base-series recipe the keeper must still arm
            # (e.g. the zonal-basis gate itself): without them the applier
            # below would no-op and every "zone anchor" would silently equal
            # the ISO anchor — measuring nothing.
            for flag in ZONAL_KEEPER_REQUIRED_FLAGS.get(iso, ()):
                if bool(getattr(rec_cfg, flag, False)) is not True:
                    raise SystemExit(
                        f"--weights-bundle does not arm {flag}: the {iso} "
                        "keeper does not apply the per-zone basis this "
                        "derivation measures — there is no zonal anchor to "
                        "derive from this bundle"
                    )
            cfg = base.with_overrides(gas_price_override=hh)
            series = _gas_series(cfg, year, HOURS_PER_YEAR)
            n_gen = int(fleet.pmax.shape[0])
            prices = np.repeat(series[None, :], n_gen, axis=0)
            # The applier call carries the RECONSTRUCTED KEEPER config for the
            # ISOs whose zonal flag also perturbs _gas_series (the base series
            # above deliberately keeps the registered ISO-anchor recipe so the
            # level term enters exactly once, from the applier — mirroring the
            # merit path); elsewhere the recipe config already arms the flag.
            apply_cfg = rec_cfg if iso in ZONAL_FLAG_PERTURBS_SERIES else cfg
            apply_basis(prices, fleet, apply_cfg, year)
            gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
            for i, zone in enumerate(zone_names):
                rows = gas_rows[fleet.zone_idx[gas_rows] == i]
                if rows.size == 0:
                    # A zone with no gas capacity has no unit to anchor — its
                    # map entry would be dead weight (assembly.py keeps the
                    # window anchor for zones absent from the map). Dropped
                    # AFTER the year loop, and only if empty in EVERY year.
                    empty_zone_years[zone].append(year)
                    continue
                # Every gas row in a zone carries the same additive spread, so
                # the first row IS the zone's transformed series — guarded: a
                # per-UNIT transform (e.g. an armed per-plant contract haircut)
                # would break the zone grain this table is keyed on.
                row_means = np.nanmean(prices[rows, :], axis=1)
                if float(np.ptp(row_means)) > 1e-9:
                    raise SystemExit(
                        f"{zone} {year}: gas rows in one zone carry DIFFERENT "
                        "transformed delivered levels (max-min "
                        f"{float(np.ptp(row_means)):.6f} $/MMBtu) — the "
                        "keeper's transform is per-unit, not per-zone, and a "
                        "zone-keyed anchor table cannot represent it"
                    )
                by_zone[zone][year] = float(row_means[0])
            del state, prices
        for zone, missing in empty_zone_years.items():
            if missing and len(missing) != len(TRAIN_WINDOW_HH):
                raise SystemExit(
                    f"{zone}: gas rows present in some years but none in "
                    f"{missing} — inconsistent weights fleet"
                )
            if missing:
                print(
                    f"  [{zone}: no gas capacity in any training year — "
                    "omitted from the table; zones absent from the map keep "
                    "the ISO window anchor]"
                )
                del by_zone[zone]
    else:
        from market_sim.data.fleet import FleetArrays

        n = len(zone_names)
        gas_idx = int(sorted(_GAS_FUEL_IDX)[0])
        for year, hh in sorted(TRAIN_WINDOW_HH.items()):
            cfg = base.with_overrides(gas_price_override=hh)
            series = _gas_series(cfg, year, HOURS_PER_YEAR)
            prices = np.repeat(series[None, :], n, axis=0)
            # One synthetic gas row per zone: this ISO's applier keys only on
            # ``fuel_type_idx`` and ``zone_idx`` (no capacity weighting), so
            # this measures its transform exactly as the solve applies it.
            fleet = FleetArrays(
                pmax=np.ones(n),
                pmin=np.zeros(n),
                heat_rate=np.full(n, 7.0),
                vom=np.zeros(n),
                emission_rate=np.zeros(n),
                nox_rate=np.zeros(n),
                so2_rate=np.zeros(n),
                zone_idx=np.arange(n),
                fuel_type_idx=np.full(n, gas_idx),
                availability=np.ones((n, HOURS_PER_YEAR)),
                unit_ids=[f"probe_{z}" for z in zone_names],
                efficiency_bin=np.zeros(n, dtype=int),
                plant_code=np.zeros(n, dtype=int),
            )
            apply_basis(prices, fleet, cfg, year)
            for i, zone in enumerate(zone_names):
                by_zone[zone][year] = float(np.nanmean(prices[i]))
    anchors = {z: float(np.mean(list(v.values()))) for z, v in by_zone.items()}
    return by_zone, anchors


def _net_revenue_check(iso: str, anchor: float) -> None:
    """Print the fixed margins the anchor implies + the SOM-style cross-check."""
    from market_sim.data.offer_curves import gas_offer_margin_markup_mult
    from market_sim.pipeline.backcast_config import backcast_config

    # Resolve the ISO's DEFAULT backcast offer curve (base ternaries + per-ISO
    # merge + the phys_* keys), so this works uniformly — including ERCOT, whose
    # phys keys live in a phys-only _ERCOT_OFFER_CURVE deep-merged onto the
    # shared base (the recipe's --offer-curve overrides are NOT applied here;
    # this is the base-curve documentation cross-check, not the keeper's live
    # peak wall).
    curve = backcast_config(2024, iso, HOURS_PER_YEAR, anchor).offer_curve_by_group
    if not any(any(k.startswith("phys_") for k in bands) for bands in curve.values()):
        print(f"[net-revenue-check] no phys-keyed curve registered for {iso}")
        return
    # Class base heat rates from the ISO's CAMPD marginal-HR artifact (the
    # same measurement the phys_* keys come from).
    import csv

    base_hr_path = (
        Path(__file__).resolve().parents[2]
        / "data/raw/reference"
        / f"{iso.lower()}_campd_marginal_hr_summary.csv"
    )
    base_hr = {
        row["class"]: float(row["base_hr"])
        for row in csv.DictReader(open(base_hr_path))
    }
    print(f"\nFixed margins at anchor {anchor:.4f} $/MMBtu (markup x HR x anchor):")
    for cls, bands in sorted(curve.items()):
        hr = base_hr.get(cls)
        # Only the phys-keyed gas classes carry the mechanism (coal / neutral
        # classes have no phys_* keys → markup 0, skipped to keep the table tight).
        if hr is None or not any(k.startswith("phys_") for k in bands):
            continue
        margins = {}
        for suffix, mult_key in (
            ("committed", "committed"),
            ("econlo", "econ_low"),
            ("econhi", "econ_high"),
            ("peak", "peak"),
        ):
            mult = bands.get(mult_key)
            if mult is None:
                continue
            mk = gas_offer_margin_markup_mult(suffix, float(mult), bands)
            margins[mult_key] = mk * hr * anchor
        print(f"  {cls:12s} " + "  ".join(f"{k}={v:7.2f}" for k, v in margins.items()))
    # Offer-side Potomac-SOM cross-check (retirements.py net-revenue logic
    # inverted): the CT scarcity margin's implied cost-recovery run-hours
    # against a FOM-only going-forward cost.
    ct = curve.get("CT_PEAKER")
    if ct and "phys_peak" in ct:
        hr = base_hr["CT_PEAKER"]
        margin = gas_offer_margin_markup_mult("peak", float(ct["peak"]), ct) * hr
        margin_usd = margin * anchor
        fom = ScenarioConfig(iso=iso).fixed_om_gas_ct  # $/kW-yr
        if margin_usd > 0:
            hours = fom * 1000.0 / margin_usd
            print(
                f"\n[net-revenue-check] CT_PEAKER scarcity margin "
                f"{margin_usd:.1f} $/MWh recovers FOM-only GFC "
                f"({fom:.0f} $/kW-yr) over {hours:.0f} expected scarcity "
                "run-hours/yr — the missing-money construction "
                "(retirements.py::apply_economic_retirements, offer side)."
            )


def main() -> None:
    """Derive and print the anchor; optionally the margin table."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--iso", default="NEISO")
    parser.add_argument(
        "--net-revenue-check",
        action="store_true",
        help="Also print the per-band fixed margins the anchor implies and "
        "the SOM-style peaker cost-recovery cross-check (documentation only).",
    )
    parser.add_argument(
        "--by-zone",
        action="store_true",
        help="Also derive the ZONE-resolved anchors (ISOs whose keeper arms a "
        "per-zone delivered-gas basis; register in constants."
        "GAS_OFFER_MARGIN_ANCHOR_BY_ZONE, cite this script).",
    )
    parser.add_argument(
        "--weights-bundle",
        default=None,
        metavar="BUNDLE",
        help="Keeper bundle whose per-year fleet supplies the gas-capacity "
        "weights (REQUIRED with --by-zone for the capacity-weighted mean-zero "
        "ISOs, e.g. results/calibration/pjm143_hy_level_B for PJM or "
        "results/calibration/ercot149_gas_event_cap_arm for ERCOT; rebuilt "
        "no-LP via scripts.lib.bundle_fleet.reconstruct_bundle_fleet).",
    )
    args = parser.parse_args()
    year_means, anchor = derive_anchor(args.iso)
    print(f"{args.iso} delivered-gas anchor derivation (train window):")
    for year, mean in year_means.items():
        print(f"  {year}: mean delivered = {mean:.4f} $/MMBtu")
    print(
        f"ANCHOR = {anchor:.4f} $/MMBtu  (register in constants."
        "GAS_OFFER_MARGIN_ANCHOR_BY_ISO, cite this script)"
    )
    if args.by_zone:
        by_zone, anchors = derive_zonal_anchors(
            args.iso,
            Path(args.weights_bundle) if args.weights_bundle else None,
        )
        print(
            f"\n{args.iso} ZONE-resolved anchors (the same series with each "
            "zone's own measured basis applied — what its gas units pay):"
        )
        for zone in sorted(anchors, key=lambda z: -anchors[z]):
            years = "  ".join(f"{y}: {v:.4f}" for y, v in sorted(by_zone[zone].items()))
            print(
                f"  {zone:<16} {years}   ANCHOR = {anchors[zone]:.4f} "
                f"(ISO anchor {anchor:+.4f} -> {anchors[zone] - anchor:+.4f})"
            )
        print(
            "  (register in constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE, cite "
            "this script)"
        )
    if args.net_revenue_check:
        _net_revenue_check(args.iso, anchor)


if __name__ == "__main__":
    main()
