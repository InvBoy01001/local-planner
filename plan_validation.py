"""Deterministic validation for generated planning graphs."""

from __future__ import annotations

from collections import Counter

from schemas import FinalPlan


def _looks_truncated(text: str | None) -> bool:
    if text is None:
        return True
    value = text.strip()
    if not value:
        return True
    if value.count("```") % 2 == 1:
        return True
    if value.endswith("`") and value.count("`") == 1:
        return True
    tail = value[-24:].lower()
    return tail.endswith(("cmd [", "hooks:", "from "))


def _cycle_nodes(graph: dict[str, list[str]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            cycles.add(node)
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            if dependency in graph:
                if dependency in visiting:
                    cycles.update({node, dependency})
                else:
                    visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def validate_final_plan(plan: FinalPlan) -> list[str]:
    """Return human-readable warnings; an empty list means no detected issue."""
    warnings: list[str] = []
    story_ids: list[str] = []
    task_ids: list[str] = []
    story_graph: dict[str, list[str]] = {}
    task_graph: dict[str, list[str]] = {}

    for epic_index, epic in enumerate(plan.epics, start=1):
        local_story_ids = {story.id for story in epic.stories}
        for story_index, story in enumerate(epic.stories, start=1):
            story_ids.append(story.id)
            story_graph[story.id] = story.depends_on
            if _looks_truncated(story.title) or _looks_truncated(story.description):
                warnings.append(
                    f"Epic {epic_index} story {story_index} ({story.id!r}): title or description may be truncated."
                )
            if story.id in story.depends_on:
                warnings.append(f"Story {story.id!r}: invalid self-dependency.")
            dangling_story = sorted(set(story.depends_on) - local_story_ids)
            if dangling_story:
                warnings.append(
                    f"Story {story.id!r}: unknown or cross-epic dependency id(s): {', '.join(dangling_story)}."
                )

            local_task_ids = {task.id for task in story.tasks}
            for task_index, task in enumerate(story.tasks, start=1):
                task_ids.append(task.id)
                task_graph[task.id] = task.depends_on
                if task.id in task.depends_on:
                    warnings.append(f"Task {task.id!r}: invalid self-dependency.")
                dangling_task = sorted(set(task.depends_on) - local_task_ids)
                if dangling_task:
                    warnings.append(
                        f"Task {task.id!r}: unknown or cross-story dependency id(s): {', '.join(dangling_task)}."
                    )
                if _looks_truncated(task.title) or _looks_truncated(task.description):
                    warnings.append(
                        f"Epic {epic_index} story {story.id!r} task {task_index} ({task.id!r}): "
                        "title or description may be truncated."
                    )
                for sub_index, subtask in enumerate(task.sub_tasks, start=1):
                    if _looks_truncated(subtask.title) or _looks_truncated(subtask.description):
                        warnings.append(
                            f"Sub-task epic {epic_index} / {task.id!r} / #{sub_index}: may be truncated."
                        )

    duplicate_stories = sorted({item for item, count in Counter(story_ids).items() if count > 1})
    if duplicate_stories:
        warnings.append(f"Duplicate story id(s): {', '.join(duplicate_stories)}")

    duplicate_tasks = sorted({item for item, count in Counter(task_ids).items() if count > 1})
    if duplicate_tasks:
        warnings.append(f"Duplicate task id(s): {', '.join(duplicate_tasks)}")

    story_cycles = sorted(_cycle_nodes(story_graph))
    if story_cycles:
        warnings.append(f"Story dependency cycle detected around: {', '.join(story_cycles)}")

    task_cycles = sorted(_cycle_nodes(task_graph))
    if task_cycles:
        warnings.append(f"Task dependency cycle detected around: {', '.join(task_cycles)}")

    return warnings
