"""nyiso-122 — CONSTRUCTION probe for ``nyiso_iroquois_winter_spread`` (no LP).

Builds NYISO's delivered gas-price object **twice at one HEAD** — flag off (the
keeper's committed construction) and flag on — and diffs the monthly reference
hub and every zone's monthly delivered price.  No LP, no dual, no solve: the
nyiso-118 / nyiso-119 pattern, because a construction claim must be settled on
construction before a solve is spent (and because a solved dual can only be
byte-identical when the mechanism does nothing — the nyiso-115 G2 error).

What it is here to settle, ahead of the pre-registration:

1. **Does the mechanism conserve the measured SOM ANNUAL spread?**  Queue item 4's
   blocker (matrix section 5.5) rests on "its construction conserves the annual
   spread; re-arming alone just moves the miss to summer".  That is a
   *construction* claim and is checked here, not assumed.
2. **WHICH months and WHICH zones move, and by how much.**  nyiso-122's phase-0
   decomposition localizes the 2025 C3a miss to Jan+Feb (the $100-300 band, not
   the tail) and Jun+Jul (the >$300 tail).  The mechanism is only a candidate for
   the WINTER half, so the probe measures whether its lift actually lands in
   Jan/Feb and what it withdraws from the summer months.

Rule 23 ``[R-FROZEN-DERIVE]``: nothing is re-derived.  The construction, its
inputs and its constants are the committed ones; this probe only *evaluates* the
already-shipped function at both flag settings.

Outputs ``results/calibration/_nyiso122_iroquois_construction.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import hubs
from market_sim.data.fuel.basis import nyiso as nyb

YEARS: tuple[int, ...] = (2023, 2024, 2025)  # rule 22 -- training years only
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/calibration/_nyiso122_iroquois_construction.json"


def _cfg(arm_on: bool) -> ScenarioConfig:
    """Keeper-recipe NYISO config with only the one flag flipped.

    The two prerequisites the mechanism declares (``nyiso_zonal_gas_basis`` and
    ``gas_hub_basis_overlay``) are BOTH already armed on the keeper
    ``2026-08-04-nyiso-120-c119-scope``, so the flag is directly armable and this
    is a genuine single-delta.
    """
    return ScenarioConfig(
        iso="NYISO",
        mode="backcast",
        nyiso_zonal_gas_basis=True,
        gas_hub_basis_overlay=True,
        gas_hub_basis_daily=True,
        gas_daily_shape=True,
        nyiso_downstate_ct_gas_daily=True,
        nyiso_iroquois_winter_spread=arm_on,
    )


def _hub_monthly(cfg: ScenarioConfig, year: int) -> np.ndarray | None:
    """Reference-hub monthly delivered gas price ($/MMBtu) under ``cfg``."""
    return hubs.iso_hub_monthly_gas_prices(cfg, year)


def measure(year: int) -> dict:
    """Off-vs-on construction diff for ``year``."""
    off, on = _cfg(False), _cfg(True)
    h_off, h_on = _hub_monthly(off, year), _hub_monthly(on, year)
    rec = nyb.nyiso_reconciled_reference_monthly(year)
    ratios = nyb.nyiso_zonal_gas_ratios_monthly(on, year)

    row: dict = {"year": year}
    if h_off is None or h_on is None:
        row["status"] = "INCOMPLETE — a source series is missing for this year"
        return row

    row["hub_monthly_off"] = [round(float(v), 4) for v in h_off]
    row["hub_monthly_on"] = [round(float(v), 4) for v in h_on]
    row["hub_delta"] = [round(float(a - b), 4) for a, b in zip(h_on, h_off)]
    row["hub_annual_off"] = round(float(np.nanmean(h_off)), 4)
    row["hub_annual_on"] = round(float(np.nanmean(h_on)), 4)
    # THE CONSERVATION TEST: does the reference hub's annual mean survive?
    row["hub_annual_delta"] = round(float(np.nanmean(h_on) - np.nanmean(h_off)), 5)

    if rec is not None:
        iroq, transco = rec
        row["transco_monthly"] = [round(float(v), 4) for v in transco]
        row["spread_on"] = [round(float(a - b), 4) for a, b in zip(iroq, transco)]
        row["spread_annual_on"] = round(float(np.nanmean(iroq - transco)), 5)
    # THE QUANTITY THE LP ACTUALLY SEES is the PER-ZONE delivered monthly price,
    # and the two arms build it by different routes -- OFF layers FLAT ANNUAL
    # ADDITIVE offsets on the flat-construction hub, ON multiplies the reconciled
    # hub by each zone's own measured monthly RATIO.  Comparing hub-to-hub would
    # therefore misread every zone but the reference; both routes are evaluated.
    offsets = nyb.nyiso_zonal_gas_offsets(year)
    if offsets:
        row["zone_offsets_off"] = {z: round(float(v), 4) for z, v in sorted(offsets.items())}
        row["zone_delivered_off"] = {
            z: [round(float(h_off[m] + off), 4) for m in range(12)]
            for z, off in sorted(offsets.items())
        }
    if ratios:
        row["zone_ratios"] = {
            z: [round(float(v), 4) for v in r] for z, r in sorted(ratios.items())
        }
        row["zone_delivered_on"] = {
            z: [round(float(h_on[m] * r[m]), 4) for m in range(12)]
            for z, r in sorted(ratios.items())
        }
    if offsets and ratios:
        row["zone_delivered_delta"] = {
            z: [
                round(float(h_on[m] * ratios[z][m] - (h_off[m] + offsets[z])), 4)
                for m in range(12)
            ]
            for z in sorted(set(offsets) & set(ratios))
        }
    return row


def main() -> None:
    res = {
        "probe": "nyiso-122 nyiso_iroquois_winter_spread CONSTRUCTION diff (no LP)",
        "keeper": "2026-08-04-nyiso-120-c119-scope",
        "flag": "nyiso_iroquois_winter_spread",
        "prereqs_on_keeper": {
            "nyiso_zonal_gas_basis": True,
            "gas_hub_basis_overlay": True,
        },
        "years": list(YEARS),
        "results": [measure(y) for y in YEARS],
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n")

    for r in res["results"]:
        print(f"=== {r['year']}")
        if "hub_delta" not in r:
            print("   ", r.get("status"))
            continue
        print("   mon   hub_off   hub_on    delta     transco    spread_on")
        for m in range(12):
            tr = r.get("transco_monthly", [float("nan")] * 12)[m]
            sp = r.get("spread_on", [float("nan")] * 12)[m]
            print(
                f"   {MONTHS[m]:>3} {r['hub_monthly_off'][m]:9.3f} "
                f"{r['hub_monthly_on'][m]:9.3f} {r['hub_delta'][m]:+9.3f} "
                f"{tr:10.3f} {sp:11.3f}"
            )
        print(
            f"   ANNUAL hub off {r['hub_annual_off']:.4f}  on {r['hub_annual_on']:.4f}"
            f"  delta {r['hub_annual_delta']:+.5f}"
            f"  | mean spread on {r.get('spread_annual_on')}"
        )
        if "zone_delivered_delta" in r:
            print("   PER-ZONE DELIVERED $/MMBtu, ON minus OFF (what the LP sees):")
            print("                     " + " ".join(f"{m:>6}" for m in MONTHS))
            for z, dd in r["zone_delivered_delta"].items():
                print(f"     {z:<15}" + " ".join(f"{v:+6.2f}" for v in dd))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
