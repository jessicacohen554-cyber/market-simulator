# MISO run-66 dashboard triage — Phase A diagnosis + design (Fable → Opus)

**Date:** 2026-07-15. **Session:** `claude/miso-run66-triage-ysywto` (Phase A —
diagnosis/design; Phase B executes from this document, the same Fable→Opus
split that produced miso-66 from `miso-coal-conduct-design-2026-07.md`).
**Trigger:** three owner-spotted issues on the live MISO run-66 dashboard:
(1) the Run Explorer's 22 TWh total-generation gap / missing CHP rows,
(2) the ST_GAS under-run (esp. 2024/2025), (3) the July-2025 LMP spike the
model doesn't form. Every number below is live-scored
(`calibration_verdict.py 2026-07-14-miso-66-coalconduct --json`, this
session), recomputed from the committed payload/bench files, or read from a
no-LP fleet reconstruction of the keeper's own `meta.json`
(`run_year(fleet_only=True)` with the full `coal_prb_sigmoid_overrides`
stack mapped — the lane-3 method). Nothing is fit to a residual; no solve
was registered (rule 16 — Phase A produces no keepers).

**Keeper verification (do first in Phase B too):** MISO keeper =
`2026-07-14-miso-66-coalconduct` (keepers.json @ `825ea75`), determination
**NOT-YET**, fail set **{fuelmix, price_mean, price_tail}**, C1 15/16 (sole
FAIL: ST_GAS-2024 −9.13), C3a PASS/PASS/FAIL (−0.9% / −7.1% / **−13.7%**),
C3b PASS ×3 (0.081 / 0.118 / **0.187** — 0.013 from the ≤0.20 gate), C3c
PASS/FAIL/FAIL (0h vs 1h · 4h vs 24h · **0h vs 38h** DA >$200; RT
diagnostic 30/37/88), C8 PASS ×3 (ST_GAS forced share 13.3/15.4/26.7%,
below the 30% cap). DOF 19/2. If the keeper moved, STOP and reconcile with
`docs/calibration-log.md`.

**Classification summary:**

| issue | classification | one-line root cause |
|---|---|---|
| 1 — 22 TWh gap / CHP rows | **(A) dashboard display fix — no solve** | header compares a 930-load-pinned model total to a 923-survey actual total; the gap **is** the EIA-923↔930 cross-survey wedge (+24.6/+20.5/+5.0 TWh), not under-generation; CHP is in BOTH totals and merely display-folded |
| 2 — ST_GAS under-run | **(B) model mechanism** (+ one small deriver-scope limb, pre-declared) | the VLR floor holds the P5-of-online LSL (~15–20% of nameplate) while measured committed operation is p25 30–49%/median 40–67%; offers sit $28–41 (outliers $118–128) above local LMP so dispatch parks AT the floor |
| 3 — July-2025 LMP | **(B)**, sequenced | July gap is ~all missing **North-up separation** (model July zonal spread $0.55 at ~$41.4 vs actual North $58.8/South ~$37); levers = Issue-2's S→N pull + the lane-2 max-gen event registry (intake); the RDC scarcity machinery is ALREADY in-LP and re-reads after those |

---

## Issue 1 — the 22 TWh total-generation gap. **(A) code fix, no solve.**

### What the header actually computes

`docs/codebase-site/backcast-runs.html::genMixTable` builds both totals over
the SAME key set (`FG = Object.keys(bench.classFull)`):

- line 1524: `aGen = Σ classFull[g]` — the EIA-923 grid-delivered survey
  total (923 − BTM, VRE on the 930 grid basis, prelim vintage reconciled);
- line 1525: `mGen = Σ gmModel[g]` over those same keys — the grid-LP class
  totals;
- lines 1544-45 print them side-by-side:
  `"<label> generation ${mGen} TWh · actual ${aGen} TWh"`.

**Both sums include the CHP classes.** `gmModel` carries CC_CHP/CT_CHP/
ST_CHP (2023: 29.50/10.77/0.51) and so does `classFull` (28.04/13.70/4.49);
`CHP_MERGE` (line 119) folds them into their parents at lines 1534-41 for
DISPLAY ONLY — identically on both columns, after the totals are taken. The
owner's hypothesis (actual counts CHP, model doesn't) is **refuted by direct
recomputation**: summing the committed payload/bench files reproduces the
header exactly — 2023 mGen = 605.6, aGen = 627.6.

### Where the 22 TWh actually comes from — the cross-survey wedge

