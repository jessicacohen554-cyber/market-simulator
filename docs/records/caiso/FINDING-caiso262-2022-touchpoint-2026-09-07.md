# FINDING — caiso-262: the CAISO 2022 validation touchpoint. **NOT-YET on C3a / C3b; the ISO stays CALIBRATED (rule 30(c)).** The miss is WINTER, not summer, and it is a gas-passthrough regime the training window never contained.

**Session caiso-262, 2026-09-07**, branch `claude/caiso-262-backcast-2022-wnukdb`.
Keeper **`2026-09-06-caiso-260-b1-demand`** UNCHANGED. Touchpoint run
**`2026-09-07-caiso-262-2022-touchpoint`**, stamped to the keeper (rule 30(a)).
Pre-registered in `PRECOMMIT-caiso262-2022-touchpoint-2026-09-07.md` and its two
addenda, all pushed before the measurement they govern.

---

## §1 — The result

**DETERMINATION: NOT-YET** (rubric v3.6), on 2022 alone.

| criterion | tier | 2022 | in-sample (keeper) | |
|---|---|---|---|---|
| C1 fuel-mix by class | load-bearing | **PASS** — 6/6, free 4/4 | PASS 12/12 | held |
| C2 system volume | load-bearing | **PASS** | PASS | held |
| **C3a mean LMP** | load-bearing | **FAIL — +21.1 %** | PASS +4.37/+8.89/+8.25 % | **degraded** |
| **C3b price duration/shape** | load-bearing | **FAIL — NRMSE 0.286** | PASS 0.083/0.142/0.111 | **degraded** |
| C3c price tail (RT hourly) | supporting | **PASS** — model 586 h vs actual 510 h | CAVEAT 23/0/0 vs 47/35/8 | **improved** |
| C4 dispatch correlation | supporting | **PASS** | PASS | held |
| C6 governance | protective | **PASS** (attested) | PASS | held |
| C8 forced-energy share | protective | **PASS** | PASS | held |
| C5a CO₂ vs eGRID | reported-only | −6.4 % | −11.0/−5.2/−4.3 % | — |

**Rule 30(c): this moves nothing.** CAISO's determination is the train-tier
(2023–2025) verdict and remains **CALIBRATED**; `build_status.py --iso CAISO`
re-reads `CAISO:CALIBRATED`, `audit_keepers.py --iso CAISO` passes 0/0, and the
keeper shard, its note and the `complete` marker's `determination` are
untouched. Rule 22: **nothing was tuned to 2022**, and nothing here proposes to
be. A validation number is model-SELECTION evidence, never a skill claim.

## §2 — WHERE the miss is, which is the actual finding

The +21.1 % is not a level shift. Load-weighted model-vs-actual RT by month
(the annual figure on this zone-demand weighting is +16.2 %; the scorer's
+21.1 % is on the `CAISO_HUB_WEIGHTS` hub basis and is the authoritative
number — the shape below is what the two agree on):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | **Dec** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| model | 55.00 | 49.46 | 46.58 | 56.94 | 64.61 | 73.18 | 78.04 | 100.96 | 113.09 | 69.15 | 85.59 | **304.69** |
| actual | 42.79 | 37.65 | 42.11 | 47.62 | 55.67 | 68.06 | 69.35 | 92.96 | 104.30 | 63.43 | 81.91 | **238.53** |
| error | **+28.5 %** | **+31.4 %** | +10.6 % | +19.6 % | +16.1 % | +7.5 % | +12.5 % | +8.6 % | +8.4 % | +9.0 % | +4.5 % | **+27.7 %** |

**The summer is in band and the winter is not.** June, August, September and
November — including the September heat wave that produced the year's record
52,061 MW peak — land at +4.5 % to +8.6 %, i.e. the same band the model holds
in 2023–2025. January, February and December run +28 % to +31 %. December alone
misses by **+$66.16/MWh** on a $238.53 actual.

**The mechanism is named in the run's own log:** the hub-basis overlay repriced
1,443 gas generators at the measured citygate spot in 12/12 months with a
**winter maximum of $54.05/MMBtu**. That is the December-2022 western gas
crisis passed through faithfully. At a ~7 MMBtu/MWh CC heat rate, $54 gas is
~$378/MWh of fuel cost alone. The model prices that passthrough at $304.69 for
the month; CAISO actually cleared at $238.53.

