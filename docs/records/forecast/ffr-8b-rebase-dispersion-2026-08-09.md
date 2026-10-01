# FFR-8B — Re-base the repaired forward price object on the corrected renewable vintage seed; diagnose the E1 committed-capability dispersion gap

**Session.** FFR Wave 8, RE-BASE + DIAGNOSIS lane (owner-re-opened D-21(a), Addendum AC.1,
via Addendum AF.4). Branch `claude/ffr-8b-rebase-dispersion-03fmfk`, off `origin/main`
`e9f99e6`. Model: Fable (rule 27 — runner/model core).

**Charter.** Two objects, in order. (Phase 0) The FFR-8A repair arm
(`docs/handoffs/ffr-8a-scarcity-restoration-2026-08-08.md` §4) was solved PRE-EPOCH — before
the FFR-3V-FIX renewable vintage seed correction (`docs/handoffs/ffr-3v-fix-2026-08-08.md`
§6.1: ERCOT hindcast wind pool 42,000 → 27,541 MW, solar 38,000 → 4,864 MW at vintage 2020,
plus the ERCOT-only §1a proposed-pipeline graft removal). The FFR-8A §4 record is therefore
STALE BY DESIGN for any run at this head; Phase 0 re-runs the repair-arm recipe VERBATIM at
this head and its outputs BECOME the new recorded baseline (Addendum AF.2 — the re-base IS
the next lift evidence). (Phase 1) FFR-8A §5 finding (c): the E1 committed-capability
formula under-disperses vs the measured RTOLCAP low tail (r_online p1 13.3 GW vs measured
p1 7.9 GW, 2024). Diagnose that gap by a pre-registered decomposition; repair ONLY if
rule-13 admissible (Phase 2); paired read ONLY if a repair lands (Phase 3).

