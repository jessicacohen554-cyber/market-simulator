# FINDING miso-237 — the SPP neighbour-state channel is **QUANTITY-SIDE, not a price-representation deficiency**: the best available price representation does not reach it. And handoff item 2's premise is **REFUTED on three of four seams** — MISO's own state is not an unused input, it is an **OVER-transmitted, wrong-signed** one, which supplies item 3 its first partial cause

**Zero LP. No arm, no screen, no bundle, no registration, no cell verdict.**
**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22:
2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was solved, scored
or registered**. MISO still carries exactly **one** registered run (rule 15).

**Pre-registration:
`PREREG-miso237-price-representation-or-quantity-channel-2026-09-07.md`, pushed at `887c7cad`
before any adjudicating quantity.** The two supplementary measurements are governed by
`ADDENDUM-miso237-own-state-purge-and-the-conditioning-leg-2026-09-07.md`, pushed at `9b729a6e`
**before the numbers it governs**; that addendum also discloses, against interest and before any
number, that this session's increment is **not** miso-236's (§0 there, restated in §1 below).
Every decision rule applied here was fixed in one of those two documents; none was written after
seeing a number.

Probe: `scripts/probes/_miso237_price_representation_vs_state_phase0.py` →
`results/calibration/_miso237_price_representation_vs_state_phase0.json`.

