"""spp-45 phase 0 (ZERO LP): does plant 762 (Ponca) reach the LP at all?

SPP-43 §7 item 1 routed the frozen 2023-2025 block of
``data/raw/campd-unit-outages-SPP.csv`` as its own lane, on the assertion that
repairing it "moves the keeper's SCORED years". Re-deriving that block at HEAD
emits **103 rows it does not carry -- all plant 762 (Ponca) units 3 and 4,
ST_GAS, zero removals** (Ponca reaches the deriver only through
``load_retired_within_window``, so the frozen block predates that scope).

That assertion is what this probe tests, and it is testable without a solve: an
outage row can only move a scored year if the unit it names is in the LP fleet
AND has availability left to remove. Both halves are measured here.

**THE lru_cache TRAP -- why every leg runs in its OWN PROCESS.**
``outages.unit_outage_derate_factors`` is ``@lru_cache``d on its ARGUMENTS
(year, hours, bins_path, iso, flags) -- never on the extract's CONTENTS. So an
arm/control that monkeypatches ``unit_outage_csv_for_iso`` inside one process
gets a CACHE HIT on the second leg and silently re-reads the FIRST leg's
factors, producing a spurious delta of exactly zero. This probe was first
written that way and did report a spurious zero; the ``--leg`` mode exists so
the driver can fork a fresh interpreter per leg. Any zero-LP probe that swaps a
measured input by path is exposed to this and should do the same.

Legs, all zero-LP:

* **A -- the extract census.** Which plant-762 rows exist, in which years.
* **B -- 2019-2022, against the rung's COMMITTED fleet parquets.** NOTE the
  unit-id convention: most SPP units are ``<CLASS>_<zone>_p<plant>_<tranche>``
  (``ST_GAS_SPP-South_p762_peak``), NOT ``<plant>_<unit>``. A ``"762_"`` prefix
  test finds nothing and reads as "absent" -- which is how the claim that 762 is
  absent from all four years arose. It is present in **2019**.
* **C -- 2023-2025, fleet-only rebuild on keeper 12's own recipe** via
  ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``. Validated
  against leg B: on 2019-2022 the fleet-only unit-id set is IDENTICAL to the
  committed post-LP ``_P1_fleet.parquet``, so it is a faithful proxy for the
  years the slim keeper bundle cannot answer directly.
* **D -- the arm/control footprint.** Every one of the 15 ``FleetArrays`` LP
  inputs hashed under the committed and the repaired extract.

MEASURED RESULT (2026-09-17, keeper 12 ``spp42_span_a``, base ``d54cd9c5``):
2023 and 2024 -- 762 absent from the fleet, the 66 rows there cannot reach the
LP. 2025 -- 762 PRESENT (4 ST_GAS tranches, 34.000 MW) and the added rows DO
reach the overlay (new ``(762, 'ST_GAS')`` key, derate < 1.0 in 7176 of 8760
hours), but its availability is IDENTICALLY ZERO across all 8760 hours (the
COD/retirement mask), so 0.000 MWh moves. All 15 LP inputs hash byte-identical
in all three scored years. **Zero LP reach: cosmetic reproducibility wart, no
re-solve, no re-gate, no promotion owed.**
Correction to the record: the 105 rows ALREADY committed are NOT inert -- in
2019 they remove 201656.459 MWh of plant-762 available energy (242143.920 ->
40487.461, live hours 8760 -> 1368), a delta exactly equal at plant and fleet
level, so confined to plant 762 and nothing else.

Run: ``PYTHONPATH=src python3 scripts/probes/_spp45_ponca_reach_phase0.py``
"""

from __future__ import annotations

import collections
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

EXTRACT = REPO / "data/raw/campd-unit-outages-SPP.csv"
RUNG = REPO / "results/calibration/spp43_holdout_span"
KEEPER = REPO / "results/calibration/spp42_span_a"
PONCA = 762

#: ``FleetArrays`` fields that are LP inputs. The footprint claim covers all of
#: them, not just ``availability`` -- the keeper arms
#: ``mustrun_commitment_feasibility_clip``, so ``min_gen`` could in principle
#: move even when availability does not.
LP_INPUT_FIELDS = (
    "pmax", "pmin", "heat_rate", "vom", "emission_rate", "nox_rate", "so2_rate",
    "zone_idx", "fuel_type_idx", "availability", "efficiency_bin", "plant_code",
    "min_gen", "min_gen_mechanism",
)