**Rule-1/13 posture.** Nothing here is tuned toward 2.294 GW, the measured price curve, the
measured RTOLCAP distribution, or any residual. The measured RTOLCAP distribution is an
OUTCOME of commitment — it may VALIDATE a repair, never parameterize one. No arming, no
promotion, no keeper contact, no backcast-registry touch, no lift recommendation (the
FH-4/FH-5 determination is the manager's). The lambda-led real-time conduct content is OUT
OF SCOPE by construction (FFR-8A §5(a)); bar re-levels and signal scaling stay REFUSED BY
NAME (FFR-6A rows 3–4). E3 (NP6-576-ER vs fallback) stays ESCALATED/HELD — re-opened only
if the Phase-1 decomposition produces direct evidence on it, and the outcome is recorded
either way.

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE invocation 1 was launched. Nothing in §1
changes after. The Phase-1 method (§1.3) was likewise committed before any dump existed and
before any decomposition number was computed.*

### 1.1 Phase 0 — the re-base invocation and its fixed read set

Invocation 1: the FFR-8A repair-arm recipe VERBATIM at this head:

```
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr8b-base
```

Cold (`results/` is gitignored; no cache hit is budgeted), 4 LP years (2022 bridged), years
SEQUENTIAL (rule 12). **The FFR-5D-M §1.3 reproduction gate is NOT attempted** — its
numbers are pre-epoch by construction; this prereg FIXES the read set and invocation 1's
outputs are the new recorded baseline. The diagnostic dumps
(`screen_signal_diag_<year>_for_<entering>.npz`) are written automatically under the armed
unified lookahead; Phase 1 consumes them.

**The comparator for every read is the PRE-EPOCH FFR-8A §4 REPAIR-arm record** (same recipe,
pre-epoch seed), with every delta reported at full magnitude. The manager's expected
DIRECTION, recorded in advance: corrected seed → smaller VRE pools → higher entering net
load at every screen → MORE scarcity content. An expectation to test, never a target.

The reads — the FFR-8A §1.5 set, re-run verbatim:

* **(i) The price side.** Per-screen (into-2022/2023/2024/2025) mean / max / h>$100 /
  h>$1000 / adder mean, vs the pre-epoch repair-arm row AND vs measured (2024: 161 h >
  $100, mean $26.82, max $3,060; 2025: 217 h, $32.49, $1,570). Per-fuel replica margins
  (the FFR-6A construction) vs the pre-epoch rows (2024: coal 0.05 / cc 8.94 / ct 0.69 /
  st 0.01; 2025: 16.96 / 20.53 / 19.37 / 17.13 $/kW-yr), the replica-at-measured-prices
  columns (2024: 75.4 / 86.7 / 65.6 / 65.6; 2025: 97.2 / 76.4 / 47.0 / 47.0) and the bars
  (coal 58.5 / cc 30 / ct 21 / st 35).
* **(ii) The exit side.** (1) The gas_st 2022-bridge wave — pre-epoch repair arm: 27 units
  / 6,500.6 MW at net $24.85 vs bar $35.00; does the corrected seed shrink it further?
  (2) In-window economic executions — must stay ≈ 0; ANY in-window economic execution is a
  FALSIFICATION signal per FFR-7C, never a success. (3) The fleet-wide entry_capped census
  — pre-epoch: 578 / 67,036.4 MW (2024), 523 / 56,518.7 MW (2025). (4) The FFR-5A coal
  cohort's event sequence — pre-epoch: never decided at the 2021 screen; 23 / 7,040.2 MW
  decided in the 2025 ledger (decided_year 2024, exe 2027) at net $16.65 vs bar $58.5 —
  including the §4.2.4 non-monotone adequacy-cap interaction (pre-epoch reserve margins
  33.1 % / 37.1 %; a higher price object can ENLARGE the coal decision through the cap).
* **(iii) Additions vs 55.4 GW actual.** Pre-epoch: 17.0 GW decision basis (wind 5.0 /
  solar 0.0 / gas_cc 3.0 / gas_ct 3.0 / storage 6.0). Reported, not targeted — the entry
  screens' economics and caps are FFR-4/5 lanes' objects.

**Bookkeeping reads.** The runtime `cache_key=` log line and the ledger path
`<out-dir>/ERCOT/<runtime-key>/` (verified before believing any zero). FFR-3V-FIX moved no
`ScenarioConfig` field, so the expected runtime key is the pre-epoch repair arm's
`816031a3308cccde` (same-key invalidation, cache epoch 2026-08-08); a DIFFERENT key is
explainable only by a registered-field change on main since 2026-08-08 and is diagnosed
before proceeding (the nyiso-128 pattern).

**Registration commitment.** The base arm registers in the HINDCAST namespace only
(`register_hindcast.py`, `meta.kind="full_forward"`, id
`ercot-2021-2025-t1ff-armr-ffr8b-base`) REGARDLESS of the Phase-2 outcome; a Phase-3 arm
(`...-ffr8b-e1disp`) registers only if a repair lands. Never the backcast registry.

### 1.2 Data sources (all committed, none new)

* Invocation 1's own dumps and evolution ledgers (this session's solve).
* Measured reserves: `data/raw/ercot/ercot_{2024,2025}_ordc_reserves_hourly.parquet`
  (NP6-905-CD; the 2025 tail past the 2025-12-05 RTC+B go-live is NaN and excluded).
* Measured net load: the clean store's demand and wind/solar generation for 2024/2025
  (training-tier years; regenerated by `regenerate_clean.py` this session).
* The FFR-6A per-fuel margin basis JSON (`docs/handoffs/ffr-6a/perfuel-margin-probe-*.json`)
  for the replica construction, exactly as the FFR-8A probes consumed it.
* The FFR-7C corrected actual-exit classes (the ffr8a ablation probe's
  `ACTUAL_EXITS_BY_CLASS_MW`) for the actual-fleet constructions.
* 2022 IS BRIDGED AND NEVER READ. No file for 2022 (or any pre-2023 year) is opened by any
  probe in this lane.

### 1.3 Phase 1 — the E1 dispersion decomposition method (fixed before computing)

