# OWNER DECISION CARD — ercot-225: revise the G-SPUR gate to close the band-top blindness? (measured on every registered ERCOT run; NO verdict of any standing run changes under the revision; one recorded artifact-leg FAIL is exonerated)

**Drafted 2026-08-21, session ercot-225, branch
`claude/ercot-225-gspur-gate-z1q0f6`. Status: AWAITING OWNER SIGN-OFF — the
gate is NOT changed by this card.** Protocol precommitted and blob-verified
before any number was computed
(`docs/PRECOMMIT-ercot225-gspur-bandtop-gate-revision-2026-08-21.md`, blob
`9b55eac9`); all numbers from committed artifacts only
(`results/calibration/ercot225_gspur_bandtop_reread.json`; no LP, no solve,
no re-bundle). Keeper `2026-08-20-ercot223-arm-eventrelease` untouched.

## 1. The question

G-SPUR counts spurious high-price hours as `model ∈ [150, 500] & actual <
150`. FINDING-ercot214 §5 measured the defect: the $500 upper lid makes the
gate **blind to phantom hours that overshoot the top** — pricing a phantom
hour HIGHER removes it from the count, so worsening reads as improvement
(h5822-2023: $583 vs actual $145; h3355-2025: $1,411 vs actual $135) and
repairing it reads as a regression (the ercot-215 "0→1" 2025 leg). Should
the gated quantity become the lidless count
`S_nolid = #{model ≥ 150 & actual < 150}`?

## 2. The options (precommit §2)

* **Option A — RECOMMENDED: gate on `S_nolid`;** keep
  `S_band`/`S_top` (`model > 500 & actual < 150`) as the reported
  decomposition. Bar semantics unchanged in form (+5/yr for baseline-bar
  scorers, no-increase for A/B scorers); the baseline constant re-reads
  under the same spec in the same commit: **9/11/1 → 9/12/1** (the
  re-reading of the baseline bundle `ercot215_decontam_B`; the +1 is
  h3068-2024, §4c). A gate whose purpose is "no new spurious high-price
  hours" must not be escapable by overshooting.
* **Option B:** keep the banded gate; add `S_nolid`/`S_top` as a mandatory
  side-by-side report (blindness documented, not closed).
* **Option C:** status quo (the flag stays a standing caveat on every future
  G-SPUR reading).

## 3. Measured effect — every registered ERCOT run (band / top / lidless, 2023 · 2024 · 2025)

| run | S_band | S_top | S_nolid |
|---|---|---|---|
| ercot204-rule26-delete | 9 · 11 · 0 | 0 · 1 · **1** | 9 · 12 · 1 |
| ercot213-ctl-headbase | 9 · 11 · 0 | 0 · 1 · **1** | 9 · 12 · 1 |
| ercot213-arm-pubanchor | 17 · 13 · 0 | **7** · 1 · **1** | **24** · 14 · 1 |
| ercot215-ctl-headbase | 17 · 13 · 0 | **7** · 1 · **1** | **24** · 14 · 1 |
| ercot215-arm-decontam | 9 · 11 · 1 | 0 · 1 · 0 | 9 · 12 · 1 |
| ercot219-ctl-headbase | 9 · 11 · 1 | 0 · 1 · 0 | 9 · 12 · 1 |
| ercot219-arm-optionb | 273 · 671 · 1239 | **1937 · 659 · 1163** | 2210 · 1330 · 2402 |
| ercot221-ctl-headbase | 9 · 11 · 1 | 0 · 1 · 0 | 9 · 12 · 1 |
| ercot221-arm-adaptive | 11 · 10 · 1 | 0 · 1 · 0 | 11 · 11 · 1 |
| ercot223-ctl-headbase | 11 · 10 · 1 | 0 · 1 · 0 | 11 · 11 · 1 |
| **ercot223-arm-eventrelease (KEEPER)** | 11 · 11 · 1 | 0 · 1 · 0 | **11 · 12 · 1** |

Both NaN conventions (`_ercot173_ab` finite-mask, `ercot221_gates`
nan-to-num) agree on every count.

## 4. What the lidless count newly sees (the §5 priors, all resolved in their expected branch)

* **(a) ercot-213-arm 2023: seven overshoot hours, not one.** h3954 $1,298,
  h4051 $903, h4069 $897, h4070 $1,310, h4071 $898, h4117 $885 (June
  adder-made afternoons, actuals $83–138) + h5822 $583 (actual $145). The
  recorded 9→17 (+8 over the +5 bar) was itself understated: lidless it is
  **9→24 (+15)** — the REJECTED-AS-ARMED verdict was right, and stronger
  than recorded.
