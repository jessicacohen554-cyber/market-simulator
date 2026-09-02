# FINDING — capx D41: both CCS-retrofit fixed-cost legs re-identified onto the model's own ATB 2024 basis, and the 45Q-only retrofit stops clearing where carbon is zero

**Session:** D41 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d41-ccs-fixedcost`, the repair lane for D30's adjudication
(`FINDING-capx-d30-45q-pace-2026-09-02.md` §6, "what a repair is identified FROM"
items 1–2). **Date:** 2026-09-02 · **HEAD at launch:** `0a3d22c7`.
**ZERO SOLVES.** Every number in §4 is an analytic reconstruction of the screen's
own arithmetic (`model/capacity_evolution/ccs.py::apply_ccs_retrofit`) at committed
config values — the same reconstruction D30 §3 built, replicated leg-for-leg before
being re-run at the corrected values (§4.1 shows the replication). No golden
re-solve, no full-horizon campaign, no T1-H leg; the follow-on measurement needs are
routed in §7 and are the director's to sequence.

**Headline.** Both legs are repaired, both now carry a primary-source citation with a
stated dollar-year, and the consequence at screen grain is decisive rather than
marginal:

| | shipped | corrected | basis |
|---|---:|---:|---|
| `fixed_om_gas_cc_ccs` | 25.0 | **65.0** $/kW-yr, 2026$ | `fixed_om_gas_cc` 30.0 + the ATB 2024 capture-island Fixed-O&M increment (71.1 − 36.1 = 35.0) |
| ⇒ screen ΔFOM | **−$5,000**/MW-yr (a *saving*) | **+$35,000**/MW-yr (a *charge*) | |
| `ccs_retrofit_capex_kw` | 900.0 (dollar-year unstated, `needs-citation`) | **1521.4** $/kW, **2026$** | the ATB 2024 capture-island CAPEX increment (3104.7 − 1583.3) |

**At carbon = 0 — PJM and MISO — NO host class clears the retrofit bar in any year.**
The break-even unabated in-merit hours rise to 9,300–13,500 h against 8,760 available
(§4.3). The 3 GW/yr/ISO cap that D30 §4 measured binding in *every* conversion year of
*every* dispositioned ISO therefore stops binding in the two zero-carbon ISOs entirely:
the conversion count goes to zero, not to a smaller positive number. **Under RGGI —
NEISO and NYISO — retrofits still clear**, on the avoided-carbon leg, but the bar rises
from a 28–35 % capacity factor to 56–85 % (§4.4). Whether the cap still binds *there*
is **not determinable from committed artifacts** and is routed as a measurement (§7),
never inferred.

**Rule 28 statement, as the charter asked.** No `ScenarioConfig` field is added, no
default posture flips, no mechanism is armed, tested or refused, and **no cell verdict
moves in any ISO shard** — two costed parameters were re-identified onto a primary
source, which is a rule-23 act, not a rule-28 one. One matrix edit was nonetheless
required and made, to the BASE file only: §6.3.

**Rule 14 line, restated because the corridor moves.** The corrected legs make
retrofits less attractive, so the FC-5 CCS rows move toward AEO. **That is a
consequence and was never a target.** Nothing here is sized by corridor distance:
both values are the model's own committed ATB extract minus each other, asserted
exactly by a test, and the direction of the corridor was not consulted at any point in
the derivation. The FC-5 dispositions are a records lane's to re-author after the next
registered run, not this lane's.

---

## 1. Charter discipline

- **Read:** the D30 finding in full; `docs/parameter-citations.md` + the JSON registry
  behind it; the G-32 record (`fom-scarcity-defaults-flip-2026-07-07.md` and the
  Stage-2 protocol §4 DOF ledger that froze the 30.0 target); spec §5.6; the screen
  itself; `ff-1e-entry-cost-atb-wiring-2026-07.md` (the new-build basis fix whose
  retrofit half was left standing).
- **Did:** re-identified both values, cited them, cleared the `needs-citation` flags,
  wrote source-consistency tests, measured the screen-grain before/after, and
  discharged the cache-key and matrix bookkeeping the change turned out to carry.
- **Did NOT:** move any other retrofit-screen field (the 3 GW/yr cap, the 15-yr life
  floor, the split HR penalty and the Gulf-Coast `co2_transport_storage_cost` are
  D30 §5 rows 5/8/9/10 and stay exactly where they are); solve anything; touch a
  keeper, board, verdict or marker; re-author an FC-5 disposition; add a workflow.

## 2. Leg 1 — `fixed_om_gas_cc_ccs`, 25.0 → 65.0 $/kW-yr (2026$)

### 2.1 The derivation

```
fixed_om_gas_cc_ccs = fixed_om_gas_cc + (ATB gas_cc_ccs FOM − ATB gas_cc FOM)
                    = 30.0           + (71.1              − 36.1            )
                    = 65.0 $/kW-yr, constant 2026$
