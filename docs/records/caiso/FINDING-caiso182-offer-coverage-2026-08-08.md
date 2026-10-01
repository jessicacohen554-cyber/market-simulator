# FINDING — caiso-182: the measured offer surface **CANNOT** be extended to the three uncovered classes. Both pre-registered identification tests **FAIL**, the masked corpus does not identify a CHP/steamer split, and **ARM A IS REFUSED**. BE-1 passes exactly, and the corpus blocker is closed

**Outcome: a CLEAN BLOCKED VERDICT — pre-registered ROUTE = REFUSED.** No LP was
spent, no bundle exists, nothing is registered. That is the charter's directed
outcome for this branch: *"a clean blocked verdict is worth more than a fitted close."*

Keeper **UNCHANGED** at `2026-08-06-caiso-175-tac-intake` (**NOT-YET**, rubric v3.1,
8 criteria, C3a the sole FAIL). DOF ledger **UNCHANGED at 11 / 8**. No `ScenarioConfig`
field added, removed or re-valued. No frozen identification constant touched.
`calibration-complete.json` and `holdout-freeze.json` **UNTOUCHED** (owner acts).
2023 + 2024 + 2025 only. **C3a was never scored, targeted or reported against** — no arm
existed to score it with.

Pre-registration: `PRECHECK-caiso182-offer-coverage-2026-08-08.md`, pushed and
blob-verified (396 lines, blob `0b6f02db…`, byte-identical both sides) **before any
offer-surface value existed on this session's corpus**. Instruments:
`scripts/probes/_caiso182_curate_stream_be.py`, `scripts/probes/_caiso182_offer_coverage_census.py`.
Records: `_caiso182_curate_stream_be.json`, `_caiso182_be1.json`,
`_caiso182_offer_coverage_census.json`, `_caiso182_stale_csv.json`.

---

## 1. THE RESULT — the masked corpus does not identify the three uncovered classes

The object was real and is confirmed: **26.0 % of CAISO's thermal fleet — 7,527.4 MW
across CC_CHP, CT_CHP and ST_GAS — prices on 100 % fitted, ERCOT-inherited
multipliers**, while the measured surface covers only CC_REGULAR and CT_PEAKER.
`_CAISO_OFFER_CURVE`'s own comment concedes those three "are NOT CAISO-grounded …
preserved verbatim". ST_GAS is precisely the class caiso-180 measured **backfilling**
the CC_REGULAR the accurate envelope removed.

| class | plants | nameplate MW | share | cap-wt base HR | measured surface |
|---|---:|---:|---:|---:|---|
| CC_REGULAR | 28 | 13,708.1 | 47.43 % | 7.44 | **COVERED** |
| CT_PEAKER | 134 | 7,616.3 | 26.35 % | 10.86 | **COVERED** |
| ST_GAS | 3 | 2,858.8 | 9.89 % | 11.85 | **UNCOVERED** |
| CC_CHP | 21 | 2,706.7 | 9.37 % | 6.90 | **UNCOVERED** |
| CT_CHP | 71 | 1,961.9 | 6.79 % | 11.01 | **UNCOVERED** |

**Both routes to covering them are refused by measurement.**

### 1a. IT-2 SEPARABILITY — **FAILS for every boundary that would extend coverage**

Candidate cuts are the midpoints between adjacent registered class base heat rates —
existing constants, never new ones. Both pre-registered legs applied: (a) a
cap-weighted density antimode within ±1.0 MMBtu/MWh, (b) the sub-buckets reconcile to
the target fleet MW inside the registered G1 bounds.

| cut | separates | (a) antimode | antimode actually *between* the two base HRs | (b) G1 reconciliation | verdict |
|---:|---|---|---|---|---|
| **7.172** | CC_CHP 6.90 \| CC_REGULAR 7.44 | yes | yes | **3.634** / 0.879 | **FAIL** |
| 9.152 | CC_REGULAR \| CT_PEAKER | yes | yes | 0.987 / 1.097 | PASS |
| **10.936** | CT_PEAKER 10.86 \| CT_CHP 11.01 | yes | **NO** | **2.311 / 2.182** | **FAIL** |
| **11.428** | CT_CHP 11.01 \| ST_GAS 11.85 | yes | **NO** | **9.751** / 0.963 | **FAIL** |

