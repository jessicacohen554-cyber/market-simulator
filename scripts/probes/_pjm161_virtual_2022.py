"""pjm-161 Phase-0: extend the pjm-158 virtual-layer attribution chain to 2022.

pjm-158 measured, IN-SAMPLE, that the DA virtual layer's rule-13 admissibility
anchor (net ≈ 0 cleared at actual DA prices) is unreachable in this LP because
the model's dual is gated as real-time, and it warned that the keeper's
near-cancellation is "a coincidence of two large opposing errors". This probe
asks the question that warning implies and that no in-sample year can answer:

    **is the layer's cleared net STABLE across price regimes, or does it flip?**

Same probe code, same helper functions, same reference series as
``_pjm158_virtual_basis.py`` / ``_pjm158_virtual_gain.py``; the only change is
the year set and the bundle each year's committed duals are read from.

RULE 22 POSTURE. This is a NO-LP READ of ALREADY-COMMITTED artifacts — the
2026-08-05-pjm-2022-touchpoint bundle, which was solved and registered under an
owner-authorized lift and is on the dashboard. Nothing is solved, scored or
registered here: no determination is produced, no bundle is written, no
registry entry is touched. It is the same posture pjm-157 and pjm-158 §1 took
when they read 2022 rows out of the committed bench.

Run:  uv run python scripts/probes/_pjm161_virtual_2022.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _pjm158_virtual_gain as G  # noqa: E402
from _pjm158_virtual_basis import canonical_prices  # noqa: E402

TWH = 1e6

#: year -> the committed bundle whose P1 duals that year was solved into.
BUNDLE_OF = {
    2022: "results/calibration/pjm2022_touchpoint",
    2023: "results/calibration/pjm152_collapse_A",
    2024: "results/calibration/pjm152_collapse_A",
    2025: "results/calibration/pjm152_collapse_A",
}
YEARS = (2022, 2023, 2024, 2025)


def _with_bundle(year: int, fn, *a, **k):
    """Call a pjm-158 helper against the bundle that owns ``year``."""
    prev = G.BUNDLE
    G.BUNDLE = BUNDLE_OF[year]
    try:
        return fn(*a, **k)
    finally:
        G.BUNDLE = prev


def main() -> None:
    pd.set_option("display.width", 190)
    years = tuple(int(a) for a in sys.argv[1:]) or YEARS
    rows = []
    for year in years:
        bids = G.load_curve(year)
        hours = G.build_hour_arrays(bids)

        da = G.actual_da_price(year)  # RTO hub-mean DA, the rule-13 reference
        canon = canonical_prices(year)  # the committed system DA/RT series
        rt_canon = canon["rt:CANON"]
        da_canon = canon["da:CANON"]

        price_z, share_z, sys_dual = _with_bundle(year, G.model_zonal, year)

        def net_at(lam: np.ndarray) -> np.ndarray:
            return G.eval_net_fast(hours, lam)

        anchor_da = float(net_at(da).sum()) / TWH
        anchor_da_c = float(net_at(da_canon).sum()) / TWH
        anchor_rt_c = float(net_at(rt_canon).sum()) / TWH
        at_model_level = float(net_at(sys_dual).sum()) / TWH
        at_model_zonal = float(G.zonal_sum(net_at, price_z, share_z).sum()) / TWH

        inc, dec = _with_bundle(year, G.model_cleared, year)
        observed = -(inc + dec)  # + = net virtual DEMAND (pjm-158 convention)

        gmean = float(np.mean(G.gain(hours, da, 1.0)))

        rows.append(
            dict(
                year=year,
                anchor_DA_hubmean=anchor_da,
                anchor_DA_canon=anchor_da_c,
                anchor_RT_canon=anchor_rt_c,
                DA_minus_RT_basis=anchor_rt_c - anchor_da_c,
                at_model_syslevel=at_model_level,
                at_model_zonal=at_model_zonal,
                OBSERVED=observed,
                unexplained=observed - at_model_zonal,
                dev_from_DA_anchor=observed - anchor_da_c,
                gain_MW_per_dollar=gmean,
                mean_DA=float(np.mean(da_canon)),
                mean_RT=float(np.mean(rt_canon)),
                mean_model_dual=float(np.mean(sys_dual)),
            )
        )

    df = pd.DataFrame(rows).set_index("year")
    print("=" * 92)
    print("pjm-161 — the DA virtual layer's cleared net, 2022 alongside 2023-2025")
    print("  TWh; sign convention  + = net virtual DEMAND (phantom load)")
    print("=" * 92)
    print(df.T.round(3).to_string())

    print()
    print("READING")
    o = df["OBSERVED"]
    if 2022 in o.index:
        print(f"  observed cleared net, 2022 = {o.loc[2022]:+.3f} TWh")
        ins = o.loc[[y for y in o.index if y >= 2023]]
        if len(ins):
            print(f"  in-sample range            = {ins.min():+.3f} .. {ins.max():+.3f}")
        if 2023 in o.index:
            print(f"  2022 minus 2023            = {o.loc[2022] - o.loc[2023]:+.3f} TWh swing")
        print("  C1 CC_REGULAR 2022 miss    = +18.276 TWh")
        print(
            "  pjm-158 §5.2 measured that ~80% of a virtual-volume change lands on "
            "physical\n  generation, predominantly CC_REGULAR:"
            f" {0.80 * o.loc[2022]:+.2f} TWh of the 2022 miss."
        )

    dest = REPO / "results" / "calibration" / "_pjm161_virtual_2022.json"
    dest.write_text(
        json.dumps(json.loads(df.reset_index().to_json(orient="records")), indent=1)
        + "\n"
    )
    print(f"\nwrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
