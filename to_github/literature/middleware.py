"""
Middleware for operation logging.
"""
import json
from django.urls import resolve
from .models import OperationLog


class OperationLogMiddleware:
    """
    Middleware to log user operations automatically.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URLs to log
        self.logged_actions = {
            'literature_upload': OperationLog.Action.UPLOAD,
            'literature_delete': OperationLog.Action.DELETE,
            'literature_edit': OperationLog.Action.UPDATE,
            'literature_download': OperationLog.Action.DOWNLOAD,
            'plagiarism_check': OperationLog.Action.CHECK,
            'user_create': OperationLog.Action.USER_CREATE,
            'user_edit': OperationLog.Action.USER_UPDATE,
            'user_delete': OperationLog.Action.USER_DELETE,
            'system_settings': OperationLog.Action.SETTINGS_CHANGE,
        }

    def __call__(self, request):
        response = self.get_response(request)

        # Log after request is processed
        if request.user.is_authenticated:
            self._log_operation(request, response)

        return response

    def _log_operation(self, request, response):
        """Log the operation if applicable."""
        try:
            # Skip if not a POST/PUT/DELETE request
            if request.method not in ['POST', 'PUT', 'DELETE']:
                return

            # Skip successful responses only (2xx)
            if not (200 <= response.status_code < 300):
                return

            # Get the view name
            match = resolve(request.path_info)
            view_name = match.url_name

            if view_name in self.logged_actions:
                # Get target info
                target = ''
                target_id = ''

                if 'pk' in match.kwargs:
                    target_id = match.kwargs['pk']

                # Get additional details from POST data
                details = {}
                if request.content_type == 'application/json':
                    try:
                        details = json.loads(request.body.decode())
                    except:
                        pass
                elif request.POST:
                    details = dict(request.POST)

                # Create log entry
                OperationLog.objects.create(
                    user=request.user,
                    action=self.logged_actions[view_name],
                    target=target,
                    target_id=target_id,
                    details=details,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
        except Exception:
            # Don't break the request if logging fails
            pass

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
