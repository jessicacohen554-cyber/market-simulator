"""capx D49 half 1 — the CCS retrofit screen's own uplift arithmetic, reconstructed per
converting unit on the D41-corrected constants, like-for-like across ERCOT / PJM / MISO
(zero solve).

The screen (``model/capacity_evolution/ccs.py::apply_ccs_retrofit``) values a retrofit as
the incremental attainable margin of the post-retrofit continuation over the unabated one,
with §45Q as a bid offset, against a two-segment windowed payback. Because the post-window
uplift (no 45Q) is negative for every host, clearing reduces to

    capex_learned(y) ≤ 12 × uplift_window,   uplift_window = Σ_t[max(0,p−b_post) − max(0,p−b_unab)]·avail − ΔFOM
    b_unab = hr·gas + vom ;  b_post = 1.12·hr·gas + vom + 8 + 0.9·er·(15 − 85)
    Δ = b_unab − b_post = 63·er − 0.12·hr·gas − 8     (the per-hour uplift CEILING, $/MWh)

so a unit CAN clear only if Δ·avail·8760 − ΔFOM ≥ capex_learned/12 (the "hour ceiling").
For each converting unit the ledgers name, this probe rebuilds the ISO's base fleet through
the repo's own ``build_base_fleet`` (the same tranche hr / measured plant CO2 rate / EFORd /
vintage the screen saw), computes Δ, the ceiling, the break-even in-merit hours H*, and the
uplift on a STAND-IN duration surface re-levelled to the ledger's own screen-price mean
(no forecast bundle commits hourly prices). It then re-runs the same arithmetic with the
CO2 rate replaced by the physical ``hr × FUEL_CO2_FACTOR`` and with the tranche's bid
replaced by the plant's base heat rate — the PREDECL §1.3 (c)/(c′) tests — and applies
the identical construction to PJM's and MISO's converting units (decided at the STALE
900 / 25 constants) so the three ISOs are compared on one arithmetic.

Usage::

    uv run python scripts/probes/_capxd49_ercot_ccs_reconstruction.py \\
        --out results/calibration/capxd49_ccs_reconstruction.json
"""

from __future__ import annotations

import argparse
import dataclasses
import glob
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.constants import FUEL_CO2_FACTOR_PER_MMBTU  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet.assembly import build_base_fleet, load_or_synthesize_bins  # noqa: E402
from market_sim.data.fuel.trajectories import resolve_annual_gas_price  # noqa: E402
from market_sim.model.capacity_evolution.ccs import (  # noqa: E402
    _adjust_retrofit_capex,
    _ccs_retrofit_payback_years,
)
from market_sim.model.capacity_evolution.new_entry import CumulativeDeployment  # noqa: E402
from market_sim.model.capacity_evolution.retirements import _THERMAL_PLANT_LIFE_YEARS  # noqa: E402
from market_sim.policy.ira import CCUS_45Q_CREDIT_PER_TON  # noqa: E402

BUNDLES = {
    "ERCOT": ROOT / "results/ff-t1f-d46/ercot",
    "PJM": ROOT / "results/ff-t1f-s6-pjm/ledger",
    "MISO": ROOT / "results/ff-t1f-s123/verify",
}
STANDIN_NPZ = {
    "ERCOT": ROOT / "results/hindcast/ercot-2021-2025-realized-t1h-d46/ERCOT/*/screen_signal_diag_2024_for_2025.npz",
    "MISO": ROOT / "results/hindcast/miso-2021-2025-realized-t1h-d46/MISO/*/screen_signal_diag_2024_for_2025.npz",
    "PJM": None,
}
CORRECTED = {"ccs_retrofit_capex_kw": 1521.4, "fixed_om_gas_cc_ccs": 65.0}
HOURS = 8760


def load_config(bundle: Path) -> tuple[ScenarioConfig, dict]:
    rc = json.loads((bundle / "run_config.json").read_text())
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    sc = dict(rc["scenario_config"])
    sc.update(CORRECTED)  # the like-for-like basis: every ISO on the D41 constants
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in names}), rc


