# PREREG — miso-141: the flat `SUMMER_CLASS_DERATE` against a net-summer `pmax` basis

**Session** miso-141, 2026-08-07, branch `claude/miso-141-summer-derate-qeynwi`.
**Charter** §5.4 **QUEUE ITEM 2** (queue head since miso-140, owner-selected
2026-08-06): *the flat summer capacity haircut vs the net-summer `pmax` basis*,
rule 14 `[R-ACCURATE]`.

**Pushed BEFORE any adjudicating statistic.** Everything already read at the
time of writing is disclosed in §2 so the prior below is calibrated honestly
rather than retro-fitted.

**NOT A LEVER.** miso-139 §7 bounds the whole capability family at **30–39×**
too small to move MISO's summer-afternoon marginal unit. **No C3a claim may
attach to any outcome of this session**, in either direction, and none will be
made. Owner directive honoured: the standing target is the 2024/2025 mean-LMP
level miss; **no C7 lane is chartered and no C7 ledger is sought.**

---

## 0. §0 re-verified from committed artifacts (not from the prompt)

`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`
at HEAD, committed artifacts only, **no re-solve**, all three years in one
invocation (rule 16):

* **`NOT-YET`**, rubric **v3.1**, **8** criteria
  (`fuelmix`, `sysvol`, `price_mean`, `price_shape`, `price_tail`,
  `dispatch_corr`, `governance`, `forced_share`).
* **SOLE FAIL — C3a `price_mean`**, on the scorer's own basis string
  *"undocumented out-of-tolerance (FAIL) criteria: price_mean"*.
  RT load-weighted: **2023 32.72 vs 32.85 = −0.4 % PASS · 2024 30.37 vs 32.30 =
  −6.0 % PASS · 2025 39.05 vs 45.46 = −14.1 % FAIL** (`MODEL MISS`).
  DA companions (diagnostic, not gated): **−4.4 / −8.4 / −15.8 %**.
* **C3b `price_shape` PASS**, NRMSE **0.075 / 0.112 / 0.191** — 2025 sits close
  to the ≤0.20 bar and is watched on any arm.
* **C3c `price_tail` — the SOLE ledgered caveat, 1 of 1** (`ledgered_max: 1`);
  protective ledger budget spent 0.
* C1 / C2 / C4 / C6 / C8 **PASS**. C8 carries three *grounded-above-budget*
  ST_GAS notes (31.9 / 33.1 / 45.1 % forced, all clearing D-4 + D-1).

**Identical to the charter §0 in every cell.** Determination, fail set and
ledger budget are unchanged by this session's reading.

**Rule 22 `[R-HOLDOUT]`** — `frontend/data/backcast/calibration-complete.json`
carries **no MISO entry in either block**. Only **2023 / 2024 / 2025** are read,
and no year outside that set is solved, scored or registered.

---

## 1. The object, stated precisely

MISO's keeper (`results/calibration/miso132_ccmin_B/run_config.json`) runs:

| field | keeper value |
|---|---|
| `cc_nameplate_summer_derate` | **False** |
| `coal_nameplate_summer_derate` | **False** |
| `plant_level_fleet` | True |
| `use_campd_bins` | True |
| `temp_dependent_derate` | True, `temp_derate_classes = ['CT_CHP','ST_CHP']`, `temp_derate_mean_anchored = **True**` |
| `gt_ambient_derate` | False |

`SUMMER_CLASS_DERATE` (`config/fuel_trajectories.py:950`) removes a flat
**CC_REGULAR/CC_CHP 0.10, CT_PEAKER/CT_CHP 0.125** from availability in Jun–Sep
(`data/fleet/arrays.py:737-745`), and `pmax` is loaded as
`net_summer_capacity_mw` (`data/fleet/eia860.py:1007`).

**One charter-scope correction I make in advance, from the code rather than from
the number.** `_td_covers` (`arrays.py:568-584`) returns **False in
mean-anchored mode by construction** — the mean-anchored curve is a pure SHAPE
overlay that composes *on top of* the level treatment rather than replacing it.
The keeper sets `temp_derate_mean_anchored = True`, so **all four**
`SUMMER_CLASS_DERATE` classes take the flat derate, **CT_CHP and CC_CHP
included**. The charter's four-class scope is therefore right, and it is right
for a reason worth stating: had the keeper been in hinge mode, CT_CHP would have
been out of scope. Scope is measured, not assumed.

---

## 2. What I have already read (disclosure — this moves my prior, and it must be visible)

Before writing this document I read, and I record it rather than pretending to
a flat prior:

