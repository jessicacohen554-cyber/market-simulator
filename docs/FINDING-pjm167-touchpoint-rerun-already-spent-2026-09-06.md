# FINDING — pjm-167: the chartered 2022 touchpoint re-run was ALREADY SPENT; the defect that remained was a records one, and it is repaired

**Date:** 2026-09-06 · **Lane:** PJM validation touchpoint (rule 22 `[R-HOLDOUT]` step 4)
· **Branch:** `claude/pjm-2022-touchpoint-rerun-0j2ng2` · **Base:** `origin/main` @ `dbf8796b`
**LP minutes spent: ZERO.** No solve, no score, no registration, no keeper change, no marker change.
**Precedent for stopping at phase 0 with a written finding:** miso-219, miso-221, miso-222.

---

## Verdict in one line

**The session's chartered task — re-measure PJM's 2022 validation touchpoint against the
corrected input clock — had already been executed on 2026-09-05, one day before this session
opened, and is registered.** Its answer is that the input-clock repair does **not** close 2022:
`CC_REGULAR` moved **+18.28 → +22.26 TWh** and C3b NRMSE **0.206 → 0.250**, i.e. the rung got
*worse* on the corrected instrument. Re-solving would have spent ~40–70 min of LP to reproduce a
committed number. What was genuinely outstanding was a **records defect** — the PJM keeper shard
still pointed at the superseded, since-pruned touchpoint — and that is repaired here.

---

## 1. Preconditions — checked in the chartered order, before anything else

All four pass; the lane was legitimately open, and it is closed on evidence rather than on a gate.

| # | precondition | source of truth | result |
|---|---|---|---|
| 1 | PJM holds `complete` (validation tier authorized) | `calibration-complete.json` → `complete.PJM` | **HELD**, declared 2026-07-31 |
| 2 | the spend freeze does not cover the validation tier | `holdout-freeze.json` → `holdout_policy.frozen_tiers` | **`frozenset({'locked_test'})`** — validation not frozen |
| 3 | `tier_for_year(2022) == validation` | `scripts/lib/holdout_policy.py` | **`validation`** |
| 4 | `final` marker / locked test | `calibration-complete.json` → `final` | **absent** — `_note` only; 2019 + H1-2026 untouched by this session |

The R-AZ registration-time gate (`holdout_policy.registration_refusals`, owner ruling 2026-09-06)
was noted and never reached: **no run was produced, so nothing was registered.**

## 2. Phase 0 — the chartered task is already spent

`ls frontend/data/backcast/registry/ | grep -i pjm` returns exactly two sidecars, and the second
one is the chartered work:

| run | years | bundle | determination |
|---|---|---|---|
| `2026-08-15-pjm-162-inputclock` | 2023, 2024, 2025 | `pjm_debugb_inputclock_A` | CALIBRATED (the keeper) |
| **`2026-09-05-pjm-2022-2021-touchpoints`** | **2022, 2021** | `pjm_tp2022_2021_k162` | **NOT-YET** |

The touchpoint solved at `46e08e5b` (2026-09-05), well after the ≤2022 clock extension was
executed on 2026-08-16, so it **is** on the corrected instrument. Its own sidecar states the
result rather than leaving it to be inferred — `holdout.supersedesNote`, verbatim:

> *THE STALE RUNG'S DIAGNOSIS DOES NOT CLOSE. The prior 2022 touchpoint measured the pjm-152
> recipe on the PRE-REPAIR input clock and failed on C1 CC_REGULAR +18.28 TWh and C3b NRMSE 0.206.
> The keeper has since moved to pjm-162 …*

### 2.1 The measured answer to the chartered question

| rung | determination | failing criteria |
|---|---|---|
| **2022** | NOT-YET | C1 `CC_REGULAR` **+22.26 TWh** (share +1.7 pp); C3b NRMSE **0.250**. C2, C3a, C3c, C4, C6, C8 PASS; C5a CO2 +4.8 % |
| **2021** | NOT-YET | C1 (`CC_REGULAR` +28.72 / `ST_GAS` +8.07 / `COAL_BIT` −9.45 TWh); C3a **+25.7 %**; C3b 0.355. C2, C4, C6, C8 PASS; C3c ledgered caveat under rubric v3.6 |

