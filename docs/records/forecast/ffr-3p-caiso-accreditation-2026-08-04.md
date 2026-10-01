# FFR-3P — Adjudicating CAISO's 6,577 MW base-year accreditation deficit, and verifying the NQC credit against CAISO's own ledger

**Session.** FFR Wave 3, the CAISO accreditation lane. Branch
`claude/caiso-accreditation-ledger-a9xb12`, based on `origin/main` **`90037bf5`**.

**Diagnosis and identification. Nothing is tuned, promoted, re-banded or armed. No solve was
run and no default moved.**

> **⚠ RULE 19 [R-ONE-MECH] — READ THIS FIRST.** A **parallel session on the same FFR-3P
> charter** (branch `claude/caiso-accreditation-ledger-lim6v5`, PR **#3450**, commit
> **`7a0999b8`**) landed the CAISO NQC VRE accreditation mechanism on `main` while this
> session was running. **This session built the same mechanism independently and has
> DELETED it rather than ship a second one.** The incumbent
> (`caiso_nqc_accreditation` → `RENEWABLE_NQC_CURVES_BY_ISO`) stands unchanged; §3 below
> records the head-to-head and **why the incumbent's construction is the better one on the
> evidence**, which is the useful residue of the duplication. What this session contributes
> that main does not have is **§1–§2 and §4: the adjudication of the base-year deficit
> against CAISO's own published ledger** — scope item 1, which the incumbent commit does not
> address and for which no handoff document existed.

**One-line result.** Adjudicated against **CAISO's own published resource ledger**, all
three of FFR-3H's candidate conservatisms are wrong — two refuted outright, the third real
but small — and the dominant cause is a fourth thing nobody had named:

> **The model's CAISO base-year battery fleet is 8,000 MW where CAISO's own February-2026
> NQC list carries 14,131 MW NDC / 13,365 MW NQC of battery alone.** That single line is
> **≈5,933 MW** — **90 % of the 6,577 MW headline deficit** and **51 % of the total
> accredited-supply gap**. It is a base-fleet **vintage** problem: not accreditation, not
> the requirement.

**Answer to scope item 1, stated plainly: BOTH, but not in the proportions anyone expected.**
The accredited ledger is **11,711 MW** below CAISO's own published NQC; the requirement is
**2,030 MW** too high. **Supply is 85 % of the error.**

---

## 0. State re-verified at this HEAD

| item | packet said | **verified this session** |
|---|---|---|
| `origin/main` | `bc9e6dbf` | **`90037bf5`** (main advanced ~45 commits during the session) |
| CAISO keeper | `2026-08-04-caiso164-zonal-loss-surface` | **confirmed** — read from `frontend/data/backcast/keepers/CAISO.json` |
| `complete` markers | {NEISO, NYISO, PJM} | **unchanged, unspent** |
| `final` markers | EMPTY | **unchanged** |
| holdout spend freeze | ACTIVE | **unchanged; neither spent nor worked around** |

**No year was solved at all**, in or out of training. The entire adjudication is
**solve-free** — exactly as FFR-3H §5 item 3 predicted it could be: arithmetic over the
model's own loaded inputs and CAISO's own published tables. Prerequisites ran as briefed
(`uv sync` ≈2 min, then `scripts/regenerate_clean.py`); the `tzdata` trap did not arise on
the `uv` path.

**Two owner decisions (G.5, D-9) untouched. FH-4/FH-5 stay blocked. D-1/D-2 stay armed. The
D-8 mechanisms stay default-off.**

---

## 1. The instrument this session adds: CAISO's own published ledger

Every prior attempt on this deficit reasoned outward from the model. This session reads
**CAISO's own answer to the same question** and differences it. Three primary sources, all
retrieved 2026-08-04:

1. **CAISO, *2026 Summer Loads and Resources Assessment* (May 2026)** —
   `https://www.caiso.com/documents/2026-summer-loads-and-resources-assessment-technical-appendix.pdf`.
   **Table 1.1**, "Existing resources by fuel type and deliverability status", September NQC
   against Net Dependable Capacity, from the March-2026 NQC list. *This is the table the
   whole adjudication turns on and it had never been read into this program.*
