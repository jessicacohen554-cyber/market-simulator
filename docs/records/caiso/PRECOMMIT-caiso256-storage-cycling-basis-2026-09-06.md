# PRECOMMIT — caiso-256: caiso-255b's ranked-first object, "THE MODEL OVER-CYCLES STORAGE" (35.4 vs 28.5 GWh/d discharged, 42.1 vs 33.3 charged, 2025). **Before a cycling cost is identified from anything, the object's BASIS has to survive: the keeper's `storage_<year>.parquet` carries TWO techs, and EIA-930 `NG: OTH` excludes one of them.** A ZERO-LP charter whose first gate can dissolve the object — and a disclosure that the first gate's value was seen before this document was pushed.

**Session caiso-256, 2026-09-06.** Branch
`claude/caiso-storage-over-cycling-ymodu3` off `main` `ba894c9c`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`, `git_sha`
`fa23c1f7`) UNCHANGED, DETERMINATION **CALIBRATED**. Rule 22 `[R-HOLDOUT]`:
2023–2025 only; CAISO holds no `complete`/`final` marker; the holdout spend
freeze is ACTIVE. **No arm is coded in any branch of this charter; no LP is
spent; no `ScenarioConfig` field is added.**

---

## §0 — THE OBJECT, AS HANDED OVER

`FINDING-caiso255b §2/§7` queue item 2 (the handoff's ranked object 1):

> the model OVER-CYCLES storage — 35.4 GWh/d discharged against 28.5 actual,
> 42.1 charged against 33.3 (2025), with correct phase (both series peak at
> hod 19) and a fleet already larger than actual ever reaches (model max
> discharge / actual max = 1.35 / 1.21 / 1.14). So this is not fleet, not
> timing — it is how much the model cycles.

The handoff's candidate mechanisms — the arbitrage spread, `battery_dispatch_adder`
(keeper value **5.0 $/MWh**, DOF ledger row `battery_dispatch_adder`,
identification `residual`), `storage_degradation` / a cycling cost,
`storage_daily_cycling`, an SOC/duration bound — are every one of them
**already adjudicated on CAISO's battery limb**:

| candidate | status | where |
|---|---|---|
| `battery_dispatch_adder` at the ATB-derived $14.25 | **REJECTED PROBE** on the pre-registered two-sided ±15 % battery-only throughput guard (volume collapsed below measured); "battery charge volume is inelastic to marginal cost" | caiso-100/101 |
| the ATB route at today's capex ($22.63) | **REFUSED a fortiori**, and **REFUTED by CAISO's own published bid stack**, which bounds the fleet's throughput cost from above at $15/MWh; the published grain BOUNDS WITHOUT IDENTIFYING, so the DOF does not close — a **disclosure wall** (the Storage DEB cycling component is per-resource and never published) | caiso-176 Arc 2 |
| a scalar storage price as a spread instrument | cancels exactly from the pinned-day identity | caiso-169 §5 R1, §9 #4 |
| `storage_daily_cycling` | **G** — refused ex ante on reach and on premise (the measured fleet banks across days at sd 2,482 / 3,685 / 4,029 MWh/d; exact day-neutrality is 2.0–2.2× further from the truth in the other direction) | caiso-169 §3/§4, §9 #1 |
| an intermediate SOC horizon / a belly-phase SOC anchor | fitted DOF / outcome pin | caiso-169 §9 #2–#3 |
| any new charge-side cap, floor, adder or hurdle on the battery limb | **barred** — the class that can reach is the armed `caiso_storage_shape_anchor`, and re-picking its percentile against a residual is an outcome pin and a stack | caiso-168 §8 #3, caiso-250 §7 #2 |
| a pumped-storage envelope by proxy | **barred** — the PS split is WALLED (no public hourly PS telemetry; Helms and Eastwood have none at all) | caiso-141/145, caiso-168 §8 #4 |

So even a confirmed over-cycling residual would be **filed, not armed**, on
this record. What is genuinely open is narrower and cheaper: **is the object
real on its own basis?** That is this charter.

## §1 — THE FIRST GATE, AND THE DISCLOSURE THAT GOES WITH IT

**G-BASIS.** `hourly/storage_<year>.parquet` has columns
`[year, pass, tech, hour, charge_mw, discharge_mw]` and, in this keeper,
**two techs: `li_ion` and `pumped_storage`** (Helms and the cited-pump-rating
PS plants, `caiso_ps_plant_params`). caiso-255b's `model_storage()` sums over
techs. EIA-930 `NG: OTH` **excludes pumped storage by construction** —
`FINDING-caiso168 §3`, and its DO-NOT-REDO #1 already names this exact error:

> Do not re-quote caiso-121's "+1967/+2049/+2244 MW storage over measured" as
> a battery statement. It is model **all-tech** net against a **PS-excluding**
> series.

The gate: reproduce caiso-255b's 35.4 / 42.1 GWh/d as `li_ion + pumped_storage`
to ±0.1 GWh/d, then restate the comparison **battery-only** (`li_ion` against
`NG: OTH`), on the loader clock (`_eia_hourly_frame_filled`, caiso-255b §6
DO-NOT-REDO #1), with the actual split into its hour-separated positive
(discharge) and negative (charge) parts — the caiso-169 §4 "basis symmetry"
construction, which caiso-169 measured as < 0.02 % from the model's gross basis.

**DISCLOSURE, AGAINST INTEREST, BEFORE ANYTHING ELSE.** The process rule is
PRECOMMIT before any measurement. While reading the sidecar's *schema* to write
this document, the `tech` column made the two-tech composition visible and I
ran the per-tech annual sums **before** this document existed. I cannot un-see
them, so they are recorded here rather than presented later as a prediction
that "held":

| year | model `li_ion` dis / chg (GWh/d) | model `pumped_storage` dis / chg | `NG: OTH` dis (+) / chg (−), hour-separated, loader clock |
|---|---|---|---|
| 2023 | 10.32 / 12.14 | 6.16 / 7.70 | 11.03 / 11.15 |
| 2024 | 19.29 / 22.69 | 6.16 / 7.70 | 20.79 / 23.91 |
| 2025 | 28.79 / 33.87 | 6.58 / 8.23 | 30.84 / 35.67 |

`li_ion + pumped_storage` in 2025 = **35.37 / 42.10** — caiso-255b's 35.4 / 42.1
to the digit. On the battery-only basis the sign of the headline **reverses**:
the model discharges **0.936 / 0.928 / 0.934** of the measured battery fleet.
A one-line hod diff (li_ion net minus `NG: OTH`) was printed in the same run
and is likewise disclosed as seen; it is not restated here so that §3's
diurnal legs are still measured by the probe rather than transcribed.

**Everything below G-BASIS is pre-registered and has NOT been computed.**

## §2 — THE RE-STATED QUESTION

If the model's battery fleet moves ~7 % *less* energy than the measured one,
the over-cycling object is refuted and the residual question becomes: is the
7 % a **conduct** shortfall (the model cycles a right-sized fleet too little)
or a **capacity** shortfall (a right-cycled fleet that is too small at the
hours that matter)? The two are separable at zero LP because the armed
`caiso_storage_shape_anchor` is a **per-hod power cap** — `env_p95[year, hod]
× power_cap` from `data/raw/reference/caiso-storage-shape-envelope.csv`
(`model/storage.py::caiso_storage_shape_caps`, caiso-99 Mechanism B, a
rule-23 frozen derive) — so the model's fleet-wide ceiling in any hour is a
p95 of the measured ratio, never its maximum.

## §3 — GATES AND PREDICTIONS, WRITTEN TO BIND

Instrument: `scripts/probes/_caiso256_storage_cycling_basis.py`, committed
artifacts only, loader clock, non-leap 8760 (caiso-168 §8 #6 / caiso-169 §9 #7:
the loader frame is 8760 rows in every year — verified by row count in the
probe). Artifact `results/calibration/_caiso256_storage_cycling_basis.json`.

| # | gate / prediction | registered threshold |
|---|---|---|
| **G-BASIS** | `li_ion + pumped_storage` reproduces 35.4 / 42.1 (2025) to ±0.1 GWh/d; battery-only ratio model/actual discharge lies in **[0.90, 1.00]** in all three years | fail ⇒ the object stands as handed over and this charter is wrong |
| **G-INTENSITY** | cycling intensity = daily discharge ÷ the fleet's **p99 hourly net discharge** (a robust proxy for the coincident fleet MW, chosen over the single max so one spike hour cannot set it), model vs actual | **P-1:** within **±5 %** in every year ⇒ the shortfall is NOT conduct |
| **G-FLEET-BATT** | model p99 / actual p99 net discharge, battery-only | **P-2:** in **[0.88, 0.98]** every year, i.e. the model's *effective* fleet is smaller — the mirror of caiso-255b's PS-contaminated 1.35 / 1.21 / 1.14 |
| **G-CAP** | share of hod-19 hours (the measured and modelled discharge peak) in which the model's `li_ion` discharge sits within 1 % of its shape-anchor cap, cap rebuilt from the envelope csv and the keeper's built `power_cap` per zone | **P-3:** ≥ 50 % in every year — the p95 envelope, not the LP's arbitrage appetite, sets the peak |
| **D-PROFILE** | hod-mean diff, `li_ion` net minus `NG: OTH`, per year — reported | **P-4:** the belly (hod 10–15) diff is **inside ±400 MW** every year (caiso-255b's −1,090 at hod 10 was PS-carried); the 22–23 diff stays **positive** (the model long, caiso-255b §6 #2 stands) |
| **D-SPREAD** | the model's realised arbitrage spread: discharge-weighted minus charge-weighted load-weighted ISO mean `price` (`system_<year>.parquet`, li_ion weights), against its own hurdle `adder/η_d + ε·(1+1/η)` at 5.0 $/MWh and RTE 0.85 — reported | **P-5:** realised spread ≥ hurdle in all years (an LP optimality condition on average, so this is an instrument check, not a finding) |
| **D-PS** | Helms/PS model cycling per year, reported beside the wall; **no comparator is constructed** (caiso-168 §8 #4) | — |

**No gate here is a target residual and none can promote anything.** The
charter has no arm to promote.

## §4 — STOP RULE

1. **G-BASIS fails ⇒ stop and report the object as standing.** No mechanism is
   proposed in that branch either — §0's table closes the lever space, and a
   confirmed residual would be filed as an open item for the owner.
2. **G-BASIS passes ⇒ the over-cycling object is REFUTED on basis** and the
   residual is re-named by G-INTENSITY / G-FLEET-BATT / G-CAP. If P-1 and P-3
   hold, the 7 % is the armed anchor's own percentile, which caiso-168 §8 #3
   and caiso-250 §7 #2 bar from being re-picked — **reported, never armed**.
3. **No gate is relaxed or re-run to a pass after its result.** P-1 keeps ±5 %.
4. Nothing is solved, nothing registered (rule 15 is not engaged — no run is
   produced), no `ScenarioConfig` field, no matrix verdict move (rule 28(b)
   attaches as an evidence append only, since no mechanism is tested).
5. The `complete` marker, the stale `program-status.json` CAISO keeper stamp,
   the C3a weight basis, the per-zone storage sidecar ask, the DMM 2025 RA-import
   basis and Panoche are carried unchanged and raised, not granted.

## §5 — RULE 13 `[R-MEASURED]`, STATED BEFORE THE RESULT

A cycling cost identified from CAISO's own measured conduct would be
admissible; one tuned to the volume residual is not. This session identifies
**neither**: caiso-176 established that the only public conduct source binds
the value inside a $15-wide bucket, and no new source has landed. The handoff's
"what spread would reproduce 28.5 GWh/d" is therefore not asked — on the
battery-only basis it is the wrong direction anyway, and answering it would be
reading a parameter off a residual.

## §6 — G-DRIFT

Not engaged for this object: no solve. (The drift chain past `d8b64997` IS
engaged for the session's second object and is recorded in its own addendum,
because `main` now carries `df277e89`, the CT-only artifact re-freeze — a LIVE
input hunk by design.)

## §7 — DELIVERABLES

This PRECOMMIT (pushed first); the probe; the artifact json; the FINDING;
the `docs/calibration-log/caiso.md` entry; an evidence append on the matrix
shard's `battery_dispatch_adder` / `storage_measured_anchors` cells with no
verdict move. Keeper unchanged.
