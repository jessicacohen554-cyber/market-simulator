# FINDING — caiso-148 `nuclear_unit_availability` for CAISO

**Session:** caiso-148, 2026-07-31. **Lever:** mechanism-matrix §5.2 CAISO queue
**item 8**, `nuclear_unit_availability` (cells `KUUUKU` at entry; `K` in ERCOT on
its own flag/file, `K` in NYISO at nyiso-98, CAISO `U`).

**Pre-registration:** `PREREG-caiso148-nuclear-availability-2026-07-31.md`,
committed and pushed **before either arm solved**.

**Base keeper:** `2026-07-31-caiso147-chp-heat-rates`,
CALIBRATED-WITH-CAVEATS, 0 FAILs, 2 ledgered non-protective caveats, 1 of 3
slots free, protective 0/1. CAISO holds **no** rule-22 calibration-complete
marker; this session solved **2023 2024 2025 only** and wrote no marker.

**Rule 25 `[R-ISO-SCOPE]` up front:** ERCOT's and NYISO's `K` verdicts transfer
**nothing**. Everything below is derived from CAISO's own reactors and CAISO's
own market data. The only thing inherited is the deriver's frozen constants
(rule 23 `[R-FROZEN-DERIVE]`).

---

## §A — the ex-ante wall check: NOT walled

The handoff required this be settled first, because queue item 5
(`unit_outage_short_windows`) was adjudicated INERT ex ante at caiso-136 on a
**coal-only CEMS detector** meeting a **CEMS-invisible** CAISO coal class. If
item 8 shared that detector it would have been adjudicated `I` the same way,
costing no solve.

**It does not, and the two share no input.** `unit_outage_short_windows` reads
CAMPD/CEMS. `nuclear_unit_availability` reads the **NRC daily Power Reactor
Status Report** (`data/raw/nrc-reactor-status/<YYYY>PowerStatus.txt`,
`ReportDt|Unit|Power`, `Power` = percent of licensed thermal power at the morning
report; US-government public domain, fetched by
`scripts/data/fetch_nrc_reactor_status.py`). **Nuclear units carry no CO₂ and are
not CEMS reporters in any ISO**, so CEMS visibility is structurally irrelevant to
this lever everywhere. caiso-136 has no bearing on item 8.

---

## §B — the derive (STEP 1, no LP)

`scripts/data/derive_nuclear_availability.py --iso CAISO` →
`data/raw/nuclear-availability-CAISO.csv`.

**No source change was needed to arm CAISO.** The application seam
(`data/fleet/arrays.py`, the `_iso != "ERCOT"` block) and the loader
(`data.outages.nuclear_unit_availability_series`) were already ISO-generic. The
session's only code delta is a **two-row identifier crosswalk** in `NRC_TO_EIA`:

```
"CAISO": {"Diablo Canyon 1": (6099, 1), "Diablo Canyon 2": (6099, 2)}
```

That is an identifier map, not a tunable (rule 24 `[R-REGISTRY]`). **Zero fitted
scalars** — `EVENT_RAW_MAX = 0.90`, `SCALE_CLIP = 1.25`, `WEDGE_TOL = 0.01` are
inherited frozen and untouched.

**Unit rows.** 1,886 rows / **2 reactors** — Diablo Canyon 1 (EIA `6099_1`,
1,122 MW) and 2 (`6099_2`, 1,118 MW), both zone NP15, fleet 2,240 MW. That is
**100 % of CAISO's nuclear capacity and unit count**; SONGS 2/3 retired 2013 and
Rancho Seco 1989, and neither carries an NRC row nor a model fleet unit. NRC
reports both reactors on **365 / 366 / 365** days — no source gaps.

**Windows found: 18** in the covered extract (`avail_raw < 0.90`), three of them
major refuels:

| reactor | window | days | mean raw |
|---|---|---|---|
| DCPP-1 | 2023-09-27 → 2023-11-17 | 52 | 0.102 |
| DCPP-2 | 2024-04-07 → 2024-05-25 | 49 | 0.038 |
| DCPP-2 | 2025-10-05 → 2025-10-31 | 27 | 0.000 |
| DCPP-2 | 2025-08-05 → 2025-08-15 | 11 | 0.476 |
| DCPP-1 | 2023-12-09 → 2023-12-17 | 9 | 0.022 |
| DCPP-1 | 2023-03-13 → 2023-03-20 | 8 | 0.568 |
| DCPP-2 | 2023-11-10 → 2023-11-17 | 8 | 0.519 |
| DCPP-2 | 2025-03-11 → 2025-03-15 | 5 | 0.512 |
| + 10 shorter (1–3 d) | | | trips / grid-related reductions |

