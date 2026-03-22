import uuid
from main import app
from schemas import AssetHealthState

thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

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

for event in app.stream(initial_input, config, stream_mode="values"):
    status = event.get("telemetry_status")
    if status:
        print(f"Current Status: {status}")

snapshot = app.get_state(config)
state_data = snapshot.values

print("\n⏸ WORKFLOW PAUSED FOR MENTOR REVIEW")
print(f"Asset ID: {state_data.get('asset_id')}")
print(f"AI Diagnosis: {state_data.get('telemetry_status')} (Risk: {state_data.get('failure_risk')})")
print(f"SOP Reference Found: {state_data.get('sop_reference')}")
print("-" * 40)

approval = input("Sir, do you approve this repair plan? (yes/no): ").lower()

if approval == "yes":
    app.update_state(config, {"mentor_approval": True})
    print("\n✅ Approval Received. Resuming to draft Work Order...")
    
    final_run = app.invoke(None, config)
    
    print("\n FINAL MAINTENANCE WORK ORDER ")
    print(final_run.get("action_plan"))
    print("\n AUDIT COMPLETE")
else:
    print("\n Audit Rejected by Mentor. Logic halted for manual intervention.")
