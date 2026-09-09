# RESULT — caiso-268 SPAN: the fossil offer-band ×0.92 cut on the LIVE keeper reproduces caiso-267 **to three decimal places**, fails on the **same single number** (C4-2025 gas NRMSE 0.298 → **0.308**), and the §5b structural objection the owner refused caiso-267 on is **CONFIRMED, not dissolved** — overnight h0–6 gas error 2025 **+202 → +764 MW**. Determination **NOT-YET on C4-2025 alone**. Registered as the rejection it scores as. **OWNER RULED 2026-09-09: DO NOT PROMOTE.**

**Session caiso-268, shard SPAN, branch `claude/caiso268-span`, 2026-09-09.**
Run **`2026-09-09-caiso-268-fossil92-span`**, bundle `results/calibration/caiso268_fossil92_span`,
**2023 + 2024 + 2025 in ONE invocation, years sequential** (rules 16 `[R-ALLYEARS]`, 12 `[R-PARALLEL]`).
Charter: `docs/PRECOMMIT-caiso268-fossil-offer-8pct-2026-09-09.md`.
G-DRIFT audit: `docs/ADDENDUM-caiso268-span-gdrift-2026-09-09.md`, pushed before the first LP.
**KEEPER UNCHANGED at `2026-09-09-caiso-fuelvintage-860-gas`.** No keeper shard was edited, no
`calibration-complete.json` entry re-keyed, no status part rebuilt.

---

## §1 — The result, in six lines

1. **The cut does exactly what its arithmetic says.** C3a **+4.4 / +8.9 / +8.3 %** →
   **−0.9 / +4.3 / +3.2 %**; mean |gap| **7.20 % → 2.80 %**. Δλ **−2.850 / −1.580 / −1.720 $/MWh**
   against a pre-solve prediction of **−2.845** for the screen year — the LP reproduced the
   zero-LP arithmetic to **$0.005/MWh**. All four structural gates PASS.
2. **C3a crosses zero in 2023 and stays inside the band.** 53.70 vs an actual 54.17 is
   **0.9 % BELOW** actual — the cut overshoots the 2023 residual, as §2.1 item 1 predicted it
   might. It is still a PASS (±10 % target / ±10 % commercial), so C3a does not fail on the low
   side; it simply stops being a one-sided error.
3. **C4-2025 breaks by 0.008, in the one year of three that was on the knife edge, while
   IMPROVING the other two.** Gas NRMSE 2023 **0.287 → 0.275**, 2024 **0.260 → 0.254**,
   2025 **0.298 → 0.308** against ≤ 0.300. Correlation is nowhere near binding
   (2025 r = 0.874 vs a 0.70 floor).
4. **Determination NOT-YET, on C4-2025 alone.** With C3c ledgered the scorecard is 7 of 8 clean;
   C4 is not a ledgerable criterion (rubric v3.1 made C3c the only one), so a 2.7 % overshoot of
   one supporting-tier bound in one year holds the determination down by itself.
5. **THE FINDING UNDER THE FINDING: this run is numerically indistinguishable from caiso-267.**
   Same r, same NRMSE, same hourly gas error **to ~1 MW in every hour of every year** — because
   the two "different" baselines are themselves indistinguishable on every scored criterion (§3).
   The PRECOMMIT's rule-28 new-evidence claim is true of what the fuelvintage promotion **armed**
   and false of what it **moved**. Reported at full magnitude in §3 rather than left for a reader
   to notice.
6. **The factor was NOT swept and will not be.** 0.92 is the owner's, fixed ex ante, one config
   across all three years. No second value was tried in this session, whatever the scorecard says.

## §2 — The scorecard, keeper vs arm

