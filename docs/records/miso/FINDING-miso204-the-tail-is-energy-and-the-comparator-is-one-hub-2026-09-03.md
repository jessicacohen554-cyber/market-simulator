# FINDING miso-204 — the C3a-2025 tail is an ENERGY object, not a congestion one (the pre-registered verdict); and, found while chasing why congestion came back NEGATIVE, the C3a comparator is a SINGLE HUB on a clock one hour off the model's (2026-09-03)

**Session:** miso-204, branch `claude/miso-lmp-decomposition-sj1sq5`.
**Keeper at open AND at close: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested
(ledger 41/2, n_residual 2).

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER
`data/raw/`. NO SCORING ARTIFACT CHANGED.**

**PREREG** `results/calibration/PREREG-miso204-lmp-component-decomposition-2026-09-03.md`,
pushed at **`fd6c4dff`** BEFORE any adjudicating statistic, with four gates,
their decision rules fixed in advance, seven scored predictions, six traps each
carrying a pre-committed counter-measurement, and a re-aim map written before the
numbers and applied mechanically.

**Instruments** `scripts/probes/_miso204_lmp_component_decomposition.py`
(pre-registered) and `scripts/probes/_miso204_scoring_reference_instrument.py`
(section F, explicitly post-hoc); records
`_miso204_lmp_component_decomposition.json`,
`_miso204_scoring_reference_instrument.json`.

---

## 1. Headline

**The pre-registered verdict is ENERGY, and it holds on both bases.** In the 15
scarce hours of 2025 the energy component carries **125.5 %** of the model's
shortfall on the frozen basis and **93.1 %** on the C3a instrument's own; the
congestion component carries **−23.3 %** and **+3.8 %**; losses **−2.2 %** and
**+3.1 %**. **15 of 15 hours are energy-largest** at the hour grain in every
year on both bases. Charter (c) is answered: **the object is system-wide energy
price formation in the afternoon–evening window, not congestion.** The
ORDC/offer/capability families are aimed at the right *kind* of thing; the
capability-removal family remains closed on miso-139 reach and miso-203 location.

**And then the sign of the congestion component sent the session somewhere the
PREREG did not anticipate.** `share_cong` came back **negative** — the eight
trading hubs sit on the *cheap* side of congestion in the object's hours — which
is only possible if the series being decomposed is not the series C3a is scored
against. It is not. Chasing it produced the session's larger result:

1. **The C3a actual is ONE HUB.** `actual_lmp_hourly_MISO.parquet` — the series
   behind `bench.avgLMP.rt`/`rt_lw`, i.e. C3a itself — is **INDIANA.HUB**
   (`derive_miso_hub_lmp.py`'s own docstring says so; verified here at
   max\|diff\| **1.3e-05 / 2.7e-05 / 5.9e-05**, float32 rounding). Both committed
   probes decompose an **eight-hub equal-weighted average** instead, which runs
   **$3.43 / $3.92 / $4.71 per MWh BELOW** it.
2. **The committed probes' clock is one hour off the model's, and 25 hours off
   after Feb 28 of a leap year.** The raw reports are hour-ending **Eastern
   Standard** year-round; the model and the scoring reference are on fixed
   **Central Standard**, non-leap. Diagnosed by lag scan, not asserted: the two
   series correlate **r = 1.000000** at exactly **k = −1** in 2023 and 2025, and
   in 2024 at **k = −1** for Jan 1–Feb 28 (r = 1.000000) and **k = −25** for
   Mar 1–Dec 31 (r = 0.999969).
3. **That is fatal to hour-matching, and invisible in the annual mean.** The
   annual means agree to three decimals (28.358 / 26.881 / 38.136 both ways) —
   but MISO's RT hub price has a **lag-1 autocorrelation of only 0.39 / 0.37 /
   0.44**, so a one-hour shift drops the hour-matched correlation to *exactly*
   that: **0.390 / 0.260 / 0.443**.
