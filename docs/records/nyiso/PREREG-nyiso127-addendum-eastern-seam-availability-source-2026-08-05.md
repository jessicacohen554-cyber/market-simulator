# PREREG ADDENDUM nyiso-127 — the eastern-seam availability source changes from P-34 `ParFlows` to P-33 `outSched`, and the split is NOT what nyiso-126 predicted

**Filed BEFORE any solve.** No LP has run in this session. Everything below is
Phase-0 identification on published NYISO postings. It amends
`results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`,
which the owner authorised for execution on 2026-08-05 ("Authorise intake +
execute"). **The parent pre-registration's §6 predictions, §7 kill gates and §8
decision rule are NOT rewritten** — §6-P2 is *reported as weakened by
measurement* below, exactly as §8-3 requires an adverse case to be reported
rather than repaired.

---

## §1 — why an addendum at all

The parent PREREG §3 identifies PAR in-service state as *"measured — P-34
`ParFlows`, per PAR per hour"*, and §4 conditions the lane on intaking ~87 MB of
`ParFlows` for that purpose. Executing it exposed a gap the parent did not
anticipate:

**`ParFlows` carries no PAR identity.** Its schema is
`"Timestamp","Point ID","Flow (MWH)"` — a bare numeric PTID and nothing else. The
posting that supplies the eight percentages names its PARs by *name*
(`RAMAPO PAR3500`, `WALDWICK E2257`, `GOETHSLN BK_1N`, `FARRAGUT TR11`, …), not
by PTID. Nothing in the parent PREREG bridges the two, and the only bridge on the
record was nyiso-126 §1.5's **inference from measured behaviour** — the
25370/25371 pair identified as Ramapo because their flows are byte-identical and
their regression slopes land near the published 16 %.

**A behavioural inference is not a published identity, and §3's kill condition is
explicit**: every entry must be *"a published constant or a measured state"*, and
*"if implementation requires any value that is not one of those two things, this
pre-registration is violated and the lane stops"*. Assigning a PTID to a PAR
because its slope looks right is neither. Under the parent PREREG as written,
**this lane would have had to stop here.**

## §2 — the source that closes it, and it closes both halves at once

**NYISO MIS P-33 `outSched` (Scheduled Outages)**,
`http://mis.nyiso.com/public/csv/outSched/<yyyymm01>outSched_csv.zip`. Schema:
`Timestamp, PTID, Equipment Name, Scheduled Out Date/Time, Scheduled In
Date/Time`. All 36 monthly archives for 2023-2025 fetched HTTP 200
(3.2 MB total, 161,692 rows, 2,355 distinct PTIDs).

It supplies **both** things the construction needs, from one published NYISO
posting:

1. **The PTID ↔ PAR-name crosswalk** (`Equipment Name`), and
2. **The in-service state itself** (`Scheduled Out` / `Scheduled In`), as
   published outage windows rather than as a flow-derived inference.

**All eight PARs in the posting resolve by exact name match. Zero freedom, zero
residual choice:**

| posting PAR | posting Description | `outSched` Equipment Name | PTID | interface | share |
|---|---|---|---|---|---|
| 3500 | `RAMAPO PAR3500` | `RAMAPO___345_345_PAR3500` | 25370 | Hopatcong–Ramapo | 16 % |
| 4500 | `RAMAPO PAR4500` | `RAMAPO___345_345_PAR4500` | 25371 | Hopatcong–Ramapo | 16 % |
| E | `WALDWICK E2257` | `P_HAWTHO-WALDWICK_230_E-2257` | 101017299 | JK | 5 % |
| F | `WALDWICK F2258` | `WALDWICK-HILLSDAL_230_F2258` | 101016633 | JK | 5 % |
| O | `WALDWICK O2267` | `WALDWICK-FAIRLAWN_230_O2267` | 101016389 | JK | 5 % |
| A | `GOETHSLN BK_1N` | `GOETHALS_345A_345B_BK 1N` | 25641 | ABC | 7 % |
| B | `FARRAGUT TR11` | `FARRAGUT_345B_345A_TR11` | 25044 | ABC | 7 % |
| C | `FARRAGUT TR12` | `FARRAGUT_345C_345A_TR12` | 25043 | ABC | 7 % |

**The change is a strict improvement in identification, not a convenience.** It
replaces an inferred identity and an inferred availability with two published
ones. `ParFlows` is still intaken under the owner's authorisation, but its role
changes from *the availability source* to *an independent corroborating
measurement* — which is the role in which it is strongest.

## §3 — the corroboration, run before anything was wired

If `outSched` says a PAR is out, its measured `ParFlows` flow must be zero.
2023-01, 8,992 five-minute intervals per PTID:

| PTID | PAR | `outSched` state | measured mean | measured \|max\| | intervals with \|flow\| > 0.5 MW |
|---|---|---|---:|---:|---:|
| 25370 | Ramapo 3500 | in service | +311.16 | 563.6 | **100.0 %** |
| 25371 | Ramapo 4500 | in service | +311.17 | 563.6 | **100.0 %** |
| 25641 | ABC-A Goethals | in service | −205.46 | 572.9 | 99.9 % |
| 25044 | ABC-B Farragut TR11 | **OUT** | **0.00** | **0.0** | **0.0 %** |
| 25043 | ABC-C Farragut TR12 | **OUT** | **0.00** | **0.0** | **0.0 %** |

Exact agreement, both directions. The two independent postings identify the same
eight facilities and the same states.

## §4 — THE RESULT THAT MATTERS, AND IT IS ADVERSE TO nyiso-126's HYPOTHESIS

**The ABC-B and ABC-C PARs (Farragut TR11 and TR12) have been out of service
since 2018-01-15 and are out for 100 % of every hour of 2023, 2024 and 2025.**
Their `Scheduled In` date is a rolling extension (2023-01-31 → 2023-02-28 → … →
2026-02-01), the published signature of a long-term outage, and it matches the
Operating Study's note that *"the Marion-Farragut 345 kV B and C cables are
expected to remain open"*.

Under the posting's own closure rule — *"if a PAR is out of service, interchange
normally distributed over that PAR will be modeled over the free-flowing western
AC tie lines"* — **14 of the 21 ABC points revert west for the entire training
window.** The measured, availability-conditioned split:

| year | `Capital_Hudson` (Zone G) | `NYC` (Zone J) | `Upstate_West` (Zone A) |
|---|---:|---:|---:|
| 2023 | 45.7 % (range 42–47 %) | **7.0 %** (0–7 %) | 47.3 % |
| 2024 | 46.8 % (15–47 %) | **6.8 %** (0–7 %) | 46.4 % |
| 2025 | 46.4 % (15–47 %) | **6.8 %** (0–7 %) | 46.8 % |
| *the flat split the parent PREREG pre-emptively refused* | *47 %* | *21 %* | *32 %* |

**Two consequences, both stated before the solve:**

1. **The parent PREREG's pre-emptive refusal of a flat 47/21/32 was correct, and
   for a bigger reason than it knew.** It expected availability-conditioning to
   move ~14 points in one winter; measured, it moves ~14 points in **every hour
   of all three years**, and the residual western share is **47 %, not 32 %**.
2. **nyiso-126 §1.6's structural hypothesis is falsified in large part.** It
   recorded — explicitly as a hypothesis, not a result — that *"21 % of the PJM
   AC interchange is scheduled into Zone J and the model has no path for it"*,
   and named it a candidate cause of the model's total absence of a downstate
   price premium. The true figure is **~7 %**, one third of that, because two of
   the three ABC PARs have been out since 2018. **§6-P2 of the parent PREREG
   ("routing 21 % of the AC interchange to Zone J … should widen that spread") is
   therefore weakened by a factor of three before the arm is even built.** It is
   recorded here as weakened, not rewritten to match, and P2 will be scored
   against its original text.

## §5 — what changes in the DOF ledger, and what does not

**`n_residual` must still stay at 6** — unchanged from the parent §3, and still
the kill condition.

| entry | value | identification source | swept? |
|---|---|---|---|
| `nyiso_par_share_ramapo` | 0.32 | NY-NJ PAR posting, table 1 (2 × 16 %) | never |
| `nyiso_par_share_jk` | 0.15 | same (3 × 5 %) | never |
| `nyiso_par_share_abc` | 0.21 | same (3 × 7 %) | never |
| `nyiso_par_share_west` | 0.32 | same, residual by the posting's closure rule | never |
| PAR in-service state | measured | **P-33 `outSched` windows per PAR per hour** (was: P-34 `ParFlows`) | never |
| PAR ↔ PTID identity | published | **P-33 `outSched` `Equipment Name`** (NEW — the parent PREREG had no entry for this and needed one) | never |

The four shares are unchanged published constants. The fifth entry changes
source. The sixth is **new and was previously implicit** — the parent PREREG
assumed the PTID identity was free, and it was not.

## §6 — kill gates: unchanged, plus one discharged early

The parent §7 gates K1–K7 stand as written and will be scored as written.

**K7 is DISCHARGED IN ADVANCE and passes.** Its text: *"if the ABC share does not
measurably fall in the window the Operating Study records Farragut B/C as open,
the availability read is wrong ⇒ stop."* Measured: the ABC share falls from 21 %
to 7 % in that window **and in every other hour of the training period**, and the
fall is corroborated by exactly-zero measured flow (§3). The gate is satisfied
more strongly than it anticipated.

**K1 (no free parameter) is re-affirmed against this addendum**: every value in
§5 is a published constant, a published state, or a published identity. Nothing
is chosen inside a bracket and nothing is swept.

## §7 — what this addendum does NOT do

* It does **not** rewrite §6's predictions. P2 is reported as weakened; P1 and P3
  are untouched. P3's honest clause stands unchanged: **this does not predict
  C3a-2025 closes.**
* It does **not** relax the §8 decision rule or its named adverse case
  (C3a-2023 crossing +10 %).
* It does **not** re-open any DO-NOT-REDO cell, propose a lever, or add a queue
  entry.
* It does **not** touch the holdout instruments. 2023-2025 only.
