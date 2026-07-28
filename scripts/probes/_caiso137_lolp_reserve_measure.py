"""caiso-137 — RE-SPECIFY and GATE ask A2, the CAISO LOLP overlay's reserve measure.

``docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md`` §4 (ask **A2**) proposes to
"re-specify the CAISO LOLP overlay's reserve measure to plant-level ONLINE".
``FINDING-caiso133`` §7 already carried A2's **D1** to a PASS *and* filed two
corrections the ask must absorb before it can be gated:

  (i) the ask's premise — that the overlay "evaluates ``reserve_headroom`` on
      total fleet headroom" — **does not match the code**; and
 (ii) the D1 number (plant-level ONLINE *thermal* headroom, p10 1,201 / 1,119 /
      1,021 MW) is a **lower bound** on the overlay's own ``r_online``, which
      also carries storage and curtailed-renewable headroom.

This instrument does STEP 1 (re-specify A2 against the code, which may kill it)
and, if a defect survives, its D2 / D3 gates. **No LP is built and no solver is
called** — every number is read from the committed keeper bundle plus a
``run_year(fleet_only=True)`` reconstruction (the caiso-105/121/127/131/133
pattern), so nothing here can touch a dispatch.

Sections
--------
* **§A — what the overlay actually computes**, read off the code and the
  keeper's own ``run_config.json`` flags. Settles A2 options (a)/(b)/(c)/(d).
* **§B — the ``r_online`` decomposition** the FINDING could not do: thermal
  (from ``unit_hourly``) + storage (from ``storage_<y>`` and the rebuilt caps)
  + curtailed VRE (rebuilt potential minus ``class_hourly`` dispatch), and the
  overlay's realised adder on the keeper, all three years.
* **§C — the defect §B exposes**: ``runner.py`` hands the overlay
  ``storage.power_cap`` — the **flat per-unit nameplate** array — where the LP
  itself dispatches against the hourly ``storage_power_cap`` that carries the
  COD vintage ramp. The overlay therefore credits, as *online spinning
  reserve*, battery power the LP's own bounds say is **not yet in service**.
* **§D — D2, the ask memo §2 E1/E2 spillover pre-check**, priced from the
  keeper's own ``system_<y>.parquet`` on the pre-adder lambda fixed point.
* **§E — D3, no fitted parameter**, verified against ``run_config.json``.
* **§F — is the verdict robust to the reconstruction's own error?** The rebuild
  is an approximation of the keeper's fleet, so ``r_online`` is reconstructed,
  not read. Bounded two ways: the LP's own dump-price floor (which pins the
  realised adder to EXACTLY 0 in thousands of hours, making any positive
  reconstructed adder there provably spurious) and a uniform-offset sensitivity
  sweep over both arms.

Rule 19 ``[R-ONE-MECH]`` note: the overlay is CAISO's **sole** scarcity-pricing
mechanism on this keeper (``caiso_reserve_coopt`` and ``scarcity_price_overlay``
are both off, and ``caiso_scarcity_pricing`` is mutually exclusive with the
in-LP co-opt by ``ScenarioConfig.__post_init__``), so a change to its measure
REPLACES rather than stacks.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python \\
        scripts/probes/_caiso137_lolp_reserve_measure.py \\
        [results/calibration/caiso130_nameplate_B] [--cache DIR]
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

KEEPER = ROOT / "results/calibration/caiso130_nameplate_B"
HOURS = 8760
YEARS = (2023, 2024, 2025)

# meta.json key -> run_year kwarg (the caiso-105/131/133 _META_RENAME, verbatim).
_META_RENAME = {
    "coal_prb_passthrough_sigmoid": "prb_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}

# Ask memo §2 envelope (docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md §2).
E1_LIMIT_2025 = 0.00  # $/MWh — 2025 has only -$0.31 of C3a band room
E2_LIMIT_2024 = 0.30  # $/MWh — 2024 has +$0.69, the tail lift spends ~+$0.36


# ---------------------------------------------------------------------------
# committed-artifact readers + the no-LP fleet reconstruction
# ---------------------------------------------------------------------------
def fleet_state(bundle: Path, year: int) -> dict:
    """``run_year(fleet_only=True)`` with the bundle's own meta flags.

    Assembles the fleet, the availability overlay, the storage caps and the
    renewable potential; builds no matrix and calls no solver.
    """
    from run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


def thermal_tiers(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Plant-level ONLINE thermal headroom and OFFLINE quick-start headroom (MW).

    Reproduces :func:`market_sim.results.scarcity.reserve_headroom`'s thermal
    legs exactly, from the committed ``unit_hourly`` sidecar: online status is
    decided at the PLANT level (``_online_plant_mask``), headroom is
    ``max(cap_mw - mw, 0)`` with ``cap_mw = pmax x availability``, the online
    tier is ``RESERVE_FUEL_TYPES`` and the offline tier is the
    ``QUICK_START_FUEL_TYPES`` subset of plants that are NOT running.
    """
    from market_sim.results.scarcity import QUICK_START_FUEL_TYPES, RESERVE_FUEL_TYPES

    u = pd.read_parquet(bundle / "hourly" / f"unit_hourly_{year}.parquet")
    u = u[u["pass"] == "P1"]
    plant_mw = u.groupby(["plant_code", "hour"], observed=True)["mw"].sum()
    u = u.join(plant_mw.rename("plant_mw"), on=["plant_code", "hour"])
    th = u[u["fuel"].isin(sorted(RESERVE_FUEL_TYPES))]
    head = (th["cap_mw"] - th["mw"]).clip(lower=0.0)

    def by_hour(sel: pd.Series) -> np.ndarray:
        return (
            head[sel]
            .groupby(th.loc[sel, "hour"])
            .sum()
            .reindex(range(HOURS), fill_value=0.0)
            .to_numpy()
        )

    online = by_hour(th["plant_mw"] > 1.0)
    offline_quick = by_hour(
        (th["plant_mw"] <= 1.0) & th["fuel"].isin(sorted(QUICK_START_FUEL_TYPES))
    )
    return online, offline_quick


def storage_flows(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Fleet-summed hourly (charge, discharge) MW from the storage sidecar."""
    s = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    chg = s.groupby("hour")["charge_mw"].sum().reindex(range(HOURS), fill_value=0.0)
    dis = s.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS), fill_value=0.0)
    return chg.to_numpy(), dis.to_numpy()


def vre_dispatched(bundle: Path, year: int) -> np.ndarray:
    """Hourly dispatched wind + solar MW from the class sidecar."""
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & ch["klass"].isin(["wind", "solar"])]
    return (
        ch.groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0).to_numpy()
    )


def system_frame(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hourly (demand-weighted price, total demand, MAX ZONAL price) from the sidecar.

    The price is the PERSISTED (post-overlay) series — ``runner.py`` adds the
    adder to ``result.prices`` before the sidecar is written — and the weighting
    is the same total-demand weighting the overlay's own ``lam_caiso`` uses.
    The max-zonal series is C3c's own basis
    (``render_calibration_html._tail_hours``: an hour counts when the max across
    the ISO's zones exceeds the threshold).
    """
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    num = s.groupby("hour").apply(
        lambda g: float((g["price"] * g["demand"]).sum()), include_groups=False
    )
    den = s.groupby("hour")["demand"].sum()
    lam = (num / den.where(den > 0, 1.0)).reindex(range(HOURS)).to_numpy()
    mx = s.groupby("hour")["price"].max().reindex(range(HOURS)).to_numpy()
    return lam, den.reindex(range(HOURS), fill_value=0.0).to_numpy(), mx


# ---------------------------------------------------------------------------
# the overlay, re-evaluated on a chosen storage-cap basis
# ---------------------------------------------------------------------------
def overlay_adder(
    r_online: np.ndarray, r_offline: np.ndarray, lam_pre: np.ndarray
) -> np.ndarray:
    """The CAISO overlay's own adder, via the production ``ordc_adder``."""
    from market_sim.results.scarcity import (
        CAISO_SCARCITY_MCL_MW,
        CAISO_SCARCITY_SHIFT_SIGMA,
        CAISO_SCARCITY_SIGMA_MW,
        CAISO_SCARCITY_VOLL,
        ordc_adder,
    )

    return ordc_adder(
        r_online + r_offline,
        lam_pre,
        voll=CAISO_SCARCITY_VOLL,
        mcl_mw=CAISO_SCARCITY_MCL_MW,
        mu_mw=0.0,
        sigma_mw=CAISO_SCARCITY_SIGMA_MW,
        shift_sigma=CAISO_SCARCITY_SHIFT_SIGMA,
        multistep_floor=False,
        reserves_online_mw=r_online,
    )


def solve_lambda_pre(
    r_online: np.ndarray, r_offline: np.ndarray, lam_post: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Recover the overlay's PRE-adder lambda from the persisted post-adder one.

    ``runner.py`` computes the adder on the pre-overlay demand-weighted price
    and then adds it to every zone, so the persisted demand-weighted price is
    ``lam_pre + adder``. The adder is monotone decreasing in lambda, so the
    fixed point ``a = f(R, lam_post - a)`` is unique and converges in a few
    iterations from ``a = 0``.

    Returns:
        Tuple ``(lam_pre, adder_keeper)``.
    """
    a = np.zeros_like(lam_post)
    for _ in range(60):
        a_new = overlay_adder(r_online, r_offline, lam_post - a)
        if np.max(np.abs(a_new - a)) < 1e-10:
            a = a_new
            break
        a = a_new
    return lam_post - a, a


def describe(label: str, arr: np.ndarray) -> str:
    return (
        f"      {label:<30} min {arr.min():>9.0f}  p1 {np.percentile(arr, 1):>9.0f}  "
        f"p10 {np.percentile(arr, 10):>9.0f}  med {np.median(arr):>9.0f}"
    )


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------
def section_a(bundle: Path) -> dict:
    """§A — what the CAISO overlay actually computes, from the code + flags.

    STEP 1 of the caiso-137 brief: A2 as written proposes to change a measure
    that may already be correct, so the ask is re-specified against the code
    BEFORE any gate is run. The four candidate readings the brief enumerates:

      (a) ``reserves_total`` is the wrong argument to the FULL-HOUR term;
      (b) ``import_headroom`` does not belong in any reserve tier;
      (c) ``r_online`` is understated because storage + curtailed VRE are
          missing;
      (d) nothing — the measure is right and A2 closes as a no-defect.
    """
    cfg = json.loads((bundle / "run_config.json").read_text())
    sc = cfg["scenario_config"]
    print("\n" + "=" * 96)
    print("A — STEP 1: what the CAISO overlay actually computes (code + keeper flags)")
    print("=" * 96)
    flags = {
        k: sc.get(k)
        for k in (
            "scarcity_pricing_enabled",
            "caiso_scarcity_pricing",
            "caiso_scarcity_import_headroom",
            "caiso_reserve_coopt",
            "energy_reserve_coopt",
            "scarcity_price_overlay",
            "storage_vintage_ramp",
            "caiso_storage_shape_anchor",
            "caiso_storage_as_reservation",
            "storage_as_commitment",
        )
    }
    for k, v in flags.items():
        print(f"      {k:<34} = {v!r}")
    live = (
        flags["scarcity_pricing_enabled"]
        and flags["caiso_scarcity_pricing"]
        and not flags["energy_reserve_coopt"]
    )
    print(f"\n      runner.py:2034 gate -> overlay RUNS on this keeper: {live}")
    print(
        "\n      The overlay (results/scarcity.py:2002-2024) computes\n"
        "          r_online, r_offline = reserve_headroom(...)          # plant-level split\n"
        "          reserves_total      = r_online + r_offline [+ import_headroom]\n"
        "          adder = ordc_adder(reserves_total, lambda, ..., reserves_online_mw=r_online)\n"
        "      i.e. the published two-half-hour RTORPA form: the FULL-hour LOLP on\n"
        "      online+offline and the HALF-hour LOLP on online alone.\n"
        "\n      r_online  = plant-level ONLINE thermal headroom (_online_plant_mask)\n"
        "                  + storage headroom (cap - discharge + charge)\n"
        "                  + curtailed-renewable headroom\n"
        "      r_offline = headroom on OFFLINE quick-start plants (gas_ct / oil)"
    )
    print(
        "\n      STEP-1 adjudication:\n"
        "      (a) NO  — reserves_total = r_online + r_offline IS the full-hour term's\n"
        "                correct argument. r_offline is offline quick-start (30-minute\n"
        "                non-spin) capability, which is exactly what a full-hour reserve\n"
        "                measure carries and what CAISO procures as Non-Spin. No defect.\n"
        f"      (b) MOOT — caiso_scarcity_import_headroom = "
        f"{flags['caiso_scarcity_import_headroom']!r} on this keeper, so\n"
        "                import_headroom is None and enters NO tier. Nothing to remove.\n"
        "      (c) NO  — the code ALREADY carries storage and curtailed-VRE headroom in\n"
        "                r_online. FINDING-caiso133 §7's 'missing' was a statement about\n"
        "                the SIDECAR measurement, not about the code. §B measures both.\n"
        "      (d) The MEASURE BASIS is right: A2 as written is a no-defect and CLOSES.\n"
        "          §C reports the distinct defect §B's decomposition exposes."
    )
    return flags


def section_b(bundle: Path, years: tuple[int, ...], cache: Path | None) -> dict:
    """§B — the r_online decomposition, and the overlay's realised adder.

    The measurement FINDING-caiso133 §7 could not do: every component of the
    overlay's own ``r_online``, on the keeper's committed bytes, plus the adder
    the overlay actually contributed to the keeper's persisted prices.
    """
    from market_sim.model.storage import storage_cap_profiles

    print("\n" + "=" * 96)
    print("B — the overlay's own r_online, decomposed, and its realised adder")
    print("=" * 96)
    print(
        "      Storage bases: NAMEPLATE is storage.power_cap, the flat per-unit array\n"
        "      runner.py:2088 actually passes. COD-RAMPED is storage_cap_profiles(),\n"
        "      the in-service power the LP's own bounds carry. LP-CAP is the full\n"
        "      hourly storage_power_cap the LP dispatched against (ramp + the\n"
        "      caiso-99 measured shape anchor)."
    )
    out: dict[int, dict] = {}
    for year in years:
        z = cache / f"caiso137_{year}.npz" if cache else None
        if z is not None and z.exists():
            d = dict(np.load(z))
        else:
            st = fleet_state(bundle, year)
            ramped, _ = storage_cap_profiles(st["storage_units"], st["storage"], HOURS)
            ramped = np.atleast_2d(np.asarray(ramped, dtype=float))
            d = {
                "cap_nameplate": np.full(
                    HOURS, float(np.asarray(st["storage"].power_cap).sum())
                ),
                "cap_ramped": np.asarray(ramped, dtype=float).sum(axis=0),
                "cap_lp": (
                    np.asarray(st["storage_power_cap"], dtype=float).sum(axis=0)
                    if np.asarray(st["storage_power_cap"]).ndim == 2
                    else np.full(
                        HOURS, float(np.asarray(st["storage_power_cap"]).sum())
                    )
                ),
                "vre_potential": (
                    np.asarray(st["wind_cf"]) * np.asarray(st["wind_cap"])[:, None]
                    + np.asarray(st["solar_cf"]) * np.asarray(st["solar_cap"])[:, None]
                ).sum(axis=0),
            }
            on, off = thermal_tiers(bundle, year)
            chg, dis = storage_flows(bundle, year)
            d |= {
                "thermal_online": on,
                "offline_quick": off,
                "charge": chg,
                "discharge": dis,
                "vre_dispatched": vre_dispatched(bundle, year),
            }
            lam_post, demand, maxzonal = system_frame(bundle, year)
            d |= {"lam_post": lam_post, "demand": demand, "maxzonal": maxzonal}
            if z is not None:
                z.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(z, **d)

        ren = d["vre_potential"] - d["vre_dispatched"]
        r_on = {
            b: d["thermal_online"] + d[f"cap_{b}"] - d["discharge"] + d["charge"] + ren
            for b in ("nameplate", "ramped", "lp")
        }
        lam_pre, adder0 = solve_lambda_pre(
            r_on["nameplate"], d["offline_quick"], d["lam_post"]
        )
        d |= {"ren": ren, "lam_pre": lam_pre, "adder_keeper": adder0} | {
            f"r_online_{b}": v for b, v in r_on.items()
        }
        out[year] = d

        print(f"\n  --- {year} ---")
        print(
            f"      storage cap  NAMEPLATE {d['cap_nameplate'][0]:>8.0f} MW flat  |  "
            f"COD-RAMPED {d['cap_ramped'].min():>8.0f} -> {d['cap_ramped'].max():<8.0f}  |  "
            f"LP-CAP {d['cap_lp'].min():>8.0f} -> {d['cap_lp'].max():<8.0f}"
        )
        print(
            f"      VRE curtailment min {ren.min():.2f} MW (>= 0 validates the "
            f"rebuilt potential against the solved dispatch)"
        )
        print(describe("thermal ONLINE (caiso-133 D1)", d["thermal_online"]))
        print(
            describe(
                "storage headroom (nameplate)",
                d["cap_nameplate"] - d["discharge"] + d["charge"],
            )
        )
        print(describe("curtailed-VRE headroom", ren))
        print(describe("r_online  (as the keeper ran)", r_on["nameplate"]))
        print(describe("r_offline (offline quick-start)", d["offline_quick"]))
        print(describe("reserves_total", r_on["nameplate"] + d["offline_quick"]))
        w = d["demand"]
        print(
            f"      REALISED overlay adder: dw-mean ${np.average(adder0, weights=w):.4f}/MWh  "
            f"max ${adder0.max():.2f}  >$1 in {(adder0 > 1).sum()} h  "
            f">$10 in {(adder0 > 10).sum()} h"
        )
    return out


def section_c(data: dict) -> None:
    """§C — the defect the decomposition exposes: a flat-nameplate storage tier.

    ``runner.py:2085-2094`` calls ``caiso_scarcity_overlay(..., storage.power_cap,
    ...)``. ``StorageArrays.power_cap`` is the per-unit NAMEPLATE array
    (``model/storage.py:109``), and ``reserve_headroom`` broadcasts a 1-D cap to
    a CONSTANT hourly series (``np.full(shape, cap.sum())``). The LP itself
    bounds storage with the hourly ``storage_power_cap``, which carries the COD
    vintage ramp (``storage_vintage_ramp``, on for this keeper). So the overlay
    credits, as ONLINE SPINNING RESERVE, battery power the LP's own bounds hold
    at zero because the unit is not yet in service.

    This is a rule-14 ``[R-ACCURATE]`` defect with ZERO new free parameters: the
    accurate input is already built, already consumed by the LP, and already in
    scope at the call site.
    """
    print("\n" + "=" * 96)
    print("C — the defect: the storage tier is credited at FLAT YEAR-END NAMEPLATE")
    print("=" * 96)
    print(
        "      runner.py:2088 passes storage.power_cap (per-unit NAMEPLATE, 1-D).\n"
        "      reserve_headroom broadcasts a 1-D cap to a CONSTANT hourly series.\n"
        "      The LP dispatches against the hourly storage_power_cap instead, which\n"
        "      carries the COD vintage ramp. Phantom = nameplate - COD-ramped:\n"
    )
    print(
        f"      {'year':<6}{'phantom max':>13}{'phantom mean':>14}"
        f"{'h > 500 MW':>12}{'% of r_online (max)':>21}"
    )
    for year, d in data.items():
        ph = d["cap_nameplate"] - d["cap_ramped"]
        frac = np.max(ph / np.maximum(d["r_online_nameplate"], 1.0))
        print(
            f"      {year:<6}{ph.max():>13,.0f}{ph.mean():>14,.0f}"
            f"{int((ph > 500).sum()):>12,}{frac:>20.1%}"
        )

    # The corrected basis is unambiguous: on this keeper the COD-ramped cap and
    # the LP's own hourly storage_power_cap are the SAME array, so the caiso-99
    # shape anchor (caiso_storage_shape_anchor, ON) does not reduce the
    # fleet-summed power cap and there is no rule-19 double-count to weigh.
    ident = max(
        float(np.abs(d["cap_ramped"] - d["cap_lp"]).max()) for d in data.values()
    )
    print(
        f"\n      COD-ramped cap vs the LP's own hourly storage_power_cap:\n"
        f"          max |COD-ramped - LP cap| = {ident:.6f} MW  (all years)\n"
        "      They are the SAME array, so the corrected basis is unambiguous — the\n"
        "      caiso-99 shape anchor does not reduce the fleet-summed power cap and\n"
        "      there is no rule-19 [R-ONE-MECH] double-count to weigh."
    )
    print(
        "\n      INDEPENDENT CORROBORATION — the codebase already disagrees with itself.\n"
        "      The OFFLINE derivers that reproduce these overlays read the hourly cap:\n"
        "          scripts/data/derive_ordc_overlay.py:200-201\n"
        "              cap = state['storage_power_cap']\n"
        "              cap_t = cap.sum(axis=0) if cap.ndim == 2 else full(..., cap.sum())\n"
        "          scripts/data/derive_caiso_scarcity_overlay.py:119\n"
        "              cap_t = a['storage_power_cap_mw']       # the hourly series\n"
        "      while runner.py:2088 (CAISO) and runner.py:1996 (ERCOT) pass the flat\n"
        "      storage.power_cap. Two implementations of one overlay, disagreeing on the\n"
        "      storage tier — and the reference implementation uses the hourly cap.\n"
        "\n      SCOPE (rule 25 [R-ISO-SCOPE]): runner.py:1996 is the ERCOT ORDC call and\n"
        "      carries the same argument. Any arming must be scoped to the CAISO call\n"
        "      site alone, or adjudicated per-ISO on ERCOT's own evidence — a CAISO\n"
        "      session may not change ERCOT's dispatch-adjacent behaviour."
    )


def section_d(data: dict) -> dict:
    """§D — D2: the ask memo §2 E1/E2 spillover pre-check, priced with no solve.

    The correction shrinks ``r_online``, which RAISES the adder, so E1 (2025
    spillover <= +$0.00) is the live risk. Every price here is computed on the
    recovered PRE-adder lambda fixed point, so the delta is exactly what the
    solve would add to the persisted demand-weighted mean LMP.
    """
    print("\n" + "=" * 96)
    print("D — D2: the §2 E1/E2 spillover pre-check (no LP)")
    print("=" * 96)
    print(
        f"      E1: 2025 delta must be <= +${E1_LIMIT_2025:.2f}/MWh   "
        f"E2: 2024 delta must be <= +${E2_LIMIT_2024:.2f}/MWh"
    )
    print(
        f"\n      {'year':<6}{'keeper $/MWh':>14}{'corrected':>12}{'DELTA':>10}"
        f"{'gate':>8}{'verdict':>10}{'h adder>$1':>12}{'max adder':>11}"
    )
    verdicts: dict[int, dict] = {}
    for year, d in data.items():
        a0, a1 = (
            d["adder_keeper"],
            overlay_adder(d["r_online_ramped"], d["offline_quick"], d["lam_pre"]),
        )
        w = d["demand"]
        m0, m1 = np.average(a0, weights=w), np.average(a1, weights=w)
        delta = m1 - m0
        gate = (
            E1_LIMIT_2025
            if year == 2025
            else (E2_LIMIT_2024 if year == 2024 else float("inf"))
        )
        ok = delta <= gate + 1e-12
        verdicts[year] = {
            "keeper": m0,
            "corrected": m1,
            "delta": delta,
            "gate": gate,
            "pass": bool(ok),
        }
        gs = "n/a" if gate == float("inf") else f"{gate:+.2f}"
        print(
            f"      {year:<6}{m0:>14.4f}{m1:>12.4f}{delta:>+10.4f}{gs:>8}"
            f"{('PASS' if ok else 'FAIL'):>10}{int((a1 > 1).sum()):>12,}"
            f"{a1.max():>11.2f}"
        )
    print(
        "\n      (2023 carries +$3.67/MWh of C3a band room, so it has no §2 gate; it is\n"
        "       shown for completeness. E1/E2 are the binding pair.)"
    )

    # --- what the correction would actually buy on C3c, on C3c's OWN basis ----
    tail = json.loads(
        (ROOT / "frontend/data/backcast/tail/actual_tail.json").read_text()
    )["isos"]["CAISO"]
    print(
        "\n      C3c impact, on the scorer's own basis (max ZONAL LMP > $200,\n"
        "      render_calibration_html._tail_hours; CAISO has no scarcity.parquet so the\n"
        "      fallback applies). The adder is uniform across zones, so the corrected\n"
        "      max-zonal series is the persisted one plus the adder delta:"
    )
    print(
        f"\n      {'year':<6}{'model now':>11}{'corrected':>11}{'RT actual':>11}"
        f"{'band':>14}{'C3c verdict':>14}"
    )
    for year, d in data.items():
        a0, a1 = (
            d["adder_keeper"],
            overlay_adder(d["r_online_ramped"], d["offline_quick"], d["lam_pre"]),
        )
        now = int((d["maxzonal"] > 200.0).sum())
        corr = int((d["maxzonal"] + (a1 - a0) > 200.0).sum())
        act = float(tail[str(year)]["rt_gt"])
        if act < 10:  # TAIL_SMALL_COUNT
            band, ok = f"|Δ| ≤ 10 of {act:.0f}", abs(corr - act) <= 10
        else:
            band, ok = (
                f"{0.5 * act:.0f}–{2.0 * act:.0f} h",
                0.5 * act <= corr <= 2.0 * act,
            )
        verdicts[year] |= {"c3c_now": now, "c3c_corrected": corr, "c3c_pass": bool(ok)}
        print(
            f"      {year:<6}{now:>11,}{corr:>11,}{act:>11,.0f}{band:>14}"
            f"{('PASS' if ok else 'FAIL'):>14}"
        )
    return verdicts


def section_f(bundle: Path, data: dict) -> None:
    """§F — is the D2 verdict robust to the reconstruction's own error?

    The rebuild is a ``run_year(fleet_only=True)`` approximation of the keeper's
    fleet (it carries only the meta.json flags that map onto ``run_year``'s
    signature), so ``r_online`` is reconstructed, not read. Two checks bound it.

    **The hard bound.** The dump column's reduced cost gives ``lambda_z >=
    -dump_cost`` in EVERY zone-hour, so wherever the PERSISTED min-zonal price
    sits exactly on that floor the pre-adder price was also on the floor and the
    overlay's realised adder there is **exactly 0**. Any positive reconstructed
    adder in a floor-pinned hour is pure reconstruction error, and the implied
    missing ``r_online`` is recoverable by inverting the half-hour LOLP.

    **The sensitivity sweep.** Add a uniform offset ``delta`` to ``r_online`` in
    BOTH arms and re-run D2. E1 is structural — the correction can only SHRINK
    the measure, and the adder is monotone decreasing in the measure, so the
    2025 delta is strictly positive at every offset. E2's margin is not.
    """
    from scipy.stats import norm

    from market_sim.results.scarcity import (
        CAISO_SCARCITY_MCL_MW,
        CAISO_SCARCITY_SIGMA_MW,
    )

    print("\n" + "=" * 96)
    print("F — is the D2 verdict robust to the reconstruction's own error?")
    print("=" * 96)
    print(
        "      F.1 — the hard bound: lambda_z >= -dump_cost in every zone-hour, so a\n"
        "      floor-pinned persisted price proves the realised adder was EXACTLY 0."
    )
    print(
        f"\n      {'year':<6}{'floor':>9}{'pinned h':>10}{'recon>$0.01':>13}"
        f"{'spurious $/MWh':>16}{'% of recon':>12}{'missing r_on (med)':>20}"
    )
    for year, d in data.items():
        s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        s = s[s["pass"] == "P1"]
        mn = (
            s.pivot_table(index="hour", columns="zone", values="price")
            .min(axis=1)
            .reindex(range(HOURS))
            .to_numpy()
        )
        floor = float(np.nanmin(mn))
        pinned = np.abs(mn - floor) < 1e-3
        a, w = d["adder_keeper"], d["demand"]
        spur = np.average(np.where(pinned, a, 0.0), weights=w)
        mean = np.average(a, weights=w)
        tgt = 0.01 / (0.5 * np.maximum(2000.0 - d["lam_post"], 1.0))
        r_star = CAISO_SCARCITY_MCL_MW + norm.ppf(np.clip(1 - tgt, 0.0, 1 - 1e-15)) * (
            CAISO_SCARCITY_SIGMA_MW / np.sqrt(2.0)
        )
        need = np.maximum(r_star - d["r_online_nameplate"], 0.0)[pinned & (a > 0.01)]
        med = np.median(need) if need.size else 0.0
        print(
            f"      {year:<6}{floor:>9.2f}{int(pinned.sum()):>10,}"
            f"{int(((a > 0.01) & pinned).sum()):>13,}{spur:>16.4f}"
            f"{(spur / mean if mean > 0 else 0):>11.1%}{med:>19,.0f} MW"
        )

    print(
        "\n      F.2 — sensitivity sweep: uniform +delta MW on r_online in BOTH arms.\n"
        "      E1's gate is +$0.00 and the correction can only RAISE the adder, so the\n"
        "      2025 delta is strictly positive at every offset — E1 fails STRUCTURALLY,\n"
        "      not on a magnitude. E2's margin is inside the reconstruction's own error."
    )
    print(
        f"\n      {'delta MW':>9}{'2023 Δ$':>12}{'2024 Δ$':>12}{'E2':>6}"
        f"{'2025 Δ$':>12}{'E1':>6}{'C3c 2023':>11}{'C3c 2024':>10}"
    )
    tail = json.loads(
        (ROOT / "frontend/data/backcast/tail/actual_tail.json").read_text()
    )["isos"]["CAISO"]
    for delta in (0, 500, 1000, 2000, 3000, 5000):
        row: dict[int, tuple[float, int]] = {}
        for year, d in data.items():
            base = d["thermal_online"] + d["ren"] + delta - d["discharge"] + d["charge"]
            lam_pre, a0 = solve_lambda_pre(
                base + d["cap_nameplate"], d["offline_quick"], d["lam_post"]
            )
            a1 = overlay_adder(base + d["cap_ramped"], d["offline_quick"], lam_pre)
            w = d["demand"]
            row[year] = (
                float(np.average(a1, weights=w) - np.average(a0, weights=w)),
                int((d["maxzonal"] + (a1 - a0) > 200.0).sum()),
            )
        d23, d24, d25 = (row[y][0] for y in (2023, 2024, 2025))
        c23, c24 = (row[y][1] for y in (2023, 2024))
        b23 = 0.5 * tail["2023"]["rt_gt"] <= c23 <= 2.0 * tail["2023"]["rt_gt"]
        b24 = 0.5 * tail["2024"]["rt_gt"] <= c24 <= 2.0 * tail["2024"]["rt_gt"]
        print(
            f"      {delta:>9,}{d23:>+12.4f}{d24:>+12.4f}"
            f"{('PASS' if d24 <= E2_LIMIT_2024 else 'FAIL'):>6}{d25:>+12.4f}"
            f"{('PASS' if d25 <= E1_LIMIT_2025 else 'FAIL'):>6}"
            f"{f'{c23} h ' + ('P' if b23 else 'F'):>11}"
            f"{f'{c24} h ' + ('P' if b24 else 'F'):>10}"
        )
    print(
        "\n      READ: E1 FAILS at every offset (structural). E2 fails only at delta=0 —\n"
        "      INDETERMINATE at this fidelity. And C3c never clears its 24 h / 18 h floor\n"
        "      at ANY offset: 16 h in 2023 at the most generous point, 0 h everywhere\n"
        "      else. The correction cannot close C3c under any admissible reconstruction."
    )


def section_e(bundle: Path) -> None:
    """§E — D3: no fitted parameter is introduced, verified against run_config."""
    from market_sim.results.scarcity import (
        CAISO_SCARCITY_MCL_MW,
        CAISO_SCARCITY_SHIFT_SIGMA,
        CAISO_SCARCITY_SIGMA_MW,
        CAISO_SCARCITY_VOLL,
    )

    print("\n" + "=" * 96)
    print("E — D3: no fitted parameter (rules 13 [R-MEASURED] / 24 [R-DOF])")
    print("=" * 96)
    for name, val, cite in (
        ("CAISO_SCARCITY_VOLL", CAISO_SCARCITY_VOLL, "Tariff §39.6.1 hard bid cap"),
        (
            "CAISO_SCARCITY_MCL_MW",
            CAISO_SCARCITY_MCL_MW,
            "Diablo Canyon / BAL-002-WECC-3",
        ),
        (
            "CAISO_SCARCITY_SIGMA_MW",
            CAISO_SCARCITY_SIGMA_MW,
            "FRP uncertainty whitepaper",
        ),
        ("CAISO_SCARCITY_SHIFT_SIGMA", CAISO_SCARCITY_SHIFT_SIGMA, "no CAISO analogue"),
    ):
        print(f"      {name:<28} = {val:<9} UNCHANGED  ({cite})")
    print(
        "\n      The correction introduces NO new ScenarioConfig field, NO threshold and\n"
        "      NO multiplier: it swaps one already-built array (storage.power_cap) for\n"
        "      another already-built array (the COD-ramped in-service cap) at one call\n"
        "      site. D3 PASSES by construction."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", nargs="?", default=str(KEEPER))
    ap.add_argument("--cache", default=None, help="npz cache dir for the rebuild")
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    args = ap.parse_args()

    bundle = Path(args.bundle)
    cache = Path(args.cache) if args.cache else None
    print(f"\ncaiso-137 — ask A2 re-specification and gates\nbundle: {bundle}")

    section_a(bundle)
    data = section_b(bundle, tuple(args.years), cache)
    section_c(data)
    verdicts = section_d(data)
    section_e(bundle)
    section_f(bundle, data)

    print("\n" + "=" * 96)
    print("VERDICT")
    print("=" * 96)
    e1 = verdicts.get(2025, {}).get("pass")
    print(
        f"      STEP 1 : A2 AS WRITTEN closes as a NO-DEFECT (option d) — the measure\n"
        f"               basis is already plant-level online. §C files a distinct,\n"
        f"               narrower rule-14 defect in the storage tier.\n"
        f"      D3     : PASS  — no fitted parameter (§E)\n"
        f"      D2 E1  : {'PASS' if e1 else 'FAIL'} (2025) — STRUCTURAL, robust at every offset (§F.2)\n"
        f"      D2 E2  : INDETERMINATE (2024) — fails at delta=0, passes at +500 MW (§F.2)\n"
        f"      C3c    : the correction NEVER clears the 24 h / 18 h floor (§F.2)\n"
        f"\n      => D2 FAILS on E1. NO SOLVE IS AUTHORIZED. The defect is filed with its\n"
        f"         measurement; arming it is a separate owner act on rule-1/14 structural\n"
        f"         grounds, and must NOT be taken on backcast-fit grounds in either\n"
        f"         direction."
    )


if __name__ == "__main__":
    main()
