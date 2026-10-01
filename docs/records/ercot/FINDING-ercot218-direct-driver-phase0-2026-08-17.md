# FINDING — ercot-218 (THE DIRECT SOC/AS-POSITION DRIVER LANE, Phase-0): the measured AS-state swap REPRODUCES the ercot-211 record to the pair, DISSOLVES 98.2 % of its storage tie-pairs — and the verdict is **NOT-TRANSFERABLE on all five gates anyway**: the surviving true-AS-state ties still violate at **71.1 %** (max irreducible error $2,479/MWh), the within-regime control WORSENS to 0/6, and the record-named source turns out unable to supply the SOC half at all (no `60d_DAM_ESR_Data` before RTC+B; no SOC column even after). **The lane CLOSES; Door D is CONFIRMED as the floor; the ERCOT backcast lane RESTS** pending the 2026 SOM RTC+B-era anchors (~mid-2027)

**Session ercot-218, 2026-08-17/18, branch `claude/ercot-218-direct-driver-5ckiur`.**
Keeper resolved fresh from `frontend/data/backcast/keepers/ERCOT.json` at
session start AND end: **`2026-08-17-ercot215-arm-decontam`** — UNCHANGED;
determination NOT-YET, fail set {C3a-2023 −40.1 %, C3b-2023 NRMSE 0.736}, C3c
the ledgered CAVEAT ×3 (68/181, 22/53, 1/31). **Phase-0 read-only as
dispatched: no LP, no solve, no year scored, no run registered, no bundle
modified, no `ScenarioConfig` field, no matrix cell verdict minted.**
Pre-registered in `docs/PRECOMMIT-ercot218-direct-driver-phase0-2026-08-17.md`,
pushed and blob-verified BEFORE the instrument read any delivery-2023 row.
Committed probe: `scripts/probes/ercot218_direct_driver_phase0.py` →
`results/calibration/ercot218_direct_driver_phase0.json`. RETENTION HOLD
honoured: `2026-08-16-ercot213-ctl-headbase` and
`2026-08-15-ercot204-rule26-delete` NOT pruned. This lane is **off-queue by
the owner dispatch itself** (the ERCOT §5.1 queue holds no live
un-adjudicated in-model item), chartered as the owner card ercot-211's
handback item (ii) required.

## 0. VERDICT

**NOT-TRANSFERABLE.** Under the pre-registered rule (precommit §6: PASS
requires T1 ∧ T2 ∧ T3 ∧ T4 ∧ T5), **all five gates fail** — the null
expectation the dispatch stated in advance, now measured on the strongest
driver set the committed record can supply. Per the precommitted rule,
**nothing is chartered, the lane CLOSES, and Door D (card W wait-for-data,
~mid-2027) is CONFIRMED as the floor** (§5).

1. **The instrument's fidelity is proven, not assumed**: on the same rows,
   the proxy-vector T5 reproduces ercot-211's storage result **to the pair**
   (1,168 tie-pairs, 1,111 violating = 95.12 %, max irreducible error
   $2,487.50/MWh), and the achieved coverage is identical
   (2,503 / 2,432 / 175 hours). The delta below is the driver swap and
   nothing else.
2. **The true AS state dissolves almost all of the proxy's tie evidence**:
   98.2 % of the 1,168 proxy tie-pairs separate under the per-product vector
   — they were never truly indistinguishable; the aggregate `(HSL−HASL)/HSL`
   proxy had been blurring genuinely different AS states together, and
   ercot-211's specific 95.1 % magnitude was proxy-inflated. Only **1.53 %**
   of the proxy-VIOLATING mass survives as true-AS-state ties.
3. **And the model-free wall still stands at the corrected magnitude**: on
   the direct vector's own tie population — hours matched on tightness,
   online capability, telemetered capability fraction AND all five product
   responsibilities — **32 of 45 pairs (71.1 %) still carry storage offer
   levels further apart than the band**, max irreducible error
   **$2,479/MWh**, against a 10 % bar. Not vacuous (the precommit's vacuity
   clause does not engage), and 7.1× the bar: **storage scarcity conduct
   remains model-free non-identifiable on the true AS state.**
