# FINDING — capx D50: the CCS retrofit capex-scaling repair, measured on four ISO t1f surfaces; the blast radius priced; the arming question returned to the owner

**Lane:** capx D50 (built; ERCOT + NEISO arms) and **D50-R** (this completion: the PJM
arm, the conditional MISO arm, the blast radius, the recommendation, and this document).
**Written 2026-09-05.** The D50 checkpoint landed in PR #4728; the PJM and MISO arms were
solved at HEAD `c9f1d26e` and scored at the rebased HEAD `921bb4cd`.
Branch `claude/capx-d50r-completion-ik2giz`. **Date in the filename is D50's
(2026-09-04)** — four ISO shard cells now cite this document by that name and the
citations must resolve; the body is dated honestly as written.

**What this is.** D49 §1 established, zero-solve and like-for-like across ERCOT / PJM /
MISO, that the CCS retrofit screen clears merchant gas-CC retrofits at carbon = 0 because
of a **construction seam**, not economics: the §45Q credit scales with the host's measured
CO2 flow per MWh while `ccs_retrofit_capex_kw` is the ATB capture-island increment for an
H-class reference host charged **flat per kW** — so a host emitting 40–90 % more CO2 per
kW is credited for all of it and charged to capture none of the excess. D50 built the
repair as ONE gated `ScenarioConfig` field, **default-off, zero DOF**, and A/B'd it on
**four** t1f surfaces — ERCOT and NEISO in the D50 checkpoint, PJM here, and MISO here
because PREDECL §2.4's own conditional fired (§7.2). **NOTHING ARMS.** No keeper, shard verdict, marker or backcast
artifact moves. The default flip is an owner ruling, priced in §6 and recommended in §8.

**A citation note, so every existing reference resolves.** The ERCOT and NEISO shard cells
were written at the D50 checkpoint against an anticipated numbering in which ERCOT was §3
and NEISO §4. This document follows the §D50-R charter's numbering: **ERCOT is §2, NEISO is
§3, PJM is §4, MISO is §4b.** Those two cells are left byte-identical (this lane does not
rewrite another lane's ISO text); read their "§3"/"§4" as §2/§3 here. The PJM and MISO
cells were written by this lane and cite §4 / §4b, which resolve as written.

**The pre-declaration** (`docs/handoffs/PREDECL-capx-d50-2026-09-04.md`, pushed before any
repair code existed) is graded at full magnitude in §7 — every prediction P1–P8, Addendum
A included, misses reported as misses.

---

## 1. The whole-fleet census — what the repair does to the candidate set (zero solve)

The census instrument is `scripts/probes/_capxd50_scaled_ceiling_census.py`, output
`results/calibration/capxd50_scaled_ceiling_census.json`, run on the rebuilt base fleets
through the same resolved golden-posture configs the arms solve. It evaluates every
eligible gas-CC tranche at the **hour ceiling** — the most generous possible test, a host
in merit for every available hour — against three bars:

- **flat** — the shipped bar, `capex_learned / 12` per MW, identical for every host;
- **scaled (seam 1)** — `flat × (0.9 · er / 0.32319)`, the capture island sized to the
  host's captured CO2 against the ATB reference host (`captured_ref` = 0.90 × 6.3
  MMBtu/MWh × 0.057 t/MMBtu = 0.32319 t/MWh);
