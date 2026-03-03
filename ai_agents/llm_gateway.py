# ai_agents/llm_gateway.py
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Optional: If you want litellm as a unified wrapper. If not installed, can be a simple wrapper.
try:
    from litellm import completion
except ImportError:
    # Graceful degradation if litellm is not yet installed.
    # In a real setup, `pip install litellm` should be in requirements.
    pass

load_dotenv()

class LLMGateway:
    """
    Unified LLM Client Gateway to easily switch between Kimi, Local Open-Source, Gemini, OpenAI, Claude.
    """
    def __init__(self, default_model: Optional[str] = None):
        # Default model could be overriden by env or passed directly
        self.model = default_model or os.getenv("LLM_MODEL", "moonshot/moonshot-v1-8k")
        self.api_key = os.getenv("LLM_API_KEY") 
        self.api_base = os.getenv("LLM_API_BASE") # Useful for local models like vLLM / Ollama
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3) -> str:
        target_model = model or self.model
        
        try:
            # Using litellm standard completion interface
            # For litellm to route properly, Kimi models use "moonshot/moonshot-v1-8k"
            # OpenAI uses "gpt-4o", Gemini uses "gemini/gemini-pro", Anthropic uses "claude-3-5-sonnet-20240620"
            # Local Ollama uses "ollama/llama3"
            response = completion(
                model=target_model,
                messages=messages,
                temperature=temperature,
                api_base=self.api_base,
                # Litellm automatically picks up keys from OPENAI_API_KEY, MOONSHOT_API_KEY etc., 
                # but we can explicitly pass fallback
                api_key=self.api_key if self.api_key else None
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback block or error logging
            return f"Error calling LLM provider: {str(e)}"
