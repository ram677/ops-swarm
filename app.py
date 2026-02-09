import streamlit as st
import asyncio
from src.graph import build_graph
from src.state import IncidentContext
from config.settings import settings

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title=f"{settings.APP_NAME} | Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Enterprise" Look
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .status-box { padding: 15px; border-radius: 8px; background-color: white; border: 1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metric-value { font-size: 24px; font-weight: bold; color: #1f77b4; }
    .metric-label { font-size: 14px; color: #666; }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT ---
if "app_state" not in st.session_state:
    st.session_state.app_state = None
if "incident_active" not in st.session_state:
    st.session_state.incident_active = False
if "logs" not in st.session_state:
    st.session_state.logs = ""

# --- 3. SIDEBAR: INCIDENT SIMULATOR ---
with st.sidebar:
    st.header("🚨 Incident Simulator")
    st.info(f"System: {settings.APP_NAME} v{settings.APP_VERSION}")
    
    selected_scenario = st.selectbox(
        "Select Scenario", 
        ["DB Connection Failure", "High Latency (Auth)", "Disk Full (Logs)"]
    )
    
    # Mock Logs based on scenario
    logs_preview = ""
    if selected_scenario == "DB Connection Failure":
        logs_preview = """
[ERROR] 2024-05-20 14:02:01 ConnectionPool: Unable to connect to DB_SHARD_04.
[CRITICAL] 2024-05-20 14:02:02 Service 'PaymentGateway' health check failed.
[WARN] 2024-05-20 14:02:03 Retrying connection... (Attempt 3/5)
[ERROR] 2024-05-20 14:02:04 Connection Refused.
        """
    elif selected_scenario == "High Latency (Auth)":
        logs_preview = "[WARN] Auth Service response time > 2000ms."
    elif selected_scenario == "Disk Full (Logs)":
        logs_preview = "[CRITICAL] /var/log partition at 99% usage. Write failed."
    
    st.text_area("Live Server Logs", value=logs_preview, height=150, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        trigger_btn = st.button("🔥 Trigger Incident", type="primary")
    with col2:
        reset_btn = st.button("🔄 Reset System")

    if trigger_btn:
        st.session_state.incident_active = True
        st.session_state.logs = logs_preview
        st.session_state.app_state = None # Clear previous agent state
        st.rerun()

    if reset_btn:
        st.session_state.incident_active = False
        st.session_state.app_state = None
        st.rerun()

# --- 4. MAIN DASHBOARD ---
st.title(f"🛡️ {settings.APP_NAME}")
st.markdown("---")

if not st.session_state.incident_active:
    st.success("✅ Systems Operational. No active incidents.")
    # Optional: Add a placeholder image or graph here
else:
    # --- INCIDENT ACTIVE VIEW ---
    
    # Initialize Agent if not already running
    if st.session_state.app_state is None:
        initial_context = IncidentContext(
            incident_id="INC-2024-001",
            logs=st.session_state.logs,
            severity="CRITICAL",
            action_status="PENDING"
        )
        initial_inputs = {
            "messages": [],
            "context": initial_context,
            "require_approval": False
        }
        
        # Run Graph (Async)
        graph = build_graph()
        
        with st.status("🤖 **Agent AI is investigating...**", expanded=True) as status:
            st.write("🔍 Analyzing Logs...")
            final_state = asyncio.run(graph.ainvoke(initial_inputs))
            st.session_state.app_state = final_state
            status.update(label="✅ Analysis Complete", state="complete", expanded=False)

    # Display Current State
    state = st.session_state.app_state
    ctx = state["context"]

    # Dashboard Layout
    col_kpi, col_chat = st.columns([1, 2])

    # LEFT COLUMN: KPIs & Status
    with col_kpi:
        st.subheader("Live Telemetry")
        
        st.markdown(f"""
        <div class="status-box">
            <div class="metric-label">Incident ID</div>
            <div class="metric-value">{ctx.incident_id}</div>
            <br>
            <div class="metric-label">Severity</div>
            <div class="metric-value" style="color: red;">{ctx.severity}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("### Root Cause")
        if ctx.diagnosis:
            st.error(ctx.diagnosis)
        else:
            st.warning("Diagnosing...")

    # RIGHT COLUMN: Chat & Action
    with col_chat:
        st.subheader("Agent Operations Log")
        
        # Chat History Container
        chat_container = st.container(height=400)
        with chat_container:
            for msg in state["messages"]:
                if "Diagnosis" in msg:
                    st.chat_message("ai").info(msg)
                elif "Proposed" in msg:
                    st.chat_message("ai").warning(msg)
                elif "Execution" in msg:
                    st.chat_message("ai").success(msg)
                elif "Blocked" in msg:
                    st.chat_message("ai").error(msg)
                elif "SECURITY ALERT" in msg:
                    st.chat_message("ai", avatar="🚨").error(msg)
                elif "Operator" in msg:
                    st.chat_message("user").write(msg)
                else:
                    st.chat_message("ai").write(msg)

        # HUMAN IN THE LOOP CONTROLS
        if ctx.action_status == "PENDING" and ctx.proposed_action:
            st.markdown("### 🛑 Human Approval Required")
            st.warning(f"**Proposed Action:** `{ctx.proposed_action}`")
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("✅ Approve & Execute"):
                    # Update state to Approved
                    state["context"].action_status = "APPROVED"
                    
                    with st.spinner("🚀 Executing Remediation Plan..."):
                        # Re-run graph with updated state
                        graph = build_graph()
                        new_state = asyncio.run(graph.ainvoke(state))
                        st.session_state.app_state = new_state
                        st.rerun()
            
            with btn_col2:
                if st.button("❌ Reject Plan"):
                    st.error("Plan Rejected. Escalating to human SRE team.")
                    st.session_state.incident_active = False

        elif ctx.action_status == "EXECUTED":
             st.success("🎉 Incident Resolved Successfully.")
             # Optional: st.balloons()

    # --- 5. MANUAL OPERATOR CONSOLE (GUARDRAILS TEST) ---
    st.markdown("---")
    st.subheader("👨‍💻 Manual Operator Console (Guardrails Test)")
    
    # Chat Input for testing Guardrails
    user_override = st.chat_input("Type a manual command (e.g., 'Check status' or 'Delete DB')...")
    
    if user_override:
        # Add user message to state
        state["messages"].append(f"👤 **Operator:** {user_override}")
        
        # SIMULATE GUARDRAIL CHECK
        # In a full deployment, this is handled by rails.generate() inside the graph.
        # For the demo, we explicitly visualize the interception.
        dangerous_keywords = ["delete", "destroy", "drop", "rm -rf", "wipe"]
        
        if any(word in user_override.lower() for word in dangerous_keywords):
            response = "⛔ **SECURITY ALERT:** I am blocked from executing destructive commands by the OpsSwarm Safety Policy."
            state["messages"].append(response)
        else:
            state["messages"].append(f"🤖 **Agent:** Acknowledged. Processing manual command: '{user_override}'")
            # Here you could optionally trigger a graph re-run if you wanted real logic
        
        st.rerun()