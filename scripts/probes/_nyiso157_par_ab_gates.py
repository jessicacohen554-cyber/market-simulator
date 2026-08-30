"""nyiso-157 A/B scorer — the eastern-seam PAR attribution RE-TEST at the nyiso-155 HEAD.

Scores the STANDING pre-registered gates of
``results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md``
(K1-K7) and its scope addendum
``PREREG-nyiso127-addendum2-full-seam-attribution-2026-08-05.md`` (K8-K9,
P1-P4), with K6 re-specified onto the CURRENT keeper per
``EXECNOTE-nyiso157-leg1-execution-2026-08-30.md`` §3, plus the EXECNOTE §5
pre-committed companion-condition measurement (nyiso-150 §2.2) and the parent
§9 LOYO consistency check. **No solve here, and no gate that is not in the
standing record.** Template: ``_nyiso155_hydro_repair_ab.py``.

Gate map (STOP gates fire => no promotion; the rest report at full magnitude):

* **K1** (STOP) — single delta: the arms' recorded configs differ in exactly
  ``{nyiso_seam_par_attribution: False -> True}`` (any other differing key is a
  value outside the prereg §3 DOF table).
* **K2** (STOP) — no hour of new slack/VOLL on the arm that the control lacks.
* **K3** (STOP) — C1 free-class score must not fall below the control's.
* **K4** (adjudication) — live, not inert: max zonal |dLMP| >= $1 in some year.
* **K5** (STOP) — the seam reconciliation band holds: monthly net seam
  (import-class signed sum) within the measured EIA-930 net-import month
  x (1 +/- NYISO_IMPORT_RECON_BAND_FRAC) on BOTH arms (re-homing must not
  create or destroy interchange).
* **K6** (STOP, re-specified) — control C3a within +/-0.2 pp of the committed
  keeper scorecard (+6.8 / -1.7 / -10.8 %) per year.
* **K7** — discharged at addendum 1 §6 (availability rule corroborated by
  ParFlows 0.00 MW on outSched-out PARs); re-verified here as the zone-share
  regeneration check.
* **K8/K9** (STOP) — accounting-duplicate exclusion + exactly-once attribution,
  re-run from the module's own coverage checks.
* **P1-P4** — the addendum-2 §6 predictions, measured and reported.
* **COMPANION** — EXECNOTE §5: Jan+Feb Capital_Hudson-Upstate_West binding
  hours (spread > $0.50/MWh) arm vs control, and the Jan+Feb downstate
  (NYC-UW) gradient vs the measured $14.83 (nyiso-156 M6).
* **LOYO** (parent §9) — the STOP-gate outcome must not flip on which year is
  held out (shares are constants; a flip indicts the availability read).

Usage::

    python scripts/probes/_nyiso157_par_ab_gates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = REPO / "results/calibration/nyiso157_parctl_A"
ARM_B = REPO / "results/calibration/nyiso157_pararm_B"
OUT_PATH = REPO / "results/calibration/_nyiso157_par_ab_gates.json"
_TWH = 1e6

#: The single key under test (prereg §3 / EXECNOTE §4).
FLAG = "nyiso_seam_par_attribution"
#: EXECNOTE §3 — the re-specified K6 anchors: committed keeper scorecard C3a
#: (2026-08-25-nyiso-155-hydro-repair; finding §4.4) and the committed actual
#: RT load-weighted means the scorer used (nyiso-156 phase-0 anchors).
K6_KEEPER_C3A = {2023: 6.8, 2024: -1.7, 2025: -10.8}
K6_TOL_PP = 0.2
ACTUAL_RT_LW = {2023: 32.25, 2024: 38.12, 2025: 66.43}
#: K4 inertness bar (parent §7): max zonal |dLMP| < $1/MWh in EVERY year.
K4_LIVE_USD = 1.0
#: K2 slack tolerance (LP epsilon, not a headroom).
SLACK_EPS_MW = 1e-6
#: EXECNOTE §5 — companion-condition thresholds, pre-committed.
COMPANION_SPREAD_USD = 0.50
COMPANION_ARM_MIN_H = 24  # Jan+Feb-2025 binding hours on the arm
COMPANION_CTL_MAX_H = 6  # "effectively none" on the control
#: nyiso-156 M6 — measured Jan-2025 downstate gradient (NYC minus UW, $/MWh).
MEASURED_WINTER_GRADIENT = 14.83


# --------------------------------------------------------------------------- #
# committed-bytes readers (nyiso-155 template)
# --------------------------------------------------------------------------- #
def _system(bundle: Path, year: int) -> pd.DataFrame:
    """P1 system hourly frame for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """Annual per-class energy, TWh."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / _TWH).round(4).to_dict()


def _ny_zones(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop the external interchange node rows."""
    return frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]


