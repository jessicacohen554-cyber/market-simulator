# nyiso-126 — the eastern seam is NO LONGER DATA-BLOCKED, and C3a's residual is two offsetting defects, not one

**Session:** nyiso-126 (successor to nyiso-125). **Keeper unchanged:**
`2026-08-04-nyiso-125-seam-envelope`. **No solve ran. No mechanism was armed, no
parameter moved, no bundle was produced, nothing was registered.** Everything
below is a Phase-0 identification result plus a scorer-side decomposition on
**committed artifacts only**.

---

## §0 — verification at this session's own head

| check | result |
|---|---|
| NYISO keeper shard | `2026-08-04-nyiso-125-seam-envelope` |
| nyiso-125 commit on `main` | **yes** — `956d612b` (PR #3542), contained in `origin/main` |
| `calibration_verdict.py --run-id 2026-08-04-nyiso-125-seam-envelope` | determination **NOT-YET**; sole FAIL `price_mean`; C3a **+7.7 / −0.8 / −10.2 %**; C3c **CAVEAT (ledgered)**, model **18 / 2 / 21 h** vs actual **10 / 12 / 42 h** |
| `audit_keepers.py --iso NYISO` | **PASS, 0 failures / 0 warnings** |
| holdout | NYISO holds `complete` (validation tier only), **absent from `final`**; the **spend freeze is ACTIVE** and outranks both. Nothing out-of-training was solved, scored, read or registered. All work is 2023–2025 or year-independent. |

---

## §1 — ITEM 1: the identifying source exists. The lane is data-blocked no longer.

nyiso-125 refused the eastern half of the seam envelope because **no source
separates `SCH - PJ - NY` into its Zone-A (west) and Zone-G (east) legs** —
neither NYISO's P-32 nor PJM's tie file, which buckets all four NYISO-facing ties
as one `NYIS` row. It named the only admissible way out: *"a PAR-level or
facility-level posting, an OASIS path-level series"*.

**That posting exists, it is NYISO's own, it is live today, and it does not
merely split the row two ways — it splits it three ways.**

### 1.1 The source

**NYISO, "NY-NJ PAR Interchange Percentages, Operational Base Flow (OBF), and
other MW Offsets"**
`https://www.nyiso.com/documents/20142/2268509/NY-NJ_PAR_Interchange_and_OBF.pdf`
(fetched 2026-08-04, HTTP 200, 56,087 bytes; percentages **effective 5/1/2017**,
OBF **reduced to 0 MW under all conditions effective 11/1/2019** — so OBF is
identically zero across 2023–2025 and adds no term).

It states, verbatim, *"the percentage of PJM-AC Interchange that is directed over
the NY-NJ PARs in the Day-Ahead and Real-Time Market models"*:

| interface | PARs | share each | interface total | NY-side terminal | **NYISO zone** | **model zone** |
|---|---|---|---|---|---|---|
| Hopatcong–Ramapo (5018) | 3500 RAMAPO, 4500 RAMAPO | 16 % | **32 %** | Ramapo 345 kV | **G** | `Capital_Hudson` |
| JK | E / F / O WALDWICK | 5 % | **15 %** | South Mahwah (Con Ed) | **G** | `Capital_Hudson` |
| ABC | A GOETHSLN, B & C FARRAGUT | 7 % | **21 %** | Goethals, Farragut | **J** | **`NYC`** |
| — residual | free-flowing western AC ties | — | **32 %** | Homer City–Stolle Rd, Falconer | **A** | `Upstate_West` |

and the closure rule that makes it exhaustive: *"If a PAR is out of service,
interchange normally distributed over that PAR will be modeled over the
free-flowing western AC tie lines between NYISO and PJM."* The four shares sum to
**100 %**.

### 1.2 Why this is an identification and not a chosen number

nyiso-125 refused because any eastern envelope required picking a value inside a
**45–955 / 0–916 / 0–1,134 MW** bracket. This posting supplies **no MW at all** —
it supplies **percentages published by NYISO**, applied to a series already
intaken (`SCH - PJ - NY`, `data/raw/NYISO/interface-flows/`). There is no free
parameter, no swept value, and no band. It is the same class of object as the
armed downstate envelope: an attribution identity, not a fitted quantity.

### 1.3 Zone landings, cited — not assumed

* **Ramapo → Zone G.** NYISO 2025 Gold Book, Table IV-1b p. 127: queue entry
  C24-089, *"Ramapo 345kV Substation"*, **ZONE G**.
* **JK → Zone G.** NYISO Operating Study Winter 2023-2024 p. 9: *"the South
  Mahwah – Waldwick circuits from Consolidated Edison to PSE&G, controlled by the
  PARs at Waldwick"* — the NY terminal is Con Ed's South Mahwah (Rockland), Zone G.
* **ABC → Zone J.** Same study p. 9: the ABC PARs control *"the Hudson – Farragut
  and Linden – Goethals interconnections"* — Farragut (Brooklyn) and Goethals
  (Staten Island) are both Zone J. Corroborated by P-33, which monitors
  `GOETHALS 230 LINDEN 230 1` (PTID 25017) as a NYISO limiting facility.
* **Western ties → Zone A.** Gold Book Table IV-1b p. 129: Falconer, Dunkirk and
  South Ripley entries all carry **ZONE A**.
* **Tariff basis.** Operating Study p. 18: *"the Waldwick E, F, O and Goethals A
  paths are expected to deliver a percentage of the scheduled interchange as
  referenced in the NYISO-PJM JOA."*

### 1.4 A second, corroborating source, and its history

**NYISO MIS P-34 `ParFlows`** — 5-minute measured flow per PAR by PTID,
`http://mis.nyiso.com/public/csv/ParFlows/<yyyymm01>ParFlows_csv.zip`. Monthly
archives verified present and non-empty for **all of 2023–2025** (36 zips, 87 MB,
all HTTP 200; 64 distinct PTIDs). Its companion P-53A `parSchedule` carries the
same PTID namespace but retains only a ~10-day rolling window (a 2023 date
returns 404), so **`ParFlows` is the historical series and `parSchedule` is not**.

### 1.5 REPORTED AGAINST INTEREST — what the measured data does *not* confirm

`scripts/probes/_nyiso126_par_identification.py` regresses every PAR PTID's
measured hourly flow on the measured `SCH - PJ - NY` schedule, keyed by local
wall-clock on both sides.

* The **one** unambiguous signature is the identical pair **25370 / 25371** —
  byte-identical flows, slope **0.131 / 0.145 / 0.135** each, r **0.74–0.78** (the
  highest in the set), mean **+278 / +283 / +312 MW**. That is the Ramapo
  3500/4500 pair at a published 16 % each, and the pairing is exact.
* But **the published percentages do NOT reproduce as measured-flow slopes in
  aggregate**: the summed |slope| over all PTIDs with |r| > 0.30 is **0.45 / 0.12 /
  0.20**, against a published PAR-directed total of **0.68**. No clean 5 %-triple
  or 7 %-triple emerges.

**This is not a falsification of the posting, and it must not be read as one.**
The posting governs how the *scheduled* interchange is **modeled** to distribute;
`ParFlows` meters *actual* flow, which also carries loop and parallel flow and the
PARs' own control action. The two are different quantities. But it does mean the
percentages are a **market-model scheduling convention, not a metered flow share**,
and any construction built on them must say so in those words.

There is a further complication the same sources expose, and it is the reason a
flat 47 / 21 / 32 split would be **wrong** in our own years: Operating Study p. 18
records that for Winter 2023-2024 *"the Marion-Farragut 345 kV B and C cables are
expected to remain open"* — i.e. two of the three ABC PARs were **out**, so their
7 % + 7 % reverted west under the posting's own outage rule. **The split is a
function of PAR availability, not a constant.** `ParFlows` is exactly what
observes that availability.

### 1.6 An unlooked-for structural finding

**21 % of the PJM AC interchange is scheduled into Zone J, and the model has no
path for it.** `IMPORT_NODE_LINKS["NYISO"]`'s `NYC` link is HTP + Linden VFT only
(the two HVDC/VFT merchant wires); the ABC AC ties into Goethals and Farragut are
absent from the model's NYC border entirely, and `SCH - PJ - NY` is today
attributed wholly to `Upstate_West` + `Capital_Hudson`. This is independent of the
envelope question and was not previously on the record.

### 1.7 Verdict on ITEM 1

**The refusal that nyiso-125 recorded is discharged on identification.** What is
*not* discharged is authorisation: the successor charter conditions this lane on
*"explicit owner-authorised intake"*, and the construction now visibly needs the
`ParFlows` series (for PAR availability), not just the eight published
percentages. **Nothing was intaken.** The 87 MB of `ParFlows` used for §1.5 lives
in the session scratchpad, was used only to test the posting, and is not written
to `data/raw/`. The pre-registration is
`results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`;
arming it is the owner's call.

---

## §2 — ITEM 2: C3a's residual decomposed. It is two offsetting defects.

`scripts/probes/_nyiso126_c3a_decomposition.py`, on the committed keeper bundle's
`hourly/system_<year>.parquet` and the committed actual hourly RT series. The
scorer's `rt_lw` basis is **reconstructed and validated first** — reconstructed
actual vs committed bench: **−0.77 % / −0.36 % / −0.23 %** — so every level below
is on the scorer's basis and no other. (Five NYISO price bases exist; none are
blended here.)