4. **So the object relocates.** Of the 15 hours miso-202 located and miso-203
   characterised, only **2 / 1 / 4** are in the top 1 % of the series C3a is
   actually scored on. Correcting the **clock alone** leaves **3 / 1 / 5**;
   correcting the **hub set alone** leaves **8 / 13 / 11** — the clock is the
   larger error.
5. **The verdict survives the relocation; miso-203's hour-of-day characterisation
   does not, in part.** On the corrected instrument the 2025 object's mean
   hour-of-day is **15.87 CST**, not 18.33; **4 of 15** fall in h18–h21 rather
   than 13 of 15, and **11 of 15** fall in **h15–h18 CST**. The 2023→2024
   migration is real and large (**11.67 → 15.73**); the 2024→2025 step miso-203
   read as a continuing march is **flat (15.73 → 15.87)**.
6. **A basis wedge sits inside C3a itself.** Load-weighted over 2025,
   INDIANA.HUB carries **+$1.54/MWh of congestion and +$0.90/MWh of loss** above
   MISO's own system energy price. Scored against that system energy price
   instead, the C3a-2025 face reads **−7.41 %** rather than **−12.38 %**. **This
   is reported as a basis fact and is NOT a proposal to change the metric.**

**What did not change.** The keeper, the determination, every scored artifact,
and the substantive object: in the single largest hour of 2025
(**2025-07-28 HE18 CST**) MISO's own **system energy price** was **$1,726.34**
against a model **$161.39**. The tail is real, it is energy, and it is 5–11×.

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **N-2** additive identity + coverage | **PASS.** Hub order identical across the three component labels; reconstruction residual **1.1e-13 / 1.1e-13 / 2.3e-13** (float). §3 |
| **N-1** MEC hub-invariance *(the TRAP 1 counter-measurement)* | **CONFIRMED, decisively.** `MEC = LMP − MCC − MLC` is hub-invariant in **100.00 %** of all 8,760 hours of all three years, max spread **$0.02**. The alternative convention is within $0.51 in **0.011 % / 0.000 % / 0.000 %** of hours, max spread up to **$4,933.68**. §3 |
| **G-1** which component carries the excess *(charter (a))* | **ENERGY**, on the frozen basis (2025 `share_energy` **1.2547** ≥ 0.50) and on the corrected instrument (**0.9306**). R-1 agrees: **15/15** energy-largest, both bases, all years. §4 |
| **G-2** cross-hub dispersion *(charter (b))* | **SPLIT**, by a wide margin — 2025 OBJ mean cross-hub `max−min` **$333.38** vs JJ **$28.91**, ratio **11.53** against a 2× line (2023 **11.84**, 2024 **7.58**). And **all** of it is congestion: MEC's cross-hub spread is **$0.012**. §5 |
| **G-3** the re-aim *(charter (c))* | applied mechanically to the ENERGY row of PREREG §5. §8 |
| **G-4** the bound *(charter (d))* | **NOT REACHED** — the §5 ENERGY row names `G` and `I` families, so the PREREG §6 stop rule fires and the session ends at the finding. **No lever bounded, no solve spent.** §8 |
| **N-3** *(section F, post-hoc)* scoring-clock reconstruction vs production | **EXACT.** max\|diff\| **0.0** on **70,080 / 70,080 / 70,072** hub-hours; NaN counts identical. §6.2 |
| *F* the instrument forensic | *post-hoc, no gate, licenses nothing.* §6 |

**Stop rule honoured as written.** PREREG §6: a solve is spent only if G-1's §5
row names an `O`/`U` family **and** a lever within it clears charter (d). The
ENERGY row names `ordc_scarcity_overlay` (`G`), `ramp_envelopes` (`I`) and
`measured_ramp_capability` (`U`, but explicitly *named, not chartered*, pending a
primary-source product question this session did not answer either). Nothing was
armed and no LP was solved. **TRAP 5 armed and held.**

---

## 3. N-1 / N-2 — the decomposition is an identity, and the convention is proved

`data/raw/lmp-data/MISO/miso_hub_lmp_<year>_rt.csv.gz` carries **LMP**, **MCC**
and **MLC** rows for the eight named trading hubs — 2,920 / 2,928 / 2,920 rows
each, identical coverage. Both committed probes filter `value == "LMP"` and
discard the rest.

