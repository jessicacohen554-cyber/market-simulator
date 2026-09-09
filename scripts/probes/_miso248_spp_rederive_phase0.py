#!/usr/bin/env python3
"""miso-248 phase 0 (ZERO LP) — the SPP hourly seam ladder on the repaired clock.

Governed by ``results/calibration/PREREG-miso248-the-spp-hourly-ladder-rederive-
on-the-repaired-clock-2026-09-09.md``, pushed with this file before either ran.

Legs, each with its decision rule fixed in the PREREG before the number exists:

``P-0``  provenance stamp — git HEAD plus the blob sha of every parsed file, so
        no gate literal is ever copied from a file that can move.
``P-1``  SCOPE.  Re-derive all 192 entries of ``MISO_SEAM_LADDER_BY_YEAR`` and
        the 48 of ``MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`` and report
        which pin reproduces at ``atol=0.005``.  PREREG §1 fixes what each
        outcome means for the session's scope.
``P-2``  THE HALF-APPLIED CHANGE.  The solve-time SPP anchor at HEAD against the
        same series at the keeper's own basis ``f29b7ab0``.  PREREG §3: if they
        are identical the premise is FALSIFIED and the session stops.
``P-3``  the re-derive, with the three STOP conditions of PREREG §4.
``P-4``  the mechanism's OWN measured footprint ``F(year)`` and the screen-year
        selection rule of PREREG §5.
``P-5``  the pre-solve prediction ``dE_pred`` the screen gate ``G-1`` tests
        (PREREG §6).

Nothing here reads an actual, a criterion or a residual.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)
ATOL = 0.005
KEEPER = REPO / "results" / "calibration" / "miso247_fullspan_K"
KEEPER_BASIS_SHA = "f29b7ab022d399f40904379d86eb2324f08535e6"
SPP_ZONAL_REL = "data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet"
OUT = REPO / "results" / "calibration" / "_miso248_spp_rederive_phase0.json"


def _sh(*args: str) -> str:
    return subprocess.run(
        args, cwd=REPO, capture_output=True, text=True, check=False
    ).stdout.strip()


def _blob_sha(rel: str) -> str:
    p = REPO / rel
    if not p.exists():
        return "ABSENT"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _load_derive_module():
    import importlib.util

    script = REPO / "scripts/data/derive_miso_seam_ladders.py"
    spec = importlib.util.spec_from_file_location("_derive_miso_seam", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def p0_provenance() -> dict:
    return {
        "git_head": _sh("git", "rev-parse", "HEAD"),
        "git_head_short": _sh("git", "rev-parse", "--short", "HEAD"),
        "tree_clean": _sh("git", "status", "--porcelain") == "",
        "keeper_basis_sha": KEEPER_BASIS_SHA,
        "blob_sha256_16": {
            rel: _blob_sha(rel)
            for rel in (
                SPP_ZONAL_REL,
                "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet",
                "data/raw/eia-930-interchange/MISO interchange hourly.parquet",
                "src/market_sim/model/interchange/spec.py",
                "src/market_sim/config/interchange_config.py",
                "scripts/data/derive_miso_seam_ladders.py",
            )
        },
    }


def p1_scope(dm, joined) -> dict:
    """PREREG §1: which of the two tables reproduces at HEAD."""
    from market_sim.config.interchange_config import MISO_SEAM_LADDER_BY_YEAR
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR as HOURLY_SPP,
    )

    incumbent: dict = {"n_entries": 0, "n_mismatched": 0, "max_abs": 0.0, "rows": {}}
    for year in YEARS:
        derived, _n = dm.derive(joined.loc[[year]])
        for seam, sides in MISO_SEAM_LADDER_BY_YEAR[year].items():
            for side in ("import", "export"):
                a = np.asarray(sides[side], dtype=float)
                b = np.asarray(derived[seam][side], dtype=float)
                d = np.abs(a - b)
                incumbent["n_entries"] += a.size
                incumbent["n_mismatched"] += int((d > ATOL).sum())
                incumbent["max_abs"] = max(incumbent["max_abs"], float(d.max()))
                if (d > ATOL).any():
                    incumbent["rows"][f"{year}/{seam}/{side}"] = {
                        "registry": a.tolist(),
                        "rederived": b.round(4).tolist(),
                        "max_abs": float(d.max()),
                    }

    hourly: dict = {"n_entries": 0, "n_mismatched": 0, "max_abs": 0.0, "rows": {}}
    for year in YEARS:
        sample = joined.loc[[year]]
        joined_rows = len(sample.join(dm.load_spp_hub_da(), how="left"))
        derived, _n = dm.derive_spp_neighbour_hourly(sample)
        for side in ("import", "export"):
            a = np.asarray(HOURLY_SPP[year]["SPP"][side], dtype=float)
            b = np.asarray(derived[side], dtype=float)
            d = np.abs(a - b)
            hourly["n_entries"] += a.size
            hourly["n_mismatched"] += int((d > ATOL).sum())
            hourly["max_abs"] = max(hourly["max_abs"], float(d.max()))
            if (d > ATOL).any():
                hourly["rows"][f"{year}/SPP/{side}"] = {
                    "registry": a.tolist(),
                    "rederived": b.round(4).tolist(),
                    "max_abs": float(d.max()),
                    "max_rel": float(
                        np.max(d / np.maximum(np.abs(a), 1e-9)),
                    ),
                }
        hourly.setdefault("row_count_pin", {})[str(year)] = {
            "sample_rows": len(sample),
            "joined_rows": joined_rows,
            "pin_holds": joined_rows == len(sample),
        }

    return {
        "incumbent_MISO_SEAM_LADDER_BY_YEAR": incumbent,
        "hourly_SPP_overlay": hourly,
        "VERDICT_scope": (
            "HOURLY SPP OVERLAY ONLY"
            if incumbent["n_mismatched"] == 0 and hourly["n_mismatched"] > 0
            else (
                "BOTH TABLES"
                if incumbent["n_mismatched"] > 0
                else "NEITHER — nothing to re-derive"
            )
        ),
    }


def p2_half_applied() -> dict:
    """PREREG §3: the solve-time anchor at HEAD vs at the keeper's own basis."""
    import pandas as pd

    scratch = Path("/tmp/_miso248_old_spp.parquet")
    blob = subprocess.run(
        ["git", "show", f"{KEEPER_BASIS_SHA}:{SPP_ZONAL_REL}"],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    if blob.returncode != 0 or not blob.stdout:
        return {"available": False, "reason": blob.stderr.decode()[:400]}
    scratch.write_bytes(blob.stdout)

    from market_sim.data.eia_loader import (
        MISO_SPP_ANCHOR_HUB,
        measured_miso_spp_hub_prices,
    )

    old_frame = pd.read_parquet(scratch)
    out: dict = {"available": True, "hub": MISO_SPP_ANCHOR_HUB, "per_year": {}}
    identical_all = True
    for year in YEARS:
        new = np.asarray(measured_miso_spp_hub_prices("MISO", year, 8760), dtype=float)
        f = old_frame[
            (old_frame["year"] == year)
            & (old_frame["zone"].astype(str) == MISO_SPP_ANCHOR_HUB)
        ]
        old = (
            pd.to_numeric(f.sort_values("hour")["da"], errors="coerce")
            .interpolate(limit=2)
            .bfill()
            .ffill()
            .to_numpy(dtype=float)[:8760]
        )
        diff = new - old
        moved = int((np.abs(diff) > 1e-9).sum())
        identical_all = identical_all and moved == 0
        out["per_year"][str(year)] = {
            "hours_moved": moved,
            "share_moved": round(moved / 8760, 6),
            "max_abs_delta": round(float(np.abs(diff).max()), 4),
            "mean_new": round(float(new.mean()), 4),
            "mean_old": round(float(old.mean()), 4),
            "sorted_value_multiset_identical": bool(
                np.allclose(np.sort(new), np.sort(old), atol=1e-6)
            ),
        }
    out["PREMISE_FALSIFIED_series_identical"] = identical_all
    return out


def p3_rederive(dm, joined) -> dict:
    """PREREG §4: the new offsets plus the three STOP conditions."""
    out: dict = {"per_year": {}, "stop_conditions": {}}
    stop = {"row_count_pin": True, "monotone": True, "no_wash": True}
    for year in YEARS:
        sample = joined.loc[[year]]
        try:
            derived, notes = dm.derive_spp_neighbour_hourly(sample)
        except ValueError as exc:  # the miso-243 row-count invariant
            stop["row_count_pin"] = False
            out["per_year"][str(year)] = {"ERROR": str(exc)}
            continue
        imp = [round(float(v), 2) for v in derived["import"]]
        exp = [round(float(v), 2) for v in derived["export"]]
        rising = imp == sorted(imp)
        falling = exp == sorted(exp, reverse=True)
        no_wash = max(exp) < min(imp)
        stop["monotone"] = stop["monotone"] and rising and falling
        stop["no_wash"] = stop["no_wash"] and no_wash
        out["per_year"][str(year)] = {
            "import": imp,
            "export": exp,
            "import_rising": rising,
            "export_falling": falling,
            "no_wash": no_wash,
            "notes": notes,
        }
    out["stop_conditions"] = stop
    out["REDERIVE_ADMISSIBLE"] = all(stop.values())
    return out


def _clearing_counts(p, hub, offsets, side) -> np.ndarray:
    """Hours each band clears, on the LP's own optimality convention."""
    n = []
    for delta in offsets:
        offer = hub + float(delta)
        n.append(int((p > offer).sum() if side == "import" else (p < offer).sum()))
    return np.asarray(n, dtype=float)


def p4_p5_footprint(new_offsets: dict) -> dict:
    """PREREG §5/§6: F(year), the screen-year selection, and dE_pred."""
    import pandas as pd

    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import measured_miso_spp_hub_prices
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR as HOURLY_SPP,
    )

    spec = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["SPP"]
    cap = spec.interface_limit_mw / SEAM_FLOW_TRANCHES

    out: dict = {"band_cap_mw": round(cap, 4), "per_year": {}}
    for year in YEARS:
        sysp = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        sysp = sysp[
            (sysp["zone"].astype(str) == "MISO_external")
            & (sysp["pass"].astype(str) == "P1")
        ].sort_values("hour")
        p = sysp["price"].to_numpy(dtype=float)[:8760]
        hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, 8760), dtype=float)
        entry = out["per_year"].setdefault(str(year), {})
        F = 0.0
        dE = 0.0
        for side in ("import", "export"):
            old = np.asarray(HOURLY_SPP[year]["SPP"][side], dtype=float)
            new = np.asarray(new_offsets[str(year)][side], dtype=float)
            n_old = _clearing_counts(p, hub, old, side)
            n_new = _clearing_counts(p, hub, new, side)
            # F counts STATUS FLIPS hour by hour, not the net count change.
            flips = []
            for k in range(len(old)):
                c_old = (p > hub + old[k]) if side == "import" else (p < hub + old[k])
                c_new = (p > hub + new[k]) if side == "import" else (p < hub + new[k])
                flips.append(int((c_old != c_new).sum()))
            F += cap * float(sum(flips))
            sgn = 1.0 if side == "import" else -1.0
            dE += sgn * cap * float((n_new - n_old).sum())
            entry[side] = {
                "delta_offsets": (new - old).round(2).tolist(),
                "max_abs_delta_offset": round(float(np.abs(new - old).max()), 2),
                "hours_clearing_old": n_old.astype(int).tolist(),
                "hours_clearing_new": n_new.astype(int).tolist(),
                "status_flip_hours": flips,
            }
        entry["F_MWh"] = round(F, 1)
        entry["F_TWh"] = round(F / 1e6, 4)
        entry["dE_pred_TWh"] = round(dE / 1e6, 4)
        entry["max_abs_delta_offset_all_bands"] = round(
            max(
                float(
                    np.abs(
                        np.asarray(new_offsets[str(year)][s], dtype=float)
                        - np.asarray(HOURLY_SPP[year]["SPP"][s], dtype=float)
                    ).max()
                )
                for s in ("import", "export")
            ),
            2,
        )

    # PREREG §5 selection rule, applied exactly as written.
    ranked = sorted(YEARS, key=lambda y: out["per_year"][str(y)]["F_MWh"], reverse=True)
    top, second = ranked[0], ranked[1]
    f_top = out["per_year"][str(top)]["F_MWh"]
    f_second = out["per_year"][str(second)]["F_MWh"]
    tie = f_top > 0 and abs(f_top - f_second) / f_top <= 0.01
    if tie:
        cand = [top, second]
        best = max(
            cand,
            key=lambda y: out["per_year"][str(y)]["max_abs_delta_offset_all_bands"],
        )
        vals = {
            y: out["per_year"][str(y)]["max_abs_delta_offset_all_bands"] for y in cand
        }
        if vals[cand[0]] == vals[cand[1]]:
            best = min(cand)
            rule = "tie within 1% AND equal max |delta| -> earliest year"
        else:
            rule = "tie within 1% -> larger max |delta offset|"
    else:
        best = top
        rule = "argmax F(year)"
    out["SCREEN_YEAR"] = int(best)
    out["selection_rule_applied"] = rule
    out["F_ranking_TWh"] = {str(y): out["per_year"][str(y)]["F_TWh"] for y in ranked}
    out["dE_pred_screen_year_TWh"] = out["per_year"][str(best)]["dE_pred_TWh"]
    out["G1_form"] = (
        "A (|dE_pred| >= 0.05 TWh)"
        if abs(out["dE_pred_screen_year_TWh"]) >= 0.05
        else "B (|dE_pred| < 0.05 TWh)"
    )
    return out


