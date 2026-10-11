# Vendored: DABstep leaderboard scorer

- Source: https://huggingface.co/spaces/adyen/DABstep (`dabstep_benchmark/`)
- Space revision: `d4431c2e4a695cbe43c33aab2adaa304a37ae64a` (read 2026-10-12)
- License: Creative Commons Attribution 4.0 International, see `LICENSE` (copied from the Space).
- Copyright: © 2025 Alexander David Egg, Martin Iglesias Goyanes, Andreu Mora, Friso H. Kingma,
  Thomas Wolf, Leandro Von Werra (DABstep authors).

## What is included

Unmodified, at the original paths so the original relative imports work:

- `evaluation/scorer.py`: `question_scorer`, the function the leaderboard uses per task
- `tests/test_scorer.py`: the upstream scorer tests
- empty package `__init__.py` files

Not included: the Gradio app, leaderboard code, baseline agent.
