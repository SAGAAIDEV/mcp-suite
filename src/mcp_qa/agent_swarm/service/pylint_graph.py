from typing import Annotated

from agents.prompts.system import get_system_prompt
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langgraph_swarm import create_handoff_tool, create_swarm

from mcp_qa.config.env import LLM_API_KEYS
from mcp_qa.utils.git_utils import get_git_root

from ..tools.file_editor import (
    append_to_file,
    execute_python_code,
    get_python_files_tree,
    read_file,
    reflect,
    replace_in_file,
    write_to_file,
)
from ..tools.pylint import (
    get_next_pylint_error,
)

model = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    api_key=LLM_API_KEYS.ANTHROPIC_API_KEY,
    extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
)
checkpointer = InMemorySaver()
# long-term memory
store = InMemoryStore()


def directected_handoff_tool(
    *, agent_name: str, tool_name: str, tool_description: str
) -> BaseTool:

    @tool(description=tool_description)
    def handoff_to_agent(
        # you can add additional tool call arguments for the LLM to populate
        # for example, you can ask the LLM to populate a task description
        # for the next agent
        task_description: Annotated[
            str,
            "Detailed description of what the next agent should do, "
            "including all of the relevant context.",
        ],
        # you can inject the state of the agent that is calling the tool
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        tool_message = ToolMessage(
            content=f"Successfully transferred to {agent_name}",
            name=tool_name,
            tool_call_id=tool_call_id,
        )
        # you can use a different messages state key here,
        # if your agent uses a different schema
        # e.g., "alice_messages" instead of "messages"
        last_agent_message = state["messages"][-1]
        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            # NOTE: this is a state update that will be applied to the swarm
            # multi-agent graph (i.e., the PARENT graph)
            update={
                "messages": [last_agent_message, tool_message],
                "active_agent": agent_name,
                # optionally pass the task description to the next agent
                "task_description": task_description,
            },
        )

    return handoff_to_agent


coding_agent = create_react_agent(
    model,
    [
        read_file,
        write_to_file,
        append_to_file,
        replace_in_file,
        get_python_files_tree,
        execute_python_code,
        reflect,
        create_handoff_tool(agent_name="pylint_agent"),
        # create_handoff_tool(agent_name="coder"),
        # create_handoff_tool(agent_name="implimenter"),
    ],
    prompt=get_system_prompt(get_git_root())
    + "When you are don fixing a error, handoff to pylint_agent to get another one.",
    name="coding_agent",
)

pylint_agent = create_react_agent(
    model,
    [
        get_next_pylint_error,  # this is a handoff,
        # it forces a handoff after the tool runs
        # create_handoff_tool(agent_name="coding_agent"),
        # create_handoff_tool(agent_name="implimenter"),
    ],
    prompt=(
        "You are a specialized pylint error provider. "
        "Your only job is to serve up pylint errors one at a time to the coding agent.\n"
        "\n"
        "WORKFLOW:\n"
        "1. When activated, immediately use the get_next_pylint_error tool to fetch "
        "the next pylint error.\n"
        "2. If an error is found, hand it off to the coding_agent without any "
        "additional analysis or suggestions.\n"
        "3. If no errors are found (linting is complete), inform the coding agent that "
        "all errors have been fixed. And it should call its reflect tool\n"
        "\n"
        "RULES:\n"
        "- Do not attempt to fix errors yourself - that's the coding agent's job.\n"
        "- Do not provide code suggestions or analysis.\n"
        "- Keep your responses brief and to the point.\n"
        "- Always use the handoff_to_agent tool to return control to the coding_agent "
        "after getting an error.\n"
        "- Never engage in extended conversations - your only purpose is to fetch and "
        "relay pylint errors.\n"
        "\n"
        "Remember: You are a simple error provider, not a problem solver. Your value "
        "comes from efficiently identifying and relaying errors to the coding agent."
    ),
    name="pylint_agent",
)
workflow = create_swarm(
    [coding_agent, pylint_agent], default_active_agent="coding_agent"
)
app = workflow.compile(checkpointer=checkpointer, store=store)
