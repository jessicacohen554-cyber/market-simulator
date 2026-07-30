"""pjm-140 A/B scorer — `ramp_envelopes` (`ramp_limits` False -> True) on PJM.

Scores the two arms against
`results/calibration/PREREG-pjm140-ramp-envelopes-2026-07-30.md` §6 **in the
PREREG's own terms**, and adds the one measurement the PREREG could not
pre-specify: **how often the keeper's own dispatch actually crosses the measured
envelope**, which is what decides whether the rows can bind at all.

The seven pre-registered kills:

- **K1 inert** — arm B's dispatch differs from arm A's by < 0.1 % of class
  energy in EVERY class and EVERY year.
- **K2 C1** — any C1 band failure, or free-band count below 12/12.
- **K3 C3c** — BOTH bounds (the 0.5x lower floor and the upper bound).
- **K4 slack/dump** — ZERO of each, both arms, all years.
- **K5 control identity** — arm A reproduces `pjm137_ctheatrate_B` to
  0.000000000 MW over 166,440 class-hours per year.
- **K6 primary direction** — the DJF h04 -> h07 model price rise must INCREASE
  toward the measured +$15.28 / +$21.63 / +$35.45. Read from the COMMITTED W5
  probe (`_pjm139_winter_ramp.py --bundle <arm>`), not recomputed here, so the
  statistic is definitionally the one the FINDING quotes.
- **K7 pruning** — read from `_pjm140_ramp_coverage.py`'s committed JSON.

The added diagnosis (**D-ENV**, no LP): for every live ramp group, the share of
the 8,759 hour transitions in which arm A's OWN summed dispatch moves by more
than that group's envelope. This is the quantity the pjm-139 W7 pre-check was a
proxy for — and the proxy compared the model's **p99** 1-h move against the real
fleet's **p99**, while the derive writes each plant's **MAX** observed move, so
a model p99 can sit 1.5x above the actual p99 and still fall far below the
actual max. D-ENV measures the binding directly and settles the question the
proxy could not.

Usage::

    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm140_rampenv_ab.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2023, 2024, 2025)
HOURS = 8760

ARM_A = Path("results/calibration/pjm140_control_A")
ARM_B = Path("results/calibration/pjm140_rampenv_B")
IDENTITY_REF = Path("results/calibration/pjm137_ctheatrate_B")
COVERAGE = Path("results/probes/pjm140_ramp_coverage.json")
W5_A = Path("results/probes/pjm140_w5_control_A.json")
W5_B = Path("results/probes/pjm140_w5_rampenv_B.json")
OUT_PATH = Path("results/probes/pjm140_rampenv_ab.json")

#: PREREG §6 K1 — below this per-class energy delta the mechanism is INERT.
INERT_PCT = 0.1
#: FINDING-pjm139 §4.2 — PJM's own DJF h04 -> h07 measured MEC rise, $/MWh.
MEASURED_RISE = {"2023": 15.28, "2024": 21.63, "2025": 35.45}
#: The keeper's own model rise, same statistic, same probe.
KEEPER_RISE = {"2023": 3.93, "2024": 4.55, "2025": 6.51}


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


def _k1(year: int) -> dict:
    """K1 — per-class energy delta B vs A, as a share of A's own class energy."""
    a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
    rows = {}
    worst_name, worst_pct = "", 0.0
    for k in sorted(set(a) | set(b)):
        av, bv = a.get(k, 0.0), b.get(k, 0.0)
        pct = 100.0 * (bv - av) / abs(av) if av else (0.0 if bv == 0.0 else float("inf"))
        rows[k] = {
            "A_twh": round(av, 4),
            "B_twh": round(bv, 4),
            "delta_twh": round(bv - av, 4),
            "pct_of_own_class": round(pct, 4) if np.isfinite(pct) else None,
        }
        if np.isfinite(pct) and abs(pct) > abs(worst_pct):
            worst_name, worst_pct = k, pct
    tot_a = sum(a.values())
    return {
        "classes": rows,
        "total_A_twh": round(tot_a, 3),
        "total_B_twh": round(sum(b.values()), 3),
        "total_delta_twh": round(sum(b.values()) - tot_a, 4),
        "sum_abs_delta_twh": round(sum(abs(r["delta_twh"]) for r in rows.values()), 4),
        "worst_class": worst_name,
        "worst_pct_of_own_class": round(worst_pct, 4),
        # "INERT" here is the PREREG's literal test: EVERY class under 0.1 %.
        "inert_by_prereg_k1": bool(abs(worst_pct) < INERT_PCT),
    }


