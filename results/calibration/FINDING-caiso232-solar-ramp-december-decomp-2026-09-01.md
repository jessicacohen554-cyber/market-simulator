# FINDING — caiso-232: the owner's two symptoms are **TWO DIFFERENT DEFECTS**, and the level/shape split proves it — the **morning** miss is a diurnal SHAPE defect monotone in the solar ramp (+11.02 $/MWh in the steepest morning-ramp sextile) whose mechanism is the ALREADY-MEASURED caiso-216 strandedness bound, here COUPLED to the morning for the first time: the model reproduces CAISO's **system** curtailment (spill 0.47/1.17/0.84 vs measured system 0.54/0.23/0.57 TWh) and **structurally cannot produce its LOCAL curtailment — 79/93/84 % of the real total, 1.97/2.96/2.91 TWh/yr solar** — because local curtailment is sub-zonal congestion and the CA network is three zones; **December** is NOT a solar defect at all — its residual is FLAT across all 24 hours (Dec-2025 +7.4…+13.5 $/MWh, including h0–h5 at zero solar), it is the model's highest-import month (7.08 GW, annual max) and it lands on the already-declared `IMPORT_TRANCHES[CAISO]` residual. The spill mechanism is PROVEN CORRECT (λ → the −$20 dump floor on spill); the defect is that the model REACHES that regime a third as often. NO LP, NO SOLVE — committed bytes only (2026-09-01)

**Keeper `2026-09-01-caiso-231-b1-ungrounded` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no LP built, no solver called, nothing registered,
no matrix cell verdict moved.** Charter: the owner's 2026-09-01 handoff — *"address
overprice in mornings while solar is available as well as Decembers. It appears our
pricing is not properly adjusting around solar availability or whatever happens each
December."*

The CAISO lane is **RESTED BY OWNER RULING** (caiso-201, 2026-08-17) with the
in-model lever queue declared **EXHAUSTED**. This session spends no lever and
proposes none. It is a measurement that answers the owner's question on its own
axes, and the honest answer is that **one symptom is a structural limit of the
zonal network and the other is the standing declared import residual** —
neither is an offer-curve object, and neither should be closed by one (rule 1
`[R-STRUCT]`, rule 13 `[R-MEASURED]`).

`calibration-complete.json` (no CAISO marker) and `holdout-freeze.json` (ACTIVE)
untouched; every read stayed inside 2023–2025.

Instruments (committed, no LP, no solve):

* `scripts/probes/_caiso232_solar_ramp_december_decomp.py` →
  `results/calibration/_caiso232_solar_ramp_december_decomp.json` — §A–§E below.
* Charts (all eight figures, both themes, table views):
  <https://claude.ai/code/artifact/24d8650d-fd6d-47ca-8967-9a6b91ace598>

Every number reproduces from the keeper's committed `hourly/` sidecars, the
committed actual-LMP reference (`actual_lmp_hourly_CAISO.parquet`, rt+da), the
committed measured HSL potential/delivered series (`data/raw/caiso-hsl`), the
EIA-930 `CISO_fueltype.parquet` extract, the measured WECC intertie hub parquet,
and CAISO's published `productionandcurtailmentsdata_<year>.xlsx`.

---

## §A — Why the prior C3a record could not answer this question

The standing decompositions bucket the residual on axes that **cannot separate
the owner's two symptoms**:

| finding | axis used | what it could not see |
|---|---|---|
| caiso-202 §B | **actual price** bucket | a residual ordered by *solar*, and the level/shape split |
| caiso-227 §A | **month block** (Sep–Dec) | that December's residual is FLAT in hour-of-day while May's is peaked |

This probe adds the two missing axes: **solar availability** (potential share and
ramp rate) and **hour-of-day within month**. The decisive move is the
**level/shape split** — subtracting each (year, month) mean residual, so the
monthly LEVEL and the diurnal SHAPE are measured separately. Under that split the
owner's two symptoms fall into two different halves and stop being one lane.

## §B — The morning: a SHAPE defect, monotone in the solar ramp

Within-month-demeaned residual (model − actual RT) by hour of day, $/MWh:

| year | h07 | h08 | h09 | h16 | h17 | h18 |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | +3.48 | **+8.58** | +7.61 | −2.35 | −6.39 | **−13.99** |
| 2024 | +6.24 | +6.21 | +5.41 | −5.04 | −7.70 | −8.55 |
| 2025 | +5.49 | +4.61 | +4.84 | −5.48 | −5.59 | −2.66 |

