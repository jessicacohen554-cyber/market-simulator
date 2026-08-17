# ASSESSMENT — nyiso-142: is NYISO ready to declare `final`?

**Session:** nyiso-142, 2026-08-17 · **Branch:** `claude/nyiso-142-astoria-rates-iwljui`
**Keeper:** `2026-08-16-nyiso-140-layup-exclusion` · **Markers:** `complete` HELD (2026-07-31,
re-keyed 2026-08-16), `final` EMPTY · **Freeze:** `holdout-freeze.json` ACTIVE.
**No out-of-training year was solved, scored or registered in this session.** Everything below
is read from committed artifacts, on-disk input coverage, and published actuals. The only
solves this session runs are in-sample (2023/2024/2025), for the pre-registered Astoria A/B.

---

## 0. Recommendation

> ### DO NOT DECLARE `final`. NYISO is **NOT READY**, on both locked-test years, for four independent reasons.
>
> 1. **Neither year can be built on the frozen keeper config.** The keeper arms
>    `nyiso_dynamic_reserve_requirements=True`, which hard-requires
>    `NYISO_reserve_requirements_<y>.csv`. That file exists on disk for **2022–2025 only**, and
>    the loader **raises rather than falling back** — *"the flag must not solve on the static
>    requirements it claims to replace."* For **2019** no covering LRR version exists; for
>    **H1-2026** the published schedule has a genuine **gap** (v2021 ends 2026-02-14, v2026
>    starts 2026-07-10), so closing it requires an adjudicated mid-year splice — a *methodology
>    decision about the frozen config's inputs*, taken after the config was selected. That is
>    precisely the thing a touch-once test cannot absorb. **H1-2026 fails even earlier than
>    that:** `load_demand` raises (*"No EIA-930 data for ISO 'NYISO' in year 2026"*), so the LP's
>    demand array cannot be built and the year is **unsolvable**, not merely unscoreable.
> 2. **2019's fleet is not representable.** Indian Point 2 and 3 (~2,060 MW of downstate
>    Zone-H nuclear, **17.4 TWh in 2019 — 11 % of NYISO load**) are absent from *every*
>    `eia860_generator*.parquet` in the repo, and the fleet builder reads the 2025-operable
>    snapshot. A 2019 solve is short that energy with no way to restore it. `constants.py`
>    already says so in its own words: *"A 2018-2021 solve is short that capacity regardless of
>    this overlay."*
> 3. **2019 cannot exercise the criterion NYISO is caveated on.** The real market had exactly
>    **one** RT hour over $300 in 2019 (max $372.38). C3c — the sole ledgered caveat, and the
>    binding limitation of the five-zone representation — would score a trivial small-count
>    result whatever the model did. (NEISO precedent: `ASSESSMENT-neiso87-…` §3, zero hours.)
> 4. **The measuring instrument just changed and the keeper has not been re-scored on it.**
>    nyiso-141 proved the 2025 ST_GAS benchmark was inflated by ≈1.31 TWh. Every NYISO run ever
>    scored on 2025 — this keeper included — was selected against that inflated target. Spending
>    the one-shot now would test a frozen config *selected on the old instrument* against years
>    *scored on the new one*. §6 answers the prompt's question: **yes, re-score first.**
>
> Separately: the **holdout spend freeze is ACTIVE and outranks both marker blocks**, so a
> `final` grant would be unspendable today in any case. Nothing here is urgent; everything here
> is worth fixing before it becomes urgent.

| question | verdict |
|---|---|
| Is NYISO's locked test spent or ungranted? | **UNGRANTED** — and the record already says so correctly at HEAD (§1). No governance correction is needed, unlike the NEISO case. |
| Could 2019 be solved on the frozen config? | **NO** — reserve requirements absent; fleet short 17.4 TWh of nuclear (§2). |
| Could H1-2026 be solved on the frozen config? | **NO — and it is the harder of the two.** `load_demand` raises: no EIA-930 rows for 2026, so the LP cannot be built at all. Plus the reserve-requirement gap, no 2026 import-ladder row, and two partial-year overlays (§3, §3b). |
| Would either year discriminate on C3c? | **2019 no** (1 actual hour). **H1-2026 yes, strongly** (85 hours in 4,343) — so it is the year worth **preserving**, even though it is the year that cannot be solved today (§4). |
| Does the nyiso-141 benchmark change argue for re-scoring first? | **YES — and this session did it.** The keeper re-scores on the corrected instrument with its determination and every criterion status **unchanged**, so that objection is now closed; the other three blockers stand (§6). |