| criterion | tier | keeper `…-fuelvintage-860-gas` | **arm `…-268-fossil92-span`** |
|---|---|---|---|
| C1 fuel-mix by class | load-bearing | PASS | **PASS** |
| C2 system volume | load-bearing | PASS | **PASS** |
| C3a mean LMP | load-bearing | PASS | **PASS** |
| C3b price duration/shape | load-bearing | PASS | **PASS** |
| C3c price tail / scarcity | supporting | CAVEAT [ledgered] | **CAVEAT [ledgered]** |
| **C4 fleet hourly dispatch corr.** | supporting | **PASS** | **FAIL** (2025 gas) |
| C6 governance | protective | PASS | **PASS** |
| C8 forced-energy share (D-2) | protective | PASS | **PASS** |
| **DETERMINATION** | | **CALIBRATED** | **NOT-YET** (C4-2025 alone) |

### §2.1 — C3a per year, SIGNED

The keeper PASSES all three years, so the question the charter asks is whether the cut pushes the
price level *below* actual. **It does, in 2023 only, by 0.9 %.**

| year | actual (bench `rt_lw`) | keeper | **arm** | Δλ | sign of the arm's error |
|---|--:|--:|--:|--:|---|
| 2023 | 54.17 | 56.55 (**+4.4 %**) | **53.70 (−0.9 %)** | **−2.850** | **BELOW actual** |
| 2024 | 34.65 | 37.73 (**+8.9 %**) | **36.15 (+4.3 %)** | **−1.580** | above actual |
| 2025 | 34.42 | 37.26 (**+8.3 %**) | **35.54 (+3.2 %)** | **−1.720** | above actual |

Mean |gap| **7.20 % → 2.80 %**. Every year is a PASS on both bands before and after.

### §2.2 — C4 gas NRMSE per year, to three decimals, against the ≤ 0.300 bound

§2.1 of the PRECOMMIT named 2025 as the knife edge **in advance**, and named caiso-267's 0.308 as
the most likely G-NOFLIP-adjacent failure. It is what happened.

| year | keeper | **arm** | Δ | vs ≤ 0.300 | r (floor 0.70) |
|---|--:|--:|--:|---|--:|
| 2023 | 0.287 | **0.275** | **−0.012** | better, inside | 0.881 → 0.882 |
| 2024 | 0.260 | **0.254** | **−0.006** | better, inside | 0.912 → 0.913 |
| 2025 | **0.298** | **0.308** | **+0.010** | **0.008 OVER (2.7 %)** | 0.877 → 0.874 |

### §2.3 — C3c, and the two criteria that are reported but do not gate

**C3c — the arm erases the model's remaining 2023 scarcity tail**: model **23 h → 0 h** against an
actual RT 47 h; 2024 is 0 h against 35 h in both runs; 2025 is 0 h against 8 h in both. A uniform
offer cut removes exactly the hours that were clearing highest. Ledgered under the rubric v3.3/v3.6
standing rule (owner: *"C3c is an acceptable caveat"*), **reported at full magnitude, not erased**,
and it still spends the single ledgerable slot.

**C5a CO2 (REPORTED-ONLY since v2.9, contributes no status)** — the arm **improves all three
years**: 2023 **−11.0 % → −7.8 %**, 2024 **−5.2 % → −2.2 %**, 2025 **−4.3 % → +0.5 %**. That is a
direct consequence of pulling gas in against imports (§4): more in-footprint fossil burn means more
in-footprint CO2, and the keeper was short. Recorded because it is the one place the cut moves a
reported quantity decisively toward measured — and it is *not* a criterion, so it earns the arm
nothing.

**D-A diurnal amplitude (REPORTED-ONLY, band-free)** — amplitude falls in all three years
(69.2 → 65.5 %, 67.3 → 65.1 %, 82.8 → 80.2 % of measured); hod r essentially unchanged
(+0.957/+0.966/+0.974 → +0.958/+0.966/+0.973). A cut that lowers the peak more than the trough
flattens the day. Against interest and reported as such.

### §2.4 — C1 and C3b, where the arm moves inside the band

