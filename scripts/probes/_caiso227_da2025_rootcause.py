"""caiso-227 step 1 — ZERO-SOLVE root-cause decomposition of the **2025
DA-basis** C3a residual on keeper ``2026-08-26-caiso-220-c1-crosswalk``.
NO LP, NO SOLVE — committed bytes plus the licensed caiso-105/131
``run_year(fleet_only=True)`` offer reconstruction (imported unchanged from
``_caiso202_marginal_rung.py`` per the caiso-227 charter's reuse directive).

Why this probe exists: FINDING-caiso202 §A established 2025 as the one year
that fails C3a on BOTH settlement bases (+10.2 % vs DA), and localized the
DA-basis gap to Sep–Dec (58 %) + the spring belly, attributing it to "the
standing CC-side supply-state residual" — an attribution to a LANE. This
probe takes it to root cause: which hours, which marginal rung, what the
model's supply state is there vs the MEASURED one (EIA-930 CISO hourly fuel
mix), and what changed 2024→2025 in reality that the model does not do.

Sections:

* **A** — the DA-basis month × hod-band residual map for 2025 (2023/2024
  controls) on THIS keeper — the caiso-202 §A/§B construction re-pointed at
  the caiso-220 bundle, scored against the DA actual on the rubric's rt_lw
  common weights.
* **B** — marginal-rung attribution of the 2025 DA-basis positive gap
  (caiso-202 §C machinery, ``act = da``): which offer rung sets the model's
  CA λ in the DA-overrun hours.
* **C** — the supply-state witness: model class dispatch + storage + implied
  net interchange vs the measured EIA-930 hourly fuel mix, per gap cell.
* **D** — the 2024→2025 delta: model YoY λ change vs the DA actual's YoY
  change, by month, with the matching measured vs model supply-state deltas.
* **E** — model binding-state witness in the gap hours: CA zone-λ dispersion
  (internal congestion), storage/PS activity, hydro dispatch level.

Every input is committed: the keeper's ``hourly/`` sidecars, the actual-LMP
reference (``rt`` + ``da``), the EIA-930 ``CISO hourly`` extract, the bench
``avgLMP`` control values, and the same measured-hub/constants path the
keeper's injector uses (via the imported caiso-202 module).

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso227_da2025_rootcause.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso220_c1_crosswalk"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
OUT = REPO / "results/calibration/_caiso227_da2025_rootcause.json"

# caiso-202 machinery, reused unchanged (charter directive); only the bundle
# and cache locations are re-pointed at this keeper / this session.
_spec = importlib.util.spec_from_file_location(
    "_caiso202_marginal_rung", REPO / "scripts/probes/_caiso202_marginal_rung.py"
)
M202 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M202)
M202.BUNDLE = BUNDLE
M202.CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "a67b5623-720c-5724-b031-e3420dd378fb/scratchpad/caiso227"
)

GAS_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS")
SEPDEC = (9, 10, 11, 12)
SPRING = (3, 4, 5)
BELLY = (10, 11, 12, 13, 14, 15)

RESULT: dict = {}


def actuals(year: int) -> pd.DataFrame:
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour").reindex(range(HOURS))


def month_of_hour(year: int) -> np.ndarray:
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(HOURS + 24), "h")
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def class_mw(year: int) -> pd.DataFrame:
    d = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="klass", values="mw").reindex(
        range(HOURS)
    )


def storage_mw(year: int) -> pd.DataFrame:
    d = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(
        index="hour", columns="tech", values=["charge_mw", "discharge_mw"]
    ).reindex(range(HOURS))


def model_state(year: int) -> dict[str, np.ndarray]:
    """The model's CA supply state per hour, EIA-930-comparable buckets."""
    cm = class_mw(year)
    st = storage_mw(year)
    sc = M202.sidecars(year)
    ca_zones = [z for z in sc["demand"].columns if not str(z).startswith("WECC")]
    demand = sc["demand"][ca_zones].sum(axis=1).to_numpy()
    gas = cm[[c for c in GAS_CLASSES if c in cm]].sum(axis=1).to_numpy()
    ps_dis = st[("discharge_mw", "pumped_storage")].to_numpy()
    ps_chg = st[("charge_mw", "pumped_storage")].to_numpy()
    li_dis = st[("discharge_mw", "li_ion")].to_numpy()
    li_chg = st[("charge_mw", "li_ion")].to_numpy()
    out = {
        "demand": demand,
        "gas": gas,
        "hydro_net": cm["hydro"].to_numpy() + ps_dis - ps_chg,
        "hydro_conv": cm["hydro"].to_numpy(),
        "ps_net": ps_dis - ps_chg,
        "ps_chg": ps_chg,
        "battery_net": li_dis - li_chg,
        "battery_chg": li_chg,
        "solar": cm["solar"].to_numpy(),
        "wind": cm["wind"].to_numpy(),
        "nuclear": cm["nuclear"].to_numpy(),
        "other": (
            cm[[c for c in ("OTHER", "biomass") if c in cm]].sum(axis=1).to_numpy()
        ),
        "import_mw": cm["import"].to_numpy() if "import" in cm else np.zeros(HOURS),
    }
    # implied net interchange (EIA sign: positive = net EXPORT out of CA)
    gen_ca = (
        out["gas"]
        + cm["hydro"].to_numpy()
        + out["solar"]
        + out["wind"]
        + out["nuclear"]
        + out["other"]
        + cm[[c for c in ("COAL", "oil") if c in cm]].sum(axis=1).to_numpy()
    )
    storage_net = ps_dis - ps_chg + li_dis - li_chg
    out["interchange"] = gen_ca + storage_net - demand
    return out


