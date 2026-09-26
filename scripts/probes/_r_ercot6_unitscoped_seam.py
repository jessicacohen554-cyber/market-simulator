"""R-ERCOT-6 Step 1 comparer: keeper (A) vs the unit-scoped seam variants (zero LP).

Reads the stage caches _r_ercot5_availability_census.py writes (keeper recipe,
bundle r_ercot5_hourgrain_span) for the keeper (A) and for each variant:
B = --set ercot_dam_availability_event_cap_unit_scoped=true as coded;
Bh = B with the shared-unit mask at the window factor's hour grain
(--variant hgmask); C = finer-grain-wins (--variant finer); D = the R-ERCOT-7
per-unit composition (--set ercot_dam_availability_event_cap_per_unit=true).
Per year and class it reports the capability lift (TWh), split into the part up
to the plant's own same-hour CEMS net output and the part above it; the
below-CEMS gap before/after; the lift in hours the tranche's mean mc_base is
below the keeper's P1 load-weighted price (econ_lift, an upper bound on the
energy the lift can add); and the mean MW lift over the keeper's P1 >$1k-or-slack
hours and over its top-100 load-weighted-price hours.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_r_ercot6_unitscoped_seam.py <cache-dir>

Record: docs/handoffs/FINDING-r-ercot-6-double-count-retest-2026-09-26.md.
"""

import sys

sys.path[:0] = [".", "src", "scripts"]
import numpy as np
import pandas as pd
import json
import scripts.probes._r_ercot5_availability_census as P

S = sys.argv[1] if len(sys.argv) > 1 else "."
B = "results/calibration/r_ercot5_hourgrain_span/hourly"
tags = {
    "B": "_ercot_dam_availability_event_cap_unit_scoped",
    "Bh": "_ercot_dam_availability_event_cap_unit_scoped_hgmask",
    "C": "_ercot_dam_availability_event_cap_unit_scoped_finer",
    # R-ERCOT-7: the per-unit composition (--set ercot_dam_availability_event_cap_per_unit=true)
    "D": "_ercot_dam_availability_event_cap_per_unit",
    # R-ERCOT-7 sensitivity: residual-preserving per-unit (--variant resid)
    "D2": "_ercot_dam_availability_event_cap_per_unit_resid",
}
out = {}
rows = []
for y in range(2019, 2026):
    A = np.load(f"{S}/r_ercot5_stages_{y}.npz", allow_pickle=True)
    H = A["fin"].shape[1]
    s = pd.read_parquet(f"{B}/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    pz = s.pivot(index="hour", columns="zone", values="price")
    dz = s.pivot(index="hour", columns="zone", values="demand")
    sl = s.groupby("hour").slack.sum()
    lw = ((pz * dz).sum(1) / dz.sum(1)).to_numpy()[:H]
    scar = np.where((pz.max(1).to_numpy()[:H] > 1000) | (sl.to_numpy()[:H] > 0))[0]
    top = np.argsort(-lw)[:100]
    fullgrp = A["all_grp"][
        np.isin(np.array([P._fam(g) for g in A["all_grp"]]), P.CLASSES)
    ]
    keys = sorted({(int(c), str(g)) for c, g in zip(A["codes"], A["grp"])})
    net = P.measured_net(y, H, keys)
    for v, t in tags.items():
        try:
            V = np.load(f"{S}/r_ercot5_stages_{y}{t}.npz", allow_pickle=True)
        except FileNotFoundError:
            continue
        assert (V["codes"] == A["codes"]).all()
        dmw = A["pmax"][:, None] * (V["fin"] - A["fin"])
        inmerit = A["mc"][:, None] < lw[None, :]
        for cls in P.CLASSES:
            sel = A["grp"] == cls
            lift = dmw[sel].sum() / 1e6
            econ = (dmw[sel] * inmerit[sel]).sum() / 1e6
            le = gA = gB = 0.0
            for c, g in keys:
                if g != cls or (c, g) not in net:
                    continue
                m = (A["codes"] == c) & (A["grp"] == g)
                meas = net[(c, g)][:H]
                fa = (A["pmax"][m, None] * A["fin"][m]).sum(0)
                fb = (A["pmax"][m, None] * V["fin"][m]).sum(0)
                li = fb - fa
                le += np.minimum(np.maximum(li, 0), np.maximum(meas - fa, 0)).sum()
                gA += np.maximum(meas - fa, 0).sum()
                gB += np.maximum(meas - fb, 0).sum()
            sub = {}
            if cls == "COAL":
                for sg in sorted(set(fullgrp[sel])):
                    ss = sel & (fullgrp == sg)
                    sub[sg] = round(dmw[ss].sum() / 1e6, 3)
            r = dict(
                variant=v,
                year=y,
                cls=cls,
                lift=lift,
                lift_le_cems=le / 1e6,
                lift_above=lift - le / 1e6,
                gap_A=gA / 1e6,
                gap_B=gB / 1e6,
                econ_lift=econ,
                scar_MW=float(dmw[sel][:, scar].sum(0).mean()) if len(scar) else np.nan,
                n_scar=len(scar),
                top100_MW=float(dmw[sel][:, top].sum(0).mean()),
                sub=json.dumps(sub) if sub else "",
            )
            rows.append(r)
df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
for v in tags:
    d = df[df.variant == v]
    if d.empty:
        continue
    print(
        f"\n##### variant {v}  (TWh, MW means over P1 >$1k-or-slack hours / top-100 LW-price hours)"
    )
    print(d.drop(columns=["variant"]).round(3).to_string(index=False))
df.to_csv(f"{S}/seam_compare.csv", index=False)