The model's supply is pinned to EIA-930 demand by LP construction; the
actual column is the EIA-923 plant survey. Those two bases do not reconcile,
and the header gap is exactly that wedge (recomputed from the committed
payload + bench, this session):

| year | load (930) | mGen | mImp | mSup−load | aGen | aImp | **aSup−load (wedge)** | header gap (aGen−mGen) |
|---|---|---|---|---|---|---|---|---|
| 2023 | 641.0 | 605.6 | 36.2 | **+0.8** | 627.6 | 37.9 | **+24.6** | +22.0 |
| 2024 | 644.6 | 626.2 | 19.3 | **+0.9** | 642.1 | 23.1 | **+20.5** | +15.9 |
| 2025 | 663.8 | 650.5 | 14.2 | **+0.9** | 649.8 | 19.0 | **+5.0** | −0.7 |

Identity: header gap ≡ wedge − (mSup−load) − (aImp−mImp); it closes to
±0.1 TWh every year. The model balances load to +0.8/+0.9/+0.9 (storage
round-trip + dump — the footnote at lines 1573-74 already says this); the
923-survey total over-covers the same load by up to +24.6. **A perfect
model could never close the header gap**: matching aGen with imports at
actuals would over-supply the 930 load by ~24 TWh (the LP would have to
dump it). Corollary worth a display footnote: Σ(per-class model−actual)
over classFull keys ≡ −wedge + small terms, so in 2023/24 roughly −22/−16
TWh of aggregate class deficit is *forced by the data bases* and gets
distributed across the C1 rows; per-class deltas are honest, the TOTAL is
not a model-quality number. The 2025 "gap" of −0.7 is equally artifactual —
the prelim-923 vintage happens to carry a small wedge — so the header swings
+22.0 → −0.7 across years purely on survey vintage.

**The scorer is NOT affected.** `calibration_verdict._gen_totals`
(scripts/calibration_verdict.py:632-653) mirrors the same construction, but
C1 gates per-class TWh (vs each class's own measured actual) and shares
normalized per side (model share of mGen vs actual share of aGen), so the
wedge cancels where it matters. No scorer change; no re-solve; no bundle
regen.

### The fix (exact, verifiable without a solve)

All in `docs/codebase-site/backcast-runs.html`:

1. **Header like-for-like annotation (lines 1543-45).** Keep both numbers,
   label the bases, and surface the wedge the code already computes for the
   reconciliation rows: e.g.
   `"<label> generation 605.6 TWh (balances EIA-930 load) · actual 627.6 TWh
   (EIA-923 grid-delivered; +24.6 TWh cross-survey wedge vs the 930 load
   basis — see reconciliation rows; the scored C1 test is the per-class
   deltas, not this total)"`. The wedge is `aSup − load`, already available
   as `dA` at line 1571 — hoist it above the header string.
2. **Un-fold the CHP rows (lines 119, 1534-41, 1551-60)** so every scored C1
   record is visible as its own row. The scored records gate CC_CHP /
   ST_CHP (and CC_CHP is essentially matched: model 29.5/28.6/28.4 vs actual
   28.0/27.9/24.1), but the folded table hides that — which is precisely
   what misled the owner into reading the header gap as missing CHP.
   Recommended shape: keep the parent fold rows, add indented `↳ of which
   CHP` sub-rows for both columns (or drop the fold entirely); requirement:
   table rows ↔ scored C1 records 1:1.
3. **Verification (no solve):** decode
   `frontend/data/backcast/runs/2026-07-14-miso-66-coalconduct.js` +
   `frontend/data/backcast/bench/MISO/<yr>.json.gz` and reproduce the table
   above; then confirm the rendered header shows the same numbers with the
   wedge annotation. (The payload/bench math in this section is the test.)

### The ST_CHP flag (found here, adjudicated: report-only)

ST_CHP is a real per-class miss — model 0.51/0.58/0.40 vs actual
4.49/4.72/3.29 — but it is **trivial-class**: ~0.5-0.7% of ISO load (well
under the 2% C8 materiality line), C1-**PASS** every year (−3.98/−4.14/−2.89
inside ±8), C8-exempt. CT_CHP is the same pattern (−2.93/−2.77 then +2.62 in
2025). Both belong to the CHP host-load representation
(`chp_steam_following`), not to Issue 2's VLR lane (different driver:
industrial host steam, not grid reliability). Per rule 20's materiality
carve-out, these are reported by the diagnostics but never gated — do NOT
open a structural lane for them; note them in the Issue-1 display fix's
commit message so the deficit is on the record.

---

