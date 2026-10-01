# FINDING — pjm-128: the commitment-status half of the Lane 2 hypothesis is BLOCKED ON NON-PUBLIC DATA (2026-07-26)

**Verdict: NO_PUBLIC_FEED.** PJM publishes no unit-level day-ahead award or
commitment feed. The commitment-status half of the mid-curve conditioning
hypothesis — *"the units offering in the tightest bin are largely already
committed, so the offers submitted there come from a different population than
the offers that set the price"* — **cannot be tested from public data**, and is
recorded as **untested and blocked**, not as refuted.

This is a terminal frontier-ledger state, and it is the *same* state the bar's
second clause names explicitly ("blocked on data that does not exist
publicly") — the state NYISO's remaining reserve lever occupies. It is not,
by itself, a frontier declaration: Lane 2's other half (the re-derive decision)
is still live and owner-gated.

Census: `scripts/probes/pjm128_da_award_feed_scope.py` (admissibility test
committed `d52740b`, **before** the census ran); machine-readable result:
`results/calibration/pjm128_da_award_feed_scope.json`. No LP, no solve, no
surface written, no keeper touched, no bulk intake — every request is a sample
of a few thousand rows.

---

## 1. Why this half was open

pjm-126's arm C (the "fixed population" arm, which restricted the ladder to
units offering in all four net-load bins) came back **VACUOUS in every year** —
≥99.2 % of units offer in all four bins, because PJM generators submit offers
regardless of commitment state. So arm C held nothing fixed, its HOLDS flags
are not evidence, and the population half of the hypothesis was never tested.
pjm-127 reproduced that vacuity in 2023 and 2024. The season half was settled
decisively (ARTIFACT, all three years and pooled); the commitment half needs
what the offer corpus does not carry: **which units were actually committed,
per hour**.

## 2. The admissibility test, and the census against it

A feed admits the Step-2 probe only if it satisfies all three:

| | criterion |
|---|---|
| **A1** | resolves an individual generating **unit** (not a zone, fuel, locale or system total) |
| **A2** | carries an **hourly-or-finer** time key (the tightness bins are hourly) |
| **A3** | carries a **cleared / awarded / committed** quantity or commitment status — an *offer* is not an award |

PJM's public DataMiner2 catalog was enumerated from the API itself
(`GET https://api.pjm.com/api/v1/`, the authoritative list): **119 feeds**, of
which **26** trip a commitment/award/schedule/unit keyword net. Every plausible
candidate was then **sampled live**, so the verdict rests on measured schemas
rather than on catalog prose:

| feed | grain measured | fails |
|---|---|---|
| `energy_market_offers` | unit × hour, 90.6 M rows | **A3** — offers only; no cleared/awarded column exists |
| `ops_init_commit` | **zone** × event, 20 zones, 3 reasons | A1, A3 — operator-initiated (out-of-market) commitments only |
| `rt_and_self_ecomax` | **system** × hour | A1, A3 — and see §3 |
| `day_gen_capacity` | **system** × hour (`total_committed`) | A1 — the only sampled feed with a genuine committed quantity, and it is a system total |
| `gen_specific_uplift_credit` | generator × **month**, real names | A2, A3 — monthly dollar credits |
| `sync_pri_reserves_resources_list` | resource roster, no time key | A2, A3 — identity without hourly award |
| `da_reserve_market_results` | locale × service × hour | A1, A3 — reserve clearing aggregates |
| `day_inc_dec_utc` | system × day, virtuals | A1, A2, A3 — not generators |