def measured_state(year: int) -> dict[str, np.ndarray]:
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    b = load_eia_hourly_benchmark(ISO, year)
    return {
        "gas": b["gas"],
        "hydro_net": b["hydro"],  # EIA-930 WAT is hydro NET of PS pumping (S2 wall)
        "solar": b["solar"],
        "wind": b["wind"],
        "nuclear": b["nuclear"],
        "other": b["other"],  # CISO: batteries net + non-folded geo/biomass
        "interchange": b["interchange"],  # positive = net export
    }


def gap_frame(year: int):
    """Per-hour DA/RT gap contributions on the rubric's rt_lw common weights."""
    sc = M202.sidecars(year)
    lam = M202.ca_lambda(sc)
    a = actuals(year)
    w = M202.rubric_weights(year)
    da = a["da"].to_numpy()
    rt = a["rt"].to_numpy()
    ok = ~np.isnan(da)
    wsum = w[ok].sum()
    contrib_da = np.where(ok, w * (lam - np.where(ok, da, 0.0)), 0.0) / wsum
    okr = ~np.isnan(rt)
    contrib_rt = np.where(okr, w * (lam - np.where(okr, rt, 0.0)), 0.0) / w[okr].sum()
    return sc, lam, da, rt, w, ok, contrib_da, contrib_rt