No class crosses a band, but the direction is worth stating. **C1**: CC_REGULAR 2023
**−3.44 → −1.33 TWh** (toward actual) but 2024 **+0.11 → +1.92 TWh** (through zero, away);
CT_PEAKER improves in both years it is scored (−2.10 → −1.88, −2.66 → −2.44).
**C3b** price shape: 2023 **0.083 → 0.093** (worse), 2024 **0.143 → 0.127** and 2025
**0.111 → 0.082** (both better).

## §3 — THE FINDING UNDER THE FINDING: this run and caiso-267 are the SAME EXPERIMENT

The PRECOMMIT §2 grounds this run against rule 28 `[R-MECH-MATRIX]`'s DO-NOT-REDO discipline on the
claim that **the baseline moved** on 2026-09-09 when the fuelvintage keeper (2019+ EIA-860 retiree
window + measured monthly gas level) replaced `caiso-260`. Measured after the fact, on the scorer's
own arrays and at zero LP cost:

**(a) The two arms are indistinguishable.** Same 40 numbers, different stated baseline:

| year | caiso-267 arm | **caiso-268 arm** | h0–6 mean gas error, c267 vs c268 |
|---|---|---|---|
| 2023 | r 0.882, NRMSE 0.275, mean err −702.3 MW | **r 0.882, NRMSE 0.275, −702.3 MW** | −424/−596/−733/−826/−697/−218/−132 vs −424/−596/−733/−826/−698/−218/−133 |
| 2024 | r 0.913, NRMSE 0.254, −262.8 MW | **r 0.913, NRMSE 0.254, −262.8 MW** | identical to 1 MW |
| 2025 | r 0.874, NRMSE 0.308, +209.0 MW | **r 0.874, NRMSE 0.308, +209.0 MW** | 988/892/568/373/574/849/1106 vs 988/892/568/373/575/849/1106 |

**(b) And so are the two baselines.** On the same C4 gas basis, `2026-09-06-caiso-260-b1-demand`
and `2026-09-09-caiso-fuelvintage-860-gas` return **identical r, identical NRMSE and identical
fleet mean error** in all three years (0.881/0.287/−969.4, 0.912/0.260/−488.8,
0.877/0.298/−107.2), and their C3a means agree to the second decimal (56.55/37.73/37.26).

**What this means, stated plainly.** The fuelvintage promotion armed two real mechanisms, and that
arming IS new evidence in the sense rule 28 asks for — the cut acts on the gas price level, and the
gas level input changed. But it was **effectively inert on every scored criterion**, so the
experiment this run performed is the experiment caiso-267 performed, and it returned the same
answer. That does not make the run illegitimate — the PRECOMMIT could not have known the two
baselines would coincide, and re-measuring rather than assuming is the correct discipline — but a
reader is owed the conclusion: **caiso-268 is a REPLICATION of caiso-267, not an independent test
of the same lever.**

**One factual correction to the PRECOMMIT, made here rather than left standing.** PRECOMMIT §2's
comparison table records caiso-260's C3a as *"FAIL in 2024/2025 (+4.37 / +8.89 / +8.25 %)"*.
caiso-267's own scorecard (FINDING §4) scores caiso-260's C3a as **PASS**, and the tolerance is
±10 % on both bands, so +8.89 % passes. The PRECOMMIT's "the keeper now PASSES where caiso-260
FAILED" contrast is therefore not available: **both baselines pass C3a in all three years.** The
substantive ground for re-testing — that the measured gas LEVEL, the quantity the cut acts on, was
armed between the two runs — is untouched by the correction.

## §4 — The §5b structural objection, RE-MEASURED on this keeper: **CONFIRMED**

This is the objection the owner refused caiso-267 on (FINDING §9): *a flat multiplier applies in
all 8,760 hours, so overnight it pulls gas in against imports the real fleet was actually running.*
The charter required it be measured on the new baseline rather than assumed either way. It is
measured on the scorer's own model/actual arrays (the instrument reproduces the committed C4
numbers exactly, which is what pins it to the scored basis).

