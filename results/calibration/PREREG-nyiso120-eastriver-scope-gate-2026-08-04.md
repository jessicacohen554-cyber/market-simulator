# PREREG — nyiso-120: the hybrid-cogen dark-fuel scope gate at NYISO, and which meter is wrong about East River's boundary

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry:** `2026-08-03-nyiso-118-seny-span`, CALIBRATED-WITH-CAVEATS,
C3c the sole ledgered caveat.

**Committed BEFORE any statistic in §4 was computed, before the derive was
re-run, and before any LP was solved.** Rule 23 `[R-FROZEN-DERIVE]`: the
re-derivation this session performs is motivated by a **scope-gate logic
change on measured grounds** (miso-122, 2026-08-04) and cites it — never by a
residual.

---

## §0 — why this session is at NYISO, and where the item comes from (rule 28(a))

The session brief opens on **NEISO**, whose lever queue is owner-gated end to
end: matrix §5.6 item 1 is SPENT (`R`, neiso-76), items 3/4/6/7/8 are closed,
item 2 is ceiling-bounded, and items 5, 5b and C3c-2023 all require an owner
green-light that is **not granted**. The brief therefore directs a **cross-ISO**
cell. This one is picked off **NYISO's** queue, and it was minted there one day
ago rather than chosen from a stale list:

> **miso-122 §7 handoff item 1** — "NYISO 2493 East River — a real defect… The
> gate therefore **excludes** it (`below_credited`) rather than correct it,
> which changes NYISO's applied map — 306 MW leaves it. **NYISO's artifact is
> deliberately NOT re-derived here** (rule 25): that is an input change to
> NYISO's keeper and needs NYISO's own A/B. **The open question there is which
> meter is wrong about East River's boundary, and it is not answerable from
> MISO's data.**"

Why this cell and not another: it is the only item on any non-owner-gated queue
that is (a) a **live input defect on a current keeper's armed mechanism**
(`measured_chp_heat_rates`, NYISO cell `K`), (b) fully **data-on-disk**
(`data/raw/campd-unit-level/NY_{2023,2024,2025}.parquet` + the committed eGRID
2023 plant sheet), (c) **zero new code and zero new parameters** — the gate was
built ISO-generically at miso-122 and is shipped exactly as committed, and
(d) carries a **306 MW NYC-zone** consequence on a lane whose sole ledgered
caveat (C3c) is a NYC price-tail question.

Rule 25 `[R-ISO-SCOPE]` is binding both ways: MISO's verdict fills **no** NYISO
cell, every statistic below is derived from NYISO's own data, and **no cell
outside NYISO is stamped by this session** — NEISO 1595 Kendall (miso-122 §7
item 2) stays in NEISO's lane, untouched.

---

## §1 — the object, stated from committed bytes only

From `data/raw/_processed-legacy/chp_power_only_heat_rates_NYISO.csv` (HEAD,
eGRID vintage 2023) and `FINDING-miso122-hybrid-cogen-scope-gate-2026-08-04.md`
§3 — nothing here is measured by this session:

| field | value |
|---|--:|
| plant / class / capacity | 2493 East River · `CT_CHP` · **306.0 MW** |
| `heat_input_electric_mmbtu` (eGRID `PLHTIAN`) | 22,845,485.1 |
| `heat_input_thermal_mmbtu` (eGRID `CHPCHTI`) | 13,493,030.8 |
| `net_mwh` (eGRID `PLNGENAN`) | 3,078,707.0 |
| `thermal_share` = CHPCHTI ÷ (PLHTIAN+CHPCHTI) | **0.371315** |
| `heat_rate_credited` = PLHTIAN ÷ PLNGENAN | **7.4205** |
| `heat_rate` as applied on the keeper today (all-fuel add-back) | **11.8032** |
| `cems_heat_mmbtu` / `cems_vs_egrid_total` | 36,338,515.9 · **1.0** |
| current `flag` | **`ok`** — i.e. **11.8032 is the rate the keeper charges** |
| miso-122's measured dark-fuel share, 2023/24/25 | 37.51 / 30.80 / 30.64 % |
| miso-122's gated rate, and why it excludes | 7.3763 **< 7.4205** ⇒ `below_credited` |

So the applied-map change under test is a single row: East River's offer heat
rate falls **11.8032 → 7.4205 (−37.1 %)** on 306 MW of NYC `CT_CHP`.

---

## §2 — the hypothesis, and its two rivals, written before the measurement

**H (double-count).** eGRID's `CHPCHTI` at East River **is** the direct-fired
boiler fuel, not a topping-cycle useful-thermal credit. If so, `PLHTIAN` is
already the power-train's fuel, `PLHTRT = 7.4205` is **already the power-only
rate**, the `measured_chp_heat_rates` add-back **double-counts** boiler fuel
into a power tranche, and the gate's exclusion is a **correction** — not a
reversion. H's sharp, falsifiable prediction: **CAMPD dark-boiler MMBtu ≈
`CHPCHTI`**, and **CAMPD power-train MMBtu ÷ `PLNGENAN` ≈ 7.4205**.

