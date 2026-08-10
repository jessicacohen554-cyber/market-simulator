# FFR-9C — execute the VRE-entry repair menu (R-a/R-b/R-d) as a staged paired-arm program

**Session.** FFR Wave 9, staged repair lane (manager dispatch Addendum AI.2,
under the owner-re-opened D-21(a) completion mandate — the repair charter
FFR-9B §4 named). Branch `claude/ffr-9c-vre-entry-repair-3r3uy8`, off
`origin/main` `aa61791e`. Model: Fable (rule 27 — capacity-evolution core).

**Charter.** Execute the FFR-9B §4 repair menu as a STAGED paired-arm program
on the ffr9a-storageseed posture (the control posture of record): a verbatim
control, then stage A (+R-a), then stage B (+R-b, +R-d), each a paired read
against the same control. **NO promotion into any shipped default this
session** — every repair is armed BY INVOCATION in measurement arms;
promotion is a later manager/owner act on this lane's evidence. **NO tuning
toward 55.4 GW or any actual.** Evidence base, cited never re-derived:
`docs/handoffs/ffr-9b-vre-entry-diagnosis-2026-08-09.md` §3 (the binding
table) and §4 (the menu, with rule-13 pre-assessments);
`docs/handoffs/ffr-9a-storage-vintage-seed-2026-08-09.md` §1.3/§2–§3 (the
control recipe and its registered reads).

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. The stage-B code (the R-b gate) was built,
regression-tested and committed before this prereg (`9ba23986`) — it is a
GATED default-off field armed only by invocation, with zero parameters
identified from any solve this session runs (the armed value 2030 is the
published ATB availability year). The FFR-9B replay probe's staged-arm
passthrough extension (additive; defaults reproduce the FFR-9B construction
byte-for-byte) is committed with this prereg, before any solve.*

### 1.1 The stages (three cold invocations, one recipe head)

All three arms run VERBATIM at this branch head, sequentially in this
container (15 GB RAM / 4 cores — FFR-9A's measured constraint; rule 12's
≤2-concurrent cap is therefore not exercised), 4 LP solve-years each
(2021, 2023, 2024, 2025; 2022 bridged), years SEQUENTIAL within each
invocation (rule 12). Prerequisites first: `uv sync`, then a COLD
`scripts/regenerate_clean.py`. Each arm gets a FRESH `--out-dir` (the D-13
same-key/stale-bundle hazard — never a surviving FFR-9A/9B dir).

```
# CONTROL (invocation 1) — the ffr9a-storageseed recipe VERBATIM
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9c-control

# STAGE A (invocation 2) — control + R-a (the FFR-5C flag; zero new params)
  ... --entry-pipeline-aware-signal \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9c-pipeline

# STAGE B (invocation 3) — stage A + R-b (SMR gate, ATB-cited 2030)
#                                  + R-d (FFR-5E procurement, vintage 2020)
  ... --entry-pipeline-aware-signal --smr-available-year 2030 \
  --vre-procurement-additions \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9c-full
```

**Pre-registered runtime cache keys** (computed pre-launch through the
runner's own resolution path — `build_config` → `resolve_policy_bundle` →
`apply_iso_scenario_defaults` — at commit `9ba23986`):

| arm | runtime key | why |
|---|---|---|
| control | `816031a3308cccde` | MUST equal the FFR-9A/9B registered key exactly — the R-b field is registered-and-dropped-at-default, so the verbatim recipe's key is untouched (verified by the cache-key-pin verdict: default pin `603c2498bf71d21d` unmoved, `check_cache_key_registration` 159 fields clean) |
| stage A | `3301180d9f501bcd` | `entry_pipeline_aware_signal=True` enters the hash — a distinct scenario |
| stage B | `d6bc5469694eeedb` | + `smr_available_year=2030` + `vre_procurement_additions_enabled=True` |

The runtime `cache_key=` line of each arm and the ledger path
`<out-dir>/ERCOT/<runtime-key>/` are verified against this table before any
ledger is believed. A DIFFERENT key is diagnosed before proceeding, not
explained away.

