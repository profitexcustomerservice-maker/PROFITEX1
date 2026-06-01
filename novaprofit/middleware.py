import logging
import time
from django.conf import settings
from django.core.cache import caches
from django.http import HttpResponse
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

class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiter using cache to protect against abusive traffic."""

    def _get_cache(self):
        return caches['default']

    def process_request(self, request):
        if request.method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
            return None

        ip = request.META.get('REMOTE_ADDR', 'unknown')
        if ip == 'unknown':
            return None

        cache_key = f"rl:{ip}"
        cache = self._get_cache()
        limit = getattr(settings, 'RATE_LIMIT_REQUESTS', 120)
        window = getattr(settings, 'RATE_LIMIT_TIME_WINDOW', 60)

        current = cache.get(cache_key, 0)
        if current >= limit:
            logger.warning("Rate limit exceeded for %s: %s/%s", ip, current, limit)
            return HttpResponse(
                'Too many requests. Please try again later.',
                status=429,
                headers={'Retry-After': str(window)},
                content_type='text/plain',
            )

        if current == 0:
            cache.set(cache_key, 1, timeout=window)
        else:
            cache.incr(cache_key)

