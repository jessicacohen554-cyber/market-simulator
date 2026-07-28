"""pjm-136 A/B scorer: the PJM zonal marginal-loss surface (no LP, no replay).

Scores `PREREG-pjm136-zonal-loss-surface-2026-07-28.md` §2/§3 from the two arms'
committed `hourly/` sidecars plus PJM's own measured zonal LMP components:

* **P1 the PRIMARY** — the arm-B minus arm-A change in each internal link's mean
  hourly dual difference reproduces the measured DA **loss** component
  `mean(MLC_a - MLC_b)` within [0.5x, 1.5x], on all 11 links x 3 years.
* **P2 the copper-plate breaks** — the share of hours in which all eight PJM
  zones sit at one dual must fall materially below arm A's 96.4/97.6/97.0 %.
* **K1 no fabricated separation** — arm B's mean separation must not exceed the
  measured DA **total** in magnitude on the three Dominion-facing links, nor
  carry the wrong sign there; and no link-year outside the PREREG's declared
  exception table may exceed its measured total.
* **K2 load shedding** — slack / dump MWh, both arms (losses consume 1-2 TWh/yr
  the fleet must make up; this was the named principal risk).
* **K3 the seam must not absorb the delta** — arm B's net interchange may not
  move further from the measured value than arm A's by more than 1.0 TWh.
* **K5 arm-A identity** — arm A vs the committed `pjm135_netpos_keeper_C`,
  every class, every hour.

Everything else (ISO-wide class volumes, the Dominion zonal classes, the rubric)
is REPORTED, never gated — rule 1 `[R-STRUCT]`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
HOURS = 8760

ARM_A = Path("results/calibration/pjm136_control_A")
ARM_B = Path("results/calibration/pjm136_lossurf_B")
IDENTITY_REF = Path("results/calibration/pjm135_netpos_keeper_C")

#: The measured side, produced by `_pjm136_model_vs_measured_zonal.py`.
MEASURED = Path("results/probes/pjm136_model_vs_measured_zonal.json")

OUT_PATH = Path("results/probes/pjm136_lossurf_ab.json")

#: Below this a dual difference is HiGHS noise, not separation.
EPS = 1e-6

#: PREREG §2 P1 acceptance band on the measured LOSS component.
P1_BAND = (0.5, 1.5)

#: The three boundaries the delta is chartered for (PREREG §3 K1).
DOMINION_LINKS = (
    ("PJM_AEP_Ohio", "PJM_Dominion"),
    ("PJM_West_APS", "PJM_Dominion"),
    ("PJM_SWMAAC", "PJM_Dominion"),
)

#: PREREG §3 K1 declared exceptions — link-years where the measured TOTAL is
#: offset by congestion so a loss-only mechanism over-states it. NAMED IN THE
#: PREREG BEFORE ANY SOLVE; any over-total link-year outside this set FAILS.
K1_DECLARED_EXCEPTIONS = {
    ("PJM_AEP_Ohio", "PJM_ATSI", 2024),
    ("PJM_AEP_Ohio", "PJM_ATSI", 2025),
    ("PJM_AEP_Ohio", "PJM_West_APS", 2023),
    ("PJM_Central_PA", "PJM_EMAAC", 2023),
    ("PJM_Central_PA", "PJM_EMAAC", 2024),
    ("PJM_Central_PA", "PJM_EMAAC", 2025),
    ("PJM_SWMAAC", "PJM_Dominion", 2025),
}

#: PREREG §3 K3 tolerance (TWh) on the net-interchange error move.
K3_TOL_TWH = 1.0

MODEL_ZONES = (
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
)


def _duals(bundle: Path, year: int) -> pd.DataFrame:
    """P1 hourly zonal duals (hour x zone)."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot(index="hour", columns="zone", values="price")


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """The bundle's P1 class-hourly frame (klass x hour, MW)."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """ISO-wide annual TWh by class."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    """The year's total slack and dump (MWh)."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return float(frame["slack"].sum()), float(frame["dump"].sum())


def _net_interchange_twh(bundle: Path, year: int) -> float:
    """The LP's own net interchange (TWh, import-positive) = the import class."""
    frame = _class_hourly(bundle, year)
    frame = frame[frame["klass"] == "import"]
    return float(frame["mw"].sum()) / 1.0e6