**So the touchpoint has surfaced an untested REGIME, not a broken mechanism.**
The training window's gas ran $2.19–$3.52/MMBtu (2022's is $6.45 annual, with a
$54 winter spike). Full measured passthrough was never exercised at that
extreme in 2023–2025, and at that extreme the real market clears well below it —
the physical market found something the model does not carry at those prices
(deeper clean/hydro imports, demand response, or bilateral positions that
blunt the spot). **That is a hypothesis, not a conclusion**; it is named here
so the lane that takes it does not start from zero, and rule 22 requires any
repair to be identified on 2023–2025 and only then re-tested on 2022.

## §3 — The one criterion that IMPROVED, and why it matters

**C3c is the standing CAISO limitation and it PASSES in 2022** — model 586
tail hours vs 510 actual (RT, >$200), against 23/0/0 vs 47/35/8 in the training
years, where it has been the ledgered caveat since caiso-184. The model has
never been able to make a scarcity tail in the calibrated years; in a year that
genuinely had one it makes one, and lands within ~15 % of it.

That is evidence about the *cause* of the in-sample C3c miss: the tail
machinery works when the drivers are present, so the training-year shortfall is
more likely a driver shortfall (gas, scarcity conditions) than a missing
scarcity mechanism. It also cuts against reading the 2022 C3a miss as "the
model just prices high" — it prices a real scarcity year's tail almost right
while over-pricing the ordinary winter months.

## §4 — Provenance: this IS the keeper's model on another year

Two checks, because the rung solved at HEAD and the keeper solved at
`e162147b`, **68 files / 40,931 insertions apart**:

* **G-DRIFT, by measurement rather than by audit.** The keeper's recipe was
  replayed on **2023** at HEAD and compared to the keeper's committed hourly
  sidecars: `class_hourly_2023.parquet` (122,640 × 5) and `system_2023.parquet`
  (61,320 × 9) are **BIT-IDENTICAL**. The drift — dominated by SPP onboarding
  on per-ISO registries and the zero-key-move D79 solve-surface landing — is
  inert for CAISO. *Disclosed: rule 29(b) prefers a hunk-level audit and would
  spend an LP only on a LIVE hunk. I spent one anyway, because 40k lines cannot
  be audited by eye to the confidence a bit-comparison gives, and the
  reproduction answers the question that actually matters. It is recorded as a
  judgment call, not as compliance.*
* **Recipe identity, machine-checked.** `gen_touchpoint_attestation.py`:
  **0 differing shared `meta.json` keys** outside the provenance set;
  solve-surface drift +2 −0 kwargs, each verified at its `ScenarioConfig`
  default. This independently reproduces the A-9 hand check.

**A-9 (hand).** The arm differs from the keeper only in `weather_year`
2023→2022, `gas_price_override` 2.54→**6.45** (the year's own measured Henry
Hub), `years`/`git_sha`, and **seven fields ABSENT from the keeper's recorded
config entirely** (813 vs 820) — added since, all default-off, four other-ISO
by name. No field changed value. *Disclosed: A-9 as written enumerated only the
year, out-dir and year-keyed lookups, so those seven are a difference it did not
anticipate.*

**G-BENCH passes in its STRONGEST form.** The 2022 bench part built from the
scaffold and from the rung have **zero differing keys** — `plants`, `e930`,
`classFull` identical (G-BENCH-A) and no other key differs either, `avgLMP`
included (G-BENCH-B). The ADDENDUM's scoping turned out to be unnecessary once
both parts were built after the price intake landed; it is left on record
because it was declared before the comparison, not after.

## §5 — Every pre-registered assertion, discharged

| | assertion | result |
|---|---|---|
| A-1 | every 2022–2026 DAM/RTM aggregate sha256-identical after the fold | **PASS** (9/9; the postprocess also rewrote `CAISO_tac_load_hourly_2023.csv` — byte-identically, confirmed by git) |
| A-2 | 2022 RTM schema/node set match 2023; ≥ `CAISO_MIN_HOURS` | **PASS** (8,760 h with all three hubs vs a 6,500 floor) |
| A-3 | `actual_lmp.json` differs in exactly one key path | **PASS** (CAISO.2022 added, 0 changed, over 48 iso-years) |
| A-4 | parquet 2023–2026 rows row-identical | **PASS** (float32 bits included) |
| A-5 | every other ISO's parquet untouched | **PASS** |
| A-6 | `actual_tail.json` differs in exactly one key path | **PASS** |
| A-7 | the demand derive leaves 2023–2025 byte-identical | **PASS** (sha256; `provenance.json` one key path) |
| A-8 | the nuclear derives leave 2023–2025 unchanged | **PASS** (row-identical; `--check` reproduces) |
| A-9 | recipe drift | **PASS** with the disclosure above |
| G-BENCH | scaffold vs rung bench part | **PASS**, strongest form |

