#!/usr/bin/env python
"""
Direct test of the followup_agent to show it works
"""
import sys

# Add backend to path
sys.path.insert(0, 'd:\\nus-iss\\Health-Insights-AI-Assistance\\backend')

from agents.followup_agent import followup_agent  # type: ignore

def test_followup_agent():
    """Test the followup agent directly"""
    
    print("Testing followup_agent directly...")
    print("-" * 60)
    
    # Prepare test state
    test_state = {
        "session_id": "test-123",
        "summary": "Patient Name: John Doe\nFindings: Elevated cholesterol levels (>240 mg/dL), increased risk of cardiovascular disease.",
        "user_question": "What does elevated cholesterol mean and what should I do about it?",
        "chat_history": []
    }
    
    print(f"Input Question: {test_state['user_question']}")
    print(f"Analysis Summary: {test_state['summary']}")
    print("-" * 60)
    
    try:
        # Run the followup agent
        result = followup_agent(test_state)
        
        print(f"\nFollowup Agent Result:")
        print(f"{'=' * 60}")
        print(result.get("followup_answer", "No answer returned"))
        print(f"{'=' * 60}")
        
        # Check if we got an LLM response
        answer = result.get("followup_answer", "")
        if answer and len(answer) > 20:  # Check if we got a meaningful response
            print("\n[SUCCESS] LLM output received!")
            print(f"Response length: {len(answer)} characters")
            return True
        else:
            print("\n[FAILED] No meaningful LLM output")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_followup_agent()
    sys.exit(0 if success else 1)
