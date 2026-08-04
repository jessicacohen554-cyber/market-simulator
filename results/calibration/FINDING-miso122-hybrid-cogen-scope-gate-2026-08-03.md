# FINDING miso-122 — the hybrid-cogen scope gate: eGRID's plant-level CHP split cannot see a package boiler, and CEMS can

Session miso-122, 2026-08-03, branch `claude/miso-c7-coal-mechanism-6d828k`, off
`origin/main` at `9aca82b`. Pre-registration
`results/calibration/PREREG-miso122-hybrid-cogen-scope-gate-2026-08-03.md`,
written and committed **before** the probe was written. Probe
`scripts/probes/_miso122_hybrid_cogen_scope.py`; transcript
`results/calibration/PROBE-miso122-hybrid-cogen-scope-2026-08-03.txt`; A/B
scorer `scripts/probes/_miso122_scope_gate_ab.py`; A/B record
`results/calibration/_miso122_scope_gate_ab.json`.

**Lever, and why this one.** The MISO queue head as written
(`docs/mechanism-testing-matrix.md` §5.4, closing line): *"the 55088 Dearborn
hybrid-cogen scope gate (item 4 above, named not chartered)"*. Every other MISO
item is adjudicated (`R`/`I`/`G`) or data-blocked; the C7 `COAL_PRB` lane is
closed and is not touched here. Matrix cell: `measured_chp_heat_rates` × MISO,
already `K` — this session changes that mechanism's **derive scope gate**, not
its arming, which is the rule 19 `[R-ONE-MECH]`-correct shape. Admissible on
rule 14 `[R-ACCURATE]` grounds **only**, and it ships whatever it does to the
residual.

## 1. The defect, one layer past miso-118

`scripts/data/derive_chp_power_only_heat_rates.py` charges **all** of a plant's
fuel to its power — right for a topping cycle, where the process steam is a free
co-product of turbine exhaust. Its two scope gates both read eGRID's **plant**-
level allocation, and a plant-level allocation cannot see a **hybrid**: a
topping CC/CT train *plus* a direct-fired package boiler on one ORIS code.

At MISO 55088 Dearborn the plant-average `thermal_share` is 0.2396 — comfortably
under the derive's 0.50 unfired ceiling, so the gate passes it — while **16.6 %
of the plant's metered fuel is burned in three `Other boiler` units that report
zero gross load all year**. CEMS resolves that at unit grain. eGRID cannot.

## 2. The correction, and what makes it admissible

    dark_share = CEMS heat input of units with heatInput > 0 and grossLoad == 0
                 over the WHOLE vintage year
                 ---------------------------------------------------------------
                 CEMS heat input of ALL units at the plant

    heat_rate  = (PLHTIAN + CHPCHTI) * (1 - dark_share) / PLNGENAN

It is a **share**, never an MMBtu subtraction: that needs CEMS's fuel
*composition* to be representative, never CEMS's *level* to equal eGRID's, so
the denominator stays `PLNGENAN` and no re-basing rides along. Same vintage on
both sides. **Zero free parameters and no threshold** — a plant with no dark
units gets `dark_share = 0.0` and a byte-identical rate, so the gate is a strict
no-op wherever the phenomenon is absent (rule 5 `[R-NO-MAGIC]`).

**Rule 13 `[R-MEASURED]`:** every eGRID vintage ships the split and every CAMPD
year ships the unit-grain fuel/gross channels, so the corrected rate regenerates
for a forward year and responds to a plant re-configuring its boilers. It is an
INPUT — a physical property of the machine — never a measured outcome fed back.

**Rule 23 `[R-FROZEN-DERIVE]`:** a **scope-gate logic** change on measured
grounds, which miso-118 §5(b) states rule 23 permits. The re-derivation commit
cites *that*, not a residual, and no source data was refreshed.

## 3. Phase 0 — the census across all five artifact ISOs, and it does NOT stay in MISO

