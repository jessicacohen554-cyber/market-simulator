# FINDING — capx D3: MISO's T1-H `retire.total_gw` PASS→FAIL flip is ATTRIBUTED — the G3 cap-grain fix unmasked a compensating error; the FAIL value is the model's stable, control-corroborated number, and the pre-fix PASS was the artifact

**Lane:** capx D3 (r#21), charter `docs/handoffs/capx-director-prompt-pack-2026-08.md` §D3.
**Precommit:** `PRECOMMIT-capx-d3-miso-retire-g3-2026-08-31.md`, pushed before measurement;
the candidate classes, evidence plan (E1–E5), adjudication rule and kills below are executed
as frozen there. **Phase 0 only: ZERO solves — every number in this finding is read from a
committed artifact.** No mechanism, no tuning, no board verdict/gate flip, no matrix cell
(no mechanism was tested). Collision check at start: clear (miso-193 mid-A/B on
`claude/miso-cc-duct-peaking-5ww6h1`, backcast namespace — untouched).

## 0. Verdict (one paragraph)

The flip's PRIMARY driver is **class (b) — a real movement in the admitted economic exit
set arriving with the FFR-3A-3 re-solve — attributed to the G3 cap-grain fix (`2adfb49`,
FFR-3F Task 1) at convergence-plus-negative-control strength** (no paired control ran; see
§3 for exactly what is and is not claimed). But "retirement-volume regression" is the wrong
name for it: the fix moved MISO **coal toward reality** (over-retirement +18.4 % → +9.1 %),
and the total band failed because the bug's +1.018 GW of excess coal exits had been
**compensating for 3.458 GW of real gas/oil exits the economic screen produces at 0.0**.
The post-fix FAIL value is byte-identical to the value FFR-2B measured under a **paired
control** a day before the fix existed — the FAIL is the model's stable number; the
FFR-3A-2 PASS (−9.8 % against a ±10 % band, a knife-edge) is the one measurement no other
run before or after reproduces. Classes (c) basis/vintage and (a) scorer-grain are
**REFUTED** for this row (§2, §4); the scorer measured a fleet the LP genuinely carried.
Per rules 1/14 the fix stays; the routed repair is the **missing non-coal economic exit
channel** (§5), not a revert and not dual-basis reporting.

## 1. The object, fixed from the committed record

| record | key | `retire.total_gw` model | err vs 15.227 actual | band (±10 %) |
|---|---|---|---|---|
| FF-2C curve leg | `miso-2021-2025-curve-ff2c-t1h` | 10.814 | −29.0 % | FAIL |
| FFR-3A-2 (pre-fix line) | `miso-t1h` (scored `8ba592814d92`†) | **13.734** | **−9.8 %** | **PASS** |
| FFR-3A-3 (post-FFR-3F, `2adfb49` in force) | `miso-2021-2025-realized-ffr3a3-t1h` (solved `941f4983`, scored `e2a422c191aa`†) | **12.716** | **−16.5 %** | **FAIL** |
| FFR-2B pipeline arm (PAIRED CONTROL, 2026-08-02, pre-fix) | `results/hindcast/miso-2021-2025-cmc-pipeline-ffr2b/MISO/0a4455fd0d642364/score.json` | **12.716** | **−16.5 %** | **FAIL** |

† Pre-2026-08-16-rewrite shas; `941f4983`/`2adfb49`/`87659ae4` map to live commits in
`docs/governance/citation-commit-map.txt` (→ `7ac1ba88` / `17865245` / `3536a054`); the two
scoring shas are absent from the map and stand as document citations only.

Sources: `ffr-3a2-battery-close-2026-08-03.md` §3.9, `ffr-3a3-battery-close-2026-08-04.md`
§2.5/§3, `ff-verdicts.json`, and the committed FFR-2B score above. Band constant:
`scripts/score_capacity_hindcast.py:124` (`thermal_gw_retired_total_frac: 0.10`).

## 2. Class (c) — basis/vintage misalignment: REFUTED

Adjudication rule step 1. The actual is **15.227 GW in every record above**, the band
constant is unchanged, and the scorer's semantics are pinned by a committed negative
control: NYISO's T1-H re-measure at the same post-fix HEAD reproduced FFR-3A-2 "to three
decimals" (`ffr-3a3` §2.1, `retire.total_gw` 1.036 identical), which a scorer-side change
would have moved. The flip is model-side. Dead.

## 3. Class (b) — the driver, and the exact strength of the attribution

**What moved (per-fuel, from `ffr-3a3` §2.5):** coal economic exits 12.95 → 11.932 GW
(−1.018 GW — the entire total movement); nuclear 0.768 and biomass 0.016 (announced)
unmoved; recall 13/17 and false-retire 0.997 GW unchanged.

**Evidence that the G3 cap-grain fix is the driver** (adjudication rule step 2, all
committed):

1. **Channel exclusion (E3).** Both solves ran the identical resolved posture (six
   solve-affecting flags at shipped defaults, `exit_rate_limits=False` — FFR-3F's Task-2
   field present but unarmed; `ffr-3a3` §1.3). The rebase separating the two lines carried
   59 commits, and the FFR-3A-2 provenance-ceiling banner's own audit names exactly two as
   bearing on the measurement: the G3 fix (unconditional) and the unarmed
   `exit_rate_limits` (cache-key only).
2. **Negative controls (E3/E4).** NYISO (zero economic exits) moved nothing to three
   decimals; NEISO/PJM/MISO moved in proportion to how hard their economic screens fire
   (`ffr-3a3` §2.1). The delta is confined to the economic-exit channel — precisely the
   admission cap's channel and nothing else's.
3. **Mechanism sign (E4).** The fix resolves the admission cap's adequacy requirement at
   the schedule's execution horizon — a larger projected peak, hence a larger requirement,
   hence **more retention, fewer exits** (`ffr-3f-exit-throughput-2026-08-03.md` §1.2–1.3,
   with a discriminating synthetic in which reverting the grain changes retention 2→1).
   Post-fix MISO retires less. Sign matches.
4. **Convergence to a controlled value (E4, strongest).** The post-fix leg lands
   **exactly** on FFR-2B's paired-control pipeline values, on every retirement quantity at
   once: total 12.716, coal 11.932, false-retire 0.997, recall 0.765 (13/17) — verified in
   this lane directly against the committed
   `miso-2021-2025-cmc-pipeline-ffr2b/…/score.json`, not just the doc's table — and PJM
   converges the same way (coal 18.309 → 14.756 = FFR-2B's controlled 14.756). Two ISOs
   independently landing on independently-controlled values (`ffr-3a3` §3).

**What is NOT claimed:** no paired control ran in FFR-3A-3 and none ran here (K2 —
zero-solve lane). The alternative that some *other* commit among the 59, also confined to
the economic-exit channel, moved MISO coal by exactly the amount that restores the
controlled value is not excluded by a control — only rendered evidence-free by 1–4. The
attribution is therefore **convergence + negative-control strength**, the same posture
`ffr-3a3` §3 takes ("stated as convergence, not attribution"). The single-delta A/B that
would upgrade it to controlled strength is **routed, not run** (§6), and is flagged as
probably not worth the compute given item 4.

**A residual anomaly, disclosed rather than smoothed over (open, not load-bearing):**
FFR-2B (2026-08-02) *predates* the fix yet shows the post-fix values, so the cap-grain
bug's +1.018 GW expressed on the FFR-3A-2 line (`f0b8c025…def7cbf8`) but not at FFR-2B's
HEAD. What armed it on that line (peak/requirement input drift between the two pre-fix
HEADs being the natural candidate) is not isolated on committed artifacts. This does not
weaken the flip attribution — the flip is FFR-3A-2→FFR-3A-3, both measured — but it means
"the pre-fix figures carried the bug" (`ffr-3a3` §3) is precise only for the FFR-3A-2
line, not for every pre-fix vintage.

## 4. Class (a) — scorer-grain artifact: REFUTED for this row (the validity verdict)

Adjudication rule step 3, the charter's "a cap-grain scorer may be measuring a fleet the
LP never carried" concern, taken seriously and answered on the seam:

- The scorer is **ledger-grain**: `retire.total_gw` sums `led["retirements"]` rows from
  the committed evolution ledgers (`score_capacity_hindcast.py::model_retirements`).
- But for the cohort that moved, the ledger **is** the LP fleet: economic exits are
  recorded at plant-binned **tranche** grain (`COAL_MISO-East_p1733_committed`,
  `…_econ`, `…_mustrun` — verified in the committed MISO ledgers, e.g.
  `miso-2021-2025-realized-cmc-probe/…/evolution_2024.json`), because the screen acts on
  the same fleet list the runner's year loop carries into the LP, derating plant-binned
  generators in place (`capacity_evolution/retirements.py`). A ledgered economic exit is
  an LP-fleet derate by construction; the scorer's own G-31 docstring records this grain.
- The miso-190 discard seam (per-unit retirement dates lost at `fleet_to_bins`, repaired
  for the backcast by the miso-191 cohort delivery) lives in the **backcast fleet-build /
  COD path** and in **unit-grain** rows. The unit-grain rows in these hindcast ledgers
  (announced: nuclear `1715_1` 0.768, biomass `4005_*` 0.016) are identical across both
  eras — not the flip — and the moved cohort never passes through that seam.

So the clean "scorer-grain, repair = R3-style dual-basis reporting" exit does **not**
obtain: the measurement is valid, the flip is real, and no dual-basis repair is routed for
this row.

## 5. What the flip actually is: a compensating-error unmasking (the root cause)

Per-fuel against actuals (committed FFR-2B pipeline score, identical to the post-fix leg):

| fuel | actual GW | model GW | err |
|---|---|---|---|
| coal | 10.934 | **11.932** | **+9.1 %** (pre-fix: 12.95, +18.4 %) |
| gas_ct | 2.435 | **0.0** | −100 % |
| gas_cc | 0.521 | **0.0** | −100 % |
| oil | 0.502 | **0.0** | −100 % |
| nuclear (announced) | 0.812 | 0.768 | −5.3 % |
| biomass (announced) | 0.023 | 0.016 | −30 % |

MISO does not under-retire coal — it **over**-retires coal, and the fix reduced that
over-shoot. The −16.5 % total is **3.458 GW of real gas_ct/gas_cc/oil exits the economic
screen never produces**, previously hidden inside the band by bug-inflated coal. This is
the rule-14 structure exactly: an inaccurate input (decision-year cap grain) was silently
compensating a real defect, and correcting it surfaced the defect. The fix stays (rules 1
`[R-STRUCT]` / 14 `[R-ACCURATE]`); the pre-fix PASS is not a target to restore.

**The board's "cap-grain regression" framing should be retired with this finding:** the
regression is not in retirement volume — it is the honest reading of a pre-existing
missing-exit-channel defect that the ±10 % level band only now sees.

## 6. Routed repairs (routed, NOT built — director's decision)

1. **PRIMARY — the missing non-coal economic exit channel (MISO T1-H).** Root-cause lane
   on why the pipeline screen executes zero gas_ct/gas_cc/oil exits in 2021–2025 while
   reality retired 3.458 GW. Candidate threads, stated for the charter-writer, none
   presumed: (i) the attainable-margin inputs for MISO gas/oil (pro-forma inframarginal
   margin vs FOM — whether modeled energy/AS margins over-reward these classes, the
   rule-1 "fix the actual root cause" direction); (ii) per-fuel
   threshold/execution-lag identification for gas_ct/gas_cc/oil vs the EIA-860 record;
   (iii) the admission cap's requirement side in the hindcast window — S-123 established
   for the t1f that MISO's requirement basis was overstated (PRM re-vintage
   0.179→0.157, external ZRC, DR netting); an overstated hindcast requirement inflates
   post-G3 retention the same way, and the S-123 terms' hindcast-window analogue has
   never been measured; (iv) FFR-3F §1.4's recorded open item — the cap's fleet side
   stays at decision year (no entry crediting), biasing toward retention.
2. **OPTIONAL — the single-delta grain A/B** (post-FFR-3F HEAD vs the same HEAD with the
   decision-year grain restored, MISO T1-H only) to upgrade §3 to controlled strength.
   Probably not worth the compute given §3 item 4; priced for the director regardless.
3. **RECORDS — none needed beyond this lane's board note** (§7). The FC-3 verdict is
   correct as it stands; nothing in this finding flips a gate, and the D5-R co2
   annotations on the live ffr3a3/ffr3a4 keys are untouched (K3 honoured: the
   `miso-2021-2025-realized-ffr3a3` bundle itself was never committed — this finding
   works from the committed scorecards, battery-close docs, verdict records, FFR-2B
   bundle, and older-vintage ledgers, and regenerates nothing).

## 7. Board refresh executed (MISO G3 row only)

`frontend/data/forecast/program-status.json`, two edits, both additive/annotative, no
verdict or gate field moved: (1) a `t1h_retire_g3` attribution note added to the MISO
block beside `t1h_provenance`; (2) the stale trailing clause of the honest_unfit I13
note — "stands untouched" — bracket-updated to point here. The I13 closure itself remains
**OPEN as an unattributed scorer-read** (K5): this lane did not investigate why I13
closed, claims nothing about it, and the charter discipline stands for whichever lane
takes it up.

## 8. Kills honoured

K1 not triggered (battery-close docs + FFR-2B bundle carried every number). K2 honoured
(zero solves; the A/B is routed). K3 honoured (§6.3). K4 honoured (no miso-193 surface,
no backcast surface touched). K5 honoured (§7). Rule 22: no out-of-training year touched
— every number is a committed 2021–2025 hindcast read. Rule 25: nothing imported across
ISOs; PJM/NYISO appear only as the committed docs' own controls. Rule 28: no mechanism
proposed or tested; no matrix edit.
