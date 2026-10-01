# NYISO in-city (Zone J / K) instrument survey — charter §3 answered (nyiso-82 session)

**Date:** 2026-07-26 · **Charter:** `docs/handoffs/nyiso-incity-mustrun-charter-2026-07.md` §3
("Step 1 of this lane is a search, not a build") · **Method:** primary-source web survey
(NYSRC, NYISO, Potomac SOM, FERC/SEC corroboration); no code written, no data intaken,
no solve run. **Status: SEARCH DONE.** Outcome below; the charter's §3 gate stays CLOSED
for mechanism work pending the one owner decision and one retrieval thread recorded here.

## 0. Bottom line

**No freely-published, current instrument states a minimum in-city (Zone J) generation or
units-in-service OPERATING requirement in hour-resolvable form.** The quantitative
pocket-level obligations that drive the real-world out-of-merit steam dispatch live in Con
Edison operating procedures whose parameters are not public — the NYISO market monitor
itself reports it cannot see them (41–42 % of NYC reliability commitments "unverified"
because "the local transmission owner may have operational requirements that are not known
by the MMU or NYISO", 2024 SOM p.57). For Zone J the charter's **documented-NO branch is
the supported outcome**, unless the owner reopens one adjacent lever (§2 below). For Zone K
**one live thread remains** before the same NO is recorded (§3).

## 1. What the candidates returned (rule-13 verdicts)

| candidate | what it actually states | shape | rule-13 verdict |
|---|---|---|---|
| NYSRC Reliability Rules **Section G** (RRC Manual **V48**, final 2026-07-17, nysrc.org; historical I-R numbering in v33 2014) | G.1 R2: NYC unit commitment "based on second contingency operation…" — **no MW, no %, no unit count**; parameters delegated to unpublished TO procedures (Con Ed SO3-18 family). G.2/G.3 loss-of-gas → Minimum Oil Burn (fuel obligation, not min-gen) | qualitative | **N/A — nothing to intake** |
| G.1 **R3** NYC 10-min reserve | NYC 10-min reserve = NYCA 10-min reserve × (NYC peak / NYCA peak), held on in-city resources "at all levels of dispatch" | formula, hourly-resolvable | **PASSES** — but a *reserve* quantity (see §2) |
| The "80 % in-city" family | Zone J **LCR** 80.0→80.4 % (Gold Book 2024 Table V-3); Zone K 93–107 % | peak installed-capacity ratio | **FAILS** — the charter's already-documented misalignment (same shape as `nyiso.csv` on disk) |
| **ARR table** ("Applications of Reliability Rules") | Last publicly-verifiable vintage (Manual 12 v2.1, 2008, ERCOT-hosted mirror) contains true units-in-service rules — **ARR 22 (LIPA, Zone K): "commitment of any two (of four) Northport units" at peak AND light load, "up to two Port Jefferson units" at peak**; ConEd rule 2 (PSC Order 27302): 10-min reserve on in-city steam + fast-start GTs | units-in-service, condition-on-load (hour-resolvable) | **PASSES in form; BLOCKED on access** — current table is behind MyNYISO login; the 2008 copy is not intake-eligible as current truth (rule 14) |
| Gold Book / RNA / CRP / STAR | planning capacity numbers only (e.g. NYC transmission-security margin deficient ≤446 MW, 2025–2034 CRP) | peak-condition planning MW | **FAILS** (wrong shape) |
| **NYISO Locational Reserve Requirements sheet** (nyiso.com, tariff-anchored) | NYC 10-min **625** / 30-min **1,250** MW (→0 in Thunderstorm Alert); LI 10-min **120**, 30-min **270 off-peak → 540 on-peak**; SENY 30-min **by hour-beginning 1,300/1,550/1,800/1,550/1,300** | published, quantitative, per-hour, diurnal | **PASSES** rule 13 outright — but reserve-shaped, and vintage must be pinned (Potomac 2024/2025 SOM model NYC as 500/1,000 with $25 curves) |
| SRE / DARU / RMR record | Only MMU aggregates: NYC reliability commitments 2,359 GWh/238 days (2024), 1,533 GWh/121 days (2025); **LI +68 % in 2025, 47 % of all NYISO reliability commitments, majority large steam committed 73 days for high-voltage light-load** | observed outcome | **FAILS as obligation source** — the exact back-derivation the charter forbids; admissible ONLY as attestation corroboration of shape/level |
| Deactivation-retention determinations (Gowanus 2&3 / Narrows 1&2 retained → May 2029) | unit-specific availability windows | availability, not min-gen | PASSES as a fleet-availability input, but wrong class (peaker GTs) — cannot close the ST_GAS gap |

Corroboration worth keeping: the MMU's observed NYC OOM commitment magnitude is the same
order as the model's ST_GAS gap, and the 2025 LI steam OOM growth (light-load VOLTAGE
driven — commitment for overvoltage control, not energy) matches the 2025 gap growth. And
NYISO's own published fix — explicit NYC/LI load-pocket reserve requirements (MMU
recommendation 2024-1) — is deferred behind the Dynamic Reserves project (~2028 deploy):
the instrument this lane wants is expected to exist eventually, but does not today.

## 2a. ADJUDICATED 2026-07-26 (owner) — §2 = YES, §3 = documented-NO

**§2 (the reserve lever): YES, full J/K reopen.** The owner ruled that the
closed C3a "reserve" lever — closed as a *pricing* lever, on the measured
`energy_reserve_coopt=false` → **Δ$0.00** 2023 off-peak A/B (nyiso-71) — does
**not** extend to a commitment-obligation reading, which addresses a different
phenomenon (ST_GAS volume/C1–C7, not the energy trough). Mechanism built this
session: `nyiso_li_locational_reserve` + `nyiso_incity_commitment_obligation`
(both default-off, byte-inert), commit `fa9fc78`.

