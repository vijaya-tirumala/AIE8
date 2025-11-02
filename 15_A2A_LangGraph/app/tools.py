"""Toolbelt assembly for agents.

Collects third-party tools and local tools (like RAG) into a single list that
graphs can bind to their language models.
"""
from __future__ import annotations

from typing import List

from langchain_tavily import TavilySearch
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from app.rag import retrieve_information

from langchain_core.tools import tool
import httpx
import asyncio
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageRequest, MessageSendParams
from uuid import uuid4

def get_tool_belt() -> List:
    """Return the list of tools available to agents (Tavily, Arxiv, RAG, general simple agent)."""
    tavily_tool = TavilySearch(max_results=5)
    return [tavily_tool, ArxivQueryRun(), retrieve_information, call_general_agent_via_a2a]


@tool
def call_general_agent_via_a2a(query: str) -> str:
    """Call the General Purpose Agent via A2A protocol to answer questions using web search, academic papers, and documents."""
    async def _call():
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            resolver = A2ACardResolver(httpx_client=client, base_url='http://localhost:10000')
            agent_card = await resolver.get_agent_card()
            a2a_client = A2AClient(httpx_client=client, agent_card=agent_card)
            
            payload = {'message': {'role': 'user', 'parts': [{'kind': 'text', 'text': query}], 'message_id': uuid4().hex}}
            request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**payload))
            response = await a2a_client.send_message(request)
            
            result = response.root.result
            if hasattr(result, 'artifact') and result.artifact:
                return result.artifact[0].root.text
            return str(result)
    
    return asyncio.run(_call())
