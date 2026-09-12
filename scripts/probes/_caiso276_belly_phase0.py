"""caiso-276 phase 0: is the C3a-2022 residual reachable by a CAISO COMMITMENT
lever, and does any admissible lever exist at all? ZERO LP.

WHY THIS EXISTS
---------------
The 2022 rung of the CAISO keeper ``2026-09-12-caiso-275-gascoupling`` reads
NOT-YET on ``price_mean`` alone: model 94.07 against an RT load-weighted actual
of 84.49, i.e. +11.3 % against a +/-10 % band. caiso-275 handed the successor
object forward as CAISO *commitment* — in the lowest net-load decile the real
market keeps 7-9 GW of its own gas online and EXPORTS, while the model
decommits that gas and IMPORTS — and proved (Arm A, ``caiso_import_solar_shape``
rejected on its own liveness gate, ``dump`` 0.000 TWh in every arm hour) that
the belly over-price is NOT reachable through the import offer.

This probe asks the question that must be answered BEFORE a solve is spent:

  If more CAISO gas were held online at minimum load through the belly, WHERE
  WOULD THAT ENERGY GO, and WHAT WOULD SET THE PRICE once it got there?

That is pure arithmetic on the keeper's own committed solution. It can kill a
commitment arm before any LP, and it cannot promote one.

WHAT IT READS — committed artifacts only
----------------------------------------
* ``results/calibration/caiso275_B_gascoupling_2022/`` — the folded 2022 rung of
  the live keeper: ``hourly/system_2022.parquet`` (P1 zonal price + demand),
  ``hourly/class_hourly_2022.parquet``, ``hourly/class_band_hourly_2022.parquet``,
  ``dispatch/2022_P1.parquet`` (unit-level MW + LMP).
* ``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`` — committed
  hourly actual RT/DA LMP.
* ``data/raw/eia-930*`` via ``market_sim.data.eia_loader`` — the measured CAISO
  hourly gas generation and net interchange, i.e. the series caiso-275's decile
  table was built from.
* ``reconstruct_bundle_fleet`` — the keeper's OWN assembled ``mc_base`` offer
  surface and ``pmax x availability``, so the offer prices read here are the
  offer prices the LP solved on.

RULE POSTURE
------------
Rule 1 ``[R-STRUCT]``: nothing here is gated on the price residual. The
decomposition in Section 2 MEASURES where the residual lives (that is the
object's description, which the charter is allowed to know); every GATE below is
a statement about a mechanism's own footprint and absorption arithmetic, and
none of them reads C3a. Rule 32 ``[R-SHARD]`` (a): this is zero-LP parent work.
It arms nothing and adds no ``ScenarioConfig`` field.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = REPO / "results/calibration/caiso275_B_gascoupling_2022"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
OUT = REPO / "results/calibration/_caiso276_belly_phase0.json"
YEAR = 2022
T = 8760

#: CA load zones — the zones that carry demand (WECC_PNW / WECC_DSW are import
#: nodes with zero demand and zero C3a weight).
CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")
#: Gas classes whose commitment the RA must-offer family can reach.
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
#: Price-match tolerance, $/MWh. Taken UNCHANGED from caiso-272's instrument
#: (10x the largest committed CAISO scarcity-adder bound for any scored year),
#: never swept here.
TOL = 0.25


def band_of(unit_id: str) -> str:
    """The LP tranche suffix — verbatim the committed sidecar's band split."""
    return str(unit_id).rsplit("_", 1)[-1]


def lw(v: np.ndarray, w: np.ndarray) -> float:
    return float((np.asarray(v) * w).sum() / w.sum())


# --------------------------------------------------------------------------
# Section 0 — load the committed solution
# --------------------------------------------------------------------------
def load_model() -> dict:
    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    pr = sysdf.pivot(index="hour", columns="zone", values="price")
    dm = sysdf.pivot(index="hour", columns="zone", values="demand")
    slk = sysdf.pivot(index="hour", columns="zone", values="slack")
    dmp = sysdf.pivot(index="hour", columns="zone", values="dump")
    zones = [z for z in CA_ZONES if z in pr.columns]
    P = pr[zones].to_numpy(float).T  # (zone, hour)
    D = dm[zones].to_numpy(float).T
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    cls = (
        ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(T), fill_value=0.0)
        .fillna(0.0)
    )
    cbh = pd.read_parquet(BUNDLE / f"hourly/class_band_hourly_{YEAR}.parquet")
    cbh = cbh[cbh["pass"] == "P1"]
    band = (
        cbh.pivot_table(
            index="hour", columns=["klass", "band"], values="mw", aggfunc="sum"
        )
        .reindex(range(T), fill_value=0.0)
        .fillna(0.0)
    )
    return {
        "zones": zones,
        "P": P,
        "D": D,
        "slack": slk[zones].to_numpy(float).T,
        "dump": dmp[zones].to_numpy(float).T,
        "cls": cls,
        "band": band,
        "lam": (P * D).sum(axis=0) / D.sum(axis=0),
        "w": D.sum(axis=0),
    }


