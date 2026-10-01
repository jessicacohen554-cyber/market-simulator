# FINDING — neiso-81: `measured_chp_heat_rates` re-adjudicated `O` → `K` and PROMOTED

**Pre-registration:**
`results/calibration/PREREG-neiso81-chp-heat-rate-readjudication-2026-08-04.md`,
committed at `66d7b44a` and pushed **before either arm solved**. Every property,
threshold, falsifier, verdict branch **and the promotion standard itself** was
fixed in advance; none was revised after a number was seen.

| | |
|---|---|
| Session | neiso-81 |
| Lane | rule 14 `[R-ACCURATE]` input accuracy — a PROMOTION re-adjudication, not new mechanism work |
| Outgoing keeper | `2026-08-03-neiso-caiso156-meter-screen` (CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat) |
| **Outcome** | **`measured_chp_heat_rates` NEISO `O` → `K`, PROMOTED.** New keeper **`2026-08-04-neiso81-chpheatrate`** |
| Bundles (one frozen HEAD `66d7b44a`) | `neiso81_control_A`, `neiso81_chpheatrate_B` |
| Runs | `2026-08-04-neiso81-control`, `2026-08-04-neiso81-chpheatrate` |
| Years | 2023 2024 2025, ONE invocation each (rule 16 `[R-ALLYEARS]`) |
| Verdict branch | **V4 PROMOTE**, reached mechanically by `scripts/probes/_neiso81_chpheatrate_ab.py` against the pre-registered ladder |

---

## §0 — the verdict in one table

| pre-registered branch | condition | fired? |
|---|---|---|
| V1 `I` | P1 or P6 falsified | no — live at both grains |
| V2 INVALID | P4 or P7 falsified | no |
| V3 `R` | P2 falsified (artifact accuracy) | no — CEMS 4/4 within 1 %, median 1.00000 |
| **V4 `K` PROMOTE** | S1–S4 hold · no N1–N4 · combined-CC test passes | **YES** |
| V5 STOP-AND-ESCALATE | any N fires, or combined-CC worsens in both scored years | no |
| V6 retain `O` | — | no |

---

## §1 — why this was re-opened, and what is NOT the reason

neiso-70 (2026-07-31) measured this arm **LIVE with every pre-registered gate
PASSING** — zero criterion regressions across all 70 scored records, C1 all
12/12 · free 8/8, C3c bit-identical — and stamped `O` **deliberately**, for
exactly one reason: fit on the repriced class degraded. Its own §6 records that
the artifact is accurate and that rule 14 `[R-ACCURATE]` forbids reverting to the
eGRID estimate because it fits better.

**The authorising change is the owner's standing standard of 2026-08-04:** *"if
structural integrity improves but gates regress that may still be a keeper."*

**The neiso-80 scope-gate correction is NOT the reason and is not offered as
one.** At the LP seam the corrected artifact gives **+27.25 %** against
neiso-70's **+27.96 %** — a 0.71 pp walk-back, **2.54 %** of the move that
produced the overshoot (neiso-80 §1.1 measured 2.15 % on the artifact
population). About one part in forty. It does not close the overshoot and this
document does not imply it does.

**Re-measured from scratch (miso-124).** neiso-70's numbers are not reused as
this arm's result: they were taken against a **different keeper** (the neiso-61
recipe) and a **pre-gate-3 artifact**. A same-HEAD **zero-delta control arm A**
was solved FIRST and every delta below is quoted against it.

---

## §2 — the load-bearing question, and the half that died before any solve

The prereg named as load-bearing: *is the CC_CHP overshoot a class-attribution
artifact of the CC_CHP/CC_REGULAR boundary, or a real dispatch error?*

### P8 — the attribution-artifact reading is **FALSIFIED**, pre-solve

| class | units | plants | capacity |
|---|---|---|---|
| CC_CHP | 19 | **7** | 320.6 MW |
| CC_REGULAR | 214 | **29** | 14,043.5 MW |