miso-118 measured the phenomenon inside MISO and concluded "it does not
generalise". Swept across the five ISOs the derive writes an artifact for, at
the artifact's own 2023 vintage, **that scoping was too narrow — three plants in
three different ISOs carry it, 1,994 MW inside MISO alone and 2,506 MW in
total:**

| ISO | plant | class | cap MW | dark share | loaded HR | corrected HR | delta | disposition |
|---|---|---|---:|---:|---:|---:|---:|---|
| MISO | 55088 Dearborn Industrial Generation | `CC_CHP` | 350.0 | 16.6 % | 8.3465 | 6.9573 | **−16.6 %** | corrected here |
| MISO | 55088 Dearborn Industrial Generation | `CT_CHP` | 165.0 | 16.6 % | 8.3465 | 6.9573 | **−16.6 %** | corrected here |
| MISO | 10745 Midland Cogeneration Venture | `CC_CHP` | 1,479.4 | 0.09 % | 8.8243 | 8.8160 | −0.09 % | corrected here |
| NYISO | 2493 East River | `CT_CHP` | 306.0 | 37.5 % | 11.8032 | 7.3763 | −37.5 % | **excluded** (`below_credited`) |
| NEISO | 1595 Kendall Green Energy | `CC_CHP` | 206.0 | 1.2 % | 9.5584 | 9.4423 | −1.2 % | NEISO's lane |
| PJM | — | — | — | none > 0 | — | — | — | no row moves |
| CAISO | — | — | — | none > 0 | — | — | — | no row moves |

Every pre-registered kill resolves:

* **K1 — the dark units are boilers, not turbines with a reporting gap.**
  **100.0 %** of dark fuel at every plant found sits in a boiler `unitType`
  (`Other boiler` at Dearborn and MCV, `Dry bottom wall-fired boiler` at East
  River and Kendall), against a 90 % bar. The selection is purely behavioural —
  no `unitType` allowlist, which would be the hand map rule 24 `[R-REGISTRY]`
  forbids — and K1 is the check that the behaviour picked the right objects.
* **K2 — persistence.** Non-zero every year with max/min inside 2.0 at all four:
  Dearborn 16.64 / 14.82 / 16.82 % (1.13), MCV 0.09 / 0.09 / 0.05 % (1.80),
  East River 37.51 / 30.80 / 30.64 % (1.22), Kendall 1.21 / 0.96 / 1.48 %
  (1.54). This is machinery, not a reporting spike.
* **K3 — two-meter reconciliation.** `cems_vs_egrid_total` = 1.0 at all four.
* **K4 — the corrected rate stays physical.** PASS at all three MISO rows.
  **It FIRES at NYISO 2493 East River**, whose 37.5 % dark share removes more
  fuel than eGRID's *entire* CHP credit (corrected 7.3763 against a credited
  7.4205), so the two sources disagree about where that plant's boundary is.
  Its pre-registered disposition is per-plant exclusion, and the derive now
  implements it as a `below_credited` flag.
* **K6 — coverage honesty.** CEMS does not cover 10 of MISO's 25 `ok` rows
  (375 of 6,732 MW), 14 of PJM's 21, 20 of CAISO's 30, 5 of NYISO's 18 and 10
  of NEISO's 12. Those rows keep `dark_share` unmeasured and applied as 0.0 —
  **the status quo, and explicitly not a claim that they burn no dark fuel.**

**K5 — no-op fidelity.** Re-deriving all five ISOs changes the applied
`heat_rate` on **exactly** the dark-fuel rows and nothing else: MISO 4 rows
(3 applied), PJM 2 (0 applied — both already `not_unfired_topping`), CAISO 0,
NYISO 1 (the East River exclusion), NEISO 1. **Zero** unintended flag churn.
One cosmetic residue is reported rather than buried: `cems_heat_mmbtu` on MISO
64854 moves 4,735,374.5 → 4,735,374.6 MMBtu, a float-summation-order artifact
of grouping by unit before summing (1 part in 5×10⁷, rounded at one decimal);
that row's applied `heat_rate` is byte-identical.

