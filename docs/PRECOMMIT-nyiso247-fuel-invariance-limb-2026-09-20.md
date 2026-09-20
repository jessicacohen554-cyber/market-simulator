# PRECOMMIT nyiso-247 — the FUEL-INVARIANCE LIMB of `gas_offer_net_revenue_margin`: the form, every bar and every kill fixed EX ANTE

**Session nyiso-247 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); ZERO LP in this container).**
**Date** 2026-09-20. **Base** `origin/main` at `f5b2356a` (the handoff names `d4cc9724`; it is an
ancestor — `caiso-291` and `soco-56` merged since, and neither is a NYISO path: see §5).
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle
`results/calibration/nyiso241_ctcommitted_span`, `git_sha` `5356fb71`, years {2022, 2023, 2024,
2025}. **ISO tier (2023–2025, rule 30 `[R-TOUCHPOINT-FOLD]` (c)) = CALIBRATED**, C3c the lone
ledgered caveat. **Registered full span (2022–2025) = NOT-YET, on 2022's C3a + C3b alone.**
**Predecessor** `docs/RESULT-nyiso246-the-deficit-is-not-a-tail-2026-09-20.md` §5–§6.

**THIS DOCUMENT IS COMMITTED AND PUSHED BEFORE ANY GATED NUMBER IS COMPUTED.** Everything cited
below is either (i) a committed prior artifact, (ii) a property of the keeper's own recorded
`run_config.json` / registered offer curve that selects no hour set and decides no gate, or (iii) a
rule fixed here. **No statistic computed under the arm exists at this commit, and no candidate form
was evaluated numerically before choosing the one in §2.**

---

## 0. THE OBJECT — ONE SENTENCE, AND IT IS A SIGN ERROR

`gas_offer_net_revenue_margin` (`data/offer_curves.py::apply_gas_offer_margin`, offer_curves.py:783)
adds `offer_markup_hr[g] × (anchor_z − fuel[g,t])`. nyiso-246 measured, at zero LP:

* it reaches **88.9 %** of the affected gas econ/peak stack (327 of 369 tranches, 14,923.6 of
  16,797.3 MW);
* the per-zone anchor **is that year's own mean delivered gas**, so the term is **antisymmetric
  about the annual mean by construction** — it adds below the mean and subtracts above it;
* in the TIGHT window it is negative in **100.0 %** of row-hours in every year, capacity-weighted
  mean **−$27.07/MWh (2022)** / **−$12.55 (2023)**;
* and the measured book does the OPPOSITE. NYISO MIS P-27 DAM 2022–2025, within-unit,
  capacity-weighted implied offer heat rate at the curve bottom, TIGHT − ORDINARY:

| | p50 | p75 | p90 | p95 | p99 |
|---|---:|---:|---:|---:|---:|
| **book** `Q_book` | **+2.035** | **+11.928** | **+27.880** | **+39.714** | **+96.710** |
| **model** `Q_mod` | −0.849 | +0.553 | +2.807 | +4.243 | +11.839 |

MMBtu/MWh. Artifact `data/raw/_validation-source/nyiso_offer_level_dispersion.json`, sha256
`1ad26b2f21e3654c5cb1f25f66c0715ebeff601299624b4dd85de05d95e2f1db`.

> **THE MARKET PRICES SCARCITY INTO ITS IMPLIED OFFER HEAT RATE; THE MODEL PRICES IT OUT.**

**WHERE THE DAMAGE SITS, from the keeper's own registered `offer_curve_by_group` and nothing else.**
`offer_markup_hr = base_HR × max(0, mult − phys)`:

| class · band | `mult` | `phys` | markup mult |
|---|---:|---:|---:|
| CT_PEAKER · **peak** | 4.000 | 1.000 | **3.000** |
| ST_GAS · **peak** | 4.200 | 1.000 | **3.200** |
| CT_PEAKER · econ_low / econ_high | 1.000 / 1.000 | 0.661 / 0.658 | 0.339 / 0.342 |
| ST_GAS · econ_low / econ_high | 1.000 / 1.000 | 0.830 / 0.828 | 0.170 / 0.172 |
| CC_REGULAR · econ_low / econ_high | 0.950 / 1.000 | 0.784 / 0.925 | 0.166 / 0.075 |
| CC_CHP · econ_high | 1.240 | 1.103 | 0.137 |
| every `committed` band, CC_REGULAR/CC_CHP `peak` | — | — | **0 (clipped)** |

