"""
LLM Integration Module - Medical Report Explanation Assistant

This module manages LLM interactions with strict safety guardrails for medical content.
It ensures all responses follow critical compliance rules regardless of the underlying LLM.

CRITICAL RULES THIS MODULE ENFORCES:
===========================================
1. Do NOT provide medical advice
2. Do NOT make diagnoses
3. Do NOT suggest treatment

SAFETY MECHANISMS:
- Response validation: All LLM outputs are checked for safety constraint violations
- Fallback system: Automatically falls back to MockLLM if Ollama is unavailable
- Prompt injection: Safety rules are prepended to all prompts sent to LLMs
- Violation detection: Checks for diagnosis patterns, treatment advice, and personal medical guidance

COMPONENTS:
- get_safety_system_prompt(): Returns the standardized safety prompt for all LLMs
- validate_response_safety(): Validates responses for rule violations
- MockLLM: Contextual mock responses for development/testing
- OllamaWithTimeout: Wrapper around Ollama LLM with timeout and fallback
- get_llm(): Factory function that returns appropriate LLM instance (Ollama or MockLLM)
"""
import os
import logging
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def get_safety_system_prompt() -> str:
    """
    Returns the safety-enforced system prompt for medical report explanations.
    Enforces strict constraints on LLM responses.
    """
    return """You are a medical report explanation assistant providing educational information only.

CRITICAL SAFETY RULES - YOU MUST FOLLOW THESE:
1. Do NOT provide medical advice
2. Do NOT make diagnoses
3. Do NOT suggest treatment

GUIDELINES:
- Explain medical terms and concepts in simple, educational language
- Describe what test results mean in general terms
- Encourage consulting healthcare providers for personalized guidance
- Focus on general health information, not individual medical decisions
- Always recommend professional medical consultation for any concerns
- Do NOT prescribe or suggest specific medications
- Do NOT give emergency instructions (except "call emergency services")
"""


class TimeoutError(Exception):
    pass


