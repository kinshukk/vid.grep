import os
from functools import wraps
from langfuse import Langfuse
from langfuse.model import CreateTrace, CreateGeneration
from datetime import datetime
import inspect

# Initialize Langfuse from environment variables
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

def langfuse_logging(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Extract trace_name from kwargs, with a default
        trace_name = kwargs.pop("trace_name", f"{fn.__name__}-trace")
        
        # Get the signature of the wrapped function
        sig = inspect.signature(fn)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Extract relevant parameters for logging
        model = bound_args.arguments.get('model')
        max_tokens = bound_args.arguments.get('max_tokens')
        system_prompt = bound_args.arguments.get('system_prompt')
        prompt = bound_args.arguments.get('prompt')

        # Create a trace
        trace = langfuse.trace(CreateTrace(name=trace_name))

        # Prepare messages for logging
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if prompt:
            messages.append({"role": "user", "content": prompt})

        # Create a generation
        generation = trace.generation(CreateGeneration(
            name=f"{fn.__name__}-generation",
            model=model,
            model_parameters={"max_tokens": str(max_tokens)},
            prompt=messages,
            start_time=datetime.now(),
        ))

        try:
            # Call the original function
            result = fn(*args, **kwargs)
            
            # Log the output
            generation.end(output=result)
            
            return result
        except Exception as e:
            # Log the error
            generation.end(output=str(e), level="ERROR")
            raise
        finally:
            # Ensure Langfuse data is sent
            langfuse.flush()
            
    return wrapper