## Issue 2 — ST_GAS under-runs. **(B) model mechanism — the VLR/steam lane.**

### The residual, restated two-sided (scored basis)

| year | model | actual | Δ | status | note |
|---|---|---|---|---|---|
| 2023 | 7.50 | 13.94 | −6.44 | PASS (1.56 from −8 edge) | |
| 2024 | 8.43 | 17.57 | **−9.13** | **FAIL** (sole C1 fail; band ±8.00) | needs ≥ +1.2 TWh, target mid-band |
| 2025 | 6.62 | 14.86 | −8.24 | prelim-923 | actual is vintage-reconciled up from 12.90 raw |

The actual tracks gas price inversely (13.94 → 17.55 → 12.90 raw across
$2.54/$2.19/$3.52) — real steamers ran MOST in the cheap-gas year; the model
misses worst exactly there. Any fix must move 2024 up ≥1.2 TWh (ideally
+4-6, mid-band) while not overshooting 2023 (headroom to the +8 edge is
huge — model is 6.4 under) and while holding the C3b-2025 ≤0.20 shape guard.

### Per-plant decomposition of the 2024 FAIL (scored basis)

Scored-basis actual per plant recomputed this session from relabelled
EIA-923 restricted to the MISO registry (`bin_assignments_MISO.csv`); model
from the committed payload. The −9.13 decomposes:

| plant | zone | model | actual | Δ | tranche-artifact row? |
|---|---|---|---|---|---|
| Harding Street (990, AES/IPL) | Indiana | 1.12 | 3.22 | **−2.11** | Y (committed 15.4%, online_frac 0.974) |
| Sabine (3459, Entergy TX) | South | 2.55 | 4.22 | **−1.67** | Y (20.2%, 0.853) |
| Brame Energy Center (6190) gas-steam | South | 0.00 | 1.10 | **−1.10** | **N — secondary group** |
| Big Cajun 2 (6055) gas-steam | South | 0.13 | 0.85 | **−0.72** | **N — secondary group** |
| Lewis Creek (3457, Entergy TX) | South | 1.59 | 2.24 | −0.65 | Y (21.2%, 0.875) |
| Little Gypsy (1402, Entergy LA) | South | 0.63 | 1.27 | −0.64 | Y (10.9%, 0.508) |
| R D Green (6639, Big Rivers) | Indiana | 0.23 | 0.68 | −0.45 | Y |
| Gerald Andrus (8054, Entergy MS) | South | 0.06 | 0.39 | −0.33 | Y |
| Lake Catherine (170, Entergy AR) | South | 0.01 | 0.30 | −0.29 | Y |
| Waterford 1&2 (8056, Entergy LA) | South | 0.05 | 0.32 | −0.27 | Y |
| Elm Road (56068) gas co-fire | East | 0.00 | 0.84 | −0.84 | model-binned COAL (basis asymmetry) |
| rest (Ames, Laskin, Karn, Greenwood, …) | — | — | — | ≈ −0.1 | mostly small |

