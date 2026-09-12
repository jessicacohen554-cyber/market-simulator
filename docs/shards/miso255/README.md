# miso-255 shard records — rescued under rule 33 `[R-SHARD-ARCHIVE]` (f)(1)

Seven shard reports, copied verbatim off their shard branches onto the parent branch **before any
archiving or branch deletion**, because a shard's own report exists nowhere else. Each is recorded
against the **full immutable SHA** it was taken from, never a branch name — rule 33(d), which
exists because shard branches rebase, force-push and are auto-deleted within minutes.

| file | year / gen | source SHA | branch (may already be gone) |
|---|---|---|---|
| `SHARD-miso255-sil-2021d.md` | 2021 D | `be5528b450f9ae36a5083d696a8562b295672826` | `claude/miso255-sil-2021d` |
| `SHARD-miso255-sil-2022d.md` | 2022 D | `a2354f3a699bb4941a0a2d8397a363bb5351992b` | `claude/miso255-sil-2022d` |
| `SHARD-miso255-sil-2023d.md` | 2023 D | `1403c3ecbd1e5e32be722d986bfb2fff6d068de5` | `claude/miso255-sil-2023d` |
| `SHARD-miso255-sil-2024d.md` | 2024 D | `7e09eee3e0bd12a786b6dd919842b5307c8796cf` | `claude/miso255-sil-2024d` |
| `SHARD-miso255-sil-2025d.md` | 2025 D | `a690790da2f0e34e3587df315a0fd113a27847f8` | `claude/miso255-sil-2025d` |
| `SHARD-miso255-sil-2022c.md` | 2022 C | `39860b4dee107c049c7b7467b0ba47ed2efbdc5e` | `claude/miso255-sil-2022c` |
| `SHARD-miso255-sil-2024c.md` | 2024 C | `5f7662f6a9fbc10c6e37c6aae469a73d5d300d53` | `claude/miso255-sil-2024c` |

**The D reports are the miso-255 screen's evidence** — gate-scorer JSON, the G-1 liveness marker,
preflight and memory-peak lines, phase timings. The C reports are *stopped-before-solve* records
(a 20 GiB disk floor that was the parent's miscalibration); they carry **no solve data** and must
never be read as results.

## THE BUNDLES ARE **NOT** HERE, AND THAT IS WHY THE D SHARDS ARE STILL ALIVE

The five `results/calibration/miso255_sil_<year>/` bundles were **gitignored by design** (rule 29
`[R-SCREEN]` (c) as amended by rule 31 `[R-RETAIN]`: keep a screen bundle out of `main`, never
`rm` it), so they were never pushed and exist **only on the five D shard containers' local disks**.

Rule 33(a)'s archive trigger is that the parent has *(i) fetched the branch, (ii) checked out the
bundle, (iii) verified it*. **Only (i) holds.** Rule 33(a) is explicit about what follows: *"Until
all three hold, the shard stays alive: it is the only thing that can re-push what it solved."*
Archiving them would release their containers and destroy the bundles — and with the promotion
question still open, that is the ercot-255 incident (rule 31) with extra steps.

So the five D shards are **deliberately left alive**, named here and in the session's final report
per rule 33(e). They are archived the moment either the owner rules on promotion, or their bundles
are recovered.

**If the bundles are lost anyway** (container reclamation beats the ruling), the recovery route is
**not** a checkout — it is a re-solve of the affected years at ~11-15 min each (measured D-generation
wall times: 911.4 / 738.3 / 639.6 / 687.4 / 741.1 s), on pin
`d0fec486fa2218afc55dbd2eb377bc2570e61699`, with `--set miso_import_sil_measured_envelope=true`
against the controls named in `docs/RESULT-miso255-measured-sil-2026-09-12.md`. Rule 33(f)(4): this
line is stated honestly rather than keeping a `git checkout` command that would fail.