**The repair moved the rung backwards on both failing criteria.** That is the honest reading and
it is reported at full magnitude: pjm-162 *is* the named repair for the stale rung's diagnosis, and
the rung fails the same two criteria with `CC_REGULAR` ~4 TWh larger. The charter's premise — that
the corrected clock was the missing ingredient — is **refuted by measurement**, not deferred.

**The scope was also wider than the charter knew: 2021 was walked in the same bundle**, and its C1
signature runs the same direction as 2022's on gas (`CC_REGULAR` over), with `COAL_BIT` under in
2021.

> **CORRECTED 2026-09-06, AGAINST INTEREST — this paragraph originally read that 2021's signature
> ran "on the year with the cheapest delivered gas in the span", that "two rungs pointing the same
> way is a merit-order-position object", and that this was "a better lead than the DA-virtual
> layer pjm-162 was built around". ALL THREE ARE MEASURED FALSE**, by a session that landed on
> `main` while this one was open (`pjm-166`, the log entry immediately above this one in
> `docs/calibration-log/pjm.md`). The clause was inherited from the registered sidecar's own note
> rather than measured here, and it should have been checked before it was repeated.
> **(a)** On EIA-923 delivered receipts **2021 and 2022 are the two DEAREST-gas and two
> CHEAPEST-coal years of 2021-2025** — gas $4.12 / $7.12 (ranks 4 and 5) against $3.26 / $2.85
> (ranks 2 and 1) in 2023/2024 — the opposite of the claim.
> **(b)** The merit-order-position reading is **refuted on three independent zero-LP tests**: the
> sign test fails (`CC_REGULAR` over-runs +28.7 / +22.3 TWh in the two dearest-gas years and only
> −3.4 / +0.5 TWh in the two cheapest); the in-sample elasticity is already right (coal share on
> `ln(g/c)`, slope ratio **0.888**, intercept gap −0.0007); and coal is not saturated (model coal
> at 0.25-0.68 of its own annual peak in 2021's high-`ln(g/c)` months, on a *larger* fleet).
> It is **not a reordering at all but an ADDITIVE FOSSIL SURPLUS** — +19.6 / +26.7 TWh held-out
> against −3.7 / −7.9 in-sample, with model demand inside ±2.2 TWh in every year.
> **(c)** The DA-virtual layer is in fact the **better** lead, not the worse one: it is the *only*
> model quantity that crosses the tier boundary (net cleared position +7.40 / +6.48 / −0.89 TWh
> in-sample against −6.14 / −9.91 held-out, sign agreement 5 of 5 years), bounding ~21 % of 2021's
> and ~44 % of 2022's `CC_REGULAR` miss.
> A further correction to the standing narrative, from the same session: **coal-under is 2021
> ONLY** — 2022 coal is +2.0 TWh, slightly *over*. §8 below is superseded; see §10.

## 3. What was actually outstanding — a live records defect, now repaired

### 3.1 The defect

`frontend/data/backcast/keepers/PJM.json` carried a hand-authored `holdout_touchpoint` block
naming **`2026-08-05-pjm-2022-touchpoint`** — a run pruned under the 2026-09-05 keeper-only
retention directive (rule 15 `[R-DASHBOARD]`). `scripts/build_status.py:574` copies that block
through to the status part **verbatim, without validating it against the registry**, and
`docs/codebase-site/js/calibration-status.js:406` renders it.

Net effect on the live PJM Calibration Status card — **two different 2022 numbers, stacked**:

| panel | source | 2022 reading | run link |
|---|---|---|---|
| `HOLDOUT 2022` (rendered first) | hand-authored shard block | C1 **+18.28 TWh**, C3b **0.206** | → `2026-08-05-pjm-2022-touchpoint` — **pruned, dead link** |
| `HOLDOUT LADDER` | derived from the registry | C1 **+22.26 TWh**, C3b **0.250** | → the live run |

The irony is on the record: the ladder's own source comment says it is derived *"so it cannot go
stale against what was actually scored"* — directly beneath a block that was exactly that stale.

### 3.2 The repair, and why deletion is the right shape rather than re-authoring

`holdout_touchpoint` is **removed** from `keepers/PJM.json`; `build_status.py --iso PJM` rebuilt
the status part. Three reasons, none of them convenience:

1. **Rule 30 `[R-TOUCHPOINT-FOLD]` clause (b) names this exact shape as wrong** — the duty is to
   *"rebuild and commit the status part, **never to hand-author a block that would go stale the
   moment a rung is re-spent**."* The block is that hand-authored block.
2. **The derived ladder strictly dominates it.** The ladder carries year, tier, determination,
   per-year note, reasons, run id and caveat — everything the panel showed, *per year* rather than
   one run-level verdict, and auto-derived so it cannot drift.
3. **ERCOT is the precedent.** ERCOT has spent 2022 touchpoints and carries a ladder with **no**
   `holdout_touchpoint` block. Four of six ISOs already have none. Removal moves PJM onto the
   established shape rather than inventing one.

**Verified after the repair** (all on the rebuilt part): `holdout_touchpoint` absent; ladder
present with both the 2021 and 2022 rungs; **zero** remaining references to the pruned run id.

### 3.3 Gates

| gate | result |
|---|---|
| `audit_keepers.py --iso PJM --check` | **PASS — 0 failures, 0 warnings** (keeper, holdout, marker, status all ✓) |
| `check_registry_payload_parity.py` | **OK** — 14 runs checked, 47 bundle dirs swept, 0 known-unsynced tolerated |
| `check_mechanism_matrix.py` | **exit 0**; its 244 anchor warnings are **pre-existing** — measured identical on a clean stash of `origin/main`, and this session adds no `ScenarioConfig` field |

## 4. NEISO carries the identical defect — ROUTED, not fixed here

The same query across all six shards finds the pattern is **not** PJM-only:

| ISO | `holdout_touchpoint.run_id` | in registry? |
|---|---|---|
| **PJM** | `2026-08-05-pjm-2022-touchpoint` | **PRUNED** → repaired here |
| **NEISO** | `2026-08-06-neiso-2022-corrected-basis` | **PRUNED** → *not this lane's file* |
| ERCOT, CAISO, MISO, NYISO | *(none — ladder only)* | — |

NEISO's was already routed once, at capx director refresh **r#41** (*"`keepers/NEISO.json.holdout_touchpoint`
still names the pruned 2026-08-06 run … ROUTED to the audit/calibration desk"*), and is still
open. It is **left untouched** here on lane discipline: `frontend/data/backcast/keepers/README.md`
and rule 25 `[R-ISO-SCOPE]` confine a lane to its own ISO's shard. The repair is one line — delete
the block, rerun `build_status.py --iso NEISO` — and NEISO's ladder already carries all three rungs.

## 5. A guard is warranted but is NOT landed here, deliberately

Nothing catches this class. `audit_keepers.py`'s **H1** checks holdout *quarantine* (registered
bundle years against tier markers); no check asserts that a keeper shard's referenced run ids
**exist in the registry**. A ~5-line referential-integrity check would close it permanently.

