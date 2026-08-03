"""miso-119 PHASE 0: the `gas_offer_margin_zonal_anchor` EX-ANTE SCREEN at MISO.

No LP. Pre-registration
``results/calibration/PREREG-miso119-zonal-anchor-screen-2026-08-03.md``
(pushed before this ran) fixes the whole decision rule; this probe only
executes it. Two ex-ante routes to ``I``, either sufficient:

* **Route A** — anchor-grain inertness (pjm-144 §1.3's own pre-declared
  ex-ante bar): ``max_z |anchor_z − 3.0492| < 0.10 $/MMBtu``.
* **Route B** — price-side unreachability of the row's K3 liveness gate:
  ``max_{g,y} |Δoffer_g(y)| < 0.10 $/MWh`` where
  ``Δoffer_g = offer_markup_hr_g × (anchor_zone(g) − 3.0492)`` — the exact,
  hour-invariant A−B offer delta of arming the zonal anchor on the keeper's
  own fleet.

If neither fires the screen returns LIVE and the pre-registered Phase 1 A/B
(prereg §5) runs. Construction gates S1–S6 (prereg §4) can only invalidate
the screen, never adjudicate.

The model side is the KEEPER's own configuration
(``results/calibration/miso117_ctheatrate_B``): the run_config check drops
ONLY keys in ``scenarios._CACHE_KEY_RETIRED_FIELDS`` and hard-fails any other
unknown key (miso-116 §7 discipline, upgraded per the miso-119 handoff), and
the fleet is rebuilt no-LP via the sanctioned
``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso119_zonal_anchor_screen.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import (  # noqa: E402
    ScenarioConfig,
    _CACHE_KEY_RETIRED_FIELDS,
)
from market_sim.data.fuel._shared import _GAS_FUEL_IDX  # noqa: E402
from market_sim.data.fuel.basis import ZONAL_BASIS_APPLIERS  # noqa: E402
from market_sim.data.fuel.basis.meanzero import (  # noqa: E402
    MISO_ZONAL_GAS_HUB_PATH,
)
from market_sim.data.fuel.trajectories import _gas_series  # noqa: E402

from scripts.data.derive_gas_offer_margin_anchor import (  # noqa: E402
    GAS_SERIES_FLAGS,
    TRAIN_WINDOW_HH,
    derive_anchor,
    derive_zonal_anchors,
)
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

ISO = "MISO"
KEEPER = REPO / "results/calibration/miso117_ctheatrate_B"
YEARS = (2023, 2024, 2025)
ISO_ANCHOR = 3.0492  # keeper run_config gas_offer_margin_anchor (asserted S1)
ROUTE_A_BAR = 0.10  # $/MMBtu — pjm-144 §1.3's pre-declared ex-ante anchor bar
ROUTE_B_BAR = 0.10  # $/MWh — the row's K3 zonal-price liveness gate
TAIL_THRESHOLD = 200.0  # $/MWh — the C3c tail-count threshold


def gate_s1_keeper_config() -> dict:
    """S1: run_config fidelity — retired-key filtering + flag assertions."""
    snap = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    valid = {f.name for f in dataclasses.fields(ScenarioConfig)}
    unknown = sorted(set(snap) - valid)
    not_retired = sorted(set(unknown) - set(_CACHE_KEY_RETIRED_FIELDS))
    if not_retired:
        raise SystemExit(
            f"S1 FAIL: keeper run_config carries unknown NON-retired keys "
            f"{not_retired} — the probe would read a different model than the "
            "keeper solved"
        )
    print(f"S1: retired keys dropped via _CACHE_KEY_RETIRED_FIELDS: {unknown}")
    expect = {
        "miso_zonal_gas_basis": True,
        "gas_offer_net_revenue_margin": True,
        "gas_offer_margin_anchor": ISO_ANCHOR,
        "gas_offer_margin_zonal_anchor": False,
        "gas_offer_margin_anchor_by_zone": None,
        "measured_chp_heat_rates": True,
        "measured_ct_heat_rates": True,
    }
    for key, want in expect.items():
        got = snap.get(key)
        if got != want:
            raise SystemExit(f"S1 FAIL: keeper {key} == {got!r}, expected {want!r}")
    print(f"S1 PASS: all {len(expect)} keeper flag assertions hold")
    return snap


def gate_s2_iso_anchor_invariance() -> None:
    """S2: the registry extension moved nothing on the ISO anchor."""
    year_means, anchor = derive_anchor(ISO)
    print(f"S2: derive_anchor(MISO) year means {year_means} -> anchor {anchor:.4f}")
    if abs(anchor - ISO_ANCHOR) > 1e-4:
        raise SystemExit(
            f"S2 FAIL: ISO anchor moved to {anchor:.6f} (registered "
            f"{ISO_ANCHOR}) — the GAS_SERIES_FLAGS extension perturbed "
            "_gas_series"
        )
    print("S2 PASS: ISO anchor unchanged by the zonal-flag recipe extension")


def gate_s6_hub_coverage() -> None:
    """S6: all six zones x 2023-2025 present, no SPARSE in-window row."""
    frame = pd.read_csv(MISO_ZONAL_GAS_HUB_PATH)
    zone_names = list(get_iso_config(ISO).zone_names)
    sub = frame[frame["year"].isin(YEARS)]
    for zone in zone_names:
        have = sorted(sub[sub["zone"] == zone]["year"].tolist())
        if have != sorted(YEARS):
            raise SystemExit(f"S6 FAIL: {zone} has in-window years {have}")
    sparse = sub[sub["source"].str.contains("SPARSE", na=False)]
    if not sparse.empty:
        raise SystemExit(
            f"S6 FAIL: SPARSE-flagged in-window rows:\n{sparse[['zone', 'year']]}"
        )
    print(
        f"S6 PASS: {len(zone_names)} zones x {len(YEARS)} years present, "
        "no SPARSE in-window row"
    )
    print("\nraw basis rows 2023-2025 ($/MMBtu vs HH):")
    piv = sub.pivot(index="zone", columns="year", values="basis_vs_hh_usd_mmbtu")
    piv["window_mean"] = piv.mean(axis=1)
    print(piv.round(4).to_string())


def screen() -> None:
    """Run the pre-registered Phase 0 screen and print the verdict."""
    print("=" * 78)
    print("miso-119 PHASE 0 — gas_offer_margin_zonal_anchor ex-ante screen (no LP)")
    print("=" * 78)
    gate_s1_keeper_config()
    gate_s2_iso_anchor_invariance()
    gate_s6_hub_coverage()

    # §2 derivation — the standing derive's own function, keeper weights.
    print("\n§2 derivation (standing derive, keeper weights bundle):")
    by_zone, anchors = derive_zonal_anchors(ISO, weights_bundle=KEEPER)
    print("\nzone-resolved anchors ($/MMBtu):")
    for zone in sorted(anchors, key=lambda z: -anchors[z]):
        yrs = "  ".join(f"{y}={by_zone[zone][y]:.4f}" for y in sorted(by_zone[zone]))
        print(
            f"  {zone:15s} {yrs}  ANCHOR={anchors[zone]:.4f} "
            f"(vs ISO {ISO_ANCHOR}: {anchors[zone] - ISO_ANCHOR:+.4f})"
        )

    # Per-year pass on the keeper's own fleet: S3 invariant, S4 census, the
    # Route B Δoffer distribution, and the derivation cross-check.
    zone_names = list(get_iso_config(ISO).zone_names)
    base = ScenarioConfig(
        iso=ISO, mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS[ISO]
    )
    apply_basis = ZONAL_BASIS_APPLIERS[ISO]
    max_abs_doffer = 0.0
    all_years_stats: dict[int, dict] = {}
    for year in YEARS:
        hh = TRAIN_WINDOW_HH[year]
        state, meta = reconstruct_bundle_fleet(KEEPER, year, verbose=True)
        fleet = state["fleet_arrays"]
        gens = state["fleet"]
        cfg = base.with_overrides(gas_price_override=hh)
        series = _gas_series(cfg, year, HOURS_PER_YEAR)
        iso_year_mean = float(np.nanmean(series))
        n_gen = int(fleet.pmax.shape[0])
        prices = np.repeat(series[None, :], n_gen, axis=0)
        apply_basis(prices, fleet, cfg, year)
        gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
        row_year_means = np.nanmean(prices[gas_rows, :], axis=1)
        # S3: the applier's own mean-zero invariant on the keeper fleet.
        w = fleet.pmax[gas_rows]
        capw_mean = float(np.average(row_year_means, weights=w))
        s3_resid = abs(capw_mean - iso_year_mean)
        print(
            f"S3 {year}: capw mean of transformed gas rows {capw_mean:.6f} vs "
            f"ISO series mean {iso_year_mean:.6f} (|Δ| = {s3_resid:.2e})"
        )
        if s3_resid > 1e-6:
            raise SystemExit(f"S3 FAIL {year}: mean-zero invariant broken")
        # Cross-check the derive's per-year zone values on this same pass.
        for i, zone in enumerate(zone_names):
            rows = gas_rows[fleet.zone_idx[gas_rows] == i]
            if rows.size == 0:
                continue
            mine = float(np.nanmean(prices[rows[0], :]))
            theirs = by_zone.get(zone, {}).get(year)
            if theirs is None or abs(mine - theirs) > 1e-9:
                raise SystemExit(
                    f"derivation cross-check FAIL: {zone} {year} probe "
                    f"{mine:.9f} vs derive {theirs}"
                )
        # S4 + Route B: the marked-up census and the exact A−B offer delta.
        mk = np.fromiter(
            (float(getattr(g, "offer_markup_hr", 0.0)) for g in gens),
            dtype=float,
            count=len(gens),
        )
        marked = np.nonzero(mk > 0.0)[0]
        if marked.size == 0:
            print(f"S4 {year}: ZERO marked-up tranches — mechanism has no domain")
            all_years_stats[year] = {"marked": 0}
            continue
        band_scoped = sum(
            1 for g in gens if getattr(g, "offer_margin_anchor", None) is not None
        )
        anchor_by_zone_idx = np.array(
            [anchors.get(name, ISO_ANCHOR) for name in zone_names], dtype=float
        )
        delta_anchor = anchor_by_zone_idx[fleet.zone_idx[marked]] - ISO_ANCHOR
        doffer = mk[marked] * delta_anchor
        wm = fleet.pmax[marked]
        order = np.argsort(np.abs(doffer))
        cum = np.cumsum(wm[order]) / wm.sum()
        capw_p50 = float(np.abs(doffer)[order][np.searchsorted(cum, 0.50)])
        capw_p95 = float(np.abs(doffer)[order][np.searchsorted(cum, 0.95)])
        year_max = float(np.abs(doffer).max())
        max_abs_doffer = max(max_abs_doffer, year_max)
        classes = sorted(
            {str(getattr(gens[i], "plant_group", "?")) for i in marked}
        )
        print(
            f"S4 {year}: {marked.size} marked-up tranches, "
            f"{wm.sum():,.1f} MW, {band_scoped} band-scoped anchors; "
            f"classes {classes}"
        )
        print(
            f"Route B {year}: |Δoffer| capw p50 {capw_p50:.4f}  "
            f"capw p95 {capw_p95:.4f}  MAX {year_max:.4f} $/MWh  "
            f"(signed range {doffer.min():+.4f} .. {doffer.max():+.4f})"
        )
        top = np.argsort(-np.abs(doffer))[:5]
        for j in top:
            gi = marked[j]
            print(
                f"    top: {getattr(gens[gi], 'name', '?')[:40]:40s} "
                f"{str(getattr(gens[gi], 'plant_group', '?')):12s} "
                f"zone={zone_names[int(fleet.zone_idx[gi])]:14s} "
                f"markup_hr={mk[gi]:8.3f}  Δoffer={doffer[j]:+.4f}"
            )
        all_years_stats[year] = {
            "marked": int(marked.size),
            "mw": float(wm.sum()),
            "capw_p50": capw_p50,
            "capw_p95": capw_p95,
            "max": year_max,
        }
        del state, prices

    # S5 + coupling census + tail proximity from the committed sidecars.
    print("\nS5: keeper zone-coupling census (committed hourly sidecars):")
    for year in YEARS:
        df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        p1 = df[df["pass"] == "P1"] if "pass" in df.columns else df
        wide = p1.pivot_table(index="hour", columns="zone", values="price")
        rng = wide.max(axis=1) - wide.min(axis=1)
        shares = {
            thr: float((rng > thr).mean()) for thr in (0.01, 0.10, 1.0, 5.0)
        }
        near_tail = int(
            (np.abs(wide.to_numpy() - TAIL_THRESHOLD) < max(max_abs_doffer, 1e-9))
            .any(axis=1)
            .sum()
        )
        print(
            f"  {year}: zones={wide.shape[1]}  cross-zone range > "
            + "  ".join(f"${t}: {shares[t]:6.1%}" for t in shares)
            + f"  | hours with any zone within {max_abs_doffer:.4f} of "
            f"${TAIL_THRESHOLD:.0f}: {near_tail}"
        )

    # The pre-registered verdict.
    max_anchor_delta = max(abs(a - ISO_ANCHOR) for a in anchors.values())
    route_a = max_anchor_delta < ROUTE_A_BAR
    route_b = max_abs_doffer < ROUTE_B_BAR
    print("\n" + "=" * 78)
    print(
        f"Route A: max_z |anchor_z − {ISO_ANCHOR}| = {max_anchor_delta:.4f} "
        f"$/MMBtu vs bar {ROUTE_A_BAR} -> {'FIRES (I)' if route_a else 'does not fire'}"
    )
    print(
        f"Route B: max |Δoffer| = {max_abs_doffer:.4f} $/MWh vs bar "
        f"{ROUTE_B_BAR} -> {'FIRES (I)' if route_b else 'does not fire'}"
    )
    if route_a or route_b:
        print("\nVERDICT: I ex-ante — no solve is spent; stamp the cell with this run")
    else:
        print("\nVERDICT: LIVE — the pre-registered Phase 1 A/B (prereg §5) runs")
    print("=" * 78)
    print(json.dumps({"per_year": all_years_stats, "anchors": anchors}, indent=1))


if __name__ == "__main__":
    screen()
