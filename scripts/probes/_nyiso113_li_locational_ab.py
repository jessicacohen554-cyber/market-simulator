"""nyiso-113 A/B — score the `nyiso_li_locational_reserve` arm against its
pre-registered construction (K1–K6) and kill (P1–P5) gates.

Arms (`PREREG-nyiso113-li-locational-reserve-2026-08-02.md`):

* **A control** — zero delta on the nyiso-112 keeper recipe, solved at this HEAD.
* **B** — the single delta `nyiso_li_locational_reserve=true`, adding the
  published Long Island (Zone K) ladder: `li_10min_total` 120 MW all hours
  (class 1) and `li_30min_total` 270 MW off-peak / 540 MW on-peak (class 0),
  both at the published $25/MW ASM §6.8 value.

Every gate is evaluated from the committed bundles alone — no re-solve, no
benchmark refit. K3 is the decisive one: the LI families are Zone-K-scoped, so
a binding family MUST show a Long-Island reserve dual above the non-LI zones'.
If the cross-zone spread stays 0.0 the arm is **INERT** by the pre-registration's
own rule and is recorded as such, not promoted.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso113_li_locational_ab.py
Writes: results/calibration/_nyiso113_li_locational_ab.json
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
A = REPO / "results/calibration/nyiso113_control_A"
B = REPO / "results/calibration/nyiso113_lilocational_B"
KEEPER = REPO / "results/calibration/nyiso112_combined_D"
OUT = REPO / "results/calibration/_nyiso113_li_locational_ab.json"
YEARS = (2023, 2024, 2025)
LI = "Long_Island"


def cfg(bundle: Path) -> dict:
    """A bundle's ScenarioConfig."""
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def k1_single_delta() -> dict:
    """K1 — arms A and B differ in exactly one ScenarioConfig field."""
    ca, cb = cfg(A), cfg(B)
    keys = set(ca) | set(cb)
    diff = {k: [ca.get(k, "<absent>"), cb.get(k, "<absent>")] for k in sorted(keys) if ca.get(k) != cb.get(k)}
    return {
        "n_deltas": len(diff),
        "deltas": diff,
        "verdict": "PASS"
        if diff == {"nyiso_li_locational_reserve": [False, True]}
        else "FAIL",
    }


def k2_control_integrity() -> dict:
    """K2 — arm A reproduces the committed keeper on every class-hour."""
    import pandas as pd  # noqa: PLC0415

    out = {}
    worst = 0.0
    for y in YEARS:
        a = pd.read_parquet(A / f"hourly/class_hourly_{y}.parquet")
        k = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        j = a.merge(k, on=["year", "pass", "klass", "hour"], suffixes=("_a", "_k"))
        d = (j.mw_a - j.mw_k).abs()
        out[y] = {
            "rows_compared": int(len(j)),
            "max_abs_class_hour_delta_mw": round(float(d.max()), 9),
            "sum_abs_delta_mwh": round(float(d.sum()), 3),
        }
        worst = max(worst, float(d.max()))
    out["worst_max_abs_delta_mw"] = round(worst, 9)
    # The keeper was solved at an earlier HEAD; a strictly-zero reproduction is
    # ideal, but the gate is that any drift is small enough not to confound a
    # single-delta attribution. Report rather than silently absorb.
    out["verdict"] = "PASS (byte-identical)" if worst == 0.0 else f"REPORTED drift {worst:.6f} MW"
    return out


def reserve_spread(bundle: Path, year: int):
    """Per-hour (max-min) cross-zone reserve dual and the LI-vs-rest excess."""
    import pandas as pd  # noqa: PLC0415

    d = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    piv = d.pivot_table(index="hour", columns="zone", values="reserve_price")
    non_li = [z for z in piv.columns if z != LI]
    li_excess = piv[LI] - piv[non_li].max(axis=1)
    return piv, (piv.max(axis=1) - piv.min(axis=1)), li_excess


