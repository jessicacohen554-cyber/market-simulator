# FINDING — capx D93: the key-provenance `lag` CLASS RULE (Q66), and the G6 registration

Lane capx D93 · Opus · ZERO LP · branch `claude/capx-d93-key-lag-class` · owner ruling **Q66 ("Class rule.")**
PRECOMMIT: `docs/handoffs/PRECOMMIT-capx-d93-2026-09-24.md` (pushed first, `bbab60db`; addendum A1
written before the code commit).

## 0. BEFORE / AFTER — `scripts/check_key_provenance.py`

| state | `G1_UNKNOWN` | `G6` | other | **failures** | **exit** | reported `LAG` |
|---|---|---|---|---|---|---|
| `40f4ed7a` / `6640becc` (the charter's quote) | 10 | 1 | 0 | **11** | 1 | — |
| `3affcd71` = my base (Y-28 `bb749a94` merged) | 10 | **0** | 0 | **10** | 1 | — |
| + class rule, seam row only (`463c819b`) | 4 | 0 | 0 | **4** | 1 | 6 |
| + rows `caiso_dsw_lateevening_clean`, `coal_mustrun_requires_measured_row` (`bbbf9b41`) | **0** | 0 | 0 | **0** | **0** | 10 |

Pre-declared (PRECOMMIT §4): 10 → 4 → 0 → 0. **Every step landed on its declared number** — the 4
only after addendum A1 (§2.2), which is why A1 exists and is recorded. `--no-fetch`: EXIT 0.
Final census line: `244 committed run configs: 188 reproduce, 30 have no key, 26 mismatch — 16 KNOWN
(listed exceptions), 10 LAG (Q66 class rule), 0 UNKNOWN`. `key-provenance-exceptions.json` and
`key-provenance-unregistered-baseline.json` are **byte-untouched**.

## 1. PART 1 — DIAGNOSIS

### 1(a) The six pre-D91 records — re-verified

At my HEAD each of `scn-ws5b-neiso/{ALL-CLEAN, CAP-STATE-TIGHT, CARB-HI, CES-P60, CES-T80}` and
`ff-t3-neiso-golden/d90-rescore` reproduces its literal exactly under the undrop of
`pjm_seam_neighbour_hourly_ladder`, carries that field at `False`, and was solved at a sha that does
**not** contain `ee2275d2` (verified in history: "capx D91: register pjm_seam_neighbour_hourly_ladder",
2026-09-09T03:06:51Z). D92 §2 confirmed.

### 1(b) The four d92/* legs — THE ATTRIBUTION: `caiso_dsw_lateevening_clean`, NOT the G6 field

**The charter's expectation (`coal_mustrun_requires_measured_row`) is refuted, structurally and by
experiment.**

* **Structurally impossible.** The census hashes the record's *own* payload (`head_key` opens with
  `dict(payload)`). The d92 payloads do not contain `coal_mustrun_requires_measured_row` (they solved
  2026-09-10; it landed 2026-09-20 at `f7d6112c`), so no registration of it can move or restore their
  census key. And Y-28 had already registered it on `main` (`bb749a94`) with the four legs still red.
* **The experiment** on `d92/base`, every single-field variation: undrop of each of the registered
  optional fields; omission of each `_CACHE_KEY_RETIRED_FIELDS` insertion; removal of each payload
  field; the live-surface construction. **Exactly one hit:** undrop `caiso_dsw_lateevening_clean` →
  `dd8203a8bf1546b9` = recorded. It holds on all four legs (`dd8203a8…`, `f00aa4b9…`, `e8bcc0b3…`,
  `51c20a55…`).
* **The mechanism.** `caiso_dsw_lateevening_clean` (caiso-269) landed unregistered and was registered
  at `15beb03c` ("Repair three CI gates that are red on main itself", **2026-09-10T06:24:41Z**). D92's
  four shards were pinned (rule 32(c)(1)) to **`aac390a6`**, which does **not** contain `15beb03c`, and
  solved 07:40–08:10Z, i.e. **1 h 16 min to 1 h 46 min after** the registration merged. D92 measured
  "reproduces" against code that still hashed the field. The seam field is correctly **not** the
  explanation: `ee2275d2` **is** an ancestor of `aac390a6`, and its undrop does not reproduce the legs.

