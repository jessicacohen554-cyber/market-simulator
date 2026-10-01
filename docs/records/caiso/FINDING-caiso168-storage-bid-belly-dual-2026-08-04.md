# FINDING — caiso-168: caiso-167's pointer is **CONFIRMED and quantified** — a storage charge column is the marginal buyer in the CA belly, and those hours carry **81.1 / 67.4 / 82.3 %** of the surplus-regime over-price. But the object **splits into two limbs**, the battery limb's instrument channel is **already armed** (`caiso_storage_shape_anchor`, rule 19), the 2023 majority owner is the **WALLED** pumped-storage limb — and caiso-121's motivating storage row is a **BASIS MISMATCH**: 67 / 65 / 56 % of it is model PS pumping differenced against a series with no PS in it. Lever-queue item 3's **S2 charter is NOT the successor for the belly residual** and is left standing on its own object. NO LP, NO SOLVE, NO DERIVE, keeper unchanged (2026-08-04)

**Session** caiso-168 · **Date** 2026-08-04 · **Branch**
`claude/caiso-168-storage-bid-f38jgi` · **Base** `afe19a56`

**Incumbent CAISO keeper** `2026-08-04-caiso164-zonal-loss-surface`
(CALIBRATED-WITH-CAVEATS, 2 owner-ledgered caveats, 0 FAILs). **Unchanged by
this session.** No mechanism was armed, no `ScenarioConfig` field was added, no
derive script was run, nothing was registered.

**Target** `docs/mechanism-testing-matrix.md` §5.2 lever-queue **item 3** — S2,
the DA/RT two-settlement separation charter — reached via caiso-167 §7's
explicit **pointer, not verdict**: with the corridor/export-path family closed
on both halves, the surplus-regime belly residual is in-state by elimination,
and "whether the belly dual is being held up by the storage charging bid is
**untested**".

**No prereg was committed** because nothing was derived, armed or solved. This
is a measurement-only Phase 0 on committed artifacts, the caiso-167 pattern.

**Method** one command, committed artifacts only, no LP anywhere in it:

```
python scripts/probes/caiso168_storage_bid_phase0.py
```

Artifact: `results/calibration/_caiso168_storage_bid_phase0.json`.

---

## §0 — the one-paragraph result

**The pointer is right, and it is now measured.** By LP optimality a storage
charge column that is *strictly interior* has zero reduced cost, so
`λ = −ε − η_c·ν`: the battery **is** the marginal buyer and its bid **is** the
zone's dual. On the keeper's own hourly sidecars, a storage charge column is
interior in **36.6 / 50.5 / 55.5 %** of surplus-regime belly hours, and those
hours carry **81.1 / 67.4 / 82.3 %** of the whole belly-surplus over-price.
Matched within month × measured-hub decile, an interior charge column carries
**+9.66 / +13.97 / +11.33 $/MWh** more model over-price than a pinned one
(positive in 95.5 / 96.3 / 93.2 % of matched cells). **But the object is not
S2's.** It splits into a battery limb (42.2 / 57.3 / 69.7 % of the defect) and
a **pumped-storage** limb (49.1 / 21.5 / 21.8 %) — the PS limb is the **majority
owner in 2023**, and PS is the owner-ledgered walled C3a object. On the battery
limb the only instrument class that can reach — a charge-side **upper bound** —
is already occupied by the armed `caiso_storage_shape_anchor`, which the model
rides at **86–94 %** of its p95 cap where the measured fleet averages 59–73 %;
tightening that percentile against this residual is barred by rules 13 and 23.
And the number that sent the lane here is **wrong on basis**: caiso-121's
storage row is model **all-tech** net differenced against EIA-930 `NG: OTH`,
which **excludes pumped storage by construction** — 67 / 65 / 56 % of it is the
model's own PS pumping. **Item 3's S2 charter is not the successor for the
belly residual**; the belly residual's charge-side channel is armed or walled,
and S2 stays standing, untouched, on its own evening/overnight object.

---

## §1 — the instrument, and an exact validation of it