1. **The constant's own provenance comment** (`fuel_trajectories.py:934-949`)
   declares the magnitudes an **"UNCITED FLAT APPROXIMATION"** of a real
   physical effect — *"consistent with, but not derived from, the 10-30 %
   typical CT summer derate the repo's own capacity audit records **against
   EIA-860 net-summer ratings**"*.
2. **`docs/capacity-audit-860-923-campd.md:134`** frames `_SUMMER_CLASS_DERATE`
   as the model's handling of *"105 plants where the CT/ST summer capacity is
   below nameplate (typical 10-30 % for CTs due to ambient temperature)"* — i.e.
   as a **nameplate→net-summer** object.
3. **`docs/parameter-citations.md:895-896`** carries
   `summer_class_derate.CT_PEAKER` / `.CT_CHP` = 0.125 tagged
   **`needs-citation, modeled`**.
4. **`campd_bins.cc_summer_capacity`'s own docstring** calls the
   `cc_nameplate_summer_derate=True` treatment *"the correct seasonal capacity
   shape (full nameplate in winter, ambient-derated to net-summer in summer)"*.

So the *provenance* gate is close to pre-answered by committed text, and I will
not claim credit for confirming it. **The gates that actually carry this session
are the MAGNITUDE and BASIS gates (G-2/G-3), which nothing on record measures**,
and the one test that settles the question **without reference to provenance at
all** (G-3b).

**An absence claim is a measurement, not a premise** (miso-136). I will not
infer "uncited" from the comment saying so — G-1 searches the full git history
of the constant and the whole repo for a derivation artifact.

---

## 3. Gates, with decision rules fixed in advance

### G-1 — PROVENANCE (gating for interpretation, not for the verdict)

Exhaustive, and reported whatever it returns: (a) `git log -S` over
`SUMMER_CLASS_DERATE` / `_SUMMER_CLASS_DERATE` / the literals `0.125` in the
defining module, back to introduction, reading every touching commit message;
(b) repo-wide search for any derive script, sweep, PREREG, handoff, or
calibration-log entry that produces the pair; (c) the
`docs/parameter-citations.md` row.

**Pre-committed interpretation map:**

* **P-A — "nameplate→summer" identification.** The record identifies the number
  as the nameplate-to-net-summer ambient gap ⇒ applying it to a net-summer base
  is a **DOUBLE COUNT on provenance**.
* **P-B — "blend / incremental" identification.** The record identifies it as a
  forced-outage+ambient blend, or as an *incremental* loss below the net-summer
  rating point ⇒ **a different object**, no provenance double-count; the
  question then stands or falls on magnitude alone (G-3b).
* **P-C — NO identification exists.** Provenance settles nothing and the verdict
  is decided entirely by G-2/G-3/G-3b.

**P-C is not a finding of guilt.** An uncited constant may still be the right
magnitude (Trap 2).

### G-2 — THE BASIS, measured per unit (GATING)

