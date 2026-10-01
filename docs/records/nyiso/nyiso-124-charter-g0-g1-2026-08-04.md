# nyiso-124 — the downstate topology-split charter CLOSES AT G0 WITH CAUSE, and the C3a basis is re-attributed to a boundary the model ALREADY HAS

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only, rule 22) ·
**Keeper:** `2026-08-04-nyiso-120-c119-scope`, **UNCHANGED**.

**Zero solves. Zero years touched outside 2023–2025. No `ScenarioConfig` field,
constant, derive script or model artifact changed. No run produced, so none
registered (rule 15 registers runs; a no-LP session registering nothing is
correct, not an omission).**

**Charter worked:** `docs/handoffs/nyiso-downstate-topology-split-charter-2026-08.md`
(precommit, opened 2026-08-04 at nyiso-123 by owner ruling "charter both, paired").
**Gates in scope:** G0 (identifiability) and G1 (Object B diagnosed) — both no-LP,
both gating every solve (charter §5).
**Probe:** `scripts/probes/_nyiso124_charter_g0_g1.py` ·
**Record:** `results/calibration/_nyiso124_charter_g0_g1.json`.

**Verified at this session's HEAD (`afe19a56`), committed artifacts only, no solve:**
`scripts/calibration_verdict.py --run-id 2026-08-04-nyiso-120-c119-scope` returns
**NOT-YET** — `price_mean` **FAIL** (2023 +7.2 % PASS, 2024 −0.9 % PASS,
**2025 −10.1 % FAIL** against ±10 %), `price_tail` **CAVEAT** (ledgered, budget
**1 of 3, unspent**), the other seven **PASS**. `scripts/audit_keepers.py --iso NYISO`
**PASS, 0 failures / 0 warnings**. NYISO holds a `complete` (validation-tier)
marker, is **absent from `final`**, and the **holdout spend freeze is ACTIVE** and
outranks the marker — nothing out-of-training was solved, scored or read.

---

## §0 — the verdict in one table

| gate | verdict | consequence |
|---|---|---|
| **G0 — identifiability** | **FAIL** — 2 of the 5 required quantities have no public source with a forward analogue | **the charter closes with cause** (charter §6(1)) |
| **G0 — incidence** (measured, beyond what the gate asked) | the F\|G cutset carries a **NEGATIVE** basis in every year; the basis the charter is chasing sits at **E\|F (Central East)** | the split targets the **wrong boundary**; an independent second reason to close |
| **G1 — Object B diagnosed** | **diagnosed and attributed** — but to an **already-adjudicated, route-exhausted** object, not to a new buildable mechanism | the pair cannot be built either (charter §6(2)) |
| §7(1) 2023's 86.40 % identity | **ANSWERED** — the measured 2023 Central-East TTC override is 1,450–1,950 MW vs 2,525–3,175 later, so the model's link separated in **13.4 %** of 2023 hours vs 1.5 %/1.1 % | and it separated in the **wrong months** |
| §7(2) is Object B nyiso-110's object? | **YES, same object** (the trough half) — rule 19 `[R-ONE-MECH]` decides against two treatments | Object B gets **no** mechanism of its own |
| §7(3) does the split subsume LI? | **moot** — no split | — |
| **the successor question** — why is the model's Central-East link slack on a limit the real interface binds at? | **ANSWERED, no solve** (§6.1) — the external **seam** delivers the right NET and the wrong DISTRIBUTION: the three downstate border links sit at their bound in **98–100 %** of all hours (3,800 MW flat vs a measured 1,772–2,040 MW median) while the upstate border link runs **net export** against a measured import | the surplus lands **east of the cutset**, so the east never draws on the west; enters the matrix as `seam_flow_envelopes` NYISO **`.` → `U`**, **no lever armed** |

**The headline, and it is a re-attribution rather than a frontier:** the model's
C3a basis defect is **not** an unrepresentable sub-zonal object. It sits on the
**Central East (E\|F) interface, which the model already carries as a link, with
an already-measured, already-rule-14-grounded TTC**. In January 2025 the real
interface ran at ≥95 % of its posted limit in **26.9 %** of hours and NYISO's own
`CAPITL` − `WEST` basis was **+$46.55/MWh**; the model's
`Upstate_West → Capital_Hudson` link separated its zonal prices in **0.0 %** of
those hours, on a monthly TTC of 3,175 MW against the posted median of 3,205 MW.
**Same cutset, same limit, same hours — the real system binds and the model does
not.** That is a diagnosable defect in what crosses the link, not a
representation frontier — and **§6.1 diagnoses it, with no solve**: the model's
external seam over-delivers ~1.8–2.0 GW *east* of the cutset in ~100 % of hours
and drains ~1.0–1.7 GW from the west, so the east never needs the west.