Notes on basis: **Nine Mile Point (1403) is a `mixed_fossil_plants` plant
every year** (fleet.py:5841-5868) — its ST_GAS rows relabel to OTHER_FOSSIL
*symmetrically* on both sides, so the flagship VLR unit (synchronized 98.2%
of all hours; the floor's largest leg, 3.46 TWh forced in 2024) is invisible
to the scored ST_GAS record. Not a bias — but it means the floor's biggest
contribution never helps this C1 row. **Elm Road et al.** are the opposite
asymmetry: EIA-923 gas-fired rows at model-binned COAL plants (2024 co-fire
at $2.19 gas) appear in the scored ST_GAS actual but the model can produce
them only as COAL — a scorer-basis artifact worth ~−0.84 in 2024 (~−0.1
other years). Report-only; do not build a mechanism for it.

### Root cause (three quantified components)

**(a) The floor's LEVEL is the LSL, and the offers price the rest out of
merit — the dominant piece (≈ −5 to −6 TWh in 2024).**
`st_gas_mustrun_per_plant` (scenarios.py:4146-4169; applied at
fleet.py:2014-2060) holds each gate-armed plant's *committed tranche* on in
its top-`online_frac` system-load hours. The committed tranche is
`committed_pct` from `thermal_tranches_MISO.csv`, and the deriver defines it
as **the P5 of available-CF over online hours — "min stable load when
online"** (derive_thermal_tranches.py:497-500), i.e. an LSL: Sabine 20.2%,
Harding Street 15.4%, Little Gypsy 10.9%. Measured committed operation is
far higher — the SAME artifact's `p25_cf`/`median_cf` columns read Sabine
32.9/60.2, Harding Street 36.7/61.8, Lewis Creek 28.4/67.0. D-2 confirms the
floor forces only **2.42/2.88/3.96 TWh** (13.3/15.4/26.7% of the raw-klass
class total), and the no-LP reconstruction of the keeper's own offer stack
(2024) shows why nothing runs above it: committed/econ offers are Sabine
$31.09-34.81, Harding Street $34.99-39.25, Little Gypsy $40.77 flat,
Greenwood $35.72, Big Cajun 2 $40.76, Brame $37.45, and the small-volume
F923 outliers **Gerald Andrus $127.73 / Lake Catherine $118.41** (their own
filed delivered gas ≈ $10/MMBtu) — against a 2024 model LMP mean of $29.99.
The plants sit AT the floor (e.g. Sabine dispatch 2.55 vs floor 0.95 + free
committed slivers; Harding Street 1.12 vs floor 0.60). Reality ran them at
30-60% CF *despite* local LMP at/below their SRMC — the SOM-documented
out-of-market VLR dispatch (Amite South / DSG / WOTAB), energy that is
definitionally not recoverable through offer prices. The F923 delivered
prices are the accurate measured input and STAY (rule 15); the missing
structure is the commitment/dispatch level, not the fuel price.

**(b) Fleet scope: secondary-group plants carry no floor (≈ −1.8 TWh in
2024).** derive_thermal_tranches.py:437-440 skips any (plant, group) where
the group is not the plant's PRIMARY group, because facility-summed CAMPD
net "cannot be separated from CEMS". Brame and Big Cajun 2 are
primary-COAL, so their gas-steam halves (model-binned ST_GAS, offers
$37-41) have no artifact row → no floor → model ≈ 0 vs actual 1.95 combined
(2024). The facility-net limitation is stale: the repo now carries
unit-level CAMPD (`campd-unit-level/`, the basis the lane-3 finding used
for unit-fuel splits), so secondary-group rows are derivable with the same
frozen estimator.

**(c) Scorer-basis asymmetries (report-only, ≈ −0.9 TWh in 2024):** the
Elm-Road co-fire rows (above) plus the Nine-Mile relabel. Neither is a
mechanism target.

### Rule-19 enumeration (everything that already floors/prices MISO ST_GAS)

| mechanism | state in miso-66 | phenomenon |
|---|---|---|
| `st_gas_mustrun_per_plant` (MECH_ST_GAS_MUSTRUN_PER_PLANT) | ON | VLR/self-commitment state: committed tranche (P5-online LSL) held on in top-`online_frac` load hours; D-4 window h0-23 declared, 0% off-window, D-1 r 0.976-0.983 PASS |
| `reliability_floor` ST_GAS limbs | ON | 0.12-0.15 TWh/yr — marginal |
| F923 per-plant fuel (`gas_plant_monthly_fuel_pricing`) + `nearby_fuel_price_fallback` + `class_aware_fuel_price_fallback` + `miso_zonal_gas_basis` (+0.343 South committed basis) + `gas_daily_shape` | ON | measured delivered-fuel offer basis (rule 15 — keep) |
| tranche offer curve: `gas_st_committed_hr_mult` 1.32 / `gas_st_econ_hr_mult` 0.97, `st_gas_intermediate_split` @ CF 50, `gas_st_startup_cost` + `tranche_startup_amortization` | ON | part-load/startup cost structure |
| `gas_st_wefor_base_override` 0.1 + unit-outage overlays (std + short) | ON | availability |
| `gas_st_drag_*` coefficients | params present, MISO gate not armed | (PJM/ERCOT lane) |
| `chp_steam_following` | ON | ST_CHP/CC_CHP host floors — different class, different driver |

The self-commitment phenomenon is carried once (the floor). What is wrong
is its **level source** (P5-online = LSL) — the fix REPLACES that level for
gate-armed plants, it does not stack a second floor.

### The design (frozen for Phase B)

**Mechanism: `st_gas_mustrun_p25_level`** (ScenarioConfig bool, tier 3,
default **off** — every existing keeper byte-identical; MISO backcast arms
it alongside `st_gas_mustrun_per_plant`).

> When ON, the `st_gas_mustrun_per_plant` floor level for each gate-armed
> ST_GAS plant becomes `p25_cf × nameplate × availability` (the plant's own
> measured 25th-percentile available-CF over online hours, pooled 2023-25 —
> the **existing, committed** `p25_cf` column of
> `thermal_tranches_<ISO>.csv`; no deriver touch, rule 23 clean), in the
> SAME top-`online_frac` system-load window, clipped to pmax×availability
> as today. Where the level exceeds the committed tranche, the floor is
> distributed cheapest-first across the plant's tranches (the CT-floor
> distribution precedent in the same fleet.py block, lines 2061-2103).
> Mechanism id unchanged (MECH_ST_GAS_MUSTRUN_PER_PLANT) — same driver,
> same window, same D-2/D-4 attribution; only the level source changes.