2. **CAISO, *Net Qualifying Capacity Report for Compliance Year 2026*** — already committed
   on main at `data/raw/capacity-market/nqc/caiso/net-qualifying-capacity-report-cy2026.xlsx`
   by the parallel session.
3. **CPUC, *2026 Resource Adequacy and Slice of Day Guide*** (78 pp) — the counting
   methodology and the current PRM.

### 1.1 CAISO's Table 1.1 (Total column), and the model beside it

| class | CAISO NDC | **CAISO NQC** | implied credit | **model firm MW** | **model − CAISO** |
|---|--:|--:|--:|--:|--:|
| Natural Gas | 26,958 | 25,866 | 0.960 | | |
| Nuclear | 2,300 | 2,280 | 0.991 | | |
| Geothermal | 1,354 | 1,208 | 0.892 | | |
| Biomass / Biogas / Distillate / Waste Heat | 821 | 625 | | | |
| **thermal subtotal** | **31,433** | **29,979** | **0.954** | **30,221.4** | **+242.4** |
| Hydro | 9,076 | 6,295 | 0.694 | 4,624.8 | **−1,670.2** |
| Solar | 20,459 | 6,503 | 0.318 | 3,960.0 | **−2,543.0** |
| Wind | 6,330 | 1,401 | 0.221 | 1,120.0 | **−281.0** |
| Battery | 14,131 | 13,365 | 0.946 | 7,431.8 *(all storage, incl. PS)* | **−5,933.2** |
| Hybrid | 2,043 | 1,484 | 0.726 | 0.0 | **−1,484.0** |
| Other | 451 | 42 | | 0.0 | −42.0 |
| **TOTAL (internal)** | **83,922** | **59,069** | | **47,358.0** | **−11,711.0** |

Model figures are FFR-3H §1.3's base-year ledger (reproduced there at the recorded cache key
`e5822277b72184f6`); the model's internal total is its 50,729 MW less the 3,371 MW
firm-import credit, which Table 1.1 excludes by construction ("excludes tie-generators").
The class gaps sum to −11,710.8 against the −11,711.0 total — the arithmetic closes.

**Reserve position, each ledger on its own basis:**

```
model  : 50,729 / 57,306 = 0.8852     (FFR-3H's figure, reproduced exactly)
CAISO  : 59,069 / 55,276 = 1.0686     (and Table 1.1 excludes RA imports AND demand
                                       response, both of which add further supply)
```

**The model's CAISO is 11.5 % short where the real CAISO is at least 6.9 % long.** That is
what this lane was missing, and it is not subtle.

---

## 2. FFR-3H's three candidates, adjudicated

### 2.1 Candidate 1 — hydro's non-dispatchable class factor: **REFUTED**

FFR-3H nominated the 0.7041 non-dispatchable factor applied to the whole hydro fleet, worth
up to 1,943.6 MW. **The class factor is not the problem — it is 1.1 pp GENEROUS.**

```
model  : 4,624.8 / 6,568.4 nameplate = 0.7041   (FFR-1C, CY2025 NQC tech factor)
CAISO  : 6,295   / 9,076   NDC       = 0.6936   (CY2026 Table 1.1, September)
```

The model's *rate* already sits above CAISO's own realized fleet-wide rate. What is short is
the **fleet**: 6,568.4 MW modelled against 9,076 MW of CAISO NDC, a 2,508 MW coverage gap
arising in `modelled_hydro_nameplate_mw`'s EIA-923 filters (positive nameplate **and**
positive reported energy in the final-release census). FFR-1C's F-4 "controllable /
run-of-river class split" is therefore **the wrong refinement to prioritise** — raising the
rate on a fleet that is 28 % too small cannot close this.

> **CAVEAT, stated because it is load-bearing and I could not resolve it.** Table 1.1 has no
> pumped-storage row and CAISO's §2.3 models "Hydro and Pumped Storage" together, so the
> 9,076 MW Hydro NDC **may** include CAISO's ~3.9 GW of pumped storage. If it does, the
> model's *conventional* hydro nameplate is not short at all and this line reverses sign.
> **The −1,670 MW hydro row is the one number in §1.1 I do not stand behind** without a
> pumped-storage split. Filed as B-2, not claimed.

