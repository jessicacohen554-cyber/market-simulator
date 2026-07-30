"""caiso-143 — D-gates for the NODE-LEVEL export constraint + the export re-basis.

Design-first, kill-before-solve (the caiso-129/140/142 discipline). Reads only
committed bytes and the model's own config/build functions. **No LP is built and
no solver runs** — the one expensive call is the keeper-fleet reconstruction
(``run_calibration.run_year(fleet_only=True)``, the caiso-131/134/140/142
machinery), which composes the real floors without a matrix.

The charter (session brief) orders two prerequisites built before any export
sink is re-armed in any ISO:

1. a **node-level net-interchange export constraint** bounding the priced node's
   net interchange in the export direction by
   ``measured_corridor_flow_envelope(direction="export")``, so a sink can never
   absorb more than the node can deliver out; and
2. a **re-based export price** (FINDING-caiso142 §I part 2 measured the as-built
   ``hub − eps`` basis too high on both corridors).

The gates here test whether either is buildable *as specified* before anything
is armed:

* §A — **D1a**: is the chartered net-interchange row effective, or algebraically
  REDUNDANT with the corridor-group export bound the keeper already carries?
  Proved from the LP's own node topology and verified on committed sidecars.
* §B — **D1b**: the resale channel's *origin* — which injection at the node is
  price-insensitive, and can any bound on the SINK remove the channel?
* §C — **D1c/D2**: the only LP-representable alternative (a gross absorption
  bound at the measured envelope), measured against the firm must-flow block and
  the keeper's own node injection: does it drive the sink to 0 in the closed
  hours, and does it leave the channel alive in the open ones?
* §D — **D2/D3**: arm B's realised net-export activity from its committed
  class hourly (how much of §J's gross export was ever net export at all), and
  the analytic C3a prediction for a bounded arm against C3a-2024's band
  headroom.
* §E — **the price re-basis**: is an export delivery basis IDENTIFIABLE from the
  measured record without a fitted value? Measured against the identification
  quality of the *import* basis it would mirror (caiso-93/94).
* §F — the deeper result: soundness is a **non-convex** condition, so *no* LP row
  at any granularity can enforce it (analytic; demonstrated numerically).
* §G — cross-ISO: which keepers meet the resale-channel **precondition** (an
  absorption row AND a must-flow injection row at the SAME priced node), and
  whether the sink is live in that ISO's scored P1. Measurement only, rule 25.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso143_node_export_gates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
HOURS = 8760
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/caiso139_dumpguard_B"
ARM_A = REPO / "results/calibration/caiso142_control_A"
ARM_B = REPO / "results/calibration/caiso142_seam_B"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
EPS = 1e-3  # model.interchange.caiso.CAISO_INTERTIE_TIEBREAK_EPS

CORRIDORS = {"WECC_PNW": "MALIN", "WECC_DSW": "PALOVRDE"}
HUB_PROBE_TRANCHE = {"WECC_PNW": "PNW_midC", "WECC_DSW": "DSW_CCGT"}
CORRIDOR_LINK = {"WECC_PNW": "WECC_PNW>NP15", "WECC_DSW": "WECC_DSW>SP15_rest"}
CORRIDOR_GROUP = {
    "WECC_PNW": "grp:+WECC_PNW>NP15",
    "WECC_DSW": "grp:+WECC_DSW>SP15_rest",
}
EXPORT_UID = {
    "WECC_PNW": "WECC_PNW_export_MALIN",
    "WECC_DSW": "WECC_DSW_export_PALOVRDE",
}
# FINDING-caiso142 §J, the closed-envelope resale census the charter's D1 names.
# (corridor -> {year: (closed_envelope_hours, sink_transacting_hours)})
J_RESALE = {
    "WECC_PNW": {2023: (None, 99), 2024: (1644, 734), 2025: (3062, 1393)},
    "WECC_DSW": {2023: (7201, 1463), 2024: (7172, 1422), 2025: (7260, 948)},
}
# FINDING-caiso142 §J P4: arm B's realised C3a move ($/MWh, load-weighted).
ARM_B_C3A_MOVE = {2023: 3.401, 2024: 4.172, 2025: 2.649}
_META_RENAME = {
    "coal_prb_passthrough_sigmoid": "prb_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}


# --------------------------------------------------------------------------- #
# committed-bytes readers
# --------------------------------------------------------------------------- #
def actual_rt(year: int) -> np.ndarray:
    """Committed hourly actual RT LMP on the model calendar."""
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(HOURS)).to_numpy()


def month_of_hour(year: int) -> np.ndarray:
    """1-based month per model hour (fixed non-leap calendar)."""
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 24), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def sys_frame(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return d[d["pass"] == "P1"]


def net_frame(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"network_{year}.parquet")
    return d[d["pass"] == "P1"]


def link_series(bundle: Path, year: int, name: str, col: str = "mw") -> np.ndarray:
    f = net_frame(bundle, year)
    g = f[f["name"] == name].set_index("hour").reindex(range(HOURS))
    return np.nan_to_num(g[col].to_numpy(), nan=0.0)


def zone_series(bundle: Path, year: int, zone: str, col: str) -> np.ndarray:
    f = sys_frame(bundle, year)
    g = f[f["zone"] == zone].set_index("hour").reindex(range(HOURS))
    return np.nan_to_num(g[col].to_numpy(), nan=0.0)


def ca_lambda(bundle: Path, year: int) -> np.ndarray:
    """CA load-weighted lambda (the C3a basis) from a bundle's system sidecar."""
    d = sys_frame(bundle, year)
    price = d.pivot_table(index="hour", columns="zone", values="price")
    dem = d.pivot_table(index="hour", columns="zone", values="demand")
    ca = [z for z in price.columns if not str(z).startswith("WECC")]
    return ((price[ca] * dem[ca]).sum(axis=1) / dem[ca].sum(axis=1)).to_numpy()


def hub_series(year: int) -> dict[str, np.ndarray]:
    """Measured hub LMP per corridor (the series the per-hub injector writes)."""
    from market_sim.data.eia_loader import measured_import_hub_prices

    prices = measured_import_hub_prices(ISO, year, HOURS)
    if not prices:
        return {}
    return {
        zone: np.asarray(prices[HUB_PROBE_TRANCHE[zone]], dtype=float)
        for zone in CORRIDORS
        if HUB_PROBE_TRANCHE[zone] in prices
    }


