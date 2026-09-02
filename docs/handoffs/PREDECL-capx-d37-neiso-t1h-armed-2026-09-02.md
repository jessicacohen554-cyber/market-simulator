# PRE-DECLARATION — capx D37: the NEISO T1-H re-measure with the D40 Net ICR requirement lever ARMED

**Lane:** capx D37 — the re-run three chains have been waiting for (GOLDEN-2 routed it;
FC-3's evidence carries the pre-arming leg; D40 built the lever and declared the post-wave
years UNSCOREABLE until this run; owner ruling **Q28** armed the lever FOR THIS MEASUREMENT
ONLY).
**Read first:** `FINDING-capx-d40-neiso-devintage-2026-09-02.md` (the lever, the screen-grain
consequence, the LOYO, the explicit D37 handoff line §6) ·
`FINDING-capx-d33-neiso-position-2026-09-02.md` (the census-supply-SHORT bound) ·
`PREDECL-capx-d27-miso-t1h-remeasure-2026-09-01.md` (the pattern this document copies).
**Session date:** 2026-09-02. **Branch:** `claude/capx-d37-neiso-t1h-armed-o98iy1`.
**Discipline:** D4-M — written and **pushed BEFORE the solve starts**. Every prediction below
is graded at full magnitude afterwards, misses included.