4. **The decisive control got WORSE, not better**: T4 (fit 2024 → predict
   2025, one design regime, true AS state in hand) drops from the proxy
   version's 1/6 to **0/6** storage months in band (errors −92 % to
   +187 %). Whatever moves the storage offer mapping year-over-year, it is
   not the AS position — the ercot-210 §4 competitive-state mechanism
   (offered volume ×8.4, price ÷2.7 at matched tightness across 2023→2025)
   stands untouched as the identified driver, and it is an equilibrium
   object no forward-computable driver can carry.
5. **The class split persists**: thermal top-of-stack transfers cleanly
   under the direct vector too (T4 6/6, T5 0 of 4,501, every 2023 month in
   band on substance) — and the direct AS columns break **zero** thermal
   ties (thermal AS shares are ~0.01–0.03 and near-uniform). Thermal is
   still not the 2023 object; storage still is; storage still does not
   transfer.
6. **P0-A's own finding**: the record-named source cannot even be built as
   named — the `60d_DAM_ESR_Data` family does not exist before RTC+B and
   carries no SOC column after it (§1). The SOC half of handback item (ii)
   is permanently unbuildable for the 2023–2025 span from any committed or
   published disclosure this record knows; the AS half was built from the
   NP3-965 corpus's own telemetered per-product responsibilities and is
   what this verdict rests on.

## 1. (P0-A) THE DATA PREMISE, MEASURED — what "the committed 60-Day DAM ESR disclosures" turn out to be

The dispatch names the committed 60-Day DAM ESR disclosures as the source for
"per-hour measured ESR SOC, AS responsibility by product
(RRSFFR/ECRSS/NSPIN/REG), and telemetered capability". Inventoried and
verified against the primary artifacts before the instrument design was
frozen (precommit §1):

1. **The `60d_DAM_ESR_Data` family does not exist for the test years.**
   ERCOT ADDED the per-day `60d_DAM_ESR_Data` CSV to the NP3-966 daily
   bundle at the RTC+B go-live — from delivery day 2025-12-06 storage leaves
   `Gen_Resource_Data` (no PWRSTR rows) and reappears as combined `ESR`
   resources. Repo's own intake record (`docs/calibration-log.md` ERCOT-66;
   `scripts/data/fetch_ercot_60day_gen_resource.py`: *"ESR_Data exists only
   from the RTC+B go-live (delivery 2025-12-06 / publication ~2026-02-04);
   earlier bundles simply have no such member"*). The committed files:
   `..._ESR_Data_2026_Jan-Mar.parquet` (183,881 rows, delivery span
   **2025-12-06 .. 2025-12-31** — verified this session) and
   `..._2026_Mar-Jul.parquet` (H1-2026 deliveries, **not read**, rule 22).
   The whole family lies **after the SCED-corpus lane's stop date (delivery
   2025-12-04)**: zero overlap with the instrument's fit or test populations.
2. **The family carries NO SOC column even in the RTC+B era** — 38 columns,
   the `Gen_Resource_Data` layout (awards, submitted curve steps, HSL/LSL
   envelope, per-product AS awards). No state-of-charge quantity of any kind.
3. **Measured per-hour ESR SOC for 2023–2025 exists in NO committed corpus.**
   The record-named source cannot supply the SOC half of handback item (ii),
   for any year this program can score — and the repo's intake record
   identifies no pre-RTC+B ERCOT disclosure that publishes ESR SOC at all.
   Integrating `Telemetered Net Output` to a SOC estimate is a construction
   (unknown initial condition and efficiency), not a measurement — REFUSED
   (rule 13; the same line the RTC+B adapter draws for `HASL`). **The SOC
   half of the record-named candidate is unbuildable on committed data**;
   recorded as a standing data blocker in §5.
4. **The direct AS state IS committed and measured for 2023–2025**: the
   NP3-965 SCED Gen Resource corpus carries five per-product telemetered
   AS-responsibility columns in its audited 108-column consumer union —
   `Ancillary Service {REGUP, RRS, RRSFFR, NSRS, ECRS}` — per resource per
   SCED interval, on the very rows the instrument reads. Verified: fully
   populated on PWRSTR rows (non-null share 1.000; 41.7 % of row-intervals
   carry a positive responsibility, pub 2024-03); REGUP/RRS/RRSFFR/NSRS
   present in **every** shard vintage; **ECRS is the one column with a
   vintage edge** — absent from the 107-column shards through pub 2023-08,
   first present at pub 2023-09 (delivery Jul-2023). Since ECRS went live
   at delivery 2023-06-10, the delivery-Jun-2023 rows carry the product but
   not the column: those hours' `x3_ecrs` reads 0.0 — an under-measurement
   confined to the 2 post-ECRS June-2023 evaluation hours, disclosed
   here; the proxy `x3_old` at the same hours still absorbs any ECRS carve
   inside `(HSL − HASL)`. `RRSFFR ≤ RRS` holds on only 90.1 % of PWRSTR
   rows, so no nesting arithmetic is assumed anywhere — the five columns
   enter verbatim.