Rule-12 triple (inherited and restated): **driver** = MISO SOM-documented
out-of-market VLR commitments in MISO-South (Amite South/DSG/WOTAB) plus
the plants' own CEMS synchronization traces (Nine Mile 98.2%, Harding
Street 97.4%, Lewis Creek 87.5%, Sabine 85.3% of ALL hours);
**window** = each plant's measured `online_frac` placed in top system-load
hours (self-limiting: Gerald Andrus, online 13.7%, floors only its
top-load sliver — its $128 fuel never sets a price); **forward story** =
`p25_cf` re-derives from each new multi-year CAMPD vintage exactly like the
P5 and `online_frac` (a measured input conditioned on operation, the
rule-13 family the forecast emission rates established; a retired or
deregulated plant exits the artifact).

Why the level and not the offers (adjudicated):

- **Offer-side "warm/make-whole" exemption — REJECTED as primary.** Removing
  startup amortization/part-load penalty moves offers by single dollars;
  Little Gypsy ($40.77), Andrus ($127.73) and Lake Catherine ($118.41) stay
  far out of merit at ANY defensible adder removal, yet ran 0.3-1.3 TWh/yr.
  Their energy is measured out-of-merit dispatch — a commitment-level fact.
- **Gas take-or-pay committed discount (the miso-66 coal pattern) —
  REJECTED on physics.** Coal Schedule-5 take-or-pay makes the committed
  band's fuel sunk; gas commodity is not take-or-pay (the sunk piece is
  pipeline reservation, which F923 delivered prices blend in a way
  Schedule-5 does not isolate). A (1−share)×fuel discount on a $10/MMBtu
  filer would fabricate ~2 TWh at Andrus alone against an actual of 0.39.
- **Re-deriving `committed_pct` upward — REJECTED** (rule 23: the estimator
  is frozen and no source data changed; and P5-online genuinely IS the LSL —
  the number is right, it is the wrong quantity for the dispatch level).

**Pre-declared fallback V2b (engage ONLY if the probe leaves ST_GAS-2024
out of band — the miso-66 V1a→V1b discipline):** extend
`derive_thermal_tranches.py` with a `--secondary-groups` mode that emits
rows for non-primary thermal groups at multi-group facilities using
unit-level CAMPD unit-fuel attribution (the lane-3 measurement basis),
leaving every existing row byte-identical — the short-windows-companion
precedent (a new artifact limb from the same frozen estimator, enabled by
unit-level source data the facility-net method predated; cite this in the
commit per rule 23). That arms Brame + Big Cajun 2 gas-steam (+≈1.8 TWh
2024 headroom). Do NOT build it preemptively.

### Admissibility (rules 13/15/17/18/19/22/23/25)

- **Rule 13:** `p25_cf` is produced by the frozen estimator from CAMPD
  per-plant history conditioned on operation; regenerates each vintage;
  responds to changed conditions (plant exits, availability changes flow
  through the clip). No outcome is pinned: the floor is a level in a
  measured window, dispatch above it stays free, and the class lands BELOW
  actual even at the floor's ceiling (see expected deltas — the forcing
  moves toward, never past, the measurement; the nyiso-53 rule-1 test).
- **Rule 15:** the measured F923 fuel outliers STAY; the fix does not touch
  any fuel input.
- **Rules 17/18:** window + driver + forward story stated above; binding
  concentrates in each plant's own measured online window (D-4 h0-23 row
  already declared for this mechanism id, off-window 0.0% all years today —
  regenerate the bundle's `legitimacy_diagnostics.json` in Phase B so the
  D-4 row reflects the new level).
- **Rule 19:** replaces the level of the existing floor; no new floor id;
  nothing stacks.
- **Rule 22:** probes on 2023/2024/2025 only (MISO has no
  calibration-complete marker — nothing touches 2022/2019/≤2021/H1-2026).
- **Rule 23:** no deriver touch in the primary design (the column exists);
  V2b's deriver extension is additive-rows-only with the trigger and
  citation pre-declared here.