```

Both ATB terms are `constants.NEW_ENTRY_COSTS[...]["fom_per_kw_yr"]`, NREL ATB 2024
(v4.0.0 pin) Moderate case @2026, derived from the committed extract by
`scripts/data/derive_entry_costs_from_atb.py` on ATB's 2022$ → 2026$
`INFLATION_RATE` basis. Reproduced this session: `gas_cc 36.1 / gas_cc_ccs 71.1`.

**Rule 23 trigger is a DATA change, never a residual.** The re-derivation is caused by
the **G-32 ATB flip** (`docs/handoffs/fom-scarcity-defaults-flip-2026-07-07.md`,
2026-07-07), which moved the host `fixed_om_gas_cc` 12.0 → 30.0 onto the ATB 2024
basis and left this "host CC + capture island" figure at its pre-flip 25.0 — *below its
own host*. Nothing about any residual was consulted, and the screen's residual was not
examined until after both values were fixed.

### 2.2 Why ADDITIVE and not ratio-scaled

The two candidate constructions on the host's own value diverge materially
(30 + 35.0 = 65.0 vs 30 × 71.1/36.1 = 59.1), so the choice is stated rather than
assumed:

1. The capture island is **separate plant with its own absolute O&M**. A ratio scales
   the island's cost by the *host field's rounding*, which has no physical referent.
2. The island is **NEW plant at retrofit time**, so it carries a full new-build fixed
   cost, not a paid-off host's going-forward discount. Additive is the conservative-
   correct direction.
3. Additive makes the screen's ΔFOM — which is exactly `fixed_om_gas_cc_ccs −
   fixed_om_gas_cc` — equal the ATB island increment **independent of the host field's
   own basis and rounding**, which is the quantity the screen actually needs.

Pinned as a test in its own right (`test_island_increment_is_additive_not_ratio_scaled`).

### 2.3 Cross-source check on the increment, and the basis caveat stated plainly

Matched-configuration increments from the committed
`data/raw/new-build-cost-benchmarks/benchmarks_2026.csv` — the same verified,
URL-carrying file the entry-cost envelope already reads:

| source | dollar-yr | CCS FOM | matched CC FOM | increment | in 2026$ |
|---|---:|---:|---:|---:|---:|
| EIA / Sargent & Lundy Jan-2024 (Table 1-2, 1x1x1 single-shaft both rows) | 2023 | 24.78 | 15.51 | 9.27 | **9.90** |
| EIA AEO2026 EMM Table 3 (single-shaft both rows) | 2025 | 25.93 | 16.23 | 9.70 | **9.91** |
| NREL ATB 2024 Moderate @2026 | 2026 | 71.1 | 36.1 | — | **35.0** |

**Two honest readings, both recorded.** (a) The **sign is unanimous**: every published
basis makes the capture island an added cost of at least ~$10/kW-yr, so the shipped
−5.0 *saving* was outside all three — the defect is not a close call. (b) The ATB
increment is **3.5× the EIA/S&L one**, because ATB's whole NG Fixed-O&M basis runs
~2.2× the EIA/S&L line for the same technology (ATB `gas_cc` 36.1 vs S&L 15.51). This
is precisely why host and island must be read off **one** basis, and this field's host
is the ATB one (G-32 cited it as "NREL ATB 2024 Gas CC FOM"). Taking ATB is therefore
the internally consistent choice, and it is also the **strictest** on this leg — a
fact stated here rather than buried, because it means §4's PJM/MISO result is measured
at the harshest of the three admissible ΔFOM values. **§4.5 reports the screen outcome
at the EIA/S&L increment too**, so the sensitivity is visible and nobody has to take
the basis choice on trust.

**Routed, not done:** `fixed_om_gas_cc` = 30.0 is itself a *rounded* ATB reading (the
derived ATB value is 36.1 in 2026$; 30.0 is the G-32 Stage-2 target, dollar-year
unstated), and the whole `fixed_om_*` family shares that looseness. Reconciling the
family onto one stated basis is a real open item — see §7 item 3. D41 owns two fields
and did not widen.

## 3. Leg 2 — `ccs_retrofit_capex_kw`, 900.0 → 1521.4 $/kW (2026$)

### 3.1 The derivation

```
ccs_retrofit_capex_kw = ATB gas_cc_ccs CAPEX − ATB gas_cc CAPEX
                      = 3104.7               − 1583.3
                      = 1521.4 $/kW, constant 2026$   ← dollar-year now STATED