The same dipole in all three years: a **morning-positive, evening-negative**
shape. Ordered by the MEASURED solar ramp (Δ HSL potential), morning hours
h6–h11, 2023–2025 pooled, six equal bins:

| ramp (MW/h) | −60 | +384 | +1,004 | +2,052 | +3,735 | +6,552 |
|---|--:|--:|--:|--:|--:|--:|
| **shape error** | **−3.75** | **+1.24** | **+2.65** | **+4.61** | **+8.31** | **+11.02** |
| model λ | 46.0 | 30.7 | 32.7 | 39.9 | 38.0 | 34.5 |
| actual RT | 46.7 | 25.2 | 25.9 | 31.8 | 25.9 | **19.2** |

**Monotone across every bin.** In the steepest bin the model clears $34.5 while
reality clears $19.2. The evening mirrors it: on the steepest down-ramps the
model is −6.43/−7.86 too LOW, failing to rise as solar leaves. One deficient
elasticity, both directions.

Summary statistic — **diurnal amplitude ratio** (mean daily price range, model ÷
actual): **0.4877 / 0.5568 / 0.6366**. The model's price swings roughly half as
far across the day as reality's.

**The phase control ACQUITS time alignment** (this was the first hypothesis and
it is dead): model solar vs measured delivered solar correlates **r = 0.9928 /
0.9956 / 0.9954 at lag 0** in 2023/2024/2025, and model λ vs actual RT peaks at
lag 0/+1. Nothing is shifted; the amplitude is short.

## §C — The mechanism: the LOCAL half of curtailment, which a 3-zone CA network cannot produce

**THE LOCAL/SYSTEM SPLIT IS NOT NEW AND IS NOT CLAIMED HERE.** caiso-216 already
measured it and the `solar_deliverability` matrix cell already records it —
*"reality's curtailment record measured 78/92/83 pct LOCAL-class 2023/24/25 of
2.66/3.42/3.77 TWh reported — the sub-zonal strandedness bound on any zonal
repair"*. This section **reproduces that bound on the caiso-231 keeper** (the
figures below are solar-only, 2.509/3.193/3.482 TWh; adding the wind rows
0.150/0.231/0.283 recovers caiso-216's 2.659/3.424/3.765 exactly, and the model
spill 475/1,170/840 GWh sits beside caiso-221's 482/1,184/849 GWh on the prior
keeper). **What is new is §B's link:** the bound had never been tied to the
*morning shape error*, because nobody had measured the residual on the
solar-ramp axis. The contribution is the coupling, not the split.

CAISO's published workbook splits solar curtailment **by reason**. Against the
keeper's own solar spill (measured HSL potential less dispatched solar):

| year | measured **Local** | measured **System** | **model spill** | spill − system | local share |
|---|--:|--:|--:|--:|--:|
| 2023 | **1.973** | 0.536 | 0.475 | −0.061 | **78.7 %** |
| 2024 | **2.960** | 0.233 | 1.170 | +0.937 | **92.7 %** |
| 2025 | **2.912** | 0.570 | 0.840 | +0.269 | **83.6 %** |

*(TWh/yr.)* **Against measured SYSTEM curtailment the model is close and in
2024–25 runs slightly OVER. Against LOCAL curtailment it produces nothing.** The
entire curtailment deficit is the local half — and local curtailment is
sub-zonal congestion, which this network cannot represent by construction. Its
timing matches the defect: local curtailment starts at h7–h8 and **38.5–40.7 %
of it falls in h6–h11**, the window where the shape error peaks.

**The spill machinery itself is PROVEN CORRECT — this is not a bug.** 2025
daylight hours with potential > 2 GW, binned by spill fraction:

| mean spill (MW) | 0 | 161 | 504 | 1,263 | 2,596 | 6,145 |
|---|--:|--:|--:|--:|--:|--:|
| model λ | 35.0 | 9.7 | −0.3 | −15.4 | −19.9 | **−20.3** |
| actual RT | 28.2 | 6.6 | −2.8 | −13.4 | −19.4 | −26.8 |

Spilling zero-MC solar drives λ to the −$20 dump floor exactly as designed. The
consequence of reaching it too rarely is a **BIMODAL** model price — gas-marginal
near $35–48, or floored — where reality's distribution is continuous. That
bimodality *is* the missing amplitude of §B.

