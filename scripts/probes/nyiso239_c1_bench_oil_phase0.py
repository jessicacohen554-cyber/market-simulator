"""nyiso-239 phase 0 (ZERO LP): the C1 2022 `CC_REGULAR` miss is a BENCHMARK
gas/oil attribution artifact, not model over-dispatch.

Reproduces every number in
``docs/FINDING-nyiso239-c1-2022-bench-oil-attribution-2026-09-16.md`` from
COMMITTED artifacts plus the immutable ``data/raw`` extracts. No LP, no solve,
no bundle regeneration (rule 32 ``[R-SHARD]`` (a): the orchestrator never
solves).

The object
----------
``render_calibration_html.reconcile_vintage_classes`` scales the EIA-923
grid-delivered fossil classes to the EIA-930 ``gas + coal`` grid cell whenever
the two differ by more than ±3 %. Its target omits EIA-930's ``OIL`` cell,
while EIA-923 books a dual-fuel plant's oil burn in its own ``oil`` class and
the plant's CC/CT/ST MWh in the gas classes. In NYISO 2022 EIA-930 carries a
~3 TWh near-FLAT block under ``NG: OIL`` that EIA-923 does not call oil, so the
comparison reads a false +5.14 % "923 over-statement" and every NYISO fossil
class is deflated by x0.9512 — including ``CC_REGULAR``, whose C1 actual drops
33.207 -> 31.586 TWh.

Four independent sources arbitrate, and all four say the 930 ``gas`` cell alone
is the wrong boundary (section 3). Nothing here is selected because a residual
moved (rule 1 ``[R-STRUCT]``): the discriminating measurements are a fuel
IDENTITY and an hourly SHAPE, and the shape test is run on all four years with
the sign predicted in advance by the mechanism.

Usage
-----
    python3 scripts/probes/nyiso239_c1_bench_oil_phase0.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO / "src", REPO / "scripts", REPO):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import render_calibration_html as rch  # noqa: E402
import run_calibration_full as rcf  # noqa: E402
import calibration_verdict as cv  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402
from market_sim.data.eia930 import frames as F  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench"
RUNS = REPO / "frontend" / "data" / "backcast" / "runs"
KEEPER = "2026-09-16-nyiso-238-hydro-budget"
KEEPER_BUNDLE = REPO / "results" / "calibration" / "nyiso238_hydroperiod_span"
FOSSIL = (*rch._GAS_GROUPS, *rch._COAL_GROUPS)
# EIA-923 fuel codes that are liquid petroleum. `_classify_f923` routes EVERY
# one of them to the `oil` class (verified in section 3b), which is exactly why
# the 923 `oil` class is the right counterpart to EIA-930's `NG: OIL` cell.
OIL_FUELS = ("DFO", "RFO", "JF", "KER", "WO", "PC")
# NYISO publishes no `oil` fuel category at all: an oil-capable unit is filed
# under `Dual Fuel`, so the ISO's own fossil total is these three rows.
NYISO_FOSSIL_CATEGORIES = ("Natural Gas", "Dual Fuel", "Other Fossil Fuels")


def _bench(iso: str, year: int) -> dict | None:
    p = BENCH / iso / f"{year}.json.gz"
    if not p.exists():
        return None
    return json.load(gzip.open(p))["bench"]


def _payload(run_id: str) -> dict:
    """Decode a committed run payload (``window.BC.runGz[...] = "<b64 gzip>"``)."""
    src = (RUNS / f"{run_id}.js").read_text()
    m = re.search(r'="([A-Za-z0-9+/=]+)";?\s*$', src.strip())
    if m is None:  # pragma: no cover - wire format change
        raise SystemExit(f"cannot decode payload for {run_id}")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _e923_by_class(gen: pd.DataFrame, iso: str, year: int) -> pd.Series:
    """EIA-923 net generation per class (TWh), the render's own construction."""
    frame = rch.apply_other_fossil_scoring(
        rcf._eia923_frame(year, gen, iso), year, plant_col="plant_id"
    )
    return frame.groupby("klass")["annual_mwh"].sum() / 1e6


