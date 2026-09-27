# prompts.py

BASE_RULES = """
RULES:
1. Output ONLY valid JSON. No markdown code fences (no triple backticks) anywhere in the output.
2. Tone must be professional, objective, and specific — match the domain in the SPECIALIZATION block (e.g. precise for engineering, brand-appropriate for marketing, rigorous for legal/compliance).
3. ABSOLUTELY NO generic project management fluff (e.g. "have a meeting", "align stakeholders") unless the user asked for process.
4. Each backlog item must be a concrete deliverable, decision, artifact, or verifiable step appropriate to the domain.
5. ANTI-DUPLICATION: Child items MUST NOT restate the parent title verbatim, NOR overlap siblings. Each item adds one distinct action.
6. 100% REQUIREMENT COVERAGE: Honor every explicit constraint from the user's query. Do not drop named tools, environments, or standards.
7. FACTUAL GROUNDING: Do not invent APIs, regulations, audience numbers, or vendor capabilities. Prefer "verify with official source for <product|policy|platform>" when unsure.
8. LOGGING: If the user asks for structured logs, prioritize application-level structured logging (e.g. JSON fields in the app). Do not mandate external log stacks (Logstash, Fluentd, ELK) unless the user requested them; if useful, mention them only as an optional later integration.
"""

SPECIALIZATION_WRAPPER = """
--- SPECIALIZATION (authoritative scope for this plan; prioritize this over generic assumptions) ---
{brief}
--- END SPECIALIZATION ---
"""


def format_domain_brief(
    original_domain: str,
    area: str,
    sub_domain: str,
    domain_summary: str,
    technical_context: str,
    success_criteria: str,
) -> str:
    """Single block injected into downstream prompts so the model stays specialized."""
    lines = [
        f"Layer 1 — Primary domain (broadest bucket): {original_domain or 'n/a'}",
        f"Layer 2 — Area (specialization within that domain): {area or 'n/a'}",
        f"Layer 3 — Sub-domain (narrow focus): {sub_domain or 'n/a'}",
    ]
    if (domain_summary or "").strip():
        lines.append(f"Working summary: {domain_summary.strip()}")
    if (technical_context or "").strip():
        lines.append(f"Tools, channels, stack & context (from query): {technical_context.strip()}")
    if (success_criteria or "").strip():
        lines.append(f"Success criteria: {success_criteria.strip()}")
    return "\n".join(lines)


def specialization_block(brief: str) -> str:
    if not (brief or "").strip():
        return ""
    return "\n" + SPECIALIZATION_WRAPPER.format(brief=brief.strip()) + "\n"


def get_domain_prompt(query: str) -> str:
    return f"""
You are a domain analyst. Your only job is to classify and summarize the user's request so later agents can plan accurately.

Use THREE LAYERS. Each layer must get MORE SPECIFIC than the one above. Do not default to technology unless the query is clearly technical.

USER QUERY:
"{query}"

TASK:

1. original_domain — LAYER 1 (most GENERAL). Pick ONE broad bucket that could apply across industries — NOT a tech-specific label unless the query is only about building software.

   Valid examples of breadth (choose the best fit or a close equivalent; invent a clear short label if needed):
   - Business & strategy | Product & innovation | Marketing & growth | Sales & revenue
   - Creative & content | Communications & PR | Social & community | Brand & design
   - People & HR | Legal & compliance | Finance & accounting | Operations & supply chain
   - Customer experience & support | Education & training | Research & insight
   - Software & technology | Data & analytics | Infrastructure & security | Manufacturing & physical delivery
   - Personal / life planning | Nonprofit & civic | Other (state what)

   original_domain MUST stay at this coarse level (like "Marketing & growth" or "People & HR"), never the same granularity as sub_domain.

2. area — LAYER 2 (SPECIALIZED within original_domain). The main lane or function inside that bucket.
   Examples: under "Marketing & growth" → "Digital social media", "Lifecycle email", "Performance ads"; under "Software & technology" → "Backend web services", "Mobile apps"; under "People & HR" → "Recruiting & hiring".

3. sub_domain — LAYER 3 (MOST SPECIFIC). The narrowest accurate focus for THIS query only.
   Examples: "Q4 LinkedIn + Instagram campaign for B2B SaaS leads", "Django admin UI overhaul", "Onboarding playbook for remote engineers".

4. domain_summary — 2–4 sentences: goals, audience, constraints, and assumptions (plain language, any industry).

5. technical_context — JSON field name is historical; content must cover ANY named concrete means: programming languages, SaaS tools, social platforms, ad networks, CRMs, channels, vendors, regulations, or media — comma-separated or short prose. If the query names none, say "Not specified in query".

6. success_criteria — One sentence: what "done" looks like (outcomes, not a task list).

QUALITY BAR:
- If the user is in marketing, creative, HR, legal, etc., original_domain MUST reflect that bucket — do not map their request to "Software & technology" unless they are building or operating software/systems.
- Keep original_domain stable and general; push detail into area and sub_domain.
- If the query is ambiguous, explain the interpretation in domain_summary; do not fabricate tools or metrics in technical_context.

OUTPUT: JSON only, no other keys.
{BASE_RULES}
EXPECTED JSON FORMAT:
{{
  "original_domain": "string",
  "area": "string",
  "sub_domain": "string",
  "domain_summary": "string",
  "technical_context": "string",
  "success_criteria": "string"
}}
"""


