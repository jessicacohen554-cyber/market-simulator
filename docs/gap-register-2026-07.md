# Gap register (2026-07)

The 2026-07 calibration cycle's gaps are tracked across the lane/prompt file
(`docs/gap-register-2026-07-prompts.md`) and the per-gap handoffs under
`docs/handoffs/`. This file carries two things: the **G-19** section below,
the owner-designated home for the cross-ISO holdout data-equivalency gate
status; and **§3**, newly-opened gap-register rows for structural/
forecast-validation and capacity-accreditation findings whose own source
docs flagged them as needing one.

## G-19 - Cross-ISO holdout data-equivalency gap register (GATE)

**Owner order (2026-07-07):** no holdout solve, no holdout score, and no holdout
result may be recorded for ANY ISO until a series-by-series register confirms
each holdout year's input coverage (drivers, fleet/overlays, bench actuals, and
their granularity/vintage) matches the keeper years', **and the owner signs off
per ISO**. The NEISO one-shot execution is HELD on exactly this
(`docs/handoffs/neiso-calibration-complete-memo-2026-07.md` §6; the memo's
§4/§5 execution + irreversibility terms apply whenever the gate clears).

**Status (2026-07-12): register CREATED - `docs/holdout-data-equivalency-register-2026-07.md`.**

- **NEISO 2018-2022 readiness DONE, register §NEISO complete** (2026-07-13
  lane, extending the 2026-07-12 2022-only readiness). Owner authorization
  (verbatim, `calibration-complete.json` intake_log): *"This data can
  literally be collected for all years — we're not running anything on it.
  Fetch it all at once for 2018-2022 and first half 2026 if available."* The
  2026-07-12 landing residuals (§NYISO N5: no NEISO 2022 in `actual_lmp*`/
  tail, no `NEISO_2022_renewable_capacity.csv`, this file a placeholder stub)
  are now CLOSED, and readiness extended back to 2018 where source data
  permits (`scripts/land_neiso_2022_readiness.py` +
  `scripts/land_neiso_holdout_multiyear.py`). Full audit:
  `docs/holdout-data-equivalency-register-2026-07.md` §NEISO. Verdict tally
  for the 2018-2022 window: **EQUIVALENT 12 / DEGRADED 8 / MISSING 6 (zero
  unresolved — every MISSING row carries an explicit fix or acceptance)**.
  - **DEGRADED**: outage-window detector vintage (all appended years, same
    class as the original 2022 finding); daily Algonquin gas (still
    2023-2025-only — monthly basis covers every year as the accepted
    fallback); fleet statics + dual-fuel switch roster + winter-fuel-security
    figures (static, accepted); parasitic load factors + fossil CO2 rates
    2018-2021 (pooled-fallback / v2-superseded, accepted).
  - **MISSING**: driver-demand model profile (`eia_demand_profiles.parquet`)
    2018-2020 — **HIGH**, blocks dispatch outright, same F3/F4 class as the
    ERCOT/PJM doc, not fixed in this data-only lane; `calibration_reference`
    2018-2020 (same root cause); ISO-NE SMD LMP bench 2018-2019 (no workbook
    on disk, hand-obtained artifact class); `actual_tail.json` 2018-2021
    (deriver's `HOLDOUT_YEARS` constant is shared cross-ISO, not hand-edited
    here); plant emission rates v1 (accepted-structural, same as NYISO);
    NEISO-AS measured hourly reserve requirements (unchanged from
    2026-07-12 finding, non-keeper limb).
  - **H1-2026**: BLOCKED (publication horizon - CAMPD Q2-2026, delivered gas
    May-2026+, F3 demand profiles, F4 reference-year registration). Locked test
    (rule 22, touch-once); executes later under the same marker.
- **ERCOT / PJM** (2022 intake landed 2026-07-04, out-of-sample §1.1):
  equivalency audit PENDING (their own lane).
- **CAISO / MISO**: no holdout intake - register rows start MISSING.
- **NYISO**: register **§NYISO DONE** (its own lane, merged to main) -
  EQUIVALENT 24 / DEGRADED 4 / MISSING 5 for the 2022 window (2026-07-12 intake);
  owner sign-off + a `complete.NYISO` marker still pending per its section.

**Exit:** owner sign-off per ISO. For NEISO, the sign-off decision also carries
two surfaced items (register "Exit criterion"): the keeper-identity
reconciliation (one-shot marker names neiso-54; dashboard keeper is neiso-56 -
audited input files are invariant across them) and the outage-window vintage
choice (reconstruct-committed vs pinned-vintage-re-derive). Separately, an
in-sample keeper-repro drift on main (+0.22/+0.38/+0.68 $/MWh, dual-fuel tranche
drift after `7f968f3`) stays in its own NEISO/main lane. Until owner sign-off,
the one-shot stays HELD.

## 3. Gap register — forecast entry/exit & accreditation-basis rows (2026-07-14)

*Continues the "§3 Gap register" numbering from the 2026-07-05/07 comprehensive
audit (subsections 3.1 Governance & CI, 3.2 Keeper integrity, 3.3 Holdout
quarantine, 3.4 Structural/mechanism, 3.5 Forecast-side validation, 3.6
External usability, 3.7 Docs-vs-code drift, 3.8 UNVERIFIED items). That content
is preserved in git history (`02304be`) but is no longer carried in this file,
which was narrowed to the G-19 gate above. The two subsections below are
newly-opened rows for items their own source docs flagged as "needs a
gap-register row" / "no dedicated gap row — should get one" — not a
restoration of 3.1–3.8.*

### 3.9 Forecast-side entry/exit structural gaps (goal B)

