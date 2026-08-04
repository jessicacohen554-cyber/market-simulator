# FFR-3H — CAISO BLK-10: why 65.5 % of CAISO's additions come from the administrative backstop

**Session.** FFR Wave 3, the CAISO backstop-diagnosis lane. FFR-3A-2 §2.2 scored FC-2 row 4
for the first time and measured **CAISO 65.5 % → FAIL**; this session finds the cause.
Branch `claude/caiso-backstop-diagnosis-hvo3u5`, based on `origin/main` **`6040f28c`**.

**Diagnosis only. Nothing is fixed, tuned, promoted or re-banded.** No `ScenarioConfig`
default moved, no threshold widened, no parameter chosen. Two mechanisms were unarmed —
each as an **explicitly-labelled paired probe arm**, declared as such below, and neither
is promoted or recommended (rules 1 / 11 / 14).

**One-line result.** The 65.5 % is **three separate things stacked**, and the prompt's
leading hypothesis is **refuted as stated and confirmed in a sharpened form**:

1. **~37 pp of it is a booking-convention artifact of the FC-2 row-4 ratio** — the
   backstop books in-year while economic entry books at decision + 2 (measured: 65.48 %
   → **28.61 %** with the commissioning lag unarmed).
2. **The residual ~29 % is real**, and its cause is that **a CAISO `gas_ct` is
   `unprofitable` in the economic entry screen in every year of every arm** — by
   $39,974–45,316/MW-yr — so the administrative channel is the only one that can add
   firm capacity.
3. **47 % of the total backstop build closes a deficit the model already has in its base
   year** (2026: accredited firm 50,729 MW vs requirement 57,306 MW, **before any
   evolution step runs**). That is an accreditation-ledger question, not an entry question.

**The growth ladder is NOT the cause** — unarming it moves the cumulative share by
**0.84 pp** (65.48 % → 64.64 %) while completely re-phasing the build. That independently
reproduces, in CAISO, the same "re-phases, cumulative invariant" result FFR-2B measured in
MISO — measured separately per rule 25, not transferred.

**ERCOT's 0.0 % is preserved and now has its mechanism.** Measured this session:
`resolve_reserve_margin_build_enabled(ERCOT) = False`. ERCOT is not in the population at
all — its 0.0 % is structural, so FFR-3C's retirement/entry-asymmetry attribution for
ERCOT stands untouched. Rule 25 `[R-ISO-SCOPE]`: nothing below transfers to any ISO.

---

## 0. State re-verified at this HEAD (the packet was stale on two counts)

| item | packet said | **verified this session** |
|---|---|---|
| `origin/main` | `9aca82b8` | **`6040f28c`** (main had advanced; branch rebased onto it) |
| CAISO keeper | `2026-08-03-caiso163-asym-path-ratings` | **confirmed** — read from `frontend/data/backcast/keepers/CAISO.json` |
| `complete` markers | {NEISO, NYISO, PJM} | **unchanged** |
| `final` markers | EMPTY | **unchanged** |
| holdout spend freeze | ACTIVE | **unchanged, neither spent nor worked around** |

No out-of-training year was solved, scored or touched. Every solve below is **2026–2030,
forecast mode** — outside the quarantine by construction (rule 22's 2026 clause: forecast
runs use no measured H1-2026 actuals).

**Prerequisites, as briefed and as measured:** `uv sync` (**2 min**) then
`scripts/regenerate_clean.py` (**63 min**, 50/50 datatypes, 0 failures, 1.6 GB). The
`tzdata` blocker FFR-3C filed does **not** arise on the `uv` path (FFR-3A-2 §0.2 confirmed
again). `git status --short` was clean after the regeneration except for two **unrelated**
formatter-churn files (`scripts/gen_nyiso119_attestation.py`,
`tests/unit/pipeline/test_p1_prep_wiring.py`), reverted rather than carried.

### 0.1 ⚠ FINDING — CLAUDE.md's "default off" is WRONG for five of six ISOs

The packet asked this be established explicitly, and the doc and the shipped value **do**
disagree. CLAUDE.md's capacity-evolution step list reads *"6. Reserve-margin adequacy
backstop (GATED `reserve_margin_build_enabled`, **default off**)"*. Measured:

```
reserve_margin_build_enabled field default: None          (tri-state, NOT False)
resolve_reserve_margin_build_enabled ->  ERCOT False | CAISO True | PJM True
                                         MISO  True  | NYISO True | NEISO True
```

`None` resolves **per market design** (G-41, PJM hindcast I7 decision 2026-07-06): ON
wherever `MARKET_DESIGN[iso].capacity_market` is true. So in the **shipped forecast
posture the backstop is ARMED in every ISO except ERCOT.** "Default off" was true only
before G-41 and is now true only for energy-only ERCOT.

The same stale claim is repeated **inside `scenarios.py` itself**, in the
`market_design_retirement_floor` docstring 30 lines below the tri-state field: *"The
default-off `reserve_margin_build_enabled` backstop is untouched…"*. `forecast_verdict.py`
already had to be repaired for the identical misreading — FFR-3A-2 found row 4 was
short-circuiting to a false `PASS` because `bool(None)` read *unset* as confirmed *off*
(`forecast_verdict.py:760-779`). That is **three independent consumers** of the same wrong
premise. The mechanism matrix row `reserve_margin_backstop` is the one place that has it
right (`cells: ".KKKKK"`).