---

## §1 — measurement bases, named up front (the nyiso-123 §1 discipline)

This session introduces a **fourth** basis and never blends it with the other
three. It is the **zone-letter basis**: NYISO's own posted 5-minute RT zonal LBMP
(MIS "Real-Time Zonal LBMP", 11 load zones with their loss and congestion
components), averaged to the hour on the published prevailing clock and re-keyed
onto the model's fixed non-leap 8760 calendar by local (month, day, hour) — never
positionally, which is nyiso-123's own correction for leap-2024.

Its ISO level is **not** the scorer's `rt_lw` bench (2023/2024/2025: this basis
33.65 / 39.60 / 69.11 against the bench's 32.30 / 38.20 / 66.53). **So no level
from this basis is ever quoted as C3a.** Only *differences* between zones, and
*shares*, are used — both of which are basis-independent in the sense that
matters here, because they are computed inside one basis.

The model side is the keeper's committed `hourly/system_<year>.parquet` P1
prices, unchanged.

## §2 — G0: the public-source census

The charter's G0 requires four quantities; the split forces a fifth
(nyiso-101 §3 leg 2). Each is tested against public, reproducible sources, and
against rule 13's forward-analogue test.

| # | quantity | public source | forward analogue | verdict |
|---|---|---|---|---|
| 1 | **F/G boundary definition** | NYISO load zones F (Capital) / G (Hudson Valley) are tariff objects with their own PTIDs in the MIS zonal LBMP posting; the cutset is the **UPNY-SENY** interface, defined in the 2025 SOM as *"the UPNY-SENY interface between zones A-F and G-I"* and listed among the RTC/RTD constrained interfaces (2025 SOM p. A-93) | static tariff zone definitions | **PASS** |
| 2 | **F/G transfer limit(s)** | **NONE FOUND** — see below | n/a | **FAIL** |
| 3 | **Zone-G share of the eastern external seam (`ext_G`)** | **NONE** — unchanged from nyiso-101 §3 leg 2 | n/a | **FAIL** |
| 4 | **zonal load allocation F vs G** | measured hourly `CAPITL` / `HUD VL` in the NYISO zonal load report, all three training years present | **yes** — the Gold Book publishes zonal (A–K) baseline load forecasts for 30 years, plus the Table I-14 zonal large-load pipeline | **PASS** |
| 5 | **fleet membership each side** | Gold Book Table III-2a carries the NYISO load-zone letter **per unit**; the per-county F/G split is already carried by `zone_assignment.NYISO_CAPITAL_HUDSON_COUNTIES` | **yes** — the same table each year, and the interconnection queue also carries the zone letter per project | **PASS** |

### §2.1 — quantity 2: NYISO publishes no F/G transfer limit anywhere we can find

Enumerated mechanically by the probe rather than asserted:

- **MIS P-32 interface flow/limit posting**, all three training years — **seven**
  internal interfaces: `CENTRAL EAST - VC`, `DYSINGER EAST`, `MOSES SOUTH`,
  `SPR/DUN-SOUTH`, `TOTAL EAST`, `UPNY CONED`, `WEST CENTRAL`. **No SENY row.**
- **MIS ATC/TTC day-ahead transfer-capability posting**, all **36** training
  months (fetched from the public archive; this is the feed
  `scripts/data/derive_nyiso_central_east_ttc.py` expects as `ATC_TTC.zip`) —
  **seven** internal interfaces: `CENT EAST`, `DYSINGER EAST`, `MOSES SOUTH`,
  `NYPP EAST`, `SPRAINBROOK/DUNWOODIE SOUTH`, `UPNY/CONED`, `WEST CENTRAL`.
  **No SENY row.**