def export_envelope(year: int) -> dict[str, np.ndarray]:
    """Measured export-direction corridor envelope (MW, >= 0), per corridor."""
    from market_sim.data.eia930.envelopes import measured_corridor_flow_envelope

    env = measured_corridor_flow_envelope(ISO, year, HOURS, direction="export")
    if not env:
        return {}
    return {z: np.abs(np.asarray(v, dtype=float)) for z, v in env.items()}


def measured_corridor_net(year: int) -> dict[str, np.ndarray]:
    """Measured EIA-930 corridor net import (MW, + = into CAISO), model clock."""
    from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA
    from market_sim.data.eia930.envelopes import _caiso_interchange_model_clock

    path = REPO / "data/raw/eia-930-interchange" / "CISO interchange hourly.parquet"
    if not path.exists():
        return {}
    frame = pd.read_parquet(path)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    m = local.year == year
    f = frame[m].copy()
    f["corridor"] = f["diba"].astype(str).map(CAISO_CORRIDOR_DIBA)
    f["ts"] = local[m].to_numpy()
    per_ts = (
        f.dropna(subset=["corridor"]).groupby(["corridor", "ts"])["mw"].sum()
    ).reset_index()
    per_ts["net_import"] = -per_ts["mw"]
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 48), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    idx = pd.Series(np.arange(HOURS), index=stamps)
    out: dict[str, np.ndarray] = {}
    for zone in CORRIDORS:
        sub = per_ts[per_ts["corridor"] == zone].copy()
        sub["h"] = sub["ts"].map(idx)
        sub = sub.dropna(subset=["h"])
        net = np.full(HOURS, np.nan)
        net[sub["h"].to_numpy().astype(int)] = sub["net_import"].to_numpy()
        out[zone] = net
    return out


def fleet_state(year: int) -> dict:
    """Reconstruct the keeper's fleet for ``year`` (no LP, no solve)."""
    import inspect

    from run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# §A — D1a: is the chartered node net-interchange row EFFECTIVE or REDUNDANT?
