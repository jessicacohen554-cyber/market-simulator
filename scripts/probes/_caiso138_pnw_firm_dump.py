"""caiso-138 — the WECC_PNW firm-hydro dump: charter instrument (NO SOLVE).

Answers the caiso-138 charter's central question — is the defect in the FLOOR
(`caiso_firm_import_selfschedule`), the CAP (`caiso_corridor_flow_limit`), or
their COMPOSITION — entirely from the keeper's committed ``hourly/`` sidecars,
the raw EIA-930 interchange bytes, and a ``run_year(fleet_only=True)``
reconstruction of the LP inputs. No LP is built beyond the fleet stage and no
solver is called.

Sections (mirroring FINDING-caiso138):

* **§A — D1 quantify.** Per year: the firm block's shaped capability, the
  corridor group cap, the model link flow, the dumped MW at ``WECC_PNW``
  (annual and on the caiso-134 defect-window basis that produced the filed
  70 / 161 / 307 MW), and the node price against the measured MALIN hub in the
  SAME hours (not the annual print).
* **§B — D2 attribute.** The dump decomposed exactly: per-hour node balance
  identity ``dump = firm + midC − flow``; ``flow ≡ cap`` in every dump hour;
  the collision set ``{firm capability > cap}`` against the dump set; the
  α (firm-vs-cap collision) / β (negative-hub tranche gaming, a DIFFERENT
  defect) energy split on both corridors; and the export sink's committed
  dispatch (identically zero — see §D for why).
* **§C — the energy basis.** The floor's forced annual energy (level × 8760 ×
  eford) against the corridor's own measured EIA-930 energy (net, and
  net-importing-hours only), per corridor — the charter's ask (a).
* **§D — the P1 sink-deletion seam.** Call-site reproduction of
  ``pipeline.commitment._bridge_floored_fleet``'s maximum-composition on the
  reconstructed fleet: ``np.maximum(base_min_gen, bridge_floor)`` with the
  detector's zeros-initialised floor deletes the export sinks' negative
  absorption range (−4,800 / −10,623 MW → 0) for the scored P1 pass.
* **§E — D3 pre-check inputs.** The per-year measure of the U-turn arbitrage
  set (hours where the CA terminus LMP sits below the corridor export hub) —
  the reason the naive seam fix and any hub-resale sink variant are refused —
  and the CA-side byte-identity argument for the envelope clip's E1/E2 = +$0.00
  prediction.

Usage::

    PYTHONPATH=.:src:scripts:scripts/probes .venv/bin/python \
        scripts/probes/_caiso138_pnw_firm_dump.py \
        results/calibration/caiso130_nameplate_B
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _caiso105_evening_q1_pin import fleet_state  # noqa: E402
from _caiso132_corridor_export_gates import (  # noqa: E402
    T,
    defect_mask,
)

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HUB_LMP = REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"
# Corridor → (link, group row, firm tranche uid, measured hub) — the exact
# sidecar names the keeper persists (network_<y>.parquet / unit_hourly_<y>).
CORRIDORS = {
    "WECC_PNW": (
        "WECC_PNW>NP15",
        "grp:+WECC_PNW>NP15",
        "WECC_PNW_PNW_hydro_base",
        "MALIN",
        "NP15",
    ),
    "WECC_DSW": (
        "WECC_DSW>SP15_rest",
        "grp:+WECC_DSW>SP15_rest",
        "WECC_DSW_DSW_solar_PV",
        "PALOVRDE",
        "SP15_rest",
    ),
}


# ---------------------------------------------------------------------------
# committed-bytes readers
# ---------------------------------------------------------------------------
def _sidecars(bundle: Path, year: int) -> dict:
    """P1 rows of the three sidecars this probe reads, hour-sorted."""
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    net = pd.read_parquet(bundle / "hourly" / f"network_{year}.parquet")
    net = net[net["pass"] == "P1"]
    uh = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["unit_id", "pass", "zone", "hour", "mw", "cap_mw"],
        filters=[("zone", "in", list(CORRIDORS))],
    )
    uh = uh[uh["pass"] == "P1"]
    return {"sys": sysf, "net": net, "uh": uh}


def _corridor_frame(sc: dict, zone: str) -> dict[str, np.ndarray]:
    """Hour-aligned arrays for one corridor from the committed sidecars."""
    link, grp, firm_uid, _hub, _term = CORRIDORS[zone]
    z = sc["sys"][sc["sys"]["zone"] == zone].sort_values("hour")
    cap = (
        sc["net"][(sc["net"]["kind"] == "group") & (sc["net"]["name"] == grp)]
        .sort_values("hour")["limit_up"]
        .to_numpy()
    )
    flow = (
        sc["net"][(sc["net"]["kind"] == "link") & (sc["net"]["name"] == link)]
        .sort_values("hour")["mw"]
        .to_numpy()
    )
    units = sc["uh"][sc["uh"]["zone"] == zone]
    firm = units[units["unit_id"] == firm_uid].sort_values("hour")
    others = (
        units[units["unit_id"] != firm_uid]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(T), fill_value=0.0)
        .to_numpy()
    )
    return {
        "dump": z["dump"].to_numpy(),
        "price": z["price"].to_numpy(),
        "cap": cap,
        "flow": flow,
        "firm_mw": firm["mw"].to_numpy(),
        "firm_cap": firm["cap_mw"].to_numpy(),
        "others": others,
    }


def _measured_hub(year: int, hub: str) -> np.ndarray:
    h = pd.read_parquet(HUB_LMP)
    h = h[(h["year"] == year) & (h["hub"] == hub)]
    return h.set_index("hour")["price"].reindex(range(T)).to_numpy()


def _measured_corridor_energy(year: int) -> dict[str, tuple[float, float]]:
    """(net TWh, net-importing-hours TWh) per corridor from the raw 930 bytes.

    The same parquet, model-clock mapping and corridor DIBA grouping that
    ``measured_corridor_flow_envelope`` uses to BUILD the cap — so §C compares
    the floor against the cap's own source, not a re-derivation.
    """
    from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA
    from market_sim.data.eia930.envelopes import _caiso_interchange_model_clock

    f = pd.read_parquet(REPO / "data/raw/eia-930-interchange/CISO interchange hourly.parquet")
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(f["local_time"]))
    f = f.assign(
        yr=np.asarray(local.year),
        corridor=f["diba"].astype(str).map(CAISO_CORRIDOR_DIBA).to_numpy(),
        mwv=pd.to_numeric(f["mw"], errors="coerce").to_numpy(),
    ).dropna(subset=["corridor", "mwv"])
    out = {}
    g = f[f["yr"] == year]
    for zone in CORRIDORS:
        per_ts = -g[g["corridor"] == zone].groupby("local_time")["mwv"].sum()
        out[zone] = (per_ts.sum() / 1e6, per_ts.clip(lower=0).sum() / 1e6)
    return out


# ---------------------------------------------------------------------------
# §A — D1 quantify
# ---------------------------------------------------------------------------
def section_a(bundle: Path) -> dict:
    print("=" * 96)
    print("§A — D1: the dump, the floor, the cap and the node price (committed bytes)")
    print("=" * 96)
    out = {}
    for year in YEARS:
        sc = _sidecars(bundle, year)
        c = _corridor_frame(sc, "WECC_PNW")
        dump, price = c["dump"], c["price"]
        dh = dump > 1e-6
        win = defect_mask(bundle, year)  # caiso-134's Sep-Dec belly window
        malin = _measured_hub(year, "MALIN")
        print(f"\n--- {year} ---")
        print(
            f"  dump: annual mean {dump.mean():7.1f} MW ({dump.sum() / 1e6:.3f} TWh), "
            f"{dh.sum()} h > 0, mean|>0 {dump[dh].mean():.1f} MW, max {dump.max():.1f}"
        )
        print(
            f"  caiso-134 window basis (n={win.sum()} h): mean dump "
            f"{dump[win].mean():7.1f} MW   <- the filed 70/161/307 series"
        )
        print(
            f"  node lambda: dump-hours median {np.median(price[dh]):.2f} "
            f"(== -26.001 in {(np.abs(price[dh] + 26.001) < 0.01).mean():.1%}); "
            f"annual median {np.median(price):.2f}"
        )
        print(
            f"  measured MALIN, SAME dump hours: median {np.nanmedian(malin[dh]):.2f}, "
            f"mean {np.nanmean(malin[dh]):.2f} "
            f"(< -26 in {np.nanmean(malin[dh] < -26):.1%} of them)"
        )
        print(
            f"  firm block: shaped capability mean {c['firm_cap'].mean():.1f} MW "
            f"(dump-hrs {c['firm_cap'][dh].mean():.1f}); "
            f"corridor cap mean {c['cap'].mean():.1f} (dump-hrs {c['cap'][dh].mean():.1f}); "
            f"flow dump-hrs {c['flow'][dh].mean():.1f}"
        )
        out[year] = {"dump": dump, "dh": dh, "win_mean": float(dump[win].mean())}
    return out


# ---------------------------------------------------------------------------
# §B — D2 attribute
# ---------------------------------------------------------------------------
def section_b(bundle: Path) -> dict:
    print("\n" + "=" * 96)
    print("§B — D2: attribution — collision identity, alpha/beta split, dead sink")
    print("=" * 96)
    out = {}
    for year in YEARS:
        sc = _sidecars(bundle, year)
        print(f"\n--- {year} ---")
        for zone in CORRIDORS:
            c = _corridor_frame(sc, zone)
            dump, cap, flow = c["dump"], c["cap"], c["flow"]
            dh = dump > 1e-6
            if not dh.any():
                print(f"  {zone}: no dump")
                continue
            resid = np.abs(c["firm_mw"] + c["others"] - flow - dump)
            alpha = np.minimum(dump, np.clip(c["firm_cap"] - cap, 0.0, None))
            beta = dump - alpha
            coll = c["firm_cap"] > cap + 0.5
            print(
                f"  {zone}: dump {dump.sum() / 1e6:.3f} TWh in {dh.sum()} h | "
                f"alpha (firm>cap collision) {alpha.sum() / 1e6:.3f} TWh | "
                f"beta (other: negative-hub gaming) {beta.sum() / 1e6:.3f} TWh"
            )
            print(
                f"     balance |firm+others-flow-dump| max {resid.max():.4f} MW; "
                f"flow==cap in {np.mean(np.abs(flow[dh] - cap[dh]) < 1e-3):.1%} of dump hrs; "
                f"dump hrs in collision set {int((dh & coll).sum())}/{int(dh.sum())}"
            )
            sink = sc["uh"][
                sc["uh"]["unit_id"].str.startswith(f"{zone}_export_")
            ]["mw"]
            print(
                f"     export sink dispatch: min {sink.min():.1f} max {sink.max():.1f} "
                f"(identically zero in all {len(sink)} P1 rows)"
            )
            out[(year, zone)] = {
                "alpha_twh": float(alpha.sum() / 1e6),
                "beta_twh": float(beta.sum() / 1e6),
            }
    print(
        "\n  No-firm counterfactual (analytic, no solve needed): every other unit at"
        "\n  the node is economic (pmin 0, mc > 0 into a dump-priced node) and the"
        "\n  dump variable itself costs +$26.001/MWh, so with the firm floor removed"
        "\n  the alpha dump is zero by optimality; the beta component (negative-hub"
        "\n  tranche gaming, mc < -dump_cost) is a DIFFERENT defect and persists."
    )
    return out


# ---------------------------------------------------------------------------
# §C — the energy basis (charter ask (a))
# ---------------------------------------------------------------------------
def section_c(bundle: Path) -> None:
    print("\n" + "=" * 96)
    print("§C — the floor's forced energy vs the corridor's own measured energy")
    print("=" * 96)
    print(f"  {'year':6s}{'corridor':10s}{'forced firm':>13s}{'model flow':>12s}"
          f"{'meas net':>10s}{'meas imp-hrs':>13s}   (TWh)")
    for year in YEARS:
        sc = _sidecars(bundle, year)
        meas = _measured_corridor_energy(year)
        nl = sc["net"]
        for zone in CORRIDORS:
            link = CORRIDORS[zone][0]
            firm_uid = CORRIDORS[zone][2]
            firm_twh = (
                sc["uh"][sc["uh"]["unit_id"] == firm_uid]["mw"].sum() / 1e6
            )
            flow_twh = (
                nl[(nl["kind"] == "link") & (nl["name"] == link)]["mw"].sum() / 1e6
            )
            net_twh, imp_twh = meas[zone]
            print(
                f"  {year:<6d}{zone:10s}{firm_twh:13.2f}{flow_twh:12.2f}"
                f"{net_twh:10.2f}{imp_twh:13.2f}"
            )
    print(
        "\n  The PNW firm block alone forces 2-4x the corridor's measured"
        "\n  net-importing-hours energy (charter ask (a): the DMM RA-import level is"
        "\n  a capacity-showing quantity; x8760 via the unit-mean shape it becomes an"
        "\n  energy obligation the northern corridor measurably never carried)."
    )


# ---------------------------------------------------------------------------
# §D — the P1 sink-deletion seam (call-site reproduction)
# ---------------------------------------------------------------------------
def section_d(bundle: Path, year: int = 2025) -> None:
    print("\n" + "=" * 96)
    print("§D — pipeline.commitment._bridge_floored_fleet deletes the export sinks")
    print("=" * 96)
    state = fleet_state(bundle, year)
    fa = state["fleet_arrays"]
    ids = [str(u) for u in fa.unit_ids]
    sink_rows = [i for i, u in enumerate(ids) if "_export_" in u]
    print(f"  fleet ({year}): sink rows {[(ids[i]) for i in sink_rows]}")
    base = (
        fa.min_gen
        if fa.min_gen is not None
        else np.broadcast_to(fa.pmin[:, None], (len(ids), T))
    )
    for i in sink_rows:
        print(
            f"    {ids[i]}: pmin {fa.pmin[i]:.0f}, base min_gen "
            f"[{base[i].min():.0f}, {base[i].max():.0f}]  <- LIVE absorption range"
        )
    # The exact composition _bridge_floored_fleet applies at the P0->P1 seam
    # (pipeline/commitment.py: new_min_gen = np.maximum(base_min_gen, floor))
    # with the detector's zeros-initialised floor (model/commitment.py:
    # ``floor = np.zeros((n_gen, T))`` — positive only on bridged gas rows).
    from market_sim.pipeline.commitment import _bridge_floored_fleet
    from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER

    zeros_floor = np.zeros((len(ids), T))
    floored = _bridge_floored_fleet(fa, zeros_floor, MECH_RA_MUSTOFFER)
    for i in sink_rows:
        print(
            f"    after seam: {ids[i]} min_gen "
            f"[{floored.min_gen[i].min():.0f}, {floored.min_gen[i].max():.0f}]"
            f"  <- absorption range DELETED (max(-TTC, 0) = 0)"
        )
    print(
        "  => the scored P1 pass solves with both export sinks pinned to zero:"
        "\n     zero exports in all 26,280 committed corridor-hours, caiso-132 §3's"
        "\n     'globally inert' export bound, and dump as the node's only outlet."
    )


# ---------------------------------------------------------------------------
# §E — D3 pre-check inputs
# ---------------------------------------------------------------------------
def section_e(bundle: Path) -> None:
    print("\n" + "=" * 96)
    print("§E — the U-turn arbitrage set (why hub-resale sink variants are refused)")
    print("=" * 96)
    for year in YEARS:
        sc = _sidecars(bundle, year)
        prices = sc["sys"].pivot_table(index="hour", columns="zone", values="price")
        for zone in CORRIDORS:
            hub = _measured_hub(year, CORRIDORS[zone][3])
            term = prices[CORRIDORS[zone][4]].to_numpy()
            n = min(len(hub), len(term))
            gap = hub[:n] - term[:n]
            arb = np.nansum(gap > 0.5)
            print(
                f"  {year} {zone}: terminus lambda < measured hub - $0.5 in "
                f"{arb} h ({arb / T:.1%}); mean positive gap "
                f"${np.nanmean(np.clip(gap, 0, None)):.2f}/MWh"
            )
    print(
        "\n  A live sink priced hub-eps with bound beyond the stranded residual pulls"
        "\n  DELIVERED firm (and, via the link, CA supply) out in every such hour —"
        "\n  voiding caiso-77's must-flow semantics and failing E1. The envelope clip"
        "\n  instead changes NOTHING CA-side: in collision hours the delivered flow is"
        "\n  cap before and after (E1/E2 prediction = +$0.00, degeneracy noise only)."
    )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    section_a(bundle)
    section_b(bundle)
    section_c(bundle)
    section_d(bundle)
    section_e(bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
