"""M1/M2 (starts vs CEMS, near-min-load online) per class/year via _ucmilp_benefit_screen.screen_year. Usage: screen_span.py <bundle> <out.json> [years]"""
import json, sys
from pathlib import Path
sys.path.insert(0, "/home/user/market-simulator/scripts/probes"); sys.path.insert(0, "/home/user/market-simulator/src"); sys.path.insert(0, "/home/user/market-simulator")
import _ucmilp_benefit_screen as s
b = Path("/home/user/market-simulator") / sys.argv[1]
years = [int(y) for y in sys.argv[3:]] or [2019, 2020, 2021, 2022, 2023, 2024, 2025]
cp = s.committed_pct("ERCOT"); out = {}
for y in years:
    r = s.screen_year("ERCOT", b, y, cp); out[str(y)] = r
    c = r["classes"]
    print(y, " | ".join(f"{g}: st {c[g]['m1_starts_model']}/{c[g]['m1_starts_cems']} ({c[g]['m1_starts_ratio']}) m2b {c[g]['m2b_twh']} TWh {c[g]['class_twh']}" for g in ("CC_REGULAR", "ST_GAS", "COAL_PRB", "COAL_LIGNITE") if g in c), flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1, default=s._js)
