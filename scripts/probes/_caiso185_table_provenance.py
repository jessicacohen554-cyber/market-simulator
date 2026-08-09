"""caiso-185 P0-2 — provenance audit of the committed CC demonstrated-capability table.

Pre-registered in ``results/calibration/PRECHECK-caiso185-cc-reconcile-2026-08-09.md``
§3 (G-REPRO, three legs) and §4 (G-OVERCARRY). **READ-ONLY**: the deriver's selection is
recomputed in-process and compared against the committed
``data/raw/_processed-legacy/cc_capacity_reconcile_CAISO.csv``. Nothing is written to the
committed path — rule 23 ``[R-FROZEN-DERIVE]`` forbids a re-derive absent a cited
source-data change, so the audit must be able to answer "is it reproducible?" WITHOUT
producing the artifact.

Legs (PRECHECK §3):

* **R1 — VALUE.** ``campd_p999_mw`` recomputed from the CAMPD state extracts on disk for
  2023-2025 via the deriver's own ``_campd_p999_and_annual``.
* **R2 — MEMBERSHIP + MODE.** the full ``--mode both`` selection re-run at this head
  (``_model_cc_capacity`` on the current fleet, ``_CAP_MARGIN``, ``_MIN_DELTA``,
  ``_CAP_FEASIBLE_CF``, the pure-play screen), row set and mode compared.
* **R3 — CT-ONLY EXCLUSION.** ``_ct_only_codes`` re-run and compared against what the
  committed table's absences imply.

**G-REPRO**: a committed row passes iff re-emitted in the SAME mode with
``reconciled_mw`` within 0.5 %. ``current_mw`` / ``delta_pct`` drift is recorded but is
not a failure on its own (neither field is read by the hook, and drift there tracks the
CODE vintage, which rule 23 does not accept as a re-derive trigger).

**G-OVERCARRY** (PRECHECK §4, rule 11): every ``cap`` row beyond ``_CAP_MARGIN - 1``
must be attributed. ``current_mw`` is reconciled against the plant's own EIA-860
combined-cycle nameplate and net-summer sums, so a cap that is really compensating for a
fleet-loading / attribution defect is separated from a genuine ambient-rating gap.

Usage::

    python scripts/probes/_caiso185_table_provenance.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

# The deriver is the authority on its own selection: import it rather than
# restate it, so the audit cannot drift from the code it audits.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "_derive_ccr", REPO / "scripts" / "data" / "derive_cc_capacity_reconcile.py"
)
_derive = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_derive)

from market_sim.config.paths import (  # noqa: E402
    EIA_860_DIR,
    cc_capacity_reconcile_path,
)

ISO = "CAISO"
YEARS = [2023, 2024, 2025]
OUT = REPO / "results" / "calibration" / "_caiso185_table_provenance.json"
REPRO_TOL = 0.005  # PRECHECK §3 G-REPRO: reconciled_mw within 0.5 %


def _eia860_cc_sums() -> pd.DataFrame:
    """Per-plant EIA-860 combined-cycle nameplate / summer / winter sums.

    The same ``Technology == "Natural Gas Fired Combined Cycle"`` filter
    :func:`market_sim.data.fleet.campd_bins.cc_summer_capacity` uses, so the
    G-OVERCARRY attribution is against the exact rating the model's own summer
    derate is built from.
    """
    df = pd.read_parquet(EIA_860_DIR / "eia860_generator_operable.parquet")
    df = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    df["plant_code"] = pd.to_numeric(df["Plant Code"], errors="coerce")
    for src, dst in (
        ("Nameplate Capacity (MW)", "np_mw"),
        ("Summer Capacity (MW)", "ns_mw"),
        ("Winter Capacity (MW)", "win_mw"),
    ):
        df[dst] = pd.to_numeric(df[src], errors="coerce")
    df = df[df["plant_code"].notna()]
    df["plant_code"] = df["plant_code"].astype(int)
    return df.groupby("plant_code")[["np_mw", "ns_mw", "win_mw"]].sum()


def _rederive() -> tuple[pd.DataFrame, set[int], dict[int, tuple[str, float]], pd.Series]:
    """Re-run the deriver's ``--mode both`` selection at this head, in memory.

    Returns ``(rows, ct_only, model_capacity, p999)``. Mirrors
    ``derive_cc_capacity_reconcile.main()``'s cap/both branch line for line, using
    the deriver's own helpers and module-level constants — no constant is
    restated here, so a frozen-parameter change would show up as an audit
    failure rather than being silently absorbed.
    """
    from market_sim.data.eia923 import load_monthly_generation

    plants = _derive._model_cc_capacity(ISO, max(YEARS))
    p999, campd_annual = _derive._campd_p999_and_annual(ISO, set(plants), YEARS)
    gen = load_monthly_generation()
    gen = gen[gen["year"].isin(YEARS)]
    annual = gen.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()
    e923_pooled = gen.groupby("plant_id")["netgen_annual_mwh"].sum()
    ct_only = _derive._ct_only_codes(campd_annual, e923_pooled)

    rows: list[dict] = []
    for code, (name, cur) in plants.items():
        peak = float(p999.get(code, np.nan))
        if np.isnan(peak) or peak <= 0.0 or cur <= 0.0:
            continue
        if code in ct_only:
            continue
        if cur > _derive._CAP_MARGIN * peak:
            implied_cf = max(
                (float(annual.get((code, y), 0.0)) / (peak * 8760.0) for y in YEARS),
                default=0.0,
            )
            if implied_cf > _derive._CAP_FEASIBLE_CF:
                rows.append(
                    {"plant_code": code, "plant_name": name, "mode": "SKIP_INFEASIBLE_CF",
                     "current_mw": round(cur, 1), "campd_p999_mw": round(peak, 1),
                     "reconciled_mw": None, "implied_cf": round(implied_cf, 3)}
                )
                continue
            reconciled, row_mode = peak, "cap"
        elif cur < peak * (1.0 - _derive._MIN_DELTA):
            if peak > _derive._CAP_MARGIN * cur:
                rows.append(
                    {"plant_code": code, "plant_name": name, "mode": "SKIP_ARTIFACT_RAISE",
                     "current_mw": round(cur, 1), "campd_p999_mw": round(peak, 1),
                     "reconciled_mw": None}
                )
                continue
            reconciled, row_mode = peak, "raise"
        else:
            continue
        rows.append(
            {
                "plant_code": code,
                "plant_name": name,
                "current_mw": round(cur, 1),
                "campd_p999_mw": round(peak, 1),
                "reconciled_mw": round(reconciled, 1),
                "delta_pct": round(100 * (reconciled - cur) / cur, 1),
                "mode": row_mode,
            }
        )
    return pd.DataFrame(rows), ct_only, plants, p999


def main() -> None:
    """Run the three G-REPRO legs and the G-OVERCARRY attribution; write the record."""
    committed = pd.read_csv(cc_capacity_reconcile_path(ISO))
    rederived, ct_only, model_cap, p999 = _rederive()
    emitted = (
        rederived[rederived["mode"].isin(("cap", "raise"))]
        if not rederived.empty
        else rederived
    )
    by_code = {int(r.plant_code): r for r in emitted.itertuples(index=False)}

    # ---- R1 + R2: per committed row -------------------------------------
    rows: list[dict] = []
    for r in committed.itertuples(index=False):
        code = int(r.plant_code)
        got = by_code.get(code)
        live_peak = float(p999.get(code, np.nan))
        live_model = model_cap.get(code)
        rec: dict = {
            "plant_code": code,
            "plant_name": str(r.plant_name),
            "committed_mode": str(r.mode),
            "committed_current_mw": float(r.current_mw),
            "committed_reconciled_mw": float(r.reconciled_mw),
            "live_p999_mw": None if np.isnan(live_peak) else round(live_peak, 2),
            "live_model_cap_mw": None if live_model is None else round(live_model[1], 2),
            "reemitted": got is not None,
            "reemitted_mode": None if got is None else str(got.mode),
            "in_ct_only_now": code in ct_only,
        }
        if got is not None:
            d = abs(float(got.reconciled_mw) - float(r.reconciled_mw)) / float(
                r.reconciled_mw
            )
            rec["reconciled_rel_delta"] = round(d, 6)
            rec["r1_value_pass"] = bool(d <= REPRO_TOL)
            rec["r2_mode_pass"] = bool(str(got.mode) == str(r.mode))
        else:
            rec["reconciled_rel_delta"] = None
            rec["r1_value_pass"] = False
            rec["r2_mode_pass"] = False
        # R1 measured independently of membership: the p999 itself.
        if not np.isnan(live_peak):
            rec["p999_rel_delta"] = round(
                abs(live_peak - float(r.campd_p999_mw)) / float(r.campd_p999_mw), 6
            )
        else:
            rec["p999_rel_delta"] = None
        rec["g_repro_pass"] = bool(rec["r1_value_pass"] and rec["r2_mode_pass"])
        rec["current_mw_rel_drift"] = (
            None
            if live_model is None
            else round(
                (live_model[1] - float(r.current_mw)) / float(r.current_mw), 6
            )
        )
        rows.append(rec)

    new_rows = [c for c in by_code if c not in set(committed["plant_code"].astype(int))]

    # ---- G-OVERCARRY -----------------------------------------------------
    e860 = _eia860_cc_sums()
    over: list[dict] = []
    for r in committed.itertuples(index=False):
        if str(r.mode) != "cap":
            continue
        if abs(float(r.delta_pct)) <= (_derive._CAP_MARGIN - 1.0) * 100.0:
            continue
        code = int(r.plant_code)
        s = e860.loc[code] if code in e860.index else None
        cur = float(r.current_mw)
        rec = {
            "plant_code": code,
            "plant_name": str(r.plant_name),
            "delta_pct": float(r.delta_pct),
            "current_mw": cur,
            "campd_p999_mw": float(r.campd_p999_mw),
            "eia860_cc_nameplate_mw": None if s is None else round(float(s.np_mw), 1),
            "eia860_cc_summer_mw": None if s is None else round(float(s.ns_mw), 1),
            "eia860_cc_winter_mw": None if s is None else round(float(s.win_mw), 1),
        }
        if s is not None and float(s.np_mw) > 0.0:
            rec["current_over_cc_nameplate"] = round(cur / float(s.np_mw), 4)
            # Attribution (PRECHECK §4): a model capacity that materially exceeds
            # the plant's OWN EIA-860 CC nameplate sum cannot be an ambient
            # rating gap — it is a fleet-loading / attribution defect, and
            # rule 11 forbids burying it in a capacity value.
            rec["verdict"] = (
                "FLEET_LOADING_DEFECT"
                if cur > float(s.np_mw) * 1.01
                else "AMBIENT_RATING_GAP"
            )
        else:
            rec["verdict"] = "NO_EIA860_CC_ROWS"
        over.append(rec)

    out = {
        "iso": ISO,
        "years": YEARS,
        "tolerances": {
            "g_repro_rel": REPRO_TOL,
            "cap_margin": _derive._CAP_MARGIN,
            "min_delta": _derive._MIN_DELTA,
            "cc_net_of_gross": _derive._CC_NET_OF_GROSS,
            "cap_feasible_cf": _derive._CAP_FEASIBLE_CF,
            "ct_only_ratio": _derive._CT_ONLY_RATIO,
            "pure_play_cc_share": _derive._PURE_PLAY_CC_SHARE,
        },
        "committed_rows": len(committed),
        "rederived_emitted_rows": int(len(emitted)),
        "rederived_skipped": [
            r for r in rederived.to_dict("records") if str(r["mode"]).startswith("SKIP_")
        ],
        "rows": rows,
        "rows_new_at_head": new_rows,
        "ct_only_now": sorted(int(c) for c in ct_only),
        "g_repro_pass": all(r["g_repro_pass"] for r in rows),
        "g_overcarry": over,
        "g_overcarry_pass": all(r.get("verdict") == "AMBIENT_RATING_GAP" for r in over),
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
