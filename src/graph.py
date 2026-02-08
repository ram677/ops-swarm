import os
import json
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState, IncidentContext
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from dotenv import load_dotenv

load_dotenv()

# --- SETUP ---
llm = ChatGroq(model="llama-3-70b-versatile", temperature=0)

# Connect to our local MCP Server script
server_params = StdioServerParameters(
    command="python", 
    args=["src/mcp_server.py"] # Path to your server file
)

# --- NODES ---

async def diagnose_node(state: AgentState):
    """Agent analyzes logs and identifies the issue."""
    logs = state["context"].logs
    
    # In a real app, we would use NeMo Guardrails here.
    # For simplicity in this file, we use direct LLM prompting.
    
    prompt = f"""
    You are a Site Reliability Engineer. Analyze these logs:
    {logs}
    
    Identify the root cause service and the specific error.
    Return ONLY a concise diagnosis string.
    """
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    state["context"].diagnosis = response.content
    state["messages"].append(f"🔍 Diagnosis: {response.content}")
    return state

async def plan_node(state: AgentState):
    """Agent consults tools to propose a fix."""
    diagnosis = state["context"].diagnosis
    
    # We use the MCP Client to check DB status before proposing a fix
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # The agent decides to check the DB status based on diagnosis
            # (Hardcoded logic for demo stability, but usually LLM decides)
            tool_result = await session.call_tool("check_db_status", arguments={"shard_id": "DB_SHARD_04"})
            
            db_status = tool_result.content[0].text
            
    proposal = f"Restart DB_SHARD_04 (Status: {db_status})"
    
    state["context"].proposed_action = proposal
    state["messages"].append(f"🛠️ Proposed Plan: {proposal}")
    state["require_approval"] = True # TRIGGER HUMAN APPROVAL
    return state

async def execute_node(state: AgentState):
    """Executes the tool via MCP."""
    action = state["context"].proposed_action
    
    if state["context"].action_status != "APPROVED":
        state["messages"].append("⛔ Execution Blocked: Approval missing.")
        return state

    # Execute via MCP
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("restart_resource", arguments={"resource_id": "DB_SHARD_04"})
            
    state["messages"].append(f"✅ Execution Result: {result.content[0].text}")
    state["context"].action_status = "EXECUTED"
    return state

# --- GRAPH BUILDER ---

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)
    
    workflow.set_entry_point("diagnose")
    workflow.add_edge("diagnose", "plan")
    
    # Conditional Edge: If approval needed, stop. Else (or after approval), go to execute.
    # Note: Streamlit handles the 'Stop', so we just map flow.
    workflow.add_edge("plan", "execute") 
    workflow.add_edge("execute", END)
    
    return workflow.compile()

