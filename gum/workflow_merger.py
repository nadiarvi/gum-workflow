from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Observation, Workflow, observation_workflow
from .schemas import MergedWorkflowSchema, get_schema


WORKFLOW_MERGE_PROMPT = """You are consolidating inferred workflows for {user_name}.

The input contains small workflow records extracted from observations. Some may be
adjacent pieces of a larger workflow, duplicates, or unrelated activities.

Your task:
- Merge related fine-grained workflows into larger canonical workflows.
- Preserve unrelated workflows as separate canonical workflows.
- Keep named entities from the source workflows and observations.
- Use the observations as evidence, but summarize them concisely in reasoning.
- Do not invent source references. Each output workflow must include the source_refs
  that support it.

# Source Workflows

{sources}

# Output

Return only JSON in this format:
{{
  "workflows": [
    {{
      "workflow_name": "<short canonical workflow name>",
      "input": "<merged input or starting material>",
      "output": "<merged output or intended result>",
      "steps": [
        {{
          "step": "<ordered observed or inferred step>",
          "confidence": <integer 1-10>
        }}
      ],
      "reasoning": "<concise evidence summary grounded in source observations>",
      "confidence": <integer 1-10>,
      "source_refs": ["<source ref>", "..."]
    }}
  ]
}}"""


@dataclass
class WorkflowSource:
    ref: str
    item: dict | None = None
    workflow: Workflow | None = None
    observations: set[Observation] | None = None

    @property
    def name(self) -> str:
        if self.workflow is not None:
            return self.workflow.name
        return self.item["workflow_name"]

    @property
    def input(self) -> str:
        if self.workflow is not None:
            return self.workflow.input
        return self.item["input"]

    @property
    def output(self) -> str:
        if self.workflow is not None:
            return self.workflow.output
        return self.item["output"]

    @property
    def steps(self) -> list[dict]:
        if self.workflow is not None:
            try:
                return json.loads(self.workflow.steps)
            except json.JSONDecodeError:
                return []
        return self.item["steps"]

    @property
    def reasoning(self) -> str:
        if self.workflow is not None:
            return self.workflow.reasoning
        return self.item["reasoning"]

    @property
    def confidence(self) -> int | None:
        if self.workflow is not None:
            return self.workflow.confidence
        return self.item.get("confidence")


