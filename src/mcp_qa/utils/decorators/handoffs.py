from typing import Callable, Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langgraph_swarm.handoff import (
    METADATA_KEY_HANDOFF_DESTINATION,
    _normalize_agent_name,
)
from typing_extensions import Annotated

from mcp_qa.models.tool_result import ToolResult


def tool_with_handoff(agent_name: str, description: Optional[str] = None):
    """Decorator that wraps a tool function with handoff functionality.

    This decorator creates a tool that will execute the decorated function
    and then hand off control to the specified agent.

    Args:
        agent_name: The name of the agent to handoff control to
        description: Optional description for the handoff tool

    Returns:
        A decorator function that wraps the tool
    """

    def decorator(func: Callable):
        # Get the original tool's name and description
        tool_name = getattr(func, "name", func.__name__)
        tool_desc = getattr(func, "description", func.__doc__ or "")

        # Create a new name for the combined tool
        combined_name = (
            f"{tool_name}_and_handoff_to_{_normalize_agent_name(agent_name)}"
        )
        combined_desc = f"{tool_desc} Then hands off to {agent_name}."

        if description:
            combined_desc = description

        @tool(combined_name, description=combined_desc)
        def wrapped_tool(
            state: Annotated[dict, InjectedState],
            tool_call_id: Annotated[str, InjectedToolCallId],
            *args,
            **kwargs,
        ):
            # Execute the original tool function
            result = func(*args, **kwargs)

            # Handle different result types
            if isinstance(result, ToolResult):
                # Get the message from the ToolResult
                message = result.message
            elif isinstance(result, str):
                if "error" in result.lower():
                    pass
                elif "failed" in result.lower() or "pylint error" in result.lower():
                    pass
                message = result
            else:
                message = str(result)

            # Create tool message with the result
            tool_message = ToolMessage(
                content=f"{message}",
                name=combined_name,
                tool_call_id=tool_call_id,
            )
            handoff_message = ToolMessage(
                content=f"Now handing off to {agent_name}",
                name=combined_name,
                tool_call_id=tool_call_id,
            )

            # Return command to handoff to the specified agent
            return Command(
                goto=agent_name,
                graph=Command.PARENT,
                update={
                    "messages": state["messages"] + [tool_message, handoff_message],
                    "active_agent": agent_name,
                },
            )

        # Add metadata for handoff destination
        wrapped_tool.metadata = {METADATA_KEY_HANDOFF_DESTINATION: agent_name}
        return wrapped_tool

    return decorator