**No feed satisfies A1+A2+A3.** The single unit-resolved hourly feed is the
offer corpus we already hold, and it carries offers, not awards. PJM's own
posting page for the same data states it plainly — the files contain no cleared
or awarded megawatts, no day-ahead scheduling or commitment status, and no unit
online/offline status per unit-hour
([PJM, Daily Energy Market Offer Data](https://www.pjm.com/markets-and-operations/energy/real-time/historical-bid-data/unit-bid.aspx)).

## 3. PJM withholds the commitment quantity by rule — measured, not inferred

`rt_and_self_ecomax` ("Scheduled Generation") is the closest thing PJM
publishes to a committed-capacity series, and it is a **system hourly total**.
Even at that aggregation the RT-committed column is suppressed: in the sampled
month (Jul 2025) `rt_ecomax` is null in **35.9 % of hours**, with PJM's own flag
`"Confidentiality Rules Prohibit Display"` on the suppressed rows (Jan 2023:
49.7 % suppressed). A quantity PJM redacts *at system level* when too few units
underlie it is not one it publishes per unit. This is the mechanism behind the
absence, not merely its symptom.

## 4. The second, independent blocker: the offer corpus cannot be joined to anything

The question is about the committed share **of the offer population** per
tightness bin, so any award source — inside DataMiner2 or outside it — would
have to be joined to the offer corpus. It cannot be. PJM masks generator
identity in `energy_market_offers` and re-draws the masked codes annually, and
publishes no crosswalk. Measured directly (one mid-July day per year):

| | 2023-07-15 | 2024-07-15 |
|---|---|---|
| distinct `unit_code` | 1,219 | 1,252 |
| codes present in **both** years | **0** | |
| Jaccard | **0.0000** | |

The two years' code spaces are **completely disjoint** — not merely
uncorrelated. So even a perfect external unit-hour award series (a bilateral
disclosure, a FERC filing, a state proceeding) could not be attached to the
offers whose committed share we need. The blocker is structural, and it is
independent of §2: closing the catalog gap would not open this half.

**Route refused, not untried.** Masked units could in principle be fingerprinted
against the EIA-860 / CAMPD fleet by their ecomax / ecomin / start-cost
signature to reconstruct identity. That is de-anonymising data PJM masks under
its confidentiality rules. It is not a route this project takes, and it is
recorded here as **refused** so no later session treats it as an unexplored
option.

## 5. What was NOT done, deliberately

* **No aggregate proxy.** `ops_init_commit` (zone) and `day_gen_capacity`
  (system `total_committed`) could each be regressed against the tightness bins
  to manufacture a committed-share number. The charter forbids it and rule 1
  forbids it independently: a zone- or system-level committed share is not the
  offer population's committed share, and a conclusion reached through a
  mechanism that is not the one claimed is not evidence. The half stays
  untested.
* **No re-derive, and no nudge on the memo.** The owner has not decided
  `docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`; rule 20 leaves
  the re-derive inadmissible until they do. Nothing in this session touches
  either surface, either derive, or the keeper.

## 6. Consequences for the ledger

1. **Lane 2's commitment-status half: CLOSED, terminal, blocked on non-public
   data.** It joins the closed list; no future session should re-open it
   without a *new public source* (the census is reproducible — re-run the probe
   if PJM's catalog changes).
2. **The season half is unaffected.** pjm-126/127's ARTIFACT verdict never
   depended on arm C; it rests on arm B, which is decisive on its own. Nothing
   here weakens or strengthens the case in the re-conditioning memo.
3. **Frontier remains NOT ready** — but for exactly one reason now. Lane 1 is
   complete, Lane 2's commitment half is terminal, and what remains is the
   **owner decision on the re-derive memo**: a named admissible mechanism that
   is neither tried nor formally blocked. When that decision lands — authorize
   and run memo §4, or decline and record the block — the ledger is whole
   either way.

## Pointers

* The vacuity that opened this: `docs/FINDING-pjm126-midcurve-conditioning-artifact-2026-07.md` §"Limitation", `docs/FINDING-pjm127-conditioning-multiyear-2026-07.md`.
* The lane and its ledger: `docs/handoffs/pjm-frontier-path-2026-07.md` §3 Lane 2, §4.3b.
* The pending decision: `docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`.
* The frontier bar: `docs/codebase-site/calibration-rubric.html` §frontier.
* The census: `scripts/probes/pjm128_da_award_feed_scope.py`, `results/calibration/pjm128_da_award_feed_scope.json`.