**Reproduction gate (control, BY CONTENT).** The control must reproduce the
FFR-9A registered treated-arm reads with zero field diffs: the three probe
records re-run verbatim on the control bundle and deep-compared against the
committed `docs/handoffs/ffr-9a/{storage-trajectory,rebase-reads,e1-dispersion}-treated.json`
(every key except `cache_dir`/`bundle` path strings). Additionally the
control's `score.json` `additions` / `additions_cod_basis` /
`additions_basis` blocks must equal the registered
`ercot-2021-2025-t1ff-armr-ffr9a-storageseed` sidecar's field-for-field.
Reproduction failure is diagnosed before ANY stage comparison is believed.

**Stage-B build note (the netting first-read).** R-d's admissibility is
adjudicated (owner D-18(a)); the FFR-5E-H DEFER caveat ("netting vacuously
satisfied") does not carry to ERCOT per FFR-9B §4 — the ERCOT merchant
screen demonstrably decides at every hot screen, so the §2.3(b) budget
netting IS exercised here and its behaviour is a FIRST-READ, reported at
full magnitude whatever it shows. The vintage-2020 committed pipeline the
channel can see was 6,575 MW at the shipped vintage (FFR-5E measurement);
the vintage-2020 sheet's committed 2021–23 cohort magnitude is itself a
first-read.

### 1.2 Pre-registered reads R1–R5 (each stage vs the same control)

All reads come from the arms' own ledgers/dumps/score.json and four probes
re-run VERBATIM per arm (`ffr8b_rebase_reads.py`, `ffr8b_e1_dispersion.py`,
`ffr9a_storage_trajectory.py`, `ffr9b_entry_screen_replay.py` — the last
with the arm's matching stage flags, so the replay runs under the gates the
solve carried). Records land under `docs/handoffs/ffr-9c/` as
`<probe>-{control,pipeline,full}.json`. Every delta is reported at FULL
MAGNITUDE; expectations are to test, never targets.

* **R1 — additions decision basis per tech per year vs 55.4 GW actual**
  (reported, never targeted): decision-grain MW by evolution step from each
  arm's ledgers (the replay record's `ledger_decided_mw`), plus the
  score.json per-tech totals, laid against the FFR-9B §3 control table.
  Expected stage-A signatures (FFR-9B §4 R-a, pre-registered): solar
  ~5/5/5/· with the 53-MW crumbs GONE; the C/L alternation KILLED (per-tech
  effective rate C, not C/2 — the FFR-5C MISO-wind law); wind's 2023
  queue−pending clip gone. Expected stage-B signatures: nuclear_smr decided
  = 0 at every step (the 2030 gate clears the whole window), its 2.0 GW
  queue cap and ISO-budget share freed; the procurement channel injects the
  vintage-2020 committed cohort as `source: "procured"` rows (magnitude a
  first-read).
* **R2 — the FFR-9B binding-layer census re-run** (which cap binds NOW):
  the replay probe per arm with `screen_ledger` diagnostics, identity check
  (replayed build MW == ledger decided MW per (step, tech), under BOTH
  reserve-leg bounds) — when the identity holds the margins/ordering/
  `binding_cap` labels are authoritative; a failure is reported and the
  labels degrade to arithmetic attribution from ledger state (the FFR-9B
  §1.4 R3 fallback, carried verbatim). Stage A expectation: the
  queue-cap-minus-pending binder class VANISHES (netting relocated); the
  static queue caps and the ISO budget become the binder set at hot
  screens.
* **R3 — the price-side read set**: per-screen (into-2022/2023/2024/2025)
  mean / max / h>$100 / h>$1000 / adder mean, and the per-fuel replica
  margins vs the FFR-6A bars and replica-at-measured-prices columns
  (2024: 75.4/86.7/65.6/65.6, 2025: 97.2/76.4/47.0/47.0 $/kW-yr; measured
  2024: 161 h>$100, mean $26.82, max $3,060; 2025: 217 h, $32.49, $1,570).
  Expected direction (9B §4 R-a): the into-2024-class overshoot DEFLATES —
  the pro-forma prices its own committed pipeline instead of re-deciding
  it — and **gas_cc entry falls WITH the deflation** (R-e: the CC
  over-entry gets NO dedicated lever; it must die of the screen level or
  the R-e claim is refuted). Reported at full magnitude either way.