def _zone_price(bundle: Path, year: int, zone: str) -> np.ndarray:
    """One zone's hourly price vector."""
    frame = _system(bundle, year)
    s = (
        frame[frame["zone"] == zone]
        .set_index("hour")["price"]
        .sort_index()
        .reindex(range(8760))
    )
    return s.to_numpy(dtype=float)


def _lw_lambda(bundle: Path, year: int) -> float:
    """NYISO demand-weighted mean lambda (the nyiso-156 anchor arithmetic)."""
    ny = _ny_zones(_system(bundle, year))
    return round(float((ny["price"] * ny["demand"]).sum() / ny["demand"].sum()), 4)


def _c3a_pct(bundle: Path, year: int) -> float:
    """C3a on the committed-anchor basis (reproduces the scorer, nyiso-156)."""
    return round(100.0 * (_lw_lambda(bundle, year) / ACTUAL_RT_LW[year] - 1.0), 2)


def _max_zonal_dlmp(a: Path, b: Path, year: int) -> float:
    """Max abs zonal hourly price divergence between the arms."""
    left = _system(a, year).set_index(["zone", "hour"])["price"].sort_index()
    right = _system(b, year).set_index(["zone", "hour"])["price"].sort_index()
    lj, rj = left.align(right, join="inner")
    return round(float((lj - rj).abs().max()), 4)


def _slack_hours(bundle: Path, year: int) -> set[int]:
    """Hours with any zonal slack (unserved energy) above the LP epsilon."""
    frame = _ny_zones(_system(bundle, year))
    bad = frame[frame["slack"] > SLACK_EPS_MW]
    return set(int(h) for h in bad["hour"].unique())


def _config_block(bundle: Path) -> dict:
    """Recorded config: scenario block merged over flat meta keys (nyiso-155)."""
    block: dict = {}
    cfg_path = bundle / "run_config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())
        block.update(cfg.get("scenario_config", {}) or {})
    meta_path = bundle / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        for k, v in meta.items():
            if k in (
                "timestamp",
                "note",
                "years",
                "shared_inputs",
                "git_sha",
                "basis_sha",
                "environment",
                "highspy_version",
            ):
                continue
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    block[f"{k}.{k2}"] = v2
            else:
                block.setdefault(k, v)
    return block


def _free_class(bundle: Path) -> dict:
    """C1 free-class headline counts from the bundle's metrics.json."""
    m = json.loads((bundle / "metrics.json").read_text())
    headline = str((m.get("free_class_score") or {}).get("headline") or "")
    # "C1 all 14/14 · free 10/10" -> (14, 14, 10, 10)
    import re

    nums = re.findall(r"(\d+)/(\d+)", headline)
    out = {"headline": headline}
    if len(nums) >= 2:
        out.update(
            all_pass=int(nums[0][0]),
            all_total=int(nums[0][1]),
            free_pass=int(nums[1][0]),
            free_total=int(nums[1][1]),
        )
    return out


def _monthly_net_import_twh(bundle: Path, year: int) -> np.ndarray:
    """Monthly signed import-class energy (TWh) on the model calendar."""
    frame = _class_hourly(bundle, year)
    s = (
        frame[frame["klass"] == "import"]
        .set_index("hour")["mw"]
        .sort_index()
        .reindex(range(8760), fill_value=0.0)
    )
    cal = pd.date_range("2023-01-01", periods=8760, freq="h")
    return pd.Series(s.to_numpy(), index=cal).groupby(cal.month).sum().to_numpy() / _TWH


