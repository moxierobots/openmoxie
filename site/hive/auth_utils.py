"""
API Authentication utilities for OpenMoxie
"""
import hashlib
import hmac
import time
from typing import Optional, Tuple
from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def generate_api_token(user_id: str, timestamp: Optional[int] = None) -> str:
    """
    Generate an API token for a user
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    # Use a combination of secret key, user ID, and timestamp
    secret_key = settings.SECRET_KEY
    message = f"{user_id}:{timestamp}"
    
    # Create HMAC signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{user_id}:{timestamp}:{signature}"


def validate_api_token(token: str, max_age_seconds: int = 3600) -> Tuple[bool, str]:
    """
    Validate an API token
    Returns (is_valid, user_id)
    """
    try:
        parts = token.split(':')
        if len(parts) != 3:
            return False, ""
        
        user_id, timestamp_str, provided_signature = parts
        timestamp = int(timestamp_str)
        
        # Check if token is too old
        current_time = int(time.time())
        if current_time - timestamp > max_age_seconds:
            logger.warning(f"API token expired for user {user_id}")
            return False, ""
        
        # Regenerate expected signature
        secret_key = settings.SECRET_KEY
        message = f"{user_id}:{timestamp}"
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures securely
        if hmac.compare_digest(expected_signature, provided_signature):
            return True, user_id
        else:
            logger.warning(f"Invalid API token signature for user {user_id}")
            return False, ""
            
    except (ValueError, IndexError) as e:
        logger.warning(f"Malformed API token: {str(e)}")
        return False, ""


def require_api_auth(max_age_seconds: int = 3600):
    """
    Decorator that requires API authentication via Authorization header
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check for Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            
            if not auth_header.startswith('Bearer '):
                return JsonResponse({
                    'error': 'Missing or invalid Authorization header. Use: Bearer <token>'
                }, status=401)
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            is_valid, user_id = validate_api_token(token, max_age_seconds)
            
            if not is_valid:
                return JsonResponse({
                    'error': 'Invalid or expired API token'
                }, status=401)
            
            # Add user_id to request for use in the view
            request.api_user_id = user_id
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


def require_api_key(view_func):
    """
    Alternative decorator that requires API key authentication
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check for API key in headers or query params
        api_key = request.META.get('HTTP_X_API_KEY') or request.GET.get('api_key')
        
        if not api_key:
            return JsonResponse({
                'error': 'Missing API key. Provide via X-API-Key header or api_key parameter'
            }, status=401)
        
        # For now, we'll use a simple validation against the OpenAI API key
        # In production, you'd want a proper API key management system
        from .models import HiveConfiguration
        
        try:
            config = HiveConfiguration.get_current()
            if not config.openai_api_key or api_key != config.openai_api_key:
                logger.warning(f"Invalid API key attempt from {request.META.get('REMOTE_ADDR', 'unknown')}")
                return JsonResponse({
                    'error': 'Invalid API key'
                }, status=401)
        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return JsonResponse({
                'error': 'Authentication system error'
            }, status=500)
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Simple rate limiting decorator
    """
    # This is a basic in-memory rate limiter
    # For production, you'd want to use Redis or similar
    request_counts = {}
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                                      request.META.get('REMOTE_ADDR', ''))
            
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Clean old entries
            request_counts[client_ip] = [
                timestamp for timestamp in request_counts.get(client_ip, [])
                if timestamp > window_start
            ]
            
            # Check rate limit
            if len(request_counts.get(client_ip, [])) >= max_requests:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Try again later.'
                }, status=429)
            
            # Add current request
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            request_counts[client_ip].append(current_time)
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator