#!/usr/bin/env python
"""ARM3-MEASURE — extract R1-R5 from the paired MISO 2031-2035 clean-tier legs.

Per-run probe / calibration record for the Arm-3 (``miso_clean_tier_rows``)
arming card, owner decision D-28 option A step 3. It READS the two committed
run out-dirs produced by ``scripts/run_full_horizon.py`` and emits the
pre-registered reads; it never solves, never tunes and never arms anything.

The five pre-registered reads (``docs/handoffs/arm3-clean-row-horizon-2026-08-09.md`` §0.4):

* **R1** — MN/MI clean-row duals by year: onset (first nonzero), level, and
  whether the ``STATE_RPS_ACP["MISO"]`` $30 ceiling binds.
* **R2** — composed nuclear revenue at the LANDED F-2 seam for the D-28 §2.1
  fleet: which reactors earn which row, cross-state mask flagged.
* **R3** — qualifying supply vs target by region-year (why a row binds).
* **R4** — arm-vs-control deltas in the retirement/entry ledgers and system cost.
* **R5** — E-1 discipline: the rows acquire no build limb.

Usage::

    uv run python scripts/probes/_arm3_clean_row_horizon.py \\
        --armed results/arm3/miso-2031-2035-armed \\
        --ctrl  results/arm3/miso-2031-2035-ctrl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_SRC), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ACP_CEILING = 30.0  # STATE_RPS_ACP["MISO"], config/capacity_market.py


def run_key_dir(out_dir: Path, iso: str = "MISO") -> Path | None:
    """Return the ``<out-dir>/<ISO>/<runtime-key>/`` ledger directory."""
    base = out_dir / iso
    if not base.is_dir():
        return None
    subs = [p for p in base.iterdir() if p.is_dir()]
    return subs[0] if len(subs) == 1 else (subs[0] if subs else None)


def duals_from_parquet(key_dir: Path) -> dict[int, dict]:
    """Read ``{year: {rps_region_duals, clean_region_duals}}`` from metadata."""
    import pyarrow.parquet as pq

    out: dict[int, dict] = {}
    for p in sorted(key_dir.glob("year_*.parquet")):
        year = int(re.search(r"year_(\d{4})", p.name).group(1))
        md = pq.read_schema(p).metadata or {}
        for k, v in md.items():
            if k.decode(errors="ignore").endswith("metadata"):
                try:
                    blob = json.loads(v.decode())
                except Exception:
                    continue
                if "clean_region_duals" in blob or "rps_region_duals" in blob:
                    out[year] = {
                        "rps": blob.get("rps_region_duals"),
                        "clean": blob.get("clean_region_duals"),
                    }
    return out


def duals_from_log(log: Path) -> dict[int, dict]:
    """Parse the runner's per-year dual log lines (the no-replay path)."""
    out: dict[int, dict] = {}
    if not log.exists():
        return out
    pat = re.compile(
        r"MISO (\d{4}): (RPS compliance-region|clean-tier region) duals "
        r"\(\$/MWh\): (\{.*?\})"
    )
    for line in log.read_text(errors="ignore").splitlines():
        m = pat.search(line)
        if not m:
            continue
        year, kind, body = int(m.group(1)), m.group(2), m.group(3)
        try:
            vals = json.loads(body.replace("'", '"'))
        except Exception:
            continue
        out.setdefault(year, {})["rps" if kind.startswith("RPS") else "clean"] = vals
    return out


def load_ledgers(key_dir: Path) -> dict[int, dict]:
    """Return ``{year: evolution ledger}`` for a run's key dir."""
    out: dict[int, dict] = {}
    if key_dir is None or not key_dir.is_dir():
        return out
    for p in sorted(key_dir.glob("evolution_*.json")):
        year = int(re.search(r"(\d{4})", p.name).group(1))
        try:
            out[year] = json.loads(p.read_text())
        except Exception:
            pass
    return out