**Coverage: 2023 365/365 (100 %), 2024 366/366 (100 %), 2025 212/365 (58.1 %)**;
**31 of 36 months**, 1,886 of 2,192 reactor-days (86.0 %).

### B.1 — the five dropped months, and why the drop is CORRECT

All five are 2025 (Apr, May, Jul, Nov, Dec) and the selection is **systematic,
not random**: each is a month containing a *real event* (refuel, trip or ramp)
whose **non-event pool is already saturated at 100 %**, so the capped fixed-point
cannot scale **up** to reach the anchor. Worked example, 2025-07: DCPP-1 at 100 %
all 31 days, DCPP-2 at 55 % on Jul 5–6 and 100 % otherwise → fleet 0.98554
against an anchor of 1.00; the two event days are held as measured and every pool
day is already at the 1.0 cap, so the maximum achievable is 1.45 % below anchor.

**This session measured the cause rather than assuming it.** EIA-930 CISO
`NG: NUC` peaks at **2,281 / 2,279 / 2,309 MW** against the model's 2,240 MW
EIA-860 nameplate — Diablo runs up to **+3.1 % above nameplate**, so a full-power
month's EIA-923 ratio (net generation ÷ nameplate × hours, **clipped at 1.0** per
the constants' own construction) hits the clip, and NRC-%thermal × nameplate can
never express it. Posting the NRC level in those months would **delete real
capability**. The deriver drops them, the loader NaNs them, and the smear stands
— rule 14 `[R-ACCURATE]`'s misalignment clause operating exactly as designed.

**Consequence, accepted in advance and not engineered around:** in 2025 the U1
Apr–May refuel, the Jul U2 derate and the Dec U1 trip keep the smear; only the
**October U2 refuel** carries measured timing. 2023 and 2024 are fully covered.
This was stated in the pre-registration §2 before either arm solved.

### B.2 — independent-source validation

Validated against **EIA-930 CISO metered hourly nuclear** — a source independent
of both NRC (the timing input) and EIA-923 (the level anchor).

NRC-derived available MW vs EIA-930 metered daily mean, 942 fully-covered days:
**r_day 0.9807** overall (0.9708 / 0.9918 / 0.9876), bias **−1.8 / +13.7 /
+20.0 MW** on a 2,240 MW fleet (≤ 0.9 %), MAE 43.2 / 28.7 / 36.2 MW (1.3–1.9 %).

**The nyiso-98 EIA-930 zero-block artifact was screened for and does NOT occur in
CISO**: 23 exact-zero hours in 2023 (25 hours < 50 MW), **0** in 2024 and 2025 —
against NYISO's 1,179 / 380 / 117. CISO `NG: NUC` is therefore usable directly as
an independent check, and nyiso-98's gap-masking step is not needed here. This is
a CAISO-specific determination; it says nothing about any other ISO's 930 series.

### B.3 — build-time gates (the nyiso-98 set), all PASS

| gate | test | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|---|
| **G1** | raw-NRC r_day lift ≥ +0.10 | +0.1836 | +0.1447 | +0.1327 | PASS |
| **G2** | reconciled retention of raw lift ≥ 70 % | 100.1 % | 100.2 % | 100.1 % | PASS |
| **G3** | annual \|ΔTWh\| < 0.5 % | 0.0001 % | 0.0239 % | 0.0746 % | PASS |

Overlay vs smear against metered, on covered days: r_day **0.7873 → 0.9709**,
**0.8474 → 0.9921**, **0.8550 → 0.9878**; MAE **156.4 → 47.2**, **100.7 → 31.3**,
**125.0 → 39.9 MW**.

### B.4 — regression (rule 25)

`--check` reproduces `nuclear-availability-PJM.csv` and
`nuclear-availability-NYISO.csv` **byte-for-byte** after the CAISO addition. No
other ISO's artifact moves.

---

## §C — the reserve-requirement framing, CORRECTED before it could be quoted

The handoff framed Diablo as "the 2,240 MW MSSC that sets CAISO's ENTIRE reserve
requirement … it moves the reserve floor for the whole ISO." **That is not how
the keeper is wired**, and this finding does not claim it. Verified in
`caiso147_chp_B/run_config.json`:

- `energy_reserve_coopt = False`, `caiso_reserve_coopt = False` — the reserve
  co-optimization is **not armed**, consistent with caiso-144's `I` /
  DO-NOT-SOLVE adjudication.
