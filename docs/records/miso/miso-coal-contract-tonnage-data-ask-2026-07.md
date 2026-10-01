# STANDING DATA ASK (opened 2026-07-29, miso-104) — MISO coal minimum-take tonnage from an EX-ANTE CONTRACTUAL source

**Status:** OPEN. Blocking. No session may treat this as closed until a source
clears §4 — **both** the §4.1 A–F specification **and** the §4.2 pin-strength
battery.

**Authority:** the miso-103 no-build determination
(`results/calibration/FINDING-miso103-coal-mintake-tonnage-2026-07-29.md` §4),
which names this as "a data-intake project, not a modelling session … the
second MISO data ask" beside the outage-grain ask
(`docs/handoffs/miso-outage-grain-data-ask-2026-07.md`, whose format this
mirrors). miso-104 executed the sourcing pass that opens it.

**This is a DATA ask, not a build charter.** It specifies what would have to
exist before the minimum-take LP constraint could be built. Until a source
clears §4, the correct behaviour is rule 24 `[R-DOF]`: report and stop. The
constraint block itself remains its own chartered session (miso-96 §7) and is
**not** authorised by this document.

**miso-104 result in one line:** the datum exists as a *form field* (FERC Form
580 Q6a) and as a *published document class* (Kentucky's fuel-contract
repository), but **no source publishes it at plant grain across the MISO target
set for 2023–2025** — so no candidate series reached the threshold of being
testable, and the §4.2 battery could not be run on anything. §3 records each
candidate with its measured blocker; §8 is the one bounded experiment that
would settle the best of them.

---

## 1. What is blocked, and by exactly what

**C7 COAL_PRB diurnal shape fails 3/3 years on the MISO keeper
(`2026-07-28-miso-101b-tempgrain`) with NO open admissible lever.** miso-102
proved the attribution — the regulated committed-band take-or-pay discount pins
~55 % of each regulated plant at VOM in all 8760 h — and closed the surrounding
lane space (offer steepening, price formation, blunt `sunk_fixed`, PRB-scoped
discounts, floors/min-gen: all refuted or not licensed; miso-102 §6). The one
identified successor is the **minimum-take LP constraint**: a contract-period
tonnage constraint `Σ_t P[p,t] ≥ MinTake[p, period]`, priced by its dual, which
separates *job 1* (the unit stays committed) from *job 2* (it chooses **when**
within the period to burn) and so restores cycling without deleting regulated
self-commitment.

**The single blocking fact:** that constraint needs a right-hand side, and
**EIA-923 publishes deliveries, not contract terms**. miso-103 tested the only
forward-regenerable receipts construction —
`MinTake[p,Y] = contract_share[p] × mean(tons[p, Y−3..Y−1])` — and it FAILED
the admissibility gate on every measure:

| miso-103 measure | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| log-space cross-section R² vs same-year burn (lag-3) | 0.923 | 0.874 | 0.935 |
| aggregate floor ÷ same-year actual tons | 0.964 | **1.136** | 0.978 |
| energy-weighted floor as % of actual CAMPD coal energy | 90.3 % | 95.9 % | 90.9 % |
| binds vs the discount-free control, of 38 plants | 22 | 33 | 20 |
| TWh forced above unconstrained economics | 32.0 | 44.0 | 19.6 |

Lag-1 and lag-5 give the same 0.87–0.94 — receipts autocorrelation *is* the
contract persistence, so lagging is cosmetic de-identification of the same
answer key. The within-plant **delta** test is R² **0.172**: the construction
transmits the *level* of the measured outcome while failing to transmit the
*year's driver* — the exact inversion of what rule 13 `[R-MEASURED]` admits.

**So the lane is blocked on the RHS and only on the RHS.** The mechanism is
specified, the control run exists (`2026-07-29-miso-102b-sunkfixed`), the
target set is enumerated, and the admissibility battery is written and
reproducible. What is missing is a tonnage that was fixed **before** the
delivery year.

