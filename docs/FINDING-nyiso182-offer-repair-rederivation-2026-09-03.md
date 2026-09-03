# FINDING — nyiso-182: the repaired offer CONFIRMS the load-bearing premise and STRENGTHENS it, and the repair is not the uniform shift I predicted

**Session:** nyiso-182, NYISO backcast-calibration track, 2026-09-03.
**Keeper:** `2026-09-02-nyiso-177-vintage-matched` (`results/calibration/nyiso177_vintage_B1p`),
determination NOT-YET, target grade 5, fails 3 {C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}.
**Pre-registration:** `results/calibration/PREREG-nyiso182-offer-repair-rederivation.md`, committed
with the probe and the repair **before any quantity on the repaired basis was computed** (commit
`85ae68bf`).
**Solves:** **ZERO non-control.** One bit-identical control replay (the instrument), **not
registered** (rule 15). Keeper, determination, gate set, every score and every parameter
**UNCHANGED**; `src/market_sim/` **untouched**.

---

## 1. Headline

1. **The repair closes.** The repaired `build_year()` reproduces the LP's own installed offer at
   `max|d| = 2.7e-05 / 1.5e-05 / 3.0e-05` $/MWh over 88 units × 8,760 h in 2023 / 2024 / 2025 —
   float32 rounding on the `mc` column. All four instrument gates PASS; **S1 did not fire.**
2. **The load-bearing premise is CONFIRMED, and it is STRONGER than published.** On the repaired
   offer the 2025 top-decile price-level term is **1.072 of the gap** (published: 0.624), the
   offer-position term falls to **0.146** (published: 0.246), and the third term **changes sign**.
   `PREMISE-CONFIRMED` on both legs. **The lane stays blocked, the standing DO-NOT-OPEN on `ST_GAS`
   offer levers stands, and the brief's task-2 conditional does NOT arm.**
3. **The third term was not just mis-sized, it had the wrong sign.** "Un-dispatched at its own
   signal" was published at **+150 MW**; repaired and population-matched it is **−220.8 MW**, of
   which only **+14.1 MW** is un-run in-the-money capacity and **−234.9 MW** is *dispatch of
   out-of-the-money bins*. The model does not under-dispatch against its own offer in the 2025 top
   decile — **it over-dispatches**, by the floors and the bridge.
4. **G3's `PEAK-EXONERATED` verdict survives**, but not because nothing moved: every leg moved, and
   the 2023 and 2024 OOM-hours legs **crossed** the 0.90 bar (0.891 → 0.934, 0.863 → 0.925) while
   2025's fell *away* from it (0.806 → 0.768). The verdict is unchanged for a different reason than
   before.
5. **G4 gains a real fourth channel.** RGGI is `emission_rate × carbon_price` and both factors move
   between years; on full Shapley it contributes **−148.2 MW** to ΔITM(2023→2025) — **larger in
   magnitude than the AVAILABILITY channel (−109.6 MW)**, which the published three-channel form
   could not have seen. `PRICE` remains the carrier in all four grid cells.
6. **My own pre-registered directional expectation was FALSIFIED and is reported at full
   magnitude** (§6). PREREG §2 G-3R predicted *"the repair raises **every** band's `mc`"*. It does
   not. The margin term is `markup_hr × (anchor − fuel)`, which is **negative wherever delivered
   fuel exceeds the $3.9046 anchor** — so in the 2025 top decile (gas ≈ $11.76/MMBtu) the repair
   **lowers** the `peak` band's mean offer by **$188/MWh**.

---

## 2. What was run

| step | artifact |
|---|---|
| control replay of the keeper recipe, three years, one invocation, sequential | `results/calibration/nyiso182_control` (119 MB, **uncommitted**, `unit_hourly` gitignored) |
| I1 — replay identity | `scripts/probes/nyiso181_replay_identity.py`, **unmodified** → `_nyiso182_replay_identity.json` |
| the repair | `scripts/probes/nyiso179_st_gas_offer_position.py::build_year`, + explicit `legacy_defective_offer` opt-in |
| I2 / I2b / I3 / G-3R / G-4R / G-S | `scripts/probes/nyiso182_offer_repair_rederivation.py` → `_nyiso182_offer_repair_rederivation.json` |

