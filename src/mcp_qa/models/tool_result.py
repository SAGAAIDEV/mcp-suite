"""
Module containing tool-related models for the QA server.

This module defines the data structures used for representing tool execution
results and statuses in the QA system. The ToolResult model enables directing
agent behavior through status codes and messages, facilitating handoffs between
agents and tools in a workflow.
"""

import json
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ToolStatus(str, Enum):
    """Enum representing possible tool execution statuses.

    These statuses can be used to control agent workflow and direct
    subsequent actions after tool execution.
    """

    SUCCESS = "Success"
    FAILURE = "Failure"
    ERROR = "Error"
    CONTINUE = "Continue"
    EXCEPTION = "Exception"


class NextAction(BaseModel):
    """Represents a next action to be taken after a tool execution.

    This model captures a function reference and optional instructions for the next
    step in a workflow. During validation, it extracts the function name to set as
    the mcp_tool field.

    Attributes:
        tool: A callable function reference for the next action.
        instructions: Optional instructions for executing the next action.
        mcp_tool: The name of the function, extracted during validation.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    tool: Callable
    instructions: str = "Call the mcp tool."
    mcp_tool: Optional[str] = None

    @field_validator("tool")
    def extract_tool_name(cls, v: Any, info: Any) -> Any:
        """Extract the tool name and set it as mcp_tool."""
        values = info.data
        values["mcp_tool"] = v.__name__
        return v

    @model_validator(mode="after")
    def ensure_mcp_tool(self) -> "NextAction":
        """Ensure mcp_tool is set from the tool's name."""
        if self.tool and not self.mcp_tool:
            self.mcp_tool = self.tool.__name__
        return self

    def __str__(self) -> str:
        """Override __str__ to run model_dump first and convert to string."""
        return str(self.model_dump())

    def model_dump(self, **kwargs):
        """Override model_dump to exclude tool callable by default."""
        exclude = kwargs.get("exclude", set())
        if isinstance(exclude, set):
            exclude.add("tool")
        else:
            exclude = {"tool"}

        kwargs["exclude"] = exclude

        # Get the result with exclude_none=False to include mcp_tool even if it's None
        kwargs.setdefault("exclude_none", False)
        result = super().model_dump(**kwargs)

        # Ensure mcp_tool is always included
        if "mcp_tool" not in result:
            result["mcp_tool"] = self.mcp_tool

        return result

    def model_dump_json(self, **kwargs):
        """Override model_dump_json to exclude None values by default and dump
        next_action."""
        kwargs.setdefault("exclude_none", True)
        # Use model_dump to get the processed dict with next_action already handled
        result = self.model_dump(**kwargs)
        # Convert to JSON using BaseModel's json serialization
        return json.dumps(result)


class ToolResult(BaseModel):
    """Represents the result of a tool execution with status and message information.

    This model enables tools to provide structured feedback to agents and
    direct subsequent workflow steps. When used with decorators like
    `tool_with_handoff`, it can trigger agent transitions or tool chains.

    Attributes:
        status: The status of the tool execution (Success, Failure, Error, Continue,
            Exception). Different statuses can trigger different agent behaviors.
        message: A descriptive message about the result. Can contain instructions
            for the agent or information to be passed to the next tool or agent.
        next_action: An optional string identifier for the next action to take.
        # success_message: An optional message specific to SUCCESS status with details.
        # failure_message: An optional message specific to FAILURE status with details.
        # error_message: An optional message specific to ERROR status with details.
        # continue_message: An optional message specific to CONTINUE status with details.
        # exception_message: An optional message specific to EXCEPTION status.
    """

    model_config = ConfigDict(extra="allow", exclude_none=True)

    status: ToolStatus
    message: str
    next_action: Optional[NextAction | dict] = None

    def __str__(self) -> str:
        """Override __str__ to handle next_action field."""
        result = self.model_dump()
        return str(result)

    def model_dump(self, **kwargs):
        """Override model_dump to exclude None values by default and dump next_action."""
        # For next_action, we want to include None values
        next_action_exclude_none = False

        # For everything else, use the provided exclude_none or default to True
        kwargs.setdefault("exclude_none", True)
        result = super().model_dump(**kwargs)

        # If next_action exists, replace it with its model_dump
        if self.next_action is not None and result.get("next_action") is not None:
            # Call model_dump with exclude_none=False for next_action
            result["next_action"] = self.next_action.model_dump(
                exclude_none=next_action_exclude_none
            )

        return result

    def model_dump_json(self, **kwargs):
        """Override model_dump_json to exclude None values by default and dump
        next_action."""
        kwargs.setdefault("exclude_none", True)
        # Use model_dump to get the processed dict with next_action already handled
        result = self.model_dump(**kwargs)
        # Convert to JSON using BaseModel's json serialization
        return json.dumps(result)
