"""
Security utilities for input sanitization and rate limiting.
"""

import re
from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings


def sanitize_input(value, max_length=100):
    """
    Sanitize user input to prevent XSS and injection attacks.
    """
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if len(value) > max_length:
            value = value[:max_length]

        dangerous_patterns = [
            r"<script",
            r"javascript:",
            r"onerror=",
            r"onclick=",
            r"onload=",
            r"<iframe",
            r"eval\(",
            r"exec\(",
        ]

        for pattern in dangerous_patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        return value

    return value


def sanitize_dict(data, max_length=100):
    """
    Sanitize all string values in a dictionary.
    """
    if not isinstance(data, dict):
        return data

    return {key: sanitize_input(value, max_length) for key, value in data.items()}


def rate_limit(key_prefix, limit=60, period=60):
    """
    Simple rate limiting decorator using cache.

    Usage:
        @rate_limit('search', limit=30, period=60)
        def search(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not hasattr(request, "user") or not request.user.is_authenticated:
                identifier = request.META.get("REMOTE_ADDR", "unknown")
            else:
                identifier = f"user_{request.user.id}"

            cache_key = f"ratelimit_{key_prefix}_{identifier}"

            current = cache.get(cache_key, 0)
            if current >= limit:
                return JsonResponse(
                    {"error": "Rate limit exceeded", "retry_after": period}, status=429
                )

            cache.set(cache_key, current + 1, period)

            response = view_func(request, *args, **kwargs)

            if hasattr(response, "headers"):
                remaining = limit - current - 1
                response["X-RateLimit-Limit"] = str(limit)
                response["X-RateLimit-Remaining"] = str(max(0, remaining))

            return response

        return wrapped

    return decorator


class RateLimitMiddleware:
    """
    Middleware for tracking request rates per IP/user.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, "RATE_LIMIT_PER_MINUTE", 60)

    def __call__(self, request):
        identifier = (
            f"user_{request.user.id}"
            if hasattr(request, "user") and request.user.is_authenticated
            else request.META.get("REMOTE_ADDR", "unknown")
        )

        cache_key = f"request_rate_{identifier}"

        current = cache.get(cache_key, 0)
        cache.set(cache_key, current + 1, 60)

        if current > self.rate_limit:
            return JsonResponse(
                {
                    "error": "Too many requests",
                    "detail": f"Rate limit: {self.rate_limit} requests per minute",
                },
                status=429,
            )

        response = self.get_response(request)
        response["X-RateLimit-Remaining"] = str(max(0, self.rate_limit - current - 1))
        return response


def validate_pagination(page, page_size, max_page_size=100):
    """
    Validate pagination parameters to prevent large queries.
    """
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = min(max(1, int(page_size)), max_page_size)
    except (TypeError, ValueError):
        page_size = 20

    return page, page_size


def safe_filename(filename):
    """
    Generate a safe filename for uploads.
    """
    import uuid
    import os

    filename = os.path.basename(filename)
    name, ext = os.path.splitext(filename)

    safe_name = re.sub(r"[^\w\s-]", "", name)
    safe_name = re.sub(r"[-\s]+", "-", safe_name)

    unique_id = uuid.uuid4().hex[:8]

    return f"{safe_name}_{unique_id}{ext}"
