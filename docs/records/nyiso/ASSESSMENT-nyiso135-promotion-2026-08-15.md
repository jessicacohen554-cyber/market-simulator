# ASSESSMENT nyiso-135 — PROMOTION of `2026-08-08-nyiso-133-cod-arm`, and a TRANSPORT GAP that deferred two doc stamps

**Session nyiso-135, 2026-08-15.** Owner ruling in session, verbatim: *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity improves
but gates regress that may still be a keeper."*

**NO SOLVE RAN.** Governance promotion over the A/B pair nyiso-133 built,
pre-registered and adjudicated, then left recommended-pending-owner. Rule 22
`[R-HOLDOUT]`: nothing outside 2023–2025 was solved, scored or registered, and the
ACTIVE holdout spend freeze was checked and is untouched.

---

## 1. WHAT THE PROMOTION IS (built and verified in-session; see §3 for what landed)

| file | change |
|---|---|
| `frontend/data/backcast/keepers/NYISO.json` | keeper → `2026-08-08-nyiso-133-cod-arm`; full promotion note; `superseded` chain extended |
| `frontend/data/backcast/status/NYISO.js` | rebuilt by `build_status.py --iso NYISO` (NYISO `CALIBRATED-WITH-CAVEATS`) |
| `frontend/data/backcast/calibration-complete.json` | NYISO `keeper` re-keyed + `determination` re-verified + `keeper_at_prior_rekey` + `rekey_history` (rule 22 D-5(b)) |
| `docs/codebase-site/data/mechanism-matrix/NYISO.js` | `vre_registry_cod_date_basis` **`O` → `K`**; keeper/updated stamps; column re-stamp block |

Verified semantically, not just by diff: in `calibration-complete.json` **only**
the NYISO block changed — `note`, `intake_log`, `withdrawn` and **`final` are
byte-identical**, and NEISO/PJM are identical. Exactly four NYISO fields moved
(`keeper`, `determination`, `keeper_at_prior_rekey`, `rekey_history`); none removed.

**Gates, all on committed artifacts, no solve:**

* `calibration_verdict.py --run-id 2026-08-08-nyiso-133-cod-arm` → **CALIBRATED-WITH-CAVEATS**
* `audit_keepers.py --iso NYISO` → **0 failures, 0 warnings**
* `check_mechanism_matrix.py` → integrity OK, anchors OK, **keeper stamps match**, §5.x prose headers OK
* `build_status.py --iso NYISO` → rebuilt, NYISO `CALIBRATED-WITH-CAVEATS`

## 2. THE PROMOTION RECORD


## 2026-08-15 — nyiso-135 PROMOTION: keeper → `2026-08-08-nyiso-133-cod-arm` (market-solar in-service DATE basis)

**Owner ruling, verbatim:** *"Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still be a
keeper."* The nyiso-133 session's own recommendation was **PROMOTE**, and the
standing structure-over-gates clause is **not needed** — no gated criterion
regresses.

**NO SOLVE RAN.** This is a **governance promotion** over the A/B pair nyiso-133
registered, pre-registered and adjudicated, and then held pending the owner's
call. No new mechanism was tested; exactly **one cell verdict moves**
(`vre_registry_cod_date_basis` NYISO `O` → `K`).

**What is armed.** `nyiso_solar_registry_cod_dates` — the market-solar registry
ramps each plant on its **commercial operation** date (EIA-860 `Operating
Month`) instead of the Gold Book Table III-2a *"In-Service Date"*, which is a
**registration / interconnection-service** date that **leads** the metered
commercial start. Rule 14 `[R-ACCURATE]` in its reconciled-real-data form: two
published registries disagree on one field and a **third** published series
(EIA-923 first metered output) adjudicates — it agrees with EIA-860 in **11 of
the 12 uncensored plants**, and the lead is **signed both ways** (Darby −1,
Stillwater −3 against Morris Ridge +2, High River +1, East Point +1), so it is a
basis difference and not a one-directional correction toward the residual.
Membership and nameplate stay **100 % Gold Book**; only the switch-on month
moves. **Zero free parameters** — a 15-row registry identity, each row verified
on nameplate agreement and **dropped** (keeping its Gold Book date) rather than
guessed when it fails (Albany County Solar 2 is the one unmatched unit). DOF
ledger **36 → 37**, `n_residual` **unchanged at 6**, identification `published`.