---

## 1. The governance precondition is already correct — nothing to repair

The NEISO assessment (neiso-87 §1) had to begin by correcting a false "SPENT" claim. **NYISO
has no such defect.** Read at HEAD:

| artifact | what it says |
|---|---|
| `calibration-complete.json` → `complete.NYISO.locked_test` | *"NOT AUTHORIZED. NYISO is absent from `final` and has never scored 2019 or H1-2026. Granting it is a separate owner decision."* |
| `calibration-complete.json` → `final._note` | block is `{"_note": …}` only — **no ISO is listed** |
| `complete.NYISO.redeclaration` | *"The withdrawn marker's own note confirms the locked test was NEVER spent — and it is still not granted here."* |
| `bench/NYISO/` | `2023.json.gz`, `2024.json.gz`, `2025.json.gz` — **no out-of-training bench of any kind** |
| `actual_tail.json` → `isos.NYISO` | 2020, 2021, 2022, 2023, 2024, 2025 — **no 2019 row and no 2026 row** |

So the question in front of the owner is stated correctly already: *should a never-granted
one-shot be granted now?* §§2–6 answer it on the merits.

## 2. 2019 — two hard blockers

### 2.1 The frozen config cannot be built: reserve requirements are absent

The keeper carries `nyiso_dynamic_reserve_requirements = True` (`meta.json`). The register
(`docs/holdout-data-equivalency-register-2026-07.md` §NYISO) grades this input **MISSING** for
2018–2021 and states the mechanism: the published LRR-schedule clean source carries three
versions — `v2020` (2020-10-29 → 2021-12-04), `v2021` (2021-12-04 → 2026-02-14), `v2026`
(2026-07-10 → open) — and *"no single version fully covers 2018, 2019, 2020, or 2021"*. Verified
on disk this session:

```
data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_{2022,2023,2024,2025}.csv
```

Four files. **2019 is not one of them**, and the deriver
(`derive_nyiso_reserve_requirements_hourly.py`) refuses rather than fabricate a
mid-version treatment — correctly, under rule 14 `[R-ACCURATE]`.

**There is no fallback.** `model/reserves/spec.py:2829` states it in its own
words: the series is *"a backcast-only record (**the loader hard-errors on a
missing year rather than reverting to the static requirements it replaces**, so
there is no forward fallback to key to)"*. So this is not a degradation to be
graded — with the flag armed, the year does not build.

### 2.2 The 2019 fleet is not representable — Indian Point

This is the larger of the two, and it is **already documented in the code**.
`src/market_sim/config/constants.py` (NYISO nuclear monthly-CF block):

> *"the model's NYISO nuclear fleet is the current 4-reactor EIA-860 snapshot. Indian Point 2
> (retired Apr 2020) and 3 (retired Apr 2021) actually ran in 2018-2021 but are absent from that
> snapshot… **A 2018-2021 solve is short that capacity regardless of this overlay**."*

Confirmed independently this session:

| check | result |
|---|---|
| `eia860_generator_operable.parquet`, NY nuclear | **4 units**: Nine Mile 1 (641.8 MW), Nine Mile 2 (1,259.3), FitzPatrick (883.3), Ginna (614.0) |
| `eia860_generator_retired_and_canceled.parquet`, NY nuclear | **0 rows** |
| `eia860_generator_retired_within_window.parquet`, NY | 16 rows, **0 nuclear**, no Indian Point |
| any `eia860_generator*.parquet` matching "Indian Point" | **none** |
| fleet builder source | `eia860_generator_operable.parquet` (`fleet/eia860.py:1217`), `EIA860_OPERABLE_VINTAGE = 2025` |

The magnitude, from NYISO's own published fuel mix (`data/raw/NYISO/fuel-mix/`, TWh):

