# ADDENDUM — pjm-h10: the PJM replay SETUP CHAIN, and why four shards died on it (2026-09-19)

**Session:** pjm-h10 · **Parent finding:** `docs/FINDING-pjm-h10-the-energy-identity-2026-09-19.md`
**Why this is a separate document:** it is not about PJM's calibration. It is about **rule 32
`[R-SHARD]` (c)'s documented launch recipe being incomplete**, which cost this session four shard
containers and is going to cost every other lane the same until it is written down.

---

## 1. What happened

Four shards were launched to replay the two committed PJM bundles at a pinned SHA. None produced a
bundle. The failures were **not** model failures, **not** memory, and **not** the emissions dual —
they were environment setup, and **two of the four were caused by an instruction I wrote.**

| # | session | outcome |
|---|---|---|
| 1 | `session_01GVm2g4rPYhEHZT6kRmiB3S` | ended its turn after preflight, mid-solve; later resumed into env setup; archived |
| 2 | `session_01WiG8kSC7zZRG9R6xb85HJp` | began regenerating the clean tree (**correctly**), ended its turn; archived |
| 3 | `session_01FKXs8PaaohGkVSsYJTp6gK` | solve **died at 59 s on missing `data/clean`** — which my prompt had forbidden it to rebuild |
| 4 | `session_01HSskC9q1YEKBMcv9RydYHr` | same generation, same blocker |
| 5 | `session_013WuzZpNy1yBLDuXVVN8AcT` | relaunched with the clean-tree step required (`claude/pjm-h10-mer-a3`) |
| 6 | `session_01DG8713GuWS33fC7aJybGoW` | same, holdout span (`claude/pjm-h10-mer-tp3`) |

**Shard 2 was right and my prompt overrode it.** It independently decided to regenerate the clean
tree; generation 2's prompt then explicitly forbade exactly that, on my assumption that the raw tree
was sufficient. It is not.

---

## 2. The complete chain a PJM keeper replay actually needs

Rule 32 `[R-SHARD]` (c)(2) documents **one** setup step — *"the prompt names the `DATA PROFILE` so the
shard hydrates only its own ISO's subtree"*. For a PJM per-plant replay there are **four**, and each
one is load-bearing:

### (a) `python3 scripts/hydrate_data.py --profile pjm`
Documented, and necessary. In a **full** clone it is a no-op and says so.

### (b) Install the Python dependencies — with a PyYAML workaround
A bare `pip install -r requirements.txt` **fails** on this image:

    ERROR: Cannot uninstall PyYAML 6.0.1, RECORD file not found. Hint: The package was
    installed by debian.

The working form is `pip install --ignore-installed PyYAML -r requirements.txt`. Worth naming in the
prompt, because the failure looks like a broken requirements file rather than a Debian-packaged
distribution without install metadata.

### (c) **`python3 scripts/regenerate_clean.py`** — REQUIRED, and this is the one that killed shards 3 and 4
`data/clean` is gitignored, derived and disposable, so **it is never in a fresh clone**. The script's
own docstring is unambiguous:

> *"The `data/clean` tree is gitignored (derived and disposable), so it must be rebuilt from
> `data/raw` before the model — or CI — can read it through `scripts.lib.clean_io.read_clean`."*

`MARKET_SIM_USE_CLEAN` is a red herring. It is default-OFF and unset, and the keeper's own
`run_config.json` records no value for it — but that switch governs only the *optional* clean-backed
read paths (`campd`, `zone_assignment`). **Several loaders read `read_clean(...)` unconditionally**,
with no env gate at all: `data/ramp_capability.py`, `data/maxgen_events.py`,
`data/reserve_requirements.py`, `data/capacity_deliverability.py`, `data/nyiso_seam_envelope.py`,
`data/confirmed_retirements.py`. And `scripts/lib/clean_io.py:548/579` raises with the instruction to
*"regenerate from raw — via `scripts/regenerate_clean.py`"*.

So: **the clean tree is a hard prerequisite of any solve, on every ISO, and rule 32(c) does not say
so.** A failure in one datatype does not stop the others (the script is per-datatype and independent),
so a partial failure is not automatically fatal — read it and continue.

### (d) **`python scripts/fetch_pjm_da_virtuals.py`** — REQUIRED for PJM, and it re-downloads
The keeper runs `pjm_da_virtual_bids = True`, which reads
`data/raw/pjm-da-virtuals/hrl_da_incs_decs_<year>_<month>.parquet`. **That directory is gitignored for
licensing reasons** — PJM DataMiner2 carries a non-member redistribution restriction
(`docs/data-licensing.md` §4) — so only its `README.md` is tracked and **the payload is in no clone, in
no container, ever.** Recovery is re-fetch only.

Two traps in it:

* the default fetch is **2023–2025**, so a **2020–2022** replay needs
  `--years 2020 2021 2022` explicitly, and whether DataMiner2 still serves those months is
  **unverified** — nobody has tested it, and a holdout-span replay may simply not be reproducible
  from a cold container;
* `hrl_da_incs_decs` is posted monthly on a **four-month delay**, so the newest months of a current
  year may be absent regardless.

Shard 1 discovered this on its own ("fetching PJM DA virtuals (36mo)") — 36 months is the 2023–2025
default, i.e. it had the training span and would still have been short for the holdout span.

### What is NOT needed, checked so nobody over-fetches
Six other PJM-relevant corpora are also README-only at tip, and **none is required to solve**:
`pjm-energy-offers` (only to *re-derive* the midcurve surface; the surface itself,
`_validation-source/pjm_offer_midcurve_condbinned.json`, is committed), `pjm-zonal-lmp`,
`pjm-binding-constraints`, `pjm-ehv-lmp`, `lmp-components`, `PJM/`. The loss surface reads
`data/raw/iso-specific-transmission/PJM_loss_surface.csv`, which **is** committed.

---

## 3. The other failure mode, which is about how CCR shards yield

Shards 1 and 2 ended their turns **mid-task** — one right after printing "starting the LP solve". A
CCR session that yields mid-solve does not reliably resume: both sat `IDLE` with `updated_at` frozen
for ~25 minutes.

**And the parent cannot steer them.** There is **no cross-session messaging route from a CCR parent to
a CCR shard** in this environment:

* `SendMessage` with the session id → *"No agent named '…' is reachable"*; with the session title →
  the same; `ListAgents` → *"No reachable agents — no other Claude session is running on this
  machine"* (a CCR shard runs on its **own** container, so it is never "on this machine");
* the `Claude_Code_Remote` MCP surface exposes `create_session`, `interrupt_session`,
  `archive_session` — and **no `send_message`**, although `create_session`'s own description says
  *"Combine with send_message for fan-out orchestration"*. `ToolSearch` for it returns nothing.

**Consequence for rule 32 `[R-SHARD]` (c): a shard prompt is the ONLY channel there will ever be.** It
cannot be corrected, extended or nudged after launch. Two concrete duties follow:

1. **Say that the turn must not end while the solve is running** — background job plus an in-turn poll
   loop (`sleep`; `tail` the log; `kill -0` the pid) until it exits. Clause (c)(5) already says to
   report in numbers *because* the parent may never read the shard's disk; this is the same fact one
   step earlier.
2. **Do not put a setup step on the FORBIDDEN list unless you have verified it is unnecessary.** A
   forbidden-list entry is unappealable from inside the shard. Mine ("do not regenerate the clean
   data tree", `scripts/regenerate_clean.py` named under FORBIDDEN) converted a 30-second setup step
   into two dead containers.

---

## 4. Proposed amendment to rule 32 `[R-SHARD]` (c) — for the owner, not self-applied

Not written into `CLAUDE.md` by this session: rule 32 is governance and the owner amends it.
Recommended, as a new clause (c)(9) or an extension of (c)(2):

> **(c)(9) A SHARD PROMPT CARRIES THE WHOLE SETUP CHAIN, NOT JUST THE DATA PROFILE, AND NAMES NO
> SETUP STEP AS FORBIDDEN.** Hydration is necessary and not sufficient. A solve also needs the
> dependency install, **`scripts/regenerate_clean.py`** (the `data/clean` tree is gitignored and
> several loaders read it with no env gate, so it is never present in a fresh container), and any
> **licensing-gitignored corpus the run's own config reads** — for PJM with
> `pjm_da_virtual_bids` armed that is `scripts/fetch_pjm_da_virtuals.py`, with `--years` matching the
> bundle's span, since the default covers 2023–2025 only. **A shard's turn may not end while its
> solve is running**, and the prompt says so: background job plus an in-turn poll loop, because the
> parent has no way to message it afterwards.

**Open question the owner may want answered before the next holdout replay is chartered:** whether
DataMiner2 still serves `hrl_da_incs_decs` for 2020–2022 at all. If it does not, then **the PJM
2020–2022 touchpoint is not reproducible from a cold container**, and that is a retention problem in
the class `docs/FINDING-history-rewrite-2026-08-16.md` already names — a committed bundle whose inputs
cannot be re-obtained. Nothing in this session tested it.

---

## 5. What this cost, stated plainly

Four containers and roughly 45 minutes of wall clock produced **no MER bundle**. The zero-LP
reconciliation this session was chartered for is complete and committed regardless — it needed no
solve. The MER series PJM owes the marginal-abatement page, and the empirical check on the G-DRIFT
form-4 verdict, **remain outstanding**, and the generation-3 shards may or may not clear step (d).
Cost to reproduce from here: one shard per span, ~10–20 min of setup plus the span's solve, **provided
the DA-virtuals fetch works for that span.**