5. **The DAM-side alternative** (hourly per-product DAM AS awards for PWRSTR
   rows in the committed `60d_DAM_Gen_Resource_Data_{2023..2025}` files) is
   recorded and NOT used: it is the day-ahead position rather than the
   real-time responsibility, it adds an Hour-Ending-CPT join surface (the
   ercot-216 §6 clock discipline is binding, and this instrument inherits
   the proven CPT→CST construction instead), and its 2023 coverage holes
   (the permanent Oct-2023 MIS hole; no committed Dec-2023 window) sit in
   the test year.

**A consistency check the swap itself provides**: at the (hour, class) grain
the five product shares sum to the old aggregate proxy almost exactly
(smoke-test example: Σ products 0.378 vs `x3_old` 0.3765) — as they must,
since `HASL ≈ HSL − Σ AS responsibilities`. The direct vector carries the
same total AS position as the proxy **plus its decomposition**; what the
swap adds is exactly the per-product information, nothing else.

**Corpus recovery, executed as pre-registered.** The fit years need the
untracked NP3-965 window (pubs 2024-04..2026-02, 673 shards); the git pin is
dead since the 2026-08-16 history rewrite. Recovered via the corpus README's
route-3 salvage: `git fetch --depth=2 origin refs/pull/3978/head` — the PR
head itself is the untracking commit, so the corpus lives in its PARENT
(`40693ff^`) — then a worktree restore of the top-level window only.
Verified: **996/996** top-level shards `sha256sum -c` OK against the tip
`SHA256SUMS.txt` (zero mismatches, zero missing); the `rtcb-format-2026/`
quarantine deliberately NOT restored and NOT read; globs non-recursive; the
lane stops at delivery 2025-12-04. The deliveries 2024-01-10..23 MIS gap is
carried exactly as at ercot-211.

## 2. (P0-B) THE INSTRUMENT, UNCHANGED EXCEPT THE SWAP

`scripts/probes/ercot218_direct_driver_phase0.py` is the ercot-210/211
instrument verbatim — population discipline (above-LSL SCED2 segments capped
at HASL, ERCOT-154/161, telemetered-ONLINE, ONTEST excluded, absolute
$/MWh), responses (`p50`/`p90`/`s500`; headline STORAGE `p50` / THERMAL
`p90`), fit window (delivery-2024/2025 at tightness ≥ p90), transfer target
(delivery-2023 ≥ p98, post-ECRS primary), folds (out-of-year; LOYO across
2023 months; the 2024→2025 within-regime control), candidate forms and CV
selection, and the T1–T5 bands, counting rules and named-months clause,
constants copied unmoved — with ONE change, the driver swap (precommit §2):

- `x3` (the aggregate `(HSL−HASL)/HSL` AS-position **proxy**) → five
  measured per-product responsibility shares `x3_regup, x3_rrs, x3_ffr,
  x3_nspin, x3_ecrs` (= `Ancillary Service <svc> / HSL`, MW-weighted over
  the same segment population, same NaN guard and median fill).
- `x4` (`HSL/HSL_ref`) retained as the telemetered-capability driver — its
  SOC-proxy role cannot be replaced (§1.3), and dropping it would only make
  T5 ties easier, biasing toward non-identifiability.
- `x1`, `x2`, `x5` unchanged; quantity-only read/refused sets unchanged and
  written into the JSON (`system_lambda`/`rtorpa`/`rtoffpa`/`rtordpa` never
  read; no settlement price, LMP, RTSPP, DAM price, MCPC or model output
  anywhere).

T5 ties on the widened scaled vector
`[x1, x2, x3_regup, x3_rrs, x3_ffr, x3_nspin, x3_ecrs, x4]` (τ = 0.05,
identical `x5`), gate rule verbatim; the proxy vector `[x1, x2, x3_old, x4]`
is re-computed on the same rows for the pre-registered direct-vs-proxy
decomposition (never as a fitted driver).

