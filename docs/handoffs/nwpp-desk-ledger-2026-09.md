# NWPP Addition Desk — ledger (2026-09)

The live record of the NWPP addition program. **This ledger wins where it and
`docs/multi-iso/nwpp-addition-plan-2026-09.md` diverge on live state**; the plan owns the charters
(§8) and the decisions (§3), this owns who is running what.

Refresh discipline: one refresh = one §0 entry = one ledger commit = one small PR, off a branch
recreated fresh from `origin/main`.

---

## 0. Live state — newest entry FIRST

### r#7 — 2026-09-16 — the owner asked for FIXES to R-f and R-j; **one has one, one does not** — NWPP-37 + NWPP-38 ISSUED (main `8b9b32e4`)

**Owner, verbatim: *"Ok do you have fixes for 1 and 2"*** — routed items **R-f** (the defective 930
hydro column) and **R-j** (the PNCA termination). The desk diagnosed both at the tree rather than
answering from the routing note, and they are **not the same kind of problem**:

---

**R-f — YES, AND THE DEFECT IS LOCATED TO THE LINE.** Traced this sitting:

- `_screen_fuel_spike_columns` (`actuals.py:219`) already exists and is **exactly the two-statistic
  screen NWPP-10 asked for**: an hour is repaired only when it clears 2.5× BOTH the series median AND
  its own p99.9 robust peak. It is well-built and its rule-13 admissibility argument holds.
- **Its docstring claims** *"this seam screens the frame every reader in this module obtains, so no
  consumer can reach an unscreened copy (rule 19)"*. **That claim is true only of readers inside
  `actuals.py`.** Measured: the screen is applied at exactly three call sites — `actuals.py:351`,
  `:412`, `:488` — **all three in that one module**.
- **`envelopes.py` is not in that module.** It obtains its frame at `:109` and `:167` by calling
  `frames._eia_hourly_frame_filled(ba, year)` **directly**, and that function does **no screening at
  all** — read in full, it only reindexes present rows onto the complete hourly clock. So
  `measured_monthly_hydro`, `measured_hydro_min_flow_level` and the month × hour-of-day envelope read
  the **RAW** `NG: WAT` column, exactly as NWPP-32 §7 reported.
- **So NWPP-32 was right and the screen's own docstring is wrong.** The gap is plumbing, not a
  threshold question: the AVA hour at 810,113 MW is roughly **1,350×** that series' own robust peak
  against a **2.5×** bar, so the existing screen would catch it trivially. NWPP-10 found and repaired
  the twin defect in the DEMAND column; the generation side was simply never routed through the
  screen that already existed for it.

**Chartered as NWPP-37 `[FABLE]`** — shared EIA-930 loader, so the licence is narrow and the exit is a
**nine-region byte-identity table**. The lane chooses between (A) moving the screen into `frames` so
the rule-19 single-seam claim becomes *true*, and (B) screening at the two envelope read sites —
**(A) only if it proves byte-identical for every pre-existing region**, otherwise (B), and never (A)
with a moved row explained away. The screen's already-measured effect (SPP 2023 wind, NYISO 2024
other, NYISO H1-2026 other, one wind profile) is handed over as the control set: anything beyond it is
a new effect and must be named. **The docstring is repaired too** — it currently asserts a property
the code does not have.

---

**R-j — NO, AND PROPOSING ONE WOULD BE INVENTING A REGIME.** The desk says this plainly rather than
manufacturing symmetry with R-f:

- The PNCA **terminated 2024-09-15 with no successor text found** (NWPP-32 §4, §7 item 5). It is the
  instrument that defines *"Period means a calendar month"* — the accounting period the model's hydro
  budget already uses. So the coordinating instrument for 56 % of the footprint's hydro changed
  **inside the scored window**.
- **This is not a defect.** It is a real-world discontinuity, and there is **nothing to model to**: no
  successor instrument exists to encode. A post-PNCA operating regime built from inference would be
  precisely the fitted mechanism rule 1 `[R-STRUCT]` forbids — and NWPP has **no price benchmark**
  against which such a mechanism could ever be validated, since NWPP-13 read NO. A desk that shipped
  one would be inventing structure and calling it a fix.
- **What IS available, cheap and decisive is the measurement nobody has made: does it bite at all?**
  NWPP-32's artifacts already carry what it needs — per-plant monthly budgets 2023–2025 and
  `nwpp_hydro_chain.csv`.

