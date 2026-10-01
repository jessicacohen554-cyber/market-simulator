# FINDING — miso-154: the CT commitment instrument is **BUILT** and the +22–24 % is **EXPLAINED**. It clears **2 of 3** — **B-PARTIAL, no lever follows.**

**Session** miso-154 · **ISO** MISO · **Date** 2026-08-12 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED** ·
**Model** `claude-opus-5`.

**PREREG** `results/calibration/PREREG-miso154-ct-commitment-instrument-2026-08-12.md`,
pushed at **`065c83e`**, blob **`771ebc33775f342a7e7b6a69632c2fcb74ed474a`**,
**verified byte-identical against the FETCHED remote ref** before any
adjudicating statistic was computed (rule 27 `[R-PUSH]`).

**Status: NO LP SOLVE, NO RUN, NO REGISTRATION, NO `ScenarioConfig` FIELD, NO
CELL VERDICT MINTED** (no mechanism was armed or tested — the miso-142 /
miso-153 precedent). Rule 15 is not engaged: a no-run session produces no run.
**Keeper unchanged.**

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only. MISO holds no marker. No
holdout year was read, solved or scored.

**BRANCH TAKEN: B-PARTIAL** (PREREG §5). The instrument clears the ±10 % bar
in **2 of 3** years. **No CT offer-LEVEL lever is proposed and no second
PREREG is opened** — B-PARTIAL forbids both.

---

## 1. Headline

The lane's blocking dependency was that the price-taking reconstruction ran
**+22.0 / +22.1 / +23.7 %** hot on `CT_PEAKER`, making CT volumes unmeasurable.
**That residual is now explained.** It was not a defect in the fleet: it was a
**mis-specification in the measuring instrument**. miso-153's T-6b compared a
**base** cost against a **bid**-cost clearing price, admitting every tranche
whose startup recovery had not been earned.

Correcting exactly that one thing — comparing `mc_bid = mc_base + markup`
against the same prices, with the markup from the **production**
`compute_monthly_markup` — moves the residual by **28–35 pp**:

| year | published price-taking (`mc_base`) | **L1 (`mc_bid`)** | correction | bar ±10 % |
|---|---|---|---|---|
| 2023 | +21.99 % | **−13.21 %** | −35.20 pp | **FAIL** |
| 2024 | +22.14 % | **−7.53 %** | −29.67 pp | **PASS** |
| 2025 | +23.72 % | **−4.47 %** | −28.19 pp | **PASS** |

**The instrument's construction is validated to three decimal places.** Its
baseline leg reproduces miso-153's published T-6b at **+21.99 / +22.14 /
+23.72 %** against the published **+21.99 / +22.14 / +23.72 %** — deltas
**+0.000 / −0.000 / −0.001 pp**, on the same `n_gen` (**2929 / 2923 / 2923**).
The correction is therefore measured against a like-for-like number, not a
re-derived one.

**But it clears only 2 of 3, and §4 shows why that count should not be
trusted in either direction: the instrument's own uncertainty is wider than
the bar.** That is the honest result, and it is why no lever follows.

---

## 2. The prior — band CONFIRMED, centre MISSED, reported both ways

PREREG §4 registered: *L1 `resid` lands in `[−15 %, +15 %]` in at least 2 of 3
years, centred on `+2 %`.*

* **Band: CONFIRMED, and over-delivered.** All **3 of 3** years land inside
  `[−15 %, +15 %]` (−13.21 / −7.53 / −4.47), against a 2-of-3 requirement.
* **Centre: MISSED by ~10 pp, in the cold direction.** Measured mean
  **−8.40 %** against a registered centre of **+2 %**. The markup does not
  merely remove the +22–24 pp; it **over-shoots** it by 4–13 pp. The prior's
  two-sidedness was not decorative — the outcome landed on the side I flagged
  as a real possibility, and it is the side that costs 2023 the bar.

**No surprise trigger fires.** `S-LOW` (< −25 % in any year): the worst is
−13.21 %, **does not fire**. `S-HIGH` (> +18 % in all three): **does not
fire**. `S-INERT` (markup ≈ 0): the CT markup is **$4.74 / $4.15 / $4.27**
per MWh cap-weighted at the top-200 hours with **0.0 %** of CT capacity at
zero markup — **does not fire**.

---

## 3. What the markup actually is, and why it bites hardest at the peak

Read through the production chain, per CT tranche (2025 grain, n = 733):

