# FINDING — miso-126: a 250 MW combined-cycle steam turbine was never in the LP, because EIA-860's fuel code on a `CA` row describes the duct burner

**Date:** 2026-08-04 · **ISO:** MISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry:** `2026-08-04-miso-124-dualfuel-rearm` ·
**Keeper at exit:** **`2026-08-04-miso-126-steampart-b`**
(`results/calibration/miso126_steampart_B`), `NOT-YET`, sole FAIL C7 `COAL_PRB`
×3y, ledgered caveats 2/3 {C3a, C3c} — **all unchanged**.
`audit_keepers --iso MISO` 0 failures / 0 warnings.

**Prereg (pushed BEFORE any adjudicating statistic, any derive and any solve):**
`results/calibration/PREREG-miso126-cc-steam-part-capacity-2026-08-04.md`,
commit `6d936130`.
**Runs registered (rule 15):** `2026-08-04-miso-126-steampart-control` (arm A,
same-HEAD zero-delta control) and `2026-08-04-miso-126-steampart-b` (arm B, the
keeper).
**Probes:** `scripts/probes/_miso126_cc_steam_part_screen.py` (no LP),
`scripts/probes/_miso126_steam_part_ab.py` (no LP).
**Records:** `_miso126_cc_steam_part_screen.json`, `_miso126_steam_part_ab.json`.

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **KE1** | is miso-125's census reproducible? | MISO **290.4 MW** missing over exactly **[50973, 55088]**; every field of the committed R4 record reproduced | **PASS** |
| **P1** | is the capacity genuinely absent (not double-counted)? | 55088 fleet holds **515.0 MW** against an EIA-860 plant total of **765.0 MW** | **PASS** |
| **P2** | is the plant's joined heat rate already a *block* rate? | eGRID `PLNGENAN` 5,259,825 net MWh ⇒ implied CF **116.6 %** on 515.0 MW (impossible) → **78.5 %** on 765.0 MW | **PASS at 55088** |
| **P2** | …at 50973 Motiva? | present-fleet implied CF **already 80.1 %** — the denominator evidence is **absent** | **FALSIFIED → excluded** |
| **P3** | is `ST1` an HRSG on the CT exhaust, or a let-down turbine on the dark boilers? | implied generation share of its block **0.4173** vs EIA-860 **nameplate** design share **0.4307**, gap **0.0134** vs a pre-declared 0.10 band | **PASS — miso-125 §4's doubt CLOSED by measurement** |
| **P4** | does the repair perturb the measurement it depends on? | re-derive moves **exactly one cell**: `class_capacity_mw` (55088, `CC_CHP`) 350.0 → 600.0. `heat_rate`, `flag`, `basis_heat_rate`, `dark_fuel_share` byte-identical on every row | **PASS** |
| **P5** | does any other ISO move? | MISO **+1 generator**; ERCOT / CAISO / PJM / NYISO / NEISO fleets **byte-identical** | **PASS** |
| **KE3** | INERT-BY-DISPATCH? | block MC $19.67 / $17.24 / $26.49 vs MISO-East median LMP $31.39 / $27.92 / $35.44 ⇒ dispatches in **99.9 / 99.4 / 95.0 %** of hours vs a 5 % band | **LIVE — as pre-declared it would be** |
| **KE4** | INERT-BY-BINDING? | **not answerable** from committed artifacts (class-grain sidecar, no bound flag) — reported, no `I` claimed on a proxy | **honest null** |
| **K0–K7** | the A/B | **every blocking gate PASS**; K4 **LIVE** | **PASS** |
| — | the outcome | `CC_CHP` **+1,013.7 / +1,149.7 / +1,073.3 GWh**; C1 `CC_CHP` error **−1.55 → −0.53** and **−1.61 → −0.46 TWh**; nothing regresses | **`K`, promoted** |

---

## §1 — the defect: a fuel code that describes the duct burner

`market_sim.data.fleet.eia860._map_fuel_type` maps a generator to a model fuel
type from `technology` / `Energy Source 1` / `Prime Mover`, and
`config.plant_taxonomy.classify_plant` then buckets it. **Both key on the
energy-source code.**

EIA's prime mover `CA` means *the steam part of a combined cycle* — the
heat-recovery steam generator and its turbine, driven by the exhaust of the
block's combustion turbines (which report `CT`). But **EIA-860's
`Energy Source 1` on a `CA` row names the block's supplementary / duct fuel**,
not its primary energy input. So a duct-fired steam part reports an exotic code
— blast-furnace gas `BFG`, other gas `OG`, distillate `DFO` — `_map_fuel_type`
returns `None`, the row is `continue`d out of the row loop, and **its capacity
never reaches the LP at all**.