def section_a() -> dict:
    print("=" * 78)
    print("§A — DA-basis residual map on keeper caiso-220 (rt_lw common weights)")
    print("=" * 78)
    out = {}
    for year in YEARS:
        sc, lam, da, rt, w, ok, cda, crt = gap_frame(year)
        mo = month_of_hour(year)
        hd = np.arange(HOURS) % 24
        gap = cda.sum()
        amean = np.average(da[ok], weights=w[ok])
        mmean = np.average(lam[ok], weights=w[ok])
        sepdec = float(cda[np.isin(mo, SEPDEC)].sum())
        spring_belly = float(cda[np.isin(mo, SPRING) & np.isin(hd, BELLY)].sum())
        spring_all = float(cda[np.isin(mo, SPRING)].sum())
        print(
            f"\n[{year}] model lw {mmean:.2f} vs DA {amean:.2f} -> gap {gap:+.2f} "
            f"({gap / amean * 100:+.1f}%)  [RT-basis gap {crt.sum():+.2f}]"
        )
        rows = []
        print(f"  {'month':<6}{'belly10-15':>12}{'eve17-21':>10}{'night0-6':>10}"
              f"{'other':>10}{'total':>10}")
        for m in range(1, 13):
            mm = mo == m
            r = [
                float(cda[mm & np.isin(hd, BELLY)].sum()),
                float(cda[mm & np.isin(hd, (17, 18, 19, 20, 21))].sum()),
                float(cda[mm & np.isin(hd, (0, 1, 2, 3, 4, 5, 6))].sum()),
            ]
            r.append(float(cda[mm].sum()) - sum(r))
            tot = float(cda[mm].sum())
            rows.append({"month": m, "belly": r[0], "eve": r[1], "night": r[2],
                         "other": r[3], "total": tot})
            print(f"  {m:<6}{r[0]:>+12.3f}{r[1]:>+10.3f}{r[2]:>+10.3f}"
                  f"{r[3]:>+10.3f}{tot:>+10.3f}")
        print(f"  Sep-Dec {sepdec:+.3f} ({sepdec / gap * 100:.0f}% of gap); "
              f"spring(3-5) {spring_all:+.3f} (belly part {spring_belly:+.3f})")
        out[year] = {
            "model_lw": round(float(mmean), 3),
            "da_lw": round(float(amean), 3),
            "gap_da": round(float(gap), 3),
            "gap_da_pct": round(float(gap / amean * 100), 2),
            "gap_rt": round(float(crt.sum()), 3),
            "sepdec": round(sepdec, 3),
            "spring": round(spring_all, 3),
            "spring_belly": round(spring_belly, 3),
            "months": rows,
        }
    return out


def section_b() -> dict:
    print("\n" + "=" * 78)
    print("§B — marginal-rung attribution of the DA-basis positive gap")
    print("=" * 78)
    from market_sim.config.fuel_trajectories import STATE_CARBON_PRICE_BY_ISO

    out = {}
    for year in (2024, 2025):
        carbon = STATE_CARBON_PRICE_BY_ISO["CAISO"][year]
        sc, lam, da, rt, w, ok, cda, _ = gap_frame(year)
        legs = M202.import_leg_prices(year, carbon)
        rec = M202.fleet_recon(year)
        mc, cap, klass = rec["mc"], rec["cap"], rec["klass"]
        if mc.ndim == 1:
            mc = np.tile(mc[:, None], (1, HOURS))
        keep = klass != "biomass"  # caiso-202 §C.1: the solve drops these units
        mc, cap, klass = mc[keep], cap[keep], klass[keep]

        pos = cda > 0
        idx = np.where(pos)[0]
        TOL = 0.75
        cats: dict[str, float] = {}
        cat_hours: dict[str, int] = {}
        for h in idx:
            best_name, best_d = None, np.inf
            for name, series in legs.items():
                d = abs(series[h] - lam[h])
                if d < best_d:
                    best_name, best_d = name, d
            avail = cap[:, h] > 1.0
            if avail.any():
                dmc = np.abs(mc[avail, h] - lam[h])
                j = int(np.argmin(dmc))
                if dmc[j] < best_d:
                    best_name = f"fleet:{klass[np.where(avail)[0][j]]}"
                    best_d = dmc[j]
            if best_d > TOL:
                best_name = "unmatched"
            cats[best_name] = cats.get(best_name, 0.0) + cda[h]
            cat_hours[best_name] = cat_hours.get(best_name, 0) + 1
        total_pos = cda[pos].sum()
        print(f"\n[{year}] DA-positive hours n={pos.sum()}, gap +{total_pos:.2f}")
        rows = {}
        for name, g in sorted(cats.items(), key=lambda kv: -kv[1]):
            print(f"  {name:<30}{cat_hours[name]:>6} h {g:>+8.3f} "
                  f"{g / total_pos * 100:>5.0f}%")
            rows[name] = {"hours": cat_hours[name], "gap": round(float(g), 3),
                          "share_pct": round(float(g / total_pos * 100), 1)}
        out[year] = {"n_pos": int(pos.sum()), "gap_pos": round(float(total_pos), 3),
                     "rungs": rows}
    return out