**R1 (genuine ambiguity).** The credit is a real topping-cycle steam credit
*and* there is separate dark boiler fuel. Then both meters are describing
different real things, the plant's boundary is genuinely ambiguous, the true
power-only rate lies **between** 7.4205 and 11.8032, and the exclusion is a
**fallback under uncertainty** rather than a correction. Under R1 the
correction still ships (it is the committed gate's own adjudicated logic) but
this session **may not** describe it as removing a double-count.

**R2 (selection artifact).** The behavioural dark-set selection
(`grossLoad` null/zero all year) has picked up a unit that does generate but
carries no gross-load channel. Under R2 the derive must **not** be re-run at
NYISO and the session stops at the measurement.

H, R1 and R2 are discriminated by KE1–KE3 below, all three of which are scored
**before** any solve.

---

## §3 — measurement construction, frozen here

1. **Dark set, behavioural, never a `unitType` allowlist** (rule 24
   `[R-REGISTRY]`): the derive's own committed rule — a CAMPD unit at facility
   2493 reporting `heatInput > 0` and `grossLoad` null-or-zero **for the whole
   year**. `unitType` is read only to *check* the selection (KE3), never to
   make it.
2. **Grain and vintage.** Unit-grain `data/raw/campd-unit-level/NY_<year>.parquet`
   for each of 2023, 2024, 2025 separately. The identity tests KE1/KE2 are
   scored at the **artifact's own vintage year, 2023**, because that is the
   only year `CHPCHTI` / `PLNGENAN` are published for in the committed sheet —
   no vintage mixing.
3. **Bands are reused, not invented.** Both agreement bands are **[0.90, 1.10]**
   — miso-118's committed two-meter band, already reused by miso-122's
   `_CEMS_RECONCILE_BAND`. No band is chosen after seeing a number.
4. **Shares, never MMBtu subtractions** (the derive's own convention): every
   comparison that crosses the two meters is a ratio, so CEMS's *composition*
   is used and its *level* is never required to equal eGRID's.
5. **The treatment is the committed gate, unmodified.** No threshold is added,
   no parameter is swept, and `scripts/data/derive_chp_power_only_heat_rates.py`
   is **not edited**. If the honest reading of the measurement were to require
   a different treatment than `below_credited`, this session STOPS and routes
   it — it does not re-cut the gate to change one plant's outcome.

---

## §4 — pre-registered kill rules

Scored in order. KE1–KE4 are **no-LP** and gate whether a solve happens at all.

| id | test | bar | what firing means |
|---|---|---|---|
| **KE1** | **the identity test** — CAMPD dark-boiler MMBtu ÷ eGRID `CHPCHTI`, 2023 | inside **[0.90, 1.10]** | **The H/R1 discriminator.** PASS ⇒ eGRID's "CHP credit" at East River *is* the boiler fuel and the add-back is a double-count. FIRE ⇒ **H is REFUTED**; the exclusion still ships (committed gate logic) but is reported as an R1 boundary-ambiguity fallback and the double-count claim is **withdrawn**, not softened. |
| **KE2** | **basis-matched two-meter power-only comparator** — (CAMPD power-train MMBtu ÷ eGRID `PLNGENAN`) ÷ `heat_rate_credited`, 2023 | inside **[0.90, 1.10]** | PASS ⇒ two independent meters agree the power-only rate is ~7.4, corroborating the reverted rate. FIRE ⇒ **neither** rate is corroborated; the session reports that and claims nothing about which is right. |
| **KE3** | **the dark set is boilers, and it is machinery** (miso-122's K1/K2, **re-scored on NYISO's own extracts** per rule 25) | ≥ 90 % of dark fuel in a boiler `unitType`; dark share non-zero in **all three** years; max/min ≤ **2.0** | FIRE ⇒ **R2 lives**: the selection is a reporting artifact, the derive is **not** re-run, and the session ends at the measurement with a negative result. |
| **KE4** | **re-derive no-op fidelity** — diff HEAD re-derive vs the committed NYISO artifact | **exactly one** applied-rate row changes (2493/`CT_CHP`, `ok`→`below_credited`); **zero** other flag changes; **zero** other applied `heat_rate` changes | FIRE ⇒ the re-derive is doing something unadvertised. **STOP before any solve** and report. |
| **KE5** | **attribution** — every A/B delta is measured against a **same-HEAD zero-delta control**, never against the committed keeper (`FINDING-nyiso114` §2: a P0-run-pattern keeper does not re-solve to byte-identity once main moves) | control-vs-keeper divergence is **measured and reported**, whatever it is | A non-zero control-vs-keeper divergence does **not** invalidate the A/B; quoting a delta against the keeper instead of the control **does**. |
| **KE6** | **direction** — the change strictly lowers one plant's marginal cost | East River `CT_CHP` energy must not **fall**; demand-weighted system λ must not **rise** by more than **1e-3 $/MWh** | FIRE ⇒ a wiring failure, not a result. Stop and diagnose. |
| **KE7** | **liveness, reported both ways** | report per-class **energy** deltas and max zonal **\|Δλ\|** against a **0.10 $/MWh** bar (miso-119/121/122's, reused for comparability) | **Pre-registered ahead of the number, in both directions:** an **inert** price result does **NOT** reverse the correction (rule 14 `[R-ACCURATE]` — an accurate input is never reverted because it failed to move a residual), and a **moved** gate does not by itself promote it (promotion additionally requires *nothing regresses*). |
| **KE8** | **rule 22** | 2023–2025 only; no out-of-training year solved, scored or read | NYISO holds a `complete` marker, so a keeper change obliges a `calibration-complete.json` re-key **with** a determination re-verification on committed artifacts only (D-5(b)). |
| **KE9** | **rule 23 / no residual conditioning** | the derive is re-run **once**, unmodified, citing miso-122's gate-logic change; no sweep, no threshold, no post-hoc re-cut | Any urge to re-cut the gate so East River lands differently ⇒ **STOP and route**, do not adjust. |

### §4.1 — the inconvenient null, declared in advance

The correction makes a **306 MW NYC-zone** unit **37 % cheaper**. The expected
direction is therefore **lower** NYC prices in the hours East River is
marginal — which runs **against** NYISO's sole ledgered caveat, C3c (too few
high-price tail hours). **Declared before the number: if C3c degrades, the
correction still ships.** Rule 1 `[R-STRUCT]` is explicit that a
structurally-correct mechanism is never rejected or reverted because the
residual moved the wrong way, and rule 14 `[R-ACCURATE]` is explicit that an
accurate input is not reverted for a worse fit. What a C3c degradation **would**
license is a root-cause question, not a revert.

Symmetrically: if C3c *improves*, that is **not** the grounds for promotion and
will not be quoted as the reason. The grounds are the measurement (KE1–KE3) and
rule 14.

---

## §5 — A/B design

* **Arm A (control)** — `scripts/replay_keeper.py results/calibration/nyiso118_seny_span`
  on the **committed, pre-gate** artifact. Same HEAD, same recipe, zero config
  delta. This is the baseline every number is quoted against (KE5).
* **Arm B (treatment)** — identical, on the **HEAD re-derived** artifact.
* **The delta is an INPUT FILE, not a `ScenarioConfig` key.** `measured_chp_heat_rates`
  is armed in **both** arms and its NYISO cell is already `K`; nothing is being
  armed. Consequently the two `run_config.json` scenario blocks must be
  **identical** and the artifact **sha256** must differ — an identical
  `run_config` is the **expected** result here, never a wiring failure
  (miso-122's inverted-K1 lesson, adopted).
* **Did it fire?** Answered by the loaded fleet's own rates pre-solve and by the
  `CT_CHP` class's own dispatch post-solve — never by a log line (the miso-113
  "hook invisible to the calibration path" hazard).
* **Both arms are registered on the dashboard this session** (rule 15), one
  bundle each, `--year 2023 2024 2025` in **one** invocation, years sequential
  (rules 12 + 16).

---

## §6 — governance

Rule 12: years sequential within each invocation; the two arms swap a
fixed-path input file, so they are run **sequentially**, not concurrently.
Rule 13 `[R-MEASURED]`: a plant's power-only heat rate is a physical property of
the machine and regenerates for a forward year from the same published pipeline;
no measured *outcome* enters any solve, and every measured price remains a
validation target. Rule 15: not done until both bundles + dashboard files are
committed and pushed **in this session**. Rule 16: all three training years, one
bundle each. Rule 22: training years only; the holdout spend freeze is ACTIVE
and untouched. Rule 26 `[R-DELETE]`: nothing is deprecated here, and the open
rule-26 queue (`neiso_oil_burn_budget`, `campd_facility_outages`) is **not**
touched — it is the owner's single decision. Rule 27 `[R-PUSH]`: no core file is
bulk-rewritten; every ≥300-line file is blob-verified after any push. Rule 28
duty (b): the `measured_chp_heat_rates` NYISO cell + citation is stamped in this
session **whatever the outcome**, rejections included.

**Session shorthand: `nyiso-120`** (the branch name carries the NEISO lane's
`neiso80` slug because the brief assigned it before the target ISO was chosen —
the work, the log entry and the matrix stamp are all NYISO's).

**Renumber, recorded rather than quietly rewritten.** This prereg was first
committed as `nyiso-119` (commit `e473d29f`). That shorthand is already SPENT on
main by the SENY-increment session
(`results/calibration/PREREG-nyiso119-seny-increment-2026-08-03.md` +
`nyiso119_seny_increment_construction_probe.json`), which the NYISO log's entry
headers do not yet carry — the log tail ends at nyiso-117 while the keeper shard
is at nyiso-118, so the log's own "next number" line was stale in both
directions and reading it would have collided either way. The collision was
found before any solve completed and before any dashboard registration. Nothing
in §1–§5 changed with the renumber; only the identifier did.
