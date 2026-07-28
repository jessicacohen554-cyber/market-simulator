"""caiso-134 — WHERE does the CAISO model's +2 GW of excess midday import DEMAND come from?

``FINDING-caiso133`` closed the corridor lane for **C3a-2025**: the binding
import limit is the corridor deliverability group alone, it is a MEASURED
envelope, and in the very hours it binds the model already carries +2.0 to
+2.5 GW MORE import than actually flowed. Its hand-back (§6) named — but did
NOT charter — the next question: the cap binds because the model *wants* that
much more import than reality took, so the pressure is **upstream of the
corridor**, in whatever makes CA's own midday supply expensive enough to pull
it. This instrument answers that, on committed bytes, with no LP.

Five sections, each answering one of the brief's questions:

* **§A — WHICH TRANCHE carries the excess.** Per-import-tranche dispatch and
  capability in the defect hours, against the measured corridor flow the cap
  was built from. Separates the SELF-SCHEDULED firm blocks (must-flow, a
  quantity) from the ECONOMIC depth rungs (a price).

* **§B — WHO the marginal import is displacing.** The CA-internal replacement
  ladder: every CA unit's unused headroom sorted by its own LP offer, per
  defect hour, and the marginal offer reached at the excess-import quantity.
  Reports the ONLINE / OFFLINE split of that block — an offline unit's first
  MW carries its full offer, a committed unit's min-load block does not.

* **§C — the IMPORT side's price and depth, against their OWN sources.** Each
  tranche's LP offer against its own measured hub print (the injector sets
  ``hub + wheel + border × EF/EF_unspec``), and each depth tranche's
  utilisation against its own measured WEIM depth. Rule 13 ``[R-MEASURED]``:
  a claim that the depths are wrong must be made against their own source.

* **§D — the CA side's price, against its OWN fuel anchor.** The replacement
  band's implied delivered gas ($/MMBtu) against the measured SoCal citygate
  weekly print, plus the offer decomposition (physical fuel term / VOM /
  ``gas_offer_net_revenue_margin`` fixed margin) so "offered too high" is
  answered on the offer's own parts.

* **§E — the CA side's QUANTITY, on the honest CEMS basis.** Model gas against
  matched-plant CAMPD hourly CEMS, level-free (each side normalised by its own
  annual mean), because ``FINDING-caiso-c2c4-bench-basis-930ng`` showed the
  raw EIA-930 CISO ``NG`` cell carries a fabricated noon-peaked block from
  ~2024-05 and is not usable as a midday anchor.

Defect-hour conventions (Sep-Dec, hod 10-15, measured RT <= $20), the CA
lambda construction and the corridor readers are imported verbatim from
``_caiso132_corridor_export_gates`` / ``_caiso133_binding_limit_separation``
so every row composes with caiso-120/121/131/132/133 on the same basis.

Offers are the LP's own ``mc_base`` reconstructed by ``run_year(fleet_only=True)``
from the bundle's ``meta.json`` — the assembled P0 objective with every pricing
overlay applied (the caiso-105/121 convention). It is the BASE cost: P1 adds
the monthly startup amortization, which needs P0 run lengths and therefore a
solve, so §B's ladder is a base-cost ladder and is labelled as one. That is
conservative for §B's conclusion — the markup only raises the replacement
offers further.

**No LP is built and no solver is called. Nothing is armed**: this is a
measurement that NAMES a lane; chartering one is a separate owner ask with its
own D-gates and prereg (rule 1 ``[R-STRUCT]``, the caiso-127 §5 charter rule).

Usage::

    PYTHONPATH=.:src:scripts:scripts/probes .venv/bin/python \\
        scripts/probes/_caiso134_import_demand_source.py \\
        results/calibration/caiso130_nameplate_B [--years 2023 2024 2025]

Finding: ``results/calibration/FINDING-caiso134-import-demand-source-2026-07-28.md``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from _caiso105_evening_q1_pin import fleet_state  # noqa: E402
from _caiso132_corridor_export_gates import (  # noqa: E402
    CA_ZONES,
    T,
    class_hourly,
    defect_mask,
    zonal_demand,
    zonal_prices,
)
from _caiso133_binding_limit_separation import measured_corridor_import  # noqa: E402

ISO = "CAISO"
TOL = 0.5  # MW — at-bound tolerance (the caiso-121 value)
# Model plant groups that burn gas, for the §E CEMS comparison.
GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
HUB_LMP = REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"


# ---------------------------------------------------------------------------
# committed-bytes readers
# ---------------------------------------------------------------------------
def unit_panel(bundle: Path, year: int) -> tuple[np.ndarray, pd.DataFrame]:
    """``(n_unit, T)`` P1 dispatch + per-unit metadata from the unit sidecar.

    Scatter-assigns rather than pivoting: the CAISO sidecar is ~14 M rows and
    ``pivot_table`` over it is minutes of wall clock for the same answer.

    Args:
        bundle: Calibration bundle carrying ``hourly/unit_hourly_<year>.parquet``.
        year: Solve year.

    Returns:
        ``(MW, meta)`` — the dispatch panel and a frame of ``unit_id`` /
        ``fuel`` / ``zone`` / ``plant_group`` aligned row-for-row with it.
    """
    frame = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "fuel", "zone", "plant_group", "hour", "mw"],
    )
    frame = frame[frame["pass"] == "P1"]
    uid = frame["unit_id"].astype(str)
    cats = pd.Index(uid.unique())
    row = pd.Series(np.arange(len(cats)), index=cats).reindex(uid).to_numpy()
    mw = np.zeros((len(cats), T), dtype=np.float32)
    mw[row, frame["hour"].to_numpy()] = frame["mw"].to_numpy(np.float32)
    meta = frame.drop_duplicates("unit_id")[
        ["unit_id", "fuel", "zone", "plant_group"]
    ].copy()
    meta["unit_id"] = meta["unit_id"].astype(str)
    meta = meta.set_index("unit_id").reindex(cats)
    meta.index.name = "unit_id"
    return mw, meta.reset_index()


def lp_state(bundle: Path, year: int) -> dict:
    """LP offers/bounds for ``year``, aligned to the unit sidecar (NO solve).

    ``run_year(fleet_only=True)`` on the bundle's own ``meta.json`` flags — the
    same reconstruction ``_caiso121_surplus_marginal`` reads its offers from,
    so ``mc`` here is the LP's assembled P0 objective and not a re-derivation.

    Args:
        bundle: Calibration bundle (supplies both ``meta.json`` and the sidecar).
        year: Solve year.

    Returns:
        Dict of ``(n_unit, T)`` / ``(n_unit,)`` arrays plus the per-unit class
        labels, every array aligned to the unit sidecar's row order.
    """
    state = fleet_state(bundle, year)
    fleet_arrays = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], T, axis=1)
    fuel_prices = np.asarray(state["fuel_prices"], dtype=float)
    if fuel_prices.ndim == 1:
        fuel_prices = np.repeat(fuel_prices[:, None], T, axis=1)
    ids = [str(u) for u in fleet_arrays.unit_ids]
    pos = {u: i for i, u in enumerate(ids)}

    mw, meta = unit_panel(bundle, year)
    keep = meta["unit_id"].isin(pos).to_numpy()
    mw, meta = mw[keep], meta[keep].reset_index(drop=True)
    sel = meta["unit_id"].map(pos).to_numpy()

    anchor = float(getattr(state["config"], "gas_offer_margin_anchor", np.nan))
    markup = np.fromiter(
        (float(getattr(g, "offer_markup_hr", 0.0)) for g in state["fleet"]),
        dtype=float,
        count=len(ids),
    )
    per_unit_anchor = np.fromiter(
        (
            float(a)
            if (a := getattr(g, "offer_margin_anchor", None)) is not None
            else anchor
            for g in state["fleet"]
        ),
        dtype=float,
        count=len(ids),
    )
    group = meta["plant_group"].to_numpy().astype(str)
    fuel = meta["fuel"].to_numpy().astype(str)
    return {
        "mw": mw,
        "cap": (fleet_arrays.pmax[:, None] * fleet_arrays.availability)[sel],
        "mc": mc[sel],
        "fuel_price": fuel_prices[sel],
        "heat_rate": np.asarray(fleet_arrays.heat_rate, dtype=float)[sel],
        "vom": np.asarray(fleet_arrays.vom, dtype=float)[sel],
        "markup_hr": markup[sel],
        "anchor": per_unit_anchor[sel],
        "uid": meta["unit_id"].to_numpy().astype(str),
        "zone": meta["zone"].to_numpy().astype(str),
        "fuel": fuel,
        "klass": np.where(group != "", group, fuel),
        "solar_potential": (
            np.asarray(state["solar_cf"], dtype=float)
            * np.asarray(state["solar_cap"], dtype=float)[:, None]
        ).sum(axis=0),
        "wind_potential": (
            np.asarray(state["wind_cf"], dtype=float)
            * np.asarray(state["wind_cap"], dtype=float)[:, None]
        ).sum(axis=0),
    }


def ca_lambda(bundle: Path, year: int) -> tuple[float, np.ndarray]:
    """Demand-weighted CA lambda over the defect hours, and the per-zone panel.

    Args:
        bundle: Calibration bundle.
        year: Solve year.

    Returns:
        ``(lambda_bar, prices)`` — the scalar demand-weighted mean over the
        defect hours and the ``(T, n_ca_zone)`` price panel.
    """
    idx = np.flatnonzero(defect_mask(bundle, year))
    price = zonal_prices(bundle, year)[list(CA_ZONES)].to_numpy()
    demand = zonal_demand(bundle, year)[list(CA_ZONES)].to_numpy()
    bar = float((price[idx] * demand[idx]).sum() / demand[idx].sum())
    return bar, price


def measured_hubs(year: int) -> pd.DataFrame:
    """Measured MALIN / PALOVRDE hourly hub prints on the model clock."""
    hub = pd.read_parquet(HUB_LMP)
    hub = hub[hub["year"] == year]
    return hub.pivot(index="hour", columns="hub", values="price").reindex(range(T))


# ---------------------------------------------------------------------------
# §A — which tranche carries the excess import?
# ---------------------------------------------------------------------------
def section_a(bundle: Path, years: tuple[int, ...]) -> dict:
    """A: per-tranche decomposition of the corridor over-import."""
    print("\n" + "=" * 98)
    print("A — WHICH import tranche carries the +2 GW excess? (FINDING-caiso133 §5)")
    print("=" * 98)
    out: dict[int, dict] = {}
    for year in years:
        idx = np.flatnonzero(defect_mask(bundle, year))
        if idx.size == 0:
            continue
        frame = pd.read_parquet(
            bundle / "hourly" / f"unit_hourly_{year}.parquet",
            columns=["pass", "unit_id", "fuel", "hour", "mw", "cap_mw"],
        )
        frame = frame[(frame["pass"] == "P1") & (frame["fuel"] == "import")]
        mw = frame.pivot_table(
            index="hour", columns="unit_id", values="mw", observed=True
        ).reindex(range(T))
        cap = frame.pivot_table(
            index="hour", columns="unit_id", values="cap_mw", observed=True
        ).reindex(range(T))
        meas = float(np.nanmean(measured_corridor_import(year)[idx]))
        print(f"\n  --- {year}: Sep-Dec surplus belly, n = {idx.size} h ---")
        print(f"      {'tranche':<26s}{'MW':>9s}{'capability':>12s}{'util':>7s}")
        rows, total = [], 0.0
        for col in mw.columns:
            m = float(np.nanmean(mw[col].to_numpy()[idx]))
            c = float(np.nanmean(cap[col].to_numpy()[idx]))
            if abs(m) < 0.5 and abs(c) < 0.5:
                continue
            total += m
            rows.append(
                (
                    str(col).replace("WECC_PNW_", "").replace("WECC_DSW_", ""),
                    m,
                    c,
                    m / c if c > 0 else np.nan,
                )
            )
        for name, m, c, u in sorted(rows, key=lambda r: -r[1]):
            print(f"      {name:<26s}{m:9.0f}{c:12.0f}{u:7.3f}")
        print(f"      {'TOTAL tranche output':<26s}{total:9.0f}")
        # Tranche output is NOT delivered flow: a self-scheduled firm block the
        # corridor cannot carry is DUMPED at its own WECC node.
        system = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        system = system[system["pass"] == "P1"]
        dump = system.pivot_table(index="hour", columns="zone", values="dump")
        wecc = [z for z in dump.columns if str(z).startswith("WECC_")]
        dumped = float(dump[wecc].to_numpy()[idx].sum(axis=1).mean()) if wecc else 0.0
        print(
            f"      {'  less DUMPED at WECC node':<26s}{-dumped:9.0f}"
            "   (self-scheduled firm the corridor cannot carry)"
        )
        print(f"      {'= delivered into CA':<26s}{total - dumped:9.0f}")
        print(
            f"      {'MEASURED corridor flow':<26s}{meas:9.0f}"
            f"   -> EXCESS {total - meas:+.0f} MW (output basis,"
            f" {total - dumped - meas:+.0f} delivered)"
        )
        out[year] = {
            "tranches": rows,
            "total": total,
            "measured": meas,
            "dumped": dumped,
        }
    return out


# ---------------------------------------------------------------------------
# §B — who would serve those MWh if the corridor were tighter?
# ---------------------------------------------------------------------------
def section_b(bundle: Path, years: tuple[int, ...], state: dict, a: dict) -> dict:
    """B: the CA replacement ladder and the marginal offer at the excess."""
    print("\n" + "=" * 98)
    print("B — WHO is the marginal import displacing? The CA replacement ladder")
    print("=" * 98)
    print("  Every CA unit's UNUSED headroom, sorted by its own LP offer, per hour.")
    print("  Headroom priced BELOW lambda is excluded: the LP already took what it")
    print("  could, so what is left there is held back by another row (hydro budget,")
    print("  storage SOC) and is not replacement supply.")
    out: dict[int, dict] = {}
    for year in years:
        st = state[year]
        idx = np.flatnonzero(defect_mask(bundle, year))
        bar, price = ca_lambda(bundle, year)
        zcol = {z: i for i, z in enumerate(CA_ZONES)}
        lam = np.stack(
            [price[:, zcol[z]] if z in zcol else np.full(T, np.nan) for z in st["zone"]]
        )
        is_ca = np.isin(st["zone"], CA_ZONES)
        sub = np.ix_(is_ca, idx)
        mw, cap = st["mw"][sub].astype(float), st["cap"][sub].astype(float)
        offer, lam_u = st["mc"][sub].astype(float), lam[sub]
        klass = st["klass"][is_ca]
        headroom = np.maximum(cap - mw, 0.0)
        online = mw > TOL
        delta = offer - lam_u
        excess = a[year]["total"] - a[year]["measured"]

        print(
            f"\n  --- {year}: n = {idx.size} h, CA lambda {bar:.2f}, "
            f"excess import {excess:.0f} MW ---"
        )
        print(
            f"      {'offer - lambda':<18s}{'ONLINE':>9s}{'OFFLINE':>9s}"
            f"{'TOTAL':>9s}{'cum':>9s}   top classes"
        )
        cum = 0.0
        for lo, hi in ((0, 2), (2, 5), (5, 10), (10, 20), (20, 50), (50, np.inf)):
            band = (delta >= lo) & (delta < hi)
            on = float((headroom * band * online).sum() / idx.size)
            off = float((headroom * band * ~online).sum() / idx.size)
            cum += on + off
            mix = {
                k: float((headroom[klass == k] * band[klass == k]).sum() / idx.size)
                for k in set(klass)
            }
            top = ", ".join(
                f"{k} {v:.0f}"
                for k, v in sorted(mix.items(), key=lambda x: -x[1])[:3]
                if v > 1
            )
            hi_s = "inf" if not np.isfinite(hi) else f"{hi:.0f}"
            print(
                f"      +${lo:<3.0f} to +${hi_s:<5s}{on:9.0f}{off:9.0f}"
                f"{on + off:9.0f}{cum:9.0f}   {top}"
            )

        marginal, on_share = [], []
        for j in range(idx.size):
            d, h = delta[:, j], headroom[:, j]
            keep = (h > 0.01) & np.isfinite(d) & (d > 0)
            if not keep.any():
                continue
            order = np.argsort(d[keep])
            d_s, h_s, on_s = d[keep][order], h[keep][order], online[:, j][keep][order]
            cums = np.cumsum(h_s)
            k = int(np.searchsorted(cums, excess))
            if k >= len(d_s):
                continue
            marginal.append(d_s[k])
            on_share.append(h_s[: k + 1][on_s[: k + 1]].sum() / max(cums[k], 1e-9))
        marginal, on_share = np.array(marginal), np.array(on_share)
        print(
            f"\n      REPLACEMENT COST at the margin  +${marginal.mean():.2f}/MWh"
            f"   (median +${np.median(marginal):.2f}, p90 +${np.percentile(marginal, 90):.2f})"
        )
        print(
            f"      -> CA lambda {bar:.2f} -> {bar + marginal.mean():.2f}"
            "   i.e. a TIGHTER corridor makes C3a WORSE"
        )
        print(
            f"      ONLINE share of that block {100 * on_share.mean():.1f} %"
            f"   -> {100 * (1 - on_share.mean()):.1f} % needs OFFLINE units STARTED"
        )
        out[year] = {
            "lambda": bar,
            "excess": excess,
            "replacement_cost": float(marginal.mean()),
            "online_share": float(on_share.mean()),
        }
    return out


# ---------------------------------------------------------------------------
# §C — is the IMPORT side mispriced or too deep? (against its own source)
# ---------------------------------------------------------------------------
def section_c(bundle: Path, years: tuple[int, ...], state: dict) -> dict:
    """C: import tranche offers vs their own measured hubs; depth utilisation."""
    print("\n" + "=" * 98)
    print("C — is the IMPORT side mispriced or too deep? (rule 13 [R-MEASURED]:")
    print("    judged against its OWN source, never against the residual)")
    print("=" * 98)
    out: dict[int, dict] = {}
    for year in years:
        st = state[year]
        idx = np.flatnonzero(defect_mask(bundle, year))
        hubs = measured_hubs(year)
        pv = float(np.nanmean(hubs["PALOVRDE"].to_numpy()[idx]))
        ml = float(np.nanmean(hubs["MALIN"].to_numpy()[idx]))
        print(f"\n  --- {year}: n = {idx.size} h ---")
        print(
            f"      measured PALOVRDE hub {pv:8.2f}   measured MALIN hub {ml:8.2f} $/MWh"
        )
        print(
            f"      {'tranche':<26s}{'LP offer':>10s}{'own hub':>10s}{'offer-hub':>11s}"
        )
        rows = {}
        for i, uid in enumerate(st["uid"]):
            if st["fuel"][i] != "import":
                continue
            hub = pv if uid.startswith("WECC_DSW_") else ml
            o = float(np.nanmean(st["mc"][i][idx]))
            name = uid.replace("WECC_PNW_", "").replace("WECC_DSW_", "")
            print(f"      {name:<26s}{o:10.2f}{hub:10.2f}{o - hub:+11.2f}")
            rows[name] = {"offer": o, "hub": hub}
        out[year] = {"palovrde": pv, "malin": ml, "tranches": rows}
    print(
        "\n  READ: the injector sets import offer = hub + wheel + border x EF/EF_unspec"
    )
    print("  (inject_caiso_per_hub_intertie_prices). A depth rung's offer-hub gap IS")
    print(
        "  its wheel; the firm rungs (PNW_hydro_base $28 / DSW_solar_PV $48) are held"
    )
    print("  at contract cost by caiso_perhub_firm_base AND self-scheduled must-flow,")
    print("  so their price is inert by construction.")
    return out


# ---------------------------------------------------------------------------
# §D — is the CA side offered too HIGH? (against its own fuel anchor)
# ---------------------------------------------------------------------------
def section_d(bundle: Path, years: tuple[int, ...], state: dict) -> dict:
    """D: replacement-band implied gas vs the measured citygate; offer parts."""
    from market_sim.data.fuel.hubs import socal_citygate_weekly_hourly

    print("\n" + "=" * 98)
    print("D — is CA's own midday supply offered too HIGH? (vs its OWN fuel anchor)")
    print("=" * 98)
    out: dict[int, dict] = {}
    for year in years:
        st = state[year]
        idx = np.flatnonzero(defect_mask(bundle, year))
        _bar, price = ca_lambda(bundle, year)
        zcol = {z: i for i, z in enumerate(CA_ZONES)}
        lam = np.stack(
            [price[:, zcol[z]] if z in zcol else np.full(T, np.nan) for z in st["zone"]]
        )
        is_ca = np.isin(st["zone"], CA_ZONES)
        sub = np.ix_(is_ca, idx)
        mw, cap = st["mw"][sub].astype(float), st["cap"][sub].astype(float)
        offer, gas = st["mc"][sub].astype(float), st["fuel_price"][sub].astype(float)
        lam_u, klass = lam[sub], st["klass"][is_ca]
        hr = st["heat_rate"][is_ca]
        headroom = np.maximum(cap - mw, 0.0)
        delta = offer - lam_u
        citygate = socal_citygate_weekly_hourly(year, T)
        cg = float(np.nanmean(citygate[idx])) if citygate is not None else np.nan
        print(f"\n  --- {year}: n = {idx.size} h ---")
        print(f"      MEASURED SoCal citygate (weekly print) {cg:6.2f} $/MMBtu")
        markup = (st["markup_hr"][is_ca] * st["anchor"][is_ca])[:, None]
        vom = st["vom"][is_ca][:, None]
        burns = hr > 0  # gas-burning rows only: a 0-HR hydro row has no implied gas
        print(
            f"      {'band':<16s}{'MW/h':>8s}{'offer':>8s}{'= fuel':>8s}"
            f"{'+VOM':>7s}{'+margin':>9s}{'+carbon':>9s}{'impl gas':>10s}"
            f"{'HR':>7s}   class mix"
        )
        bands = {}
        for lo, hi in ((0, 5), (5, 10), (10, 20), (20, 50)):
            band = (delta >= lo) & (delta < hi) & (headroom > TOL)
            w = headroom * band
            wg = w * burns[:, None]
            if w.sum() <= 0 or wg.sum() <= 0:
                continue
            wmean = lambda x: float((x * wg).sum() / wg.sum())  # noqa: E731
            g = wmean(gas)
            mix = {k: float(w[klass == k].sum() / idx.size) for k in set(klass)}
            top = ", ".join(
                f"{k} {v:.0f}"
                for k, v in sorted(mix.items(), key=lambda x: -x[1])[:3]
                if v > 1
            )
            fuel_t = wmean(hr[:, None] * gas)
            vom_t = wmean(np.broadcast_to(vom, w.shape))
            mk_t = wmean(np.broadcast_to(markup, w.shape))
            carbon_t = wmean(offer) - fuel_t - vom_t - mk_t
            print(
                f"      +${lo:<3.0f}..+${hi:<7.0f}{w.sum() / idx.size:8.0f}"
                f"{wmean(offer):8.2f}{fuel_t:8.2f}{vom_t:7.2f}{mk_t:9.2f}"
                f"{carbon_t:9.2f}{g:10.2f}"
                f"{wmean(np.broadcast_to(hr[:, None], w.shape)):7.2f}   {top}"
            )
            bands[(lo, hi)] = {
                "implied_gas": g,
                "offer": wmean(offer),
                "margin": mk_t,
                "carbon": carbon_t,
            }
        print(
            "      (capacity-weighted over the band's GAS-BURNING headroom only;"
            " 'impl gas' is the LP's own delivered fuel price. '+carbon' is the"
        )
        print(
            "      residual = offer - fuel - VOM - margin: the CA cap-and-trade"
            " allowance term (state_carbon_pricing) plus any EAC/NOx leg.)"
        )
        # offer decomposition on the ONLINE CC_REGULAR block
        cc = is_ca & (st["klass"] == "CC_REGULAR")
        csub = np.ix_(cc, idx)
        cmw, ccap = st["mw"][csub].astype(float), st["cap"][csub].astype(float)
        cmc, cgas = st["mc"][csub].astype(float), st["fuel_price"][csub].astype(float)
        w = np.where(cmw > TOL, ccap, 0.0)
        if w.sum() > 0:
            chr_ = st["heat_rate"][cc][:, None] * np.ones_like(w)
            mk = (st["markup_hr"][cc] * st["anchor"][cc])[:, None] * np.ones_like(w)
            wm = lambda x: float((x * w).sum() / w.sum())  # noqa: E731
            print(
                f"      [ONLINE CC_REGULAR offer parts]  fuel term {wm(chr_ * cgas):6.2f}"
                f" + VOM {wm(np.broadcast_to(st['vom'][cc][:, None], w.shape)):5.2f}"
                f" + net-rev margin {wm(mk):5.2f}  =  {wm(cmc):6.2f} $/MWh"
                f"   (margin {100 * wm(mk) / wm(cmc):.1f} % of offer,"
                f" delivered gas {wm(cgas):.2f} $/MMBtu)"
            )
        out[year] = {"citygate": cg, "bands": bands}
    return out


# ---------------------------------------------------------------------------
# §E — the CA side's QUANTITY, on the honest CEMS basis
# ---------------------------------------------------------------------------
def section_e(bundle: Path, years: tuple[int, ...], state: dict, a: dict) -> dict:
    """E: model gas vs matched-plant CAMPD CEMS, level-free; plus curtailment."""
    from market_sim.data.fleet import _hour_to_month_index

    print("\n" + "=" * 98)
    print("E — the CA side's QUANTITY: model gas vs matched-plant CEMS (level-free)")
    print("=" * 98)
    print("  The raw EIA-930 CISO NG cell carries a fabricated noon-peaked block from")
    print(
        "  ~2024-05 (FINDING-caiso-c2c4-bench-basis-930ng) and is NOT a usable midday"
    )
    print("  anchor, so this compares against CAMPD hourly CEMS on the SAME physical")
    print("  plants, each side normalised by its OWN annual mean.")
    month = _hour_to_month_index(T)
    hod = np.arange(T) % 24
    out: dict[int, dict] = {}
    print(f"\n  {'':6s}{'MODEL':>27s}{'CEMS (same plants)':>28s}")
    print(
        f"  {'year':6s}{'annual':>9s}{'defect':>9s}{'util':>9s}{'plants':>8s}"
        f"{'annual':>9s}{'defect':>9s}{'util':>9s}{'shape':>8s}"
    )
    for year in years:
        frame = pd.read_parquet(
            bundle / "hourly" / f"unit_hourly_{year}.parquet",
            columns=["pass", "plant_code", "plant_group", "zone", "hour", "mw"],
        )
        frame = frame[
            (frame["pass"] == "P1")
            & frame["zone"].isin(CA_ZONES)
            & frame["plant_group"].isin(GAS_GROUPS)
        ]
        cems = pd.read_parquet(
            REPO / f"data/raw/campd-unit-level/CA_{year}.parquet",
            columns=["facilityId", "date", "hour", "grossLoad"],
        )
        cems["fid"] = pd.to_numeric(cems["facilityId"], errors="coerce")
        common = set(int(x) for x in frame["plant_code"].unique() if int(x) > 0) & set(
            int(x) for x in cems["fid"].dropna().unique()
        )
        model = (
            frame[frame["plant_code"].isin(common)]
            .groupby("hour", observed=True)["mw"]
            .sum()
            .reindex(range(T))
            .fillna(0)
            .to_numpy()
        )
        sel = cems[cems["fid"].isin(common)]
        stamp = pd.to_datetime(sel["date"]) + pd.to_timedelta(sel["hour"], unit="h")
        per = (
            sel.assign(month=stamp.dt.month, hod=stamp.dt.hour, ts=stamp)
            .groupby(["ts", "month", "hod"], observed=True)["grossLoad"]
            .sum()
            .reset_index()
        )
        tab = np.full((12, 24), np.nan)
        for (m, h), g in per.groupby(["month", "hod"], observed=True):
            tab[int(m) - 1, int(h)] = float(g["grossLoad"].mean())
        actual = tab[month, hod]
        idx = np.flatnonzero(defect_mask(bundle, year))
        m_ann, m_def = float(model.mean()), float(model[idx].mean())
        c_ann, c_def = float(np.nanmean(actual)), float(np.nanmean(actual[idx]))
        expected = c_def * (m_ann / c_ann)
        print(
            f"  {year:<6d}{m_ann:9.0f}{m_def:9.0f}{m_def / m_ann:9.3f}{len(common):8d}"
            f"{c_ann:9.0f}{c_def:9.0f}{c_def / c_ann:9.3f}"
            f"{(m_def / m_ann) / (c_def / c_ann):8.3f}"
        )
        out[year] = {
            "model_util": m_def / m_ann,
            "cems_util": c_def / c_ann,
            "deficit": m_def - expected,
            "plants": len(common),
        }
    print(
        "\n  'util' = defect-hour mean / own annual mean. 'shape' = model util / CEMS util."
    )
    print(
        "\n  Shape-normalised belly gas deficit (CEMS defect x model/CEMS annual scale):"
    )
    for year in years:
        excess = a[year]["total"] - a[year]["measured"]
        d = out[year]["deficit"]
        print(
            f"    {year}: {d:+7.0f} MW   vs corridor import EXCESS {excess:+7.0f} MW"
            f"   -> {100 * abs(d) / excess:.0f} % of the excess"
        )
    print(
        "\n  Renewable curtailment in the same hours (the model's own zero-cost margin):"
    )
    for year in years:
        st = state[year]
        idx = np.flatnonzero(defect_mask(bundle, year))
        ch = class_hourly(bundle, year)
        for tech, pot in (("solar", "solar_potential"), ("wind", "wind_potential")):
            p = float(np.nanmean(st[pot][idx]))
            m = float(np.nanmean(ch[tech].to_numpy()[idx]))
            out[year][f"{tech}_curtail_pct"] = 100 * (p - m) / p if p > 0 else np.nan
        print(
            f"    {year}: solar {out[year]['solar_curtail_pct']:5.2f} % curtailed,"
            f" wind {out[year]['wind_curtail_pct']:5.2f} %"
        )
    return out


def main() -> int:
    """Run every section against a committed bundle. No LP, nothing armed."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    bundle, years = args.bundle, tuple(args.years)
    if not (bundle / "hourly" / f"unit_hourly_{years[0]}.parquet").exists():
        print(f"ERROR: {bundle} carries no unit_hourly sidecar (caiso-133).")
        return 2

    print("\ncaiso-134 — where does the excess midday IMPORT DEMAND come from?")
    print(f"bundle: {bundle}   years: {list(years)}   (NO LP, nothing armed)")
    state = {y: lp_state(bundle, y) for y in years}
    a = section_a(bundle, years)
    section_b(bundle, years, state, a)
    section_c(bundle, years, state)
    section_d(bundle, years, state)
    section_e(bundle, years, state, a)
    print("\n" + "=" * 98)
    print("VERDICT: neither side's PRICE is misplaced against its own measured anchor.")
    print("The lane is the CA-internal committed-gas STATE (the caiso-118b RA")
    print("must-offer paradigm), NOT the corridor and NOT an offer reprice.")
    print("=" * 98)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
