"""FFR-4A: compact (K, L) map + ratchet-frequency summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from market_sim.config.capacity_market import (  # noqa: E402
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
)
from market_sim.config.entry_config import (  # noqa: E402
    ENTRY_COD_LAG_DEFAULT_YEARS,
    ENTRY_COD_LAG_YEARS,
    ENTRY_GROWTH_LIMIT_MULTIPLE as K,
)

SCRATCH = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "cfc8cad9-a015-5137-a698-21ea3a926be0/scratchpad"
)
data = json.loads((SCRATCH / "build_record.json").read_text())

ENTRY_TECHS = ("wind", "solar", "gas_cc", "gas_ct")

for vintage, blob in data.items():
    lo, hi = blob["window"]
    print(f"\n{'='*100}\n{vintage}  (COD window {lo}-{hi})   K = {K}\n{'='*100}")
    print(
        f"{'ISO':7} {'tech':7} {'L':>2} {'seed GW':>8} {'ladder':>8} {'static':>7} "
        f"{'ISO tot':>8} {'binds':>14} {'K-L+1':>6} {'newmax/yrs':>11} {'max r':>7}"
    )
    tot = {"on": 0, "above": 0, "below": 0}
    for iso, techs in blob["isos"].items():
        for tech in ENTRY_TECHS:
            st = techs.get(tech)
            L = ENTRY_COD_LAG_YEARS.get(tech, ENTRY_COD_LAG_DEFAULT_YEARS)
            static = QUEUE_CAP_PER_TECH_GW[iso].get(tech, 0.0)
            iso_tot = QUEUE_CAP_GW.get(iso, 0.0)
            if st is None:
                print(
                    f"{iso:7} {tech:7} {L:>2} {'--':>8} {'no ladder':>8} "
                    f"{static:>7.1f} {iso_tot:>8.1f} {'static only':>14}"
                )
                continue
            seed = st["seed_gw"]
            ladder = K * seed
            binder = min(ladder, static if static > 0 else ladder, iso_tot)
            which = (
                "growth_ladder"
                if abs(binder - ladder) < 1e-9
                else ("per_tech_cap" if abs(binder - static) < 1e-9 else "iso_budget")
            )
            edge = "ON" if K == L else ("ABOVE" if K > L else "BELOW")
            tot["on" if edge == "ON" else ("above" if edge == "ABOVE" else "below")] += 1
            print(
                f"{iso:7} {tech:7} {L:>2} {seed:>8.3f} {ladder:>8.3f} {static:>7.1f} "
                f"{iso_tot:>8.1f} {which:>14} {K - L + 1:>6.1f} "
                f"{st['n_new_max']:>4}/{st['n_eligible_years']:<6} "
                f"{st['max_ratio'] if st['max_ratio'] is not None else 0:>7.2f}"
            )
    print(f"\n  knife-edge census: ON={tot['on']}  ABOVE={tot['above']}  BELOW={tot['below']}")

# Pooled ratchet statistics across all ISO x entry-tech cells
print(f"\n{'='*100}\nPOOLED MEASURED RATCHET STATISTICS (identifying data)\n{'='*100}")
for vintage, blob in data.items():
    all_r: list[float] = []
    nmax = nyrs = 0
    over_k: list[tuple[str, str, float]] = []
    for iso, techs in blob["isos"].items():
        for tech in ENTRY_TECHS:
            st = techs.get(tech)
            if not st:
                continue
            all_r.extend(st["ratios"])
            nmax += st["n_new_max"]
            nyrs += st["n_eligible_years"]
            for r in st["ratios"]:
                if r > K:
                    over_k.append((iso, tech, r))
    all_r.sort()
    n = len(all_r)
    print(
        f"{vintage}: {nyrs} ISO-tech-years, NEW MAXIMUM in {nmax} "
        f"({100*nmax/nyrs:.1f} %); ratio p50={all_r[n//2]:.3f} "
        f"p75={all_r[int(0.75*n)]:.3f} p90={all_r[int(0.90*n)]:.3f} "
        f"p95={all_r[int(0.95*n)]:.3f} max={all_r[-1]:.3f}; "
        f"exceed K=2.0 in {len(over_k)} ({100*len(over_k)/n:.1f} %)"
    )
