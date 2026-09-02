"""capx D42 plant-grain grading probe (committed artifacts only, no solve).

Reads a T1-H bundle's evolution ledgers + the committed MISO scoring target
and reports what the rubric scorer does not: model exits BY CHANNEL and fuel,
plant-grain precision (model exit MW at plants that really exited ÷ model
exit MW), the per-plant false-positive list at full magnitude, timing of the
matched plants, and — when the bundle carries the D42 ``announced_fossil_
schedule`` — the deferral-class census with the rolling-vintage KNOWABILITY
grade (was the re-filing on file before the vintage date's effective year?).

Usage::

    uv run python scripts/probes/_capxd42_plant_grain.py \\
        results/hindcast/miso-2021-2025-realized-t1h-d42-dates [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

THERMAL = {"coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear", "biomass"}
SCORED = (2023, 2024, 2025)


def plant_of(unit_id: str) -> int | None:
    m = re.search(r"_p(\d+)_", unit_id)
    if m:
        return int(m.group(1))
    m = re.match(r"^(\d+)_", unit_id)
    return int(m.group(1)) if m else None


def effective_year(year: int, month: int | None) -> int:
    return year + 1 if (month is not None and month > 6) else year


def load_bundle(bundle: Path) -> tuple[dict, dict[int, dict]]:
    meta = json.loads((bundle / "meta.json").read_text())
    cache = Path(meta["bundle"])
    if not cache.exists():
        cache = bundle / meta["iso"] / meta["cache_key"]
    ledgers = {}
    for p in sorted(cache.glob("evolution_*.json")):
        y = int(p.stem.split("_")[1])
        ledgers[y] = json.loads(p.read_text())
    return meta, ledgers


def model_exits(ledgers: dict[int, dict]) -> pd.DataFrame:
    rows = []
    for y, led in ledgers.items():
        for r in led.get("retirements", []):
            rows.append((r["unit_id"], r["fuel"], float(r["mw"]), y, r.get("reason", "economic")))
        for key, reason in (("confirmed_derates", "confirmed"), ("announced_derates", "announced")):
            for r in led.get(key, []) or []:
                rows.append((r["unit_id"], r["fuel"], float(r["derate_mw"]), y, reason))
    df = pd.DataFrame(rows, columns=["unit_id", "fuel", "mw", "year", "reason"])
    df["plant"] = df["unit_id"].map(plant_of)
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument(
        "--scored-only",
        action="store_true",
        help="restrict to the 2023-2025 scored years (default: the cumulative 2021-2025 window the rubric scorer grades)",
    )
    args = ap.parse_args()
    meta, ledgers = load_bundle(args.bundle)
    iso = meta["iso"]
    act = pd.read_csv(ROOT / "data/raw/_validation-source" / f"capacity_actuals_{iso.lower()}.csv", comment="#")
    act = act[(act["kind"] == "retirement") & act["fuel"].isin(THERMAL)].copy()
    act["plant"] = act["plant_id"].astype(int)
    mod = model_exits(ledgers)
    if args.scored_only:
        mod = mod[mod["year"].isin(SCORED)]
        act_s = act[act["year"].isin(SCORED)]
    else:
        act_s = act
    out: dict = {"bundle": str(args.bundle), "cache_key": meta["cache_key"], "years": sorted(mod["year"].unique().tolist())}

    # 1. by channel x fuel (GW)
    piv = mod.pivot_table(index="fuel", columns="reason", values="mw", aggfunc="sum", fill_value=0.0) / 1000.0
    piv["model_total"] = piv.sum(axis=1)
    piv["actual"] = act_s.groupby("fuel")["mw"].sum() / 1000.0
    piv = piv.fillna(0.0).round(3)
    out["by_fuel_channel_gw"] = piv.to_dict(orient="index")
    print("\n== model exits by fuel x channel (GW, window) ==")
    print(piv.to_string())

    # 2. plant-grain precision per fuel + false-positive list
    real_plants = act.groupby(["plant", "fuel"])["mw"].sum()  # any window year
    real_plant_any = set(act["plant"])
    prec = {}
    fps = []
    for fuel, g in mod.groupby("fuel"):
        total = g["mw"].sum()
        hit = g[[ (p, fuel) in real_plants.index for p in g["plant"]]]["mw"].sum()
        prec[fuel] = {"model_mw": round(total, 1), "at_real_exit_plants_mw": round(hit, 1), "precision": round(hit / total, 3) if total else None}
        for p, gg in g[[ (p, fuel) not in real_plants.index for p in g["plant"]]].groupby("plant"):
            fps.append({"plant": int(p), "fuel": fuel, "model_mw": round(gg["mw"].sum(), 1), "years": sorted(gg["year"].unique().tolist()), "reasons": sorted(gg["reason"].unique().tolist()), "plant_exited_other_fuel": bool(p in real_plant_any)})
    fps.sort(key=lambda r: -r["model_mw"])
    tot = mod["mw"].sum(); hit_all = sum(v["at_real_exit_plants_mw"] for v in prec.values())
    prec["ALL"] = {"model_mw": round(tot, 1), "at_real_exit_plants_mw": round(hit_all, 1), "precision": round(hit_all / tot, 3) if tot else None}
    out["plant_grain_precision"] = prec
    out["false_positive_plants"] = fps
    print("\n== plant-grain precision ==")
    for k, v in prec.items():
        print(f"  {k:8s} model {v['model_mw']:9.1f} MW  at-real-exit-plants {v['at_real_exit_plants_mw']:9.1f}  precision {v['precision']}")
    print(f"\n== false-positive plants (model exit MW at plants with no real exit of that fuel): {len(fps)} plants, {sum(r['model_mw'] for r in fps):.1f} MW ==")
    for r in fps[:25]:
        print(f"  {r['plant']:6d} {r['fuel']:6s} {r['model_mw']:8.1f} MW  years {r['years']} {r['reasons']}")

    # 3. real cohort coverage at plant grain (real exit MW at plants the model exited, by fuel)
    cov = {}
    mod_plants = mod.groupby(["plant", "fuel"])["mw"].sum()
    for fuel, g in act_s.groupby("fuel"):
        real = g["mw"].sum()
        got = g[[ (p, fuel) in mod_plants.index for p in g["plant"]]]["mw"].sum()
        cov[fuel] = {"real_mw": round(real, 1), "at_model_exit_plants_mw": round(got, 1), "coverage": round(got / real, 3) if real else None}
    out["plant_grain_coverage"] = cov
    print("\n== real-cohort coverage at plant grain (window) ==")
    for k, v in cov.items():
        print(f"  {k:8s} real {v['real_mw']:9.1f}  at-model-exit-plants {v['at_model_exit_plants_mw']:9.1f}  coverage {v['coverage']}")

    # 4. large units (>=300 MW) — per-unit hit at plant+fuel grain, with timing
    big = act[(act["mw"] >= 300.0)].copy()
    hits = []
    for r in big.itertuples(index=False):
        m = mod[(mod["plant"] == r.plant) & (mod["fuel"] == r.fuel)]
        hits.append({"unit_id": r.unit_id, "plant": int(r.plant), "fuel": r.fuel, "real_mw": float(r.mw), "real_year": int(r.year), "model_mw_at_plant": round(float(m["mw"].sum()), 1), "model_years": sorted(m["year"].unique().tolist()), "reasons": sorted(m["reason"].unique().tolist()), "hit": bool(len(m))})
    out["large_units"] = hits
    print(f"\n== large (>=300 MW) real exits: {sum(h['hit'] for h in hits)}/{len(hits)} plants reached (plant+fuel grain, any window-year model exit) ==")
    for h in hits:
        print(f"  {'HIT ' if h['hit'] else 'MISS'} {h['unit_id']:10s} {h['fuel']:6s} real {h['real_mw']:7.1f} @{h['real_year']}  model {h['model_mw_at_plant']:7.1f} @{h['model_years']} {h['reasons']}")

    # 5. D42 schedule / deferral-class knowability
    sched = None
    for y in sorted(ledgers):
        if ledgers[y].get("announced_fossil_schedule"):
            sched = ledgers[y]["announced_fossil_schedule"]
            break
    if sched:
        rows = []
        for s in sched:
            eff_v = effective_year(s["vintage_exit_year"], s["vintage_exit_month"])
            eff = (
                None
                if s["disposition"] in ("cancelled", "reversed") or not s["exit_year"]
                else effective_year(s["exit_year"], s["exit_month"])
            )
            fcv = s.get("first_change_vintage")
            knowable = (fcv is not None and fcv + 1 <= eff_v)
            rows.append({**s, "effective_vintage": eff_v, "effective_verified": eff, "knowable_before_vintage_effective_year": knowable if s["disposition"] in ("deferred", "cancelled") else None})
        df = pd.DataFrame(rows)
        out["schedule_dispositions"] = df["disposition"].value_counts().to_dict()
        cls = df[(df["effective_vintage"] <= 2025) & df["disposition"].isin(["deferred", "cancelled", "reversed"])].copy()
        cls = cls[(cls["effective_verified"].isna()) | (cls["effective_verified"] > 2025)]
        out["deferral_class"] = cls.sort_values("mw", ascending=False).to_dict(orient="records")
        print(f"\n== deferral class (vintage-effective <=2025, verified out of window or withdrawn): {len(cls)} rows, {cls['mw'].sum():.1f} MW; knowable-in-time {cls['knowable_before_vintage_effective_year'].sum()} rows / {cls[cls['knowable_before_vintage_effective_year']==True]['mw'].sum():.1f} MW ==")
        for r in cls.sort_values("mw", ascending=False).itertuples(index=False):
            print(f"  {r.plant_id:6d} {str(r.plant_name)[:22]:22s} {r.generator_id:4s} {r.fuel:6s} {r.mw:7.1f}  {r.vintage_exit_year}/{r.vintage_exit_month} (eff {r.effective_vintage}) -> {r.disposition} {r.exit_year if r.disposition!='cancelled' else ''}  first-change v{r.first_change_vintage}  knowable={r.knowable_before_vintage_effective_year}")
    if args.json:
        args.json.write_text(json.dumps(out, indent=2, default=str))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
