"""MISO SRMC-ladder + reliability-floor diagnostic (fleet_only, no LP).

Q1: are neutral-1.0 committed bands consistent with a >=1.0x SRMC floor?
Q2: do the de-leaked gas classes carry the physical part-load premium
    (committed min-load priced ABOVE the full-load econ body) or a FLAT curve?
Q3: CT_PEAKER reliability-floor diurnal shape (C7 off-window signature)?

No dashboard registration (rule 15 diagnostic).
"""

import sys
import numpy as np
import collections

sys.path.insert(0, "scripts")
sys.path.insert(0, "src")

from run_calibration import run_year  # noqa: E402

YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
GAS = {2023: 2.54, 2024: 2.19, 2025: 3.52}[YEAR]

out = run_year(
    YEAR,
    "MISO",
    8760,
    GAS,
    ttc_overrides={},
    coal_prb_passthrough=1.0,
    outage_source="historic",
    coal_prb_passthrough_sigmoid=True,
    coal_mustrun_per_plant=True,
    coal_drop_pof=True,
    coal_prb_passthrough_tiered=True,
    coal_bit_sigmoid=True,
    cc_intermediate_split=True,
    ct_intermediate_split=True,
    st_gas_intermediate=True,
    fleet_only=True,
)
fa = out["fleet_arrays"]
config = out["config"]
hr = np.asarray(fa.heat_rate, float)
vom = np.asarray(fa.vom, float)
er = np.asarray(fa.emission_rate, float)
pmax = np.asarray(fa.pmax, float)
uids = fa.unit_ids
pg = fa.plant_group
carbon = config.carbon_price or 0.0
srmc = hr * GAS + vom + er * carbon


def band_of(uid):
    u = uid.lower()
    if u.endswith("_mustrun"):
        return "mustrun"
    if u.endswith("_committed"):
        return "committed"
    if u.endswith("_econlo"):
        return "econ_low"
    if u.endswith("_econhi"):
        return "econ_high"
    if u.endswith("_peak"):
        return "peak"
    if "_econc" in u:
        return "econ_body"  # coal smoothed sub-tranches
    return "other"


def plant_of(uid):
    parts = uid.split("_")
    for p in parts:
        if p.startswith("p") and p[1:].isdigit():
            return p
    return None


def class_of(i):
    return str(pg[i]) if pg is not None and pg[i] else "?"


band_order = {
    "mustrun": 0,
    "committed": 1,
    "econ_low": 2,
    "econ_body": 3,
    "econ_high": 4,
    "peak": 5,
    "other": 6,
}

# ---- per-representative-plant tranche ladder (largest plant per gas class) ----
print(
    f"# MISO {YEAR} gas=${GAS} carbon=${carbon}  (offer curve = current post-deleak default)"
)
print("\n## Representative-plant tranche ladders (eff_HR = band-scaled heat rate)\n")
GAS_CLASSES = ["CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS"]
for cls in GAS_CLASSES:
    # find plant with the most tranches in this class
    plants = collections.defaultdict(list)
    for i, u in enumerate(uids):
        if class_of(i) == cls:
            p = plant_of(u)
            if p:
                plants[p].append(i)
    if not plants:
        continue
    # pick a plant that has a committed tranche + econ tranches
    best = max(plants.items(), key=lambda kv: len(kv[1]))
    p, idxs = best
    idxs = sorted(idxs, key=lambda i: band_order.get(band_of(uids[i]), 9))
    base_ref = None
    # reference = the econ_low (or econ_body) eff_HR to normalise the shape
    for i in idxs:
        if band_of(uids[i]) in ("econ_low", "econ_body"):
            base_ref = hr[i]
            break
    print(f"### {cls}  plant {p}")
    print("band | cap_MW | eff_HR | SRMC$/MWh | HR/econ_low")
    for i in idxs:
        rr = hr[i] / base_ref if base_ref else float("nan")
        print(
            f"{band_of(uids[i])} | {pmax[i]:.0f} | {hr[i]:.2f} | {srmc[i]:.1f} | {rr:.3f}"
        )
    print()

# ---- CT_PEAKER reliability floor diurnal shape (C7 signature) ----
mg = fa.min_gen
print("## CT_PEAKER reliability-floor diurnal profile")
if mg is None:
    print("min_gen is None (no floors on this fleet build)")
else:
    mg = np.asarray(mg, float)  # (n_gen, T)
    ct_mask = np.array([class_of(i) == "CT_PEAKER" for i in range(len(uids))])
    ct_floor = mg[ct_mask].sum(axis=0)  # (T,) total CT floor MW per hour
    hod = np.arange(len(ct_floor)) % 24
    prof = np.array([ct_floor[hod == h].mean() for h in range(24)])
    tot = ct_floor.sum()
    onwin = ct_floor[(hod >= 15) & (hod <= 21)].sum()
    print(f"total CT_PEAKER floored MWh (annual): {tot:,.0f}")
    print(
        f"share inside justified window h15-21: {onwin / tot:.1%}"
        if tot
        else "no floor"
    )
    print("hour_of_day mean floored MW:")
    print(" ".join(f"{h:02d}:{prof[h]:.0f}" for h in range(24)))
    # peak-window vs overnight
    overnight = prof[[0, 1, 2, 3, 4, 5]].mean()
    evening = prof[[16, 17, 18, 19, 20]].mean()
    print(
        f"overnight(0-5) mean {overnight:.0f} MW  vs  evening(16-20) mean {evening:.0f} MW"
    )