# --------------------------------------------------------------------------- #
def section_a() -> dict:
    """The chartered row's algebra, on the model's own topology + sidecars.

    A node-level net-interchange row bounds ``sum_g P[g, t]`` over the priced
    node's rows. The priced node is an EXTERNAL zone with its own energy-balance
    row, so that same sum is already pinned by the balance to the node's link
    flow. If the node carries no load, no renewables, no storage and exactly one
    link, the two quantities are the SAME variable combination and the new row
    can only restate a bound the corridor group already imposes.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.caiso import (
        CAISO_PER_HUB_IMPORT_ZONES,
        split_caiso_import_node_per_hub,
    )

    print("\n" + "=" * 78)
    print("§A  D1a — the chartered node-level net-interchange row: EFFECTIVE or")
    print("     REDUNDANT with the corridor-group export bound already armed?")
    print("=" * 78)

    cfg = split_caiso_import_node_per_hub(get_iso_config(ISO))
    corridor_zones = sorted(set(CAISO_PER_HUB_IMPORT_ZONES.values()))
    out: dict = {"topology": {}, "sidecars": {}, "envelope_identity": {}}

    print("\n  (i) node topology (config, after the per-hub split)")
    for z in corridor_zones:
        zone = next(zz for zz in cfg.zones if zz.name == z)
        out_links = [lk for lk in cfg.links if lk.from_zone == z]
        in_links = [lk for lk in cfg.links if lk.to_zone == z]
        out["topology"][z] = {
            "load_share": float(zone.load_share),
            "links_out": [f"{lk.from_zone}>{lk.to_zone}" for lk in out_links],
            "links_in": [f"{lk.from_zone}>{lk.to_zone}" for lk in in_links],
        }
        print(
            f"    {z:9s} load_share={zone.load_share:.3f}  "
            f"links out={[f'{lk.from_zone}>{lk.to_zone}' for lk in out_links]}  "
            f"links in={[f'{lk.from_zone}>{lk.to_zone}' for lk in in_links]}"
        )

    print("\n  (ii) the node's balance terms in the SOLVED sidecars (keeper + arm B)")
    print("       demand / slack / dump at the priced node, max |.| over 8,760 h")
    for label, bundle in (("keeper", KEEPER), ("armB", ARM_B)):
        for year in YEARS:
            row: dict[str, dict] = {}
            for z in corridor_zones:
                row[z] = {
                    c: float(np.abs(zone_series(bundle, year, z, c)).max())
                    for c in ("demand", "slack", "dump")
                }
            out["sidecars"][f"{label}_{year}"] = row
            txt = "  ".join(
                f"{z}: dem={row[z]['demand']:.4f} slack={row[z]['slack']:.4f} "
                f"dump={row[z]['dump']:.4f}"
                for z in corridor_zones
            )
            print(f"    {label:6s} {year}  {txt}")

    print("\n  (iii) the corridor group's export-direction limit vs the measured")
    print("        envelope (is the chartered bound ALREADY the armed bound?)")
    for year in YEARS:
        env = export_envelope(year)
        yr: dict[str, dict] = {}
        for z in corridor_zones:
            lim_dn = link_series(KEEPER, year, CORRIDOR_GROUP[z], "limit_dn")
            e = env.get(z)
            if e is None:
                continue
            same = float(np.abs(np.abs(lim_dn) - e).max())
            yr[z] = {
                "max_abs_diff_mw": same,
                "env_mean_mw": float(e.mean()),
                "env_zero_hours": int((e <= 0.0).sum()),
            }
            print(
                f"    {year} {z:9s} |group limit_dn| vs measured envelope: "
                f"max diff = {same:.6f} MW   (envelope mean {e.mean():7.1f} MW, "
                f"0 MW in {int((e <= 0.0).sum()):5d} h)"
            )
        out["envelope_identity"][str(year)] = yr

    print("\n  (iv) the node identity itself, DIRECTLY on the keeper's committed")
    print("       unit-level rows: max |sum_g P[g,t] - link_flow[t]| over 8,760 h")
    out["node_identity"] = {}
    for year in YEARS:
        u = pd.read_parquet(
            KEEPER / "hourly" / f"unit_hourly_{year}.parquet",
            columns=["pass", "unit_id", "fuel", "zone", "hour", "mw"],
        )
        u = u[u["pass"] == "P1"]
        for z in corridor_zones:
            at_node = u[u["zone"] == z]
            node = (
                at_node.groupby("hour")["mw"]
                .sum()
                .reindex(range(HOURS))
                .fillna(0.0)
                .to_numpy()
            )
            flow = link_series(KEEPER, year, CORRIDOR_LINK[z], "mw")
            gap = np.abs(node - flow)
            fuels = sorted(str(f) for f in at_node["fuel"].unique())
            out["node_identity"][f"{year}_{z}"] = {
                "max_abs_gap_mw": float(gap.max()),
                "mean_abs_gap_mw": float(gap.mean()),
                "fuels_at_node": fuels,
            }
            print(
                f"    {year} {z:9s} max gap = {gap.max():.6f} MW   "
                f"mean {gap.mean():.8f} MW   fuels at node: {fuels}"
            )
    print(
        "       (float32 parquet rounding only; the ONLY fuel at either node is\n"
        "       'import' -- no renewables, no storage, no thermal, so nothing else\n"
        "       can enter the node's balance.)"
    )

    print("\n  (v) VERDICT")
    print(
        "    Every priced corridor node has load_share = 0.0, exactly ONE link out,\n"
        "    no link in, and (measured above) slack = dump = 0.0000 MW in every\n"
        "    hour of every solved year -- in the keeper AND in arm B, with 'import'\n"
        "    the only fuel present. Its energy balance is therefore the identity\n\n"
        "        sum_g P[g, t]  ==  link_flow[t]     (verified DIRECTLY above to\n"
        "                                             0.000244 / 0.000488 MW)\n\n"
        "    so a row bounding the node's NET interchange in the export direction,\n"
        "        sum_g P[g, t] >= -envelope_export[t],\n"
        "    is the SAME linear combination as\n"
        "        link_flow[t]   >= -envelope_export[t],\n"
        "    which the corridor group ALREADY imposes at exactly that bound\n"
        "    (max diff 0.000000 MW above). The chartered row is ALGEBRAICALLY\n"
        "    REDUNDANT: it adds a duplicate of an armed constraint and cannot\n"
        "    change the feasible set.\n\n"
        "    FINDING-caiso142 §J measured the consequence directly: in the resale\n"
        "    hours the net LINK flow is >= 0 in 100.0 % of hours (PNW p50 exactly\n"
        "    0.0 MW), i.e. the chartered row is SLACK in precisely the hours the\n"
        "    charter's D1 asks it to bind. D1a: the row cannot bind and cannot\n"
        "    drive the sink to 0.\n\n"
        "    Granularity, separately: the in-repo machinery the charter cites\n"
        "    (rows.py::_build_import_node_rows) builds ONE ROW PER MONTH pinning a\n"
        "    monthly net-throughput band (the NYISO EIA-930 reconciliation design),\n"
        "    not an hourly directional bound -- so it is not the row the charter\n"
        "    describes either."
    )
    return out


# --------------------------------------------------------------------------- #
# §B — D1b: where the resale channel comes from (and what could remove it)
# --------------------------------------------------------------------------- #
def section_b(year: int = 2024) -> dict:
    """Which node injection is price-insensitive, and can a SINK bound remove it?

    Resale needs a counterparty at the node that injects regardless of price. A
    price-responsive import tranche cannot be one: it costs ``hub + wheel + eps``
    and the sink pays ``hub - eps``, so buying to resell loses ``wheel + 2 eps``
    per MWh. Only rows whose ``min_gen > 0`` (must-flow) inject against the
    spread.
    """
    from market_sim.config.interchange_config import (
        CAISO_IMPORT_DELIVERY_BASIS,
        IMPORT_TRANCHES,
    )
    from market_sim.model.interchange.caiso import (
        CAISO_FIRM_IMPORT_TRANCHES,
        CAISO_PER_HUB_IMPORT_ZONES,
    )

    print("\n" + "=" * 78)
    print(f"§B  D1b — the ORIGIN of the resale channel ({year} keeper fleet)")
    print("=" * 78)

    st = fleet_state(year)
    fa = st["fleet_arrays"] if isinstance(st, dict) else st.fleet_arrays
    uids = list(fa.unit_ids)
    corridor_zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    mg = fa.min_gen
    if mg is None:
        mg = np.broadcast_to(fa.pmin[:, None], (fa.pmin.size, HOURS))
    rows: list[dict] = []
    for r, uid in enumerate(uids):
        z = next((zz for zz in corridor_zones if str(uid).startswith(f"{zz}_")), None)
        if z is None:
            continue
        name = str(uid)[len(z) + 1 :]
        shaped = float(fa.pmax[r]) * fa.availability[r, :]
        floor = np.asarray(mg[r, :], dtype=float)
        rows.append(
            {
                "uid": str(uid),
                "zone": z,
                "name": name,
                "pmin": float(fa.pmin[r]),
                "pmax": float(fa.pmax[r]),
                "vom": float(fa.vom[r]),
                "wheel": float(CAISO_IMPORT_DELIVERY_BASIS.get(name, (0.0, 0.0))[1]),
                "firm": name in CAISO_FIRM_IMPORT_TRANCHES,
                "floor_mean": float(floor.mean()),
                "floor_hours": int((floor > 1e-9).sum()),
                # must-flow = floored AT the shaped capability (pmin == pmax in
                # effect), counted only where that capability is nonzero.
                "mustflow_hours": int(
                    ((floor >= shaped - 1e-6) & (shaped > 1e-9)).sum()
                ),
                "floor_energy_twh": float(np.clip(floor, 0.0, None).sum() / 1e6),
            }
        )
    print(
        f"\n  {'row':34s} {'zone':9s} {'pmin':>9s} {'pmax':>9s} {'wheel':>6s} "
        f"{'floor>0 h':>9s} {'must-flow h':>11s} {'floor TWh':>9s}"
    )
    for d in sorted(rows, key=lambda x: (x["zone"], -x["floor_energy_twh"])):
        print(
            f"  {d['uid']:34s} {d['zone']:9s} {d['pmin']:9.1f} {d['pmax']:9.1f} "
            f"{d['wheel']:6.2f} {d['floor_hours']:9d} {d['mustflow_hours']:11d} "
            f"{d['floor_energy_twh']:9.3f}"
        )
    forced = [d for d in rows if d["floor_hours"] > 0 and d["pmax"] > 0]
    print(
        f"\n  price-INSENSITIVE injection rows (min_gen > 0 in >=1 h): "
        f"{len(forced)} of {len([d for d in rows if d['pmax'] > 0])} import rows"
    )
    for d in forced:
        print(
            f"    {d['uid']:34s} floor mean {d['floor_mean']:7.1f} MW over "
            f"{d['floor_hours']:5d} h  ({d['floor_energy_twh']:.3f} TWh forced)"
        )
    wheels = {
        n: float(CAISO_IMPORT_DELIVERY_BASIS.get(n, (0.0, 0.0))[1])
        for n, _, _ in IMPORT_TRANCHES[ISO]
    }
    print(
        "\n  VERDICT — the resale channel is created by the MUST-FLOW rows, not by\n"
        "  the sink's price or its bound:\n"
        "    * an ECONOMIC tranche costs hub + wheel + eps and the sink pays\n"
        f"      hub - eps, so buy-to-resell loses wheel + 2 eps per MWh (wheels "
        f"{sorted(set(wheels.values()))}) -- never profitable, so an all-economic\n"
        "      node cannot resell at ALL, whatever the sink's bound;\n"
        "    * the FIRM rows above are floored at min_gen = pmax x availability\n"
        "      (inject_caiso_firm_import_selfschedule, caiso-77 must-flow), so\n"
        "      their energy arrives at the node whatever CA's lambda is -- that is\n"
        "      the counterparty §J measured (import inject p50 ~2,100 MW against\n"
        "      ~1,800 MW of absorption, node identity to 0.0002 MW).\n"
        "  A bound on the SINK therefore cannot remove the channel; it can only\n"
        "  meter it. The channel closes only where it opens: at the forced\n"
        "  injection (FINDING-caiso138 §C, the charter's prerequisite (c))."
    )
    return {"rows": rows, "forced": [d["uid"] for d in forced]}


# --------------------------------------------------------------------------- #
# §C — D1c/D2: the gross absorption bound, measured against firm + injection
# --------------------------------------------------------------------------- #
def section_c() -> dict:
    """The only LP-representable alternative: bound GROSS absorption at the envelope.

    ``S[t] >= -envelope_export[t]`` is a per-hour column bound on the sink (not a
    row). It does drive the sink to 0 wherever the envelope is closed. The
    question D1c must answer is what it leaves behind in the OPEN hours: if the
    node's own must-flow injection already exceeds the envelope there, the net
    flow stays >= 0 at full absorption and the transaction is still resale --
    metered, not removed.
    """
    print("\n" + "=" * 78)
    print("§C  D1c/D2 — a GROSS absorption bound at the measured envelope:")
    print("     does it remove the resale channel, or only meter it?")
    print("=" * 78)

    firm_by_year: dict[int, dict[str, np.ndarray]] = {}
    for year in YEARS:
        st = fleet_state(year)
        fa = st["fleet_arrays"] if isinstance(st, dict) else st.fleet_arrays
        mg = fa.min_gen
        if mg is None:
            mg = np.broadcast_to(fa.pmin[:, None], (fa.pmin.size, HOURS))
        per: dict[str, np.ndarray] = {z: np.zeros(HOURS) for z in CORRIDORS}
        for r, uid in enumerate(fa.unit_ids):
            z = next((zz for zz in CORRIDORS if str(uid).startswith(f"{zz}_")), None)
            if z is None or fa.pmax[r] <= 0.0:
                continue
            per[z] += np.clip(np.asarray(mg[r, :], dtype=float), 0.0, None)
        firm_by_year[year] = per

    out: dict = {}
    print(
        f"\n  {'yr':4s} {'corridor':9s} {'env>0 h':>8s} {'in-money':>9s} "
        f"{'open&ITM':>9s} {'F>=E':>12s} {'I_A>=E':>12s} {'net floor p50':>13s}"
    )
    for year in YEARS:
        env = export_envelope(year)
        hubs = hub_series(year)
        yr: dict[str, dict] = {}
        for z in CORRIDORS:
            e = env.get(z)
            hub = hubs.get(z)
            if e is None or hub is None:
                continue
            lam_node = zone_series(KEEPER, year, z, "price")
            i_a = link_series(KEEPER, year, CORRIDOR_LINK[z], "mw")
            firm = firm_by_year[year][z]
            export_px = hub - EPS  # the as-built basis
            itm = np.isfinite(hub) & (lam_node < export_px)
            openh = e > 0.0
            both = openh & itm
            f_ge_e = both & (firm >= e)
            i_ge_e = both & (i_a >= e)
            net_floor = i_a[both] - e[both]  # net flow at FULL permitted absorption
            yr[z] = {
                "open_hours": int(openh.sum()),
                "itm_hours": int(itm.sum()),
                "open_itm_hours": int(both.sum()),
                "firm_ge_env_share": float(f_ge_e.sum() / max(1, both.sum())),
                "inj_ge_env_share": float(i_ge_e.sum() / max(1, both.sum())),
                "net_floor_p50": float(np.median(net_floor)) if both.any() else None,
                "net_floor_neg_share": (
                    float((net_floor < 0).mean()) if both.any() else None
                ),
                "env_energy_twh": float(e.sum() / 1e6),
                "permitted_absorb_twh": float(e[both].sum() / 1e6),
                "firm_energy_twh": float(firm.sum() / 1e6),
            }
            v = yr[z]
            print(
                f"  {year} {z:9s} {v['open_hours']:8d} {v['itm_hours']:9d} "
                f"{v['open_itm_hours']:9d} {v['firm_ge_env_share']:11.1%} "
                f"{v['inj_ge_env_share']:11.1%} "
                f"{(v['net_floor_p50'] if v['net_floor_p50'] is not None else float('nan')):13.1f}"
            )
        out[str(year)] = yr

    print(
        "\n  Columns: env>0 = hours the measured export envelope is open; in-money =\n"
        "  hours the sink's as-built price (hub - eps) beats the node lambda;\n"
        "  open&ITM = the hours a bounded sink would transact; F>=E = share of those\n"
        "  hours where the node's own MUST-FLOW injection alone already equals or\n"
        "  exceeds the envelope; I_A>=E = same for the keeper's realised node\n"
        "  injection; net floor = I_A - E, the net corridor flow that REMAINS at\n"
        "  full permitted absorption (>= 0 means the whole absorbed quantity is\n"
        "  matched by same-node injection -- resale, not export)."
    )
    for year in YEARS:
        for z in CORRIDORS:
            v = out[str(year)].get(z)
            if not v:
                continue
            print(
                f"    {year} {z:9s} permitted absorption {v['permitted_absorb_twh']:6.3f} TWh"
                f"  vs forced injection {v['firm_energy_twh']:6.3f} TWh"
                f"  | net flow < 0 in {v['net_floor_neg_share']:.1%} of transacting h"
            )
    return out


# --------------------------------------------------------------------------- #
# §D — D2/D3: arm B's realised NET export, and the bounded arm's C3a prediction
# --------------------------------------------------------------------------- #
def section_d() -> dict:
    """How much of arm B's gross export was ever NET export, and what a bound buys.

    Arm B's per-link sidecar is gitignored (``hourly/network_*.parquet``, rule-15
    slim bundle), so the per-corridor split is FINDING-caiso142 §J's binding
    record. What IS committed is arm B's ``class_hourly`` ``import`` class -- the
    SIGNED sum over both nodes' rows, i.e. the seam's net interchange -- which
    measures the aggregate directly.
    """
    print("\n" + "=" * 78)
    print("§D  D2/D3 — arm B's realised NET export vs its gross export, and the")
    print("     analytic C3a prediction for a bounded arm")
    print("=" * 78)

    out: dict = {"net": {}, "c3a": {}}
    # §J's gross (any-MW) export-hour census, both corridors summed, for scale.
    gross_all = {2023: 3339 + 1683, 2024: 4788 + 1496, 2025: 4075 + 1062}
    print(
        f"\n  {'yr':4s} {'net import TWh':>15s} {'net export h':>13s} "
        f"{'net export TWh':>15s} {'closed-env txn h':>17s} "
        f"{'gross export h':>15s} {'measured net-exp h':>19s}"
    )
    for year in YEARS:
        kb = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        ab = pd.read_parquet(ARM_B / "hourly" / f"class_hourly_{year}.parquet")
        k = kb[(kb["pass"] == "P1") & (kb["klass"] == "import")]
        b = ab[(ab["pass"] == "P1") & (ab["klass"] == "import")]
        kn = k.set_index("hour")["mw"].reindex(range(HOURS)).to_numpy()
        bn = b.set_index("hour")["mw"].reindex(range(HOURS)).to_numpy()
        gross_j = sum(
            J_RESALE[z][year][1] for z in CORRIDORS if year in J_RESALE[z]
        )  # transacting hours in CLOSED-envelope hours only (§J census)
        meas = measured_corridor_net(year)
        meas_tot = np.nansum(np.vstack([meas[z] for z in CORRIDORS]), axis=0)
        row = {
            "keeper_net_twh": float(np.nansum(kn) / 1e6),
            "armB_net_twh": float(np.nansum(bn) / 1e6),
            "armB_net_export_hours": int((bn < 0).sum()),
            "armB_net_export_twh": float(-np.nansum(np.clip(bn, None, 0.0)) / 1e6),
            "armB_min_mw": float(np.nanmin(bn)),
            "closed_env_transacting_hours_J": int(gross_j),
            "gross_export_hours_J": int(gross_all[year]),
            "measured_net_export_hours": int((meas_tot < -50).sum()),
            "measured_net_export_twh": float(
                -np.nansum(np.clip(meas_tot, None, 0.0)) / 1e6
            ),
        }
        out["net"][str(year)] = row
        print(
            f"  {year} {row['armB_net_twh']:15.3f} {row['armB_net_export_hours']:13d} "
            f"{row['armB_net_export_twh']:15.3f} "
            f"{row['closed_env_transacting_hours_J']:17d} "
            f"{row['gross_export_hours_J']:15d} "
            f"{row['measured_net_export_hours']:19d}"
        )

    print("\n  D3 — the bounded arm's C3a move, scaled from arm B's realised move")
    print(
        f"\n  {'yr':4s} {'armB Δnet TWh':>14s} {'closed-h absorb TWh (§J)':>25s} "
        f"{'kept share':>11s} {'armB C3a':>9s} {'bounded C3a pred':>17s}"
    )
    band = {}
    for year in YEARS:
        # arm B's absorption is not separately committed; its NET effect is.
        d_net = (
            out["net"][str(year)]["keeper_net_twh"]
            - out["net"][str(year)]["armB_net_twh"]
        )
        # §J census: absorption removed by a closed-hour bound = transacting hours
        # x that corridor's measured p50 absorption in those hours.
        p50_absorb = {
            (2024, "WECC_PNW"): 1825.0,
            (2024, "WECC_DSW"): 1503.0,
            (2025, "WECC_PNW"): 1761.0,
            (2025, "WECC_DSW"): 1332.0,
        }
        removed = 0.0
        for z in CORRIDORS:
            hrs = J_RESALE[z].get(year, (None, 0))[1]
            mw = p50_absorb.get((year, z))
            if mw is None:
                # 2023 p50s are not in the §J table; use the year's own corridor
                # mean of the 2024/2025 measurements as the stated approximation.
                mw = float(
                    np.mean([v for (yy, zz), v in p50_absorb.items() if zz == z])
                )
            removed += hrs * mw / 1e6
        kept = max(0.0, (d_net - removed) / d_net) if d_net > 0 else float("nan")
        pred = ARM_B_C3A_MOVE[year] * kept
        band[str(year)] = {
            "armB_delta_net_twh": float(d_net),
            "closed_hour_absorb_twh": float(removed),
            "kept_share": float(kept),
            "armB_c3a_move": ARM_B_C3A_MOVE[year],
            "bounded_c3a_pred": float(pred),
        }
        print(
            f"  {year} {d_net:14.3f} {removed:25.3f} {kept:10.1%} "
            f"{ARM_B_C3A_MOVE[year]:9.3f} {pred:17.3f}"
        )
    out["c3a"] = band
    print(
        "\n  C3a-2024 band headroom is $0.69 (keeper gap +2.768 against a +-$3.46\n"
        "  band). The bounded arm's predicted 2024 move above is compared to that\n"
        "  headroom in the finding. A bound can only REDUCE absorption relative to\n"
        "  arm B, so arm B's realised move is the upper bound and 0 the lower;\n"
        "  the scaling above apportions it by the absorption the closed-hour bound\n"
        "  removes (§J's own census), which is the only committed decomposition."
    )
    return out


# --------------------------------------------------------------------------- #
# §E — the export price re-basis: IDENTIFIABLE without a fitted value?
# --------------------------------------------------------------------------- #
def section_e() -> dict:
    """Is an export delivery basis identifiable the way caiso-93/94 identified imports?

    The import basis is a STATIC per-tranche constant
    (``CAISO_IMPORT_DELIVERY_BASIS``). For the export leg to be re-based the same
    way, the measured ``actual CAISO RT - raw hub`` spread in real net-export
    hours must be (a) stable enough across years to pick one constant without
    choosing, (b) tight enough within a year that a constant is a basis rather
    than an average of a congestion distribution, and (c) the right SIGN for a
    price-taking sink. Each is measured here, with the IMPORT-direction spread of
    the same series as the reference standard the mirror has to meet.
    """
    print("\n" + "=" * 78)
    print("§E  the export PRICE re-basis — is it identifiable without a fitted value?")
    print("=" * 78)

    out: dict = {"export": {}, "import_ref": {}, "structure": {}}
    print(
        f"\n  (i) per-year spread, real net-export hours (net < -50 MW)\n"
        f"  {'corridor':9s} {'yr':4s} {'n':>6s} {'p25':>8s} {'p50':>8s} "
        f"{'p75':>8s} {'IQR':>8s} {'mean':>8s} {'sd':>8s}"
    )
    for z in CORRIDORS:
        for year in YEARS:
            a = actual_rt(year)
            hub = hub_series(year).get(z)
            net = measured_corridor_net(year).get(z)
            if hub is None or net is None:
                continue
            m = (net < -50.0) & np.isfinite(a) & np.isfinite(hub)
            if not m.any():
                continue
            sp = a[m] - hub[m]
            q = np.percentile(sp, [25, 50, 75])
            out["export"].setdefault(z, {})[str(year)] = {
                "n": int(m.sum()),
                "p25": float(q[0]),
                "p50": float(q[1]),
                "p75": float(q[2]),
                "iqr": float(q[2] - q[0]),
                "mean": float(sp.mean()),
                "sd": float(sp.std()),
            }
            v = out["export"][z][str(year)]
            print(
                f"  {z:9s} {year} {v['n']:6d} {v['p25']:8.2f} {v['p50']:8.2f} "
                f"{v['p75']:8.2f} {v['iqr']:8.2f} {v['mean']:8.2f} {v['sd']:8.2f}"
            )
    for z in CORRIDORS:
        p50s = [out["export"].get(z, {}).get(str(y), {}).get("p50") for y in YEARS]
        p50s = [p for p in p50s if p is not None]
        if p50s:
            out["structure"].setdefault(z, {})["p50_year_range"] = float(
                max(p50s) - min(p50s)
            )
            print(
                f"  {z:9s} across-year p50 RANGE = ${max(p50s) - min(p50s):.2f} "
                f"(p50s {[round(p, 2) for p in p50s]})"
            )

    print(
        "\n  (ii) the IMPORT-direction spread of the SAME series (the standard the\n"
        "       mirror must meet: caiso-93/94 read a static constant off this)"
    )
    for z in CORRIDORS:
        for year in YEARS:
            a = actual_rt(year)
            hub = hub_series(year).get(z)
            net = measured_corridor_net(year).get(z)
            if hub is None or net is None:
                continue
            m = (net > 50.0) & np.isfinite(a) & np.isfinite(hub)
            if not m.any():
                continue
            sp = a[m] - hub[m]
            q = np.percentile(sp, [25, 50, 75])
            out["import_ref"].setdefault(z, {})[str(year)] = {
                "n": int(m.sum()),
                "p50": float(q[1]),
                "iqr": float(q[2] - q[0]),
            }
            print(
                f"  {z:9s} {year} n={int(m.sum()):5d} p50={q[1]:+7.2f} "
                f"IQR={q[2] - q[0]:7.2f}"
            )

    print(
        "\n  (iii) does the spread track a CONGESTION driver (season / depth /\n"
        "        hour-of-day)? A delivery basis should not."
    )
    for z in CORRIDORS:
        for year in YEARS:
            a = actual_rt(year)
            hub = hub_series(year).get(z)
            net = measured_corridor_net(year).get(z)
            if hub is None or net is None:
                continue
            base = (net < -50.0) & np.isfinite(a) & np.isfinite(hub)
            if not base.any():
                continue
            sp = a - hub
            mo = month_of_hour(year)
            hd = np.arange(HOURS) % 24
            shallow = base & (net >= -500.0)
            deep = base & (net < -500.0)
            summer = base & np.isin(mo, (6, 7, 8, 9))
            winter = base & np.isin(mo, (12, 1, 2))
            onpk = base & np.isin(hd, (16, 17, 18, 19, 20))
            offpk = base & np.isin(hd, (0, 1, 2, 3, 4, 5))

            def med(mask: np.ndarray) -> float:
                return float(np.median(sp[mask])) if mask.any() else float("nan")

            cells = {
                "shallow": med(shallow),
                "deep": med(deep),
                "summer": med(summer),
                "winter": med(winter),
                "onpeak": med(onpk),
                "offpeak": med(offpk),
            }
            out["structure"].setdefault(z, {})[str(year)] = cells
            spread_of_cells = np.nanmax(list(cells.values())) - np.nanmin(
                list(cells.values())
            )
            out["structure"][z][f"{year}_cell_range"] = float(spread_of_cells)
            print(
                f"  {z:9s} {year} "
                + "  ".join(f"{k}={v:+6.2f}" for k, v in cells.items())
                + f"  | cell range ${spread_of_cells:.2f}"
            )

    print(
        "\n  (iv) SIGN test — can a price-taking sink priced off the hub reproduce\n"
        "       reality's export hours at all?"
    )
    for z in CORRIDORS:
        for year in YEARS:
            a = actual_rt(year)
            hub = hub_series(year).get(z)
            net = measured_corridor_net(year).get(z)
            if hub is None or net is None:
                continue
            m = (net < -50.0) & np.isfinite(a) & np.isfinite(hub)
            if not m.any():
                continue
            below = float((a[m] < hub[m]).mean())
            print(
                f"  {z:9s} {year} reality net-exports in {int(m.sum()):5d} h; CA RT is\n"
                f"            BELOW the hub in {below:5.1%} of them "
                f"(a hub-priced sink can only export when CA < hub)"
            )
            out["structure"].setdefault(z, {})[f"{year}_below_hub_share"] = below
    return out


# --------------------------------------------------------------------------- #
# §F — the soundness set is NON-CONVEX, so no LP row can enforce it
# --------------------------------------------------------------------------- #
def section_f() -> dict:
    """Is a SOUND export sink LP-representable at all on this node?

    "Sound" = every MWh the sink books as an export is energy that actually left
    CAISO, i.e. gross withdrawal never exceeds net outflow::

        -S[t] <= max(0, -flow[t])

    §A established the node identity ``sum_g P = flow`` exactly (no load, no
    renewables, no storage, one link, slack = dump = 0), so ``flow`` and the
    node's net interchange are the same variable combination and the condition
    above is a joint restriction on ``(flow, S)``. This section checks whether
    that set is convex — an LP feasible region always is, so a non-convex
    soundness set cannot be written as rows at any granularity.
    """
    print("\n" + "=" * 78)
    print("§F  is a SOUND sink LP-representable? (convexity of the soundness set)")
    print("=" * 78)

    def sound(flow: float, s: float) -> bool:
        """The soundness condition: absorbed MW <= MW that actually left."""
        return s <= 1e-9 and (-s) <= max(0.0, -flow) + 1e-9

    # Two SOUND operating points drawn from the corridor's own measured scale
    # (PNW: 4,800 MW link TTC; the keeper's node injection p50 ~2,100 MW).
    p1 = (2100.0, 0.0)  # net import, sink off            -> sound
    p2 = (-500.0, -500.0)  # net export 500, sink takes 500 -> sound
    mids = [
        (0.5 * p1[0] + 0.5 * p2[0], 0.5 * p1[1] + 0.5 * p2[1]),
        (0.75 * p1[0] + 0.25 * p2[0], 0.75 * p1[1] + 0.25 * p2[1]),
    ]
    print(
        f"\n  endpoint 1  flow={p1[0]:+9.1f} MW  S={p1[1]:+9.1f} MW  sound={sound(*p1)}"
    )
    print(
        f"  endpoint 2  flow={p2[0]:+9.1f} MW  S={p2[1]:+9.1f} MW  sound={sound(*p2)}"
    )
    rows = []
    for lam, m in zip((0.5, 0.75), mids):
        ok = sound(*m)
        rows.append({"lambda": lam, "flow": m[0], "S": m[1], "sound": ok})
        print(
            f"  convex combo lambda={lam:.2f}  flow={m[0]:+9.1f} MW  S={m[1]:+9.1f} MW"
            f"  sound={ok}   <-- {'RESALE' if not ok else 'ok'}"
        )
    print(
        "\n  VERDICT — the soundness set is NON-CONVEX: two sound points whose convex\n"
        "  combination is a RESALE point (net IMPORT while the sink withdraws). An\n"
        "  LP's feasible region is convex by construction, so:\n\n"
        "    * NO set of linear rows -- node-level, link-level, hourly, monthly,\n"
        "      per-corridor or grouped -- can express soundness. The exact condition\n"
        "      is the disjunction {flow >= 0 => S = 0} OR {flow < 0 => -S <= -flow},\n"
        "      which needs a binary (a MIP) and is FORBIDDEN by the stack rules.\n"
        "    * Its tightest LINEAR surrogate, -S <= -flow imposed unconditionally,\n"
        "      reduces via the §A node identity to F + I_econ <= 0 -- INFEASIBLE\n"
        "      while the must-flow block F > 0 (§B: 11.7 / 15.6 TWh forced in 2024).\n"
        "    * Its convex HULL contains the resale points above, i.e. the best any\n"
        "      LP relaxation can do is permit exactly the behaviour being excluded.\n\n"
        "  So the chartered prerequisite is not merely redundant (§A) -- a sound\n"
        "  node-level export constraint DOES NOT EXIST in this model class. The\n"
        "  dependency inverts: the forced injection (F) must go elastic FIRST\n"
        "  (FINDING-caiso138 §C), and only then is the already-armed NET bound\n"
        "  (limit_dn = the measured export envelope) sufficient, because with\n"
        "  F = 0 the surrogate -S <= -flow is feasible and equals the net bound."
    )
    return {"endpoints": [p1, p2], "combos": rows}


# --------------------------------------------------------------------------- #
# §G — cross-ISO: which keepers satisfy the resale-channel PRECONDITION?
# --------------------------------------------------------------------------- #
def section_g() -> dict:
    """Measure the precondition §B identifies, in every ISO's own keeper.

    The channel needs BOTH halves at the same priced node: a ``pmin < 0``
    absorption row **and** a price-insensitive (must-flow) injection row. Neither
    alone opens it. Rule 25 [R-ISO-SCOPE]: this is a MEASUREMENT of exposure, not
    a verdict in another ISO's lane — each lane re-gates on its own evidence.
    """
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.interchange.spec import (
        build_interchange_fleet,
        get_interchange_spec,
    )

    print("\n" + "=" * 78)
    print("§G  cross-ISO — which keepers meet the RESALE-CHANNEL precondition?")
    print("=" * 78)

    # Each ISO's current keeper bundle + the config flags that force must-flow
    # injection at its priced node (the caiso-142 §F census, extended).
    KEEPERS = {
        "ERCOT": "ercot139_cc_committed_arm",
        "CAISO": "caiso139_dumpguard_B",
        "PJM": "pjm137_ctheatrate_B",
        "MISO": "miso101_tempgrain_B",
        "NYISO": "nyiso99_demandfix",
        "NEISO": "neiso61_netrev_margin",
    }
    MUSTFLOW_FLAGS = (
        "caiso_firm_import_selfschedule",
        "nyiso_firm_imports",
        "miso_firm_imports",
        "miso_firm_import_floor",
    )
    out: dict = {}
    print(
        f"\n  {'ISO':6s} {'keeper':28s} {'rows':>5s} {'pmin<0':>7s} "
        f"{'must-flow flags armed':32s} {'precondition':>12s}"
    )
    for iso, bundle in KEEPERS.items():
        meta_path = REPO / "results/calibration" / bundle / "run_config.json"
        if not meta_path.exists():
            print(f"  {iso:6s} {bundle:28s} run_config absent — skipped")
            continue
        sc = json.loads(meta_path.read_text())["scenario_config"]
        fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
        cfg = ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})
        spec = get_interchange_spec(cfg, iso, 2025)
        gens = build_interchange_fleet(spec) if spec.import_zone else []
        neg = [g for g in gens if float(g.pmin_mw) < 0.0]
        armed = [f for f in MUSTFLOW_FLAGS if getattr(cfg, f, False)]
        pre = bool(neg) and bool(armed)
        out[iso] = {
            "keeper": bundle,
            "interchange_rows": len(gens),
            "absorption_rows": len(neg),
            "absorption_mw": float(sum(-float(g.pmin_mw) for g in neg)),
            "mustflow_flags": armed,
            "precondition": pre,
        }
        print(
            f"  {iso:6s} {bundle:28s} {len(gens):5d} {len(neg):7d} "
            f"{','.join(armed) if armed else '—':32s} {'YES' if pre else 'no':>12s}"
        )
        if pre:
            # Per-NODE refinement: the two halves must meet at ONE priced zone,
            # and the bridge (if any) decides whether the sink is live in P1.
            by_zone: dict[str, dict] = {}
            for g in gens:
                z = str(g.zone)
                e = by_zone.setdefault(z, {"sinks": [], "injects": []})
                (e["sinks"] if float(g.pmin_mw) < 0.0 else e["injects"]).append(
                    str(g.name)
                )
            shared = {z: e for z, e in by_zone.items() if e["sinks"] and e["injects"]}
            out[iso]["nodes_with_both_row_kinds"] = sorted(shared)
            bridge_flag = {
                "CAISO": "caiso_ra_mustoffer",
                "NYISO": "nyiso_gas_commitment_bridge",
                "MISO": None,
            }.get(iso)
            bridge_armed = (
                bool(getattr(cfg, bridge_flag, False)) if bridge_flag else False
            )
            out[iso]["p1_bridge_armed"] = bridge_armed
            out[iso]["sink_live_in_p1"] = not bridge_armed
            for z, e in sorted(shared.items()):
                print(
                    f"         node {z:16s} sinks={len(e['sinks'])} "
                    f"injects={len(e['injects'])}  injects: "
                    f"{','.join(sorted(e['injects'])[:4])}"
                    + ("…" if len(e["injects"]) > 4 else "")
                )
            print(
                f"         P1 bridge {bridge_flag or '(none)'} armed={bridge_armed} "
                f"-> sink LIVE in the scored P1: "
                f"{'NO (deleted by the seam)' if bridge_armed else 'YES'}"
            )
            # Context only: the keeper's SIGNED seam total. Negative hours mean the
            # seam net-exported; it does NOT separate resale from true export
            # (that needs unit-level rows, which these slim bundles do not carry).
            ch = REPO / "results/calibration" / bundle / "hourly"
            seam_hours: dict[str, int] = {}
            for year in YEARS:
                p = ch / f"class_hourly_{year}.parquet"
                if not p.exists():
                    continue
                fr = pd.read_parquet(p)
                fr = fr[(fr["pass"] == "P1") & (fr["klass"] == "import")]
                if fr.empty:
                    continue
                s = fr.set_index("hour")["mw"].reindex(range(HOURS)).to_numpy()
                seam_hours[str(year)] = int(np.nansum(s < 0))
            out[iso]["seam_net_export_hours"] = seam_hours
            if seam_hours:
                print(
                    "         signed seam total < 0 in "
                    + " / ".join(f"{y}: {h} h" for y, h in seam_hours.items())
                    + "  (context; not a resale measurement)"
                )
    print(
        "\n  Reading (measurement only, rule 25): the resale channel opens ONLY where\n"
        "  both halves meet at one priced node. CAISO's keeper is the case §A-§F\n"
        "  analyses. An ISO with absorption rows but NO must-flow injection cannot\n"
        "  resell (an economic tranche costs hub + wheel + eps against the sink's\n"
        "  hub - eps, §B), so for those the caiso-142 seam fix is safe on this axis;\n"
        "  an ISO meeting the precondition would inherit the same non-convexity, and\n"
        "  its OWN lane decides. Note the seam fix is CAISO-flag-gated, so no other\n"
        "  ISO's recipe moves either way from this session."
    )
    return out


def main() -> int:
    a = section_a()
    b = section_b()
    c = section_c()
    d = section_d()
    e = section_e()
    f = section_f()
    g = section_g()
    print("\n" + "=" * 78)
    print("machine-readable summary")
    print("=" * 78)
    print(
        json.dumps(
            {
                "A": a,
                "B": {"forced": b["forced"]},
                "C": c,
                "D": d,
                "E": e,
                "F": f,
                "G": g,
            },
            indent=1,
            default=float,
        )[:4000]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