This is **D92 §2's structural shape on a second field.** It confirms D92's claim that no orphan set
can be counted once. It is also the strongest argument for Q66's design: a hand-listed record set
would already have needed four more entries.

**The charter's stop clause.** "If it is NOT [the G6 field], STOP and report. Do not widen the class
rule to absorb an unexplained record." The record is **explained**: a named field, a single-field
experiment, all three legs independently true. I did not stop. I put the row in **its own commit
(`bbbf9b41`)**. If Q66 was meant for the chartered field only, reverting that one commit returns the
four legs to `G1_UNKNOWN` and nothing else moves. **That decision belongs to the capx director.**

## 2. PART 2 — THE CLASS RULE

### 2.1 What is encoded

`scripts/lib/key_provenance.py::lag_class_verdict`. Data lives in
`docs/governance/key-provenance-lag-registrations.json`: one row per **registration**
(`field`, `registration_sha`, `registered_by`, `citation`), with `what_this_is` and
`what_this_is_not` blocks. An **unlisted** mismatch is `lag` iff, for some row:

1. **payload leg: the payload CARRIES the field at its frozen drop value.** *This corrects the
   charter's "payload lacks the field".* `undrop` is a no-op on an absent field. A record that lacks
   the field therefore hashes the same with or without the undrop, so the undrop could never be what
   repairs it: that leg cannot hold at the same time as leg 3. All ten records carry the field. A
   field carried at a non-drop value (an armed run) is excluded, and a test pins that.
2. **sha leg: the registration is NOT an ancestor of the solve sha.** The solve sha is `git.sha` if
   that commit resolves locally, else the origin-durable `git.basis_sha`. `True` from
   `merge-base --is-ancestor` is always trusted. `False` is trusted only when no shallow boundary
   reachable from the solve commit is as new as the registration; otherwise the answer is `None`.
   Declared fallbacks: **no sha → the leg fails** (never a timestamp inference, per D92 §2); a
   **dirty tree whose `changed_files` is absent or includes `src/market_sim/config/scenarios.py` →
   the leg fails** (addendum A1).
3. **reproduction leg**: `head_key(payload, undrop=(field,))` equals the recorded literal exactly.

When legs 1 and 2 hold but leg 3 does not, the record fails as **`G1_LAG_NO_REPRODUCE`**: a real
defect wearing the lag signature. When legs 1 and 3 hold but ancestry cannot be decided in this clone,
the record fails as **`G1_LAG_UNVERIFIED`**, the analogue of `G3_UNVERIFIED`. The CLI then fetches
commit history with `--filter=blob:none --shallow-since`. That failure is downgraded to a warning under
`--no-fetch` and tolerated by the offline regression tests. Every `lag` prints as a
`LAG (Q66 class rule): <record> <- undrop <field>; registration <sha> not in solve <sha>; reproduces <key>`
line, so none is silent.

### 2.2 Addendum A1: the one refinement, and why it is not fitting to the result

With the seam row seeded, the first implementation measured **5**, not 4. The fifth record was
`CES-T80`: `dirty: true`, and its only changed file was its own FINDING doc. The declared fallback's
own rationale was "the tree may carry an uncommitted registration". A registration can live only in
`scenarios.py`. I narrowed the fallback back to that rationale, recorded the change in the PRECOMMIT
before the code commit, and pinned it with tests in both directions.

### 2.3 Tests, both directions (`tests/regression/test_key_provenance_exceptions.py`, 8 new, fast tier, 0.1 s)

These are synthetic, built from the live dataclass. The ancestry oracle and commit resolver are
injected, so no census, no commits and no network are needed.

| test | expectation | result |
|---|---|---|
| genuine lag record | classified `lag`, zero failures | pass |
| same record, perturbed literal | `G1_LAG_NO_REPRODUCE` | pass |
| payload lacks the field | `G1_UNKNOWN` | pass |
| field carried off its drop value | `G1_UNKNOWN` | pass |
| post-registration sha | `G1_UNKNOWN` | pass |
| no sha / dirty with unknown files / dirty touching scenarios.py | `G1_UNKNOWN` (each) | pass |
| dirty in docs only | classified `lag` | pass |
| undecidable ancestry | `G1_LAG_UNVERIFIED` | pass |
| table well-formed (registered fields, 40-char shas, no duplicates, cited) | holds | pass |

