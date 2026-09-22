"""nwpp-46 phase 0 (ZERO LP): where NWPP's OWN measured hydro envelope binds.

The lever this lane pre-registers. NWPP-45 ruled C4's amplitude defect IN on
the coal offer stack; NWPP-46's phase 0 falsified that on NWPP's own data and
re-routed it to hydro over-flexibility (see the PRECOMMIT). This probe sizes
the re-routed lever before any LP is spent.

``config.hydro_dispatch_envelope`` (caiso-72 STEP-2) caps the conventional
hydro fleet's hourly dispatch at the measured per-(month x hour-of-day)
percentile (``constants.HYDRO_ENVELOPE_PERCENTILE``) of the ISO's OWN EIA-930
``NG: WAT`` series. Nothing is transferred from CAISO (rule 25
``[R-ISO-SCOPE]``): the ceiling is built from NWPP's own meter, and the
percentile is the shared structural convention, not an ISO-fitted number.

Reported here, all from committed artifacts plus the ISO's own EIA-930 extract:
  (1) the envelope itself, per month x hour-of-day;
  (2) how many model hours breach it, and by how much energy;
  (3) the DIURNAL prediction -- what the keeper's own hydro profile becomes
      once clipped to the ceiling, in the peak-to-trough GW currency C4's
      amplitude is denominated in;
  (4) the residual duty that must move onto the thermal classes.

(3) and (4) are PREDICTIONS from a static clip, not solve results: the budget
row re-allocates the clipped energy and the LP re-prices, neither of which a
clip models. They bound the mechanism's direction and order of magnitude,
which is what a pre-registration needs. NO RESIDUAL IS READ (rules 1 / 13).

Run: ``PYTHONPATH=.:src python3 scripts/probes/_nwpp46_hydro_envelope_phase0.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_sim.config.constants import (  # noqa: E402
    HYDRO_ENVELOPE_PERCENTILE,
    HYDRO_MIN_FLOW_PERCENTILE,
)
from market_sim.data.fleet import _hour_to_month_index  # noqa: E402
from market_sim.data.eia930.envelopes import (  # noqa: E402
    measured_hydro_hourly_envelope,
    measured_hydro_min_flow_level,
)
from scripts.lib.bundle_io import require_bundle_input  # noqa: E402

BUNDLE = Path("results/calibration/nwpp44_takeorpay_reg")
YEARS = (2023, 2024, 2025)
HYDRO_CLASSES = ("hydro", "HYDRO")
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL")


def _diurnal(x: np.ndarray) -> np.ndarray:
    n = len(x) // 24 * 24
    return x[:n].reshape(-1, 24).mean(axis=0)


def main() -> None:
    print(f"HYDRO_ENVELOPE_PERCENTILE = {HYDRO_ENVELOPE_PERCENTILE}  "
          f"HYDRO_MIN_FLOW_PERCENTILE = {HYDRO_MIN_FLOW_PERCENTILE} (the mirror)")
    e930 = pd.read_parquet(require_bundle_input(BUNDLE, "eia930"))
    for year in YEARS:
        env = measured_hydro_hourly_envelope("NWPP", year, 8760)
        if env is None:
            print(f"\n{year}: NO ENVELOPE — the ISO has no usable NG:WAT extract.")
            continue
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        mdl = (
            ch[ch["klass"].isin(HYDRO_CLASSES)]
            .groupby("hour")["mw"].sum().sort_index().to_numpy(float)
        )
        act = (
            e930[(e930["year"] == year) & (e930["series"] == "hydro")]
            .sort_values("hour")["mw"].to_numpy(float)
        )
        n = min(len(env), len(mdl), len(act))
        env, mdl, act = env[:n], mdl[:n], act[:n]

        over = np.maximum(mdl - env, 0.0)
        breach = over > 0.0
        print(f"\n{'=' * 84}\nYEAR {year}\n{'=' * 84}")
        print(f"  envelope   mean {env.mean():>8,.0f}  p5 {np.percentile(env, 5):>8,.0f}"
              f"  p95 {np.percentile(env, 95):>8,.0f}  max {env.max():>8,.0f} MW")
        print(f"  model hydro mean {mdl.mean():>7,.0f}  min {mdl.min():>8,.0f}"
              f"  max {mdl.max():>8,.0f} MW   total {mdl.sum() / 1e6:>7.3f} TWh")
        print(f"  actual      mean {act.mean():>7,.0f}  min {act.min():>8,.0f}"
              f"  max {act.max():>8,.0f} MW   total {act.sum() / 1e6:>7.3f} TWh")
        print(f"\n  BREACH: {breach.sum():,} of {n:,} hours ({breach.mean():.1%}), "
              f"energy above the ceiling {over.sum() / 1e6:.3f} TWh "
              f"({over.sum() / mdl.sum():.2%} of model hydro); "
              f"max breach {over.max():,.0f} MW")

        # breach by hour of day — is the hoarding diurnal, as caiso-72 found?
        bh = np.zeros(24)
        oh = np.zeros(24)
        for h in range(24):
            sel = np.arange(h, n, 24)
            bh[h] = breach[sel].mean()
            oh[h] = over[sel].mean()
        top = np.argsort(-oh)[:6]
        print("  breach concentration (top 6 hours of day): "
              + ", ".join(f"h{h} {bh[h]:.0%}/{oh[h]:,.0f}MW" for h in sorted(top)))

        # --- the LOWER half of the same two-sided envelope ---
        lvl = measured_hydro_min_flow_level("NWPP", year)
        floor = None
        if lvl is not None:
            mi = _hour_to_month_index(8760)[:n]
            floor = np.asarray(lvl, dtype=float)[mi]
            under = np.maximum(floor - mdl, 0.0)
            ub = under > 0.0
            print(f"\n  MIN-FLOW Q95 level  mean {floor.mean():>7,.0f} MW "
                  f"(min {floor.min():,.0f} / max {floor.max():,.0f})")
            print(f"  UNDERRUN: {ub.sum():,} of {n:,} hours ({ub.mean():.1%}), "
                  f"energy below the sustained level {under.sum() / 1e6:.3f} TWh; "
                  f"max underrun {under.max():,.0f} MW")
            uh = np.array([under[np.arange(h, n, 24)].mean() for h in range(24)])
            topu = np.argsort(-uh)[:6]
            print("  underrun concentration (top 6 hours of day): "
                  + ", ".join(f"h{h} {uh[h]:,.0f}MW" for h in sorted(topu)))

        # (3) the diurnal prediction under the two-sided clip
        clipped = np.minimum(mdl, env)
        two = np.maximum(clipped, floor) if floor is not None else clipped
        dm, dc, da = _diurnal(mdl), _diurnal(clipped), _diurnal(act)
        dt = _diurnal(two)
        print("\n  MEAN DIURNAL PROFILE, peak-to-trough swing (GW):")
        print(f"    model      {(dm.max() - dm.min()) / 1000:>6.3f}  "
              f"(ratio {(dm.max() - dm.min()) / (da.max() - da.min()):.2f}x)")
        print(f"    ceiling    {(dc.max() - dc.min()) / 1000:>6.3f}  "
              f"(ratio {(dc.max() - dc.min()) / (da.max() - da.min()):.2f}x)")
        print(f"    TWO-SIDED  {(dt.max() - dt.min()) / 1000:>6.3f}  "
              f"(ratio {(dt.max() - dt.min()) / (da.max() - da.min()):.2f}x)")
        print(f"    actual     {(da.max() - da.min()) / 1000:>6.3f}")
        # (4) residual duty released to the thermal classes
        released = _diurnal(mdl - two)
        coal = (
            ch[ch["klass"].isin(COAL_CLASSES)]
            .groupby("hour")["mw"].sum().sort_index().to_numpy(float)[:n]
        )
        dcoal = _diurnal(coal)
        acoal = _diurnal(
            e930[(e930["year"] == year) & (e930["series"] == "coal")]
            .sort_values("hour")["mw"].to_numpy(float)[:n]
        )
        print(f"    released to thermal, evening h19 {released[19]:,.0f} MW, "
              f"trough h11 {released[11]:,.0f} MW, h19-h11 "
              f"{(released[19] - released[11]) / 1000:.3f} GW")
        print(f"    coal swing now {(dcoal.max() - dcoal.min()) / 1000:.3f} GW vs "
              f"actual {(acoal.max() - acoal.min()) / 1000:.3f} GW "
              f"(ratio {(dcoal.max() - dcoal.min()) / (acoal.max() - acoal.min()):.2f})")


if __name__ == "__main__":
    main()