Build MISO's fleet through the model's own loader under the keeper config
(`load_fleet_from_csv` → `generators_to_fleet_arrays` → `_availability_matrix`,
the miso-139 construction, so every overlay and the trailing
`np.clip(availability, 0, 1)` are the code's own). For every
CC_REGULAR / CC_CHP / CT_PEAKER / CT_CHP generator, compare the LP's `pmax`
against that plant's EIA-860 **nameplate** and **net-summer** sums.

**Decision rule (fixed now):** basis is confirmed net-summer iff **≥95 % of each
class's LP capacity** matches its EIA-860 net-summer figure to within **1 %**.

**Counter-branch, and it kills the hypothesis if it fires:** if MISO's gas
`pmax` turns out to be **nameplate** (e.g. a CAMPD-bin path that carries
`Nameplate_MW`, as ERCOT's does), then there is **no double count**, the flat
derate is doing exactly the job the audit doc describes, and the session reports
that and stops. **This is the branch on which the whole charter is wrong**, and
it is checked first for that reason.

### G-3 — THE MAGNITUDE, measured (GATING for size)

Per class, per year, on the same fleet: the EIA-860 **nameplate**, **net-summer**
and **winter** capability sums; the ratios `net_summer/nameplate` and
`winter/net_summer`; and the model's **stacked** summer capability
(`pmax × availability`, all overlays live) expressed against **nameplate** and
against **net-summer** — so the excess removal is a measured MW quantity, not an
inference.

**Materiality bar (fixed now):** an excess **> 2 %** of the class's summer
capability is material; ≤ 2 % is reported and closed as immaterial.

### G-3b — THE DECISIVE TEST, and it does not depend on provenance

If the flat derate is interpretation **P-B** — an *incremental* ambient loss
below the net-summer rating point — its magnitude is bounded by the measured
ambient swing between the rating condition and actual summer hours. MISO's own
slopes are already measured and committed (miso-139 G-1,
`_miso139_derate_gates.json`): **CT_PEAKER 0.00363/°C, CC_REGULAR 0.00192/°C**.

Two pre-registered sub-tests:

* **G-3b(i) MAGNITUDE.** implied incremental = `slope × (T̄_summer_hours −
  T_rating_point)`, with the rating point taken as the measured summer **peak**
  dry-bulb (EIA net-summer is a summer-peak capability rating). **Bar: if the
  flat derate exceeds 3× the implied incremental, P-B is REFUTED as an
  explanation of the magnitude**, whatever the provenance says.
* **G-3b(ii) SIGN.** the mean summer hour is cooler than the summer-peak rating
  condition, so an honest incremental-below-net-summer treatment is on average
  an **UPRATE**. **If the measured `T̄_summer_hours − T_summer_peak` is
  negative in ≥90 % of zone-years, a flat 10–12.5 % DERATE has the wrong SIGN
  for P-B.**

### G-4 — REACH (diagnostic, NOT licensing)

*Method bar, miso-139:* **bound the next candidate against the ~12 GW cushion
before a solve is spent.** Restored summer-afternoon (h12–17) capability in MW
against the measured 13.7–18.8 GW idle cushion, from the keeper's own committed
`hourly/` sidecars. Reported as a bound on what any repair can do — **never as a
C3a claim**, and the sign is disclosed in advance in §4/P5: this repair **adds**
capability, so it pushes prices **down**, i.e. the **wrong way** for a model
already −14.1 % low in 2025.

### G-5 — TREATMENT CONSISTENCY across ISOs (diagnostic)

Which ISOs' current keepers run `cc_nameplate_summer_derate` on vs off, and what
effective `summer capability / nameplate` each treatment yields. **Rule 25
`[R-ISO-SCOPE]` observed:** this is a *consistency* reading of committed
configs — **no parameter is transferred into MISO from any other ISO, and no
other ISO's matrix cell is touched** (rule 28(d)).

---

## 4. Prior — two-sided, with falsifiable numbers

| # | prediction | conf. |
|---|---|---|
| **P1** | G-1 returns **P-C or P-A** — no derivation artifact for the pair exists in the repo or in the constant's full git history, and the constant has **never been changed** since introduction | 0.75 |
| **P2** | G-2 confirms the **net-summer** basis: ≥95 % of each class's LP capacity within 1 % of EIA-860 net-summer | 0.85 |
| **P3** | measured MISO **`net_summer/nameplate`**: CC **0.92–0.97**, CT **0.85–0.94**. *(These are NOT miso-139's +8.3 %/+15.8 % — see Trap 1.)* | 0.60 |
| **P4** | the stacked summer capability sits **≥ 9 % (CC) / ≥ 11 % (CT)** below the published net-summer rating for ≥95 % of affected capacity — i.e. the excess is material by the G-3 bar | 0.90 |
| **P5** | G-4 restored summer-afternoon capability **2.5–4.5 GW** — **5–9×** the ambient family's 456–497 MW reach, yet still **3–7× inside** the 13.7–18.8 GW cushion | 0.55 |
| **P6** | **no single existing `ScenarioConfig` field expresses the correction for all four classes** (there is a CC flag, `cc_nameplate_summer_derate`; there is **no** CT analogue) ⇒ **no arm, no solve this session** | 0.70 |
| **P7** | G-3b(ii): `T̄_summer_hours − T_summer_peak` is **negative in ≥90 %** of MISO zone-years, so P-B has the wrong sign | 0.85 |
| — | **P(an arm is licensed AND solved this session)** | **0.20** |

**The other side — three ways I expect to be wrong, stated before the fact.**

1. **P-B may be right and my sign argument may be too clever.** EIA-860
   net-summer is a *self-reported registration* rating, not a measurement at a
   controlled condition; plants may report conservatively, and a real fleet may
   genuinely sit below its own registered summer rating in hot hours for reasons
   (auxiliary load, condenser limits, degradation) that are not the linear
   ambient term G-3b models. If so the flat derate is a crude but non-empty
   object and "double count" overstates it.
2. **The CC branch may be a trap of its own.** Arming
   `cc_nameplate_summer_derate=True` raises the *winter* base to nameplate as
   well as re-anchoring summer. That is a **year-round capability increase**,
   and the miso-139 Trap-1 lesson cuts both ways: a change sold as a basis
   correction that moves annual capability is a level move and must be reported
   as one. I may find the "accurate" fix is itself a level lever in disguise.
3. **A partial fix may be worse than no fix.** If only CC is armable and CT is
   not, the fleet ends up internally *inconsistent* across two classes that
   compete on the same margin. Rule 14's "keep the accurate input" does not
   obviously license half of it.

---

## 5. Look-alike traps, named in advance with their counter-measurements

* **TRAP 1 — THE BASIS CROSSING, and the charter itself commits it.** The
  charter quotes miso-139's **summer↔WINTER** spread (CC +8.3 %, CT +15.8 %;
  unit-p50 +8.2 %/+8.8 %) against a flat derate the audit doc frames as a
  **nameplate→SUMMER** gap. **Different numerator, different denominator, three
  distinct ratings.** *Counter-measurement:* report **nameplate, net-summer and
  winter separately** with both ratios named, and **never** substitute one for
  the other. *(Method bar: ONE basis; check basis crossings.)*
* **TRAP 2 — "UNCITED ⇒ WRONG".** The absence of a derivation is not evidence of
  the wrong magnitude. *Counter-measurement:* the verdict rests on **G-3/G-3b
  measured magnitudes**, and would be identical if the constant carried a
  citation.
* **TRAP 3 — THE DERATE IS NOT THE ONLY SUMMER TERM** (rule 19
  `[R-ONE-MECH]`). Also acting on MISO summer capability:
  `THERMAL_AVAILABILITY` (WEFOR + DERATE + POF), `SUMMER_WEFOR_SHARE = 0.30`,
  the mean-anchored `temp_dependent_derate` shape overlay, `gt_ambient_derate`
  (off), `COAL_SUMMER_MAX_CF` / `COAL_MAX_CF_BY_PLANT` (coal only),
  `BIN_FORCED_DERATE_BY_YEAR` (backcast). *Counter-measurement:* a **term-by-term
  attribution** of the summer capability stack off the model's own availability
  matrix before any excess is attributed to `SUMMER_CLASS_DERATE`.
* **TRAP 4 — THE FIX WEARING LEVER CLOTHES.** Any C3a movement is disqualified
  in advance, in **both** directions: the family is bounded 30–39× too small
  (miso-139 §7) and the repair moves capability **up** in a model already 14 %
  **low**. *Counter-measurement:* pre-committed here — **no C3a number is quoted
  as evidence for or against the repair**, and the verdict is decided on basis
  correctness alone.
* **TRAP 5 — THE PROBE-HYGIENE HAZARD (miso-140b §6, binding).** `load_demand`
  **silently** returns a different zonal split when the repo root is off
  `sys.path` (up to 6,747 MW per zone-hour on MISO 2025). *Counter-measurement:*
  every probe this session writes inserts the **repo root** (not only `src/`)
  and **asserts `load_zonal_shares(...) is not None`** before any per-zone
  quantity is computed — enforced whether or not the probe reads demand.

---

## 6. Stop rules and solve posture

* **G-2 counter-branch fires (basis is nameplate) ⇒ STOP.** Report "no double
  count", close the queue item, no arm.
* **G-3 excess ≤ 2 % ⇒ STOP.** Immaterial; report and close.
* **P6 confirmed (no single field covers all four classes) ⇒ NO ARM, NO SOLVE.**
  Report the measured basis defect, **specify** the successor mechanism, and
  leave it as an explicit **owner decision** — the miso-139 §10(3) discipline.
  If no LP is solved there is **no run to register** (rule 15; the
  miso-131…140b precedent).
* **Only if** a single existing mechanism expresses the whole correction: same-HEAD
  **zero-delta control FIRST**, then `replay_keeper --set`, **one invocation per
  arm**, `--years 2023 2024 2025` in a **SINGLE** invocation, arms sequential
  (rules 12/16), swap enabled before any solve on this 15 GB host. Every such run
  is registered in this session (rule 15).
* **Rule 14 is honoured as written**: if an arm is licensed and the backcast gets
  **worse**, the accurate input **stays** and the worse fit is reported as a
  discovered root-cause issue — it is never reverted to recover a number.

## 7. Governance

**Rule 13** every input is a physical/registration quantity (EIA-860 ratings,
zone dry-bulb, the model's own availability matrix), forward-reproducible; **no
price, benchmark or model price output enters any estimator**. **Rule 19** no
mechanism stacked — the existing summer-capability treatments are enumerated and
reconciled (Trap 3). **Rule 21** no free parameter added. **Rule 23** no derive
script re-run against a residual. **Rules 24/25** no tuning channel created; no
non-MISO parameter armed for MISO and no other ISO's artifact written. **Rule
28(b)** any mechanism actually tested gets its cell + §5.4 queue stamp in **this**
session, rejections included. **Rule 27** pushed blobs verified. **Owner
directive** no C7 work.
