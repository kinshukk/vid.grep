"""
Provides a simple, configured interface for making API calls to LLMs via OpenRouter.

This module handles retrieving API keys and other configuration from environment
variables and provides a core `call_llm` function for executing calls. It is
integrated with Langfuse for logging and observability.
"""
import os
import requests
from typing import Optional, Dict, Any
import tiktoken
from langfuse import observe
from dotenv import load_dotenv

load_dotenv()

def get_api_key() -> str:
    """Retrieves the OpenRouter API key from environment variables."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    return api_key

def get_env_variable(name: str, default: Optional[str] = None) -> str:
    """
    Gets an environment variable, raising an error if it's not set and no
    default is provided.
    """
    value = os.getenv(name)
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"{name} environment variable not set")
    return value

def get_openrouter_api_base() -> str:
    """Returns the OpenRouter API base URL."""
    return get_env_variable('OPENROUTER_API_BASE', 'https://openrouter.ai/api/v1')

def get_default_model() -> str:
    """Returns the default model name for API calls."""
    return get_env_variable('MODEL_NAME', 'anthropic/claude-3.5-sonnet')

def get_system_prompt() -> str:
    """Returns the default system prompt."""
    return get_env_variable('SYSTEM_PROMPT', "You are a helpful assistant.")

def get_max_output() -> int:
    """Returns the maximum number of tokens for the model's output."""
    return int(get_env_variable('MAX_OUTPUT', '8192'))

def get_context_window() -> int:
    """Returns the context window size for the model."""
    return int(get_env_variable('CONTEXT_WINDOW', '200000'))

@observe()
def call_llm(prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
    """
    Makes a raw API call to the configured LLM.

    Args:
        prompt: The user prompt to send to the model.
        system_prompt: An optional system prompt. If None, uses the default.
        model: The model to use. If None, uses the default.
        max_tokens: The maximum number of tokens to generate. If None, uses the default.

    Returns:
        The text response from the LLM.

    Raises:
        requests.exceptions.RequestException: For any network or API-related errors.
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
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    
    response = requests.post(
        f"{get_openrouter_api_base()}/chat/completions",
        headers=headers,
        json=data
    )
    
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content']

def count_tokens(text: str, model: str) -> int:
    """
    Counts the number of tokens in a given text string for a specified model.

    Uses tiktoken for an approximation, as exact tokenization can vary.

    Args:
        text: The text to analyze.
        model: The model name (used to select the appropriate tokenizer).

    Returns:
        The estimated number of tokens.
    """
    # Using cl100k_base as a general approximation for modern models.
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def get_default_model_info() -> Dict[str, Any]:
    """
    Returns a dictionary containing information about the default model,
    such as its context window and max output tokens.
    """
    return {
        'context_window': get_context_window(),
        'max_output': get_max_output()
    }