### 2.1 The headline

**C3a-2025's −10.2 % is not a level error.** It is the net of two structurally
distinct errors of opposite sign, both present in **all three years**:

| year | C3a | contribution of bottom 80 % of hours | contribution of top 20 % | **decile 10 alone** |
|---|---|---|---|---|
| 2023 | **+7.7 %** | **+$5.51/MWh** | −$2.76 | −$2.95 |
| 2024 | **−0.8 %** | +$3.79 | −$4.05 | −$3.59 |
| 2025 | **−10.2 %** | +$4.39 | **−$10.99** | **−$9.35** |

Mean error within each half:

| year | bottom 80 % (7,008 h) | top 20 % (1,752 h) | decile 10: model vs actual |
|---|---|---|---|
| 2023 | **over** by **+$7.18** | under by −$11.92 | $49.78 vs $74.45 |
| 2024 | over by +$4.92 | under by −$17.61 | $65.21 vs $95.84 |
| 2025 | over by +$5.71 | under by **−$47.49** | **$108.69 vs $187.98** |

**The bulk over-pricing is roughly constant across years (+$3.79 to +$5.51/MWh of
contribution). Only the top-decile miss moves — −$2.95 → −$3.59 → −$9.35. C3a's
year-to-year sign is set entirely by that one term.** Against a 2025 net residual
of $6.79/MWh (66.53 × 10.2 %), decile 10 alone is **138 % of it**.

