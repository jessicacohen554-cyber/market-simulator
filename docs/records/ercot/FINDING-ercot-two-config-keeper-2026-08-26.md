# FINDING — ERCOT becomes a TWO-CONFIG KEEPER (owner ruling, program-director sitting 2026-08-26): forward keeper `2026-08-25-234-eastex-identity` (2024–2025) + 2023 carve-out `2026-08-25-236-swcap-clip-k33` — and the headline consequence, stated first: the forward keeper scored on its own span reads CALIBRATED where its registered 3-year determination is NOT-YET

**Governance-records session (ercot-238), branch
`claude/ercot-governance-rulings-0826-9xqfaw`. ZERO-SOLVE — every number in
this finding is read from committed artifacts
(`scripts/calibration_verdict.py`, registered sidecars/payloads/bench;
no LP, no re-bundle, no registration change). This is ruling 3 of the three
signed owner rulings executed by this session (ruling 1 = the 59→61 band-count
correction pass; ruling 2 = the ercot-225 G-SPUR Option A gate revision).**

## 0. The ruling, verbatim (owner, 2026-08-26)

> "The keeper should be the 2023 config that works plus the 2024-2025 keeper
> from before, so two different configurations with 2024/2025 config being
> the forward keeper for use in the model and 2023 as a carve out designed
> to address unique market conditions for that year"

## 1. THE HEADLINE — what the partition changes, reported first because it is the whole substance of the ruling

**The forward keeper `2026-08-25-234-eastex-identity`, scored on its
designated span {2024, 2025}, reads `CALIBRATED` — where its registered
3-year determination is `NOT-YET` on fail set {C3a-2023 −39.7 %, C3b-2023
0.730}.** Both failing criteria are 2023 and ONLY 2023 — the exact year the
carve-out covers — so partitioning the training window by config drops both
failures out of the forward keeper's scored span. Span read (from
`calibration_verdict.py --run-id 2026-08-25-234-eastex-identity --years
2024 2025`, committed artifacts only, 2026-08-26):

* C1, C2, C3a, C3b, C4, C6, C8: **PASS** in both years
  (2024 C3a −0.2 % / C3b 0.131 · 2025 C3a −7.9 % / C3b 0.101).
* C3c: **CAVEAT, ledgered ×2** (2024 22/53 = 0.42×, 2025 1/31 = 0.03× —
  ACCEPTED MODEL-CLASS LIMITATION), non-downgrading under rubric v3.3
  (lone ledgered C3c), named on the determination basis at full magnitude.
* The verdict is stamped **SPAN-RESTRICTED** by the scorer and is never the
  run's registered determination, which stands untouched.

This is **legitimate only as a config carve and never as a year drop**, which
is why the structure below refuses to let either half disappear.

## 2. Forward-keeper identity — verified before acting (ruling 3(a))

The director's reading is confirmed by the record; no ambiguity, no
escalation needed:

* The ercot-235 charter (owner order, log entry verbatim): "2024/2025 are
  neither solved nor scored in this lane and the 3-year keeper
  `2026-08-25-234-eastex-identity` stands untouched as **the cross-year
  recipe**."
* Both the ercot-235 and ercot-236 promotion addenda: "2024/2025 stay
  referenced to the cross-year `2026-08-25-234-eastex-identity` keeper
  (3-year, zero fitted scalars, untouched)."
* It supersedes `2026-08-24-231-tie-zone-measured` by carrying the REPAIRED
  EASTEX crosswalk (the card Z-A identity repair): reverting to ercot-231
  would re-arm the geographically mis-attributed `NE_LOB` measured input,
  which rule 14 `[R-ACCURATE]` forbids.

**FORWARD KEEPER = `2026-08-25-234-eastex-identity`** (bundle
`results/calibration/ercot234_eastex_identity`, 3-year, zero fitted scalars).
**2023 CARVE-OUT = `2026-08-25-236-swcap-clip-k33`** (bundle
`results/calibration/ercot236_k33_clip`, 2023-only under the owner's
2026-08-25 rule-16 waiver; the ECRS-era regime — ECRS introduced 2023-06-10).

## 3. The coverage invariant, and how it was verified

**Every year of the training window 2023–2025 is covered by exactly one
designated config. Nothing is dropped, hidden, or left uncovered.**

| year | designated config | span determination | registered determination |
|---|---|---|---|
| 2023 | `2026-08-25-236-swcap-clip-k33` (carve-out) | CALIBRATED | CALIBRATED (2023-only record) |
| 2024 | `2026-08-25-234-eastex-identity` (forward) | CALIBRATED (span {2024, 2025}) | NOT-YET (3-year record, fails 2023-only) |
| 2025 | `2026-08-25-234-eastex-identity` (forward) | CALIBRATED (span {2024, 2025}) | NOT-YET (3-year record, fails 2023-only) |

Verified mechanically: the `config_partition.configs[].years` in
`frontend/data/backcast/keepers/ERCOT.json` are {2023} ∪ {2024, 2025} =
{2023, 2024, 2025} with empty intersection — the partition of the training
window. The forward keeper's registered 3-year record (NOT-YET, both 2023
misses at full magnitude) remains registered, published, and re-verified —
it is surfaced BY the partition machinery on the Calibration Status page,
not displaced by it. This preserves the substance of rule 16 `[R-ALLYEARS]`
under the owner's invoked waiver.

## 4. Both determinations, re-verified from committed artifacts (ruling 3(c))

`scripts/calibration_verdict.py --run-id <id>` — no solve
(`[R-HOLDOUT]` rule 22, D-5(b) discipline; years ⊂ {2023, 2024, 2025}):