**Basis (PREREG §0b).** The Indiana-hub **RT** series builds the finite-hour `ok` mask
(byte-identically to miso-236, so the hour set is the predecessor's) and is the price `P` in the
ADDENDUM §A alignment column — the same series miso-235 §4b used. **Every regressor is the
Indiana-hub DA** series. They correlate only +0.402 / +0.424 / +0.553 and are never interchanged.
miso-232's measured decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by
anything here.

---

## 0. The provenance gate cleared on BOTH legs — the instrument is the predecessors', not a lookalike

PREREG §1 fixed two legs, either failing declaring the instrument BROKEN and nothing published.

| leg | what it reproduces | cells | bar | **measured** |
|---|---|---:|---:|---:|
| **G-P1** | miso-235's `sigma_measured_mw` and `sigma_resid_measured_mw` | 4 seams × 3 years × 2 | ≤ 0.5 MW | **0.00 MW** |
| **G-P2** | miso-236's **gated** `delta_r2_A_nohydro`, in miso-236's OWN metric | 9 | ≤ 0.005 | **0.00005** |

G-P2 per cell: PJM 0.00005 / 0.00000 / 0.00001; SPP 0.00005 / 0.00004 / 0.00003; South
0.00005 / 0.00002 / 0.00002. So what follows decomposes miso-235's and miso-236's objects, not
different ones.

**A THIRD reproduction, unplanned and reported because it is evidence for the instrument rather
than for any verdict:** ADDENDUM §A's alignment column reproduces miso-235 §4b's published PJM
figures **exactly** — model `|corr(r_model, P)|` **0.3243 / 0.3143 / 0.2858** against its published
−0.3243 / −0.3143 / −0.2858, and measured **0.1260 / 0.1234 / 0.0621** against its −0.1260 /
−0.1234 / −0.0621. No decision rule rests on this and none was written for it.

## 1. What is measured — and, stated first, what it is NOT

**`ΔR²_S|P1` here is NOT miso-236's `ΔR²_A`.** PREREG §2b defines `ΔR²_S|P = R²(x on P ∪ S) −
R²(x on P)` on the **raw measured flow** for a state block `S`, with `S_nbr` and `S_own` as two
**separate** blocks — so `ΔR²_nbr|P1` does not condition on MISO's own state, whereas miso-236's
`ΔR²_A` is the neighbour increment over Block B on the single-spread residual. **The two are
different quantities and neither is presented as the other anywhere below.** ADDENDUM §0 said so
before the numbers were read; §5 measures `rho` under miso-236's conditioning as well, so the
reader need not take it on faith; and §0's G-P2 leg reproduces miso-236's own quantity separately.

The three nested price blocks, fixed in PREREG §2a:

| block | what it is | what it corresponds to in the model |
|---|---|---|
| **`P1`** | the single **linear** spread miso-235/236 used | one linear regressor — **less** than the model actually has |
| **`P2`** | the same series **non-parametrically** (20-ventile step + linear) | **the band ladder's own expressive class**: `spec.py` clears band `k` iff `p_bus − p_nbr > delta_k`, i.e. a monotone step function of the spread |
| **`P3`** | `P2` **plus each leg of the spread separately and non-parametrically** | what only a **better price representation** could express — the model's merit test sees the **difference** alone, so the two legs cannot act with different gains and the neighbour's price **level** cannot enter |

`P2` exists so that price is not under-credited: attributing to "price" only what a single linear
term can express would overstate the non-price residual, and this session refused to do that
(PREREG §0c). **South and Manitoba have no neighbour price series at all** (SOCO/TVA are not
organised markets; MHEB publishes none), so `P3 ≡ P2` there **by construction** — declared in the
PREREG before any number, not discovered after.

Every `R²` is dof-**ADJUSTED** with `k` the **numerical rank** of the design (`P3` carries ~57
columns whose legs are collinear by construction), which is the gated statistic; raw values are in
the JSON. The gated statistic is the **survival ratio** `rho = ΔR²_S|P3 / ΔR²_S|P1`, in which the
state block, the rows and the denominator are all held fixed and **only the price block varies**.

## 2. Q-1 — THE FORM QUESTION IS ANSWERED. SPP's neighbour-state channel is QUANTITY-SIDE

Bars fixed ex ante: **QUANTITY-SIDE FORM** iff `rho ≥ 0.50` in all three years **and**
`ΔR²|P3 ≥ 0.05` in all three years; **PRICE-REPRESENTATION FORM** iff `rho < 0.25` in all three;
**MIXED** otherwise. **GATED on SPP** — the one seam miso-236 read ADMISSIBLE.

| seam | year | `ΔR²_nbr|P1` | `ΔR²_nbr|P2` | **`ΔR²_nbr|P3`** | **`rho`** |
|---|---|---:|---:|---:|---:|
| **SPP** (GATED) | 2023 | 0.3519 | 0.3516 | **0.2891** | **0.822** |
| | 2024 | 0.2396 | 0.2357 | **0.1873** | **0.782** |
| | 2025 | 0.0356 | 0.0448 | **0.0688** | **1.933** |
| PJM | 2023 / 2024 / 2025 | 0.0371 / 0.0360 / 0.0195 | 0.0322 / 0.0200 / 0.0240 | 0.0320 / 0.0146 / 0.0792 | 0.863 / **0.406** / 4.062 |
| South | 2023 / 2024 / 2025 | 0.0288 / 0.0067 / 0.0134 | 0.0301 / 0.0072 / 0.0167 | 0.0301 / 0.0072 / 0.0167 | 1.045 / 1.075 / 1.246 |
| Manitoba | — | — | — | — | **no block — MHEB has no US-BA record** |

| seam | **verdict** | gated? |
|---|---|---|
| **SPP** | **QUANTITY-SIDE FORM** | **GATED** |
| PJM | MIXED (2024 `rho` 0.406) | reported |
| South | MIXED (`ΔR²|P3` 0.0301 / 0.0072 / 0.0167, below the 0.05 floor) | reported |
| Manitoba | NO BLOCK — data absence | reported |

**THE ANSWER TO THE HANDOFF'S FIRST QUESTION: the miso-236 §6.3 alternative is REFUTED for SPP.**
78–82 % of the neighbour-state increment survives a price representation that is strictly richer
than anything the model's merit test can express — non-parametric in the spread *and* in each of
its two legs separately, built on the very SPP NORTH hub DA series the armed keeper already
carries. In 2025 the increment **grows** under `P3` (`rho` 1.933): the rich price block absorbs
variance that was masking state signal rather than absorbing the signal itself.

**Two disclosures that do not change the verdict, made because they could be read as if they
did.** (a) SPP 2025's `rho` = 1.933 sits on a small denominator (`ΔR²|P1` = 0.0356), so it is not
a precise ratio; the verdict does not depend on its size, only on its clearing 0.50, and §5's
conditioned value for the same cell is a well-behaved **1.013**. (b) The pre-registered absolute
floor is on `ΔR²|P3` and SPP clears it in all three years (0.2891 / 0.1873 / 0.0688); it is what
**stops** South's near-1.0 `rho` from confirming on increments of 0.0072–0.0301, which is exactly
what the floor was fixed for.

**PJM's contrast is the sharpest thing in the table and it points the other way.** Under §5's
conditioning PJM's neighbour increment is **59 / 63 / 74 % absorbed** by `P3` (`rho` 0.410 / 0.373
/ 0.257): PJM's neighbour-state channel is **substantially a price-representation object** where
SPP's is not. Reported, not gated — PJM reads MIXED under both conditionings, so nothing moves.

## 3. Q-2 — handoff item 2's premise is REFUTED on three of four seams

### 3a. The gated leg — the same form question for MISO's OWN state

| seam | year | `ΔR²_own|P1` | `ΔR²_own|P2` | **`ΔR²_own|P3`** | **`rho`** | verdict |
|---|---|---:|---:|---:|---:|---|
| **PJM** | 2023 / 2024 / 2025 | 0.1170 / 0.0845 / 0.1737 | 0.1249 / 0.0674 / 0.1821 | **0.2374 / 0.0875 / 0.3362** | **2.029 / 1.036 / 1.936** | **QUANTITY-SIDE (GATED)** |
| **SPP** | 2023 / 2024 / 2025 | 0.1786 / 0.2103 / 0.1742 | 0.1832 / 0.1963 / 0.1629 | **0.1149 / 0.1464 / 0.1763** | **0.643 / 0.696 / 1.012** | **QUANTITY-SIDE (GATED)** |
| South | 2023 / 2024 / 2025 | 0.0465 / 0.0423 / 0.0491 | 0.0401 / 0.0496 / 0.0466 | 0.0401 / 0.0496 / 0.0466 | 0.862 / 1.173 / 0.949 | **MIXED (GATED)** — floor |
| Manitoba | 2023 / 2024 / 2025 | 0.0911 / 0.3340 / 0.0041 | 0.0801 / 0.2673 / 0.0047 | 0.0801 / 0.2673 / 0.0047 | 0.879 / 0.800 / 1.146 | MIXED (reported) |

MISO's own state acts on its PJM and SPP ties through a channel **no price representation
reaches**. South fails only the absolute floor (0.0401–0.0496 against 0.05) — a corroboration of
miso-236's PREDOMINANTLY IDIOSYNCRATIC verdict on a different statistic, not a contradiction of
it. Manitoba's own-state increment swings 0.0047–0.2673 across three years, which is why the
PREREG declined to gate it.

### 3b. THE TRANSMISSION CHECK — and the refutation (REPORTED, NOT GATED)

The handoff's cross-cutting claim was: *"MISO's own net load and VRE … explain 4–19 % of EVERY
seam's measured residual … and the model reproduces NONE of it."* Measured directly:

| seam | year | `R²(model bus price | own state)` | `R²(r_measured | own)` | `R²(r_model | own)` | model : measured |
|---|---|---:|---:|---:|---:|
| **PJM** | 2023 | 0.3946 | 0.1241 | **0.2475** | **1.99×** |
| | 2024 | 0.1606 | 0.0888 | **0.3175** | **3.58×** |
| | 2025 | 0.2684 | 0.1800 | **0.2450** | **1.36×** |
| **SPP** | 2023 | 0.3946 | 0.1764 | **0.0498** | **0.28×** |
| | 2024 | 0.1606 | 0.1914 | **0.0132** | **0.07×** |
| | 2025 | 0.2684 | 0.1606 | **0.0144** | **0.09×** |
| South | 2023 / 2024 / 2025 | 0.3935 / 0.1611 / 0.1955 | 0.0451 / 0.0385 / 0.0499 | 0.1294 / 0.2015 / 0.0400 | 2.87× / 5.23× / 0.80× |
| Manitoba | 2023 / 2024 / 2025 | 0.3946 / 0.1606 / 0.2684 | 0.0715 / 0.2554 / 0.0030 | 0.2059 / 0.3445 / 0.1054 | 2.88× / 1.35× / 35.1× |

**THE PREMISE IS REFUTED ON PJM, SOUTH AND MANITOBA AND CONFIRMED ONLY ON SPP.** MISO's own state
is **not** an unused input: the model's own solved bus price is 16–39 % own-state by `R²`, and the
model transmits that through the merit test into three of its four seam residuals **more strongly
than the real seams carry it** — 1.4–3.6× on PJM, 0.8–5.2× on South, 1.4–35× on Manitoba. **SPP is
the single seam where the model genuinely under-transmits** (0.07–0.28×), and SPP is also the seam
carrying the admissible neighbour-state driver. **The one seam starved of state information is
starved of it on both blocks.**

### 3c. The signs — the model's PJM response is large, stable and not in the measured record

Own-net-load coefficient on the single-spread residual, MW per z-score, import-positive
(PREREG §3c, reported not gated):

| seam | measured 2023 / 2024 / 2025 | **model** 2023 / 2024 / 2025 |
|---|---:|---:|
| **PJM** | **+47.4 / −361.1 / +271.5** (sign-unstable) | **−866.2 / −1043.4 / −843.5** (stable, 2–18×) |
| SPP | −296.6 / −301.9 / −17.0 | −51.1 / −34.1 / −26.9 (same sign, 6–9× small in 2023/24) |
| South | +13.1 / +90.7 / −1.1 | +73.1 / +152.7 / +70.8 |
| Manitoba | +195.9 / +422.3 / −30.6 | +161.3 / +251.6 / +55.6 |

The model's PJM seam residual carries a **large, stable, negative own-net-load response that the
real seam does not have** — the measured coefficient changes sign across the three years and is
2–18× smaller. This is the object §4 tests.

## 4. ADDENDUM §A — item 3's defect gets its FIRST partial cause, and it is PARTIAL

miso-235 §4b measured the model's PJM residual as **2.5–4.6× more price-aligned** than the
measured seam's; miso-236 removed the `(month × hod)` envelope template as the explanation and
left the defect with **no named cause at all**. §3c says the model carries an own-net-load
response the real seam does not, and MISO net load is the dominant driver of MISO's price — so the
hypothesis is that this response **is** a spurious price alignment. The ADDENDUM fixed the test
and its bars before computing it: purge `S_own` from each side and read how far the model's
alignment moves **toward** the measured seam's, `phi`; **CANDIDATE CAUSE** iff `phi ≥ 0.50` in all
three years, **REFUTED** iff `phi < 0.20` in any year, **PARTIAL** otherwise. Gated on PJM.

| seam | year | `|corr(r_model,P)|` | purged | `|corr(r_meas,P)|` | measured purged | **`phi`** |
|---|---|---:|---:|---:|---:|---:|
| **PJM** (GATED) | 2023 | 0.3243 | **0.2530** | 0.1260 | 0.1745 | **0.360** |
| | 2024 | 0.3143 | **0.1967** | 0.1234 | 0.0830 | **0.616** |
| | 2025 | 0.2858 | **0.1750** | 0.0621 | 0.1404 | **0.495** |
| South | 2023 / 2024 / 2025 | 0.1201 / 0.1223 / 0.0209 | 0.0497 / 0.0007 / 0.0841 | 0.0002 / 0.0135 / 0.0204 | 0.0226 / 0.0548 / 0.0321 | 0.587 / 1.117 / **−113.7** |
| SPP | 2023 / 2024 / 2025 | 0.0244 / 0.0087 / 0.0589 | 0.0342 / 0.0444 / 0.0258 | 0.1141 / 0.1062 / 0.0539 | 0.0155 / 0.0136 / 0.0450 | 0.109 / 0.366 / **6.618** |
| Manitoba | 2023 / 2024 / 2025 | 0.0745 / 0.1227 / 0.0012 | 0.0368 / 0.0601 / 0.0805 | 0.0207 / 0.0495 / 0.0171 | 0.0482 / 0.1191 / 0.0319 | 0.701 / 0.855 / 4.983 |

**PJM VERDICT: PARTIAL** (`phi` 0.360 / 0.616 / 0.495 — no year below the 0.20 refutation bar, one
year below the 0.50 confirmation bar). On the pre-registered rule this **closes nothing and
licenses nothing**. What it establishes is quantitative and is more than item 3 had: **purging
MISO's own state from the model's PJM residual removes 36 / 62 / 50 % of its excess price
alignment**, taking `|corr|` from 0.3243 / 0.3143 / 0.2858 to 0.2530 / 0.1967 / 0.1750 against a
measured 0.1260 / 0.1234 / 0.0621. **Roughly half of the defect miso-236 left uncaused is the
spurious own-net-load response, and roughly half is still unaccounted for.**

**The measured side is the control and it behaves differently, which is the point.** Purging the
same block from the *real* seam's residual moves its alignment **up** in 2023 (0.1260 → 0.1745)
and 2025 (0.0621 → 0.1404) and down only in 2024. The real seam's price alignment does not rest on
own state; the model's substantially does.

**The three non-gated seams' `phi` values are arithmetically explosive and are disclosed as
meaningless rather than quoted** — South 2025 (−113.7), SPP 2025 (6.618) and Manitoba 2025 (4.983)
all divide by a near-zero model-minus-measured alignment gap (0.0005, 0.0050, 0.0159). Only PJM's
column carries meaning, which is why the ADDENDUM gated PJM alone.

## 5. ADDENDUM §B — the conditioning leg. The gated verdicts SURVIVE, and one of them tightens

REPORTED, NOT GATED, and by the ADDENDUM's own rule it **cannot move a pre-registered verdict**.
`rho` recomputed with the *other* state block held in **every** price base — i.e. under miso-236's
conditioning:

| seam | year | `rho_nbr` (pre-reg) | **`rho_nbr|own`** | `rho_own` (pre-reg) | **`rho_own|nbr`** |
|---|---|---:|---:|---:|---:|
| **SPP** | 2023 | 0.822 | **0.954** | 0.643 | **0.896** |
| | 2024 | 0.782 | **0.957** | 0.696 | **0.893** |
| | 2025 | 1.933 | **1.013** | 1.012 | **0.875** |
| PJM | 2023 / 2024 / 2025 | 0.863 / 0.406 / 4.062 | **0.410 / 0.373 / 0.257** | 2.029 / 1.036 / 1.936 | 1.105 / 0.974 / 0.944 |
| South | 2023 / 2024 / 2025 | 1.045 / 1.075 / 1.246 | 1.038 / 1.016 / 1.039 | 0.862 / 1.173 / 0.949 | 0.975 / 1.073 / 0.957 |

**SPP's gated verdict is not merely robust, it is cleaner under the predecessor's conditioning:
95 / 96 / 101 % of the neighbour-state increment survives `P3`, on increments of 0.3102 / 0.2204 /
0.1027 that clear the 0.05 floor in every year.** PJM's and SPP's own-state verdicts also survive
(`rho_own|nbr` ≥ 0.875 in all six cells).

**Two disclosures against interest.** (a) The conditioned SPP `ΔR²_nbr|own` on `P1` is 0.3252 /
0.2303 / 0.1014, close to but **not identical with** miso-236's `ΔR²_A` of 0.3246 / 0.2472 /
0.1140 — the denominator and the dof adjustment differ, as §1 says, and the two are never equated;
miso-236's own quantity is reproduced separately and exactly by §0's G-P2 leg. (b) **South's
neighbour block WOULD read QUANTITY-SIDE under this conditioning** (`rho` 1.038 / 1.016 / 1.039 on
increments 0.1203 / 0.0741 / 0.0545, all clearing the floor). **It does not, and cannot**: the
gated verdict is the pre-registered unconditional one and the ADDENDUM fixed in advance that this
leg moves nothing. **South's neighbour-state route stays CLOSED** on miso-236's D-4 rule, which is
a statement about its **unexplained share** (0.8388 / 0.8853 / 0.8968 against a 0.75 floor) — a
different statistic, and one a 5–12 % conditional contribution corroborates rather than
contradicts. Rule 28(a): corroborated, **never re-tested**.

## 6. Q-3 — what a better price representation reaches at all (REPORTED, NOT GATED, NEVER A TARGET)

| seam | year | `R²(P1)` | `R²(P2)` | `R²(P3)` | `P2 − P1` (inside the ladder's class) | `P3 − P1` |
|---|---|---:|---:|---:|---:|---:|
| **PJM** | 2023 / 2024 / 2025 | 0.0576 / 0.0700 / 0.0374 | 0.1166 / 0.1127 / 0.1024 | 0.2218 / 0.2643 / 0.1968 | 0.0591 / 0.0427 / 0.0650 | **0.1642 / 0.1943 / 0.1594** |
| **SPP** | 2023 / 2024 / 2025 | 0.0016 / 0.0003 / 0.0024 | 0.0037 / 0.0246 / 0.0168 | 0.0825 / 0.1142 / 0.0256 | 0.0021 / 0.0244 / 0.0144 | **0.0809 / 0.1139 / 0.0232** |
| South | 2023 / 2024 / 2025 | 0.0007 / 0.0034 / 0.0197 | 0.0285 / 0.0133 / 0.0346 | *(≡ P2)* | 0.0278 / 0.0099 / 0.0150 | 0.0278 / 0.0099 / 0.0150 |
| Manitoba | 2023 / 2024 / 2025 | 0.0987 / 0.0349 / 0.0393 | 0.1264 / 0.1048 / 0.0461 | *(≡ P2)* | 0.0277 / 0.0698 / 0.0068 | 0.0277 / 0.0698 / 0.0068 |

On PJM, **most of the price-representation headroom is in the separate legs, not in the step
function of the spread** (`P3 − P2` = 0.1052 / 0.1516 / 0.0944 against `P2 − P1` = 0.0591 / 0.0427
/ 0.0650) — the model's merit test sees the difference alone, and that restriction costs more than
the linearity does. **Declared un-targetable before it was computed** (ADDENDUM §A's rule and
PREREG §4): no successor may size, scale or tune any mechanism to make a modelled statistic land
on a value here (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`). It says whether a route is worth
chartering at all, never what value to give anything.