- **Gold Book**, all four editions on disk (2023, 2024, 2025, 2026), full-text
  scan: `SENY` **0**, `UPNY` **0**, `Central East` **0**, `Total East` **0**,
  `transfer limit` **0** hits — the Gold Book carries **no interface
  transfer-limit table at all**, for any interface.

The only public appearance of UPNY-SENY carrying any substance is narrative, and
it cuts against the charter: the 2025 SOM records that the interface *"was once
studied in the deliverability highways test and caused SDUs to be identified, but
**NYISO ceased studying it** in the deliverability test after the creation of the
G-J locality in 2013."*

**This is the nyiso-97 pattern exactly.** There, the in-city AORR was
MyNYISO-walled *and* the public 2008-vintage Appendix B carried no derivable NYC
parameter. Here the boundary is nameable and its load and fleet are public, but
the one quantity that would make it a *constraint* is not published in any
operational or planning feed we can reach. A limit chosen to make congestion
appear is precisely what charter §3 forbids.

### §2.2 — quantity 3: `ext_G` is unchanged, and the split forces it

The 1,600 MW `import_node → Capital_Hudson` link lumps the PJM Ramapo 345 kV ties
(Zone G) with the ISO-NE New Scotland / Pleasant Valley corridor (Zones F/G).
`model/interchange/spec.py` records the F-vs-G split of that capability as *"a
modelling choice inside the topology"* — not a measured allocation. Aggregated,
the choice is invisible; **split, it must be made**, and there is no measured
quantity to recover it from. That is the leg on which nyiso-101 refused the G-J
locality, and nothing has changed it.

**G0 VERDICT: FAIL.** Under charter §6(1) the charter **closes with cause**.
This is a legitimate and pre-registered outcome, reported as plainly as a pass
would be.

## §3 — G0, beyond the gate: the split targets the wrong boundary

The gate did not require this, and it is reported because it is decisive
independently of §2.

NYISO's own posted zonal RT LBMP, decomposed into the three eastward steps —
annual mean $/MWh, with the market's own congestion component in brackets:

| step (interface) | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| **E\|F  Central East** (`CAPITL` − `WEST`) | **+10.17** (−8.67) | **+5.09** (−2.41) | **+11.69** (−6.62) |
| **F\|G  UPNY-SENY** (`HUD VL` − `CAPITL`) | **−2.65** (+2.98) | **−0.36** (+0.87) | **−1.48** (+2.07) |
| **G\|H  UPNY-ConEd** (`MILLWD` − `HUD VL`) | +0.84 (−0.72) | +1.20 (−1.07) | +1.30 (−1.10) |

And in the cold-snap months nyiso-123 §2.1 localized the winter object to:

| month | E\|F | F\|G |
|---|--:|--:|
| Feb 2023 | **+39.77** | **−12.19** |
| Dec 2024 | **+15.75** | **−2.21** |
| Jan 2025 | **+46.55** | **−8.91** |
| Feb 2025 | **+33.96** | **−15.41** |

**Zone G prices BELOW Zone F, and it prices furthest below in exactly the months
the charter targets.** A constraint from F into G would raise G relative to F —
the opposite sign to the market. The basis the charter set out to represent forms
at **E\|F**, one cutset upstream, on a link the model already has.

Stated fairly: the F\|G separation is *real* (|basis| p95 of $14.67 / $3.74 /
$17.58) and it is a genuine locational feature — Zone G sits next to the PJM
Ramapo and ISO-NE Pleasant Valley ties and gets relief Zone F does not. But it is
a **G-cheaper-than-F** object, not the downstate premium the charter chartered,
and representing it would need a *reverse* constraint with no published limit
either. That is a different object and it is not chartered.

## §4 — G0, beyond the gate: only one internal interface binds, and the model's copy of it does not

Share of hours at ≥95 % of the posted limit, measured from the committed P-32
postings (the same 0.95 bar nyiso-122 used, kept identical so the two
measurements are comparable):

