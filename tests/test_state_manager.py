import pytest

pytest.importorskip("ollama")

import state_manager
from schemas import UserQueryRequest


@pytest.mark.asyncio
async def test_planner_assigns_canonical_ids_and_valid_dependencies(monkeypatch):
    async def fake_consensus(prompt, required_keys, **kwargs):
        key = required_keys[0]
        if key == "original_domain":
            return {
                "original_domain": "Software & technology",
                "area": "Backend services",
                "sub_domain": "Local planning agent",
                "domain_summary": "A local planning service.",
                "technical_context": "FastAPI, Ollama",
                "success_criteria": "Return a validated plan.",
            }
        if key == "user_role":
            return {"user_role": "Developer"}
        if key == "expertise_level":
            return {"expertise_level": "Intermediate"}
        if key == "gaps":
            return {"gaps": []}
        if key == "epics":
            return {
                "epics": [
                    {"title": "Foundation", "description": "Build foundations."},
                    {"title": "Implementation", "description": "Implement behavior."},
                    {"title": "Verification", "description": "Test and harden."},
                ]
            }
        if key == "stories":
            return {
                "stories": [
                    {"id": "S1", "title": "One", "description": "First story.", "depends_on": []},
                    {"id": "S2", "title": "Two", "description": "Second story.", "depends_on": ["S1"]},
                    {"id": "S3", "title": "Three", "description": "Third story.", "depends_on": ["S2"]},
                ]
            }
        if key == "tasks":
            # The canonical story id is embedded in the task prompt.
            story_id = next(
                token.strip('"')
                for token in prompt.split()
                if token.strip('"').startswith("E") and "-S" in token and "-T" not in token
            )
            return {
                "tasks": [
                    {"id": f"{story_id}-T1", "title": "One", "description": "First task.", "depends_on": []},
                    {"id": f"{story_id}-T2", "title": "Two", "description": "Second task.", "depends_on": [f"{story_id}-T1"]},
                    {"id": f"{story_id}-T3", "title": "Three", "description": "Third task.", "depends_on": [f"{story_id}-T2"]},
                ]
            }
        if key == "sub_tasks":
            return {
                "sub_tasks": [
                    {"title": "Prepare", "description": "Prepare inputs."},
                    {"title": "Execute", "description": "Execute the change."},
                    {"title": "Verify", "description": "Verify the result."},
                ]
            }
        raise AssertionError(required_keys)

    monkeypatch.setattr(state_manager, "generate_with_consensus", fake_consensus)
    plan = await state_manager.PlannerStateManager(
        UserQueryRequest(query="Build a local planner service")
    ).build_plan()

    assert [story.id for story in plan.epics[0].stories] == ["E1-S1", "E1-S2", "E1-S3"]
    assert plan.epics[0].stories[1].depends_on == ["E1-S1"]
    assert [task.id for task in plan.epics[0].stories[0].tasks] == [
        "E1-S1-T1",
        "E1-S1-T2",
        "E1-S1-T3",
    ]
    assert plan.epics[0].stories[0].tasks[1].depends_on == ["E1-S1-T1"]
    assert plan.validation_warnings == []
