# PRECOMMIT — caiso-246: the 2025 hub-overlay COVERAGE GAP is a GATE ARTIFACT, not a data hole — the EIA survey is "NA" for Sep–Nov 2025 while the measured daily citygate spot the keeper prices gas at has 21 / 22 / 12 prints in those months. Arm: cover a month on its own spot prints. Pushed BEFORE the arm is coded and BEFORE any LP.

**Session caiso-246, 2026-09-04. Branch `claude/caiso-244-backcast-calibration-jag23e`
(reset onto `main` `a276e8c7`, which carries caiso-245 merged).** Keeper at open:
**`2026-09-04-caiso-243-b1-f923`** (`caiso243_b1_f923_fallback_guard`, `git_sha
b053e3b8`), **NOT-YET**, C3a the sole load-bearing FAIL **+3.9 / +12.3 /
+14.4 %** (required move +3.297 / −0.805 / −1.498 $/MWh); C1 12/12 free 8/8;
C2 / C3b / C4 PASS; C3c the single ledgered caveat; C6 attested; C8 PASS; DOF
9 / 6. No `complete` / `final` marker; holdout freeze ACTIVE; 2023–2025 only.

---

## §0 — WHAT THIS SESSION IS, AND WHAT IT ALREADY KNOWS

### §0.1 — Form (ii) of the import object is CLOSED AT PHASE A from the committed record (zero fetch)