MISO settles `LMP = MEC + MCC + MLC`, so `MEC = LMP − MCC − MLC` is an identity
with **zero free parameters**. TRAP 1 pre-committed the sign convention's
counter-measurement, and it is decisive because MISO prices a **single
system-wide** energy component:

| year | frac. of hours with MEC hub-spread < $0.51 | max spread | same, under `MEC = LMP + MCC + MLC` | its max spread |
|---|---:|---:|---:|---:|
| 2023 | **1.000000** | $0.02 | 0.000114 | $1,059.68 |
| 2024 | **1.000000** | $0.02 | 0.000000 | $2,076.65 |
| 2025 | **1.000000** | $0.02 | 0.000000 | $4,933.68 |

The preferred convention yields a MEC identical across all eight hubs to **two
cents** in **every hour of every year**. That is not a fit; it is the signature
of a single published system energy price, and it settles TRAP 1.

---

## 4. G-1 — the excess is ENERGY, on both bases

**On the frozen OBJ set** (PREREG §1.3, inherited byte-identically from
`_miso202_c3a_2025_anatomy.json`), mean over the 15 hours, $/MWh:

| year | actual LMP | actual **MEC** | actual MCC | actual MLC | model | **share energy** | share cong | share loss | R-1 (E/C/L) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2023 | 138.49 | **171.15** | −31.36 | −1.30 | 37.95 | **1.3248** | −0.3119 | −0.0129 | **15/0/0** |
| 2024 | 310.28 | **330.64** | −16.39 | −3.97 | 38.21 | **1.0748** | −0.0602 | −0.0146 | **15/0/0** |
| 2025 | 546.46 | **665.28** | −108.76 | −10.05 | 79.95 | **1.2547** | −0.2331 | −0.0216 | **15/0/0** |

Shares exceed 1 because congestion is **negative** at the eight-hub average — the
hubs sit *below* the system energy price, so the model has further to climb than
the LMP gap shows. That sign is what sent the session to §6.

**On the C3a instrument's own series and clock** (§6), same construction, the
object relocated to that series' own top 1 %:

| year | actual LMP | actual **MEC** | actual MCC | actual MLC | model (lw) | **share energy** | share cong | share loss | R-1 (E/C/L) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2023 | 187.67 | **170.69** | +13.25 | +3.73 | 36.13 | **0.8880** | 0.0874 | 0.0246 | 13/2/0 |
| 2024 | 328.94 | **326.01** | +1.11 | +1.81 | 38.92 | **0.9899** | 0.0038 | 0.0063 | **15/0/0** |
| 2025 | 718.32 | **674.03** | +24.29 | +20.00 | 81.46 | **0.9306** | 0.0381 | 0.0314 | **15/0/0** |

**The verdict is the same and the corrected numbers are better behaved** — all
three shares in [0, 1] and summing to 1, because INDIANA.HUB is a load-side
import point where congestion is positive, while the eight-hub average is dragged
below system energy by the four MISO-South hubs. **R-1 agrees with the mean-share
verdict on both bases** in every year but 2023-corrected, where 2 of 15 hours are
congestion-largest; per PREREG R-1 that is reported here rather than treated as a
flip.

**TRAP 4 held.** The load-weighted hub basis moves the congestion offset
(2025: −0.2331 → −0.1012) and **does not flip the verdict** (`share_energy`
1.2547 → 1.1081). The verdict is taken on the equal-weighted basis as
pre-registered.

**TRAP 6 held.** The model's zonal dual is not decomposable at comparable grain,
so `share_energy` absorbs any model-side congestion misplacement. Stated in the
PREREG before the result and repeated here. §5 bounds how much that can be: the
model's own cross-zone spread in the 2025 object hours is **$7.95**, against
the actual hubs' **$333.38**.

---

## 5. G-2 — the hubs split hard, and every dollar of the split is congestion

Mean cross-hub `max − min`, $/MWh:

| year | LMP, OBJ | LMP, JJ | **ratio** | MCC, OBJ | MEC, OBJ | model zone price, OBJ | model zone price, JJ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 193.78 | 16.37 | **11.84** | 178.41 | **0.012** | 0.00 | 0.45 |
| 2024 | 141.79 | 18.70 | **7.58** | 113.75 | **0.010** | 0.63 | 1.82 |
| 2025 | 333.38 | 28.91 | **11.53** | 278.23 | **0.012** | 7.95 | 1.56 |

**G-2 returns SPLIT in all three years**, against a 2× line. The charter framed
the two signatures as alternatives — *"a system-wide energy/scarcity event and a
binding-constraint event look completely different here: the first moves all 8
hubs together, the second splits them."* **They are not alternatives here; they
are simultaneous.** MISO's scarce hours are a system-wide energy event — MEC is
literally the *same number* at all eight hubs, to two cents — **with heavy
congestion superimposed** that splits the hubs by $333/MWh. The level is energy;
the dispersion is congestion.

**What this does and does not license.** It does **not** re-open
`internal_congestion_split` (`G`, miso-78/79/80): miso-79 established that
NO-BUILD is **fundamental, not provisional** — 88–99.7 % of every internal
congestion class's Σ\|SP\| is **intra-LBA**, and an optimal simultaneous split of
all six zones (~12 zones) captures only **1.9–3.8 %** of the mass. What it does
establish is that **the model's six-zone representation reproduces essentially
none of the dispersion** ($7.95 against $333.38 in 2025) — which is the known
representation limit, now measured in the object's own hours, and it is **not**
where the C3a residual lives.

---

## 6. Section F — the instrument forensic (POST-HOC, NOT PRE-REGISTERED, NO GATE)

G-1 returned a negative congestion share. The eight trading hubs cannot be below
the system energy price *and* be the series a load-weighted actual is built from,
so the comparator's provenance was read. **This block carries no gate and
licenses nothing.**

### 6.1 The C3a actual is INDIANA.HUB

`scripts/data/derive_miso_hub_lmp.py` states it in its own docstring: the system
scoring reference `actual_lmp_hourly_MISO.parquet` is *"verified hour-for-hour
identical to this staging's INDIANA.HUB series under the shared indexing."*
Verified here against the committed zonal parquet:

| year | max\|diff\| sysref − INDIANA.HUB | annual mean, INDIANA.HUB | annual mean, 8-hub | **gap** |
|---|---:|---:|---:|---:|
| 2023 | 1.34e-05 | 31.789 | 28.358 | **+3.431** |
| 2024 | 2.69e-05 | 30.796 | 26.881 | **+3.915** |
| 2025 | 5.86e-05 | 42.850 | 38.136 | **+4.714** |

`bench.avgLMP.rt` for 2025 is **42.85** — INDIANA.HUB's mean exactly. The eight
hubs are staged and available; the scoring reference uses one of them.

### 6.2 The clock, diagnosed by lag scan rather than asserted

The raw reports are hour-ending 1–24 **EST year-round**; the model's MISO
calendar and the scoring reference are fixed **CST** (`Etc/GMT+6`),
chronological, non-leap. The production transform is EST hour-beginning → UTC →
CST — a constant **−1 h** — with CST Feb 29 dropped. Both committed probes index
the raw hour-ending label directly.

**N-3 first:** the reconstruction of that transform reproduces the committed
zonal parquet at **max\|diff\| = 0.0** on **70,080 / 70,080 / 70,072** hub-hours,
with identical NaN counts. The instrument is production's.

Correlation of the committed-probe series against the same eight hubs on the
scoring clock, as a function of the shift `k` applied to the committed series:

| year | k=−2 | **k=−1** | k=0 | k=+1 | k=+2 | series' own lag-1 autocorr |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 0.3900 | **1.0000** | 0.3900 | 0.3001 | 0.2396 | **0.3901** |
| 2024 | 0.2910 | 0.3188 | 0.2595 | 0.1850 | 0.1768 | 0.3711 |
| 2025 | 0.4429 | **1.0000** | 0.4429 | 0.2309 | 0.1753 | **0.4430** |