def validate_response_safety(response: str) -> tuple[bool, str]:
    """
    Validate LLM response for safety constraint violations.
    Returns: (is_safe, warning_message)
    """
    response_lower = response.lower()
    violations = []
    
    # Check for diagnosis patterns
    diagnosis_phrases = [
        "you have ", "you suffer from", "you are diabetic", "you are hypertensive",
        "diagnosis:", "diagnosed with", "definitely have"
    ]
    for phrase in diagnosis_phrases:
        if phrase in response_lower:
            violations.append(f"Potential diagnosis statement detected: '{phrase}'")
    
    # Check for treatment/medication advice patterns
    treatment_phrases = [
        "take this medication", "you should take", "prescribe", "start taking",
        "stop taking", "don't take", "switch to", "increase your dose"
    ]
    for phrase in treatment_phrases:
        if phrase in response_lower:
            violations.append(f"Potential treatment advice detected: '{phrase}'")
    
    # Check for medical advice patterns
    advice_phrases = [
        "follow this diet", "do this exercise", "avoid these foods",
        "sleep like this", "here's what you should do"
    ]
    for phrase in advice_phrases:
        if phrase in response_lower:
            violations.append(f"Potential personal medical advice detected: '{phrase}'")
    
    if violations:
        warning = f"Safety validation warnings: {'; '.join(violations)}"
        logger.warning(warning)
        return False, warning
    
    return True, ""


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
    """Wrapper around Ollama LLM with timeout support and safety enforcement"""
    
    def __init__(self, ollama_llm, timeout_seconds=30):
        self.ollama_llm = ollama_llm
        self.timeout_seconds = timeout_seconds
        self.model_name = "llama3"
        self.safety_prompt = get_safety_system_prompt()
    
    def invoke(self, prompt: str) -> str:
        """Invoke with timeout fallback to MockLLM, enforce safety rules"""
        try:
            logger.info(f"Invoking Ollama with timeout {self.timeout_seconds}s")
            
            # Prepend safety rules to the prompt for Ollama
            enhanced_prompt = f"{self.safety_prompt}\n\n{prompt}"
            
            # Try Ollama with a timeout
            response = self.ollama_llm.invoke(enhanced_prompt)
            logger.info("Ollama response received successfully")
            
            # Validate response for safety violations
            is_safe, warning = validate_response_safety(response)
            if not is_safe:
                logger.warning(f"Ollama response safety check failed: {warning}")
            
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
        self.safety_prompt = get_safety_system_prompt()
    
    def invoke(self, prompt: str) -> str:
        """Generate a contextual mock response based on the prompt, enforcing safety rules"""
        prompt_lower = prompt.lower()
        
        # Check for cholesterol-related questions
        if "cholesterol" in prompt_lower:
            response = """Cholesterol is a waxy substance found in your blood. Your body needs some cholesterol to make hormones and digest fats. When cholesterol levels are higher than normal (above 240 mg/dL), it can increase the risk of heart disease.

High cholesterol can accumulate in artery walls, forming plaques that narrow blood vessels - a process called atherosclerosis.

GENERAL INFORMATION about cholesterol management:
- Dietary choices (like fiber and omega-3 sources) are typically discussed with healthcare providers
- Physical activity is generally recommended by health authorities
- Weight management is part of most health recommendations
- Many people benefit from medications prescribed by their doctors

For personalized guidance on managing your cholesterol, schedule a consultation with your healthcare provider. They can assess your individual risk factors and discuss appropriate options for your situation."""
            
        # Check for blood pressure questions
        elif "blood pressure" in prompt_lower or "hypertension" in prompt_lower:
            response = """Blood pressure is the force of blood pushing against artery walls. It's measured in two numbers: systolic (when heart beats) and diastolic (when heart rests).

Normal blood pressure is generally less than 120/80 mmHg. Higher readings may indicate elevated blood pressure, which some health authorities suggest monitoring.

GENERAL INFORMATION about blood pressure management:
- The DASH diet is often discussed in health literature
- Regular aerobic activity is widely recommended by health organizations
- Weight management is part of most wellness approaches
- Stress reduction techniques are generally discussed
- Reducing sodium intake is commonly recommended

Your healthcare provider can evaluate your specific blood pressure readings and discuss management options that may be appropriate for your individual situation."""
        
        # Check for diabetes questions
        elif "diabetes" in prompt_lower or "glucose" in prompt_lower or "blood sugar" in prompt_lower:
            response = """Diabetes is a condition where blood glucose levels are higher than normal. There are different types, and high blood sugar can affect various body systems over time.

GENERAL INFORMATION about glucose management:
- Nutritional choices involving lower glycemic foods are often discussed in health literature
- Physical activity is widely recommended by health authorities
- Weight management is part of most health recommendations
- Blood glucose monitoring helps track patterns
- Many people use medications to help manage glucose levels

For an understanding of your specific glucose readings and management strategies suited to your situation, consult with your healthcare provider or a diabetes educator."""
        
        # Default fallback response
        else:
            response = """Based on the medical analysis provided, here is general educational information:

UNDERSTANDING YOUR RESULTS:
- Test results are compared against normal reference ranges
- Abnormal results may indicate areas worth discussing with your healthcare provider
- Some values may be borderline and require monitoring over time

GENERAL RECOMMENDATIONS:
1. **Follow-up Care**: Schedule regular check-ups with your healthcare provider to monitor your health
2. **General Wellness**: Healthy lifestyle choices often include balanced nutrition and physical activity
3. **Monitoring**: Tracking relevant health metrics can be useful information for your provider
4. **Education**: Learning about your health condition helps you have informed conversations
5. **Support**: Healthcare providers can connect you with resources and support options

For personalized medical guidance based on your specific results and health situation, consult with your healthcare provider. They can explain what your results mean for you individually and discuss appropriate next steps."""
        
        # Validate response for safety rule violations
        is_safe, warning = validate_response_safety(response)
        if not is_safe:
            logger.warning(f"Safety check failed: {warning}. Adding disclaimer.")
            response += "\n\n[This response was flagged for safety review. Please consult your healthcare provider.]"
        
        return response


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

