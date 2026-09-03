# PRECOMMIT — caiso-242: the CT_PEAKER residual is a GAS-BASIS IDENTITY defect in the measured offer surface

**Session caiso-242, 2026-09-03. Branch `claude/caiso-ct-peaker-backcast-3ma46i`.**
Parent object: `FINDING-caiso241-ct-peaker-committed-2026-09-03.md` §7 — the
`CT_PEAKER` volume miss SURVIVES the committed-band grounding at
**−2.502 / −3.582 / −1.961 TWh** (the class runs at **39.4 / 17.2 / 16.2 %** of
its plant-level actual), and its dominant cause is *"the econ/peak bands,
availability, or a structural absence — a separate, larger, unfunded object."*

CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**; every read below and any solve stays inside **2023–2025**.

Keeper at open: **`2026-09-03-caiso-241-b1-ctpeaker`**
(`results/calibration/caiso241_b1_ctpeaker_committed`, `git_sha 607f9324`),
**NOT-YET**, one load-bearing FAIL — C3a **+3.9 / +12.3 / +15.5 %** (2023 PASSES),
C3c the single ledgered caveat, C1 12/12 free 8/8, `audit_keepers --iso CAISO`
PASS 0/0.

---

## §0 — WHAT THIS SESSION IS, AND THE DISCLOSURES THAT CONDITION IT

### §0.1 — THE FIRST DELIVERABLE IS A DIAGNOSIS, AND IT IS NOT THE ONE THE CHARTER EXPECTED

The caiso-242 charter named three candidate routes and instructed that the
choice be made *"on measurement not intuition"*: (a) the econ/peak bands and a
suspected margin-mechanism inversion, (b) availability, (c) something else
serving the evening ramp. **Measurement returns (a) — but not the (a) the
charter described, and it subsumes (c).** The charter's suspected inversion is
real, is measured below, and is **immaterial** (623 MW, 8.3 % of the class).
What binds is one level below it: **the armed measured multipliers are
normalised on a DIFFERENT gas series than the one the solve prices their
tranches at**, so every CAISO gas offer built from the measured OASIS surface is
inflated by the ratio of the two series — **1.298 / 1.310 / 1.327** on the
carbon-inclusive basis the derive itself uses, i.e. **+$26.55 / +$17.22 /
+$18.95 per MWh** on `CT_PEAKER`'s `econ_low` band alone.

For scale: the caiso-241 repair moved **−$18.62/MWh on 11.0 %** of the class.
This is **+$17–27/MWh on 100 %** of it — and on every other CAISO gas class's
measured bands too.

### §0.2 — FULL DISCLOSURE: EVERYTHING READ **AND MEASURED** BEFORE THIS FILE WAS PUSHED

