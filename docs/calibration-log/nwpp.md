# NWPP calibration log

Per-region continuation of `docs/calibration-log.md` (frozen archive, entries through 2026-07-19) for
the **Northwest Power Pool / Western Power Pool footprint** — a **pool of ~17 balancing authorities**
(BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP), NERC WECC.
**NWPP is neither a balancing authority nor an ISO**, the first such region in this repo; every name
downstream still says "ISO". Program: `docs/multi-iso/nwpp-addition-plan-2026-09.md` (charters, cards,
wave graph, lane table); desk ledger `docs/handoffs/nwpp-desk-ledger-2026-09.md` — **the ledger wins
where the two diverge**; Phase-0 census `docs/multi-iso/nwpp-data-audit.md`.

Entries are appended **verbatim** by the NWPP ADDITION DESK from each lane's FINDING `## Log entry`
section (plan §8.0 rule 1 — **a lane never writes this file**). Newest last.

Lever queue: `docs/mechanism-testing-matrix.md` §5.9; cell verdicts
`docs/codebase-site/data/mechanism-matrix/NWPP.js`.

---

## Lane state at file creation (2026-09-14, lane NWPP-35)

**No keeper exists.** NWPP was registered on 2026-09-14 by lane NWPP-20
(`docs/handoffs/FINDING-nwpp-20-2026-09-14.md`), so
`frontend/data/backcast/keepers/NWPP.json` does not exist, no bundle has been solved, and this lane
has no run to score, no determination and no gates. The first solve is lane **NWPP-40**, which is
**gated on NWPP-36** (owner ruling N3 — see below). Training window **2023–2025**, and rule 16
`[R-ALLYEARS]` binds from day one: a single-year NWPP keeper is refused.

**Counts measured at this file's base sha `d54cd9c5`, because both this program and the SOCO program
flip the same pin list and the second to land re-counts (plan §0):**
`config/iso_configs._ISO_BUILDERS` carries **NINE** regions — ERCOT CAISO MISO PJM NYISO NEISO SPP
**NWPP SOCO** — the last two both registered 2026-09-14 (NWPP-20 merged first, SOCO-20 second). The
mechanism matrix carries **nine** columns and nine shards. Seven keeper shards exist; NWPP and SOCO
have none. Prose saying "seven ISOs" is stale; prose saying "eight" was true only between the two
merges.

Facts every NWPP session inherits, so nobody rediscovers them in a residual:

- **THERE IS NO NWPP PRICE, and the rubric already knows it.** Card **N2** was ruled 2026-09-13 in
  both limbs. Limb (a) chartered lane **NWPP-13** to build a WEIM-derived hourly series under a STOP
  gate pre-registered before any data was read; **it read NO**
  (`docs/handoffs/FINDING-nwpp-13-2026-09-13.md`). Gate D3 — reconciliation against the independent
  Mid-C Peak index — failed in **every** year: the NW-group WEIM on-peak price sits
  **−37.5 % / −22.6 % / −23.6 %** (2023 Jun–Dec / 2024 / 2025) against Mid-C, daily correlation
  0.74 / 0.95 / 0.67, against pre-registered bars of ±10 % and ≥ 0.80. **No bar was moved after the
  series was seen, and nothing landed to `_validation-source`.** WEIM is not thin here — it clears
  **5.5–6.2 %** of footprint energy net (10.6 % pairwise-gross), so volume was never the problem;
  the problem is what the price *is*. Limb (b) is therefore live: an NWPP run reads a determination
  **naming its own basis, never a bare `CALIBRATED`**. The class exists in the scorer as rubric
  **v3.8**'s `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` /
  `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)`, keyed on the **absence** of an
  `actual_lmp.json` block — landed from lane SOCO-22, which is why lane NWPP-22's identical branch
  was **withdrawn** on rebase rather than doubled (rule 19 `[R-ONE-MECH]`;
  `FINDING-nwpp-22-2026-09-13.md` §0-bis). **A neighbouring-hub proxy stays refused outright**
  (gate G17) — do not re-open it.