**What this session is NOT.** No mechanism is built. **No `ScenarioConfig` field is added or
moved and the SHIPPED DEFAULT of `neiso_net_icr_requirement` STAYS `False`** — Q28 arms it
*in this run's config only*, where it lands in `run_config.json` (rule 24). Rule 28 is not
triggered (the lever's row and six cells landed with D40). No FOM constant, retirement
threshold, execution lag or screen parameter moves. No keeper, no shard, no marker; the
backcast namespace is untouched.

---

## 1. The posture, resolved and verified BEFORE the solve

Two arms, launched concurrently (rule 12: separate invocations concurrent, years sequential
*within* each). Both at HEAD, both with the diagnostics sink on, differing in **exactly one
field** — the lever:

```
# ARM (the object)
uv run python scripts/run_capacity_hindcast.py \
  --iso NEISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --entry-screen-diagnostics --neiso-net-icr-requirement \
  --out-dir results/hindcast/neiso-2021-2025-realized-t1h-d37-armed

# CONTROL (HEAD, lever off)
uv run python scripts/run_capacity_hindcast.py \
  --iso NEISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --entry-screen-diagnostics \
  --out-dir results/hindcast/neiso-2021-2025-realized-t1h-d37-control
```

Recipe = the committed NEISO T1-H recipe (`neiso-2021-2025-realized-mystic-rescore`
meta: `variant=realized`, `vintage_year=2020`, `start 2021`, `end 2025`), every other
solve-affecting flag omitted so each inherits its shipped default. Solve years
`{2021, 2023, 2024, 2025}`, 2022 bridged, scored 2023–2025 (rule 22 — no out-of-training year
is solved, scored or registered; the holdout freeze is untouched).

**Why a CONTROL arm, which D27 could not afford.** The committed baseline was solved
2026-08-22; HEAD has moved since (D41's CCS constants, D34's carbon guard, D40's own landing).
Its bare-HEAD cache key today is `3f786c831cc93d46`, **not** the baseline's
`e118e887b306da37` — so a bare ARM-vs-committed diff would confound the lever with HEAD
drift. The control makes the A/B exact. Priced: NEISO T1-H is **0.95 h projected / 0.54 h
lower / 4.3 GB peak, `must_run_solo: false`** (FFR-3A-2 scorecard, criterion C). Host:
**15 GB RAM, 4 cores, 20 GB free disk** — 2 × 4.3 GB fits with ~6 GB headroom. If either arm
OOMs or exceeds ~2× its price, the session reports the failure and registers nothing rather
than trimming years.

### 1.1 Resolved cache keys — measured at HEAD, no solve

| arm | `entry_screen_diagnostics` | `neiso_net_icr_requirement` | cache key |
|---|---|---|---|
| bare HEAD | False | False | `3f786c831cc93d46` |
| diagnostics only (**CONTROL**) | **True** | False | `17f74b5ffc1808c9` |
| lever only | False | **True** | `3092c1728c10819a` |
| **ARM (D37 posture)** | **True** | **True** | **`0c08990cce1f1a18`** |

Neither arm's key collides with any committed NEISO bundle
(`e118e887b306da37` mystic-rescore, `b50062a643832c25` k99), and
`run_capacity_hindcast.py` redirects `cachemod.CACHE_ROOT` to `--out-dir`, so a fresh
out-dir cannot serve a pre-existing bundle at any key. Both out-dirs are verified
absent/empty immediately before launch. A realized key differing from the table above is
itself a reportable finding.

### 1.2 The `entry_screen_diagnostics` zero-cost precondition — VERIFIED, and the D36/D39 claim is HALF WRONG

The handoff states this as "the D36/D39 zero-cost precondition — output-only, no cache-key
term" and asks that it be verified against the cache-key registry before the solve. Verified,
both halves, and **they do not both hold**:

* **"Output-only" — TRUE, verified at source.** `evolve.py:726-730` allocates the sink only
  when the flag is on; `new_entry.py:974-976` guards every diagnostic write behind
  `_diag = screen_ledger is not None`; the sink is written by `.extend`/`setdefault`
  (`new_entry.py:1866-1868`) and **never read back into any decision**. `evolve.py:794`
  persists it into the year's ledger. The fleet outcome is byte-identical with it on.
* **"No cache-key term" — FALSE.** `entry_screen_diagnostics` is **NOT** a member of
  `_CACHE_KEY_OPTIONAL_FIELDS` (234 members, checked at HEAD), and that tuple is precisely
  the set of fields *dropped* from the hash at their default. A field absent from it is
  hashed **at every value**. Measured: bare HEAD `3f786c831cc93d46` → diagnostics-on
  `17f74b5ffc1808c9`. **Arming the flag moves the cache key.**
* **Consequence, stated plainly.** "Zero-cost" is true in the sense that matters for
  *correctness* (no fleet effect) and false in the sense that matters for *compute*: a
  diagnostics-on run can never reuse a diagnostics-off cached bundle. It costs this session
  nothing extra, because the lever already moves the key independently and both arms are
  fresh out-dirs — but a future lane that arms it expecting to reuse a cached bundle will pay
  a full re-solve. Registering the field in `_CACHE_KEY_OPTIONAL_FIELDS` at `"False"` would
  make the claim true as written; **this lane proposes it and does not do it** (rule 28 /
  cache-key registry edits are out of a measurement lane's scope).

### 1.3 CONFOUNDS and scope limits — declared before the run, not after

* The ARM-vs-CONTROL diff **is** attributable to the lever (one field apart, same HEAD,
  same recipe). The ARM-vs-`mystic-rescore` diff is **not** — it carries HEAD drift since
  2026-08-22 — and no causal claim will be made on it.
* **The CCS axis (handoff-requested note).** `ccs_retrofit_available_year = 2028` at HEAD,
  and this run's window ends **2025**, so the CCS retrofit screen is **structurally
  unreachable in every year of this run**. D41's repaired constants are live at HEAD
  (`fixed_om_gas_cc_ccs = 65.0`, `ccs_retrofit_capex_kw = 1521.4`, both verified) and this
  is the first NEISO capacity bundle solved on them, but on this axis the bundle is a
  **structural no-op, not a measurement**: the committed baseline records `ccs_retrofits: []`
  in all five years and the arm cannot produce a non-empty list. **Predicted: 0 retrofits in
  every year of both arms.** The constants' first real NEISO exposure is the T3 golden
  (2026–2050), not this run. Reported as such, never as evidence about the repair.

---

## 2. The baseline being re-measured (committed, OFF)

Two distinct objects, and the finding will not conflate them:

**(a) The verdict record at the bare `neiso-t1h` key** — session FFR-3A-2, `scored_at_sha`
`8ba592814d92`: determination **HOLD**; FC-3 **FAIL** (12 bands); FC-7 **FAIL**
(`run_config.json absent` + DOF-ledger CAVEAT); FC-1/FC-8 **SKIPPED**; FC-2/4/5/6 n/a. This
is the record D37 preserves-then-overwrites.

**(b) The numeric trajectory baseline** — `neiso-2021-2025-realized-mystic-rescore`
(`NEISO/e118e887b306da37`, solved 2026-08-22), the most recent committed NEISO T1-H bundle
carrying per-year evolution ledgers. Its score differs from (a) in two bands
(`add.by_tech.solar` PASS, `add.shares.gas_ct` PASS), i.e. **(a) and (b) are different runs**;
(b) supplies every model number below.

| year | bridge | peak | reserve margin | thermal before → after | exits | floor retained | entry (decided MW) |
|---|---|---:|---:|---|---:|---:|---|
| 2021 | no | 25,101 | 0.278277 | 28,328.9 → 28,328.9 | 0 | 0 | — |
| 2022 | **yes** | *(none)* | *(none)* | 28,328.9 → 26,888.9 | **1,440.0** | 0 | solar 514.0, wind 715.2 |
| 2023 | no | 23,475 | 0.305476 | 26,888.9 → 26,888.9 | 0 | 0 | gas_cc 1000, solar 514.0, wind 284.8 |
| 2024 | no | 24,255 | 0.029110 | 26,888.9 → 20,997.0 | **5,891.9** | 0 | solar 514.0, wind 715.2 |
| 2025 | no | 25,898 | 0.007767 | 20,997.0 → 21,997.0 | 0 | 0 | gas_cc 1000, gas_ct 500, solar 514.0, wind 284.8 |

Exits by fuel and reason (ledger-exact): **2022** gas_st 1,438.2 + biomass 1.8 (39 economic,
2 announced); **2024** gas_cc 5,100.4 + coal 791.5 (**all 57 economic**). Cumulative
**7,331.9 MW = 7.332 GW**, which is the scored `retire.total_gw` exactly. **80 % of the
model's entire retirement portfolio is the single 2024 economic wave** — the object the lever
targets.

Scored bands (b): `retire.total_gw` actual **4.997** / model **7.332** GW, err **+46.7 %**,
**FAIL** (band ±10 %) · `retire.false_retire` **4.175 GW = 56.9 %** of model, **FAIL** (max
15 %) · `retire.unit_recall_gt300` **0.667** (4/6), **FAIL** (min 0.70) · additions
`wind` 2.000 vs 0.225 FAIL, `solar` 2.056 vs 1.947 **PASS**, `gas_cc` 2.000 vs 0.000 SKIP,
`gas_ct` 0.500 vs 0.162 FAIL, **`storage` 0.000 vs 0.642 FAIL (−100 %, the channel is shut)**.
Per-fuel retirement model vs actual (GW): coal 0.791/0.846, gas_cc **5.100**/1.884,
gas_st **1.438**/0.480, gas_ct **0.000**/0.319, oil **0.000**/1.208, biomass 0.002/0.262.

### 2.1 The lever projected onto THIS trajectory (zero solves) — and why it is only a bound

Instrument: `docs/handoffs/d37/predecl-screen-grain-2026-09-02.py` (rows in the sibling JSON).
It evaluates HEAD's own committed resolvers and R2 vintage curves on the (b) ledgers. It
**self-checks** first, reproducing D33 §2's cross-validation: HEAD's curves at the REAL FCA
positions return the real clearing prices to the cent ($24.01 / $31.33 / $31.09).

| yr | peak | firm | req OFF | req ON | Δreq | Net ICR | pos OFF raw | pos ON raw | real | gap OFF | gap ON | $ OFF | $ ON | $ real |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 25,101 | 32,086.0 | 25,819.1 | 30,762.5 | +4,943.4 | 33,725 | 1.2214 | 1.0392 | — | — | — | — | — | — |
| 2023 | 23,475 | 30,646.0 | 24,146.5 | 29,636.0 | **+5,489.4** | 32,490 | 1.2455 | 1.0311 | 1.0451 | **+20.04** | **−1.40** | 0.00 | **42.07** | 24.01 |
| 2024 | 24,255 | 24,961.1 | 24,948.9 | 30,347.5 | **+5,398.6** | 33,270 | 1.0004 | 0.8381 | 1.0406 | −4.02 | **−20.25** | 103.63 | 167.18 | 31.33 |
| 2025 | 25,898 | 26,099.1 | 26,638.9 | 28,865.2 | +2,226.3 | 31,645 | 0.9815 | 0.9126 | 1.0368 | −5.53 | **−12.42** | 148.80 | 148.80 | 31.09 |

Read against **D40 §2's crossover table** (its 2023 = a clean, un-evolved base-year census;
this run's 2023 = a fleet already evolved through 2021–2022):

| row | D40 crossover OFF → ON | D37 T1-H OFF → ON |
|---|---|---|
| 2023 position gap | +21.43 → **−2.13** | +20.04 → **−1.40** |
| 2024 post gap | +6.29 → −12.52 | −4.02 → **−20.25** |
| 2025 post gap | −3.17 → −10.29 | −5.53 → **−12.42** |
| 2023 entry exit budget | 6,263 → 774 MW (**−88 %**) | 6,499.5 → **1,010.1 MW (−84 %)** |

**THE HONEST NOTE, stated before any prediction (the handoff asks for it explicitly, and it
is the load-bearing caveat of this lane).** D40's clean-entry figure — the artifact removed,
+21.4 → −2.1 pts — **does not guarantee the post-wave years, and this table is not evidence
that it does.** Three reasons, each measured:

1. Rows 2024 and 2025 above price a fleet **the OFF requirement produced**. The 5,891.9 MW
   2024 wave was rationed against a requirement 5,398.6 MW too small; under the arm that wave
   is inadmissible, so those ON positions (−20.25, −12.42 pts) describe a fleet **that would
   not exist under the arm**. They are an artifact-contaminated *bound*, not a forecast.
2. This trajectory is **more** contaminated than D40's, not less: the T1-H 2024 wave
   (5,891.9 MW) is **2.05× the crossover's** (2,877.7 MW), so the post-wave rows are further
   from anything the arm would produce.
3. The 2023 row here is itself **not** D40's clean census — it sits downstream of a 1,440 MW
   2022 bridged exit. That it still lands at −1.40 pts, within 0.73 pts of D40's clean −2.13,
   is corroboration that the denominator artifact is the dominant term; it is **not**
   independent confirmation, since both evaluate the same transform on the same registry.

**Only the re-solve can score the post-wave years. That is this lane's whole point, and every
prediction below is a prediction about the re-solve, never a restatement of this table.**

---

## 3. PREDICTIONS (graded at full magnitude afterwards, misses included)

**Standing note on the mechanism I am predicting through.** In the baseline's 2024 the wave
lands at `firm_post − req_OFF = +12.2 MW` — the exits are rationed to **within 0.05 % of the
requirement**, with `floor_retained` empty and 189 `entry_capped` events. Whether the rationer
is the admission cap ordering the candidate list or `_apply_reliability_floor` selecting on
`_floor_retention_merit` (D27's distinction), **the requirement is the binding quantity**;
the arm raises it by +5,398.6 MW on essentially the same entering fleet. Every magnitude
below is anchored on that identity, and inherits its limit: it bounds how much exit budget
the arm *withholds*, and says nothing about which units sit deepest below the bar.

### P1 — the 2024 economic wave collapses

* **Direction: DOWN, decisively.** Baseline 5,891.9 MW.
* **Magnitude: 0.2–1.5 GW, central ≈ 0.6 GW** — the baseline wave less Δreq (+5,398.6 MW),
  credited back the ≈139 MW of 2022 exits the arm also forbids (P2).
* **FALSIFIER:** the 2024 wave stays **> 4.0 GW** ⇒ the requirement is **not** the binding
  rationer of the wave at HEAD, D33 §3.3's attribution of the oscillation to the denominator
  is wrong on this trajectory, and the arming recommendation must be re-opened rather than
  confirmed. Reported as a MISS, not re-narrated.

### P2 — the 2022 bridged wave also shrinks (the year D40's crossover never saw)

* The published resolver needs **no peak** (the auction's own denominator), so it resolves in
  a bridged year too: 2022/2023 Net ICR 33,750 → req_ON **30,785.3 MW** against an entering
  firm of 32,086.0 ⇒ budget **1,300.7 MW**, against a baseline wave of **1,440.0 MW**.
* **Prediction: 2022 exits fall, to 0.0–1.31 GW, central ≈ 1.1 GW** (the floor caps at
  1,300.7 MW; the ~$30–40/kW-yr of capacity revenue the arm creates at a 1.0386 position
  deters some gas_st units from deciding to exit at all).
* **FALSIFIER:** 2022 exits stay at exactly 1,440.0 MW ⇒ the bridged year does **not** see
  the armed requirement, which would be a **defect in the lever** (a year evolving outside its
  own gate) and is routed as one, not absorbed.

### P3 — `retire.total_gw`, the headline band

* **Model FALLS from 7.332 GW to 1.0–3.5 GW, central ≈ 2.0 GW** (P2 + P1: ≈1.1 + ≈0.6, plus
  the 2 announced 2022 rows).
* Against the 4.997 GW actual that is **−80 % to −30 %, central ≈ −60 %**.
* **Band: FAIL, WITH THE SIGN FLIPPED** — from **+46.7 % over**-retirement to
  **under**-retirement. This is the same shape D27 found in MISO and for the same structural
  reason: a requirement repair **rations** a channel, it does not **aim** it.
* **Pre-registered alternative, which I judge ≈20 % likely:** the collapse stops inside the
  ±10 % band (4.497–5.497 GW) and `retire.total_gw` **PASSES**. If that happens it is recorded
  as a MISS on magnitude and a hit on direction, and it does **not** license calling the object
  closed, because P4's composition test still governs.

### P4 — composition: `false_retire` improves a lot and still FAILS; recall gets WORSE

* `retire.false_retire` **falls from 4.175 GW / 56.9 % of model** to **0.3–1.2 GW**, because
  the entire gas_cc excess (5.100 vs 1.884 actual = 3.216 GW) is inside the 2024 wave P1
  removes. **As a fraction of a much smaller model total it stays above the 15 % band ⇒ still
  FAIL**, central ≈ 40 %.
* `retire.unit_recall_gt300` **falls from 0.667** (already FAIL at band 0.70) to **0.17–0.50**:
  the ≥300 MW targets the model was covering are covered *by* the wave being removed. **The
  arm makes this row worse, and I say so before the run.**
* **The composition defect is untouched.** Model `oil` (0.000 vs 1.208 actual) and `gas_ct`
  (0.000 vs 0.319) stay at **exactly 0.000 GW** in both arms — a requirement-side lever cannot
  open a channel the merit key never selects (D27's measured mechanism). **FALSIFIER:** either
  becomes strictly positive.

### P5 — the additions legs, and the one channel the arm could actually OPEN

* **`add.by_tech.storage` — the interesting one.** Baseline **0.000 GW vs 0.642 actual
  (−100 %, FAIL)**. Storage entry is a value stack that includes **RA capacity value**, paid
  because NEISO has a capacity market; the arm takes the capacity price from **$0.00** to
  **≈$42/kW-yr** at the 2023 entering position. **Prediction: storage entry becomes STRICTLY
  POSITIVE, 0.1–1.5 GW, central ≈ 0.5 GW.** I give it **≈45 %** to land inside the ±25 %
  storage band (0.482–0.803 GW) and **PASS**. **FALSIFIER:** storage stays exactly 0.000 GW ⇒
  the storage channel is shut by something other than capacity revenue, which is a new
  identified object (route it; do not tune this lever to it).
* `add.by_tech.gas_ct`: 0.500 GW baseline → **UP or flat (0.4–1.5 GW)**, **stays FAIL**
  (actual 0.162, band ±15 %).
* `add.by_tech.wind`: 2.000 GW → **roughly unchanged (1.5–2.5 GW)**, **stays FAIL** (actual
  0.225) — VRE entry is RPS-driven and `entry_vre_capacity_revenue` is **False** for NEISO,
  so the lever reaches wind/solar only through energy prices.
* `add.by_tech.solar`: 2.056 GW → **near-unchanged (1.7–2.4 GW)**; PASS in baseline (b),
  and I predict it **stays PASS**, though it is close enough to the band edge that I flag it.
* `add.by_tech.gas_cc`: 2.000 GW → up (2.0–4.0 GW); **band stays SKIP** (actual 0.000 ⇒
  `err_frac` null).

### P6 — floor binding and the diagnostics evidence

* **`floor_retained` becomes NON-EMPTY in at least one year of the ARM** (it is empty in
  every year of the baseline and, I predict, of the control). Most likely 2022 and/or 2024.
* **`entry_screen_diagnostics` rows are present in every evolved year of BOTH arms** — this is
  the precondition's payoff, and the per-candidate decomposition is what will attribute the P5
  storage outcome to a term rather than to an argument.
* End-of-window `reserve_margin` **rises materially** from the baseline's 0.007767 (2025) —
  predicted **0.10–0.30** — because the floor now holds the fleet at a requirement ~2.2 GW
  higher.

### P7 — capacity revenue at the corrected positions

* At the **2023 entering** position the ARM pays **$20–55/kW-yr, central ≈ $35**, against the
  real FCA 14 clearing of **$24.01** — i.e. **the curve OVER-pays**, the direction D40 §2
  reading 5 pre-stated. D40's crossover figure was $55.20; I predict **lower** here, because
  suppressing the wave leaves a **fuller** fleet, a **longer** position, and ISO-NE's MRI curve
  is steep on that segment.
* **If the arm lands at ≈$42+/kW-yr against $24.01 while the floor retains ~2 GW the real
  market de-listed, that is the R-C / de-list wedge** (D33 §3.2's measured
  census-supply-SHORT bound; D28's clearing half) — **routed to the director as the next
  object, NOT tuned into this lever** (D40 §6, verbatim).

### P8 — verdict rows and cross-lane safety

* **FC-3 STAYS FAIL.** `retire.total_gw` predicted out of band with its sign flipped;
  `false_retire` and `unit_recall_gt300` predicted FAIL; the wind/gas_ct addition bands are
  untouched by a requirement-side lever.
* **FC-7 row 1 `run_config` FLIPS FAIL → PASS by construction** (the harness now writes
  `run_config.json`; the FFR-3A-2 leg predates that). The DOF-ledger row stays **CAVEAT**, so
  **FC-7 goes FAIL → CAVEAT**. This is an **INSTRUMENT change, not a model improvement**, and
  will be labelled as such.
* **FC-1 and FC-8 stay SKIPPED** (this harness emits no `summary.invariants` and no
  `total_wall_s` perf ledger).
* **Determination STAYS HOLD** (FC-3 FAIL is sufficient on its own).
* **No verdict outside `neiso-t1h`'s own rows moves.** If one does, the session **STOPS and
  ROUTES** (cross-lane re-grade) rather than writing it.

### P9 — the arming question the owner actually asked

* **I predict the measured evidence will NOT support flipping the shipped default in this
  session**, and that the honest recommendation will be *keep the default OFF, keep the lever
  armed for the NEISO forecast lane's next measurement*. Basis: P3/P4 predict the lever
  **relocates** NEISO's FC-3 failure (over- → under-retirement) rather than closing it, and
  rule 22 puts the burden on a **clean held-out score** before a default moves.
* **The condition that would change that recommendation, pre-stated so it cannot be traded
  after the fact:** `retire.total_gw` lands **in band** (P3's 20 % alternative) **AND**
  `false_retire` lands **in band** **AND** the LOYO over 2023–2025 on the armed fleet shows no
  fold degrading. Any two of three is **not** enough.

---

## 4. Registration plan (frozen here)

**Preserve-then-overwrite, the NEISO-RC-R / D27 pattern.** The current `neiso-t1h` verdict
record is preserved **verbatim** under **`neiso-t1h-pre-d37`** — a PRESERVED BASELINE, never
quoted as current state — and the armed re-measure takes the **bare `neiso-t1h`** key via
`scripts/register_forecast_run.py`, with the NEISO board block refreshed. The control arm is
registered under its **own** id and is **not** pointed at any bare per-tier key (a run must
never render a verdict its own score contradicts). Every other ISO's rows are untouched.
Run ids: **`neiso-2021-2025-realized-t1h-d37-armed`** (bare key) and
**`neiso-2021-2025-realized-t1h-d37-control`**.

**STOP condition (handoff, binding):** if anything beyond `neiso-t1h`'s own rows would flip,
the session stops and routes it as a cross-lane re-grade rather than writing it.

## 5. Kills

* **K-a — solve budget.** Two T1-H legs, priced. If either OOMs or exceeds ~2× its price, the
  session reports the failure and registers nothing rather than trimming years (rule 16's
  spirit: the window is the window). If only the CONTROL is lost, the ARM is still registered
  and every ARM-vs-committed number is labelled confounded (§1.3).
* **K-b — no parameter moves.** If any prediction misses in a direction that "wants" a tuned
  constant, that is an open root-cause issue routed onward, never a parameter (rule 21). The
  shipped default of `neiso_net_icr_requirement` stays `False` whatever this run measures;
  flipping it is an owner decision on the evidence, and this lane only recommends.
* **K-c — no cross-lane writes.** `neiso-t1h` key + NEISO board block only. D42 (MISO) and
  D43 (CAISO) share no files; a conflict on `docs/` or `ff-verdicts.json` is **rebased**,
  never resolved in another lane's favour.
* **K-d — rule 22.** No out-of-training year is solved, scored or registered; nothing is
  scored against measured H1-2026; the holdout freeze is untouched.
* **K-e — rule 27.** Local edits, exact on-disk bytes pushed; any pushed file ≥300 lines is
  blob-verified against the remote before the next commit.