**Not fixed here** (this is a diagnosis charter, and a CLAUDE.md edit is a rule-28/§sync
action for the lane that owns it) — filed as blocker B-1 in §6.

---

## 1. Attribution — which years, which technologies, which zones

### 1.1 The measurement reproduces exactly, at the recorded key

**Arm A** is the shipped T1-F posture, byte-for-byte as FFR-3A-2 ran it
(`--golden-posture`, 2026–2030, all defaults inherited):

```
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ffr3h/caiso-A-repro
```

**Resolved cache key `e5822277b72184f6` — an EXACT match to FFR-3A-2 §2's recorded CAISO
T1-F key**, cold-solved in a fresh container at a different HEAD. Reserve-margin path
`1.80 / −3.12 / −0.31 / 12.35 / 15.28 %` matches §2.1's `1.8, −3.1, −0.3, 12.3, 15.3` to
the digit, and the share reproduces at **65.48 %**.

### 1.2 It is a PERSISTENT PER-YEAR RESIDUAL, not one large event

| year | peak MW | RM % | **backstop MW** | economic thermal | renew | storage | retire |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2026 | 49,831 | 1.80 | **0.0** | 0.0 | 0.0 | 0.0 | 0.0 |
| 2027 | 51,018 | −3.12 | **1,396.4** | 0.0 | 0.0 | 0.0 | 1,492.5 |
| 2028 | 52,245 | −0.31 | **2,792.8** | 0.0 | 0.0 | 0.0 | 0.8 |
| 2029 | 53,512 | 12.35 | **5,585.6** | 2,000.0 | 4,702.2 | 0.0 | 0.0 |
| 2030 | 54,821 | 15.28 | **4,268.8** | 0.0 | 702.2 | 0.0 | 1,122.0 |
| **Σ** | | | **14,043.6** | 2,000.0 | 5,404.4 | **0.0** | 2,615.3 |

`14,043.6 / 21,448.0 = ` **65.48 %**.

**Technology: 100 % `gas_ct`. Zone: 100 % `NP15`. Grain: exactly one unit per year**
(`gas_ct_adequacy_2027 … _2030`). Both are hardcoded, not chosen —
`apply_reserve_margin_build` always builds a single `gas_ct` at `_default_build_zone(iso_config)`.

**The 2027–2029 builds are EXACTLY the growth ladder, to the decimal:** the CAISO EIA-860
`gas_ct` throughput seed is 0.6982 GW/yr, and `ENTRY_GROWTH_LIMIT_MULTIPLE = 2.0`, so
1,396.4 → 2,792.8 → 5,585.6 is 2× compounding on the prior max. The backstop in those
years is **rate-limited, not need-limited**: the 2027 firm gap was ~9.2 GW and it built
1.4 GW. Only 2030 (4,268.8 < 2 × 5,585.6) is need-limited — the year the gap finally closes
and the margin lands at 15.28 % against a 15.00 % requirement.

**Reading:** this is the signature of a rate-capped channel *grinding out an inherited
deficit over four years*, not of a backstop over-firing. Whatever is wrong, the backstop
is the symptom.

### 1.3 The inherited deficit — 47 % of the whole build exists before evolution runs

I7, arm A, base year: **accredited firm 50,729 MW vs requirement 57,306 MW — short by
6,577 MW in 2026**, a year in which the model performs no capacity evolution at all
(no retirements, no additions, no entry decisions in the ledger). Reserve position 0.8852.

Reconstructed from the run's own artifacts (ledger `fleet_by_fuel_after`, `firm_clean_mw`,
trajectory `capacity_by_fuel_mw`, and the shipped accreditation registries):

| class | nameplate MW | credited firm MW | basis |
|---|--:|--:|---|
| thermal (7 fuels) | 31,957.2 | 30,221.4 | UCAP, `1 − EFORd` per fuel |
| conventional hydro | 6,568.4 | 4,624.8 | 0.7041 — CPUC **non-dispatchable** class factor |
| solar | 22,000.0 | 3,960.0 | **0.18 generic fallback** (CAISO has no curve, no override) |
| wind | 7,000.0 | 1,120.0 | **0.16 generic fallback** |
| firm imports | — | 3,371.0 | DMM 2024 Table 15.6 RA imports (not the 16,148 MW MIC) |
| storage (residual) | 8,000 + PS | 7,431.8 | duration ELCC |
| **accredited (I7)** | | **50,729.0** | |
| **requirement** | | **57,306.0** | peak × 1.15, **no DR netting, ICAP→UCAP ratio 1.0** |
| **deficit** | | **−6,577.0** | |

Requirement growth over the window is +5,739 MW (peak 49,831 → 54,821 × 1.15) and
retirements remove 2,615 MW nameplate. So the 14,043.6 MW of backstop decomposes roughly
as *inherited deficit 6,577 + requirement growth 5,739 + retirements ~2,470 − economic firm
arriving ~2,800*, and **the single largest term is the base-year deficit**.

