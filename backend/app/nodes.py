from app.state import State
import logging

logger = logging.getLogger("nodes")

def document_parser_node(state: State):
    logger.info("Reached Document Parser Node: %s", state)

    parsed_text = "Patient Name: John Doe\nFindings: Elevated cholesterol..."
    # Immediately clean PII
    state.cleaned_text = parsed_text.replace("John Doe", "[REDACTED]")
    return state

def clinical_analysis_node(state: State):
    logger.info("Reached Clinical Analysis Node: %s", state)

    state.clinical_analysis = "Summary: Elevated cholesterol, recommend lifestyle changes."
    return state

def risk_assessment_node(state: State):
    logger.info("Reached Risk Assessment Node: %s", state)

    state.risk_assessment = ["High cholesterol"]
    return state

def insights_summary_node(state: State):
    logger.info("Reached Insights Summary Node: %s", state)

    state.insight_summary = f"{state.clinical_analysis}; Risks: {', '.join(state.risk_assessment)}"
    return state

def qna_node(state: State):
    logger.info("Reached QnA Node: %s", state)

    state.qna_answer = f"QnA response..."
    state.pre_compliance_response = f"QnA response..."
    return state

def compliance_node(state: State):
    logger.info("Reached Compliance Node: %s", state)

    state.final_response = state.pre_compliance_response
    return state
