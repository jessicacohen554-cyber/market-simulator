# FINDING — neiso-66: the residual CAMPD outage over-count is **not a detector error and not a CNOG reporting gap** — it is a **definitional seam**. CNOG publishes *unavailability*; the CEMS detector measures *non-operation*. The residual is **available-but-not-committed** capacity. Two of the charter's inputs are corrected on the way: the published-side reconstruction was mis-built (inflating every ratio ~1.3x), and both of the re-audit's stated candidate directions are REFUTED by measurement (2026-07-26)

**Freeze status: STILL ACTIVE, and this finding does not lift it.** It replaces
the two open directions with one measured mechanism and a specific, testable
lift condition. Only the owner lifts the freeze.

Context: `RESULTS-neiso65-crossiso-reaudit-2026-07.md` §4-§5 left the residual
over-count as the charter's lift condition, measured at 1.52-2.13x on CAISO's
crosswalked active-plant scope, with two candidate directions and no
adjudication:

> either the detector books short economic cycling below the guard's 90 %
> out-of-merit threshold as outage, or CNOG (a DAM prior-trade-date snapshot)
> under-reports intraday forced outages — both directions stated; neither is
> resolved here.

Both are now measured. **Neither survives.**

Probes (committed, re-runnable, no LP solve anywhere):
`scripts/probes/_neiso65_overcount_rootcause.py`,
`scripts/probes/_neiso65_cnog_revision_rebuild.py`.

---

## §1 — the published side was mis-reconstructed; every over-count ratio was inflated ~1.3x

Both charter scorers (`_neiso64_meritguard_score.py`,
`_neiso65_caiso_crosswalk_score.py`) collapse CNOG with

```python
d.sort_values("last_trade_date").groupby("mrid").tail(1)
```

on the stated premise that *"the raw parquet repeats each outage on every trade
date it was reported: 794,103 rows over 151,758 mrids = 5.23x ... the last
report is the settled version."*

**The premise is false.** The fetcher had already collapsed the trade-date
repetition — it emits one row per distinct reported *segment* and records the
repetition in `first_trade_date` / `last_trade_date` / `days_reported`
(`days_reported` sums to 1,325,042 over the 794,103 rows). Measured directly:

| grain | distinct rows | duplicates |
|---|---|---|
| `(mrid, start, end, curtailment_mw)` | 794,103 | **0** |
| `(mrid, start, end)` | 794,103 | **0** |

The 5.23 rows per mrid are not repeats of one outage. They are **distinct
segments** of one outage record, carrying different spans and different
curtailment levels. `tail(1)` therefore keeps one arbitrary segment and throws
the rest away — on the crosswalked non-ambient 2023-25 scope it discards
**72 % of segments and 23 % of published MW-days**.

The naive repair (sum every segment) is also wrong, and for the reason the
charter originally sensed: segments of one mrid frequently *overlap*, because
later trade dates report **revisions** of the same outage. Summing them
double-counts.

**Correct reconstruction** (`build_revision`): per mrid, each day takes the
curtailment of the segment covering it with the latest `last_trade_date`.
Overlapping revisions collapse to the settled value; genuinely disjoint
segments all survive; distinct mrids are summed against each other.

CAISO crosswalked active-plant scope, guard-on extract:

| published-side build | mean published MW | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| `tail(1)` — charter §4 | 2,528 | 1.64x | 1.99x | 2.15x |
| raw sum — double-counts | 5,568 | 0.73x | 0.90x | 0.99x |
| **revision-aware — correct** | **2,925** | **1.40x** | **1.69x** | **1.90x** |

So the charter's headline was inflated, but **the over-count is real and
survives the correction**. Every number below uses the revision-aware build.

*(Consequence for the record: the §4 CAISO table and the neiso-64 NEISO
whole-fleet levels are both built on `tail(1)` and are overstated by roughly
this factor. NEISO's published instrument is a different report and was not
re-measured here — its 1.29-1.36x needs the same audit before it is quoted
again.)*

## §2 — the residual is entirely extra DAYS, at correct magnitude

