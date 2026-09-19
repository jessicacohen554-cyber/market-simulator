# RESULT — nyiso-241: the CT_PEAKER merit collapse, two grounded arms solved

**Session** nyiso-241 (orchestrator; rule 32 `[R-SHARD]` (a) — **zero LP in this container**).
**Date** 2026-09-19. **Pre-registration** `docs/PRECOMMIT-nyiso241-ct-peaker-merit-2026-09-19.md`,
pushed at `5356fb712f8ff3ad2b785421d34ed9b4cae71f4c` **before either LP**.

**Incumbent keeper** `2026-09-17-nyiso240-bench-attribution` — **UNCHANGED**. Nothing is promoted
in this session; **the promotion decision is the owner's and it is open (§7).**

---

## 1. THE HEADLINE

| | determination | C1 | C2 | C3a | C3b | C3c | C4 | C6 | C8 |
|---|---|---|---|---|---|---|---|---|---|
| **keeper** | **CALIBRATED** | PASS | PASS | PASS | PASS | CAVEAT | PASS | PASS | PASS |
| **ARM A** committed-only | NOT-YET | PASS | PASS | **FAIL** (2022 only) | **FAIL** (2022 only) | FAIL | PASS | PASS | PASS |
| **ARM B** three-band | NOT-YET | **FAIL** | PASS | **FAIL** (2022, 2025) | **FAIL** (2022, 2025) | FAIL | PASS | PASS | **FAIL** |

* **ARM B is REJECTED on its own pre-registered gates**, its named risk included. Its two matrix
  cells stay `R` and their nyiso-200 re-test condition is now **SPENT** (§4).
* **ARM A is a clean structural repair whose cost is two hair's-breadth 2022 crossings** (§3). Its
  cell moves `U` → `O`, and what to do about it is a judgement this session does not make.

---

## 2. PHASE 0 — ZERO LP, AND IT RE-AIMED THE LEVER BEFORE ANYTHING WAS SOLVED

Eight probes on committed artifacts plus sanctioned `run_year(..., fleet_only=True)` rebuilds of
the keeper's own recipe. All records committed under `results/calibration/_nyiso241_*.json`.

**2.1 The energy is not in the band the handoff's lever moves.** CT_PEAKER's `committed` band
carries **3.2 / 7.7 / 11.8 / 21.1 %** of the class's energy (346.7 MW of 3,034.0 MW, 11.4 %). The
rest is in `econlo`/`econhi`, already at the registered neutral 1.0.

**2.2 The object's dominant carrier is the fuel basis, and it is correct.** The CT fleet is charged
**+1.00 / +1.40 / +2.04 / +2.57 $/MMBtu** over the CC/ST fleet in 2022–2025 while Transco Z6 NY
falls 6.86 → 1.98 — a premium that does NOT fall with the hub and that, at HR 15.8, is
**$16–41/MWh** of merit disadvantage. It is `nyiso_downstate_ct_gas_daily`'s measured LDC non-firm
transport rate, and its growth tracks the published KEDLI/KEDNY rate steps (0.16080 → 0.22310
eff 2024-09 → 0.28530 eff 2025-04 $/therm). **DO-NOT-REDO (2026-08-19) and not re-litigated.**

**2.3 `ST_GAS` pays EXACTLY ZERO startup amortization** while CT's `committed` rows pay
**$11.97 / $16.48 / $15.78 / $13.22** per MWh. Tempting and **not re-tested**:
`gas_st_startup_cost` is DO-NOT-REDO for NYISO (nyiso-172, two independent refusals — direction on
the code, and grounding degenerate at model = measured = 1 start) and this session offers no new
grounding evidence. What the measurement DID establish is arm A's second ground: the 1.35 hurdle is
a **second charge for a start those rows already pay**.

**2.4 THE REACHABILITY BOUND — declared before the solves and it forecloses both arms.** Against
the keeper's own hourly prices, with the fleet running flat out in every zone-hour its offer clears
(no min-run, no ramp, no start, no competition — the LP can only do less):