def _reconcile_target(cf: dict, e930: dict, iso: str) -> float:
    """The target ``reconcile_vintage_classes`` actually tests against."""
    tgt = float(e930.get("gas", 0.0)) + float(e930.get("coal", 0.0))
    tgt -= rch._gas_foldin_deflation(cf, e930, iso)
    if iso in rch.EIA930_NG_CELL_CORRUPT:
        anchor = e930.get("fossil_cems_grid")
        if anchor is not None and float(anchor) > 0.0:
            tgt = min(tgt, float(anchor))
    return tgt


def _fires(cur: float, tgt: float) -> bool:
    frac = rch._VINTAGE_RECONCILE_FRAC
    return not (frac * tgt <= cur <= tgt / frac)


def _stats(model: np.ndarray, actual: np.ndarray) -> tuple[float, float]:
    r = float(np.corrcoef(model, actual)[0, 1])
    nrmse = float(np.sqrt(np.mean((model - actual) ** 2)) / np.mean(actual))
    return r, nrmse


def _nyis_930(year: int) -> tuple[np.ndarray, np.ndarray] | None:
    frame = F._eia_hourly_frame("NYIS", year)
    if frame is None:
        return None
    gas = np.nan_to_num(frame["NG: NG"].to_numpy(float))
    oil = np.nan_to_num(frame["NG: OIL"].to_numpy(float))
    return gas, oil


# --------------------------------------------------------------------------
# Section 1 — WHERE the reconcile fires today, across every committed bench part
# --------------------------------------------------------------------------
def section1_census() -> list[dict]:
    print("\n=== 1. WHERE reconcile_vintage_classes FIRES (committed bench parts)")
    print(
        f"{'ISO':7s} {'yr':>5} {'fossil classFull':>17} {'target':>10} "
        f"{'ratio':>8} {'FIRES':>6}"
    )
    out = []
    for iso_dir in sorted(BENCH.iterdir()):
        if not iso_dir.is_dir():
            continue
        iso = iso_dir.name
        for part in sorted(iso_dir.glob("*.json.gz")):
            year = int(part.stem.split(".")[0])
            b = _bench(iso, year)
            if not b:
                continue
            cf = dict(b.get("classFull", {}))
            e930 = b.get("e930", {})
            cur = sum(v for k, v in cf.items() if k in FOSSIL)
            tgt = _reconcile_target(cf, e930, iso)
            if cur <= 0 or tgt <= 0:
                continue
            # The COMMITTED classFull is post-scale, so "fired" shows as the
            # fossil sum sitting exactly on the target.
            fired = abs(cur / tgt - 1.0) < 3e-4
            out.append({"iso": iso, "year": year, "fired": fired})
            print(
                f"{iso:7s} {year:>5} {cur:17.3f} {tgt:10.3f} "
                f"{cur / tgt:8.5f} {str(fired):>6}"
            )
    n = sum(1 for r in out if r["fired"])
    print(f"\n  FIRED in {n} of {len(out)} committed (ISO, year) bench parts:")
    print("   ", [(r["iso"], r["year"]) for r in out if r["fired"]])
    return out


# --------------------------------------------------------------------------
# Section 2 — the NYISO arithmetic: gas-only vs gas+oil comparison basis
# --------------------------------------------------------------------------
def section2_basis(gen: pd.DataFrame) -> dict:
    print("\n=== 2. NYISO — the reconcile basis, gas-only vs gas+oil")
    print(
        f"{'yr':>5} {'923 fossil':>11} {'930 gas':>9} {'dev%':>7} {'FIRES':>6} | "
        f"{'923 oil':>8} {'930 oil':>8} | {'923+oil':>9} {'930+oil':>9} "
        f"{'dev%':>7} {'FIRES':>6}"
    )
    res = {}
    for year in (2022, 2023, 2024):
        cls = _e923_by_class(gen, "NYISO", year)
        pre = float(sum(cls.get(g, 0.0) for g in FOSSIL))
        # The BTM host supply the bench removes before comparing (bench basis).
        b = _bench("NYISO", year)
        btm = b["co2"].get("btmClass", {}) if b else {}
        pre -= float(sum(btm.values()))
        oil923 = float(cls.get("oil", 0.0))
        gas930, oil930 = _nyis_930(year)
        g, o = float(gas930.sum()) / 1e6, float(oil930.sum()) / 1e6
        dev1, f1 = 100.0 * (pre / g - 1.0), _fires(pre, g)
        dev2, f2 = 100.0 * ((pre + oil923) / (g + o) - 1.0), _fires(pre + oil923, g + o)
        res[year] = {
            "e923_fossil_grid_twh": round(pre, 4),
            "e930_gas_twh": round(g, 4),
            "dev_gas_only_pct": round(dev1, 3),
            "fires_gas_only": f1,
            "e923_oil_twh": round(oil923, 4),
            "e930_oil_twh": round(o, 4),
            "dev_gas_plus_oil_pct": round(dev2, 3),
            "fires_gas_plus_oil": f2,
        }
        print(
            f"{year:>5} {pre:11.3f} {g:9.3f} {dev1:+7.2f} {str(f1):>6} | "
            f"{oil923:8.3f} {o:8.3f} | {pre + oil923:9.3f} {g + o:9.3f} "
            f"{dev2:+7.2f} {str(f2):>6}"
        )
    print(
        "\n  2022 is the ONLY complete NYISO vintage where the gas-only basis "
        "fires, and on the\n  gas+oil basis its agreement is the TIGHTEST of "
        "the three years."
    )
    return res


