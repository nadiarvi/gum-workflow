# schemas.py

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class AuditSchema(BaseModel):
    """
    Output produced by the privacy-audit LLM call.
    """
    is_new_information: bool = Field(..., description="Whether the message reveals anything not seen before")
    data_type:          str  = Field(..., description="Category of data being disclosed")
    subject:            str  = Field(..., description="Who the data is about")
    recipient:          str  = Field(..., description="Who receives the data")
    transmit_data:      bool = Field(..., description="Should downstream processing continue")

    model_config = ConfigDict(extra="forbid")

class PropositionItem(BaseModel):
    reasoning: str = Field(..., description="The reasoning for the proposition")
    proposition: str = Field(..., description="The proposition string")
    confidence: Optional[int] = Field(
        ...,
        description="Confidence score from 1 (low) to 10 (high)"
    )
    decay: Optional[int] = Field(
        ...,
        description="Decay score from 1 (low) to 10 (high)"
    )

    model_config = ConfigDict(extra="forbid")

class PropositionSchema(BaseModel):
    propositions: List[PropositionItem] = Field(
        ...,
        description="Up to K propositions"
    )
    model_config = ConfigDict(extra="forbid")

class WorkflowStepItem(BaseModel):
    step: str = Field(..., description="One observed step in the workflow")
    confidence: Optional[int] = Field(
        ...,
        description="Confidence score from 1 (low) to 10 (high)"
    )

    model_config = ConfigDict(extra="forbid")

class WorkflowItem(BaseModel):
    workflow_name: str = Field(..., description="Short name for the observed workflow")
    input: str = Field(..., description="Inputs or starting materials used in the workflow")
    output: str = Field(..., description="Outputs or results produced by the workflow")
    steps: List[WorkflowStepItem] = Field(..., description="Ordered workflow steps")
    reasoning: str = Field(..., description="Evidence supporting this workflow pattern")
    confidence: Optional[int] = Field(
        ...,
        description="Overall confidence score from 1 (low) to 10 (high)"
    )

    model_config = ConfigDict(extra="forbid")

class WorkflowSchema(BaseModel):
    workflows: List[WorkflowItem] = Field(
        ...,
        description="Observed workflow patterns"
    )

    model_config = ConfigDict(extra="forbid")

class MergedWorkflowItem(BaseModel):
    workflow_name: str = Field(..., description="Short name for the merged workflow")
    input: str = Field(..., description="Inputs or starting materials used in the workflow")
    output: str = Field(..., description="Outputs or results produced by the workflow")
    steps: List[WorkflowStepItem] = Field(..., description="Ordered workflow steps")
    reasoning: str = Field(..., description="Evidence summary grounded in source observations")
    confidence: Optional[int] = Field(
        ...,
        description="Overall confidence score from 1 (low) to 10 (high)"
    )
    source_refs: List[str] = Field(
        ...,
        description="Source workflow references used to produce this merged workflow"
    )

    model_config = ConfigDict(extra="forbid")

class MergedWorkflowSchema(BaseModel):
    workflows: List[MergedWorkflowItem] = Field(
        ...,
        description="Canonical merged workflow patterns"
    )

    model_config = ConfigDict(extra="forbid")

class Update(BaseModel):
    content: str = Field(..., description="The content of the update")
    content_type: Literal["input_text", "input_image"] = Field(..., description="The type of the update")

RelationLabel = Literal["IDENTICAL", "SIMILAR", "UNRELATED"]

class RelationItem(BaseModel):
    source: int                     = Field(description="Proposition ID")
    label:  RelationLabel           = Field(description="Relationship label")

    # give target a default_factory so the JSON‐schema default is [] (allowed)
    target: List[int] = Field(
        default_factory=list,
        description="IDs of other propositions (empty if none)"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "required": ["source", "label", "target"]
        }
    )


class RelationSchema(BaseModel):
    relations: List[RelationItem]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "required": ["relations"]
        }
    )

def get_schema(json_schema):
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "json_output",
            "schema": json_schema,
        },
    }

UPDATE_MAP = {
    "input_text": "text",
    "input_image": "image_url",
}