def _cell_table(ms, es, mask, w, label) -> dict:
    keys = ("gas", "hydro_net", "solar", "wind", "nuclear", "other", "interchange")
    print(f"\n  [{label}] n={mask.sum()} h  (MW means over the cell; "
          f"delta = model - measured)")
    print(f"    {'series':<12}{'model':>9}{'measured':>10}{'delta':>9}")
    row = {}
    for k in keys:
        mv = float(np.nanmean(ms[k][mask]))
        ev = float(np.nanmean(es[k][mask]))
        print(f"    {k:<12}{mv:>9.0f}{ev:>10.0f}{mv - ev:>+9.0f}")
        row[k] = {"model": round(mv), "measured": round(ev),
                  "delta": round(mv - ev)}
    for k in ("ps_net", "ps_chg", "battery_net", "battery_chg", "hydro_conv",
              "import_mw", "demand"):
        row[k] = {"model": round(float(np.nanmean(ms[k][mask])))}
    print(f"    model-only: PS net {row['ps_net']['model']:+d} "
          f"(chg {row['ps_chg']['model']}), battery net "
          f"{row['battery_net']['model']:+d} (chg {row['battery_chg']['model']}), "
          f"conv hydro {row['hydro_conv']['model']}, import {row['import_mw']['model']}")
    return row


def section_c() -> dict:
    print("\n" + "=" * 78)
    print("§C — supply-state witness: model vs measured (EIA-930) in the gap cells")
    print("=" * 78)
    out = {}
    for year in (2024, 2025):
        sc, lam, da, rt, w, ok, cda, _ = gap_frame(year)
        mo = month_of_hour(year)
        hd = np.arange(HOURS) % 24
        ms = model_state(year)
        es = measured_state(year)
        print(f"\n[{year}]")
        cells = {
            "all_hours": ok,
            "da_pos_gap": ok & (cda > 0),
            "sepdec_belly": ok & np.isin(mo, SEPDEC) & np.isin(hd, BELLY),
            "sepdec_eve": ok & np.isin(mo, SEPDEC) & np.isin(hd, (17, 18, 19, 20, 21)),
            "spring_belly": ok & np.isin(mo, SPRING) & np.isin(hd, BELLY),
        }
        out[year] = {
            name: _cell_table(ms, es, mask, w, f"{year} {name}")
            for name, mask in cells.items()
        }
    return out


