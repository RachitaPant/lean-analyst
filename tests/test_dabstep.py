"""Offline checks of agent/dabstep.py. No network, no LLM.

Scorer cases pin the leaderboard's behaviour as we observed it (Phase A1), including its quirks,
so C2's answer formatter can rely on them. Tests that need data/dabstep/ (gitignored) skip when
it is absent, e.g. in CI.
"""

import json

import numpy as np
import pandas as pd
import pytest

from agent import dabstep
from agent.dabstep import format_answer, score

needs_data = pytest.mark.skipif(not dabstep.data_available(), reason="data/dabstep not downloaded")


# ---------------------------------------------------------------- scorer (no data needed)

@pytest.mark.parametrize("given, truth, expected", [
    # numbers: adaptive tolerance
    ("0.120132", "0.120132", True),
    ("0.12013", "0.120132", True),        # both < 1: isclose(abs 1e-4)
    ("0.1203", "0.120132", False),
    ("13.57", "13.5712", True),           # rounded to the fewer decimals
    ("13.58", "13.5712", False),
    ("10,765", "10765", True),
    ("12 transactions", "12", True),      # first number extracted
    # strings
    ("nl", "NL", True),
    ("Netherlands", "NL", False),
    ("Not Applicable", "Not Applicable", True),
    ("not applicable.", "Not Applicable", True),
    ("B. BE", "B. BE", True),
    ("A. BE", "B. BE", False),            # option letter matters
    # lists: order-free, separator-free
    ("286, 477, 741", "741, 477, 286", True),
    ("[286; 477; 741]", "741, 477, 286", True),
    ("286, 477", "741, 477, 286", False),
    ("", "", True),
])
def test_scorer_cases(given, truth, expected):
    assert score(given, truth) is expected


@pytest.mark.parametrize("given, truth", [
    ("0.948103", "-0.94810300000017"),    # the minus sign is ignored
    ("F:13.57", "E:13.57"),               # 'label:number' compared by number only
])
def test_scorer_known_leniencies(given, truth):
    """Upstream quirks: these count as correct on the leaderboard. Our own evals use the same
    scorer, so don't 'fix' them here; C2 must still produce the exact intended answer."""
    assert score(given, truth)


@pytest.mark.parametrize("value, expected", [
    (None, ""),
    (True, "True"),
    (["a", "b"], "a, b"),
    ((1, 2.5), "1, 2.5"),
    (np.int64(7), "7"),
    (np.float64(0.25), "0.25"),
    (np.array([3, 4]), "3, 4"),
    (pd.Series(["x", "y"]), "x, y"),
    ("  NL \n", "NL"),
])
def test_format_answer(value, expected):
    assert format_answer(value) == expected


# ---------------------------------------------------------------- data-backed

@needs_data
def test_manifest_hashes_match():
    assert dabstep.verify_manifest() == []


@needs_data
@pytest.mark.parametrize("split", ["dev", "all"])
def test_task_counts_and_fields(split):
    tasks = dabstep.load_tasks(split)
    assert len(tasks) == dabstep.N_TASKS[split]
    assert len({t["task_id"] for t in tasks}) == len(tasks)
    assert {t["level"] for t in tasks} == {"easy", "hard"}
    assert all(isinstance(t["task_id"], str) and t["question"] for t in tasks)


@needs_data
def test_all_split_has_no_answers_dev_has_all():
    assert not any(t["answer"] for t in dabstep.load_tasks("all"))
    assert all(t["answer"] for t in dabstep.load_tasks("dev"))


@needs_data
def test_dev_answers_score_one_against_themselves():
    dev = dabstep.load_tasks("dev")
    rows = dabstep.score_tasks({t["task_id"]: t["answer"] for t in dev}, dev)
    assert all(r["score"] for r in rows)


@needs_data
def test_missing_answer_scores_zero():
    dev = dabstep.load_tasks("dev")
    rows = dabstep.score_tasks({}, dev)
    assert not any(r["score"] for r in rows)  # includes task 70, whose truth is not ""


@needs_data
def test_context_loaders():
    p = dabstep.load_payments()
    assert p.shape == (138236, 21)
    p.drop(columns=["merchant"], inplace=True)        # mutating a copy ...
    assert "merchant" in dabstep.load_payments().columns  # ... leaves the cache intact
    fees = dabstep.load_fees()
    assert len(fees) == 1000
    fees[0]["rate"] = -1
    assert dabstep.load_fees()[0]["rate"] != -1
    assert len(dabstep.load_merchants()) == 30
    assert list(dabstep.load_mcc().columns) == ["mcc", "description"]
    assert list(dabstep.load_acquirer_countries().columns) == ["acquirer", "country_code"]
    assert "fixed_amount" in dabstep.read_doc("manual.md")
    with pytest.raises(ValueError):
        dabstep.read_doc("../../secrets")


@needs_data
def test_submission_roundtrip(tmp_path):
    tasks = dabstep.load_tasks("all")
    answers = {t["task_id"]: ["a", "b"] if i == 0 else 1.5 for i, t in enumerate(tasks)}
    path = dabstep.write_submission(answers, tmp_path / "sub.jsonl",
                                    traces={tasks[0]["task_id"]: "step 1"})
    assert dabstep.validate_submission(path) == []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 450
    assert rows[0] == {"task_id": tasks[0]["task_id"], "agent_answer": "a, b", "reasoning_trace": "step 1"}
    assert all(isinstance(v, str) for r in rows for v in r.values())


@needs_data
def test_submission_refuses_partial(tmp_path):
    tasks = dabstep.load_tasks("all")
    answers = {t["task_id"]: "x" for t in tasks[:-1]}
    with pytest.raises(ValueError, match="1 missing"):
        dabstep.write_submission(answers, tmp_path / "sub.jsonl")
    with pytest.raises(ValueError, match="unknown"):
        dabstep.write_submission({**answers, tasks[-1]["task_id"]: "x", "nope": "x"}, tmp_path / "s.jsonl")
