# FINDING — capx D4-I3: the ERCOT I3 scarcity-slack invariant (half scope)

**Lane:** capx D4-I3 · **Model:** Opus · **Branch:** `claude/capx-d4i3-ercot-slack`
**Charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` §D4-I3 (r#21) ·
ledger `docs/handoffs/capx-director-ledger-2026-08.md` §6 / §1153
**Binding prior:** `docs/forecast-readiness-audit-2026-07.md` FR-6
**Date:** 2026-08-31 · **Zero-solve.** Every number below is read from a committed artifact.

**SCOPE BOUNDARY.** Card Y is signed **Y-C** (hold open), so this lane owns the **I3
scarcity-slack invariant half ONLY**. The net-revenue half is HELD and is not touched,
measured, or re-opened anywhere in this finding. No mechanism was tested; rule 28 duty (a)
only (the ERCOT shard was read, not written — see §7).

---

## 0. Headline

1. **ERCOT I3 slack is an under-build signature, and the committed record proves it
   quantitatively.** Across the eleven committed ERCOT T1-H records, 2023 slack is
   **monotone in the year's total added GW** — zero at ≥ 48.0 GW, 0.01 % at 39.9 GW,
   0.07 % at 27.8 GW — and monotone in the resulting reserve margin. It is not an entry-timing
   artifact and not a curve artifact at first order (§2).
2. **The newly-armed D12-A pair makes I3 strictly worse, and that is the correct behaviour.**
   The same-session `d12c` A/B measures 2023 slack **0.01 % → 0.07 %** (≈ 7×) and opens a
   **second breach year** (2024, 0.02 %, where the control has none), because both levers
   remove build volume by design. Pre-declared expectation for D6 in §4.
3. **No committed ERCOT posture clears I3 and the I12 reserve-margin band together.** Every
   arm that clears I3 does so by over-building into a 2025 margin of 38.8–40.4 % against a
   [13.8 %, 28.7 %] band. I3 and I12 are one phenomenon in ERCOT, not two (§3).
4. **Two committed records of one cache key disagree on I3.** Five records share key
   `28cef3500ec1fd9e`; the 2026-08-22 one reports 2023 slack 0.02 % / LW $100.4, the four
   2026-08-30/31 ones report 0.01 % / $86.1, and their scored CO2 differs too — three
   independent quantities, so not a rounding boundary. Either the key carried two solves (the
   hazard `results/cache.py` documents) or the scorer changed; **not separable zero-solve, and
   no cause is asserted.** Either way: **an ERCOT I3 magnitude is comparable only within a
   solve vintage**, so FR-6's "0.01–0.03 %" must not be differenced against a 2026-08-30
   record. The A/B deltas above are unaffected. Routed as R-5 (§5.1).
5. **The committed I3 record carries no MW, no hours and no GWh** — the instrument emits
   `% of load` only, so the charter's "slack MW/hours by year" is **not obtainable zero-solve**
   for T1-H. Instrument gap, routed as R-4 (§5.2, §6).
6. **FR-6's cause now has a code home** (§6.0): a design-intent block at the
   `resolve_reserve_margin_build_enabled` energy-only seam. Comment only, zero behaviour change.

---

## 1. What the invariant actually measures

`scripts/check_forecast_invariants.py::check_i3_unserved_dump` flags a year when
`slack_energy / demand_energy > 1e-4` (0.01 % of load) and emits
`"<year>: slack {frac:.2%} of load"`. `slack` is the LP's load-slack column — bounded
`0 <= Slack <= inf` in `model/lp/bounds.py::build_variable_bounds` at the `_slack_off` seam and priced
at `voll` in `model/lp/costs.py::build_cost_vector`.

*FR-6 line-number drift, for citation hygiene:* FR-6 cites `lp/bounds.py:193-194` and
`lp/costs.py:127-134`. At this HEAD the seams are `bounds.py:195-196` and `costs.py:159-166`.
Same seams, same semantics; cite them by function + `_slack_off` rather than by line.

The design-intent half of FR-6 is exact and re-verified here: `adequacy.py`
`resolve_reserve_margin_build_enabled` returns `False` for energy-only ERCOT
(`MARKET_DESIGN[iso].capacity_market` is false) *by design* — the docstring's own rule-1
rationale is that a force-build backstop would manufacture firm MW an energy-only market never
procures. Combined with one-pass evolution (rule 10 `[R-ONE-PASS]`), an under-built ERCOT year
has **no corrective**, and the hourly balance residual leaves through the only unbounded
column that can absorb it. **I3 is therefore a capacity-evolution signal read off the
dispatch.** What FR-6 correctly complained about is that this chain lived only in memos — §6.0
fixes that.

---

## 2. THE BREACH SET — eleven committed ERCOT T1-H records

Sources: `frontend/data/hindcast/ercot-2021-2025-realized-t1h-<arm>.json` (the `invariants`
block) and each bundle's `results/hindcast/.../score.json` (`additions.model_total_gw`).
All eleven: `--year 2021 2023 2024 2025`, 2022 bridged, `scored_years` 2023–2025, vintage
2020-12-31, `variant=realized`. Sorted by total build.

| record (`…-t1h-`) | cache key | built GW | 2023 slack | 2024 slack | 2023 RM | 2024 RM | 2025 RM | I3 |
|---|---|---|---|---|---|---|---|---|
| `disarm` | `2eab2146` | **54.000** | — | — | in band | in band | 40.2 % ↑ | **PASS** |
| `c1joint-arm` | `0490af52` | **48.450** | — | — | 14.0 % | in band | 38.8 % ↑ | **PASS** |
| `fwdexp` | `a2dc52ff` | **48.000** | — | — | in band | in band | 40.4 % ↑ | **PASS** |
| `refresh` | `28cef350` | 39.908 | 0.02 % | — | 8.5 % | in band | in band | FAIL |
| `d11r-control` | `28cef350` | 39.908 | 0.01 % | — | 8.5 % | in band | in band | FAIL |
| `d12c-control` | `28cef350` | 39.908 | 0.01 % | — | 8.5 % | in band | in band | FAIL |
| `capentry-control` | `28cef350` | 39.908 | 0.01 % | — | 8.5 % | in band | in band | FAIL |
| `c1joint-control` | `28cef350` | 39.908 | 0.01 % | — | 8.5 % | in band | in band | FAIL |
| `capentry-repair` | `dcbd3b95` | 39.908 | **0.04 %** | — | 7.0 % | 13.1 % | in band | FAIL |
| `d11r-exhaustion` | `cc7bbe11` | **34.211** | **0.06 %** | — | 6.3 % | 11.6 % | in band | FAIL |
| `d12c-armed` | `f061b264` | **27.837** | **0.07 %** | **0.02 %** | 6.1 % | 6.8 % | in band | FAIL |

Gate = 0.01 % of load. "in band" = inside I12's [13.8 %, 28.7 %]; "↑" = out of band **high**.
Actual ERCOT 2021-2025 additions, from the same score files: **55.436 GW**. Modelled
retirements are **0.000 GW in every one of the eleven** against 2.294 GW actual.

**No arm breaches 2025.** Every breach is 2023, plus 2024 in `d12c-armed` alone.

### 2.1 The arm/control levers behind each row

From each bundle's committed `run_config.json` → `scenario_config` (17 fields differ across
the eleven; `<absent>` fields are later schema additions, not settings). The substantive deltas:

| record | delta vs the registered control posture |
|---|---|
| `refresh`, `d11r-control`, `d12c-control`, `capentry-control`, `c1joint-control` | (control) |
| `disarm` | `entry_lookahead_reprice` **False** |
| `fwdexp` | `entry_forward_expectation_signal` **True** |
| `d11r-exhaustion` | `entry_margin_exhaustion` **True** |
| `d12c-armed` | `entry_margin_exhaustion` **True** + `entry_forward_reserve_leg` **True** |
| `capentry-repair` | `storage_entry_availability_gate` **True** + `storage_entry_cost_normalized_rank` **True** |
| `c1joint-arm` | `entry_lookahead_reprice` **False** + `entry_margin_exhaustion` **True** |

### 2.2 Attribution — under-build vs entry-timing vs curve

**(a) Under-build (entry VOLUME) is the first-order cause, and it is measured, not inferred.**
Nine distinct build levels, one monotone response: slack is 0 at 54.0 / 48.5 / 48.0 GW, 0.01 %
at 39.9 GW, 0.04 % at 39.9 GW (see (b)), 0.06 % at 34.2 GW, 0.07 % at 27.8 GW. The onset sits
between 48.0 GW (clean) and 39.9 GW (0.01 %). The same monotonicity holds against reserve
margin — 14.0 % clean, 8.5 % → 0.01 %, 7.0 % → 0.04 %, 6.3 % → 0.06 %, 6.1 % → 0.07 % — and
holds in 2024 independently: 13.1 % and 11.6 % are clean, 6.8 % breaches. **Retirements
contribute nothing**: every arm retires 0.000 GW, so the deficit is entirely entry-side.

**(b) Entry-timing / duration is separable, and the `capentry` pair isolates it exactly.**
`capentry-repair` builds the **identical 39.908 GW with an identical per-tech split**
(wind 0.350 / solar 17.987 / gas_cc 9.000 / gas_ct 7.571 / storage 5.000 GW) as its control,
yet its 2023 slack is **0.04 % against the control's 0.01 %** — 4× on zero MW of difference.
Per that lane's own ledger note (`invariant-failures.json` `capentry_note`) the difference is
storage **duration**: a 5.6 h li-ion fleet covers fewer 2023 scarcity hours than the control's
64 h build. Since `score.json.additions` is GW of *power* only, the duration mix is invisible
to the volume attribution above — which is precisely why this pair is the clean isolate.
**≈ 0.03 pp of the 2023 breach is a within-MW timing/duration effect, not a volume effect.**

**(c) Curve shape is NOT separable from committed artifacts, and this finding does not claim
it is.** The I3 record has no hourly resolution (§5.2). The only curve-adjacent committed
signal is I14's load-weighted price, and it moves monotonically with slack —
$86.1 (0.01 %) → $100.4 (0.02 %) → $138.4 (0.04 %) → $158.9 (0.06 %) → $168.7 (0.07 %),
against a CC-implied MC of $23.9 — which is exactly what VOLL hours entering a load-weighted
mean would do. **I14 therefore cannot discriminate curve shape from scarcity volume**, and
no committed artifact can. Routed as R-4.

---

## 3. I3 and I12 are one phenomenon in ERCOT

Every arm that clears I3 clears it by over-building: `disarm` 40.2 %, `fwdexp` 40.4 %,
`c1joint-arm` 38.8 % 2025 reserve margin, against an I12 band top of 28.7 %. Every arm inside
the band in 2025 breaches I3 in 2023. **In the committed set there is no ERCOT entry-screen
setting that lands inside the reserve-margin band in all years**, and the model's build
(27.8–54.0 GW) brackets the actual 55.4 GW only from below.

Consequence for the board and for any future repair: **treating I3 and I12 as two independent
FC-1 failures over-counts the defect.** They are the low and high sides of one mis-scaled entry
volume rule. A repair that closes I3 by building more will push I12 out the top; one that closes
I12's high side will re-open I3. This is a rule 19 `[R-ONE-MECH]` observation — one phenomenon,
one mechanism — and it is the single most useful thing this measurement says about where the
ERCOT forecast repair actually lives.

---

## 4. PRE-DECLARED post-arming expectation (NOT a measurement)

**Status: ex-ante prediction, written before any post-arming solve exists. The measurement
belongs to the next chartered ERCOT T1-H run (D6 or a director decision). No solve in this
lane.** Basis: the committed `d12c` A/B (`d12c-armed` vs `d12c-control`, both scored in one
session at `bf5e08f50f0d`, so the pair is internally consistent — see §5.1) plus the two
fields' own citation blocks in `config/scenarios.py`.

`entry_margin_exhaustion` + `entry_forward_reserve_leg` are armed as **ERCOT forecast defaults**
in `config/iso_configs.py` (owner ruling Q15, 2026-08-30; the D12-A citation block), so the next
T1-H at the registered posture picks up both.

**Mechanism — why both levers can only reduce build volume.** The exhaustion rule replaces
bang-bang ("clear the screen by $1, build the full cap") with "build until the screen's own
repriced margin is exhausted" — its own offline probe measured terminal RM 18.7 % vs the
shipped 25.2 %. The forward reserve leg removes the realized-ORDC revenue *floor* that the
D12 finding measured as the **sole driver** of the shipped 6 GW gas builds (entering-2024
forward margins are negative: gas_cc −$10.7k, gas_ct −$42.7k/MW-yr). Neither can add capacity.

**Pre-declaration, D6's ERCOT T1-H, at the registered posture with the pair armed:**

| # | prediction | committed basis |
|---|---|---|
| **P-1** | I3 **FAILs**, and fails **worse than the control** — direction is not in doubt. | both levers strictly reduce build volume |
| **P-2** | 2023 slack lands near **0.07 % of load** (≈ 7× the control's 0.01 %, ≈ 7× the gate). | `d12c-armed` measured |
| **P-3** | A **second breach year opens at 2024**, near **0.02 %**, where the control is clean. | `d12c-armed` measured |
| **P-4** | **2025 stays clean.** No committed arm breaches 2025 at any build level. | all eleven records |
| **P-5** | Total build falls to ≈ **27.8 GW** (from 39.9 GW), and 2023/2024 reserve margin to ≈ **6.1 % / 6.8 %**. | `d12c-armed` measured |
| **P-6** | The composition is **super-additive** vs the exhaustion leg alone: exhaustion-only leaves 2024 clean at RM 11.6 %; adding the reserve leg collapses 2024 to 6.8 % and opens the breach. | `d11r-exhaustion` vs `d12c-armed` |
| **P-7** | I14 2023 LW price rises to ≈ **$168.7** (control $86.1), tracking the added VOLL hours. | `d12c-armed` measured |
| **P-8** | On the T1-F horizon the 2027-2030 breach should **widen** from the live 0.08/0.14/0.13/0.41 % by the same mechanism. **This leg has NO bracketing A/B** — flagged as an unbracketed prediction, not a derived one. | mechanism only |

**How to read a confirming result — this is the part that matters.** A worse I3 under the armed
pair is **not a regression and must not be repaired by re-disarming.** Rule 1 `[R-STRUCT]`:
both levers are structurally-motivated corrections (one removes a bang-bang volume artifact,
the other removes a cross-basis phantom revenue floor), and rule 14 `[R-ACCURATE]` applies in
its exact intended sense — the more faithful mechanism making a gate worse is the discovered
bug, not the mechanism. What the armed pair does is stop 6 GW of gas the forward story never
supported from papering over an under-build; **I3 rising is that under-build becoming visible.**
The admissible response is to find why the screen under-builds, not to restore the phantom.

**Falsifiers (any of these contradicts this pre-declaration and is reportable as such):**
- **F-1** — I3 reads **PASS**, or slack ≤ the control's. First check the run's own
  `run_config.json` for `entry_margin_exhaustion` / `entry_forward_reserve_leg`; if both are
  `True`, the contradiction is real and P-1 is wrong.
- **F-2** — a **2025** breach appears. Outside everything the committed set predicts.
- **F-3** — 2023 slack exceeds ~0.15 % or falls below the control. Outside the measured spread.
- **F-4** — total build differs materially from ≈ 27.8 GW while the slack still matches P-2/P-3
  — that would break the volume↔slack monotonicity of §2.2(a), which is the load-bearing claim
  of this whole finding.

---

## 5. Two measurement-integrity findings

### 5.1 One cache key, two disagreeing records — ERCOT I3 is only comparable within a vintage

Five committed records share cache key **`28cef3500ec1fd9e`** (`refresh`, `d11r-control`,
`d12c-control`, `capentry-control`, `c1joint-control`) and their copied
`screen_signal_diag_*.npz` are **byte-identical** (sha256 `55d2534930eb4032…` on
`2023_for_2024`, all five). Yet:

| | `refresh` (2026-08-22, `8084b135ed8d`) | the four (2026-08-30/31) |
|---|---|---|
| I3 2023 slack | **0.02 %** of load | **0.01 %** of load |
| I14 2023 LW price | **$100.4** | **$86.1** |
| `score.json` co2 model 2023 | 167,517,105.0 t | 167,539,465.4 t |
| co2 model 2024 / 2025 | 155,434,439.5 / 188,202,977.8 t | 155,434,858.9 / 188,208,784.6 t |

Three independent quantities differ, so **this is not a display-rounding boundary**: something
real separates the two records. The CO2 deltas are tiny (+0.013 % / +0.0003 % / +0.003 %) while
the slack halves and the LW price moves 14 % — the signature of a handful of VOLL hours moving,
which is exactly the metric this lane owns. The four 2026-08-30/31 records are mutually
byte-identical apart from `generated_utc` (and `co2.actual_basis`, a scorer-field addition), so
the later vintage is self-consistent and `refresh` is the outlier.

**On the byte-identical npz — a qualifier that matters.** It does *not* by itself prove the two
dispatches were the same. `screen_signal_diag_*.npz` is a **screen-stage reconstruction**: its
members are `net_load_mw`, `top_of_stack_mw`, `installed_headroom_mw`, `mc_sorted_usd_mwh`,
`cap_sorted_mean_mw`, `price_base_usd_mwh`, `adder_usd_mwh` — a merit-stack rebuild from fleet
and net load, not the LP's realized duals. It can be reproducible across a change that still
moves the clearing. The load-bearing evidence is therefore the three *scored* quantities in the
table above, not the npz.

**Not resolvable zero-solve at this HEAD, and I am not asserting a cause.** The container holds
a shallow clone (266 commits); both older `scored_at_sha` values (`8084b135ed8d`,
`c2ebb74fa7f1`) are unreachable, and the dispatch parquet is gitignored by design. Two
candidates remain and cannot be separated from committed artifacts: **(i)** the cache key
carried two different solves, or **(ii)** the checker/scorer changed in the window.

**Candidate (i) is the one the codebase itself documents as possible** — cited, not assumed.
`src/market_sim/results/cache.py`, module docstring, "Cache-key staleness (cache-epoch policy)":
the key hashes `asdict(config)`, so *"a change that alters a solve's output but is **not** a
`ScenarioConfig` field (a bug fix in the LP builder, a new mechanism gated by an env var, a
change to a measured input basis) does NOT move the key, and a pre-change `results/{iso}/{key}/`
bundle would be silently re-used"*; the module *"never auto-invalidates on epoch; that is the
operator's responsibility."* `data/confirmed_retirements.py` restates it operationally —
*"cache_key hashes config only, never data-file state"*, with an instruction to delete caches
solved before a data regeneration. So the repo already knows a key can span two dispatches, and
relies on a human step to prevent it. That makes (i) the leading candidate on documented
mechanism; it does **not** make it proven, and (ii) stays open.

**Binding consequence, which holds whichever candidate is right:**
- **An ERCOT I3 magnitude is comparable only within a solve vintage.** FR-6's "0.01–0.03 % of
  load" **must not be differenced** against a 2026-08-30 record. (The board already carries this
  hazard for T1-F, corrected 2026-08-24 when the live slack came back 2.7×–20.5× the FF-2D
  vintage it had been quoting.)
- **The A/B deltas in §2 and §4 are unaffected**: every pair quoted (`d12c`, `d11r`,
  `capentry`, `c1joint`) was arm-and-control scored in one session at one `scored_at_sha`.
  Only cross-session comparisons are at risk, and the only one in the committed ERCOT set is
  `refresh` vs the 2026-08-30 controls.
- **Routed as R-5** (§6). If it is cache under-determination, it reaches beyond ERCOT and
  beyond I3, because any A/B drawing a cached control from an earlier session inherits it.

### 5.2 The I3 instrument emits no MW, no hours, no GWh

The charter asks for "slack MW/hours by year". **That is not obtainable zero-solve.**
`check_i3_unserved_dump` emits only `"<year>: slack {frac:.2%} of load"` — no breach-hour
count, no peak slack MW, no GWh — and the sidecar stores that string verbatim. The dispatch
parquet that would carry the hourly detail is gitignored. Deriving GWh would require an
external annual-load figure the committed set does not contain, which would be an estimate
presented as a measurement; this finding declines to do that and reports `% of load` as
measured.

For contrast, the board's PJM I3 row quotes "31 and 58 hours; 146.0 and 231.3 GWh" — that came
from a bespoke in-session measurement with the parquet in hand, **not** from the standard
instrument. So the program currently has two non-comparable grains of I3 evidence. Routed as R-4.

### 5.3 Adjacent, and NOT actioned here: the FR-24 declaration ledger, and I3 outside ERCOT

`frontend/data/hindcast/invariant-failures.json` declares 3 of the **8** committed ERCOT T1-H
I3 FAILs. Undeclared: `refresh`, `d11r-control`, `d11r-exhaustion`, `d12c-control`,
`d12c-armed`. Measured across the whole committed sidecar set (30 runs), **13 runs carry a FAIL
that does not match their declaration** — the 5 ERCOT I3 rows plus 8 belonging to CAISO
(`I7`,`I9`), MISO (`I3`), NEISO (`I6`×2, `I3`) and PJM (`I7`×2, `I7`+`I12`). No declaration is
stale. The CI job `forecast-invariant-artifacts` (`check_forecast_invariants.py --sidecar-dir`)
**fails on all 13** — run here to confirm, not inferred. It has been red on main since at least
2026-08-14 (`.github/workflows/ci.yml`'s own header records it then, on three undeclared PJM I7
rows, from the pre-clear-out sidecar set), so this is a standing red the ERCOT rows deepen
rather than one they caused.

**Deliberately not fixed by this lane.** The ledger's own `capentry_note` and `c1joint_note`
assign each declaration to the lane that registered the run and state that "the d11r/d12c rows
are capx-lane artifacts this lane must not touch". This lane respects the same boundary rather
than making an exception for itself. Routed to the director as **R-6** — it is a records duty
needing one owner, not a measurement question.

**One observation the director should have, scoped and not acted on.** `invariant-failures.json`
`dominant_open_causes` still reads *"I3: FR-6 ERCOT energy-only scarcity slack"*, i.e. it treats
I3 as an ERCOT-only phenomenon. Two committed non-ERCOT runs now carry an I3 FAIL —
`miso-2026-2030-s123-verify` and `neiso-2026-2050-t3-golden-bau` — and **FR-6's cause cannot
explain either**, because MISO and NEISO are capacity-market ISOs where
`resolve_reserve_margin_build_enabled` returns `True` and the backstop is armed. Whatever drives
those rows is a different mechanism. **Adjudicating them belongs to their own ISO lanes (rule 25
`[R-ISO-SCOPE]`) and this lane does not touch them**; it matters here only because it widens
R-4's value (a shared instrument grain) and because the `dominant_open_causes` line, as written,
would mislead the next reader into attributing a MISO or NEISO I3 to ERCOT's energy-only design.

---

## 6. Repair options ROUTED to the director — nothing built

Each option states its rule-13 `[R-MEASURED]` and rule-21 `[R-DOF]` admissibility. Matrix cells
checked in `docs/codebase-site/data/mechanism-matrix/ERCOT.js` before routing (rule 28 duty (a)).

### 6.0 ALREADY DONE in this lane (the only code change)

**FR-6's cause now has a code home.** A design-intent block was added to
`resolve_reserve_margin_build_enabled` in
`src/market_sim/model/capacity_evolution/adequacy.py` — naming the consequence chain
(energy-only ⇒ backstop off ⇒ one-pass ⇒ no corrective ⇒ residual leaves as VOLL-priced load
slack ⇒ that is I3), citing FR-6 and this finding, carrying the §2 monotonicity, and closing
with the two things not to do (do not arm the backstop for ERCOT; do not repair it in the LP).
**Docstring text only — zero behaviour change**, `+24` lines, AST- and compile-verified.

### R-1 — Energy-only-aware adequacy backstop for ERCOT — **ROUTED AS NOT RECOMMENDED**
Arm `reserve_margin_build_enabled` for ERCOT, or add an energy-only variant.
**Admissibility: rule 1 `[R-STRUCT]` FAILS on the merits.** This is the force-build the seam's
own docstring rules out: ERCOT procures no capacity to an adequacy requirement, so a backstop
manufactures firm MW the market never buys, and it would close I3 by a mechanism that is not
real. It would also push I12 further out the top (§3). ERCOT's `reserve_margin_backstop` matrix
cell is `.` (n/a), consistent with that. **Recorded so the option is visibly closed, not
silently unconsidered.**

### R-2 — Entry-screen volume calibration — **ROUTED AS THE PRIMARY LANE**
The §2 monotonicity says the whole breach set is one number: how much the ERCOT entry screen
builds. The model spans 27.8–54.0 GW against 55.4 GW actual, and the band-satisfying settings
sit at the bottom of that span.
**Admissibility: rule 13 PASS** — the entry screen is a forward construction driven by forward
prices/margins with no measured outcome fed back. **Rule 21: the real question.** Any repair
must identify its parameters from the screen's own objects (as `entry_margin_exhaustion` did —
zero new DOF), never from the I3 or I12 residual. **A volume knob fitted to close I3 is
inadmissible** and would be exactly the "adder tuned to the residual" rule 13 forbids.
**Sequencing:** this lane recommends the D12-A pair's post-arming T1-H (D6) land **first** —
it moves the build 39.9 → 27.8 GW, i.e. it changes the very quantity R-2 would work on.
Calibrating volume against a pre-arming baseline would be work done against a superseded posture.

### R-3 — Scarcity-revenue-consistent entry timing (storage duration) — **ROUTED, SMALL, READY**
The `capentry` isolate (§2.2(b)) shows 4× slack at identical MW and identical per-tech GW,
purely from storage duration. The screen's duration choice is not scarcity-hour-aware.
**Admissibility: rule 13 PASS** if the duration screen values a candidate at the entering year's
own expected-ORDC surface — the same one-object discipline `entry_forward_reserve_leg` already
established (rule 19 `[R-ONE-MECH]`: re-found the existing storage screen's leg, never add a
second). **Rule 21 PASS** if it reuses that adder, as the D12 leg did (zero new DOF).
Matrix: `storage_entry_value_stack` / `storage_entry_availability_gate` /
`storage_entry_cost_normalized_rank` — the latter two are freshly armed (owner ruling R-A), so
any candidate here must be scoped against that posture, not the pre-R-A one.

### R-4 — Give the I3 instrument a grain — **ROUTED, CHEAP, DO THIS BEFORE THE NEXT MEASUREMENT**
Extend `check_i3_unserved_dump`'s detail to carry **breach hours, slack GWh and peak slack MW**
alongside `% of load`, so a committed sidecar records what §5.2 shows it currently cannot, and
so ERCOT rows become comparable with the bespoke PJM grain.
**Admissibility: rule 13 N/A** (a reporting change; no model input, no threshold moved — the
`1e-4` gate must not be touched). **Rule 21 N/A** (no free parameter). Scorer-only, no re-solve;
existing sidecars keep their coarse strings and new ones gain the grain. **This lane recommends
it be scheduled ahead of D6** so the post-arming measurement lands at the finer grain and the
§4 pre-declaration can be checked on hours as well as percent.

### R-5 — Adjudicate the shared-cache-key divergence — **ROUTED, POSSIBLY PROGRAM-WIDE**
Resolve §5.1: determine whether `28cef3500ec1fd9e` was written by two different solves or
whether the checker/scorer changed in the 2026-08-22 → 2026-08-30 window. Needs a full-history
clone (both `scored_at_sha` are unreachable here) and, for the first branch, one re-solve —
so it is **out of this lane's zero-solve scope**. Concretely: diff
`scripts/check_forecast_invariants.py` and the hindcast scorer across that window; if unchanged,
candidate (ii) is eliminated and the cache-epoch ledger for the window
(`PINNED_DEFAULT_CACHE_KEY` in `tests/regression/test_persisted_identity.py`, per
`results/cache.py`'s policy) is the place to look for an unrecorded advance.
**Admissibility: rule 13 N/A, rule 21 N/A** — an audit, no model surface touched.
**Blast radius, which is why this is routed at all:** `results/cache.py` states the hazard as
general, so if it is candidate (i) then **every ISO's A/B work that draws a cached control from
an earlier session inherits it**, not just ERCOT I3 — a rule 7 `[R-PARQUET]` check-before-run
hazard, and one that would silently corrupt exactly the arm-vs-control deltas the capx program
runs on. **Recommended priority: high, on blast radius rather than on magnitude.**

### R-6 — FR-24 declaration ledger — **ROUTED, RECORDS ONLY**
13 of 30 committed sidecars carry a FAIL not matching their declaration (§5.3) — 5 ERCOT I3
plus 8 across CAISO/MISO/NEISO/PJM — with `forecast-invariant-artifacts` red on main and three
lanes each declining on lane-boundary grounds. Needs **one owner assigned**, not a measurement;
the per-lane convention has demonstrably not converged. Worth pairing with a correction to
`dominant_open_causes`' "I3 = FR-6 ERCOT energy-only" line, which two capacity-market I3 rows
now contradict.

---

## 7. Governance, scope and provenance

- **Zero solves.** Every number is read from a committed artifact: eleven
  `frontend/data/hindcast/ercot-2021-2025-realized-t1h-*.json` sidecars, their
  `results/hindcast/*/ERCOT/*/score.json`, their `run_config.json`, the `.npz` hashes,
  `frontend/data/forecast/ff-verdicts.json` (`ercot-t1f`), and
  `frontend/data/forecast/program-status.json`.
- **Card Y-C respected.** The net-revenue half is untouched: not measured, not modelled, not
  referenced as evidence. §4's `entry_forward_reserve_leg` discussion quotes that field's own
  committed citation block for the *volume* prediction only.
- **Rule 13 `[R-MEASURED]`:** no measured outcome enters any model input here. The only code
  change is a docstring.
- **Rule 22 `[R-HOLDOUT]`:** no year outside 2023–2025 was solved, scored or registered. The
  T1-H records read here are pre-existing committed artifacts of forecast-mode runs.
- **Rule 25 `[R-ISO-SCOPE]`:** ERCOT only. No other ISO's files, cells or rows touched.
- **Rule 27 `[R-PUSH]`:** `adequacy.py` (508 → 533 lines) was edited locally with a targeted
  edit and pushed as exact on-disk bytes, then blob-verified against the remote.
- **Rule 28 `[R-MECH-MATRIX]` duty (a) only.** No mechanism was tested, so **no cell is
  written.** The ERCOT shard was READ before routing §6: `reserve_margin_backstop` `.`,
  `entry_margin_exhaustion` `O`/fc `K`, `entry_forward_reserve_leg` `O`/fc `K`,
  `entry_lookahead_reprice` `K`/fc `O`, `ordc_scarcity_overlay` **`R`** (ERCOT-97 — deliberately
  not routed). No routed option re-tests a cell adjudicated `R`/`I`/`G`.
- **Board:** the ERCOT `blocking_rows` I3 entry in `frontend/data/forecast/program-status.json`
  was refreshed with the T1-H breach set, the §4 pre-declaration and the §5.1 comparability
  caveat. **ERCOT block only**; no verdict, gate leg or determination moved.
