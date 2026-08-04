# PREREG miso-123 — hour-of-day-resolved MISO seam band AVAILABILITY

Session miso-123, 2026-08-04, branch `claude/miso-seam-band-availability-tb6atf`,
off `origin/main` at `05d291d7`. **Written and committed BEFORE any probe is
written or run.**

Current MISO keeper: `2026-08-04-miso-122b-scope-gate`
(`results/calibration/miso122_scopegate_B`), determination `NOT-YET`, sole FAIL
C7 `COAL_PRB` diurnal shape, ledgered caveats {C3a, C3c}.

---

## 1. The lever, and why this one

`docs/mechanism-testing-matrix.md` §5.4 item **0c**, the successor miso-114
named and deliberately did not charter:

> "The one admissible successor is hour-of-day-resolved band **availability** at
> the `(month × hour-of-day)` grain `MISO_SEAM_DIBA` already uses — changing
> *when* a band may clear, not *how much* flows — which needs its own charter."

The measured defect it targets (miso-114 §0.1, §3): the MISO seam reproduces
annual net-interchange energy to **1.017 / 1.016 / 0.908** while its hour-of-day
correlation with reality is **+0.097 / −0.453 / −0.030** — no hourly skill, and
inverted in 2024. Signed mis-shape: **night short 1,333 / 1,210 / 1,206 MW, peak
long 1,338 / 1,147 / 746 MW.** The mechanical cause miso-114 identified is that
`MISO_SEAM_LADDER_BY_YEAR` is an **8-band hour-INVARIANT price ladder**, so the
count of bands in the money is a monotone function of MISO's own price — lowest
overnight (4.4 / 3.5 / 2.9 bands) and highest at peak (6.0 / 4.9 / 4.2), the
opposite of measured flow.

§5.4 has no other named, un-adjudicated, non-data-blocked item: the C7
`COAL_PRB` regulated-self-commitment family is closed (`R`/`R`/`I`, rule 19
forbids a fourth mechanism), items 1–2 are data-blocked at a **sourcing** step,
item 3 is `R` ex ante, items 4/5/6 are `K`/`I`/`I`, and miso-122 executed the
hybrid-cogen scope gate. This and miso-118's `CT_CHP`-side plant rate are the two
remaining named-but-unchartered successors; this session takes this one.

### 1.1 Charter grounds, stated up front and binding

This is a **rule 1 `[R-STRUCT]` structural-fidelity** item and **NOTHING ELSE.**
miso-114 §0.2 sized it at the model's own local stack slope (0.24–0.40 $/GW) as
worth **−$0.32 / −$0.39 / −$0.44 overnight** and **+$0.34 / +$0.43 / +$0.30 at
peak**, against measured gaps of +$6…+$8 overnight and −$5…−$25 at peak — i.e.
**4–7 % of the residual.**

* It is **NOT** chartered as a C7 `COAL_PRB` instrument. It cannot close C7 and
  no result here may be quoted as C7 progress.
* It is **NOT** chartered as a C3a or C3c instrument.
* It ships, or is refused, on whether the seam's hour-to-hour behaviour becomes
  the market's — **whatever it does to the residual** (rule 1, both directions).

### 1.2 What is already refused and is NOT re-opened

* **`miso_pjm_lmp_import_pricing` — REFUTED ex ante** (miso-114 §4, on MISO's own
  measured data: actual MISO−PJM_WEST spread ±$1–2 overnight, night-minus-peak
  only −1.07 / +2.16 / +3.15 $/MWh, corr(spread, actual net import)
  +0.289 / +0.240 / +0.286, MISO importing 4,591 MW at h2 on a +$1.0/MWh spread).
  A **price-side** fix is out of scope here. This session does not arm it, sweep
  it, or re-measure it.
* **`miso_firm_import_floor` — stays rejected as an outcome pin** (rule 13).
  Nothing in this charter re-licenses it, and no candidate construction here may
  be a **floor**. Every candidate is a **ceiling** (an availability upper bound);
  a construction that forces flow is out of scope by definition.
* **`miso_cc_coal_rebalance` — do NOT arm** (miso-114 §5: hand-specified offer
  override targeted at another *model* quantity; rules 5/21/24).
* The C7 `COAL_PRB` family (miso-111 `R` / miso-112 `R` / miso-113 `I`,
  confirmed miso-114) is untouched.

---

## 2. THE rule-13 question this charter exists to adjudicate

miso-114 §4 closed by naming this as **"a design question with a real rule-13
argument on both sides."** That adjudication is this session's primary
deliverable, and it is settled by **measurement against a pre-registered test**,
not by assertion.