The census needs each hour's charge *bound*, and the keeper arms
`caiso_storage_shape_anchor`, so a battery row's bound is not nameplate but
`env_p95_chg[year, hod] × power_cap[s, t]`
(`model/storage.py::caiso_storage_shape_caps`). `power_cap` is
**piecewise-constant by month** (`storage.storage_cap_profiles` →
`data.fleet._hour_to_month_index`) and the envelope CSV is committed, so
inverting the keeper's own dispatch against the envelope recovers the monthly
fleet cap:

```
cap[m] = max_{t∈m} max( chg_t / f_chg[hod] , dis_t / f_dis[hod] )
```

That reconstruction is **exact**, and this is checked rather than asserted —
against `load_eia860_storage`'s own monthly battery fleet, all 36 months:

| year | recovered Jan → Dec (MW) |
|---|---|
| 2023 | 4443 4443 4499 4499 4579 5061 5628 5915 6302 6471 6870 7492 |
| 2024 | 7564 7564 7968 8363 8720 9006 9399 10054 10297 10480 10653 11131 |
| 2025 | 11131 11371 11470 11985 12536 13038 13295 13954 14079 14711 14910 15448 |

Every month matches the EIA-860 fleet to rounding, and December of one solve
meets January of the next across independent solves (7492 → 7564, 11131 →
11131). The three states follow from the charge column's reduced cost
`ε + λ_t + η_c·ν_t`: **interior** ⇒ rc = 0, the battery sets λ; **at-cap** ⇒
rc ≤ 0, λ is *below* its willingness to pay, so it is a pinned demand and cannot
set λ; **zero** ⇒ rc ≥ 0, λ is above it.

> **Clock defect found and fixed, and it is inherited.** The model frame is the
> fixed **non-leap 8760** calendar with Feb-29 dropped (repo convention,
> `_caiso102`/`_caiso105`/`_caiso140`). caiso-167's `_hour_index` maps a
> timestamp by *linear offset* from Jan 1, which in **2024** puts every hour
> after Feb-28 a full day out of phase with the solve — and it silently shifted
> this probe's recovered 2024 cap staircase by a whole month until it was
> caught by the EIA-860 check above. Every number in this finding is on the
> corrected clock. **The same shift is present in
> `scripts/probes/caiso167_import_basis_phase0.py`**; caiso-167's 2024 column is
> therefore hour-misaligned against its measured comparators. It is flagged here,
> not silently repaired — that is caiso-167's lane and its DSW verdict was a
> reach bound at 1.6 / 0.1 / 1.4 % of the defect, far outside anything a
> one-day phase shift moves.

## §2 — the census: a storage charge column is the marginal buyer

Surplus-regime belly hours (Pacific `[09,16)`, measured CA day-ahead hub
≤ $20/MWh — both cuts carried verbatim from caiso-120/165/167, neither chosen
here). Battery charge state:

| year | interior | at-cap | zero | λ interior | λ at-cap | defect interior | defect at-cap |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 16.2 % | 82.0 % | 1.8 % | 34.78 | 10.18 | **+24.94** | +6.15 |
| 2024 | 41.8 % | 53.6 % | 4.6 % | 22.01 | **−1.21** | **+22.97** | +10.81 |
| 2025 | 43.6 % | 55.7 % | 0.7 % | 24.84 | 2.02 | **+19.51** | +6.22 |

λ is the CA demand-weighted dual (the C3a construction). Note the 2024 at-cap
cell: **the model prices the belly NEGATIVE when the battery is pinned.** The
LP is perfectly capable of clearing below zero here — `negative_renewable_offers`
is armed on the CAISO keeper (the REC floor) — it simply never gets there while
a storage charge column is the marginal buyer.

**Where the over-price lives** (share of the belly-surplus over-price, stage D):

| year | interior | at-cap | zero |
|---|---:|---:|---:|
| 2023 | **42.2 %** | 52.6 % | 5.2 % |
| 2024 | **57.3 %** | 34.6 % | 8.1 % |
| 2025 | **69.7 %** | 28.4 % | 1.8 % |

Two independent corroborations that this is the LP fact and not a coincidence.

**(a) The matched control.** The raw contrast is confounded — at-cap hours are
by construction hours the battery wanted *more* energy in. Pairing the two
states inside the same month **and** the same decile of the *measured* hub
(exogenous to the model), the interior state still over-prices by
**+9.66 / +13.97 / +11.33 $/MWh**, positive in **95.5 / 96.3 / 93.2 %** of the
22 / 54 / 59 matched cells (109 / 438 / 403 matched hours).

