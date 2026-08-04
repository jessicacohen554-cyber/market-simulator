"""FFR-3N — attribute the FH-1 §3.3 gate's I12 inversion (ERCOT).

Read-only scorer over two paired T1-FF arms' committed evolution ledgers. No
LP, no solve, no config mutation: every number here is arithmetic on
``evolution_<year>.json`` plus the requirement/accreditation registries.

Three separations, matching the charter:

* **Candidate 3 (band basis)** — restate I12's ERCOT floor onto the ledger's
  own gross-peak basis and report how much of the overshoot is instrument
  rather than model. Needs no ledger at all (``--band-only``).
* **Candidate 1 (the retirement rule)** — the paired ``pipeline`` vs
  ``legacy`` arms, compared on executed economic exits and per-year margin.
* **Candidate 2 (the entry side)** — an exact decomposition of the accredited
  firm capacity that produces the margin, by capacity class and by addition
  channel (``planned`` / ``economic`` / ``reserve_backstop``).

Usage::

    uv run python scripts/probes/_ffr3n_i12_attribution.py \\
        --pipeline-dir results/hindcast/ffr3n-ercot-pipeline \\
        --legacy-dir   results/hindcast/ffr3n-ercot-legacy \\
        --out results/calibration/_ffr3n_i12_attribution.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    resolve_adequacy_requirement_mw,
)
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402

# I12's band width above the floor (check_forecast_invariants.Thresholds).
BAND_PP = 0.15


def find_cache_dir(out_dir: Path, iso: str) -> Path:
    """Return the single ``<out-dir>/<ISO>/<cache_key>/`` directory.

    The ledgers live under the resolved cache key, not the out-dir root, so a
    run is read through whatever key it actually landed on rather than a
    request-side recomputation of it.
    """
    iso_dir = Path(out_dir) / iso
    keys = [p for p in iso_dir.iterdir() if p.is_dir()] if iso_dir.is_dir() else []
    if len(keys) != 1:
        raise SystemExit(f"expected exactly one cache key under {iso_dir}, got {keys}")
    return keys[0]


def band_arithmetic(iso: str = "ERCOT") -> dict:
    """Candidate 3: I12's scored floor vs the floor the model actually enforces.

    I12's energy-only branch scores the ledger's ``reserve_margin`` — which is
    ``accredited_firm / GROSS peak - 1`` — against the scalar
    ``config.planning_reserve_margin``. That scalar is ERCOT's Board target
    stated on the CDR's DR-netted **firm** peak, so the two sit on different
    denominators. Restating the model's own requirement as a margin over the
    gross peak puts both on the ledger's basis.
    """
    cfg = ScenarioConfig()
    peak = 100_000.0  # basis-only; the restatement is scale-free
    model_floor = resolve_adequacy_requirement_mw(cfg, iso, peak) / peak - 1.0
    scored_floor = cfg.planning_reserve_margin
    return {
        "iso": iso,
        "scored_floor": scored_floor,
        "scored_ceiling": scored_floor + BAND_PP,
        "model_floor_gross_basis": model_floor,
        "model_ceiling_gross_basis": model_floor + BAND_PP,
        "basis_gap_pp": (scored_floor - model_floor) * 100.0,
        "band_width_pp": BAND_PP * 100.0,
    }


def decompose_year(led: dict) -> dict:
    """Candidate 2: reconstruct the accredited firm MW behind one year's margin.

    ERCOT accredits thermal at ``seasonal_rating`` (factor 1.0), so the thermal
    leg is exactly ``sum(fleet_by_fuel_after)``. VRE enters at the resolved
    per-fuel credit and storage at its firm MW; the reconstruction is checked
    against the firm MW the ledger's own ``reserve_margin`` implies, and the
    residual is REPORTED rather than absorbed (storage firm MW is recorded
    pre-dilution, so exact closure is not assumed).
    """
    peak = float(led.get("peak_demand_mw") or 0.0)
    rm = led.get("reserve_margin")
    firm_implied = (1.0 + float(rm)) * peak if rm is not None and peak > 0 else None

    credits = led.get("renewable_credit_applied") or {}
    wind_cap = float(led.get("wind_cap_mw") or 0.0)
    solar_cap = float(led.get("solar_cap_mw") or 0.0)
    wind_firm = wind_cap * float(credits.get("wind", 0.0))
    solar_firm = solar_cap * float(credits.get("solar", 0.0))
    storage_firm = float(led.get("storage_firm_mw") or 0.0)
    hydro_firm = float(led.get("firm_clean_accredited_mw") or 0.0)
    thermal_firm = sum(float(v) for v in (led.get("fleet_by_fuel_after") or {}).values())

    recon = thermal_firm + wind_firm + solar_firm + storage_firm + hydro_firm

    # Addition channels. `load_planned_additions` skips wind/solar/hydro/storage
    # by construction, so every renewable and storage addition is economic entry
    # (step 5); only thermal carries a planned/economic/reserve_backstop split.
    thermal_by_source: dict[str, float] = {}
    for a in led.get("thermal_additions", []):
        thermal_by_source[a.get("source", "?")] = thermal_by_source.get(
            a.get("source", "?"), 0.0
        ) + float(a.get("mw", 0.0))
    ren_by_tech: dict[str, float] = {}
    for a in led.get("renewable_additions", []):
        ren_by_tech[a.get("tech", "?")] = ren_by_tech.get(
            a.get("tech", "?"), 0.0
        ) + float(a.get("mw", 0.0))
    sto_added = sum(float(a.get("mw", 0.0)) for a in led.get("storage_additions", []))

    ev_counts: dict[str, int] = {}
    for e in led.get("pipeline_events", []):
        ev_counts[e.get("event", "?")] = ev_counts.get(e.get("event", "?"), 0) + 1
    retire_by_reason: dict[str, float] = {}
    for r in led.get("retirements", []):
        retire_by_reason[r.get("reason", "?")] = retire_by_reason.get(
            r.get("reason", "?"), 0.0
        ) + float(r.get("mw", 0.0))

    return {
        "year": led.get("year"),
        "peak_demand_mw": peak,
        "reserve_margin": rm,
        "firm_mw_implied": firm_implied,
        "firm_mw_reconstructed": recon,
        "reconstruction_residual_mw": (
            None if firm_implied is None else firm_implied - recon
        ),
        "firm_legs_mw": {
            "thermal": thermal_firm,
            "wind": wind_firm,
            "solar": solar_firm,
            "storage": storage_firm,
            "hydro": hydro_firm,
        },
        "nameplate_pools_mw": {"wind": wind_cap, "solar": solar_cap},
        "renewable_credit_applied": credits,
        "additions_mw": {
            "thermal_by_source": thermal_by_source,
            "renewable_by_tech": ren_by_tech,
            "storage": sto_added,
        },
        "retirements_mw_by_reason": retire_by_reason,
        "pipeline_event_counts": ev_counts,
        "floor_retained_n": len(led.get("floor_retained", [])),
    }


ACTUALS_CSV = REPO_ROOT / "data/raw/_validation-source/capacity_actuals_ercot.csv"


def actuals_by_year() -> dict:
    """ERCOT's MEASURED additions/retirements per year and tech, 2023-2025.

    The registry-outcome scoring target `build_capacity_actuals.py` writes from
    EIA-860 (operable + retired_and_canceled). Used here as the reality anchor
    for candidate 2: whether the model's build is an over-build is a question
    about what ERCOT actually built, not about the I12 band.

    Assumption-free by design — nameplate MW compared to nameplate MW, with no
    accreditation factor applied on either side.
    """
    import csv

    adds: dict[int, dict[str, float]] = {}
    rets: dict[int, dict[str, float]] = {}
    with open(ACTUALS_CSV) as fh:
        rows = [ln for ln in fh if not ln.startswith("#")]
    for row in csv.DictReader(rows):
        year = int(row["year"])
        if not 2023 <= year <= 2025:
            continue
        sink = adds if row["kind"] == "addition" else rets
        d = sink.setdefault(year, {})
        d[row["fuel"]] = d.get(row["fuel"], 0.0) + float(row["mw"])
    return {"additions": adds, "retirements": rets}


def compare_to_actuals(rows: list[dict]) -> None:
    """Print modelled vs measured capacity events per year (nameplate MW)."""
    act = actuals_by_year()
    print("=== Candidate 2 reality anchor — modelled vs ACTUAL (nameplate MW) ===")
    for r in rows:
        y = r["year"]
        if y not in act["additions"] and y not in act["retirements"]:
            continue
        a = act["additions"].get(y, {})
        rt = act["retirements"].get(y, {})
        m = r["additions_mw"]
        m_thermal = sum(m["thermal_by_source"].values())
        m_ren = m["renewable_by_tech"]
        m_sto = m["storage"]
        a_thermal = sum(v for k, v in a.items() if k in ("gas_cc", "gas_ct", "gas_st", "coal", "other", "nuclear"))
        print(
            f"  {y}  thermal  model {m_thermal:9,.0f}  actual {a_thermal:9,.0f}"
            f"   | wind model {m_ren.get('wind', 0.0):8,.0f} actual {a.get('wind', 0.0):8,.0f}"
            f"   | solar model {m_ren.get('solar', 0.0):8,.0f} actual {a.get('solar', 0.0):8,.0f}"
            f"   | storage model {m_sto:8,.0f} actual {a.get('storage', 0.0):8,.0f}"
        )
        print(
            f"        exits  model {sum(r['retirements_mw_by_reason'].values()):9,.0f}"
            f"  actual {sum(rt.values()):9,.0f}"
        )
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--pipeline-dir")
    ap.add_argument("--legacy-dir")
    ap.add_argument("--band-only", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    report: dict = {"iso": args.iso, "band": band_arithmetic(args.iso)}
    b = report["band"]
    print("=== Candidate 3 — I12 band basis (no LP) ===")
    print(f"  I12 scores against : [{b['scored_floor']:.4%}, {b['scored_ceiling']:.4%}]")
    print(
        f"  model's own floor  : [{b['model_floor_gross_basis']:.4%}, "
        f"{b['model_ceiling_gross_basis']:.4%}]  (gross-peak basis)"
    )
    print(f"  basis gap          : {b['basis_gap_pp']:.4f} pp\n")

    if not args.band_only:
        for label, out_dir in (("pipeline", args.pipeline_dir), ("legacy", args.legacy_dir)):
            if not out_dir:
                continue
            cache_dir = find_cache_dir(Path(out_dir), args.iso)
            ledgers = load_ledgers_for_run(cache_dir)
            if not ledgers:
                raise SystemExit(f"no ledgers under {cache_dir} (load returns {{}} silently)")
            rows = [decompose_year(led) for _y, led in sorted(ledgers.items())]
            report[label] = {"cache_key": cache_dir.name, "years": rows}
            print(f"=== arm: {label}   cache_key={cache_dir.name} ===")
            for r in rows:
                ceil_model = b["model_ceiling_gross_basis"]
                if r["reserve_margin"] is None:
                    # Bridge year: evolved but never solved, so no firm-capacity
                    # accounting is persisted. Reported, never silently dropped.
                    print(f"  {r['year']}: reserve_margin absent (bridge/unsolved year)")
                    continue
                over_scored = (r["reserve_margin"] - b["scored_ceiling"]) * 100.0
                over = (r["reserve_margin"] - ceil_model) * 100.0
                print(
                    f"  {r['year']}: RM {r['reserve_margin']:.4%}  peak {r['peak_demand_mw']:,.0f} MW"
                    f"  firm {r['firm_mw_implied']:,.0f} MW"
                    f"  | over ceiling: as-scored {over_scored:+.2f} pp,"
                    f" corrected {over:+.2f} pp"
                )
                resid = r["reconstruction_residual_mw"]
                print(
                    f"        legs MW: " + ", ".join(
                        f"{k}={v:,.0f}" for k, v in r["firm_legs_mw"].items()
                    )
                    + (
                        "   recon residual n/a"
                        if resid is None
                        else f"   recon residual {resid:,.1f} MW"
                    )
                )
                print(
                    f"        adds MW: thermal={r['additions_mw']['thermal_by_source']}"
                    f" renew={r['additions_mw']['renewable_by_tech']}"
                    f" storage={r['additions_mw']['storage']:,.0f}"
                )
                print(
                    f"        exits MW: {r['retirements_mw_by_reason'] or '{}'}"
                    f"   pipeline_events: {r['pipeline_event_counts'] or '{}'}"
                    f"   floor_retained: {r['floor_retained_n']}"
                )
            print()
            if label == "pipeline":
                compare_to_actuals(rows)

        if "pipeline" in report and "legacy" in report:
            print("=== Candidate 1 — paired rule delta (pipeline − legacy) ===")
            pl = {r["year"]: r for r in report["pipeline"]["years"]}
            lg = {r["year"]: r for r in report["legacy"]["years"]}
            deltas = []
            for y in sorted(set(pl) & set(lg)):
                if pl[y]["reserve_margin"] is None or lg[y]["reserve_margin"] is None:
                    print(f"  {y}: reserve_margin absent in one arm — not compared")
                    continue
                d_rm = (pl[y]["reserve_margin"] - lg[y]["reserve_margin"]) * 100.0
                e_pl = sum(pl[y]["retirements_mw_by_reason"].values())
                e_lg = sum(lg[y]["retirements_mw_by_reason"].values())
                deltas.append({"year": y, "d_rm_pp": d_rm, "exit_pl": e_pl, "exit_lg": e_lg})
                print(
                    f"  {y}: ΔRM {d_rm:+.4f} pp | exits pipeline {e_pl:,.1f} MW"
                    f" vs legacy {e_lg:,.1f} MW"
                )
            report["rule_delta"] = deltas

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True))
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
