"""Emit the NWPP-41 calibration attestation for ``results/calibration/nwpp41_span_A``.

NWPP-41 is NWPP-40's frozen recipe plus **exactly one** solve-affecting change:
``coal_prb_proxy_own_iso=True``, wired for NWPP alone at
``pipeline/backcast_config.py``. Everything else — the five whole-BA zones, the
WECC-catalogue TTC tiers, served measured EIA-930 interchange, the 0.144 PRM
scalar, legacy heat-rate bins, ``--hydro-backfill-year 2024`` and
``--hydro-cascade-coupling`` — is NWPP-40's, unchanged. The control diff over
``scenario_config`` is **two fields**: this lane's arm, and
``neiso_coldsnap_derate_dualfuel_unswitched`` at its default ``False``, which is
NEISO-gated and therefore INERT for NWPP (the rule-29(b) ``G-DRIFT``
classification).

**What the lane fixed, and why it is not tuning (rules 1 / 13 / 14).** Two
defects at one seam, both plumbing:

1. **C1, the coal taxonomy.** ``data/raw/_processed-legacy/coal_supply_NWPP.csv``
   had never been derived, so ``coal_supply_class`` returned ``""`` for all 17
   NWPP coal plants and ``run_calibration_full.py`` binned every one of them to
   the bare class ``COAL`` — a class the benchmark carries no row for, because
   the benchmark passes the EIA-923 row's own fuel code to the *same* resolver
   and itemizes ``COAL_PRB`` / ``COAL_BIT`` / ``COAL_WC``. Five C1 rows failed on
   an asymmetry in the plumbing, not on dispatch. The file is now derived
   (17 rows; 9 prb / 6 bituminous / 2 waste; 0 unresolved).
2. **Rule 25 [R-ISO-SCOPE], the PRB price proxy.** ``_prb_monthly_actuals``
   pooled ``data.coal.COAL_PLANT_SUPPLY``, **every plant of which is in Texas**,
   so an NWPP plant with no EIA-923 Schedule-2 filing of its own priced against
   ERCOT's delivered PRB cost. NWPP's own four PRB reporters pay
   $2.463 / $2.134 / $2.066 per MMBtu in 2023 / 2024 / 2025 against ERCOT's
   $1.818 / $1.760 / $1.622. The proxy now pools the target ISO's own measured
   deliveries.

**Rule 21 [R-DOF]: the arm is NOT a free parameter.** It selects *which measured
series* the proxy reads — NWPP's own EIA-923 Schedule-2 delivered PRB prices
instead of another ISO's — so its identification is **measured**, not residual.
Nothing was swept: the flag is boolean, it was set ex ante in
``PRECOMMIT-nwpp-41-2026-09-17.md`` §7 before any solve, and there is no NWPP
price residual to tune on in the first place (``FINDING-nwpp-13`` read NO).

**Gate G5 / rule 1 [R-STRUCT] carve-out: NONE**, and independently verified from
dispatch rather than asserted. Every ``committed / econ_low / econ_high / peak``
band on every class NWPP dispatches is exactly 1.0. Three groups in the shared
config do carry non-unity bands — ``CC_INTERMEDIATE``, ``CT_INTERMEDIATE``,
``ST_GAS_INTERMEDIATE`` — and all three carry **zero NWPP energy in all three
solved years**, so no band that touches this footprint was moved. This generator
MACHINE-CHECKS that, plus ``coal_prb_proxy_own_iso`` true, ``hydro_cascade_coupling``
true, ``hydro_backfill_year`` 2024, ``hydro_eia930_monthly`` off and ``iso``
NWPP, and refuses a bundle that reads otherwise.

Usage:
    python scripts/gen_nwpp41_attestation.py [--bundle results/calibration/nwpp41_span_A]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwpp41_span_A"

#: Classes NWPP dispatches through ``offer_curve_by_group`` (gate G5 check set).
#: Verified against the bundle's own ``hourly/class_hourly_<year>.parquet``: the
#: 16 classes carrying nonzero energy include none of the ``*_INTERMEDIATE``
#: groups that hold non-unity bands.
_UNIT_BAND_CLASSES = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "COAL",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "COAL_WC",
)
_BANDS = ("committed", "econ_low", "econ_high", "peak")

#: Disclosures inherited VERBATIM from the NWPP-40 attestation. Every one still
#: applies: this lane changed one coal-pricing seam and nothing else, so the
#: price-unscored posture, the G-A3 miss, the 16 %-coupled set, the 2025 data
#: posture, the PRM regime mismatch, the demand convention, the interim VOLL and
#: the Tier-3 placeholder all ride unchanged onto this determination basis.
#: Extracted mechanically from the committed NWPP-40 JSON, not retyped.
_INHERITED_DISCLOSURES = {'coal_fuel_price_gap': 'Colstrip (6076) and Centralia (3845) file no EIA-923 Schedule-2 '
                        'fuel price in any year — 2,377.3 of 8,910.2 MW of coal (26.7 %), '
                        'the whole coal fleet of NWPP-INLAND and NWPP-NW; they price on the '
                        'supply-class trajectory (NWPP-12 §2.5). Reported, not filled.',
 'coupled_set_is_16pct': 'The coupling reaches 5 of 15 measured links — 5,717 MW, 16.0 % of '
                         'conventional-hydro nameplate — not the 14 plants / 65.9 % the '
                         'PRECOMMIT asked for: 3 links uncoupled on tau (Wells->Rocky Reach '
                         'celerity 34.9 mph; Rock Island->Wanapum diurnal alias; '
                         'Dworshak->Lower Granite r = 0.02) and 7 on the 2 % side-inflow '
                         'floor, a spill-metering artefact at the federal lower-river '
                         'projects (FINDING-nwpp-36 §3.4 / §7 item 1). Grand Coulee, McNary, '
                         'John Day, The Dalles and the lower Snake above Ice Harbor dispatch '
                         'on their monthly budgets.',
 'data_posture_2025': '263 conventional-hydro plants absent from the 2025 EIA-923 early '
                      'release carry 2024 water (see hydro_backfill_year_2024); '
                      'eia923_incomplete: true (BA total / EIA-930 net gen = 0.7881), so '
                      '2025 C1 rows gate only where the completeness audit reads COMPLETE '
                      'and the rest route to the C2 EIA-930 family fallback; 2025 wind '
                      '(923/930 = 0.5746) and hydro (0.6796) benchmarks are swapped to '
                      'EIA-930. The fuel columns this solve reads carry the NWPP-37 / 37b / '
                      '39 screen state (pooled NG: WAT 2025 peak 23,607 MW; '
                      'measured_monthly_hydro 2025 110.2639 TWh); the committed '
                      'nwpp_hydro_budget.parquet is EIA-923-derived and never carried a 930 '
                      'hour.',
 'demand_convention_and_the_30_hours': 'LP demand reads Demand (MW) (Adjusted) per member '
                                       'BA; _screen_demand_dropouts applied per member (the '
                                       '17 exactly-zero NEVP hours of 2025); '
                                       '_screen_demand_spikes NOT applied (it would delete '
                                       '54 real hours of the 12-16 January 2024 CHPD cold '
                                       "snap holding NWPP-NW's own 2024 peak, 21,560 MW at "
                                       '2024-01-13 19:00 UTC). The 30 raw-feed artifacts '
                                       '(AVA 10, NWMT 11, NEVP 6, PACE 1, SCL 2; 558x median '
                                       'at AVA 2025-10-12 10:00 UTC, -58,286 MW at AVA '
                                       '2024-01-05 16:00) are named individually in '
                                       'PRECOMMIT-nwpp-40 §4.3 and are all repaired in the '
                                       'Adjusted column. Nothing padded, interpolated or '
                                       'rescaled.',
 'g_a3_miss': "NWPP-36's armed-response gate G-A3 FAILED and rides this basis (owner ruling "
              'N12): within-day amplitude at coupled run-of-river plants falls 1-10 % (Chief '
              'Joseph 2.339 -> 2.131, Wells 2.153 -> 2.088, Rock Island 2.489 -> 2.394, '
              'Bonneville 2.045 -> 2.027, Ice Harbor 4.275 -> 3.825; January 2023), not the '
              ">= 30 % the gate expected; Rock Island's armed peak (606 MW) exceeds the "
              'flat-arrivals bound (552 MW) because its UNCOUPLED upstream Rocky Reach peaks '
              "into it; the pond is never drawn. Grand Coulee's own January amplitude falls "
              '3.71 -> 2.15 instead. A mis-specified gate, not a passing one.',
 'nw_or_tier3_placeholder': 'NWPP-NW <-> NWPP-OR carries a 43,600 MW Tier-3 placeholder (the '
                            'NW zone nameplate), non-binding by construction: no WECC path '
                            'rates that boundary and none will — it is a multi-point '
                            'interconnection around Portland; Paths 4 / 5 / 71 / 86-88 are '
                            'east-west cuts, not BA interfaces (card N5). Lever NWPP-55.',
 'pnca_terminated_inside_window': 'The 1997 Pacific Northwest Coordination Agreement — the '
                                  "instrument that defines 'Period means a calendar month', "
                                  "the model's own budget period — terminated 2024-09-15 "
                                  'with no successor text found (card R-j). Declared '
                                  "regardless of the measurement; NWPP-38's result reported "
                                  'alongside: verdict (a), no measurable change — 0 of 56 '
                                  'treated cells (BPAT CHPD DOPD GCPD) reach the |z| >= 4.07 '
                                  'detection threshold in 2024 or 2025 (max 2.45 / 3.04) '
                                  'while the control group (PGE TPWR PACW) moved MORE (1 / 8 '
                                  'cells past threshold; PGE ramp z = 10.95); a 2022-09-15 '
                                  'placebo returns a bigger effect (t = +4.76) than the real '
                                  'date (t = -1.17). Power: a one-fifth change in within-day '
                                  'shaping would have been detected; a one-tenth change '
                                  'would not.',
 'price_unscored': 'There is NO admissible NWPP hourly price series. NWPP-13 built the '
                   'WEIM-derived footprint index under a STOP gate pre-registered before any '
                   'data was read and it read NO: the NW-group WEIM on-peak price sits -37.5 '
                   '/ -22.6 / -23.6 % (2023 Jun-Dec / 2024 / 2025) below the independent '
                   'Mid-C Peak index against a +/-10 % bar, at daily correlation 0.74 / 0.95 '
                   '/ 0.67 against 0.80, while clearing 5.5-6.2 % of footprint energy net. '
                   'Nothing landed to _validation-source; actual_lmp.json carries no NWPP '
                   'block; TAIL_THRESHOLD has no NWPP key. C3a / C3b / C3c are therefore '
                   "UNSCORED (never PASS) and the run reads rubric v3.8's "
                   'PHYSICALLY-CALIBRATED ... (PRICE UNSCORED) class — never a bare '
                   "CALIBRATED (owner ruling N2 limb b). The model's own annual mean price "
                   'is printed MODEL-ONLY / UNVERIFIED. A neighbouring-hub proxy stays '
                   'refused (gate G17).',
 'prm_two_regime_mismatch': 'Card N7: one PLANNING_RESERVE_MARGIN_BY_ISO scalar 0.144 '
                            '(PacifiCorp 2025 IRP summer, adopted from WRAP) tested against '
                            'the summer coincident peak, while NWPP-NW peaks in WINTER every '
                            'year (winter/summer 0.86 / 0.80 / 0.82), NWPP-SNV in SUMMER at '
                            '1.95 / 2.06 / 1.87x its winter load, and NWPP-INLAND mixes both '
                            'regimes inside one zone (8 winter-peaking BAs, 6 summer, 1 '
                            'flipping). Largely inert in a backcast (capacity evolution is '
                            "forecast-mode); lever NWPP-57. WRAP's first binding season is "
                            'Winter 2027-28 (WPP BPM 109 p. 4) — forecast-side only.',
 'served_interchange_limits': 'See '
                              'governance.measured_input_switches.served_measured_interchange.limit.',
 'voll_interim': 'See governance.measured_input_switches.voll_interim_2000.'}

#: Measured-input switches inherited from NWPP-40, unchanged by this lane.
_INHERITED_SWITCHES = {'hydro_backfill_year_2024': {'identification': 'measured-physical',
                              'limit': 'Reported, not absorbed: 2025 hydro is one third '
                                       "carried water; the benchmark's own 2025 hydro is the "
                                       'EIA-930 value 110.2719 TWh (923/930 = 0.6796 < '
                                       '0.80), so the 2025 hydro C1 row compares a '
                                       'backfilled budget against a pool total. Named at the '
                                       'gate as part of the 2025 data posture.',
                              'source': 'FINDING-nwpp-32 §2-§3: 2025 EIA-923 is an early '
                                        'release with 25 of 288 conventional-hydro plants '
                                        'reporting; the 263 NO_923_SERIES plants carry their '
                                        '2024 monthly water, giving a 2025 budget of 113.156 '
                                        'TWh over 280 plants (66.2 % measured 2025 energy — '
                                        'every >= 1 GW plant among the reporters — and 33.8 '
                                        '% carried 2024 water). The eia930_monthly repin was '
                                        'REFUSED (card R-f): the -2.5 % 930-vs-923 gap is a '
                                        'BA population mismatch (Priest Rapids 860->BPAT / '
                                        '930->GCPD; WAUW -2.6/-2.8 TWh), so a repin would '
                                        'rescale a measured input to a different boundary '
                                        '(rule 14).',
                              'value': 2024,
                              'where': 'run_calibration_full --hydro-backfill-year '
                                       '(meta.json hydro_backfill_year)'},
 'hydro_cascade_coupling': {'forward_test': 'Rule 13: tau, the band and the chain are '
                                            'physical properties of the river and its dams; '
                                            'eta and the monthly means regenerate from the '
                                            'CROHMS feed for any year and respond to changed '
                                            'water.',
                            'identification': 'measured-physical',
                            'one_mech': 'Rule 19 [R-ONE-MECH]: the coupling redistributes '
                                        "WHEN a coupled plant's monthly water is turbined "
                                        'and never how much — G-A1 measured a 0.000 % move '
                                        'in monthly energy; the EIA-923 monthly budget stays '
                                        'the sole quantity mechanism and no generation '
                                        'column is added.',
                            'reach': '5 coupled downstream plants / 5 links in every solved '
                                     'year — Chief Joseph 3921, Wells 3886, Rock Island '
                                     '6200, Bonneville 3075, Ice Harbor 3925 = 5,717 MW = '
                                     '16.0 % of NWPP conventional-hydro nameplate (NOT the '
                                     "14 plants / 65.9 % the mechanism's docstring "
                                     'describes: 3 links uncoupled on tau, 7 on the 2 % '
                                     'side-inflow floor). tau by link 0 / 1 / 1 / 0 / 0 h.',
                            'source': 'data/raw/nwpp-hydro/nwpp_hydro_cascade_{links,monthly}.csv, '
                                      'derived by scripts/data/build_nwpp_hydro_cascade.py '
                                      'from the CROHMS hourly project feed (2,103,124 '
                                      'values, every one quality code 0), NID and EIA-923 '
                                      '(PRECOMMIT-nwpp-36 §4; FINDING-nwpp-36 §3). Every '
                                      'tau, pondage band, eta and side inflow is MEASURED; a '
                                      'link that failed its pre-registered measurement gate '
                                      'is left UNCOUPLED on its monthly budget, never given '
                                      'a substituted value (rule 13).',
                            'value': True,
                            'warrant': "Owner ruling N3 (2026-09-13, against the desk's "
                                       'recommendation): build the coupling BEFORE the first '
                                       "keeper. Owner ruling N12 (2026-09-16): NWPP-36's "
                                       'pre-registered armed-response gate G-A3 FAILED '
                                       '(within-day amplitude at coupled run-of-river plants '
                                       'falls 1-10 % — Chief Joseph 2.34 -> 2.13, Ice Harbor '
                                       '4.28 -> 3.83 — not the >= 30 % the gate expected, '
                                       "because a coupled plant INHERITS its upstream's "
                                       'hourly shape) and was ACCEPTED as a mis-specified '
                                       'gate, not a passing one; W4 proceeds with the miss '
                                       'carried at full magnitude on this determination '
                                       'basis.',
                            'where': 'ScenarioConfig.hydro_cascade_coupling via '
                                     '--hydro-cascade-coupling (prb_overrides channel)'},
 'served_measured_interchange': {'identification': 'measured-physical',
                                 'limit': 'A footprint-wide scalar spread across the five '
                                          'zones by load share, so CAISO-facing flow lands '
                                          'on NWPP-EAST / NWPP-INLAND, which have no '
                                          'California leg; and it is exogenous and '
                                          'price-inelastic. Priced NeighborInterfaces are '
                                          'registered and default-OFF (card N4; lever '
                                          'NWPP-56).',
                                 'source': 'Sigma over the 17 members of (Net generation - '
                                           "Demand)(Adjusted) minus GRID's Desert-Southwest "
                                           'legs, export-positive: -13.745 / -12.891 / '
                                           '-4.785 TWh in 2023 / 2024 / 2025 (NWPP-34 §3). '
                                           'The naive Sigma Total-interchange derive would '
                                           'have read a net EXPORTER (+28.8 / +32.6 / +18.3 '
                                           "TWh) because BPAT's balance identity fails "
                                           'structurally (mean residual -3,206 MW, 81.5 % of '
                                           'hours) until a one-hour reporting step at UTC '
                                           '2025-06-01 07:00.',
                                 'value': True,
                                 'where': 'envelopes.nwpp_net_interchange via '
                                          "_SCALAR_INTERCHANGE_ISOS['NWPP'] (NWPP-20 / "
                                          'NWPP-34)'},
 'voll_interim_2000': {'identification': 'published',
                       'source': 'The WEIM hard offer cap (CAISO Tariff §39.6.1, the FERC '
                                 'Order 831 $2,000/MWh cap) — eleven of the seventeen '
                                 'balancing areas bid into WEIM, which clears 5.5-6.2 % of '
                                 'footprint energy net (NWPP-13). DECLARED INTERIM (NWPP-10 '
                                 '§7.1; iso_configs comment): the cap of an imbalance market '
                                 'that clears ~6 % of energy is NOT a customer damage '
                                 'function. No participant IRP states a $/MWh loss-of-load '
                                 "cost; the LBNL-ICE derivation on the footprint's own "
                                 'customer mix is the routed successor (FINDING-nwpp-20 §5). '
                                 'Never swept against a gate.',
                       'value': 2000.0,
                       'where': 'config/iso_configs._nwpp_config voll'}}


def _check_recipe(bundle: Path) -> dict:
    """Refuse a bundle whose recipe contradicts this attestation's claims."""
    rc = json.loads((bundle / "run_config.json").read_text())
    sc = rc.get("scenario_config", {})
    meta = json.loads((bundle / "meta.json").read_text())
    problems: list[str] = []
    if sc.get("iso") != "NWPP" and meta.get("iso") != "NWPP":
        problems.append(f"iso is {sc.get('iso')!r} / {meta.get('iso')!r}, not NWPP")
    if sc.get("mode") != "backcast":
        problems.append(f"mode is {sc.get('mode')!r}, not backcast")
    # The lane's one arm.
    if sc.get("coal_prb_proxy_own_iso") is not True:
        problems.append("coal_prb_proxy_own_iso is not true — this is NOT the NWPP-41 arm")
    # NWPP-40's recipe, which this run inherits unchanged.
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
            "gen_nwpp41_attestation refuses this bundle:\n  " + "\n  ".join(problems)
        )
    return {"scenario_config": sc, "meta": meta}