def load_ledgers(bundle: Path, iso: str) -> dict[int, dict]:
    out = {}
    for p in glob.glob(str(bundle / iso / "*" / "evolution_*.json")):
        out[int(Path(p).stem.split("_")[1])] = json.loads(Path(p).read_text())
    return out


def learned_capex_path(cfg: ScenarioConfig, ledgers: dict[int, dict]) -> dict[int, float]:
    """Replicate the runner's tracker: initial + global GW/yr + the run's OWN CCS GW per year."""
    cum = CumulativeDeployment.initial()
    out = {}
    for y in sorted(ledgers):
        out[y] = _adjust_retrofit_capex(cfg.ccs_retrofit_capex_kw, cum.get("gas_cc_ccs"))
        led = ledgers[y]
        local = sum(r["mw"] for r in led.get("ccs_retrofits", [])) / 1000.0
        local += sum(t["mw"] for t in led.get("thermal_additions", []) if t.get("fuel") == "gas_cc_ccs") / 1000.0
        cum.add("gas_cc_ccs", local)  # the screen adds retrofitted GW itself; new builds via local_builds
        cum.advance_year({})
    return out


def unit_terms(gen, cfg: ScenarioConfig, gas: float, er_override: float | None = None, hr_bid_override: float | None = None) -> dict:
    hr = float(gen.heat_rate)
    hr_bid = hr if hr_bid_override is None else float(hr_bid_override)
    er = float(gen.emission_rate_co2) if er_override is None else float(er_override)
    captured = er * cfg.ccs_retrofit_capture_rate
    q45 = CCUS_45Q_CREDIT_PER_TON * captured
    b_unab = hr_bid * gas + gen.vom
    b_post = hr_bid * (1.0 + cfg.ccs_retrofit_hr_penalty) * gas + gen.vom + cfg.ccs_retrofit_vom_adder + captured * cfg.co2_transport_storage_cost - q45
    return {"hr": hr, "hr_bid": hr_bid, "er": er, "q45": q45, "b_unab": b_unab, "b_post": b_post, "delta": b_unab - b_post,
            "avail": max(0.0, 1.0 - float(gen.eford))}


def uplift_on_surface(p: np.ndarray, t: dict, dfom: float) -> tuple[float, float, float]:
    """(uplift_window, share of Σ-term from the band b_post ≤ p < b_unab, in-merit hours unabated)."""
    both = np.maximum(p - t["b_unab"], 0.0)
    post = np.maximum(p - t["b_post"], 0.0)
    total = float((post - both).sum()) * t["avail"] * (HOURS / p.size)
    mask = (p >= t["b_post"]) & (p < t["b_unab"])
    band = float((mask * (p - t["b_post"])).sum()) * t["avail"] * (HOURS / p.size)
    return total - dfom, (band / total if total > 0 else 0.0), int((p >= t["b_unab"]).sum())


def evaluate(gen, cfg, year, gas, capex_kw, surfaces: dict[str, np.ndarray], **overrides) -> dict:
    t = unit_terms(gen, cfg, gas, **overrides)
    dfom = (cfg.fixed_om_gas_cc_ccs * cfg.retirement_fom_multiplier_gas_cc_ccs - cfg.fixed_om_gas_cc * cfg.retirement_fom_multiplier_gas_cc) * 1000.0
    remaining = max(0, _THERMAL_PLANT_LIFE_YEARS - (year - int(gen.online_year)))
    window = min(float(cfg.ira_45q_credit_window_years), float(remaining))
    capex = capex_kw * 1000.0
    bar_uplift = capex / window if window > 0 else float("inf")
    ceiling = t["delta"] * t["avail"] * HOURS - dfom
    hstar = (bar_uplift + dfom) / (t["delta"] * t["avail"]) if t["delta"] > 0 else float("inf")
    out = {**t, "remaining_life": remaining, "window": window, "capex_kw": capex_kw, "dfom": dfom,
           "bar_uplift": bar_uplift, "ceiling_uplift": ceiling, "clears_at_ceiling": bool(ceiling >= bar_uplift and remaining >= cfg.ccs_retrofit_min_remaining_life),
           "h_star": hstar, "surfaces": {}}
    for name, p in surfaces.items():
        up, band_share, hmerit = uplift_on_surface(p, t, dfom)
        pb = _ccs_retrofit_payback_years(capex, up, -abs(up) - 1.0, window) if up > 0 else float("inf")
        out["surfaces"][name] = {"uplift": up, "band_share": band_share, "in_merit_h_unab": hmerit,
                                 "payback": pb, "clears": bool(up > 0 and pb < remaining)}
    return out