### 3.1 Two exclusions the census forced into the gate, both measured

The first pass of the gate — share applied unconditionally — produced two
absurd results that the census exposed and that are now closed in the derive:

1. **`dark_unreconciled`.** At a plant whose combustion units sit **below the
   Part-75 reporting threshold**, CEMS meters the boilers and misses the
   turbines, so the dark share runs to 100 % and would drive the rate to zero.
   The derive's own header already names three such MISO plants (10328, 55096,
   55799). The gate now applies only where `cems_vs_egrid_total` is inside
   **[0.90, 1.10]** — miso-118's pre-registered two-meter agreement band,
   reused rather than reinvented — and treats an entirely-dark footprint the
   same way, because CEMS never saw the power train there either. Measured
   effect: MISO 10328 (100 % dark) and 55096 (22 % dark) correctly keep their
   rates; without the band they would have been repriced on a meter that is not
   looking at the same machine.
2. **`below_credited`.** As above, NYISO 2493.

Both are exclusions, never substitutions — rule 14's named "different boundary"
exception, and never a guess.

## 4. Phase 1 — the A/B: **DISPATCH-LIVE, PRICE-INERT**

Arms `2026-08-04-miso-122a-control` (`miso122_control_A`) and
`2026-08-04-miso-122b-scope-gate` (`miso122_scopegate_B`), one invocation each
over `--years 2023 2024 2025`, arms sequential. **The single delta is the input
artifact**, sha256 `4cbeb961…` → `949fc67a…`; the two `run_config.json`
scenario blocks are byte-identical, which is this lever's correct signature and
**not** a wiring failure.

**Did it fire? Yes, on two independent checks, neither of which is a log line.**
W1, pre-arm, through the model's own `load_fleet_from_csv` with the keeper's
flags: 55088 `CC_CHP` 350.0 MW and `CT_CHP` 165.0 MW both load at **6.9573**
against the control's 8.3465, and 10745 `CC_CHP` 1,479.4 MW at **8.8160**
against 8.8243 — the pre-registered values exactly. W2, post-arm: both touched
classes move in all three years.

*(The miso-113 "P1 warm-re-solved the P0 model" hazard does not apply and was
not treated as one: a heat rate enters at fleet load, before P0, so BOTH passes
carry the corrected rate and a warm P1 is the correct path. That hazard is
specific to `p1_fleet_prep` floors.)*

| gate | result |
|---|---|
| **K1** artifact fidelity | **PASS** — sha differs, mechanism armed in both arms, exactly 3 applied rows move (−16.64 / −16.64 / −0.09 %), none added, none dropped |
| **K2** control integrity | **PASS** — the control is **byte-identical to the keeper** (max class-hour \|Δ\| ≤ 1e-6 in all three years), same determination, same nine criterion statuses |
| **K3** liveness | **dispatch PASS / price FAIL** — see below |
| **K4** zero config delta | **PASS** — **zero** differing `ScenarioConfig` keys; a pure input-only A/B |
| **K5** year span | **PASS** — both bundles `[2023, 2024, 2025]` |
| **K6** direction integrity | **PASS** — no applied row's rate rose (arithmetic: `(1 − dark_share)` is non-increasing), system λ falls every year, **no zone's λ rises** above tolerance |
| **P1–P6** | **all PASS** — 12/12 free classes and 16/16 all classes in BOTH arms, the same single `FAIL` (`shape`) in both, slack+dump identical to the MWh |

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| max class-hour \|Δ\| (MW) | 912.500 | 912.500 | 914.662 |
| **max zonal \|Δλ\| ($/MWh)** | **0.0491** | **0.0390** | **0.0752** |
| Δ system demand-weighted λ | −0.0417 | −0.0317 | −0.0568 |
| `CC_CHP` energy Δ (TWh) | +0.3575 | +0.2718 | +0.5190 |
| `CT_CHP` energy Δ (TWh) | +0.2197 | +0.2218 | +0.2240 |
| `CC_REGULAR` | −0.1932 | −0.2249 | −0.3081 |
| `import` | −0.1520 | −0.1115 | −0.1290 |
| `COAL_PRB` | −0.1074 | −0.0558 | −0.1420 |

