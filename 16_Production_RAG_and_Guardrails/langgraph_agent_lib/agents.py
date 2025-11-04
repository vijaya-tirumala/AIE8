"""LangGraph agent integration with production features."""

from typing import Dict, Any, List, Optional
import os

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_core.tools import tool
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

from .models import get_openai_model
from .rag import ProductionRAGChain
from .guardrails import (
    create_guardrails_guard,
    create_factuality_guard,
    create_input_validation_node,
    create_output_validation_node,
    GuardrailsState
)


class AgentState(TypedDict):
    """State schema for agent graphs."""
    messages: Annotated[List[BaseMessage], add_messages]


def create_rag_tool(rag_chain: ProductionRAGChain):
    """Create a RAG tool from a ProductionRAGChain."""
    
    @tool
    def retrieve_information(query: str) -> str:
        """Use Retrieval Augmented Generation to retrieve information from the student loan documents."""
        try:
            result = rag_chain.invoke(query)
            return result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            return f"Error retrieving information: {str(e)}"
    
    return retrieve_information


def get_default_tools(rag_chain: Optional[ProductionRAGChain] = None) -> List:
    """Get default tools for the agent.
    
    Args:
        rag_chain: Optional RAG chain to include as a tool
        
    Returns:
        List of tools
    """
    tools = []
    
    # Add Tavily search if API key is available
    if os.getenv("TAVILY_API_KEY"):
        tools.append(TavilySearchResults(max_results=5))
    
    # Add Arxiv tool
    tools.append(ArxivQueryRun())
    
    # Add RAG tool if provided
    if rag_chain:
        tools.append(create_rag_tool(rag_chain))
    
    return tools


def create_langgraph_agent(
    model_name: str = "gpt-4",
    temperature: float = 0.1,
    tools: Optional[List] = None,
    rag_chain: Optional[ProductionRAGChain] = None
):
    """Create a simple LangGraph agent.
    
    Args:
        model_name: OpenAI model name
        temperature: Model temperature
        tools: List of tools to bind to the model
        rag_chain: Optional RAG chain to include as a tool
        
    Returns:
        Compiled LangGraph agent
    """
    if tools is None:
        tools = get_default_tools(rag_chain)
    
    # Get model and bind tools
    model = get_openai_model(model_name=model_name, temperature=temperature)
    model_with_tools = model.bind_tools(tools)
    
    def call_model(state: AgentState) -> Dict[str, Any]:
        """Invoke the model with messages."""
        messages = state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def should_continue(state: AgentState):
        """Route to tools if the last message has tool calls."""
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "action"
        return END
    
    # Build graph
    graph = StateGraph(AgentState)
    tool_node = ToolNode(tools)
    
    graph.add_node("agent", call_model)
    graph.add_node("action", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"action": "action", END: END})
    graph.add_edge("action", "agent")
    
    return graph.compile()