def section_d() -> dict:
    print("\n" + "=" * 78)
    print("§D — the 2024→2025 delta: what reality did that the model does not")
    print("=" * 78)
    frames = {}
    for year in (2024, 2025):
        sc, lam, da, rt, w, ok, cda, _ = gap_frame(year)
        frames[year] = {
            "lam": lam, "da": da, "w": w, "ok": ok,
            "mo": month_of_hour(year),
            "ms": model_state(year), "es": measured_state(year),
        }
    out = {"monthly": []}
    print(f"\n  per-month lw means: model λ and DA actual, 2024 vs 2025")
    print(f"  {'mon':<4}{'mod24':>8}{'mod25':>8}{'Δmod':>8}{'da24':>8}{'da25':>8}"
          f"{'Δda':>8}{'Δgap':>8}")
    for m in range(1, 13):
        vals = {}
        for year in (2024, 2025):
            f = frames[year]
            mm = (f["mo"] == m) & f["ok"]
            vals[year] = (
                np.average(f["lam"][mm], weights=f["w"][mm]),
                np.average(f["da"][mm], weights=f["w"][mm]),
            )
        dmod = vals[2025][0] - vals[2024][0]
        dda = vals[2025][1] - vals[2024][1]
        print(f"  {m:<4}{vals[2024][0]:>8.2f}{vals[2025][0]:>8.2f}{dmod:>+8.2f}"
              f"{vals[2024][1]:>8.2f}{vals[2025][1]:>8.2f}{dda:>+8.2f}"
              f"{dmod - dda:>+8.2f}")
        out["monthly"].append({
            "month": m, "model_2024": round(float(vals[2024][0]), 2),
            "model_2025": round(float(vals[2025][0]), 2),
            "da_2024": round(float(vals[2024][1]), 2),
            "da_2025": round(float(vals[2025][1]), 2),
            "d_model": round(float(dmod), 2), "d_da": round(float(dda), 2),
        })
    # supply-state YoY deltas, annual + Sep-Dec
    print("\n  supply-state YoY deltas (2025 - 2024, MW mean):")
    print(f"    {'series':<12}{'meas Δ':>9}{'model Δ':>9}{'ΔΔ(mod-meas)':>13}")
    keys = ("gas", "hydro_net", "solar", "wind", "nuclear", "other", "interchange")
    out["yoy_annual"] = {}
    out["yoy_sepdec"] = {}
    for scope, name in ((None, "yoy_annual"), (SEPDEC, "yoy_sepdec")):
        if scope is not None:
            print(f"    -- Sep-Dec only --")
        for k in keys:
            dv = {}
            for year in (2024, 2025):
                f = frames[year]
                mask = f["ok"] if scope is None else f["ok"] & np.isin(f["mo"], scope)
                dv[year] = (float(np.nanmean(f["es"][k][mask])),
                            float(np.nanmean(f["ms"][k][mask])))
            dmeas = dv[2025][0] - dv[2024][0]
            dmod = dv[2025][1] - dv[2024][1]
            print(f"    {k:<12}{dmeas:>+9.0f}{dmod:>+9.0f}{dmod - dmeas:>+13.0f}")
            out[name][k] = {"measured": round(dmeas), "model": round(dmod),
                            "excess": round(dmod - dmeas)}
        # model-only storage detail
        for k in ("ps_net", "ps_chg", "battery_net", "battery_chg"):
            dv = {}
            for year in (2024, 2025):
                f = frames[year]
                mask = f["ok"] if scope is None else f["ok"] & np.isin(f["mo"], scope)
                dv[year] = float(np.nanmean(f["ms"][k][mask]))
            out[name][k] = {"model": round(dv[2025] - dv[2024])}
    return out


def section_e() -> dict:
    print("\n" + "=" * 78)
    print("§E — model binding-state witness in the 2025 DA-positive gap hours")
    print("=" * 78)
    out = {}
    for year in (2024, 2025):
        sc, lam, da, rt, w, ok, cda, _ = gap_frame(year)
        ca = [z for z in sc["price"].columns if not str(z).startswith("WECC")]
        pz = sc["price"][ca].to_numpy()
        disp = pz.max(axis=1) - pz.min(axis=1)
        pos = ok & (cda > 0)
        ms = model_state(year)
        flat = disp < 0.01
        print(f"\n[{year}] DA-positive hours n={pos.sum()}:")
        print(f"  CA zone-λ dispersion: p50 {np.percentile(disp[pos], 50):.2f} "
              f"p90 {np.percentile(disp[pos], 90):.2f}; "
              f"all-CA-flat (<$0.01) {int((pos & flat).sum())} h "
              f"({(pos & flat).sum() / pos.sum() * 100:.0f}%)")
        print(f"  storage in gap hours: PS pumping {int((pos & (ms['ps_chg'] > 1)).sum())} h, "
              f"battery charging {int((pos & (ms['battery_chg'] > 1)).sum())} h")
        gap_flat = float(cda[pos & flat].sum())
        print(f"  gap carried in all-CA-flat hours: {gap_flat:+.3f} "
              f"({gap_flat / cda[pos].sum() * 100:.0f}% of positive)")
        out[year] = {
            "n_pos": int(pos.sum()),
            "disp_p50": round(float(np.percentile(disp[pos], 50)), 3),
            "disp_p90": round(float(np.percentile(disp[pos], 90)), 3),
            "flat_hours": int((pos & flat).sum()),
            "flat_gap": round(gap_flat, 3),
            "ps_pumping_hours": int((pos & (ms["ps_chg"] > 1)).sum()),
            "battery_charging_hours": int((pos & (ms["battery_chg"] > 1)).sum()),
        }
    return out


