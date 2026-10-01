# FINDING miso-190 — the partial-plant exit carry arm is REJECTED BY ITS OWN PRE-REGISTERED S-1 KILL: MISO's plant-binned LP discards per-unit retirements, so the injected units run on PAST THEIR REAL DEATHS; keeper UNCHANGED (`2026-08-30-miso-188-rvsscope`)

**Session miso-190 (2026-08-30).** Charter: the FINDING-miso188 §6.6
partial-plant mid-window exit gap, granted by the miso-190 handoff.
PREREG: `PREREG-miso190-partial-plant-exit-carry-2026-08-30.md` (pushed +
blob-verified BEFORE the mechanism existed). Phase-0 census:
`_miso190_partial_exit_phase0.json`. Gates record:
`_miso190_ab_gates.json`. Runs `2026-08-30-miso-190-control`
(`miso190_ppx_A`) / `2026-08-30-miso-190-ppexit` (`miso190_ppx_B`) — both
registered per rule 15.

## 1. Ask A — zero-solve validation

PASS. `calibration_verdict.py --run-id 2026-08-30-miso-188-rvsscope`
reproduces the registered determination exactly: NOT-YET on {C3a-2025
−12.3 %} alone; C1 16/16 all / 12/12 free; C3c the single ledgered caveat;
C6 attested; C8 PASS all years (2025 ST_GAS grounded note carries).

## 2. Phase-0 (zero-solve, committed before the PREREG)

The census reproduced every §6.6 named unit at unit grain (59 leg-1
partial-plant retiree units / 3,999 MW; 31 leg-2 snapshot-OS/SB units —
at ≥40 MW exactly Big Cajun 2-1 and Warrick-2) and REFINED the charter's
sizing: the quoted 5.93 TWh (2023) is the named set MINUS Dan E Karn
(5.933 — a CAMPD unit-id mapping gap: EIA generators 1A/1B/2A/2B report
as CAMPD boilers 1/2), and Warrick-2 adds 1.038 TWh; the full oracle-kept
measured gross is **7.683 TWh (2023) / 0.597 (2024) / 0.010 (2025)**. The
2023 coal-side under-carry (COAL_BIT −5.77 / COAL_PRB −2.21 TWh raw) ≈
the missing set — the identification is real and stands.

## 3. The A/B (PREREG-miso190 §4) — what the gates found

* **S-0 PASS.** The control (`miso190_ppx_A`) reproduces the committed
  keeper value-identically — max |diff| = 0.0 on every scored sidecar of
  every year (fourth consecutive clean HEAD reproduction).
* **The loader acted as designed** (arm log, every year): leg 1 injected
  59 units / 3,984 MW; the armed vintage-status oracle scoped the widened
  membership (51 units / 1,708 MW dropped, Dallman-3 and Weston-2
  included); leg 2 re-carried 35 (2023) / 21 (2024) units including Big
  Cajun 2-1 (both years) and Warrick-2 (2023 only, OA-in-vintage_2024
  correctly excluded).
* **S-1 KILL FIRES — the flag did NOT act as specified at the LP grain.**
  The frozen per-unit witnesses (`6090_2`, `1702_1A`, …) matched NOTHING:
  MISO's dispatch fleet is PLANT-BINNED (`COAL_MISO-West_p6090_committed`,
  …tranches), so a unit's identity — and with it its per-unit retirement
  date — does not survive `fleet_to_bins`. The injected rows were pooled
  into their surviving plants' bins, whose plant-keyed COD entries carry
  no (or a future) retirement. The plant-grain evidence is decisive
  (arm − control, TWh):

  | plant (real exit) | 2024 | 2025 |
  |---|---|---|
  | Dan E Karn ×4 (ALL COAL DEAD 2023-05) | **+1.989** | **+2.760** |
  | A B Brown 1+2 (dead 2023-10) | **+2.068** | **+2.972** |
  | Sherco-2 (dead 2023-12) | +2.581 | +2.895 |
  | Petersburg-ST2 (dead 2023-06) | +1.115 | +1.991 |
  | South Oak Creek 5+6 (dead 2024-05) | +0.401 | +1.636 |
  | Big Cajun 2-1 (leg 2 — correctly year-scoped) | +0.091 | −0.054 |

  Leg 2 (whole-year vintage-scoped, no month timing needed) behaved; leg
  1's unit-grain exits did not exist in the LP. The arm dispatches
  **~10 TWh/yr of capacity that was measured dead** in 2024–2025.
* **S-2 read PASS (+7.0013 TWh coal-2023) but is POISONED** — the same
  defect inflates every year (2024 +6.5, 2025 +9.3), so the 2023 volume
  is not the repair's signal; it is the phantom's.
* **BOTH CHARTER KILLS FIRE.** Kill 1 (C3a-2025 must not regress):
  −12.2965 → **−15.0902 %** (−2.79 pp — the ~9 TWh of phantom 2025
  supply crushing prices; tolerance was 0.10). Kill 2 (identification
  integrity): the scored 2023 coal-side C1 improves (Σ|err| 8.546 →
  3.472 TWh) while S-1 shows the flag did not act as specified — an
  unidentified level lever wearing a repair's name (rule 1's
  enforcement). S-5 face at full magnitude: C3a-2023 +3.5008 →
  −0.5175 % (through zero, supply-driven), C3a-2024 −4.3034 →
  −6.6563 % (the declared adverse face, in the ±10 band), one
  PASS→FAIL flip (C3b price_shape 2025), S-4 itself clean,
  determinations NOT-YET → NOT-YET.

