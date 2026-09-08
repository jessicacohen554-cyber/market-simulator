# DESIGN — capx D87 / D88 READ: the two S19 seams, dispositioned at zero LP

**Lane:** capx D87/D88 READ · **Branch:** `claude/capx-d87-d88-read-eb52a8` (fresh off `origin/main`
`4e4ad90d`) · **Date:** 2026-09-08 · **Model:** Fable (rule 27 `[R-PUSH]`) · **Data profile:** `code`
**Charter:** capx ledger r#60 (`capx-director-ledger-2026-08.md` §0bd am.1 + the D87/D88 READ row) ←
SCN ruling S19 (`scenario-desk-ledger-2026-09.md` r#21, §4 "Routed OUT, not chartered")
**Kind:** a READ. **Zero LP. No file under `src/` edited. No test, no config, no matrix shard, no
registration.** Every line quoted below is HEAD `4e4ad90d`; every number is from a committed artifact.

---

## RECOMMENDATION

- **D87 (SCN D-15, the CCS attribute-coverage seam): CHARTER. Real at HEAD, forecast-only, zero
  DOF, no key moves, one seam — the same shape as capx D77, one file over. Scope paragraph in §1.6.**
- **D88 (SCN D-14, `unit_id` uniqueness): CHARTER, as its own lane and FIRST. Real at HEAD, and the
  committed record now answers the question the G1 re-check left UNKNOWN: the collision is
  in-horizon on every NEISO T3 golden variant, including the run the registered `neiso-t3` verdict
  is scored on. Zero DOF, no key moves. Scope paragraph in §2.6.**
- **Not merged.** They are not one object (§3): D87 is a pricing-coverage omission inside the step-2
  screen; D88 is an identity defect in the fleet builder's conversion path. They share one file and a
  forecast-only footprint and nothing else. A merged lane could not attribute its screen.

---

## 1. D87 — the CES target row cannot reach the CCS retrofit screen

### 1.1 Is it real at HEAD? YES — reproduced from the code, unrepaired since it was raised

`git log --since=2026-09-06 -- ccs.py legacy_bins.py federal_ces.py evolve.py data/fleet/__init__.py`
shows one commit (`9d9ffacd`, the PJM sector-gate merge, 2026-09-06), which predates SCN
r#19/r#21 and does not touch the pricing lines. The seam is exactly as SCN-WS5A-POLICY-NYISO §4.2
read it.

The retrofit screen prices each continuation's certificate through ONE resolver and nothing else:

```python
# src/market_sim/model/capacity_evolution/ccs.py:472-476
        # Per-state attribute (certificate) prices — max(legacy eac_price_*,
        # premium × state credit fraction); the unabated state's cesa_ci
        # partial credit is what makes the uplift INCREMENTAL, never gross.
        attr_unabated = effective_eac_price_for_unit(config, "gas_cc", old_er, year)
        attr_post = effective_eac_price_for_unit(config, "gas_cc_ccs", new_er, year)
```

and that resolver folds two legs only — the legacy per-fuel scalar and the exogenous premium:

```python
# src/market_sim/policy/federal_ces.py:586-590, 627-629
    legacy = get_eac_price_for_new_entry(fuel_type, config)
    federal = premium_for_year(config, year) * unit_credit_fraction(
        config, fuel_type, emission_rate_t_per_mwh
    )
    return legacy, federal
    ...
    return max(
        eac_price_components_for_unit(config, fuel_type, emission_rate_t_per_mwh, year)
    )
```

The target row's dual lives somewhere else entirely — `clean_attribute_price_by_fuel`, threaded
from the prior year's `clean_region_duals` (`runner.py:2331`, `:2351`, `:4724-4738`) into
`evolve_fleet` (`evolve.py:118`) — and `evolve_fleet` never hands it to the retrofit screen:

```python
# src/market_sim/model/capacity_evolution/evolve.py:664-674
    fleet, retrofit_log = _pkg_ns().apply_ccs_retrofit(
        fleet,
        prices,
        year,
        config,
        config.iso,
        gas_price_per_mmbtu=gas_price_per_mmbtu,
        carbon_price=carbon_price,
        zone_names=screen_zone_names,
        cumulative=cumulative,
    )
```

`apply_ccs_retrofit`'s signature (`ccs.py:179-189`) has no parameter for it. The other two capacity
screens DO read it, through the one shared consumer helper:

```python
# src/market_sim/model/capacity_evolution/retirements.py:3634-3636   (step 3)
        clean_for_unit = clean_credit_for_zone(
            clean_attribute_price_by_fuel, g.fuel_type, zone
        )
# src/market_sim/model/capacity_evolution/new_entry.py:1202-1209      (step 5, the CCS new-build)
            clean_for_tech = _clean_credit_for_tech(
                tech, iso_config, zone_names, clean_attribute_price_by_fuel
            )
            effective_attribute_price = max(
                effective_eac_price_for_tech(config, tech, year),
                rps_for_tech,
                clean_for_tech,
            )
```

**Why the target row's dual is otherwise invisible to the screen.** A target-row config carries a
ZERO premium by construction — `__post_init__` refuses the two together (`scenarios.py:17546-17552`,
rule 19 `[R-ONE-MECH]`) — so under `CES-T80` the resolver returns the legacy scalar
`eac_price_gas_cc_ccs`, whose default is `0.0` (`scenarios.py:3518`). `attr_post = attr_unabated = 0`:
the $50 ACP row prices the LP's certificates and the entry and exit screens, and buys the retrofit
screen nothing. That is the measured `0.0 MW` in every year of every `CES-T80` leg
(`FINDING-scn-ws5a-policy-nyiso-2026-09-07.md` §4.2; generalised to five of six ISOs in
`FINDING-scenario-campaign-2026-09-07.md` §5).

**It was always meant to reach the screen.** The row's own docstring says its dual is "mapped to the
screens by `federal_ces_row_fuel_credit` through the existing `clean_attribute_price_by_fuel` seam
(no new consumer)" (`federal_ces.py:203-206`), and `federal_ces_row_fuel_credit` already carries a
`gas_cc_ccs` entry at `dual × tech_credit_fraction` (`federal_ces.py:167-185`; `clean_tiers.py:263-266`:
"a CCS candidate earns 0.95 of the federal dual"). The seam exists and the fraction exists; the third
screen was simply never connected to them. `evolve_fleet`'s own docstring records the history:
the clean credit is "composed into the SAME max(eac, rps) attribute doctrine at **both** screens"
(`evolve.py:215-219`) — "both" being retirement and entry, the two that existed when FFR-7B Arm 3
wired the seam — while the retrofit screen's attribute revenue "resolves internally via
`effective_eac_price_for_unit` — one delivery channel, W2-C" (`evolve.py:226-229`), i.e. it was wired
in the premium era and never revisited when SCN-WS2a added the row.

### 1.2 Blast radius

**Backcast: NONE, on two independent gates.** `apply_ccs_retrofit` returns before any pricing when
`year < config.ccs_retrofit_available_year` (`ccs.py:354-355`; 2028 in every committed config this
read inspected — the 13 target-row configs and the six r2 `REF`s the G1 re-check read), and
`__post_init__` refuses a target row in `mode="backcast"` outright (`scenarios.py:17528-17533`).
Every keeper is byte-identical whatever a repair does. **Hindcast (T1-H, 2021–2025) and the
crossover window: inert** for the same year gate. **This is a forecast-mode, capacity-evolution
step-2 object only** — which is exactly why it is this desk's and no keeper's.

**Forecast, ≥ 2028, with a live clean-row dual on `gas_cc_ccs`.** Three families of row can put one
in `clean_attribute_price_by_fuel`; the seam is blind to all three equally:

| row family | admits `gas_cc_ccs`? | committed bundles reachable |
|---|---|---|
| federal CES target row (`federal_ces_target_by_year`) | yes, at `federal_ces_ccs_capture_fraction` = 0.95 | **12 live**: `scn-campaign-policy-2026-09-06/<ISO>/{CES-T80, ALL-CLEAN}` × CAISO, ERCOT, MISO, NEISO, NYISO, PJM (2026–2030). The 13th target-row config, `scenario-probes/scn-ws2a/neiso-2026-t0-target`, is a 2026-only T0 leg — below the 2028 gate, inert. |
| MISO state clean tiers (`miso_clean_tier_rows`) | **MI yes** (`capacity_market.py:5356-5369` lists `gas_cc_ccs`; MN does not) | 32 tracked configs arm it. The hindcast ones (2021–2025) are inert; the MISO T1-F family (`ff-t1f-d45r/d60/d65br/miso`, `ff-t1f-s123/verify`, the `scn-campaign-load-*-r2/MISO/*` legs) is reachable **iff** the MI row's dual is non-zero in 2027–2029 and a `gas_cc` host sits in `MISO-East`. **Unmeasured** — the clean duals are not in these bundles' committed artifacts (NYISO §9 item 4). Named as the charter's first zero-LP measurement, not asserted either way. |
| voluntary clean-demand row (`voluntary_clean_demand_path`) | **no** by default — `VOLUNTARY_ELIGIBLE_FUELS_DEFAULT = (wind, solar, offshore_wind, geothermal)` (`constants.py:5319-5324`) | inert unless a config overrides `voluntary_eligible_fuels` to list CCS gas; none of the 21 armed configs is known to. |

**Scored surfaces.** No FF-2D verdict is keyed to a target-row run (`frontend/data/forecast/` has no
`CES-T80` reference), so **no scored cell moves**. What is mis-stated is the scenario campaign's own
record: the target-row rows of the Stage C memo (`FINDING-scenario-campaign-2026-09-07.md` §5) and
the six ISO policy FINDINGs — all of which already carry the caveat SCN ruled at S19 ("not one
instrument at two levels"). A repair re-bases those rows; it does not change any determination.

**Direction of the correction, from the code.** With the dual folded in, `attr_post` rises by
`dual × 0.95` and `attr_unabated` stays 0 (below), so `uplift_window` and `uplift_post` rise by
`≈ dual × 0.95 × utilised hours × avail` per MW-yr and the retrofit set can only grow — toward the
premium legs, which is the direction the campaign's own arithmetic says it must, and in the five
cap-bound ISOs it saturates at the 3 GW/yr cap exactly as the premium does. NYISO is the one ISO
with headroom (campaign §6), so it is where the arm can actually move MW.

### 1.3 Defect or convention? DEFECT — a coverage omission, not a doctrine

The NYISO lane was careful to say "not a defect judgement — the max() attribute doctrine is
deliberate" (§9 item 1). The doctrine is indeed deliberate and the repair keeps it: one certificate,
several buyers, `max()`, never a sum. What is NOT deliberate is that the retrofit screen folds two of
the buyers where its two sibling screens fold three, and the row's own documentation says all
screens see it. Two facts make this a defect rather than a design:

1. **Steps 2 and 5 are one joint decision on the same technology and read different prices.** The
   retrofit screen "runs before new entry so retrofits displace some new-build CCS demand"
   (`evolve.py:660-661`); the new-build `gas_cc_ccs` candidate earns the clean dual
   (`new_entry.py:1198-1204`, explicitly "this is what lets a … `gas_cc_ccs` (MI clean) candidate earn
   a state clean dual") while the retrofit of an existing `gas_cc` into the same `gas_cc_ccs` does
   not. Under a target row the model therefore prefers a new-build capture island over a retrofit of
   the same host by the full value of the certificate. That is not a market structure; it is a wiring
   asymmetry.
2. **It is not CES-specific.** MI's clean tier admits CCS gas and the same omission applies to it —
   so this is the *footprint-wide attribute-coverage seam* SCN named, and the right description is
   "the retrofit screen does not consume the clean-tier seam", not "the CES target row is special".

### 1.4 Zero free parameters? YES

The repair is a composition through helpers that already exist, with values that already exist:

```python
# the only change in kind — one new keyword on apply_ccs_retrofit, default None:
zi = zone_names.index(gen.zone)                         # the same lookup _retrofit_price_row does (ccs.py:172-175)
attr_unabated = max(effective_eac_price_for_unit(config, "gas_cc",     old_er, year),
                    clean_credit_for_zone(clean_attribute_price_by_fuel, "gas_cc",     zi))
attr_post     = max(effective_eac_price_for_unit(config, "gas_cc_ccs", new_er, year),
                    clean_credit_for_zone(clean_attribute_price_by_fuel, "gas_cc_ccs", zi))
```

- No `ScenarioConfig` field, no constant, no per-ISO value (rules 21 `[R-DOF]`, 24 `[R-REGISTRY]`,
  25 `[R-ISO-SCOPE]`). The credit fraction is the one `federal_ces_row_fuel_credit` /
  `MISO_CLEAN_TIER_REGIONS` already declare; the dual is the LP's own.
- `None` (the family off) ⇒ `clean_credit_for_zone` returns `0.0` (`clean_tiers.py:303-310`) ⇒
  `max(x, 0.0) == x` for every non-negative `x` ⇒ **byte-identical wherever no clean row exists**,
  which is every backcast, every hindcast and every forecast bundle without a target row or an armed
  MISO tier.
- The unabated leg folds to 0 today under both crediting modes (`federal_ces_row_fuel_credit`
  documents unabated `gas_cc` as "conservative 0" at fuel level, `federal_ces.py:175-178`), so
  folding it is a no-op that keeps the two states symmetric with `retirements.py:3634`, which folds
  for every `g`. Pre-register it as the symmetric form; do not leave it asymmetric "because it is
  zero" — that is the shape this seam came from.
- The RPS leg is deliberately NOT added: `_RPS_ELIGIBLE_FUELS = {wind, solar}`
  (`retirements.py:145`) — gas never earns it, and a leg that is zero by construction is a misleading
  leg (rule 19).
- No `ScenarioConfig` field ⇒ rule 28 duty (c) not engaged; duty (b) is the `ccs_retrofit_screen`
  and `federal_ces` cells of whichever ISO the charter screens on.

### 1.5 Does it move any key? NO — and it is the same-key invalidation class D77 was

- The cache key hashes the config plus the D79 solve surface (`scenarios.py:18673-18717`);
  `clean_attribute_price_by_fuel` is a runtime prior-year value, not a field, and `ccs.py` /
  `federal_ces.py` / `evolve.py` are not `SURFACE_MODULES` (`solve_surface.py:57-65`). **Zero keys
  move.**
- Therefore the 12 live target-row bundles sit at exactly the key a post-fix run computes and will
  CACHE-HIT stale unless purged — the "Epoch 2026-09-06b" class (`results/cache.py:371`). The charter
  owes an epoch entry naming those 12 (and the MISO family conditionally, per the §1.2 measurement).

### 1.6 Recommendation — CHARTER (scope paragraph for the director)

> **capx D87 — the retrofit screen consumes the clean-tier seam.** Opus. Profile: `nyiso` (screen)
> + `code`. One seam, one file pair: thread `clean_attribute_price_by_fuel` from `evolve_fleet`
> (`evolve.py:664`) into `apply_ccs_retrofit` as a `None`-default keyword, and fold
> `clean_credit_for_zone(by_fuel, fuel, zone_idx)` into BOTH `attr_unabated` and `attr_post` at
> `ccs.py:475-476` through the existing `max()` — the same composition `retirements.py:3634` and
> `new_entry.py:1202` already use, no new field, no new constant, no RPS leg. Phase 0 (zero LP):
> (i) reconstruct the pre-solve delta for the NYISO `CES-T80` 2028–2030 cohort from its committed
> `duals.json` (`dual × 0.95` per MWh into `uplift_window`), and (ii) measure whether the MI clean
> row's dual is non-zero in any committed MISO T1-F bundle — if it is, the MISO T1-F family is in the
> blast radius and the epoch entry names it. Screen (rule 29): ONE year, NYISO 2030 — the only ISO
> with retrofit headroom (campaign §6) and the ISO the seam was measured on — control = the committed
> `scn-campaign-policy-2026-09-06/NYISO/CES-T80` bundle under a G-DRIFT audit, never a control
> solve. STOP gates, structural only: every `CES-P*` leg's retrofit ledger byte-identical (no row ⇒
> `by_fuel` has no federal entry ⇒ `max(x, 0) == x`); the target leg's retrofit set moves in the
> direction and order the phase-0 delta implies and stays within the 3 GW/yr cap; no non-CCS ledger
> row moves in 2026–2027; every backcast keeper and the `ff-t1h` hindcasts byte-identical by
> construction and by test. Deliverables: the fix, a seam test in
> `tests/unit/model/test_ccs_retrofit.py` (a target-row config buys retrofit where a zero-premium
> config does not; a `None` family is byte-identical), the cache-epoch entry, the NYISO shard cells
> for `ccs_retrofit_screen` and `federal_ces`, and a FINDING that re-bases the campaign's target-row
> rows and routes the six ISO policy FINDINGs' `CES-T80` numbers to SCN for re-statement. Not in
> scope: D77's routed parasitic-uplift item; the level of `ccs_retrofit_vom_adder`; anything under
> `_AGGREGATABLE_FUELS` (that is D88). Land AFTER D88's guard so the screen runs with it armed.

---

## 2. D88 — `unit_id` is not a key in an evolved fleet

### 2.1 Is it real at HEAD? YES — the mechanism, quoted, and no guard anywhere

Three lines make the collision, and none has changed since SCN r#19:

**(a) Retrofit keeps the id and changes the fuel.** Documented as a convention and executed as one:

```python
# ccs.py:192-193 (docstring)          A retrofit converts a ``gas_cc`` generator to ``gas_cc_ccs`` in place.
#                                     The unit keeps its zone, capacity and ``unit_id`` but gets: …
# ccs.py:590-591 (conversion block)
        gen.ccs_capture_fraction = config.ccs_retrofit_capture_rate
        gen.fuel_type = "gas_cc_ccs"
```

**(b) The end-of-year aggregation passes the converted unit through and re-mints its old id for
whatever unabated `gas_cc` now occupies the same group.** `gas_cc_ccs` is not aggregatable, so the
converted unit takes the `passthrough` branch with its pre-retrofit id, while every unabated
`gas_cc` in the same `(efficiency_bin, zone)` collapses into a representative whose id IS that
string:

```python
# src/market_sim/data/fleet/legacy_bins.py:41-43
_AGGREGATABLE_FUELS: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "coal", "oil", "biomass"}
)
# legacy_bins.py:244-256 (passthrough predicate) … g.fuel_type not in _AGGREGATABLE_FUELS … or g.is_campd_bin
# legacy_bins.py:269
            unit_id = f"{fuel_type}_{efficiency_bin}_{zone}"
# legacy_bins.py:300
    return passthrough + representatives
# evolve.py:1125 — runs at the end of EVERY evolution year
    fleet = aggregate_fleet(fleet, n_bins=config.heat_rate_bin_count)
```

**(c) New gas-CC entry lands in exactly that group.** A new unit is minted
`f"{tech_type}_new_{year}_{seq}"` (`new_entry.py:648`) with `efficiency_bin` = the best
`HEAT_RATE_BINS["gas_cc"]` entry (`new_entry.py:658-663`, `h_class`), and `gas_cc` IS aggregatable —
so at the next `aggregate_fleet` it becomes `gas_cc_h_class_<zone>`, the id the converted unit still
holds. **The trigger is therefore: a legacy representative retrofitted in year Y, then any economic
`gas_cc` build in the same zone in a year ≥ Y within the horizon.** Under CAMPD binning
(`use_campd_bins=True`, every ISO's forecast recipe) the base thermal fleet is per-plant passthrough,
so the `gas_cc_h_class_<zone>` representatives are, in practice, **the model's own prior new-build
gas CC** (plus any raw EIA-860 gas CC the synthesis did not bin, `assembly.py:1695-1711`). The
collision is a forecast-fleet-on-forecast-fleet event.

**No guard exists.** `FleetArrays.unit_ids` is a positional comprehension
(`data/fleet/arrays.py:3651`: `unit_ids=[g.unit_id for g in generators]`), `n_gen = len(unit_ids)`
(`data/fleet/__init__.py:407-410`), and there is no `assert`, `Counter` or `len(set(...))` over
`unit_id` anywhere in `src/market_sim/` (grep, this session).

### 2.2 Blast radius — the record answers what the G1 re-check could not

The G1 re-check (`FINDING-scn-resolve-g1-recheck-2026-09-07.md` §3.2) stated in-horizon exposure as
"UNKNOWN without the ledgers … none is ruled out". **The ledgers are committed** (496 tracked
`evolution_<year>.json`), and one pass over them (zero LP, this session) settles it. Eighteen tracked
bundles record a CCS retrofit on a legacy-form id; the trigger of §2.1(c) fires in two families:

| family | legacy-id retrofit | later economic `gas_cc` in the same zone | verdict |
|---|---|---|---|
| NYISO T1-F ×3 (`ff-t1f-d45r`, `d60`, `d65br`) | 2028 `gas_cc_h_class_NYC` (1.8 MW); 2030 `…Upstate_West` | none | no collision |
| CAISO T1-F ×3 (`d46`, `d60`, `d65br`) | 2030 `gas_cc_h_class_NP15` | none (last year) | no collision |
| MISO `ff-t1f-s123/verify` | 2029 `…MISO-Illinois` | none | no collision |
| PJM `ff-t1f-s6-pjm/ledger` | 2030 `…PJM_ATSI` | none (last year) | no collision |
| **ERCOT `ff-t1f-d65br`** | 2029 `…Houston`; **2030 `gas_cc_h_class_North`** | **2030: 3,000 MW economic `gas_cc`, North** | duplicate in the **2030 solved fleet** (the year's LP and `FleetContext`); no capacity screen reads it in-horizon — 2030 is the last year. This is the instance the ERCOT resolve lane measured. |
| **NEISO T3 golden, ALL 9 variants** (`bau`, `bau-prera-2026-08-31`, `bau-d46` + its 4 `fc6` arms, `bau-d60`, `bau-d65br`; 2026–2050) | 2031 `gas_cc_h_class_Central` (2032 in `bau`) | **2032 on**: 1,000 MW economic `gas_cc` in Central in 2032/2034/2036/… (`bau-d65br`: from 2037) | **duplicate from the 2032 (resp. 2037) solved fleet to 2050 — 13 to 18 years in-horizon, read by every step-3 consumer every year.** |

The T3 record is unambiguous because it shows the re-mint *happening*: in `bau-prera-2026-08-31` the
SAME id `gas_cc_h_class_Central` is logged as retrofitted in **2031, 2040, 2042 and 2044** (in `bau`:
2032 and 2040), which is impossible for one unit — a retrofit is irreversible and a converted unit is
never a candidate again (`ccs.py:400`). Each later row is a re-minted unabated twin (the 2040 row's
`mw` = 3,000.0 = the 2032 + 2034 + 2036 builds collapsed into one representative), so by 2045 that
bundle's fleet carries **four generators named `gas_cc_h_class_Central`**, three converted and the
fourth whatever entry followed.

**The registered `neiso-t3` verdict is scored on one of these runs**: `ff-verdicts.json:4835-4843`
keys it to `neiso-2026-2050-t3-golden3-d60`, cache key `f04fd06348e1623d` = `ff-t3-neiso-golden/bau-d60`,
which collides from 2032. So the consumers below did read a duplicate, in-horizon, on the program's
only T3 golden, for eighteen scored years — including the FC-5 corridor years 2035 and 2040 that
D77 §8.2 names as the ones actually scored.

**Consumers that collapse on a duplicate** (enumerated this session over `src/` and the scorers;
verified at HEAD for the decision-path three):

| site (HEAD) | keys on | duplicate effect |
|---|---|---|
| `retirements.py:3423` `idx_of = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}` | `unit_id → LP dispatch row` | **last-write-wins**: both twins read the SAME row — the converted unit's pro-forma margin is the unabated twin's dispatch (or vice versa) inside the step-3 exit screen |
| `retirements.py:3937-3938` `margins = [m … if m[0].unit_id not in exit_exempt_unit_ids]` | set membership | one twin's exemption (retrofit, dated exit, sector gate) exempts **both** |
| `retirements.py:4020` / `:4038` `retired = {g.unit_id …}`; `survivors = [g … not in retired]` | set membership | **retiring one twin drops both** from the fleet — a capacity leak, not bookkeeping |
| `retirements.py:4011-4015`, `evolve.py:685-687` | `loss_years[unit_id]` counter | shared exit clock; one twin resets or clears the other's |
| `retirements.py:3096-3120`, `adequacy.py:735-737, 781-796` | D57 sell-offer stack / `cleared_unit_ids` | two offers under one id; both twins read one accredited MW; one clearing marks both cleared (PJM-armed only) |
| `evolve.py:663/691` `_pre_ccs` / `_post_ccs`; `evolve.py:933/993` `_pre_entry_ids_all` set-diff | ledger writers + the growth-ladder MW | a retrofit row can be dropped; an entrant whose minted id collides is invisible to entry accounting and never charged to the rate cap |
| `scripts/check_forecast_invariants.py:482-492` (I5) | `retired_at[unit_id]` | a re-minted twin after a retired twin is the exact false-positive shape of "retire-and-re-enter" |
| `model/lp/model.py:1562`, `pipeline/basis_cache.py:153-155` | warm-start basis | self-healing (HiGHS repairs); the layout fingerprint changes deterministically — not a cache key |

Backcast: **never** — a backcast rebuilds its base fleet every year and does not enter
`evolve_fleet`; hindcast and crossover: the retrofit is below the 2028 gate, so this trigger cannot
fire (the census found no legacy-id retrofit in any `results/hindcast/` ledger). CAMPD per-plant
tranches never re-mint (`is_campd_bin` passthrough, the G-28 fix), so CAISO's and MISO's measured
cohorts are unexposed *through their cohorts*, as the re-check said — but their fleets are exposed
through their own new-build gas CC exactly like NEISO's, the moment a horizon is long enough.

### 2.3 Defect or convention? BOTH conventions are legitimate; their composition is the defect

- Re-minting `f"{fuel_type}_{efficiency_bin}_{zone}"` is a convention with a reason: the id *is* the
  group key, so a representative is addressable by what it represents (`legacy_bins.py:185-192`).
- Keeping `unit_id` on retrofit is a convention with a reason: the ledger, `loss_tracker` and the
  exempt set all need to say "this unit converted" (`evolve.py:689-691`: "a fuel shift … on the same
  `unit_id`, not a new column").
- The defect is that after conversion the id asserts a group key (`gas_cc`, `h_class`, zone) the
  unit no longer belongs to, and the builder will re-mint that key for whoever does. The G1 re-check's
  reading (§4 point 3: "the id is already self-describing and is simply stale") is the one the code
  supports. "Every consumer qualifies by `fuel_type`" is the wrong shape for the reason the re-check
  gave and the table above confirms: the highest-leverage sites are **set memberships**
  (`exit_exempt_unit_ids`, `retired`, `_pre_entry_ids_all`) with no fuel to qualify by.

### 2.4 Zero free parameters? YES

- **The guard** is an assertion at the one seam every LP fleet passes through —
  `generators_to_fleet_arrays` (`arrays.py:3651`) — raising on `len(set(unit_ids)) != len(unit_ids)`
  with the offending ids named. It changes no decision, costs one set build per year, and it would
  have caught the NEISO T3 case in 2032 instead of five lanes downstream.
- **The re-mint** at conversion is a string. Zero config, zero constants. One design choice to
  pre-register, and it is NOT the form the re-check sketched: `gas_cc_ccs_h_class_Central` alone is
  **insufficient**, because the T3 record shows the same zone converting a second (2040), third and
  fourth representative, and `gas_cc_ccs` is not aggregatable — two converted representatives would
  then collide *with each other*. The id must carry the conversion vintage:
  `f"gas_cc_ccs_{efficiency_bin}_{zone}_r{year}"`, mirroring `new_entry.py:648`'s `{tech}_new_{year}_{seq}`
  — deterministic, order-independent (the re-check's objection to `_2` suffixes does not apply), and
  unique by construction once the guard holds (one id converts at most once per year). Applied only
  where `not gen.is_campd_bin` and the id equals the legacy form exactly; CAMPD per-plant ids are
  untouched. The alternative — adding `gas_cc_ccs` to `_AGGREGATABLE_FUELS` so converted
  representatives merge — is rejected here on structure: it changes the LP column set (merges units
  with different `online_year` and `ccs_capture_fraction` provenance), which is a behaviour change
  beyond identity and a second mechanism in one lane.
- Stated costs (the re-check's §4(b), still true): any cross-year join on a converted unit's
  pre-retrofit id breaks. `loss_tracker` is already popped at conversion (free); the `ccs_retrofits`
  ledger row should carry both `unit_id` (pre) and a new additive `to_unit_id` so the D42/D53 exempt
  sets and every scorer that reads the ledger can follow the rename; `_plant_codes_from_unit_ids`
  is unaffected (legacy ids carry no `_p<code>_`).

### 2.5 Does it move any key? NO

Ids are not hashed (`scenarios.py:18691-18717`; `SURFACE_MODULES` excludes `data/fleet`). Behaviour
moves at unchanged keys on the nine NEISO T3 variants from 2032 on (the `idx_of` correction alone
changes which dispatch row each twin's exit screen reads) and on ERCOT `d65br`'s 2030 `FleetContext`
ids — the same-key invalidation class, so the charter owes an epoch entry naming them. Every T1-F
bundle in the table above is byte-identical (no collision ⇒ the rename fires on a unit no later
entry collides with ⇒ only the ledger string changes; the charter's byte-identity check should
prove that on one such bundle, e.g. NYISO `d65br`, at zero LP by replaying the ledger).

### 2.6 Recommendation — CHARTER, first (scope paragraph for the director)

> **capx D88 — fleet ids are keys: a uniqueness guard and a vintage-stamped re-mint at CCS
> conversion.** Opus. Profile: `neiso` (screen) + `code`. Two parts, one lane, guard first.
> **(a)** In `generators_to_fleet_arrays` (`data/fleet/arrays.py:3651`) raise `ValueError` naming
> the duplicated ids when `unit_id` is not unique; phase 0 (zero LP, ~90 s each) proves it does not
> fire on any ISO's on-recipe `fleet_only` rebuild for every backcast keeper and every T1-F/T1-H
> recipe, so no keeper can be touched. **(b)** In `apply_ccs_retrofit`'s conversion block
> (`ccs.py:590-591`), for a non-CAMPD legacy representative whose id equals
> `f"gas_cc_{efficiency_bin}_{zone}"`, re-mint it as `f"gas_cc_ccs_{efficiency_bin}_{zone}_r{year}"`
> and write the new id to the ledger row as an additive `to_unit_id` beside the existing `unit_id`;
> `_retrofitted_ids` / `exit_exempt_unit_ids` (`evolve.py:685`, `:757`) carry the NEW id. No config
> field, no constant (rules 21/24); no key moves (§2.5). Screen (rule 29): ONE year is not the
> right instrument here — the object only exists across years — so the screen is the cheapest
> colliding horizon: NEISO T3 `bau-d65br` recipe, 2026–2040, control = the committed bundle under a
> G-DRIFT audit. STOP gates, structural only: the guard is silent on every year; 2026–2031 ledgers
> byte-identical to the control; from the first colliding year the fleet carries no duplicate id and
> the `ccs_retrofits` rows carry distinct `to_unit_id`s; no non-gas ledger row moves in any year.
> Deliverables: the guard + rename, a seam test (a legacy representative retrofitted then re-minted
> by later entry yields two distinct ids and no raise; a CAMPD tranche keeps its id; a fleet with a
> forced duplicate raises), the cache-epoch entry naming the nine NEISO T3 variants and ERCOT
> `d65br`, the NEISO shard's `ccs_retrofit_screen` cell, and a FINDING that hands the
> `neiso-t3` re-score (FC-5 2035/2040 rows) to the D63/D65-B batch rather than performing it. Not in
> scope: `_AGGREGATABLE_FUELS`, any consumer refactor, the I5 invariant's own keying (route to the
> forecast desk with the guard as the fix).

---

## 3. Are they one object? NO — and the order matters

| | D87 | D88 |
|---|---|---|
| kind | pricing-coverage omission | identity defect |
| where | `ccs.py:475-476` + `evolve.py:664` (the screen's inputs) | `ccs.py:590-591` + `legacy_bins.py:269/300` + `arrays.py:3651` (the fleet's ids) |
| fires when | a clean-row dual on `gas_cc_ccs` exists (target row; MI tier) | a legacy representative converts and the zone builds gas CC later |
| committed reach | 12 policy-campaign bundles; no scored cell | 9 NEISO T3 variants incl. the registered `neiso-t3` run; ERCOT `d65br` 2030 |
| repair | fold one more leg into a `max()` | a raise and a string |

They touch different hunks of one file and are both forecast-only, zero-DOF, key-preserving — which
is why they LOOK like one card. But a merged lane would screen a pricing change and an identity
change in one arm and could not say which moved the retrofit set. **Sequence D88 first**: its guard is
a detector, and D87's NYISO screen should run with it armed, so that if folding the dual grows the
NYISO retrofit set into a later re-mint the screen says so instead of a downstream scorer.

Neither belongs to another desk. SCN §4 assigned both objects here by name; the fleet SoA builder
(D88's guard) and the CCS pricing path (D87) are the capacity-evolution seams SCN's lanes were told
to report and stop on, and this read finds nothing in them that is SPP's, the audit board's or SCN's.

## 4. Measurements this read could not make, left to the charters (no LP was spent)

1. **D87 / MISO:** whether the MI clean row's dual is non-zero in 2027–2029 in any committed MISO
   T1-F bundle. Not in the artifacts; a zero-LP `--fleet-only` replay of one MISO recipe with the
   dual logged answers it (§1.2).
2. **D88 / T1-F:** whether any evolved T1-F fleet carries a duplicate from a source OTHER than a
   CCS conversion (the census keyed on `ccs_retrofits` because that is the only re-mint path the code
   supports; the guard answers this for every future run, which is why it lands first).
3. **D88 / NEISO T3:** the decision delta from the `idx_of` correction in 2033–2050 — the screen in
   §2.6 measures it; nothing in the committed record can.

## 5. What this read touched

`docs/handoffs/DESIGN-capx-d87-d88-s19-read-2026-09-08.md` — this file. Nothing else: no `src/`,
no test, no config, no matrix shard, no registration, no result bundle.
