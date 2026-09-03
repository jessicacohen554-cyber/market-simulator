"""capx D45 instrument, model side (ZERO solves): read a registered T1-H bundle's committed
evolution ledgers and lay the model's adequacy position, the capacity leg its screens saw,
and its retirement / entry events beside the published record the sibling instrument
(published-positions-2026-09-03.py/.json) holds.

    uv run python docs/handoffs/d45/positions-from-ledgers-2026-09-03.py <run_dir> [<run_dir> ...]

Per year the ledger carries (capx D45 runner observability, additive): the ENTERING-fleet
CR-1 position ``capacity_reserve_position`` (None when the ISO's clearing gate is off) and
the shared ``adequacy_requirement_mw``; the post-evolution ``reserve_margin`` identity
``firm = peak x (1 + rm)`` gives the exit-side position the way D28/D37 computed it.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.capacity_market import (
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)  # noqa: E402

PUB = json.loads(
    (Path(__file__).parent / "published-positions-2026-09-03.json").read_text()
)


def curve_price(iso: str, year: int, pos: float | None) -> float | None:
    if pos is None:
        return None
    v = resolve_demand_curve_vintage(iso, year)
    if not v.demand_curve:
        return None
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr


def published(iso: str, year: int) -> dict | None:
    if iso == "PJM":
        for r in PUB["pjm"]:
            if int(r["delivery_year"][:4]) == year:
                return r
    if iso == "NYISO":
        for r in PUB["nyiso"]:
            if int(r["capability_year"][:4]) == year:
                return r
    return None


def analyse(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "meta.json").read_text())
    iso = meta["iso"]
    bundle = REPO / meta["bundle"]
    years = sorted(int(p.stem.split("_")[1]) for p in bundle.glob("evolution_*.json"))
    rows, prev_firm = [], None
    for y in years:
        led = json.loads((bundle / f"evolution_{y}.json").read_text())
        peak = led.get("peak_demand_mw")
        rm = led.get("reserve_margin")
        firm_after = peak * (1 + rm) if (peak and rm is not None) else None
        req = led.get("adequacy_requirement_mw")
        pos_enter = led.get("capacity_reserve_position")
        pos_after = (firm_after / req) if (firm_after and req) else None
        pos_enter_identity = (prev_firm / req) if (prev_firm and req) else None
        # Realized exits this year (fuel / mw / reason) and the pipeline screen rows
        # (every candidate the screen FAILED, with the revenue stack it consumed —
        # capacity_revenue_usd is the capacity leg at the entering position).
        by_fuel: dict[str, float] = {}
        for e in led.get("retirements") or []:
            if isinstance(e, dict):
                by_fuel[e.get("fuel", "?")] = by_fuel.get(
                    e.get("fuel", "?"), 0.0
                ) + float(e.get("mw") or 0.0)
        pe = [r for r in (led.get("pipeline_events") or []) if isinstance(r, dict)]
        events: dict[str, float] = {}
        caprev = 0.0
        caprev_per_kw = []
        for r in pe:
            k = f"{r.get('event')}:{r.get('fuel')}"
            events[k] = events.get(k, 0.0) + float(r.get("mw") or 0.0)
            caprev += float(r.get("capacity_revenue_usd") or 0.0)
            if r.get("mw"):
                caprev_per_kw.append(
                    float(r.get("capacity_revenue_usd") or 0.0)
                    / (float(r["mw"]) * 1000.0)
                )
        diag = led.get("entry_screen_diagnostics") or []
        diag = diag if isinstance(diag, list) else []
        cap_terms = sorted(
            {round(float(r.get("capacity_revenue_per_mw_yr") or 0.0), 1) for r in diag}
        )
        pub = published(iso, y)
        pub_pos = (
            (pub.get("pos_cleared") if iso == "PJM" else pub.get("pos_published"))
            if pub
            else None
        )
        rows.append(
            dict(
                year=y,
                bridge=bool(led.get("bridge")),
                peak_mw=peak,
                requirement_mw=req,
                firm_after_mw=firm_after,
                pos_entering_ledger=pos_enter,
                pos_entering_identity=pos_enter_identity,
                pos_after=pos_after,
                curve_price_at_model_entering=curve_price(iso, y, pos_enter),
                pub_pos=pub_pos,
                pub_pos_offered=(pub or {}).get("pos_offered"),
                curve_price_at_pub_pos=curve_price(iso, y, pub_pos),
                real_price=(pub or {}).get(
                    "real_price_kw_yr", (pub or {}).get("spot_kw_yr")
                ),
                retire_events_mw_by_fuel=by_fuel,
                pipeline_events_mw=events,
                retire_capacity_revenue_usd=caprev,
                pipeline_capacity_rev_per_kw_yr=(
                    sorted(set(round(v, 2) for v in caprev_per_kw))[:4]
                    if caprev_per_kw
                    else []
                ),
                floor_retained_n=len(led.get("floor_retained") or []),
                entry_diag_rows=len(diag) if isinstance(diag, list) else 0,
                entry_diag_capacity_terms=cap_terms,
                thermal_additions=[
                    (a.get("fuel"), a.get("mw"))
                    for a in (led.get("thermal_additions") or [])
                ],
                storage_firm_mw=led.get("storage_firm_mw"),
                wind_cap_mw=led.get("wind_cap_mw"),
                solar_cap_mw=led.get("solar_cap_mw"),
                firm_clean_accredited_mw=led.get("firm_clean_accredited_mw"),
            )
        )
        if firm_after:
            prev_firm = firm_after
    return dict(run=run_dir.name, iso=iso, cache_key=meta.get("cache_key"), rows=rows)


if __name__ == "__main__":
    out = [analyse(Path(a)) for a in sys.argv[1:]]
    for r in out:
        print(f"\n===== {r['run']} ({r['iso']}, key {r['cache_key']})")
        hdr = f"{'yr':>5} {'peak':>9} {'req':>9} {'firmAfter':>10} {'posEnter':>9} {'posEnterId':>10} {'posAfter':>8} {'$model':>7} {'pubPos':>7} {'pubOff':>7} {'$@pub':>7} {'$real':>7} {'retireMW':>9} {'capRev$':>10} {'floor':>5} {'diag':>5}"
        print(hdr)
        for x in r["rows"]:
            f = lambda v, w, p=1: (
                f"{v:>{w},.{p}f}"
                if isinstance(v, (int, float)) and v is not None
                else f"{'-':>{w}}"
            )
            print(
                f"{x['year']:>5} {f(x['peak_mw'], 9, 0)} {f(x['requirement_mw'], 9, 0)} {f(x['firm_after_mw'], 10, 0)} "
                f"{f(x['pos_entering_ledger'], 9, 4)} {f(x['pos_entering_identity'], 10, 4)} {f(x['pos_after'], 8, 4)} "
                f"{f(x['curve_price_at_model_entering'], 7, 2)} {f(x['pub_pos'], 7, 4)} {f(x['pub_pos_offered'], 7, 4)} "
                f"{f(x['curve_price_at_pub_pos'], 7, 2)} {f(x['real_price'], 7, 2)} {f(sum(x['retire_events_mw_by_fuel'].values()), 9, 0)} "
                f"{f(x['retire_capacity_revenue_usd'], 10, 0)} {x['floor_retained_n']:>5} {x['entry_diag_rows']:>5}"
            )
            if x["retire_events_mw_by_fuel"] or x["pipeline_events_mw"]:
                print(
                    "       exits by fuel:",
                    {k: round(v, 1) for k, v in x["retire_events_mw_by_fuel"].items()},
                    "| pipeline events MW:",
                    {k: round(v, 0) for k, v in x["pipeline_events_mw"].items()},
                    "| cap leg $/kW-yr seen:",
                    x["pipeline_capacity_rev_per_kw_yr"],
                    "| entry cap terms $/MW-yr:",
                    x["entry_diag_capacity_terms"][:6],
                    "| thermal adds:",
                    x["thermal_additions"],
                )
    Path(__file__).with_suffix(".json").write_text(
        json.dumps(out, indent=1, default=float)
    )


# ---------------------------------------------------------------------------
# Counterfactual re-screen (PJM stage 3, zero-solve): for every candidate the
# pipeline screen FAILED in a year (event 'decided' / 'entry_capped'), add the
# capacity leg it WOULD have earned at the published CLEARED position on HEAD's own
# vintage curve (thermal accreditation on PJM's ELCC class basis, the same
# thermal_accreditation_fraction seam the screen used) and re-test
# net_revenue + delta >= going_forward_cost. Reports the MW that would have
# survived the bar. A bound: the screen's own year-over-year dynamics (a unit
# saved in year Y changes year Y+1's stack) are not replayed.
# ---------------------------------------------------------------------------
def counterfactual(run_dir: Path, positions: dict[int, float] | None = None) -> list[dict]:
    from market_sim.model.capacity_evolution.retirements import (
        thermal_accreditation_fraction,
    )

    meta = json.loads((run_dir / "meta.json").read_text())
    iso = meta["iso"]
    bundle = REPO / meta["bundle"]
    out = []
    for p in sorted(bundle.glob("evolution_*.json")):
        y = int(p.stem.split("_")[1])
        led = json.loads(p.read_text())
        pos_model = led.get("capacity_reserve_position")
        pub = published(iso, y)
        pos_cf = (positions or {}).get(y) or (
            (pub.get("pos_cleared") if iso == "PJM" else pub.get("pos_published"))
            if pub
            else None
        )
        if pos_cf is None:
            continue
        px_cf = curve_price(iso, y, pos_cf) or 0.0
        px_model = curve_price(iso, y, pos_model) if pos_model is not None else None
        rows = [
            r
            for r in (led.get("pipeline_events") or [])
            if isinstance(r, dict) and r.get("event") in ("decided", "entry_capped")
        ]
        failed_mw = sum(float(r.get("mw") or 0.0) for r in rows)
        saved_mw, saved_by_fuel = 0.0, {}
        for r in rows:
            mw = float(r.get("mw") or 0.0)
            frac = thermal_accreditation_fraction(r.get("fuel", ""), 0.0, iso)
            cap_now = float(r.get("capacity_revenue_usd") or 0.0)
            cap_cf = mw * frac * px_cf * 1000.0
            nr = float(r.get("net_revenue_usd") or 0.0) - cap_now + cap_cf
            if nr >= float(r.get("going_forward_cost_usd") or 0.0):
                saved_mw += mw
                saved_by_fuel[r["fuel"]] = saved_by_fuel.get(r["fuel"], 0.0) + mw
        out.append(
            dict(
                year=y,
                pos_model=pos_model,
                price_model=px_model,
                pos_counterfactual=pos_cf,
                price_counterfactual=px_cf,
                failed_mw=failed_mw,
                saved_mw=saved_mw,
                saved_by_fuel=saved_by_fuel,
                n_failed=len(rows),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Firm-capacity decomposition (stage 2, both ISOs): restate the ledger's
# post-evolution accredited firm capacity by component on the ISO's OWN
# accreditation basis — thermal by fuel (PJM: the ELCC class ratings; NYISO:
# 1 - EFORd, the registry default), hydro at the published accreditation
# (ledger firm_clean_accredited_mw), wind/solar at the credits the ledger
# recorded, storage at its ELCC (ledger storage_firm_mw), and the firm import
# credit — and check the sum against the reserve_margin identity. Every term
# is a committed ledger field or a HEAD registry constant.
# ---------------------------------------------------------------------------
def firm_decomposition(run_dir: Path) -> list[dict]:
    from market_sim.config.capacity_market import ADEQUACY_EXTERNAL_TIE_FIRM_MW
    from market_sim.model.capacity_evolution.retirements import (
        resolve_internal_supply_accounting_ratio,
        thermal_accreditation_fraction,
    )
    from market_sim.config.constants import EFORD

    meta = json.loads((run_dir / "meta.json").read_text())
    iso = meta["iso"]
    bundle = REPO / meta["bundle"]
    out = []
    for p in sorted(bundle.glob("evolution_*.json")):
        led = json.loads(p.read_text())
        if led.get("reserve_margin") is None:
            continue
        y = int(p.stem.split("_")[1])
        fleet = led.get("fleet_by_fuel_after") or {}
        thermal = {
            f: mw * thermal_accreditation_fraction(f, EFORD.get(f, 0.05), iso)
            for f, mw in fleet.items()
        }
        cred = led.get("renewable_credit_applied") or {}
        wind = float(led.get("wind_cap_mw") or 0.0) * float(cred.get("wind", 0.0))
        solar = float(led.get("solar_cap_mw") or 0.0) * float(cred.get("solar", 0.0))
        hydro = float(led.get("firm_clean_accredited_mw") or 0.0)
        storage = float(led.get("storage_firm_mw") or 0.0)
        internal = sum(thermal.values()) + wind + solar + hydro + storage
        internal *= resolve_internal_supply_accounting_ratio(iso)
        ties = ADEQUACY_EXTERNAL_TIE_FIRM_MW.get(iso, 0.0)
        total = internal + ties
        identity = led["peak_demand_mw"] * (1 + led["reserve_margin"])
        out.append(
            dict(
                year=y,
                thermal_nameplate_mw=sum(fleet.values()),
                thermal_firm_by_fuel=thermal,
                thermal_firm_mw=sum(thermal.values()),
                wind_firm_mw=wind,
                solar_firm_mw=solar,
                hydro_firm_mw=hydro,
                storage_firm_mw=storage,
                tie_firm_mw=ties,
                total_firm_mw=total,
                ledger_identity_firm_mw=identity,
                residual_mw=identity - total,
            )
        )
    return out
