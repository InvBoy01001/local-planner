"""Planner orchestration: classify, decompose, expand, and validate."""

from __future__ import annotations

import asyncio
import logging

import prompts
from ollama_client import generate_with_consensus
from plan_validation import validate_final_plan
from query_utils import normalize_user_query
from schemas import Epic, FinalPlan, Story, SubTask, Task, UserQueryRequest

logger = logging.getLogger(__name__)

_DOMAIN_KEYS = [
    "original_domain",
    "area",
    "sub_domain",
    "domain_summary",
    "technical_context",
    "success_criteria",
]


def _remap_dependencies(raw: list[str] | object, mapping: dict[str, str]) -> list[str]:
    if not isinstance(raw, list):
        return []
    remapped: list[str] = []
    for dependency in raw:
        if not isinstance(dependency, str):
            continue
        canonical = mapping.get(dependency, dependency)
        if canonical not in remapped:
            remapped.append(canonical)
    return remapped


class PlannerStateManager:
    """Owns one planning request and its in-memory plan state."""

    def __init__(self, request: UserQueryRequest):
        self.query = normalize_user_query(request.query)
        self.plan = FinalPlan()

    def _domain_brief(self) -> str:
        return prompts.format_domain_brief(
            self.plan.original_domain,
            self.plan.area,
            self.plan.sub_domain,
            self.plan.domain_summary,
            self.plan.technical_context,
            self.plan.success_criteria,
        )

    async def build_plan(self) -> FinalPlan:
        logger.info("Phase 1/3: classifying request domain")
        domain_data = await generate_with_consensus(
            prompts.get_domain_prompt(self.query),
            _DOMAIN_KEYS,
            temperature=0.2,
            max_attempts=8,
            k=1,
        )
        for key in _DOMAIN_KEYS:
            setattr(self.plan, key, str(domain_data.get(key, "") or ""))

        domain_brief = self._domain_brief()
        logger.info("Phase 2/3: inferring role, expertise, and gaps")
        role_task = generate_with_consensus(
            prompts.get_role_prompt(self.query, domain_brief), ["user_role"]
        )
        level_task = generate_with_consensus(
            prompts.get_level_prompt(self.query, domain_brief), ["expertise_level"]
        )
        gap_task = generate_with_consensus(
            prompts.get_gap_prompt(self.query, domain_brief),
            ["gaps"],
            list_lengths={"gaps": (0, 5)},
            max_attempts=8,
        )
        role_data, level_data, gap_data = await asyncio.gather(
            role_task, level_task, gap_task
        )
        self.plan.user_role = str(role_data.get("user_role", "") or "")
        self.plan.expertise_level = str(level_data.get("expertise_level", "") or "")
        raw_gaps = gap_data.get("gaps", [])
        self.plan.gaps = (
            [item.strip() for item in raw_gaps if isinstance(item, str) and item.strip()]
            if isinstance(raw_gaps, list)
            else []
        )

        logger.info("Phase 3/3: expanding epics, stories, tasks, and sub-tasks")
        epic_data = await generate_with_consensus(
            prompts.get_epic_prompt(self.query, domain_brief, self.plan.expertise_level),
            ["epics"],
        )

        prior_epic_summaries: list[str] = []
        for epic_index, epic_data_item in enumerate(epic_data["epics"], start=1):
            epic = Epic(
                title=str(epic_data_item.get("title", "")),
                description=str(epic_data_item.get("description", "")),
            )
            story_data = await generate_with_consensus(
                prompts.get_story_prompt(
                    epic.title,
                    epic.description,
                    self.query,
                    self.plan.expertise_level,
                    domain_brief,
                    prior_epic_summaries,
                ),
                ["stories"],
            )

            raw_stories = story_data["stories"]
            story_id_map: dict[str, str] = {}
            for index, item in enumerate(raw_stories, start=1):
                raw_id = str(item.get("id", f"S{index}"))
                story_id_map.setdefault(raw_id, f"E{epic_index}-S{index}")

            for story_index, story_item in enumerate(raw_stories, start=1):
                story_id = f"E{epic_index}-S{story_index}"
                story = Story(
                    id=story_id,
                    title=str(story_item.get("title", "")),
                    description=str(story_item.get("description", "")),
                    depends_on=_remap_dependencies(
                        story_item.get("depends_on", []), story_id_map
                    ),
                )

                task_data = await generate_with_consensus(
                    prompts.get_task_prompt(
                        story_id,
                        story.title,
                        story.description,
                        epic.title,
                        self.query,
                        self.plan.expertise_level,
                        domain_brief,
                        prior_epic_summaries,
                    ),
                    ["tasks"],
                )
                raw_tasks = task_data["tasks"]
                task_id_map: dict[str, str] = {}
                for index, item in enumerate(raw_tasks, start=1):
                    raw_id = str(item.get("id", f"T{index}"))
                    task_id_map.setdefault(raw_id, f"{story_id}-T{index}")

                for task_index, task_item in enumerate(raw_tasks, start=1):
                    task_id = f"{story_id}-T{task_index}"
                    task = Task(
                        id=task_id,
                        title=str(task_item.get("title", "")),
                        description=str(task_item.get("description", "")),
                        depends_on=_remap_dependencies(
                            task_item.get("depends_on", []), task_id_map
                        ),
                    )
                    subtask_data = await generate_with_consensus(
                        prompts.get_subtask_prompt(
                            task.title,
                            task.description,
                            self.query,
                            domain_brief,
                        ),
                        ["sub_tasks"],
                        temperature=0.2,
                        num_predict=768,
                    )
                    task.sub_tasks.extend(
                        SubTask(
                            title=str(item.get("title", "")),
                            description=str(item.get("description", "")),
                        )
                        for item in subtask_data["sub_tasks"]
                    )
                    story.tasks.append(task)
                epic.stories.append(story)

            summary = epic.description.strip()
            if len(summary) > 240:
                summary = summary[:237] + "..."
            prior_epic_summaries.append(f"{epic.title}: {summary}")
            self.plan.epics.append(epic)

        self.plan.validation_warnings = validate_final_plan(self.plan)
        return self.plan


# Backward-compatible import name for older consumers of the prototype.
AragStateManager = PlannerStateManager