**The target set** (regenerate with
`scripts/probes/miso104_contract_source_coverage.py`, no LP, no network):
**39 plants, 26 owners, 12 states**, all EIA-860 regulated — the take-or-pay
coal plants that report Schedule-5 fuel costs, which is exactly the set the
constraint targets. **94.0 / 80.7 / 89.5 Mt** in 2023 / 2024 / 2025. The five
largest owners (Union Electric, Rainbow Energy Center, MidAmerican, DTE
Electric, Duke Energy Indiana) are 39 / 44 / 44 % of the tonnage; the tail runs
to municipals and co-ops (City of Springfield, Muscatine, Southern Illinois
Power Coop) at well under 1 Mt each.

## 2. The required datum — specification

A source clears this ask only if it delivers **all** of A–F **and then survives
the §4.2 battery**. A–F is necessary; the battery is sufficient.

| | requirement | why |
|---|---|---|
| **A** | **Ex-ante by construction.** The quantity must be a **contract term** whose instrument was executed *before* the delivery year (signing/effective date < 1 Jan of the delivery year), not a delivery, receipt, burn, or any smoothing of one. | This is the whole ask. miso-103 §2: any post-hoc quantity is the answer key however it is lagged. |
| **B** | **Plant grain from the source itself, with NO receipts bridge.** The tonnage must attach to a named generating plant *by the document* — the contract names the destination plant, or the contract maps 1:1 to one plant. **Apportioning a multi-plant contract across plants by delivered tons is DISQUALIFYING**, because the apportionment weights are the forbidden series. | The constraint is per-plant. A contract-grain quantity split by receipts re-imports exactly what miso-103 refuted, one level down. |
| **C** | **A cross-section wide enough to test and to matter: ≥ 15 of the 39 target plants AND ≥ 60 % of target-set tonnage, in EACH of 2023, 2024, 2025.** | The §4.2 battery is a cross-section regression (miso-103 ran n ≈ 38); a handful of plants yields no R² and cannot be adjudicated either way. The 60 % tonnage leg is so the constraint governs the majority of the class it exists to reshape rather than a decorative corner of it. |
| **D** | **All three training years inside one vintage span.** | Rule 16 `[R-ALLYEARS]`: keepers solve and register 2023–2025 in one bundle. A source covering 2023 only cannot feed a keeper. |
| **E** | **Terms, not just a number** — duration, price/quantity reopeners, make-up or carry-over tons, force-majeure and buy-out/buy-down provisions. | Rule 13's forward test is *"would it respond to changed conditions?"*. The stated mechanics are what let a forecast year regenerate the quantity and let it move when conditions move. A bare tonnage with no terms cannot answer that question. |
| **F** | **Enumerable retrieval.** Programmatic bulk access, or an explicit documented retrieval path for 39 plants × 3 years. | Not a purity criterion — a one-off hand assembly cannot be re-derived when the source updates (rule 23 `[R-FROZEN-DERIVE]` requires re-derivation to cite a *data* change, which presumes a repeatable pull). |

### 2a. What a clearing source actually looks like

This is not hypothetical — a **public, un-redacted instance of exactly the
right datum exists**, it is simply in the wrong state. Kentucky PSC publishes
utility fuel-supply contracts in full (§3(b)). In
`Alliance Coal, LLC / LG&E & KU Contract No. J24007`, executed 2024-01-19,
Section 3 reads:

> §3.1 **Base Quantity.** … a total of 3.4 million tons subject to the
> following annual base quantity of coal nominated by Buyer ("Base Quantity")
> on a quarterly basis:
>
> | YEAR | BASE QUANTITY (TONS) | QUARTERLY NOMINATION (TONS) |
> |---|---|---|
> | 2024 | 150,000 | 37,500 |
> | 2025 | 500,000 – 600,000 | 125,000 – 150,000 |
> | 2026 | 750,000 – 950,000 | 187,500 – 237,500 |
> | 2027 | 1,000,000 – 1,200,000 | 250,000 – 300,000 |
> | 2028 | 500,000 – 1,000,000 | Remaining tons divided by 4 |