**The two PEAK bands carry a markup an order of magnitude larger than every econ band** — and the
peak band is the rung that sets the price in a scarcity hour. nyiso-182 measured the consequence
independently: *"in the 2025 top decile (gas ≈ $11.76/MMBtu) it LOWERS the peak band's mean offer by
$188/MWh and econ\* by $5/MWh."* That is the C3a/C3b defect mechanism, named and signed.

---

## 1. THE ALGEBRA, WRITTEN OUT, BECAUSE THE FORM FOLLOWS FROM IT

Per tranche, with `G(t)` the zone's delivered gas and `a` its anchor:

```
ARMED (the keeper) :  mc = base_HR × [ phys × G(t) + (mult − phys) × a ]  + vom + co2
DISARMED           :  mc = base_HR × [ mult × G(t)                     ]  + vom + co2
```

Divide by `G(t)` — the implied offer heat rate the book is measured in:

```
ARMED    :  mc/G = base_HR × phys + base_HR × (mult − phys) × a / G(t)     →  FALLS as G rises
DISARMED :  mc/G = base_HR × mult                                          →  FLAT in G
BOOK     :                                                                     RISES in G
```

**The registered family has exactly two members. The armed one is the only member whose conditional
implied-heat-rate response is strictly NEGATIVE; the disarmed one is the unique member whose
response is exactly ZERO. The measured response is POSITIVE.** So the disarmed member is the
family's closest admissible point to the measured conduct, and the armed member is its farthest.

**The markup SURVIVES AT FULL STRENGTH under the disarm** — `mult` is untouched. Only the markup's
FUEL BASIS moves, from the frozen anchor to the hour's own delivered gas. **This is NOT the change
nyiso-195 killed**, which set `econ_low/econ_high := phys_econ_low/high` and *deleted* the markup.
The margin FORM stays; the fuel-invariance LIMB is what moves, exactly as the handoff scopes it.

---

## 2. THE FORM — CHOSEN ON STRUCTURE, EX ANTE, WITH THE REJECTED ALTERNATIVES NAMED

> **`nyiso247_fuelinv` = the keeper's frozen recipe with `gas_offer_net_revenue_margin` DISARMED
> for NYISO, and NOTHING ELSE.**

Mechanically, a `replay_keeper.py` single-delta A/B off the committed keeper bundle:

```
--set gas_offer_margin=false
--set gas_offer_margin_zonal_anchor=false
--set gas_offer_margin_zonal_anchor_vintage=false
```

The second and third are **mechanically required, not a second mechanism**:
`data/fleet/assembly.py:210` hard-errors on a zonal anchor without its parent, with the reason this
PRECOMMIT relies on — *"the zonal anchor resolves the SAME mechanism's identification point, it is
not a mechanism of its own (rule 19 `[R-ONE-MECH]`)."*

**Routing verified at HEAD, before the solve** (this is the trap that would silently make the arm
identical to the keeper): `gas_offer_margin` is a `solve_and_persist` kwarg and is **NOT** a
`ScenarioConfig` field, so `--set` routes it through the kwarg channel alone; `run_calibration.py`
arms the gate only inside `if gas_offer_margin:` (line ~1264). With the kwarg False the gate is
never armed and `apply_gas_offer_margin` returns at its first line.

**ZERO NEW CODE. ZERO NEW `ScenarioConfig` FIELD. ZERO NEW FREE PARAMETER.** Rule 26 `[R-DELETE]`
has nothing to revert on a refusal; rule 28 `[R-MECH-MATRIX]` (c) is not engaged (no new field), and
duty (b) is owed and will be discharged either way.

### 2.1 THE THREE ALTERNATIVES CONSIDERED AND REJECTED — on structure, before any number

