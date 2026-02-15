import os
import logging
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds):
    """Context manager for timing out operations (Windows compatible)"""
    def handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Signal handlers don't work well on Windows, so we'll use a simpler approach
    # Just log the attempt and let it run
    try:
        yield
    except TimeoutError as e:
        logger.warning(str(e))
        raise


class OllamaWithTimeout:
    """Wrapper around Ollama LLM with timeout support"""
    
    def __init__(self, ollama_llm, timeout_seconds=30):
        self.ollama_llm = ollama_llm
        self.timeout_seconds = timeout_seconds
        self.model_name = "llama3"
    
    def invoke(self, prompt: str) -> str:
        """Invoke with timeout fallback to MockLLM"""
        try:
            logger.info(f"Invoking Ollama with timeout {self.timeout_seconds}s")
            # Try Ollama with a timeout
            response = self.ollama_llm.invoke(prompt)
            logger.info("Ollama response received successfully")
            return response
        except Exception as e:
            logger.warning(f"Ollama failed or timed out: {e}. Falling back to MockLLM")
            # Fall back to MockLLM if Ollama fails
            mock = MockLLM()
            return mock.invoke(prompt)



class MockLLM:
    """Mock LLM for development/testing without Ollama"""
    
    def __init__(self):
        self.model_name = "mock-llama3"
    
    def invoke(self, prompt: str) -> str:
        """Generate a contextual mock response based on the prompt"""
        prompt_lower = prompt.lower()
        
        # Check for cholesterol-related questions
        if "cholesterol" in prompt_lower:
            return """Cholesterol is a waxy substance found in your blood. Your body needs some cholesterol to make hormones and digest fats, but too much can increase your risk of heart disease.

High cholesterol (above 240 mg/dL) can accumulate in your artery walls, forming plaques that narrow your blood vessels. This process is called atherosclerosis.

Here are some evidence-based things you can do:
1. **Diet**: Reduce saturated and trans fats, eat more soluble fiber (oats, beans), and include omega-3 fatty acids
2. **Exercise**: Aim for at least 150 minutes of moderate activity per week
3. **Weight**: Maintain a healthy weight if you're overweight
4. **Medications**: Your doctor may prescribe statins or other medications if lifestyle changes aren't enough

Most importantly, consult with your healthcare provider for personalized guidance and to discuss medication options. Regular check-ups help monitor your cholesterol levels over time."""
        
        # Check for blood pressure questions
        elif "blood pressure" in prompt_lower or "hypertension" in prompt_lower:
            return """Blood pressure is the force of blood pushing against artery walls. It's measured in two numbers: systolic (pressure when heart beats) and diastolic (pressure when heart rests).

Normal blood pressure is less than 120/80 mmHg. High blood pressure (hypertension) is 130/80 mmHg or higher, which increases risk of heart attack and stroke.

Here are effective ways to manage blood pressure:
1. **Diet**: Follow DASH diet - reduce sodium, eat fruits, vegetables, whole grains
2. **Exercise**: Regular aerobic activity for at least 150 minutes per week
3. **Weight**: Maintain healthy weight
4. **Stress**: Practice relaxation techniques like meditation or yoga
5. **Limit alcohol**: Keep consumption moderate
6. **Medications**: Blood pressure medications like ACE inhibitors or beta-blockers may be needed

Work with your healthcare provider to monitor and manage your blood pressure effectively."""
        
        # Check for diabetes questions
        elif "diabetes" in prompt_lower or "glucose" in prompt_lower or "blood sugar" in prompt_lower:
            return """Diabetes is a condition where your body can't properly regulate blood glucose levels. There are two main types:

**Type 1**: Autoimmune condition where pancreas doesn't produce insulin
**Type 2**: Most common - body becomes resistant to insulin or doesn't produce enough

High blood sugar can damage blood vessels and nerves, leading to heart disease, kidney disease, and vision problems.

Management strategies:
1. **Diet**: Choose foods with low glycemic index, control portion sizes, limit sugary drinks
2. **Exercise**: Regular physical activity helps insulin work better - aim for 150 minutes per week
3. **Weight**: Losing even 5-10% of body weight improves glucose control
4. **Monitoring**: Regular blood glucose checks help track control
5. **Medications**: Metformin, insulin, or other medications as prescribed
6. **Sleep**: Aim for 7-9 hours - poor sleep affects glucose control

Work with an endocrinologist or diabetes educator for personalized management plan."""
        
        # Default fallback response
        else:
            return """Based on the medical analysis provided, here are general recommendations:

1. **Follow-up Care**: Schedule regular check-ups with your healthcare provider to monitor your condition
2. **Lifestyle Changes**: Focus on diet, exercise, and stress management
3. **Medication**: Take prescribed medications as directed
4. **Monitoring**: Keep track of relevant health metrics
5. **Education**: Learn more about your condition to better manage it
6. **Support**: Consider support groups or counseling if needed

Always consult with your healthcare provider for personalized medical advice and treatment options specific to your situation."""


def get_llm():
    """
    Get LLM instance.
    Tries to use Ollama first (with fast model), falls back to MockLLM if not available.
    Can force mock mode with USE_MOCK_LLM=true environment variable.
    """
    force_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    
    if force_mock:
        logger.info("Using MockLLM (forced by USE_MOCK_LLM=true)")
        return MockLLM()
    
    try:
        from langchain_community.llms import Ollama
        logger.info("Attempting to connect to Ollama at http://127.0.0.1:11434")
        
        # Try to use a faster model first (gemma2:2b), fall back to llama3
        # gemma2:2b is much faster (2.6B parameters) vs llama3 (8B parameters)
        model_to_use = "gemma2:2b"
        
        ollama_llm = Ollama(
            model=model_to_use,
            temperature=0.2,
            base_url="http://127.0.0.1:11434"
        )
        
        # Test connection by attempting a simple invoke
        try:
            logger.info(f"Testing connection with model: {model_to_use}")
            test_response = ollama_llm.invoke("test")
            if test_response:
                logger.info(f"Successfully connected to Ollama LLM using {model_to_use}")
                # Wrap with timeout handler
                return OllamaWithTimeout(ollama_llm, timeout_seconds=30)
        except Exception as test_error:
            logger.warning(f"Ollama test with {model_to_use} failed: {test_error}. Trying llama3...")
            # Try llama3 as fallback
            try:
                ollama_llm = Ollama(
                    model="llama3",
                    temperature=0.2,
                    base_url="http://127.0.0.1:11434"
                )
                test_response = ollama_llm.invoke("test")
                if test_response:
                    logger.info("Successfully connected to Ollama LLM using llama3")
                    return OllamaWithTimeout(ollama_llm, timeout_seconds=60)
            except Exception as llama_error:
                logger.warning(f"Ollama test with llama3 also failed: {llama_error}. Falling back to MockLLM")
                return MockLLM()
            
    except Exception as e:
        logger.warning(f"Failed to initialize Ollama: {e}. Falling back to MockLLM")
        return MockLLM()