**(b) Flatness.** Where SOC is interior the SOC-row dual is common across the
episode, so every interior-charge hour of that episode carries the *same* λ. The
within-day spread of the model dual is **0.85 / 2.53 / 3.78 $/MWh** across
interior-charge hours against **15.78 / 9.56 / 8.72** across at-cap hours — a
pinned dual tracks net load, a battery-set dual does not. The real market moved
those same hours by 4.56 / 4.37 / 3.65.

**(c) The zone that escapes.** In interior hours every CA zone sits within
$0.65 of the others — except **SDGE**, which prices **$3.59 / $7.67** lower in
2024 / 2025 (18.52 vs 22.12; 17.51 vs 25.19). SDGE is exactly the zone
caiso-121 §3 identified as the one where model solar curtailment binds and "the
price collapses correctly". The contrast is the whole finding in one line: the
one zone that reaches its curtailment margin prices right; the rest are held at
the storage water value.

**What this does NOT establish.** The state and the dual are jointly determined
by the same LP. This is a **decomposition of where the defect lives**, not a
counterfactual of what removing it would do — a counterfactual needs a solve,
and §5 is why no solve was spent.

## §3 — the number that sent the lane here is a BASIS MISMATCH

caiso-121 §3 recorded **"storage net (charging +) +1967 / +2049 / +2244 MW"**
and caiso-167 §7 forwarded it verbatim as the top of the in-state stack. It is
the model's **all-tech** storage net differenced against EIA-930 `NG: OTH` —
and OTH **excludes pumped storage by construction**. The anchor's own derive
script states it outright: *"Pumped storage is excluded from both numerator and
denominator (not an LESR; EIA-930 OTH does not carry Helms pumping)."* So the
model's PS pumping is being differenced against a series that contains no PS.

| year | n | caiso-121 basis | **battery, like-for-like** | model PS net | PS share of the row |
|---|---:|---:|---:|---:|---:|
| 2023 | 1,116 | +2,235 | **+736** | +1,499 | **67.1 %** |
| 2024 | 1,604 | +2,034 | **+717** | +1,317 | **64.7 %** |
| 2025 | 1,623 | +2,242 | **+979** | +1,263 | **56.3 %** |

