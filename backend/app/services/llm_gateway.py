import os
from typing import Optional, List, Dict, Any
import litellm
from litellm import completion
from dotenv import load_dotenv
import logging

# Ensure env is loaded
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
load_dotenv(env_path)

# Adjust logger
logger = logging.getLogger(__name__)

# Optionally suppress litellm verbose output if needed
litellm.suppress_debug_info = True

try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False
    logger.warning("llama-cpp-python is not installed. Local GGUF models will be disabled.")

class LLMGateway:
    """
    Centralized Gateway for calling Large Language Models.
    Prioritizes direct local GGUF execution, falls back to LiteLLM cloud routing.
    """
    
    def __init__(self):
        # 1. Local GGUF Configuration
        self.local_model_path = os.getenv("MODEL_PATH", r"F:\models\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")
        self.llm_provider = os.getenv("LLM_PROVIDER", "local")
        self.local_llm_instance = None
        self._local_initialized = False # Flag for lazy-loading
        
        # 2. Cloud Fallbacks
        self.kimi_model = "moonshot-v1-8k"
        self.openai_model = "gpt-4o"
        self.gemini_model = "gemini/gemini-pro"
        
        # Build Router Fallback List
        self.model_cascade = [
            {"model": self.kimi_model, "api_key": os.getenv("MOONSHOT_API_KEY")},
            {"model": self.gemini_model, "api_key": os.getenv("GOOGLE_API_KEY")},
            {"model": self.openai_model, "api_key": os.getenv("OPENAI_API_KEY")}
        ]

    def _init_local_model(self):
        """Lazy loader for large local models to prevent API startup freeze."""
        if self._local_initialized:
            return
            
        self._local_initialized = True
        if self.llm_provider == "local" and HAS_LLAMA_CPP and os.path.exists(self.local_model_path):
            # Qwen3.5-397B is exceedingly large, ensure defensive loading mapping
            try:
                logger.info(f"Lazy-loading local GGUF model from {self.local_model_path}...")
                self.local_llm_instance = Llama(
                    model_path=self.local_model_path,
                    n_ctx=4096,
                    n_gpu_layers=-1 # Allow library to determine best offloading
                )
                logger.info("Local model loaded successfully via lazy-load.")
            except Exception as e:
                logger.error(f"Failed to lazy-load local model {self.local_model_path}: {e}")

    def _generate_local(self, messages: List[Dict[str, str]], json_mode: bool) -> Optional[str]:
        # Ensure it attempts to load if configured
        self._init_local_model()
        
        if not self.local_llm_instance:
            return None
            
        try:
            logger.info("Attempting inference via local GGUF model")
            # Create completions strictly following chatML or provided templating
            response = self.local_llm_instance.create_chat_completion(
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"} if json_mode else None
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Local inference failed: {e}")
            return None

    def generate_insight(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> Optional[str]:
        """
        Attempts to generate an insight. Tries Local GGUF first, then cloud cascade.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Priority 1: Direct Local Execution
        if self.llm_provider == "local" and self.local_llm_instance:
            local_insight = self._generate_local(messages, json_mode)
            if local_insight:
                return local_insight
                
        # Priority 2: Cloud Fallback
        for config in self.model_cascade:
            model_name = config["model"]
            api_key = config.get("api_key")
            api_base = config.get("api_base")
            
            # Skip cloud models if keys are missing
            if not api_base and not api_key:
                logger.warning(f"Skipping {model_name} due to missing API key configuration.")
                continue
                
            try:
                logger.info(f"Attempting inference via model: {model_name}")
                kwargs = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.2, # Low temp for deterministic analytical generation
                }
                
                if api_key:
                    # litellm dynamically maps api key env vars based on string format but passing explicitly is safest if mixed
                    if "moonshot" in model_name:
                        os.environ["MOONSHOT_API_KEY"] = api_key
                    elif "gemini" in model_name:
                        os.environ["GEMINI_API_KEY"] = api_key
                    elif "gpt" in model_name:
                        os.environ["OPENAI_API_KEY"] = api_key

                if api_base:
                    kwargs["api_base"] = api_base
                    
                if json_mode and "gpt" in model_name:
                    kwargs["response_format"] = { "type": "json_object" }

                response = completion(**kwargs)
                content = response.choices[0].message.content
                logger.info(f"Successfully generated insight using {model_name}")
                return content
                
            except Exception as e:
                logger.error(f"Failed inference with {model_name}: {str(e)}")
                continue # Try next fallback

        logger.error("All models in the fallback cascade failed.")
        return "AI 分析暂时不可用，核心计算已完成。"

# Singleton Instance
llm_gateway = LLMGateway()
