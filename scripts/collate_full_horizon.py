#!/usr/bin/env python
"""Collate the P-3A full-horizon per-ISO summaries into findings tables.

Reads every ``results/full-horizon/<iso>/full_horizon_summary.json`` produced by
``run_full_horizon.py`` and the cached run-dir parquets, then emits the markdown
tables the findings report needs:

  * feasibility (wall + peak RSS per ISO, and per ISO-year detail)
  * invariant matrix (ISO x I1-I14, with offending years)
  * F1/F2 de-firming trajectory (reserve margin + thermal MW to 2050)
  * scarcity trajectory incl. the #2064 slack>1 MW metric (computed here from
    the parquets, matching the driver-battery's definition), price-based hours
  * capacity / price / CO2 snapshots at 2026/2030/2040/2050

Pure post-processing: it never solves, tunes, or changes a threshold. Run it
incrementally — it collates whatever summaries exist so far.

Usage::

    python scripts/collate_full_horizon.py --root results/full-horizon \
        [--out results/full-horizon/_tables.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.model.dispatch import DispatchResult  # noqa: E402

ISO_ORDER = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
SNAPSHOT_YEARS = [2026, 2030, 2040, 2050]
INVARIANT_IDS = [f"I{i}" for i in range(1, 15)]


def _slack_hours(run_dir: Path) -> dict[int, int]:
    """Per-year count of hours with system slack > 1 MW (#2064 definition)."""
    out: dict[int, int] = {}
    for pq in sorted(run_dir.glob("year_*.parquet")):
        if pq.stem.endswith("_p1"):
            continue
        try:
            year = int(pq.stem.replace("year_", ""))
        except ValueError:
            continue
        try:
            res = DispatchResult.from_parquet(pq)
            slack_sys = np.asarray(res.slack, dtype=float).sum(axis=0)  # (T,)
            out[year] = int((slack_sys > 1.0).sum())
        except Exception:  # noqa: BLE001
            out[year] = -1
    return out


def load_summaries(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for iso in ISO_ORDER:
        p = root / iso.lower() / "full_horizon_summary.json"
        if p.exists():
            out[iso] = json.loads(p.read_text())
    return out


def _traj_by_year(summary: dict) -> dict[int, dict]:
    return {row["year"]: row for row in summary.get("trajectory", [])}


def _perf_by_year(summary: dict) -> dict[int, dict]:
    return {row["year"]: row for row in summary.get("per_year_perf", [])}


def fmt_feasibility(summaries: dict[str, dict]) -> str:
    lines = [
        "### Feasibility — wall time & peak RSS (per ISO)",
        "",
        "| ISO | years | status | total wall | median yr | max yr | global peak RSS | max yr peak RSS |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for iso, s in summaries.items():
        perf = s.get("per_year_perf", [])
        walls = [p["wall_s"] for p in perf]
        rss = [p["peak_rss_mb"] for p in perf]
        med = sorted(walls)[len(walls) // 2] if walls else 0
        status = "OK" if not s.get("error") and s.get("n_solved_years") else "ERROR"
        n = s.get("n_solved_years", 0)
        span = f"{n}/{s['end_year'] - s['start_year'] + 1}"
        lines.append(
            f"| {iso} | {span} | {status} | {s.get('total_wall_s', 0) / 60:.1f} min | "
            f"{med:.0f}s | {max(walls) if walls else 0:.0f}s | "
            f"{s.get('global_peak_rss_mb', 0) / 1024:.2f} GB | "
            f"{max(rss) / 1024 if rss else 0:.2f} GB |"
        )
    return "\n".join(lines)


def fmt_invariant_matrix(summaries: dict[str, dict]) -> str:
    lines = [
        "### Invariant matrix (I1-I14)",
        "",
        "| ISO | " + " | ".join(INVARIANT_IDS) + " |",
        "|---|" + "|".join(["---"] * len(INVARIANT_IDS)) + "|",
    ]
    detail_lines = ["", "**FAIL/WARN detail:**", ""]
    for iso, s in summaries.items():
        byid = {i["id"]: i for i in s.get("invariants", [])}
        cells = []
        for iid in INVARIANT_IDS:
            st = byid.get(iid, {}).get("status", "-")
            cells.append(
                {"PASS": "P", "FAIL": "**F**", "WARN": "W", "SKIP": "s"}.get(st, "-")
            )
        lines.append(f"| {iso} | " + " | ".join(cells) + " |")
        for iid in INVARIANT_IDS:
            it = byid.get(iid, {})
            if it.get("status") in ("FAIL", "WARN"):
                detail_lines.append(
                    f"- {iso} [{it['status']}] {iid} {it['name']}: {it['detail']}"
                )
    return "\n".join(lines + detail_lines)


def fmt_defirming(summaries: dict[str, dict]) -> str:
    lines = [
        "### F1/F2 de-firming — reserve margin & thermal MW trajectory",
        "",
        "Reserve margin (accredited firm / peak − 1) at snapshot years; last column"
        " = 2050−2026 change (negative ⇒ de-firming compounds).",
        "",
        "| ISO | " + " | ".join(f"RM {y}" for y in SNAPSHOT_YEARS) + " | ΔRM 26→50 |",
        "|---|" + "|".join(["---"] * (len(SNAPSHOT_YEARS) + 1)) + "|",
    ]
    for iso, s in summaries.items():
        t = _traj_by_year(s)
        cells = []
        rms = {}
        for y in SNAPSHOT_YEARS:
            rm = t.get(y, {}).get("reserve_margin")
            rms[y] = rm
            cells.append(f"{rm:.1%}" if isinstance(rm, (int, float)) else "-")
        d = None
        if isinstance(rms.get(2050), (int, float)) and isinstance(
            rms.get(2026), (int, float)
        ):
            d = rms[2050] - rms[2026]
        cells.append(f"{d:+.1%}" if d is not None else "-")
        lines.append(f"| {iso} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "Thermal MW at snapshot years (de-firming shows as falling thermal vs peak):",
        "",
        "| ISO | " + " | ".join(f"Th {y}" for y in SNAPSHOT_YEARS) + " | Peak 2050 |",
        "|---|" + "|".join(["---"] * (len(SNAPSHOT_YEARS) + 1)) + "|",
    ]
    for iso, s in summaries.items():
        t = _traj_by_year(s)
        cells = []
        for y in SNAPSHOT_YEARS:
            th = t.get(y, {}).get("thermal_mw")
            cells.append(f"{th / 1000:.1f} GW" if isinstance(th, (int, float)) else "-")
        pk = t.get(2050, {}).get("peak_demand_mw")
        cells.append(f"{pk / 1000:.1f} GW" if isinstance(pk, (int, float)) else "-")
        lines.append(f"| {iso} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fmt_scarcity(summaries: dict[str, dict], root: Path) -> str:
    lines = [
        "### Scarcity trajectory (#2064 watch) — slack>1 MW hours & price hours",
        "",
        "`slack_hrs` = hours with system slack > 1 MW (the exact #2064 metric, "
        "computed from parquets). `p≥500`/`p≥2000` = hours with load-weighted "
        "system price at/above threshold. Reported for all snapshot years plus "
        "any year with a scarcity spike.",
        "",
    ]
    for iso, s in summaries.items():
        run_dir = Path(s["run_dir"]) if s.get("run_dir") else None
        slack = _slack_hours(run_dir) if run_dir and run_dir.exists() else {}
        t = _traj_by_year(s)
        years = sorted(t)
        lines.append(f"**{iso}**")
        lines.append("")
        lines.append(
            "| year | slack_hrs | p≥500 | p≥2000 | max $ | RM | retire GW | co2 Mt |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for y in years:
            r = t[y]
            rm = r.get("reserve_margin")
            lines.append(
                f"| {y} | {slack.get(y, '-')} | {r.get('hours_ge_500', '-')} | "
                f"{r.get('hours_ge_2000', '-')} | {r.get('max_hourly_price', '-')} | "
                f"{rm:.1%} | {r.get('retire_mw', 0) / 1000:.2f} | "
                f"{r.get('co2_mt', '-')} |"
                if isinstance(rm, (int, float))
                else f"| {y} | {slack.get(y, '-')} | {r.get('hours_ge_500', '-')} | "
                f"{r.get('hours_ge_2000', '-')} | {r.get('max_hourly_price', '-')} | - | "
                f"{r.get('retire_mw', 0) / 1000:.2f} | {r.get('co2_mt', '-')} |"
            )
        # Monotonicity note on slack hours.
        sv = [slack.get(y, 0) for y in years if slack.get(y, -1) >= 0]
        if sv:
            mono = all(a <= b for a, b in zip(sv, sv[1:]))
            lines.append("")
            lines.append(
                f"_slack_hrs monotone non-decreasing over horizon: {mono}; "
                f"range [{min(sv)}, {max(sv)}], total {sum(sv)}._"
            )
        lines.append("")
    return "\n".join(lines)


def fmt_trajectory(summaries: dict[str, dict]) -> str:
    lines = [
        "### Capacity / price / CO2 snapshots",
        "",
        "| ISO | year | LW $ | CO2 Mt | thermal GW | VRE GW | storage GW | total GW | cum build GW |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for iso, s in summaries.items():
        t = _traj_by_year(s)
        cum_build = 0.0
        # cumulative builds up to each snapshot
        build_to_year: dict[int, float] = {}
        for y in sorted(t):
            r = t[y]
            cum_build += (
                r.get("builds_thermal_mw", 0)
                + r.get("builds_renew_mw", 0)
                + r.get("builds_storage_mw", 0)
            )
            build_to_year[y] = cum_build
        for y in SNAPSHOT_YEARS:
            if y not in t:
                continue
            r = t[y]
            co2 = r.get("co2_mt")
            lines.append(
                f"| {iso} | {y} | {r.get('lw_price', '-')} | "
                f"{co2 if co2 is not None else '-'} | {r.get('thermal_mw', 0) / 1000:.1f} | "
                f"{r.get('vre_mw', 0) / 1000:.1f} | {r.get('storage_mw', 0) / 1000:.1f} | "
                f"{r.get('total_cap_mw', 0) / 1000:.1f} | {build_to_year.get(y, 0) / 1000:.1f} |"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("results/full-horizon"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    summaries = load_summaries(args.root)
    if not summaries:
        print("no summaries found under", args.root)
        return 1

    blocks = [
        f"_Collated from {len(summaries)} ISO summaries: {', '.join(summaries)}._",
        "",
        fmt_feasibility(summaries),
        "",
        fmt_invariant_matrix(summaries),
        "",
        fmt_defirming(summaries),
        "",
        fmt_scarcity(summaries, args.root),
        "",
        fmt_trajectory(summaries),
    ]
    text = "\n".join(blocks) + "\n"
    if args.out:
        args.out.write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
