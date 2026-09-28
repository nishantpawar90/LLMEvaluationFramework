from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Annotated, Any, TypedDict

from deepeval.integrations.langchain import CallbackHandler
from deepeval.test_case import ToolCall
from deepeval.tracing import observe, update_current_trace
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from .config import Settings
from .mongo_client import MongoProductRepository
from .prompts import SYSTEM_PROMPT
from .tools import make_product_tools


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


@dataclass
class AgentResult:
    answer: str
    tool_calls: list[ToolCall]
    tool_context: list[str]


class ProductAgent:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.settings.require_openai()
        self.repository = MongoProductRepository(self.settings)
        self.tools = make_product_tools(self.repository)
        self.deepeval_callback = CallbackHandler()
        #
        self.model = ChatOpenAI(model=self.settings.model, temperature=0, callbacks = [self.deepeval_callback]).bind_tools(self.tools)
        graph = StateGraph(AgentState)
        graph.add_node("agent", self._call_model)
        graph.add_node("tools", ToolNode(self.tools))
        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
        self.graph = graph.compile()

    def _call_model(self, state: AgentState) -> dict[str, list[AnyMessage]]:
        return {"messages": [self.model.invoke(state["messages"])]}

    @observe(type="agent")
    def run(self, question: str) -> AgentResult:
        if not question.strip():
            raise ValueError("A product question is required.")
        state = self.graph.invoke({"messages": [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]})
        messages = state["messages"]
        answer = str(messages[-1].content)
        calls_by_id: dict[str, ToolCall] = {}
        context: list[str] = []
        for message in messages:
            for call in getattr(message, "tool_calls", []) or []:
                calls_by_id[call["id"]] = ToolCall(name=call["name"], input_parameters=call.get("args", {}))
            if getattr(message, "type", None) == "tool":
                text = str(message.content)
                context.append(text)
                if message.tool_call_id in calls_by_id:
                    calls_by_id[message.tool_call_id].output = text
        update_current_trace(input=question, output=answer, tools_called=list(calls_by_id.values()))
        return AgentResult(answer=answer, tool_calls=list(calls_by_id.values()), tool_context=context)

    def close(self) -> None:
        self.repository.close()


if __name__ == "__main__":
    agent = ProductAgent()
    try:
        result = agent.run(" ".join(sys.argv[1:]) or "What product is UPC 0001960004580?")
        print(result.answer)
        print(json.dumps([call.model_dump() for call in result.tool_calls], indent=2, default=str))
    finally:
        agent.close()