class WorkflowMerger:
    def __init__(
        self,
        *,
        user_name: str,
        model: str,
        client: AsyncOpenAI,
        logger: logging.Logger,
        candidate_limit: int = 25,
        similarity_threshold: float = 0.2,
    ) -> None:
        self.user_name = user_name
        self.model = model
        self.client = client
        self.logger = logger
        self.candidate_limit = candidate_limit
        self.similarity_threshold = similarity_threshold

    async def merge_new_workflows(
        self,
        session: AsyncSession,
        workflow_items: list[dict],
        observations: list[Observation],
    ) -> int:
        if not workflow_items:
            return 0

        existing = await self._related_existing_workflows(session, workflow_items)
        sources: list[WorkflowSource] = [
            WorkflowSource(
                ref=f"N{idx}",
                item=item,
                observations=set(observations),
            )
            for idx, item in enumerate(workflow_items)
        ]
        sources.extend(
            WorkflowSource(
                ref=f"E{workflow.id}",
                workflow=workflow,
                observations=set(workflow.observations),
            )
            for workflow in existing
        )

        if len(sources) == 1:
            await self._add_workflow(
                session,
                self._source_to_item(sources[0]),
                sources[0].observations or set(),
            )
            return 1

        return await self._merge_sources(session, sources)

    async def merge_existing_workflows(
        self,
        session: AsyncSession,
        *,
        limit: int = 100,
    ) -> int:
        stmt = (
            select(Workflow)
            .options(selectinload(Workflow.observations))
            .order_by(Workflow.created_at.desc())
            .limit(limit)
        )
        rows = (await session.execute(stmt)).scalars().all()
        sources = [
            WorkflowSource(
                ref=f"E{workflow.id}",
                workflow=workflow,
                observations=set(workflow.observations),
            )
            for workflow in rows
        ]
        if len(sources) <= 1:
            return 0
        return await self._merge_sources(session, sources)

    async def _merge_sources(
        self,
        session: AsyncSession,
        sources: list[WorkflowSource],
    ) -> int:
        by_ref = {source.ref: source for source in sources}
        merged_items = await self._construct_merged_workflows(sources)
        delete_ids: set[int] = set()
        used_refs: set[str] = set()
        created = 0

        for item in merged_items:
            source_refs = [ref for ref in item.get("source_refs", []) if ref in by_ref]
            if not source_refs:
                self.logger.warning("Skipping merged workflow with no valid source refs")
                continue

            used_refs.update(source_refs)
            observations: set[Observation] = set()
            for ref in source_refs:
                source = by_ref[ref]
                observations.update(source.observations or set())
                if source.workflow is not None:
                    delete_ids.add(source.workflow.id)

            await self._add_workflow(session, item, observations)
            created += 1

        for source in sources:
            if source.workflow is None and source.ref not in used_refs:
                await self._add_workflow(
                    session,
                    self._source_to_item(source),
                    source.observations or set(),
                )
                created += 1

        if delete_ids:
            await session.execute(delete(Workflow).where(Workflow.id.in_(delete_ids)))

        await session.flush()
        return created

    async def _construct_merged_workflows(
        self,
        sources: list[WorkflowSource],
    ) -> list[dict]:
        prompt = WORKFLOW_MERGE_PROMPT.replace("{user_name}", self.user_name).replace(
            "{sources}", self._format_sources(sources)
        )
        rsp = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=get_schema(MergedWorkflowSchema.model_json_schema()),
        )
        return json.loads(rsp.choices[0].message.content)["workflows"]

    async def _related_existing_workflows(
        self,
        session: AsyncSession,
        workflow_items: list[dict],
    ) -> list[Workflow]:
        stmt = (
            select(Workflow)
            .options(selectinload(Workflow.observations))
            .order_by(Workflow.created_at.desc())
            .limit(self.candidate_limit)
        )
        candidates = (await session.execute(stmt)).scalars().all()
        if not candidates:
            return []

        new_docs = [self._item_doc(item) for item in workflow_items]
        existing_docs = [self._workflow_doc(workflow) for workflow in candidates]
        try:
            vecs = TfidfVectorizer().fit_transform(new_docs + existing_docs)
        except ValueError:
            return []

        sims = cosine_similarity(vecs[: len(new_docs)], vecs[len(new_docs) :])
        selected = []
        for idx, workflow in enumerate(candidates):
            if float(sims[:, idx].max()) >= self.similarity_threshold:
                selected.append(workflow)
        return selected

    def _format_sources(self, sources: list[WorkflowSource]) -> str:
        blocks = []
        for source in sources:
            obs_lines = []
            for obs in list(source.observations or set())[:5]:
                preview = obs.content.replace("\n", " ")[:500]
                obs_lines.append(f"- [{obs.observer_name}] {preview}")
            observations = "\n".join(obs_lines) if obs_lines else "- None"
            steps = "\n".join(
                f"{idx}. {step.get('step')} (confidence: {step.get('confidence')})"
                for idx, step in enumerate(source.steps, 1)
            )
            blocks.append(
                f"[{source.ref}]\n"
                f"Workflow: {source.name}\n"
                f"Input: {source.input}\n"
                f"Output: {source.output}\n"
                f"Steps:\n{steps}\n"
                f"Reasoning: {source.reasoning}\n"
                f"Confidence: {source.confidence}\n"
                f"Supporting Observations:\n{observations}"
            )
        return "\n\n".join(blocks)

    async def _add_workflow(
        self,
        session: AsyncSession,
        item: dict,
        observations: set[Observation],
    ) -> None:
        workflow = Workflow(
            name=item["workflow_name"],
            input=item["input"],
            output=item["output"],
            steps=json.dumps(item["steps"]),
            reasoning=item["reasoning"],
            confidence=item.get("confidence"),
        )
        session.add(workflow)
        await session.flush()

        for obs in observations:
            await session.execute(
                insert(observation_workflow)
                .prefix_with("OR IGNORE")
                .values(observation_id=obs.id, workflow_id=workflow.id)
            )

    def _source_to_item(self, source: WorkflowSource) -> dict:
        return {
            "workflow_name": source.name,
            "input": source.input,
            "output": source.output,
            "steps": source.steps,
            "reasoning": source.reasoning,
            "confidence": source.confidence,
            "source_refs": [source.ref],
        }

    def _item_doc(self, item: dict) -> str:
        steps = " ".join(step.get("step", "") for step in item.get("steps", []))
        return " ".join(
            [
                item.get("workflow_name", ""),
                item.get("input", ""),
                item.get("output", ""),
                steps,
                item.get("reasoning", ""),
            ]
        )

    def _workflow_doc(self, workflow: Workflow) -> str:
        try:
            steps = json.loads(workflow.steps)
        except json.JSONDecodeError:
            steps = []
        return self._item_doc(
            {
                "workflow_name": workflow.name,
                "input": workflow.input,
                "output": workflow.output,
                "steps": steps,
                "reasoning": workflow.reasoning,
            }
        )
