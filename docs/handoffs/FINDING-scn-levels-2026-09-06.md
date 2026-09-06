# FINDING — SCN-LEVELS: owner ruling S3 committed the §3.5 campaign levels, and **not one number moved**

**Lane:** SCN-LEVELS (records/governance; released by ruling **S3**, SCN-DESK r#5 amendment 1).
**Branch:** `claude/scn-levels-label-commit-5u3xny` (the issued stem `claude/scn-levels-d2-commit-c3jx`
is advisory per ledger §5; the realized branch is this one). **Date:** 2026-09-06.
**Model:** Fable `claude-fable-5-1`. **DATA PROFILE:** `code`. **Solves: ZERO.**

---

## 0. Bottom line

**Owner card D-2 was ruled as S3 — "the plan's §3.5 table is the COMMITTED default" — and executing
it required changing no number anywhere in the repo.** Every level S3 committed is bit-for-bit the
level the building lane already carried under an "illustrative" label. This lane changed labels,
cited the ruling, and measured that nothing else moved.

Three facts, measured not asserted:

1. **The levels are identical.** §1 puts what SCN-WS2a probed beside what S3 committed, value by
   value. They are the same values.
2. **No cache key moved.** 91 pre-existing keys — the two pins, the twelve REF bases, every live
   campaign case on all six ISOs, and every committed keeper `run_config.json` on disk — are
   byte-identical before and after (§3). The only delta is **6 added** keys for the newly-live
   `CES-T80` case, which hash exactly as they did *before* this lane touched anything.
3. **No `ScenarioConfig` default moved.** The `scenarios.py` diff contains **zero non-comment
   lines** (§3).

**What this releases:** `CES-T80` is now a LIVE case at a committed level, so **Stage A's case set
is a committed campaign rather than an illustrative one** — its results answer the owner's question
instead of demonstrating machinery.

**What it does NOT release, and this matters as much:** S3 is silent in three places, and this lane
refused to fill any of them (§4). They are re-presented to the owner, not inferred.

---

## 1. The numbers, side by side — the whole point of the lane

| what | SCN-WS2a built and probed against | S3 committed (2026-09-06) | same? |
|---|---|---|---|
| CES target, 2026 knot | `0.55` | `<current>` → **0.55** (resolved by plan §3 WS-2 item 5) | **yes** |
| CES target, 2035 knot | `0.80` | `0.80` | **yes** |
| CES target, 2050 knot | `1.00` | `1.00` | **yes** |
| CES ACP ($/MWh, real 2026$) | `50.0` | `$50` | **yes** |
| CES premium ladder | `{10, 20, 30}` (from D8) | `{10, 20, 30}` | **yes** |
| LOAD-HI | growth `high` + DC `high` | growth high + DC high | **yes** |
| LOAD-HI-ORGANIC | growth `high` + DC `mid` | growth high + DC mid | **yes** |

Sources: `PRECOMMIT-scn-ws2a-2026-09-05.md` lines 15–17 (`federal_ces_target_by_year={2026: 0.55,
2035: 0.80, 2050: 1.00}`, `federal_ces_acp_usd_per_mwh=50.0`, "**The schedule and the ACP are
ILLUSTRATIVE**"); `FINDING-scn-ws2a-2026-09-05.md` §0 item 5; ledger §2 D-2 row; plan §3.5.

### 1.1 How `<current>` is resolved — and the limit of that resolution, said plainly

§3.5 writes the 2026 knot as the token `<current>`; the plan's **own** §3 WS-2 item 5 writes the
same schedule as `{2026: 0.55, 2035: 0.80, 2050: 1.0}`. S3's text is what binds the two: *"SCN-WS2a
built and probed against exactly this and labelled it illustrative, so the change is to the label,
not the number."* WS-2a probed 0.55. **So 0.55 is the committed 2026 knot.**

This is a resolution of an underspecified token, **not** a discrepancy, so it was not routed under
the STOP rule — the committed level does not *differ* from what the lane ran; one statement of it
was a placeholder and the other was the number, and the ruling identifies them.

**The honest limit:** 0.55 is the plan's declared stand-in for "the current national clean share".
It is **not** an independently sourced measurement, and this lane did not source one (that would be
inventing a level). It is a what-if level exactly like every other level in the campaign, which is
what rule 1 `[R-STRUCT]` requires of a scenario knob. For scale, the model's own NEISO 2026 credited
share is **0.345** (`FINDING-scn-ws2a-2026-09-05.md` §4.3) — i.e. the committed 2026 knot sits
*above* at least one ISO's measured share, which is why that probe lands in the escape regime.
Anyone quoting `CES-T80` should quote it as a policy what-if, never as a calibrated baseline.

### 1.2 What follows for the registered probe

Because the probe ran at exactly the committed level, the registered NEISO T0 pair
`neiso-2026-2026-scn-ws2a-neiso-2026-t0-{ref,target}` is now quotable as a **campaign-level
result**, not only as a machinery demonstration. Its measured content is unchanged and its caveats
stand undiluted: escape regime (dual = ACP $50 exactly, credited 40.37 TWh < 0.55 × 117.09 = 64.40
TWh, escape 24.03 TWh), the CO2 leg's literal +2e-4 miss reported and not smoothed, and the two
things a 1-year T0 cannot show (a binding non-escape year; the deployment response).

---

## 2. Where the word "illustrative" was removed

| file | region | was | now |
|---|---|---|---|
| `configs/scenario_campaign_matrix.yaml` | header, "READ THIS BEFORE USING THE LEVELS" | "EVERY NUMBER BELOW IS ILLUSTRATIVE PENDING OWNER CARD D-2" | "THE LEVELS BELOW ARE COMMITTED, NOT ILLUSTRATIVE", S3 + date, and the three uncommitted places |
| `configs/scenario_campaign_matrix.yaml` | carbon case block | "ILLUSTRATIVE knots pending D-2" | "THE INTERIM REDUCED FORM, NOT THE COMMITTED LEVEL" (§4 item 3) |
| `configs/scenario_campaign_matrix.yaml` | CES premium block | "the least illustrative numbers in this file" | "COMMITTED: … named explicitly in S3 … re-affirms D8 rather than moving it" |
| `configs/scenario_campaign_matrix.yaml` | `CES-T80` block | commented, `{2026: <current>…}` / `<owner D-2>` | **LIVE** at the committed level, with the `<current>` chain written out |
| `configs/scenario_campaign_matrix.yaml` | VOL-* block | "ONLY if owner card D-3 rules the axis admissible … if D-3 rules NO these cases are struck" | spent clause deleted; **D-3 RULED YES (S1)**, D-3b deferred; blocked on the missing field alone |
| `src/market_sim/config/scenarios.py` | `federal_ces_target_by_year` docstring | "ILLUSTRATIVE, NOT A CAMPAIGN LEVEL … No value here is a committed level" | S3 citation; `<current>` = 0.55; where a committed level actually lives (the YAML, rule 24) |
| `src/market_sim/config/scenarios.py` | `federal_ces_acp_usd_per_mwh` docstring | "Illustrative $50 in the SCN-WS2a probe (D-2 open)" | "The COMMITTED campaign level is $50 — owner box D-2 → S3 … the same $50" |
| `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` | §3.5 header | "Levels are illustrative until D-2." | deleted (now false); replaced by the committed-per-S3 header |
| `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` | §5.1 rows 1 and 3 | "illustrative level, D-2 open" | "yes, at a COMMITTED level"; probe quotable as a campaign result |
| `docs/handoffs/scenario-desk-ledger-2026-09.md` | §2 D-2 row, §3 rows 1 and 3 | same as above | executed-by record + the three uncommitted levels; scorecard mirrors the plan |

Also relabelled, not "illustrative" but stale in the same way: the plan §5.1 and ledger §3 **Carbon**
cells read "repair gated on D-1" — D-1 is ruled (S2), so they now name **SCN-WS1c** as the lane
holding the repair and the additive ladder as the interim.

---

## 3. Verification — measured, not asserted

**(a) The `scenarios.py` change is comment-only.** Every added/removed line in the diff begins with
`#`; filtering the diff for non-comment changes returns nothing:

```
git diff --unified=0 src/market_sim/config/scenarios.py \
  | grep -E "^[+-]" | grep -vE "^(\+\+\+|---)" | grep -vE "^[+-]\s*#"
→ (empty)
```

**(b) No cache key moved.** A snapshot script hashed, before any edit and again after all of them:
the two pins; the twelve REF bases (six ISOs × 2030/2050); **every LIVE campaign case on every ISO**;
and **every `results/calibration/*/run_config.json` on disk** — 91 keys, no skips.

| result | count |
|---|---|
| keys present before and **unchanged** | **91 / 91** |
| keys **changed** | **0** |
| keys **removed** | **0** |
| keys **added** (the newly-live `CES-T80` case, one per ISO) | 6 |

The pins re-computed to their in-repo values: `PIN/default = e5ecd4105ada3e58`,
`PIN/backcast = 6a2845e50951394e`. The six added keys — ERCOT `9705402585de89e0`, CAISO
`4e6a8bef2477fb31`, MISO `31c01a42dea923ad`, PJM `8eb29037d1ac1828`, NYISO `c345b6e8e4761fae`,
NEISO `f0e20c97051279cd` — are **identical to the keys the same config produced when probed BEFORE
any edit**, so making the case live materialized a config; it did not change a hash. `CES-T80` is
registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `None` by SCN-WS2a, which is why an unset run is
unaffected.

**(c) Tests.** `tests/scoring/test_scenario_campaign_configs.py`: **17 passed** (16 before, plus the
new committed-level test). Wider slice `tests/unit/config tests/unit/policy tests/scoring`:
**2352 passed**, 24 skipped. Five failures in that slice
(`test_crossover_harness.py::test_forward_year_demand_not_from_realized_loader` and four in
`test_ff_readiness_battery.py`) **reproduce identically on a clean tree** (`git stash`, same five)
and are pre-existing under the `code` data profile — not this lane's.

---

## 4. Where "illustrative" MUST REMAIN, and the levels S3 did not reach

**This section is the counterweight to §0 and should be read with it.** S3 committed a table; the
table is silent in three places, and a ruling's silence is not a level. None of the following was
filled in, and none may be inferred from S3.

1. **`CAP-STATE-TIGHT`'s declining budget — STILL AN OWNER LEVEL (D-2).** §3.5's row writes only
   "`mass_cap_enabled: true` + declining `mass_cap_tons` on program ISOs" — no number — and S3's
   enumeration names no budget. SCN-WS1a's pre-declared case says so in terms: *"RGGI's own
   post-2030 trajectory is not landed in the repo, and CARB publishes no power-sector budget at all,
   so the slope is an OWNER level (D-2)"* (`FINDING-scn-ws1a-2026-09-05.md` §4.2). The case also
   still needs a `{year: tons}` schedule field (`mass_cap_tons_by_year`; `mass_cap_tons` is a scalar)
   and has no exported read-out (`co2_cap_price` has no reader under `results/`, WS-1a §4.3).
   **Re-present the budget.**
2. **Two voluntary sub-cells — STILL OWNER-SET.** S3 commits "the WS-3a memo's box-5 defaults", but
   box 5's own recommendation leaves **`f_commit` mid** and the **WTP-ceiling level** owner-set
   (`voluntary-clean-demand-design-memo-2026-09-05.md` box 5; the memo calls `f_commit` "the weakest
   cell in the construction, said plainly"). Committing "the box-5 defaults" therefore does not
   commit these two. **SCN-WS3b must build against the box-5 recommendation and flag both as unset.**
3. **The carbon ladder's FORM — the one place the committed level is not the live one.** S3 commits
   the RFF **path** ladder. It cannot go live: G-C1 is still live at HEAD, so an explicit path
   *suppresses* the program trajectory and a path-form case is a carbon **cut** of $16–$102/t in
   every one of 25 years on CAISO/NYISO/NEISO (`FINDING-scn-ws1a-2026-09-05.md` §0.1/§6). D-1 is
   ruled **FLOOR (S2)** and **SCN-WS1c** holds the repair. Until it merges the campaign runs the
   reduced additive `carbon_price_delta` form, whose **{15, 25, 50} knots are a desk stand-in and
   were never ruled**. Anything quoted off `CARB-*` or `CARB-MID+LOAD-HI` is a reduced-form result
   and must say so. This is a **disclosure, not a routed discrepancy**: the desk assigned the reduced
   form to SCN-WS1b deliberately while D-1 was open (ledger §5 r#3 issuance), so the gap between the
   committed form and the running form is on the record and predates this lane.

**And the card that keeps its recommendation label: D-3c is STILL OPEN.** S1 ruled the voluntary
*axis* admissible and S3 ruled its *levels*; **neither reaches the eligible set** (renewable-only by
default vs carbon-free as a labelled override; all eligible units vs new builds only — memo box 3).
So SCN-WS3b's eligible-set default stays labelled **the memo's recommendation**, not a committed
level — this is the one place the illustrative-class wording is deliberately left standing.
**D-6 (attribute netting) is likewise unruled**: `CES-P20+VOL-HI` reports both nettings and asserts
neither, with memo §4.3 as the brief and Addendum A.2 as the dissent to weigh beside it.

---

## 5. Routed to SCN-DESK

1. **Two out-of-region "illustrative" labels left standing in the plan**, both historical charter
   text for a landed lane: **§3 WS-2 item 5** ("illustrative; the campaign target is owner box D-2")
   and the **§7 "WS-2a" prompt body** ("use the illustrative {2026: current, …}"). SCN-LEVELS owns
   §3.5 and §5.1 only, so these were not edited. They read as a record of what the lane was told at
   the time; the desk may prefer a one-line "RULED S3" annotation.
2. **One edit outside the charter's named file list, disclosed:**
   `tests/scoring/test_scenario_campaign_configs.py::test_blocked_cases_are_commented_not_live`
   asserted `CES-T80` "must not be live yet" — a premise written when its fields did not exist. It
   is the campaign YAML's own contract test and it is the *only* thing that made this lane's
   deliverable fail CI. `CES-T80` was removed from that list and a new
   `test_ces_target_case_is_live_at_the_committed_level` pins the committed level so it cannot drift
   silently. No other test touched; no mechanism file touched. **If the desk reads this as widening,
   the remedy is to revert the two test hunks and re-comment `CES-T80` — say so and it will be done.**
3. **The commented path form now names the test that must move with it.** When SCN-WS1c lands S2's
   floor and the carbon ladder swaps to the path form,
   `test_the_carbon_ladder_is_the_additive_delta_form` pins the interim form on purpose and must be
   re-pointed in the same PR. The YAML comment says so at the swap point.
4. **`CES-T80` is now solvable and nobody is chartered to solve it.** It has never been run at the
   campaign horizon — the only evidence is SCN-WS2a's 1-year NEISO T0 in the escape regime. The
   binding regime (`0 < dual < ACP`) and the deployment response remain unexercised on a real fleet.
   That is Stage A / WS-5 work, flagged here so it is scheduled rather than assumed.

---

## 6. Rules

Rule 1 `[R-STRUCT]` — scenario levels are the owner's what-ifs; S3 is what makes these the owner's,
and this lane derived no level of its own. Rule 5 `[R-NO-MAGIC]` — every level carries its ruling
citation and date; the three S3 did not reach are named as uncommitted rather than given a number.
Rule 24 `[R-REGISTRY]` — a committed campaign level is a **case override in the campaign YAML**,
never a shipped default; both CES defaults stay `None` and the docstrings now say why (it is what
keeps the keys stable). Rule 28 `[R-MECH-MATRIX]` — **no duty fires**: this lane tests no mechanism
and adds no `ScenarioConfig` field, so no matrix row or cell is owed and the tree was not touched.
Rule 27 `[R-PUSH]` — `scenarios.py` (≥300 lines) was edited locally and pushed as on-disk bytes,
then blob-verified by fetch-back.
