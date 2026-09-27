"""NYISO-NEXT-6 G-1 (ZERO LP): the LI posted-limit clip's footprint, production path.

Builds each year's NYISO topology under the keeper's own ScenarioConfig, applies
the armed PAR-attributed seam envelope, then ``nyiso_li_posted_limit_cap``, and
records hours cut / TWh removed on NYISO_external>Long_Island and the largest
move on any other link. Record: results/calibration/_nyisonext6_g1_footprint.json.
"""

import json
import dataclasses
import numpy as np
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.interchange import spec as sp
from market_sim.data.nyiso_par_attribution import nyiso_par_attributed_ttc_hourly
from market_sim.data.nyiso_seam_envelope import nyiso_li_posted_limit_cap

f = {x.name for x in dataclasses.fields(ScenarioConfig)}
out = {}
for y in (2021, 2022, 2023, 2024, 2025):
    b = "nyisonext3_2021" if y == 2021 else "nyisonext3_span"
    sc = json.load(open(f"results/calibration/{b}/run_config.json"))["scenario_config"]
    cfg = ScenarioConfig().with_overrides(
        **{k: v for k, v in sc.items() if k in f and k != "reliability_floor_overrides"}
    )
    ic = sp.apply_interchange_topology(
        get_iso_config("NYISO"), sp.get_interchange_spec(cfg, "NYISO", y), cfg, year=y
    )
    static = np.array([l.ttc_mw for l in ic.links], dtype=float)
    fwd, rev = nyiso_par_attributed_ttc_hourly(static, ic, y, 8760)
    arm = nyiso_li_posted_limit_cap(fwd, ic, y, 8760)
    i = [(l.from_zone, l.to_zone) for l in ic.links].index(
        ("NYISO_external", "Long_Island")
    )
    cut = fwd[:, i] - arm[:, i]
    other = np.delete(arm, i, axis=1) - np.delete(fwd, i, axis=1)
    out[y] = dict(
        hours_cut=int((cut > 0).sum()),
        cut_twh=round(float(cut.sum()) / 1e6, 3),
        mean_cut_mw=round(float(cut[cut > 0].mean()), 1),
        any_raise=bool((cut < 0).any()),
        other_links_max_abs_delta=float(np.abs(other).max()),
    )
    print(y, out[y])
json.dump(out, open("results/calibration/_nyisonext6_g1_footprint.json", "w"), indent=1)