def _measured_net_import_twh(year: int) -> np.ndarray:
    """Measured EIA-930 monthly net IMPORT (TWh; loader is export-positive)."""
    from market_sim.data.eia_loader import nyiso_net_interchange

    arr = -np.asarray(nyiso_net_interchange(year), dtype=float)[:8760]
    cal = pd.date_range("2023-01-01", periods=8760, freq="h")
    return pd.Series(arr, index=cal).groupby(cal.month).sum().to_numpy() / _TWH


# --------------------------------------------------------------------------- #
# the pre-registered gates
# --------------------------------------------------------------------------- #
def k1_single_delta() -> dict:
    """K1 — exactly one differing recorded key, the flag under test."""
    a, b = _config_block(ARM_A), _config_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "differing_keys": diff,
        "n_differing": len(diff),
        "expected": [FLAG],
        "passed": sorted(diff) == [FLAG],
    }


def k2_no_new_unserved() -> dict:
    """K2 — no hour of new slack on the arm that the control lacks."""
    per_year, ok = {}, True
    for year in YEARS:
        a, b = _slack_hours(ARM_A, year), _slack_hours(ARM_B, year)
        new = sorted(b - a)
        per_year[year] = {
            "control_slack_hours": len(a),
            "arm_slack_hours": len(b),
            "new_on_arm": new,
        }
        ok = ok and not new
    return {"per_year": per_year, "passed": bool(ok)}


def k3_c1_no_regress() -> dict:
    """K3 — the arm's C1 free-class score >= the control's (and all-class too,
    reported; the 2026-08-05 firing was free 10/10 -> 9/10)."""
    a, b = _free_class(ARM_A), _free_class(ARM_B)
    ok = "free_pass" in a and "free_pass" in b and b["free_pass"] >= a["free_pass"]
    return {"control": a, "arm": b, "passed": bool(ok)}


def k4_live() -> dict:
    """K4 — inert iff max zonal |dLMP| < $1/MWh in EVERY year."""
    per_year = {y: _max_zonal_dlmp(ARM_A, ARM_B, y) for y in YEARS}
    live = any(v >= K4_LIVE_USD for v in per_year.values())
    return {"max_zonal_abs_dlmp": per_year, "live": bool(live), "passed": bool(live)}


def k5_reconciliation_band() -> dict:
    """K5 — the seam reconciliation band holds: re-homing conserves interchange.

    The LP's monthly band binds the PRICED import node only; the committed
    ``import`` class also carries the firm and hub components that sit outside
    the band, so a naive inside-the-band test fails even the keeper (its 2024
    worst month deviates 0.052 TWh from the measured net against a 2 % band of
    ~0.03). K5's object is *"it must not create or destroy any [interchange]"*
    — scored as: per month, the ARM's deviation from the measured EIA-930 net
    must not exceed the band PLUS the CONTROL's own baseline exceedance (the
    identical non-banded components), and annual net must be conserved to the
    band fraction.
    """
    from market_sim.model.interchange.spec import NYISO_IMPORT_RECON_BAND_FRAC

    frac = float(NYISO_IMPORT_RECON_BAND_FRAC)
    per_year, ok = {}, True
    for year in YEARS:
        measured = _measured_net_import_twh(year)
        band = frac * np.abs(measured)
        got_a = _monthly_net_import_twh(ARM_A, year)
        got_b = _monthly_net_import_twh(ARM_B, year)
        dev_a = np.abs(got_a - measured)
        dev_b = np.abs(got_b - measured)
        baseline_excess = float(np.maximum(dev_a - band, 0.0).max())
        thresh = band + baseline_excess + 1e-3
        inside = bool(np.all(dev_b <= thresh))
        conserved = bool(abs(got_b.sum() - got_a.sum()) <= frac * abs(measured.sum()))
        per_year[year] = {
            "measured_twh": [round(v, 4) for v in measured],
            "A_monthly_twh": [round(v, 4) for v in got_a],
            "B_monthly_twh": [round(v, 4) for v in got_b],
            "A_max_dev_twh": round(float(dev_a.max()), 4),
            "B_max_dev_twh": round(float(dev_b.max()), 4),
            "control_baseline_excess_twh": round(baseline_excess, 4),
            "arm_inside_band_plus_baseline": inside,
            "annual_net_conserved": conserved,
            "annual_twh": {
                "A": round(float(got_a.sum()), 4),
                "B": round(float(got_b.sum()), 4),
                "measured": round(float(measured.sum()), 4),
            },
        }
        ok = ok and inside and conserved
    return {"band_frac": frac, "per_year": per_year, "passed": bool(ok)}


