# Conventions

## Naming

- Python files use `snake_case.py`; frontend files use `kebab-case`.
- Public functions follow `verb_noun` naming (e.g. `load_fleet`, `solve_dispatch`).
- Single-letter variables are allowed only for `t`, `g`, `z`, `s` in LP
  construction, and each must carry a comment explaining the index.
- Constants live in `config/constants.py`, each with a citation comment
  identifying its source.

## Git

- Feature branches follow `phase-N/description`.
- Commit messages use the imperative present tense (e.g. "Add fleet loader").

## Documentation

- Every public function needs a docstring.

## Data

- Raw data in `data/` is never modified in place.