## 7. What is handed forward — NAMED, and NOT CHARTERED

No lever is proposed and nothing here licenses one. The PREREG fixed that before the numbers.

1. **THE SPP NEIGHBOUR-STATE OBJECT SURVIVES ITS FORM TEST AS A QUANTITY-SIDE ONE.** The
   handoff's first question is answered on a pre-registered rule: a better neighbour price
   representation does **not** reach it (78–82 % survives `P3`, 95–101 % under miso-236's
   conditioning), so miso-236 §5.1's object is a **quantity-side measured input** and the §6.3
   alternative is refuted for SPP. **This does not charter one**, size one, or name a field, and
   miso-236's sizing (328.6 / 341.7 / 207.5 MW) remains explicitly un-targetable. A successor
   writing that charter still owes the mechanism's own form, its window and its forward story
   (rule 17 `[R-FLOOR-WINDOW]`), and rule 19 `[R-ONE-MECH]` requires it to enumerate what already
   moves the SPP seam before adding anything.
2. **HANDOFF ITEM 2 IS ANSWERED AND ITS PREMISE IS REFUTED, WHICH REDIRECTS IT.** MISO's own state
   is **not** an unused input on PJM, South or Manitoba — the model **over**-transmits it (1.4–3.6×
   on PJM) and, on PJM, with a large stable response of a sign the real seam does not carry. The
   "unused input" reading holds **only on SPP** (0.07–0.28×). The item as filed is closed; what
   replaces it is two different objects — an **over**-transmission defect on PJM (§4) and an
   **under**-transmission one on SPP (§3b).
