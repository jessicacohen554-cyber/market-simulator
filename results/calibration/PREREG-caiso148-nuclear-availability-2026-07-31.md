# PRE-REGISTRATION — caiso-148 `nuclear_unit_availability` for CAISO (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document does
not contain cannot be quoted as a pass. Format mirrors
`PREREG-caiso147-chp-heat-rates-2026-07-31.md` and
`docs/PREREG-nyiso98-nuclear-availability-2026-07-29.md`, not copied.

Lever: mechanism-matrix §5.2 CAISO queue **item 8**, `nuclear_unit_availability`,
cells `KUUUKU` (`K` in ERCOT on its own flag/file, `K` in NYISO at nyiso-98;
CAISO `U`). Rule 25 `[R-ISO-SCOPE]`: **no verdict transfers** — CAISO derives its
own artifact from CAISO's own reactors, and this document scores CAISO on
CAISO's evidence alone. ERCOT's and NYISO's `K` contribute nothing but the
frozen deriver constants (rule 23 `[R-FROZEN-DERIVE]`).

**Promotion is NOT pre-granted** and is not requested in advance by this
document. It remains a separate act, and (rule 22 `[R-HOLDOUT]`) a structural
mechanism change is scored leave-one-year-out within 2023–2025 before promotion.

Base keeper: `2026-07-31-caiso147-chp-heat-rates`, determination
CALIBRATED-WITH-CAVEATS, 0 FAILs, 2 ledgered non-protective caveats (C3a-2025 on
the caiso-141 A2 water wall, C3c-2023/24 on caiso-131 A4) carried from the
owner's caiso-145 disposition, 1 of 3 slots free, protective 0/1. CAISO holds
**no** rule-22 calibration-complete marker — this session solves
**2023 2024 2025 only** and writes no marker.

---

## §0 — the ex-ante wall check the handoff ordered, and its result: NOT WALLED

The handoff required this be settled before anything else, because queue item 5
(`unit_outage_short_windows`) was adjudicated INERT ex ante at caiso-136 on a
**coal-only detector** meeting a **CEMS-invisible** CAISO coal class. The
question was whether item 8 shares that detector.

