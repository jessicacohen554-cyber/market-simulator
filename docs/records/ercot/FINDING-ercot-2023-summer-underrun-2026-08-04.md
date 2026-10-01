# FINDING — the 2023 −30 % price underrun is 100 hours of Aug/Sep afternoon, and it is an ENERGY-OFFER defect, not a scarcity-mechanism one

**Session ercot-159 (owner redirect), 2026-08-04. NO LP, no solve, no mechanism
armed, keeper UNCHANGED (`2026-08-03-ercot158-pool-arm`).** Measured entirely on
committed artifacts: the keeper's own hourly sidecars, the committed
`actual_lmp_hourly_ERCOT.parquet`, and the committed NP6-905-CD series
`ercot_2023_ordc_reserves_hourly.parquet` (which carries ERCOT's own SCED
`system_lambda`, `rtorpa` and `prc` alongside `rtolcap`/`rtolhsl`).

## 1. Where the residual is

Load-weighted 2023: model **$43.08** vs actual **$61.97** → **−30.5 %**, an
annual gap of **$18.89/MWh**. Its distribution across the year is not merely
"summer" — it is two months, and inside them, two afternoon blocks:

| slice | share of the annual gap |
|---|---|
| August alone | **61.2 %** |
| August + September | **87.8 %** |
| June–September | **97.6 %** |
| Aug/Sep hours with actual > $500 (88 h) | **83.2 %** |
| Aug/Sep h14–16 | 45.4 % |
| Aug/Sep h17–21 | 34.6 % |
| **top 100 gap-hours (of 8,760)** | **98.3 %** (83 in Aug/Sep) |
| top 50 gap-hours | 74.3 % |

Every other month is within ±1.6 % of neutral, and four months are slightly
*over*. There is no diffuse underrun to chase: **the entire −30 % is ~100
hours.**

Note the hour-block split contradicts the standing framing. ERCOT-153/154/155
all worked the **evening** (h17–21). The larger block is the **afternoon
h14–16** (45.4 % vs 34.6 %), where the model is proportionally worst
(model $125 vs actual $378 = 33 % of actual, against $195 vs $319 = 61 % in the
evening).

## 2. What ERCOT's price in those hours actually was

Decomposing ERCOT's own settlement at the top-100 gap hours, using ERCOT's
published components:

| component | mean at the top-100 gap hours |
|---|---|
| actual RT settlement | **$1,487.84** |
| ERCOT SCED **system lambda** (the energy stack) | **$1,470.16** |
| ERCOT **RTORPA** (the ORDC scarcity adder) | **$36.03** |
| RTORDPA (incl. reliability deployment) | $32.60 |
| **model price** | **$441.27** |

**98 % of the gap is the ENERGY stack.** Among the 53 of those hours with
actual > $1,000, ERCOT's lambda averaged **$2,159** and exceeded $1,000 in
**49 of 53**. ERCOT's scarcity adder was a rounding error in the very hours the
model misses.

The model's own reserve channel confirms the same from the other side: at those
hours the model sits in ORDC shortfall in 82/100 hours (p50 1,465 MW) but its
reserve dual is **$0.15 p50 / $11.93 mean**, and ERCOT's measured RTORPA in the
same hours is only **$4.80 p50 / $36.03 mean**. The reserve-side gap is
**$24/h against a total gap of $1,047/h**. There is no missing scarcity adder to
recover — **ERCOT did not price those hours through ORDC.**

## 3. The corrected cushion picture (this supersedes the ERCOT-155 framing at these hours)

ERCOT-155 measured the model carrying **15.3–17.5 GW** of evening thermal
headroom against the real market's 0.9–2.8 GW (5.5–19×) and made that the
successor object. That statistic is an **evening average over all days**. At the
hours that actually carry the residual the model is far tighter:

| at the top-100 gap hours | GW |
|---|---|
| available thermal | 68.14 |
| dispatched | 61.51 |
| **headroom** | **6.63** (90.3 % utilisation) |
| of which CT_PEAKER | 1.92 (71.4 % utilised) |
| COAL | 0.13 (98.9 % utilised) |

ERCOT's own loading factor on its event days was 92.0–96.2 %. **The model is at
90.3 % — comparable, not 5–19× loose.** The cushion is real on an average
evening and largely absent in the hours that matter. Any successor built on the
"15–17 GW phantom headroom at the scarcity tail" premise is aimed at a quantity
gap that is ~2–3×, not ~10×, and cannot by itself close a $1,029/h energy-price
gap.