* **(b) h3355-2025 predates ercot-213.** It sits above the top in the
  ercot-204-era keeper too ($630.98 vs actual $134.84) — every recorded
  "2025: 0" in the 204/213 lineage was blindness, never a clean zero.
* **(c) h3068-2024 is a standing blind hour in EVERY registered run,**
  all lineages: May 8 2024 20:00 CST, model $676.80–$798.20 (keeper
  $798.20) vs actual **$110.41** — the hour after the May-8 evening event,
  where the model holds a deep price after reality came off the peak. Never
  counted by any G-SPUR reading to date. Under Option A it enters both arm
  and baseline (hence 9/12/1), so it flips nothing — but it becomes visible
  and permanently counted, and is a named object for a future lane.
* **(d) The ercot-219 catastrophe was ~8× the recorded size in 2023:**
  banded 273 concealed 1,937 further hours above the top (lidless
  2210/1330/2402). Already a FAIL; now an honest one.

## 5. The verdict-flip table (precommit §4 rules, both sides re-read lidless)

| # | run / rule | recorded | revised | flip? |
|---|---|---|---|---|
| V1 | ercot-204 (no-increase) | PASS | PASS | no |
| V2 | ercot-213 (+5 bar; strict leg) | **FAIL** (2023 +8) | **FAIL** (2023 +15; strict also fails 2024 12→14) | no — **a fortiori** |
| V3 | ercot-215 (+5 bar; strict leg) | session PASS; **strict leg FAIL on 2025 0→1** | **PASS on BOTH rules** (24→9 / 14→12 / 1→1, non-increasing every year) | **YES — the sole flip.** The recorded strict-leg FAIL was the blindness artifact itself; lidless, the decontamination reads strictly improving in every year |
| V4 | ercot-219 (+5 vs baseline) | FAIL | FAIL (vs revised bars 14/17/6) | no — a fortiori |
| V5 | ercot-221 (+5 vs baseline) | PASS | PASS (11/11/1 vs 14/17/6) | no |
| V6 | ercot-223 KEEPER (+5 vs baseline) | PASS | PASS (11/12/1 vs 14/17/6) | no |

**No historical promotion or standing determination would have differed.**
ercot-213 was owner-promoted over its G-SPUR FAIL (that record stands, now
stronger); ercot-215's operative session verdict was already PASS (its
rejection was G-C3c, untouched here); the current keeper keeps PASS with
margin (2024 closest: 12 vs bar 17). The single flip is the exonerating one,
aligned with the promotion that in fact happened.

## 6. Why Option A is cheap and honest

The revision changes **zero** standing verdicts, exonerates one recorded
false regression, closes the only known way to defeat the gate's purpose
(price the phantom hour higher), and surfaces two real objects (h3068-2024
in every lineage; h3355-2025 pre-213) that the current gate structurally
cannot report. Its full cost is: the baseline constant becomes 9/12/1 and
two scorer functions drop an upper-bound comparison at their next use.

## 7. On sign-off (Option A) — the executing session's checklist

1. Edit the G-SPUR construction in the live A/B scorers
   (`scripts/probes/ercot221_gates.py` pattern for the next gates file;
   `_ercot173_ab.py` if reused), dropping the upper lid from the gated
   count and reporting the band/top decomposition.
2. Re-mint `SPUR_BASELINE` counts as 9/12/1 from `ercot215_decontam_B`'s
   committed sidecars — same commit. Also repair the §6 hygiene defect: the
   2023/2024 `SPUR_BASELINE` hour LISTS in `ercot221_gates.py` do not match
   the baseline bundle's own banded hours on the file's own construction
   (counts agree — [5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821, 5822] /
   [336–349, 2540, 2829] are the true 2023/2024 identities; 2025 [3355] is
   correct). No recorded verdict is affected (the gate compares counts),
   but the lists should not survive another session wrong.
3. No re-solve, no re-bundle, no registration change — scorer-only, exactly
   as this card's numbers demonstrate.
4. Matrix §5.1 re-stamp: queue item closed by owner decision.

**If the owner declines (Option C) or takes Option B, the queue item closes
with this card as the recorded adjudication either way — the measurement
does not need repeating.**
