import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from schemas import AssetHealthState
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph,END
from langgraph.checkpoint.memory import MemorySaver
from schemas import AssetHealthState

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

llm = ChatOpenAI(
    model="gpt-5-nano-2025-08-07",
    temperature=0.0
)

file_path = "data/Ongc sop.txt"

loader = TextLoader(file_path=file_path)
data = loader.load()
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="gpt-5-nano",
    chunk_size=1000,
    chunk_overlap=200
)

chunks = text_splitter.split_documents(data)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = FAISS.from_documents(chunks,embedding=embeddings)
vector_store.save_local("faiss_index_ongc")
retriever = vector_store.as_retriever()

class Diagnosis(BaseModel):
    status: str = Field(description="'Normal' or 'Anomaly'")
    risk_score: float = Field(description="Failure risk from 0.0 to 1.0 based on severity")

def diagnostician_node(state: AssetHealthState) -> dict:
    """
    Acts as the 'First Responder' engineer at the pump house.
    Evaluates raw numbers against internal engineering knowledge.
    """
    print(f"DIAGNOSING ASSET: {state['asset_id']}")
    
    # Prepare the sensor data for the LLM
    telemetry = state.get("latest_telemetry", {})
    
    # Force structured output so the state update is clean
    structured_llm = llm.with_structured_output(Diagnosis)
    
    # The 'Senior Engineer' Prompt
    prompt = f"""
    You are a Senior Maintenance Engineer at an ONGC Centrifugal Pump station.
    Analyze the following telemetry data to detect potential failures:
    
    ASSET_ID: {state['asset_id']}
    Vibration: {telemetry.get('vibration', 0)} mm/s
    Bearing Temperature: {telemetry.get('temp', 0)} °C
    Discharge Pressure: {telemetry.get('pressure', 0)} bar
    
    Rules:
    1. If vibration > 4.5 mm/s or temp > 80 °C, status is 'Anomaly'.
    2. Calculate risk_score based on how close the values are to 'Trip' levels 
       (7.1 mm/s or 93 °C).
    """
    
    try:
        result = structured_llm.invoke(prompt)
        
        return {
            "telemetry_status": result.status,
            "failure_risk": result.risk_score
        }
    except Exception as e:
        print(f"Diagnosis Node Error: {e}")
        return {"telemetry_status": "Error", "failure_risk": 0.0}
    
class LibrarianOutput(BaseModel):
    sop_clause: str = Field(description="The exact section or clause ID from the manual")
    required_action: str = Field(description="The specific safety or maintenance instruction found in the SOP")
    
def Librarian_Node(state:AssetHealthState)->dict:
    """
    Acts as the 'Technical Librarian' and 'Compliance Auditor' 
    by mapping detected anomalies to official ONGC Standard Operating Procedures (SOPs).
    """

    if state.get("telemetry_status")!="Anomaly":
        return {"sop_reference":"N/A - Asset Healthy"}

    print(f"Giving required Maintenence steps: {state['asset_id']}")

    telemetry = state.get("latest_telemetry",{})
    query = f"Maintenance procedure for high vibration {telemetry.get('vibration')} or high temperature {telemetry.get('temp')}"

    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])

    structured_llm = llm.with_structured_output(LibrarianOutput)
    prompt = f"""
    You are an ONGC Technical Auditor. Match the following anomaly to the provided SOP context.
    
    ANOMALY DATA: {telemetry}
    SOP CONTEXT:
    {context}
    
    Rules:
    1. Extract the exact 'SOP Clause' (e.g., Section 2.1).
    2. Extract the 'Required Action' specifically mentioned for these values.
    3. If no exact match is found, state 'SOP Clause Not Found'.
    """

    try:
        response = structured_llm.invoke(prompt)
        return{
            "sop_reference": f"Per {response.sop_clause}: {response.required_action}"
        }
    except Exception as e:
        print(f"Librarian Node Error: {e}")
        return {"sop_reference": "Error during SOP retrieval"}
    
def should_continue(state: AssetHealthState):
    """
    Routes the workflow based on the health of the asset.
    If an Anomaly is detected, it triggers the 'Librarian' for SOP research.
    """
    # Check the flag set by the Diagnostician node
    if state["telemetry_status"] == "Anomaly":
        return "continue"
    
    # If the pump is healthy, skip the research and end the process
    return "end"
    
class Planner_Output(BaseModel):
    Work_Order_ID: str = Field(description="A unique identifier (e.g., WO-2026-001)")
    Priority_Level: str = Field(description="Routine, Urgent, or Emergency based on the failure_risk")
    step_by_step_instruction:str = Field(description="The actual mechanical tasks.")
    Safety_precautions:str = Field(description="Specific LOTO (Lock-out/Tag-out) requirements.")

    
def Maintenance_Planner_Node(state:dict)->dict:
    """
    Acts as the 'Field Maintenance Supervisor' by 
    synthesizing the technical diagnosis and official SOP requirements into a structured, actionable repair plan
    """
    prompt = """
    You are a Maintenance Supervisor at the ONGC Jorhat site. Your goal is to convert a technical anomaly and an SOP reference into a safe, professional Work Order.

    Context Provided:

    Asset: {asset_id}.

    Diagnosis: {telemetry_status} with Risk Score: {failure_risk}.

    Official SOP Requirement: {sop_reference} (The ground truth from the Librarian node).

    Your Task:

    Determine the Priority Level:

    If failure_risk > 0.8: Emergency.

    If failure_risk > 0.5: Urgent.

    Otherwise: Routine.

    Draft a 3-step Maintenance Plan that strictly follows the sop_reference.

    Include Safety Requirements, specifically mentioning LOTO and necessary PPE for Centrifugal Pumps.

    State that this plan is 'Pending Senior Engineer Approval'.
    """
    structured_llm = llm.with_structured_output(Planner_Output)
    
    try:
        formatted_prompt = prompt.format(
            asset_id=state.get("asset_id"),
            telemetry_status=state.get("telemetry_status"),
            failure_risk=state.get("failure_risk"),
            sop_reference=state.get("sop_reference")
        )
        response = structured_llm.invoke(formatted_prompt)
        formatted_plan = (
            f"📋 WORK ORDER: {response.Work_Order_ID}\n\n"
            f"Priority Level: {response.Priority_Level}\n\n"
            f"🛠️ Maintenance Steps:\n{response.step_by_step_instruction}\n\n"
            f"⚠️ Safety Precautions:\n{response.Safety_precautions}\n\n"
            f"Status: Pending Senior Engineer Signature"
        )
        return{
            "action_plan": formatted_plan
        }
    except Exception as e:
        print(f"Planner Node Error: {e}")

memory = MemorySaver()
workflow = StateGraph(AssetHealthState)
workflow.add_node("diagnostician",diagnostician_node)
workflow.add_node("Librarian",Librarian_Node)
workflow.add_node("Maintenance_Planner",Maintenance_Planner_Node)
workflow.set_entry_point("diagnostician")
workflow.add_edge("Librarian","Maintenance_Planner")

workflow.add_conditional_edges(
    "diagnostician",
    should_continue,
    {
        "continue": "Librarian",
        "end": END
    }
)
workflow.add_edge("Maintenance_Planner",END)

app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["Maintenance_Planner"]
)