def _rubric(bundle: Path) -> dict:
    """The bundle's own determination and per-criterion verdicts."""
    path = bundle / "metrics.json"
    if not path.exists():
        return {"available": False}
    m = json.loads(path.read_text())
    crit = m.get("criteria", {})
    return {
        "available": True,
        "determination": m.get("determination"),
        "criteria": {
            k: (v.get("verdict") if isinstance(v, dict) else v)
            for k, v in crit.items()
        },
    }


def _w5(path: Path) -> dict:
    """K6 — the committed W5 DJF h04 -> h07 rise per year, or unavailable."""
    if not path.exists():
        return {"available": False, "reason": f"missing {path}"}
    payload = json.loads(path.read_text())
    out = {"available": True, "per_year": {}}
    for year in map(str, YEARS):
        w5 = payload["per_year"][year]["W5_ramp"]
        out["per_year"][year] = {
            "model_rise": w5["djf_morning_ramp_h04_to_h07"]["model_system_price"],
            "measured_rise": w5["djf_morning_ramp_h04_to_h07"]["measured_mec"],
            "model_trough_to_peak": w5["djf_trough_to_peak"]["model_system_price"],
            "djf_model_profile": w5["djf_hour_of_day"]["model_system_price"],
        }
    return out


def _k6(a: dict, b: dict) -> dict:
    """K6 — did the primary statistic move UP? (a FALL refutes the charter)."""
    if not (a.get("available") and b.get("available")):
        return {"available": False, "reason": "W5 payload missing for an arm"}
    per_year, worst = {}, None
    for year in map(str, YEARS):
        ra = a["per_year"][year]["model_rise"]
        rb = b["per_year"][year]["model_rise"]
        meas = MEASURED_RISE[year]
        per_year[year] = {
            "A_rise": round(ra, 3),
            "B_rise": round(rb, 3),
            "delta": round(rb - ra, 4),
            "measured_rise": meas,
            "A_pct_of_measured": round(100 * ra / meas, 1),
            "B_pct_of_measured": round(100 * rb / meas, 1),
            "closed_share_of_gap_pct": round(100 * (rb - ra) / (meas - ra), 2)
            if meas != ra
            else None,
            "direction": "UP" if rb > ra else ("DOWN" if rb < ra else "FLAT"),
        }
        if worst is None or (rb - ra) < worst:
            worst = rb - ra
    return {
        "available": True,
        "per_year": per_year,
        "min_delta": round(worst, 4),
        # K6 fires (delta REJECTED) when the primary FALLS in any year.
        "k6_pass": bool(worst >= 0.0),
    }


