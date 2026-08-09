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
produced.)*