| input | value | source |
|---|---|---|
| startup cost | **$20.00/MW**, identical on **733 of 733** tranches | CAMPD bin |
| measured run horizon | **8.83 h** cap-weighted; per-plant 2–8+ h on **86.8 %** of CT capacity | `campd_ct_run_lengths_MISO.csv` |
| v4 band ratio at the top-200 hours | **0.638 / 0.652 / 0.684** | `campd_ct_run_bands_MISO.csv` |
| resulting markup | capwtd **$4.74 / $4.15 / $4.27**; p50 **$3.33** (= 20 ÷ 6 h), p90 **$5.56–6.67**, max **$20.00** | production `compute_monthly_markup` |

The v4 conditional-run basis **shortens** the amortization horizon exactly
where this lane is looking: the top net-load band carries ratio **0.6**, so at
the summer peak a CT recovers its start over ~6 h instead of ~10. The markup
is therefore at its **largest** in precisely the top-200 window — which is why
ignoring it produced a residual that looked like a fleet defect.

**Across-unit note, reported because it runs against a tidy story:** startup
cost carries **no** across-unit variation at all ($20.00/MW on every tranche).
All of the markup's across-plant spread comes from the CAMPD-measured run
length. That is consistent with miso-153 §12–§13 (CT's across-unit dispersion
is already the widest in the fleet and is faithful to its measured input); it
adds no new dispersion object and **does not re-open the closed one**.

---

## 4. THE LIMITATION THAT GOVERNS THE VERDICT — the instrument's uncertainty exceeds its own bar

This is the finding's most important number, and it works against the
instrument.

### 4.1 The P0 proxy dominates (T-9)

The keeper's committed `hourly/` sidecars carry **`pass == "P1"` only**. There
is no committed P0, so the markup's run-length source must be reconstructed.
Bounding it with the two extreme bases:

| year | P0 = `never` (max markup) | **P0 = price-taking (used)** | P0 = `always` (min markup) | span |
|---|---|---|---|---|
| 2023 | −28.98 % | **−13.21 %** | −7.28 % | **21.7 pp** |
| 2024 | −24.11 % | **−7.53 %** | −3.21 % | **20.9 pp** |
| 2025 | −18.65 % | **−4.47 %** | −0.25 % | **18.4 pp** |

**The ±10 % bar is 20 pp wide. The P0-proxy span is 18–22 pp.** A single
input the instrument cannot observe moves the answer by more than the bar
discriminates. **2023's FAIL and 2024/2025's PASS are both inside this band.**

### 4.2 …and its direction is against the instrument

The proxy clears `mc_base` at the keeper's **P1** prices. A true P0 clears at
**P0** prices, which are ≤ P1 prices (P1 adds a non-negative markup to every
offer); and an LP dispatches **less** than price-taking, which hands every
in-merit tranche its full availability. **Both errors push the same way** —
fewer and shorter P0 runs → a **larger** markup → a **colder** reconstruction.

**So the true residual sits BELOW every number in §1**: 2023 fails harder, and
2024/2025 move toward the −10 % edge rather than away from it. The PREREG
declared this bias before measuring it, as a bias that would make the bar
harder to clear. It did.

### 4.3 The v4 band series is approximated, and it matters (T-10)

Production keys the amortization horizon on renewable **potential**
(`cap × cf`); the committed sidecars carry only **dispatched** wind/solar, so
the reconstruction bands on `demand − wind − solar` from `class_hourly`.

| year | v4 (reconstructed, used) | v3 flat ratio ≡ 1.0 | gap |
|---|---|---|---|
| 2023 | −13.21 % | −7.70 % | **5.51 pp** |
| 2024 | −7.53 % | −2.67 % | **4.86 pp** |
| 2025 | −4.47 % | +0.19 % | **4.66 pp** |

Every gap is **above** the 2 pp threshold the PREREG set for "immaterial", so
this is a **live limitation**, disclosed rather than absorbed.

**Stated explicitly because it would flatter this session to do otherwise:
the v3 basis clears 3 of 3.** It is **not** the keeper's basis — the keeper
arms `tranche_startup_conditional_runs=True` — and substituting it to buy a
pass would be exactly the fitted move rule 1 `[R-STRUCT]` forbids. **The
verdict stands at B-PARTIAL on the keeper's own basis.**

---

## 5. min-run / min-down are **ABSENT** for MISO's CT — verified twice (T-11, T-3)

The charter named three legs of CT commitment. Two of them do not exist here:

* **Cap-weighted `min_run_hours` for `CT_PEAKER` = 0.00 h.**
* **Second, independent derivation** (distinct-value census at tranche grain,
  2025): `min_run_hours` distinct = **[0.0]** across **733 of 733** tranches;
  `min_down_hours` distinct = **[0.0]** across **733 of 733**. The only
  fleet units carrying a min-run at all are **51 `COAL_FAMILY`** units —
  `CT_PEAKER` is **not among them**.
* **Consequence, measured:** `enforce_min_run` extends **678 / 919 / 237**
  runs and moves the CT residual by **exactly 0.00 pp** in all three years.