**Environment note, disclosed:** this container's `data/clean` tree was empty, so the replay needed
`capacity-deliverability` and `nyiso-interface-flows` curated from `data/raw` first
(`scripts/regenerate_clean.py`). That is a hydration gap in the session, **not** a model or data
change: `data/clean` is derived, disposable and gitignored by design, and I1 proves the resulting
solve is the keeper.

### 2.1 The repair, and why it is not silent

`build_year()` gains `legacy_defective_offer: bool = False`. The **default is repaired**:

```
mc = assemble_mc(fa, fuel, resolve_carbon_price(cfg_y, year),
                 cfg_y.nox_price, so2=(fa.so2_rate, cfg_y.so2_price))
apply_gas_offer_margin(mc, gens, fuel, cfg_y)
```

`legacy_defective_offer=True` reproduces the published form exactly, **`main()` is pinned to it**,
and the module carries a repair banner. So `_nyiso179_st_gas_offer_position.json` — and every number
in `docs/FINDING-nyiso179-st-gas-offer-position-2026-09-03.md` — stays byte-reproducible by running
that file, which is the condition under which nyiso-181 declined to make this edit. The repair also
swaps nyiso-179's hardcoded `0.0` NOx/SO₂ prices for the config's own (both **are** 0.0 on this
keeper, so it is a no-op here and a correctness fix anywhere else).

---

## 3. Instrument gates — ALL PASS, S1 did not fire

### I1 — is the control replay THE keeper? **PASS.**
0 of 52,560 hourly zonal price cells and 0 of 122,640 class-hour cells differ, `max|d| = 0.0`, in
**all three years**. Bar inherited verbatim from nyiso-181. The replay is an **instrument, not a
run**, and is **not registered**.

### I2 — does the REPAIRED reconstruction equal the LP's installed offer? **PASS.**

| year | units | repaired `max|d|` $/MWh | legacy median `d` | legacy `max|d|` | capacity `max|d|` MW |
|---|---|---|---|---|---|
| 2023 | 88 | **2.665e-05** | −9.5736 | 1,458.99 | 1.713e-05 |
| 2024 | 88 | **1.496e-05** | −15.3879 | 686.58 | 1.713e-05 |
| 2025 | 88 | **2.980e-05** | −11.9775 | 2,914.03 | 1.713e-05 |

Bar `≤ 1e-4`, inherited from `nyiso181_offer_reconstruction_repair.py`'s `EXACT` criterion. **This
is the gate nyiso-180's P-c could not be**: it compares the *reconstruction* to the LP, not the LP
to itself. It independently reproduces nyiso-181 §4's identity from a fresh instrument.

### I2b — do the two routes to the ITM anchor agree? **PASS.**
2,489.633 / 2,397.389 / 2,448.846 MW by reconstruction vs the identical figures from the LP's own
`unit_hourly` frame; `|d| = 2.3e-05 / 7e-06 / 1.3e-05` MW against a 0.05 MW bar.

### I3 — does the LEGACY path still reproduce the published record EXACTLY? **PASS.**
`max|d| = 0.0` MW and `0.0` on shares, across all three years, every band, every G3 and G4 field.
The published verdicts (`PEAK-EXONERATED`, `CARRIER IDENTIFIED`) reproduce. **The repaired-vs-published
comparison is therefore like-for-like and not a different statistic.**

---

## 4. G-3R — the `peak` exoneration, re-derived. **PEAK-EXONERATED, and every leg moved.**

`p179.g3_band_attribution` run **unmodified** on a repaired state; both bars (0.40 / 0.90) and the
three-leg conjunction inherited verbatim.

| year | `peak` share of top-decile OOM MW | | `peak` OOM-hours share | | verdict legs |
|---|---|---|---|---|---|
| | **published** | **repaired** | **published** | **repaired** | bar |
| 2023 | 0.5338 | **0.3841** | 0.8912 | **0.9343** | hours ≥ 0.90 |
| 2024 | 0.5273 | **0.4729** | 0.8628 | **0.9252** | — |
| 2025 | 0.3359 | **0.3659** | 0.8062 | **0.7676** | share ≥ 0.40 **and** hours ≥ 0.90 |