| interface | 2023 ann / Jan / Feb / Dec | 2024 ann / Jan / Feb / Dec | 2025 ann / Jan / Feb / Dec |
|---|---|---|---|
| `CENTRAL EAST - VC` | **4.4 / 22.0 / 14.6 / 0.1 %** | **2.5 / 17.2 / 1.4 / 6.5 %** | **3.6 / 26.9 / 7.7 / 1.7 %** |
| `TOTAL EAST` | 0.0 / 0.0 / 0.0 / 0.0 % | 0.0 / 0.0 / 0.0 / 0.0 % | 0.0 / 0.0 / 0.0 / 0.0 % |
| `UPNY CONED` | 0.0 / 0.0 / 0.0 / 0.0 % | 0.0 / 0.0 / 0.0 / 0.0 % | 0.0 / 0.0 / 0.0 / 0.0 % |
| `SPR/DUN-SOUTH` | 0.0 / 0.0 / 0.0 / 0.0 % | 0.0 / 0.0 / 0.0 / 0.0 % | 0.0 / 0.0 / 0.0 / 0.0 % |
| `DYSINGER EAST`, `MOSES SOUTH`, `WEST CENTRAL` | 0.0 % everywhere | 0.0 % everywhere | 0.0 % everywhere |

`CENTRAL EAST - VC` is the **only** internal NYISO interface that binds at all,
and it binds in precisely the cold-snap months nyiso-123 dated the winter object
to. The 0.0 % rows for `UPNY CONED` and `SPR/DUN-SOUTH` reproduce nyiso-122's
refutation independently — that finding stands and is not re-opened.

Against the model's own link on that same cutset (prices are LP duals, so
identical zonal prices ⟺ the link is off its bound):

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| model `Upstate_West→Capital_Hudson`: share of hours with any price separation | **13.4 %** | **1.5 %** | **1.1 %** |
| model annual mean basis $/MWh | +0.40 | +0.22 | **+0.02** |
| measured East(F+G) − Upstate(A–E) basis $/MWh | +7.93 | +3.68 | +7.75 |
| **share of the measured basis the model reproduces** | **5.0 %** | **6.0 %** | **0.3 %** |

**And it is mis-phased even where it exists.** In 2023, the model's separation is
concentrated in **March (34.5 %), August (38.7 %) and September (26.7 %)** —
months in which the real interface bound in **5.2 %, 1.6 % and 1.1 %** of hours —
while in January, where the real interface bound in **22.0 %**, the model
separated in **6.3 %**. So §7(1)'s "2023 carried more zonal dispersion" is
answered *and* qualified: 2023's dispersion is a consequence of that year's
tighter measured TTC override (1,450–1,950 MW monthly, versus 2,525–3,175 in
2024–25), and it is **not the same dispersion the market ran**.

## §5 — G1: Object B, and a correction to this session's own first reading

**Reported against interest.** This session's first reading — from the CE-binding
partition alone — was that Object B is the *mirror image* of Object A: one object,
seen from the two sides of the interface, with rule 19 `[R-ONE-MECH]` forbidding
two treatments. In CE-binding hours the model's upstate over-pricing is
**+$18.60 / +$23.62 / +$17.87** against **+$6.76 / +$2.22 / +$0.59** in slack
hours, which looks conclusive. **It is not, and the probe's own quintile
decomposition falsifies it.** Bucketing every hour by the *measured* East−Upstate
basis:

| bucket | measured basis | model basis | model upstate − actual upstate | model upstate − actual east |
|---|--:|--:|--:|--:|
| **2023** Q1 | +0.40 | +0.35 | **+6.41** | +6.00 |
| Q2 | +1.09 | +0.21 | **+6.43** | +5.34 |
| Q3 | +1.68 | +0.26 | +5.23 | +3.54 |
| Q4 | +4.21 | +0.28 | +3.82 | −0.38 |
| Q5 | +32.26 | +0.88 | +14.47 | −17.78 |
| **2024** Q1 | −0.04 | +0.01 | **+4.72** | +4.77 |
| Q5 | +13.21 | +0.49 | −3.87 | −17.08 |
| **2025** Q1 | −0.90 | +0.00 | **+4.19** | +5.09 |
| Q2 | +1.44 | +0.03 | **+7.21** | +5.76 |
| Q5 | +31.08 | +0.01 | −15.54 | −46.62 |

The model over-prices upstate by **$4.2–$7.2/MWh in the quintiles where the
market's own basis is $0–2** — hours in which there is no congestion for a
missing constraint to explain. `corr(model upstate error, measured basis)` is
**+0.124 / −0.061 / −0.263**: essentially uncorrelated, and *negatively*
correlated in 2025. Load-weighted, CE-binding hours contribute only **13 % / 31 %
/ −344 %** of the annual upstate error on 382 / 220 / 317 hours; the
+$18-to-+$24 conditional reading was a **level artifact** — errors are larger in
absolute dollars when all prices are high — and is corrected here rather than
carried.