**The hazard, stated at its strongest.** The matrix carries `import_shape_lever`
= **`G`** at NYISO (nyiso-99), governance-refused *ex ante* with no solve, on the
ground that *"the only series that says 'import more at h17' is the measured net
interchange, which is the SCORED OUTCOME and forbidden as an input (rule 13)."*
MISO's net interchange is likewise a scored quantity (the C1 interchange family).
Rule 25 `[R-ISO-SCOPE]` means NYISO's **verdict** does not fill MISO's cell — but
NYISO's **argument** applies to any MISO construction that shapes flow by hour
from the measured hourly flow, and this pre-registration must clear it rather
than route around it.

**The distinction that decides it.** MISO **already arms**
`miso_seam_flow_limit` + `miso_seam_export_limit` +
`miso_seam_envelope_merit_cap` on the keeper (confirmed in
`miso122_scopegate_B/run_config.json`), whose envelope is the per-`(month ×
hour-of-day)` **p90** of the measured directed BA-to-BA flow over
`MISO_SEAM_DIBA` — so the `(month × hod)` grain of the measured directed flow is
**already an admitted MISO input**, accepted as an ATC/deliverability proxy
because a high percentile leaves headroom and the LP still clears economically
below it.

The live question is therefore **not** the grain. It is whether moving from *one
high quantile per cell* to a *finer per-band statistic of the same cell* crosses
the line from **capability envelope** (bounds what CAN flow; the LP chooses
within it) to **outcome pin** (determines what DOES flow).

### 2.1 KILL-13 — the pre-registered rule-13 test, binding

A candidate availability construction is **REFUSED under rule 13, with no
solve**, if either of these measures on the keeper's own committed output:

* **(a) Headroom collapse.** The candidate's summed per-seam availability
  reproduces the measured cell-conditional **mean** flow to within 5 % in the
  majority of `(month × hod)` cells — i.e. the construction leaves the LP no
  economic headroom and the seam's hourly flow becomes the statistic rather than
  a choice made against it. *(An availability whose band sum is a Riemann sum of
  the cell survival function has exactly this property by construction — it is
  the first thing this session measures, and it is a disqualifying property, not
  a feature.)*
* **(b) Choice extinguished.** Under the candidate, the availability ceiling
  binds (cleared = ceiling) in **> 70 %** of hours in any year, so the LP's
  merit-order clearing is decorative.

If **either** fires, the construction is refused and recorded as refused. This
session then reports the finding and spends **no LP**, in the miso-103 / 104 /
105 / 114 discipline.

---

## 3. Phase 0 — no LP, committed artifacts only

**No solve. No holdout year read** (rule 22 — MISO holds no
`calibration-complete` marker; 2023 / 2024 / 2025 only).

Sources: the keeper bundle `results/calibration/miso122_scopegate_B/hourly/`
(`system_<year>.parquet` P1 duals, `class_hourly_<year>.parquet` class
dispatch), `data/raw/eia-930-interchange/MISO interchange hourly.parquet` (the
directed BA-to-BA series the envelope is already built from),
`data/raw/eia-930-hourly/MISO hourly.parquet` (total interchange), and the
model's own seam construction (`MISO_SEAM_LADDER_BY_YEAR`, `MISO_SEAM_DIBA`,
`measured_seam_import_envelope`, `inject_miso_seam_flow_limit`) rebuilt offline
at the keeper's flags.

### Q1 — Is availability ALREADY hour-of-day-resolved, and does its shape point the right way?

The armed p90 envelope is per-`(month × hod)`. Measure, per seam and direction,
the **hour-of-day profile of the p90 cap** against the hour-of-day profile of
the **measured flow** and of the **model's cleared flow**.

*This question can dissolve the lever.* miso-114 attributed the mis-shape to the
hour-invariant **price ladder**; if the availability channel is already
correctly hod-shaped, then "hour-of-day-resolved band availability" is a premise
that is **already satisfied**, and the named successor is closed on measurement
rather than chartered. That outcome is a legitimate deliverable and is reported
as such.

### Q2 — Does the envelope BIND? (the miso-121 statistic, and the decisive one)

miso-121's standing lesson: **binding is not marginality; the predictive ex-ante
statistic is the MARGINAL SHARE OF BINDING HOURS.** Measure, per seam, direction
and year, on the keeper's own solved P1 prices:

* the share of hours in which the seam's cleared import equals its envelope
  ceiling (**binding share**), and
* the share of hours in which the ceiling is the constraint that **stops the
  next band from clearing** — band *k+1* in the money at the solved price but
  availability-zeroed by the envelope (**marginal binding share**).