Decomposing the level ratio into a magnitude term (do the two instruments agree
on *how much* on the days they both flag?) and a detection term:

| year | overall | co-detected plant-days | magnitude on those days | CAMPD-only days | CNOG-only days |
|---|---|---|---|---|---|
| 2023 | 1.40x | 2,152 | **1.14x** (904 vs 792 GW-d) | 2,098 d / 549 GW-d (**+61 %**) | 1,151 d / 248 GW-d |
| 2024 | 1.69x | 1,742 | **1.12x** (858 vs 765 GW-d) | 2,554 d / 898 GW-d (**+105 %**) | 1,793 d / 274 GW-d |
| 2025 | 1.90x | 2,443 | **1.14x** (1,018 vs 891 GW-d) | 3,689 d / 1,129 GW-d (**+111 %**) | 1,297 d / 236 GW-d |

Two things follow. The detector's **MW attribution is essentially calibrated** —
where both instruments see an event they agree within 12-14 %. And the entire
residual is **extra outage days**, growing 61 % → 105 % → 111 % across the three
years. (The traffic is not one-way: CNOG-only days exist too — the detector
*misses* 236-274 GW-days a year that CAISO does publish.)

## §3 — the extra days are GENUINE FULL STOPS: the detector is right

CEMS ground truth on every window in the committed guard-on extract, restricted
to **interior** days (first and last calendar day of each window dropped, since
a boundary day legitimately carries pre/post-outage generation):

| year | windows ≥3 d | interior unit-days | with non-zero generation | windows that are a complete stop |
|---|---|---|---|---|
| 2023 | 450 | 6,590 | 13 (**0.2 %**) | **97 %** |
| 2024 | 431 | 6,650 | 11 (**0.2 %**) | **98 %** |
| 2025 | 565 | 8,093 | 17 (**0.2 %**) | **97 %** |

The units really were completely offline for the whole window. This **refutes
the "detector books cycling as outage" direction** outright, in both the
charter's form (sub-threshold economic cycling) and the sharper form tested
here (a daily-cycling CC never achieving `MIN_REAL_RUN_HOURS = 24` consecutive
hours above `REAL_RUN_CF`, so its every-day runs collapse into one long false
outage). Neither happens: there is no generation inside these windows to
collapse.

*(Method note, recorded because it nearly produced a false finding: a first
pass compared `facility_id` as `int` against CAMPD's `facilityId`, which is a
**string** column — the filter silently matched nothing and returned "0 %
generation, 100 % full stops", the right answer for the wrong reason. The
un-restricted pass then showed 10 % generating days, which turned out to be
entirely boundary-day artifact. Only the interior-day pass above is load-bearing.)*

## §4 — and the guard's discriminator has no power on this population

The over-count is not something a re-tuned guard can reach. Attribution of the
EXCESS GW-days (windows the guard kept whose plant carries no published outage
over ≥25 % of the window's days — a deliberately lenient match, so EXCESS is
conservative):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| EXCESS share of kept GW-days | 34 % | 46 % | 48 % |
| of EXCESS: unidentified by the panel (**coverage** gap) | 3 % | 9 % | 28 % |
| of EXCESS: in the 0.50-0.90 out-of-merit **near-miss band** (**threshold** gap) | 5 % | 5 % | 3 % |
| of EXCESS: below 0.50 out-of-merit | 92 % | 86 % | 69 % |

Neither lever closes it: loosening `MERIT_OOM_FRAC` from 0.90 reaches at most
3-5 % of the excess, and extending panel coverage to every unidentified unit
reaches at most 28 % (2025; 3 % in 2023). The bulk of the excess is windows the
guard is *correct* to keep — the unit was in merit on the margin.

How firmly in merit, measured as the inframarginal spread `RCC − SRMC` over the
same units' booked-out hours versus their own running hours:

| year | booked-OUT hours: median spread / share in merit | RUNNING hours: median spread / share in merit | gap |
|---|---|---|---|
| 2023 | +6.60 $/MWh / 88 % | +12.75 $/MWh / 95 % | +6.14 |
| 2024 | +3.23 $/MWh / 90 % | +4.06 $/MWh / 92 % | +0.82 |
| 2025 | +4.34 $/MWh / 90 % | +4.81 $/MWh / 89 % | +0.47 |

In 2024-25 the units sit **fully stopped for a median ~10 days at a marginal
spread within $0.50-0.80/MWh of the spread they run on**. A marginal-cost test
cannot separate those two states, because on marginal cost they are the same
state.

## §5 — what the residual actually is

Putting §2-§4 together, the excess windows are, jointly and measurably:

* genuine sustained **full stops** (§3), so not a detection artifact;
* at **correct MW** (§2), so not a magnitude convention mismatch;
* **in merit on the margin** for ~90 % of their hours (§4), so not economic
  layup in the sense the guard was built to catch;
* **not published by CAISO as outages** — and CAISO is not wrong: the units
  were *available*.

That is not an error on either side. It is a **definitional seam**:

> **CNOG publishes UNAVAILABILITY. The CEMS detector measures NON-OPERATION.**
> A unit that is available but not committed is non-operating and not
> unavailable, so it appears in one instrument and not the other — by
> construction.

The residual over-count is therefore **available-but-not-committed capacity**:
offline multi-day spells that a marginal-cost test cannot classify because the
binding economics are *commitment* economics (start cost, minimum run, minimum
down), which live above the margin. The growth across 2023 → 2025 is consistent
with CAISO's deepening solar belly shortening and devaluing the evening runs a
CC start has to amortize against — stated as consistency, **not** as a
demonstrated cause: this finding does not measure start-cost recovery, and
that is exactly the open work in §6.

**Why this matters beyond bookkeeping (rule 1 `[R-STRUCT]`, rule 13
`[R-MEASURED]`).** These units belong in the availability envelope as
**available**, and the LP should decline to start them **on its own commitment
economics**. The detector currently deletes them from the envelope instead.
Deleting available capacity is a structurally wrong mechanism that reaches a
price level by removing supply rather than by declining it — the very shape
rule 1 forbids. It also explains the re-audit's direction-of-travel result
without any appeal to fit: restoring laid-up capacity *raised* CAISO prices
(§3b) because the RA must-offer bridge, not a scarcity margin, owns that
capacity's commitment.

## §6 — the lift condition, restated

The charter's freeze was held for "the residual over-count is unexplained". It
is no longer unexplained; it is **explained but not yet fixed**, and the fix is
a mechanism change, not a threshold change. What is required before the
residual can stop being an open root-cause item:

1. **Re-measure NEISO on a corrected published-side build.** NEISO's 1.29-1.36x
   is a `tail(1)` number against a different report; §1 invalidates the
   comparison as built. Whether NEISO's residual is the same seam is unknown.
2. **Test the commitment-economics mechanism directly** — does the observed
   idle/run split track start-cost recovery over the expected run (start cost
   vs spread × expected run hours), per unit? §4 shows the marginal test is
   uninformative here; it does not yet show the commitment test is informative.
   This is measurable from CAMPD operation + delivered fuel + published start
   costs, with no LP solve and no dispatch outcome (rule 13 clean).
3. **Only then**, decide the disposition: a commitment-aware second
   discriminator in the detector (so these windows leave the availability
   envelope as *available*, and the LP declines them), versus leaving the
   envelope alone and carrying the seam explicitly. Rule 19 `[R-ONE-MECH]`
   applies — CAISO already has `caiso_ra_mustoffer` owning commitment on this
   same capacity, and a second mechanism must replace or reconcile with it,
   never stack.

Nothing here changes a keeper, an extract, or a default. The guard stays
adopted and default-off exactly as the charter §8 verdict left it; the
corrected extracts stay (rule 14 — §2 shows their MW attribution is right).
The CAISO and NYISO re-tune verdicts are unaffected: both were measured as
keeper *sensitivity* to the envelope change, which §1-§5 do not touch.