**Recorded, not applied:** the CY2026 vintage of the same tab moves the non-dispatchable
hydro factor 0.7041 → **0.6999** (min over Jul/Aug/Sep of the published 2022–2024 average:
0.75725 / 0.746038 / 0.699889), i.e. **−27 MW**. A rule-23 source-vintage refresh that makes
the deficit slightly *worse*; routed to whoever owns `HYDRO_ACCREDITATION_CREDIT_BY_ISO`.

### 2.2 Candidate 2 — thermal UCAP against an NQC-basis PRM: **TEXTUALLY REAL, EMPIRICALLY REFUTED — and the estimate is KEPT**

The textual case is strong, and I confirmed it independently:

* CPUC, *2026 RA and Slice of Day Guide*: **"Dispatchable resources (including resources not
  explicitly discussed elsewhere) are assigned a single value based on Pmax."**
* A full-text search of the 78-page guide for **"EFOR" returns ZERO matches** — the same test
  R5b applied to the ISO-NE tariff before adopting `claimed_capability`.
* CAISO's own Summer Assessment: **"For dispatchable resources like battery and natural gas
  plants, the NQC value is typically near its NDC or installed capacity."**

So on its face CAISO belongs in `THERMAL_ACCREDITATION_BASIS_BY_ISO` on a
no-forced-outage-derate basis, and `1 − EFORd` double-counts against a PRM that already
covers forced outages. **Checked against CAISO's own numbers, it fails:**

```
model thermal : 30,221.4 MW firm on 31,957.2 nameplate  -> implied credit 0.9457
CAISO thermal : 29,979   MW NQC  on 31,433   NDC        -> published credit 0.9537
model - CAISO : +242.4 MW   (the model is already 0.8 % ABOVE CAISO's own number)

if switched to a Pmax / seasonal-rating basis (credit 1.00):
                31,957.2 vs 29,979 = +1,978 MW OVER-CREDIT
```

**"Near its NDC" is not "equal to its NDC."** CAISO's NQC is the Master-File capacity *after*
the Pmax test and the monthly ambient derates — CAISO devotes a whole figure (2.1) to
thermal ambient derates — so the published basis lands ~4.6 % below NDC, and the model's
`1 − EFORd` lands within 0.8 % of it.

**Rule 14 disposition, applied in the direction the rule actually points.** This is the
documented-misalignment exception in textbook form: the accurate-*sounding* literal input
(credit = 1.00 on Pmax) is defined on a **different capacity boundary** (Master-File
installed capacity, before test and ambient derate) than the model's nameplate, so using it
literally would make the ledger *less* reflective of reality by ~2 GW. The estimate is
**KEPT**, as a *reconciled* stand-in for the published quantity — 0.9457 against a published
0.9537 — with the misalignment documented here rather than buried. That is why this session
does **not** add CAISO to `THERMAL_ACCREDITATION_BASIS_BY_ISO`.

**FFR-3H's 1,735.8 MW figure for this candidate should not be carried forward.** It is the
size of the derate, not the size of the error; the error is +242 MW of the opposite sign.

### 2.3 Candidate 3 — demand response absent from the requirement: **CONFIRMED, small, unquantified**

CPUC counts DR as supply-side RA with its own hourly QC: *"The value of DR resources will
vary by hour based on the resource's capability on the worst day of the month under the
1-in-2 planning framework."* Table 1.1's footnote likewise excludes "participating loads and
any demand response resources", and the Summer Assessment carries a separate Table 2.4 of
monthly utility / third-party / non-CPUC DR capacity.

CAISO's absence from `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO` is therefore a **real
omission** — and, as for PJM and NEISO whose constructs also count DR as supply, closing it
needs the same **documented reconciliation** (a supply MW over the requirement it clears
against), never a raw fraction of peak. Table 2.4 did not survive text extraction, so **no
number is claimed**; FFR-3H's "~2 GW" is an estimate and should be labelled as one wherever
it is quoted.

### 2.4 The candidate none of them named — **base-year storage fleet currency: the dominant cause**

`STORAGE_BASE_FLEET_MW["CAISO"]["mid"] = 8,000.0` MW. CAISO's published February-2026 NQC
list carries **14,131 MW NDC / 13,365 MW NQC of battery**, before the further 1,354 MW of
battery CAISO expects online by June 30 2026 and before the 2,043 MW hybrid class. The
model's *entire* storage accreditation — batteries **and** pumped storage — is 7,431.8 MW.