**It is not landed in this PR because CI runs `audit_keepers.py --check` across every ISO**
(`.github/workflows/ci.yml:124`, no `--iso`), so the guard would immediately fail on NEISO's
still-open block and red `main` for a defect this lane is barred from fixing. The correct order is
**NEISO's repair first, guard second** — the two belong in the NEISO lane's PR together. Filed for
that lane rather than silently dropped.

## 6. The ONE open limit on PJM's touchpoints — and why it is harder than the assessment assumed

`ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05.md` §4(i) leaves PJM's HEAD-drift limit
open and its §5 item 2 recommends closing it with a same-HEAD in-sample control solve. NEISO's
equivalent was measured **INERT**, and the verdict does not transfer (rule 25).

Rule 29 `[R-SCREEN]` clause (b) directs the cheaper instrument first: **G-DRIFT**, a hunk-level
code audit from the keeper's solve commit to HEAD, at zero LP. **That instrument is not
dischargeable for PJM as recorded**, and the reason is structural rather than effort:

| baseline the keeper records | probe | result |
|---|---|---|
| `meta.json` → `git_sha` = **`457ae04`** | `git cat-file -t` | *not a valid object* — a **7-char pre-rewrite prefix**, and CLAUDE.md warns short prefixes may now resolve **WRONG** |
| `meta.json` → `basis_sha` = **`c447199c9009…35454`** (full 40) | `git cat-file -t`; direct `git fetch origin <sha>` | **unresolved**; the targeted fetch did not return within ~3 min and was abandoned |
| both shas | `docs/governance/citation-commit-map.txt` | **absent from the map** (95 mapped entries; neither is one) |

The keeper solved **2026-08-15**, one day *before* the 2026-08-16 `cleanup-large-blobs` history
rewrite, so its baseline is exactly the class of citation the rewrite finding declares dead.
This clone is additionally **shallow** (511 commits, back only to 2026-09-04), so no pre-09-04
commit is present locally regardless.