```

Same extract, same Moderate @2026 basis, same derive script. This is *the increment the
model's own new-build CCS screen already charges*, so after the repair the retrofit and
new-build screens price the capture island off one number instead of two.

### 3.2 What was wrong with 900.0 — three separate defects

1. **`needs-citation`.** The registry row carried the auto-harvested comment, no
   source, no `last_verified`.
2. **No dollar-year.** "NETL 2021, Sargent & Lundy 2022" spans two editions in two
   dollar bases; the number was uncomparable to anything.
3. **Inverted rationale.** The comment read *"Lower than greenfield (~$1400/kW)
   because host plant exists"*. A retrofit capture island costs **more** per kW than
   the greenfield increment — congested brownfield site, steam and flue-gas tie-ins,
   outage tie-in risk. The stated reason argued for the opposite sign of correction to
   the one the evidence supports.

At 900 the value was **59 % of the increment the entry screen charges** — the same
"≈ $900/kW increment makes the capture island look nearly free" defect FF-1E repaired
for new-build and explicitly recorded the retrofit screen as "unaffected" by.

### 3.3 THIS IS A FLOOR, AND IT IS LABELLED ONE

All three published bases are **greenfield** increments. Matched-configuration
cross-check, same CSV:

| source | dollar-yr | CCS capex | matched CC capex | increment | in 2026$ |
|---|---:|---:|---:|---:|---:|
| EIA / S&L Jan-2024 (both 1x1x1 single-shaft) | 2023 | 2365 | 921 | 1444 | **1541** |
| EIA AEO2026 EMM Table 3 (both single-shaft) | 2025 | 2824 | 1086 | 1738 | **1776** |
| NREL ATB 2024 Moderate @2026 | 2026 | 3104.7 | 1583.3 | — | **1521.4** |

ATB is the **lowest of the three**, which is why it is the floor rather than a
midpoint. A retrofit-specific TPC — D30 §6 item 2's NETL "Cost and Performance of
Retrofitting NGCC Units for Carbon Capture" series, which is not in-repo and which a
`code`-profile lane cannot fetch — can only **raise** this number. **The screen
therefore stays biased TOWARD retrofitting after the repair, never against it**, and
§4's "nothing clears at carbon = 0" result is a *lower bound* on the correction, not an
overshoot. Sourcing the premium is §7 item 2.

### 3.4 What the repair closes as a side-effect

D30 §4 measured the sharpest single artifact of the defect in the NEISO golden: the
entry screen builds a 1,000 MW unabated `gas_cc_h_class_Central` in 2031 having
**rejected** its own CCS variant at the $1,521/kW increment, then the retrofit screen
converts that same unit in 2032 at a learning-adjusted $621/kW. Two cost bases
arbitraging each other inside one model year. Both screens now start from 1521.4, so
the *basis* gap closes entirely; what remains is only the Wright-curve treatment
(2032 retrofit base 1049.6 vs the unlearned 1521.4 increment), which is a separate and
legitimate mechanism, not a basis discrepancy.

## 4. Screen-grain measurement (reconstruction only, zero solves)

### 4.1 Replication first — the reconstruction is D30's, unchanged

Before re-running at corrected values the reconstruction reproduces **every** D30 §3
number exactly: PJM 2028 per-MWh offsets H-class **+11.34** / F-class **+12.57** /
older-CC **+15.03**; NEISO 2028 F-class **+22.48** and 2030 **+23.31**; the
learning-adjusted capex path **783.0 / 710.2 / 669.6 / 641.8 / 620.9** $/kW for
2028–2032; and all four §3.3 sensitivity rows (F-class PJM 2028 payback at H = 8,760 =
**7.1 yr**, break-even H = **5,045**; ΔFOM at the ATB increment **8,395**; capex at the
ATB increment **8,818**; both legs **12,167**). The corrected-value rows below are the
same arithmetic with the two constants moved, so any disagreement with D30 is a real
effect and not a different model.

### 4.2 Per-leg attribution — PJM 2028, F-class host (hr 6.7, carbon 0)

| legs | capex $/kW (2028, learned) | ΔFOM $/MW-yr | uplift @ H=8760 | payback @ H=8760 | break-even H for a 12-yr payback |
|---|---:|---:|---:|---:|---:|
| shipped (25 / 900) | 783.0 | −5,000 | 109,610 | 7.1 yr | 5,045 |
| FOM leg only (65 / 900) | 783.0 | +35,000 | 69,610 | 11.2 yr | 8,395 |
| capex leg only (25 / 1521.4) | 1,323.6 | −5,000 | 109,610 | **never** | 8,818 |
| **both corrected (65 / 1521.4)** | **1,323.6** | **+35,000** | **69,610** | **never** | **12,167** |

**Either leg alone very nearly closes PJM's headroom on its own** (8,395 h and 8,818 h
against 8,760 available); together they put it far out of reach. The two defects were
not independently small.

### 4.3 Which units still clear — the zero-carbon ISOs (PJM, MISO)

Break-even unabated in-merit hours for a 12-year payback, as hours and as the implied
capacity factor:

| ISO · year | host | shipped | corrected |
|---|---|---:|---:|
| PJM 2028 | H-class (6.3) | 5,591 h (64 %) | **13,485 h (154 %)** |
| PJM 2028 | F-class (6.7) | 5,045 h (58 %) | **12,167 h (139 %)** |
| PJM 2028 | older CC (7.5) | 4,221 h (48 %) | **10,178 h (116 %)** |
| PJM 2030 | F-class | 4,486 h (51 %) | 11,421 h (130 %) |
| MISO 2028 | F-class | 4,929 h (56 %) | 11,886 h (136 %) |
| MISO 2030 | older CC | 3,655 h (42 %) | 9,304 h (106 %) |

**Every corrected row exceeds 8,760 h.** A year has 8,760 hours, so **no PJM or MISO
host of any class clears the bar in any year at the corrected values** — the payback at
the ceiling (H = 8,760, the theoretical maximum) is already `never`, because the capex
exceeds twelve years of in-window uplift and the post-window uplift is negative
(−173,520 $/MW-yr at the ceiling). **Answer to the cap question in the two zero-carbon
ISOs: the cap does NOT bind — it is not reached at all.** §45Q alone, at $85/t on a
0.344 t/MWh captured basis, can no longer pay for a correctly-costed capture island
where there is no carbon price.

### 4.4 The RGGI ISOs (NEISO, NYISO) — retrofits survive, on a much higher bar

The avoided-carbon leg adds ~$10–12/MWh in 2028–2030, and retrofits still clear:

| ISO · year | host | shipped | corrected |
|---|---|---:|---:|
| NEISO 2028 | H-class | 3,070 h (35 %) | **7,404 h (85 %)** |
| NEISO 2028 | F-class | 2,821 h (32 %) | **6,804 h (78 %)** |
| NEISO 2028 | older CC | 2,428 h (28 %) | **5,856 h (67 %)** |
| NEISO 2030 | F-class | 2,294 h (26 %) | 5,840 h (67 %) |
| NYISO 2028 | F-class | 2,767 h (32 %) | 6,673 h (76 %) |
| NYISO 2030 | older CC | 1,941 h (22 %) | 4,942 h (56 %) |

The qualifying set narrows from "essentially any CC that runs at all" to
"genuinely near-baseload CCs". **Whether the 3 GW/yr cap still binds here is an
empirical question this lane cannot answer** — it depends on the utilization
distribution of the NEISO/NYISO CC fleets, and D30 §8 items 2–3 already record why:
no forecast bundle commits hourly prices, and a `code`-profile lane has no fleet data.
D30 §4 measured 80–84 % of those (small, ~11 GW) fleets converting by 2030 with the cap
binding; a 56–85 % CF requirement plainly cuts into that, but by how much is a
measurement, not an inference. Routed in §7 item 1.

*(NEISO/NYISO carbon is the endogenous RGGI program price, pinned in the reconstruction
at the values D30 §2/§3.1 read off the committed bundles — $29.83/t 2028, $34.15/t 2030
— because reproducing it requires a solve. The PJM/MISO carbon-zero result, which is
the decisive one, needs no such pin.)*

### 4.5 Sensitivity to the ΔFOM basis choice (§2.3(b), stated so it is checkable)

At the **EIA/S&L–AEO2026** increment (~9.9 $/kW-yr, i.e. `fixed_om_gas_cc_ccs` ≈ 39.9
and ΔFOM ≈ +$9,900/MW-yr) instead of the ATB 35.0, the corrected PJM 2028 F-class
break-even H is **10,065 h** rather than 12,167 h (115 % of the year; the
AEO2026 increment gives 10,067 h — the two are indistinguishable). **Still above 8,760** — so the
PJM/MISO "nothing clears" result holds on *every* published FOM basis, and is driven
primarily by the capex leg. The basis choice changes the margin of the conclusion, not
the conclusion.

## 5. Deliverables landed

| what | where |
|---|---|
| both values + full cited derivations, dollar-years stated | `src/market_sim/config/scenarios.py` (the two field comments) |
| registry citations, `needs-citation` cleared on both | `frontend/data/parameters.json` → rendered `docs/parameter-citations.md` |
| source-consistency + direction tests (8, all passing) | `tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py` |
| cache-key advance, cause blocks | `tests/regression/test_persisted_identity.py` (both pins) |
| cache-epoch record | `src/market_sim/results/cache.py` (epoch 2026-09-02) |
| matrix base-row def/note (no cell verdict moved) | `docs/codebase-site/data/mechanism-matrix.js`, row `ccs_retrofit_screen` |

The tests are deliberately a mix of **exact pins** (the value equals the derivation) and
**physics inequalities** stated so they keep biting under a future ATB edition:
`fixed_om_gas_cc_ccs > fixed_om_gas_cc` (a host-plus-island cost can never sit below its
host — the invariant that would have caught G-32 at the G-32 commit), and
`ccs_retrofit_capex_kw >= the ATB capture-island increment` (the floor property of
§3.3).

## 6. Bookkeeping the charter did not anticipate — reported in full

### 6.1 Rule 28 is NOT triggered, as the charter said

No field added, no default posture flipped, no mechanism armed/tested/refused, no ISO
shard cell verdict moved. Two costed parameters moved onto a primary source: rule 23.

### 6.2 BUT the change re-keys every config in the program — escalated and authorized

The charter's conditional ("if either value is actually a registered cache-key field
whose change re-keys configs, STOP and report the blast radius first") fired **in
substance though not in letter**, and was escalated before anything landed. Neither
field is a `_CACHE_KEY_OPTIONAL_FIELDS` member — they are *unregistered*, which is
strictly worse, not better: an unregistered field is hashed **at every value**, so a
value change moves the key unconditionally and registration is not an available remedy.

**Measured blast radius:**

- default forecast key `603c2498bf71d21d` → **`cedadc285f8603b9`**
- bare backcast key `e027bc248c93c835` → **`e006dfd7cef8bedd`**
- ERCOT lane poles: D12-A armed `68a207068509f2b0` → `6bb61037c072502d`, Stage-B armed
  `8d9ef77edb3e44cb` → `71f20d708a810f0a`, pre-Stage-B `062d440558103f81` →
  `ddeb8a9aaffe1f6b` (moved together, by the same delta — every relation those tests
  pin still holds, and the armings themselves are untouched)
- 22 pinned-literal assertion sites across 20 test files, all advanced
- every on-disk `results/<ISO>/<key>/` bundle at an old key orphans: a one-time cache
  MISS, never a wrong answer, since the key moved rather than colliding

**Behaviour moves in forecast years ≥ 2028 only — which is the repair.** The two fields
have exactly two consumers, both inside forecast-mode capacity evolution:
`apply_ccs_retrofit` (year-gated 2028) and the `_THERMAL_FOM` lookup in
`retirements.py`, which reaches `fixed_om_gas_cc_ccs` only for a `gas_cc_ccs` unit.
**Backcast is byte-identical**: no backcast year reaches 2028 and no measured backcast
fleet contains a `gas_cc_ccs` unit, so dispatch, scores and every other `run_config.json`
value are unmoved. **No keeper, sidecar, determination or dashboard row is affected** —
committed artifacts are files, not cache lookups.

Re-pinning is the **sanctioned** route here, not the forbidden one: `results/cache.py`'s
own policy distinguishes a "key advance" (a change that legitimately re-keys the default
config → record it at `PINNED_DEFAULT_CACHE_KEY` with a dated cause block) from the
wrong fix it warns against (re-pinning to accept a cache orphaned by an unregistered
**new field** that is cache-neutral at its default). This is the former. **Precedent:
G-32 itself moved this pin when it flipped `fixed_om_gas_cc` 12 → 30.** Both prior
advances carried an owner authorization; so does this one — the blast radius above was
put to the owner before any of it landed, and the answer was to land it and advance the
pins.

### 6.3 One matrix edit was required, and only the base file was touched

The rule-28(c) shared ratchet flagged both fields as "ARMED on the keeper with no matrix
row" on **all six ISOs** the moment the defaults moved. That is a **false positive by
construction**: every keeper's `run_config.json` records the then-current default of
every field, so any default change makes each keeper read "armed", and here both fields
are unreachable in a backcast anyway. Rather than take an exemption (an entry in
`SHARED_CENSUS_EXCLUSIONS` is an exemption from a rule-28(c) duty) or regress a ratchet
that currently stands at zero gaps, the two fields are **named in the existing
`ccs_retrofit_screen` row's `def`/`note`** — the checker's own first-listed remedy, and
a genuine improvement: the retrofit screen's row now names the cost parameters it prices
against. **No ISO shard was edited and no cell verdict moved**; the note says so
explicitly. Ratchet green, at zero, on all six.

### 6.4 Two unrelated registry rows came along

Re-running `scripts/generate_parameter_registry.py` (the single writer of
`docs/parameter-citations.md`) picked up two `auto-generated` rows other lanes added
without regenerating — `scenario.unit_outage_mixed_gas_routing` and
`adequacy_internal_supply_accounting_ratio_by_iso.MISO`. Pre-existing drift, not this
lane's; kept because hand-editing generated output is worse.

## 7. Routed follow-on — which registered runs are now stale on this axis

**Nothing below was run here, and nothing below should be run without the director
sequencing it.** Listed so the sequencing decision has the inputs.

1. **Stale on this axis — every forecast bundle whose horizon reaches 2028.** By D30 §4's
   own census that is at minimum: `results/ff-t1f-s6-pjm` (PJM), `results/ff-t1f-s123/verify`
   (MISO, and provisional pending D31), `results/ff-t1f-extcap` (NYISO),
   `results/ff-t1f-s4b-ara` (NEISO), and `results/ff-t3-neiso-golden/bau` plus its four
   FC-6 arm summaries. Every one of them carries retrofit conversions decided at
   ΔFOM = −$5,000/MW-yr and capex 900 — i.e. at the two legs now repaired. The **PJM and
   MISO** rows are the sharpest: §4.3 says their conversions go to **zero**, so those
   bundles' CCS fleets are wrong in kind, not in degree.
   **Not stale:** every backcast bundle and every keeper (§6.2 — byte-identical), and
   `results/hindcast/miso-2021-2025-realized-t1h-d27` and its siblings (T1-H windows end
   at 2025; D30 verified zero retrofits in every ledger by construction).
2. **The one measurement this lane could not make: does the cap still bind in NEISO/NYISO
   at the corrected values?** §4.4 raises the bar to a 56–85 % CF but cannot resolve the
   fleet's utilization distribution from committed artifacts. This needs a solve, and it
   is the single question that decides whether the corrected screen produces "much less
   CCS" or "essentially none" outside RGGI.
3. **`fixed_om_gas_cc` and the rest of the `fixed_om_*` family carry the same looseness
   this lane just repaired one level up** — 30.0 is a *rounded* ATB reading with no stated
   dollar-year (the derived ATB value is 36.1 in 2026$), and `fixed_om_gas_ct` 21.0 /
   `fixed_om_coal` 45.0 / `fixed_om_gas_st` 35.0 / `fixed_om_oil` 25.0 /
   `fixed_om_nuclear` 130.0 are in the same state, three of them still flagged
   `needs-citation`. §2.3(b) shows the basis question is not cosmetic: the ATB and
   EIA/S&L FOM bases differ by ~2.2× for the same technology. A family-wide
   reconciliation onto one stated basis is a coherent next lane; D41 owned two fields
   and did not widen.
4. **A retrofit-specific capex premium over the §3.3 floor** — the NETL NGCC-retrofit
   series. Needs a data-profile lane that can fetch it. It can only raise 1521.4, so it
   strengthens §4's result and cannot reverse it.
5. **D30 §5's remaining rows are untouched and still open**: the uncited 3 GW/yr cap
   (row 9 — note that in PJM/MISO it is now moot, since nothing reaches it), the split
   HR penalty 0.12 vs 1.16 from one NETL case (row 5), the Gulf-Coast
   `co2_transport_storage_cost` applied in New England and New York (row 8), and the
   un-persisted `retrofit_log` decomposition (row/§8 item 1) that forced both D30 and
   this lane to reconstruct margins analytically instead of reading them.

---

*Produced 2026-09-02 (D41, zero solves). Reconstruction script in the session
scratchpad; every input it reads is named in §2–§4 and is a committed artifact. The
cache-key advance in §6.2 was escalated to the owner before it landed and authorized.
No keeper, board, verdict or marker was touched; no FC-5 disposition was re-authored.*