### 1.4 Storage adds ZERO MW in all five years

`storage_additions` is empty in every year, against a CAISO annual build cap of 3,000 MW
and 17 GW of headroom to the 25,000 MW deployment ceiling. The ISO whose real-world
adequacy answer is batteries adds none, while the administrative channel adds 14 GW of CTs.
(Caveat, stated so it is not over-read: the base fleet **does** carry 8,000 MW of storage
plus pumped storage — the finding is zero *additions*, not an empty fleet. The trajectory's
`storage_mw` column reading 0.0 in every year is a separate **instrument defect**, B-3 in §6.)

---

## 2. The leading hypothesis, tested — REFUTED as stated, CONFIRMED sharpened

> *"Economic entry under-delivers in CAISO BECAUSE the flat CPM proxy gives the entry
> screen no capacity revenue to see, so the adequacy gap survives to step 6."*

**Arm B** re-ran the identical posture with `entry_screen_diagnostics` armed — the RC-0C
per-candidate decomposition sink, which `run_capacity_hindcast.py` has always exposed and
this runner did not (added here as an instrument; §7). It is observability-only, and that
was **verified in situ, not assumed**: arm B's trajectory is identical to arm A's in every
cell despite taking its own cache key (`0a41c0d0bd87eec2` — the field is not in
`_CACHE_KEY_OPTIONAL_FIELDS`).

### 2.1 REFUTED as stated: the screen sees $82,795/MW-yr, not zero

`gas_ct` entry economics, arm B ($/MW-yr):

| year | energy | **capacity** | AS | **revenue** | **cost** | **margin** | verdict |
|---|--:|--:|--:|--:|--:|--:|---|
| 2027 | 5,343 | **82,795** | 0 | 88,138 | 128,112 | **−39,974** | `unprofitable` |
| 2028 | 4,305 | **82,795** | 0 | 87,100 | 128,112 | **−41,011** | `unprofitable` |
| 2029 | 2,081 | **82,795** | 0 | 84,876 | 128,112 | **−43,235** | `unprofitable` |
| 2030 | **27** | **82,795** | 0 | 82,823 | 128,112 | **−45,289** | `unprofitable` |

The capacity term is **$82,795/MW-yr — 64.6 % of the entire CT hurdle** (the $88.08/kW-yr
CPM anchor × the `1 − EFORd` accreditation). The hypothesis' literal claim, that the screen
has "no capacity revenue to see", is **false**. Across all six ISOs the flat-mode payment
ranks CAISO third of five capacity-market ISOs:

| ISO | CT hurdle $/MW-yr | flat capacity payment | residual energy+AS must cover | FFR-3A-2 backstop share |
|---|--:|--:|--:|--:|
| NEISO | 128,112 | 108,940 | **19,172** | **11.7 %** |
| NYISO | 128,112 | 103,400 | **24,712** | **23.8 %** |
| **CAISO** | 128,112 | **82,795** | **45,316** | **65.5 %** |
| MISO | 128,112 | 75,012 | 53,100 | not measured |
| PJM | 128,112 | 46,459 | 81,653 | not measured |
| ERCOT | 128,112 | 0 | 128,112 | 0.0 % (channel OFF) |

Across the three ISOs FC-2 row 4 actually measured, the ordering of the residual is
**exactly** the ordering of the backstop share. n = 3, so this is a consistency check, not
an identification — and ERCOT is not a counterexample because it has no backstop channel.

### 2.2 CONFIRMED sharpened: the price is FLAT, and cannot respond to an 18 pp shortfall

`capacity_revenue_per_mw_yr` returns **$82,795 in every year of every one of the four
arms**, while CAISO's reserve position runs **0.885 / 0.843 / 0.867 / 0.977**. FFR-2E
proved *why*, and this session's ledger is the downstream consequence: `MARKET_DESIGN["CAISO"]`
carries `demand_curve=()` and `seasonal_rbdc=None`, so the curve branch's own guard is
false and the seam falls through to the flat anchor **in both postures** — the clearing
gate resolves `True` for CAISO and changes nothing (FFR-2E §2, *"a proof, not a sample"*).

Every other capacity-market ISO's price rises when it is short. At reserve position 0.95,
FFR-2E's price sweep measures PJM $150,541, NEISO $157,188, MISO $103,040 (and $509,446 on
the 2025-26 seasonal RBDC) — 1.3–6.4× their own anchors. **CAISO pays $88,080 at position
0.84 and $88,080 at position 1.10.**

The magnitude lines up: `gas_ct` needs **+$40.0–45.3 k/MW-yr**, i.e. a capacity price of
**≈ 1.48–1.55 × the flat anchor**, to clear. That multiple sits inside the range published
sloped curves reach at a short position. **This is stated as a magnitude scale, not a
transfer**: rule 25 forbids importing another ISO's curve verdict, CAISO publishes no
demand curve to import, and that absence is precisely the open blocker (§5).

So the corrected finding is: **not "the entry screen sees no capacity price" but "the entry
screen sees a capacity price that cannot know CAISO is short."** The one signal that should
call forth firm capacity during an adequacy shortfall is, by construction, invariant to the
shortfall.

### 2.3 The self-defeating half — the backstop destroys the signal that would replace it

