# PREREG — miso-152: the base-band inversion (charter B), and the tranche FILL-ORDER question it opens

**Session** miso-152 · **ISO** MISO · **Keeper** `2026-08-09-miso-148-basis-aware`
(`miso148_basis_B`) · **Date** 2026-08-11 · **Charter** (B), the base-band
inversion named but not opened by miso-151 §8 · **Phase 0 only** — no LP solve
of the real system, no registered run anticipated.

Pushed **before any adjudicating statistic**. Everything below §1 was derived
from source, `run_config.json` and the committed bundle *inventory* only.

---

## 1. Pre-PREREG state of knowledge (source + config reads, NOT measurements)

These are config/source facts, established before this PREREG and disclosed so
the priors below can be read against what was already known:

1. **MISO's registered CC bands are non-monotone in output position.** The
   keeper's own resolved `scenario_config.offer_curve_by_group`:

   | class | committed | econ_low | econ_high | peak |
   |---|---|---|---|---|
   | CC_REGULAR | 1.005 | **0.95** | 1.08 | 2.25 |
   | CC_INTERMEDIATE | 1.005 | **0.95** | 1.08 | 2.25 |
   | CT_PEAKER | 1.025 | **1.00** | **1.00** | 4.00 |

   `econ_low < committed` in all three; for CT_PEAKER `committed` is above
   **both** econ bands. Every other MISO class is flat or monotone.
