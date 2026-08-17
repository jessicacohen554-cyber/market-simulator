# FINDING — miso-163: the C3a-2025 lane is CLOSED by owner ruling as a model-class limit. The Shape-1 data blocker was FALSE and the real blocker is a structural `G` that measures inert — the intake was available and the lever was still refused

**Session** miso-163 · **ISO** MISO · **Date** 2026-08-17 ·
**Keeper** `2026-08-16-miso-160-wefor-shape` (bundle `miso160_wefor_B`),
**UNCHANGED**.

**NO SOLVE. NO RUN REGISTERED. NO `ScenarioConfig` FIELD. NO CELL VERDICT
MINTED** (nothing armed or tested — the miso-142/153/155/156/157/161 no-LP
precedent). Rule 15 `[R-DASHBOARD]` is not engaged: there is no run to
register, and none was produced.

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only, read from committed
artifacts and the in-repo measured record. MISO holds neither `complete` nor
`final`; the holdout spend freeze is untouched; no marker was read, written or
relied on.

**Charter.** miso-161 escalated the C3a-2025 residue to the owner with two
shapes on the record. miso-162 did no solve; it de-duplicated the twice-restored
`reliability_floor_plant_exclusions` override (`a84baa2`, merged) and ran
read-only recon that **materially changed the question**. This session's whole
scope is: verify that recon, put both halves to the owner, and execute the
ruling.

---

## 1. The state being ruled on, re-verified from committed artifacts

`scripts/calibration_verdict.py --run-id 2026-08-16-miso-160-wefor-shape`
(committed bundle + bench only, no solve):

| criterion | tier | result |
|---|---|---|
| C1 fuel-mix by class | load-bearing | **PASS** |
| C2 system volume | load-bearing | **PASS** |
| **C3a mean LMP** | load-bearing | **FAIL — 2025 −12.5 % `[MODEL MISS]`** (2023/2024 inside band) |
| C3b price duration/shape | load-bearing | **PASS** |
| C3c price tail / scarcity | supporting | **CAVEAT (ledgered)** — model 3 / 6 / 4 h vs RT actual **30 / 37 / 88** h >$200 |
| C4 fleet hourly dispatch corr | supporting | **PASS** |
| C6 governance gate | protective | **PASS** |
| C8 forced-energy share (D-2) | protective | **PASS** (ST_GAS grounded above budget 32.7 / 34.4 / 46.2 %, all binding mechanisms clear D-4) |

**Determination: NOT-YET.** Basis line: *undocumented out-of-tolerance (FAIL)
criteria: `price_mean`* — **C3a-2025 is the sole failing criterion**, exactly as
miso-161 left it. The C3c standing rule does not and cannot fire here: it
requires C3c to be the **lone** failure, and C3a's FAIL keeps it silent (guard
(a) working as designed).

---

## 2. Verification of the miso-162 recon — both halves hold

### 2.1 (i) The stated Shape-1 data blocker is FALSE — CONFIRMED

`data/raw/MISO-AS/` already carries the measured RCPF/ORDC observables for the
full 2023–2025 training window. Per that corpus's own tracked `README.md`:

* `asm_rtmcp_zonal_{2023,2024,2025}.parquet` — **real-time final zonal
  ancillary-service market clearing prices**, columns
  `date, zone, product, he01..he24` (Hour-Ending 1–24, EST year-round; MISO
  market reports never observe DST), deduplicated to one row per
  (zone, product). Products: reg / spin / supp / str.
* `asm_damcp_zonal_{2023,2024,2025}.parquet` — the day-ahead ex-ante twin.
* `asm_rt_cleared_mw_{2023,2024,2025}.parquet` — hourly **Region × product
  cleared reserve MW** (North / Central / South).

The files are present and non-trivial (RT MCP 2023/2024/2025 = 235,805 /
238,863 / 243,010 bytes; RT cleared MW = 472,711 / 530,078 / 494,031 bytes).
Regeneration is a standing script (`scripts/fetch_miso_asm.py --years …`), and
the corpus is already consumed by `scripts/report_miso_posture_gate.py` and
`scripts/run_calibration_full.py`.

**Consequence:** RCPF binding hours — which hours, which reserve product, at
what step — are derivable **in-repo** against the published step schedule
(Spin $65 / $98, Reg ~$140, STR multi-step to $500, energy steps
$1,100 / $2,100 anchored to a $3,500 VOLL for the 2023–2025 window; MISO
BPM-002 Att. B §5.4, Potomac IMM 2024 MISO SOM). **No data ask is needed, and
none should be raised.** The Shape-1 framing that treated the intake as
blocked was wrong on the facts.

*(Note the 2022 boundary, unchanged and not relevant here: 2022 ASM data is
confirmed ungettable — a MISO Azure retention purge, 1,095/1,095 days 404 —
and must not be re-attempted. The training window is unaffected.)*

### 2.2 (ii) The REAL blocker is the mechanism, and it is already adjudicated — CONFIRMED

`ordc_scarcity_overlay` is cell **`G`** in the MISO shard
(`docs/codebase-site/data/mechanism-matrix/MISO.js`), extended to the
forecast/entry lane by ffr-4e. **The grounds are STRUCTURAL, not procedural**
(`docs/multi-iso/miso-scarcity-tail-external-validation-2026-07.md` §1–§4):

1. **The mechanism mismatch (§2).** MISO's ORDC is not an emergent
   marginal-cost outcome even inside MISO's own engine. It is an administrative
   stepped curve **derived from a Monte-Carlo loss-of-load-probability
   simulation** over net-load and outage/derate uncertainty in a **10–30 minute
   lead window**, scaled by a $35,000/MWh operating-reserve target cost (MISO
   Scarcity Pricing White Paper Mar-2024 §3.2.1). It prices **probabilistic
   short-term risk that a perfect-foresight hourly LP structurally does not
   contain**. Reproducing it means manufacturing the uncertainty — out of
   representation, or a fit to the residual that rules 1 `[R-STRUCT]` and 13
   `[R-MEASURED]` forbid.
2. **The measured inertness (§1), on the keeper's own hourly.** In the **88
   actual 2025 Indiana-Hub RT>$200 hours** the model clears **$50 median, $83
   p90, $125 p99, $157 max**; the reserve adder fires **2 of 88**;
   energy+reserve exceeds $200 in **1 of 88**; load-shed is **0 hours**.
   Deliverable reserve holds **≥11 GW against a ~4.4 GW requirement** in every
   event hour, and the LP re-times energy to relieve any zonal shortfall for
   ≤$23/MWh — always cheaper than the $200 ORDC step, so the shortage steps
   never engage. **The model is not sitting just under the threshold awaiting a
   nudge.** The DA column is decisive: h6425 RT $1,598 / DA $99; h2274 RT $876 /
   DA $52; h5849 RT $810 / DA $53 — the day-ahead market, which has full unit
   commitment, ramp modelling and network, never saw ~90 % of these, and a
   deterministic perfect-foresight hourly LP ≈ the DA market.
3. **The limitation is universal, not a MISO gap (§3).** 23 of 23 surveyed PCMs
   default to hourly + deterministic; deterministic perfect-foresight LPs
   systematically under-produce the spike tail (arXiv 2101.02303;
   PyPSA-Eur arXiv 2606.16486), and limited-foresight rolling-horizon moves
   hourly-price SMAPE only 21.3 % → 20.8 %.
4. **The frontier designation (§4) is already on record** and is quoted in the
   keeper's own C3c ledger text: every named admissible mechanism has been tried
   and adopted (reserve deliverability miso-39, Midwest sub-regional reserves
   miso-71, measured reserve requirements miso-56) — each kept per rule 1 even
   though the residual did not move. *“Further work needs a NEW admissible
   measured identification, its own charter. NEVER an offer adder tuned to the
   tail.”*

**Consequence:** chartering the RCPF/ORDC intake as a C3a-2025 lever is a
**rule-28 `[R-MECH-MATRIX]` DO-NOT-REDO collision** (a cell already adjudicated
`G`, re-tested without new evidence) **AND provably inert** (~2 of 88 hours).
The two facts compound rather than offset: (i) removes the *excuse* for not
building it, and (ii) removes the *reason* to.

---

## 3. The decision put to the owner, and the ruling