3. **ITEM 3 HAS ITS FIRST CAUSE AND IT IS HALF OF ONE.** Purging own state removes **36 / 62 /
   50 %** of the model's excess PJM price alignment (`phi`, PARTIAL on the pre-registered bar).
   Roughly half the defect miso-236 left uncaused is now attributed; roughly half is not. A
   successor should measure the remainder, not re-test this.
4. **PJM's NEIGHBOUR CHANNEL IS SUBSTANTIALLY A PRICE OBJECT WHERE SPP's IS NOT** (§2, §5:
   59 / 63 / 74 % absorbed by `P3`). Reported; PJM reads MIXED under both conditionings and
   nothing moves.
5. **SOUTH AND MANITOBA ARE UNCHANGED.** South's neighbour-state route stays **CLOSED** (miso-236
   D-4), corroborated here on a further statistic and never re-tested; South stays routed upstream
   to the South-gas price-out lane (`gas_marginal_commodity_pricing` **O** /
   `gas_variable_transport` **O**, owner-court). `miso_manitoba_seam` stays **CLOSED as
   already-armed** (miso-235 §3) and is not re-opened; its determinism question (miso-236 §5.3)
   is untouched.
6. **Nothing licenses a re-derive or a damping factor** on the PJM or SPP `delta_k` ladders, which
   are derived, frozen and pinned to their derives by test (rule 23 `[R-FROZEN-DERIVE]`). **This
   binds even though §6 measures real price-representation headroom**: PREREG §5.2 and ADDENDUM §A
   both fixed it in advance, and a factor swept against any residual is the rule 1 `[R-STRUCT]`
   fitted mechanism.
