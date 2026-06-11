#!/usr/bin/env python3
"""Empirical cross-class offer-curve tuning Jacobian from calibration bundles.

Pure parquet/JSON analysis of existing calibration bundles under
``results/calibration`` — no LP is re-solved. From consecutive run pairs whose
only difference is offer-curve band-multiplier moves ("pure-curve pairs"), it
collects observations Δ(band multiplier vector) → Δ(class TWh vector) per year
and fits a sparse ridge-regularized linear map

    Δgen[in_class] ≈ Σ S[in_class, (out_class, band)] · Δmult[(out_class, band)]

so tuning can solve one joint multi-class move instead of sequential
single-knob walks that whack-a-mole between interrelated classes
(CT_PEAKER committed ↔ ST_GAS, COAL_PRB ↔ COAL_LIGNITE, CC_REGULAR as the
big residual marginal class). Each year is fitted separately — the 2024 vs
2023/2025 asymmetry is gas-price-driven ($2.54 / $2.19 / $3.52 per MMBtu).

Run pairs that include structural code or data changes (storage fix, plant
appends, BTM trims, fuel-cost re-grounding, demand alignment, heat-rate
re-bases, …) are excluded from the regression via a curated registry below;
unknown future runs are auto-classified from the bundle's
``model_changes_note`` plus a ``git diff`` between the recorded shas when both
are resolvable, so the tool keeps working as new backcasts accrue for any ISO.

Outputs
-------
- ``inputs/processed/offer_curve_jacobian.csv`` (long format: iso, year,
  out_class, band, in_class, dTWh_per_unit_mult, n_obs, stderr, confidence)
- printed matrix sorted by |sensitivity| with confidence flags
- merit-order adjacency validation: each class-band's $/MWh offer range
  (band mult × class base HR × monthly fuel price) vs the demand-weighted
  clearing-price distribution in ``system.parquet`` — overlapping ranges are
  the substitution pairs the regression should agree with
- a joint-move recipe: given the latest run's error vector err (TWh per
  class-year), solve min ‖S·Δm + err‖² (ridge-regularized, per-step band
  moves capped at ±0.15) and print the recommended Δm

Usage
-----
    python scripts/derive_offer_curve_jacobian.py                 # all ISOs found
    python scripts/derive_offer_curve_jacobian.py --iso ERCOT
    python scripts/derive_offer_curve_jacobian.py --include-pair Run-60-prbfix
    python scripts/derive_offer_curve_jacobian.py --validate-run Run-73
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO / "results" / "calibration"
DEFAULT_OUT = REPO / "inputs" / "processed" / "offer_curve_jacobian.csv"
CACHE_PATH = REPO / "inputs" / "processed" / ".offer_curve_jacobian_cache.json"
FUEL_COSTS = REPO / "inputs" / "processed" / "eia923_monthly_fuel_costs.parquet"

# Offer-curve knobs per class as resolved in run_config.json
# scenario_config.offer_curve_by_group. The first four are heat-rate band
# multipliers (the ±0.15 recipe cap applies to these); econ_low_share is a
# fraction and pct_peaking a percent of nameplate — different units, fitted
# and reported but excluded from the joint-move solver.
BANDS = ("committed", "econ_low", "econ_high", "peak",
         "econ_low_share", "pct_peaking")
PRICE_BANDS = BANDS[:4]

# ---------------------------------------------------------------------------
# Pair classification registry. Keyed by the *later* run of a consecutive
# pair; a pair inherits the later run's status:
#   pure       — verified offer-curve-only move; regression input.
#   structural — code/data change (possibly alongside curve moves); excluded
#                from the regression, usable only as a qualitative sign check.
#   legacy     — early/exploratory bundles whose provenance was not verified;
#                excluded by default (force with --include-pair).
#   sidecar    — A/B experiment off a mainline run (e.g. a smoothing sweep);
#                removed from the pairing chain entirely so the mainline runs
#                on either side still pair with each other.
# Verification for the entries below: model_changes_note review plus
# `git diff <sha0> <sha1> -- src/ inputs/ data/` between the recorded shas
# (clean for every pure pair; note that several structural changes do NOT
# show in those diffs — storage parquet, ER plant append, BTM trim — so the
# note review is authoritative, not git).
# ---------------------------------------------------------------------------
REGISTRY: dict[str, tuple[str, str]] = {
    # --- ERCOT ---
    "Run46-tuning": ("legacy", "early tuning era, provenance unverified"),
    "run-47-tuning": ("legacy", "early tuning era, provenance unverified"),
    "run-48-tuning": ("legacy", "early tuning era, provenance unverified"),
    "Run-58-tuning": ("legacy", "OTHER-class breakout alongside tuning"),
    "Run-59-Claude-tuning": ("structural", "OTHER-class breakout alongside tuning"),
    "Run-60-prbfix": (
        "legacy",
        "note lists only multiplier moves and git is clean, but predates the "
        "verified candidate window — include explicitly once vetted",
    ),
    "Run-61": ("pure", "multiplier moves only (note + clean git)"),
    "Run-62": ("pure", "multiplier moves only (note + clean git)"),
    "Run-63": ("structural", "EIA-860 ER storage parquet; 2025 battery fleet 8.05->12.82 GW"),
    "Run-64": ("structural", "ER plant append + storage 13.7 GW (CC_CHP shape move mixed in)"),
    "Run-65": ("pure", "cross-class rebalance, multipliers only"),
    "Run-66": ("structural", "CHP BTM pull-out trim (supply-side data change)"),
    "Run-67": ("pure", "consolidation of Run-66, multipliers only"),
    "Run-68": ("structural", "measured EIA-923 PRB fuel costs replace flat assumption"),
    "Run-69": ("structural", "CC_CHP heat-rate re-base to eGRID PLHTRT (custom-bin-assignments.csv)"),
    "Run-70": ("pure", "multiplier moves only on the new HR basis"),
    "Run-71": ("structural", "2025 demand-alignment fix (curves unchanged from Run-70)"),
    "Run-72": ("pure", "multiplier moves only (note + clean git)"),
    "Run-73": ("structural", "CHP steam-floor fix + Petra Nova reclassification (curve moves mixed in — sign-check only)"),
    "curve-n12-2024": ("sidecar", "A/B of offer_curve_smoothing_n off Run-72, single year"),
    "Run-74": ("structural", "regenerated unit-outage extract (Rio Nogales / C.R. Wing derates) alongside the curve walk-back"),
    # --- PJM ---
    "pjm_2023": ("legacy", "exploratory era"),
    "pjm_2024": ("legacy", "exploratory era"),
    "pjm_2023_8z_ix": ("legacy", "exploratory era"),
    "pjm_2024_v2": ("structural", "unit-only outages + grounded tranches + n=6 curve rebase"),
    "pjm_2024_coalclass": ("structural", "EIA-923 coal supply class breakout"),
    "pjm_basis_tune2": ("legacy", "basis-scaling era, provenance unverified"),
    "pjm_n6_tuned": ("legacy", "mix-ratio LMP scaling era"),
    "pjm_tune5_2025": ("structural", "fuller unit-level CAMPD outages"),
    "pjm_2_hydro_ps": ("structural", "LP budget hydro + pumped storage + OTHER must-run injection"),
    "pjm_3_tune": ("structural", "PS throughput adder (reserve reduced form) mixed with curve moves"),
    "pjm_4_gasmonthly": ("structural", "measured EIA-923 ISO-monthly delivered gas"),
    "pjm_5_coalcommit": ("pure", "multiplier moves only (note + clean git)"),
    "pjm_6_ccpeak": ("pure", "multiplier moves only (note + clean git)"),
    "pjm_7_ct": ("pure", "multiplier moves only (note + clean git)"),
    "pjm_8_outages": ("structural", "full-footprint CAMPD outage refresh (curves unchanged)"),
    "pjm_9_chp_solar": ("structural", "CHP steam floors + sector BTM for PJM cogens"),
}

# Bundles older than this per-ISO timestamp are "legacy" unless REGISTRY or
# --include-pair says otherwise: the model changed too much since (storage,
# BTM, fuel-cost, demand fixes) for their sensitivities to describe the
# current code. ERCOT's window opens at Run-58 (the verified candidate pairs
# start at Run-60 -> Run-61); PJM's at the pjm_2.. tuning sequence.
ERA_START = {"ERCOT": "2026-06-07", "PJM": "2026-06-09"}

# Words in a model_changes_note that suggest a structural (non-curve) change;
# used only for runs absent from REGISTRY. Matches are case-insensitive.
STRUCTURAL_NOTE_HINTS = (
    "fix", "append", "reclassif", "re-base", "rebase", "breakout", "measured",
    "parquet", "refresh", "overlay", "btm", "pull-out", "alignment",
    "storage fleet", "heat rate", "hr basis", "steam-floor", "outage",
)

# Representative base heat rates (MMBtu/MWh) per class for the merit-order
# adjacency check — midpoints of config.constants.HEAT_RATE_BINS vintages.
# Approximate by design: the check is qualitative (which bands share a price
# range), not quantitative.
CLASS_BASE_HR = {
    "CC_REGULAR": 7.0, "CC_CHP": 7.0, "CT_PEAKER": 10.5, "CT_CHP": 10.0,
    "ST_GAS": 10.4, "ST_CHP": 10.4, "COAL_LIGNITE": 10.4, "COAL_PRB": 10.4,
    "COAL_BIT": 10.0, "COAL_SUB": 10.2, "COAL_WC": 10.8, "COAL": 10.2,
}
ISO_STATES = {
    "ERCOT": {"TX"},
    "PJM": {"PA", "NJ", "MD", "DE", "OH", "WV", "VA", "KY", "IL", "IN",
            "MI", "NC", "TN", "DC"},
}


@dataclass
class Bundle:
    name: str
    path: Path
    iso: str
    timestamp: str
    years: list[int]
    curves: dict[str, dict[str, float]]
    note: str
    sha: str
    scenario: dict = field(default_factory=dict, repr=False)
    totals: pd.DataFrame | None = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# Discovery + class totals
# ---------------------------------------------------------------------------

def discover_bundles(root: Path) -> list[Bundle]:
    """All bundles under root with resolved curves and dispatch parquet."""
    out = []
    for d in sorted(root.iterdir()):
        cfg_path = d / "run_config.json"
        if not d.is_dir() or not cfg_path.exists():
            continue
        try:
            cfg = json.loads(cfg_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        sc = cfg.get("scenario_config", {})
        curves = sc.get("offer_curve_by_group") or {}
        disp = sorted((d / "dispatch").glob("*_P1.parquet"))
        if not curves or not disp or not (d / "eia923.parquet").exists():
            continue
        meta = {}
        if (d / "meta.json").exists():
            try:
                meta = json.loads((d / "meta.json").read_text())
            except (json.JSONDecodeError, OSError):
                pass
        git = cfg.get("git") or {}
        out.append(Bundle(
            name=d.name, path=d,
            iso=meta.get("iso") or sc.get("iso") or "?",
            timestamp=meta.get("timestamp") or cfg.get("timestamp") or "",
            years=sorted(int(f.name.split("_")[0]) for f in disp),
            curves=curves,
            note=str(cfg.get("model_changes_note") or ""),
            sha=git.get("sha") or meta.get("git_sha") or "",
            scenario={k: v for k, v in sc.items()
                      if k != "offer_curve_by_group"},
        ))
    return sorted(out, key=lambda b: b.timestamp)


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def class_totals(b: Bundle, cache: dict) -> pd.DataFrame:
    """Per (year, klass): model TWh (grid + BTM add-back) and EIA-923 TWh.

    Mirrors scripts/compare_runs_classes.py. Thermal response classes are the
    upper-case klass values in dispatch (excluding OTHER). Bundles without
    btm.parquet (older PJM format) get btm_twh=0 — pair deltas stay valid as
    long as BTM config didn't change inside the pair, which pure pairs satisfy.
    """
    if b.totals is not None:
        return b.totals
    stamp = {f.name: [f.stat().st_mtime, f.stat().st_size]
             for f in sorted((b.path / "dispatch").glob("*_P1.parquet"))}
    ent = cache.get(b.name)
    if ent and ent.get("stamp") == stamp:
        b.totals = pd.DataFrame(ent["rows"])
        return b.totals

    e923 = pd.read_parquet(b.path / "eia923.parquet")
    btm_path = b.path / "btm.parquet"
    btm = pd.read_parquet(btm_path) if btm_path.exists() else None
    rows = []
    for f in sorted((b.path / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        year = int(disp["year"].iloc[0])
        grid = disp.groupby("klass", observed=True)["mw"].sum() / 1e6
        bt = {}
        if btm is not None:
            sl = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
            bt = dict(zip(sl["klass"], sl["btm_twh"]))
        bench = (e923[e923["year"] == year]
                 .groupby("klass", observed=True)["annual_mwh"].sum() / 1e6)
        klasses = sorted(k for k in grid.index
                         if isinstance(k, str) and k == k.upper() and k != "OTHER")
        for k in klasses:
            rows.append({
                "year": year, "klass": k,
                "model_twh": float(grid.get(k, 0.0)) + float(bt.get(k, 0.0)),
                "eia_twh": float(bench.get(k, 0.0)),
            })
    b.totals = pd.DataFrame(rows)
    cache[b.name] = {"stamp": stamp, "rows": rows}
    return b.totals


# ---------------------------------------------------------------------------
# Pair classification
# ---------------------------------------------------------------------------

def _git_pair_dirty(sha0: str, sha1: str) -> bool | None:
    """True if src/inputs/data differ between the shas; None if unresolvable."""
    if not sha0 or not sha1:
        return None
    if sha0 == sha1:
        return False
    try:
        r = subprocess.run(
            ["git", "diff", "--quiet", sha0, sha1, "--",
             "src/", "inputs/", "data/"],
            cwd=REPO, capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode in (0, 1):
        return r.returncode == 1
    return None  # sha not in local history


def _config_diff(b0: Bundle, b1: Bundle) -> list[str]:
    """scenario_config keys (curves excluded) that differ inside the pair."""
    return sorted(k for k in set(b0.scenario) | set(b1.scenario)
                  if b0.scenario.get(k) != b1.scenario.get(k))


def classify_pair(b0: Bundle, b1: Bundle) -> tuple[str, str]:
    """(status, reason) for the consecutive pair b0->b1."""
    cfg_diff = _config_diff(b0, b1)
    if b1.name in REGISTRY:
        status, reason = REGISTRY[b1.name]
        if status == "pure" and cfg_diff:
            return ("structural",
                    f"registry says pure but scenario_config differs "
                    f"({', '.join(cfg_diff[:4])}) — downgraded")
        return status, reason
    era = ERA_START.get(b1.iso)
    if era and b1.timestamp < era:
        return ("legacy",
                f"predates {b1.iso} analysis era ({era}) — model has since "
                "changed structurally")
    # Unknown (future) run: scenario-config equality + git diff + note hints.
    if cfg_diff:
        return ("structural",
                f"auto: scenario_config differs ({', '.join(cfg_diff[:4])})")
    dirty = _git_pair_dirty(b0.sha, b1.sha)
    hinted = [w for w in STRUCTURAL_NOTE_HINTS if w in b1.note.lower()]
    if dirty:
        return "structural", "auto: src/inputs/data differ between run shas"
    if hinted:
        return ("legacy",
                f"auto: note hints structural ({', '.join(hinted[:3])}) — "
                "add to REGISTRY after review")
    if dirty is False:
        return ("pure", "auto: scenario_config identical, clean git diff, "
                        "no structural note hints")
    return ("legacy",
            "auto: shas unresolvable and note inconclusive — add to REGISTRY")


@dataclass
class PairObs:
    b0: Bundle
    b1: Bundle
    status: str
    reason: str
    dmult: dict[tuple[str, str], float] = field(default_factory=dict)

    @property
    def label(self) -> str:
        return f"{self.b0.name} -> {self.b1.name}"


def curve_deltas(b0: Bundle, b1: Bundle, klasses: set[str]) -> dict:
    """{(class, band): Δmult} for classes actually present in dispatch."""
    out = {}
    for cls in sorted(set(b0.curves) & set(b1.curves) & klasses):
        for band in BANDS:
            v0, v1 = b0.curves[cls].get(band), b1.curves[cls].get(band)
            if v0 is None or v1 is None:
                continue
            d = round(float(v1) - float(v0), 6)
            if abs(d) > 1e-9:
                out[(cls, band)] = d
    return out


def build_pairs(bundles: list[Bundle], cache: dict,
                include: set[str], exclude: set[str]) -> list[PairObs]:
    side = [b for b in bundles if REGISTRY.get(b.name, ("",))[0] == "sidecar"]
    for b in side:
        print(f"  [sidecar   ] {b.name}: {REGISTRY[b.name][1]} — "
              "skipped from the pairing chain")
    bundles = [b for b in bundles if b not in side]
    pairs = []
    for b0, b1 in zip(bundles, bundles[1:]):
        if not set(b0.years) & set(b1.years):
            continue
        status, reason = classify_pair(b0, b1)
        if b1.name in include:
            status, reason = "pure", "forced via --include-pair"
        if b1.name in exclude:
            status, reason = "structural", "forced via --exclude-pair"
        p = PairObs(b0, b1, status, reason)
        if status in ("pure", "structural"):
            klasses = set(class_totals(b1, cache)["klass"])
            p.dmult = curve_deltas(b0, b1, klasses)
        pairs.append(p)
    return pairs


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------

def _ridge(X: np.ndarray, Y: np.ndarray, alpha: float) -> np.ndarray:
    """B (n_knobs × n_classes) minimizing ‖XB−Y‖² + λ‖B‖², λ trace-scaled."""
    lam = alpha * float(np.trace(X.T @ X)) / max(X.shape[1], 1)
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ Y)


def fit_year(pairs: list[PairObs], knobs: list[tuple[str, str]],
             klasses: list[str], year: int, alpha: float) -> pd.DataFrame:
    """Long-format S for one year, with jackknife stderr per cell."""
    rows_x, rows_y, used = [], [], []
    for p in pairs:
        t0 = p.b0.totals.set_index("klass")
        t1 = p.b1.totals.set_index("klass")
        t0 = t0[t0["year"] == year]
        t1 = t1[t1["year"] == year]
        if t0.empty or t1.empty:
            continue
        rows_x.append([p.dmult.get(k, 0.0) for k in knobs])
        rows_y.append([
            float(t1["model_twh"].get(c, 0.0)) - float(t0["model_twh"].get(c, 0.0))
            for c in klasses])
        used.append(p)
    if not used:
        return pd.DataFrame()
    X, Y = np.array(rows_x), np.array(rows_y)
    B = _ridge(X, Y, alpha)
    n = len(used)
    if n > 2:  # leave-one-pair-out jackknife
        Bs = np.stack([
            _ridge(np.delete(X, i, 0), np.delete(Y, i, 0), alpha)
            for i in range(n)])
        se = np.sqrt((n - 1) / n * ((Bs - Bs.mean(0)) ** 2).sum(0))
    else:
        se = np.full_like(B, np.nan)
    n_obs = (np.abs(X) > 1e-9).sum(0)

    rows = []
    for i, (cls, band) in enumerate(knobs):
        for j, in_cls in enumerate(klasses):
            coef, s = float(B[i, j]), float(se[i, j])
            if n_obs[i] >= 3 and np.isfinite(s) and abs(coef) > 2 * s:
                conf = "high"
            elif n_obs[i] >= 2 and (not np.isfinite(s) or abs(coef) > s):
                conf = "med"
            else:
                conf = "low"
            rows.append({
                "year": year, "out_class": cls, "band": band, "in_class": in_cls,
                "dTWh_per_unit_mult": round(coef, 4),
                "n_obs": int(n_obs[i]),
                "stderr": round(s, 4) if np.isfinite(s) else None,
                "confidence": conf,
            })
    return pd.DataFrame(rows)


def fit_iso(pairs: list[PairObs], alpha: float) -> pd.DataFrame:
    pure = [p for p in pairs if p.status == "pure" and p.dmult]
    if not pure:
        return pd.DataFrame()
    knobs = sorted({k for p in pure for k in p.dmult})
    klasses = sorted({k for p in pure for k in p.b1.totals["klass"]})
    years = sorted({y for p in pure for y in set(p.b0.years) & set(p.b1.years)})
    return pd.concat(
        [fit_year(pure, knobs, klasses, y, alpha) for y in years],
        ignore_index=True)


# ---------------------------------------------------------------------------
# Sanity anchors (ERCOT Run-72 -> Run-73; structural pair, sign check only)
# ---------------------------------------------------------------------------

def check_anchors(bundles: dict[str, Bundle], cache: dict) -> None:
    b0, b1 = bundles.get("Run-72"), bundles.get("Run-73")
    if not (b0 and b1):
        return
    t0 = class_totals(b0, cache).set_index(["year", "klass"])["model_twh"]
    t1 = class_totals(b1, cache).set_index(["year", "klass"])["model_twh"]
    d = (t1 - t0).round(2)
    print("\n--- Sanity anchors: Run-72 -> Run-73 (structural pair — "
          "qualitative sign checks only) ---")
    checks = [
        ("CT_PEAKER committed 1.30->1.10 lifts CT_PEAKER (expect ~+1.6/+2.1/+1.4)",
         [d.get((y, "CT_PEAKER"), 0) > 0 for y in (2023, 2024, 2025)]),
        ("ST_GAS falls nearly 1:1 (expect ~-1.7/-2.4/-2.0)",
         [d.get((y, "ST_GAS"), 0) < 0 for y in (2023, 2024, 2025)]),
        ("COAL_PRB committed/econ_low -0.10 lifts PRB (expect ~+0.7/+1.3 in 2023/24)",
         [d.get((y, "COAL_PRB"), 0) > 0 for y in (2023, 2024)]),
        ("COAL_LIGNITE falls (expect ~-0.7/-0.9 in 2023/24)",
         [d.get((y, "COAL_LIGNITE"), 0) < 0 for y in (2023, 2024)]),
    ]
    for label, oks in checks:
        print(f"  [{'PASS' if all(oks) else 'FAIL'}] {label}")
    for cls in ("CT_PEAKER", "ST_GAS", "COAL_PRB", "COAL_LIGNITE"):
        vals = [d.get((y, cls)) for y in (2023, 2024, 2025)]
        print(f"    {cls:<14} ΔTWh 23/24/25: "
              + " / ".join("n/a" if v is None else f"{v:+.2f}" for v in vals))


# ---------------------------------------------------------------------------
# Merit-order adjacency validation
# ---------------------------------------------------------------------------

def monthly_fuel_prices(iso: str, year: int) -> dict[str, tuple[float, float]]:
    """{fuel_group: (min, max) quantity-weighted monthly $/MMBtu} for the ISO."""
    if not FUEL_COSTS.exists():
        return {}
    df = pd.read_parquet(FUEL_COSTS)
    df = df[df["year"] == year]
    states = ISO_STATES.get(iso)
    if states:
        df = df[df["state"].isin(states)]
    out = {}
    for fuel, g in df.groupby("fuel_group"):
        m = g.groupby("month").apply(
            lambda x: np.average(x["price_per_mmbtu"], weights=x["quantity"])
            if x["quantity"].sum() else x["price_per_mmbtu"].mean(),
            include_groups=False)
        if len(m):
            out[fuel] = (float(m.min()), float(m.max()))
    return out


def band_offer_ranges(b: Bundle, year: int, klasses: list[str]) -> pd.DataFrame:
    """$/MWh offer range per class-band: mult × base HR × monthly fuel price."""
    fuel = monthly_fuel_prices(b.iso, year)
    rows = []
    for cls in klasses:
        curve, hr = b.curves.get(cls), CLASS_BASE_HR.get(cls)
        if not curve or not hr:
            continue
        grp = "Coal" if cls.startswith("COAL") else "Natural Gas"
        if grp not in fuel:
            continue
        pmin, pmax = fuel[grp]
        for band in PRICE_BANDS:
            mult = curve.get(band)
            if mult is None:
                continue
            rows.append({"class": cls, "band": band,
                         "lo": round(mult * hr * pmin, 2),
                         "hi": round(mult * hr * pmax, 2)})
    return pd.DataFrame(rows)


def price_mass(b: Bundle, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Demand-weighted hourly clearing prices + weights from system.parquet."""
    sysp = pd.read_parquet(b.path / "system.parquet",
                           columns=["year", "pass", "price", "demand"])
    sysp = sysp[(sysp["year"] == year) & (sysp["pass"] == "P1")]
    return sysp["price"].to_numpy(), sysp["demand"].to_numpy()