Plants in **both** classes: **none**. Artifact CC_CHP plants absent from the
model's CC_CHP class: **none**. The benchmark side is
`classFull[k] = e923_bench[k] − btm[k]`, which buckets EIA-923 per-plant net
generation through the **same** `plant_taxonomy.classify_plant` registry the
model fleet uses.

⇒ **ONE REGISTRY, APPLIED TWICE.** The CC_CHP movement is a **real per-class
reallocation**, not a bookkeeping seam. **The promotion does not rest on it, and
this session does not argue it** — the case was killed with zero solves spent
(the miso-125 discipline).

### P9 — RESOLVABILITY is the surviving half, and it is a number

C1's per-class volume band is `min(2 % ISO load, 8 TWh)`:

| year | C1 band | CC_CHP's ENTIRE annual actual | ratio | resolvable? |
|---|---|---|---|---|
| 2023 | ±1.955 TWh | 1.072 TWh | **0.548×** | **NO** |
| 2024 | ±2.103 TWh | 1.124 TWh | **0.534×** | **NO** |
| 2025 | ±2.066 TWh | 1.194 TWh | **0.578×** | **NO** |

**A class whose whole annual output is roughly half its own tolerance cannot be
discriminated by its C1 row in either direction** — zero generation and double
generation both PASS. Compounding it, from the keeper's own scorecard: CC_CHP is
**D-10 `pinned` / `excluded_from_free`**, so the arm cannot move the free-class
score by construction (neiso-70 §3); its **2025 row is SKIPPED** on preliminary
EIA-923 (3/7 plants missing, 57 % reporting); and CHP classes are exempt from
**both** C7 and C8 by **explicit class list** — not the 2 % floor — so CHP
D-1/D-2 numbers are diagnostics and never a passed gate (the caiso-147
protective-framing correction).

---

## §3 — the construction properties (prereg §4), all PASS

| property | result |
|---|---|
| **P1 wiring, grain 1** | **PASS** — 20/602 generators, **271.008 MW**; CC_CHP cap-wt HR 8.1437 → **10.3632** (+27.25 %), CT_CHP 6.2962 → 6.7784 (+7.66 %), CC_REGULAR unmoved |
| **P2 artifact accuracy** | **PASS** — 40 rows × 22 cols (gate-3), census 22/12/5/1; CEMS **4/4 within 1 %, median 1.00000** |
| **P3 scope-gate bound** | recorded, not a gate — see §1 |
| **P4 single delta** | **PASS** — the scenario-block diff returns exactly `['measured_chp_heat_rates']`, A `false` / B `true` |
| **P5 control integrity** | **PASS on the scorecard basis** (the pre-registered gate); byte basis reported in §6 |
| **P6 firing, grain 2** | **PASS** — CC_CHP energy delta **−0.5866 / −0.3404 / −0.6533 TWh** |
| **P7 conservation** | **PASS** — full identity across `class_hourly` + storage + `system`; per-hour **relative** residual **1.6e-7 / 1.7e-7 / 1.9e-7** against the 1e-6 bar |
| **P10 substitution** | **PASS** — CC_REGULAR absorbs **103.8 % / 103.5 % / 103.9 %** |

**P6 and P7 are the two the DO-NOT-MISREAD chain demanded, and both were scored
the hard way.** Grain 1 (a fleet-loader check) is *not* sufficient proof
(miso-126(a)), so firing is proved again at grain 2 on per-class **energy**, not
on `max_abs_class_hour_mw` (miso-122 — the class-hour maxima, 567.5 / 614.6 /
796.3 MW, are reported as liveness only and are **not** a mechanism magnitude).
`tests/unit/data/test_cc_steam_part_capacity.py::TestBackcastFleetSourcing`,
which generalises the forwarding guard to **every** boolean
`ScenarioConfig`-backed keyword of `load_fleet_from_csv`, was run this session
and passes. Conservation is scored on the FULL identity, never `class_hourly`
alone (miso-126(b)).