| ID | Gap | Evidence / cross-refs | Severity | Effort | Owner / lane |
|---|---|---|---|---|---|
| BLK-8 | Solar new-entry = **0 GW** in BOTH the ERCOT and PJM realized hindcasts, against **25.1 GW** (ERCOT) / **13.1 GW** (PJM) actual — the single largest capacity-addition miss in either ISO's hindcast. Root cause is undiagnosed: the entry-economics stack's cost/queue/negative-price interaction has not been decomposed to isolate why the economic new-entry screen never clears a solar build, in either ISO, across all three hindcast years. | `docs/forecasting-entry-exit-assessment.md` §5 (BLK-8 row; verdict rows 6, 10, 14); `docs/hindcast-reports/ercot-2021-2025-realized-p2c-2026-07-12.md:32` (solar 25.08→0.0 GW, −100%); `docs/hindcast-reports/pjm-2021-2025-realized-2026-07-07.md:32` (solar 13.066→0.0 GW, −100%); adjacent to the G-30/G-31 ERCOT retirement-side diagnosis (same hindcast lane, `docs/hindcast-reports/ercot-g30-entry-lookahead-2026-07-08.md`) | blocks-claim | SH — re-diagnosis needs the entry-economics stack decomposed (cost curve vs. interconnection-queue proxy vs. negative-price treatment), most likely via targeted hindcast re-solves | Forecast-validation lane (ERCOT + PJM hindcast harness); unowned — no session currently assigned |
| BLK-9 | Fixed capacity payment clears **1.26×–4.92×** of FOM-only going-forward cost for every fossil/CCS class in every capacity-market ISO (PJM/NYISO/NEISO/MISO/CAISO) — MISO coal (1.26×) is closest to the 1.0× cliff; the assessment's headline rounds this "≥1.3× for all fossil classes." Consequence: fossil economic retirement is **arithmetically impossible** (the energy-margin term can never be the binding constraint), while nuclear is the *only* class below 1.0× (0.60×–0.82×) — inverting the retirement signal onto the one class the flat payment doesn't carry (PJM hindcast: model retires 4.1 GW nuclear, 100% false, vs. actual nuclear retirements of zero; real coal/gas_ct recall both 0%). | `docs/handoffs/capacity-revenue-fom-ratio-2026-07-13.md` (PR #2160, cross-ISO ratio table §3, answers P-3B §8.3 — pure arithmetic check, no LP solve); `docs/handoffs/equilibrium-battery-2026-07-12.md` §6 item 3 (origin hypothesis: NEISO 0 MW thermal retired / 25 yr); `docs/forecasting-entry-exit-assessment.md` §2 (verdict rows 7, 8, 11, 14). **Resolution is the CR (capacity-revenue) accreditation chain — BLK-3 + BLK-4 — never a payment haircut**: a tuned cut to `net_cone_per_kw_yr` or an ad hoc multiplier would force the ratio down with no published basis, which rule 13 forbids precisely because it has no forward analogue. | blocks-claim | S (arithmetic diagnosis — done, no LP) → SH (full closure rides BLK-3/BLK-4's accreditation-basis migration, then a `capacity_market_clearing=True` re-validation needing a full-horizon P-3A re-run per ISO) | Capacity-revenue / accreditation-basis lane (P-2B); resolution owned jointly with BLK-3/BLK-4, not a standalone fix |

### 3.10 Capacity accreditation pairing audits (goal B)

| ID | Gap | Evidence / cross-refs | Severity | Effort | Owner / lane |
|---|---|---|---|---|---|
| R5a | **NYISO ICAP/UCAP pairing audit.** NYISO's published IRM (24.4%) is stated on an **ICAP** basis, but the registry carries **no ICAP→UCAP ratio** for NYISO (unlike PJM's FPR/(1+IRM) or MISO's (1+PRM_UCAP)/(1+PRM_ICAP) conversions) — so today's pairing tests an ICAP-stated requirement against the model's UCAP-counted supply ledger ((1−EFORd), which otherwise already matches NYISO's own UCAP construction — the requirement is the broken half). Same basis-mismatch error class as the PJM #1532 flag, but in the **opposite direction**: position understated ~5–7%, over-pays. Blocks NYISO curve eligibility (anchor 50.55 $/kW-yr, published ARV) until the published IRM→UCAP translation is intaken — no touching the pairing without that citation (rule 13). | `docs/handoffs/accreditation-basis-memo-2026-07-12.md` §2(a) table (NYISO row), §4.3 item R5, §6 Option A (recommended); parent issue #1532; resolution shares BLK-3/BLK-4's chain | blocks-claim | M — published-parameter filing search + citation, no LP (same discipline as the PJM R1–R4 steps) | P-2B accreditation-basis lane; unassigned — P-2A separately already blocks NYISO on curve vintage |
| R5b | **NEISO qualified-capacity pairing audit.** NEISO's requirement is stated on a **Net ICR** basis against **qualified capacity** (≈ seasonal claimed capability with **no EFORd derate** — ISO-NE prices outage/availability risk separately, through Pay-for-Performance) — a third accreditation convention distinct from PJM's ELCC-class and MISO/NYISO's EFORd-flavored bases. The model's B2 supply ledger ((1−EFORd) thermal) likely **under-counts** relative to ISO-NE's own qualified-capacity ledger, since it derates for an outage risk that FCA's PFP construct already prices elsewhere. Needs the FCA qualified-capacity definition intaken and reconciled against the model's ledger before NEISO's curve (anchor 108.94 $/kW-yr, published FCA18) is curve-eligible. | `docs/handoffs/accreditation-basis-memo-2026-07-12.md` §2(a) table (NEISO row), §4.3 item R5, §6 Option A (recommended); parent issue #1532; resolution shares BLK-3/BLK-4's chain | blocks-claim | M — FCA qualified-capacity filing search + citation, no LP | P-2B accreditation-basis lane; unassigned |