- **Rule 25:** the boolean is ISO-generic, default-off everywhere; arming
  evidence is MISO's own SOM + MISO CAMPD. No tuned curve crosses an ISO.
- **C8 / rubric v2.2 — the expected budget path:** forced share will rise
  well past the 30% cap (floor ceiling ≈ 9.6 TWh on a ~11-13 TWh class).
  That is the **grounded-above-budget** lane: mechanism has a declared D-4
  window (have) and D-1 must clear (`profile_r` 0.976-0.983 today;
  cv_ratio 1.38-1.71 — adding a flat measured base LOWERS model off-peak CV
  toward actual, helping the ratio). NYISO ST_GAS is the exact precedent
  (g05 memo + addendum: a real 24h reliability base, forced ≥60%, clean
  PASS surfaced as a report note). Verify D-1 from the regenerated
  diagnostics before promoting.
- **DOF ledger:** +1 measured-physical entry (CAMPD p25-of-online committed
  dispatch level; zero fitted scalars) → expected **20 measured / 2 legacy**.
- **Rule 20 (as amended 2026-07-14): NO zero-forcing ablation twin** —
  forcing-legitimacy rests on the DOF ledger + `legitimacy_diagnostics.json`
  (D-2/D-4) alone. Do not build or register a twin.

### Expected scored deltas (verify in Phase B; probe decides)

- Floor-energy ceiling at P25 level, ex-Nine-Mile (scored-class-relevant):
  ≈ **9.6 TWh** (vs 2.9 today). Expected scored ST_GAS: 2024 **−9.13 →
  ≈ −3.5..−5.5 PASS**; 2023 −6.44 → ≈ −3..−4.5 PASS; 2025 −8.24 → ≈ −4..−5
  (prelim). **C1 → 16/16 expected; fail set sheds `fuelmix`.**
- C2-2025 gas −8.0% → ≈ −4..−5% (toward the commercial band).
- OTHER_FOSSIL watch: Nine Mile's floor rises ~3.5 → ~6 TWh → OTHER_FOSSIL
  2024 ≈ +1..+2 vs actual 9.42 (band ±8 — fine, but read it).
- Prices: floored South steam is inframarginal (weakly lowers South duals)
  BUT raises S→N corridor flow toward the measured 919 binding hours → the
  North (where the scored load-weight sits) separates UP — the miso-60
  expected direction ("2025 RDT direction toward S→N-dominant, separation
  toward the IMM's $9.31, C3a-2025 toward zero"). Net C3a-2025 expected UP
  (from −13.7%); C3a-2024 (−7.1%, ±10 band) and the 2023/24 RDT anchors
  (S→N mean-flow ~1.55 GW, separation-when-binding ~$2.5-2.9) must hold.
- **C3b-2025 is the veto gate: 0.187 vs ≤0.20.** Read it mechanism-only
  (probe minus same-box base replica — the miso-66 drift lesson: a raw
  probe-vs-registered comparison once mis-read +0.018 of solver-box drift
  as mechanism).
- C5a: more gas steam displaces some coal/CT → 2024 CO2 (−3% est. after
  miso-66) drifts down — watch the ±7% band; 2025 (+0.9%) gains headroom.

### Phase B checklist (Issue 2)

1. Implement `st_gas_mustrun_p25_level` (scenarios.py tier-3 + registry
   entry; fleet.py level swap + cheapest-first tranche distribution;
   docstring carries the rule-12 triple). Unit tests: level swap on/off
   byte-identity, clip at pmax×availability, tranche distribution.
2. Probe `scripts/probes/_miso67_stgas_vlr_level.py` on the
   `_miso66_coalconduct.py` pattern (miso-66 meta strict RENAME/SKIP replay
   + the new flag via `prb_overrides`), **all three years, one bundle**,
   plus a same-box base replica for drift control. Rule 16: throwaway.
3. Read: ST_GAS/OTHER_FOSSIL C1 rows, C2-2025 gas, C3a/C3b (mechanism-only),
   RDT anchors, D-1/D-2/D-4 from regenerated diagnostics. Fallback V2b only
   on the pre-declared trigger.
4. If promoted → miso-67 candidate: full bundle → DOF ledger 20/2 →
   attestation → `legitimacy_diagnostics` (regenerate; D-4 row + C8
   grounded path) → `dashboard_add_run` BEFORE `calibration_verdict
   --write-metrics` → sidecar market_story → parity → calibration-log →
   push via `mcp__github__push_files`. **No ablation twin.** Registration
   with a recommendation; keepers.json swap is owner-only.

---

## Issue 3 — the July-2025 LMP spike. **(B), sequenced AFTER Issue 2.**

### The miss, on miso-66's own scored series (RT load-weighted monthly)

| month (2025) | model | actual RT-lw | Δ |
|---|---|---|---|
| Jan | 42.07 | 51.23 | −9.2 |
| **Jun** | 40.78 | 57.37 | **−16.6** |
| **Jul** | 41.40 | 59.47 | **−18.1** |
| Sep | 37.72 | 46.37 | −8.7 |
| Dec | 42.78 | 47.25 | −4.5 |
| annual | 39.18 | 45.39 | −13.7% (C3a FAIL) |

C3c: model 0h > $200 all 2025 vs 38h DA actual (88h RT diagnostic);
2024 4h vs 24h. The Jun+Jul block alone is ≈ $2.9 of the $6.2 annual gap;
Jan/Sep/Dec carry another ≈ $1.9.

### The dominant July structure: missing North-up separation, not level

On miso-66 the model's July-2025 zonal prices span **$0.55** (Indiana 41.51,
South 41.09, Illinois 41.64 — effectively uniform), while actuals split
North ≈ $58.8 / South ≈ $35-38 (93% congestion, one-sided: the South
export-trapped at MCC ≈ −$18 under a North-set MEC — lane-3 finding §1).
**The model July level is already AT/ABOVE the actual South.** So the July
gap on the scored (North-heavy load-weighted, Indiana-hub-benchmarked)
series is almost entirely the missing North premium. The decomposition and
its owners (all previously measured; restated against miso-66):