def cems_gas_hourly(year: int) -> np.ndarray:
    """Measured hourly CAISO grid-gas series on the CEMS basis (gross MW).

    The raw EIA-930 ``NG: NG`` cell is CORRUPTED for CISO from ~2024-05
    (owner-signed FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12: a growing
    noon-peaked solar-shaped phantom block, +4.2/+7.9 TWh in 2024/25), so the
    measured gas witness here is built the way the bench anchor is: the CAMPD
    hourly unit series summed over the bench part's own CAISO gas-plant
    membership (``bench.plants``, ``nodata`` excluded). Gross-load basis — no
    parasitic scaling and no BTM removal — and the non-CEMS cogen block
    (bench ``gas_cogen_grid``, ~6.4 TWh/yr ≈ flat) is NOT in the series; both
    facts are stated wherever the series is compared to the model.
    """
    import gzip

    from market_sim.data.campd import load_campd_hourly, states_for_iso

    bench = json.loads(
        gzip.open(
            REPO / f"frontend/data/backcast/bench/CAISO/{year}.json.gz"
        ).read()
    )
    plants = bench["bench"]["plants"]
    gas_groups = {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS"}
    gas_ids = {
        int(str(pid).split(":")[0])  # bench keys may be "<plant>:<group>"
        for pid, p in plants.items()
        if p.get("group") in gas_groups and not p.get("nodata")
    }
    df = load_campd_hourly(states_for_iso(ISO), [year])
    df = df[df["plant_id"].isin(gas_ids) & (df["year"] == year)]
    out = np.zeros(HOURS)
    g = df.groupby("hour_of_year", observed=True)["gross_mw"].sum()
    out[np.asarray(g.index, dtype=int)] = g.to_numpy()
    return out


def section_c2() -> dict:
    print("\n" + "=" * 78)
    print("§C2 — the gas witness on the CEMS basis (the 930 NG cell is corrupt)")
    print("=" * 78)
    out = {}
    for year in (2024, 2025):
        sc, lam, da, rt, w, ok, cda, _ = gap_frame(year)
        mo = month_of_hour(year)
        hd = np.arange(HOURS) % 24
        ms = model_state(year)
        cems = cems_gas_hourly(year)
        cells = {
            "all_hours": ok,
            "da_pos_gap": ok & (cda > 0),
            "sepdec_belly": ok & np.isin(mo, SEPDEC) & np.isin(hd, BELLY),
            "sepdec_eve": ok & np.isin(mo, SEPDEC) & np.isin(hd, (17, 18, 19, 20, 21)),
            "spring_belly": ok & np.isin(mo, SPRING) & np.isin(hd, BELLY),
        }
        print(f"\n[{year}] model gas vs CEMS-basis measured gas (gross, no cogen "
              f"block):")
        print(f"    {'cell':<14}{'n':>6}{'model':>9}{'cems':>9}{'delta':>9}")
        out[year] = {"annual_twh": {"model": round(float(np.nansum(
            model_state(year)["gas"])) / 1e6, 3),
            "cems_gross": round(float(cems.sum()) / 1e6, 3)}}
        for name, mask in cells.items():
            mv = float(np.nanmean(ms["gas"][mask]))
            cv = float(np.nanmean(cems[mask]))
            print(f"    {name:<14}{int(mask.sum()):>6}{mv:>9.0f}{cv:>9.0f}"
                  f"{mv - cv:>+9.0f}")
            out[year][name] = {"model": round(mv), "cems_gross": round(cv),
                               "delta": round(mv - cv)}
    return out


def section_f() -> dict:
    print("\n" + "=" * 78)
    print("§F — fuel-passthrough coupling: the CC offer level vs λ, 2024→2025")
    print("=" * 78)
    out = {"monthly": []}
    frames = {}
    for year in (2024, 2025):
        sc, lam, da, rt, w, ok, cda, _ = gap_frame(year)
        rec = M202.fleet_recon(year)
        mc, cap, klass = rec["mc"], rec["cap"], rec["klass"]
        if mc.ndim == 1:
            mc = np.tile(mc[:, None], (1, HOURS))
        cc = klass == "gas_cc"
        if not cc.any():
            cc = np.char.startswith(klass.astype(str), "gas:cc")
        # capacity-weighted median CC offer among AVAILABLE capacity, per hour:
        # the level of the rung §B shows setting ~50 % of the DA-positive gap.
        cc_mc = np.full(HOURS, np.nan)
        mcc, ccap = mc[cc], cap[cc]
        for h in range(HOURS):
            c = ccap[:, h]
            m = c > 1.0
            if not m.any():
                continue
            order = np.argsort(mcc[m, h])
            cs = np.cumsum(c[m][order])
            cc_mc[h] = mcc[m, h][order][np.searchsorted(cs, cs[-1] / 2.0)]
        frames[year] = {"lam": lam, "da": da, "w": w, "ok": ok,
                        "mo": month_of_hour(year), "cc_mc": cc_mc}
    print(f"\n  {'mon':<4}{'ccmc24':>8}{'ccmc25':>8}{'Δccmc':>8}{'Δmod':>8}"
          f"{'Δda':>8}")
    for m in range(1, 13):
        row = {}
        for year in (2024, 2025):
            f = frames[year]
            mm = (f["mo"] == m) & f["ok"] & ~np.isnan(f["cc_mc"])
            row[year] = (
                np.average(f["cc_mc"][mm], weights=f["w"][mm]),
                np.average(f["lam"][mm], weights=f["w"][mm]),
                np.average(f["da"][mm], weights=f["w"][mm]),
            )
        dmc = row[2025][0] - row[2024][0]
        dmod = row[2025][1] - row[2024][1]
        dda = row[2025][2] - row[2024][2]
        print(f"  {m:<4}{row[2024][0]:>8.2f}{row[2025][0]:>8.2f}{dmc:>+8.2f}"
              f"{dmod:>+8.2f}{dda:>+8.2f}")
        out["monthly"].append({
            "month": m, "cc_mc_2024": round(float(row[2024][0]), 2),
            "cc_mc_2025": round(float(row[2025][0]), 2),
            "d_cc_mc": round(float(dmc), 2), "d_model": round(float(dmod), 2),
            "d_da": round(float(dda), 2),
        })
    # the coupling statistic: over Sep-Dec months, how much of each side's YoY
    # move does the CC offer move explain?
    sd = [r for r in out["monthly"] if r["month"] in SEPDEC]
    dmc = np.mean([r["d_cc_mc"] for r in sd])
    dmod = np.mean([r["d_model"] for r in sd])
    dda = np.mean([r["d_da"] for r in sd])
    print(f"\n  Sep-Dec means: Δcc_mc {dmc:+.2f}, Δmodel λ {dmod:+.2f} "
          f"(ratio {dmod / dmc:.2f}), Δ DA actual {dda:+.2f} "
          f"(ratio {dda / dmc:.2f})")
    out["sepdec"] = {"d_cc_mc": round(float(dmc), 2),
                     "d_model": round(float(dmod), 2),
                     "d_da": round(float(dda), 2),
                     "model_ratio": round(float(dmod / dmc), 2),
                     "da_ratio": round(float(dda / dmc), 2)}
    return out


def section_g() -> dict:
    """Monthly available-capacity YoY: is the model's autumn-2025 λ jump a
    supply-curve shift (outage overlay / fleet) rather than fuel?"""
    print("\n" + "=" * 78)
    print("§G — model available capacity by class, monthly, 2024 vs 2025")
    print("=" * 78)
    frames = {}
    for year in (2024, 2025):
        rec = M202.fleet_recon(year)
        cap, klass = rec["cap"], rec["klass"]
        mo = month_of_hour(year)
        by = {}
        for cls in ("gas_cc", "gas_ct", "gas_st", "import", "hydro"):
            rows = np.char.startswith(klass.astype(str), cls)
            if rows.any():
                by[cls] = np.asarray(cap[rows].sum(axis=0), dtype=float)
        frames[year] = {"mo": mo, "by": by,
                        "w": M202.rubric_weights(year)}
    out = {}
    for cls in frames[2024]["by"]:
        print(f"\n  {cls}: available MW, monthly mean (2024 / 2025 / Δ)")
        rows = []
        for m in range(1, 13):
            v = {y: float(np.mean(frames[y]["by"][cls][frames[y]["mo"] == m]))
                 for y in (2024, 2025)}
            rows.append({"month": m, "cap_2024": round(v[2024]),
                         "cap_2025": round(v[2025]),
                         "d": round(v[2025] - v[2024])})
            flag = " <--" if m in SEPDEC else ""
            print(f"    {m:<4}{v[2024]:>9.0f}{v[2025]:>9.0f}"
                  f"{v[2025] - v[2024]:>+9.0f}{flag}")
        out[cls] = rows
    # demand YoY for the same months
    print("\n  demand (rubric weights): monthly mean (2024 / 2025 / Δ)")
    out["demand"] = []
    for m in range(1, 13):
        v = {y: float(np.mean(frames[y]["w"][frames[y]["mo"] == m]))
             for y in (2024, 2025)}
        out["demand"].append({"month": m, "d": round(v[2025] - v[2024])})
        flag = " <--" if m in SEPDEC else ""
        print(f"    {m:<4}{v[2024]:>9.0f}{v[2025]:>9.0f}"
              f"{v[2025] - v[2024]:>+9.0f}{flag}")
    return out


def section_h() -> dict:
    """The below-the-gas-stack witness: share of hours (load-weighted) whose
    clearing price sits BELOW the cheapest available CC offer — model λ vs the
    DA actual, per month-group. This is the direct measurement of 'reality's
    margin left the gas stack; the model's did not'."""
    print("\n" + "=" * 78)
    print("§H — share of load-weighted hours priced BELOW the cheapest "
          "available CC offer")
    print("=" * 78)
    out = {}
    for year in (2024, 2025):
        sc, lam, da, rt, w, ok, cda, _ = gap_frame(year)
        mo = month_of_hour(year)
        rec = M202.fleet_recon(year)
        mc, cap, klass = rec["mc"], rec["cap"], rec["klass"]
        if mc.ndim == 1:
            mc = np.tile(mc[:, None], (1, HOURS))
        cc = klass == "gas_cc"
        mcc, ccap = mc[cc], cap[cc]
        cc_min = np.full(HOURS, np.nan)
        for h in range(HOURS):
            m = ccap[:, h] > 1.0
            if m.any():
                cc_min[h] = mcc[m, h].min()
        rows = {}
        print(f"\n[{year}]  {'scope':<10}{'model<ccmin':>13}{'DA<ccmin':>11}"
              f"{'cc_min lw':>11}")
        for name, months in (("annual", tuple(range(1, 13))),
                             ("sepdec", SEPDEC), ("spring", SPRING)):
            mm = ok & np.isin(mo, months) & ~np.isnan(cc_min)
            wsum = w[mm].sum()
            f_mod = float(w[mm & (lam < cc_min - 0.01)].sum() / wsum)
            f_da = float(w[mm & (da < cc_min - 0.01)].sum() / wsum)
            lwmin = float(np.average(cc_min[mm], weights=w[mm]))
            print(f"        {name:<10}{f_mod * 100:>12.1f}%{f_da * 100:>10.1f}%"
                  f"{lwmin:>11.2f}")
            rows[name] = {"model_below_pct": round(f_mod * 100, 1),
                          "da_below_pct": round(f_da * 100, 1),
                          "cc_min_lw": round(lwmin, 2)}
        out[year] = rows
    return out


def main() -> None:
    RESULT["A_da_map"] = section_a()
    RESULT["B_rungs"] = section_b()
    RESULT["C_supply_state"] = section_c()
    RESULT["C2_cems_gas"] = section_c2()
    RESULT["D_yoy"] = section_d()
    RESULT["E_binding"] = section_e()
    RESULT["F_fuel_coupling"] = section_f()
    RESULT["G_capacity"] = section_g()
    RESULT["H_below_stack"] = section_h()
    OUT.write_text(json.dumps(RESULT, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
