# PREREG nyiso-126 — eastern-seam attribution from NYISO's published NY-NJ PAR interchange percentages

**Status: PRE-REGISTERED AND NOT EXECUTED.** No solve ran in the session that
wrote this. It is filed **before** any result exists so that the decision rule,
the kill gates and the adverse case are on the record first, and so the owner can
authorise or refuse on a fixed construction rather than on a moving one.

**Blocking condition (owner):** the nyiso-125 successor charter conditions this
lane on *"explicit owner-authorised intake"*. §4 needs a series that is not yet in
`data/raw/`. **This does not proceed without that authorisation.** Identification
evidence: `results/calibration/FINDING-nyiso126-seam-identification-and-c3a-decomposition-2026-08-04.md` §1.

---

## §1 — the object

Replace the **unattributed** treatment of the measured `SCH - PJ - NY` schedule —
today wholly split between `Upstate_West` and `Capital_Hudson` by the model's own
static link ratings — with **NYISO's own published attribution** of that same
schedule across the zones its ties physically land in.

Source: NYISO, *"NY-NJ PAR Interchange Percentages, Operational Base Flow (OBF),
and other MW Offsets"*,
`https://www.nyiso.com/documents/20142/2268509/NY-NJ_PAR_Interchange_and_OBF.pdf`
(percentages effective 5/1/2017; OBF identically 0 MW since 11/1/2019).

| destination | published share | basis |
|---|---|---|
| `Capital_Hudson` (Zone G) | Ramapo 3500 + 4500 = **32 %**, JK E/F/O = **15 %** → **47 %** | posting, table 1 |
| `NYC` (Zone J) | ABC A/B/C = **21 %** | posting, table 1 |
| `Upstate_West` (Zone A) | residual free-flowing western AC ties = **32 %** | posting's own outage clause |

**Availability-conditioned, not flat.** The posting's closure rule — *"If a PAR is
out of service, interchange normally distributed over that PAR will be modeled
over the free-flowing western AC tie lines"* — is part of the identification, not
an embellishment. It **must** be implemented: NYISO's Operating Study Winter
2023-2024 p. 18 records the Farragut B and C cables **open** in one of our own
years, which moves 14 points from `NYC` to `Upstate_West`. A flat 47/21/32 is a
**known-wrong** simplification and is pre-emptively refused here.

PAR availability is read from **NYISO MIS P-34 `ParFlows`** (5-minute measured
flow per PAR PTID; 2023–2025 archives verified present).

---

## §2 — what makes this admissible, stated before the result

* **Zero free parameters.** Eight percentages, all published by NYISO; none
  swept, none fitted, none chosen inside a bracket. This is the exact distinction
  from nyiso-125's refusal, which would have required picking a value inside
  45–955 / 0–916 / 0–1,134 MW.
* **Rule 13 `[R-MEASURED]` forward test.** Regenerable for a forward year from
  forward drivers: the percentages are a standing tariff-referenced convention
  (NYISO-PJM JOA) and PAR availability is an outage input. It responds to changed
  conditions. It is an *input*, never an outcome fed back.
* **Rule 25 `[R-ISO-SCOPE]`.** NYISO-only, from NYISO's own posting. Nothing
  crosses an ISO boundary.
* **Honest limitation, on the record first.** These percentages govern how the
  *scheduled* interchange is **modeled** to distribute; they are **not** a metered
  flow share. FINDING §1.5 measures that the published shares do **not** reproduce
  as `ParFlows`-vs-`SCH - PJ - NY` regression slopes in aggregate (summed |slope|
  0.45 / 0.12 / 0.20 against a published 0.68). **If the owner regards a
  market-model scheduling convention as inadmissible as a physical attribution,
  this lane closes here, and that is a legitimate refusal.**

---

## §3 — the DOF ledger delta

| entry | value | identification source | swept? |
|---|---|---|---|
| `nyiso_par_share_ramapo` | 0.32 | NY-NJ PAR posting, table 1 (2 × 16 %) | never |
| `nyiso_par_share_jk` | 0.15 | same (3 × 5 %) | never |
| `nyiso_par_share_abc` | 0.21 | same (3 × 7 %) | never |
| `nyiso_par_share_west` | 0.32 | same, residual by the posting's closure rule | never |
| PAR in-service state | measured | P-34 `ParFlows`, per PAR per hour | never |

**`n_residual` must stay at 6.** Every entry above is a published constant or a
measured state. **If implementation requires any value that is not one of those
two things, this pre-registration is violated and the lane stops** — that is the
kill condition, not a thing to negotiate at the time.

Registry: all four shares enter `ScenarioConfig` (rule 24 `[R-REGISTRY]`) and
appear in `run_config.json`. Matrix row added in the same PR (rule 28 duty c).

---

## §4 — intake required (owner authorisation)

| series | what for | size | status |
|---|---|---|---|
| NYISO MIS P-34 `ParFlows`, 2023–2025 | PAR in-service state for the outage-reallocation rule | ~87 MB zipped, 5-min, 64 PTIDs → hourly curated | **NOT intaken.** Verified fetchable; used in-session only to test the posting, held in scratchpad, never written to `data/raw/` |