Both halves above were put to the owner as a single decision with two shapes,
the recommendation stated as Shape 2 on the evidence.

**THE OWNER RULED SHAPE 2 — CLOSE THE LANE.** Recorded verbatim, with its
provenance, at `docs/governance/rule-history.md` §7.

The precedent is **ERCOT C3a-2023 (Q-B)**
(`docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md`):

> **(Q-B) STOP — ERCOT stands at NOT-YET on C3a-2023 as a model-class limit, and
> the program stops spending on it.** … this is a **budget decision, not a
> rubric decision**. The determination stays NOT-YET; C3a-2023 stands a MODEL
> MISS at full magnitude; no ledger text moves.

The parallel is exact in the load-bearing respects: a lone C3a level miss whose
closure requires price formation the accepted C3c limitation's own text says a
competitive-offer deterministic LP cannot produce; the only untried instrument
adjudicated against on structural grounds; and the residual beyond the tail
object closed to tuning by rule 20 `[R-DOF]`.

---

## 4. The standing posture

1. **The determination stays `NOT-YET` on C3a-2025 ALONE (−12.5 % against the
   ±10 % bar)**, held as the **deterministic-LP edge**.
2. **The miss is reported at FULL magnitude as a `[MODEL MISS]`.** Nothing is
   reclassified, no ledger text moves, and the rubric is untouched — C3a has not
   been ledgerable since v3.1, and this closure does not seek to make it so.
   **Closing the lane is a budget decision about where sessions are spent; it is
   not a claim that the model passes.**
3. **C3c remains the single ledgered CAVEAT**, on its existing frontier text.
4. **MISO has NO open tuning lane.** The availability channel is exhausted at
   admissible grain (miso-161); every other cushion/identity cell is
   `R` / `I` / `G` / refuted-at-charter or `K`-armed; rule 20 closes the Δ₁/Δ₂
   cancellation (+$2.4–4.4) to tuning.
5. **Re-opening requires new evidence that defeats external-validation §1–§4
   SPECIFICALLY, or an explicit owner re-charter.** A data-availability
   argument is **NOT** such evidence — §2.1 above settles that the data is
   present, which is precisely why it cannot carry a re-charter.
6. **Keeper `2026-08-16-miso-160-wefor-shape` is UNCHANGED** — no promotion, no
   registration, no bundle regeneration, no dashboard mutation.

---

## 5. DO-NOT-REDO, restated for the successor

`ordc_scarcity_overlay` **`G`** (this session re-affirms it by owner ruling and
narrows its basis to §1–§4 alone); `dam_availability_rebasis` **`R`**
(miso-85/86); cross-fuel attribution **refuted-at-charter** (miso-87);
`measured_offer_surface` **`R`** (miso-151); `gas_hub_basis_overlay` **`R`**
(miso-156 — the measured input points the wrong way); `ramp_envelopes` **`I`**
(miso-156); reserves **inert at the peak** (miso-153 D-4, dual $0.00 in all
families × years); MOM daily shape **immaterial** (miso-161, ≲0.11 pp against
the +2.5 pp needed); and anything the MISO shard marks `R` / `I` / `G`.
Cross-ISO export of `summer_wefor_share_override` is other lanes' work
(rule 25 `[R-ISO-SCOPE]`) — each derives its own share from its own admissible
record.

---

**Artifacts.** No probe was written and no measurement was designed this
session: every number above is either read from a committed artifact by
`scripts/calibration_verdict.py` (§1) or quoted from an existing committed
record (§2.2 from `docs/multi-iso/miso-scarcity-tail-external-validation-2026-07.md`
§1–§4; §2.1 from `data/raw/MISO-AS/README.md` and the on-disk parquet
inventory). Surfaces stamped: `docs/mechanism-testing-matrix.md` §5.4 queue
header, `docs/calibration-log/miso.md`, the MISO matrix shard
(`updated`/`gates` + the `ordc_scarcity_overlay` evidence citation, cell
unchanged at `G`), and `docs/governance/rule-history.md` §7/§8.
`scripts/audit_keepers.py --iso MISO` green before and after.
Predecessor: `FINDING-miso161-c3a-residue-exhaustion-2026-08-17.md`.