1. **The S→N pull — supplied by Issue 2.** The model's corridor binds ~236h
   vs 919h measured because the model serves the South from Plains coal/CC
   over N→S (the miso-60 finding); honest South steam commitment reverses
   the direction and lets the RDT/TCDC/RPE machinery (already in the
   keeper, anchor-verified for 2023/24) earn the separation. This is why
   the two issues compose favorably: prices are too LOW and the steam fix
   RAISES the scored series through the congestion channel, not the energy
   margin.
2. **Lane-2 max-gen event unavailability — the event-day residual (~$6 of
   July) and most of the C3c tail.** Measured (diagnosis §4): at the
   Jul 28-29 peak blocks 11.9 GW of capability that ran elsewhere in July
   was absent; the outage overlay sees 3.6 GW; the invisible 8.4 GW is
   North-heavy (6.5 GW; 3.1 GW in MISO-Indiana) and splits COAL 2.85 /
   CT 2.84 / CC 1.26 / ST_GAS 0.66. The coal share is now partly covered
   (miso-65 regen + short windows); **the CT/CC leg (~4.1 GW) remains
   UNMODELED and has no identification without a declared event registry**
   (diagnosis §4 conclusion). Fix = **data intake**: MISO Maximum
   Generation Event / capacity-advisory declarations (public MISO notices)
   as a declared event-window registry, + CAMPD revealed event derates for
   CT/CC inside those declared windows only, under frozen guards on the
   `unit_outage_short_windows` pattern. Rule-13 class: physical
   availability events (same admissibility as CAMPD outage windows);
   backcast/calibration overlay by construction. This is `data-intake`
   skill work + one gated ScenarioConfig boolean.
3. **Scarcity depth (C3c) — machinery already in-LP; re-read, don't build.**
   The published MISO stepped RDC is already implemented and armed in the
   keeper: zonal ORDC steps $200/$1,100/$3,300 (BPM-002 §5.2.1.2 /
   Schedule 28-A, `reserve_config.MISO_ZONAL_ORDC_STEPS`, South family),
   market-wide RBDC anchored at VOLL $3,500
   (`MISO_RESERVE_DEMAND_CURVE_MAX`) on the **measured hourly cleared
   reserves** (`miso_measured_reserve_requirements`). It prints 0h > $200
   because the stack carries 14-20 GW of phantom headroom at the events
   (diagnosis §4: model margin $45-54 while reality printed $200-433) — a
   headroom-truth problem, not a missing-curve problem. Sequence: after
   Issue 2 + the event registry, re-read C3c on the honest stack; per the
   diagnosis §7(4), the existing pergen/zonal machinery may engage on its
   own. Only if it stays dark does a new scarcity mechanism question open —
   and it would be a MISO-parameter update, not an ERCOT/NYISO analogue
   import (rule 25): specifically, **verify the 2025 Schedule 28 anchors at
   intake** (the $3,500 VOLL constant predates MISO's 2025 reserve-market
   filings; if the tariff raised VOLL/RDC steps effective in 2025, updating
   the constant is a measured tariff input with a citation — check the
   effective date against the primary document, do not trust memory).
