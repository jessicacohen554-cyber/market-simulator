"""Cross-cutting, dependency-light helpers shared across the package.

Modules here sit at the bottom of the import graph: they depend only on
``config`` (and third-party numerics), never on ``data`` / ``model`` /
``results``, so any layer may import them without risking a cycle.
"""