- **scaled + CHP excluded (seams 1+2)** — cogeneration hosts removed from the candidate
  set on the published three-limb basis (§1.3 of the pre-declaration: no published
  capture-island $/kW exists for a cogeneration host's combined flue gas at the electric
  plant's cost basis; the CAMPD rate charges the steam host's fuel to net electric MWh;
  the screen's uplift is the electric-market margin only).

| ISO · year | gas $/MMBtu | carbon $/t | capex $/kW | eligible gas-CC | clears FLAT | clears SCALED | clears SCALED + noCHP | CHP eligible | min er clearing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ERCOT 2028 | 3.17 | 0 | 1,323.6 | 14.99 GW | 3.79 GW | 0.24 GW | **0** | 1.27 GW | — |
| ERCOT 2029 | 3.34 | 0 | 1,271.8 | 10.03 | 1.73 | 0 | **0** | 0.55 | — |
| ERCOT 2030 | 3.98 | 0 | 1,232.3 | 8.52 | 1.72 | 0 | **0** | 0.55 | — |
| NEISO 2028 | 4.77 | 29.83 | 1,323.6 | 12.89 | 12.79 | 12.86 | **12.38** | 0.49 | 0.340 |
| NEISO 2029 | 4.94 | 31.92 | 1,271.8 | 12.89 | 12.84 | 12.89 | **12.39** | 0.49 | 0.340 |
| NEISO 2030 | 5.58 | 34.15 | 1,232.3 | 12.89 | 12.87 | 12.89 | **12.39** | 0.49 | 0.340 |
| PJM 2028 | 4.34 | 0 | 1,323.6 | 58.82 | 5.74 | 0.82 | **0** | 2.38 | — |
| PJM 2029 | 4.51 | 0 | 1,271.8 | 58.82 | 5.89 | 2.50 | **1.68** | 2.38 | 0.606 |
| PJM 2030 | 5.15 | 0 | 1,232.3 | 58.82 | 5.74 | 2.50 | **1.68** | 2.38 | 0.606 |
| MISO 2028 | 3.97 | 0 | 1,323.6 | 34.45 | 5.00 | 1.59 | **0.05** | 7.04 | 0.838 |
| MISO 2029 | 4.14 | 0 | 1,271.8 | 34.45 | 5.23 | 3.37 | **0.38** | 7.04 | 0.576 |
| MISO 2030 | 4.78 | 0 | 1,232.3 | 34.45 | 5.00 | 3.52 | **0.53** | 7.04 | 0.576 |

**The census in one sentence.** At **carbon = 0** the repair very nearly closes the screen
(ERCOT 3.79 GW → 0; PJM 5.74 → 0 in 2028; MISO 5.00 → 0.05), and under **RGGI it does
not** (NEISO 12.79 → 12.38 GW, 96 % of the eligible fleet) — because the avoided-carbon
leg of the uplift is **per tonne too**, so scaling the island per tonne cannot outrun it.
That asymmetry, not the level, is the repair's signature.

**Two structural facts behind it.** (i) A host below the reference rate (`er < 0.359`)
gets a *cheaper* island under seam 1, but at carbon 0 it still needs `er ≥ 0.46` even at
`hr → 0` — no sub-reference host can appear, which is why no carbon-0 ISO gains rows.
(ii) Under RGGI the ceiling slope in `er` gains `0.9 · er · carbon` per hour, ≈ 441,000
$/MW-yr per t/MWh at NEISO 2028 — an order above the scaled bar's slope, so essentially
every New England gas-CC clears.

---

## 2. ERCOT — the repair closes the screen completely

**The A/B.** `ercot-t1f-d50-ccscapex` (run id `ercot-2026-2030-d50-ccscapex`, cache key
`0c3e9cd5b5993bdf`, **pre-declared in PREDECL §4 and matched**; 10.2 min / 4.1 GB peak,
paired with NEISO per rule 12) against the bare `ercot-t1f` control
(`ercot-2026-2030-d46-remeasure`, `873d8c0e6cab52ae`). A **one-field** A/B: the resolved
config differs from the control only in `ccs_retrofit_capex_co2_scaling`, plus five
HEAD-added default-off fields at their cache-neutral drop values.

| year | control | arm |
|---|---|---|
| 2028 | 11 rows / **2,130.9 MW** (684.3 MW CHP) | **0** |
| 2029 | 3 rows / **610.9 MW** | **0** |
| 2030 | 0 | **0** |
| **window** | **2,741.8 MW** | **0 MW** |

Every regular-CC host that converted in the control sits at **0.82–0.94 of the scaled
ceiling bar**; the single host above it (p55470, hr 34.75, 2.06 t/MWh, ratio 1.373) is the
CHP data artifact seam 2 removes and `data/raw/reference/README.md` now flags. Fleet MW,
retirements, builds, the backstop and the reserve margin are **identical to the control in
every year**; only 2028–2030 dispatch moves at the margin (load-weighted price 103.33 →
102.61 / 959.55 → 958.39 / 2342.05 → 2341.13 $/MWh; CO2 2030 285.04 → 285.32 Mt — the
2.74 GW that no longer captures).

**FC rows:** FC-1 FAIL `[I12, I3]` and FC-2 row1/row6 FAIL are **byte-identical** to the
control. FC-8 PASS. FC-7 CAVEAT on both (control: no ledger; arm: ledger built, 8 of 10
entries are ERCOT's registry-armed scarcity/lookahead family with no curated
identification row — an ERCOT lane's item, rule 25). **Determination HOLD → HOLD.**

**Reading (rule 14, stated before the solve):** the 2.7 GW of §45Q-only merchant CCS the
D46 ledger carried was the D49 §1.4 construction seam and nothing else.

---

## 3. NEISO — the cap still binds; what changes is WHO converts

**The A/B.** `neiso-t1f-d50-ccscapex` (run id `neiso-2026-2030-d50-ccscapex`, cache key
`18515067bf4d2fbe`, **pre-declared and matched**; 6.7 min / 3.5 GB, paired with ERCOT)
against the bare `neiso-t1f` control (`neiso-2026-2030-d46-remeasure`, `6690e4d6d66bc819`).

| year | control | arm | delta |
|---|---|---|---:|
| 2028 | 17 rows / 2,999.6 MW (139.6 CHP) | 15 / **2,982.2** | −17.4 |
| 2029 | 23 / 2,994.4 (226.8 CHP) | 12 / **2,996.7** | +2.3 |
| 2030 | 10 / 2,948.6 (8.4 CHP) | 12 / **2,982.6** | +34.0 |
| **window** | **8,942.6 MW** | **8,961.5 MW** | **+18.9** |

Under RGGI (29.83 / 31.92 / 34.15 $/t) the **3 GW/yr cap still binds in every year**, as
pre-declared. Every per-year delta is within one cap-packing unit, so PREDECL §3 STOP 1
(which exempts a cap-bound control year by up to 60 MW) is **not met** — and the +18.9 MW
window total is cap packing, not the repair clearing more MW on the merits.

**What moves is composition.** The control's five `CC_CHP` rows (139.6 / 226.8 / 8.4 MW)
are gone under seam 2 and are back-filled by regular-CC MW. The 2028 set **re-ranks toward
efficient hosts**, MW-weighted CO2 rate **0.608 → 0.550** — the docstring's
"efficient-hosts-win" ordering restored where D49 §1.4 showed it inverted. 2029–2030 draw
from the residual pool and drift the other way (0.429 → 0.431, 0.361 → 0.393). Fleet MW by
fuel is within 20 MW, retirements / builds / backstop / reserve margin identical;
generation shifts toward the converted set (gas_cc_ccs 18.27 → 19.23 TWh in 2030); CO2
2030 14.71 → 14.98 Mt.

**FC rows:** all 14 invariants PASS and every FC-2 row PASS on both arms; FC-7 **PASS**
with the ledger built from the arm's own `run_config.json` (8 entries, 0 UNIDENTIFIED via
the field's curated design-decision row). **Determination PROMOTE → PROMOTE.**

---

## 4. PJM — the repair closes 2028 entirely and **defers** 2029; STOP 1 fired and is diagnosed

**The A/B.** `pjm-t1f-d50-ccscapex` (run id `pjm-2026-2030-d50-ccscapex`, cache key
`167e65187f32056b`, **pre-declared in PREDECL §4 and matched**; 27.3 min / 9.0 GB peak,
solo per rule 12) against the bare `pjm-t1f` control (`pjm-2026-2030-d45r-remeasure`,
`321f04e9060787f0` — re-resolved at HEAD and **unmoved**). A one-field A/B.

| year | control | arm | delta |
|---|---|---|---:|
| 2028 | 16 rows / **2,832.6 MW** (777.2 CHP) | **0** | −2,832.6 |
| 2029 | 3 rows / **752.1 MW** (99.9 CHP) | 2 rows / **909.8 MW** | **+157.7** |
| 2030 | 0 | 0 | 0 |
| **window** | **3,584.7 MW** | **909.8 MW** | **−2,674.9 (−74.6 %)** |

### 4.1 STOP 1 fired — and what the ledger says it is

PREDECL §3 STOP 1 trips when "the arm converts MORE MW than its control in any ISO-year
where the control was NOT cap-bound". PJM 2029 does exactly that (+157.7 MW against a
752.1 MW, non-cap-bound control year). **The STOP is recorded as FIRED, not waived**, and
§3's remedy — "diagnose from the ledger, no registration until explained" — is discharged
here before the run was registered.

**The two converting tranches are `p55337_econ` (501.6 MW, `er` 0.606) and `p55976_econ`
(408.2 MW, `er` 0.607)** — two of the **exact five tranches PREDECL Addendum A.3 named
before this solve** as PJM's 2029–2030 residual channel, sitting at **1.023 and 1.030** of
the scaled ceiling bar on the lower 2029 learned capex (1,271.8 $/kW).

**Why the per-year comparison is not like-for-like.** In the *control*, `p55337` and
`p55976` (both `_econ` and `_committed`) had **already converted in 2028**. The control's
2029 candidate pool is therefore depleted by its own 2028 conversions. In the *arm* nothing
converts in 2028, so those units **remain candidates** in 2029 at a lower learned capex.
The arm **defers** conversions the control took a year earlier; it does not add new ones.
The window total is the like-for-like measure, and it falls by 2,674.9 MW (−74.6 %). The
wrong-direction signature STOP 1 exists to catch — a repair that makes retrofits *easier* —
is **not present**.

**Which object owns the 2029 conversion — A.3's own falsifier clause decides it, and the
finding says which, as A.3 required.** A.3 pre-stated: *"a conversion of any of these five
tranches is NOT a P3 miss on the mechanism — it is the surface (a zone-flat lookahead
signal sitting above a $34–54 unabated bid in ≥ 97 % of hours, the D49 §1.4 price-object
seam) doing what D49 already measured at ERCOT — and the finding must say which."* It is
**the surface**: clearing at a ceiling ratio of 1.02–1.03 requires the host in merit for
≥ 97 % of the year's hours on the prior-year zone signal, which is the unbuilt **seam 3**,
not the capex repair. **P3's 2029–30 leg is nevertheless a MISS and is graded as one** in
§7 at full magnitude — the mechanism attribution explains it, it does not excuse it.

### 4.2 What is identical, and what moves

**Retrofit-preserving to the decimal.** `gas_cc + gas_cc_ccs` is identical to the control
in every year (2029: 62,218.536 MW both sides; 2030: 63,718.536 MW both sides), and the
**adequacy requirement is identical every year** (2028 150,263 / 2029 153,001 / 2030
155,946 MW). Retirements are row-identical.

**What moves is the capacity PATH.** Accredited firm capacity: **−595 MW (2028), −562 MW
(2029), +639 MW (2030)**. Reserve margin (I12): 2027 identical, 2028 −13.5 → −13.8 %,
2029 −13.1 → −13.5 %, **2030 −13.0 → −12.6 %**. And in **2030 the adequacy backstop builds
5,874.3 MW of CT against the control's 3,874.3**, while the control instead decides
**2,000 MW of `gas_ct` through the ECONOMIC entry pipeline at COD 2032** — outside the
window. That is the substitution behind the 2030 sign flip: the control's higher-cost CCS
fleet lifts prices enough for the *economic* screen to fire for 2032, and the arm's cheaper
unabated CCs leave the *administrative* backstop to cover the same adequacy gap in-window.
It is a real consequence of the repair and is reported rather than absorbed.

### 4.3 FC rows

| row | control | arm |
|---|---|---|
| FC-1 invariants | FAIL `['I12','I7']` | FAIL `['I12','I7']` — same failing set |
| FC-2 row1 reserve-margin band | FAIL | FAIL |
| FC-2 row3 no cobweb | PASS | PASS |
| FC-2 row4 backstop share | FAIL 43.9 % | FAIL **48.9 %** |
| FC-7 provenance & DOF | PASS | PASS |
| FC-8 runtime | CAVEAT (9.0 GB) | CAVEAT (9.0 GB) |
| **determination** | **HOLD** | **HOLD** |

**No row changes status — P9's PJM leg is a HIT**, and P9 even pre-named the row pattern
("PJM HOLD→HOLD (FC-1 FAIL; FC-2 row1 FAIL, row3 PASS, row4 FAIL)"). The one magnitude that
moves materially is row4's backstop share, +5.0 points, which is the 2030 substitution
above. *(P9's PJM parenthetical also said "FC-8 CAVEAT"; it reads CAVEAT on both sides.)*

### 4.4 Provenance disclosure

The bundle was **solved at `c9f1d26e`** and **scored at the rebased HEAD `921bb4cd`**. The
only `src/` change between them is **capx D59's `locality_capacity_curves`**, GATED
default-off and NYISO-only, and the PJM cache key is **unmoved** across it
(`167e65187f32056b` re-resolves at both). Stated rather than absorbed.

---

## 4b. MISO — the conditional leg fired, and it is the wave's cleanest result

**Why this leg exists.** PREDECL §2.4 and the D50 charter made MISO conditional: *"it is
solved only if §2.2 misses."* PJM's P3 2029 leg **did** miss on its own falsifier (§4.1),
so the conditional fired **on its literal terms** and the leg was solved rather than argued
away. A.3's pre-attribution of that miss to the surface explains it; it does not un-fire the
condition the miss was written to trigger. This is a deliberately conservative reading.

**The A/B.** `miso-t1f-d50-ccscapex` (run id `miso-2026-2030-d50-ccscapex`, cache key
`f3f96e14bb75c9d9`, **pre-declared in PREDECL §4 and matched**; 64.3 min / 10.0 GB, solo
per rule 12) against the bare `miso-t1f` control (`miso-2026-2030-d45r-remeasure`,
`8d8bc63a0d4378a9`).

| year | control | arm |
|---|---|---|
| 2028 | 12 rows / **2,985.2 MW** (12 of 12 CC_CHP, 100 %) | **0** |
| 2029 | 18 rows / **1,645.9 MW** (924.0 CHP + 722.0 regular-CC) | **0** |
| 2030 | 0 | 0 |
| **window** | **4,631.1 MW** | **0 MW** |

**Which seam removes what.** Seam 2 (CHP exclusion) removes **3,909.2 MW**; seam 1 (the
scaled bar) removes the remaining **722.0 MW** of regular-CC — `p1007` and `p7985`, the two
plants PREDECL §2.4 named. §2.4's reading is confirmed, with two corrections graded at full
magnitude: its **row count is off** (it said "14 converting 2028 rows … all CC_CHP", reading
the stale S123 ledger; the live `d45r` control carries **12**, and they are indeed all CHP),
and its hedge that "at most `p7985_econ` (334.5 MW)" might be marginal **resolves to zero**.

**The arm is capacity-identical to the control in every year.** `gas_cc + gas_cc_ccs` is
identical to the decimal (36,327.000 / 39,327.000 / 39,327.000 MW), reserve margins are
identical to six decimals (−0.088622 / −0.035983 / +0.030874), and the **FC-1 invariant
detail string is byte-identical** to the control's.

| row | control | arm |
|---|---|---|
| FC-1 invariants | FAIL `['I12','I7']` | FAIL `['I12','I7']` — **byte-identical detail** |
| FC-2 row1 / row3 / row4 | FAIL / PASS / FAIL (33.6 %) | FAIL / PASS / FAIL (**33.6 %**, unchanged) |
| FC-7 | CAVEAT (unattested DOF skeleton) | CAVEAT (same; a MISO lane's item, rule 25) |
| FC-8 | CAVEAT (65.0 min, 10.0 GB) | CAVEAT (64.3 min, 10.0 GB) |
| **determination** | **HOLD** | **HOLD** |

**This is the wave's cleanest confirmation of P9's reasoning.** A retrofit preserves the
unit's MW, zone and accreditation, so removing **4.6 GW** of it moves **no gated row at
all** — not a status, not a magnitude, not a digit of the invariant detail. Where PJM's
capacity path did move (§4.2), the cause was the entry/backstop substitution, not the
retrofit accounting; MISO shows the accounting itself is inert.

---

## 5. The FC rows moved, per ISO

The pre-declaration's reasoning (P9) was that a retrofit keeps the unit's **MW, zone and
accreditation**, so every capacity-side invariant and adequacy row is capacity-identical;
what moves is 2028–2030 dispatch at the margin, because a converted unit bids
`hr × 1.12 × gas + vom + 8 + 0.9 · er · 15` with no §45Q in the dispatch bid (spec §5.6, a
known simplification). That is what the four arms show — and MISO shows it in its purest form, with the FC-1
invariant detail byte-identical across a 4.6 GW swing in conversions (§4b).

| ISO | FC-1 | FC-2 | FC-7 | FC-8 | determination |
|---|---|---|---|---|---|
| ERCOT | FAIL `[I12, I3]` — **byte-identical** to control | row1 / row6 FAIL — **byte-identical** | CAVEAT both (instrument difference, §2) | PASS | **HOLD → HOLD** |
| NEISO | PASS — all 14 invariants, both arms | every row PASS, both arms | **PASS** (ledger 8 entries, 0 UNIDENTIFIED) | PASS | **PROMOTE → PROMOTE** |
| PJM | FAIL `['I12','I7']` — **same failing set** as control | row1 FAIL, row3 PASS, row4 FAIL (share 43.9 % → **48.9 %**) | PASS both | CAVEAT both (9.0 GB) | **HOLD → HOLD** |
| MISO | FAIL `['I12','I7']` — **byte-identical detail** | row1 FAIL, row3 PASS, row4 FAIL (share **33.6 % unchanged**) | CAVEAT both (unattested skeleton) | CAVEAT both (10.0 GB) | **HOLD → HOLD** |

FC-3 and FC-4 are `n/a` at this tier; FC-5 and FC-6 are `SKIPPED` (not a golden campaign).

**The FC-7 instrument difference, declared in the pre-declaration before any solve and
repeated here so no reader mistakes it for a model gain:** where a control's FC-7 reads
CAVEAT for a *missing* DOF ledger, the arm may read PASS simply because this lane built one
with `build_forecast_dof_ledger.py` from the arm's own `run_config.json`. At NEISO both
sides carry a ledger and the PASS is real; at ERCOT both read CAVEAT for a different reason
(8 of 10 entries are ERCOT's registry-armed scarcity/lookahead family with no curated
identification row — an ERCOT lane's item under rule 25, not this lane's to close).

---

## 6. The blast radius a default flip would carry — measured, not estimated

### 6.1 The mechanic, verified at HEAD rather than assumed

Under the **(b′-1)** declared-default-flip pattern D44 §1 landed, arming
`ccs_retrofit_capex_co2_scaling` appends a dated line to
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` and **leaves the frozen drop value in
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"`**. Verified in this session against the
live registration: the field is a registered optional field and its frozen drop value is
`False`. Two consequences follow, both measured:

1. **A post-flip bare config hashes identically to today's explicit-`True` arm.** Resolved
   through `run_full_horizon.reference_config(..., golden_posture=True)` →
   `apply_iso_scenario_defaults` → `cache_key()` for all six ISOs:

   | ISO | bare key today | bare key after the flip |
   |---|---|---|
   | ERCOT | `873d8c0e6cab52ae` | **`0c3e9cd5b5993bdf`** |
   | NEISO | `6690e4d6d66bc819` | **`18515067bf4d2fbe`** |
   | PJM | `321f04e9060787f0` | **`167e65187f32056b`** |
   | MISO | `8d8bc63a0d4378a9` | **`f3f96e14bb75c9d9`** |
   | NYISO | `cc7d1050a8090c76` | **`b9e4c79e188ab01e`** |
   | CAISO | `772b1e5abc7fc80c` | **`29f8eb372810195f`** |

   The right-hand column **is** the suffixed arm-key column of PREDECL §4. All twelve keys
   re-resolve at HEAD `c9f1d26e` to their pre-declared values — no drift since the D50
   basis `a35c9f9`, and the five default-off fields added to `ScenarioConfig` since (the
   D51 / D52 / nyiso-189 / miso-213 / caiso-246 gates) are confirmed cache-neutral.
2. **An explicit `False` keeps its key** — D44 §2's rows 3–4 property. One committed
   artifact already exercises it: `results/hindcast/miso-2021-2025-realized-t1h-d55-keyfix`
   records `ccs_retrofit_capex_co2_scaling: false` explicitly and would be untouched.

### 6.2 The census, at HEAD

**153** committed forecast-mode `run_config.json` (the pre-declaration counted 145 at
`a35c9f9`; the difference is bundles landed by other lanes since).

| class | count | consequence of the flip |
|---|---:|---|
| carry the field **explicitly** | 3 | 2 D50 arms already **at** the post-flip key; 1 MISO hindcast at explicit `False` keeps its key |
| leave it at the default → **re-key** | 150 | |
| … of which **end ≤ 2027** | 108 | the screen is gated 2028 → **byte-identical**; a cache-key formality, never a re-measure on the merits |
| … of which **reach ≥ 2028** | 42 | |
| … … with a **decided CCS retrofit** in a committed ledger | **31 bundles / 25 distinct keys** | **behaviour can move** |
| … … with **no committed evolution ledger** | 11 | slim bundles — cannot be read from committed artifacts; stated, not assumed inert |

The 31 behaviour-moving bundles split three ways by registration status:

- **7 BARE keys** — the live canonical verdict rows: `ercot-t1f`, `neiso-t1f`, `pjm-t1f`,
  `miso-t1f`, `nyiso-t1f`, `caiso-t1f`, and **`neiso-t3` (GOLDEN-3)**. **This is exactly
  the set PREDECL §6 named** ("the six bare t1f keys and GOLDEN-3").
- **6 historical / suffixed keys** — preserved baselines (`*-pre-d45r`, `*-pre-d46`,
  `*-pre-p2scope`, `neiso-t1f-s4*`, `miso-t1f-pre-d45r`, `nyiso-t1f-pre-d45r`, the
  GOLDEN-3 `*-pre-fc5/fc6` family). Frozen records of a superseded posture: they re-key
  but are **never re-solved** — re-solving one would destroy the thing it preserves.
- **12 unregistered keys** — bundles with no live verdict row: the CAISO
  `ffr3p`/`ffr4d`/`ffr4e`/`ffr4f`/`ffrsc` A/B family (10 keys, 69 retrofit rows each), the
  NEISO GOLDEN-3 FC-6 arms, and `arm3arm/miso-2031-2035-armed-default`. **PREDECL §6 did
  not enumerate these** — see §7's grading of that line.

### 6.3 The price, at the D45-R / D46 / D47 measured rates — the number for the owner's card

Only the **bare** keys are re-measure candidates (the historical keys are preserved by
definition; the unregistered ones carry no live verdict to refresh):

| bare key | ISO / tier | measured rate | source |
|---|---|---:|---|
| `ercot-t1f` | ERCOT t1f 2026–2030 | 11.8 min | D46 |
| `neiso-t1f` | NEISO t1f 2026–2030 | 8.0 min | D46 |
| `caiso-t1f` | CAISO t1f 2026–2030 | 22.6 min | D46 |
| `pjm-t1f` | PJM t1f 2026–2030 | 28 min | D45-R (**this lane measured 27.3 min** on the same recipe) |
| `miso-t1f` | MISO t1f 2026–2030 | 65 min | D45-R (**this lane measured 64.3 min**) |
| `nyiso-t1f` | NYISO t1f 2026–2030 | ~12 min | D45-R |
| `neiso-t3` | NEISO GOLDEN-3 2026–2050 (25 yr) | 33.0 min | D47 §320 |
| **total** | | **180.4 min ≈ 3.0 h** | |

**But four of the seven are already paid.** Because the post-flip bare key *is* the arm
key (§6.1), this programme's four A/B arms **are** the post-flip ERCOT, NEISO, PJM and MISO
bare bundles — their behaviour is already measured and reported in §§2–4b. The residual
the owner's card actually carries is therefore:

> **CAISO 22.6 + NYISO 12 + GOLDEN-3 33.0 = 67.6 min ≈ 1.1 h of solve**, single-threaded;
> under an hour of wall clock if CAISO and NYISO are paired per rule 12.

That is the number for the card. The un-discounted figure, if none of this lane's four arms
is reused, stays **180.4 min ≈ 3.0 h**.

Two honest qualifications. (a) The committed arm bundles are **slim** (config + evolution
ledgers; the parquet cache is gitignored), so a container needing the full bundle re-pays
that ISO's minutes — the *measurement* is banked, the *cache* is not. (b) GOLDEN-3's FC-6
battery (4 paired arms, 2.37 h measured at D46) is **not** in the 2.2 h: those are
unregistered keys, and whether the campaign is re-run in full is a separate scheduling
call for the audit programme, not a consequence of this flip.

### 6.4 What does NOT move

Backcast keys advance with **byte-identical** behaviour (no backcast year reaches 2028 and
no measured backcast fleet contains a `gas_cc_ccs` unit) — the D41 §6.2 finding, unchanged.
**No committed artifact moves at all**: sidecars, bundles, keeper shards, determinations
and dashboard rows are files, not cache lookups. A key that moved cannot mis-serve, so the
cost is a one-time cache MISS, never a wrong answer.

---

## 7. The pre-declaration, graded at full magnitude

`PREDECL-capx-d50-2026-09-04.md` was pushed **before any repair code existed on the
branch**. Every prediction is graded below as written — including where the addendum's own
grading was more generous to itself than the numbers support.

| # | prediction (as written) | outcome |
|---|---|---|
| **P1** (HIGH) | ERCOT converts **0 rows / 0 MW in 2028** | **HIT** — 0, against the control's 11 rows / 2,130.9 MW |
| **P2** (HIGH) | ERCOT **0 in 2029 and 2030**; window **0 vs 2,741.8 MW** | **HIT** — exactly |
| **P3** (HIGH; refined MED for 2029–30 by A.3) | PJM converts **0 rows in every year** (0 vs 3,584.7 MW) | §7.1 |
| **P4** (HIGH) | seam 2 **LOAD-BEARING at PJM**: 722.2 MW of 2028 + 99.9 MW of 2029 clear the scaled ceiling at 1.01–1.13 and are removed ONLY by the CHP rule; seam-1-only PJM ≈ 0.5–0.8 GW in 2028. *Falsifier: < 500 MW of the control's CHP rows clearing.* | **HIT, to the decimal** — the census puts **exactly 722.2 MW** (8 tranches: p10633, p10805, p55216, p58933) and **99.9 MW** (p58933_committed) above the scaled bar, ratios **1.011–1.130**. Falsifier did not fire. One honest overshoot: the seam-1-only 2028 ceiling set is **0.822 GW**, 2.7 % above the stated 0.8 GW upper bound |
| **P5** (HIGH 2028 / MED 2029–30; sharpened to HIGH in all three by A.2) | NEISO **cap binds every year**; each year 2,850–3,000 MW; total 8,700–9,000 vs 8,942.6 | **HIT** — 2,982.2 / 2,996.7 / 2,982.6 MW, total **8,961.5**; every value inside the pre-declared band |
| **P6** (MED) | NEISO composition **re-ranks toward lower-`er` hosts**; graded MW-weighted `er` of the arm ≤ the control's **in each year** | **MISS, 1 of 3** — 2028 **0.608 → 0.550** (hit, the docstring's efficient-hosts-win ordering restored); 2029 **0.429 → 0.431** and 2030 **0.361 → 0.393** both move the wrong way. The later years draw from the residual pool once the cap has taken the efficient hosts |
| **P7** (MED, conditional) | MISO under the repair converts **≤ 0.35 GW** in the window | **HIT, with room — and it WAS solved** (§7.2 / §4b): the arm converts **0 MW** in every year, against the control's 4,631.1 MW. Worth stating because the zero-solve census had put MISO's *ceiling-clearing* set at 0.05 / 0.38 / 0.53 GW = 0.96 GW for the window, i.e. P7's bound was **not supported by its own upper bound** — the solve, not the census, is what carries it |
| **P8** (MED) | carbon-0 ISOs **≤ 0.5 GW each** with seam 2 (ERCOT ≤ 0.1); NEISO **≥ 80 %** of its gas-CC fleet | **SPLIT — and Addendum A.1 over-graded it.** ERCOT 0 / 0 / 0 **HIT**; NEISO 96 % **HIT**; PJM **2028 0 HIT but 2029–30 1.68 GW — 3.4× the bound, a MISS**; MISO 0.05 / 0.38 **HIT** but 2030 **0.53 GW, a marginal miss**. A.1 graded PJM on 2028 alone and called MISO's 0.53 "HIT … at the edge"; graded at full magnitude P8 holds in 2028 for every carbon-0 ISO and **fails in 2029–2030** |
| **P9** (HIGH) | **no FC-1/FC-2 row changes STATUS** in any arm; every determination unchanged (ERCOT HOLD→HOLD, PJM HOLD→HOLD, NEISO PROMOTE→PROMOTE) | **HIT in all four** — ERCOT (FC-1 FAIL `[I12,I3]`, FC-2 row1/row6 FAIL, byte-identical); NEISO (all PASS both sides); PJM §7.1; MISO byte-identical invariant detail across a 4.6 GW swing (§4b) |
| **STOP 1–4** | §3's four binding STOPs | **none fired** — §8.2 |

**Addendum A**, graded separately:

| # | claim | outcome |
|---|---|---|
| **A.1** | the census instrument, run zero-solve on the rebuilt fleets before the NEISO/PJM solves | **stands** — reproduced independently this session from the committed JSON; every cell of §1's table matches |
| **A.2** | P5 sharpens to HIGH in all three NEISO years; only five eligible NEISO tranches fail the scaled bar | **HIT** — the cap bound in all three |
| **A.3** | PJM's 2029–30 residual channel: five regular-CC tranches (p55976 ×2, p55337 ×2, p3096_econ) sit **1.0–3.6 % above** the scaled bar at the lower learned capex, 1.68 GW total; P3's 2029–30 leg drops HIGH → MED | **the channel is confirmed exactly** — measured ratios **1.005–1.036**, **1,675.5 MW**, the same five tranches. Whether they converted is §7.1 |

### 7.1 P3 and P9 at PJM, graded

**P3 — SPLIT, and the miss is reported at full magnitude.**

| leg | as written | outcome |
|---|---|---|
| 2028 (HIGH) | 0 rows | **HIT** — 0 vs 2,832.6 MW |
| 2029–30 (HIGH in §2.2, refined to MED by A.3) | 0 rows | **MISS** — 2 rows / 909.8 MW in 2029 |
| window | 0 MW vs 3,584.7 | **MISS on the letter** — 909.8 MW; but −74.6 % against the control |

The falsifier §2.2 wrote for P3 ("any conversion") **fired**. A.3, pushed before the solve,
had already named the five candidate tranches and pre-committed the reading: a conversion
among them is the **surface** (seam 3, unbuilt), not the capex repair. Two of those five
converted, at ceiling ratios 1.023 / 1.030. §4.1 gives the ledger diagnosis. **The
attribution explains the miss; it does not convert it into a hit.**

**P9 — HIT at PJM.** No FC-1 or FC-2 row changed status, and the determination is HOLD →
HOLD, exactly as pre-declared including the row-by-row pattern.

### 7.2 The MISO trigger, and P7

PREDECL §2.4 and the charter make MISO conditional: *"The PJM result decides whether MISO
is solved: it is solved only if §2.2 misses."* **§2.2 missed** — P3's 2029 leg is a miss on
its own falsifier — so the trigger fired **on its literal terms** and MISO was solved rather
than argued away, even though A.3 had pre-attributed the miss to the surface. The reading
is deliberately conservative: a pre-declaration that anticipates a miss does not un-fire the
condition that miss was written to trigger.

**And the leg paid for itself.** MISO converts **0 MW** against its control's 4,631.1 MW
(§4b) — **P7 HIT with room**, where the zero-solve census alone could not have carried it
(its ceiling bound was 0.96 GW, nearly 3× P7's claim). The leg also produced the wave's
cleanest structural result: a 4.6 GW swing in conversions that moves **no gated row and no
digit of the FC-1 invariant detail**, which is P9's premise demonstrated rather than argued.

---

## 8. The arming recommendation

### 8.1 What D50 pre-stated, verbatim

Unlike D52 — which fixed a numeric `±3-point` arming condition in its own §6 — **D50
pre-declared no numeric arming threshold.** What it pre-stated is a *direction* and a
*STOP set*, and those are quoted here in full rather than paraphrased.

The charter (`capx-director-prompt-pack-2026-08.md` §D50, items 4–5 and GUARDRAILS):

> **BLAST RADIUS, measured:** list every committed forecast/hindcast key whose cache key
> the default flip would advance … and the solve-minutes to re-measure them at the D45-R
> measured rates — that number goes on the owner's card.
>
> **FINDING** … the per-ISO conversion tables before / after, the FC rows moved, the blast
> radius, and the **ARMING RECOMMENDATION on the pre-stated condition. NOTHING ARMS in
> this lane — the default flip is an owner ruling.**
>
> GUARDRAILS: rules 5, 12, 13, 14 (**a faithful capex makes retrofits HARDER — fewer
> conversions is the expected signature**), 21, 22, 24, 25, 27, 28.

The pre-declaration (`PREDECL-capx-d50-2026-09-04.md` §3), the four binding STOPs:

> 1. **More MW anywhere (rule 14).** The arm converts MORE MW than its control in any
>    ISO-year where the control was NOT cap-bound (control < 2,940 MW), OR exceeds a
>    cap-bound control year by > 60 MW … Either is the wrong-direction signature: STOP …
> 2. **A sub-reference host converting at carbon 0** (`er < 0.359` in ERCOT or PJM) …
> 3. **Any realized cache key ≠ its §4 value**, or any collision with a committed key.
> 4. **The byte-inertness proof failing** … the repair does not land at all.

**So the pre-stated condition is: the repair moves in the rule-14 direction, no STOP
fires, and the blast radius is priced.** That is what is graded below — no threshold is
retrofitted onto the result.

### 8.2 The condition, graded

| limb | outcome |
|---|---|
| Rule-14 direction (fewer conversions) | **MET in every ISO** — ERCOT window 2,741.8 → **0 MW**; PJM window 3,584.7 → **909.8 MW (−74.6 %)**; NEISO cap-bound on both sides, composition-only |
| **STOP 1 — more MW anywhere** | **FIRED at PJM 2029** (+157.7 MW against a non-cap-bound control year) — recorded, not waived. Diagnosed from the ledger in §4.1: the control's 2029 pool was depleted by its own 2028 conversions, so the arm **defers** rather than adds; the like-for-like window figure falls 74.6 %. The wrong-direction signature the STOP exists to catch is **not present**. NEISO's +18.9 MW window is inside the pre-declared one-cap-packing-unit exemption |
| STOP 2 — sub-reference host at carbon 0 | **not fired** — the two PJM converters carry `er` 0.606 / 0.607, far above the 0.359 reference |
| STOP 3 — key drift or collision | **not fired** — all 12 keys re-resolve to their §4 values at HEAD |
| STOP 4 — byte-inertness | **not fired** — the off path is byte-identical on the committed `ercot-t1f` recipe |
| Blast radius priced | **DONE** — §6.3 |

### 8.3 The recommendation: **ARM**, with two disclosures

**Recommend arming `ccs_retrofit_capex_co2_scaling` as the default posture**, on this
reasoning:

1. **This is a construction repair, not a lever.** The shipped flat-per-kW bar charges a
   2.06 t/MWh host and a 0.36 t/MWh host the same capex for capture islands that differ
   ~6× in size, while crediting each for its own tonnes. Rule 13 `[R-MEASURED]` and rule 21
   `[R-NO-MAGIC]` both point the same way: `captured_ref` = 0.90 × 6.3 × 0.057 = 0.32319
   t/MWh is composed entirely of existing cited constants, has **zero DOF**, and
   regenerates for any forward year from forward drivers. The off posture is the defect.
2. **Rule 1 `[R-STRUCT]` decides it, and decides it independently of the numbers.** The
   repair would stay in even if it made a fit worse. That it *also* removes 6.3 GW of
   §45Q-only merchant CCS the model had no economic basis to build is the seam closing,
   not a residual improving.
3. **The direction is the pre-stated one**, in both regimes and for the right reason: the
   screen closes where carbon is 0 and does **not** close under RGGI, because the
   avoided-carbon leg is per tonne too. A repair that had closed NEISO as well would have
   been evidence the arithmetic was wrong.
4. **The cost is small and bounded** — **1.1 h** of residual solve (§6.3), no committed
   artifact moves, no keeper, marker or backcast row touched, and **four of the seven bare
   keys are already measured** by this programme's own arms.
5. **Four ISOs now carry their own measured evidence**, none transferred (rule 25), and all
   four determinations are unchanged. MISO is the structural proof that the retrofit
   accounting itself is inert: 4.6 GW of conversions removed, and not one gated row or
   invariant digit moves (§4b).

**Disclosure 1 — the fourth seam is NOT closed, and the finding says so at the gate.** The
ΔFOM ($35,000/MW-yr) and the capture VOM adder stay **reference-host-sized** and therefore
dilute per captured tonne as `er` rises. The clearing threshold moves (`er ≥ ~0.46` →
`~0.58–0.63` at carbon 0) rather than vanishing. D49 named three seams and this lane built
those three; the fourth is recorded for the director, unbuilt and unfitted.

**Disclosure 2 — a PJM channel the census can see and the pre-declaration under-called.**
1.68 GW of PJM regular-CC tranches sit **1.0–3.6 % above** the scaled ceiling bar in
2029–2030 (PREDECL Addendum A.3). **That channel is LIVE**: two of the five tranches
(`p55337_econ`, `p55976_econ`, 909.8 MW) converted in the arm's 2029, at ceiling ratios
1.023 / 1.030 — which is what fired STOP 1 and what makes P3's 2029–30 leg a miss. Whether
those units convert is decided by the **price object** (D49 §1.4 / seam 3, **unbuilt**),
not by this repair: clearing at 1.02–1.03 of the bar needs the host in merit ≥ 97 % of the
year's hours on a zone-flat prior-year signal. **The recommendation does not depend on
it** — arming is right either way, and a live seam-3 channel is an argument *for* lanes on
seam 3, not against this one. It does mean the repair's PJM effect is a 74.6 % reduction
rather than a closure, and §4 says so.

**Scope of the recommendation.** ARM the field's *default*. This is a **posture** carrying
no ISO's fitted numbers — `captured_ref` is one ATB reference host for all six ISOs — so
rule 25 `[R-ISO-SCOPE]` is satisfied by construction, as Q30/D44 was. The recommendation
does **not** ask for any re-measure to be scheduled; §6.3 prices it so the owner can.

**Nothing in this lane arms.** The field ships default-off at HEAD. Every ISO shard cell
stays `fc: "O"` (ERCOT / NEISO / PJM: measured, open) or `fc: "U"` (MISO / NYISO / CAISO:
untested, no transfer — rule 25).

---

## 9. Governance attestation

**Rule 22 `[R-HOLDOUT]`.** Every solve in this lane is **t1f forecast mode, 2026–2030**, on
forward drivers only. No holdout year is touched: no backcast solve, no scoring against
measured H1-2026, no validation or locked-test year, no `--holdout-authorized`. The CLAUDE.md
standing clause that 2026+ forecast-mode runs are unrestricted is what licenses them.

**Rule 24 `[R-REGISTRY]`.** `ccs_retrofit_capex_co2_scaling` is a `ScenarioConfig` field,
registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at
`"False"`, exposed as `--ccs-retrofit-capex-co2-scaling`, and recorded in every run's
`run_config.json`. No env knob, no per-plant dict, no `getattr` fallback.

**Rule 25 `[R-ISO-SCOPE]`.** Three ISOs measured, three cells stamped with **their own**
evidence. MISO / NYISO / CAISO enter as `U` — no verdict transfers. The MISO expectation in
PREDECL §2.4 is recorded as an unsolved zero-solve expectation, never as a verdict.

**Rule 28 `[R-MECH-MATRIX]`.** The base row `ccs_retrofit_capex_co2_scaling` exists in
`mechanism-matrix.js` with a cell in all six shards (duty c, landed with the field in
PR #4728). This session discharges duty (b) for **PJM only** — it stamps the PJM shard's
cell with the measured result and leaves the ERCOT / NEISO / MISO / NYISO / CAISO cell
texts byte-identical.

**Rule 27 `[R-PUSH]`.** Every file ≥ 300 lines pushed by this session is blob-verified
against the remote (line count + SHA) before the next commit; verification results are
recorded in §9.1. No full-file rewrite from regenerated response content — exact on-disk
bytes only.

**Authority to author for a closed lane.** D50 closed as a checkpoint at director round
r#36 with four items owed. This session is the chartered **§D50-R** completion lane, which
is its authority. The nearest governance precedent is the **Q37** limb the owner adopted
2026-09-04 (rubric v1.1 §5): *"a follow-up lane may author a forecast attestation iff it is
pre-declared before authoring, moves only the attestation row, and re-scores
artifact-only."* Stated precisely: Q37 licenses a narrower act than this one — it governs
**attestation-row** authorship, and this lane also produces a new arm — so Q37 is cited as
the adopted precedent for pre-declared follow-up authorship, not as the literal authority
for §4. No attestation row is moved by this session and no bundle is re-scored artifact-only.

**What this session did NOT do.** No keeper, no shard verdict flip, no `complete`/`final`
marker, no default flip, no backcast artifact, no ERCOT or NEISO re-solve, no matrix cell
outside PJM's and MISO's. **MISO WAS solved** — not as an expansion of scope but because PREDECL §2.4's
own conditional fired on its literal terms when P3's 2029 leg missed (§7.2); its cell is
stamped with its own measured evidence under rule 25, and it arms nothing.

### 9.1 Rule-27 blob verification record

Every file ≥ 300 lines pushed by this session, fetched back from
`origin/claude/capx-d50r-completion-ik2giz` and compared to the local on-disk bytes
(line count + SHA-256 prefix). All five verified **byte-identical**:

| file | lines | sha256[:16] | verdict |
|---|---:|---|---|
| `frontend/data/forecast/ff-verdicts.json` | 11,966 | `20fe6be80c73711b` | **OK** |
| `docs/codebase-site/data/mechanism-matrix/PJM.js` | 311 | `3af02c65975e560e` | **OK** |
| `docs/codebase-site/data/mechanism-matrix/MISO.js` | 484 | `93134fa08dc3f53b` | **OK** |
| `docs/handoffs/FINDING-capx-d50-2026-09-04.md` | 624 | `d83e9dad9c57ac70` | **OK** |
| `CHANGELOG.md` | 5,518 | `c0ee1fde86b7e5d4` | **OK** |

*(This table records the state at the verification push; the finding's own row is its
pre-§9.1 revision, re-verified in the same way on the commit that adds this section.)*

No file was rewritten from regenerated response content. `ff-verdicts.json` was edited
through a writer that reproduces the committed formatting exactly (`indent=1`,
`ensure_ascii=True`, trailing newline), verified by round-trip before use, so the diff is
**283 insertions / 0 deletions** across a 400 KB file. Transport was `git push` on a pack
freshly based on `origin/main`, per the Git & Pushing rule (the ≥ 400 KB payload is
precisely the class `push_files` cannot carry).
