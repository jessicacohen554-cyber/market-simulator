"""ercot-215 G-EXACT scorer (read-only, no LP): the armed member vs the
ercot-214 exact counterfactual, plus the dispatch-sidecar byte identity.

The ercot-215 delta (``ercot_ordc_adder_family_counterpart``) is post-solve
additive — it moves no MW — so the armed member's full-span scorecard was
EXACTLY computable before any solve ran, from the keeper's committed bytes
(``scripts/probes/ercot214_gspur_phase0.py`` §4 → ``counterfactual_repoint``
in ``results/calibration/ercot214_gspur_phase0.json``). G-EXACT
(``docs/PRECOMMIT-ercot215-counterpart-decontamination-2026-08-17.md`` §3)
therefore holds the armed member to that counterfactual with NO tolerance
band:

(a) the per-year spurious mid-band HOUR SETS (not just counts);
(b) the adder incidence nonzero / > $1 / > $100;
(c) the max written adder to the cent;
(d) zero G-CAP violations (``adder <= VOLL - lambda`` every hour);
(e) the armed member's NON-system hourly sidecars (class_hourly / storage /
    reserve_family x 3 years) byte-identical to the keeper's committed bundle
    — the dispatch is untouched by construction, so any difference is HEAD
    drift or a build defect.

ANY mismatch is a BUILD DEFECT — stop the line (no registration, no
promotion) — except a documented (e)-only miss from measured score-inert HEAD
drift, which escalates in the finding rather than being absorbed.

Also reports, for the finding's G-REPRO' row: the control-vs-keeper and
armed-vs-control sidecar hash tables.

Usage::

    python scripts/probes/ercot215_gexact.py \
        [--arm results/calibration/ercot215_decontam_B] \
        [--control results/calibration/ercot215_control_A] \
        [--keeper results/calibration/ercot213_anchor_B] \
        [--out results/calibration/ercot215_gexact.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
COUNTERFACTUAL = REPO / "results/calibration/ercot214_gspur_phase0.json"
DEFAULT_OUT = REPO / "results/calibration/ercot215_gexact.json"
YEARS = (2023, 2024, 2025)
MID_BAND = (150.0, 500.0)
VOLL = 5000.0  # the keeper's registered ordc_voll (run_config.json)
SIDECARS = ("class_hourly", "storage", "reserve_family", "system")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _hash_table(a: Path, b: Path) -> dict[str, dict]:
    """Per-sidecar byte comparison between two bundles' hourly/ dirs."""
    out: dict[str, dict] = {}
    for kind in SIDECARS:
        for year in YEARS:
            name = f"{kind}_{year}.parquet"
            pa, pb = a / "hourly" / name, b / "hourly" / name
            ha = _sha(pa) if pa.exists() else None
            hb = _sha(pb) if pb.exists() else None
            out[name] = {"a": ha, "b": hb, "identical": bool(ha and ha == hb)}
    return out


def _member(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Per-hour demand-weighted price / lambda / adder for one bundle-year
    (the `_ercot173_ab` conventions, matching ercot214_gspur_phase0)."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")].copy()
    overlay = np.zeros(len(df))
    for col in ("rtordpa_overlay", "dam_as_overlay", "ordc_adder"):
        if col in df.columns:
            overlay = overlay + df[col].to_numpy(float)
    df["lam_z"] = df["price"].to_numpy(float) - overlay

    def dw(col: str) -> np.ndarray:
        num = (df[col] * df["demand"]).groupby(df["hour"]).sum()
        den = df.groupby("hour")["demand"].sum()
        return (num / den).reindex(range(8760)).to_numpy(float)

    return {
        "price": dw("price"),
        "lam": dw("lam_z"),
        "adder": (
            df.groupby("hour")["ordc_adder"].first().reindex(range(8760)).to_numpy(float)
        ),
    }