**Verdict grain — nothing regresses.** Determination **UNCHANGED** at
`CALIBRATED-WITH-CAVEATS`, all 8 criterion statuses identical, **C3c the lone
ledgered caveat at 1 of 1 and BIT-UNCHANGED at 21 / 3 / 24 h** against actual
10 / 12 / 42, so no C3c evidence moved and no new slot is spent. Re-verified
2026-08-15 with `calibration_verdict.py --run-id` on **committed artifacts only,
no solve**, per rule 22 D-5(b) — the worse-determination stop does not fire.
C3a reads +8.8 / +0.8 / −3.4 %. All seven pre-registered gates PASS: K1 exactly
**one** differing `scenario_config` field of 703; K2 zero slack/dump; K3
liveness 1.0118 / 0.8746 / 1.0000 against *ex-ante* predictions of
1.0118 / 0.8746 / 1.0000; K4 wind identical; K5 no status regression; K6 C3c
bit-unchanged; K7 C8 PASS with no forced share rising (ST_GAS-2024 24.5 →
24.4 %). Hourly grain at full size: demand-weighted ΔLMP −0.0023 / +0.0345 /
0.0000 $/MWh, max zonal |ΔLMP| 4.55 / 5.67 / 0.00, and **2025 is
bit-identical** — the construction's own prediction, since the 2025 registry is
flat and the two bases coincide. The paired control reproduces the superseded
keeper **exactly** (max |class-year delta| 0.000 GWh) on a toolchain **matching**
the keeper bundle's recorded one, so unlike nyiso-132 there is no drift excuse
available and the delta is attributable to the armed field alone.

**Reported against interest.** Solar vs the published Gold Book Net Energy goes
+20.9 / +33.2 / −0.1 % → **+22.3 / +16.5 / −0.1 %**: 2024 improves by half and
**2023 gets worse**. That was written into the prereg as **ADV-1 before the
solve** and expressly ruled out as grounds for rejection — the band
(`calibration_verdict.VRE_TOL`) is **report-only** and D-10 classes NYISO solar
`delivered_pinned` ("advisory-only, excluded from skill claims"), so no gated
criterion moves on it (rule 1 `[R-STRUCT]`). **The signature that this is a
repair and not a fit is the coherence, not the level:** the implied fleet CF the
published energy demands goes from 0.1629 / 0.1473 (adjacent years disagreeing
by 10 %) to **0.1613 / 0.1641** (agreeing to 1.7 %) — a quantity nothing in the
construction targets. Second cost, disclosed: 2023 year-end registered capacity
rises **174.4 → 194.4 MW** (Stillwater meters 745 MWh in Dec-2023), so "year-end
capacity is invariant" holds for 2024 and 2025 only.

**Refuted and not built (rule 26 `[R-DELETE]`).** nyiso-132's named successor —
*"the model has no commissioning curve"* — was measured **nationally** before any
mechanism was written: 730 single-vintage EIA-860 `OP` PV plants ≥ 5 MW (36.4 GW,
COD 2019–2022) against their own EIA-923 monthly history, two-way normalized, give
age-0/1/2-month ratios **0.723 / 0.962 / 0.995** on a 36–47-month **placebo of
1.0072**. A new utility PV plant is at **mature output from its second month**;
the entire commissioning shortfall is 0.321 month-equivalents ≈ **11 %** of the
effect it was named to explain. No commissioning curve exists and none is built.

**What this promotion does NOT do.** It does not close, narrow or re-open C3c —
the tail is bit-unchanged, the diagnosed owner is unchanged (100 % of the
modelled tail is Long Island inside HB14-21 with both Zone-K import paths at
their bound), and the successor remains the **chartered joint reconciliation** of
the Zone-K transfer bound and the downstate ST_GAS `min_gen` floor under rule 19
`[R-ONE-MECH]`. **Do not re-test the bare number swap** —
`nyiso_li_tsl_n11_security` is `R`, killed on gate K6 at nyiso-130. It does not
restore frontier status (**cleared 2026-08-06, stays cleared**). It does not touch
the holdout posture: `complete` (**validation ONLY**), **absent from `final`**, and
the **ACTIVE spend freeze** independently blocks every out-of-training solve, score
and registration. This promotion **grants, spends and re-arms nothing**.