Broken out **overnight (h0–5, h22–23) and peak (h16–19)** separately, because
the defect is a night/peak differential.

### Q3 — The candidate's own effect, held-price

Recompute each seam's cleared import under the candidate availability while
**holding the keeper's solved hourly prices fixed** (the same held-price
reconstruction miso-114 used to count bands in the money). Reports the
**upper bound** on the achievable correction: hour-of-day correlation, signed
night/peak MW, and annual energy ratio per year.

### Q4 — KILL-13 measurement

Both limbs of §2.1 (a) and (b), measured per seam, direction and year.

### Q5 — Annual-energy integrity

The candidate's held-price annual import energy against the keeper's
1.017 / 1.016 / 0.908. A ceiling can only **reduce**; a construction that buys
hod shape by deleting energy is not a fidelity gain.

### Q6 — Direction of the achievable correction

Decompose the held-price Δ into its **night** and **peak** limbs. A ceiling
cannot lift the overnight **short** (1,206–1,333 MW); at most it can cut the peak
**long** (746–1,338 MW). Report explicitly how much of the measured mis-shape is
reachable by an availability ceiling **at all**, and state the unreachable
remainder rather than leaving it to be discovered.

---

## 4. The candidate construction (evaluated in Phase 0, armed only if it survives)

**C1 — per-band cell survival availability.** For seam *s*, direction *d*, band
*k* spanning depths `[L_{k−1}, L_k)` on the existing 8-band equal-width grid:

    avail[s,d,k,m,h] = fraction of measured hours in cell (m,h) whose directed
                       flow exceeded L_{k−1}

Same source, same `(month × hod)` grain and same band grid as the armed
envelope; **zero free parameters, zero thresholds**; a strict ceiling
(availability ∈ [0,1], never a floor); byte-identical no-op for any ISO without
a seam-DIBA map (rule 25).

**C1 is expected to FAIL KILL-13(a)** — its band sum is a Riemann sum of the cell
survival function and therefore approximates the cell **mean** flow, removing
exactly the headroom the p90 envelope exists to preserve. **This is written down
before measuring it.** If it fails, it is refused, not reshaped into something
that passes.

**C2 — hod-resolved percentile envelope.** Retain the existing
`clip((cap − depth)/width, 0, 1)` merit-order waterfall and the existing p90
percentile, but note that this *is* the status quo. **C2 is not a candidate**;
it is named to make explicit that no percentile sweep is admissible here — a
percentile chosen because it improves the hod residual is a fitted value
(rules 5 / 21 / 23), and `miso_seam_flow_percentile` is an already-registered
knob whose sweep is exactly the tuning rule 23 `[R-FROZEN-DERIVE]` forbids.

If C1 is refused and no construction survives §2.1 with zero free parameters,
**the honest outcome is refusal on measurement and no LP is spent.**

---

## 5. Phase 1 — the A/B, conditional on Phase 0 passing every kill

Run **only if** Q1 shows the availability channel is not already correctly
shaped, Q2 shows a non-trivial marginal binding share, Q3 shows a material
held-price hod-shape gain, and KILL-13 does not fire.

* Two arms, control = keeper replay at HEAD, arm = candidate; **one invocation
  each over `--years 2023 2024 2025`** (rule 16), arms sequential.
* New `ScenarioConfig` field, default **off**, MISO-only, byte-identical no-op
  elsewhere (rules 24 / 25), with its matrix row added in the same PR (rule 28c).
* Wiring: **three** `run_energy_solve` call sites (`pipeline/year.py`,
  `runner.py`, `scripts/run_calibration.py` — the backcast orchestrator every
  calibration arm actually runs). This lever enters at **fleet-array assembly**,
  not `p1_fleet_prep`, so the miso-113 warm-P1 hazard does not apply; firing is
  proved by a **pre-arm offline availability check** plus a **post-arm per-class
  energy delta**, per miso-122 §4. `pytest tests/unit/pipeline/test_p1_prep_wiring.py`
  runs regardless.
* **Budget (miso-122 §8, measured):** a MISO 2025 P1 OOMs at ~15.9 GB on this
  15 GB box **even unfloored**. Add a **12 GB swapfile** before the first arm and
  **remove it afterwards** (disk is tight). Do **not** use the fresh-process +
  `--reuse-solved` merge route — the swapfile keeps `meta.json`'s year span
  truthful by construction.

### 5.1 Pre-registered A/B gates