**The object.** FFR-8A §5(c): E1's committed-capability point model under-disperses vs the
measured RTOLCAP low tail. The structural cause candidates are fixed by the formula's own
construction (`ercot_rtolcap_forward_supply_cap_mw`): (a) the share tables are
conditional-MEDIAN models per (class × season × net-load decile) — they carry no
within-cell realization dispersion; (b) the decile axis is the WITHIN-SERIES percentile
rank of the evaluated net-load series (`_ercot_rtolcap_fwd_decile` ranks the series
itself), so the formula's unconditional distribution assigns exactly 10 % of hours to each
decile's share level whatever net-load series it is fed — its year-distribution is a step
function over (season × decile) cells, nearly invariant to the net-load basis except
through seasonal rank alignment and the physical-headroom `min()`; (c) the forced-outage
realization is deliberately NOT in E1 — E4 carries it as the Gauss–Hermite integration over
the WEFOR variance sigma_R.

**The decomposition.** Sequential distributional steps, each swapping ONE ingredient,
evaluated per year (2024, 2025) on four constructed hourly series:

* **A** — measured RTOLCAP (committed NP6-905-CD telemetry; 2025 truncated at RTC+B).
  The target distribution. Diagnosis-only; parameterizes nothing.
* **B** — the E1 formula evaluated at the MEASURED realized net load (clean demand −
  measured wind − solar generation) on the ACTUAL fleet class capacities (vintage-2020
  classes minus the FFR-7C corrected exits), with the measured storage-AS series as the
  storage term (the derive script's own fit basis). The formula's ceiling given perfect
  net-load knowledge.
* **C** — the arm's own E1 `r_online` from invocation 1's dumps (evolved fleet, forward
  net-load basis, physical-headroom min() included).
* **C′** — the formula evaluated on the arm's dumped forward net load with the ACTUAL
  fleet (isolates the fleet-length term out of C → B).

Steps, each read at matched quantiles (mean, p50, p25, p10, p5, p1, min) and at
knee-visit counts (hours below the fallback-curve $10/$100/$1000 knees: 7,415 / 6,200 /
4,578 MW):

1. **Fleet-length step (C → C′)** — expected ≈ 0 (FFR-8A §2.5 term (c): wrong sign,
   small); measured to bound it, not because it is suspected.
2. **Net-load realization share (C′ → B)** — the charter's share (2): forecast-error dips
   the point evaluation cannot see. Because of construction fact (b) above, the
   pre-registered EXPECTATION is that this step is SMALL in unconditional quantiles — the
   rank-relative decile axis makes the formula nearly blind to which net-load series it is
   fed. A small C′ → B step is itself the finding: the formula construction CANNOT express
   a net-load realization share, so any repair to dispersion must enter through a
   different term. NOTE (double-count guard): the published curve's own sigma (intra-hour
   PRC projection error) is a DIFFERENT horizon and composes orthogonally; it appears
   nowhere in this decomposition and no share may be identified from it.
3. **Commitment share (B → A)** — the charter's share (1): realized commitment dispersion
   around the conditional-median model at the TRUE net load. Read as the quantile gaps
   plus the within-cell residual: per (season × decile) cell, the std of (A − B); pooled
   residual std `s_resid`.
