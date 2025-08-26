"""
Middleware to handle health endpoints from internal IPs without security checks.
"""

import ipaddress


class HealthCheckMiddleware:
    """
    Handle health check endpoints directly for internal IP addresses,
    bypassing all other middleware including security checks.

    This middleware must be placed FIRST in the MIDDLEWARE list.
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

    def __call__(self, request):
        # Check if this is a health check path
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
                        # Handle the health check directly here
                        # This bypasses ALL other middleware
                        return self.handle_health_check(request)
            except (ValueError, TypeError):
                pass

        # Continue with normal middleware chain
        return self.get_response(request)

    def handle_health_check(self, request):
        """
        Handle health check directly.
        You can customize this or import your actual health check logic.
        """
        # Simple health check response
        # You can import and call your actual health view here if needed
        from django.http import JsonResponse

        # Basic health check
        return JsonResponse({
            'status': 'healthy',
            'service': 'openmoxie'
        }, status=200)
