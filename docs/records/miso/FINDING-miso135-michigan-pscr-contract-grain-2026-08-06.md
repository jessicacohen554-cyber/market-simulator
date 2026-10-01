# FINDING — miso-135: Michigan PSCR publishes a genuine EX-ANTE minimum-take tonnage, publicly, for all three training years — and it is STILL inadmissible, because it is published at CONTRACT grain and the only bridge to plant grain is the forbidden series

**Session:** miso-135, 2026-08-06, branch `claude/miso-135-calibration-zya3y5`,
off `origin/main` at `2321ce86`.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NOTHING INTAKEN under `data/raw/`.** MISO keeper
unchanged at **`2026-08-05-miso-132b-cc-committed`** (bundle
`results/calibration/miso132_ccmin_B`, **NOT-YET**, sole FAIL C7 `COAL_PRB` 2025
`cv_ratio` 0.338 vs 0.50, ledgered caveats 2/3 {C3a, C3c}). Rule 22
`[R-HOLDOUT]`: 2023–2025 only — MISO holds no marker; no 2022 / 2019 / H1-2026
year was solved, scored or read, and no out-of-training quantity was extracted
from any document.

**Pre-registration** `results/calibration/PREREG-miso135-michigan-pscr-tonnage-lead-2026-08-06.md`,
committed and pushed at **`d4d182a5`** *before any adjudicating statistic and
before any MPSC document was opened.* **Probe**
`scripts/probes/_miso135_michigan_pscr_tonnage_lead.py`; **record**
`results/calibration/_miso135_michigan_pscr_tonnage_lead.json`.

**Lane:** charter option **(a)** — the **Michigan PSCR state lead**, the sole
unspent item on the MISO board, named at
`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` §3(b) as *"not yet
checked, and the highest-value remaining state."*

---

## 1. Headline

**The ask's open question is ANSWERED, and the answer is both halves of a split.**

> §3(b): *"Whether the public PSCR plan exhibits carry per-plant contracted coal
> tonnage (as opposed to cost projections, with volumes confidential) is
> **open**."*

**The volumes are NOT confidential and they are NOT cost projections.** Both
Michigan utilities publish, in the public record, an ex-ante coal-contract
tonnage for every one of the three training years. DTE's is *literally the
datum the minimum-take constraint needs* — Exhibit A-15 column (b) is defined
by the exhibit itself as:

> **"the minimum tonnage contracted to purchase in the 2023 PSCR plan year"**

That is a **MinTake**, filed 2022-09-30 for delivery year 2023, with contract
term dates and price. Nothing in the ask's §2a wish-list about ex-ante-ness is
missing. **Leg A PASSES, in both utilities, in all three years.**

**And the source is still inadmissible, decisively, on leg B.** Not one of the
six coal-contract exhibits — two utilities × three plan years — carries a
**destination-plant column**. The tonnage is at **contract** grain; the filings'
only plant-grain coal quantity is a *projected as-burned* volume, which fails
leg A on kind. Splitting a contract across plants would take delivered-tons
weights, which ask §2B calls **DISQUALIFYING** in terms.

**Branch: CLOSED ON KIND** (PREREG §4). The Michigan lead is **SPENT**.

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **G-0** access (GATING) | **PASS.** All six PSCR **PLAN** cases enumerated from the public MPSC docket and each verified by `Case.Subject`. |
| **G-1** kind (GATING) | **FAIL** — leg A **PASS**, leg **B FAIL**, leg E **PARTIAL**. §3–§4. |
| **G-2** coverage §2C | **FAIL.** Michigan is **2 of 39 plants** and **10.6 / 12.6 / 12.8 %** of target tonnage vs bars of ≥ 15 plants **and** ≥ 60 %. Battery-power sub-bar also fails: **n = 0 / 1 / 1** vs ≥ 8. |
| **G-3** §4.2 battery | **NOT RUN — CANDIDATE NOT ACCEPTED.** No leg-B-clearing series exists to test, and at n ≤ 1 a cross-section cannot reject. Per PREREG §2/§4 a battery that cannot reject **cannot acquit**: not accepted, *never acquitted*. |

**K1–K8 all honoured.** No LP; nothing written under `data/raw/`; no receipts
variant re-tested; no threshold softened; no mechanism built or sized; no
adjudicated cell re-opened; no other ISO's cell touched; the projected-burn trap
was named in advance (K7) and it fired (§4).

**G-0 detail.** MPSC files PSCR **plan** and **reconciliation** cases in one
annual block per utility, so the plan cases are:

| plan year | Consumers Energy | DTE Electric | filed |
|---|---|---|---|
| 2023 | **U-21257** | **U-21259** | 2022-09-30 |
| 2024 | **U-21423** | **U-21425** | 2023-09-29 |
| 2025 | **U-21592** | **U-21594** | 2024-09-30 |