### §3.1 — a scorer defect found and corrected against the prereg, not against the data

The first A/B run reported **P7 FAIL**. The prereg specifies a **per-hour
relative** tolerance ("any hour breaching a 1e-6 relative tolerance"); the
scorer as first written applied an **annual-sum absolute** bar of 1e-3 GWh —
something the prereg never specified. Re-implemented as pre-registered, P7
passes at 1.6–1.9e-7. The residuals sit **at the float32 epsilon (1.2e-7) of the
sidecar `mw` column**, so an absolute GWh bar on a ~100 TWh system was measuring
stored-column dtype rather than conservation. **This is a correction of the
scorer to the pre-registered definition, not a loosening of a threshold after
seeing a number** — and it is recorded here rather than silently fixed. The
annual-sum absolute residuals (+0.103 / −0.036 / +0.225 MWh) are retained in the
artifact as reported diagnostics.

---

## §4 — the result

### Dispatch (P1, TWh, B − A)

| year | CC_CHP | CC_REGULAR | absorption | λ |
|---|---|---|---|---|
| 2023 | 1.327 → **0.741** (−0.5866) | 51.971 → 52.580 (+0.6088) | **103.8 %** | 39.169 → 39.328 (+0.159, +0.405 pp) |
| 2024 | 1.293 → **0.952** (−0.3404) | 56.496 → 56.848 (+0.3521) | **103.5 %** | 43.982 → 44.075 (+0.093, +0.211 pp) |
| 2025 | 1.207 → **0.554** (−0.6533) | 57.841 → 58.520 (+0.6790) | **103.9 %** | 72.031 → 72.320 (+0.289, +0.401 pp) |

A **clean CC-pair reallocation**: CC_REGULAR takes slightly more than CC_CHP
gives up, the excess being CT_CHP's own small decline (−0.032 / −0.032 / −0.031
TWh). Nothing else moves materially; total generation, slack and dump are
unmoved. λ stays far inside the pre-registered 1.0 pp allowance and the C3a
headroom of 6.7 / 4.1 / 7.1 pp — a PASS→FAIL would have needed roughly ten times
the observed push.

### C1 grid-delivered |error| vs the committed bench (TWh)

| year | class | actual | control A | arm B | Δ\|err\| |
|---|---|---|---|---|---|
| 2023 | CC_CHP | 1.072 | 1.327 (0.256) | 0.741 (0.331) | **+0.075** |
| | CC_REGULAR | 52.360 | 51.971 (0.388) | 52.580 (0.221) | **−0.168** |
| | **CC combined** | 53.431 | 53.299 (0.133) | 53.321 (0.110) | **−0.022** |
| 2024 | CC_CHP | 1.124 | 1.293 (0.169) | 0.952 (0.172) | **+0.003** |
| | CC_REGULAR | 56.608 | 56.496 (0.113) | 56.848 (0.239) | +0.127 |
| | **CC combined** | 57.732 | 57.788 (0.056) | 57.800 (0.068) | **+0.012** |
| 2025 *(C1 SKIPPED)* | CC_CHP | 1.194 | 1.207 (0.013) | 0.554 (0.640) | +0.627 |
| | CC_REGULAR | 55.813 | 57.841 (2.028) | 58.520 (2.707) | +0.679 |
| | **CC combined** | 57.007 | 59.048 (2.041) | 59.074 (2.067) | +0.026 |

**The identified aggregate holds** — combined CC |error| improves in 2023 and
worsens by 0.012 TWh in 2024, against the pre-registered **0.50 TWh** allowance
(anchored at one quarter of the C1 band, fixed before the solve and not moved).

**And the fit cost on the repriced class is materially SMALLER than at
neiso-70** — CC_CHP |error| **+0.075** in 2023 (neiso-70: +0.145) and **+0.003**
in 2024 (neiso-70: +0.084). The 2024 row is essentially unmoved. This is measured
here, not inherited.

### The pre-registered stop-and-escalate triggers — none fires

