"""Emit the SPP-38 calibration attestation for ``results/calibration/spp38_span``.

SPP-38 is SPP keeper 10's recipe (``results/calibration/spp36_span``,
``2026-09-12-spp-36-shortwindow-span``) replayed with **no ``--set`` at all** on
a repaired code base. It is the simplest member of this generator family: the
``ScenarioConfig`` is not changed by this lane in any way, so the DOF ledger is
inherited **verbatim** — ``n_entries`` 5, ``n_residual`` 3, the same five entries
— and the authorized price-tuning channel is replayed byte-identically (the
whole-mapping ``json.dumps(sort_keys=True)`` SHA-256 of ``offer_curve_by_group``
is ``090abd79...`` in both bundles, machine-checked by the shard before it
solved and again by the parent after it landed).

What changed is **the code**, not the recipe: twelve ``lru_cache``d loaders read
the process-global active EIA-860 directory while omitting it from their cache
key, so under ``eia860_vintage_tracks_solve_year`` year 1 of a span pinned its
vintage's value for every later year. Two are direct LP inputs on SPP's keeper
path — ``outages._iso_plant_capacity`` (the denominator of BOTH outage overlays)
and ``campd_bins.cc_duct_peaking_pct`` (the CC peak offer band). Measured at zero
LP in ``docs/handoffs/FINDING-spp-37-order-sensitivity-2026-09-12.md``; repaired
by keying each cache on the active directory (rule 14 ``[R-ACCURATE]``).

**ZERO free parameters are added and none is re-cut.** A cache key is not a
tuning channel: there is no threshold, share, multiplier, adder, offset, haircut
or proxy in the repair, no new ``ScenarioConfig`` field, no gate and no declared
default flip (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``). Nothing was swept
against any gate, and no criterion was consulted in deciding to land it.

This is NOT the ``replay_keeper --out-dir`` attestation gap being papered over:
that driver does not propagate ``calibration_attestation.json`` into an
``--out-dir`` bundle, so without this script the span scores C6 UNATTESTED for a
plumbing reason rather than a governance one — the same gap SPP-27, SPP-63 and
SPP-64 each closed with their own generator.

Usage:
    python scripts/gen_spp38_attestation.py [--bundle results/calibration/spp38_span]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp36_span/calibration_attestation.json"
DEFAULT_BUNDLE = REPO / "results/calibration/spp38_span"


def build() -> dict:
    """Return the SPP-38 attestation: keeper 10's ledger, verbatim, plus the repair."""
    att = json.loads(KEEPER.read_text())

    fp = att["free_parameters"]
    # Rule 21 [R-DOF]: `free_parameters` is left in the CANONICAL shape
    # scripts/build_dof_ledger.py emits, so `--check` stays clean; the
    # inheritance narrative goes in `governance` below, where it does not
    # perturb the checker. Verified at this HEAD: rebuilding the ledger from
    # this bundle's OWN config gives the same 5 entries / 3 residual with the
    # same names, i.e. the like-for-like baseline rule 21 asks for.
    inheritance_basis = (
        "SPP-38 replays keeper 10's recipe with NO --set at all: the "
        "ScenarioConfig is not changed by this lane, so every keeper-10 entry "
        "carries over unchanged and NOTHING IS ADDED. The change is a CACHE-KEY "
        "REPAIR in the loader layer, which is not a tuning channel — no "
        "threshold, share, multiplier, adder, offset, haircut or proxy, no new "
        "ScenarioConfig field, no gate, no declared default flip. The "
        "authorized price-tuning channel declared below is replayed BYTE-"
        "IDENTICALLY (offer_curve_by_group whole-mapping SHA-256 "
        "090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65 in "
        "both bundles) and is NOT re-cut by this lane. The rule-23-frozen "
        "thermal_tranches_SPP.csv and campd-unit-outages-short-SPP.csv are "
        "neither regenerated nor touched. n_entries stays 5 and n_residual "
        "stays 3."
    )
    # Recomputed from the inherited entries, never retyped.
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    gov = att["governance"]
    gov["dof_inherited_from"] = "spp36_span (SPP keeper 10)"
    gov["dof_inheritance_basis"] = inheritance_basis
    gov["attested_by"] = (
        "SPP-38 (2026-09-13): SPP keeper 10's recipe "
        "(2026-09-12-spp-36-shortwindow-span) replayed VERBATIM — no --set, no "
        "config delta introduced by this lane — on a repaired code base. ONE "
        "--years 2023 2024 2025 invocation in ONE shard, years sequential "
        "inside it (rules 12 / 16 [R-ALLYEARS] / 32(b) [R-SHARD]). The shard "
        "machine-checked the config signature before solving and the parent "
        "re-checked it after: eia860_vintage_tracks_solve_year True, "
        "unit_outage_short_windows True, unit_outage_short_windows_gas False, "
        "cc_duct_peaking True, and the offer_curve_by_group SHA-256 identical "
        "to the keeper's. The ONLY two differing scenario_config keys against "
        "keeper 10 are miso_import_sil_measured_envelope and "
        "gas_offer_margin_zonal_anchor_vintage — two fields that did not exist "
        "when keeper 10 solved, both bool default False, both declared in "
        "_CACHE_KEY_OPTIONAL_FIELDS at that default, both classified INERT by "
        "the G-DRIFT audit recorded in the PRECOMMIT BEFORE the arm was "
        "solved. Rule 21 [R-DOF]: ledger inherited from keeper 10 with ZERO "
        "additions — n_entries 5, n_residual 3, both unchanged. Rule 29(b): "
        "the control is keeper 10's COMMITTED bundle differenced, form 4; NO "
        "control solve was spent, and form 4's validity was established by a "
        "code-level G-DRIFT audit plus a live re-score of keeper 10's own "
        "committed artifacts at the arm's base, which reproduced its committed "
        "determination exactly (CALIBRATED, rubric v3.7, grade 7 of 8, 0 "
        "FAILS, 1 ledgered C3c caveat, 0 protective, free-class 16/16 all / "
        "12/12 free). NO SCREEN GATE AND NO RESIDUAL GATE EXISTS FOR THIS ARM, "
        "deliberately: rule 29 [R-SCREEN]'s screen applies to a candidate "
        "MECHANISM, and a known-wrong LP input is not a candidate mechanism "
        "competing against a correct one. The repair is landed on rule 14 "
        "[R-ACCURATE] and the band movement is REPORTED AT FULL MAGNITUDE, "
        "never gated on (rule 1 [R-STRUCT])."
    )

    gov["measured_input_switches"]["eia860_vintage_cache_keying"] = {
        "value": True,
        "where": (
            "NOT a ScenarioConfig field — a construction repair in the loader "
            "layer, recorded here because it changes an LP input. Twelve "
            "lru_cache'd loaders in data/outages.py, data/fleet/campd_bins.py "
            "and data/fleet/eia860.py each keep their public name as an "
            "UNCACHED thin shim over a cached core taking the active EIA-860 "
            "directory as its first key argument — the pattern the repo "
            "already used four times (cod_ramp._load_cod_map, "
            "chp._chp_by_plant, eia860._cc_steam_part_generators, "
            "eia860._eia860_plant_sectors). Where a core reads a sheet "
            "directly it now reads from its own argument, so a stale global "
            "cannot desync from the key."
        ),
        "identification": "structural-construction",
        "source": (
            "NO measured artifact enters the repair and no data changed: "
            "data/raw is byte-identical between keeper 10's basis_sha "
            "706aa5475a44e2bb87326a556833f326f926160b and this arm's base "
            "859c5dd52f4ac9e2be6381faf595a85ec66de217 (git diff over data/raw "
            "returns nothing). The defect and its magnitudes were measured at "
            "ZERO LP by scripts/probes/_spp37_vintage_cache_census.py and "
            "recorded in FINDING-spp-37-order-sensitivity-2026-09-12.md."
        ),
        "warrant": (
            "Rule 14 [R-ACCURATE], not the residual. Under "
            "eia860_vintage_tracks_solve_year run_year re-points the "
            "process-global _ACTIVE_EIA_860_DIR every year (vintage_2023 -> "
            "vintage_2024 -> canonical, no vintage_2025 being committed). The "
            "LP's own fleet follows correctly because load_fleet_from_csv is "
            "uncached, but the twelve cached loaders did not, so years 2+ of a "
            "span read YEAR 1's vintage while the LP fleet advanced — the "
            "numerator/denominator basis split _iso_plant_capacity's own "
            "docstring says must never happen ('this denominator has to be THE "
            "SAME capacity the derate multiplier is applied to in the LP'). "
            "The stale 2023 map MISSES 12 bins / 526.1 MW in 2024 and 26 bins "
            "/ 3,692.3 MW in 2025, whose outage events never reached the LP at "
            "all: _unit_outage_factors_from_events skips any event whose bin "
            "is absent from the map. The single largest term is physical and "
            "legible — plant 6193 is (6193,'COAL') 1,018.0 MW in the 2023 "
            "vintage and (6193,'ST_GAS') 1,018.0 MW in the true 2025 fleet, a "
            "coal-to-gas conversion between vintages — so a span run routed "
            "its 2025 outage events to ST_GAS, found no such bin, and dropped "
            "every one. ONE of the two constructions is simply wrong about "
            "which fleet existed in 2025; no gate, band or residual was "
            "consulted in deciding which."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED]: the repair changes only WHICH CACHE ENTRY "
            "is served, never what is computed from a given vintage, so it "
            "adds no measured overlay and has no forward analogue to test — "
            "the underlying inputs are unchanged and each remains whatever it "
            "already was. No output is pinned to an actual. The repair is a "
            "STRICT NO-OP wherever the active directory does not move, which "
            "is every ISO that does not arm eia860_vintage_tracks_solve_year "
            "(measured at this HEAD: SPP's is the only committed bundle config "
            "that arms it), every SPP single-year run, and year 1 of every SPP "
            "span. The 2023 leg of this very bundle is the live proof: LW "
            "price, slack, dump, hours>200 and all fifteen class TWh are "
            "byte-identical to keeper 10's 2023."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: nothing is stacked and no mechanism is "
            "added. The outage overlays, the offer curve, the must-run floors "
            "and the commitment bridges are all exactly keeper 10's; only the "
            "vintage each cached loader answers for changed. Machine-verified "
            "at zero LP: with the vintage flipped on a warm cache all twelve "
            "loaders now return each vintage's own value (census section 2b), "
            "and the span-vs-single-year delta in the LP's own 2025 "
            "availability input goes from -5,817,173 MWh (18 bins) on the >=5-"
            "day overlay and +142,296 MWh (5 bins) on the <5-day one to +0 MWh "
            "/ 0 bins on BOTH (census section 5). Independently, "
            "scripts/lib/bundle_fleet.reconstruct_bundle_fleet — recorded "
            "order-dependent for SPP by SPP-27 — is the same defect one layer "
            "over and is CLOSED by this repair: SPP 2025's fleet_arrays."
            "availability digest built alone vs built after 2023->2024 was "
            "7,580,565.41768 vs 7,625,968.40751 pre-repair (order-dependent) "
            "and is identical post-repair, each leg run in its OWN process."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: no ISO's fitted number is carried "
            "anywhere. The repair is one shared construction applied "
            "identically in every ISO, and it is inert in every ISO but SPP "
            "because only SPP arms vintage tracking — a property of the "
            "configs, re-measured at this HEAD rather than inherited, not a "
            "per-ISO carve-out. No iso_configs default override is added and "
            "no mechanism-matrix cell moves: a cache key is not a tuning "
            "channel, so rule 28 [R-MECH-MATRIX] does not reach it."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: ZERO registered fields added. The repair "
            "introduces no env-var knob, no per-plant dict in a data/ module, "
            "no getattr fallback literal in the offer path and no new "
            "artifact. Guarded by tests/unit/data/"
            "test_eia860_vintage_cache_keying.py (33 hermetic tests), which "
            "pins re-keying on a vintage switch, a strict no-op at a constant "
            "vintage (same object back, one cache entry, one hit), and "
            "structurally that each public name is uncached and each core's "
            "first parameter is named eia860_dir."
        ),
        "limits_declared_at_the_gate": (
            "STATED AND NOT ABSORBED. (1) KEEPER 10'S 2024/2025 NUMBERS ARE "
            "SUPERSEDED BY THIS RUN, and so are keeper 9's and every prior SPP "
            "span's: they were solved on the defective input. Their 2023 legs "
            "are sound. (2) THIS RUN OVERTURNS A CONCLUSION IN KEEPER 10'S OWN "
            "PROMOTION NOTE: that note dismissed three single-year fan-out "
            "shards' slack readings (1295.6995 MWh in 2024, 240.5966 in 2025) "
            "as 'a CONSTRUCTION MISMATCH IN THE PARENT'S OWN DESIGN' and "
            "declared the span-vs-span A/B 'the valid one'. The repaired span "
            "reproduces those exact numbers, and every 2025 class TWh in "
            "FINDING-spp-37 section 4c's single-year column to 4 dp. The "
            "single-year legs were right; the span carried the defect. The "
            "SPP-36 A/B itself still survives — both its legs shared the "
            "identical stale state, so the DIFFERENCE it measured is real — "
            "but the LEVEL either leg reported for 2024/2025 was not. (3) A "
            "SEPARATE CONFOUND, NOT THIS REPAIR: the eia923 shared-input hash "
            "moved (58267fd3f822 -> 7da41467dba7) while all seven other shared "
            "inputs are identical, because gov-hydro-seam-1 landed between "
            "keeper 10's basis and this arm's base and repaired "
            "plant_taxonomy.classify_plant so prime mover 'PS' returns OTHER "
            "instead of falling through to hydro. That moves the EIA-923 "
            "SCORED ACTUALS, not the LP, so any C1/C2 comparison against "
            "keeper 10 carries it; it is reported with the run rather than "
            "folded into the repair's effect. (4) NOTHING ELSE IS CLAIMED: "
            "this run fixes a wrong LP input. It does not close card R-be "
            "(D-4 still fails, 71 rows, identical to keeper 10), it does not "
            "touch C3c, and it buys no structural mechanism."
        ),
    }

    return att


def main() -> None:
    """Write the attestation into the SPP-38 span bundle."""
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
