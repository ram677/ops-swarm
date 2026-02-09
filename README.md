# 🛡️ OpsSwarm: Autonomous Infrastructure Remediation Agent

![License](https://img.shields.io/badge/License-MIT-green) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Stack](https://img.shields.io/badge/Tech-LangGraph%20|%20Groq%20|%20MCP-orange) ![Safety](https://img.shields.io/badge/Safety-NeMo%20Guardrails-red)

> **A production-grade Agentic System designed to detect, diagnose, and resolve infrastructure incidents autonomously—with strict Human-in-the-Loop governance.**

![Main Dashboard](results/test_1.1.png)

---

## 📖 Overview
**OpsSwarm** is not just a chatbot; it is a state-aware **Site Reliability Engineering (SRE) Agent**. It connects to live infrastructure logs, reasons about root causes using **Groq's LPU**, and executes remediation tools via the **Model Context Protocol (MCP)**.

Crucially, it implements a **Safety-First Architecture**:
1.  **Cyclic Reasoning:** Uses **LangGraph** to plan and verify fixes before executing.
2.  **Tool Isolation:** Tools run on a separate **MCP Server**, decoupling the AI from the OS.
3.  **Deterministic Guardrails:** **NeMo Guardrails** intercept and block destructive commands (like `rm -rf` or `DROP DB`) at the embedding level.

---

## 🚀 Key Features
* **🧠 Cognitive Architecture:** Implements a `Diagnose -> Plan -> Approval -> Execute` loop.
* **⚡ Sub-Second Inference:** Powered by **Llama-3-70b** on **Groq**, enabling real-time log parsing.
* **🔌 Model Context Protocol (MCP):** Standardized interface for connecting LLMs to local/remote tools (Docker, K8s, CLI).
* **👨‍💻 Human-in-the-Loop (HITL):** Critical actions require explicit operator approval via the UI.
* **🛡️ Enterprise Security:** Custom **Colang** flows prevent prompt injection and unauthorized actions.

---

## 📸 Project Walkthrough

### Scenario 1: The "Happy Path" (Auto-Remediation)
The system detects a critical failure, diagnoses the root cause, and proposes a fix. It then pauses for human verification.

**1. Incident Detection & Diagnosis**
The agent parses raw server logs, identifies `Database Shard 04 Connection Refused`, and formulates a plan.
![Diagnosis](results/test_1.1.png)

**2. Human-in-the-Loop Approval**
The workflow halts at a "Conditional Edge." The agent cannot proceed without a state update from the operator.
![Approval Required](results/test_1.2.png)

**3. Execution & Resolution**
Once approved, the agent executes the `restart_resource` tool via MCP and verifies system health.
![Success](results/test_1.3.png)

---

### Scenario 2: The "Security Test" (Guardrails)
Demonstrating resilience against malicious prompts or accidental destructive commands.

**1. Simulated Attack**
An operator (or prompt injector) attempts to force the agent to delete the production database.
![Attack Attempt](results/test_2.1.png)

**2. Guardrail Interception**
The **NeMo Guardrails** layer intercepts the intent *before* it reaches the planner. The command is blocked deterministically.
![Blocked](results/test_2.2.png)

---

## 🛠️ Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Orchestrator** | **LangGraph** | Manages the cyclic state machine and agent memory. |
| **Inference Engine** | **Groq API** | Provides Llama-3-70b inference at ~300 tokens/sec. |
| **Tooling Layer** | **MCP (Model Context Protocol)** | Standardizes tool execution (Server/Client architecture). |
| **Safety Layer** | **NeMo Guardrails** | Enforces security policies using Colang definitions. |
| **Data Validation** | **Pydantic** | Ensures strict schema compliance for all agent outputs. |
| **Frontend** | **Streamlit** | Provides the interactive SRE Dashboard. |

---

## 📂 Project Structure
```text
opsswarm/
├── config/
│   ├── settings.py         # Centralized App Configuration
│   └── rails/              # NeMo Guardrails Configs
│       ├── config.yml      # Model & Flow Definitions
│       └── security.co     # Colang Security Rules
├── src/
│   ├── graph.py            # LangGraph State Machine (The Brain)
│   ├── mcp_server.py       # Tool Provider (The Hands)
│   ├── mcp_client.py       # Tool Connector
│   └── state.py            # Pydantic Data Models
├── results/                # Demo Screenshots
├── app.py                  # Streamlit Dashboard Entry Point
├── requirements.txt        # Dependencies
└── .env                    # Secrets (API Keys)
```
---

### Installation

1.  **Install Dependencies**
    Open a terminal in the project root (`opsswarm/`) and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment**
    Create a `.env` file in the root directory and add your API keys:
    ```properties
    PROJECT_NAME="OpsSwarm Enterprise"
    GROQ_API_KEY=gsk_your_key_here
    # Optional: LangSmith Keys
    # LANGCHAIN_TRACING_V2=true
    # LANGCHAIN_API_KEY=lsv2_your_key_here
    ```

3.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

---

## 🔮 Future Roadmap

- **Kubernetes Integration**: Move MCP server to a sidecar pod for K8s cluster management.
- **Slack Integration**: Allow approval/rejection directly via Slack channels.
- **RAG Knowledge Base**: Indexing past incident reports (Post-Mortems) to improve diagnosis accuracy.
