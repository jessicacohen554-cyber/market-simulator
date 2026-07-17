"""Derive the CAISO DAYTIME (hod 6-21) trigger-OFF south-corridor clean depth — gate check.

The mechanism-depth companion for the daytime clean-import leg
(``ScenarioConfig.caiso_dsw_daytime_clean``, caiso-94), the daytime analogue of
``derive_caiso_overnight_clean_depth.py`` (the promoted caiso-93 overnight
depth). The pre-registered daytime no-wedge gate
(``derive_caiso_daytime_wedge.py``, FINDING-caiso94) PASSED: the measured
daytime trigger-OFF CAISO-PaloVerde spread carries NO carbon wedge, and the
autumn daytime cells clear at raw-hub parity with year-stable depths. Owner
authorized (2026-07-17, session-logged) an UNCONDITIONAL daytime trigger-OFF
diagnostic build — this script derives the single per-year depth that leg reads.

CRITICAL — the window here MUST match the injector
(``transmission.inject_caiso_dsw_daytime_clean``) hour-for-hour, else the
depth prices a different population than it caps:

    window[t] = (CAISO_DAYTIME_CLEAN_HOD_MIN <= hod(t) <= CAISO_DAYTIME_CLEAN_HOD_MAX)
                AND measured hub finite (the 2023 Jan-Feb OASIS gap never arms)
                AND NOT the caiso-87 surplus trigger
                    (PALOVRDE >= HR_CCGT x SoCal_citygate_weekly + $2.5)

  depth[y] = p95 of measured WECC_DSW corridor net import (EIA-930 CISO DIBAs,
             model clock) over ``window`` hours of year y.

Why trigger-OFF (NOT caiso-93's unconditional): daytime caiso-87 is
coverage-RICH (66-90 % trigger-ON in the belly), so an unconditional daytime
depth would double-count caiso-87's own trigger-ON hours. Scoping to trigger-OFF
keeps the daytime leg DISJOINT from caiso-87 (FINDING-caiso94 §1; the lens-4
build watch-item). The injector additionally nets the depth against the shaped
firm block + the caiso-87 surplus tranche + the caiso-93 overnight tranche
per hour, so no single hour double-carries clean depth.

Frozen (NOT iterated against the gates, the caiso-86b prohibition): the gate
thresholds (CV <= 0.20, LOYO <= 25 %, the caiso-81/86/87/88/93 standard), the
depth statistic (p95, the caiso-87/93 statistic), the corridor series (EIA-930
CISO DIBAs via ``corridor_net_import``), the trigger (the committed caiso-87
construction), and the hod window (6-21, the FINDING-caiso94 daytime band, set
before the depth was measured). A FAIL files a FINDING and the lane stops.

Usage: .venv/bin/python scripts/derive_caiso_daytime_clean_depth.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from derive_caiso_import_tranches import (  # noqa: E402
    YEARS,
    corridor_net_import,
    hub_prices,
)
from market_sim.config.interchange_config import (  # noqa: E402
    CAISO_DSW_SURPLUS_REMOTE_VOM,
)
from market_sim.data.fuel import socal_citygate_weekly_hourly  # noqa: E402

HOURS = 8760
HR_CCGT = 0.37 / 0.0531  # ~6.97, the committed caiso-87 coupling
HOD_MIN = 6  # daytime window lower hod (FINDING-caiso94 band)
HOD_MAX = 21  # daytime window upper hod (inclusive)
CV_MAX = 0.20
LOYO_MAX = 0.25


def main() -> None:
    """Derive per-year daytime trigger-OFF depths; exit 0 PASS / 2 FAIL."""
    net = corridor_net_import()
    hub = hub_prices()
    hod = np.arange(HOURS) % 24
    daytime_hod = (hod >= HOD_MIN) & (hod <= HOD_MAX)

    depths: dict[int, float] = {}
    print(
        f"=== CAISO daytime (hod {HOD_MIN}-{HOD_MAX}) trigger-OFF WECC_DSW clean depth ==="
    )
    print(
        f"    window: daytime hod AND measured-hub AND NOT surplus "
        f"(PV >= {HR_CCGT:.2f} x SoCal_citygate + {CAISO_DSW_SURPLUS_REMOTE_VOM})"
    )
    for yr in YEARS:
        pv = hub.loc[yr]["PALOVRDE"].to_numpy()
        flow = net.loc[yr]["WECC_DSW"].to_numpy()
        gas = np.asarray(socal_citygate_weekly_hourly(yr, HOURS))
        floor = HR_CCGT * gas + CAISO_DSW_SURPLUS_REMOTE_VOM
        measured = np.isfinite(pv)
        surplus = measured & np.isfinite(floor) & (pv < floor)
        window = daytime_hod & measured & ~surplus
        m = window & np.isfinite(flow)
        depths[yr] = float(np.percentile(flow[m], 95))
        print(
            f"  {yr}: n={int(m.sum())} daytime-OFF hours (of {int((daytime_hod & measured).sum())} "
            f"measured daytime) -> mean {flow[m].mean():,.0f} / p50 "
            f"{np.percentile(flow[m], 50):,.0f} / p95 {depths[yr]:,.0f} MW"
        )

    vals = np.array([depths[y] for y in YEARS])
    cv = float(vals.std() / vals.mean())
    g_cv = cv <= CV_MAX
    print(
        f"\n  daytime-OFF depths (p95 MW): {' / '.join(f'{depths[y]:,.0f}' for y in YEARS)}"
    )
    print(f"  pooled mean (static entry): {vals.mean():,.0f} MW")
    print(
        f"  year-stability CV = {cv:.3f} (gate <= {CV_MAX}): {'PASS' if g_cv else 'FAIL'}"
    )

    g_loyo = True
    for held in YEARS:
        pred = float(np.mean([depths[y] for y in YEARS if y != held]))
        err = abs(pred - depths[held]) / depths[held]
        ok = err <= LOYO_MAX
        g_loyo = g_loyo and ok
        print(
            f"  LOYO held-out {held}: mean-of-others {pred:,.0f} vs "
            f"{depths[held]:,.0f} -> {err:.1%} (gate <= {LOYO_MAX:.0%}): "
            f"{'PASS' if ok else 'FAIL'}"
        )

    passed = g_cv and g_loyo
    print(
        f"\n  OVERALL: "
        f"{'PASS — depth admissible; build/solve authorized (owner 2026-07-17)' if passed else 'FAIL — file FINDING, do NOT build'}"
    )
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
