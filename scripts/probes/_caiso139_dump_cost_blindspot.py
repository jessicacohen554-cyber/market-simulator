"""caiso-139 — the dump-cost blind spot: charter instrument (NO SOLVE).

Answers the caiso-139 charter's central question — *what is the structurally
correct dump price when priced-import tranches with measured-hub (possibly
deeply negative) MCs share a node with the Dump variable* — entirely from the
caiso-138 keeper's committed ``hourly/`` sidecars and a
``run_year(fleet_only=True)`` reconstruction of the LP's own offer arrays
(``mc_base``). No LP is built beyond the fleet stage and no solver is called.

The defect (caiso-138 §B, β): ``model/lp/costs.py::build_cost_vector`` sets

    min_renewable_mc = min(0, min wind_mc, min solar_mc, −storage_eac)
    dump_cost        = max(ε, −min_renewable_mc + ε)

so the guard's domain is the renewable/storage credit set ONLY. Any generator
row whose ``mc`` sits below ``−dump_cost`` can generate purely to dump at a
profit of ``−mc − dump_cost`` per MWh. The CAISO per-hub import tranches are
priced at their own measured hub (``inject_caiso_per_hub_intertie_prices``:
``mc = hub + wheel + carbon + ε``), and the Palo Verde hub crashes deeply
negative in the desert-SW solar glut — below the guard.

Sections:

* **§A — D1 quantify.** Per year × node: the dump on the NEW keeper
  (``caiso138_envclip_B``), the node λ, and the per-tranche output inside the
  dump hours (which tranche is doing the gaming).
* **§B — D2 attribute.** Reconstruct the LP's own ``mc_base`` and the exact
  ``dump_cost`` the objective carried; then, per dump hour, test the
  identity *∃ a producible row at that node with* ``mc < −dump_cost`` — and
  count the dump hours with NO such row (the residual, un-attributed dump).
* **§C — D3 pre-check.** The CA-side invariance argument on committed bytes:
  CA-zone dump census, CA-zone λ vs ``−dump_cost``, and the corridor
  flow-at-cap census inside the β hours — the three facts that make the E1/E2
  prediction analytic rather than a guess.
* **§D — D4 provenance.** The repaired guard's value per year, derived from
  the model's own offer arrays, with the producible-row mask (export sinks
  have ``pmax = 0`` and a negative ``mc`` that is a *willingness-to-pay*, not
  a production credit — including them would inflate the guard).
* **§E — cross-ISO reach (rule 25).** ``dump_cost`` is ISO-agnostic LP
  infrastructure. For EVERY ISO keeper: the guard it carried, the most
  negative producible offer, and whether the repair would move that ISO's
  objective at all.

Usage::

    PYTHONPATH=.:src:scripts:scripts/probes .venv/bin/python \
        scripts/probes/_caiso139_dump_cost_blindspot.py \
        results/calibration/caiso138_envclip_B
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _caiso105_evening_q1_pin import fleet_state as _fleet_state  # noqa: E402


def fleet_state(bundle, year, **overrides):
    """``_caiso105_evening_q1_pin.fleet_state`` with run_year kwarg overrides.

    ``overrides`` ride the generic ``prb_overrides`` ScenarioConfig channel, the
    same seam ``replay_keeper.py --set`` uses, so a reconstruction can disable
    one layer (PJM's virtual-bid source is absent in this container) without
    editing the keeper's meta.
    """
    if not overrides:
        return _fleet_state(bundle, year)
    import json as _json

    meta_path = bundle / "meta.json"
    original = meta_path.read_text()
    meta = _json.loads(original)
    prb = dict(meta.get("prb_overrides") or {})
    prb.update(overrides)
    meta["prb_overrides"] = prb
    meta.update(overrides)
    try:
        meta_path.write_text(_json.dumps(meta))
        return _fleet_state(bundle, year)
    finally:
        meta_path.write_text(original)


YEARS = (2023, 2024, 2025)
CA_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")
WECC_ZONES = ("WECC_PNW", "WECC_DSW")
# corridor → (link name, group row) as the keeper's network sidecar names them
CORRIDOR_LINK = {
    "WECC_PNW": ("WECC_PNW>NP15", "grp:+WECC_PNW>NP15"),
    "WECC_DSW": ("WECC_DSW>SP15_rest", "grp:+WECC_DSW>SP15_rest"),
}
# All ISO keepers (frontend/data/backcast/keepers/<ISO>.json → registry bundle)
KEEPER_BUNDLES = {
    "CAISO": "results/calibration/caiso138_envclip_B",
    "ERCOT": "results/calibration/ercot137_margin_arm",
    "MISO": "results/calibration/miso101_tempgrain_B",
    "NEISO": "results/calibration/neiso61_netrev_margin",
    "NYISO": "results/calibration/nyiso96_ctamort",
    "PJM": "results/calibration/pjm137_ctheatrate_B",
}


# ---------------------------------------------------------------------------
# committed-bytes readers
# ---------------------------------------------------------------------------
def _system(bundle: Path, year: int) -> pd.DataFrame:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return s[s["pass"] == "P1"]


def _network(bundle: Path, year: int) -> pd.DataFrame:
    f = bundle / "hourly" / f"network_{year}.parquet"
    if not f.exists():
        return pd.DataFrame()
    n = pd.read_parquet(f)
    return n[n["pass"] == "P1"]


def _unit_hourly(bundle: Path, year: int, zones: list[str]) -> pd.DataFrame:
    f = bundle / "hourly" / f"unit_hourly_{year}.parquet"
    if not f.exists():
        return pd.DataFrame()
    u = pd.read_parquet(
        f,
        columns=["unit_id", "pass", "zone", "hour", "mw", "cap_mw"],
        filters=[("zone", "in", zones)],
    )
    return u[u["pass"] == "P1"]


# ---------------------------------------------------------------------------
# the LP's own guard, reconstructed exactly
# ---------------------------------------------------------------------------
def _credit_bound(state: dict) -> tuple[float, float, float]:
    """``(wind_mc_min, solar_mc_min, −storage_eac)`` as the objective saw them.

    Mirrors ``run_calibration.run_year``'s chain: IRA dispatch credits →
    EAC subtraction → ``apply_negative_renewable_offer_floor``. These are the
    three series ``build_cost_vector``'s ``min_renewable_mc`` is taken over.
    """
    from market_sim.policy.eac import (
        apply_negative_renewable_offer_floor,
        compute_eac_dispatch_credits,
    )
    from market_sim.policy.ira import compute_dispatch_credits

    config = state["config"]
    year = int(config.weather_year)
    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    if getattr(config, "wind_ptc_vintage_offers", False):
        from market_sim.data.offer_curves import wind_ptc_vintage_dispatch_offer

        v = wind_ptc_vintage_dispatch_offer(config, year)
        if v is not None:
            wind_mc = v
    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    wind_mc = wind_mc - wind_eac
    solar_mc = solar_mc - solar_eac
    wind_mc, solar_mc = apply_negative_renewable_offer_floor(wind_mc, solar_mc, config)
    return (
        float(np.min(np.asarray(wind_mc, dtype=float))),
        float(np.min(np.asarray(solar_mc, dtype=float))),
        -float(storage_eac),
    )


def guard_state(state: dict) -> dict:
    """Current and repaired guard, plus the producible-row offer census.

    ``mc_base`` is the assembled P0 objective the bundle solved on (fuel + VOM
    + carbon + NOx + EAC + every pricing overlay, incl. the measured per-hub
    import prices). P1's mc is ``mc_base`` plus a NON-NEGATIVE amortized
    startup markup, so ``min mc_P1 ≥ min mc_P0`` — reading the guard off
    ``mc_base`` is exact for the rows that carry no markup (imports do not)
    and conservative elsewhere.
    """
    from market_sim.config.constants import STORAGE_TIEBREAKER_EPSILON as EPS

    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    w_min, s_min, neg_eac = _credit_bound(state)
    cur_min = min(0.0, w_min, s_min, neg_eac)
    cur = max(EPS, -cur_min + EPS)

    # Producible rows only. Export sinks are built with pmax = 0, pmin = −cap
    # (import_nodes.build_export_sinks): their NEGATIVE mc is the neighbour's
    # willingness-to-pay on a *withdrawal*, not a production credit — such a
    # row can never generate-to-dump, so it must stay outside the guard.
    pmax = np.asarray(fa.pmax, dtype=float)
    can_inject = pmax > 0.0
    mc_inj = mc[can_inject]
    row_min = mc_inj.min(axis=1) if mc_inj.size else np.array([])
    rep_min = min(cur_min, float(row_min.min()) if row_min.size else 0.0)
    rep = max(EPS, -rep_min + EPS)
    ids = np.asarray([str(u) for u in fa.unit_ids])[can_inject]
    below = np.where(row_min < -cur)[0]
    return {
        "eps": EPS,
        "wind_min": w_min,
        "solar_min": s_min,
        "neg_eac": neg_eac,
        "current": cur,
        "repaired": rep,
        "mc": mc,
        "can_inject": can_inject,
        "unit_ids": ids,
        "row_min": row_min,
        "below_rows": below,
        "below_ids": ids[below],
        "n_sink_rows": int((pmax <= 0.0).sum()),
        "sink_mc_min": float(mc[~can_inject].min()) if (~can_inject).any() else np.nan,
    }


# ---------------------------------------------------------------------------
# §A — D1 quantify
# ---------------------------------------------------------------------------
def section_a(bundle: Path) -> dict:
    print("=" * 96)
    print("§A — D1: the residual (β) dump on the caiso-138 keeper, per node and tranche")
    print("=" * 96)
    out = {}
    for year in YEARS:
        sysf = _system(bundle, year)
        uh = _unit_hourly(bundle, year, list(WECC_ZONES))
        print(f"\n--- {year} ---")
        for zone in WECC_ZONES:
            z = sysf[sysf["zone"] == zone].sort_values("hour")
            dump = z["dump"].to_numpy()
            price = z["price"].to_numpy()
            dh = dump > 1e-6
            print(
                f"  {zone}: dump {dump.sum() / 1e6:.4f} TWh in {int(dh.sum())} h "
                f"(mean|>0 {dump[dh].mean() if dh.any() else 0.0:.1f} MW, "
                f"max {dump.max():.1f}); node λ in dump hrs: "
                f"median {np.median(price[dh]) if dh.any() else float('nan'):.3f}"
            )
            out[(year, zone)] = {
                "dump": dump,
                "dh": dh,
                "price": price,
                "twh": float(dump.sum() / 1e6),
            }
            if not dh.any() or uh.empty:
                continue
            u = uh[uh["zone"] == zone]
            piv = u.pivot_table(
                index="hour", columns="unit_id", values="mw", aggfunc="sum"
            ).reindex(range(len(dump)), fill_value=0.0)
            inside = piv.to_numpy()[dh]
            tot = inside.sum(axis=0) / 1e6
            order = np.argsort(-tot)
            names = list(piv.columns)
            top = [
                f"{names[i].removeprefix(zone + '_')} {tot[i]:.4f}"
                for i in order[:4]
                if tot[i] > 1e-6
            ]
            print(f"     tranche output inside those hours (TWh): {', '.join(top)}")
    return out


# ---------------------------------------------------------------------------
# §B — D2 attribute
# ---------------------------------------------------------------------------
def section_b(bundle: Path, a: dict) -> dict:
    print("\n" + "=" * 96)
    print("§B — D2: every dump hour carries a producible offer below −dump_cost")
    print("=" * 96)
    out = {}
    for year in YEARS:
        state = fleet_state(bundle, year)
        g = guard_state(state)
        mc, ids = g["mc"], g["unit_ids"]
        mc_inj = mc[g["can_inject"]]
        # FleetArrays carries zone_idx, not names; the WECC pseudo-node rows are
        # unambiguously prefixed with their zone (build_caiso_per_hub_intertie),
        # the same identification the caiso-138 probe used.
        zone_of = np.asarray(
            [
                next((z for z in WECC_ZONES if u.startswith(z + "_")), "")
                for u in ids
            ]
        )
        print(
            f"\n--- {year} ---  dump_cost = {g['current']:.6f} "
            f"(from wind {g['wind_min']:.3f} / solar {g['solar_min']:.3f} / "
            f"−eac {g['neg_eac']:.3f}); rows below −dump_cost: "
            f"{len(g['below_ids'])} → {list(g['below_ids'])}"
        )
        for zone in WECC_ZONES:
            rec = a[(year, zone)]
            dh = rec["dh"]
            if not dh.any():
                print(f"  {zone}: no dump hours")
                continue
            sel = zone_of == zone
            gamed = mc_inj[sel] < -g["current"]  # (rows_at_zone, T)
            have = gamed.any(axis=0)
            n_with = int((dh & have).sum())
            n_without = int((dh & ~have).sum())
            # energy the gamed rows produced inside the dump hours
            gamed_rows = np.where(sel)[0][gamed.any(axis=1)]
            names = ids[gamed_rows]
            print(
                f"  {zone}: dump hours WITH a gamed offer {n_with}/{int(dh.sum())}; "
                f"WITHOUT {n_without}; gamed rows at node: "
                f"{[n.removeprefix(zone + '_') for n in names]}"
            )
            deepest = mc_inj[sel][gamed].min() if gamed.any() else np.nan
            print(
                f"     deepest offer at node {deepest:.3f} $/MWh "
                f"(margin below the guard: {-g['current'] - deepest:.3f}); "
                f"gaming profit at that offer "
                f"{-deepest - g['current']:.3f} $/MWh"
            )
            out[(year, zone)] = {"with": n_with, "without": n_without}
        # the converse: hours where a gamed offer exists but no dump
        for zone in WECC_ZONES:
            rec = a[(year, zone)]
            sel = zone_of == zone
            if not sel.any():
                continue
            have = (mc_inj[sel] < -g["current"]).any(axis=0)
            print(
                f"  {zone}: gamed-offer hours {int(have.sum())}, of which dumping "
                f"{int((have & rec['dh']).sum())} (the rest deliver into the "
                f"corridor instead of dumping)"
            )
        out[year] = g
    return out


# ---------------------------------------------------------------------------
# §C — D3 pre-check
# ---------------------------------------------------------------------------
def section_c(bundle: Path, a: dict, b: dict) -> None:
    print("\n" + "=" * 96)
    print("§C — D3: the CA-side invariance facts (committed bytes)")
    print("=" * 96)
    for year in YEARS:
        sysf = _system(bundle, year)
        net = _network(bundle, year)
        g = b[year]
        print(f"\n--- {year} --- (dump_cost {g['current']:.3f} → {g['repaired']:.3f})")
        ca = sysf[sysf["zone"].isin(CA_ZONES)]
        print(
            f"  CA zones: dump {ca['dump'].sum():.6f} MWh total, "
            f"{int((ca['dump'] > 1e-6).sum())} zone-hours > 0; "
            f"min λ {ca['price'].min():.4f} vs −dump_cost "
            f"{-g['current']:.4f} (repaired {-g['repaired']:.4f}); "
            f"zone-hours at λ ≤ −dump_cost+0.01: "
            f"{int((ca['price'] <= -g['current'] + 0.01).sum())}"
        )
        for zone in WECC_ZONES:
            rec = a[(year, zone)]
            dh = rec["dh"]
            if not dh.any() or net.empty:
                continue
            link, grp = CORRIDOR_LINK[zone]
            cap = (
                net[(net["kind"] == "group") & (net["name"] == grp)]
                .sort_values("hour")["limit_up"]
                .to_numpy()
            )
            flow = (
                net[(net["kind"] == "link") & (net["name"] == link)]
                .sort_values("hour")["mw"]
                .to_numpy()
            )
            n = min(len(cap), len(flow), len(dh))
            at_cap = np.abs(flow[:n] - cap[:n]) < 1e-3
            print(
                f"  {zone}: inside its {int(dh[:n].sum())} dump hours the corridor "
                f"flow is AT CAP in {int((dh[:n] & at_cap).sum())} "
                f"({(dh[:n] & at_cap).sum() / max(dh[:n].sum(), 1):.1%}); "
                f"below cap in {int((dh[:n] & ~at_cap).sum())}"
            )
    print(
        "\n  Prediction basis: the Dump column's reduced cost is dump_cost + λ_z."
        "\n  Where a CA zone never dumps AND its λ sits strictly above −dump_cost,"
        "\n  RAISING dump_cost only raises that column's reduced cost — it stays"
        "\n  non-basic, so the CA primal and every CA dual are unchanged. The only"
        "\n  rows that move are the gamed import tranches at the WECC pseudo-nodes,"
        "\n  and their corridor delivery is cap-bound in the same hours."
    )


# ---------------------------------------------------------------------------
# §D — D4 provenance
# ---------------------------------------------------------------------------
def section_d(b: dict) -> None:
    print("\n" + "=" * 96)
    print("§D — D4: the repaired guard is read off the model's own offer arrays")
    print("=" * 96)
    print(
        f"  {'year':6s}{'current':>10s}{'repaired':>10s}{'driver row':>34s}"
        f"{'row min mc':>12s}{'sink rows':>11s}{'sink mc min':>12s}"
    )
    for year in YEARS:
        g = b[year]
        i = int(np.argmin(g["row_min"])) if g["row_min"].size else -1
        print(
            f"  {year:<6d}{g['current']:10.4f}{g['repaired']:10.4f}"
            f"{(g['unit_ids'][i] if i >= 0 else '—'):>34s}"
            f"{(g['row_min'][i] if i >= 0 else float('nan')):12.4f}"
            f"{g['n_sink_rows']:11d}{g['sink_mc_min']:12.4f}"
        )
    print(
        "\n  Zero DOF: every input is an offer series the LP already carries. No"
        "\n  threshold, percentile, margin or residual-tuned value enters. The"
        "\n  producible mask (pmax > 0) is a structural property of the row, not a"
        "\n  parameter — note the sink mc min column: those rows are negative-mc"
        "\n  WITHDRAWALS and would inflate the guard if the mask were dropped."
    )


# ---------------------------------------------------------------------------
# §E — cross-ISO reach (rule 25)
# ---------------------------------------------------------------------------
def section_e(iso_only: str | None = None) -> None:
    print("\n" + "=" * 96)
    print("§E — cross-ISO: does the repair move ANY other ISO's objective?")
    print("=" * 96)
    print(
        f"  {'ISO':7s}{'year':6s}{'dump_cost':>11s}{'repaired':>10s}"
        f"{'min producible mc':>19s}{'driver row':>30s}  verdict"
    )
    for iso, bdir in KEEPER_BUNDLES.items():
        if iso_only and iso != iso_only:
            continue
        bundle = REPO / bdir
        meta = json.loads((bundle / "meta.json").read_text())
        years = [int(y) for y in meta.get("years", YEARS)]
        for year in years:
            note = ""
            try:
                state = fleet_state(bundle, year)
                g = guard_state(state)
            except Exception as exc:  # pragma: no cover - diagnostic path
                # PJM's keeper arms pjm_da_virtual_bids, whose raw source is
                # not in this container. The virtual rows are settled
                # ANALYTICALLY instead (see the FINDING §E): DEC rows are
                # pmax 0 / pmin −peak (outside the injectable mask by
                # construction) and INC rungs are floored at
                # ``virtual_bids._inc_offer_floor`` = min_credit + ε, i.e.
                # ≥ −dump_cost + ε in every hour by construction. So the rest
                # of the fleet is the only measurable question, and it is
                # measured here with that one layer disabled.
                if "pjm_da_virtual_bids" not in str(exc):
                    print(f"  {iso:7s}{year:<6d}  RECONSTRUCTION FAILED: {exc}")
                    continue
                try:
                    state = fleet_state(bundle, year, pjm_da_virtual_bids=False)
                    g = guard_state(state)
                    note = "  [virtuals off: INC floored ≥ −dump_cost+ε, DEC pmax=0]"
                except Exception as exc2:  # pragma: no cover - diagnostic path
                    print(f"  {iso:7s}{year:<6d}  RECONSTRUCTION FAILED: {exc2}")
                    continue
            i = int(np.argmin(g["row_min"])) if g["row_min"].size else -1
            mn = float(g["row_min"][i]) if i >= 0 else float("nan")
            same = abs(g["repaired"] - g["current"]) < 1e-12
            print(
                f"  {iso:7s}{year:<6d}{g['current']:11.4f}{g['repaired']:10.4f}"
                f"{mn:19.4f}{(g['unit_ids'][i] if i >= 0 else '—'):>30s}"
                f"  {'UNCHANGED (byte-identical)' if same else 'GUARD WIDENS'}"
                f"{note}"
            )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    only = sys.argv[2] if len(sys.argv) > 2 else None
    if only == "--cross-iso":
        section_e(sys.argv[3] if len(sys.argv) > 3 else None)
        return 0
    a = section_a(bundle)
    b = section_b(bundle, a)
    section_c(bundle, a, b)
    section_d(b)
    if only != "--no-cross-iso":
        section_e()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
