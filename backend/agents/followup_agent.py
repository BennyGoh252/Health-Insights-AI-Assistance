"""
Follow-up Agent
Handles user follow-up questions after report summary is generated.
Ensures no diagnosis or treatment advice is given.
"""

from typing import Dict, Any
from core.llm import get_llm
import logging

logger = logging.getLogger(__name__)


def followup_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expected state structure:
    {
        "session_id": str,
        "summary": str,
        "chat_history": list,
        "user_question": str
    }
    """

    try:
        # Get LLM instance (now done here, not at module level)
        llm = get_llm()
        
        session_id = state.get("session_id")
        report_summary = state.get("summary", "")
        user_question = state.get("user_question", "")
        chat_history = state.get("chat_history", [])

        logger.info(f"[FollowUpAgent] Session: {session_id}")
        logger.info(f"[FollowUpAgent] Question: {user_question}")

        # Safety Prompt
        system_prompt = """
You are a medical report explanation assistant.

IMPORTANT RULES:
- You are NOT a doctor.
- Do NOT provide diagnosis.
- Do NOT recommend treatment.
- Do NOT give emergency instructions.
- Provide general educational explanations only.
- Encourage consulting healthcare professionals when appropriate.
"""

        # Construct conversation context
        history_text = ""
        for msg in chat_history:
            history_text += f"{msg['role']}: {msg['content']}\n"

        prompt = f"""
{system_prompt}

Medical Report Summary:
{report_summary}

Previous Conversation:
{history_text}

User Question:
{user_question}

Provide a clear, simple explanation:
"""

        response = llm.invoke(prompt)

        logger.info(f"[FollowUpAgent] Response generated")

        return {
            "followup_answer": response,
            "chat_history": chat_history + [
                {"role": "user", "content": user_question},
                {"role": "assistant", "content": response},
            ],
        }

    except Exception as e:
        logger.error(f"[FollowUpAgent] Error: {e}", exc_info=True)
        raise