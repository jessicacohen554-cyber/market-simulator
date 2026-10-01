# FINDING miso-225 — THE OWNER-RULED GAS OFFER SURVIVES THE C1 GATE THAT KILLED ITS PREDECESSOR AND IS KILLED ON THE COAL-RESPONSE FRACTION BY 37 MW; THE NEIGHBOUR-ANCHORED SEAM LADDER RECOVERS ~4.8 TWh OF IMPORTS AND STILL FAILS ITS OWN DIRECTION GATE, BECAUSE AN ANCHOR CHANGES A LADDER'S LEVELS AND NOT ITS RESPONSIVENESS (2026-09-06)

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the single
ledgered caveat. **No promotion is proposed.** The screen bundle `miso225_ruled_S` (2023 only)
is NOT registered and is **DELETED before this PR merges** (rule 29 `[R-SCREEN]` clause (c),
owner ruling R-AV): every number cited here lives in this document or in a committed JSON.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; ONE LP was scored (2023); 2024/2025 never spent.

Records: `PRECOMMIT-miso225-transport-seam-joint-2026-09-06.md` (+ **Addendum A**, both pushed
before the scored solve at `3c17b49a` / `208a714d`); instruments
`scripts/probes/_miso225_{transport_identification,wedge_anatomy,static_remerit,seam_neighbour}_phase0.py`
→ `_miso225_*.json`; blind scorer `_miso225_screen_gates.py` → `_miso225_screen_gates.json`;
frozen derives `scripts/data/derive_miso_gas_variable_transport.py` and
`derive_miso_seam_ladders.py::derive_pjm_neighbour`. Mechanisms:
`miso_gas_variable_transport`, `miso_seam_neighbour_anchored_ladder` (both `ScenarioConfig`,
default off); matrix rows `gas_variable_transport`, `seam_neighbour_anchored_ladder`, MISO cells
**`O`**.

---

## 0. Verdict in one paragraph

The owner ruled that MISO gas is priced at marginal commodity **plus variable transport**, and
conditioned the ruling on that transport being *measured* before the arm ran. Phase 0 measured
it from the receipts — for the margin-setting CC class, **$0.209/MMBtu of a $0.452 wedge over
the hub is variable**, so the ruled form drops 54 % of the print premium where miso-224's bare
hub dropped 100 % — and the LP then did almost exactly what that arithmetic predicted. **G-1
PASS**: the 2023 body falls **−$1.917** inside the pre-registered [−4.464, −1.488]. **G-4
PASS, and this is the result that matters**: the two C1 cells that flipped and killed
miso-224 both stay in band, at values inside the ranges this document's PRECOMMIT named before
the solve — COAL_PRB −1.557 → **−6.586** (predicted −6 to −7) and CC_REGULAR −4.172 →
**+4.018** (predicted +1 to +4) — and CT_PEAKER, the keeper's fragile edge at 0.015 TWh of
headroom, moves **toward** actual. The arm nonetheless **dies on G-3 by 37 MW**: coal falls
404 MW in the real sub-$20 hours against a required 441, i.e. **0.275× the static prediction
against a 0.30× line** — the same conversion ratio miso-224 measured (0.27×), which is the
honest reading that the LP's coal is held by something the static stack does not carry. The
seam leg **fails G-2 outright**: every PJM import band is $2.3–4.6 cheaper and imports still
**fall** (−75 MW in the cheap hours, −0.693 TWh annual). Attributed against the fuel arm's own
price move, the anchor recovered **≈ +4.8 TWh** of the imports the fuel arm would otherwise
have destroyed — real work — but it could not reverse the sign, because **an anchor changes a
fixed ladder's LEVELS and not its RESPONSIVENESS to the model's own price**, which is the
defect. Phase 0 measured the levels and inferred the response; the LP falsified the inference.

## 1. THE GATE TABLE, exactly as the blind scorer printed it