4. **What Issue 3 is NOT: the G-23 import starvation (−5.8 TWh 2025).**
   Fixing under-imports ADDS supply and LOWERS prices — it is a
   volume-accounting/C2 confounder fix (it deflates the 2025 coal over-read
   and the C2-2025 coal +4.8%), not a July-price lever. It stays in its own
   measured-seam-ladder lane (G-23) and should be sequenced with awareness
   that it pulls C3a-2025 the WRONG way — another reason to land Issues 2 +
   3(2) first.

### Expected scored deltas (direction; probes decide)

- Issue-2 alone: C3a-2025 up from −13.7% by the separation channel
  (magnitude unknowable pre-probe; the miso-60 lane predicted "toward
  zero"); C3c likely still short (events need the registry).
- Event registry on top: Jun/Jul event-day prices into the stack tail
  ($114-949 band per the diagnosis reconstruction); C3c-2025 model hours
  > $200 from 0 toward the [19, 76] pass band (0.5×-2× of 38); C3a-2025
  ≈ +1.5-2pp further.
- Every price-side change: read **C3b-2025 (0.187, gate ≤0.20)**
  mechanism-only vs a same-box base replica before believing it.

### Phase B checklist (Issue 3)

1. AFTER Issue-2's probe verdict: `data-intake` of the MISO max-gen /
   capacity-advisory event registry (raw → schema → clean; per-event
   ISO/date/window/level provenance; freeze-test).
2. Derive the event-window CT/CC revealed derates (unit-level CAMPD inside
   declared windows only; frozen guards stated in the deriver docstring;
   disjointness checks vs the std + short outage extracts — the
   miso-65/short-windows precedent).
3. Gated boolean (`unit_outage_maxgen_events` or similar), default off;
   probe all three years composed on the Issue-2 stack + same-box base;
   read Jun/Jul monthly, C3c, C3a/C3b, D-diagnostics.
4. Re-read C3c/RDC engagement on the honest stack before opening any new
   scarcity design. Verify Schedule 28 anchors (primary document) while in
   the tariff.
5. Registration chain as in Issue 2; keeper swaps owner-only.

---

## Sequencing memo

1. **Issue 1 (A)** — immediate, no solve, verifiable by recomputation;
   independent of everything else. Ship first.
2. **Issue 2 (B)** — the biggest C1 win (16/16 expected) AND the July
   separation prerequisite. Probe → miso-67 candidate.
3. **Issue 3, limb 2 (B)** — max-gen event registry intake + derate overlay,
   composed on the Issue-2 stack.
4. **Issue 3, limb 3** — C3c re-read on the honest stack; only then decide
   whether any scarcity-parameter update is needed (with the Schedule 28
   verification done regardless).
5. **G-23 (imports)** stays parked in its own lane; note it pulls C3a-2025
   down when it lands.

Cross-issue interactions to watch on every probe: **C3b-2025 ≤ 0.20** (the
tight guard — 0.013 headroom; always mechanism-only vs a same-box replica);
C3a-2024 within ±10 (−7.1% today, Issue-2 floors push South down/North up);
the miso-61/62 RDT anchors (2023/24 S→N flow + separation) must hold; C5a
2024 downward drift; OTHER_FOSSIL-2024 upward drift (Nine Mile). All probes
2023-2025 only (rule 22 — no MISO calibration-complete marker), one bundle
(rule 16), LOYO by construction (booleans arming measured data, zero fitted
scalars), fallbacks pre-declared HERE before any deciding probe is read.
No zero-forcing twins (rule 20 as amended 2026-07-14).

## What NOT to re-litigate (inherited + this session)

`coal_committed_takeorpay_all` overshoots; `temp_dependent_derate` refuted
for MISO; the coal/CT conduct lane is CLOSED (miso-66); P2 is archived (P1
is scored); CAISO's startup-aware screen is dropped-with-cause for MISO.
New this session: the gas committed take-or-pay discount (rejected on
commodity-vs-transport physics, §Issue-2); offer-side-only ST_GAS fixes
(rejected on the $118-128 outlier arithmetic); re-deriving `committed_pct`
(rule 23 — and the P5 is the correct LSL, just not a dispatch level); any
scorer change for Issue 1 (the verdict basis is sound — display only).