**Mean gas MW error (model − actual) by hour of day, arm vs keeper:**

| year | window | keeper | **arm** | change |
|---|---|--:|--:|---|
| **2025** | **overnight h0–6** | **+202.4** | **+764.4** | **WORSE by +562.0** |
| 2025 | belly h8–16 | −1,031.8 | −862.0 | better by +169.8 |
| 2025 | evening h17–23 | +766.1 | +1,030.9 | worse by +264.8 |
| 2025 | fleet mean err / RMSE | −107.2 / 1,730.5 | **+209.0 / 1,785.7** | **crosses zero; RMSE worse** |
| 2024 | overnight h0–6 | −464.2 | −34.8 | better by +429.4 |
| 2024 | fleet mean err / RMSE | −488.8 / 1,808.4 | −262.8 / 1,771.7 | better |
| 2023 | overnight h0–6 | −991.5 | −518.3 | better by +473.2 |
| 2023 | fleet mean err / RMSE | −969.4 / 2,249.9 | −702.3 / 2,157.6 | better |

Actual fleet means: 7,848.4 / 6,964.8 / 5,804.7 MW.

**The mechanism, named exactly.** The cut is uniformly *more gas*, in every hour. Where the keeper
**under-dispatches** gas (2023 −969 MW, 2024 −489 MW) that helps everywhere and both years improve.
Where the keeper is **already near-unbiased** (2025, −107 MW against a 5,805 MW fleet) the same cut
pushes it into **over**-dispatch (+209 MW) — and because the overnight hours are where the model
has least headroom, they take the largest share of it. **2025 is the year the objection bites, and
2025 is the year C4 fails.** They are the same fact.

**The annual-scale confirmation of "against imports", which caiso-267 asserted hour-by-hour and is
established here at the class level** (G-FOOT, §5):

| year | import | CC_REGULAR | fossil total | non-fossil total |
|---|--:|--:|--:|--:|
| 2023 | **−2.3242** | +2.1157 | **+2.3450** | **−2.3478** |
| 2024 | **−1.9745** | +1.8088 | **+1.9855** | **−2.0102** |
| 2025 | **−2.7763** | +2.5861 | **+2.7741** | **−2.8064** |

(TWh, arm − keeper.) The displaced non-fossil is **essentially all imports** — the substitution is
one-for-one, and it is the substitution rule 1 `[R-STRUCT]` asks about.

**Verdict on the objection: it carries over, and in 2025 it is stronger than the belly gain.**
Nothing here dissolves it, and nothing here licenses an hour-scoped or shaped cut as a remedy — that
would be a different mechanism needing its own PRECOMMIT, its own footprint-named screen year and,
critically, an external driver that is not "the residual is overnight" (rule 17 `[R-FLOOR-WINDOW]`).
**This session proposes none.**

## §5 — Rule 29 `[R-SCREEN]` gates, all measured on the full span

The PRECOMMIT fixed these before the solve. They are STOP-ONLY: they may kill the arm, never
promote it, and none reads the target residual.

| gate | pre-registered condition | measured | verdict |
|---|---|---|---|
| **G-IDENT** | demand / renewables / hydro / imports / outages / fleet byte-identical | **max &#124;Δdemand&#124; = 0.000000 MW** over **61,320 zone-hours per year**, all three years; Δslack and Δdump **0.000000** likewise | **PASS** |
| **G-FOOT** | response confined to fossil rows and the prices they set | fossil **+2.3450 / +1.9855 / +2.7741** TWh vs non-fossil **−2.3478 / −2.0102 / −2.8064**; conservation residual **−0.0028 / −0.0247 / −0.0323** | **PASS** |
| **G-DIR** | &#124;Δλ&#124; ∈ [0.5, 8.0] $/MWh **and negative** | **−2.850 / −1.580 / −1.720** — in band and negative in every year; the 2023 screen-year value lands **$0.005** from the pre-solve prediction of −2.845 | **PASS** |
| **G-NOFLIP** | no non-target load-bearing criterion flips PASS → FAIL (C1, C2, C3b, C6, C8) | C1 PASS→PASS, C2 PASS→PASS, C3b PASS→PASS, C6 PASS→PASS, C8 PASS→PASS | **PASS** |
| **G-CTRL** | form 4, earned by G-DRIFT | all hunks INERT; CAISO surface fingerprint `cba92d202f32f9fd` identical at HEAD — **no control solve spent** | **PASS** |

