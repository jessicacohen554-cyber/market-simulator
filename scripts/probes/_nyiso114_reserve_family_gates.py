"""nyiso-114 — score the pre-registered gates G1–G6 and predictions P1–P5.

Reads ONLY committed bundle artifacts (no re-solve). The instrument under test
is the new ``hourly/reserve_family_<year>.parquet`` sidecar; the run under test
is the zero-delta confirmation replay of the nyiso-113 keeper.

Gates and predictions are as pre-registered in
``results/calibration/PREREG-nyiso114-reserve-family-sidecar-2026-08-03.md``
§3–§4, written and pushed before either solve.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso114_reserve_family_gates.py
Writes: results/calibration/_nyiso114_reserve_family_gates.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results/calibration"
ARM = CAL / "nyiso114_lilocational_confirm"
KEEPER = CAL / "nyiso113_lilocational_B"
BASE_ATTRIB = CAL / "_nyiso114_baseattrib_2024"
OUT = CAL / "_nyiso114_reserve_family_gates.json"
YEARS = (2023, 2024, 2025)

# nyiso-113 §7's Zone-K headroom probe, stated ex ante: the hours in which
# li_30min_total's own requirement exceeds Zone-K thermal headroom.
P1_PREDICTED_2025_HOURS = [4193, 4194, 4195, 4217, 4218]


def _p1(path: Path) -> pd.DataFrame:
    """A bundle sidecar's P1 rows (the scored pass)."""
    df = pd.read_parquet(path)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def _system_pair(year: int, a: Path, b: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Two bundles' P1 system rows, aligned on (zone, hour)."""
    fa = _p1(a / "hourly" / f"system_{year}.parquet")
    fb = _p1(b / "hourly" / f"system_{year}.parquet")
    fa = fa.sort_values(["zone", "hour"]).reset_index(drop=True)
    fb = fb.sort_values(["zone", "hour"]).reset_index(drop=True)
    return fa, fb


def gate_g1() -> dict:
    """G1 — does the replay reproduce the committed keeper?

    Pre-registered as a PASS/FAIL that changes how every other result is
    LABELLED, not whether it is reported: a failing G1 means the numbers below
    are measured on a re-solve, never on the keeper itself.
    """
    per = {}
    for y in YEARS:
        a, k = _system_pair(y, ARM, KEEPER)
        dp = np.abs(a["price"].to_numpy() - k["price"].to_numpy())
        dr = np.abs(a["reserve_price"].to_numpy() - k["reserve_price"].to_numpy())
        per[str(y)] = {
            "max_abs_dprice": float(dp.max()),
            "max_abs_dreserve_price": float(dr.max()),
            "n_zone_hours": int(dp.size),
            "n_differing": int((dp > 1e-6).sum()),
            "share_differing": float((dp > 1e-6).mean()),
            "mean_abs_dprice_over_differing": (
                float(dp[dp > 1e-6].mean()) if (dp > 1e-6).any() else 0.0
            ),
            "mean_price_replay": float(a["price"].mean()),
            "mean_price_keeper": float(k["price"].mean()),
            "mean_price_pct_delta": float(
                100.0 * (a["price"].mean() - k["price"].mean()) / k["price"].mean()
            ),
            "pass": bool(dp.max() <= 1e-6 and dr.max() <= 1e-6),
        }
    return {"per_year": per, "pass": all(v["pass"] for v in per.values())}


def attribution() -> dict:
    """Is G1's miss caused by THIS session's diff, or by the code basis moving?

    The pre-registered kill K-A reverts the instrument if the sidecar changed a
    solved number. The discriminating experiment: re-solve one year at the
    session's BASE commit — the same code the confirmation replay ran MINUS this
    session's diff — against the same data root. Identical output there means
    the sidecar is not the cause and the divergence belongs to the 58 commits
    that landed on main between the keeper's solve and this session's base.
    """
    if not (BASE_ATTRIB / "hourly" / "system_2024.parquet").exists():
        return {"available": False}
    a, b = _system_pair(2024, ARM, BASE_ATTRIB)
    k = _p1(KEEPER / "hourly" / "system_2024.parquet")
    k = k.sort_values(["zone", "hour"]).reset_index(drop=True)
    d_sidecar = np.abs(a["price"].to_numpy() - b["price"].to_numpy())
    d_basis = np.abs(b["price"].to_numpy() - k["price"].to_numpy())
    return {
        "available": True,
        "year": 2024,
        "sidecar_vs_base_max_abs_dprice": float(d_sidecar.max()),
        "sidecar_vs_base_n_differing": int((d_sidecar > 1e-6).sum()),
        "base_vs_keeper_max_abs_dprice": float(d_basis.max()),
        "base_vs_keeper_n_differing": int((d_basis > 1e-6).sum()),
        "verdict": (
            "SIDECAR IS NOT THE CAUSE — base code reproduces the replay exactly; "
            "the keeper divergence is present WITHOUT this session's diff"
            if d_sidecar.max() <= 1e-9 and d_basis.max() > 1e-6
            else "INCONCLUSIVE — inspect both legs"
        ),
    }


def gates_g2_g3_g4() -> dict:
    """G2 well-formed · G3 the LP row identity · G4 the sum identity."""
    per = {}
    for y in YEARS:
        fam = _p1(ARM / "hourly" / f"reserve_family_{y}.parquet")
        n_fam = int(fam["family"].nunique())
        sysdf = _p1(ARM / "hourly" / f"system_{y}.parquet")
        one = sysdf[sysdf["zone"] == sysdf["zone"].iloc[0]].sort_values("hour")
        fam_sum = fam.groupby("hour")["dual"].sum().sort_index().to_numpy()
        rp = one["reserve_price"].to_numpy()
        # G3: held + shortfall >= requirement, tight exactly where the family
        # prices. Both sides are persisted columns, so this is checkable from
        # the bundle alone — which is the whole point of the held_mw column.
        slack = (
            fam["held_mw"].to_numpy()
            + fam["shortfall_mw"].to_numpy()
            - fam["requirement_mw"].to_numpy()
        )
        binds = fam["dual"].to_numpy() > 1e-9
        per[str(y)] = {
            "n_families": n_fam,
            "n_rows": int(len(fam)),
            "rows_expected": n_fam * 8760,
            "any_nan": bool(fam.isna().any().any()),
            "g2_pass": bool(len(fam) == n_fam * 8760 and not fam.isna().any().any()),
            "g3_min_row_slack_mw": float(slack.min()),
            "g3_max_slack_where_binding_mw": (
                float(np.abs(slack[binds]).max()) if binds.any() else 0.0
            ),
            "g3_pass": bool(
                slack.min() >= -1e-2
                and (not binds.any() or np.abs(slack[binds]).max() <= 1e-2)
            ),
            "g4_max_abs_sum_gap": float(np.abs(fam_sum - rp).max()),
            "g4_pass": bool(np.abs(fam_sum - rp).max() <= 1e-4),
            "n_hours_reserve_price_positive": int((rp > 1e-9).sum()),
        }
    return {
        "per_year": per,
        "g2_pass": all(v["g2_pass"] for v in per.values()),
        "g3_pass": all(v["g3_pass"] for v in per.values()),
        "g4_pass": all(v["g4_pass"] for v in per.values()),
    }


def per_family_binding() -> dict:
    """Which family bound, when — the thing no committed bundle could show."""
    out = {}
    for y in YEARS:
        fam = _p1(ARM / "hourly" / f"reserve_family_{y}.parquet")
        rows = {}
        for name, g in fam.groupby("family", observed=True):
            b = g[g["dual"] > 1e-9]
            rows[str(name)] = {
                "reserve_class": int(g["reserve_class"].iloc[0]),
                "requirement_min_mw": float(g["requirement_mw"].min()),
                "requirement_max_mw": float(g["requirement_mw"].max()),
                "n_hours_dual_positive": int(len(b)),
                "max_dual": float(g["dual"].max()),
                "n_hours_shortfall": int((g["shortfall_mw"] > 1e-6).sum()),
                "max_shortfall_mw": float(g["shortfall_mw"].max()),
                "min_headroom_to_requirement_mw": float(
                    (g["held_mw"] - g["requirement_mw"]).min()
                ),
                "binding_hours": sorted(int(h) for h in b["hour"]),
            }
        out[str(y)] = rows
    return out


def predictions(binding: dict) -> dict:
    """Score P1–P5 exactly as written in the pre-registration §4."""

    def li_hours(y, fam):
        return binding[str(y)].get(fam, {}).get("binding_hours", [])

    got_2025 = li_hours(2025, "li_30min_total")
    p1 = got_2025 == P1_PREDICTED_2025_HOURS
    p3 = all(not li_hours(y, "li_10min_total") for y in YEARS)
    p4 = not li_hours(2024, "li_30min_total") and not li_hours(2024, "li_10min_total")
    li_2023 = li_hours(2023, "li_30min_total") + li_hours(2023, "li_10min_total")
    p5 = len(li_2023) == 2
    # P2: every hour with a positive system reserve dual is attributable to at
    # least one named family (a hole would falsify the instrument itself).
    holes = {}
    for y in YEARS:
        fam = _p1(ARM / "hourly" / f"reserve_family_{y}.parquet")
        sysdf = _p1(ARM / "hourly" / f"system_{y}.parquet")
        one = sysdf[sysdf["zone"] == sysdf["zone"].iloc[0]].sort_values("hour")
        priced = set(np.flatnonzero(one["reserve_price"].to_numpy() > 1e-9).tolist())
        named = set(int(h) for h in fam.loc[fam["dual"] > 1e-9, "hour"].unique())
        holes[str(y)] = sorted(priced - named)
    p2 = all(not v for v in holes.values())
    return {
        "P1_2025_li30_binds_the_predicted_hours": {
            "predicted": P1_PREDICTED_2025_HOURS,
            "measured": got_2025,
            "verdict": "CONFIRMED (exact)" if p1 else "MISS",
        },
        "P2_every_priced_hour_attributable": {
            "unattributed_hours_by_year": holes,
            "verdict": "CONFIRMED" if p2 else "INSTRUMENT FALSIFIED",
        },
        "P3_li10_never_binds": {
            "measured_binding_hours": {
                str(y): li_hours(y, "li_10min_total") for y in YEARS
            },
            "verdict": "CONFIRMED" if p3 else "MISS",
        },
        "P4_no_li_family_binds_in_2024": {"verdict": "CONFIRMED" if p4 else "MISS"},
        "P5_li_binds_2_hours_in_2023": {
            "predicted_n": 2,
            "measured_n": len(li_2023),
            "measured_hours": li_2023,
            "verdict": "CONFIRMED" if p5 else "REFUTED",
        },
    }


def main() -> None:
    g1 = gate_g1()
    g234 = gates_g2_g3_g4()
    binding = per_family_binding()
    doc = {
        "probe": "nyiso-114 reserve-family sidecar gates",
        "arm_bundle": str(ARM.relative_to(REPO)),
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "years": list(YEARS),
        "G1_replay_fidelity": g1,
        "G1_attribution": attribution(),
        "G2_G3_G4": g234,
        "per_family_binding": binding,
        "predictions": predictions(binding),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str))

    print(f"G1 replay fidelity : {'PASS' if g1['pass'] else 'FAIL'}")
    for y, v in g1["per_year"].items():
        print(
            f"   {y}: max|Δprice| {v['max_abs_dprice']:.3e}  "
            f"differing {v['n_differing']}/{v['n_zone_hours']} "
            f"({100 * v['share_differing']:.2f}%)  mean LMP {v['mean_price_pct_delta']:+.4f}%"
        )
    att = doc["G1_attribution"]
    if att.get("available"):
        print(f"   attribution: {att['verdict']}")
        print(
            f"     sidecar-vs-base max|Δ| {att['sidecar_vs_base_max_abs_dprice']:.3e}"
            f" | base-vs-keeper max|Δ| {att['base_vs_keeper_max_abs_dprice']:.3f}"
        )
    print(
        f"G2 well-formed     : {'PASS' if g234['g2_pass'] else 'FAIL'}\n"
        f"G3 row identity    : {'PASS' if g234['g3_pass'] else 'FAIL'}\n"
        f"G4 sum identity    : {'PASS' if g234['g4_pass'] else 'FAIL'}"
    )
    print("\npredictions:")
    for k, v in doc["predictions"].items():
        print(f"   {k:<48} {v['verdict']}")
    print("\nper-family binding (hours with dual > 0):")
    for y, fams in binding.items():
        live = {k: v["n_hours_dual_positive"] for k, v in fams.items() if v["n_hours_dual_positive"]}
        dead = [k for k, v in fams.items() if not v["n_hours_dual_positive"]]
        print(f"   {y}: {live}")
        print(f"        never binds: {dead}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