**It does not, and the two mechanisms share no input.** `unit_outage_short_windows`
reads CAMPD/CEMS. `nuclear_unit_availability` reads the **NRC daily Power Reactor
Status Report** (`data/raw/nrc-reactor-status/<YYYY>PowerStatus.txt`,
`ReportDt|Unit|Power`, `Power` = percent of licensed thermal power at the morning
report; US-government public domain, fetched by
`scripts/data/fetch_nrc_reactor_status.py` from
<https://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/>).
Nuclear units carry no CO₂ and are not CEMS reporters at all, so CEMS visibility
is irrelevant to this lever in **every** ISO. The caiso-136 adjudication has no
bearing on item 8, and the cell stays live.

---

## §1 — the delta, exactly

`ScenarioConfig.nuclear_unit_availability: False → True` for CAISO. **One
existing field, one flag, no new mechanism** (rule 19 `[R-ONE-MECH]`; nothing is
stacked). Both arms are replays of the caiso-147 keeper config at the same HEAD;
the control is a **zero-delta replay solved in this session**, *not* the keeper's
committed bytes (caiso-146 measured the caiso-139 keeper drifting up to 3.2 GW on
a class-hour at HEAD, so committed bytes are not a clean baseline).

**No source change was needed to arm CAISO.** The application seam
(`data/fleet/arrays.py`, the `_iso != "ERCOT"` block) and the loader
(`data.outages.nuclear_unit_availability_series`) are already ISO-generic. This
session's only code change is a **crosswalk entry** — two rows added to
`NRC_TO_EIA` in `scripts/data/derive_nuclear_availability.py` mapping the NRC
unit names to the model's EIA keys:

```
"CAISO": {"Diablo Canyon 1": (6099, 1), "Diablo Canyon 2": (6099, 2)}
```

That is an identifier crosswalk, not a tunable (rule 24 `[R-REGISTRY]`). **Zero
fitted scalars**: `EVENT_RAW_MAX = 0.90`, `SCALE_CLIP = 1.25`, `WEDGE_TOL = 0.01`
are inherited frozen from the ERCOT deriver and are **not** touched here
(rule 23 `[R-FROZEN-DERIVE]`).

**What it replaces.** Today CAISO nuclear availability is
`NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"]` — the measured EIA-923 monthly fleet
energy, but **smeared uniformly across both reactors and every hour of the
month**. The overlay keeps that monthly *level* (the anchor owns the level) and
replaces the *timing* inside the month with the measured per-reactor daily state
(NRC owns the timing). Uncovered dates are `NaN` and keep the smear.

**Admissibility (rule 13 `[R-MEASURED]`).** A reactor power state / refuel window
is a physical availability event — the same class as the CAMPD fossil outage
windows and the ERCOT/NYISO nuclear overlays. It is an *input*, not an outcome:
it is produced forward by the static `NUCLEAR_MONTHLY_CF` + refuel-block
scheduling, and it responds to changed conditions. Nothing here is keyed to a
price or volume residual.

---

## §2 — STEP 1 derive report (no LP), as ordered before arming

`scripts/data/derive_nuclear_availability.py --iso CAISO` →
`data/raw/nuclear-availability-CAISO.csv`.

**Unit rows.** 1,886 rows / **2 reactors** — Diablo Canyon 1 (EIA 6099_1,
1,122 MW) and Diablo Canyon 2 (6099_2, 1,118 MW), both zone NP15, fleet
2,240 MW. That is **100 % of CAISO's nuclear capacity and unit count**: SONGS 2/3
retired 2013 and Rancho Seco 1989; neither carries an NRC row nor a model fleet
unit. NRC reports Diablo 1 and 2 on **365 / 366 / 365 days** in 2023 / 2024 /
2025 — no source gaps.

**Windows found (18 in the covered extract, `avail_raw < 0.90`).** Three are
major refuels; the rest are trips, coast-downs and deep derates:

| reactor | window | days | mean raw | note |
|---|---|---|---|---|
| DCPP-1 | 2023-09-27 → 2023-11-17 | 52 | 0.102 | refuel (shallow coast-down late Sep, deep Oct–Nov) |
| DCPP-2 | 2024-04-07 → 2024-05-25 | 49 | 0.038 | refuel |
| DCPP-2 | 2025-10-05 → 2025-10-31 | 27 | 0.000 | refuel |
| DCPP-1 | 2023-12-09 → 2023-12-17 | 9 | 0.022 | outage |
| DCPP-2 | 2025-08-05 → 2025-08-15 | 11 | 0.476 | derate |
| DCPP-1 | 2023-03-13 → 2023-03-20 | 8 | 0.568 | derate |
| DCPP-2 | 2023-11-10 → 2023-11-17 | 8 | 0.519 | derate |
| DCPP-2 | 2025-03-11 → 2025-03-15 | 5 | 0.512 | derate |
| + 10 shorter (1–3 d) | | | | trips / grid-related reductions |

**Provenance.** NRC daily Power Reactor Status (timing) × EIA-923 monthly net
generation via `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"]` (level). Both are measured,
citable, and forward-reproducible.

**Coverage.** 2023 **365/365 days (100 %)**, 2024 **366/366 (100 %)**, 2025
**212/365 (58.1 %)**; **31 of 36 months** kept, 1,886 of 2,192 reactor-days
(86.0 %).

**The five dropped months are all 2025 — Apr, May, Jul, Nov, Dec — and the drop
is systematic, not random.** All five are months containing a *real event*
(refuel, trip or ramp) in which the non-event pool is already saturated at 100 %,
so the capped fixed-point cannot scale **up** to reach the anchor. The cause is
the deriver's documented **thermal-vs-net wedge**, and this session **measured it
directly**: EIA-930 CISO `NG: NUC` peaks at **2,281 / 2,279 / 2,309 MW** in
2023/24/25 against the model's 2,240 MW EIA-860 nameplate — Diablo runs up to
**+3.1 % above nameplate**, so a full-power month's EIA-923 ratio clips at 1.0
and NRC-%thermal × nameplate can never express it. Posting the NRC level in those
months would *delete real capability*; the deriver correctly drops them and the
smear (the anchor itself) stands. This is rule 14 `[R-ACCURATE]`'s misalignment
clause operating as designed, **not** a fit choice.

**Consequence, stated plainly and accepted in advance:** in 2025 the U1 Apr–May
refuel, the Jul U2 derate and the Dec U1 trip keep the smear. Only the **October
U2 refuel** carries measured timing in 2025. 2023 and 2024 are fully covered.

**Comparison to what the model currently assumes** (overlay vs smear, both scored
against **EIA-930 CISO metered hourly nuclear** — a source independent of both):

| year | covered days | r_day smear | r_day overlay | lift | MAE smear → overlay |
|---|---|---|---|---|---|
| 2023 | 365 | 0.7873 | **0.9709** | **+0.1836** | 156.4 → 47.2 MW |
| 2024 | 365 | 0.8474 | **0.9921** | **+0.1447** | 100.7 → 31.3 MW |
| 2025 | 212 | 0.8550 | **0.9878** | **+0.1327** | 125.0 → 39.9 MW |

**Independent-source validation.** NRC-derived available MW vs EIA-930 metered
daily-mean MW over 942 fully-covered days: **r_day 0.9807** overall (0.9708 /
0.9918 / 0.9876), bias **−1.8 / +13.7 / +20.0 MW** on a 2,240 MW fleet (≤ 0.9 %),
MAE 43.2 / 28.7 / 36.2 MW (1.3–1.9 %). **The nyiso-98 EIA-930 zero-block artifact
does NOT occur in CISO** and was screened for explicitly: 23 exact-zero hours in
2023 (25 hours < 50 MW), **0** in 2024 and 2025 — versus NYISO's 1,179 / 380 /
117. CISO `NG: NUC` is usable as an independent check here; the nyiso-98
gap-masking step is not needed.

**Build-time gates (the nyiso-98 set), all PASS:**

- **G1** raw-NRC lift ≥ +0.10 → **+0.184 / +0.145 / +0.133** ✅
- **G2** reconciled retention of the raw lift ≥ 70 % → **100.1 / 100.2 / 100.1 %** ✅
- **G3** max annual |ΔTWh| < 0.5 % → **0.0001 / 0.0239 / 0.0746 %** ✅

**Regression (rule 25).** `--check` reproduces `nuclear-availability-PJM.csv` and
`nuclear-availability-NYISO.csv` **byte-for-byte** after the CAISO addition. No
other ISO's artifact moves.

**Incidental finding, recorded not acted on.** `NUCLEAR_MONTHLY_CF_BY_YEAR`'s
CAISO comment attributes the 2023 Oct–Dec dip to **U2** and the 2024 Apr–May dip
to **U1**; NRC says the opposite (2023 = **DCPP-1**, 2024 = **DCPP-2**). The
anchor is fleet-level so no number changes — but it is exactly the unit-level
detail the smear cannot carry. Comment correction only; **no constant is
re-derived** (rule 23).

---

## §3 — the reserve-requirement framing, corrected before it is quoted

The handoff frames Diablo as "the 2,240 MW MSSC that sets CAISO's ENTIRE reserve
requirement … it moves the reserve floor for the whole ISO." **That is not how
the keeper is wired, and this document will not claim it.** Verified in
`caiso147_chp_B/run_config.json`:

- `energy_reserve_coopt = False`, `caiso_reserve_coopt = False` — the reserve
  co-optimization is **not armed** (consistent with caiso-144's `I`/DO-NOT-SOLVE
  adjudication).
- `as_reserve_formula = False` — the `max(MSSC, 0.067×load)` withholding
  formula, the one place a live MSSC would enter, is **off**.
- `caiso_scarcity_pricing = True`, and its MCL is a **static tariff constant
  (1,400 MW)**, not keyed to Diablo's hourly availability.

So there is **no dynamic MSSC channel in this A/B**. Two channels are live:

1. **Primary — within-month daily re-timing of nuclear availability**, displacing
   energy on/off the marginal classes. This is the mechanism.
2. **Secondary — the `caiso_scarcity_pricing` overlay's `reserve_headroom`.**
   Nuclear itself contributes ~0 to either tier (at pmax it has no headroom; out,
   it is a cold slow-start unit and backs neither tier), but the *displaced*
   energy loads gas units higher, cutting their headroom and raising the LOLP
   adder. Second-order and unbudgeted.

A successor must not cite this session as evidence about the reserve floor.

---

## §4 — expected direction and magnitude (pre-registered)

The overlay is **level-neutral by construction** and a **pure timing
re-arrangement**. From the extract, before any solve:

- **Nuclear annual energy: |Δ| < 0.1 %** (extract predicts +0.0001 / −0.0239 /
  −0.0746 %). Direction: none.
- **Daily available-MW delta (overlay − smear): mean ≈ 0** (+0.0 / −0.5 /
  −1.5 MW), but **p05/p95 of −440/+373, −279/+113, −378/+204 MW**, min/max
  **−1,075 / +963 MW**. **254 covered days** carry |Δ| > 100 MW, **51 days**
  > 500 MW, **1 day** > 1,000 MW.
- **Largest negatives** (model *loses* nuclear vs smear): 2023-01-06 −1,075 MW
  (both units at ~48 % on one January day the smear books at 0.96); 2023-11-11→14
  −941…−975 MW; 2023-12-09→13 −745 MW.
- **Largest positives** (model *gains* nuclear): 2025-10-01→04 **+963 MW** and
  2024-04-01→04 **+893 MW** — the signature smear defect, a refuel starting
  mid-month pre-booked from day 1.
- **Prices:** annual mean λ change **small, < $0.50/MWh**, sign not predicted;
  individual hours repriced in both directions. Displacement expected to land on
  CC_REGULAR (marginal in most CAISO hours), CT_PEAKER and imports.
- **In-solve S2 check:** the arm's nuclear dispatch r_day against EIA-930 should
  rise from the control's ≈0.79 / 0.85 / 0.86 toward the extract's 0.97 / 0.99 /
  0.99 on covered days. 2025 will land short of that because 5 months keep the
  smear; that is expected, not a miss.

---

## §5 — what makes this a REJECT

Rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]` bind: **a worse backcast on an
accurate measured input is a DISCOVERED BUG, not a reject.** If a criterion
degrades and the cause is genuine re-timing, the input **stays in** and the root
cause is opened. The REJECT criteria below are therefore structural and
provenance-based only:

- **R1** — the extract does not reproduce byte-for-byte on re-run (`--check`).
- **R2** — the PJM or NYISO extract changes (cross-ISO contamination, rule 25).
- **R3** — the overlay is **inert or mis-wired**: the arm's nuclear dispatch is
  byte-identical to the control in a year that holds covered event windows, or
  its r_day fails to improve over the control. (A mechanism that changes nothing
  is an `I`, not a `K`.)
- **R4** — annual nuclear energy moves **> 0.5 %** in any year (the G3 gate
  violated in-solve ⇒ the overlay is posting a *level*, not timing, and has
  escaped the anchor).
- **R5** — the overlay posts availability on a date the NRC source does not
  cover, or resurrects a month the wedge fallback dropped.

A PASS → FAIL on any scored criterion **blocks promotion** and is reported
adverse (rule 14: reported, not patched), but is not by itself an R unless it
traces to R1–R5.

---

## §6 — protective checks (on the ABSORBING classes, not nuclear)

**Nuclear is exempt from BOTH C7 and C8 by explicit class list** —
`D1_GATED_CLASSES` does not contain it and `D2_EXEMPT_CLASSES = ("CC_CHP",
"CT_CHP", "ST_CHP", "nuclear")`. Per the caiso-147 §G binding framing, **no
nuclear D-1/D-2 number may be quoted in this session as a passed gate.** The
binding gates sit on the classes that absorb the displaced energy:

- **CT_PEAKER** — C7 `profile_r` / `cv_ratio` must not cross their gates, and C8
  forced share must stay ≤ the **0.15 peaker cap**. (Its 2025 `profile_r` is
  0.864 after caiso-146; a fall below gate is the primary protective risk.)
- **ST_GAS** — C7 gated; C8 grounded-above-budget both sides, must not worsen its
  provenance/shape posture.
- **COAL** — C7 gated (nominal in CAISO at 50.0 MW; reported for completeness).
- **CC_REGULAR** — C1 free-class band; the knife-edge cell to watch, as in
  nyiso-98.
- **C1 `fuelmix`** free-class score must not lose a class.
- Determination must not gain a **FAIL**, and must not spend a **protective**
  ledger slot (currently 0/1). The 2 non-protective slots are already spent on
  the owner's caiso-145 caveats; a third would exhaust the ledger.

`legitimacy_diagnostics.json` is generated **explicitly for both arms** (the
handoff's gotcha: `replay_keeper.py` does not emit it, and C7/C8 score SKIPPED
without it).

---

## §7 — materiality trigger and leave-one-year-out

Pre-registered on the caiso-146/147 precedent: **if |ΔC3a| ≥ 1.0 pp in any year**
between control and arm, the mechanism is scored **leave-one-year-out within
2023–2025** before any promotion is proposed (rule 22 `[R-HOLDOUT]`). Below
1.0 pp the A/B stands on its own.

No out-of-training year is touched: **2023 2024 2025 only**, one invocation per
arm (rule 16 `[R-ALLYEARS]`), arms concurrent (rule 12 `[R-PARALLEL]`). **No
rule-22 calibration-complete marker is written** — that is a separate owner act.

---

## §8 — arms

```
A (control)  replay caiso147_chp_B, zero delta, same HEAD  -> caiso148_control_A
B (arm)      replay caiso147_chp_B  --set nuclear_unit_availability=true
                                                            -> caiso148_nucavail_B
```

Control carries **no** `calibration_attestation.json` (caiso-146/147 precedent);
the two arms are compared **unattested, criterion by criterion**. Only if arm B
is proposed for promotion does it get an attestation built from the caiso-147
one, carrying the 3 ledger entries forward as the owner's caiso-145 act with
magnitudes re-measured, plus `scripts/build_dof_ledger.py`.

Both arms are registered on the dashboard (rule 15 `[R-DASHBOARD]`) whatever the
verdict, and the `nuclear_unit_availability` CAISO matrix cell is updated in this
session (rule 28b `[R-MECH-MATRIX]`) — including if the verdict is `R` or `I`.
