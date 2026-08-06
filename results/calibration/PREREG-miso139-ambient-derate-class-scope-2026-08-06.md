# PREREG — miso-139: ambient capability-derate CLASS SCOPE for MISO's merchant thermal fleet

**Session:** miso-139, 2026-08-06, branch `claude/miso-ambient-derate-scope-e4t0v6`.
**HEAD at pre-registration:** `dd4e919cc69a1abe4a976bdf326f5df48a10635a`.
**Pushed BEFORE any adjudicating statistic.** Everything below is written from
(a) source code read at HEAD, (b) the committed keeper artifacts re-verified in
§0, and (c) the two prior findings. **No G-0, G-1 or G-2 quantity has been
computed at the time of this commit.**

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss.
No C7 lane is chartered and no C7 ledger is sought.

---

## §0 State of record, RE-VERIFIED from committed artifacts (not from the charter)

Source: `scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed
--json` at HEAD, over the committed bundle `results/calibration/miso132_ccmin_B`.

| | value |
|---|---|
| keeper | `2026-08-05-miso-132b-cc-committed` |
| determination | **NOT-YET** |
| criteria scored | 8 (C1, C2, C3a, C3b, C3c, C4, C6, C8) |
| **sole FAIL** | **C3a `price_mean`** — *"undocumented out-of-tolerance (FAIL) criteria: price_mean"* |
| ledgered caveats | **1 of 1** — C3c `price_tail` only |
| protective | C6 governance **PASS**, C8 forced-share **PASS** |

C3a per year (RT load-weighted, Indiana Hub), and the DA diagnostic companion:

| year | model | actual RT | C3a | DA diagnostic |
|---|---:|---:|---:|---:|
| 2023 | 32.72 | 32.87 | **−0.5 % PASS** | −4.4 % |
| 2024 | 30.37 | 32.27 | **−5.9 % PASS** | −8.3 % |
| 2025 | 39.05 | 45.39 | **−14.0 % FAIL** | −15.6 % |

**TWO CHARTER §0 CORRECTIONS, recorded rather than carried silently.**

