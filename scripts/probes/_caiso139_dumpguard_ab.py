"""caiso-139 A/B gate scorer: `dump_cost_full_offer_domain` vs same-HEAD control.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-caiso139-dump-cost-offer-domain-2026-07-29.md``
from the two solved bundles (arm A = the caiso-138 keeper recipe, arm B = + the
single flag) plus the committed measured intertie-hub validation source. No
solve, and no gate that is not in the prereg.

Gates, verbatim from the prereg §2:

* **P1** dump → 0 at BOTH WECC pseudo-nodes, all three years (≤ 0.001 TWh,
  0 dump hours). Kill if missed.
* **P2** CA demand-weighted annual LMP move: 2025 ≤ +$0.00, 2024 ≤ +$0.30;
  point prediction +$0.0000 both, and max CA per-zone-hour |Δprice| = 0.0000
  (±$0.02 degeneracy tolerance). Kill if missed.
* **P3** rubric identical to arm A (fail set {C3a-2025, C3c}, NOT-YET).
* **P4** 2023 null control: arm B's 2023 byte-identical to arm A's on prices
  and dumps. Kill if missed.
* **P5** (reported, not gated) node print in the former dump hours vs the
  measured PALOVRDE / MALIN hub in the SAME hours, and the tranche energy
  withdrawn at each node.

Also checks **control integrity**: arm A against the committed keeper bundle.

Usage::

    PYTHONPATH=.:src:scripts:scripts/probes .venv/bin/python \
        scripts/probes/_caiso139_dumpguard_ab.py \
        --control results/calibration/caiso139_control_A \
        --arm results/calibration/caiso139_dumpguard_B \
        --keeper results/calibration/caiso138_envclip_B
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

YEARS = (2023, 2024, 2025)
WECC_ZONES = ("WECC_PNW", "WECC_DSW")
HUB_OF = {"WECC_PNW": "MALIN", "WECC_DSW": "PALOVRDE"}
HUB_LMP = REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"

# Pre-registered thresholds (PREREG-caiso139 §2). Frozen with the prereg.
P1_MAX_RESIDUAL_TWH = 0.001
P2_E1_CEILING = 0.00  # 2025
P2_E2_CEILING = 0.30  # 2024
P2_DEGENERACY_TOL = 0.02


def _system(bundle: Path, year: int) -> pd.DataFrame:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return s[s["pass"] == "P1"].sort_values(["zone", "hour"])


def _ca_lambda(sysf: pd.DataFrame) -> np.ndarray:
    """CA demand-weighted hourly λ (WECC seam zones excluded).

    The caiso-125 ``ca_lambda`` definition, inlined so this scorer depends only
    on the committed sidecars.
    """
    ca = sysf[~sysf["zone"].str.startswith("WECC")]
    num = (ca["price"] * ca["demand"]).groupby(ca["hour"]).sum()
    den = ca["demand"].groupby(ca["hour"]).sum()
    return (num / den).sort_index().to_numpy(dtype=float)


def _ca_price_matrix(sysf: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    ca = sysf[~sysf["zone"].str.startswith("WECC")]
    piv = ca.pivot_table(index="hour", columns="zone", values="price")
    return list(piv.columns), piv.to_numpy(dtype=float)


def _measured_hub(year: int, hub: str) -> np.ndarray:
    h = pd.read_parquet(HUB_LMP)
    h = h[(h["year"] == year) & (h["hub"] == hub)]
    return h.set_index("hour")["price"].sort_index().to_numpy(dtype=float)


def _unit_hourly(bundle: Path, year: int) -> pd.DataFrame:
    f = bundle / "hourly" / f"unit_hourly_{year}.parquet"
    if not f.exists():
        return pd.DataFrame()
    u = pd.read_parquet(
        f,
        columns=["unit_id", "pass", "zone", "hour", "mw"],
        filters=[("zone", "in", list(WECC_ZONES))],
    )
    return u[u["pass"] == "P1"]


def gate_p1(control: Path, arm: Path) -> bool:
    print("=" * 96)
    print("P1 — dump → 0 at both WECC pseudo-nodes, all three years (KILL GATE)")
    print("=" * 96)
    ok = True
    for year in YEARS:
        a, b = _system(control, year), _system(arm, year)
        for zone in WECC_ZONES:
            da = a[a["zone"] == zone]["dump"].to_numpy()
            db = b[b["zone"] == zone]["dump"].to_numpy()
            twh_b = float(db.sum() / 1e6)
            hit = twh_b <= P1_MAX_RESIDUAL_TWH and int((db > 1e-6).sum()) == 0
            ok &= hit
            print(
                f"  {year} {zone:9s}: A {da.sum() / 1e6:.4f} TWh / "
                f"{int((da > 1e-6).sum()):4d} h  →  B {twh_b:.4f} TWh / "
                f"{int((db > 1e-6).sum()):4d} h   {'PASS' if hit else 'FAIL'}"
            )
    print(f"\n  P1: {'PASS' if ok else 'FAIL'}")
    return ok


def gate_p2(control: Path, arm: Path) -> bool:
    print("\n" + "=" * 96)
    print("P2 — CA demand-weighted annual LMP move (KILL GATE)")
    print("=" * 96)
    ok = True
    for year in YEARS:
        a, b = _system(control, year), _system(arm, year)
        la, lb = _ca_lambda(a), _ca_lambda(b)
        delta = float(np.mean(lb) - np.mean(la))
        zones, pa = _ca_price_matrix(a)
        _, pb = _ca_price_matrix(b)
        max_abs = float(np.nanmax(np.abs(pb - pa)))
        ceiling = (
            P2_E1_CEILING
            if year == 2025
            else (P2_E2_CEILING if year == 2024 else P2_E2_CEILING)
        )
        hit = delta <= ceiling + P2_DEGENERACY_TOL
        ok &= hit
        label = "E1" if year == 2025 else ("E2" if year == 2024 else "  ")
        print(
            f"  {year} {label}: CA λ A {np.mean(la):8.4f} → B {np.mean(lb):8.4f} "
            f"Δ {delta:+.4f} (ceiling {ceiling:+.2f}) | max per-zone-hour |Δ| "
            f"{max_abs:.4f} over {len(zones)} zones   {'PASS' if hit else 'FAIL'}"
        )
    print(f"\n  P2: {'PASS' if ok else 'FAIL'}")
    return ok


def gate_p3(control: Path, arm: Path) -> bool:
    print("\n" + "=" * 96)
    print("P3 — rubric identical to arm A")
    print("=" * 96)

    def rubric(b: Path) -> tuple[str, list[str]]:
        """(determination, sorted FAIL criteria ids) from the bundle metrics."""
        m = json.loads((b / "metrics.json").read_text())
        det = str(m.get("determination", ""))
        crit = m.get("criteria") or {}
        fails = sorted(
            k
            for k, v in crit.items()
            if str((v or {}).get("status", "")).upper().startswith("FAIL")
        )
        return det, fails

    da, fa = rubric(control)
    db, fb = rubric(arm)
    hit = (da, fa) == (db, fb)
    print(f"  arm A: {da or '(n/a)'} fail {fa}")
    print(f"  arm B: {db or '(n/a)'} fail {fb}")
    print(f"\n  P3: {'PASS' if hit else 'FAIL — scored-gate flip, stop and report'}")
    return hit


def gate_p4(control: Path, arm: Path) -> bool:
    print("\n" + "=" * 96)
    print("P4 — 2023 null control: the guard is unchanged in 2023 (KILL GATE)")
    print("=" * 96)
    a, b = _system(control, 2023), _system(arm, 2023)
    dp = float(np.nanmax(np.abs(b["price"].to_numpy() - a["price"].to_numpy())))
    dd = float(np.nanmax(np.abs(b["dump"].to_numpy() - a["dump"].to_numpy())))
    hit = dp == 0.0 and dd == 0.0
    print(
        f"  2023 max |Δprice| {dp:.6f}, max |Δdump| {dd:.6f} "
        f"(all zones incl. WECC)   {'PASS' if hit else 'FAIL'}"
    )
    print(f"\n  P4: {'PASS' if hit else 'FAIL'}")
    return hit


def report_p5(control: Path, arm: Path) -> None:
    print("\n" + "=" * 96)
    print("P5 — node print in the FORMER dump hours, and the phantom energy removed")
    print("=" * 96)
    for year in YEARS:
        a, b = _system(control, year), _system(arm, year)
        ua, ub = _unit_hourly(control, year), _unit_hourly(arm, year)
        for zone in WECC_ZONES:
            za = a[a["zone"] == zone]
            zb = b[b["zone"] == zone]
            dh = za["dump"].to_numpy() > 1e-6
            if not dh.any():
                continue
            hub = _measured_hub(year, HUB_OF[zone])
            n = min(len(hub), len(dh))
            m = dh[:n]
            pa = za["price"].to_numpy()[:n][m]
            pb = zb["price"].to_numpy()[:n][m]
            print(
                f"  {year} {zone:9s} ({int(m.sum())} former dump hrs): node λ "
                f"A median {np.median(pa):+8.3f} → B {np.median(pb):+8.3f}; "
                f"measured {HUB_OF[zone]} same hrs {np.nanmedian(hub[:n][m]):+8.3f}"
            )
            if ua.empty or ub.empty:
                continue
            ta = (
                ua[ua["zone"] == zone]
                .pivot_table(index="hour", columns="unit_id", values="mw", aggfunc="sum")
                .reindex(range(n), fill_value=0.0)
            )
            tb = (
                ub[ub["zone"] == zone]
                .pivot_table(index="hour", columns="unit_id", values="mw", aggfunc="sum")
                .reindex(range(n), fill_value=0.0)
                .reindex(columns=ta.columns, fill_value=0.0)
            )
            delta = (tb.to_numpy()[m].sum(axis=0) - ta.to_numpy()[m].sum(axis=0)) / 1e6
            order = np.argsort(delta)
            moved = [
                f"{ta.columns[i].removeprefix(zone + '_')} {delta[i]:+.4f}"
                for i in order[:4]
                if abs(delta[i]) > 1e-6
            ]
            print(f"     tranche energy inside those hours (TWh, B−A): {', '.join(moved)}")


def control_integrity(control: Path, keeper: Path) -> None:
    print("\n" + "=" * 96)
    print("Control integrity — arm A vs the committed keeper bundle")
    print("=" * 96)
    for year in YEARS:
        a, k = _system(control, year), _system(keeper, year)
        dp = float(np.nanmax(np.abs(a["price"].to_numpy() - k["price"].to_numpy())))
        dd = float(np.nanmax(np.abs(a["dump"].to_numpy() - k["dump"].to_numpy())))
        print(
            f"  {year}: max |Δprice| {dp:.6f}, max |Δdump| {dd:.6f} "
            f"{'(byte-identical)' if dp == 0.0 and dd == 0.0 else '(DRIFT — investigate)'}"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--keeper", default="results/calibration/caiso138_envclip_B")
    args = ap.parse_args()
    control, arm = Path(args.control), Path(args.arm)
    control_integrity(control, Path(args.keeper))
    p1 = gate_p1(control, arm)
    p2 = gate_p2(control, arm)
    p3 = gate_p3(control, arm)
    p4 = gate_p4(control, arm)
    report_p5(control, arm)
    print("\n" + "=" * 96)
    print(
        f"VERDICT — P1 {'PASS' if p1 else 'FAIL'} | P2 {'PASS' if p2 else 'FAIL'} | "
        f"P3 {'PASS' if p3 else 'FAIL'} | P4 {'PASS' if p4 else 'FAIL'}"
    )
    print("=" * 96)
    return 0 if (p1 and p2 and p4) else 1


if __name__ == "__main__":
    raise SystemExit(main())
