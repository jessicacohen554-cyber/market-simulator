# FFR-4E — the entry price signal's missing scarcity tail: what it is, what it is worth

**Session:** ffr-4e, 2026-08-04. **DIAGNOSIS lane.** Nothing was promoted, no default
was flipped, no band was widened, no parameter was tuned, **no LP was solved.** Every
number below is read off a committed artifact, computed from `src/` at head, or
measured from `data/raw/`. Chartered by the workstream manager (sitting Addendum
P.3b), not by an owner card.

**Head:** `5eac75b0` (`origin/main` merge of #3548). Branch
`claude/entry-price-scarcity-tail-j2q2fh`.

---

## 0. Headline

**The overlay's absence is a deliberate, already-adjudicated scoping choice — and
the premise it was chartered against is wrong. The missing ORDC tail is not the
largest suppressor of MISO entry. It is worth approximately nothing.**

Three measured bounds, each independently decisive:

1. **If the overlay were armed on the lookahead today it would add
   $0.0002/MWh.** The ORDC adder is a function of one quantity — reserves — and
   MISO's modelled reserve never gets near the curve. At the keeper's own
   measured floor of **≥11 GW** deliverable reserve in every event hour
   (miso-82), the adder computed by `scarcity_prices()` at MISO's effective
   parameters is **$0.00022/MWh**; at the 31.9 GW idle headroom the mechanism
   matrix records it is **exactly $0.00**. The curve needs reserves below
   ~8 GW to reach even $2.65/MWh (§3).
2. **The in-LP mechanism the overlay defers to would not help either.** Armed,
   in the backcast, MISO's reserve duals are non-zero in **0 / 6 / 2 hours** of
   8,760 (matrix `energy_reserve_coopt` note).
3. **The real market's scarcity is not where the money is.** On MISO's measured
   2024 DA hub prices, a $25.91/MWh peaker earns **$42,175/MW-yr** of energy
   margin, of which the hours above $200 — everything an ORDC tail could
   possibly represent — contribute **$1,192/MW-yr, 2.8 %**, in 6 hours. Against
   a $128,112 CONE that is **0.9 %** (§4).

**What actually suppresses the signal is the lookahead re-price itself, across
the whole distribution rather than in the tail.** For the same 2024 decision
year and the same $25.91 peaker:

| price basis | mean | max | h>$39 | h>$100 | h>$200 | peaker energy margin |
|---|---|---|---|---|---|---|
| **measured** MISO 2024 DA, 8-hub mean | $27.25 | $256.29 | 901 | 84 | 6 | **$42,175/MW-yr** |
| **the model's own LP duals** (miso-127 keeper, demand-wtd) | $29.42 | $500.00 | 351 | 44 | 6 | **$39,044/MW-yr** |
| **the entry lookahead stack signal** (FFR-3V's run) | $25.92 | **$39** | **0** | **0** | **0** | **$8,727/MW-yr** |

The model forms a price distribution that recovers **93 %** of the measured
peaker margin and matches the measured >$200 hour count exactly (6 vs 6). The
lookahead re-price then **replaces** that signal with a static merit-order stack
and hands the screens **21 %** of it. The ~$30,300/MW-yr thrown away is
**97 % sub-$200 dispersion**, not scarcity.

**Consequences for the concurrent lanes.** FFR-4B (D-12 + D-2') and FFR-4C
(D-13) operate downstream of a price signal that is impoverished — but **not in
the way the charter says, and not by an amount that makes their levers moot.**
Solar's 2024 rejection remains arithmetically unreachable at the $39 ceiling, so
that specific claim of FFR-3V §3.2 stands. But the fix is not a scarcity
mechanism, and no scarcity mechanism this repo could legitimately arm would
change a single MISO entry decision. Their levers are not operating on a
hopeless signal; they are operating on a *flattened* one.

**No new mechanism is proposed here** (charter escalation clause not triggered):
the alternative price basis is an existing registered flag,
`entry_lookahead_reprice`, whose OFF branch already routes `result.prices` to
the screens (`runner.py:2501`).

---

## 1. Limb 1 — where the flag is set, and whether the two paths agree

### 1.1 It is one flag read at two sites, with two different gate expressions

`scarcity_price_overlay` is a single `ScenarioConfig` field
(`config/scenarios.py:2257`, default `False`). It is read at exactly two places
in the solve loop:

| path | site | gate |
|---|---|---|
| **dispatch / capacity-economics** (post-solve adder onto `econ_prices`) | `runner.py:2362-2366` | `scarcity_pricing_enabled` **AND** `scarcity_price_overlay` **AND NOT** `energy_reserve_coopt` |
| **entry / lookahead** (ORDC tail inside `_lookahead_reprice_signal`) | `runner.py:531` | `scarcity_pricing_enabled` **AND** `scarcity_price_overlay` |

**The gates are not the same expression.** The dispatch site carries a
double-count guard — "when co-optimization is on the energy LMP already carries
the scarcity lift via the reserve clearing price, so the post-solve adder is
skipped" (`runner.py:2357-2359`) — and the lookahead site does not. That is one
mechanism answering to two definitions (rule 19 `[R-ONE-MECH]`).

**It is a latent defect, not a live one.** No ISO currently reaches the
divergent branch: it requires `scarcity_price_overlay=True` **and**
`energy_reserve_coopt=True` simultaneously on the entry path, and the per-ISO
map in §2 shows no ISO has both. Were MISO ever armed on both, the dispatch
prices would correctly skip the adder while the lookahead double-counted it.
Reported as a code-hygiene finding; **not** proposed for repair in this lane.

### 1.2 On MISO the two paths agree — both are off, and that is the real problem

For MISO the flag is `False` at both sites, so the paths do not disagree. What
disagrees is something larger: **the backcast lane and the forecast lane price
MISO with entirely different mechanism sets.**

Read from the two committed `run_config.json` files:

| flag | MISO backcast keeper (`miso127_onlinepmin_B`) | MISO forecast/hindcast (`results/ffr3v/miso-entry-diag`) |
|---|---|---|
| `energy_reserve_coopt` | **True** | **False** |
| `miso_measured_reserve_requirements` | **True** | **False** |
| `miso_zonal_reserves` | **True** | **False** |
| `miso_midwest_subregional_reserves` | **True** | **False** |
| `miso_reserve_pergen` | **True** | **False** |
| `miso_rpe_pricing` | **True** | **False** |
| `scarcity_pricing_enabled` | False | True |
| `scarcity_price_overlay` | **False** | **False** |

`scarcity_price_overlay=False` on the **backcast** keeper is correct and is the
adjudicated position: `docs/handoffs/miso-price-formation-design-2026-07.md`
§2b lists the post-solve overlays as "**OFF (correct)** — MISO scarcity is in-LP
only — no overlay may be added (one mechanism per phenomenon)". The mechanism
matrix records the same verdict as a hard **`G`** (governance-refused) in the
MISO column of `ordc_scarcity_overlay`, citing
`docs/multi-iso/miso-scarcity-tail-external-validation-2026-07.md` §1.

**But that refusal is a deferral to the in-LP mechanism, and on the forecast
path the in-LP mechanism is itself off.** MISO's forecast price signal therefore
carries **no scarcity mechanism of any kind** — neither the one it was
calibrated with nor the substitute it was refused. The `G` was decided in a lane
where the deferral target exists; it was inherited into a lane where it does
not. That is the honest statement of the defect, and it is a **lane-scope**
defect, not a wrong flag value.

### 1.3 A related casualty: MISO's screens also get no reserve-price signal

`runner.py:2600-2615` builds `reserve_price_signal` for the retirement/entry
screens from exactly one of two sources (rule 19): the co-opt's own
`reserve_price_by_family` — **gated `iso == "ERCOT"`** — else `overlay_adder`.
For MISO both are absent (`overlay_adder is None`), so
`reserve_price_signal = None` and the screens fall back to legacy annual AS
credits. Even when MISO's co-opt *is* armed, its per-family reserve duals are
not readable by the screens. Flagged, not pursued.

### 1.4 Provenance trap — `run_config` under-reports the resolved overlay

`ISOConfig.default_scenario_overrides` is applied inside `run_scenario_iso`
(`runner.py:585-593`), **after** the harness writes `run_config.json`/`.yaml`.
So `results/hindcast/ercot-*/run_config.yaml` reads
`scarcity_price_overlay: false` while ERCOT's effective value on that run is
`True`. **Do not build a per-ISO map from the persisted run configs** — the §2
map is computed from the code. (MISO's `False` is unaffected: MISO carries no
overrides at all.)

---

## 2. Limb 2 — the per-ISO map on the entry path

Computed by reproducing `runner.py:582-593` against the standard forecast/
hindcast footing (`run_capacity_hindcast.build_config:642` sets
`scarcity_pricing_enabled=True`; every reserve/co-opt flag stays at its
`ScenarioConfig` default):

| ISO | `scarcity_price_overlay` | source | dispatch overlay fires | **lookahead tail fires** | ORDC params (voll/mcl/σ/shift/floor) |
|---|---|---|---|---|---|
| ERCOT | **True** | `ISOConfig` | ✅ | ✅ | 5000 / 3000 / 1400 / 0.5 / True |
| CAISO | False | `ScenarioConfig` default | ❌ | ❌ | (unreached) |
| **MISO** | **False** | `ScenarioConfig` default | ❌ | ❌ | (unreached) |
| PJM | False | `ScenarioConfig` default | ❌ | ❌ | (unreached) |
| NYISO | False | `ScenarioConfig` default | ❌ | ❌ | (unreached) |
| NEISO | **True** | `ISOConfig` | ✅ | ✅ | 2000 / 1200 / 900 / 0.0 / False |

**It is not MISO-specific — it is four-of-six.** Only ERCOT and NEISO carry a
scarcity mechanism on the entry path; CAISO, MISO, PJM and NYISO carry none.
**Rule 25 `[R-ISO-SCOPE]`: this is a program-wide observation and each ISO's
remedy is its own decision.** Nothing here arms, or argues for arming, any ISO
from another ISO's evidence. Note in particular that PJM's and NYISO's cells on
this matrix row are `G` and `·` on their own grounds (the in-LP co-opt and the
RCPF family respectively own the phenomenon there), and CAISO's `K` is
forecast-lane only.

**The cross-lane pattern generalises.** ERCOT's backcast keeper also runs
`energy_reserve_coopt=True` / `scarcity_price_overlay=False`, and its forecast
path runs the reverse. So *every* ISO drops its calibrated in-LP scarcity
mechanism on the forecast path; ERCOT and NEISO have a standing substitute, the
other four do not.

**Third parameter finding (MISO-specific, rule 25).** MISO's `ISOConfig` carries
**no** `default_scenario_overrides` at all, so its ORDC parameters are the bare
`ScenarioConfig` defaults — **which are ERCOT's** ($5,000 VOLL, 3,000 MW MCL,
1,400 MW σ, 0.5σ PUCT shift, OBDRR048 floor steps). NEISO, when it opted in,
brought its own ISO-NE-grounded set. **Arming MISO's overlay today would import
ERCOT's published curve wholesale into MISO — a rule 25 violation on its face.**
MISO's own parameters are already documented and are different in every term
(`miso-scarcity-tail-external-validation` §5: $10,000 VOLL / $6,000 ORDC cap /
$600–$1,100 steps post-2025-09-30; $3,500 / $1,100–$2,100 before). Any future
charter to arm this must derive MISO's curve from MISO's primary documents
first.

---

## 3. Limb 3 — what the tail would be worth, bounded before any solve

The bound is decisive and no solve was needed.

### 3.1 The adder is a function of one quantity, and it is a cliff

`_lookahead_reprice_signal` (`runner.py:530-534`) computes
`reserves = cum_cap[-1] − net_load` — **total availability-derated fleet
capacity minus next year's net load** — and feeds it to the same
`scarcity_prices()` the dispatch overlay uses. Evaluated at MISO's effective
parameters with λ = $39 (the signal's own ceiling):

| reserves (MW) | LOLP | **adder $/MWh** |
|---|---|---|
| 3,000 | 1.000 | 4,961.00 |
| 4,000 | 4.15e-01 | 1,786.29 |
| 5,000 | 1.77e-01 | 597.24 |
| 6,000 | 5.02e-02 | 138.66 |
| 8,000 | 1.07e-03 | 2.65 |
| **11,000** | 9.23e-08 | **0.00023** |
| 14,000 | 9.39e-14 | 0.00000 |
| 31,900 | 0 | 0.00000 |

The OBDRR048 floor steps are `((6500, $20), (7000, $10))` — they need reserves
**below 7 GW** to engage at all.

### 3.2 MISO's modelled reserve is nowhere near the cliff — measured, twice

* **≥11 GW in every event hour**, against a ~4.4 GW requirement, measured on the
  keeper's own committed hourlies (`miso-scarcity-tail-external-validation` §1:
  "the LP always re-times energy to relieve any zonal shortfall for ≤$23/MWh,
  always cheaper than the $200 ORDC step, so the shortage steps never engage").
* **31.9 GW idle headroom** (mechanism matrix, `ordc_scarcity_overlay` MISO
  note, miso-82) — "scarcity is STARVED not missing".

The lookahead's reserve measure is **looser still** than either: it counts the
whole derated fleet with no reserve-eligibility screen, no deliverability
constraint and no online/offline split, so at equal net load it reports *more*
reserve than the deliverable measure does. **⇒ arming
`scarcity_price_overlay=True` on MISO's lookahead adds < $0.001/MWh in every
hour of the year. It is provably inert.**

An independent corroboration from the signal's own log line: the 2024 signal
prints `max $39`. `prices_h` is monotone in net load and `reserves` is monotone
*decreasing* in it, so a marginal unit at $39/MWh in the tightest hour means
every unit above $39 in the merit order — MISO's whole gas-CT / gas-ST / oil
tail, 41.8 GW nameplate in the 2023 fleet — sits idle as reserve in that hour.

### 3.3 The in-LP mechanism, armed, would not close it either

Arming MISO's calibrated stack on the forecast path is the other candidate
route. Measured, in the backcast where it *is* armed, MISO's reserve duals are
non-zero in **0 / 6 / 2 hours** of 8,760 for 2023/2024/2025 (matrix
`energy_reserve_coopt` note, cross-ISO dormancy paragraph). The 2024 keeper
hourly confirms it: `reserve_price` > $0 in 48 zone-hours = **6 system hours**.

### 3.4 What that does to a peaker and to solar

* **Peaker.** To close `gas_ct`'s measured $119,385/MW-yr shortfall the tail
  would have to add ~$13.6/MWh to the *annual mean* — e.g. 100 hours at
  $1,200/MWh, i.e. reserves under 3.7 GW for 100 hours, ~7 GW tighter than the
  measured floor. Unreachable by four orders of magnitude.
* **Solar.** Solar needs its capture price lifted $26.69 → $43.18/MWh, +$16.5,
  on a daytime-weighted basis. An adder that is $0.0002/MWh in the tightest hour
  of the year cannot move a capture price at all. **FFR-3V §3.2's conclusion
  that solar's 2024 rejection is arithmetically unreachable stands; its
  attribution of that ceiling to the missing overlay does not.**

---

## 4. Limb 4 — is the $39 ceiling faithful? No, and by a wide margin

Measured from `data/raw/lmp-data/MISO/miso_hub_lmp_{year}_{da,rt}.csv.gz` — the
eight named MISO trading hubs, `value == "LMP"` rows, system series = mean across
hubs (rule 14 `[R-ACCURATE]`: the measured distribution, not a modelled proxy).
2023–2025 only; no out-of-training year was read (rule 22).

| year / market | mean | p95 | p99 | max | h>$39 | h>$100 | h>$200 | h>$500 |
|---|---|---|---|---|---|---|---|---|
| 2023 DA | $29.22 | $48.04 | $64.40 | $180.41 | 1,096 | 13 | 0 | 0 |
| 2023 RT | $28.36 | $48.42 | $93.54 | $569.17 | 874 | 79 | 12 | 1 |
| **2024 DA** | **$27.25** | **$47.08** | **$97.95** | **$256.29** | **901** | **84** | **6** | **0** |
| 2024 RT | $26.87 | $52.77 | $103.44 | $694.20 | 803 | 102 | 27 | 4 |
| 2025 DA | $38.75 | $71.16 | $117.64 | $343.99 | 2,984 | 146 | 19 | 0 |
| 2025 RT | $38.13 | $72.73 | $173.14 | $1,669.52 | 2,199 | 232 | 62 | 13 |

(Single-hub maxima run higher: TEXAS.HUB $420.00 DA / $1,070.34 RT in 2024.)

**The $39 modelled annual maximum sits at roughly the 90th percentile of the
real 2024 market.** 901 of 8,784 measured DA hours — 10.3 % of the year —
exceed the model's entire annual range. **The lookahead stack is not
representing the market, and that is the finding independent of the flag.**

**But the shortfall is not a scarcity shortfall.** In 2024 the real DA market
never exceeded $256/MWh system-wide and spent 6 hours above $200, against a
$2,000/MWh MISO offer cap and a $3,500 RDC. The missing $39–$256 band is
ordinary merit-order and congestion dispersion. Decomposing a $25.91 peaker's
measured 2024 DA margin:

| block | margin | hours | share |
|---|---|---|---|
| all in-money hours | $42,175/MW-yr | 3,516 | 100 % |
| of which hours > $39 | $29,096 | 901 | 69.0 % |
| of which hours > $200 | **$1,192** | 6 | **2.8 %** |

**97.2 % of the real peaker's energy margin lives between $26 and $200/MWh.**
Even a perfectly reproduced scarcity tail is worth $1,192/MW-yr against a
$128,112 CONE — **0.9 %**. And the full measured margin, $42,175, still leaves
the peaker $85,937/MW-yr short of CONE, so gas_ct's rejection in MISO 2024 is
*faithful* on energy alone: a MISO peaker is built on capacity revenue, which
FFR-3V measured at $0 that year because MISO is long.

### 4.1 The model's own LP duals are close to faithful; the lookahead is not

From the miso-127 keeper's committed `hourly/system_<year>.parquet`,
demand-weighted across the 8 zones (backcast, P1):

| year | mean | p95 | p99 | max | h>$39 | h>$100 | h>$200 | peaker margin (vc $25.91) |
|---|---|---|---|---|---|---|---|---|
| 2023 | $32.03 | $40.50 | $45.88 | $182.91 | 632 | 3 | 0 | $55,122/MW-yr |
| **2024** | **$29.42** | $38.35 | $51.05 | **$500.00** | **351** | **44** | **6** | **$39,044/MW-yr** |
| 2025 | $38.02 | $51.00 | $72.05 | $183.16 | 2,915 | 10 | 0 | $106,061/MW-yr |

Against measured 2024 DA ($42,175/MW-yr, 901 / 84 / 6 hours): the model
under-produces the $39–$100 band (351 vs 901) but recovers **93 %** of the
peaker margin and hits the >$200 count exactly. **The model can form this
signal. The lookahead discards it** — $8,727 vs $39,044/MW-yr, and the $8,727
already includes ancillary value (`new_entry.py:879-883`), so its energy-only
content is smaller still.

**Caveat, stated plainly:** the keeper is a *backcast* with MISO's full
mechanism stack armed; the hindcast run has that stack off. The three rows are
therefore indicative of the *shape* difference, **not** a matched A/B on one
config. See §6.

---

## 5. What this means for the charter's question, and what should happen next

**Answer to limb 1's question:** the overlay's absence is a **deliberate,
adjudicated scoping choice** (matrix `G`, rule 19, MISO scarcity is in-LP), which
was then **inherited into a lane where its deferral target does not exist**. So
it is neither a simple defect nor a clean choice: the *value* is right and the
*lane scope* is wrong.

**Answer to the charter's framing:** FFR-3V §0 calls the missing tail "the
largest single suppressor of MISO entry in 2024/2025". **That is not supported.**
Measured three ways, no admissible scarcity mechanism moves any MISO entry
decision. The suppressor is the lookahead re-price's flattening of the entire
price distribution — a much larger effect that happens to include the tail.

**Two corrections to the inherited text**, for the record:

* The charter (and FFR-3V §0) says the $39 ceiling "zeroes the peaker outright:
  gas_ct variable cost $41.39 exceeds the $39 ceiling". **FFR-3V §3.2 already
  self-corrected this**: $41.39 is the *2022* decision year's cost; the 2024
  figure is **$25.91**, below the $39 ceiling, and gas_ct earns $8,727/MW-yr
  rather than zero. The uncorrected §0 sentence propagated into the charter.
  Anyone reading downstream should use §3.2's number.
* "No ORDC tail at all" is accurate as a description of the code path and
  materially irrelevant as a diagnosis.

**Reported, not implemented (charter scope).** The entry screen needs a
different price basis. The candidate basis is **already a registered flag** —
`entry_lookahead_reprice=False` routes `econ_prices` (the LP's own duals,
`runner.py:2501`) to the screens, which is the $39,044/MW-yr signal rather than
the $8,727 one. **This is not a recommendation to flip it**, for two reasons an
owner should weigh:

1. The lookahead exists for a real reason — the screen must price *next* year's
   load against *this* year's fleet, and the duals are a stale, wrong-year
   basis. FFR-3V §3.2b already flags the mirror defect ("the screen values 2021
   revenue against 2023 fuel costs"). Both bases are wrong in different
   directions.
2. Most MISO hindcast runs on disk already carry `entry_lookahead_reprice:
   false`; FFR-3V's diagnostic run is the one that carries `true`. Whether the
   forecast *default* has the same exposure is a separate question this lane did
   not establish.

The structurally faithful third option — give the lookahead the dispersion it
lacks (hourly rather than time-mean variable cost, hourly rather than mean
availability, zonal rather than one system stack) — **is a new mechanism and
therefore an owner decision**, per this lane's escalation clause. It is not
proposed here, only named.

**If a scarcity charter is opened anyway** (rule 1 `[R-STRUCT]`: a real market
behaviour stays in even when it doesn't move a residual — and MISO's ORDC *is*
real), it must (a) derive MISO's curve from MISO's primary documents, never
inherit ERCOT's defaults (§2), (b) reconcile with the standing `G` on rule 19,
and (c) be argued on fidelity alone, because §3 proves it will change no
decision.

---

## 6. What I did NOT separate

* **The keeper-vs-hindcast comparison in §4.1 is not a matched A/B.** The
  $39,044/MW-yr LP-dual figure comes from a backcast run with MISO's full
  in-LP mechanism stack armed; the $8,727 comes from a forecast run with that
  stack off. **I cannot say how much of the ~$30,300/MW-yr gap is the
  lookahead's flattening and how much is the forecast path's missing mechanism
  stack.** Separating them needs one solve: the same hindcast config with
  `entry_lookahead_reprice` off, compared to FFR-3V's run. I did not spend it —
  the §3 bound closes this lane's actual question without it, and MISO is
  ~8.6 GB per solve.
* **I did not compute `cum_cap[-1]` exactly.** The §3.2 reserve bound rests on
  two independently measured figures (11 GW deliverable floor, 31.9 GW idle
  headroom) plus the monotonicity argument from the logged $39 ceiling, all of
  which are *conservative* relative to the lookahead's looser measure. An exact
  `cum_cap[-1]` would need a fleet build; it would tighten the presentation, not
  the conclusion. (`scripts/regenerate_clean.py` was started and then stopped
  once the bound closed.)
* **I did not check whether the forecast *default* config sets
  `entry_lookahead_reprice`.** §5 reports only what the run configs on disk
  carry.
* **I did not establish why the forecast path drops each ISO's calibrated
  reserve mechanism stack.** §2 measures that it does, for all six ISOs. Whether
  that is deliberate (forecast-mode cost/robustness) or an omission is a
  separate question, and it is the more consequential one.
* **Solar's capture-price arithmetic is FFR-3V's, not re-derived.** I checked
  only that no scarcity adder can move it.
* **No PJM/NYISO/CAISO remedy is implied.** §2's map is reported per rule 25;
  their cells stay as their own lanes left them.

---

## 7. Rule compliance

* **Rule 22 `[R-HOLDOUT]`:** only 2023–2025 artifacts and measured data were
  read. No out-of-training year (2022, 2019, ≤2021, H1-2026) was solved, scored
  or read. No solve of any kind was run. Holdout freeze untouched.
* **Rule 1 `[R-STRUCT]` / 11:** nothing was armed or rejected on a residual. The
  overlay is reported inert on *measurement of the mechanism*, and §5 explicitly
  preserves the rule-1 route to arming it on fidelity grounds despite that.
* **Rule 14 `[R-ACCURATE]`:** limb 4 is checked against MISO's measured hub LMP
  distribution, not a modelled proxy.
* **Rule 25 `[R-ISO-SCOPE]`:** the per-ISO map is reported; no ISO is armed from
  another's evidence; the ERCOT-parameter-inheritance hazard is called out.
* **Rule 28 `[R-MECH-MATRIX]`:** the `ordc_scarcity_overlay` MISO cell stays
  **`G`** — this session produced no evidence to overturn it and every new
  measurement reinforces it. Its `ev.M` citation and note are extended with this
  session's forecast-lane bound in the same session (§8 of the commit).
* **Scope:** diagnosis only. No promotion, no default flipped, no band widened,
  no ORDC parameter tuned, no scarcity adder added, no new mechanism proposed.
