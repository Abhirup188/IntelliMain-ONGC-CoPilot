IntelliMain: AI-Powered Maintenance Co-Pilot for ONGC
Autonomous Asset Integrity & SOP Compliance Orchestrator

The Mission
In high-stakes environments like the ONGC Jorhat site, the gap between real-time sensor data and static PDF manuals (SOPs) can lead to catastrophic failure or safety violations. IntelliMain bridges this gap using a multi-agent system that audits machine health against international standards in seconds.

System Architecture
Built on LangGraph, the system employs a "Chain-of-Agents" to ensure deterministic engineering logic:

Diagnostician Agent: Evaluates live telemetry (vibration, temp, pressure) against ISO 10816-3 thresholds.

Librarian Agent (RAG): Semantically retrieves the "Ground Truth" from industrial SOPs using a FAISS vector store and GPT-5 Nano.

Maintenance Planner Agent: Synthesizes the diagnosis and SOP rules into a structured, safety-first Work Order.

Human-in-the-Loop (HITL) Safety
Unlike generic AI, this system respects the Senior Engineer's authority. It utilizes LangGraph Checkpointers to pause execution, requiring a professional "signature" before any maintenance action is officially recommended.

Tech Stack
Orchestration: LangGraph (Stateful Multi-Agent Workflows)

Intelligence: GPT-5 Nano (2025-08-07)

Knowledge Retrieval: LangChain + FAISS + OpenAI Embeddings

Interface: Streamlit (Industrial Dashboard)

Domain Logic: Mechanical Reliability, API 610, ISO 10816

🚀 Setup & Installation
Clone the Repo: 
```terminal
git clone https://github.com/your-username/IntelliMain-ONGC-CoPilot.git
```

Install Dependencies: 
```terminal
pip install -r requirements.txt
```
Watch the Demo Video: https://drive.google.com/file/d/1sBUtfSwjt0FnLN923DFgtN6GToy51fWQ/view?usp=drive_link

Environment Variables: Create a .env file based on .env.example.

Run the App: streamlit run app.py