def main() -> None:
    dm = _load_derive_module()
    joined = dm.load_joined()

    record: dict = {
        "probe": "miso-248 phase 0 — SPP hourly seam ladder re-derive on the repaired clock",
        "prereg": (
            "results/calibration/PREREG-miso248-the-spp-hourly-ladder-rederive-"
            "on-the-repaired-clock-2026-09-09.md"
        ),
        "zero_lp": True,
        "keeper": "2026-09-09-miso-247-p19-posture",
        "cited_data_change": "86e45462 (2026-09-09) — SPP actual-LMP clock repair",
        "P0_provenance": p0_provenance(),
    }
    record["P1_scope"] = p1_scope(dm, joined)
    record["P2_half_applied_change"] = p2_half_applied()
    record["P3_rederive"] = p3_rederive(dm, joined)

    if record["P2_half_applied_change"].get("PREMISE_FALSIFIED_series_identical"):
        record["SESSION_STOPS"] = (
            "PREREG §3: the anchor series is identical at HEAD and at the keeper's basis — the premise is FALSIFIED"
        )
    elif not record["P3_rederive"]["REDERIVE_ADMISSIBLE"]:
        record["SESSION_STOPS"] = "PREREG §4: a STOP condition on the re-derive failed"
    else:
        new_offsets = {
            str(y): {
                "import": record["P3_rederive"]["per_year"][str(y)]["import"],
                "export": record["P3_rederive"]["per_year"][str(y)]["export"],
            }
            for y in YEARS
        }
        record["P4_P5_footprint"] = p4_p5_footprint(new_offsets)

    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