`gas_ct` energy margin over the window collapses **5,343 → 4,305 → 2,081 → 27 $/MW-yr**.
The probe arms make the causal direction unmistakable: **the faster the backstop builds,
the faster it collapses.**

| arm | 2027 backstop MW | gas_ct energy margin 2027 → 2030 |
|---|--:|---|
| A/B shipped (ladder-capped) | 1,396 | 5,343 → 4,305 → 2,081 → **27** |
| C no-lag | 1,396 | 5,343 → 1,518 → 487 → **5** |
| **D no-ladder** (8 GW in one year) | **8,000** | 5,343 → 243 → 37 → **0** |

Every CT the administrative channel builds suppresses the scarcity hours that would have
paid for the economic CT entry the model wants instead. This is a rule-19 `[R-ONE-MECH]`
pathology in its purest form: two mechanisms answer one phenomenon, and the administrative
one erodes the economic one's price signal for the same product. It is a **ratchet** — once
the backstop starts, economic firm entry can only get less profitable.

### 2.4 The internal inconsistency the ledger makes visible

Wind, solar and geothermal show `capacity_revenue_per_mw_yr = 0` in **every** row of
**every** arm — `entry_vre_capacity_revenue` ships default-OFF (owner decision D-2′ HELD).
But `accredited_firm_capacity_mw` **does** credit CAISO solar at 0.18 and wind at 0.16 of
nameplate toward the very requirement the backstop is enforcing.

So the model simultaneously holds that a CAISO solar MW is worth 0.18 firm MW of adequacy
**and** that it should be paid $0 for it. The only candidate that can be *induced* by an
adequacy shortage is therefore a thermal one — and the only thermal one is the one the
screen has just priced as losing $40 k/MW-yr. **That asymmetry, not a shortage of
candidates, is what leaves step 6 as the only channel that can move.** Solar and wind are
meanwhile among the most profitable candidates on the board ($87–190 k/MW-yr margins) and
are `growth_ladder` / `per_tech_cap` / `per_tech_cap_zero` bound in every single year — they
are throughput-limited, never economics-limited.

---

## 3. The full enumeration — everything else that could produce it, adjudicated

Rule 19's discipline applied to diagnosis: enumerate what *else* already acts on this
phenomenon before concluding. Two candidates were tested with **explicitly-labelled paired
probe arms** (declared here per the charter; **nothing is promoted, nothing recommended**).

| # | candidate | verdict | evidence |
|---|---|---|---|
| **1** | **Commissioning lag (D-2, `entry_commissioning_lag`, ARMED)** | **DOMINANT single contributor: −36.9 pp** | probe arm C, §3.1 |
| **2** | **Firm-entry unprofitability (flat capacity price)** | **CONFIRMED — the residual cause** | §2.1–2.2, all four arms |
| **3** | **Inherited base-year accreditation deficit** | **CONFIRMED — 47 % of the build** | §1.3 |
| **4** | Backstop/economic-entry sequencing blindness | **CONFIRMED in code, magnitude not isolated** | §3.2 |
| **5** | Backstop → energy-price feedback ratchet | **CONFIRMED, direction proven by arm D** | §2.3 |
| **6** | **Growth ladder (D-2, `entry_rate_limits`, ARMED)** | **REFUTED — 0.84 pp, re-phases only** | probe arm D, §3.1 |
| **7** | Storage value stack | **CONTRIBUTES via the denominator; cause not isolated** | §1.4 |
| **8** | Locational deliverability (`capacity_deliverability_limits`) | **RULED OUT of this measurement** | §3.3 |
| **9** | ELCC saturation collapsing VRE credit | **RULED OUT — CAISO's curve is flat** | §3.3 |
| **10** | Net-CONE currency / staleness | **NOT the level problem it looks like** | §3.4 |
| **11** | Exit-throughput asymmetry (FFR-3C G-31) | **PRESENT, feeds the backstop rather than a collapse** | §3.5 |

### 3.1 The two probe arms — the isolation

> **⚠ EXPLICITLY-LABELLED PAIRED PROBE ARMS.** Arms C and D unarm one owner-signed D-2
> mechanism each, solely to isolate its contribution. Both remain **ARMED** in the shipped
> posture; **neither is promoted, recommended, or offered as a fix** (owner decision D.1 —
> HOLD PROMOTION, FIND ROOT CAUSE — is honoured).

| arm | posture | resolved key | backstop MW | total add MW | **share** | row 4 | RM path % |
|---|---|---|--:|--:|--:|---|---|
| **A** | shipped (reproduction) | `e5822277b72184f6` | 14,043.6 | 21,448.0 | **65.48 %** | **FAIL** | 1.80 / −3.12 / −0.31 / 12.35 / 15.28 |
| **B** | shipped + entry diagnostics | `0a41c0d0bd87eec2` | 14,043.6 | 21,448.0 | **65.48 %** | **FAIL** | *identical to A* |
| **C** | *probe:* `--no-entry-commissioning-lag` | `3f512d7246d2672a` | 10,783.9 | 37,699.3 | **28.61 %** | CAVEAT | 1.80 / 2.24 / 6.72 / 16.30 / 17.21 |
| **D** | *probe:* `--no-entry-rate-limits` | `e458dda9bb4471ec` | 14,627.2 | 22,627.2 | **64.64 %** | **FAIL** | 1.80 / 9.18 / 15.09 / 17.25 / 15.03 |