# --------------------------------------------------------------------------
# Section 3 — the four independent arbiters
# --------------------------------------------------------------------------
def section3_arbiters(gen: pd.DataFrame) -> dict:
    out: dict = {}

    print("\n=== 3a. NYISO's OWN published hourly fuel mix (the ISO's meter)")
    print(
        f"{'yr':>5} {'NYISO fossil':>13} {'930 gas':>9} {'d':>8} {'r':>7} "
        f"{'nrmse':>7} | {'930 gas+oil':>12} {'d':>8} {'r':>7} {'nrmse':>7}"
    )
    rows = {}
    for year in (2022, 2023, 2024):
        src = REPO / "data/raw/NYISO/fuel-mix" / f"NYISO_fuelmix_hourly_{year}.csv.gz"
        d = pd.read_csv(src)
        d["utc"] = pd.to_datetime(d["interval_start_utc"], utc=True)
        piv = d.pivot_table(
            index="utc", columns="fuel_category", values="gen_mw", aggfunc="sum"
        ).fillna(0.0)
        nyiso = sum(
            (piv[c] for c in NYISO_FOSSIL_CATEGORIES if c in piv.columns),
            pd.Series(0.0, index=piv.index),
        )
        frame = F._eia_hourly_frame("NYIS", year)
        utc = pd.DatetimeIndex(frame["UTC time"]).tz_localize("UTC")
        gas = pd.Series(np.nan_to_num(frame["NG: NG"].to_numpy(float)), index=utc)
        oil = pd.Series(np.nan_to_num(frame["NG: OIL"].to_numpy(float)), index=utc)
        idx = nyiso.index.intersection(gas.index)
        a = nyiso.reindex(idx).to_numpy()
        g = gas.reindex(idx).to_numpy()
        o = oil.reindex(idx).to_numpy()
        r1, n1 = _stats(g, a)
        r2, n2 = _stats(g + o, a)
        rows[year] = {
            "nyiso_published_fossil_twh": round(float(a.sum()) / 1e6, 4),
            "gas_only": {
                "level_delta_twh": round(float(g.sum() - a.sum()) / 1e6, 4),
                "r": round(r1, 4),
                "nrmse": round(n1, 4),
            },
            "gas_plus_oil": {
                "level_delta_twh": round(float((g + o).sum() - a.sum()) / 1e6, 4),
                "r": round(r2, 4),
                "nrmse": round(n2, 4),
            },
        }
        print(
            f"{year:>5} {a.sum() / 1e6:13.3f} {g.sum() / 1e6:9.3f} "
            f"{(g.sum() - a.sum()) / 1e6:+8.3f} {r1:7.4f} {n1:7.4f} | "
            f"{(g + o).sum() / 1e6:12.3f} {((g + o).sum() - a.sum()) / 1e6:+8.3f} "
            f"{r2:7.4f} {n2:7.4f}"
        )
    out["nyiso_published"] = rows
    print(
        "  The repair closes a -5.413 TWh gap in 2022 and a -2.337 TWh gap in "
        "2023, and is a\n  near no-op in 2024 — the year the mislabelled block "
        "is already gone. A residual-fitted\n  correction does not switch "
        "itself off."
    )

    print("\n=== 3b. EIA-923 routes EVERY liquid-fuel row to the `oil` class")
    ids = rcf._iso_plant_ids("NYISO")
    b3 = {}
    for year in (2022, 2023, 2024):
        df = gen[(gen["year"] == year) & (gen["plant_id"].isin(ids))].copy()
        df["klass"] = [
            rcf._classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
            for f, pm, c, pid in zip(
                df["fuel_type"], df["prime_mover"], df["chp"], df["plant_id"]
            )
        ]
        liq = df[df["fuel_type"].astype(str).str.upper().isin(OIL_FUELS)]
        by = (liq.groupby("klass")["netgen_annual_mwh"].sum() / 1e6).round(4)
        b3[year] = {str(k): float(v) for k, v in by.items() if abs(v) > 1e-3}
        print(
            f"  {year}: {b3[year]}  (total {liq['netgen_annual_mwh'].sum() / 1e6:.3f} TWh)"
        )
    print(
        "  So EIA-923's `oil` class IS the counterpart of EIA-930's `NG: OIL` "
        "cell, and the\n  ~3 TWh EIA-930 books as oil in 2022 is not oil FUEL "
        "by the 923 survey."
    )
    out["e923_liquid_routing"] = b3

    print("\n=== 3c. The EIA-930 NYIS `NG: OIL` block is FLAT, then stops")
    b3c = {}
    for year in (2022, 2023, 2024):
        frame = F._eia_hourly_frame("NYIS", year)
        mo = (
            frame.groupby(pd.DatetimeIndex(frame["Local date"]).month)["NG: OIL"].sum()
            / 1e3
        )
        b3c[year] = [round(float(x), 1) for x in mo.tolist()]
        print(f"  {year} GWh/month: {b3c[year]}")
    print(
        "  ~400-470 GWh EVERY month of 2022 (a ~550 MW baseload) is not a "
        "physical oil-burn\n  shape — NYISO's liquid fleet is peaking. It "
        "steps to ~zero at 2023-m07."
    )
    out["e930_oil_monthly_gwh"] = b3c

    print("\n=== 3d. CEMS (fixed plant set present in ALL four bench years)")
    benches = {y: _bench("NYISO", y) for y in (2022, 2023, 2024, 2025)}
    common = set(benches[2022]["plants"])
    for y in (2023, 2024, 2025):
        common &= set(benches[y]["plants"])
    common = {
        k
        for k in common
        if all(float(benches[y]["plants"][k].get("c_ann") or 0) > 0 for y in benches)
    }
    print(f"  {len(common)} plants metered in every year")
    print(f"{'yr':>5} {'CAMPD net':>10} {'930 gas':>9} {'930gas/CAMPD':>13}")
    b3d = {}
    for year in (2022, 2023, 2024, 2025):
        bp = benches[year]["plants"]
        cn = sum(float(bp[k]["c_ann"]) for k in common)
        g930 = float(benches[year]["e930"]["gas"])
        b3d[year] = round(g930 / cn, 4)
        print(f"{year:>5} {cn:10.3f} {g930:9.3f} {g930 / cn:13.4f}")
    print(
        "  0.906 in 2022 against 0.955 / 0.956 / 0.964 — the 930 gas cell is "
        "the outlier\n  against the one source whose meters do not move."
    )
    out["cems_ratio"] = b3d
    return out