**Coverage falsifier (precommit §3), judged before any gate was read — ALL
requirements PASS:**

| requirement | measured | pass |
|---|---|---|
| corpus restore `sha256sum -c` vs tip `SHA256SUMS.txt` | **996/996 OK**, 0 mismatch, 0 missing (quarantine deliberately absent) | ✓ |
| fit hours with offer rows: 2024 ≥ 2,400 / 2025 ≥ 2,300 | **2,503** of 2,629 / **2,432** of 2,434 (the 126 missing 2024 hours are the known deliveries 2024-01-10..23 MIS gap) | ✓ |
| test hours 175/175 (2023) | **175/175** | ✓ |
| non-empty selected-form map, both classes | 6/6 (cls × stat), logit selected throughout | ✓ |
| PWRSTR AS-column non-null share | **1.000** on every column, every year | ✓ |

The achieved coverage equals ercot-211's exactly, and 738 / 833 / 657
resources carry HSL references — the same population, same bytes
(sha-verified), same discipline.

## 3. THE GATES, AT FULL MAGNITUDE

### 3.1 T1 / T2 — out-of-year transfer, fit {2024 ∪ 2025} → post-ECRS 2023

STORAGE headline (`p50`, $/MWh):

| month | hours | measured | predicted | rel err | in band | (ercot-211 proxy rel err) |
|---|---:|---:|---:|---:|---|---:|
| Jun | 2 | 5,000.00 | 1,661.81 | **−66.8 %** | no | −83.4 % |
| Jul | 6 | 4,999.98 | 863.66 | **−82.7 %** | no | −96.9 % |
| **Aug** | 9 | 3,361.12 | 4,500.77 | **+33.9 %** | **yes** | −77.6 % |
| **Sep** | 4 | 4,052.48 | 9,536.15 | **+135.3 %** | no | −51.3 % |
| Dec | 1 | 271.81 | 743.42 | +173.5 % | no | +28.4 % |

The direct AS state moves **August into band** (2023's eval-hour AS position
— REGUP 0.11 + RRS 0.22 of HSL, ECRS/NSPIN near zero — is distinctive, and
the fitted function chases it upward) and **overshoots September by +135 %**
in the same motion, where the proxy had undershot by −51 %. No stable
identification: the named-months clause (Aug AND Sep) fails on substance,
and no post-ECRS month reaches the `FOLD_MIN_HOURS = 10` admissibility bar
(the known-unsatisfiable constant, carried verbatim; the relaxed-to-≥1
diagnostic is in the JSON and changes no verdict). THERMAL `p90` is in band
in every month on substance (measured $29.90–$75.00 vs predicted
$37.11–$41.59) and fails the gate only on the same admissibility arithmetic
— the ercot-211 reading, reproduced. **T1 FAIL.**

T2 (`s500`): storage Jul/Aug/Sep/Dec in band on substance (Aug −21.5 %,
Sep −14.1 % — better than the proxy's Aug −47.3 %), Jun outside (measured
1.00 vs predicted 0.58); thermal in band throughout (shares ~0.01 under the
±0.15 absolute floor). Fold arithmetic as T1. **T2 FAIL.**

### 3.2 T3 — non-degeneracy (fit years only)

Still **inverted**: predicted tight/mid ratio **0.46** (storage) and
**0.64** (thermal) against the 3× bar — **T3 FAIL**, with the ercot-210
§2.4 caveat unchanged (the gate evaluates outside the ≥ p90 fit support, so
the inversion magnitude is extrapolation-confounded; the failure stands).

### 3.3 T4 — the within-regime control, fit 2024 → predict 2025. The decisive one.

| class | admissible months | in band | rel errors | ercot-211 proxy |
|---|---:|---:|---|---|
| STORAGE | 6 | **0** | **−91.6 % to +56.6 %** | 1/6 |
| THERMAL | 6 | **6** | −10.2 % to −37.0 % | 6/6 |

With the true per-product AS state in the design matrix, storage conduct
transfers **one year forward inside one design regime** *worse* than the
proxy version did (0/6 vs 1/6; Jun–Sep −64 % to −92 %). The AS
position is not what moves the mapping. **T4 FAIL.**

### 3.4 T5 — the model-free tie test, direct vector

| class | tie-pairs | exceeding band | share | max irreducible error | verdict |
|---|---:|---:|---:|---:|---|
| STORAGE | **45** | **32** | **71.1 %** | **$2,479.00/MWh** | **FAIL** |
| THERMAL | 4,501 | 0 | 0.0 % | $25.49/MWh | PASS |