**Verdict: `PEAK-EXONERATED`** — the 2025 legs are 0.3659 (< 0.40) and 0.7676 (< 0.90), so the
conjunction fails, as it did before.

**But the reason changed.** On the published basis the exoneration rested on 2025's share leg
missing by 0.064 with the 2023 hours leg *also* short (0.891 < 0.90). On the repaired basis the 2023
and 2024 hours legs **clear** the bar comfortably and it is **2025's hours leg that now fails
harder** (0.806 → 0.768). The verdict is the same word for a materially different configuration, and
that is worth saying plainly rather than reporting "unchanged".

**Why the legs moved as they did** — the per-band mean top-decile offer, which is the whole story:

| year | committed | econ\* | peak | actual top-decile price |
|---|---|---|---|---|
| 2023 | 41.83 → **49.40** (+7.57) | 43.81 → **51.22** (+7.41) | 155.30 → **161.04** (+5.74) | $72.20 |
| 2024 | 56.38 → **67.91** (+11.53) | 59.13 → **66.67** (+7.54) | 213.53 → **178.86** (**−34.67**) | $93.39 |
| 2025 | 106.99 → **119.28** (+12.29) | 112.38 → **107.38** (**−5.00**) | 415.94 → **227.82** (**−188.12**) | $176.25 |

---

## 5. G-4R — the between-year channels, with a fourth channel the published form could not see

Bar `0.60` inherited. Reported as the pre-registered 2 × 2 basis × method grid; the top-left cell is
I3's G4 leg and reproduces the published table exactly.

| basis × method | ΔITM MW | FUEL | PRICE | AVAIL | CARBON | carrier | verdict |
|---|---|---|---|---|---|---|---|
| legacy, published 3ch / 2 orders | +182.5 | −740.8 | +1,163.1 | −239.9 | — | PRICE | CARRIER IDENTIFIED |
| legacy, 4ch full Shapley (24 orders) | +182.5 | −700.2 | +1,082.0 | −199.3 | 0.0 | PRICE | CARRIER IDENTIFIED |
| repaired, published 3ch / 2 orders | +518.9 | −418.8 | +1,070.2 | −132.4 | — | PRICE | CARRIER IDENTIFIED |
| **repaired, 4ch full Shapley — PRIMARY** | **+357.8** | **−369.5** | **+985.1** | **−109.6** | **−148.2** | **PRICE** | **CARRIER IDENTIFIED** |

* **`share_denominator_is_small` is TRUE in every cell**, so — exactly as nyiso-179 disclosed of its
  own result and as this session's PREREG re-declared **in advance** — the shares are a
  near-cancellation artifact and **the MW contributions are the reported output**. The verdict word
  is secondary in all four cells and is reported as such.
* **CARBON is a real channel and it is not small**: **−148.2 MW**, larger in magnitude than
  AVAILABILITY (**−109.6 MW**). RGGI ran $13.49 → $22.09/tCO₂ across the window and the plant CO₂
  rate itself drifts (`max|d| = 0.0825 t/MWh`, measured); both are carried inside CARBON **by
  construction**, as pre-declared.
* **Structural certification holds**: `heat_rate`, `vom` and `markup_hr` max drift are **exactly
  0.0**, so the band channel is confirmed constant and the decomposition closes.
* The substantive answer to nyiso-179's chartered question is **unchanged in kind and smaller in
  magnitude**: a large delivered-fuel headwind (−369.5 MW) plus a real carbon headwind (−148.2 MW),
  more than offset by a price tailwind (+985.1 MW).

---

## 6. THE PRE-REGISTERED EXPECTATION I GOT WRONG

PREREG §2 G-3R states, in advance: *"the repair raises **every** band's `mc`. The OOM-hours legs must
therefore move **up** (weakly)."* **That is false, and §4's table falsifies it directly.**

The reason is mechanical and I should have seen it from `apply_gas_offer_margin`'s own docstring,
which I read (disclosure E10). The margin term is

    mc[g,t] += markup_hr[g] × (anchor − fuel_price[g,t])

with `anchor = $3.9046/MMBtu`. It is **negative wherever delivered fuel exceeds the anchor** — which
is most of the top decile, and dramatically so in 2025 (top-decile gas ≈ $11.76/MMBtu). The `peak`
band carries the largest `markup_hr`, so it takes the largest reduction: **−$188/MWh** in 2025. Only
where the RGGI charge (≈ $11/MWh at a 0.5 t/MWh rate in 2025) outweighs the compression does the
offer rise, which is what the `committed` band does in all three years.

