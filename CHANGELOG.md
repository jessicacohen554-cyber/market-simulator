# Changelog

## 2026-09-13 — SOCO W1 lands: the zonal-load spine fails its own gate, and a COD defect would have inverted the nuclear year

Desk refresh r#3 (`docs/handoffs/soco-desk-ledger-2026-09.md`). All three W1 lanes landed and graded
PASS by content. Docs only in this commit — the lanes' own data and findings are already on `main`
(PRs #6083, #6091, #6092). Seven owner cards ruled.

- **The FERC-714 zonal spine fails its reconciliation gate.** SOCO-11 measured the three chartered
  respondents at **73.2 %** of the BA's metered demand — short **61.4 / 66.2 / 64.2 TWh** in 2023/24/25,
  in *every hour of every year*, shape right (r ≈ 0.99) and level short, which is whole planning areas
  absent rather than a scaling error. **Nothing was rescaled and no share was derived** (rules 13/23):
  raw landed, failure documented, lane stopped. Adding Oglethorpe + MEAG + Southern Power closes it to
  **1.63 / 1.50 / −0.03 %**, and the PowerSouth + Tallahassee falsifier **overshoots** — so the
  enumeration discriminates on BA membership, not on whichever combination minimises the residual.
- **Card S3 ruled 3 zones on that six-respondent sum**, over the desk's own 1-zone recommendation. The
  desk's stated risk is controlled rather than dropped: new gate **G22** makes a cited BA-membership
  basis a hard precondition on SOCO-32, and new lane **SOCO-14** produces it — PUDL carries no county
  attribution for any of the three added respondents. Zones are named geographically, and the split is
  never sold as improving accuracy: with non-binding Tier-3 TTCs, 3-zone and 1-zone SOCO produce the
  same dispatch until a TTC binds, and SOCO has no zonal price or congestion archive to validate one.
- **A COD defect big enough to invert SOCO's headline year — new card S12, new lane SOCO-15.**
  `cod_ramp.effective_cod` always prefers a plant's capacity-weighted mean COD for the **online** date;
  the per-unit preference exists only for retirement. Measured by calling the live code,
  `load_cod_map()[649] -> (2005, 5)`, so **Vogtle 3 and 4 read as online all 12 months of 2023**.
  Phantom **+12.979 TWh** (+24.8 %): a 2023 SOCO backcast would show ≈65.41 TWh of nuclear, *above* the
  measured 2025 value of 64.17, inverting the observed 52.4 → 63.0 → 64.2 commissioning step and
  displacing ~13 TWh of gas. The defect is general — blast radius **SOCO 3,040.3 MW** vs SPP 1,127.4,
  ERCOT 1,091.4, CAISO 1,037.2, MISO 927.4, PJM 177.2, NYISO 72.9, NEISO 50.0 — so the repair is
  chartered as its own cross-ISO lane **before** SOCO-20, never inside a registration PR.
- **Gate G12 is MET**: LTLF edition `Budget 2025 (B2025) / 2025 IRP`, vintage 2025, 60 rows committed.
  The material qualification is stated rather than papered over — the forecast is **Georgia Power**, the
  `System` column is REDACTED throughout the public disclosure, and **Alabama Power files no public IRP
  because Alabama has no IRP statute**, so a SOCO-wide forward peak is a construction SOCO-20/32 must
  declare. Nothing is grossed up.
- **SEEM corrected on three counts, and the correction strengthens card S2 rather than reopening it.**
  Live **November 2022** (not 2023); SEEM itself publishes no price **but its Independent Market Auditor
  publishes a monthly series publicly back to 2022-11**; and a FERC-accepted settlement (2026-01-05) will
  oblige hourly posting prospectively. SOCO-12 then **refused its own find as a benchmark** on four
  disqualifying grounds — SEEM-wide not SOCO, monthly not hourly, 1.3 TWh against 239 TWh of demand, and
  the hourly posting not retroactive — and re-cast it as the *boundedness anchor* SOCO-13's STOP gate
  needs. SEEM's own FAQ routes price to "existing FERC reporting", corroborating the EQR route.
- **Also ruled:** S4 served EIA-930 interchange (the cleanest book in the corpus — zero NaN hours on nine
  DIBAs, legs agreeing with the BA book to 0.001 TWh); S5 a DOE/LBNL ICE VOLL, since Order 831's $2,000
  caps *offers* and SOCO takes none; S6 winter **26.0 %** as the PRM scalar, SOCO being winter-peaking in
  2 of 3 backcast years; S7 the CAES unit to a gas CT at its **25 MW rating**, not the 110 MW nameplate
  the charter carried; S11 the no-price determination class chartered as SOCO-22, keyed on the absence of
  an `actual_lmp.json` block so it serves the NWPP program too.
- **Other measured findings now on the record:** gate **G19 closed** (`America/Chicago`, DST-aware,
  hour-ending); the census corrected to **336 / 788 / 70,667.2 MW** with the Massachusetts row rejected as
  an EIA-860 BA-field mis-entry and the six Florida panhandle plants kept; the CEMS gap at **91.6 %** of
  fossil MW before SOCO-11's eight files landed; SOCO's **1,306.6 MW of pumped storage unobservable in
  EIA-930** for 2023 and most of 2024, a hard constraint on the C1 benchmark; and no wind anywhere in the
  fleet.
## 2026-09-13 — NWPP r#2: W1 issued, and two gates this program was chartered without

Desk refresh r#2 (`docs/handoffs/nwpp-desk-ledger-2026-09.md`). Docs only — no code, no data, no
registry; every existing keeper's cache key untouched by construction.

- **W1 ISSUED — all four lanes**, verbatim from the plan's prompt pack with §8.0 pasted in and
  `origin/main` pinned: **NWPP-10** (data audit + registry-values table + the TRE defect),
  **NWPP-11** (CAMPD ID/OR/UT/WA + the per-BA EIA-930 *derive* + interchange + monthly hydro),
  **NWPP-12** (WECC path ratings + WRAP + IRPs + NRC + fuel) — all `[OPUS]` — and **NWPP-13**
  `[FABLE]`, the STOP-gated WEIM price index, which ruling N2 unblocked.
- **NWPP-21 HELD, for a measured reason.** SOCO-21 was issued at the sibling desk's r#2 and has not
  landed: the matrix base file still carries seven `isos`, there is no `SOCO.js` shard, and
  `scripts/lib/mech_matrix.py` contains zero `SOCO` occurrences. Two lanes on one base file is the
  collision this register exists for.
- **A routed question answered instead of bounced.** NWPP-13's charter asked the desk whether
  `data/raw/caiso-weim/` would be swept into the CAISO profile. Measured against
  `configs/data-profiles.yaml`'s own substring rule: it would (`caiso-weim` contains `caiso`), while
  `nwpp-weim` resolves to `shared` today and moves into the `nwpp` profile automatically once
  NWPP-20 registers that token. The plan is corrected at all four places and the fixed text issued.
- **Gate G13 REWRITTEN.** As chartered it read *".gitignore the bundle family — never `rm`"*, which
  pre-orders the miso-255 incident: rule 34 `[R-SHARD-PROMOTABLE]` (a), corrected 2026-09-12 *after*
  this program was chartered, requires the **shard** to push its bundle. G13 now states the seam —
  `.gitignore` is the parent's tree; the shard appends a negation and uses a plain `git add`, never
  `git add -f`; the bundle must carry `dispatch/<year>_P1.parquet`; nothing is `rm`'d before the
  owner rules on promotion.
- **Gates G23 and G24 ADDED**, for rules 33 `[R-SHARD-ARCHIVE]` and 35 `[R-PROMOTE]`, neither of
  which had a gate in this plan. G24 is not housekeeping: `audit_keepers.py` E13 already fails at
  this pin for MISO (×4) and SPP (×1).
- **R-c re-measured and rewritten.** The feared divergence did not occur — SOCO's card S2 was ruled
  in substantially the same terms as NWPP's N2. The live risk moved to the implementation:
  `scripts/calibration_verdict.py` carries no branch that can express the ruled determination class,
  so neither program's first keeper can score until one exists. Routed to the SOCO desk's card S11,
  deliberately **not** carded here — one branch serves both programs.

## 2026-09-13 — SOCO r#2: the price card is ruled, and the plan is reconciled with rules 33/34/35

Desk refresh r#2 (`docs/handoffs/soco-desk-ledger-2026-09.md`). Docs only — no code, no data, no
registry; every existing keeper's cache key untouched by construction.

- **Card S1 RULED — the key is `SOCO`**, the EIA balancing-authority code already used as the on-disk
  filename convention. `ISO_EV_KEY["SOCO"] = "O"` and the shard `SOCO.js` follow from it.
- **Card S2 RULED — both limbs.** Southern publishes no LMP and SEEM publishes no price, while three
  rubric criteria score against an hourly price series. The owner ruled: build the FERC-EQR footprint
  index (lane SOCO-13) behind a STOP gate registered *before* any data is read, **and** rule the
  fallback now — with no price benchmark a SOCO run reads a determination naming its own basis
  (e.g. `PHYSICALLY CALIBRATED — price unscored, no public price exists`), scored on C1/C2/C4/C6/C8,
  **never `CALIBRATED`**, with the price gap on the determination basis at full magnitude. Gate G17
  is untouched: a neighbouring market's hub remains refused.
- **Card S11 raised.** The ruling authorizes the determination class; it does not write it, and
  `scripts/calibration_verdict.py` carries no branch that can express it — so W4 cannot score until
  someone is assigned. Served at sitting #3.
- **Lanes SOCO-13 `[FABLE]` and SOCO-21 `[OPUS]` issued**, verbatim from the plan's prompt pack.
  SOCO-21's gate-independence from registration was measured, not assumed: neither
  `scripts/lib/mech_matrix.py` nor `scripts/check_mechanism_matrix.py` validates the matrix ISO list
  against `SUPPORTED_ISOS`, and the shard-migration test's own comment records SPP's column being
  seeded before SPP's first keeper — an 8-ISO matrix over a 7-ISO registry is a supported
  intermediate state.
- **The plan is reconciled with three CLAUDE.md rules that landed after it was chartered.** Gate G13
  as written told W4 to `.gitignore` the bundle family, which is exactly what rule 34(a) — corrected
  2026-09-12 — calls *"a defect in the prompt"*: the **shard** pushes its bundle to its own branch via
  a `.gitignore` negation and a **plain `git add`, never `git add -f`**, including
  `dispatch/<year>_P1.parquet`; the `.gitignore` belongs to the parent's tree. G13 rewritten; **G20**
  added for rule 33 `[R-SHARD-ARCHIVE]` (archive on "the parent has it", verify retrievability with
  `git ls-tree` first, pin recovery to a full 40-char SHA, and the measured HTTP 403 on branch
  deletion); **G21** added for rule 35 `[R-PROMOTE]` (prune the outgoing keeper's three stores in the
  promoting session, enumerate the year union *before* pruning, promote → verify → delete,
  `audit_keepers.py` E13 as the invariant). Collision rules §8.0 gained rules 8 and 9; the SOCO-40
  charter and the definition of done were updated to match.
- **Both new gates were observed live in other programs the same day**, which is why the edit was not
  deferred: `check_registry_payload_parity` is RED on a dead CAISO bundle dir (G13's failure mode) and
  `check_gate_a_provenance` is RED because NYISO's promotion did not sweep its superseded keeper
  (G21's). Both routed, neither this desk's to fix.
## 2026-09-13 — NWPP addition program chartered: the first region that is a POOL of balancing authorities

A chartering session for adding the **Northwest Power Pool / Western Power Pool footprint** as a registered
region, using the SPP addition workstream as the process reference and the SOCO charter (2026-09-12) as the
non-market precedent. Committed: `docs/multi-iso/nwpp-addition-plan-2026-09.md`,
`docs/handoffs/nwpp-desk-handoff-2026-09-13.md`, `docs/handoffs/nwpp-desk-ledger-2026-09.md`, plus one row in
`docs/multi-iso/README.md`. No code, no data, no registry touched — every existing keeper's cache key is
untouched by construction.

- **The anchor, measured off `data/raw/eia-860/`:** Hermiston Generating Plant is EIA plant **54761**,
  Umatilla County OR, 621.2 MW across four CC generators, balancing authority **`PACW`** (PacifiCorp - West),
  NERC region WECC. The adjacent **Hermiston Power Partnership** (plant **55328**, 689.4 MW) is balancing
  authority **`GRID`**. Two Hermiston plants, two BAs.
- **What makes it unlike every prior addition:** NWPP is **not a BA and not an ISO — it is a pool of ~17
  balancing authorities**, a first for this repo. Fleet over the candidate footprint: **940 plants /
  1,932 operable generators / 98,738.1 MW**, **36.3 % conventional hydro** (35,799.5 MW over 288 plants, of
  which **eight ≥ 1 GW plants hold 17,821.8 MW on one hydraulic chain**), one nuclear unit (1,200 MW), and
  **69.7 % of nameplate owned by regulated electric utilities**.
- **Four charter measurements that corrected the session's own starting premises**, recorded in the ledger's
  §0 rather than absorbed silently: (1) the per-BA load spine is **already committed** in
  `data/raw/eia-930/EIA930_BALANCE_*.parquet` for all 17 BAs, 2019–2026, so it is a *derive*, not a fetch,
  and needs no `EIA_API_KEY`; (2) **AVRN and GRID serve zero load** in all 26,295 hours — generation-only
  BAs, so not zone candidates; (3) EIA-930 assigns **one timezone per BA** (14 Pacific / 3 Mountain), which
  reduces the "two-timezone footprint" problem to a convention choice; (4) **30 defective demand hours** of
  394,424 which, unscreened, put the 2025 coincident peak at 835,464 MW against a true **50,953 MW**.
- **The load-bearing decision (card N2):** the Pool publishes no LMP and had no day-ahead market in
  2023–2025, yet three of the rubric's four load-bearing criteria are price criteria. Unlike SOCO, two
  *measured* prices exist and were pulled live in-session: **CAISO WEIM 15-minute LMPs** (212 `EIMT` apnodes
  across this footprint's BAs; `PRC_RTPD_LMP` returned $63.9213/MWh) and the **Mid-C** traded index (244
  trade dates, 4,748,000 MWh in 2023). Neither is straightforwardly the benchmark — WEIM clears *imbalance
  only* and Mid-C is *daily and peak-only* — so the plan charters a STOP-gated construction lane and refuses
  a neighbouring-hub substitution in advance (gate G17).
- **Routed, not fixed:** CAISO is already registered with a `WECC_import` zone whose firm tranche is named
  **`PNW_hydro_base`** — this footprint, by name. Registering NWPP puts the same energy on both sides of a
  seam. Rule 25 `[R-ISO-SCOPE]` keeps that question with the CAISO lane (ledger R-a).

## 2026-09-12 — SOCO addition program chartered: Hillabee is in a balancing authority, not an ISO

Owner request: a plan and prompt pack to add "whatever ISO Hillabee gas plant in Alabama is in", using the
SPP addition workstream as the reference. The chartering session measured the answer instead of assuming
it. Committed: `docs/multi-iso/soco-addition-plan-2026-09.md`, `docs/handoffs/soco-desk-handoff-2026-09-12.md`,
`docs/handoffs/soco-desk-ledger-2026-09.md`. No code, no data, no registry touched — every existing keeper's
cache key is untouched by construction.

- **The answer, measured off `data/raw/eia-860/`:** Hillabee Energy Center is EIA plant **55411**, Tallapoosa
  County AL, 822.8 MW across three CC generators, balancing authority **`SOCO`** (Southern Company Services,
  Inc. - Trans), NERC region SERC. It is in **no RTO/ISO**. North-Alabama's 8,396.4 MW is **TVA**, a different
  BA, and is out of scope.
- **Phase-0 census done at charter, so no lane re-derives it:** 335 plants / 786 generators / **70,665.7 MW**
  (GA 41,284.4 · AL 24,494.0 · MS 4,577.7 · FL 309.6); demand **229.47 / 239.33 / 239.36 TWh** 2023/24/25;
  a **net exporter** of 10.2 / 10.8 / 13.0 TWh; nuclear **52.4 → 63.0 → 64.2 TWh** across the Vogtle 3
  (2023-07) and Vogtle 4 (2024-04) commissionings, both inside the backcast window.
- **The program's defining problem, stated at charter rather than discovered in W4:** Southern publishes
  **no LMP** and SEEM publishes **no price**, while three of the rubric's load-bearing criteria (C3a/C3b/C3c)
  score against a committed hourly price series. Owner card **S2** is the only route: build a FERC-EQR
  footprint index under a pre-registered STOP gate (lane SOCO-13, `[FABLE]`), and/or rule a determination
  class for a region with no price benchmark. A neighbouring market's hub is refused in advance (gate G17).
- **Two measured findings that redirect the standard recipe.** SOCO has **no EIA-930 sub-BAs** (the product
  covers CISO/ERCO/ISNE/MISO/NYIS/PJM/PNM/SWPP only), so zonal load comes from **FERC Form 714** hourly
  planning-area demand — reachable via PUDL (probed 206) where `ferc.gov` itself 403s. And CAMPD CEMS for
  **AL and GA is absent** while MS is present, so the two states carrying 65.8 of the 70.7 GW are the
  critical path (EPA bulk probed 200 anonymous, ~187 MB per state-year).
- **Two firsts for this model, both gated:** a **two-timezone footprint** (AL/MS Central, GA Eastern —
  gate G19) and the fleet's only **CAES** unit (McIntosh AL, 110 MW — card S7).

## 2026-09-08 — SPP re-baselined on the repaired inputs: the fuel mix is fixed, the price level is not (lane SPP-50)

The batched re-baseline owner ruling P19b called for — SPP-48's wind LEVEL repair and both SPP-49 input
seams in **one** full-span solve. Registered as `2026-09-08-spp-50-rebaseline`. **Promotion DECLINED by
owner ruling P15**: keeper-3 `2026-09-07-spp-3-screened-input` stands, and the price level is opened as
the next lane. Record: `docs/handoffs/FINDING-spp-50-2026-09-08.md`; log `spp-17`; desk ledger §0p.

- **The fuel mix is substantially repaired, in exactly the rows the repairs targeted.** 2024 CC_REGULAR
  **−8.60 → −2.94 TWh** and CT_PEAKER **+9.94 → +1.91** — both FAIL → PASS; COAL_PRB −4.80 → +0.26;
  summed absolute 2024 class error **31.69 → 16.45 TWh** (2023: 22.91 → 15.67, every class flat or
  better). The LP's realised response reproduces SPP-49's **zero-LP** pooled prediction on every class of
  every year (2024 CT −8.06 against −8.46 predicted; CC +5.74 against +5.60).
- **The price level moved the wrong way in every year, and that is the honest cost of the repair.** C3a
  **+14.1 / +7.5 / +7.2 → +15.0 / +12.1 / +14.2 %**. Keeper-3's better 2024/2025 level was being produced
  by gas priced at $0.16/MMBtu at Elk, negative in seven months at Mustang CC, and $0.32–1.52 at
  Harrington — prices that held the level down *while putting the merit order in the wrong place*.
  Removing them fixed the merit order and exposed a level residual that was there all along.
- **The recipe is keeper-3's, machine-verified rather than asserted:** 0 differences across 297
  `meta.json` keys outside provenance, 0 across every `scenario_config` field present in both configs,
  all 8 shared-input fingerprints byte-identical. Three inputs moved: R-LEVEL wind (North
  **+1.915 / +2.304 / +2.131 TWh**, South equal and opposite, **system total 0.000000**), `fuel_prices`
  on 484 / 499 / 482 rows, `heat_rate` on 32 rows.
- **One promotion leg was reported as a miss rather than re-cut after the result.** `emission_rate` moved
  on exactly the 21 clamped rows as the algebraic consequence of the heat-rate clamp
  (`ratio_emission ≡ ratio_heat_rate` to 4.4e-16), inert because SPP's carbon price is 0.0 — a defect in
  the lane's own declaration, put to the owner rather than ruled on by the lane.
- **A condition now on the record:** with promotion declined and the repaired wind parquets kept, SPP's
  designated keeper does not reproduce from the repository's own inputs, so rule 29(b) form 4 no longer
  holds unqualified for SPP — a lane differencing against keeper-3 carries a LIVE input hunk.

## 2026-09-08 — Two measured-input seams repaired repo-wide: an EIA-923 gas-price plausibility screen and a simple-cycle heat-rate floor (lane SPP-49)

Owner ruling **P19**, executed at **zero LP**, with all seven ISOs censused before and after. This is the
repair SPP-46 identified when it killed both gas-split mechanisms at phase 0 and found the defect was in
the inputs. Record: `docs/handoffs/FINDING-spp-49-2026-09-08.md`; log `spp-16`; desk ledger §0o.

- **Seam 1 — the EIA-923 own-month gas price is now screened for plausibility, as a registered gate.**
  `f923_gas_price_plausibility_screen` (`ScenarioConfig`, **default ON**, declared at
  `("2026-09-08", …, "True")`): an own-reported Natural Gas plant-month outside **[0.5, 2.0] ×** the
  plant's own state's EIA delivered-to-electric-power price (`N3045<ST>3` ÷ 1.037) falls back to that
  reference. It landed as a *gate* rather than a construction because a desk can legitimately want its
  own raw series. Reach, measured: SPP 2024 screens 60 low / 11 negative / 25 high plant-months across
  19 plants — **31.9 %** of the gas fleet by MW; MISO 12–24 %; PJM 4–9 %; NEISO ~2 %; NYISO and ERCOT
  nothing.
- **Seam 2 — a simple-cycle heat-rate floor, as a construction.** `_apply_simple_cycle_hr_floor`, beside
  the eGRID CC ceiling it mirrors: a **non-CHP** plant whose every operating row is a simple-cycle prime
  mover and whose plant-grain eGRID rate is below the aero floor is reconciled. Pioneer 57881 moves from
  **3.43 to 9.00** MMBtu/MWh. **CHP is excluded deliberately** — eGRID's cogen rate is steam-credited, so
  a sub-9 value there is the published convention and the model already owns it
  (`_correct_chp_steam_credit_hr`); clamping first would have put two mechanisms on one row (rule 19).
- **The cache-key census predicted the blast radius exactly.** Recorded before either file was edited:
  **18 keys move, 0 off-target**. The landed tree moved the identical set and the identical key pairs —
  CAISO 2, MISO 1, NEISO 5, NYISO 7, PJM 2, SPP 1, six of them designated keepers; **0 forecast, 0
  hindcast, 0 ERCOT**, with ERCOT's keeper key byte-identical to the pre-edit tree.
- **The repair moves the rows it was supposed to and leaves the rest alone.** Pre-repair the lane
  reproduces SPP-46's plant-level attribution **to the GWh**; post-repair Pioneer moves −3,362, the CT
  low-price cohort −5,739 and Harrington's ST_GAS −4,643 GWh, while the **clean** cohorts stay put
  (ST_GAS clean +6 GWh on −6,062). **SPP, MISO and PJM keepers owe a re-solve; ERCOT owes none.**

## 2026-09-08 — SPP's C1 gas split is an input defect, not a mechanism; the wind LEVEL rule loses a free parameter (lanes SPP-46 · 47 · 48)

Three SPP lanes, **zero LP spent between them**. No keeper moved, no `ScenarioConfig` field was added, no
default flipped. Two of the three changed shared code and both are net **parameter-reducing**. Records:
`docs/handoffs/FINDING-spp-{46,47,48}-2026-09-07.md`; log `spp-13` / `spp-14` / `spp-15`; desk ledger §0n.

- **SPP-46 — the gas split SPP has chased through three lanes is a measured-INPUT defect.** Both objects
  SPP-44 left admissible are killed at rule-29 phase 0: the commitment-state input reaches ≤ 25 % of the
  ST_GAS under-run and its measured-state form fails rule 13's forward test; the per-class band needs
  CT ×2.0, and ~100 % of the CT over-run sits on rows whose own inputs are already implausible — so a band
  that closed it would bury the error inside a bad input (rule 14). What the census found instead: across
  the SPP states the EIA-923 own-month gas frame carries **91 plant-months ≤ $0.50, 31 negative and 206
  ≥ $10 of 5,707**, consumed at face value with no plausibility screen; one simple-cycle plant carries an
  eGRID heat rate of **3.43 MMBtu/MWh**; Harrington is priced as $1.48 gas steam while CAMPD has it burning
  coal. The **clean** CT cohort — 110 plants, 7,080 MW — reproduces to **−244 GWh**.
- **SPP-47 — the EIA-923 incomplete-vintage swap now covers each ISO's own extra benchmarked fuels.** One
  executable line, zero new parameters, same threshold and same EIA-930 authority. Six reference cells move
  (SPP/MISO/NEISO 2025 hydro, NEISO 2025 oil, NYISO 2023 **and 2022** oil — the sixth found by an exhaustive
  census, and required by rule 22's *what is held out is the score, never the data*). **Every ISO's scorer
  report is byte-identical**, because `calibration_verdict.py` never reads the reference file: the repair
  fixes a number two committed artifacts state, and changes no score anywhere.
- **SPP-48 — the wind-shape builders lose an undeclared free parameter.** The zonal redistribution is
  invariant to a common rescaling of the shapes but **not** to a per-zone one, so the six-largest-plants
  subsample — covering 13.8 % to 100 % of a zone's capacity — was a per-zone level bias identified by
  nothing measured. It is replaced by the definition it approximated: every operable wind plant in the zone,
  at its own coordinates and hub height, through the unchanged shear law and power curve. `_SAMPLES_PER_ZONE`
  is deleted, the shared rule lives once in `scripts/lib/wind_shape.py` with no ISO name or branch, and the
  result is partition-consistent, so re-cutting a zone boundary can no longer move another zone's weight —
  which is what dissolved SPP-54's three-zone STOP. **Both SPP's and MISO's keepers are now owed a wind
  re-baseline**; the solve-path parquets are deliberately not regenerated yet, so nothing has changed for
  either ISO's LP.

## 2026-09-07 — SPP's W5/W6 batch: six lanes, five killed arms, one T1-H (lanes SPP-45 · 51 · 54 · 55 · 58 · 60)

Six SPP lanes landed together. **Exactly one spent an LP** (SPP-60's T1-H); four of the other five were
decided at **zero LP** on measured records, and the fifth stopped before its screen. **No keeper moved** —
`2026-09-07-spp-3-screened-input` stands, NOT-YET on the same four criteria — **no default flipped**, and
the seven-ISO backcast recipes are untouched. Records: `docs/handoffs/FINDING-spp-{45,51,54,55,58,60}-2026-09-07.md`;
desk ledger `spp-desk-ledger-2026-09.md` §0m (r#12).

- **SPP-51 — the priced SPP↔MISO seam is refused by its own identity, not by a residual.** *Flow follows
  spread* fails on the **measured** record in every year: sign agreement 0.436–0.501 against a 0.55 bar,
  corr(measured spread, measured import) ≈ 0. The real flow is scheduled / JOA / loop flow — which is why
  MISO's own keeper prices this seam as an hourly-anchored offset ladder. Three adjudications did land:
  `derive_neighbor_hr_by_year.py` now carries a **per-ISO** anchor map (an ISO with no map fails), the
  SPP seam blocks carry the **HH + basis** heat rates (`MISO_West` 10.55, `MISO_South` 9.63, `AECI` 10.23,
  `ERCOT` 16.78), and SPP's ERCOT DC-tie block carries the **measured 835 MW clip** (rule 14; ERCOT's own
  820 row untouched, rule 25).
- **SPP-55 — SPP's Contingency Reserve family lands default-off, under the shared `energy_reserve_coopt`
  gate; no new field.** On the published $275 / $550 / $1,100 curve with SPP's own RSG requirement rule,
  the row can bind in **0 / 1 / 0 hours** of 2023 / 2024 / 2025 and in **none** of the 4 / 3 / 7 measured
  hour-long shortage hours — inert on the keeper's dispatch. It also settles what the C3c tail is *not*:
  **1 / 0 / 0** of 42 / 59 / 68 C3c hours carry any reserve-short interval, and the RT LMP in the shortage
  hours has a median of $32–36. C3c is a five-minute price-formation object.
- **SPP-58 — a second, model-blind identification of the N↔S link disagrees with the first.** ψ₂ is a DC
  PTDF/OTDF on a reduced network from public HIFLD geometry + EIA-860 coordinates: it reads no price, no
  shadow price and no model output. It puts the corridor at **11,022 / 13,175 MW** against ψ₁'s
  3,400 / 4,206, and the SPS tie at **1,600 MW** against 10,705. `ttc_mw` is **untouched** — outside the
  pre-declared band is a card, never an edit. The disagreement has a physical address: ψ₁ rests on
  Franklin 161/69 (44 % of binding hours), which HIFLD's 2023 edition cannot see below 115 kV.
- **SPP-54 — the three-zone SPS / Texas-Panhandle pocket is designed and censused, and stopped before any
  solve.** The per-zone wind reconciliation passes both identity legs (Σ_z cap·cf = M(t) to 6e-16) and
  fails feasibility in one hour, because the wind-shape builder weights zones by `cap_z · SHAPE_z(t)` —
  so a six-site sample's mean **level** acts as a zonal capacity-factor level, and splitting the South
  moves the North's potential **+1.4 / +1.5 / +1.9 TWh** at an identical system total. The solve path was
  restored to `origin/main`'s bytes before the PR: **HEAD is still two zones and one 3,400 MW link.**
- **SPP-60 — SPP's first T1-H is on the forecast dashboard** (`spp-2021-2025-realized-t1h-spp60`, key
  `e586d7cae19eab13`; verdict `spp-t1h` **HOLD / FC-3 FAIL at full magnitude**, the reading every ISO's
  bare T1-H has at HEAD). The intake it needed landed with it: **1,527 SWPP rows** in the 2020-vintage
  `eia860_generators.parquet` (the six existing BAs byte-for-byte preserved), `capacity_actuals_spp.csv`
  (110 retirements / 2.2 GW; 185 additions / 13.9 GW), and SPP's first `confirmed-retirements` rows
  (Tolk 1/2, NMPRC 22-00286-UT). `GOLDEN_ISOS` untouched.
- **SPP-45 — the forecast board row's gate-(a) provenance is green**, and the lane's finding is that the
  re-key had already landed under the same standing duty, so it did not manufacture a supersession; it
  supplied the promotion instrument the row was missing. `docs/codebase-site/data/iso-topologies.json`
  also loses the last **48,700 MW** N↔S placeholder (desk repair, SPP-54 R-25) — the site now matches
  `get_iso_config("SPP")`.

## 2026-09-07 — The seven-ISO prose sweep finished, and the ISO badges made readable (lanes SPP-35 + SPP-37)

SPP-34's changelog entry claimed "every 'six ISOs' phrase in the prose" was reached; it was not.
SPP-35 took the five core-doc claims and the `.iso-badge` contrast bug, and routed six leftovers;
SPP-37 executed all six. Together they close the seven-ISO prose position and put every ISO badge
on the site above WCAG AA. **No `src/`, no `frontend/data/`, no matrix shard, no `ScenarioConfig`
field, no default flip, no cache key, no solve, no keeper** — the seven ISOs' recipes are untouched
by construction. The only `scripts/` touch across both lanes is SPP-35's two docstrings (below);
SPP-37 is prose, CSS and one `.gitignore` line. Records: `docs/handoffs/FINDING-spp-35-2026-09-07.md`,
`docs/handoffs/FINDING-spp-37-2026-09-07.md`.

- **Eight "six ISOs" prose sites go to seven, SPP appended last.** SPP-35: `CLAUDE.md:19`,
  `model-methodology-spec.md:13,719`, `docs/codebase/README.md:22`, and `docs/user-manual.md:646`
  (a *correction*, not a substitution — `git check-ignore` over all seven showed `results/SPP/`
  was NOT ignored, so the line stated the measured six-of-seven position). SPP-37: root
  `index.html` ×3 (`:7` meta description, `:34` hero, `:153` footer), `README.md:121`, and
  `market-sim-build-plan.md:9` (that doc's own known-drift banner, plus "SPP 2" in the same
  bullet's zone-count list). Zone count from `get_iso_config("SPP").zones` = 2.
- **`.gitignore` gains `/results/SPP/`** (`:277`), beside the six. An SPP forecast cache would
  otherwise have landed untracked-but-unignored; `git check-ignore -v results/SPP/x` now resolves.
  This also discharges the `user-manual.md:646` caveat SPP-35 had to write.
- **`.iso-badge` contrast: 10 of 10 badges now pass WCAG AA.** SPP-35 routed the shared
  `.iso-badge` (config-reference.html + `css/bc-pages.css`) onto shared.css's tinted
  `.badge--iso-*` pattern — **7/7 at 17.35–19.13:1**, from five outright FAILs plus NYISO at 4.35;
  the seven accents are unchanged and no new hue was introduced. SPP-37 took the one badge outside
  that pattern: `policy-scarcity.html`'s own `.iso-badge` block, whose CAISO cell measured
  4.4786:1 arithmetically. Alpha 0.15 → 0.12 on that one rule: **CAISO 4.57, PJM 5.12,
  NYISO 4.66** — measured in Chromium on painted pixels over the page as served. Reported against
  interest: as Chromium actually paints it the pre-fix CAISO cell read **4.50**, i.e. exactly on
  the threshold rather than SPP-35's 0.03 under it.
- **Two stale-value repairs to the SPP-53 position.** SPP-35 brought
  `scripts/lib/transmission_expansion/spp.py`'s docstring off "Tier-3 placeholder / vintage 2025"
  and gave `scripts/generate_parameter_registry.py`'s preserve-curated-entries contract its missing
  scope; SPP-37 replaced `js/iso-configs-table.js:32`'s "the N↔S TTC is a non-binding placeholder"
  with the **3,400 MW** rule-14 reconciled corridor limit (`FINDING-spp-53`). The code half of the
  registry item — teaching the generator the `iso_configs` link objects, so a hand-added
  `parameter-citations.md` row survives regeneration — stays **open** and routed.

## 2026-09-07 — SPP on the codebase site and in the docs (lane SPP-34; no solve, no keeper, no default)

The seventh ISO reaches every hardcoded ISO list on the codebase site and every "six ISOs" phrase in
the prose. **No `ScenarioConfig` field, no default flip, no `results/cache.py` edit, no matrix cell
move, no keeper shard, no `frontend/data/forecast/` or `frontend/data/backcast/` touch** — the six
existing keepers' cache keys are unmoved by construction (nothing on the solve surface changed).
Record: `docs/handoffs/FINDING-spp-34-2026-09-07.md`.

- **Site.** `js/iso-configs-table.js` (`ISO_COLORS` / `ISO_DESCRIPTIONS` / `isoOrder`),
  `js/viz-iso-topology.js` (`ISO_ORDER` / `ISO_COLORS`), `css/site.css`
  (`.tabs__tab[data-iso="SPP"]` on the already-reserved `--iso-spp`), `forecast-runs.html`
  `ISO_ORDER`, `data-completeness.html` `ISOS`.
- **`data/iso-topologies.json` re-serialized from `get_iso_config`** — the file's own `_meta`
  contract. Adds SPP (2 zones, 1 link, VOLL $2,000) and picks up **one drifted ERCOT value**:
  the `Northeast → North` TTC is 2,300 MW in the config, not the 1,300 MW serialized on
  2026-08-19. Every other pre-existing block is byte-identical. Site counts follow: 7 ISOs,
  39 zones (36 carry load), 47 links — `network.html` stat cards, `index.html` page card.
- **Prose.** `docs/README.md`, `data-pipeline.html`, `docs/codebase/08-config-reference.md`
  (SPP row in the zone table, plus the stale CAISO 4→6 / MISO 3→6 rows repaired against the config;
  SPP's "no scarcity seed / no floor / served scalar interchange" entries in the per-ISO mechanism
  lists), `docs/multi-iso/00-iso-addition-protocol.md` §0/§3 (**SPP IS registered** — SPP-10's
  "not registered" correction was itself stale), `scripts/render_data_dictionary.py` `ISO_ORDER`
  + the regenerated `data/dictionary/data-dictionary.md` coverage matrix.
- **`docs/calibration-log/spp.md`** opened on the MISO header format — lane state, the two
  inherited facts (the non-binding N↔S TTC placeholder; the hubs are a two-point spread), the
  holdout posture (neither marker), the pre-push checklist, `Next shorthand: spp-1`.
- **Four items routed to this lane by `FINDING-spp-20` §5, all closed.** **R-3** — the parameter
  registry regenerated: 1,927 → 2,023 entries, of which **33 are exactly the SPP rows**, each
  re-cited from its own constant's SPP-row comment block (the generator harvests at the constant,
  not at the nested key, so all 33 had landed `needs-citation`); `validate_parameters.py` goes
  FAIL 96 → **OK**. **R-4** — `hydrate_data.iso_for_split_child`: a split-directory child named
  exactly `SPP`/`spp` now matches on whole name before token, moving 8 files
  (`zone-specific-demand/SPP` ×6, `load-forecast/spp` ×2) from `shared` to the `spp` profile with
  **no other ISO's attribution moved** and the `DAMLZHBSPP_*.zip` trap still shut. **R-5** — the
  protocol doc's stale "not registered" claim. **R-8** — `export_lce_lmp._DUMMY_BASE_LMP["SPP"]`
  plus a test that every `SUPPORTED_ISOS` member has a row, which is what would have caught it.

## 2026-09-06 — SPP addition program chartered (docs only)

A seventh ISO — SPP (Southwest Power Pool) — gets a plan and a standing workstream director.
**Docs only**: no code, no `ScenarioConfig` field or default, no data, no solve, no keeper /
marker / matrix shard / registry / workflow edit; SPP is still NOT registered (`_ISO_BUILDERS`
holds six) and every six-ISO pin is untouched.

- **`docs/multi-iso/spp-addition-plan-2026-09.md`** — definition of done (a 2023–2025 SPP keeper on
  the backcast dashboard, six existing keepers' cache keys unmoved throughout); the verified state at
  charter (what SPP data already exists, the five-place six-ISO pin, the `spp`/`DAMLZHBSPP_*` token
  trap, the moved portal.spp.org API); the eight owner cards P1–P8 (topology by audit — owner ruling
  O-1; per-ISO seam representation; ERCOT DC ties; reserves deferred; no scarcity seed; tail
  threshold; the first-solve rule-29 screen with no incumbent control; forecast entry routed); the
  wave graph W1–W6 with `[FABLE]`/`[OPUS]` labels per lane; the lane table; the fetch/upload manifest
  (every row a fetch lane first — owner ruling O-3); hard gates G1–G18; the prompt pack (W1–W4 charters
  in full, W5 reserved, W6 routed to the capx director).
- **`docs/handoffs/spp-desk-handoff-2026-09-06.md`** + **`spp-desk-ledger-2026-09.md`** — the SPP
  ADDITION DESK (standalone — owner ruling O-2), mirroring the scenario desk's §0–§7 structure and the
  capx director's refresh doctrine: first-act read order, grade-by-content, ask-before-LOST, never
  read a green check as proof, cards via AskUserQuestion, one sitting = one ledger entry, errors
  against interest, collision register against the capx / SCN / per-ISO lanes.
- Index lines in `docs/README.md` and `docs/multi-iso/README.md`.

## 2026-09-06 — wallclock 3a: the per-ISO anchor table re-baselined on main (docs only)

Wave-3 item 3a of the wall-clock desk (`docs/handoffs/wallclock-desk-log-2026-09.md` §1 row 3a),
run once every wave-1/2 item was merged or closed. **Docs only** — no code, no `ScenarioConfig`
default, no keeper shard / marker / matrix shard / registry / workflow edit; nothing promoted,
nothing dashboard-registered; every bundle captured was deleted before the PR (rule 29
`[R-SCREEN]` (c)). Full record, with every number: `docs/handoffs/wallclock-baseline-2026-07.md`
§WALLCLOCK 3a.

- **Why re-baseline.** §PERF-B's anchor table predates A-1/A-2/A-4 (which removed the year-1
  `data_prep` premium), **A-3 (which changed what `total` means** — the `hourly/` sidecar block
  now runs *inside* `results_write` as `sidecars`, where before it ran after the timing line and
  was booked to no phase), and **B** (calibration-CLI default ON, so a real calibration run's
  `solve_p1` no longer resembles a pinned replay's).
- **Two arm families, and they must not be confused.** (1) **Pinned anchor** — `--all
  --max-concurrency 1` under `HIGHS_THREADS=1 WARMSTART=1 WARMSTART_XYEAR=0`, all six ISOs,
  every fidelity oracle clean; the P1 seed is **off by construction** here. (2)
  **Calibration-CLI default** — `XYEAR=1` + `MARKET_SIM_P1_BASIS_SEED=1`, NEISO and ERCOT, empty
  basis cache per arm; **not goldens, not a byte instrument.**
- **The gap A-3 closed, measured.** Process wall vs Σ per-year `total`: the assessment measured
  **28.4 s on one NEISO year** (243.3 vs 271.7); this session measures **3.2 s across three
  NEISO years** (305.6 vs 308.8) and **4.0 s across ERCOT's two** (1,114.0 vs 1,118.0). The
  sidecar cost did not vanish, it is now *reported*: `sidecars` is 3.6–5.5 s on NEISO/NYISO,
  13.5–14.2 s on CAISO, 13.8–21.8 s on ERCOT, and **24.0–26.0 s on MISO/PJM** — over half of
  `results_write` there.
- **Attribution, stated because the arm-2 delta is two mechanisms, not one.** On ERCOT
  (2024+2025) `total` **1,764.4 → 1,114.0 s (−36.9 %)** decomposes exactly: `solve_p1`
  **−546.9 s** (item B), `solve_p0` **−165.7 s on 2025 alone** (the pre-existing cross-year warm
  start; 2024's −29.2 s is host noise at *identical* 250,529 P0 iterations on both arms), against
  `markup` **+91.9 s** of export/apply overhead. On NEISO the P1 seed is **provably inert** —
  2023 P1 iterations are **62,954 on both arms, identical to the digit** — so none of its
  −17 % is B.
- **Cross-session reproduction.** The pinned arm reproduces §WALLCLOCK B's OFF-arm iteration
  counts exactly (NYISO 2023 P0 269,416 / P1 268,305; CAISO 2023 P0 300,609 / P1 290,022), and
  the CLI-default arm lands within 0.2 % of its ON-arm P1 counts (ERCOT 2025 78,731 vs 78,856).
  Wall deltas between sessions remain inside the §PERF-B ±35 % host-noise band; iteration counts
  are the reliable instrument.
- **Ledger.** A-1+A-2+A-4 took NEISO year-1 `data_prep` **71.3 → 12.1 s** (measured here at
  **14.0 s** pinned / 9.0 s CLI-default, three days and several `main` merges later). **A-5 was
  already on main since 2026-09-02** (PR #4579) — the assessment doc's "not on main" row is
  stale and is corrected in the baseline doc, not by editing the assessment. **A-6 is not a
  landed change**: measured-negative (peak 13.28 → 13.27 GB) and reverted (`d9ad2ae3`).
- **Environmental, recorded:** `data/clean` is absent in a fresh container and CAISO/NYISO refuse
  to solve without it (`regenerate_clean.py`, 56 datatypes) — the solve-path face of the check-[4]
  artifact §WALLCLOCK B reports; and **PJM's `pjm-da-virtuals` corpus is gitignored under PJM
  DataMiner2 licensing**, so its capture fails until re-fetched (72 parquets, 22 MB). Neither is
  the §PERF-B OOM — and that OOM **did not reproduce**: MISO (13.28 GB) and PJM (13.29 GB) both
  completed all three years at 8760 h with the swapfile untouched.

## 2026-09-06 — wallclock B: the cold-rebuilt P1 seeded from the same year's P0 basis (WARM-START CLASS; calibration default ON)

Wallclock desk item B (`docs/handoffs/wallclock-opportunities-2026-09.md` §3 / §6.3). Owner memo
`docs/handoffs/p1-basis-seed-decision-memo-2026-09.md`, **signed (A) FLIP 2026-09-06** by chat
instruction. Wall-clock only: **the LP, its objective, bounds and rows are untouched**; the
change is **WARM-START CLASS, not byte-identical** — it moves the simplex starting point of the
cold-rebuilt P1 on the three bridge ISOs (ERCOT / NYISO gas commitment bridges, CAISO RA
must-offer) and nothing else. No `ScenarioConfig` field or default, no keeper shard / marker /
matrix shard / registry / workflow edit, nothing promoted, nothing registered; the probe
bundles were deleted.

- **The change.** `pipeline/solve.py::run_energy_solve`, cold-P1 branch: the P0 model's basis
  is exported (the export the cross-year holder already took there) before `model = None`
  and installed on the second `DispatchModel` through
  `apply_cross_year_basis` (identity column map, `alien=True`) before its first solve. An
  adaptive re-solve pass (C-1b `reuse_p0_from`) is seeded from the previous pass's P1 basis
  when that pass exported one (new `export_p1_basis` kwarg → `EnergySolveResult.p1_basis`; set
  by the ercot-221 pass 1 and every ercot-230 iteration), else from the P0 basis.
- **Gate — the P-2 shape.** `MARKET_SIM_P1_BASIS_SEED`, global default OFF; the calibration
  CLIs default it ON through `run_calibration.resolve_p1_basis_seed_default`
  (`--no-p1-basis-seed` opts out, an explicit env var is honored). Armed only inside the
  cross-year gate and only on the backcast callers, so `MARKET_SIM_WARMSTART_XYEAR=0` (the
  goldens / replay / merge-base-control pin) and the forecast path (explicit `xyear_warmstart`
  bool) stay cold and byte-identical; `--report` / `--replay-bundle` / `--rebuild-benchmark`
  and the direct `solve_and_persist` callers stay OFF.
- **A latent crash on main, fixed here.** The cold-P1 branch exported the cross-year basis
  from `model` guarded on the gate but not on the model's existence; a reused-P0 pass (C-1b)
  has none, so under the calibration default `XYEAR=1` every ERCOT adaptive pass 2 raised
  `AttributeError` at that export (reproduced at the merge base on the trivial LP; the s3
  measurements ran under the `XYEAR=0` pin and never saw it). Pinned by test with the seed off
  and on.
- **Tooling.** `capture_keeper_goldens.py`'s fidelity oracle no longer fails on the `years`
  key: since R-AW / Y-14 the bare `ERCOT` key replays the forward config on its designated
  2024–2025 span while the composed keeper's `meta.json` records 2023–2025, so every post-Y-14
  ERCOT capture was refused on that key alone (the subset invariant is asserted at the solve
  site). The HiGHS solve log line now carries `simplex iterations N, objective X` (reads after
  `h.run()`; byte-inert).
- **Gates.** (1) Byte-identity with the seed OFF, merge-base control `34f3ce35` vs branch under
  the determinism pin: `regression_gate.py --mode byte` check [1] **PASS** — ERCOT 2024–2025
  (7 files, 28 numeric columns, atol=rtol=0) and NEISO 2023 (5 files, 20 columns); zero
  reshuffle; smoke PASS; `audit_keepers` PASS; `legitimacy` red by control (and green once
  `data/clean/capacity-deliverability` is regenerated — a fresh-container artifact, recorded).
  (2) Seed ON vs OFF through `diff_warmstart_bundles.py` + `hourly/system`: objective and total
  generation identical on every arm; per-unit differences marginal-tie only with the LMP
  identical at every moved unit-hour; price differences confined to dual-degenerate hours —
  none on ERCOT/NYISO, and on CAISO only on the zero-load import nodes (CA zones bit-identical).
  **P1: ERCOT 2025 349.2 → 142.0 s (273,893 → 78,856 iters); ERCOT 2024 two-pass 628.1 → 225.1 s
  (pass 2 seeded from pass 1's P1 basis: 332.9 → 92.8 s); NYISO 2023 96.4 → 67.6 s; CAISO 2023
  354.5 → 123.1 s.** Peak RSS +0.6 GB on ERCOT (13.27 GB, inside the s3 envelope). (3) Fast tier:
  12 failures, 9 pre-existing by control and 3 order-sensitive passes in isolation, none in a
  touched file; `test_xyear_warmstart_default.py` 10 → 23. Full record: baseline doc §WALLCLOCK B.
- Docs: `docs/cross-year-warmstart.md` "Same-year P1 basis seed"; the evidence record
  `docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK B; the memo's decision block;
  `tests/unit/pipeline/test_xyear_warmstart_default.py` +13 tests.

## 2026-09-06 — wallclock A-4: the year-1 `data_prep` premium re-profiled after A-1/A-2; one site memoized on disk (byte-identical)

Wallclock desk item A-4 (`docs/handoffs/wallclock-opportunities-2026-09.md` §2). Wall-clock
only. **No LP, objective, bound or row change, no `ScenarioConfig` default, no keeper /
marker / matrix shard / registry / workflow edit, nothing promoted, nothing registered.**

- **The re-profile (the item's actual ask).** `cProfile` over a one-year keeper replay per
  ISO through the `capture_keeper_goldens` machinery — NEISO `2026-08-17-neiso-99-joint-p1`
  **2023**, and ERCOT `2026-09-05-ercot248-two-config-keeper` via the bare `ERCOT` key (the
  forward config on 2024–2025 per R-AW, replayed on **2024** only; the retired
  `ERCOT__carveout-2023` key is not used). **Exactly one site is ≥3 s cumulative, once per
  process, and a pure function of on-disk inputs**: `fleet/eia860._egrid_boundary_hr_repairs_for`
  — NEISO 4.739 s, ERCOT 4.550 s, `ncalls == 1` on both.
- **Both named A-4 candidates are measured NOT to be candidates and are left alone.**
  `zone_assignment.build_zone_lookup`'s derivation reads **0.129 / 0.118 s** and
  `fleet/eia860._rows_to_generators` **0.073 / 0.027 s** of *own* time — A-2's sheet mirror
  already took the cost out from under them, and `_rows_to_generators`'s 5.24 s cumulative is
  the boundary repair it calls. Every other ≥3 s `data_prep` site is year-keyed or takes
  `year`, so year 2 pays it again and it is not a year-1 premium at all.
- **The change.** New `src/market_sim/data/disk_memo.py` generalizes A-2's content-addressed
  pattern from a DataFrame to a mapping: sha256 over every source file's bytes plus the
  caller's parameters names a JSON memo beside the anchor source. JSON never pickle; values
  re-typed and re-validated on read; a non-finite value is refused for writing rather than
  served from a memo whose identity cannot be proved; every failure degrades to the caller's
  own `compute`; a fresh dict per call. `egrid_sheets.py`'s inline digest is replaced by the
  shared `content_digest`, **byte-compatible** so mirrors already on disk keep their names.
  `_egrid_boundary_hr_repairs_for` becomes the resolver (`lru_cache` per process + the memo
  across processes) over the unchanged derivation, now `_egrid_boundary_hr_repairs_compute`.
- **Gate (1), dict equality vs the direct derivation, every EIA-860 source pair on disk:**
  `direct == miss == hit` **True on 8/8** (canonical + seven `vintage_<year>/`), compared by
  `==` *and* per-item `repr` *and* key/value type. **2.166 → 0.058 s (37×)** on the canonical
  vintage, **12.688 → 0.455 s** across all eight. Accepted set `{55641: 6.880032798350796}`
  unchanged at full precision.
- **Byte gate — merge-base control, arms solved SEQUENTIALLY:** NEISO full 8760 × 2023–2025
  from a sparse worktree at `0a50feb4` and the branch tree at `9e05bd74` (whose diff is
  exactly this change's six files), both `git_dirty: false`.
  `regression_gate.py --mode byte` **check [1] PASS** (9 files, 32 numeric columns,
  atol=rtol=0), zero reshuffle in all three years, smoke PASS (24), `audit_keepers` PASS;
  check [4] `legitimacy(--keepers)` FAIL is **pre-existing by control** (the standing NYISO
  Long Island `transfer_security_limit` gap, rc=1 with the identical exception on the
  `0a50feb4` worktree). Manifests under `results/regression-goldens/wc-a4-{before,after}/`;
  bundles deleted before merge per rule 29 `[R-SCREEN]` (c).
- **Fast tier on the branch: 8,425 passed, 44 skipped, 1 xfailed, 542 subtests passed,
  0 failed** in 276 s — nothing pre-existing to except.
- **In-solve effect:** NEISO year-1 `data_prep` **16.3 → 12.1 s (−4.2 s, −26 %)**; the year-1
  vs warm-year premium **8.85 → 4.40 s (−50 %)**. Warm years move +0.9 / −0.4 s — noise, as a
  once-per-process cache should. **Residual stated and the item closed on it:** 4.4 s, of
  which the largest single item is `cache_control.retained_footprint` at 1.9 s (a disk scan of
  `results/`, not a derivation), the rest genuine parse and distributed first-touch cost with
  no frame ≥0.5 s. Record: `docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK A-4.

## 2026-09-06 — wallclock A-1: the COD map's per-plant reduction vectorized — RETRO EVIDENCE for merged commit `be598ead` (byte-identical)

Docs + two golden manifests only. **No source file, no LP change, no `ScenarioConfig` default,
no keeper / marker / matrix shard / registry / workflow edit, nothing promoted, nothing
registered.** Wallclock desk item A-1 (`docs/handoffs/wallclock-opportunities-2026-09.md` §2)
shipped through PR #4875 (commit `be598ead`, merge `fc05c5c3`) carrying `cod_ramp.py` + its
unit test **only** — the charter's baseline-doc row and this entry never landed, and the PR
body was empty, so no measurement was on record (desk log §2.5). Re-measured from scratch:

- **The change (already on main, unmodified here):** `_load_cod_map`'s
  `for code, grp in work.groupby("pc")` per-plant reduction — 14,330 groups, each paying a
  `DataFrame.dropna` / `sort_values` / `iloc` — replaced by `_reduce_cod_groups`: one stable
  sort on the plant code plus numpy segment reductions over the resulting contiguous slices.
  The per-plant arithmetic is unchanged, including the pairwise summation order (`reduceat`
  is *not* a drop-in: it flips the `round` for the 15 of 14,334 plants whose exact mean is a
  half-integer).
- **Gate (1), dict equality vs the frozen shipped loop, every EIA-860 vintage directory:**
  `vec == ref` **True on all 8** (the canonical `data/raw/eia-860` plus seven
  `vintage_<year>/`). `_load_cod_map` **16.20 → 0.07 s (231×)** on the canonical vintage
  (14,334 plants), **91.60 → 0.38 s** across all eight; the reduction in isolation
  15.78 → 0.010 s. Unit file at HEAD: 46 passed, 8 subtests passed.
- **Byte gate — merge-base control on the commit itself:** NEISO keeper
  `2026-08-17-neiso-99-joint-p1` replayed full 8760 × 2023–2025 under the determinism pin from
  worktrees at `be598ead~1` (`2886235c`) and `be598ead`, which differ in exactly two files
  (`cod_ramp.py` and its test). `regression_gate.py --mode byte` **check [1] PASS**
  (9 files, 32 numeric columns, atol=rtol=0), zero reshuffle in all three years, smoke PASS,
  `audit_keepers` PASS; check [4] `legitimacy(--keepers)` FAIL is **pre-existing by control**
  (the standing NYISO Long Island `transfer_security_limit` gap, rc=1 on plain `origin/main`).
  Manifests under `results/regression-goldens/wc-a1-{before,after}/`; bundles deleted before
  merge per rule 29 `[R-SCREEN]` (c).
- **In-solve effect:** NEISO year-1 `data_prep` **72.9 → 35.9 s (−37.0 s, −51 %)**; 2024/2025
  −1.1 / −0.6 s (noise) — the map is `lru_cache`d, so the win is **once per process**.
  Independently reproduces the A-1 leg of the stacking §WALLCLOCK A-2 records (71.3 → 36.7 s
  from A-1 alone, → 10.8 s with A-2). Record:
  `docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK A-1.

## 2026-09-05 — wallclock A-3: class-band sidecar vectorized, sidecar block put on the clock (byte-identical)

`scripts/run_calibration_full.py` only (plus its unit test, the baseline-doc row and two
golden manifests). **No LP change, no `ScenarioConfig` default, no keeper / marker / matrix
shard / registry / workflow edit, nothing registered.** Wallclock desk item A-3
(`docs/handoffs/wallclock-opportunities-2026-09.md` §2):

- **`_write_class_band_hourly_sidecar`** mapped `unit_id → band` per ROW — 6,718,920
  `_tranche_band` calls plus a ~14 s list comprehension materialising the strings of an
  already-categorical column, per NEISO year. New `_band_categorical` computes the band once
  per distinct id (over the categorical's categories) and indexes by the codes; categories,
  codes and values are identical to the per-row `pd.Categorical([...])`. Measured on the real
  NEISO 2023 P1 frame: the band column 15.63 s → 0.16 s; the whole writer ~16 s → ~5 s.
- **The `hourly/` sidecar block ran AFTER `log_year_phase_timing`**, so it was booked to no
  phase and no year's `total`. It now runs before the timing line as the new `sidecars` entry
  of `results_write_parts`: the six frozen wire fields are unchanged and
  `results_write == state + frames + parquet + bench + sidecars` exactly
  (`pipeline/timing.py` untouched — its parts contract already carries any ordered mapping).
  NEISO now reports `sidecars` 8.0 / 5.9 / 7.2 s (2023/24/25).
- **Gates:** `BandCategoricalTest` (every `_TRANCHE_BANDS_EXACT` token, every prefix
  family, non-tranche ids, an unused category, a missing id, end-to-end sidecar equality);
  NEISO keeper full-span replay merge-base vs branch — every hourly sidecar and dispatch
  frame sha256-identical, `class_band_hourly` `frame.equals` all three years,
  `regression_gate.py --mode byte` check [1] PASS at atol=rtol=0 (check [4] pre-existing
  by control); fast tier 8,104 passed. Record:
  `docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK A-3.
## 2026-09-05 — wallclock B-0: owner decision memo for seeding the cold-rebuilt P1 from the same year's P0 basis, with the ERCOT bench the assessment doc was missing

Docs only. **No `src/` file, no `ScenarioConfig` default, no keeper shard / marker / matrix shard /
registry / workflow touched; nothing promoted, nothing registered.**
`docs/handoffs/p1-basis-seed-decision-memo-2026-09.md` is the plan-§6 memo the wallclock desk
gates wave 2a on: what changes (simplex starting point only — the P0 basis handed to the second
`DispatchModel` through the shipped `apply_cross_year_basis`), who pays today (the ERCOT / NYISO /
CAISO cold-P1 keepers, P1 ≈ P0 on the anchor tables), the neutrality class and its
`diff_warmstart_bundles.py` gate, what stays cold (goldens/replay pin `MARKET_SIM_WARMSTART_XYEAR=0`
⇒ seed off), the proposed surface (calibration-CLI default ON, `--no-p1-basis-seed`, env var
honored, forecast path unchanged, adaptive pass seeded from the previous pass's P1 basis), two
options and an owner signature block. The measurement it cites did not exist at HEAD
(`wallclock-opportunities-2026-09.md` §3 placeholder): supplied here — ERCOT forward keeper
config, 2025, determinism pin, scratch monkeypatch driver never committed: `solve_p1` 287.1 →
139.3 s (2.06×), 273,893 → 78,856 iterations, objective / total gen / served load / prices
identical (0 dual-degenerate hours), 16 offsetting marginal-tie unit-hours. Both placeholders in
the opportunities doc (§3 table, §6.3 bench record) are filled. Recommendation: (A) flip.

## 2026-09-05 — Y-14: the ERCOT stage-0 golden captures the FORWARD 2024–2025 config; the `ERCOT__carveout-2023` capture key is retired (owner ruling R-AW)

Two scripts, one test file, one manifest block. **No shard, marker, bench, status page,
`results/calibration/` file, solve or re-capture.** Owner ruling R-AW (audit-program director
sitting 2026-09-05, verbatim *"The golden config should be the 2024:2025 one not 2023"*), executed
per `docs/handoffs/FINDING-y14-ercot-golden-forward-2026-09-05.md`:

- **`scripts/check_golden_manifest.py`** — `FORWARD_ROLE` / `RETIRED_CAPTURE_KEYS` constants;
  `resolve_role` / `designated_years`; a partitioned ISO's bare key resolves through its `forward`
  role; a CURRENT golden of a partitioned config must replay exactly its designated span (hard);
  `registered_years ⊇ years` (rule 22, hard); a retired key's entries are validated as v2 and
  reported as historical capture records, never compared to the live shard. Exit 0 unchanged;
  every bare-ERCOT report line byte-identical (9 stale + 6 retired where 15 stale read before).
- **`scripts/capture_keeper_goldens.py`** — imports both constants from the gate; the bare
  `ERCOT` key (and `ERCOT__forward`) resolves to the composed run's registered bundle
  `ercot248_two_config_keeper` (its `meta.json` is the forward config verbatim, 280/280 keys) sliced
  to [2024, 2025] with `registered_years` [2023, 2024, 2025] kept on the entry and snapshot;
  `slice_to_designated_span` raises unless designated ⊆ registered; `ERCOT__carveout-2023` is
  refused with the citation.
- **`results/regression-goldens/perfb-stage0/manifest.json`** — the carve-out entry gains a
  `retired` block; every other byte identical. The five perfb-s2/s3 refactor-pair manifests are
  untouched (a `keeper_id` records what was actually captured).
- **`tests/scoring/test_golden_manifest_provenance.py`** — the two Y-11 STOP reds rewritten to the
  new semantics (retired-record provenance chain; forward config on its designated span) plus
  eleven new tests; 57 passed. Fast tier 8114 passed, exit 0.
- The R-AI re-capture (ERCOT clock 2026-09-07 19:02Z) is NOT run; its command is in the finding §7.
## 2026-09-06 — wallclock A-2: the eGRID xlsx comes off the solve path (27.80 s → 0.219 s per process; `data_prep` y1 36.7 → 10.8 s on top of A-1), byte-identical on a NEISO merge-base control

Wall-clock only. **No `ScenarioConfig` field, no default, no constant, no keeper shard,
marker, matrix shard, registry or workflow is touched; the LP, its objective, bounds and
rows are untouched, and the values read are the same values.** Classed BYTE-IDENTICAL and
gated as such.

Three `pd.read_excel` calls against the 21 MB `egrid2023_data_rev2.xlsx` sat on the solve
path and were paid afresh in every process — `zone_assignment._plnt23` (PLNT23), and
`fleet/eia860._egrid_boundary_hr_repairs_for` (PLNT23 again under a *different*
projection, then UNT23). openpyxl's read-only parser is ~10 µs/cell; the three cost
**27.80 s** on this container.

- **The helper (`src/market_sim/data/egrid_sheets.py::read_egrid_sheet`).** One function
  both call sites use. It mirrors the frame `read_excel` returns to a parquet file beside
  the workbook — `<xlsx-stem>.<sha256[:16]>.<sheet>.parquet`, gitignored, written on first
  miss — and serves every later call from there. **27.80 s → 0.219 s (127×).**
- **The digest covers the read parameters, not just the workbook.** The two PLNT23 call
  sites ask for different column sets, and `read_excel` returns columns in **sheet** order
  rather than the caller's `usecols` order. Mirroring the exact frame each site receives,
  instead of one wide per-sheet mirror that callers subset, is what makes the mirror read
  equal to the xlsx read *by construction* — column order and dtypes included. Changed
  workbook bytes still hash differently, so self-invalidation is unaffected.
- **Advisory, never authoritative.** Parquet, never pickle (no `allow_pickle` path
  anywhere). An unhashable workbook, an unwritable directory or a corrupt/truncated mirror
  logs a warning and falls back to `pd.read_excel`; mirrors are written to a pid-unique
  temp name and `os.replace`d, so the two concurrent invocations rule 12 permits can never
  read a partial file. The `MARKET_SIM_USE_CLEAN` branch in `_plnt23` is untouched and
  still takes precedence when armed — the mirror backs only the raw fallback beneath it.
- **Gates**, all at merge base `fc05c5c34`. (1) `frame.equals` xlsx-vs-mirror **True** for
  all three `(sheet, usecols)` pairs on the real workbook, with column order and dtypes
  compared explicitly, plus 8 fast-tier tests on a synthetic workbook
  (`tests/test_egrid_sheets.py`). (2) Fast tier 8270 passed / 6 failed, all six confirmed
  failing identically on the merge-base tree. (3) **NEISO 2023–2025 merge-base control**,
  keeper `2026-08-17-neiso-99-joint-p1`: `regression_gate.py --mode byte` **check [1]
  PASS** (9 files, 32 numeric columns, atol=rtol=0), zero reshuffle in all three years,
  smoke PASS, `audit_keepers` PASS. Its overall `RESULT: FAIL` is check [4]
  `legitimacy(--keepers)` alone, pre-existing by control (NYISO Long Island
  `transfer_security_limit` gap).
- **Reach, and how it stacks with A-1.** The win is **once per process, not once per
  year** — both readers were already process-cached — so a 3-year NEISO replay gains
  ~26 s in year 1 and nothing after. Measured **on top of A-1**, which landed first and
  had already taken y1 `data_prep` 71.3 → 36.7 s: A-2 takes it to **10.8 s** (−25.9 s,
  −71 % of the phase; combined y1 −85 %). ~6 % of the 3-year wall. An earlier
  measurement of this change at base `5b5af5a` (−25.2 s off 71.3 s) is superseded and
  must not be added to A-1's number — it is largely the same seconds. Record, the
  drift audit since the gated base, and the not-widened follow-up (`data/egrid.py`, a
  fourth read of the same workbook family, deliberately left alone as out of scope):
  `docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK A-2.
## 2026-09-06 — wallclock A-6: `malloc_trim` at the cold-P1 seam is MEASURED-NEGATIVE; the seam's RSS step is live payload, not allocator retention

Docs + the AFTER golden manifest. **No file under `src/` changes in this entry.**
Nothing promoted, registered, or dashboard-touched; no `ScenarioConfig` field, keeper
shard, marker or matrix cell. This is the evidence half of wallclock A-6: the code
(`pipeline/solve.py` +12, new `utils/heap.py`) merged ahead of it via PR #4893 /
commit `c2cb9a78`, with only the BEFORE arm's manifest (desk log §2.8, "evidence
owed"). **The measurement says the trim does not earn its place; removing it is
recommended, and is the owner's call** — it is byte-identical either way, so leaving
it carries no correctness risk.

- **The test.** `malloc_trim(0)` immediately after `model = None` on the cold-P1 route
  in `pipeline/solve.py::run_energy_solve`, on the hypothesis
  (`docs/FINDING-perfb-s3-adaptive-pass-2026-09.md` §6) that the 12.1–13.4 GB ERCOT year
  peak is the P1-rebuild moment and glibc is holding the freed P0 arena. Both arms are
  `capture_keeper_goldens.py --iso ERCOT__carveout-2023` (registered 2023–2025) on merge
  base `2886235c`, `MARKET_SIM_MEM_DEBUG=1`, determinism pin, 6 GiB swap armed.
- **The result.** Process peak VmHWM **13.28 → 13.27 GB** — the target (get under the
  14 GB cgroup by trimming) is unmet. Seam recovery 0.05–0.23 GB; `p1_post` +0.3 / +0.5
  / +0.1 s, inside this box's noise but the same sign in all three years.
- **Why (the reusable part).** Each cold-P1 model's `after addRows` RSS sits ~1.15 GB
  above the P0 model's on a byte-identical LP, but that step is **live** payload —
  `r0` (`dispatch` + `emissions`), `markup`, `mc_bid`, and the floored
  `p1_fleet_arrays` (`min_gen` + `availability`) — ≈1.0 GB of the 1.15 GB,
  arithmetically. A trim frees only what is already free. The next lever on the ERCOT
  peak is narrowing what stays alive across the seam, not allocator tuning; the
  year-loop `_malloc_trim` in `run_calibration_full.py` is unaffected and still earns
  its place.
- **Byte gate.** `regression_gate.py --mode byte` check [1] **PASS** (9 files, 34
  numeric columns, `atol=rtol=0`), 0.000 % reshuffle in all three years, manifests
  10/10 identical. Overall `RESULT: FAIL` is checks [4] only — the NYISO Long Island
  TSL gap and a stale `status/NEISO.js` — both reproduced identically on the merge-base
  control, i.e. pre-existing on main.
- **Instrument caveat.** The `ERCOT__carveout-2023` capture key was retired by owner
  ruling R-AW (Y-14) while this ran; both arms used it on the merge base where it still
  resolved, with the identical config, so the A/B is internally valid. A re-run at HEAD
  must use `--iso ERCOT` (forward, {2024, 2025}).
- Full row, the per-model RSS ladder and the corollary for the next session:
  `docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK A-6.

## 2026-09-05 — capx D64: the CCS retrofit's FOURTH seam adjudicated (Phase 0, zero solves) — both fixed-cost legs are TPC-fractions in their source and scale with the island; PJM's 2029 residual closes on the arithmetic; the capture VOM adder is found uncited and 2.7–3.6× every published basis

Docs + one results JSON. **No `src/` file, no `ScenarioConfig` field, no constant, no matrix cell,
no forecast surface, no solve.** `docs/handoffs/FINDING-capx-d64-2026-09-05.md` discharges D50 §8
Disclosure 1 the way D49 §1 adjudicated the first three seams:

- **Basis (§1).** ATB 2024 (fetched from OEDI, sha256 `567dde9d…`) publishes the capture island's
  Fixed O&M ($/kW-yr) and Variable O&M ($/MWh) for a specific NETL reference plant and states in
  terms that property taxes & insurance, maintenance labor and maintenance materials "are
  calculated as a percentage of TPC". NETL Rev 4a (`da0027aa…`) B31A→B31B.90 decomposes to 95.5 %
  TPC-proportional (fixed) and 100 % island-proportional (variable); the NGCC-retrofit report Rev 3
  (`e66c0111…`) carries the retrofit's O&M as exactly the capture plant's. Construction: ΔFOM and
  the VOM adder × `k = captured / captured_ref` — the D50 factor, zero new constants.
- **Re-screen (§2).** The recovered D50 census instrument, extended and run on six ISOs
  (`results/calibration/capxd64_fourth_seam_census.json`): every carbon-0 row lost (PJM 2029's two
  converters fall to 0.633 / 0.638 of the bar — the residual closes), one sub-reference RGGI row
  gained; NEISO / NYISO / CAISO stay cap-bound at the ceiling, with the hour requirement compressed
  from 4,900–7,800 h to 6,500–7,700 h (efficient hosts win again).
- **The VOM level (§2.4).** `ccs_retrofit_vom_adder` = 8.0 $/MWh is `needs-citation`; ATB says 2.95
  (2026$), NETL 2.23. At the published level the carbon-0 screen reopens on the shipped shape
  (6–11 GW per ISO at the ceiling) and sits on a 0.1–4 % knife-edge under seam 4 — the shipped
  carbon-0 closure is carried by the uncited number, and the shape and the level are coupled.
- **Blast radius (§3)** stated: every forecast bare key re-keys under (b′-1); behaviour can move only
  in the six live ≥2028 ledgers with CCS rows; ≈ 53 min of marginal solve.
- **D65 charter (§4):** one default-off field (`ccs_retrofit_fixed_cost_co2_scaling`, requires the
  D50 field) + the rule-23 re-identification of the VOM adder onto the pinned ATB extract (widened
  to carry `Variable O&M`), two NEISO t1f arms against the committed keeper, six STOPs (a k = 1 row
  moving; seam 4 alone opening any carbon-0 row).

## 2026-09-05 — landing-page cleanup: root `index.html` + `model-updates.html` brought to the current model state

Site-only. **No file under `src/`, `scripts/`, `results/` or `frontend/data/` is
touched; nothing changes a solve, a keeper, a marker or a matrix shard.** Executes
the two owner-signed SITE dispositions of `docs/model-audit-release-plan-2026-08.md`
§6 (items 5–6, signed 2026-08-13) that touch the root pages, and the plan's
standing instruction to remove hard page/ISO counts from prose because they rot.
Every claim on the edited pages was re-verified against source before writing:

| Claim as written | Source truth | Fix |
|---|---|---|
| root `index.html` hero + meta: "two ISOs (ERCOT and CAISO)" | `iso_configs.py::_ISO_BUILDERS` — six entries (ERCOT, CAISO, PJM, MISO, NYISO, NEISO); imported and counted: 37 zones (34 carry load), 46 links | "six ISOs … on one ISO-agnostic LP"; no zone/link counts on the landing page |
| hero: forecast horizon only | `holdout_policy.CALIBRATION_YEARS = {2023, 2024, 2025}`; forecast 2026–2050 | states both modes: forecast 2026–2050, backcast against 2023–2025 to calibrate |
| Codebase Explorer card: "Ten interactive pages … with D3 visualizations" | 22 `.html` under `docs/codebase-site/` incl. hub, five data dashboards and a redirect stub; count already contradicted the site's own hero | describes the arc without a count |
| Backcast Run Explorer card: "for every registered calibration run" | rule 15 retention is KEEPER-ONLY since 2026-09-05 (`frontend/data/backcast/registry/` holds exactly the six keeper sidecars) | "for each ISO's keeper run; the dashboard retains keepers only" |
| Calibration Status card: "C1–C6 criteria matrix" | `calibration_verdict.py::CRITERIA` runs to C8 under `RUBRIC_VERSION = 3.5` | "per-criterion scorecard", no letter range |
| no link to the forecast dashboards or the mechanism matrix | `forecast-status.html`, `forecast-runs.html`, `mechanism-matrix.html` are live nav targets on the codebase site | three cards added; a nav row (Calibration · Backcast · Forecast · Explorer · Updates) added, matching `model-updates.html` |
| `model-updates.html`: two hand-written entries dated 2026-06-04 comparing ERCOT probe runs 27/28 and 31/32, citing `inputs/raw-data/campd-unit-outages.csv` | those runs were pruned (keeper-only retention); the path moved to `data/raw/` in W1; the log had not been extended since | **repositioned as a pointer** per the signed disposition: URL kept, short intro, cards to `CHANGELOG.md`, `docs/calibration-log/`, Calibration Status, the Backcast and Forecast dashboards and the Mechanism Matrix; stale entries removed (git history is the record) |
| `docs/codebase-site/index.html` hero "Sixteen pages, 19 visualizations" / intro "Ten pages … plus three live dashboards" | `forecast-validation.html` became a redirect stub after the 2026-08-19 count was taken; the Forecast menu has three dashboards | counts removed from both sentences |
| `docs/codebase-site/index.html` Capacity Evolution card + system-diagram tooltip: "6-step … known retirements → economic retirements → known additions → CCS retrofit → new entry → backstop" | `model/capacity_evolution/`: step 0 confirmed exits, step 1 announced retirements, step 2 CCS retrofit (BEFORE economic retirements since W2-C), step 3 economic retirements, 4 known additions, 5 economic entry, 6 reserve-margin backstop | order corrected, "6-step" dropped |
| `frontend/css/style.css` `.link-card-cta` coloured by the card's fuel accent | measured contrast on white: `--solar` 1.66:1, `--wind` 2.10, `--gas-ct` 2.24, `--hydro` 2.41, `--storage` 2.85 — all fail WCAG AA for text | CTA text is always `--accent-deep` (5.19:1); the accent stays on the decorative top border |

Also verified, unchanged: the Learning Hub card (five explainers, `learning-hub/index.html`);
`backcast-results.html` (frozen redirect stub, untouched by design); the `forecast-validation.html
→ nav` disposition is moot — that page is itself a redirect to `forecast-status.html`, which the
Forecast dropdown already carries. Both root pages validated for tag balance and every local
`href` resolved on disk; both rendered headlessly in Chromium.

**Deferred (narrative-page restructure, SITE-A scope, not this cleanup):**
`docs/codebase-site/capacity-evolution.html` and its `viz-capacity-flow.js` flowchart still
walk the pre-W2-C six-step order (known → economic retirements → additions → CCS → entry →
backstop) with no step-0 confirmed-exit channel; the hub card and tooltip now state the code's
order, the page behind them does not yet.

## 2026-09-05 — keeper-only retention + dead-code sweep (owner instruction: delete, never archive)

**Owner instructions this session:** on the backcast side only KEEPER run data is
retained; stale forecast runs are not retained either; superseded scripts are
DELETED, never archived; the branch is refreshed onto main. No solve, no
mechanism, no determination change anywhere.

- **Backcast (`results/calibration/`):** 20 unmapped solve-output bundles deleted —
  every same-HEAD A/B control (nyiso-150/151/152/185-189, caiso-224, miso-170) and
  every superseded arm (caiso-231, miso-198, neiso-97, nyiso-186, nyiso-192, and
  miso-213 once main promoted miso-217). Kept: the six keeper bundles, the
  ercot-248 two-config keeper's constituent bundles (ercot234 / ercot236), the
  class R/P pre-registered artifacts and the `_`-prefixed working dirs.
  `check_registry_payload_parity.KEEP_REQUIRED_UNMAPPED_BUNDLES` is now EMPTY.
  The two non-keeper registrations main added (nyiso-192, miso-213) were pruned
  with `scripts/prune_iso_runs.py`; MISO's forecast gate-(a) stamp re-keyed to
  miso-217 (R-T step 4, which the promotion had skipped).
- **Forecast (`frontend/data/hindcast/` + `results/hindcast/`, `results/ff*`):** 36
  stale sidecars deleted with their results dirs — kept per ISO every run holding
  a current bare FF-2D verdict key, every run the `program-status.json` board
  seed cites, the registered crossovers and the T3 goldens (41 sidecars). 109
  `results/hindcast/` dirs no sidecar referenced and the sidecar-less
  `ffr3p/3v/4b-4f/ffrsc/arm3arm/ffr-sa-smoke/baselines` lane outputs deleted
  (their READMEs stay). `VERDICT_MAP` and `invariant-failures.json` drop the
  pruned runs' lines; `ff-verdicts.json` untouched.
- **Scripts:** the whole `scripts/archive/` tree (292 files) deleted; 54
  `gen_*_attestation.py` for non-keeper runs deleted; 1,229 record-only
  `scripts/probes/` files deleted (the 69 that live code imports or names stay);
  21 dead top-level/data one-offs deleted (miso-148 helpers, ffr3a2/3a3 scorecard
  trio, ownership attribution pair, zonal-sufficiency CLIs, bench regens, …).
  `regen_caiso_bench_cems.py` → `scripts/data/`, `bench_cold_solve.py` →
  `scripts/diagnostics/` (still called). `scripts/README.md` keeper-rotation rule
  now reads DELETE; CLAUDE.md tree updated.
- **`src/market_sim`:** dead modules `results/metrics.py`, `data/som_conduct.py`,
  `pipeline/result.py` (placeholder `YearSolveResult`) and 7 unreferenced
  functions / 6 unreferenced constants removed. ScenarioConfig fields with no
  production reader are REPORTED in the session summary, not removed
  (rules 24/26/28 govern those).
- **Verification:** parity, audit_keepers, legitimacy --keepers, golden-manifest,
  gate-(a), refactor-guards and forecast --reindex all pass; fast pytest tier
  shows only the failures already red on main (ERCOT golden partition ×3, the
  miso intermediate cache-key pin, the PJM override test) plus the pre-existing
  forecast-invariant undeclared-FAIL rows.
## 2026-09-05 — DOCS-B (model-audit WS4): methodology spec FINALIZED, user manual FINAL, CHANGELOG catch-up, index refresh

Docs-only. **No file under `src/`, `scripts/`, `frontend/`, `results/` or
`.github/` is touched; no keeper shard, marker, matrix shard or
`program-status.json`; nothing changes a solve.** Executes DOCS-A's gap-audit
checklist (`docs/handoffs/methodology-finalization-audit-2026-08.md`), verifying
every claim against source before writing — where the memo and the code
disagreed, the code won.

- **`model-methodology-spec.md` is FINALIZED** and carries a status banner
  saying so. It stops being a build specification with as-built patches: §7
  "Build Agent Instructions" is deleted (its durable content rehomed to a new
  §1.9 "Modelling Commitments & Stated Limitations"; the rules themselves live
  only in `CLAUDE.md` and §7 is now a cite-by-ID index), §2.3 becomes
  "Construction invariants", the §6.2 performance-target table is deleted, and
  the Phase-0 as-built note is gone. The words "Build Agent" no longer appear.
- **Five P1 corrections.** §5.2 is restructured around
  `ScenarioConfig.retirement_rule` — default **`"pipeline"`**, which the spec
  never mentioned, so its entire economic-retirement section had been
  documenting the non-default `"legacy"` branch. Coal's threshold 1 → 3
  consecutive loss years. CAISO's topology 3 zones → **5 in-state zones + the
  WECC import node**, naming the three SP15 children. The §6.1 parallelism
  snippet (the uncapped `ProcessPoolExecutor` that was removed from `run_sweep`
  as a rule 12 `[R-PARALLEL]` violation) is replaced by `pipeline/members.py`
  and `DEFAULT_MEMBER_CAP = 2`.
- **Five further divergences found while re-deriving the audit's number list,
  none of them in the memo:** `ccs_retrofit_capex_kw` ≈$900/kW → **1,521.4**
  (the ATB 2024 capture-island increment); the IRA "other clean" credit's
  2028→2033 cliff → the **four-knot 2033/34/35/36 ladder**;
  `use_plant_emission_rates_v2` "default off" → **on**;
  `reserve_margin_build_enabled` "default off" → **tri-state `None`**, resolving
  ON for the five capacity-market ISOs; ERCOT 9 links → 10 and CAISO 4 → 6.
- **Seven shipped mechanisms the spec did not describe** are now in it: the
  §2.1b solve-window cap, the `matrix` subcommand and cases-mode expansion, the
  `_p1` pass-tagged cache file, `MARKET_SIM_DATA_ROOT`, the real `cache_key`
  construction (drop-at-default over registered optional fields, the CI-enforced
  registration ledger, key moves as declared epochs), warm-start, and
  byte-identity as a reproducibility contract.
- **Citations repaired and rule citations stabilized.** Five `tests/` paths
  repointed to the tiered layout; `model/dispatch.py` and `data/fleet.py`
  citations repointed to `model/lp/` and `data/fleet/` with one note that both
  facades are frozen import surfaces. The duplicate **§1.8 heading** is resolved
  by relocating benchmark basis to the delegation block (the determination
  rubric §0b specifies it in full, including a fallback path the spec never
  carried). **All ~37 bare-ordinal rule citations now carry stable `[R-*]`
  IDs**, each referent read in its own sentence — including four that were not
  CLAUDE.md ordinals at all but the older legitimacy-audit numbering
  ("rule #12" → `[R-MEASURED]`, "repo rule #1" → `[R-STRUCT]`, §5.8's
  "rule #12" → `[R-ACCURATE]`, "#9/#11").
- **The delegation boundary is intact** — nothing re-absorbed from
  `calibration-and-validation-methodology.md` or either rubric.
- **`docs/user-manual.md` swept command-by-command on a clean clone, draft →
  FINAL.** Two substantive errors corrected: §7.5 described **two** holdout
  tiers and placed 2022 in the wrong one ("Locked-test years (2022, H1-2026)"),
  where `[R-HOLDOUT]` has **three** tiers with separate markers — train
  2023–2025, validation 2022 laddering to 2020 (**iterable**, `complete`), and
  locked test **2019** and H1-2026 (touch-once, `final`), with 2019 missing
  entirely; and §3.2 said "History was kept (no rewrite)" and offered
  `git restore --source=<pin-sha>` as an always-available recovery route, when
  the 2026-08-16 history rewrite **was executed and force-pushed**, making the
  pin shas dead references and some payloads unrecoverable from this repository.
  Counts and keys re-derived rather than transcribed (ScenarioConfig fields
  713 → 794; default cache key → `e5ecd4105ada3e58`; `regenerate_clean --list`
  50 → 55; test files 447/454 → 524/531), and all ~30 `file.py:NNN` citations
  converted to `module::symbol` because every one of them had drifted.

## 2026-09-05 — `run_calibration_full.py --help` regression found (parser unaffected; routed, not fixed here)

Found by DOCS-B while verifying the manual on a clean clone.
`python scripts/run_calibration_full.py --help` exits with
`ValueError: unsupported format character ')' (0x29)` raised inside
`argparse.HelpFormatter._expand_help`. The cause is a literal `%` in the
`--caiso-st-gas-peak-measured` help string (`"(+6.0 %), so it makes C3a WORSE"`),
which argparse interpolates; it needs `%%`.

**The parser itself is unaffected** — every flag parses and every documented
invocation runs; only the rendered `--help` catalogue is unavailable, and
`run_calibration.py --help` still renders. Recorded in the manual (§4.6 warning
+ a new §9.9 troubleshooting entry) and **routed to the calibration desk**:
DOCS-B is a docs-only lane and cannot patch `scripts/`.

## 2026-09-05 — Keeper wave: four ISOs promoted across 2026-09-04/05; ERCOT, NYISO, NEISO and PJM read CALIBRATED

Catch-up entry — these promotions merged without CHANGELOG entries. Each is
recorded in its own ISO's keeper shard, calibration log and finding; this entry
is the index, not a re-adjudication.

| ISO | Designated keeper | Determination |
|---|---|---|
| ERCOT | `2026-09-05-ercot248-two-config-keeper` | CALIBRATED |
| PJM | `2026-08-15-pjm-162-inputclock` (unchanged) | CALIBRATED |
| NYISO | `2026-09-05-nyiso-189-steam-identity` | CALIBRATED |
| NEISO | `2026-08-17-neiso-99-joint-p1` (unchanged) | CALIBRATED |
| CAISO | `2026-09-05-caiso-246-b1-spot` | NOT-YET |
| MISO | `2026-09-05-miso-217-intermphys` | NOT-YET |

- **NYISO** advanced three times in two days: `nyiso-187` (Astoria routing +
  `cc_capacity_reconcile`, promoted by owner ruling), `nyiso-188` — **the first
  NYISO keeper to read CALIBRATED** — and `nyiso-189` (the eGRID steam-collapse
  CT heat-rate identity), promoted under the owner's standing-disposition
  formula. Each is a measured-input or identity repair at **zero free
  parameters** under rules 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` / 1
  `[R-STRUCT]`; the rejections stand beside them (nyiso-190 refuted clause,
  nyiso-191 CC_CHP scope rejected on rule 19 `[R-ONE-MECH]`).
- **MISO** ran `miso-210` (clock, all ten A/B gates passing) → `miso-213`
  (zonal gas-basis layering) → `miso-217` (the `phys_*` coverage gap closed).
  MISO stays **NOT-YET on C3a-2025 alone**.
- **CAISO** promoted `caiso-246`, a coverage-gate repair of the keeper's own
  designed gas-pricing mechanism at zero free parameters — the EIA N3050CA3
  monthly survey publishes NA for 2025-09/10/11, so those months fell out of the
  measured spot overlay's coverage test. CAISO stays **NOT-YET**.
- **ERCOT** registered its two-config partition as one run (`ercot-248`) and
  pruned the dashboards to keepers only.

## 2026-09-05 — NYISO `complete` and `frontier` re-declared on nyiso-189 (owner rulings Q38 and Q39; records lanes D56-R and D56-R2)

Two records lanes, **zero solves**, executing two owner rulings from the
capacity-expansion director's refresh sittings. Both halves of the 2026-08-30
withdrawal are now reversed, because the withdrawal removed both instruments
together and its stated cause was never a merits finding against the frontier
claim — it was that the then-designated keeper read NOT-YET.

- **`complete` (validation tier) re-declared 2026-09-05** by owner ruling **Q38**
  (2026-09-04, r#35, card C-9: "Re-declare now via a records lane"), executed by
  records lane **D56-R**. The licence is the withdrawn block's own `reentry`
  clause: re-entry is a new explicit owner declaration on a designated keeper
  that scores CALIBRATED. The original D56 never launched and its target keeper
  `nyiso-188` was superseded by `nyiso-189` before execution.
- **`frontier` re-declared 2026-09-05** by owner ruling **Q39** (r#37, card
  C-10), executed by records lane **D56-R2**, closing the split the D56-R finding
  recorded on the frontier leg. The determination was re-verified artifact-only
  (`calibration_verdict.py --run-id`, committed artifacts, no solve) before the
  declaration was written, per rule 22 `[R-HOLDOUT]` D-5(b).
- **Nothing is granted beyond the validation tier.** `final` remains **empty for
  every ISO**, the holdout spend freeze is active and tier-scoped to the locked
  test, and NYISO's 2019 and H1-2026 are **never granted and unspent** — as they
  are for every ISO. `final` readiness reads NOT-YET on the merits. Frontier is
  not `final`.
- The genealogy is preserved in place, five layers deep: declared 2026-07-31 →
  cleared 2026-08-06 → ratified 2026-08-23 → reverted 2026-08-30 → **re-declared
  2026-09-05**.

With this, the four-instrument test (frontier · `complete` · forecast-board gate
(a) · ISO-level determination) reads {ERCOT, NEISO, NYISO, PJM} on all four.

## 2026-09-05 — PERF-B session 3: the vacuous adaptive pass eliminated; full byte gate PASS at atol=rtol=0

Executes the WS3-next charter (`docs/handoffs/perfb-session2-markup-charter-2026-09.md`).
Three items, one PR each, merged in order (#4741 → #4742/#4744 → #4752/#4753),
with the finding at `docs/FINDING-perfb-s3-adaptive-pass-2026-09.md`.

- **C-2** — count every build and every pass in the phase-timing accounting.
- **C-1a** — skip the ercot-221 adaptive pass when its P1 objective is
  elementwise identical to pass 1's.
- **C-1b** — reuse pass-1's P0 in the adaptive passes instead of re-solving the
  identical LP.

**Byte-gated, not merely regression-tested:** `regression_gate.py --mode byte`
at `atol = rtol = 0` reads **PASS** on ERCOT forward 2023–25,
`ERCOT__carveout-2023` and NEISO — 0.000 % reshuffle in every year, manifest
`content_hashes` agreeing 10/10, 6/6 and 10/10, and every bundle parquet
(`hourly/` sidecars included) frame-identical at 34/34, 14/14 and 31/31.

Measured removal, from the merge-base control's own solve log: ERCOT forward
2025 loses the whole adaptive pass (**−823 s**, 4 → 2 HiGHS runs) and the other
years lose their duplicated P0 (−298.5 / −352.6 / −369.7 s). The three-year
ERCOT forward wall goes **4,859.5 → 3,592.3 s (−26 %)**, 12 → 8 HiGHS runs.

No `ScenarioConfig` default changed; no keeper shard, marker, matrix shard,
registry or workflow touched; nothing promoted.

## 2026-09-05 — Governance: owner rulings R-AH … R-AK recorded (audit records lane v28b)

Four rulings from the 2026-09-05 15:32Z audit sitting, on the record for the
first time. They had grepped **zero files** before this lane — the third
consecutive cycle of the R-AF / R-AG defect, in which a ruling given verbally
goes unrecorded until a records lane writes it.

- **R-AH** (card A, Y-1) — the branch-protection flip is performed on the first
  CI-covered head whose R-AE six-check set reads 6 of 6. The condition was met at
  18:06:46Z; the Settings action itself is unread from here.
- **R-AI** (card C, X-2) — hold the stage-0 golden re-captures until the 09-07
  clocks; no capture taken, all three clocks intact, stage-0 at 4 of 7.
- **R-AJ** (card D, G2 leg 1 + R-V) — golden-tier CI proof, **then** declare.
  X-3's non-launch is discharged (PERF-B s3 merged), the one authorized proof is
  run #11 / `33983249186`, **status unread — so leg 1 is NOT declared by that
  entry.**
- **R-AK** (card E) — launch-failure routing: until the failure class clears,
  records / capture / small-repair lanes are assigned to **Opus**; Fable stays
  for adjudication-class lanes and rule-27 core-infrastructure scope. Recorded on
  the director's attestation, not claimed as verified — session launch outcomes
  leave no artifact in the tree.

One dated correction carried with them: the parallel v28 lane's sweep read
"`R-AH` → 0 files. Confirmed: none issued." **The count was right and the
conclusion is wrong** — a zero grep shows nothing was *recorded*, never that
nothing was *issued*.

## 2026-09-05 — Gate G2: released to DOCS-B by dispatch; NOT recorded as declared in the tree

**Recorded as a discrepancy rather than resolved, because resolving it is the
owner's act, not a docs lane's.**

DOCS-B (this lane, model-audit WS4) was released by a director dispatch citing
**owner ruling R-AM, 2026-09-05**, as the G2 declaration — WS4's charter holds
it until G2 (`docs/model-audit-release-plan-2026-08.md` §4.9).

**At this pin the repository carries no record of either.** A word-boundary grep
across `docs/` and `CHANGELOG.md` returns **zero files** for `R-AL`, `R-AM` and
`R-AN`; there is no "G2 DECLARED" line anywhere; and the newest board entry
states the opposite — under **R-AJ**, "G2 leg 1 is therefore NOT declared by this
entry", with the one authorized golden-tier proof (run `33983249186`) recorded as
**status unread**. The plan's §2 preconditions also list PERF-B merged
byte-green, which is now satisfied (see the PERF-B s3 entry above).

This entry therefore records what is verifiable: **the dispatch asserts G2; the
tree does not show it.** That is the exact shape of the R-AF / R-AG / R-AH defect
the audit board has now documented three cycles running — a ruling given
verbally and unrecorded until a records lane writes it — and it is logged here
in the same form the board uses for R-AK: on attestation, not claimed as
verified. **A governance records lane should confirm R-AM and write the G2
declaration with its date**; this docs lane does not mint an owner act it cannot
observe, and no CHANGELOG line here should be read as that declaration.

## 2026-09-05 — capx D60: the three-ruling arming batch (Q40 · Q41 · Q42) — the MISO ratio, both NYISO requirement gates, and the CCS capex repair as the global default

**Execution of three owner rulings** given 2026-09-05 at director sitting r#37 (capx ledger
§0ah.3 / §3), landed FLIP-FIRST in one commit so every downstream re-solve meets the final
posture exactly once. No new field, no new parameter value, no keeper, no marker, nothing
against measured H1-2026. Pre-declaration
`docs/handoffs/PREDECL-capx-d60-2026-09-05.md` (pushed before any code); execution record
`docs/handoffs/FINDING-capx-d60-2026-09-05.md`.

- **Q40 — `adequacy_accounting_ratio_dated_net` armed for MISO** through
  `_miso_config` `default_scenario_overrides` (rule 25 `[R-ISO-SCOPE]`; the dataclass default
  stays `False`). D31's own arithmetic with the denominators net of the step-1b fossil-dates
  channel's accredited exits: **0.854600 → 0.893436**, zero DOF
  (`FINDING-capx-d51-2026-09-04.md` §7). The owner resolved the letter-vs-substance
  divergence D51 recorded against itself: limb (c) failed by the letter, and its measured
  cause is arithmetic — every `add.shares` move is the ratio of a total that lost 2.9 GW of
  `gas_ct` when the longer position stopped the BLK-10 backstop.
- **Q41 — `nyiso_requirement_forecast_peak` AND `nyiso_requirement_vintage_factors` armed for
  NYISO** through `_nyiso_config` `default_scenario_overrides`, which NYISO did not have
  before (rule 25; both dataclass defaults stay `False`). The in-table requirement is now
  NYSRC Table D.2's published NYCA UCAP requirement to under 1 MW, the model's peak dropping
  out; the position artifact D45 §6 named is closed (+9.4 / +5.2 / +7.3 pts long → 0.6–2.6
  pts short of the market's published position), LOYO 3/3, zero free parameters
  (`FINDING-capx-d52-2026-09-04.md` §8(1)). **The NYCA ICAP demand curve stays OFF** (D52
  §8(2), re-affirmed D59), and so does `locality_capacity_curves` (D59).
- **Q42 — `ccs_retrofit_capex_co2_scaling` armed as THE DATACLASS DEFAULT for all six ISOs**,
  as a **(b′-1) declared flip** — the second entry in
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, with the frozen drop value left at `"False"`,
  exactly the D44 pattern (`FINDING-capx-d50-2026-09-04.md` §8). A **posture, not a
  transfer**: no ISO's fitted number is carried — the island is sized against
  `captured_ref` = 0.90 × 6.3 × 0.057 = 0.32319 t/MWh, the same reference host
  `new_entry._emerging_lcoe` charges the ATB increment against.

**Both pinned default keys advance, by design:** `ScenarioConfig()`
`4c6b03ae098b6e3e` → **`e5ecd4105ada3e58`**, bare backcast `8211c72bb1960adc` →
**`6a2845e50951394e`**, with dated cause blocks in
`tests/regression/test_persisted_identity.py` and a new cache-epoch ledger entry
(2026-09-05) in `src/market_sim/results/cache.py`. An **explicit `False` still drops from
the hash and still addresses its pre-flip bundle**, which is (b′-1)'s useful inverse and is
asserted by test. **No committed artifact moves**: no keeper, sidecar, determination or
dashboard row, because those are files rather than cache lookups — and behaviour is
byte-identical for every backcast and for every hindcast/crossover horizon ending before
`ccs_retrofit_available_year` (2028), since `ccs.py::apply_ccs_retrofit` returns at its
first statement before any read of the flag and that call site is the field's only consumer
in the source tree.

**Docs, matrix and tests.** CLAUDE.md capacity-evolution step 2 and
`model-methodology-spec.md` §5.6 carry dated amendments; the three mechanism rows'
definitions and their cells in all six ISO shards are re-stamped (CCS: `K` on measured
evidence at ERCOT / NEISO / PJM / MISO, `K`-by-posture at CAISO / NYISO with each ISO's own
zero-solve ceiling census recorded and its t1f evidence to follow; MISO ratio `K` on the D51
record; both NYISO gates `K` on the D52 record). New
`tests/unit/config/test_d60_arming_batch.py` pins that each override reaches exactly its own
ISO, that every other ISO and every plain backcast still resolve all three fields off, and
that nothing else armed. `tests/unit/model/test_ccs_retrofit.py` pins the pre-flip
construction explicitly in its fixture so each pre-D60 test still tests what it was written
to test, and adds `TestCapexCo2ScalingIsTheDefault` for the shipped posture.

## 2026-09-05 — capx D50-R: the CCS capex-scaling repair completed — PJM + the conditional MISO arm, the blast radius priced, the arming question returned to the owner (nothing armed)

**The completion of capx D50** (built default-off in PR #4728, ERCOT + NEISO arms
registered there): `docs/handoffs/FINDING-capx-d50-2026-09-04.md` now exists at the
filename all four ISO shard cells cite, with the pre-declaration
(`PREDECL-capx-d50-2026-09-04.md`) graded at full magnitude — P1/P2/P4/P5/P7/P9 HIT,
**P3 SPLIT**, **P6 MISS 1-of-3**, and **P8 SPLIT with Addendum A.1's own grading corrected**
(A.1 graded PJM on 2028 alone and called MISO's 0.53 GW a hit "at the edge"; at full
magnitude P8 holds in 2028 for every carbon-0 ISO and fails in 2029–2030 at PJM 1.68 GW and
marginally at MISO 2030).

**PJM** `pjm-t1f-d50-ccscapex` (`pjm-2026-2030-d50-ccscapex`, key `167e65187f32056b`,
pre-declared and matched; 27.3 min / 9.0 GB, solo): 2028 converts **zero** vs the control's
16 rows / 2,832.6 MW, but 2029 converts 2 rows / 909.8 MW vs 3 / 752.1 — the **window falls
3,584.7 → 909.8 MW (−74.6 %)** while the **year 2029 rises +157.7 MW**, so **PREDECL §3
STOP 1 FIRED** and is recorded and diagnosed rather than waived: the two converters
(`p55337_econ`, `p55976_econ`) are two of the exact five tranches Addendum A.3 pre-named,
and in the control they had already converted in 2028, so the arm **defers** rather than
adds. A.3's own falsifier clause assigns the 2029 conversion to the **surface** (the D49
§1.4 price-object seam, unbuilt), and P3's 2029–30 leg is still graded a MISS. Fleet MW is
retrofit-preserving to the decimal; what moves is the capacity path (accredited firm
−595 / −562 / +639 MW, and in 2030 the adequacy backstop builds 5,874.3 MW of CT against the
control's 3,874.3 while the control instead decides 2,000 MW of `gas_ct` through the
economic pipeline at COD 2032). FC rows status-identical; HOLD → HOLD.

**MISO** `miso-t1f-d50-ccscapex` (`miso-2026-2030-d50-ccscapex`, key `f3f96e14bb75c9d9`,
matched; 64.3 min / 10.0 GB, solo): solved because **PREDECL §2.4's conditional fired on its
literal terms** when PJM's P3 2029 leg missed. **Zero conversions in every year** vs the
control's 4,631.1 MW (**P7 HIT with room**; seam 2 removes 3,909.2 MW, seam 1 the remaining
722.0 MW of regular-CC). The arm is **capacity-identical to the control in every year** —
`gas_cc + gas_cc_ccs` identical to the decimal, reserve margins identical to six decimals,
and the FC-1 invariant detail string **byte-identical** — the wave's cleanest confirmation
that a retrofit is MW-, zone- and accreditation-preserving. HOLD → HOLD.

**Blast radius, measured (the number for the owner's card).** The (b′-1) flip mechanic was
verified at HEAD rather than assumed: the frozen drop value stays `False`, so **a post-flip
bare config hashes identically to today's explicit-`True` arm** — the arm-key column of
PREDECL §4 *is* the post-flip bare-key column, and all 12 keys re-resolve to their
pre-declared values. Of **153** committed forecast-mode `run_config.json`, 150 re-key; 108
end ≤ 2027 and are byte-identical (the screen is gated 2028); 42 reach ≥ 2028, of which
**31 bundles / 25 distinct keys** carry a decided CCS retrofit. Those split into **7 bare
keys** (the six t1f + GOLDEN-3 — exactly the set PREDECL §6 named), 6 preserved historical
keys that are never re-solved, and 12 unregistered keys §6 did not enumerate. Re-measuring
the bare set costs **180.4 min ≈ 3.0 h**, but **four of the seven are already paid** by this
programme's own arms, leaving **CAISO 22.6 + NYISO 12 + GOLDEN-3 33.0 = 67.6 min ≈ 1.1 h**.
No committed artifact moves; backcast keys advance byte-identically.

**Recommendation: ARM the default** (finding §8), on the pre-stated condition — which D50
declared as a *direction plus a STOP set*, not a numeric threshold, and which is quoted
verbatim and graded there. Two disclosures ride with it: the **fourth seam is not closed**
(ΔFOM and the capture VOM adder stay reference-host-sized and dilute per tonne, moving the
clearing threshold rather than removing it), and the **PJM 2029–30 surface channel is live**.
**NOTHING ARMS in this lane** — the field ships default-off and the flip is an owner ruling.

**Records.** `VERDICT_MAP` gains the MISO row; `ff-verdicts.json` gains the two suffixed
keys **purely additively** (283 insertions, 0 deletions); the **PJM and MISO matrix shard
cells** carry their own measured verdicts (MISO `U → O` on its own solve, rule 25 — nothing
transferred); no keeper, shard verdict outside those two cells, marker, default flip or
backcast artifact moves.

## 2026-09-04 — capx D51: the MISO internal-supply accounting ratio re-identified on the dates-ON fleet (default-off, rule 23); forecast rubric v1.1 (owner ruling Q37, the pre-declared follow-up-attestation limb)

**Mechanism (default-off, nothing armed).** D49 §2.6 routed it:
`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"] = 0.8546` (capx D31)
was identified on the D27 census fleet, which still carried the 2021–2023 real
exits the PRA had already dropped; since owner ruling Q30 / capx D44 the
fossil-dates channel removes those same plants explicitly at step 1b while the
ratio still applies — the same MW netted twice, the consumed reserve position
5.8 / 6.9 pts short of the market's own (D49 §2.4). One term of D31's
arithmetic moved: the same PRA Summer offered Generation numerators over the
same D27-ledger denominators (reproduced to the decimal, 143,822.1 / 143,749.5)
NET of the accredited dated exits the D46 dates-ON ledgers record (4,508.5 /
7,977.6 MW) → **0.893436** (per-year 0.878 / 0.909), zero free parameters,
derived and reconciled by test from three committed inputs
(`scripts/data/derive_miso_adequacy_accounting_ratio.py`,
`tests/curation/test_derive_miso_adequacy_accounting_ratio.py`). Ships as
`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO` behind the new
gate `ScenarioConfig.adequacy_accounting_ratio_dated_net` (default `False`;
registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False`, so the default key
`4c6b03ae098b6e3e` and the bare `miso-t1h` recipe key `eff2c890746ec966` are
unmoved; the armed A/B keys `b538d37b36a88247`; backcast-coerced), resolved at
all three D31 seams (ledger / floor increments / backstop) through the one
resolver `resolve_internal_supply_accounting_ratio(iso, config)`; harness flag
`run_capacity_hindcast.py --adequacy-accounting-ratio-dated-net`; matrix base
row + six shard cells (MISO `fc: O`, the other five ISO-exclusive `·`).
Pre-declared `docs/handoffs/PREDECL-capx-d51-2026-09-04.md` (pushed before the
derive script existed); measured on the suffixed `miso-t1h-d51-ratio`
(`docs/handoffs/FINDING-capx-d51-2026-09-04.md`). The owner arms or declines.

**Forecast rubric v1.0 → v1.1** (`docs/forecast-determination-rubric.md` §5,
§0, §9; `scripts/forecast_verdict.py::RUBRIC_VERSION`): a follow-up lane may
author a forecast attestation iff it is pre-declared before authoring, moves
only the attestation row, and re-scores artifact-only (model case
`FINDING-capx-d47-golden3-attestation-2026-09-04.md` §1; signature capx ledger
§3 Q37). Text only — no threshold, no re-score; records scored under `"1.0"`
stand.

**Records rider (zero solves):** `ercot-t1f-pre-d46` / `caiso-t1f-pre-d46`
marked provenance-only stubs no delta may be read against (D47 §6 item 2); the
board's NEISO `golden` field repointed to GOLDEN-3 with the GOLDEN-2 text
preserved beneath (D47 §6 item 4); D49 §5 item 5 (oil unscreened after 2022)
recorded in the MISO matrix retirement cell. NEISO leg 7
(`neiso-t1h-d45r-datesoff`, owner ruling Q36) is registered by the same lane.

## 2026-09-03 — capx D44: the fossil announced-date channel ARMS AS THE DEFAULT POSTURE (owner ruling Q30). One default flip, both pins advanced, no solve

`ScenarioConfig.fossil_announced_exits_enabled` flips default `False` →
`True`, executing **owner ruling Q30** (director sitting r#31, 2026-09-02) on
the capx D42 A/B (`docs/handoffs/FINDING-capx-d42-fossil-dates-ab-2026-09-02.md`):
a fossil unit's owner-filed EIA-860 Schedule-3 planned retirement date is now
honored as an **exogenous, vintage-gated step-1 input** (reversal registry
armed; under the verified posture a later re-filing may defer or cancel a
vintage exit, never inject or advance one), and the economic retirement screen
runs on the **residual UNDATED fleet** — the rule-19 `[R-ONE-MECH]`
reconciliation D42 designed with the gate, so no unit's exit is decided twice.
Admissibility was ruled on rule 13 `[R-MEASURED]` by the additions-pipeline
symmetry; the superseded default's "an announcement is not a certainty"
rationale is a statement about precision, and D42 measured that precision
(MISO T1-H unit recall 5/19 → 16/19, every non-coal exit class opened,
`false_retire` 0.0, 98.5 % plant-grain precision of released MW, **zero**
economic-screen decisions displaced).

Nothing else moved: **no new field, no parameter value, no solve, no keeper,
no marker, rule 22 untouched.** Documentation amended to match the posture —
CLAUDE.md capacity-evolution steps 0/1, `model-methodology-spec.md` §5.1
(the pseudocode gains limb 1b and the "Confirmed vs announced" prose is
rewritten), the field/module/limb docstrings in `scenarios.py`,
`capacity_evolution/{evolve,retirements}.py`, `data/announced_retirements.py`,
`data/fleet/assembly.py` and `runner.py` — plus the mechanism matrix (base row
+ all six shards: MISO `fc` O → **K** on its measured verdict, the other five
U → **O**, armed but holding no verdict of their own, rule 25).

**Cache keys.** The flip is DECLARED as the first entry in
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`; the frozen drop declaration stays
`False`, so under capx D24-R option (b′-1) the armed default **enters** the
hash and takes its own key rather than silently re-using the pre-flip bundle —
the collision that ledger exists to prevent. Both pins advance: default
`cedadc285f8603b9` → `4c6b03ae098b6e3e`, bare backcast
`e006dfd7cef8bedd` → `8211c72bb1960adc` (dated cause blocks on the pins in
`tests/regression/test_persisted_identity.py`; cache-epoch ledger entry
2026-09-03 in `src/market_sim/results/cache.py`), and the ERCOT resolved poles
move with them. An explicit `fossil_announced_exits_enabled=False` still
equals the frozen declaration, is still dropped, and still addresses its
pre-flip bundle — measured, so control arms and the D42 legs are unaffected.
**Backcast is byte-identical** (the channel loads only in `mode="forecast"`),
so no keeper, sidecar, determination or dashboard row moves and nothing needs
re-scoring. Forecast/hindcast bundles solved at the pre-flip default record
the superseded posture and join the director's batched re-measure decision;
this lane re-solved nothing.

**Harness plumbing (required for the flip to be effective).**
`run_capacity_hindcast.py` pinned this field to its own `False` parameter
default on every invocation, which would have left the flip inert for the
entire hindcast lane. It now rides the None-drop dict — omit to inherit the
shipped default, `--no-fossil-announced-exits` for an explicit pre-Q30 control
arm (`argparse.BooleanOptionalAction`, the house pattern).

Record: `docs/handoffs/FINDING-capx-d44-fossil-dates-arm-2026-09-03.md`.

## 2026-09-02 — capx D35: FC-6 P2 gas leg re-scoped to the model's gas partition; neiso-t3 P2 re-scored artifact-only (no LP, no field, nothing armed)

The golden-2 P2 FAIL ("year 2050: wrong: gas_cc↓") was the instrument crossing
the CCS class migration on a 25-year pair, not a merit-order sign error
(`docs/handoffs/FINDING-capx-d35-p2-scope-2026-09-02.md`): the gas price is a
fuel-level driver, the LP comparative-statics inequality bounds the
gas-burning AGGREGATE and says nothing about one class, and on an evolution
pair the gas_cc / gas_cc_ccs split is itself a response to the driver.
`check_forecast_invariants.py` P2 now scores `gas↓` on TOTAL gas-fired
generation over `GAS_FIRED_FUELS` (the `data/fuel/_shared._GAS_FUEL_IDX`
mirror: gas_cc, gas_ct, gas_cc_ccs, gas_st), keeps coal↑ / price↑ /
objective↑ as they were, retires the per-class key to the row's evidence
block as a reported control, carries the per-year gas-fired series, and gains
`--paired-summaries` (P2 from committed `full_horizon_summary.json`, whose
energy block is the checker's own `_fuel_gen_mwh`; objective↑ reported as not
scored at that grain, never assumed). Controls: the unmodified scorer
reproduces the committed verdict with zero non-provenance diffs, and the
retired key at summary grain reproduces the committed FAIL string exactly.
Re-score: P2 PASS (gas-fired 36.53→35.36 TWh at 2050, falling in all 25
years), FC-6 FAIL→CAVEAT (T16-A battery row untouched), determination HOLD
unchanged; prior verdict preserved at `neiso-t3-pre-p2scope`. No other ISO
holds a committed P2 row. Rule 28 not triggered (no `ScenarioConfig` field).

## 2026-08-30 — capx D12: entry-screen scarcity basis adjudicated (no LP; one default-OFF field; nothing armed)

The two-scarcity-objects question the D11-R finding §4 escalated, answered
by exact arithmetic on committed objects
(`docs/handoffs/FINDING-capx-d12-scarcity-basis-2026-08-30.md`;
pre-declarations committed verbatim in
`PREDECL-capx-d12-scarcity-basis-2026-08-30.md`): the shipped thermal ENTRY
margin's realized-r reserve leg (prior solved year's post-solve ORDC adder)
is a cross-year phantom that fires exactly at post-tight-year steps —
entering-2024 control gas margins are NEGATIVE under the entering year's own
expectation on both committed bounds yet the screen built 6 GW, and the
D11-R exhaustion arm's entering-2025 repeats it at ≥4× the whole consistent
forward annuity. Everywhere else the basis choice changes nothing (no
committed sign moves; the B-walk reproduces the committed r-none L-1b walk
tranche-for-tranche). Shipped `ScenarioConfig.entry_forward_reserve_leg`
(GATED default-OFF, cache-key-registered at default — default key
`603c2498bf71d21d` unmoved, registered keys reconstruct): armed, the entry
screens' reserve legs read the entering year's OWN expected-ORDC adder from
the same instrument invocation as the energy leg, and the D11-R walk closure
`max(0, r + Δadder)` becomes the exact identity `r_walk = adder_current`
(gas half of `entry_margin_exhaustion` goes live, zero walk-code change).
Matrix row + all-shard cells added (ERCOT `O`, sisters `U`); Q8 decision
card in the finding §7 — arming is the owner's. Also repairs the
pre-existing `test_pipeline_prior` contract-set failure (D11-R's
`entry_reprice` was never added to it).

## 2026-08-22 — miso-176: M2M/CMP seam-class intake + binding-reality adjudication (no LP, nothing armed, keeper unchanged)

New curated datatype `miso-m2m-flowgates` (schema-first, data-intake
contract): MISO's public annual `M2M_Settlement_srw_YYYY.csv` — hourly
per-flowgate FFE + market flows + shadow prices + credits for the MISO–PJM
and MISO–SWPP seams, 2023–2025 (miso-77 §2a series). Mirrors gitignored
with sha256 README rows (bc_HIST precedent);
`scripts/data/{fetch,curate}_miso_m2m_flowgates.py`; rule-13 line fixed in
the schema header (FFE input-class in kind; shadow/flow/credit
ANSWER-class, validation only). The miso-176 no-LP measurement
(`_miso176_m2m_seam_binding.json`, prereg-first) verified the file's clock
against `rt_bc_HIST` on the NERC-ID join (r = 0.9934), measured PJM-seam
M2M binding CO-MOVING with MISO's 72 scarce hours (4–6× harder,
restriction-consistent, MISO over its own FFE on 67–82 % of binding rows),
and minted matrix cell `m2m_seam_entitlement_cap` = `G` (every zero-DOF
encoding refused: rule-13 conditioning + the miso-77 §5.2 apportionment
refusal). Evidence transfers to the standing coincident-peak seam-response
owner item. `FINDING-miso176-m2m-seam-binding-reality-2026-08-22.md`.

## 2026-08-17 — BLOAT-S2: Stage-2 (a)-only untrack executed — six evidence passes, −444.5 MiB / 144 files at tip

Executes the signed O2 grant (BLOAT-3 card, 2026-08-16). Six §4.8
BLOAT-A-grade evidence passes (`docs/FINDING-bloat-s2-evidence-passes-
2026-08-17.md`): per corpus, a consumer census with loud-vs-silent absence
semantics, golden+holdout overlap incl. the rule-22 vintage question, a
MEASURED retention window (live probes with negative controls), an exercised
fetch instrument, and the manifest plan. Untracked in per-corpus commits
(tree-sha-verified SHA256SUMS + README recovery sections; re-fetch-only
recovery — no pins): `storage-as-awards/CAISO` xlsx (−165.2 MiB), the
zero-consumer `data/raw/PJM` orphan (−107.1), the `campd-unit-level` 2018
vintage (−105.1 — 2019–2026 stay: solve-time year-keyed inputs, refuting the
prima facie 692.6 MiB), the `eia-930` per-BA long files + 2018 BALANCE
(−33.8 — BALANCE 2019–2026 and the hand-assembled `eia_*` files stay), and
the `iso-specific-transmission` PJM-2018 pair (−33.3 — the NP6-86 parquets
stay: no fetch instrument). `lmp-data` non-golden FAILED its pass (MISO
archive measured decaying; ERCOT/ zips are holdout scoring rebuild inputs)
and stays tracked whole. Golden-tier sparse list needed zero edits;
skip-when-absent verified like-for-like in a payload-absent worktree. The
baseline run also surfaced a pre-existing SyntaxError at origin/main —
`scripts/run_calibration.py` carried a duplicate
`reliability_floor_plant_exclusions` kwarg from the #4036 merge race,
breaking collection of 32 test modules and every calibration-solve import.
Twin fixes on main then collided and dropped the kwarg's `with_overrides`
application entirely (the restore brought back only the signature), leaving
the flag silently ignored by `run_year`; both defects were re-fixed upstream
mid-flight (the #4044 merge restored the wiring), so this PR ships no
run_calibration.py delta — FINDING §8 carries the genealogy. CLAUDE.md corpus
list updated; bloat plan §9 BLOAT-3 annotated EXECUTED; release-plan §8
entry. Post-merge proof: the first weekly golden-tier cron green.

## 2026-08-16 — BLOAT-2 closed: Class-E retention rule adopted; the point-4 bundle-parity sweep built into the CI parity gate

The four-point Class-E retention rule (bloat plan §7 item E2) was served to
the owner as the G1-style in-session card and **ADOPTED**; the text is written
verbatim with the adoption date into
`frontend/data/backcast/keepers/README.md`, now the rule's standing home.
Point 4's quarterly bundle-parity sweep — the one unbuilt mechanic — is built:
`scripts/check_registry_payload_parity.py` gains `check_bundle_retention`,
which FAILS any top-level `results/calibration/<bundle>` directory that no
retained registry sidecar's `bundle` field maps and that is not keep-required
(the §5.2 `_`-prefixed working/archive dirs, bundles referenced by a
`results/regression-goldens/*/manifest.json` capture record, and the
documented `KEEP_REQUIRED_UNMAPPED_BUNDLES` allowlist — empty at adoption;
root-level loose records and the `results/hindcast` /
`results/regression-goldens` roots are out of scope by construction, and the
keeper / ablation-referenced / structural-prior classes stay sidecar-mapped
via the prune immunity, needing no carve-out). The sweep runs inside the
always-on CI parity gate — a strict superset of the rule's quarterly cadence —
closing the last three-store drift channel. 10 new tests
(`tests/scoring/test_registry_payload_parity.py`); no data change. Both
checkers green at HEAD before and after: parity OK (15 runs checked, 15
bundle dirs swept) and `audit_keepers.py --check` PASS 0/0. D-ledger:
bloat plan §9 BLOAT-2 annotated CLOSED; release-plan §8 carries the entry;
only BLOAT-3 (Stage-2 charter) remains open of the D-8 successors.

## 2026-08-16 — BLOAT-3: Stage-2 charter decision card served and SIGNED — O2 staged (a)-only GO; story (a) alone admitted

Docs-only. `docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md` serves the
open D-ledger item BLOAT-3 (bloat plan §9) over the BLOAT-B-7 re-measured pool
at `04d1cf0`: adjudication pool 4,008.7 MiB / 1,487 files, takeable residual
≈ 3,311.9 MiB after the §4.2/§4.7 keep-verdicts, full untrack → tip
≈ 3.0 GiB. Because the 2026-08-16 history rewrite demonstrated that
history-as-archive is not durable under owner-authorized rewrites, the card's
central ruling is the RECOVERY STORY per corpus — (a) evidence-passed
re-fetch / (b) owner-held external archive / (c) explicit signed loss, with
pin-based recovery admissible only under a no-further-rewrite commitment —
before any untrack verdict. Options O1–O4 with O2 (staged (a)-only GO,
prima facie ≈ 1,133 MiB) recommended; decisions D1–D5; §0ar-3 pre-merge
checklist walked at HEAD (golden-tier sparse list needs zero edits;
skip-when-absent tests named as an unverified execution duty;
`hydrate_data.py` pin support conditional on D2). No untracking, gitignore
edit, data move, or workflow edit. **The card was answered in-session
(owner, all four rulings as recommended): D1 = O2 staged (a)-only GO;
D2 = story (a) alone admitted — no external archive, no loss route (a
corpus failing its pass stays tracked), no pin commitment (pins stay dead,
no hydrate pin support); D3 = §4.8 evidence passes authorized, golden-tier
proof = weekly cron green; D4 = DAM 2024+ out of the grant.** BLOAT-3 is
adjudicated; open follow-on: per-corpus evidence passes, then untrack PRs
for passing corpora only (prima facie ≈ 1,133 MiB). Verdict recorded on the
card, bloat plan §9/BLOAT-3, and release-plan §8.

## 2026-08-16 — BLOAT-B-8: post-rewrite aftercare — the 2026-08-16 history rewrite ledgered, the citation map recovered, every corpus recovery contract repaired, the pack re-measured

The owner executed the `cleanup-large-blobs.yml` history rewrite (run
31955205445, 15:17–15:49 UTC — an explicit decision superseding the Addendum
AQ NO-GO): 7,254 superseded blobs / 7,373.4 MiB stripped, integrity verify
PASSED, force-push landed. This aftercare lane (docs + metadata only) ships
the durable record `docs/FINDING-history-rewrite-2026-08-16.md`; the
reconstructed `docs/governance/citation-commit-map.txt` (95 load-bearing
commits old→new by unique identity match + 9 refs/pull-only self-maps, each
API-verified alive — the runner's own copy and the full filter-repo
commit-map were never archived), wired into `citation-tags.md` §8; the honest
cost measured per rewrite-prep §8: **926 of 929 formerly-resolving citation
tokens (2,492 occurrences) are dead in a fresh clone**, and `00abb60` is a
FALSE survivor (prefix-collides with the rewritten main tip — a wrong-commit
resolution, not a dead one). Every converted corpus's restore-from-pin
contract was repaired in place (pins `971eaa3`/`315a245`/`726f389d` dead;
twins `94f8e179`/`94b9cda5`/`4759a160` verified payload-free): re-fetch is
now the primary route everywhere, and the CAISO OASIS GRP dailies, the
pre-slim SCED raw columns (ERCOT-157 window) and the pre-slim SHA256
manifests are declared **unrecoverable from this repository** (GitHub
`refs/pull/*` salvage window recorded). Pack re-measured on fresh clones:
**5.46 GiB / 162 s full bare clone** (was 7.44 GiB / stalls), tip 8,777
blobs / 4.13 GiB packed, blobless recipe unchanged (3.5 s / 13.7 MB) —
`docs/fast-clone.md` + CLAUDE.md updated; NO-GO references annotated in
place (rewrite-prep FINDING, bloat plan §0, report-final §5). Release-plan
§8 carries the ledger entry. Greens at HEAD: registry/payload parity OK
(15 runs), `audit_keepers.py --check` PASS 0/0.

## 2026-08-15 — GOLDEN-TIER-FIX: `curate_emissions.py` runner OOM fixed (peak RSS 10.05 → 5.17 GiB, output byte-equivalent); the deferred golden-tier dispatch SPENT and GREEN (run 31913648051) — G3's evidence gate reopens

`curate_year()` held a full CAMPD year in pandas several times over (per-state
frame list + `pd.concat` copies, a `drop_duplicates` hashtable, a
`sort_values` whole-frame take, `write_clean`'s second full Arrow copy),
peaking **10.05 GiB RSS from 119 MiB of input** — the OOM that killed the
golden tier's standard runner in 2 of its 3 dispatches ever (report §4;
perf-recheck §1.2/§1.5). The assembly is now Arrow-side and streaming
(per-state cleaning unchanged; key-column-only stable sort +
first-occurrence dedupe; one-row-group chunks through the existing
`clean_io.write_clean_iter`; `validate_clean` untouched): **5.17 GiB peak on
the tier's 2023 inputs, 4.71 GiB on 2024**, wall unchanged. A memory
refactor, not a re-derivation — `[R-FROZEN-DERIVE]` output-equivalence
verified for both years: data region **byte-identical** (every page and row
group), row-group structural metadata equal,
`assert_frame_equal(check_exact=True)` + dtype equality over all
26,534,489 / 26,030,146 rows; the footer differs only in the `created_utc`
provenance timestamp (and the `ARROW:schema` blob embedding it). The single
authorized dispatch (decision 7; the B-1/B-2/B-5 duty deferred by the
BLOAT-B-5 sitting) was spent on the fix branch, whose base carries every
executed BLOAT-B prune: run `31913648051` — **GREEN in 11m33s** (emissions
step 1m31s), loud-failure guard PASS, zero data-missing skips, no corpus
restored, sparse list untouched.
Ledger entries: release plan §8 (2026-08-15 GOLDEN-TIER-FIX) + bloat plan §8
Close-out.

## 2026-08-15 — BLOAT-B-7: the re-measured WS6 close-out — tip 6,405.7 MiB (−36.5 % vs the BLOAT-A base), every §3–§7 item adjudicated, post-prune dry-run floor quantified, BLOAT-1 spent

The AFTER measurement the salvaged pre-prune baseline
(`docs/bloat-removal-report-2026-08.md`, #3976) was preserved for:
**`docs/bloat-removal-report-final-2026-08.md`**, measured at `04d1cf0` with
all five BLOAT-B data PRs merged. Tip **6,405.7 MiB / 9,204 files** —
−3,674.3 MiB vs the 10,080.0 MiB BLOAT-A base; the PRs' measured recovery
(3,737.1) plus organic growth (+62.8) closes the ledger exactly, landing
~315 MiB above the plan's ≈6.1 GiB full-sign-off trajectory with all
variances reconciled (PR-1 −805.2 / PR-5-A2 +566.9 are one already-zstd
codec fact booked from both sides; PR-3's target corpus grew 92.9→158.4 MiB
while BLOAT-B waited). Per-item executed/vetoed ledger complete: every
class-approved item executed, A2/B1b/B3 signed-and-executed, the two
C-touchpoint rows vetoed-kept and verified intact with their `hourly/`;
parity (70 runs) and `audit_keepers --check` green at HEAD.
`cleanup-large-blobs.yml` dry run `31912344135` (`dry_run=true`, the
REWRITE-HISTORY phrase never supplied) re-quantified the superseded-blob
pool against the salvaged 922.3 MiB / 3,974-blob floor: **7,053 blobs /
7,338.4 MiB removable** — ≈6,416 MiB of prune-created reclaim, attributed
item-by-item — and the **AQ NO-GO stands with its rationale inverted**:
those superseded blobs are now the archive behind every corpus README's
restore-from-pin contract. Also surfaced from the artifact record:
the golden tier's **first-ever green** (run `31867650665` at `c447199`,
post-PR-1/2/4, stock `curate_emissions.py` — the deferred B-1/B-2 dispatch
duty was in fact discharged; GOLDEN-TIER-FIX, unlanded at the measurement
commit, then delivered while this close-out was in flight and supplied the
post-PR-3/PR-5 green — see its entry above), and an **aborted real rewrite
attempt** (run `31907287115`, `dry_run=false` with the confirm phrase,
self-stopped by the citation-integrity verify — 9 cited commits; nothing
pushed). D-ledger: BLOAT-1 **SPENT → propose CLOSE**; BLOAT-2 open; BLOAT-3
open over the re-measured Stage-2 pool (4,008.7 MiB, takeable ≈3,311.9).
Release-plan §8 ledger back-filled with the missing BLOAT-B-1
(#3957/#3958) and BLOAT-B-4 (#3955) entries. Docs only.

## 2026-08-15 — BLOAT-B-5 (PR-5, #3978): owner-signed batch executed — A2 + B1b + B3 untracked (−2,518.5 MiB at tip, 763 payloads), C touchpoints vetoed; golden-tier dispatch deferred by owner

The owner answered the G1 item card in-session: **A2 / B1b / B3 SIGNED**, the
two §5.1 C-touchpoint rows **VETOED** (kept while the 2022 touchpoint loops
are live). Per-corpus commits in the merged PR-2 idiom — SHA256 manifests
tracked (B3's newly created over tree-sha-verified bytes; A2/B1b reuse
BLOAT-B-1's post-slim manifests), corpus READMEs with source tables,
past-retention statements, pin sha `726f389d` and `git restore` recovery
commands, gitignore payload globs (README/SHA256SUMS kept; the OASIS
SingleZip pattern keeps future pulls out by corpus design). The ERCOT-157
SCED window (323 shards), `ercot86_tail_days`, and the golden-listed CAISO
hourly aggregates stay tracked. No history rewrite; pack size unchanged. The
post-merge golden-data-tier dispatch is deferred by owner decision pending
the curate_emissions OOM fix lane (GOLDEN-TIER-FIX); the bloat plan's §8
PR-5 bullet and item sections carry the execution record.

## 2026-08-15 — BLOAT-B-6 close-out SALVAGED (PR #3954, superseded — not merged as written): the pre-prune baseline at `315a245` preserved — dry-run floor 922.3 MiB removable, golden tier broken (G3 evidence-blocked), D-ledger closures re-verified

Salvage of unmerged PR #3954 (head `f877d61`; the authoring session was lost
with the PR unmergeable against a moved main). The full report lands verbatim
under a supersession banner: `docs/bloat-removal-report-2026-08.md`. The PM
ruling it lands under (release plan §8, 2026-08-15 refresh): the close-out
measured `315a245` at ~02:00 and correctly reported BLOAT-B never executed /
0.0 MiB recovered — and was then overtaken the same morning when BLOAT-B ran
out of sequence at 05:38–05:39 (PR-1 #3958 −739.8 MiB, PR-2 #3956
−361.8 MiB, PR-4 #3955 script rotation; ≈1,101 MiB recovered at tip;
PR-3/PR-5 remain). The headline is therefore superseded; what is salvaged is
what stays true:

- **The pre-prune floor, quantified** (`cleanup-large-blobs.yml` dry run
  `31857841269` at `315a245`; the `REWRITE-HISTORY` confirm phrase never
  supplied, and the run's own step record proves the guard held): **922.3 MiB
  removable (3,974 blobs) vs 9,901.7 MiB protected (6,032), disjointness
  PASSED**, 17.92 GiB mirror pack — a history rewrite at that tip reclaims
  8.5 % of in-scope bytes / ~5 % of the pack, the standing NO-GO's
  arithmetic confirmed from a second angle. Measured hours before the first
  prune merged, this is the exact floor a post-prune dry run subtracts from.
- **The golden data tier does not work — G3 is evidence-blocked** (report
  §4): `golden-data-tier.yml` red twice at the same step (`31767823203`,
  `31857842156`), cause reproduced locally — `curate_emissions.py --years
  2023` peaks at 9.07 GiB RSS from 119.1 MiB of input parquet (three
  whole-year materializations in `curate_year()`,
  `scripts/data/curate_emissions.py:268–291`) and OOMs the runner, reported
  as "shutdown signal" exit 143. Independently corroborated the same day by
  PERF-A (10.04 GiB stock peak measured; 6.45 GiB low-mem prototype,
  `docs/handoffs/perf-recheck-2026-08.md`). The tier has never reached its
  own tests; a pre-prune green must be recorded before any post-prune red
  can be attributed.
- **D-ledger closures re-verified at `315a245`** (report §7): D-3 CLOSE AS
  SHIPPED (parity checker green — 69 runs, 0 orphans; `live_bundles`
  immunity intact), D-4 CLOSE AS EXECUTED (zero root-level zips), D-8
  SUPERSEDE by BLOAT-1/2/3 — plus the correction that **D-5 was already
  closed by DEBUG-A on 2026-08-14** (patch archived to `patches/archive/`,
  moved not deleted, keep-required honored); the bloat plan §9 line now
  carries that annotation.
- **Plan §2's measurement method re-validated** (report §3): the
  golden-tier sparse globs re-evaluated at tip reproduce the keep-required
  block at 1,512.8 MiB / 1,043 files, matching the plan to within the five
  files added since.

Still open, deliberately not attempted in the salvage: the re-measured
close-out (BLOAT-B-7) against the post-prune tip, and the
`curate_emissions.py` memory fix (PERF-B's surface). Docs-only — no data
file, corpus, bundle, script or workflow was moved, slimmed, converted or
deleted.

## 2026-08-15 — BLOAT-B PR-1: the SCED corpus slimmed in place (plan §3 A1 + §4.1 B1a)

WS6 of `docs/model-audit-release-plan-2026-08.md`, executing
`docs/bloat-removal-plan-2026-08.md` §8 PR-1. All 996 corpus shards, the 27
`rtcb-format-2026/` parts and the four loose probe-day extracts rewritten by
`scripts/data/slim_ercot_dam_disclosure.py --sced-only`: column projection to
the re-audited consumer union (corpus KEEP 79→108; extracts 180; rtcb NO
projection — the read adapter serves every native column, card D/D1) +
zstd-15. **739.8 MiB recovered (21.3%)**; values/rows/order untouched; every
consumer derive byte-identical pre-vs-post (the ERCOT-157 acceptance; 12
artifacts + the 27-part rtcb adapter fingerprint). The measured recovery sits
below the plan's ≈1,450 estimate because the 2026-08 re-uploads were already
zstd — the precedent ratio was measured against SNAPPY originals. Pre-slim
SHA256 manifests committed alone (971eaa3, merged via PR #3957); post-slim
manifests + README provenance in the PR. Committed derived artifacts are
byte-untouched; the pre-existing frozen-artifact drift on the 2024/25-window
wall/faststart/storage surfaces (the ercot-183 basis switch) is recorded in
the PR, not altered. A2 (2024+ window conversion) stays un-executed
(needs-sign-off, Stage-2 call).

## 2026-08-14 — DEBUG-A: debug sweep (solve-neutral) — fast tier 6→0 ambient reds; D-5 closed, PJM input-clock defect confirmed and chartered to DEBUG-B

WS2 of `docs/model-audit-release-plan-2026-08.md`. Every seed row
dispositioned (triage table: `docs/handoffs/debug-sweep-2026-08.md`). Landed,
all solve-neutral: the six ambient fast-tier reds fixed — a real
config-serialization bug (YAML round-trip binds lists to tuple-typed
`ScenarioConfig` fields, so a reloaded sidecar hashed to a different
`cache_key` than its writer; fixed by `__post_init__` coercion, pinned default
key `603c2498bf71d21d` proven unmoved), the FF-1A `retirement_rule` D-1
fallout pair (probe pinned to `legacy` per the `test_capacity.py` pattern),
and the unrouted `data-profiles.yaml` roundtrip case; the `gen_caisoNNN`
placeholder allowlisted (un-reddening `refactor-guards`); `tools/launcher.py`
baseline re-pointed keeper-shard→registry→bundle (was a guaranteed post-solve
crash on the absent `run10_peak85`); the 10 unfiled top-level test files filed
into the tiered layout; the sibling-import census re-measured 105/91 → 74/50
and made re-runnable (`ci_refactor_guards.py --sibling-census`); the stale
README known-failing note retired. **D-5 closed:** the PJM M-1 patch is
archived (must not be applied verbatim — the committed parquet's region
family was healed post-diagnosis, so the patch would double-shift it), and
the still-live defect — `NG: *` fueltype family one hour early in BOTH 2023
and 2024 (July solar centroid 10.91/10.94 vs [11.5, 12.3]; wind/solar/gas
diff-lag +1) plus four live `datetime_beginning_ept` read sites — is
chartered with an updated transform in
`docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md` (full-span PJM
re-solve + same-session registration). CI health: the wall-to-wall cancelled
record explained (pull_request-only triggers + merge-fast branch deletion);
`golden-data-tier.yml` cron "never fired" because its first Monday is
2026-08-17 — its first-ever run manually dispatched per §6 decision 7;
branch-protection memo (exact G2 ruleset, two by-design-red jobs excluded)
at `docs/governance/branch-protection-memo-2026-08.md`.

The cross-ISO mechanism matrix's one-file shape (six-char `cells: "KKKKKK"`
strings, position = ISO) made every parallel lane edit the same line — 21 lanes
in three days, three union-merges and one silently-lost edit on the MISO leg
alone. Mirroring the 2026-07-19 keeper sharding: mechanism-level rows stay in
`docs/codebase-site/data/mechanism-matrix.js` (base, edited only by the
rule-28(c) PR that adds a mechanism); each ISO's cell verdicts / fc / `ev`
citations / keeper+gates stamps move to `docs/codebase-site/data/`
`mechanism-matrix/<ISO>.js` — **a lane's rule-28 duty is now a one-file edit
and two ISOs discharge it concurrently with zero shared-file edits.** The page
assembles base + shards client-side (`mechanism-matrix-assemble.js`); Python
readers use the new stdlib `scripts/lib/mech_matrix.py::load_merged` (legacy
monolith shape). Migration proven mechanical: the pre-shard file is frozen as a
fixture and `tests/unit/config/test_mechanism_matrix_shard_migration.py`
asserts split∘assemble reproduces it exactly per mechanism × ISO (cells, fc,
citations; 1,266 cells, zero verdict changes — Node-verified on the real page
path too). `check_mechanism_matrix.py` validates the sharded store (full
coverage per shard, errors name the ISO shard file) with the 28(c) enforced
gate intact; hook/docs/CLAUDE.md rule 28 re-point WHERE (duties unchanged).
Also: `frontend/data/backcast/{manifest,benchmark,completeness}.js` are now
gitignored (deploy regenerates them into `_site` from committed sidecars and
never read the committed copies — local `file://` preview needs
`python scripts/build_manifest.py`, as the forecast side already does), and
the `scenarios.py` cache-key ledgers document a per-ISO-cluster insertion
convention (comments only). Handoff:
`docs/handoffs/house-3-matrix-shard-2026-08-11.md`.

## 2026-08-05 — ercot-167: the storage AS SOC reservation built, 2023-probed, A/B-tested, and OWNER-PROMOTED TO ERCOT KEEPER (2026-08-05-run167b-soc-reserve) — the session's REJECTED-AS-ARMED precommit verdict carried openly

Matrix §5.1 item 10 executed (owner-directed, separate-2023-first per the distinct 2023 scarcity
design). New mechanism `ercot_storage_as_soc_reserve` (+ derive
`scripts/data/derive_ercot_storage_as_products.py`): battery SOC floored at the measured AS award ×
the published per-product duration, deployment-netted, pin-reachability-clipped (two probe-found
infeasibilities localized exactly — LP-bounds dump + per-unit feasibility LP — and fixed
structurally; precommit amendments 1–2, zero fitted scalars). 2023 passes every gate (scarcity-hour
discharge 666→520 MW vs SCED-measured actual 423); kills fired on 2024 C3a (+1.4 pp, concentrated
on the known maintenance-season fabricated-spike days) and one 2025 spurious hour ($43 graze
adjacent to two newly-captured real tail hours) — verdict REJECTED-AS-ARMED, re-gate the identical
arm after the 2024 availability defect lands. Runs `2026-08-05-run167a-soc-control` +
`2026-08-05-run167b-soc-reserve`; `FINDING-ercot167-storage-soc-reserve-ab-2026-08-05.md`.

**Promotion addendum (same day):** owner directive "Promote" on the surfaced record, under the
standing structural standard. Attestation generated (`scripts/gen_ercot167_attestation.py`,
n_entries 11→12 measured/published, zero scalars; the three rubric-v3.0 C3c model-class entries
carried with updated magnitudes 61/181, 25/53, 3/31); re-scored C6 PASS / C3c ledgered CAVEAT ×3;
determination NOT-YET on {C3a 2023 −32.2%, C3b 2023 0.603 + 2024 0.206 (a NEW +0.006 scorer-basis
band cross, same spike-day root, carried as an honest limit), C7 lignite cv 0.331}. Keeper shard,
status part, matrix header + item-10 + def-registration all re-stamped; `audit_keepers --iso
ERCOT` PASS; ercot165 stays as the immediate-prior comparison; standing re-gate condition
unchanged.

## 2026-08-05 — ercot-166: ERCOT 2023 diagnosis triage; Oak Grove conduct solved from the disclosure corpora; rubric v3.0 model-class ledger kind and the ERCOT C3c caveat (no LP, no solve, keeper unchanged)

Owner-directed. Full record `results/calibration/FINDING-ercot166-2023-diagnosis-triage-2026-08-05.md`;
log entry ercot-166; matrix §5.1 re-stamped with three new owner-chartered queue items (10–12).

- **Rubric v3.0** (`scripts/calibration_verdict.py`, `docs/calibration-determination-rubric.md`):
  a second ledgered caveat kind, `ACCEPTED MODEL-CLASS LIMITATION` (`"kind": "model-class"`
  exceptions entries) — supporting-tier-only, fail-closed against load-bearing/protective
  criteria, same ≤3 ledgered budget, requires owner decision + exhaustion record + open residual
  lane. Three new scorer tests.
- **ERCOT C3c ledgered across 2023–2025** (owner decision 2026-08-05): three model-class entries on
  the `ercot165_unpooled_share_B` attestation; keeper re-scored in place — C3c FAIL→CAVEAT ×3,
  C6 UNATTESTED→PASS (stale promotion-day metrics), determination stays NOT-YET with its basis
  narrowed to the 2023-only C3a/C3b + C7 lignite. Registry sidecar annotated; `status/ERCOT.js`
  rebuilt; `audit_keepers --iso ERCOT` PASS.
- **Diagnosis headlines** (measured, no solve): the 2023 −30 % is Aug (−46.7 %) + Sep (−48.7 %)
  tail mass; the model's ORDC-shortfall regime matches the actual scarcity calendar and its ~$1
  duals match measured RTORPA — the miss is the energy stack (ercot-160→163 attribution
  confirmed); storage nets +661 MW over actual in the >$1000 hours while the model sheds load in
  4 hours reality served; the year-round 17–19 h underrun is NOT a clock artifact (three
  DST-window-only data defects found and ranked, none price-moving); **Oak Grove's Aug–Oct 2023
  overnight backdown is solved** — a seasonal RT offer repricing (TPO top step $4.50 → $60.30 at
  full HSL, zero AS awards, no DAM position) that the keeper's 2024/25→2023 offer-curve
  extrapolation cannot see; the delivery-2023 SCED corpus (ercot-157, publication-month-keyed)
  dissolves the ERCOT-143 "no 2023 SCED" closure premise and re-arms the per-plant offer derive
  as a rule-23 re-identification (queue item 12).

## 2026-08-04 — xiso-3: the cross-ISO shared-stem matrix backlog CLOSED, and line-anchor decay is now gated (no LP, no solve, all six keepers unchanged)

The last rule-28(c) debt, and the successor nyiso-121 named. **Both halves of
the matrix-gap census now read zero for all six ISOs, and both are ratcheted.**

- **45 shared fields registered on 19 existing rows.** Every SHARED
  (non-ISO-prefixed) `ScenarioConfig` field a designated keeper *arms* with no
  matrix cell anywhere — **54 (ISO, field) pairs**, nine armed in two ISOs at
  once — now carries a literal sub-scalar registration in its family row's
  `def`, each home chosen on a **cited code read site** rather than on theme.
  Ratchet `shared_armed_on_keeper` CAISO 5 / ERCOT 14 / MISO 17 / PJM 18 →
  **0 0 0 0**; **169 → 169 rows, zero new**; every `cells:` string
  byte-identical, **no cell minted anywhere** (a census may mint a `U` and
  nothing more, rule 28(d)).
- **The cause was the caiso-161 §2 abbreviation defect, three more times.**
  Seven registrations existed only as abbreviations no literal-matching checker
  could resolve — including a bare **`etc.`** standing in for three armed fields
  at once, and `conditional runs` written with a space instead of an underscore.
- **New: a standing anchor-resolution gate.** nyiso-121 found all 20 MISO line
  anchors stale and filed a checker as a suggestion; measured file-wide here,
  **163 of 167 checkable anchors did not resolve — only 4 did**, most off by
  900–1,400 lines because `scenarios.py` grew under them. 161 were repaired
  mechanically (verified digits-only: with every `:\d+` normalised the texts are
  byte-identical), and `scripts/check_mechanism_matrix.py` gains an anchor leg
  (field-style, row-id and file-in-range checks), a shrink-only ratchet
  `docs/codebase-site/data/mechanism-matrix-anchors.json` (**now empty**) and a
  **`--fix-anchors`** repair path so a `scenarios.py` PR fixes drift with one
  command. Existence is gated first, preserving the deliberate `miso_pjm_lmp
  :2914` defect *quotation*. Caveat recorded in the docs: the gate proves an
  anchor points at the field it **names**, never that the named field is the
  right one.
- **Seven armed-but-dead pairs found and filed, none adjudicated.** Measured on
  **construction** (no LP, no solve, no dual; built twice at one HEAD,
  `np.array_equal` on float32): four ERCOT coal-passthrough scalars and three
  CAISO CT-drag coefficients are **provably unreadable on their own keepers**,
  so those `run_config.json`s overstate what the solve read. All five arms
  Δ = 0.0 exactly with all five positive controls separating. The CAISO result
  is *consistent* with that family's existing CAISO `R`.

## 2026-08-04 — ERCOT-160: the item-7 / item-8 data intakes (no LP, no mechanism, keeper unchanged)

Data-intake session on the ERCOT lever queue. MISO's C7 COAL_PRB item was
checked first and remains data-blocked (the miso-104 ex-ante coal-contract
tonnage ask has not landed), so precedence fell to ERCOT items 7/8.

- **Item 7's blocker dissolved.** The queue recorded that a station→area
  crosswalk "does not exist in-repo". ERCOT *publishes* one — **NP4-160-SG
  "Settlement Points List and Electrical Buses Mapping"**
  (`reportTypeId=10008`) — and it had simply never been fetched. New
  `scripts/data/fetch_ercot_settlement_point_mapping.py` intakes it to
  `data/raw/ercot-network-model/` (1.2 MB, **committed**), writing each member
  as its **exact published bytes with a sha256**, because ERCOT ToU §5 permits
  redistribution only if contents are unmodified. Committed rather than
  gitignored because MIS retention here is ~31 days: only the current
  network-model version is ever reachable, so an un-committed vintage is lost
  permanently. Every consumer must report its own match rate against its target
  year.
- **Item 8(a) delivered at 98.7 % of the training span.**
  `fetch_ercot_60day_sced_gen_resource.py` gains `--resource-types`,
  `--delivery-range`, `--shard-by-month` and `--skip-existing` — scope and
  plumbing only. CT-scoping cuts a delivery day to 15.1 % of its rows
  (0.51 MB parquet vs ~90 MB unscoped CSV), which is what makes a ~700-day span
  affordable; month sharding bounds memory and makes it resumable. Delivery
  2024-01-24…2025-12-31 landed CT-only in `data/raw/ercot/SCED-CT/` (gitignored
  + README + SHA256SUMS). **14 days (delivery 2024-01-10…2024-01-23) are
  unreachable** — they fall between the committed corpus and the MIS rolling
  window — and are reported, never interpolated. The rule-22 holdout guard was
  not relaxed and refused 2026 delivery days live.
- **Item 8(b) is BLOCKED and is the only thing still blocking the lever.** The
  licensing check ERCOT-147 §4 demanded is now a reproducible probe: EIA's free
  weekly spot table carries Waha/Katy/Agua Dulce/Carthage at **zero** mentions
  (Chicago scores 6, Henry Hub 10), and ERCOT's own catalog has 5,773 products
  of which none is a fuel price series. The series exists only behind
  NGI/Platts/Argus — an owner licensing decision. Logged as blocked, **not**
  inferred as zero and **not** substituted with Henry Hub.
- **Item 8(c) reshaped by a grain correction.** The crosswalk's `site` column
  holds a site prefix for `CC_REGULAR` but the full resource name for
  `CT_PEAKER` (165/165 CT rows match a corpus resource name, 0/165 a site
  prefix), so "165 CT_PEAKER sites" counts resources and the "~150-site hand
  crosswalk" was mis-sized in kind. Most CT resources already carry a candidate
  row, making the bulk an adjudication rather than an identification.

No LP solve, no `ScenarioConfig` field, no mechanism tested, no matrix cell
verdict, no dashboard run; keeper unchanged at `2026-08-03-ercot158-pool-arm`.

## 2026-08-03 — FFR-SC input refreshes: ATB derivation pin → 2024 v4.0.0 (no-op); NYISO demand anchor → 2026 Gold Book

Two rule-23 `[R-FROZEN-DERIVE]` re-derivations, each triggered by a **source-data
vintage change and nothing else** — no residual was consulted and none moved.

- **ATB derivation pin `v3.0.0` → `v4.0.0`** (`curate_nrel_atb.DERIVATION_PINNED_VERSION`),
  closing audit FR-20's open half after FFR-PB landed the v4.0.0 extract. **A measured
  no-op on every committed constant**: `derive_entry_costs_from_atb`
  (`NEW_ENTRY_COSTS`, `TECH_COST_MULTIPLIERS`) and `derive_cost_benchmark_envelope`
  (envelope table + multipliers, `STORAGE_TECHS` li-ion, `OFFSHORE_WIND_PARAMS`,
  `derive_egs_fom` = 163.4) return byte-identical output under both versions, so
  `constants.py` is unchanged. Of 3,858 rows on an identical key index, 56 differ
  materially and **all** are `Geothermal`/`DeepEGSFlash`/`Moderate` (CAPEX
  +1.50…+6.14 %, Fixed O&M +0.13…+2.00 %) — a class no derive script reads; the
  other 16 are ~1e-14 float noise. `test_parse_defaults_to_the_pinned_derivation_version`
  is rewritten against `DERIVATION_PINNED_VERSION` instead of the literal `v3.0.0`,
  so a future pin move re-points it rather than failing it.
- **`DEMAND_GROWTH_RATES["NYISO"]` re-derived from the 2026 Gold Book**
  (NYISO Load & Capacity Data Report, released April 2026), landed at
  `data/raw/NYISO/2026-Gold-Book-Public.pdf` — closing FF-G4 §8-D4 item 3, which
  flagged the 2025 edition this row cited as stale. Basis is now **formulaic**
  (rule 5 `[R-NO-MAGIC]`) instead of the FF-1C "~1.8 %/yr" reading: per-case CAGR
  of Table I-1a's own Energy-GWh series, near = 2026→2030, long = 2031→2050 —
  the identical construction `DEMAND_GROWTH_RATES_VINTAGES` already uses for every
  NYISO row. mid `near 0.018 → 0.0122`, `long 0.012 → 0.0127`; low
  `0.008/0.006 → -0.0024/0.0028`; high `0.030/0.020 → 0.0263/0.0196`. Two rule-14
  `[R-ACCURATE]` improvements beyond the level: low/high are now the edition's own
  Lower/Higher Demand series rather than prior-vintage band ratios re-centred on the
  mid (the "exact published low/high tables" FF-1C recorded as unavailable are in
  this edition), and the low case's **negative** near rate is the Lower Demand
  forecast's real sign. `parameters.json` / `parameter-citations.md` re-cited to the
  edition, table, URL and file sha256.
- **MISO's 2026 LTLF anchor is NOT refreshed** — `cdn.misoenergy.org` and
  `misoenergy.org/planning/…` both return HTTP 403 to a non-browser client, exactly
  the bot-wall FF-G4 §8-D4 item 5 marks ⬇. Handed forward as a manual download; the
  row keeps its cited Sept-2025 LTLF basis rather than an uncited estimate.

Full session record incl. the CAISO transmission-expansion A/B:
`docs/handoffs/ffr-sc-transmission-ab-2026-08-03.md`.

## 2026-08-03 — ERCOT-157: NP3-965 delivery-2023 corpus re-upload verified + wired; 2023 SCED blocks completed (pool/wall/steam)

The ERCOT-151 §4 data blocker is resolved: the owner re-uploaded the 60-Day
SCED Gen Resource corpus for delivery-2023 to `data/raw/ercot/SCED/` (315
publication-month shards, 187-column raw schema). Session verification: all
shards readable, all 365 delivery days of 2023 present at full weight (35.8M
rows); two failed upload batches (deliveries 2023-04-10..19, 2023-09-08..17)
identified by shard forensics and re-supplied same-day. Full record:
`docs/calibration-log/ercot.md` ERCOT-157.

- **`derive_ercot_sced_offer_wall._sced_source_files`** (shared by the CC/CT
  wall, steam wall and fast-start pool derives): scans both corpus locations
  (`data/raw/ercot/` + `data/raw/ercot/SCED/`, subdirectory copy wins name
  collisions) and supersedes the legacy sample-day extracts only on MAJORITY
  delivery-month coverage (≥7/12 by the exact 60-day publication lag) — the
  re-upload's edge months (pubs 2024-01..03, 1/12 of delivery-2024) must not
  silently replace 2024's sample-day basis. Historical selections unchanged
  (July full corpus: 12/12/10). Tests:
  `tests/curation/test_sced_corpus_selection.py` (5).
- **`derive_ercot_faststart_pool`**: `_load_year` sources via the shared
  helper (streaming with a light live frame; full columns only for the
  OFFQS/OFFNS pool rows); the artifact gains its 2023 CT year block (the
  ERCOT-151 charter deliverable; 2024/2025 blocks verified byte-identical —
  the charter's derive check). Cell `ercot_faststart_pool_offer` stays `O`:
  arming remains owner-gated (ERCOT-89 §7 step 2), LOYO at arming time.
- **`ercot_sced_offer_wall_condbinned.json`**: the committed 2023 block was
  the post-purge partial slice (deliveries Jan–Oct 2023 only, per its own
  `ercot105_added` note); refreshed full-year from the re-upload — matches
  the 2026-07-21 full-corpus verification (8,751 intervals/bin 0). Net-load
  bins 5–6 (the scarcity tail) byte-identical; 2022/2024/2025 blocks
  byte-identical.
- **`ercot_sced_offer_wall_steam_condbinned.json`**: first ST 2023 block
  (16 fleet plants, none absent). Measure-first, no apply path — changes no
  solve. One steam artifact test year-scoped: the mid-band RT>DAM q90
  invariant is strict on its measured years (2024/25); 2023 sits at parity
  in bin −3 (−0.14%).
- **Corpus slimmed in place** (owner directive, same session): all 315
  shards projected to the audited `SCED_KEEP` 79 columns at zstd-15 —
  896.1 → 490.5 MB (45% saved). Verified lossless for consumers: per-shard
  rows/ranges match the raw baseline (315/315), full delivery-day scan
  reproduces exactly, and both the pool artifact (entire JSON) and the
  wall's 2023 block re-derive byte-identical from the slimmed shards. The
  108 dropped columns for 2023 survive only in the owner's local raw
  archive (2023 is past free MIS retention); the raw-blob history purge is
  the owner's follow-up.

No solve, no registration, keeper unchanged (`2026-08-02-ercot150b-zonal-anchor`).
Surfaced owner decisions: keeper full-span re-solve on the completed inputs
(ercot98 pattern) and the standing pool arming gate.

## 2026-08-03 — FFR-SA: FF-G4 Option-B electrification load-shape layers (FR-16), DEFAULT OFF

Implements the decided design of
`docs/handoffs/ff-g4-load-shape-design-memo-2026-07.md` (§8-D1 = Option B):
additive EV + heat-pump end-use layers over the weather-8760, folded in by the
generalized DC-relocation algebra. Session handoff (DC seam reconciliation,
DOF ledger, T0 smoke, owner arming box):
`docs/handoffs/ffr-sa-load-shape-implementation-2026-08.md`.

- **New scenario axis** `electrification_path` (default **"off"**) +
  `electrification_percentile` (0.5) — the `datacenter_load_path` grammar;
  backcast/hindcast-coerced off in `__post_init__`; registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` (pinned default cache_key `603c2498bf71d21d`
  measured unmoved) and `TIER_TAGS`; mechanism-matrix row
  `electrification_layers` in the same PR (rule 28c).
- **`data/datacenter.py::add_load_layers`** — ONE fold-in for all additive
  load layers (rule 19): DC block = layer #1, electrification layers share the
  energy-invariant relocation under a single sum-of-layers guard; the DC-only
  path is **bit-identical** to `add_datacenter_block` (tested), so the armed
  DC "mid" forecast default is unchanged. Both runner seams switched. The
  CX-4 zero stub `electrification_shape` is deleted (rule 26).
- **`constants.ELECTRIFICATION_LAYERS`** adoption anchors (incremental to the
  weather-year base, {} where unsourced): NEISO `heat_pump` mid
  {2026: 0, 2035: 7,165 GWh} from the ISO-NE 2026 CELT HEF; `ev` ships `{}`
  everywhere — a citable charging profile is an open D4 intake, and a layer
  with anchors but no profile source FAILS CLOSED.
  `HEAT_PUMP_BALANCE_POINT_C` = 18.3 °C (NOAA/EIA 65 °F degree-day base).
- **Heat-pump profile** = heating-degree hours on the run weather year's
  measured NOAA GHCN daily zone temperatures, Parton & Logan (1981) diurnal
  bridge (the on-main miso-101 reconstruction). Winter-morning ridge emerges
  from the weather; energy relocation is invariant to machine precision.
- **Probe arm** `run_full_horizon.py --electrification-path`; T0 NEISO/PJM
  2026-2028 armed-vs-off smoke registered in the handoff §4. Citations added
  to `frontend/data/parameters.json` (+ registry regen, which also
  auto-registered 56 pre-existing uncited constants — `validate_parameters.py`
  is green again). Tests: `tests/unit/data/test_electrification_layers.py`.
- **No default moved; no keeper touched** — arming posture is the owner's box
  (memo §8-D2), pending NEISO T0 evidence review.

## 2026-07-24 — CAMPD outage backfill 2018-2026 (all six ISOs) + EIA-923 non-CAMPD fallback (backup data)

Out-of-training DATA-INTAKE session (owner-authorized, logged in
`frontend/data/backcast/calibration-complete.json` `intake_log`). No dispatch
solve, no scoring, no dashboard registration; validated no-LP only.

- **Standard CAMPD unit-outage extracts backfilled to the full 2018-2026 span
  for every ISO** — `data/raw/campd-unit-outages.csv` (ERCOT) and
  `campd-unit-outages-{CAISO,PJM,MISO,NYISO,NEISO}.csv`. Previously most ISOs
  carried only 2023-2025 (ERCOT/PJM 2022+2026), so an out-of-training backcast
  ran with zero outages. Re-derived via
  `scripts/data/derive_campd_unit_outages.py --iso <ISO> --years 2018..2026`
  (default flags; the detector is per-year-independent). Every file's
  already-committed in-sample rows (2023-2025, plus 2022+2026 for ERCOT/PJM)
  asserted **byte-identical** before write, for every ISO except CAISO. CAISO's
  committed 2023-2025 windows were on the pre-2026-07-19 phantom-outage detector
  (its regenerate-lane was still open); on explicit owner instruction CAISO was
  **re-derived in full** with the current detector like the other five ISOs, so
  its 2023-2025 rows changed (2023 439→640, 2024 405→622, 2025 509→733). This
  updates the CAISO keeper's in-sample outage input and closes the regenerate-
  lane — flagged for a CAISO re-audit/re-solve (not solved or scored here). 2026
  is Q1-only (CAMPD Q2-2026 unposted).
- **New default-OFF EIA-923 fallback** (`--eia923-noncampd-fallback`) for fleet
  plants ABSENT from CAMPD (non-CEMS units the gross detector is blind to). A
  month at or below `EIA923_FALLBACK_OUTAGE_RATIO` (0.10) × the plant's own
  median positive-month net generation becomes a full-stop availability window
  (a measured physical quantity, per-plant, no residual tuning — rules 13/14).
  Written to SEPARATE companion files `campd-unit-outages-e923-{ISO}.csv` tagged
  `capacity_source="eia923"` that the outage loader does **not** read by default
  (backup only; wiring is a later scored session). 2025/2026 EIA-923 filings lag
  (2025: 3,427 plants; 2026: Jan-Apr), so many candidates get no window —
  counts logged per year, never silently dropped.

## 2026-07-23 — ERCOT-98: 2023 HSL → published NP6 GEO, zonal HSL sidecars, AS-plan CST clock fix

Two measured-input alignment fixes + one new data capability (the 2023
summer scarcity-tail attribution lane —
`docs/DIAGNOSIS-ercot-2023-summer-tail-attribution-2026-07.md`):

- **2023 ERCOT HSL now builds from ERCOT's own NP4-742/745 GEO reports**
  (owner upload, `data/raw/ercot-hsl/np6/2023/`), superseding the UMass
  partial-footprint reconstruction. Delivered totals match EIA-930 directly
  (wind 108.01 vs 107.99 TWh, solar 31.88 vs 31.87), so
  `renewables.hsl_potential_mw`'s footprint reconciliation is now a **no-op
  for every year** (tests updated to assert the no-op path). Solar's +13.7 %
  vs EIA-923 is a 930-vs-923 scope difference, not an NP6 over-count.
- **`build_ercot_hsl.py` emits per-region zonal sidecars**
  (`ercot_<year>_hsl_zonal_hourly.parquet`, long format
  `hour/fuel/region/gen_mw/hsl_mw`) from every region-resolved upload —
  GEO wind (panhandle/coastal/south/west/north), GEO solar
  (centerwest/…/centereast), NP4-732 wind load zones (lz_*) — with COP-HSL
  semantics documented, partial coverage kept NaN (never interpolated across
  month-scale holes), `--zonal-only` refresh mode, and a sum-of-regions
  cross-check (2023: 1.0000 for both fuels). Diagnostics input; not yet a
  dispatch input.
- **`scarcity.ercot_as_plan_requirement_mw` CPT→CST clock fix**: ASPLANNP433
  stamps are Central Prevailing Time; unconverted they landed one hour late
  through every DST season, misplacing the evening reserve step-down at the
  scarcity-formation hours (same defect class as the NP6 HSL builder's fixed
  lag). DSTFlag-disambiguated conversion; winter placement and levels
  unchanged. Feeds all four `ercot_multiproduct_as_coopt` families.
- Probe `scripts/probes/ercot98_tail_attribution_measure.py` reproduces the
  attribution: all three chartered suspects (RE over-credit, AS under-hold,
  West/Panhandle deliverability) REFUTED against measured data; the 135
  missed 2023 tail hours are offer-driven SCED λ (RTORPA p50 $1, PRC p50
  5,765 MW) — the offer-formation successor lane.

## 2026-07-20 — FF-G3: forward net-CONE evolution (design + grounding, default-inert)

Forecast-only capacity-price surface; **no default flip, no LP solve, pricing
seam untouched, backcast byte-identical** (default `cache_key` cache-neutral —
unchanged with the field added; the field is dropped from the hash at its
`"hold_last"` default). Full methodology, per-ISO grounding, delta ledger,
divergence quantification, field survey, and owner-decision box:
`docs/capacity-price-forward-methodology-2026-07.md` +
`docs/handoffs/ff-g3-net-cone-forward-2026-07.md`.

- **Designs the explicit forward-evolution rule** for the net-CONE anchor beyond
  the last published vintage (today `resolve_demand_curve_vintage` silently
  HOLDS-LAST for 25 forecast years, a live bias — PJM's cleared 2028/29 net-CONE
  is +34% over the 2027/28 value on disk). New `ScenarioConfig.
  net_cone_forward_escalation` (`"hold_last"` default | `"reindex_net"` |
  `"reindex_gross"`), in `_CACHE_KEY_OPTIONAL_FIELDS` (default cache-neutral),
  TIER-2, `__post_init__`-coerced to `"hold_last"` in backcast.
- **`constants.forward_net_cone_anchor(iso, year, escalation, *, rate,
  eas_offset_per_kw_yr)`** — pure resolver on `resolve_demand_curve_vintage`;
  escalates only years past the last published vintage; `None` for CAISO/ERCOT.
  `constants.NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO` — cited per-ISO real rate,
  **0.0 for all** (field finding: ISOs escalate GROSS CONE by a construction
  index and RE-NET the E&AS offset each year; net-CONE is never indexed directly,
  and Brattle's out-year guidance is inflation-only, so sharp recent moves are
  step re-anchorings, not a real trend).
- **Scope guard:** the escalation is NOT wired into the pricing seam
  `capacity_price_per_firm_mw_yr` (FF-2C owns the seam wiring + per-ISO
  `capacity_market_clearing` flips); `forward_net_cone_anchor` is exercised by
  tests + the offline divergence quantification only.
- **Researched forward vintages filed as MANUAL DOWNLOADS NEEDED** (not encoded —
  the machine-readable sources are bot-walled here; rule 13 forbids guessing):
  PJM 2028/29 (325.69 $/MW-day UCAP), NYISO 2026/27, MISO PY2026/27 (per-LRZ +
  RBDC), ISO-NE FCA 19 2028/29 (regime-superseded — the FCM is terminating for a
  prompt/seasonal market with no published parameters). sha256-pinned where a PDF
  was obtained (`data/raw/capacity-market/demand-curve/README.md`).
- `tests/test_net_cone_forward.py` (19): hold_last ≡ the seam's current anchor
  (byte-identity), central-rate collapse, reindex arithmetic, no-escalation
  at/before the last vintage, registry hygiene, config cache/backcast invariants.

## 2026-07-20 — Fuel-forward trajectories: AEO2025 → AEO2026 vintage bump + near-term triangulation (FF-G2)

Forecast-only fuel-price refresh; **no LP formulation change, backcast
byte-identical** (the trajectories are read only in `mode="forecast"`; the sole
backcast reader is the neighbor-price seam, which reads gas ≤2025 historical
actuals held fixed). Full grounding + near-term AEO-vs-STEO-vs-strip
triangulation + owner-decision box: `docs/fuel-forward-methodology-2026-07.md`.

- **Vintage bump (CLAUDE.md rule 23 — source-data edition change).** Re-derived
  `HENRY_HUB_TRAJECTORIES`, `COAL_PRICE_TRAJECTORIES`, `OIL_PRICE_TRAJECTORIES`
  from **AEO2026** (was AEO2025) via `fetch_eia_aeo.py --aeo-year 2026` →
  `derive_fuel_trajectories.py`. AEO2026 is in real **2025$** (was 2024$) and
  renamed its central case Reference → **Counterfactual Baseline** (`cb2026`).
  Both scripts are now vintage-aware (`SCENARIOS_BY_AEO`, `--aeo-year`).
- **Gas near-term corrected.** Mid Henry Hub 2026 rises $2.74 → **$3.88**, 2027
  $2.62 → $3.62 — closing (and slightly overshooting) the ~$1/MMBtu low bias vs
  the EIA STEO ($3.67 for 2026). Gas 2023/2024/2025 historical actuals unchanged
  (backcast seam). Gas 2050 low/high spread widens ($2.75/$13.67), lifting the
  forecast-only `uncertainty.GasMarginal` AEO σ floor 0.555 → 0.843.
- **Coal/oil** re-vintaged whole (forecast-only); coal is a dollar-year-invariant
  ratio to each ISO's `COAL_PRICE_BASE` anchor (anchor year 2024 → 2025). Oil
  eases modestly. Nuclear **unchanged** (EIA-UMAR source not updated, rule 23).
- **New benchmark datatype** `data/raw/fuel-forward-benchmarks/`: EIA STEO Henry
  Hub snapshot (API-fetched) + the EIA free NYMEX feed (stale-flagged) +
  sha256-pinned README with a MANUAL-download row for the current CME strip;
  fetch script `scripts/data/fetch_fuel_forward_benchmarks.py`. Benchmarks are
  context only, never fit targets (rule 1).
- **Consistency tests** `tests/test_fuel_trajectory_consistency.py` (new, 10):
  constants == AEO2026 derivation; gas historical actuals fixed; nuclear
  unchanged. Two value-tests updated for the new vintage
  (`test_uncertainty`, `test_fuel` dual-fuel). Full suite green.
- **Owner decision (findings-first, no default flip):** the vintage bump alone
  closed the near-term gap, so a strip/STEO near-term blend is now low-value —
  recommended posture is pure AEO2026 paths (methodology doc §6). Nothing beyond
  the refresh implemented pending the owner's pick.

## 2026-07-19 — Transmission expansion: committed-instrument registry + gated forward TTC channel (FF-G1, WAVE FI)

The forecast's network topology was frozen at base-year statics for all 25
forecast years; board/regulator-committed builds were invisible. Forecast-only
channel, **GATED default-off** (`transmission_expansion_enabled`, in
`_CACHE_KEY_OPTIONAL_FIELDS`; backcast/hindcast coerced off) — **every
existing cache key, backcast keeper, and default forecast is unchanged**
(verified: pre-change vs flag-off NEISO 2026 result frames + objective exactly
equal). Standing methodology: `docs/transmission-expansion-methodology-2026-07.md`;
session record: `docs/handoffs/transmission-expansion-grounding-2026-07.md`.

- **New raw datatype** `data/raw/transmission-expansion/` (schema
  `transmission-expansion.schema.yaml`, lib `scripts/lib/transmission_expansion/`,
  curation `scripts/data/curate_transmission_expansion.py` with live
  topology-resolvability validation, sha256-pinned sources + page-marked md
  conversions via `scripts/data/fetch_transmission_expansion_sources.py`):
  35 rows across all six ISOs, closed instrument vocabulary
  (energized/under_construction/approved_funded — roadmap excluded), per-row
  rule-14 `mapping_note`, deltas additive to each ISO's base-static vintage
  (new `data.transmission_expansion.TRANSMISSION_BASE_STATIC_VINTAGE`, kept beside its sole consumer).
- **Applied deltas (10 rows)**: NECEC +1,200 MW (NEISO HQ_import→North +
  simultaneous cap, energized 2026-01); CAISO SWIP-North +1,117.5 MW ISO
  entitlement on the WECC simultaneous cap (2028); MISO LRTP Tranche 1
  published per-LRZ CIL uplifts (+658/+1,443/+492/+166/+2,327 on the five CIL
  groups, 2030); ERCOT 765 kV STEP WTX-export re-rate +3,500 MW split 8:3
  per the WESTEX convention (2032). Where an instrument publishes **no MW**
  (all six PJM RTEP corridors, Propel NY, Gates–Los Banos No. 3, IV–NoSONGS),
  rows carry delta 0.0 — documented, dispatch-inert, never guessed (rule 5).
- **Consumption seam**: `src/market_sim/data/transmission_expansion.py`
  (fail-loud W2-E/G12 loader cloned from confirmed-retirements;
  `apply_transmission_expansion` returns the same object when nothing applies)
  wired at the runner's per-year `year_ttc` seam with per-year interface-group
  rebuild; `scripts/run_full_horizon.py --transmission-expansion`.
- **T0 smoke (NEISO 2026–2028, ON)**: 2026 applies HQ_import→North 900→2,100
  and simultaneous 3,850→5,050; flows re-route onto the new wires
  (HQ→Boston mean 1,612→1,930, HQ→CT 1,118→1,430) while total HQ energy stays
  tranche-depth-limited (1,987.6 MW mean both legs) — measured confirmation
  that the import-tranche energy-depth seam is the named V1 follow-up
  (methodology §6.1), alongside the ERCOT import-direction split, the
  hindcast information gate, and the no-published-MW re-rates.
- Registered as **WAVE FI** in the FF plan (§1.2-11 + §6) with the FF-G2…G5
  companion prompts (fuel forwards, net-CONE vintages, load-shape memo,
  nuclear registry) and gap-register §3.11 rows.

*(Core-wiring correction, 2026-07-26: the DATA half above landed 2026-07-19,
but the engine half — the `ScenarioConfig` gate + coercion + cache-key entry and
the runner's per-year seam — shipped as the unapplied patch
`docs/handoffs/patches/ff-g1-core-wiring.patch` and was applied only on
2026-07-26, under fast-tier escalation D2. Until then the flag did not exist and
everything data-side was inert, exactly as commit `221c5e10` warned. The
default-off / cache-key-stable claims above hold as written and were re-verified
at apply time: `cache_key(ScenarioConfig())` still pins `edbc1b103207170a`.)*

## 2026-07-19 — New-build capacity costs: cross-source grounding, literature-envelope ranges, storage/offshore/EGS/H2 derivation-lock

Forecast-only cost-input grounding (capacity-expansion entry screens); **no LP
formulation change, backcast byte-identical** (evolution is `mode="forecast"`
gated). Full methodology + citations:
`docs/new-build-cost-methodology-2026-07.md`.

- **New raw benchmark datatype** `data/raw/new-build-cost-benchmarks/`:
  cross-source overnight-cost/FOM table (`benchmarks_2026.csv`) transcribed
  from five downloaded-and-markdown-converted documents — EIA/Sargent & Lundy
  Jan-2024 capital-cost study (AEO2025 basis), EIA AEO2026 EMM assumptions
  (Apr 2026, Tables 3-4 incl. 25-region costs), EIA AEO2025 LCOE report,
  Lazard LCOE+ v18.0 (Jun 2025, incl. LCOS v10 and the $2,400-2,600/kW CCGT
  market-quote case), Brattle 2025 PJM CONE report (Apr 2025) — with QA'd
  conversions committed under `md/`, sha256-pinned re-download script
  (`scripts/data/fetch_cost_benchmark_sources.py`), and per-row
  `in_envelope`/`verified` flags (unreachable primaries — DOE Liftoff, PNNL —
  are recorded `verified=0` and never enforce).
- **`TECH_COST_MULTIPLIERS` capex low/high re-derived as the published-cost
  literature envelope** (`scripts/data/derive_cost_benchmark_envelope.py`,
  asserted by new `tests/test_cost_benchmark_envelope.py`): min/max across
  ATB 2024's own three cases ∪ the verified benchmark rows, normalized to
  2026$ — replacing FF-1E's ATB-internal ratios, which were degenerate for
  mature techs (gas_ct 1.0/1.0 → 0.6246/1.0372; gas_cc ±1% → 0.5852/1.6783).
  Mid stays the pinned ATB 2024 Moderate (defaults byte-identical; ATB 2024
  verified to be the FINAL ATB edition, so the pin is current).
- **Derivation-locked the hand-set cost tables** onto committed sources:
  li-ion `STORAGE_TECHS` (4hr $1,140→$1,810.3, 8hr $2,280→$3,154.3, 12hr
  $3,100→$4,498.4 via ATB's exactly-linear duration split, + FOM);
  `OFFSHORE_WIND_PARAMS` (fixed $4,200→$6,312.3 @2026, floating
  $5,500→$10,243.8 @2030 — the FF-1E-flagged re-derivation);
  `GEOTHERMAL_PARAMS` EGS FOM 0→163.4 (ATB NF-EGS Flash; capex $5,000 kept on
  the DOE-Liftoff level, decorative "ATB" label corrected);
  `HYDROGEN_TURBINE_PARAMS` ($1,400/$1,800 → $1,499.0/$1,661.2 = ATB gas
  hosts × the AEO2026-measured H2/frame-CT premium; FOM onto the same basis).
  ATB extract extended with the four EGS classes (append parts 11-12,
  FF-1E parts byte-untouched).
- Parameter-citation registry regen run locally (`--check` green) but its
  push is deferred to the standing registry-reconcile chore (1.5 MB pair
  exceeds a safe single-call API payload; no new top-level keys, so
  `validate_parameters.py` is green against main's registry — verified).
  Data register + `data/raw/nrel-atb/README.md` updated.
- **Collateral main fix:** `runner.py` used the `UNSET` sentinel without
  importing it (miso-76 B, `2ad50aa`) — a `NameError` killing EVERY
  forecast-mode run on main (backcasts don't traverse `run_scenario_iso`).
  One-line import fix, found by this session's T0 forecast smoke.

## 2026-07-17 — Consolidate CAMPD outage detection: delete the facility-summed layer, per-unit detector is the sole source (all ISOs)

Core-infra refactor + data-derive; **no LP solve**. Enables the two ERCOT/PJM
keeper reruns that follow.

- **Shared detector library.** The CAMPD outage-detection primitives
  (`detect_outages`, `detect_outages_eventbased`, `filter_revealed_outages`,
  `high_load_mask`, `_runs`, the partial-plateau `_detect`, and the
  ERCOT-79-tightened constants — `REAL_RUN_CF`, `ST_GAS_CF_PEAK/MIN_OUTAGE_HOURS`,
  `EVENTBASED_CYCLING_GROUPS`, `FULL_STOP_OVERRIDE_*`, `HIGH_LOAD_PCTL`,
  `MIN_INMERIT_HOURS`, `WINDOW_DAYS`) moved from the deleted
  `scripts/derive_campd_outages.py` into a new `scripts/lib/outage_detect.py`,
  imported by `derive_campd_unit_outages.py`, `derive_partial_outages.py`, and
  `probes/_outage_gate_audit.py` (byte-parity verified against the old detector).
- **Facility layer deleted.** `git rm scripts/derive_campd_outages.py`,
  `data/raw/campd-outages.csv`, `data/raw/campd-outages-PJM.csv`. `fleet.py`:
  removed the facility-overlay block (the hard `availability=0` per plant);
  `unit_outage_derate_factors` is now the SOLE CAMPD outage layer for every ISO.
  `outages.py`: removed the `outage_masks_for_year` / `_build_outage_masks` /
  `_clean_outage_masks_for_year` / `_qualifying_plant_codes` / `OUTAGES_CSV` /
  `default_outages_path` / `MIN_OUTAGE_SPAN_HOURS` path. `curate_outages.py`:
  dropped the facility source, so the `outages` clean datatype is unit-grain (no
  `unit_id="ALL"` rows). `ScenarioConfig.historic_outage_overlay` is now INERT
  (retained for run_config / legitimacy-diagnostics back-compat; it no longer
  changes a solve — PJM was already unit-only, ERCOT loses the facility layer).
- **Rationale (ERCOT-79).** The facility detector summed a plant's units,
  hiding single-unit outages, and folded a daily-cycling combined cycle's
  overnight-down gaps into phantom summer outages
  (`results/calibration/FINDING-ercot79-phantom-outage-2026-07.md`). The per-unit
  detector is event-based for load-following classes and never had that bug.
  Only ERCOT + PJM used the facility layer; the other four ISOs already ran
  unit-only.
- **Coverage preserved (rule 23/26 — justified from data, not residual).** The 6
  ERCOT ST_GAS plants in the old facility file but absent from the unit extract
  (Graham 3490, Spencer 4266, Stryker Creek 3504, Trinidad 3507, Ray Olinger
  3576, Mountain Creek 3453) are exactly `ST_GAS_PEAKER_PLANTS` — economic
  dispatch, no overlay, no coverage lost. The one PJM facility-only plant (50279
  Archbald) is a ~44 MW peaker-dominated cogen whose facility "outages" are
  economic weekly cycling (phantom); its only qualifying component is a 20 MW
  ST_GAS unit — immaterial, correctly dropped. `CT_CHP` stays excluded from the
  derate (like `CT_PEAKER`): a CT down-window cannot be certified a forced outage
  vs out-of-merit-at-peak on CEMS alone (unlike baseload coal/CC), so the
  event-based+revealed-availability filter does not cleanly separate the two; the
  detector still writes CT_CHP windows for audit but the derate skips them.
- **Data re-derived (measured CEMS + EIA-930, no solve).** ERCOT
  `campd-unit-outages.csv` (2,702 → 4,910 rows), PJM `campd-unit-outages-PJM.csv`
  (6,275 → 7,033 rows), and PJM `campd-unit-outages-short-PJM.csv` (290 → 286
  rows) on the consolidated detector. The standard extracts grow because the
  committed CSVs predated the ERCOT-79 detector fix (`258bfa0`, which changed the
  shared filter but never re-derived the CSVs): the corrected
  revealed-availability filter + 5-day full-stop override now keep the
  shoulder-season dead-stops the old overlap filter dropped. All backcast +
  holdout years regenerated (allowed data-derive). The ERCOT plant-grain partial
  (`campd-partial-outages.csv`) re-derives byte-identical (its `_detect` moved to
  the lib unchanged and it applies no revealed-availability filter).
- **Known follow-up — `--partial-windows` × ERCOT-79 filter (flagged, not
  fixed).** Re-deriving the PJM unit-grain partial extract
  (`campd-partial-outages-PJM.csv`) with the current detector EMPTIES it: a
  partial plateau is a unit running at a *depressed ceiling* (committed windows
  p50 derate 0.56, i.e. ~56% — cf ≫ `REAL_RUN_CF`), so the ERCOT-79
  `filter_revealed_outages` "ran during high-load ⇒ available ⇒ drop" clause
  (correct for full stops) wrongly discards every partial plateau. This is a
  pre-existing latent bug the re-derivation surfaced, not introduced here. Rather
  than ship an empty file and lose 76 real partial windows (rule 11/26), the
  committed `campd-partial-outages-PJM.csv` is **left unchanged**; the
  `unit_partial_outage_windows` overlay is default-OFF and used by no keeper, so
  nothing scored is affected. Follow-up: give the `--partial-windows` path a
  partial-appropriate revealed-availability test (keep a plateau where the unit
  stayed *below its normal ceiling* through high-load, rather than dropping it
  for running at all).
- **Tests.** Deleted the facility-clean parity test (`test_consume_outages.py`)
  and the facility-overlay tests (`BuildMasksFilterTest` etc.); added a
  single-unit-plant-fully-zeroed test for the unit derate. Outage suite green
  (the one pre-existing NEISO data/test mismatch is byte-identical to `main`).

## 2026-07-17 — MISO: Midwest sub-regional reserve-holding family (miso-71) — new gated reserve mechanism, registered as a rule-1 KEEPER CANDIDATE (keeper swap owner-only)

- **Model:** new `ScenarioConfig.miso_midwest_subregional_reserves` (GATED,
  default off; CLI `--miso-midwest-subregional-reserves`). Appends ONE
  operating-reserve family over the 5 physical Midwest zones
  (`reserve_config.MISO_MIDWEST_ZONES`), `reserve_class 0` nested inside the
  market-wide RBDC. Requirement = the measured hourly Midwest (North+Central)
  cleared OR reservation (`data.miso_reserve_requirements` new `"MISO-Midwest"`
  leg) when `miso_measured_reserve_requirements` is on, else the within-region
  MSSC; a single shortfall step prices at the published `MISO_RPE_DEMAND_VALUE`
  ($200/MWh, 2024 SOM §III.B). Closes the congestion-blind market-wide family's
  phantom-South-parking gap. Zero fitted scalars. Also: an env-gated
  (`MARKET_SIM_RESERVE_DUAL_DUMP`, default off) reserve-dual diagnostic sidecar
  in the per-year persist (per-family duals + per-zone reserve MW; never touches
  any scored output); `build_dof_ledger` enumerates the family as a
  measured-physical DOF entry (main 25/2, base 24/2); `pipeline/kwargs.py`
  co-opt log labels the Midwest family correctly.
- **Result:** mechanism-only (main − same-box base) — C3b IDENTICAL
  (0.079/0.124/0.184, R1 veto held), C3c 1/7/1 vs 1/6/1 (in-window +1),
  reserve fidelity clean (R2), no Jan-2024 engagement (R3); fail set = the
  keeper's {C1, C3a-2025, C3c} with no gated regression. The C3c-2025 deep tail
  stays open on the honest leg-(b) measured-requirement-dip lower bound.
- **Docs realigned:** `docs/multi-iso/miso-reserve-coopt.md` (Midwest family in
  Model mapping + miso-71 Results bullet), `docs/multi-iso/
  miso-scarcity-posture-design-2026-07.md` §B (marked UN-BLOCKED/EXECUTED with
  the two revised premises), `docs/calibration-log.md` (2026-07-17 miso-71
  entry). New tests: `TestMisoMidwestDesign`, `TestMisoMidwestReserveLP`,
  `tests/test_miso_reserve_requirements.py`.

## 2026-07-16 — NEISO: v2.7 RT-basis ledger-accuracy re-check — no determination change (CWC holds), but the neiso-59 C3c ledger's winter-only framing is corrected to the measured RT hour-set (keeper unchanged, no solve)

- **Issue:** the three `price_tail` entries on
  `results/calibration/neiso59_cc_hr_regate/calibration_attestation.json`
  (carried verbatim from the neiso-55/56 lineage) still read "DA-expressible"
  and attributed the whole tail gap to WINTER oil-parity formation — the
  2026-07-10 Limb A session's seasonal correction never reached the
  attestation, and the v2.7 RT-judged hour-set contradicts it: 2024's RT tail
  is 7/8 summer with zero DA/RT overlap; 2025's is 11 summer + 2 shoulder
  transients vs 7 winter (6 hours DA-visible, Jun-24 wave); 2023's is 10
  winter + 5 summer.
- **Fix (documentation, scorer-only):** entries rewritten to the RT basis
  with the per-year hour-set decomposition, preserving the still-true
  model-side facts (oil-parity cap, dormant winter build, static-requirement
  co-opt dual $0); the 2025 entry now surfaces the un-promoted Limb A
  (neiso-57) engagement on the Jun-24-2025 DA-visible event and its pending
  LOYO-gated owner promotion decision. `metrics.json` refreshed; `status.js`
  rebuilt — determination unchanged (CALIBRATED-WITH-CAVEATS), all six ISOs
  hold. Full anatomy: calibration-log 2026-07-16 NEISO entry.

## 2026-07-16 — NYISO: the v2.7 C3c-2024 RT-tail miss addressed by documentation — 12-hour anatomy verifies the B1 frontier, under-tail ledgered on the nyiso-62 attestation; NYISO NOT-YET → CALIBRATED-WITH-CAVEATS (keeper unchanged, no solve)

- **Investigation (no build):** all 12 actual 2024 RT>$300 hours carry
  ORDINARY as-enforced reserve requirements in the measured #1344 series (no
  condition-varying increment fires; the Jul-6/Jul-15 TSA zeroing windows do
  not cover the event hours), 9/12 cleared DA < $215, and 8/12 are
  weekend/holiday hours — RT-only forecast-miss/commitment-state transients,
  the B1 data-blocked residual (formal NYISO Market Operations request) plus
  the out-of-representation DA−RT wedge. The 2026-07-11 frontier designation
  is re-verified hour-by-hour under the RT basis; building a mechanism would
  be residual-fitting (rules 11/26).
- **Ledger (scorer-only):** new `price_tail`/2024 exceptions entry on
  `results/calibration/nyiso62_cc_hr_regate/calibration_attestation.json`
  (same B1 measured-input limitation already ledgered on C3a/C3b-2024);
  stale `_open_items` item (4) marked superseded by the v2.7 RT gate.
  `metrics.json` refreshed (`--write-metrics`); `status.js` rebuilt — C3c
  2024 FAIL → ledgered CAVEAT (1 of 3 budget), NYISO
  **CALIBRATED-WITH-CAVEATS**; every other ISO determination holds.
  Full anatomy: calibration-log 2026-07-16 NYISO entry.

## 2026-07-16 — Rubric v2.7 (owner amendments, second of the day): C3c gates on the actual RT hourly scarcity tail for EVERY ISO (DA = report-only diagnostic); C5b/C5c storage criteria REMOVED from the rubric outright

- **Scorer (`scripts/calibration_verdict.py`, RUBRIC_VERSION 2.6 → 2.7):**
  (a) C3c gates every ISO on the committed RT hourly tail (`rt_gt`); the DA
  count becomes the non-gated `da_diagnostic` row everywhere and the per-ISO
  `TAIL_BASIS` switch (v2.6(a), ERCOT-only RT) is deleted — basis parity
  restored, now on RT. (b) `score_storage`/`score_storage_shape` (C5b/C5c),
  their tolerances (`STORAGE_TOL`, `STORAGE_SHAPE_R_FLOOR/MIN_CV`) and the
  v2.6(c) `TIER_RETIRED` tier are removed: EIA-930 storage-dispatch data is
  not reliable enough to be a calibration gate (owner). Storage numbers stay
  committed payload/bench diagnostics on the run pages; the v2.6(b)
  observed-months bench honesty rule is unchanged.
- **Docs/UI:** rubric doc header+§0/§C3c/§C5/§2/§5/§8 + v2.7 history entry;
  methodology doc criteria table + version table (v2.5/v2.6 backfilled);
  `build_status.py` rubric/benchmark/methodology rows; calibration-status
  page criterion order; `derive_actual_tail.py` + committed
  `tail/actual_tail.json` note (counts untouched); renderer comments.
- **Re-score (scorer-only, no re-solve; `status.js` rebuilt):** ERCOT-73
  unchanged (CWC — already RT-gated); PJM-114 stays CALIBRATED (2024 tail
  9 h vs RT 18 h = 0.50×, on the band edge); NEISO-59 stays CWC (ledgered);
  CAISO-90/MISO-67 stay NOT-YET; **NYISO-62 flips CWC → NOT-YET** (C3c 2024:
  model 3 h vs RT 12 h = 0.25×, undocumented — the old DA actual was 0 h and
  passed small-count). An honest new open item surfaced by the re-basis, not
  a regression.

## 2026-07-15 — ERCOT-66: measured storage-capability re-basis (60-Day disclosure non-OUT HSL) — phantom-evening defect fixed; candidates registered NOT-YET (exposed 2024 under-pricing); keeper unchanged

- **Data intake:** new `scripts/fetch_ercot_60day_gen_resource.py` (NP3-966-ER
  daily bundles over the free MIS API) lands deliveries 2025-11-02..12-31:
  `60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2026_Jan-Mar.parquet` plus
  the NEW `..._ESR_Data_2026_Jan-Mar.parquet` family — at the RTC+B go-live
  (delivery 2025-12-06) storage leaves Gen_Resource_Data (no more PWRSTR rows)
  and reappears as combined `ESR` resources in a new per-day CSV. 2025
  deliveries now complete; the Oct-2023 hole is permanent on the free path
  (documented; EIA-860 fallback window).
- **Derive (rule-23 frozen):** `scripts/derive_ercot_storage_capability.py` →
  `data/raw/ercot-storage-capability.csv` — hourly ISO-wide battery capability
  (non-OUT PWRSTR/ESR HSL, model clock; 2,881/6,541/11,428 MW mean 2023/24/25);
  reproduces the summer-availability audit's evening reference points exactly.
- **Model:** `ScenarioConfig.ercot_storage_capability_measured` (default off,
  ERCOT backcast-gated) — `model.storage.ercot_storage_capability_caps`
  re-bases battery power caps on the measured series (EIA-860 stays the
  zone-split + duration basis; uncovered hours keep EIA-860; forecast keeps
  EIA-860 + planned pipeline). Applied before the M1 award subtraction at the
  run_calibration storage seam. Parameter registry regenerated; 4 new tests.
- **Runs:** `2026-07-15-ercot66-storage-rebasis` (A-only) and
  `...-endog` (+ endogenous energy-vs-AS split) registered, both 2023-2025,
  both NOT-YET: the design-target phantom windows collapse onto measured
  capability (Aug-2024 VOLL/shed eliminated, model max 2,859/1,870 vs actual
  3,060; Jul 30-31 2025 1,944 → 251 vs 243) and 2025 throughput moves toward
  measured (4.11 → 4.33/4.14 vs 5.46 TWh), but removing the phantom scarcity
  exposes pre-existing 2024 under-pricing (C3a-2024 −6.4 → ~−14%;
  May/Nov/Apr) — the rule-14 root-cause lane, chartered. **Keeper PROMOTED
  same day (owner sign-off "Promote A-only"):** `2026-07-15-ercot66-storage-rebasis`
  supersedes ercot63-gas-bridge on rule-1/14 structural faithfulness, honestly
  NOT-YET; ERCOT dashboard pruned to keeper-and-later (standing directive).
  Full workings: the two 2026-07-15 ERCOT-66 calibration-log entries.

## 2026-07-15 — All-ISO LMP scoring-clock fix (scorer-only): actual hourly parquets rebuilt on the model's chronological calendar; all 33 registered payloads re-paired in place; shift-invariant metrics verified unchanged

- **Scorer/data:** `scripts/derive_actual_lmp.py` now indexes every
  `actual_lmp_hourly_<ISO>.parquet` on the model's CHRONOLOGICAL calendar
  (row k = k-th UTC hour after local standard-time midnight Jan 1, standard
  Feb 29 dropped; `_STD_TZ` + `_std_hour_index`) instead of the reports'
  DST-prevailing wall labels, which paired every hourly comparison
  (`lmpDeltaHr` heatmap, scarcity-overlay monthly MAE, hour-of-day residuals)
  one real hour off for ~5,600 DST hours/year in every ISO
  (`docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md`
  §1 — ERCOT 2024 JJA hourly r 0.55 → 0.94 on re-pairing, verified). The DST
  fall-back hour's two instances now occupy their own real slots (no
  averaging), no spring-forward hour is NaN'd. Per-ISO readers: PJM uses the
  export's own UTC column; ERCOT resolves the ambiguous hour by the workbook
  "Repeated Hour Flag"; NYISO disambiguates duplicated fall-back stamps by
  row order; NEISO reconstructs positionally within each day (the `02X`
  repeated-hour row, previously silently dropped, is kept); CAISO indexes
  its OASIS UTC stamps directly. MISO (`scripts/derive_miso_hub_lmp.py`,
  `fetch_neighbor_lmp._densify_central`) maps its fixed-EST hub reports by a
  constant −1 h to fixed CST — no DST logic — and `derive_miso_hub_lmp.py`
  now re-emits the system parquet (INDIANA.HUB, the verified committed
  composition) alongside the zonal one. Parquet writes MERGE by year, so
  out-of-training holdout blocks (NYISO 2018-2022/2026, NEISO 2020-2022)
  stay byte-frozen (still old-clock; re-derive under authorization — noted
  in the holdout equivalency register). New `--parquet-only` flag rebuilds
  parquets without touching `actual_lmp.json` (byte-identical this change;
  its raw-row means are clock-invariant).
- **Dashboard:** all 33 registered run payloads re-paired in place
  (`new_delta = old_delta + actual_old − actual_new`, exact to the render's
  int16 rounding — the slim committed bundles cannot re-render off-machine;
  includes the same-day `2026-07-15-pjm-111-cc-reconcile`, rendered against
  the old actuals); C3c fallback `ordc.hoursGt200.actual` recomputed (only
  CAISO-2023 moved, 21 → 59 — a stale-semantics catch-up, not a clock
  effect; verdict-inert). `actual_tail.json` re-derived byte-identical;
  `build_status.py` verdicts identical; `manifest.js`/`benchmark.js`
  regenerate byte-identical. The re-pairing exposes model-side phase defects
  previously masked — NYISO/CAISO DST-only, PJM/CAISO/MISO 2025-uniform —
  filed as follow-up input-clock lanes (2026-07-15 calibration-log entry has
  the full tables).
- **Tests:** `tests/test_derive_miso_hub_lmp.py` updated to the
  chronological convention.

## 2026-07-13 — ERCOT-65 negative-price epoch pair: both premises corrected, PTC vintage scoping built (probe-inert), wtx recorder defect fixed, trough/spread lane at frontier

- **Model:** new default-off gate `wind_ptc_vintage_offers` (ISO-agnostic) —
  the wind dispatch offer becomes `-PTC_statutory(year) x EIA-860
  PTC-window-eligible capacity share[zone, month]`
  (`data/renewables.py::wind_ptc_eligible_monthly_share` +
  `policy/ira.py::wind_ptc_vintage_dispatch_offer`; statutory $28/29/30 for
  2023-25 in `constants.WIND_PTC_STATUTORY_USD_PER_MWH`, IRS FR notices)
  instead of the flat `-ira_ptc_wind` on every MW. Wired through both
  orchestrators + the forecast runner (D-5 parity), meta/recorded-cfg
  mirrors, `--wind-ptc-vintage-offers` CLI. 13 unit tests. **Probe verdict
  (rule-16 2023 ladder, bundles deleted): dispatch-byte-identical;** only
  the Panhandle epoch dual deepens -26.00 -> -27.03 (96.5% in-window fleet);
  West's -14.8 blend never prices (West wind is never marginal — the
  relief-valve topology). Kept as the recorded closure, default off.
- **Discovery/fix:** the WP-B `ercot_wtx_curtailment_driver` has been LIVE
  in every ercot42+ lineage solve — the generic `prb_overrides` channel
  (applied last in `run_year`) carries `true` and stomps the explicit
  tri-state kwarg, while the `run_calibration_full` recorder applied the
  override in the opposite order and mis-wrote `driver: false` into
  `run_config.json`. Recorder now mirrors the live order (+ loud channel-
  conflict warnings in both paths); the ercot63 keeper + ablation twin
  `run_config.json` corrected (annotated `_record_corrections`), keeper DOF
  ledger gains the omitted depth pair (0.1004/0.1637). No solve changes
  (probe byte-evidence in diagnosis §9).
- **Adjudication:** `negative_renewable_offers` on ERCOT is rule-25 refused
  (it would only push solar to the CAISO $20 REC value); the trough/spread
  lane is AT FRONTIER — frontier block drafted in the calibration log for
  owner sign-off; remaining named lever is the West/Panhandle topology
  split (own charter). Keeper `2026-07-12-ercot63-gas-bridge` unchanged.

## 2026-07-13 — ERCOT floor-scoped LSL markdown: built, probe-adjudicated provably inert (ERCOT-64)

- **Model:** new default-off gate `ercot_offer_surface_lowcurve_floorscoped`
  (ERCOT-only) — the measured committed-CC LSL bid (the frozen ERCOT-62
  `offer_curve_dam_lowcurve_condbinned.json` quantiles) applied to the gas-CC
  committed tranche ONLY in the gas commitment bridge's own floored
  plant-hours (`data/fleet.py::build_ercot_offer_surface_lowcurve_floorscoped_markdown`),
  keyed on the bridge floor mask (never the v2 P0-online gate). New pairing
  seam `pipeline/commitment.py::build_ercot_gas_bridge_p1_preps` computes the
  bridge floor ONCE per P0 result and shares it across the P1 fleet hook and
  the `p1_bid_adjust_prep` bid hook, in both orchestrators; mutually exclusive
  with the tranche-wide v2 and hard-requires the bridge (fail loud). 13 unit
  tests. **Probe verdict (rule-16 2023 ladder, bundles deleted): provably
  inert** — the bridge floor clips at the committed-tranche bound on every
  bridged plant, so the markdown's entire window is pinned and the probe is
  byte-identical to the ercot63 keeper (price/dispatch max |Δ| = 0.0). The
  LSL price-side enumeration is closed; ERCOT-65 chartered on the
  negative-price epoch pair (`negative_renewable_offers` + the West-corridor
  curtailment topology lane). Keeper unchanged.
- **Docs realigned:** CLAUDE.md + model-methodology-spec.md (P1-native
  bridges section — the preps pairing + verdict), trough diagnosis §8,
  calibration-log ERCOT-64 entry, parameter registry.

## 2026-07-13 — Cross-year LP warm-start default ON for calibration

- **Perf:** `MARKET_SIM_WARMSTART_XYEAR` (carry each backcast year's optimal LP
  basis into the next year's cold P0) now defaults **ON** on the calibration/
  backcast path — the calibration CLIs (`scripts/run_calibration.py`,
  `scripts/run_calibration_full.py`) enable it unless `--no-xyear-warmstart` is
  passed or the env var is set explicitly. New shared resolver
  `resolve_xyear_warmstart_default()` (precedence: flag > explicit env > default
  ON). `run_calibration_full.py`'s year loop now threads an `xyear_cache` (it
  previously did not). Gated by a full 3-year ERCOT + MISO bundle A/B
  (`diff_warmstart_bundles.py`, 8760 h, one-thread): warm-year P0 2.3–2.5×
  faster; objective, served load and total generation bit-identical; per-unit
  dispatch reshuffle 0.004–0.112% confined to marginal ties, plus one small
  MISO-2025 dual-degeneracy price set (182/61,320 zone-hours, load-wt
  Δ 2.4e-4 $/MWh). +~4% peak RSS. See docs/cross-year-warmstart.md.
- **Forecast stays cold-only:** `runner.py` passes `xyear_cache=None` and cannot
  consume the basis regardless of the env var — the capacity-evolution tie-flip
  rejection stands. `tests/test_xyear_warmstart_default.py` pins this invariant
  and the resolver precedence.
- **Reproducibility pinned:** `scripts/replay_keeper.py` now hard-pins
  `MARKET_SIM_WARMSTART_XYEAR=0` at import (like `capture_keeper_goldens.py`),
  and the D-13 `bench-repro.yml` gate pins it at the job level, so byte-identity
  baselines stay basis-independent.
- **Docs:** `docs/cross-year-warmstart.md` default wording updated.

## 2026-07-12 — ERCOT gas commitment bridge (ERCOT-63)

- **Model:** new P1-native committed-state mechanism `ercot_gas_commitment_bridge`
  (default off, ERCOT-only): the ISO-neutral CAISO RA-mustoffer bridge internals
  scoped to merchant gas-CC with the measured committed-CC LSL/HSL cap-weighted
  p50 min-load (0.574, 60-Day DAM disclosure), economic ≥min-down bridging on the
  model's own P0 duals bounded to one DA operating day. Internals gained two
  default-neutral params (`fuel_types`, `max_econ_gap_hours`); D-2 id
  `gas_commitment_bridge` (17) + ablation entry + cited D-4 window; forecast and
  backcast orchestrators both carry the hook. Full-span candidate
  `2026-07-12-ercot63-gas-bridge` registered CALIBRATED-WITH-CAVEATS (one
  ledgered caveat vs the keeper's two; C5c-2024 storage-shape FAIL flips to
  PASS); keeper stays ercot59-storage-deploy pending owner decision. Meta-writer
  fix: `ercot_storage_as_deployment(_from_year)` now recorded in meta.json.
- **Docs realigned:** CLAUDE.md + model-methodology-spec.md (P1-native bridges
  section; caiso_ra_mustoffer no longer listed as a P2 trigger), trough
  diagnosis §7, calibration-log ERCOT-63 entry, parameter registry.

## 2026-07-12 (forecast: CR-3.1 penetration-indexed ELCC accreditation curves for wind/solar)

- **CR-3.1 (P-2C, audit plan §3.4.1; P-2B Option A basis):** the adequacy
  ledger now accredits wind/solar at each ISO's OWN published
  penetration-indexed ELCC accreditation instead of the flat generic
  wind 0.16 / solar 0.18. New `constants.RENEWABLE_ELCC_CURVES_BY_ISO`
  (+ `RenewableElccCurve` / `evaluate_renewable_elcc_curve`, piecewise-linear
  flat-clamped) digitized from the P-0B `capacity-market-elcc` datatype and
  reconciled against the committed rows by `tests/test_renewable_elcc_curves.py`:
  PJM BRA final class ratings on an installed-MW axis (wind 41 % flat; solar
  MW-weighted 10.64 % → 7.89 % declining), MISO's 2019-report
  capacity-credit-vs-penetration-of-peak curve (9 published points), NYISO's
  2025-26 CAFs as single points (wind 16.84 % / solar 12.24 % / OSW 35.79 %,
  ROS/LI). Penetration = the model's own installed share (pools + fleet vs
  the year's peak) so accreditation responds to modeled build (rule 13).
  One resolver (`capacity.resolve_renewable_capacity_credit`: curve → per-ISO
  point override → generic fallback) feeds all four consumers together —
  `accredited_firm_capacity_mw`, the retirement reliability floor, the
  reserve-margin backstop, and the CR-1 reserve position (rule 19). Gate
  `ScenarioConfig.renewable_elcc_curves` default ON (rule 15);
  `False` = frozen-penetration byte-compat mode (pre-CR-3.1 flat credits,
  byte-identical — the hindcast baseline arm,
  `run_capacity_hindcast.py --legacy-renewable-credit`). NEISO/CAISO keep the
  generic fallback (no ISO-published / incremental-basis-only study —
  documented in the registry comment); ERCOT's CDR point override is
  untouched and byte-inert under the gate (tested). Storage is deliberately
  untouched — its duration-ELCC × saturation × dilution stack stays the one
  storage mechanism (rule 19; passthrough locked by test; the datatype's
  storage rows stay unwired pending Option-A step 3). Evolution ledger grew
  an accreditation trail (`renewable_credit_applied`, `wind/solar_cap_mw`,
  `storage_power_mw`/`storage_firm_mw`). T1.9's `storage_cap_value_per_mw`
  metric is now real (marginal 4-h accreditation from the ledger fleet state)
  and the #2063 crash (fixed by P-1C's step-schedule fields) carries a
  regression lock. Methodology spec §5.2 + parameter registry updated.
  Handoff: `docs/handoffs/elcc-curves-p2c-2026-07.md`.

## 2026-07-12 (docs: final truth-gate QA on the calibration/validity documentation refresh)

- **Docs (truth-gate audit, no code changes):** audited every factual claim on
  `docs/codebase-site/calibration-rubric.html`, `model-validity.html`, the
  changed sections of `results-calibration.html`, and
  `docs/calibration-and-validation-methodology.md` against source
  (`calibration_verdict.py`, `legitimacy_diagnostics.py`, `audit_keepers.py`,
  `build_dof_ledger.py`, `floor_mechanisms.py`, `scenarios.py`,
  `run_calibration_full.py`, `constants.py`, `build_status.py`, ci.yml,
  `keepers.json`, `calibration-complete.json`). Fixed: six drifted line
  citations in the methodology doc + two in model-validity.html
  (`as_zero_forcing_ablation` now 4957-4985; holdout gate now 5217/5221;
  `START_YEAR`/`END_YEAR` now constants.py:3871-3872; DOF schema tag now
  build_dof_ledger.py:802); the rubric page's D-4 window table gained the two
  missing `D4_WINDOWS` registry rows (`caiso_gas_commitment_floor` [9,17),
  `cc_mustrun_per_plant` × CC_REGULAR [0,24)) and its citation now spans
  184-262; the illustrative scorecard's C6 note no longer claims C6 checks the
  DOF ledger / ablation twin (those are audit_keepers E8/E9);
  results-calibration.html's measured-data box now cites rule #13 (was #12);
  `docs/calibration-determination-rubric.md` rule citations aligned (rule #13
  admissibility at C6.1; rule 17 "no floor without a window" at C8, with the
  older "rule 12" comment numbering noted). The calibration-keeper-auditor
  agent verified all keeper/frontier text against `keepers.json`,
  `calibration-complete.json`, sidecars, and `status.js`: 0 mismatches (E7
  newer-run warnings on ERCOT/PJM noted, not doc drift). Findings table:
  `docs/codebase-site/QA-REPORT-2026-07.md`.

## 2026-07-11 (docs: multi-ISO triage archive reorg; calibration: fleet-group CAMPD backfill bucketing fix)

- **Docs (multi-ISO reorg):** executed the 2026-07 triage
  (`docs/handoffs/multi-iso-triage-2026-07.md`) — moved 27 resolved
  session/investigation notes from `docs/multi-iso/` to
  `docs/sessions/multi-iso/` (the 22 living references + 8 open-issue notes stay
  in place), applied the flagged trims (doc 04's stale as-built topology table →
  pointer to `config/iso_configs.py`; inlined the `pjm-lmp-residual` afternoon
  reserve-scarcity finding into the living `pjm-reserve-ordc.md`; marked NYISO
  upload U2 landed 2026-06-12 in `nyiso-data-audit.md`; archival closing pointer
  on `outage-gate-fullstop-override-2026-06.md`), and refreshed the
  `docs/multi-iso/README.md` index. Living cross-references repointed to the new
  archive paths.
- **Calibration benchmark (`scripts/run_calibration_full.py`):** the non-ERCOT
  plant-level CAMPD backfill now buckets a genuinely mixed-fuel plant's net
  across the classes physically at it by measured EIA-923 prime-mover class
  shares (`_plant_class_shares`; prior-year shares for incomplete vintages),
  instead of booking the whole plant net to one last-generator-wins class
  (implements the G-21 fleet-group-sweep follow-up: WA-Parish coal↔gas, Doswell/
  Linden CC↔CT). The fix also removes a mixed-plant **double-count** — plants
  whose mapped class is their under-gate minority fuel had the whole plant CAMPD
  net booked there on top of the adequately-reported majority row (~2×). ERCOT
  (curated bin sheet → `class_shares=None`) is byte-identical; complete-year
  non-ERCOT scored benchmarks change (double-count removed), so the PJM/non-ERCOT
  keeper re-score is flagged for owner review (issue #2049). Regression coverage:
  `tests/test_campd_backfill_bucketing.py` (11 cases). Docs realigned:
  `docs/calibration-log.md` G-21 entry + `docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md`
  §6 banner.

## 2026-07-11 (CAISO: storage-AS-award intake, inert reservation probe, 2023 demand-clock fix)

- **Data:** new `storage-as-awards` datatype (schema + per-ISO registry lib +
  curation + tests + loader): CAISO Daily Energy Storage Report quarterly xlsx
  (12 files, 2023–2025) — system-level battery/hybrid AS awards by product,
  hourly DA (IFM) + RT (RTPD); DA battery means reproduce DMM-published anchors
  to ~1 %. Raw fetched and committed by the `apply-caiso74-intake` runner.
- **Model/config:** `ScenarioConfig.caiso_storage_as_reservation` (default off)
  — measured battery upward-AS award reserved from the battery power cap +
  SOC floored at the tariff 30-min sustain; new optional
  `storage_soc_min` bound threaded through `build_variable_bounds` /
  `DispatchModel` / `solve_dispatch` / `DispatchSpec`. The caiso-74 probe
  measured the reservation ex-ante inert on the zone-aggregate CAISO fleet
  (dispatch identical to caiso-73); flag ships default-off, not in any keeper.
- **Model/config:** `ScenarioConfig.caiso_demand_clock_realign` (default off)
  — rule-14 clock fix for the EIA-930 CISO `Demand` column, +1 h late for
  local dates before 2023-11-01 (measured against the extract's own balance
  identity; OASIS SLD corroborates); guard
  `scripts/validate_caiso_demand_clock.py`. caiso-75 probe: 2023 C3a
  +23.5→+22.7 %, tail 480→458 h, C5a-2023 CAVEAT→PASS; 2024/25 byte-identical.
  Keeper stays caiso65 (C2 regression vs keeper blocks promotion).
- **Docs realigned:** methodology spec (optional SOC sustain floor in the
  storage bounds), `docs/backcast-measured-data-audit-2026-06.md` (two new
  measured-input inventory rows), `docs/calibration-log.md` (dated entry),
  FINDINGs for both probes, evening-CC commitment design handoff.

## 2026-07-09 (replay fidelity: ST_GAS net-load drag hinge now round-trips through meta.json)

- **Fix:** `solve_and_persist` now persists `gas_st_drag_overrides` in the bundle
  `meta.json` (alongside the existing `ct_drag_overrides` key). Without it, a
  `--replay-bundle` re-solve of a PJM ST_GAS-drag bundle silently fell back to the
  ScenarioConfig default hinge (`0.00906·netGW − 0.1376`, cap 0.34) instead of the
  PJM-fit hinge (`0.01029·netGW − 0.7263`, cap 0.39) and forced ~4× the ST_GAS
  energy the original run did — the same round-trip gap
  `docs/FINDING-pjm-burndown-2026-07.md` documented for the CT drag. Found while
  restoring the pjm-94/pjm-95 bundles to their full 2023–2025 span (rule 16); the
  same gap also explains why pjm-95's original `run_config.json` recorded the
  default hinge while its dispatch demonstrably ran the PJM fit (its probe passed
  the config directly and only the recording lost the coefficients).
- **Data:** pjm-94 keeper, its zero-forcing ablation twin, and the pjm-95 probe
  re-solved over 2023–2025 in one bundle each (they were registered 2025-only) and
  re-registered; `legitimacy_diagnostics.json` / `metrics.json` now score all
  three years. The v2 re-solve reproduces the pjm-94 attestation's 3-year numbers
  (ST_GAS 8.4/8.1/11.7 TWh) and the promotion commit's keeper-vs-twin delta.

## 2026-07-07 (MISO C-6: measured seam ladders — G-23-residual import-starvation fix)

- **Model/config:** new `ScenarioConfig.miso_seam_measured_ladder` (default off,
  CLI `--miso-seam-measured-ladder`): prices every MISO reference-price seam band
  (PJM/SPP/South, import + export) at the measured per-year Q-Q band ladder in the
  new `interchange_config.MISO_SEAM_LADDER_BY_YEAR`, replacing the
  gas × HR × load-shape band prices + hurdle for backcast years (forecast years
  keep the gas-elastic formula — the hr_by_year two-track design). New injector
  `transmission.inject_miso_seam_ladder_prices` runs last among the backcast seam
  price overwrites (displaces `miso_pjm_border_anchor` /
  `miso_pjm_lmp_import_pricing` on rows it covers; alternatives, never stacked).
- **Derivation:** new `scripts/derive_miso_seam_ladders.py` (the NEISO audit-C-6
  measured-ladder pattern): per-seam Q-Q duration coupling of the measured EIA-930
  MISO BA-to-BA seam flows with the measured MISO DA hub LMP, on the existing
  8-band grid — band capacities and the measured (month × hod) seam envelopes
  unchanged; zero fitted parameters (rule 23: re-derives only when the source
  data extends). Root cause it fixes (G-23 residual, `docs/multi-iso/
  miso-import-starvation-rootcause-2026-07.md`): the measured PJM+IESO seam is a
  firm/scheduled base — importing in 97.5-99.5% of all hours, uncorrelated with
  the hourly spread (r ≈ +0.06), 2025 mean RT spread $0.00 while 28 TWh flowed —
  which a hurdle-gated spot-spread seam structurally deletes in a zero-spread
  year (miso-45: 3.4 TWh gross imports vs 19.0 actual net in 2025).
- **Tests:** `tests/test_miso_seam_ladder.py` — registry completeness/monotonicity/
  same-seam no-wash, band repricing, spot-check of the derived 2025 PJM base band,
  availability untouched, non-MISO / forecast-year / non-seam-row no-ops.

- **Rubric/scoring:** `scripts/calibration_verdict.py` C8 (forced-energy share)
  gains a **grounded-above-budget escalation** (rubric v2.2, owner amendment). The
  15 %/30 % caps and the 2 % materiality floor are unchanged; a material class
  **above** its cap is no longer an automatic `FAIL` but escalates to a conditional
  pass on **provenance (D-4 off-window binding) + shape (D-1 profile)** — forcing
  may exceed the budget when it is a real windowed grid/RA/AS driver that
  reproduces the observed dispatch. A grounded pass is a clean `PASS` surfaced as a
  report **note** (new top-level `notes` in the verdict + `metrics.json`), never a
  caveat; a miss FAILs as a forcing shape/provenance mismatch. Scorer-only — reads
  D1/D2/D4 rows + gates from the committed `legitimacy_diagnostics.json`, no
  re-solve or bundle regen; C8 only *relaxes*, so existing keepers re-score in
  place with **no determination flips** (CAISO-58 / NYISO-53 now fail C8 with an
  explicit "no declared D-4 window" diagnosis instead of a flat over-cap fail).
  `RUBRIC_VERSION` 2.1 → 2.2.
- **Docs:** CLAUDE.md rule 20, `docs/calibration-determination-rubric.md` (§1 C8
  + §9 v2.2), and `docs/model-legitimacy-audit-2026-07.md` (rule 19) amended;
  D-4 is now a promotion-gating input for any over-budget class, not merely a
  reported diagnostic.
- **Tests:** `tests/test_calibration_verdict.py` — grounded pass, off-window fail,
  bad-shape fail, unwindowed-mechanism fail, no-mechanism-rows fail, note
  surfaced in the verdict, and a drift guard that `FORCED_EXEMPT_MECH_NAMES`
  mirrors `floor_mechanisms` (D2_EXEMPT_MECHS ∪ NON_THERMAL_MECHS).

## 2026-07-06 (NEISO C-6: measured seam ladders, priced-interchange P9 re-test, neiso-50 ablation twin)

- **Model/config:** `IMPORT_TRANCHES[_BY_YEAR]["NEISO"]` / `EXPORT_TRANCHES["NEISO"]`
  rederived from measured data only (new `scripts/derive_neiso_import_tranches.py`:
  per-seam Q-Q duration coupling of measured ISO-NE DA LMP with EIA-930 per-seam flows,
  NYISO proxy-bus anchors, no-wash sink clamp) — closes the model-legitimacy audit C-6
  open item for NEISO. New `EXPORT_TRANCHES_BY_YEAR` (year-keyed export sinks) resolved
  through `get_interchange_spec`/`build_export_sinks`.
- **Data intake:** EIA-930 per-DIBA interchange for ISNE (new reproducible
  `scripts/fetch_eia930_interchange.py`) and NYISO proxy-bus DA LBMPs
  (`scripts/build_nyiso_proxy_lmp_neiso.py`, border-lmp schema; source monthly zips
  gitignored with documented public regeneration).
- **Runs registered:** `neiso 51 priced-ix` (P9 probe: net interchange −14.8/−8.9/−9.6
  vs −15.1/−10.3/−8.1 TWh actual — the 2026-06-12 smoke over-imported 2.3×; real
  mechanistic HQ_import zonal separation), `neiso 52 head baseline` (drift attribution:
  keeper's registered C3a is stale vs HEAD after the `use_plant_emission_rates_v2` flip),
  and `neiso 50 ablation` (D-3 zero-forcing twin; audit_keepers E9 now PASS).
- **Docs realigned:** methodology spec §1.3 (NEISO measured seam-ladder note),
  legitimacy-audit C-6 row annotated (NEISO portion resolved), raw-data READMEs,
  border-lmp schema, parameter registry regenerated, calibration-log entry.


## 2026-07-06 (Lane L-5 — doc/code drift sync, gap register G-53–G-58/G-08/G-56)

Prose/comment-only sweep, no behavior changes. Executes `docs/gap-register-2026-07.md`
§5 Wave 1 lane L-5 (`/sync-docs`-style pass after L-2/L-3/L-4 merged):

- **G-53** capacity-evolution step numbering: renumbered `model-methodology-spec.md` §5.1
  and CLAUDE.md's "Capacity Evolution" line to match `capacity.py`'s actual `evolve_fleet`
  order (0 confirmed exits → 1 announced → 2 economic retirement → 3 known additions →
  4 CCS retrofit → 5 economic new entry → 6 reserve-margin backstop → 7 dispatch/RPS) —
  the spec previously had CCS retrofit ahead of known additions, the reverse of the code.
  Also added the previously-undocumented reserve-margin adequacy backstop step to the spec.
- **G-54** CLAUDE.md's architecture block now lists `pipeline/`, `ensemble.py`, `matrix.py`,
  `uncertainty.py`, `structural_prior.py`, `model/ancillary.py`, `policy/cap_and_trade.py`,
  `results/{rcpf,scarcity,evolution_ledger}.py`, the missing `config/` modules, and the
  missing `data/` modules.
- **G-55** `config/paths.py` docstring: `CLEAN_DIR`/`clean_path` were documented as a
  "future" layout nothing reads yet; the clean seam is live (16+ data modules read through
  it) — docstring corrected.
- **G-57** stale comments: `capacity.py` (three spots) said `confirmed_exits_enabled`
  defaults off; it's default-on since the 2026-07-05 flip. `scenarios.py:388`'s
  `use_plant_emission_rates_v2` comment said the legacy path holds "until the 7-year
  history lands" — the 7-year history landed 2026-07-05 (plan §9.5); comment now reflects
  the gate decision (conditioning stays closed, trailing window = 2 years) instead of a
  landing that already happened.
- **G-08** added MISO to CLAUDE.md rule 16's explicit all-years ISO list
  (`multi-iso-triage-2026-07.md` §2: MISO already satisfies the rule, doc-only oversight).
- **G-56** plan-doc status sections refreshed to match the tree: scalar-remediation plan §0
  (pointer to the 2026-07-05 W0 closure doc; `CAISO_BIDIR_EXPORT_CAP_MW` 3500→4361 MW),
  probability-bounds plan header (PB-0..PB-4 landed, PB-5 production run still pending),
  NEISO winter-fuel plan header (Component A landed default-off, probe found the cap inert;
  Component B unbuilt), forecast-validation-program (`ci.yml`'s pytest + `quarantine-gates`
  jobs landed; golden-scenario band fixture seeded at `tests/golden/`, though the band
  comparison itself stays `@pytest.mark.slow`), capacity-economics-plan (Stage-3
  backstop-off diagnostic addendum — backstop off does not unblock the FOM axis either).
  Holdout-policy-memo CI-wiring and orchestrator-unification-plan's stage table were left
  alone: both were already current at review time (L-2 landed the former; the latter's
  Stage 2/3 rows landed independently via #1455 during this session).

No files under `results/calibration/**`, `frontend/data/backcast/**`, or
`scripts/audit_keepers.py` were touched (lane L-1 owns them).

## 2026-07-06 (Orchestrator unification Stages 2-3 — shared dispatch-kwargs assembly and P0/P1 solve core)

Executes Stages 2 and 3 of `docs/handoffs/orchestrator-unification-plan-2026-07.md`
(Stages 0/1/5 previously merged). Pure solve-core unification — both stages gated
dispatch-neutral at **exact byte-identity** (stricter than the required 1e-9) on
dual keeper canaries (CAISO `caiso-51-firm-base` + ERCOT
`ercot32-ordc-total-rtolcap`, all years 2023-2025, `regression_gate.py`):
every dispatch/price/flow/storage column Δ = 0, reshuffle 0.000% every ISO-year.
Gate records: plan §7.3.4 / §7.3.5.

- **Stage 2 — `pipeline/kwargs.py`**: `build_base_dispatch_kwargs` (base LP kwargs
  from a `DispatchSpec`; UNSET-sentinel backcast-only keys keep each orchestrator's
  emitted key set byte-for-byte its pre-refactor set) and `apply_reserve_coopt`
  (the one reserve co-opt seam over `reserve_config`), now called by BOTH
  `runner.py` and `scripts/run_calibration.py`. The backcast's 365-line per-ISO
  reserve elif ladder is deleted — its hand-built PJM zone-aggregate block was
  verified value-identical to `_pjm_design`, and the post-design ERCOT RTOLCAP
  supply-cap overwrite folds into the designs as **audit-wiring gap A5**:
  `_ercot_design` now sets the mode-aware supply cap itself (measured RTOLCAP in
  backcast — identical array; WS-A forward formula in forecast), so the
  single-product forecast ERCOT co-opt is no longer silently uncapped
  (gated `ercot_reserve_supply_cap`).
- **Stage 3 — `pipeline/solve.py`**: `run_energy_solve` — P0 base-cost solve →
  monthly startup markup → P1 bid-cost solve, intra-year warm start, and the
  cross-year warm-start seam — hoisted statement-for-statement from both
  orchestrators. The backcast threads its `xyear_cache` through unchanged; the
  forecast passes `None` per plan §8 (cross-year warm-start now wireable-for-free
  but OFF pending the basis-independent capacity screen; AR-6 closed by
  construction). The startup-markup config gates (`gas_st_startup_spread` et al.)
  now reach the forecast path — byte-identical at their default-off values.
- Tests: `tests/test_pipeline_kwargs.py` (key-set fidelity + A5 trivial case),
  `tests/test_pipeline_solve.py` (inline-sequence equivalence, warm/cold, cache
  seams); `test_runner.py`/`test_matrix.py` LP mocks repointed to
  `pipeline.solve`. Fast tier 2881 passed / 0 failed at each stage.
- Not touched (next wave's lane): Stage 4 (P2 commitment core), Stage 7
  (backcast_config move + getattr fold); capacity logic, keepers/registry,
  offer curves, policy/.

## 2026-07-06 (Lane L-8 — emissions forward-channel decisions + mass-cap backcast wiring)

Gap-register (`docs/gap-register-2026-07.md` §5 Wave 2) G-39/G-29/W8/W10 items. No default
flips, no keeper artifacts, no solves.

- **G-29 wiring (done, tested):** the backcast calibration harness previously never called
  `get_active_policy_constraints` at all (`mass_cap_enabled` was fully inert there, distinct from
  `runner.py`'s already-wired forecast path). Extracted the row-building logic into
  `policy.constraints.build_mass_cap_dispatch_kwargs(config, year, zone_names, fleet_arrays)` and
  called it from `scripts/run_calibration.py::run_year`'s `dispatch_kwargs` assembly (mirrors
  `runner.py`'s `mass_caps` block). `run_year` gained `mass_cap_enabled`/`mass_cap_tons`/
  `mass_cap_program` parameters (applied via `config.with_overrides`, the file's existing
  convention) and matching CLI flags. Default stays off everywhere; `scripts/
  run_calibration_full.py`'s own argparse/`solve_and_persist` forwarding was deliberately left
  unwired (separate large surface, 3-line follow-on documented in the plan doc) to keep this
  lane's diff to the config-threading seam. New `tests/test_constraints.py`
  (`TestBuildMassCapDispatchKwargs`): a mass-cap-enabled backcast config actually builds
  `mass_cap_coeffs`/`mass_cap_rhs`/`mass_cap_labels`; disabled/no-program/quarantined-year
  configs all return `{}`.
- **G-39 decision memo** (`docs/handoffs/emissions-co2-rate-plan-2026-07.md` §9.6):
  `use_plant_emission_rates_v2`'s flip is dispatch-inert for ERCOT/PJM/MISO (carbon_price=0 in
  backcast there) and dispatch-affecting only for CAISO/NYISO/NEISO (measured CARB/RGGI price
  nonzero) — mirrors the 2026-07-05 R2 re-gate's own finding. Recommends a cheap no-solve
  re-score PROBE for the three carbon-zero ISOs now, and folding the v2 flip into each
  carbon-priced ISO's *next* already-scheduled HEAD re-gate rather than forcing a standalone
  wave; flip the global default only after all three have been evaluated under it at least once.
  States explicitly that the W10 emission-control retrofit channel's triple gate
  (`control_retrofit_forward` + `use_plant_emission_rates_v2` + forecast mode) is unaffected by
  this decision and should stay inert until the E2 NOx/SO2 forward-rate wave lands.
- **W8 leftovers filed as explicit plan-doc sections**
  (`docs/handoffs/emissions-mass-cap-plan-2026-07.md`): §13 NOx mass-cap follow-on (CSAPR
  ozone-season design sketch, seasonal-hour-mask wrinkle vs the CO2 row, rule-13 admissibility
  with the honest caveat that no measured NOx allowance price exists in-repo to validate a row's
  dual against — ships scenario-only if built) and an expanded §8 rule-13 admissibility
  subsection for banking/borrowing (why a self-referential bank-balance recursion fails rule 13
  independent of the rule-9 one-pass argument already on file).
- **RGGI dual-vs-auction-price validation probe spec'd as a runnable recipe** (§14 of the
  mass-cap plan doc): NYISO 2023-2024, `scripts/run_calibration.py --mass-cap-enabled
  --mass-cap-tons <near-realized-tonnage>`, reading `result.co2_cap_price` directly (not printed
  by `_report_year`); explicit non-goal framing (a sanity/order-of-magnitude check and a
  negative-control leg against the real published budget, never a pass/fail calibration gate).
  Not run in this session.

## 2026-07-05 (Emissions mass-cap follow-ons — PJM per-unit membership, per-state RGGI budgets)

Completes the two deferred follow-ons from `docs/handoffs/emissions-mass-cap-plan-2026-07.md`
(mechanism itself default-off, unchanged):

- **PJM fractional RGGI membership** is now populated (`PJM_RGGI_ZONE_SHARE`, per zone per year),
  derived by the new `scripts/derive_pjm_rggi_zone_share.py` from the year-matched EIA-860
  plant/generator tables and the model's own PJM zone assignment; Virginia's 1 Jan 2024 RGGI exit
  shows up directly (`PJM_Dominion` 0.9881 → 0.0). Membership is now per-unit where the fleet
  representation allows it: `policy/cap_and_trade.py::per_generator_membership` (new) tests any
  generator with a real `plant_code` against its own plant's state exactly
  (`data/zone_assignment.py::plant_state_lookup`, new), falling back to the zone-level fractional
  share only for synthetic/aggregate units. Wired at `runner.py`'s `mass_caps` cap_coeffs call site.
  Found and fixed a latent bug in the process: `resolve_carbon_program`'s membership vector was
  sized to the static ISO zone list, not the runtime-extended one (PJM's dynamically-appended
  external interchange zone) — `resolve_carbon_program`/`get_active_policy_constraints` now accept
  an explicit `zone_names` override, and `runner.py` passes its already-extended list.
- **Per-state RGGI budgets**: `RGGI_STATE_CO2_BUDGET` now carries each member state's own CO2
  Allowance Base Budget for 2023-2025 (exact figures from RGGI, Inc.'s official per-state
  distribution spreadsheets, also correcting the regional total from an ICAP-derived estimate to
  the exact published sum). A RGGI ISO's power-sector cap row now sums its own member states
  instead of the region-wide over-bound.
- New tests: `tests/test_cap_and_trade.py` (PJM per-unit membership, per-state budget sums, Virginia
  exit year-gating) and `tests/test_runner.py::TestMassCapPerUnitMembershipWiring` (end-to-end PJM
  wiring check with a mocked dispatch solve).
- The optional diagnostic backcast probe (endogenous dual vs. observed RGGI auction price) was not
  run: the backcast calibration harness (`scripts/run_calibration.py`/`run_calibration_full.py`) has
  its own independent dispatch pipeline that never threads `get_active_policy_constraints`, so
  `mass_cap_enabled` is inert there today — a scoped follow-on, documented in the plan doc rather
  than half-wired in this pass.
## 2026-07-05 (W2-P3 Stage 2 — capacity-screen revenue fix, reversal supersession, FOM re-verification)

**Revenue-side fix (capacity-economics plan §5 step 2).** The retirement screen's
margin basis is now the attainable pro-forma inframarginal margin —
per-hour `max(0, price − mc, reserve price) × pmax × availability`, the Potomac-SOM
net-revenue construction and the same basis the thermal new-entry screen already used —
replacing realized-LP-dispatch margin, which structurally missed the post-solve ORDC
adder's scarcity rent (Stage-1 audit: fleet CT screen revenue ~1.5 $/kW-yr vs the SOM
≈68 observable). A new hourly reserve-price signal (`screen_reserve_value_enabled`,
default on; threaded via `PriorYearResults`) values each reserve-eligible unit's
per-hour best use — energy or reserve, never both on the same MW: the reserve co-opt's
own duals under `ercot_thermal_as_endogenous` (superseding that flag's annual per-fuel
rate), else the ORDC scarcity adder (RTORPA/RTOFFPA pay real-time reserves the same
ORDC price — ERCOT Nodal Protocols §6.5.7.5). When present it is the SOLE thermal AS
pricing (rule 19). Zero fitted parameters; SOM is the validity check, never a target.
VRE new entry is now shape-aware (plan §6 CX-6c): wind/solar candidates value their
build zone's hourly CF against that zone's prices, scalar base-CF as fallback.
First-screen-year ERCOT CT revenue on the default ORDC footing: 1.6 → 17.2 $/kW-yr.

**FOM re-verification (plan §5.4 grid vs the accredited floor): NOT flipped, again.**
The 2×3 ERCOT + 2-cell PJM grid re-ran at HEAD
(`docs/handoffs/fom-scarcity-grid-2026-07-05-stage2.json`): capacity trajectory
byte-identical across the FOM axis, zero retirements everywhere. The masking is no
longer the Stage-1 nameplate-ledger bug but genuine mid-growth adequacy shortage — the
accredited floor correctly un-retires every eligible unit and the harness-enabled
backstop floods CT (15.2 GW in three years), collapsing scarcity below every bar. ATB
targets (21/30/45) stay frozen; tornado re-centring deferred with the flip; unblocking
paths recorded in `docs/handoffs/fom-scarcity-joint-protocol-2026-07-05-stage2.md` §3
(foresight A/B re-run remains the open next step).

**Retirement-reversal supersession (confirmed-retirement plan §2.2 / §4.3.2).**
`apply_announced_retirements` now ignores announced dates for plants whose
confirmed-retirements registry rows are ALL superseded — an exit reversed outright by a
public counter-instrument, nothing re-confirmed — via
`data.confirmed_retirements.load_announced_reversal_plants`, loaded in every forecast
run independently of `confirmed_exits_enabled` (still default-off). Byron 1–2 /
Dresden 2–3 reversal rows seeded (Exelon 2020 PJM deactivations reversed by IL CEJA
P.A. 102-0662, 2021-09-15) — the PJM hindcast's entire 4.1 GW false-retire. The
curation exit-year window check applies to live rows only.

**ERCOT realized capacity hindcast re-run at HEAD** and registered on the
forecast-validation dashboard (`frontend/data/hindcast/ercot-2021-2025-realized-s2`) as
the before/after diagnostic for the screen changes — deltas reported as found, nothing
tuned to them (rules 1/11/14).

## 2026-07-05 (confirmed-retirement channel — default flip to on)

**Model default.** `ScenarioConfig.confirmed_exits_enabled` flips **False →
True** (`src/market_sim/config/scenarios.py`), completing the owner sign-off
contemplated in `docs/handoffs/confirmed-retirement-plan-2026-07.md` §7. The
registry now covers all six ISOs (PR #1420, merged 2026-07-05); this session
resolved the two remaining primary-document caveats first:

- **Rockport 1** (PJM, consent decree): confirmed the S.D. Ohio civil action
  numbers directly against the filed Fifth Joint Modification (Case
  2:99-cv-01250-EAS-KAJ Doc #438) — Consolidated Cases C2-99-1182 and
  C2-99-1250, and Paragraph 140's verbatim 2028-12-31 Rockport Unit 1
  retirement date.
- **Diablo Canyon** (CAISO, SB 846): confirmed CPUC Decision D.23-12-036
  directly against a CPUC decision in R.23-01-007 that quotes it verbatim,
  including both units' authorized-operation end dates (2029-10-31 / 
  2030-10-31).

Both `data/raw/confirmed-retirements/{pjm,caiso}.csv` rows and the README are
updated with the primary-document citations; neither caveat remains.

The flip also activates the non-fossil announced-horizon gate in
`capacity.evolve_fleet` (same `confirmed_exits_enabled` flag couples both —
unchanged mechanism, documented in CLAUDE.md and the plan). The channel
remains forecast-mode only: `runner._confirmed_exits_active` (new, extracted
from the inline gate for testability) hard-gates on `mode == "forecast"`, so a
backcast run is byte-identical regardless of this default — verified with
`scripts/probes/verify_backcast_noop.py` and a new
`TestConfirmedExitsDefaultAndBackcastGate` test class in
`tests/test_confirmed_retirements.py`. Verification forecast probes
(`scripts/probes/confirmed_retirement_probe.py`, ERCOT + CAISO, not a keeper)
confirm only the registry's own instruments change channel after the flip.

Docs synced: CLAUDE.md's capacity-evolution section, `model-methodology-spec.md`
§5.1, `docs/codebase/03-capacity-and-commitment.md`, and the parameter registry
(`frontend/data/parameters.json` / `docs/parameter-citations.md`) all now cite
the default as **on** with the sign-off citation.

## 2026-07-05 (CI wiring — W2-P5 forecast invariants)

Wired the W2-P5 forecast-invariant checks into CI (docs/handoffs/forecast-validation-program-2026-07.md §6): the fast invariant-logic tests already run in `ci.yml`'s per-PR tier (no change needed, documented explicitly), and a new scheduled `.github/workflows/forecast-invariants.yml` runs the slow real-LP e2e test plus the P1-P3 paired-run invariants weekly. No checker/test logic changed.

## 2026-07-05 (Stage 5 — interchange unification onto the shared InterchangeSpec)

**Refactor, dispatch-neutral (builder-swap gate §7.2).** `run_calibration.py`'s
inline priced-interchange construction now rides the SAME
`config/interchange_config.get_interchange_spec` → `build_interchange_fleet` →
`apply_interchange_topology` path the forecast runner uses; the spec resolves
the full backcast builder ladder (CAISO reference seam ≻ per-hub ≻ bidir ≻
static year-grounded tranches + Manitoba firm block) from the existing
`ScenarioConfig` gates, and `build_interchange_fleet` delegates to the
canonical `transmission.py` builders (the spec module's parallel private
copies are deleted). New shared `transmission.apply_interchange_injections`
runs the forward-native post-assembly sequence for BOTH orchestrators
(reference-price seams, firm import/export floors, CAISO gas-coupling +
solar-shape couplings); the backcast's measured-price overlays are
consolidated into one labelled closure threaded in at the documented seam
point, each naming its measured source and forecast substitute — none is
reachable from the forecast. Closes the §2.2 CAISO drift trio (bidir
intertie, import solar-shape, import gas-coupling — plus the unlisted NYISO
firm-import floor) by construction: each is now forecast-reachable behind its
default-off gate, with no bespoke per-mechanism runner wiring.
`tests/test_interchange_parity.py` pins old-inline vs new-spec parity for all
five priced-interchange ISOs and all three CAISO seam modes. Details:
`docs/handoffs/orchestrator-unification-plan-2026-07.md` §7.3.3.

**Builder-mode gate result: PASS.** CAISO keeper canary
(`2026-07-03-caiso-51-firm-base`, 2023-2025) re-solved before
(`fb44295`)/after (`8d46b90`) this stage: `regression_gate.py --mode
builder` reports every result column within tolerance (1e-9), 0.000%
hourly reshuffle in every year, and the 2023 bundle files are in fact
byte-identical — dispatch-neutral, no solved number moved. Full breakdown
(including the pre-existing, unrelated PJM/MISO ablation-twin
`audit_keepers.py` findings) in plan §7.3.3.

## 2026-07-05 (CO2-rate 7-year gate decision — wave-3 E1 close-out)

- Completed the 2018–2021 CAMPD hourly unit-level intake (136/136 state-years)
  and re-derived `plant_emission_rates_v2` over all six ISOs × 7 years (29,435
  unit-year rows; 2018–2021 net conversion on pooled parasitic factors — EIA-923
  those years remains a documented DATA NEEDED gap).
- `scripts/loyo_co2_rates.py` gained rule-23 sweep capabilities
  (`--forward-chain`, `--window-sweep`, `--gate-sweep`); constants chosen ONCE
  from the 7-year held-in LOYO: `CO2_RATE_CONDITIONING_ENABLED` stays **False**
  (envelope-gated sim conditioning never beat `a_gw` on ERCOT at any gate) and
  `CO2_RATE_TRAILING_WINDOW_YEARS` **0 → 2** (forward-chained sweep: w2 won 8/8
  per-target comparisons across ERCOT+PJM). Docs realigned:
  `model-methodology-spec.md` forward-mode source, `docs/parameter-citations.md`
  (regenerated), plan `§9.5` (full tables + PJM sim-op caveat).

## 2026-07-05 (confirmed-vs-announced retirement channel — implementation, W2-P2)

**Model.** Implemented the confirmed-vs-announced retirement channel from the
W0-P2 plan (`docs/handoffs/confirmed-retirement-plan-2026-07.md`). Only
**confirmed** exits — units bound by an enforceable public instrument (RTO
deactivation acceptance, consent decree, statute, regulatory order, RMR end) —
are exogenous; **announced** EIA-860 dates stay with the economic screen.

- **New `confirmed-retirements` datatype** (schema-first, per-ISO registry
  modules, `write_clean` seam): `data/dictionary/schema/confirmed-retirements.schema.yaml`
  (closed `confirmation_class` vocabulary), `scripts/lib/confirmed_retirements/`
  (`IsoSpec` + register + generic CSV parser, one module per ISO — no if-iso
  ladders), `scripts/curate_confirmed_retirements.py` (EIA-860 spine validation:
  plant/generator exists, MW within 5 %, `exit_year >= 2023`), registered in
  `regenerate_clean.py` + the data dictionary. Seeded PJM (Rockport consent
  decree, Kincaid IL CEJA statute, Brandon Shores/Wagner `rmr_end`, Eddystone
  `superseded` by DOE 202(c)) and ERCOT (Braunig `rmr_end`); other ISOs land as
  DATA NEEDED. **All seeded instruments require re-verification before the flag
  is defaulted on** (open item).
- **Confirmed-exit injector** (`model.capacity.apply_confirmed_exits`, step 0 of
  `evolve_fleet` + first-year `build_base_fleet`): plant-code join, unit-grain
  drop or plant-binned MW derate, `exit_month<=6 → exit_year else exit_year+1`,
  bypasses the reliability floor, composes as `min(economic, confirmed_date)`.
  Consumption seam `data.confirmed_retirements.load_confirmed_exits` (drops
  superseded, earliest instrument per unit). GATED new `confirmed_exits_enabled`
  (default OFF); forecast-mode only. Default-off is byte-identical to before.
- **`apply_known_retirements` → `apply_announced_retirements` rename** (RC-3, no
  alias). The fossil default no-op is now explicit in code, CLAUDE.md, and the
  methodology spec §5.1.
- **Non-fossil data-horizon gate** (RC-5,
  `constants.NONFOSSIL_ANNOUNCED_HORIZON_YEARS = 5`): announced non-fossil dates
  beyond `EIA860_OPERABLE_VINTAGE + 5` are honored only if the unit is in the
  confirmed registry (the gate activates with the confirmed channel).
  **Behaviour change** (with the channel on): the 2040-2072 hydro-relicense /
  solar-EOL placeholders stop force-retiring, and of the 3 announced nuclear
  units (1,871 MW, 2030-2034) the 2030 exit stays deterministic (within horizon)
  while 2033/2034 become economic unless confirmed.
- **EIA-860 intake (RC-2):** carry `Planned Retirement Month` into
  `eia860_generators.parquet` (`process_eia860._GENERATOR_COLUMN_MAP` +
  `EIA_860_CSV_COLUMNS`); the loader already consumed `retirement_month` when
  present (338 operable units now carry it). Loader `OP` filter unchanged.
- **Tests:** `tests/test_capacity.py` (announced rename + horizon gate + confirmed
  injector: unit drop, bin derate math, RC-1 confirmed-fossil-vs-announced-twin,
  month convention, floor bypass), `tests/test_curate_confirmed_retirements.py`
  (schema/spine/vocabulary guards), `tests/test_confirmed_retirements.py` (loader
  earliest-instrument/superseded, first-year `build_base_fleet`, default-off).
- **Verification probe** (`scripts/probes/confirmed_retirement_probe.py`, injector
  ON, forecast ERCOT + PJM 2026-2029): see the commit message. Not a keeper.
- **Known limitation (follow-up):** a plant-binned coal/gas confirmed exit
  effective 2+ years into a CAMPD forecast is not matched, because
  `evolve_fleet`'s end-of-year `aggregate_fleet` merges per-plant coal/gas bins
  into vintage efficiency bins and erases `plant_code` after the base year (a
  pre-existing model behaviour). The injector fires for first-year exits and for
  unit-grain units that pass through aggregation carrying an announced date
  (e.g. Wagner's oil units). Preserving a registry plant's identity through
  aggregation requires the dispatch/economic-screen pipeline to accept
  un-aggregated coal tranches (attempted here via a `keep_plant_codes`
  pass-through, reverted because it desynced the economic screen's dispatch
  mapping) — deferred.
## 2026-07-05 (PB-3 follow-up — emissions-basis staleness handling + committed prior artifact)

**Post-processing only — no solves.** Extends the landed PB-3 structural prior
with the basis-staleness handling the W0-P4 design requires
(`docs/handoffs/forecast-validation-program-2026-07.md` §0/§3.2): the D-7
statmode fit inputs predate the R2 measured-rate CO2 basis (PR #1371).
`default_prior` now (a) re-scores the carbon-zero ISOs (ERCOT/PJM/MISO) under
the current basis with no solve (`rescore_carbon_zero`: recompute model/actual
CO2 from the committed `gmModel`/`classFull` × stored class intensities;
refuses to fit on a mismatch — all three verify identical, the 2023–2025
scoring-rate rows being content-identical at HEAD), and (b) flags the
carbon-priced ISOs (CAISO/NYISO/NEISO, new cited constant
`STRUCTURAL_PRIOR_CARBON_PRICED_ISOS`) `basis_stale` /
`"stale-pending-W3-P1"` — R2 moves their merit order, so only the W3-P1
re-solves can refresh them. Staleness and the emissions-basis identity (label +
sha256 of `fossil_co2_rates.parquet`) flow through `IsoResidual`/
`StructuralPrior.as_dict()` into `ensemble_meta.json` and the band label. New
`write_prior_artifact` commits the fit record to
`results/ensemble/structural-prior/<version>.json`
(`paths.STRUCTURAL_PRIOR_ARTIFACT_DIR`) so the W3-P1 re-fit is a clean,
diffable swap; the fitted `pb3-statmode-d7-2026-07.json` is committed.
Methodology note gains §6 (the staleness record); tests cover the flags, the
re-score verification, the mismatch refusal, and the artifact round-trip.

## 2026-07-05 (PB-3 — structural-error prior + published emissions band)

**Post-processing only — no solves, no keeper/registry changes.** Landed on
`claude/pb3-structural-prior-2026-wave5` per
`docs/handoffs/probability-bounds-prompts-2026-07.md` PB-3 / plan §3. New
`src/market_sim/structural_prior.py` folds the model's own dispatch-skill error
into the emissions band: `fit_prior` reads `eps = ln(model/actual)` CO2 for
2023–2025 straight off the committed D-7 statistical-mode probes
(`STATMODE_PROBE_RUNS`; model from `frontend/data/backcast/runs/<id>.js`, actual
from `frontend/data/backcast/bench/<ISO>/<y>.json.gz`) — a measured, reproducible
source, never tuned to a residual (rules 1/13/24). Per-ISO bias `b_i`, noise
pooled across ISOs, carried as `Student-t(nu=2)` with the `(1 + 1/n)` small-sample
inflation so the prior is strictly wider than the plug-in normal. `convolve`
builds the `parametric_plus_structural` band (log-space `emissions·exp(eps)`,
K=25, P5–P95); the parametric P50 point forecast is never recentered (the
structural layer is written alongside, not over, it). Horizon term `lambda(h)=0`
(UNMEASURED) keeps every band labelled **dispatch-conditional** until PP-0.3.
`ensemble.export_sampler_ensemble(..., prior=…)` / `bands_from_metrics` and
`market-sim ensemble --structural-prior` wire it in; only 2023–2025 are ever read
(rule 22). New constants (`STRUCTURAL_PRIOR_*`), `paths.FRONTEND_BACKCAST_DIR`,
and methodology note `docs/probabilistic-emissions-methodology.md` (assumptions
A-1…A-8 + the §3.4 coverage gaps).

## 2026-07-05 (orchestrator-unification Stage 1 — pipeline typing scaffold)

**Typing/scaffolding only — no solved number changes.** Landed on
`claude/stage1-pipeline-typing-3w1mhl` per
`docs/handoffs/orchestrator-unification-plan-2026-07.md` §7.3.2, Stage 1 of the
staged migration that unifies the forecast (`runner.py`) and backcast
(`run_calibration.py`) solve orchestrators. New `src/market_sim/pipeline/`
package: `spec.py` (`DispatchSpec`, `ReserveSpec` — frozen containers mirroring
the existing `dispatch_kwargs`/reserve-kwargs dicts key-for-key), `prior.py`
(`PriorYearResults`, a typed replacement for the 14-key untyped `prior_results`
dict threaded across forecast years, with dict-shim `.get`/`__getitem__` so
existing readers are unaffected), `result.py` (`YearSolveResult` placeholder for
Stages 3-4). `runner.py`'s per-year `prior_results` now constructs a
`PriorYearResults` instead of a bare dict. `run_calibration.py` is untouched
(migrates in later stages). Regression gate: byte-identical on every re-solved
column — structurally guaranteed here, since the backcast path (what the six
keeper golds re-solve) imports neither `runner.py` nor `market_sim.pipeline`.

## 2026-07-05 (orchestrator-unification Stage 0 — regression-gate harness)

**Infra only — add-only, no source-file changes.** Landed on
`claude/regression-gate-stage-0-umopup` per
`docs/handoffs/orchestrator-unification-plan-2026-07.md` §7.3.1, establishing
the regression-gate every later orchestrator-unification stage runs before
pushing: `scripts/capture_keeper_goldens.py` (re-solves each of the six ISO
keepers from its frozen bundle, determinism-pinned, writes P1/P2 dispatch +
system frames plus a hashes-only `manifest.json`), `scripts/regression_gate.py`
(one command running the golden diff, the warm-start reshuffle localizer, the
per-ISO smoke suite, and the holdout-quarantine checks, with `--mode byte` /
`--mode builder` tolerance selection per the plan's stage-type standard),
verified `tests/test_regression_smoke.py` coverage. A/A byte-identity confirmed
on the NEISO keeper (double capture, zero column deviation). MISO golden capture
deferred to a ≥24 GB host (this box's 15 GB ceiling OOMs during MISO's
per-asset reserve-column construction, per CLAUDE.md's documented memory tier).

## 2026-07-05 (weather-year pool widened per ISO — PB-2 data intake)

**Data intake, no solves, no dashboard changes.** Widens the forecast
ensemble's weather-year draws (`docs/handoffs/probability-bounds-plan-2026-07.md`
§2.1 flagged the original 3-draw `WEATHER_YEAR_POOL` as thin). New
`constants.WEATHER_YEAR_POOL_BY_ISO` registry + `weather_year_pool(iso)`
helper: ERCOT and NEISO verified end-to-end (clean 8760-hour EIA-930 hourly
demand + resolved wind/solar CF, no fallback needed) for 2019-2021, added
alongside the existing 2023-2025 window; NYISO gets 2021 only (its solar
series always falls back to the EIA-930 generation-distribution parquet,
whose own coverage floor is 2021, so 2019/2020 fail end-to-end despite raw
hourly demand coverage existing). CAISO/PJM/MISO are unchanged — their
`<BA> hourly` extracts don't reach back before late 2021/2022, and fetching
more history is blocked in this managed sandbox (`api.eia.gov` 403). Rule-22
quarantine untouched (2022, H1-2026 excluded from every pool). `ensemble.py`'s
`weather_ensemble_configs` now defaults to the per-ISO pool instead of the
flat global one; `configs/uncertainty_ercot.yaml`'s PB-2 sampler weather
weights widened to match (uniform 1/6 over the six ERCOT years). COVID-2020's
documented demand-shape anomaly is disclosed but not down-weighted (a
client-adjustable choice, not a baked-in one). Full per-ISO/year verification
log and rationale: `docs/weather-pool-coverage-2026-07.md`.

## 2026-07-05 (confirmed-vs-announced retirement channel — design plan, W0-P2)

**Docs/plan only — no mechanism change.** Landed
`docs/handoffs/confirmed-retirement-plan-2026-07.md`: the audit §B (RC-1…RC-5)
design for making only CONFIRMED retirements (binding instruments: RTO
deactivation acceptances, consent decrees, statutes, PUC orders) exogenous while
announced dates stay with the economic screen. Covers the new
`confirmed-retirements` datatype (schema-first, per-ISO registry modules,
`write_clean` seam), the forecast-mode confirmed-exit injector
(`apply_confirmed_exits`, plant-code join with plant-bin derates, GATED
`confirmed_exits_enabled` default-off), the data-horizon confirmation gate for
non-fossil placeholder dates (RC-5), the `apply_known_retirements` →
`apply_announced_retirements` rename (RC-3), rule-17 forward stories, and the
complete W2-P2 implementation prompt.

- **Probe evidence** (new `scripts/probes/confirmed_retirement_probe.py`,
  instrumented 2026–2029 default-config forecasts): the economic screen retired
  **zero** units in both ERCOT and PJM. ERCOT is floor-inert — the reliability
  floor `(peak − firm_clean) × 1.15` ≈ 103 GW permanently exceeds ~80 GW total
  thermal (CX-3), rescuing every eligible unit (Spruce/Sommers tranches eligible,
  never retired). PJM is profitability-inert — capacity revenue + below-ATB FOM
  bars (CX-1) leave 2 of 1,387 units with any loss year; the consent-decree-bound
  Rockport units run to the horizon.
- **New finding:** `bins_to_fleet` drops `planned_retirement_year` for every
  binned thermal plant (tranche generators carry `None`), so the date-based
  retirement step is a no-op for the binned fleet regardless of the fossil
  exemption — the injector therefore joins the registry by `plant_code`.
- EIA-860 inspection: no confirmation flag exists on planned retirements (558
  units carry planned years, 205 in 2026–2028); `Planned Retirement Month` is
  dropped at intake (RC-2 fix specced); loader's `OP` filter hides SB/OS/OA.
- Prompt-pack W0-P2 status row flipped to PLAN DONE.

## 2026-07-05 (CHP behind-the-meter host share, measured)

**Model.** Closed the deferred half of Wave-2 R5 (EM-7): the forecast CHP
must-run BTM sizing now uses a **measured** per-plant host self-supply share
instead of the sector-keyed `chp_btm_pct` default. New `chp-btm-share` clean
datatype (`scripts/curate_chp_btm_share.py`,
`data/dictionary/schema/chp-btm-share.schema.yaml`): per (iso, plant, CHP
class), `btm_share = (eia923_net_mwh − campd_net_mwh) / eia923_net_mwh`, pooled
across every available non-quarantined year from the committed
`plant_emission_rates_v2` (CAMPD, steam-reporting units only) and
`eia923_monthly_generation` (EIA-923) artifacts — both measured, reproducible
inputs independent of the model's own dispatch (rule 13).

`data.chp.measured_btm_share_by_plant` reads it through the `clean_io` seam;
`runner._chp_measured_co2_inputs` resolves it for **forecast** years only and
`results/emissions.compute_must_run_emissions` now consumes
`btm_share_by_plant` in its measured-CF-fallback branch too (previously only
the measured-share/`total_gen_by_plant` branch did), falling back to the bin's
own `pct_mr` for an uncovered plant. The backcast `_btm_frame` path
(`run_calibration_full.py`) is unchanged. Docs: `docs/binning-methodology.md`
CHP must-run post-processing section corrected to the current two-branch
formula; `docs/handoffs/emissions-co2-rate-plan-2026-07.md` §9.2 records the
wave.

## 2026-07-05 (NOx/SO2 full wiring — plan §5 R7 / §7)

**Model.** NOx and SO2 now ride the identical measured-rate v2 path as CO2
(previously CO2-only; NOx/SO2 were left to the legacy pooled artifact). The v2
artifact (`plant_emission_rates_v2.parquet`) carries `nox_kg`/`so2_kg` masses
and their net-basis intensities alongside CO2; `emission_rates.measured_plant_rates`
and `class_median_rates` gained a `pollutant` selector; `fleet.apply_plant_emission_rates_v2`
books all three pollutants at the plant's measured tonnes/MWh-net rate under the
same mode/composition-mask policy (backcast = target-year measured, forecast =
gen-weighted trailing estimator base). CO2/NOx override only when the measured
rate is positive; SO2 is always set (zero is a legitimate gas value). **No CO2
rate, no merit order, no dispatch changes** — the v2 CO2 columns are byte-identical
after the re-derive; NOx/SO2 are secondary. `scripts/score_backcast_shape_emissions.py`
now scores model-vs-CAMPD NOx and SO2 masses beside CO2 (the SO2 coal/gas split is
the sharpest independent dispatch-mix check) and reads intensities from the v2
artifact via `config/paths` (fixing its stale `inputs/` paths). No new tunable —
the class-median percentile is the shared `CO2_RATE_CLASS_MEDIAN_PERCENTILE`.
**Docs.** `model-methodology-spec.md` per-plant-emission-rate override section
gained the NOx/SO2-ride-the-v2-path paragraph.

## 2026-07-05 (mass-cap budget schedules landed + row validated)

**Data.** Landed the published CARB and RGGI power-sector budget schedules as
cited constants, mirrored by curated raw artifacts — same intake discipline as
`STATE_CARBON_PRICE_BY_ISO`:

- `CARB_ALLOWANCE_BUDGET` (MMT CO2e; 17 CCR §95841 Table 6-2, 2023-2025 + forward
  2027-2031) and `CARB_FLOOR_PRICE` ($/tonne; CARB Annual Auction Reserve Price
  Notices 2023-2025).
- `RGGI_STATE_CO2_BUDGET["RGGI"]` — the regional cap (short tons; RGGI cap
  trajectory, 2023-2025 published + 2027-2030 projected). Per-state budgets await
  the RGGI allowance-distribution intake; until then a RGGI ISO's row uses the
  regional cap.
- Raw CSVs under `data/raw/policy/{carb-cap-schedule,rggi-co2-budgets}/` curate to
  the gitignored `data/clean/` via `scripts/curate_*.py`. **No 2022/H1-2026 rows**
  (holdout quarantine, rule 22). A test asserts each constant mirrors its CSV.

**Model.** `policy/cap_and_trade.py::_power_sector_cap` now sources the mass-cap
row's `cap_tons` (metric tonnes) from an explicit `config.mass_cap_tons` or, else,
the published budget for the year — CARB MMT × 1e6, RGGI short tons ×
`SHORT_TON_TO_METRIC_TONNE`. These region-/economy-wide budgets vastly exceed a
single ISO's power-sector emissions, so the row is **slack and its dual ≈ 0** on a
real ISO — the faithful power-sector, no-bank result (plan §2). Still **GATED,
`mass_cap_enabled` default OFF**; default runs are byte-identical.

**Tests.** Resolver returns the published, unit-converted `cap_tons` for
CAISO/NYISO/NEISO (explicit-tons override still wins; quarantined 2026 stays
inert); an explicit dispatch test asserts the endogenous dual is non-negative,
monotone non-decreasing as the cap tightens, and re-orders merit coal→gas.

## 2026-07-05 (emissions docs/citation reconciliation — wave-2 R4/R5/R6, no behavior change)

**Docs only.** Reconciled prose docs and the parameter-citation registry with the CO2
emissions-plan wave-2 code (`036bd3e`, `c17eaa4`, PR #1371) that had landed without a
paired doc sync, plus fixed pre-existing drift the sweep turned up. No source logic
changed.

- `docs/fable-repo-audit-2026-07.md` §A: marked EM-2/EM-4/EM-5/EM-6/EM-7/EM-8 **RESOLVED**
  with landing commits and tests; EM-3 **RESOLVED (provenance)** with its retrofit tail
  called out as open; EM-1 **PARTIALLY RESOLVED** (rebased a second time same-day onto the
  NOx/SO2-full-wiring wave above — the measured-rate/LP-pricing side and a standalone
  diagnostic scorer are now wired, but `results/export.py`'s scenario JSON and
  `compute_nox`/`compute_so2` in `results/emissions.py` still have no production caller —
  see the updated W3-E2 note). Added a "Wave-3 in-flight" list (W3-E2 NOx/SO2 export/
  verdict-scoring/dashboard wiring, W3-E3 mass-cap validation, W3-E5 retrofit/degradation
  trajectories) so the still-open items have a citable pointer instead of living only in
  prose. W3-E3 itself was narrowed by the mass-cap-budget-schedules wave above (real
  published CARB/RGGI budgets now populate the row and the endogenous dual is validated
  on a dispatch fixture) after a second same-day rebase; still gated `mass_cap_enabled`
  default OFF with no keeper enabling it.
- `model-methodology-spec.md` §3.3 (fleet/offer curves) and §1.6 (commitment): documented
  `measured_class_cf` (R5/EM-7 CHP consistency) and `startup_co2_tons` (R6/EM-5,
  default-off reporting adder) — neither had a spec mention before this sweep. Also
  corrected an overstatement: the spec previously implied the CAMPD class-median fallback
  (`emission_rates.class_median_rates`) covers CEMS-uncovered plants and new entrants in
  production; it does not — only pieces (a) gen-weighted average and (c) unit-composition
  mask of the four-piece estimator are wired into `fleet.py`; (b) NN conditioning and (d)
  class fallback are implemented and unit-tested but reachable only from
  `scripts/loyo_co2_rates.py` and its tests. Recorded as a follow-on, not yet scheduled.
- `docs/binning-methodology.md`: rewrote the CHP must-run post-processing section, which
  still described the pre-R5 sizing (`total_gen_by_plant − grid_gen_by_plant`, a
  rule-13-violating construction the code itself no longer uses) and the unconditional flat
  `must_run_cf=0.85`. Now matches the shipped measured-share / measured-class-CF / measured
  CO2-rate logic in `results/emissions.py::compute_must_run_emissions`.
- `docs/handoffs/emissions-co2-rate-plan-2026-07.md`: added §9.4 documenting the
  production-wiring gap above (found this sweep, not previously written down anywhere;
  numbered after the chp-btm-share wave's §9.2 and the NOx/SO2-wiring wave's §9.3 above).
- `docs/parameter-citations.md` / `frontend/data/parameters.json`: re-ran
  `scripts/generate_parameter_registry.py` (1035→1056 parameters registered). Picked up
  constants added by other recently-merged work that had never been registered
  (`ercot_rtolcap_fwd_*`, `ercot_reserve_supply_forward`, etc.) and, as a side effect,
  resolved a pre-existing duplicate `scenario.ercot_storage_as_duration_gate` entry (one
  full-citation copy kept; the orphaned duplicate slot now correctly holds the distinct
  `ercot_reserve_supply_forward` parameter). The CO2-rate-plan constants themselves
  (`CO2_RATE_*`, `CARB_FLOOR_ESCALATION`, `RGGI_RESERVE_ESCALATION`,
  `scenario.startup_co2_reporting`) were already registered from a prior run and are
  unchanged. `scripts/validate_parameters.py` and `ruff check .` both pass.

## 2026-07-05 (forward emission-control retrofit channel)

**Model.** Added a forecast-only, default-OFF channel that steps a covered
unit's forward emission rate at an **announced** control install year — closing
the gap flagged in the CO2-rate plan §7 (the trailing-window estimator only
picks up *realized* drift, never an announced SCR/scrubber). Sourced from
EIA-860's committed environmental-control pipeline
(`eia860_enviro_assoc_emissions_control_equipment.parquet`): a control in a
committed status (`PL`/`CO`/`TS`/`OZ`) with a future Inservice Year steps the
unit's rate by a class-typical removal fraction (`post = pre × (1 − removal)`),
mirroring the CCS retrofit screen's form. The install *date* is a forward driver,
not a residual, so the step is rule-13-admissible. New
`data/emission_rates.apply_control_retrofits` (pure override) +
`load_announced_controls` (EIA-860 loader). With the NOx/SO2 v2 wiring now
landed (same-day R7), the channel steps **all three** pollutants: the default
EIA-860 control map targets NOx (SCR/SNCR) and SO2 (FGD/DSI); CO2 carries no
default control (carbon capture is owned by the CCS retrofit screen, rule 15).
Applied per-pollutant over the measured `(co2, nox, so2)` map in
`fleet.apply_plant_emission_rates_v2` (`_apply_forward_control_retrofits`)
behind `ScenarioConfig.control_retrofit_forward` (default `False` →
byte-identical). Constants: `CONTROL_RETROFIT_HISTORY_END_YEAR`,
`_ANNOUNCED_STATUSES`, `_TYPE_MAP`. No keeper change, no calibration solve.

**Docs.** New design handoff
`docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md`; methodology
spec forward-emission-rate section gained the sibling-channel paragraph; tests in
`tests/test_emission_rates.py`.

## 2026-07-04 (emissions mass-cap / cap-and-trade LP constraint)

**Model.** Unified every carbon path through one `emission_rate × membership`
channel behind a new resolver, `policy/cap_and_trade.py::resolve_carbon_program`,
and added the optional endogenous mass-cap row (PP-2.1 IPM parity). The resolver
returns a per-zone membership `m_zone` plus **exactly one** price source
(invariant-asserted): the exogenous allowance-price *adder* (measured backcast /
projected forecast) or a *mass-cap spec* whose LP dual is the endogenous
allowance price. The two-source split is deliberate (plan §2): RGGI/CARB clear in
a banked, multi-sector market this power model does not contain, so their faithful
representation is the adder — the endogenous dual is a **power-sector, no-bank
scenario** price (EPA 111(d)/CSAPR or a user cap), never fitted to the observed
$/ton. No banking/borrowing in v1 (plan §8).

- **EM-6 seam closed.** `resolve_carbon_price` is now a thin wrapper over the
  resolver; forecast RGGI/CARB carries the *projected* program price (last
  realized clearing price escalated at the published CARB 5%+CPI / RGGI CCR 7%/yr
  floor-band rate) instead of zero. An explicit non-default RFF `carbon_price_path`
  still wins. Backcast measured prices unchanged (bit-for-bit).
- **`CAP_AND_TRADE_PROGRAMS` registry** (`constants.py`, all values cited):
  CAISO→CARB, NYISO→RGGI(NY), NEISO→RGGI(6 NE states) with `m_zone≡1` on load
  zones (import nodes = 0); PJM→RGGI with a fractional `PJM_RGGI_ZONE_SHARE`
  (empty → adder ships OFF pending the EIA-860→state crosswalk). ERCOT/MISO: no
  program.
- **`_build_mass_cap_rows`** (`dispatch.py`, vectorized, no hour loop): coefficient
  `m[g]·emission_rate[g]` on member `P[g,t]` columns, `≤ cap`; import/flow columns
  get zero coefficient (in-region emissions only — leakage represented, not
  suppressed). Appended after import-node rows, immediately before RPS; the dual
  is reported as `DispatchResult.co2_cap_price` (= −λ). `get_active_policy_constraints`
  returns the cap spec; the runner threads it into the dispatch builder.
- **New `ScenarioConfig` fields** (registered, in `run_config.json`, default OFF):
  `mass_cap_enabled`, `mass_cap_program`, `mass_cap_tons`, `carbon_program_price_path`.
  `assemble_mc` now accepts a membership-weighted per-generator carbon adder
  (uniform membership reproduces the scalar path bit-for-bit).

**Data.** New schema-first intake datatypes `rggi-co2-budgets` and
`carb-cap-schedule` (schemas + `curate_*.py` + orchestrator registration + data
dictionary), landing the RGGI/CARB budget & floor-price schedules that feed the
row/projection once published tables arrive. Both curators skip cleanly until
their raw CSV lands (the row stays inert) and reject 2022/H1-2026 rows (rule 22).

**Tests.** `tests/test_cap_and_trade.py` (resolver invariant, membership,
measured/projected adder, cap path, membership-weighted MC),
`tests/test_dispatch.py::TestMassCapConstraint` (trivial binding-cap dual =
switching price, simultaneous RPS+reserve+cap dual index, membership zeroing,
no-hour-loop), `tests/test_curate_{rggi_co2_budgets,carb_cap_schedule}.py`.
Two pre-EM-6 forecast-zero assertions in `test_fuel.py` / `test_capacity.py`
updated to the projected-adder behaviour.

**Docs.** `docs/handoffs/emissions-mass-cap-plan-2026-07.md` is the design;
`model-methodology-spec.md` (emissions/policy) and `docs/codebase/05-policy.md`
synced.

## 2026-07-04 (forecast-mode storage AS withholding — endogenous, no double-count)

**Model.** The forecast analogue of the measured backcast storage-AS reservation
is the endogenous reserve co-optimization, not a new exogenous haircut (rule 19).
No new LP structure — storage headroom `cap − Dis + Chg` already backs upward AS
and the ERCOT design marks storage `storage_eligible`, so with `energy_reserve_coopt`
on the forecast battery trades energy vs AS on its own cap (7-day slice: top-15%-hour
discharge −37%, hours dumping >4 GW into the peak 19→0). `ercot_storage_as_endogenous`
is now meaningful in forecast: it (a) is validated to require `energy_reserve_coopt`
(and, in forecast multi-product, `ercot_as_forward_requirement` — closing the
silent-zero-requirement footgun), and (b) switches the storage new-entry AS credit
from the exogenous `as_revenue_per_mw_yr` to one **derived from the solved co-opt's
own reserve duals** (`ancillary.realized_storage_as_revenue_per_mw_yr`, threaded via
`runner.prior_results`) — exactly one mechanism prices storage AS. The measured
`reserve_storage_as_power` overlay stays backcast-only; backcast keepers are
bit-unchanged (the gate keys on `ercot_storage_as_endogenous`, off there).

**Docs.** New `docs/storage-as-withholding-attribution-2026-07.md` (per-mode
mechanism map). Realigned `model-methodology-spec.md` §5.5 (AS value-stack slice +
endogenous reconciliation) and the reserve-subsystem note (forecast runner wiring);
`docs/storage-modeling-audit-2026-07.md` §1.3 follow-up marked resolved. Tests:
`tests/test_forecast_storage_as_entry.py` (derived credit, entry-credit gate,
forward-requirement load-scaling, config guards).

## 2026-07-04 (S5 governance closeout — protective rules, C7/C8 rubric criteria, DOF ledger, holdout quarantine CI)

**Governance (audit §8 → CLAUDE.md rules 17–26, audit-numbered 16–25):** the
legitimacy audit's protective rules land verbatim, with rule 22 (holdouts)
amended to the owner's strict quarantine — 2022 and H1-2026 see **no solves,
no scoring, no data intake** until an ISO's marker lands in
`frontend/data/backcast/calibration-complete.json`, then are scored **exactly
once** with frozen keeper configs (data intake happens at that moment). CI
enforces it: `legitimacy_diagnostics.run_d6_quarantine` (in `--keepers` mode)
and `audit_keepers` H1 fail any registered bundle with a solve year outside
2023–2025 pre-marker. **Rubric:** two first-class HARD criteria in
`calibration_verdict.py` — **C7 diurnal shape** (D-1: per-class profile r ≥
0.8, off-peak CV ratio ≥ 0.5) and **C8 forced-energy share** (D-2: < 10 %
peaker / < 30 % merchant; nuclear/CHP-steam/coal-ToP exempt) — scored from
the bundle's committed `legitimacy_diagnostics.json`
(`legitimacy_diagnostics.py --json-out`; absent artifact = SKIPPED, which now
caps the determination). Motivation recorded in the rubric doc: the loosened
C1 band absorbed a >6× ERCOT CT_PEAKER miss and every ISO's CAVEATs collapse
to ~0 in statistical mode. The **D-7 stat-mode fail-count gap** is a REPORTED
(non-gating) line per keeper on Calibration Status (`statmode_d7.json`).
**Re-gate:** all six keepers re-scored — all remain NOT-YET; caiso-51 FAILS
C7+C8 on CT (flat-floor signature, 27–33 % forced; successor probe caiso-52
named as the open scrub thread), NEISO fails C7+C8, NYISO fails C8, ERCOT
fails C8 (2023 CT 11.1 %), PJM/MISO pass both. **DOF ledger:** every keeper
attestation gains `free_parameters` (`build_dof_ledger.py`; audit_keepers E8
fails residual-sourced parameters without a root-cause ref); ercot32's "none
fitted" claim corrected (~90 inherited residual-identified scalars itemized).
**Deleted means deleted:** `ordc_reliability_deployment_mw` removed outright
(ScenarioConfig field, scarcity ORDC path hard-0, derive CLI channel); stale
retired-knob docs purged (scenarios.py PS-adder text; registry rows for the
ORDC offset, `sigmoid_midpoint`, AGT convexity, the PJM PS $10 adder). Docs
realigned: `CLAUDE.md`, `docs/model-legitimacy-audit-2026-07.md` (D-6/rule
21 amendment), `docs/calibration-determination-rubric.md` (C7/C8/D-7),
`docs/ordc-overlay.md`, `docs/backcast-measured-data-audit-2026-06.md`,
methodology spec admissibility note, calibration-report skill,
`docs/parameter-citations.md` (re-rendered).

## 2026-07-03 (MISO scarcity tail — 10-min reserve deliverability; gate 4 closed-negative)

**New gated mechanism:** `ScenarioConfig.miso_reserve_pergen` /
`--miso-reserve-pergen` — MISO per-asset reserve co-optimization at
(zone, fuel-class) pooling (`reserve_config._miso_design` pergen branch →
the shared `dispatch._build_reserve_rows_pergen`): joint `Σ P + R ≤
Σ pmax·availability` per pool-hour and `R ≤ Σ ramp10 × availability` (the
10-minute deliverable class ramp, `fleet.RAMP10_FRAC_BY_GROUP` ×
capacity, NREL/TP-5500-55588 App. H; hourly, so outaged units contribute
no ramp — `dispatch.build_variable_bounds` now accepts `(n_r, T)` pergen
caps). Class-level pooling is the documented 15 GB memory tier. Zero
residual-fitted parameters. **Empirical result (keeper
`2026-07-03-miso-39-reserve-pergen`):** the >$200 tail stays 0 h vs actual
30/37/88 — the perfect-foresight LP relieves every deliverability shortfall
by re-timing ~100 MW of South thermal/exports at ≤ $23/MWh, below the $200
first curve step; the zonal family fires more (59/64/207 h) but never
reaches the steps. Root-cause decomposition (RT sub-hourly transients /
commitment posture / missing Midwest locational family), the actual-event
anatomy (2023's tail is 100% single-hour RT spikes with DA ≈ $40), and the
bind-gate method: `docs/multi-iso/miso-scarcity-tail-diagnosis.md`. New
probes `scripts/probes/_miso_scarcity_bindgate.py` /
`_miso39_tail_gate.py`. Docs realigned: methodology spec §851 reserve
bullet (per-asset deliverability layout), `docs/multi-iso/miso-reserve-coopt.md`,
`miso-zonal-refinement-scope.md` status, the new diagnosis doc.

## 2026-07-02 (MISO zonal refinement — phase 2: reserve co-opt at 6 zones)

**Wiring bug found & fixed:** `--energy-reserve-coopt` had been silently
inert for MISO on the backcast path — the co-opt chain in
`run_calibration.run_year` ended at NEISO, so `_miso_design` (the RBDC) was
reachable only from the forecast runner, and every prior MISO "co-opt"
dashboard run (incl. probe miso-34) solved an energy-only LP. A new
`run_year` MISO branch routes to the **unchanged** design. Wired, the
market-wide RBDC is structurally inert at 6 zones (reserve dual $0 in all
26,280 h — probe `miso-37`; congestion cannot make a market-wide sum bind).
Phase-2b per scope §6 adds gated **locational reserve families**
(`miso_zonal_reserves` / `--miso-zonal-reserves`, default off; default
MISO-South): requirement = within-zone MSSC (BPM-002 §3.3.2
largest-zonal-event basis; 3,953 MW South), priced at the **published**
Zonal Operating Reserve Demand Curve (BPM-002 §5.2.1.2 / Schedule 28-A —
20% @ $200, 70% @ $1,100, 10% @ $3,300; `MISO_ZONAL_ORDC_STEPS`). Gate 4
partial on keeper `2026-07-02-miso-38-zonal-reserves`: the zonal family
fires (dual nonzero 266/287/875 h, 2025-concentrated) at re-dispatch
opportunity cost ($8–21/MWh max), but the >$200 tail stays 0 h vs actual
30/37/88 — the residual root cause is not missing reserve structure.
Keeper flipped miso-35 → miso-38 (strictly more structurally faithful, fit
unchanged). Docs realigned: `docs/multi-iso/miso-reserve-coopt.md`
(rewritten), scope doc status, methodology-spec §"resolved limitations"
bullet, `frontend/data/parameters.json` (+2 gated fields). Memory note: the
co-opt LP peaks ~16 GB at 6-zone MISO plant scale — a 12 GB swapfile
absorbs the transient (`MALLOC_ARENA_MAX=1 MARKET_SIM_HIGHS_THREADS=1`
still required).

## 2026-07-02 (Backcast dashboard migrated to the codebase site)

The root `backcast-results.html` dashboard is retired: the file is now a
static redirect stub (committed, never regenerated) pointing to the
codebase-site pages, which are the results surface —
`docs/codebase-site/backcast-runs.html` (Run Explorer, deep links
`#iso=<ISO>&run=<run-id>`) and `docs/codebase-site/calibration-status.html`
(all-ISO keeper summary, `#iso=<ISO>`). `scripts/build_manifest.py` now
assembles only the shared data files (`manifest.js`/`benchmark.js`/
`completeness.js`); the old shell template
(`scripts/probes/_backcast_shell.py`) is deleted and
`render_backcast.py`/`dashboard_add_run.py`/`regen_dashboard.py` no longer
write any HTML. `scripts/build_codebase_site_backcast.py` copies EVERY
registered run (was keeper + latest 9) into the site's data dir at deploy.
The deploy workflow stops committing the root HTML; all links (landing page,
model-updates, results-calibration, launcher) point at the codebase-site
pages. Docs realigned: calibration-report skill, CLAUDE.md #13 + Git
section, README, .gitignore, DESIGN_SYSTEM, codebase doc 06.


## 2026-07-02 (MISO zonal refinement — phase 1: 6-zone topology)

MISO's Midwest is split from the 3-zone copperplate to the **six measured
EIA-930 sub-BA (LRZ-union) zones** — West (LRZ 1), Plains (3+5), Illinois
(4), Indiana (6), East (2+7), South (8+9+10, unchanged) — per
`docs/multi-iso/miso-zonal-refinement-scope.md` (decisions D1–D7). Internal
congestion is carried by per-zone directional **CIL/CEL interface groups**
from the MISO LOLE Study Reports, expanded to per-season hourly caps in
backcasts (`transmission.build_miso_deliverability_groups`; Jan–May 2023
backfilled from PY2023-24 pending the PY2022-23 extraction); the six
internal bilateral links are deliberately non-binding placeholders and the
RDT one-way pair (3,000/2,500 MW) attaches to MISO-Plains (D3 probe: no
spurious Plains congestion, kept). `InterfaceLimit` gains `reverse_cap_mw`
and net-corridor orientation (signed member links). **Bug fix:** one-way
link bounds (`link_bidirectional`) existed in dispatch but were never wired
into either runner — the RDT had been silently symmetric; now enforced
(byte-identical for all other ISOs). Bundles persist `flows.parquet`;
structural gates report via `scripts/report_miso_zonal_gates.py`. Full
touchpoint remap (zone assignment, sub-BA load map + stale-parquet guard,
LRZ crosswalk, border seams, gas hubs, weather stations, 6-column wind
shapes, reliability floor re-derived at 6-zone granularity). Backcast
2023–2025 registered as `2026-07-02-miso-35-zonal-refinement` (new MISO
keeper — most structurally faithful; level metrics ~unchanged, scarcity
tail awaits phase-2 reserve co-opt). Docs realigned: methodology spec §1.3
(transmission/interface groups + MISO topology), CLAUDE.md,
`docs/multi-iso/04-transmission-zones-and-congestion.md`, MISO data audit
(superseded banner), parameter citations, zonal-refinement scope status.


## 2026-07-01 (Capacity-deliverability — docs reconciliation, Wave 3)

Wire capacity-deliverability into the capacity screens behind
`capacity_deliverability_limits` (default off). Consumes the 5-ISO
(PJM/MISO/NYISO/ISO-NE/CAISO) `capacity-deliverability` clean datatype
intake (CETO/CETL, LRR/LCR/CIL, LCR/TSL, LSR/MCL, LCR/MIC): Part A replaces
the calibrated simultaneous-import cap with the published seam import limit
(CAISO MIC → WECC_import); Part B gates the retirement, new-entry, and
storage-entry screens by per-zone deliverable-vs-required headroom. Gated,
default-off structural mechanism (repo rule #1) — never enabled in a
keeper. See `docs/capacity-deliverability-wiring.md` for the full mapping
and wiring detail; `model-methodology-spec.md` §5.8 for the mechanism.
This entry covers docs/dictionary reconciliation only — the model code was
already merged (#1197).

## 2026-06-30 (Reliability-floor rebuild — docs reconciliation, Phase 4)

**Documentation reconciliation for the per-(zone, class) temperature/net-load
reliability-floor rebuild** (Phase 4 of the full rebuild). The mechanism is
fully implemented and merged; all six ISOs (ERCOT, CAISO, PJM, MISO, NYISO,
NEISO) re-solved with `reliability_floor=True` and registered on the
dashboard. This entry covers the doc sync only — no model code changes.

**What changed:**

- **`docs/multi-iso/reliability-floor-feature.md`** — full rewrite to
  describe the shipped engine: per-(zone, class) `ReliabilityFloorSpec`
  (`zone`, `plant_class`, `driver`, `threshold`, `floor_pct`, `enabled`,
  `min_event_hours`, `distribution`); CSV-seeded registry
  (`reliability_floor_coeffs_<ISO>.csv`, 221 limbs, ~30 enabled); full-day
  step-function day gate (no hour-of-day windows); `floor_pct =
  commit_frac × min_stable_pct`; per-limb toggles via `reliability_floor`
  + `reliability_floor_overrides`; steam-gas longer min-run (48h event
  bridging). All references to the retired slope/cap/base/t0 + hour-of-day
  window model and the five removed legacy injectors
  (`inject_caiso_ct/nyiso_ct/nyiso_st/neiso_temp/miso_temp_reliability_floor`)
  deleted.
- **`model-methodology-spec.md`** — added §1.8 (Dispatch-Time Reliability
  Floor) documenting the shipped mechanism: registry, day gate, floor_pct
  decomposition, coefficient derivation (CAMPD CF-vs-temperature regression,
  ρ/n enable gate, no p97-CF ceiling, no residual-tuning), steam event
  bridging, config flags. Updated §1.7 admissibility rule to include
  reliability-floor coefficients as allowed forward-reproducible inputs and
  note that `ct_mustrun_per_plant` and `ct_deployment_overlay` are demoted
  to default-off diagnostic probes.
- **`docs/backcast-measured-data-audit-2026-06.md`** — added
  reliability-floor rebuild section recording that `ct_mustrun_per_plant`
  (EIA-923) and `ct_deployment_overlay` (CEMS) are demoted to default-off
  probes, the p97-CF ceiling crutch is removed, and all six rebuild keepers
  have `ct_mustrun_per_plant=False` (no outcome-pinned floor).

## 2026-06-27 (NYISO ST_GAS temperature reliability floor + ISO-aware solar actuals — new keeper `nyiso 34 st-tempfloor`, CALIBRATED-WITH-CAVEATS)

**Keeper change: NYISO `nyiso 33 ct-tempfloor` → `nyiso 34 st-tempfloor` — the
first NYISO keeper to clear the determination gate (CALIBRATED-WITH-CAVEATS; all
prior were NOT-YET).** Adds a temperature-keyed downstate **ST_GAS (gas-steam)
local-reliability floor** (`--nyiso-st-reliability-floor`, NYISO default-on;
`transmission.inject_nyiso_st_reliability_floor`), the gas-steam companion to the
CT floor, plus two structural corrections it depends on. NYISO's downstate steam
fleet (NYC zone J Ravenswood/Arthur Kill/Astoria; Long Island; Capital) runs a
persistent in-city / cable-islanded reliability baseline an energy-only LP zeroes
out. The floor is a **persistent 24-hour baseline** (`base_24h`) with an **evening
cooling hot-limb** layered on over HB14-21 via `maximum`, applied **per unit,
pro-rata** (each in-pocket unit floored at `frac × its own available capacity`),
keyed per zone to its load-center daily max temperature (NOAA GHCN: Islip / Central
Park / Albany). Coefficients (`transmission.NYISO_ST_FLOOR_COEFFS`) regressed a
priori from the measured per-zone CAMPD ST_GAS CF vs zone TMAX, 2023-2025
(`scripts/derive_nyiso_st_reliability_floor.py`; archived
`data/raw/nyiso-weather/nyiso_zone_tmax_daily.csv`). **Two structural corrections
(both fix real methodology errors that were suppressing the costly in-city
units):** (1) **When-available CF basis** — `frac` is regressed on CF normalised
by *available* capacity (nameplate net of the unit-outage derate), not by nameplate
over all hours; since the floor is applied as `frac × pmax × availability`,
regressing on the all-hours CF double-discounted the outage downtime and floored
Astoria/Arthur Kill near zero. On the available basis these units run a steady
~0.3-0.4 baseline when committed (NYC temperature corr → ~0, a flat in-city
must-run). (2) **Ravenswood outage routing** (`data.outages._FLEET_GROUP_OVERRIDE`)
— Ravenswood (2500) is a mixed CC/ST facility classified ST_GAS, but CAMPD tags its
units `CC_REGULAR`, so its outages never derated its ST_GAS bin (over-available →
floor over-forced it); route plant 2500's outages to its ST_GAS bin. A
capacity-derate check confirmed the under-running units are not ceiling-capped
(0.66–0.92× nameplate in summer CAMPD), so the under-run was a
dispatch/availability/offer effect, not a derate. ST_GAS lands under actual,
conservative not pinned (rules #11/#12). **Effect — HARD C1 fuel-mix now PASSES
every gas class both scored years:** ST_GAS 2023 −0.24, 2024 −3.77 → −1.03 TWh
(PASS); CC_REGULAR/CT_PEAKER PASS; dispatch_corr PASS; C5a CO2 in band all years.
Plant distribution improved (Arthur Kill near-exact, Astoria/EF Barrett recovered,
Ravenswood no longer over-forced); per-plant residuals offset within the C1 band.
The remaining caveats are all SOFT price criteria (C3a/C3b/C3c) — the ledgered
reserve-scarcity (ORDC) + min-gen-floor frontier, kept per rule #1.

**Benchmark-basis fix (reporting only, not a model lever):**
`results.calibration.actuals_source(klass, iso)` is now ISO-aware — NYISO solar
routes to **EIA-923**, since EIA-930 NYIS grid solar is a structural 0 (NYISO
solar is overwhelmingly behind-the-meter / net-metered, invisible to the
balancing-area telemetry). `render_calibration_html` keeps NYISO solar's
`classFull` on the EIA-923 utility-scale total (2.05 / 2.90 TWh for 2023/2024) and
mirrors it into the `e930` bench slot, so the dashboard scores the model's ~2 TWh
of dispatched grid solar against ~2 TWh, not a spurious zero. Docs realigned:
`docs/calibration-best-so-far-nyiso.md` (new keeper block); the mechanism is fully
specified in the run-34 `calibration_attestation.json`.

## 2026-06-25 (NYISO path-B commitment-gated synchronised reserve — REJECTED probe)

**No keeper/methodology change; NYISO keeper stays `nyiso 27 cc-offer`.** Wired
the path-B route of the default-off `--nyiso-synchronised-reserve` lever: with
the P2 commitment screen on (`--commitment`), the NYC spinning family rides the
ordinary class-1 quick-start headroom and commitment is the online gate
(`apply_commitment_with_coal_pin` zeroes decommitted availability, so the row
equals `Σ_online(pmax − P)` — the physically-correct synchronised headroom,
MILP-free), and a new `commitment.reserve_adequacy_commit` force-commits NYC
quick-start to the measured 250 MW spin requirement (`NYISO_SPIN_FRACTION` × NYC
10-min total). New helpers `scarcity.nyiso_spin_requirement_mw` /
`nyiso_spin_eligible`, constant `NYISO_SPIN_FRACTION`, config field
`ScenarioConfig.nyiso_spin_headroom_frac` (+ `--nyiso-spin-headroom-frac` CLI).
Tested all 3 years as `nyiso 31 synch-commit [probe]`: **a true no-op** — every
scored metric reproduces the keeper exactly (C3c >$300 1/0/8; CT_PEAKER
−1.30/−1.51; C3a 2024 −9.7%; P1==P2). Root cause: the committed NYC quick-start
fleet holds ~1,700 MW of online headroom in the tightest hours vs a 500 MW
requirement, so the measured reserve never binds and no RCPF tail forms;
commitment removes only offline pmax, not the dominant committed-but-backed-off
headroom. Both path A (`nyiso 29`) and path B are thus insufficient with grounded
inputs — the >$300 downstate tail is an accepted, ledgered open frontier on
nyiso-27 (closing it would need an ungrounded requirement/adder, forbidden by
rule #12). Wiring kept as a NYISO-only default-off scaffold; other ISOs and
NYISO-without-the-flags byte-identical (103 reserve/dispatch/commitment tests
green). Docs realigned: `docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md`
(Path B implemented & rejected) + `docs/handoffs/nyiso-synchronised-reserve-probe-2026-06.md`
(status update).

## 2026-06-25 (Weather-year forecast ensemble — G13 built)

**New forecast-robustness tool, no keeper/calibration change.** Implements the
weather-year sample/ensemble from `docs/forecast-methodology-gaps-2026-06.md`
G13 (was DESIGN-ONLY). A forecast pins one representative weather year for its
load + VRE capacity-factor shapes (`ScenarioConfig.weather_year`); the ensemble
runs the *same* forecast once per weather draw over the new
`constants.WEATHER_YEAR_POOL` (2023-2025, bounded by EIA-930 hourly coverage)
and reports the cross-draw distribution of each annual metric. A weather draw is
an admissible forecast *input*, not a measured outcome (CLAUDE.md #10), so this
is methodological robustness, not a backcast pin. New module
`src/market_sim/ensemble.py` (`weather_ensemble_configs` / `run_weather_ensemble`
/ `summarize_ensemble` / `export_ensemble_json`) + `market-sim ensemble` CLI
subcommand (`--config`, `--iso`, `--weather-years`, `--workers`, `--out`).
Members are independent solves and run in parallel (CLAUDE.md #16), each caching
under its own `weather_year`-hashed `cache_key`; the report reuses the canonical
`export._summarize_year` aggregation and adds mean/std/min/p10/p50/p90/max plus
per-fuel generation distributions and the raw per-member summaries. Tests:
`tests/test_ensemble.py`.

## 2026-06-25 (Forecast hydro monthly-energy budget — forward analogue + wet/dry scenario knob, G9)

**Implements the forecast analogue of the measured EIA-930 hydro budget level
(forecast-methodology-gaps-2026-06.md G9); no keeper re-solve, default-off,
byte-identical baseline.** The hydro monthly-energy-budget LP constraint
(dispatch picks *when* within a month each plant generates) is already the
forward mechanism; only its monthly *level* was a measured input
(`--hydro-eia930-monthly` pins it to EIA-930 NG:WAT). This adds the forward level
source:

- **Normal-water-year climatology** — `data.eia_loader.climatological_monthly_hydro`
  returns the per-month mean of measured EIA-930 NG:WAT across
  `constants.HYDRO_CLIMATOLOGY_YEARS` (2021–2025; uncovered years skipped), so a
  forecast year inherits a normal water year rather than a single year's draw.
- **Wet/dry hydro-year lever** — `ScenarioConfig.hydro_year` (`"dry"`/`"normal"`/
  `"wet"`) scales the climatology by `constants.HYDRO_YEAR_MULTIPLIER`
  (0.85/1.0/1.15, bracketing the ±15% central reservoir-system inter-annual
  range). `data.hydro.forecast_monthly_hydro` combines the two and feeds the
  existing `load_hydro_budget(monthly_target_mwh=…)` seam (per-plant within-month
  shares preserved — level only).
- **CLI** — `--hydro-forecast-budget` + `--hydro-year {dry,normal,wet}` on
  `run_calibration_full.py`, the forward mirror of `--hydro-eia930-monthly`
  (mutually exclusive; threaded through `run_year` → `_hydro_fleet`).

Pure level input, never pinned to a realized outcome (CLAUDE.md #1/#12); the
within-month dispatch mechanism is untouched. Tests in `tests/test_hydro.py`
(`TestForecastHydroBudget`).

## 2026-06-25 (Forecast monthly maintenance shape — spec §1.7 / gap G12 BUILT)

**Replaced the flat shoulder-POF heuristic with a historically-derived monthly
maintenance shape, applied in forecast mode.** The forecast availability model
previously smeared each plant group's planned-outage factor (POF) evenly across
the five `_CC_SHOULDER_MONTHS = {3,4,5,10,11}`. It now distributes POF across the
year by `MAINTENANCE_MONTHLY_SHAPE` (`config/constants.py`) — a per-plant-group
12-month weight learned from the measured timing of spring/autumn maintenance in
the committed CAMPD unit-outage extracts (all six ISOs pooled — a forecast shape,
not pinned to any backcast year; `scripts/derive_maintenance_shape.py`). Each
group's weights are the planned-maintenance excess over its annual-minimum
(forced-outage-floor) month, normalized to a month-length-weighted mean of 1, so
the per-hour planned-maintenance derate is `POF·(shoulder_hours/8760)·w[month]`.
Because the shape has a month-weighted mean of 1, the group's **annual POF budget
(`POF·shoulder_hours`) is conserved exactly** — only the seasonal distribution is
sharpened (peaks Apr and Oct–Nov, ≈0 at the Jul/Aug summer peak, modest in
winter; forecast ERCOT thermal availability dips to ~0.754 in April vs ~0.854 at
the July peak). Gated by `ScenarioConfig.maintenance_monthly_shape` (default on,
**forecast mode only**); `False` restores the legacy flat block. **Backcast runs
are byte-identical** — their POF comes from the historic overlay
(`data/outages.py`), which is untouched, so every calibration keeper is
unaffected. New `TestMaintenanceMonthlyShape` covers budget conservation, summer-
peak protection, spring/autumn reshape, and the backcast no-op; the legacy
`TestThermalAvailability` mechanics tests are pinned to the flat block. Forecast
sanity run (real ERCOT fleet, 2024, full 8760): dispatch solves Optimal, budget
conserved to ~7e-4 capacity-weighted. Spec §1.7 and `docs/forecast-methodology-
gaps-2026-06.md` G12 updated (DESIGN-ONLY → BUILT).
## 2026-06-25 (CAISO forward WECC-tie seam — reference-price import + ATC corridor cap, G8)

**Built the forecast-native replacement for CAISO's two MEASURED WECC-tie levers**
(`forecast-methodology-gaps-2026-06.md` G8). The keeper priced each per-hub
corridor at the measured OASIS hub LMP (`caiso_per_hub_intertie`) and capped it at
the measured p95 net-import envelope (`caiso_corridor_flow_limit`); both go inert
in a forecast year. Two new default-off flags carry the forward path:

- `caiso_intertie_reference_price` — prices each corridor from
  `(henry_hub[year] + gas_basis) × marginal_heat_rate × load_shape` (the same
  reference-price interface PJM/MISO use), specialised to the two ties: COI/Path-66
  proxies the Pacific-NW at Malin (gross-load shape), Path-46/WOR the desert-SW at
  Palo Verde (**net-load** shape, so its midday price dips with the solar glut).
  HR anchors are 3-year-mean structural values; the shape is the EIA-930 CISO
  series (a forward driver). New: `NeighborInterface`-style `CaisoHubNeighbor` +
  `CAISO_PER_HUB_NEIGHBORS` (constants), `neighbor_price.caiso_hub_reference_price`
  / `caiso_hub_load_shape`, `transmission.inject_caiso_per_hub_reference_prices`.
- `caiso_corridor_atc_forward` — caps corridor import flow at a forward ATC =
  `TTC × posted-ATC fraction × clip(1 − k × solar_frac(t), floor, 1)` (a capability
  limit shaped by forward CISO solar penetration, not the measured flow). New:
  `transmission.forward_corridor_atc_envelope`, `eia_loader.caiso_solar_fraction`,
  `CAISO_CORRIDOR_ATC_SOLAR_K` (constants). Export keeps the physical TTC.

The measured hub LMP + p95 envelope are kept **only** as the backcast realization
the formula is validated against (`scripts/compare_caiso_intertie_formula_vs_measured.py`).
**Honesty gate met** (CLAUDE.md #10/#12): import price from forward gas/HR/shape,
deliverability from a capability — neither pinned to the measured realization.
Validation: the formula reproduces the measured desert-SW diurnal shape at corr
**0.96** (2024) with no measured-LMP input; forward 3-year re-solve keeper
`caiso_intertie_forward_3yr`. Tests: `tests/test_caiso_intertie_forward.py`. Off
the flags every ISO/run is byte-identical.

## 2026-06-25 (NYISO `nyiso 30 fwd-band` — forecast-aware import reconciliation band; new NYISO keeper; forecast gap G10 closed)

**Forward band source for the NYISO import reconciliation (G10).**
`transmission.build_import_node_reconciliation` is now **mode-aware**, giving the
priced import-node net-interchange band a forward analogue (forecast gap G10,
`docs/forecast-methodology-gaps-2026-06.md`):

- **Backcast** (`mode="backcast"`, the calibration path) targets the **measured**
  EIA-930 NYIS net-interchange schedule (`eia_loader.nyiso_net_interchange`) — the
  realization, **byte-identical** to the prior `nyiso 27 cc-offer` keeper.
- **Forecast** (`mode="forecast"`) targets the **neighbor's forecast net
  position**: a new `ScenarioConfig.nyiso_forward_net_import_twh` (annual NYISO
  net import in TWh, from the PJM / Hydro-Québec / Ontario / ISO-NE forward export
  outlook) shaped to twelve monthly targets by the forecast load
  (`eia_loader.nyiso_forward_net_import_monthly`, so imports track load and the
  band responds to changed conditions — the rule-#12 forward-reproducibility
  test). When no forecast is supplied the band **relaxes to the bare priced-seam
  economics** (returns `None`); the seam clears endogenously, never pinned to a
  measured monthly total.

**New NYISO keeper `nyiso 30 fwd-band`** (all years 2023/2024/2025). The backcast
LP is unchanged vs `nyiso 27 cc-offer` (same flags, same `_NYISO_OFFER_CURVE`,
P1, no commitment; verdict + exceptions ledger carried over), so the re-solve
**confirms metrics hold** while proving the mechanism is forward-ready: the
priced seam clears **within** the ±2% band rather than on the measured total —
model net interchange −23.03 / −20.23 / −19.18 TWh vs measured
−23.45 / −20.35 / −19.09. Determination NOT-YET (unchanged: the CC-offer /
NYC-peaker / RCPF reserve-scarcity frontier remains the open MODEL MISS, out of
scope here). Tests: `tests/test_import_node_reconciliation.py::TestForwardBandSource`.
Dashboard top-15-per-ISO retention pruned the oldest NYISO
(`nyiso-16-transco-daily`); keeper pointer 27 → 30.

## 2026-06-25 (NYISO probe `nyiso 29 synch-reserve` — REJECTED: online-only spinning reserve confirms mechanism, insufficient for the tail)

**Rejected probe; keeper stays `nyiso 27 cc-offer`; live source reverted to the
keeper (no code landed).** Path A of the downstate synchronised-reserve fix (PR
#877 / `docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md`
recommendation #2): a NYISO-only, default-off lever
(`--nyiso-synchronised-reserve` / `ScenarioConfig.nyiso_synchronised_reserve`)
adding a NYC 10-minute **spinning** sub-requirement = `NYISO_SPIN_FRACTION` (0.5,
the published ½-largest-contingency rule) × the NYC 10-min total = **250 MW**,
supplied by a third, **online-bounded** reserve class. `dispatch._build_reserve_rows`
gains an online block (`R[c,z] ≤ Σ online P`) so only already-generating capacity
backs spin; with the standard headroom row the effective bound `R ≤ min(P, cap−P)`
forces idle NYC peakers to commit — attacking PR #877's confirmed root cause
(the pure-ED LP credits an idle peaker's full pmax as deliverable reserve).
**Mechanism confirmed** (CT_PEAKER 2023 −1.30→−0.92, 2024 −1.51→−1.05 TWh; CC
over-run shrinks) but **insufficient for the tail**: C3c >$300 hours unchanged
(1/0/8) and C3a 2024 regresses −9.7%→−11.0% — the grounded 250 MW spin clears
cheaply (online quick-start covers it) so the RCPF never fires, and the
committed-for-spin peakers add low-cost pmin energy in non-scarce hours, dipping
the mean. Exactly PR #877's prediction → scopes **path B** (zonal/family
commitment-aware reserve where the FULL downstate 10-/30-min stack binds on
committed-only headroom). The path-A implementation is preserved in the bundle's
`model_changes.diff`; live source is the run-27 keeper (all ISOs byte-identical).
C6 PASS, determination NOT-YET (caveat budget). Docs: new handoff
`docs/handoffs/nyiso-synchronised-reserve-probe-2026-06.md`; dashboard top-15-per-ISO
retention pruned the oldest NYISO (`nyiso-15-transco-z6`). No methodology-spec
change (no code landed).
## 2026-06-25 (NYISO synchronised-reserve — path-A scaffold KEPT default-off + path-B core helper)

**Follow-on to the rejected `nyiso 29` probe above.** Rather than leaving the
path-A lever only in the probe's `model_changes.diff`, this branch keeps it as a
**default-off scaffold in live source** (`--nyiso-synchronised-reserve` /
`ScenarioConfig.nyiso_synchronised_reserve`; NYISO-only; byte-identical when off,
all other ISOs and NYISO-without-flag unchanged): `dispatch._build_reserve_rows`
carries an `online_gated` per-class mask + `online_rho`, and
`scarcity.nyiso_reserve_coopt_inputs` builds the NYC spinning family (req = ½ the
NYC 10-min total). It reproduces the probe's confirmed-but-insufficient result
(CT_PEAKER/CC volume mix improves; >$300 tail unchanged), kept as the base for
path B rather than as a keeper. **Adds the path-B core**
`commitment.reserve_adequacy_commit` (+ unit tests; additive/unwired):
force-commits the cheapest-startup downstate quick-start until committed headroom
covers the spinning requirement, so the spinning family can bind on
`Σ_online(pmax−P)` — the real tail lever, MILP-free via the existing P2
commitment mask. Path-B design recorded in
`docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md`.

## 2026-06-25 (NYISO probe `nyiso 28 native-hr` — REJECTED: native CAMPD marginal-HR re-level craters LMP)

**New derivation tool + rejected probe; keeper stays `nyiso 27 cc-offer`.** Added
`scripts/derive_campd_marginal_hr.py` (the CEMS analogue of
`derive_dam_offer_hrmults.py`): per-class `committed`/`econ_low`/`econ_high`
incremental-HR multipliers from an ISO's own unit-level CAMPD CEMS, expressed vs
the class cap-weighted base_HR (output `data/raw/reference/<iso>_campd_marginal_hr_summary.csv`).
The `nyiso 28 native-hr` probe re-grounded `_NYISO_OFFER_CURVE` CC_REGULAR /
CC_CHP / ST_GAS to NYISO's OWN derived medians (`CC_REGULAR 0.632/0.784/0.925`,
`CC_CHP 0.809/0.989/1.103`, `ST_GAS 0.818/0.825/0.830`), removing the
ERCOT-borrowed CC reach (1.21/1.24) and ST_GAS shape (1.10/1.45). It **craters
`C3a`** to −24.0/−26.5/−23.5 % across 2023-25: the bare CEMS marginal HR is the
marginal **cost**, not the **offer** — it omits the competitive offer **markup**
that NYISO has no disclosure to measure, which the borrowed reach was proxying.
Per rule #1 a run missing real structure (the markup) is not a keeper. The
steam-side re-level *was* directionally right (2024 `ST_GAS` under-run −4.14 →
−2.22 TWh). Live source reverted to the run-27 keeper curve (probe preserved in
its bundle + dashboard); C6 PASS, determination NOT-YET. Docs realigned:
`docs/calibration-best-so-far-nyiso.md`, `docs/cc-high-cf-investigation.md`,
`docs/handoffs/pjm-cc-level-tuning-2026-06.md` (per-ISO-per-class native grounding
is the standing pattern; a no-offer-disclosure ISO still needs its markup
component grounded — run-29 path: a NYISO markup on top of the native marginal HR).

## 2026-06-25 (NYISO keeper `nyiso 27 cc-offer` — CC offer-level re-level to CAMPD marginal-HR reach)

**New NYISO keeper, one source edit.** Re-solved the `nyiso 26 cc-nameplate`
config (byte-identical flags, P1, no commitment) with the NYISO CC offer **level**
raised toward the CAMPD CC marginal-heat-rate SRMC reach: `_NYISO_OFFER_CURVE`
`CC_REGULAR` `econ_high` **1.12 → 1.21** and `CC_CHP` **1.15 → 1.24** (the same
`1.21×` base_hr fit ERCOT's keeper uses; `econ_low`/`committed`/`peak` unchanged).
The rule-#1 second step: `nyiso 26` fixed the structure (full-nameplate CC + the
Ravenswood steam HR, no wall), `nyiso 27` calibrates the offer level on it,
grounded in the CAMPD CC marginal HR, not the residual (rules #11/#12). Effect vs
`nyiso 26`, all predicted-direction, no re-walling / no merit inversion / no 2025
overshoot: `2023 CC_REGULAR +2.09 → +1.70 TWh`, `ST_GAS −1.48 → −1.26`; `2024
CC_REGULAR +2.39 → +2.09`, `ST_GAS −4.31 → −4.14`; `C3a` 2023 `−8.9 %` → in-band,
2024 `−11.0 %` → `−9.7 %`, 2025 in-band; `C3b` 2024 `0.250 → 0.243`. C6 PASS;
determination NOT-YET (residual CC/ST + `C3a` 2024 honest misses at the grounded
offer ceiling + the ledgered gas basis floor). The CC offer-level frontier
(`docs/handoffs/pjm-cc-level-tuning-2026-06.md`) is **DONE for NYISO**. Docs
realigned: `docs/calibration-best-so-far-nyiso.md` (new keeper banner),
`docs/cc-high-cf-investigation.md` (NYISO resolution), the PJM handoff (NYISO
status). Top-15 retention dropped `nyiso-13-citygate-gas`.

## 2026-06-25 (NYISO keeper `nyiso 26 cc-nameplate` — re-solve on merged nameplate-CC code)

**New NYISO keeper, no source change.** Re-solved the `nyiso 25 steam-merit`
config (byte-identical flags, P1, no commitment) on the merged code: the
Ravenswood mixed CC+ST steam-HR fix (PR #850) + `cc_nameplate_summer_derate`
(commit `a8b0e55`, AUTO-ON for PJM/NYISO/NEISO). Combined effect is the predicted
structural direction — nameplate CC capacity + steam correctly above CC
**over-closes** the 2023 within-gas merit split (`CC_REGULAR −3.47 → +2.09`,
`ST_GAS +2.76 → −1.48`; 2024 likewise). CC now mildly over-runs on energy
(~+2 TWh/yr) and depresses LMP (`C3a` 2023 −8.9 %, 2024 −11.0 %; 2025 +9.3 % →
in-band) — the documented CC offer-level frontier (fix via `_NYISO_OFFER_CURVE`
`econ_low/econ_high`, not a re-walled capacity). Kept per rule #1 as the most
structurally faithful NYISO config; C6 governance PASS, determination NOT-YET.
Docs realigned: `docs/calibration-best-so-far-nyiso.md` (new keeper banner),
`docs/cc-high-cf-investigation.md` (NYISO confirmation of the mild over-run).

## 2026-06-24 (Calibration verdict — C1 complete-vintage-only; dashboard volume basis; ERCOT keeper)

**C1 asset-class tolerance applies to complete-vintage years only.**
`scripts/calibration_verdict.py:score_fuelmix` now SKIPs every fossil class for
preliminary-EIA-923 years (year ≥ `PRELIM_923_FROM_YEAR` = 2025) instead of gating
them: a preliminary 923 release under-reports thermal generation already on the grid
(per the authoritative EIA-930 total) and EIA-930 carries no per-class split, so
there is no complete per-class actual to gate against. The raw `model − actual` gap
is kept only as a report-only `vintage_gap_twh` annotation with no status effect;
the boundary auto-extends from the constant as a year's 923 finalises. Complete
vintage years (2023, 2024) keep the full PASS/FAIL gate, and C2's EIA-930 family
reconcile still covers the preliminary year. This **supersedes** the per-class
preliminary-923 *vintage credit* (`_vintage_credit`, CAVEAT path) added earlier the
same day — the function, its call and the CAVEAT branch are removed so C1 no longer
both skips and credits.

**Effect.** ERCOT run154's only C1 breach — 2025 `CC_REGULAR` +6.15 TWh — is now
SKIPPED as a preliminary-vintage class (model gas matches EIA-930 to 1.0%; EIA-923
under-reports 5.8 TWh of 2025 gas), so C1 PASSES. run154 stays **NOT-YET** — C2 2024
coal (+3.0%) and C3a/C3b price (2024) still block it. Rubric §C1 and the run154
attestation updated; tests in `tests/test_calibration_verdict.py`.

## 2026-06-24 (ERCOT run154 — net-load Waha delivered-gas step + Laredo zone fix)

Replaced the run152/153 per-plant Waha **contract haircut** (which was backwards
— it kept 100%-spot Permian/Laredo at the full hub collapse and over-priced
100%-contract Ector) with a **structural net-load-indexed West delivered-gas
step**, and fixed a fleet zone misassignment.

**1. Two-regime net-load Waha step** (`fuel.apply_ercot_west_netload_gas_shape`,
rewritten from the earlier linear shape). The West/Panhandle Waha basis is split
by the **measured** Waha negative-price-day frequency (new `neg_day_freq` column
in `data/raw/ercot_zonal_gas_hub.csv`; 2024 EIA-authoritative 0.42, id=64445)
into a collapsed (lowest net-load) and a firm (highest net-load) regime; the firm
level is the cited firm Waha delivered basis and the deep value is forced by the
measured annual-mean constraint. New `ScenarioConfig.ercot_west_gas_collapse_freq`
(override) and **`ercot_west_gas_delivered_floor`** — a burner-tip delivered floor
(the hub goes to ~$0 but a plant's delivered gas never does; flooring the collapse
regime at the generic ~$0.10 gas floor created a cheap-hour magnet that pulled
low-HR West CTs into low-demand hours). Net-load = load − wind − solar, so the
shape regenerates forward (admissibility #10/#12); no fit to the CT residual.

**2. Laredo (3439) zone fix.** Corrected West→South in
`custom-bin-assignments.csv` — Laredo is Webb County / Rio Grande border (ERCOT
South), not West/Permian, so it now pays measured South TX delivered gas, not the
Waha hub, and idles correctly (2024 model 56 vs real 52 GWh).

Result (run154, registered `2026-06-23-run154-netload-gas-laredo`, NOT-YET):
CT_PEAKER in band all three years (−2.27/−1.01/−1.48 TWh), fixing the run151
keeper's accepted +6.8/+7.05 TWh CT over-run (which was wrongly attributed to
intra-Permian transmission — West export uses only ~2 of 10 GW TTC). LMP MAE
27.8/15.3/11.7 (flat). Documented residual: CC_REGULAR 2025 +6.15 TWh absorbs the
freed CT energy (masked in run153; next root-cause). Docs realigned:
`docs/ercot-west-netload-gas-shape-2026-06.md` (rewritten),
`docs/ercot-ct-waha-offer-floor-2026-06.md` (superseded-banner).

## 2026-06-23 (CAISO imports — aggregate simultaneous-import cap + delivered-cost basis)

CAISO's bidirectional priced intertie reversed to export correctly but
**over-imported** on both the deep tail and the body. Two structural fixes,
each addressing a distinct cause.

**1. Aggregate WECC→CAISO import cap.** Path 66 / COI (4,800 MW) and Path 46 /
West-of-River (10,623 MW) carry correct *individual* ratings, but their 15,423
MW **sum is not the simultaneous import capability** — the two corridors draw on
overlapping WECC generation and contract paths. With no aggregate limit the
11.4 GW priced-import supply curve (`IMPORT_TRANCHES["CAISO"]`) cleared its full
depth in CAISO's tightest hours, putting the modeled deepest-import tail at
~−11.2 GW versus the EIA-930 CISO measured p01 of ~−8.3 GW. New general
mechanism: `ISOConfig.interface_limits` (an `InterfaceLimit` groups a set of
links under one cap), resolved by `transmission.build_interface_groups` and
enforced as **one LP row per group per hour** (`dispatch.build_constraints`,
vectorized with `scipy.sparse.kron` — no hour loop) capping the *signed sum* of
the member links' flow at the simultaneous rating. The component per-link TTCs
are untouched; the row binds only when several would otherwise load past the
aggregate. CAISO declares an 8,300 MW `WECC_import` cap (published Maximum
Import Capability / measured p01); every other ISO declares none, so their LP is
identical. The rows append after the energy/storage blocks and before
hydro/RPS/reserve, so the front-anchored energy-balance duals and the
end-anchored RPS/reserve duals keep their positions. *2024 P1: import tail p01
−11,172 → −8,300 MW (actual −8,302).*

**2. Per-tranche delivered-cost basis over the measured hub MCE.** The hub-price
injector priced every import tranche at the neighbor-hub **energy (MCE)
component only** (~$38, system-wide), flattening the rising delivered merit
order so a deep slug cleared whenever CAISO's price crossed ~$38 — the body
over-imported (median −6.1 GW vs actual −4.2). `measured_import_hub_prices`
returns the energy component *at the neighbor hub*;
`inject_caiso_import_hub_prices` now **delivers** each tranche to the CA border
via `constants.CAISO_IMPORT_DELIVERY_BASIS`: a transmission **line-loss markup**
(a fraction of the energy price, so it scales with price and responds to changed
conditions) plus the **OATT point-to-point wheeling charge** ($/MWh), keyed by
import path. A reproducible *physical* input, not a residual-fitted offset
(claude.md #12). The desert-SW gas blocks carry the basis here but are then
overwritten off measured gas by `inject_caiso_import_gas_coupling`, so the basis
mainly shapes the non-gas blocks (`PNW_*`, `DSW_solar_PV`). *2024 P1: body
median import −6,076 → −4,312 MW (actual −4,183); import hours 83.8% → 86.3%.*

Both mechanisms are structurally correct (a real simultaneous limit; a real
delivered-import premium) and both nudge the price level *up* slightly; per
claude.md #1 they stay in regardless — the residual CAISO price-level item is
pre-existing and separately owned. The diurnal phase error (corr ~−0.69) is the
separate bidirectional-zone task. Tests: `test_dispatch`
(`TestInterfaceGroupLimit` — cap binds below the per-link TTC sum, no-op without
groups), `test_transmission` (`TestInterfaceGroups` — CAISO config + group
resolution), `test_caiso_import_hub_prices` (delivered-cost basis).

## 2026-06-23 (scripts/derive_load_shares.py — fix stale ERCOT paths + EAST mis-mapping)

`scripts/derive_load_shares.py ercot` was un-runnable and inconsistent with the
live model after the W1 data collapse. Two fixes:

- **Paths.** `REF` now points at `data/raw/reference/` (was the pre-collapse
  `data/reference/`), where the NP6-345-CD `*ACTUALSYSLOADWZNP6345_csv.zip`
  archives live. `CAISO_TAC_DIR` / `NYISO_DIR` / `NEISO_DIR` likewise repointed
  from the dead `inputs/raw-data/...` root to `data/raw/zone-specific-demand/`.
- **EAST → Northeast.** `WZ_TO_ZONE` mapped `EAST -> North` and `ZONES` listed
  only 6 zones, but the live model (`eia_loader._ERCOT_LOAD_ZONE_GROUPS`) carved
  the EAST weather zone into its own **Northeast** transmission zone (behind the
  NE_LOB export limit). Fixed `EAST -> "Northeast"` and added "Northeast" to
  `ZONES`. `FAR_WEST` stays folded into West (the Far_West/Permian split was
  rejected — see `docs/ercot-far-west-zone-split-2026-06.md`).

The script now prints 7 transmission zones summing to 1.0. Its clean one-pass
derivation gives **North 0.3064 / Northeast 0.0351**, vs the committed
**0.3081 / 0.0335**; every other ERCOT zone matched the script exactly. The
committed North/Northeast split predated the consistent EAST-carve-out, so the
**iso_configs ERCOT `load_share` fallbacks were updated to the measured values**
(North 0.3081→0.3064, Northeast 0.0335→0.0351; South 0.0799→0.0800 absorbs the
4-dp rounding residual so the literals sum to exactly 1.0). These are
fallback-only — the native-load hourly shapes drive actual demand — so the
change is low-risk.

## 2026-06-22 (calibration page — fleet-wide fossil CO2 metric, activating the C5a gate)

The dashboard's CO2 verdict (`calibration_verdict.score_co2`, criterion **C5a**)
has been SKIPPED on every run for want of a committed emissions actual. It now
has one. `market_sim.data.egrid` derives a **fleet-wide** per-plant fossil CO2
emission rate (kg CO2 / net MWh): eGRID 2023/2024 (`PLCO2AN` short-tons ×
907.18474 / `PLNGENAN` net-MWh) is the base — the only source spanning the small
non-CEMS units — **overridden by the CAMPD-measured intensity**
(`plant_emission_rates.parquet`) where it exists (eGRID's large-plant CO2 is
itself CEMS-derived, so the two are consistent). `scripts/derive_fossil_co2_rates.py`
writes the `fossil_co2_rates.parquet` artifact (2,518 fossil plants for 2023, 131
CAMPD-measured + the rest eGRID).

`render_calibration_html.build_payload` net-generation-weights those rates within
each dispatch class to a tonnes/MWh intensity (over the bundle's EIA-923 fossil
plants, ~98% gen-coverage), then applies it to the same grid-delivered class
totals the generation-mix benchmark uses: `bench[year].co2.egrid` (actual Mt) and
`run.years[year].co2.model` (model Mt). So the metric is the model's generation
mix re-weighted by measured carbon intensity — the independent check on the
coal/gas split a pure MWh volume gate is blind to (swapping coal MWh for gas MWh
passes the volume gate but moves total CO2, since coal is ~2× the intensity).
Sanity: ERCOT 2024 ≈ 172 Mt, PJM 2024 ≈ 276 Mt. The backcast dashboard gains a
**Fossil CO2 — model vs actual (Mt)** panel (per-class + total, ±7% C5a badge).

**Nothing is pinned to an outcome** (claude.md #11): an emission rate is a
reproducible physical input that regenerates for a forward year and responds to
changed conditions — the admissibility test the audit applies to fuel prices and
outages. The actual is `rate × generation`, not observed CO2 fed back to drive a
residual. Tests in `tests/test_egrid.py` and `tests/test_co2_metric_payload.py`.
Existing committed run payloads surface the metric once re-rendered (the model
side is already in their `gmModel`; the actual needs only the committed
`eia923.parquet` + the eGRID artifact).

## 2026-06-22 (PJM energy+reserve co-optimization — built, wired, and the bind-gate result)

The in-LP energy+reserve co-optimization the PJM price-formation campaign
(`docs/multi-iso/pjm-reserve-ordc.md`) named as the lever for the missing
$75–200 afternoon regime is now built and wired, and the bind gate it hinges on
is answered. `scarcity.pjm_reserve_coopt_inputs` assembles the co-opt inputs (the
PJM analogue of `ercot_reserve_coopt_inputs`): the **measured** PJM_RTO Primary
Reserve requirement (`pr_req_mw`, ~3.4 GW, +190 MW ORDC shoulder) as the
reserve-balance RHS, the **published** vertical two-step ORDC (`Primary/RTO`,
`$850/$300/+190 MW`) as ascending shortfall steps (`[300, 850]`, widths
`[190, REQ_max]`), and the generic `RESERVE_FUEL_TYPES` thermal eligibility
mask. `runner.py` gains the `iso == "PJM"` co-opt branch (thermal-only reserve;
no storage-as-reserve), and `_system_frame` now persists the reserve clearing
price (`reserve_price`, the balance-row dual) so the residual analysis can split
the energy and reserve components. **Nothing is fitted to the LMP residual**
(claude.md #11): the requirement is measured, the curve is the cited market
design. Tests in `tests/test_reserve_coopt.py`; the mechanism is unit-validated
(slack headroom → reserve price $0; tight headroom → $300 lifting the energy LMP
+$300).

**PROBE #2 (the bind gate), empirical on the `pjm_38` keeper, 2024**
(`scripts/probes/_pjm_coopt_bindgate.py`, no LP re-solve): the as-built
zone-aggregate `dispatch._build_reserve_rows` caps a zone's reserve at its
**total** eligible thermal headroom (idle units included) and the balance row is
system-wide (reserve fungible across zones), so the requirement clears at **$0 in
all 8,760 hours** — system-wide eligible headroom is **min 7.34 GW** (p50
50.5 GW), a minimum **1.9×** the 3.6 GW requirement, never below it. The
published vertical step never fires; the energy LMP gets no lift. This confirms
finding #2: the perfect-foresight LP holds far more idle eligible headroom than
PJM's reserve product, so co-optimization *as-built* cannot price the residual.

**Finding #3 (the ramp cap), analytic on the same dispatch:** restricting reserve
to **plant-level online** headroom thins it to a 21.6 GW median (binds in 16 h);
adding a **10-minute ramp cap** (per-fuel engineering ramp fractions: CT/oil
~100%, CC 60%, ST 30%, coal 15%, nuclear 0% — not fitted) thins it to a **median
10.3 GW (still 2.9× the requirement)**, crossing below the requirement in only
**49 h/yr**. Those 49 h bind at the **penalty** step ($300–850), the shortage
regime that *overshoots* the $75–200 band; the broad afternoon band still sits on
free deliverable headroom. So the ramp cap makes the scarcity *tail* fire but does
**not** populate the $75–200 **opportunity-cost** middle — that needs the per-gen
`R[g] ≤ ramp10[g]` co-opt LP *and* a tighter commitment posture (Phase 1: the
model keeps ~10 GW of fast deliverable headroom synchronized and idle). The
per-gen build is memory-infeasible on the 15 GB box (the zone-aggregate co-opt
already OOMs at ~16 GB; per-gen reserve vars at PJM plant scale are far heavier)
and is blocked on ramp-rate data absent from `FleetArrays`. Per claude.md #11
this is reported, not papered over: the breakpoint is not lowered and the penalty
is not inflated. The diagnosis points at **commitment posture** (and the coupled
cheap-marginal-coal suppression) as the prerequisite lever, exactly the campaign
sequence.

## 2026-06-19 (combined-cycle steam-turbine outage coupling — all ISOs)

The CAMPD unit-outage overlay only ever flagged combustion turbines: a combined
cycle's steam turbine (EIA-860 `prime_mover = CA`) burns no fuel, has no CEMS
series, and so was never detected or derated. When a feeding CT went down for an
extended period the model kept the plant's steam turbine fully online even
though it physically loses that CT's share of HRSG steam — an under-derate of
the orphaned steam. At Wolf Hollow II (59812, 2×CT 360 MW + 1×CA steam 511 MW)
the 90-day 2025 CGT5 outage derated the bin by only `360/1231 = 29%`, leaving
the plant ~71% available when reality was ~50%. Across the six consumed
unit-outage CSVs, 43 of 46 ERCOT CC plants (and the CC fleets of every other
ISO) carried this orphaned steam — ~12.7 GW of CC steam absent from every
outage derate.

- **Fix** (`scripts/derive_campd_unit_outages.py::build_capacity_index`). A
  combined-cycle combustion turbine's CSV `unit_capacity_mw` is now its full
  block share — `CT_nameplate × (1 + Σ CA_nameplate / Σ CT_nameplate)` over the
  plant's `CT`/`CA` prime movers — so the plant's CT shares sum back to the full
  block (CT + steam, the same basis as the model-bin denominator) and one CT out
  derates its turbine *plus* the steam it fed. Wolf Hollow II's CTs go 360 →
  615.6 MW each (sum 1231.2 = the bin), so the CGT5 outage now derates 50%.
- **Detection is unchanged.** A new `(detect_mw, derate_mw, cc_augmented)`
  capacity entry separates the CF denominator the outage *detector* thresholds
  on (the CT's own nameplate — untouched) from the steam-augmented *derate*
  share written to the CSV. Verified window-neutral: every committed outage
  window is preserved across all six ISOs (0 lost), non-CC capacities are
  byte-identical, and the only added windows (PJM +64, CAISO +26) are
  `observed_peak` rows from newly-landed CAMPD extracts, not the steam fix.
- **Edge cases.** Single-shaft CC (`CS`) carries no separate `CA` and keeps its
  steam-inclusive nameplate (no double count). The per-plant `CT`/`CA` sums keep
  the allocation inside the CC, so the W A Parish (3470, coal/gas `ST`) and
  Barney M Davis (4939, gas-steam `ST` unit 1 vs CC) splits never cross — the
  steam stays on the CC CTs. CT/ST peakers remain excluded. The concurrent-CT
  clip in `unit_outage_derate_factors` still holds: two CTs out sum to exactly
  full derate (0.5 + 0.5 → clip 1.0), not an overshoot. The cosmetic
  `plant_capacity_mw` column now equals the bin (Wolf Hollow II 720 → 1231.2).
- **Regenerated all six consumed unit-outage CSVs** with
  `scripts/derive_campd_unit_outages.py --iso <ISO>`. CC-augmented rows
  (`eia_*_cc` source): ERCOT 1272, PJM 1102, NYISO 497, NEISO 541, CAISO 719,
  MISO 764. Window-set deltas are input-data drift only (`observed_peak` rows
  from newly-landed extracts): PJM 4594→4658, CAISO 1961→1987, MISO 3767→3806;
  ERCOT/NYISO/NEISO window counts unchanged. Also repointed the script's stale
  `inputs/raw-data/...` path defaults
  (UNIT_LEVEL_DIR, `--bins`, `--eia860`, `--out`, the F923 parquet) to their
  post-W1 `data/raw/...` homes via `market_sim.config.paths`, so it runs again.
- **GATED** (derate → dispatch → volumes). ERCOT 3-yr co-opt keeper recipe
  re-run (`ercot_dam_ccsteam_3yr`): the [7c] operating-shape regression gate
  PASSES every class/year (CC_REGULAR/CC_CHP cf_emd held or improved — the
  steam-coupled derate does not distort CC shape), and the per-class TWh volume
  gate holds. The deeper CC derate lifts scarcity in the outage windows (2023
  >$200 tail 151→171, toward the 181 actual); 2024/2025 LMP is being re-gated
  against a same-recipe baseline A/B before adoption.

## 2026-06-19 (PJM — coal-rank fallback for mid-backcast retirees; coal-over de-masked)

Three retiring PJM coal plants — **W H Sammis** (OH), **Homer City** (PA) and
**AES Warrior Run** (MD), all bituminous — were left in the model's generic
unranked `COAL` bucket because `coal_supply_class` consulted only the curated
and EIA-923 fuel-receipt maps, and a plant that retired mid-backcast has no
recent burned-fuel receipts to derive a rank from. The EIA-923 calibration
benchmark already resolves them to `COAL_BIT` via the plant's fuel code, so the
model showed a spurious generic "Coal" row the actual never has, and priced
them at generic full fuel cost instead of PJM's bituminous passthrough.

- **Fix** (`data.fleet.coal_supply_class`): a tertiary fallback to the retiree's
  EIA-860 `energy_source` rank (`_eia860_retiree_coal_supply`), mirroring the
  benchmark's fuel-code fallback so model and benchmark bucket these plants
  identically. Scoped to the retired-within-window vintage only — the exact
  structural gap; operable coal is untouched (an unresolved operable plant means
  its ISO's receipt map was never derived, a separate piece of work). PJM coal
  now fully resolves (32 bituminous, 0 unranked); 212 fleet/coal tests pass.
- **Consequence — the "+7%" coal-over was a labeling artifact.** The scorecard's
  `coal-tot` gate sums only `BIT+PRB+WC`, so it had been comparing **model coal
  *minus* the 3 retirees** (the ~13 TWh hidden in the excluded generic bucket)
  against **actual coal that *includes* them**. Apples-to-apples the 2023 PJM
  coal-over is **+18.7% (+21 TWh)**, not +7%. Total model coal barely moved
  (136.7→134.8 TWh; the bituminous repricing was ~dispatch-neutral) — only the
  attribution became honest. LMP/interchange unchanged.
- **Root cause now visible**: ~half the coal-over is the 3 retirees
  over-dispatching (Homer City 9.1 vs 1.0 TWh actual). Two parts — a COD-ramp
  partial-retirement bug (`load_cod_map` collapses heterogeneous unit-retirement
  dates to the latest, keeping full capacity until then, so Homer City runs 2
  units that retired Jul/Aug through year-end; a cross-ISO fix deferred) and the
  dominant economic over-dispatch of cheap uneconomic retirees the energy-only
  LP runs as baseload (needs CAMPD unit-level availability, not a fit).
## 2026-06-19 (scripts/ — one-off investigation probes corralled into scripts/probes/)

Pure move + import/path fix, no behaviour change. The ~20 manual probe scripts
(`scripts/_*.py` left after the shared helpers moved to `scripts/lib/`) now live
in `scripts/probes/` — the `_caiso_*` set, the `_pjm_*` run/probe/score chain,
`_dam_offer_compare`, `_neiso_probe_compare`, `_reldeploy_compare`,
`_backcast_shell`, etc. They are the reproducible record behind committed
findings, so they are moved, never deleted.

- **Imports kept working.** `scripts/probes/` is a namespace package (no
  `__init__.py`, matching `scripts/`). Each moved probe's `__file__`-relative
  path math was bumped one level deeper (`parent`/`parents[1]` → `parents[1]`/
  `parents[2]`) so its `sys.path` shim still points at `scripts/` (for bare
  `from run_calibration_full import …`) or the repo root (for
  `from scripts.… import …`), and its output dirs still resolve. `render_backcast`
  and `build_manifest` now import the shell from `scripts.probes._backcast_shell`.
- **References refreshed.** Current-usage pointers in `docs/`, `results/`,
  `.claude/skills/`, `.gitignore`, and a `scenarios.py` comment now point at
  `scripts/probes/…`. Historical records (prior `CHANGELOG` entries, per-run
  `run_config.json` provenance, the `code-docs-cleanup-plan` session prompts)
  stay as-is.

## 2026-06-19 (NEISO — ISO-NE RCPF scarcity-pricing lever, mirroring NYISO)

Adds an ISO-NE Reserve Constraint Penalty Factor (RCPF) scarcity overlay, the
NEISO analogue of the NYISO RCPF lever. Post-solve only (never an LP input):
volumes, dispatch and emissions are untouched, and the adder is $0 whenever
reserves clear the requirement. ISO-NE recovers fixed cost through the Forward
Capacity Market, so the lever owns the price **tail** only — it is for
forward/scarcity scenarios, not a backcast adjustment. Additive and gated; no
existing keeper moves.

- **Sourced curve, nothing fitted.** `constants.NEISO_RCPF_PRODUCTS`: three
  nested products (TMSR ⊂ total-10-min ⊂ total-30-min). Requirements from
  ISO-NE OP-8 (TMSR = ½·first contingency; total-10-min = first contingency;
  total-30-min = first + ½·second) with a documented 1,200 MW contingency
  estimate (`TODO(NE-contingency)`); penalties are the sourced tariff RCPFs
  (TMSR $50, TMNSR $1,500, TMOR $1,000/MWh). Linear demand-curve stand-in
  between sourced anchors, same convention as the NYISO products.
- **Wiring.** `results.rcpf.resolve_rcpf_products` is now ISO-aware (NEISO →
  ISO-NE table, every other ISO unchanged); `ScenarioConfig.neiso_rcpf_enabled`
  / `neiso_rcpf_products` mirror the NYISO flags; the shared reserve/headroom
  machinery is reused (ISO-NE reserve fuels = gas + oil, the same set).
- **New overlay script** `scripts/derive_neiso_rcpf_overlay.py` (system-wide;
  local reserve zones NEMA/Boston/CT/SWCT deferred to a locational follow-up,
  as for NYISO).
- **Verified dormant in the backcast.** On the `neiso_monthly_keeper` bundle
  the adder is **$0 in every hour of 2023–25** (tightest-hour reserve headroom
  ~6,900 MW vs the 1,800 MW requirement), so the keeper's LMP/scoring is
  unchanged; the curve produces the expected stacked tail ($2,550/MWh at zero
  reserves) only when reserves collapse. New tests in `tests/test_rcpf.py`.

## 2026-06-17 (NEISO — backcast fleet made year-correct: within-window plant exits)

The COD ramp can only age out a unit that is **in the fleet snapshot**, but the
single recent operable EIA-860 vintage (2025 Early Release) omits whole plants
that ran during the backcast window and retired before it — so a 2023–2025
backcast was missing them in **every** year and the surviving plants silently
over-dispatched to cover the hole. New keeper `neiso_mystic_cod_3yr` (neiso 17),
superseding neiso 16; ERCOT/PJM/CAISO/NYISO unaffected (additive data + a
backcast-only, mode-gated loader).

- **The blind spot.** Mystic Generating Station (plant `1588`, a ~1.4 GW CC in
  NEISO's Boston/NEMA zone) generated ~1.3 TWh in 2023, ran Jan–May 2024, and
  retired June 2024 — but the 2025ER carries no Mystic CC at all (the early
  release omits pre-survey retirees). It was absent from the modeled fleet in
  every year; the surviving CCs over-dispatched ~1.3 TWh to match the EIA-923
  CC_REGULAR total, a hidden composition error (wrong plants, wrong zone).
- **Fix (general, mirror of forecast's planned additions).**
  `scripts/process_eia860.py --retired-window-from <final.zip ...>` reads the
  "Retired and Canceled" sheet of each final EIA-860 vintage (2023, 2024, which
  carry Mystic with its real June-2024 retirement), keeps whole-plant exits that
  retired in/after the window start and are absent from the operable snapshot,
  and writes `eia860_generator_retired_within_window.parquet`. `load_cod_map()`
  unions it (the ramp gains each exit's retirement month) and a backcast-only
  `fleet.load_retired_within_window(iso)` injects the matching generators
  (gated on `mode == "backcast"`, so a forecast never carries a retired unit).
- **Capped by observed CEMS outages.** An injected exit is a real generator at
  its full economic merit, but several ran far below merit for reliability/RMR
  reasons. The historic unit-outage overlay now covers the retirees too
  (`derive_campd_unit_outages.py` and `outages._iso_plant_capacity` both union
  the retiree fleet), so Mystic's `(1588, CC_REGULAR)` derate resolves to its
  ~0.11 observed availability ceiling and the LP cannot run it as baseload.
- **Result.** Mystic now dispatches **0.72 TWh (2023) / 0.85 TWh (Jan–Jun 2024)
  in Boston, zero 2025**; the modeled CC_REGULAR plant set differs by year
  (**31 / 31 / 29**, was the identical 29 every year). Total CC_REGULAR stays in
  tolerance (−0.2 / −0.2 / +8.7 % vs EIA-923) and the run is gas-neutral
  (54.8 / 58.9 / 60.1 TWh) and price-level-neutral (34.5 / 39.8 / 70.5 vs DA
  36.8 / 41.5 / 67.9) vs neiso 16; 2025 is byte-identical (Mystic absent).
  Mystic's 0.72 vs 1.31 TWh actual is the reliability/RMR dispatch the economic
  LP cannot recover (same class as the documented CT/ST/oil wedge); the 2025
  +8.7 % CC over-forecast is the separate merit-order issue, untouched here.
  Other within-window NEISO exits handled the same way (Tanner Street CC, South
  Meadow / North Main oil, Androscoggin Mill gas-ST, …). Tests: +12 across
  `test_cod_ramp` / `test_fleet` / `test_outages`.

## 2026-06-17 (ERCOT — OTHER_FOSSIL scoring bucket for genuinely-mixed gas-thermal plants)

The EIA-923 dominant-class assignment collapses each plant to one model class
(`eia923_dominant_class_by_plant`), but a handful of plants are a near-50/50 mix
of steam and combustion-turbine units (Dansby, Powerlane, V H Braunig), so the
"dominant" class is a coin-flip that can flip year-to-year and pollute the clean
CC/CT/ST scores. `market_sim.data.fleet.apply_other_fossil_scoring` now re-buckets
these into an **OTHER_FOSSIL** scoring class:

- A plant is flagged `mixed_fossil_plants` when no single gas-thermal class holds
  >= 60% of its EIA-923 net generation and its two largest classes are both
  gas-thermal. The transform relabels those plants' gas-thermal rows to
  OTHER_FOSSIL on **both** the model dispatch frame and the EIA-923 actuals frame
  (keyed by EIA plant code), so they score in the same bucket on both sides.
- **Scoring/benchmark only — dispatch is unchanged.** The bin keeps its
  dominant-class offer curve; no re-solve. Applied in the text report ([3b]/[4])
  and the dashboard (`classFull` / `gmModel`), so it needs no recalibration —
  ERCOT keepers were regenerated from their existing bundles.
- Effect (ERCOT 2023): pulls ~0.25 TWh of ambiguous generation out of CC/CT/ST
  into OTHER_FOSSIL, cleaning the gas-class scores (e.g. ST_GAS +4.8 → +3.2).

## 2026-06-17 (Measured-data rule + HSL real-data reconciliation + formulaic ERCOT ORDC reserves)

New Non-Negotiable Rule (claude.md): measured data is allowed only as a
reproducible physical/market input that has a forward analogue, never as a
measured *outcome* fed back to force the backcast to match. Audit of the current
keeper (run 124) in `docs/backcast-measured-data-audit-2026-06.md`: compliant on
the load-bearing items (CEMS deployment floors and the fitted ORDC offset off).
Two follow-on fixes landed from the audit:

- **HSL: output-target rescale → real-data coverage reconciliation.** The 2023
  `_HSL_RESCALE_TWH` set renewable potential *above* delivered so the LP's
  economic re-curtailment landed delivered output on the actuals (tuning an input
  to the model's output). Replaced: `renewables.hsl_potential_mw` consumes each
  HSL parquet as-is, with one real-data reconciliation — a partial-footprint
  source whose delivered (GEN) undercounts the EIA-930 system total is scaled UP
  to that level *preserving its measured curtailment ratio*; no-op for
  full-footprint published data. `build_ercot_hsl.py` now prefers the published
  NP4-732/737 HSL for any year (np6/), UMass only as the 2023 fallback.

- **ERCOT ORDC: fitted offset → on-line/off-line reserve split.** The fitted
  `ordc_reliability_deployment_mw` (~2,500 MW tuned to the 2023 LMP residual) is
  deprecated and out of the default reserve path. `results.scarcity.reserve_headroom`
  now returns an (online, offline) split — only responsive capacity backs the
  ORDC curve; a cold slow-start unit the LP left idle is not reserve — and
  `ordc_adder` evaluates the published RTOLCAP/RTOFFCAP two-tier LOLP honestly.
  AS-plan netting was tested and **rejected** (RTOLCAP already counts online
  AS-held capacity as reserve → double-counts, overshoots ~6×). The split
  reproduces 2023 scarcity *incidence* (online reserve < 6,500 MW floor in 178 h
  ≈ 181 actual >$200 h) and improves 2023 monthly LMP MAE 32.3 → 27.7 with no
  fitted constant; 2024/25 neutral. The residual magnitude gap is left for AS/
  reserve co-optimization (the bang-bang LP doesn't part-load to carry reserve),
  not chased with an offset (Rule #1). See `docs/ordc-overlay.md`.
## 2026-06-17 (ALL ISOs — commercial-operation-date (COD) vintage ramp for the whole fleet, default-on for backcasts)

The backcast fleet snapshot (the curated ERCOT CAMPD bins / the EIA-860 generator
parquet) is a recent vintage that includes units commissioned **after** the
solved year. Renewables and storage already respect their commercial-operation
dates, but thermal/nuclear/oil did not — so a 2023 backcast dispatched GWs of
capacity that were not yet built, inflating reserve headroom and suppressing the
scarcity prices the LP can set. `market_sim.data.cod_ramp` now extends the COD
rule to **every generator** as a single month-precise mechanism
(`cod_ramp_enabled`, default-on, backcast mode; forecast-applicable):

- One monthly online mask inside `generators_to_fleet_arrays`: `online_year >
  run_year` → offline; `online_year == run_year` → online from `online_month` on
  (a Sept-COD unit is absent in the August scarcity hours, which a flat annual
  prorate gets wrong); retirements step capacity down at `retirement_month`. The
  mask zeroes the must-run floor (`min_gen`) in offline months too, so the LP
  lower bound cannot force a not-yet-built / retired unit to run.
- **Sourced from EIA-860, not CAMPD** (which has no build dates):
  `load_cod_map()` reduces `eia860_generator_operable.parquet` (month-precise
  `Operating Month/Year`, `Planned Retirement Month/Year`) to a per-plant
  capacity-weighted `{plant_code: (online_year, online_month, ret_year,
  ret_month)}` map. This is what gives the ERCOT CAMPD bins — which carry no
  build date of their own — their COD; raw EIA-860 units fall back to their own
  `online_year`/`online_month`. Registry-only plants back-fill at a mid-year
  default month.
- **Reconciliation:** this collapses two overlapping COD implementations that had
  coexisted on `main` — the year-granular `cod_ramp_enabled` (`ramp_bins` /
  `ramp_fleet`, registry-keyed, flat half-year prorate) and the month-granular
  `thermal_vintage_ramp` (which reached only EIA-860-month-carrying gens, missing
  the ERCOT bins) — into one path. `ramp_bins`/`ramp_fleet`/`online_fraction`/
  `load_cod_year_map` and the `thermal_vintage_ramp` flag are deleted; see
  [`docs/cod-vintage-ramp.md`](docs/cod-vintage-ramp.md).
- **Measured ERCOT impact:** the 2023 bins shed ~870 MW cap-month-equivalent
  (496 MW of plants built after 2023 dropped outright — incl. Remy Jade 484 MW,
  COD 2024-06 — plus nine 2023-COD plants masked from their real online month,
  e.g. Brotman 484 MW from May); 2024 ~250 MW; 2025 unchanged. **Gated:** the
  month mask moves the COD-year units versus the old flat prorate, so it needs a
  calibration re-run before a keeper is re-cut (run125 → run126); set
  `cod_ramp_enabled=False` to reproduce a pre-ramp run.

## 2026-06-17 (ERCOT — 60-Day DAM offer parser + thermal offer-curve grounding)

`scripts/parse_ercot_dam_offers.py` reshapes the wide 60-Day DAM Disclosure Gen
Resource Data into a tidy per-(resource, hour, curve-point) offer table (19.5 M
rows, 2022-11 → 2025-11) with the three-part startup/min-gen fields, and
`scripts/analyze_dam_offer_multipliers.py` inverts the offers into the model's
heat-rate-multiplier space to overlay the measured distribution on the run124
bands (`docs/ercot-dam-offer-grounding-2026-06.md`). Verdict: CC bands sit inside
the observed distribution; the CT econ ramp is flat at fuel cost (econ_high p50
~1.11 every year), so the model's rising 1.27→2.18 ramp is an offer markup, not
the observed energy-curve shape — a defensible re-derivation target. Analysis
only; no band changed.

## 2026-06-17 (CAISO — RA must-offer midday gas-commitment floor: model goes long, spring-midday LMP floor collapses to ~$0)

New default-off mechanism that reproduces CAISO's collapsed spring-midday LMP by
making the model **long** midday. CAISO's Resource-Adequacy must-offer obligation
keeps gas online at min-load through the solar glut (it can't economically cycle
off for the evening ramp), so it over-generates midday and the ISO
exports/curtails the surplus — the marginal is the export, priced near $0. The
economic dispatch instead decommits gas to ~1.5 GW midday and imports the
balance, staying balanced, so its midday marginal is always a ≥$28 import/gas
(the over-priced floor; `AUDIT-caiso-structural.md` phase 2).

- **Mechanism (measured, no magic number).** A hard min-generation floor on the
  gas fleet (`gas_cc`/`gas_ct`/`gas_st`) over the midday solar-glut window
  (local hours 9–16), sized to `--caiso-gas-floor-frac` × the measured EIA-930
  `NG: NG` (month × hour-of-day median) profile, through the hour-varying
  `FleetArrays.min_gen` lower bound — the same mechanism the CHP steam floor and
  the CT/reliability-deployment overlays use. The hourly fleet target is
  distributed cheapest-first (by heat rate), each unit capped at its available
  capacity, and survives the P2 commitment screen (`preserve_min_gen`), so the
  screen can't decommit RA gas it held on for reliability.
  - `eia_loader.measured_gas_floor_profile` — the (month × hod) percentile of
    measured EIA-930 `NG: NG` mapped onto the run horizon (mirrors
    `measured_interchange_envelope`).
  - `transmission.inject_caiso_gas_commitment_floor` — injected in
    `run_calibration` after `generators_to_fleet_arrays`, mirroring
    `inject_offshore_wind_availability` / `inject_interchange_shape`.
  - Flags: `--caiso-gas-commitment-floor` (`config.caiso_gas_commitment_floor`,
    default off) + `--caiso-gas-floor-frac` (default 1.0).
- **Frac is a measured fraction, not a fitted constant.** EIA-930's `NG: NG` for
  CISO silently absorbs ~21 % geo+bio (EIA-930 reports neither), so
  **frac ≈ 0.79 = EIA-923 gas / EIA-930 `NG: NG`** strips that and targets the
  true must-offer gas. The keeper uses **frac 0.80**.
- **Result (2024, clean floor-only A/B vs `caiso_tune0_base`).** The model goes
  long midday — spring-midday gas 1457→4835 MW (frac 0.70) … 6874 MW (frac 1.0,
  ≈ the measured 6834), net interchange flips from +2308 MW (import) toward
  export, export hours rise from 0 %. The spring-midday LMP **floor collapses
  from a hard $28 to ~$0**: at frac 0.80, LMP min 28→0, spring p5 36→8, spring
  min 28→0, with gas modestly up (68.0→71.3 TWh, +5 %; validated vs EIA-923 =
  67.7, **not** EIA-930). 3-year keeper (`frac 0.80`, +2025 hydro repin): LMP
  min 0.0 every year (was $8/$28/$42); gas 67.2/71.3/70.6 (2023/24/25). The
  spring *mean* still sits above actual — pushing the belly **below** $0 is the
  negative-renewable-offer tail (Session B); this collapses the floor, not the
  negative tail. Watch item respected: the surplus **exports/curtails**, it does
  not pad the mix.
- **Default off ⇒ byte-identical.** Every existing run/ISO is unchanged when the
  flag is off (CAISO-only; no-op for non-CAISO, frac≤0, no gas units, or no
  measured profile). Tests: `TestCaisoGasCommitmentFloor` (8),
  `TestGasFloorProfile` (4). Full write-up:
  `results/calibration/RESULTS-caiso-ra-mustoffer-floor.md`.

## 2026-06-17 (NEISO — CT_PEAKER reserve recovered: ct_deployment overlay survives the P2 commitment screen)

The targeted CT AS/reserve-deployment overlay now survives the P2 unit-commitment
pass, recovering NEISO's measured sub-marginal CT_PEAKER energy without injecting
net gas. New keeper `neiso_ctdeploy_3yr` (neiso 16), superseding neiso 14.

- **Bug fix — a reserve floor was being decommitted by the economic screen.**
  `commitment.apply_commitment_with_coal_pin` rebuilt the P2 `FleetArrays`
  **without `min_gen`**, so every hard floor (the `ct_deployment` reserve floor
  and the CHP steam-following floor) was dropped in P2 and the commitment screen
  decommitted the floored peakers as uneconomic. A reserve / AS-deployment floor
  is energy that ran for reliability, not economics, so the *economic* screen
  must not shut it off.
- **Fix (gated, regression-proof).** `apply_commitment_with_coal_pin` gains
  `preserve_min_gen` (default False = byte-identical): when True it carries
  `min_gen` into P2 and raises each floored generator-hour's availability to
  cover the floor (the LP binds `min_gen ≤ P ≤ pmax·availability`).
  `run_calibration._commitment_pass` sets it True **only when a deployment
  overlay is active** (`ct_deployment_overlay` / `reliability_deployment_overlay`,
  both default-off), so the forecast runner and every non-overlay keeper
  (ERCOT/PJM/CAISO/NYISO + NEISO neiso 14) take the exact prior path — verified
  byte-identical (NEISO base 2024, overlay off, max |ΔTWh| = 0.0). Tests 361 pass.
- **Result.** With `--ct-deployment`, `scripts/derive_ct_deployment.py --iso
  NEISO` measures the wedge at 0.08/0.04/0.05 TWh and CT_PEAKER recovers
  0.014/0.014/0.038 → 0.084/0.052/0.079 TWh (2023/24/25) while the gas total
  (54.78/58.89/60.14, −1.2/−1.3/+0.1% vs EIA-930) and price level
  (34.9/40.2/70.5 vs actual DA 36.8/41.5/67.9) stay at sign-off — the CT energy
  displaces CC within gas, not coal/imports (the blanket-floor failure mode).
  See `docs/calibration-log.md` and `docs/multi-iso/neiso-data-audit.md` §2e.

## 2026-06-17 (NEISO — Merrimack reclassified COAL_BIT; CC_REGULAR offer-curve Jacobian re-derived)

The lone NEISO coal unit is now classified by its **measured** rank, and the
CC_REGULAR offer-curve sensitivity panel was re-seeded on the corrected
(AGT-overlay-wired) structure because the prior Jacobian was stale.

- **Merrimack (ORIS 2364) → COAL_BIT.** `scripts/derive_coal_supply.py --iso
  NEISO` reads the plant's EIA-923 Schedule-5 fuel receipts (54,050 tons
  2023-2025, 100 % bituminous) and writes `inputs/processed/coal_supply_NEISO.csv`,
  so `fleet.coal_supply_class(2364)` returns `bituminous` and the dispatch class,
  offer curve, and delivered-cost path all resolve to **COAL_BIT** instead of the
  generic unclassified `COAL` fallback. EIA-860 confirms the window: unit 1
  (108 MW, `OP`, retire 2027) runs all three backcast years, unit 2 (330 MW, `OS`)
  is out of service — so coal is the EIA-930 ISNE 0.18/0.24/0.28 TWh winter-peaking
  run, not zero. Dispatch is unchanged (the COAL_BIT and generic COAL curves are
  identical and the NEISO delivered cost is already the bituminous-by-rail blend);
  the new 3-year keeper `neiso_cc_coalbit_3yr` (neiso 14) reproduces `neiso_agt_3yr`
  to the TWh with coal now scored against the bituminous benchmark.
- **CC_REGULAR Jacobian re-derived (`results/calibration/neiso_probe_v2_*`).**
  Fresh ±0.05 single-knob probes on the wired keeper show the live CC_REGULAR
  bands (econ_high > econ_low > committed) redistribute energy **only within the
  CC family (CC_REGULAR ↔ CC_CHP) and to imports — never to CT_PEAKER, ST_GAS, or
  oil** (ST_GAS is dead to its own knob too). CT_PEAKER's cheapest tranche
  (1.55 × 10.4 ≈ 16.1 eff-HR) sits above CC_REGULAR's whole curve including the
  duct-fire fold (2.25 × 7.0 ≈ 15.8), so CC tuning cannot reach the peakers. The
  CC_REGULAR offer curve is **held at the keeper values** (no Jacobian-supported
  move improves the CT/ST/oil mix); the CT/ST shortfall is the not-offer-recoverable
  reserve/AS-deployment limit (cross-ISO finding), recoverable only via the
  off-by-default `ct_deployment` overlay. ERCOT/PJM/CAISO byte-identical (the only
  change is the additive NEISO coal CSV; no offer-curve code edit). See
  `docs/calibration-log.md` and `docs/multi-iso/neiso-data-audit.md` §2e.

## 2026-06-17 (NYISO locational RCPF reserve overlay — the downstate scarcity tail)

The NYISO RCPF scarcity overlay gains its **locational** tier. With measured
zonal load (upload U3) active, the per-zone diagnostic confirms the 2023–2025
scarcity tail is downstate: in the actual >$300/MWh hours the **NYC** zone's
reserve headroom collapses to ~1,000 MW — the NYC 30-minute reserve
requirement — while NYCA-wide headroom is still ~5 GW, so the system-wide
overlay (correctly) stays $0. The shortage lives inside the import-constrained
NYC/SENY pocket, invisible to the NYCA-aggregate energy LP.

- **`constants.NYISO_RCPF_LOCATIONAL`** — NYISO's nested locational reserve
  regions (NYCA ⊃ East ⊃ SENY ⊃ NYC) as `region -> {zones, products}`, mapped
  onto the five-zone model topology. East: 1,200 MW 30-min over zones F–K,
  $500/MWh max; NYC (zone J): 1,000 MW 30-min + 500 MW 10-min, $500/MWh max
  (FERC ER21-502 / NYISO MST Rate Schedule 4). SENY (zones G–K): $500/MWh max
  sourced, MW requirement a **placeholder** 1,100 MW (midpoint of the sourced
  nested anchors East 1,200 ⊇ SENY ⊇ NYC 1,000; `TODO(SENY-MW)` to source the
  RS4 value). Overridable via `ScenarioConfig.nyiso_rcpf_locational`.
- **`scripts/process_nyiso_as.py`** — the committed measured reference
  `actual_as_reserve_NYISO.parquet` now carries a `reserve_<model_zone>` column
  for all five model zones (built from the NYISO OASIS RT AS archive, 2023–25,
  all 11 settlement zones), so the overlay validates every zone against
  measured data from the committed artifact, not the raw CSV.
- **`results.rcpf.locational_zone_adders`** — prices each region's reserve
  demand curve on the sum of its member zones' headroom and stacks it onto
  every zone the region contains (on top of the system-wide NYCA tier),
  reproducing the measured upstate→NYC reserve-price cascade.
- **`scripts/derive_nyiso_rcpf_overlay.py --locational`** — builds per-model-
  zone reserve headroom (`availability_rcpf_zonal.parquet`), writes the per-zone
  `scarcity_locational.parquet`, and validates each zone's modeled adder against
  the measured per-zone RT reserve price (`NYISO_as_rt_<year>.csv`). No LP
  re-solve; the adder is post-solve and byte-identical to the energy-only LP.

Result (no fitting to LMP residuals): the NYC locational adder fires in the
right hours and its mean tracks the measured N.Y.C. reserve adder (2023: model
$5.15 vs measured $6.37; 2024: $4.36 vs $7.64), producing a downstate price
tail to ~$1,100/MWh. It under-fires in *incidence* (2023: 219 h vs 3,020 h;
worse in the tight 2025 summer) because the LP's downstate headroom is still
too loose in the body — the perfect-foresight import over-service that backs
down NYC gas, which the overlay now quantifies. Import discipline (pricing each
tranche from its neighbor's marginal cost) is the next structural lever. Tests:
`tests/test_rcpf.py` (locational cascade, region-headroom summing, override,
empty-region no-op).

## 2026-06-16 (data — NYISO ancillary-service reserve prices, measured RCPF validation)

NYISO OASIS ancillary-service price downloads (`inputs/raw-data/NYISO-AS/`,
the zip-of-zips `NYISO-AS-Data.zip`: monthly real-time `rtasp` 5-minute and
day-ahead `damasp` hourly CSVs, 2021–2026) are processed into the measured
reserve clearing prices — the empirical realization of the NYISO Reserve
Constraint Penalty Factors, which the RCPF overlay can now validate against
instead of standing on published curve values alone.

- **`scripts/process_nyiso_as.py`** — folds the `rtasp` / `damasp` zips into
  per-year per-zone hourly CSVs (`NYISO_as_{rt,da}_{year}.csv`: `spin_10`,
  `nonsync_10`, `op_30`, `reg_cap` in $/MWh) and a compact calibration
  reference `inputs/calibration/actual_as_reserve_NYISO.parquet` (per
  (year, hour): `nyca_reserve_adder` = the WEST/upstate stacked RT reserve
  price the system-wide overlay targets; `nyc_reserve_adder` = the full
  downstate cascade the locational products target). Duplicate `(1)`
  downloads are de-duplicated.
- **`scripts/derive_nyiso_rcpf_overlay.py`** now reports the model adder
  against this measured reserve adder.

**What the measured data shows (2023 RT):** reserve scarcity is real and
**locational** — the per-zone 30-min reserve price cascades from upstate
(WEST max $662, nonzero 196 h) through the East/SENY zones up to **N.Y.C.**
(max $727, nonzero 515 h); the stacked reserve price reaches **$2,448** in
NYC (how LMP gets to $1,147+). This **corroborates the published
`NYISO_RCPF_PRODUCTS` curve values** (upstate 30-min max $662 sits right
under the $750 NYCA cap) — they are measured-consistent, not magic numbers.
The measured NYCA reserve adder is >$0 in 629 h (mean $2.20) and the
downstate NYC adder in 3,020 h (mean $6.37), versus the overlay's $0.00 —
re-confirming the tail gap is a locational + LP-headroom-bias problem, to be
closed by the congestion fix + locational RCPF products, not by forcing the
system-wide curve.

## 2026-06-16 (NEISO — AGT hub-basis overlay wired into calibration)

Makes the measured Algonquin Citygate (AGT) monthly gas basis the correct price
driver it was always documented to be — a bug fix using data already in the
repo, no new parameters. (A fitted daily-basis refinement is included only as an
off-by-default diagnostic; see below.) See `docs/multi-iso/neiso-data-audit.md`
§2c–2d.

- **Bug fix — the AGT hub-basis overlay was never applied in the calibration
  dispatch.** `run_calibration.run_year` resolves fuel prices with
  `apply_monthly=False` and re-applied the plant-monthly and dual-fuel passes
  but **not** `apply_hub_basis_overlay`, so every NEISO keeper priced gas at the
  two-reporter EIA-923 ISO-month series instead of the measured AGT hub. That
  series was over-priced in shoulder months and under-priced in winter, so the
  modeled price level was wrong in both directions (load-weighted hub vs ISO-NE
  .H.INTERNAL_HUB DA: 2023 $53.6→$34.5 vs $36.8; 2024 $55.7→$40.0 vs $41.5;
  2025 $54.3→$68.0 vs $67.9). `run_year` now applies the overlay between the
  plant-monthly and dual-fuel passes. The overlay is idempotent and no-ops for
  non-NEISO ISOs, so ERCOT/PJM/CAISO/NYISO stay byte-identical.
- **Keeper** `results/calibration/neiso_agt_3yr` (one 2023–2025 bundle, dashboard
  neiso 13), on the measured monthly overlay with hydro 930-pinned uniformly —
  **no fitted parameter**. Gas within −1.3% of EIA-930 all years; hydro
  8.70/7.33/5.11 vs 930 8.77/7.39/5.12. Supersedes the `neiso_p12_*` /
  `neiso_hydro930_2025` keepers. The winter >$200 tail and near-zero oil are the
  honest monthly-granularity limits.
- **`gas_hub_basis_daily` + `dual_fuel_oil_reattribution` are OFF-BY-DEFAULT
  diagnostics** (opt in with `--gas-hub-basis-daily`), NOT in the keeper. The
  daily path redistributes each winter month's measured mean basis across days
  by NEISO demand^`AGT_DAILY_BASIS_CONVEXITY` (=7.0) and re-attributes switched
  dual-fuel MWh to oil; it builds the winter tail / oil burn the monthly plateau
  can't (2025 A/B, identical mean: hours >$200 13→128; oil 0.06→2.12 vs 1.24).
  But the convexity is *fitted to the backcast* (tuned to the oil/>$200 counts
  it predicts), not a measured/forecast-grade input, and the daily AGT spot it
  proxies (U4) is paywalled/unavailable — so a backcast without that series
  should not manufacture the within-month tail from a fitted shape. Kept opt-in
  for diagnosis; when real daily AGT lands the convexity can be derived from
  data and promoted. `fuel.iso_hub_daily_gas_prices` /`dual_fuel_switch_mask`,
  `constants.AGT_DAILY_BASIS_CONVEXITY`. See `neiso-data-audit.md` §2c–2d.

## 2026-06-16 (data — NYISO per-zone hourly actual load, upload U3)

NYISO OASIS ``pal`` actual-load downloads (monthly zips of daily 5-minute
zonal CSVs, 2023–2025, under
``inputs/raw-data/zone-specific-demand/NYISO/raw/``) are folded into the
per-year hourly CSVs the loader expects.

- **`scripts/process_nyiso_zonal_load.py`** — aggregates each zone's
  5-minute integrated load to the hour-beginning mean and writes
  ``NYISO_load_actuals_{year}.csv`` (cols ``Time Stamp, Name, Load``) for the
  eleven NYISO settlement zones. Idempotent; naive Eastern wall-clock
  timestamps (the loader re-localizes and handles DST / Feb 29).
- **Effect:** `eia_loader.nyiso_zonal_load_shares` now gives each model zone
  its own *measured hourly shape* instead of the static Gold-Book share
  fallback. NYC's share rises from the static 0.280 to a measured mean 0.328
  peaking at **0.403**; at the 2023 system peak (30.2 GW) downstate (NYC +
  Long Island) is **51.8%** of load (NYC 10.6 GW, Long Island 5.1 GW against
  a 1,650 MW LI import limit). This is the downstate concentration the
  congestion fix (scorecard gap #1) needs for the interfaces to bind.

## 2026-06-16 (physics — NYISO RCPF scarcity-pricing overlay)

NYISO's analogue of the ERCOT ORDC overlay: a post-solve reserve-demand-curve
price adder that replicates NYISO real-time scarcity formation (Reserve
Constraint Penalty Factors). The LP is untouched — volumes/dispatch/emissions
are byte-identical with the overlay on or off; the adder is written next to
the energy-only LMP.

- **New module `market_sim/results/rcpf.py`** — the NYISO reserve demand
  curve as a set of nested operating-reserve products (10-min spin ⊂ 10-min
  total ⊂ 30-min total). Each product's curve is piecewise-linear between
  published anchors; the products' penalties stack in a deepening shortage,
  the way NYISO RT LMP reaches the low-thousands off a ~$2,000/MWh offer cap.
- **`constants.NYISO_RCPF_PRODUCTS`** — (name, requirement_MW, critical_MW,
  max_$/MWh) for the three NYCA products. Requirements from the NYISO
  Transmission & Dispatch Operations Manual (largest contingency ≈1,310 MW →
  655 / 1,310 / 2,620 MW); NYCA 30-min curve $750/MWh max at the 1,965 MW
  critical level per FERC Docket ER21-502. Nothing fitted to LMP residuals.
- **`ScenarioConfig.nyiso_rcpf_enabled` / `nyiso_rcpf_products`** — master
  flag (default off) + optional curve override; both cited in
  `frontend/data/parameters.json`.
- **`scripts/derive_nyiso_rcpf_overlay.py`** — post-solve overlay mirroring
  `derive_ordc_overlay.py`: reconstructs reserve-fleet headroom from a
  persisted bundle (`run_year(fleet_only=True)`, no LP re-solve), applies the
  RCPF curves, writes `scarcity.parquet` + `availability_rcpf.parquet`, and
  reports tail counts / distribution / LMP MAE vs the actual NYCA RT series.
- **Tests** `tests/test_rcpf.py`; **docs** `docs/nyiso-rcpf-overlay.md`.

**Finding (run on the 2023–2025 keepers):** the system-wide overlay fires
**zero** adder in every hour — the perfect-foresight energy LP floors at
~5.5–6 GW of NYCA-wide reserve headroom even in its tightest hours (2023
actual >$300 hours: model headroom median 5,954 MW, p5 3,981 MW), never
approaching the 2,620 MW 30-min requirement. The 2023–2025 RT tail (max
$1,147 / $997 / $2,074) is therefore **locational** — downstate
import-constrained pockets (zones J/K) and the locational East/SENY/NYC/LI
reserve requirements — not NYCA-wide capacity scarcity. Per the calibration
methodology the overlay is deliberately *not* forced to fire (no inflated
requirement, no headroom offset, which would bury the locational/import
error). It is correct infrastructure that binds once the upstream physics
lands: per-zone hourly load (upload U3) + the interface audit, then
locational RCPF products keyed off zonal headroom — for which the overlay is
already scaffolded.

## 2026-06-16 (data — CAMPD unit-level outage integration across ISOs)

Newly-uploaded EPA CAMPD unit-level extracts
(`inputs/raw-data/campd-unit-level/{STATE}_{YEAR}.parquet`) are now routed into
each ISO's unit-outage overlay. Each state file is incorporated into the
ISO(s) whose EIA-860 fleet actually contains plants there — the per-ISO fleet
filter in `derive_campd_unit_outages.py` keeps every detected window scoped to
that ISO's own plants, so states shared across ISOs (e.g. IL/IN/KY/MI in both
PJM and MISO, TX in both ERCOT and MISO) do not leak between them.

- **`ISO_STATES` (`market_sim/data/campd.py`) widened to each ISO's fleet
  footprint:**
  - **MISO** expanded from the `IL`-only probe to its full footprint
    (`AR, IA, IL, IN, KY, LA, MI, MN, MO, MS, ND, SD, TX, WI`).
  - **NYISO** gains `NJ` — a handful of NYISO-fleet plants (EIA-860 BA
    `NYIS`) sit physically in New Jersey.
  - PJM/NEISO/ERCOT/CAISO maps unchanged; their newly-landed extracts (PJM
    `MD/DE/MI/NJ-2025/TN`, NEISO `2025` for all non-NH states) are picked up
    automatically on regeneration.
  - SPP left empty (not yet a calibration target, no consumed CSV).
- **Regenerated all six consumed unit-outage CSVs** with
  `scripts/derive_campd_unit_outages.py --iso <ISO>`. Window-count deltas:
  ERCOT 3346 (unchanged), CAISO 1933→1961, NYISO 1621→2498, NEISO 1305→1328,
  PJM 4484→4594, MISO 78→3435. Every facility in each CSV is verified present
  in that ISO's fleet, in a qualifying plant group, and not an excluded
  ST_GAS peaker.
- **NEISO 2025 coverage corrected.** The committed NEISO CSV predated the
  2025 extracts already in the repo; regeneration brings 2025 to full coverage
  for every NEISO state except NH (no `NH_2025.parquet`). The NH gap now shows
  specifically as Merrimack (2364, the lone NEISO coal plant) dropping out of
  2025, not as a lower overall facility count — two `test_outages.py` smoke
  assertions that encoded the stale aggregate counts were updated accordingly
  (the Merrimack/coal-gap invariants are unchanged and still pass).

## 2026-06-15 (diagnostics — CC >90% CF investigation + 5% CF-band view)

Investigation of why grid-serving combined cycles (Colorado Bend II, Wolf Hollow
II, Freestone, Guadalupe, …) miss their observed 90–97% CF hours in runs 115b /
118, plus the tooling to see it. **No dispatch/calibration parameters changed** —
the offer-curve fix is proposed in the writeup, not applied.

- **Root cause documented** in `docs/cc-high-cf-investigation.md`: the
  `CC_REGULAR` duct-firing **peak band** (top ~8% of nameplate at ~2.57× base
  HR in run 118) is a *separate flat scarcity tranche above the econ ramp*, so
  there is a price discontinuity from `econ_high` to the peak block. Combined
  with the availability derate on `pmax`, that imposes an effective steady
  output ceiling of ~87–92% of nameplate — Freestone never exceeds 87% of its
  real peak in any year, logging **0** hours ≥90% CF against CAMPD's 1 300–3 000.
  The per-CF-value "precision" chart's spikes are the LP parking at discrete
  tranche edges, an artifact of the discretization.
- **`--cf-band-width`** on `scripts/run_calibration_full.py` makes the `[7b]`
  per-plant operating-level histogram and `plant_cf_bands.parquet` resolution
  configurable (default unchanged at 0.10; pass **0.05** for twenty 5% bands).
  The `[7b]` header now reads the width back from the data, and `cf_emd` already
  infers it from the parquet, so the metric stays comparable across widths.
- **`scripts/plot_cf_histogram.py`** — new standalone, dependency-free
  (inline-SVG) per-plant model-vs-CAMPD CF histogram at a configurable band
  width, the visual companion to `[7b]`.
- **Stale doc fixed:** `docs/binning-methodology.md` claimed the CC/coal peak
  band is *folded into* the econ ramp top (`_CURVE_FOLD_PEAK`). That fold was
  removed; the peak is a separate flat tranche for every group. Corrected to
  match `fleet.py` ("Nothing is folded into the ramp").
- **Peak-band sweep (measured, not promoted).** `scripts/cc_peak_band_probe.py`
  replays the run115b keeper with the CC_REGULAR peak multiplier lowered
  (2.57× → 2.0× / 1.5×) across 2023–2025. The peak band is confirmed as the
  lever for the price-limited plants (CB II, WH II, Guadalupe move toward their
  observed >90% mass), but a **year-uniform cut is not a keeper**: peak 2.0×
  breaches the 0.33% class gate in 2024/2025 (+2.50 / +1.75 TWh) and worsens
  the plants that already over-run the top (CB II 2025). Freestone is
  capacity-limited (model nameplate 1036 < real peak 1119 MW, no peak tranche)
  and CB EC capacity-overstated (654 > 560) — per-plant data axes the offer
  lever can't touch. Full results + recommended three-lever path in the
  investigation doc.
- **Dashboard:** the backcast "Hours at each capacity factor" panel defaults to
  a 5% CF-band histogram (model vs CAMPD) with a toggle back to the per-CF line
  (`scripts/_backcast_shell.py`: `cfBins` / `cfBarChart`).
- **CC capacity reconciliation (`ScenarioConfig.cc_capacity_reconcile`, default
  off, ERCOT backcast).** Raises an understated CC's LP capacity to its
  demonstrated CAMPD peak where that exceeds the curated bin nameplate — the
  cold-weather (winter) over-rating EIA-860 corroborates. Raise-only (never
  lowers a real nameplate); reconciliation table from
  `scripts/derive_cc_capacity_reconcile.py` →
  `inputs/processed/cc_capacity_reconcile_ERCOT.csv` (8 CC_REGULAR plants,
  +377 MW), applied in `load_campd_bins`. Validated: it unblocks Freestone's
  hard zero (0 → 3956 hrs ≥90% CF in 2023; Lamar lands on CAMPD's 2082), and
  surfaces — per `claude.md` rule 11 — that the understated capacity was masking
  the offer curve's over-baseloading (class total +1.56 TWh; pair with the
  offer-ramp shape for a keeper). Tests in `tests/test_fleet.py`.

## 2026-06-15 (backcast dashboard — annual LMP Δ measured against the ORDC overlay)

Fixed the dashboard's model-vs-actual LMP deltas so they compare like-for-like.
The actual ERCOT DA/RT series the dashboard scores against *include* the ORDC
reserve-price adder, which the energy-only dispatch LP structurally cannot
produce — so measuring the energy-only model price against the scarcity-
inclusive actuals was apples-to-oranges and made the model look far off (e.g.
run115b/run118 2023 annual Δ vs DA ≈ −59%, 2024 ≈ −30%).

- **All displayed annual/monthly LMP Δ-vs-actual now use the ORDC-overlaid
  price** (energy LMP + ORDC/reliability-deployment adder) wherever a run
  carries an overlay, falling back to energy-only only for runs/ISOs with none.
  Affects the run scorecard ("LMP Δ vs DA/RT" + the "Avg LMP" KPI, now tinted
  and labeled "model + ORDC" when overlaid), the per-year LMP card "annual Δ"
  badge, the monthly-LMP table Δ columns + annual row, and the LMP-alignment
  diagnostics. With the fix, run115b annual Δ vs DA: 2023 −59% → **−9%**, 2024
  −30% → **−22%**, 2025 −1.8% → **−1.6%**.
- New helpers `avgLMPScar` (demand-weighted annual overlay average, refactored
  out of the monthly table) and `avgLMPDelta` (overlay-when-present, else
  energy-only) in `scripts/_backcast_shell.py`.
- Display-only and non-gating by construction: the energy-only series is still
  shown beside the overlay, it remains the gated calibration metric, and **no
  run payload changed** — the overlay values were already baked into the
  `lmpScar`/`ordc` keys, so this is a pure dashboard-rendering fix (no re-run).
  The residual 2024/2025 under-bias is the documented flat-reliability-
  deployment-offset limitation (anchored to the 2023 stress year), not a
  measurement artifact. See `docs/ordc-overlay.md`.

## 2026-06-15 (multi-ISO — W1b: per-plant CAMPD binning & historic-outage overlay go per-ISO)

Generalized two ERCOT-locked fleet behaviors so they resolve per ISO, with an
ERCOT byte-identical guard (ERCOT stays on its exact prior path).

- **Per-plant CAMPD binning unlocked beyond ERCOT.** `runner.py`'s binning gate
  was hard-coded to `iso == "ERCOT"`; it now keys off the new
  `constants.CAMPD_BINNING_ISOS = {ERCOT, CAISO, NEISO, NYISO, PJM}`. ERCOT still
  reads its curated `custom-bin-assignments.csv`; the other CAMPD ISOs synthesize
  the same per-plant bins frame from the EIA-860 fleet plus their CAMPD-derived
  `thermal_tranches_<ISO>.csv` via `fleet_to_bins` (the runner now mirrors
  `run_calibration.py`, filtering raw units by the exact binned `(plant_code,
  plant_group)` set so no plant is dropped or double-counted). ISOs without a
  bin artifact (MISO, SPP) cleanly fall back to the legacy `aggregate_fleet`
  path, exactly as before.
- **`historic_outage_overlay` default is now per-ISO.** New registry
  `constants.HISTORIC_OUTAGE_OVERLAY_BY_ISO` sets the effective default: `True`
  for the facility-summed ERCOT extract (the unit-level derate only supplements
  it), `False` for ISOs whose unit-level CAMPD file is the complete source
  (CAISO/NEISO/NYISO/PJM), so the two layers don't double-count. The runner
  resolves `registry.get(iso, config.historic_outage_overlay)` and threads the
  result into the fleet-array build without mutating the recorded run config;
  the `ScenarioConfig` flag remains the fallback for ISOs absent from the
  registry. No outage function signatures changed.
- Tests: `tests/test_runner.py` covers the per-ISO binning path (ERCOT curated
  sheet, CAISO/NEISO/NYISO/PJM synth, MISO/SPP legacy fallback) and the overlay
  resolution (ERCOT→True, PJM→False, unlisted→config flag).

## 2026-06-15 (W1a — per-ISO planning reserve margin)

The reserve-margin adequacy backstop
(`capacity.py::apply_reserve_margin_build`) no longer makes every ISO inherit
ERCOT's economically-optimal 13.75% reserve margin. Added
`PLANNING_RESERVE_MARGIN_BY_ISO` (cited per-ISO resource-adequacy targets) and
resolve the margin as
`PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, config.planning_reserve_margin)`:

- The per-ISO registry now leads; `ScenarioConfig.planning_reserve_margin`
  (still 0.1375) is the fallback/override for an ISO absent from the registry.
- Cited targets: ERCOT 0.1375 (Brattle/Astrapé 2022, PUCT), CAISO 0.15 (CPUC
  RA), PJM 0.178 (PJM 2025/26 IRM), MISO 0.179 (MISO PY2024-25 LOLE ICAP PRMR),
  SPP 0.15 (SPP Planning Criteria v4.1A), NYISO 0.244 (NYSRC 2025-26 IRM),
  NEISO 0.157 (NERC 2023 LTRA reference margin; `needs-citation` for a firm
  ISO-NE filing).
- ERCOT parity: the registry value equals the historic scalar default, so the
  ERCOT backstop build is byte-identical; capacity-market ISOs now force-build
  to their own (higher) published floor. New `test_capacity.py` coverage for
  ERCOT parity, the higher PJM floor, explicit-scalar override, and
  absent-ISO fallback.

## 2026-06-15 (W1c — generic-improvement coverage verified for all seven ISOs)

Verified that the already-ISO-agnostic ERCOT engine improvements fire for every
registered ISO, and that no per-ISO config datum they read is missing. **No
engine code changed and no config backfill was needed** — every datum was
already present and consistent with each ISO's real mechanism.

- New `tests/test_iso_coverage.py` — parametrized over
  `config.iso_configs._ISO_BUILDERS`. Asserts per ISO: gas_ct is a new-entry
  candidate with a `QUEUE_CAP_PER_TECH_GW[iso]["gas_ct"]` cap; all seven
  thermal fuel classes (coal, gas_cc, gas_ct, gas_st, oil, gas_cc_ccs, nuclear)
  are in the retirement screen; an import node resolves where the ISO has
  import tranches; ERCOT has no import node and a zero state carbon price
  (parity).
- New `docs/multi-iso/propagation-coverage.md` — per-ISO coverage matrix.
  CAISO/PJM/NYISO/NEISO carry priced import nodes (ERCOT/MISO/SPP none, as
  intended); CAISO (CARB) and NYISO/NEISO (RGGI) carry state carbon prices.
- W1c marked DONE in `docs/multi-iso/09-ercot-propagation-prompt-pack.md`.

## 2026-06-15 (docs — ERCOT→all-ISO propagation audit & prompt pack)

Audited the ERCOT model's accumulated changes for applicability to the other
six ISOs and produced a sequenced propagation prompt pack
(`docs/multi-iso/09-ercot-propagation-prompt-pack.md`), indexed in the
multi-iso README. Docs only — no code changed.

- **Energy-only-specific (do NOT propagate):** ORDC overlay, the RTORDPA
  reliability-deployment offset, the RTC+B regime switch, the exogenous AS
  revenue stream, and the $5,000 energy-only VOLL stay ERCOT-gated.
- **Already ISO-agnostic (verify only):** reserve-margin backstop, full
  fossil/nuclear retirement, gas-CT peaker entry, price-duration entry
  economics, commitment screen, priced imports, carbon pricing — these read
  per-ISO config and already apply to any ISO.
- **Actionable propagation gaps:** the ERCOT-tuned `planning_reserve_margin =
  0.1375` global default (→ per-ISO registry), the ERCOT-gated CAMPD per-plant
  binning at `runner.py:207`, the global `historic_outage_overlay` default, the
  ERCOT-only curated fleet dicts, missing `thermal_tranches_{MISO,SPP}.csv`, and
  uncurtailed-HSL coverage for PJM/NEISO/MISO/SPP.
- Pack is sequenced W0 (parity-baseline gate) → W1a/W1b/W1c (parallel engine
  generalizations) → W2a/W2b (parallel, after binning unlock) → W3 (per-ISO
  HSL/recalibration), with an ERCOT byte-identical guard on every wave.

## 2026-06-15 (ERCOT — market-design regime switch: contain the 2023 reliability-deployment to its own design)

The reliability-deployment offset (RTORDPA analogue) is calibrated to the 2023
ECRS-conservatism design ERCOT reformed at RTC+B go-live (2025-12-05), so it
must not be carried silently into forecasts. New `ercot_market_design`
("auto"/"ordc"/"rtcb") + `rtcb_reliability_deployment_mw` (default 0), with
`scarcity.ercot_market_regime` / `effective_reliability_deployment_mw`:

- ORDC regime (auto: years <= 2025) applies `ordc_reliability_deployment_mw` —
  2023 backcast reproduced under its own design (MAE 32.5 -> 12.3, unchanged).
- RTC+B regime (auto: years >= 2026, forecast) applies
  `rtcb_reliability_deployment_mw` (default 0 -> price to fundamentals); a
  scenario can raise it to model 2023-style conservatism recurring.
- Deriver and runner use the per-year effective offset. 3 regime tests added;
  backcast 2023/2024/2025 behavior byte-identical.

## 2026-06-15 (capacity — reserve-margin adequacy backstop + full fossil/nuclear retirement coverage)

Entry/exit fitness fix 4 from docs/forecasting-entry-exit-assessment.md, plus
broadened retirement coverage.

- **Reserve-margin adequacy backstop** (`reserve_margin_build_enabled`, default
  off; `planning_reserve_margin` default 0.1375 = ERCOT economically-optimal RM,
  Brattle/Astrape 2022). After the economic new-entry screen, if the system's
  accredited firm capacity (thermal UCAP = pmax x (1-EFORd); wind/solar/hydro by
  RENEWABLE_CAPACITY_CREDIT ELCC; storage by duration ELCC) is below
  peak x (1 + margin), force-builds gas_ct to fill the gap (capped at the ISO
  annual queue throughput). The ReEDS/NEMS/CDR structural adequacy mechanism:
  keeps the lights on independent of price accuracy. Uses the prior-year peak
  (build-ahead-of-need). New capacity.accredited_firm_capacity_mw /
  apply_reserve_margin_build; wired into evolve_fleet; renewable/storage firm
  threaded via prior_results. nuclear removed from _FIRM_CLEAN_FUELS (it is now
  screened, so it is a protected-thermal resource in the floor, not always-on).
- **Every fossil class and nuclear can now retire on economics:** oil,
  gas_cc_ccs and nuclear added to _THERMAL_FOM / _RETIREMENT_YEARS /
  _FOM_MULTIPLIER, with fixed_om_oil 25, fixed_om_gas_cc_ccs 25,
  fixed_om_nuclear 130 $/kW-yr and per-fuel loss-year thresholds. Previously
  only gas_cc/gas_ct/gas_st/coal were screened.
- Tests: reserve-margin-build + firm-capacity tests; fossil/nuclear coverage
  regression. Full suite green except 3 pre-existing CAISO data-file failures.

## 2026-06-15 (capacity — AS revenue + new-entry peaker candidate + price-duration entry economics)

Entry/exit fitness fixes 2-3 from docs/forecasting-entry-exit-assessment.md.

- **Ancillary-service revenue** (see prior entry; src/market_sim/model/
  ancillary.py) credited in the retirement, new-entry and storage-entry
  screens.
- **gas_ct (simple-cycle peaker) is now a new-entry candidate**
  (`_NEW_ENTRY_TECHS`), with NEW_ENTRY_COSTS data (NREL ATB / Brattle ERCOT
  CONE frame-CT ~$162/kW-yr) and its own per-ISO interconnection-queue cap
  (ERCOT 3 GW/yr). Previously the model could not forecast new peaker entry at
  all.
- **Price-duration new-entry economics for dispatchable thermal:** gas_cc and
  gas_ct expected revenue is now the price-duration energy margin
  `sum_t max(price_t - var_cost, 0)` vs annualized fixed cost (the
  net-revenue-vs-CONE test), replacing the flat `base_cf x mean(price)` that
  ignored the price shape and understated peakers severalfold (they earn in the
  scarcity tail, not at the mean). Renewable/nuclear CF-profile path unchanged.
- Tests: gas_ct peaker-entry regression added; two queue-cap tests updated for
  the new candidate mix; gas_cc fuel-cost test updated to the corrected
  price-duration economics (a CC facing a flat price above its marginal cost
  correctly runs baseload). test_capacity + test_storage + test_soundness +
  test_ancillary green.

## 2026-06-15 (ERCOT — reliability-deployment scarcity overlay + steam-gas retirement screen)

Fixes the two entry/exit gaps `docs/forecasting-entry-exit-assessment.md`
identified as making the model over-retire / under-price tail-dependent units.
**Dispatch is byte-identical** — the scarcity adder is a separate series that
never gates volumes; only the capacity-economics revenue and the retirement
screen change.

- **Reliability-deployment overlay** (`ordc_reliability_deployment_mw`, the
  RTORDPA analogue; default 0, recommended ERCOT ~2,500 MW): a reserve-tightness
  offset netted from reserves before the published ORDC curve, calibrated to the
  2023 stress year. The published ORDC formula is untouched (stays
  parameter-honest); this is an explicit, scenario-adjustable stress-year
  scarcity calibration, kept separate. At 2,500 MW: 2023 monthly LMP MAE
  32.5 → 12.3 (was → 30.1), 2023 scarcity hours 0 → 112 (vs 181 actual), 74% of
  the Jun–Sep gap closed; 2024/2025 ~unchanged (self-targeting via the curve
  nonlinearity). Wired into the deriver (`--reliability-deployment`) and the
  runner's forecast econ-price path. Series committed as
  `scarcity_reldeploy2500.parquet` in the keeper bundle. See
  `docs/ordc-overlay.md`.
- **Steam-gas retirement screen:** `gas_st` added to `capacity._THERMAL_FOM`
  (+ `_RETIREMENT_YEARS`, `_FOM_MULTIPLIER`); new `fixed_om_gas_st = 35 $/kW-yr`,
  `retirement_years_gas_st = 2`, `retirement_fom_multiplier_gas_st = 1.0`.
  Legacy gas steam was previously absent from the screen → could never retire on
  economics regardless of revenue. Net effect (2023 stress year, net $/kW-yr vs
  bar): ST_GAS 21 → 127 (bar 35: retire → KEEP), COAL_PRB 22 → 143 (bar 52:
  retire → KEEP), CT_PEAKER 12 → 109. Two regression tests added.
- Assessment memo updated (`docs/forecasting-entry-exit-assessment.md`):
  AS-revenue evidence corrected to point at the missing AS term in
  `capacity.py` (AS-aware volume/cost layers exist; AS market *revenue* does
  not). Full suite: 1,029 + 2 new pass; 3 pre-existing CAISO data-file
  failures unrelated.

## 2026-06-13 (CAISO — offer-curve probe panel + Jacobian, sensitivity map only)

Mapped CAISO offer-curve band sensitivities ahead of calibration; **no keeper,
no band move applied** — the import-tranche mis-pricing (P9/P12) stays the
blocking owner of the price level and the CC_REGULAR −21 TWh gap.

- **Probe panel** (12 bundles, 2023, `results/calibration/caiso_probe_*`):
  zero-delta code baseline reproducing `caiso_1_priced_ix`'s 2023 numbers, plus
  11 single-knob ±0.05 band probes (CC_REGULAR ×5 incl. both committed signs,
  CT_PEAKER ×2, ST_GAS ×2, CC_CHP, CT_CHP; no coal — CAISO has none). Dashboard:
  `caiso 3 probe-base` / `3a` / `3k` kept, 9 dominated entries pruned.
- **Jacobian fitted** (`inputs/processed/offer_curve_jacobian.csv`, +80 CAISO
  cells; ERCOT/PJM rows byte-equal): CC_REGULAR committed/econ_low/econ_high
  own-class −14.7/−9.0/−7.3 TWh/unit-mult (med confidence); CHP committed knobs
  −3.6/−4.4; **CT_PEAKER, ST_GAS and CC peak knobs measure dead** — the
  over-importing WECC node owns the margin and absorbs 30–50% of every live
  move. Held-out back-test (CC committed +0.05): prediction-error RMS 0.039 TWh
  vs actual 0.357. Max in-trust-region joint move recovers only 1.6 of the
  21 TWh CC gap — documented as what the Jacobian cannot fix.
- `scripts/derive_offer_curve_jacobian.py`: curated REGISTRY entries for the
  probe chain + `ISO_STATES["CAISO"]={"CA"}` (adjacency fuel filter). Analysis:
  `docs/calibration-log.md` "CAISO 3". ERCOT/PJM/NYISO/NEISO untouched.

## 2026-06-13 (NEISO offer-curve probe panel + Jacobian — analysis only)

Mapped the offer-curve band sensitivities around the NEISO P12 primary-year
keeper (`neiso_p12_base_2024`) without re-tuning it.

- **11-run probe panel** under `results/calibration/neiso_probe_*`: a
  code-accumulation anchor (P12 keeper config on current main — reproduces the
  keeper exactly) plus ten ±0.05 single-knob `--offer-curve-delta-json` probes
  (CC_REGULAR committed/econ_high ±, CT_PEAKER committed ±, ST_GAS
  committed/peak −, CC_CHP/CT_CHP committed −). Dashboard keeps the two
  econ_high probes (`neiso 8/9`); the 9 dominated entries were registered then
  pruned per the top-5 rule (bundles kept).
- **`scripts/derive_offer_curve_jacobian.py`**: NEISO REGISTRY entries (P11/P12
  bundles + the panel's pure pairs) and the NEISO state set for the
  merit-order adjacency check. Fit writes 70 NEISO cells into
  `inputs/processed/offer_curve_jacobian.csv` (ERCOT/PJM rows byte-identical).
- **Findings** (full writeup in `docs/calibration-log.md`): NEISO TWh is
  band-immune (max −1.47 TWh/unit-mult, CC_REGULAR.econ_high — no coal, no
  substitution partner); econ_high is the only live knob and prices the
  monthly-AGT winter plateau (Jan/Feb-loaded ×2–3 — the U4 limitation, not a
  band target); ST_GAS bands are dead, proving no band reaches the
  dual-fuel/oil winter tail (no OIL band class exists). Joint-move recipe
  trust-region-freezes at the default cap; the capped move is immaterial and
  flips sign for 2025 — **no re-tune; the P12 keeper stands.** Backtest:
  held-out probe predicted to 0.001 TWh RMS.

## 2026-06-12 (NYISO 2025 — EIA-930 refresh unblock + price re-score)

Refreshed the EIA-930 `NYIS hourly` extract and re-ran NYISO 2025, which P12
had to file as data-blocked, then price-scored 2023 + 2025 now that P10/U2 LMP
landed.

- **`data/eia_hourly/NYIS hourly.parquet` regenerated** from the re-uploaded raw
  long files (`inputs/raw-data/eia-930/NYIS_{region,fueltype}.parquet`, now
  2015–2026) via `python scripts/convert_eia930.py NYIS --input-dir
  inputs/raw-data/eia-930 --force`. 2025 now carries a full 8,760 h (was
  Q1-only, 2,154 h); 2023/2024 demand & interchange are byte-identical
  pre/post, so the 2023 keeper, other ISOs, and loader tests are untouched.
  `nyiso_net_interchange(2025)` now returns the measured series (−19.09 TWh,
  was `None`).
- **NYISO 2025 backcast re-run** (`results/calibration/nyiso_p12_2025_refreshed`,
  dashboard `nyiso 2025 refreshed`). The P12 +22.7% over-generation closes: the
  measured net interchange is served by default (−19.09 vs −19.09 TWh, duration
  RMSE 0 MW), gas 68.30 TWh (−2.8% vs EIA-930 70.25), total 132.76 (+2.5% vs
  129.54). EIA-923 2025 is the preliminary M-file (total 115.84 TWh,
  under-reported) — flagged, EIA-930 used as the operational basis.
- **Price re-score (no longer level-only)** — scored 2023 keeper + 2025 vs
  `actual_lmp.json` (per-zone DA/RT) + `actual_lmp_hourly_NYISO.parquet` (system
  duration, `scripts/analyze_lmp_residual.py`). 2023 model $41.79 vs RT $30.29
  (+$11.5); 2025 $69.24 vs RT $60.73 (+$8.5). Both over-price the mid-merit band
  and under-price the scarcity tail (no-ORDC signature); p90 near-exact in 2025.
  Per-zone level + duration logged in the calibration log and bundle
  `SUMMARY-nyiso-2025-refreshed.md` / `PRICE-RESCORE-*`.
- **Docs** — `docs/calibration-log.md` ("NYISO 2025"), the doc-00 status table
  (NYISO now 2023+2025, price-scored), doc-07 §1 banner, the backcast writeup
  and `docs/calibration-best-so-far-nyiso.md` updated. oil stays U4-gated; 2024
  stays blocked on NY_2024 CEMS. ERCOT/PJM/CAISO/NEISO untouched.

## 2026-06-12 (ERCOT — ORDC scarcity-pricing overlay + revenue wiring)

Post-solve ERCOT ORDC scarcity adder (published RTORPA formula, zero fitted
parameters) and forecast-mode revenue plumbing, behind
`ScenarioConfig.scarcity_pricing_enabled` (default off). The LP, volumes and
emissions are untouched; the overlay owns the price tail.

- **`src/market_sim/results/scarcity.py`** — published ORDC math: two
  half-hour LOLP terms, normal-CDF over reserves minus the minimum
  contingency level (LOLP pinned to 1 below it), `(VOLL − λ)` cap, the
  2019/2020 PUCT 0.5σ curve shift and the OBDRR048 multi-step RTORPA floor
  (date-gated 2023-11-01). Reserve headroom from the solved fleet
  (thermal availability − dispatch + storage and renewable-curtailment
  headroom; optional AS-plan netting, default 0 — netting the AS plan
  double-counts scarcity since ERCOT's RTOLCAP/RTOFFCAP count AS-held
  capacity; see docs/ordc-overlay.md).
- **`scripts/derive_ordc_overlay.py`** — post-processes a solved bundle:
  reconstructs hourly availability via the new
  `run_calibration.run_year(fleet_only=True)` exit (no LP re-solve), caches
  `availability.parquet`, writes `scarcity.parquet`
  (`lmp`/`scarcity_adder`/`lmp_scarcity`), prints gate metrics, the
  pre-adder residual-vs-headroom diagnostic (`--diagnostic`) and a
  per-class revenue report (`--revenue-report`).
- **`scripts/analyze_lmp_residual.py --with-scarcity`** — tail localization
  on the overlaid series.
- **`src/market_sim/runner.py`** — forecast mode (ERCOT only): economic
  retirement / new entry / CCS screens now see `prices + adder` instead of
  raw LP duals (the over-retirement bias on scarcity-dependent classes);
  persisted results unchanged.
- **ScenarioConfig** — 10 new tier-1/2 fields (`ordc_voll`, `ordc_mcl_mw`,
  `ordc_lolp_{sigma,mu}_mw`, `ordc_lolp_shift_sigma`, `ordc_multistep_floor`,
  `ordc_as_plan_mw`, `ordc_lolp_params_path`, `scarcity_pricing_enabled`)
  with curated citations in the parameter registry; PUCT changes (pre-Uri
  $9,000 VOLL) are runnable scenarios.
- **Validation (run92_kiamichi):** 2023 monthly LMP MAE 32.1 → 28.0 with
  the deep tail restored (0 → 15 hours >$500 vs 104 actual); 2024/2025 hold
  the ±$1 gates (7.3 → 7.9, 2.2 → 2.2). Docs: `docs/ordc-overlay.md`,
  calibration-log section "ERCOT — ORDC scarcity overlay + AS netting".

## 2026-06-12 (NYISO + NEISO P10 — LMP benchmark & zonal-sufficiency)

Processed the uploaded NYISO and NEISO LMP drops into the price reference and
ran the zonal-sufficiency gate for both ISOs (prompt P10, docs 07/08).

- **Organized `inputs/raw-data/lmp-data/`** — the uploads landed flat and mixed
  across ISOs; the 2023–2025 NYISO files (`NYISO_zonal_hourly.zip`, the monthly
  `*realtime_zone_csv.zip`, `dartmonthlylmpindex_*.csv`) moved to `NYISO/` and
  the NEISO files (`*_smd_hourly.xlsx`, `historical.zip`) to `NEISO/` via
  `git mv`. The SPP `*DAMLZHBSPP*` / `mirDownload.zip` and the PJM/CAISO files
  were left in place.
- **`scripts/derive_actual_lmp.py`** — added NYISO and NEISO builders.
  `actual_lmp.json` now carries complete NYISO (5-zone) and NEISO (4-zone)
  2023–2025 blocks: hub-level `da`/`rt`/`*_mon`/`*_pct` (NYISO = simple mean of
  the 11 internal zones; NEISO = the `.H.INTERNAL_HUB`) plus a new additive
  `zones` sub-dict of per-model-zone DA/RT annual + monthly means. ERCOT, PJM
  and CAISO blocks and their hourly parquets are **byte-identical**. New
  `actual_lmp_hourly_{NYISO,NEISO}.parquet` sidecars (same shape as PJM) feed
  the duration-curve overlays.
- **New: `scripts/_zonal_sufficiency.py`, `scripts/nyiso_zonal_sufficiency.py`,
  `scripts/neiso_zonal_sufficiency.py`** — the zone-spread duration-curve test
  (per-year p50/p90/p99, % hours |spread|>$5 / >$20, season + hour-of-day
  concentration), in the style of `scripts/caiso_zonal_sufficiency.py`.
- **New: `docs/multi-iso/nyiso-zonal-adequacy.md`** — 5 zones stand decisively;
  large one-signed downstate-dear separation (K/Long-Island the load-bearing
  split, p99 $85–98, >$20 in 10–21% of hours; J/NYC and F/Capital material).
  **New: `docs/multi-iso/neiso-zonal-adequacy.md`** — 4 zones stand but weakly;
  zones track the hub within a dollar or two (CT carries the only growing tail,
  p99 $5→$13.5 over 2023–2025). Noted that the NEISO SMD workbooks also carry
  zonal load — a follow-on U3/P8 demand refresh, out of scope here.

## 2026-06-12 (NEISO Stage H sign-off — P14 documentation)

Completed Stage H (documentation and sign-off) for the ISO-NE backcast.
The P12 three-year bundle (2023–2025) remains the keeper; this entry documents
and commits all reconciliation work only.

- **New file: `docs/multi-iso/neiso-backcast-2024.md`** — calibration results
  document in the style of `pjm-backcast-2023.md`. Covers the 2024 primary year
  in full (fuel-mix table, CO₂, interchange, run inputs) and cross-year 2023/2025
  scorecard. Documents the monthly-AGT dual-fuel limitation (largest monthly
  basis Jan-2025 $16.31 — below distillate parity ~$18/MMBtu; daily AGT U4
  needed to fully resolve), PS/BESS over-cycling (amber), P10-held price level,
  and the 2025 hydro-backfill-year workaround.
- **`docs/multi-iso/00-iso-addition-protocol.md`** — NEISO row updated to 4-zone
  topology (North/Central/Boston/CT + HQ_import), FIPS state→zone assignment,
  Stage H sign-off 2026-06-12.
- **`docs/multi-iso/01-data-needs-and-upload-manifest.md`** — EIA-930 table
  body updated (all seven ISOs now "present"); NEISO CEMS row corrected (all six
  states 2023/2024 present; NH_2025 the only remaining gap — upload U1).
- **`docs/multi-iso/08-neiso-prompt-pack.md`** — P14 block added with Stage G/H
  sign-off scorecard summary and filed limitations.
- **`docs/data-dictionary.md`** — NEISO and NYISO rows added to the per-ISO
  demand conventions table (measured interchange handling, zonal allocation).
- **`docs/parameter-citations.md`** — Six NEISO-specific entries resolved:
  `market_design.NEISO` (ISO-NE FCA 18 $95/kW-yr net CONE), `state_rps_floors.NEISO`
  (MA CES + regional blend), `gas_availability_factor.NEISO` (NERC GADS
  2019-2023, P12 verified), `nuclear_monthly_cf.NEISO` (EIA-923 Millstone 2+3 +
  Seabrook 2019–2023), `coal_price_base.NEISO` (EIA AEO 2024 NE bituminous,
  Tier-3 placeholder), `import_eford.NEISO` (scheduled NEPOOL/ISO-NE interties,
  0% EFORd per NERC GADS).
## 2026-06-12 (NYISO Stage H — P14 documentation sign-off)

NYISO 2023 backcast reaches Stage H. All packs P0–P13 were merged in earlier
sessions; this pass reconciles the prose docs with the as-built code:

- **New:** `docs/multi-iso/nyiso-backcast-2023.md` — results tables, the
  served-interchange structural fix (P9b closing the +25.6% over-generation),
  the 2024/2025 data blocks as named gaps, P12 probe results (`nyiso 1
  gas-actuals` no-op, `nyiso 2 chp-covered` negligible), and next-step
  hypotheses. Written in the style of `pjm-backcast-2023.md`.
- **doc-01:** EIA-930 §2 table updated — NYISO (`NYIS`), CAISO, PJM, ISO-NE
  rows changed from "MISSING — upload" to "present" (the banner already noted
  all-7-ISO coverage; the table rows were stale).
- **doc-07:** §1 P12 sign-off banner added; P14 prompt marked done.
- **CHANGELOG** this entry.

No code, config, or data changes in this pass. Parameter citations for NYISO
were already appended in P12 (`state_carbon_price_by_iso.NYISO`,
`nyiso_hydro_treaty_min_flow`, measured monthly gas citations in
`calibration-best-so-far-nyiso.md`).

## 2026-06-12 (CAISO import/export node calibrated — CAISO P9)

Fitted `IMPORT_TRANCHES["CAISO"]` / `EXPORT_TRANCHES["CAISO"]` to the EIA-930
CISO net-interchange duration curve, replacing the placeholder engineering
estimates. This is the calibration follow-up to defaulting the priced node on
(below).

- **Method.** `scripts/derive_import_tranches.py` measured-only mode against the
  pooled 2023-2025 CISO series (the existing CAISO bundle has no priced node, so
  a bundle-mode price fit would be circular). CAISO is a heavy, growing net
  importer: −28.9 / −32.4 / −36.2 TWh and imports in 86% / 89% / 91% of hours.
- **New tranches.** Six import blocks tiling the import duration curve —
  PNW_hydro_base (COI firm hydro baseload) → PNW_midC → DSW_solar_PV → DSW_CCGT
  → DSW_CT → WECC_scarcity, 11.4 GW total — plus two export sinks (export_solar
  midday surplus + export_curtail $0 floor, 6.5 GW). Prices are pre-carbon
  delivered WECC energy costs, cheapest-first, all below every sink; the CARB
  border-carbon adder is layered on at build time.
- **Fit quality** (price-orthogonal, vs measured): annual net imports within
  1-3%, duration-curve RMSE ~560 MW (was ~1,400), import-hour share 83-88% vs
  86-91%. Aggregate import capacity sits between the deepest measured hour
  (11.0 GW) and the ~12-15 GW WECC simultaneous-import rating (COI + PDCI +
  Path 46/45). Modeled clearing-frequency validation is deferred to CAISO
  P10/P11.
- Updated `build_wecc_export_sink` (now returns the $0 curtailment sink, since
  CAISO has two sinks) and the affected transmission tests.

## 2026-06-12 (CAISO backcasts default to priced WECC interchange)

CAISO backcasts now serve interchange through the priced import/export node by
default — the calibration harness no longer needs an explicit
`--priced-interchange` flag for CAISO.

- **Why.** `eia_loader.load_demand` does no interchange netting for CAISO (the
  CISO series is net load), so a backcast run *without* the priced node leaves
  CAISO's ~30 TWh/yr of net imports unserved and the domestic fleet
  over-generates gas. There is no measured-schedule mode for CAISO to displace,
  so the priced WECC node is the only correct default (the eastern ISOs keep
  their measured tie-line schedule by default).
- **New `constants.PRICED_INTERCHANGE_DEFAULT_ISOS`** (`frozenset({"CAISO"})`)
  plus a `resolve_priced_interchange(flag, iso)` helper. Both
  `run_calibration.py` and `run_calibration_full.py` expose
  `--priced-interchange` / `--no-priced-interchange` (tri-state, default per
  ISO); the run_config records the resolved value.
- **Tranches still uncalibrated.** The CAISO import tranches remain engineering
  estimates (CAISO P9 TODO: fit to the EIA-930 CISO net-interchange duration
  curve and validate vs OASIS path ratings). Defaulting the node *on* fixes the
  structural gap; fitting the tranche shape is the follow-up.

## 2026-06-11 (NEISO backcast P2 — per-plant offer-curve tranches & bin assignments)

NEISO prompt-pack P2 — the offline derivation that turns the NEISO thermal fleet
into per-plant offer-curve tranches. The CAMPD committed / peaking shares
(2023 + 2024 + 2025 NE-state facility CEMS) and the source-tagged bin-assignment
artifact already landed alongside P3; this pack validates that pipeline
end-to-end, documents the NEISO inflexible layer and the oil/dual-fuel peaker
band, and adds the regression tests. No modeled validation here (that is
P11/P12); ERCOT/PJM/CAISO artifacts are byte-identical (regression-tested).

- **Committed / peaking from CAMPD.** `thermal_tranches_NEISO.csv` carries each
  plant's measured committed floor (P5 of online available-CF) and CC duct-firing
  peaking share (P95 vs P99.5 of online net MW, capped 25%) over the pooled
  three-year window. Coverage: **100%** of CC_REGULAR MW (≈ 12.8 GW), **≈ 87%**
  of CC_CHP, **≈ 89%** of CT_PEAKER carry a *measured* committed share; the
  sub-CEMS fuel-cell / micro-cogen tail keeps the class default.
- **No coal must-run.** NEISO's lone coal unit, **Merrimack** (EIA 2364), is a
  winter peaker by 2023-2025 (a few hundred CEMS online hours/yr), so its
  derived `mustrun_pct` is **0.0** — every NEISO plant-group's must-run share is
  zero. The inflexible layer is CHP BTM steam hosts, nuclear (Millstone 2 & 3,
  Seabrook ≈ 3.4 GW), hydro min-flows, and any reliability units (none binds in
  the window).
- **Oil / dual-fuel peaker band — tagged from P13, not re-derived.**
  `fleet.dual_fuel_plant_groups()` (EIA-860 multifuel) flags the gas-primary
  oil-switchers in the offer-curve fleet — Montville (ST_OIL-capable) and the CT
  peakers (Potter, Waters River, A L Pierce, Bucksport, Waterbury, Exelon West
  Medway II, MMWEC, …). These dispatch as ordinary economic bins with no
  must-run pin; the oil switch is a fuel-price overlay, not a capacity floor.
- **Bin assignments are deterministic.** `bin_assignments_NEISO.csv` regenerates
  byte-for-byte from the current code + tranche artifact (no stale hand-edits);
  mixed gas facilities (Hartford Hospital, Kimberly Clark, Dartmouth Power,
  Medical Area Total Energy) split one row per `Plant_Group`.
- **Tests:** `tests/test_neiso_bins.py` — fleet bins load and cover the thermal
  fleet, tranche shares sum to 100, no coal must-run layer, CHP BTM removed from
  LP capacity, dual-fuel peakers dispatch economically, and the artifact is
  deterministic. ERCOT/PJM/CAISO bins regression-tested byte-identical.

## 2026-06-11 (NEISO backcast P13 — dual-fuel / oil winter switching)

NEISO prompt-pack P13 (Wave 1) — activate and validate oil/dual-fuel winter
switching, the second half of the ISO-NE winter-price mechanism (P7 set the
Algonquin gas basis). The national machinery needed no source change beyond the
gating already in place; this pack confirms detection end-to-end, proves the
switch consumes the P7 overlay, validates modeled oil against EIA-923, and adds
tests. ERCOT/PJM/CAISO MC unchanged (regression-tested).

- **Detection confirmed.** `fleet.dual_fuel_plant_groups()` (EIA-860 Multifuel
  "Switch Between Oil and Natural Gas? = Y", NG-primary) intersects the loaded
  NEISO fleet at **107 gas tranches / 6,367 MW across 42 plants** (incl.
  Middletown, Montville). Oil-**primary** RFO/DFO steam is correctly excluded
  from the switch and carried as `oil` fuel type: **135 units / 5,182 MW**
  (Wyman, Canal, New Haven, Montville, Newington). Mystic is **retired** in the
  2025 EIA-860 vintage — correctly absent.
- **Switch consumes the P7 overlay.** `resolve_fuel_prices` already orders
  `apply_hub_basis_overlay` before `apply_dual_fuel_pricing`, so a dual-fuel
  unit caps the AGT-blown winter hub gas at `min(hub_gas, oil)` × gas HR.
  `dual_fuel_switching` stays default-on for the PJM + NE/NY cluster and off for
  ERCOT/CAISO/MISO/SPP.
- **Validation (2023 smoke, `--iso NEISO --year 2023 --hours 8760`):** modeled
  oil **0.24 TWh** vs EIA-923 **0.39 TWh** — same order of magnitude, not
  near-zero (the doc-08 red-flag test passes). The ~37% shortfall tracks the
  gas_cc over-run in this pre-calibration smoke (69.3 vs 54.3 TWh) and should
  close as P11/P12 tune the offer-curve/import/gas-basis knobs.
- **Documented limitation (not fabricated).** The committed AGT basis is
  *monthly*; monthly averages never reach distillate parity (~$18/MMBtu; max
  Jan-2025 $16.9), so the dual-fuel CT/ST switch is wired but does not bind on
  monthly data — winter oil comes from the oil-primary steam fleet's scarcity
  dispatch. A daily-AGT U4 refinement is what would trip the CT switch. Same
  shape as the NYISO P13 finding.
- **Tests.** `tests/test_fuel.py`: `test_neiso_hub_overlay_drives_dual_fuel_
  switch` (Jan AGT spike trips the dual-fuel unit to oil; gas-only unit eats
  the full hub spike; shoulder month stays on gas) and
  `test_neiso_monthly_agt_basis_stays_below_distillate_parity` (guards the
  monthly-granularity finding across 2023–2025). Existing dual-fuel gating /
  parity / overlay no-op tests already cover ERCOT/PJM/CAISO unchanged.
- **Docs.** `docs/multi-iso/neiso-data-audit.md` §2b (detection + validation
  table); doc-08 §1 "Done by P13" status; this entry.

## 2026-06-11 (NYISO + NEISO P9 — priced import/export node, offline tranche fit)

NYISO and NEISO prompt-pack P9 (Wave 1), done together because they share
`constants.IMPORT_TRANCHES` / `EXPORT_TRANCHES`. Adds each ISO's priced
import/export node to the generalized J1 machinery (`build_import_generators`
/ `build_export_sinks` / `extend_with_import_node`) and fits the tranche
capacities to the EIA-930 net-interchange **duration curve** — an offline
data fit on the measured series, no LP calibration run (modeled-net-import
validation is P11/P12's, and depends on this pack, so self-validating here
would be circular). ERCOT/PJM/CAISO are untouched (regression-tested).

- **`IMPORT_TRANCHES` / `EXPORT_TRANCHES["NYISO"]`.** NYISO is a large,
  near-constant net importer (EIA-930 NYIS: +23.45 TWh / −2,677 MW avg in
  2023, imports in 100% of hours). Five import tranches priced at the
  neighbor hub, cheapest first — HQ hydro ($14, Châteauguay/Cedars), Ontario
  HOEP ($24), PJM West ($34), ISO-NE Mass Hub ($44), scarcity ($75) — plus
  one small export sink ($10; NYISO almost never exports). Each proxy cited
  inline (Tier 3).
- **`IMPORT_TRANCHES` / `EXPORT_TRANCHES["NEISO"]`.** NEISO is a steady net
  importer (+15.14 TWh / −1,728 MW avg in 2023, easing to +10.30 TWh in
  2024). Five tranches — HQ Phase II ($18, Sandy Pond HVDC), Highgate ($22,
  VT–HQ), NB/north ($30), NYISO ties ($36, Cross-Sound/Northport–Norwalk),
  scarcity ($68) — and two export sinks ($16/$8). The HQ_import zone was
  already in `_neiso_config`; added its Highgate/NB → North and NYISO-tie →
  Connecticut links so the bubble can carry the full ~4.4 GW measured import.
- **`IMPORT_ZONE` / `IMPORT_NODE_LINKS` / `IMPORT_EFORD`** entries for both.
  NYISO's external node (`NYISO_external`) is appended on demand by
  `extend_with_import_node` (PJM pattern) with four border links (sum ≈ 6.4
  GW); NEISO's is baked in (CAISO pattern). EFORD 0 (scheduled interties).
- **Duration-curve fit (offline, no LP).** `derive_import_tranches.py` gains
  a measured-only mode (no `--bundle`): the node's achievable net-export
  *levels* are placed optimally against the measured duration curve, so the
  reported RMSE depends only on the block capacities, not a (circular)
  self-solved price. Headline fit RMSE: **NYISO 320 MW (2023) / 333 (2024)**,
  **NEISO 271 / 266 (2023/24)** — both tighter than PJM's ~570; annual TWh
  within ~1%.
- **Report.** The calibration report's net-interchange section [2] now prints
  the offline priced-node **fit RMSE** alongside the modeled annual TWh,
  duration curve, and a new **diurnal** shape line, for every ISO with the
  node configured. `--priced-interchange` smoke-solves for both ISOs.

## 2026-06-11 (NEISO backcast P7 — measured gas, Algonquin winter basis, RGGI)

NEISO prompt-pack P7 (Wave 1) — the structural price pack. Measured monthly
gas, the Algonquin Citygate winter basis, and RGGI now reach NEISO marginal
cost; ERCOT/PJM/CAISO fuel prices and MC are unchanged (regression-tested).

- **`GAS_BASIS_DIFFERENTIAL["NEISO"] = +1.10`** (was missing). EIA-923
  Schedule-5 delivered-gas basis vs Henry Hub annual: +1.17 (2024), +1.07
  (2025 Apr–Sep); 2023 measured +3.17, skewed by the Jan/Feb arctic events.
  Strong caveat documented: only **two** NE plants report Schedule-5 gas
  (EIA codes 1660, 6081, partly LNG-priced), so the scalar is a
  forward-year/fallback value only — backcasts use the measured paths below.
- **Algonquin hub-month basis overlay (upload U4 satisfied via web-sourced
  index).** `inputs/raw-data/gas_basis_by_iso_month.csv` (the doc-01
  header-only template) now carries 35 of 36 NEISO months 2023–2025:
  basis = ISO-NE "average Massachusetts natural gas index price" (a
  volume-weighted AGT-area index, isonewswire.com monthly wholesale posts,
  one source URL per row) − EIA Henry Hub monthly. Winter blowouts land as
  measured: Jan-24 +4.50, Dec-24 +6.12, Jan-25 +12.79, Feb-25 +10.43,
  Dec-25 +10.64 $/MMBtu. Aug-2025 is missing upstream (no post found) and
  falls back to the EIA-923/shaped path — the flagged limitation.
- **New `gas_hub_basis_overlay` (Tier 3, default off).**
  `fuel.apply_hub_basis_overlay` REPLACES every gas unit's fuel price with
  measured HH-month + measured hub basis in covered months — the
  constrained-hub spot is the marginal unit's opportunity cost, and for
  NEISO the index is the far better measurement than the 2-plant Schedule-5
  sample (which it supersedes, e.g. LNG-skewed Jan-24 receipts of $11.69 vs
  the $7.68 index). Runs before the dual-fuel min so oil parity still caps
  the winter spike (the P13 switch trigger). Cross-check: the resolved 2024
  NEISO annual gas mean is $3.03 vs ISO-NE's published $3.06.
- **RGGI in marginal cost.** `STATE_CARBON_PRICE_BY_ISO["NEISO"]` =
  {2023: 14.87, 2024: 22.83, 2025: 24.35} $/t — yearly averages of the four
  RGGI quarterly auction clearing prices (Auctions 59–70, rggi.org press
  releases, cited per year), converted from RGGI's $/short ton at ×1.10231.
  Default-on for NEISO backcasts through the existing CAISO/CARB machinery
  (~$6–10/MWh on a 7.0-HR CC). All six NE states are RGGI members, so the
  cost applies ISO-wide.
- **Calibration harness defaults:** `gas_monthly_actuals` now also on for
  NEISO; `gas_hub_basis_overlay` on for NEISO only. `COAL_PRICE_BASE["NEISO"]
  = 3.0` placeholder added (Merrimack, ~5% CF, confidential receipts) so the
  resolver prices the NEISO fleet at all.
- **Tests:** RGGI in NEISO gas MC 2023–2025 (with the $5–7/MWh 2023 CC
  uplift), ERCOT/PJM zero and CAISO untouched; synthetic-CSV overlay
  semantics (covered months replaced, others kept, non-gas untouched, flag
  off = no-op); real-data Jan-2025 AGT-spike hour prices gas MC > 2× the
  annual average; ERCOT/PJM/CAISO resolver output byte-identical even with
  the flag forced on (no basis rows exist for them).

## 2026-06-11 (NYISO backcast P7 — measured gas, winter basis, RGGI carbon)

NYISO prompt-pack P7. Prices NYISO gas at the measured EIA-923 ISO-month series
and charges RGGI on in-state fossil marginal cost, both default-on for NYISO
backcasts. ERCOT/PJM/CAISO marginal cost is unchanged (full suite green bar one
pre-existing, unrelated CAISO TAC-area load-data failure).

- **Measured monthly gas default-on for NYISO.** `run_calibration.py` flips
  `gas_monthly_actuals` on for NYISO (as CAISO), so backcasts price gas at the
  EIA-923 volume-weighted ISO-month delivered cost (nearby-plant/state fallback)
  instead of Henry Hub + the flat +0.55 basis seed. The measured monthly basis
  runs +0.66/+0.49/+0.89 (2023–25) — annual deltas of only +0.11/−0.07/+0.34 vs
  the seed, but the **monthly** series carries the Transco Z6 winter blowout the
  seed flattens (Jan-2023 delivered **$10.02**/MMBtu vs HH $3.27; Dec-2025
  $8.20). Delta report in `nyiso-data-audit.md` §4.
- **RGGI in marginal cost (default-on).** `STATE_CARBON_PRICE_BY_ISO["NYISO"]`
  = `{2023: 13.49, 2024: 20.71, 2025: 22.09}` $/tCO2 — each year the simple mean
  of the four quarterly RGGI auction clearing prices (per-auction citations in
  `constants.py` / `parameter-citations.md`). Applied via the same
  `resolve_carbon_price` path CAISO uses; ~$5.4→$8.8/MWh on a 0.40 t/MWh gas CC.
  No border adjustment on imports (contrast CARB). A 7.0-HR CC at $18/t shows a
  $7.18/MWh uplift (doc-07 design-decision-4 ~$5–7/MWh).
- **Winter basis (U4) not landed → 923 fallback.** Added the tested
  `data.fuel.load_winter_gas_basis()` loader for the per-ISO monthly hub-basis
  CSV (`gas_basis_by_iso_month.csv`); it is still the header-only template, so
  the loader returns `None` and the gas path falls back to the measured 923
  series. Limitation and activation path documented (`nyiso-data-audit.md` §4).
- **`COAL_PRICE_BASE["NYISO"]`** added (2.3, defensive Appalachian fallback;
  NY grid coal is retired) so `resolve_fuel_prices` no longer `KeyError`s on the
  NYISO fleet.
- **Tests.** NYISO RGGI price + gas-MC uplift, ERCOT/PJM carbon-free and CAISO
  CARB unchanged, the $18/t CC uplift band, and the winter-basis loader
  (absent → `None`; present → per-month parse). `test_capacity.py` gains the
  NYISO RGGI case alongside CAISO's.

## 2026-06-11 (NYISO backcast P1 — unit-outage windows verified, coverage documented)

NYISO prompt-pack P1. Verifies the measured CAMPD unit-outage overlay for
NYISO and documents its detection coverage. No data regenerated — the
committed `campd-unit-outages-NYISO.csv` is current, and ERCOT/PJM/CAISO
extracts are untouched.

- **CSV verified current (2023 + 2025).** `derive_campd_unit_outages.py
  --iso NYISO` reproduces the committed `campd-unit-outages-NYISO.csv`
  **byte-identically** from the present `campd-unit-level/NY_{2023,2025}.parquet`
  extracts (1 621 windows, 44 plants). No `NY_2024.parquet` has landed, so
  **2024 is statistical-availability-only**: `unit_outage_derate_factors`
  returns an empty dict for 2024 and the fleet builder logs the statistical
  fallback. The CSV adds 2024 automatically once the extract is supplied.
- **Event-based rule confirmed; no coal targets.** NYISO's CEMS data carries
  **no coal-labelled units**, so the coal real-run rule fires on zero units —
  every NYISO unit is detected by the load-following event-based rule (any
  hour ≥ 2% CF breaks a window, ≥ 120 h minimum). Spot-checked Ravenswood,
  Astoria, Roseton/Danskammer, and Bowline: the cold-standby oil-gas steamers
  resolve into many event windows, the modern CCGTs into few.
- **Overlay wiring confirmed.** Under `outage_source == "historic"` for
  `--iso NYISO`, `generators_to_fleet_arrays` picks up the NYISO CSV through
  the generic per-ISO path (`unit_outage_csv_for_iso` → `_generic_unit_outage_target`
  / `_iso_plant_capacity`), mirroring PJM/CAISO; a smoke build derates 120
  plant-tranches for 2023 and 2025. The facility-summed layer has no NYISO
  file and degrades gracefully (as with CAISO).
- **Coverage documented.** `docs/offer-curve-methodology.md` §3 gains a
  *Detection coverage* subsection: of ≈ 21.2 GW of qualifying NYISO fossil
  capacity, **89% (≈ 18.9 GW, 44 plants) is CEMS-measured** and 11% falls to
  statistical, with CT/oil peakers carrying no overlay by design.

## 2026-06-11 (CAISO backcast P10 — LMP benchmark + zonal-sufficiency test)

CAISO prompt-pack P10 (Wave 1). The OASIS hub LMPs (upload U2) are now a
calibration price benchmark, and the 3-zone topology has its empirical gate.
ERCOT/PJM outputs regenerate byte-identically (regression-checked).

- **`actual_lmp.json` CAISO block + hourly sidecar.**
  `scripts/derive_actual_lmp.py` grew a CAISO builder: with no single system
  hub, the comparable-to-the-model system price is the three trading hubs
  (TH_NP15/TH_ZP26/TH_SP15) **load-weighted by zone share** and reindexed
  onto the Pacific dispatch clock. Emits DA + RT **2024 & 2025**
  annual/monthly means + duration-curve percentiles, plus
  `actual_lmp_hourly_CAISO.parquet` for the overlay. A full-year gate omits
  the retention-aged 2023 DAM stub; RT 2023 was never fetched.
- **Zonal-sufficiency test (`scripts/caiso_zonal_sufficiency.py`).** Hub-spread
  duration curves from the DA aggregates. Conclusion: **keep 3 zones** — the
  NP15−SP15 spread exceeds $20/MWh in 16.8% (2024) / 10.3% (2025) of hours
  (Path 15 north-south congestion, NP15 dear, solar shoulder seasons), while
  SP15 and ZP26 move together (>$20 in ~1% of hours). Write-up in
  `docs/multi-iso/caiso-zonal-adequacy.md`.
- **Aggregates documented as complete.**
  `scripts/postprocess_oasis_downloads.py` is idempotent/rerun-safe; the
  committed `CAISO_{dam,rtm}_hourly_{2024,2025}.csv` and
  `CAISO_tac_load_hourly_{2024,2025}.csv` are full years × all hubs/TACs.
  `caiso-data-audit.md` §4 U2 marked done with the 2023 gaps recorded.

## 2026-06-11 (E3 follow-up — one curtailment table, measured against consumed potential)

Cleanup after E3 (#304) and CAISO P6 (#310) landed overlapping curtailment
reporting:

- **One shared table.** The ERCOT-only `_print_curtailment` duplicate in
  `run_calibration_full.py` is gone; the ERCOT report path now calls the
  shared `_print_curtailment_vs_reported` (printed as `[3e]` there, `[1b]`
  on the generic path via a `label` parameter).
- **Model curtailment measures against the *consumed* potential**
  (`hsl_potential_mw`, the per-year-rescaled HSL) instead of the raw HSL.
  Latent-bug fix: ERCOT 2023's wind HSL is rescaled 104 -> 110 TWh before
  dispatch, so against the raw series the model's wind curtailment read a
  phantom ~0. The reported side keeps the raw `hsl - gen`. Regression test
  added.
- **Data-needed note instead of silent skip** for HSL-capable ISO-years
  without a built parquet (ERCOT 2024+ awaiting the NP6 uploads); ISOs with
  no HSL family stay silent.
- `run_calibration.py`'s reported-curtailment comparison now resolves any
  ISO through `load_hsl_hourly` (was ERCOT-gated), so CAISO smoke runs of
  the older script also get the reported columns.

## 2026-06-11 (CAISO backcast P5 — grid-battery fleet: COD ramp + EIA-930 battery benchmark wiring)

CAISO prompt-pack P5 (Wave 1). The CAISO BESS fleet was already loaded from
the EIA-860 energy-storage schedule (11.1 GW / 38.5 GWh by end-2024 in the
CISO BA, matching CAISO's published ~11 GW and the CEC's 10-GW-crossed-in-2024
milestone); this pack adds what the year-end snapshot missed. The pack's
cycling-cost item landed independently as ERCOT E2's `battery_dispatch_adder`
(PR #312) — P5 adopts that knob (no duplicate field) and adds the cycle-aging
citation to its registry entry. ERCOT/PJM backcasts are unchanged
(regression-guarded by tests). **Cache keys rotate**: `ScenarioConfig` gained
`storage_vintage_ramp`, so previously cached scenario-years re-solve on
first touch.

- **Intra-year COD capacity ramp (`storage_vintage_ramp`).** CAISO
  commissioned 3.0 GW of batteries during 2023 and 3.6 GW during 2024, so a
  flat year-end fleet overstates spring capability by ~2 GW.
  `load_eia860_storage` now aggregates each zone's capacity per EIA-860
  Operating Month (the renewables `vintage_capacity_ramp` convention) and the
  new `storage.storage_cap_profiles` expands the monthly steps into
  hour-varying `(n_storage, T)` charge/discharge/SOC bounds, which
  `dispatch.build_variable_bounds` now accepts alongside the static 1-D form.
  Tier-3 toggle, on for CAISO only in `_calibration_config`; ERCOT/PJM keep
  their calibrated flat year-end fleets until a recalibration pass (pack E2).
- **EIA-930 battery benchmark wired "if present" for every ISO.** Neither
  `data/eia_hourly/CISO hourly.parquet` nor `inputs/raw-data/CISO_fueltype.parquet`
  carries the EIA-930 `BAT`/`PS` storage split yet (CISO batteries currently
  ride in `OTH`, which swings −8.5 to +9.7 GW with a clear charge-midday /
  discharge-evening shape). The generic `load_eia_hourly_benchmark` now maps
  `NG: BAT`→`battery` and `NG: PS`→`pumped_storage` (net series, + =
  discharge), picked up automatically once a regenerated extract carries
  them — complementing E2's ERCOT-specific `load_ercot_battery_gen`. The
  non-ERCOT calibration report gains a `[2b] Battery cycling` section off
  the bundle's `storage.parquet` (E2's frame): model vs EIA-930
  discharge/charge TWh, evening (h17-22) discharge share, and hourly-net
  Pearson r — model-only with a note while the benchmark columns are absent.
- **Tests.** CAISO 2024 fleet vs published capacity (>10 GW, CEC/CAISO DMM);
  per-year power+energy totals reconciled against an independent EIA-860
  recomputation (acceptance); ramp monotonicity, December == year-end caps,
  profile expansion, and an LP check that a unit is idle before COD;
  ERCOT/PJM fleets carry no ramp and zero cycling cost under defaults;
  EIA-930 battery columns wired when present, skipped when absent.

## 2026-06-11 (ERCOT E2 — storage throughput cost + nuclear refuel validation)

ERCOT backcast realism for storage and nuclear (backlog item E2); PJM
unchanged (knob defaults to 0 and PJM bundles are untouched).

- **`ScenarioConfig.battery_dispatch_adder`** (Tier 3, default 0): per-MWh-
  discharged throughput/cycling cost on the EIA-860 grid-battery fleet — the
  battery analogue of `pumped_storage_dispatch_adder` (cycling degradation +
  ancillary-service opportunity cost the energy-only LP ignores). Wired
  `load_eia860_storage` → `StorageUnit.vom` → the LP discharge slot;
  `run_calibration_full.py --battery-adder`. Without it the LP over-cycled
  the ERCOT BESS fleet +48% vs the EIA-930 measured 2025 discharge; at the
  calibrated $10/MWh the model lands −1.5% (5.36 vs 5.44 TWh).
- **Storage observability:** calibration bundles persist per-unit hourly
  charge/discharge (`storage.parquet`, P1/P2 incl. `--run-p2`), carry the
  EIA-930 battery benchmark series (`NG: BAT`/`NG: UES`, NaN over unreported
  hours so partial years benchmark their reported window), and the report
  gains a §3d storage-throughput section.
- **ERCOT keeper re-tuned** (dashboard `run79 storage retune`): battery
  adder $10 + Jacobian joint-move on the non-CHP bands. 2023/2025 thermal
  classes land within ±3% (lignite and 2024's cheap-gas coal deficit → E1);
  nuclear −0.7% all years.
- **`scripts/derive_nuclear_monthly_cf.py`**: backcast analogue of
  `forecast_nuclear_refuel.py` — derives `NUCLEAR_MONTHLY_CF_BY_YEAR` from
  EIA-923 monthly actuals and `--check`-validates the committed table
  (ERCOT 2023–2025 reproduce exactly; the audit's +2.4% nuclear overshoot
  predated the overlay landing in PR #252).
- **Solver provenance:** `meta.json` records `highspy_version`. An
  identical-config Run-77 re-run on highspy 1.14.0 moved class splits
  several TWh at an equal objective (cheap-gas PRB/gas committed bid
  plateau admits alternate optima) — see the calibration-log E2 entry.
- **Docs realigned** (sync-docs): methodology-spec storage section now
  documents the per-unit discharge-cost adders (the "flag if unrealistic
  cycling appears" sensitivity fired and was resolved); claude.md objective
  carries the `dis_cost×Dis` term; parameter registry regenerated
  (battery_dispatch_adder + upstream dual-fuel/import params).

## 2026-06-11 (CAISO P6 — uncurtailed renewable potential, the HSL analogue)

CAISO backcasts now feed the dispatch *uncurtailed* wind/solar potential so
it re-curtails endogenously (playbook §8.3), instead of inheriting the
historical curtailment baked into EIA-930 delivered output. ERCOT's NP6 HSL
path is byte-for-byte unchanged (regression-tested).

- **`scripts/build_caiso_hsl.py`** builds
  `inputs/raw-data/caiso-hsl/caiso_<year>_hsl_hourly.parquet` (same schema
  as `ercot-hsl/`): uncurtailed = EIA-930 `CISO hourly` delivered +
  CAISO's reported 5-minute wind/solar curtailment
  (`inputs/raw-data/caiso-curtailment/`, upload U3), mapped onto the
  model's non-leap 8760 clock. 2023 and 2024 are built and committed
  (curtailment 2.66 / 3.40 TWh — matches CAISO's published totals;
  solar ~6.3 / 6.6% of potential, spring-peaked). 2025's workbook ends in
  May, so the year is **skipped with a data-needed marker** rather than
  fabricating zero curtailment for Jun–Dec; CAISO 2025 keeps the
  delivered-profile fallback.
- **`renewables.py`**: the HSL file lookup is generalized (`_hsl_file`);
  `load_renewable_profiles` now resolves CAISO backcast years to the
  uncurtailed parquet, zone-shaped by EIA-860 capacity exactly like the
  delivered path. New `load_hsl_hourly(iso, year)` exposes the GEN/HSL
  frame to the report and tests.
- **Calibration report**: new headline table `[1b] Renewable curtailment`
  in the generic (non-ERCOT) report — modeled re-curtailment
  (potential − dispatched) vs ISO-reported (HSL − delivered), annual TWh
  per fuel plus the monthly GWh shape. Prints only for HSL-backed
  ISO-years.
- **Tests**: CAISO backcast profile reconstructs the zero-floored HSL and
  sits ≥ delivered every hour; every committed CAISO HSL parquet has
  HSL ≥ delivered hourly with multi-TWh solar curtailment; ERCOT 2023
  still reconstructs the rescaled NP6 targets (110 / 32 TWh).

## 2026-06-11 (CAISO backcast — demand series and zonal disaggregation)

CAISO prompt-pack P8 (doc 06 §P8): system demand and zonal load split.

- **System demand from the EIA-930 `CISO hourly` extract.** `load_demand`
  gains a CAISO branch (`_load_caiso_hourly_demand`) reading
  `data/eia_hourly/CISO hourly.parquet`, so demand shares the
  chronological clock of the wind/solar/benchmark series read off the
  same rows (ERCOT precedent: the demand-profiles parquet is hour-shifted,
  which would desynchronize the duck curve). Generation-side convention,
  `td_loss_factor = 0.0`; **no interchange netting** — CAISO imports are
  supply via the `WECC_import` node, netting them into demand would
  double count. Net-load convention documented (playbook §8.1, data
  dictionary): the series is net of ~15+ GW BTM PV; backcasts model
  front-of-meter resources only.
- **Measured zonal load split from TAC-area load (upload U4, partial).**
  `eia_loader.caiso_zonal_load_shares` maps OASIS `SLD_FCST` ACTUAL
  TAC-area hourly load onto the trading hubs (PGE-TAC split 0.86/0.14
  onto NP15/ZP26 — no TAC boundary at Path 15, ratio preserved from the
  prior split, Tier 3; SCE+SDGE+VEA→SP15) and serves measured hourly
  zonal shapes for covered hours; uncovered hours carry the
  sample-average shares. Only 2023-01 has landed, so the static
  `load_share` fallback is now *measured* from that sample via the
  generalized `scripts/derive_load_shares.py caiso`:
  NP15/ZP26/SP15 = 0.43/0.07/0.50 → 0.3969/0.0646/0.5385 (Tier 2,
  winter-month sample — summer shifts share south). Refresh path:
  complete the U4 monthly pulls; shapes upgrade automatically.
- Tests: CAISO hourly shares sum to 1.0 each hour, measured window moves
  while the fallback stays static, missing-file year falls back, and
  zonal demand reconciles to the CISO system series within rounding.
## 2026-06-11 (PJM J1 — generalized priced import/export node)

Closes backlog item J1 (doc 06 §6). The +40 TWh PJM net-export structural
gap itself was already served by the measured tie-line schedule (2026-06-05,
Module M4) — the pjm-6 baseline carries it (2023 demand 823 TWh = 783
internal + 40 export) and gas dispatch already rose accordingly. What was
missing is the **price-responsive** node: forward PJM scenarios fell back to
*zero* interchange, and the CAISO WECC machinery was not reusable. ERCOT is
untouched (no import node; full suite green minus the known-stale
`test_coal_supply_pricing_uses_year_trajectory`, doc 06 E1).

- **Generalized machinery** (`model/transmission.py`): per-ISO
  `IMPORT_TRANCHES` / `EXPORT_TRANCHES` / `IMPORT_ZONE` / `IMPORT_NODE_LINKS`
  / `IMPORT_EFORD` constants drive `build_import_generators(iso)`,
  `build_export_sinks(iso)` (priced negative-generation blocks — a sink's
  $/MWh rides in `vom`, so absorbing exports credits the neighbors'
  willingness-to-pay) and `extend_with_import_node(iso_config)`. CAISO's
  WECC entries moved into the dicts unchanged (`build_wecc_*` remain as
  wrappers); NYISO/NEISO only need constants entries.
- **PJM node, calibrated to the 2023 net-interchange duration curve.**
  `PJM_external` zone + 5 border links (TTCs bounding the measured per-zone
  tie flows) joined on demand. Two scarcity import tranches (4 GW @ $46/$60)
  + six export sinks (9.8 GW @ $18–42), fitted by the new
  `scripts/derive_import_tranches.py`: measured net export is hourly
  price-orthogonal (corr −0.06), so the fit pairs the pjm_6 price duration
  curve with the measured interchange duration curve quantile-by-quantile.
  Static fit: 2023 annual 100% of actual, duration RMSE ~570 MW, diurnal
  corr 0.49; the same curve over-exports 2024 by ~+37% (load growth cut
  exports at an unchanged price level) — Tier 3, re-fit per vintage.
- **No double counting.** `load_demand` gained `include_interchange`; the
  runner and `--priced-interchange` calibration runs disable the measured
  schedule when the node serves interchange. Backcasts keep the measured
  schedule (data-first; exact); `run_calibration_full.py --priced-interchange`
  validates the node's calibration and the report's [2] section now prints
  the node's net position, duration-curve RMSE and import-hour share.
- **Forward runs**: `runner.run_scenario_iso` builds the node for any ISO
  with constants entries — PJM forecasts now carry price-responsive
  interchange (previously zero), and CAISO forward runs gain the export
  sink that `build_wecc_export_sink` documented but never wired in.
- **Bug fix:** `generators_to_fleet_arrays` pinned export sinks to a zero
  floor whenever any CHP/ST_GAS `min_gen` floor was active (the min_gen
  matrix replaces `pmin` as the LP lower bound for *every* generator, and
  PJM fleets always carry CHP floors). Sinks now keep their negative range.
- **Runs:** `results/calibration/pjm_j1_baseline` (pjm-6 config re-run,
  measured schedule — regression check) and
  `results/calibration/pjm_j1_priced` (same config through the priced node —
  calibration validation). Priced 2023: net export +39.0 TWh = 97.6% of
  actual (duration RMSE 647 MW); 2024 drifts +26% as fitted. The priced run
  also flattens zonal spreads (the external node wheels around the internal
  interfaces; all zones land at one price vs the baseline's ~$5 spread) and
  caps scarcity at the $46 import tranche (baseline max $695) — two more
  reasons backcasts keep the measured schedule.
## 2026-06-11 (PJM J3 — hourly LMP overlay + scarcity-residual localization)

- **J3a — true duration-curve overlay.** `scripts/derive_actual_lmp.py` now
  also writes `inputs/calibration/actual_lmp_hourly_PJM.parquet` (hub-mean
  hourly RT/DA LMP, 2023–2025, on the model's fixed 8760-hour local
  calendar) and adds `da_pct`/`rt_pct` duration-curve percentiles to
  `actual_lmp.json` (existing keys unchanged). The PJM `lmp-data/` exports
  were already hourly — the `_monthly_` filename is a misnomer.
- **New `scripts/analyze_lmp_residual.py`** compares a calibration bundle's
  hourly system price against the actual hourly series: monthly residuals,
  duration-curve overlay, and a Jul/Aug (configurable) localization by
  hour-of-day and actual-price band. Findings for pjm-9/pjm-10d in
  `docs/multi-iso/pjm-lmp-residual.md`: the Jul/Aug residual (−4.9 / −6.4
  $/MWh in 2023/2024) is a missing afternoon $75–200 price regime
  (16:00–17:00 −35/−39; actual-≥$75 hours carry 92% of the 2024 gap), not
  a level bias (p50 matches) — quantified before any reserve/ORDC work, per
  the J-series sequencing.
- **J3b prep.** Added TN to `campd.ISO_STATES["PJM"]`; the unit-outage
  derivation still awaits MD/DE/NC/TN (+ MI 2023/2025) CAMPD unit-level
  extracts before `campd-unit-outages-PJM.csv` can be regenerated.

## 2026-06-11 (ERCOT E3 — HSL coverage beyond 2023 + curtailment headline metric)

- **`scripts/build_ercot_hsl.py` builds any backcast year.** 2023 keeps the
  auto-downloaded UMass 60-Day-SCED path (regeneration verified
  byte-identical); 2024+ ingests uploaded ERCOT MIS wind/solar
  power-production reports (NP4-732/737-CD hourly actuals or NP4-733/738-CD
  5-minute actuals; csv or zip under `inputs/raw-data/ercot-hsl/np6/`),
  aggregating system-wide actual GEN and actual HSL onto the model's fixed
  non-leap 8760-hour clock (Feb 29 dropped, fall-back hours averaged,
  spring-forward gap interpolated). A year without uploads is skipped with
  a data-needed message — curtailment is never fabricated from
  delivered-generation data. The EIA cross-check now prefers the EIA-923
  totals in `calibration_reference.json`.
- **Per-year HSL profile path.** `renewables.py` resolves
  `ercot_<year>_hsl_hourly.parquet` for any ERCOT backcast year (was
  hardcoded to 2023), so 2024–2025 dispatch consumes uncurtailed potential
  the moment its parquet is built. New public helpers
  `load_ercot_hsl_hourly()` / `hsl_potential_mw()` expose the reported
  series and the rescaled potential the dispatch consumed.
- **Modeled-vs-reported curtailment is a headline ERCOT calibration
  metric** (the CAISO P6 pattern): `run_calibration.py` and the
  `run_calibration_full.py` bundle report (table [3e]) print wind/solar
  potential and modeled curtailment (TWh and %) against ERCOT's reported
  `HSL − GEN`, plus the monthly GWh shape. First 2023 reading: model
  curtails wind 2.0% vs 4.7% reported and solar 0.4% vs 6.3% — the model
  under-curtails.

## 2026-06-11 (PJM winter fidelity — dual-fuel switching, doc 03 Pack G)

Implements oil/gas dual-fuel switching for the PJM backcast (J2 winter
fidelity cluster: CT runtime −16/−21%, ST_GAS 2024 winter −15%, oil 0 vs
0.9 TWh). Objective-only — an `assemble_mc` fuel-price extension, no LP
structural change. Gated on `ScenarioConfig.dual_fuel_switching` (default
off; the calibration harness enables it for PJM only), so ERCOT and all
existing forecasts are byte-identical.

- **Dual-fuel flag from EIA-860 multiple-energy-source fields.** New
  `fleet.dual_fuel_plant_groups()` reads the committed EIA-860 Multifuel
  schedule parquet (`eia860_multifuel_operable.parquet`) and flags every
  operable gas-primary unit ("Energy Source 1" = NG) whose "Switch
  Between Oil and Natural Gas?" field is Y, classing each with the
  canonical gas classifier so the `(plant_code, plant_group)` keys line
  up with both the per-unit EIA-860 fleet and the per-plant tranche
  fleet. 577 keys nationally; 101 in PJM (~27 GW of switch-capable gas).
- **Oil price series with citations.** New `fuel.iso_monthly_oil_prices()`
  — the volume-weighted EIA-923 Schedule 5 monthly Petroleum receipt cost
  across the ISO's plants (PJM ~$17–23/MMBtu over 2023–2025; consistent
  with EIA's distillate ~$20 / residual ~$14 per MMBtu delivered to the
  electric power sector, 2023–2024) — sharing one resolver with
  `iso_monthly_gas_prices`. Unreported months and forward years fall back
  to the cited flat `OIL_PRICE_PER_MMBTU` ($18).
- **MC = min(gas, oil) per hour for capable units.** New
  `fuel.apply_dual_fuel_pricing()` caps each capable gas tranche's hourly
  fuel price at the delivered oil price (idempotent elementwise min,
  applied after the per-plant EIA-923 monthly gas overwrite so it sees
  the final delivered gas price). Emissions/heat rate stay on the gas
  characterization (known simplification). On the PJM 2024 calibration
  fleet the cap binds where reported delivered gas spiked past oil parity
  (e.g. plant 56807's CC tranches, 628 MW, ~12k unit-hours at an average
  −$32/MMBtu); with monthly ISO/plant-average gas it binds for few
  plant-months, so most of the modeled-oil gap awaits finer-than-monthly
  winter gas pricing.
- **Tests.** `test_fuel.py`: switch above parity / no switch below / off
  by default (ERCOT unchanged) / per-hour cap granularity. `test_fleet.py`:
  real-parquet capability extract and missing-parquet fallback.
## 2026-06-11 (CAISO hydro energy budgets + pumped storage — multi-iso P4)

Verifies the CAISO hydro/PS data through the generic PJM-built machinery
and makes the pumped-storage dispatch adder a per-ISO default. Full detail
in `docs/calibration-log.md` (2026-06-11 CAISO entry). **Cache keys
rotate**: `ScenarioConfig.pumped_storage_dispatch_adder` default changed
`10.0 → None`.

- **CAISO hydro budgets verified** (no loader changes needed): EIA-923
  CISO `HY` monthlies give 166 plants / 23.90 TWh (2023, extreme wet) and
  160 / 21.48 TWh (2024), within −2.0% / −5.6% of EIA-930 CISO hydro; all
  plants resolve to NP15/ZP26/SP15. Regression anchors added to
  `tests/test_hydro.py` (incl. an end-to-end solve pinning monthly
  dispatch ≤ budget on real CAISO budgets, and PJM/ERCOT-unchanged
  checks).
- **`load_hydro_budget(..., backfill_year=)`** (default off): the 2025
  EIA-923 early release covers only monthly-survey reporters (CAISO: 26 of
  ~185 plants, 12.3 of ~21.4 TWh); backfilling non-reporters from 2024
  recovers 20.39 TWh (−4.5% vs EIA-930). For the CAISO 2025 backcast.
- **Per-ISO PS dispatch adder** (`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`):
  PJM keeps its calibrated $10/MWh reserve-duty proxy; CAISO (2,078 MW
  EIA-860 PS fleet, Helms 1,053 MW, all NP15; 10 h / RTE 0.80 fleet
  params) resolves to $0 until its calibration says otherwise. The
  `ScenarioConfig` field is now `None` = per-ISO; a number overrides all.
- **`HydroBudget.monthly_min_energy` clips to the monthly budget** so a
  nameplate-fraction min-flow floor can't make a low-inflow month
  infeasible. Small-vs-large hydro split judged not warranted (≤30 MW =
  14% of CAISO capacity, ~13% of energy; see calibration log).
- Parameter registry regenerated; `validate_parameters.py` passes again
  (the new constants plus three previously missing scenario fields are
  registered).
## 2026-06-11 (CAISO pack P2 — per-plant offer-curve tranches & bin assignments)

CAISO backcast, 2024-first. ERCOT/PJM committed artifacts are untouched
(byte-identical); one runtime fix below also applies to PJM.

- **CEMS→EIA split-plant remap** (`campd.CAMPD_UNIT_PLANT_REMAP`): the AES
  Alamitos / Huntington Beach CCGTs (EIA 62115/62116) report CEMS under the
  legacy boiler ORIS codes (315/335). Their units (CT1/CT2) are re-keyed
  wherever unit identity is known, and facility-level loads substitute the
  companion unit-level rows for the split facilities (gross conserved).
  ~5.0 TWh/yr of CC history now attaches to the right fleet rows.
- **ST_GAS peaker exclusions**: AES Alamitos (315), AES Huntington Beach
  (335) and Ormond Beach (350) — the last once-through-cooling steamers,
  online 0.4–2.5% of CAMPD 2024–25 hours — join
  `outages.ST_GAS_PEAKER_PLANTS`: no outage overlay, no reliability floor,
  purely economic dispatch. `campd-unit-outages-CAISO.csv` regenerated:
  1,386 → 1,321 windows (126 economic-idleness rows dropped, 61 measured
  CC windows added for 62115/62116; all other rows byte-identical).
- **`thermal_tranches_CAISO.csv` re-derived from 2024–25** (2023 deferred
  with U1) with the remap in place: 83 measured plant-groups. Huntington's
  ST_GAS committed drops 68.2 → 8.9% (was polluted by the colocated CC);
  62115/62116 get measured committed 28.2/29.8%. CHP steam floors are
  **consumed, not re-derived** (`--chp-floors-from`): all 86 P3 floors
  byte-preserved.
- **Per-plant CC peaking (duct-firing) shares**: new `peaking_pct` column —
  the share of a CC's demonstrated sustained maximum (P99.5 of online net
  MW) cleared in <5% of online hours, capped at 25 — consumed by
  `fleet.thermal_tranche_peaking` under `cc_peaking_per_plant`, superseding
  the offer curve's class `pct_peaking`. CAISO CCs derive 0–6% (they cycle
  on the solar ramp; duct-fire headroom is thin) with Malburg at the 25 cap.
- **Bin assignments emitted**: `inputs/processed/bin_assignments_CAISO.csv`
  (`scripts/export_iso_bin_assignments.py`), 258 rows
  (Plant_Code, Plant_Group, Pct_Must_Run/Committed/Economic/Peaking, source
  tags). Measured committed covers 92.5% of CC_REGULAR, 100% of ST_GAS,
  78.6% of CT_PEAKER MW. Mixed facilities split per Plant_Group (Glenarm
  422 CC+CT flagged; no cross-fuel re-key needed).
- **CHP grid-share clamp in `bins_to_fleet`** (fix, affects PJM too): under
  `chp_steam_following`, a cogen whose measured committed floor exceeds the
  grid share net of the BTM pull-out (Elk Hills, Salinas River; PJM Marcus
  Hook, Grays Ferry) carried more LP capacity than its grid-facing share
  (up to +13%). Committed + peaking now clamp into `grid_cap` (committed
  keeps its measured level; the scarcity peak gives way).
- **Geothermal verification** (audit §2c): the biomass/OTHER must-run
  injection carries CISO geothermal at 8.05/7.81 TWh (2023/24) in a
  monthly-shaped 835–969 MW baseload band — not a flat annual average. The
  dedicated EIA-930 GEO column is only populated from mid-Dec 2025 (CISO
  folds geothermal into the 930 NG aggregate before that); where populated
  it reads 740 MW flat (CV 4.4%) vs the injection's 746 MW — within 1%.
- Tests: `tests/test_caiso_bins.py` (remap routing, artifact bounds, bin
  shares sum to 100, CHP BTM removed from LP capacity, per-plant peaking
  survives the offer-curve override).

## 2026-06-09 (Forecast mode — P0 fixes from the peer review)

Implements the P0 "fix before quoting any forward run" items from
`docs/peer-review-2026-06.md` (§F). Backcast behavior is unchanged (the
full suite passes; backcasts solve the weather year itself, where every
fix below is a no-op); forward runs change materially. **Cache keys
rotate**: `ScenarioConfig` gained a `mode` field, so previously cached
scenario-years re-solve on first touch.

- **B1 — retirement screens margin, not gross revenue.** The economic
  retirement screen now nets each unit's *full* variable cost (fuel + VOM +
  emission prices; computed even on cached years and threaded as
  `prior_results["mc_cost"]`) against price before comparing with
  going-forward fixed cost. Gross revenue let units "cover" FOM with money
  already spent on fuel — only units that barely ran could ever retire.
  Take-or-pay coal is charged full fuel cost here (avoidable on a
  retirement horizon) even though it bids below it in dispatch. The
  `mc=None` fallback (gross + a warning) survives only for callers that
  cannot supply costs. Spec §5.2 updated — it documented the same bug.
  Measured magnitude (ERCOT 2027 screen on 2026 dispatch): 28.0 GW of
  tranche capacity flags a loss year under the margin screen vs 10.3 GW
  under gross — 17.7 GW was mis-assessed. PJM barely moves (~34 MW)
  because its full-net-CONE capacity payment (finding B6, P1 scope)
  dominates the screen there.
- **B2/C8 — eastern-ISO forward runs no longer crash.** `QUEUE_CAP_GW` /
  `QUEUE_CAP_PER_TECH_GW`, `RENEWABLE_INSTALLED_MW`, `RENEWABLE_AVG_CF`
  and `RENEWABLE_ZONE_ALLOCATION` now carry PJM/MISO/SPP/NYISO/NEISO
  entries (Tier 3, flagged needs-citation), and `apply_economic_new_entry`
  raises a clear `KeyError` for any ISO missing queue caps instead of
  silently building nothing. A 2-year PJM forecast smoke run completes.
- **C1 — demand growth gap closed.** `_scale_demand` compounds from
  `config.weather_year`, not `START_YEAR`: 2026 demand is now 2024 actuals
  × two years of growth instead of 2024 actuals verbatim (an error that
  compounded through 2050).
- **B8 — Wright's-Law exponent.** `wright_cost` uses
  `-log2(1 − learning_rate)`, so a documented "20%/doubling" rate now
  yields exactly ×0.80 per doubling (was ×0.87); matches the CCS-retrofit
  path, which already used the correct form and now delegates to it.
- **B3 — vintage survives aggregation.** All three fleet aggregators carry
  a capacity-weighted `online_year` into bin representatives (was: reset
  to the 2000 default, which permanently disqualified every aggregated
  gas-CC bin from the CCS-retrofit screen and broke local learning
  attribution).
- **A3 — storage daily-cycling flag wired in the runner.**
  `storage_daily_cycling=True` now bounds forecast storage to within-day
  arbitrage (the backcast script already honored it; the runner ignored
  it, leaving full-year perfect foresight).
- **C9 — explicit `ScenarioConfig.mode`.** `"forecast"` (default) /
  `"backcast"`, validated in `__post_init__`; the renewables loader reads
  it instead of inferring backcast from `gas_price_override`, so a
  pinned-gas forecast sensitivity stays a forecast. The calibration
  scripts set it explicitly.
- **B10 — known-additions pipeline wired.** New
  `fleet.load_planned_additions()`: EIA-860 proposed units with
  construction-committed statuses (U/V/TS), BA-mapped to the ISO,
  post-snapshot effective years (`EIA860_OPERABLE_VINTAGE`, bumped to
  2025 with the 2025 Early Release parquets — older effective dates are
  slipped projects the snapshot has overtaken), zoned by plant lat/lon,
  injected in their online year (units already due join the first-year
  fleet). Forecast mode only; an all-non-thermal pipeline (CAISO)
  returns empty. `runner.py` no longer hard-codes
  `planned_additions=[]`. ERCOT pipeline: 30 units / 3.95 GW, 2026-29.
- **Registry**: `parameters.json` / `docs/parameter-citations.md`
  regenerated for the new constants (and 10 pre-existing missing entries).
  New tests: retirement margin semantics, queue-cap coverage + loud
  failure, PJM entry smoke, wright doubling, vintage preservation,
  planned-additions loader, mode validation, demand-scaling pins.

## 2026-06-09 (Backcast dashboard — single-run report redesign + diagnostics)

Redesigns the backcast results page around interpreting **one run across all
testing years at once**, replacing the comparison-centric layout. The run data
schema and the registry/regen pipeline are untouched, so concurrently pushed
ERCOT/PJM bundles render without any regeneration of their payloads.

- **Run report view (new default).** A per-year scorecard (classes in
  tolerance, system volume error, generation-weighted fleet dispatch r, model
  vs actual avg LMP), a **class-tolerance heatmap** (class × year, signed
  volume error with the ±5% deadband in gray) and a **dispatch-correlation
  heatmap** (class × year, hourly r vs CAMPD in green/amber/red bands at
  0.85/0.70), plus per-year monthly LMP model-vs-DA/RT charts — no more
  clicking through years to remember how a run did.
- **Auto-generated diagnostics.** The report decomposes every failing class by
  month, zone and plant (from the existing `volErr` payload + per-plant Δ923)
  and writes plain-language pointers: level shift vs seasonal concentration
  (→ committed vs peak/econ tranche), zone concentration (→ zonal load/basis),
  single-plant misses (→ outage overlay/capacity), weak-r classes split into
  timing-vs-volume problems with hour-of-day bias (too flat / too peaky), and
  LMP bias months tied to the coincident class volume miss. Computed
  client-side, so diagnostics appear automatically for every pushed bundle.
- **Comparison mode retired.** The Comparison/Single toggle, multi-run picker
  and run-over-run slope chart are gone; the sidebar is a simple newest-first
  run radio list. The old signed-volume-error matrix (Year/Month/Zone/Run
  column selector) is replaced by per-class **month and zone miss bars**
  ("Where the volume miss lives") on the Charts view.
- **Charts/Tables kept.** All deep-dive charts (commitment heatmaps, daily
  profile, hours-at-CF with tranche markers, monthly + annual generation)
  remain on Charts; the generation-mix, fuel-vs-930, fossil-class, monthly-LMP
  and per-plant tables remain on Tables. Year/class controls hide on the
  report (it spans years); zone chips steer every zone-aware metric on all
  views. Mobile: single-column cards/grids, tap-to-pin tooltips kept.

## 2026-06-09 (PJM backcast diagnostics — hydro/pumped storage in the LP, fresh dashboard benchmark, EIA-860 2025 ER)

Root-causes the "wildly off" PJM dashboard results: a stale shared benchmark
in the report layer, and ~14 TWh of supply (hydro + residual OTHER) plus ~8 GW
of peak capability (pumped storage + hydro) missing from the non-ERCOT LP,
which drove July/August VOLL price spikes that never happened.

- **Dashboard benchmark now comes from the newest bundle.**
  `render_calibration_html.build_payload` rebuilt the shared per-ISO benchmark
  only from registry run 0 — the *oldest* bundle — freezing plant→group
  classification and EIA-923 class totals to pre-coal-split code (PJM coal as
  one generic `COAL`, `COAL_SUB` before the SUB→`COAL_PRB` rename). Newer runs
  then rendered "Coal: model 0.00 vs actual ~116 TWh (−100%)" while the split
  coal classes had no benchmark plants and vanished from the heatmaps. The
  benchmark is now rebuilt per run so the newest bundle covering each year
  wins. The stale `pjm_8zone` bundle and its registry/run artifacts are
  removed.
- **Conventional hydro dispatches in the LP for every ISO.**
  `run_calibration.run_year` now builds one LP unit per EIA-923-reporting
  hydro plant (`_hydro_fleet`: EIA-860 nameplate power cap, EIA-923 monthly
  net generation as the dispatch LP's hydro energy-budget rows), replacing
  the flat-monthly ERCOT-only must-run injection — hydro can now peak-shave.
  PJM: 76 plants, ~3.3 GW, ~8.9 TWh.
- **Pumped storage joins the storage fleet.** New
  `storage.load_eia860_pumped_storage` reads prime-mover `PS` units off the
  EIA-860 generator schedule (the battery schedule does not carry them) into
  per-zone `StorageUnit`s with cited duration/RTE constants
  (`PUMPED_STORAGE_DURATION_HOURS` = 10 h, `PUMPED_STORAGE_RTE` = 0.80). PJM
  gains its ~5.0 GW (Bath County, Muddy Run, Yards Creek, Seneca, Smith
  Mountain).
- **Must-run injection un-gated from ERCOT.** The biomass/OTHER residual
  injection (`run_calibration_full._must_run_profiles`) now applies to every
  ISO; classes the LP fleet already carries as units are skipped (biomass for
  the per-plant non-ERCOT fleets), and pumped-storage plants are held out of
  OTHER (they dispatch as LP storage). Hydro is no longer an injected class
  anywhere. `--rebuild-benchmark` also stops using the ERCOT bin sheet for
  non-ERCOT plant→group maps.
- **Dead `COAL_SUB` knob removed and guarded.** Sub-bituminous routes to
  `COAL_PRB` (one PRB name across ISOs), so `COAL_SUB` offer-curve entries
  silently tuned nothing; the defaults are scrubbed and
  `--offer-curve-json` / `--offer-curve-delta-json` now reject unknown class
  keys loudly.
- **EIA-860 2025 Early Release.** `process_eia860.py` locates the header row
  by anchor columns (the ER adds a disclaimer preamble) and the committed
  parquet extracts are regenerated from `eia8602025ER.zip` (operating years
  through 2025).

## 2026-06-08 (Backcast — multi-ISO toggle + color-coded market chrome)

Makes the ISO axis a real, prominent toggle and registers a PJM run alongside
the ERCOT set so the dashboard ships with more than one market.

- **PJM on the dashboard.** Registered `pjm_8zone` (2023+2024) as `pjm 1 8zone`
  via `dashboard_add_run.py`, so the ISO toggle now switches between **ERCOT**
  (Run-58 / Run-59 / run57-canonical) and **PJM**. Both markets carry the new
  actual-LMP benchmark (PJM hub average, ERCOT `HB_HUBAVG`).
- **Color-coded market toggle.** The sidebar "Market (ISO)" control is now a set
  of prominent, color-coded buttons (canonical ISO colors from
  `docs/DESIGN_SYSTEM.md` — ERCOT green, PJM sky) with a per-ISO run count and a
  one-line hint listing the other loaded markets. The active market is echoed in
  a colored header badge next to the title and in a dynamic subtitle
  (`ERCOT · 3 runs · …`), so it is always clear which ISO is on screen.
- **`scripts/_backcast_shell`.** Added the ISO color tokens, `.isobtn` /
  `.isobadge` styles, and `isoColorVar` / `isoRunCount` / `updateIsoChrome`
  helpers; `selectIso` now repaints the header chrome on every switch. No change
  to the run data shape.

## 2026-06-08 (Backcast summary — looser class tolerance + actual-LMP comparison)

Loosens the backcast dashboard **Summary** page's per-class pass band and adds a
model-vs-actual average-LMP comparison.

- **Class tolerance.** A fossil class on the summary now passes within **±3%
  _or_ 1 TWh** of the actual (`SUM_TOL_PCT` / `SUM_TOL_TWH` in
  `scripts/_backcast_shell`), so small-volume classes that are off by a larger %
  but within a TWh no longer count against the headline. This summary band is
  separate from — and looser than — the per-cell heatmap deadband
  (`TOLERANCE_PCT`, unchanged at 0.02). The "Classes in tolerance" KPI, the
  worst-class color, the tornado band and its caption all reflect the dual band.
- **Average LMP comparison.** New `scripts/derive_actual_lmp.py` reduces the raw
  ERCOT settlement-point workbooks (`HB_HUBAVG`, DAM hourly / RTM 15-min) and the
  PJM hub LMP export to a small committed reference,
  `inputs/calibration/actual_lmp.json` (`{iso: {year: {da, rt}}}`, $/MWh).
  `build_payload` attaches it to each benchmark year as `avgLMP`, and the summary
  gains an "Avg LMP — model vs actual historical" KPI + panel showing the model
  (load-weighted over the selected zones) against the actual day-ahead /
  real-time system hub average with the signed Δ. Diagnostic only — LMP level is
  not a calibration target. Absent for an ISO-year with no price file (card shows
  model only).

## 2026-06-08 (Backcast — signed volume-error heatmap on the Charts view)

Adds a Plotly heatmap to the backcast dashboard's Charts view showing each
asset class's signed volume error — `(model_TWh − actual_TWh) / actual_TWh` —
with a class-row × axis-toggle (Year / Month / Zone / Run) layout, a diverging
cool→white→warm scale built from the dashboard color tokens, a neutral-gray
deadband, and a ±20% color cap. Each cell is annotated with its absolute model
TWh.

- **`market_sim.results.calibration`.** New canonical source-authority rule:
  `actuals_source(klass)` returns EIA-923 for every class except solar, which
  uses EIA-930 (utility + distributed PV is under-reported in 923). Added
  `signed_volume_error`, a thin wrapper over the existing `_pct_diff` so the
  export computes the delta with the same sign/zero-actual convention as the
  other diagnostics. The choice lives here, not in JS.
- **`scripts/render_calibration_html.build_payload`.** Each run-year now emits a
  `volErr` field: per fossil class, model vs EIA-923 TWh decomposed by zone and
  month (so the heatmap re-aggregates to any axis); solar carries a system
  annual vs EIA-930. Non-finite errors (nonzero model over a zero actual) are
  stored as `null` so the browser's `JSON.parse` never sees a bare `Infinity`.
- **`scripts/_backcast_shell`.** One `TOLERANCE_PCT` const at the top of the
  script (default 0.02; spec target 0.05) drives the deadband. The heatmap is
  Plotly-only and reuses the `--accent` / `--danger` / `--mr` design tokens —
  no new palette. The LP/dispatch/capacity code, the calibration
  source-authority logic, the Tables view and the existing run data are
  untouched (run data files only gain `volErr`).

## 2026-06-06 (CC peak — tweakable flat band instead of per-class duct burner)

Makes the CC_REGULAR / CC_CHP peak band a tunable offer-curve `peak` key
(default **2.25**, the F-class duct-burner multiplier and modal CC class)
instead of the hardcoded per-turbine-class table. So `CC_REGULAR.peak` /
`CC_CHP.peak` can now be nudged from the calibration workflow like every other
group's peak.

- **`scripts/run_calibration`.** Added `"peak": 2.25` to the CC_REGULAR and
  CC_CHP offer-curve entries. `fleet.bins_to_fleet` already honored an explicit
  `peak` key over the duct-burner fallback, so no model-code change was needed.
- **Behavior change at default:** all CC plants now peak at 2.25× regardless of
  turbine class — G/H-class CCs drop 2.50→2.25 (cheaper peak) and E-class rise
  2.00→2.25. The ERCOT fleet is overwhelmingly F-class, so the shift is small;
  a recalibration captures it. The per-class `cc_duct_burner_peak_mult` stays as
  the fallback when no `peak` key is set (e.g. other ISOs).

## 2026-06-06 (Uniform gas pricing — drop per-plant gas fuel cost by default)

Gas generators now all pay the **same** delivered price for a year (AEO
Henry Hub trajectory + ISO basis, optionally seasonal). Per-plant EIA-923
monthly *gas* costs are now **off by default** behind a new flag
`ScenarioConfig.gas_plant_monthly_fuel_pricing` (default `False`).

- **Why.** EIA-923 Schedule-5 gas-cost reporting is sparse in ERCOT (~12%
  of CC capacity), and merchant CCs in a hub all buy gas in the same
  market. Giving the few reporting plants their own (often higher,
  winter-spiking) cost while suppressed peers paid the smoothed trajectory
  split same-zone units on a reporting artifact, not real economics — e.g.
  Jack County (the only reporting CC among its North-zone neighbours) paid
  ~$2.69/$2.46 in 2023/2024 vs the $2.54/$2.19 everyone else paid,
  penalising it in 7/12 and 5/12 months and contributing to its under-run.
- **What changed.** `apply_plant_monthly_fuel_prices` skips gas unless the
  new flag is set; Jack now pays exactly the same uniform price as
  Freestone, Colorado Bend II, etc. **Coal is unchanged** — lignite
  mine-mouth vs railed PRB are physically distinct costs, so per-plant coal
  pricing (`coal_plant_monthly_pricing`) stays on by default.
- **Docstrings fixed.** Corrected the inaccurate "ERCOT — whose plants
  overwhelmingly report — is unchanged" note on `nearby_fuel_price_fallback`
  and updated `fuel.py` / `binning-methodology.md` to describe gas as
  uniform-by-default.
- Tests updated: the gas-overwrite mechanism tests now opt in via the flag;
  added a test asserting gas is uniform by default. All fuel tests pass.

## 2026-06-06 (Docs/data cleanup — kill the "bin dispatch" confusion)

Removes stale artifacts that misrepresented how the ERCOT CC fleet
dispatches. The model has dispatched **one LP generator per plant** on each
plant's **own** measured heat rate for some time, with the economic block
rendered as a 6-slice rising offer-curve ramp (`offer_curve_smoothing_n=6`,
linear) and the committed/min-load floor sized per-plant from CAMPD
(`cc_committed_per_plant`). But several legacy columns and doc sections
still described a multi-plant, bin-weighted-HR, flat-4-tranche, `pmin`-floor
model — enough to mislead a fresh reader (and an LLM) into the wrong mental
model.

- **`inputs/custom-bin-assignments.csv`** — dropped 12 columns that the
  loader never reads and that encoded the misleading picture:
  `Bin_Zone_Weighted_Avg_HR` (implies a bin-weighted dispatch HR — never
  used), `Dispatch_Mode`, `Must_Run`, the four absolute `HR_Must_Run/
  Committed/Economic/Peaking` (the dispatched band HRs come from the offer
  curve, not these), and `Plant_Age`/`POF_pct`/`WEFOR_pct`/`Derate_pct`/
  `EAF_pct` (availability comes from the age model + CAMPD outage overlays,
  not the CSV). `load_campd_bins` and all 117 bin/fleet/outage/fuel tests
  pass unchanged.
- **`docs/binning-methodology.md`** — retitled and rewritten to lead with
  "one plant = one LP generator", correct the tranche table (no `pmin`
  floors), add an **Economic ramp** section documenting the actual default
  (`_econ_curve_steps`, `offer_curve_smoothing_n`/`_exp`, peak folded for
  CC), fix the wrong `N=12`/`p=3` smoothing claim, and mark the flat
  per-group tranche table as legacy fallback.
- **`model-methodology-spec.md`** — corrected the §3.3 tranche bullets so
  Economic is the default rising N-slice ramp and Committed is the
  CAMPD-derived per-plant floor; flagged that no bin-weighted HR / `pmin`
  is used.
- **Docstrings** — `load_campd_bins` now states which CSV columns are
  overridden downstream; `disaggregate_dispatch` now states it is an
  identity no-op for the per-plant ERCOT fleet (a legacy multi-plant path),
  so its pro-rata split is not read into per-plant results.

No dispatch behaviour changes — this is documentation and dead-data only.

## 2026-06-06 (Unified offer-curve ramp — econ_low → econ_high, separate peak)

Makes every thermal group's offer curve behave identically: the n-slice
economic ramp spans **`econ_low → econ_high`** (its slope set by those two
endpoints), and the duct-firing / scarcity **peak is always a separate flat
tranche that jumps up above the ramp** — never folded into the ramp top.

- **Why.** Previously `_CURVE_FOLD_PEAK = (CC_REGULAR, CC_CHP, COAL)` ran the
  ramp from `econ_low` straight up to the duct-burner peak and emitted **no**
  separate peak tranche, so `econ_high` was **dead** for CC and coal — tuning
  it did nothing — and the LP disagreed with the dashboard (which already drew
  `econ_low → econ_high` + a separate peak). Only `CT_PEAKER` / `ST_GAS` did the
  intended thing. Now all groups share the `CT/ST` structure.
- **`data/fleet.bins_to_fleet`.** Removed the `_CURVE_FOLD_PEAK` /
  `_CURVE_ECON_ONLY` split (and `peak_in_curve`): the ramp always spans
  `econ_cap` from `econ_low` to `econ_high`, and the peak band is always
  emitted. `econ_high` is now the live ramp endpoint for CC and coal.
- **Configurable bands.** New optional offer-curve keys: **`pct_committed`**
  (committed capacity %, overrides the CSV; per-plant CC grounding still wins)
  and, for CC, an explicit **`peak`** HR multiplier (overrides the per-turbine-
  class duct-burner default, which is retained when `peak` is omitted). The peak
  capacity % (`pct_peaking`) was already configurable.
- **CT_CHP folded into the offer curve.** CT_CHP was the last group still on the
  legacy single-value overrides (`ct_committed/econ/peak_hr_override`); it now has
  an `offer_curve_by_group` entry (committed 1.10, econ_low = econ_high = 1.20,
  peak 1.40) mapped from those values, so its econ ramp and peak are tweakable
  like every other group. `econ_low == econ_high` makes the default a flat 1.20
  block — no dispatch change until the endpoints are pulled apart. The
  `ct_*_hr_override` config fields are now inert for CT_CHP.
- **Calibration impact.** CC and coal dispatch shifts — the ramp top drops from
  ~2.0–2.5× (duct burner) to `econ_high`, with the peak re-added as a separate
  slab above it. A recalibration run is expected to re-settle the band values.
- Tests: `TestUnifiedOfferCurve` (ramp tops at `econ_high`, separate peak band,
  `pct_committed` and CC `peak` configurable). Docstrings in
  `config/scenarios` and `scripts/run_calibration` updated.

## 2026-06-05 (ERCOT Northeast zone — NE_LOB trapped-generation lobe)

Splits a seventh ERCOT zone, **Northeast**, out of North to model the NE_LOB
generic transmission constraint — the single biggest piece of ERCOT congestion
the 6-zone topology was missing (binds 17.4% of 2023–24 SCED intervals).

- **Why.** NE Texas (the EAST weather zone) is a generation-rich lobe: ~4.2 GW
  of coal (Martin Lake, Welsh, Pirkey) + ~3.9 GW of gas (Tenaska Gateway CC,
  Wilkes, …) serving only ~3.4% of system load, behind a ~1,300 MW export limit.
  The six-zone model let all ~8 GW pour into North as if unconstrained, over-
  running Martin Lake (PRB) and mis-dispatching the NE combined-cycles. This is
  the carve-out the data-first rule calls out — real congestion the aggregation
  couldn't represent.
- **`config/iso_configs._ercot_config`.** New `Northeast` zone (load_share
  0.0335 = the EAST weather zone; North drops to 0.3081) and a
  `Northeast→North` link at **1,300 MW** (the NE_LOB limit). 7 zones, 9 links.
- **`data/eia_loader._ERCOT_LOAD_ZONE_GROUPS`.** EAST weather zone → Northeast,
  so the zone gets its own measured hourly load shape.
- **`data/zone_assignment._ercot_zone`.** NE-Texas box (lat 31.3–34.0,
  lon −95.55…−93.0) routes the lobe's plants to Northeast before the North
  catch-all; DFW / central-Texas (Limestone) stay in North.
- Tests updated to the 7-zone / 9-link topology, plus NE plant-assignment
  coverage. Baselined with the smooth offer curve (PRB sigmoid off) before any
  economic re-tuning.

## 2026-06-05 (ERCOT export TTCs from full-year SCED; data-first rule)

Sets the ERCOT West/Panhandle export TTCs to the **measured** GTC limits from
the full 2023–2024 NP6-86 SCED binding-constraint archive
(`inputs/raw-data/iso-specific-transmission/`, 202,512 SCED intervals), and
codifies the principle behind it.

- **New non-negotiable rule (`claude.md`): prefer accurate/measured data over
  estimates; never revert to an estimate because it fits the backcast better.**
  If real data makes the backcast worse, that's a *discovered bug* elsewhere in
  the model (the estimate was masking it) — keep the real input and fix the root
  cause. The only exception is genuine misalignment to our representation
  (different boundary/aggregation/units than our zones), which must be
  documented and reconciled rather than guessed.
- **`config/iso_configs._ercot_config` links.** West→North 7,300 + West→SC 2,700
  (WESTEX ~10,000 MW, binds 9.3%); Panhandle→North 2,680 (PNHNDL, 10.2%) — both
  measured. North→Houston **kept at 8,000** as the documented carve-out: the
  single N_TO_H GTC (~4,810, binds 0.21%) is one of several parallel 345 kV
  paths the six-zone reduction collapses into one link, so using it literally
  would understate the real interface.
- **West TTC effect is negligible (correction).** An earlier revision of this
  entry blamed the accurate West limit for a coal overshoot — that was a
  confounded comparison (`run33` predates the n=6 econ-curve smoothing). Clean
  isolation from existing bundles: `run34` (old TTC, smoothing on) and `run37`
  (new TTC, smoothing on) give an **identical** coal mix (70.4 TWh, +13% vs
  EIA-930), while `run33` (old TTC, **smoothing off**) is +3%. So the West TTC
  has ~zero effect on dispatch; the +13% coal overshoot is the **n=6 offer-curve
  smoothing** (`offer_curve_smoothing_n`, introduced run34), whose rising econ
  ramp cheapens the bottom of PRB's curve and pulls in ~+5.7 TWh of baseload
  PRB. The accurate West/Panhandle TTCs are kept as data-first hygiene.
- **PRB offer-curve experiment (run38).** Dropping the gas-keyed PRB passthrough
  sigmoid and relying on the static `offer_curve_by_group` COAL_PRB bands (with
  smoothing on) gives coal **−4.4%** vs EIA — closer than the sigmoid+smoothing
  default's +13%, and removes the eight sigmoid magic numbers. A small downward
  nudge to the PRB bands would close the remaining gap. Candidate replacement
  for the sigmoid, pending sign-off.
- **`scripts/derive_ttc_limits.py`** rewritten to scan the full multi-year
  NP6-86 set, report every GTC's binding frequency and mean limit, and print the
  derived `ttc_mw`; hardened against off-schema / latin-1 daily files.
- **Caveat (in the config comment).** ERCOT's *most*-binding GTCs are intra-zone
  pockets the six-zone topology cannot represent — NE_LOB (NE-Texas export,
  ~1,300 MW, 17.4%), VALEXP (5.9%), EASTEX (0.5%), TRDWEL — so intra-ERCOT
  dispatch is near copper-plate, faithful to ERCOT; a zone split (e.g. a NE lobe
  out of North) is the only way to capture that pocket congestion.

## 2026-06-05 (PJM refinements: CHP classification, border-zone exports, gas offer curves)

Three PJM fidelity refinements on top of the 8-zone topology + import/export
node. ERCOT untouched (full suite green).

- **CHP classification.** EIA-860's "Associated with Combined Heat and Power
  System" flag (joined plant-level from the operable sheet, dropped from the
  processed parquet) now maps gas cogens to CC_CHP / CT_CHP / ST_CHP instead of
  the merchant variants — 202 PJM CHP units (47 CC, 155 CT). CHP CC/CT/ST are in
  the outage-overlay QUALIFYING set, so they now get the historic overlay too.
  ERCOT is unaffected (its thermal comes from CAMPD bins; CHP grouping only
  reaches the filtered-out non-thermal subset of `load_fleet_from_csv`).
- **Border-zone export attribution.** `pjm_zonal_interchange` attributes each
  tie's measured net flow to the border zone it interconnects (NYISO→EMAAC,
  MISO-west→ComEd, Indiana/Ohio→AEP-Ohio, Michigan→ATSI, Carolinas/TVA→
  Dominion) instead of spreading the system total by load share. Total is
  conserved (40 TWh) but now realistic per zone: ComEd +17, AEP-Ohio +16,
  EMAAC +18.5 TWh export; Dominion −11.6 (net import from the Carolinas) —
  sharpening inter-zone congestion. `load_demand` adds the per-zone matrix for
  PJM, falling back to the system-net scalar when the tie file is absent.
- **Gas offer curves (`gas_offer_curve`, default off).** `split_gas_tranches`
  gives the per-plant gas fleet a stepped offer curve — a part-load committed
  band (heat rate × `cc_/ct_/gas_st_committed_hr_mult`), an efficient economic
  band, and a small duct-fired peaking top slice (× `ct_peak_hr_penalty`) —
  instead of a single flat block. Capacity-conserving; runs after the coal
  tranche split and preserves its passthrough fracs. Off by default so the
  current calibration is unchanged; enabling it shifts the gas merit order and
  wants a tuning pass on `_GAS_TRANCHE_SHARES`.

## 2026-06-05 (PJM import/export node — measured net interchange)

Closes the PJM backcast's largest structural gap (Module M4). PJM is a large
net exporter (~40 TWh / +4,564 MW avg in 2023), but the energy-only LP served
only internal load, so it under-generated by the export and mis-attributed the
missing marginal gas to coal. ERCOT and other ISOs are unaffected.

- **`data/eia_loader.pjm_net_interchange`** reads PJM's hourly actual tie-line
  interchange (`inputs/raw-data/iso-specific-transmission/
  PJM_{year}_import_export_act_sch_interchange.csv`), sums `actual_flow` across
  all 22 ties per hour and returns it export-positive on the 8760-hour clock.
  `load_demand` adds it to PJM's internal-load demand (the same interchange
  mechanism ERCOT uses for its DC ties), so the fleet now generates internal
  load **plus** the measured net export. The 2023 schedule (+4,564 MW = 40 TWh)
  matches the EIA-930 figure exactly. Modeled as the *measured* schedule (a
  backcast reproduces actual flows), not a price-responsive offer; absent a
  file (forward years) PJM falls back to zero interchange. Border-zone
  attribution of the export (vs the current system-net allocation) is the
  natural next refinement now that the 8-zone topology exists.
## 2026-06-05 (ERCOT per-zone hourly load shapes)

Gives each of ERCOT's six model transmission zones its **own measured hourly
demand shape** instead of a single ERCOT-wide demand curve scaled by a fixed
per-zone `load_share`. Mirrors the PJM per-zone-load change. Every other ISO is
untouched (full suite green, 701 tests).

- **Per-zone shapes** (`data/eia_loader.ercot_zonal_load_shares` + the
  `load_demand` hook): reads ERCOT's hourly *Actual System Load by Weather Zone*
  (NP3-565-CD, `inputs/raw-data/zone-specific-demand/ERCOT_Native_Load_<year>.xlsx`,
  2022–2025) and aggregates the eight weather zones onto the six model zones —
  West ← FAR_WEST+WEST, North ← EAST+NORTH+NORTH_C, Houston ← COAST,
  South_Central ← SOUTH_C, South ← SOUTHERN; Panhandle keeps no load (ERCOT has
  no Panhandle weather zone). For each hour, each zone gets its fraction of
  system load, and those time-varying shares multiply the existing EIA-930
  system demand total — so the **system level is unchanged** but zones now peak
  at different hours (the hot, wind-belt West and coastal Houston no longer track
  North Central's shape). This removes the single shared demand curve that was
  driving the previously-observed zonal-price artifacts.
- The eight-weather-zone → six-transmission-zone map matches
  `scripts/derive_load_shares.py`, which seeded the static `load_share` values;
  the full-year native-load annual averages reproduce those static shares to
  within ~1 pt, so only the *intra-year shape* changes, not the levels.
- Falls back to the static `load_share` split when the native-load file is
  absent, so non-ERCOT ISOs and missing-year ERCOT runs are unaffected.
- Refactored the shared normalize/back-fill tail (`_hourly_shares_from_groups`)
  out of `pjm_zonal_load_shares`; updated `tests/test_eia_loader.py` (CAISO now
  guards the static-share split; ERCOT gains per-zone-shape coverage).
- Re-ran the run32 configuration with the new per-zone demand
  (`results/calibration/run33_ercot_zonal_load`).

## 2026-06-05 (PJM 8-zone topology + per-zone hourly load shapes)

Replaces PJM's 4-zone pipe-and-bubble with an 8-zone, LDA-aligned topology
derived from the uploaded PJM transmission/LMP/load data, and gives each zone
its own measured hourly load shape. ERCOT and every other ISO are untouched
(full suite green, 699 tests).

- **Eight zones** (`config/iso_configs._pjm_config`): ComEd · AEP-Ohio · ATSI ·
  West-APS · Central-PA · Dominion · EMAAC · SWMAAC. The old `PJM_West` (half
  the load) blended ComEd ($24/MWh, export-congested), the AEP coal belt ($30)
  and import-constrained western PA ($33) — a ~$9/MWh spread across the
  AP-South / Bedington-BlackOak interfaces (the most-binding ones in the 2024
  transfer-limits data) that the 4-zone model erased. Cross-hub LMP std is
  ~$6.4/MWh, so the locational signal is real. Load shares and the inter-zone
  TTC/link mesh are seeded from the PJM metered-load and transfer-limits files
  (AEP/DOM ~4,069 MW, AP-South ~4,453 MW, Bedington-BlackOak ~1,947 MW).
- **Plant→zone crosswalk** (`data/zone_assignment._pjm_zone`): rewritten for the
  eight zones, splitting OH (ATSI north of ~40.9°), WV (APS north of ~39.0°), PA
  (Philadelphia metro → EMAAC, west of ~-79° → West-APS, else Central-PA) and MD
  (western panhandle → West-APS, else SWMAAC) by eGRID lat/lon/county. 29 of
  PJM's ~36 GW of coal correctly lands in AEP-Ohio (17 GW) + West-APS (12 GW).
  Tier 3 — approximates utility territories; verify against a PJM zone-county
  crosswalk.
- **Per-zone hourly load** (`data/eia_loader.pjm_zonal_load_shares`): reads
  PJM's hourly metered-load file, aggregates the 20 real transmission zones to
  the 8 model zones, and gives each its own hourly *share* of system load (zones
  peak at different times — EMAAC summer-peaking, West/ATSI flat). The shares
  multiply the existing system-demand total, so zonal *shape* comes from real
  data while the demand *level* stays tied to the existing series. Falls back to
  the static per-zone share when the file is absent. **Data note:** the uploaded
  `PJM2024_hrl_load_metered.csv` currently contains 2023 data — its (stable)
  zonal shape is used against 2024 demand and a warning is logged; a real 2024
  re-upload will refine the shapes.

## 2026-06-04 (Unit-level ERCOT outage backcast from CAMPD)

Replaces the hand-maintained, Jan–Aug-2023-only unit-outage extract with a
CAMPD-derived one covering **full 2023 and 2024**, so the ERCOT backcast's
unit-level derate layer now removes each generating unit's capacity during its
*own* observed outages — including the coal-unit outages the facility-summed
overlay structurally cannot see. ERCOT-only; no other ISO has unit-level CAMPD
extracts, so their plant codes never match and behaviour is unchanged.

- **`scripts/derive_campd_unit_outages.py` (new).** Detects an outage on each
  *unit's* own CAMPD hourly gross (`inputs/raw-data/campd-unit-level/
  {STATE}_{YEAR}.parquet`) and writes `inputs/raw-data/campd-unit-outages.csv`
  in the schema `unit_outage_derate_factors` consumes. Each unit's capacity is
  the EIA-860 generator nameplate (matched on plant code + normalised unit id —
  CAMPD `WAP5`↔EIA `5`, CAMPD `1`↔EIA `OG1`), falling back to the unit's
  observed CAMPD peak when no generator matches. The detector is chosen by the
  unit's own fuel: **coal** (baseload) uses the averaged real-run rule, so a
  sustained sub-5%-CF gap is an outage; **CC / gas-steam** (load-following) use
  the event-based rule (any hour above ~2% CF breaks the window), so a unit is
  flagged only when it goes genuinely dead and an economically idle CC turbine
  is *not* mistaken for an outage. CT peakers and the ST_GAS peaker plants are
  excluded, matching the overlay's convention.
- **`data/outages.py`.** `UNIT_OUTAGE_CSV` now points at
  `campd-unit-outages.csv`; the per-row `(outage_start, outage_end)` windows
  carry the calendar year and are clipped to the run year, so one file feeds
  every backcast year (2024 previously had *no* unit-level coverage). The
  hand-curated `inputs/tx-jan-aug23-unit-outages.csv` stays in the repo for
  reference (and is still read by `scripts/derive_cc_committed_pct.py`) but is
  no longer the model's source.
- **W A Parish coal units now resolve.** The facility-summed overlay misses a
  WAP coal-unit outage because the gas units keep the CEMS series running; the
  unit layer detects WAP5–8 directly (e.g. WAP8 offline Jan–Aug 2023, matching
  the old hand entry, plus the previously uncovered 2024 windows).
- **Backcast effect (apples-to-apples, untuned `run_calibration.py`,
  unit-outage source the only change).** Coal and gas-steam move toward
  EIA-923 in both years: 2023 coal −13.7%→−11.9% and gas-steam +27.7%→+18.0%;
  2024 coal −24.4%→−22.2% and gas-steam +29.0%→+9.6%. Total energy balance and
  the full test suite are unchanged.
- **Tuned-config validation (`run32_unitoutage` = run 31's tuned config +
  CAMPD unit outages; both on the dashboard).** In the calibrated config the
  largest-biased gas-steam class drops sharply (2023 ST_GAS +10.2%→+2.6%) and
  2024 lignite improves (−7.2%→−5.3%); the freed energy flows to CT peakers,
  which the no-commitment config already over-runs (2023 CT_PEAKER
  +18.6%→+42.5%), so a light CT-peaker / ST_GAS re-tune is the natural
  follow-up. Coal totals stay close (2023 +6.2%, 2024 +1.8% combined) and the
  grid energy balance holds at ~+1%.

## 2026-06-04 (PJM backcast: per-plant fuel costs, CAMPD outages, capacity payments)

Makes the PJM 2023/2024 backcast bind to real per-plant data instead of the
energy-only stub. Every change defaults off / no-op for ERCOT, whose fleet,
fuel costs and outage overlay are bit-for-bit unchanged (verified: identical
F923 rows, no oil units, both new flags off, full suite green).

- **National EIA-923 fuel-cost table.** `scripts/process_f923_fuel_costs.py`
  now defaults to all balancing authorities (was `--ba ERCO`), so PJM plants
  and the **Petroleum (oil)** fuel group flow through; it also carries each
  plant's `state` and drops anomalous receipts outside a per-fuel plausibility
  band (gas ≤ $200, petroleum ≤ $120, coal ≤ $60 /MMBtu — set above the real
  ~$118/~$59/~$27 maxima in this window so legitimate constrained-winter gas
  survives while order-of-magnitude data-entry errors, e.g. gas at
  $99,241/MMBtu in May, are removed). 98 bad receipts dropped; the 25 ERCOT
  plants' rows are byte-identical.
- **Oil priced from EIA-923.** `data/fuel.py` maps `oil → "Petroleum"`, so
  oil-fired units pay their own measured monthly delivered cost where reported
  (flat `OIL_PRICE_PER_MMBTU` otherwise). ERCOT has no oil dispatch units, so
  this is a no-op there.
- **"Nearby plant" fuel-cost fallback (`nearby_fuel_price_fallback`).** A
  gas/coal/oil plant with no EIA-923 cost of its own for a month is filled —
  before the Henry Hub / coal / oil trajectory — from the quantity-weighted
  average of the other plants that reported: its own state first (≥
  `nearby_fuel_price_min_state_plants`), else its model zone, restricted to the
  ISO's own fleet. Essential for merchant-heavy PJM, where PA/NJ/DE plants file
  almost no Schedule-5 cost. Off for ERCOT (its plants overwhelmingly report).
- **ISO-generic CAMPD historic-outage overlay.** EIA-860 generators now carry
  `plant_code`, `plant_group` and `state` (previously unset for every non-ERCOT
  ISO, which silently disabled both the F923 lookup and the outage overlay).
  `scripts/derive_campd_outages.py --iso PJM` derives
  `inputs/raw-data/campd-outages-PJM.csv` from the CAMPD CEMS state extracts
  (building nameplate/group from the EIA-860 fleet); the overlay reads a
  per-ISO `campd-outages-{ISO}.csv` (ERCOT keeps its legacy file + bin
  intersection, unchanged). The CAMPD loader now also reads unit-level uploads
  from `inputs/raw-data/campd-unit-level/{STATE}_{YEAR}.parquet` (flat dir
  first, so ERCOT/PA/NJ/MD/DE/IL are unchanged even where TX appears in both;
  unit rows are summed to the facility). PJM's full state footprint is listed;
  states whose parquet is not yet uploaded (currently OH, WV, KY, VA, NC, MI)
  skip with a warning and keep statistical availability until added. The PJM
  outage extract presently covers PA/NJ/MD/DE/IL/IN/DC (70 plants).
- **Note:** the EIA-923 *fuel-cost* parquet is regenerated national (the
  feature's input); the *generation* parquet is kept at its prior ERCOT scope
  (it only feeds hydro/offline reference-building, not PJM dispatch) — rebuild
  it national with `process_f923_fuel_costs.py --ba ""` when needed.
- **Per-plant calibration fleet (`plant_level_fleet`).** Non-ERCOT calibration
  runs the EIA-860 fleet at full per-plant granularity (no efficiency-bin
  aggregation) so plant identity reaches dispatch — required for the per-plant
  fuel cost and outage overlay to bind. Off by default (forward runs keep the
  faster aggregated fleet); ERCOT is unaffected (it builds from CAMPD bins).
- **Module M1: capacity-payment revenue.** `capacity.py` adds a per-ISO
  resource-adequacy payment (net-CONE × UCAP, gated on `MARKET_DESIGN`) to the
  thermal retirement and new-entry economics, so PJM/NYISO/ISO-NE/CAISO units
  are no longer over-retired on energy margin alone. Zero for energy-only ERCOT.
- **Effect on the PJM 2024 backcast:** outage overlay zeroes 233 coal/CC
  tranches (64 plants); 241 generators price from their own EIA-923 cost and
  1,119 gap-fill from nearby plants; modeled coal falls 149.4 → 140.5 TWh
  toward the ~122/116 actuals. The per-plant solve is slower (minutes, larger
  LP) — acceptable for a backcast.

## 2026-06-04 (storage daily-cycling toggle)

- **Added the `storage_daily_cycling` foresight toggle.** A new LP constraint
  family (`dispatch._build_storage_daily_cycle_rows`) optionally pins each
  storage unit's SOC back to its day-start level every 24 h, so storage cannot
  arbitrage across days — bounding the single-LP perfect-foresight advantage to
  within-day spreads (the realistic limit for short-duration storage). Off by
  default (annual-cyclic, unchanged). Exposed as `ScenarioConfig.storage_daily_cycling`
  and `run_calibration_full.py --storage-daily-cycling`; recorded in each run's
  `meta.json`/`run_config.json`. Covered by `TestStorageDailyCycling`.

## 2026-06-03 (storage backcast RTE fix + perfect-foresight docs)

- **Fixed: storage RTE override now reaches the backcast.** `load_eia860_storage`
  hard-coded round-trip efficiency from the `STORAGE_TECHS["li_ion_4hr"]`
  constant (0.86), so a calibration sweep of `config.storage_rte_4hr` (e.g. the
  0.85 in the run configs) never changed the backcast battery fleet — the lever
  was silently decoupled from the model. It now reads RTE through `_storage_rte`,
  matching the forward new-entry path; the function takes `config` and the
  calibration call site passes it. Magnitude is small (√0.86→√0.85) but the
  knob now actually binds.
- **Documented the storage perfect-foresight assumption.** The full 8760-hour
  horizon is solved as one LP, so storage is co-optimized against the whole
  year's prices (an upper bound on realized arbitrage that over-flattens net
  load). Added the limitation and the standard mitigations (daily SOC cycling
  caps, rolling/receding horizon, day-ahead+real-time, price-taker pass,
  stochastic, empirical haircut) to `model-methodology-spec.md` §storage and a
  note in `dispatch.build_constraints`. Bounded for the short-duration 2023
  fleet by the `SOC ≤ energy_cap` constraint; grows with long-duration storage.

## 2026-06-03 (storage + offer-curve docs)

- Documented the storage new-entry overhaul (PR #180): the value stack
  (duration-sized arbitrage net of cycling degradation **+** resource-adequacy
  capacity value via the per-ISO `MARKET_DESIGN` registry, net-CONE × ELCC ×
  saturation derate), tech-diversified build budget, and per-tech learning
  curves. Methodology spec §5.5 was updated in that PR; this pass aligns
  `claude.md`, the multi-ISO market-design catalogue (`MARKET_DESIGN` registry
  note), and `docs/binning-methodology.md` (smooth N-slice offer curve now
  spanning CC/coal/CT/ST, exponent p=3 — runs 25–26).
- **Parameter-citation registry back-filled — CI green.** Added
  `scripts/generate_parameter_registry.py`, which reuses the validator's exact
  `expected_param_ids()` derivation, preserves the 133 curated entries, and
  registers the 401 missing parameters with values plus citations harvested
  from each constant's inline comment. `validate_parameters.py` now exits 0.
  534 entries total; 232 auto-entries are flagged `needs-citation` (no dated
  primary source in the comment) for later human review. The human view
  `docs/parameter-citations.md` is now rendered from the registry by the same
  generator, so the two stay consistent — re-run after adding constants.

## 2026-06-03

- **Documentation reconciliation.** Realigned the prose docs with the as-built
  code after the code had outpaced them. Methodology spec, `claude.md`, the
  calibration logs and the multi-ISO baseline now reflect: the opt-in
  three-solve unit-commitment layer (still pure LP, no MIP), CAMPD per-plant
  binning with tranche-based rising offer curves (ERCOT default), config-driven
  retirement plus the CCS-retrofit pathway, forecast-vs-backcast outage
  modelling, hydro monthly energy budgets, EAC/REC attribute credits, and the
  seven registered ISO topologies (ERCOT, CAISO, PJM, MISO, SPP, NYISO, NEISO).
- Added the `/sync-docs` skill — a manually-invoked, end-of-session doc
  reconciler (deliberately not a hook) with a code→doc map.
- Roadmap noted: derive forecast-mode spring/autumn maintenance shaping from
  historic outage data (replacing the flat shoulder-POF heuristic).
- Documented the per-plant tranche-config system added across the run5–run24
  calibration series (`inputs/plant-tranche-config.csv`,
  `plant_tranche_config_path`, `cc_peaking_per_plant`,
  `fleet.load_plant_tranche_config`/`plant_tranche_bands`): an optional
  per-plant **five-slice rising offer curve** (Econ split into Low/High) that
  overrides the per-group tranche defaults for flagship-plant calibration.
  See `docs/binning-methodology.md` and methodology spec §3.3.

## 2026-05-16

- Phase 0 started.
