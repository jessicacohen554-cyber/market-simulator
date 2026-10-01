# PREREG miso-204 — DECOMPOSE THE TAIL BEFORE MOVING IT: the published MEC / MCC / MLC components of MISO's own price in the 15 scarce hours (2026-09-03)

**Session:** miso-204, branch `claude/miso-lmp-decomposition-sj1sq5`.
**Keeper at open:** `2026-09-03-miso-202-unitclip` (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone; C3c the single ledgered caveat; C6 attested
(ledger 41/2, n_residual 2). `audit_keepers --iso MISO` PASS 0/0. MISO holds
**no** `complete`/`final` marker; the holdout freeze is active (rule 22:
2023–2025 only).

**COMMITTED BEFORE ANY ADJUDICATING STATISTIC.** At the time of writing, the
measurements read are exactly: `_miso202_c3a_2025_anatomy.json`,
`_miso203_scarce_hour_identity.json`, `FINDING-miso202-…`, `FINDING-miso203-…`,
`PREREG-miso203-…`, the MISO mechanism-matrix shard, the `miso-79` calibration-log
entry, the *schema* of `data/raw/lmp-data/MISO/miso_hub_lmp_<year>_rt.csv.gz`
(row counts, the three `value` labels `LMP`/`MCC`/`MLC`, the eight hub node
names, 365/366/365 dates), and the *construction* of the two committed probes'
price series. **No MEC has been computed anywhere. No component value in any
scarce hour, ordinary hour, hub or year has been read, printed, or looked at.**

---

## 0. Charter, and why this is a MEASUREMENT and not a lever

The miso-204 charter is explicit: *decompose the tail before moving it.* Two
sessions have located the object and it is now narrow:

* **miso-202** — C3a-2025 is **not a level miss**. The model's Jun–Jul median and
  p75 are *higher* than actual; the gap opens only past p90; **15 hours** (the
  top 1 % of actual Jun–Jul hours, threshold $238.93) carry **99.9 %** of the
  mean gap and the other 1,449 contribute **−0.00**.
* **miso-203** — those 15 hours are an **evening net-load ramp** window (13 of 15
  in h18–h21 over 9 days), **not** extreme in load (p88.4), dry-bulb (p89.6) or
  capacity adequacy (44.3 GW reserve-eligible idle, 0.0 MWh unserved). The model
  prices them **$38.84–165.58** against an actual **$244.22–1,669.52**.

**What nobody in this lane has ever read is the actual price's own published
components in those hours.** `miso_hub_lmp_<year>_rt.csv.gz` carries `LMP`,
`MCC` and `MLC` rows per hub per hour; both committed probes filter
`value == "LMP"` and **discard the other two thirds of the file**. miso-203
deliberately did not compute the decomposition so that it would stay behind this
session's pre-registration.

**This PREREG licenses NOTHING.** Its output is an object identification. Any
lever it re-aims toward must then clear its own bound (charter (d)) — the object's
own percentile in its own driver — **before** a solve is spent. No
`ScenarioConfig` field is minted in this session on the strength of §2 alone.

---

## 1. The instrument, fixed now

### 1.1 The decomposition

MISO settles `LMP = MEC + MCC + MLC`. The file publishes `LMP`, `MCC`, `MLC`, so

```
MEC(hub, hour) = LMP(hub, hour) − MCC(hub, hour) − MLC(hub, hour)
```

is an **identity**, not an estimate, and carries **zero free parameters**.

### 1.2 The series, inherited verbatim from the two committed probes

The hub-average actual price is reproduced with the **same construction** that
defined the 15 hours and reproduced the C3a verdict to 0.0004 pp
(`_miso202_c3a_2025_anatomy.json` a0): read the gz, filter the `value` label,
`groupby("date")[he01…he24].mean()` over the **eight named trading hubs,
equal-weighted**, sort by date, ravel, truncate to 8760. The identical function
is applied to each of the three labels, so the three component series are on the
same index as the `LMP` series that selected the hours. **No re-selection of the
hour set is permitted in this session** (TRAP 3).

The model price is the keeper's committed `hourly/system_<year>.parquet`, P1
rows, `groupby("hour")["price"].mean()` over the six model zones — again the
committed construction, unchanged.

### 1.3 The three populations, fixed now

Every statistic below is computed on **all three** of these, so the scarce-hour
number is read against its own baseline and never in isolation:

| population | definition |
|---|---|
| **OBJ** | the 15 scarce hours — Jun–Jul hours whose actual hub RT LMP is in the top 1 % of Jun–Jul (thresholds 100.42 / 129.68 / 238.93) — **the anatomy's own set, byte-identical definition** |
| **JJ** | all 1,464 Jun–Jul hours |
| **YR1** | the 88 top-1 %-of-year hours |

### 1.4 The shares, defined now so they cannot be chosen later

Per hour `h`, with `P_model(h)` the model's zone-mean P1 price and each actual
component the equal-weighted hub mean:

```
excess(h)   = LMP(h) − P_model(h)                       # what C3a is short
energy(h)   = MEC(h) − P_model(h)
cong(h)     = MCC(h)
loss(h)     = MLC(h)
```

`energy(h) + cong(h) + loss(h) ≡ excess(h)` **exactly, by construction** — this is
an identity and its residual is asserted at 0 (N-2). The reported shares are the
**mean over the population**:

```
share_energy = mean(energy) / mean(excess),  etc.
```

The mean (not the median) is the primary statistic **because C3a is itself a
load-weighted mean and the object is defined by the 99.9 % of the mean gap those
hours carry**. The per-hour *count* of which component is largest is reported as
a robustness read with its own pre-committed interpretation (§2, R-1) and
**cannot flip the verdict**.

---

## 2. The gates, with the decision rules FIXED IN ADVANCE

| gate | construction | rule fixed now |
|---|---|---|
| **N-1** MEC hub-invariance | max−min of `MEC` across the 8 hubs, per hour | MISO prices a **single system-wide** MEC. If `max−min < $0.51` (one cent above two-decimal rounding on a difference of two rounded quantities) in **≥ 99 %** of OBJ ∪ JJ hours, the sign convention and the decomposition are **CONFIRMED**. If not, the convention is reported as **UNCONFIRMED** and the alternative `MEC = LMP + MCC + MLC` is tested and whichever yields hub-invariance is used, **stated as such**. |
| **N-2** additive identity | `max abs(LMP − (MEC+MCC+MLC))` over every row | must be `0` (identity). A nonzero value is a stop-the-line instrument failure. |
| **G-1** *(the charter's (a))* which component carries the excess | `share_energy`, `share_cong`, `share_loss` on **OBJ**, per year | **ENERGY object** iff `share_energy ≥ 0.50` in **2025**. **CONGESTION object** iff `share_cong ≥ 0.50` in **2025**. Neither ⇒ **MIXED**: the larger is named as the leading component and **explicitly not called dominant**. 2023/2024 are reported and may add a caveat; **2025 decides**, because 2025 is the failing year and the sole ground of the NOT-YET. |
| **G-2** *(the charter's (b))* cross-hub dispersion | per hour, `sd` and `max−min` of `LMP` across the 8 hubs; the OBJ mean against the JJ mean | **SPLIT signature** iff the OBJ mean `max−min` is **≥ 2×** the JJ mean in 2025 (a binding-constraint event splits the hubs). **TOGETHER signature** iff it is **≤ 1.25×**. In between ⇒ **INDETERMINATE**, reported as such and given no weight. |
| **G-3** *(the charter's (c))* the re-aim | the §5 map, applied mechanically to the G-1 verdict | no discretion: §5 is written before the numbers and is applied as written. |
| **G-4** *(the charter's (d))* the bound | only reached if a lever is proposed | **no lever is bounded and no solve is spent in this session unless G-1 returns a verdict whose §5 row names an OPEN or UNTESTED family.** If the named family is `G` or `R`, the session **stops at the finding** (§6 stop rule). |

**R-1, the robustness read, with its interpretation fixed now.** The per-hour
count of which component is largest in OBJ. If the count majority and the
mean-share verdict **agree**, the verdict is reported as concentrated *and*
typical. If they **disagree**, the verdict stands on the mean share (the object
is defined by mean gap) and the disagreement is reported as a **first-class
qualification in the headline**, naming how many hours and which component.

---

## 3. Predictions, scored against interest

| # | prediction | conf |
|---|---|---|
| **P1** | **N-1 confirms**: MEC is hub-invariant to within $0.51 in ≥ 99 % of hours. MISO publishes one system-wide energy component. | 0.80 |
| **P2** | **G-1 returns ENERGY** in 2025: `share_energy ≥ 0.50`. Reasoning stated in advance: the model has 44.3 GW of reserve-eligible idle and 0.0 MWh unserved, and the actual reaches $1,669.52 — a level a hub congestion component rarely reaches, and one that reads like system-wide scarcity pricing on a ramp. | 0.70 |
| **P3** | `share_cong` in 2025 OBJ is **< 0.25**, and the mean hub-average `MCC` in those hours is **< $60/MWh**. | 0.65 |
| **P4** | `share_loss` **< 0.05** in all three years. Losses are a few percent of price and do not move at stress. | 0.90 |
| **P5** | **G-2 returns SPLIT**: OBJ mean cross-hub `max−min` is ≥ 2× the JJ mean in 2025. Congestion intensifies at stress *even when it is not the leading component* — P5 and P2 are deliberately **not** the same claim, and both can be true. | 0.70 |
| **P6** | *(against interest)* **at least 3 of the 15** 2025 hours are congestion-largest at the hour grain, i.e. R-1 disagrees at least partially with the mean-share verdict. | 0.55 |
| **P7** | The energy component of the 2025 excess is **large in absolute terms**: mean `MEC` over OBJ ≥ $250/MWh against a model mean under $80/MWh. | 0.60 |
| — | **net: P(this session arms a mechanism or spends a solve)** | **0.10** |

**P2 is the load-bearing prediction and it is the one most likely to be wrong in
the way that matters.** If it is wrong — if congestion carries the excess — then
every lever this lane has queued (ORDC, offer level, capability removal, a ramp
product) is aimed at the wrong object, and §5 says so in advance.

---

## 4. Traps, with pre-committed counter-measurements

| # | trap | counter-measurement, fixed now |
|---|---|---|
| **TRAP 1** | **Sign convention.** `MEC = LMP − MCC − MLC` could be backwards, and a backwards MEC would make an energy object look like a congestion object or vice versa. | **N-1 is the counter-measurement and it is decisive**: only the correct convention yields a hub-invariant MEC, because MISO prices one system-wide energy component. Both conventions are computed if the first fails N-1, and the finding states which was used and why. |
| **TRAP 2** | **The 2024 leap-day misalignment.** The committed construction takes `arr[:8760]` from a **366-day** 2024 file, so every actual hour after Feb 28 sits **24 h ahead** of the model's fixed non-leap clock. The stamps in `_miso203_scarce_hour_identity.json` are model-clock labels on real-calendar data. | **The TRUE calendar date of every scarce hour is reported beside the model-clock stamp, in every year**, and the finding states plainly which model-vs-actual hour-matched quantities are offset. **The decomposition itself is immune** — it is computed entirely within the actual series, at one index, so all three components are the same real hour. **The hour set is NOT re-selected** (that would move the object mid-session). Whether the misalignment is a defect worth repairing is **named, not chartered**. |
| **TRAP 3** | **Re-selecting the object.** A decomposition that disappoints invites redefining "scarce". | The OBJ definition is inherited byte-identically from `_miso202_c3a_2025_anatomy.json` and is **frozen in §1.3 before any number**. JJ and YR1 are fixed in the same breath so no third window can be introduced afterwards. |
| **TRAP 4** | **Basis mismatch.** The hub average is **equal-weighted over 8 trading hubs**; C3a is **load-weighted over 6 model zones**. A verdict could be an artifact of the weighting. | The full decomposition is **also** computed on a load-weighted hub basis, using a hub→zone map declared in the probe and the keeper's own committed zonal `demand`. **The verdict is taken on the equal-weighted basis** — that is the series that defined the 15 hours and reproduced the C3a instrument to 0.0004 pp. The load-weighted version can **add a caveat and never flip the verdict** without an explicitly stated re-adjudication. |
| **TRAP 5** | **Reading a measurement as a licence.** "Energy dominates" would be an easy licence to re-open ORDC. | §5 is written **now** and mapped mechanically. The `ordc_scarcity_overlay` cell is `G` on **structural** grounds (miso-163, re-affirmed by owner ruling), and rule 28(a) requires new evidence **defeating those grounds specifically** — a component share is not that. §5's ENERGY row therefore routes to a **finding and an owner question**, never to an arm. |
| **TRAP 6** | **Treating the model's own price as decomposable.** The model's zonal dual has no loss component (`zonal_loss_surface` is `R`, off) and its congestion is a 6-zone aggregate, so a *model-side* MCC/MLC does not exist at comparable grain. | The decomposition is applied to the **actual only**. `P_model` enters exactly once, as the subtrahend in `energy(h)`, and the finding states explicitly that `share_energy` therefore absorbs any model-side congestion misplacement. This is a **stated limitation of the instrument**, declared before the result. |

---

## 5. The re-aim map — written before the numbers, applied mechanically

| G-1 verdict | what the object is | where the queue points, and what it is allowed to do |
|---|---|---|
| **ENERGY** (`share_energy ≥ 0.50`) | **system-wide energy price formation in the evening ramp.** The model's marginal unit in h18–21 is priced 5–10× below the market with ample idle capability. | Consistent with miso-203 §10(4). The aimed families are: `ordc_scarcity_overlay` (**`G`**, structural, owner-re-affirmed — **not re-openable on a share statistic**); a **ramp-constrained product** (queue item 2, **`measured_ramp_capability` `U`** / `ramp_envelopes` **`I`** — and `ramp_envelopes` is inert because MISO's model *under*-ramps its own fleet, which is evidence a successor must confront); the marginal-unit **identity/offer** families in the evening window. **This session's output is a finding plus the primary-source question queue item 2 already owns.** No arm. |
| **CONGESTION** (`share_cong ≥ 0.50`) | **binding-constraint price separation**, which the model's 6-zone representation cannot express. | The aimed cells are `internal_congestion_split` **`G`** and `zonal_loss_surface` **`R`**. The `G` is a **NO-BUILD, data-blocked-at-representation** verdict that miso-79 established is **FUNDAMENTAL, not provisional**: 88–99.7 % of every internal congestion class's Σ\|SP\| is **intra-LBA**, and an optimal simultaneous split of all six zones (~12 zones) captures only **1.9–3.8 %** of the mass. Re-opening needs RO-1 (published PTDFs / boundary-aligned limits) or RO-2 (an owner-chartered physics-network program). **In that case this session's finding is that C3a-2025 is not reachable by MISO's admissible mechanism set at the model's present representation** — a governance-grade statement that goes to the owner as a question, and **explicitly not** a licence to build a zonal split. |
| **MIXED** | neither component carries the majority | Both rows above are reported, the leading component is named **without** the word dominant, and the queue is re-aimed to the leading one with the qualification stated in the headline. |

Under **every** branch the ambient/heat/peak-load capability-removal family stays
closed (miso-139 reach, miso-203 location) and the unit-outage family stays a
defect-repair lane, never a C3a lever.

---

## 6. Stop rule, and the rule duties

**STOP RULE.** This is a **zero-solve measurement session by design**. A solve is
spent **only** if G-1 returns a verdict whose §5 row names an `O`/`U` family
**and** a concrete lever within it clears charter (d) — its bound at the object's
own percentile in its own driver — **and** that bound is itself computed from
committed artifacts. Any other outcome ends at the FINDING. The zero-solve
precedent (miso-131…139 / miso-179 / miso-194 / miso-203) is the expected
outcome and is a legitimate one: three of the last six MISO sessions spent no LP.

**Rule duties, declared now.**
`[R-DASHBOARD]` (15) — a zero-solve session registers nothing; keeper unchanged.
`[R-HOLDOUT]` (22) — 2023/2024/2025 **only**; MISO holds no `complete`/`final`
marker and the locked-test freeze is active. No out-of-training year is read,
solved, scored or registered.
`[R-MEASURED]` (13) — the inputs are MISO's **own published settlement price
components** and the keeper's committed sidecars. They are read as a
**diagnostic decomposition of the residual**, never fed into a solve; nothing
here becomes a model input, so the rule-13 answer-class line is not approached.
`[R-MECH-MATRIX]` (28) — no mechanism is tested, so no cell verdict moves; the
cells this session **re-aims toward** get their evidence citation amended in
MISO's shard, in-session, per duty (b), and no other ISO's shard is touched
(rule 25).
`[R-ISO-SCOPE]` (25) — MISO artifacts only. The pre-existing NYISO §5.x prose
drift on `main` is not this lane's to repair.
