from openai import OpenAI
from anthropic import Anthropic
import logging
import os

logger = logging.getLogger(__name__)

_OPENAPI_KEY = None
_ANTHROPIC_KEY = None

def set_openai_key(key):
    global _OPENAPI_KEY
    _OPENAPI_KEY = key

def set_anthropic_key(key):
    global _ANTHROPIC_KEY
    _ANTHROPIC_KEY = key

def create_openai():
    global _OPENAPI_KEY
    return OpenAI(api_key=_OPENAPI_KEY)

def create_claude():
    global _ANTHROPIC_KEY
    return Anthropic(api_key=_ANTHROPIC_KEY)

def get_claude_model():
    """Get the Claude model to use from environment or default"""
    return os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
