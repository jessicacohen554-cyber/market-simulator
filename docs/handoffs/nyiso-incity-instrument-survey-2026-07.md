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