At MISO 55088 Dearborn Industrial Generation:

| gen | technology | pm | Unit Code | summer MW | ES1 | in the LP? |
|---|---|---|---|---|---|---|
| `GT 1` | NG Fired Combined Cycle | `CT` | `SINT` | 175.0 | NG | yes, `CC_CHP` |
| `GT2` | NG Fired Combined Cycle | `CT` | `SINT` | 175.0 | NG | yes, `CC_CHP` |
| `GTP1` | NG Fired Combustion Turbine | `GT` | — | 165.0 | NG | yes, `CT_CHP` |
| **`ST1`** | **Other Gases** | **`CA`** | **`SINT`** | **250.0** | **BFG** | **NO** |

The row is not an exotic process-gas machine. It shares Unit Code `SINT` with
the two gas turbines whose exhaust drives it — EIA-860's own machine-level
statement that they are one block — and it is in the processed parquet the
fleet loads, already carrying the eGRID plant heat rate its siblings carry.
The fleet build simply drops it.

## §2 — the rate was already right, and that is the whole argument

miso-125 §4 measured the consequence without naming this as its cause: eGRID's
`PLNGENAN` at 55088 is **5,259,825 net MWh**, which on the 515.0 MW the LP held
implies a **116.6 % capacity factor**. Net generation cannot exceed nameplate
hours. On the repaired 765.0 MW it is **78.5 %** — ordinary for a cogen.

That arithmetic is the evidence, and it is what property **P2** was written on:
the incumbent measured-CHP rate's **denominator already counts the missing
machine**. It was a *block* rate being charged to two thirds of the block. So
the repair adds capacity at the rate that was always meant for it, and the rate
itself does not move.

Re-deriving `chp_power_only_heat_rates_MISO.csv` on the repaired fleet confirms
it exactly (rule 23 `[R-FROZEN-DERIVE]`, cited to the fleet/denominator change
and never to a residual): **one cell moves**, `class_capacity_mw` at
(55088, `CC_CHP`) 350.0 → 600.0. `heat_rate` 6.9573, `flag` `ok`,
`basis_heat_rate`, `model_heat_rate`, `thermal_share` and `dark_fuel_share` are
byte-identical on every row of every plant, and a flag-off control re-derive
reproduces the committed artifact **byte-for-byte**.

## §3 — the lever is 250.0 MW, not the 290.4 MW that was named

miso-125 §6 named 290.4 MW over two plants. **50973 Motiva Port Arthur's
40.4 MW does not enter**, and two independent sources say so.

* **The pre-registered P2 falsifier.** 50973's present-fleet implied capacity
  factor is **80.1 %** — physically possible, so eGRID's denominator gives *no
  evidence* that the missing rows sit inside it. Stated precisely: the evidence
  is **absent, not contrary**. eGRID is plant-grain, so its denominator very
  likely does cover those rows too; what is missing is the *proof*, and the
  pre-registration admits only what is proven.
* **Vintage.** 50973's `CA` rows commissioned **1957 / 1962 / 1978** against
  `NG` `CT` siblings of **1983** and **2011**. Three steam turbines predating by
  up to 26 years every turbine that supposedly drives them is a refinery steam
  header sharing a `Unit Code` label, not a combined-cycle block.

**1004 Edwardsport is not a defect and is untouched.** It matches the predicate
(`ST` row, pm `CA`, `SGC`, Unit Code `1`, two `NG` `CT` siblings) but its
technology string carries "coal", so `_map_fuel_type` resolves it and it is
already in the fleet as `COAL` 555.0 MW. The repair only ever **restores** a row
the fuel map drops; it never reclassifies one that resolves. This is miso-125's
555 MW false positive, and it is now pinned by a unit test rather than by luck.

**A census-method correction, recorded rather than quietly applied.** miso-125's
presence test summed EIA-860 **summer** capacity against a fleet whose `pmax`
already falls back to nameplate, so at any plant with a NaN-summer row the two
sides were on different bases — which is why 1004 and 6081 came back
`UNDETERMINED` there. This session coalesces summer-else-nameplate, the fleet's
own rule, and reports both statuses. 1004 resolves `REPRESENTED`, confirmed
directly against the fleet (`1004_ST`, `COAL`, 555.0 MW). **The miso-125 record
is reproduced, not overwritten.**

## §4 — the wiring gap, and why the first answer was a lie

**The first arm-B solve came back exactly inert** — zero class-energy delta and
zero price delta *to machine precision* across all three years, for 250 MW of
capacity the screen said would dispatch in 95–99.9 % of hours. A null that
clean is not a small effect; it is a mechanism that never ran.

