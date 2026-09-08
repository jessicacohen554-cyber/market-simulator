"""miso-245 phase 0 — ATTRIBUTE the drift between ``MISO_SEAM_LADDER_BY_YEAR`` and
its own derive at HEAD.  ZERO LP, read-only, repairs nothing.

Pre-registration:
``results/calibration/PREREG-miso245-attribute-the-incumbent-ladder-drift-2026-09-08.md``.
Every bar below is a LITERAL quoted from that document, and every predecessor
reference value is restated here as a literal so this probe adjudicates even if
the predecessor's artifact is missing (handoff process requirement).

THE OBJECT.  miso-244 established on a pre-registered rule that the one-cent gap
at three of the 192 committed entries is ``V-NOT-A-TIE`` (``t_max`` 0.0049998
against a 1e-4 tie bar) and that the ESTIMATOR family is eliminated, leaving the
SAMPLE as what moved -- but it was barred by its own PREREG 2.4 from naming the
cause.  This probe runs the one-line test miso-244 handed forward.

THE HYPOTHESIS AND ITS RULE (PREREG 2.2, fixed before any number existed).  If
the committed table came from this estimator on a marginally different SAMPLE,
each mismatching entry's committed value is reachable by perturbing THAT ENTRY'S
OWN integer exceedance/depth COUNT by at most +-1 hour out of 8,760, holding
estimator, price series, row set and every other entry fixed:

    m_j = min { |D| : D integer, 0 <= c_j + D <= n_j,
                round(v_j(D), 2) == committed_j },   +inf if none
    M   = max_j m_j over the three mismatching entries

    A-CONFIRMED  iff M <= 1
    A-REFUTED    iff M >= 2   (an infeasible m_j counts as +inf)

GATED: G-RAW / G-QUANT / G-COUNT / G-REPRO / G-LOC / G-DIR (instrument +
provenance), and M -> VERDICT.
REPORTED, NEVER GATED: R-1 per-entry m_j and signed delta; R-2 the flip distance
f_j for all 192 entries with the three mismatches' rank and separation; R-3 the
degenerate-run census behind entry 3; R-4 the clamp census under perturbation;
R-5 the price-side counterpart (a RESTATEMENT of miso-244's published t_j, not a
measurement); P-1 the source-data provenance reading (no decision rule attached).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/_miso245_ladder_drift_attribution_phase0.json"
YEARS = (2023, 2024, 2025)
SEAMS = ("PJM", "SPP", "South", "Manitoba")
SIDES = ("import", "export")

# ---- BARS, quoted as literals from the PREREG -------------------------------
ATTRIB_BAR = 1  # 2.2: A-CONFIRMED iff M <= 1
QUANT_BAR = 1e-12  # 2.1 G-QUANT
COUNT_BAR = 1e-6  # 2.1 G-COUNT, distance from an integer
REPRO_BAR = 1e-9  # 2.1 G-REPRO
CENT = 5e-9  # 2-dp equality tolerance

# ---- PREDECESSOR REFERENCE VALUES, restated as literals ---------------------
# miso-244 D-3 (_miso244_incumbent_ladder_cent_phase0.json reported.D3_...):
REF_MISMATCHES = [
    {
        "year": 2023,
        "seam": "PJM",
        "side": "import",
        "band": 5,
        "committed": 27.86,
        "rounded_head": 27.87,
        "t": 0.001182258684,
        "expected_sign": +1,  # import, raw > committed => value must FALL => c up
    },
    {
        "year": 2023,
        "seam": "South",
        "side": "export",
        "band": 4,
        "committed": 27.69,
        "rounded_head": 27.70,
        "t": 0.001280358153,
        "expected_sign": -1,  # export, raw > committed => value must FALL => c down
    },
    {
        "year": 2024,
        "seam": "South",
        "side": "export",
        "band": 5,
        "committed": 23.77,
        "rounded_head": 23.76,
        "t": 0.004999771118,
        "expected_sign": +1,  # export, raw < committed => value must RISE => c up
    },
]
# miso-244 D-1' (same JSON, reported.D1p_tie_mechanism), and PREREG F5's counts:
REF_D1P = [
    {
        "n": 8760,
        "q": 0.3818493150684932,
        "lo_index": 3344,
        "frac": 0.618150685,
        "x_lo": 27.860000610351562,
        "x_hi": 27.8700008392334,
        "value": 27.866182258684344,
        "count": 5415,
    },
    {
        "n": 8760,
        "q": 0.37203196347031964,
        "lo_index": 3258,
        "frac": 0.627968037,
        "x_lo": 27.690000534057617,
        "x_hi": 27.700000762939453,
        "value": 27.69628035815339,
        "count": 3259,
    },
    {
        "n": 8760,
        "q": 0.34748858447488584,
        "lo_index": 3043,
        "frac": 0.652511416,
        "x_lo": 23.760000228881836,
        "x_hi": 23.760000228881836,
        "value": 23.760000228881836,
        "count": 3044,
    },
]


def _load_derive_module():
    """Import the derive script as a module (reading its ESTIMATOR, not a label)."""
    script = REPO / "scripts/data/derive_miso_seam_ladders.py"
    spec = importlib.util.spec_from_file_location("_miso245_derive", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _q_linear(xs_sorted: np.ndarray, q: np.ndarray) -> np.ndarray:
    """``np.quantile(x, q, method='linear')`` on a PRE-SORTED array, vectorised.

    The estimate sits at ``h = q * (n - 1)`` and interpolates the two adjacent
    order statistics.  G-QUANT asserts this reproduces ``np.quantile`` at the
    unperturbed position for all 192 entries, so a divergence fails loudly
    instead of silently mis-stating the attribution statistic.
    """
    n = xs_sorted.size
    h = np.asarray(q, dtype=float) * (n - 1)
    lo = np.clip(np.floor(h).astype(np.int64), 0, n - 1)
    hi = np.minimum(lo + 1, n - 1)
    return xs_sorted[lo] + (h - lo) * (xs_sorted[hi] - xs_sorted[lo])


def _raw_one(da: np.ndarray, flow: np.ndarray, spec, eps: float) -> dict:
    """Replicate ``_derive_one`` and return the UNROUNDED bands + the counts.

    Byte-for-byte the estimator in ``scripts/data/derive_miso_seam_ladders.py``:
    the same midpoint-depth grid, the same Q-Q duration coupling, the same
    same-seam no-wash clamp taken off the UNROUNDED import list.
    """
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
    mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step
    exceed_i = [float((flow > m).mean()) for m in mids]
    depth_e = [float((flow < -m).mean()) for m in mids]
    imp = [float(np.quantile(da, 1.0 - e)) for e in exceed_i]
    exp = [float(np.quantile(da, d)) for d in depth_e]
    lim = min(imp) - eps
    clamped = [False] * len(exp)
    for k, s in enumerate(exp):
        if s > lim:
            clamped[k] = True
            exp[k] = lim
    return {
        "import": imp,
        "export": exp,
        "mids": [float(m) for m in mids],
        "exceed_import": exceed_i,
        "depth_export": depth_e,
        "clamped_export": clamped,
        "clamp_lim": float(lim),
    }


def _seam_samples(g: pd.DataFrame) -> dict:
    """The per-seam (da, flow, spec) row sets ``derive()`` itself builds."""
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_MANITOBA_SEAM_SPEC,
    )

    out = {}
    g3 = g.dropna(subset=["da"] + [n.name for n in INTERFACE_NEIGHBORS["MISO"]])
    da3 = g3["da"].to_numpy(dtype=float)
    for spec in INTERFACE_NEIGHBORS["MISO"]:
        out[spec.name] = (da3, g3[spec.name].to_numpy(dtype=float), spec)
    gm = g.dropna(subset=["da", MISO_MANITOBA_SEAM_SPEC.name])
    out[MISO_MANITOBA_SEAM_SPEC.name] = (
        gm["da"].to_numpy(dtype=float),
        gm[MISO_MANITOBA_SEAM_SPEC.name].to_numpy(dtype=float),
        MISO_MANITOBA_SEAM_SPEC,
    )
    return out


def _perturbed_curve(
    xs_sorted: np.ndarray, count: int, n: int, side: str, clamp_lim: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(deltas, rounded_values)`` over every feasible integer nudge.

    Exactly one knob moves: the entry's own integer duration count.  The price
    series, the row set, the sorted order statistics and every other entry are
    held fixed, and the export side is passed through the estimator's own
    same-seam no-wash clamp computed on the UNPERTURBED import list.
    """
    deltas = np.arange(-count, n - count + 1, dtype=np.int64)
    share = (count + deltas) / float(n)
    q = (1.0 - share) if side == "import" else share
    vals = _q_linear(xs_sorted, q)
    if side == "export":
        vals = np.minimum(vals, clamp_lim)
    return deltas, np.round(vals, 2)


