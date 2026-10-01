# PRECOMMIT — ercot-224: the item-8 CME/NYMEX basis-swap REOPEN SCREEN, Phase-0 (read-only — NO LP, NO solve, NO intake, NO arming) — questions, verdict rule and STOP rule pinned BEFORE any evaluation

**Session ercot-224, 2026-08-20, branch
`claude/ercot-224-calibration-ye2ivp`.** Pushed and blob-verified BEFORE the
screen reads any CME/NYMEX product or settlement content. Keeper at dispatch:
`2026-08-20-ercot223-arm-eventrelease` (NOT-YET, fail set {C3a-2023 −39.7 %,
C3b-2023 0.729}, C3c ledgered CAVEAT ×3) — this Phase-0 touches no solve, no
keeper artifact, no gate.

## 0. WHAT THIS SESSION ADJUDICATES, AND WHAT WAS TOUCHED PRE-PRECOMMIT

§5.1 item 8 (daily gas basis for the CT-band/winter offer-cost object) is
**CLOSED, REFUSED ON DATA** (owner decision 2026-08-04, ercot-163 addendum:
NO PAID DAILY GAS DATA; monthly insufficient by construction — ERCOT-147 §3's
confound is daily). Its **SOLE RECORDED REOPEN CONDITION** is verbatim:
*"CME/NYMEX publishes Waha and Houston-Ship-Channel basis-swap daily
settlements publicly at no cost — a FORWARD settlement, not cash spot, so it
needs its own rule-13 admissibility argument screened first (no LP) before
item 8 could return."* This session runs exactly that screen and nothing
else. The ERCOT-160 DO-NOT-REDO stands untouched: the free EIA/ERCOT paths
are NOT re-screened, no licence is re-asked, Henry Hub is never substituted.

**Pre-precommit disclosure:** before this file was written the session made
transport-level reachability checks only — `curl` to `www.cmegroup.com`
times out from this environment (bot protection), while the session's
WebFetch route reaches the host (one guessed product URL returned a real
404). **No product page, settlement page, or price content was read.** The
screen's evidence therefore comes via the WebFetch/WebSearch route, quoted
and dated in the probe record; the probe script re-attempts `curl`
best-effort so the transport constraint is itself recorded reproducibly.

## 1. SCOPE (pinned)

The screen covers the **CME/NYMEX-published route only** — the reopen
condition's named path. Within that route, TWO product families are in
scope, because both are the same free-CME publication channel and the second
is strictly more on-target for the daily object:

- **(F1) Basis futures/swaps** settling to the **monthly** Platts Inside
  FERC first-of-month index differential vs the NYMEX Henry Hub last-day
  settlement (the family the reopen condition names), for **Waha** and
  **Houston Ship Channel**.
- **(F2) Gas-Daily-settled products** (swing/index futures settling to the
  **daily** Platts Gas Daily price) for the same two hubs, if CME lists
  them. The reopen text predates any screen of this family; adjudicating F1
  while ignoring a same-source family that settles to the daily cash object
  would be a screen designed to fail. F2 is IN SCOPE on the same gates.

Out of scope, restated: NGI/Platts/Argus direct (owner-refused), EIA/ERCOT
free paths (ERCOT-160, screened), ICE (not the named source; also paid),
any paid CME service beyond identifying that it IS paid (DataMine et al.).

## 2. THE PRE-REGISTERED QUESTIONS

**Leg A — existence and free public access** (the reopen condition's own
words, decomposed):

- **A1 (existence):** Do CME/NYMEX Waha and HSC products of family F1
  (and/or F2) exist as listed, tradeable contracts with identifiable
  product codes?
- **A2 (current settlements free):** Are their **daily settlement prices**
  published by CME publicly at no cost for the current/recent window?
- **A3 (history free — the load-bearing half):** Are daily settlements for
  the **2023–2025 trading days** (the training span; the confound is
  2023-daily) available publicly at no cost — not merely the last few
  sessions? A reopen on data that cannot reach calendar 2023 grounds
  nothing the object needs.
- **A4 (licence compatibility):** Do CME's terms permit this repo's use
  (intake of settlement values into `data/raw/`, derived use in
  calibration)? Read against the unresolved `docs/data-licensing.md` §5
  standard. An "available to view, forbidden to store" answer FAILS A4.

**Leg B — rule-13 admissibility and fidelity** (reached only if A1 ∧ A2
hold; recorded regardless for the record if cheaply determinable):

