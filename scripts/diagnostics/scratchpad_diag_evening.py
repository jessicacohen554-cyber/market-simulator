"""Evening CT-vs-CC merit-order diagnosis for CAISO (caiso-52 recipe).

Loads the model P1 dispatch + flows for a diagnostic bundle, the CAMPD bench
actuals, and reconstructs the class SRMC ladder for the evening ramp so the
three candidate root causes can be quantified from data:

  A. CC committed/peak bands too cheap -> CC covers the evening ramp on merit.
  B. import corridors mispriced/at-cap in the evening -> imports don't fill.
  C. CT offers priced above the evening LMP -> CTs never clear on merit.

Run AFTER the bundle's dispatch/<year>_P1.parquet exists.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from legitimacy_diagnostics import load_bench  # noqa: E402

REPO = Path(".").resolve()
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
BUNDLE = (
    Path(sys.argv[2])
    if len(sys.argv) > 2
    else Path("results/calibration/caiso_diag_evening_2024")
)
EVE = list(range(15, 22))  # evening ramp local hours 15..21 (t % 24)


def hod_profile(mw_8760, hours_col=None):
    a = np.asarray(mw_8760, dtype=float)[:8760]
    hod = np.arange(len(a)) % 24
    return np.array([a[hod == h].mean() for h in range(24)])


# ---- model dispatch (P1 — the main no-commitment clearing run) ----
label = "P1"
disp = pd.read_parquet(BUNDLE / "dispatch" / f"{YEAR}_P1.parquet")
print(f"# model dispatch pass={label} rows={len(disp):,}")
# per-class hourly total MW
mclass = (
    disp.groupby(["klass", "hour"], observed=True)["mw"]
    .sum()
    .unstack("klass", fill_value=0.0)
)  # index hour, cols class
model_class_hourly = {
    k: mclass[k].reindex(range(8760), fill_value=0.0).to_numpy() for k in mclass.columns
}

# zonal LMP hourly (use the generator-carried lmp; take per-zone mean)
lmp = disp.groupby(["zone", "hour"], observed=True)["lmp"].mean().unstack("zone")
zones = [z for z in lmp.columns if z in ("NP15", "SP15", "ZP26")]
print("# zones with LMP:", zones)

# ---- actual per-class from CAMPD bench ----
bench = load_bench(REPO, "CAISO", YEAR)
actual_class_hourly = {}
for pid, b in bench.items():
    k = b["group"]
    actual_class_hourly.setdefault(k, np.zeros(8760))
    actual_class_hourly[k] += np.asarray(b["mw"], dtype=float)[:8760]

FOCUS = ["CT_PEAKER", "CC_REGULAR", "CC_CHP", "ST_GAS", "CT_CHP"]
print("\n## Annual TWh (model P1 vs CAMPD actual)")
for k in FOCUS:
    m = model_class_hourly.get(k, np.zeros(8760)).sum() / 1e6
    a = actual_class_hourly.get(k, np.zeros(8760)).sum() / 1e6
    print(f"  {k:12s} model {m:6.2f}  actual {a:6.2f}  delta {m - a:+6.2f}")

print("\n## Hour-of-day mean MW (model | actual), evening hours 15-21 bold")
for k in FOCUS:
    mp = hod_profile(model_class_hourly.get(k, np.zeros(8760)))
    ap = hod_profile(actual_class_hourly.get(k, np.zeros(8760)))
    print(f"\n  {k}")
    print("   h :  " + " ".join(f"{h:5d}" for h in range(24)))
    print(
        "   M :  "
        + " ".join(
            (f"[{v:4.0f}]" if h in EVE else f"{v:5.0f}") for h, v in enumerate(mp)
        )
    )
    print(
        "   A :  "
        + " ".join(
            (f"[{v:4.0f}]" if h in EVE else f"{v:5.0f}") for h, v in enumerate(ap)
        )
    )

# ---- evening-hour deficit/surplus ----
print("\n## Evening (h15-21) mean MW model vs actual")
for k in FOCUS:
    mp = hod_profile(model_class_hourly.get(k, np.zeros(8760)))[EVE].mean()
    ap = hod_profile(actual_class_hourly.get(k, np.zeros(8760)))[EVE].mean()
    print(f"  {k:12s} model {mp:6.0f}  actual {ap:6.0f}  delta {mp - ap:+6.0f}")

# ---- LMP evening profile ----
print("\n## Evening LMP by zone (hod mean)")
for z in zones:
    p = hod_profile(lmp[z].reindex(range(8760)).to_numpy())
    print(f"  {z}: " + " ".join(f"h{h}={p[h]:.0f}" for h in EVE))

# ---- import corridor flows ----
fpath = BUNDLE / "flows.parquet"
if fpath.exists():
    flows = pd.read_parquet(fpath)
    if "pass" in flows.columns:
        flows = flows[flows["pass"] == "P1"]
    print("\n## Import corridor flows (flows.parquet) — link mean MW by hod, evening")
    # links from/to per corridor; positive = from->to
    for (fz, tz), g in flows.groupby(["from_zone", "to_zone"], observed=True):
        if "WECC" in str(fz) or "WECC" in str(tz):
            arr = (
                g.set_index("hour")["mw"]
                .reindex(range(8760), fill_value=0.0)
                .to_numpy()
            )
            p = hod_profile(arr)
            print(
                f"  {fz}->{tz}: evening "
                + " ".join(f"h{h}={p[h]:.0f}" for h in EVE)
                + f"  | ann {arr.sum() / 1e6:.2f} TWh"
            )
else:
    print("\n(no flows.parquet)")

# ---- import tranche dispatch from dispatch frame (units in WECC corridors) ----
imp = disp[disp["zone"].astype(str).str.startswith("WECC")]
if len(imp):
    print("\n## Import-tranche units (WECC corridors): annual TWh + evening mean MW")
    for uid, g in imp.groupby("unit_id", observed=True):
        arr = g.set_index("hour")["mw"].reindex(range(8760), fill_value=0.0).to_numpy()
        p = hod_profile(arr)
        print(
            f"  {uid:28s} ann {arr.sum() / 1e6:6.2f} TWh  eve {p[EVE].mean():6.0f} MW  midday(h12) {p[12]:6.0f}"
        )