def adjacency_check(b: Bundle, S: pd.DataFrame, cache: dict) -> None:
    """Merit-order adjacency from one bundle vs the regression's couplings."""
    klasses = sorted(class_totals(b, cache)["klass"].unique())
    for year in b.years:
        ranges = band_offer_ranges(b, year, klasses)
        if ranges.empty:
            print(f"\n  {b.iso} {year}: no fuel-price data — adjacency check skipped")
            continue
        prices, w = price_mass(b, year)
        wtot = w.sum()
        ranges["price_mass_%"] = [
            round(100 * w[(prices >= lo) & (prices <= hi)].sum() / wtot, 1)
            for lo, hi in zip(ranges["lo"], ranges["hi"])]
        q = np.quantile(prices, [0.05, 0.25, 0.5, 0.75, 0.95])
        print(f"\n  {b.iso} {year} clearing price P5/P25/P50/P75/P95: "
              + " / ".join(f"${v:.0f}" for v in q))
        print("  Class-band offer ranges ($/MWh, mult × base HR × monthly "
              "fuel price) and share of demand-weighted hours priced inside:")
        print(ranges.to_string(index=False, col_space=8).replace("\n", "\n    "))

        # Substitution pairs: class-bands of different classes whose offer
        # ranges overlap where the price distribution actually has mass.
        adj: dict[tuple[str, str], float] = {}
        rec = ranges.to_dict("records")
        for i, a in enumerate(rec):
            for c in rec[i + 1:]:
                if a["class"] == c["class"]:
                    continue
                lo, hi = max(a["lo"], c["lo"]), min(a["hi"], c["hi"])
                if lo >= hi:
                    continue
                mass = 100 * w[(prices >= lo) & (prices <= hi)].sum() / wtot
                key = tuple(sorted((a["class"], c["class"])))
                adj[key] = max(adj.get(key, 0.0), mass)
        top = sorted(adj.items(), key=lambda kv: -kv[1])[:10]
        print("  Top merit-order adjacencies (max overlap mass, % of "
              "demand-weighted hours):")
        for (a, c), mass in top:
            print(f"    {a:<14} <-> {c:<14} {mass:5.1f}%")

        if S.empty:
            continue
        cross = S[(S["year"] == year) & (S["out_class"] != S["in_class"])
                  & (S["confidence"] != "low")]
        cross = cross.reindex(
            cross["dTWh_per_unit_mult"].abs().sort_values(ascending=False).index
        ).head(10)
        print("  Regression cross-couplings vs adjacency:")
        for _, r in cross.iterrows():
            key = tuple(sorted((r["out_class"], r["in_class"])))
            mass = adj.get(key, 0.0)
            verdict = "consistent" if mass > 1.0 else "REVIEW (no price overlap)"
            print(f"    {r['out_class']}.{r['band']} -> {r['in_class']}: "
                  f"{r['dTWh_per_unit_mult']:+.2f} TWh/unit "
                  f"[{r['confidence']}] — adjacency {mass:.1f}% -> {verdict}")