* **R4 — exits**: in-window economic executions must stay ≈ 0 — ANY
  in-window economic execution is a FALSIFICATION signal per FFR-7C, never
  a success; the gas_st false wave stays gone; the `entry_capped` census
  and per-year reserve margins reported.
* **R5 — the E1/E2 reserve-quantity reads** (the FFR-9A probes re-run
  verbatim): E1's reserve quantity vs the measured series (2024 mean
  16,703 vs 16,679 measured in the control's baseline), the B̃-vs-B
  storage-term step, and E2's `as_hold` liveness per screen. Expected
  direction: as the stages build more VRE mid-window, the screens' scarcity
  content falls and the storage-AS term moves with the (unmodified) storage
  stack's response; magnitudes are first-reads.

**Storage is context, not object**: the storage entry stack is not modified
by any stage; its trajectory (ffr9a_storage_trajectory per arm) is reported
because the deflating screens are expected to move its cap-saturated
profile, and that movement is evidence for the FFR-9A §3.1 routed finding —
not something this lane tunes.

**Leave-one-year-out (rule 22).** Any stage this handoff proposes for
promotion is scored LOYO within 2023–2025 IN THE HANDOFF (no promotion
performed): the stage-vs-control deltas on the scored metrics are tabulated
per scored year (2023 / 2024 / 2025) to show the movement is not
concentrated in one training year. The stages carry zero fitted parameters
(R-a relocates a guard; R-b is a published year; R-d has zero free
parameters), so LOYO here is a robustness demonstration, not a fit-selection
loop — but it is still owed before any promotion recommendation.

### 1.3 R-c (solar queue cap) — explicitly NOT this session's to change

`QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"]` stays 5.0 whatever the reads
show. IF stage A's measured solar throughput still caps below the EIA-860
2025 demonstrated record (actual solar CODs 7.29 / 7.74 GW/yr in
2024/2025, FFR-9B §3.1), this handoff WRITES THE RE-DERIVATION CASE for the
manager — rule 23: from source data only (the EIA-860 record of
demonstrated interconnection throughput), never from the residual — and
touches no constant.

### 1.4 Holdout posture

Solve years per arm: {2021, 2023, 2024, 2025} — training-tier years plus
the enumerated hindcast seed year; 2022 bridged, never solved, no market
data for it read (the 2022 EVOLUTION ledger — bridge-year fleet
bookkeeping — is read, as FFR-9A/9B's R1 probes already did). The holdout
freeze state is read at launch; no marker is spent; no out-of-training year
is approached. 2026+ is not touched in any arm.

### 1.5 What this lane will NOT do

No promotion, no shipped-default move (so NO epoch on other lanes — the
FH-4 sibling legs run concurrently on other ISOs and are not re-based by
anything here: every repair is invocation-armed, cache-key-separated, and
the control's key is byte-identical to the registered posture of record).
No tuning toward 55.4 GW or any actual. **Bar re-levels, signal scaling,
and residual tuning are REFUSED BY NAME.** No backcast-registry touch, no
keeper contact. R-c's constant is not moved (§1.3). If a stage cannot be
built without inventing a parameter: STOP, record it, land the prior
stages — the earlier stages' registrations stand on their own.

**Registration commitment.** ALL solved arms register in the HINDCAST
namespace (`scripts/register_hindcast.py`, ids
`ercot-2021-2025-t1ff-armr-ffr9c-{control,pipeline,full}`) REGARDLESS of
what the reads show. NEVER the backcast registry — the backcast CI gates
stay blind to this namespace. Commits land stage by stage (prereg →
results → handoff as they exist); pushes are small-pack `git push` after
fetch+rebase; no `push_files` on ≥300-line files; no new workflows.

**Matrix duties.** Duty (c) for the R-b field was discharged in the same
commit as the field (`9ba23986`: row `smr_available_year`, cells all U).
Duty (b): the session that tests a mechanism updates its cell + citation in
the same session — after the stages run, the ERCOT cells of
`entry_pipeline_aware_signal`, `smr_available_year` and
`vre_procurement_additions` move U → O (measured, verdict left to the
manager) with this handoff as the citation. No cell claims K/R from a
measurement lane.

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*