| fuel_category | 2019 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| **Nuclear** | **44.78** | 27.57 | 27.14 | 28.49 |
| Hydro | 29.24 | 27.18 | 26.98 | 24.25 |
| Natural Gas | 23.76 | 29.10 | 32.29 | 33.41 |
| Dual Fuel | 27.89 | 34.07 | 35.31 | 36.67 |
| Wind | 4.47 | 4.68 | 6.12 | 7.12 |

The model's four upstate units at ~92 % CF give ≈27.4 TWh — which is exactly the 2023–2025
actual. **The 2019 gap is therefore the whole of Indian Point: 17.4 TWh, 11 % of NYISO load,
must-run, downstate.** A 2019 solve would have to fill it from gas, and C1 (nuclear + every gas
class), C2 and C3a would all miss for a *data-representation* reason with no calibration content
whatever. Under rule 22's own instruction — *"grade against regime drift, not raw MAE"* — this
is not a hard case: the drift is not a nuance to grade around, it is 11 % of the year's energy
that the model cannot put on the system at all.

## 3. H1-2026 — three blockers, none of them the model

| input | status for H1-2026 | source |
|---|---|---|
| `NYISO_reserve_requirements_2026.csv` (hard-required by the armed `nyiso_dynamic_reserve_requirements`) | **MISSING — published-schedule GAP.** `v2021` ends 2026-02-14, `v2026` starts 2026-07-10; H1 straddles both. Closing it is *"an explicit, adjudicated mid-year-version-splice… a genuine methodology decision"* | register §NYISO; verified on disk |
| `IMPORT_TRANCHES_BY_YEAR["NYISO"]` (keeper arms `nyiso_firm_imports`, `nyiso_import_hub_prices`) | **MISSING 2026** — ladder covers 2018–2025 only (verified this session by import) | `config/interchange_config.py` |
| NYISO nuclear monthly CF | **deliberately ABSENT for 2026** — *"EIA-923 carries only Jan-Apr 2026 (zeros May onward), so a 2026 anchor would post a false zero for H1's May-Jun"* | `constants.py` |
| `plant_emission_rates_v2` NYISO 2026 | **DEGRADED — Q1-only measured rate** (heat/mass ratios over Jan–Mar operating hours only) | register §NYISO |
| `gas_basis_by_iso_month.csv` NYISO 2026 | **DEGRADED** — still on the old EIA-citygate-proxy construction, not the in-sample Iroquois Z2 construction the tuned years use | register §NYISO |
| `actual_lmp_hourly_NYISO` 2026 | **EQUIVALENT-partial** — 4,343 of 8,760 hours (H1 only), by construction | verified this session |

The first three are hard: two inputs the armed config requires do not exist, and the third is a
measured overlay its own producer refuses to emit. **And the audit in §3b finds a fourth, larger
one: `load_demand` RAISES for 2026 — there are no EIA-930 NYISO rows for the year, so the LP's
demand array cannot be constructed at all. H1-2026 is not merely unscoreable at HEAD; it is
unsolvable**, the same hard blocker NEISO's 2019 carried (neiso-87 §0).

Note the shape of the H1-2026 problem — it is **publication horizon**, not data quality. It
closes on its own with time, unlike §2.2.

## 3b. The full input-preparedness audit

`scripts/probes/_nyiso142_final_prereq_audit.py` walks every input the keeper's
armed recipe resolves, for both locked-test years, with **2023 as a control** —
the column that proves the probe itself works rather than merely reporting
absence. Raw output: `results/calibration/_nyiso142_prereq_audit.json`.

**Control 2023: 0 blocked or degraded of 18. 2019: 9. H1-2026: 10.**