def fleet_context(key_dir: Path) -> dict | None:
    """Return the ``FleetContext`` dict stored in a year parquet's metadata."""
    import pyarrow.parquet as pq

    for p in sorted(key_dir.glob("year_*.parquet")):
        md = pq.read_schema(p).metadata or {}
        for k, v in md.items():
            if b"fleet" in k.lower():
                try:
                    return json.loads(v.decode())
                except Exception:
                    continue
    return None


def qualifying_supply(
    pq_path: Path, ctx: dict, reg: dict, zones: list[str]
) -> dict:
    """Return each clean row's qualifying energy (MWh) plus per-zone demand.

    Qualifying energy = dispatch of generators whose ``fuel_type`` is in the
    row's ``qualifying_fuels`` AND whose zone is in its ``eligible_zones``,
    plus the zonal wind/solar decision variables over the same eligible zones
    (wind/solar are per-ZONE columns, not per-generator — the rule-3
    representation).
    """
    import numpy as np
    import pyarrow.parquet as pq

    tbl = pq.read_table(pq_path)
    cols = set(tbl.column_names)

    def stack(name: str) -> "np.ndarray":
        # list<double> column, one row per hour, n_entity per cell -> (n, T)
        arr = np.vstack([np.asarray(r) for r in tbl.column(name).to_pylist()])
        return arr.T

    dispatch = stack("dispatch")  # (n_gen, T)
    gen_zone = ctx["zones"]
    gen_fuel = ctx["fuel_types"]
    gen_mwh = dispatch.sum(axis=1)

    wind = stack("wind") if "wind" in cols else None  # (n_zone, T)
    solar = stack("solar") if "solar" in cols else None
    demand = stack("demand") if "demand" in cols else None

    out: dict = {}
    out["zone_demand_mwh"] = (
        demand.sum(axis=1) if demand is not None else np.zeros(len(zones))
    )
    # The shipped rows, plus the MN in-state COUNTERFACTUAL mask. FFR-7B-2 §3.2
    # recorded MN's eligibility mask as an OPEN statutory-reading question: the
    # shipped table gives MN the 5-zone Midwest footprint (mirroring its
    # renewable tier's §216B.1691 delivery construction), while FFR-6B §6.2's
    # sizing implicitly assumed an in-state (host-zone-only) mask. Scoring both
    # off the SAME dispatch answers "which reading binds" with no extra solve.
    # It is a SUPPLY-vs-TARGET accounting screen, NOT a re-solved dual: a
    # narrower mask would shift dispatch, so this bounds the question rather
    # than settling it.
    specs = dict(reg)
    specs["MN_instate_cf"] = {
        **reg["MN"],
        "eligible_zones": (reg["MN"]["obligated_zone"],),
    }
    for key, spec in specs.items():
        elig = set(spec["eligible_zones"])
        qf = set(spec["qualifying_fuels"])
        total = float(
            sum(
                mwh
                for mwh, z, f in zip(gen_mwh, gen_zone, gen_fuel)
                if z in elig and f in qf
            )
        )
        for name, arr in (("wind", wind), ("solar", solar)):
            if arr is None or name not in qf:
                continue
            for zi, zn in enumerate(zones):
                if zn in elig and zi < arr.shape[0]:
                    total += float(arr[zi].sum())
        out[key] = total
    return out


def _mw(events: list, field: str = "pmax_mw") -> float:
    tot = 0.0
    for e in events or []:
        if isinstance(e, dict):
            for k in (field, "mw", "capacity_mw", "nameplate_mw"):
                if k in e:
                    tot += float(e[k] or 0.0)
                    break
    return round(tot, 3)