| year | actual | control | arm A frozen / relaxed | arm B frozen / relaxed |
|---|---:|---:|---:|---:|
| 2022 | 2.829 | 2.507 (89 %) | 3.119 / 3.320 (110 / 117 %) | 8.507 / 8.708 (301 / 308 %) |
| 2023 | 2.114 | 0.264 (12 %) | 0.334 / 0.544 (**16 / 26 %**) | 1.121 / 1.330 (**53 / 63 %**) |
| 2024 | 1.911 | 0.340 (18 %) | 0.445 / 0.646 (**23 / 34 %**) | 1.066 / 1.267 (**56 / 66 %**) |
| 2025 | 2.812 | 0.901 (32 %) | 1.010 / 1.145 (36 / 41 %) | 2.986 / 3.122 (106 / 111 %) |

**Even arm B leaves the 2023/2024 upper bound at 53–66 % of metered energy**, so **at least a third
of the object is not offer-reachable at all.** The residual belongs to the price side (the ledgered
C3c tail: model 7 / 0 / 0 / 3 h > $300 against 101 / 10 / 13 / 42 actual) or to a commitment /
local-reliability obligation. Recorded so no later session reads a favourable C1 move as the object
closing.

---

## 3. ARM A — `nyiso_ct_peaker_committed_measured`

`committed` 1.35 → NYISO's own registered `phys_committed` **0.843**; `econ_low`/`econ_high` stay
at the neutral 1.0, `peak` at the $1,000-offer-cap wall 4.0.

**GROUNDS, BOTH PRE-REGISTERED, NEITHER THE RESIDUAL.** (1) Rules 14 `[R-ACCURATE]` / 25
`[R-ISO-SCOPE]`: 1.35 reads "NYISO/CAISO-grounded" here, "NYISO-grounded" in CAISO's curve and
"NYISO/CAISO-grounded" in NEISO's — a three-way ring in which **no ISO cites a measurement** — and
1.35/0.843 = **1.60** is the largest such ratio in the model. (2) Rule 19 `[R-ONE-MECH]`: the
measured startup double count of §2.3.

**ZERO new literals, ZERO free parameters**, `authorized_price_tuning` **NONE** (nyiso-232
precedent). **G-STRUCT PASSED pre-solve and was recorded before the result**: 22 rows move, all
CT_PEAKER `committed`, **max |Δ| exactly `$0.00e+00`** in every other band, group and ISO, all four
years.

**MEASURED.** CT_PEAKER 2.429 → **3.054** / 0.246 → **0.360** / 0.300 → **0.457** / 0.771 →
**0.893** TWh: **6.1 / 9.7 / 6.0 %** of the 2023/24/25 miss closed, and 2022's absolute miss
0.400 → 0.225. That is inside the pre-registered 5–15 % and matches the caiso-241 sibling's
7.6 / 6.6 / 7.0 % on an 11.0 %-of-class band. **C1 PASSES in every year; C2, C4, C6, C8 PASS.**

**THE COST, AT FULL MAGNITUDE.** The determination falls **CALIBRATED → NOT-YET on 2022 alone**, on
two crossings of bands the keeper was passing by a hair:

| | keeper | arm A | band | keeper headroom |
|---|---:|---:|---|---:|
| C3a 2022 | −9.7 % ($73.22) | **−10.8 %** ($72.38) | ±10 % | 0.3 pp |
| C3b 2022 | 0.196 | **0.201** | ≤0.20 | 0.004 |

The mean price moves **−$0.84/MWh**. Every other year is essentially unmoved: C3a 2023 −2.1 →
−2.3, 2024 −0.2 → −0.4, 2025 −9.4 → −9.6 %; C3b 2023 0.124 → 0.124, 2024 0.162 → 0.163, 2025
0.168 → 0.171. **C3c's FAIL is a mechanical consequence, not a third defect**: with C3a and C3b
failing, rule 22 `[R-C3C]`'s lone-failure guard stops applying and the same miss that reads CAVEAT
on the keeper reads FAIL here.

