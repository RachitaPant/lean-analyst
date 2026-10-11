"""DABstep adapter: tasks, context files, the official scorer, and leaderboard submission files.

Data lives in data/dabstep/ (gitignored), downloaded in Phase A1 at a pinned dataset revision;
data/dabstep/MANIFEST.json holds the SHA-256 of every file. Set DABSTEP_DIR to use another copy.

Scoring uses the leaderboard's own `question_scorer`, vendored unmodified under
third_party/dabstep_benchmark (CC BY 4.0). Its quirks are pinned in tests/test_dabstep.py.

Never load data/submissions or data/task_scores from the HF dataset (see CLAUDE.md, leakage rule).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "third_party"))

from dabstep_benchmark.evaluation.scorer import question_scorer  # noqa: E402

DABSTEP_DIR = Path(os.environ.get("DABSTEP_DIR", ROOT / "data" / "dabstep"))
CONTEXT_DIR = DABSTEP_DIR / "data" / "context"
TASKS_DIR = DABSTEP_DIR / "data" / "tasks"
MANIFEST = DABSTEP_DIR / "MANIFEST.json"

SPLITS = {"dev": "dev.jsonl", "all": "all.jsonl"}
N_TASKS = {"dev": 10, "all": 450}

CONTEXT_FILES = (
    "payments.csv",
    "payments-readme.md",
    "manual.md",
    "fees.json",
    "merchant_data.json",
    "merchant_category_codes.csv",
    "acquirer_countries.csv",
)

# Leaderboard submission schema (app.py validate_submission): exactly these columns, all strings
SUBMISSION_FIELDS = ("task_id", "agent_answer", "reasoning_trace")


def data_available() -> bool:
    return all((CONTEXT_DIR / f).exists() for f in CONTEXT_FILES) and all(
        (TASKS_DIR / f).exists() for f in SPLITS.values()
    )


def verify_manifest() -> list[str]:
    """Return the files whose SHA-256 differs from MANIFEST.json (empty list = all good)."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = []
    for rel, meta in manifest["files"].items():
        path = DABSTEP_DIR / rel
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
            bad.append(rel)
    return bad


# ---------------------------------------------------------------- tasks

def load_tasks(split: str = "dev") -> list[dict]:
    """Tasks as dicts with task_id (str), question, guidelines, level, answer ('' when hidden)."""
    if split not in SPLITS:
        raise ValueError(f"split must be one of {sorted(SPLITS)}, got {split!r}")
    tasks = []
    with open(TASKS_DIR / SPLITS[split], encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                row["task_id"] = str(row["task_id"])
                row["answer"] = row.get("answer") or ""
                tasks.append(row)
    return tasks


# ---------------------------------------------------------------- context files
# Parsed once per process; callers get copies so an agent can't corrupt the cache.

@lru_cache(maxsize=None)
def _payments() -> pd.DataFrame:
    return pd.read_csv(CONTEXT_DIR / "payments.csv")


@lru_cache(maxsize=None)
def _json(name: str) -> Any:
    return json.loads((CONTEXT_DIR / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _csv_dropping_index(name: str) -> pd.DataFrame:
    # merchant_category_codes.csv and acquirer_countries.csv carry a junk unnamed index column
    df = pd.read_csv(CONTEXT_DIR / name)
    return df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")])


def load_payments() -> pd.DataFrame:
    return _payments().copy()


def load_fees() -> list[dict]:
    return json.loads(json.dumps(_json("fees.json")))


def load_merchants() -> list[dict]:
    return json.loads(json.dumps(_json("merchant_data.json")))


def load_mcc() -> pd.DataFrame:
    return _csv_dropping_index("merchant_category_codes.csv").copy()


def load_acquirer_countries() -> pd.DataFrame:
    return _csv_dropping_index("acquirer_countries.csv").copy()


def read_doc(name: str = "manual.md") -> str:
    if name not in ("manual.md", "payments-readme.md"):
        raise ValueError(f"not a document: {name!r}")
    return (CONTEXT_DIR / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------- answers and scoring

def format_answer(answer: Any) -> str:
    """Turn an agent's final_answer value into the string the leaderboard compares."""
    if answer is None:
        return ""
    if isinstance(answer, bool):
        return str(answer)
    if isinstance(answer, (list, tuple, set)):
        return ", ".join(format_answer(a) for a in answer)
    if callable(getattr(answer, "tolist", None)):  # numpy scalar/array, pandas Series/Index
        return format_answer(answer.tolist())
    return str(answer).strip()


def score(agent_answer: Any, truth: str) -> bool:
    """Official per-task score: True if the leaderboard would count the answer correct."""
    return bool(question_scorer(format_answer(agent_answer), str(truth)))


def score_tasks(answers: Mapping[str, Any], tasks: Iterable[dict]) -> list[dict]:
    """Score answers against labelled tasks; a missing answer scores False."""
    rows = []
    for t in tasks:
        if not t.get("answer"):
            raise ValueError(f"task {t['task_id']} has no label")
        given = format_answer(answers.get(t["task_id"]))
        rows.append({
            "task_id": t["task_id"],
            "level": t["level"],
            "agent_answer": given,
            "answer": t["answer"],
            "score": t["task_id"] in answers and score(given, t["answer"]),
        })
    return rows


# ---------------------------------------------------------------- submission files

def write_submission(
    answers: Mapping[str, Any],
    path: str | Path,
    traces: Mapping[str, str] | None = None,
    split: str = "all",
) -> Path:
    """Write a leaderboard JSONL. Refuses if any task of the split is missing (the leaderboard
    rejects partial files) or if answers name unknown tasks."""
    expected = [t["task_id"] for t in load_tasks(split)]
    answers = {str(k): v for k, v in answers.items()}
    missing = [tid for tid in expected if tid not in answers]
    unknown = sorted(set(answers) - set(expected))
    if missing or unknown:
        raise ValueError(f"submission incomplete: {len(missing)} missing (e.g. {missing[:5]}), "
                         f"{len(unknown)} unknown (e.g. {unknown[:5]})")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for tid in expected:
            row = {"task_id": tid, "agent_answer": format_answer(answers[tid])}
            if traces is not None:
                row["reasoning_trace"] = str(traces.get(tid, ""))
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def validate_submission(path: str | Path) -> list[str]:
    """Re-check a written file the way the leaderboard's validate_submission does."""
    errors = []
    df = pd.read_json(path, lines=True, dtype=str)
    for col in ("task_id", "agent_answer"):
        if col not in df.columns:
            errors.append(f"missing column {col}")
    extra = [c for c in df.columns if c not in SUBMISSION_FIELDS]
    if extra:
        errors.append(f"unexpected columns {extra}")
    if df.isnull().values.any():
        errors.append("NaN values")
    if df["task_id"].duplicated().any():
        errors.append("duplicate task_id")
    return errors