**The verdict on the pre-registered rule.** `max zonal |Δλ| ≥ 0.10 $/MWh in ≥ 2
of 3 years` is the LIVE bar; the measured 0.049 / 0.039 / 0.075 clears it in
**zero** years. So the branch is **DISPATCH-LIVE / PRICE-INERT**, and by the
pre-registration's own disposition **the mechanism cell is NOT re-stamped `I`** —
`measured_chp_heat_rates` is `K` at MISO and stays `K`. What is price-inert is
this *scope gate*, which is a different object.

**What it does do is re-order the stack correctly.** The corrected cogen
displaces roughly 0.58 / 0.49 / 0.74 TWh of merchant `CC_REGULAR`, imports,
`COAL_PRB` and `CT_PEAKER` — a plant that was being charged 16.6 % too dear now
runs where it should. That is the rule 14 `[R-ACCURATE]` gain, and it is
invisible at every scored grain because 515 MW does not set price in a
~100 GW market.

**DO-NOT-MISREAD, extending miso-119's and miso-121's.** `max_abs_class_hour_mw`
is **not** a magnitude of the mechanism at MISO. It reads **912.5 MW here and
912.5 / 912.5 / 912.500061 at miso-119** — two unrelated levers, the same
number to seven figures — because in both cases the statistic lands on the
`import` class, where a single **912.5 MW seam band** flips in or out. Measured
on this arm's own 2023 output: the import delta is non-zero in 1,546 h with a
median of 72 MW, and hits exactly 912.5 in **7** of them. The K3 dispatch
statistic at MISO is therefore quantised by the seam ladder and near-constant
across levers. **The informative statistics are the per-class ENERGY deltas**
(above), not the max class-hour.

The chain now reads: miso-119 — a percentile of the offer delta over-predicts
by two orders of magnitude; miso-121 — *binding is not marginality*, use the
marginal share of binding hours; miso-122 — the max class-hour delta is a seam
quantisation constant, not a mechanism magnitude.

## 5. Rule duties

* **Rule 15 `[R-DASHBOARD]`** — both arms registered in this session.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025 in one bundle per arm.
* **Rule 22 `[R-HOLDOUT]`** — training years only; no out-of-training year was
  solved, scored **or read**.
* **Rule 25 `[R-ISO-SCOPE]`** — **only MISO's artifact is re-derived here.**
  The derive is ISO-agnostic code and the census had to be ISO-wide before it
  could ship, but a re-derived artifact is an input change to that ISO's
  keeper, and each lane owns its own A/B. NYISO and NEISO are handed off in §6
  with measured numbers; no verdict cell outside MISO is stamped.
* **Rule 28 `[R-MECH-MATRIX]`** — the `measured_chp_heat_rates` × MISO cell's
  evidence is re-stamped in this session. The cell stays `K`; a scope-gate
  refinement inside a `K` mechanism is not a new verdict.

## 6. The keeper question — a seam this session opens and does NOT close

**The corrected artifact is now the committed input, so the designated MISO
keeper `2026-08-03-miso-117b-ct-heat` is no longer reproducible from HEAD.**
That is stated plainly rather than left to be discovered: it solved on the
pre-gate `chp_power_only_heat_rates_MISO.csv`, and HEAD now carries the
corrected one.

**Arm B is the promotion candidate, and this session does not promote it.**
The evidence, for whoever does:

* It is the only registered MISO run whose inputs match HEAD.
* **Nothing regresses.** All nine criteria carry identical statuses in both
  arms (`dispatch_corr`/`forced_share`/`fuelmix`/`governance`/`price_shape`/
  `sysvol` PASS, `price_mean`/`price_tail` CAVEAT, `shape` FAIL), the same
  determination `NOT-YET`, the same single ledgered FAIL, 12/12 free classes
  and 16/16 all classes in both.