**C4 is supporting tier and is deliberately NOT a G-NOFLIP stop** — it is measured, reported at full
magnitude, and carried to the owner as the promotion question. The PRECOMMIT §2.1 item 2 named it
in advance, so this reading is not post-hoc.

**The screen (rule 29 clause a) was not separately spent by this shard.** The PRECOMMIT assigned
the 2023 screen to the Y2023 shard; this shard is the full span. The 2023 numbers reported here
are the span's own 2023, solved inside the one invocation with the one input snapshot — which is
what §6.1 requires and what a hand-composed bundle cannot give.

## §6 — Governance record

* **Rule 1 `[R-STRUCT]` / 13 `[R-MEASURED]` carve-out, conditions (a)–(e).** (a) 40 band
  multipliers only — `committed` / `econ_low` / `econ_high` / `peak` across 10 classes;
  **verified post-solve against the bundle's own `run_config.json`: all 40 land at exactly
  `0.92 ×` the keeper's, 0 mismatches at 1e-12**, every `phys_*`, `econ_low_share` and
  `pct_peaking` untouched, and the `peak_ladder` rebuilt from the post-override `peak`
  (`[[0.2, 1.27512]]×5` and `[[0.2, 1.06168]]×5`) exactly as predicted. (b) ONE config across all
  three scored years; `years_held [2023, 2024, 2025]` read from the bundle's own `meta.json` and
  checked by exact set equality — **C6 PASSES**. (c) set ex ante by the owner, declared in a
  PRECOMMIT pushed before the first LP of any shard, **never swept**. (d) relative band ratios
  preserved, so fossil merit order is unchanged and only fossil-vs-non-fossil moves — the intended
  effect, and §4 measures it. (e) declared in `governance.authorized_price_tuning` and carried in
  the DOF ledger.