def _env_binding(bundle: Path, year: int, iso: str = "PJM") -> dict:
    """D-ENV — how often the arm's own dispatch would cross the envelope.

    Sums the bundle's per-unit ``dispatch/`` MW into the SAME (plant_code,
    CC/CT/ST bucket) groups the loader builds, diffs each group's hourly
    series, and counts transitions whose move exceeds that group's envelope.
    The envelope comes from the production loader, so the comparison is
    against exactly the bound the LP would impose.

    Reported per group and pooled. On a bundle without ``dispatch/`` (a
    committed slim bundle) it returns ``available: False`` rather than an
    imputed number.
    """
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.exists():
        return {"available": False, "reason": f"missing {path}"}

    import sys

    REPO = Path(__file__).resolve().parent.parent.parent
    for p in (str(REPO), str(REPO / "src")):
        if p not in sys.path:
            sys.path.insert(0, p)
    from market_sim.data.fleet.campd_bins import _RAMP_BUCKET_BY_GROUP

    # The loader's envelopes, keyed the same way, recovered from the coverage
    # audit CSV this probe's STEP-1 sibling wrote (it records the post-rebasis
    # MW and the prune decision for every group).
    aud_path = Path("results/probes") / f"pjm140_ramp_groups_{year}.csv"
    if not aud_path.exists():
        return {"available": False, "reason": f"missing {aud_path}"}
    aud = pd.read_csv(aud_path)
    live = aud[aud["live"].astype(bool)]
    env = {
        (int(r.plant_code), str(r.bucket)): (float(r.ru_mw), float(r.rd_mw))
        for r in live.itertuples(index=False)
    }

    frame = pd.read_parquet(path, columns=["plant_code", "klass", "hour", "mw"])
    # The loader buckets on the fleet's ``plant_group``, where every coal unit is
    # the single group ``COAL``; the dispatch parquet's ``klass`` splits that into
    # COAL_BIT / COAL_PRB / COAL_WC. Mapping ``klass`` through
    # ``_RAMP_BUCKET_BY_GROUP`` alone therefore silently DROPS every coal group —
    # 42 of the 194 live groups and 38.6 GW (31 % of live capacity), i.e. exactly
    # the class the winter-morning defect implicates. Collapse the coal variants
    # back onto the ``COAL`` key before mapping.
    klass = frame["klass"].astype(str)
    frame["bucket"] = (
        klass.where(~klass.str.startswith("COAL"), "COAL")
        .map(_RAMP_BUCKET_BY_GROUP)
        .fillna("")
    )
    frame = frame[(frame["plant_code"] > 0) & (frame["bucket"] != "")]
    grouped = (
        frame.groupby(["plant_code", "bucket", "hour"], observed=True)["mw"]
        .sum()
        .unstack("hour")
        .reindex(columns=range(HOURS))
        .fillna(0.0)
    )

    rows = []
    for key, series in grouped.iterrows():
        if key not in env:
            continue
        ru, rd = env[key]
        d = np.diff(series.to_numpy(float))
        n_up = int((d > ru + 1e-6).sum())
        n_dn = int((-d > rd + 1e-6).sum())
        rows.append(
            {
                "plant_code": int(key[0]),
                "bucket": str(key[1]),
                "ru_mw": ru,
                "rd_mw": rd,
                "max_up_mw": float(d.max()) if d.size else 0.0,
                "max_dn_mw": float(-d.min()) if d.size else 0.0,
                # The pjm-139 W7 pre-check's own numerator: the model's p99 1-h
                # up-move. Recording it against the envelope (which is the real
                # fleet's MAX, not its p99) is what exposes the proxy's gap.
                "p99_up_mw": float(np.quantile(d, 0.99)) if d.size else 0.0,
                "n_up_violations": n_up,
                "n_dn_violations": n_dn,
                "n_violations": n_up + n_dn,
                "excess_up_mwh": float(np.clip(d - ru, 0, None).sum()),
                "excess_dn_mwh": float(np.clip(-d - rd, 0, None).sum()),
            }
        )
    det = pd.DataFrame(rows)
    if det.empty:
        return {"available": False, "reason": "no live group matched dispatch"}
    n_trans = HOURS - 1
    # Disclose the match rate rather than reporting a share of an unstated
    # denominator: a live group absent from dispatch contributes no transitions.
    n_live = int(len(live))
    matched_cap = float(
        live[
            live.apply(
                lambda r: (int(r.plant_code), str(r.bucket))
                in set(zip(det["plant_code"], det["bucket"])),
                axis=1,
            )
        ]["cap_net_mw"].sum()
    )
    det.sort_values("n_violations", ascending=False).to_csv(
        Path("results/probes") / f"pjm140_env_binding_{year}.csv", index=False
    )
    return {
        "available": True,
        "n_groups": int(len(det)),
        "n_live_groups_in_loader": n_live,
        "matched_cap_mw": round(matched_cap, 1),
        "live_cap_mw": round(float(live["cap_net_mw"].sum()), 1),
        "n_transitions_per_group": n_trans,
        "n_group_transitions": int(len(det) * n_trans),
        "n_violating_group_transitions": int(det["n_violations"].sum()),
        "share_of_group_transitions_pct": round(
            100.0 * det["n_violations"].sum() / (len(det) * n_trans), 4
        ),
        "n_groups_never_violating": int((det["n_violations"] == 0).sum()),
        "n_groups_violating": int((det["n_violations"] > 0).sum()),
        "median_violations_per_group": float(det["n_violations"].median()),
        "p90_violations_per_group": float(det["n_violations"].quantile(0.90)),
        "max_violations_per_group": int(det["n_violations"].max()),
        "total_excess_energy_mwh": round(
            float(det["excess_up_mwh"].sum() + det["excess_dn_mwh"].sum()), 1
        ),
        # The proxy-vs-bound comparison the pjm-139 pre-check could not make.
        # W7 compared the model's p99 1-h move against the REAL FLEET's p99 and
        # found a 1.4-1.7x excess; the envelope is the real fleet's MAX. These
        # two rows put the model's max AND its p99 against that max directly, so
        # the ratio that actually decides binding is on the record.
        "median_max_up_over_envelope": round(
            float((det["max_up_mw"] / det["ru_mw"]).median()), 3
        ),
        "p90_max_up_over_envelope": round(
            float((det["max_up_mw"] / det["ru_mw"]).quantile(0.90)), 3
        ),
        "median_p99_up_over_envelope": round(
            float((det["p99_up_mw"] / det["ru_mw"]).median()), 3
        ),
        "p90_p99_up_over_envelope": round(
            float((det["p99_up_mw"] / det["ru_mw"]).quantile(0.90)), 3
        ),
        "top_groups": det.sort_values("n_violations", ascending=False)
        .head(10)
        .to_dict("records"),
    }