**(i) PARTIAL ANCHORING.** `markup = mk × (a + θ(G(t) − a))`, `θ ∈ [0,1]`, `θ=0` armed, `θ=1`
disarmed. **REJECTED:** `θ` is a NEW free parameter with no identification inside the family, and
the family **saturates at `θ=1`** — the measured response is above the *whole* family, so `θ` would
be pinned at its boundary. A boundary-pinned DOF buys nothing and is sweepable, which is exactly
what rule 1 `[R-STRUCT]`'s anti-sweep clause forbids.

**(ii) ONE-SIDED FLOOR.** `mc += mk × max(0, a − G(t))`, i.e. `markup = mk × max(a, G(t))` — keep the
anchored form below the anchor, the multiplier form above it. **REJECTED ON TWO INDEPENDENT
GROUNDS**, the second decisive: (a) the kink at the anchor is a functional form the book does not
support — the measured response is monotone in tightness, not kinked at the training mean; and
(b) it removes only the NEGATIVE half of a term whose annual mean is ≈ 0 by construction, so it is a
**LEVEL INCREASE with no measured level behind it** — the fitted adder rule 1 forbids, wearing a
sign-repair costume. *(This is the one alternative that is strictly more conservative on §3's
overshoot leg, and it is refused anyway. Stated here so the reader can see the easier arm was
available and declined.)*

**(iii) SIGN FLIP.** `mc += mk × (G(t) − a)`. **The only candidate that reaches the book's POSITIVE
sign — and REJECTED.** It uses `offer_markup_hr`, a parameter identified as a *heat-rate markup*, as
the coefficient of a *fuel-excess sensitivity*: precisely the **"derivation-vs-dispatch basis
mismatch"** nyiso-167 refused. Nothing measures that coefficient, and it would double the
intervention on the two peak bands (a further +$130–230/MWh in 2022 TIGHT hours) on an unidentified
number.

### 2.2 WHAT THIS FORM DOES NOT CLAIM — stated at the gate, never absorbed later

**It moves the model's conditional implied-heat-rate response from NEGATIVE to ZERO. The book's is
POSITIVE.** It therefore closes the **SIGN** error and leaves the remaining positive response to the
two objects nyiso-246 named and refused-or-deferred: the conditional level-dispersion object
(refused **on form**, `r_anchor = 0.145` against a 0.50 floor — the object itself measures
**25.845** MMBtu/MWh and clears 4 of 4 years) and the daily-citygate successor. **An arm landing
`Q_mod ≈ 0` has captured exactly the object this PRECOMMIT names and no more.** Pre-registered here
so a partial close cannot later be read as a full one.

**It is also not a claim that the level is right.** nyiso-246 §5.1 and the nyiso-246 PRECOMMIT §4(c)
both record that the armed term depresses the level in the failing hours; removing it is
level-neutral **in annual mean by construction** (§3, G-E) and redistributes across hours. Any
residual level defect stays with `nyiso_st_gas_econ_bands_deleaked`'s OPEN ROOT CAUSE issue #1344,
which this form does not touch and does not stack beside.

---

## 3. THE GATES — every bar fixed HERE, in this order. G-A/G-B/G-E/G-F at ZERO LP, before any shard

A **FAIL** on a zero-LP gate refuses the arm **before a shard is launched**.

### G-A — THE IDENTITY. *(zero LP, hard)*
On the rebuilt fleet arrays at HEAD, the arm's `mc` differs from the keeper's by **exactly**
`− offer_markup_hr[g] × (anchor_z(g) − fuel[g,t])` and by nothing else: max |err| ≤ **1e-4 $/MWh**
over every row and hour, and **zero** rows move where `offer_markup_hr == 0`. *(nyiso-195's own E-2
verification protocol, adopted unchanged; its measured tolerance there was 2e-5 on float32.)*
A FAIL means the disarm is not the single delta claimed → **STOP, no shard.**

### G-B — THE SIGN GUARD. *(zero LP, hard — the handoff's duty (e))*
`Q_mod` built by `scripts/probes/nyiso246_dispersion_phase0.py`'s **own** construction, pooled
2022–2025, on the family's frozen 199-point grid, against the committed `Q_book`. Three legs, all
binding:

* **S1 — DIRECTION.** `Q_mod^arm(p) > Q_mod^keeper(p)` at `p ∈ {0.50, 0.75, 0.90}`, **strictly, all
  three.** A flat `Q_mod` is a **KILL**, verbatim per the handoff: *"An arm that fixes the level
  while leaving Q_mod flat has NOT captured the object."*
* **S2 — NO OVERSHOOT.** `Q_mod^arm(p) ≤ Q_book(p)` at **every** grid rank `p ≥ 0.50`.
  **Why `p ≥ 0.50`, fixed here and on a committed measurement rather than chosen for convenience:**
  nyiso-246 §3 measured `r_anchor = 0.145` — the model **already** sits above the book at the bottom
  **29 of 199** ranks — so "no overshoot at any rank" is **unsatisfiable at the keeper itself** and
  cannot be the bar. p50 is the **object's own measured boundary**: 92.1 % of the (book − model) gap
  sits above it. Below p50 the comparison is **REPORTED at full magnitude and gates nothing**; S3 is
  what stops a repair that pays for the top by wrecking the bottom.
* **S3 — NET CLOSURE.** The **rank-mean `|Q_mod − Q_book|` over the FULL 199-point grid** must
  strictly **DECREASE**, arm vs keeper. This is the leg that catches "fixed above p50, broke below
  it", and it is evaluated on the whole distribution so the S2 restriction cannot hide anything.