- `as_reserve_formula = False` — the `max(MSSC, 0.067×load)` withholding formula,
  the one place a live MSSC would enter the LP, is **off**.
- `caiso_scarcity_pricing = True`, but its MCL is a **static 1,400 MW tariff
  constant**, not keyed to Diablo's hourly availability.

**There is no dynamic MSSC channel in this A/B.** The live channels are:

1. **Primary — within-month daily re-timing** of nuclear availability, displacing
   energy on and off the marginal classes.
2. **Secondary — the `caiso_scarcity_pricing` overlay's `reserve_headroom`.**
   Nuclear contributes ~0 to either reserve tier itself (at pmax it has no
   headroom; out, it is a cold slow-start unit backing neither tier), but the
   *displaced* energy loads gas units higher, cutting their headroom and raising
   the LOLP adder. Second-order.

**Binding on successors:** do not cite caiso-148 as evidence about CAISO's
reserve floor or MSSC. It tested neither.

---

## §D — the "0 reactors" log line is NOT a defect (diagnosed, not left open)

Arm B's log contains two overlay lines per year:

```
CAISO nuclear unit-availability overlay (2023): 0 reactor(s) ...
CAISO nuclear unit-availability overlay (2023): 2 reactor(s) ...
```

The `0` comes from `assembly.bins_to_fleet` (lines 96–1111), which builds
`FleetArrays` for the **CAMPD-binned thermal fleet only** — that fleet contains
no nuclear by construction, because for non-ERCOT ISOs nuclear joins later
through `build_base_fleet`'s `non_thermal` list. The `2` is the dispatch fleet
build at `runner.py:1118`, which is the one the LP consumes. **The mechanism is
correctly armed.** The duplicate line is pre-existing, ISO-generic log noise
(PJM and NYISO emit it identically) and was not changed here.

---

## §E — the A/B

Two single-flag replays of the caiso-147 keeper at the same HEAD, `--year 2023
2024 2025` in one invocation each (rule 16), run concurrently (rule 12):

| arm | bundle | run id |
|---|---|---|
| A (control) | `caiso148_control_A` | `2026-07-31-caiso148-control-zerodelta` |
| B (arm) | `caiso148_nucavail_B` | `2026-07-31-caiso148-nuclear-availability` |

Environment conditions are symmetric across arms (identical warning counts:
7 capacity-deliverability, 4 hydro-modes), so the delta is the flag alone.

### E.0 — the control reproduces caiso-147 BIT-EXACTLY (carried item resolved)

The **keeper-reproducibility drift** carried as an open item since caiso-146 —
the caiso-139 keeper's committed sidecars diverging up to 3.2 GW on a class-hour
at HEAD — **does not affect the caiso-147 keeper**:

| year | max \|class-hour\| control − committed keeper | CA λ keeper → control |
|---|---|---|
| 2023 | **0.000 MW** | $55.7916 → $55.7916 |
| 2024 | **0.000 MW** | $37.4222 → $37.4222 |
| 2025 | **0.000 MW** | $38.2331 → $38.2331 |

caiso-147's re-basing onto HEAD closed it **for CAISO**. The program-wide
charter is unaffected — this is a CAISO observation, not a general resolution.

### E.1 — pre-registered REJECT checks (§5): all clear

- **R1/R2** — the extract reproduces on `--check`; PJM and NYISO reproduce
  byte-for-byte. No cross-ISO contamination.
- **R3 (inertness)** — **PASS, the overlay binds.** Hours moving > 1 MW:
  **4,368 / 3,672 / 2,232**; max \|Δ\| **1,075 / 893 / 963 MW**.
- **R4 (level escape)** — **PASS.** Annual nuclear energy moves
  **+0.0001 % / −0.0240 % / −0.0445 %** (17.6263→17.6263, 18.1972→18.1929,
  17.4924→17.4847 TWh) against a 0.5 % gate. **The G3 gate holds in-solve**, so
  the overlay posts *timing*, not a level.
- **R5** — no dropped month is resurrected; uncovered dates keep the smear.

### E.2 — S2: the mechanism does what it was armed to do

Nuclear dispatch r_day against **EIA-930 CISO metered**, covered days only:

| year | days | r_day control → arm | lift | MAE control → arm |
|---|---|---|---|---|
| 2023 | 365 | 0.7873 → **0.9709** | **+0.1836** | 156.4 → **47.2 MW** |
| 2024 | 364 | 0.8473 → **0.9921** | **+0.1448** | 101.0 → **31.3 MW** |
| 2025 | 212 | 0.8550 → **0.9878** | **+0.1327** | 125.0 → **39.9 MW** |