| trigger | result |
|---|---|
| **N1** any criterion PASS → FAIL | **no** |
| **N2** re-verified determination worse (rule 22 D-5(b)) | **no** — CALIBRATED-WITH-CAVEATS in both arms |
| **N3** C3c degrades / new caveat slot | **no** — C3c bit-unchanged, 1 ledgered caveat |
| **N4** total gen ±0.05 %, slack/dump rise | **no** |

Both arms score **CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat (C3c), C1
all 12/12 · free 8/8**, criterion for criterion identical. **So rule 22 D-5(b)
does not stop this promotion** — which is precisely the test NYISO's identical
arm failed at nyiso-120, where a worse determination correctly stopped it and
escalated to the owner.

---

## §5 — disclosed against interest

1. **The prereg predicted this might fail, in advance.** It recorded that this
   keeper's CC_REGULAR error had already shrunk relative to neiso-70's control
   (−0.38 / −0.11 vs −0.471 / −0.340), so the counterweight had **less** room and
   the combined-CC improvement **might not replicate**. It **half**-replicated:
   2023 improves, 2024 worsens slightly. The pre-registered allowance is what
   made that outcome adjudicable rather than arguable.
2. **2025 is UNSCORED and would look worse if it were gated.** Arm B's
   CC_REGULAR reads 2.707 TWh against a 2.066 band while the control's 2.028 is
   barely inside — on a complete EIA-923 vintage that row would be out of band.
   But the 2025 CC-**family** overshoot is **98.7 % pre-existing** (combined
   2.041 → 2.067; this arm adds +0.026) and the pair merely re-splits it.
   **Flagged for the re-gate when the 2025 vintage finalises**, not buried.
3. **CC_CHP now sits UNDER actual in every year where it sat over.** That
   residual is real, ungated, and **currently unclosable**: its only named route
   — a measured host-steam floor — is CLOSED WITH EVIDENCE by neiso-71 (NEISO's
   merchant CC_CHP genuinely carries no host-steam obligation; the non-Kendall
   CC_CHP floor totals 15.0 MW across all seven plants, and a Kendall-based floor
   would be a FITTED parameter, rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).
4. **The CT_CHP leg is not identified in either direction.** The artifact's
   CT_CHP half covers 19.3 % of class capacity and **0.0 % of the class's metered
   CAMPD energy** — every covered CT_CHP plant is below the Part-75 boundary
   (neiso-70 §1). Its |error| moves +0.033 / +0.032 / −0.032 and is reported
   only.
5. **CHP D-1/D-2 movement is a diagnostic, not a gate**, by explicit class list.

---

## §6 — same-HEAD drift, reported rather than hidden

This is why the control exists. The committed keeper's `git_sha` **`f6238a5` is
not in the repo** (squash-merged away), so keeper-relative deltas would charge
unattributable drift to the mechanism. Control A minus committed keeper,
class-hour maxima:

| year | max \|Δ\| | largest classes |
|---|---|---|
| 2023 | 402.6 MW | CC_REGULAR 402.6, hydro 354.7, CT_PEAKER 73.2 |
| 2024 | 614.6 MW | CC_REGULAR 614.6, hydro 304.1, CT_PEAKER 61.0 |
| 2025 | 442.3 MW | CC_REGULAR 442.3, oil 378.6, hydro 364.3, CT_PEAKER 135.2 |

**A refinement on neiso-70:** there the drift was code *and* environment. Here
the numerics stack is **identical** (highspy 1.14.0, pandas 3.0.3, pyarrow
24.0.0), so the drift is **CODE ONLY** — and still cannot be decomposed further
with `f6238a5` gone. Both arms solved at HEAD `66d7b44a`, so the A/B itself is
unaffected.

---

## §7 — DOF ledger (rule 21 `[R-DOF]`)

