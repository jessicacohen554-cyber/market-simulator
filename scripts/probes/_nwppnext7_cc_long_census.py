"""NWPP-NEXT-7 zero-LP census: why C1 CC_REGULAR runs long in 2019 / 2020 / 2024 (/ 2025).

Reads only committed artifacts — no LP, no fleet build:
  - keeper #13's run payload  frontend/data/backcast/runs/<KEEPER>.js   (per-plant model TWh, zone x month)
  - the NWPP per-plant benchmark frontend/data/backcast/bench/NWPP/<Y>.json.gz (EIA-923 per plant)
  - keeper #13's scored C1 records (calibration_verdict.py --json, run in-process)
  - the NWPP-NEXT-5 coal contract census  results/calibration/_nwppnext5_coal_contract_census.json
  - EIA-923 generation-fuel, for PGE Beaver (8073), which has no CEMS and so no benchmark plant row

Writes results/calibration/_nwppnext7_cc_long_census.json. Record:
docs/handoffs/FINDING-nwppnext7-cc-long-is-coal-short-2026-09-26.md.
"""

from __future__ import annotations

import base64
import csv
import gzip
import json
import subprocess
import sys
from collections import defaultdict

from market_sim.config.paths import REPO_ROOT

KEEPER = "2026-09-26-nwppnext6-path76-ctrederive"
YEARS = list(range(2019, 2026))
ZONES = ["NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"]
COAL = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE")
BEAVER = 8073


def load_payload() -> dict:
    """Decode the keeper's gzip+base64 run payload."""
    s = (REPO_ROOT / "frontend/data/backcast/runs" / f"{KEEPER}.js").read_text()
    blob = s.split('="', 1)[1].rsplit('"', 1)[0]
    return json.loads(gzip.decompress(base64.b64decode(blob)))


def load_c1() -> dict[int, dict[str, tuple[float, float]]]:
    """Scored C1 (model, actual) TWh per year and class."""
    out = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/calibration_verdict.py"), "--run-id", KEEPER, "--json"],
        capture_output=True, text=True, check=False,  # exits 1 on a NOT-YET determination
    ).stdout
    recs = json.loads(out)["criteria"]["fuelmix"]["records"]
    c1: dict[int, dict[str, tuple[float, float]]] = defaultdict(dict)
    for r in recs:
        if r["model"] is not None and r["actual"] is not None:
            c1[r["year"]][r["key"]] = (r["model"], r["actual"])
    return c1


def main() -> None:
    """Run the census and write the JSON record."""
    pay = load_payload()
    c1 = load_c1()
    census = json.loads((REPO_ROOT / "results/calibration/_nwppnext5_coal_contract_census.json").read_text())["per_year"]
    beaver_act = defaultdict(float)
    with open(REPO_ROOT / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv") as f:
        for r in csv.DictReader(f):
            if int(r["plant_id"]) == BEAVER and r["prime_mover"] in ("CT", "CA"):
                beaver_act[int(r["year"])] += float(r["net_generation_mwh"]) / 1e6

    rec: dict = {"keeper": KEEPER, "years": {}}
    for y in YEARS:
        yp = pay["years"][str(y)]
        d = {k: m - a for k, (m, a) in c1[y].items()}
        coal_d = sum(d.get(k, 0.0) for k in COAL)
        nf = yp["nonfossilHr"]
        zm = yp["volErr"]["CC_REGULAR"]["zoneMon"]
        cc_zone = {z: sum(zm[z]["m"]) - sum(zm[z]["a"]) for z in ZONES if z in zm}
        bench = json.loads(gzip.open(REPO_ROOT / f"frontend/data/backcast/bench/NWPP/{y}.json.gz").read())["bench"]["plants"]
        plants = {}
        for k in set(bench) | set(yp["plants"]):
            bp, mp = bench.get(k, {}), yp["plants"].get(k, {})
            grp = bp.get("group") or (k.split(":")[1] if ":" in k else "")
            if grp in ("CC_REGULAR",) + COAL:
                plants[k] = {"name": bp.get("name", ""), "zone": bp.get("zone", ""), "group": grp,
                             "model_twh": mp.get("m_ann", 0.0), "eia923_twh": bp.get("e_ann") or 0.0}
        mp_all = yp["plants"]

        def model_coal(pc: str) -> float:
            return sum(p["m_ann"] for k, p in mp_all.items()
                       if k.split(":")[0] == pc and (":" not in k or "COAL" in k))

        bind = {}
        for est in ("A", "B"):
            bind[est] = sum(max(0.0, (p.get(f"burn_floor_{est}_twh") or 0.0) - model_coal(pc))
                            for pc, p in census[str(y)]["plants"].items())
        beaver_m = sum(p["m_ann"] for k, p in mp_all.items() if k == f"{BEAVER}:CC_REGULAR")
        rec["years"][str(y)] = {
            "c1_delta_twh": d,
            "cc_regular_delta": d["CC_REGULAR"],
            "coal_family_delta": coal_d,
            "hydro_delta": nf["hydro"]["mTwh"] - nf["hydro"]["aTwh"],
            "hydro_actual": nf["hydro"]["aTwh"],
            "fossil_total_delta": sum(d.values()),
            "cc_regular_delta_by_zone_volerr": cc_zone,
            "take_binding_vs_k13_twh": bind,
            "cc_if_take_displaces_cc_1to1": {e: d["CC_REGULAR"] - b for e, b in bind.items()},
            "beaver_8073_model_cc_twh": beaver_m,
            "beaver_8073_eia923_cc_twh": beaver_act.get(y),
            "plants": plants,
        }
    cc = [rec["years"][str(y)]["cc_regular_delta"] for y in YEARS]
    co = [rec["years"][str(y)]["coal_family_delta"] for y in YEARS]
    mc, mo = sum(cc) / len(cc), sum(co) / len(co)
    num = sum((a - mc) * (b - mo) for a, b in zip(cc, co))
    den = (sum((a - mc) ** 2 for a in cc) * sum((b - mo) ** 2 for b in co)) ** 0.5
    rec["r_ccdelta_vs_coaldelta"] = num / den
    out = REPO_ROOT / "results/calibration/_nwppnext7_cc_long_census.json"
    out.write_text(json.dumps(rec, indent=1))
    print(f"r(CC delta, coal delta) = {rec['r_ccdelta_vs_coaldelta']:.3f}")
    print("year  CCd   coald  hydrod  fossild | bind A  B | CC after A  B | Beaver m/a")
    for y in YEARS:
        r = rec["years"][str(y)]
        ba = r["beaver_8073_eia923_cc_twh"]
        print(f"{y} {r['cc_regular_delta']:+5.1f} {r['coal_family_delta']:+6.1f} {r['hydro_delta']:+6.1f} "
              f"{r['fossil_total_delta']:+6.1f} | {r['take_binding_vs_k13_twh']['A']:5.2f} "
              f"{r['take_binding_vs_k13_twh']['B']:5.2f} | {r['cc_if_take_displaces_cc_1to1']['A']:+5.1f} "
              f"{r['cc_if_take_displaces_cc_1to1']['B']:+5.1f} | {r['beaver_8073_model_cc_twh']:.2f}/"
              f"{'n/a' if ba is None else f'{ba:.2f}'}")


if __name__ == "__main__":
    main()
