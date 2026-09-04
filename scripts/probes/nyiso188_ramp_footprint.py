"""nyiso-188 Object 1a: ramp-envelope footprint of the Astoria routing.

(i) reproduce the COMMITTED artifact with the two Astoria remap entries stripped
    (the committed invocation: derive_campd_ramp_envelopes.py --iso NYISO, default
    years 2023 2024 2025) -> byte-compare;
(ii) derive at HEAD (remap armed) -> row diff;
(iii) list which NYISO fleet (plant, bucket) groups resolve to the (0, CC)/(0, ST)
    class-fraction fallback under build_ramp_groups' resolution rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "results" / "calibration" / "_nyiso188_ramp_footprint"
OUT.mkdir(parents=True, exist_ok=True)

from market_sim.data import campd  # noqa: E402
import derive_campd_ramp_envelopes as d  # noqa: E402

COMMITTED = REPO / "data/raw/_processed-legacy/campd_ramp_envelopes_NYISO.csv"
committed = pd.read_csv(COMMITTED)

# (i) committed reproduction: strip the Astoria entries (they were added at
# nyiso-187 AFTER the committed artifact was derived; nyiso-187 restored it).
astoria = {k: v for k, v in campd.CAMPD_UNIT_PLANT_REMAP.items() if k[0] == 55375}
for k in astoria:
    del d.CAMPD_UNIT_PLANT_REMAP[k]
pre = d.derive_envelopes("NYISO", [2023, 2024, 2025])
pre.to_csv(OUT / "ramp_pre_remap.csv", index=False)
same = (OUT / "ramp_pre_remap.csv").read_bytes() == COMMITTED.read_bytes()
print("committed reproduced byte-identical with remap stripped:", same)
if not same:
    m = committed.merge(
        pre,
        on=["plant_code", "bucket"],
        how="outer",
        suffixes=("_c", "_p"),
        indicator=True,
    )
    print(m[m._merge != "both"].to_string())
    for c in ["pmax_obs_mw", "n_online_hours", "ramp_up_mw", "ramp_dn_mw"]:
        dd = m[(m._merge == "both") & (m[f"{c}_c"] != m[f"{c}_p"])]
        if len(dd):
            print(c, dd[["plant_code", "bucket", f"{c}_c", f"{c}_p"]].to_string())

# (ii) HEAD derive with the remap armed
for k, v in astoria.items():
    d.CAMPD_UNIT_PLANT_REMAP[k] = v
post = d.derive_envelopes("NYISO", [2023, 2024, 2025])
post.to_csv(OUT / "ramp_post_remap.csv", index=False)
m = committed.merge(
    post,
    on=["plant_code", "bucket"],
    how="outer",
    suffixes=("_c", "_a"),
    indicator=True,
)
print("\nrows only in committed / only in arm:")
print(m[m._merge != "both"][["plant_code", "bucket", "_merge"]].to_string())
moved = []
for c in ["pmax_obs_mw", "n_online_hours", "ramp_up_mw", "ramp_dn_mw", "basis"]:
    dd = m[
        (m._merge == "both")
        & ~((m[f"{c}_c"] == m[f"{c}_a"]) | (m[f"{c}_c"].isna() & m[f"{c}_a"].isna()))
    ]
    for r in dd.itertuples():
        moved.append(
            (r.plant_code, r.bucket, c, getattr(r, f"{c}_c"), getattr(r, f"{c}_a"))
        )
print("\ncells that moved (plant, bucket, col, committed, arm):")
for t in moved:
    print(" ", t)

# (iii) fallback readers: the fleet's (plant, bucket) groups without a "plant" row.
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.fleet.campd_bins import _RAMP_BUCKET_BY_GROUP  # noqa: E402

fleet = load_fleet_from_csv("NYISO", get_iso_config("NYISO"))
groups: dict[tuple[int, str], float] = {}
names: dict[int, str] = {}
for g in fleet:
    pc = int(g.plant_code or 0)
    b = _RAMP_BUCKET_BY_GROUP.get(str(getattr(g, "plant_group", "")), "")
    if pc > 0 and b:
        groups[(pc, b)] = groups.get((pc, b), 0.0) + float(g.pmax_mw)
        names[pc] = getattr(g, "plant_name", "") or getattr(g, "name", "")
measured_c = {
    (int(r.plant_code), r.bucket)
    for r in committed[committed.basis == "plant"].itertuples()
}
measured_a = {
    (int(r.plant_code), r.bucket) for r in post[post.basis == "plant"].itertuples()
}
rows = []
for (pc, b), cap in sorted(groups.items()):
    rows.append(
        {
            "plant_code": pc,
            "name": names[pc],
            "bucket": b,
            "group_pmax_mw": round(cap, 1),
            "measured_row_committed": (pc, b) in measured_c,
            "measured_row_arm": (pc, b) in measured_a,
            "reads_class_fallback": b in ("CC", "ST") and (pc, b) not in measured_a,
        }
    )
fb = pd.DataFrame(rows)
fb.to_csv(OUT / "ramp_fallback_readers.csv", index=False)
fr = fb[fb.reads_class_fallback]
print("\nfleet groups reading the class-fraction fallback (arm basis):")
print(fr.to_string(index=False))
cf_c = committed[committed.basis == "class_fraction"].set_index("bucket")
cf_a = post[post.basis == "class_fraction"].set_index("bucket")
print("\nclass-fraction rows committed vs arm:")
print(
    pd.concat(
        [
            cf_c[["n_online_hours", "ramp_up_mw", "ramp_dn_mw"]],
            cf_a[["n_online_hours", "ramp_up_mw", "ramp_dn_mw"]],
        ],
        axis=1,
        keys=["committed", "arm"],
    ).to_string()
)
# magnitude of the fallback drift on the readers, in MW
for b in ("CC", "ST"):
    sub = fr[fr.bucket == b]
    if len(sub) == 0:
        continue
    cap = sub.group_pmax_mw.sum()
    print(
        f"\n{b} fallback readers: {len(sub)} groups, {cap:.1f} MW; up-envelope frac {cf_c.loc[b, 'ramp_up_mw']}->{cf_a.loc[b, 'ramp_up_mw']} "
        f"(= {cap * cf_c.loc[b, 'ramp_up_mw']:.1f} -> {cap * cf_a.loc[b, 'ramp_up_mw']:.1f} MW summed), dn {cf_c.loc[b, 'ramp_dn_mw']}->{cf_a.loc[b, 'ramp_dn_mw']} "
        f"(= {cap * cf_c.loc[b, 'ramp_dn_mw']:.1f} -> {cap * cf_a.loc[b, 'ramp_dn_mw']:.1f} MW)"
    )
# the pool itself: per-plant fractions, to show where the median moves
pool = post[post.basis == "plant"].copy()
pool["up_frac"] = pool.ramp_up_mw / pool.pmax_obs_mw
pool["dn_frac"] = pool.ramp_dn_mw / pool.pmax_obs_mw
pool.to_csv(OUT / "ramp_pool_fracs_arm.csv", index=False)
for b in ("CC",):
    s = pool[pool.bucket == b].sort_values("up_frac")
    print(f"\n{b} pool (arm) up_frac sorted:")
    print(
        s[["plant_code", "pmax_obs_mw", "up_frac", "dn_frac"]]
        .round(4)
        .to_string(index=False)
    )
