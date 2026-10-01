# FINDING — miso-155: the P0 is now **READ**, and the residual was **THE MISSING FLOORS**. Branch **C-FLOOR**: the instrument clears **3 of 3** and MISO's CT volumes are measurable to **~1 %**.

**Session** miso-155 · **ISO** MISO · **Date** 2026-08-13 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED** ·
**Model** `claude-opus-5`.

**PREREG** `results/calibration/PREREG-miso155-p0-exact-commitment-instrument-2026-08-13.md`,
pushed at **`a920c85`**, blob **`07b12e5aa081de79f15adebc4ac8321e0233d0d5`**,
**verified byte-identical against the FETCHED remote ref** before any
adjudicating statistic was computed (rule 27 `[R-PUSH]`).

**Run registered (rule 15 `[R-DASHBOARD]`)**: `2026-08-13-miso-155-control-p0`
(bundle `miso155_p0_C`, years **2023 / 2024 / 2025** in one bundle, rule 16
`[R-ALLYEARS]`).

**Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. MISO holds neither `complete` nor
`final`. No holdout year was read, solved, scored or registered.

**BRANCH TAKEN: C-FLOOR** (PREREG §6). **NO CT offer-LEVEL lever is applied,
no `ScenarioConfig` field is added, no matrix cell verdict is minted** — no
mechanism was armed or tested. **Keeper unchanged.**

---

## 1. Headline

miso-154 left this lane with an instrument whose own uncertainty (18–22 pp)
was **wider than the ±10 % bar it was gated on**, and named the cause: no
committed P0 pass. This session built the missing artifact, read the model's
own P0, and found that **the P0 was never the problem.** The problem was that
the reconstruction had never seen MISO's **CT reliability floors** at all.

| year | published baseline (`mc_base`) | miso-154 **PROXY** | **L1X** exact P0+band | **L1F** floors read | bar ±10 % |
|---|---|---|---|---|---|
| 2023 | +21.99 % | −13.21 % | **−13.91 %** | **−0.89 %** | **PASS** |
| 2024 | +22.14 % | −7.54 % | **−8.66 %** | **−0.26 %** | **PASS** |
| 2025 | +23.72 % | −4.47 % | **−5.53 %** | **−0.52 %** | **PASS** |

**CT volumes are now measurable to ~1 %, against ±13 pp worst case at
miso-154 and ±22–24 pp at miso-153.** The lane's blocking dependency —
*"CT volumes are currently unmeasurable"* — is **CLOSED**.

Two validity gates were cleared **before** any of the above was computed:

* **V1 PASS.** The baseline leg reproduces miso-153's published T-6b at
  **+21.990 / +22.140 / +23.722 %** against the published **+21.99 / +22.14 /
  +23.72 %** — deltas **+0.000 / −0.000 / +0.002 pp** — on the published
  `n_gen` **2929 / 2923 / 2923**.
* **V2 PASS.** The control is a faithful keeper reproduction: **2025 is
  BIT-IDENTICAL** (0 of 70,080 zone-hour price cells differ; mean delta
  −5.9e−17), 2024 differs in **8 of 70,080** cells (mean LMP −0.00027 %), 2023
  in **1,220 of 70,080** (mean LMP −0.0020 %, max |Δ| $3.50 — marginal-tie
  reshuffling). CT_PEAKER annual energy 14.0792 vs 14.0807 TWh in 2023 and
  **exact** in 2025. **S-NOREPRO does not fire.**

---

## 2. THE FINDING — the reconstruction was blind to MISO's CT floors, and a pre-registered trap is what caught it

**This was not measured directly. It was forced by trap T-3** — *"disbelieve
clean zeros: any exact 0.0 gets a second, different derivation."*

The PREREG's §4.2 admissibility test, written against the probe's own
re-assembled `arrays.min_gen`, returned out-of-merit floored CT energy of
**exactly 0.000** in all three years. Under T-3 that zero was not accepted. The
second derivation — the solve's **own committed floor array**
(`floors/<year>_P1.npz`) — refuted it outright:

| year | solve's CT floor | probe's re-assembled CT floor | solve fleet floor | probe fleet floor |
|---|---|---|---|---|
| 2023 | **2.8457 TWh**, 158 rows, max 144.605 MW | **0.0 MWh** | 117.4 TWh | 113.0 TWh |
| 2024 | **2.8773 TWh**, 150 rows, max 144.605 MW | **0.0 MWh** | 120.7 TWh | 116.3 TWh |
| 2025 | **2.8677 TWh**, 153 rows, max 144.605 MW | **0.0 MWh** | 121.9 TWh | 117.4 TWh |

The probe's re-assembled floor is **non-zero fleet-wide** (2023: 113.0 TWh over
1,208,529 cells) and **exactly zero on every one of the 733 CT_PEAKER rows**.
`_miso134.build_year` stops before the reliability-floor registry the
production pipeline applies (the solve logs *"reliability floor — 12 enabled
limb spec(s) applied from RELIABILITY_FLOOR_REGISTRY"*), so **every
reconstruction built on that chain — miso-152's, miso-153's T-6b, miso-154's
L1 — has been measuring a CT fleet with no reliability floors.**

With the floors READ instead of re-derived, the pre-registered admissibility
gate passes on its own terms — out-of-merit floored CT at the top-200 hours is
**13.02 / 8.40 / 5.02 %** of control CT top-200 energy against the
pre-registered **≥ 5 % in ≥ 2 of 3 years** — and L1F clears **3 of 3**.

**Stated plainly because it governs how much this session may claim:** the
floor correction is an **instrument-defect repair forced by a pre-registered
trap**, not a basis substitution chosen after seeing the answer. It was made
before the corrected L1F was evaluated, and the 5 % / 2-of-3 threshold is
**unchanged from the PREREG**. Reading the model's own floors is the same rule
14 `[R-ACCURATE]` move as reading its own P0.

### 2.1 It fixes the class miso-154 flagged as unreproducible, too

Per-class top-200 residuals under L1F, against miso-154's L1:

| year | CC_REGULAR | CC_CHP | CT_PEAKER | CT_CHP | **ST_GAS** | ST_CHP | COAL_FAMILY |
|---|---|---|---|---|---|---|---|
| 2023 | −3.35 % | −5.79 % | **−0.89 %** | −0.06 % | **−1.94 %** *(was −11.8)* | −0.55 % | +0.09 % |
| 2024 | −2.07 % | −0.00 % | **−0.26 %** | −0.00 % | **−1.34 %** *(was −17.0)* | −0.80 % | +4.92 % |
| 2025 | −0.01 % | −0.06 % | **−0.52 %** | −0.15 % | **−0.72 %** *(was −19.4)* | −0.07 % | +0.56 % |

miso-154 recorded `ST_GAS` at **−11.8 / −17.0 / −19.4 %** and attributed it to
a *construction limit* — "price-taking cannot dispatch an out-of-merit
must-run floor". That diagnosis was **right in kind and wrong in cause**: the
floors were not un-dispatchable, they were **absent from the instrument**.
Read them and ST_GAS lands at **−1.9 / −1.3 / −0.7 %**. Every thermal class is
now within 5.8 %, and six of seven within 2 % in 2025.

---

## 3. The P0 exactness — delivered, and SMALLER than advertised

The build works exactly as designed, and the honest report is that **it bought
about 1 pp, not the 18–22 pp its bound implied.**

| year | PROXY L1 | **L1X** (exact P0 + exact band) | move | miso-154's claimed T-9 span |
|---|---|---|---|---|
| 2023 | −13.21 % | **−13.91 %** | **−0.70 pp** | 21.7 pp |
| 2024 | −7.54 % | **−8.66 %** | **−1.12 pp** | 20.9 pp |
| 2025 | −4.47 % | **−5.53 %** | **−1.06 pp** | 18.4 pp |

**The T-9 span was an artifact of its own extreme bounds, not a measure of the
proxy's error.** Bounding an unknown by "no P0 runs at all" and "always on"
brackets it, but the true P0 sits **0.7–1.1 pp** from the price-taking proxy —
roughly **5 %** of the span that blocked the lane. That is the durable
methodological result: *a bound is not an uncertainty*, and miso-154's §4
limitation, though correctly derived, materially over-stated the doubt.

**S-INERT FIRED, in 2024 and 2025**, exactly as pre-registered: the exact and
proxy cap-weighted CT markups differ by **+0.476 %** and **+0.414 %** — under
the 1 % trigger. In 2023 they differ by **−4.795 %** ($4.5115 exact vs $4.7388
proxy). Per the PREREG's own instruction for this trigger: *the build still
ships (rule 14), but the finding says the limitation was over-stated.* It does.

**T-10 is likewise closed and was likewise smaller than bounded.** The exact
band series against the reconstructed one: top-200 means **0.6390 vs 0.6380**
(2023) and **identical to 4 dp** in 2024 and 2025; max absolute difference over
all 8,760 hours **0.30**. miso-154's 4.66–5.51 pp T-10 gap was measured against
the **v3 flat basis** (ratio ≡ 1.0), not against the exact v4 series — so it
never was the error in the v4 reconstruction it was read as. **The v3-vs-v4
question is now retired: the series is read, not chosen.**

---

## 4. The priors, scored — one confirmed, one confirmed-in-band-missed-in-centre, and a mechanism I got wrong

* **P-1 (direction): CONFIRMED 3 of 3.** L1X is colder than the proxy in every
  year.
* **P-2 (magnitude): band CONFIRMED 3 of 3, centre MISSED by ~6 pp in the WARM
  direction.** Registered bands [−28.98, −13.21] / [−24.11, −7.53] /
  [−18.65, −4.47], centres −20 / −15 / −11. Measured **−13.91 / −8.66 /
  −5.53** — inside every band, but pinned at the **warm edge** of each. I
  registered the expectation that *"L1X FAILS the ±10 % bar in 2023 with
  near-certainty and plausibly in all three years"*; on the gating leg 2023 did
  fail, but 2024 and 2025 cleared, and the C-FLOOR leg cleared all three.
* **P-3 (L1F): CONFIRMED.** Registered "3–15 pp hotter than L1X". Measured
  **+13.02 / +8.40 / +5.02 pp** — inside the band in all three years.
* **A MECHANISM I GOT WRONG, reported because it runs against my own
  reasoning.** P-1's stated mechanism was that the exact P0 cycles more →
  shorter runs → a **LARGER** markup. In 2024/2025 the exact markup is indeed
  marginally larger (+0.48 % / +0.41 %). **In 2023 it is 4.80 % SMALLER**
  ($4.5115 vs $4.7388) and the residual still went colder. So in 2023 the cold
  move is **not** a markup-magnitude effect — it comes from the *distribution*
  of the markup across tranches relative to price, which my prior did not
  describe. The direction was right for a reason I had partly wrong.

**No other surprise trigger fires.** **S-CEILING**: no year is colder than the
T-9 `never` bound (worst −13.91 % against −28.98 %). **S-WARMER**: L1X is
colder than the proxy in all three years, so it does not fire.
**S-NOREPRO**: V2 passes.

---

## 5. Traps — every counter-measurement, at full magnitude

| # | Counter-measurement | Result |
|---|---|---|
| **T-1** | Bundle repointed and asserted | **PASS** — repointed to `miso155_p0_C` on BOTH probe modules, asserted at import |
| **T-2** | Zero 3-argument `getattr(` added on the offer path | **PASS** — the one 3-arg `getattr` written during the build was removed before commit (`Generator.unit_id` is a required field, so a default could only mask a rename); `ruff` clean on all four touched files |
| **T-3** | Full suffix inventory; **disbelieve clean zeros** | **PASS — AND IT IS THE SESSION'S FINDING.** The 0.000 admissibility share was refused, given a second derivation, and **REFUTED** (§2) |
| **T-4** | Production types only | **PASS** — every array from `generators_to_fleet_arrays`; no `SimpleNamespace` |
| **T-5** | Carry-zone count == 6 | **PASS** — asserted; import nodes priced `+inf` |
| **T-6** | `weather_year` pinned per solve year | **PASS** — `dataclasses.replace(cfg, weather_year=y)` per year; V1's exact reproduction on all three years is its control |
| **T-7** | Markup magnitude, so an inert instrument can't hide | **REPORTED — S-INERT FIRES for 2024/2025** (§3) |
| **T-8** | Production markup, never a re-implementation | **PASS** — the surrogate-dispatch route keeps `compute_monthly_markup`; asserted `__module__` |
| **T-9** | *(retired by construction)* P0 proxy bounded | **CLOSED AND MEASURED**: the span was 18–22 pp, the actual proxy error **0.70 / 1.12 / 1.06 pp** |
| **T-10** | *(retired by construction)* band series approximated | **CLOSED AND MEASURED**: top-200 means agree to 0.001; max all-hours difference 0.30 |
| **T-11** | MISO's CT carries no min-run | **RE-CONFIRMED** on the control's own fleet |
| **T-12** | Bit-packing round-trip, partial final byte included | **PASS** — asserted elementwise in 5 parametrised unit tests (`hours ∈ {8, 24, 8759, 8760, 8761}`) and on real data: 2023 on-share 0.2714, 1,139 gens never on, 175 always on, **0 zero-`pmax` rows** |
| **T-13** | `pmax == 0` rows | **PASS** — 0 such rows in all three years, so the case is vacuous here (and the unit test covers it) |
| **T-14** | The flag must not perturb a solve | **PASS** — write-only by construction (the record is taken AFTER both LPs and read by nothing downstream; static trace reported), 6 unit tests on writer no-op/additivity, and **V2's bit-identical 2025** is the empirical proof at solve grain |
| **T-15** | The control is not the keeper | **PASS** — V2 (§1); `replay_keeper`'s STRICT `build_kwargs` reconstruction, single `--set` delta |
| **T-16** | Mixing the control's P0 with the keeper's `class_hourly` | **PASS** — every leg scored against the **control's own** `class_hourly` |
| **T-17** | Exact-vs-proxy confounded by control-vs-keeper drift | **PASS** — both legs run on the same control bundle (§3) |

---

## 6. NOT PRE-REGISTERED — labelled, with counter-measurements

1. **A fleet-size discrepancy between the reconstruction and the solve.** The
   probe assembles **2929 / 2923 / 2923** generators; the solve dispatched
   **2787 / 2788 / 2786**. Matched by `unit_id`: **2633 / 2627 / 2627**, leaving
   **296 probe-only rows carrying 1,865.7 MW** in every year — **all of them
   with an empty `plant_group` label**, and **solve-only** rows of 154 / 161 /
   159. **Counter-measurement, and it is why this does not disturb any number
   above: `CT_PEAKER` matches 733 of 733 with 0.0 MW probe-only in all three
   years.** The fleet-ALIGNED legs (every reconstruction masked to the units
   the solve actually carries) are therefore **identical to the unaligned ones
   to every reported digit** — `ALIGNED_baseline` +21.99 / +22.14 / +23.72 %,
   `ALIGNED_L1X` −13.91 / −8.66 / −5.53 %. Reported because the join was
   changed from positional to `unit_id` on account of it; a positional join
   would have silently attributed one unit's run pattern to another.
2. **Reading the floors from `floors/<year>_P1.npz`** (§2). Forced by T-3, made
   before the corrected leg was evaluated, threshold unchanged.
3. **The `--reuse-solved` exemption.** `--persist-p0-commitment` had to be added
   to `_REUSE_KWARG_EXEMPT`: it is write-only, so two runs differing only in it
   have byte-identical solves, but the eligibility check refused every year with
   *"solve kwargs differ"*. Without it the rule-12 per-year chain cannot reuse,
   and on MISO's per-plant LP that is the difference between fitting the box and
   OOM-ing. Its sibling `persist_p2_state` has the same property and was
   **deliberately left alone** — changing an archived-P2 knob's reuse
   eligibility is another lane's call.
4. **The V2 construction.** The PREREG specified V2 as a re-score; the scorer
   reads a *registered* run, so V2 was evaluated instead as a direct
   control-vs-keeper comparison on the two bundles' own committed hourly
   artifacts. That is **strictly stronger** — bit-level price and class-energy
   agreement implies identical C3a/C3b — and it is reported at full magnitude
   in §1.

---

## 7. What this session did NOT do, and the two limitations that remain

* It **did not** propose, arm, test or adjudicate any mechanism. **No cell
  verdict is minted**; no `ScenarioConfig` field exists.
* It **did not** apply a CT offer-LEVEL lever. Branch C-FLOOR makes a SECOND
  PREREG *reachable*; it does not authorize a lever inside this session, and
  the against-interest bound is inherited unchanged: **2023 passes C3a at
  ≈ −0.5 %, so a lever lifting 2023's mean by more than +3 % is a REGRESSION
  even if 2025 improves.**
* It **did not** re-open the closed objects (across-unit dispersion, the D-4
  window flag, the within-unit offer-shape family, the base-band inversion) or
  touch C3c or C7.

**Limitation 1 — the instrument is validated on L1F, not on L1X, and the
finding says so in those words** (PREREG §6's requirement for this branch).
Price-taking on the bid alone still reads **−13.91 / −8.66 / −5.53 %**; it is
the floors-read leg that clears. Any successor quoting "CT volumes measurable
to ~1 %" must quote L1F and must dispatch the committed floors.

**Limitation 2 — the control carries no governance attestation.** The
registered run scores **NOT-YET** with C6 **UNATTESTED** ("no governance
attestation in bundle"), because `replay_keeper` does not regenerate the
attestation. It is a control reproduction of an existing keeper, not a
promotion candidate, so nothing rests on its determination — but the run page
will show C6 unattested and that is why.

---

## 8. Where this leaves the lane

**Delivered.** (a) `--persist-p0-commitment` — opt-in, default-off,
additive-only, **412 KB + 53 KB per year** (smaller than the existing
`class_hourly` sidecar's 644 KB), with 11 unit tests. (b) A control bundle that
reproduces the keeper to bit-identity in 2025. (c) An instrument that measures
MISO's CT volumes to **~1 %** and every thermal class to within 5.8 %.
(d) The discovery that **three sessions of CT reconstruction were run against a
fleet with no reliability floors.**

**The owner decision miso-154 named is now decidable on evidence.** Making the
P0 sidecar part of the committed bundle spec (default-on) would cost **465 KB
per ISO-year**. This session did **not** take that decision and ships the flag
default-off.

**Two things a successor should not have to rediscover.** First, `_miso134`'s
`build_year` does not apply the reliability-floor registry — **any probe
scoring a floored class against a keeper must read `floors/<year>_P1.npz`**,
and the three CT reconstructions that predate this finding should be read with
that in mind. Second, the *shape* of what remains: with the markup exact and
the floors read, CT lands at −0.89 / −0.26 / −0.52 %, so **there is no
remaining unexplained CT volume residual to attribute to the offer level.** A
CT offer-LEVEL charter must therefore identify its target from something other
than a volume miss — and §8 of the PREREG records the datum it will have to
confront: the Potomac Economics MISO IMM measures the **system price-cost
mark-up at +3.0 % (2023) and −2.5 % (2024)** with a de-minimis output gap,
i.e. MISO's real market clears essentially **at cost**, while the model's CT
already offers at its own base heat rate plus a startup markup.

---

**Artifacts.** Probe `scripts/probes/_miso155_p0_exact_instrument.py`
(ruff clean). Record `results/calibration/_miso155_p0_exact_instrument.json`.
Tests `tests/test_miso155_p0_commitment_sidecar.py` (11 passing). Build
`scripts/run_calibration.py::p0_commitment_pattern` +
`scripts/run_calibration_full.py::_write_p0_commitment_sidecar`. Run
`2026-08-13-miso-155-control-p0` (`miso155_p0_C`). PREREG `a920c85`, blob
`07b12e5a`.