| gate | scorer | measured | reading |
|---|---|---|---|
| **S-1** single delta | **FAIL** | all three armed fields `ok: True` (True in arm, absent in keeper — the miso-224 §2 artifact is fixed); `other_diffs = ['ccs_retrofit_vom_adder']`; `year_scoped_diffs = []` | **A REAL fourth difference**, disclosed not edited (§2) |
| **S-2** liveness, on the SOLVE log | **PASS** | mechanism line present **with** the transport clause; winter-shape line ABSENT; seam line names `PJM WESTERN-BORDER DA quantiles` | clean |
| **G-1** fuel body direction & magnitude | **PASS** | Indiana body 33.342 → 31.424, **Δ = −1.917**, band [−4.464, −1.488]; tail −3.473; annual LW −1.913 | 64 % of the −2.976 static |
| **G-2** seam direction & footprint | **FAIL** | cheap-hour imports 3,043 → 2,968 MW (**−75**, needed ≥ +150); annual 45.754 → 45.061 TWh (**−0.693**) | **KILL — the mechanism moved the wrong way** (§4) |
| **G-3** fuel dispatch response | **FAIL** | coal **−404 MW** (needed ≤ −441 = 0.30 × −1,470), gas **+585 MW** (needed ≥ +445) | **KILL on the coal leg, 0.275× vs 0.30×**; gas leg clears at 0.394× |
| **G-4** no C1 flip | **PASS** | flips `[]`, inconclusive `[]`, band 8.0 TWh | **the pre-registered likeliest kill did NOT fire** |

**ARM KILLED ON S-1, G-2 AND G-3.**

## 2. S-1: A REAL FOURTH DIFFERENCE, disclosed rather than scored away

Unlike miso-224 §2 — where S-1 could not be satisfied by construction and the failure was a
scorer artifact — this S-1 failure is a **genuine config difference**: `ccs_retrofit_vom_adder`
reads 8.0 in the keeper's recorded config and 2.95 in the arm's, because capx D65-B changed
that value on `main` between the keeper's solve and this one. The three armed fields are each
exactly `True` in the arm and absent from the keeper, so the successor scoping miso-224 §2
prescribed works as intended.

**PRECOMMIT §7's G-DRIFT classified this hunk INERT before the solve**, and that classification
stands on the merits: the CCS retrofit screen is a forecast-mode capacity-evolution step, inert
below `ccs_retrofit_available_year` = 2028 by construction, and a `mode="backcast"` 2023 run
never enters it. But S-1 is a config-IDENTITY gate, not a reachability gate, and the config
genuinely differs — so it FAILS as frozen, and it is reported as a fail. **I did not edit the
scorer after seeing this.** A successor that wants S-1 to mean "differs only in fields that can
reach this solve" must say so in its own PRECOMMIT, before its solve.

## 3. THE FUEL LEG — the arithmetic held, and so did both numeric predictions

### 3.1 Price

Indiana body 33.342 → 31.424 (**−1.917**), tail −3.473, annual load-weighted −1.913. Predicted
−2.976 from the ruled static re-merit; realized 64 % of it, well inside the pre-registered
0.5×–1.5× band. (The bare-hub predecessor moved −4.11 on a −6.72 static, 61 % — the conversion
ratio is stable across both arms, which is itself evidence the instrument is sound.) The C3a
face is **not quoted**: a single-year replay writes no `metrics.json`, and this session's own
actual-price comparator is not the scorer's, so only the DELTA above is comparable. Direction
reported per rule 1: the body falls, so the positive-body / negative-tail cancellation that
makes C3a-2023 pass is reduced, exactly as PRECOMMIT §6 said before the solve.

### 3.2 Dispatch — G-4 in full, and the predictions that held

C1 by delta transfer, 2023, band 8.0 TWh (TWh; **every cell passes**):

| class | actual | keeper (err) | arm (err) | Δ TWh | reading |
|---|---:|---:|---:|---:|---|
| **COAL_PRB** | 121.671 | 120.114 (−1.557) | 115.085 (**−6.586**) | −5.029 | **PREREG predicted −6 to −7. Held.** |
| **CC_REGULAR** | 141.817 | 137.645 (−4.172) | 145.835 (**+4.018**) | +8.189 | **PREREG predicted +1 to +4. Held.** |
| CT_PEAKER | 17.038 | 9.053 (**−7.985**, the fragile edge) | 9.424 (−7.614) | +0.370 | moves **away** from the ±8.00 edge |
| COAL_BIT | 57.069 | 54.146 (−2.923) | 52.939 (−4.130) | −1.207 | pass |
| CC_CHP | 21.311 | 19.627 (−1.684) | 20.658 (−0.653) | +1.031 | pass, **toward** |
| ST_CHP | 5.203 | 2.530 (−2.672) | 3.042 (−2.161) | +0.512 | pass, **toward** |
| COAL_LIGNITE | 7.047 | 6.382 (−0.665) | 6.146 (−0.901) | −0.236 | pass |
| **ST_GAS** | 13.940 | 14.483 (+0.544) | 11.134 (**−2.806**) | **−3.349** | pass, **AWAY** — the one adverse move |