**So Objects A and B are TWO objects, and the owner's pairing instinct was
right.** What Object B *is*:

- it is an **off-peak / trough** object — model upstate error off-peak
  **+$8.37 / +$4.53 / +$5.05** against on-peak **+$6.72 / +$1.87 / −$0.70**;
- in those low-basis hours the model over-prices **the whole state**, not upstate
  specifically (model upstate − actual *east* in Q1: **+$6.00 / +$4.77 / +$5.09**);
- which makes it numerically the same object as nyiso-123 §2.2's ≤$100-band
  conditional over-credit (**+$4.79 / +$2.43 / +$4.25** per hour) and as
  nyiso-122's "trough over-pricing mask".

**§7(2) is therefore decided: Object B is the TROUGH HALF of nyiso-110's
price-distribution compression**, the same object whose lane is
**route-exhausted** — `diurnal_price_amplitude` NYISO = **G**, the in-LP
reserve-formation family closed at nyiso-110 (reserve offers unpublished, MIP
forbidden, the class-widening successor refuted by the same arithmetic). Rule 19
`[R-ONE-MECH]` forbids giving Object B a second mechanism of its own.

**G1 verdict, stated honestly in halves.** The *diagnosis* half **PASSES**:
Object B has a named cause with an identification source (the quintile /
correlation / peak-split decomposition above, on NYISO's own posted zonal LBMP and
the keeper's committed sidecars), and every candidate on the charter's list —
upstate offer-curve level, hydro, wind, upstate must-run/floor forcing, upstate
marginal-unit mix — is discriminated *against* by the fact that the over-pricing
applies to the whole state in trough hours rather than to upstate relative to the
east. The *mechanism* half **FAILS**: the cause resolves onto an already-adjudicated
object with no buildable route. Under charter §6(2) the pair cannot be built, so
**both of the charter's closure conditions are independently satisfied**.

## §6 — what this changes, and the named successor question

**Object A is re-attributed, and that is the most decision-relevant output here.**
It was carried as an unrepresentable sub-zonal object needing a topology change.
It is not. It sits on `Upstate_West → Capital_Hudson`, a link the model **already
has**, whose TTC is **already** the measured DAM posting under rule 14
`[R-ACCURATE]` (`NYISO_INTERFACE_TTC_BY_MONTH`), in the **same months** and at
**the same limit** the real interface binds at. January 2025: model TTC 3,175 MW
vs posted median 3,205 MW; real interface ≥95 % in **26.9 %** of hours; model link
separating prices in **0.0 %**.

### §6.1 — CORRECTION, and the question is ANSWERED: the seam, not the interface

**This section's first draft said the successor question was unmeasurable from
committed artifacts because `system_<year>.parquet` carries no link flow.** That
is true of the keeper bundle and **wrong as a statement about the repo**, and the
error is corrected here rather than carried. `run_calibration_full._network_frame`
has **always** written `hourly/network_<year>.parquet` — per-link hourly flow,
reduced cost and bounds — `.gitignore` merely excludes it by default, and **NYISO
already has it committed**: matrix row `unit_network_layer_sidecar`, NYISO cell
**K**, on `nyiso116_c3c_unitlayer`. The question is answerable with **no solve**,
and this session answered it.

**Provenance, stated because it bounds the claim.** That bundle is a zero-delta
replay of the **nyiso-113** keeper recipe, not the current nyiso-120 keeper, and
its **G1 replay fidelity FAILED** (max |Δp| $10.5 / $10.6 / $9.0); nyiso-116
licensed it for C3c tail work on G2. It is used here **only** for link saturation
and gross flow magnitude — a marginal-tie reshuffle in the body of the price
distribution cannot move a bound that holds in ~100 % of hours or a 2–3× flow gap
— and the *measured* side of every comparison below needs no model at all. A
successor wanting the caveat gone commits the layer on the current keeper's own
replay with `git add -f`; the cell is already `K` and there is nothing to arm.

**The answer: the model's external seam delivers the right NET and the wrong
DISTRIBUTION, and the surplus lands east of the cutset.**

| year | link | limit | model flow p50 | hours at bound | **measured p50** |
|---|---|--:|--:|--:|--:|
| **2025** | `external→Capital_Hudson` | 1,600 | **1,600.0** | **100.0 %** | **490.5** |
| | `external→NYC` | 1,000 | **1,000.0** | **100.0 %** | 760.8 |
| | `external→Long_Island` | 1,200 | **1,200.0** | **98.1 %** | 788.6 |
| | `external→Upstate_West` | 3,000 | **−1,688.5** | 0.0 % | **+148.0** |
| | `Upstate_West→Capital_Hudson` | 2,850 | **722.8** (util **0.253**) | 1.5 % | *measured Central East util p50 **0.591*** |

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| downstate-landing import: model (pinned) | 3,800 | 3,800 | 3,800 |
| downstate-landing import: **measured p50** | 1,870 | 1,772 | 2,040 |
| **ratio** | **2.03×** | **2.14×** | **1.86×** |
| upstate border: model p50 | −1,003 | −1,520 | −1,689 |
| upstate border: **measured p50** | **+668** | **+454** | **+148** |
| **NET all four links: model** | +2,797 | +2,280 | +2,112 |
| **NET all four links: measured** | +2,538 | +2,226 | +2,188 |

The three downstate border links sit **at their bound in 98–100 % of all hours of
all three years**, delivering a flat 3,800 MW against a measured downstate median
of 1,772–2,040 MW, while the upstate border link runs **net export** (−1,003 /
−1,520 / −1,689 MW) against a measured **import** of +668 / +454 / +148 MW. The
**net across all four links reconciles to 2–11 %** — exactly the signature of a
seam whose total is pinned (the monthly EIA-930 reconciliation band) while its
spatial allocation is free.

**That is the mechanism.** ~1.8–2.0 GW of surplus import is delivered *east of
Central East* and ~1.0–1.7 GW is drained from the west, so the east never needs
the west and the model's Central-East link carries **722.8 MW at the median
(util 0.253)** where the real interface carries **util 0.591**. The interface
limit was never the defect — rule 14 `[R-ACCURATE]` already grounded it — and no
accurate input is reverted. The defect is one step upstream, on the seam.

**What is NOT concluded.** No lever is proposed and the queue stays empty. Which
part of the seam construction is wrong — the border-link capacities, the import
ladder's tranche pricing, or the absence of any aggregate downstate cap since
nyiso-100 correctly retired the mis-attributed 4,350 MW `NYISO_simultaneous_import`
scalar — is **not** adjudicated here, and nyiso-100's retirement is **not**
re-opened (its provenance finding stands; what is reported is a measured
consequence nobody had checked). This is the PJM `pjm_seam_envelope_by_neighbor`
object in kind, but rule 25 `[R-ISO-SCOPE]` is binding both ways: it enters NYISO
as **`U`**, on NYISO's own data, with NYISO's own parameters. The matrix row
`seam_flow_envelopes` moves NYISO **`.` → `U`** on that basis and on nothing else.

**Residual candidates NOT adjudicated**, carried forward for the successor:
forced eastern generation (the keeper's own D-2 rows carry `ST_GAS
reliability_floor` 2.80 TWh — 21 % of the class — and `firm_import` 7.88 TWh in
2025) and the zonal load allocation. Both are second-order against a 2× seam
misallocation and neither was tested.

**C3c's stated re-open condition is falsified as written, and is flagged rather
than edited.** The C3c ledger entry and the keeper `frontier` note both record the
re-open condition as *"a `Capital_Hudson` → Zone-F/Zone-G TOPOLOGY SPLIT"*. §2 and
§3 establish that this route is neither identifiable nor aimed at the right
boundary. The ledger text is generated by `scripts/gen_nyiso100_attestation.py`
and lives inside the keeper's attestation; **this session does not touch it** —
correcting it is a keeper-text change and belongs with an owner disposition, since
it removes the only stated satisfiable re-open condition C3c has.

## §7 — what is NOT claimed

1. **No mechanism was tested, proposed or armed.** No matrix cell verdict changes.
   The lever queue stays **EMPTY** and no lever was manufactured.
2. **The nyiso-122 TTC refutation is not re-opened.** `UPNY CONED` and
   `SPR/DUN-SOUTH` are re-measured here at 0.0 % binding in every month of every
   year, which *confirms* it. What §4 measures is a **different interface**
   (`CENTRAL EAST - VC`), which nyiso-122 did not test and which is not covered by
   that refutation.
3. **The model's link FLOW was not measured** — it is not in the committed
   sidecars. The evidence that the link is off its bound is the price identity,
   which is exact (prices are LP duals), not a proxy.
4. **No level from the zone-letter basis is quoted as C3a** (§1). The scorer's
   `rt_lw` bench remains the only C3a basis.
5. **No claim the benchmark is wrong.** Every measured price, basis, flow and
   limit here is a validation target (rule 13).
6. **Item 4 (`nyiso_iroquois_winter_spread`) is untouched** and remains
   **unadjudicated** per the owner's 2026-08-04 ruling — cell stays `O`,
   default-off, not part of this charter in either direction.
7. **The F\|G separation is not dismissed as noise** (§3): it is real, it is a
   G-cheaper-than-F object, and it is not the object the charter chartered.
8. **This session's own first reading was falsified by its own measurement**
   (§5) and is recorded as corrected, not quietly dropped.

## §8 — governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; the charter closes on
identification and incidence. Rule 12: **no solve**. Rule 13 `[R-MEASURED]`: every
measured series identifies a boundary or attributes a residual; nothing entered a
solve, and the §3/§5 measurements are diagnostics, not proposals. Rule 14
`[R-ACCURATE]`: §4's finding is that an already-accurate input (the measured
Central-East TTC) is **not** the defect — the defect is downstream of it, and no
accurate input is reverted. Rule 15 `[R-DASHBOARD]`: **no run was produced, so
none is registered**; the keeper is unchanged and its dashboard entry untouched.
Rule 16: n/a. Rule 17 `[R-FLOOR-WINDOW]`: no window declared. Rule 19
`[R-ONE-MECH]`: §5 decides the open §7(2) question **against** a second mechanism
for Object B. Rule 20 `[R-DOF]` / rule 21: DOF ledger unchanged, nothing tuned; the
§6 residual is written up as an open blocker, not closed by a picked value. Rule 22
`[R-HOLDOUT]`: **training years only** — `YEARS` is a hard filter and every loader
raises otherwise, which matters because the committed NYISO series carry 2018–2022
and 2026 and because the probe *fetches* from a public archive; the holdout spend
freeze is ACTIVE and untouched, and NYISO's `complete`/`final` markers are
unchanged. Rule 23 `[R-FROZEN-DERIVE]`: nothing re-derived. Rule 24 `[R-REGISTRY]`:
no tunable added. Rule 25 `[R-ISO-SCOPE]`: **NYISO only**. Rule 27 `[R-PUSH]`: every
file authored here is new; nothing ≥300 lines was rewritten; pushes are exact local
bytes. Rule 28: duty (a) the queue was read first and found **EMPTY** and the
DO-NOT-REDO list was honoured (the Tier-3 TTC re-grounding is not re-opened, G-J is
not re-tested, item 4 is untouched, no second peak mechanism is proposed); duty (b)
**no cell verdict changes because no mechanism was tested** — the §5.5 status block
and the matrix header carry the new evidence.

**Hook hygiene (the recurring artifact).** `.claude/hooks/ruff-autofix.sh` runs
`ruff format .` whole-tree and reformatted
`scripts/data/derive_chp_power_only_heat_rates.py` — another lane's file, the same
one nyiso-122 §5(5) and nyiso-123 §5(7) flagged. It was caught in the pre-commit
status scan and restored byte-identical to HEAD before any commit.

## §9 — reproduce

```
uv sync
PYTHONPATH=.:src uv run --with pypdf python scripts/probes/_nyiso124_charter_g0_g1.py
```

No LP; runs in a few minutes. The probe reads the keeper's committed `hourly/`
sidecars, the committed MIS P-32 interface postings and the committed measured
zonal load, and fetches the public MIS monthly zonal-LBMP and ATC/TTC zips it does
not find in `data/raw/lmp-data/NYISO` into a gitignored `.cache/nyiso124/`. The
Gold Book keyword scan needs `pypdf`, which is not a project dependency; without
it the section reports `[not scanned]` rather than asserting the result. Sections:
`sources`, `incidence`, `binding`, `objectb`.