def main() -> None:
    out: dict = {
        "session": "caiso-276",
        "year": YEAR,
        "phase": 0,
        "bundle": str(BUNDLE.relative_to(REPO)),
    }
    M = load_model()
    lam, w = M["lam"], M["w"]
    cls = M["cls"]
    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == YEAR].sort_values("hour")
    rt = act["rt"].to_numpy(float)

    # ---------------- G-REPRO: the published numbers ----------------
    # THE GATE IS THE COMMITTED BENCH ``rt_lw`` (84.49) — what
    # ``calibration_verdict.score_price_mean`` actually compares against. This
    # probe's own hourly reconstruction (the committed hourly RT series
    # weighted by the MODEL's zonal demand) returns 83.76; the difference is a
    # weighting-BASIS artifact, not a price error. Every gate figure below is
    # therefore computed against the bench, and the reconstruction is reported
    # beside it for shape work only (part 2 §"basis reconciliation").
    import gzip

    bench_rt_lw = float(
        json.load(gzip.open(REPO / "frontend/data/backcast/bench/CAISO/2022.json.gz"))[
            "bench"
        ]["avgLMP"]["rt_lw"]
    )
    model_lw = lw(lam, w)
    repro = {
        "model_lw_price": round(model_lw, 3),
        "published_model_lw": 94.07,
        "gate_actual_bench_rt_lw": bench_rt_lw,
        "gap_usd_mwh": round(model_lw - bench_rt_lw, 3),
        "gap_pct": round(100 * (model_lw / bench_rt_lw - 1), 3),
        "band_pct": 10.0,
        "usd_needed_to_pass": round(model_lw - 1.10 * bench_rt_lw, 3),
        "probe_hourly_rt_lw": round(lw(rt, w), 3),
        "basis_delta_probe_minus_bench": round(lw(rt, w) - bench_rt_lw, 3),
        "total_slack_mwh": round(float(M["slack"].sum()), 3),
        "total_dump_mwh": round(float(M["dump"].sum()), 3),
    }
    out["G_REPRO"] = repro
    print("=== G-REPRO (must reproduce the committed keeper numbers) ===")
    for k, v in repro.items():
        print(f"  {k:>26s}  {v}")

    # ---------------- Section 2 — where the gap lives ----------------
    # net load = demand - (wind + solar), the model's OWN realized series.
    dem = w
    vre = cls.get("wind", pd.Series(0.0, index=range(T))).to_numpy(float) + cls.get(
        "solar", pd.Series(0.0, index=range(T))
    ).to_numpy(float)
    netload = dem - vre
    order = np.argsort(netload)
    dec = np.empty(T, int)
    for i in range(10):
        dec[order[i * T // 10 : (i + 1) * T // 10]] = i
    gasmw = sum(
        cls.get(k, pd.Series(0.0, index=range(T))).to_numpy(float) for k in GAS_CLASSES
    )
    imp = cls.get("import", pd.Series(0.0, index=range(T))).to_numpy(float)

    rows = []
    tot_w = w.sum()
    for i in range(10):
        m = dec == i
        ww = w[m]
        rows.append(
            {
                "decile": i,
                "hours": int(m.sum()),
                "netload_mean_mw": round(float(netload[m].mean()), 1),
                "model_price": round(lw(lam[m], ww), 2),
                "rt_price": round(lw(rt[m], ww), 2),
                "gap": round(lw(lam[m], ww) - lw(rt[m], ww), 2),
                # load-weighted CONTRIBUTION of this decile to the annual gap
                "contrib_usd_mwh": round(
                    float(((lam[m] - rt[m]) * ww).sum() / tot_w), 3
                ),
                "model_gas_mw": round(float(gasmw[m].mean()), 0),
                "model_import_mw": round(float(imp[m].mean()), 0),
            }
        )
    out["decile_decomposition"] = rows
    print("\n=== Section 2 — 2022 gap by model net-load decile ===")
    print("  dec  hours   netload  model     rt    gap  CONTRIB   gasMW   impMW")
    for r in rows:
        print(
            f"  {r['decile']:>3d} {r['hours']:>6d} {r['netload_mean_mw']:>9.0f}"
            f" {r['model_price']:>7.2f} {r['rt_price']:>6.2f} {r['gap']:>6.2f}"
            f" {r['contrib_usd_mwh']:>+8.3f} {r['model_gas_mw']:>7.0f}"
            f" {r['model_import_mw']:>7.0f}"
        )
    print(
        f"  {'TOTAL':>10s} contribution = "
        f"{sum(r['contrib_usd_mwh'] for r in rows):+.3f} $/MWh"
    )

    # hour-of-day
    hod = np.arange(T) % 24
    hodrows = []
    for h in range(24):
        m = hod == h
        ww = w[m]
        hodrows.append(
            {
                "hod": h,
                "gap": round(lw(lam[m], ww) - lw(rt[m], ww), 2),
                "contrib_usd_mwh": round(
                    float(((lam[m] - rt[m]) * ww).sum() / tot_w), 3
                ),
                "model_gas_mw": round(float(gasmw[m].mean()), 0),
                "model_import_mw": round(float(imp[m].mean()), 0),
                "model_price": round(lw(lam[m], ww), 2),
                "rt_price": round(lw(rt[m], ww), 2),
            }
        )
    out["hod_decomposition"] = hodrows
    print("\n=== Section 2b — gap by hour-of-day ===")
    print("  hod   model     rt    gap  CONTRIB   gasMW   impMW")
    for r in hodrows:
        print(
            f"  {r['hod']:>3d} {r['model_price']:>7.2f} {r['rt_price']:>6.2f}"
            f" {r['gap']:>6.2f} {r['contrib_usd_mwh']:>+8.3f}"
            f" {r['model_gas_mw']:>7.0f} {r['model_import_mw']:>7.0f}"
        )

    # ---------------- Section 3 — the ABSORPTION arithmetic ----------------
    # If a commitment lever forces +X MW of gas min-load into hour t, the
    # energy balance must absorb it. The only sinks the LP has, in the order
    # the dispatch would use them:
    #   (1) back down IMPORT dispatch (import class MW above its own min),
    #   (2) back down other dispatchable thermal / hydro above min,
    #   (3) spill VRE (only if there is VRE headroom to spill, i.e. the LP
    #       is dispatching VRE below cap x CF),
    #   (4) DUMP at dump_cost.
    # Sink (1) sets price at the import offer; (3) at the negative renewable
    # keep-running offer; (4) at dump_cost. WHICH sink binds decides whether a
    # commitment lever moves price DOWN at all.
    # VRE headroom is read from the keeper's own spill: `caiso_solar_endogenous
    # _spill` is armed, so realized solar below potential is spill the LP chose.
    stor = None
    spath = BUNDLE / f"hourly/storage_{YEAR}.parquet"
    if spath.exists():
        sd = pd.read_parquet(spath)
        sd = sd[sd["pass"] == "P1"] if "pass" in sd.columns else sd
        stor = sd
    out["storage_cols"] = list(stor.columns) if stor is not None else None

    hydro = cls.get("hydro", pd.Series(0.0, index=range(T))).to_numpy(float)
    sink = []
    for i in range(10):
        m = dec == i
        sink.append(
            {
                "decile": i,
                "import_mw": round(float(imp[m].mean()), 0),
                "hydro_mw": round(float(hydro[m].mean()), 0),
                "gas_mw": round(float(gasmw[m].mean()), 0),
                "dump_mw": round(float(M["dump"][:, m].sum(axis=0).mean()), 3),
                "slack_mw": round(float(M["slack"][:, m].sum(axis=0).mean()), 3),
                "solar_mw": round(
                    float(
                        cls.get("solar", pd.Series(0.0, index=range(T)))
                        .to_numpy(float)[m]
                        .mean()
                    ),
                    0,
                ),
                "wind_mw": round(
                    float(
                        cls.get("wind", pd.Series(0.0, index=range(T)))
                        .to_numpy(float)[m]
                        .mean()
                    ),
                    0,
                ),
                "price": round(lw(lam[m], w[m]), 2),
            }
        )
    out["sink_census"] = sink
    print("\n=== Section 3 — absorption sinks by decile (model, P1) ===")
    print("  dec   impMW  hydroMW   gasMW  solarMW  windMW   dumpMW  slackMW  price")
    for r in sink:
        print(
            f"  {r['decile']:>3d} {r['import_mw']:>7.0f} {r['hydro_mw']:>8.0f}"
            f" {r['gas_mw']:>7.0f} {r['solar_mw']:>8.0f} {r['wind_mw']:>7.0f}"
            f" {r['dump_mw']:>8.3f} {r['slack_mw']:>8.3f} {r['price']:>6.2f}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
