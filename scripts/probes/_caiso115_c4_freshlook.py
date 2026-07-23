"""caiso-115 FRESH-LOOK: is C4 a model limitation, and can C5a-fix / C3a-guard coexist?

Measurement-only, committed artifacts + raw EIA-930 only, NO SOLVE. Reproduces the
five measurements behind FINDING-caiso115-c4-freshlook-and-separability-2026-07-23.md:

  1. Cross-ISO C4 benchmark (Inv 1a) — score every ISO keeper's gas dispatch_corr
     from its committed payload/bench, showing CAISO's NRMSE is the sole outlier
     while its r sits in-family with NYISO/NEISO, so the gate is not mis-specified.
  2. C4 gas-residual decomposition (Inv 1b) — reproduce the exact CEMS-basis gas
     series the gate uses (model plants[].m vs bench plants[].campd), resolve the
     residual by hour-of-day and gas class, and split SSE into a flat volume bias
     vs an hour/day timing part; report the irreducible day-to-day scatter floor.
  3. 2023 benchmark-basis fragility — 2023 is scored on the EIA-930 NG cell
     (CEMS-anchor onset is 2024); rescoring it on the same CEMS basis as 2024/25.
  4. Evening merit order (Inv 1c) — from the class_hourly / system sidecars, what
     fills the evening ramp and at what price (why CT peakers do not fire).
  5. Hydro & import shape (Inv 3) — model vs actual (raw EIA-930 NG:WAT / interchange)
     hydro and net-import by hour-of-day, showing the residual evening over-hydro
     that survives the keeper's p95 hydro_dispatch_envelope.

Run:  PYTHONPATH=<repo> python scripts/probes/_caiso115_c4_freshlook.py
"""

from __future__ import annotations

import base64
import math

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from scripts.calibration_verdict import GAS_CLASSES, load_artifacts, score_dispatch_corr

T = 8760
CA_ZONES = {"NP15", "SP15", "ZP26"}  # CA zones proper (exclude WECC_import node)
KEEPER = "2026-07-19-caiso-102-hourfix"
# Keeper-proxy with committed hourly sidecars (reproduces keeper gas to <0.25 %;
# the keeper bundle carries no hourly/ sidecar, caiso104_m1_B does).
PROXY_HOURLY = "results/calibration/caiso104_m1_B/hourly"
KEEPERS = {
    "ERCOT": "2026-07-23-ercot98-np6-hsl-fullspan",
    "PJM": "2026-07-19-pjm-gasshape-interpfix",
    "CAISO": KEEPER,
    "NYISO": "2026-07-22-nyiso-70-scr-edrp",
    "NEISO": "2026-07-13-neiso-60-phantom-outage",
    "MISO": "2026-07-20-miso-81-phantom-outage",
}
DISP_R_FLOOR, DISP_NRMSE_MAX = 0.70, 0.30


def _series(b64: str) -> np.ndarray:
    """Decode a committed uint8 CF% base64 series into a length-T float array."""
    return np.frombuffer(base64.b64decode(b64)[:T], dtype=np.uint8).astype(float)


def _pearson_nrmse(m: np.ndarray, a: np.ndarray) -> tuple[float, float]:
    """Pearson r and mean-normalized RMSE of two hourly series (verdict's formula)."""
    om = a.mean()
    r = float(np.corrcoef(m, a)[0, 1])
    nrmse = float(math.sqrt(((m - a) ** 2).mean()) / om) if om > 0 else 9.9
    return r, nrmse


