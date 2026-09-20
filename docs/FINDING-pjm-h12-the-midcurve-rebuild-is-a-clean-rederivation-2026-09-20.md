# FINDING — pjm-h12 card D-1: the offer-midcurve rebuild is a CLEAN rule-23 re-derivation. The coal defect is downstream, and it is NOT forcing (2026-09-20)

**Session:** pjm-h12 · **Branch:** `claude/pjm-h12-midcurve-seam-ar8wcb` · **HEAD:** `2c42c926a338ba916969badfcc1d4beb20e11107`
**ZERO LP MINUTES, ZERO SHARDS LAUNCHED.** Card D-1 is answered entirely from git and from the
keeper's committed sidecars, which is what the charter predicted ("this answer decides the whole
card and costs no LP"). Nothing here required a solve, so nothing was solved.
**Keeper untouched:** `2026-09-19-pjm-h11-c1seam-span` (CALIBRATED, 2023–2025) remains PJM's keeper.

---

## 1. Headline

1. **D-1a resolves to branch (i): the rebuild is LEGITIMATE and the table STAYS.** The rule 23
   `[R-FROZEN-DERIVE]` trigger is real, cited, and verified three independent ways — including at
   the **blob level**, which is stronger than the commit message the charter nominated as the
   evidence.
2. **Rule 14 `[R-ACCURATE]` independently REQUIRED it.** The old table priced 2020/2021/2022 from
   `pooled` — a capacity-weighted blend **of 2023–2025**. PJM's held-out years were being priced at
   an average of years that had not happened yet. Reverting that is not available to this lane.
3. **The +8.26 TWh on COAL_BIT is therefore a genuine model response to a better input**, and its
   mechanism is now measured rather than inferred: the rebuild made PJM coal **cheaper** in exactly
   the three years that moved — LONG_RUN mean implied-HR multiplier **−0.298 / −1.993 / −0.164**
   for 2020 / 2021 / 2022, against **+0.000 / +0.002 / +0.000** for 2023 / 2024 / 2025.
4. **D-1b: there is nothing to un-stack.** Every mechanism that forces PJM coal, summed, accounts
   for **4.00 % / 4.14 % / 0.99 %** of COAL class energy against a 30 % budget, and coal's floors
   **clear D-4** (the keeper's two D-4 failures are `st_netload_drag` and `cc_mustrun_per_plant`,
   neither of them coal). **PJM coal is over-generating ECONOMICALLY, not because a floor holds it
   on.** Under rule 19 `[R-ONE-MECH]` the enumeration returns essentially nothing, so a new floor
   would be stacking on a residual no floor is creating. The target is the coal **offer level**.
5. **Two things the h9c commit asserted that are NOT true as written** — both harmless to the
   keeper, both live for the next lane. §4.
6. **A latent reproducibility trap, found in passing:** the committed table depends on six years of
   corpus, but **both** the fetch script and the derive script still default to **three**. A bare
   re-run of the documented pipeline silently reverts the rule-14 repair. §5. **Not fixed by this
   lane** — the derive script is frozen under rule 23 and the pair must move together. Owner-facing.

---

## 2. D-1a — the verification, three ways

The charter named the commit message as the evidence. It is `73a682347d175fd001c8a5cfcd08e3241d03c82e`
(2026-09-16), *"pjm-h9c: re-derive the PJM offer surface over 2020-2025 — SOURCE DATA CHANGE"*, and
it does cite a source-data change as rule 23 requires: the corpus went from 36 month-files
(2023–2025) to 72 (2020–2025) from PJM DataMiner2's `energy_market_offers` feed. A commit message is
an assertion, so it was checked rather than believed:

| # | check | result |
|---|---|---|
| **V1** | the artifact's own `_provenance` corroborates the corpus claim | **CONFIRMED.** `n_month_files_parsed` **36 → 72**; `month_coverage` gains 2020, 2021, 2022 at **12 of 12 expected months each** — no partial year. `source` names delivery years `[2023,2024,2025]` → `[2020,…,2025]`. |
| **V2** | the derive script did not change (*"the derive ran unmodified"*) | **CONFIRMED AT THE BLOB LEVEL.** `scripts/data/derive_pjm_offer_midcurve.py` is blob `1e7ba58ab4bd1145d62c9041bec4fb8e280f11ea` at the old table's commit, at the rebuild commit, **and at HEAD** — byte-identical across the change. |
| **V3** | no residual was consulted, no value chosen | **CONFIRMED by construction.** The commit adds zero `ScenarioConfig` fields and zero scalars; the mechanism already prefers `years[str(year)]` and falls back to `pooled` only when that key is absent. Adding the key is what changed. |

Blob trail, for the record:

```
derive script  12aeb410 → 1e7ba58ab4bd1145d62c9041bec4fb8e280f11ea
               73a68234 → 1e7ba58ab4bd1145d62c9041bec4fb8e280f11ea   (unchanged)
               HEAD     → 1e7ba58ab4bd1145d62c9041bec4fb8e280f11ea   (unchanged)
midcurve table 12aeb410 → 5165951b2e300149c4a365273461698719e2a777   (OLD)
               73a68234 → 8dd1f4c98511cd1aef2ff0c380f0b27d5db742e3   (NEW, = HEAD)
```

**Verdict: branch (i).** The table is correct, it stays, and this lane proposes no change to it.

---

## 3. What actually moved — the quantification the card asked for