`scripts/run_calibration.py::run_year` does not call
`fleet.assembly.load_or_synthesize_bins` — it **inlines its own copy** of the
bin synthesis for the non-ERCOT per-plant ISOs. The flag was threaded through
every path except the one every calibration arm actually runs. The comment at
that exact call site warns about it verbatim:

> "every fleet-sourcing flag has to be forwarded HERE too, or a calibration
> solve silently ignores it while `run_config.json` records it as on
> (`measured_ct_heat_rates` was byte-identical to its control for exactly this
> reason, nyiso-89)."

A wiring test already pinned that call site — **but only for
`measured_ct_heat_rates`**, the one flag that had hit the wall. A per-flag pin
only protects the flag someone remembered to add, which is exactly why it did
not stop this one. **The durable fix is the guard, not the one-liner:** it is
now generalised to *every boolean-defaulted keyword of `load_fleet_from_csv`
that is also a `ScenarioConfig` field*, so a new fleet-sourcing flag is caught
the day it lands with nobody editing the test. It was verified to **FAIL**
against the pre-fix source and pass against the fixed one, so it is a regression
test rather than a tautology.

**The rule for successors:** prereg KE6 required firing to be proven *two* ways
— a pre-arm `load_fleet_from_csv` check **and** a post-arm class-energy delta —
and said "a null is not trusted until both fire." The loader check passed while
the LP saw nothing. **That discipline is what caught this.** A fleet-loader
check alone would have shipped a mechanism that does nothing.

## §5 — what it does