# ---------------------------------------------------------------------------
# Joint-move recipe
# ---------------------------------------------------------------------------

def solve_joint_move(S: pd.DataFrame, err: pd.DataFrame, ridge: float = 0.5,
                     cap: float = 0.15, min_obs: int = 2,
                     ) -> tuple[pd.Series, pd.DataFrame] | None:
    """min ‖S·Δm + err‖² + λ‖Δm‖² with |Δm| ≤ cap, price bands only.

    S: long-format Jacobian (one ISO). err: columns [year, klass, err_twh],
    model − EIA-923. Returns (Δm per knob, predicted residual per class-year).
    """
    S = S[(S["band"].isin(PRICE_BANDS)) & (S["n_obs"] >= min_obs)]
    if S.empty:
        return None
    knobs = sorted({(r.out_class, r.band)
                    for r in S.itertuples()})
    years = sorted(set(S["year"]) & set(err["year"]))
    klasses = sorted(set(S["in_class"]) & set(err["klass"]))
    if not years or not klasses:
        return None
    coef = S.set_index(["year", "out_class", "band", "in_class"])[
        "dTWh_per_unit_mult"]
    e = err.set_index(["year", "klass"])["err_twh"]
    A = np.array([[coef.get((y, c, bnd, k), 0.0) for (c, bnd) in knobs]
                  for y in years for k in klasses])
    b = np.array([e.get((y, k), 0.0) for y in years for k in klasses])

    lam = ridge * float(np.trace(A.T @ A)) / max(len(knobs), 1)
    L = float(np.linalg.norm(A, 2) ** 2 + lam)
    x = np.zeros(len(knobs))
    for _ in range(5000):  # projected gradient on the box constraint
        x = np.clip(x - (A.T @ (A @ x + b) + lam * x) / L, -cap, cap)
    dm = pd.Series(x, index=pd.MultiIndex.from_tuples(knobs))
    resid = A @ x + b
    pred = pd.DataFrame({
        "year": [y for y in years for _ in klasses],
        "klass": klasses * len(years),
        "err_now_twh": b.round(2), "err_pred_twh": resid.round(2)})
    return dm, pred


