"""caiso-276 phase 0 part 2: WHERE does the 2022 C3a residual actually live,
and is it the belly-commitment object caiso-275 handed forward? ZERO LP.

caiso-275 measured its decile decomposition on **2024** and named CAISO
commitment as the successor object: in 2024's lowest net-load decile the real
market keeps 7.2 GW of gas online and EXPORTS while the model runs 1.5 GW and
IMPORTS. This probe asks whether that object carries **2022's** residual, which
is the number the caiso-276 charter is pointed at. It also separates the two
objects caiso-273 §6.3 warned are conflated in 2022 — the year-invariant
additive adder and the December gas-crisis excess.

Nothing here is gated on a residual moving; it MEASURES the residual's location
so a mechanism can be chosen on its own footprint (rule 1 ``[R-STRUCT]``,
rule 29 ``[R-SCREEN]`` step 0).
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
BENCH = REPO / "frontend/data/backcast/bench/CAISO/2022.json.gz"
OUT = REPO / "results/calibration/_caiso276_where_2022_lives.json"
YEAR = 2022
T = 8760
CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
#: Cumulative month-start hour edges for a non-leap 8760 calendar — the SAME
#: ``_CUM`` construction ``render_calibration_html`` uses for ``pMon``, so the
#: monthly split here is the scorer's own calendar, not a 730-hour
#: approximation (the caiso-273 §6.4 disclosure).
_MDAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_CUM = np.cumsum((0,) + tuple(d * 24 for d in _MDAYS))[:12]


def lw(v, w) -> float:
    v = np.asarray(v, float)
    w = np.asarray(w, float)
    return float((v * w).sum() / w.sum())


def main() -> None:
    import gzip

    out: dict = {"session": "caiso-276", "year": YEAR, "phase": "0b"}
    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    pr = sysdf.pivot(index="hour", columns="zone", values="price")
    dm = sysdf.pivot(index="hour", columns="zone", values="demand")
    zones = [z for z in CA_ZONES if z in pr.columns]
    P = pr[zones].to_numpy(float).T
    D = dm[zones].to_numpy(float).T
    lam = (P * D).sum(axis=0) / D.sum(axis=0)
    w = D.sum(axis=0)

    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    cls = (
        ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(T), fill_value=0.0)
        .fillna(0.0)
    )

    def col(k):
        return cls[k].to_numpy(float) if k in cls.columns else np.zeros(T)

    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == YEAR].sort_values("hour")
    rt = act["rt"].to_numpy(float)

    bench = json.load(gzip.open(BENCH))["bench"]
    rt_lw_bench = bench["avgLMP"]["rt_lw"]
    rt_lw_mon_bench = bench["avgLMP"]["rt_lw_mon"]

    # ---- BASIS RECONCILIATION, stated before any decomposition ----
    # The GATE is the committed bench ``rt_lw`` (84.49) — what
    # calibration_verdict.score_price_mean actually compares against. This
    # probe's hourly reconstruction weights the committed hourly RT series by
    # the MODEL's zonal demand, which returns 83.76. The 0.73 $/MWh difference
    # is a weighting-basis artifact, not a price error, and every number below
    # is therefore used for SHAPE (which hours/months carry the gap) and never
    # quoted as the gate magnitude.
    model_lw = lw(lam, w)
    recon = {
        "model_lw": round(model_lw, 3),
        "gate_actual_bench_rt_lw": rt_lw_bench,
        "gate_gap_usd_mwh": round(model_lw - rt_lw_bench, 3),
        "gate_gap_pct": round(100 * (model_lw / rt_lw_bench - 1), 3),
        "usd_needed_to_pass_10pct": round(model_lw - 1.10 * rt_lw_bench, 3),
        "probe_hourly_rt_lw": round(lw(rt, w), 3),
        "basis_delta": round(lw(rt, w) - rt_lw_bench, 3),
    }
    out["basis_reconciliation"] = recon
    print("=== BASIS RECONCILIATION (the gate is the bench, not the probe) ===")
    for k, v in recon.items():
        print(f"  {k:>30s}  {v}")

    # ---- Section 1 — monthly contribution ----
    midx = np.clip(np.searchsorted(_CUM, np.arange(T), side="right") - 1, 0, 11)
    tot_w = w.sum()
    mrows = []
    for m in range(12):
        sel = midx == m
        ww = w[sel]
        mrows.append(
            {
                "month": m + 1,
                "model": round(lw(lam[sel], ww), 2),
                "rt_probe": round(lw(rt[sel], ww), 2),
                "rt_bench": rt_lw_mon_bench[m],
                "gap_vs_bench": round(lw(lam[sel], ww) - rt_lw_mon_bench[m], 2),
                # contribution to the ANNUAL gate gap, on the bench monthly actual
                "contrib_usd_mwh": round(
                    float(ww.sum() / tot_w * (lw(lam[sel], ww) - rt_lw_mon_bench[m])), 3
                ),
                "load_share_pct": round(100 * float(ww.sum() / tot_w), 2),
                "gas_mw": round(float(sum(col(k) for k in GAS_CLASSES)[sel].mean()), 0),
            }
        )
    out["monthly"] = mrows
    print("\n=== Section 1 — 2022 gap by CALENDAR month (against bench rt_lw_mon) ===")
    print("  mon   model  rt_bench    gap  CONTRIB  load%   gasMW")
    for r in mrows:
        print(
            f"  {r['month']:>3d} {r['model']:>7.2f} {r['rt_bench']:>9.2f}"
            f" {r['gap_vs_bench']:>6.2f} {r['contrib_usd_mwh']:>+8.3f}"
            f" {r['load_share_pct']:>6.2f} {r['gas_mw']:>7.0f}"
        )
    s = sum(r["contrib_usd_mwh"] for r in mrows)
    print(
        f"  {'SUM':>3s} contribution = {s:+.3f} $/MWh"
        f"  (gate gap {recon['gate_gap_usd_mwh']:+.3f})"
    )
    dec_share = mrows[11]["contrib_usd_mwh"] / s * 100 if s else 0.0
    out["december_share_pct"] = round(dec_share, 1)
    print(f"  DECEMBER share of the annual gap = {dec_share:.1f} %")

    # ---- Section 2 — net-load decile decomposition, WITH and WITHOUT December ----
    vre = col("wind") + col("solar")
    netload = w - vre
    gasmw = sum(col(k) for k in GAS_CLASSES)
    imp = col("import")

    def deciles(mask: np.ndarray) -> np.ndarray:
        idx = np.where(mask)[0]
        order = idx[np.argsort(netload[idx])]
        dec = np.full(T, -1, int)
        n = order.size
        for i in range(10):
            dec[order[i * n // 10 : (i + 1) * n // 10]] = i
        return dec

    for label, mask in (
        ("ALL 8760 h", np.ones(T, bool)),
        ("EX-DECEMBER (8016 h)", midx != 11),
        ("DECEMBER ONLY (744 h)", midx == 11),
    ):
        dec = deciles(mask)
        sub_w = w[mask].sum()
        rows = []
        for i in range(10):
            m = dec == i
            if not m.any():
                continue
            ww = w[m]
            rows.append(
                {
                    "decile": i,
                    "hours": int(m.sum()),
                    "netload_mw": round(float(netload[m].mean()), 0),
                    "model": round(lw(lam[m], ww), 2),
                    "rt": round(lw(rt[m], ww), 2),
                    "gap": round(lw(lam[m], ww) - lw(rt[m], ww), 2),
                    "contrib_within": round(
                        float(((lam[m] - rt[m]) * ww).sum() / sub_w), 3
                    ),
                    "contrib_annual": round(
                        float(((lam[m] - rt[m]) * ww).sum() / tot_w), 3
                    ),
                    "gas_mw": round(float(gasmw[m].mean()), 0),
                    "imp_mw": round(float(imp[m].mean()), 0),
                    "solar_mw": round(float(col("solar")[m].mean()), 0),
                }
            )
        out[f"deciles_{label.split()[0].lower()}"] = rows
        print(f"\n=== Section 2 — deciles, {label} ===")
        print(
            "  dec  hours  netload   model      rt    gap  c_within"
            " c_annual   gasMW   impMW  solarMW"
        )
        for r in rows:
            print(
                f"  {r['decile']:>3d} {r['hours']:>6d} {r['netload_mw']:>8.0f}"
                f" {r['model']:>7.2f} {r['rt']:>7.2f} {r['gap']:>6.2f}"
                f" {r['contrib_within']:>+9.3f} {r['contrib_annual']:>+8.3f}"
                f" {r['gas_mw']:>7.0f} {r['imp_mw']:>7.0f} {r['solar_mw']:>8.0f}"
            )
        print(
            f"  within-subset total = "
            f"{sum(r['contrib_within'] for r in rows):+.3f} $/MWh;"
            f" annual contribution = "
            f"{sum(r['contrib_annual'] for r in rows):+.3f} $/MWh"
        )

    # ---- Section 3 — hour-of-day, ex-December ----
    hod = np.arange(T) % 24
    exdec = midx != 11
    sub_w = w[exdec].sum()
    hrows = []
    for h in range(24):
        m = (hod == h) & exdec
        ww = w[m]
        hrows.append(
            {
                "hod": h,
                "model": round(lw(lam[m], ww), 2),
                "rt": round(lw(rt[m], ww), 2),
                "gap": round(lw(lam[m], ww) - lw(rt[m], ww), 2),
                "contrib_within": round(
                    float(((lam[m] - rt[m]) * ww).sum() / sub_w), 3
                ),
                "gas_mw": round(float(gasmw[m].mean()), 0),
                "imp_mw": round(float(imp[m].mean()), 0),
                "solar_mw": round(float(col("solar")[m].mean()), 0),
            }
        )
    out["hod_ex_december"] = hrows
    print("\n=== Section 3 — hour-of-day, EX-DECEMBER ===")
    print("  hod   model      rt    gap  c_within   gasMW   impMW  solarMW")
    for r in hrows:
        print(
            f"  {r['hod']:>3d} {r['model']:>7.2f} {r['rt']:>7.2f} {r['gap']:>6.2f}"
            f" {r['contrib_within']:>+9.3f} {r['gas_mw']:>7.0f}"
            f" {r['imp_mw']:>7.0f} {r['solar_mw']:>8.0f}"
        )

    # ---- Section 4 — MEASURED gas + interchange vs model, 2022, by decile ----
    # This is caiso-275's own instrument re-pointed at 2022: does the belly
    # commitment deficit it measured in 2024 exist in 2022, and at what size?
    try:
        from market_sim.data.eia930.actuals import load_eia_hourly_benchmark
        from market_sim.data.eia930.envelopes import measured_interchange_envelope

        eb = load_eia_hourly_benchmark("CAISO", YEAR)
        ie = measured_interchange_envelope("CAISO", YEAR)
    except Exception as exc:  # pragma: no cover - data availability
        eb, ie = None, None
        out["eia930_error"] = repr(exc)
        print(f"\n!! EIA-930 read failed: {exc!r}")

    if eb is not None:
        meas_gas = (
            np.asarray(eb.get("gas"), float) if eb.get("gas") is not None else None
        )
        out["eia930_keys"] = sorted(eb.keys())
        print(f"\n=== Section 4 — measured EIA-930 keys: {sorted(eb.keys())}")
        if meas_gas is not None and meas_gas.size == T:
            dec = deciles(np.ones(T, bool))
            mi = None
            if ie is not None:
                arr = np.asarray(ie, float)
                mi = arr if arr.ndim == 1 else None
                if mi is None:
                    out["interchange_shape"] = list(np.shape(arr))
            crows = []
            for i in range(10):
                m = dec == i
                crows.append(
                    {
                        "decile": i,
                        "model_gas_mw": round(float(gasmw[m].mean()), 0),
                        "meas_gas_mw": round(float(meas_gas[m].mean()), 0),
                        "gas_deficit_mw": round(
                            float(meas_gas[m].mean() - gasmw[m].mean()), 0
                        ),
                        "model_import_mw": round(float(imp[m].mean()), 0),
                        "meas_net_import_mw": (
                            round(float(mi[m].mean()), 0) if mi is not None else None
                        ),
                        "model_price": round(lw(lam[m], w[m]), 2),
                        "rt_price": round(lw(rt[m], w[m]), 2),
                    }
                )
            out["gas_commitment_census_2022"] = crows
            print(
                "\n=== Section 4 — 2022 belly commitment census"
                " (caiso-275's 2024 instrument, re-pointed) ==="
            )
            print("  dec  modelGas  measGas  DEFICIT  modelImp   measImp  model$   rt$")
            for r in crows:
                mi_s = (
                    "     n/a"
                    if r["meas_net_import_mw"] is None
                    else f"{r['meas_net_import_mw']:>8.0f}"
                )
                print(
                    f"  {r['decile']:>3d} {r['model_gas_mw']:>9.0f}"
                    f" {r['meas_gas_mw']:>8.0f} {r['gas_deficit_mw']:>+8.0f}"
                    f" {r['model_import_mw']:>9.0f} {mi_s}"
                    f" {r['model_price']:>7.2f} {r['rt_price']:>6.2f}"
                )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