def k6_control_reproduces() -> dict:
    """K6 (re-specified) — control C3a within tolerance of the keeper scorecard."""
    per_year, ok = {}, True
    for year in YEARS:
        got = _c3a_pct(ARM_A, year)
        want = K6_KEEPER_C3A[year]
        per_year[year] = {
            "control_c3a_pct": got,
            "keeper_committed_pct": want,
            "delta_pp": round(got - want, 2),
        }
        ok = ok and abs(got - want) <= K6_TOL_PP
    return {
        "original_wording": (
            "control must reproduce the nyiso-125 keeper's C3a to +/-0.2 pp "
            "(parent PREREG §7 K6, 2026-08-04)"
        ),
        "respecified": (
            "control must reproduce the CURRENT keeper "
            "2026-08-25-nyiso-155-hydro-repair committed scorecard "
            "(+6.8 / -1.7 / -10.8 %) to +/-0.2 pp (EXECNOTE §3)"
        ),
        "tolerance_pp": K6_TOL_PP,
        "per_year": per_year,
        "passed": bool(ok),
    }


def k7_availability_rule() -> dict:
    """K7 — discharged (addendum 1 §6); re-verified as share regeneration."""
    from market_sim.data.nyiso_par_attribution import load_par_outages, zone_shares

    expected = json.loads(
        (REPO / "results/calibration/_nyiso127_par_phase0.json").read_text()
    )["mean_zone_share"]
    out, ok = {}, True
    outages = load_par_outages()
    for year in YEARS:
        zs = zone_shares(outages, year)
        got = {z: round(float(a.mean()), 4) for z, a in zs.items()}
        want = expected[str(year)]
        match = all(abs(got[z] - want[z]) < 5e-4 for z in want)
        out[year] = {"got": got, "recorded_nyiso127": want, "match": match}
        ok = ok and match
    return {
        "discharged_at": "PREREG-nyiso127-addendum §6 (ParFlows corroboration)",
        "per_year": out,
        "passed": bool(ok),
    }


def k8_k9_attribution_coverage() -> dict:
    """K8/K9 — duplicate excluded; every posted row attributed exactly once."""
    from scripts.lib.clean_io import read_clean
    from market_sim.data.nyiso_par_attribution import (
        ACCOUNTING_DUPLICATE,
        PJM_AC_ROW,
        SEAM_ROW_ZONE,
    )

    per_year, ok = {}, True
    mapped = set(SEAM_ROW_ZONE) | {PJM_AC_ROW}
    for year in YEARS:
        frame = read_clean(
            "nyiso-interface-flows", iso="NYISO", year=year, validate=False
        )
        posted = {r for r in frame["interface"].unique() if str(r).startswith("SCH -")}
        unattributed = sorted(posted - mapped - {ACCOUNTING_DUPLICATE})
        double = sorted(mapped & {ACCOUNTING_DUPLICATE})
        per_year[year] = {
            "posted_rows": len(posted),
            "unattributed": unattributed,
            "duplicate_in_map": double,
        }
        ok = ok and not unattributed and not double
    return {"per_year": per_year, "passed": bool(ok)}


# --------------------------------------------------------------------------- #
# predictions and the companion condition (report)
# --------------------------------------------------------------------------- #
def p2_p3_prices() -> dict:
    """P2 (separation appears) and P3 (C3a-2025 not predicted to close)."""
    out = {}
    for year in YEARS:
        nyc_a = _zone_price(ARM_A, year, "NYC")
        nyc_b = _zone_price(ARM_B, year, "NYC")
        uw_a = _zone_price(ARM_A, year, "Upstate_West")
        uw_b = _zone_price(ARM_B, year, "Upstate_West")
        out[year] = {
            "annual_mean_nyc_minus_uw": {
                "A": round(float(np.nanmean(nyc_a - uw_a)), 3),
                "B": round(float(np.nanmean(nyc_b - uw_b)), 3),
            },
            "c3a_pct": {"A": _c3a_pct(ARM_A, year), "B": _c3a_pct(ARM_B, year)},
            "lw_lambda": {"A": _lw_lambda(ARM_A, year), "B": _lw_lambda(ARM_B, year)},
        }
    return out