plus §3.2 **Make-up Tons** (undelivered quantity rolls into the following
calendar year and *increases* that year's Base Quantity), §3.3 quarterly
nominations due 15 Nov / 15 Feb / 15 May / 15 Aug for the following quarter
with the minimum applying by default, §10 force majeure, and §2 a stated term
through 2028-12-31.

That is A and E in full: fixed years ahead of delivery, with a floor **and** a
ceiling, an explicit shortfall-carry mechanic, and stated conditions under
which it changes. It is also the reason the ask is written as it is — the
target is a document of this kind for MISO plants, not a statistic.

## 3. Candidate sources — assessed by miso-104, none cleared

Every entry below was **checked**, not hypothesised. Each records what it
actually contains and the measured blocker.

### (a) FERC Form 580 — the right field, at the wrong grain, with thin coverage and a timing gap

*Interrogatory on Fuel and Energy Purchase Practices*, FPA §205(f)(2),
18 CFR 141.61, OMB 1902-0137, Docket **IN79-6-000**.

**Frequency and vintage — biennial, filed in even years, covering the two
preceding calendar years.** The 2018 form asks for contracts "in force at any
time during 2016 and/or 2017"; the 2020 Desk Reference sets responses due
2020-10-30; DTE Electric filed a partial-waiver request for the **2024** form
on 2024-10-31 (90 FR 7691, 2025-01-22); Pacific Gas and Electric filed one for
the **2026** form on 2026-05-21 (91 FR 32025, 2026-05-29). So:

| form | reporting years | status as of 2026-07-29 |
|---|---|---|
| 2022 | CY2020–2021 | filed (out-of-training, §5) |
| 2024 | CY2022–**2023** | filed — **covers one training year** |
| 2026 | CY**2024**–**2025** | **due 2026-10-30 — not yet filed** |

**What Question 6a collects** (per contract, per reporting year): Contract
ID / number · Reporting Year · **Contract signing date** · **Contract
expiration date** · Is contract evergreen? · Contract type (Appendix A coal
types) · **Fuel quantity — Coal (×10³ tons)** · Coal Btu/lb · sulfur / ash /
moisture.

**What Question 6b collects** (per delivery, electronically linked to the
contract): **Destination Plant** (drop-down, plus a "Plant Not Listed" free
field) · primary state/country of origin · type of purchase point ·
transport distance · **Coal (×10³ tons)** delivered · **Coal (×10³ tons) not
delivered by end of contract year** · quality/impurity · actual weighted-average
FOB origin and FOB plant price (¢/mmBtu). Q7 adds contract **shortfall** cause
and the shortfall **costs** passed through the FAC; Q8 adds buy-downs and
buy-outs.

**The Q6a coal quantity is genuinely ex-ante** — it is a contract
specification carrying its own signing date, reported alongside the deliveries
against it. It satisfies **A** and much of **E**. Four blockers:

1. **Grain (structural, and the serious one).** The quantity is at **contract**
   grain; the plant appears only on the **delivery** rows. A contract serving
   *n* plants can be pushed to plant grain only by delivered tons — the exact
   receipts weighting miso-103 refuted. **Admissible only for contracts with a
   single destination plant.** What share of MISO target-plant tonnage sits in
   such 1:1 contracts is **unmeasured** and is the first job of §8.
2. **Coverage (severe).** Q6 is answered **only** by utilities with a
   *wholesale* FERC fuel adjustment clause under 18 CFR 35.14 — the 2020 Desk
   Reference is explicit that a utility with no FAC completes Questions 1 and 2
   and stops. The current information-collection request estimates
   **24 respondents with FACs nationally** (Docket IC25-1-000, 2024-12-03),
   down from 29 in the 2020 collection — across **all fuels and all regions**.
   The MISO target set is 26 owners recovering fuel predominantly through
   **state retail** fuel clauses, which are outside 35.14 and therefore outside
   Q6.
3. **Scope.** Only contracts **longer than one year in duration**, and only
   where the costs ran through the 35.14 clause.
4. **Retrieval (F).** Individually eFiled PDFs in docket IN79-6. No bulk
   dataset, CSV, or API is published; eLibrary is a Cloudflare-gated SPA and no
   public search API resolved from this environment (probed 2026-07-29:
   `/eLibraryAPI/v1/...` 404, no API base in the client bundle). Retrieval is
   through the eLibrary UI, per filing.

**Verdict: does not clear today**, on B and C certainly and on D by timing.
**But blockers 2–4 are countable rather than fatal, and blocker D expires**:
from ~Nov 2026 the 2024 + 2026 forms span 2023–2025 exactly. This is the only
national, standardised, ex-ante contract-quantity collection that exists, and
§8 is its bounded test.

### (b) State fuel-adjustment / fuel-cost-recovery filings — one exemplary state at 1/39 coverage; the large states file it under seal

**Kentucky clears on kind and fails on coverage.** 807 KAR 5:056 requires each
utility to file *copies of each fossil fuel purchase contract* plus all
amendments at the time they are entered into, and the PSC publishes them:
`https://psc.ky.gov/webnet/fuelcontracts`. The J24007 excerpt in §2a is from
that repository, un-redacted. **But the repository covers six Kentucky
utilities (BREC, DEK, EKPC, KP, KU, LGE), of which exactly one — Big Rivers
Electric — is in MISO**, holding one target plant: **D B Wilson (6823) =
1.5 / 1.1 / 1.1 % of target-set tonnage in 2023 / 2024 / 2025**. That is an
order of magnitude below the §2C bar and yields no cross-section. Two further
practical notes: the browsable index is a **rolling recent-filings view**
(36 documents at fetch on 2026-07-29), not an archive — historical contracts
are reachable by direct URL but are not enumerable from the index (an **F**
problem) — and BREC's currently-indexed documents are six **gas** supply
agreements dated 2026-07-09, with no D B Wilson coal supply agreement
surfaced.

**The large MISO states do not publish the equivalent.** Indiana is the
pattern and was checked directly: in Cause No. 38702 FAC-91 (OUCC *Public's
Exhibit No. 2*, filed 2023-09-05) the section headed **"VI. COAL CONTRACTS AND
INVENTORY"** is entirely qualitative — the direction of inventory, a
recommendation that the utility "update the Commission on its 2023 projected
coal burn and coal purchases", and EIA regional price charts. Contract
specifics live in confidential attachments. Indiana alone is 8 plants and
13.3 Mt (2025) of the target set.

> **STATUS 2026-08-06 (miso-135) — MICHIGAN IS SPENT AND CLOSED ON KIND. DO NOT
> RE-DERIVE.** The paragraph below is preserved as written; its premise is
> **falsified** and it must be read against this block.
> **Both utilities DO publish an ex-ante coal-contract tonnage, publicly, for all
> three training years** — DTE Exhibit **A-15** *Long-Term Coal Contracts*, whose
> column (b) is defined by the exhibit as *"the minimum tonnage contracted to
> purchase in the <Y> PSCR plan year"* (**6,015 / 6,165 / 4,818** kt), and
> Consumers Exhibit **A-22/A-24 (AKR-1)** *Coal Contract & Purchase Data*
> (committed **4,019,216 / 2,710,680 / 156,000** t). Volumes are neither
> confidential nor cost projections: **leg A PASSES**.
> **Leg B FAILS 6/6 — no destination-plant column exists** in either utility in
> any of the three plan years (Consumers **U-21257 / U-21423 / U-21592**, DTE
> **U-21259 / U-21425 / U-21594**), machine-verified by re-deriving every column
> header from the live docket (`plant_word_on_page` FALSE 6/6). DTE burns at
> Monroe **and** Belle River, Consumers at Campbell **and** Karn in 2023, so only
> delivered-tons weights would split the totals — **§2B disqualifying**. The only
> plant-grain coal tonnage in the filings is a **projected as-burned** volume,
> closed on principle at §3(c).
> **The §2C bar fails on measurement, not arithmetic alone**: Michigan is **2 of
> 39 plants** and **10.6 / 12.6 / 12.8 %**; the §2B 1:1 carve-out yields
> Consumers/**J H Campbell** in 2024–25 only = **1 plant, 0 in 2023**.
> **This paragraph's "combined with a Form 580 pull" premise is FALSE**: Michigan
> cannot compose, because its tonnage attaches to no plant at all; it is strictly
> **worse than Form 580 on leg B**; and for **DTE the PSCR route is DOMINATED**
> (DTE is a Form 580 filer — partial-waiver request 2024-10-31, 90 FR 7691 —
> so the same contracts reach Form 580 *with* a Destination Plant). **§8 remains
> the decisive, undischarged next step.**
> Do **not** re-open the PSCR **reconciliation** cases either: they report against
> the plan **ex post**, i.e. the miso-103 answer key.
> `results/calibration/FINDING-miso135-michigan-pscr-contract-grain-2026-08-06.md`.
> *(Original text follows.)*

**Not yet checked, and the highest-value remaining state: Michigan.** The PSCR
process (MCL 460.6j) is the most genuinely *ex-ante* state mechanism in MISO —
a plan-year filing plus a five-year forecast, filed **before** the plan year,
with an annual reconciliation against it — and its two utilities (DTE Electric,
Consumers Energy) are **11.4 Mt = 12.8 % of 2025** target tonnage. Whether the
*public* PSCR plan exhibits carry per-plant contracted coal tonnage (as opposed
to cost projections, with volumes confidential) is **open**. It cannot clear
§2C alone, but combined with a Form 580 pull it is the second-largest block of
addressable tonnage.

### (c) IRP fuel-budget exhibits — REJECTED ON KIND, do not re-attempt

Integrated resource plans publish forward **fuel price** trajectories and
**modelled burn** from the utility's own capacity-expansion run. Modelled burn
is *another model's forecast of the outcome* — feeding it in would substitute
that model's answer for ours. That is rule 13's forbidden half in a worse form
than receipts, since it is not even a measurement. Contract position, where it
exists at all, is a confidential workpaper. **This candidate is closed on
principle, not on availability** — a future session must not "check whether the
IRPs have it".

### Explicitly ruled OUT — do not re-attempt

* **Any receipts-derived tonnage**, in any window / lag / smoothing / scalar
  shrink (miso-103 §2 and §4).
* **EIA-923 Schedule 2 `purchase type` (C/S/T) and `contract expiration
  date`.** The dates are genuine contract terms, but the quantity on the same
  row is a **delivery**; subsetting receipts by the contract flag yields
  receipts.
* **SEC 10-K "purchase obligations" / fuel commitment tables.** Company grain,
  denominated in **dollars**, not tons; converting needs a price assumption and
  there is no plant key. Fails A's spirit and B outright.
* **Coal producer disclosures** ("committed and priced tons" — Alliance,
  Hallador, NACCO, Core Natural). Genuinely ex-ante, but at **producer** grain
  across all customers, with no plant key and no MISO scoping.
* **FERC Form 1 page 402 steam-plant statistics.** Fuel **burned**, ex post.
* **STB Carload Waybill Sample.** Ex-post shipments, confidential, no plant
  identifier in the public-use file.
* **A penalty-priced soft floor, or a scalar-shrunk floor** (`0.7 × …`). Both
  identify their knob off the C1/C7 residual — rule 24 `[R-DOF]`, and rule 17
  `[R-FLOOR-WINDOW]`'s window would come from the tuning, not a driver.

## 4. Acceptance test

A candidate is accepted only on a written finding that answers **both** parts.

### 4.1 Specification

**§2 A–F, each with the actual field names, document class, grain and year
span** — not a description of the publication. State explicitly, for B, how
each plant's tonnage is attached *by the source*, and, for C, the measured
plant count and tonnage share **per year** against the
`miso104_contract_source_coverage.py` denominators.

### 4.2 The pin-strength battery — BINDING, run BEFORE any mechanism charter

Run the miso-103 methodology
(`scripts/probes/miso103_mintake_pin_strength.py`) on the candidate,
substituting it for the trailing-mean construction. Report all five, per year:

1. **Level identity** — log-space cross-section R² of same-year actual receipt
   tons on the candidate. miso-103's failing range was **0.87–0.94**. A
   candidate at **≥ 0.80 FAILS**: it is the answer key by another name.
2. **Floor ÷ actual** — aggregate MinTake ÷ same-year actual tons, and the
   energy-weighted floor as a share of actual CAMPD coal energy. miso-103
   failed at 0.96 / 1.14 / 0.98 and 90–96 %. A candidate that lands annual coal
   energy on actuals **FAILS regardless of its provenance** — a contractual
   pedigree does not license a pin.
3. **No overshoot** — no year may put the aggregate floor **above** actual
   burn. 2024's 1.136× was miso-103's independent killer: a hard `≥` floor then
   forces more coal than reality burned, breaking C1 in the opposite direction.
4. **Delta test — the one that must PASS.** Within-plant year-over-year R² of
   Δactual on Δcandidate. miso-103's **0.172** was the diagnostic inversion:
   level without driver. **An admissible contractual series shows the opposite
   profile — LOWER level-R² (1) and HIGHER delta-R² (4) than the receipts
   construction.** That signature — carries the year's driver, does not
   reproduce the level — *is* what rule 13 admissibility looks like, and it is
   the single most informative number in the battery.
5. **Binding margin** — against the discount-free control
   `2026-07-29-miso-102b-sunkfixed`: plants bound and TWh forced above
   unconstrained economics, so the pin is assessed as operative rather than
   hypothetical.

**A candidate that clears 4.1 but fails 4.2 is INADMISSIBLE and is not built**
(rule 13; the miso-103 precedent is that this determination is made ex ante,
with no LP). Report it, update the matrix cell, stop.

**Symmetry clause, as in the outage ask:** a source that clears §4.1 and §4.2
but shows that contracted minimums are **not binding** on MISO coal — e.g.
Base Quantities well below observed burn at most plants — has **refuted** the
minimum-take hypothesis rather than enabled it. That outcome is a finding to be
reported, not a source to be discarded, and it would close the lane honestly.

## 5. Rule-22 intake protocol

* Training years **2023–2025** are unrestricted.
* Any **out-of-training** vintage — including the **2022 Form 580 (CY2020–21)**
  and any contract instrument covering pre-2023 deliveries — requires its own
  **explicit, session-logged owner authorization**, appended verbatim to
  `intake_log` in `frontend/data/backcast/calibration-complete.json`, and is
  validated **no-LP only** (byte-identity / loader-resolvability / row counts).
  The 2018–2022 **receipts** authorization does **not** extend to these
  sources; they are new sources.
* **MISO carries NO calibration-complete marker.** Solve, score and dashboard
  registration of any out-of-training year stay fully quarantined regardless of
  intake; CI (`quarantine-gates`) enforces this independently.
* **miso-104 intook nothing.** No new-source authorization was requested or
  granted in that session; nothing was written under `data/raw/`. Every
  document cited here was read in a scratch directory and is re-fetchable from
  the URLs in §7.

## 6. What this ask must not become

* **Not** a licence to reopen the receipts construction under a new name. A
  "contract-flagged", "nominated", or "budgeted" tonnage that is ultimately
  derived from deliveries is the same answer key (miso-103 §2).
* **Not** a licence for a penalty-priced soft floor, a scalar-shrunk floor, or
  any other softening whose parameter is identified off the residual — no
  matter what the incoming data shows (rules 13 `[R-MEASURED]` / 24 `[R-DOF]`).
* **Not** a licence to reach for a substitute C7 mechanism. miso-102 §6 closed
  offer steepening, price formation, blunt `sunk_fixed`, PRB-scoped discounts
  and floors/min-gen; the miso-103 charter's prohibition stands — if this ask
  does not clear, C7 stays failing and unledgered.
* **Not** authorization to build the constraint. Even a clearing source only
  unblocks the **charter** for the constraint session (miso-96 §7), which
  brings its own pre-registered gates.
* **Not** a blocker on unrelated MISO work. The keeper stands; this ask governs
  whether C7 can ever be *closed*, not whether MISO can proceed.

## 7. Sources consulted (miso-104, 2026-07-29)

Vintages and URLs in `docs/parameter-citations.md` style. Nothing below was
intaken; all were read for assessment only.

| source | vintage | URL |
|---|---|---|
| FERC Form 580 Desk Reference | 2020 | `https://www.ferc.gov/sites/default/files/2020-08/2020-FERC-Form-580-desk-reference.pdf` |
| FERC Form 580, blank form (Q6a/6b field set) | 2018 | `https://www.reginfo.gov/public/do/DownloadDocument?objectID=83588101` |
| FERC Form 580, Q5 Privileged Addendum | 2018 | `https://www.reginfo.gov/public/do/DownloadDocument?objectID=83588401` |
| FERC-580 information collection request (respondent counts: 24 with FACs) | 2024-12-03, Docket IC25-1-000 | `https://www.federalregister.gov/documents/2024/12/03/2024-28248` |
| DTE Electric partial-waiver request, **2024** Form 580 (filed 2024-10-31) | 90 FR 7691, 2025-01-22 | `https://www.federalregister.gov/documents/2025/01/22/2025-01504` |
| PG&E partial-waiver request, **2026** Form 580 (filed 2026-05-21) | 91 FR 32025, 2026-05-29 | `https://www.federalregister.gov/documents/2026/05/29/2026-10788` |
| Kentucky PSC fuel-contract repository (807 KAR 5:056) | index fetched 2026-07-29 | `https://psc.ky.gov/webnet/fuelcontracts` |
| Coal Supply Agreement, Alliance Coal LLC / LG&E & KU No. J24007 (§2 Term, §3 Quantity) | executed 2024-01-19 | `https://psc.ky.gov/PSC_WebNet/FuelContracts/Kentucky%20Utilities%20Company%20-%20KU/Alliance%20Coal%201-19-24.pdf` |
| IURC Cause No. 38702 FAC-91, OUCC Public's Exhibit No. 2 (§VI Coal Contracts and Inventory) | filed 2023-09-05 | `https://iurc.portal.in.gov/_entity/sharepointdocumentlocation/55234c27-9e63-ee11-be6e-001dd80bf130/bb9c6bba-fd52-45ad-8e64-a444aef13c39?file=38702+FAC+91+-+Public+Exhibit+No.+2.pdf` |

## 8. The one bounded experiment that would settle candidate (a)

Cheapest decisive next step, **no LP, no solve, training-year only**: pull the
**2024** Form 580 filings (filed on/around 2024-10-31, covering CY2022–2023)
for the 26 target owners from eLibrary docket **IN79-6** and answer three
counts:

1. How many of the 26 owners filed a Form 580 at all?
2. Of those, how many answered **Question 6** — i.e. hold a 18 CFR 35.14
   wholesale FAC? (This is the §3(a) blocker 2 test, and the national ceiling
   is 24 filers across all fuels and regions.)
3. Of their reported **coal** contracts, how many have exactly **one**
   destination plant, that plant is in the target set, and what share of **2023**
   target tonnage do those 1:1 contracts cover? (This is blocker 1, the only
   one that cannot be inferred from published aggregates.)

**Access re-probed 2026-07-29 (miso-105, incidental): eLibrary is still
SPA-walled with no reachable public API.** Four endpoint classes tried from the
session environment — the legacy `idmws/*.asp` CGI (`docket_sheet.asp` etc.,
which 301-redirects into the Angular app), `eLibrarySWS/api/v1/*` (404), and
both `eLibrary/api/*` and `eLibrary/assets/*.json` (which return the 22,464-byte
SPA shell for every path). The only `/api/` base in the app bundle is Datadog
RUM, not FERC. So this count needs either a headless-browser session against the
search UI or an authorized alternative source; it is **not** a `curl`-able
fetch. This does not change the ask's status — it records what the next session
should not re-derive.

If (3) clears the §2C bar for 2023, the lane is **timing-blocked, not
data-blocked**, and the ask reduces to waiting for the **2026** form
(CY2024–2025, due **2026-10-30**) to complete the three-year span — at which
point §4.2 runs on a genuine contractual series for the first time. If (3) does
not clear, candidate (a) is closed on grain and coverage, Michigan PSCR
(§3(b)) becomes the sole remaining lead, and C7 stays where miso-103 left it.

**Governance note — the budget is saturated.** MISO's non-protective ledgered
caveat budget is **3/3** (C3a mean LMP, C3b price shape, C3c price tail;
`MAX_LEDGERED_CAVEATS = 3`). C7 is **not** ledgered and cannot be — which is
what makes this ask load-bearing rather than housekeeping: the next
load-bearing MISO miss must be *built*, and this is the datum that would let
the one identified mechanism be built honestly.

## 9. §8 retrieval attempt, xiso-4 (2026-08-04) — the count is NOT PRODUCIBLE from a standard session

**No LP, no solve, no intake.** Nothing was written under `data/raw/`; the
assessment-not-intake posture of §5 ("miso-104 intook nothing") was preserved, so
no rule-22 authorization was required or claimed. **No receipts variant was
re-tested** (miso-103 DO-NOT-REDO respected) and **no charter was written** —
nothing cleared §4, so per §6 nothing was built and C7 stays failing and
unledgered.

**The §8 count was attempted and could not be produced.** Three retrieval routes
were tested; all close. Two are new relative to miso-104/105.

1. **eLibrary exposes no machine surface — reconfirmed against the CURRENT
   bundles.** Every `/eLibrary/*` path returns the same 22,464-byte SPA shell
   (`/eLibrary/api/search`, `/eLibrary/filelist`,
   `/eLibrary/docketsheet?docket=IN79-6`, and the legacy
   `idmws/search/fercgensearch.asp`); everything else 404s. All four JS bundles
   were fetched at their current hashes and grepped: the **only** `/api/` base is
   `"/api/v2/"` inside the **Datadog RUM SDK** (`ddforward`, `datadoghq`).
   §3(a) blocker 4 and the miso-105 note are correct and now independently
   re-verified rather than carried forward on trust.
2. **NEW — the headless-browser fallback this ask names is unavailable.** §8 says
   the count "needs either a headless-browser session against the search UI or an
   authorized alternative source." Chromium + Playwright are installed in the
   session image, but **Chromium cannot traverse the agent proxy at all**:
   `example.com` fails with `ERR_CONNECTION_RESET` identically to
   `elibrary.ferc.gov`, with and without `--proxy-server` / `proxy=`, and the
   proxy logs a `non-CONNECT request` from the browser. This is a browser-egress
   limitation of the session environment, **not** a FERC block. The ask's own
   escape hatch does not work in a standard session.
3. **NEW — FERC's structured open-data catalog does not carry Form 580.**
   `data.ferc.gov` is a real data catalog with a developer API, and a surface
   miso-104/105 never probed (both hit only `elibrary.ferc.gov`). It publishes
   **Forms 1, 552 and 556 and the Market-Based Rate database**; searching the
   Electric catalog for "580" returns **zero** hits. There is therefore **no
   bulk/API alternative to eLibrary for Form 580.** (`www.ferc.gov` is
   additionally 403/bot-blocked from this environment.)

**Status unchanged — still blocked — but on a sharper boundary.** It is no
longer "the browser route is untried"; it is *eLibrary exposes no API, FERC's
open-data catalog does not carry this form, and the browser fallback is
environment-blocked*. Producing the count requires a session with working
browser egress, or a human/authorized eLibrary retrieval.

### The scheduling point, which is independent of the count

The **2026** Form 580 (CY2024–2025) is **due 2026-10-30**; today is 2026-08-04.
The CY2024 and CY2025 contract data **does not yet exist**, so this ask **cannot**
clear §2C's "≥15 plants AND ≥60 % of tonnage in EACH of 2023/2024/2025" before
late 2026 — *whatever the count returns*. Per §8 the count decides only **which
kind** of blocked the lane is (timing-blocked vs data-blocked). Hence the owner
question:

> Spend a human/authorized eLibrary retrieval **now** to distinguish
> timing-blocked from data-blocked, or **wait** for the 2026 form and run the
> §8 count once against the full 2023–2025 span? Waiting forfeits nothing that
> is recoverable today.

### Target-set denominators, re-derived for the record

From committed artifacts only (`scripts/probes/miso104_contract_source_coverage.py`,
no network, no LP): **39 plants across 26 owners**, **93.99 / 80.67 / 89.52 Mt**
in 2023 / 2024 / 2025. Unchanged from miso-104.

`docs/handoffs/xiso-4-queue-ratchet-2026-08-04.md` §3(a).