#: Matches a plant code in EITHER SPP unit-id convention:
#: ``762_1`` and ``ST_GAS_SPP-South_p762_peak``.
def _has_plant(unit_id: str, code: int = PONCA) -> bool:
    for part in str(unit_id).split("_"):
        if part.isdigit() and int(part) == code:
            return True
        if len(part) > 1 and part[0] == "p" and part[1:].isdigit() and int(part[1:]) == code:
            return True
    return False


def _hash(x) -> str:
    if x is None:
        return "None"
    a = np.ascontiguousarray(np.asarray(x))
    if a.dtype == object:
        a = np.asarray([str(v) for v in a.ravel()]).astype("U")
    return hashlib.sha256(a.tobytes()).hexdigest()[:16]


def leg(bundle: str, year: int, extract: str) -> dict:
    """One leg, in THIS process. The driver forks one interpreter per call."""
    import market_sim.data.outages as outages

    if extract != "-":
        real = outages.unit_outage_csv_for_iso

        def patched(iso, *a, **kw):
            p = real(iso, *a, **kw)
            return (
                Path(extract)
                if (iso or "").upper() == "SPP"
                and p.name.startswith("campd-unit-outages-SPP")
                else p
            )

        outages.unit_outage_csv_for_iso = patched

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    b = REPO / "results/calibration" / bundle
    meta = json.loads((b / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(b, year))
    fa = run_year(
        year, meta["iso"], 8760, float(meta["gas_prices"][str(year)]), {},
        fleet_only=True, **kw,
    )["fleet_arrays"]

    ids = list(fa.unit_ids)
    idx = [i for i, v in enumerate(ids) if _has_plant(v)]
    av = np.asarray(fa.availability, dtype=float)
    pm = np.asarray(fa.pmax, dtype=float)
    d = outages.unit_outage_derate_factors(year, 8760, iso="SPP").get((PONCA, "ST_GAS"))
    out = {
        "year": year,
        "extract": Path(extract).name if extract != "-" else "COMMITTED",
        "n_units": len(ids),
        "n_762": len(idx),
        "pmax_762": round(float(pm[idx].sum()), 6) if idx else 0.0,
        "energy_762": round(float((av[idx] * pm[idx][:, None]).sum()), 6) if idx else 0.0,
        "live_hours_762": int((av[idx] > 0).any(0).sum()) if idx else 0,
        "fleet_energy": round(float((av * pm[:, None]).sum()), 6),
        "overlay_762": d is not None,
        "overlay_hours_lt1": int((np.asarray(d, float) < 1.0).sum()) if d is not None else None,
        "unit_ids": _hash(np.asarray(ids)),
    }
    out.update({f: _hash(getattr(fa, f, None)) for f in LP_INPUT_FIELDS})
    return out


def _fork(bundle: str, year: int, extract: str) -> dict:
    """Run one leg in a FRESH interpreter -- the lru_cache guard."""
    p = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--leg", bundle, str(year), extract],
        capture_output=True, text=True, cwd=str(REPO),
        env={**__import__("os").environ, "PYTHONPATH": "src"},
    )
    for line in p.stdout.splitlines():
        if line.startswith("LEG "):
            return json.loads(line[4:])
    raise RuntimeError(f"leg failed ({bundle} {year} {extract}):\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")


def build_variants(scratch: Path) -> tuple[Path, Path]:
    """Write the REPAIRED (+103 Ponca rows) and STRIPPED (-all 762) extracts."""
    scratch.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(EXTRACT.open()))
    flds = csv.DictReader(EXTRACT.open()).fieldnames
    rede = scratch / "spp45_rederive_2023_2025.csv"
    if not rede.exists():
        raise SystemExit(
            "Re-derive the frozen block first, at the sidecar's FROZEN settings "
            "(rule 23 -- differ in --years and nothing else):\n"
            "  PYTHONPATH=src python3 scripts/data/derive_campd_unit_outages.py --iso SPP \\\n"
            "    --years 2023 2024 2025 --min-outage-days 5.0 --min-inmerit-hours 24 \\\n"
            "    --high-load-pctl 0.85 --fullstop-override-cf 0.02 --fullstop-override-days 5 \\\n"
            f"    --out {rede}"
        )
    key = lambda r: (r["facility_id"], r["unit_id"], r["outage_start"], r["outage_end"])
    ko = {key(r) for r in rows}
    add = [r for r in csv.DictReader(rede.open()) if key(r) not in ko]
    rep = scratch / "campd-unit-outages-SPP-REPAIRED.csv"
    strip = scratch / "campd-unit-outages-SPP-NO762.csv"
    for path, data in (
        (rep, rows + add),
        (strip, [r for r in rows if int(r["facility_id"]) != PONCA]),
    ):
        with path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=flds)
            w.writeheader()
            w.writerows({k: r.get(k, "") for k in flds} for r in data)
    print(f"  repaired: {len(rows)} + {len(add)} rows   stripped: "
          f"{len([r for r in rows if int(r['facility_id']) != PONCA])} rows")
    return rep, strip