### 2.2 Where it sits in the day and the year

* **Hour-of-day (2025):** h16 / h17 / h18 carry **25.0 % / 24.6 % / 21.0 %** of the
  signed residual — **70.6 % in three hours**; h14–h19 is **84.4 %**. Hours 0–4 and
  21–23 run the *other* way (the model is over).
* **Month (2025):** Jun 34.5 %, Jan 29.0 %, Feb 26.5 %, Jul 21.3 % — four months are
  **111 %** of the residual; the other eight net negative.
* **The same shape holds in 2023 and 2024.** In 2024 the h16–h18 block is
  **+541 %** of that year's (near-zero) net residual — the arithmetic signature of
  a year that nets out.

### 2.3 The consequence, stated plainly

1. **2024's C3a "PASS" (−0.8 %) is cancellation, not agreement.** Its two halves
   are +$3.79 and −$4.05/MWh. Reading it as a fit is a mistake; it is the same
   two defects, sized to offset.
2. **No level lever can close C3a-2025.** Anything that lifts the level worsens a
   bottom-80 % over-pricing that is already +$4–7/MWh in every year.
3. **C3a-2025 and C3c are one defect measured twice, not two.** Decile 10 in 2025
   begins at an actual **$113.6/MWh** and is 138 % of the net residual; C3c gates
   the >$300 tail inside that same decile. This is consistent with — and now
   quantifies — nyiso-109's compression finding, and with nyiso-120's measurement
   that ~94 % of the gap was pre-existing and nyiso-125's that the seam repair
   does not touch it.