**The downward price direction was the field's DECLARED HAZARD, never its case** — its own CLI help
and `ScenarioConfig` comment say so, and the PRECOMMIT repeated it. The C3a hole it exposes is the
OPEN ROOT CAUSE `_NYISO_OFFER_CURVE`'s own comments name: **NYISO scarcity/reserve (RCPF/AS) price
formation, issue #1344** — not a CC or CT energy markup.

---

## 4. ARM B — the three-way, REJECTED on its own gates

`nyiso_ct_peaker_bands_measured` (`committed` 0.843, `econ_low` 0.661, `econ_high` 0.658) +
`cc_duct_peaking_row_scoped`, over `nyiso_gas_bridge_startup_aware` already armed on the keeper.

**The rule 28(a) new evidence was real**: nyiso-200 stopped this pairing because its run-screen
partner was not yet on the keeper, and `nyiso240_benchfix_span/meta.json` now carries it. The
"never alone" limb was honoured. The "span only if the 2025 screen clears" staging was **spent**
rather than satisfied — rule 29 `[R-SCREEN]` was removed 2026-09-16.

**FOUR pre-registered gates fail, and the named one is among them.**

* **G-C3a — its NAMED RISK, materialised.** C3a-2025 **−9.4 → −15.3 %** against ±10 %; C3a-2022
  −9.7 → **−19.0 %**.
* **G-C1 FAILS**: 2022 `ST_GAS` **−3.93 TWh / −2.9 pp**; 2024 `CC_REGULAR` **+4.69 TWh / +3.8 pp**.
* **G-C3b FAILS**: 2022 0.196 → **0.255**; 2025 0.168 → **0.220**.
* **G-C8 FAILS**: 2022 `ST_GAS` **33.0 % forced** against the 30 % cap, **not grounded**, on a D-4
  per-unit conduct provenance failure at plant 2480.

**The mechanism is directionally right and is still refused.** CT_PEAKER 0.246 → **0.737** /
0.300 → **0.708** / 0.771 → **1.770** TWh closes **26.3 / 25.3 / 49.0 %** of the 2023/24/25 miss —
far more than arm A. But it **overshoots 2022 by nearly 2×** (2.429 → **5.616** against a 2.829
actual) and pays for the CT energy out of `ST_GAS` (7.292 → **4.985** against 8.106 actual), which
is exactly the C1 and C8 failure. **2022 is the year nyiso-199/200 never screened**, so this is new
information rather than a re-run of a settled result.

**No band value was re-cut after the result** — the PRECOMMIT forbade it, and nothing was.

---

## 5. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — both arms were selected on structure (a citation ring and a measured
  double count) and both were sized against the object BEFORE the solve; §2.4 was written to
  foreclose reading a C1 gain as the object closing. Arm B's adverse rows are reported at full
  magnitude and it is refused on its gates rather than re-cut. `authorized_price_tuning` **NONE**
  on both: rule 1's carve-out governs a band identified by the PRICE RESIDUAL, and these are
  identified by NYISO's own CAMPD conduct (the nyiso-232 precedent).
* **Rules 13 / 14 `[R-MEASURED]` / `[R-ACCURATE]`** — a measured p50 replaces a transferred,
  uncited number. It regenerates forward from CAMPD conduct, so it is admissible in a forecast.
* **Rule 19 `[R-ONE-MECH]`** — the two arms are ALTERNATIVES and `backcast_config` raises if both
  are armed; the startup double count is the second ground for arm A.
* **Rule 21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters, zero new literals; both arms are
  registered `ScenarioConfig` fields with CLI flags, fail-loud ISO-scope and phys-key guards, and a
  `run_calibration.py` guard against the silent-no-op `prb_overrides`-only path.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing crosses: CAISO's 0.991 and NEISO's 0.985 are never carried.