**The single passing cut, 9.152, separates two classes that are ALREADY COVERED** — it
is the CC/CT boundary the incumbent `hr_cut` 8.5 already serves, so it buys no new
class and cannot trigger the separation route. Every boundary that would extend
coverage fails, and fails by wide margins: the CC_CHP side sorts **3.6×** that class's
whole fleet below the cut, the ST_GAS side **9.8×**.

**Leg (a) alone is not evidence, and this session's own measurement says why.** The
gas-classified population is **146 resources over 44 non-empty 0.25 MMBtu/MWh bins =
3.32 resources per bin**, a density at which a strict local minimum is nearly free —
the histogram alternates up/down across almost its whole range. Two independent checks
confirm the leg-(a) passes are sampling noise rather than structure: for the two CT-side
cuts the nearest antimode **does not lie between the two class base heat rates at all**
(both 10.62 and 11.88 sit outside the 10.86–11.01 and 11.01–11.85 intervals, so cutting
there puts both classes on the same side), and **the same two bins are cited as the
antimode for two different cuts** — one valley cannot separate three populations.

The underlying reason is physical, not statistical: **the three CT-like classes' base
heat rates span 0.99 MMBtu/MWh in total** (10.86 / 11.01 / 11.85) while the recovered
slope distribution's own interquartile width is **3.87** (p25 7.49, p75 11.36). A
0.147-wide class cannot be cut out of a distribution that wide. *This confirms the
falsifiable expectation recorded in PRECHECK §3c.*

### 1b. IT-1 CONDUCT HOMOGENEITY — **FAILS on 5 of 6 consumed bands**

The fallback route asked whether a bucket's measured band is transferable to the other
classes in that bucket. It is transferable **iff** the conduct ratio — each resource's
band multiplier re-normalised by its **own** recovered heat rate rather than the class
constant — does not itself vary with heat rate. Measured across terciles of recovered
slope, against the deriver's **own frozen G3 tolerance** `max(0.08, 10 %)`:

| bucket | band | pooled | tercile spread | tolerance | verdict |
|---|---|---:|---:|---:|---|
| CC_REGULAR | econ_low | 1.2778 | **0.3538** | 0.1278 | **FAIL** (2.8×) |
| CC_REGULAR | econ_high | 1.3850 | **0.4970** | 0.1385 | **FAIL** (3.6×) |
| CC_REGULAR | peak | 1.6011 | **0.4980** | 0.1601 | **FAIL** (3.1×) |
| CT_PEAKER | econ_low | 1.2574 | 0.0958 | 0.1257 | PASS |
| CT_PEAKER | econ_high | 1.2627 | **0.2249** | 0.1263 | **FAIL** (1.8×) |
| CT_PEAKER | peak | 1.2549 | **0.3206** | 0.1255 | **FAIL** (2.6×) |

**Conduct is emphatically NOT heat-rate-homogeneous within either bucket.** A resource's
markup over its own marginal fuel+carbon cost depends systematically on its efficiency,
so the cap-weighted median measured over a mixed bucket is **not** the conduct of any
particular member — and applying it to CC_CHP / CT_CHP / ST_GAS would be an assumption
dressed as a measurement, not a rule-14 accurate input.

### 1c. Consequence

> **ROUTE = REFUSED. ARM A cannot be built on committed/measured data.** No LP spent,
> nothing registered, no promotion available or sought.

The contamination bound is nevertheless now measured rather than asserted: the CT
bucket's recorded 1.306 "over-shoot" against CT_PEAKER alone is **0.800 against the full
reachable population** (CT_PEAKER + CT_CHP + ST_GAS), and the CC bucket's 0.871 is
**0.727** against CC_REGULAR + CC_CHP — consistent with the deriver's disclosed
contamination and with the widened `[0.5, 1.6]` CT band being exactly the allowance it
says it is.