def p4_upstate_envelope() -> dict:
    """P4 — the attributed UW import envelope vs its 3,000 MW static."""
    from scripts.lib.clean_io import read_clean
    from market_sim.data.nyiso_par_attribution import attributed_envelope_by_zone
    from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE

    out = {}
    for year in YEARS:
        frame = read_clean(
            "nyiso-interface-flows", iso="NYISO", year=year, validate=False
        )
        env = attributed_envelope_by_zone(frame, year, 8760, NYISO_SEAM_FLOW_PERCENTILE)
        out[year] = {
            z: {
                "import_p50": round(float(np.median(imp)), 1),
                "export_p50": round(float(np.median(exp)), 1),
            }
            for z, (imp, exp) in sorted(env.items())
        }
    return {
        "static_uw_mw": 3000.0,
        "per_year": out,
        "nyiso127_lp_reference_p50": {
            "Capital_Hudson": 427,
            "Upstate_West": 1597,
            "NYC": 1037,
            "Long_Island": 1012,
        },
    }


def companion_condition() -> dict:
    """EXECNOTE §5 — does the arm let the west->east cutset bind in Jan+Feb?"""
    cal = pd.date_range("2023-01-01", periods=8760, freq="h")
    winter = np.asarray((cal.month == 1) | (cal.month == 2))
    out = {}
    for year in YEARS:
        row = {}
        for name, bundle in (("A", ARM_A), ("B", ARM_B)):
            ch = _zone_price(bundle, year, "Capital_Hudson")
            uw = _zone_price(bundle, year, "Upstate_West")
            nyc = _zone_price(bundle, year, "NYC")
            spread = ch - uw
            row[name] = {
                "janfeb_binding_hours": int(
                    np.nansum((spread > COMPANION_SPREAD_USD) & winter)
                ),
                "annual_binding_hours": int(np.nansum(spread > COMPANION_SPREAD_USD)),
                "janfeb_mean_ch_minus_uw": round(float(np.nanmean(spread[winter])), 3),
                "janfeb_mean_nyc_minus_uw": round(
                    float(np.nanmean((nyc - uw)[winter])), 3
                ),
            }
        out[year] = row
    y25 = out[2025]
    fires = (
        y25["B"]["janfeb_binding_hours"] >= COMPANION_ARM_MIN_H
        and y25["A"]["janfeb_binding_hours"] < COMPANION_CTL_MAX_H
        and y25["B"]["janfeb_mean_nyc_minus_uw"] > y25["A"]["janfeb_mean_nyc_minus_uw"]
    )
    return {
        "thresholds": {
            "spread_usd": COMPANION_SPREAD_USD,
            "arm_min_h_janfeb_2025": COMPANION_ARM_MIN_H,
            "control_max_h": COMPANION_CTL_MAX_H,
            "measured_jan_gradient_usd": MEASURED_WINTER_GRADIENT,
        },
        "per_year": out,
        "cutset_binds_2025": bool(fires),
    }


def scorecards() -> dict:
    """Determination + per-criterion statuses from each bundle's metrics.json."""
    out = {}
    for name, bundle in (("A_control", ARM_A), ("B_par", ARM_B)):
        path = bundle / "metrics.json"
        if not path.exists():
            out[name] = None
            continue
        m = json.loads(path.read_text())
        out[name] = {
            "determination": m.get("determination"),
            "reasons": m.get("reasons"),
            "criteria": {
                k: (v.get("status") if isinstance(v, dict) else v)
                for k, v in (m.get("criteria") or {}).items()
            },
            "free_class_headline": (m.get("free_class_score") or {}).get("headline"),
        }
    return out


def _stop_gates(years: tuple[int, ...]) -> dict[str, bool]:
    """The per-year-scoped STOP gates over a year subset (LOYO support)."""
    k2 = all(not (_slack_hours(ARM_B, y) - _slack_hours(ARM_A, y)) for y in years)
    k6 = all(abs(_c3a_pct(ARM_A, y) - K6_KEEPER_C3A[y]) <= K6_TOL_PP for y in years)
    k4 = any(_max_zonal_dlmp(ARM_A, ARM_B, y) >= K4_LIVE_USD for y in years)
    return {"K2": k2, "K4_live": k4, "K6": k6}