* **Rule 22's leave-one-year-out is satisfied at year grain by construction:**
  no single year carries the result. Dispatch moves and price stays under the
  bar in each of 2023, 2024 and 2025 taken separately, and no criterion moves
  in any year.
* It is strictly more structurally faithful (rule 1 `[R-STRUCT]` / rule 14),
  which is the same ground miso-117b was promoted on — *"chartered on rule 14
  regardless of the residual"*.

Promotion in this repo is an owner call (miso-117b and ercot-150 were both
owner-authorized in-session), and there is no owner in this session, so the
keeper is **left unchanged** and the question is escalated rather than taken.
The determination would not move either way: `NOT-YET`, decided by the same C7
`COAL_PRB` diurnal-shape issue this lever does not touch and claims nothing
about.

## 7. Handoffs, with measured numbers

1. **NYISO 2493 East River — a real defect, and the opposite sign from
   Dearborn's.** 306 MW of `CT_CHP`, **37.5 / 30.8 / 30.6 %** of its metered
   fuel in two `Dry bottom wall-fired boiler` units with zero gross load, and
   the dark share removes **more than eGRID's entire CHP credit** (corrected
   7.3763 against a credited 7.4205). The gate therefore **excludes** it
   (`below_credited`) rather than correct it, which changes NYISO's applied
   map — 306 MW leaves it. **NYISO's artifact is deliberately NOT re-derived
   here** (rule 25): that is an input change to NYISO's keeper and needs
   NYISO's own A/B. The open question there is which meter is wrong about East
   River's boundary, and it is not answerable from MISO's data.
2. **NEISO 1595 Kendall Green Energy** — 206 MW of `CC_CHP`, dark share
   1.21 / 0.96 / 1.48 %, corrected 9.5584 → 9.4423 (−1.2 %). Clean on every
   kill; NEISO's lane to re-derive and A/B if it judges 1.2 % worth a session.
3. **PJM and CAISO carry nothing** above 0 % on their `ok`-flagged rows — no
   action.
4. **The MISO queue head is now open.** With the Dearborn item executed, §5.4
   has no named un-adjudicated item left: the C7 `COAL_PRB` family is closed
   (`R`/`R`/`I`), items 1–2 are data-blocked (the bounded next step is the Form
   580 count in `docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md`
   §8, a sourcing pass and not a solve), item 3 is `R` ex ante, items 4/5/6 are
   `K`/`I`/`I`. The two *named but unchartered* successors that remain are
   miso-114 §0c's hour-of-day-resolved seam **band availability** at the
   `(month × hour-of-day)` `MISO_SEAM_DIBA` grain — which, note, is the very
   seam whose 912.5 MW band quantises the K3 statistic above — and miso-118's
   `CT_CHP`-side plant-level rate question. Neither is chartered by this
   session.

## 8. Pre-existing `origin/main` breakage — reported, not fixed

`tests/regression/test_persisted_identity.py` fails on a **clean `origin/main`
worktree** at `9aca82b`, verified in a throwaway worktree, not on this branch's
changes (which touch no `ScenarioConfig` field):

* `test_default_scenario_config_cache_key_is_pinned` — default key
  **`973a0acdef818e91`** vs the pinned `603c2498bf71d21d`
* `test_backcast_scenario_config_cache_key_is_pinned`
* `test_default_cache_key_is_checkout_path_invariant` — **`973a0acdef818e91`**

**The drift has moved since the bisect quoted in this session's brief**
(`0e9fce2fb55b889f` → `973a0acdef818e91`), so at least one further field has
landed on top of the original culprit; the failing set is now three tests, not
the previously-named trio. Registering the culprit field(s) versus advancing
the pin belongs to the lane that owns them and is not touched here. Everything
this session added passes: `tests/unit/data/test_measured_chp_heat_rates.py`
22/22, including the seven new scope-gate cases.
</content>