**Deferred, flagged, NOT done — first item for the next session.** nyiso-133 §9
recommends collapsing the gate to **unconditional** on promotion (rule 26: a
default-off gate whose *off* position is the **less accurate** basis is a
re-armable wrong answer). nyiso-135 did **not** do it, for two stated reasons:
(a) it is an owner decision nyiso-133 explicitly flagged and did not take, because
collapsing it **re-stales the NYISO forecast lane's 11 committed hindcast
sidecars** (rule 15's separate namespace, its own governance); and (b) this
session had **no `git fetch`** — the environment carries no git credentials — so
`src/market_sim/config/scenarios.py` could not be rebased onto a `main` that had
advanced **19 merged PRs**, and editing a >300-line core file off a stale base is
precisely the rule 27 `[R-PUSH]` hazard. **The promoted keeper carries the flag
`True` in its own `run_config.json`**, so the designated keeper is correct either
way; only the DEFAULT is deferred.

**Gates run (all green, committed artifacts only).**
`calibration_verdict.py --run-id 2026-08-08-nyiso-133-cod-arm` →
`CALIBRATED-WITH-CAVEATS`; `audit_keepers.py --iso NYISO` → 0 failures /
0 warnings; `check_mechanism_matrix.py` → integrity, anchors, keeper stamps and
§5.x prose headers all OK; `build_status.py --iso NYISO` rebuilt the shard
(NYISO `CALIBRATED-WITH-CAVEATS`). Only NYISO's shard, status and matrix column
were touched (rule 25 `[R-ISO-SCOPE]`).

**Lever queue after this promotion.** (1) the chartered **JOINT Zone-K
transfer-bound + downstate ST_GAS `min_gen` reconciliation** (rule 19) — open,
needs its own owner charter **and** pre-registration before any solve; (2) the
**FLEET-CF COMPOSITION** object this promotion's own finding opens, **replacing**
the refuted commissioning-curve item — after the date repair 2023 and 2024 both
imply fleet CF **~0.162** against 2025's **0.1955**, while measured mature
per-plant CF is 0.174–0.182 for the 2021–22 small fixed-tilt NY8 units and
0.198–0.221 for the 2024 tracking plants (Morris Ridge 0.1998, High River 0.1983,
East Point 0.2207), so a single ISO-wide `RENEWABLE_AVG_CF` cannot track a fleet
whose technology mix goes 100 % fixed-tilt → 56 % large tracking across the span.

**Still open and unchanged from nyiso-134:** the ACTIVE holdout freeze (the sole
blocker on the 2022 touchpoint, which is otherwise **data-ready**); the
import-tranche 719 MW duration RMSE disclosure, **still not re-measured** — grade
it before quoting any 2022 result; and the Transco Dec-2022 Elliott hole,
unfixable from the free archive — disclose before quoting any Dec-2022 or
winter-tail number.

* Next number: **nyiso-136**.

---

## 3. TRANSPORT GAP — WHAT ACTUALLY LANDED, AND WHAT DID NOT

**This session had no git credentials.** `git fetch` and `git push` both fail with
`could not read Username for 'https://github.com'`; there is no `GITHUB_TOKEN`, no
credential helper and no `gh` CLI. The only working transport was the GitHub MCP
API, which requires re-emitting each file's full content and caps a payload at
~457 KB.

**ONLY THIS FILE LANDED.** The four governance files in §1 were built, verified
green and committed LOCALLY, but could not be pushed, and are **not claimed as
landed**. The minimum governance-consistent set is **mutually dependent** and
totals ~276 KB: `check_mechanism_matrix.py` FAILS if the keeper shard moves
without the matrix shard, and rule 22 D-5(b) forbids the promotion commit landing
without the `calibration-complete.json` re-key. **No valid subset exists**, and
re-emitting a 340-line file plus its mandatory rule 27 blob verification did not
fit this session. Landing a half-promotion would have left the branch in an
inconsistent governance state, so this commit is deliberately **additive only**.

Two further files are over the API cap outright and could not have been pushed
even with unlimited room:

| file | size | note |
|---|---:|---|
| `docs/mechanism-testing-matrix.md` | 879 KB | over the ~457 KB cap on its own |
| `docs/calibration-log/nyiso.md` | 406 KB | would not fit alongside the governance files |

Their edits were made, verified green, and then **reverted rather than left as
local-only changes**, because this container is ephemeral and an unpushed edit is
lost, not pending. Their content is preserved verbatim below.

### 3a. Pending edit 1 — append §2 above to `docs/calibration-log/nyiso.md`

Append the whole of §2 verbatim to the end of the file. It already ends with the
`* Next number: **nyiso-136**.` line, so nothing else is needed.

### 3b. Pending edit 2 — re-stamp the NYISO §5.5 prose header

In `docs/mechanism-testing-matrix.md`, the single line beginning `### 5.5 NYISO —`
must be REPLACED by the text below, followed by `**(PRIOR HEADER, nyiso-132,
unedited below.)** ` and then **the existing header's text from `KEEPER 2026-08-08
(nyiso-132):` onward, verbatim** (i.e. the old line minus its own `### 5.5 NYISO — `
prefix). This is what `check_mechanism_matrix.py` checks; it was applied and
verified green in-session before the revert.

