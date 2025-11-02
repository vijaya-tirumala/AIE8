"""Simple Agent that uses the General Purpose Agent via A2A protocol."""
import os
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from app.tools import call_general_agent_via_a2a

load_dotenv()

class SimpleAgentState(TypedDict):
    messages: Annotated[List, add_messages]

def build_simple_agent():
    """Build a simple LangGraph agent that calls the A2A agent."""
    model = ChatOpenAI(
        model=os.getenv('TOOL_LLM_NAME', 'gpt-4o-mini'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        temperature=0
    )
    tools = [call_general_agent_via_a2a]
    model_with_tools = model.bind_tools(tools)
    
    def agent_node(state):
        messages = state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    graph = StateGraph(SimpleAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", lambda state: "tools" if state["messages"][-1].tool_calls else END)
    graph.add_edge("tools", "agent")

    return graph.compile()


if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "What are the latest developments in AI in 2025?"
    agent = build_simple_agent()
    response = agent.invoke({"messages": [("user", query)]})
    print("\n=== SIMPLE AGENT RESPONSE ===")
    print(response["messages"][-1].content)