Following caiso-238 §0.6 / caiso-239 §0.2 / caiso-240 §0.3 / caiso-241 §0.2, and
stated first because it conditions what §4 can honestly pre-register.
**This session's diagnostic phase came BEFORE this push** — the charter required
it (*"Start by measuring which, from committed artifacts, before proposing any
lever"*) — so unlike caiso-241 this file is **not** written against unmeasured
quantities, and every number already measured is reproduced here rather than
registered as a prediction. §4's predictions are confined to quantities that are
still unmeasured: the arm's footprint, the bound, and every solve outcome.

**Read:** `pipeline/backcast_config.py`; `data/offer_curves.py`
(`gas_offer_margin_markup_mult`, `apply_gas_offer_margin`, `band_margin_anchor`);
`data/fuel/hubs.py` (`apply_hub_basis_overlay`, `_caiso_citygate_daily_dated`);
`config/constants.py` (`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`,
`GAS_TRANCHE_SHARES_BY_GROUP`, the two `ST_GAS_*_MEASURED_*` registries);
`config/fuel_trajectories.py` (`GAS_BASIS_DIFFERENTIAL`,
`CAISO_CITYGATE_TRANSPORT_ADDER`); `scripts/data/derive_caiso_offer_surface.py`
(docstring **and** the `denom`/`mult` construction at its static-band stage);
`scripts/run_calibration_full.py::_write_class_band_hourly_sidecar`;
`data/fleet/__init__.py::FleetArrays`. **Committed artifacts:** the keeper's
`meta.json` / `run_config.json` / `metrics.json` / `legitimacy_diagnostics.json`
and all twelve `hourly/` sidecars; `frontend/data/backcast/bench/CAISO/*.json.gz`;
`frontend/data/backcast/keepers/CAISO.json`;
`docs/codebase-site/data/mechanism-matrix/CAISO.js`;
`data/raw/reference/caiso_campd_marginal_hr_summary.csv`;
`data/raw/_validation-source/caiso_offer_curve_measured.json`;
`data/raw/gas-prices/caiso_citygate_daily.csv`; the caiso-238/239/240/241
precommits, addenda, assessments and findings; the caiso.md tail.

**Measured before this push (three probes, ZERO LP, NOTHING ARMED, no flag
delta — each rebuilds the keeper's own recipe with `run_year(fleet_only=True)`):**

| probe | artifact |
|---|---|
| `scripts/probes/_caiso242_ctpeaker_anatomy.py` | `_caiso242_ctpeaker_anatomy.json` |
| `scripts/probes/_caiso242_passthrough_test.py` | `_caiso242_passthrough_test.json` |
| `scripts/probes/_caiso242_gas_basis_identity.py` | `_caiso242_gas_basis_identity.json` |

**NO FLEET HAS BEEN REBUILT WITH ANY ARM, NO FOOTPRINT DIFFED, NO BOUND
EVALUATED, NO LP RUN.** The arm's G-STRUCT footprint and the §3 bound are
computed after this push and registered in an **ADDENDUM pushed before any
solve** — the caiso-240/241 two-file pattern, kept.

### §0.3 — HARD STOPS

Training window only (2023 / 2024 / 2025); if a solve happens, all three years in
**one invocation and one bundle** (rule 16 `[R-ALLYEARS]`), **sequential**
(rule 12 `[R-PARALLEL]`), and **never two CAISO solves concurrently** (each
3-year LP holds ~6.5 GB; two OOM-killed this container at caiso-241). No
`calibration-complete.json`, no `holdout-freeze.json`, no other ISO's keeper
shard or matrix shard touched. **No mechanism armed outside CAISO** (rule 25
`[R-ISO-SCOPE]`) — §1.6 establishes that the same identity question exists for
every ISO carrying a measured offer surface, and that is an **ASK for those
lanes, never an arm here, and never a value transfer in either direction.** No
P2. No off-registry knob (rule 24). No derive script re-run against a residual
(rule 23 `[R-FROZEN-DERIVE]`).

### §0.4 — DO-NOT-REDO ACKNOWLEDGED (rule 28(a))

Re-read in full: caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9, and
the `CAISO.js` cells for `measured_offer_surface`, `offer_curve_by_group`,
`gas_offer_net_revenue_margin` and `cc_committed_offer_margin`. Not re-opened,
not re-proposed, and not offered as a C3a instrument anywhere below:

1. **`CT_PEAKER.committed` is CLOSED** (caiso-241 §10.1). It is grounded at
   `phys_committed` and is not touched by this session's arm in either
   direction. §2.4 reports, **against interest**, a cost of that repair which
   this session's measurement surfaces for the first time — as an observation on
   the record, **not** as a re-litigation and **not** as a proposal to move it.
2. **The measured BID committed multipliers (CC 1.030 / CT 1.166) are NOT
   armed** for any CAISO gas class. The Lever-A refusal stands uniformly on the
   bid route. This session touches no `committed` band.
3. **caiso-229's "the marginal rung over-propagates fuel" hypothesis is REFUTED
   and is NOT re-opened.** §1.5 states precisely why this object is a different
   one — caiso-229 measured a *coupling slope* and found the model
   **UNDER**-coupled; this session measures a *denominator identity* and finds a
   **LEVEL** inflation. Both can be true simultaneously and the second does not
   revive the first.
4. **caiso-230's offer-side sign kill is NOT re-opened.** It adjudicated
   *raising* un-grounded class multipliers onto measured bucket values
   (+0.553 / +0.700 / +0.709 $/MWh, wrong sign). This session changes no band's
   **relative** grounding; it corrects the **denominator** of bands already
   measured and already armed, and moves in the opposite direction. §1.4.
5. **EIA-930's CISO NG cell is never a CAISO gas benchmark** (caiso-240 §7.1).
   Every volume number below is against the plant-level EIA-923 / CAMPD pair.
6. **Nothing transfers to another ISO** (rule 25): no `phys_*`, no multiplier, no
   basis ratio. `_DEFAULT_HR_MULT_BY_GROUP` is not re-censused; the five gas `mr`
   literals are not re-proposed; `ST_GAS:econ` is not armed by picking a ramp
   endpoint; `ST_GAS_PEAKER_PLANTS`'s offer scope is not split as posed. The
   caiso-229/230/233/234/235/224/221 closure list stands; the W-1/W-2/W-3 sweep
   is DATED (≤ 2026-12-01) and not swept here.

### §0.5 — TWO INHERITED INSTRUMENT DEFECTS, ADOPTED, NOT RE-DISCOVERED

1. **NEITHER §H NOR §H′ IS A BOUND ON VOLUME.** caiso-240 falsified §H as a
   strict upper bound (2024 under-predicted 4.5×); caiso-241's crossing envelope
   §H′ passed its **price** leg with margin (the measured move was 9 % of the
   ceiling) and **BREACHED** its **volume** leg in 2024 (+2.4 %) and 2025
   (+23.1 %), because it counts only hours where the tranche crosses the
   *control's* price and is blind to hours that re-dispatch itself opens.
   **§3 therefore quotes the price leg as a two-sided envelope and the volume
   leg as an ORDER-OF-MAGNITUDE INDICATION ONLY, declared as such in advance,
   with no falsifier attached to it** (§3.3). This arm is even deeper in §H′'s
   anti-conservative regime than caiso-241's was — it reprices 82 % of a class
   that is 83–90 % absent — so pretending otherwise would be dishonest.
2. **THE DOF LEDGER CANNOT SEE A FITTED→MEASURED SUBSTITUTION.**
   `build_dof_ledger._count_scalars` counts numeric **leaves**, so a repair that
   changes a value without removing a key is invisible to it. Four consecutive
   grounding repairs (caiso-239, -240, -241 twice) did not move it.
   **P-7 below therefore predicts it does NOT move, and no claim of DOF progress
   is made from the counter.** The standing owner ask (a per-leaf
   `fitted`/`measured` provenance count) is re-filed unchanged, not re-derived.

### §0.6 — THE DIRECTION IS FAVOURABLE TO THE SOLE FAILING GATE, AND IT MAY OVERSHOOT IT. BOTH ARE DISCLOSURES, NEITHER IS AN ARGUMENT.

Renormalising CAISO's measured gas offers onto their own identification basis
**lowers** them, which (a) raises CT_PEAKER volume — a C1 improvement on a class
missing by 61–84 % — and (b) pushes C3a **DOWN** in hours it is over (required
move **0.00 / −0.848 / −1.893 $/MWh**). Per rule 1 `[R-STRUCT]` **that is not an
argument for the repair, and this object must never be re-proposed as a C3a
lever.**

**And the disclosure has a second half that cuts the other way, stated before
any solve:** this arm is far larger than caiso-241's and its price effect may
**overshoot** — 2023 currently PASSES C3a at **+3.9 %** with a required move of
**0.00**, so a large downward move can turn a passing year into a low-side
FAIL, and 2024/2025 can overshoot past zero. **That is a registered falsifier
(G-C3a, §5.6), not an excuse**, and P-4 is written to be uncomfortable about it.

---

## §1 — THE RULING: THIS IS A DIMENSIONAL IDENTITY DEFECT, AND IT IS OUTSIDE EVERY CLOSED CELL

### §1.1 — The measured multiplier's denominator, from the derive's own code

`scripts/data/derive_caiso_offer_surface.py`, static-band stage, **verbatim**:

```python
bids["day"]  = bids.interval_start_utc.dt.tz_convert("US/Pacific")...
bids["gas"]  = bids.day.map(gas)          # gas = _gas_staircase()
bp["denom"]  = base_hr * (bp.gas + CO2_FACTOR * bp.year.map(carbon))
bp["mult"]   = (bp.p - vom) / bp.denom
```

and `_gas_staircase()` reads **`data/raw/gas-prices/caiso_citygate_daily.csv`,
column `ca_composite_usd_mmbtu`** — the CA-composite citygate daily spot on
trade+1 flow days. The artifact's own `_provenance.gas_basis` says the same
thing. **So every armed CAISO band multiplier is, by construction, a ratio whose
denominator is the CA-composite citygate spot.**

### §1.2 — The series the solve prices those tranches at, from the model's own code

`data/fuel/hubs.py::apply_hub_basis_overlay` reprices every CAISO gas generator
at the **EIA N3050CA3 monthly citygate** level (`gas_basis_by_iso_month.csv`)
**plus `CAISO_CITYGATE_TRANSPORT_ADDER = 0.46`**, shaped within the month.
Its own comment: *"a CA power plant pays the citygate PLUS the LDC intrastate
backbone/transmission to its burner tip … Without it the pure citygate
under-prices the marginal CC to ~the import price and collapses the import
knife-edge (the discovered caiso-38 under-import)."*

**That reasoning is correct for a COST and is not disputed here.** The defect is
that the same series is then used as the denominator's replacement in an
**OFFER** built from a multiplier measured against a different denominator.

### §1.3 — The measurement (`_caiso242_gas_basis_identity.json`, zero LP)

Cap-weighted over the keeper's own CT_PEAKER tranches, month-matched:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| model delivered gas ($/MMBtu) | 7.4178 | 3.8416 | 4.5829 |
| derive denominator, CA-composite citygate | 5.2831 | 2.4567 | 3.0593 |
| **difference** | **+2.1347** | **+1.3849** | **+1.5236** |
| ratio, fuel only | 1.4041 | 1.5637 | 1.4980 |
| **ratio, carbon-inclusive (the derive's own denominator)** | **1.298** | **1.310** | **1.327** |
| monthly ratio median / min / max | 1.461 / 0.749 / 1.816 | 1.636 / 0.949 / 2.500 | 1.467 / 1.128 / 1.898 |

**In $/MWh on `CT_PEAKER.econ_low` (`mult` 1.145 × `base_hr` 10.862 × Δgas):
+26.55 / +17.22 / +18.95.**

Reconstructed end to end for 2024 at the class base heat rate: the **measured
OASIS bid** is `VOM 3.5 + 1.158 × 10.862 × (2.4567 + 0.057 × 35.23)` =
**$59.65/MWh**; the **model's offer for the same band** is **$81.07/MWh**.
**The model offers CAISO's CT economic band ≈ 36 % above the bid CAISO's own
public record shows.** The keeper's assembled `econc00` capacity-weighted mc is
**74.49** (2024), consistent once the per-plant heat-rate mix and the margin
reform are carried.

### §1.4 — Why this is OUTSIDE caiso-230's sign kill, and outside caiso-238's F4

caiso-230 adjudicated **re-grounding un-measured class bands onto measured
bucket values** — a change in *which* multiplier a band carries — and killed it
on sign (+0.553/+0.700/+0.709 $/MWh, the wrong direction). caiso-238 graded the
five **`committed`** bands F4 on the Lever-A refusal.

**This object changes no band's grounding and no `committed` band.** It leaves
every armed multiplier's *identity* untouched and corrects the *denominator it
is evaluated against*, which is a units property of the estimator, not a choice
of value. Its sign is therefore the opposite of caiso-230's by construction, and
it cannot be reached by any move caiso-230 or caiso-238 considered.

**And caiso-230 itself flagged the general shape of this defect, one level
away** — its own rule-14 misalignment caveat, on the record before this session:
*"the measured multiplier is defined against its BUCKET base HR 7.442/10.862
while CC_CHP is 6.90 and ST_GAS ~11.85, so a naive transplant does not round-trip
to the measured bid level."* That is the same failure mode — a measured ratio
applied against a different normaliser than the one it was measured against —
diagnosed for the *heat-rate* leg of the denominator. **This session finds it in
the *gas-price* leg of the same denominator, where it is larger and affects the
bands that were correctly transplanted, not only the naive ones.**

### §1.5 — Why this does NOT re-open caiso-229 (which is REFUTED and stays refuted)

caiso-229's refuted hypothesis was *"the marginal rung over-propagates fuel"*,
and it was killed by a **slope** measurement: the model CC floor couples to the
CA citygate at Theil-Sen **2.18–4.34 MMBtu/MWh** against CAISO's measured DAM
body coupling of **6.7–7.4**, i.e. the model is **UNDER**-coupled.

**This session makes no claim about slope, and does not contradict that.**
A series that is *shifted up* relative to another can simultaneously be *less
responsive* to it — indeed that is exactly what an EIA monthly contract-weighted
citygate + a flat $0.46 tariff adder is, relative to a daily spot index. The two
findings compose: the model's CAISO gas offer is **too high in level** and
**too flat in slope** against the index the market's own bids are written on.
The cell `gas_offer_net_revenue_margin` stays `K`; nothing about it is re-tested
here.

Independent corroboration already committed, found **after** the measurement and
labelled as such: the derive's own classifier reports, for the CT bucket, a
Theil–Sen slope of **9.2–10.4 MMBtu/MWh against the CA-composite citygate**
(0.85–0.96 × `base_hr` 10.862) with an implied non-fuel adder of **$9.6–12.7**.
**CAISO's CT bids track the CA-composite citygate at ≈ one base heat rate.** The
model instead prices them at `1.145 × base_hr × (composite × ≈1.5)`.

### §1.6 — The rule-25 disposition, executed strictly

`GAS_OFFER_MARGIN_ANCHOR_BY_ISO` shows every ISO derives its anchor from
*"the model's own merit-order delivered-gas series"*, while each ISO's measured
offer surface is derived by its own `derive_*_offer_surface.py` against whatever
index that script chose. **Whether the same identity gap exists in ERCOT / PJM /
MISO / NYISO / NEISO is an ASK FOR THOSE LANES and is NOT measured, claimed or
armed here.** Their cells stay `U`. No value transfers in either direction.

---

## §2 — WHAT ELSE THE DIAGNOSTIC PHASE SETTLED (all measured, all pre-push)

### §2.1 — ROUTE (b), AVAILABILITY, IS FALSIFIED OUTRIGHT

`_caiso242_ctpeaker_anatomy.json`:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| class nameplate (MW) | 7,528.5 | 7,535.0 | 7,538.7 |
| available MW, mean | 6,306.5 | 6,315.5 | 6,341.6 |
| available MW, **p05** | 5,916.9 | 5,929.0 | 5,995.1 |
| dispatch (TWh) | 1.627 | 0.744 | 0.378 |
| **hours with < 1 % of nameplate headroom** | **0** | **0** | **0** |

**Availability never binds, in any hour of any year.** The class carries ≈ 6 GW
of available capacity in 95 % of hours and dispatches a mean of 186 / 85 / 43 MW.

### §2.2 — ROUTE (a) IS THE BINDER: THE CLASS IS PRICED OUT

Cheapest **available** CT_PEAKER offer vs the load-weighted system price:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| hours cheapest offer **>** price | **7,070** | **7,839** | **7,941** |
| (share of year) | 80.7 % | 89.5 % | 90.7 % |
| median gap (cheapest − price, $/MWh) | +15.57 | +12.63 | +12.96 |
| cheapest offer / system price mean | 76.43 / 54.65 | 53.08 / 37.18 | 54.75 / 38.22 |

### §2.3 — THE CHARTER'S SUSPECTED INVERSION IS REAL, IS CREATED BY THE MARGIN MECHANISM, FLIPS SIGN BY YEAR — AND IS IMMATERIAL

Capacity-weighted assembled mc by band ($/MWh), with band capacity:

| band | MW | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| `committed` | 829.8 | 99.00 | 61.61 | 66.57 |
| `econc00…05` (6 rungs) | 6,189.4 | 100.39 → 101.88 | 74.49 → 75.20 | 76.44 → 77.31 |
| `peak…peak5` (5 rungs) | 623.5 | 109.92 | **71.92** | **76.59** |

In **2023** the curve rises correctly (peak dearest). In **2024** `peak` is the
**cheapest** rung of the class above `committed`; in **2025** it sits between
`econc00` and `econc01`. **The inversion is not a property of the multipliers —
it is manufactured by `apply_gas_offer_margin` and its sign is the sign of
`anchor − fuel`:** econ carries `markup_hr` ≈ 4.99 MMBtu/MWh against peak's
1.805, so the adjustment `markup_hr × (anchor − fuel)` moves econ 2.8× further
than peak, downward in 2023 (fuel 7.41 > anchor 4.796) and upward in 2024/2025.
**The charter predicted this from the raw multipliers; the measurement locates
its cause in the mechanism and dates its sign to the year's gas price.**

**It is nonetheless NOT the object.** It reorders 623.5 MW (8.3 % of the class)
against 6,189 MW, and in ≈ 90 % of hours **both** sides of the inversion are
above the price, so no reordering of them changes dispatch. Recorded as a
structural finding about the mechanism; **not** proposed as this session's arm.

### §2.4 — THE FUEL-INVARIANT-MARGIN FORM IS FALSIFIED BY CAISO'S OWN THREE-YEAR OASIS RECORD

`gas_offer_net_revenue_margin` asserts `mult(f) = phys + (markup_hr/base_hr) ×
anchor / f`, i.e. the band multiplier must fall hyperbolically as gas rises.
`caiso_offer_curve_measured.json::_provenance.per_year_band_mults` measures that
same multiplier separately in each of 2023/2024/2025 — years whose model
delivered gas spans **7.41 → 3.83 → 4.58**, a 1.93× swing. Range of the measured
multiplier against the range the armed decomposition requires
(`_caiso242_passthrough_test.json`):

| class · band | measured range | armed-implied range | ratio |
|---|--:|--:|--:|
| **CT_PEAKER `econ_low`** (1.145 / 1.158 / 1.147) | **0.013** | **0.2775** | **21.3×** |
| CT_PEAKER `econ_high` | 0.040 | 0.2756 | 6.9× |
| CT_PEAKER `peak` | 0.026 | 0.1004 | 3.9× |
| CC_REGULAR `econ_low` | 0.058 | 0.1391 | 2.4× |
| CC_REGULAR `econ_high` | 0.039 | 0.0629 | 1.6× |

**CAISO's CT economic band multiplier is FLAT — 1.145 / 1.158 / 1.147 across a
1.93× fuel swing — where the armed form requires it to move by 0.28.** Full
fuel passthrough with a near-zero fixed margin is what the record shows; the
armed decomposition (`phys_econ_low` 0.686 against a bid of 1.145) books
**40 % of the offer as fuel-invariant margin — $27.26/MWh at the anchor** — on
**82.1 %** of the class's capacity.

**AGAINST INTEREST, and reported because it is a cost of the session's own
predecessor:** the same table shows the caiso-241 repair now prices
`CT_PEAKER.committed` **$31.03 / $8.64 / $4.99 per MWh BELOW** the measured
OASIS committed bid (armed 0.991 against measured 1.329 / 1.173 / 1.079). That
is the *bid* route, which DO-NOT-REDO item 2 forbids arming and which caiso-241
deliberately did not use — its case was the **physical** route and it stands on
that. **This is an observation on the record, not a proposal, and
`CT_PEAKER.committed` stays exactly where caiso-241 put it.**

### §2.5 — ROUTE (c) IS NOT AN ALTERNATIVE — IT IS THE SAME DEFECT SEEN FROM THE OTHER SIDE

The charter noted the keeper over-imports by **−8.4 / −7.6 / −5.6 TWh**, a larger
absolute miss than CT_PEAKER's, and called the interaction unexamined. It is not
independent: an offer surface that prices domestic CAISO gas ≈ 30 % above the
market's own bids makes imports win the evening ramp that peakers should win.
**One defect, two symptoms, opposite signs.** No separate import lever is
proposed and `IMPORT_TRANCHES[CAISO]` is not touched (it stays the standing
unfunded object).

---

## §3 — THE ARM, THE BOUND, AND THE ESTIMATOR — NAMED HERE, EVALUATED IN THE ADDENDUM

### §3.1 — THE MECHANISM

`ScenarioConfig.caiso_offer_surface_basis_reconciled` — **gated, default OFF,
CAISO-gated, hard-error on any ISO absent from its registry** (rule 25). It
multiplies each band multiplier that came from the measured OASIS surface by the
**measured basis ratio**

```
rho = mean_2023-25( gas_derive_basis + CO2_FACTOR x P_carbon )
    / mean_2023-25( gas_model_delivered + CO2_FACTOR x P_carbon )
```

both series already committed (`caiso_citygate_daily.csv`;
`gas_basis_by_iso_month.csv` + `CAISO_CITYGATE_TRANSPORT_ADDER`), both stated by
the code that consumes them. **`rho` is a ratio of two measured means over the
training window — no free parameter, no fitted value, nothing selected against a
residual.** It restores exactly the identity the reform already claims for its
own anchor: *at the window mean, the model's offer equals the measured bid.*

`phys_*` keys are **NOT** rescaled — they are CAMPD burn ratios, dimensionless in
heat rate and normalised by no gas price. So `markup = max(0, rho x mult − phys)`
falls with the multiplier, which is why this single change also moves §2.4's
falsified margin in the direction the record requires **without** touching the
`gas_offer_net_revenue_margin` mechanism itself (rule 19 `[R-ONE-MECH]`: one
mechanism, one phenomenon — the denominator is repaired once, at the multiplier).

**Registered, unmeasured, and to be settled in the addendum:** `rho` is
expected near **0.76** (fuel-and-carbon basis) — the reciprocal of §1.3's
1.298/1.310/1.327 — but the exact value, its per-year dispersion, and whether it
is stable enough to be a single ISO scalar rather than requiring a finer grain
are **not measured yet**. If the per-year dispersion exceeds **±0.05**, a single
scalar is **not** admissible and the arm is withdrawn rather than re-grained
against a residual (falsifier, §5.1).

### §3.2 — SCOPE IS AN OWNER DECISION, NOT A SESSION CHOICE (§6, ask 2)

The defect is a property of the **derive**, so it reaches **every CAISO gas class
whose econ/peak bands come from the measured surface** — CC_REGULAR, CC_CHP,
CT_PEAKER, CT_CHP, ST_GAS. Scoping the arm to CT_PEAKER alone would repair the
class the session was chartered on **and deliberately leave the identical defect
armed on four others**, which is exactly the class-by-class withholding that
caiso-241 limb 5 found had inverted CT_PEAKER's own merit order. **The session's
recommendation is the ISO-wide scope; it is put to the owner because it changes
the blast radius by roughly 6× and because the narrow scope is defensible as a
staged landing.**

### §3.3 — THE ESTIMATOR: §H‴, AND WHAT IT IS AND IS NOT A BOUND ON

**§H‴ — the re-offer envelope.** For each zone-hour of the committed keeper,
take the keeper's own marginal-rung identification and the assembled `mc` of
every CAISO gas tranche, apply the arm's exact per-tranche `Δmc`, and sum the
load-weighted change in the marginal rung's offer.

* **PRICE LEG — a TWO-SIDED ENVELOPE, and the registered falsifier.** Its
  upper limb assumes every repriced tranche that is marginal in a zone-hour
  passes its full `Δmc` into that hour's price; its lower limb is **0.0** (no
  repriced tranche is ever marginal). The measured `ΔC3a` must land inside
  `[lower, upper]` in **every** year. Registered as this session's falsifier
  precisely because caiso-241's price leg **passed with margin** while its
  volume leg breached — the price leg is the half that has earned the right to
  be called a bound, and it is conservative by construction (caiso-241 came in
  at **9 %** of its ceiling).
* **VOLUME LEG — AN ORDER-OF-MAGNITUDE INDICATION, EXPLICITLY NOT A BOUND, WITH
  NO FALSIFIER ATTACHED.** Per §0.5(1). A crossing count is reported so the
  addendum's expectation is legible, and **a breach of it is neither a gate
  failure nor evidence against the arm** — it is the known blindness to
  re-dispatch-opened hours, one level up from caiso-240's §H and caiso-241's
  §H′. Stated here, before the number exists, so it cannot be quoted as a bound
  afterwards.

---

## §4 — PREDICTIONS, REGISTERED AGAINST QUANTITIES NOT YET MEASURED

Written to be **uncomfortable**: P-2, P-4 and P-6 constrain the session's own
claim, and P-7 predicts its instrument stays blind.

| # | prediction | falsified by |
|---|---|---|
| **P-1** | `rho` lands in **[0.72, 0.80]** and its per-year dispersion is **≤ ±0.05**, so a single ISO scalar is admissible | any year outside, or dispersion > ±0.05 ⇒ the arm is WITHDRAWN (§3.1), not re-grained |
| **P-2** | **the arm does NOT close the CT_PEAKER gap either.** The class still ends **below its actual in all three years** (model/actual < 1.00), and below **75 %** of actual in at least two | the class reaching ≥ 75 % of actual in ≥ 2 years |
| **P-3** | G-STRUCT exact: **only** CAISO tranches whose band multiplier came from the measured surface move; **zero** rows move in any other ISO, and **zero** `committed`-band rows move in any class | any row outside that set moving |
| **P-4** | **the price move OVERSHOOTS at least one year's C3a requirement.** Measured `ΔC3a` is more negative than **−1.893 $/MWh** in 2025, or drives 2023 below **0.00** | the move landing inside the required window in every year |
| **P-5** | **C3a's 2023 verdict FLIPS to FAIL on the low side**, i.e. the arm cannot be promoted on a "no verdict regression" reading of G-C3a | 2023 still PASSing after the arm |
| **P-6** | **CT_PEAKER is still not the largest single-class gas miss in 2023** (CC_REGULAR remains larger there, as it already is on the keeper at −3.079 vs −2.502) | CT_PEAKER becoming the largest 2023 miss |
| **P-7** | **the DOF ledger does NOT move** (9 entries / 6 residual, unchanged) — §0.5(2); this arm changes values without removing keys, exactly the substitution the counter cannot see | any change in the ledger's counts |
| **P-8** | **the arm is LIVE in all three years** (no inert year), so caiso-240's dispatch-identity form of G-CTRL cannot bind and G-CTRL must take form 3 or form 4 | any year byte-identical to the control |

---

## §5 — GATES, EACH WITH A FALSIFIER. ALL SCORED ON **ARM − CONTROL**.

### §5.1 — G-STRUCT (pre-solve, zero LP)
**PASS** iff the armed-vs-recorded fleet diff moves exactly the measured-surface
bands of exactly the scoped CAISO classes, each at exactly `rho`, with
`offer_markup_hr` recomputed as `max(0, rho·mult − phys)` and **zero** rows
moving in any other band, class or ISO; **and** `rho` clears P-1's admissibility.
**FALSIFIER:** any row outside the declared set moving, any ratio off `rho`, or
`rho` failing P-1 ⇒ the arm is withdrawn and no solve is spent.

### §5.2 — G-CTRL — **FORM 4 IS AVAILABLE AND FREE, AND IS PROPOSED**
The gate's history: form 1 (*"one `run_config` field differs"*) is unsatisfiable
against any keeper more than a day old (caiso-239: 22 differing fields); form 2
(dispatch-identity in a measured-inert year, caiso-240) needs an inert year and
**P-8 predicts none**; form 3 (a spent control solve at HEAD, the owner's
2026-09-03 carve-out) cost caiso-241 ~65 minutes of LP to measure **exactly zero
drift**.

**FORM 4 — CODE-PATH EMPTINESS, MEASURED, ZERO LP.** Between the keeper's
`git_sha 607f9324` and HEAD there are **26 commits and 291 changed files, and
NOT ONE lies under `src/market_sim/`, `scripts/run_calibration*.py`, or
`data/raw/`.** The only changed `.py` outside `scripts/probes/` is
`scripts/register_forecast_run.py`, a dashboard registration script that cannot
reach a solve. **HEAD drift on the solve path is EMPTY BY CONSTRUCTION** — a
strictly stronger statement than caiso-241's empirical zero, obtained for
nothing. **PASS** iff that emptiness re-verifies at the moment of the solve.
**FALSIFIER:** any file under `src/market_sim/`, `scripts/run_calibration*.py`,
`scripts/run_calibration.py`, `src/market_sim/config/**` or `data/raw/**` differing
at solve time ⇒ form 4 is void, the arm falls back to **form 3** and spends a
control, and the fallback is reported as such. *(Form 4 is a gate re-spec and is
put to the owner as ask 3, §6.)*

### §5.3 — G-INERT
**PASS** iff the arm is not byte-identical to its baseline in any year.
**FALSIFIER:** byte-identity in any year ⇒ the mechanism is inert and nothing is
claimed for it.

### §5.4 — G-C1 (fuel mix)
**PASS** iff C1 does not regress: **≥ 12/12 rows in band and ≥ 8/8 free**, and no
class that is in band on the baseline leaves it.
**FALSIFIER:** any row leaving its band, or the free count falling below 8/8.

### §5.5 — G-C3b, G-C8, G-CAVEAT, G-C6
**PASS** iff C3b's verdict is unchanged; C8 stays PASS with no new mechanism in
D-2/D-4 (the arm lowers offers and adds no floor); the caveat budget stays
**≤ 1 ledgered / 0 protective**; and C6 is attested on **every** registered
bundle (an unattested C6 makes C3c FAIL rather than CAVEAT and would inject a
scorecard artifact into ARM − CONTROL).
**FALSIFIER (each):** a C3b verdict change; any new D-2/D-4 mechanism or a C8
budget breach; a second ledgered or any protective caveat; any bundle registered
without an attestation.

### §5.6 — G-C3a — TWO LEGS, AND THE SECOND IS NOT A "NO REGRESSION" LEG
* **Envelope leg — PASS** iff the measured `ΔC3a` lands inside §H‴'s two-sided
  price envelope in **every** year. **FALSIFIER:** any year outside ⇒ reported as
  an estimator or mechanism defect, **never re-fitted** (caiso-241 §8.1's
  standing instruction).
* **Verdict leg — DELIBERATELY NOT A PROMOTION CONDITION.** P-4 and P-5 predict
  this arm **overshoots** and that 2023 flips to a low-side FAIL. **Registering
  "no C3a verdict regression" as a promotion condition here would let the
  session pick the arm's size against C3a, which is precisely the rule 1
  `[R-STRUCT]` violation this lane exists to avoid.** The verdict is measured,
  reported at full size, and **excluded from §5.7**.

### §5.7 — THE PROMOTION RULE, FIXED NOW
Promote **iff** G-STRUCT, G-CTRL, G-INERT, G-C1, G-C3b, G-C8, G-CAVEAT and G-C6
all pass **and** the §H‴ price-envelope leg of G-C3a passes. **C3a's verdict,
in either direction, is reported and excluded from the basis.** The basis is
**structural**: a measured dimensionless ratio is evaluated against the
denominator it was measured against, at zero free parameters, restoring the
round-trip to CAISO's own public bid record.

**If C3a's verdict WORSENS, that is not by itself a bar to promotion** (the
owner's standing standard: *"if structural integrity improves but gates regress
that may still be a keeper"*). **If C3a's verdict IMPROVES, that is not a reason
to promote either**, and §0.6 fixes that in advance.

---

## §6 — OWNER ASKS (three; the lane is at terminal rest and none is presumed)

1. **IS THE SOLVE FUNDED?** The CAISO lane rests at caiso-201/222 and caiso-241
   was funded by an explicit per-object ruling. **This session's primary
   deliverable — the diagnosis in §1–§2 — is complete and costs nothing further.**
   The arm needs ~55–65 min of LP (one bundle; ~110–130 min if G-CTRL falls back
   to form 3).
2. **SCOPE: CT_PEAKER-only, or every CAISO gas class on the measured surface?**
   §3.2. The session recommends **ISO-wide**; the narrow scope is defensible as a
   staged landing and is the owner's to choose.
3. **G-CTRL FORM 4** (§5.2) — accept the code-path emptiness proof in place of a
   spent control solve for this arm, given the measured empty diff and
   caiso-241's measured zero drift? Declining costs one extra control solve and
   nothing else.

---

## §7 — DELIVERABLES OF THIS SESSION SO FAR (all zero-LP, all pushed with this file)

`scripts/probes/_caiso242_ctpeaker_anatomy.py` → `_caiso242_ctpeaker_anatomy.json`;
`scripts/probes/_caiso242_passthrough_test.py` → `_caiso242_passthrough_test.json`;
`scripts/probes/_caiso242_gas_basis_identity.py` → `_caiso242_gas_basis_identity.json`;
this precommit. **No `ScenarioConfig` field added, nothing armed, keeper
unchanged, no run registered.**