* **Rule 20 `[R-DOF]`.** The ledger gains **one** free parameter, `fossil_offer_band_scale = 0.92`,
  identification source *"price residual, authorized channel (rules 1/13 amendment 2026-09-05);
  owner instruction 2026-09-09"* — **the ruling itself, never a measured input**. Ledger goes
  9 → **10** entries, 6 → **7** residual. Per the R-AY cross-reference its presence does not by
  itself open a new root-cause issue; the `root_cause` field records the standing in-sample
  identification item the `offer_curve_by_group` family row already carries, which this parameter
  does not enlarge. **Disclosure:** the entry is classified `identification: "residual"` (the
  ledger's own three-value taxonomy has no "authorized-channel" class) with the ruling carried in a
  separate `identification_source` field; that is the honest encoding, not an evasion of E8.
* **Rule 29(b) G-DRIFT / G-CTRL form 4.** Earned by a code audit, not asserted — two files, 102
  lines of comment-only change plus one NYISO-scoped declaration line, corroborated by the capx-D79
  fingerprint matching byte-for-byte. **No control solve was spent.** Full audit in
  `docs/ADDENDUM-caiso268-span-gdrift-2026-09-09.md`, pushed before this shard's first LP.
* **Rule 22 `[R-HOLDOUT]`.** 2023 / 2024 / 2025 only — all training tier. No `--holdout-authorized`,
  no marker question. **2019, 2020, 2021, 2022 and H1-2026 were not solved, scored or registered.**
* **Rule 15 `[R-DASHBOARD]`.** Registered as `2026-09-09-caiso-268-fossil92-span` in the session
  that produced it, **as the rejection it scores as** — which is what the rule requires of a
  rejection. **NOT promoted; the keeper shard was not touched.**
* **Rule 16 `[R-ALLYEARS]` + §6.1.** One invocation, one bundle, **one input snapshot**. The
  hand-composition route that produced a broken C4-2025 (`r=None, NRMSE=8.406`) four hours before
  this session was never taken.
* **Rule 31 `[R-RETAIN]`.** Nothing solved was deleted. See §8.
* **Rule 27 `[R-PUSH]`.** No source file ≥ 300 lines was rewritten from generated content. The one
  new file (`scripts/gen_caiso268_attestation.py`, 310 lines) was blob-verified after its push —
  310 lines both sides, md5 `45efdf715ee8c40b5e0e5c13e68cc71c` identical.
* **Rule 28 `[R-MECH-MATRIX]`.** The `offer_curve_by_group` cell in
  `docs/codebase-site/data/mechanism-matrix/CAISO.js` carries this session's evidence. No other
  ISO's shard was touched. No new `ScenarioConfig` field, so duty (c) does not fire.
* **Rule 25 `[R-ISO-SCOPE]`.** A CLI override on a CAISO invocation. No shared default, no
  `constants.py` value, no other ISO's curve.

## §7 — Disclosures against interest

1. **§3 is the big one and it is against this session's own premise.** The run replicates
   caiso-267 rather than testing the lever against a genuinely moved baseline, and the PRECOMMIT's
   C3a FAIL→PASS contrast is factually wrong. Both are stated in §3 rather than left for a reader.
2. **The cut puts committed gas below its own measured physical min-load heat rate.**
   `CT_PEAKER.committed` 0.991 → **0.912** against `phys_committed` **0.991** (the keeper sat
   exactly *at* physical), and `CT_CHP.committed` 1.100 → **1.012** against 1.073. Three more
   (CC_REGULAR/CC_CHP `committed` and `peak`, ST_GAS `committed`) were already below theirs and are
   deepened. `phys_*` is inert in this recipe (`gas_offer_net_revenue_margin=false`) and was not
   touched, so **no LP row changes** — but the model now offers committed gas below its own
   measured fuel cost, and that is worth a reader's attention either way.
3. **Two ST_GAS bands are bypassed per-plant and the cut does not reach them.**
   `caiso_st_gas_committed_measured` and `caiso_st_gas_peak_measured` are both armed and resolve
   those bands per plant for `ST_GAS_PEAKER_PLANTS` members. ST_GAS carries 0.02–0.19 TWh — a
   completeness note, not a material one.
4. **The three sibling per-year shards did not land.** `claude/caiso268-y2023`, `-y2024` and
   `-y2025` are **absent from the remote** at the time of writing (checked after the solve:
   `origin/claude/caiso268-span` is the only `caiso268` branch). **The per-year vs one-invocation
   cross-check the charter asked for could not be performed**, and no divergence is reported
   because none could be measured. It is a gap, not a clean result. If those shards land later,
   the numbers to compare against are §2.1's C3a and §2.2's C4 per year.
5. **The container needed six things installed or rebuilt before the first LP** and none is a model
   change: the pinned solve stack (highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3,
   pyarrow 24.0.0, pydantic 2.13.4), `openpyxl` (eGRID sheet reads), `tzdata` (`US/Pacific` for the
   CAISO interchange clock), the 8 GiB swap from `prepare_solve_container.py`, and the **gitignored
   `data/clean/capacity-deliverability` partition**, whose absence hard-fails the solve by design
   (the caiso-157/188 guard) rather than silently re-arming the fitted 7,500 MW import scalar. The
   guard worked exactly as intended.
6. **The legitimacy-diagnostics gate reports FAIL on the replayed bundle**, on `unit-conduct`
   `chp_steam` rows in all three years. C7/C8 score from the artifact's contents and **C8 PASSES**;
   the same rows are present on the keeper. It is a pre-existing condition of the recipe, not
   something this arm introduced — stated rather than omitted because the word FAIL appears in the
   solve log.

## §8 — THE PROMOTION QUESTION, PUT EXPLICITLY TO THE OWNER (rule 31 `[R-RETAIN]`)

**DECIDED BY THE OWNER, 2026-09-09: DO NOT PROMOTE.** The keeper stays
**`2026-09-09-caiso-fuelvintage-860-gas`** and CAISO stays **CALIBRATED**. The caiso-268 arm
stays **registered as evidence**, which is what rule 15 `[R-DASHBOARD]` requires of a rejection.
No keeper shard was edited, no `calibration-complete.json` entry re-keyed, no status part rebuilt.
The recommendation below was option (b) and the owner took it; the record is preserved as it stood
when the decision was taken.

**I have NOT promoted this run.** The keeper stays
`2026-09-09-caiso-fuelvintage-860-gas`; the arm stands registered as evidence, which is what rule 15
requires of a rejection.

**THE BUNDLE IS ON LOCAL DISK IN AN EPHEMERAL CONTAINER AND WILL NOT SURVIVE THIS SESSION.** Its
committed slim set (`meta.json`, `run_config.json`, `metrics.json`,
`calibration_attestation.json`, `legitimacy_diagnostics.json` and the `hourly/` sidecars) is pushed,
so a promotion does **not** need a re-solve — but the heavy `dispatch/` parquets are gitignored and
go with the container. **Nothing has been deleted** (rule 31; the ercot-255 incident is why).

The trade, stated once: the cut **more than halves the price-level error** (mean |C3a|
7.20 % → 2.80 %), leaves 7 of 8 criteria clean, **improves C4 in two years of three**, improves the
reported CO2 in all three, and costs **one supporting-tier bound overshot by 0.008 in 2025**.

**My recommendation is (b), and the reason is §4, not the scorecard.** The arm buys its better price
by making the *dispatch* worse in the year where the dispatch was right: 2025 overnight gas error
**+202 → +764 MW**, fleet mean error crossing from −107 to +209 MW, RMSE up, and **2.78 TWh of
imports displaced** by in-footprint gas the real system did not run. Rule 1 `[R-STRUCT]` is explicit
that a more-accurate number reached through a mechanism that degrades real structure is not a
keeper. The carve-out made the *tuning* admissible; it did not make this particular trade a good one
— and §3 means the owner is being asked the **same question they already answered on 2026-09-09**,
against the same measured evidence.

Options:

* **(a) Promote anyway** — accept NOT-YET as the price of a materially better price level. What you
  would be accepting is precisely one number: C4-2025 gas NRMSE at 0.308 instead of ≤ 0.300, plus
  the §4 overnight regression. Say so and I will promote the registered bundle: edit
  `frontend/data/backcast/keepers/CAISO.json`, rebuild `status/CAISO.js`, re-key
  `calibration-complete.json` with a determination re-verification (rule 22 D-5(b)), and run the
  keeper auditor. **No re-solve is needed.**
* **(b) Do not promote** — the keeper stays `2026-09-09-caiso-fuelvintage-860-gas` and caiso-268
  stands as a registered rejection with its evidence. **RECOMMENDED.**
* **(c) Re-cut the factor** — **I have not done this and will not without an explicit ruling**,
  because choosing a smaller factor *because* it keeps C4-2025 inside 0.300 is exactly the
  fitted-mechanism selection carve-out condition (c) exists to forbid. If a different value is
  wanted it must be set ex ante, for a stated reason that is not a gate, exactly as 0.92 was.

**Next number: caiso-269.**
