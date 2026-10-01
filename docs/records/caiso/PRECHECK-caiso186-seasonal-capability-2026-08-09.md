# PRECHECK — caiso-186: THE SEASONAL, AVAILABILITY-AWARE CC CAPABILITY BASIS (`cc_winter_capability_basis`)

**Pre-registration. Written and pushed BEFORE any scored metric of this session's object is
read, and before any LP is solved.** Every bar, branch and stop rule below is fixed here and
is fail-closed: a branch that does not fire licenses nothing, and a gate with no measurement
is a FAIL, not a silent pass.

* **Session:** caiso-186. **ISO: CAISO ONLY** (rule 25 `[R-ISO-SCOPE]`, rule 28 duty d).
* **Branch:** `claude/caiso-186-seasonal-capability-nmgjkb`.
* **Incumbent keeper:** `2026-08-09-caiso-184-c1-lpbasis` — **NOT-YET**, C3a the SOLE
  load-bearing FAIL (2023 **+3.7 %** PASS, 2024 **+10.5 %** FAIL, 2025 **+13.1 %** FAIL;
  RT, band ±10 %). **DOF ledger 11 / 8.**
* **Holdout:** CAISO holds **no `complete` marker** (withdrawn by the owner 2026-08-06) and
  the **spend freeze is ACTIVE**. **2023 + 2024 + 2025 ONLY**, one bundle per arm (rule 16),
  years sequential within a run and **arms sequential** (rule 12).
  `calibration-complete.json` and `holdout-freeze.json` are **OWNER ACTS — neither is
  written by this session.**
* **C3a is REPORTED, never TARGETED, and is NEVER the promotion basis** (rule 1
  `[R-STRUCT]`; rule 13 `[R-MEASURED]` — nothing is tuned to it).

---

## 0. P0-1 — DO-NOT-REDO audit (rule 28 duty a), discharged in advance

The CAISO in-model lever queue (`docs/mechanism-testing-matrix.md` §5.2) is **EMPTY with
every cell adjudicated** (FINDING-caiso185 §9 item 4). This charter must therefore prove its
object is a **distinct, un-adjudicated cell** or stop. It is:

* **NOT `cc_capacity_reconcile` (caiso-185, CAISO = `R`, REFUSED).** That cell is **CLOSED
  and stays closed.** This session does **not** arm it, does **not** re-derive its table,
  does **not** hand-edit it, and does **not** read `reconciled_mw` / `campd_p999_mw` into
  any capacity slot. The distinction is the whole point of §2 below: caiso-185's hook writes
  an **availability-INCLUSIVE realized output** (a CEMS peak) into the
  availability-**EXCLUSIVE** `capacity_mw` slot; this session's instrument writes only
  **EIA-860 PUBLISHED RATINGS** — which are availability-exclusive by construction — into
  that slot, and lets the CEMS record enter **only as a check**. Same organ, opposite basis.
  The two are not the same cell and the refusal of one does not adjudicate the other:
  FINDING-caiso185 §5 says so in terms, filing "a seasonal, availability-aware capability
  basis … a **different mechanism** requiring its own pre-registration, its own DOF
  accounting and its own byte-equivalence proof. **It is filed here, not built.**"
* **NOT the denominator basis (caiso-184, `unit_outage_lp_capacity_basis`, `K`, promoted).**
  It is armed on the incumbent keeper and is **carried forward unchanged on both arms**.
  `outages._iso_plant_capacity` is **NOT modified** — see G-DENOM in §5, which is precisely
  the gate that keeps caiso-184's numerator/denominator identity intact under this arm.
* **NOT the envelope DEPTH (caiso-181, SETTLED) and NOT its GRAIN (caiso-183, CLOSED).**
  This session touches **no window, no hour, no detector, no threshold and no outage
  artifact of any kind.**