def standin_surfaces(iso: str, level: float | None, zone_names: list[str]) -> dict[str, dict[str, np.ndarray]]:
    """Return {surface_name: {zone: prices}} re-levelled additively to ``level`` (the ledger's own zone-flat mean)."""
    if level is None:
        return {}
    # The dispersion-free bound: every hour AT the ledger's own zone-flat mean. The
    # lookahead stack signal the screen consumed is a net-load step function floored
    # at the cheapest unit, so this is the surface it tends toward as its steps compress.
    out: dict[str, dict[str, np.ndarray]] = {"flat_level": {zn: np.full(HOURS, level) for zn in zone_names}}
    pat = STANDIN_NPZ.get(iso)
    files = glob.glob(str(pat)) if pat is not None else []
    if not files:
        return out
    z = np.load(files[0])
    stack = z["price_base_usd_mwh"] + z["adder_usd_mwh"]
    duals = z["econ_prices_usd_mwh"]
    out.update({"standin_stack": {}, "standin_duals": {}})
    shift = level - float(stack.mean())
    for zi, zn in enumerate(zone_names):
        out["standin_stack"][zn] = stack + shift
        if zi < duals.shape[0]:
            out["standin_duals"][zn] = duals[zi] + (level - float(duals[zi].mean()))
    return out