**Arm C — the commissioning lag is the dominant measured contributor, and it works through
the DENOMINATOR.** The backstop itself falls only 23 % (14,043.6 → 10,783.9 MW) while total
additions rise **76 %** (21,448 → 37,699 MW). `ENTRY_COD_LAG_YEARS = 2`, so in a 2026–2030
window the 2029 and 2030 decision years commission in 2031/2032 and are **censored out of
the denominator entirely** — while the backstop, which commissions in-year, loses nothing.
This is FFR-3A-2 §3.5's censoring mechanism, previously recorded as biting the T1-H
*additions bands*, now measured biting the FC-2 row-4 **ratio**.

Re-booking the shipped arm on a **decision grain** — which asks the same question without
changing the model — gives the same story from the other side:

```
shipped arm, DECISION grain      : 14,043.6 / 31,852.4 = 44.09 %   (still FAIL)
shipped arm, COMMISSIONING grain : 14,043.6 / 21,448.0 = 65.48 %   (as scored)
```

**~21 pp of the headline is the booking convention alone**, on the *unmodified* model.

**Arm C also identifies CAISO's negative reserve margins.** The path goes from
`−3.12 / −0.31 %` to `+2.24 / +6.72 %`, and I12 stops reporting any negative year. So the
lag is the proximate cause of the FFR-3A/FFR-3A-2 CAISO headline `−3.1 %` as well — the
fleet cannot use, and the backstop cannot see, 6.7 GW of decided-but-pending entry.

**Arm D — the growth ladder is REFUTED as a cause.** Cumulative share moves **0.84 pp**
(65.48 → 64.64 %) and cumulative backstop MW moves **+4.2 %**, while the phasing changes
completely: 2027's build goes 1,396 → **8,000 MW** (the CAISO `QUEUE_CAP_GW` of 8), and the
reserve-margin path flips from `−3.12 / −0.31` to `+9.18 / +15.09`. This is the **same
signature FFR-2B measured in MISO** — *"does NOT reduce BLK-10 magnitude … −0.07 %, i.e.
INVARIANT. It RE-PHASES"*. Measured **independently in CAISO**; the MISO verdict is not
transferred (rule 25), and the agreement is reported as corroboration only.

### 3.2 Sequencing — the backstop is blind to what economic entry has already decided

Established from code, not inferred. At step 6, `evolve_fleet` computes `firm_mw` from
`fleet` plus **prior-year** `wind_pool_mw` / `solar_pool_mw` / `storage_firm_mw`
(`evolve.py:278–287, 688–700`). That excludes, all at once:

* **this year's economic thermal decisions** — with the lag armed they go to
  `entry_pipeline`, not `fleet`;
* **prior years' still-pending pipeline MW** — up to two full decision-years' worth, which
  live in the pipeline until COD and are invisible to the gap test;
* **this year's economic VRE decisions** — the pools passed in are the prior year's;
* **this year's storage entry entirely** — `apply_storage_new_entry` is called at
  `runner.py:1158`, *after* `evolve_fleet` returns at `runner.py:1063`.

The one netting that does exist is on the **budget**, not the **need**:
`_gas_ct_rate_budget` subtracts this year's economic `gas_ct` decisions from the ladder
(`evolve.py:700–710`), correctly treating the two channels as one physical queue. Nothing
subtracts the pending pipeline from the **firm gap**. So the backstop re-fills, at
nameplate and in-year, a gap that contracted entry is already going to fill.

**Magnitude not isolated.** Separating it needs an arm that nets the pipeline into the gap
test — and that is a *change to the mechanism*, which this charter forbids. Recorded as
confirmed-in-code, unquantified.

### 3.3 Two candidates ruled OUT, not merely unlikely

**Locational deliverability is not in this measurement.** `capacity_deliverability_limits`
resolves **`False`** in the shipped T1-F posture (verified by direct config read). Its
unvalidated RA-saturation half therefore cannot be contributing to the 65.5 %. Note the
contrast worth carrying forward: the **CAISO backcast keeper** (caiso-51 onward) *does*
enable it, for the measured-seam-import half — so backcast and forecast differ here, and a
successor must not assume the keeper's posture describes the forecast leg.

**ELCC saturation is structurally impossible for CAISO.** `RENEWABLE_ELCC_CURVES_BY_ISO`
contains PJM, MISO and NYISO only; `RENEWABLE_CAPACITY_CREDIT_BY_ISO` contains ERCOT only.
CAISO falls through to the **generic flat fallback**, measured invariant across a 0.2×–2.0×
penetration sweep (solar 0.18, wind 0.16 at every point). VRE credit cannot collapse as the
model builds, so a saturating-ELCC story is excluded.

That exclusion is itself a finding under rule 14 `[R-ACCURATE]`: **the ISO with the most
elaborate published VRE accreditation in the country — CPUC slice-of-day / ELCC — is
accredited in this model on a generic non-CAISO number.** Its *direction* is unresolved
(§4), so it is filed as an open ledger question, not as a shortfall.