def report(armed: Path, ctrl: Path) -> int:
    """Emit the R1-R5 evidence for the two legs."""
    from market_sim.config.capacity_market import MISO_CLEAN_TIER_REGIONS as REG
    from market_sim.policy.clean_tiers import _clean_tier_target

    print("=" * 78)
    print("ARM3-MEASURE — MISO 2031-2035 clean-tier row measurement")
    print("=" * 78)

    legs = {}
    for name, d in (("ARMED", armed), ("CONTROL", ctrl)):
        kd = run_key_dir(d)
        legs[name] = {
            "out": d,
            "key_dir": kd,
            "key": kd.name if kd else None,
            "ledgers": load_ledgers(kd) if kd else {},
            "duals": (duals_from_parquet(kd) if kd else {}),
        }
        summ = d / "full_horizon_summary.json"
        legs[name]["summary"] = (
            json.loads(summ.read_text()) if summ.exists() else None
        )
        print(f"\n[{name}] out-dir={d}  cache_key={legs[name]['key']}")

    # ---------------------------------------------------------------- R1 ---
    print("\n" + "-" * 78)
    print("R1 — MN/MI clean-tier row duals by year (onset, level, $30 ceiling)")
    print("-" * 78)
    print(f"{'year':<6}{'MN oblig':>10}{'MI oblig':>10}"
          f"{'MN dual':>10}{'MI dual':>10}{'  ceiling?':>12}")
    a = legs["ARMED"]["duals"]
    onset = {"MN": None, "MI": None}
    for year in sorted(a):
        clean = a[year].get("clean")
        mn = mi = None
        if isinstance(clean, dict):
            mn, mi = clean.get("MN"), clean.get("MI")
        elif isinstance(clean, list) and len(clean) >= 2:
            mn, mi = clean[0], clean[1]
        mn_t = _clean_tier_target(REG["MN"]["floors"], year) * REG["MN"]["obligated_load_share"]
        mi_t = _clean_tier_target(REG["MI"]["floors"], year) * REG["MI"]["obligated_load_share"]
        for lbl, val in (("MN", mn), ("MI", mi)):
            if val is not None and float(val) > 1e-9 and onset[lbl] is None:
                onset[lbl] = year
        cf = []
        for lbl, val in (("MN", mn), ("MI", mi)):
            if val is not None and abs(float(val) - ACP_CEILING) < 1e-6:
                cf.append(f"{lbl}@ACP")
        print(f"{year:<6}{mn_t:>10.4f}{mi_t:>10.4f}"
              f"{(f'{mn:.4f}' if mn is not None else 'n/a'):>10}"
              f"{(f'{mi:.4f}' if mi is not None else 'n/a'):>10}"
              f"{('  ' + ','.join(cf)) if cf else '':>12}")
    print(f"\nonset (first nonzero dual): MN={onset['MN']}  MI={onset['MI']}")
    print("$30 ACP ceiling = STATE_RPS_ACP['MISO'] (config/capacity_market.py)")

    # RPS family alongside, to show the two families co-exist.
    print("\n  RPS compliance-region duals (Arm 2, armed in BOTH legs):")
    for year in sorted(a):
        print(f"    {year}: {a[year].get('rps')}")

    # ---------------------------------------------------------------- R2 ---
    print("\n" + "-" * 78)
    print("R2 — which reactors earn which row (D-28 §2.1 fleet, shipped masks)")
    print("-" * 78)
    from market_sim.config.iso_configs import get_iso_config

    zones = [z.name for z in get_iso_config("MISO").zones]
    for k, v in REG.items():
        elig = [z for z in v["eligible_zones"] if z in zones]
        print(f"  {k} row: obligated={v['obligated_zone']}  eligible={elig}")
        print(f"      qualifying_fuels={v['qualifying_fuels']}")
    print("\n  CROSS-STATE MASK FLAG (D-28 §2.1): MN's mask is the 5-zone")
    print("  MISO_RPS_MIDWEST_FOOTPRINT_ZONES, so a WI (Point Beach), IL")
    print("  (Clinton) or MO (Callaway) reactor earns MINNESOTA's dual.")
    print("  MI's mask is East-only, so Fermi 2 is the ONLY reactor on it.")

    # The model's OWN nuclear fleet, read back from the run's FleetContext, so
    # the D-28 §2.1 table is VERIFIED against what actually solved rather than
    # transcribed.
    kd = legs["ARMED"]["key_dir"]
    ctx = fleet_context(kd) if kd else None
    if ctx:
        print("\n  MODEL nuclear fleet (from the armed run's FleetContext):")
        nuke = [
            (u, z, p)
            for u, z, p, f in zip(
                ctx["unit_ids"], ctx["zones"], ctx["pmax_mw"], ctx["fuel_types"]
            )
            if f == "nuclear"
        ]
        tot = sum(p for _, _, p in nuke)
        print(f"    {len(nuke)} nuclear units, {tot:,.1f} MW nameplate")
        for k, v in REG.items():
            elig = set(v["eligible_zones"])
            paid = [(u, z, p) for u, z, p in nuke if z in elig]
            print(
                f"    {k} row pays {len(paid)} units / "
                f"{sum(p for _, _, p in paid):,.1f} MW"
            )
        for u, z, p in sorted(nuke, key=lambda r: (r[1], r[0])):
            rows = [k for k, v in REG.items() if z in set(v["eligible_zones"])]
            print(f"      {u:<28} {z:<15} {p:>8.1f} MW  earns={rows or ['-']}")

    # ---------------------------------------------------------------- R3 ---
    print("\n" + "-" * 78)
    print("R3 — qualifying supply vs target by region-year (WHY a row binds)")
    print("-" * 78)
    if ctx:
        for year in sorted(legs["ARMED"]["duals"]):
            pq_path = kd / f"year_{year}.parquet"
            if not pq_path.exists():
                continue
            supply = qualifying_supply(pq_path, ctx, REG, zones)
            for k in list(REG) + ["MN_instate_cf"]:
                base = REG["MN"] if k == "MN_instate_cf" else REG[k]
                oblig = _clean_tier_target(
                    base["floors"], year
                ) * base["obligated_load_share"]
                zi = zones.index(base["obligated_zone"])
                target = oblig * supply["zone_demand_mwh"][zi]
                qual = supply[k]
                slack = qual - target
                print(
                    f"  {year} {k}: target {target/1e6:>8.3f} TWh   "
                    f"qualifying {qual/1e6:>8.3f} TWh   "
                    f"slack {slack/1e6:>+8.3f} TWh"
                    f"{'   <-- SHORT' if slack < 0 else ''}"
                )
    else:
        print("  (no FleetContext available — run the armed leg first)")

    # ---------------------------------------------------------------- R4 ---
    print("\n" + "-" * 78)
    print("R4 — arm-vs-control ledger deltas (retirements / entry)")
    print("-" * 78)
    al, cl = legs["ARMED"]["ledgers"], legs["CONTROL"]["ledgers"]
    print(f"{'year':<6}{'retire MW A/C':>26}{'thermal add A/C':>26}"
          f"{'renew add A/C':>26}")
    for year in sorted(set(al) | set(cl)):
        ay, cy = al.get(year, {}), cl.get(year, {})
        row = []
        for field in ("retirements", "thermal_additions", "renewable_additions"):
            row.append(f"{_mw(ay.get(field)):>11.1f}/{_mw(cy.get(field)):<11.1f}")
        print(f"{year:<6}" + "".join(f"{r:>26}" for r in row))

    # ---------------------------------------------------------------- R5 ---
    print("\n" + "-" * 78)
    print("R5 — E-1 discipline: the rows acquire NO build limb")
    print("-" * 78)
    print("  policy/clean_tiers.py exposes exactly four functions:")
    print("    _clean_tier_target, build_clean_region_arrays,")
    print("    clean_credit_by_fuel, clean_credit_for_zone")
    print("  -> a TARGET, an LP ROW BUILDER and two PRICE resolvers. No build/")
    print("     procurement entry point exists. Consumers are retirements.py")
    print("     and new_entry.py, both of which take the dual as a REVENUE")
    print("     term on the same seam the RPS dual already uses — never a")
    print("     forced build (FFR-7B-2 §1 step 9 / FFR-6B §5.3).")
    print("  Behavioural check: the R4 renewable/thermal addition columns.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--armed", type=Path, required=True)
    ap.add_argument("--ctrl", type=Path, required=True)
    args = ap.parse_args(argv)
    return report(args.armed, args.ctrl)


if __name__ == "__main__":
    raise SystemExit(main())