```
### 5.5 NYISO — **KEEPER 2026-08-15 (nyiso-135): `2026-08-08-nyiso-133-cod-arm`, arming the market-solar in-service DATE BASIS (`nyiso_solar_registry_cod_dates`).** `vre_registry_cod_date_basis` NYISO **`O` → `K`**. A **GOVERNANCE promotion** on the owner's in-session ruling — nyiso-133 built, pre-registered and A/B'd the arm and left it *recommended pending the owner*; **nyiso-135 ran no solve and tested no new mechanism**, so exactly one cell verdict moves and the open-gate set is unchanged. Rule 14 `[R-ACCURATE]` in its **reconciled-real-data** form with **ZERO free parameters** (DOF 36 → 37, `n_residual` unchanged at 6, identification `published`): the Gold Book Table III-2a *"In-Service Date"* is a **registration / interconnection-service** date that **leads** the plant's metered commercial start, and EIA-860's `Operating Month` matches that start — adjudicated by a **third** published series, EIA-923 first metered output, which agrees with EIA-860 in **11 of the 12 uncensored plants**, with the lead **signed both ways** (Darby −1, Stillwater −3 against Morris Ridge +2, High River +1, East Point +1), so it is a *basis difference*, not a one-directional correction toward the residual. Membership and nameplate stay **100 % Gold Book**; only the switch-on month moves. **ALL SEVEN pre-registered gates PASS** (K1 exactly one differing config field of 703; K3 liveness 1.0118 / 0.8746 / 1.0000 against *ex-ante* predictions of 1.0118 / 0.8746 / 1.0000; K6 **C3c bit-unchanged** at 21 / 3 / 24 h; K7 C8 PASS, no forced share rises). Determination **UNCHANGED** at `CALIBRATED-WITH-CAVEATS`, all 8 statuses identical, **C3c the lone ledgered caveat 1 of 1**, re-verified per rule 22 D-5(b) so the worse-determination stop does not fire. **The control reproduces the superseded keeper EXACTLY** (max |class-year delta| 0.000 GWh) on a **matching toolchain** — no drift excuse available, unlike nyiso-132 — and **2025 is BIT-IDENTICAL**, the construction's own prediction since the 2025 registry is flat. **Reported against interest:** solar vs published goes +20.9 / +33.2 / −0.1 % → +22.3 / **+16.5** / −0.1 % — 2024 halves, **2023 worsens**, pre-registered as ADV-1 *before* the solve on a **report-only** band for a D-10 **pinned** class; the repair signature is **coherence, not level** (implied fleet CF 0.1629 / 0.1473, 10 % apart → 0.1613 / 0.1641, 1.7 % apart — a quantity nothing in the construction targets). Disclosed: 2023 year-end capacity 174.4 → 194.4 MW. **REFUTED and NOT BUILT** (rule 26 `[R-DELETE]`): nyiso-132's named successor *"the model has no commissioning curve"* — 730 single-vintage EIA-860 PV plants (36.4 GW, COD 2019–2022) two-way normalized against their own EIA-923 history give age-0/1/2-month ratios 0.723 / 0.962 / 0.995 on a **1.0072 placebo**, so a new plant is at **mature output from its second month** and the entire shortfall is 0.321 month-equivalents ≈ **11 %** of the effect it was named to explain. **DEFERRED, FLAGGED, NOT DONE:** nyiso-133 §9 recommends **collapsing the gate to unconditional** on promotion (a default-off gate whose *off* position is the less accurate basis is a re-armable wrong answer); nyiso-135 did **not**, because it is an owner decision with a NYISO **forecast-lane** blast radius (11 committed hindcast sidecars) and no `git fetch` was available to rebase `scenarios.py` onto a main 19 PRs ahead (rule 27 `[R-PUSH]`) — the keeper carries the flag **TRUE in its own `run_config.json`**, so only the DEFAULT is deferred. **Holdout unchanged:** `complete` (validation ONLY), **ABSENT from `final`**, and the **ACTIVE spend freeze** blocks every out-of-training solve, score and registration. **LEVER QUEUE:** (1) the chartered **JOINT Zone-K transfer-bound + downstate ST_GAS min_gen reconciliation** (rule 19) — still open, still needs its own owner charter **and** pre-registration before any solve, and **do not re-test the bare number swap** (`nyiso_li_tsl_n11_security` is `R`, killed on K6 at nyiso-130); (2) the **FLEET-CF COMPOSITION** object this promotion's finding opens, **replacing** the refuted commissioning-curve item — 2023/2024 imply ~0.162 against 2025's 0.1955 while measured mature per-plant CF is 0.174–0.182 (2021–22 fixed-tilt NY8) vs 0.198–0.221 (2024 tracking), so one ISO-wide `RENEWABLE_AVG_CF` cannot track a fleet going 100 % fixed-tilt → 56 % tracking. Evidence: `results/calibration/FINDING-nyiso133-market-solar-cod-basis-2026-08-08.md`, `PREREG-nyiso133-market-solar-cod-basis-2026-08-08.md`, `_nyiso133_ab_gates.json`, `_nyiso133_commissioning_ramp.json`.
```