### 3.4 Net-CONE currency — the anchor is current, but it is not a net-CONE

CAISO's $88.08/kW-yr is **not stale**: FF-2C R4 (owner sign-off 2026-07-19) re-derived it
to the exact published CPM soft-offer cap, $7.34/kW-month × 12, FERC ER24-1225 effective
2024-06-01. FFR-2C left it alone deliberately.

But the CPM soft-offer cap is **a price cap on CAISO's own administrative backstop
procurement** — not a market-clearing capacity price and not a net-CONE. So the model
prices CAISO capacity at *the administered price of CAISO's own backstop*, and then closes
two-thirds of its adequacy gap with an administrative backstop. The level is defensible and
cited; what the parameter cannot do is **vary**, and §2.2 shows that invariance — not the
level — is what binds. **A level re-anchor would not fix this**, which is the most
decision-relevant thing to say about candidate 10.

### 3.5 The exit-throughput asymmetry is present, and it lands differently here

CAISO retires **1,492.5 MW of `gas_st` in a single year** (2027: the class goes 2,858.8 →
34.8 MW, a **98.8 % single-year class exit**), plus 1,122 MW of nuclear in 2030. Exit is
uncapped; entry is capped. That is exactly FFR-3C's G-31 asymmetry, reproduced in CAISO.

**But it expresses differently than in ERCOT, and the difference is the whole point.** In
ERCOT — backstop OFF — the asymmetry produces a *collapse* (I12 to −1.5 %). In CAISO —
backstop ON — the same asymmetry is absorbed by step 6 and shows up as *administrative
over-build* instead. Same underlying defect, two different symptoms, because of one gate.
This is offered as a **structural observation about where G-31 surfaces**, not as a transfer
of ERCOT's attribution (rule 25).

---

## 4. What this evidence does NOT separate — stated plainly

Mirroring FFR-3C §5, because the charter asks for the honest boundary.

1. **The three causes are not additively decomposed.** 36.9 pp (lag) + a real 28.6 pp
   residual **does not equal** 65.5 %, and must not be presented as if it did. They are not
   orthogonal: unarming the lag changes both numerator and denominator *and* the price path
   that feeds the entry screen the following year. What is measured is each arm's total
   effect, not a variance decomposition.
2. **The base-year deficit is not attributed to a specific ledger input.** §1.3 quantifies
   the deficit (6,577 MW) and identifies three candidate conservatisms — hydro's
   non-dispatchable class factor on the whole fleet (1,943.6 MW), thermal UCAP against a
   PRM published on the CPUC **NQC** basis with CAISO absent from
   `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO` (1,735.8 MW), and CAISO's absence
   from `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO` while CPUC RA counts DR as supply
   (~2 GW). They sum to the same order as the deficit, **which proves nothing** — I have not
   verified CAISO's published NQC totals against the model's fleet, and doing so is a data
   intake, not a diagnosis. **No claim is made that CAISO's ledger is wrong**, only that
   these are the three places to look.
3. **The direction of the generic 0.18/0.16 VRE credit is unresolved.** CAISO's own
   slice-of-day accreditation for solar at ~22 GW penetration is plausibly *below* 0.18 for
   the net-peak slice, in which case the generic fallback is too **generous** and the true
   deficit is larger, not smaller. I did not measure it. Anyone reading §1.3 as a list of
   understatements is over-reading it.
4. **Why storage builds zero is not diagnosed.** There is no diagnostic sink for
   `apply_storage_new_entry` equivalent to `entry_screen_diagnostics`, so its per-tech value
   stack is unobservable in the artifact. Whether the arbitrage term, the capacity term, the
   degradation cost, or a cap is binding is **unknown** — only the zero is measured (§6, B-4).
5. **The sequencing blindness (§3.2) has no measured magnitude.** Isolating it requires
   changing the mechanism, which this charter forbids.
6. **n = 3 on the cross-ISO residual ordering.** §2.1's table is a consistency check across
   the three ISOs FC-2 row 4 has measured. PJM and MISO are unmeasured. It is not an
   identification, and per rule 25 it is not a verdict in any ISO but CAISO.
7. **Nothing here re-measures another ISO.** NYISO's 23.8 % and NEISO's 11.7 % are
   FFR-3A-2's numbers, quoted. Their causes are **not** diagnosed by this document, and
   CAISO's cause must not be assumed for them.

---

## 5. What a fix lane would need to charter

Written as a specification, not a recommendation to arm anything — the fix is a successor
lane with its own charter and its own owner decision.

1. **Adjudicate the ratio before adjudicating the model.** ~21 pp of the headline is the
   FC-2 row-4 denominator counting decisions at COD while counting the backstop at decision
   (§3.1, measured on the unmodified model). The lane's **first** deliverable is an owner
   ruling on which grain row 4 is supposed to measure. If the answer is decision-grain, the
   scorer changes and CAISO's number is 44.1 % — still FAIL, but a different problem.
   **This is the cheapest step and it needs no solve**, only the emitters
   `run_full_horizon.py` already writes. Doing it first stops any subsequent mechanism work
   being measured against a mis-specified instrument.
