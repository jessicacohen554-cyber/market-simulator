"""Emit the NWPP-40 calibration attestation for ``results/calibration/nwpp40_span_A``.

NWPP-40 is the **first NWPP solve that has ever existed** — the pool of seventeen
balancing authorities registered by NWPP-20, solved on the calibration CLI's
ISO-agnostic backcast construction with exactly two things the per-ISO
registries do not already carry: ``--hydro-backfill-year 2024`` (the NWPP-32
posture for the 263 conventional-hydro plants absent from the 2025 EIA-923 early
release) and ``--hydro-cascade-coupling`` (owner rulings N3 / N12: the Columbia
mainstem hydraulic coupling NWPP-36 built and measured, ARMED for the first
keeper). Every offer band is 1.0, no floor / bridge / adder / seam ladder /
scarcity overlay is armed, and there is no NWPP price series
(``docs/handoffs/FINDING-nwpp-13-2026-09-13.md`` read NO), so the run scores on
the rubric-v3.8 ``PHYSICALLY-CALIBRATED … (PRICE UNSCORED)`` class.

**Rule 21 [R-DOF].** ``free_parameters`` is seeded by ``scripts/build_dof_ledger.py``
in its CANONICAL shape (so ``--check`` reads clean and ``audit_keepers`` E8 can
grade it) and is NOT hand-edited here; everything this lane has to say about the
ledger goes into ``governance`` / ``disclosures``. The ledger is short, and that
is the claim: **zero values chosen on an NWPP residual**, because no NWPP residual
existed when the recipe was fixed (``PRECOMMIT-nwpp-40-2026-09-16.md`` §5).

**Gate G5 / rule 1 [R-STRUCT] carve-out.** ``authorized_price_tuning`` is **NONE**:
the four governance assertions read ``true``, there is deliberately NO
``authorized_price_tuning`` block (a block names a channel in use; there is
none), and the explicit ``authorized_price_tuning_declared`` line carries the
declaration so C6 reads a declaration rather than an absence (the SOCO-40 §8 /
SPP-40 form). The generator MACHINE-CHECKS the recipe against that claim before
writing anything: every ``committed / econ_low / econ_high / peak`` band on the
classes NWPP dispatches must be exactly 1.0, ``hydro_cascade_coupling`` must be
``true`` and ``iso`` must be ``NWPP`` — a bundle that reads otherwise is refused.

Usage:
    python scripts/gen_nwpp40_attestation.py [--bundle results/calibration/nwpp40_span_A]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwpp40_span_A"

#: Classes NWPP dispatches through ``offer_curve_by_group`` (gate G5 check set).
_UNIT_BAND_CLASSES = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "COAL",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "COAL_WC",
)
_BANDS = ("committed", "econ_low", "econ_high", "peak")


def _check_recipe(bundle: Path) -> dict:
    """Refuse a bundle whose recipe contradicts the NONE declaration."""
    rc = json.loads((bundle / "run_config.json").read_text())
    sc = rc.get("scenario_config", {})
    meta = json.loads((bundle / "meta.json").read_text())
    problems: list[str] = []
    if sc.get("iso") != "NWPP" or meta.get("iso") != "NWPP":
        problems.append(f"iso is {sc.get('iso')!r} / {meta.get('iso')!r}, not NWPP")
    if sc.get("mode") != "backcast":
        problems.append(f"mode is {sc.get('mode')!r}, not backcast")
    if sc.get("hydro_cascade_coupling") is not True:
        problems.append("hydro_cascade_coupling is not true")
    if meta.get("hydro_backfill_year") != 2024:
        problems.append(f"hydro_backfill_year is {meta.get('hydro_backfill_year')!r}")
    if meta.get("hydro_eia930_monthly"):
        problems.append("hydro_eia930_monthly is armed (REFUSED, card R-f)")
    groups = sc.get("offer_curve_by_group") or {}
    for cls in _UNIT_BAND_CLASSES:
        bands = groups.get(cls)
        if bands is None:
            continue  # a class absent from the mapping carries no band at all
        for b in _BANDS:
            if float(bands.get(b, 1.0)) != 1.0:
                problems.append(f"offer band {cls}.{b} = {bands.get(b)} != 1.0")
        for k in bands:
            if str(k).startswith("phys_"):
                problems.append(f"phys_* field present on {cls}: {k}")
    if problems:
        raise SystemExit(
            "gen_nwpp40_attestation refuses this bundle:\n  " + "\n  ".join(problems)
        )
    return {"scenario_config": sc, "meta": meta}


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-40 attestation (after seeding the canonical DOF ledger)."""
    rec = _check_recipe(bundle)
    sc, meta = rec["scenario_config"], rec["meta"]
    # Seed / refresh free_parameters in the canonical shape FIRST, then layer the
    # governance block on top of whatever the tool wrote.
    update_attestation(bundle, "NWPP")
    att = json.loads((bundle / "calibration_attestation.json").read_text())
    att["schema"] = "calibration-attestation/v1"

    solved_years = sorted(
        int(f.name.split("_")[0])
        for f in (bundle / "dispatch").glob("*_P1.parquet")
        if f.name.split("_")[0].isdigit()
    )
    if not solved_years:
        raise RuntimeError(f"no dispatch/<year>_P1.parquet under {bundle}")

    fp = att["free_parameters"]
    residual_names = [
        e["name"] for e in fp["entries"] if e.get("identification") == "residual"
    ]

    gov: dict = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        # Gate G5: NONE, declared as a statement rather than an absence. There is
        # deliberately no `authorized_price_tuning` block.
        "authorized_price_tuning_declared": (
            "NONE — no rule-1 [R-STRUCT] / rule-13 [R-MEASURED] authorized price-tuning "
            "channel is in use. Every committed / econ_low / econ_high / peak band on "
            "every class NWPP dispatches is exactly 1.0 (machine-checked by "
            "scripts/gen_nwpp40_attestation.py against this bundle's run_config.json "
            "before this file was written); the delta JSON is {}; no phys_* field "
            "exists; no --offer-curve-json, --set, adder, offset, haircut or proxy was "
            "passed. Most of this footprint is cost-based vertically-integrated dispatch "
            "and NO NWPP price residual exists to tune on (FINDING-nwpp-13 read NO), so "
            "the channel could not have been used even in principle. A band != 1.0 would "
            "also break rule 25 [R-ISO-SCOPE]."
        ),
        "attested_by": (
            "NWPP-40 (2026-09-16): the FIRST NWPP solve. ONE shard, ONE "
            "--year 2023 2024 2025 invocation, years sequential inside it (rules 12 / 16 "
            "[R-ALLYEARS] / 32(b) [R-SHARD]); owner ruling N10-R: no screen. The recipe is "
            "the calibration CLI's ISO-agnostic backcast construction on the NWPP "
            "registries landed by NWPP-20 (five whole-BA zones on WECC-catalogue TTC "
            "tiers, card N5; served measured EIA-930 interchange with priced seams "
            "default-off, card N4; one PRM scalar 0.144, card N7; legacy heat-rate bins, "
            "card N8) plus exactly two solve inputs: --hydro-backfill-year 2024 "
            "(NWPP-32's posture; the 2025 eia930_monthly repin REFUSED on rule-14 "
            "grounds, card R-f) and --hydro-cascade-coupling (owner rulings N3 / N12). "
            "The recipe, the phase-0 census, the DOF ledger and every declaration below "
            "were fixed in docs/handoffs/PRECOMMIT-nwpp-40-2026-09-16.md, pushed at "
            "c8819f51de3d8a8d5e754f016d7f3620e59e5185 BEFORE the shard was launched; "
            "the shard machine-checked the config signature before pushing and the "
            "parent re-checked it after. Rule 21 [R-DOF]: the ledger is seeded by "
            "build_dof_ledger.py and is SHORT — the entries tagged residual are "
            f"{residual_names} — every one an inherited generic default (the "
            "offer_curve_by_group container at the identity, the smoothing shape with "
            "zero span, wefor_multiplier at the CLI's non-MISO 0.7), none chosen on an "
            "NWPP residual because none existed. Nothing was swept against any gate."
        ),
        "measured_input_switches": {
            "hydro_cascade_coupling": {
                "value": True,
                "where": "ScenarioConfig.hydro_cascade_coupling via --hydro-cascade-coupling (prb_overrides channel)",
                "identification": "measured-physical",
                "source": (
                    "data/raw/nwpp-hydro/nwpp_hydro_cascade_{links,monthly}.csv, derived by "
                    "scripts/data/build_nwpp_hydro_cascade.py from the CROHMS hourly project "
                    "feed (2,103,124 values, every one quality code 0), NID and EIA-923 "
                    "(PRECOMMIT-nwpp-36 §4; FINDING-nwpp-36 §3). Every tau, pondage band, "
                    "eta and side inflow is MEASURED; a link that failed its pre-registered "
                    "measurement gate is left UNCOUPLED on its monthly budget, never given a "
                    "substituted value (rule 13)."
                ),
                "reach": (
                    "5 coupled downstream plants / 5 links in every solved year — Chief Joseph "
                    "3921, Wells 3886, Rock Island 6200, Bonneville 3075, Ice Harbor 3925 = "
                    "5,717 MW = 16.0 % of NWPP conventional-hydro nameplate (NOT the 14 plants / "
                    "65.9 % the mechanism's docstring describes: 3 links uncoupled on tau, 7 on "
                    "the 2 % side-inflow floor). tau by link 0 / 1 / 1 / 0 / 0 h."
                ),
                "warrant": (
                    "Owner ruling N3 (2026-09-13, against the desk's recommendation): build "
                    "the coupling BEFORE the first keeper. Owner ruling N12 (2026-09-16): "
                    "NWPP-36's pre-registered armed-response gate G-A3 FAILED (within-day "
                    "amplitude at coupled run-of-river plants falls 1-10 % — Chief Joseph "
                    "2.34 -> 2.13, Ice Harbor 4.28 -> 3.83 — not the >= 30 % the gate "
                    "expected, because a coupled plant INHERITS its upstream's hourly shape) "
                    "and was ACCEPTED as a mis-specified gate, not a passing one; W4 proceeds "
                    "with the miss carried at full magnitude on this determination basis."
                ),
                "one_mech": (
                    "Rule 19 [R-ONE-MECH]: the coupling redistributes WHEN a coupled plant's "
                    "monthly water is turbined and never how much — G-A1 measured a 0.000 % "
                    "move in monthly energy; the EIA-923 monthly budget stays the sole quantity "
                    "mechanism and no generation column is added."
                ),
                "forward_test": (
                    "Rule 13: tau, the band and the chain are physical properties of the river "
                    "and its dams; eta and the monthly means regenerate from the CROHMS feed for "
                    "any year and respond to changed water."
                ),
            },
            "hydro_backfill_year_2024": {
                "value": 2024,
                "where": "run_calibration_full --hydro-backfill-year (meta.json hydro_backfill_year)",
                "identification": "measured-physical",
                "source": (
                    "FINDING-nwpp-32 §2-§3: 2025 EIA-923 is an early release with 25 of 288 "
                    "conventional-hydro plants reporting; the 263 NO_923_SERIES plants carry "
                    "their 2024 monthly water, giving a 2025 budget of 113.156 TWh over 280 "
                    "plants (66.2 % measured 2025 energy — every >= 1 GW plant among the "
                    "reporters — and 33.8 % carried 2024 water). The eia930_monthly repin was "
                    "REFUSED (card R-f): the -2.5 % 930-vs-923 gap is a BA population "
                    "mismatch (Priest Rapids 860->BPAT / 930->GCPD; WAUW -2.6/-2.8 TWh), so a "
                    "repin would rescale a measured input to a different boundary (rule 14)."
                ),
                "limit": (
                    "Reported, not absorbed: 2025 hydro is one third carried water; the "
                    "benchmark's own 2025 hydro is the EIA-930 value 110.2719 TWh (923/930 = "
                    "0.6796 < 0.80), so the 2025 hydro C1 row compares a backfilled budget "
                    "against a pool total. Named at the gate as part of the 2025 data posture."
                ),
            },
            "served_measured_interchange": {
                "value": True,
                "where": "envelopes.nwpp_net_interchange via _SCALAR_INTERCHANGE_ISOS['NWPP'] (NWPP-20 / NWPP-34)",
                "identification": "measured-physical",
                "source": (
                    "Sigma over the 17 members of (Net generation - Demand)(Adjusted) minus "
                    "GRID's Desert-Southwest legs, export-positive: -13.745 / -12.891 / -4.785 "
                    "TWh in 2023 / 2024 / 2025 (NWPP-34 §3). The naive Sigma Total-interchange "
                    "derive would have read a net EXPORTER (+28.8 / +32.6 / +18.3 TWh) because "
                    "BPAT's balance identity fails structurally (mean residual -3,206 MW, 81.5 % "
                    "of hours) until a one-hour reporting step at UTC 2025-06-01 07:00."
                ),
                "limit": (
                    "A footprint-wide scalar spread across the five zones by load share, so "
                    "CAISO-facing flow lands on NWPP-EAST / NWPP-INLAND, which have no "
                    "California leg; and it is exogenous and price-inelastic. Priced "
                    "NeighborInterfaces are registered and default-OFF (card N4; lever NWPP-56)."
                ),
            },
            "voll_interim_2000": {
                "value": 2000.0,
                "where": "config/iso_configs._nwpp_config voll",
                "identification": "published",
                "source": (
                    "The WEIM hard offer cap (CAISO Tariff §39.6.1, the FERC Order 831 $2,000/MWh "
                    "cap) — eleven of the seventeen balancing areas bid into WEIM, which clears "
                    "5.5-6.2 % of footprint energy net (NWPP-13). DECLARED INTERIM (NWPP-10 §7.1; "
                    "iso_configs comment): the cap of an imbalance market that clears ~6 % of "
                    "energy is NOT a customer damage function. No participant IRP states a $/MWh "
                    "loss-of-load cost; the LBNL-ICE derivation on the footprint's own customer "
                    "mix is the routed successor (FINDING-nwpp-20 §5). Never swept against a gate."
                ),
            },
        },
    }
    att["governance"] = gov

    att["disclosures"] = {
        "note": (
            "NWPP-40 disclosures — the determination basis, reported at full magnitude and "
            "absorbed nowhere (PRECOMMIT-nwpp-40 §8)."
        ),
        "price_unscored": (
            "There is NO admissible NWPP hourly price series. NWPP-13 built the WEIM-derived "
            "footprint index under a STOP gate pre-registered before any data was read and it "
            "read NO: the NW-group WEIM on-peak price sits -37.5 / -22.6 / -23.6 % (2023 "
            "Jun-Dec / 2024 / 2025) below the independent Mid-C Peak index against a +/-10 % "
            "bar, at daily correlation 0.74 / 0.95 / 0.67 against 0.80, while clearing "
            "5.5-6.2 % of footprint energy net. Nothing landed to _validation-source; "
            "actual_lmp.json carries no NWPP block; TAIL_THRESHOLD has no NWPP key. C3a / "
            "C3b / C3c are therefore UNSCORED (never PASS) and the run reads rubric v3.8's "
            "PHYSICALLY-CALIBRATED ... (PRICE UNSCORED) class — never a bare CALIBRATED "
            "(owner ruling N2 limb b). The model's own annual mean price is printed "
            "MODEL-ONLY / UNVERIFIED. A neighbouring-hub proxy stays refused (gate G17)."
        ),
        "g_a3_miss": (
            "NWPP-36's armed-response gate G-A3 FAILED and rides this basis (owner ruling "
            "N12): within-day amplitude at coupled run-of-river plants falls 1-10 % (Chief "
            "Joseph 2.339 -> 2.131, Wells 2.153 -> 2.088, Rock Island 2.489 -> 2.394, "
            "Bonneville 2.045 -> 2.027, Ice Harbor 4.275 -> 3.825; January 2023), not the "
            ">= 30 % the gate expected; Rock Island's armed peak (606 MW) exceeds the "
            "flat-arrivals bound (552 MW) because its UNCOUPLED upstream Rocky Reach peaks "
            "into it; the pond is never drawn. Grand Coulee's own January amplitude falls "
            "3.71 -> 2.15 instead. A mis-specified gate, not a passing one."
        ),
        "coupled_set_is_16pct": (
            "The coupling reaches 5 of 15 measured links — 5,717 MW, 16.0 % of conventional-"
            "hydro nameplate — not the 14 plants / 65.9 % the PRECOMMIT asked for: 3 links "
            "uncoupled on tau (Wells->Rocky Reach celerity 34.9 mph; Rock Island->Wanapum "
            "diurnal alias; Dworshak->Lower Granite r = 0.02) and 7 on the 2 % side-inflow "
            "floor, a spill-metering artefact at the federal lower-river projects (FINDING-"
            "nwpp-36 §3.4 / §7 item 1). Grand Coulee, McNary, John Day, The Dalles and the "
            "lower Snake above Ice Harbor dispatch on their monthly budgets."
        ),
        "pnca_terminated_inside_window": (
            "The 1997 Pacific Northwest Coordination Agreement — the instrument that defines "
            "'Period means a calendar month', the model's own budget period — terminated "
            "2024-09-15 with no successor text found (card R-j). Declared regardless of the "
            "measurement; NWPP-38's result reported alongside: verdict (a), no measurable "
            "change — 0 of 56 treated cells (BPAT CHPD DOPD GCPD) reach the |z| >= 4.07 "
            "detection threshold in 2024 or 2025 (max 2.45 / 3.04) while the control group "
            "(PGE TPWR PACW) moved MORE (1 / 8 cells past threshold; PGE ramp z = 10.95); a "
            "2022-09-15 placebo returns a bigger effect (t = +4.76) than the real date "
            "(t = -1.17). Power: a one-fifth change in within-day shaping would have been "
            "detected; a one-tenth change would not."
        ),
        "prm_two_regime_mismatch": (
            "Card N7: one PLANNING_RESERVE_MARGIN_BY_ISO scalar 0.144 (PacifiCorp 2025 IRP "
            "summer, adopted from WRAP) tested against the summer coincident peak, while "
            "NWPP-NW peaks in WINTER every year (winter/summer 0.86 / 0.80 / 0.82), NWPP-SNV "
            "in SUMMER at 1.95 / 2.06 / 1.87x its winter load, and NWPP-INLAND mixes both "
            "regimes inside one zone (8 winter-peaking BAs, 6 summer, 1 flipping). Largely "
            "inert in a backcast (capacity evolution is forecast-mode); lever NWPP-57. WRAP's "
            "first binding season is Winter 2027-28 (WPP BPM 109 p. 4) — forecast-side only."
        ),
        "data_posture_2025": (
            "263 conventional-hydro plants absent from the 2025 EIA-923 early release carry "
            "2024 water (see hydro_backfill_year_2024); eia923_incomplete: true (BA total / "
            "EIA-930 net gen = 0.7881), so 2025 C1 rows gate only where the completeness audit "
            "reads COMPLETE and the rest route to the C2 EIA-930 family fallback; 2025 wind "
            "(923/930 = 0.5746) and hydro (0.6796) benchmarks are swapped to EIA-930. The "
            "fuel columns this solve reads carry the NWPP-37 / 37b / 39 screen state (pooled "
            "NG: WAT 2025 peak 23,607 MW; measured_monthly_hydro 2025 110.2639 TWh); the "
            "committed nwpp_hydro_budget.parquet is EIA-923-derived and never carried a 930 "
            "hour."
        ),
        "demand_convention_and_the_30_hours": (
            "LP demand reads Demand (MW) (Adjusted) per member BA; _screen_demand_dropouts "
            "applied per member (the 17 exactly-zero NEVP hours of 2025); "
            "_screen_demand_spikes NOT applied (it would delete 54 real hours of the 12-16 "
            "January 2024 CHPD cold snap holding NWPP-NW's own 2024 peak, 21,560 MW at "
            "2024-01-13 19:00 UTC). The 30 raw-feed artifacts (AVA 10, NWMT 11, NEVP 6, "
            "PACE 1, SCL 2; 558x median at AVA 2025-10-12 10:00 UTC, -58,286 MW at AVA "
            "2024-01-05 16:00) are named individually in PRECOMMIT-nwpp-40 §4.3 and are all "
            "repaired in the Adjusted column. Nothing padded, interpolated or rescaled."
        ),
        "voll_interim": "See governance.measured_input_switches.voll_interim_2000.",
        "nw_or_tier3_placeholder": (
            "NWPP-NW <-> NWPP-OR carries a 43,600 MW Tier-3 placeholder (the NW zone "
            "nameplate), non-binding by construction: no WECC path rates that boundary and "
            "none will — it is a multi-point interconnection around Portland; Paths 4 / 5 / "
            "71 / 86-88 are east-west cuts, not BA interfaces (card N5). Lever NWPP-55."
        ),
        "coal_fuel_price_gap": (
            "Colstrip (6076) and Centralia (3845) file no EIA-923 Schedule-2 fuel price in "
            "any year — 2,377.3 of 8,910.2 MW of coal (26.7 %), the whole coal fleet of "
            "NWPP-INLAND and NWPP-NW; they price on the supply-class trajectory (NWPP-12 "
            "§2.5). Reported, not filled."
        ),
        "served_interchange_limits": "See governance.measured_input_switches.served_measured_interchange.limit.",
        "solved_years": solved_years,
        "recorded_signature": {
            "hydro_cascade_coupling": sc.get("hydro_cascade_coupling"),
            "hydro_backfill_year": meta.get("hydro_backfill_year"),
            "hydro_eia930_monthly": bool(meta.get("hydro_eia930_monthly")),
            "wefor_multiplier": sc.get("wefor_multiplier"),
            "plant_level_fleet": sc.get("plant_level_fleet"),
            "use_campd_bins": sc.get("use_campd_bins"),
            "use_campd_bins_note": (
                "reads True in the config and is INERT: NWPP is absent from "
                "CAMPD_BINNING_ISOS (card N8), so the fleet takes the legacy aggregate_fleet "
                "path with plant_level_fleet=True; thermal_tranches_NWPP.csv is not read."
            ),
        },
    }
    att["exceptions"] = []
    return att


def main() -> None:
    """Write the attestation into the NWPP-40 span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        default=str(DEFAULT_BUNDLE),
        help="bundle directory to write calibration_attestation.json into",
    )
    args = ap.parse_args()
    att = build(Path(args.bundle))
    out = Path(args.bundle) / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att["free_parameters"]
    print(f"wrote {out}")
    print(f"  DOF ledger: n_entries={fp['n_entries']} n_residual={fp['n_residual']}")
    print(f"  entries: {[e['name'] for e in fp['entries']]}")


if __name__ == "__main__":
    main()