**Chartered as NWPP-38 `[OPUS]`, a MEASUREMENT lane that writes no code.** It tests the eleven
mainstem plants across 2024-09-15 on the quantities the monthly budget does not already fix by
construction (within-month shaping, diurnal amplitude, the chain's correlation structure, the
inter-project lag). Its hard part is stated as the hard part: **2024 and 2025 are different water
years**, so the identification strategy is declared BEFORE the numbers, and the independent tributary
systems NWPP-32 named (Skagit, Cowlitz, Lewis, Deschutes, Willamette, Baker, Nisqually) are the
control group — outside the PNCA's coordination object in the same water years. Three outcomes are
all successful and the lane is told it may not prefer one: no measurable change (with the test's
POWER stated), a measured change (magnitude reported, **mechanism NOT proposed — that decision is the
owner's**), or confounded-and-unseparable, said plainly.
**Binding data caveat carried into it:** the 2025 pooled series still has R-f's defective hours, so
NWPP-38 either waits for NWPP-37 or screens them itself and *says* it did — it may not read the raw
column and report the result as clean.

---

**Why the asymmetry is the honest answer.** R-f is a plumbing gap between two pieces of code that
already exist, and it has a located fix. R-j is the world changing mid-window. The temptation is to
give the owner two fixes because two were asked for; the correct response is one fix, one
measurement, and the reason stated. **NWPP-40's PRECOMMIT declares R-j regardless of what NWPP-38
finds** — the declaration is not contingent on the measurement.

**Gates:** not re-run at this pin — this refresh is program documents only and `8b9b32e4` is the same
pin r#6 measured six gates at, with the three failures carrying **zero NWPP mentions**. Recorded as
r#6's exits, unchanged, rather than re-asserted as fresh.

**Next act:** grade NWPP-36, NWPP-37 and NWPP-38 by content as they land; then serve card **N10** and
charter **NWPP-40**. NWPP-37 is now a soft precondition on NWPP-38 and on NWPP-40's hydro reads.

---

### r#6 — 2026-09-16 — **ALL SIX W3 LANES LANDED** · the region count is NINE · **W3b / NWPP-36 ISSUED** against NWPP-32's specification (main `8b9b32e4`)

**Re-count at this desk's own pin (handoff §0.3) — the count moved AGAIN, and the desk measured it
rather than carrying r#5's number forward:**

| Surface | r#5 (`c6c70190`) | **r#6 (`8b9b32e4`)** |
|---|---|---|
| `_ISO_BUILDERS` / `SUPPORTED_ISOS` | 8 | **9** — SOCO registered between the two sittings |
| `mech_matrix.ISO_ORDER` / matrix `isos` / shards | 9 / 9 / 9 | **9 / 9 / 9 — now CONSISTENT** |

The eight-registry-over-nine-matrix intermediate state r#5 recorded has closed on its own, exactly as
expected. **NWPP-35 independently measured NINE and led its FINDING with it** — *"the region count is
NINE, not seven and not eight"* — which is the §0.3 discipline working in a lane rather than only at
the desk.

**ALL SIX W3 LANES LANDED. Graded by content.**

| Lane | Verdict |
|---|---|
| **NWPP-30** | **LANDED** — outage windows + thermal tranches, with the coverage arithmetic stated at the top as chartered |
| **NWPP-31** | **LANDED — GATE G9 PASSES EXACTLY.** "the non-NWPP diff is EXACTLY ZERO": all **7 pre-existing regions byte-identical** in `calibration_reference.json` and all **36 pre-existing `*_renewable_capacity.csv` byte-identical**. The price side is skipped per G6 **and verified skipped by execution**, not by assertion |
| **NWPP-32** | **LANDED — and it is the best lane this program has run.** Reconciliation PASS at **0.000 MWh** for every plant, every year, against a 1.0 MWh pre-registered tolerance; predictions P1–P4 all held; **263 plants absent from the 2025 early release read `NO_923_SERIES` and stay absent** — nothing filled |
| **NWPP-33** | **LANDED** — zonal shares, measured per-zone VRE shape, per-zone gas basis |
| **NWPP-34** | **LANDED** — the BPAT identity trap adjudicated and the R-a CAISO seam **quantified**, so the routed item now carries a number |
| **NWPP-35** | **LANDED** — region count corrected to NINE across the site; `docs/calibration-log/nwpp.md` now exists (header only, per §8.0 rule 1) |

**NWPP-32 CORRECTED THIS DESK'S OWN CHARTER, AND THE CORRECTION IS CARRIED.** The r#5 charter told the
lane the chain contained *"eight plants ≥ 1 GW holding 17,821.8 MW"* and listed **Boundary** among
them. Measured against the ORNL EHA FY2024 `Water` field: **seven of those are mainstem (16,662.1 MW);
Boundary (1,159.7 MW) is on the Pend Oreille**, which reaches the Columbia only through Canada and is
**coupled to nothing else in this footprint**. Had NWPP-36 been chartered from the desk's list it
would have built a coupling link that does not physically exist. The correction is written into
NWPP-36's charter in the lane's own terms, flagged as the desk's error.

**THE CHAIN, AS MEASURED — this is what NWPP-36 is built against, and it may not re-derive it:**
eleven mainstem plants (Grand Coulee → Chief Joseph → Wells → Rocky Reach → Rock Island → Wanapum →
Priest Rapids → McNary → John Day → The Dalles → Bonneville), **20,098.8 MW = 56.14 % of the
footprint's conventional hydro** and **58.84 % / 57.96 % of its 2023 / 2024 hydro energy**; the lower
Snake (4 plants, 3,033.0 MW) entering at the McNary pool, fed by Hells Canyon (3, 1,276.1 MW) and
Dworshak. **Coupled chains total 24,408 MW = 68.2 % of hydro.** The hydrological fact behind the order
is BPA's own published discharge rising monotonically down the chain, 107,700 → 183,300 cfs.

**`HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NWPP"]` IS EMPTY, and that is the right answer.** Eight
instruments read or attempted; none states an energy-conservation period for a named plant; the one
coordinating instrument that defines an accounting period — the 1997 PNCA — defines *"Period means a
calendar month"*, which is already the model's default. The lane pre-registered this as prediction P4
and it held. An empty entry set was named a good outcome in the charter and it is one.

**NWPP-36 ISSUED.** Its charter is composed entirely from NWPP-32 §5–§6 and is committed at plan §8
W3b. What the desk fixed in composing it, beyond the Boundary correction:

1. **The rule-19 sentence, stated so the lane cannot drift past it:** *the coupling redistributes WHEN
   energy is produced and NEVER changes HOW MUCH per month.* The EIA-923 monthly budget stays the sole
   energy-quantity mechanism; a coupling that can move a monthly total is a second budget and is
   refused.
2. **Two quantities must be MEASURED, not assumed**, because NWPP-32 searched and reported them
   unpublished at mechanism precision: **τ per link**, from the USACE/CROHMS hourly project-outflow
   feed by cross-correlating adjacent projects' discharge; and the **pondage bound per run-of-river
   link**, from NID. BPA's "three to five feet" is the published ORDER, not the number. If either
   cannot be measured the lane STOPS rather than substituting a plausible value.
3. **Gate G8 is now a NINE-region proof**, not seven, and the keeper ids are re-read at the lane's own
   base sha because promotions move them.
4. **Rule 28(c) is now EIGHT foreign cell lines plus its own**, the matrix having reached nine shards.

**ROUTED — five new items from NWPP-32 §7, recorded in §3 and not fixed here.** The first is the one
that matters for W4:

| # | Item |
|---|---|
| **R-f** | **The NWPP pool `NG: WAT` series carries the G20 defective hours** (AVA 810,113 MW at 2025-10-12 10:00 UTC and four more; NWMT 65,891 / 65,880 in 2024). NWPP-10's repair was **demand-side only**, but `measured_monthly_hydro`, `measured_hydro_min_flow_level` and the envelope read the **unrepaired** column. **Until repaired, `eia930_monthly` and the 930-derived hydro floors/envelopes are UNSAFE for NWPP 2024–25.** NWPP-32's posture — `backfill_year=2024` alone, the 2025 repin **refused on rule-14 grounds** — stands until a lane fixes it. **NWPP-40's PRECOMMIT must state this.** |
| **R-g** | **930-vs-923 population mismatch, −2.7 TWh and stable**: WAUW (−2.6/−2.8) and PACW (−0.7) file their EIA-923 hydro plants under other EIA-930 BAs; Priest Rapids sits in BPAT (860) and GCPD (930). Any level pin between the two series needs a reconciliation the loader does not have |
| **R-h** | **Swift 2 (72 MW, PACW)** has no EIA-923 series in either complete year — an id question |
| **R-i** | `curate_hydro_plant_modes.py` registers CAISO only; an NWPP curation is a W4/W5 lever (`hydro_ror_split`), with §5(d) as its evidence |
| **R-j** | **The PNCA TERMINATED 2024-09-15** with no successor text found — the coordinating instrument changes **inside the scored window**. NWPP-40's PRECOMMIT states it |

**Gates at `8b9b32e4` — 6 run, exits recorded, none carried forward. Every failure checked for NWPP
content: `grep -ci nwpp` = 0 on all three.** Unchanged in character from r#4 and r#5 — other regions'
promotion debris, disclosed and routed (handoff §0.5), never fixed here (rule 25).

| Gate | Exit | NWPP mentions |
|---|---|---|
| `audit_keepers --check` · `check_registry_payload_parity` · `check_gate_a_provenance` | **FAIL** | **0 · 0 · 0** |
| `check_mechanism_matrix` · `check_bench_freshness` · `check_golden_manifest` | **PASS** | 0 |

**Next act:** grade NWPP-36 by content when it lands, then serve card **N10** (the first-solve screen)
and charter **W4 / NWPP-40** — which is now the only thing between this program and its first keeper,
and which inherits R-f and R-j as PRECOMMIT duties. Card **N9** still waits on that keeper.

---

### r#5 — 2026-09-14 — **NWPP IS REGISTERED** (NWPP-20 landed) · W3 chartered and ISSUED, all six lanes (main `c6c70190`)

**THE PIN FLIPPED. NWPP is the EIGHTH registered region.** Re-counted at this desk's own pin, not
taken from the lane's claim (handoff §0.3):

| Surface | At `c6c70190` |
|---|---|
| `_ISO_BUILDERS` / `SUPPORTED_ISOS` | **8** — ERCOT CAISO MISO PJM NYISO NEISO SPP **NWPP** |
| `solve_surface.SURFACE_ISOS` | **8**, NWPP appended LAST with the gate-G1 comment in place |
| `mech_matrix.ISO_ORDER` / matrix `isos` | **9** — SOCO is matrix-seeded but **NOT registered** |

A nine-column matrix over an eight-region registry is the supported intermediate state the SOCO desk
measured and NWPP-21 relied on; it is not a half-landed matrix.

**NWPP-20 GRADED BY CONTENT.** What the lane claims, and what this desk verified independently:

| Claim | Desk's verification |
|---|---|
| Gate G1 atomicity | `SURFACE_ISOS` carries NWPP with an in-place comment citing the same commit as `_ISO_BUILDERS` and `DEMAND_LOADERS` — **confirmed structurally** |
| Gate G8: zero moved rows, **all 19 stored keeper configs across the seven incumbent regions re-derive byte-identical `cache_key()`** | **UNREAD by this desk** — the container has no `pydantic`/`numpy`, so no import-level check was possible. Recorded as the lane's measurement plus CI, **not** as a desk verification. Said plainly rather than implied |
| Card N5 — five zones, BA-keyed | `zone_assignment._NWPP_BA_ZONES` exists and is keyed on Balancing Authority Code; `_iso_ba_codes` membership path in use — **confirmed** |
| Card N8 — legacy bins | NWPP **absent** from `CAMPD_BINNING_ISOS`, `use_campd_bins=False` documented at `iso_configs.py:2058` — **confirmed** |
| Card N7 — one PRM scalar, declared | `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"] = 0.144` with the two-regime mismatch declared — **confirmed present** |
| Card N4 — served interchange, links off | `INTERFACE_NEIGHBORS["NWPP"]` = CAISO / WECC_SW / WECC_CAN, every block `enabled=False`; `_SCALAR_INTERCHANGE_ISOS` carries NWPP — **confirmed** |
| Census 939 / 1,930 / 98,238.1 MW | reproduced by the lane's curated-fleet extension — **UNREAD by the desk** (same import limitation) |

**R-e IS CLOSED, AND THE FIX IS BETTER THAN WHAT WAS RECOMMENDED — the desk records this in the
lane's favour.** NWPP-10 proposed a codes-tuple plus membership. The lane did that (`ISO_TO_BA_CODES:
dict[str, tuple[str, ...]]` + a `ba_codes(iso)` accessor, and all 13 call sites migrated — verified at
`hydro.py` 610/642/687, `eia860.py` 1693/2633/2807, `campd_bins.py` 168 and `zone_assignment.py`
1214/1242/1450). But it went one step further, and the step matters: **the scalar `ISO_TO_BA_CODE` is
now built only from regions with exactly ONE code** (`{iso: codes[0] ... if len(codes) == 1}`), so
**NWPP deliberately has no entry at all** and `ISO_TO_BA_CODE.get("NWPP")` returns `None`. That
converts the failure mode from **silent** (an arbitrary 1-of-17 BA, an empty result indistinguishable
from "none") to **loud** — any consumer not yet migrated breaks visibly instead of quietly modelling a
seventeenth of the fleet. That is the right shape for the single most dangerous silent bug this
program identified, and it is a stronger answer than the desk's charter asked for.

**W3 IS CHARTERED AND ISSUED — all six lanes.** §8's W3–W6 section carried only *deltas* and directed
the desk to compose the charters against the SPP program's worked W3. That composition is this
sitting's work and is now committed at plan §8 W3: **NWPP-30** (outages + tranches) · **NWPP-31**
(benchmarks) · **NWPP-32 `[FABLE]`** (the hydro budget) · **NWPP-33** (zonal shares, VRE shape, gas
basis) · **NWPP-34** (seam derive) · **NWPP-35** (site prose + log header). All parallel, all
file-disjoint, `DATA PROFILE: nwpp` except NWPP-35 (`code`).

**Three things the desk fixed in composing them, which a naive copy of SPP's W3 would have got
wrong:**

1. **NWPP-30's output has two destinations and card N8 split them.** Outage windows are read by the
   first keeper regardless of binning; the thermal tranches feed the pre-declared W5 CAMPD-per-plant
   lever and **nothing in W4 reads them**. A charter that did not say so would have had the lane
   arguing to arm per-plant binning against a ruled decision.
2. **NWPP-31's price side is entirely negative work.** No `actual_lmp.json` block, no
   TAIL_THRESHOLD, no amplitude derive, no hub substitution — and the determination-side consequence
   is already built by NWPP-22. Its real deliverable is the gate-G9 zero-diff proof.
3. **NWPP-34 must not write the naive identity derive.** BPAT is 20.26 % of footprint load and its
   balance identity misses by more than 1 MW in **81.5 % of hours** (mean −3,206 MW) because BPA
   wheels energy it neither generates nor serves. Every charter that touches interchange now carries
   that measurement.

**NWPP-32 also carries the half that is easy to miss: it is writing NWPP-36's specification.** Owner
ruling N3 put cascade coupling before the first keeper, and NWPP-36 is built against NWPP-32's
measurement of the four §2.7 constraints — so that measurement is a deliverable, not a discussion, and
the mainstem chain is stated as *a hydrological fact to be cited, never a list to be chosen*.

**What NWPP-21 already landed, so no W3 lane duplicates it:** the `--iso-nwpp` colour token
(`#65A30D`) with its badge and button rules, the NWPP matrix shard, and the §5.9 lever queue. Stale
there and flagged to NWPP-35: §5.9's header still reads "NOT YET REGISTERED".

**Gates at `c6c70190` — 6 run, exits recorded, none carried forward. Every failure was checked for
NWPP content and NONE contains any** (`grep -ci nwpp` = 0 on all three failing outputs), so all three
remain other regions' promotion debris, disclosed and routed (handoff §0.5), never fixed here
(rule 25):

| Gate | Exit | NWPP mentions |
|---|---|---|
| `audit_keepers --check` | **FAIL** | **0** |
| `check_registry_payload_parity` | **FAIL** | **0** |
| `check_gate_a_provenance` | **FAIL** | **0** |
| `check_mechanism_matrix` | **PASS** | 0 |
| `check_bench_freshness` | **PASS** | 0 |
| `check_golden_manifest` | **PASS** | 0 |

**A limitation this desk states rather than papers over:** this container carries neither `pydantic`
nor `numpy`, so **no import-level verification of the registration was possible here** —
`get_iso_config("NWPP").validate_topology()` is UNREAD by the desk. Everything above marked confirmed
was verified by reading the committed source; everything marked UNREAD rests on the lane's own
measurement and on CI. A desk that reported the cache-key proof as its own finding would be claiming a
check it did not run.

**Next act:** grade the six W3 lanes by content as they land, then charter **W3b / NWPP-36** at the
sitting that follows NWPP-32 — its input is NWPP-32's §2.7 measurement and it may not start before it.
Card **N10** is served at the sitting that opens W4; card **N9** still waits on a keeper.

---

### r#4 — 2026-09-14 — ALL OF W1 + W1c LANDED · cards N4/N5/N7/N8 RULED, N6 resolved by measurement · **W2 UNBLOCKED, NWPP-20 ISSUED** (main `39a1c9a1`)

**Every lane this desk has ever issued has now landed.** Graded by opening artifacts on `main`, never
a branch name or a green check (gate G15):

| Lane | Verdict | What the artifact actually says |
|---|---|---|
| **NWPP-10** | **LANDED** | census CONFIRMED to the MW on the headline; **3 technology rows CORRECTED** (gas ST 2,393.0 · gas ICE 737.5 · solar PV 10,051.3; MT 6,939.6), total unchanged. TRE row **REJECTED** on a two-key test, **plus two more rows the charter never found**. Demand convention established — and it found a screen that *would have destroyed a real annual peak* |
| **NWPP-11** | **LANDED 5/5** | CEMS ID/OR/UT/WA · the 17-BA derive · DIBA · EIA-923 monthly hydro · a BPAT divergence reported, not corrected away |
| **NWPP-12** | **LANDED** | **G12 PASSES** · WRAP binding = Winter 2027–28, out of window · **NW↔OR has no path rating and never will** |
| **NWPP-13** | **LANDED — NO** | D3 fails: WEIM on-peak 22.6/23.6/37.5 % below Mid-C against a ±10 % bar. **D2 PASSED** (5.5–6.2 % net, 10.6 % gross) |
| **NWPP-21** | **LANDED** | the **ninth** shard, `ev = "W"`. It re-counted after SOCO-21 landed mid-flight — exactly the rebase the r#3 un-hold accepted, handled as G2 designed |
| **NWPP-22** | **LANDED — and WITHDRAWN IN FAVOUR OF `main`** | see below; definition-of-done row 7 is **MET** |

**NWPP-22's resolution is the honest item of this sitting, and the desk records it against itself.**
The lane built the class, measured **7/7 keepers byte-identical**, then found on rebase that an
identical class had already landed from another program's lane. Rather than ship a second
implementation — which would be the doubled mechanism rule 19 `[R-ONE-MECH]` forbids — it **withdrew
its own scorer edit whole** (`git diff origin/main -- scripts/calibration_verdict.py` empty) and
adopted `main`'s, keeping its PRECOMMIT, its FINDING and a trimmed NWPP test file. It then did the
thing that makes the withdrawal safe: **a leg-by-leg predicate comparison proving nothing was lost**,
with named tests for each subsumed leg.

**Verified by this desk rather than taken on the lane's word:** `RUBRIC_VERSION = 3.8`; the strings
`PHYSICALLY-CALIBRATED (PRICE UNSCORED)` / `...-WITH-CAVEATS (PRICE UNSCORED)` exist at lines 541–542;
the predicate at line 3590 is `_price_reference_absent(iso) and all(...)` — **data-driven, no
`if iso ==` ladder**; `actual_lmp.json` carries **exactly the seven pre-existing ISOs**, so **NWPP
reaches the class and it is structurally unreachable for every ISO that has a block**; both test files
are on `main`. **Definition-of-done row 7 is MET and NWPP-40 is no longer blocked on the scorer.**

**ERROR AGAINST INTEREST — E-3, recorded in §6.** At r#2 this desk wrote that one branch serves both
programs and that two desks chartering it would produce two. The owner then directed the desk to stop
coordinating and send it now; both lanes were chartered; the other landed first; **this program built a
scorer implementation that was then discarded.** The desk is not second-guessing the directive — NWPP
got the class, it landed sooner, and a *delayed* NWPP-22 would have left the program blocked on another
desk's schedule, which is exactly what the directive was preventing. But the cost was real and is
stated: one lane's implementation was written and withdrawn. **Partly offset**: the withdrawal produced
an independent leg-by-leg cross-check of the surviving predicate that a single-lane build would not
have produced, and the desk verified NWPP's reachability from that comparison rather than assuming it.

**CARDS RULED AT SITTING #4 — all four as the desk recommended.** Full text in plan §3; N6 needed no
card:

| Card | Ruling | The measured fact behind it |
|---|---|---|
| **N5** topology | **FIVE ZONES, as scoped** | 4 of 5 boundaries carry a published WECC rating; **two are clean Tier-1 candidates** (Path 35, Path 16). NW↔OR is a **documented absence**, which is a positive result |
| **N7** adequacy | **ONE SCALAR NOW, DECLARED**; per-zone seasonal → lever NWPP-57 | 8 winter / 6 summer / 1 flipping BA; SNV peaks summer at **1.95–2.06×** its own winter load. WRAP binds Winter 2027–28 — **out of window** |
| **N4** CAISO seam | **SERVED MEASURED INTERCHANGE, priced links default-OFF** | a priced seam is unvalidatable when NWPP-13 read NO. **BPAT's balance identity fails structurally**: −3,206 MW mean, 81.5 % of hours |
| **N8** fleet | **LEGACY HEAT-RATE BINS**; CAMPD per-plant → W5 lever | CAMPD reaches 30.98 % nameplate / 41.8–43.6 % energy, and **36.3 % of the footprint is hydro CEMS can never cover** |
| **N6** timezone | **RESOLVED BY MEASUREMENT — no card** | 14 Pacific / 3 Mountain; **IPCO files Pacific**; all 6 DST transitions correctly signed. **UTC is canonical**; gate G19 closed |

**R-e IS CONFIRMED AND IT IS BIGGER THAN THE PLAN SAID — scope correction adopted.** Plan §2.3 called
`data/zone_assignment.py` "the one genuinely novel code change in W2". NWPP-10 §3 measured otherwise:
the object is **`ISO_TO_BA_CODE`** (`models.py:221`), its `{iso: ba for ba, iso in ...}` inversion
**silently keeps only the last BA**, and there are **13+ live call sites across five modules** — every
one failing silently with an empty or 1/17 result, never an exception. The one that matters most:
**`data/hydro.py` 607/639/684 would cover 1/17 of the fleet — card N3's OWN machinery**, which NWPP-32
and NWPP-36 both read. The correction, and NWPP-10's recommended codes-tuple shape, are written into
NWPP-20's charter with the byte-identity proof extended to cover it explicitly.

**NWPP-20 ISSUED**, verbatim from plan §8 as **corrected at this refresh** — preconditions rewritten
to record that all four are met, the R-e scope correction, the five ruled zones with their TTC tiers,
the demand convention (including *do not* run `_screen_demand_spikes`), the footprint admission
predicate, the curated-fleet seam, the census corrections, the TAIL_THRESHOLD skip, the timezone keys
and the adequacy declaration.

**Gates at `39a1c9a1` — 6 run, exits recorded, none carried forward.** No NWPP object appears in any
failure; every one is another region's, disclosed and routed (handoff §0.5), never fixed here (rule 25):

| Gate | Exit | |
|---|---|---|
| `audit_keepers --check` | **FAIL** | 5 failures / 4 warnings — E13 promotion debris (MISO, SPP) + stale status files. Routed |
| `check_registry_payload_parity` | **FAIL** | `caiso279_ablate_dswcouple_span`, `soco15_spp_arm` unregistered. Routed |
| `check_gate_a_provenance` | **FAIL** | SPP cites a superseded keeper **and** a marker mismatch (`complete=True` vs claimed False) — the verdict-flipping half of F-5. Routed |
| `check_mechanism_matrix` | **PASS** | warning: NYISO shard stamp drift vs its new keeper. **NWPP.js present, 9 `isos`, `ev = "W"`** — NWPP-21 verified |
| `check_bench_freshness` | **PASS** | 34 parts, 0 stale |
| `check_golden_manifest` | **PASS** | OK |

**Next act:** grade NWPP-20 by content when it lands, then W3 (NWPP-30/31/32/33/34/35) and W3b
(NWPP-36). Card **N10** (the first-solve screen) is deferred to the sitting that opens W4 — it governs
a solve that cannot start until W3b lands. **Card N9** (forecast entry) still waits on a keeper.

---

### r#3 — 2026-09-13 — W1 GRADED (3 of 4 landed, NWPP-13 read NO) · card N11 RULED "SEND IT NOW" · NWPP-22 + NWPP-21 ISSUED (main `33a7c961`)

**Owner directive that opens this sitting: *"Ignore SOCO desk you focus on nwpp."*** The desk drops
the coordination posture. Two things change and one deliberately does not:

- **R-c is rewritten as an NWPP-owned item** (§3). It previously routed the scorer branch to the SOCO
  desk's card S11 and asked the owner only to note that its scope covered NWPP. That is exactly the
  deferral the directive ends.
- **NWPP-21 is UN-HELD and issued.** Its only blocker was C-2 — waiting on SOCO-21, which is *still*
  unlanded at this pin (7 `isos`, 7 shards, zero `SOCO` in `mech_matrix.py`). With the posture
  dropped, the hold has no basis: **gate G2 and the charter's own first instruction were written for
  precisely this** (*"read the base file's `isos` list AT YOUR OWN BASE SHA … never hard-code the
  count"*), and §8.0 rule 3 rebases. Residual risk, stated rather than hidden: if SOCO-21 lands
  first, NWPP-21 takes a rebase conflict on ~5 lines of one base file. Survivable by design; that is
  what G2 is.
- **What does NOT change: the collision REGISTER stays.** C-1…C-5 are facts about files, not
  deference to a desk. Ignoring a sibling desk's *opinions* is an instruction; colliding with its
  in-flight *edits* would just lose PRs — the failure the SPP program lost four PRs to.

**W1 GRADED BY CONTENT (handoff §0.4 / gate G15) — 3 of 4 LANDED, and the fourth is the one that
matters most.** Graded by opening the artifacts on `main`, never a branch name or a green check:

| Lane | Verdict | Evidence opened |
|---|---|---|
| **NWPP-10** | **LANDED** | `docs/multi-iso/nwpp-data-audit.md`; `FINDING-nwpp-10-2026-09-13.md`; protocol + manifest corrected (`53bea3e0`), plus `3b7fb463` routing six **pre-existing main-branch CI failures** it found — correctly routed, not absorbed |
| **NWPP-11** | **LANDED, 5/5** | CAMPD ID/OR/UT/WA (`73478c98`) · the 17-BA derive from committed BALANCE (`ccafbcaf`) · per-counterparty DIBA (`681680c6`) · EIA-923 monthly hydro (`68e20574`) · FINDING (`feebfd2a`), which reports a **BPAT divergence** as a finding rather than correcting it away |
| **NWPP-12** | **NOT LANDED** | no commit, no FINDING, no `data/raw/nwpp-planning/`. **Not graded LOST** — absence is not evidence (gate G15). It carries gate **G12**, the LTLF edition+vintage that is a hard W2 precondition, so W2 stays blocked on it regardless |
| **NWPP-13** | **LANDED — verdict NO** | PRECOMMIT pushed at `715fff9d` **before any value was read**; FINDING at `976e7724` |

**NWPP-13 READ NO, AND IT FAILED HONESTLY — WHICH IS THE OUTCOME THE CHARTER CALLED SUCCESSFUL.**
The lane's own numbers, not the desk's:

| Gate leg | Bar (pre-registered) | Measured | |
|---|---|---|:--:|
| D1 coverage | — | 2023 partial by OASIS retention, as declared | **PASS** |
| **D2 WEIM volume share** | ≥ 5 % | **5.66 / 5.54 / 6.15 %** net basis (10.6 % pairwise-gross) | **PASS** |
| **D3 Mid-C reconciliation** | ±10 %, corr ≥ 0.80 | **−37.5 / −22.6 / −23.6 %**; corr **0.74 / 0.95 / 0.67** | **FAIL** |
| D4 sanity | — | — | **PASS** |

**The interesting part is *which* leg failed.** The charter's stated worry was that WEIM would be too
thin to price the footprint. It is not — it cleared the volume bar in every year. What failed is the
**price level**: WEIM's on-peak price sits ~23–38 % *below* the footprint's own traded bilateral hub.
That is economically coherent rather than anomalous — an imbalance market clearing the residual of a
mostly-bilateral, cost-based, hydro-rich footprint need not price like the forward bilateral index —
but it means the series prices a different quantity than the LP dispatches, which is rule 14
`[R-ACCURATE]`'s misalignment test failing on its own terms. **Nothing was landed to
`_validation-source`. No bar was moved after the series was seen.**

**CONSEQUENCE, AND IT IS THE WHOLE OF THIS SITTING: card N2 limb (b) is now LIVE, not hypothetical.**
NWPP has **no admissible hourly price series**, so C3a/C3b/C3c cannot be scored for it by any
admissible route (G17 keeps a neighbouring hub refused). The ruled fallback — *a determination naming
its own basis* — is now the **only** route to any NWPP determination at all.

**CARD N11 SERVED AND RULED: "SEND IT NOW."** The desk served the scorer-branch question as a
decision card. The owner directed it be chartered and issued **immediately**, rather than deferred to
W3 or routed outside the desk. Effects, implemented in the plan rather than noted:

- **Plan §1's rubric prohibition is CARVED — once, for this one lane.** That prohibition was written
  when N2 was unruled, so that the desk could not answer its own question; N2 is ruled, and the
  ruling authorized a class the code cannot express. The carve is narrow and stated in §1.
- **New lane NWPP-22 `[FABLE]`** in §5, **new wave W1c** in §4 (issuable now, file-disjoint from
  every other lane — it touches no registry, so it does **not** wait on NWPP-20), a **new charter**
  in §8, and **new gate G25** holding it to the byte-identity exit.
- **Definition-of-done row 7 added**: the class must actually exist, with byte-identical verdicts
  across every pre-existing keeper.

**Why the predicate is data-driven and not `if iso == "NWPP"`** — the one design point the desk fixed
rather than leaving to the lane: the branch fires on the **absence of an admissible series**, which
covers both failure modes identically ("none was ever built" and "one was built and its gate refused
it" both leave `_validation-source` empty). That is also why NWPP-13's NO does not change the lane's
code — only whether the branch fires.

**Issued this sitting — NWPP-22 `[FABLE]` and NWPP-21 `[OPUS]`**, both with §8.0 pasted in and
`origin/main` pinned at this refresh's sha. NWPP-22 is verbatim the charter written into §8 at this
refresh (a charter the plan did not previously carry cannot be issued without first being written
into it — handoff §4). NWPP-21 is verbatim from §8 W2, unchanged.

**Gates:** not re-run at this pin. The r#2 exits were recorded fourteen hours and ~12 merges earlier,
and this refresh touches only program documents — but the honest statement is that they are **UNREAD
at `33a7c961`**, not green. NWPP-10's `3b7fb463` separately routed **six pre-existing main-branch CI
failures**, which is consistent with the r#2 reading that main carries other regions' debris; none of
it is NWPP's.

**Next act:** grade **NWPP-12** by content when it lands (it gates W2 through G12), then sitting #4 —
cards **N4–N8 and N10**, served with NWPP-10's audit and NWPP-11's measured evidence, which are now
on disk. NWPP-22 and NWPP-21 report independently.

---

### r#2 — 2026-09-13 — W1 ISSUED (all four lanes) · SOCO's W1 graded LANDED · G13 repaired, G23/G24 added (main `c93b0d27`)

**Merge-state check first, per the handoff's ⚠ block.** `git show origin/main:…nwpp-desk-ledger…
| grep -c "BUILD CASCADE COUPLING FIRST"` → **2**. The r#1 rulings refresh (`78baed1c`) **has merged**;
main is carrying the post-ruling documents. No recovery from the charter branch was needed.

**Re-count at this desk's OWN pin (handoff §0.3 — neither plan's §2.3 may be executed from its own
number).** Measured at `c93b0d27`, not carried forward:

| Surface | Value at `c93b0d27` |
|---|---|
| `_ISO_BUILDERS` / `SUPPORTED_ISOS` | **7** — ERCOT CAISO MISO PJM NYISO NEISO SPP |
| `solve_surface.SURFACE_ISOS` | 7, pinned equal to `SUPPORTED_ISOS` |
| `mech_matrix.ISO_ORDER` | 7 · `ISO_EV_KEY` taken = `E C P M N Q S` |
| matrix base `isos` (`mechanism-matrix.js:1460`) | 7 · shards on disk: 7 (no `SOCO.js`) |
| `keepers/` shards | 7 |

**SOCO has NOT registered.** "Eighth" and "ninth" remain claims about charter order, not the tree.
NWPP's claimed ev letter **`W`** is free; SOCO's claimed **`O`** is free; no collision.

**Graded BY CONTENT, never by claim (handoff §0.4 / gate G15).**

- **NWPP-10/11/12/13/20/21/36/40 — NOT DISPATCHED.** `git ls-remote --heads origin | grep -i nwpp` →
  empty; no `FINDING-nwpp-*` on main; the only commits matching an NWPP lane id are **this desk's own
  r#1 refresh** (`78baed1c`, three docs). Not graded LOST — never dispatched. The scoreboard stands.
- **SOCO-10, SOCO-11 and SOCO-12 have LANDED**, which the SOCO desk's own r#2 entry could not yet say
  (it recorded them *dispatched and running* at pin `7404ef12`). Graded by opening the artifacts, not
  a CI check: `FINDING-soco-{10,11,12}-2026-09-13.md` are on main; `docs/multi-iso/soco-data-audit.md`
  exists; `00-iso-addition-protocol.md` carries its SOCO row and the corrected count sentence; and
  `fetch_eia930_hourly.BA_TIMEZONE` carries a `"SOCO": "America/Chicago"` key whose comment cites
  *"MEASURED (soco-11, 2026-09-13)"* on two independent agreeing sources.
- **SOCO-13 and SOCO-21 were issued at SOCO r#2 and have NOT landed.** Confirmed structurally, not by
  branch name: `mechanism-matrix.js` still carries 7 `isos`, there is no `SOCO.js` shard, and
  `scripts/lib/mech_matrix.py` contains zero `SOCO` occurrences.

**Collision register, re-resolved at this pin — two of the four moved.**

| # | Status at r#2 | Action taken |
|---|---|---|
| **C-2** matrix base file | **LIVE** — SOCO-21 is issued, running, and unlanded on exactly `mechanism-matrix.js` / `mech_matrix.py` | **NWPP-21 HELD.** It was already blocked; it is now blocked for a *measured* reason rather than a precautionary one. Re-check at sitting #3 |
| **C-4** `00-iso-addition-protocol.md` §0/§3 | **DISCHARGED** — SOCO-10 landed its edit; the sentence is quiet | NWPP-10 issues. The desk states what the lane will find (*"**Seven** ISOs are registered… An eighth region is chartered but NOT registered: `SOCO`"*), and the charter's own "read it at your own base sha" duty is **unchanged** — SOCO-13/20/21 can still move it |
| `fetch_eia930_hourly.BA_TIMEZONE` (not previously registered) | **QUIET** — SOCO-11's key has landed; no concurrent writer | NWPP-11 appends its 17 keys after SOCO's. Registered as **C-5** below so the next refresh does not re-derive it |
| **C-1** `capacity_market.py` / `constants.py` / `interchange/spec.py` | not binding at this sitting | W1 touches none of them. Re-check at W2 issuance |

**A routed question ANSWERED by the desk rather than bounced back to a live lane.** NWPP-13's charter
carried a conditional — *"`data/raw/caiso-weim/` sits under a CAISO-token name; confirm with the desk
that it will not be swept into the caiso profile, and if it would, name it `data/raw/nwpp-weim/`."*
The desk **measured it** at this pin by running `configs/data-profiles.yaml`'s own substring rule:

```
caiso-weim     -> CAISO      (contains the CAISO token "caiso")
nwpp-weim      -> shared
nwpp-planning  -> shared
nwpp-hydro     -> shared
```

So the conditional **fires**. The plan is corrected in this refresh at all four places it appeared
(§5 row, §6 row 4, the charter's FILES-YOU-OWN line, and the NOTE — which now carries the measured
answer instead of the question), and the **fixed** text is what was issued (handoff §4). The second
half matters as much as the first: `nwpp-weim` resolves to `shared` today, which is right for W1, and
**moves into the `nwpp` profile automatically** when NWPP-20 registers the `nwpp` token — no rename
later.

**Desk repairs to the plan — found by reading the sibling desk's r#2, verified against this plan.**

- **G13 REWRITTEN.** As chartered it read *"`.gitignore` the bundle family — never `rm`"*. Read alone
  by a W4 charter author that **pre-orders the miso-255 incident**, because rule 34
  `[R-SHARD-PROMOTABLE]` (a) — corrected 2026-09-12, *after* this program was chartered — requires the
  SHARD to push its bundle and states that *"a shard prompt that tells its shard to gitignore or omit
  the bundle is a defect in the prompt."* G13 now states the seam: `.gitignore` is the **parent's**
  tree, the shard appends a **negation** for its own out-dir and uses a **plain `git add`, never
  `git add -f`**, the bundle must carry `dispatch/<year>_P1.parquet`, and nothing is `rm`'d before the
  owner rules. *(§8.0 collision rule 8 already carried rule 34's push duty — this plan was chartered a
  day after SOCO's and picked that up — so the defect was confined to the gate row. It is still a
  defect: a lane reads its gate.)*
- **G23 NEW (rule 33 `[R-SHARD-ARCHIVE]`) and G24 NEW (rule 35 `[R-PROMOTE]`).** Neither rule had a
  gate in this plan. G24 is not hypothetical housekeeping: `audit_keepers.py` **E13 is already failing
  at this pin for MISO (×4) and SPP (×1)** — superseded runs left registered behind a promotion. The
  gate exists so NWPP never joins that list.

**R-c UPDATED — the divergence did NOT happen at the ruling layer, and has MOVED to the
implementation layer.** This is the item the handoff orders surfaced at every sitting that touches
scoring, so it is reported as measured rather than as the standing worry:

- The SOCO desk's **card S2 was ruled at its r#2 — BOTH limbs, in substantially the same terms as this
  desk's N2**: build the index behind a pre-registered STOP gate, **and** rule the fallback now, so a
  run with no usable price reads *a determination naming its own basis*, never a bare `CALIBRATED`,
  with the price gap at full magnitude, and G17 (neighbouring-hub substitution) untouched. Two desks
  asked the same question separately and **got the same answer**. The feared divergence did not occur.
- **What is now live is the SCORER, not the ruling.** The SOCO desk measured that
  `scripts/calibration_verdict.py` **carries no branch that can express that determination class**, so
  its W4 cannot score until someone builds one; it raised **card S11** and recommends chartering
  **SOCO-22 `[FABLE]`** narrowly (an added branch no existing ISO can reach; byte-identity over all
  seven keepers' verdicts as the exit). **NWPP's N2 limb (b) has the identical dependency**, and
  NWPP-40 is blocked on it exactly as SOCO-40 is.
- **The desk did not card it and will not.** One branch serves both programs; two desks chartering it
  produces two branches, which is the *original* R-c failure wearing different clothes. Reported to
  the owner, routed, and left with the desk that raised it first. **This desk's ask is only that the
  owner, when ruling S11, note that its scope covers NWPP** — not that NWPP be given its own lane.

**Issued this sitting — W1, all four lanes**, verbatim from plan §8 W1 with §8.0 pasted in and
`origin/main` pinned at this refresh's sha. NWPP-10/11/12 `[OPUS]`, NWPP-13 `[FABLE]`, all
`DATA PROFILE: shared`, all file-disjoint. NWPP-13 was unblocked by ruling N2 and its charter's own
first line (*"ONLY START AFTER the owner has ruled card N2"*) is satisfied; the ruling is quoted into
the issued prompt.

**Gates run at `c93b0d27` — 7 attempted, every exit recorded, none carried forward green.** No NWPP
object exists in any of them, so every failure below is **another region's**, disclosed and routed
(handoff §0.5), never fixed by this desk (rule 25 `[R-ISO-SCOPE]`).

| Gate | Exit | What it says |
|---|---|---|
| `audit_keepers.py --check` | **FAIL (1)** | 6 failures / 4 warnings, **all non-NWPP**: E13 rule-35 promotion debris — MISO ×4 (`miso-250-ep-gas` registered-not-keeper; three `miso-251` runs stamped to it), SPP ×1 (`spp-38-vintage-cache`); plus S1 status files stale for ERCOT/PJM/CAISO/NYISO/NEISO/SPP (`build_status.py`). **Routed to the MISO and SPP lanes** |
| `check_registry_payload_parity.py` | **FAIL (1)** | 3 unregistered bundle dirs — `caiso279_ablate_dswcouple_span`, `nyiso230_arm_y2022`, `nyiso231_arm_y2022`. **Routed to the CAISO and NYISO lanes** |
| `check_gate_a_provenance.py` | **FAIL (1)** | MISO and NYISO `gate.a_keeper_marker` cite superseded keepers. **Routed** |
| `check_mechanism_matrix.py` | **PASS (0)**, 3 warnings | anchor drift on `entry_lookahead_reprice` / `startup_co2_reporting`; SPP §5.x prose header does not name its designated keeper. **The diff gate did NOT run** (no `--base`) — recorded as such, because a 0 from this mode is not a registration verdict |
| `check_bench_freshness.py` | **PASS (0)** | 34 parts, 0 stale, 31 with engine drift (warnings) |
| `check_golden_manifest.py` | **PASS (0)** | 57 manifests, 100 entries; OK |
| `scripts/ci_refactor_guards.py` | **UNREAD + 1 real row** | Most rows are `ModuleNotFoundError: No module named 'numpy'` — **numpy is absent from this container**, so those rows are recorded **UNREAD** per handoff §0.7, not as repo defects. The one substantive row is real and non-NWPP: `scripts/run_calibration_full.py` references a missing `scripts/test_recorded_config_gas_anchor_mirror.py` |

**Next act:** sitting #3 — grade W1 **by content** as each lane's FINDING lands, then serve cards
**N4–N8 and N10** with W1's evidence. Re-check C-2 before issuing NWPP-21. NWPP-36 is chartered at the
sitting that follows NWPP-32.

---

### r#1 — 2026-09-13 — SITTING #1: cards N1, N2, N3 RULED (main `2c2fc065`)

**What happened.** The three sitting-#1 cards were served as clickable decision cards. **N1 and N2 were
ruled as the desk recommended. N3 was ruled AGAINST the desk's recommendation**, and that one ruling
restructures the program.

| Card | Ruling | vs. desk |
|---|---|---|
| **N1** | **All 17 BAs**, key `NWPP`; NEVP in, Canada out, AVRN/GRID supply-side only | as recommended |
| **N2** | **Both (a) and (b)** — charter NWPP-13's STOP-gated WEIM build **and** rule now that a failed gate yields a determination naming its own basis, never a bare `CALIBRATED` | as recommended |
| **N3** | **BUILD CASCADE COUPLING FIRST** — hydraulic coupling of the Columbia mainstem is built **before** any first keeper | **AGAINST**: the desk recommended proceeding on the monthly-budget machinery with the gap declared |

**What N3 changes, implemented in the plan rather than noted.** The desk's recommendation would have
pre-declared cascade coupling as W5 lever NWPP-54 and solved a first keeper without it. The owner ruled
that the first NWPP number must mean more than a test of monthly hydro budgets. So:

- A new wave **W3b** is inserted between derivation and the first solve, and **W4 does not start without
  it** (plan §4).
- A new lane **NWPP-36** `[FABLE]` is added to the lane table (plan §5) and its W3 delta written (§8).
- **Lever NWPP-54 is RETIRED from the W5 queue**, its content promoted into NWPP-36. The queue is now
  NWPP-55/56/57/58/59.
- **Gate G8 is AMENDED** (plan §7). This is the part that mattered and the desk checked it rather than
  assuming: G8 forbade *any* new `ScenarioConfig` field through W4, and a mechanism is a field — so the
  ruling and the gate were in direct tension. **The tension resolves by construction, not by exception.**
  The repo carries `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, and a field
  registered default-OFF in both, in the same commit, is dropped from the hash at its default so every
  pre-existing cached run — every ISO's keepers included — keeps its key. **There is a worked hydro
  precedent to copy rather than invent:** `hydro_budget_period_by_instrument` (lane nyiso-220) is the
  **first entry** in that tuple and was added on exactly this basis. NWPP-20 remains forbidden any field
  at all; the exception is NWPP-36's single field and nothing else.

**What did NOT change.** N3 is a sequencing and scope ruling, not a licence: rule 1 `[R-STRUCT]` still
forbids judging the coupling by whether it improves a residual — and since no NWPP run exists, there is
no residual to judge it against, which is the cleanest possible position for a structural build. Rule 2
`[R-VECTOR]` binds its LP rows. Rule 28 `[R-MECH-MATRIX]` (c) requires its matrix base row plus one `·`
cell per foreign shard in the same PR.

**The joint-sitting option on N2 was offered and NOT taken.** The desk presented "rule N2 and SOCO's S2
together" as an explicit option; the owner ruled N2 on its own. **R-c therefore stays OPEN and must be
surfaced at every sitting that touches scoring** — the SOCO desk's ledger still routes that the rubric
question be ruled once for both, and it now has one half-answer. That is a live divergence risk, not a
closed item.

**Gates run:** none — this refresh touches only the three program documents plus the two index rows, so
every gate's input is unchanged. Recorded UNREAD rather than carried forward green.

**Next act:** issue W1 — NWPP-10, NWPP-11, NWPP-12 (all `[OPUS]`, `DATA PROFILE: shared`, parallel,
file-disjoint) **and NWPP-13** `[FABLE]`, which N2's ruling unblocks. Then sitting #2 for N4–N8 and N10
once W1's evidence lands. NWPP-36 is chartered at the sitting that follows NWPP-32.

---

### r#0 — 2026-09-13 — CHARTER (main `2c2fc065`)

**What happened.** The owner directed a chartering session for adding the Northwest Power Pool /
Western Power Pool footprint as a registered region, using the SPP addition workstream as the process
reference and the SOCO charter (2026-09-12) as the non-market precedent. The session measured its
facts rather than restating the ones it was handed, and four of those measurements changed the
program's shape (see **Corrections** below).

**Committed at charter:** `docs/multi-iso/nwpp-addition-plan-2026-09.md`,
`docs/handoffs/nwpp-desk-handoff-2026-09-13.md`, this ledger, plus one row in
`docs/multi-iso/README.md` and one `CHANGELOG.md` entry. Nothing else. No code, no data, no registry
touched.

**Measured in the charter session** (plan §2 carries all of it with its provenance; do not
re-derive):

| Fact | Value |
|---|---|
| Hermiston | EIA plant **54761**, Umatilla County OR, 621.2 MW / 4 CC gens, op. 1996, BA **PACW**, NERC WECC. The adjacent Hermiston Power Partnership is plant **55328**, 689.4 MW, BA **GRID** |
| Fleet, 17 candidate BAs, EIA-860 operable | **940 plants** (1,082 plant-table rows) · **1,932 generators** · **98,738.1 MW** |
| NERC | WECC 98,238.1 / 1,930 gens · **TRE 500.0 / 2 gens — a source defect, NWPP-10 adjudicates** |
| By technology | hydro **35,799.5 (36.3 %)** · CC 15,609.3 · wind 14,460.3 · solar 10,049.9 · coal 8,910.2 · CT 4,565.5 · batteries 2,522.0 · gas ST 2,163.0 · **nuclear 1,200.0** · geothermal 972.6 · **pumped storage 314.0** |
| Hydro concentration | 288 plants; **8 plants ≥ 1 GW = 17,821.8 MW (49.8 % of all hydro)**; 141 plants < 10 MW = 504.1 MW (1.4 %) |
| Ownership | **Electric Utility 68,860.0 MW (69.7 %)** · IPP Non-CHP 26,962.3 · IPP CHP 1,568.8 |
| Demand (EIA-930, committed) | **283.97 / 291.56 / 294.86 TWh** (2023/24/25) |
| Coincident peak, defect-screened | **49,290 / 52,564 / 50,953 MW**; load factor 0.658 / 0.631 / 0.657 |
| 2024 load share | BPAT 20.26 · PACE 18.10 · NEVP 14.11 · PSEI 8.53 · PGE 7.79 · PACW 7.30 · IPCO 6.43 · AVA 4.44 · NWMT 4.18 · SCL 3.23 · GCPD 2.29 · TPWR 1.56 · DOPD 0.82 · CHPD 0.68 · WAUW 0.28 · **AVRN 0.00 · GRID 0.00** |
| Timezones | EIA-930 assigns **one zone per BA**: Mountain = NWMT, PACE, WAUW; Pacific = the other 14 (incl. IPCO) |
| CAMPD CEMS | present MT/NV/WY/CA; **ABSENT ID/OR/UT/WA** (and CO) |
| Probes at this pin | EPA CAMPD bulk **206** anon · CAISO OASIS `ATL_APNODE` **200** and `PRC_RTPD_LMP` **200 with real 15-min LMPs** · EIA ICE workbooks **200** · BPA `baltwg.txt` **206** · westernpowerpool.org **200** · wecc.org **200** · PUDL FERC-714 **200** · `ferc.gov` **403** · no `EIA_API_KEY` |

**Corrections and extensions to the facts this desk was handed** — recorded here because a desk that
silently absorbs a wrong premise mis-charters every lane downstream:

| # | Handed | Measured | Consequence |
|---|---|---|---|
| 1 | *"EIA-930 hourly parquets on disk: … NOT ONE NWPP BA. Every one must be fetched."* | The **derived** per-BA files are indeed absent, but `data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet` is **committed 2019-01 → 2026-06 and carries all 17 BAs** with Demand, Net Generation, Total Interchange, Sum(Valid DIBAs), Adjusted demand and **both** time columns | NWPP-11's load spine is a **DERIVE, not a fetch**, and needs no `EIA_API_KEY`. Manifest row 2 rewritten |
| 2 | *"940 plants / 98,738.1 MW"* | MW confirmed **exactly**; 940 is the count of plants **with ≥ 1 operable generator** — 1,082 plant-table rows carry a footprint BA | stated precisely in plan §2.1 so NWPP-10's census reconciles |
| 3 | (not handed) | **AVRN and GRID carry NULL demand in all 26,295 hours** — generation-only BAs holding 3,538.1 MW | they are supply-side members and **not zone candidates**; card N5's grouping must place their generation |
| 4 | *"the two-timezone problem"* (SOCO gate G19) | **Largely closed by measurement**: 14 Pacific / 3 Mountain, one zone per BA, both time columns committed | card N6 is reduced to a canonical-convention choice, not a data problem |

**Additional measured findings with no handed counterpart:** 30 defective demand hours of 394,424
(AVA 810,948 MW at 2025-10-12 10:00 UTC; −58,286 at 2024-01-05 16:00; NWMT 11, NEVP 6, PACE 1,
SCL 2) which unscreened put the 2025 coincident peak at 835,464 MW — and the `Demand (MW) (Adjusted)`
column already carries the screened series. The **data-profile token trap is the worst yet measured**:
`ava` steals ten files across five ISOs, `grid` steals `fleet-egrid`, `pge` steals CAISO's
`reference/pge-helms-ps-plant-2008`, `wpp` steals SPP's `SWPP_*`. And
`data/raw/eia-860/eia860_generators.parquet` is a **curated seven-ISO file with zero NWPP rows**.

**The program's defining problem, stated at charter so it is never discovered late:** the Northwest
Power Pool publishes **no LMP** and had **no day-ahead market** in 2023–2025. Unlike SOCO, two
measured public prices **do** cover it — CAISO **WEIM** 15-minute LMPs (212 `EIMT` apnodes across
this footprint's BAs; a live pull returned $63.9213/MWh) and the **Mid-C** traded index (244 trade
dates, 4,748,000 MWh in 2023). Neither is straightforwardly the benchmark: WEIM clears **imbalance
only** and its share of footprint volume is `pending NWPP-13`; Mid-C is **daily and peak-only**, so
it can anchor a level and score nothing. Card **N2** is the only route, and it is due at **sitting
#1**.

**Gates run at charter:** none — the charter commit touches no code, no data and no registry, so
every gate's input is unchanged. Recorded UNREAD rather than carried forward green.

**Next act:** sitting #1 — serve cards **N1** (the region and its footprint), **N2** (the price
benchmark / rubric class) and **N3** (hydro representation) to the owner via AskUserQuestion, then
issue W1 (NWPP-10/11/12; NWPP-13 only if N2 rules for option (a)).

---

## 1. Scoreboard

| Lane | Model | Wave | Status | Branch | FINDING |
|---|---|---|---|---|---|
| NWPP-10 audit | OPUS | W1 | **LANDED r#3** (graded by content) | merged `53bea3e0`, `3b7fb463` | `FINDING-nwpp-10-2026-09-13.md` |
| NWPP-11 CEMS + 930 derive + interchange + hydro | OPUS | W1 | **LANDED r#3, 5/5** | merged `73478c98`…`feebfd2a` | `FINDING-nwpp-11-2026-09-13.md` |
| NWPP-12 WECC paths / WRAP / IRPs / fuel | OPUS | W1 | **LANDED r#4** — **G12 PASSES**; WRAP out of window; NW↔OR has no path rating | merged `5b0a19fb`…`111c68ac` | `FINDING-nwpp-12-2026-09-13.md` |
| NWPP-13 WEIM price index | FABLE | W1 | **LANDED r#3 — verdict NO** (D3 Mid-C reconciliation −22.6…−37.5 % vs a ±10 % bar; D2 volume share 5.5–6.2 % PASSED). Nothing landed to `_validation-source` | merged `715fff9d`, `97121c22`, `976e7724` | `FINDING-nwpp-13-2026-09-13.md` |
| NWPP-20 registration | FABLE | W2 | **LANDED r#5 — NWPP IS THE EIGHTH REGISTERED REGION.** G8 proof: zero moved rows, 19 keeper configs byte-identical (lane-measured; UNREAD by the desk, no pydantic here). **R-e closed better than recommended** — the scalar `ISO_TO_BA_CODE` now holds only 1:1 regions, so NWPP's absence fails LOUD | merged `f2191f5d` | `FINDING-nwpp-20-2026-09-14.md` |
| NWPP-21 matrix shard | OPUS | W2 | **LANDED r#4** — the **ninth** shard, `ev = "W"`; re-counted after another shard landed mid-flight, as G2 designed | merged `8e88c3dd`…`622f69cf` | `FINDING-nwpp-21-2026-09-13.md` |
| **NWPP-22 the scorer branch** | **FABLE** | **W1c** | **LANDED r#4 — class live (v3.8), own edit WITHDRAWN as a duplicate** (rule 19). 7/7 keepers byte-identical; NWPP reaches the class, verified by the desk. Done-row 7 **MET** | merged `86b5dc92`…`088094be` | `FINDING-nwpp-22-2026-09-13.md` |
| NWPP-30 outages + tranches | OPUS | W3 | **LANDED r#6** — windows + tranches, coverage arithmetic stated | merged `66712d2b`,`442f2ce4`,`9bc3aa95` | `FINDING-nwpp-30-2026-09-14.md` |
| NWPP-31 benchmarks | OPUS | W3 | **LANDED r#6 — G9 PASSES EXACTLY**: 7 regions + 36 CSVs byte-identical; price side verified skipped **by execution** | merged `e15c02b0` | `FINDING-nwpp-31-2026-09-14.md` |
| NWPP-33 zonal shares / VRE / gas basis | OPUS | W3 | **LANDED r#6** | merged `e469a889` | `FINDING-nwpp-33-2026-09-14.md` |
| NWPP-34 seam derive | OPUS | W3 | **LANDED r#6** — BPAT trap adjudicated; **R-a now carries a measured magnitude** | merged `e2e3c123` | `FINDING-nwpp-34-2026-09-14.md` |
| NWPP-35 site + docs | OPUS | W3 | **LANDED r#6** — measured the count as **NINE** independently and led with it; `calibration-log/nwpp.md` created | merged `ab47320c` | `FINDING-nwpp-35-2026-09-14.md` |
| **NWPP-32 hydro budget** | **FABLE** | W3 | **LANDED r#6 — reconciles at 0.000 MWh, every plant, every year**; P1–P4 all held; 263 absent plants read `NO_923_SERIES` and stay absent. **Corrected the desk's own chain list** (Boundary is Pend Oreille, not mainstem) | merged `06a80274` | `FINDING-nwpp-32-2026-09-14.md` |
| **NWPP-36 cascade coupling** | **FABLE** | **W3b** | **ISSUED r#6** — charter composed entirely from NWPP-32 §5–§6. 11 mainstem plants / 20,098.8 MW / 56.14 % of hydro; τ and pondage **must be measured**; ONE default-off field; nine-region G8 proof | pending | — |
| **NWPP-37 envelope screen seam** | **FABLE** | **W3c** | **ISSUED r#7** — the R-f fix, located to `envelopes.py:109/:167` bypassing `_screen_fuel_spike_columns`. Nine-region byte-identity exit | pending | — |
| **NWPP-38 PNCA discontinuity** | OPUS | **W3c** | **ISSUED r#7** — a MEASUREMENT, not a fix: R-j has no code fix and inventing one is refused | pending | — |
| NWPP-40 first solve | FABLE | W4 | **BLOCKED on NWPP-36 ALONE** — all of W3 has landed. Inherits **R-f** (930 hydro unsafe 2024–25) and **R-j** (PNCA terminated in-window) as PRECOMMIT duties; card **N10** is served at its sitting | — | — |
| NWPP-55…59 levers | — | W5 | pre-declared, not issuable (**NWPP-54 RETIRED into NWPP-36**, ruling N3) | — | — |
| W6 forecast entry | — | W6 | ROUTED to the capx director (card N9) | — | — |

## 2. Owner rulings — verbatim, numbered

| # | Card | Ruling | Date |
|---|---|---|---|
| O-1 | charter | Charter the NWPP addition using the SPP workstream as reference and the SOCO charter as the non-market precedent | 2026-09-13 |
| N1 | the region, key and footprint | **ALL 17 BAs** — key `NWPP`; NEVP in; Canada out; AVRN/GRID supply-side members, not zone candidates. *As the desk recommended.* | 2026-09-13 |
| N2 | price benchmark / rubric class | **BOTH (a) AND (b)** — charter NWPP-13's STOP-gated WEIM build, AND rule now that a failed gate yields a determination naming its own basis, never a bare `CALIBRATED`, with the gap at full magnitude. Neighbouring-hub substitution stays refused (G17). *As the desk recommended. The joint-sitting-with-SOCO option was offered and not taken — R-c stays open.* | 2026-09-13 |
| N3 | hydro representation | **BUILD CASCADE COUPLING FIRST** — hydraulic coupling of the Columbia mainstem is built before any first keeper. ***AGAINST the desk's recommendation***, which was to proceed on monthly budgets with the gap declared. Effects: new wave W3b, new lane NWPP-36, lever NWPP-54 retired, gate G8 amended. | 2026-09-13 |
| N11 | the scorer branch | **SEND IT NOW** — charter and issue NWPP-22 immediately rather than defer or route it. Plan §1's rubric prohibition is carved for this one lane only; gate G25 holds it to a byte-identity exit over every pre-existing keeper. *(Served after the owner directed: "Ignore SOCO desk you focus on nwpp.")* | 2026-09-13 |
| N5 | topology | **FIVE ZONES, as scoped** — NW/EAST/INLAND/OR/SNV. TTC tiers ruled with them: Path 35 and Path 16 Tier-1; Paths 8/6/14 and Path 20 Tier-2; **NW↔OR Tier-3 documented absence**. Paths 4/5/71/86/87/88 are east–west cuts, never BA interfaces | 2026-09-14 |
| N7 | adequacy | **ONE SCALAR NOW, DECLARED** — tested against the footprint coincident peak, with the 8-winter/6-summer/1-flipping mismatch on the determination basis at full magnitude. Per-zone seasonal PRM → lever **NWPP-57**. WRAP binds Winter 2027–28, **out of window** | 2026-09-14 |
| N4 | CAISO seam | **SERVED MEASURED INTERCHANGE, priced links default-OFF** — `_SCALAR_INTERCHANGE_ISOS += NWPP`. **BPAT's balance identity fails structurally** (−3,206 MW mean, 81.5 % of hours): the derive must handle it. R-a stays routed | 2026-09-14 |
| N8 | fleet representation | **LEGACY HEAT-RATE BINS** (`use_campd_bins=False`) for the first keeper; CAMPD per-plant → W5 lever. Supersedes the §3 recorded `per_plant=True` default | 2026-09-14 |
| N6 | timezones | **RESOLVED BY MEASUREMENT, not ruled** — 14 Pacific / 3 Mountain, IPCO files Pacific, UTC canonical. Gate G19 closed | 2026-09-14 |
| N10 | first-solve screen | **DEFERRED** to the sitting that opens W4 — it governs a solve that cannot start until W3b lands | — |
| N9 | W6 routing | **PENDING** — due when a keeper exists | — |

## 3. Routed — open, not this desk's to fix

| # | Item | Owner | Why it stays visible |
|---|---|---|---|
| R-a | **The CAISO double-count.** CAISO's `WECC_import` zone is fed by firm tranche `PNW_hydro_base` (`interchange/caiso.py:443`) — this footprint, by name, as a Tier-3 contract-cost proxy. Registering NWPP puts the same energy on both sides of a seam, represented two ways | the CAISO lane (rule 25 `[R-ISO-SCOPE]`) | Card N4 governs NWPP's side only; the exposure does not disappear by being unmentioned |
| R-b | The rubric cannot express a determination for a region whose only price is an imbalance price covering an unmeasured share of volume | the owner (card N2) | A keeper solved before it is ruled cannot be scored |
| R-c | **~~SOCO divergence~~ — CLOSED AS A ROUTED ITEM at r#3 and replaced by lane NWPP-22.** Owner directive: *"Ignore SOCO desk you focus on nwpp."* The scorer branch that card N2 limb (b) requires is **this program's own work**, not a sibling desk's to supply, and card **N11** ruled *send it now*. What made it urgent is measured: NWPP-13 read **NO**, so NWPP has no admissible price series and NWPP-40 cannot be scored without the branch | **NWPP-22 `[FABLE]`**, issued r#3 | Tracked as a LANE, not a routed item. The only residual cross-program fact — that a sibling program has the same unmet need — is **not this desk's to manage** and is recorded here once, for the record, and never acted on |
| R-d | 500.0 MW filed under BA `DOPD` with state `TX` / NERC `TRE` | NWPP-10 adjudicates; any upstream EIA correction is outside this program | A silent mis-key would put 500 MW of the wrong interconnection in the fleet |
| R-e | `data/fleet/models.py:221` inverts `BA_CODE_TO_ISO` with a comprehension that **silently keeps only the last BA per ISO**. Every existing entry is 1:1; NWPP's is **17:1** | NWPP-20 audits it | The single most likely silent bug in the registration |
| R-f | **The NWPP pool `NG: WAT` series carries the G20 defective hours** (AVA 810,113 MW at 2025-10-12 10:00 UTC + four more; NWMT 65,891 / 65,880 in 2024). NWPP-10's repair was **demand-side only**; `measured_monthly_hydro`, `measured_hydro_min_flow_level` and the envelope read the **unrepaired** column | **NWPP-37 `[FABLE]`, ISSUED r#7** — desk located the defect: `envelopes.py:109/:167` call `frames._eia_hourly_frame_filled` directly, and the screen is applied only at `actuals.py:351/:412/:488` | **`eia930_monthly` and the 930-derived hydro floors/envelopes are UNSAFE for NWPP 2024–25 until repaired.** NWPP-32's posture — `backfill_year=2024`, the 2025 repin **refused on rule-14 grounds** — stands. **NWPP-40's PRECOMMIT must state it** |
| R-g | **930-vs-923 population mismatch, −2.7 TWh and stable**: WAUW (−2.6/−2.8 TWh) and PACW (−0.7) file their EIA-923 hydro plants under other EIA-930 BAs; Priest Rapids sits in BPAT (860) and GCPD (930) | a `data/eia930` lane | Any level pin between the two series needs a reconciliation the loader does not have — so no lane may pin one casually |
| R-h | **Swift 2 (72 MW, PACW)** has no EIA-923 series in either complete year | an id/crosswalk lane | An id question, not a data gap; it must not be silently filled |
| R-i | `curate_hydro_plant_modes.py` registers CAISO only; an NWPP curation is a W4/W5 lever (`hydro_ror_split`) | NWPP W5 | NWPP-32 §5(d) is the evidence it would start from |
| R-j | **The PNCA TERMINATED 2024-09-15**, no successor text found — the coordinating instrument for the whole Columbia system **changes inside the scored window** | **NWPP-38 `[OPUS]`, ISSUED r#7 — a MEASUREMENT lane.** There is **no code fix**: no successor instrument exists to model to, and inventing a post-PNCA regime is the fitted mechanism rule 1 forbids | A structural discontinuity between 2024 and 2025 that no mechanism currently expresses. **NWPP-40's PRECOMMIT states it**; it is not something to average over |

## 4. Collision register

| # | Surface | Other writer | Action |
|---|---|---|---|
| C-1 | `config/capacity_market.py`, `config/constants.py`, `model/interchange/spec.py` | capx D-lanes, the SCN desk, the per-ISO calibration lanes, **and the SOCO desk** | NWPP-20 rebases last and appends; the desk re-checks their ledgers' top entries at issuance |
| C-2 | `docs/codebase-site/data/mechanism-matrix.js` (base file), `scripts/lib/mech_matrix.py` | every ISO's lanes; **SOCO-21 is chartered to add a shard to the same file** | **LIVE at r#2, measured:** SOCO-21 was ISSUED at SOCO r#2 and has **not landed** (base `isos` still 7, no `SOCO.js`, zero `SOCO` in `mech_matrix.py`). **NWPP-21 is HELD.** Re-check at sitting #3; NWPP-21 re-counts `isos` at its own sha |
| C-3 | **The pin list itself** — `_ISO_BUILDERS`, `SURFACE_ISOS`, `_MULTI_YEAR_ISOS`, `ISO_ORDER`, `data-profiles.yaml`, `calibration-solve.yml` | **the SOCO desk's NWPP-20 analogue, SOCO-20** | Whichever lands second re-counts (plan §0). Neither plan's §2.3 may be executed from its own number |
| C-4 | `docs/multi-iso/00-iso-addition-protocol.md` §0/§3 (the registered-region count sentence) | SOCO-10 is chartered to edit the same sentence | **DISCHARGED at r#2:** SOCO-10 **landed**; the sentence is quiet and reads *"**Seven** ISOs are registered… An eighth region is chartered but NOT registered: `SOCO`"*. NWPP-10 issued. Its duty to re-read at its OWN base sha is **unchanged** — SOCO-13/20/21 can still move it |
| C-5 | `scripts/data/fetch_eia930_hourly.py` `BA_TIMEZONE` (additive keys) | SOCO-11 (**landed**), NWPP-11 (issued) | **QUIET at r#2** — SOCO's `"SOCO": "America/Chicago"` key is committed with its measured provenance comment; no concurrent writer. NWPP-11 appends its 17 keys after it. Registered so a later refresh does not re-derive this |

## 5. Issuance record

| Sitting | Date | Lanes issued | Cards served |
|---|---|---|---|
| r#0 | 2026-09-13 | none (charter commit) | N1, N2, N3 served to the owner at the close of the charter session |
| r#1 | 2026-09-13 | none yet — W1 (NWPP-10/11/12/13) is the next act | N1, N2, N3 **RULED**; N3 against the desk's recommendation |
| r#2 | 2026-09-13 | **W1 ISSUED — NWPP-10, NWPP-11, NWPP-12 `[OPUS]` and NWPP-13 `[FABLE]`**, verbatim from plan §8 W1, §8.0 pasted in, `origin/main` pinned. NWPP-21 **HELD** (C-2 live) | none — N4–N8/N10 await W1 evidence. **R-c re-measured**: SOCO's S2 converged with N2; the live risk moved to the scorer branch (SOCO card S11), routed not carded |
| r#3 | 2026-09-13 | **NWPP-22 `[FABLE]` ISSUED** (charter written into plan §8 at this refresh, then issued) and **NWPP-21 `[OPUS]` ISSUED** (un-held) | **N11 RULED — "send it now"**. W1 graded by content: NWPP-10/11 LANDED, NWPP-13 LANDED with verdict **NO**, NWPP-12 outstanding |
| r#4 | 2026-09-14 | **NWPP-20 `[FABLE]` ISSUED** — the pin flip, charter corrected at this refresh for the R-e scope finding and all six card outcomes | **N4, N5, N7, N8 RULED** (all as recommended); **N6 resolved by measurement**; N10 deferred to the W4 sitting |
| r#5 | 2026-09-14 | **W3 ISSUED — all six lanes** (NWPP-30/31/32/33/34/35). Their charters did not exist: §8 carried only deltas, so the desk composed them against SPP's worked W3 and committed them at plan §8 W3 before issuing | none due — N10 at the W4 sitting, N9 on a keeper |
| r#6 | 2026-09-16 | **NWPP-36 `[FABLE]` ISSUED** — W3b, composed entirely from NWPP-32 §5–§6 and committed at plan §8 W3b before issuing | none due — **N10 is served at the W4 sitting**, which NWPP-36 now gates; N9 on a keeper |
| r#7 | 2026-09-16 | **NWPP-37 `[FABLE]` and NWPP-38 `[OPUS]` ISSUED** (wave W3c), on the owner's request for fixes to R-f and R-j | none — the owner's request was answered with a located fix (R-f) and a stated refusal to invent one (R-j) |

## 6. Errors against interest

*(The desk records its own mistakes here, in its own words, so the next refresh does not repeat
them.)*

- **E-1 (r#0, caught in-session).** The desk's first census script joined the plant and generator
  frames without disambiguating the `State` column present in both, and the groupby raised
  `KeyError: 'State'`. Nothing downstream consumed the bad frame, but the lesson stands for every
  lane: the EIA-860 plant and generator parquets share several column names, and a merge that does
  not name its suffixes will silently take the wrong one where it does not raise. NWPP-10's census
  should state which frame each column came from.
- **E-2 (r#0, method note against interest).** The desk accepted the handed probe results as a
  starting point but re-ran every one at its own pin rather than citing 2026-09-12 results as
  current. Two differed in form (EPA and BPA answered 206 to a range request rather than 200), which
  changes nothing — but had a host gone dark overnight, a carried-forward green would have sent a
  lane at a dead route. No lane should cite a probe it did not run.
- **E-3 (r#4, against the desk's own r#2 position).** At r#2 the desk wrote that one scorer branch
  serves both this program and a sibling, and that two desks chartering it would produce two. The owner
  then directed it to stop coordinating and send it now; both were chartered; the other landed first;
  **NWPP-22 built an implementation that was then withdrawn.** The desk is not re-arguing the
  directive — NWPP got the class, sooner, and a deferred NWPP-22 would have left this program waiting
  on another desk's schedule, which is what the directive was preventing. The cost is stated anyway
  because a desk that only records vindicated calls is not keeping a ledger: **one lane's scorer
  implementation was written and discarded.** Partly offset — the withdrawal produced a leg-by-leg
  cross-check of the surviving predicate, which is what let this desk verify NWPP's reachability
  rather than assume it.
- **E-4 (r#4, method note).** The desk carried `26,295 hours` for AVRN/GRID's null-demand window from
  charter through three refreshes. NWPP-10 measured **26,304** — the charter's 2023 hour count was a
  UTC-boundary artifact, not missing data. Nothing downstream turned on it, but it was restated three
  times without being re-derived, which is the failure mode gate G15 names applied to the desk's own
  numbers rather than a lane's.
- **E-5 (r#6, the desk's own charter was wrong and a lane caught it).** The r#5 NWPP-32 charter told
  the lane the Columbia chain contained *"eight plants ≥ 1 GW holding 17,821.8 MW"* and listed
  **Boundary** among them. Measured against the ORNL EHA FY2024 `Water` field, **seven are mainstem
  (16,662.1 MW) and Boundary (1,159.7 MW) is on the Pend Oreille**, reaching the Columbia only through
  Canada and coupled to nothing else in this footprint. The number came from the charter's own §2.1
  census — eight plants ≥ 1 GW — and the desk silently promoted "largest hydro plants" into "the
  chain", which is a different claim requiring different evidence. **Had NWPP-36 been chartered from
  the desk's list it would have built a coupling link that does not physically exist.** The lane's
  charter told it the chain was "a hydrological fact to be cited, not a list to be chosen", and that
  instruction is what caught the desk's own error — which is the argument for writing it that way.