def get_gap_prompt(query: str, domain_brief: str) -> str:
    spec = specialization_block(domain_brief)
    return f"""
Analyze the user query: "{query}"
{spec}
Task: Identify genuine gaps, risks, or underspecified areas — NOT requirements the user already stated.

GAP RULES:
- Return between 0 and 5 gaps (inclusive). Use an empty list if the request is sufficiently complete.
- NEVER claim a requirement is "missing" or "not mentioned" if it appears in the user query or SPECIALIZATION summary.
- Frame gaps in vocabulary appropriate to the domain (e.g. brand safety for social campaigns, attribution/data for marketing, SLOs for ops, test strategy for software, ethics for research).
- You may combine related concerns into one gap string to stay within the limit.

SOFTWARE / WEB / ADMIN CHECK (apply when the query involves a web framework, HTTP APIs, browser UI, or admin panels — e.g. Django, Flask, FastAPI, Rails, "admin", "dashboard"):
- Scan for security and operational omissions the user did NOT already spell out. If any apply, include at least ONE concise gap covering the theme (combine into one string if needed), e.g.:
  · Authentication/authorization model for admin or staff users; principle of least privilege.
  · Session/cookies, CSRF, HTTPS/`SECURE_*` settings, `SECRET_KEY` handling and rotation.
  · Admin URL exposure, rate limiting or lockout for admin login, dependency/supply-chain updates.
- Do not invent specific CVEs or compliance certifications; stay at "planning gap" level.

{BASE_RULES}
EXPECTED JSON FORMAT:
{{
  "gaps": []
}}
(Example with items: {{ "gaps": ["Gap one", "Gap two"] }})
"""


def get_role_prompt(query: str, domain_brief: str) -> str:
    spec = specialization_block(domain_brief)
    return f"""
Analyze the user query: "{query}"
{spec}
Task: Deduce the implicit professional role the user is taking on, consistent with the SPECIALIZATION scope.
{BASE_RULES}
EXPECTED JSON FORMAT:
{{
  "user_role": "String"
}}
"""


def get_level_prompt(query: str, domain_brief: str) -> str:
    spec = specialization_block(domain_brief)
    return f"""
Analyze the user query: "{query}"
{spec}
Task: Deduce the user's expertise level based on phrasing and depth of the request.
{BASE_RULES}
EXPECTED JSON FORMAT:
{{
  "expertise_level": "String"
}}
"""


def get_epic_prompt(query: str, domain_brief: str, expertise_level: str) -> str:
    spec = specialization_block(domain_brief)
    return f"""
You are a planning architect for the domain described in SPECIALIZATION. You are NOT limited to software-only projects — adapt epic themes to the actual domain.

Task: Break down the objective into EXACTLY 3 high-level 'Epics' that cover the full lifecycle of THIS request.

CRITICAL CONSTRAINT 1: You MUST return EXACTLY 3 Epics. No more, no less.

CRITICAL CONSTRAINT 2 — Epic 3 ("quality & closure"):
- For software / systems work: Epic 3 MUST group testing & quality, security & safety where relevant, observability or monitoring if applicable, documentation, and engineering standards (e.g. typing, style, reviews).
- Epic 3 title OR description MUST explicitly mention security/hardening AND verification/testing (not only Docker, theming, or env files). Docker/env work may appear here only if paired with those quality themes or clearly labeled as deployment packaging under a broader quality epic.
- For non-software work (research, operations, content, organizational): Epic 3 MUST group validation of outcomes, risk & compliance, handoff documentation, and stakeholder acceptance or equivalent quality gates.

Use domain-appropriate naming in titles (do not force "Sprint" or Scrum jargon unless the user did).

User's Original Query: "{query}"
Expertise Level: {expertise_level}
{spec}
{BASE_RULES}
EXPECTED JSON FORMAT:
{{
  "epics": [
    {{ "title": "Epic 1 Title", "description": "Technical description of first phase" }},
    {{ "title": "Epic 2 Title", "description": "Technical description of second phase" }},
    {{ "title": "Epic 3 Title", "description": "Quality, validation, documentation, and closure" }}
  ]
}}
"""


