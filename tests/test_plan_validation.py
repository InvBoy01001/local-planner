from plan_validation import validate_final_plan
from schemas import Epic, FinalPlan, Story, Task


def test_valid_plan_has_no_warnings():
    plan = FinalPlan(
        epics=[
            Epic(
                title="Build",
                description="Build the system.",
                stories=[
                    Story(
                        id="E1-S1",
                        title="Foundation",
                        description="Create a foundation.",
                        tasks=[
                            Task(
                                id="E1-S1-T1",
                                title="Implement",
                                description="Implement the foundation.",
                            )
                        ],
                    )
                ],
            )
        ]
    )
    assert validate_final_plan(plan) == []


def test_validation_finds_dangling_and_self_dependencies():
    task = Task(
        id="E1-S1-T1",
        title="Implement",
        description="Implement it.",
        depends_on=["E1-S1-T1", "missing"],
    )
    story = Story(
        id="E1-S1",
        title="Story",
        description="Do the work.",
        depends_on=["E1-S1", "missing-story"],
        tasks=[task],
    )
    warnings = validate_final_plan(
        FinalPlan(epics=[Epic(title="Epic", description="Description", stories=[story])])
    )
    joined = "\n".join(warnings)
    assert "self-dependency" in joined
    assert "unknown or cross-epic" in joined
    assert "unknown or cross-story" in joined


def test_validation_finds_cycles():
    plan = FinalPlan(
        epics=[
            Epic(
                title="Epic",
                description="Description",
                stories=[
                    Story(id="E1-S1", title="One", description="One.", depends_on=["E1-S2"]),
                    Story(id="E1-S2", title="Two", description="Two.", depends_on=["E1-S1"]),
                ],
            )
        ]
    )
    assert any("cycle" in warning.lower() for warning in validate_final_plan(plan))