| input | 2019 | H1-2026 | 2023 (control) |
|---|:--:|:--:|:--:|
| `load_demand` (the LP demand array) | OK | **ERR** *no EIA-930 rows* | OK |
| `backcast_config` (the recipe, built) | OK | **ERR** *KeyError 2026* | OK |
| `henry_hub_actual` | OK | **ERR** | OK |
| `load_nyiso_reserve_requirements` | **ERR** | **ERR** | OK |
| nuclear fleet vs published actual (regime drift) | **GAP** *+17.39 TWh short* | OK | OK *+0.18* |
| EIA-860 restorability of pre-vintage retirees | **GAP** | OK | OK |
| `calibration_reference.json` (C1/C2 target) | **GAP** | **GAP** | OK |
| `actual_tail.json` (C3c benchmark) | **GAP** | **GAP** | OK |
| `NYISO_<y>_renewable_capacity.csv` | **GAP** | **GAP** | OK |
| `nyiso_market_solar` (keeper arms the COD basis) | **GAP** | **GAP** | OK |
| EIA-930 `NYIS_fueltype` / `NYIS_region` | **GAP** | **GAP** | OK |
| `actual_lmp_hourly_NYISO`, hydro budget, gas basis, outages, emission rates v2, interface flows | OK | OK | OK |

Two rows deserve quoting because they are the difference between "degraded" and
"does not run":

* **`load_nyiso_reserve_requirements`, both years** — the loader's own message:
  *"`nyiso_dynamic_reserve_requirements=True` but the measured requirement series
  is absent … the flag must not solve on the static requirements it claims to
  replace."*
* **`load_demand`, H1-2026** — *"No EIA-930 data for ISO 'NYISO' in year 2026."*
  The LP's demand array cannot be constructed at all.

And the regime-drift row calibrates itself: the same measurement reads
**+0.18 TWh** on the control year and **+17.39 TWh** on 2019.

## 4. Discrimination — can either year test what NYISO is actually caveated on?

NYISO's determination is CALIBRATED-WITH-CAVEATS with **C3c the lone ledgered caveat** (re-verified
this session: `calibration_verdict.py --run-id 2026-08-16-nyiso-140-layup-exclusion` →
CALIBRATED-WITH-CAVEATS, C1/C2/C3a/C3b/C4/C6/C8 PASS). So the value of a locked-test year is
mostly the value of the C3c evidence it can carry.

From `actual_lmp_hourly_NYISO.parquet` — **an actuals property; no model output is involved on
either side, so this is not a score** (same disclosure neiso-87 §3 made):

| year | mean RT | max RT | **RT hours > $300** | tier |
|---|---:|---:|---:|---|
| **2019** | **$24.96** | $372.38 | **1** | locked test |
| 2020 | $19.41 | $343.40 | 1 | validation |
| 2021 | $37.04 | $583.61 | 3 | validation |
| 2022 | $74.74 | $2,943.95 | 101 | validation |
| 2023 | $30.28 | $1,174.88 | 10 | train |
| 2024 | $35.97 | $1,064.38 | 13 | train |
| 2025 | $60.72 | $1,981.72 | 42 | train |
| **H1-2026** | **$71.75** | $1,899.65 | **85** *(in 4,343 covered h)* | locked test |

**2019 is the least discriminating year in the entire record.** One scarcity hour cannot
distinguish a model that reproduces NYISO's tail formation from one that does not; the criterion
would return a small-count result that is uninformative in both directions. Spending the
single most irreversible resource in the policy on it would be a waste even if §2 were closed.

**H1-2026 is the opposite** — 85 hours in half a year is the richest tail density in the record,
and it sits on the *same* fleet regime as the training window. If NYISO's locked test is ever
granted, **H1-2026 is the year with the evidentiary value; 2019 is not.**

Note the resulting asymmetry, which is the single most useful thing in this assessment: **the
year that could discriminate cannot be solved, and the year that could be solved cannot
discriminate.** 2019's blockers are *substantive* — a fleet that no longer exists in any source
the repo holds, and a market that never went scarce. H1-2026's are *temporal* — EIA-930 rows,
an LRR schedule version and a Gold Book that have not been published yet. Time fixes the second
list and does not touch the first. That is an argument for **preserving H1-2026 carefully** and
for treating 2019, if it is ever used at all, as a validation-tier diagnostic rather than the
one-shot.

## 5. Regime drift, stated as rule 22 asks

Rule 22: *"Pre-2020 years exercise a structurally different fleet — grade against regime drift,
not raw MAE."* For NYISO the drift is unusually sharp and unusually one-directional:

* **Nuclear −16.3 TWh (−36 %) 2019 → 2025**, entirely the Indian Point retirements (2020-04,
  2021-04), and entirely **downstate**.
* **Gas + dual-fuel +18.4 TWh (+36 %)** over the same span — the gas fleet backfilled the
  nuclear loss almost exactly 1:1. Total in-state generation is nearly flat (132.9 → 133.2 TWh).
* **Wind +59 %** (4.47 → 7.12 TWh); market solar is essentially nil in 2019 and is a *keeper
  mechanism* today (`nyiso_solar_market_generator_basis`, plus the registry-COD basis promoted
  at nyiso-133).
* **The NYSDEC peaker rule** (`nysdec_peaker_rule_availability`, armed) has compliance dates in
  2023 and 2025. It is not a 2019 phenomenon at all.
* **Price level**: 2019 mean RT $24.96 against $30–61 in the tuned years — the cheapest year in
  the record.

Three of the keeper's armed mechanisms are therefore either inapplicable to 2019 (peaker rule,
market-solar basis) or exercise a fleet that no longer exists (downstate nuclear). This is not a
model that would be *tested* by 2019; it is a model that would be *misapplied* to it. And note
the direction: the 2019 → 2025 substitution of gas for downstate nuclear is the same object as
the open ST_GAS successor (§ the nyiso-141 finding §1) — 2019 sits on the far side of exactly
the transition the model does not yet reproduce.

## 6. The prompt's question — does the nyiso-141 benchmark change argue for re-scoring the keeper before any `final` grant?

**Yes, and it is the cheapest of the four blockers to close.**

nyiso-141 established (three independent channels, no residual) that Astoria files one
generator's output on two CEMS rows, and that `_backfill_eia923_with_campd` put the doubled
number into the **2025** ST_GAS benchmark — 2.672 TWh where the corrected series gives 1.359, so
the scored 2025 ST_GAS actual of 16.003 TWh is overstated by ≈1.31 TWh. 2023 and 2024 used
metered EIA-923 and do not move.

The consequence is a **change to the measuring instrument, not to the model**, and that is
exactly why it matters here:

1. **Every NYISO keeper in the current lineage was selected against the inflated 2025 target.**
   That includes `2026-08-16-nyiso-140-layup-exclusion` and every A/B that promoted its way to
   it. Model selection is what the training window is *for*, so this is not a scandal — but it
   does mean the frozen config was chosen with one criterion mis-levelled.
2. **The locked-test protocol freezes the config, not the instrument.** If the one-shot were
   spent after the correction lands, 2019/H1-2026 would be scored on the corrected instrument
   while the config under test was selected on the uncorrected one. The resulting number is
   still *out-of-sample*, but it is no longer a clean measurement of the thing the policy exists
   to measure, and — because the tier is touch-once — the ambiguity could never be resolved
   afterwards.
3. **The remedy is entirely in-training and costs nothing irreversible.** Re-solve the keeper
   recipe on 2023–2025 against the corrected intake, re-score, and confirm the determination
   holds. That is the A/B this session executes under
   `PREREG-nyiso141-astoria-stack-duplication-2026-08-17.md`. If the determination holds, the
   instrument question is closed and the record says so explicitly; if it does not, the owner
   learns that *before* spending the one-shot rather than after.

This is the same logic the owner already applied to NEISO on 2026-08-06: a validation touchpoint
scored against a defective fuel input *"is not interpretable as forecast error"*, so the year was
re-spent on the repaired input — and the reason that was affordable is that 2022 is **iterable**.
2019 and H1-2026 are **not**. The asymmetry argues for closing instrument defects *before* the
touch-once tier is opened, not after.

**One honest qualification against my own recommendation.** The 2025 correction moves the
benchmark by ≈1.2 TWh on one class in one year, and the keeper's C1/C2 both PASS with margin
today; it was unlikely that the determination would turn on it. So this is a **sequencing**
argument, not a claim that the keeper is wrong: the re-score is cheap, in-training, already
pre-registered and already done; there is no reason to spend an irreversible year ahead of it.