def get_story_prompt(
    epic_title: str,
    epic_description: str,
    original_query: str,
    expertise_level: str,
    domain_brief: str,
    prior_epic_summaries: list[str] | None = None,
) -> str:
    prior = _format_prior_epics(prior_epic_summaries)
    spec = specialization_block(domain_brief)
    return f"""
You are a domain lead for this SPECIALIZATION (marketing, engineering, HR, etc.). Break down the Epic into EXACTLY 3 actionable 'Stories'.

Epic: "{epic_title}" - {epic_description}
User's Original Query: "{original_query}"
Expertise Level: {expertise_level}
{spec}
{prior}
{BASE_RULES}
Implement Dependency Tracking:
- Use local story ids exactly as "S1", "S2", "S3". The application will convert them to globally unique canonical ids.
- Use "depends_on" for prerequisite story ids within this Epic only. NEVER list a story's own id in depends_on.
Scope stories to THIS epic; do not duplicate deliverables from prior epics.
EXPECTED JSON FORMAT:
{{
  "stories": [
    {{ "id": "S1", "title": "Specific Story 1", "description": "Granular details...", "depends_on": [] }},
    {{ "id": "S2", "title": "Specific Story 2", "description": "Granular details...", "depends_on": ["S1"] }},
    {{ "id": "S3", "title": "Specific Story 3", "description": "Granular details...", "depends_on": [] }}
  ]
}}
"""


def get_task_prompt(
    story_id: str,
    story_title: str,
    story_description: str,
    epic_title: str,
    original_query: str,
    expertise_level: str,
    domain_brief: str,
    prior_epic_summaries: list[str] | None = None,
) -> str:
    prior = _format_prior_epics(prior_epic_summaries)
    spec = specialization_block(domain_brief)
    return f"""
You are a senior executor in the SPECIALIZATION domain. Break down the Story into EXACTLY 3 concrete tasks.

Epic: "{epic_title}"
Story id (prefix for ALL task ids): "{story_id}"
Story: "{story_title}" - {story_description}
User's Original Query: "{original_query}"
Expertise Level: {expertise_level}
{spec}
{prior}
{BASE_RULES}
Implement Dependency Tracking:
- Task ids MUST be globally unique: "{{story_id}}-T1", "{{story_id}}-T2", "{{story_id}}-T3".
- Use "depends_on" for blockers within this story only. NEVER list a task's own id in depends_on. Use [] for the first task or only prior task ids (e.g. ["{{story_id}}-T1"]).
Tasks must be specific to this domain (artifacts, configs, analyses, runbooks — not generic essays).
EXPECTED JSON FORMAT:
{{
  "tasks": [
    {{ "id": "{story_id}-T1", "title": "Actionable Task 1", "description": "...", "depends_on": [] }},
    {{ "id": "{story_id}-T2", "title": "Actionable Task 2", "description": "...", "depends_on": ["{story_id}-T1"] }},
    {{ "id": "{story_id}-T3", "title": "Actionable Task 3", "description": "...", "depends_on": ["{story_id}-T1"] }}
  ]
}}
"""


def get_subtask_prompt(
    task_title: str,
    task_description: str,
    original_query: str,
    domain_brief: str,
) -> str:
    spec = specialization_block(domain_brief)
    return f"""
You are a detail-oriented implementer in the SPECIALIZATION domain.
Task: Break down into EXACTLY 3 Sub-tasks.

Task: "{task_title}" - {task_description}
User's Original Query: "{original_query}"
{spec}
{BASE_RULES}
SUB-TASK STYLE:
- Each description: at most 2 short sentences OR one line listing files/locations and the change.
- Do NOT paste multi-line code or config blocks; name the artifact and the change (e.g. "Set retention policy in backup job definition").
- Three chronological steps: prepare → execute core change → verify or document.

EXPECTED JSON FORMAT:
{{
  "sub_tasks": [
    {{ "title": "Code level action 1", "description": "..." }},
    {{ "title": "Code level action 2", "description": "..." }},
    {{ "title": "Code level action 3", "description": "..." }}
  ]
}}
"""


PRIOR_EPIC_BLOCK = """
ALREADY PLANNED (earlier epics — do NOT repeat the same work; only fill gaps for THIS epic):
{prior}
"""


def _format_prior_epics(summaries: list[str] | None) -> str:
    if not summaries:
        return ""
    lines = "\n".join(f"- {s}" for s in summaries)
    return "\n" + PRIOR_EPIC_BLOCK.format(prior=lines) + "\n"