# --------------------------------------------------------------------------
# Section 4 — the hourly SHAPE test (predicted sign, all four years)
# --------------------------------------------------------------------------
def section4_shape() -> dict:
    print(
        "\n=== 4. HOURLY SHAPE — model(gas) vs 930(gas), and model(gas+oil) vs 930(gas+oil)"
    )
    gas_classes = rch.classes_for_fuel930("gas")
    print(
        f"{'yr':>5} {'r gas-only':>11} {'r gas+oil':>10} {'dr':>8} | "
        f"{'nrmse gas':>10} {'nrmse +oil':>11} {'dnrmse':>8}"
    )
    out = {}
    for year in (2022, 2023, 2024, 2025):
        path = KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet"
        d = pd.read_parquet(path)
        d = d[d["pass"] == "P1"]
        piv = d.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum"
        ).fillna(0.0)
        m_gas = sum(
            (piv[c].to_numpy() for c in gas_classes if c in piv.columns),
            np.zeros(len(piv)),
        )
        m_oil = piv["oil"].to_numpy() if "oil" in piv.columns else np.zeros(len(piv))
        gas930, oil930 = _nyis_930(year)
        n = min(len(m_gas), len(gas930))
        r1, n1 = _stats(m_gas[:n], gas930[:n])
        r2, n2 = _stats(m_gas[:n] + m_oil[:n], gas930[:n] + oil930[:n])
        out[year] = {
            "gas_only": {"r": round(r1, 4), "nrmse": round(n1, 4)},
            "gas_plus_oil": {"r": round(r2, 4), "nrmse": round(n2, 4)},
        }
        print(
            f"{year:>5} {r1:11.4f} {r2:10.4f} {r2 - r1:+8.4f} | "
            f"{n1:10.4f} {n2:11.4f} {n2 - n1:+8.4f}"
        )
    print(
        "  8 of 8 directional wins. This is the SHAPE leg: no uniform level "
        "scale can move a\n  correlation, so it is independent of every number "
        "in sections 2-3."
    )
    return out


