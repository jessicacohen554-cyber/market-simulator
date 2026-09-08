"""miso-244 L' — the pre-registered LIVENESS gate, on BOTH external buses.

Pre-registration: ``PREREG-miso244-diagnose-the-incumbent-ladder-cent-2026-09-08.md``
§3 (the gate, its bars and its disposition), as repaired by
``ADDENDUM-miso244-the-verdict-is-not-a-tie-and-my-liveness-gate-named-the-wrong-bus-2026-09-08.md``
§0c, which is pushed BEFORE any number here exists.  **No bar moves**: the only
repair is that ``L`` and ``dq_hat`` are evaluated on ``MISO_external_South`` (the
bus the moving South bands are hosted on) as well as on ``MISO_external`` (the
bus the PREREG named), and **the gate takes the MAXIMUM over the two**, which is
strictly harder to pass than either alone.

    INERT, and NO SCREEN SOLVE AUTHORIZED, iff
        max_bus max_year L        <= 0.001   AND
        max_bus max_year |dq_hat| <= 5.0 MW

``L`` is the share of the year's hours whose South band-count vector
``(n_i, n_e)`` changes when the committed incumbent South ladder is replaced by
its HEAD-derived counterpart; ``dq_hat = 375 MW * (dn_i - dn_e)``, South's own
step (``3000 / 8``), the identical form miso-243's P-4 used.  Membership is
evaluated in each side's own operand form: an import band is in merit iff
``p(t) >= imp_k``, an export band iff ``p(t) <= exp_k``.

Both are FOOTPRINT measures computed from two ladders and one committed price
series.  **Zero scored criterion, zero band comparison and zero residual enters
either.**  The gate is STOP-only: it may kill the arm, it may never promote one.

STOP-ONLY and GATED: L'.  REPORTED, NEVER GATED: the changed-hour counts, the
per-bus price statistics, and the per-band moves.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/_miso244_liveness_gate.json"
KEEPER = REPO / "results/calibration/miso243_sppair_K"
YEARS = (2023, 2024, 2025)
SIDES = ("import", "export")
BUSES = ("MISO_external_South", "MISO_external")

# ---- BARS, quoted as literals from the PREREG §3 / ADDENDUM §0c --------------
L_BAR = 0.001
DQ_BAR = 5.0
SOUTH_STEP_MW = 3000.0 / 8.0  # South's interface limit / SEAM_FLOW_TRANCHES

# ---- The moves this session PUBLISHED in the addendum, restated as literals --
# (a provenance leg against this session's own prior claim; ADDENDUM §2)
REF_MOVES = {
    (2023, "export", 4): (27.69, 27.70),
    (2024, "export", 5): (23.77, 23.76),
}
REF_ROWS_PER_BUS_YEAR = 8760


def _load_derive_module():
    script = REPO / "scripts/data/derive_miso_seam_ladders.py"
    spec = importlib.util.spec_from_file_location("_miso244L_derive", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _band_counts(p: np.ndarray, imp: np.ndarray, exp: np.ndarray) -> tuple:
    """(n_i, n_e) per hour, each side in its OWN operand form.

    An import band is in merit iff the bus price clears its offer
    (``p >= imp_k``); an export sink iff the bus price is at or below what it
    pays (``p <= exp_k``).  Written as two explicit comparisons rather than an
    algebraic rearrangement: a rearrangement is exact in real arithmetic and NOT
    in IEEE at ties, which cost miso-242 a failed gate on 43 exact-tie hours.
    """
    n_i = (p[:, None] >= imp[None, :]).sum(axis=1)
    n_e = (p[:, None] <= exp[None, :]).sum(axis=1)
    return n_i, n_e


def main() -> None:
    from market_sim.config.interchange_config import MISO_SEAM_LADDER_BY_YEAR

    dm = _load_derive_module()
    g_all = dm.load_joined()

    report: dict = {
        "probe": "miso-244 L' — the pre-registered liveness gate, both external buses",
        "prereg": (
            "results/calibration/"
            "PREREG-miso244-diagnose-the-incumbent-ladder-cent-2026-09-08.md §3"
        ),
        "addendum": (
            "results/calibration/ADDENDUM-miso244-the-verdict-is-not-a-tie-and-"
            "my-liveness-gate-named-the-wrong-bus-2026-09-08.md §0c"
        ),
        "keeper": "2026-09-07-miso-243-spp-pairing",
        "zero_lp": True,
        "read_only": True,
        "stop_only": True,
        "basis": (
            "model basis = the keeper's COMMITTED P1 bus price "
            "(hourly/system_<year>.parquet); ladders = committed incumbent vs "
            "HEAD-derived. Footprint measures only — zero scored criterion, "
            "zero band comparison, zero residual."
        ),
        "bars": {
            "L_bar": L_BAR,
            "dq_hat_bar_mw": DQ_BAR,
            "south_step_mw": SOUTH_STEP_MW,
        },
        "gates": {},
        "reported": {},
    }
    fails: list[str] = []

    # ---- G-MOVE: which South bands move, against this session's own literals --
    gmove = {"detail": {}, "PASS": True}
    head_south: dict[int, dict[str, list[float]]] = {}
    for year in YEARS:
        out, _notes = dm.derive(g_all.loc[[year]])
        head_south[year] = {s: list(out["South"][s]) for s in SIDES}
        moved = []
        for side in SIDES:
            c = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["South"][side], float)
            h = np.asarray(head_south[year][side], float)
            for k in np.nonzero(np.abs(h - c) >= 5e-9)[0]:
                moved.append(
                    {
                        "side": side,
                        "band": int(k) + 1,
                        "committed": float(c[k]),
                        "head": float(h[k]),
                    }
                )
        expected = [
            {"side": s, "band": b, "committed": v[0], "head": v[1]}
            for (y, s, b), v in REF_MOVES.items()
            if y == year
        ]
        ok = moved == expected
        gmove["detail"][str(year)] = {
            "moved": moved,
            "expected": expected,
            "PASS": bool(ok),
        }
        gmove["PASS"] &= bool(ok)
    report["gates"]["G_MOVE"] = gmove
    if not gmove["PASS"]:
        fails.append("G-MOVE")

    # ---- G-BUS: the committed sidecar carries both buses, 8760 P1 rows each --
    gbus = {"detail": {}, "PASS": True}
    prices: dict[tuple[int, str], np.ndarray] = {}
    for year in YEARS:
        sysd = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysd = sysd[sysd["pass"].astype(str) == "P1"]
        yr = {}
        for bus in BUSES:
            sub = sysd[sysd["zone"].astype(str) == bus].sort_values("hour")
            p = sub["price"].to_numpy(dtype=float)
            prices[(year, bus)] = p
            ok = len(p) == REF_ROWS_PER_BUS_YEAR
            yr[bus] = {"rows": int(len(p)), "PASS": bool(ok)}
            gbus["PASS"] &= bool(ok)
        gbus["detail"][str(year)] = yr
    report["gates"]["G_BUS"] = gbus
    if not gbus["PASS"]:
        fails.append("G-BUS")

    # ================= L' — the pre-registered liveness gate =================
    lp: dict = {"detail": {}, "max_L": 0.0, "max_abs_dq_hat_mw": 0.0}
    for bus in BUSES:
        per_bus = {}
        for year in YEARS:
            p = prices[(year, bus)]
            imp_c = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["South"]["import"], float)
            exp_c = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["South"]["export"], float)
            imp_h = np.asarray(head_south[year]["import"], float)
            exp_h = np.asarray(head_south[year]["export"], float)
            ni_c, ne_c = _band_counts(p, imp_c, exp_c)
            ni_h, ne_h = _band_counts(p, imp_h, exp_h)
            changed = (ni_c != ni_h) | (ne_c != ne_h)
            L = float(changed.mean())
            dn_i = float(ni_h.mean() - ni_c.mean())
            dn_e = float(ne_h.mean() - ne_c.mean())
            dq = SOUTH_STEP_MW * (dn_i - dn_e)
            per_bus[str(year)] = {
                "L_share_of_hours_with_changed_band_counts": round(L, 8),
                "hours_changed": int(changed.sum()),
                "hours": int(len(p)),
                "d_mean_n_import": round(dn_i, 8),
                "d_mean_n_export": round(dn_e, 8),
                "dq_hat_mw": round(dq, 6),
                "price_min": round(float(p.min()), 4),
                "price_max": round(float(p.max()), 4),
                "price_mean": round(float(p.mean()), 4),
            }
            lp["max_L"] = max(lp["max_L"], L)
            lp["max_abs_dq_hat_mw"] = max(lp["max_abs_dq_hat_mw"], abs(dq))
        lp["detail"][bus] = per_bus
    lp["max_L"] = round(lp["max_L"], 8)
    lp["max_abs_dq_hat_mw"] = round(lp["max_abs_dq_hat_mw"], 6)
    inert = lp["max_L"] <= L_BAR and lp["max_abs_dq_hat_mw"] <= DQ_BAR
    lp["INERT"] = bool(inert)
    lp["screen_authorized"] = bool(not inert)
    lp["rule"] = (
        "INERT (and NO screen solve authorized) iff max_bus max_year L <= 0.001 "
        "AND max_bus max_year |dq_hat| <= 5.0 MW (PREREG §3 as repaired by "
        "ADDENDUM §0c; bars unchanged, maximum over both buses)"
    )
    if not inert:
        # PREREG §3: argmax_year L, ties break to the EARLIEST year.
        best = max(
            YEARS,
            key=lambda y: (
                max(
                    lp["detail"][b][str(y)]["L_share_of_hours_with_changed_band_counts"]
                    for b in BUSES
                ),
                -y,
            ),
        )
        lp["SCREEN_YEAR"] = int(best)
    report["gates"]["L_prime"] = lp

    report["FAILED_LEGS"] = fails
    report["ALL_GATED_LEGS_PASS"] = not fails
    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps(report["gates"], indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