7. **C3c** is untouched and stays the designated frontier (2026-07-20). Its charter needs a new
   admissible measured identification **and an owner ruling**; no LP is authorized there and none
   was sought.
8. **The CC_REGULAR 2024→2025 shape emergence** is untouched and stays where miso-234 filed it.

## 8. Non-claims

1. **This session solved nothing.** No screen was run, so nothing here has been through a
   structural gate, and no number is a solve result.
2. **`R²` here is descriptive variance share, not skill.** There is no out-of-sample statistic in
   this session at all — miso-236's fragility leg is not re-run and is not restated as one.
3. **`ΔR²_S|P1` is not miso-236's `ΔR²_A`** (§1, ADDENDUM §0), disclosed before the numbers were
   read and never equated; miso-236's own quantity is reproduced separately and exactly (§0).
4. **`P2` and `P3` are MEASUREMENT INSTRUMENTS, not proposed mechanisms.** A ventile dummy block
   is not a candidate and this session proposes none; the ADDENDUM §A purge is a diagnostic
   projection and nothing here proposes removing a term from the model.
5. **The model-side residual is a RECONSTRUCTION number** (miso-235's four-seam form, harness
   `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839), labelled as one in every table. 2024
   remains the loosest year and is also where PJM's neighbour `rho` reads 0.406; the two are
   reported together and neither explains the other.
6. **The PJM seam's neighbour-state census is 82–84 %, not 100 %** (IESO has no US-BA record), and
   PJM's MIXED verdict is measured on that partial cover.
7. **South's ADDENDUM §B numbers do NOT re-open its closure** and are disclosed as such against
   interest (§5b).
8. **`phi` is meaningful for PJM only**; the other three seams' values divide by a near-zero gap
   and are disclosed as meaningless rather than quoted.
9. **No verdict moves anywhere in the matrix**, in either direction. Evidence only.
10. **MISO has no failing gate**, and nothing here proposes trading a passing one. There is no
    rubric failure anywhere in the program and this session did not invent one.

## 9. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; nothing was proposed or selected, and
§6's headroom and §4's `phi` were both declared un-targetable in advance. Rule 12 `[R-PARALLEL]`:
no LP was solved; nothing ran on CI. Rule 13 `[R-MEASURED]`: measurement only; no measured outcome
enters any solve, and PREREG §2c fixed both the admissibility argument and the named inadmissible
forms (the DIBA interchange series itself, neighbour Net Generation as a whole, and any noise term,
variance inflator, damping factor or tuned scalar) **before** the numbers. Rule 14 `[R-ACCURATE]`:
no input changed. Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registered or pruned; MISO
keeps exactly one registered run and the keeper's `hourly/` sidecars stay committed. Rule 19
`[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22 `[R-HOLDOUT]`:
2023–2025 only; MISO holds no `complete` marker and no out-of-training year was solved, scored or
registered. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run; §7.6 restates the freeze and binds §6 to
it. Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section and
lane only. Rule 27 `[R-PUSH]`: every pushed blob verified against local. Rule 28(a): the queue
items taken are the handoff's item 1 first question with its item 2, which one instrument answers;
the standing adjudications this touches (`miso_south_firm_export_block` **G**,
`miso_south_export_ladder_rt_tail` **R**, `miso_manitoba_seam` closed-as-armed,
`vre_reference_rate_curtailment_grossup` **K**, `internal_congestion_split` **G**) are
**corroborated, never re-tested**. Rule 28(b): no verdict moves; evidence appended in-session.
Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0 first, and it **answered the successor's
form question, refuted a handoff premise and supplied half a cause for an uncaused defect before a
single LP minute was spent**, which is the outcome the clause exists to produce.