Against the same-HEAD zero-delta control, and never against the committed
predecessor (miso-124's DO-NOT-MISREAD: the price response is not stable across
keepers):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CC_CHP` energy | **+1,013.7 GWh** | **+1,149.7 GWh** | **+1,073.3 GWh** |
| displaced | CT_PEAKER −246.7, CC_REGULAR −216.5, COAL_PRB −187.6, import −185.3, ST_GAS −89.7, COAL_BIT −56.8 | CT_PEAKER −306.7, CC_REGULAR −243.6, import −226.9, COAL_PRB −201.5, ST_GAS −86.9, COAL_BIT −54.7 | CT_PEAKER −301.2, CC_REGULAR −209.7, COAL_PRB −184.9, import −181.4, COAL_BIT −110.8, ST_GAS −62.6 |
| max zonal \|ΔLMP\| | 18.578 | 1.328 | 12.267 $/MWh |
| hours with any Δ | 7,179 | 7,608 | 8,077 |
| system demand-wtd Δλ | **−0.0805** | **−0.0812** | **−0.1005** $/MWh |
| full energy-balance residual | −0.010 | +0.054 | +0.031 GWh |

Direction is **checked, not assumed**: adding deep-inframarginal capacity can
only lower or leave unchanged the clearing price, and the system
demand-weighted λ falls in every year. Unserved energy falls too (2024 slack
19.06 → 18.21 GWh).

**C1 improves materially and for the right reason.** The EIA-923 benchmark
target *always* counted `ST1`'s generation — the scorer's own bench flag reads
"55088:`CC_CHP` Dearborn (1.41×)", the same ratio miso-125 measured — so the
model was under-producing this class by exactly the missing machine:

| year | class | control | arm B | improvement |
|---|---|---|---|---|
| 2023 | `CC_CHP` | −1.55 TWh | **−0.53 TWh** | **1.02** (68 % of the class error) |
| 2024 | `CC_CHP` | −1.61 TWh | **−0.46 TWh** | **1.15** (71 %) |
| — | **summed C1 \|error\|, all scored rows** | 37.20 TWh | **35.46 TWh** | **1.74** |

Offsetting movements are small and all stay `PASS` (2023 CT_PEAKER −2.87 →
−3.11, CC_REGULAR −2.46 → −2.66; 2024 CC_REGULAR +3.06 → +2.82 and COAL_PRB
+2.00 → +1.80 both *improve*).

**C3a drifts 0.3 pp further negative** in each year (−1.1 → −1.4 %, −6.4 →
−6.6 %, −14.2 → −14.5 %) with **no status change**. It is kept: rule 14
`[R-ACCURATE]` is explicit that a worse fit from a more accurate input is a
discovered root-cause item, never grounds to bury the error back inside an
inaccurate input — and MISO's C3a under-pricing already has its own ledgered
root cause (the deterministic-LP scarcity-tail limitation), which this repair
does not touch.

**Nothing regresses.** Determination `NOT-YET`, all nine criterion statuses, the
ledgered-caveat budget {C3a, C3c} and every legitimacy-diagnostic verdict across
D-1 / D-2 / D-4 / D-5 / D-9 / D-10 are identical to the control. C7 `COAL_PRB`
remains the sole FAIL and was never offered as a target.

## §6 — a pre-registered statistic that was wrong, recorded as corrected rather than loosened

Prereg **K6 (energy conservation)** was written as "the summed **class**-energy
delta must be ~0", tolerance 0.5 GWh. **As written it fails**: +0.39 / +2.06 /
−1.31 GWh.

The defect is in the statistic's **boundary**, not in the mechanism. The class
sidecar is not the whole balance — storage charge/discharge lives in
`hourly/storage_<year>.parquet` and unserved energy in
`hourly/system_<year>.parquet`, and this lever legitimately moves both (it
displaces expensive energy, so storage cycles differently and scarcity slack
falls). On the full identity
`Δclass + Δdischarge − Δcharge + Δslack − Δdump − Δdemand` the residual is
**−0.010 / +0.054 / +0.031 GWh** on a ~650 TWh system, with Δdemand exactly 0.

This is the session's own miso-125 lesson turned on itself: **a magnitude that
violates a conservation law is a boundary defect in the statistic before it is a
result about the mechanism.** The band was not widened; the statistic was
completed, and both figures are reported.

## §7 — what shipped

* `ScenarioConfig.cc_steam_part_capacity` — default **off**, byte-identical off,
  ISO-gated on `plant_taxonomy.CC_STEAM_PART_REPAIR_ISOS = {MISO}`.
* `plant_taxonomy.classify_plant(..., cc_steam_part=...)` — the canonical
  statement of the rule, a strict widening, default-off.
* `fleet.eia860.cc_steam_part_generators` — the predicate, resolved from the raw
  EIA-860 operable sheet (the same bridge `_chp_by_plant` uses, because the
  processed parquet carries no `Unit Code`).
* `chp_power_only_heat_rates_MISO.csv` — re-derived, one descriptive cell moved.
* `scripts/run_calibration.py` — the backcast bin-synthesis forward.
* `tests/unit/data/test_cc_steam_part_capacity.py` — 15 tests, including the
  **generalised** backcast wiring guard.
* Keeper promoted; matrix row minted and cell stamped `K`.

**Zero free parameters.** Every clause of the predicate is an equality on a
published EIA-860 categorical field plus one physical inequality, and the
restored generator takes the block's existing heat rate — the mechanism
introduces no new numeric value of any kind. `n_residual` unchanged at 2.

**Known conservative limitation, named not buried.** The vintage clause also
excludes a **repowered** block (an existing steam turbine fitted with new gas
turbines and an HRSG), where the `CA` row legitimately predates its turbines.
That direction is safe — the model drops 100 % of these rows today, so the
clause can only restore fewer, never more — and it is the named successor
question. The clause itself is **declared unregistered**: it was not in the
pre-registration, it was added as an implementation device so the shipped
predicate's population equals the properties' admitted set without a per-plant
list (rule 24), it is strictly narrowing, and it changes no verdict.

## §8 — for the next session

1. **Do not re-test this cell.** `cc_steam_part_capacity` MISO is `K`. The
   population is a national census of exactly four rows and it is closed.
2. **Two ISO hand-offs stand, unstamped (rule 25).** **CAISO 54912 Martinez
   `STG1`, 20.0 MW `OG`** — `MISSING` against CAISO's fleet (80.0 held vs 100.0
   EIA-860) and vintage-coherent (`STG1` 1995 = `GTG1` 1995); it needs CAISO's
   own P1–P3 and a CAISO entry in `CC_STEAM_PART_REPAIR_ISOS`. **NEISO 6081
   Stony Brook `CA1`, 96.0 MW `DFO`** — presence still `UNDETERMINED` even on
   the basis-consistent test (fleet 435.7 vs EIA-860 446.6 incl / 350.6 excl
   `CA`); that lane must resolve presence first. Neither cell is stamped here.
3. **The repowered-block case** is the only known gap in the predicate.
4. **C7 `COAL_PRB` is untouched** and remains MISO's sole FAIL and determination
   blocker. It stays data-blocked: route (i) needs the miso-78/79 congestion +
   sub-hourly-RT lane, route (ii) has no admissible source (miso-103/104). The
   bounded next step is still the Form 580 tonnage **count** — a sourcing pass,
   not a solve.
5. **Method note worth carrying.** Two pre-registered things were wrong and both
   are recorded as wrong rather than re-narrated: the K6 statistic's boundary
   (§6) and the 290.4 MW headline (§3). Meanwhile the *one* pre-registered
   discipline that mattered most was KE6's insistence that firing be proven at
   **two** grains — it is the only reason §4's wiring gap was caught instead of
   being published as "the mechanism is inert."
