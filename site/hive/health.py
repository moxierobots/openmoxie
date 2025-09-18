"""
Health check utilities for OpenMoxie
"""
import logging
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import time
import os

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Comprehensive health check endpoint
    """
    health_status = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'environment': getattr(settings, 'DJANGO_ENV', 'unknown'),
        'checks': {}
    }
    
    overall_healthy = True
    
    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        overall_healthy = False
    
    # MQTT configuration check
    try:
        mqtt_config = getattr(settings, 'MQTT_ENDPOINT', {})
        if mqtt_config:
            health_status['checks']['mqtt_config'] = {
                'status': 'healthy',
                'message': f"MQTT configured for {mqtt_config.get('host', 'unknown')}:{mqtt_config.get('port', 'unknown')}"
            }
        else:
            health_status['checks']['mqtt_config'] = {
                'status': 'warning',
                'message': 'MQTT configuration not found'
            }
    except Exception as e:
        health_status['checks']['mqtt_config'] = {
            'status': 'unhealthy',
            'message': f'MQTT configuration error: {str(e)}'
        }
    
    # File system checks
    work_dir = getattr(settings, 'DATA_STORE_DIR', '/app/site/work')
    try:
        if os.path.exists(work_dir) and os.access(work_dir, os.W_OK):
            health_status['checks']['filesystem'] = {
                'status': 'healthy',
                'message': f'Work directory {work_dir} is writable'
            }
        else:
            health_status['checks']['filesystem'] = {
                'status': 'unhealthy',
                'message': f'Work directory {work_dir} not accessible'
            }
            overall_healthy = False
    except Exception as e:
        health_status['checks']['filesystem'] = {
            'status': 'unhealthy',
            'message': f'Filesystem check failed: {str(e)}'
        }
        overall_healthy = False
    
    # OpenAI configuration check (non-blocking)
    try:
        from .models import HiveConfiguration
        config = HiveConfiguration.get_current()
        if config and config.openai_api_key:
            health_status['checks']['openai'] = {
                'status': 'healthy',
                'message': 'OpenAI API key configured'
            }
        else:
            health_status['checks']['openai'] = {
                'status': 'warning',
                'message': 'OpenAI API key not configured - some features may not work'
            }
    except Exception as e:
        health_status['checks']['openai'] = {
            'status': 'warning',
            'message': f'OpenAI configuration check failed: {str(e)}'
        }
    
    # Memory and disk space checks (basic)
    try:
        import shutil
        disk_usage = shutil.disk_usage('/')
        free_space_gb = disk_usage.free / (1024**3)
        
        if free_space_gb < 1.0:  # Less than 1GB
            health_status['checks']['disk_space'] = {
                'status': 'warning',
                'message': f'Low disk space: {free_space_gb:.1f}GB free'
            }
        else:
            health_status['checks']['disk_space'] = {
                'status': 'healthy',
                'message': f'Disk space OK: {free_space_gb:.1f}GB free'
            }
    except Exception as e:
        health_status['checks']['disk_space'] = {
            'status': 'warning',
            'message': f'Could not check disk space: {str(e)}'
        }
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
    elif any(check.get('status') == 'warning' for check in health_status['checks'].values()):
        health_status['status'] = 'degraded'
    
    # Return appropriate HTTP status
    if health_status['status'] == 'healthy':
        status_code = 200
    elif health_status['status'] == 'degraded':
        status_code = 200  # Still OK for load balancer
    else:
        status_code = 503  # Service unavailable
    
    return JsonResponse(health_status, status=status_code)


def simple_health_check(request):
    """
    Simple health check for basic liveness probe
    """
    try:
        # Just check if Django is responding
        return JsonResponse({'status': 'ok', 'timestamp': int(time.time())})
    except Exception:
        return JsonResponse({'status': 'error'}, status=500)


def readiness_check(request):
    """
    Readiness check - more comprehensive than liveness
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({'status': 'ready', 'timestamp': int(time.time())})
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JsonResponse({'status': 'not_ready', 'error': str(e)}, status=503)