* **Rule 27 `[R-PUSH]`** — Opus session; all four ≥300-line solve-path files edited locally and
  **every pushed blob verified byte-identical** (line count + hash) immediately after the push.
* **Rule 28 `[R-MECH-MATRIX]`** — the queue and the DO-NOT-REDO set were read before anything was
  proposed; two DO-NOT-REDO cells were checked and **not** re-tested. Three cells stamped in this
  session: `ct_peaker_committed_measured` `U` → `O`, `nyiso_ct_peaker_bands_measured` and
  `cc_duct_peaking_row_scoped` stay `R` with their re-test condition SPENT. The new field's matrix
  registration landed in the same PR (28(c)); `check_mechanism_matrix.py` is green.
* **Rules 16 / 32 / 34** — one shard per arm, each `--years 2022 2023 2024 2025` in ONE invocation
  into ONE bundle covering the ISO's full registered union; both pushed their bundles including
  `dispatch/<yr>_P1.parquet`, so both can back a promotion (34(a), (c), (d)).
* **Rule 15 `[R-DASHBOARD]`** — both runs registered, keeper and rejected probe alike.
* **Rule 31 `[R-RETAIN]`** — **nothing has been deleted.** Both bundles are retained (§6) and the
  promotion question is asked rather than pre-empted (§7).

---

## 6. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

Both bundles are **on the remote, durable, and cost ZERO re-solve to promote**. They are 155 MB and
156 MB, so they are kept on their shard branches rather than pushed to `main` while the decision is
open; the promoted one is committed when the owner rules.

| arm | bundle | branch | **full immutable SHA** | files |
|---|---|---|---|---|
| A | `results/calibration/nyiso241_ctcommitted_span` | `claude/nyiso241-arm-a` | `2d15779b986ae8af11d60d86fbb5359ea0f82d6d` | 47 |
| B | `results/calibration/nyiso241_ctbands_span` | `claude/nyiso241-arm-b` | `b97cbede095577f7e1682a136f2282b67b13592d` | 47 |

```
git fetch origin <sha> && git checkout <sha> -- results/calibration/<dir>
```

Both recovery lines are also in `.gitignore` beside the ignore entries. **Both branches are kept
until the owner rules** (rule 33 `[R-SHARD-ARCHIVE]` (f) step 3: a branch carrying a bundle a
promotion would register is not deleted while the promotion is undecided).

**One thing that is NOT on the remote and had to be rebuilt**: `results/calibration/_shared/NYISO/`
is gitignored and was never committed, so the shards' copies did not travel with their bundles and
`render_calibration_html.build_payload` could not resolve `meta.shared_inputs`.
`run_calibration_full.py --rebuild-benchmark` regenerated it locally at **zero LP** and — because
the store is content-addressed — **at the identical hashes** (`eia930-12e2ee328d0a`,
`eia923-18923f3b9623`, `campd-7ea5a0beeb85`), which independently confirms both arms read exactly
the keeper's inputs. The keeper's committed bench parts did **not** move (`git status` on
`frontend/data/backcast/bench/` is clean and the keeper re-scores CALIBRATED).

---

## 7. THE DECISION — THE OWNER'S, AND IT IS OPEN

**Arm B needs no decision**: it fails four pre-registered gates including its named risk, its cells
stay `R`, and this session does not propose it.

**Arm A is the question, and the pre-registered decision rule and the gates point opposite ways —
stated plainly rather than resolved in whichever direction suits.**

* The PRECOMMIT §4.1 said *"Arm A is promotable on rule-14 grounds alone, whatever the residual
  does."* On that reading it should be promoted: it replaces an uncited transferred multiplier with
  NYISO's own measurement, removes a measured rule-19 double count, is exactly confined, adds no
  free parameter, and improves C1 in every year.
* The PRECOMMIT §5 gate **G-C3a/G-C3b said "no PASS → FAIL"**, and arm A crosses both — by 0.8 pp
  of a ±10 % band and by 0.001 of a ≤0.20 band, in 2022 only.