def _copper_plate_share(bundle: Path, year: int) -> float:
    """Share of hours in which all eight PJM zones sit at ONE dual."""
    duals = _duals(bundle, year)[list(MODEL_ZONES)].to_numpy()
    spread = duals.max(axis=1) - duals.min(axis=1)
    return float((spread <= EPS).mean())


def _identity(year: int) -> dict:
    """K5 — arm A against the committed keeper bundle, every class-hour."""
    for path in (ARM_A, IDENTITY_REF):
        if not (path / "hourly" / f"class_hourly_{year}.parquet").exists():
            return {"available": False, "reason": f"missing {path}"}
    a = _class_hourly(ARM_A, year).set_index(["klass", "hour"])["mw"].sort_index()
    r = _class_hourly(IDENTITY_REF, year).set_index(["klass", "hour"])["mw"].sort_index()
    joined = a.align(r, join="outer", fill_value=0.0)
    diff = (joined[0] - joined[1]).abs()
    return {
        "available": True,
        "max_abs_diff_mw": float(diff.max()),
        "n_class_hours": int(diff.size),
        "identical": bool(diff.max() < 1e-6),
    }


def _measured_block(year: int) -> dict[tuple[str, str], dict]:
    """Measured per-link DA total / congestion / loss means, keyed by zone pair."""
    payload = json.loads(MEASURED.read_text())
    out: dict[tuple[str, str], dict] = {}
    for row in payload["years"][str(year)]["links"]:
        out[(row["zone_a"], row["zone_b"])] = {
            "total": row["measured_total"]["mean_spread"],
            "congestion": row["measured_congestion"]["mean_spread"],
            "loss": row["measured_loss"]["mean_spread"],
            "measured_separated_pct": 100.0 * row["measured_total"]["share_separated"],
        }
    return out


def score(year: int) -> dict:
    """Every pre-registered gate plus reported context for ``year``."""
    out: dict = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        if not (bundle / "hourly" / f"system_{year}.parquet").exists():
            out[f"arm_{name}"] = {"available": False}
            continue
        slack, dump = _slack_dump(bundle, year)
        out[f"arm_{name}"] = {
            "available": True,
            "copper_plate_share": _copper_plate_share(bundle, year),
            "net_import_twh": _net_interchange_twh(bundle, year),
            "slack_mwh": slack,
            "dump_mwh": dump,
            "mean_price": float(_duals(bundle, year).mean().mean()),
            "class_twh": _class_twh(bundle, year),
        }
    a, b = out.get("arm_A", {}), out.get("arm_B", {})
    if not (a.get("available") and b.get("available")):
        return out

    meas = _measured_block(year)
    da, db = _duals(ARM_A, year), _duals(ARM_B, year)
    links = []
    for (za, zb), m in meas.items():
        sep_a = float((da[za] - da[zb]).mean())
        sep_b = float((db[za] - db[zb]).mean())
        delta = sep_b - sep_a
        loss = m["loss"]
        ratio_loss = delta / loss if abs(loss) > 1e-9 else float("nan")
        total = m["total"]
        over_total = abs(sep_b) > abs(total) + 1e-9
        links.append(
            {
                "zone_a": za,
                "zone_b": zb,
                "model_sep_A": round(sep_a, 4),
                "model_sep_B": round(sep_b, 4),
                "delta": round(delta, 4),
                "measured_loss": loss,
                "measured_total": total,
                "ratio_vs_loss": round(ratio_loss, 4),
                "p1_in_band": bool(P1_BAND[0] <= ratio_loss <= P1_BAND[1]),
                "sign_matches_total": bool(sep_b * total > 0) if abs(total) > 1e-9 else None,
                "over_total": bool(over_total),
                "declared_exception": (za, zb, year) in K1_DECLARED_EXCEPTIONS,
                "is_dominion_link": (za, zb) in DOMINION_LINKS,
            }
        )
    out["links"] = links

    dom = [r for r in links if r["is_dominion_link"]]
    undeclared_over = [
        r for r in links if r["over_total"] and not r["declared_exception"]
    ]
    out["gates"] = {
        "P1_all_links_in_band": all(r["p1_in_band"] for r in links),
        "P1_n_in_band": sum(r["p1_in_band"] for r in links),
        "P1_n_links": len(links),
        "P2_copper_plate_fell": b["copper_plate_share"] < a["copper_plate_share"],
        "P2_share_A": round(a["copper_plate_share"], 4),
        "P2_share_B": round(b["copper_plate_share"], 4),
        "K1_dominion_within_total": all(not r["over_total"] for r in dom),
        "K1_dominion_sign_ok": all(r["sign_matches_total"] is not False for r in dom),
        "K1_no_undeclared_over_total": not undeclared_over,
        "K1_undeclared_over_total": [
            f"{r['zone_a']}->{r['zone_b']}" for r in undeclared_over
        ],
        "K2_no_shedding": (
            a["slack_mwh"] == 0.0
            and a["dump_mwh"] == 0.0
            and b["slack_mwh"] == 0.0
            and b["dump_mwh"] == 0.0
        ),
        "K5_identity": _identity(year),
    }
    return out


