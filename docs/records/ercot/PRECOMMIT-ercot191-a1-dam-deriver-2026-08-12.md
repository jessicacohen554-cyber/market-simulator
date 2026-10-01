# PRECOMMIT — ercot-191: the signed A1 DAM-deriver lane (#9 → #8 → #10) — one precommit, one re-derive, one re-gate sweep

**Date** 2026-08-12 · **ISO** ERCOT (rule 25 `[R-ISO-SCOPE]`) · years
{2023, 2024, 2025} only (rule 22) · pushed BEFORE the re-derive and the solve
(the ERCOT-148/149 protocol). **Authority: owner signature A1, 2026-08-11**
(`docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md` card A /
RESOLUTIONS): *"authorize as ONE lane, #9 first"* — sequence #9 → #8 → #10,
one precommit, one re-derive of the DAM availability family, one re-gate
sweep of every armed DAM keeper mechanism. The rule-23 `[R-FROZEN-DERIVE]`
re-derivation citation for every artifact this lane regenerates **is the A1
signature itself** (a signed data-correctness ruling on the deriver, not a
residual move).

Basis keeper: `2026-08-11-run188-arm-topfine-cliff` (bundle
`results/calibration/ercot188_topfine_arm_B`, determination NOT-YET, fail set
{C3a-2023, C3b-2023}, C3c a ledgered caveat ×3 years, C6 ATTESTED). The two
armed DAM keeper mechanisms in its recipe are
`ercot_dam_availability_coal_event_cap=true` and
`ercot_dam_availability_gas_event_cap=true`; the DAM availability family
itself is armed as `ercot_thermal_dam_availability` +
`..._hourly` + `..._plant` (+ the coal scope via
`ercot_thermal_dam_availability_coal`, backcast-auto).

Defect record being repaired (all committed): ruling **#9** —
`docs/DIAGNOSIS-ercot149-gas-cop-window-2026-08-01.md` §3.1–3.2, §6.1–6.2
(the `_site()` cross-train collapse takes the MAX not the SUM of ON-row HSL;
name-grain OFF CC 48.9 GW vs 14.1 GW train-collapsed, card A §A; the gas
crosswalk's partial site acceptance). Ruling **#8** —
`docs/DIAGNOSIS-ercot148-coal-outage-windows-2026-07-31.md` §5.1, §6.2 (the
same-year p98 rating basis makes an all-year-OUT site vanish from both sides
of the class fraction; Martin Lake U1 2025, COP `OUT` all 8,760 h @ 815 MW).
Ruling **#10** — ercot-149 §6.3 (the pin's remove-direction over-removal at
partial-coverage plants; V H Braunig 2025, VHB3 down pins the whole plant to
~0.075 while VHB1/2's status is unmeasured by the accepted subset; **sized
small on the keeper, and the record is explicit that most of the VHB gap is
offer-economics under-dispatch — this lane does not predict a residual move
from it**).

---

## 1. The three repairs, pre-registered exactly

### 1a. #9 — `_site()` collapses to the PHYSICAL TRAIN, so class/site sums become the SUM of per-train maxes

`scripts/data/derive_ercot_thermal_dam_availability.py::_site`. The CC
resource-name grammar in the corpus is `<MNEMONIC>_<CCTAG><train#>_<config#>`
— verified pre-commit against **all 310 unique CC resource names across every
Gen_Resource file of both disclosure lanes**: every name matches
`^(?P<train>.+_(?:CC|CCU|GT|ST)\d*)_\d+$` (0 exceptions). The current code
truncates at the config TAG (`name.rfind("_CC")` → `GUADG`), so two physical
trains (`GUADG_CC1_*`, `GUADG_CC2_*`) alias onto ONE site key whose live
capability and rating are `max()` across BOTH trains — the ruling-#9 defect:
a single-train outage is arithmetically invisible (ercot-149 §3.1; GUADG
Oct–Dec 2024).