2023 and 2025 are a **pure one-hour shift** — r = 1.000000 at k = −1. **2024
reaches 1.0 at no single k, because it is a leap year**, and splitting it
confirms the mechanism exactly:

| 2024 half | correct k | r | wrong k | r |
|---|---:|---:|---:|---:|
| Jan 1 – Feb 28 | −1 | **1.000000** | −25 | 0.4924 |
| Mar 1 – Dec 31 | −25 | **0.999969** | −1 | 0.1849 |

**−1 h everywhere, and a further −24 h after Feb 28 in a leap year.** That is
TRAP 2's defect, measured.

**Why it is invisible in the level and fatal in the hours.** The annual means are
identical to three decimals (28.358 / 26.881 / 38.136 on both indexings), so
nothing in an annual or monthly aggregate reveals it — and C3a, being annual, is
**unaffected**. But MISO's RT hub price has a lag-1 autocorrelation of only
**0.39 / 0.37 / 0.44**, so the hour-matched correlation of the committed series
against the scoring reference is **0.296 / 0.229 / 0.432**. **Any hour-matched
analysis on the committed construction is close to uninformative.**

### 6.3 The object relocates

Top-1 %-of-Jun–Jul hours, 15 per year, overlap with the frozen OBJ set:

| year | committed ∩ **scoring reference** | committed ∩ scoring-clock 8-hub *(clock error only)* | scoring-clock 8-hub ∩ scoring reference *(hub error only)* | threshold, committed | threshold, scoring ref |
|---|---:|---:|---:|---:|---:|
| 2023 | **2 / 15** | 3 / 15 | 8 / 15 | 100.42 | 121.43 |
| 2024 | **1 / 15** | 1 / 15 | 13 / 15 | 129.68 | 159.01 |
| 2025 | **4 / 15** | 5 / 15 | 11 / 15 | 238.93 | 373.02 |

**The clock is the larger error** — it alone costs 12–14 of the 15 hours, while
the hub choice alone costs 2–7.

### 6.4 The verdict is robust to all of it

§4's second table is the whole answer: **ENERGY in all three years on the
corrected instrument**, `share_energy` 0.888 / 0.990 / 0.931, R-1 13/15, 15/15,
15/15. **The pre-registered conclusion does not depend on the defect.** The 2025
hours, on the model's own clock (`model_lw` is the C3a load-weighted model
price):

| CST stamp | LMP | **MEC** | MCC | MLC | model_lw | in frozen OBJ |
|---|---:|---:|---:|---:|---:|---|
| 2025-06-17 HE18 | 543.22 | 537.81 | 0.00 | 5.41 | 49.45 | — |
| 2025-06-23 HE18 | 838.90 | 772.96 | 33.63 | 32.31 | 85.31 | — |
| 2025-06-23 HE19 | 1046.69 | 937.76 | 73.81 | 35.12 | 127.64 | ✓ |
| 2025-06-24 HE11 | 382.73 | 322.15 | 50.15 | 10.43 | 52.77 | — |
| 2025-06-24 HE12 | 406.29 | 350.74 | 43.77 | 11.78 | 58.45 | — |
| 2025-06-24 HE16 | 390.12 | 339.64 | 35.48 | 15.00 | 64.56 | — |
| 2025-06-24 HE17 | 451.42 | 411.96 | 19.85 | 19.61 | 64.61 | — |
| 2025-06-24 HE18 | 1202.05 | 1108.33 | 36.11 | 57.61 | 64.61 | — |
| 2025-06-24 HE19 | 774.99 | 724.43 | 13.96 | 36.60 | 68.46 | ✓ |
| 2025-07-15 HE16 | 413.32 | 402.35 | 5.06 | 5.91 | 50.65 | — |
| 2025-07-22 HE18 | 643.66 | 645.39 | 2.11 | −3.84 | 48.34 | — |
| **2025-07-28 HE18** | **1782.55** | **1726.34** | 19.51 | 36.70 | **161.39** | — |
| 2025-07-28 HE19 | 683.21 | 666.78 | 1.94 | 14.49 | 183.22 | ✓ |
| 2025-07-28 HE20 | 388.70 | 383.64 | 1.64 | 3.42 | 97.48 | ✓ |
| 2025-07-30 HE14 | 826.91 | 780.18 | 27.29 | 19.44 | 44.88 | — |