**Two survey questions closed on primary sources, not assumption:**

- **The vintage pin is resolved from evidence already on disk — and needs no
  change.** `data/raw/NYISO-AS/requirements/nyiso_locational_reserve_requirements.csv`
  carries three dated versions of the posting (two Wayback + one 2026 retrieval).
  The **v2021 regime spans all of 2023–2025**, and in it NYC is **500 / 1,000** —
  i.e. the "SOM-modeled" values already in `NYISO_RCPF_LOCATIONAL` *are* the
  published values for the training window. The 625/1,250 raise appears only
  between 2026-02-14 and 2026-07-10 and is a forecast-year event. **No NYC
  requirement changes.**
- **What was actually missing is Zone K, entirely.** `NYISO_RCPF_LOCATIONAL`
  stops at NYC, and the measured as-enforced #1344 intake has **no LI region**
  either — so a *published* locational requirement (LI 10-min 120; 30-min
  270→540) was represented nowhere in the model. That reframes the LI half from
  "new mechanism" to a **rule-14 [R-ACCURATE] omission**.
- **The LI on/off-peak boundary — the intake README's `DATA NEEDED` — is
  closed.** It is not defined in the LRR posting or the Ancillary Services
  Manual, but it is defined in the tariff itself: **MST §2.15 Definitions-O**
  (effective 10/31/2025, Docket ER26-1265-000) — *"On-Peak: The hours between 7
  a.m. and 11 p.m. inclusive, prevailing Eastern Time, Monday through Friday,
  except for NERC-defined holidays"*, Off-Peak its complement. A published
  **calendar** rule ⇒ regenerates for any forward year ⇒ rule-13 admissible.
  Implemented as `nerc_holidays` / `nyiso_onpeak_mask`.
- **LI demand-curve values** come from **Ancillary Services Manual §6.8** items
  **10** and **15**: "Long Island 10-Minute Reserves … shall be **$25/MW**" and
  the same for the 30-minute product — the same $25/MW locational tier the
  published NYC products carry.

**§3 (Zone K / the ARR table): documented-NO, retrieval attempted and
exhausted.** Owner authorized a bounded public attempt. Result:

1. The current **Manual 12 no longer contains the table.** Its revision log
   records "Table B.1, B.2, B.3, B.4, and B.5 — replaced with links to the
   external locations", and Table B.5 is now a one-line pointer: *"The current
   version of the ARR Table is posted at: https://www.nyiso.com/reports-information"*.
2. That page's ARR section resolves to a **login wall** — its literal text is
   *"Log into MyNYISO to view the Application of Reliability Rules"*, linking
   `nyiso.com/login`.

So the ARR-22-type units-in-service instrument for Long Island (2008 vintage:
"any two of four Northport units" at peak *and* light load) is **not publicly
obtainable**, and the 2008 copy is not intake-eligible as current truth (rule
14). **The Zone-K documented-NO is recorded.** The LI half of this lane
therefore rests on the published *reserve ladder*, not on a units-in-service
rule. Consequence for the mechanism: the eligibility restriction to in-city
steam is grounded on the **physics of a 10-minute product in a load pocket** (a
steam boiler carrying 10-minute reserve is necessarily synchronised), with the
Con Edison local rule cited as *corroboration only* — this is written into the
code comment so no later session mistakes the walled document for the basis.

*(Sources retrieved in-session: NYISO Transmission & Dispatch Operations Manual
(171 pp) Table B.5 + revision log; nyiso.com/reports-information ARR section;
NYISO Ancillary Services Manual (142 pp) §6.8; NYISO MST full tariff (1,079 pp)
§2.15. PDFs reviewed in the session scratchpad — none is a dataset intake.)*

## 2. The one owner decision this survey tees up

The only instrument passing rule 13 outright is the **locational reserve requirement
ladder** (NYC 625/1,250; LI 120, 270→540 diurnal; SENY diurnal). The charter lists
"reserve" among the **closed NYISO C3a levers** — but it was closed as a *pricing* lever.
The candidate mechanism here is different in kind: reserve-carrying as a **commitment
obligation** on in-city/LI steam (the published requirement held on ONLINE in-zone units
forces the steam fleet up — ConEd local rule 2's "10-min reserve on in-city steam units"
is literally this), i.e. the `nyiso_synchronised_reserve` path-A family generalized from
NYC-spinning to the J/K ladders, superseding the NYC/LI ST_GAS floor limbs per the
charter's rule-19 substitution requirement. **Whether the closed-lever ruling extends to
this commitment-shaped reopening is an owner adjudication — do not build without it.**

## 3. The one live retrieval thread (Zone K)

The current **ARR table** posted on nyiso.com/reports-information is login-walled
(MyNYISO). The 2008 vintage proves the genre carries exactly the needed form for Long
Island (2-of-4 Northport at peak and light load). A bounded retrieval attempt (owner may
simply have or request access) is the last step before recording the Zone-K NO. If
retrieved and current, ARR-22-type entries pass rule 13 (published requirement + fleet
composition; condition-on-load → hour-resolvable; responds to retirements via re-study).

## 4. Source record

RRC Manual V48 (2026-07-17) and v33 (2014); NYISO Manual 12 v10.0 + v2.1-2008 mirror
(ERCOT-hosted); Gold Book 2024 (Table V-3); 2025–2034 CRP; NYISO Locational Reserve
Requirements sheet; Potomac 2024 SOM (Table 4, p.57, p.xv) + 2025 SOM (pp.62–65, Table 8);
NYISO Gowanus/Narrows press release + AlphaGen withdrawal (retention → May 2029). Full
URLs in the survey transcript; PDFs were reviewed in-session (session scratchpad, not
committed — none is a dataset intake).
