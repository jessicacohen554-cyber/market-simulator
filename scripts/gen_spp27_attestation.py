"""Emit the SPP-27 calibration attestation for ``results/calibration/spp27_span``.

SPP-27 is SPP keeper 8's recipe (``results/calibration/spp64_span``,
``2026-09-10-spp-64-stgas-selfcommit``) plus **exactly one change**:
``mustrun_window_commitment_grain`` is armed, so the per-plant must-run window
is placed at the WHOLE-OPERATING-DAY commitment grain instead of on
individually top-ranked hours. Size (``online_frac``), level (``committed_pct``)
and membership are untouched.

**THE DOF LEDGER IS INHERITED UNCHANGED — this lane adds ZERO free parameters.**
``mustrun_window_commitment_grain`` is a boolean gate with no threshold, share,
multiplier or length: the grain is the operating day, and ``round(k/24)`` is
arithmetic on the existing ``online_frac``. So ``n_entries`` stays 3 and
``n_residual`` stays 2, and the authorized price-tuning channel (the uniform
0.93 fossil offer bands) is replayed VERBATIM and is not re-cut by this lane.

WHY IT EXISTS is card **R-be**, the named rule-17 ``[R-FLOOR-WINDOW]`` defect
keeper 8 carries: the floor asserts a COMMITMENT — a day-ahead, whole-operating-
day decision — but the engine places it by ranking INDIVIDUAL HOURS by system
load, so it inherits the diurnal shape of LOAD rather than of COMMITMENT.
Charter and every phase-0 number:
``docs/handoffs/PRECOMMIT-spp-27-commitment-grain-2026-09-10.md``.

This is NOT the ``replay_keeper --out-dir`` attestation gap being papered over:
that driver does not propagate ``calibration_attestation.json`` into an
``--out-dir`` bundle, so without this script the span scores C6 UNATTESTED for a
plumbing reason rather than a governance one.

Usage:
    python scripts/gen_spp27_attestation.py [--bundle results/calibration/spp27_span]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp64_span/calibration_attestation.json"
DEFAULT_BUNDLE = REPO / "results/calibration/spp27_span"


def build() -> dict:
    """Return the SPP-27 attestation: keeper 8's ledger, unchanged, plus the switch."""
    att = json.loads(KEEPER.read_text())

    fp = att["free_parameters"]
    fp["inherited_from"] = "spp64_span (SPP keeper 8)"
    fp["inheritance_basis"] = (
        "SPP-27 is the SPP-64 recipe plus ONE armed ScenarioConfig gate, "
        "mustrun_window_commitment_grain. Every keeper-8 entry carries over "
        "unchanged: no offer band, structural share or shared default is "
        "touched, and the authorized price-tuning channel declared below is "
        "replayed VERBATIM at 0.93 and NOT re-cut by this lane. NOTHING IS "
        "ADDED: the gate is a boolean with no threshold, share, multiplier or "
        "length — the grain is the operating day, the period a unit commitment "
        "is made for, and round(k/24) is arithmetic on the existing "
        "online_frac. The rule-23-frozen thermal_tranches_SPP.csv is neither "
        "regenerated nor touched. n_entries stays 3 and n_residual stays 2."
    )
    # Rule 21 [R-DOF]: recomputed from the inherited entries, never retyped.
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    gov = att["governance"]
    gov["attested_by"] = (
        "SPP-27 (2026-09-10): SPP keeper 8's recipe "
        "(2026-09-10-spp-64-stgas-selfcommit — st_gas_mustrun_per_plant on "
        "SPP-62's coal supply-class census, itself on keeper 6's "
        "eia860_vintage_tracks_solve_year and SPP-52a's authorized offer-curve "
        "level) plus ONE change: mustrun_window_commitment_grain armed. ONE "
        "--years 2023 2024 2025 invocation, years sequential (rules 12 / 16). "
        "The authorized price-tuning channel declared above is replayed "
        "VERBATIM at 0.93 on all four bands of the ten registered fossil "
        "classes and is NOT re-cut by this lane; no multiplier was swept "
        "against any gate (rule 1 [R-STRUCT] condition (c)). Rule 21 [R-DOF]: "
        "ledger inherited from keeper 8 with ZERO additions — n_entries 3, "
        "n_residual 2, both unchanged. The arm was screened on 2023 — the year "
        "of the mechanism's OWN largest measured footprint (858,999.2 MWh of "
        "floor moved, 22.20 % of the mechanism's floored energy, against "
        "806,653.2 / 19.61 % and 669,504.3 / 19.25 %), named in the PRECOMMIT "
        "before the solve and demonstrably NOT the failing-residual choice "
        "(2024 carries the larger C1 ST_GAS miss and the smaller footprint) — "
        "against six structural STOP gates, NONE of which reads the target: "
        "the target is the D-4 per-unit conduct rider, and no gate reads D-4 "
        "or any per-plant conduct statistic in either direction."
    )

    gov["measured_input_switches"]["mustrun_window_commitment_grain"] = {
        "value": True,
        "where": (
            "ScenarioConfig.mustrun_window_commitment_grain. Applied in "
            "data/fleet/arrays.py::_compose_min_gen_floors via two pure "
            "helpers, _commitment_day_order and _mustrun_window_hours, at BOTH "
            "per-plant must-run window sites (the committed-tranche block and "
            "the st_gas_mustrun_p25_level block) so the mechanism id's window "
            "stays single-valued. The window becomes round(k/24) whole "
            "operating days ranked by that day's MEAN system load; every hour "
            "of a selected day carries the floor, each tranche still clipped "
            "to pmax * availability that hour so an outage relaxes it."
        ),
        "identification": "structural-construction",
        "source": (
            "NO measured artifact enters the PLACEMENT — the day ranking is "
            "the MODEL'S OWN system load shape, the identical signal the hour "
            "ranking it replaces uses. The DRIVER evidence that the grain is "
            "the operating day is SPP's own CAMPD record, read at phase 0 with "
            "zero LP from the committed frontend/data/backcast/bench/SPP: "
            "the peak-to-mean of each plant's ONLINE hour-of-day profile is "
            "1.007-1.146 on 21 of the 22 ST_GAS plants (3-year means; only "
            "Mooreland 3008 at 1.609 genuinely two-shifts), and the "
            "night(h0-5)/afternoon(h12-17) share of online hours is 0.78-1.09 "
            "on 19 of 22. Rule 25 [R-ISO-SCOPE]: SPP's own data only."
        ),
        "warrant": (
            "Rule 17 [R-FLOOR-WINDOW] triple. DRIVER: SPP's gas-steam fleet is "
            "100.0 % EIA-860 Sector 1 'Electric Utility' (9,515 of 9,515 MW; "
            "keeper 8's census, inherited) and a vertically-integrated utility "
            "commits DAY-AHEAD FOR THE OPERATING DAY, not hour by hour. The "
            "meter agrees twice over: the flat online diurnal profile above, "
            "and 647 / 746 / 778 measured runs per year across the fleet — "
            "multi-day blocks, not daily cycles. WINDOW: round(k/24) whole "
            "operating days by day-mean system load — the mechanical lift of "
            "the incumbent's own hourly ranking to the commitment period, same "
            "signal, same ordering statistic, one grain coarser. FORWARD "
            "STORY: the ranking is the model's own load shape, so a forecast "
            "year regenerates it from forward drivers and it responds to "
            "changed conditions. THE PHYSICS (rule 18 [R-PHYSICS]): the "
            "incumbent hour grain implies 2,843 / 2,740 / 2,335 STARTS per "
            "year against the meter's 647 / 746 / 778 — 3.65x fleet-wide, and "
            "202 starts on 989 MW Muskogee in 2024 against 27 measured, 307 on "
            "Plant X against 45, 179 on 883 MW Wilkes against 11. A gas-steam "
            "unit cannot start 200 times in a year. The day grain implies 892 "
            "against 2,171 over the span — FEWER than measured, i.e. a "
            "conservative commitment scaffold."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED]: NOTHING MEASURED ENTERS THE PLACEMENT, so "
            "the field is deliberately NOT in _BACKCAST_ONLY_OVERLAY_FIELDS — "
            "unlike mustrun_online_frac_per_year (miso-172), which corrects "
            "the window's SIZE from the solve year's own meter and is "
            "registered backcast-only for exactly that reason. This lane "
            "REFUSES that field: trading a rule-13-admissible pooled input for "
            "one with no forward analogue, in order to move a diagnostic, is "
            "the wrong direction. No output is pinned to an actual — dispatch "
            "above the floor stays free, and the floor's level and size are "
            "untouched."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH], enumerated. The floor has four orthogonal "
            "properties: MEMBERSHIP (mustrun_plant_exclusions, off), window "
            "SIZE (mustrun_online_frac_per_year, off), LEVEL "
            "(st_gas_mustrun_p25_level / _measured_level / _oom_level, all "
            "off) and hour-eligibility (mustrun_layup_window_mask, off). This "
            "arm moves window PLACEMENT alone and none of the other four is "
            "armed on SPP's keeper. The window is REPLACED, never stacked. "
            "Machine-verified at zero LP on the keeper's own 2023 recipe: "
            "mechanism 16 floored 3.870051 -> 4.070490 TWh with diurnal "
            "peak-to-mean 1.235 -> 1.000, nuclear (16.926975 TWh) and "
            "chp_steam (1.245162 TWh) BYTE-IDENTICAL, and max |delta min_gen| "
            "over every cell neither run tags ST_GAS-mustrun = 0.000000. The "
            "COAL synchronization floor (coal_sync_online_frac, armed on SPP "
            "via coal_mustrun_per_plant) and the CT_PEAKER floors deliberately "
            "KEEP the hour grain — separate mechanism ids whose own conduct "
            "evidence this lane does not carry."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: the gate is armed for SPP alone via --set. "
            "The shared dataclass default stays False and the field is "
            "registered in _CACHE_KEY_OPTIONAL_FIELDS at that declared "
            "default, so every pre-existing cache key of all seven ISOs is "
            "byte-stable and no other ISO moves. No iso_configs default "
            "override is added. The chartering measurement is SPP's own ST_GAS "
            "census; the matrix cell is O in SPP's shard and U everywhere else."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: one registered ScenarioConfig field. No "
            "env-var knob, no per-plant dict in a data/ module, no getattr "
            "fallback literal in the offer path, and no new artifact."
        ),
        "limits_declared_at_the_gate": (
            "STATED BEFORE THE SOLVE AND NOT ABSORBED: this arm does NOT close "
            "card R-be. On the D-4 rider's own conduct statistic the fleet "
            "mean moves 0.8168 -> 0.8238 over 65 plant-years (25 rows better, "
            "26 worse) and the count of plant-years below 0.50 goes 10 -> 11, "
            "because Mooreland 3008 is the one measured two-shifter in the "
            "fleet and a uniform whole-day window is wrong for it. It is NOT "
            "special-cased: a per-plant grain predicate needs a threshold, "
            "which is a free parameter (rule 21), and choosing it against this "
            "statistic is the fitted-mechanism selection rule 1 [R-STRUCT] (c) "
            "forbids; a plant-level exclusion is refused on miso-170's own "
            "warning that it 'would bury that error inside a membership list'. "
            "The rest of the R-be residual is DAY SELECTION — for plants 1230 "
            "/ 1235 / 1271 the day-selection lift over chance is only ~2x and "
            "no forecast-admissible signal reaches it — plus a SIZE component "
            "that is NOT a defect (pooled online_frac is the rule-13-admissible "
            "construction and necessarily mis-sizes an individual year). The "
            "arm also raises floored energy +3.2 to +5.2 %, so rule 20 "
            "[R-FORCED-BUDGET]'s ST_GAS share rises from the keeper's 0.1962 / "
            "0.1849 / 0.1744 against a 0.30 cap. Two variants measured at "
            "phase 0 and DELIBERATELY NOT TAKEN, declared so the choice is not "
            "hidden: a day-PEAK key and a NET-load (load - wind - solar) "
            "signal score marginally better on the same conduct statistic "
            "(net+peak 0.8368), and each was refused because it bundles a "
            "second, independently-unmotivated change into the same arm — and "
            "net-vs-gross is a WASH at the hour grain (0.8168 vs 0.8168). "
            "Nothing was swept against any gate. The warrant for the arm is "
            "rule 1 [R-STRUCT]'s first half and only that."
        ),
    }

    return att


def main() -> None:
    """Write the attestation into the SPP-27 span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        default=str(DEFAULT_BUNDLE),
        help="bundle directory to write calibration_attestation.json into",
    )
    args = ap.parse_args()
    att = build()
    out = Path(args.bundle) / "calibration_attestation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att["free_parameters"]
    print(f"wrote {out}")
    print(f"  DOF ledger: n_entries={fp['n_entries']} n_residual={fp['n_residual']}")
    print(f"  entries: {[e['name'] for e in fp['entries']]}")


if __name__ == "__main__":
    main()