**This is the headline structural result.** miso-224 flipped CC_REGULAR to +12.60 and COAL_PRB
to −11.88 and died on G-4; the ruled form lands both inside band, at the values predicted from
the measured transport. **The transport measurement is what did it** — it is the difference
between dropping 100 % and 54 % of the CC print premium — and that is a measured input doing
the work, not a tuned one. Reported against interest: **ST_GAS moves away from actual by
3.35 TWh** (its `v` is $1.288/MMBtu, so the ruled arm makes steam gas relatively dearer and it
loses dispatch), the largest adverse cell and the one a successor must watch.

### 3.3 Why G-3 failed, stated as a defect and not as a near-miss

Coal fell 404 MW against a required 441 — short by 37 MW, 8 %. The gas leg cleared comfortably
(+585 vs +445 required, 0.394×). So the arm put gas exactly where its arithmetic said and could
not take the matching coal out. The conversion ratio, 0.275×, is the SAME the bare-hub arm
measured (0.27×) at 2.3× the fuel move — so this is not noise and it is not a threshold
artifact: **the LP's coal in the cheap hours is held by something the static stack does not
carry, at a strength that scales with neither the fuel move nor the price.** The keeper's own
D-2 says it is not forcing (COAL forced energy 0.30 % of the class, one `reliability_floor`
mechanism), so the candidate is the commitment structure — the P0-detected run pattern and the
take-or-pay committed band — holding units online through hours their own offer loses. That is
the named successor object, and it is a COMMITMENT question, not a fuel one.

## 4. THE SEAM LEG — it did real work and still failed, and the reason is the important part

**Measured**: every PJM import band $2.3–4.6 cheaper (bands 1–4 mean −$3.81 in 2023), and
imports **fell**: 3,043 → 2,968 MW in the real sub-$20 hours (−75, needed ≥ +150), 45.754 →
45.061 TWh annual (−0.693).

**Attribution, against the fuel arm's own price move.** miso-224's bare-hub arm, with no seam
repair, lost **−11.85 TWh** of imports at a body move of −4.11. Scaled linearly to this arm's
−1.917 body move, the fuel leg alone would have lost **≈ −5.53 TWh**. Measured loss: −0.693.
**The neighbour anchor therefore recovered ≈ +4.8 TWh of imports** — the mechanism is not inert
and it is not cosmetic. It simply could not reverse the sign, which is what G-2 as frozen
demanded, and the gate is not renegotiated.

**The structural reason, which is the finding.** The ladder is a fixed price ladder that the LP
clears against **its own internal price**. Re-anchoring it on the neighbour changes the band
LEVELS; it does not change the fact that the bands go out of merit when MISO's price falls.
Both things happened at once here — bands got cheaper, MISO's price fell $1.9 — and the price
fall dominated. **Phase 0 measured the level change and INFERRED the response; the LP falsified
the inference.** The owner's ruling ("an import's merit position depends on the neighbour's
supply cost") is satisfied in the ladder's *levels* and not in its *responsiveness*, and the
gap between those two is exactly what this screen discovered.

**The clean successor test is unambiguous and cheap**: the seam arm **ALONE**, no fuel arm. With
MISO's price unmoved, cheaper bands must raise imports, and the measurement is a direct read of
the anchor's own effect with no confound. That test was not run here because the queue head
required the joint form; it is the first thing a successor should spend an LP on.

## 5. WHAT THIS DOES NOT LICENSE, and the cells

- **No keeper, no full span, no registration.** The arm is dead on the screen's own
  pre-registered gates. Rule 29: the remaining years are never spent. PRECOMMIT §6 narrowed
  rule 29(2) ex ante to screen → owner → full span; the screen did not clear, so neither step
  follows.