* **NOT any struck lever.** `battery_dispatch_adder` (permanent declared-residual DOF,
  caiso-176/178/179), the measured-offer-surface coverage extension (caiso-182, both
  identification tests failed), the AS-power-reservation family (caiso-74/127/129), every
  N–S topology lever (caiso-164 §0/§6, **FORBIDDEN**), the seam/intertie family
  (caiso-142/143/167, STRUCK), `caiso_ps_charge_shape_anchor` (`G`, input walled),
  `unit_outage_short_windows` / `unit_partial_outage_windows` (caiso-136/180, coal-only
  detectors against **zero** coal in CAMPD's CAISO population) — **none re-opened,
  re-derived or re-tested.** `caiso_dam_outages` stays `U` and is **NOT armed here.**

**Positive licence:** FINDING-caiso185 §5 and §10 item 2, verbatim above. Rule 14
`[R-ACCURATE]` *requires* that the root cause a rejected accurate input opens be
investigated rather than left; caiso-185 was charter-barred from taking it. This is that
successor.

**If it IS one of those cells, STOP.** It is not, and the discriminator is stated in §2
before any measurement, not after.

---

## 1. THE DEFECT, at source precision

`cc_nameplate_summer_derate` (armed on the CAISO keeper) is a **one-season** instrument
applied to a **two-season** published record.

`fleet/campd_bins.py::fleet_to_bins` (:1684-1694) divides a CC bin's summed net-summer
capacity by the published `cc_summer_derate_ratio = net_summer / nameplate`, so **the LP
carries full EIA-860 NAMEPLATE**. `data/fleet/arrays.py::_availability_matrix` (:737-745)
then multiplies the **summer months only** (Jun-Sep, `_SUMMER_MONTHS`) by that same ratio.
The intended seasonal shape is stated in `fleet/campd_bins.py::cc_summer_capacity`'s own
docstring:

> "the correct seasonal capacity shape (**full nameplate in winter**, ambient-derated to
> net-summer in summer)"

**"Full nameplate in winter" is the unpublished premise, and it is the defect.** EIA-860's
Generator_Y Operable sheet publishes **three** ratings per generator — `Nameplate Capacity
(MW)`, `Summer Capacity (MW)` and **`Winter Capacity (MW)`** — and the model consumes only
the first two. Nameplate is a plate rating; the *winter capability* EIA-860 publishes is the
cold-weather analogue of the summer rating the model already trusts, and it is what CEMS
corroborates. FINDING-caiso185 §5, measured on the 7 CAISO CC plants of the committed
reconcile table:

| ratio | range across the 7 plants |
|---|---|
| CEMS off-summer p999 ÷ EIA-860 published **winter** | **0.906 – 1.001** |
| CEMS off-summer p999 ÷ EIA-860 **nameplate** | **0.73 – 0.89** |

and unarmed off-summer capability sits **8–13 % above** each plant's demonstrated off-summer
output. Plant **358 Mountainview** is the mirror image and is the reason this is a
*two-directional* basis change and not a haircut: its published winter capacity (1110.0 MW)
**exceeds** its nameplate (1036.8 MW) and its demonstrated off-summer peak is 1111.0 MW — the
model **under-rates** it for exactly the reason it over-rates the other six.

**The published pair is not a special case at CAISO.** Read-only census of EIA-860 Operable,
`Technology == "Natural Gas Fired Combined Cycle"`, California plants, summed per plant
(67 plants; published ratings only, no model quantity, no CEMS, no price):

| `winter / nameplate` | plants |
|---|---:|
| < 0.90 (winter materially **below** nameplate) | 23 |
| 0.90 – < 1.00 | 32 |
| = 1.00 | 4 |
| > 1.00 (winter **above** nameplate) | 8 |

Range **0.571 → 1.089**. So the incumbent basis over-rates the large majority of the CAISO
CC fleet off-summer and under-rates a real minority — both errors, from the same omission.

### 1a. A SECOND, sharper reading of the same defect, under the keeper's own `temp_dependent_derate`