**Verdict: REJECTED on the PREREG's own rule ("S-1 … firing ⇒ NOT
promoted, cell R"). Keeper UNCHANGED at `2026-08-30-miso-188-rvsscope`.**
The owner's in-session posture directive (*"If structural integrity
improves but gates regress that may still be a keeper"*) was considered
and does NOT reach this arm: structural integrity did not improve — the
arm's fleet is LESS faithful than the control's (it carries measured-dead
capacity through 2024–2025), which rules 1/13/14 all refuse.

## 4. Root cause and the named successor (its own charter)

The PREREG's leg-1 premise — "`cod_ramp.effective_cod` already prefers a
generator's own per-unit retirement (the Homer City seam), so the
un-maskable over-count the builder feared has been maskable since that
seam landed" — is TRUE ONLY where a retiree keeps its own LP row: the
whole-plant channel (its plants are absent from the snapshot, so the
injected units form their own bins — Mystic, Homer City, Grand Tower) and
unbinned fleets. For a **partial** exit into a **surviving, plant-binned**
plant the builder's original comment was right all along: the plant-keyed
COD map cannot time out a single unit, and binning erases the per-unit
date before the ramp ever sees it. The 2023-only effects the charter
wanted (Sherco-2's real 1.263 TWh etc.) were delivered — but bundled
inseparably with 2024/2025 phantoms.

**Successor (named, sized, NOT built):** binning-aware unit-grain exit
timing. Two admissible forms, for the successor PREREG to choose and
freeze ex ante: (a) route partial-exit rows into their OWN date-scoped
bins (exit-cohort tranches per plant × retirement month, so the existing
COD per-unit seam applies — the Grand Tower topology generalized); or
(b) a monthly capacity derate on the surviving plant's bins equal to the
exited units' capacity from each exit month (unit-grain timing carried as
a bin-level availability mask). Either must witness at plant grain
(post-exit plant MW ≤ surviving-unit capacity) since unit ids do not
exist in the LP. The census, sizing, oracle verdicts and coal supply
registry of THIS session carry over unchanged — only the fleet-side
delivery mechanism needs the new work.

## 5. Reported against interest

1. The S-1 witness suite was partially VACUOUS as frozen: the exit-timing
   and oracle-drop witnesses keyed on unit-id strings that cannot exist
   in a binned fleet, so they "passed" by matching nothing. The presence
   witnesses failed honestly and the plant-grain drill above supplies the
   decisive evidence; no witness was re-selected after results.
2. The instrument's verdict-scorer step required registered runs; the
   gates JSON was completed after both legs were registered (order
   disclosed; no gate threshold changed).
3. The mechanism commit (field + loaders + registry + tests + matrix
   row) is in the tree and REMAINS default-off/byte-inert; the field is
   retained rather than deleted (rule 26: zero fitted content, and the
   successor reuses the loader/census/registry code verbatim).
4. The first arm attempt was OOM-killed (a container restart silently
   dropped the 8 GB swapfile); relaunched clean with swap restored,
   deleted unread. The scored attempt-2 leg is the registered one.
5. Wall-clock estimates given mid-session ("1–2 h per year") were wrong;
   measured solve time was ~15–18 min per year per leg.

## 6. Standing OWNER items (restated, not decided)

(1) the C8 provenance-materiality floor; (2) committed-vs-regenerated
diagnostics exposure; (3) `RHO_CLIP` cross-ISO band; (4) **D-4 posture —
the C3a-2025 direction object** (~3.3 GW mc-idled/flat-stack model-class
residual; ~1.3 GW scarce-export concession) — the lane's only open road,
unchanged by this session; (5) the miso-189 §7.3 marginal-vs-average
delivered-cost residue (adverse sign, cross-ISO); NEW (6) the §4
successor charter (binning-aware partial-exit timing).

## 7. Governance

Rule 22: 2023/2024/2025 ONLY; MISO holds neither marker; freeze
untouched; no new data fetch. Rules 15/16: BOTH legs registered, full
span, one invocation each. Rule 12: years sequential within each leg;
legs sequential. Rules 5/13/14/19/23/24: the field registered (4-site,
same commit), measured-identified, zero fitted scalars; the reject is on
implementation delivery, not on the identification. Rule 25: only MISO's
shard/keeper/status touched. Rule 27: exact on-disk bytes; every pushed
blob ≥300 lines verified. Rule 28: queue stamp + shard cell (U → R) +
calibration-log entry in-session. THE OWNER MERGES; no PR opened.

## 8. Reproduction

```
python3 scripts/probes/_miso190_partial_exit_phase0.py
python3 scripts/probes/_miso190_ab_gates.py
python3 scripts/calibration_verdict.py --run-id 2026-08-30-miso-188-rvsscope
```