**Nothing was rescued and no bar was moved.** The prediction was a directional expectation, not a
bar; the gated legs were fixed before measurement and are reported exactly as they landed. But the
error is real, it was avoidable from a docstring I had already read, and the honest statement of
nyiso-181's median-under-statement figure ($9.57 / $15.39 / $11.98) is that it is a **class median**
whose per-band, per-hour composition is **signed** — a fact this finding establishes and the
inherited record did not.

---

## 7. G-S — the 62.4 / 24.6 / 13.0 split. **THE LOAD-BEARING RESULT: `PREMISE-CONFIRMED`.**

2025 top decile by actual RT price. Anchors, on the LP's own `unit_hourly` frame:

| symbol | quantity | published | **repaired** |
|---|---|---|---|
| `M` | measured CAMPD `ST_GAS` MW | 2,596.9 | 2,596.9 *(offer-independent)* |
| `A` | in the money at the **ACTUAL** price | 2,313.3 | **2,448.8** |
| `P` | in the money at the **MODEL'S OWN** price | 1,592.4 | **1,361.7** |
| `D` | model dispatch | 1,441.9 | **1,582.5** *(trap (j) corrected, +140.5 MW)* |

| term | published MW | published share | **repaired MW** | **repaired share** |
|---|---|---|---|---|
| **`T1` model price below actual** (`A − P`) | 721 | 62.4 % | **+1,087.1** | **107.2 %** |
| **`T2` offer position proper** (`M − A`) | 284 | 24.6 % | **+148.1** | **14.6 %** |
| **`T3` un-dispatched at own signal** (`P − D`) | 150 | 13.0 % | **−220.8** | **−21.8 %** |
| **gap `G`** (`M − D`) | 1,155 | 100 % | **1,014.5** | 100 % |

The chain closes exactly (`|ΣT − G| = 0.0`). The shares no longer partition into non-negative
pieces — pre-declared in PREREG §2.4 as a possible and reportable outcome, and it is what happened.

**`T3` refined to matched populations** (the nyiso-181 §5 defect, repaired inside the split):

| piece | MW | reading |
|---|---|---|
| `T3a` un-run **in-the-money** capacity | **+14.1** | the well-formed "capacity in the money that does not run" |
| `T3b` dispatch of **out-of-the-money** bins | **−234.9** | the floors and the commitment bridge |
| `T3a + T3b` | **−220.8** | exact (`|d| = 1.6e-05`) |

**Gates.**

* **G-S1 dominance** — `T1 / G = 1.0717` against the inherited `0.60` bar → **`PRICE-DOMINANT`**.
* **G-S2 plurality** — `|T1| = 1,087.1` > `|T3| = 220.8` > `|T2| = 148.1` → **`PRICE-LARGEST`**.
* **LANE VERDICT: `PREMISE-CONFIRMED`.**

**Pre-declared consequence, executed:** the *"the `ST_GAS` C1 lane and the C3a-2025 lane are ONE
OBJECT"* identification **STANDS on a repaired instrument**; the standing **DO-NOT-OPEN on `ST_GAS`
offer levers STANDS**; the lane **stays blocked** on owner-court C3a-2025
(`DECISION-CARD-nyiso148-2025-level-remainder`, Q1 pending); **the brief's task-2 conditional does
NOT arm and no lever was opened.**

