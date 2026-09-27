"""Pydantic request and response models for the planner API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserQueryRequest(BaseModel):
    """A fuzzy user objective that should be decomposed into an execution plan."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        ...,
        min_length=3,
        max_length=20_000,
        description="The user's initial fuzzy request.",
        examples=["Design a production-ready Django admin with RTL and dark mode."],
    )

    @field_validator("query")
    @classmethod
    def reject_whitespace_only_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must contain non-whitespace characters")
        return value


class SubTask(BaseModel):
    title: str
    description: str


class Task(BaseModel):
    id: str = Field(..., description="Globally unique task ID, e.g. E1-S1-T1.")
    title: str
    description: str
    depends_on: list[str] = Field(default_factory=list)
    sub_tasks: list[SubTask] = Field(default_factory=list)


class Story(BaseModel):
    id: str = Field(..., description="Globally unique story ID, e.g. E1-S1.")
    title: str
    description: str
    depends_on: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)


class Epic(BaseModel):
    title: str
    description: str
    stories: list[Story] = Field(default_factory=list)


class FinalPlan(BaseModel):
    user_role: str = ""
    expertise_level: str = ""
    original_domain: str = Field(
        default="",
        description="Broad domain bucket, such as Software & technology or People & HR.",
    )
    area: str = Field(default="", description="Specialization inside the broad domain.")
    sub_domain: str = Field(default="", description="Narrow focus for this request.")
    domain_summary: str = Field(
        default="",
        description="Short synthesis of goals, audience, constraints, and assumptions.",
    )
    technical_context: str = Field(
        default="",
        description="Named tools, platforms, stack, vendors, channels, or regulations.",
    )
    success_criteria: str = Field(
        default="",
        description="One-sentence definition of done for the generated plan.",
    )
    gaps: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Deterministic post-validation issues such as invalid dependencies.",
    )
    epics: list[Epic] = Field(default_factory=list)
