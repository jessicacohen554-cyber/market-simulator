# FINDING — caiso-256: **"THE MODEL OVER-CYCLES STORAGE" IS REFUTED ON BASIS.** caiso-255b's 35.4 / 42.1 GWh/d is `li_ion + pumped_storage` against a series that excludes pumped storage — the caiso-121 basis error caiso-168 §8 #1 already names. Battery-only the model **UNDER**-cycles by 6.4–7.2 % in every year, in a fleet that is NOT short (p99 1.00–1.12×) and under a shape-anchor cap that has ~30 % headroom at the evening peak. **The residual is the caiso-127 evening/overnight object, already chartered and unfunded.** ZERO LP, nothing armed, keeper UNCHANGED.

**Session caiso-256, 2026-09-06.** Branch
`claude/caiso-storage-over-cycling-ymodu3`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** UNCHANGED, DETERMINATION **CALIBRATED**.
Pre-registration: `PRECOMMIT-caiso256-storage-cycling-basis-2026-09-06.md`
(`885c405e`), pushed before the probe ran, carrying the one disclosure that
matters (§5 #1 below). Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no
`complete`/`final` marker; freeze ACTIVE. Probe:
`scripts/probes/_caiso256_storage_cycling_basis.py`; artifact
`results/calibration/_caiso256_storage_cycling_basis.json`.

---

## §1 — THE GATES, SCORED

| # | registered | measured | verdict |
|---|---|---|---|
| **G-BASIS** (decisive) | `li_ion + pumped_storage` reproduces 35.4 / 42.1 (2025) to ±0.1; battery-only model/actual discharge in [0.90, 1.00] all years | **35.37 / 42.10**; ratios **0.936 / 0.928 / 0.933** | **PASS — the object is refuted** |
| **G-INTENSITY / P-1** | daily discharge ÷ p99 net discharge, model vs actual within ±5 % | h/day at the coincident rate: actual **3.51 / 3.52 / 3.79**, model **2.93 / 3.25 / 3.54** → ratio **0.834 / 0.922 / 0.932** | **FALSIFIED** — the shortfall IS conduct |
| **G-FLEET-BATT / P-2** | model p99 / actual p99 in [0.88, 0.98] | **1.122 / 1.006 / 1.001** | **FALSIFIED** — the fleet is NOT short |
| **G-CAP / P-3** | ≥ 50 % of hod-19 hours with `li_ion` discharge within 1 % of its shape-anchor cap | **46.0 / 28.5 / 14.5 %**; hod-19 mean discharge **2,135 / 4,298 / 5,623 MW** against a cap of **2,950 / 6,121 / 8,551 MW** (72 / 70 / 66 % used) | **FALSIFIED** — the p95 envelope does NOT set the peak |
| **D-PROFILE / P-4** | belly \|diff\| ≤ 400 MW every year; 22–23 diff > 0 | belly max **582 / 411 / 247 MW**; hod 22/23 **+235/+199, +161/+191, +276/+414** | **FALSIFIED in 2023–24 on the belly; 22–23 sign holds** |
| **D-SPREAD / P-5** | realised margin after RTE ≥ the LP's own hurdle | margin **29.95 / 24.53 / 22.69 $/MWh** vs hurdle **5.002** | HOLDS (instrument check) |

Four of five predictions are falsified. **Every falsification simplifies the
object rather than complicating it**, and the sequence is the finding.

## §2 — WHAT THE BATTERY FLEET ACTUALLY DOES, ON THE RIGHT BASIS

Loader clock (`_eia_hourly_frame_filled`), `NG: OTH` split into its
hour-separated positive and negative parts, model `li_ion` P1 (the model's
two legs coincide above 1 MW in only 2 / 2 / 10 hours, so gross = net-basis):

| year | actual dis / chg (GWh/d) | model `li_ion` dis / chg | ratio dis / chg | model `pumped_storage` dis / chg | implied RTE actual / model |
|---|---|---|---|---|---|
| 2023 | 11.03 / 11.15 | 10.32 / 12.14 | 0.936 / **1.089** | 6.16 / 7.70 | 0.989 / 0.850 |
| 2024 | 20.79 / 23.91 | 19.29 / 22.69 | 0.928 / 0.949 | 6.16 / 7.70 | 0.869 / 0.850 |
| 2025 | 30.84 / 35.67 | 28.79 / 33.87 | 0.933 / 0.950 | 6.58 / 8.23 | 0.865 / 0.850 |

Three things follow, each measured rather than inferred:

1. **The model discharges ~7 % LESS battery energy than the measured fleet, in
   every year, at a ratio stable across a 2.8× build-out.** The direction of
   the handed-over object is reversed, not merely its magnitude.
2. **It is not a fleet-size shortfall.** At the p99 of hourly net discharge —
   the robust proxy for coincident fleet MW — the model matches the measured
   fleet in 2024–25 (5,942 vs 5,905 MW; 8,139 vs 8,130 MW) and exceeds it by
   12 % in 2023. caiso-255b's "1.35 / 1.21 / 1.14×" was the PS-summed single
   maximum; the battery-only maximum ratio is 0.94 / 0.93 / 0.93 and the p99
   ratio is 1.12 / 1.01 / 1.00 — one spike hour was carrying the claim.
3. **It is not the armed shape-anchor cap.** Rebuilt from the shipped builder
   (`caiso_storage_shape_caps` on the keeper's own `fleet_only` rebuild), the
   fleet-wide hod-19 discharge cap has **28 / 30 / 34 % headroom** over the
   model's mean discharge in that hour, and the cap binds in only
   **46 / 28 / 15 %** of hod-19 hours. The LP could discharge more at the
   evening peak and chooses not to.

**So the 7 % is CONDUCT, and it has a shape.** The hod diff (model `li_ion`
net minus `NG: OTH`, MW) is the object:

| year | 01–05 (overnight) | 10–15 (belly) | 17–21 (evening) | 22–23 |
|---|---|---|---|---|
| 2023 | +308 / +345 / +215 / −5 / −156 | −371 … **−581** | −389 / −369 / +110 / +172 / +185 | +235 / +199 |
| 2024 | +175 / +343 / +409 / +298 / +5 | −411 … −74 | +101 / −241 / +9 / −21 / −77 | +161 / +191 |
| 2025 | +138 / +367 / +490 / +346 / +97 | −246 … −112 | +108 / **−499 / −551** / −267 / −240 | +276 / +414 |

The model is **short in the early evening (17–19 in 2025: −0.5 GW mean) and
long from 22 through 05**, i.e. it moves ~1.5 GWh/d of discharge out of the
block where the measured fleet delivers it and spreads it across the late
evening and the overnight. **That is `FINDING-caiso127 §2`'s evening/overnight
spread compression — the storage pin — measured a fourth time** (caiso-127 on
the caiso-126 keeper; caiso-169 §3 on caiso-166; here on caiso-252), and its
overnight sign has not changed across the whole keeper chain. In 2023 the
belly carries a second known object: the model charges **9 % more** than the
measured fleet, concentrated at hod 11–14 (−513 … −581 MW), which is
`FINDING-caiso168`'s belly-surplus cell (+736 MW like-for-like battery net,
2023).

## §3 — WHY NONE OF THE HANDED-OVER MECHANISMS CAN BE THE LEVER, ON THIS BASIS

The handoff named the arbitrage spread, `battery_dispatch_adder`, a
degradation / cycling cost, `storage_daily_cycling` and an SOC/duration bound
— every one a mechanism that **reduces** cycling. On the correct basis the
model already cycles **less** than the measured fleet, so each would move the
volume the wrong way; the PRECOMMIT §0 table records that each was also
already adjudicated on this limb before this session (caiso-100/101 rejected
the $14.25 adder on the two-sided throughput guard when the fleet *lost*
volume; caiso-176 walled the identification inside a $15-wide public bucket;
caiso-169 refused `storage_daily_cycling` on reach and premise and showed a
scalar `c_dis` cancels from the pinned-day identity; caiso-168 §8 #3 bars any
new charge-side cap, floor, adder or hurdle on the battery limb).

The handoff's second question — "what spread would reproduce 28.5 GWh/d" — is
not answered, for two reasons that are both disclosures: the number is on the
wrong basis (the correct battery-only actual is 30.84, above the model), and
reading a cycling cost off that residual is the rule-13 pin the PRECOMMIT §5
refused in advance. What the committed duals do say (D-SPREAD) is that the
model's realised margin after round-trip losses is **$23–30/MWh** against a
$5 hurdle — the fleet is nowhere near its hurdle on average, which is
consistent with §2(3): the evening shortfall is not a price the LP declines to
take, it is the single-market perfect-foresight allocation of a fixed SOC
across the evening and the overnight (caiso-169 §5 R2). **The lever is the
one caiso-129 §5 and caiso-169 §5 already specify — S2, the DA/RT
two-settlement separation with a measured DA-vs-actual forecast-error
input — and it is unfunded under the caiso-201 resting ruling.** Nothing here
changes that ruling's premise; it removes a candidate that would have been
built on a basis error.

## §4 — THE PUMPED-STORAGE SIDE, REPORTED BESIDE THE WALL

Model PS (Helms + the cited-pump-rating plants under `caiso_ps_plant_params`)
cycles **6.16 / 6.16 / 6.58 GWh/d** discharged, 7.70 / 7.70 / 8.23 charged —
2.25 / 2.25 / 2.40 TWh/yr, 14–17 % of the model's all-tech throughput and the
entire 35.4-vs-28.5 headline. **No comparator is constructed**: caiso-141
established that no public source separates CAISO pumped storage from
conventional hydro at hourly grain, the owner accepted the wall at caiso-145,
and caiso-168 §8 #4 forbids approximating the PS envelope from `WAT`, a
hydro-minus-PS split, a scaled battery envelope or a fitted adder. Whether the
model's Helms cycling is right is therefore **unmeasurable on the record as
it stands**, and this session says so rather than reading it off a residual.

## §5 — DISCLOSURES AGAINST INTEREST

1. **The decisive gate's value was seen before the PRECOMMIT was pushed.** The
   sidecar's `tech` column made the two-tech composition visible while I was
   reading its schema, and I ran the per-tech annual sums before the document
   existed. The PRECOMMIT records those numbers as *seen* and pre-registers
   every other gate; §1's G-INTENSITY, G-FLEET-BATT, G-CAP, D-PROFILE and
   D-SPREAD values were all computed after the push. The one number in §2's
   table that was known in advance is the discharge ratio.
2. **Four of my five predictions were wrong, and P-2 was wrong in the
   direction that would have supported a fleet-size story.** I registered the
   p99 ratio in [0.88, 0.98] because the single-max ratio I had seen was 0.93;
   the p99 says the fleet is not short at all. The single max was one spike
   hour, and I had nearly built the residual's explanation on it.
3. **P-3 (the cap sets the peak) was the tidy story and it is false.** Had it
   held, the 7 % would have been "the armed anchor's own percentile" and
   closed as barred. It is not; the shortfall is the LP's allocation, which is
   a harder and already-chartered object.
4. **caiso-255b's actual-side numbers (28.5 / 33.3) are not reproduced here
   and are not on the basis this probe uses.** They appear to be a
   profile-averaged read; the hour-separated positive/negative split gives
   30.84 / 35.67. Both bases put the battery-only model *below* the actual.
5. **caiso-255b §6 #2 stands, and this finding strengthens it**: at hod 22–23
   the model is long storage battery-only too (+235/+199, +161/+191,
   +276/+414 MW), so the 22–23 CC over-run remains open with no named carrier
   and storage is still on the wrong side of it.
6. The 2023 actual implied RTE of 0.989 is reported as read; `NG: OTH` is a
   catch-all and in 2023 its positive side evidently carries something other
   than battery discharge. It does not affect the discharge comparison's
   direction.
7. **No solve was spent, no arm was coded, no `ScenarioConfig` field was
   added, the keeper did not move, no marker was declared.** Rule 15 is not
   engaged: no run was produced.

## §6 — DO-NOT-REDO ADDS

1. **Never compare the keeper's `storage_<year>.parquet` summed over techs to
   `NG: OTH`.** Filter `tech == "li_ion"`. This is the caiso-121 error
   (caiso-168 §8 #1) recurring on a different statistic, and it has now
   produced a false queue item once.
2. **Never re-open "the model over-cycles storage".** Battery-only it
   under-cycles by 6.4–7.2 % in every year; the all-tech excess is Helms.
3. **Never propose a cycling cost, throughput adder, degradation charge, SOC
   horizon or duration bound as the lever for the battery-only residual.**
   Each reduces cycling; the model already cycles less than the measured
   fleet. (Additional to caiso-100/101, caiso-168 §8 #3, caiso-169 §9 #1–#4,
   caiso-176.)
4. **Never quote caiso-255b's 1.35 / 1.21 / 1.14× as a battery fleet-size
   statement, and never use the single annual maximum as the fleet proxy.**
   Battery-only p99 ratio 1.12 / 1.01 / 1.00.
5. **Never read the evening battery shortfall as cap-bound.** The anchor cap
   has 28–34 % headroom at hod 19 and binds in 15–46 % of those hours.
6. caiso-255b §6, caiso-254 §6, caiso-253 §7, caiso-252 §7 and §12, caiso-251
   §8, caiso-250 §7, caiso-249 §7, caiso-248 §8, caiso-247 §8, caiso-246 §8,
   caiso-245 §7, caiso-244 §7, caiso-243 §10, caiso-242 §9, caiso-241 §10,
   caiso-240 §7, caiso-239 §8, caiso-230 §9, caiso-229 §10, caiso-169 §9,
   caiso-168 §8 stand in full.

## §7 — QUEUE

1. caiso-255b queue item 2 is **STRUCK** (refuted on basis). What replaces it
   is not new: the battery-only 7 % under-discharge is the **caiso-127
   evening/overnight object (S2)**, unfunded under caiso-201, and the 2023
   belly excess is the **caiso-168** cell with a closed lever space.
2. **The hod 22–23 CC over-run** stays open with no named carrier (import
   refused, storage on the wrong side — now on both bases).
3. **The granted partition object** is taken up by this same session as its
   second object: the repaired CT-only artifact is already on `main`
   (`df277e89`, PR #5133) — see `ADDENDUM-caiso256-partition-screen`.
4. Carried unchanged, raised not granted: the `complete` marker; the stale
   `program-status.json` CAISO keeper stamp; the C3a weight basis; the
   per-zone storage/class sidecar; the DMM 2025 RA-import basis; Panoche.

**No run registered (none produced), no keeper change, no `ScenarioConfig`
field, no matrix verdict move (evidence append only), no `complete`
declaration.**