**And the identification is stronger than the record it replaces.** The offer-position component is
not a quarter of the gap — it is a seventh. The price-level component does not explain 62 % of it —
it exceeds 100 % of it, and is offset rather than complemented by the third term. The third term is
not 150 MW of in-the-money capacity failing to run; it is **14 MW** of that (consistent with
nyiso-181's 8 MW mean over all hours) plus **235 MW of out-of-the-money capacity being run** by
mechanisms that are not the offer.

---

## 8. What this does and does not touch in the inherited record

**Re-derived and now superseded (cite these, not the published figures):**

* **The 2025 top-decile split** — **107.2 / 14.6 / −21.8** on a gap of **1,014.5 MW**, not
  62.4 / 24.6 / 13.0 on 1,155 MW. The published figures were computed on an offer missing two armed
  terms **and** on a dispatch anchor short by 140.5 MW (trap (j)).
* **G4's channel table** — the four-channel full-Shapley row of §5 is the current one.
* **G3's leg values** — §4's repaired column. The **verdict** word (`PEAK-EXONERATED`) is unchanged.

**NOT affected:**

* **The keeper, its determination, target grade, fail set and every scored metric.** I1 is
  bit-identical; `metrics.json` is untouched. Nothing was registered (rule 15) because nothing
  non-control was solved.
* **C3a-2025 stays owner-court** in every branch, including this one. What §7 settles is the
  *decomposition*, never the wall.
* **C3c** — SUPPORTING tier, not lone; not opened.
* **Every DO-NOT-REDO cell** (nyiso-178 / 179 / 180 / 181) is untouched and stays closed. §3's I2
  independently re-confirms nyiso-180 §3(a)/(b): the reconstruction matches the LP exactly with no
  delivery factor and no post-solve price transform anywhere in the identity.
* **`R = mo / itm` stays RETIRED.** It is not computed, quoted or repaired anywhere in this session,
  on either basis.
* **`Ω`, the reserve rows and carrier 2.** nyiso-181's one-sided `INCONCLUSIVE` reading stands and is
  **not** an exoneration.

---

## 9. Honest expected value — what is NOT delivered

* **No lever, in any branch, and none was available** — pre-declared in PREREG §3.4 and §5. The
  deliverable is a repaired instrument plus three re-derived numbers.
* **`PREMISE-CONFIRMED` is the branch with the least forward value, and the PREREG said so before
  the measurement.** The lane is exactly as blocked as it was; nothing new is openable.
* **The C1-2023 `ST_GAS` +3.86 TWh gate is not moved and nothing here moves it.** This session
  re-sizes an explanation of a *2025* object; the 2023 object is untouched and still unexplained.
* **`T3b = −234.9 MW` is measured but NOT attributed.** It is *"dispatch of out-of-the-money bins"* —
  the reliability floor, the NYISO gas commitment bridge, or both — and this session does **not**
  decompose it per mechanism. That attribution is real successor work and is named, not implied.
* **The 2 × 2 grid cannot separate a genuine four-channel structure from a partition choice.**
  Assigning the offer margin to FUEL (it is a function of `fuel[g,t]`) is a choice made in the PREREG
  in advance and named as one; full Shapley is exact only for the channels it is given.
* **G-4R's verdict word is not load-bearing** in any cell, because `share_denominator_is_small` is
  true in all four. Only the MW contributions are.
* **nyiso-179's V1, V2, G0, G1 and G2 are OUT OF SCOPE and are not re-claimed.** They were declared
  out of scope in PREREG §3.2 before measurement. G1's `R` is retired rather than repaired.
* **I predicted the sign of the repair wrong** (§6), from a docstring I had already read.
* **Reproducibility cost, inherited and named:** every number here needs the ~15-minute control
  replay plus a `data/clean` regeneration, because `unit_hourly` stays uncommitted at 16–17 MB/yr.

---

## 10. Governance

* **Rule 1 `[R-STRUCT]`** — no residual consulted; nothing adopted or rejected on whether it moved a
  fit. The repair makes the *instrument* faithful, not the score.
* **Rule 13 `[R-MEASURED]`** — nothing pinned to actuals. Every gated quantity is a model-internal LP
  output on the keeper's own recipe; the measured CAMPD anchor `M` enters only as the published
  comparison it always was.
* **Rule 14 `[R-ACCURATE]`** — the whole session: an accurate reconstruction is kept and the record
  that rested on the inaccurate one is re-derived, wherever it lands.
* **Rule 15** — the control replay is bit-identical (I1) and is an **instrument, not a run**; nothing
  registered, correctly. No non-control solve ran.
* **Rule 16 `[R-ALLYEARS]`** — one invocation, all three years from the bundle's own `meta.json`,
  sequential (rule 12).
* **Rule 19 `[R-ONE-MECH]`** — nothing added. §7's `T3b` **names** the mechanisms already doing the
  job and declines to add another.
* **Rules 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — **zero parameters touched, zero swept, nothing
  re-derived from a residual.** The DOF ledger is unchanged.
* **Rule 22 `[R-HOLDOUT]`** — every year is 2023 / 2024 / 2025. NYISO is absent from both `complete`
  and `final`; **no marker was requested**; the spend freeze is untouched.
* **Rule 24 `[R-REGISTRY]`** — **no new tunable**, no env-var knob, no gate flag. The one new
  argument is a probe-local reproducibility switch, not a solve-affecting channel.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only; only the NYISO matrix shard edited.
* **Rule 27 `[R-PUSH]`** — `scripts/probes/nyiso179_st_gas_offer_position.py` (748 → 839 lines) was
  edited **locally** and its pushed blob **verified** (line count + hash) against the local file.
  `src/market_sim/` is untouched.
* **Rule 28 `[R-MECH-MATRIX]`** — §11.

## 11. Matrix (rule 28 b)

NYISO shard only. **No verdict moves.**

* **`unit_network_layer_sidecar` stays `K`**, re-stamped: the `mc` column is used a second time and
  for a new purpose — an **exact basis test of a reconstruction against the LP** (I2), the check
  nyiso-180's P-c could not be — and the `cap_mw`/`mw` columns supply the matched-population repair
  of the split's third term (`T3a` +14.1 / `T3b` −234.9 MW), which no class-level artifact can.
* **`gas_offer_net_revenue_margin` stays `K`**, annotated: it is one of the two terms the
  reconstruction omitted, and §4/§6 measure the **sign structure** of its compression on the LP's own
  offer for the first time (`peak` −$188/MWh in the 2025 top decile, `committed` +$12/MWh).
* **`state_carbon_pricing` stays `K`**, annotated: the other omitted term, and §5 sizes its
  **between-year** contribution at −148.2 MW — larger than the availability channel.
* `offer_curve_by_group`, `ramp_envelopes`, `energy_reserve_coopt` and `dual_fuel_switching` are
  **not re-opened** and their cells are not rewritten.

## 12. Handed forward

1. **CITE THE REPAIRED SPLIT: 107.2 % / 14.6 % / −21.8 % on a 1,014.5 MW gap.** Do not cite
   62.4 / 24.6 / 13.0 again. The premise it supports — *the `ST_GAS` C1 lane and the C3a-2025 lane
   are one object* — **stands and is stronger**; the lane stays blocked and `ST_GAS` offer levers
   stay closed.
2. **`T3b = −234.9 MW` of out-of-the-money `ST_GAS` dispatch in the 2025 top decile is a NEW,
   UNATTRIBUTED object.** It is not the offer, and it is 16× the un-run in-the-money capacity in the
   same hours. Attributing it per mechanism (reliability floor vs `nyiso_gas_commitment_bridge`) is
   D-2 work on committed `legitimacy_diagnostics.json` rows plus this instrument, and is the natural
   successor. **It is a diagnostic, not a lever**: rule 19 says enumerate before adding, and this is
   the enumeration.
3. **`build_year()` IS NOW SAFE TO REUSE** — its default is the repaired offer, verified to the LP at
   `max|d| ≈ 3e-05` from a fresh instrument. The legacy path is preserved behind an explicit flag and
   `main()` is pinned to it, so the published nyiso-179 artifact stays reproducible.
4. **THE CROSS-ISO AUDIT IS STILL OPEN and is still not NYISO's** (nyiso-181 §11 item 4). §6 adds a
   second limb to the defect class: it is not only *omitting a term the runner installs*, it is
   omitting one whose sign is **not constant** — so a sanity check on a class median can miss it
   entirely. CAISO and NEISO carry state carbon programs; `gas_offer_net_revenue_margin` is armed
   more widely still. Rule 25 keeps it out of this session.
5. **UNCHANGED and not opened:** C3c (SUPPORTING, not lone); C3a-2025 (owner-court); the
   measured-availability family, the merit guard, an `ST_GAS` duty curve, `gas_st_startup_cost`,
   `gas_st_committed_hr_mult`; `ramp_envelopes` as dominant carrier; the loss surface; the
   post-solve transform; the capacity/label-basis mismatch.
6. **The C1-2023 `ST_GAS` object remains open and unexplained.**