- **`gas_variable_transport` MISO cell `O`, not `R`.** It is the owner-ruled convention, it did
  what its arithmetic claimed on price (G-1), and it **passes the C1 gate that killed its
  predecessor** — including both ex-ante numeric predictions. It failed the coal-response
  FRACTION, which is a statement about what holds MISO's coal, not about the fuel convention.
  A joint re-test with the commitment object named in §3.3 is new evidence.
- **`seam_neighbour_anchored_ladder` MISO cell `O`, not `R`.** It failed its own direction gate,
  but in a JOINT arm whose other half moved the price against it, and the attribution in §4
  measures it doing ≈ +4.8 TWh of real work. It must be re-tested ALONE before any verdict; a
  joint failure is not a refutation of a mechanism whose partner moved the variable it clears
  against.
- **The transport table stands regardless.** `data/raw/reference/miso_gas_variable_transport.csv`
  is a measured, frozen-derive input with an exact forward analogue; nothing in this screen
  bears on its correctness, and the identification evidence (§1.2 of the PRECOMMIT) is
  independent of any LP.
- **Reported against interest, in full**: S-1 failed on a real difference (§2); ST_GAS moved
  3.35 TWh away from actual (§3.2); the body fall reduces the C3a-2023 cancellation (§3.1); and
  the first launch of this screen died on a guard of my own at the wrong layer, costing one
  582-second LP (PRECOMMIT Addendum A).

## 6. GOVERNANCE — what happened, in the order it happened

- **PREREG and both mechanisms committed and pushed BEFORE the scored solve** (`3c17b49a`),
  with the blind scorer in the same push; Addendum A pushed before the re-run (`208a714d`).
  No band, kill condition or pre-registered value was edited at any point.
- **Phase 0 killed one of the three chartered legs before any LP.** The coal self-commitment
  floor was refused on rule 19 `[R-ONE-MECH]` from the keeper's own committed D-2 (MISO COAL
  forced energy 0.30 / 0.34 / 0.17 % of the class) plus miso-53's standing adjudication of the
  per-plant CAMPD must-run band (29.3 % cap-weighted, 44 of 57 plants). The 2025 MISO SOM —
  whose publication miso-53 named as the rule-23 re-derive trigger — was intaken as evidence
  instead (12 rows; source PDF verified byte-exact against the committed `SHA256SUMS.txt`,
  `a179e31a…398aec06`). Regulated coal must-run share of starts: **56 / 53 / 61 %** for
  2023 / 2024 / 2025.
- **First launch OOM-free but killed in post-solve bookkeeping** by my own `__post_init__`
  cross-field validator, after both LP passes had completed. Diagnosed as a LAYER error, both
  validators moved to the point of use, disclosed in Addendum A and pushed **before** any gate
  was scored or any arm output read; partial bundle deleted and the screen re-run from scratch,
  so the scored bundle is one code state throughout.
- **No control solve.** G-DRIFT `cbcd3d33..d1aa877f`: seven files, 511 insertions, 22 deletions,
  ALL INERT (capacity-market / capacity-evolution / CCS-retrofit, all forecast-mode). Form 4:
  the committed keeper is the control. The one hunk that surfaced downstream — the
  `ccs_retrofit_vom_adder` value — surfaced in S-1, not in dispatch, exactly as an inert-for-
  the-solve classification predicts.
- **Rule 27**: every ≥300-line file was edited locally and pushed as on-disk bytes, with the
  blob verified equal on the remote after each push (10 files, then 5).
- **Rule 28**: two base rows minted with the fields plus a cell line in all six shards;
  `check_mechanism_matrix.py --base d1aa877f` exits 0. MISO cells stamped in this session.
- **Disclosed, not this lane's to fix**: `main` at `d1aa877f` carries 18 pre-existing failures
  in the pinned-default-cache-key tests, reproduced identically with this session's changes
  stashed. This session's two fields do NOT move the default key — the hashed payload of
  `ScenarioConfig()` was diffed directly against HEAD and is byte-identical.
- **DOF ledger unchanged at 41/2**: zero fitted scalars minted. Both new inputs are measured
  tables from frozen derives.
