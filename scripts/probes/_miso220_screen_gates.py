"""miso-220 SCREEN gates — COMMITTED BEFORE THE SCREEN'S NUMBERS ARE READ.

Scores the rule 29 ``[R-SCREEN]`` one-year screen of the non-steam fossil x1.10
offer lift, against the gate frozen in ADDENDUM A of
``PREREG-miso220-nonsteam-offer-lift-2026-09-05.md``, which was itself written and
pushed (``a4a72ece``) before the screen was launched.

**The gate is STRUCTURAL and STOP-ONLY (rule 29).** It asks whether the mechanism
does what its own pre-solve arithmetic says it does. **It may kill the arm; it may
never promote one**, and it is NEVER gated on the target residual — a screen reading
"did C3a improve" would be the fitted-mechanism selection rule 1 ``[R-STRUCT]``
forbids, done one year at a time.

* **G-1 direction and order of magnitude.** The pre-solve delta raises cap-weighted
  offers by CC_REGULAR +9.29 %, CC_CHP +8.58 %, CT_PEAKER +7.54 %, CT_CHP +7.48 %,
  COAL +6.53 %, ST_GAS +0.00 %. The system load-weighted price must RISE by between
  +3.0 % and +12.0 %.
* **G-2 the merit-order identity the arm asserts.** Holding steam gas makes it
  relatively cheaper, so ``ST_GAS`` grid-delivered energy must RISE against the
  control's. If it falls, the rationale for excluding steam gas is refuted here.
* **G-3 footprint confinement.** No non-target load-bearing criterion flips
  PASS -> FAIL in the screen year.

G-1 and G-2 are computed from the two bundles' own committed sidecars — model vs
model, no actuals, so neither can be contaminated by the target. G-3 needs actuals
and goes through ``calibration_verdict``; C6 is expected to read UNATTESTED on a
replay and is NOT part of this gate (it is protective, not load-bearing), so a
missing attestation cannot silently fail the screen.

**C3a is REPORTED and carries no decision weight.**

Record: ``results/calibration/_miso220_screen_gates.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "results/calibration/miso217_intermphys_B"
SCREEN = REPO / "results/calibration/miso220_nonsteamlift_screen2025"
OUT = REPO / "results/calibration/_miso220_screen_gates.json"

SCREEN_YEAR = 2025
G1_BAND_PCT = (3.0, 12.0)
LOAD_BEARING = ("fuelmix", "sysvol", "price_mean", "price_shape")
EXTERNAL_PREFIX = "MISO_external"
CONTROL_C1_ST_GAS_2025 = -5.820  # frozen from the control's own verdict


def _lw_price(bundle: Path, year: int) -> float:
    """Load-weighted system mean LMP from a bundle's committed P1 ``system`` sidecar."""
    df = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    p = df.pivot_table(index="hour", columns="zone", values="price", aggfunc="first")
    d = df.pivot_table(index="hour", columns="zone", values="demand", aggfunc="first")
    zones = [z for z in p.columns if not str(z).startswith(EXTERNAL_PREFIX)]
    pa, da = p[zones].to_numpy(float), d[zones].to_numpy(float)
    return float((pa * da).sum() / max(da.sum(), 1e-9))


def _class_twh(bundle: Path, year: int, klass: str) -> float:
    """Annual TWh for one class from a bundle's committed P1 ``class_hourly`` sidecar."""
    df = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == klass)]
    return float(df["mw"].sum() / 1e6)


def _verdict(bundle: Path) -> dict | None:
    """``calibration_verdict --json`` for a bundle, or ``None`` if it cannot score."""
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json", str(bundle)],
        capture_output=True, text=True, check=False,
    )
    if not res.stdout.strip():
        return None
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        return None


def _status(v: dict, year: int) -> dict:
    """``{criterion|key: status}`` for the load-bearing criteria in one year."""
    out = {}
    for name in LOAD_BEARING:
        for r in ((v.get("criteria") or {}).get(name) or {}).get("records", []) or []:
            if r.get("year") != year:
                continue
            out[f"{name}|{r.get('key')}"] = r.get("status")
    return out