| gate | bar |
|---|---|
| **K1** artifact/mechanism fidelity | the arm's availability differs from the control's on exactly the seam import rows and nowhere else; no band added, none dropped |
| **K2** control integrity | control is byte-identical to the keeper (max class-hour \|Δ\| ≤ 1e-6, same determination, same nine criterion statuses) |
| **K3** hod-shape liveness — **THE bar** | seam net-import **hour-of-day correlation** improves by **≥ +0.20 in ≥ 2 of 3 years** and goes **more negative in none** |
| **K4** config delta | exactly one differing `ScenarioConfig` key |
| **K5** year span | both bundles `[2023, 2024, 2025]` |
| **K6** annual-energy integrity | annual import-energy ratio stays inside **[0.85, 1.15]** in all three years |
| **K7** no scored regression | no criterion moves PASS → FAIL / CAVEAT; C7 `COAL_PRB` is **not** claimed either way |

### 5.2 Pre-registered disposition — written before the result

* **K3 met and K7 clean** → structural-fidelity **keeper candidate** on rule 1 /
  rule 14 grounds; matrix cell **`K`**. A price-inert outcome does **not** demote
  it: §1.1 sizes the price effect at 4–7 % of the residual *in advance*, so
  price-inertness is the **predicted** result and cannot be the disqualifier.
  *(This is why K3 is a shape bar, not the |Δλ| ≥ 0.10 bar miso-119/122 used —
  fixed here, before any number is seen.)*
* **Dispatch moves but K3 fails** → cell **`R`**: the construction does not do
  what it claims.
* **Seam energy moves < 0.5 %** → cell **`I`**.
* **KILL-13 fires, or Phase 0 refuses** → **no solve**; the successor named in
  §5.4 item 0c is **closed on measurement**, recorded with its numbers, and the
  cell records the refusal.

---

## 6. Statistics this session will NOT use — the running DO-NOT-MISREAD chain

Applied *ex ante*, all three:

* **miso-119:** `max |Δoffer|` is an **UPPER bound only**; it over-predicted the
  realized price effect by two orders of magnitude.
* **miso-121:** **binding is not marginality.** The predictive ex-ante statistic
  is the **marginal share of binding hours** — which is exactly why it is Q2 and
  why Q2 is decisive.
* **miso-122:** **`max_abs_class_hour_mw` is NOT a mechanism magnitude at MISO.**
  It read 912.5 MW to seven figures for two unrelated levers because it lands on
  the `import` class where a single **912.5 MW seam band** flips. This session's
  lever operates on **that very seam**, so the statistic is doubly meaningless
  here and is **not reported as a magnitude.** Magnitudes are **per-class ENERGY
  deltas** and the **hour-of-day correlation**.

---

## 7. Rule duties

* **Rule 1 `[R-STRUCT]`** — chartered on structural fidelity; ships or is refused
  on the seam's hour-to-hour behaviour, never on the residual, in either
  direction.
* **Rule 13 `[R-MEASURED]`** — §2.1 KILL-13 is the binding test; no candidate may
  be a floor, and no measured outcome is fed back.
* **Rule 15 `[R-DASHBOARD]`** — every completed run registered this session,
  keeper or rejected. If Phase 0 refuses, no run is produced and there is nothing
  to register.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025 in one bundle per arm.
* **Rule 19 `[R-ONE-MECH]`** — the seam's hour-of-day shape has no existing
  mechanism; the candidate **replaces** the envelope's composition rather than
  stacking on it, and the refused price-side alternatives are named in §1.2.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; no out-of-training year solved,
  scored **or read**. LOO within training years before proposing promotion.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no percentile sweep, no re-derivation against
  a residual (§4 C2).
* **Rule 25 `[R-ISO-SCOPE]`** — MISO only. NYISO's `import_shape_lever` `G` is
  confronted as an **argument** in §2 and is never treated as MISO's verdict; no
  cell outside MISO is stamped, and the cross-ISO CHP handoffs miso-122 opened
  (NYISO 2493 East River, NEISO 1595 Kendall) are **not** touched from this
  session.
* **Rule 28 `[R-MECH-MATRIX]`** — the tested cell is stamped in this session,
  refusal included; a new `ScenarioConfig` field lands with its matrix row in the
  same PR.

**Contamination declared:** this session read miso-114's finding, miso-122's
finding and the matrix `import_shape_lever` / `seam_flow_envelopes` rows before
measuring, so it is **not** blind to the hod-correlation result or to NYISO's
refusal. Immaterial to Q1–Q6, which rest on the committed EIA-930 directed-flow
series, the keeper's own solved duals, and the model's own seam construction.
</content>
</invoke>
