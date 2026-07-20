"""CAISO-107 intertie re-charter: EVENING price-premium + BELLY hub-level depth (derive-first).

FINDING-caiso106 split the caiso-105 unified "too-elastic-both-directions"
intertie diagnosis into two mechanistically DISTINCT defects and RE-CHARTERED
each with a fresh measurement (`caiso-106-evening-intertie-exhaustion-ask` §7):

  1. EVENING is a PRICE / merit-order defect, not a volume defect (the model's
     evening import VOLUME ≈ measured, so the withdrawn volume ceiling is inert).
     The model prices the marginal evening MW at the hub-equalized (static
     firm-block contract) level, BELOW reality's marginal supply. Candidate LP
     form: an inelastic exhaustion PREMIUM lifting the marginal tight-hour
     import offer above the hub by the MEASURED RT-over-hub separation in the
     tight state (the MISO/NEISO Q-Q measured-ladder class), NOT a residual-tuned
     adder. NEXT STEP (this probe, lane 1): MEASURE that premium and gate it.
  2. BELLY is a VOLUME defect (the net-import ceiling BINDS — model over-imports
     +2.6 GW in deep surplus) but the depth is not year-stable on any CAISO
     net-load state (west-wide dependence, FINDING-caiso106 §3). Candidate
     observable: the Palo Verde / Malin hub LEVEL, which prices the neighbor
     surplus CAISO net-load misses. NEXT STEP (this probe, lane 2): RE-MEASURE
     the belly depth conditioned on the hub LEVEL and test whether it stabilizes.

This probe MEASURES both lanes on pure raw data (EIA-930 CISO interchange +
WECC hub DA LMP + CA actual RT/DA LMP + EIA-930 net-load) — NO LP, NO mechanism,
NO fitted throttle (rule 1: any eventual ask must rest on a measured quantity
conditioned on an observable, forward-reproducible state, never a residual-tuned
value). It reuses the committed caiso-106 measurement primitives (``_load``, the
windows, the fixed net-load bands, the CV/LOYO honesty gate) and adds:

  LANE 1 — EVENING RT-over-hub premium: mean/p50 of (actual RT − measured hub)
    per fixed net-load band and in the tightest net-load quintile, with the
    caiso-81/86/87 CV≤0.20 + LOYO≤25 % gate. The go/no-go for the exhaustion
    PREMIUM ask: only draftable if the premium is a year-stable POSITIVE
    separation in the tight state. Also prints the CA DA−RT basis so the
    day-ahead-hub-vs-real-time-CA market mismatch in the measurement is explicit.

  LANE 2 — BELLY depth on hub LEVEL: p50/mean TOTAL net import per PaloVerde /
    Malin hub-level band, with the per-band CV / ±MW-near-zero gate — the direct
    test of whether the hub LEVEL (the west-wide observable) stabilizes the
    belly depth that net-load conditioning could not (FINDING-caiso106 §3, CV
    0.33-0.53). The go/no-go for the belly net-import-ceiling ask.

Both lanes report their PASS/FAIL verdict; per the derive-first mandate a lane
whose measurement FAILS the stability gate is FILED and re-chartered, NEVER fit.

Usage: .venv/bin/python scripts/probes/_caiso107_intertie_recharter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _caiso106_intertie_elasticity import (  # noqa: E402
    BELLY,
    CV_MAX,
    EVENING,
    LOYO_MAX,
    N_BUCKET,
    NL_BANDS_GW,
    YEARS,
    _load,
)

HOURS = 8760
# Fixed hub-level bands ($/MWh) for the belly west-wide observable. Absolute
# thresholds so the same band is the same physical neighbor-price state in every
# year and forward — the belly analogue of NL_BANDS_GW.
HUB_BANDS = [
    (-120.0, -2.0),
    (-2.0, 8.0),
    (8.0, 18.0),
    (18.0, 28.0),
    (28.0, 40.0),
    (40.0, 120.0),
]


# --------------------------------------------------------------------------- #
# shared honesty gates (caiso-81/86/87 standard, reused from caiso-106)         #
# --------------------------------------------------------------------------- #
def _scalar_gate(name: str, vals: dict[int, float]) -> bool:
    """CV≤0.20 + LOYO≤25 % gate on a single per-year quantity (caiso-106 _gate)."""
    arr = np.array([vals[y] for y in YEARS], dtype=float)
    mean = float(np.mean(arr))
    cv = float(np.std(arr) / abs(mean)) if abs(mean) > 1e-9 else float("nan")
    g_cv = np.isfinite(cv) and cv <= CV_MAX
    print(
        f"\n  {name}: "
        + " ".join(f"{y}={vals[y]:+,.1f}" for y in YEARS)
        + f"  |  CV {cv:.3f} ({'PASS' if g_cv else 'FAIL'})"
    )
    g_loyo = True
    for held in YEARS:
        pred = float(np.mean([vals[y] for y in YEARS if y != held]))
        denom = abs(vals[held])
        err = abs(pred - vals[held]) / denom if denom > 1e-9 else float("inf")
        ok = err <= LOYO_MAX
        g_loyo = g_loyo and ok
        print(
            f"    LOYO {held}: mean-of-others {pred:+,.1f} vs {vals[held]:+,.1f}"
            f" -> {err:.1%} ({'PASS' if ok else 'FAIL'})"
        )
    return g_cv and g_loyo


def _band_gate(title: str, bands, per_year: dict[int, dict[tuple, float]]) -> bool:
    """Per-band cross-year CV (or ±MW near a zero crossing) — caiso-106 standard."""
    print(f"\n  {title}:")
    print("    band          " + "".join(f"{y:>9}" for y in YEARS) + "     CV/spread")
    all_ok = True
    for band in bands:
        vals = np.array([per_year[y][band] for y in YEARS], dtype=float)
        if np.isnan(vals).any():
            print(
                f"    [{band[0]:6.0f},{band[1]:5.0f}) "
                + "".join(f"{v:>9.0f}" for v in vals)
                + "   (sparse)"
            )
            continue
        std = float(np.std(vals))
        mean = float(np.mean(vals))
        cv = std / abs(mean) if abs(mean) > 500 else float("nan")
        ok = (np.isfinite(cv) and cv <= CV_MAX) or (
            not np.isfinite(cv) and std <= 750.0
        )
        all_ok = all_ok and ok
        cvs = f"CV {cv:.2f}" if np.isfinite(cv) else f"±{std:.0f}MW"
        print(
            f"    [{band[0]:6.0f},{band[1]:5.0f}) "
            + "".join(f"{v:>9.0f}" for v in vals)
            + f"   {cvs} {'ok' if ok else 'FAIL'}"
        )
    return all_ok


def _dollar_band_gate(title: str, bands, per_year: dict[int, dict[tuple, float]]) -> bool:
    """Per-band cross-year stability of a $/MWh quantity (premium).

    A $/MWh premium is not a MW flow, so the caiso-106 ±750-MW near-zero
    fallback is inapplicable — a $5 premium with a $6 std is NOT stable even
    though its MW-scale std is tiny. Gate: CV≤0.20 where |mean|>$5, else the
    absolute cross-year spread ≤ $5. A sign flip across years fails outright.
    """
    print(f"\n  {title}:")
    print("    band          " + "".join(f"{y:>9}" for y in YEARS) + "     CV/spread")
    all_ok = True
    for band in bands:
        vals = np.array([per_year[y][band] for y in YEARS], dtype=float)
        if np.isnan(vals).any():
            print(
                f"    [{band[0]:6.0f},{band[1]:5.0f}) "
                + "".join(f"{v:>9.1f}" for v in vals)
                + "   (sparse)"
            )
            continue
        std = float(np.std(vals))
        mean = float(np.mean(vals))
        spread = float(np.max(vals) - np.min(vals))
        sign_flip = bool(np.any(vals > 0) and np.any(vals < 0))
        if abs(mean) > 5.0:
            cv = std / abs(mean)
            ok = cv <= CV_MAX and not sign_flip
            tag = f"CV {cv:.2f}"
        else:
            ok = spread <= 5.0 and not sign_flip
            tag = f"±${spread:.1f}"
        if sign_flip:
            tag += " SIGN-FLIP"
        all_ok = all_ok and ok
        print(
            f"    [{band[0]:6.0f},{band[1]:5.0f}) "
            + "".join(f"{v:>9.1f}" for v in vals)
            + f"   {tag} {'ok' if ok else 'FAIL'}"
        )
    return all_ok


def _finite_window(d: dict[str, np.ndarray], hods, *keys) -> np.ndarray:
    """Window mask requiring every named series finite."""
    hod = np.arange(HOURS) % 24
    m = np.isin(hod, hods)
    for k in keys:
        m = m & np.isfinite(d[k])
    return m


# --------------------------------------------------------------------------- #
# LANE 1 — EVENING RT-over-hub premium                                          #
# --------------------------------------------------------------------------- #
def _hub_ref(d: dict[str, np.ndarray], how: str) -> np.ndarray:
    """The reference hub level: max / min / palo / malin of the two hub prints."""
    palo, malin = d["palo"], d["malin"]
    if how == "max":
        return np.fmax(palo, malin)
    if how == "min":
        return np.fmin(palo, malin)
    return d[how]


def _evening_premium_tables(data: dict[int, dict]) -> None:
    """Per-year evening RT − hub level by band, plus the CA DA−RT confound."""
    for y in YEARS:
        d = data[y]
        hubmax = _hub_ref(d, "max")
        m = _finite_window(d, EVENING, "rt", "palo", "malin")
        nl = d["netload"]
        print(f"\n--- {y} EVENING (hod 17-21): RT vs hub, by fixed net-load band ---")
        print(
            "  band(GW)   n    RT    PALO   MALIN  RT-max(hub)  RT-min(hub)  "
            "CA(DA-RT)"
        )
        for lo, hi in NL_BANDS_GW:
            sel = m & (nl >= lo * 1e3) & (nl < hi * 1e3)
            if sel.sum() < 20:
                continue
            rt = d["rt"][sel]
            pa, ma = d["palo"][sel], d["malin"][sel]
            dabasis = (d["da"] - d["rt"])[sel & np.isfinite(d["da"])]
            print(
                f"  [{lo:4.0f},{hi:3.0f}) {int(sel.sum()):4d} {rt.mean():6.1f} "
                f"{pa.mean():6.1f} {ma.mean():6.1f}   {(rt - hubmax[sel]).mean():+7.1f}"
                f"      {(rt - _hub_ref(d, 'min')[sel]).mean():+7.1f}    "
                f"{dabasis.mean() if dabasis.size else float('nan'):+7.1f}"
            )


def _premium_by_band(data: dict[int, dict], hub_how: str) -> dict[int, dict[tuple, float]]:
    """Mean (RT − hub_how) per fixed net-load band, per year — the premium curve."""
    out: dict[int, dict[tuple, float]] = {}
    for y in YEARS:
        d = data[y]
        hub = _hub_ref(d, hub_how)
        m = _finite_window(d, EVENING, "rt", "palo", "malin")
        nl = d["netload"]
        prem = d["rt"] - hub
        row: dict[tuple, float] = {}
        for lo, hi in NL_BANDS_GW:
            sel = m & (nl >= lo * 1e3) & (nl < hi * 1e3)
            row[(lo, hi)] = float(prem[sel].mean()) if sel.sum() >= 20 else float("nan")
        out[y] = row
    return out


def _tight_quintile_premium(data: dict[int, dict], hub_how: str) -> dict[int, float]:
    """Mean (RT − hub_how) in the TIGHTEST evening net-load quintile, per year."""
    out: dict[int, float] = {}
    for y in YEARS:
        d = data[y]
        hub = _hub_ref(d, hub_how)
        m = _finite_window(d, EVENING, "rt", "palo", "malin")
        nl = d["netload"]
        edges = np.percentile(nl[m], np.linspace(0, 100, N_BUCKET + 1))
        sel = m & (nl >= edges[N_BUCKET - 1])
        out[y] = float((d["rt"] - hub)[sel].mean())
    return out


def lane1_evening_premium(data: dict[int, dict]) -> bool:
    """LANE 1: measure + gate the tight-evening RT-over-hub premium."""
    print("\n" + "=" * 72)
    print("LANE 1 — EVENING RT-over-hub PREMIUM (candidate exhaustion-premium ask)")
    print("=" * 72)
    _evening_premium_tables(data)

    print(
        "\n  >> premium = mean(RT − hub) per net-load band; the ask needs a"
        "\n     year-stable POSITIVE separation in the tight (high net-load) state."
    )
    gates = []
    tight_bands = [(20.0, 25.0), (25.0, 30.0), (30.0, 45.0)]
    for how in ("max", "min"):
        pv = _premium_by_band(data, how)
        gates.append(
            _dollar_band_gate(
                f"EVENING premium mean(RT − {how}(hub)) by net-load band ($/MWh)",
                NL_BANDS_GW,
                pv,
            )
        )
        # Sign check: the exhaustion-premium mechanism lifts the marginal import
        # ABOVE the hub, so it requires a POSITIVE separation in the tight
        # (high-net-load) state. If RT prints BELOW the hub there, the mechanism
        # has the wrong sign (raising λ would over-price, not fix the under-price).
        tight_vals = [pv[y][b] for y in YEARS for b in tight_bands if not np.isnan(pv[y][b])]
        pos_frac = float(np.mean([v > 0 for v in tight_vals])) if tight_vals else float("nan")
        print(
            f"    tight-state ([20,45) GW) sign: mean RT − {how}(hub) "
            f"{np.nanmean(tight_vals):+.1f} $/MWh, positive in {pos_frac:.0%} of tight"
            f" band-years -> {'right sign' if pos_frac > 0.5 else 'WRONG SIGN (RT below hub)'}"
        )
    tq_max = _tight_quintile_premium(data, "max")
    tq_min = _tight_quintile_premium(data, "min")
    g_tq_max = _scalar_gate("EVENING premium RT − max(hub), tightest NL quintile", tq_max)
    g_tq_min = _scalar_gate("EVENING premium RT − min(hub), tightest NL quintile", tq_min)

    passed = all(gates) and g_tq_max and g_tq_min
    print(
        f"\n  LANE 1 VERDICT: premium {'PASS (stable)' if passed else 'FAIL (not year-stable / wrong-sign)'}"
        f" — band-gates {[('PASS' if g else 'FAIL') for g in gates]}, "
        f"tight-quintile max={'PASS' if g_tq_max else 'FAIL'} "
        f"min={'PASS' if g_tq_min else 'FAIL'}"
    )
    return passed


# --------------------------------------------------------------------------- #
# LANE 2 — BELLY depth on hub LEVEL                                             #
# --------------------------------------------------------------------------- #
def _belly_depth_by_hublevel(
    data: dict[int, dict], hub_how: str, pct: float
) -> dict[int, dict[tuple, float]]:
    """pXX TOTAL net import per hub-level band in the belly, per year."""
    out: dict[int, dict[tuple, float]] = {}
    for y in YEARS:
        d = data[y]
        hub = _hub_ref(d, hub_how)
        hod = np.arange(HOURS) % 24
        m = np.isin(hod, BELLY) & np.isfinite(hub) & np.isfinite(d["total"])
        row: dict[tuple, float] = {}
        for lo, hi in HUB_BANDS:
            sel = m & (hub >= lo) & (hub < hi)
            row[(lo, hi)] = (
                float(np.percentile(d["total"][sel], pct)) if sel.sum() >= 20 else float("nan")
            )
        out[y] = row
    return out


def _belly_hublevel_table(data: dict[int, dict], hub_how: str) -> None:
    """Print the belly TOTAL net-import summary per hub-level band, per year."""
    for y in YEARS:
        d = data[y]
        hub = _hub_ref(d, hub_how)
        hod = np.arange(HOURS) % 24
        m = np.isin(hod, BELLY) & np.isfinite(hub) & np.isfinite(d["total"])
        print(f"\n--- {y} BELLY (hod 10-14): TOTAL net import by {hub_how.upper()}-hub band ---")
        print("  hub$band     n    mean    p50    p95   export%")
        for lo, hi in HUB_BANDS:
            sel = m & (hub >= lo) & (hub < hi)
            if sel.sum() < 20:
                print(f"  [{lo:6.0f},{hi:5.0f}) {int(sel.sum()):4d}   (sparse)")
                continue
            tot = d["total"][sel]
            print(
                f"  [{lo:6.0f},{hi:5.0f}) {int(sel.sum()):4d} {tot.mean():+7.0f} "
                f"{np.percentile(tot, 50):+6.0f} {np.percentile(tot, 95):+6.0f}  "
                f"{float((tot < 0).mean()):5.0%}"
            )


def lane2_belly_hublevel(data: dict[int, dict]) -> bool:
    """LANE 2: re-measure + gate the belly depth conditioned on the hub LEVEL."""
    print("\n" + "=" * 72)
    print("LANE 2 — BELLY depth conditioned on hub LEVEL (west-wide observable)")
    print("=" * 72)
    print(
        "  Net-load conditioning FAILED the stability gate (FINDING-caiso106 §3:"
        "\n  fixed-band p50 CV 0.33-0.37, quintile depth CV 0.53). Does the hub"
        "\n  LEVEL (which prices the neighbor surplus CAISO net-load misses) stabilize it?"
    )
    gates = []
    for how in ("palo", "min"):
        _belly_hublevel_table(data, how)
        for pct, tag in ((50, "p50"), (95, "p95 ceiling")):
            pv = _belly_depth_by_hublevel(data, how, pct)
            gates.append(
                _band_gate(
                    f"BELLY {tag} TOTAL net import by {how.upper()}-hub-level band (MW)",
                    HUB_BANDS,
                    pv,
                )
            )
    passed = all(gates)
    print(
        f"\n  LANE 2 VERDICT: hub-level depth "
        f"{'PASS (stable)' if passed else 'FAIL (not year-stable on hub level)'}"
        f" — band-gates {[('PASS' if g else 'FAIL') for g in gates]}"
    )
    return passed


def main() -> int:
    data = {y: _load(y) for y in YEARS}
    g1 = lane1_evening_premium(data)
    g2 = lane2_belly_hublevel(data)
    print("\n" + "=" * 72)
    print("SUMMARY (derive-first — a FAIL files + re-charters, never fits):")
    print(
        f"  LANE 1 evening RT-over-hub premium : {'READY (draft premium ask)' if g1 else 'NOT READY — file + re-charter'}"
    )
    print(
        f"  LANE 2 belly depth on hub level    : {'READY (draft ceiling ask)' if g2 else 'NOT READY — file + re-charter'}"
    )
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