Note `2025-06-24 HE17` and `HE18`: the actual **triples** ($451 → $1,202) while
the model does not move at all ($64.61 → $64.61). That is the object in one row.

### 6.5 What miso-203's characterisation becomes

miso-203's G-E was measured on the committed construction, so its hour-of-day
statistics are on the raw **EST** hour-ending index rather than the model's
**CST** clock, and one hour late on top of that. Re-measured on the scoring
reference:

| year | mean hour-of-day, **committed** (reproduces miso-203 exactly) | mean hour-of-day, **corrected (CST)** | in h18–h21, committed | in h18–h21, **corrected** | in h15–h18, corrected |
|---|---:|---:|---:|---:|---:|
| 2023 | 14.40 | **11.67** | 2 / 15 | 1 / 15 | 1 / 15 |
| 2024 | 17.07 | **15.73** | 6 / 15 | 3 / 15 | 9 / 15 |
| 2025 | 18.33 | **15.87** | 13 / 15 | **4 / 15** | **11 / 15** |

The committed column reproduces miso-203's published 14.4 / 17.1 / 18.3, so this
is the same measurement on a repaired instrument, not a different one.

**What survives:** the object is an **afternoon-into-evening** phenomenon, it is
**not** at the load or temperature peak, and it moved substantially later between
2023 and 2024 (**11.67 → 15.73**, +4.1 h). **What does not:** the specific claim
that *"13 of 15 fall in h18–h21"* becomes **4 of 15**; the concentration is
**11 of 15 in h15–h18 CST**. And the *monotone* migration miso-203 read as
tracking the solar build (14.4 → 17.1 → 18.3, +2.7 h and +1.2 h/yr) is, on the
corrected instrument, **one large step and then flat** (11.67 → 15.73 → **15.87**,
+0.14 h in the final year). **The forward-relevant claim that MISO's tail is
migrating into the evening is NOT refuted — but it rests on a single year-pair,
not on a three-year march, and should be re-established before it is relied on.**

**The full driver re-characterisation is NAMED, NOT CHARTERED.** miso-203's
net-load / solar-collapse contrast (11.6 GW less load but only 2.2 GW less net
load; solar 11,435 → 1,859 MW) was computed on the misaligned hour set against
model-clock drivers, so it is **not** re-affirmed here and **not** refuted here —
it is **unmeasured on the corrected instrument**. Redoing it is a cheap,
zero-solve successor and it should be done before any lever is keyed to that
story.

### 6.6 The basis wedge inside C3a — reported, and NOT a proposal

Load-weighted over the year, on the scoring reference's own clock:

| year | actual (INDIANA.HUB) | system MEC at that hub | model_lw | **C3a face** *(verdict)* | face on the MEC basis | congestion wedge | loss wedge |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 32.847 | 30.502 | 32.889 | **+0.1274** *(+0.1218)* | +7.83 | +1.653 | +0.692 |
| 2024 | 32.301 | 30.019 | 30.814 | **−4.6028** *(−4.5820)* | +2.65 | +1.498 | +0.784 |
| 2025 | 45.456 | 43.016 | 39.827 | **−12.3833** *(−12.3845)* | **−7.41** | +1.542 | +0.897 |

**The instrument reproduces the verdict** (2025 to **0.0012 pp**), so this is
C3a, not an approximation of it.

C3a compares a **MISO-wide load-weighted model price** to a **single load-side
hub** that carries **+$2.44/MWh** of congestion and loss above MISO's own system
energy price in 2025. Scored against the system energy price instead, the
2025 face is **−7.41 %** — i.e. roughly **40 % of the C3a-2025 residual is a
locational-basis artifact of the comparator**, not model error.