Rule 1 `[R-STRUCT]` is the tie-breaker the repo already states: *a real market behaviour stays in
even if it makes the fit worse, and you then fix the actual root cause* — and the root cause here
is already named and ledgered (NYISO scarcity/reserve price formation, issue #1344). The owner's
own standing framing is the same: *"If structural integrity improves but gates regress that may
still be a keeper."* But a CALIBRATED → NOT-YET headline is a real cost, and it is the owner's to
accept or decline.

**THREE OPTIONS, and I recommend the first.**

1. **Promote arm A.** The ISO's headline reads NOT-YET until the C3a-2022 root cause is fixed, and
   the model is better grounded. Rule 35 `[R-PROMOTE]` then applies in full: the year union
   `{2022, 2023, 2024, 2025}` is already enumerated and covered exactly by the arm bundle, so
   register → `audit_keepers` (E1/E13) → `prune_iso_runs --force-uncite` → re-run
   `build_status.py --iso NYISO`.
2. **Keep the nyiso-240 keeper and leave arm A registered as an adjudicated candidate** (cell `O`),
   with the C3a-2022 root cause carried forward as the blocker. Nothing is lost; the grounding
   repair waits for the price-formation work that would give it headroom.
3. **Promote arm A and accept the NOT-YET as temporary**, pairing it with a chartered successor
   session on NYISO scarcity/reserve price formation — the mechanism §2.4 shows the CT object
   actually needs.

**Nothing is at risk while this takes time**: both bundles are on the remote by immutable SHA (§6)
and nothing has been deleted.

---

## 8. THE SUCCESSOR OBJECT, RE-AIMED AGAIN

§2.4 is the finding that should drive the next session: **the CT_PEAKER object is majority
NOT offer-reachable.** The two candidates that remain, in the order the evidence supports them:

1. **NYISO scarcity / reserve (RCPF/AS) price formation** — the OPEN ROOT CAUSE the offer curve's
   own comments name, the thing that would give C3a-2022 headroom, and the thing that would let CT
   earn its energy in the top hours the way the real fleet does (C3c: model 0 h > $300 in 2023
   against 10 actual).
2. **In-City / Zone-J local-reliability commitment** — the chartered JOINT Zone-K reconciliation is
   already item 1 in the NYISO lever queue.

An offer-side lever aimed at the CT residual after this session would be reaching a number through
a mechanism that is not real, which rule 1 forbids however good the residual looks.

---

## 9. HANDED FORWARD, NOT THIS SESSION'S

Unchanged from nyiso-240 and re-verified as not made worse here:

* `scripts/legitimacy_diagnostics.py` is **not reproducible** on nine measured columns at the 3rd
  decimal — a GATING artifact (C8, rule 20's conditional-pass path) that **nobody owns**.
* `tests/scoring` carries **20 failures on clean main**; this session adds zero (its own slice —
  251 config/offer-curve tests — passes).
* **G2 hydro loss** (−55.2 / −25.5 GWh in 2022/23) stays a LEDGERED OPEN ROOT-CAUSE ISSUE.
* **D-4 unit-conduct** False at plants 2480 / 8006 — pre-existing on the keeper. Note that **arm B's
  C8 failure convicts plant 2480 specifically**, so that pre-existing provenance gap is now
  load-bearing for at least one candidate.
* `check_registry_payload_parity.py` REDs: `caiso279_ablate_dswcouple_span` and `soco15_spp_arm`
  are **pre-existing and non-NYISO** — reported, not touched. The four `nyiso_mer_2026-09-19_*`
  REDs are this session's own gitignored local checkouts and are invisible to CI.
* `data/raw/gas-prices/SOURCES_nyiso_downstate_ldc_transport.md` still says 2022 is
  "holdout-quarantined (CLAUDE.md rule 22)". `[R-HOLDOUT]` was removed 2026-09-09 and the CSV now
  carries 12 rows of 2022 for both LDCs — stale prose over live data. Cosmetic; not fixed here.
