# ASSESSMENT miso-227 — THE FULL-SPAN SEAM CANDIDATE SCORES **NOT-YET** ON **ONE CELL**: CT_PEAKER-2023 at **−8.29 TWh** against a ±8.00 band, from **0.015 TWh** of keeper headroom. Every other criterion PASSES and C3a/C3b IMPROVE. The pre-registered rule sends this to the owner rather than promoting it.

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** pending the owner's call.
**Candidate registered**: `2026-09-06-miso-227-seam-neighbour` (bundle
`results/calibration/miso227_seamneighbour_K`), rule 15 `[R-DASHBOARD]`. Rule 16
`[R-ALLYEARS]`: 2023+2024+2025 in ONE invocation, years sequential, ONE bundle. Rule 22: no
year outside 2023–2025. **DOF ledger unchanged at 41/2**; no `ScenarioConfig` field minted.

Records: `PREREG-miso227-seam-fullspan-candidate-2026-09-06.md` (pushed **before** the solve at
`316b592a`, blob-verified); `FINDING-miso226-seam-alone-2026-09-06.md` (the screen this
follows); `scripts/gen_miso227_attestation.py`.

---

## 0. The determination, and the one number it turns on

**`CALIBRATION DETERMINATION: NOT-YET`** — basis: *"undocumented out-of-tolerance (FAIL)
criteria: fuelmix"*. That is the **whole** basis. Inside C1, **one cell of sixteen**:

| | model | actual | error | band | verdict |
|---|---:|---:|---:|---:|---|
| **CT_PEAKER 2023, keeper** | 9.053 | 17.038 | **−7.985** | ±8.00 | PASS by **0.015 TWh** |
| **CT_PEAKER 2023, candidate** | 8.750 | 17.038 | **−8.29** | ±8.00 | **FAIL by 0.29** |

**The PREREG named this cell, and the prediction was exact.** §5 said before the solve: *"the
2023 screen's delta transfer put the arm at −8.289 … the escalation branch is a genuine
possibility, named here before the solve, not a surprise to be explained afterwards."* The
scored bundle reads **−8.29**. The delta transfer was accurate to **0.001 TWh**.

## 1. The full criterion table, candidate vs incumbent

| criterion | tier | incumbent | **candidate** | movement |
|---|---|---|---|---|
| **C1** fuel-mix by class | LOAD | PASS (16/16) | **FAIL (15/16)** | **the only failure** — CT_PEAKER-2023 alone |
| C2 system volume | LOAD | PASS | **PASS** | — |
| **C3a** mean LMP | LOAD | PASS | **PASS** | **improves in 2 of 3 years** (§3) |
| **C3b** price duration/shape | LOAD | PASS | **PASS** | improves 2023 (0.108 → 0.102) |
| C3c price tail / scarcity | SUPP | CAVEAT [ledgered] | **CAVEAT [ledgered]** | **model values byte-identical** (§2) |
| C4 fleet hourly dispatch corr | SUPP | PASS | **PASS** | — |
| C6 governance gate | PROT | PASS | **PASS** | attestation generated (§2) |
| C8 forced-energy share (D-2) | PROT | PASS | **PASS** | — |

Every C1 cell other than CT_PEAKER-2023 stays in band in both scored years. 2025's C1 is
**SKIPPED** on this EIA-923 vintage (preliminary, incomplete plant data), so it cannot fail C1
at all — the exposure was always 2023 and 2024, and 2024's CT_PEAKER (−6.11 → −6.27) has
1.73 TWh of headroom left.

## 2. TWO ARTIFACTS THAT ARE NOT RESULTS, closed rather than reported as findings

- **C3c's first read was `FAIL`, and that was a missing file.** `replay_keeper` writes no
  `calibration_attestation.json`, so C6 read **UNATTESTED**, and guard (b) of the C3c standing
  rule blocks reclassification when governance does not pass — the miso-200 vacuous-pass trap,
  hit at miso-217 §5. C3c's model values are **byte-identical to the keeper's** (3 / 7 / 0 model
  hours against actuals of 30 / 37 / 88): **C3c did not move at all.**
  `scripts/gen_miso227_attestation.py` closes it, and the table above is the honest read.
- **The attestation carries the keeper's governance flags VERBATIM.** This candidate *is* the
  miso-220 recipe plus one field, so miso-220's x1.10 non-steam offer lift is still in it. Its
  `authorized_price_tuning` block and its two **FALSE** assertions
  (`no_fit_to_price_residuals`, `levers_trace_to_measured_input`) are copied unchanged. They
  describe the **inherited** lift, not this session's delta; flipping them to true because
  *this* delta is a measured table would launder the inherited lever, which is exactly what C6
  exists to catch. This session's own claim is made in the disclosure, scoped to its own delta.

## 3. WHAT IMPROVED — the structural side of the ledger

**C3a mean LMP moved TOWARD actual in the two years the model over-prices** ($/MWh):

| year | actual | incumbent | candidate | error |
|---|---:|---:|---:|---|
| 2023 | 32.85 | 35.20 | **34.94** | +2.35 → **+2.09** |
| 2024 | 32.30 | 33.39 | **33.30** | +1.09 → **+1.00** |
| 2025 | 45.46 | 42.28 | **42.19** | −3.18 → −3.27 |

C3b improves in 2023. And the mechanism's own structural claim, measured in the miso-226 screen
and reproduced here bit-for-bit: cheap-hour imports **3,043 → 3,624 MW (+581)** at **0.829×**
its zero-LP static, footprint confined **277×** to the hours a band actually crosses merit.

