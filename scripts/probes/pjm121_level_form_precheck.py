"""pjm-121 no-LP pre-check: what does LEVEL-form CC_LIKE actually do to the bids?

The pjm-120 finding requires a DISPERSION mechanism — one that makes the model
CHEAPER when the system is slack and DEARER when it is tight. Before spending a
solve, this measures the proposed mechanism's bid delta directly, by calling the
real builder (``build_pjm_offer_midcurve_conditional_markup``) on the real fleet
and offer arrays under three scopes:

  A. keeper           — segments ("LONG_RUN",), all floor form
  B. floor  +CC_LIKE  — segments ("LONG_RUN","CC_LIKE"), all floor form  [= pjm-108]
  C. level  +CC_LIKE  — same segments, CC_LIKE in LEVEL form            [= the candidate]

and reports, for the CC_REGULAR econ rows the mechanism targets:

  * where those rows sit on their plant's within-unit capacity-share ladder
    (the mechanism's own ``share_g``) — this decides which part of the measured
    ladder they read;
  * the MW-weighted bid delta vs the keeper, split by net-load bin and by
    direction (cheaper / dearer);
  * the resulting dispersion of the CC econ offer stack (p10/p50/p90 spread),
    which is the quantity the residual is a compression of.

Pure diagnostic, no LP (rule 16). Falsification: if C only ever LOWERS bids, it
is a level lever and cannot close a dispersion gap — the candidate dies here.

Usage:
    python scripts/probes/pjm121_level_form_precheck.py \
        results/calibration/pjm119_overlay_restore --year 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
# REPO itself must be on the path so ``scripts.lib.clean_io`` resolves as a
# package — without it the data/clean readers silently fall back and the
# measured overlays (east interface cut, ramp capability) refuse to load.
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))


def _scoped(config, segments, level):
    """Return the config with the mid-curve floor/level scopes overridden."""
    return config.with_overrides(
        pjm_offer_midcurve_conditional=True,
        pjm_offer_midcurve_segments=list(segments),
        pjm_offer_midcurve_level_segments=list(level),
    )


def main() -> int:
    """Build the three markups on one fleet and print the comparison."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, default=2025)
    args = ap.parse_args()

    from derive_pjm_ordc_overlay import _run_year_kwargs
    from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup
    from run_calibration import run_year

    meta = json.loads((args.bundle / "meta.json").read_text())
    year, hours = args.year, int(meta["hours"])
    state = run_year(
        year, meta["iso"], hours, meta["gas_prices"][str(year)], **_run_year_kwargs(meta)
    )
    fa = state["fleet_arrays"]
    gens = state["fleet"]
    mc = np.asarray(state["mc_base"], dtype=float)
    cfg = state["config"]
    # Same LP-served net-load convention as the builder's call site
    # (run_calibration.py::run_year) so the hour->bin mapping is identical.
    net_load = (
        state["demand"].sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )

    scopes = {
        "A_keeper_floor_LONGRUN": (("LONG_RUN",), ()),
        "B_floor_plus_CCLIKE": (("LONG_RUN", "CC_LIKE"), ()),
        "C_level_CCLIKE": (("LONG_RUN", "CC_LIKE"), ("CC_LIKE",)),
    }
    marks = {}
    for name, (seg, lvl) in scopes.items():
        m = build_pjm_offer_midcurve_conditional_markup(
            fa, gens, mc, net_load, _scoped(cfg, seg, lvl), year
        )
        marks[name] = np.zeros_like(mc) if m is None else m

    # CC_REGULAR econ rows — the rows the CC_LIKE scope targets.
    cc_econ = np.array(
        [
            (getattr(g, "plant_group", None) == "CC_REGULAR")
            and g.unit_id.rpartition("_")[2].startswith("econ")
            for g in gens
        ]
    )
    print(f"\nCC_REGULAR econ rows targeted: {int(cc_econ.sum())} of {len(gens)} gens")
    cap = fa.pmax[cc_econ]
    print(f"their capacity: {cap.sum() / 1e3:.2f} GW")

    base = marks["A_keeper_floor_LONGRUN"]
    for name in ("B_floor_plus_CCLIKE", "C_level_CCLIKE"):
        d = marks[name][cc_econ] - base[cc_econ]  # (n_cc, T) bid delta vs keeper
        w = cap[:, None] / cap.sum()
        up = d > 0.01
        dn = d < -0.01
        print(f"\n=== {name}  (delta vs keeper, CC_REGULAR econ rows) ===")
        print(
            f"  MW-weighted mean bid delta: {float((d * w).sum() / d.shape[1]):+.3f} $/MWh"
        )
        print(
            f"  row-hours DEARER {up.mean() * 100:5.1f}%  (mean +{d[up].mean() if up.any() else 0:.2f})"
            f"   CHEAPER {dn.mean() * 100:5.1f}%  (mean {d[dn].mean() if dn.any() else 0:.2f})"
        )
        # by net-load bin (the mechanism's own conditioning driver)
        q = np.quantile(net_load[: d.shape[1]], [0.80, 0.90, 0.97])
        hb = np.searchsorted(q, net_load[: d.shape[1]], side="right")
        for b in range(4):
            sel = hb == b
            if not sel.any():
                continue
            dd = d[:, sel]
            print(
                f"    net-load bin{b} ({int(sel.sum()):5d} h): "
                f"mean {float((dd * cap[:, None] / cap.sum()).sum() / sel.sum()):+7.3f} $/MWh"
            )

    # Offer-stack dispersion of the CC econ band (p90-p10 across rows), by bin.
    print("\n=== CC econ offer-stack spread (p90-p10 across rows, $/MWh) ===")
    q = np.quantile(net_load[: mc.shape[1]], [0.80, 0.90, 0.97])
    hb = np.searchsorted(q, net_load[: mc.shape[1]], side="right")
    print(f"    {'scope':<26}{'bin0':>9}{'bin1':>9}{'bin2':>9}{'bin3':>9}")
    for name in scopes:
        bid = mc[cc_econ] + marks[name][cc_econ]
        row = []
        for b in range(4):
            sel = hb == b
            if not sel.any():
                row.append(float("nan"))
                continue
            v = bid[:, sel]
            row.append(float(np.quantile(v, 0.9) - np.quantile(v, 0.1)))
        print(f"    {name:<26}" + "".join(f"{x:>9.2f}" for x in row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