2. **It is deliberate, and documented as a fix rather than a defect.**
   `backcast_config.py` §_MISO_OFFER_CURVE grounds it in the measured CAMPD
   part-load shape ("a CC's part-load $/MWh is ~30–40 % above its full-load
   SRMC, so the committed tranche must price ABOVE the full-load body"), and
   the header comment records the *previous* state (committed 0.92 < econ_low
   0.95) as "the inverse of the real part-load curve — an unphysical,
   artificially-cheap min-load block".
3. **The LP has no same-plant fill-order constraint.**
   `model/lp/bounds.py::build_variable_bounds` sets `col_lower = min_gen` (else
   `pmin`) and `col_upper = pmax × availability` per column; tranches are
   independent columns. The only tranche coupling in the codebase
   (`commitment.py` ~1486–1553) is an ON/OFF availability coupling in the
   *decommit* path, not a fill-order constraint.
4. **MISO floors coal, ST_GAS and CT — but nothing floors the CC committed
   tranche.** Armed: `coal_mustrun_per_plant`, `coal_mustrun_online_pmin`,
   `st_gas_mustrun_per_plant`, `ct_mustrun_floor_frac=1.0`. Not armed: every
   commitment bridge (`caiso_ra_mustoffer`, `ercot_gas_commitment_bridge`,
   `nyiso_gas_commitment_bridge`, `ercot_gas_bridge_online_hours`).
5. `gas_offer_net_revenue_margin` **is armed** (anchor 3.0492 $/MMBtu), so the
   effective mc is `phys × HR_base × fuel(t) + markup_hr × anchor`, **not** the
   registered multiplier × fuel. Any ordering arithmetic must go through
   `offer_curves.apply_gas_offer_margin`, never the raw multipliers (trap T-3).

**The question this opens.** Physics fills a thermal plant in OUTPUT-POSITION
order (min-load block first — a unit cannot produce its incremental band
without being at min load). The LP fills in COST order. Where the two orders
disagree — exactly the three classes in (1) — the model produces a plant's
incremental band while its min-load block sits idle. Whether that is material,
and which way it moves price, is what this session measures.

---

## 2. Gating — fixed here, with reasons

| id | question | gated? | reason |
|---|---|---|---|
| **G-1** | Does any same-plant fill-order constraint exist in the LP? | **GATED** | binary, source-decidable; the whole object is void if one exists |
| **G-2** | Which MISO classes are non-monotone in *effective mc* (through the real offer path, at the keeper's delivered gas)? | **GATED** | §1(1) is a multiplier read; the mc-level statement is the load-bearing one |
| **G-3** | On a minimal LP built from production types: does the solve dispatch `econ` while `committed` < its own cap? | **GATED** | the mechanism's existence proof |
| **G-4** | Magnitude on the real MISO fleet: what share of CC energy is exposed to out-of-order fill? | **GATED** | materiality |
| **G-5** | Which way does repairing it move the clearing price? | **GATED, two-sided** | the rule-14 "right sign" claim in the charter must be *earned*, not assumed |
| D-1 | Do other ISOs carry the same non-monotonicity? | **DESCRIPTIVE** | rule 25 — no cross-ISO verdict is taken here, cell stays this ISO's |

---

## 3. Two-sided numeric priors

**P-1 (G-4, magnitude).** Share of the keeper's CC (`CC_REGULAR` +
`CC_INTERMEDIATE`) annual energy in plant-hours where the plant is partly
loaded, so out-of-order fill is possible: **25 %**, band **[5 %, 60 %]**,
P = 0.7. Below 5 % the object is real but immaterial and this lane closes it as
a documented infidelity; above 60 % it is the dominant shape of MISO's CC
dispatch.

**P-2 (G-5, sign and size).** Effect on the modelled mean LMP of enforcing
fill order (min-load block pinned whenever the plant produces), estimated
analytically on the reconstructed stack: **+$0.60/MWh**, band
**[−$0.50, +$2.50]**, P = 0.6. **The band deliberately spans zero.** The
mechanism has two opposing limbs and this session does not know which
dominates: pinning the *expensive* min-load block raises the cost of producing
at all (price **up**), but it also converts flexible MW into must-take MW that
is then supplied regardless of price (price **down**). miso-151 predicted a
sign in writing and was wrong; this PREREG declines to.

**P-3 (G-2).** Number of MISO classes non-monotone in effective mc at the
keeper's own 2025 delivered gas: **3**, band **[2, 5]**, P = 0.75.

---

## 4. Pre-committed branches

* **B-1 VOID** — G-1 finds a fill-order constraint. The object does not exist;
  session reports the constraint and closes.
* **B-2 IMMATERIAL** — G-1/G-2/G-3 confirm the mechanism but G-4 lands
  **< 5 %**. Recorded as a documented structural infidelity with a measured
  materiality bound; **no lever proposed**, matrix cell annotated, lane closes.
* **B-3 MATERIAL, SIGN UP** — G-4 ≥ 5 % and G-5 positive. A rule-14 repair with
  the right sign: the FINDING names the repair, its DOF ledger and its kill
  gates, and puts it to the owner as a lever. **No solve this session** (Phase 0
  charter).
* **B-4 MATERIAL, SIGN DOWN** — G-4 ≥ 5 % and G-5 negative. Reported at full
  magnitude **and still named as a repair candidate**: rule 1 `[R-STRUCT]` makes
  a structurally-correct mechanism a keeper candidate even when it moves the
  residual the wrong way, and the owner's standing guidance covers exactly this
  case. The lane must not quietly drop it because the sign disappointed.
* **B-5 INDETERMINATE** — the T-6 counter-measurement fails, i.e. the merit
  reconstruction does not reproduce the committed class dispatch within
  tolerance. G-4/G-5 are then reported as **DESCRIPTIVE ONLY**, no verdict is
  taken from them, and the FINDING says so in its headline.

Any outcome in none of these is recorded as an **unanticipated branch**, named
as such, and never retrofitted into one (the miso-151 precedent).

---

## 5. Traps, each with its counter-measurement

* **T-1 fixtures must be built from the PRODUCTION type.** miso-151 lost an arm
  to `SimpleNamespace(pmax=…)` when the field is `pmax_mw`. *Counter-measurement:*
  G-3's fixture constructs real `Generator` rows through the real assembly path;
  the test asserts the tranche capacities it reads back are non-zero and
  distinct.
* **T-2 never `getattr(obj, field, default)` on the offer path.** A silent
  default IS the bug. *Counter-measurement:* probe reads required fields
  directly and raises on absence.
* **T-3 effective mc must go through the real offer path.** With
  `gas_offer_net_revenue_margin` armed, ordering computed from registered
  multipliers is wrong. *Counter-measurement:* assert that at `fuel == anchor`
  the margin-form mc equals the multiplier-form mc to 1e-9, then report ordering
  at the keeper's own delivered gas.
* **T-4 do not destroy committed artifacts.** The `_miso150_universe.py
  --footing` precedent. *Counter-measurement:* the probe writes only to its own
  `_miso152_fillorder.json`; a `git diff --stat` over `results/calibration/` is
  checked before commit.
* **T-5 no bit-identity bars on floating-point data.** *Counter-measurement:*
  every comparison carries an explicit tolerance and reports its magnitude in
  **both** branches, pass or fail.
* **T-6 the merit reconstruction is an approximation.** It ignores
  transmission, reserves and floors. *Counter-measurement:* reconstructed class
  dispatch is compared against the committed `class_hourly_2025.parquet`;
  divergence beyond **±10 % of class annual energy** sends the session to
  branch **B-5** and G-4/G-5 become descriptive.

---

## 6. What this session will NOT do

* No LP solve of the real MISO system, no registered run, no keeper change
  (Phase 0 charter). Any lever is *proposed*, not tested.
* No re-opening of the within-unit offer-shape family (miso-151 cell `R`).
* No cross-ISO verdict (rule 25); D-1 is descriptive.
* No holdout spend: 2023–2025 artifacts only, MISO holds no marker (rule 22).

---

## 7. Disclosure (§10)

* The three facts in §1(1)–(5) were read **before** this PREREG was written and
  are disclosed above rather than presented as findings.
* This session's author formed a **prior expectation that the sign is UP**
  while reading §1, and has deliberately pre-registered P-2 with a band
  spanning zero rather than encoding that expectation. The expectation is
  recorded here so that a positive result cannot later be presented as
  unbiased confirmation.
* miso-151's §6 observation ("the model's rising offer curve dips below its
  committed block") is the origin of this object and is credited as such; this
  session re-derives it through the real offer path rather than inheriting it.