def score(year: int) -> dict:
    """Every per-year gate for one calendar year."""
    sa, da = _slack_dump(ARM_A, year)
    sb, db = _slack_dump(ARM_B, year)
    return {
        "K1_class_energy": _k1(year),
        "K4_slack_dump": {
            "A": {"slack_mwh": sa, "dump_mwh": da},
            "B": {"slack_mwh": sb, "dump_mwh": db},
            "pass": bool(sa == 0.0 and da == 0.0 and sb == 0.0 and db == 0.0),
        },
        "K5_arm_a_identity": _identity(year),
        "D_ENV_binding_arm_A": _env_binding(ARM_A, year),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)

    w5a, w5b = _w5(W5_A), _w5(W5_B)
    payload = {
        "arms": {"A": str(ARM_A), "B": str(ARM_B)},
        "identity_ref": str(IDENTITY_REF),
        "years": list(YEARS),
        "K6_primary": _k6(w5a, w5b),
        "K7_coverage": (
            json.loads(COVERAGE.read_text()) if COVERAGE.exists() else {"available": False}
        ),
        "rubric": {"A": _rubric(ARM_A), "B": _rubric(ARM_B)},
        "per_year": {str(y): score(y) for y in YEARS},
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))

    print("=" * 78)
    print("pjm-140 A/B — ramp_limits False -> True on the measured PJM envelope")
    print("=" * 78)
    k6 = payload["K6_primary"]
    if k6.get("available"):
        print("\nK6 PRIMARY — DJF h04 -> h07 model price rise ($/MWh):")
        for y, r in k6["per_year"].items():
            print(
                f"  {y}: A {r['A_rise']:+7.3f} -> B {r['B_rise']:+7.3f}  "
                f"delta {r['delta']:+7.4f}  {r['direction']:<4}  "
                f"(measured {r['measured_rise']:+.2f}; "
                f"{r['A_pct_of_measured']:.1f}% -> {r['B_pct_of_measured']:.1f}%)"
            )
        print(f"  K6 {'PASS' if k6['k6_pass'] else 'FAIL (primary FELL)'}")
    else:
        print(f"\nK6 unavailable: {k6.get('reason')}")

    for y in map(str, YEARS):
        row = payload["per_year"][y]
        k1, sd, ident = row["K1_class_energy"], row["K4_slack_dump"], row["K5_arm_a_identity"]
        env = row["D_ENV_binding_arm_A"]
        print(f"\n--- {y} ---")
        print(
            "  K5 arm A identity: "
            + (
                "BYTE-IDENTICAL"
                if ident.get("identical")
                else f"max |delta| {ident.get('max_abs_diff_mw')} MW over "
                f"{ident.get('n_class_hours')} class-hours"
            )
        )
        print(
            f"  K4 slack/dump: A {sd['A']['slack_mwh']:.0f}/{sd['A']['dump_mwh']:.0f}  "
            f"B {sd['B']['slack_mwh']:.0f}/{sd['B']['dump_mwh']:.0f}  "
            f"{'PASS' if sd['pass'] else 'FAIL'}"
        )
        print(
            f"  K1 worst class {k1['worst_class']} {k1['worst_pct_of_own_class']:+.4f} % "
            f"of own class; total {k1['total_A_twh']:.3f} -> {k1['total_B_twh']:.3f} TWh "
            f"({k1['total_delta_twh']:+.4f}); sum|delta| {k1['sum_abs_delta_twh']:.4f} TWh"
        )
        print(
            f"     PREREG K1 literal test (every class < {INERT_PCT} %): "
            f"{'INERT' if k1['inert_by_prereg_k1'] else 'not inert'}"
        )
        for k, r in sorted(
            k1["classes"].items(), key=lambda kv: -abs(kv[1]["delta_twh"])
        )[:6]:
            print(
                f"       {k:<12} {r['A_twh']:>10.4f} -> {r['B_twh']:>10.4f} TWh "
                f"({r['delta_twh']:+.4f}, {r['pct_of_own_class']:+.4f} %)"
            )
        if env.get("available"):
            print(
                f"  D-ENV arm A envelope crossings: "
                f"{env['n_violating_group_transitions']:,} of "
                f"{env['n_group_transitions']:,} group-transitions "
                f"({env['share_of_group_transitions_pct']:.4f} %); "
                f"{env['n_groups_violating']}/{env['n_groups']} groups ever cross; "
                f"median max-up/envelope {env['median_max_up_over_envelope']:.3f}, "
                f"median p99-up/envelope {env['median_p99_up_over_envelope']:.3f}"
            )
        else:
            print(f"  D-ENV unavailable: {env.get('reason')}")

    for arm in ("A", "B"):
        r = payload["rubric"][arm]
        if r.get("available"):
            print(
                f"\narm {arm} determination {r['determination']}: "
                + ", ".join(f"{k}={v}" for k, v in sorted(r["criteria"].items()))
            )

    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