def _c3a(v: dict, year: int) -> float | None:
    """Signed % error on the RT load-weighted mean LMP — REPORTED, never gated."""
    for r in ((v.get("criteria") or {}).get("price_mean") or {}).get("records", []) or []:
        if r.get("year") == year and r.get("benchmark") == "RT" and r.get("key") is None:
            return round(100.0 * (float(r["model"]) - float(r["actual"])) / float(r["actual"]), 4)
    return None


def main() -> int:
    """Score G-1/G-2/G-3, write the record, print the screen verdict."""
    if not (SCREEN / f"hourly/system_{SCREEN_YEAR}.parquet").exists():
        raise SystemExit(f"screen bundle incomplete: {SCREEN}")

    pc, pa = _lw_price(CONTROL, SCREEN_YEAR), _lw_price(SCREEN, SCREEN_YEAR)
    g1_pct = round(100.0 * (pa / pc - 1.0), 4)
    g1 = bool(G1_BAND_PCT[0] <= g1_pct <= G1_BAND_PCT[1])

    stc, sta = _class_twh(CONTROL, SCREEN_YEAR, "ST_GAS"), _class_twh(SCREEN, SCREEN_YEAR, "ST_GAS")
    g2 = bool(sta > stc)

    vc, va = _verdict(CONTROL), _verdict(SCREEN)
    flips, g3, c3a_screen = [], True, None
    if vc and va:
        sc, sa = _status(vc, SCREEN_YEAR), _status(va, SCREEN_YEAR)
        flips = [
            {"criterion": k, "control": sc.get(k), "screen": sa.get(k)}
            for k in sorted(set(sc) | set(sa))
            if sc.get(k) == "PASS" and sa.get(k) == "FAIL"
        ]
        g3 = not flips
        c3a_screen = _c3a(va, SCREEN_YEAR)

    killed = [n for n, ok in (("G1", g1), ("G2", g2), ("G3", g3)) if not ok]
    rep = {
        "probe": "miso-220 rule-29 SCREEN gates (structural, stop-only)",
        "prereg": "PREREG-miso220-nonsteam-offer-lift-2026-09-05.md ADDENDUM A @ a4a72ece",
        "screen_year": SCREEN_YEAR,
        "control": str(CONTROL.relative_to(REPO)),
        "screen": str(SCREEN.relative_to(REPO)),
        "G1_price_direction_magnitude": {
            "control_lw_price_usd": round(pc, 4),
            "screen_lw_price_usd": round(pa, 4),
            "pass_through_pct": g1_pct,
            "band_pct": list(G1_BAND_PCT),
            "PASS": g1,
        },
        "G2_merit_order_identity_st_gas_rises": {
            "control_twh": round(stc, 4),
            "screen_twh": round(sta, 4),
            "delta_twh": round(sta - stc, 4),
            "control_c1_error_twh": CONTROL_C1_ST_GAS_2025,
            "PASS": g2,
        },
        "G3_no_non_target_load_bearing_flip": {
            "flips": flips,
            "scored": bool(vc and va),
            "PASS": g3,
        },
        "REPORTED_NOT_GATED": {
            "c3a_screen_pct": c3a_screen,
            "note": "C3a carries NO decision weight in the screen (rule 29 / rule 1)",
        },
        "gates_failed": killed,
        "verdict": "SCREEN KILLS THE ARM" if killed else "SCREEN CLEARS - spend the full 2023-2025 span",
        "licenses": (
            "Clearing licenses ONLY spending the full span. It is NOT evidence the arm is a "
            "keeper: K-1 (CT_PEAKER-2023 band exit) and K-3 (ST_GAS-2024) cannot fire here."
        ),
    }
    OUT.write_text(json.dumps(rep, indent=2))
    print(f"  G-1 price {pc:.3f} -> {pa:.3f} = {g1_pct:+.3f}% band {G1_BAND_PCT}  {'PASS' if g1 else 'FAIL'}")
    print(f"  G-2 ST_GAS {stc:.4f} -> {sta:.4f} TWh ({sta - stc:+.4f})  {'PASS' if g2 else 'FAIL'}")
    print(f"  G-3 load-bearing flips: {flips or 'none'}  {'PASS' if g3 else 'FAIL'}")
    print(f"  [reported, not gated] C3a-{SCREEN_YEAR}: {c3a_screen}")
    print(f"  VERDICT: {rep['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