The keeper arms `temp_dependent_derate=True` with `temp_derate_mean_anchored=False`, so
`_td_covers` is **True** for CC: the flat summer multiplier in the availability loop is
**skipped**, and the temperature curve `raw = 1 − slope·max(0, tmax − 15 °C)` is rescaled by
`anchor / mean(raw[summer])` with `anchor = net_summer / nameplate` (`arrays.py`:817-876).
That rescale is applied to **all 8760 hours**, not to summer only. Therefore, on the keeper,
the model's off-summer CC capability is **not** nameplate either: it is
`nameplate · raw[~summer] · (net_summer/nameplate) / mean(raw[summer])`, i.e. a level that is
an **incidental by-product of a summer-mean rescale** and that no published quantity asserts.

This makes the §5 story **stronger**, not weaker: the incumbent off-summer level is not
merely unpublished, it is unintended. It also means the sign and size of this arm's effect
**cannot be read off `winter / nameplate`** on the keeper path and must be MEASURED per
plant (P0-3, §4). That is pre-registered here, before the measurement.

---

## 2. P0-2 — THE AVAILABILITY-BASIS RULE, stated before it is used

caiso-185's refusal turned on one identity, and it binds this session:

> What the LP can dispatch is `pmax × availability(t)`. `capacity_mw` is the
> availability-**EXCLUSIVE** slot. A **realized output** (a CEMS peak) is
> availability-**INCLUSIVE** — whatever derate the plant actually suffered is already inside
> the number — so writing one into the other applies every multiplier between the two a
> second time (rule 19 `[R-ONE-MECH]`), and makes the plant's achievable output strictly
> below its own demonstrated peak by construction.

**Per-quantity declaration for every quantity this instrument touches:**

| quantity | source | side of `pmax × availability` | role here |
|---|---|---|---|
| EIA-860 `Nameplate Capacity (MW)` | published rating | **exclusive** | LEAVES the capacity basis |
| EIA-860 `Summer Capacity (MW)` | published rating | **exclusive** | summer leg (as today) |
| EIA-860 **`Winter Capacity (MW)`** | published rating | **exclusive** | **off-summer leg (NEW)** |
| `B = max(net_summer, winter)` | derived from the two above, no free parameter | **exclusive** | the new `capacity_mw` basis |
| `net_summer / B`, `winter / B` | ratios of published ratings | **inclusive** (multipliers) | the seasonal availability legs |
| WEFOR / POF / age derate / CAMPD outage overlay / temperature curve | unchanged | **inclusive** | compose on top, untouched |
| **CAMPD / CEMS demonstrated peaks** | measured **output** | **INCLUSIVE** | **CHECK ONLY** — G-NOCONTRA. **Never written into any capacity slot, never into any multiplier.** |

**A published rating is availability-exclusive by construction**: it states what the machine
can do at a stated ambient condition when it is available, which is exactly what `pmax`
means. That is why this instrument is admissible where caiso-185's was not, and the
distinction is declared **before** any number is read.

**No CEMS-derived number enters a capacity slot or a multiplier in this session.** A
violation of that is stop-the-line (G-NOFIT / G-CHECKONLY, §5).

---

## 3. THE INSTRUMENT — `cc_winter_capability_basis`

**One new `ScenarioConfig` field, one boolean, `default False`.** It acts **only when
`cc_nameplate_summer_derate` is also armed** (the two are one seasonal-capability
statement); with the parent off it is a documented no-op. **Zero fitted scalars. Zero new
numeric parameters. Every value is an EIA-860 PUBLISHED rating or a ratio of two of them.**

Define, per CC plant, summing that plant's `Natural Gas Fired Combined Cycle` generators
from the EIA-860 Operable sheet (the identical population and the identical `ns := min(ns,
np)` double-file clamp `cc_summer_capacity` already applies):

```
B  =  max( net_summer , winter )        # the published seasonal envelope
```