4. **Outage share, already carried (share 3)** — sigma_R from the model's OWN WEFOR
   machinery (the dump's `sigma_r_mw`, seasonal). Report sigma_R vs `s_resid` (the
   fraction of the B → A residual E4's integration already prices) and the tail view: the
   arm's C ± 2·sigma_R envelope vs A's p1. The commitment share NET of sigma_R is the
   only surface a Phase-2 repair may target — E4's part must not be double-carried.

**Pre-registered expectations (to test, not targets):** share (1) commitment dominates the
p1 gap; step 2 near-nil in unconditional quantiles (construction fact (b)); step 1 ≈ 0;
sigma_R ≈ 2.2–2.4 GW covers a minority of `s_resid`. **E3 evidence check:** the
decomposition is quantity-side; the expectation is it produces NO direct evidence on the
NP6-576-ER-vs-fallback curve-parameter question, in which case E3 stays ESCALATED/HELD
untouched; whatever it shows is recorded.

### 1.4 Phase 2 admissibility rule (fixed in advance)

A repair may be built ONLY from: the model's own commitment machinery (P0 run patterns),
the forward AS model, published methodology quantities, the model's own outage machinery.
The rule-13 test VERBATIM: reproducible for a forward year from forward drivers, responds
to changed conditions. The measured RTOLCAP distribution may VALIDATE a repair, never
parameterize one. If the repair cannot be built without inventing a parameter: STOP, record
the escalation, and land Phases 0–1 alone — that is a successful session outcome. If a
repair lands: one new `ScenarioConfig` gate, default OFF, composing with (requiring)
`capacity_screen_scarcity_restoration`; `_CACHE_KEY_OPTIONAL_FIELDS` + defaults ledger in
the SAME commit; matrix row in the same PR; the cache-key-pin check verdict is WAITED FOR
before merging. Phase 3 then re-runs the §1.1 recipe plus the new flag
(`--out-dir .../ercot-2021-2025-t1ff-armr-ffr8b-e1disp`) with its own pre-registered
arm-vs-base reads and an honest expectation committed BEFORE invocation 2 (the prereg-2
pattern; hash recorded in this doc).

### 1.5 What this lane will NOT do

No tuning, no arming, no keeper contact, no promotion, no backcast-registry touch, no lift
recommendation, no bar re-levels, no signal scaling, no measured-outcome input in any solve
path. A Phase-0 read that surprises is a finding to record, never a license to adjust.

---

*(Sections below this line are filled AFTER the pre-registered work runs, in order, as
produced. Prereg commits: `76d79b2` (this doc's §1), `797426c` (the probe scripts) — both
BEFORE invocation 1 launched.)*

## 2. Phase 0 — the re-based baseline (invocation 1)

Invocation 1 ran the §1.1 recipe verbatim, cold, years sequential: solved
[2021, 2023, 2024, 2025], bridged [2022], `leakage_violations: []`, exit 0, ~25 min wall.
**Runtime `cache_key=816031a3308cccde` — byte-identical to the pre-epoch repair arm's, as
pre-registered** (the epoch is a same-key invalidation; no registered field moved). Holdout
freeze ACTIVE and read at launch; no marker spent. Registered
`ercot-2021-2025-t1ff-armr-ffr8b-base` (hindcast namespace, `meta.kind="full_forward"`).
Committed reads: `docs/handoffs/ffr-8b/rebase-reads-2026-08-09.json` (probe
`scripts/probes/ffr8b_rebase_reads.py`); dumps committed in-flight (`97182ee`, `d0a856b`).

### 2.1 Read (i) — the price side

Per-screen distributions, re-based vs the pre-epoch §4 repair-arm record vs measured:

| screen | arm | mean $/MWh | max $ | h>$100 | h>$1000 | adder mean |
|---|---|---|---|---|---|---|
| into-2022 | pre-epoch | 55.88 | 5,000 | 72 | 72 | 28.57 |
| into-2022 | **re-based** | **67.93** | 5,000 | **92** | 72 | **36.35** |
| into-2023 | pre-epoch | 68.02 | 5,000 | 120 | 72 | 39.36 |
| into-2023 | **re-based** | **110.07** | 5,000 | **413** | **170** | **75.99** |
| into-2024 | pre-epoch | 14.15 | 36.3 | 0 | 0 | 0.005 |
| into-2024 | **re-based** | **40.86** | **4,798.2** | **174** | **68** | **21.17** |
| into-2024 | measured | 26.82 | 3,060 | 161 | — | — |
| into-2025 | pre-epoch | 14.27 | 4,247.8 | 13 | 7 | 2.456 |
| into-2025 | **re-based** | **15.99** | **1,376.1** | **8** | **1** | **0.66** |
| into-2025 | measured | 32.49 | 1,570 | 217 | — | — |

Per-fuel replica margins ($/kW-yr, the pre-epoch basis kept verbatim):

| screen | fuel | pre-epoch | re-based | replica (measured) | bar |
|---|---|---|---|---|---|
| 2024 | coal | 0.05 | **148.68** | 75.4 | 58.5 |
| 2024 | gas_cc | 8.94 | **186.83** | 86.7 | 30.0 |
| 2024 | gas_ct | 0.69 | **173.54** | 65.6 | 21.0 |
| 2024 | gas_st | 0.01 | **148.54** | 65.6 | 35.0 |
| 2025 | coal | 16.96 | **4.52** | 97.2 | 58.5 |
| 2025 | gas_cc | 20.53 | **12.60** | 76.4 | 30.0 |
| 2025 | gas_ct | 19.37 | **5.53** | 47.0 | 21.0 |
| 2025 | gas_st | 17.13 | **4.47** | 47.0 | 35.0 |

**The manager's directional expectation is CONFIRMED at the 2021-stack and 2023-stack
screens and INVERTED at the 2024-stack screen.** The corrected seed (−14.5 GW phantom
wind, −33.1 GW phantom solar) raises every entering net load priced off the 2021/2023
fleets: into-2023 mean nearly doubles (68 → 110, 170 h > $1000 — the 2021 vintage fleet
against 2023 net load carries genuine shortage hours, headroom min −18.9 GW), and the
into-2024 screen goes from ZERO scarcity content to 174 h > $100 — the measured count is
161 — with margins ~2× the replica-at-measured-prices columns. But the higher object
roughly DOUBLES the model's own build (§2.3), so by the 2024 solve the fleet is long again
(installed headroom p1 14.9 GW) and the into-2025 screen's deep tail SHRINKS below its
pre-epoch value (7 → 1 h > $1000, max 4,248 → 1,376) while measured 2025 is the tightest
year in the record (217 h > $100). Both directions are the measurement; neither is a
target. The 2024-screen overshoot and the 2025-screen undershoot share one mechanism: the
screens price the MODEL's evolved fleet, whose VRE/storage trajectory (36 GW added vs 55.4
actual, timed differently) is now the binding error term — the price object's scarcity
content tracks the model's fleet error, no longer a phantom seed.

E2 note: `as_hold` is identically 0 at every screen (storage AS share 5.95–10.5 GW swallows
the ~4.6 GW responsive requirement) — the FFR-8A conditional-inertness finding reproduces
post-epoch unchanged.

### 2.2 Read (ii) — the exit side

1. **The gas_st 2022-bridge false wave is GONE ENTIRELY.** Pre-epoch: 27 units / 6,500.6 MW
   decided+executed at net $24.85 vs bar $35.00. Re-based: **zero gas_st pipeline events in
   any ledger** — the into-2022 object (gas_st margin $283.26/kW-yr vs bar $35) lifts the
   whole class over the bar. Model in-window thermal retirements are now **0.0 GW vs 2.294
   actual** (err −100 %, band FAIL on the UNDER side): the false wave that FFR-5A/7C
   chartered this lane against has vanished, and what remains is the model missing the
   real, confirmed-channel exits — a different, smaller defect than manufacturing 6.5–10.9
   GW of phantom ones.
2. **In-window economic executions = 0** (the FFR-7C falsification bound holds; no
   executed events exist at all).
3. **entry_capped census**: 2024 ledger **NONE** (the re-based into-2024 screen's margins
   clear every bar — no merchant unit fails, so the adequacy cap has nothing to hold
   back); 2025 ledger **559 / 64,594.5 MW** (coal 5.9 / cc 34.7 / ct 12.7 / st 11.3 GW) —
   the weak into-2025 screen fails the fleet again. Pre-epoch: 578 / 67.0 GW (2024) and
   523 / 56.5 GW (2025).
4. **The coal cohort: still never decided at the 2021 screen; its 2025-ledger decision
   GROWS again** — 26 / 8,057.6 MW decided (decided_year 2024, exe 2027, outside the
   window) at net $4.66 vs bar $58.5 (pre-epoch: 23 / 7,040.2 at $16.65). The §4.2.4
   non-monotone adequacy-cap interaction continues: reserve margins 2021 34.9 % / 2023
   24.6 % / 2024 36.1 % / 2025 43.2 % (pre-epoch 33.1 / 37.1), and the higher-RM fleet
   admits more of the always-failing coal into the decided pipeline. The net revenue FELL
   ($16.65 → $4.66) because the re-based into-2025 screen is WEAKER than pre-epoch — the
   same screen asymmetry as §2.1.

### 2.3 Read (iii) — additions

**17.0 → 36.0 GW decision basis** (wind 5.0 / solar **7.429** / gas_cc 6.0 / gas_ct 4.571 /
storage **13.0**) vs 55.4 GW actual. Two reads worth stating at full magnitude: **solar
entry fires for the first time in this posture's record** (0 → 7.4 GW; FFR-3V §6.1's
compounding claim — the over-seeded pool depressed the very signal the solar screen is
judged against — validated at the ERCOT re-base), and **storage lands INSIDE its score
band** (13.0 vs 13.691 GW actual, err −5.0 %, PASS — the arm's storage fleet is no longer
"over-built vs actual" on the additions metric, though the BASE-year fleet plus additions
still reaches 30 GW power by the 2024 solve against ~10 GW actual installed, so the
storage-conditional findings (E2 inertness, §3's storage-term inflation) still hold on
this arm). gas_cc stays FAIL high (6.0 vs 0.244), wind FAIL low (5.0 vs 12.663). Reported,
not targeted — the entry economics and caps are FFR-4/5 lanes' objects.

## 3. Phase 1 — the E1 dispersion decomposition (pre-registered §1.3 method)

Committed read: `docs/handoffs/ffr-8b/e1-dispersion-2026-08-09.json` (probe
`scripts/probes/ffr8b_e1_dispersion.py`, committed before any dump existed). The probe's
self-check — `C == min(C″, phys)` — holds EXACTLY (max |Δ| = 0.0 both years), so the
offline reconstruction is the runner's own construction.

The chain at matched quantiles (MW; A = measured RTOLCAP, B = formula at measured net
load + measured storage-AS + actual fleet, B̃ = B with the arm's storage scalar, C′ =
formula at the arm's net load + actual fleet, C″ = + evolved fleet, C = the arm's
phys-bounded r_online):

| year | series | mean | p50 | p10 | p5 | p1 | min |
|---|---|---|---|---|---|---|---|
| 2024 | A measured | 16,679 | 16,197 | 10,328 | 9,298 | 7,874 | 5,094 |
| 2024 | B | 16,076 | 16,642 | 11,964 | 11,103 | 9,555 | 8,966 |
| 2024 | B̃ | 22,678 | 23,382 | 19,303 | 16,844 | 16,844 | 16,844 |
| 2024 | C′ | 22,635 | 23,271 | 19,249 | 16,844 | 16,844 | 16,844 |
| 2024 | C″ | 23,206 | 23,905 | 19,770 | 17,206 | 17,206 | 17,206 |
| 2024 | C | 22,604 | 23,905 | 17,206 | 12,684 | 6,277 | 431 |
| 2025 | A measured | 19,124 | 18,551 | 12,474 | 10,975 | 8,955 | 7,060 |
| 2025 | B | 16,749 | 17,287 | 12,377 | 11,017 | 9,789 | 8,640 |
| 2025 | B̃ | 24,497 | 25,132 | 21,053 | 18,594 | 18,594 | 18,594 |
| 2025 | C′ | 24,407 | 25,132 | 21,053 | 18,594 | 18,594 | 18,594 |
| 2025 | C″ | 24,978 | 25,655 | 21,594 | 18,956 | 18,956 | 18,956 |
| 2025 | C | 24,846 | 25,655 | 20,863 | 18,956 | 14,871 | 5,716 |

Knee visits (h at/below the fallback $10 / $100 / $1000 knees): **A: 48 / 8 / 0 (2024),
5 / 0 / 0 (2025). B: 0 / 0 / 0 both years.** C: 133 / 83 / 39 (2024, all via the phys
bound), 5 / 1 / 0 (2025).

The single-swap steps at the low tail (p1 Δ, MW):

| step | 2024 | 2025 | reading |
|---|---|---|---|
| phys bind (C vs C″) | −10,930 (1,070 h bound) | −4,085 (334 h) | ALL of the arm's own low-tail dispersion is the physical-headroom `min()`, none is the share formula |
| fleet length (C″ vs C′) | +362 | +362 | ≈ 0, as pre-registered (FFR-8A term-c again) |
| **net-load realization (C′ vs B̃)** | **0.0** | **0.0** | **EXACTLY zero — pre-registered expectation confirmed: the rank-relative decile axis makes the formula's unconditional distribution invariant to the net-load series. The formula construction CANNOT express a net-load realization share.** |
| **storage-term basis (B̃ vs B)** | **+7,289** | **+8,805** | the arm's storage scalar (0.35 × 25–30 GW evolved fleet = 8,750–10,500 MW flat) vs the measured storage-AS series (mean 2,148–2,716, p1 ~0–901): the single LARGEST model-side inflator of E1's R on this arm |
| commitment (B vs A) | +1,681 (p5 +1,804, p50 +445) | +834 (p5 +42, p50 −1,264) | the conditional-median share model at TRUE net load and TRUE storage still misses the measured low tail by ~0.8–1.7 GW at p1 — and never visits any knee where the measured series spends 48 h (2024) at/below the $10 knee |

Within-cell (season × decile) residual of A − B: pooled std **4,515 MW (2024) / 4,727 MW
(2025)**. The model's own σ_R (E4's WEFOR variance, mean 2,640 / 2,765 MW) covers **58.5 %
of the within-cell residual std in both years**; the remainder — √(4,515² − 2,640²) ≈
**3,660 MW** (2024), ≈ 3,830 MW (2025) — is commitment-realization dispersion no model
element carries. (Double-count guard honoured: the published curve's intra-hour σ appears
nowhere in this decomposition.)