**This is stated as a fact about the instrument and is explicitly NOT a proposal
to change it.** Three reasons, recorded so a later session does not read a
licence here: (i) the wedge is not free — a MEC comparator would change every
ISO's C3a basis and every historical MISO verdict, which is a rubric change and
an owner decision, not a calibration one; (ii) the model's own zonal duals are
not loss-free-comparable in the way the arithmetic above pretends (TRAP 6);
(iii) rule 1 `[R-STRUCT]` — the residual would move without any mechanism
becoming more faithful, which is exactly the move the rule forbids. It is filed
as a **rule-14 `[R-ACCURATE]` instrument-basis item for the owner**, alongside the
one-hub and clock defects.

---

## 7. My prior, scored against interest

| # | prediction | stated | measured | verdict |
|---|---|---|---|---|
| **P1** | N-1 confirms; MEC hub-invariant in ≥99 % of hours | 0.80 | **100.00 %**, max spread $0.02; alternative up to $4,933.68 | **RIGHT, decisively** |
| **P2** | G-1 returns ENERGY in 2025 (`share_energy` ≥ 0.50) | 0.70 | **1.2547** frozen / **0.9306** corrected | **RIGHT, understated** |
| **P3** | `share_cong` < 0.25 **and** mean MCC < $60 | 0.65 | share **−0.2331** (inside, barely); mean MCC **−$108.76** (1.8× outside) | **HALF-WRONG — and the half I never wrote down is the one that mattered: I did not predict the SIGN, and the negative sign is what produced §6** |
| **P4** | `share_loss` < 0.05 in all years, on OBJ | 0.90 | \|−0.0129\| / \|−0.0146\| / \|−0.0216\| frozen; 0.025 / 0.006 / 0.031 corrected | **RIGHT.** Reported against it: on the JJ population the 2023 loss share reads 0.1034, a ratio of two near-zero numbers (mean excess −$2.25) and not meaningful |
| **P5** | G-2 returns SPLIT (≥2× in 2025) | 0.70 | **11.53×**, and all of it MCC (MEC spread $0.012) | **RIGHT, badly understated** |
| **P6** | *(against interest)* ≥3 of 15 congestion-largest in 2025 | 0.55 | **0 / 15** frozen, **0 / 15** corrected | **WRONG** |
| **P7** | mean MEC ≥ $250 **and** model < $80, 2025 OBJ | 0.60 | frozen $665.28 vs **$79.95** — inside by **five cents**; corrected $674.03 vs **$81.46** — **outside** | **RIGHT on the frozen basis by a hair, WRONG on the corrected one.** The substantive claim (MEC ≫ $250, model ≪ MEC) holds on both; the $80 line was arbitrary and I should not have written a threshold I had no basis for |
| — | P(arms a mechanism or spends a solve) | 0.10 | nothing armed, no LP | **RIGHT** |

**What I did not predict at all, and it is the session's larger result.** The
PREREG contains no prediction about the comparator's provenance. I decomposed
the series two committed probes used and assumed — without checking, and with the
means agreeing to three decimals, which would have reassured me if I had — that
it was the series C3a scores. It is not, on two independent counts. **P3's
missing sign is the thread**: I framed congestion as something that *adds* to
price, wrote a magnitude line and no sign line, and the negative value is the
only reason §6 exists. That is the second consecutive MISO session whose most
useful output came from the part of the prior that was wrong or absent, and the
lesson generalises: **predict the sign, not just the magnitude.**

**Against interest, plainly stated:** this session's headline correction lands on
miso-203 and miso-202 — this lane's own immediately preceding work, including the
probe construction that located the object in the first place. The object is
still real and still where those sessions said it was in kind; its hours are not.

---

## 8. What this licenses — nothing armed, and a re-aimed queue

**No lever is licensed and none is proposed.** PREREG §5's ENERGY row applied
mechanically:

1. **The object is system-wide energy price formation in the h15–h18 CST
   window**, in hours where the model has ample idle capability and prices the
   marginal unit **5–11× below** MISO's own system energy price. Confirmed on
   both bases; §6.4's table is the record.