### G-E — LEVEL NEUTRALITY. *(zero LP, REPORTED at full magnitude, gates nothing)*
Per zone per year, the capacity-weighted mean over all 8760 hours of the removed term
`offer_markup_hr × (anchor_z − G_z(t))`, in $/MWh. **The claim under test is ≈ 0** (the anchor is the
zone's own year mean). If it is materially non-zero the disarm is a **LEVEL** intervention and this
session says so **before** the solve, at full magnitude, and carries it into the C3a reading.
It gates nothing because a structurally-correct repair is never judged by the residual (rule 1) —
it exists so the size of the intervention is written down before any result is seen.

### G-F — RULE 19 `[R-ONE-MECH]`: REPLACE, NEVER STACK. *(zero LP, hard)*
The five armed non-base generator-row writers, enumerated from the keeper's **own**
`run_config.json` and not from memory: `gas_offer_net_revenue_margin`,
`gas_offer_margin_zonal_anchor`, `gas_offer_margin_zonal_anchor_vintage`,
`nyiso_st_gas_econ_bands_deleaked`, `nyiso_ct_peaker_committed_measured`.
(`nyiso_zonal_loss_surface` name-matches and writes no generator row — it splits internal
transmission chain links.) The duty is discharged **by construction**: this arm **REMOVES** one of
the five and adds nothing, which is the strongest possible form of replace-never-stack. Two
reconciliations, both required to hold and both checked:
1. **`nyiso_st_gas_econ_bands_deleaked` (#1344).** Under the disarm the ST_GAS econ markup
   (0.170 / 0.172 above `phys`) **reverts to the multiplier form; it is not removed.** The
   un-identified markup that routes to #1344 is therefore untouched and un-stacked-upon — this arm
   neither closes that issue nor adds a second mechanism beside it.
2. **`nyiso_ct_peaker_committed_measured`** writes the CT_PEAKER `committed` band, whose markup
   clips to 0 (`mult = phys = 0.843`). It is provably untouched; **G-A's "zero rows move where
   `offer_markup_hr == 0`" is the test.**

### G-C — THE LOADING-SHAPE GUARD. *(POST-SOLVE, hard — the handoff's duty (c); the exact prior that killed nyiso-195)*
**CC_REGULAR class MW-weighted 80–90 % loading share, reported for EVERY scored year against CAMPD
16.5**, computed by the identical construction on both legs from each run's own committed per-plant
hourly loading series (`render_calibration_html._b64(100 × mw / cap)`, the payload's `plants[*].m`).

> **BAR: the arm's share must not RISE by more than +0.5 pp above the keeper's own value in any
> scored year.**

**Why +0.5 pp, and why it is not a number invented to be passed:** it is **nyiso-195's own measured
killing margin** — that arm moved 33.0 → 33.5 against CAMPD 16.5 and was killed on it — adopted
unchanged. The bar is stated **relative to the keeper**, so it is fixed here without knowing either
value. A DECREASE (toward 16.5) is an improvement and is reported, never a criterion in the other
direction (rule 1).

### G-D — C1 / C2 EXPOSURE. *(POST-SOLVE, hard — the handoff's duty (d))*
**C1 and C2 are reported at full magnitude beside C3a / C3b / C3c for EVERY scored year.**
The PASS→FAIL band is the scorer's own and is pre-stated here so it cannot be re-read after the
fact: the **C1/C2 volume band is `min(max(2 % of load, 3 % of actual generation), 8 TWh)`**
(`calibration_verdict.py:1632`), with C1's per-class share leg at ±`FUELMIX_SHARE_PP`.
**A C1/C2 degradation is REPORTED, never traded for price** (promotion criterion P3).

---

## 4. THE ANTI-SWEEP CLAUSE, BINDING

**There is nothing to sweep, and that is the point of choosing this form.** The arm has **no
parameter**: it is the removal of one term. No anchor is re-identified (nyiso-167's refused
per-year re-anchor is **not** proposed and is not touched), no multiplier moves, no band edge moves,
no threshold is introduced. **Every bar in §3 is fixed in this document and none is evaluated at a
second value.** A bar relaxed, a leg dropped, or a form substituted after seeing a gate is a
**KILL**, not an option — and since the only remaining degree of freedom is *whether to promote*,
that decision is the owner's (§7, P5).

---

## 5. THE CONTROL — form 4, and the G-DRIFT audit that validates it (rule 29 `[R-SCREEN]` (b))

**NO CONTROL SOLVE IS SPENT. The committed keeper bundle is the control.** Three things establish
it, and the third is recorded here before the arm is solved so it cannot be written to fit a result:

1. **Rule 36 `[R-YEAR-ISOLATION]` (f) is measured CLOSED for NYISO** (nyiso-245 §6): all four years
   replayed at HEAD, year-isolated, both knobs OFF — **max |Δ class TWh| = 0.0000 and 0 of 43,800
   zonal price cells moved, every year.** `replay_keeper.py` additionally pins
   `MARKET_SIM_WARMSTART_XYEAR=0` itself.
2. **The arm IS a replay of the keeper's own bundle**, so every non-delta kwarg is the keeper's by
   construction rather than by reconstruction.
3. **G-DRIFT over `83543f3c → f5b2356a`** — the window this session owes (nyiso-245 audited
   `5356fb71 → 4a01ae60`; nyiso-246 audited `4a01ae60 → 83543f3c`, 5 files, all INERT). Over rule
   29 (b)'s paths, **6 files changed, every hunk INERT for a NYISO backcast**:

| path | classification | reason |
|---|---|---|
| `data/raw/_validation-source/nyiso_offer_level_dispersion.json` | INERT | nyiso-246's measured artifact; its mechanism was refused and **no `ScenarioConfig` field was ever written**, so nothing in the solve path opens it |
| `config/scenarios.py` (+37) | INERT | exactly one new field, `gas_basis_differential_measured_by_year: bool = False` — default off, **absent from the keeper's recipe**, plus its two registry lines |
| `config/fuel_trajectories.py` (+62) | INERT | the new `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR` table — **`{"SOCO": {...}}` only**; NYISO has no row, so the lookup misses even if armed |
| `config/constants.py` (+1) | INERT | one re-export import line; **no value changed** |
| `config/solve_surface_declared.py` (+1) | INERT | one declared drop key for that table, scoped `{"SOCO": ...}`; a cache-key object, not a solve object — and every shard solves into a **fresh `--out-dir`** with no cache to hit |
| `data/fuel/trajectories.py` (+17) | INERT | the consuming branch is gated on `config.gas_basis_differential_measured_by_year` (default off, absent from the recipe) **and** on an ISO row NYISO does not have — inert twice over |

**All hunks INERT ⇒ form 4 is valid and the committed keeper is the control.** A corroborating
zero-LP observation, reported rather than relied on: nyiso-246 rebuilt this keeper's fleet at HEAD
through `_nyiso245_fleet_cache.py` and recovered the keeper's recorded per-zone anchors and markup
footprint exactly, so the offer path at HEAD reproduces the keeper's offer surface.

---

## 6. THE SOLVE, IF AND ONLY IF EVERY ZERO-LP GATE CLEARS

**Rule 36 `[R-YEAR-ISOLATION]` (a): ONE YEAR, ONE SHARD, ONE CONTAINER, its own `--out-dir`** —
2022, 2023, 2024, 2025, four shards, each pinned to **this document's commit SHA**. Rule 32
`[R-SHARD]` (b)'s fan-out ban does not apply to a backcast; rule 36 (a) says so in terms, and the
parent composes at zero LP. `MARKET_SIM_WARMSTART_XYEAR` and `MARKET_SIM_P1_BASIS_SEED` are **left
at their defaults (OFF)** and are not set (rule 36 (d)).

**Rule 34 `[R-SHARD-PROMOTABLE]` (a): every shard pushes its FULL bundle including
`dispatch/<year>_P1.parquet`**, by a `.gitignore` **NEGATION** plus a **PLAIN `git add`** — never
`git add -f`. **Rule 34 (c): all four years of the keeper's union are solved**, none left out; the
union `{2022, 2023, 2024, 2025}` is enumerated from `frontend/data/backcast/registry/` **before**
anything is pruned (rule 35 `[R-PROMOTE]` (b)).

The parent composes, scores, registers (rule 15 `[R-DASHBOARD]`), updates the NYISO matrix shard
(rule 28 (b)) and puts the promotion question to the owner (rule 31 `[R-RETAIN]`).

## 7. THE PROMOTION CRITERIA — fixed here, so the residual cannot choose them

* **P1** — **every §3 gate clears** (G-A, G-B, G-F at zero LP; G-C, G-D post-solve). *Prerequisite.*
* **P2** — the **ISO tier (2023–2025)** determination does not degrade from **CALIBRATED**.
* **P3** — **C1 and C2 do not cross a PASS→FAIL boundary in ANY of the four years.** Both reported
  at full magnitude beside C3a/C3b/C3c for every scored year. **A C1/C2 degradation is REPORTED,
  never traded for price** — a price gain bought with a volume loss is refused here, in advance.
* **P4 — verbatim from the handoff.** **2022's C3a and C3b are REPORTED, and are NOT a promotion
  criterion** (rule 1 `[R-STRUCT]`). **If the structure gates clear and 2022 still fails, the
  mechanism stays promotable on structure and this session will say so.** Conversely, **2022
  improving is not by itself a reason to promote** — P1 is.
* **P5** — rule 31 `[R-RETAIN]`: **nothing is deleted**, the bundles' retrievability is stated in
  the RESULT (rule 34 (e)), and the promotion question is put to the owner **explicitly** before
  this session ends. This arm re-opens a **`K`-verdict keeper mechanism** that three prior sessions
  (nyiso-167, -182, -195) each declined to move; that decision is not a lane's to take alone.

## 8. DUTIES THIS SESSION OWES REGARDLESS OF OUTCOME

* **Rule 15 `[R-DASHBOARD]`** — an arm that solves is registered in this session, keeper or not.
* **Rule 28 `[R-MECH-MATRIX]`** (b) — the `gas_offer_net_revenue_margin` cell in
  `docs/codebase-site/data/mechanism-matrix/NYISO.js` is updated with this session's verdict and
  citation, **rejection included**. Duty (c) is not engaged: no new `ScenarioConfig` field.
* **Rule 26 `[R-DELETE]`** — nothing to revert on a refusal; no field or applier is written.
* **Rule 33 `[R-SHARD-ARCHIVE]`** — shards archived once the parent holds and has **verified** their
  bytes; a shard branch is TRANSPORT, not STORAGE, and what must survive lands on `main`.
