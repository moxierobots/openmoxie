"""
Middleware to bypass ALLOWED_HOSTS check and HTTPS redirect for health endpoints from internal IPs.
"""

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import ipaddress


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Bypass ALLOWED_HOSTS validation and HTTPS redirect for health check endpoints
    when accessed from internal/private IP addresses.

    This middleware must be placed BEFORE SecurityMiddleware in the MIDDLEWARE list.
    """

    # Health check paths
    HEALTH_PATHS = ['/health', '/health/', '/healthz', '/healthz/']

    # Internal IP ranges
    INTERNAL_NETWORKS = [
        '127.0.0.0/8',      # Localhost
        '10.0.0.0/8',       # Private network
        '172.16.0.0/12',    # Private network
        '192.168.0.0/16',   # Private network
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        # Store original SECURE_SSL_REDIRECT value
        self.original_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)

    def __call__(self, request):
        # Check if this is a health check from internal IP
        is_health_check = False

        if request.path in self.HEALTH_PATHS:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(',')[0].strip()
            else:
                client_ip = request.META.get('REMOTE_ADDR')

            # Check if IP is internal
            try:
                ip = ipaddress.ip_address(client_ip)
                for network in self.INTERNAL_NETWORKS:
                    if ip in ipaddress.ip_network(network):
                        is_health_check = True
                        break
            except (ValueError, TypeError):
                pass

        if is_health_check:
            # Bypass ALLOWED_HOSTS
            request.get_host = lambda: 'localhost'

            # Temporarily disable SECURE_SSL_REDIRECT
            settings.SECURE_SSL_REDIRECT = False

            try:
                response = self.get_response(request)
            finally:
                # Restore original SECURE_SSL_REDIRECT value
                settings.SECURE_SSL_REDIRECT = self.original_ssl_redirect

            return response

        # Normal request processing
        return self.get_response(request)
