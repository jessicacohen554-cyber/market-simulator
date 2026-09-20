"""nyiso-246 phase 0 (b) — decompose the model's conditional response (ZERO LP).

The nyiso-246 anchor guard (g1) tests whether the model's conditional offer
response sits at or above the measured book's. This probe says WHICH TERM
carries it, by isolating the armed ``gas_offer_net_revenue_margin``
contribution on the affected stack.

That mechanism holds a gas tranche's net-revenue markup **fuel-invariant** at a
frozen per-zone anchor, so its contribution to a row's marginal cost is::

    markup_hr x (anchor - fuel)          $/MWh

which is **negative exactly when delivered gas exceeds the anchor** -- i.e. in
the winter gas-scarcity hours the mechanism's own conditioning selects. This
probe measures that contribution's distribution over the affected tranches, in
the frozen TIGHT and ORDINARY windows, capacity-weighted.

DIAGNOSTIC ONLY. ``G0`` already stopped the nyiso-246 mechanism (PRECOMMIT
section 3); nothing here revives it, and no geometry variant is tried. What it
produces is the evidence a successor needs, sized rather than asserted.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso246_margin_sign_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
YEARS = (2022, 2023, 2024, 2025)


def main() -> None:
    from scripts.data.derive_nyiso_offer_level_dispersion import state_windows
    from scripts.probes.nyiso246_dispersion_phase0 import affected, weighted_quantiles

    tight, ordinary, _ = state_windows()
    out: dict = {"session": "nyiso-246", "term": "markup_hr x (anchor - fuel)", "years": {}}
    pick = (0.05, 0.25, 0.50, 0.75, 0.95)

    for year in YEARS:
        z = np.load(CACHE / f"{year}.npz", allow_pickle=False)
        gas = np.load(CACHE / f"gas_{year}.npy").astype(float)
        aff = affected(z["unit_ids"], z["plant_group"])
        pmax = z["pmax"].astype(float)
        markup = z["gen_markup_hr"].astype(float)
        anchor = z["gen_margin_anchor"].astype(float)

        tagged = aff[markup[aff] > 0.0]
        rec: dict = {
            "affected_tranches": int(aff.size),
            "tagged_markup_gt0": int(tagged.size),
            "tagged_pmax_mw": round(float(pmax[tagged].sum()), 1),
            "tagged_share_of_affected_mw": round(
                float(pmax[tagged].sum() / max(1e-9, pmax[aff].sum())), 4
            ),
            "anchor_usd_per_mmbtu_distinct": sorted(
                {round(float(x), 4) for x in anchor[tagged]}
            )[:6],
        }
        for label, mask in (("tight", tight[year]), ("ordinary", ordinary[year])):
            if not mask.any() or not tagged.size:
                continue
            # (n_tagged, n_hours) contribution, $/MWh.
            contrib = markup[tagged][:, None] * (
                anchor[tagged][:, None] - gas[mask][None, :]
            )
            w = np.repeat(pmax[tagged][:, None], int(mask.sum()), axis=1).ravel()
            v = contrib.ravel()
            q = weighted_quantiles(v, w, np.array(pick))
            rec[label] = {
                "mean_gas_usd_per_mmbtu": round(float(gas[mask].mean()), 4),
                "cap_weighted_mean_usd_per_mwh": round(
                    float((v * w).sum() / w.sum()), 3
                ),
                "share_of_row_hours_negative": round(float((v < 0).mean()), 4),
                **{f"p{int(p * 100)}": round(float(x), 3) for p, x in zip(pick, q)},
            }
        out["years"][str(year)] = rec

    dest = REPO / "results" / "calibration" / "_nyiso246_margin_sign_phase0.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out["years"], indent=1))
    print("wrote", dest)


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