and replace the incumbent nameplate basis with `B`:

| | incumbent | armed |
|---|---|---|
| LP `capacity_mw` (`fleet_to_bins`) | `nameplate` | **`B`** |
| summer availability leg | `× net_summer / nameplate` | `× net_summer / B` |
| off-summer availability leg | *(none)* | **`× winter / B`** |
| td-curve anchor (`_td_covers` path) | summer-mean `→ net_summer/nameplate` | summer-mean `→ net_summer/B` **and** off-summer-mean `→ winter/B` |

**Three legs, all forced by symmetry with the existing summer leg — nothing is chosen:**

1. **`fleet/campd_bins.py::fleet_to_bins`** — the CC bin's summed net-summer capacity is
   divided by `net_summer / B` instead of by `net_summer / nameplate`, via a new
   `cc_seasonal_capability_ratios(plant_code) -> (summer_ratio, winter_ratio)` sitting
   beside the existing `cc_summer_derate_ratio` (which is **not modified**; the off path is
   untouched).
2. **`arrays.py::_availability_matrix`, non-`_td_covers` branch** — summer `× net_summer/B`
   (basis-aware form of today's leg) and, NEW, off-summer `× winter/B`. The off-summer leg
   is the exact mirror of the summer leg, same block, same guard.
3. **`arrays.py` temperature-curve block** — the curve is anchored **twice**: its summer
   mean to `net_summer/B` (today's anchor, basis-aware) and its off-summer mean to
   `winter/B` (NEW). The existing code already anchors the **summer mean** of the curve to
   the published summer ratio; anchoring the **off-summer mean** to the published winter
   ratio is its only symmetric completion. **The statistic is forced by the incumbent's own
   choice — it is not selected, and it will not be re-selected after seeing a sizing or a
   price.**

**Resulting effective capability (the identity this arm asserts):**

```
summer      mean capability  =  B × (net_summer / B)  =  net_summer   (published)
off-summer  mean capability  =  B × (winter      / B)  =  winter      (published)
```

Both seasons land on a published rating. Nameplate — the one rating no season's capability
equals — leaves the capacity basis entirely.

### 3a. Declared consequence on the SUMMER side (H-SUMMER), stated before measurement

This is a **capacity-basis** change, so it is not confined to off-summer, and that is
declared rather than discovered. Availability is clipped to `[0, 1]`, so peak capability is
bounded by `pmax`. Today `pmax = nameplate`, which for a plant like 260 Moss Landing
(nameplate 1398.0, net-summer 1020.0, winter 1020.0) lets the temperature curve carry summer
capability **above the published summer rating** on cooler summer hours. Armed, `pmax = B =
1020.0` bounds it at the published envelope. So **summer capability can fall for plants
whose nameplate materially exceeds both published ratings.** That is a real, intended
consequence of putting the capacity basis on the published record, and it is gated exactly
like the off-summer leg: **G-NOCONTRA applies to BOTH seasons** (§5). It is reported at full
magnitude in P0-3 whatever it shows.

### 3b. Declared implementation detail — the off-summer clip (H-CLIP)

In the td path the anchored curve is applied as `np.clip(raw, 0, 1)`. A two-season anchor can
push `raw` above 1 on the coldest off-summer hours, which would truncate the off-summer level
below `winter`. Armed, the **off-summer block only** uses `np.maximum(raw, 0.0)` — the
precedent the code already documents for `temp_derate_mean_anchored` ("clipping the
multiplier at 1 here would keep only the downward half and turn a level-neutral reshape into
a net level cut") — and relies on the trailing `np.clip(availability, 0, 1)`, which still
bounds capability at `B`. **The summer block keeps `np.clip(raw, 0, 1)` unchanged.** The
realized off-summer mean vs `winter` is measured in P0-3 and reported; a material shortfall
is a reported defect of the instrument, not a licence to add a compensating factor.

### 3c. `run_config` / cache-key / CLI

`--cc-winter-capability-basis`, threaded through `run_calibration_full.py` exactly as
`--unit-outage-lp-capacity-basis` is, recorded in `run_config.json`. The field is registered
in **`_CACHE_KEY_OPTIONAL_FIELDS` AND `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the SAME
COMMIT as the field** (caiso-184 §6 — that session's omission is the reason this is stated
here), and `scripts/check_cache_key_registration.py` is run before pushing.

---

## 4. P0-3 — SIZE IT FIRST, no LP (design fixed here, measured after this file is pushed)

Read-only, no LP, through the **shipped path** only — `load_or_synthesize_bins` →
`bins_to_fleet` → `generators_to_fleet_arrays`, built twice from the keeper bundle's **own
`run_config.json`**, identical but for the one new field. Reusing caiso-185's instruments
(`scripts/probes/_caiso185_arm_capability.py`, `_caiso185_seasonal_stack.py`) as the
charter directs, extended to the **whole CAISO CC population**, not the 7 reconcile-table
plants.

Per CC plant, reported for **(a) the keeper** and **(b) the winter-basis arm**:

* LP `capacity_mw`;
* effective **summer** and **off-summer** capability, both `max_t(Σ tranches pmax ×
  availability)` (caiso-185's statistic, so the two sessions are commensurable) **and** the
  seasonal **mean**, since the anchors are mean-statistics;
* against **EIA-860 published summer / winter / nameplate**;
* against **CEMS seasonal p999** (`_caiso185_seasonal_stack`'s construction, the model's own
  `_SUMMER_MONTHS` mask, the deriver's `_CC_NET_OF_GROSS = 0.975`) — **as a CHECK only**.

**Reported totals:** GW·h of capability moved and **its sign, by season**
(`Σ_t Δ(pmax × availability)` over each season, summed over CC), plus the per-plant sign
split. `Σ_t` is used for the GW·h leg because that is what "capability moved" means as an
energy quantity; the max/mean statistics above carry the per-plant level story.

---

## 5. GATES — pre-registered, fail-closed, each sized on THIS mechanism's own physics

**None of these is keyed to caiso-185's contradiction ratios (a different instrument) or to
caiso-184's f_CEMS reduction.** No gate references a price, a residual or a benchmark.

| gate | bar | how scored |
|---|---|---|
| **G-DOF** | ledger **EXACTLY 11 / 8**. Any increase is an automatic FAIL. | The field is a **structural selector with no free parameter** — every value it introduces is an EIA-860 published rating or a ratio of two of them, identically to `cc_nameplate_summer_derate` and `unit_outage_lp_capacity_basis` (both booleans, both DOF-neutral, caiso-184 precedent). Attestation regenerated and diffed. |
| **G-NOFIT** | **ZERO fitted scalars.** Every capacity EIA-860-**PUBLISHED**. No value tuned to a residual. **No CEMS-derived number may enter a capacity slot or a multiplier** (§2). | Source audit of the diff + the probe record; the CEMS legs appear only under `*_check_*` keys. |
| **G-CHECKONLY** | The CEMS peak enters **only** as a check. | `git diff` over `src/` contains **no** CAMPD/CEMS read on any path reachable from `capacity_mw` or from `availability`. Fail is stop-the-line. |
| **G-NOCONTRA** | The arm must **NOT push any plant's effective seasonal capability below its own CEMS-demonstrated seasonal output, in EITHER season.** | Per plant, per season: FAIL if `capability_armed < CEMS_p999 × 0.99` **and** `capability_keeper ≥ CEMS_p999 × 0.99` (a NEW contradiction), or if an existing contradiction is **deepened** (`capability_armed < capability_keeper` while already below). A pre-existing contradiction that the arm **improves** is reported, not failed — it is the defect being repaired (plant 358). **A violation is stop-the-line: the arm is not solved.** |
| **G-MONO** | The sign rule is **stated and proved**, per plant. | **Stated now, before measurement.** Off the td path the off-summer factor is `winter/nameplate`: it **falls** for every plant with `winter < nameplate` (55 of the 67 CA CC plants; 4 are exactly 1.000) and **rises** for the 8 with `winter > nameplate` (7307 +8.87 %, 358 Mountainview +7.06 %, 56041 +6.92 %, 55985 +5.55 %, 54912 +5.00 %, 55970 +4.45 %, 55656 +2.57 %, 55933 +1.81 %). On the keeper's td path the incumbent off-summer level is the incidental `net_summer/mean(raw[summer])` (§1a), so the per-plant sign is `winter · mean(raw[summer]) / net_summer` vs 1 and is **weather- and zone-dependent**: it is MEASURED per plant in P0-3 and both signs are admissible. Summer: capability can only **fall or stay** (`B ≤ nameplate` wherever `winter ≤ nameplate`) and can only **rise or stay** where `winter > nameplate`. **A plant moving against its own published pair is stop-the-line.** |
| **G-SIXISO** | The other **five ISOs byte-unchanged**; no verdict transfers. | Default `False` on a freshly-built config for all six ISOs; every other ISO's default-config `cache_key()` unchanged vs `origin/main`; a fleet/availability identity diff on each of the six with the flag at its default; plus a **test** (`tests/`) pinning default-off, the parent-off no-op, and the CAISO-only reach. PJM/NYISO/NEISO **do** arm `cc_nameplate_summer_derate`, so default-off is what keeps them still. |
| **G-DENOM** | caiso-184's numerator/denominator identity **preserved bit-for-bit**. | `outages.py` is **NOT modified**. `_iso_plant_capacity(cc_nameplate_basis=True)` still returns **nameplate** (`net_summer ÷ (net_summer/nameplate)`), which is the basis of the extract's own `unit_capacity_mw` numerator, so the outage share stays the dimensionless `unit_nameplate / plant_nameplate` and is applied to whatever capacity the LP carries. Verified by asserting the map is identical on both arms. |
| **G-C1** | **C1 free-class fuelmix PASS on every free class, all three years.** | Scorer on the arm's own bundle. |
| **G-PROT** | **C6 and C8 PASS**; C8 stays **SCORED** (`legitimacy_diagnostics.json` registered with the bundle). | Scorer + committed diagnostics. |
| **G-LOYO** | Any verdict flip scored **leave-one-year-out within 2023-2025 BEFORE promotion.** | Only reached if a flip occurs. |
| **CONTROL** | **MANDATORY if any arm solves.** Reproduce the keeper via `--replay-bundle results/calibration/caiso184_c1_lpbasis` (**never** a remembered CLI string), re-measure the same-head identity at **FULL precision**, and **quote the noise floor BEFORE reading any treated delta.** caiso-184 measured this as **BIT-ZERO** (0 of 61,320 zone-hours). If it is no longer bit-zero, **that is a finding about the head** and is reported as one. | `scripts/probes/_caiso184_arm_identity.py`, reused. |

**Gate ordering is binding.** G-CHECKONLY, G-NOCONTRA, G-MONO, G-DENOM and G-SIXISO are
**pre-solve**. If any fails, **no LP is spent, nothing is registered, the keeper is
unchanged** — the caiso-185 kill-before-solve discipline. CONTROL is read **before** any
treated number.

---

## 6. P0-4 — DIRECTION, pre-registered HONESTLY as a HAZARD

**The dominant leg REMOVES capability off-summer** (59 of 67 CA CC plants have
`winter < nameplate`, some by 20-40 %), and removing capability **RAISES price**. The model
is already **+10.5 % (2024) / +13.1 % (2025)** over on C3a. **So the likely direction of this
arm is the WRONG one for the residual.** The Mountainview leg pushes the other way and is far
smaller (8 plants, +1.8 to +8.9 %).

**Pre-registered, binding:**

1. **A NET PRICE INCREASE IS ADMISSIBLE and does NOT refute the mechanism** (rule 1
   `[R-STRUCT]`: a structurally-correct mechanism is never judged by its effect on the fit,
   and never reverted because the residual didn't move). If C3a widens, the arm is still
   correct and the finding says so.
2. **A PRICE DECREASE IS NOT CORROBORATION.** It would be a coincidence of sign, and it will
   be reported as one — never quoted as evidence the basis is right.
3. **C3a is never the promotion basis.** The only promotion basis available to this session
   is that the model's CC capacity stops resting on an unpublished nameplate premise its own
   data refutes, in **both** seasons — i.e. G-NOCONTRA, G-MONO and G-NOFIT, plus the
   protective gates. **If the residual does not close — or widens — the finding SAYS SO in
   its headline.**
4. **No subsetting.** Arming the basis for some plants and not others (e.g. only the 8 that
   raise, or only the 6 that caiso-185 named) is a residual-fitted mechanism and is
   **FORBIDDEN** here exactly as PRECHECK-caiso185 §5 item 4 forbade it. The instrument is
   whole-population or nothing.
5. **No compensating factor.** If the arm moves capability more than expected in either
   direction, the response is to report it, not to add a scalar, a clamp or a blend.

---

## 7. P0-5 — BYTE-EQUIVALENCE AND SCOPE (the ercot-174 discipline)

* **BE-1** — flag defaults `False`; the **default-config `cache_key()` of all six ISOs is
  unchanged vs `origin/main`** (this is what the `_CACHE_KEY_OPTIONAL_FIELDS` registration
  buys, and its absence is exactly the caiso-184 §6 defect being avoided).
* **BE-2** — with the flag at its default, each of the six ISOs' **bin capacities and
  availability matrices are identical** to `origin/main` (measured, per ISO, not asserted).
* **BE-3** — with `cc_nameplate_summer_derate=False`, the flag is a **no-op** (so MISO/ERCOT
  cannot move even if it were flipped).
* **BE-4** — **a TEST**, not merely a measurement: default-off, parent-off no-op, the
  published-pair basis arithmetic, and the CAISO-only reach.
* **No data byte written.** No derive re-run (rule 23 `[R-FROZEN-DERIVE]` — nothing in this
  session is a re-derivation; the EIA-860 sheet is read, never written). sha256 ledger over
  the EIA-860 parquet and the CAISO CAMPD extract, before and after.
* `scripts/check_cache_key_registration.py` and `scripts/check_mechanism_matrix.py` both
  exit 0 before pushing.

---

## 8. ARMS AND THE SOLVE PLAN

Sequential (rule 12), each a single invocation covering **2023 + 2024 + 2025** (rule 16), one
bundle per arm:

1. **CONTROL** — `--replay-bundle results/calibration/caiso184_c1_lpbasis`, out-dir
   `results/calibration/caiso186_ctl`. Establishes the head noise floor. Read FIRST.
2. **ARM A** — the keeper recipe + `--cc-winter-capability-basis`, out-dir
   `results/calibration/caiso186_wintercap_A`.

**No third arm.** No subset arm, no parameter sweep, no variant chosen after a result.

**If a pre-solve gate fails, neither is run.**

---

## 9. DISPOSITION BRANCHES, fixed now

* **BRANCH A — PASS.** All pre-solve gates pass, both arms solve, protective gates pass.
  → Register the arm on the dashboard (rule 15) whatever C3a does, update the matrix cell
  from **this session's own evidence** (rule 28 duty b), and state plainly whether the
  residual closed, did not move, or widened. Promotion is considered **only** on the
  structural basis of §6.3, never on C3a, and any verdict flip is scored LOYO first
  (G-LOYO).
* **BRANCH B — PRE-SOLVE GATE FAILS.** → **Kill before solve.** No LP, nothing registered,
  keeper unchanged; the matrix cell is scored `R` (or `I` if the arm is provably inert) from
  this session's evidence, and the reason is filed at full magnitude.
* **BRANCH C — INERT.** The arm changes capability below a material threshold (**< 0.1 % of
  CC seasonal capability in both seasons**, i.e. indistinguishable from the head noise
  floor). → Report `I`, register nothing, spend no LP.
* **BRANCH D — G-NOCONTRA violation.** → **Stop-the-line.** Same as Branch B, and the
  finding states that this instrument repeats the caiso-185 failure mode despite §2.

**In every branch the mechanism-matrix cell is updated in THIS session** (rule 28 duty b),
rejections included, and the new field gets its **own verdict-bearing row in the same PR**
(duty c) with **every other ISO `U` or `.` and NO verdict transferred** (duty d) — except
that an ISO whose **own** committed keeper `run_config.json` arms a field is recorded as
armed (registration, not adjudication; the caiso-185 §8 precedent). Nothing is written to any
other ISO's extract, keeper shard, registry sidecar, status part, bench file or matrix cell.

---

## 10. THE STANDING DATA BLOCKER — not a session lever

C3a's first named contributor is the **WALLED hourly pumped-storage water state**
(FINDING-caiso140 §B / caiso-141 A2) — no public source, **OWNER-FUNDED INTAKE**. This
session attempts **no** proxy, **no** split heuristic and **no** PS mechanism tuned to the
level residual.

**If this lever is refused or proves inert, the CAISO in-model queue is EMPTY with every cell
adjudicated**, and the honest next step is **not** an eleventh lever: it is an owner sitting
on (a) funding the hourly PS water-state intake, and (b) whether CAISO should be declared
`CALIBRATED-WITH-CAVEATS` on a C3a ledger entry — **which rubric v3.1 currently FORBIDS**,
since C3c is the only ledgerable criterion and C3a is load-bearing. That question is put to
the owner rather than answered by inventing a lever.

---

## 11. Governance

Rule 1 `[R-STRUCT]` — structure first; the arm is judged on its basis, never on C3a, and a
price increase is pre-declared admissible (§6). Rule 11 `[R-ONE-MECH]`-adjacent / rule 19 —
this **REPLACES** a capacity basis, it does not stack a second derate on the first; the
off-summer leg is the mirror of the summer leg, not an addition to it. Rule 13
`[R-MEASURED]` — every input is an EIA-860 published rating, forward-reproducible for any
year and responsive to a re-rating; the CEMS record enters **only** as a check (§2). Rule 14
`[R-ACCURATE]` — accurate published data replaces an unpublished estimate, and the root
cause caiso-185 opened is taken rather than left. Rule 15 / 16 — if an arm solves, the full
2023-2025 bundle is registered on the dashboard in this session; no single-year keeper. Rule
21 `[R-DOF]` — ledger 11 / 8, G-DOF fail-closed. Rule 22 `[R-HOLDOUT]` — 2023-2025 only,
spend freeze respected, **both markers untouched (owner acts)**; CAISO holds no `complete`,
so no determination re-key is owed. Rule 23 `[R-FROZEN-DERIVE]` — no derive re-run, no data
byte written. Rule 24 `[R-REGISTRY]` — one registered `ScenarioConfig` field, in
`run_config.json`, cache-key-registered in the same commit; no env knob, no hardcoded
per-plant dict, no `getattr` fallback literal. Rule 25 `[R-ISO-SCOPE]` — CAISO only; the
ratio IS each plant's own published rating, so no parameter crosses a boundary. Rule 27
`[R-PUSH]` — this pre-registration is pushed and blob-verified before any measurement of the
object and before any LP; every push verified by commit-SHA round trip; no existing
≥300-line file rewritten from regenerated content. Rule 28 `[R-MECH-MATRIX]` — duty (a) in
§0, duty (b) and (c) in §9, duty (d) in §9.