Every application is `Public__c = true`, `Confidential__c` unset, and filed
**before** its plan year. Access route, for the next session that needs it: the
E-Dockets portal is a Salesforce Experience Cloud SPA (HTML is a 13,995-byte
shell — the eLibrary failure mode), **but its guest Aura endpoint answers**
(`aura://RecordUiController/ACTION$getRecordWithFields`,
`aura://RelatedListUiController/ACTION$getRelatedListRecords` over
`Case` → `Filings__r`), `robots.txt` is `Allow: /`, `/s/sitemap.xml` enumerates
**167,735 filings across 5,931 cases**, and documents download directly from
`/sfc/servlet.shepherd/version/download/<ContentVersionId>`. **Unlike FERC
eLibrary, this docket is machine-readable from a standard session.**

---

## 3. Leg B, measured — the six exhibits, and what is not in them

| utility | PY | exhibit | columns | plant col? |
|---|---|---|---|---|
| DTE | 2023 | **A-15** *Long-Term Coal Contracts* | Contract Number · **Tonnage (000's)** · Cents/Mbtu · Begin · End · Fuel Type | **NO** |
| DTE | 2024 | A-15 | same | **NO** |
| DTE | 2025 | A-15 | same | **NO** |
| Consumers | 2023 | **A-22 (AKR-1)** *Coal Contract & Purchase Data* | Supplier Contract No · Coal Type · Contract Execution Date · Contract Start Date · Contract End Date · **Volume (Tons)** · Price ($/Ton) | **NO** |
| Consumers | 2024 | A-24 (AKR-1) | same | **NO** |
| Consumers | 2025 | A-22 (AKR-1) | same | **NO** |

**This is verified, not asserted.** `--verify-source` re-fetches all six from
the live public docket, re-derives every column header from the PDF text, and
reports **`all_columns_confirmed` true 6/6** and — the decisive check —
**`plant_word_on_page` FALSE 6/6**. The word *plant* does not appear on any of
the six exhibit pages.

**The quantities are real and internally consistent** (which is what licenses
quoting them). DTE plan-year **minimum contracted tonnage**: **6,015 / 6,165 /
4,818** thousand tons for 2023 / 2024 / 2025. Consumers **committed** tonnage,
independently reconstructed two ways — summing the per-contract rows, and
subtracting the exhibit's own *uncommitted* line from its plan-year total —
agreeing to ±1 ton: **4,019,216 / 2,710,680 / 156,000** tons.

**What the tonnage cannot be attached to.** DTE burns coal at **Monroe *and*
Belle River** in all three years (Exhibit A-11, 15,043–15,545 GWh Monroe against
5,125–5,277 GWh Belle River), so its single contract total spans two plants —
and only **Monroe (EIA 1733)** is in the 39-plant target set, so even isolating
the target-set share would need apportionment. Consumers burns at **J H Campbell
*and* D E Karn** in 2023, and at Campbell alone from 2024.

---

## 4. The pre-registered trap fired, exactly as written

PREREG §2 G-1-A and K7 named, in advance, the failure mode that would look like
success: *"a public **projected burn** at plant grain, which looks like the datum
and fails A on kind."*

It is there. Consumers' **Exhibit A-17/A-16 (KCL-1) *Projected As-Burned Coal
Costs*** is plant grain and denominated in tons —
`JHCampbell 1-2 2,118,878 / JHCampbell 3 (CE Owned Portion) 3,055,291 /
DEKarn 1-2 659,385` for 2023 — and DTE's **A-11 *Forecast of Plant Generation***
is plant grain in GWh. Both are **projections of burn produced by the utility's
own planning model**, which ask §3(c) closes **on principle, not availability**.
Had the trap not been pre-registered, this exhibit is what a session under
pressure would have reached for: it is public, plant-grain, in tons, and in the
same filing as the contract table.

**The two halves never meet.** Ex-ante exists without plant grain; plant grain
exists without ex-ante-ness. The only bridge is delivered tons — the forbidden
series (miso-103 §2, ask §2B). **So this is an identification gap, not a
retrieval gap**, and no further searching of the Michigan record closes it.

---

## 5. The §2B single-destination-plant carve-out, measured rather than waved away

Ask §3(a) blocker 1 admits contract-grain data **"only for contracts with a
single destination plant"** — a utility-year whose coal fleet is one plant needs
no apportionment. Read from the filings' own exhibits:

| utility-year | coal plants burning | 1:1? |
|---|---|---|
| Consumers 2023 | J H Campbell, D E Karn | no |
| **Consumers 2024** | **J H Campbell only** (Karn 1-2 burn = 0 t) | **YES** |
| **Consumers 2025** | **J H Campbell only** | **YES** |
| DTE 2023 / 2024 / 2025 | Monroe, Belle River | no |

So a leg-B-clearing sub-population **does exist** — and it is **one plant, in
two of three years**:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| target-set total (Mt) | 93.99 | 80.67 | 89.52 |
| Michigan (2 plants) | 9.94 (**10.6 %**) | 10.19 (**12.6 %**) | 11.44 (**12.8 %**) |
| **leg-B-clearing plants** | **0** | **1** | **1** |
| leg-B-clearing tonnage | 0.0 % | **4.6 %** | **4.9 %** |

Against §2C's ≥ 15 plants and ≥ 60 %. **The thresholds were not softened and are
not close** — 1 plant against 15, 4.9 % against 60 %, and **zero coverage in
2023**, which alone forecloses the rule-16 all-years bundle the constraint would
have to feed.

---

## 6. Descriptive, UNGATED — and a confound that would have produced a false finding

The ask's §4.2 **symmetry clause** anticipates a source that clears provenance
but shows minimums are **not binding**. Only one comparison in this record is
even single-basis (Consumers 2024/2025, Campbell on both sides):

| | committed tons (ex ante) | Campbell actual receipts | ratio |
|---|---:|---:|---:|
| 2024 | 2,710,680 | 3,725,361 | 0.73 |
| 2025 | **156,000** | 4,366,958 | **0.04** |

**That 0.04 is NOT evidence that Michigan coal minimums are slack, and quoting it
as such would be a mistake.** Consumers' 2025 plan was filed on the premise that
**Campbell Units 1–3 retire 2025-05-31**, per the June 23 2022 order approving
the settlement in IRP case **U-21090** — stated four times in the filing. The
plant did not retire. So the 156,000 tons is a **planned-retirement** artifact,
and the same premise deflates the plan's projected burn (2,122,443 t) to roughly
half of realised receipts. The 2023 row is separately confounded: the contract
side spans Campbell **+ Karn** while the receipts side is Campbell only — a
**basis crossing**, the miso-133 lesson.

**No verdict is taken from any of this.** It is banked, with its confounds
named, for whoever next meets the symmetry clause. It is recorded here
specifically because a session that measured the ratio without reading the
retirement premise would have reported "MISO coal minimums are not binding" —
a false closure of the whole minimum-take hypothesis, on n = 1.

---

## 7. What this does to the Form 580 lane — a prior update, not a verdict

Ask §3(b) held that Michigan, *"combined with a Form 580 pull, is the
second-largest block of addressable tonnage."* **That premise is now false, and
it fails in a specific way worth carrying forward.**

* Michigan **cannot compose** with a Form 580 pull, because its tonnage cannot
  be attached to plants **at all** — there is nothing to add.
* Michigan is strictly **worse than Form 580 on leg B**: Form 580's Q6b carries a
  **Destination Plant** on the delivery rows, where the Michigan exhibits carry
  no plant anywhere.
* For **DTE specifically the PSCR route is DOMINATED**: DTE is a Form 580 filer
  (it filed a partial-waiver request for the 2024 form on 2024-10-31, 90 FR 7691),
  so the same contracts would reach Form 580 *with* a destination plant. The PSCR
  route adds nothing DTE's Form 580 filing would not already carry.
* For **Consumers** the PSCR route is the only route, and it delivers **one plant
  in two years**.

**The §8 Form 580 count therefore remains the decisive next step, unchanged and
undischarged.** What Michigan does add is a *prior*: fuel-cost-recovery filings
publish at the grain the **filer's purpose** requires — portfolio cost recovery —
so contract-grain-without-plant should be expected as the norm, and Form 580's
blocker 1 (what share of tonnage sits in **1:1** contracts) is the right thing to
count. Rule 25 in spirit: this is evidence for how to *read* the Form 580 count,
and it transfers **no verdict** onto it.

---

## 8. The generalisable lesson — **GRAIN IS A PROPERTY OF THE PUBLICATION'S PURPOSE**

Five MISO lanes died because the object was not there. miso-134 was different —
the object was real and the lever still refused. **This one is different again:
the datum is real, public, ex-ante, and even carries the exact name of the
quantity we need — and it is still the wrong source.**

> **A source can publish exactly the right quantity and still be inadmissible,
> because the grain it is published at is set by the FILER's purpose, not by the
> quantity's nature.** A PSCR exhibit exists to recover a **portfolio** fuel cost,
> so it publishes **portfolio** tonnage. Our constraint is **per-plant**. No
> amount of searching harder finds plant grain in a document class whose purpose
> never required it — **so check the publication's purpose before budgeting the
> search**, and check whether the bridge from the source's grain to the model's
> grain is the forbidden series. Here it is.

This is miso-134's category error one level up. There, the measured value was not
the measurand of the slot; here, the measured value **is** the right measurand
and is not at the slot's **grain** — and the fix in both cases is barred for the
same reason: the only thing that would close it is the answer key.

The family: miso-129 *a signature is not a cause* → miso-131 *a plant-grain
signature is not a class-grain defect* → miso-132(a) *a missing rule is not a
binding one* → miso-133 *measure the slack, on one basis* → miso-134 *binding is
not licensing* → **miso-135 *the right quantity at the wrong grain is the wrong
source***.

---

## 9. Consequences for the queue

1. **THE MICHIGAN PSCR LEAD IS SPENT AND CLOSED ON KIND. DO NOT RE-DERIVE IT.**
   Specifically do **not** re-open it by (a) re-reading the PSCR plan cases for a
   plant column — six exhibits across two utilities and three years were fetched
   and their headers machine-verified, and there is none; (b) reaching for the
   *Projected As-Burned Coal Costs* / *Forecast of Plant Generation* exhibits,
   which are modelled burn and closed on principle at ask §3(c); (c) apportioning
   a contract total across Monroe/Belle River or Campbell/Karn by delivered tons,
   which is §2B-disqualifying; or (d) proposing the Consumers 2024–25 Campbell
   sub-population as a partial build — it is 1 plant, 0 in 2023, and cannot feed
   a rule-16 all-years bundle.
2. **The PSCR *reconciliation* cases are NOT a residual lead.** They report
   against the plan **ex post**; a reconciliation tonnage is a delivery, which is
   the miso-103 answer key. Do not open them.
3. **What would be needed instead**, stated so the next session does not re-derive
   the requirement: a source that attaches contracted tonnage to a **named plant
   by the document**. Three candidates in order of cost — (i) the **§8 Form 580
   count**, still the decisive step, still environment-blocked on eLibrary and
   calendar-blocked until the 2026 form lands **2026-10-30**; (ii) **MPSC
   discovery responses**, which this session confirms are docketed and public in
   these very cases (e.g. `U21257-ST-CE-0019`–`0032`, `U21592-AB-CE-0033`) — a
   discovery answer *could* carry plant-level contract detail, but nothing
   establishes that one does, and this session neither surveyed them nor assumes
   they do; (iii) an owner-authorized human/eLibrary retrieval.
4. **The ask §3(b) text is now stale** and should be read against §7 above: the
   "second-largest addressable block" premise is falsified, and the Michigan row
   should be marked SPENT rather than "not yet checked".
5. **C7-2025 stays where miso-103 left it** — failing and unledgered, with the
   coal offer-LEVEL route still data-blocked and the miso-89/90 Jun/Jul-2025
   under-derate still instrument-blocked. Nothing here licenses a substitute C7
   mechanism (ask §6).
6. **The miso-134 DO-NOT list carries forward intact and is extended by §9.1.**

---

## 10. Secondary item — a RECORD REPAIR, minting no verdict (PREREG §6)

miso-134 §9.5 flagged that `measured_offer_surface`'s `cells` string reads
`KKRUGI` (MISO = **`U`**) while its own `note` prose said *"MISO cell R inherits
only the MISO-specific refusal of SOM deep-discount premise (MISO-53)"*.

**Resolved from the evidence record, in the direction the record actually
supports: the `cells` string is CORRECT and the prose was a MIS-CITATION.**
MISO-53 adjudicated the **coal deep-discount premise**, and its evidence entry
already lives on the **`coal_passthrough_sigmoids`** row (`ev.M = "MISO-53"`) —
a different mechanism. The `measured_offer_surface` row's own `ev` block carries
**no `M` entry at all**, so no MISO evidence was ever cited on it. MISO is `U` by
**absence of a testable input** — it has no DAM submitted-curve corpus at the
grain this family needs (miso-134 §9.3) — not `R` by refusal.

**No cell changed, no verdict minted, no other ISO touched**; the note now states
the repair and its ground. `scripts/check_mechanism_matrix.py`: **integrity OK,
0 errors**, warning count unchanged from base (229, pre-existing anchor drift).

---

## 11. Rule duties

* **Rule 15** — **no LP was solved, so no run exists to register** (the
  miso-131/132(a)/133/134 no-LP precedent). Keeper unchanged; dashboard untouched.
* **Rule 28(b)** — matrix touched **only** for the §10 record repair; **no cell
  verdict minted** by this session, because no mechanism was tested. §5.4 queue
  stamp written this session.
* **Rule 22** — 2023–2025 only. Documents covering later *plan* horizons
  (five-year forecasts) were read for structure; **no out-of-training quantity was
  extracted, tabulated or gated on.**
* **Rules 13/19/21/24/25** — nothing sized on any residual, no parameter derived,
  no artifact re-derived, no tuning channel created, no other ISO's cell touched.
* **Ask §5 posture preserved** — assessment, not intake: nothing written under
  `data/raw/`, no rule-22 intake authorization requested or claimed, every
  document re-fetchable from the ContentVersion ids recorded in the probe.
