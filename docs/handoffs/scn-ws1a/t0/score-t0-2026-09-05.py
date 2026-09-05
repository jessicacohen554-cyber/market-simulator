"""Score the SCN-WS1a CAISO T0 pair against the precommit (FINDING §0.4). Zero solves."""
import sys, json, glob, importlib.util
import numpy as np
sys.path.insert(0, "/home/user/market-simulator/src"); sys.path.insert(0, "/home/user/market-simulator")
REPO = "/home/user/market-simulator"
T0 = "/tmp/claude-0/-home-user-market-simulator/b4b6b0f8-d301-514a-ab7b-706ed88e44d3/scratchpad/t0"
spec = importlib.util.spec_from_file_location("cfi", f"{REPO}/scripts/check_forecast_invariants.py")
cfi = importlib.util.module_from_spec(spec); sys.modules["cfi"] = cfi; spec.loader.exec_module(cfi)
from pathlib import Path
runs = {}
for arm in ("base", "carbon_plus25"):
    d = glob.glob(f"{T0}/{arm}/CAISO/*/")
    assert len(d) == 1, d
    runs[arm] = (Path(d[0]), cfi.load_run(Path(d[0])), json.load(open(f"{T0}/{arm}/full_horizon_summary.json")))
out = {"arms": {}}
for arm, (d, run, summ) in runs.items():
    yd = run.years[2026]
    res, ctx = yd.result, yd.context
    uids = list(ctx.unit_ids)
    disp = np.asarray(res.dispatch)
    gen = disp.sum(axis=1)
    imports = {u: float(gen[i]) / 1e3 for i, u in enumerate(uids) if u.startswith("WECC_")}
    em = np.asarray(res.emissions).sum() / 1e6 if res.emissions is not None else None
    tr = [r for r in summ["trajectory"] if r["year"] == 2026][0]
    out["arms"][arm] = {"run_dir": str(d), "cache_key": summ.get("cache_key"), "wall_s": summ.get("total_wall_s"),
        "co2_mt": tr["co2_mt"], "lw_price": tr["lw_price"], "import_gwh": imports,
        }
from market_sim.policy.carbon import resolve_carbon_price
for arm, (d, run, summ) in runs.items():
    out["arms"][arm]["carbon"] = float(resolve_carbon_price(run.config, 2026))
b, h = out["arms"]["base"], out["arms"]["carbon_plus25"]
out["delta"] = {"carbon": h["carbon"] - b["carbon"], "co2_mt": h["co2_mt"] - b["co2_mt"], "lw_price": h["lw_price"] - b["lw_price"],
    "import_gwh": {u: h["import_gwh"][u] - b["import_gwh"].get(u, 0.0) for u in h["import_gwh"]}}
out["paired_checker"] = [(r.ident, r.name, r.status, r.detail, r.data) for r in cfi.run_paired(runs["base"][0], runs["carbon_plus25"][0], "carbon")]
json.dump(out, open(f"{T0}/score_t0.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