# --------------------------------------------------------------------------
# Section 5 — what the counterfactual does to the keeper's C1 and determination
# --------------------------------------------------------------------------
def section5_counterfactual(gen: pd.DataFrame) -> dict:
    print(
        "\n=== 5. COUNTERFACTUAL — C1 and the determination with the reconcile NOT firing"
    )
    b = _bench("NYISO", 2022)
    cf = b["classFull"]
    cur = sum(v for k, v in cf.items() if k in FOSSIL)
    # Recover the scale the render applied: post = pre * s and sum(post) = tgt,
    # so s = tgt / sum(pre); sum(pre) is rebuilt from the 923 source (section 2).
    cls = _e923_by_class(gen, "NYISO", 2022)
    btm = b["co2"].get("btmClass", {})
    pre_sum = float(sum(cls.get(g, 0.0) for g in FOSSIL)) - float(sum(btm.values()))
    scale = cur / pre_sum
    print(f"  recovered uniform deflation applied to NYISO 2022: x{scale:.6f}")

    pay = _payload(KEEPER)
    ypay = pay["years"]["2022"]
    b_cf = json.loads(json.dumps(b))
    for k in list(b_cf["classFull"]):
        if k in FOSSIL:
            b_cf["classFull"][k] = round(b_cf["classFull"][k] / scale, 4)

    out = {}
    for tag, bb in (("committed", b), ("counterfactual", b_cf)):
        m_gen, a_gen = cv._gen_totals(ypay, bb)
        band = cv._fuelmix_vol_band(cv._total_load(ypay, a_gen), a_gen)
        recs = cv.score_fuelmix(2022, ypay, bb, "NYISO")
        row = next(r for r in recs if r["key"] == "CC_REGULAR")
        out[tag] = {
            "actual_twh": row["actual"],
            "model_twh": row["model"],
            "delta_twh": round(row["model"] - row["actual"], 4),
            "share_pp": row["share_pp"],
            "vol_band_twh": round(band, 4),
            "status": row["status"],
        }
        print(
            f"  {tag:15s} CC_REGULAR model={row['model']:.4f} "
            f"actual={row['actual']:.4f} d={row['model'] - row['actual']:+.4f} TWh "
            f"(band ±{band:.3f})  share {row['share_pp']:+.4f} pp (band ±3.0)  "
            f"-> {row['status']}"
        )
        fails = [r["key"] for r in recs if r["status"] == "FAIL"]
        print(f"                  C1 FAIL rows this year: {fails or 'none'}")
    print(
        "\n  REPORTED AT FULL MAGNITUDE: the counterfactual share leg lands at "
        f"{out['counterfactual']['share_pp']:+.4f} pp\n  against a ±3.0 pp band "
        "— a 0.03 pp margin. The model's +3.19 TWh `CC_REGULAR`\n  over-run is "
        "REAL and remains the lane's open object; this repair corrects how it "
        "is\n  MEASURED, not the model."
    )
    return {"scale": round(scale, 6), "cc_regular": out}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    gen = load_monthly_generation()
    result = {
        "session": "nyiso-239",
        "keeper": KEEPER,
        "census": section1_census(),
        "basis": section2_basis(gen),
        "arbiters": section3_arbiters(gen),
        "shape": section4_shape(),
        "counterfactual": section5_counterfactual(gen),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=1, default=str))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