def run_errors(b: Bundle, cache: dict) -> pd.DataFrame:
    t = class_totals(b, cache)
    t["err_twh"] = t["model_twh"] - t["eia_twh"]
    return t[["year", "klass", "err_twh"]]


def print_recipe(iso: str, S: pd.DataFrame, target: Bundle, cache: dict,
                 ridge: float, cap: float) -> None:
    res = solve_joint_move(S, run_errors(target, cache), ridge=ridge, cap=cap)
    print(f"\n--- {iso} joint-move recipe (target: {target.name} errors; "
          f"ridge-regularized, |Δmult| ≤ {cap}) ---")
    if not (target.path / "btm.parquet").exists():
        print("  NOTE: target bundle has no btm.parquet — errors are "
              "grid-only vs EIA-923 totals (BTM add-back missing), so "
              "CHP-class targets are biased low.")
    if res is None:
        print("  not enough well-observed knobs (n_obs >= 2) to solve")
        return
    dm, pred = res
    moves = dm[dm.abs() > 0.005].sort_values(key=lambda s: -s.abs())
    if moves.empty:
        print("  no move recommended (errors already balanced or S too weak)")
    else:
        print("  Recommended Δmult per knob:")
        for (cls, band), v in moves.items():
            print(f"    {cls:<14} {band:<10} {v:+.3f}")
    pv = pred.pivot(index="klass", columns="year",
                    values=["err_now_twh", "err_pred_twh"])
    print("  Predicted class errors after the move (TWh, model − EIA-923):")
    print("    " + pv.to_string().replace("\n", "\n    "))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--iso", action="append",
                    help="restrict to ISO(s); default: every ISO discovered")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--ridge", type=float, default=0.05,
                    help="regression ridge alpha (trace-scaled)")
    ap.add_argument("--recipe-ridge", type=float, default=0.5,
                    help="joint-move solver ridge (heavier: small fits)")
    ap.add_argument("--cap", type=float, default=0.15,
                    help="per-step band-move cap for the joint-move recipe")
    ap.add_argument("--validate-run", action="append", default=[],
                    help="bundle name(s) for adjacency check + recipe target "
                         "(default: latest bundle per ISO)")
    ap.add_argument("--include-pair", action="append", default=[],
                    help="force-include the pair ending at this run name")
    ap.add_argument("--exclude-pair", action="append", default=[],
                    help="force-exclude the pair ending at this run name")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--no-recipe", action="store_true")
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args(argv)

    pd.set_option("display.width", 220)
    bundles = discover_bundles(args.root)
    if args.iso:
        bundles = [b for b in bundles if b.iso in args.iso]
    if not bundles:
        print(f"no calibration bundles with offer_curve_by_group under {args.root}")
        return 1
    cache = {} if args.refresh_cache else _load_cache()
    by_name = {b.name: b for b in bundles}

    all_S = []
    for iso in sorted({b.iso for b in bundles}):
        seq = [b for b in bundles if b.iso == iso]
        print(f"\n{'=' * 78}\nISO {iso}: {len(seq)} bundles "
              f"({seq[0].name} … {seq[-1].name})")
        pairs = build_pairs(seq, cache,
                            set(args.include_pair), set(args.exclude_pair))
        print("\nConsecutive run pairs and classification:")
        for p in pairs:
            moved = (f"{len(p.dmult)} knob(s) moved" if p.dmult
                     else "no curve deltas" if p.status != "legacy" else "-")
            print(f"  [{p.status:<10}] {p.label:<44} {moved:<22} {p.reason}")

        pure = [p for p in pairs if p.status == "pure" and p.dmult]
        if not pure:
            print(f"\n  no verified pure-curve pairs for {iso} yet — the "
                  "Jacobian will populate as tuning backcasts accrue. "
                  "(Vet pairs above and add them to REGISTRY or use "
                  "--include-pair.)")
            continue
        for p in pure:  # materialize totals for both ends
            class_totals(p.b0, cache)

        S = fit_iso(pairs, args.ridge)
        S.insert(0, "iso", iso)
        all_S.append(S)

        print(f"\n--- {iso} sensitivity matrix "
              f"({len(pure)} pure pairs; sorted by |dTWh/unit|; "
              "cells with n_obs<2 or |coef|<stderr are low-confidence) ---")
        show = S[S["dTWh_per_unit_mult"].abs() > 0.05]
        show = show.reindex(
            show["dTWh_per_unit_mult"].abs().sort_values(ascending=False).index)
        print(show.drop(columns="iso").head(60).to_string(index=False))

        if iso == "ERCOT":
            check_anchors(by_name, cache)

        targets = ([by_name[n] for n in args.validate_run if n in by_name
                    and by_name[n].iso == iso] or [seq[-1]])
        if not args.no_validate:
            print(f"\n--- {iso} merit-order adjacency validation "
                  f"(bundle: {targets[0].name}) ---")
            adjacency_check(targets[0], S, cache)
        if not args.no_recipe:
            print_recipe(iso, S, targets[0], cache,
                         ridge=args.recipe_ridge, cap=args.cap)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache))
    if all_S:
        out = pd.concat(all_S, ignore_index=True)
        if args.out.exists():  # keep other ISOs' rows when run with --iso
            prev = pd.read_csv(args.out)
            out = pd.concat(
                [prev[~prev["iso"].isin(out["iso"])], out], ignore_index=True)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        out.sort_values(["iso", "year", "out_class", "band", "in_class"]
                        ).to_csv(args.out, index=False)
        print(f"\nwrote {len(out)} cells -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