Handoff item A asked first whether the OASIS Public Bid Data exposes intertie
ids. It does not, and the repo already says so: `data/raw/caiso-public-bids/
README.md` (*"Resource identity is MASKED … no location/fuel"*) and
`scripts/data/derive_caiso_intertie_selfsched.py`'s identification wall
(*"the masked feed carries no direction field … 1,141 of 1,452 resources
carrying 94.91 % of self-scheduled MW unclassifiable … There is no public
crosswalk: masking is the disclosure's purpose"*, caiso-150 §B, DO-NOT-REDO).
A per-intertie price-insensitive ceiling cannot be measured from that source.
**No fetch is spent on it; form (ii) is recorded closed** (FINDING §1). The
firm block's energy basis stays an owner object with forms (iv) and the two
fitted prices (caiso-245 §6) — none touched here.

### §0.2 — The object taken instead: queue item C, and what the source actually says

The keeper prices every CAISO gas unit at the **measured daily CA-composite
citygate spot** in every covered month (`caiso_citygate_spot_level`, caiso-84,
rule 15: the spot is the marginal cost-based DEB's index). A month is
"covered" only where the EIA **N3050CA3 monthly survey** has a basis row
(`gas_basis_by_iso_month.csv`) — and in 2025 that file has Jan–Aug and Dec:
**9/12**. In the three uncovered months the F923 plant layer shows through
(caiso-242 §5, caiso-243's object, D3's 55077 row, the autumn-2025 slab).

**Measured this session, from the source itself (data prep, unrestricted):**

* EIA's published N3050CA3 series (`https://www.eia.gov/dnav/ng/hist/n3050ca3m.htm`
  and its `hist_xls/N3050CA3m.xls`, fetched 2026-09-04, HTTP 200): **2025-09,
  2025-10, 2025-11 = "NA"** (also 2026-04). The survey has no value; **the
  gap is EIA's, not the fetch's.** The fetcher cannot produce the rows.
* The committed daily spot `data/raw/gas-prices/caiso_citygate_daily.csv` HAS
  prints in those months: **Sep 21, Oct 22, Nov 12** (monthly means of the
  prints 3.24 / 2.87 / 3.20 $/MMBtu; Henry Hub monthly 2.97 / 3.20 / 3.79).
* `hubs.py::_caiso_hub_daily_gas_prices` documents the gate explicitly:
  *"Coverage is the SAME month-set as the default path — a month reprices only
  where the survey basis row exists — so spot_level is a pure LEVEL swap …
  never a coverage expansion (… CAISO 2025 Sep-Nov with no basis row, stay on
  the base EIA-923 series)."* Under `spot_level` the survey VALUE is not used
  in any month that has prints — the level and shape come entirely from the
  daily series. **The survey row is a gate and nothing else.**

So the design the keeper carries — marginal gas at the measured daily spot —
is fully identified for Sep–Nov 2025 by data already committed, and only a
gate keyed to a DIFFERENT series (one EIA chose not to publish) keeps those
months on the F923 fallback.

**Also seen before this push (disclosed):** caiso-243's footprint of the
fallback months (1,364 CA rows / 25,527 MW re-tiered onto the ~4.38 $/MMBtu
state mean in Nov; Sep ~4.2, Oct ~4.4 after the state stamp) and the
December-2025 model−actual RT slab (+9.2; caiso-245 §3). **No model quantity
for the arm has been computed.**

### §0.3 — The mechanism (to be coded after this push)

`ScenarioConfig.caiso_citygate_spot_coverage: bool = False` (CAISO-only,
backcast-only by construction like `caiso_citygate_spot_level`, default off;
requires `caiso_citygate_spot_level`). In `_caiso_hub_daily_gas_prices`, a
month is covered if it has a survey basis row **or** — under this flag — it
has measured daily prints of its own; in the second case the day series is
built exactly as in every other covered month under `spot_level` (flow-date
staircase or calendar interpolation of the prints; the +0.46
`CAISO_CITYGATE_TRANSPORT_ADDER` is layered by `apply_hub_basis_overlay` as
today). Months with neither stay uncovered. **Zero new numbers, zero free
parameters** (rule 21): the flag admits an already-committed measured series
into months it was excluded from by a gate. Rule 14: measured daily spot over
the F923 gap-fill estimate. Rule 19: ONE mechanism (the overlay) reaching the
months it was designed for — nothing stacked. Forward story unchanged: the
overlay is backcast-only; forecast years keep the HH-forward path.

### §0.4 — Admissibility, stated against interest

The daily spot is an NGI index displayed by EIA (`docs/data-licensing.md` §5,
flagged for owner review) — the SAME series the keeper already uses in 33 of
36 months; this arm changes its reach, not its standing. The three months have
fewer prints than a full month (12 in November) — the interpolation between
prints is the same construction the other 33 months use on their non-trading
days, and the print counts are reported.

### §0.5 — HARD STOPS

Training window only; one bundle, three years, sequential; no second CAISO
solve concurrently. No `calibration-complete.json` / `holdout-freeze.json` /
other-ISO shard or bundle touched. No change to the survey rows, to the
transport adder, to the F923 fallback (D1/D2 CLOSED), to the spot-level
mechanism itself or to any offer band. The import objects are untouched.

### §0.6 — THE HAZARD

The spot means (3.24 / 2.87 / 3.20 + 0.46) sit **below** the F923 state-mean
fallback (~4.2 / 4.4 / 4.38) in all three months, so ~25 GW of CA gas is
repriced DOWN for Sep–Nov 2025 and C3a-2025 moves **DOWN — the FIFTH
consecutive favourable direction in this lane.** Stated now; never an
argument. C3a's verdict is EXCLUDED from the promotion basis (§5). It also
closes D3 (55077's own 96.161 $/MMBtu November row is overwritten by the
overlay), which is reported as a consequence, not a purpose.

### §0.7 — DO-NOT-REDO acknowledged

caiso-245 §7, caiso-244 §7, caiso-243 §10 (D1/D2 CLOSED; form (b) refused;
the fallback guard is not a lever; never rebuild a recipe by name), caiso-242
§9, caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9 — read, none
re-opened. The transport adder (caiso-244 ask E) is NOT touched.

---

## §1 — GATES

* **G-SOURCE:** the EIA NA cells are committed as evidence
  (`data/raw/gas-prices/eia_citygate_CA_monthly.csv`, parsed from the fetched
  xls) so the "gate artifact" claim reproduces from committed bytes.
* **G-STRUCT (pre-solve, zero LP):** the on-recipe rebuild with the flag ON
  differs from the keeper rebuild in **gas rows × Sep–Nov-2025 hours ONLY**:
  0 non-gas rows, 0 rows in any other month, **0 rows in 2023 and 2024**
  (12/12 covered); every gas row's Sep–Nov price equals the overlay's own
  construction (daily spot + 0.46) — including plant 55077's November row.
* **G-CTRL, form 2** (owner's caiso-241 §B2 carve-out — an arm with a
  measured-inert year spends no control): 2023 and 2024 must reproduce the
  keeper at **0.000 TWh in every class and 0.000 $/MWh** (caiso-243's
  standard, met exactly there). FALSIFIER: any inert-year class moving ⇒ a
  control (form 3) before any claim.
* **G-INERT:** 2025 moves.
* **G-C1 / G-C3b / G-C8 / G-CAVEAT / G-C6:** C1 ≥ 12/12 free 8/8; no scored
  verdict regresses; ≤ 1 ledgered / 0 protective; C6 attested.
* **G-C3a, envelope leg:** the caiso-243 price-leg envelope
  (`_caiso243_price_envelope.py` machinery: assembled `mc_base` offers vs the
  keeper's own zonal prices × demand, lower limb = every live-month zone-hour
  where the keeper price exceeds the cheapest repriced tranche's new offer
  falls to it; upper limb = the largest positive offer move) computed on the
  arm's fuel array before the solve and registered in the FINDING as
  **[L, U]**; ΔC3a-2025 must land inside it, ΔC3a-2023/2024 exactly 0.
  Outside ⇒ estimator defect, reported, never re-fitted. The VERDICT leg is
  excluded.

---

## §2 — PREDICTIONS (uncomfortable ones marked)

| # | prediction | falsified by |
|---|---|---|
| P-1 | G-STRUCT exact: every gas row and only gas rows, Sep–Nov 2025 only; 0 rows 2023/2024 | any other cell moving |
| P-2 | Nov-2025 capacity-weighted CA gas price falls from ~4.38 to **3.5–3.8 $/MMBtu**; 55077's November row from 96.16 to the same band (D3 closed by consequence) | outside the band |
| **P-3** | ΔC3a-2025 ∈ **[−1.0, −0.2] $/MWh** — the arm does NOT close C3a-2025 (required −1.498) and delivers less than two-thirds of it; **no verdict flips** (2023 PASS, 2024 FAIL, 2025 FAIL) | < −1.0, > −0.2, or a flip |
| P-4 | ΔC3a-2023 = ΔC3a-2024 = 0.000 exactly (form 2) | any move |
| **P-5** | CC_REGULAR-2025 rises by **0.3–1.0 TWh**, imports fall by **more than** CC_REGULAR rises (the caiso-243 displacement repeats), CT_PEAKER-2025 falls | imports falling less than CC rises, or CT_PEAKER rising |
| **P-6** | the model−actual RT slab shrinks in Sep/Oct/Nov 2025 by ≥ 1.0 $/MWh each but **December does not move by more than 0.3** (December was already covered; the December slab is not this object) | Dec moves > 0.3, or any of Sep–Nov < 1.0 |
| P-7 | C3c-2025 stays PASS at 0 h > $200; C1 12/12 free 8/8; C8 PASS; DOF ledger unchanged (9 / 6) | any change |
| **P-8** | the import-marginal share (caiso-244 §3.6; 23.0 % in 2025) rises by ≥ 1 point in 2025 (cheaper domestic gas pushes more hours to the hub margin) | change < +1 point |

---

## §3 — WHAT THIS DOES NOT DO

It does not touch the north-corridor firm floor (the import LEVEL object),
the CT_PEAKER volume miss, the flatness object, or the transport adder; it
does not extend coverage to a month with no prints; and it does not change
2023 or 2024 at all.

---

## §4 — THE PROMOTION RULE, FIXED NOW

Promote **iff** G-SOURCE, G-STRUCT, G-CTRL (form 2), G-INERT, G-C1, G-C3b,
G-C8, G-CAVEAT, G-C6 and the envelope leg of G-C3a all pass. **The basis is
structural:** the keeper's own designed mechanism — marginal gas at the
measured daily spot — reaches the three months a survey gate keyed to a series
EIA did not publish had withheld from it, at zero free parameters, retiring
the F923 fallback from the training window entirely (0 reachable months in
36) and D3 with it. C3a's verdict is reported and excluded. If a scored gate
regresses while structure improves, the regression is reported at full size
and the promotion is put to the owner rather than taken.

---

## §5 — OWNER ASKS ANTICIPATED

1. Whether the EIA NA months should also be back-filled in
   `gas_basis_by_iso_month.csv` for the OTHER ISOs' lanes if their surveys
   carry NA (not measured here; rule 25).
2. The transport adder on a spot-indexed offer (caiso-244 ask E) — unchanged.
3. Everything caiso-245 §8 carried.