def screen_level(ledgers: dict[int, dict], year: int) -> float | None:
    """The zone-flat screen-price mean the ledger's own failing rows record for the year's screen."""
    for y in (year, year - 1, year + 1, year - 2):
        rows = ledgers.get(y, {}).get("pipeline_events", [])
        if rows:
            return float(np.mean([r["screen_price_mean_usd_mwh"] for r in rows]))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--isos", nargs="*", default=["ERCOT", "PJM", "MISO"])
    args = ap.parse_args()
    report: dict = {"co2_factor": FUEL_CO2_FACTOR_PER_MMBTU, "isos": {}}

    for iso in args.isos:
        bundle = BUNDLES[iso]
        cfg, rc = load_config(bundle)
        ledgers = load_ledgers(bundle, iso)
        iso_config = get_iso_config(iso)
        zone_names = list(iso_config.zone_names)
        bins = load_or_synthesize_bins(cfg, iso, iso_config, [])
        fleet = build_base_fleet(bins, iso, iso_config, zone_names, cfg, [], [], int(cfg.start_year))
        by_id = {g.unit_id: g for g in fleet}
        hr_col = next((c for c in ("Plant_Avg_HR_MMBtu_MWh", "hr_plant", "plant_hr", "base_hr", "heat_rate", "hr_mc", "hr_econ") if bins is not None and c in bins.columns), None)
        if bins is not None:
            print(f"  bins columns: {list(bins.columns)}")
        plant_hr = {}
        if bins is not None and hr_col:
            for _, r in bins.iterrows():
                plant_hr[int(r["Plant_Code"])] = float(r[hr_col])
        capex_path = learned_capex_path(cfg, ledgers)
        fac = FUEL_CO2_FACTOR_PER_MMBTU["gas_cc"]
        print(f"\n=================== {iso}  (run {rc['cache_key']} @ {rc['git']['sha']}; fleet {len(fleet)} units; gas_cc {sum(1 for g in fleet if g.fuel_type=='gas_cc')})")
        print(f"  learned capex path on corrected 1521.4 (run's own CCS GW fed back): { {y: round(v,1) for y,v in capex_path.items()} }")
        print(f"  bins hr column: {hr_col}; CO2 factor gas {fac}")
        iso_rep = {"cache_key": rc["cache_key"], "sha": rc["git"]["sha"], "capex_path": capex_path, "years": {}}

        conv_rows = [(y, r) for y in sorted(ledgers) for r in ledgers[y].get("ccs_retrofits", [])]
        years = sorted({y for y, _ in conv_rows}) or [2028]
        for y in years:
            gas = resolve_annual_gas_price(cfg, y)
            level = screen_level(ledgers, y)
            surf = standin_surfaces(iso, level, zone_names)
            capex_kw = capex_path.get(y, capex_path[max(capex_path)])
            print(f"\n  ---- screen year {y}: gas ${gas:.2f}; learned capex {capex_kw:.1f} $/kW; ledger screen-price mean {level}; stand-in surfaces {list(surf)}")
            print(f"  {'unit':44s} {'MW':>6} {'hr':>5} {'hr_pl':>5} {'er':>5} {'er_phy':>6} {'vint':>4} {'Δ':>6} {'ceil':>8} {'bar':>8} {'H*':>6} ceil? | stand-in stack: uplift band% clears | duals: uplift clears | phys-er: ceil? | base-hr bid: ceil?")
            rows_out = []
            for yy, r in conv_rows:
                if yy != y:
                    continue
                g = by_id.get(r["unit_id"])
                if g is None:
                    print(f"  {r['unit_id']:44s} NOT IN BASE FLEET (added/renamed after {cfg.start_year})")
                    rows_out.append({"unit_id": r["unit_id"], "mw": r["mw"], "missing": True})
                    continue
                zsurf = {k: v[g.zone] for k, v in surf.items() if g.zone in v}
                base = evaluate(g, cfg, y, gas, capex_kw, zsurf)
                er_phys = float(g.heat_rate) * fac
                phys = evaluate(g, cfg, y, gas, capex_kw, {}, er_override=er_phys)
                phr = plant_hr.get(int(g.plant_code))
                basehr = evaluate(g, cfg, y, gas, capex_kw, zsurf, hr_bid_override=phr) if phr else None
                ss = base["surfaces"].get("standin_stack", {})
                sd = base["surfaces"].get("standin_duals", {})
                fl = base["surfaces"].get("flat_level", {})
                print(f"  {g.unit_id:44s} {g.pmax_mw:6.1f} {g.heat_rate:5.2f} {(phr or 0):5.2f} {g.emission_rate_co2:5.3f} {er_phys:6.3f} {int(g.online_year):4d} {base['delta']:6.2f} {base['ceiling_uplift']/1000:8.1f} {base['bar_uplift']/1000:8.1f} {base['h_star']:6.0f} {'Y' if base['clears_at_ceiling'] else 'N'} | "
                      f"{(ss.get('uplift',0)/1000):8.1f} {100*ss.get('band_share',0):4.0f}% {'Y' if ss.get('clears') else 'N'} | {(sd.get('uplift',0)/1000):8.1f} {'Y' if sd.get('clears') else 'N'} | flat {(fl.get('uplift',0)/1000):7.1f} {'Y' if fl.get('clears') else 'N'} | {'Y' if phys['clears_at_ceiling'] else 'N'} | {('Y' if basehr and basehr['clears_at_ceiling'] else ('N' if basehr else '-'))}")
                rows_out.append({"unit_id": g.unit_id, "mw": float(g.pmax_mw), "zone": g.zone, "plant": int(g.plant_code), "tranche": g.unit_id.rsplit("_", 1)[-1],
                                 "hr": base["hr"], "plant_hr": phr, "er": base["er"], "er_phys": er_phys, "er_over_phys": base["er"] / er_phys if er_phys else None,
                                 "vom": float(g.vom), "eford": float(g.eford), "online_year": int(g.online_year), "delta": base["delta"], "q45": base["q45"],
                                 "b_unab": base["b_unab"], "b_post": base["b_post"], "ceiling_uplift": base["ceiling_uplift"], "bar_uplift": base["bar_uplift"],
                                 "h_star": base["h_star"], "clears_at_ceiling": base["clears_at_ceiling"], "surfaces": base["surfaces"],
                                 "phys_er_clears_at_ceiling": phys["clears_at_ceiling"], "phys_er_delta": phys["delta"], "phys_er_h_star": phys["h_star"],
                                 "base_hr_bid_clears_at_ceiling": (basehr["clears_at_ceiling"] if basehr else None)})
            # whole-fleet ceiling census for this ISO-year on the corrected constants
            cc_units = [g for g in fleet if g.fuel_type == "gas_cc"]
            cens = []
            for g in cc_units:
                b = evaluate(g, cfg, y, gas, capex_kw, {})
                cens.append((g, b))
            mw_all = sum(g.pmax_mw for g, _ in cens)
            mw_ceil = sum(g.pmax_mw for g, b in cens if b["clears_at_ceiling"])
            hr_ceil = [g.heat_rate for g, b in cens if b["clears_at_ceiling"]]
            hr_no = [g.heat_rate for g, b in cens if not b["clears_at_ceiling"]]
            dist = {"n_gas_cc": len(cens), "mw_gas_cc": mw_all, "mw_clear_at_ceiling": mw_ceil,
                    "hr_min_clearing": float(min(hr_ceil)) if hr_ceil else None, "hr_max_not_clearing": float(max(hr_no)) if hr_no else None,
                    "er_over_phys_p10_50_90": np.percentile([g.emission_rate_co2 / (g.heat_rate * fac) for g, _ in cens], [10, 50, 90]).round(3).tolist(),
                    "mw_clear_on_standin_stack": None}
            if surf:
                mw_std = 0.0
                for g, _ in cens:
                    zs = {k: v[g.zone] for k, v in surf.items() if g.zone in v}
                    if zs:
                        e = evaluate(g, cfg, y, gas, capex_kw, zs)
                        if e["surfaces"].get("standin_stack", {}).get("clears"):
                            mw_std += g.pmax_mw
                dist["mw_clear_on_standin_stack"] = mw_std
            print(f"  fleet census {y}: gas_cc {len(cens)} units / {mw_all/1000:.1f} GW; clear at the HOUR CEILING {mw_ceil/1000:.2f} GW "
                  f"(min hr clearing {dist['hr_min_clearing']}, max hr not clearing {dist['hr_max_not_clearing']}); on stand-in stack {dist['mw_clear_on_standin_stack']}; er/phys p10/50/90 {dist['er_over_phys_p10_50_90']}")
            # D41 class-average replication row
            class_row = {}
            for label, hr in (("H-class", 6.3), ("F-class", 6.7), ("older", 7.5)):
                er = hr * fac
                delta = 63.0 * er - cfg.ccs_retrofit_hr_penalty * hr * gas - cfg.ccs_retrofit_vom_adder
                avail = 0.95
                dfom = 35000.0
                bar = capex_kw * 1000.0 / 12.0
                class_row[label] = {"delta": delta, "h_star": (bar + dfom) / (delta * avail)}
            print(f"  D41 class-average replication {y}: " + ", ".join(f"{k}: Δ {v['delta']:.2f} H* {v['h_star']:.0f}" for k, v in class_row.items()))
            iso_rep["years"][y] = {"gas": gas, "capex_kw": capex_kw, "screen_level": level, "converting": rows_out, "fleet_census": dist, "class_avg": class_row}
        report["isos"][iso] = iso_rep

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=1, default=float))
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