Units throughout are the surface's own **implied heat-rate multiplier** (`offer price / delivered
gas day`), 12 within-unit shares × 4 net-load bins = 48 cells per segment-year.
Armed segments are `pjm_offer_midcurve_segments = ['LONG_RUN','CC_LIKE']` — **`CT_FAST` is built but
never read by the solve.** That distinction carries most of the interpretation below.

### 3a. Training years 2023–2025 — old own-year vs new own-year (pure restatement)

| segment | year | cells moved / 48 | med \|Δ\| | p90 \|Δ\| | max \|Δ\| | mean Δ | up/down |
|---|---|---|---|---|---|---|---|
| **LONG_RUN** | 2023 | 10 | 0.000 | 0.050 | 0.050 | +0.000 | 5/5 |
| **LONG_RUN** | 2024 | 14 | 0.000 | 0.050 | 0.100 | +0.002 | 8/6 |
| **LONG_RUN** | 2025 | **0** | 0.000 | 0.000 | 0.000 | +0.000 | 0/0 |
| **CC_LIKE** | 2023 | 5 | 0.000 | 0.015 | 0.050 | −0.001 | 2/3 |
| **CC_LIKE** | 2024 | 27 | 0.050 | 0.050 | 0.150 | +0.012 | 19/8 |
| **CC_LIKE** | 2025 | **0** | 0.000 | 0.000 | 0.000 | +0.000 | 0/0 |
| *CT_FAST (unarmed)* | 2023 | 37 | 0.100 | 0.200 | **0.650** | −0.045 | 15/22 |
| *CT_FAST (unarmed)* | 2024 | 36 | 0.175 | 0.350 | **0.600** | +0.043 | 24/12 |
| *CT_FAST (unarmed)* | 2025 | **0** | 0.000 | 0.000 | 0.000 | +0.000 | 0/0 |
| **ALL** | | **129 / 432** | 0.000 | 0.145 | 0.650 | +0.001 | |

This reproduces h9c's own reported signature exactly (129 of 432, median 0.0, p90 0.145,
sign-balanced). Two readings it did **not** state, and they matter:

- **73 of the 129 moved cells are `CT_FAST`, which the solve never reads.** In the two armed
  segments the largest move in any training year is **0.10** (LONG_RUN) and **0.15** (CC_LIKE), and
  the LONG_RUN means are **+0.000 / +0.002 / +0.000**. The training-year contamination is real but
  is, for the armed surface, at the rounding grid. This is consistent with the keeper passing C1
  18/18 on the training years.
- **2025 moved exactly zero cells in all three segments.** That is a structural fact worth carrying
  forward, and it is the one that falsifies h9c's safety argument (§4a).

### 3b. Held-out years 2020–2022 — old `pooled` fallback vs new own-year (THE operative change)

This is the comparison that reaches the LP, because in these years the old table had no own-year key
and the mechanism fell through to `pooled`. Δ = new − old; **negative = the class got CHEAPER**.

| segment | year | med Δ | mean Δ | min Δ | max Δ |
|---|---|---|---|---|---|
| **LONG_RUN** | 2020 | −0.350 | **−0.298** | −1.150 | +0.550 |
| **LONG_RUN** | 2021 | −2.175 | **−1.993** | −2.750 | −0.950 |
| **LONG_RUN** | 2022 | −0.200 | **−0.164** | −1.550 | +1.050 |
| **CC_LIKE** | 2020 | −0.250 | −1.319 | −8.550 | +0.150 |
| **CC_LIKE** | 2021 | −0.175 | −1.055 | −7.800 | +0.400 |
| **CC_LIKE** | 2022 | +0.900 | +0.387 | −3.650 | +1.450 |
| *CT_FAST (unarmed)* | 2020 | −14.375 | −14.078 | −19.400 | −7.950 |
| *CT_FAST (unarmed)* | 2021 | −13.950 | −14.133 | −20.700 | −8.250 |
| *CT_FAST (unarmed)* | 2022 | −6.525 | −7.060 | −15.700 | −1.050 |

**`CT_FAST` moves by 7–14 multiplier points and is the single largest number in this whole
document — and it is inert**, because `pjm_offer_midcurve_segments` does not include it. A successor
reading this table must not attribute any dispatch change to those rows.

### 3c. LONG_RUN — the segment COAL_BIT reads

Mean over all 48 cells, and the top-of-curve belt where coal's **peak tranche** prices:

| year | source | mean mult | Δ vs old | belt (bin 0, shares .85/.95/.97/.99) |
|---|---|---|---|---|
| 2020 | old `pooled` → new own | 8.253 → **7.955** | **−0.298** | 9.68/9.97/10.12/10.47 → 8.53/9.38/9.78/9.97 |
| 2021 | old `pooled` → new own | 8.253 → **6.260** | **−1.993** | 9.68/9.97/10.12/10.47 → 7.42/7.72/8.03/8.47 |
| 2022 | old `pooled` → new own | 8.253 → **8.090** | **−0.164** | 9.68/9.97/10.12/10.47 → 9.47/9.97/10.18/10.68 |
| 2023 | own → own | 8.753 → 8.753 | +0.000 | — |
| 2024 | own → own | 8.895 → 8.897 | +0.002 | — |
| 2025 | own → own | 7.048 → 7.048 | +0.000 | — |

**2021 is the event.** Coal's committed rung (s = 0.45) goes 8.025/7.725/7.825/7.775 → 6.125/5.425/
5.325/5.525 across the four net-load bins — roughly **30 % cheaper**, and at 2021 delivered gas a
−2.0 multiplier is on the order of **$10/MWh** off PJM coal's offer. Cheaper coal dispatches more
coal. That is the mechanism behind the +8.26 TWh, stated as physics rather than correlation.

Note **2022 is not monotone with the others**: it gets *cheaper* at the bottom of the curve and
*dearer* at the top (belt bin 1 rises 9.22/9.57/9.68/10.03 → 9.72/10.28/10.53/11.07). Any successor
that models the rebuild as "a uniform coal discount" will mis-predict 2022.

---

## 4. Two h9c assertions that do not survive checking

Neither damages the keeper. Both are live for whoever touches this surface next, and both are
recorded here rather than left for a third lane to rediscover.

### 4a. "A 2020-2022 mask never contributes to a 2023-2025 unit's median physics" — FALSE as written

h9c's safety argument was that PJM re-keys masked `unit_code`s between vintages, so the added years
introduce disjoint keys and cannot disturb the training years. The code says otherwise:
`_unit_physics(files)` concatenates **every parsed file** and takes a per-unit median over the union,
and `_segments()` classifies on those medians. **Segment membership is therefore pooled across all
parsed years**, so any key that survives the 2022→2023 boundary can be re-segmented by the added
rows, which moves it between histograms and moves the training-year ladders. That the masks are
*mostly* disjoint is why the effect is small; it is not why it is zero, because it is not zero — 129
cells moved.

The clean falsifier is **2025 = exactly 0 cells in all three segments** while 2023 and 2024 move. A
fully disjoint-key story predicts zero everywhere; a pooled-membership story predicts movement
concentrated in whichever years share keys with 2020–2022, which is what is observed.

**Consequence for the program, stated plainly:** "adding data for held-out years cannot touch the
training years" is not a property of this derive. It is an empirical outcome that has to be measured
each time, and this time it came out small **in the armed segments only**.

### 4b. The OLD table was STALE against its own landed derive script

The old payload has no `conditioning` and no `season_of_month` key, and its `driver` string reads
*"edges shared with the frozen pjm-99 top-of-curve surface"*. Script blob `1e7ba58a` writes
`"conditioning": args.conditioning` and `"season_of_month"` **unconditionally**, and writes
*"edges AND conditioning shared"*. Both the script and the old table landed in the **same** commit
(`12aeb410`).

So the committed old table **cannot have been produced by the derive script committed beside it**.
It came from an unlanded earlier iteration and was never regenerated; h9c was the first execution of
the landed script. That has a consequence for attribution: **part of the 2023/2024 restatement is
this staleness being cured, not the data addition**, and the two cannot be separated from git
because the iteration that produced the old table exists nowhere. The honest statement is that
§3a's 129 cells are an **upper bound** on the data-addition effect, not a measurement of it.

This is a provenance defect in the *old* artifact, now cured. It is recorded because "the old
number" is no longer a defensible baseline for anything.

---

## 5. A latent reproducibility trap (found in passing, NOT fixed here)

The committed table's provenance declares 72 month-files over 2020–2025. But:

- `scripts/data/fetch_pjm_energy_offers.py` — `--years` **default `[2023, 2024, 2025]`**
- `scripts/data/derive_pjm_offer_midcurve.py` — `--years` **default `[2023, 2024, 2025]`**
- `data/raw/pjm-energy-offers/README.md` — still documents *"the 3-year corpus (2023–2025)"* and
  gives `fetch_pjm_energy_offers.py` (bare) as the regeneration command.

**Running the documented pipeline with its own defaults regenerates the OLD three-year table and
silently reverts the rule-14 repair**, with no error and no diff in any script. The corpus payload
is gitignored (DataMiner2 redistribution restriction, `docs/data-licensing.md` §4), so the on-disk
state that distinguishes the two cannot be checked into the repo — the defaults *are* the contract.

**Not fixed by this lane, deliberately.** The derive script is frozen under rule 23
`[R-FROZEN-DERIVE]`, and the two defaults must move together — fixing only the fetch default would
create the worse state where the corpus holds six years and the derive still reads three. The README
is fixed (documentation, no behaviour), and the default pair is put to the owner in §7.

---

## 6. D-1b — the coal forcing enumeration (rule 19 `[R-ONE-MECH]`)

From the keeper's own committed `legitimacy_diagnostics.json`. **No re-solve**, as the card required.

Every mechanism that forces PJM COAL, and its share of class energy:

| year | `coal_mustrun` | `reliability_floor` | `chp_steam` | **total forced** | class energy | **forced share** | budget |
|---|---|---|---|---|---|---|---|
| 2023 | 4.3002 | 0.2083 | 0.0295 | **4.538 TWh** | 113.443 TWh | **4.00 %** | 30 % |
| 2024 | 4.2251 | 0.4037 | 0.0506 | **4.679 TWh** | 113.039 TWh | **4.14 %** | 30 % |
| 2025 | 1.3833 | 0.0556 | 0.0008 | **1.440 TWh** | 145.976 TWh | **0.99 %** | 30 % |

And the D-4 off-window check: the keeper's D-4 does read `passed: false`, but **its failures are
`st_netload_drag` (plant 3138) and `cc_mustrun_per_plant` × CC_REGULAR (plants 2393, 7153)**.
**No coal mechanism appears in any D-4 failure row.** Coal's floors bind inside their declared
windows.

**The conclusion, which is the point of the card:**

> PJM coal is over-generating by **economics, not by forcing**. At most ~4.5 TWh of a 113–146 TWh
> class is held on by any mechanism, against a C1 error of **+16.90 TWh** (registered keeper) to
> **+25.16 TWh** (the control at HEAD), summed over six years. Removing every coal floor in the
> model could not close it.

Under rule 19 the enumeration exists to stop a new floor being stacked on an old one's unexplained
residual. Here it returns the opposite answer: **there is no floor stack to reconcile, and adding one
would be a mechanism aimed at a residual that forcing does not produce.** That is forbidden by rule 1
`[R-STRUCT]` regardless of what it would do to the fit.

**The target is the coal OFFER LEVEL — where coal sits in merit order against gas — not a floor.**

---

## 7. What this lane did NOT do, and the questions it leaves open

**No shards were launched and no LP ran.** D-1a resolved to "the table is correct", which is the one
branch of the card that carries no arm to solve. Launching six containers to re-measure a table this
lane just certified would have spent ~6 containers to learn nothing. The charter's shard recipe,
`pjm_h11_compose_span.py`, and the PJM keeper posture signature are all untouched and ready for the
lane that does have an arm.

**Card D-2 (the export seam) is NOT advanced.** The matrix cell `seam_neighbour_hourly_ladder` is
`O`: built, screened, full span solved, owner-ruled not promotable because its central structural
claim (hourly *r* improves) was contradicted by the solve, and the charter says do not re-run it as
is. pjm-174 already located the defect — the ladder is anchored Q-Q to the **measured** DA duration
curve and the LP clears it against the **model's** — and already holds the proof: quantile-mapping
the model price onto the measured DA marginal, hourly ranking untouched, feeding the **unchanged**
ladder returns 31.732 / 37.805 TWh, the measured volume exactly. A successor is therefore a
**rank-preserving re-anchoring** of the ladder's price argument, and it must demonstrate the hourly
claim the last arm failed. That is a PRECOMMIT-and-six-shards task and it is not started here.

### Open questions for the owner

- **Q4 (new) — the default pair in §5.** Move `fetch_pjm_energy_offers.py` and
  `derive_pjm_offer_midcurve.py` both to `--years 2020..2025`? It restores reproducibility of the
  committed artifact and changes no solve, but it edits a rule-23 frozen derive script, so this lane
  will not do it unilaterally.
- **Q1 (carried) — the three truncated ladder rungs.** Untouched, as the charter instructed.
- **Q3 (carried) — the MER dual is ungated.** Untouched. Still an off-registry knob that runs a
  second HiGHS `run()` on every pass of every solve of every ISO, in the post-solve window where six
  pjm-h11 shards were OOM-killed.
- **Proposed rule 32(c)(8) addendum** — still unadjudicated.

**Nothing is at risk of being lost with this container.** This lane solved nothing, so there are no
bundles on ephemeral disk and rule 31 `[R-RETAIN]`'s promotion question has no subject here. The
keeper's own bundles (`results/calibration/pjm_h11_keeper_span/`,
`pjm_h11_touchpoint_span/`) are the committed, registered keeper and are unchanged.