2. **`ordc_scarcity_overlay` stays `G`.** A component share is **not** new
   evidence against the structural grounds of miso-163 §1–§4 (a Monte-Carlo LOLP
   probabilistic-risk construct absent from a perfect-foresight hourly LP), and
   rule 28(a) requires evidence defeating *those* grounds specifically. This
   finding **strengthens** the description of what the ORDC family would be
   aimed at and changes nothing about why it is refused.
3. **The congestion families stay closed.** `internal_congestion_split` `G`
   (miso-78/79/80, NO-BUILD fundamental), `zonal_loss_surface` `R`. §5 measures
   that the model reproduces ~2 % of the actual cross-hub dispersion, which is
   the known representation limit — and G-1 says that is **not** where the C3a
   residual lives, so nothing here argues for re-opening either.
4. **Queue item 2 (a ramp-constrained product) is untouched and still NAMED, NOT
   CHARTERED.** Its primary-source question — whether MISO's real market prices a
   ramp product in these hours — is unanswered by this session too. What §6.5
   adds is a caution: the *evening ramp* framing it inherited from miso-203 is
   one hour late and rests on a weaker year-pattern than reported, so its phase 0
   must re-establish the window on the corrected instrument before minting
   anything.
5. **Three instrument defects are NAMED, none chartered, none a lever.**
   * **(a) The C3a comparator is a single hub.** `actual_lmp_hourly_MISO.parquet`
     is INDIANA.HUB while seven other staged hubs are discarded, and it carries a
     **+$1.54 congestion / +$0.90 loss** wedge over system energy in 2025. Owner
     item; **not** to be "fixed" by a calibration lane, and not a licence to
     re-score anything.
   * **(b) The committed probe construction is on the wrong clock.**
     `_miso202_c3a_2025_anatomy` (blocks a2/a4) and `_miso203_scarce_hour_identity`
     index the raw EST hour-ending label; production applies −1 h and drops
     CST Feb 29. **Every hour-matched statistic in those two records is affected**
     (their annual and monthly blocks, which use `bench` aggregates, are not).
     The cheap repair is to route both through the committed
     `actual_lmp_hourly_zonal_MISO.parquet` rather than re-deriving from the raw
     staging — a successor, not this session's to spend.
   * **(c) `derive_miso_hub_lmp._market_frame` hardcodes `value == "LMP"`.** The
     MCC and MLC rows are staged, verified, and reach no committed artifact. If
     the component decomposition is ever wanted as a standing diagnostic, that is
     the one-line seam — **and it must stay a diagnostic**: rule 13, a measured
     price *outcome* is answer-class and must never enter a solve.
6. **The D-2 5(i) seam-response object is untouched by this session** and remains
   the largest named candidate, still awaiting the owner's admissibility ruling.

---

## 9. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…139 / miso-179 / miso-194 / miso-203 zero-solve precedent). Keeper
unchanged at `2026-09-03-miso-202-unitclip`.
**Rule 28(b) `[R-MECH-MATRIX]`** — **no mechanism was tested, so no cell verdict
moves.** The cells this session re-aims toward or re-affirms —
`ordc_scarcity_overlay` (`G`), `internal_congestion_split` (`G`),
`measured_ramp_capability` (`U`) — carry an amended evidence citation in MISO's
shard only, in this session. No other ISO's shard is touched (rule 28(d), rule
25); the pre-existing NYISO §5.x prose drift on `main` is not this lane's.
**Rule 28(c)** — no `ScenarioConfig` field added, so no base row is due.
**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only. MISO holds no `complete`/`final`
marker and the locked-test freeze is active. No out-of-training year was read,
solved, scored or registered.
**Rule 13 `[R-MEASURED]`** — the inputs are MISO's own published settlement price
components and the keeper's committed sidecars, read as a **diagnostic
decomposition of the residual**. Nothing here enters a solve, and §8(5c) records
explicitly that it must not.
**Rule 1 `[R-STRUCT]`** — §6.6 measures that ~40 % of the C3a-2025 residual is a
comparator basis artifact and **declines to act on it**, because moving the
residual without making a mechanism more faithful is the move the rule forbids.
**Rule 27 `[R-PUSH]`** — the two probes are new files; no existing ≥300-line file
is rewritten.