Not vacuous (45 > 0; the precommit's vacuity clause does not engage). Hours
matched within τ = 0.05 on **all eight** scaled coordinates — tightness,
online-capability percentile, five product-responsibility shares,
telemetered-capability fraction — still carry storage offer medians up to
$4,958/MWh apart. **T5 FAIL**, and per the precommit's description rule the
failure is reported as **model-free non-identifiable at this grain on the
true AS state** (SOC coordinate honestly absent — unmeasured in every
committed corpus, §1).

## 4. THE DIRECT-VS-PROXY T5 DELTA — the dispatch's named deliverable

The dispatch asks verbatim: *"report how much of T5's tie-pair violation
survives when driver-indistinguishability is measured on the TRUE SOC/AS
state."* Measured on identical row populations (storage; SOC honestly
absent per §1, so "true state" = the five product responsibilities +
telemetered capability):

| quantity | value |
|---|---:|
| proxy tie-pairs (ercot-211's construction, re-run) | **1,168** |
| … of which violating | **1,111 (95.12 %)** — the record, to the pair |
| proxy tie-pairs still tied on the direct vector | **21 (1.8 %)** |
| share of proxy ties BROKEN by the true AS state | **98.2 %** |
| proxy-VIOLATING pairs still tied on the direct vector | **17 of 1,111 (1.53 %)** |
| max irreducible error among those survivors | **$2,478.50/MWh** |
| direct-vector tie-pairs (its own population) | **45** (21 surviving + 24 newly tied)¹ |
| … of which violating | **32 (71.1 %)**, max **$2,479.00/MWh** |

¹ A pair can tie on the direct vector without having tied on the proxy: the
proxy coordinate is approximately the SUM of the five product shares, so two
hours within τ on every product can differ by up to 5τ on the aggregate.

**Both halves of the answer, stated at full strength:**

1. **As a fraction of the original violation mass, almost nothing survives
   — 1.53 %.** ercot-211's headline "95.1 % of driver-indistinguishable
   hour-pairs" was carried by pairs the true AS state distinguishes: the
   aggregate proxy had collapsed 2023's distinctive AS mix (heavy
   REGUP+RRS, total ~0.34 of HSL at the eval hours) onto 2024/25 hours
   whose mix is materially different (ECRS+NSPIN-weighted, totals
   0.14–0.25). The proxy-era T5 magnitude was proxy-inflated, and this
   session corrects the record on that number.
2. **And the corrected measurement still refutes identifiability, seven
   times over the bar.** On true-AS-state ties the violation share is
   71.1 % with a $2,479/MWh worst case — hours the committed record cannot
   distinguish on ANY quantity it carries (tightness, capability, every
   product responsibility, capability fraction, season) clear thousands of
   dollars apart. And T4 (§3.3) shows the added information buys **no
   transfer at all** — 0/6 within-regime, worse than the proxy. The
   identification wall moved from "the drivers are blurred" to "the mapping
   itself moves", which is exactly the ercot-210 §4 competitive-state
   mechanism (volume ×8.4, price ÷2.7 at matched tightness), an equilibrium
   object a forecast would have to predict, not condition on.

The storage AS state itself, measured at the eval cut (context, gating
nothing): 2023 `x3_old` 0.337 (REGUP 0.112, RRS 0.221, FFR 0.001, NSPIN
0.016, ECRS 0.021) → 2024 0.254 (ECRS 0.090) → 2025 0.144 — the AS
position halved across the span while the storage offer `p50` fell 2.7×
and offered volume grew 8.4× (ercot-210 §4). The decomposition is real
information — it is what breaks the ties — but it tracks the fleet's
build-out, not its conduct.

## 5. (P0-C) CLOSE-OUT — the lane closes; Door D is the floor; the ISO rests

Per the precommitted rule (dispatch + precommit §6), on anything less than
five PASSes: **the lane CLOSES. No Phase-1 charter is drafted, nothing is
armed, nothing is built.** The one record-named unmeasured candidate
(ercot-211 handback item (ii)) is now measured, under its own owner card,
and it does not open the door: **Door D — wait for the 2026 SOM RTC+B-era
anchors (~mid-2027) — is CONFIRMED as the floor**, with the exhaustion
proof extended to its strongest form yet: the storage scarcity-conduct
layer is model-free non-identifiable at hour grain on tightness, capability
AND the true per-product AS state, and does not transfer within-regime even
with that state in hand.