**Honest limit on the attribution, recorded against interest.** Correlating the
within-month shape error against measured local curtailment over month × hod
cells gives **r = +0.267 / +0.202 / +0.219**, consistently above the
system-curtailment correlation (+0.122 / +0.014 / +0.050) but **modest**. The
load-bearing evidence is the volume identity and the timing, NOT the cell-level
correlation, and this finding does not claim more.

## §D — December: a LEVEL defect with no solar involvement

December-2025 residual by hour of day, $/MWh — **every one of the 24 hours**:

| h00 | h02 | h05 | h08 | h11 | h14 | h17 | h20 | h23 |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| +10.03 | +11.18 | +8.74 | +9.66 | +8.56 | +13.51 | +8.29 | +8.19 | +13.26 |

Range **+7.41 … +13.51**, including h0–h5 at **zero solar**. There is no diurnal
structure to explain — this is a slab, where May's residual is a solar-shaped
bulge. **Whatever is wrong in December is wrong at 2 a.m.**, so no solar
mechanism reaches it.

December is also the only month positive on **both** settlement bases in all
three years (vs RT +4.58/+5.07/+9.56; vs DA +2.49/+4.59/+6.13), which is what
distinguishes it from the January/July swings that are RT–DA basis artifacts.

The supply-state witness points at imports, not gas:

* Dec-2025 model gas is only **−873 MW** below the CEMS-measured actual — its
  **smallest** gas deficit of the year (every other 2025 month: −2,660 to
  −4,433 MW).
* Dec-2025 model imports are **7,082 MW**, the **annual maximum** (every other
  2025 month: 3,485–5,851 MW).
* Model λ sits near the measured MALIN hub plus wheel + CARB border carbon
  ($44.33 model vs $39.14 MALIN) while CAISO's own RT cleared **$34.77** —
  below the delivered cost of the marginal in-state CC, reproducing the
  caiso-227 §A observation on this keeper.
* Pooled over the 34 months with hub coverage: **corr(monthly residual, model
  import volume) = +0.419**. (corr with the MALIN premium over RT is −0.215 —
  the volume, not the hub premium, is the ordered axis.)

**This lands on an already-declared residual, and adds no new object.** The
`IMPORT_TRANCHES[CAISO]` row carries **six live fitted scalars** on the backcast
binding path — four uncited spot capacities (8,800 MW) and two firm prices
(caiso-188/189 census). The new fact is *where they bite*: December, hardest,
and worsening year on year.

## §E — What would actually close each, and what this session refuses to do

**Morning (§B/§C) — needs sub-zonal congestion, not a lever.** The missing
physics is local transmission limits inside the CA zones, whose dual would
produce local curtailment endogenously and pull the morning λ down with it.

* Feeding measured curtailment volumes back in is **REFUSED under rule 13**:
  that is the existing `caiso_solar_cap_at_delivered`, self-labelled a default-off
  diagnostic pin that "must never feed a keeper" — it pins the model to an
  OUTCOME, not a driver, and has no forward analogue.
* The legitimate route is a deliverability constraint identified from published
  limits — and both such routes are recorded **CEII-blocked** (caiso-218/219,
  caiso-220 split witness).
* `ramp_envelopes` is **I** in CAISO and is NOT re-opened here: the CAMPD
  max-observed 1-h envelope is far too loose to bind in these hours, and rule
  28(a) forbids re-testing an adjudicated cell without new evidence that the
  mechanism itself reaches the defect. This finding supplies evidence about the
  DEFECT, not about that mechanism.

**December (§D) — the standing owner object.** Grounding the import tranches is
adjudicated and unfunded. Nothing here unblocks it; the contribution is a
sharper target (December, import-volume-ordered) than "the belly", and December
is the cleanest test month precisely because no solar mechanism competes there.

**What this session did NOT do:** no solve, no bundle, no dashboard
registration (rule 15 applies to completed runs — the caiso-134/140/150/202
disposition), no cell verdict moved, no lever proposed off an exhausted queue.

## §F — Record changes

* Keeper, markers, freeze, determination (**NOT-YET**): UNCHANGED.
* Matrix (rule 28(b), CAISO shard only) — **evidence appends, no verdict moves**:
  `diurnal_price_amplitude` (U — §B is now its quantified CAISO evidence base:
  the amplitude ratio triplet and the ramp-ordered monotone), `solar_deliverability`
  (K — §C's local/system split), `import_hub_pricing` (K — §D's December
  import-volume ordering, consistent with the caiso-202 §C <5 % direct-marginal
  acquittal: volume, not rung).
* This document + the probe + its JSON are the deliverable.