def _spur_hours(m: np.ndarray, a: np.ndarray) -> list[int]:
    mm = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    return [
        int(h)
        for h in np.where(
            (mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & (aa < MID_BAND[0])
        )[0]
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--arm", type=Path, default=REPO / "results/calibration/ercot215_decontam_B"
    )
    ap.add_argument(
        "--control", type=Path, default=REPO / "results/calibration/ercot215_control_A"
    )
    ap.add_argument(
        "--keeper", type=Path, default=REPO / "results/calibration/ercot213_anchor_B"
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    cf = json.loads(COUNTERFACTUAL.read_text())["counterfactual_repoint"]
    act_all = pd.read_parquet(ACTUAL_LMP)

    out: dict = {
        "_provenance": {
            "scorer": "scripts/probes/ercot215_gexact.py",
            "arm": str(args.arm),
            "control": str(args.control),
            "keeper": str(args.keeper),
            "counterfactual": str(COUNTERFACTUAL),
            "gate": "PRECOMMIT-ercot215-counterpart-decontamination-2026-08-17.md §3 G-EXACT",
            "voll": VOLL,
        },
        "years": {},
        "sidecar_bytes": {},
    }

    all_ok = True
    for year in YEARS:
        a = (
            act_all[act_all.year == year]
            .set_index("hour")["rt"]
            .reindex(range(8760))
            .to_numpy()
        )
        m = _member(args.arm, year)
        exp = cf[str(year)]
        got_spur = _spur_hours(m["price"], a)
        got_inc = [
            int((m["adder"] > 1e-9).sum()),
            int((m["adder"] > 1.0).sum()),
            int((m["adder"] > 100.0).sum()),
        ]
        got_max = round(float(m["adder"].max()), 2)
        head = np.maximum(VOLL - m["lam"], 0.0)
        got_gcap = int((m["adder"] - head > 1e-6).sum())
        ok = np.isfinite(m["price"]) & np.isfinite(a)
        got_tail = int((m["price"][ok] > 200.0).sum())

        checks = {
            "spurious_hours": {
                "expected": exp["repointed_spurious_hours"],
                "got": got_spur,
                "match": got_spur == exp["repointed_spurious_hours"],
            },
            "adder_incidence_nonzero_gt1_gt100": {
                "expected": exp["adder_incidence_nonzero_gt1_gt100"]["repointed"],
                "got": got_inc,
                "match": got_inc == exp["adder_incidence_nonzero_gt1_gt100"]["repointed"],
            },
            "max_adder": {
                "expected": exp["max_adder_arm_vs_repointed"][1],
                "got": got_max,
                "match": abs(got_max - exp["max_adder_arm_vs_repointed"][1]) < 0.005,
            },
            "gcap_violations": {
                "expected": 0,
                "got": got_gcap,
                "match": got_gcap == 0,
            },
            "tail_model_gt200": {
                "expected": exp["repointed"]["tail_model"],
                "got": got_tail,
                "match": got_tail == exp["repointed"]["tail_model"],
            },
        }
        year_ok = all(c["match"] for c in checks.values())
        all_ok = all_ok and year_ok
        out["years"][str(year)] = {"checks": checks, "PASS": year_ok}

    arm_vs_keeper = _hash_table(args.arm, args.keeper)
    ctl_vs_keeper = _hash_table(args.control, args.keeper)
    arm_vs_ctl = _hash_table(args.arm, args.control)
    out["sidecar_bytes"] = {
        "arm_vs_keeper": arm_vs_keeper,
        "control_vs_keeper": ctl_vs_keeper,
        "arm_vs_control": arm_vs_ctl,
    }
    # (e): the armed member's NON-system sidecars must byte-match the keeper's.
    e_rows = {
        k: v for k, v in arm_vs_keeper.items() if not k.startswith("system_")
    }
    e_ok = all(v["identical"] for v in e_rows.values())
    out["gexact"] = {
        "a_to_d_pass": bool(all_ok),
        "e_dispatch_bytes_pass": bool(e_ok),
        "e_mismatches": sorted(k for k, v in e_rows.items() if not v["identical"]),
        "PASS": bool(all_ok and e_ok),
    }

    args.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"years": {y: v["PASS"] for y, v in out["years"].items()}, "gexact": out["gexact"]}, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