No STOP rule fired.

## §6 — The 2022 measured basis (H-2 closed)

RTM crawl 365/365 trade dates, **8,760/8,760 distinct hours**, 0 missing, 0
partial, ~85 GB transferred and discarded. `CAISO_rtm_hourly_2022.csv` 87,600
rows = 10 nodes × 8,760 h. Measured: **RT $79.07, DA $86.31**; RT tail 510 h and
DA 553 h above $200 at 1.000 coverage — an order of magnitude above 2023–2025
(47/35/8 RT).

**A silent DST loss was found and repaired before any of this was used.** The
year first folded 8,749 hours: 2022-03-13 held 13 of its 23 and 2022-11-06 held
24 of its 25. The requests were correct — OASIS maps `startdatetime` → `OPR_HR`
by the local wall clock and correctly skips `OPR_HR 3` on spring-forward. The
fetcher's intra-day resume probe was keyed on the **request index**, which
diverges from the server's group index after that gap, so every other request
found the previous one's file already on disk and skipped itself. The probe is
deleted, both days re-crawled (23 h and 25 h, contiguous), and a coverage check
now reads the folded artifact rather than counting successful requests — the
test that passed while the data was missing.

## §7 — DISCLOSURES AGAINST INTEREST

1. **I rebased the working tree while the G-DRIFT reproduction was mid-solve**,
   having reasoned it was safe. It was not: the post-solve phase lazily imported
   a module mid-swap and raised `ImportError: MECH_SPP_GAS_COMMITMENT_BRIDGE`.
   The LP outputs had already been written and the symbol is present at HEAD, so
   this was a pure race and the comparison artifacts are sound — but the failure
   was mine, and a cleaner sequence would have waited twelve minutes.
2. **The monthly table in §2 is on a different weighting than the scored
   number** (zone-demand vs `CAISO_HUB_WEIGHTS`), which is why it reads +16.2 %
   where the scorer reads +21.1 %. It is a SHAPE diagnostic; the scorer's figure
   is the one that counts.
3. **§2's mechanism is a hypothesis.** That the winter miss is full gas
   passthrough into a regime the training window never contained is consistent
   with the monthly shape and with the $54.05/MMBtu print, but nothing here
   isolates it against the alternatives (import depth, hydro, storage).
4. **2019–2021 remain unreachable on two independent inputs**, which compounds:
   CARB allowance prices are absent (those rungs resolve to $0/t) *and*, per
   caiso-263 landed the same day, OASIS GroupZip has its own retention boundary
   at **2021-04-27**, so 2019 / 2020 / Jan–Apr 2021 hub LMPs cannot be fetched
   from OASIS by any endpoint. Those rungs need a rule-14 source adjudication,
   not another crawl.
5. **An eighth silent fallback (S-7, the zonal loss surface) was found only
   because I went looking**; caiso-259 §2 enumerated S-1…S-6 and missed it. I
   have no basis for asserting there is not a ninth.
6. **I first wrote C3c's model count as 580 h, which was wrong** — that was my
   own re-computation off `system_2022.parquet` on a zone-demand weighting, and
   I put it in this document, the calibration-log entry and the commit message
   in the place where the SCORER's number belongs. The scorer reads **586 h**
   (`criteria.price_tail.records[0].model`, hub-weighted). Caught by the
   `calibration-keeper-auditor` agent, not by me. Corrected here and in the log;
   the commit message is already pushed and stands uncorrected, which is why the
   correction is recorded rather than quietly applied. It changes no status, no
   band and no determination — 586 and 580 both sit inside the [0.5×, 2×]
   tolerance on 510 — but a number in the record should be the scored one, and a
   habit of substituting my own arithmetic for the scorer's is the actual defect.

## §8 — QUEUE

1. **The 2022 winter over-pricing is the new named object** — diagnose the
   high-gas passthrough regime, identify any repair on 2023–2025 (rule 22), and
   only then re-test 2022. It is the first CAISO object in some time that is
   neither DO-NOT-REDO nor blocked on an owner data decision.
2. The C3c inversion (§3) is evidence for the standing C3c lane and should be
   cited there.
3. Carried unchanged: the hod 22–23 import object (CLOSED as data-intake),
   Panoche (DECLARED PERMANENT RESIDUAL), the whole-plant-off days
   (DO-NOT-REDO), S2, the per-zone sidecar, the G-26 public-bid surface.
4. 2020/2021 rungs are blocked per §7 #4.

**No keeper change, no `ScenarioConfig` field, no offer-curve channel, no
mechanism-matrix verdict move (no mechanism was tested), no determination
change. Next number: caiso-264.**