```
model storage firm (batteries + PS)  :  7,431.8 MW
CAISO battery NQC alone              : 13,365   MW
shortfall                            : >= 5,933 MW  = 90 % of the 6,577 MW deficit
                                                    = 51 % of the 11,711 MW supply gap
```

The `≥` is not hedging: pumped storage sits *inside* the model's 7,431.8 MW and is
*excluded* from CAISO's battery row, so the battery-only shortfall is larger.

**This reframes FFR-3H §1.4.** "Storage adds ZERO MW in all five years, in the ISO whose
real-world adequacy answer is batteries" was filed as an unexplained anomaly with no
diagnostic instrument (its blocker B-4). It now has a companion reading needing no
instrument: **the model begins the horizon ~6 GW of accredited battery capacity below the
real CAISO and never builds any**, so step 6's 14,043.6 MW of administrative CTs is in large
part substituting for batteries that already physically exist. Whether storage *entry* is
also broken remains open — B-4 stands — but the **level** question is answered, and the
answer is fleet vintage.

**Not fixed here.** `STORAGE_BASE_FLEET_MW` is a scenario-path registry whose CAISO row feeds
the `low/mid/high` `storage_deployment` ladder; re-vintaging it is a data intake with its own
rule-23 citation and its own owner box — not something a diagnosis charter may move, and
emphatically not something to move *because* it closes a deficit. Filed as **B-1**.

---

## 3. Scope item 2 — the VRE identification, and the rule-19 reconciliation

### 3.1 What happened, and what was deleted

Two sessions were dispatched on this charter and both built the mechanism. The parallel
session's landed first (`7a0999b8`, PR #3450). **Rule 19 [R-ONE-MECH] permits exactly one
mechanism per phenomenon, so this session's duplicate was deleted in full** — its registry
(`RENEWABLE_NQC_EXCEEDANCE_CREDIT_BY_ISO`), its gate
(`renewable_nqc_exceedance_accreditation`), its resolver rung, its CLI flag, its parallel
raw intake into `capacity-market-elcc`, its derive and its tests. **Nothing of it is
proposed, and no part of it should be revived.** The incumbent stands unchanged:

```
caiso_nqc_accreditation : bool = False        # GATED, default OFF
RENEWABLE_NQC_CURVES_BY_ISO["CAISO"]          # solar 0.2096, wind 0.2202
cache_key(ScenarioConfig())            = 603c2498bf71d21d   (pinned literal, unmoved)
cache_key(...caiso_nqc_accreditation=True) = c644d2c7657492e0
```

### 3.2 The head-to-head, and why the incumbent is right

