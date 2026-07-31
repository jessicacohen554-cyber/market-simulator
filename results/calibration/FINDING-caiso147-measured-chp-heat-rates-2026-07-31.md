# FINDING — caiso-147 `measured_chp_heat_rates` for CAISO

**Lever:** mechanism-matrix §5.2 CAISO lever-queue **item 7**,
`measured_chp_heat_rates` (cells `UUUKUU`; `K` in MISO at miso-99, CAISO `U`).
**Pre-registration:** `PREREG-caiso147-chp-heat-rates-2026-07-31.md`, committed
and pushed at `b1b5e5f` **before either arm solved**.

**Base keeper:** `2026-07-31-caiso146-ct-heat-rates` (CALIBRATED-WITH-CAVEATS,
0 FAILs, 2 ledgered non-protective caveats, protective 0/1). CAISO holds **no**
rule-22 calibration-complete marker; this session solved **2023 2024 2025 only**
and wrote no marker.

Rule 25 `[R-ISO-SCOPE]`: MISO's `K` transfers nothing. Every number below is
measured on CAISO's own fleet from CAISO's own data.

---

## §A — the mechanism, and what it replaces **in CAISO specifically**

The measured rate is eGRID's own published CHP heat-input allocation added back
on the same net denominator:

```
heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN
```

`PLHTIAN` is heat input allocated to electricity — the incumbent
`PLHTRT = PLHTIAN / PLNGENAN` is exactly that over the same denominator — and
`CHPCHTI` is the useful-thermal allocation eGRID removed. `PLNGENAN` is already
**net** generation, so **no gross-to-net factor is involved**, which is why this
route works where the CEMS route was blocked (`FINDING-miso98` §6.1). Zero
fitted parameters (rule 24 `[R-REGISTRY]`).

**In CAISO the delta is not the one MISO measured.** CAISO is one of the two
ISOs in `fleet.arrays.CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` (CAISO, PJM), so a
covered CAISO plant's incumbent is not eGRID's credited rate — it is that rate
times a **hand factor**: `x1.8` for a CT_CHP under 8.0 MMBtu/MWh,
`max(x1.15, 6.3)` for a CC_CHP under 6.0. The swap here is therefore **hand
factor → published measurement**, a rule-21/24 win (an off-registry hand number
retired for a citable one) on top of the rule-14 accuracy win.

Plants the measurement does not reach **keep the hand factor untouched**
(`apply_measured_chp_heat_rates` returns a `skip_ids` set that
`_correct_chp_steam_credit_hr` honours, rule 19 `[R-ONE-MECH]`). This mechanism
does not remove the hand factor from CAISO; it supersedes it only where a
published measurement covers.

---

## §B — the derive was blinded by the hand factor, and the fix (no LP)

**The shipped derive gave CAISO 14 `ok` rows / 1,117 MW, with
`basis_mismatch = 65`.** That is not a data wall — it is a gate misfiring, and
the diagnosis is `scripts/probes/_caiso147_chp_basis_gate.py`.

`_flag`'s `_BASIS_TOL` check asks *"is the incumbent rate this eGRID row, or a
boundary repair / `HEAT_RATE_BINS` fallback?"* and compared eGRID's **credited**
rate against the **shipped** model rate. In a hand-factor ISO the shipped rate
*is* the credited rate times 1.8 or 1.15, so **every hand-corrected plant reads
as a mismatch.** Measured ratio of shipped-to-credited across the excluded rows:

| class | n | median ratio | matches |
|---|---|---|---|
| CT_CHP | 56 | **1.800** | `CAISO_EOR_TOPPING_FACTOR` exactly |
| CC_CHP | 9 | **1.150** | `CAISO_CHP_CC_STEAM_CREDIT_FACTOR` exactly |

Loading the fleet twice — as shipped, and with the hand factor neutralised —
partitions the exclusions exactly:

> **59 of the 65 `basis_mismatch` rows — 3,089 of 3,186 MW — were excluded by
> the hand factor alone.** The remaining **6 rows / 96.5 MW** are the genuine
> boundary-repair / bin-fallback mismatches the gate was built to catch (Fresno
> Cogen, SDSU, UC Santa Cruz, CSUF Trigeneration, Broadridge, Sierra Nevada
> Brewing).

So the gate was excluding **precisely the population the mechanism exists to
fix**, leaving only the 14 plants the hand factor never touched. The artifact
would have been a swap applied everywhere *except* where caiso-128 §3 says the
error is.

**The fix.** Compare the credited rate against the incumbent **at the seam where
the swap actually happens** — after the eGRID join and the boundary repairs,
before the hand factor. That is exactly what `apply_measured_chp_heat_rates`
overwrites, since it runs first and hands the hand factor its `skip_ids`.
Implemented as `basis_heat_rates()` in the derive plus a default-`True`
`apply_chp_steam_credit_correction` kwarg on `load_fleet_from_csv` (the model
always leaves it `True`; only the derive passes `False`, and the binned-fleet
side cache is left untouched in that mode so the committed cache always reflects
the fleet the model prices with).

**Governance of the fix:**

- **Zero fitted parameters.** It introduces no number. `_BASIS_TOL`,
  `_MAX_THERMAL_SHARE` and the physical bands are untouched.
- **Not rule-23 `[R-FROZEN-DERIVE]`.** This is CAISO's *first* derive; the
  defect was found by code inspection and a no-LP probe **before any solve
  existed**, so no residual was visible and none could have been fitted to.
- **Not rule-25 and not on the caiso-146 DO-NOT-REDO list.** It is ISO-generic
  (see through the hand factor wherever it exists), not a CAISO-scoped
  multiplier, band or exclusion.
- **The gate keeps its discriminating power** — the 6 genuine mismatches still
  fail it, and every physics gate still applies downstream. The exclusion count
  did not fall to zero; it moved to the gate that should own it
  (`not_unfired_topping` 1 → 44, because those rows previously short-circuited
  at `basis_mismatch` before the physics check could see them).
- **MISO verified untouched.** No hand factor there, so `basis == model` on
  every MISO row; the re-derived MISO artifact is identical on **every applied
  value** (only the deliberately-edited provenance string differs) and its
  applied population is still **6,732 MW**, exactly miso-99's committed figure.

**This is a latent defect in PJM too** — PJM is the other hand-factor ISO and
has never derived this artifact. Anyone taking `measured_chp_heat_rates` into
PJM gets the fixed gate automatically; that is noted, not acted on here
(rule 25).

---

## §C — the artifact (STEP 1, no LP)

`data/raw/_processed-legacy/chp_power_only_heat_rates_CAISO.csv`, eGRID2023
(`PLNT23` — the vintage the model's own `heat_rate` is joined from, so the delta
is "eGRID's CHP allocation, undone" with basis, source, vintage and denominator
all held fixed). 92 (plant, class) rows, 4,668.6 MW of CHP.

| flag | rows | MW | meaning |
|---|---|---|---|
| `ok` (applied) | **30** | **2,371.8** | measurement applies |
| `not_unfired_topping` | 44 | 1,914.4 | `thermal_share > 0.50` — boiler-first, excluded on physics |
| `basis_mismatch` | 6 | 96.5 | genuine boundary repair / bin fallback |
| `above_physical_band` | 3 | 251.1 | corrected rate outside the class band |
| `no_chp_credit` | 3 | 19.4 | eGRID applied no credit — nothing to add back |
| `no_egrid_row` | 6 | 15.4 | plant absent from the eGRID vintage |

**Coverage — energy reach is what matters, not capacity:**

| class | rows | capacity | **metered CAMPD energy (2023)** |
|---|---|---|---|
| CC_CHP | 11/21 | 1,819/2,707 MW (67.2 %) | **7.490/7.490 TWh — 100.0 %** |
| CT_CHP | 19/71 | 553/1,962 MW (28.2 %) | 0.146/0.413 TWh — 35.4 % |

CC_CHP — the material class at 3.7–4.3 % of generation — is covered on
**100.0 %** of its own metered energy; the uncovered plants sit below the
Part-75 boundary and meter nothing.

**Validation.** `PLHTIAN + CHPCHTI` reproduces independently metered CAMPD
annual heat input within 1 % on **13 of 13** covered plants, median ratio
**1.00000**. MISO's was 19/22. **CAISO's validation is better**, so the charter's
stop-condition (validation materially worse than miso-99's) was not triggered.

**Direction — two-sided, and opposite between the classes** (cap-weighted,
shipped → measured):

| class | shipped | measured | delta | cheaper | dearer |
|---|---|---|---|---|---|
| CC_CHP | 6.779 | 8.108 | **+1.330 (+19.6 %)** | 1 row / 525 MW | 10 rows / 1,294 MW |
| CT_CHP | 11.935 | 10.196 | **−1.739 (−14.6 %)** | 10 rows / 389 MW | 9 rows / 164 MW |

CC_CHP was **under**-costed and CT_CHP **over**-costed. This is caiso-128 §3's
"a universal hand factor is wrong in both directions at once" measured directly
on CAISO's own fleet, and it is the substantive case for a published per-plant
measurement over a single ISO-keyed factor. 28 of 30 rows move > 0.5 MMBtu/MWh.

**Stated limitations (pre-registered, not discovered after the fact):**

- **CT_CHP coverage is thin and adversely selected** — 35.4 % of metered energy,
  and the covered plants are the *less* steam-credited ones (cap-weighted
  credited 7.167 covered vs 6.377 excluded; thermal share 0.288 vs 0.526).
  CT_CHP is 0.72–0.74 % of model generation so this is immaterial to the
  determination either way, but it is **not** a clean identification and is not
  claimed as one.
- **The `not_unfired_topping` exclusion is large and correct** — 44 rows /
  1,914 MW (41 % of CHP capacity), median `thermal_share` 0.598 against the 0.50
  EPA-envelope ceiling, and the power-only rate those plants would otherwise
  take has median 14.52 and max **58.4** MMBtu/MWh: nonsense for an offer rate,
  exactly the boiler-first case the gate exists to reject. They keep the
  existing eGRID → hand-factor chain.

---

## §D — the gate framing, corrected against the scorer's source

The session charter stated that CC_CHP, being ~4 % of load and so above the 2 %
materiality floor, "IS gated" by C7/C8 unlike caiso-146's CT_PEAKER. **That is
not what the scorer implements**, and the correction matters for how this run is
read:

- **C7 / D-1:** `legitimacy_diagnostics.D1_GATED_CLASSES` =
  `CT_PEAKER, ST_GAS, COAL*`. CHP is absent; the keeper's own rows read
  `"gated": false`.
- **C8 / D-2:** `D2_EXEMPT_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP", "nuclear")`.

Both carry the same rationale in source: *"host-steam-pinned duty."* The
exemption is **by explicit class list, not by materiality** — so CC_CHP's
0.44–0.47 `chp_steam` forced share is not gated by C8 no matter how large the
class is, and the materiality floor never comes into it.

Consequently this finding **reports CHP's D-1/D-2 numbers as diagnostics and
never quotes them as a passed gate**, and places the binding protective gates on
the classes that absorb the displaced energy — CT_PEAKER (C7-gated, C8
peaker-capped at 0.15), ST_GAS and COAL.

*(Noted for a future session, not acted on here: CT_CHP's 2025 `profile_r` is
**0.393** in the incumbent keeper — far below the 0.80 threshold — and is
ungated. A latent shape limitation this session inherits and does not create.)*

---

## §E — the A/B result

Two arms, single flag, both replays of the caiso-146 keeper at the same HEAD,
solved concurrently (rule 12), **2023 2024 2025 in one invocation each**
(rule 16). The control is a **same-HEAD zero-delta replay**, not the keeper's
committed bytes — caiso-146 measured the caiso-139 keeper drifting up to 3.2 GW
on a class-hour at HEAD, so committed bytes are not a clean baseline.

Mechanism verified **live first** (the nyiso-89 §4a check, prereg reject #4):
arm B logs `measured power-only CHP heat rates applied to 57 generator(s) across
30 (plant, class) pair(s)` — matching the artifact's 30 `ok` rows exactly — and
arm A is silent. Max |Δ| on a CHP class-hour: **229.8 / 278.9 / 144.7 MW**
(CC_CHP) and 111.5 / 104.0 / 94.1 MW (CT_CHP), all far above the 50 MW inertness
floor. **Not inert.**

**Class energy, TWh (control → armed), against the committed benchmark:**

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **CC_CHP** | 9.025 → **8.353** (−0.673) · 117 → **108 %** | 8.126 → **7.337** (−0.789) · 120 → **108 %** | 7.754 → **7.317** (−0.438) · 108 → **102 %** |
| CC_REGULAR | 48.429 → 48.933 (+0.504) · 93 → **94 %** | 42.905 → 43.554 (+0.649) · 93 → **95 %** | 36.376 → 36.763 (+0.387) · 90 → **91 %** |
| CT_PEAKER | 1.726 → 1.786 (+0.059) · 42 → 43 % | 0.634 → 0.656 (+0.022) · 15 → 15 % | 0.455 → 0.465 (+0.010) · 19 → 20 % |
| CT_CHP | 1.549 → 1.578 (+0.029) · 73 → 74 % | 1.535 → 1.546 (+0.012) · 76 → 77 % | 1.523 → 1.525 (+0.002) · 115 → 115 % |
| import | 35.894 → 35.978 (+0.084) | 40.220 → 40.318 (+0.098) | 41.435 → 41.479 (+0.044) |
| **TOTAL** | 208.592 → 208.596 | 214.088 → 214.093 | 208.141 → 208.145 |

Total generation moves only **+0.003 / +0.006 / +0.004 TWh** (~0.002 % of a ~210 TWh system) — **pure reallocation**, and
**no material class moves away from actual.** (The only class that does is
ST_GAS, 515 → 529 % in 2024 on a **0.3 %-of-load** class the rubric skips as
immaterial; reported for completeness.)

**All three pre-registered predictions confirmed:**

- **P1 — CC_CHP falls.** Predicted down from 117/120/108 %, magnitude
  0.3–1.5 TWh/yr. Delivered **−0.673 / −0.789 / −0.438 TWh**, to
  **108 / 108 / 102 %**. Inside the predicted band in all three years.
- **P2 — CT_CHP barely moves despite getting 14.6 % cheaper.** Predicted
  |Δ| < 0.15 TWh/yr on the grounds that 95–97 % of the class is already pinned
  at its `chp_steam` floor, leaving almost no economic headroom. Delivered
  **+0.029 / +0.012 / +0.002 TWh.** This was flagged in advance as the
  prediction most likely to be wrong; it held, which **independently
  corroborates the D-2 floor attribution** — the class really is floor-bound,
  not economically dispatched.
- **P3 — the displaced energy goes to CC_REGULAR and/or `import`.** Delivered:
  CC_REGULAR takes 75–82 % of it, `import` most of the rest, both moving toward
  actual.

**Rubric verdicts — every criterion identical, scored control vs armed on the
same basis:**

| criterion | control | armed |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C2 system volume | PASS | PASS |
| C3a mean LMP | FAIL\* | FAIL\* |
| C3b price duration/shape | PASS | PASS |
| C3c price tail | FAIL\* | FAIL\* |
| C4 dispatch correlation | PASS | PASS |
| C7 diurnal shape (D-1) | PASS | PASS |
| C8 forced share (D-2) | PASS | PASS |

\* Both arms scored **unattested** for the comparison (the caiso-146 control was
handled the same way), so the two ledgered gates show as raw FAILs. With the
attestation carrying the owner's caiso-145 ledger, the armed arm scores
**CALIBRATED-WITH-CAVEATS: 0 FAILs, C3a + C3c ledgered (the same 2 of 3
non-protective slots, no new slot spent), protective 0/1, C6/C7/C8 PASS.**

**The two ledgered caveats:**

- **C3c — BIT-IDENTICAL** in both arms and to the caiso-146 keeper: model 0 h vs
  RT actual 47 h / 35 h. The CHP re-price buys **zero** tail hours.
- **C3a-2025 — +11.0 % → +11.2 %**, a **0.2 pp ADVERSE** move, **inside** the
  1.0 pp materiality trigger fixed in prereg §7, so no leave-one-year-out
  re-scoring was required. Measured directly on the bundles' own sidecars, CA
  load-weighted λ moves **$54.88 → $55.02 / $36.99 → $37.14 / $38.27 → $38.37**
  (+$0.134 / +$0.150 / +$0.098). The direction is expected and mechanical:
  pricing a ~4 %-of-generation class at its true (dearer) rate makes the
  marginal hour clear fractionally higher. **Reported, never tuned toward**, and
  per rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]` not a reason to revert an
  accurate published input.

---

## §F — protective gates, and one structural fact worth stating plainly

**The binding gates — the classes that ABSORB the displaced energy — are
unchanged:**

| gate | control | armed | threshold |
|---|---|---|---|
| CT_PEAKER C7 `profile_r` | 0.885 / 0.936 / 0.864 | 0.881 / 0.934 / 0.864 | ≥ 0.80 |
| CT_PEAKER C7 `cv_ratio` | 1.613 / 1.805 / 2.172 | 1.623 / 1.817 / 2.178 | ≥ 0.50 |
| CT_PEAKER C8 forced share | 0.0016 / 0.0055 / 0.0007 | 0.0016 / 0.0054 / 0.0007 | ≤ 0.15 |

ST_GAS's raw D-1 rows read FAIL in 2024/2025 — **in both arms, bit-identical**
(0.229 → 0.229, −0.032 → −0.031). It is a pre-existing condition of the incoming
keeper, it is immaterial-skipped by C7 (0.1–0.6 % of load), and this lever
neither causes nor changes it.

**C7 shape improves markedly on the classes actually repriced** (reported as
diagnostics per §D, never as a passed gate):

| | control | armed |
|---|---|---|
| CT_CHP `profile_r` | 0.817 / 0.801 / **0.393** | 0.959 / 0.937 / **0.852** |
| CT_CHP `cv_ratio` | 0.006 / 0.000 / 0.000 | 0.193 / 0.103 / 0.076 |
| CC_CHP `profile_r` | 0.968 / 0.969 / 0.988 | 0.983 / 0.982 / 0.989 |

The CT_CHP-2025 `profile_r` of **0.393** flagged in §D as a latent ungated shape
defect rises to **0.852**, and both CHP classes' near-zero off-peak variability
moves toward measured. The mechanism did not merely move a level; it made the
classes' *diurnal shape* more like the real ones.

**The one structural fact that cuts the other way, stated rather than buried:**
CC_CHP's `chp_steam` forced share **rises 0.435 / 0.470 / 0.461 → 0.557 / 0.629
/ 0.592**. This is the arithmetic consequence of the correction working — the
class contracts toward a *fixed, measured* steam floor as its economic tranche
is correctly priced out of merit, so the floor becomes a larger share of a
smaller class. No gate is engaged (CHP is C8-exempt by class, §D), and the floor
itself is the measured WP-3 steam-following level, not a fitted number. But
**more of CC_CHP's dispatch is now floor-determined than before**, and a future
session revisiting CAISO CHP should know that.

---

## §G — determination and DO-NOT-REDO

**PROMOTED. New keeper: `2026-07-31-caiso147-chp-heat-rates`**,
CALIBRATED-WITH-CAVEATS, 0 FAILs, 2 of 3 non-protective ledgered slots
(unchanged — the owner's caiso-145 act carried forward with magnitudes
re-measured, **no new disposition created**), protective 0/1.
Control: `2026-07-31-caiso147-control-zerodelta`.

CAISO holds **no** rule-22 calibration-complete marker. This session solved
2023/2024/2025 only and wrote **no** marker.

**Binding on successors:**

1. **DO NOT re-derive `chp_power_only_heat_rates_CAISO.csv` against a residual.**
   Rule 23 `[R-FROZEN-DERIVE]`: it re-derives only when EPA publishes a new
   eGRID vintage, and that commit must cite the data change.
2. **DO NOT add a CAISO-scoped CHP heat-rate multiplier, band or exclusion.**
   The `_MAX_THERMAL_SHARE` ceiling, the physical bands and `_BASIS_TOL` are
   definitional and frozen; the hand factor that this lever retired is exactly
   the kind of number not to reintroduce (rules 21/24/25).
3. **DO NOT re-open the `not_unfired_topping` exclusion as a coverage lever.**
   Those 44 rows / 1,914 MW are boiler-first cogens whose total-fuel-per-MWh
   reaches 58.4 MMBtu/MWh — the gate is physics, not conservatism.
4. **DO NOT quote CHP C7/C8 numbers as passed gates.** CC_CHP and CT_CHP are
   exempt from both by explicit class list, *not* by materiality (§D). A CHP
   class above the 2 % floor is still ungated.
5. **DO NOT treat the C3a-2025 +0.2 pp as a defect to be closed.** It is the
   mechanical consequence of pricing a class correctly, it is inside the
   pre-registered trigger, and C3a-2025 remains the owner's ledgered caveat on
   the caiso-141 A2 data wall — reopened only by non-public hourly PS data.
6. Everything in `FINDING-caiso146` §G, `FINDING-caiso144` §G, caiso-143 §H,
   caiso-142 §K, caiso-141, caiso-138 §G, caiso-137b §6, caiso-131 §10 remains
   binding and untouched by this session.

**Open leads this session created but did not act on (rule 25 — each needs its
own ISO's session):**

- **The basis-gate defect is latent in PJM**, the other hand-factor ISO, which
  has never derived this artifact. A PJM session takes the fixed gate
  automatically.
- **CT_CHP's coverage in CAISO is thin and adversely selected** (35.4 % of
  metered energy, covered plants systematically *less* steam-credited). The
  class is 0.7 % of generation so it does not matter for the determination, but
  it is not a clean identification and a future CAISO session should not treat
  it as one.
- **Latent D-2 vs dashboard basis inconsistency (found by the caiso-147 keeper
  audit, NOT caused by this lever, not acted on).** `legitimacy_diagnostics.json`'s
  D-2 `class_total_twh` for **CT_PEAKER** does not match the payload's
  `gmModel` / C1-scored class total — keeper 2023 reads 1.7981 TWh in D-2 vs
  1.7827 TWh in `gmModel`, a ~0.9 % gap — while CC_CHP, CC_REGULAR and CT_CHP
  agree closely. Every number quoted in this finding and in the keeper note uses
  the `gmModel` / C1-consistent basis, so no claim here is affected, and the C8
  gate is nowhere near its cap either way. But the two bases should agree, and a
  future session should find out why they don't. It is a scorer/pipeline
  question, not a CAISO calibration one.

- **CC_CHP is a `pinned` class in the C1 free-class score** (`excluded_from_free`
  alongside ST_CHP), so its 117 → 108 % improvement does **not** show up in the
  free-class headline (8/8 both arms). The gain is real and is in the `all`
  12/12 count; it is simply invisible to that particular summary statistic.
