import json
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger("prompt_loader")

def load_prompt_config(module: str, key: str, version: str = "v1.0") -> Dict[str, Any]:
    """
    Load full prompt configuration including system, model, temperature, etc.
    
    Structure: prompts/module/version/prompts.json
    
    Args:
        module: e.g., "orchestrator", "clinical_analysis"
        key: e.g., "classification", "off_topic_response"
        version: e.g., "v1.0", "v1.2"
        
    Returns:
        Dictionary with 'system', 'model', 'temperature', 'description', etc.
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        KeyError: If key not found in prompts
    """
    backend_dir = Path(__file__).parent.parent
    prompt_file = backend_dir / "prompts" / module / version / "prompts.json"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    if key not in prompts:
        raise KeyError(f"Prompt key '{key}' not found in {module}/{version}")
    
    return prompts[key]