**Mutation proof that the tests can go red.** Each of these was checked against a restored copy.
Ignoring leg 3 → 1 red. Letting unverified pass as lag → 1 red. Ignoring the drop-value test in leg 1
→ 1 red (this mutation *first* survived, which is why the off-drop-value test exists). Ignoring the
dirty fallback → 1 red. Treating a post-registration sha as lag → 1 red. The `if anc is True:
continue` guard is **mutation-equivalent**: removing it alone changes nothing, because the later
`anc is False` test already excludes that case. I say so here rather than claim a test that proves
it. All 18 tests in the file pass, including the 7 census-backed slow ones.

## 3. PART 3 — THE G6 REGISTRATION: ALREADY ON `main` (Y-28, `bb749a94`), VERIFIED, NOT REDONE

Y-28 merged "register coal_mustrun_requires_measured_row in the cache key" at 2026-09-24T15:33Z,
after the charter's snapshot. At my HEAD the field is in `_CACHE_KEY_OPTIONAL_FIELDS` (line 2007) and
in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"` (line 2529). The dataclass default is `False`
(line 11885). G6 reads 0. **This lane made no `scenarios.py` edit.**

**Orphans.** 9 committed configs carry the field, all solved 2026-09-22 to 2026-09-24. **Every one has
`cache_key: null`**, so they are census "no key" rows and cannot mismatch. That makes **zero keyed
orphans.** I still added the row `{coal_mustrun_requires_measured_row, bb749a94}`. Its sha is known and
already merged, so there was no reason to defer it to "the lane's last act". A pinned shard still
solving on a pre-`bb749a94` sha will now produce a reported `lag` instead of a new G1.

**Cache-key pin tests, red before → red after, identical:** `test_persisted_identity.py` +
`test_cache_key_default_flip_guard.py` gave **6 failed / 28 passed** at base `3affcd71` and **6 failed
/ 28 passed** at my HEAD. All six are `test_solve_surface_fingerprint_is_pinned[CAISO, ERCOT, MISO,
NEISO, NYISO, PJM]`: the solve-surface fingerprint pins are stale. The census shows the cause:
`RGGI_MEMBER_STATES_BY_YEAR` is off its declaration in every ISO, and PJM's `CAP_AND_TRADE_PROGRAMS`,
`PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE` and `PJM_RGGI_ZONE_SHARE` have moved too. So **0** keys reproduce
under both constructions, where 138 did at `6640becc`. This lane touches none of it. **OWNER: pjm-h22,
which moved those rows (`da9fc148`, "RGGI inputs for 2020-2022", merged via PR #6574). It owes the pin
advance with a cause block, as Y-28 did.** Rule 28 does not fire (no new mechanism).

## 4. NAMED AND LEFT

* **Redundant listed entry.** `scn-ws5b-neiso/REF` is listed in `key-provenance-exceptions.json`
  (class `lag`, seam undrop) and **also** satisfies the class rule. The listed entry takes precedence,
  so nothing double-counts. Deleting it is the rule-26 tidy-up, but the exceptions record is not this
  lane's to edit. The other six listed `lag` entries (`caiso_offer_surface_measured_ungrounded`) are
  not covered: that field has no table row. **OWNER: the capx director / key-provenance desk (capx
  D85 / D91)** decides whether listed `lag` entries migrate to rows.
* **Offline cost.** In this blobless-promoted clone, `git rev-parse` of an **absent** 40-character sha
  costs about 4.7 s. The census path hits this only for unresolvable solve shas, which means the CLI
  and slow lane only. The fast-tier tests inject the resolver. No owner is needed unless it shows up
  in CI time.
* **The caiso row (`bbbf9b41`)**: see §1(b). **OWNER: the capx director.**

## 5. BOUNDARIES

Zero LP. No `ScenarioConfig` field added or changed. The exceptions record and the G6 baseline were
not edited. No surface-pin literal was re-pinned. Rule 27: every pushed file of 300 lines or more was
blob-verified after the push (see the PR).