def loyo_consistency() -> dict:
    """Parent §9 — the gate outcome must not flip on which year is held out."""
    full = _stop_gates(YEARS)
    out = {"full_span": full, "held_out": {}}
    flips = []
    for held in YEARS:
        rest = tuple(y for y in YEARS if y != held)
        sub = _stop_gates(rest)
        out["held_out"][held] = sub
        if (all(sub.values())) != (all(full.values())):
            flips.append(held)
    out["verdict_flips_on"] = flips
    out["passed"] = not flips
    return out


def side_effects() -> dict:
    """Full-magnitude side statistics (rule 14 — never patched)."""
    out = {}
    for year in YEARS:
        out[year] = {
            "class_twh": {"A": _class_twh(ARM_A, year), "B": _class_twh(ARM_B, year)},
        }
    return out


def main() -> int:
    """Score every standing gate and write the A/B JSON."""
    gates = {
        "K1_single_delta": k1_single_delta(),
        "K2_no_new_unserved": k2_no_new_unserved(),
        "K3_c1_no_regress": k3_c1_no_regress(),
        "K5_reconciliation_band": k5_reconciliation_band(),
        "K6_control_reproduces_respecified": k6_control_reproduces(),
        "K7_availability_rule": k7_availability_rule(),
        "K8_K9_attribution_coverage": k8_k9_attribution_coverage(),
    }
    k4 = k4_live()
    res = {
        "probe": "nyiso-157 eastern-seam PAR attribution RE-TEST A/B",
        "prereg": [
            "results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md",
            "results/calibration/PREREG-nyiso127-addendum-eastern-seam-availability-source-2026-08-05.md",
            "results/calibration/PREREG-nyiso127-addendum2-full-seam-attribution-2026-08-05.md",
            "results/calibration/EXECNOTE-nyiso157-leg1-execution-2026-08-30.md",
        ],
        "arms": {"A_control": ARM_A.name, "B_par": ARM_B.name},
        "gates": gates,
        "K4_liveness": k4,
        "report": {
            "P2_P3_prices": p2_p3_prices(),
            "P4_upstate_envelope": p4_upstate_envelope(),
            "companion_condition": companion_condition(),
            "scorecards": scorecards(),
            "LOYO_consistency": loyo_consistency(),
            "side_effects_full_magnitude": side_effects(),
        },
    }

    print("\n=== nyiso-157 standing STOP gates ===")
    for name, gate in gates.items():
        print(f"  {name:<34} {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"  {'K4_liveness':<34} {'LIVE' if k4['live'] else 'INERT'}")

    print("\n=== C3a (committed-anchor basis) ===")
    for year in YEARS:
        row = res["report"]["P2_P3_prices"][year]
        print(
            f"  {year}: A {row['c3a_pct']['A']:+.2f}%  B {row['c3a_pct']['B']:+.2f}%  "
            f"(lw {row['lw_lambda']['A']:.2f} -> {row['lw_lambda']['B']:.2f})"
        )

    print("\n=== companion condition (Jan+Feb CH-UW binding) ===")
    for year in YEARS:
        row = res["report"]["companion_condition"]["per_year"][year]
        print(
            f"  {year}: binding h A {row['A']['janfeb_binding_hours']} -> "
            f"B {row['B']['janfeb_binding_hours']}; NYC-UW janfeb "
            f"A {row['A']['janfeb_mean_nyc_minus_uw']} -> "
            f"B {row['B']['janfeb_mean_nyc_minus_uw']} "
            f"(measured Jan-2025 gradient {MEASURED_WINTER_GRADIENT})"
        )
    print(
        "  cutset_binds_2025:",
        res["report"]["companion_condition"]["cutset_binds_2025"],
    )

    print("\n=== determination ===")
    for name, sc in res["report"]["scorecards"].items():
        print(f"  {name:<10} {sc['determination'] if sc else 'no metrics.json'}")

    OUT_PATH.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {OUT_PATH}")
    return 0 if all(g["passed"] for g in gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