* **`2026-08-25-234-eastex-identity` (registered, 3-year):** `NOT-YET`,
  determination basis "undocumented out-of-tolerance (FAIL) criteria:
  price_mean, price_shape" — C3a-2023 −39.7 % / C3b-2023 0.730; per-year
  officials 2023 −39.7 % / 0.730 / 72 · 2024 −0.2 % / 0.131 / 22 PASS ·
  2025 −7.9 % / 0.101 / 1 PASS; C3c ledgered ×3. Reproduces the registered
  record exactly.
* **`2026-08-25-234-eastex-identity` (span {2024, 2025}):** `CALIBRATED`,
  lone ledgered C3c ×2 reported on the determination basis (§1).
* **`2026-08-25-236-swcap-clip-k33` (registered, 2023):** `CALIBRATED`,
  "all criteria pass, governance attested," zero caveats (C3a −7.3 %,
  C3b 0.102, C3c 180/181). Reproduces the registered record exactly.

## 5. What was built to express the structure (the machinery could NOT previously express two designated configs)

The ruling's stop-condition was checked first: the keeper store schema,
`build_status.py` and the Calibration Status renderer all carried exactly one
run id and one determination badge per ISO — a bare single badge for a
partitioned ISO would launder the partition into whichever half reads better.
Rather than forcing the structure into a single-keeper field with prose
nuance (which the ruling forbids), the machinery was extended so the
partition is a first-class, machine-scored object:

1. **`scripts/calibration_verdict.py`** — `determine(run_id, years=…)` /
   CLI `--years`: the SAME rubric over the SAME committed artifacts,
   restricted to a designated span. The verdict is stamped
   `span_restricted` (and `render_text` prints it) so it can never be quoted
   as the registered determination; an unrestricted verdict's payload is
   byte-identical to the pre-change scorer (verified: the five other ISOs'
   status parts are byte-unchanged). `--write-metrics --years` is refused —
   a span verdict can never be baked into a bundle's `metrics.json`.
2. **`frontend/data/backcast/keepers/ERCOT.json`** — re-keyed: `keeper` =
   the forward run id; a new `config_partition` block carries the ruling
   verbatim + date, the coverage invariant, and both configs (role, run_id,
   bundle, years, both determinations at declaration, and each config's
   note). The standing note is rewritten for the structure under the X-2
   discipline, with the prior (ercot-236) note preserved verbatim in
   `note_provenance` — including the same-day 59→61 correction.
3. **`scripts/build_status.py`** — a shard `config_partition` is scored
   LIVE at build time: each config on its designated span AND on its full
   registered span, both attached to the status part. The primary `keeper`
   verdict stays the forward keeper's registered full-span NOT-YET —
   conservative by construction.
4. **`docs/codebase-site/js/calibration-status.js`** — a partitioned ISO
   renders one span-labelled badge PER config (card and detail header), the
   card accent takes the WORST config determination, and the detail pane
   shows the ruling verbatim, the invariant, and each config with its span
   and — whenever it differs — its registered determination with the fail
   reasons. The bare-single-badge path is unreachable for a partitioned ISO.
5. **`scripts/dashboard_add_run.py`** — `_protected_run_ids` now includes
   every `config_partition` member, so the carve-out is retention-immune
   exactly like a keeper (the status page scores it on every rebuild).

`build_status.py --check`: parts in sync, 6 keepers; only ERCOT's part
changed. `audit_keepers.py` (full): PASS 0 failures / 0 warnings — including
the re-keyed ERCOT lane. (The handoff's warning about a pre-existing S1
failure at its HEAD no longer reproduces at this HEAD — the owning lane
fixed it before this session; nothing here touched any bench part.)
`check_mechanism_matrix.py`: clean — keeper stamps and §5.1 prose header
re-stamped to the two-config structure (`[R-MECH-MATRIX]` duty, ERCOT shard
only).

## 6. Forecast-lane inheritance (ruling 3(e))

**The forecast lane inherits the FORWARD keeper's config —
`2026-08-25-234-eastex-identity` — per the owner's words: "2024/2025 config
being the forward keeper FOR USE IN THE MODEL."** The 2023 carve-out does
NOT leak into forward runs, verified from committed configs:

* `ercot_offer_swcap_clip` is **default False** in `ScenarioConfig`
  (`src/market_sim/config/scenarios.py`); it is armed (`True`) only in the
  carve-out bundle's `run_config.json`, and the forward keeper's
  `run_config.json` does not carry the key at all.
* The k_peak = 33.0 gas-peak offer scaling exists only in the carve-out
  run's `offer_curve_by_group` values; the forward keeper's
  `offer_curve_by_group` is the unscaled ercot-234 recipe.

There is no automatic keeper→forecast config plumbing to re-wire: forecast
runs reference a recipe explicitly (the `replay_keeper` channel and the
matrix's fc postures), and the designated recipe reference for ERCOT forward
work is the forward keeper's bundle. Any future forecast handoff citing the
ERCOT recipe cites `ercot234_eastex_identity`, never `ercot236_k33_clip`.

## 7. What this finding does NOT do

* No re-adjudication: the ruling is executed, not re-opened.
* No registered record is modified: both runs' sidecars, payloads and
  determinations stand exactly as registered (the carve-out's sidecar prose
  carries only the separately-authorized ruling-1 59→61 correction).
* No solve, no LP, no holdout spend (`holdout-freeze` respected; ERCOT holds
  no `complete`/`final` marker; no `--holdout-authorized` anywhere).
* No other ISO's shard, matrix shard, status part or bench is touched
  (`[R-ISO-SCOPE]` rule 25) — verified by `git status` and by the five
  byte-unchanged status parts.
