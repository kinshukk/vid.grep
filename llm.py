import os
import requests
import json
from typing import Optional, Dict, Any
import tiktoken

def get_api_key() -> str:
    """Get OpenRouter API key from environment."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    return api_key

def get_default_model() -> str:
    """Get default model from environment or return fallback."""
    return os.getenv('MODEL_NAME', 'anthropic/claude-3-haiku')

def call_llm(prompt: str, model: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
    """
    Make a raw API call to OpenRouter.
    
    Args:
        prompt: The prompt to send
        model: Model name (defaults to MODEL_NAME env var)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Response text from the model
    """
    if model is None:
        model = get_default_model()
    
    if max_tokens is None:
        max_tokens = 4000
    
    api_key = get_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": max_tokens
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")
    
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
    Returns approximate values for common models.
    """
    model_info = {
        'anthropic/claude-3-haiku': {
            'context_window': 200000,
            'max_output': 4096
        },
        'anthropic/claude-3-sonnet': {
            'context_window': 200000,
            'max_output': 4096
        },
        'anthropic/claude-3-opus': {
            'context_window': 200000,
            'max_output': 4096
        }
    }
    
    return model_info.get(model_name, {
        'context_window': 4096,  # Conservative fallback
        'max_output': 1000
    })