**The ERCOT backcast lane RESTS.** Its standing data blockers, recorded:

1. **The 2026 SOM RTC+B-era anchors (~mid-2027)** — the Door D wait. The
   RTC+B design moves shortage pricing into energy via per-product ASDCs
   and real-time AS sales; its first monitored year is the first data that
   can anchor a storage conduct layer inside a design the forward model
   must represent anyway.
2. **The 2025 EIA-923 final-vintage re-derivation** — the five C1 gas-class
   SKIPs on the keeper's 2025 scorecard close whenever the final vintage
   lands; independent of this lane.
3. **Measured ESR SOC does not exist pre-RTC+B** (this session's P0-A
   finding, §1): no committed corpus and no pre-RTC+B ERCOT disclosure the
   record identifies publishes per-hour ESR SOC, and even the RTC+B-era
   `60d_DAM_ESR_Data` family carries no SOC column. The SOC half of
   handback item (ii) is permanently unbuildable for the 2023–2025 span;
   any future SOC-conditioned work is RTC+B-era work.

What this close-out does NOT touch: the keeper
(`2026-08-17-ercot215-arm-decontam`, NOT-YET, unchanged), the C3c ledger
and its magnitudes, Q-B FINAL / R-A (cited, not spent — no C3a/C3b/C3c
value was computed in any year), the ercot-216 filed item (the C3c
exception's OPEN RESIDUAL LANE re-wording stays with the NEXT
keeper-promoting session; no registered attestation was edited here), and
the G-SPUR band-top blindness (FINDING-ercot214 §5 — stays an owner
gate-revision item, flagged, not self-amended).

## 6. GOVERNANCE

Owner dispatch executed as the lane's charter (the owner card required by
ercot-211 handback item (ii)); off-queue status stated (§0). Q-B FINAL and
R-A honoured: **no C3a, C3b or C3c value computed in any year** — every such
number here is a committed-artifact citation; this dispatch does NOT
re-suspend Q-B, and every 2023 quantity measured by the probe is a
measured-vs-measured evaluation target only (rule 13; nothing feeds any
model input). DO-NOT-REDO honoured in full: Door A conduct-function fitting
not re-run (this is the DIRECT family under its own card; nothing fitted to
any residual); item 11 (Q-B) closed and untouched;
`energy_online_capability_cap` (R) and `ercot_storage_rt_offer_surface` (R)
not re-opened; the mid-band spill lane stays CLOSED (ercot-215); LOLP-table
arming not re-opened (ercot-206 B0); V0/ercot-201 honoured (conditioning is
the same within-year percentile rank, no tightness-conditioned R_f); 28a
honoured; the regime lane stays CLOSED (ercot-217). Rule 22: {2023, 2024,
2025} only — the H1-2026 ESR file and the RTC+B quarantine never read, no
marker sought. Rule 25: ERCOT only. Rules 5/23/24: no `ScenarioConfig`
field, no constant, no derive touched, nothing fitted to a residual —
the probe's fitted forms exist only inside the identifiability instrument
and are consumable by no solve. Rule 15: no run produced, nothing to
register; keeper and dashboard untouched. Rule 28: no mechanism tested ⇒ no
cell verdict minted (28b, the ercot-214/217 note precedent — an attribution
note is appended to the ERCOT shard, verdicts untouched); no new field ⇒ 28c
not engaged; duty (a) discharged — the §5.1 queue was read first and this
lane's off-queue charter is the owner dispatch itself. Rule 27: every file
edited locally, exact on-disk bytes pushed, pushed files ≥300 lines
blob-verified on both transports. **Transport note for the record**: native
`git push` initially hung indefinitely at the pack-POST through the session
egress relay (reads unaffected; 7-object pack; HTTP/1.1 + enlarged
postBuffer in place); the relay was replaced mid-session (proxy port and CA
changed) and the SAME push then succeeded in ~1 s — an environment fault,
not a pack-size event; the remote branch was created via the API
(`create_branch`), and every file travelled over `git push` with ≥300-line
artifacts blob-verified.
No new workflows, no cron, no CI job, no PR (push-and-stop on the
designated branch).

**Session consumed the ercot-218 shorthand. Next shorthand: ercot-219**
(ercot-199 remains unclaimed).