---

## 2. BE-1 — the corpus was ABSENT, was re-fetched in full, and reproduces EXACTLY

`data/raw/caiso-public-bids/` is gitignored and this container carried **only its
README** — zero daily zips, no `data/clean/` tree. caiso-178's "FETCHED IN FULL" status
describes a previous container, not a committed artifact. Re-fetched in full:
**1,095 of 1,096 trade dates, 422 MB**, the single gap being the known **2023-06-01**
OASIS archive hole — reproducing caiso-178's own count and size exactly. Zero
rate-limit/AUP responses across the whole fetch.

The **UNMODIFIED** deriver then reproduced the committed artifacts:

| quantity | committed | re-derived |
|---|---|---|
| GENERATOR EN curve rows | 66,985,503 | **66,985,503** |
| rows at cap ≥ 20 MW | 50,164,548 | **50,164,548** |
| resources | 694 | **694** |
| G1 CC_REGULAR | 11,935 MW / 0.871 | **11,935 MW / 0.871** |
| G1 CT_PEAKER | 9,950 MW / 1.306 | **9,950 MW / 1.306** |
| CC_REGULAR bands | 1.03 / 1.066 / 1.072 / 1.386 | **identical** |
| CT_PEAKER bands | 1.166 / 1.145 / 1.166 / 1.166 | **identical** |
| ladder p50 CC / CT | 1.565 / 1.234 | **identical** |
| **both CONSUMED JSONs** | — | **byte-identical ex `derived_utc`** |

`GATES ALL PASS`. **BE-1 PASSES.** The pandas 3.0.5 major-version risk pre-registered in
PRECHECK §2c **did not materialise** (this container: pandas 3.0.5, numpy 2.4.6, pyarrow
25.0.0, scipy 1.17.1). Artifacts were restored to their committed sha256 afterwards and
the ladder verified.

### 2a. The curation memory ceiling — **CLOSED** (known-open item 5)

caiso-178 filed `curate_dam_public_bids.py` as unable to process a full CAISO year
(~14.3 GB vs ~15 GB). Root cause confirmed: `_curate_spec` holds every day-frame and
`pd.concat`s them, then `write_clean` takes a **full `pa.Table.from_pandas` copy on
top**. Fixed as pure engineering in its own commit: `clean_io.write_clean_iter` streams
chunks into a `ParquetWriter`, bounding peak memory at one row group.

**Proven byte-equivalent BEFORE use**, 40 days / 3,552,863 rows — BE-A content, BE-B
row-group layout `[1048576, 1048576, 1048576, 407135]`, BE-C normalised data sha256
`fb5535a9…` all **identical**. Raw-file byte identity is impossible by construction
(`_build_metadata` stamps `created_utc`), so BE-C normalises exactly that field and
`git_commit` on both sides. All three full years then curated: **34.7 M + 36.8 M +
40.0 M rows**. *(A first probe run FAILED BE-C on a probe artifact — the two legs wrote
different `year` partition keys — and the harness was corrected rather than the bar
moved; recorded so the PASS is not read as first-try.)*

### 2b. INCIDENTAL FINDING — the committed summary CSV is **STALE**

`caiso_offer_surface_summary.csv` and `caiso_offer_surface_condbinned.json` are written
by the **same `main()` call from the same `ladder` object**
(`summary_rows.append({..., f"rung{i+1}_mult": ladder[i][1]})` beside
`binned_ladder.append(ladder)`), so they cannot legitimately disagree. They do:

* committed JSON vs committed CSV — **0 of 8** ladder bins agree;
* committed JSON vs **re-derived** CSV — **8 of 8** agree.

The committed CSV is therefore from an earlier (pre-Theil-Sen) run that was never
refreshed when caiso-153 promoted the re-derivation. **No loader reads it** (verified: it
is a human-readable summary; only two historical probes redirect it to their own scratch
dirs), so nothing consumed is affected. The refreshed CSV is committed here as the repair.

