import os
import requests
from typing import Optional, Dict, Any
import tiktoken
from langfuse import observe, get_client
from dotenv import load_dotenv

load_dotenv()

def get_api_key() -> str:
    """Get OpenRouter API key from environment."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    return api_key

def get_env_variable(name: str, default: Optional[str] = None) -> str:
    """Get an environment variable or raise an error if not set."""
    value = os.getenv(name)
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"{name} environment variable not set")
    return value

def get_default_model() -> str:
    """Get default model from environment."""
    return get_env_variable('MODEL_NAME', 'anthropic/claude-3.5-sonnet')

def get_system_prompt() -> str:
    """Get system prompt from environment."""
    return get_env_variable('SYSTEM_PROMPT', "You are a helpful assistant.")

def get_max_output() -> int:
    """Get max output tokens from environment."""
    return int(get_env_variable('MAX_OUTPUT', '8192'))

def get_context_window() -> int:
    """Get context window size from environment."""
    return int(get_env_variable('CONTEXT_WINDOW', '200000'))

@observe()
def call_llm(prompt: str, model: Optional[str] = None, max_tokens: Optional[int] = None, system_prompt: Optional[str] = None) -> str:
    """
    Make a raw API call to OpenRouter.
    
    Args:
        prompt: The prompt to send
        model: Model name (defaults to MODEL_NAME env var)
        max_tokens: Maximum tokens to generate
        system_prompt: The system prompt to use
        
    Returns:
        Response text from the model
    """
    if model is None:
        model = get_default_model()
    
    if max_tokens is None:
        max_tokens = get_max_output()

    if system_prompt is None:
        system_prompt = get_system_prompt()

    api_key = get_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user", 
            "content": prompt
        }
    ]

    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content']

def count_tokens(text: str, model: str = None) -> int:
    """
    Count tokens in text for the given model.
    Uses tiktoken for approximation since exact tokenization varies by model.
    """
    if model is None:
        model = get_default_model()
    
    # Use cl100k_base for Claude models as approximation
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def get_model_info(model_name: str) -> Dict[str, Any]:
    """
    Get model information including context window size.
    """
    if model_name == get_default_model():
        return {
            'context_window': get_context_window(),
            'max_output': get_max_output()
        }

    return {
        'context_window': get_context_window(),
        'max_output': get_max_output()
    }