def main() -> None:
    scratch = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / ".spp45"

    rows = list(csv.DictReader(EXTRACT.open()))
    p = [r for r in rows if int(r["facility_id"]) == PONCA]
    print(f"\n{'=' * 100}\nLEG A -- extract census\n{'=' * 100}")
    print(f"  total {len(rows)} rows; plant {PONCA}: {len(p)} rows, "
          f"by start year {dict(sorted(collections.Counter(r['outage_start'][:4] for r in p).items()))}")
    rep, strip = build_variants(scratch)

    print(f"\n{'=' * 100}\nLEG B/D -- 2019-2022 ({RUNG.name}): reach of the Ponca rows ALREADY committed\n{'=' * 100}")
    for y in (2019, 2020, 2021, 2022):
        c, a = _fork(RUNG.name, y, "-"), _fork(RUNG.name, y, str(strip))
        if not c["n_762"]:
            print(f"  {y}: 762 ABSENT from fleet -> zero reach; "
                  f"fleet energy identical: {c['fleet_energy'] == a['fleet_energy']}")
            continue
        print(f"  {y}: 762 PRESENT ({c['n_762']} tranches, {c['pmax_762']:.3f} MW) -- rows remove "
              f"{a['energy_762'] - c['energy_762']:+.3f} MWh "
              f"({a['energy_762']:.3f} -> {c['energy_762']:.3f}), live hours "
              f"{a['live_hours_762']} -> {c['live_hours_762']}; fleet-level delta "
              f"{a['fleet_energy'] - c['fleet_energy']:+.3f} MWh (confined: "
              f"{abs((a['fleet_energy']-c['fleet_energy'])-(a['energy_762']-c['energy_762'])) < 1e-3})")

    print(f"\n{'=' * 100}\nLEG C/D -- 2023-2025 ({KEEPER.name}): reach of the 103 rows the frozen block OMITS\n{'=' * 100}")
    allsame = True
    for y in (2023, 2024, 2025):
        c, a = _fork(KEEPER.name, y, "-"), _fork(KEEPER.name, y, str(rep))
        same = [f for f in ("unit_ids",) + LP_INPUT_FIELDS if c[f] == a[f]]
        allsame &= len(same) == len(LP_INPUT_FIELDS) + 1
        where = (f"ABSENT from the LP fleet ({c['n_units']} units)" if not c["n_762"]
                 else f"PRESENT ({c['n_762']} tranches, {c['pmax_762']:.3f} MW), "
                      f"availability live hours {c['live_hours_762']}/8760")
        print(f"  {y}: 762 {where}")
        print(f"       overlay key under repaired extract: {a['overlay_762']}"
              + (f" (derate < 1.0 in {a['overlay_hours_lt1']}/8760 h)" if a["overlay_762"] else "")
              + f" | 762 energy {c['energy_762']:.3f} -> {a['energy_762']:.3f} MWh")
        print(f"       LP inputs identical: {len(same)}/{len(LP_INPUT_FIELDS) + 1}"
              f" | fleet energy {c['fleet_energy']:.6f} vs {a['fleet_energy']:.6f}")

    print(f"\n{'=' * 100}\nSTOP GATE\n{'=' * 100}")
    print("  VERDICT: " + (
        "every LP input byte-identical in all three scored years -> the frozen block's\n"
        "  non-reproducibility has ZERO LP reach. Cosmetic wart; no re-solve, no re-gate,\n"
        "  no promotion owed."
        if allsame else
        "an LP input MOVED -> rule 14 [R-ACCURATE] repair; re-solve 2023-2025, re-gate, promote."
    ))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--leg":
        print("LEG " + json.dumps(leg(sys.argv[2], int(sys.argv[3]), sys.argv[4])))
    else:
        main()