---

## 3. TWO CORRECTIONS TO THIS SESSION'S OWN INSTRUMENT — reported, not quietly applied

1. **IT-2 leg (b) was pre-registered but missing from the first implementation.** Only
   leg (a) ran, and on leg (a) alone all four candidates "passed". Leg (b) — the G1
   reconciliation — was implemented and the test re-run. **No bar was moved**; a
   pre-registered leg that had not been executed was executed.
2. **The route selector counted a pass on an already-covered boundary as
   coverage-extending**, which would have reported ROUTE = SEPARATION off the 9.152 cut.
   Fixed to require that a passing cut involve an uncovered class.

Both corrections ran **against** this session's ability to build an arm, and both are
recorded here rather than folded silently into the result.

---

## 4. GATES

| gate | status |
|---|---|
| **G-DOF** | **N/A — no arm built.** Ledger unchanged 11 / 8. See §5. |
| **G-NOFIT** | **HELD** — zero new fitted scalars; nothing entered the LP at all. |
| **G-FROZEN** | **HELD** — `BODY_FRAC` 0.35, `GAS_MIN_R` 0.6, `hr_cut` 8.5, Theil-Sen, `GAS_SLOPE_RANGE`, `GAS_MIN_DAYS`, `MIN_CAP_MW` all byte-unchanged; the deriver ran **unmodified** and its output proves it. |
| **G-C1 / G-CAISO180 / G-PROT / G-LOYO / CONTROL** | **NOT REACHED** — they gate an arm, and no arm solved. |

## 5. THE G-DOF GRANULARITY DEFECT — filed at P0, and it stands

Pre-registered in PRECHECK §7a **before any arm was attempted**, so it cannot be read as
an excuse for a gate the work failed. `offer_curve_by_group` is **one** ledger entry of
**112 scalars** spanning CC_REGULAR, CC_INTERMEDIATE, CC_CHP, CT_CHP, CT_PEAKER,
CT_INTERMEDIATE, ST_GAS, ST_GAS_INTERMEDIATE and five COAL_* groups. A coverage
extension retires 9–12 *scalars* inside it but cannot move `n_residual` off 8, because
the `*_INTERMEDIATE` groups, the COAL groups, every `committed` band, `econ_low_share`
and `pct_peaking` remain fitted. The only offer-path entry small enough to retire whole
is `offer_curve_committed_below_floor[CAISO]` (1 scalar, ST_GAS `committed` 0.81) — and
retiring it means arming a measured **committed** band, which the deriver's own frozen
method refuses (step 5, the Lever-A inversion lesson, rule 19). Splitting the entry
would push `n_entries` to 12, an automatic fail.

**So G-DOF as chartered is unachievable by the chartered ARM A object, for a reason
internal to the ledger's granularity rather than to the work.** It is moot this session
— no arm was built — but it will bind any future attempt and is **escalated to the owner**
as a charter/ledger item.

## 6. Governance

Rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`: no mechanism was judged by its effect on
the fit; the refusal is an identification failure, not a residual outcome. Rule 13
`[R-MEASURED]`: **nothing was tuned to C3a, which was never scored this session** — no
adder, no haircut, no band. Rule 15 / 16: **no solve, therefore no bundle and no
registration** — stated so the absence is not mistaken for an omission. Rule 21
`[R-DOF]` / rule 23 `[R-FROZEN-DERIVE]`: the corrected basis of PRECHECK §1b was honoured —
rule 23 is **not** triggered (the offer path consumes OASIS bids + citygate, neither of
which changed on 2026-07-24, and nothing in it consumes the outage envelope), so **no
frozen identification constant was re-valued**; the deriver ran unmodified. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; no out-of-training year solved, scored, registered or
read; freeze respected, both markers untouched. Rule 24 `[R-REGISTRY]`: no field added or
re-valued, no off-registry channel. Rule 25 `[R-ISO-SCOPE]`: CAISO-scoped; no other ISO's
keeper shard, registry sidecar, status part or bench file read or written. Rule 27
`[R-PUSH]`: the pre-registration was pushed and blob-verified before any metric was read;
every push blob-verified (all files ≥300 lines MATCH); no large file rewritten from
regenerated content. Rule 28 `[R-MECH-MATRIX]`: §5.2 stamped in this session;
**no cell verdict moves** — `measured_offer_surface` CAISO stays **K**, since the
mechanism was neither rejected nor found inert, only found un-extendable.

**DO-NOT-REDO honoured in full** — `battery_dispatch_adder` not re-opened or re-derived;
`_degradation_cost_per_mwh` routing closed; the AS-power-reservation family closed; the
N–S topology lever FORBIDDEN and untouched; `caiso_ps_charge_shape_anchor` stays `G`; the
seam/intertie family STRUCK; `unit_outage_short_windows` / `unit_partial_outage_windows`
not re-tested; the outage envelope's DEPTH not re-audited (caiso-181 SETTLED it);
`caiso_dam_outages` stays `U` and was **not** armed.

## 7. Disposition and the named successor

1. **The fitted residue on CC_CHP / CT_CHP / ST_GAS STAYS**, because the measured
   replacement **does not identify**. This is a data-identifiability limit of the
   **masked** OASIS disclosure, not a modelling choice: the corpus carries no fuel,
   physics or location column, and the one axis it does recover — marginal heat rate —
   cannot resolve classes whose base HRs sit 0.147–0.84 MMBtu/MWh apart inside a
   distribution 3.87 wide.
2. **ARM B (the caiso-181 H-EDGE grain repair) was NOT built.** It is charter-secondary
   ("run only if A is blocked or after A is adjudicated") and, decisively, its repair
   touches `outages.py`, which **all six ISOs' loaders share** — modifying it before a
   control arm exists would put CAISO's required **$0.000** same-head control drift at
   risk. It remains available, unstarted, and its write/loader sites are now located
   precisely: `derive_campd_unit_outages.py:1417-1437` (detects in hours, writes
   `strftime("%Y-%m-%d")`) and `outages.py:519-523`
   (`pd.Timestamp(r.outage_end) + pd.Timedelta(days=1)`).
3. **No promotion, and none was ever available** — no arm, no solve, and C3a is a live
   FAIL so a C3a move could never be the basis (rule 1).
4. **No existing adjudication is repealed.** Nothing was tested that could repeal one.

## 8. Known-open, carried forward

1. **The N–S congestion majority** — model 5.2 / 2.4 / 2.9 % of the measured NP15–ZP26
   basis; the N–S topology lever stays **FORBIDDEN** (caiso-164 §0/§6).
2. **C3a's first named contributor is the WALLED hourly PS water state**
   (`FINDING-caiso140` §B / caiso-141 A2) — an **owner-funded non-public intake**, not a
   session lever. Its second named contributor was located by caiso-181 in the offer
   curves; **this session establishes that the measured route into the uncovered part of
   those curves is closed**, which narrows the remaining offer-curve options to the two
   covered classes (already measured) and the `committed` bands (deliberately unarmed).
3. **`battery_dispatch_adder` is a PERMANENT DECLARED-RESIDUAL DOF** — all three exits
   closed (caiso-176/178/179). Its ledger `root_cause` still needs re-wording by a
   keeper-lane session.
4. **`unit_outage_maxgen_events` is a CAISO DATA GAP** (no registry exists) — data-intake
   charter; reported, not armed.
5. ~~`curate_dam_public_bids.py` cannot process a full CAISO year~~ — **CLOSED** this
   session (§2a).
6. **NEW: the G-DOF ledger-granularity defect** (§5) — owner item.
7. **NEW: the corpus is gitignored and does not survive a fresh container.** Any future
   offer-surface session must budget a full re-fetch (~1,096 rate-limited requests).
   caiso-178's "FETCHED IN FULL" is a statement about a container, not the repo.