- **CASCADE COUPLING IS BUILT BEFORE THE FIRST KEEPER** (owner ruling **N3**, 2026-09-13, *against*
  the desk's own recommendation). The fleet is **35,799.5 MW (36.3 %) conventional hydro** with eight
  ≥ 1 GW plants in one hydraulic chain, on machinery that models independent monthly budgets. The
  owner ruled that the first NWPP number must mean more than a test of monthly hydro budgets, so
  wave **W3b** and lane **NWPP-36** (Columbia mainstem hydraulic coupling) exist and **NWPP-40 does
  not start without them**. Lever NWPP-54 is retired, its content promoted into NWPP-36. The
  coupling is ONE default-OFF `ScenarioConfig` field on `_CACHE_KEY_OPTIONAL_FIELDS` **and**
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit, so no existing keeper's key moves
  (gate G8 as amended).
- **BPAT'S BALANCE IDENTITY FAILS STRUCTURALLY — never assume `Demand = NetGen − TotalInterchange`.**
  It holds to 0.000 MW for PACW/PSEI/TPWR and near-exactly for ten more BAs, but for **BPAT** the mean
  residual is **−3,206 MW** and **81.5 % of hours** miss by more than 1 MW, because BPA wheels energy
  it neither generates nor serves. **BPAT is 20.26 % of footprint load** (NWPP-10 §3.1). A derive that
  assumes the identity is wrong for a fifth of the footprint in four hours out of five. A divergence
  here is a FINDING, never something to correct away (rule 14 `[R-ACCURATE]`).
- **THE CAISO DOUBLE-COUNT — DISCLOSE, DO NOT FIX.** CAISO is registered with a `WECC_import` zone
  whose firm tranche is named **`PNW_hydro_base`** (`model/interchange/caiso.py`) — *this footprint,
  by name*, priced as a Tier-3 contract-cost proxy under rule 14's misalignment exception.
  Registering NWPP puts the same physical energy on both sides of a seam, represented two ways.
  **Rule 25 `[R-ISO-SCOPE]` forbids this desk touching how CAISO prices its side**; the CAISO-side
  question is ROUTED (ledger R-a) and **stays routed**. Quantify NWPP's side; never reconcile
  CAISO's.
- **VOLL $2,000/MWh is DECLARED INTERIM and is a ledgered rule 21 `[R-DOF]` free parameter.** FERC
  Order 831's $2,000 applies by its own terms to RTOs and ISOs, and NWPP is neither. No participant
  IRP states a $/MWh loss-of-load cost, and no WECC/WRAP planning VOLL is published. The value
  standing in is the **WEIM hard offer cap** (CAISO Tariff §39.6.1) — *the cap of an imbalance market
  that clears ~6 % of footprint energy is not a customer damage function*. It must be declared as
  interim in **every** attestation that reads it, and the pre-declared successor is an LBNL ICE
  derivation on the footprint's own customer mix (routed, `FINDING-nwpp-20` §5). **Never swept
  against a gate.**
- **THE NW↔OR LINK IS A TIER-3 PLACEHOLDER THAT CANNOT BIND** — 43,600 MW, the NWPP-NW zone's own
  nameplate rounded to the nearest 100, registered for a **documented absence** of any published
  limit. The other six path limits are cited WECC paths (Tier-1 Path 35 / Path 16; Tier-2 Path 20 and
  the aggregated Paths 8+6+14). Never tune the placeholder to a price residual (rules 1 / 13 / 14).
- **THE SCORER IS CLOSED TO THIS PROGRAM.** The plan's rubric prohibition was carved exactly once, by
  owner ruling **N11**, for lane NWPP-22 alone — and that lane's branch was then withdrawn as a
  duplicate. **No other lane in this program may touch `scripts/calibration_verdict.py`.**
- **SEASONALITY IS NOT UNIFORM ACROSS THE ZONES, AND THE FLOOR READS ONE SCALAR ANYWAY.** The
  reliability floor reads a single `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]` against the footprint
  **coincident** peak — summer in all three years — while the members split
  **8 winter-peaking BAs / 6 summer / 1 flipping (PACW)**. **NWPP-NW peaks in WINTER every year**
  (summer ÷ winter = 0.86 / 0.80 / 0.82) while **NWPP-SNV peaks in SUMMER** at 1.95 / 2.06 / 1.87 ×
  its own winter load, with load correlation **0.048** against NWPP-NW; **NWPP-INLAND mixes both
  regimes inside one zone**, so even a per-zone seasonal PRM would average two regimes there. The
  mismatch is DECLARED at full magnitude on `_nwpp_config`, not softened, and a per-zone seasonal
  requirement is pre-declared lever **NWPP-57** — never an edit to a dict every registered region
  reads.

## Pre-push checklist (STANDING — every session in this lane, before every push)

`.claude/hooks/ruff-prepush-gate.sh` (`PreToolUse` on `Bash|mcp__github__push_files`) refuses a push
whose *own* changed `.py` files fail either gate, and names them plus the fix. It is check-only — it
never edits your tree (rule 27 `[R-PUSH]`). Run the two commands yourself anyway: a hook can be
disabled, a session can run without it, and it deliberately does not gate the whole tree. Run from the
repo root and confirm **exit 0** before staging:

```
uv run ruff format --check .
uv run ruff check .
```

---

## nwpp-41 — 2026-09-19

**NWPP's FIRST KEEPER.** `2026-09-19-nwpp41-coal-taxonomy-own`, bundle
`results/calibration/nwpp41_span_A`, 2023–2025. Promoted on the owner's pre-solve ruling *"Promote
after the C1 fix lands"*. **Determination `NOT-YET` — a keeper is not a calibration**, and NWPP is
additionally PRICE UNSCORED (rubric v3.8), so nothing here certifies a price level, shape or tail.

**One field armed**: `coal_prb_proxy_own_iso`, for NWPP alone in `pipeline/backcast_config.py`. It
closes two defects at one seam, both plumbing, both proven zero-LP before any solve:

1. **C1** — `coal_supply_NWPP.csv` had never been derived, so all 17 NWPP coal plants binned to the
   bare class `COAL`, which the benchmark has no row for (the benchmark passes the EIA-923 row's own
   fuel code to the *same* resolver and itemizes `COAL_PRB`/`COAL_BIT`/`COAL_WC`). The seam also
   corrupted the share denominator, since `_gen_totals` sums the model over *benchmark* keys and so
   excluded the model's whole coal output from its own total (2024 `CC_REGULAR` +3.6 pp → +1.4 pp).
2. **Rule 25** — `_prb_monthly_actuals` pooled `COAL_PLANT_SUPPLY`, **every plant of which is in
   Texas**, so an NWPP plant with no Schedule-2 filing priced against ERCOT's delivered PRB cost
   ($1.818/$1.760/$1.622 per MMBtu) instead of NWPP's own reporters' ($2.463/$2.134/$2.066). Not a
   corner case here: Colstrip and Centralia file no price in any year, 26.7 % of coal MW.

**Rule 14 `[R-ACCURATE]` is the basis, never the residual.** Zero free parameters — the DOF ledger is
3 entries / 3 residual, identical to NWPP-40's, because the flag selects *which measured series* the
proxy pools. Confinement measured: only Colstrip and Hardin move in every year (TS Power also in
2025); non-coal offer max|Δ| **$0.0000000000**, `pmax`/`availability` max|Δ| exactly 0.

**Gates**, against the lane-NWPP-40 control differenced at rule-29(b) form 4, **no control solve**
(G-DRIFT classified the one other config delta, `neiso_coldsnap_derate_dualfuel_unswitched` at its
NEISO-gated default, INERT): **C1 FAIL (5 rows) → PASS** (18/18 all, 14/14 free); C2 PASS; **C4 FAIL**
(coal r .511/.535/.475 → .539/.546/.502); C6 PASS (authorized_price_tuning NONE, verified from
dispatch — the three non-unity-band groups carry zero NWPP energy); C8 PASS (0.0 % forced everywhere).
Basis shrank from `{fuelmix, dispatch_corr}` to `{dispatch_corr}`.

**Both pre-registered predictions landed** (C1 closed, C4 still FAILs). Two unpredicted moves are
**side effects reported, not achievements claimed** (rule 1 — no dispatch mechanism was touched):
C4's r and NRMSE both improved, and reported-only C5a CO2 went −65.9/−58.7/−54.8 % →
−15.1/−23.7/−21.4 % (likely per-class emission-rate coverage restored by the taxonomy fix, since less
coal would push the error the other way; no ablation run).

**C4 ROUTED, not attempted** (owner ruling). Diagnosis: the coal offer stack is bimodal — a $4.50
must-run tranche in the money 100 % of hours against $37.7–42.8 for everything else, versus a $26.15
mean price — so ~90 % of model coal is price-insensitive and ~4,600 MW of available coal sits out of
merit 87 % of hours; availability was measured and ruled out. The measured fleet's midday trough
**deepens** with solar (peak/trough 1.21 → 1.32 → 1.40) where the model reads 1.02. **Successor
blocked on `bin_assignments_NWPP.csv`**, absent for every legacy-bin ISO.

**Still carried, absorbed nowhere**: 2025 coal volume −28.8 % (row SKIPPED on the preliminary EIA-923
vintage; model 27.21 vs 42.26 TWh — the bigger half of C4's cause), energy balance −10.02 TWh vs a
±3.0 tol, the Chief Joseph 2025 pond dual (−325.17 $/kcfs·h for 5,808 h), NWPP-SNV VOLL hours 23+34,
and every NWPP-40 disclosure inherited verbatim.

**Reported and deliberately NOT fixed**: the same PRB-proxy defect reaches MISO (12 plants), PJM (2)
and SPP (3–5); their matrix cells stay `O` (rules 25 / 28(d)).

**Solve**: ONE shard, ONE `--year 2023 2024 2025` invocation, years sequential; the parent ran no LP.
44,960.5 s = 749.3 min = 1.36× NWPP-40, peak RSS 4.78 GiB, no swap. Per-pass ratios are strongly
non-uniform — 2023 P0 0.99×, **2024 P1 2.26×**, **2025 P1 0.90×** — with 2024 P1 the sole outlier at
1.8× 2023 P1's iterations *and* the slowest iterations/s of the six. No mechanism attached.
**Attempt 1 was lost to a platform restart** mid-2025-P1 after ~13 h; reuse was foreclosed (verified
in code), the owner ruled relaunch, and 2023/2024 reproduced to four decimals across attempts.

Records: `docs/handoffs/FINDING-nwpp-41-2026-09-19.md`,
`docs/handoffs/PRECOMMIT-nwpp-41-2026-09-17.md` (nine addenda),
`docs/handoffs/NWPP41-attempt2-solve-log-excerpt.txt`, `scripts/gen_nwpp41_attestation.py`,
`scripts/probes/_nwpp41_coalrank_phase0.py`. Full 36-file bundle recoverable at
`1fb4b6b5c680ca5ae0ef9375eb11b7cbbb08d64d`.

---
