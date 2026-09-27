import pytest
from pydantic import ValidationError

from schemas import FinalPlan, Task, UserQueryRequest


def test_mutable_defaults_are_isolated():
    first = FinalPlan()
    second = FinalPlan()
    first.gaps.append("one")
    assert second.gaps == []


def test_task_default_lists_are_isolated():
    first = Task(id="E1-S1-T1", title="A", description="B")
    second = Task(id="E1-S1-T2", title="A", description="B")
    first.depends_on.append("E1-S1-T0")
    assert second.depends_on == []


def test_query_rejects_too_short_value():
    with pytest.raises(ValidationError):
        UserQueryRequest(query="x")
