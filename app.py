import streamlit as st
import asyncio
from src.graph import build_graph
from src.state import IncidentContext

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OpsSwarm | Autonomous SRE",
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
# Streamlit reruns the script on every interaction. We must persist data.
if "app_state" not in st.session_state:
    st.session_state.app_state = None  # Stores the Agent's memory
if "incident_active" not in st.session_state:
    st.session_state.incident_active = False
if "logs" not in st.session_state:
    st.session_state.logs = ""

# --- 3. SIDEBAR: INCIDENT SIMULATOR ---
with st.sidebar:
    st.header("🚨 Incident Simulator")
    st.info("Simulate a production outage to trigger the Autonomous Agent.")
    
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
st.title("🛡️ OpsSwarm: Autonomous Infrastructure Healer")
st.markdown("---")

if not st.session_state.incident_active:
    st.success("✅ Systems Operational. No active incidents.")
    st.image("https://img.freepik.com/free-vector/server-room-rack-center-cloud-database-backup-mining-farm-dark-interior-vector-illustration_107791-2487.jpg", width=600)

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
            # We use asyncio.run to execute the async graph in Streamlit
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
        
        # Status Box
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
        
        # Chat History
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

        # HUMAN IN THE LOOP CONTROLS
        if ctx.action_status == "PENDING" and ctx.proposed_action:
            st.markdown("### 🛑 Human Approval Required")
            st.warning(f"**Proposed Action:** `{ctx.proposed_action}`")
            
            # Action Buttons
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
             st.balloons()