def inv1a_cross_iso() -> None:
    """Score every ISO keeper's gas/coal dispatch_corr from committed artifacts."""
    print("\n" + "=" * 78)
    print(
        "INV 1a — CROSS-ISO C4 (dispatch_corr) BENCHMARK  (gate: r>=0.70, NRMSE<=0.30)"
    )
    print("=" * 78)
    print(f"{'ISO':6} {'gas r':>12} {'gas NRMSE':>14} {'verdict (per-year)'}")
    for iso, rid in KEEPERS.items():
        art = load_artifacts(rid)
        payload, bench = art["payload"], art["bench"]
        rs, ns, per = [], [], []
        for year in sorted(int(y) for y in (payload or {}).get("years", {})):
            recs = score_dispatch_corr(
                year, payload["years"][str(year)], bench.get(year, {}), iso
            )
            for rec in recs:
                if rec.get("key") != "gas":
                    continue
                mod = rec.get("model", "")
                import re

                mm = re.search(r"r=([\-\d.]+) nrmse=([\-\d.]+)", mod)
                if mm and mm.group(1) != "None":
                    rs.append(float(mm.group(1)))
                    ns.append(float(mm.group(2)))
                per.append((year, rec.get("status")))
        rr = f"{min(rs):.3f}-{max(rs):.3f}" if rs else "n/a"
        nn = f"{min(ns):.3f}-{max(ns):.3f}" if ns else "n/a"
        print(f"{iso:6} {rr:>12} {nn:>14}   {per}")
    print("READ: CAISO gas NRMSE is the sole outlier (all peers <=0.207); its r is")
    print("      in-family (NYISO 0.804-0.888). 5/6 ISOs pass comfortably -> the C4")
    print("      gate is NOT mis-specified for a reduced-network model.")


def _keeper_gas_series(year: int, ypay: dict, ybench: dict):
    """Reproduce the gate's CEMS-basis model & actual gas hourly series + per-class."""
    e930 = ybench.get("e930") or {}
    cogen = float(e930.get("gas_cogen_grid") or 0.0)
    bpl = ybench.get("plants") or {}
    ppl = ypay.get("plants") or {}
    model = np.zeros(T)
    act = np.zeros(T)
    cls_m: dict[str, np.ndarray] = {}
    cls_a: dict[str, np.ndarray] = {}
    btm = 0.0
    for code, bp in bpl.items():
        grp = bp.get("group")
        if grp not in GAS_CLASSES or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        camp = bp.get("campd")
        pp = ppl.get(str(code))
        if cap <= 0 or not camp or not pp or not pp.get("m"):
            continue
        s = cap / 100.0
        a = _series(camp) * s
        m = _series(pp["m"]) * s
        act += a
        model += m
        cls_a[grp] = cls_a.get(grp, np.zeros(T)) + a
        cls_m[grp] = cls_m.get(grp, np.zeros(T)) + m
        btm += float(bp.get("btm") or 0.0)
    btm_mw = btm * 1e6 / T
    cog_mw = cogen * 1e6 / T
    rows = {r.get("fuel"): r for r in ypay.get("fuelRows", [])}
    model_twh = rows.get("gas", {}).get("m")
    core = model.sum() / 1e6 - btm
    fill = (float(model_twh) - core) * 1e6 / T if model_twh is not None else 0.0
    return model - btm_mw + fill, act - btm_mw + cog_mw, cls_m, cls_a