4. **The model has essentially no zonal price separation in 2025**: `NYC` $58.65,
   `Upstate_West` $58.65, `Lower_Hudson` $59.25, `Capital_Hudson` $59.52,
   `Long_Island` $65.94. Real NYISO carries a large downstate premium. §1.6's
   missing 21 % AC path into Zone J is a *candidate* cause and is pre-registered as
   a falsifiable prediction — **it is a hypothesis, not a result.**

---

## §3 — ITEM 3: surfaced to the owner, NOT edited

The C3c ledger text is stale in two independent ways. **Its correction is an
owner disposition and this session did not touch it** (the text lives in
`scripts/gen_nyiso125_attestation.py`; editing only the emitted JSON is reverted
by the next generator run).

**(a) Its stated re-open condition is falsified as written.** The ledger says the
re-open route is *"a `Capital_Hudson` → Zone-F/Zone-G TOPOLOGY SPLIT"*. nyiso-124
closed that with cause (G0, CLOSED). Citation:
`docs/handoffs/nyiso-124-charter-g0-g1-2026-08-04.md`; probe
`scripts/probes/_nyiso124_charter_g0_g1.py`; already flagged-not-edited at
`docs/codebase-site/data/mechanism-matrix.js:1258-1264` and in
`docs/calibration-log/nyiso.md` §(6).

**(b) Its premise is partly falsified.** The ledger classifies C3c as *"structural
— five-zone representation **cannot** form the sub-zonal NYC/LI load-pocket
scarcity"*. nyiso-125 moved the tail **3/0/14 h → 18/2/21 h** with a **seam-side
input correction carrying no scarcity parameter** — no ORDC change, no floor, no
reserve mechanism. Citation:
`results/calibration/FINDING-nyiso125-seam-envelope-2026-08-04.md` §5.5, which
states the finding and explicitly declines to act on it.

**This session adds a third item to that disposition.** §2.3(3) shows C3a-2025
and C3c are the same object. The ledger currently carries C3c as a *supporting*
criterion caveat while C3a is the *load-bearing* FAIL — but if they are one
defect, that split understates what is carried. Whether the ledger should say so
is likewise the owner's call, not this lane's.

---

## §4 — governance

* **Rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`.** §1 is an identification, not a
  fit; §1.5 reports the measured evidence that *weakens* it, in the same section
  that presents it.
* **Rule 13 `[R-MEASURED]`.** The §1 construction would enter as a formulaic input
  regenerable for a forward year (published percentages × forward PAR
  availability), never as an outcome pinned to a residual. It is pre-registered,
  not armed.
* **Rule 16 / rule 12.** No solve ran, so neither binds; §2 covers all three years
  from one committed bundle.
* **Rule 15.** **No run was produced** — no keeper, no probe bundle, no rejected
  arm — so there is nothing to register on the backcast dashboard. The keeper is
  unchanged and its dashboard entry is untouched.
* **Rule 22.** No promotion, so D-5(b) does not fire. No out-of-training year was
  solved, scored, read or registered; the spend freeze was checked first and is
  active.
* **Rule 24 / rule 20.** No `ScenarioConfig` field added, no parameter moved, no
  DOF entry created. The pre-registration lists what *would* be added, with its
  identification source, if the owner authorises.
* **Rule 28.** No mechanism was tested, so no verdict letter changes. The
  `seam_flow_envelopes` NYISO cell keeps its nyiso-125 `K`; a citation is added
  recording that the eastern half's **data-blocked** status is superseded by an
  identified source and now waits on authorisation, so the next session does not
  re-derive a refusal that no longer holds.
* **No tuning.** No band widened, no percentile swept, nothing scoped to a year or
  zone in response to any score.

---

## §5 — reproduce

```
uv run python scripts/probes/_nyiso126_c3a_decomposition.py
uv run python scripts/probes/_nyiso126_par_identification.py   # needs the ParFlows
                                                               # zips fetched to the
                                                               # scratchpad; see §1.4
uv run python scripts/calibration_verdict.py --run-id 2026-08-04-nyiso-125-seam-envelope --json
uv run python scripts/audit_keepers.py --iso NYISO
```
