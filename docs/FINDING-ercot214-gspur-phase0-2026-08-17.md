# FINDING — ercot-214 (G-SPUR-2023 Phase-0): the mid-band spill is ADDER-MADE and its maker is IDENTIFIED — the AS-product shortfall-ramp penalty (VOLL/12 = $416.67) leaking through the all-tier cap dual into the published-anchor adder; the ONE lever is a counterpart decontamination whose full-span consequences are EXACTLY measured pre-solve, and it KILLS G-C3c — escalated to the owner, Phase-1 NOT entered

**Session ercot-214, 2026-08-17, branch `claude/ercot-214-g-spur-spill-c1qmfk`.**
Keeper resolved fresh at session start AND end:
**`2026-08-16-ercot213-arm-pubanchor`** — UNCHANGED; determination NOT-YET,
fail set {C3b-2023} alone, C3c-2025 the single ledgered CAVEAT. **Phase-0
READ-ONLY as dispatched: no LP, no solve, no year scored, no run registered,
no bundle modified, no cell verdict minted** (the ercot-163/170/208 no-LP
precedent). Committed probe: `scripts/probes/ercot214_gspur_phase0.py` →
`results/calibration/ercot214_gspur_phase0.json`. Everything below is read
from the two registered ercot-213 bundles' committed `hourly/` sidecars, the
committed actual-RT parquet, and the published NP6-905-CD telemetry already
on disk — no new data, no measured input touched.

## 0. VERDICT — the three dispatched questions, answered

**(a) Adder-made or energy-made? BOTH, in two cleanly separated populations —
and the G-SPUR *movement* (the open lane) is entirely adder-made.** The
keeper's 17 spurious 2023 hours split exactly:

* **8 shared hours** (in the control's 9 too): mid-August afternoons
  (Aug 15–31, hod 13–20 CST), **energy-made** — λ alone ≥ $150 with adder
  ≤ $43. They belong to the surrounding recipe, predate the ercot-213 delta,
  and are zonally differentiated real price formation (West decoupled at
  ~$40 while the load zones sit at $155–284).
* **9 keeper-only hours**: June 11–19 + July 10, hod 15–19 CST,
  **adder-made** — λ = $50–77 with a near-constant written adder of
  $411–414. The control's 9th hour (h5822, Aug 31 14h) left the band
  *upward* in the keeper (λ $172.74 + adder $410.53 = $583.26 > $500), so
  the net is 9 − 1 + ... = 17.

**(b) Clustering:** the 9 new hours are one regime — early-summer afternoons
with cheap energy (λ p50 $62), the ORDC total family comfortable (its own
marginal step $0.1–8.6), and the **netted reserve-supply cap binding below
the sum of the AS-plan product requirements**, with NonSpin 73–414 MW short.
No zonal structure: the adder is a system-wide broadcast.

**(c) What did the real market do in those hours? Essentially nothing.**
Published settled RTORPA in the 9 hours: **$0.11–$1.32** (RTORDPA 0–$13);
RTOLCAP 6,994–8,655 MW, PRC 5,410–5,888 MW; actual RT $68–$146, every hour
< $150. The model's own `ercot_ordc_total` family dual in the same hours is
**$0.15–$2.51 — matching the published RTORPA almost one-for-one** — while
the written adder is $411–414.

**The maker, identified exactly.** In **808 of 808** adder-writing hours
across all three years (564/177/67), the recovered all-tier supply-cap dual
decomposes to the last cent as

```
gamma_all(t) = k(t) x (VOLL / ercot_as_n_ramp) + gamma_ordc_family(t),   k integer
```

i.e. the AS-product shortfall-ramp step (`nyiso_rcpf_product_shortfall_steps`
with the registered `ercot_as_n_ramp = 12`: steps at $416.67, $833.33, …)
**plus** the ORDC total family's own balance-row dual. One capped reserve MW
serves a product row and the total row simultaneously, so the cap dual is
their SUM — and the published-anchor formula rescales the whole sum into the
written adder. The 9 spill hours are k = 1 with a tiny family term
(416.67 × rescale ≈ $411–414). Verified: h2034 $1,835 = 1,666.7 + 167.9;
h4094 $2,543 = 2,500 + 42.6; every uncontaminated August hour k = 0 with
γ_all = γ_family exactly.

**The market-design ground, already in the repo's own words**
(`src/market_sim/model/reserves/spec.py:1420`, the `ercot_ordc_only_scarcity`
block): *"2023-25 ERCOT has NO real-time per-product scarcity pricing — RT
reserve scarcity prices via the ORDC on the REALIZED total online reserves …
a product-vs-capability squeeze triggers RUC commitment, not a price."* The
ramp penalty is model scaffolding for the DAM award's physical withholding;
exporting it into the RT energy price manufactures a price formation channel
the 2023–25 design cannot produce. The published protocol cap (G-CAP) does
not catch it because the leak respects the cap.

## 1. THE ENUMERATION (committed sidecars; `_ercot173_ab` conventions)

Keeper 17: h3879, 3953, 4003, 4047, 4048, 4049, 4072, 4073, 4576 (the
adder-made 9) + h5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821 (the shared
8). Control 9: the shared 8 + h5822. Full per-hour decomposition rows
(λ / adder / overlay / γ_all / γ_family / family req-held-shortfall /
published RTORPA·RTORDPA·RTOLCAP·RTOFFCAP·PRC / actual RT·DA) are in the
committed probe JSON. The signature row, h3879 (2023-06-11 15h): model
$462.76 = λ $49.68 + adder $412.84 + overlay $0.25; family req 8,307 / held
6,604 / short 1,703 with family dual **$0.31**; NonSpin short 414 MW with
every product-family dual at **$416.67**; published RTORPA **$0.26**, actual
RT **$79.60**.

The total-family construction itself is **verified faithful** in the same
measurement: its effective evaluation level is the gross capability
(10,700 − shortfall = held + credits — reproduced by hand at h4003: step
$2.51 vs sidecar dual 2.51; h5443: $14.95 vs 15.04), and its dual tracks
published RTORPA with rank-corr 0.709/0.807/0.758 (2023/24/25) over the
writing hours — slightly better than the contaminated γ_all in every year.

## 2. THE DEEP HOURS — the same leak carries the keeper's tail

Contaminated hours (k ≥ 1) with adder > $100: **116 of 2023's 117** deep
hours, **16 of 16** (2024), **3 of 3** (2025). In the 2023 deep set: γ_all
p50 **$876** vs γ_family p50 **$25.7**, actual RT p50 **$668.9** — but
published settled RTORPA p50 **$14.2**, > $100 in only **15** of the 116
(published 2023 total: 17 h > $100 vs the arm's 117). The real 2023 tail was
overwhelmingly **energy/conduct-made** (actual > $200 in 181 h against 17 h
of > $100 published adder), and the real online tier was not depleted in the
model's deep hours (RTOLCAP p50 6,805 MW). So the keeper's C3c-2023 gain
(57 → 123) and its C3a-2023 gain ride the SAME phantom channel that makes
the spill: the model reproduces a conduct-made tail through an AS-plan
penalty ramp the real market does not price.

## 3. THE ONE LEVER — counterpart decontamination (zero scalars), and its exact scorecard

**Proposed lever:** inside the armed published-anchor branch, write the ORDC
component of the cap dual instead of the contaminated sum —
`gamma' = min(gamma_all, gamma_ordc_family)` (equivalently: drop the ramp
term the decomposition isolates), keeping the `(VOLL − λ)` anchor, the
single-counterpart form, the protocol cap, and the netting untouched.
**Identification source:** the 2023–25 market-design fact above (no RT
per-product scarcity pricing; the ORDC on realized total reserves is the
only RT adder — spec.py:1420's own citation block, the IMM-documented
design), plus the two-regime measured match of γ_family to published RTORPA
(§1, §2). Zero fitted scalars — it swaps which committed LP dual is read.
The in-LP role of the ramp (physical withholding of the DAM plans) is
untouched; only its export into the written price stops.

**Because the anchor is post-solve additive (it moves no MW), the lever's
full-span consequences are EXACT from committed bytes** — the LP solution,
λ, dispatch, shed, and every family dual are identical; only `ordc_adder`
and `price` change. Measured (probe §counterfactual, `_ercot173_ab` basis):

| | 2023 arm → repointed | 2024 arm → repointed | 2025 arm → repointed |
|---|---|---|---|
| **G-SPUR** (own gate) | **17 → 9** = the control set EXACTLY | **13 → 11** = the control set EXACTLY | 0 → **1** (h3355¹) |
| tail > $200 (actual 181/53/31) | **123 → 67** | **33 → 22** | **3 → 1** |
| c3a (probe basis) | +0.40 → **−30.38 %** | 14.06 → 7.88 % | 1.21 → 0.51 % |
| adder h > $100 (published 17/4/0) | 117 → **37** | 16 → **3** | 3 → **0** |
| adder h > $1 (published 294/78/14) | 184 → 175 | 37 → 36 | 7 → 5 |
| max adder | $4,701.14 → **$4,701.14** (the VOLL-cap hour, untouched) | $2,049 → $356 | $1,197 → $14.61 |
| G-CAP | 0 violations | 0 | 0 |
| G-SHED / G-SPAN / G-COAL148 / G-DOF / G-D2 | unchanged BY IDENTITY (post-solve delta; dispatch bytes identical) | | |

¹ h3355 (2025-05-20 19h) is **energy-made** (λ $214.30, actual $134.84) and
was already above-band in the arm only because a $1,196.56 phantom adder
pushed it out the top — the same band-top blindness as h5822. The repoint
restores G-SPUR to the energy-made baseline in all three years.

**And the honest half: the lever KILLS G-C3c in every year** (123 → 67 away
from 181; 33 → 22 away from 53; 3 → 1 away from 31), because the keeper's
tail is measured to be carried by the ramp leak (§2). Under the inherited
ercot-213 §3 direction-blind gates, an armed A/B of this lever is
**REJECTED-AS-ARMED before any solve runs.**

## 4. WHY THE TWO STANDING CANDIDATES ARE NOT THE LEVER (both measured, neither guessed)

* **(i) The published two-basis form (increment (c))** — REFUTED as the
  spill lever. The spill's maker is the ramp term in γ_all, which no curve
  or tier re-basis touches; and in the deep hours the online tier cannot
  legitimately price what reality priced through offers (published RTORPA
  p50 $14.2 there, RTOLCAP p50 6,805 MW). The online/total distinction does
  not bite in the 9 hours: the squeezed product is offline-capable NonSpin
  while the online tier was comfortable (RTOLCAP 7.0–8.7 GW).
* **(ii) An energy-side object** — REFUTED for the movement. The 9 new
  hours are adder-made (λ $50–77). The energy-made population (the shared 8
  + h3355-2025) is the CONTROL's own baseline, unchanged by the ercot-213
  delta — a different, pre-existing object that this lane's G-SPUR delta
  never measured.

## 5. PHASE-1 NOT ENTERED, AND WHAT THE OWNER IS BEING ASKED

Phase-1 is not entered: the delta is post-solve, so a full-span A/B would
reproduce the §3 table bit-for-bit at the cost of two multi-hour solves, and
its mechanical verdict under the inherited gates is already known
(**G-SPUR passes as the object's own gate; G-C3c kills in all three
years**). Solving to register a known kill adds no information; registering
it would spend roster and compute on ceremony.

What Phase-0 establishes is a genuine fork, and it is the owner's (the
standing structural standard has been applied twice in this lane, both times
over a mechanical kill — ercot-188, ercot-213):

* **The structural reading (rule 1's second half):** the keeper's
  C3c/C3a-2023 gains are reached through a mechanism that isn't real — an
  AS-plan penalty ramp priced into RT energy, which the 2023–25 design
  cannot emit. The decontaminated form writes adders at the published order
  of magnitude (37 vs 17 published h > $100; max unchanged at the true
  VOLL-cap hour), restores G-SPUR to the energy-made baseline in every
  year, keeps G-CAP at zero violations, and returns the 2023 tail to the
  model-class-limitation ledger where ercot-209/211 adjudicated it
  (conduct: Door A closed; C3c the ledgered caveat). The mid-band lane
  closes as a solved identification.
* **The gate reading:** G-C3c moves away from actual in all three years and
  C3a-2023 gives back ~31 pp (probe basis) — the very movement the owner
  promoted ercot-213 to obtain, and Q-B/R-A forbid using either direction
  as a basis.

If the owner wants the lever armed despite the known G-C3c kill (or with an
owner-amended gate set that recognizes the tail as phantom-carried), the
Phase-1 recipe is one boolean on the keeper recipe and the precommit is a
paragraph: the counterfactual here IS the landing zone, exact by
construction. If the owner declines, the spill lane closes as IDENTIFIED —
its mechanism named, measured, and priced — with the phantom channel
carried as the keeper's known price-formation caveat.

**A reporting defect this measurement also surfaces, flagged not fixed:**
G-SPUR's [150, 500] band is blind to phantom adders that overshoot the top —
h5822 (2023) and h3355 (2025) each read as *improvements* in the arm while
being made strictly worse ($583 and $1,411 against actuals of $145 and
$135). Any future gate revision should count `actual < 150 & model ≥ 150`
without the upper lid, or report both.

## 6. GOVERNANCE

Q-B FINAL + R-A cited and honoured: every C3a/C3b-2023 number above is
side-effect reporting at full magnitude; the lever proposal rests on the
market-design identification and the G-SPUR object, and the §5 fork
explicitly declines to weigh residual direction. ercot-206 B0 honoured — no
LOLP-table arming; the published NP6-576-ER table was not read. ercot-211
Door A honoured — no conduct object touched; the §2 attribution cites the
existing record only. V0/ercot-201 DO-NOT-REDO honoured — no
tightness-conditioned identification; RTOLCAP/RTOFFCAP entered only as the
already-armed cap telemetry (FFR-8B §4). 28a honoured — the bare netting was
not re-run (nothing was run). Rule 22: no year solved or scored; committed
artifacts only. Rule 25: ERCOT only. Rule 13: no measured outcome fed back —
the published RTORPA series is read as *evidence about a mechanism*, never
as an input. Rules 5/23: the proposed lever carries zero scalars. Rule 28:
no mechanism tested ⇒ no cell verdict minted; the `ercot_multiproduct_as`
cell note carries the Phase-0 attribution (same-session edit), matrix
integrity re-checked. Rule 27: edits local, exact on-disk bytes pushed,
≥300-line pushed files blob-verified. No new workflows, no cron, no PR
(push-and-stop on the designated branch).

**Session consumed the ercot-214 shorthand. Next shorthand: ercot-215**
(ercot-199 remains unclaimed).
