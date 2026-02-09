import os
import asyncio
from dotenv import load_dotenv

# LangGraph & LangChain Imports
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Local Imports
from src.state import AgentState
from src.mcp_client import execute_tool
from config.settings import settings

# Load Environment Variables
load_dotenv()

# --- 1. SETUP ---
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    temperature=settings.TEMPERATURE,
    api_key=settings.GROQ_API_KEY
)

# --- 2. NODES (The Logic Steps) ---

async def diagnose_node(state: AgentState):
    """
    Step 1: Analyze logs and identify the root cause.
    """
    # If we are already approved/executing, skip re-diagnosis to save tokens/time
    if state["context"].action_status == "APPROVED":
        return state

    print("--- [Agent] Diagnosing Incident ---")
    logs = state["context"].logs
    
    prompt = f"""
    You are a Senior Site Reliability Engineer (SRE).
    Analyze the following server logs and identify the specific service failure and error type.
    
    LOGS:
    {logs}
    
    Output ONLY a concise diagnosis (e.g., 'Database Shard 04 Connection Refused').
    Do not propose fixes yet.
    """
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    state["context"].diagnosis = response.content
    state["messages"].append(f"🔍 **Diagnosis:** {response.content}")
    
    return state

async def plan_node(state: AgentState):
    """
    Step 2: Check system status and propose a fix.
    """
    # --- FIX: If already approved, pass through to execution immediately ---
    if state["context"].action_status == "APPROVED":
        return state

    print("--- [Agent] Planning Fix ---")
    diagnosis = state["context"].diagnosis
    
    # Check status tool
    tool_result = await execute_tool("check_db_status", {"shard_id": "DB_SHARD_04"})
    
    prompt = f"""
    Diagnosis: {diagnosis}
    Current System Status: {tool_result}
    
    Propose a specific remediation action using available tools.
    Available Tools: ['restart_resource', 'fetch_service_logs']
    
    Output ONLY the recommended action in this format:
    "Action: <ToolName> <Args>"
    Example: "Action: restart_resource DB_SHARD_04"
    """
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    proposal = response.content.strip()
    
    # Update State
    state["context"].proposed_action = proposal
    state["messages"].append(f"🛠️ **Proposed Plan:** {proposal}")
    state["messages"].append(f"📊 **Live Status Check:** {tool_result}")
    
    # Set to PENDING to trigger the pause
    state["require_approval"] = True 
    state["context"].action_status = "PENDING"
    
    return state

async def execute_node(state: AgentState):
    """
    Step 3: Execute the fix ONLY if approved.
    """
    print("--- [Agent] Executing Fix ---")
    action_status = state["context"].action_status
    proposal = state["context"].proposed_action
    
    # Safety Check
    if action_status != "APPROVED":
        msg = "⛔ **Execution Blocked:** Waiting for Human Approval."
        # Avoid duplicate messages if looping
        if not state["messages"] or state["messages"][-1] != msg:
            state["messages"].append(msg)
        return state

    # Parse and Execute
    try:
        if "restart_resource" in proposal:
            resource_id = proposal.split("restart_resource")[-1].strip()
            
            # CALL MCP TOOL
            result = await execute_tool("restart_resource", {"resource_id": resource_id})
            
            success_msg = f"✅ **Execution Result:** {result}"
            state["messages"].append(success_msg)
            state["context"].action_status = "EXECUTED"
        else:
            state["messages"].append("⚠️ **Error:** Unknown action type.")
            
    except Exception as e:
        state["messages"].append(f"❌ **Execution Failed:** {str(e)}")

    return state

# --- 3. GRAPH CONSTRUCTION ---

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)

    workflow.set_entry_point("diagnose")
    workflow.add_edge("diagnose", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", END)

    return workflow.compile()