def _dispatched_classes(bundle: Path) -> set[str]:
    """Classes carrying nonzero energy in any solved year (gate G5 evidence)."""
    import pandas as pd

    seen: set[str] = set()
    for path in sorted((bundle / "hourly").glob("class_hourly_*.parquet")):
        df = pd.read_parquet(path)
        totals = df.groupby("klass", observed=True)["mw"].sum()
        seen |= {str(k) for k, v in totals.items() if v > 0}
    return seen


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-41 attestation (after seeding the canonical DOF ledger)."""
    rec = _check_recipe(bundle)
    sc, meta = rec["scenario_config"], rec["meta"]

    # Gate G5, measured rather than asserted: the groups holding non-unity bands
    # must carry NO NWPP energy, or the NONE declaration below is false.
    dispatched = _dispatched_classes(bundle)
    groups = sc.get("offer_curve_by_group") or {}
    live_nonunity = sorted(
        g
        for g, b in groups.items()
        if isinstance(b, dict)
        and g in dispatched
        and any(float(b.get(k, 1.0)) != 1.0 for k in _BANDS)
    )
    if live_nonunity:
        raise SystemExit(
            "gen_nwpp41_attestation refuses this bundle: non-unity bands on classes "
            f"NWPP actually dispatches: {live_nonunity}"
        )

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

    switches = dict(_INHERITED_SWITCHES)
    switches["coal_prb_proxy_own_iso"] = {
        "value": True,
        "where": (
            "ScenarioConfig.coal_prb_proxy_own_iso, armed for NWPP alone at "
            "pipeline/backcast_config.py (the backcast path; iso_configs "
            "default_scenario_overrides would have been DEAD here, since "
            "run_calibration_full.py never applies them)"
        ),
        "identification": "measured-physical",
        "source": (
            "EIA-923 Schedule-2 delivered PRB prices filed by NWPP's OWN reporters — "
            "Dave Johnston, Naughton, Wyodak and Jim Bridger — read through the new "
            "per-ISO reader data.coal.coal_supply_by_iso over the derived "
            "data/raw/_processed-legacy/coal_supply_NWPP.csv (17 rows, md5 "
            "4bc7f9a61724ec4562599230ca77e4c6; 9 prb / 6 bituminous / 2 waste; 0 "
            "unresolved), produced by scripts/data/derive_coal_supply.py --iso NWPP "
            "--census-vintage 2023 2024 2025. The flag selects WHICH measured series the "
            "fallback proxy pools; it introduces no value of its own."
        ),
        "why_not_a_free_parameter": (
            "Rule 21 [R-DOF]: a boolean that swaps one measured input for a better-aligned "
            "measured input is not a tuned value. Before the arm, an NWPP plant with no "
            "Schedule-2 filing priced against ERCOT's delivered PRB cost "
            "($1.818 / $1.760 / $1.622 per MMBtu in 2023 / 2024 / 2025) because "
            "_prb_monthly_actuals pooled data.coal.COAL_PLANT_SUPPLY, every plant of which "
            "is in TEXAS — a rule-25 [R-ISO-SCOPE] violation in substance. NWPP's own PRB "
            "reporters pay $2.463 / $2.134 / $2.066. Rule 14 [R-ACCURATE], not the residual, "
            "is why it arms. Set ex ante in PRECOMMIT-nwpp-41 §7 and never swept."
        ),
        "reach": (
            "Measured zero-LP before the solve and confined exactly: only the coal plants "
            "with no Schedule-2 filing of their own move — Colstrip and Hardin in every "
            "year, plus TS Power in 2025. Non-coal offer max|delta| = $0.0000000000; pmax "
            "and availability max|delta| exactly 0 in all three years. The arm cannot reach "
            "a non-coal unit, a capacity or an availability."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED]: the same quantity regenerates for a forward year from "
            "the then-current EIA-923 Schedule-2 filings and responds to changed delivered "
            "coal cost. It is a price input, never an outcome pinned to an actual."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: the proxy REPLACES the pooled-average fallback for these "
            "plants rather than stacking on it — a plant that files its own delivered price "
            "still uses that price, unchanged, and the proxy is reached only where no filing "
            "exists. No second coal-pricing mechanism is introduced."
        ),
    }

    gov: dict = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "authorized_price_tuning_declared": (
            "NONE — no rule-1 [R-STRUCT] / rule-13 [R-MEASURED] authorized price-tuning "
            "channel is in use. Every committed / econ_low / econ_high / peak band on every "
            "class NWPP dispatches is exactly 1.0, and that is verified from the bundle's "
            "own dispatch rather than asserted: the three groups in the shared config that "
            "DO carry non-unity bands (CC_INTERMEDIATE, CT_INTERMEDIATE, ST_GAS_INTERMEDIATE) "
            "carry ZERO NWPP energy in all three solved years, machine-checked by "
            "scripts/gen_nwpp41_attestation.py against hourly/class_hourly_<year>.parquet "
            "before this file was written. econ_low_share 0.55 is a STRUCTURAL SHARE, which "
            "rule 1 excludes from the band channel by name, not a band multiplier. The delta "
            "JSON is {}; no phys_* field exists; no --offer-curve-json, --set, adder, offset, "
            "haircut or proxy-on-a-residual was passed. Most of this footprint is cost-based "
            "vertically-integrated dispatch and NO NWPP price residual exists to tune on "
            "(FINDING-nwpp-13 read NO), so the channel could not have been used even in "
            "principle."
        ),
        "attested_by": (
            "NWPP-41 (2026-09-19): NWPP-40's frozen recipe plus ONE arm, "
            "coal_prb_proxy_own_iso=True. ONE shard, ONE --year 2023 2024 2025 invocation, "
            "years sequential inside it (rules 12 / 16 [R-ALLYEARS] / 32(b) [R-SHARD]); the "
            "parent ran no LP (rule 32(a)). The recipe, the zero-LP root-cause analysis, the "
            "confinement measurement and every expected number were fixed in "
            "docs/handoffs/PRECOMMIT-nwpp-41-2026-09-17.md and pushed BEFORE the shard was "
            "pinned; the shard was pinned to the immutable SHA "
            "666343a2bf86f204c5ca6c672a680da32150a640, added exactly three commits on top of "
            "it (two per-year evidence pushes and the final bundle at "
            "1fb4b6b5c680ca5ae0ef9375eb11b7cbbb08d64d) and never rebased, pulled or synced — "
            "verified by the parent with git merge-base --is-ancestor. The rule-29(b) control "
            "is NWPP-40's committed bundle, differenced at form 4; G-DRIFT classifies the one "
            "other config delta (neiso_coldsnap_derate_dualfuel_unswitched, default False, "
            "NEISO-gated) as INERT, so no control solve was spent. Rule 21 [R-DOF]: the "
            "ledger is seeded by build_dof_ledger.py and the entries tagged residual are "
            f"{residual_names} — every one an inherited generic default carried unchanged from "
            "NWPP-40, none chosen on an NWPP residual. The arm itself is measured-identified, "
            "not residual (see measured_input_switches.coal_prb_proxy_own_iso). Nothing was "
            "swept against any gate. The determination was reached on structure: the C1 fix "
            "was proven zero-LP before the solve and the solve confirmed it, and C4 was "
            "expected to remain FAIL and is reported as such rather than pursued by tuning "
            "(rule 1 [R-STRUCT])."
        ),
        "cross_iso_defect_reported_not_fixed": (
            "Rules 25 [R-ISO-SCOPE] / 28(d) [R-MECH-MATRIX]: the SAME pooled-proxy defect "
            "reaches MISO (12 affected plants), PJM (2) and SPP (3-5), whose plants without "
            "their own Schedule-2 filing likewise price against Texas PRB deliveries. This "
            "lane did NOT fix them — a verdict in one ISO never fills another ISO's cell, and "
            "each target lane must derive its own rank file from its own market's data. Their "
            "mechanism-matrix cells stay O (open) with the affected plant lists recorded."
        ),
        "measured_input_switches": switches,
    }
    att["governance"] = gov

    disc = dict(_INHERITED_DISCLOSURES)
    disc["note"] = (
        "NWPP-41 disclosures — the determination basis, reported at full magnitude and "
        "absorbed nowhere. Every NWPP-40 disclosure is inherited VERBATIM and still "
        "applies; the two entries below are this lane's own."
    )
    disc["c1_coal_taxonomy_seam_repaired"] = (
        "This lane's headline, and it was a PLUMBING defect rather than a dispatch one. "
        "data/raw/_processed-legacy/coal_supply_NWPP.csv had never been derived, so "
        "coal_supply_class returned \"\" for all 17 NWPP coal plants and every one binned to "
        "the bare class COAL — which the benchmark has no row for, because the benchmark "
        "passes the EIA-923 row's own fuel code to the SAME resolver and itemizes COAL_PRB / "
        "COAL_BIT / COAL_WC. Five C1 rows failed on that asymmetry. The seam also corrupted "
        "the SHARE denominator: calibration_verdict._gen_totals sums the model over BENCHMARK "
        "keys, so the model's entire coal output was excluded from its own total and every "
        "other class's share read high (2024 CC_REGULAR +3.6 pp before, +1.4 pp after). "
        "Measured on the committed NWPP-40 bundle zero-LP BEFORE any solve: C1 5 FAIL -> 0 "
        "FAIL with the dispatch byte-identical, and C2 / C4 byte-identical. The solve "
        "confirms it: no bare COAL row in any of 2023 / 2024 / 2025, and the itemized family "
        "reads 39.6133 / 27.0076 / 27.2069 TWh."
    )
    disc["prb_proxy_was_pooling_texas"] = (
        "The rule-25 [R-ISO-SCOPE] half, found while fixing C1 and fixed with it because the "
        "same derived file feeds both. _prb_monthly_actuals pooled "
        "data.coal.COAL_PLANT_SUPPLY, every plant of which is in TEXAS, so an NWPP coal plant "
        "with no EIA-923 Schedule-2 filing priced against ERCOT's delivered PRB cost. This "
        "compounds the inherited coal_fuel_price_gap disclosure above: Colstrip and Centralia "
        "file no price in any year (2,377.3 of 8,910.2 MW of coal, 26.7 %), so the proxy is "
        "not a corner case for this footprint — it prices a quarter of the coal fleet. NWPP's "
        "own four PRB reporters pay $2.463 / $2.134 / $2.066 per MMBtu against ERCOT's "
        "$1.818 / $1.760 / $1.622. Confinement measured exactly: only Colstrip and Hardin "
        "move in every year (TS Power also in 2025), non-coal offer max|delta| "
        "$0.0000000000, pmax and availability max|delta| exactly 0."
    )
    disc["c4_still_fails_and_was_not_pursued"] = (
        "PRE-REGISTERED AND UNCHANGED: C4 coal hourly shape was expected to remain FAIL and "
        "does. The diagnosis is recorded (PRECOMMIT-nwpp-41 §4) and the lever is ROUTED to "
        "the desk, not attempted here: the coal offer stack is bimodal — a $4.50 must-run "
        "tranche in the money 100 % of hours against $37.7-42.8 for everything else, versus a "
        "$26.15 mean price — so ~90 % of model coal is price-insensitive and ~4,600 MW of "
        "available coal sits out of merit 87 % of hours. Availability was measured and ruled "
        "out. The measured fleet's midday trough DEEPENS with solar (peak/trough 1.21 -> 1.32 "
        "-> 1.40 across 2023-2025) where the model reads 1.02. The successor is blocked on "
        "bin_assignments_NWPP.csv, which is absent for every legacy-bin ISO. Rule 1 "
        "[R-STRUCT]: this lane did not reach for the residual, and the miss rides this "
        "determination basis at full magnitude."
    )
    disc["solved_years"] = solved_years
    disc["recorded_signature"] = {
        "coal_prb_proxy_own_iso": sc.get("coal_prb_proxy_own_iso"),
        "hydro_cascade_coupling": sc.get("hydro_cascade_coupling"),
        "hydro_backfill_year": meta.get("hydro_backfill_year"),
        "hydro_eia930_monthly": bool(meta.get("hydro_eia930_monthly")),
        "wefor_multiplier": sc.get("wefor_multiplier"),
        "plant_level_fleet": sc.get("plant_level_fleet"),
        "use_campd_bins": sc.get("use_campd_bins"),
        "use_campd_bins_note": (
            "reads True in the config and is INERT: NWPP is absent from CAMPD_BINNING_ISOS "
            "(card N8), so the fleet takes the legacy aggregate_fleet path with "
            "plant_level_fleet=True; thermal_tranches_NWPP.csv is not read. Identical to the "
            "NWPP-40 control."
        ),
        "control_diff": (
            "scenario_config differs from results/calibration/nwpp40_span_A in exactly TWO "
            "fields: coal_prb_proxy_own_iso (absent -> True, this lane's arm) and "
            "neiso_coldsnap_derate_dualfuel_unswitched (absent -> False, a NEISO-gated flag "
            "at its default, INERT for NWPP under the rule-29(b) G-DRIFT classification)."
        ),
        "dispatched_classes": sorted(dispatched),
    }
    att["disclosures"] = disc
    att["exceptions"] = []
    return att


def main() -> None:
    """Write the attestation into the NWPP-41 span bundle."""
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
    print(f"  gate G5: authorized_price_tuning = NONE (verified from dispatch)")
    print(f"  dispatched classes: {len(att['disclosures']['recorded_signature']['dispatched_classes'])}")


if __name__ == "__main__":
    main()
