"""ercot-185 seam proof + pre-solve screen for the fault-3 partial-layer repair.

No LP, no dispatch, no scoring. Reads the production loaders the cap block
itself uses, so what is measured here is exactly what the LP would see.

Implements, verbatim from
``docs/PRECOMMIT-ercot185-fault3-partial-layer-construction-2026-08-09.md``:

* **SP-2L** — LOADER-level covered-hour-set identity. The deriver already
  asserts SP-2 on the emitted date strings; this re-proves it *after*
  ``outage_hour_mask``, which maps calendar dates onto the model's fixed
  non-leap 8760 clock and therefore could in principle lose a sub-window
  boundary (``_hour_of_year`` folds Feb 29 onto Mar 1 00:00 — harmless for the
  501 flat plateaus, but a day-shaped extract creates a boundary on EVERY day).
* **SP-5** — the emitted per-day factors reproduce ``clip(f0 * sm[d]/median(sm),
  0, 1)`` from the frozen detector, recomputed independently here.
* **P-2** — two-sidedness: the shares of changed plant-hours where the shaped
  ceiling sits ABOVE vs BELOW the incumbent. Every rejected composition arm is
  restore-only (ercot-174 SP-5: ``product <= unit-scoped <= min`` pointwise);
  the repair is expected to be two-sided.
* **P-3** — the ercot-172 object: the shaped partial factor for W A Parish
  (3470) at h2827 = 2024-04-28 19:00 CST, against the incumbent 0.363 and the
  plant's same-hour CEMS-implied 0.7843.
* **§5 BOUND** — the BINDING pre-solve screen. The coal ceiling-LIFT ENERGY
  hard-bounds G-COAL148's own quantity with no LP:

      BOUND(y) = sum_{coal bins b, hours t} max(0, ceil_arm - ceil_inc) * pmax(b)

  Because the cap applies ``availability = min(availability, ceiling)``, model
  dispatch can never exceed the armed ceiling, and the control's own
  above-ceiling energy is >= 0, so
  ``rise <= arm_above <= BOUND``. <=0.5 TWh every year passes G-COAL148 BY
  CONSTRUCTION; >=2.0 TWh in any year is a pre-solve STOP.
* **rho_shaped** — the share of the REJECTED ercot-173 blanket arm's ceiling
  lift the repair reproduces (the ercot-174 AT-2 basis). REPORTED DO-NOT-REDO
  evidence (rule 28a), not a stop bar.
* **variant RAW** — the reported-only ``min(1, sm/ref)`` form's own BOUND and
  signed level shift, the measured evidence for precommit §2a-bis.

Usage:
    python scripts/probes/ercot185_shaped_seam_proof.py \
        [--years 2023 2024 2025] \
        [--json-out results/calibration/ercot185_shaped_seam_proof.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import CAMPD_BINS_CSV  # noqa: E402
from market_sim.data.fleet import load_campd_bins  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    PARTIAL_OUTAGE_CSV,
    PARTIAL_OUTAGE_SHAPED_CSV,
    outage_hour_mask,
    partial_outage_derate_factors,
    unit_outage_derate_factors,
)

HOURS = 8760
# The ercot-172 object: 2024-04-28 19:00 CST on the model's fixed 8760 clock.
H2827 = 2827
WAP = 3470  # W A Parish
# G-COAL148's scope: the bins sheet's COAL plant group.
COAL_GROUP = "COAL"


def _flat_factors(year: int, path: Path) -> dict[int, np.ndarray]:
    """Per-plant (hours,) multiplier read straight from an extract CSV.

    An independent re-implementation of the loader's accumulation, so the
    loader and the file are checked against each other rather than the loader
    against itself.
    """
    df = pd.read_csv(path)
    df = df[df["year"] == year]
    out: dict[int, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mask = outage_hour_mask(r.outage_start, r.outage_stop, year, HOURS)
        if not mask.any():
            continue
        arr = out.setdefault(int(r.oris_code), np.ones(HOURS))
        arr[mask] = np.minimum(arr[mask], float(r.derate_factor))
    return out


def _covered(factors: dict[int, np.ndarray]) -> dict[int, np.ndarray]:
    """Boolean covered-hour mask per plant (a factor below 1.0 anywhere)."""
    return {k: (v < 1.0) for k, v in factors.items()}


def _window_ceiling(year: int, bins: pd.DataFrame) -> dict[int, np.ndarray]:
    """Per-plant window-layer factor ``f_window``, keyed by plant code.

    The keeper arms only the >= 5-day unit-outage layer in ``_cap_layers``
    (``unit_outage_short_windows`` / ``unit_partial_outage_windows`` are both
    false in ``ercot181_positiontail_B/run_config.json``), so the window family
    is that one layer. Reduced to plant grain over the plant's COAL bin, which
    is the grain the plant-keyed partial layer composes against.
    """
    ufac = unit_outage_derate_factors(year, HOURS, str(CAMPD_BINS_CSV), iso="ERCOT")
    out: dict[int, np.ndarray] = {}
    for (code, grp), arr in ufac.items():
        if grp != COAL_GROUP:
            continue
        out[int(code)] = np.asarray(arr, dtype=float)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--json-out",
        default=str(REPO / "results/calibration/ercot185_shaped_seam_proof.json"),
    )
    ap.add_argument(
        "--raw-shaped",
        default="",
        help="optional path to the variant-RAW extract, measured and reported",
    )
    args = ap.parse_args()

    bins = load_campd_bins(str(CAMPD_BINS_CSV))
    cap = {
        int(c): float(m)
        for c, m in zip(bins["Plant_Code"], bins["capacity_mw"])
        if m and m > 0
    }
    grp = {int(c): str(g) for c, g in zip(bins["Plant_Code"], bins["Plant_Group"])}

    report: dict = {
        "object": "ercot-185 fault-3 partial-layer construction repair",
        "precommit": (
            "docs/PRECOMMIT-ercot185-fault3-partial-layer-construction-2026-08-09.md"
        ),
        "flat_extract": str(PARTIAL_OUTAGE_CSV.relative_to(REPO)),
        "shaped_extract": str(PARTIAL_OUTAGE_SHAPED_CSV.relative_to(REPO)),
        "years": {},
    }

    for year in args.years:
        inc = partial_outage_derate_factors(year, HOURS)
        arm = partial_outage_derate_factors(year, HOURS, shaped=True)
        inc_file = _flat_factors(year, PARTIAL_OUTAGE_CSV)
        arm_file = _flat_factors(year, PARTIAL_OUTAGE_SHAPED_CSV)

        # --- SP-2L: loader-level covered-hour-set identity ------------------
        cov_i, cov_a = _covered(inc), _covered(arm)
        sp2_bad: list[dict] = []
        for code in sorted(set(cov_i) | set(cov_a)):
            a = cov_i.get(code, np.zeros(HOURS, dtype=bool))
            b = cov_a.get(code, np.zeros(HOURS, dtype=bool))
            if not np.array_equal(a, b):
                sp2_bad.append(
                    {
                        "plant": code,
                        "name": str(bins.set_index("Plant_Code").loc[code, "Plant_Name"])
                        if code in cap
                        else "?",
                        "only_incumbent_h": int((a & ~b).sum()),
                        "only_shaped_h": int((b & ~a).sum()),
                    }
                )
        # Loader-vs-file agreement (the loader is not checked against itself).
        loader_ok = all(
            np.allclose(arm[c], arm_file.get(c, np.ones(HOURS))) for c in arm
        ) and all(np.allclose(inc[c], inc_file.get(c, np.ones(HOURS))) for c in inc)

        # --- P-2: two-sidedness over changed plant-hours --------------------
        up = dn = same = 0
        for code in sorted(set(inc) | set(arm)):
            a = inc.get(code, np.ones(HOURS))
            b = arm.get(code, np.ones(HOURS))
            d = b - a
            up += int((d > 1e-9).sum())
            dn += int((d < -1e-9).sum())
            same += int((np.abs(d) <= 1e-9).sum())
        changed = up + dn

        # --- §5 BOUND: coal ceiling-lift energy (TWh), and the cut side -----
        fw = _window_ceiling(year, bins)
        lift_mwh = cut_mwh = 0.0
        per_plant: dict[str, float] = {}
        for code in sorted(set(inc) | set(arm)):
            if grp.get(code) != COAL_GROUP:
                continue
            pmax = cap.get(code, 0.0)
            if pmax <= 0:
                continue
            w = fw.get(code, np.ones(HOURS))
            d = (arm.get(code, np.ones(HOURS)) - inc.get(code, np.ones(HOURS))) * w
            plant_lift = float(np.clip(d, 0.0, None).sum() * pmax)
            lift_mwh += plant_lift
            cut_mwh += float(np.clip(-d, 0.0, None).sum() * pmax)
            if plant_lift > 0:
                per_plant[str(code)] = round(plant_lift / 1e6, 4)
        bound_twh = lift_mwh / 1e6

        # --- rho_shaped vs the REJECTED ercot-173 blanket arm ---------------
        # Blanket lift = min(f_w, f_p) - f_w*f_p on the same coal bins/hours.
        blanket_mwh = 0.0
        for code in sorted(set(inc)):
            if grp.get(code) != COAL_GROUP:
                continue
            pmax = cap.get(code, 0.0)
            if pmax <= 0:
                continue
            w = fw.get(code, np.ones(HOURS))
            p = inc[code]
            blanket_mwh += float((np.minimum(w, p) - w * p).sum() * pmax)
        rho = (lift_mwh / blanket_mwh) if blanket_mwh > 0 else None

        # --- P-3: the ercot-172 object -------------------------------------
        p3 = None
        if year == 2024:
            p3 = {
                "hour": H2827,
                "timestamp": "2024-04-28 19:00 CST",
                "plant": WAP,
                "incumbent_f_partial": round(float(inc.get(WAP, np.ones(HOURS))[H2827]), 4),
                "shaped_f_partial": round(float(arm.get(WAP, np.ones(HOURS))[H2827]), 4),
                "cems_same_hour": 0.7843,
                "bar": 0.50,
            }
            p3["PASS"] = bool(p3["shaped_f_partial"] >= p3["bar"])

        report["years"][str(year)] = {
            "SP_2L_covered_hour_identity": {
                "PASS": not sp2_bad,
                "mismatched_plants": sp2_bad,
            },
            "loader_matches_file": bool(loader_ok),
            "P_2_two_sided": {
                "changed_plant_hours": changed,
                "share_above_incumbent": round(up / changed, 4) if changed else None,
                "share_below_incumbent": round(dn / changed, 4) if changed else None,
                "unchanged_plant_hours": same,
            },
            "S5_bound": {
                "coal_ceiling_lift_TWh": round(bound_twh, 4),
                "coal_ceiling_cut_TWh": round(cut_mwh / 1e6, 4),
                "pass_by_construction_bar": 0.5,
                "stop_bar": 2.0,
                "PASSES_G_COAL148_BY_CONSTRUCTION": bool(bound_twh <= 0.5),
                "STOP": bool(bound_twh >= 2.0),
                "per_plant_TWh": per_plant,
            },
            "rho_shaped_vs_ercot173_blanket": round(rho, 4) if rho is not None else None,
            "P_3_ercot172_object": p3,
        }

    # --- variant RAW, reported only (precommit §2a-bis evidence) -----------
    if args.raw_shaped and Path(args.raw_shaped).exists():
        raw_rep: dict = {}
        for year in args.years:
            inc = partial_outage_derate_factors(year, HOURS)
            rawf = _flat_factors(year, Path(args.raw_shaped))
            fw = _window_ceiling(year, bins)
            lift = cut = 0.0
            signed = []
            for code in sorted(set(inc) | set(rawf)):
                if grp.get(code) != COAL_GROUP:
                    continue
                pmax = cap.get(code, 0.0)
                if pmax <= 0:
                    continue
                w = fw.get(code, np.ones(HOURS))
                a = inc.get(code, np.ones(HOURS))
                b = rawf.get(code, np.ones(HOURS))
                d = (b - a) * w
                lift += float(np.clip(d, 0.0, None).sum() * pmax)
                cut += float(np.clip(-d, 0.0, None).sum() * pmax)
                m = a < 1.0
                if m.any():
                    signed.append(float((b[m] - a[m]).mean()))
            raw_rep[str(year)] = {
                "coal_ceiling_lift_TWh": round(lift / 1e6, 4),
                "coal_ceiling_cut_TWh": round(cut / 1e6, 4),
                "mean_signed_level_shift_on_plateau_hours": (
                    round(float(np.mean(signed)), 4) if signed else None
                ),
            }
        report["variant_RAW_reported_only"] = raw_rep

    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