2. **The capacity-price invariance is the load-bearing structural question, and it cannot
   be closed with a parameter.** §2.2 shows a CAISO firm MW needs ≈1.5× the flat anchor to
   clear during an 18 pp shortfall, and that CAISO's price is invariant by construction
   (`demand_curve=()` — FFR-2E's proof). **There is no published CAISO demand curve to
   read**, because CAISO's RA is bilateral rather than an auction. So the lane faces a real
   fork, and it is an **owner decision, not a modelling choice**:
   * (a) accept that a bilateral-RA ISO has no scarcity-responsive capacity price and that
     an administrative backstop is therefore the *structurally correct* channel for CAISO —
     in which case **the rubric bar is what is wrong for this ISO**, and FC-2 row 4 needs a
     market-design-conditional band, defended on design and pre-registered; **or**
   * (b) identify a CAISO-specific scarcity-responsive RA price from a published CAISO/CPUC
     instrument (the CPM must-offer/soft-cap structure, the Central Procurement Entity
     framework, or the RA import price series) — a **data-intake deliverable with its own
     rule-13 admissibility test**, not a fitted slope.
   **Any curve shape borrowed from PJM/NEISO/MISO is a rule-25 violation and must be
   refused**, however well the arithmetic lines up. Rules 1/11/14: a residual closable only
   by an unidentified value is an open blocker, not a value to pick.
3. **The base-year ledger is a separable, cheaper lane that should probably go first.**
   47 % of the build closes a 2026 deficit that exists before any mechanism runs (§1.3).
   Three named registry entries carry it (§4 item 2), each is externally identified from a
   published CPUC/CAISO instrument, and **none requires a solve to investigate** — the
   deliverable is a reconciliation of the model's CAISO accredited ledger against the CPUC
   Net Qualifying Capacity report the hydro factor already cites. If the deficit is largely
   a basis artifact, the entry-side question shrinks by half before anyone touches it. The
   hydro registry's own comment already routes the per-plant RA-class intake this needs.
4. **The sequencing blindness must be adjudicated under rule 19, head-on, not routed
   around.** §3.2 shows the backstop's *budget* nets economic decisions but its *need* does
   not. Netting the pending pipeline into the firm gap is a small, parameter-free change —
   but it makes two mechanisms share one state, and whether that is *one* mechanism or *two*
   is the same question FFR-3C §6 item 2 raised for exit latency vs exit throughput. **A
   session that has not obtained that ruling must not net the pipeline.**
5. **The ratchet (§2.3) means ordering matters and must be tested jointly.** Because the
   backstop suppresses the energy margin that funds economic firm entry, fixing the
   capacity price *after* the backstop has already built 14 GW is measured against a price
   path the backstop itself flattened. Any price-side arm must be paired with a
   backstop-suppressed control, or it will under-read its own effect.
6. **Storage needs an instrument before it needs a lane** (§6, B-4). Zero storage additions
   in the ISO with the largest storage market is either a real economic finding or a defect,
   and **the artifact cannot currently tell them apart**. A `storage_screen_diagnostics`
   sink mirroring `entry_screen_diagnostics` is a few lines, decision-inert, and would
   settle it without a mechanism change.
7. **Test set: CAISO alone.** Every finding here is CAISO's. NYISO (23.8 %) and NEISO
   (11.7 %) are in the CAVEAT band with *undiagnosed* causes; a lane that assumes CAISO's
   cause for them would be doing exactly what rule 25 forbids. If the lane wants a second
   ISO, it must re-derive from that ISO's own market.

---

## 6. Open blockers

**Carried forward unchanged from FFR-3A / FFR-3C / FFR-3A-2** (none was in this charter to
fix): blocker 0 (the collapse itself), 1 (`data/clean` prerequisite — cost re-measured here
at 63 min + 2 min `uv sync`), 4 (optional-field cache-key hazard), 6 (pre-existing test
failures), 7 (`run_full_horizon` `run_config.json` — **now fixed upstream**, arm A wrote one),
10 (ledgers live at `<out-dir>/<ISO>/<cache_key>/`, not the out-dir root — confirmed again).

**New from this session:**

* **B-1. CLAUDE.md's capacity-evolution step 6 says "default off"; it resolves ON in five
  of six ISOs** (§0.1). The same stale claim appears in `scenarios.py`'s
  `market_design_retirement_floor` docstring, and `forecast_verdict.py` already needed a
  repair for the identical misreading. **Not fixed here** — a CLAUDE.md/spec edit belongs to
  the lane that owns the doc-sync, and this is a diagnosis charter. Three consumers have now
  been misled by it; the fourth will be too.
* **B-2. FC-2 row 4 compares two channels booked on different grains** (§3.1). Numerator
  books at decision; denominator books at COD. Worth ~21 pp of CAISO's headline on the
  unmodified model, and it will distort **every** ISO's row-4 number under armed D-2, in the
  same direction, by an amount that grows as the scoring window shortens.
* **B-3. `trajectory["storage_mw"]` is structurally always 0.0.** `_capacity_by_fuel`
  (`run_full_horizon.py:270–277`) builds its map from `ctx.fuel_types` plus explicit `wind`
  and `solar` keys; storage lives in a separate array and never appears, so
  `cap.get("storage", 0.0)` cannot be anything but zero. **CAISO's fleet does carry 8,000 MW
  of storage plus pumped storage** — the column is an instrument defect, not a measurement,
  and any successor reading a T1-F trajectory will read "no storage in this ISO." Recorded
  because that failure mode is silent. (`builds_storage_mw`, read from the ledger, *is*
  trustworthy — and it is genuinely 0.)
* **B-4. There is no storage-entry diagnostic sink.** `apply_economic_new_entry` has
  `entry_screen_diagnostics`; `apply_storage_new_entry` has no equivalent, so CAISO's zero
  storage additions cannot be attributed to any term or cap (§4 item 4).
* **B-5. CAISO is absent from three per-ISO adequacy registries that every other
  capacity-market ISO populates** — `RENEWABLE_ELCC_CURVES_BY_ISO`,
  `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`, and
  `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO` — so it takes the generic fallback on all
  three, in the ISO with the most elaborate published RA accreditation in the country. Each
  absence is individually defensible; the *pattern* is the blocker, and it sits underneath
  the base-year deficit (§1.3).

---

## 7. Mechanism matrix (rule 28)

Three cells were exercised. Updated in-session per duty (b);
`scripts/check_mechanism_matrix.py` passes.

| row | CAISO cell | action |
|---|---|---|
| `reserve_margin_backstop` | **K — unchanged** | note records the full attribution: 14,043.6 MW, 100 % `gas_ct` @ NP15, one unit/year, ladder-capped 2027-29 and need-limited 2030; 47 % closes an inherited base-year deficit |
| `entry_dampers` | **U → O** (open, measured, **not adjudicated**) | the two probe arms: commissioning lag −36.9 pp (dominant), growth ladder −0.84 pp (invariant, re-phases) — independently reproducing the MISO signature without transferring it |
| `capacity_market_clearing` | **K — unchanged** | note records the downstream consequence of the CAISO pricing no-op: the entry screen's capacity term is pinned at $82,795/MW-yr across reserve positions 0.84–0.98 |

No new `ScenarioConfig` field was added, so duty (c) does not apply. No run was registered
(these are forecast probe legs, not keeper bundles), so the duty-(b) registration half is
moot — the evidence is this document plus the four `results/ffr3h/` bundles.

**One instrument was added:** `run_full_horizon.py --entry-screen-diagnostics`, exposing the
existing RC-0C sink that `run_capacity_hindcast.py` has always had. It is decision-inert —
**verified in situ**, arm B is cell-for-cell identical to arm A — and it is not a mechanism,
so it takes no matrix row. It **does** move the cache key (the field is not in
`_CACHE_KEY_OPTIONAL_FIELDS`), which is documented at both the flag and the function.

---

## 8. What this session does NOT claim

* **It does not claim the 65.5 % is wrong.** It reproduces exactly, at the recorded key.
  What it claims is that ~21 pp of it is the *ratio's* booking convention rather than the
  model's behaviour, on the unmodified model, and that the remaining ~44 % (decision grain)
  is real.
* **It does not claim CAISO's adequacy ledger is wrong.** §1.3 identifies where to look and
  §4 item 2 states plainly that the arithmetic proves nothing without a CPUC NQC
  reconciliation nobody has done.
* **It does not recommend unarming either D-2 mechanism.** Arms C and D are labelled probes.
  Both mechanisms remain ARMED; owner decision D.1 stands.
* **It does not recommend a CAISO demand curve, a re-anchored net-CONE, or a widened
  rubric band.** §5 item 2 states the fork and leaves it with the owner, because every
  branch of it needs either a published instrument or a pre-registered design argument —
  neither of which a diagnosis session may supply.
* **It does not transfer anything across an ISO boundary.** ERCOT's 0.0 % keeps FFR-3C's
  attribution; MISO's `entry_rate_limits` result is cited as corroboration of an
  independently measured CAISO result, never as its source; NYISO's and NEISO's CAVEATs
  remain undiagnosed.
* **It does not re-score any rubric row.** FC-2 row 4 for CAISO is FAIL before this
  document and FAIL after it.

---

### Reproduction

```bash
uv sync                                   # ~2 min
uv run python scripts/regenerate_clean.py # ~63 min, 50/50 datatypes

# arm A — reproduction of the FFR-3A-2 measurement (resolved key e5822277b72184f6)
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ffr3h/caiso-A-repro

# arm B — same posture + the RC-0C entry-screen decomposition (decision-inert)
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --entry-screen-diagnostics --out-dir results/ffr3h/caiso-B-diag

# arms C and D — LABELLED PROBES, one D-2 mechanism unarmed each. Not promoted.
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --entry-screen-diagnostics --no-entry-commissioning-lag \
    --out-dir results/ffr3h/caiso-C-nolag
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --entry-screen-diagnostics --no-entry-rate-limits \
    --out-dir results/ffr3h/caiso-D-noladder
```

Arms A and B ran concurrently, then C and D (rule 12: two per-plant multi-zone invocations
at a time, years sequential within each). ≈8.5 min/solve-year with two concurrent on a
4-core/15 GB container; ≈21 min per arm, ≈43 min for both phases.