**RESOLVED IN THIS SESSION, and it resolves in the keeper's favour.** The A/B landed while this
assessment was being written, and the keeper re-scores on the corrected instrument with **its
determination and every criterion status unchanged** — CALIBRATED-WITH-CAVEATS, C1/C2/C3a/C3b/C4/C6/C8
PASS, C3c the lone ledgered caveat (`build_status.py --iso NYISO` moves only its `generated`
timestamp). What the corrected instrument changes is the *reported residual*, and in the
keeper's favour on both classes it touches:

| keeper `2026-08-16-nyiso-140-layup-exclusion`, 2025 | error vs old benchmark | vs corrected |
|---|---:|---:|
| ST_GAS | −3.737 | **−2.533** |
| CC_REGULAR | +2.877 | **+2.091** |

2023 and 2024 are unchanged to the digit. **So the instrument objection to a `final` grant is
now closed** — it was worth closing before spending an irreversible year, and it cost one
in-training A/B rather than a locked-test one-shot. The other three blockers (§§2–4) stand
entirely unaffected, and they are the ones that decide the recommendation.

## 7. What would have to be true before `final` is worth putting to the owner

In dependency order, cheapest first:

1. **Re-score the keeper on the corrected 2025 benchmark** (this session's A/B). *In-training,
   already under way.*
2. **Lift the holdout spend freeze**, or grant a narrow single-purpose lift. Owner action; its
   standing basis (the CAMPD economic-layup residual) is separate from anything here.
3. **Close the H1-2026 reserve-requirement gap** by an explicit, adjudicated mid-year LRR splice
   — a methodology decision, and one that should be taken and *frozen into the config* before,
   not after, any grant. Add the 2026 import-ladder row (blocked on PJM/NEISO LMP-bench
   extension — cross-ISO, not fixable from this lane).
4. **For 2019 only:** restore Indian Point to the fleet. This is a real intake task (EIA-860
   historical vintages or eGRID2019, which does carry it), not a flag — and until it is done,
   2019 measures a fleet that never existed. **Note that rule 22's data-prep clause makes this
   unrestricted work today:** *"WHAT IS HELD OUT IS THE SCORE, NEVER THE DATA."* Nothing stops
   a future session from preparing it; only looking at the answer is gated.
5. **Then, and only then**, decide the grant — and if it is granted, my recommendation is that
   **H1-2026 carries it and 2019 does not**, on §4's discrimination evidence. 2019 would be
   better spent, if ever, as a *validation-tier* diagnostic under the `complete` marker's
   touchpoint loop, where a miss can send you back to re-train — which is the only use a
   non-discriminating, structurally-alien year can honestly serve.

## 7b. A note on this session's own touching of quarantined-year rows

The Astoria repair rewrote `plant_emission_rates_v2` rows for **every** year the
artifact carries — 2018 through 2026, the quarantined 2022 and 2026 included.
That is not a holdout spend and needs no marker. Rule 22 as rewritten
2026-08-06 is explicit: *"an input is either the best measured representation of
a physical/market quantity or it is not, and if it is, it belongs in **every**
year"*, and *"Data intake needs NO per-ISO/per-window authorization and no
marker."* The gated act is looking at an answer — solving, scoring or
registering an out-of-training year — and none of that happened. The
`--holdout-intake` one-shot guard is likewise untouched: that path *adds*
quarantined rows and may run once; this repair *corrects rows already present*,
by a route that asserts every non-Astoria row byte-frozen.

The practical benefit is exactly the one rule 22 describes: if a locked test is
ever granted, its inputs are already configured identically to the training
years, with nothing left to prepare.

## 8. What this assessment does NOT do

It does not solve, score or register 2019 or H1-2026; it does not touch `final`,
`calibration-complete.json` or `holdout-freeze.json` — editing a locked-tier marker is an owner
act. It does not re-open the frontier question (cleared 2026-08-06) or the `complete` marker
(held, re-keyed 2026-08-16). And it does not claim the keeper is defective: §6 is a sequencing
argument about an instrument, and the keeper re-verifies **CALIBRATED-WITH-CAVEATS with C3c the
lone ledgered caveat** at HEAD, on committed artifacts, with no solve.
