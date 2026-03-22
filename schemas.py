from typing import TypedDict,Dict,List,Annotated
from langgraph.graph.message import add_messages
class AssetHealthState(TypedDict):
    messages: Annotated[list,add_messages]
    asset_id: str
    latest_telemetry: Dict[str, float]
    telemetry_status: str 
    failure_risk: float  
    sop_reference: str   
    action_plan: str      
    mentor_approval: bool 
    errors: List[str]