## 4. The defect

At ~90 % utilisation the model's marginal energy offer is **$441** (p50 $147);
ERCOT's cleared lambda at its comparable loading was **$1,470** (p50 $1,029).
This is corroborated exactly by ERCOT-155's own offer census, which measured the
model's stack reaching only **$103–116 at the 90 % headroom rung** before a
**38 MW** West CT tail jumps to $2,797 — i.e. the model has essentially **no
capacity priced between ~$120 and ~$2,800**, while ERCOT has GW of capacity
offered across $500–3,000 and cleared there for ~100 hours.

**The object is the LEVEL and SHAPE of the top of the energy offer curve in the
Aug/Sep scarcity afternoons — not commitment state, not reserve supply, not the
ORDC curve.**

## 5. Why this re-points the program (and what it does NOT re-open)

- **ERCOT-159's rejection is explained, not merely recorded.** The energy
  online-capability cap forced price up through the **reserve** channel
  (shortfall → ORDC/VOLL steps). ERCOT formed these prices through the
  **energy** channel. Forcing the right answer through the wrong channel is
  exactly why it hit the missed hours ($105 → $813) *and* fabricated 33 tail
  hours elsewhere: the reserve rows fire on a system-wide condition, so they
  cannot discriminate the ~100 hours that need it.
- **This is not the refused offer-dispersion arm** (ERCOT-155, rules 1/13/20).
  That refusal was about assigning event-day conduct prices to capacity ERCOT
  keeps **COLD** — capacity with no forward analogue for its offer. The object
  here is the **submitted offer curve of units that are ONLINE and near the
  margin** in those hours, which is measured conduct with an existing
  rule-13-admissible instrument and an armed consumer (the RT SCED offer wall).
  The distinction is status, and it is the same distinction ERCOT-158's pool
  turned on.
- **The instrument exists and its data blocker is closed.** The full-year
  delivery-2023 60-Day SCED corpus landed at ERCOT-157 (315 shards, all 365
  delivery days) and carries the submitted SCED curves for exactly these hours.
  The keeper already arms the RT wall over it.

## 6. The question a successor must answer first (Phase 0, no LP)

**Why does the armed measured RT offer wall — derived from ERCOT's own SCED
submitted curves — not reproduce ERCOT's cleared lambda in these ~100 hours?**
Candidate explanations, each answerable from committed artifacts plus the
corpus, and each pointing at a different (or no) lever:

1. **Bin resolution.** The wall conditions on net-load percentile bins; the
   Aug/Sep scarcity afternoons are the extreme tail. Do those hours land in a
   bin whose measured rungs actually carry the $500–3,000 conduct, or are they
   pooled into a bin whose median washes it out (the ercot43 collapse shape)?
2. **Row coverage.** The wall re-prices a masked row set. Is the model's
   *marginal* unit in those hours inside that mask, or is the margin set by a
   tranche the wall never touches?
3. **Class coverage.** The model's CT_PEAKER runs at 71.4 % with 1.92 GW idle
   while COAL is at 98.9 %. If the marginal unit is a CT, ERCOT-147 already
   found the CT band's submitted curve is daily-repriced and unresolvable
   without a Texas hub daily gas basis — **that is a live data blocker** (item
   8(b), licensing-blocked at ercot-160) and would bound what any CT-side lever
   can be identified from.
4. **Ceiling.** `ercot_offer_surface_price_cap_frac` is 0.95 × VOLL = $4,750,
   so the cap is not the binder; but the ladder may simply have no rungs in the
   $500–3,000 band to interpolate onto.

Only if Phase 0 identifies a *measured* deficiency with a forward story should a
lever be chartered; if the answer is "the corpus shows those hours' offers and
the wall drops them", the fix is a coverage repair, not a new mechanism.

## 7. Governance

No mechanism tested, no `ScenarioConfig` field added, no solve, no registration
owed (no run produced — the ERCOT-142/143/145/147/152/154/155 no-LP pattern).
Holdouts untouched: 2023 only, inside the training span (rule 22). ERCOT-scoped
(rule 25). No matrix cell changes (no mechanism adjudicated); the §5.1 queue
gains this object as the ERCOT-159 successor, superseding the ordinary-hour
commitment-level object that the ERCOT-159 log entry named — **that object was
derived from the 523 ordinary binding hours of a REJECTED arm, and the owner has
deprioritised it; this finding replaces it on the evidence above.**
