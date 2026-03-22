import uuid
from main import app
from schemas import AssetHealthState

# 1. Setup Session Configuration
# A unique thread_id allows the MemorySaver to persist this specific audit.
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# 2. Define Simulated Anomaly Data
# We use vibration (6.5) and temp (85) to trigger the 'Anomaly' branch.
initial_input = {
    "asset_id": "PUMP-JORHAT-001",
    "latest_telemetry": {
        "vibration": 6.5, 
        "temp": 85.0, 
        "pressure": 12.5
    },
    "mentor_approval": False,
    "errors": []
}

print("\n STARTING AUTOMATED ONGC ASSET AUDIT")

# 3. First Execution: Run until the Breakpoint
# The graph will run through Diagnostician and Librarian, then stop.
for event in app.stream(initial_input, config, stream_mode="values"):
    status = event.get("telemetry_status")
    if status:
        print(f"Current Status: {status}")

# 4. Inspect the "Paused" State
# We pull the saved state from memory to show the mentor what the AI found.
snapshot = app.get_state(config)
state_data = snapshot.values

print("\n⏸ WORKFLOW PAUSED FOR MENTOR REVIEW")
print(f"Asset ID: {state_data.get('asset_id')}")
print(f"AI Diagnosis: {state_data.get('telemetry_status')} (Risk: {state_data.get('failure_risk')})")
print(f"SOP Reference Found: {state_data.get('sop_reference')}")
print("-" * 40)

# 5. Simulate Mentor Approval
# In your Streamlit app, this would be a button click.
approval = input("Sir, do you approve this repair plan? (yes/no): ").lower()

if approval == "yes":
    # Manually update the state to reflect human oversight.
    app.update_state(config, {"mentor_approval": True})
    print("\n✅ Approval Received. Resuming to draft Work Order...")
    
    # 6. Resume Execution
    # Passing None tells LangGraph to continue from the last checkpoint.
    final_run = app.invoke(None, config)
    
    print("\n FINAL MAINTENANCE WORK ORDER ")
    print(final_run.get("action_plan"))
    print("\n AUDIT COMPLETE")
else:
    print("\n Audit Rejected by Mentor. Logic halted for manual intervention.")