**Stated against interest:** this does **not** prove the object is permanently gone from the
remote — only that it is not obtainable in this session by the two routes available (local
resolution, targeted fetch) and is not in the map that exists to survive the rewrite. A deeper
`--unshallow` was not attempted; CLAUDE.md's clone guidance makes that a 5.46 GiB transfer and it
is out of proportion to the question.

**Consequence under rule 29(b):** an unclassifiable drift audit is treated as **LIVE**, and a LIVE
hunk is what earns a control solve. So PJM's control solve *is* authorized — this is the same
place the NEISO lane landed, by a different route (its diff was 120 files / +119 k lines and it
declared the audit undischargeable at reasonable cost, then solved the control and measured it
inert). **It is an owner/operator call, not this session's to spend**: ~35–70 min of LP whose only
product is closing a stated limit on a diagnostic number that rule 22 already forbids quoting as
skill, and rule 30(c) already forbids from downgrading the ISO.

## 7. What this session did NOT do

* **No solve, no score, no registration.** No LP minute was spent. The 2022 and 2021 rungs stand
  exactly as registered on 2026-09-05; nothing was re-spent and nothing re-scored.
* **No keeper change and no marker change.** PJM's keeper is `2026-08-15-pjm-162-inputclock`,
  unchanged; `complete` is untouched; `final` remains empty and the locked test (2019, H1-2026) is
  neither granted nor spent, for PJM or any ISO.
* **No mechanism was tested, so no matrix cell verdict moves** (rule 28 duty d, and the
  miso-221/222 precedent that sizing or refuting around a mechanism moves no verdict). No
  `ScenarioConfig` field is added (duty c).
* **No tuning of any kind.** Rule 30(c) governs the reading of the rungs: a held-out year never
  downgrades the ISO, and PJM's determination remains the train-tier verdict — **CALIBRATED**.

## 8. Successor — SUPERSEDED, see §10 (kept for the record, do not act on it)

The object is **PJM's gas-over / coal-under C1 signature**, visible in the *same direction* on
both held-out rungs (`CC_REGULAR` +22.26 TWh in 2022, +28.72 TWh in 2021, with `COAL_BIT`
−9.45 TWh in 2021) against a tuned window where C1 passes clean. Rule 22 step 3 sends that to
**2023–2025** — the only place fitting ever happens — and never to the touchpoint year.

Two prep items remain unrestricted and marker-free (rule 22 as amended 2026-08-06: what is held
out is the score, never the data): PJM 2020 is **not data-ready** on three measured blockers (an
inflated zonal demand feed, a missing `calibration_reference` block, a missing renewable-capacity
file), and the PJM 2021 int32 sentinel (2,147,480,064 MW in three hours) is located but unfixed —
fixing it re-renders PJM's committed benchmark, so it needs its own re-render decision.

## 9. Addendum — re-scored from committed artifacts, and one new observation for the successor

`scripts/calibration_verdict.py --run-id 2026-09-05-pjm-2022-2021-touchpoints` was run at HEAD
(committed artifacts only, **no solve**) to check the quoted numbers against the scorer rather
than against sidecar prose. **Every figure in §2.1 reproduces exactly**, and the determination
basis is confirmed as **three** failing criteria, not four:

> `determination basis: undocumented out-of-tolerance (FAIL) criteria: fuelmix, price_mean, price_shape`

C3c reads **CAVEAT — ACCEPTED MODEL-CLASS LIMITATION** (2021: model 145 h vs RT actual 23 h,
6.30×), auto-applied under the rubric v3.6 holdout clause with the governance gate passing.

**A vintage note, benign but worth stating:** the bundle's committed
`results/calibration/pjm_tp2022_2021_k162/metrics.json` still carries the **solve-time** stamp
(`rubric_version: 3.5`, `fails: 4`, C3c counted as a failure). The registered sidecar, the derived
ladder and this re-score all carry **v3.6**. The sidecar is the scored surface and it is correct;
the bundle metric is simply the older stamp. Nothing is mis-stated on the dashboard.

### 9.1 NEW, and directly relevant to the successor — the two rungs diverge sharply on diurnal amplitude

The scorer's `D-A` row (REPORTED-ONLY and **band-free**, so this is a diagnostic and **not** a
gate, and nothing here is or may become a tuning target):