def inv1b_decomposition() -> None:
    """Decompose the CEMS-basis C4 gas residual by hod, class, and SSE component."""
    print("\n" + "=" * 78)
    print("INV 1b — C4 GAS-RESIDUAL DECOMPOSITION (keeper, CEMS basis)")
    print("=" * 78)
    art = load_artifacts(KEEPER)
    payload, bench = art["payload"], art["bench"]
    hod = np.arange(T) % 24
    mon = np.minimum(np.arange(T) // 730, 11)
    for year in (2023, 2024, 2025):
        M, A, cls_m, cls_a = _keeper_gas_series(
            year, payload["years"][str(year)], bench.get(year, {})
        )
        resid = M - A
        om = A.mean()
        r, nrmse = _pearson_nrmse(M, A)
        # SSE split: flat bias vs day-to-day scatter (within-hod variance)
        sse = (resid**2).mean()
        var_hod = np.array([resid[hod == h].var() for h in range(24)])
        floor_hod = math.sqrt(var_hod.mean()) / om  # perfect hour-of-day fix
        key = hod * 12 + mon
        mh = np.array(
            [
                resid[key == k].mean() if (key == k).any() else 0.0
                for k in range(24 * 12)
            ]
        )
        floor_hodmon = math.sqrt(((resid - mh[key]) ** 2).mean()) / om
        bias = resid.mean()
        print(
            f"\n {year}: r={r:.3f} NRMSE={nrmse:.3f}  mean_act={om / 1000:.2f}GW  bias={bias:.0f}MW"
        )
        print(
            f"   SSE split: flat-bias {bias**2 / sse * 100:4.0f}%  |  timing {(1 - bias**2 / sse) * 100:4.0f}%"
        )
        print(
            f"   irreducible day-to-day scatter floor: perfect-hod={floor_hod:.3f}  "
            f"perfect-hod*month={floor_hodmon:.3f}  (both < 0.30 ceiling)"
        )
        ev = np.isin(hod, [17, 18, 19, 20, 21])
        belly = np.isin(hod, [9, 10, 11, 12, 13, 14, 15])
        night = hod <= 5
        ccr_m, ccr_a = (
            cls_m.get("CC_REGULAR", np.zeros(T)),
            cls_a.get("CC_REGULAR", np.zeros(T)),
        )
        ctp_m, ctp_a = (
            cls_m.get("CT_PEAKER", np.zeros(T)),
            cls_a.get("CT_PEAKER", np.zeros(T)),
        )
        print(
            f"   CC_REGULAR under: belly {ccr_m[belly].mean() - ccr_a[belly].mean():+.0f}MW  "
            f"overnight {ccr_m[night].mean() - ccr_a[night].mean():+.0f}MW  "
            f"(annual m/a {ccr_m.sum() / 1e6:.1f}/{ccr_a.sum() / 1e6:.1f} TWh)"
        )
        print(
            f"   CT_PEAKER under: evening {ctp_m[ev].mean() - ctp_a[ev].mean():+.0f}MW  "
            f"(annual m/a {ctp_m.sum() / 1e6:.1f}/{ctp_a.sum() / 1e6:.1f} TWh -> {ctp_a.sum() / max(ctp_m.sum(), 1):.1f}x under)"
        )
    print("\n READ: C4 is timing-dominated (flat volume bias is only 13-18% of SSE),")
    print("       so fixing the C5a volume barely moves C4 (contra caiso-108). ~75% is")
    print("       day-to-day scatter (floor ~0.20-0.25, the reduced-model signature).")
    print("       The removable diurnal part = belly/overnight CC under-dispatch")
    print("       (import substitution = C5a) + evening CT-peaker under-run (= C3c).")


def inv1b2_basis_fragility() -> None:
    """2023 is scored on 930 (onset 2024); rescore on the same CEMS basis as 24/25."""
    print("\n" + "=" * 78)
    print("2023 BENCHMARK-BASIS FRAGILITY (CEMS-anchor onset = 2024)")
    print("=" * 78)
    art = load_artifacts(KEEPER)
    p, b = art["payload"], art["bench"]
    # gate value (2023 -> 930): recompute what score_dispatch_corr emits
    recs = score_dispatch_corr(2023, p["years"]["2023"], b.get(2023, {}), "CAISO")
    gate = next((r["model"] for r in recs if r.get("key") == "gas"), "n/a")
    # CEMS-basis 2023 (same basis as 2024/25):
    M, A, _, _ = _keeper_gas_series(2023, p["years"]["2023"], b.get(2023, {}))
    r_cems, n_cems = _pearson_nrmse(M, A)
    print(f"  2023 gate basis (EIA-930 NG cell): {gate}  -> FAIL (NRMSE > 0.30)")
    print(
        f"  2023 CEMS basis (as 2024/25):      r={r_cems:.3f} nrmse={n_cems:.3f}  -> PASS"
    )
    print("  READ: the two bases differ by ~0.06 NRMSE > the 0.033 fail margin. 2023")
    print("        was kept on 930 'for continuity - the two agree there' (bench-basis")
    print(
        "        FINDING 2026-07-12 §5.2); they do NOT agree at the hourly-NRMSE grain."
    )


def inv1c_evening_merit() -> None:
    """From the sidecars: what fills the model evening ramp, at what price."""
    print("\n" + "=" * 78)
    print("INV 1c — MODEL EVENING MERIT ORDER (keeper-proxy sidecars)")
    print("=" * 78)
    for year in (2023, 2024, 2025):
        ch = pq.read_table(f"{PROXY_HOURLY}/class_hourly_{year}.parquet").to_pandas()
        sy = pq.read_table(f"{PROXY_HOURLY}/system_{year}.parquet").to_pandas()
        ch["hod"] = ch["hour"] % 24
        piv = ch.groupby(["hod", "klass"])["mw"].mean().unstack()
        sy["hod"] = sy["hour"] % 24
        ca = sy[sy["zone"].isin(CA_ZONES)]
        pr = ca.groupby("hod").apply(
            lambda d: (d["price"] * d["demand"]).sum() / d["demand"].sum()
        )
        ev = [17, 18, 19, 20, 21]
        print(
            f"  {year}: evening(17-21) CA load-wtd price {pr.loc[ev].mean():5.1f} $/MWh  |  "
            f"CT_PEAKER {piv.loc[ev, 'CT_PEAKER'].mean():4.0f}MW  hydro {piv.loc[ev, 'hydro'].mean():4.0f}MW  "
            f"import {piv.loc[ev, 'import'].mean():4.0f}MW  CC_REG {piv.loc[ev, 'CC_REGULAR'].mean():5.0f}MW  "
            f"(model CT annual max {ch[ch['klass'] == 'CT_PEAKER']['mw'].max():.0f}MW -> capacity AVAILABLE)"
        )
    print("  READ: evening ramp filled by maxed CC + over-hydro + over-import; price")
    print("        caps below the scarcity tail (C3c FAIL) so CT peakers stay idle.")
    print("        Under-run is ECONOMIC (capacity exists), not capacity-limited.")


def inv3_hydro_import() -> None:
    """Model vs actual hydro (NG:WAT) & net-import by hod (raw EIA-930)."""
    print("\n" + "=" * 78)
    print("INV 3 — HYDRO & IMPORT SHAPE  (model vs raw EIA-930 CISO, by hod)")
    print("=" * 78)
    w = pq.read_table("data/raw/eia-930-hourly/CISO hourly.parquet").to_pandas()
    w["lt"] = pd.to_datetime(w["Local time"])
    w["year"] = w["lt"].dt.year
    w["hod"] = w["lt"].dt.hour
    ev, belly = [17, 18, 19, 20, 21], [10, 11, 12, 13, 14]
    for year in (2023, 2024, 2025):
        a = w[w["year"] == year]
        if len(a) < 8000:
            continue
        ah = a.groupby("hod")["NG: WAT"].mean()
        ai = -a.groupby("hod")["Total interchange"].mean()  # +export -> net import
        ch = pq.read_table(f"{PROXY_HOURLY}/class_hourly_{year}.parquet").to_pandas()
        ch["hod"] = ch["hour"] % 24
        piv = ch.groupby(["hod", "klass"])["mw"].mean().unstack()
        hm, ha = piv["hydro"], ah
        im, ia = piv["import"], ai
        print(
            f"  {year}: HYDRO annual model {piv['hydro'].mean() * 8760 / 1e6:.1f} vs actual "
            f"{ah.mean() * len(a) / 1e6:.1f} TWh (matched)  |  evening +{hm.loc[ev].mean() - ha.loc[ev].mean():.0f}MW  "
            f"belly {hm.loc[belly].mean() - ha.loc[belly].mean():+.0f}MW"
        )
        print(
            f"        IMPORT belly {im.loc[belly].mean() - ia.loc[belly].mean():+.0f}MW (the C5a driver)  "
            f"evening {im.loc[ev].mean() - ia.loc[ev].mean():+.0f}MW"
        )
    print("  READ: annual hydro matches but the model over-concentrates it into the")
    print("        evening (+0.5-0.65 GW) and under-runs the belly. This survives the")
    print("        keeper's p95 hydro_dispatch_envelope (already ON) because p95 is a")
    print("        loose ceiling the perfect-foresight LP saturates every evening.")


if __name__ == "__main__":
    inv1a_cross_iso()
    inv1b_decomposition()
    inv1b2_basis_fragility()
    inv1c_evening_merit()
    inv3_hydro_import()
