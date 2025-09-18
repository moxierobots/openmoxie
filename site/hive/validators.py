"""
Input validation utilities for OpenMoxie
"""
import json
import re
from typing import Optional, Dict, Any
from django.core.exceptions import ValidationError


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


def validate_openai_api_key(api_key: str) -> bool:
    """
    Validate OpenAI API key format
    """
    if not api_key:
        return False
    
    # OpenAI API keys typically start with "sk-" and are 51 characters long
    # But we'll be more flexible to accommodate different key formats
    if len(api_key) < 20 or len(api_key) > 100:
        raise ValidationError("API key length should be between 20 and 100 characters")
    
    # Basic pattern check - should contain alphanumeric characters and common symbols
    if not re.match(r'^[a-zA-Z0-9\-_\.]+$', api_key):
        raise ValidationError("API key contains invalid characters")
    
    return True


def validate_google_api_key(api_key_json: str) -> Dict[str, Any]:
    """
    Validate Google API key JSON format
    """
    if not api_key_json:
        raise ValidationError("Google API key cannot be empty")
    
    try:
        parsed_json = json.loads(api_key_json)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")
    
    # Check for required fields in Google service account JSON
    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
    missing_fields = [field for field in required_fields if field not in parsed_json]
    
    if missing_fields:
        raise ValidationError(f"Missing required fields in Google API key: {', '.join(missing_fields)}")
    
    if parsed_json.get('type') != 'service_account':
        raise ValidationError("Google API key must be a service account key")
    
    return parsed_json


def validate_hostname(hostname: str) -> bool:
    """
    Validate hostname format
    """
    if not hostname:
        return True  # Hostname is optional
    
    # Basic hostname validation
    if len(hostname) > 255:
        raise ValidationError("Hostname is too long")
    
    # Allow localhost, IP addresses, and domain names
    hostname_pattern = re.compile(
        r'^(?:'
        r'localhost|'
        r'(?:\d{1,3}\.){3}\d{1,3}|'  # IP address
        r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'  # Domain
        r')(?::\d{1,5})?$'  # Optional port
    )
    
    if not hostname_pattern.match(hostname):
        raise ValidationError("Invalid hostname format")
    
    return True


def sanitize_input(input_string: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize input string by removing dangerous characters
    """
    if not isinstance(input_string, str):
        return str(input_string)
    
    # Remove null bytes and control characters except newlines and tabs
    sanitized = ''.join(char for char in input_string if ord(char) >= 32 or char in '\n\t')
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_device_name(name: str) -> bool:
    """
    Validate device name
    """
    if not name:
        raise ValidationError("Device name cannot be empty")
    
    if len(name) > 200:
        raise ValidationError("Device name is too long (max 200 characters)")
    
    # Allow alphanumeric, spaces, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        raise ValidationError("Device name contains invalid characters")
    
    return True


def validate_json_field(json_string: str, field_name: str) -> Dict[str, Any]:
    """
    Generic JSON field validation
    """
    if not json_string:
        return {}
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {field_name}: {str(e)}")