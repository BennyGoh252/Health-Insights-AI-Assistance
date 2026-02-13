from langgraph.graph import StateGraph, START, END
from fastapi import APIRouter, Header, Request, UploadFile, File, Form, HTTPException, Response
from typing import Optional
from api.models.responses import ChatResponse
from app.state import State
from core.file_validators import FileValidator
from datetime import datetime
from zoneinfo import ZoneInfo
from agents.orchestrator import orchestrator
import app.nodes as nodes
import logging  

logger = logging.getLogger("chat")
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    message: Optional[str] = Form(None, description="User's text message"),
    file: Optional[UploadFile] = File(None, description="Optional file upload"),
    response: Response = None,
    x_session_id: Optional[str] = Header(None)
):
    
    # Validate: must have either message or file
    validate_input(message, file)
    
    # Get managers from app state 
    session_manager = request.app.state.session_manager

    # Get session data and set session id in response header
    session_data = await session_manager.get_or_create_session(x_session_id)
    current_session_id = session_data["session_id"]
    response.headers["X-Session-ID"] = current_session_id
    
    logger.info("Session Data:", session_data)

    # Prepare state for graph
    file_meta = None
    file_bytes = None

    if file:
        # Validate file type
        file_bytes = await file.read() 
        is_valid, error = FileValidator.validate_file(file_bytes, file.filename) 
        if not is_valid: 
         raise HTTPException(status_code=400, detail=error)
        
        file_meta = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_bytes)
        }

    # Build graph once and store in app.state
    graph = request.app.state.graph

    initial_state = State(
        session_id=current_session_id,
        input_text=message,
        file_meta=file_meta,
        file_bytes=file_bytes
    )

    # Run LangGraph Orchestrator
    final_state = graph.invoke(initial_state)

    logger.info("Response state from graph: %s", final_state)

    # Persist session metadata
    now = datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

    session_data["last_active"] = now
    session_data["message_count"] += 1 if message else 0
    session_data["upload_count"] += 1 if file else 0

    # Append upload history details if there was a file upload in this interaction
    if file_meta:
        session_data["upload_history"].append({
            "filename": file_meta["filename"],
            "content_type": file_meta["content_type"],
            "size": file_meta["size"],
            "created_at": now
        })

    # Add clinical analysis metadata
    if final_state.get("clinical_analysis"):
        session_data["analysis"] = {
            "clinical_analysis": final_state.get("clinical_analysis"),
            "risk_assessment": final_state.get("risk_assessment"),
            "insight_summary": final_state.get("insight_summary"),
            "last_analyzed_at": now
        }
        session_data["has_active_analysis"] = True

    # Add conversation history
    session_data["conversation_history"].append({
        "timestamp": now,
        "input_text_snippet": (message or "")[:200],
        "response_snippet": (final_state.get("final_response") or "")[:400]
    })

    logger.info("Final session state: %s", session_data)

    await session_manager.save_session(current_session_id, session_data)

    # -----------------------------
    # Return final response
    # -----------------------------
    return ChatResponse(
        message=final_state.get("final_response"),
        has_active_analysis=bool(final_state.get("analysis_state"))
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Health Insights AI"}


def validate_input(message: Optional[str], file: Optional[UploadFile]):
    if not message and not file:
        raise HTTPException(
            status_code=400,
            detail="Must provide either a message or a file"
        )
    
def build_graph():
    """
    Build the orchestrator graph with 3 routing scenarios:
    
    1. Text only -> QnA → Compliance -> END
    2. File only -> Document Parser -> Clinical -> Risk -> Insights -> Compliance -> END  
    3. File + Text -> Document Parser -> Clinical -> Risk -> Insights -> QnA -> Compliance -> END
    """
    
    builder = StateGraph(State)

    # Add all nodes
    builder.add_node("orchestrator", orchestrator.orchestrator_node)
    builder.add_node("document_parser", nodes.document_parser_node)
    builder.add_node("clinical_analysis", nodes.clinical_analysis_node)
    builder.add_node("risk_assessment", nodes.risk_assessment_node)
    builder.add_node("insights_summary", nodes.insights_summary_node)
    builder.add_node("qna", nodes.qna_node)
    builder.add_node("compliance", nodes.compliance_node)

    # Entry point
    builder.add_edge(START, "orchestrator")

    # ============================================
    # Conditional routing from orchestrator
    # ============================================
    def route_from_orchestrator(state: State) -> str:
        """
        Determine initial route based on input.
        
        Routes:
        - "doc_pipeline" -> File only OR File + Text
        - "qna" -> Text only
        """
        next_node = state.next_node
        
        if next_node == "doc_pipeline" or next_node == "doc_then_qna":
            return "document_parser"
        elif next_node == "qna":
            return "qna"
        else:
            # Fallback - shouldn't happen
            return "compliance"
        
    builder.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "document_parser": "document_parser",
            "qna": "qna",
            "compliance": "compliance"
        }
    )   
    
    # ============================================
    # Document pipeline path
    # ============================================
    
    builder.add_edge("document_parser", "clinical_analysis")
    builder.add_edge("risk_assessment", "insights_summary")
    
    # ============================================
    # Conditional routing from clinical_analysis
    # ============================================
    def route_from_clinical_analysis(state: State) -> str:
        """
        Determine route after clinical analysis.
        
        Routes:
        - if medical related -> route to risk_assessment
        - if not medical related -> route to compliance (skip risk assessment)
        """
        next_node = state.next_node
        
        if next_node == "medical_related":
            return "risk_assessment"
        elif next_node == "off-topic":
            return "compliance"
        else:
            # Fallback - shouldn't happen
            return "compliance"
    

    builder.add_conditional_edges(
        "clinical_analysis",
        route_from_clinical_analysis,
        {
            "risk_assessment": "risk_assessment",
            "compliance": "compliance"
        }
    )

    # ============================================
    # After insights: Check if we need QnA
    # ============================================
    def route_after_insights(state: State) -> str:
        """
        After document analysis:
        - If user asked a question (file + text) → Go to QnA
        - If file only → Go straight to compliance
        """
        next_node = state.next_node
        
        # If user uploaded file + asked a question
        if next_node == "doc_then_qna":
            return "qna"
        else:
            # File only - go straight to compliance
            return "compliance"
    
    builder.add_conditional_edges(
        "insights_summary",
        route_after_insights,
        {
            "qna": "qna",
            "compliance": "compliance"
        }
    )
    
    # ============================================
    # QnA always goes to compliance
    # ============================================
    builder.add_edge("qna", "compliance")
    
    # ============================================
    # Compliance is the final node before END
    # ============================================
    builder.add_edge("compliance", END)

    return builder.compile()