Both derivations read the **same** published quantity — the CY2026 "Tech Factors" tab's
peak-hour exceedance QC, per (technology, region, month), minimum over Jul/Aug/Sep — and both
reached it from the same reasoning (it is the tab FFR-1C already read the hydro factor from;
under Slice-of-Day, *"Wind and solar NQC is based on the peak hour exceedance value with the
single QC value being updated based on changing monthly peak hours every year"*). **They
differ only in the fleet mix used to blend the sub-class factors onto the model's one solar
and one wind class:**

| | **incumbent (main)** | this session (deleted) |
|---|---|---|
| mix source | the **same report's own NQC List** — resource class and Pmax recovered from the identity `NQC_r(m) = Pmax_r × factor(m)` by least squares, unmatched resources dropped | EIA-860 operable solar/wind, model-zone assigned, tracking flags |
| coverage | 12,470.4 MW / 200 solar; 6,211.3 MW / 97 wind | 24,919 MW solar; 6,344 MW wind |
| energy-only / partial-deliverability | **excluded** (a deliverability outcome, not an accreditation factor) | not distinguished |
| out-of-state wind | **excluded** (credited at the seam via `ADEQUACY_EXTERNAL_TIE_FIRM_MW`; rule 19) | excluded by zone assignment |
| **solar / wind** | **0.2096 / 0.2202** | 0.2181 / 0.2377 |
| on the 2026 pools | **+651 / +421 = +1,072 MW** | +837 / +544 = +1,381 MW |

**Verified against CAISO's Table 1.1, which neither derivation used, the incumbent is very
nearly exact and this session's is 1–2 pp high:**

| September basis | CAISO Table 1.1, full-capacity-deliverable | **incumbent** | this session |
|---|--:|--:|--:|
| solar | 4,611 / 11,612 = **0.3971** | **0.3942** *(−0.3 pp)* | 0.4086 *(+1.2 pp)* |
| wind | 1,344 / 6,068 = **0.2215** | **0.2202** *(−0.1 pp)* | 0.2377 *(+1.6 pp)* |

That is a genuine independent closure check, from a **second CAISO document**, of a
mechanism that had none: the incumbent's same-document construction reproduces CAISO's own
published ratios almost exactly, and its two exclusions (energy-only, out-of-state) are the
reason. **The duplication is waste; this verification is the one thing worth keeping from
it.**

### 3.3 Direction resolved — and it is the one FFR-3H warned against assuming

FFR-3H §4 item 3: *"CAISO's own slice-of-day accreditation for solar at ~22 GW penetration is
plausibly BELOW 0.18 … Anyone reading §1.3 as a list of understatements is over-reading it."*
That caution was right to state and is now **measured false in both classes**: the generic
non-CAISO fallback is too **stingy**, solar 0.18 → 0.2096 and wind 0.16 → 0.2202,
**+1,072 MW** on the model's 2026 pools — **16 % of the base-year deficit**, independently
derived twice.

The intuition pointing the other way — "CAISO solar is worthless at the evening net peak" —
is true of the *net*-peak slice and irrelevant here: the single QC value is an exceedance **at
the month's peak hour**, the same hour the model's `peak × (1 + PRM)` requirement is defined
on. The 24-slice evening constraint is a different test this ledger does not run (B-8).

**Why the min-over-Jul/Aug/Sep month choice is not merely cautious but necessary.** At the
September factor the model's solar would accredit 0.3942 × 22,000 = **8,672 MW**, well
*above* CAISO's published whole-fleet solar NQC of 6,503 MW — because CAISO gives zero NQC
to energy-only solar (2,424 MW NDC → 0) and truncates partial-deliverability solar
(3,127 → 703 MW), a haircut the model has no representation of. The adopted August value
lands at 4,611 MW, *below* CAISO's 6,503 MW. **The conservative construction is what keeps
the armed ledger from over-crediting a fleet the model treats as fully deliverable.**

### 3.4 Arming posture — unchanged, and a recommended ordering

The mechanism stays **GATED DEFAULT-OFF** and this session neither arms it nor recommends
arming it yet. Rule 14 prefers the published values on the merits and they are encoded; what
rule 14 does not decide is arming posture on a mechanism that changes forecast solve
behaviour (the ledger drives the retirement reliability floor, the reserve-margin backstop
and the CR-1 position). That is the owner's box, and owner decision D.1 (HOLD PROMOTION,
FIND ROOT CAUSE) stands. Backcast mode never runs capacity evolution, so no keeper is
reachable in either state.

**And the measurement argues for patience.** +1,072 MW is 16 % of the deficit; the storage
line is 90 %. Arming the VRE credit first would move CAISO's reserve position 0.8852 →
0.9039 and close about a sixth of the gap the backstop is grinding out — real, but it would
leave the backstop firing for the same reason **and remove a sixth of the signal from the
next diagnosis**. **Recommended ordering, offered and not taken: B-1 (storage vintage) first,
this second.**

---

## 4. Scope item 1's other half — the requirement IS on the wrong basis, in both directions

Two independent currency errors pulling opposite ways, both measured against CAISO's own
published inputs:

| term | model | **published** | effect on requirement |
|---|--:|--:|--:|
| peak load basis | 49,831 MW (own 8760, weather year 2024) | **46,844 MW** CEC 1-in-2 for 2026 | **+3,435 MW** too high |
| planning reserve margin | 0.15 (R.21-10-002) | **0.18** (D.25-06-048, CY2026 & CY2027) | **−1,405 MW** too low |
| DR netting | none | DR counted as supply | unquantified, requirement too high |
| **net** | **57,306 MW** | **55,276 MW** | **+2,030 MW too high** |