**The §5(c) finding, re-based:** the under-dispersion is now SCREEN-ASYMMETRIC. At the
re-based 2024 screen the phys-headroom bound alone drives C's p1 to 6.3 GW — BELOW the
measured 7.9 — so the FFR-8A "13.3 vs 7.9" gap does not reproduce there (the energy-
shortage mechanism, not the share formula, carries the tail). At the long-fleet 2025
screen it persists in full (C p1 14.9 vs measured 9.0). The share-formula component
itself is a ~14×4-cell step function whose p5 = p1 = min at the bottom cell — its
under-dispersion is structural to the conditional-median construction, exactly as §1.3
pre-stated.

**E3 evidence check (pre-registered):** the decomposition is entirely quantity-side and
produced NO direct evidence on the NP6-576-ER-vs-fallback curve-parameter question. E3
stays **ESCALATED/HELD**, untouched, as the charter requires.

## 4. Phase 2 — the admissibility verdict: NO REPAIR; ESCALATED

The §3 decomposition leaves exactly one in-charter repairable object: the
commitment-realization dispersion (the B → A step; within-cell ~3.7–3.8 GW std net of
σ_R). The §1.4 rule is applied verbatim:

* **The only faithful identification source for that dispersion is realized commitment
  conduct** — the NP6-905-CD RTOLCAP telemetry or the CAMPD hourly online-headroom
  extracts (the same telemetry at unit grain; the derive script's identification gate is
  precisely that their headroom reproduces measured RTOLCAP). Both are measured OUTCOMES
  of commitment. The charter bars them from PARAMETERIZING a repair — validate-only.
