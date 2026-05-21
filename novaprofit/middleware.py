import logging
import time

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """Logs basic request/response metadata and timing for debugging."""

    def process_request(self, request):
        request._request_start_time = time.monotonic()
        logger.debug(
            "Request started: %s %s from %s",
            request.method,
            request.get_full_path(),
            request.META.get("REMOTE_ADDR", "unknown"),
        )

    def process_response(self, request, response):
        start_time = getattr(request, "_request_start_time", None)
        if start_time is not None:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            response["X-Request-Duration-ms"] = str(elapsed_ms)
            logger.debug(
                "Request finished: %s %s in %dms",
                request.method,
                request.get_full_path(),
                elapsed_ms,
            )
        return response

    def process_exception(self, request, exception):
        logger.exception(
            "Unhandled exception for request %s %s",
            request.method,
            request.get_full_path(),
            exc_info=exception,
        )
        return None
