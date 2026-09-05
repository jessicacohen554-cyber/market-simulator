# FINDING — nyiso-189 (`backcast-calibration` lane, second sitting): the owner-chosen form B2 built, A/B-solved and PROMOTED — `egrid_steam_collapse_heat_rates` puts Bethlehem 2539 at its CT-heat identity (9.665 → 6.877) and the determination holds at CALIBRATED with every regression stated

**Session:** nyiso-189 (continuation), `backcast-calibration` lane
(`claude/nyiso-189-bethlehem-heat-rate-7suj05`), 2026-09-05. **Solves run:
TWO** — the same-HEAD control on the committed artifacts
(`results/calibration/nyiso189_control`, an instrument, bit-identical to the
keeper) and the one arm (`results/calibration/nyiso189_steam_identity`,
registered `2026-09-05-nyiso-189-steam-identity`). **Keeper at entry:
`2026-09-04-nyiso-188-combined`** — CALIBRATED, grade 7, fails 0, C3c
ledgered; C3a +7.9 / +3.8 / −6.9 %; C1-2024 `CC_REGULAR` +2.05 TWh.
**Pre-registration:** `results/calibration/PREREG-nyiso189-steam-collapse-identity-ab.md`,
pushed at `a73d1df0` (now `46930e8` after the rebase) BEFORE the mechanism was
built and before any solve; every bar below is read verbatim. **Owner ruling
(this sitting, 2026-09-05, `AskUserQuestion` on the three questions of
`docs/DECISION-CARD-nyiso189-bethlehem-vintage-form-2026-09-04.md` §3):**
form **B2**, the plant's own **T1-clean median** steam share, the
plant-history bound **authorized**. **Machine records:** the bundle's computed
`calibration_attestation.json` (`scripts/gen_nyiso189_attestation.py`, every
premise computed, refuses on any failed check),
`results/calibration/_nyiso189_ab_report.json`
(`scripts/probes/nyiso189_ab_report.py`), the committed artifact
`data/raw/_processed-legacy/egrid_steam_collapse_heat_rates_NYISO.csv`
(`scripts/data/derive_egrid_steam_collapse_heat_rates.py --check` reproduces).

---

## 1. The result in one paragraph