**This clean zero is corroborated, not asserted** (T-3's standing rule:
disbelieve clean zeros). Two different constructions — a cap-weighted mean and
a distinct-value census — agree, and the census explains *why* the zero is
exact.

**So MISO's P1 carries exactly one piece of commitment physics for CT: the
startup amortization.** MISO arms no commitment bridge, no P2 pass, no P1 bid
adjustment and no bid-max target (PREREG §1.1), so there is nothing else for
an instrument to reproduce. That is a structural fact about the model, and it
is why the markup alone moves the residual by 28–35 pp.

---

## 6. L2, and the class it exposes

**L2 (merit-order clearing) is reported and does NOT gate**, exactly as
pre-registered — it conserves the keeper's own hourly thermal total by
construction, so a good L2 number is partly an artifact of its own clearing
and must not buy a pass.

| year | L2 top-200 | L2 annual |
|---|---|---|
| 2023 | **+3.69 %** | −18.90 % |
| 2024 | **−9.28 %** | −25.39 % |
| 2025 | **−1.75 %** | −12.80 % |

L2 clears the top-200 bar in 3 of 3 — **and it is still not allowed to change
the verdict.** Its annual residuals (−12.8 to −25.4 %) show why the
pre-registration was right to fence it: conserving the hourly total does not
make the *allocation* right, and over 8760 hours the misallocation is large.

**What L1 exposes about floored classes.** Per-class L1 top-200 residuals:

| year | CC_REGULAR | CC_CHP | CT_PEAKER | CT_CHP | **ST_GAS** | ST_CHP | COAL_FAMILY |
|---|---|---|---|---|---|---|---|
| 2023 | −3.3 % | −6.0 % | −13.2 % | −1.7 % | **−11.8 %** | −0.5 % | +0.1 % |
| 2024 | −2.0 % | −0.1 % | −7.5 % | −2.6 % | **−17.0 %** | +0.0 % | +4.8 % |
| 2025 | +0.1 % | −0.2 % | −4.5 % | −2.6 % | **−19.4 %** | −0.0 % | +0.6 % |

`ST_GAS` is reproduced **worse than CT in every year**. This is a construction
limit, not a new defect: price-taking **cannot** dispatch an out-of-merit
must-run floor, and `ST_GAS` is the keeper's most heavily floored class
(**47.0 %** forced energy, D-2). Any future use of this helper on a floored
class must use **L2**, which dispatches floors first. Recorded so the next
session does not rediscover it as a finding.

---

## 7. Traps — every counter-measurement, at full magnitude

| # | Counter-measurement | Result |
|---|---|---|
| **T-1** | Bundle repointed to `miso148_basis_B` and asserted | **PASS** — asserted at import; `run_config` **0 keys dropped** |
| **T-2** | Zero 3-argument `getattr(` on the offer path | **PASS** — grep returns **0**; `ruff` clean |
| **T-3** | Full raw band-suffix inventory before aggregation; disbelieve clean zeros | **PASS** — econ smoothing intact and **not** collapsed (`econc00…econc05` each n=44 / 1154.5 MW, plus `econlo` 5812.9, `econhi` 5237.7, `committed` 2935.5, `peak` 1368.4). Every clean zero in this document carries a second derivation (§5, and T-6 below) |
| **T-4** | Fixtures from production types only | **PASS** — every array from `generators_to_fleet_arrays`; **0** `SimpleNamespace` |
| **T-5** | Carry-zone count == 6 | **PASS** — asserted; import nodes given `+inf` price so they can never enter merit |
| **T-6** | `weather_year` pinned per year | **PASS, and the trap is LIVE.** Control A (2023 pinned vs unpinned): max\|Δavail\| **0.000e+00**, max\|Δmc\| **0.000e+00** — unchanged, as its own `weather_year` already was 2023. Control B (2024 correct vs the bug): **12.81 %** of cells differ, max **0.970**, mean **0.068**; CT availability at top-200 **20 518.9** vs **20 613.9 MW** |
| **T-7** | Markup magnitude, so an inert instrument can't hide | **PASS** — capwtd **$4.74 / $4.15 / $4.27**/MWh; **0.0 %** of CT cap at zero markup. `S-INERT` does not fire |
| **T-8** | Production markup, never a re-implementation | **PASS** — asserted at import: `compute_monthly_markup.__module__ == "market_sim.model.commitment"` |
| **T-9** | P0-proxy error bounded, not assumed away | **REPORTED — AND IT IS THE VERDICT'S BIGGEST LIMITATION.** Spans **21.7 / 20.9 / 18.4 pp**, wider than the 20 pp bar (§4.1–4.2) |
| **T-10** | v4 band reconstruction vs v3 basis | **FIRES.** Gaps **5.51 / 4.86 / 4.66 pp**, all above the 2 pp threshold — live limitation (§4.3) |
| **T-11** | Does enforcing min-run help or hurt? | **NEITHER — exactly 0.00 pp**, because MISO's CT carries no min-run at any tranche (§5) |

