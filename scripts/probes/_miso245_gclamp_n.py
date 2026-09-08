"""miso-245 G-CLAMP-N — the instrument leg declared in
``results/calibration/ADDENDUM-miso245-the-test-passed-with-low-power-and-one-more-leg-can-still-kill-it-2026-09-08.md``
§0c, pushed before its numbers exist.  ZERO LP, read-only, repairs nothing.

THE QUESTION.  ``m_j`` is only a statement about the SAMPLE if the estimator's
value at the reaching perturbation is the QUANTILE.  If it were the same-seam
no-wash clamp instead, ``m_j`` would be measuring a mechanism miso-244 already
REFUTED as the cause, and the ``A-CONFIRMED`` verdict would be an artifact.

THE RULE (addendum §0c, fixed before this ran).  For each mismatching entry j,
at its own reaching perturbation and at delta in {-1, 0, +1}, the estimator's
value must be the UNCLAMPED quantile:  v_raw,j(delta) <= lim_seam, with lim the
same-seam no-wash limit computed on the UNPERTURBED import list.

    FAIL at ANY entry  ->  that entry's m_j is VOID, A-CONFIRMED is WITHDRAWN,
                           and the failure is published FIRST at full magnitude.

It CANNOT rescue anything: passing changes no number and adds no evidence -- it
only removes a way the verdict could be false.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/_miso245_gclamp_n.json"

# Coordinates and reaching perturbations, restated as LITERALS from
# _miso245_ladder_drift_attribution_phase0.json so this leg adjudicates even if
# that artifact is missing.
ENTRIES = [
    {
        "year": 2023,
        "seam": "PJM",
        "side": "import",
        "band": 5,
        "count": 5415,
        "committed": 27.86,
        "signed_delta": +1,
    },
    {
        "year": 2023,
        "seam": "South",
        "side": "export",
        "band": 4,
        "count": 3259,
        "committed": 27.69,
        "signed_delta": -1,
    },
    {
        "year": 2024,
        "seam": "South",
        "side": "export",
        "band": 5,
        "count": 3044,
        "committed": 23.77,
        "signed_delta": +1,
    },
]


def _load_derive_module():
    script = REPO / "scripts/data/derive_miso_seam_ladders.py"
    spec = importlib.util.spec_from_file_location("_miso245_gc_derive", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _q_linear(xs_sorted: np.ndarray, q: float) -> float:
    n = xs_sorted.size
    h = float(q) * (n - 1)
    lo = int(min(max(np.floor(h), 0), n - 1))
    hi = min(lo + 1, n - 1)
    return float(xs_sorted[lo] + (h - lo) * (xs_sorted[hi] - xs_sorted[lo]))


def main() -> None:
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_MANITOBA_SEAM_SPEC,
    )
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    dm = _load_derive_module()
    eps = float(dm.NO_WASH_EPS)
    g_all = dm.load_joined()

    specs = {s.name: s for s in INTERFACE_NEIGHBORS["MISO"]}
    specs[MISO_MANITOBA_SEAM_SPEC.name] = MISO_MANITOBA_SEAM_SPEC

    report: dict = {
        "probe": "miso-245 G-CLAMP-N — the reaching value must be the UNCLAMPED quantile",
        "addendum": (
            "results/calibration/ADDENDUM-miso245-the-test-passed-with-low-power-"
            "and-one-more-leg-can-still-kill-it-2026-09-08.md §0c"
        ),
        "keeper": "2026-09-07-miso-243-spp-pairing",
        "zero_lp": True,
        "read_only": True,
        "can_only_invalidate": True,
        "rule": (
            "v_raw(delta) <= lim_seam at the reaching delta and at delta in "
            "{-1,0,+1}; a FAIL voids that entry's m_j and WITHDRAWS A-CONFIRMED"
        ),
        "detail": [],
    }
    ok_all = True

    for e in ENTRIES:
        g = g_all.loc[[e["year"]]]
        g3 = g.dropna(subset=["da"] + [n.name for n in INTERFACE_NEIGHBORS["MISO"]])
        da = g3["da"].to_numpy(dtype=float)
        flow = g3[e["seam"]].to_numpy(dtype=float)
        spec = specs[e["seam"]]
        step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
        mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step
        imp = [float(np.quantile(da, 1.0 - float((flow > m).mean()))) for m in mids]
        lim = min(imp) - eps
        xs = np.sort(da)
        n = int(xs.size)

        rows = []
        entry_ok = True
        for d in sorted({-1, 0, 1, int(e["signed_delta"])}):
            share = (e["count"] + d) / float(n)
            q = (1.0 - share) if e["side"] == "import" else share
            v_raw = _q_linear(xs, q)
            # The clamp only ever applies on the export side.
            clamped = bool(e["side"] == "export" and v_raw > lim)
            entry_ok &= not clamped
            rows.append(
                {
                    "delta": d,
                    "is_reaching_delta": bool(d == int(e["signed_delta"])),
                    "v_raw": round(v_raw, 10),
                    "v_after_clamp": round(
                        min(v_raw, lim) if e["side"] == "export" else v_raw, 10
                    ),
                    "rounded": round(
                        float(
                            np.round(
                                min(v_raw, lim) if e["side"] == "export" else v_raw, 2
                            )
                        ),
                        2,
                    ),
                    "clamped": clamped,
                }
            )
        ok_all &= entry_ok
        report["detail"].append(
            {
                "entry": f"{e['year']} {e['seam']} {e['side']} band {e['band']}",
                "committed": e["committed"],
                "clamp_lim": round(lim, 10),
                "cheapest_import_band": round(min(imp), 10),
                "margin_to_clamp_at_reaching_delta": round(
                    lim - next(r["v_raw"] for r in rows if r["is_reaching_delta"]), 10
                ),
                "rows": rows,
                "PASS": bool(entry_ok),
            }
        )

    report["PASS"] = bool(ok_all)
    report["VERDICT_STATUS"] = (
        "A-CONFIRMED STANDS (this leg removes a way it could be false; it adds no evidence)"
        if ok_all
        else "A-CONFIRMED WITHDRAWN — a reaching value is the clamp, not the quantile"
    )
    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