**Reproducibility, worth recording**: 2023 in this full-span bundle reproduces the **deleted**
miso-226 screen exactly — identical simplex iteration counts (387,804 cold / 238,284 warm) and
identical objectives (5645830534.0440 / 5725592247.0909). Rule 29(c)'s "delete the bundle, the
doc is the record" cost nothing.

## 4. WHAT DID NOT IMPROVE, stated at full magnitude

- **The responsiveness defect is essentially untouched**: corr(imports, own price)
  **+0.750 → +0.725** against a **measured −0.101** — 3 % of the distance — and the price-decile
  slope closes **10 %** of its sign error. This form repairs the ladder's **anchor** and leaves
  its **frozen-annual-quantile** shape.
- **The annual import total moves further from every measured comparator.**
- **Seven of eight thermal C1 classes move away from actual** (2023 class sum −3.12 TWh against
  imports +3.18) — the mechanism displaces generation the model does not have to spare.

## 5. THE READING THAT MATTERS FOR THE DECISION — the band is doing almost no work on this cell

**The candidate did not create the CT_PEAKER defect; it tipped a cell that was already 0.015 TWh
from its band.** MISO's model under-produces CT_PEAKER in **every** year, by a wide margin, in
the incumbent keeper:

| year | actual | incumbent | error | candidate | error |
|---|---:|---:|---:|---:|---:|
| 2023 | 17.038 | 9.053 | **−7.985** | 8.750 | **−8.29** |
| 2024 | 19.225 | 13.117 | −6.108 | 12.960 | −6.27 |
| 2025 | 19.291 | 13.888 | −5.402 | 13.730 | −5.56 |

A cell at −7.985 against ±8.00 is not meaningfully *passing*; it is failing in substance and
passing on 0.19 % of the band. The candidate adds **0.30 TWh** to a **7.99 TWh** pre-existing
miss. **So MISO's CALIBRATED status currently hinges on 0.015 TWh of a cell that is wrong by
eight.** That cuts both ways and both directions are stated here rather than only the one that
supports a preferred answer:

- **For promoting**: the structural anchor is the owner-ruled-correct one, C3a and C3b improve,
  and the failing band was already saturated by a defect this arm neither caused nor addresses.
- **Against promoting**: the determination is the program's published standard; **all six ISO
  keepers currently read `CALIBRATED`** (verified this session), so a NOT-YET keeper would make
  MISO the only decertified market in the model — and this form buys **3 %** of the
  responsiveness repair, i.e. the certification would be spent on a partial fix whose successor
  is already identified and unbuilt.

## 6. THE DECISION RULE FIRES ITS ESCALATION BRANCH — this is not a judgment made after the fact

PREREG §4, committed and pushed at `316b592a` **before** the solve, in full:

> **Determination `NOT-YET` on a load-bearing criterion (C1 / C2 / C3a / C3b)** → **DO NOT
> PROMOTE unilaterally. Report and escalate.** The owner authorized *accepting a gate
> regression*; **decertifying the ISO is a different act** … the candidate bundle, its verdict
> and the full criterion table go to the owner with a recommendation, and the incumbent keeper
> stays designated until they rule.

C1 is load-bearing and it FAILS. **The keeper is unchanged and the candidate is registered, not
promoted.**

**RECOMMENDATION — option (c), and it is what rule 1 `[R-STRUCT]` actually prescribes.** Rule 1
does not say "keep the mechanism and accept the worse fit"; it says *"a real market behaviour
stays in even if it makes the fit worse (**then fix the actual root cause per #11**)"*. The root
cause here is named and is not the seam: **MISO under-produces CT_PEAKER by 5.4–8.0 TWh in
every year**, and C8 independently reports CT_PEAKER **27.6 / 18.6 / 15.6 %** forced —
grounded, but the largest forced share in the fleet. Fixing that cell is a MISO calibration
lever in its own right, it would restore this candidate to `CALIBRATED` on its own, and it is
worth more than the seam arm either way. The three options as they stand:

| | action | cost | what it buys |
|---|---|---|---|
| **(a)** | promote as-is | MISO reads NOT-YET, the only such ISO | the ruled-correct anchor now; 3 % of the responsiveness repair |
| **(b)** | reject and build the **hourly** neighbour anchor (miso-226 queue head) | one lane | attacks the actual defect (the +0.725 correlation), zero fitted parameters, data already in the repo |
| **(c) RECOMMENDED** | **hold the candidate, fix CT_PEAKER, re-score the pair** | one lane | keeps the structural mechanism AND removes the reason it fails — rule 1's own prescription, and it lands `CALIBRATED` |

## 7. Governance

PREREG and its decision rule committed and pushed before the solve (`316b592a`, blob-verified);
no band, threshold or verdict rule touched by this session; the scorer is `main`'s. G-DRIFT
`47e306d3..13ee0c89` (45 commits) audited ALL INERT before the solve — formatter reflows, a
comment-only `constants.py` hunk, SCN-CAP `mass_cap_tons_by_year` (coerced to `None` in backcast
mode and doubly unreachable at `carbon_price 0`), forecast-mode capacity evolution, a cache
epoch note, and CAISO reference artifacts — so no control solve was spent (rule 29(b) form 4).
pydantic pinned to the keeper's recorded 2.13.4, so no environment caveat is carried. Rule 27
`[R-PUSH]`: every file edited locally and pushed as on-disk bytes, each blob verified equal on
the remote after its push, the 1.46 MB run payload over `git push` per the transport rule.
Rule 15: the candidate is registered because it completed, keeper or not; under keeper-only
retention it is pruned at the next registration if the owner does not promote it.
