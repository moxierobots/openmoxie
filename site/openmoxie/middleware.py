"""
Middleware to bypass ALLOWED_HOSTS check for health endpoints from internal IPs.
"""

from django.utils.deprecation import MiddlewareMixin
import ipaddress


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Bypass ALLOWED_HOSTS validation for health check endpoints
    when accessed from internal/private IP addresses.
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

    def process_request(self, request):
        """Check if this is a health check from an internal IP and bypass ALLOWED_HOSTS if so."""

        # Check if this is a health check path
        if request.path not in self.HEALTH_PATHS:
            return None

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
                    # Bypass ALLOWED_HOSTS by modifying get_host method
                    request.get_host = lambda: 'localhost'
                    break
        except (ValueError, TypeError):
            pass

        return None