def create_guardrails_agent(
    model_name: str = "gpt-4.1-mini",
    temperature: float = 0.1,
    tools: Optional[List] = None,
    rag_chain: Optional[ProductionRAGChain] = None,
    valid_topics: Optional[List[str]] = None,
    invalid_topics: Optional[List[str]] = None,
    enable_jailbreak_detection: bool = True,
    enable_pii_protection: bool = True,
    enable_profanity_check: bool = True,
    enable_factuality_check: bool = False,
    strict_mode: bool = True,
    max_refinements: int = 3
):
    """Create a LangGraph agent with Guardrails validation.
    
    This agent includes input validation (jailbreak, topic, PII) and output validation
    (content moderation, factuality) with refinement loops for failed validations.
    
    Args:
        model_name: OpenAI model name. Default: "gpt-4.1-mini"
        temperature: Model temperature. Default: 0.1
        tools: List of tools to bind to the model. If None, uses default tools.
        rag_chain: Optional RAG chain to include as a tool
        valid_topics: List of valid topics to allow. Default: student loan topics
        invalid_topics: List of invalid topics to block. Default: common off-topics
        enable_jailbreak_detection: Whether to enable jailbreak detection. Default: True
        enable_pii_protection: Whether to enable PII detection. Default: True
        enable_profanity_check: Whether to enable profanity filtering. Default: True
        enable_factuality_check: Whether to enable factuality checking. Default: False
        strict_mode: If True, blocks invalid inputs/outputs. Default: True
        max_refinements: Maximum refinement attempts for failed validations. Default: 3
        
    Returns:
        Compiled LangGraph agent with guardrails
        
    Example:
        >>> agent = create_guardrails_agent(
        ...     rag_chain=rag_chain,
        ...     valid_topics=["student loans", "financial aid"]
        ... )
        >>> response = agent.invoke({"messages": [HumanMessage(content="What are loan repayment options?")]})
    """
    from langchain_core.messages import HumanMessage, AIMessage
    
    # Set default topics if not provided
    if valid_topics is None:
        valid_topics = ["student loans", "financial aid", "education financing", "loan repayment"]
    if invalid_topics is None:
        invalid_topics = ["investment advice", "crypto", "gambling", "politics", "medical advice"]
    
    # Get tools
    if tools is None:
        tools = get_default_tools(rag_chain)
    
    # Get model and bind tools
    model = get_openai_model(model_name=model_name, temperature=temperature)
    model_with_tools = model.bind_tools(tools)
    
    # Create input guard (for user queries)
    input_guard = create_guardrails_guard(
        valid_topics=valid_topics,
        invalid_topics=invalid_topics,
        enable_jailbreak_detection=enable_jailbreak_detection,
        enable_pii_protection=enable_pii_protection,
        enable_profanity_check=enable_profanity_check,
        enable_competitor_check=False
    )
    
    # Create output guard (for agent responses)
    output_guard = create_guardrails_guard(
        valid_topics=None,  # Don't restrict topics on output
        invalid_topics=None,
        enable_jailbreak_detection=False,  # Not needed for output
        enable_pii_protection=enable_pii_protection,
        enable_profanity_check=enable_profanity_check,
        enable_competitor_check=False
    )
    
    # Create factuality guard if enabled
    factuality_guard = None
    if enable_factuality_check:
        factuality_guard = create_factuality_guard(
            eval_model=model_name,
            on_prompt=False  # Check on response, not prompt
        )
    
    # Create validation nodes
    input_validation_node = create_input_validation_node(
        input_guard=input_guard,
        strict_mode=strict_mode
    )
    
    output_validation_node = create_output_validation_node(
        output_guard=output_guard,
        factuality_guard=factuality_guard,
        strict_mode=strict_mode,
        max_refinements=max_refinements
    )
    
    # Agent node
    def call_model(state: GuardrailsState) -> Dict[str, Any]:
        """Invoke the model with messages."""
        messages = state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Tool node
    tool_node = ToolNode(tools)
    
    # Routing functions
    def should_continue(state: GuardrailsState):
        """Route to tools if the last message has tool calls."""
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "action"
        return "output_validation"
    
    def route_after_input_validation(state: GuardrailsState):
        """Route after input validation."""
        if state.get("validation_failed", False):
            return END  # Block invalid input
        return "agent"  # Continue to agent
    
    def route_after_output_validation(state: GuardrailsState):
        """Route after output validation."""
        if state.get("validation_failed", False) and state.get("needs_refinement", False):
            refinement_count = state.get("refinement_count", 0)
            if refinement_count < max_refinements:
                return "agent"  # Try refinement
        return END  # Done or max refinements reached
    
    # Build graph
    graph = StateGraph(GuardrailsState)
    
    # Add nodes
    graph.add_node("input_validation", input_validation_node)
    graph.add_node("agent", call_model)
    graph.add_node("action", tool_node)
    graph.add_node("output_validation", output_validation_node)
    
    # Set entry point
    graph.set_entry_point("input_validation")
    
    # Add edges
    graph.add_conditional_edges(
        "input_validation",
        route_after_input_validation,
        {
            "agent": "agent",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "action": "action",
            "output_validation": "output_validation"
        }
    )
    
    graph.add_edge("action", "agent")
    
    graph.add_conditional_edges(
        "output_validation",
        route_after_output_validation,
        {
            "agent": "agent",  # Refinement loop
            END: END
        }
    )
    
    return graph.compile()