1. The charter states *"NOT-YET; sole FAIL C7 shape 2025"*. **C7 is not a scored
   criterion at HEAD.** The standalone C7 diurnal-shape gate was RETIRED by the
   rubric v3.1 owner amendment 2026-08-06 (CLAUDE.md rule 20 `[R-FORCED-BUDGET]`),
   and MISO's blocker moved C7 → C3a the same day
   (`docs/calibration-log/miso.md`, entry "MISO blocker moves C7 → C3a under
   rubric v3.1"). The sole FAIL is **C3a**.
2. The charter states *"ledgered caveats {C3a, C3c}"*. Under v3.1 **C3c is the
   only ledgerable criterion at all**, so the bundle's `price_mean` ledger entry
   is no longer admissible and C3a scores as an **undocumented FAIL**. Ledger
   budget spent: **1 of 1**, on C3c.

Neither correction changes the target: it is the same 2024/2025 mean-LMP level
miss, and it now carries the determination directly.

**Rule 22 `[R-HOLDOUT]`:** `frontend/data/backcast/calibration-complete.json`
carries `complete` for **NEISO, NYISO, PJM** and MISO is in **neither** block.
**2023, 2024, 2025 ONLY.** No out-of-training year will be read, solved, scored
or registered this session.

---

## §1 The object, and the chartered lever

**The object (miso-137, not re-derived here).** MISO's price error is a
**compressed price distribution**: over-priced below ~$40, under-priced above
it, monotone in the actual price level with no break; mirrored on the clock —
summer h12–17 model 44.24 vs actual 74.68 (−41 %, 39 % of the 2025 RT gap),
summer h00–05 model 33.40 vs actual 28.41 (+18 %). A LEVEL lever is disqualified
on its face; the admissible family **steepens the stack** where measured conduct
says it is steep.

**The chartered lever.** `ScenarioConfig.temp_dependent_derate` is **already
armed** on the keeper and scoped to cogen only — a **scope + identification**
question, not a new mechanism, so rule 19 `[R-ONE-MECH]` is satisfied. Keeper
`run_config.scenario_config`, read this session:

```
temp_dependent_derate    = True
temp_derate_classes      = ['CT_CHP', 'ST_CHP']
temp_derate_mean_anchored= True
temp_derate_hourly_grain = True
temp_derate_ref_c        = 15.0        temp_derate_ref_c_coal = 25.0
temp_derate_slope_ct_chp = 0.00141     temp_derate_slope_st_chp = 0.00141   (MISO-MEASURED)
temp_derate_slope_ct     = 0.0126      temp_derate_slope_cc   = 0.0076
temp_derate_slope_st_gas = 0.0054      temp_derate_slope_coal = 0.0040       (LITERATURE, INERT out of scope)
gt_ambient_derate = False · cc_nameplate_summer_derate = False · coal_nameplate_summer_derate = False
```

**Three code facts established by reading `src/market_sim/data/fleet/arrays.py`
and `eia860.py` at HEAD** — stated now because they drive §3, and because they
are code, not measurements:

* **F1. `pmax` IS the EIA-860 net-summer rating.** `eia860.py:998` —
  `pmax = net_summer_capacity_mw`, falling back to nameplate only when absent.
* **F2. In mean-anchored mode the flat summer class derate is RETAINED.**
  `arrays.py:568-584` — `_td_covers()` returns `False` whenever `_td_anchored`,
  by design ("a pure SHAPE overlay with annual mean 1.0 … composes ON TOP of the
  existing level treatment"). So the armed classes keep
  `SUMMER_CLASS_DERATE = {CC_REGULAR 0.10, CC_CHP 0.10, CT_PEAKER 0.125,
  CT_CHP 0.125}` on Jun–Sep hours **and** take the temperature curve on top.
  `COAL` and `ST_GAS` carry no flat summer derate.
* **F3. The uprate half is TRUNCATED by the trailing clip.** `arrays.py:868-878`
  — mean-anchored multiplies by `max(raw, 0)` deliberately un-clipped, but
  `np.clip(availability, 0, 1)` immediately follows, so any hour where
  `availability_base × raw > 1` loses the excess. The comment acknowledges this
  ("the trailing clip on availability still bounds the result at the pmax
  basis"). Whether that truncation is material is a §3 measurement.

---

## §2 My prior — two-sided, stated before any measurement

**Which way I lean, and why (so it can be scored against me).** I expect the arm
**as chartered** — i.e. "already armed, just re-scope" — to fail G-0 on its own
arithmetic, for a reason the charter's mechanism sentence gets wrong:

> charter: *"Applied to summer it derates h12–17 … and uprates h00–05 (adding
> cheap supply where the model over-prices). That is the SIGN REVERSAL within
> one season and one fleet that miso-137 demands."*

With an **ANNUAL**-mean anchor in a continental-climate ISO, **every summer hour
sits above the annual mean**, so `raw = 1 − slope × (T − T̄_annual) < 1` in
h00–05 as well as h12–17. The arm would derate **both** summer windows — more in
the afternoon, less at night — and the genuine uprate leg would land in
**winter**, where F3 then truncates part of it. If that is what the numbers say,
the charter's sign reversal is not delivered by convention (A), and the
`h00–05` over-pricing gets *worse*, not better.

**Numeric predictions, registered so they can be falsified:**

* **P1.** Zone-mean summer h00–05 dry-bulb exceeds the zone annual-mean dry-bulb
  in **all 6 MISO zones in all 3 years** ⇒ `raw < 1` in both summer windows.
  *Confidence 0.9.*
* **P2.** Under convention (A) the summer h12–17 capability of an armed merchant
  class falls **below** its net-summer basis after the retained flat derate —
  i.e. a genuine double-derate against F1. *Confidence 0.8.*
* **P3.** MISO's OWN identified slope is **materially smaller** than the
  committed literature slope for the same class — I predict the EIA-860 route
  returns CT in the range **0.0015–0.0040 /°C** against the committed 0.0126
  (a ~3–8× gap), on the arithmetic that a +0.076 summer→winter capability spread
  spread over a summer-peak↔winter-peak dry-bulb difference of order 30–40 °C is
  ~0.002/°C. *Confidence 0.7.* (Cross-check that points the same way and is
  already committed: MISO's own CAMPD within-day cogen estimate is **0.00141**,
  9× below the literature CT value.)
* **P4.** In ≥60 % of summer h12–17 hours the MW the identified derate removes is
  smaller than the model's own unloaded headroom on units at or below the
  marginal offer, i.e. no marginal-unit change. *Confidence 0.6.*

**Net:** P(an arm is licensed and solved) ≈ **0.45**; P(it materially moves the
summer h12–17 window) ≈ **0.25**.

**THE OTHER SIDE — the three ways I expect to be wrong, written so they can win.**

1. **Convention (B) may be both admissible and exactly right.** The non-anchored
   branch already implements a **net-summer anchor** (`arrays.py:847-867`): the
   curve *replaces* the flat summer derate and is rescaled so its Jun–Sep mean
   equals `1 − SUMMER_CLASS_DERATE`. About a **summer** anchor the sign reversal
   is real and within-season: afternoons below the summer mean derate, nights
   above it uprate. If that convention is reachable without disturbing the
   committed CHP identification, the charter's mechanism is delivered and my
   lean is simply wrong.
2. **EIA-860's summer/winter spread is a LOWER bound on the instantaneous
   ambient response.** Both ratings are demonstrated at peak-period conditions,
   and the winter rating is frequently limited by non-ambient factors, so P3 may
   understate the true slope; a capability-envelope estimator on MISO's own CAMPD
   could return materially more.
3. **A small MW removal is not a small price effect.** miso-137's whole finding
   is that the model's summer-afternoon stack is too flat *in price*; that says
   nothing about whether it is flat *in quantity*. If the marginal segment is a
   peaking tranche at 2.25× MC, a modest displacement can move price a lot. G-2
   measures headroom, and headroom is not a price prediction (miso-134).

---

## §3 G-0 — ANCHORING / DOUBLE-COUNT (GATING). Convention fixed BEFORE any solve.

**What is measured** (MISO's own committed inputs only — the same
`iso_zone_hourly_drybulb` the LP consumes, and the same 6 zones):

* **G-0(a)** the per-zone, per-year annual-mean dry-bulb anchor; the summer
  (Jun–Sep) mean; and the mean in the two miso-137 windows h12–17 and h00–05.
* **G-0(b)** the resulting `raw(t)` per candidate class in each window, under
  each candidate convention, and the **total summer-afternoon capability
  relative to the net-summer basis** after F2's retained flat derate — the
  double-count test proper.
* **G-0(c)** the **truncation** F3 causes: share of hours, and share of
  class-MWh of intended uprate, lost to `np.clip(availability, 0, 1)`.
* **G-0(d)** the **annual capability integral** per class under each convention,
  relative to control. A convention whose annual integral is materially below
  control is a level cut wearing a shape mechanism's clothes (see §6).

**The candidate conventions, enumerated in advance:**

| | convention | what it is |
|---|---|---|
| **(A)** | `temp_derate_mean_anchored=True` | the currently-armed CHP convention: annual-mean anchor, flat summer derate RETAINED, uprate truncated by F3 |
| **(B)** | `temp_derate_mean_anchored=False` | hinge at `ref_c` + net-summer anchor: curve REPLACES the flat summer derate, Jun–Sep mean pinned to `1 − SUMMER_CLASS_DERATE` |
| **(C)** | — | neither is admissible without a new field/mechanism |

**PRE-COMMITTED DECISION RULE — decided on basis consistency, NEVER on a price
outcome.** `pmax` is the net-summer rating (F1). The physically consistent
convention is therefore the one whose **summer-hours mean capability equals the
class's net-summer basis** — capacity-neutral *within summer*, reshaped inside
it. I adopt the convention that satisfies this to within **±1 % of the class's
summer-mean capability**, measured in G-0(b). If both satisfy it, (A) is
preferred as the smaller delta from the committed keeper. If neither does, the
verdict is **(C) REFUSED-AT-G0** and no solve is spent.

**Explicit constraint, registered now.** `temp_derate_mean_anchored` is a single
global bool, so selecting (B) would also move the committed **CT_CHP / ST_CHP**
classes off the convention their 0.00141 slope was identified under
(`derive_campd_temp_derate_params.py`, mean-anchored no-hinge form). **I will not
silently re-treat CHP.** If (B) is the physically correct convention for the
merchant classes, the honest outcome is that the arm needs a per-class
convention — a mechanism change, which this session is not chartered to make —
and that is reported as the finding under branch (C), not worked around.

**Stop rule.** If G-0 returns (C), the session reports the anchoring finding and
**stops before any solve**. Per the charter: *"If it double-counts as configured,
that is the finding, not a reason to re-cut."*

---

## §4 G-1 — IDENTIFICATION, MISO-OWN (GATING). Zero fitted values.

Rule 25 `[R-ISO-SCOPE]` is binding: pjm-95 refuted the committed literature
slopes on PJM's own CAMPD, so **MISO may not inherit them**, and
`temp_derate_slope_ct/_cc/_st_gas/_coal` as shipped are **not armable for MISO**
unless MISO's own data reproduces them.

**E1 — PRIMARY: the EIA-860 MISO two-point ambient slope.** Per class `k`,

```
slope_k = (C_winter_k − C_summer_k) / ( C_summer_k × (T_sum_peak − T_win_peak) )
```

* `C_summer_k`, `C_winter_k`: MISO class-aggregate EIA-860 **Net Summer** and
  **Net Winter** capacity, from the committed EIA-860 the model already loads,
  on the model's own `plant_group` taxonomy and the model's own MISO fleet
  membership. (miso-138 measured the per-unit ratio distribution; E1 uses the
  class aggregate, and I will report both aggregate and unit-p50 forms.)
* `T_sum_peak`, `T_win_peak`: the **load-weighted mean zone dry-bulb** over
  MISO's own measured summer-peak and winter-peak hours, computed from the
  identical `iso_zone_hourly_drybulb` series the LP consumes and the identical
  committed MISO demand. **No assumed design temperatures.**

Zero free parameters; every input measured; forward-reproducible (rule 13 —
the same construction regenerates for a forward year from forward weather and
responds when conditions change).

**E1 robustness set, pre-registered.** The peak-hour definition is varied over
**{top-0.5 %, top-1 %, top-5 % of load within the season, the single annual peak
day}**. If `slope_k` moves by more than **±30 % relative** across that set for a
class, that class's identification is declared **UNSTABLE** and it is **NOT
ARMED**.

**E2 — CROSS-CHECK ONLY: the CAMPD within-day estimator.**
`scripts/data/derive_campd_temp_derate_params.py` is the frozen instrument
(rule 23) and its MISO CHP run is committed. **Its identifying assumption fails
for merchant units and I name that now**: the script's own scope note says a
pinned cogen "has no dispatch freedom, so its metered output IS its hourly
capability." A merchant CT's within-day output is **dispatch**, and dispatch is
positively correlated with temperature through load — so a naive within-day
regression on merchant units is confounded with the wrong sign. **E2 may never
set a parameter in its pinned-unit form.** It is reported as a cross-check, and
the only merchant-admissible variant is a **capability-envelope** construction
(per-unit upper envelope of gross load within temperature bins, which does not
assume pinning). If E1 and the envelope construction disagree by more than **2×**
on a class, that class is declared **UNSTABLE** and **NOT ARMED**.

**Pre-registered class exclusion.** miso-138 measured EIA-860 MISO **COAL derate
p50 +0.000 with 70.4 % of units exactly flat** — correctly no ambient derate.
I will re-verify that from the committed EIA-860 this session; if it reproduces,
**COAL is excluded a priori**. That is a measured exclusion, not a scope choice.

**Refusal condition (rule 20 `[R-DOF]`).** If no admissible estimator returns a
slope for a class without a fitted value, that class is an **open root-cause
issue, not a parameter**, and it is not armed. If that empties the scope, the
verdict is **REFUSED-AT-G1** and no solve is spent.

**Forbidden by construction (rules 1/13/21/24).** No window, magnitude, hour set
or price number from miso-137 — or from any residual — may enter any estimator,
any bound, or any class-selection decision. The estimators never see a price, a
benchmark, or a model output.

---

## §5 G-2 — BINDING (diagnostic, NOT licensing)

Measured on the keeper's **own committed hourly sidecars** (`class_hourly_*`,
`system_*`, `reserve_family_*`) — no re-solve:

1. the marginal class in summer h12–17 hours, and the model's price there;
2. the **MW the identified derate would remove** per class in those hours;
3. the model's **unloaded headroom** on units at or below the marginal offer in
   the same hours;
4. the count and share of window hours where (2) exceeds (3) — the only hours
   where a marginal-unit change is even arithmetically possible.

**BINDING IS NOT LICENSING (miso-134), and it runs both ways.** A binding count
does not license a price claim; an inertness count does not license skipping the
solve. G-2 gates *what may be claimed*, never *whether the solve happens*.

---

## §6 The look-alike traps — named in advance, with pre-committed counter-measurements

**TRAP 1 — A LEVEL CUT WEARING A SHAPE MECHANISM'S CLOTHES.** By F2+F3, a
mean-anchored overlay applied on a base that keeps its flat summer derate, with
its uprate half truncated at `availability = 1`, is **net a capability
reduction**. Summer prices would rise and summer h12–17 would "improve" — and it
would be the disqualified LEVEL family (miso-137 §7) delivered through a quantity
channel. **Counter-measurement, pre-committed:** report the **annual and
per-season capability integral** (class-MWh of `pmax × availability`) of arm vs
control, per class, in the finding. **If the arm removes net annual capability,
it is reported as a level lever regardless of what C3a does**, and its C3a
movement is not quotable as a compression fix.

**TRAP 2 — THE TAIL CHANNEL WEARING THE BODY'S CLOTHES.** miso-137 §4: on RT
2025, 70 % of the gap books to 88 hours at the $200 cut. An arm that manufactures
a handful of extra spike hours moves the annual mean while leaving the body
untouched — and C3a would improve for a C3c reason. **Counter-measurement,
pre-committed:** decompose any C3a movement into (i) the summer h12–17 body
window and (ii) actual-side >$200 hours, **on both RT and DA bases, never
blended** (miso-133 ONE-BASIS bar). **An arm whose C3a gain is >50 % from tail
hours is reported as a C3c-channel effect, not a body-compression fix.**

**TRAP 3 — REPORTING h12–17 ALONE.** The defect is a *reversal*; half of it is
the over-priced summer night. **h00–05 is reported beside h12–17 in every table,
always.** An arm that fixes the afternoon by making the night worse has not
addressed the object.

**TRAP 4 — CONVENTION SHOPPING.** §3's decision rule is fixed on basis
consistency before any solve. **No convention may be selected, re-selected or
"corrected" after seeing a price outcome.** If the adopted convention performs
badly, that is the result.

---

## §7 Pre-committed verdict branches

| branch | condition | consequence |
|---|---|---|
| **REFUSED-AT-G0** | §3 returns (C) | anchoring finding reported; **no solve**, no arm, no merchant cell verdict; the committed CHP cell untouched |
| **REFUSED-AT-G1** | every candidate class UNSTABLE or unidentifiable without a fitted value | open root-cause issue (rule 20); **no solve** |
| **LICENSED** | an admissible convention **and** ≥1 class with a stable MISO-own slope | build the arm; **zero-delta control first**, then the arm; both registered (rule 15) |
| **NOT ASSERTED** | the gates' verdicts flip across the pre-registered robustness sets | reported as unstable; nothing armed |

A verdict is **REFUTED** only against the gate that fired, and is stated at that
gate's scope — never generalised to "ambient derates don't work in MISO."

---

## §8 KILLS — pre-registered, from the charter plus this session's additions

Fired by the **arm** relative to the same-HEAD zero-delta control:

* **C1 16/16 held** (the 16 scored 2023+2024 class-year records; 2025 is SKIPPED
  on this bench). Baselines this session: CC_REGULAR 137.526/145.314,
  CT_PEAKER 14.497/19.062, ST_GAS 13.005/13.294, CC_CHP 21.21/21.233,
  ST_CHP 2.238/2.658 TWh (2023/2024).
* **COAL_BIT no-overshoot** — model must not cross above actual
  (2023 52.066 vs 57.069; 2024 49.851 vs 53.332).
* **C3b duration/shape held** (NRMSE 0.075 / 0.111 / 0.191, gate ≤ 0.20 — 2025
  has only 0.009 of slack; a 2025 C3b breach is a KILL).
* **C8 forced-share held** — every class stays PASS. Watch ST_GAS specifically:
  it already runs 0.319 / 0.331 / 0.451 and is a material class.
* **C6 governance PASS** and **C2 / C4 held**.
* **LOYO within 2023–2025** — leave-one-year-out before any promotion.

**Not kills, registered so they cannot be smuggled in as one:**

* **The arm is NOT scored on whether it closes C3a.** Rule 1 `[R-STRUCT]`: a
  structurally-correct mechanism stays in even if the residual worsens, and a
  worse C3a is not grounds to revert.
* **A C7 regression is NOT grounds to revert** (owner directive + the miso-132b
  precedent; C7 is not a scored criterion at HEAD in any case).

---

## §9 Rule duties and scope limits

* **Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only. MISO holds no marker (§0).
* **Rule 15 `[R-DASHBOARD]`** — every LP solved this session is registered in
  this session. If the stop rule fires and no LP is solved, there is no run to
  register (the miso-131…138 precedent).
* **Rule 28(b) `[R-MECH-MATRIX]`** — `temp_dependent_derate` MISO is currently
  `K` for the **cogen scope**. A scope change needs its own evidence and its own
  cell citation; whatever this session adjudicates is stamped in this session,
  refusals included, with a §5.4 queue stamp.
* **Rule 19 `[R-ONE-MECH]`** — no new mechanism is added. Before arming, the
  existing treatments of the same phenomenon are enumerated
  (`SUMMER_CLASS_DERATE`, `gt_ambient_derate`, `cc_nameplate_summer_derate`,
  `coal_nameplate_summer_derate`, `COAL_SUMMER_MAX_CF`) and reconciled, never
  stacked.
* **Rules 13 / 21 / 24** — no measured *outcome* is fed back; nothing is sized to
  any residual; no off-registry channel is created. The arm reaches the solver
  only through `ScenarioConfig` fields present in `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — no other ISO's cell, keeper, parameter or
  identification is touched, and no non-MISO slope is armed for MISO.
* **Rule 12/16** — if solved: arms sequential, one invocation each, `--years 2023
  2024 2025` together.

**DO-NOT-REDO acknowledged (rule 28(a)).** This session does not re-test the
{capacity, seasonal derate, min-load fraction} class bridge (REFUTED on ground
truth, miso-138); does not quote the `cc_block` CT count agreement as class
recovery; does not use miso-138's by-predicted-class secondary-feature contrasts
(circular); does not re-split the MISO gap at a price threshold; does not use the
"88 spike hours" arithmetic as a premise; proposes no LEVEL adder or multiplier;
and does not re-open `gas_offer_margin_zonal_anchor` (I), the seam
price/ceiling/floor classes (SPENT), the fitted trough adder (REFUSED), trough
marginal-unit pricing (SPENT), the CC committed band, the coal deep-discount
premise, CEMS/dispatch bridging, SOM PDFs as a unit-hour corpus, FERC EQR, or
Michigan PSCR (SPENT).

**Method bars carried (miso-129→138):** a signature is not a cause · a
plant-grain signature is not a class-grain defect · a missing rule is not
automatically binding, measure the slack · ONE basis, check basis crossings ·
BINDING IS NOT LICENSING · grain is a property of the publication's purpose · an
absence claim is a measurement, not a premise · a threshold is a hypothesis, not
a definition · **measure an identification's ceiling where the answer is known**.

---

**Artifacts this PREREG commits to producing:** a probe under
`scripts/probes/_miso139_*.py`, a machine record under
`results/calibration/_miso139_*.json`, and a `FINDING-miso139-*.md` reporting the
gates against the branches in §7 — whichever branch fires.