* **None of the four admissible sources can produce it.** (i) The model's own commitment
  machinery: this posture runs no commitment pass, and the P1 LP is perfect-foresight —
  it contains no day-ahead commitment-realization process, so a σ_commit derived from its
  run patterns would measure within-cell net-load variation (an axis the share table
  already conditions on — a double-count), and could only reach the measured dispersion
  by being tuned toward it, which is the barred channel wearing a different coat. (ii)
  The forward AS model carries requirement QUANTITIES, no dispersion. (iii) No published
  methodology quantity states a year-ahead committed-capability dispersion — NP6-576-ER's
  σ is the intra-hour projection error, orthogonal by charter and held under E3. (iv) The
  outage machinery's dispersion is already carried by E4 (58.5 % of the within-cell
  residual); re-deriving from it would double-count.
* **Therefore the repair cannot be built without inventing a parameter → STOP.** Per §1.4
  this is recorded as an ESCALATION and Phases 0–1 land alone. No new `ScenarioConfig`
  field, no Phase-3 invocation (its precondition did not obtain), no matrix row owed
  under rule 28(c).

**De-prioritization evidence for the manager, from the decomposition itself:** the largest
model-side distortion of E1's reserve quantity on this arm is NOT the missing commitment
dispersion (~0.8–1.7 GW at p1) but the **storage-AS term inflation (~+7.3–8.8 GW at p1)**
— the correct 0.35 constant multiplied by the over-built evolved storage fleet, the same
FFR-4/5 lane object that keeps E2 inert. Fixing the storage fleet trajectory removes the
dominant E1 error with zero changes to E1 itself; the admissibility-orphaned commitment
share is second-order behind it, and at re-based tight screens the phys-headroom bound
already supplies more low-tail mass than the measured series carries.