- **B1 (what the number IS):** Pin, from the contract specs themselves,
  what a daily settlement of the prompt contract measures. For F1 the
  expected answer: the market's expectation of a **monthly-average** index
  differential — a forward price of a monthly object, whose day-to-day
  movement is expectation revision, not the day's realized cash basis. For
  F2: the settlement basis is the daily Gas Daily index (the daily cash
  object itself, one publication step removed).
- **B2 (rule-13 test):** Could the same quantity be produced for a forward
  year from forward drivers, and would it respond to changed conditions? A
  forward basis curve is prima facie the MOST forecast-compatible gas input
  the model could carry (a forecast year has forward curves and no cash
  history), so B2 is expected to PASS for F1 — the screen must still write
  the argument, including what the backcast overlay vs the forecast
  analogue each read.
- **B3 (fidelity to the confound — the kill question):** ERCOT-147 §3's
  object is whether a given DAY's CT offer sits below that day's true burn
  cost or merely below HH-based burn because the local hub was cheap THAT
  DAY (Waha's 2023 negative DAYS vanish in monthly means; intra-day
  variance share 0.14, daily rel IQR 0.64). The instrument must therefore
  carry **realized daily cash-basis variation**, not a smoothed expectation
  of a monthly average. Pinned criterion: F1 passes B3 only if its daily
  prompt-month settlement can be shown (from spec/construction, no price
  fitting) to track the daily cash basis rather than the expected monthly
  mean — the default presumption is that it CANNOT (a price OF a monthly
  average cannot resolve intra-month daily cash swings even in principle,
  beyond expectation drift). F2, settling to Gas Daily itself, passes B3
  by construction IF its settlement history exists and is free (A3).

## 3. THE VERDICT RULE (pinned)

- **REOPEN item 8** iff, for at least one in-scope family/hub pair
  covering BOTH hubs (Waha AND HSC): A1 ∧ A2 ∧ A3 ∧ A4 ∧ B2 ∧ B3.
- **Any leg fails → item 8 STAYS CLOSED**, the failed leg(s) named as the
  new recorded blocker, and the reopen-condition text in matrix §5.1 is
  re-stamped with the screen's result so the condition is never re-screened
  without new evidence (28a discipline).
- A **split verdict** (e.g. F2 admissible but history paid; F1 free but
  B3-failed) is recorded per-leg; item 8 reopens only on a fully-passing
  column. Partial passes may NAME a follow-up (e.g. an owner question on a
  bounded paid history) but grant nothing.
- **Indeterminate access** (bot-walls prevent verifying a leg either way)
  is recorded as INDETERMINATE, never coerced to pass/fail; the item stays
  closed (fail-closed), with the specific unverifiable leg named.

## 4. STOP RULE AND FENCES (pinned)

- **NO LP, no solve, no run registration, no `ScenarioConfig` change, no
  intake** in ANY branch of the verdict — a REOPEN verdict yields a named
  data-intake charter for a FUTURE session (data-intake skill shaped) plus
  the rule-13 memo, nothing more. This session ends at the memo.
- No measured 2019–2022 or 2026 price content enters any statistic (rule
  22 data-not-score is not even approached: no statistic is computed —
  this screen reads contract SPECS and ACCESS terms, not price series;
  incidental price values quoted on a settlements page are evidence of
  publication, never inputs).
- Known blocker honoured, not re-checked: the 2022 NP3-965 offer corpus is
  unrecoverable (FINDING-ercot221 §7) — nothing here touches it.
- Rule 25: ERCOT only. Rule 27: local edits + `git push`, blob-verify every
  ≥300-line file touched (and this precommit regardless of size, per
  dispatch). No PR; push-and-stop on the designated branch.

## 5. DELIVERABLES (pinned)

1. This precommit, pushed + blob-verified before any evaluation.
2. Probe record: `scripts/probes/ercot224_cme_basis_screen.py` →
   `results/calibration/ercot224_cme_basis_screen.json` — the evidence
   table (URL, retrieval date, transport, quoted finding per A/B leg) plus
   best-effort `curl` transport re-checks; honest about which legs came via
   the session's WebFetch route vs reproducible transport.
3. `docs/FINDING-ercot224-item8-cme-screen-2026-08-20.md` — the full
   screen record and the rule-13 memo (whatever the verdict).
4. `docs/calibration-log/ercot.md` entry (ercot-224; next shorthand
   ercot-225, ercot-199 unclaimed).
5. Matrix §5.1 item-8 block re-stamped with the screen result (28b
   evidence duty; no mechanism is tested so no cell verdict is minted).
6. Push, blob-verified per rule 27.