**The peak.** CPUC's System RA requirement is *"each LSE's CEC-adjusted forecast plus a
planning reserve margin"*, and CAISO's own assessment publishes the CEC ISO 1-in-2 peak
forecast as **46,844 MW in 2026, rising 8 % to 50,498 MW in 2030**. The model's own path is
49,831 → 54,821 MW: **+6.4 % in 2026, widening to +8.6 % by 2030**. So requirement and ledger
*are* on different bases — the requirement is built on a single simulated weather-year
realization while the PRM it multiplies is defined against a probabilistic 1-in-2 forecast.
This reproduces FF-2B's peak-currency item and **corrects its magnitude**: FF-2B/FFR-1C
quoted "~4.4 GW" against a "~46 GW" placeholder; on the published 46,844 MW it is
**3,435 MW**. Routed to the FF-1C demand lane, unchanged here.

**The PRM is stale, and rule 14 makes that a finding I keep rather than a fix I decline.**
The shipped 0.15 is the pre-Slice-of-Day value. For the model's own 2026 base year CPUC has
adopted **18 %** (D.25-06-048: *"For the 2026 and 2027 RA compliance years, an 18 % Planning
Reserve Margin (PRM) … was adopted"*). Substituting it **makes the model's deficit worse**,
6,577 → 8,071 MW — which under rules 1/14 is exactly why it must not be quietly left at 0.15
to flatter the ledger.

> **MISALIGNMENT CAVEAT, and why I did not change the constant.** The 18 % is calibrated
> **inside** the 24-slice framework (LSEs demonstrate load + PRM in *each of 24 hours*
> against a gross load profile), whereas the model applies its PRM once at the gross peak
> hour. These are not the same test, and dropping 0.18 into a single-hour test is not
> obviously "the current published number for this construction". The honest statement:
> **0.15 is certainly stale, 0.18 is the current published figure, and the conversion
> between the SOD PRM and a single-peak-hour PRM is an open question needing CPUC's PRM
> Calibration Tool, not a substitution.** Filed as **B-3**. `PLANNING_RESERVE_MARGIN_BY_ISO`
> is also the requirement side, which this charter does not own.

---

## 5. What this session does NOT claim

* **It does not claim the deficit is closed**, or that arming anything closes it. The VRE
  credit is 16 % of it; the dominant term is a fleet-vintage blocker this charter may not
  touch.
* **It does not claim the hydro row of §1.1.** The pumped-storage attribution in Table 1.1 is
  unresolved (B-2) and the row could reverse sign.
* **It does not claim a DR magnitude.** Table 2.4 exists and was not extracted.
* **It does not propose its own mechanism.** The duplicate was deleted; the incumbent stands.
* **It does not re-anchor CAISO's net-CONE and does not touch the entry screen.** FFR-3H's
  causes 1 and 2 belong to other lanes; the CPM soft-offer cap is current and correctly cited
  (FF-2C R4).
* **It does not change** `PLANNING_RESERVE_MARGIN_BY_ISO`, `HYDRO_ACCREDITATION_CREDIT_BY_ISO`,
  `THERMAL_ACCREDITATION_BASIS_BY_ISO`, `STORAGE_BASE_FLEET_MW` or
  `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`. Each is named, measured and routed.
* **It does not solve, score or register anything.** No holdout year was approached; the
  freeze and both markers are as found.
* **It does not re-score FC-2 row 4.** CAISO is FAIL before this document and FAIL after it.

---

## 6. Open blockers

* **B-1. `STORAGE_BASE_FLEET_MW["CAISO"]["mid"] = 8,000 MW against a published 14,131 MW NDC
  / 13,365 MW NQC battery fleet.** ≈5,933 MW — 90 % of the base-year deficit and the single
  largest term in the model's CAISO adequacy ledger. A data-intake lane with its own rule-23
  citation and owner box. **This should go first.**
* **B-2. CAISO Table 1.1's Hydro row may or may not include ~3.9 GW of pumped storage**, and
  the §1.1 hydro line reverses sign depending which. Needs a per-resource split; the CY2026
  NQC list carries no technology column, but the incumbent derive's
  `NQC = Pmax × factor` least-squares recovery is exactly the machinery that could do it.
* **B-3. CAISO's PRM is stale** (0.15 shipped; 18 % adopted for CY2026–27, D.25-06-048), and
  the SOD PRM is defined on a 24-slice test the model does not run. The substitution is not
  one-for-one; converting needs CPUC's PRM Calibration Tool.
* **B-4. The requirement's peak is a single simulated weather-year realization** (49,831 MW,
  wy 2024) against a PRM defined on the CEC 1-in-2 (46,844 MW). +3,435 MW of requirement in
  2026, widening to +8.6 % of peak by 2030. FF-1C demand lane; magnitude corrected here.
* **B-5. CAISO is absent from `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`** while CPUC counts
  DR as supply-side RA (FFR-3H's B-5; its VRE half is now closed on main). Needs the
  PJM/NEISO reconciliation treatment, never a raw fraction of peak.
* **B-6. The model has no hybrid (solar+storage) resource class**, while CAISO accredits
  2,043 MW NDC / 1,484 MW NQC of it as a distinct class with its own QC construction
  (renewable component + storage component, capped at the POI limit). Whether the model's
  solar and storage pools already carry those MW is **unverified**, so the −1,484 MW row in
  §1.1 may be partly double-counted — flagged, not claimed.
* **B-7. The model has no deliverability truncation on VRE accreditation.** CAISO gives zero
  NQC to energy-only solar (2,424 MW NDC) and haircuts partial-deliverability solar
  (3,127 → 703 MW); the model credits every pool MW at one rate. This is what
  `capacity_deliverability_limits` would own; it resolves **False** in the shipped forecast
  posture (FFR-3H §3.3).
* **B-8. The adequacy ledger is a single-peak-hour test; CPUC's is a 24-slice test.** The
  single QC value is the correct counterpart for a single-hour test, but nothing in the model
  reproduces SOD's binding evening slice. A structural limitation, recorded so nobody reads
  the armed ledger as "CAISO's RA construction, modelled".
* **B-9. PROCESS — two sessions were dispatched on one charter and both built the same
  mechanism.** ~300 lines of duplicate registry/gate/resolver/derive/tests were written and
  thrown away, and only a merge conflict revealed it. Whatever dispatches FFR lanes should
  check for an in-flight branch on the same charter id before opening a second.
* **Carried forward unchanged** from FFR-3H: its B-1 (CLAUDE.md step 6 "default off" is wrong
  for five of six ISOs), B-2 (FC-2 row 4 grain mismatch), B-3 (`trajectory["storage_mw"]`
  structurally 0.0), B-4 (no storage-entry diagnostic sink).

---

## 7. Mechanism matrix (rule 28)

No new row: the `caiso_nqc_accreditation` row landed with its mechanism at `7a0999b8` per
duty (c), CAISO cell **O**, and its verdict is unchanged by this session — still built,
default-off, **not adjudicated**. Per duty (b) its evidence citation is extended in this
session with the independent Table-1.1 verification (§3.2) and this document.
`scripts/check_mechanism_matrix.py` passes.

No run was registered (nothing was solved), so the duty-(b) registration half is moot.

---

### Reproduction

```bash
uv sync                                    # ~2 min
uv run python scripts/regenerate_clean.py  # ~63 min, 50/50 datatypes

# the incumbent identification, unchanged on main
uv run python scripts/data/derive_caiso_nqc_class_factors.py
uv run python -m pytest tests/unit/data/test_caiso_nqc_class_factors.py -q

# the published ledger this session differenced against
#   https://www.caiso.com/documents/2026-summer-loads-and-resources-assessment-technical-appendix.pdf   (Table 1.1)
#   https://www.caiso.com/documents/net-qualifying-capacity-report-for-compliance-year-2026.xlsx        (committed on main)
#   https://www.cpuc.ca.gov/-/media/cpuc-website/divisions/energy-division/documents/
#     resource-adequacy-homepage/resource-adequacy-compliance-materials/guides-and-resources/
#     2026-ra-slice-of-day-filing-guide.pdf

# to MEASURE the arm (owner box; not run here, and not recommended before B-1)
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ffr3p/caiso-control
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --caiso-nqc-accreditation --out-dir results/ffr3p/caiso-armed
```