**The repair:** for CC resource types the site key becomes the TRAIN —
`match.group("train")` (`GUADG_CC1_1` → `GUADG_CC1`); the existing tag-scan
remains only as the fallback for a name the regex does not match (none in the
current corpus). Config-collapse (max across a train's own alternates) is
UNCHANGED and stays correct — alternates never run together; the cross-train
SUM the diagnosis names then happens in the existing site-summing
aggregations, which are untouched. Non-CC resource types keep the resource
name unchanged (byte-identical site keys). Ratings become per-train p98 —
the "sum of per-train maxes" arithmetic at every grain.

**Seam predictions (deriver-level, checked after the re-derive, before the
solve):** (i) CT_PEAKER and COAL and ST_GAS site keys byte-identical; their
class-day series may move ONLY through #8's fallback sites (else
byte-identical). (ii) CC class-day fractions drop on days a train of a
multi-train shared-mnemonic family (GUADG, KMCHI, AMOCOOIL, BOSQUESW, CBEC,
FORMOSA, FREC, FRNYPP, LPCCS, OECCS, QALSW, THW) is OUT while a sibling runs
— the GUADG Oct–Dec 2024 block reads a site frac near 0.5, not ≈0.97.
(iii) The CC class rating denominator RISES toward the fleet's true summed
train ratings (the 14.1 GW train-collapse under-count unwinds toward the
class's real registered capability).

### 1b. #9 (companion) — the gas crosswalk's partial site acceptance is completed

`scripts/data/build_ercot_dam_resource_crosswalk.py`. Two deterministic
completions, both evidence-gated, zero fitted parameters:

1. **Sibling completion.** After the per-site scoring pass: a rejected site
   whose TOP candidate plant already has an accepted site in the same class,
   whose corroboration is STRONG (`corr ≥ 0.85`, the existing bar,
   unchanged), and which failed ONLY the capacity band (a unit/train
   fraction below `_CAP_LO`) flips to `accepted=1` with method
   `sibling_completion` — guarded by the plant-sum band: the plant's total
   accepted `p98_rating_mw` must stay ≤ 1.30 × plant nameplate (the existing
   `_CAP_HI`, applied at plant sum). This is the ercot-149 §6.2 completion
   for **BRAUNIG_VHB1/VHB2** (0.187/0.198 < 0.30, strong `token_prefix` to
   V H Braunig), **GIDEON_GIDEONG1/G2** (0.177/0.199, Sim Gideon),
   **OLINGR_OLING_2** (0.25, Ray Olinger). No bar moves: `_STRONG`,
   `_CAP_LO`, `_CAP_HI` keep their committed values; the rule only stops the
   per-train band from vetoing a plant the scorer has already identified.
2. **A hand seed for JCKCNTY2** (Jack County train 2), which has NO lexical
   bridge (method `none`, and its auto top-candidate is the WRONG plant —
   Colorado Bend at a coincidental ratio 1.0). New reviewable seeds file
   `data/raw/reference/ercot-dam-gas-site-seeds.csv` (the ERCOT-110
   coal-seeds pattern: exact-site-keyed, separate file so the frozen
   ERCOT-71 `ercot_noncampd_dam_crosswalk.csv` scope is untouched), one row:
   `JCKCNTY2_CC1 → 55230` (Jack County). Evidence carried on the row: same
   QSE pair as JACKCNTY (`QBRAZP;QEAGL3`), settlement point `JCKCNTY2_CC1`,
   p98 rating 654.0 MW with JACKCNTY 627.0 → 1,281 MW against the EIA plant
   nameplate 1,280.0 MW (ratio 1.001), and ercot-149 §3.2's identification
   of JCKCNTY2 as Jack County's second train.

The crosswalk is rebuilt with its committed default scope (`--years 2023`),
site keys now train-grain by construction (it imports `_site` from the
deriver). The forensic STEM seeds (KMCHI, Hidalgo, AVR) are unaffected:
`_mnem_stem("KMCHI_CC1") == "KMCHI"` — the stem strips the tag either way.
Coal exact-site seeds are non-CC and byte-identical.

**Coverage predictions:** Jack County accepted rating 627 → ≈1,281 MW;
V H Braunig 400 → ≈838 MW; Sim Gideon 323 → ≈557 MW; Ray Olinger
142 → ≈249 MW; Guadalupe and Kiamichi carry BOTH trains (each train a row;
plant-summed series unchanged in rating scale but single-train outages now
visible). No previously-accepted (site → plant) pair changes plant.

### 1c. #8 — a multi-year rating fallback for all-year-OUT sites

`derive_ercot_thermal_dam_availability.py::derive_year` (restructured to
derive all requested years in one pass so ratings can cross years). A
(class, site) with NO in-year rating (no non-OUT, non-zero row all delivery
year) takes its rating from the NEAREST other derived year (tie → the
earlier year — a destroyed unit's last-operating rating is the physical
basis; ERCOT-148 §6.2's "multi-year rating fallback"). Its live series (0
under the existing OUT arithmetic) then survives the clip, and the site
enters BOTH sides of every grain: class-day/class-hour denominators and the
site-hour parquet (live 0 / rating > 0). A site with no non-OUT row in ANY
derived year remains absent (nothing measurable to rate) — recorded, not
guessed. In-year ratings are byte-identical to the current basis; the
fallback engages ONLY where the current code emits NaN.

**Named prediction:** Martin Lake U1's DAM site carries 2025 live 0 at its
2023/2024-based rating, so the COAL class-day and Martin Lake plant series
finally SEE the destroyed unit (ERCOT-148 §5.1). The
`BIN_FORCED_DERATE_BY_YEAR["N_COAL4"] = {2025: 0.67}` registry entry is
**NOT retired in this lane**: its own TO-RETIRE condition names the OUTAGE
derive (or a registry home), and the entry still guards every configuration
in which the DAM plant pin is not armed. The ERCOT-137 ceiling composition
(`min()` with the pin's target) makes the two expressions of the same
measured fact non-stacking; the finding records the residual TO-RETIRE
status.

### 1d. #10 — the pin's REMOVE direction is diluted to its measured coverage

`src/market_sim/data/outages.py::ercot_thermal_dam_availability_plant_series`
gains a companion loader returning each crosswalked plant's per-hour covered
rating MW (Σ `rating_mw` over its accepted sites with rows at that hour) —
same file read, same accepted-gate, no new artifact.
`src/market_sim/data/fleet/withholding.py::_ercot_dam_plant_hourly_apply`
then, on REMOVE hours only (`pf < cur`), pins the plant to

    pf_eff = pf · cov + cur · (1 − cov),   cov = clip(covered_rating_MW / Σ pmax(plant units), 0, 1)

i.e. the measured fraction governs exactly the share of the model plant the
accepted DAM sites measure, and the UNMEASURED remainder keeps its incumbent
availability instead of being dragged by a sibling's outage — the ruling-#10
over-removal, unwound. The RESTORE direction is untouched (its collisions
are owned by the armed ERCOT-148/149 event caps — rule 19, one mechanism per
phenomenon), and `cov = 1` reproduces the current arithmetic bit-for-bit.
The unmapped-residual accounting stays on the RAW `pf` (the ERCOT-137
precedent in the same function: a plant's unmeasured/destroyed share must
not push its removal onto other plants).

**Interaction note, stated ex ante:** after 1b completes V H Braunig /
Gideon / Olinger coverage, #10's guard binds only at plants that REMAIN
partially covered; on the keeper it is expected SMALL (the record's own
sizing), and no residual move is predicted from it.

### 1e. What is deliberately NOT touched

* The `OFF`-at-HSL convention (`Resource Status == "OUT"` is the only
  zero-contribution state) — the measured-vs-measured precedence collision
  is owned by the armed event caps (ERCOT-148 §4.1, ercot-149 §5); this lane
  does not re-legislate it.
* The event-cap mechanisms themselves (`ercot_dam_availability_*_event_cap`)
  — they stay armed exactly as in the keeper recipe and "the cap stays
  correct after it" (ercot-149 §6.1).
* `_RATING_QUANTILE` (0.98), `_STRONG` (0.85), `_CAP_LO/_CAP_HI`
  (0.30/1.30), the crosswalk's committed `--years 2023` scope, the class
  scope (`RESTYPE_TO_CLASS`), and every ScenarioConfig default — **no new
  ScenarioConfig field, no new tunable** (rule 24).
* `N_COAL4` (§1c above). The CHP exclusion. The forecast path (all touched
  code is backcast-only by mode gate).
* The ercot-170 probe's bars and tiers. One GRAIN ADAPTER only, provably
  neutral on the old artifact: `committed_pairs()` normalizes crosswalk site
  keys through the probe's own `_site_of_train` (identity on every committed
  plant-mnemonic key; collapses the new train-grain keys to the probe's site
  mnemonic). Without it the re-test would fail on a key-format mismatch
  rather than on coverage — a plumbing artifact, not a measurement.

### 1f. Committed-value re-pins that follow mechanically

`tests/unit/data/test_outages.py::ErcotThermalDamAvailabilityTest` pins
committed-artifact spot values (e.g. CC 2023-06-14 HE20 ≈ 0.834). The
re-derive changes the committed CSVs, so those pins are re-set to the NEW
derived values in the same commit as the artifacts — a rule-23 consequence
of the A1 signature, not test tuning. New unit coverage is added for the
train-grain `_site()` (the GUADG aliasing case) and the #8 fallback.

---

## 2. One re-derive, then one re-gate sweep (the A1 sequence)

1. **Re-derive the family** (single invocation, after all three code
   repairs land): `derive_ercot_thermal_dam_availability.py --years 2023
   2024 2025` (all three grains), then
   `build_ercot_dam_resource_crosswalk.py --years 2023` + the seeds file.
2. **The ercot-150 zone-anchor re-trigger** (card A §A.2 names it; the
   freeze clause at `constants.py` GAS_OFFER_MARGIN_ANCHOR_BY_ZONE conditions
   on the weights-bundle reconstruction, which reads these artifacts):
   re-run `scripts/data/derive_gas_offer_margin_anchor.py --iso ERCOT
   --by-zone --weights-bundle results/calibration/ercot149_gas_event_cap_arm`
   on the re-derived family; re-register the ERCOT table in `constants.py`
   if any value moves; re-run
   `scripts/probes/_ercot150_zonal_anchor_derivation.py` so the committed
   derivation record re-asserts the registered table. This happens BEFORE
   the re-gate solve (the keeper arms `gas_offer_margin_zonal_anchor`).
3. **One re-gate sweep** of every armed DAM keeper mechanism: replay the
   keeper recipe unchanged (`--replay-bundle
   results/calibration/ercot188_topfine_arm_B`), full span `--year 2023 2024
   2025`, years sequential (rule 12), bundle
   `results/calibration/ercot191_dam_rederive_regate`. The recipe carries
   both event caps armed; no flag is added or removed. Registered per rule
   15 (bundle + sidecar + payload + bench; keeper hourlies on promotion),
   ERCOT matrix shard cells re-stamped for the re-gated mechanisms (rule
   28b).

**Promotion is pre-registered, direction-blind:** the re-gated bundle
becomes the ERCOT keeper WHATEVER the residual does, because the incumbent
keeper's availability inputs rest on an aggregation the record already calls
wrong (rule 14 `[R-ACCURATE]` — never revert to the inaccurate input because
it fit better; rule 1 — a keeper is the most structurally faithful run). The
verdict is re-scored at full magnitude (`calibration_verdict.py`); any gate
that worsens is reported as-is and opens/keeps its root-cause item — it is
never a reason to keep the wrong derivation. Zero fitted parameters in the
whole lane ⇒ structurally LOYO-exempt (the ERCOT-145b/148/149 precedent),
with the per-year guard table below standing in.

## 3. Guards (per-year, scored on the re-gated bundle)

| guard | bar |
|---|---|
| G-SHED | no manufactured-shortage signature: unserved-hour counts stay at the keeper's 4/2/0 pattern (±0 tolerance on new nonzero-shed years) |
| G-OWNER | C3a-2024 stays PASS; C3a-2025 stays within its band (−8.0% keeper reading; band edge −10%) |
| G-C1 | every material class's annual-energy deviation stays inside the C1 band; COAL and CC_REGULAR/ST_GAS moves attributed to the three named repairs |
| G-C7 | the ercot-168 C7 lignite legs HOLD (per-year curves untouched by this lane) |
| G-C8 | forced-share budgets unmoved (no floor/commitment mechanism is touched) |
| G-C6 | governance attestation re-produced for the new bundle |

No STOP band is set on C3a/C3b/C3c themselves: the lane's object is
availability correctness (rule 14), any gate movement is UN-TARGETED (rule
1), and the promotion rule above is direction-blind. A guard breach does not
un-promote the accurate derivation; it is reported at full magnitude and
escalated to the owner with the run registered (the ercot-188/E2 posture:
verdicts are never rewritten by outcomes).

## 4. The ercot-190 checkpoint (card Q, signed 2026-08-12 — executed by this session after the re-derive)

On the repaired deriver: re-run the ercot-170 coverage-licence test
(`scripts/probes/ercot170_cc_headroom_phase0.py`), **bars unchanged: L1 ≥
0.90, L2 ≤ 0.10**, phase-0 read, NO LP. Committed baseline: L1 0.5111 / L2
0.1829, verdict FILED-UNLICENSED. The branch rule is SIGNED, not predicted:

* **PASS → (Q-A)**: phase-0 identification of the ~2.7 GW CC capability
  object is authorized (item 11 charter; ERCOT-163 constraint — a rule-14
  fleet-scope correction on the existing
  `ercot_thermal_dam_availability_*` channel ONLY, never a commitment gate /
  aggregate cap / telemetered-HSL cap). Identification only; ANY build needs
  its own sitting with the $709 tail-lw-mean reach bar and the ERCOT-159
  kill gates pre-registered.
* **FAIL → (Q-B), automatic and final**: no further ERCOT C3a-2023 spend;
  ERCOT stands at NOT-YET on it as a model-class limit. Record and stop.

The read is recorded in `docs/calibration-log/ercot.md` (entry ercot-191)
and on matrix item 11 either way. This precommit predicts NOTHING about
which branch fires.

## 5. Fences

* No other C3a-2023 work of any kind (the Q-C freeze).
* Card B's coal-limb re-adjudication is NOT touched (sequenced after this
  lane by the A1 board).
* No rubric text, no ledger entry, no holdout marker, no out-of-training
  year (rule 22: solve years ⊂ {2023, 2024, 2025}).
* No new `ScenarioConfig` field ⇒ no new matrix row (rule 28c not
  triggered); the re-gate re-stamps EXISTING ERCOT cells only (28b).
