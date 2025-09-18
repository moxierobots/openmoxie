"""
API Authentication utilities for OpenMoxie
"""
import hashlib
import hmac
import time
import secrets
import threading
from typing import Optional, Tuple, Dict
from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.core.cache import cache
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Thread-safe cleanup for rate limiter
_rate_limit_lock = threading.Lock()
_last_cleanup_time = 0
CLEANUP_INTERVAL = 300  # Clean up every 5 minutes


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


def generate_api_key() -> str:
    """
    Generate a secure API key
    """
    return f"om_{secrets.token_urlsafe(32)}"


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate that an API key has the correct format
    """
    if not api_key:
        return False

    # OpenMoxie API keys should start with 'om_' and be properly formatted
    if not api_key.startswith('om_') or len(api_key) < 20:
        return False

    # Check for valid characters
    import re
    if not re.match(r'^om_[a-zA-Z0-9_-]+$', api_key):
        return False

    return True


def require_api_key(view_func):
    """
    Decorator that requires API key authentication
    Uses a separate API key system instead of reusing OpenAI key
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check for API key in headers or query params
        api_key = request.META.get('HTTP_X_API_KEY') or request.GET.get('api_key')

        if not api_key:
            return JsonResponse({
                'error': 'Missing API key. Provide via X-API-Key header or api_key parameter'
            }, status=401)

        # Validate API key format
        if not validate_api_key_format(api_key):
            logger.warning(f"Invalid API key format attempt from {request.META.get('REMOTE_ADDR', 'unknown')}")
            return JsonResponse({
                'error': 'Invalid API key format'
            }, status=401)

        # Check against stored API keys
        # For now, we'll check if the key exists in the database
        from .models import APIKey

        try:
            # Use cache to avoid database hits for every request
            cache_key = f"api_key_valid:{api_key}"
            is_valid = cache.get(cache_key)

            if is_valid is None:
                # Not in cache, check database
                api_key_obj = APIKey.objects.filter(key=api_key, is_active=True).first()
                is_valid = api_key_obj is not None

                if is_valid:
                    # Cache for 5 minutes
                    cache.set(cache_key, True, 300)
                    # Update last used timestamp
                    api_key_obj.last_used = timezone.now()
                    api_key_obj.save(update_fields=['last_used'])

            if not is_valid:
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
    Rate limiting decorator with automatic cleanup
    Uses Django cache for production-ready rate limiting
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get client identifier
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            else:
                client_ip = request.META.get('REMOTE_ADDR', '')

            if not client_ip:
                client_ip = 'unknown'

            # Use cache for rate limiting
            cache_key = f"rate_limit:{client_ip}"

            try:
                # Get current request count
                request_count = cache.get(cache_key, 0)

                # Check rate limit
                if request_count >= max_requests:
                    retry_after = window_seconds
                    response = JsonResponse({
                        'error': 'Rate limit exceeded. Try again later.',
                        'retry_after': retry_after
                    }, status=429)
                    response['Retry-After'] = str(retry_after)
                    return response

                # Increment counter
                cache.set(cache_key, request_count + 1, window_seconds)

            except Exception as e:
                # If cache fails, log but don't block the request
                logger.error(f"Rate limiting error: {str(e)}")

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator


def cleanup_old_tokens():
    """
    Cleanup expired API tokens from the database
    Should be called periodically via a management command or celery task
    """
    from .models import APIKey
    from django.utils import timezone
    from datetime import timedelta

    # Remove API keys that haven't been used in 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = APIKey.objects.filter(
        last_used__lt=cutoff_date,
        is_active=False
    ).delete()[0]

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired API keys")