(The re-computed all-tech column reproduces caiso-121's row to +268/−15/−2 MW;
the 2023 gap is its RT-based surplus cut against this lane's day-ahead one.)

**Two thirds of the motivating number is model pumped-storage pumping, not a
measured battery excess.** And on a like-for-like battery basis the model's
volume is close to right where it is not conditioned on the belly:

| year | window | model | measured | excess | model rate | measured rate | anchor p95 cap |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | annual | 540 | 464 | **+76** | 0.099 | 0.083 | 0.202 |
| 2024 | annual | 1,030 | 996 | **+34** | 0.112 | 0.107 | 0.214 |
| 2025 | annual | 1,535 | 1,488 | **+47** | 0.119 | 0.113 | 0.199 |
| 2023 | belly-surplus | 2,067 | 1,335 | +732 | **0.386** | 0.244 | 0.411 |
| 2024 | belly-surplus | 3,770 | 3,055 | +715 | **0.415** | 0.332 | 0.505 |
| 2025 | belly-surplus | 5,551 | 4,573 | +977 | **0.439** | 0.359 | 0.493 |

The battery's **annual** charge volume is right to +76 / +34 / +47 MW/h. The
defect is entirely a **belly concentration**: the model rides at **93.9 / 82.2 /
89.0 %** of the armed p95 capability cap in belly-surplus hours where the real
fleet averages **59.4 / 65.7 / 72.8 %** of it.

## §4 — the limb split, and the wall

Pumped storage is **exempt** from the anchor (its bound is nameplate) and its
charge column can be interior too — with exactly the same reduced-cost
consequence. Cross-tabbing both limbs on the belly-surplus mask:

| year | battery only | PS only | both | neither |
|---|---:|---:|---:|---:|
| 2023 hours | 12.0 % | 20.4 % | 4.2 % | 63.4 % |
| 2023 **defect** | 32.0 % | **38.9 %** | 10.2 % | 18.9 % |
| 2024 hours | 33.0 % | 8.7 % | 8.8 % | 49.5 % |
| 2024 **defect** | **45.9 %** | 10.1 % | 11.4 % | 32.6 % |
| 2025 hours | 37.3 % | 12.0 % | 6.2 % | 44.5 % |
| 2025 **defect** | **60.5 %** | 12.6 % | 9.2 % | 17.7 % |

Read three ways:

* **Any storage column marginal** owns **81.1 / 67.4 / 82.3 %** of the defect.
* **Neither** marginal — 63.4 / 49.5 / 44.5 % of the hours — carries a mean
  defect of only **+2.86 / +11.05 / +4.84**. When no storage column sets the
  price, the model's belly level is close to right in 2023 and 2025.
* The **battery limb** owns 42.2 / 57.3 / 69.7 % and the **PS limb** 49.1 /
  21.5 / 21.8 %. **In 2023 the PS limb is the larger owner.**

**The PS limb is the walled object, and this is the stop-and-report.** The model
carries the entire CAISO pumped-storage fleet as **one continuous 2,077.6 MW /
20,776 MWh column in NP15** with **no shape restraint of any kind** (caiso-129
§7) and `pumped_storage_dispatch_adder = None`. A capability envelope for it —
the PS analogue of the battery's anchor — is **not derivable from public data**:
EIA-930 `WAT` mixes pumped storage with conventional hydro (caiso-141: Helms +
Eastwood = 60.3 % of the fleet uninstrumented) and `NG: OTH` excludes PS
entirely. That is the **owner-ledgered C3a-2025 wall** (accepted caiso-145;
re-opened only by the non-public hourly PS intake). Per the standing
instruction, this is **reported, not approximated** — no proxy envelope, no
fitted adder, no derived-from-hydro split.

## §5 — rule 19 `[R-ONE-MECH]`: the battery limb's channel is already occupied

caiso-129 §5 established what the surviving instrument class must be: an
instrument that can **remove** volume — an upper bound or a price — because *"a
floor can only ADD"*. The charge-side census of that class:

| instrument | status |
|---|---|
| `caiso_storage_shape_anchor` — measured p95 hod charge/discharge cap | **ARMED on the keeper** (caiso-99). *This is the charge-side upper bound.* |
| `caiso_charge_allocation_schedule` — measured DAM intra-day charge shape | **BUILT and REJECTED** at caiso-104: conduct-faithful but **belly-λ INERT**. It is a floor (caiso-129 §3(c)). |
| S1 — DA/RT discharge allocation floor | **KILLED** at caiso-129 on its own derive gates; DO-NOT-REDO. |
| `battery_dispatch_adder` | **ARMED at 5.0 $/MWh** — discharge side; a charge-side twin is the same object. |
| `caiso_storage_as_reservation` — measured AS power reservation + SOC sustain | **INERT** (caiso-74); family refuted by arithmetic at caiso-127/129. |
| `caiso_solar_deliverability` — the complementary curtailment margin | **ARMED default-on for CAISO**; its residual is the ~70 %-local curtailment the reduced topology cannot see (the intra-SP15 data blocker). |

So the one instrument class that can reach the battery limb **is the armed
anchor**, and the measured gap is in its *percentile*, not its absence: the
model sits at 82–94 % of a p95 **capability** statistic where the fleet averages
59–73 % of it. Moving that percentile — or adding a second, tighter cap on top —
is barred three ways and none of them is negotiable:

1. **Rule 23 `[R-FROZEN-DERIVE]`** — the envelope re-derives only on an
   EIA-930/EIA-860 source update, *never because a residual moved*. This lane is
   a residual.
2. **Rule 13 `[R-MEASURED]`** — a percentile chosen so the belly λ lands on the
   actuals is an **outcome pin**. p95 was fixed a priori as the repo-standard
   capability statistic (the corridor measured-p95 ATC/GTC convention); re-picking
   it here would make it a fitted DOF (rule 24).
3. **Rule 19 `[R-ONE-MECH]`** — a new charge-side cap would **stack** on the
   anchor rather than replace or reconcile it.

And the residual **after** the anchor binds is measured, so the ceiling is known
either way: in at-cap hours the belly defect is still **+6.15 / +10.81 / +6.22**.
Pinning the battery harder does not reach that; it is not the battery's.

## §6 — what this means for item 3 (S2), stated precisely

**S2 as filed is not the successor for the belly residual, and this session does
not spend it.** S2 is the DA/RT two-settlement separation charter for the
**evening/overnight storage spread** — caiso-127's compression, caiso-129's only
surviving candidate. caiso-167 §7 re-pointed the **belly** residual at it. That
re-point does not land:

* the belly residual's mechanism is a **charge-side** column being marginal
  (§2), not the evening/overnight discharge spread S2 was written against;
* on the **battery** half of it, the instrument class S2 would need is the armed
  anchor's own channel (§5);
* on the **PS** half — the *majority* owner in 2023, and rule 16
  `[R-ALLYEARS]` means 2023 must be covered — the input is walled (§4);
* and the volume premise that motivated the re-point is 56–67 % PS-on-a-PS-free
  basis (§3).

**S2 therefore stays STANDING and UNTOUCHED on its own object.** Nothing here
adjudicates the evening/overnight spread; this session measured the belly only,
and item 3 keeps its original scope. What is closed is the **belly** route into
it.

## §7 — stated limits, not buried

* **The storage sidecar carries no zone.** `storage_<y>.parquet` is by tech, so
  the limb census is fleet-level; the per-zone λ in §2(c) is the keeper's own
  zonal dual, not a per-zone storage state. The PS column is single-zone (NP15)
  by construction, so its attribution is unambiguous; the battery fleet is
  per-zone and its state is aggregated.
* **The state/dual endogeneity is real** and is stated in §2 rather than
  papered over. The matched control bounds it; it does not eliminate it.
* **Stage C (the round-trip identity) is reported and is NOT load-bearing.**
  Predicting the interior belly dual from the same day's interior evening
  discharge dual via `λ_chg = RTE·(λ_dis − adder)` gives MAE 3.23 / 11.84 /
  12.38 (r 0.94 / 0.70 / 0.62). It holds in 2023 and degrades in 2024–25 —
  expected, because the SOC **energy** bound binds between the two windows and
  breaks the common-`ν` premise. The reduced-cost argument in §1 needs no such
  premise and carries the finding on its own.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only, hard-filtered in the probe and
  fail-closed. CAISO holds no `complete` marker, so 2022 / 2019 / ≤2021 /
  H1-2026 were untouched and no marker was written.
* **The measured comparator is the day-ahead hub**, matching the keeper's own
  import-tranche basis (caiso-167 §6). No RT series was used.

## §8 — DO-NOT-REDO (new, binding)

1. **Do not re-quote caiso-121's "+1967/+2049/+2244 MW storage over measured"**
   as a battery statement. It is model **all-tech** net against a **PS-excluding**
   series. Quote **+736 / +717 / +979 MW** (belly-surplus, like-for-like battery
   net) or **+76 / +34 / +47 MW/h** (annual), and name the basis. §3.
2. **Do not re-measure whether a storage charge column sets the belly dual.**
   §1–§2 carry it, with the bound reconstruction validated exactly against
   EIA-860 on all 36 months.
3. **Do not propose a new charge-side cap, floor, adder or hurdle on the battery
   limb.** §5's census is complete; the class that can reach is the armed
   `caiso_storage_shape_anchor`, and re-picking its percentile against this
   residual is an outcome pin (rules 13/23/24) and a stack (rule 19). A charge-side
   `battery_dispatch_adder` twin is the same object.
4. **Do not approximate the pumped-storage envelope.** No hydro-minus-PS split,
   no proxy from `WAT`, no scaled battery envelope, no fitted PS adder. The
   C3a-2025 wall (caiso-141/145) governs; only the non-public hourly PS intake
   re-opens it. §4.
5. **Do not treat this as a verdict on S2.** Item 3 keeps its original
   evening/overnight scope and is untouched. §6.
6. **Use the non-leap 8760 clock with Feb-29 dropped** for any CAISO probe that
   pairs a measured series to model hours. A linear-offset hour index is a
   one-day phase error for every 2024 hour after Feb-28. §1.