**Zero free parameters added.** 12 → 13 entries, **`n_residual` UNCHANGED at 5**.
Both the incumbent (eGRID `PLHTRT`) and the replacement (eGRID
`(PLHTIAN + CHPCHTI)/PLNGENAN`) are **published** eGRID quantities on the **same
net denominator**, so no gross-to-net factor is involved and nothing is chosen,
tuned or swept. The only screens are the **0.50 thermal-share ceiling** (the EPA
CHP Partnership unfired gas-turbine envelope) and the **miso-122 dark-fuel scope
gate** (a measured per-unit CAMPD quantity: NEISO dark share 0.012142 / 0.009584
/ 0.014798 for 2023/24/25; the committed artifact is the 2023 vintage so 9.4423
is the number of record and no vintage is mixed).

Rule 23 `[R-FROZEN-DERIVE]` is satisfied: the artifact's last re-derive
(neiso-80) cites the miso-122 measured **scope change**, never a residual — and
no residual was consulted here in either direction.

---

## §8 — DO-NOT-REDO honoured (rule 28a)

* **No CC_CHP host-steam floor was built** and **`chp_steam_floor_p25` stays
  UNARMED.** neiso-71 closed that route with evidence; it was not re-opened to
  rescue the arm, and the CC_CHP undershoot is reported as an open residual
  instead (§5.3).
* **Kendall's capacity basis** stays ADJUDICATED-ARTIFACT (neiso-73).
* **`cc_steam_part_capacity` NEISO stays `I`** (neiso-80) and was **not stamped**
  by this session in either direction.
* `da_virtual_bids` NEISO stays `R`; `pumped_storage_cycling_depth` stays `G`.

---

## §9 — governance

* **Rule 22 `[R-HOLDOUT]`** — years **2023/2024/2025 only**. The holdout spend
  freeze is **ACTIVE**; NEISO's locked test is **SPENT and never re-grantable**
  and `locked_test_scored_on` is **not** re-keyed. **D-5(b) discharged in full:**
  the `complete` entry is re-keyed to `2026-08-04-neiso81-chpheatrate` **with a
  determination re-verification** run on committed artifacts
  (`calibration_verdict.py --run-id`, no solve) returning
  CALIBRATED-WITH-CAVEATS — **not worse**, so the promotion proceeds without an
  owner escalation.
* **Rule 22 LOYO** — zero free parameters introduced, so leave-one-year-out
  reduces to the no-held-out-degradation check; the determination is identical in
  all three years.
* **Rule 15 `[R-DASHBOARD]`** — **both** runs registered in-session, control and
  arm alike.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, one invocation per arm.
* **Rule 25 `[R-ISO-SCOPE]`** — MISO's / CAISO's / PJM's / NYISO's `K`
  transferred **nothing**; NEISO derived its own artifact from its own data and
  **no file outside the NEISO lane** was re-derived or stamped.
* **Rule 26 `[R-REGISTRY]`** — the arming is visible in `run_config.json`.
* **Rule 28b `[R-MECH-MATRIX]`** — the cell is stamped in this session
  (`O` → `K`), with its evidence citation. The row's NEISO evidence key was the
  non-canonical `NE:` (2 uses file-wide against 22 for `Q:`), so its citation did
  not render; corrected to `Q:` as part of the stamp.
* **Rule 27 `[R-PUSH]`** — Opus; every push touching a file ≥ 300 lines is
  blob-verified immediately after.

---

## §10 — what is left in the NEISO lane

**No agent-actionable lever remains.** C3c stays at its declared frontier and was
untouched (bit-unchanged between the arms). The named secondary — NEISO
**`6081_CA1`**, a 96.0 MW unit sitting in the LP as `oil` with an **empty
`plant_group`** while its three CC1-block CT siblings are CC_REGULAR/`gas_cc`,
and with CAMPD metering the block on Pipeline Natural Gas at units 001/002/003
and **no CAMPD unit for CA1 at all** — was **not** opened. It is a
**classification/repricing** question needing **its own charter** and its own
measured identification, and at 73–91 GWh/yr gross it is a **correctness**
question before a magnitude one. Everything else in §5.6 is owner-gated.