The owner chose form B2 and the lane built it as ONE new `ScenarioConfig`
field, `egrid_steam_collapse_heat_rates` (default off, matrix row + six shard
cells in the same PR), consuming a per-ISO artifact the derive writes over
every NYISO combined cycle with a filed steam generator. At the applied eGRID
2023 vintage the population rule admits EXACTLY the two plants the
pre-registration named — Bethlehem 2539 (fence: steam share 0.065 against its
own 2018–2022 record [0.492, 0.519]; heat per CT-MWh 10.30 inside the record;
`PLHTRT` 9.665 → identity **6.877**) and World Generation X 54131 (T1: the
steam generator at zero while the CT runs; 9.807 → **6.996**) — and declines
Flynn / Ravenswood / Lederle on a one-member record. The arm moves Bethlehem
INTO merit in Capital-Hudson (loading of available 0.35 → 0.70 / 0.62 → 0.89
/ 0.61 → 0.87; +2.45 / +1.78 / +1.71 TWh), the load-weighted price falls
−2.8 / −2.0 / −1.5 % in every year, and the determination holds at
**CALIBRATED, grade 7, fails 0, C3c ledgered** with **no rejection-rule flip**.
Gains: C3a-2023 +7.9 → **+4.9 %**, C3a-2024 +3.8 → **+1.7 %**, C3b-2023 0.134 →
0.119, C3b-2024 0.175 → 0.166, C1-2023 `ST_GAS` +2.97 → +1.92 TWh, C8
`CC_REGULAR` 5.0 / 2.8 / 2.7 → 2.7 / 0.9 / 1.2 %. Regressions, every one in
band and stated: **C1-2024 `CC_REGULAR` +2.05 → +3.33 TWh / +1.8 → +2.8 pp
against the 3.0 pp band** (0.2 pp of margin), **C3a-2025 −6.9 → −8.3 %**
(against −10 %), C3b-2025 0.171 → 0.177, C8 `ST_GAS` 17.2 / 22.3 / 17.3 →
19.7 / 23.6 / 18.3 %. Under the owner's standing-disposition formula
(re-delivered this sitting, verbatim: *"Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates
regress that may still be a keeper.."*) the arm is a **recommended keeper
candidate and is PROMOTED**: a zero-parameter repair of a measured input
whose defect three independent bases established before any residual was
read (rule 14 `[R-ACCURATE]` + rule 13 `[R-MEASURED]` + rule 1
`[R-STRUCT]`). No marker is requested.

---

## 2. What was built (the owner's form, operationalized)

### 2.1 The rule, and why it is not the literal wording

The owner authorized *"a vintage whose filed ST/CT lies below the plant's
own minimum over its T1-clean vintages is inadmissible"*. Evaluated over the
census's 38 plants × 7 vintages BEFORE any solve (PREREG §0): with the
vintage under test INSIDE its own T1-clean set the bound never fires for a
T1-clean vintage (it reduces to B1 and misses Bethlehem 2023, the card's
stated reach); with it EXCLUDED — the card's own arithmetic, "0.065 <
0.49" — the minimum-share vintage of EVERY plant is below the others'
minimum: it fires at 35 of 38 plants and, at the applied vintage, at
Bethlehem plus three noise minima (Indeck Corinth 0.573 vs [0.573, 0.573],
Sterling 0.413 vs [0.413, 0.414], Saranac 0.471 vs [0.479, 0.546]). A rule
that fires at every plant is not a test. **The operational form, fixed in
the pre-registration:** a vintage is inadmissible when its steam share lies
below the record's minimum **by more than the record's own range**
(`ST/CT(v) < min(R) − (max(R) − min(R))`, `R` = the plant's T1-clean vintages
other than `v`). The unit is the plant's own observed variability; no
external constant enters. Over the census it fires at six plant-vintages
(Bethlehem 2023, Castleton 2019, Bethpage 2022, Cornell 2024, Batavia 2022,
Caithness 2018) and at the applied vintage at exactly one. Both readings are
written per row (`below_ref_min`, `below_ref_fence`); the mechanism reads the
fence.

### 2.2 The CT-side guard and the two-member record

The identity holds only where the CT generators' filing is intact: the heat
per CT-generator MWh must lie inside the record's `[min, max]`. Where a
filing moved the steam output INTO the CT row instead — Richard M Flynn
7314: 12.74 per CT-MWh with the steam filed in 2018, 8.34–8.70 with it at
zero in 2019–2024, `PLHTRT` flat at 8.3–8.7 in both regimes — the plant
already carries its block rate and the identity would be wrong (5.69). The
guard, plus the definitional two-member record (`|R| ≥ 2`: two points define
a range), declines Flynn, Ravenswood (mixed-family, `egrid_family_heat_rates`
K covers it) and Lederle at every vintage.

### 2.3 The artifact, at the applied vintage

| plant | class / zone | admitted by | `R` | ref ST/CT [min, max], median | ST/CT 2023 | heat / CT-MWh (ref range) | `PLHTRT` → identity |
|---|---|---|---|---|---|---|---|
| Bethlehem 2539 | `CC_REGULAR`, Capital-Hudson, 862 MW installed | fence (0.065 < 0.465) | 2018–2022 | [0.492, 0.519], 0.4973 | 0.0655 | 10.298 ([10.26, 12.55]) | **9.6651 → 6.8773** |
| World Generation X 54131 | `CC_CHP`, 56 MW | T1 | 2018–2022, 2024 | [0.370, 0.418], 0.4018 | 0.000 | 9.807 ([9.73, 12.33]) | **9.8065 → 6.9955** |

Record-only rows (written, never read — the join is 2023 for every backcast
year): Bethlehem 2024 (T1 → 6.984); Bethpage 2022 (fence; identity 15.73 —
a real steam-share swing at a plant whose heat per CT-MWh is 21 that year,
non-physical as a block rate and a caution that the fence at a small cogen
can fire on a genuine operating change, not only a filing gap); Cornell 2024
(fence → 4.14). Neither is the applied vintage. The stated sensitivity
(PREREG §3, no solve): had the mechanism read the literal LOO-min, the three
extra 2023 admissions would have moved Indeck Corinth 7.654 → 7.654, Sterling
8.558 → 8.572 and Saranac 10.111 → 9.838 — where the filing is intact the
identity reproduces `PLHTRT`, which is why the two readings differ only at
the noise minima.

### 2.4 Rule 19 — what already priced the two plants

Nothing else reaches either: Bethlehem has CEMS (the identity mechanism is
CAMPD-less-only), is single-family (the family mechanism is multi-family-
only), `PLHTRT` < 11.5 (the boundary repair needs > 11.5 + a co-located
sibling), and NYISO is not in `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`; World
Generation X's `measured_chp_heat_rates` row carries `flag =
above_physical_band` and is not applied. The new apply sits at the identity
seam of `load_fleet_from_csv`, after `measured_chp` / identity, skipping any
generator those repriced and any family-covered plant. G-INPUTS (computed):
exactly six generators repriced, four at 2539 and two at 54131, off-fleet
byte-identical.

---

## 3. The A/B, at full magnitude

**G-CONTROL (computed):** the same-HEAD control is BIT-IDENTICAL to the
keeper — 0 of 52,560 hourly zonal prices differ in each of 2023 / 2024 /
2025 (max |Δ| 0.0), through eleven lane merges since the keeper's basis. The
keeper is the baseline. **G-DELTA:** exactly
`{egrid_steam_collapse_heat_rates: false → true}`. **G-DOF:** zero new
entries (13 / 6 verbatim). **G-ENGAGE:** Bethlehem's mean installed `mc`
falls and its energy rises in every year (below).

### 3.1 What the flag did (P1 unit-hourly and system hourlies, control → arm)

| year | Bethlehem TWh (of available) | loading | mean installed `mc` $/MWh | committed-tranche `mc` | World Gen X TWh | load-weighted price | Capital-Hudson price | price hours differing (of 52,560), max \|Δ\| |
|---|---|---|---|---|---|---|---|---|
| 2023 | 2.448 → **4.898** (6.997) | 0.35 → 0.70 | 51.78 → 39.78 (−11.99) | 44.92 → 30.83 | 0.077 → 0.134 | 34.81 → **33.84** (−2.8 %) | 38.41 → 37.13 | 46,887, $9.28 |
| 2024 | 4.171 → **5.951** (6.680) | 0.62 → 0.89 | 46.12 → 35.56 (−10.56) | — | 0.241 → 0.292 | 39.56 → **38.76** (−2.0 %) | 40.36 → 39.50 | 46,192, $20.15 |
| 2025 | 4.110 → **5.815** (6.701) | 0.61 → 0.87 | 69.46 → 52.30 (−17.16) | — | 0.301 → 0.321 | 61.84 → **60.88** (−1.5 %) | 63.93 → 62.87 | 45,211, $30.13 |

The `mc` moves by more than fuel × ΔHR (≈ $7–10) because the tranche offer's
markup is heat-rate-scaled (`offer_markup_hr`): the committed tranche falls
$14.09 and the economic tranches $9.0–9.2 in 2023. Bethlehem's 2023 loading
of 0.70 against a measured online share of 0.94 (nyiso-186 §5.3) and the
+2.45 TWh against the −2.28 TWh EIA-923 deficit that section recorded on the
understated filing basis: the block is now in the merit position its
physical heat rate puts it in. Every NYISO zone's price falls (Upstate West
−$0.41 / −$0.71 / −$0.82; NYC −$1.30 / −$0.86 / −$1.03); the C3c hour counts
are unchanged (5 / 0 / 16 model hours > $300, scorer 3 / 0 / 4 RT-comparable).

**Where the energy comes from — NOT the class alone.** The pre-registered
expectation that the class total stays pinned is FALSIFIED at the class
grain: `CC_REGULAR` rises 32.01 → 34.01 / 36.11 → 37.39 / 34.02 → 35.22 TWh,
i.e. about 80 % / 72 % / 70 % of Bethlehem's gain is a class gain and the
rest a within-class displacement. The plant movers (TWh): 2023 Ravenswood
−0.565, Arthur Kill (`ST_GAS`) −0.391, East River (`ST_CHP`) −0.373, Empire
(`CC_CHP`) −0.308, Cricket Valley −0.153; 2024 Empire −0.284, Brooklyn Navy
Yard (`CC_CHP`) −0.225, East River −0.209, Cricket Valley −0.168, Athens
−0.116; 2025 East River −0.275, Empire −0.272, Athens −0.172, Cricket Valley
−0.125, Arthur Kill −0.104. Classes: `ST_GAS` −1.05 / −0.30 / −0.30, `CC_CHP`
−0.50 / −0.71 / −0.52, `CT_CHP` −0.30 / −0.11 / −0.18, `ST_CHP` −0.09 / −0.11
/ −0.10, `CT_PEAKER` −0.03 / −0.01 / −0.06. The gas family is pinned; the
family's cheapest 750 MW now sits in Capital-Hudson and displaces the NYC
steam and cogen blocks first.

### 3.2 Criteria (scorer, committed artifacts only; `nyiso188_verdict_compare.py`)

| criterion | keeper | arm |
|---|---|---|
| C1 2023 `CC_REGULAR` / `CC_CHP` / `ST_GAS` / `CT_PEAKER` | −1.00 / +1.20 / +2.97 / −1.65 TWh PASS | **+1.00 / +0.70 / +1.92 / −1.68** PASS |
| **C1 2024 `CC_REGULAR`** | +2.05 TWh, +1.8 pp PASS | **+3.33 TWh, +2.8 pp PASS** (band ±3.82 TWh / 3.0 pp — 0.2 pp of margin) |
| C1 2024 `CC_CHP` / `ST_GAS` / `CT_PEAKER` | +2.54 / −0.32 / −1.58 | +1.82 / −0.62 / −1.59 |
| C2 | PASS | PASS (all classes in band) |
| C3a 2023 / 2024 / **2025** | +7.9 / +3.8 / −6.9 % PASS | **+4.9 / +1.7 / −8.3 %** PASS (band ±10 %) |
| C3b NRMSE 2023 / 2024 / 2025 | 0.134 / 0.175 / 0.171 PASS | **0.119 / 0.166 / 0.177** PASS |
| C3c (RT hours > $300) | 3 / 0 / 4 vs 10 / 13 / 42 CAVEAT | 3 / 0 / 4 — CAVEAT (lone, rubric v3.3 standing rule) |
| C4 gas r / NRMSE | 0.94 / 0.126; 0.902 / 0.131; 0.84 / 0.188 | 0.94 / 0.126; 0.90 / 0.132; 0.838 / 0.189 |
| C6 | PASS (attested) | PASS (attested, computed premises) |
| C8 `CC_REGULAR` D-2 | 5.0 / 2.8 / 2.7 % | **2.7 / 0.9 / 1.2 %** |
| C8 `ST_GAS` D-2 | 17.2 / 22.3 / 17.3 % | 19.7 / 23.6 / 18.3 % (budget 30 %) |
| D-4 | `passed: false`, the rider rows (2480 / 2500 / 2511 …) | the same rider rows, slightly larger floored TWh at Arthur Kill / Ravenswood as the NYC steam is displaced |
| **determination** | **CALIBRATED, grade 7, fails 0, C3c ledgered** | **CALIBRATED, grade 7, fails 0, C3c ledgered** |

**Verdict under PREREG §3 (verbatim):** no criterion flips PASS → FAIL; the
arm is a **KEEPER CANDIDATE**. **Every regression, stated:** C1-2024
`CC_REGULAR` +2.05 → +3.33 TWh / +2.8 pp — the nyiso-187 §2 disposition
(the within-gas-family fill of the CT / steam deficits the market ran
out-of-market, cell G) at a LARGER magnitude, because the class now also
carries Bethlehem's real 1.8 TWh while the NYC steam it displaces is what
the market committed anyway; C3a-2025 −6.9 → −8.3 % (the 2025 offer-level
remainder, DECISION-CARD-nyiso148 Q1, owner-court, grows by the cheaper
750 MW); C3b-2025 0.171 → 0.177; C8 `ST_GAS` +2.5 / +1.3 / +1.0 pp. **LOYO**
reduces to the per-year record: the same sign in every year for every moved
quantity (Bethlehem +2.45 / +1.78 / +1.71; price −2.8 / −2.0 / −1.5 %; class
+2.0 / +1.3 / +1.2), no fitted scalar, largest in 2023 where the block was
furthest out of merit. Rule 1 reading: the mechanism repairs a measured
input whose defect was established on eGRID's own GEN sheet and two
independent bases before any residual was read; that C3a improves in two
years and worsens in the third is reported, not the reason for anything.

---

## 4. Promotion

Under the owner's standing formula the recommendation is **promote**, and
it is executed in this PR: `frontend/data/backcast/keepers/NYISO.json`
(keeper → `2026-09-05-nyiso-189-steam-identity`, promotion and determination
notes, the nyiso-188 keeper into the `superseded` chain);
`scripts/build_status.py --iso NYISO`; `scripts/audit_keepers.py --iso NYISO`
(PASS); the forecast gate-(a) stamp re-keyed in the same PR (README step 4 /
R-T; `check_gate_a_provenance.py --iso NYISO` OK — the leg still reads FAIL
on its marker condition: NYISO holds no `complete` marker; D56 is issued and
not landed, so no D-5(b) re-key applies); the NYISO matrix shard (keeper +
gates re-stamped; `egrid_steam_collapse_heat_rates` O → K); the §5.5 header
and queue; `docs/calibration-log/nyiso.md`. The determination is NOT worse
than the superseded keeper's (CALIBRATED → CALIBRATED). **If D56 lands
before this PR merges, the merging session re-keys `complete.NYISO` to this
keeper with a re-verified determination (rule 22 D-5(b)) — flagged for the
owner.**

---

## 5. What this session does NOT claim, and what it hands forward

### 5.1 Not claimed

* Nothing on the 2024 `CC_REGULAR` disposition (nyiso-187 §2, cell G) is
  re-opened; its magnitude grows for a stated reason and the cell is 0.2 pp
  inside its band — the closest cell to failing on this keeper.
* No price claim: C3a-2023 / 2024 improve and 2025 worsens; the 2025 remainder
  stays DECISION-CARD-nyiso148 Q1.
* The fence is the lane's operationalization of the owner's bound; the owner
  may overturn it. The literal reading's extra reach is quantified (§2.3) and
  is nil where the filing is intact.

### 5.2 Handed forward (the §5.5 queue, in order)

1. **C1-2024 `CC_REGULAR` at +3.33 TWh / +2.8 pp** is now the keeper's
   closest cell to a band edge (3.0 pp). Its owner is unchanged (nyiso-187
   §2: out-of-market commitment of the CT / steam deficit classes, G + the
   accepted CT markup trade); any further in-merit CC repair will push it
   over the band unless the out-of-market half is represented. A lane that
   wants that cell needs the owner to re-open G — not a CC lever.
2. **C3a-2025 −8.3 %** — DECISION-CARD-nyiso148 Q1 (the 2025 offer-level
   remainder) remains the owner's; it is now ~1.4 pp larger.
3. **The forecast lane:** `egrid_steam_collapse_heat_rates` regenerates per
   eGRID vintage; a forecast-mode fleet load reads the same applied-vintage
   artifact. When the 2025 eGRID vintage lands, re-derive and re-check the
   applied vintage's admissions (rule 23: a source-data change).
4. **Bethpage 50292 (2022) and Cornell 50368 (2024)** fire the fence at
   non-applied vintages with non-physical identities (15.7; 4.1): the fence
   can catch a genuine operating change at a small cogen. Record only today;
   if a future applied vintage admits such a row, the CT-side guard alone
   will not stop it — a second source-internal check (e.g. the identity
   inside the class physical band, as `measured_chp_heat_rates` already
   applies) would be the rule-24 route.
5. Unchanged: Zeltmann's 2024 cold-weather record vs the pooled p99.9 cap
   (recorded, not a lever); the v2 artifact's frozen 2018 / 2022 / 2026
   rows; NYISO parasitic factors absent; the Astoria merit-panel
   stack-duplicate defect (nyiso-184 §4.1); the D-2 / C8 grain under-count
   escalation (nyiso-181 §6).

## 6. Governance

Rule 1: nothing adopted or rejected on a residual; the bars were pushed
before the build and read verbatim. Rules 5 / 21 / 23: zero parameters
(the fence unit and the guard are the plant's own range; the two-member
minimum is definitional; the applied vintage is the join's own), zero new
DOF entries; the derive re-derives on an eGRID or EIA-860 change only.
Rule 13: the CT-heat identity regenerates from any eGRID vintage and
responds to changed conditions. Rule 14: the license — an accurate
representation of a measured quantity replaces a filing artifact. Rule 15:
the arm is registered with its computed attestation; the bit-identical
control's slim files are committed as the instrument. Rules 16 / 12: one
invocation per bundle, years sequential, two concurrent invocations. Rule
19: one measured rate per plant (skip sets computed at the seam). Rule 22:
2023–2025 only; no marker requested; the D56 interaction flagged. Rule 24:
a population rule over the ISO's 38 CCs; no plant named in code. Rules 25 /
28: NYISO shard only beyond the six `U` cell lines; the base row + every
shard cell in the same PR (`check_mechanism_matrix.py` clean). Rule 27:
on-disk bytes pushed; every ≥300-line blob verified after each push.