def _min_abs_delta_to(target: float, deltas: np.ndarray, rounded: np.ndarray) -> dict:
    """Minimal |delta| reaching ``target`` (2 dp), with its signed value."""
    hit = np.flatnonzero(np.abs(rounded - target) < CENT)
    if hit.size == 0:
        return {"m": None, "signed_delta": None, "feasible": False}
    d = deltas[hit]
    j = int(np.argmin(np.abs(d)))
    return {"m": int(abs(d[j])), "signed_delta": int(d[j]), "feasible": True}


def _flip_distance(deltas: np.ndarray, rounded: np.ndarray, base: float) -> int | None:
    """Minimal |delta| >= 1 that changes the entry's rounded cent at all."""
    moved = np.flatnonzero((np.abs(rounded - base) >= CENT) & (deltas != 0))
    if moved.size == 0:
        return None
    return int(np.min(np.abs(deltas[moved])))


def _provenance(path: Path) -> dict:
    """P-1: the on-disk vintage record of one source parquet. REPORTED-ONLY."""
    rec: dict = {"path": str(path.relative_to(REPO)), "exists": path.exists()}
    if not path.exists():
        return rec
    df = pd.read_parquet(path)
    rec["rows"] = int(len(df))
    rec["columns"] = {c: str(df[c].dtype) for c in df.columns}
    idx = df.index
    if isinstance(idx, pd.MultiIndex) and "year" in (idx.names or []):
        yrs = sorted({int(v) for v in idx.get_level_values("year")})
    elif "year" in df.columns:
        yrs = sorted({int(v) for v in df["year"]})
    else:
        yrs = []
    rec["years"] = yrs
    for sib in ("README.md", "SHA256SUMS.txt"):
        f = path.parent / sib
        rec[sib] = {
            "exists": f.exists(),
            "bytes": (f.stat().st_size if f.exists() else 0),
        }
    try:
        log = subprocess.run(
            [
                "git",
                "log",
                "--no-merges",
                "--format=%h %ad %s",
                "--date=short",
                "--",
                str(path.relative_to(REPO)),
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
        )
        rec["git_log_no_merges"] = [ln for ln in log.stdout.splitlines() if ln][:10]
    except Exception as exc:  # pragma: no cover - provenance read is best effort
        rec["git_log_no_merges"] = [f"unavailable: {exc}"]
    return rec


def main() -> None:
    from market_sim.config.interchange_config import MISO_SEAM_LADDER_BY_YEAR

    dm = _load_derive_module()
    eps = float(dm.NO_WASH_EPS)
    g_all = dm.load_joined()

    report: dict = {
        "probe": (
            "miso-245 phase 0 — attribute the drift between "
            "MISO_SEAM_LADDER_BY_YEAR and its own derive at HEAD"
        ),
        "prereg": (
            "results/calibration/"
            "PREREG-miso245-attribute-the-incumbent-ladder-drift-2026-09-08.md"
        ),
        "keeper": "2026-09-07-miso-243-spp-pairing",
        "zero_lp": True,
        "read_only": True,
        "repairs_nothing": True,
        "queue_item": "the handoff's RECOMMENDED item (miso-244 §7.1's named successor)",
        "price_basis": (
            "incumbent ladder anchor = measured Indiana-hub DA "
            "(actual_lmp_hourly_MISO.parquet 'da', stored float32); row sets = the "
            "derive's own per-seam dropna. No model basis and no residual enters any bar."
        ),
        "bars": {
            "attribution_bar_M": ATTRIB_BAR,
            "quant_bar": QUANT_BAR,
            "count_bar": COUNT_BAR,
            "repro_bar": REPRO_BAR,
            "NO_WASH_EPS": eps,
        },
        "gates": {},
        "reported": {},
    }
    fails: list[str] = []

    # ========================= per-year raw capture ==========================
    raws: dict[int, dict] = {}
    derived: dict[int, dict] = {}
    samples: dict[int, dict] = {}
    for year in YEARS:
        g = g_all.loc[[year]]
        out, _notes = dm.derive(g)
        derived[year] = out
        samples[year] = _seam_samples(g)
        raws[year] = {
            name: _raw_one(da, flow, spec, eps)
            for name, (da, flow, spec) in samples[year].items()
        }

    # ---- G-RAW: instrument validity (round(raw,2) == derive(), all 192) ------
    graw = {"max_abs_delta": 0.0, "PASS": True}
    for year in YEARS:
        for seam in SEAMS:
            for side in SIDES:
                r = np.round(np.asarray(raws[year][seam][side], float), 2)
                d = np.asarray(derived[year][seam][side], float)
                graw["max_abs_delta"] = max(
                    graw["max_abs_delta"], float(np.max(np.abs(r - d)))
                )
    graw["PASS"] = bool(graw["max_abs_delta"] < 1e-9)
    graw["max_abs_delta"] = round(graw["max_abs_delta"], 12)
    report["gates"]["G_RAW"] = graw
    if not graw["PASS"]:
        fails.append("G-RAW")

    # ---- G-QUANT + G-COUNT: the vectorised quantile and the integer counts ---
    gq = {"max_abs_delta": 0.0, "n_entries": 0, "PASS": True}
    gc = {
        "max_distance_from_integer": 0.0,
        "n_entries": 0,
        "reference_counts": [d["count"] for d in REF_D1P],
        "recovered_counts": [],
        "PASS": True,
    }
    entries: list[dict] = []
    for year in YEARS:
        for seam in SEAMS:
            da, flow, _spec = samples[year][seam]
            xs = np.sort(np.asarray(da, dtype=float))
            n = int(xs.size)
            r = raws[year][seam]
            for side in SIDES:
                shares = r["exceed_import"] if side == "import" else r["depth_export"]
                for k in range(len(shares)):
                    share = float(shares[k])
                    q = (1.0 - share) if side == "import" else share
                    cf = share * n
                    c = int(round(cf))
                    gc["max_distance_from_integer"] = max(
                        gc["max_distance_from_integer"], abs(cf - c)
                    )
                    gc["n_entries"] += 1
                    mine = float(_q_linear(xs, np.array([q]))[0])
                    ref = float(np.quantile(xs, q))
                    gq["max_abs_delta"] = max(gq["max_abs_delta"], abs(mine - ref))
                    gq["n_entries"] += 1
                    entries.append(
                        {
                            "year": year,
                            "seam": seam,
                            "side": side,
                            "band": k + 1,
                            "n": n,
                            "count": c,
                            "q": q,
                            "committed": float(
                                MISO_SEAM_LADDER_BY_YEAR[year][seam][side][k]
                            ),
                            "raw_head": float(r[side][k]),
                            "clamp_lim": float(r["clamp_lim"]),
                        }
                    )
    gq["PASS"] = bool(gq["max_abs_delta"] <= QUANT_BAR and gq["n_entries"] == 192)
    gq["max_abs_delta"] = round(gq["max_abs_delta"], 15)
    report["gates"]["G_QUANT"] = gq
    if not gq["PASS"]:
        fails.append("G-QUANT")

    # ---- G-LOC: exactly the three published mismatches, nowhere else --------
    mism = [e for e in entries if abs(round(e["raw_head"], 2) - e["committed"]) >= CENT]
    loc_ok = len(mism) == len(REF_MISMATCHES)
    for got, ref in zip(mism, REF_MISMATCHES):
        loc_ok &= (
            got["year"] == ref["year"]
            and got["seam"] == ref["seam"]
            and got["side"] == ref["side"]
            and got["band"] == ref["band"]
            and abs(got["committed"] - ref["committed"]) < CENT
            and abs(round(got["raw_head"], 2) - ref["rounded_head"]) < CENT
        )
    report["gates"]["G_LOC"] = {
        "n_mismatching": len(mism),
        "reference": [
            f"{r['year']} {r['seam']} {r['side']} band {r['band']}"
            for r in REF_MISMATCHES
        ],
        "measured": [
            f"{m['year']} {m['seam']} {m['side']} band {m['band']}" for m in mism
        ],
        "PASS": bool(loc_ok),
    }
    if not loc_ok:
        fails.append("G-LOC")

    gc["recovered_counts"] = [m["count"] for m in mism]
    gc["PASS"] = bool(
        gc["max_distance_from_integer"] <= COUNT_BAR
        and gc["n_entries"] == 192
        and gc["recovered_counts"] == gc["reference_counts"]
    )
    gc["max_distance_from_integer"] = round(gc["max_distance_from_integer"], 12)
    report["gates"]["G_COUNT"] = gc
    if not gc["PASS"]:
        fails.append("G-COUNT")

    # ---- G-REPRO: reproduce miso-244's published D-1' record ----------------
    grep = {"detail": [], "PASS": True}
    for got, ref in zip(mism, REF_D1P):
        xs = np.sort(np.asarray(samples[got["year"]][got["seam"]][0], dtype=float))
        n = xs.size
        h = got["q"] * (n - 1)
        lo = int(np.floor(h))
        hi = min(lo + 1, n - 1)
        obs = {
            "n": int(n),
            "q": float(got["q"]),
            "lo_index": lo,
            "frac": float(h - lo),
            "x_lo": float(xs[lo]),
            "x_hi": float(xs[hi]),
            "value": float(xs[lo] + (h - lo) * (xs[hi] - xs[lo])),
        }
        ok = (
            obs["n"] == ref["n"]
            and obs["lo_index"] == ref["lo_index"]
            and abs(obs["q"] - ref["q"]) <= REPRO_BAR
            and abs(obs["frac"] - ref["frac"]) <= REPRO_BAR
            and abs(obs["x_lo"] - ref["x_lo"]) <= REPRO_BAR
            and abs(obs["x_hi"] - ref["x_hi"]) <= REPRO_BAR
            and abs(obs["value"] - ref["value"]) <= REPRO_BAR
        )
        grep["detail"].append(
            {
                "entry": f"{got['year']} {got['seam']} {got['side']} band {got['band']}",
                "observed": {
                    k: (round(v, 12) if isinstance(v, float) else v)
                    for k, v in obs.items()
                },
                "reference": ref,
                "PASS": bool(ok),
            }
        )
        grep["PASS"] &= bool(ok)
    report["gates"]["G_REPRO"] = grep
    if not grep["PASS"]:
        fails.append("G-REPRO")

    # ============ THE ATTRIBUTION STATISTIC (PREREG §2.2) ====================
    # R-2 needs the flip distance for ALL 192 entries, so the perturbed curve is
    # built once per entry and both statistics are read off it.
    sorted_da: dict[tuple[int, str], np.ndarray] = {}
    for year in YEARS:
        for seam in SEAMS:
            sorted_da[(year, seam)] = np.sort(
                np.asarray(samples[year][seam][0], dtype=float)
            )

    clamp_binds_anywhere = False
    for e in entries:
        xs = sorted_da[(e["year"], e["seam"])]
        deltas, rounded = _perturbed_curve(
            xs, e["count"], e["n"], e["side"], e["clamp_lim"]
        )
        base = float(np.round(e["raw_head"], 2))
        e["f"] = _flip_distance(deltas, rounded, base)
        reach = _min_abs_delta_to(e["committed"], deltas, rounded)
        e["m"] = reach["m"]
        e["signed_delta"] = reach["signed_delta"]
        e["reach_feasible"] = reach["feasible"]
        if e["side"] == "export":
            _d, raw_unclamped = (
                deltas,
                _q_linear(xs, (e["count"] + deltas) / float(e["n"])),
            )
            if bool(np.any(raw_unclamped > e["clamp_lim"])):
                clamp_binds_anywhere = True

    mism_e = [
        e for e in entries if abs(round(e["raw_head"], 2) - e["committed"]) >= CENT
    ]
    m_vals = [(float("inf") if e["m"] is None else float(e["m"])) for e in mism_e]
    M = max(m_vals) if m_vals else float("inf")
    verdict = "A-CONFIRMED" if M <= ATTRIB_BAR else "A-REFUTED"
    report["gates"]["VERDICT"] = {
        "rule": (
            "A-CONFIRMED iff M <= 1, where M = max over the mismatching entries of "
            "the minimal |delta| in integer duration-count hours that makes the "
            "frozen estimator return the committed cent, holding estimator, price "
            "series, row set and every other entry fixed (PREREG §2.2, fixed before "
            "any number existed). An infeasible m_j counts as +inf."
        ),
        "n_mismatching": len(mism_e),
        "m_by_entry": [
            {
                "entry": f"{e['year']} {e['seam']} {e['side']} band {e['band']}",
                "count": e["count"],
                "n": e["n"],
                "m_hours": e["m"],
                "signed_delta_hours": e["signed_delta"],
                "feasible": e["reach_feasible"],
            }
            for e in mism_e
        ],
        "M": (None if M == float("inf") else int(M)),
        "bar": ATTRIB_BAR,
        "VERDICT": verdict,
    }

    # ---- G-DIR: the reaching perturbation carries the sign monotonicity needs
    gdir = {"detail": [], "PASS": True}
    for e, ref in zip(mism_e, REF_MISMATCHES):
        sd = e["signed_delta"]
        ok = sd is None or (np.sign(sd) == ref["expected_sign"])
        gdir["detail"].append(
            {
                "entry": f"{e['year']} {e['seam']} {e['side']} band {e['band']}",
                "expected_sign": ref["expected_sign"],
                "observed_signed_delta": sd,
                "PASS": bool(ok),
            }
        )
        gdir["PASS"] &= bool(ok)
    report["gates"]["G_DIR"] = gdir
    if not gdir["PASS"]:
        fails.append("G-DIR")

    # ---- R-1/R-5: per-entry magnitudes, count side and price side ----------
    report["reported"]["R1_R5_count_and_price_side"] = [
        {
            "entry": f"{e['year']} {e['seam']} {e['side']} band {e['band']}",
            "committed": e["committed"],
            "raw_head": round(e["raw_head"], 10),
            "count_c": e["count"],
            "n": e["n"],
            "m_hours_count_side": e["m"],
            "signed_delta_hours": e["signed_delta"],
            "m_share_of_year": (None if e["m"] is None else round(e["m"] / e["n"], 6)),
            "price_side_t_usd_per_mwh_RESTATED_FROM_miso244": ref["t"],
        }
        for e, ref in zip(mism_e, REF_MISMATCHES)
    ]

    # ---- R-2: the flip distance across all 192 entries ---------------------
    finite = [e for e in entries if e["f"] is not None]
    mism_f = [e["f"] for e in mism_e if e["f"] is not None]
    match_f = [
        e["f"] for e in finite if abs(round(e["raw_head"], 2) - e["committed"]) < CENT
    ]
    order = sorted(finite, key=lambda e: e["f"])
    ranks = {
        f"{e['year']} {e['seam']} {e['side']} band {e['band']}": i + 1
        for i, e in enumerate(order)
    }
    report["reported"]["R2_flip_distance"] = {
        "definition": (
            "minimal |delta| >= 1 hour of duration count that changes an entry's "
            "rounded cent at all; the same construction as m, applied to every entry"
        ),
        "n_entries_with_finite_f": len(finite),
        "f_by_mismatch": [
            {
                "entry": f"{e['year']} {e['seam']} {e['side']} band {e['band']}",
                "f_hours": e["f"],
                "rank_among_192": ranks.get(
                    f"{e['year']} {e['seam']} {e['side']} band {e['band']}"
                ),
            }
            for e in mism_e
        ],
        "max_f_over_mismatches": (max(mism_f) if mism_f else None),
        "min_f_over_matches": (min(match_f) if match_f else None),
        "separated": bool(mism_f and match_f and max(mism_f) < min(match_f)),
        "f_quantiles_over_matches": (
            {
                "p05": int(np.quantile(match_f, 0.05)),
                "p25": int(np.quantile(match_f, 0.25)),
                "p50": int(np.quantile(match_f, 0.50)),
                "p75": int(np.quantile(match_f, 0.75)),
                "p95": int(np.quantile(match_f, 0.95)),
            }
            if match_f
            else None
        ),
        "reading": (
            "DESCRIPTIVE ONLY (PREREG §2.4 R-2): it cannot move the verdict in "
            "either direction and is never used to argue past the +-1 bar."
        ),
    }

    # ---- R-3: the degenerate run behind entry 3 ----------------------------
    e3 = mism_e[2] if len(mism_e) > 2 else None
    if e3 is not None:
        xs3 = sorted_da[(e3["year"], e3["seam"])]
        h3 = e3["q"] * (xs3.size - 1)
        lo3 = int(np.floor(h3))
        x0 = float(xs3[lo3])
        run = np.flatnonzero(xs3 == x0)
        report["reported"]["R3_degenerate_run"] = {
            "entry": f"{e3['year']} {e3['seam']} {e3['side']} band {e3['band']}",
            "x_at_position": x0,
            "hours_at_exactly_that_price": int(run.size),
            "run_first_index": int(run.min()),
            "run_last_index": int(run.max()),
            "position_index": lo3,
            "hours_from_position_to_run_end": int(run.max() - lo3),
            "next_distinct_value_above": (
                float(xs3[run.max() + 1]) if run.max() + 1 < xs3.size else None
            ),
        }

    # ---- R-4: does the no-wash clamp ever bind under perturbation? ---------
    report["reported"]["R4_clamp_under_perturbation"] = {
        "clamp_binds_anywhere_in_any_scan": bool(clamp_binds_anywhere),
        "note": (
            "miso-244 D-4 measured ZERO clamp notes in any year at delta = 0; the "
            "clamp lim is held at its UNPERTURBED value throughout, per PREREG §2.2"
        ),
    }

    # ---- P-1: source-data provenance reading (REPORTED-ONLY, no rule) ------
    report["reported"]["P1_source_provenance"] = {
        "decision_rule": "NONE — read of the record; licenses nothing by itself",
        "interchange": _provenance(Path(dm.INTERCHANGE_PARQUET)),
        "lmp": _provenance(Path(dm.ACTUAL_LMP_PARQUET)),
    }

    report["FAILED_LEGS"] = fails
    report["ALL_GATED_LEGS_PASS"] = not fails
    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps(report["gates"], indent=1))
    print(json.dumps(report["reported"]["R1_R5_count_and_price_side"], indent=1))
    print(json.dumps(report["reported"]["R2_flip_distance"], indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