This matches the extract's ex-ante prediction (§B.3) **to four decimals** in all
three years. Note the control's r_day is *exactly* the smear's own r_day — the
model dispatches nuclear at availability, which is what makes the test
well-posed.

### E.3 — where the displaced energy goes

Annual class energy delta (arm − control), GWh:

| year | CC_REGULAR | import | CT_PEAKER | other |
|---|---|---|---|---|
| 2023 | **−85.6** | +36.0 | +46.1 | solar +2.4, ST_GAS +2.3 |
| 2024 | **−35.8** | +31.7 | +2.7 | hydro +7.8, ST_GAS −2.1 |
| 2025 | −13.8 | **+16.4** | +6.0 | solar −4.7, hydro −1.6 |

Small, and it lands on the marginal classes. **This is NOT the
imports-dominated signature nyiso-98 measured**, and the difference is
structural rather than contradictory: NYISO swings a 4-reactor pool in and out,
while CAISO's 2-unit fleet mostly *re-times within a month* at constant monthly
energy.

System demand-weighted price: **+$0.015 / −$0.036 / +$0.018 per MWh**, p99
essentially unchanged (148.18→148.14, 76.48→76.48, 62.18→62.26); **3,261 /
1,897 / 1,835** hours repriced. Well inside the pre-registered "< $0.50/MWh".

### E.4 — criterion verdicts: identical, arm for arm

Scored **unattested on both** first (the caiso-146/147 probe posture):

| criterion | control | arm |
|---|---|---|
| C1 `fuelmix` | PASS | PASS |
| C2 `sysvol` | PASS | PASS |
| C3a `price_mean` | FAIL | FAIL |
| C3b `price_shape` | PASS | PASS |
| C3c `price_tail` | FAIL | FAIL |
| C4 `dispatch_corr` | PASS | PASS |
| C6 `governance` | UNATTESTED | UNATTESTED |
| C7 `shape` | PASS | PASS |
| C8 `forced_share` | PASS | PASS |

**Every verdict is unchanged.** With arm B's attestation applied (the owner's
caiso-145 ledger carried forward, magnitudes re-measured), C3a/C3c become
`CAVEAT` and C6 `PASS` → determination **CALIBRATED-WITH-CAVEATS, 0 FAILs, C1
all 12/12 · free 8/8**, still **2 of 3** ledgered slots and **0 of 1**
protective.

### E.5 — protective gates, on the ABSORBING classes

Nuclear is exempt from **both** C7 and C8 by explicit class list, so **no
nuclear D-1/D-2 number is quoted here as a passed gate** (caiso-147 §G framing).

**C7 / D-1, CT_PEAKER** (floor 0.80) — holds, and the most exposed year improves:

| year | profile_r control → arm | cv_ratio control → arm |
|---|---|---|
| 2023 | 0.881 → 0.881 | 1.623 → 1.684 |
| 2024 | 0.934 → 0.933 | 1.817 → 1.814 |
| 2025 | 0.864 → **0.866** | 2.178 → 2.175 |

**C8 / D-2, CT_PEAKER** forced share (0.15 peaker cap): 0.0016 → 0.0015,
0.0054 → 0.0059, 0.0007 → 0.0007.

**ST_GAS 2024/2025 raw D-1 rows read `FAIL` in BOTH arms identically** (0.229 →
0.231, −0.031 → −0.034). Pre-existing, not caused by this lever, and below the
rubric's 2 % materiality floor — which is why C7 scores PASS on both sides. This
is reported rather than buried, and it is **not** a caiso-148 finding.

### E.6 — materiality (prereg §7)

C3a: **+3.0 → +3.0 %**, **+8.2 → +8.1 %**, **+11.2 → +11.2 %** — max **0.1 pp**
against the pre-registered **1.0 pp** trigger. CA load-weighted λ moves
$55.7916→$55.8026, $37.4222→$37.3871, $38.2331→$38.2506. **Trigger did not
fire**, so no leave-one-year-out re-scoring was required.

C3c: **bit-identical** — model 0 h vs RT actual 47/35/8 h in both arms. An
energy-neutral within-month re-arrangement cannot create a tail, exactly as
pre-registered.

---

## §F — verdict: **KEEPER**, promoted 2026-07-31

`nuclear_unit_availability` CAISO cell **`U` → `K`**; keeper
`2026-07-31-caiso147-chp-heat-rates` → **`2026-07-31-caiso148-nuclear-availability`**.