The eight percentages need no intake — they are cited constants.

---

## §5 — blast radius

* **In scope:** the zonal attribution of `SCH - PJ - NY` only; a new `NYC` AC
  border path that does not exist today (FINDING §1.6).
* **Untouched:** `NYISO_INTERFACE_TTC_BY_MONTH` / `_BY_YEAR` (Tier-3 re-grounding
  is REFUTED/CONFIRMED-closed, nyiso-122/124); nyiso-100's retired 4,350 MW
  `NYISO_simultaneous_import` scalar, **not** re-installed; the armed downstate
  `nyiso_seam_deliverability_envelope` (HTP/VFT/Neptune/CSC/1385), unchanged; every
  scarcity, ORDC, floor and reserve mechanism, unchanged — **this construction
  carries no scarcity parameter** (rule 19 `[R-ONE-MECH]`).
* **All three years in one invocation, one bundle** (rule 16), years sequential
  (rule 12), 2023–2025 only.

---

## §6 — the ex-ante prediction

Registered **before** solving, and falsifiable:

**P1.** `Capital_Hudson` — at its bound in ~100 % of hours in both nyiso-125 arms
and carrying ~1.5 GW of the misallocation — **stops being permanently bound**, and
Central-East utilisation moves further toward the measured 0.807 / 0.616 / 0.591
than nyiso-125's 0.668 / 0.335 / 0.383.

**P2.** Zonal price separation appears. FINDING §2.3(4) measures the 2025 model at
`NYC` $58.65 = `Upstate_West` $58.65 — no downstate premium at all. Routing 21 %
of the AC interchange to Zone J and 47 % east of Central-East should **widen** that
spread.

**P3 — the honest one.** **P2 predicts the downstate level moves; it does NOT
predict C3a-2025 closes.** FINDING §2 shows the −10.2 % is 138 % attributable to
decile 10, and nyiso-120 measured ~94 % of it as pre-existing. **If this arm
closes C3a-2025, that is a surprise to be explained, not a success to be
claimed** — the pre-registered expectation is that C3a-2025 moves **little**.

---

## §7 — kill gates

Any one firing **stops promotion**. Registered before the result.

* **K1 — no free parameter.** Any value not in §3 appears ⇒ **stop** (§3).
* **K2 — no new unserved energy.** Any hour of new slack/VOLL that the same-HEAD
  control does not have ⇒ stop.
* **K3 — C1 does not regress.** Fuel-mix free-class score must not fall below the
  control's 10/10.
* **K4 — live, not inert.** If max zonal |ΔLMP| < $1/MWh in every year, the arm is
  inert; it is **reported as inert and not armed** (rule 26 `[R-DELETE]` — no
  default-off parking).
* **K5 — the seam reconciliation band holds.** Net four-link seam p50 must stay
  inside the monthly EIA-930 reconciliation band. This construction **re-homes**
  interchange; it must not create or destroy any.
* **K6 — control reproduces.** The same-HEAD control must reproduce the nyiso-125
  keeper's C3a to ±0.2 pp, else the comparison is invalid and nothing is read.
* **K7 — the availability rule is real.** If the ABC share does not measurably
  fall in the window the Operating Study records Farragut B/C as open, the
  `ParFlows` availability read is wrong ⇒ stop.

---

## §8 — the decision rule, and the adverse case

**Promotion is on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]` grounds — the more
faithful attribution — and NEVER on a score.**

1. Any kill gate fires ⇒ **no promotion**, register the arm as a rejected probe
   (rule 15), update the matrix cell with the rejection (rule 28).
2. All gates silent and the arm is live ⇒ promote, **even if C3a or C3c is
   unchanged or modestly worse**, under the owner's standing disposition that
   structural gain may outweigh a gate regression.
3. **The adverse case, named now:** the most likely bad outcome is that routing
   47 % east **over**-relieves Central-East and pushes C3a-2023 (today +7.7 %,
   already the closest to a band edge) **through +10 %**, converting a PASS to a
   FAIL. **If that happens it is reported as a FAIL and the arm is not rescued by
   scoping the share to a year, a zone or a season.** Any such scoping is a
   fitted parameter and is refused in advance by §3.
4. A second adverse case: the arm closes C3a-2025 *and* worsens C3c. Per §6-P3
   that would contradict the pre-registered expectation, and it is to be
   **investigated, not banked**.

**No tuning under any branch.** No band widened, no share swept, no leg unarmed,
nothing scoped in response to a score.

---

## §9 — leave-one-year-out

A mechanism change gets leave-one-year-out within 2023–2025 before promotion
(rule 22). Because §1's shares are published constants and not fitted to any year,
LOYO here is a **consistency check** — the shares are identical whichever year is
held out, so a verdict that flips on which year is held out would indicate the
*availability read*, not the shares, is doing the work, and that is itself a stop.