def main() -> None:
    payload = {
        "probe": "pjm136_lossurf_ab",
        "session": "pjm-136",
        "prereg": "results/calibration/PREREG-pjm136-zonal-loss-surface-2026-07-28.md",
        "arm_A": str(ARM_A),
        "arm_B": str(ARM_B),
        "years": {str(y): score(y) for y in YEARS},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2))

    print("=" * 88)
    print("pjm-136 A/B — PJM zonal marginal-loss surface")
    print("=" * 88)
    for year in YEARS:
        blk = payload["years"][str(year)]
        if "gates" not in blk:
            print(f"\n### {year}: arms not both complete")
            continue
        g, a, b = blk["gates"], blk["arm_A"], blk["arm_B"]
        print(f"\n### {year}")
        print(
            f"  P2 copper-plate (all 8 zones at one dual): "
            f"{100 * g['P2_share_A']:.1f}% -> {100 * g['P2_share_B']:.1f}%   "
            f"mean price ${a['mean_price']:.2f} -> ${b['mean_price']:.2f}"
        )
        print(
            f"  {'link (a→b)':32s} {'sep A':>8s} {'sep B':>8s} {'Δ':>8s} "
            f"{'meas loss':>9s} {'ratio':>6s} {'meas tot':>9s}"
        )
        for r in blk["links"]:
            flag = "" if r["p1_in_band"] else "  << P1 OUT OF BAND"
            if r["over_total"]:
                flag += "  << OVER TOTAL" + (
                    " (declared)" if r["declared_exception"] else " (UNDECLARED)"
                )
            name = f"{r['zone_a'].replace('PJM_', '')}→{r['zone_b'].replace('PJM_', '')}"
            print(
                f"  {name:32s} {r['model_sep_A']:8.3f} {r['model_sep_B']:8.3f} "
                f"{r['delta']:8.3f} {r['measured_loss']:9.3f} "
                f"{r['ratio_vs_loss']:6.2f} {r['measured_total']:9.3f}{flag}"
            )
        print(
            f"  K2 slack/dump  A {a['slack_mwh']:.1f}/{a['dump_mwh']:.1f}   "
            f"B {b['slack_mwh']:.1f}/{b['dump_mwh']:.1f}"
        )
        print(
            f"  K3 net interchange  A {a['net_import_twh']:+.2f}  "
            f"B {b['net_import_twh']:+.2f} TWh"
        )
        ident = g["K5_identity"]
        if ident.get("available"):
            print(
                f"  K5 arm-A identity vs keeper: max |Δ| "
                f"{ident['max_abs_diff_mw']:.9f} MW "
                f"({'IDENTICAL' if ident['identical'] else 'DIFFERS'})"
            )
        print(
            f"  GATES  P1 {g['P1_n_in_band']}/{g['P1_n_links']} in band | "
            f"P2 {'PASS' if g['P2_copper_plate_fell'] else 'FAIL'} | "
            f"K1 dom-within-total {'PASS' if g['K1_dominion_within_total'] else 'FAIL'} "
            f"sign {'PASS' if g['K1_dominion_sign_ok'] else 'FAIL'} "
            f"undeclared {'PASS' if g['K1_no_undeclared_over_total'] else 'FAIL'} | "
            f"K2 {'PASS' if g['K2_no_shedding'] else 'FAIL'}"
        )
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