The case is structural, not residual-driven. It is a rule-14 `[R-ACCURATE]`
measured-input swap with **zero fitted parameters**, covering **100 % of CAISO's
nuclear capacity and unit count**, validated against an **independent** source at
r_day 0.9807, clearing every build-time and in-solve gate that was fixed in
advance — and it **closes S2 in every year** while leaving every criterion
verdict unchanged and *improving* the binding protective gate's most exposed
number. The residual barely moved (max C3a 0.1 pp), which is the expected result
for an energy-neutral timing correction and is **not** the reason for promotion.

**What it is not:** not a C3a lever, not a C3c lever, not a reserve/MSSC test
(§C). It closes neither ledgered caveat and was not selected to.

---

## §G — DO-NOT-REDO (binding on successors)

1. **Do NOT re-derive `nuclear-availability-CAISO.csv` against a residual**
   (rule 23 `[R-FROZEN-DERIVE]`). It re-derives **only** when NRC publishes a new
   year or EIA-923 revises the anchor, and the commit **must cite the data
   change**. The deriver's `EVENT_RAW_MAX` / `SCALE_CLIP` / `WEDGE_TOL` are
   frozen from ERCOT — do not re-tune them for CAISO.
2. **Do NOT "fix" the five dropped 2025 months by loosening `WEDGE_TOL`,
   raising `SCALE_CLIP`, or letting the per-day cap exceed 1.0.** The drop is
   correct (§B.1). Every one of those knobs would post an availability level the
   EIA-923 basis is known to under-express, deleting real capability to buy
   coverage. The **only** admissible fix is item 3.
3. **The real open item is a Diablo nameplate/uprate basis reconciliation** —
   EIA-860 net summer capacity (2,240 MW) vs licensed thermal power, where
   EIA-930 measures the unit reaching 2,309 MW. That is a **fleet-representation**
   change, not a calibration lever, and it is out of scope for a calibration
   session. It would recover 2025 coverage *and* is the honest fix. Anyone
   opening it should treat it as a fleet/data charter, and note it likely
   touches other ISOs' uprated units too.
4. **Do NOT cite caiso-148 as evidence about CAISO's reserve floor, MSSC, or
   scarcity requirement** (§C). The keeper runs `energy_reserve_coopt`,
   `caiso_reserve_coopt` and `as_reserve_formula` all `False`, and
   `caiso_scarcity_pricing`'s MCL is a static 1,400 MW tariff constant. This
   session tested **no** reserve mechanism. The handoff's framing was checked and
   found not to hold for this keeper.
5. **Do NOT re-open the "0 reactor(s)" log line as a defect** (§D). It is
   `bins_to_fleet` correctly reporting no nuclear in the binned *thermal* fleet;
   the dispatch fleet gets 2. Pre-existing, ISO-generic, cosmetic.
6. **Do NOT quote a nuclear D-1/D-2 number as a passed gate** — nuclear is in
   `D2_EXEMPT_CLASSES` and absent from `D1_GATED_CLASSES`, exempt by **explicit
   class list**, not by the 2 % materiality floor (the caiso-147 §G framing,
   which this session re-confirms for nuclear).
7. **Do NOT attribute the ST_GAS 2024/2025 D-1 FAILs to this lever.** They are
   identical in both arms and pre-date it (§E.5).
8. **Do NOT treat the EIA-930 CISO screen as transferable.** That CISO carries
   no zero-block artifact is a **CAISO-specific** measurement; it says nothing
   about any other ISO's 930 series, and nyiso-98's gap-masking remains correct
   for NYISO.
9. **The verdict transfers to no other ISO** (rule 25). MISO and NEISO cells stay
   `U`; PJM stays `U` on its own build-time refusal (negative G2 retention). Each
   must derive its own artifact and clear its own gates.
10. Everything carried in `FINDING-caiso147` §G, `FINDING-caiso146` §G,
    `FINDING-caiso144` §G, caiso-143 §H, caiso-142 §K, caiso-141, caiso-138 §G,
    caiso-137b §6, caiso-131 §10 remains binding and is **not** re-litigated here.

**Also carried forward unchanged** (not this session's scope, not resolved by
it): the latent CHP derive defect in PJM (caiso-147 §B); CT_CHP's thin and
adversely-selected CAISO coverage; the shared-derive sub-6.0 MMBtu/MWh meter bug
across all four measured ISOs. The **keeper-reproducibility drift** is resolved
*for CAISO only* (§E.0) — the program-wide charter still stands.