def k3_liveness_k4_scoping() -> dict:
    """K3 — do the LI families bind? K4 — is any effect Zone-K-scoped?"""
    out = {}
    for y in YEARS:
        pa, sa, ea = reserve_spread(A, y)
        pb, sb, eb = reserve_spread(B, y)
        # Non-LI zones must be untouched (K4): compare A vs B on those columns.
        non_li = [z for z in pb.columns if z != LI]
        non_li_delta = float((pb[non_li] - pa[non_li]).abs().to_numpy().max())
        out[y] = {
            "control_hours_reserve_dual_positive": int((pa.max(axis=1) > 0).sum()),
            "arm_hours_reserve_dual_positive": int((pb.max(axis=1) > 0).sum()),
            "control_max_cross_zone_spread": round(float(sa.max()), 6),
            "arm_max_cross_zone_spread": round(float(sb.max()), 6),
            "arm_hours_LI_dual_above_rest": int((eb > 1e-6).sum()),
            "arm_max_LI_excess_per_mw": round(float(eb.max()), 4),
            "arm_sum_LI_excess": round(float(eb[eb > 0].sum()), 3),
            "k4_max_non_LI_reserve_dual_delta": round(non_li_delta, 9),
        }
    live = any(out[y]["arm_hours_LI_dual_above_rest"] > 0 for y in YEARS)
    scoped = all(out[y]["k4_max_non_LI_reserve_dual_delta"] <= 1e-6 for y in YEARS)
    out["K3_verdict"] = "PASS (families bind)" if live else "INERT (no LI dual in any hour)"
    out["K4_verdict"] = "PASS (Zone-K scoped)" if scoped else "FAIL (non-LI reserve duals moved)"
    return out


def price_and_feasibility() -> dict:
    """C3c-relevant LI tail, plus P3 feasibility, per arm."""
    import pandas as pd  # noqa: PLC0415

    measured = {2023: 10, 2024: 12, 2025: 42}
    out = {}
    for y in YEARS:
        row = {"measured_h300": measured[y]}
        for tag, bundle in (("control", A), ("arm", B)):
            d = pd.read_parquet(bundle / f"hourly/system_{y}.parquet")
            d = d[d["pass"] == "P1"]
            li = d[d.zone == LI]
            row[tag] = {
                "li_h300": int((li.price > 300).sum()),
                "li_h250": int((li.price > 250).sum()),
                "li_max": round(float(li.price.max()), 2),
                "slack_total": round(float(d.slack.sum()), 6),
                "dump_total": round(float(d.dump.sum()), 6),
                "mean_price_all_zones": round(float(d.price.mean()), 4),
            }
        out[y] = row
    return out


def metrics_gates() -> dict:
    """C3a / C1 / C7 / C8 verdicts as each bundle's own scorer recorded them."""
    out = {}
    for tag, bundle in (("control", A), ("arm", B)):
        p = bundle / "metrics.json"
        if not p.exists():  # metrics are written by the scoring pass, not the replay
            out[tag] = "<metrics.json absent>"
            continue
        m = json.loads(p.read_text())
        out[tag] = m
    return out


def main() -> None:
    result = {
        "probe": "nyiso-113 nyiso_li_locational_reserve A/B",
        "prereg": "PREREG-nyiso113-li-locational-reserve-2026-08-02.md",
        "arm_A": str(A.relative_to(REPO)),
        "arm_B": str(B.relative_to(REPO)),
        "K1_single_delta": k1_single_delta(),
        "K2_control_integrity": k2_control_integrity(),
        "K3_K4_liveness_scoping": k3_liveness_k4_scoping(),
        "price_and_feasibility": price_and_feasibility(),
    }
    OUT.write_text(json.dumps(result, indent=2, default=str))

    k1 = result["K1_single_delta"]
    print(f"K1 single delta      : {k1['verdict']}  ({k1['n_deltas']} delta(s)) {list(k1['deltas'])}")
    k2 = result["K2_control_integrity"]
    print(f"K2 control integrity : {k2['verdict']}")
    for y in YEARS:
        print(f"     {y}: max |delta| {k2[y]['max_abs_class_hour_delta_mw']} MW over {k2[y]['rows_compared']} class-hours")
    k34 = result["K3_K4_liveness_scoping"]
    print(f"K3 liveness          : {k34['K3_verdict']}")
    print(f"K4 scoping           : {k34['K4_verdict']}")
    for y in YEARS:
        b = k34[y]
        print(
            f"     {y}: LI dual > rest in {b['arm_hours_LI_dual_above_rest']} h "
            f"(max excess {b['arm_max_LI_excess_per_mw']}); reserve-dual hours "
            f"{b['control_hours_reserve_dual_positive']} -> {b['arm_hours_reserve_dual_positive']}; "
            f"non-LI dual delta {b['k4_max_non_LI_reserve_dual_delta']}"
        )
    print("\nLI price tail & feasibility:")
    for y in YEARS:
        r = result["price_and_feasibility"][y]
        c, a = r["control"], r["arm"]
        print(
            f"  {y} (measured >$300 = {r['measured_h300']}): "
            f">300 {c['li_h300']} -> {a['li_h300']} | >250 {c['li_h250']} -> {a['li_h250']} | "
            f"max {c['li_max']} -> {a['li_max']} | slack {c['slack_total']}/{a['slack_total']} "
            f"dump {c['dump_total']}/{a['dump_total']}"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
