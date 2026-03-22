import streamlit as st
import uuid
from main import app # Your compiled LangGraph app
from schemas import AssetHealthState
from fpdf import FPDF
import datetime
import re

st.set_page_config(page_title="ONGC Asset Co-Pilot", layout="wide")

# 1. Session State Initialization
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "audit_complete" not in st.session_state:
    st.session_state.audit_complete = False

config = {"configurable": {"thread_id": st.session_state.thread_id}}

st.title("🛢️ ONGC Maintenance Co-Pilot")
st.subheader(f"Jorhat Site Asset Integrity Orchestrator")

def generate_pdf(plan_text, asset_id):
    pdf = FPDF()
    pdf.add_page()
    
    clean_text = re.sub(r'[^\x00-\x7F]+', '', plan_text) 
    clean_text = clean_text.replace("###", "").replace("##", "").replace("**", "")

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="ONGC MAINTENANCE ADVISORY", ln=True, align='C')
    
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Asset ID: {asset_id}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, txt=clean_text)
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# 2. Asset Inputs
col1, col2, col3 = st.columns(3)
with col1:
    vibration = st.number_input("Vibration (mm/s)", value=1.5, step=0.1)
with col2:
    temp = st.number_input("Bearing Temp (°C)", value=50.0, step=1.0)
with col3:
    pressure = st.number_input("Discharge Pressure (bar)", value=10.0, step=0.1)

if st.button("Run Asset Audit", type="primary"):
    st.session_state.audit_complete = False
    initial_input = {
        "asset_id": "PUMP-JORHAT-CENTRIFUGAL",
        "latest_telemetry": {"vibration": vibration, "temp": temp, "pressure": pressure},
        "mentor_approval": False, "errors": []
    }
    
    # Execute the graph until it hits a breakpoint or finishes
    with st.spinner("Analyzing telemetry against ONGC SOPs..."):
        app.invoke(initial_input, config)
    
# 3. Handle the State and Interruption
snapshot = app.get_state(config)
current_values = snapshot.values

if current_values.get("telemetry_status") == "Normal":
    st.success("✅ ASSET STATUS: NORMAL. No maintenance required at this time.")
    
elif current_values.get("telemetry_status") == "Anomaly":
    st.warning(f"⚠️ ANOMALY DETECTED (Risk: {current_values.get('failure_risk')})")
    
    # Display the Librarian's Ground Truth
    st.info(f"**Official SOP Reference Found:** \n\n{current_values.get('sop_reference')}")
    
    st.divider()
    
    # 4. Human-in-the-Loop Approval
    st.markdown("### 🖋️ Senior Engineer Approval")
    st.write("Please review the SOP clause above. Do you authorize the AI to draft the formal Work Order?")
    
    if st.button("Approve & Generate Work Order"):
        with st.status("Processing Mentor Approval...", expanded=True) as status:
            st.write("Updating state with Senior Engineer signature...")
            app.update_state(config, {"mentor_approval": True})
            
            st.write("Drafting final Work Order via Maintenance Planner node...")
            # Resume the graph
            app.invoke(None, config)
            
            st.write("Finalizing PDF Advisory report...")
            st.session_state.audit_complete = True
            
            # 2. Complete the status
            status.update(label="✅ Work Order Finalized!", state="complete", expanded=False)
        st.rerun()

# 5. Show Final Result
if st.session_state.audit_complete:
    final_snapshot = app.get_state(config)
    plan = final_snapshot.values.get("action_plan")
    
    st.success("✅ Work Order Generated Successfully.")
    st.markdown(plan) 
    
    # Add the Download Button
    pdf_bytes = generate_pdf(plan, final_snapshot.values.get("asset_id"))
    st.download_button(
        label="📥 Download Advisory PDF",
        data=pdf_bytes,
        file_name=f"ONGC_WorkOrder_{final_snapshot.values.get('asset_id')}.pdf",
        mime="application/pdf"
    )