### 3c. How to land the promotion in a session that HAS git credentials

All four §1 edits are deterministic and reproducible in minutes:

1. `frontend/data/backcast/keepers/NYISO.json` — set `keeper` to
   `2026-08-08-nyiso-133-cod-arm`; prepend §2's substance as the new
   `promotion_note`, keeping the existing note appended after
   `(PRIOR NOTE, nyiso-132 promotion, unedited below.)`; push the existing
   `superseded` block down under a new one dated `2026-08-15` whose
   `former_keeper` is `2026-08-08-nyiso-132-cf-arm`.
2. `frontend/data/backcast/calibration-complete.json` — in `complete.NYISO`:
   re-key `keeper`; prepend the re-verified `determination` text, keeping the old
   text after `(SUPERSEDED TEXT, preserved for the record.)`; set
   `keeper_at_prior_rekey` to the nyiso-132 entry; append a `rekey_history` row
   dated `2026-08-15`, session `nyiso-135`. **Leave `tier_authorized`,
   `locked_test`, `keeper_at_declaration` and the `final` block untouched.**
3. `docs/codebase-site/data/mechanism-matrix/NYISO.js` — `updated: "2026-08-15"`,
   `keeper: "2026-08-08-nyiso-133-cod-arm"`, `vre_registry_cod_date_basis`
   `cell: "K"` with the §3b evidence text, and a column re-stamp block at EOF.
4. `python scripts/build_status.py --iso NYISO` regenerates
   `frontend/data/backcast/status/NYISO.js`.

Then the doc stamps in §3a/§3b, and re-run the four gates listed in §1.
Serialize both JSON files with `indent=1`, `ensure_ascii=True` and a trailing
newline to match the repo convention and keep the diff minimal.

## 4. WHAT IS OPEN AFTER THIS SESSION

1. **Land the promotion itself** (§3c) — built and verified, blocked only on
   transport.
2. **Collapse the gate to unconditional** (rule 26 `[R-DELETE]`) — nyiso-133 §9's
   own recommendation, deliberately NOT taken here. Reasons: it is an owner
   decision with a **NYISO forecast-lane blast radius** (11 committed hindcast
   sidecars, rule 15's separate namespace), and with no `git fetch` available
   `src/market_sim/config/scenarios.py` could not be rebased onto a `main` that had
   advanced **19 merged PRs** — editing a >300-line core file off a stale base is
   exactly the rule 27 `[R-PUSH]` hazard. The candidate run carries the flag `True`
   in its own `run_config.json`, so only the DEFAULT is deferred.
3. **The two doc stamps in §3a/§3b.**
4. **Lever queue** — (1) the chartered JOINT Zone-K transfer-bound + downstate
   ST_GAS `min_gen` reconciliation (rule 19; **do not** re-test the bare number
   swap, `nyiso_li_tsl_n11_security` is `R` on kill gate K6 at nyiso-130);
   (2) the **FLEET-CF COMPOSITION** object, which replaces the refuted
   commissioning-curve item.
5. **Carried from nyiso-134, unchanged:** the ACTIVE holdout freeze is the sole
   blocker on the otherwise data-ready 2022 touchpoint; the import-tranche 719 MW
   duration RMSE disclosure is **still not re-measured** (grade it before quoting
   any 2022 result); the Transco Dec-2022 Elliott hole is unfixable from the free
   archive (disclose before quoting any Dec-2022 or winter-tail number).