---

## 8. NOT PRE-REGISTERED — labelled, with counter-measurements

1. **The first execution was VOID and is DISCARDED.** The session's initial
   run was made on a **truncated working tree** — the container's checkout had
   been interrupted, leaving 1 874 tracked files absent (`gas-prices`,
   `nrel-atb`, `nuclear-license-status`, `zone-specific-demand`, `lmp-data`
   and others), and `data/clean` uncurated. It assembled **`n_gen` =
   2766 / 2763 / 2763** and produced **−27.71 / −0.95 / −8.38 %**.
   **Those numbers are not in this document's evidence chain and support
   nothing.** They are recorded here at full magnitude because one of them
   (−27.71 %) would have fired the `S-LOW` trigger, and a reader is entitled
   to know a discarded run said so.
   **The tell was pre-registered:** the baseline leg failed to reproduce
   miso-153's published T-6b. The tree was repaired (1 874 files restored,
   `curate_capacity_deliverability.py` run → **776 MISO rows**), and the
   repaired run reproduces the published baseline to **±0.001 pp** on the
   published `n_gen`. **The validity check caught it, which is what it was
   for.**
2. **The `BASELINE_pricetaking_mc_base` leg itself.** Recomputing miso-153's
   T-6b inside this probe is an addition beyond PREREG §3, made so the
   correction is measured like-for-like. It is the check that **caught item 1**
   and it works against this session by construction — a baseline that failed
   to reproduce would have invalidated the whole instrument. Magnitudes in §1.
3. **The per-class L1 table** (§6). An addition, so that a CT "fix" which
   wrecked another class could not pass unseen. It surfaced the `ST_GAS`
   −11.8 / −17.0 / −19.4 % result, which is **unfavourable** to the
   instrument and is reported as a limitation in its docstring.

---

## 9. What this finding does **NOT** conclude

* It does **not** propose, test, arm or adjudicate any mechanism. **No cell
  verdict is minted** and no `ScenarioConfig` field is added.
* It does **not** propose a CT offer-LEVEL lever. B-PARTIAL forbids it, and
  §4 is the substantive reason: an instrument whose own uncertainty exceeds
  its bar cannot yet certify a level.
* It does **not** claim the CT offer level is right or wrong. It claims only
  that the **+22–24 % was the instrument, not the fleet**.
* It does **not** re-open the across-unit dispersion object (miso-153
  §12–§13), re-raise the withdrawn D-4 window flag (§11), or touch the MISO
  outage extract (§3). All remain closed.
* It does **not** engage the C3c ledger, and does **not** bear on C7
  `COAL_PRB` (deprioritized by standing directive).

---

## 10. Where this leaves the lane

**Delivered.** The chartered instrument exists, is reusable
(`assemble_year` → `reconstruct_p0` → `commitment_markup` →
`reconstruct_p1_*` → `class_energy_residual`, each independently importable),
is `ruff`-clean, and carries its limitation in its own docstring. The lane's
stated blocker — *"CT volumes are currently unmeasurable"* — is **substantially
resolved**: CT volumes are now measurable to **±13 pp worst-case, ±4.5 pp
best**, against **±22–24 pp** before, and the residual's **cause is
identified**.

**Not delivered, and honestly so.** The ±10 % bar is met in 2 of 3 years, and
§4 shows the count is not robust: the P0-proxy span (18–22 pp) exceeds the bar
(20 pp), the v4 approximation moves it a further ~5 pp, and both known biases
point **colder**. **CT volumes are measurable; they are not yet measurable to
±10 %.**

**The one thing that would close it, stated for the owner without proposing
it as this lane's next step.** Every limitation in §4 traces to a single
missing artifact: **there is no committed P0 pass.** A keeper bundle that
committed `class_hourly` at `pass == "P0"` — or a unit-grain P0 run-length
sidecar — would collapse the T-9 span to zero and remove §4.2's bias
entirely, because the markup's run-length source would then be *read* rather
than reconstructed. That is a bundle-contents question, not a mechanism
question, and it is an owner decision.

---

**Artifacts.** Probe `scripts/probes/_miso154_ct_commitment.py` (ruff clean,
reusable helper surface, limitation in its module docstring). Record
`results/calibration/_miso154_ct_commitment.json`. PREREG
`results/calibration/PREREG-miso154-ct-commitment-instrument-2026-08-12.md`
(`065c83e`, blob `771ebc33`).