| rung | model hod range | measured hod range | **amplitude vs measured** | hod r | phase |
|---|---|---|---|---|---|
| 2021 | $28.65 | $25.42 | **112.7 %** | +0.881 | peak h16 vs h17, trough h02 vs h02 — OK |
| 2022 | $28.18 | $46.40 | **60.7 %** | +0.960 | peak h16 vs h17, trough h02 vs h01 — OK |

**The model's own diurnal range is essentially flat across the two years ($28.65 vs $28.18) while
the market's nearly doubles ($25.42 → $46.40).** The rungs fail C1 in the *same* direction
(gas over, coal under) but sit on opposite sides of the amplitude comparison, so amplitude is not
simply tracking the C1 miss.

This is the **flat-offer-stack signature** the keeper's own note item (15a) already diagnoses
in-sample — *"nothing in the model's offer varies by hour … the entire intra-day amplitude comes
from merit-order traversal"* — now visible out-of-sample, and it is the natural companion to
2022's C3b NRMSE 0.250. Recorded as evidence for the §8 successor, **not** as a new lever: item
(15a) states the lever queue for that defect is empty with no open successor, and rule 22 step 3
sends any work on it to **2023–2025**, never to a touchpoint year. It moves **no** matrix cell
verdict (rule 28 d — no mechanism was tested).

---

## 10. Superseding note — `pjm-166` landed on `main` while this session was open

This session was numbered `pjm-166` when it began. A different session took that number on `main`
first (`## pjm-166 — 2026-09-06 — the held-out C1 object is NOT a merit-order-position object`),
so this one is renumbered **pjm-167** and its finding file renamed to match. Nothing in §§1–5
changes; §§6 and 8 do.

**§8's successor is SUPERSEDED — do not take the C1 signature to 2023–2025 as a merit-order
object.** `pjm-166` did exactly that, zero-LP, and refuted it on three independent tests (see the
against-interest correction in §2.1). The live object it names instead is the **DA-virtual layer's
net cleared position** — the only model quantity that crosses the tier boundary, +7.40 / +6.48 /
−0.89 TWh in-sample against −6.14 / −9.91 TWh held-out, i.e. 6–10 TWh of net phantom **demand**
that physical gas must serve, against the mechanism's own rule-13 anchor of ≈0 at actual DA
prices. That is **pjm-158's own standing warning realized out of sample**. Its cell
`da_virtual_bids` **stays `K`** (evidence append only, rule 28 d), and its root cause — the LP
carries one price series gated as RT while the curve needs a DA price — is an **architecture
question escalated to the owner** inside PJM's owner-declared-closed price-formation frontier.
At pjm-158's own measured channel gain it bounds ~21 % of 2021's and ~44 % of 2022's `CC_REGULAR`
miss; **55–79 % stays unexplained**, and that session explicitly does not claim otherwise.

**§6 is INDEPENDENTLY REPLICATED and can be closed as a question.** `pjm-166` reached this
session's G-DRIFT conclusion separately and by a stronger route: `457ae04` does not exist at HEAD,
is absent from `citation-commit-map.txt`, and **the clone was deepened to 11,640 commits without
resolving it** — a step this session judged out of proportion and therefore left as an honest
"unobtainable here" rather than "gone". Their deepening settles it. Their framing is also sharper
than §6's and is adopted: there is **no diff to classify**, which is a stronger condition than
NEISO's "too large to classify". They then spent the control this session flagged as owner-court
(`pjm_headctrl_k162`, keeper recipe on 2023–2025 only, no `--holdout-authorized`, thresholds fixed
in a PRECOMMIT beforehand, bundle deleted before merge per rule 29 c). **So §6's owner-court item
is DISCHARGED — do not re-raise it, and do not re-spend that control.**

**What stands from this session, unaffected:** the phase-0 result that the chartered re-run was
already spent (§2); the measured verdict that the input-clock repair does not close 2022 (§2.1);
the records repair and its gates (§3); the NEISO routing and the deliberately-unlanded guard (§§4–5);
and the re-score plus the out-of-sample diurnal-amplitude divergence (§9). The amplitude
observation in §9.1 is **complementary** to `pjm-166`'s additive-fossil-surplus reading rather than
in tension with it: a surplus of fossil energy and a compressed price amplitude are the two faces
of a flat offer stack, which is keeper note (15a)'s in-sample diagnosis seen from out of sample.