## 5. Governance

* **Rule-1/13 posture kept.** Nothing was tuned toward 2.294 GW, the measured curve, the
  measured RTOLCAP distribution, or any residual; the §2 deltas — overshoots included
  (into-2024 mean $40.86 vs measured $26.82; margins 2× replica) — are measurements
  reported at full magnitude. The prereg (§1, `76d79b2`) and both probes (`797426c`) were
  committed before invocation 1 launched; the Phase-1 method was fixed before any dump
  existed; the decomposition ran once, as pre-registered, with its identity self-check
  exact.
* **The FFR-8A §4 record is superseded AS BASELINE by §2 of this doc** for any run at or
  after the FFR-3V epoch; it remains the valid record of the pre-epoch harness. The
  FFR-5D-M reproduction gate was not attempted, per charter — this doc's §2 is the new
  recorded baseline for the repair-arm recipe.
* **E3 remains ESCALATED/HELD** — the Phase-1 decomposition produced no direct evidence
  on it (§3), so it was not re-opened.
* **The Phase-2 escalation** (§4) goes to the manager with this record: the E1 commitment-
  dispersion repair has no admissible identification; the measured-conduct sources may
  only validate. The FH-4/FH-5 lift determination remains the manager's; no lift
  recommendation is made here (Addendum AF.2: the Phase-0 re-base is the lift evidence).
* **No arming, no promotion, no keeper contact, no backcast-registry touch.** One arm
  registered, hindcast namespace only. Bar re-levels and signal scaling stay REFUSED BY
  NAME; the λ-led conduct content stays out of scope.
* **Matrix duty (b)**: the `capacity_screen_scarcity_restoration` cell's evidence citation
  gains the re-base (this doc §2–§3 + the two probe JSONs); the cell stays `O` — measured,
  not adjudicated. No new row (no new field).
* **Session incident, recorded**: mid-session the remote branch was deleted server-side by
  an actor outside this session and pushes failed with HTTP 500 on the pack upload for
  ~15 min (traced via `GIT_TRACE_PACKET`); the branch was re-created via the API and the
  history force-with-lease-pushed over the placeholder once the transport recovered. All
  artifacts verified present on the remote afterward. No content was lost or rewritten.
